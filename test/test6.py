# file: test_agentgraph.py


import os
import sys
sys.path.append('/root/nightsky/NightSky')


import json
from function_registry import register_function, list_registered_functions
from json_to_agentgraph_parser import parse_json_to_graphs

# Define some example functions
@register_function
def process_data_1(input_data):
    return {"result": f"Processed in function 1: {input_data}"}

@register_function
def process_data_2(input_data):
    return {"result": f"Processed in function 2: {input_data}"}

# Define a function with the same name in a different module
@register_function
def process_data_1(input_data):
    return {"result": f"Processed in function 1 (alternate): {input_data}"}

# Create a sample JSON configuration
sample_config = {
    "graph1": {
        "graph_id": "graph1",
        "chat_id": "chat1",
        "data_schema": {
            "type": "object",
            "properties": {
                "common_key": {"type": "string"},
                "graph1_key": {"type": "string"}
            },
            "required": ["common_key"]
        },
        "nodes": [
            {"id": "Start", "type": "start"},
            {
                "id": "Node1",
                "type": "function",
                "function": {
                    "function": "process_data_1",
                    "module": "__main__"
                }
            },
            {
                "id": "Node2",
                "type": "function",
                "function": {
                    "function": "process_data_2"
                }
            },
            {"id": "End", "type": "end"}
        ],
        "edges": [
            {"source": "Start", "target": "Node1"},
            {"source": "Node1", "target": "Node2"},
            {"source": "Node2", "target": "End"}
        ]
    }
}

# Write the sample configuration to a JSON file
with open("sample_config.json", "w") as f:
    json.dump(sample_config, f, indent=2)

# Test the parser and graph creation
def test_agentgraph():
    print("Registered functions:")
    print(list_registered_functions())

    graphs = parse_json_to_graphs("sample_config.json")
    
    print("\nCreated graphs:")
    for graph_id, graph in graphs.items():
        print(f"Graph: {graph_id}")
        print(f"Nodes: {list(graph.nodes.keys())}")
        print(f"Edges: {graph.edges}")
    
    # Test graph execution
    initial_data = {"common_key": "initial_value", "graph1_key": "graph1_value"}
    graphs['graph1'].execute(initial_data)
    
    print("\nExecution results:")
    for node, data in graphs['graph1'].get_graph_data().items():
        print(f"Node {node}: {data}")

if __name__ == "__main__":
    test_agentgraph()