import uuid
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict, Tuple, Type, TypeVar
from pydantic import BaseModel, ValidationError, Field
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import asyncio
from sse_manager import push_update

class ExecutionError(Exception):
    pass

class AgentSchema(BaseModel):
    role: str
    content: str

class MessageDict(BaseModel):
    role: str
    input_data: Dict[str, Any]
    agent_msgs: Optional[List[Dict[str, Any]]] = None
    toolcall_in_output: bool
    tool_args: Optional[Dict[str, Any]] = None
    output_state: Any
    execution_id: str = ""

class Node:
    def __init__(self, name: str, function: Callable, is_agent: bool = False, agent_schema: Type[BaseModel] = AgentSchema):
        self.id = name
        self.name = name
        self.function = function
        self.is_agent = is_agent
        self.agent_id = str(uuid.uuid4()) if is_agent else None
        self.agent_schema = agent_schema if is_agent else None

    def execute(self, input_data: Dict[str, Any], agentic_memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if self.is_agent and agentic_memory is not None:
            result = self.function(input_data, agentic_memory)
        else:
            result = self.function(input_data)

        if isinstance(result, dict) and "graph_data" in result and "metahistory" in result:
            return result
        else:
            return {"graph_data": result, "metahistory": None}

class StartNode(Node):
    def __init__(self, name: str = "Start"):
        super().__init__(name, lambda x: x)
    
    def execute(self, graph_data: Any, agentic_memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        logging.info(f"Starting execution with initial data: {graph_data}")
        return {"graph_data": graph_data, "metahistory": None}

class EndNode(Node):
    def __init__(self, name: str = "End"):
        super().__init__(name, lambda x: x)
    
    def execute(self, graph_data: Any, agentic_memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        logging.info(f"Execution ended with final data: {graph_data}")
        return {"graph_data": graph_data, "metahistory": None}

class FlexibleBranch:
    def __init__(self, condition: Callable[[Any], Any], branches: Dict[Any, Union[str, List[str]]]):
        self.condition = condition
        self.branches = branches

class EdgeContainer:
    def __init__(self):
        self.regular_edges: List[Tuple[Optional[str], str, Optional[Callable[[Any], bool]], bool]] = []
        self.flexible_branch: Optional[FlexibleBranch] = None

class DataSchema(BaseModel):
    field1: str = Field(...)
    field2: int = Field(...)
    field3: Optional[List[str]] = Field(default=None)

class AgenticGraph:
    def __init__(self, graph_id: str, chat_id: Optional[str] = None, data_schema: Type[BaseModel] = DataSchema, max_parallel: int = 3, metahistory_type: Type = MessageDict, agent_schema_type: Type[BaseModel] = AgentSchema):
        self.graph_id = graph_id
        self.chat_id = chat_id or str(uuid.uuid4())
        self.initial_data = None
        self.data_schema = data_schema
        self.max_parallel = max_parallel
        self.metahistory_type = metahistory_type
        self.agent_schema_type = agent_schema_type
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, EdgeContainer] = {}
        self.reverse_edges: Dict[str, List[Union[str, Tuple[str, str]]]] = {}
        self.required_dependencies: Dict[str, Set[Union[str, Tuple[str, str]]]] = {}
        self.start_node: Optional[StartNode] = None
        self.end_nodes: List[EndNode] = []
        self.current_node: Optional[Node] = None
        self.stop_execution: bool = False
        self.connected_graphs: Dict[str, 'AgenticGraph'] = {}
        self.shared_keys: Dict[str, Set[str]] = {}
        self.metahistory: Dict[str, Tuple[Dict[str, Any], List[str]]] = {self.chat_id: ({}, [])}
        self.agent_ids: List[str] = []
        self.agentic_memory: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_schemas: Dict[str, Type[BaseModel]] = {}
        self.node_graph_state: Dict[str, Dict[str, Any]] = {self.chat_id: {}}
        self.current_execution_id: Optional[str] = None

        ##SSE 
        self.sse_queue = asyncio.Queue()
        self.sse_task = None
        
        self.logger = logging.getLogger(f"AgenticGraph-{self.graph_id}")
        self.logger.setLevel(logging.INFO)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    async def sse_sender(self):
        while True:
            try:
                update = await self.sse_queue.get()
                await push_update(update['chat_id'], update)
                self.logger.info(f"SSE update sent for node: {update.get('node')}, chat_id: {update['chat_id']}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error sending SSE update: {str(e)}")
            finally:
                self.sse_queue.task_done()

    async def start_sse_sender(self):
        if self.sse_task is None or self.sse_task.done():
            self.sse_task = asyncio.create_task(self.sse_sender())
            await asyncio.sleep(0)  # Ensure the task starts

    async def stop_sse_sender(self):
        if self.sse_task:
            self.sse_task.cancel()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                pass

    def add_node(self, node_or_name: Union[Node, str], function: Optional[Callable] = None, is_agent: bool = False, agent_schema: Optional[Type[BaseModel]] = None):
        if isinstance(node_or_name, Node):
            if function is not None:
                raise ValueError("Cannot provide both a Node object and a function")
            node = node_or_name
        elif isinstance(node_or_name, str):
            if function is None:
                raise ValueError("Must provide a function when adding a node by name")
            node = Node(node_or_name, function, is_agent, agent_schema or self.agent_schema_type)
        else:
            raise ValueError("First argument must be either a Node object or a string name")

        self.nodes[node.id] = node
        if isinstance(node, StartNode):
            if self.start_node:
                raise ValueError("Graph already has a start node")
            self.start_node = node
        elif isinstance(node, EndNode):
            self.end_nodes.append(node)

        if node.is_agent:
            self.agent_ids.append(node.agent_id)
            self.agentic_memory[node.agent_id] = []
            self.agent_schemas[node.agent_id] = agent_schema or self.agent_schema_type

    def connect_graph(self, other_graph: 'AgenticGraph'):
        self.connected_graphs[other_graph.graph_id] = other_graph
        self._update_shared_keys(other_graph)

    def _update_shared_keys(self, other_graph: 'AgenticGraph'):
        self_keys = set(self.data_schema.model_fields.keys())
        other_keys = set(other_graph.data_schema.model_fields.keys())
        
        common_keys = self_keys.intersection(other_keys)
        self.shared_keys[other_graph.graph_id] = common_keys
        other_graph.shared_keys[self.graph_id] = common_keys

    def add_edge(self, source: str, target: Union[str, Tuple[str, str]], condition: Optional[Callable[[Any], bool]] = None, is_required: bool = True):
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' does not exist in the current graph")

        if isinstance(target, tuple):
            target_graph_id, target_id = target
            if target_graph_id not in self.connected_graphs:
                raise ValueError(f"Target graph '{target_graph_id}' is not connected")
            target_graph = self.connected_graphs[target_graph_id]
            if target_id not in target_graph.nodes:
                raise ValueError(f"Target node '{target_id}' does not exist in the connected graph '{target_graph_id}'")
        else:
            target_graph_id = None
            target_id = target
            if target_id not in self.nodes:
                raise ValueError(f"Target node '{target_id}' does not exist in the current graph")

        if source not in self.edges:
            self.edges[source] = EdgeContainer()
        self.edges[source].regular_edges.append((target_graph_id, target_id, condition, is_required))

        if target_graph_id is None:
            if target_id not in self.reverse_edges:
                self.reverse_edges[target_id] = []
            self.reverse_edges[target_id].append(source)
        else:
            target_graph = self.connected_graphs[target_graph_id]
            if target_id not in target_graph.reverse_edges:
                target_graph.reverse_edges[target_id] = []
            target_graph.reverse_edges[target_id].append((self.graph_id, source))

        if is_required:
            if target_graph_id is None:
                if target_id not in self.required_dependencies:
                    self.required_dependencies[target_id] = set()
                self.required_dependencies[target_id].add(source)
            else:
                target_graph = self.connected_graphs[target_graph_id]
                if target_id not in target_graph.required_dependencies:
                    target_graph.required_dependencies[target_id] = set()
                target_graph.required_dependencies[target_id].add((self.graph_id, source))

    def add_branching_edge(self, source_id: str, condition: Callable[[Any], Any], branches: Dict[Any, Union[str, List[str], Tuple[str, str], List[Tuple[str, str]]]]):
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist in the graph")
        
        if source_id not in self.edges:
            self.edges[source_id] = EdgeContainer()
        
        self.edges[source_id].flexible_branch = FlexibleBranch(condition, branches)
        
        for branch_targets in branches.values():
            targets = [branch_targets] if isinstance(branch_targets, (str, tuple)) else branch_targets
            for target in targets:
                if isinstance(target, str):
                    if target not in self.nodes:
                        raise ValueError(f"Target node '{target}' does not exist in the graph")
                    if target not in self.reverse_edges:
                        self.reverse_edges[target] = []
                    self.reverse_edges[target].append(source_id)
                elif isinstance(target, tuple):
                    target_graph_id, target_id = target
                    if target_graph_id not in self.connected_graphs:
                        raise ValueError(f"Target graph '{target_graph_id}' is not connected")
                    target_graph = self.connected_graphs[target_graph_id]
                    if target_id not in target_graph.nodes:
                        raise ValueError(f"Target node '{target_id}' does not exist in the connected graph '{target_graph_id}'")
                    if target_id not in target_graph.reverse_edges:
                        target_graph.reverse_edges[target_id] = []
                    target_graph.reverse_edges[target_id].append((self.graph_id, source_id))
                else:
                    raise ValueError("Branch target must be either a string (node name), a tuple (graph_id, node_name), or a list of these")

    def get_next_nodes(self, current_node: Node, graph_data: Any) -> List[Tuple[Node, Optional[str]]]:
        next_nodes = []
        edge_container = self.edges.get(current_node.id)
        
        if edge_container:
            # Handle regular edges
            for target_graph_id, target_id, condition, is_required in edge_container.regular_edges:
                if condition is None or condition(graph_data):
                    if target_graph_id is None:
                        next_nodes.append((self.nodes[target_id], None))
                    else:
                        target_graph = self.connected_graphs[target_graph_id]
                        next_nodes.append((target_graph.nodes[target_id], target_graph_id))
            
            # Handle flexible branching
            if edge_container.flexible_branch:
                branch_value = edge_container.flexible_branch.condition(graph_data)
                if branch_value in edge_container.flexible_branch.branches:
                    targets = edge_container.flexible_branch.branches[branch_value]
                    if isinstance(targets, (str, tuple)):
                        targets = [targets]
                    for target in targets:
                        if isinstance(target, str):
                            next_nodes.append((self.nodes[target], None))
                        elif isinstance(target, tuple):
                            target_graph_id, target_id = target
                            target_graph = self.connected_graphs[target_graph_id]
                            next_nodes.append((target_graph.nodes[target_id], target_graph_id))
        
        return next_nodes

    def get_previous_nodes(self, node: Node) -> List[Union[Node, Tuple[str, Node]]]:
        previous_node_ids = self.reverse_edges.get(node.id, [])
        previous_nodes = []
        for node_id in previous_node_ids:
            if isinstance(node_id, tuple):
                graph_id, node_id = node_id
                previous_nodes.append((graph_id, self.connected_graphs[graph_id].nodes[node_id]))
            else:
                previous_nodes.append(self.nodes[node_id])
        return previous_nodes

    def are_dependencies_met(self, node: Node, chat_id: str) -> bool:
        required_deps = self.required_dependencies.get(node.id, set())
        for dep in required_deps:
            if isinstance(dep, tuple):
                dep_graph_id, dep_node_id = dep
                dep_graph = self.connected_graphs[dep_graph_id]
                if dep_graph.chat_id not in dep_graph.node_graph_state or dep_node_id not in dep_graph.node_graph_state[dep_graph.chat_id]:
                    return False
            else:
                if chat_id not in self.node_graph_state or dep not in self.node_graph_state[chat_id]:
                    return False
        return True

    # def create_agent_message(self, metahistory: Any, agent_id: str) -> Dict[str, Any]:
    #     schema = self.agent_schemas.get(agent_id, self.agent_schema_type)
    #     try:
    #         if isinstance(metahistory, self.metahistory_type):
    #             agent_message = schema(**metahistory.dict(exclude={'create_agent_msg', 'node_index'}))
    #         else:
    #             agent_message = schema(**{k: v for k, v in metahistory.items() if k not in {'create_agent_msg', 'node_index'}})
    #         return agent_message.dict(exclude_unset=True)
    #     except ValidationError as e:
    #         logging.warning(f"Validation error for agent {agent_id}: {e}")
    #         return {"role": getattr(metahistory, 'role', 'unknown'), "content": getattr(metahistory, 'content', '')}

    async def execute_node(self, node: Node, input_data: Dict[str, Any], max_retries: int = 1) -> Any:
        self.logger.info(f"Executing node '{node.name}' in graph '{self.graph_id}'")
        loop = asyncio.get_event_loop()
        for attempt in range(max_retries):
            try:
                if node.is_agent:
                    agentic_memory = self.agentic_memory.get(node.agent_id, [])
                    # Run node.execute in an executor to prevent blocking the event loop
                    result = await loop.run_in_executor(None, node.execute, input_data, agentic_memory)
                else:
                    # Run node.execute in an executor to prevent blocking the event loop
                    result = await loop.run_in_executor(None, node.execute, input_data)
                self.logger.info(f"Node '{node.name}' execution completed successfully")
                return result
            except ExecutionError as e:
                self.logger.error(f"Attempt {attempt + 1}/{max_retries} failed for node '{node.name}': {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Wait before retrying

    async def execute_branch(self, node: Node, source_graph_id: Optional[str] = None):
        while node and not self.stop_execution:
            self.current_node = node 
            self.logger.info(f"Processing node '{node.name}' in graph '{self.graph_id}'")

            if not self.are_dependencies_met(node, self.chat_id):
                required_deps = self.required_dependencies.get(node.id, set())
                missing_deps = [dep for dep in required_deps if isinstance(dep, str) and dep not in self.node_graph_state[self.chat_id]]
                self.logger.info(f"Node '{node.name}' is waiting for required dependencies: {missing_deps}. Required dependencies: {required_deps}")
                return

            if isinstance(node, StartNode):
                input_data = self.initial_data
            else:
                previous_nodes = self.get_previous_nodes(node)
                self.logger.info(f"Previous nodes for '{node.name}': {[n.name if isinstance(n, Node) else f'{n[0]}:{n[1].name}' for n in previous_nodes]}")
                input_data = {}
                for prev_node in previous_nodes:
                    if isinstance(prev_node, tuple):
                        prev_graph_id, prev_node = prev_node
                        self.logger.info(f"Previous node from connected graph: graph_id={prev_graph_id}, node={prev_node.name}")
                        prev_graph = self.connected_graphs[prev_graph_id]
                        shareable_data = prev_graph.get_shareable_data(self.graph_id, prev_node.name)
                        if shareable_data is not None:
                            input_data[prev_node.name] = shareable_data
                        else:
                            self.logger.warning(f"Empty shareable data for node '{prev_node.name}' from graph '{prev_graph_id}'")
                    elif prev_node.name in self.node_graph_state[self.chat_id]:
                        input_data[prev_node.name] = self.node_graph_state[self.chat_id][prev_node.name]
                
                if not input_data:
                    raise ValueError(f"No available input data for {node.name}")

            result = await self.execute_node(node, input_data)
            
            if result is not None:
                self.node_graph_state[self.chat_id][node.name] = result["graph_data"]
                #for connected_graph_id in self.connected_graphs:
                #    self._update_shared_keys(self.connected_graphs[connected_graph_id])
                self.logger.info(f"Updated node graph state for '{node.name}'")

                if result["metahistory"]:
                    try:
                        if isinstance(result["metahistory"], dict):
                            metahistory = self.metahistory_type(**result["metahistory"])
                        elif isinstance(result["metahistory"], self.metahistory_type):
                            metahistory = result["metahistory"]
                        else:
                            raise ValueError(f"Unexpected metahistory type: {type(result['metahistory'])}")
                        
                        metahistory.execution_id = self.current_execution_id
                        entry_id = str(uuid.uuid4())

                        if node.is_agent:
                            if metahistory.agent_msgs is not None:
                                self.agentic_memory[node.agent_id] = metahistory.agent_msgs
                            else:
                                self.agentic_memory[node.agent_id] = []  # Clear the memory if no new messages

                        self.metahistory[self.chat_id][0][entry_id] = metahistory
                        self.metahistory[self.chat_id][1].append(entry_id)

                        # Push update via SSE
                        update = {
                            "node": node.name,
                            "chat_id": self.chat_id,
                            "entry_id": entry_id,
                            # "metahistory": metahistory.dict()
                        }
                        await self.sse_queue.put(update)
                        self.logger.info(f"SSE update queued for node: {node.name}, chat_id: {self.chat_id}")

                    except Exception as e:
                        logging.warning(f"Invalid metahistory from node {node.name}. Error: {str(e)}")

            if isinstance(node, EndNode):
                self.logger.info(f"Reached EndNode: '{node.name}'")
                return

            next_nodes = self.get_next_nodes(node, {node.name: self.node_graph_state[self.chat_id].get(node.name)})

            if not next_nodes:
                self.logger.warning(f"No next nodes found for '{node.name}'")
                return

            if len(next_nodes) == 1:
                next_node, next_source_graph_id = next_nodes[0]
                self.logger.info(f"Moving to next node: '{next_node.name}' in graph '{next_source_graph_id or self.graph_id}'")
                
                if next_source_graph_id:
                    # If the next node is in a different graph, call that graph's execute_branch
                    self.connected_graphs[next_source_graph_id].execute_branch(next_node, self.graph_id)
                    return
                else:
                    node = next_node
            else:
                self.logger.info(f"Branching execution for node '{node.name}' to {len(next_nodes)} parallel paths")
                tasks = []
                for next_node, next_source_graph_id in next_nodes[:self.max_parallel]:
                    if next_source_graph_id:
                        tasks.append(asyncio.create_task(self.connected_graphs[next_source_graph_id].execute_branch(next_node, self.graph_id)))
                    else:
                        tasks.append(asyncio.create_task(self.execute_branch(next_node)))
                await asyncio.gather(*tasks)
                return

        if self.stop_execution:
            self.logger.info(f"Execution stopped at node: '{node.name}'")

    async def execute(self, initial_data: Any, max_parallel: int = 3, chat_id: Optional[str] = None):
        if not self.start_node:
            raise ValueError("Graph must have a start node")

        if max_parallel is not None:
            self.max_parallel = max_parallel


        # Validate initial_data against the schema
        try:
            validated_data = self.data_schema(**initial_data)
            self.initial_data = validated_data.dict()
        except ValidationError as e:
            raise ValueError(f"Initial data does not match the specified schema: {e}")

        if chat_id:
            self.chat_id = chat_id
        if self.chat_id not in self.metahistory:
            self.metahistory[self.chat_id] = ({}, [])
        if self.chat_id not in self.node_graph_state:
            self.node_graph_state[self.chat_id] = {}


        self.current_execution_id = str(uuid.uuid4())  # Generate execution_id for this run

        start_node = self.current_node if self.current_node else self.start_node
        self.logger.info(f"Starting graph execution from node '{start_node.name}'. Execution ID: {self.current_execution_id}")

        await self.start_sse_sender()

        try:
            await self.execute_branch(start_node)
        finally:
            # Don't stop the SSE sender here, let it continue running
            pass

        self.logger.info(f"Graph execution completed. Chat ID: {self.chat_id}, Execution ID: {self.current_execution_id}")

    def stop_at_current_node(self):
        self.stop_execution = True

    def resume_execution(self):
        self.stop_execution = False

    def get_current_node(self) -> Optional[Node]:
        return self.current_node

    def get_graph_data(self) -> Optional[Dict[str, Any]]:
        return self.node_graph_state.get(self.chat_id)

    def get_shareable_data(self, target_graph_id: str, node_name: str) -> Optional[Any]:
        shared_keys = self.shared_keys.get(target_graph_id, set())
        if node_name in self.node_graph_state[self.chat_id]:
            node_data = self.node_graph_state[self.chat_id][node_name]
            if isinstance(node_data, dict):
                return {k: v for k, v in node_data.items() if k in shared_keys}
            else:
                # If node_data is not a dict, we can't filter it, so we return it as is
                return node_data
        return None

    def get_metahistory(self, chat_id: Optional[str] = None) -> Tuple[Dict[str, Any], List[str]]:
        return self.metahistory[chat_id or self.chat_id]

    def get_agentic_memory(self, agent_id: str) -> List[Dict[str, Any]]:
        return self.agentic_memory.get(agent_id, [])

    def get_node_graph_state(self, chat_id: Optional[str] = None) -> Dict[str, Any]:
        return self.node_graph_state.get(chat_id or self.chat_id, {})

    def visualize_graph(self) -> str:
        dot_str = "digraph G {\n"
        for node_id, node in self.nodes.items():
            shape = "box" if node.is_agent else "ellipse"
            dot_str += f'  "{node_id}" [shape={shape}];\n'
        
        for source, edge_container in self.edges.items():
            for target_graph_id, target_id, condition, is_required in edge_container.regular_edges:
                target_label = f"{target_graph_id}:{target_id}" if target_graph_id else target_id
                label = "required" if is_required else ""
                if condition:
                    label += f" (condition)" if label else "condition"
                dot_str += f'  "{source}" -> "{target_label}"'
                if label:
                    dot_str += f' [label="{label}"]'
                dot_str += ';\n'
        
        dot_str += "}"
        return dot_str

    def save_graph_visualization(self, filename: str = "graph.png"):
        try:
            from graphviz import Source
            dot_str = self.visualize_graph()
            src = Source(dot_str)
            src.render(filename, format='png', cleanup=True)
            print(f"Graph visualization saved to {filename}.png")
        except ImportError:
            print("graphviz is not installed. Please install it to use this feature.")

    def __str__(self):
        return f"AgenticGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, chats={len(self.metahistory)})"

    def __repr__(self):
        return self.__str__()