from typing import Any, Callable, Dict, List, Optional, Union, Tuple, Type, Set
from pydantic import BaseModel, Field
import uuid
from concurrent.futures import ThreadPoolExecutor
from pydantic import ValidationError
import logging
import time

class ExecutionError(Exception):
    pass

class AgentSchema(BaseModel):
    role: str = Field(...)
    content: str = Field(...)

class MessageDict(BaseModel):
    role: str
    content: str
    tool_call: bool
    tool_args: Optional[Dict[str, Any]] = None
    result: Any
    create_agent_msg: bool
    node_index: Optional[Tuple[str, str, int]] = None
    execution_id: str = ""  # Default to empty string

class Node:
    def __init__(self, name: str, function: Callable, is_agent: bool = False, agent_schema: Type[AgentSchema] = AgentSchema):
        self.id = name
        self.name = name
        self.function = function
        self.is_agent = is_agent
        self.agent_id = str(uuid.uuid4()) if is_agent else None
        self.agent_schema = agent_schema if is_agent else None

    def execute(self, input_data: Dict[str, Any], agentic_memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        #try:
        if self.is_agent and agentic_memory is not None:
            result = self.function(input_data, agentic_memory)
        else:
            result = self.function(input_data)

        if isinstance(result, dict) and "graph_data" in result and "metahistory" in result:
            return result
        else:
            return {"graph_data": result, "metahistory": None}
        # except Exception as e:
        #     raise ExecutionError(f"Error executing node {self.name}: {str(e)}")
        
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
        self.regular_edges: List[Tuple[str, Optional[Callable[[Any], bool]], bool]] = []
        self.flexible_branch: Optional[FlexibleBranch] = None

class AgenticGraph:
    def __init__(self, initial_data: Any, chat_id: Optional[str] = None):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, EdgeContainer] = {}
        self.reverse_edges: Dict[str, List[str]] = {}
        self.required_dependencies: Dict[str, Set[str]] = {}
        self.start_node: Optional[StartNode] = None
        self.end_nodes: List[EndNode] = []
        self.current_node: Optional[Node] = None
        self.stop_execution: bool = False
        self.initial_data: Any = initial_data
        self.chat_id: str = chat_id or str(id(self))
        self.metahistory: Dict[str, Tuple[Dict[str, MessageDict], List[str]]] = {self.chat_id: ({}, [])}
        self.agent_ids: List[str] = []
        self.agentic_memory: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_schemas: Dict[str, Type[AgentSchema]] = {}
        self.current_execution_id: Optional[str] = None
        self.execution_ids: List[str] = []
        self.node_graph_state: Dict[str, Dict[str, Any]] = {}
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def add_node(self, node_or_name: Union[Node, str], function: Optional[Callable] = None, is_agent: bool = False, agent_schema: Type[AgentSchema] = AgentSchema):
        if isinstance(node_or_name, Node):
            if function is not None:
                raise ValueError("Cannot provide both a Node object and a function")
            node = node_or_name
        elif isinstance(node_or_name, str):
            if function is None:
                raise ValueError("Must provide a function when adding a node by name")
            node = Node(node_or_name, function, is_agent, agent_schema)
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
            self.agent_schemas[node.agent_id] = agent_schema

    def add_edge(self, source_id: str, target_id: str, condition: Optional[Callable[[Any], bool]] = None, is_required: bool = False):
        
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist in the graph")
        if target_id not in self.nodes:
            raise ValueError(f"Target node '{target_id}' does not exist in the graph")
        
        if source_id not in self.edges:
            self.edges[source_id] = EdgeContainer()
        
        self.edges[source_id].regular_edges.append((target_id, condition, is_required))

        if target_id not in self.reverse_edges:
            self.reverse_edges[target_id] = []
        self.reverse_edges[target_id].append(source_id)

        if is_required:
            if target_id not in self.required_dependencies:
                self.required_dependencies[target_id] = set()
            self.required_dependencies[target_id].add(source_id)

    def add_branching_edge(self, source_id: str, condition: Callable[[Any], Any], branches: Dict[Any, Union[str, List[str]]], is_required: bool = False):
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist in the graph")
        
        if source_id not in self.edges:
            self.edges[source_id] = EdgeContainer()
        
        self.edges[source_id].flexible_branch = FlexibleBranch(condition, branches)
        
        for target in branches.values():
            if isinstance(target, str):
                if target not in self.nodes:
                    raise ValueError(f"Target node '{target}' does not exist in the graph")
                if target not in self.reverse_edges:
                    self.reverse_edges[target] = []
                self.reverse_edges[target].append(source_id)
            elif isinstance(target, list):
                for node in target:
                    if node not in self.nodes:
                        raise ValueError(f"Target node '{node}' does not exist in the graph")
                    if node not in self.reverse_edges:
                        self.reverse_edges[node] = []
                    self.reverse_edges[node].append(source_id)
            else:
                raise ValueError("Branch target must be either a string (node name) or a list of strings")

    def get_next_nodes(self, current_node: Node, graph_data: Any) -> List[Node]:
        next_nodes = []
        edge_container = self.edges.get(current_node.id)
        
        if edge_container:
            # Process regular edges
            for target_id, condition, _ in edge_container.regular_edges:
                if condition is None or condition(graph_data):
                    next_nodes.append(self.nodes[target_id])
            
            # Process flexible branch if it exists
            if edge_container.flexible_branch:
                branch = edge_container.flexible_branch
                condition_result = branch.condition(graph_data)
                branch_targets = branch.branches.get(condition_result, [])
                if isinstance(branch_targets, str):
                    branch_targets = [branch_targets]
                next_nodes.extend([self.nodes[node_id] for node_id in branch_targets])
        
        return next_nodes

    def get_previous_nodes(self, node: Node) -> List[Node]:
        previous_node_ids = self.reverse_edges.get(node.id, [])
        return [self.nodes[node_id] for node_id in previous_node_ids]

    def are_dependencies_met(self, node: Node, execution_id: str) -> bool:
        required_deps = self.required_dependencies.get(node.id, set())
        return all(dep in self.node_graph_state[execution_id] for dep in required_deps)

    def create_agent_message(self, metahistory: MessageDict, agent_id: str) -> Dict[str, Any]:
        schema = self.agent_schemas.get(agent_id, AgentSchema)
        try:
            agent_message = schema(**metahistory.dict(exclude={'create_agent_msg', 'node_index'}))
            return agent_message.dict(exclude_unset=True)
        except ValidationError as e:
            logging.warning(f"Validation error for agent {agent_id}: {e}")
            return {"role": metahistory.role, "content": metahistory.content}

    def execute_node(self, node: Node, input_data: Dict[str, Any], max_retries: int = 1) -> Any:
        for attempt in range(max_retries):
            try:
                if node.is_agent:
                    agentic_memory = self.agentic_memory.get(node.agent_id, [])
                    return node.execute(input_data, agentic_memory)
                else:
                    return node.execute(input_data)
            except ExecutionError as e:
                logging.error(f"Attempt {attempt + 1}/{max_retries} failed for node {node.name}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)  # Wait before retrying

    def execute(self, max_parallel: int = 3, chat_id: Optional[str] = None):
        if not self.start_node:
            raise ValueError("Graph must have a start node")

        if chat_id:
            self.chat_id = chat_id
            if chat_id not in self.metahistory:
                self.metahistory[chat_id] = ({}, [])

        self.current_execution_id = str(uuid.uuid4())
        self.execution_ids.append(self.current_execution_id)
        self.node_graph_state[self.current_execution_id] = {}

        def execute_branch(node: Node):
            while node and not self.stop_execution:
                #try:
                self.current_node = node

                if not self.are_dependencies_met(node, self.current_execution_id):
                    logging.info(f"Node {node.name} is waiting for required dependencies")
                    return

                # Prepare input data
                if isinstance(node, StartNode):
                    input_data = self.initial_data #{"start": self.initial_data}
                else:
                    previous_nodes = self.get_previous_nodes(node)
                    input_data = {}
                    for prev_node in previous_nodes:
                        if prev_node.name in self.node_graph_state[self.current_execution_id]:
                            input_data[prev_node.name] = self.node_graph_state[self.current_execution_id][prev_node.name]
                    
                    if not input_data:
                        raise ValueError(f"No available input data for {node.name}")

                result = self.execute_node(node, input_data)
                
                if result is not None:
                    self.node_graph_state[self.current_execution_id][node.name] = result["graph_data"]

                    if result["metahistory"]:
                        try:
                            metahistory = MessageDict.parse_obj(result["metahistory"])
                            metahistory.execution_id = self.current_execution_id
                            entry_id = str(uuid.uuid4())

                            if metahistory.create_agent_msg and node.is_agent:
                                agent_message = self.create_agent_message(metahistory, node.agent_id)
                                self.agentic_memory[node.agent_id].append(agent_message)
                                msg_index = len(self.agentic_memory[node.agent_id]) - 1

                                metahistory.node_index = (node.name, node.agent_id, msg_index)

                            self.metahistory[self.chat_id][0][entry_id] = metahistory
                            self.metahistory[self.chat_id][1].append(entry_id)
                        except ValidationError as e:
                            logging.warning(f"Invalid metahistory from node {node.name}. Error: {str(e)}")

                if isinstance(node, EndNode):
                    logging.info(f"Reached EndNode: {node.name}")
                    return

                next_nodes = self.get_next_nodes(node,{node.name : self.node_graph_state[self.current_execution_id].get(node.name) })

                if not next_nodes:
                    logging.warning(f"No next nodes found for {node.name}")
                    return

                if len(next_nodes) == 1:
                    node = next_nodes[0]
                else:
                    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                        futures = [executor.submit(execute_branch, next_node) for next_node in next_nodes[:max_parallel]]
                        for future in futures:
                            future.result()  # Wait for all branches to complete, but don't collect results
                    return

                # except ExecutionError as e:
                #     logging.error(f"Error: {str(e)}")
                #     return

            if self.stop_execution:
                logging.info(f"Execution stopped at node: {node.name}")

        start_node = self.current_node if self.current_node else self.start_node
        execute_branch(start_node)
        logging.info(f"Graph execution completed. Execution ID: {self.current_execution_id}")


    def stop_at_current_node(self):
        self.stop_execution = True

    def resume_execution(self):
        self.stop_execution = False

    def get_current_node(self) -> Optional[Node]:
        return self.current_node

    def get_graph_data(self) -> Any:
        if self.current_execution_id and self.current_execution_id in self.node_graph_state:
            return self.node_graph_state[self.current_execution_id]
        return None

    def get_metahistory(self, chat_id: Optional[str] = None, execution_id: Optional[str] = None) -> Tuple[Dict[str, MessageDict], List[str]]:
        chat_history = self.metahistory[chat_id or self.chat_id]
        if execution_id:
            if execution_id not in self.execution_ids:
                raise ValueError(f"Execution ID {execution_id} not found")
            filtered_history = ({k: v for k, v in chat_history[0].items() if v.execution_id == execution_id}, 
                                [entry_id for entry_id in chat_history[1] if chat_history[0][entry_id].execution_id == execution_id])
            return filtered_history
        return chat_history

    def get_agentic_memory(self, agent_id: str, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        memory = self.agentic_memory.get(agent_id, [])
        if execution_id:
            if execution_id not in self.execution_ids:
                raise ValueError(f"Execution ID {execution_id} not found")
            return [msg for msg in memory if msg.get('execution_id') == execution_id]
        return memory

    def get_execution_ids(self) -> List[str]:
        return self.execution_ids

    def get_node_graph_state(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        if execution_id is None:
            execution_id = self.current_execution_id
        if execution_id not in self.execution_ids:
            raise ValueError(f"Execution ID {execution_id} not found")
        return self.node_graph_state.get(execution_id, {})

    def get_execution_data(self, execution_id: str) -> Dict[str, Any]:
        if execution_id not in self.execution_ids:
            raise ValueError(f"Execution ID {execution_id} not found")
        
        execution_data = {
            "metahistory": self.get_metahistory(execution_id=execution_id),
            "agentic_memory": {agent_id: self.get_agentic_memory(agent_id, execution_id) for agent_id in self.agent_ids},
            "node_graph_state": self.get_node_graph_state(execution_id)
        }
        return execution_data

    def visualize_graph(self) -> str:
        """
        Returns a string representation of the graph in DOT format for visualization.
        """
        dot_str = "digraph G {\n"
        for node_id, node in self.nodes.items():
            shape = "box" if node.is_agent else "ellipse"
            dot_str += f'  "{node_id}" [shape={shape}];\n'
        
        for source, edges in self.edges.items():
            if isinstance(edges, FlexibleBranch):
                for branch_value, targets in edges.branches.items():
                    if isinstance(targets, str):
                        targets = [targets]
                    for target in targets:
                        dot_str += f'  "{source}" -> "{target}" [label="{branch_value}"];\n'
            else:
                for target, condition, is_required in edges:
                    label = "required" if is_required else ""
                    if condition:
                        label += f" (condition)" if label else "condition"
                    dot_str += f'  "{source}" -> "{target}"'
                    if label:
                        dot_str += f' [label="{label}"]'
                    dot_str += ';\n'
        
        dot_str += "}"
        return dot_str

    def save_graph_visualization(self, filename: str = "graph.png"):
        """
        Saves a visualization of the graph to a file.
        Requires graphviz to be installed.
        """
        try:
            from graphviz import Source
            dot_str = self.visualize_graph()
            src = Source(dot_str)
            src.render(filename, format='png', cleanup=True)
            print(f"Graph visualization saved to {filename}.png")
        except ImportError:
            print("graphviz is not installed. Please install it to use this feature.")

    def __str__(self):
        return f"AgenticGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, executions={len(self.execution_ids)})"

    def __repr__(self):
        return self.__str__()