import json
from typing import Dict, Any, Optional
from pydantic import create_model, Field
from AgentGraph import AgenticGraph, StartNode, EndNode
from function_registry import load_registered_function
import random
import string

def create_data_schema(schema_dict: Dict[str, Any]):
    """Create a Pydantic model from the schema dictionary."""
    type_mapping = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        'array': list,
        'object': dict,
        # Add other type mappings as needed
    }
    
    def get_type(type_info: Dict[str, Any]):
        if isinstance(type_info['type'], list):
            return Optional[type_mapping[type_info['type'][0]]]
        return type_mapping[type_info['type']]
    
    fields = {}
    for k, v in schema_dict['properties'].items():
        field_type = get_type(v)
        default = v.get('default', ... if v.get('required', False) else None)
        fields[k] = (field_type, Field(default=default))
    
    return create_model('DataSchema', **fields)

def generate_dummy_data(schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Generate dummy data based on the schema."""
    dummy_data = {}
    for key, value in schema_dict['properties'].items():
        if 'default' in value:
            dummy_data[key] = value['default']
        elif value['type'] == 'string':
            dummy_data[key] = ''.join(random.choices(string.ascii_letters, k=10))
        elif value['type'] == 'integer':
            dummy_data[key] = random.randint(0, 100)
        elif value['type'] == 'number':
            dummy_data[key] = random.uniform(0, 100)
        elif value['type'] == 'boolean':
            dummy_data[key] = random.choice([True, False])
        elif value['type'] == 'array':
            dummy_data[key] = []
        elif value['type'] == 'object':
            dummy_data[key] = generate_dummy_data(value)
        else:
            dummy_data[key] = None
    return dummy_data

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
                function = load_registered_function(node['function']['function'], node['function'].get('module'))
                graph.add_node(node['id'], function, is_agent=node.get('is_agent', False))
        
        # Add edges
        for edge in graph_config['edges']:
            if isinstance(edge['target'], dict):
                condition = lambda input_data, edge=edge: next(
                    (cond['condition'] for target, cond in edge['target'].items() if eval(cond['condition'], {'state': input_data})),
                    None
                )
                branches = {target: target for target in edge['target'].keys()}
                graph.add_branching_edge(edge['source'], condition=condition, branches=branches)
            else:
                graph.add_edge(edge['source'], edge['target'], is_required=edge.get('is_required', True))
        
        # Generate dummy input data
        dummy_input_data = generate_dummy_data(graph_config['data_schema'])
        
        # Store the graph object and dummy input data
        graphs[graph_id] = {
            'graph': graph,
            'dummy_input_data': dummy_input_data
        }
    
    # Connect graphs
    for graph_id, graph_config in config.items():
        for connected_graph_id in graph_config.get('connected_graphs', []):
            graphs[graph_id]['graph'].connect_graph(graphs[connected_graph_id]['graph'])
    
    return graphs

# Example usage
if __name__ == "__main__":
    graphs = parse_json_to_graphs("path_to_your_json_file.json")
    
    # Now you can use these graphs with their dummy input data, for example:
    for graph_id, graph_data in graphs.items():
        print(f"Executing graph: {graph_id}")
        graph_data['graph'].execute(graph_data['dummy_input_data'])