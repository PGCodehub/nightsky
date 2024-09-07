import json
from typing import Dict, Any
from pydantic import create_model
from AgentGraph import AgenticGraph, StartNode, EndNode
from function_registry import load_registered_function

def create_data_schema(schema_dict: Dict[str, Any]):
    """Create a Pydantic model from the schema dictionary."""
    type_mapping = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        # Add other type mappings as needed
    }
    
    def get_type(type_name: str):
        if type_name in type_mapping:
            return type_mapping[type_name]
        else:
            raise ValueError(f"Unsupported type: {type_name}")
    
    return create_model('DataSchema', **{
        k: (get_type(v['type']), ... if k in schema_dict.get('required', []) else None)
        for k, v in schema_dict['properties'].items()
    })

def load_function(function_info: Dict[str, str]):
    """Load a function based on the information in the JSON."""
    function_name = function_info['function']
    module_name = function_info.get('module')
    return load_registered_function(function_name, module_name)

def parse_json_to_graphs(json_file: str) -> Dict[str, AgenticGraph]:
    with open(json_file, 'r') as f:
        config = json.load(f)
    
    graphs = {}
    
    for graph_id, graph_config in config.items():
        data_schema = create_data_schema(graph_config['data_schema'])
        graph = AgenticGraph(
            graph_id=graph_config['graph_id'],
            chat_id=graph_config.get('chat_id'),
            data_schema=data_schema
        )
        
        # Add nodes
        for node in graph_config['nodes']:
            if node['type'] == 'start':
                graph.add_node(StartNode(node['id']))
            elif node['type'] == 'end':
                graph.add_node(EndNode(node['id']))
            else:
                function = load_function(node['function'])
                graph.add_node(node['id'], function)
        
        # Store the graph object
        graphs[graph_id] = graph
    
    # Add edges and connect graphs
    for graph_id, graph_config in config.items():
        graph = graphs[graph_id]
        
        for edge in graph_config['edges']:
            if isinstance(edge['target'], dict):
                target_graph = graphs[edge['target']['graph_id']]
                graph.add_edge(edge['source'], (edge['target']['graph_id'], edge['target']['node_id']))
            else:
                graph.add_edge(edge['source'], edge['target'])
        
        for connected_graph_id in graph_config.get('connected_graphs', []):
            graph.connect_graph(graphs[connected_graph_id])
    
    return graphs

# Usage
if __name__ == "__main__":
    graphs = parse_json_to_graphs("path_to_your_json_file.json")
    
    # Now you can use these graphs, for example:
    initial_data = {"common_key": "initial_value", "graph1_key": "graph1_value", "graph2_key": "graph2_value"}
    graphs['graph1'].execute(initial_data)