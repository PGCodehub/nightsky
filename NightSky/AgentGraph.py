from typing import Any, Callable, Dict, List, Optional, Union, Tuple, Type
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

class Node:
    def __init__(self, name: str, function: Callable, is_agent: bool = False, agent_schema: Type[AgentSchema] = AgentSchema):
        self.id = name
        self.name = name
        self.function = function
        self.is_agent = is_agent
        self.agent_id = str(uuid.uuid4()) if is_agent else None
        self.agent_schema = agent_schema if is_agent else None
    
    def execute(self, graph_data: Any, agentic_memory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            if self.is_agent and agentic_memory is not None:
                result = self.function(graph_data, agentic_memory)
            else:
                result = self.function(graph_data)
            
            if isinstance(result, dict) and "graph_data" in result and "metahistory" in result:
                return result
            else:
                return {"graph_data": result, "metahistory": None}
        except Exception as e:
            raise ExecutionError(f"Error executing node {self.name}: {str(e)}")

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

class AgenticGraph:
    def __init__(self, initial_data: Any, chat_id: Optional[str] = None):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Union[List[Tuple[str, Optional[Callable[[Any], bool]]]], FlexibleBranch]] = {}
        self.start_node: Optional[StartNode] = None
        self.end_nodes: List[EndNode] = []
        self.current_node: Optional[Node] = None
        self.stop_execution: bool = False
        self.graph_data: Any = initial_data
        self.chat_id: str = chat_id or str(id(self))
        self.metahistory: Dict[str, Tuple[Dict[str, MessageDict], List[str]]] = {self.chat_id: ({}, [])}
        self.agent_ids: List[str] = []
        self.agentic_memory: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_schemas: Dict[str, Type[AgentSchema]] = {}
        
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

    def add_edge(self, source_id: str, target_id: str, condition: Optional[Callable[[Any], bool]] = None):
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist in the graph")
        if target_id not in self.nodes:
            raise ValueError(f"Target node '{target_id}' does not exist in the graph")
        
        if source_id not in self.edges:
            self.edges[source_id] = []
        
        self.edges[source_id].append((target_id, condition))

    def add_branching_edge(self, source_id: str, condition: Callable[[Any], Any], branches: Dict[Any, Union[str, List[str]]]):
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist in the graph")
        
        for target in branches.values():
            if isinstance(target, str):
                if target not in self.nodes:
                    raise ValueError(f"Target node '{target}' does not exist in the graph")
            elif isinstance(target, list):
                for node in target:
                    if node not in self.nodes:
                        raise ValueError(f"Target node '{node}' does not exist in the graph")
            else:
                raise ValueError("Branch target must be either a string (node name) or a list of strings")
        
        self.edges[source_id] = FlexibleBranch(condition, branches)

    def get_next_nodes(self, current_node: Node, graph_data: Any) -> List[Node]:
        edge = self.edges.get(current_node.id)
        if isinstance(edge, FlexibleBranch):
            condition_result = edge.condition(graph_data)
            next_node_ids = edge.branches.get(condition_result, [])
            if isinstance(next_node_ids, str):
                next_node_ids = [next_node_ids]
            return [self.nodes[node_id] for node_id in next_node_ids]
        elif isinstance(edge, list):
            next_nodes = []
            for target_id, condition in edge:
                if condition is None or condition(graph_data):
                    next_nodes.append(self.nodes[target_id])
            return next_nodes
        else:
            return []

    def create_agent_message(self, metahistory: MessageDict, agent_id: str) -> Dict[str, Any]:
        schema = self.agent_schemas.get(agent_id, AgentSchema)
        try:
            agent_message = schema(**metahistory.dict(exclude={'create_agent_msg', 'node_index'}))
            return agent_message.dict(exclude_unset=True)
        except ValidationError as e:
            logging.warning(f"Validation error for agent {agent_id}: {e}")
            return {"role": metahistory.role, "content": metahistory.content}

    def execute_node(self, node: Node, max_retries: int = 1) -> Any:
        for attempt in range(max_retries):
            try:
                if node.is_agent:
                    agentic_memory = self.agentic_memory.get(node.agent_id, [])
                    return node.execute(self.graph_data, agentic_memory)
                else:
                    return node.execute(self.graph_data)
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

        def execute_branch(node: Node):
            while node and not self.stop_execution:
                try:
                    self.current_node = node
                    result = self.execute_node(node)
                    self.graph_data = result["graph_data"]
                    
                    if result["metahistory"]:
                        try:
                            metahistory = MessageDict.parse_obj(result["metahistory"])
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
                        return self.graph_data
                    
                    next_nodes = self.get_next_nodes(node, self.graph_data)
                    
                    if not next_nodes:
                        logging.warning(f"No next nodes found for {node.name}")
                        return self.graph_data
                    
                    if len(next_nodes) == 1:
                        node = next_nodes[0]
                    else:
                        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                            futures = [executor.submit(execute_branch, next_node) for next_node in next_nodes[:max_parallel]]
                            results = [future.result() for future in futures]
                        return results
                
                except ExecutionError as e:
                    logging.error(f"Error: {str(e)}")
                    return None

            if self.stop_execution:
                logging.info(f"Execution stopped at node: {node.name}")
                return self.graph_data

        start_node = self.current_node if self.current_node else self.start_node
        result = execute_branch(start_node)
        logging.info("Graph execution completed.")
        return result

    def stop_at_current_node(self):
        self.stop_execution = True

    def resume_execution(self):
        self.stop_execution = False

    def get_current_node(self) -> Optional[Node]:
        return self.current_node

    def get_graph_data(self) -> Any:
        return self.graph_data

    def get_metahistory(self, chat_id: Optional[str] = None) -> Tuple[Dict[str, MessageDict], List[str]]:
        return self.metahistory[chat_id or self.chat_id]

    def get_agentic_memory(self, agent_id: str) -> List[Dict[str, Any]]:
        return self.agentic_memory.get(agent_id, [])