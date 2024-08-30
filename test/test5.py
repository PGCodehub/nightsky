import openai
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import os

import os
import sys
sys.path.append('/root/nightsky/NightSky')

from AgentGraph import AgenticGraph , MessageDict , StartNode , EndNode, DataSchema
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict, Tuple, Type, TypeVar
from pydantic import BaseModel, Field
import json

class CustomDataSchema(BaseModel):
    common_key: str
    graph1_key: Optional[str] = None
    graph2_key: Optional[str] = None

def test_inter_graph_communication():
    # Create two graphs with initial data and custom schema
    graph1 = AgenticGraph(graph_id="graph1", chat_id="chat1", data_schema=CustomDataSchema)
    graph2 = AgenticGraph(graph_id="graph2", chat_id="chat1", data_schema=CustomDataSchema)

    # Connect the graphs
    graph1.connect_graph(graph2)
    graph2.connect_graph(graph1)

    # Define nodes for graph1
    def node1_func(input_data):
        result = f"Processed in Graph 1: {input_data}"
        return {
            "graph_data": {"result": result, "common_key": "updated_by_graph1", "graph1_key": "new_graph1_value"},
            "metahistory": {
                "role": "system",
                "content": "Node1 processing complete",
                "tool_call": False,
                "result": result,
                "create_agent_msg": False
            }
        }

    def node2_func(input_data):
        result = f"Final processing in Graph 1: {input_data}"
        return {
            "graph_data": {"result": result, "common_key": "final_update_by_graph1"},
            "metahistory": {
                "role": "system",
                "content": "Node2 processing complete",
                "tool_call": False,
                "result": result,
                "create_agent_msg": False
            }
        }

    # Define nodes for graph2
    def node3_func(input_data):
        print(f"Node3 received input_data: {input_data}")
        shared_data = input_data.get("common_key", "No shared data")
        result = f"Processed in Graph 2: {shared_data}"
        return {
            "graph_data": {"result": result, "common_key": "updated_by_graph2", "graph2_key": "new_graph2_value"},
            "metahistory": {
                "role": "system",
                "content": "Node3 processing complete",
                "tool_call": False,
                "result": result,
                "create_agent_msg": False
            }
        }

    def node4_func(input_data):
        result = f"Processed in Graph 2 Node 4: {input_data}"
        return {
            "graph_data": {"result": result, "common_key": "updated_by_graph2_node4"},
            "metahistory": {
                "role": "system",
                "content": "Node4 processing complete",
                "tool_call": False,
                "result": result,
                "create_agent_msg": False
            }
        }

    def node5_func(input_data):
        result = f"Processed in Graph 2 Node 5: {input_data}"
        return {
            "graph_data": {"result": result, "common_key": "updated_by_graph2_node5"},
            "metahistory": {
                "role": "system",
                "content": "Node5 processing complete",
                "tool_call": False,
                "result": result,
                "create_agent_msg": False
            }
        }

    # Add nodes to graphs
    graph1.add_node(StartNode())
    graph1.add_node("Node1", node1_func)
    graph1.add_node("Node2", node2_func)
    graph1.add_node(EndNode())

    graph2.add_node("Node3", node3_func)
    graph2.add_node("Node4", node4_func)
    graph2.add_node("Node5", node5_func)

    # Add edges
    graph1.add_edge("Start", "Node1")
    graph1.add_edge("Node1", ("graph2", "Node3"))  # Edge from Graph1 to Graph2
    graph2.add_edge("Node3", "Node4")
    graph2.add_edge("Node4", "Node5")
    graph2.add_edge("Node5", ("graph1", "Node2"))  # Edge from Graph2 back to Graph1
    graph1.add_edge("Node2", "End")


    # Execute the workflow with initial data
    initial_data = {"common_key": "initial_value", "graph1_key": "graph1_value", "graph2_key": "graph2_value"}
    graph1.execute(initial_data)

    # Print results
    print("Graph 1 data:", graph1.get_graph_data())
    print("Graph 2 data:", graph2.get_graph_data())
    print("Graph 1 shareable data with Graph 2:", graph1.get_shareable_data("graph2", "Node1"))
    print("Graph 2 shareable data with Graph 1:", graph2.get_shareable_data("graph1", "Node5"))
    print("Graph 1 shared keys:", graph1.shared_keys)
    print("Graph 2 shared keys:", graph2.shared_keys)
    print("Graph 1 metahistory:", graph1.get_metahistory())
    print("Graph 2 metahistory:", graph2.get_metahistory())

# Add this line at the end of the file
if __name__ == "__main__":
    test_inter_graph_communication()

