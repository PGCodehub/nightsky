"""
NightSky AgentGraph - Quick Start Example
==========================================

This example demonstrates the basic usage of NightSky AgentGraph:
1. Creating a simple workflow
2. Adding nodes and edges
3. Executing the graph
4. Retrieving results
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# Import NightSky components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from NightSky.AgentGraph import AgenticGraph, StartNode, EndNode, MessageDict


# Step 1: Define your data schema
class SimpleWorkflowState(BaseModel):
    """Define the structure of data flowing through your graph"""
    message: str
    counter: int = 0
    results: List[str] = Field(default_factory=list)


# Step 2: Define node functions
def process_message(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    A simple processing node that transforms the message
    
    Args:
        input_data: Dictionary containing outputs from previous nodes
                   Key = node name, Value = node output
    
    Returns:
        Dictionary with 'graph_data' and 'metahistory'
    """
    # Access data from the Start node
    start_data = input_data.get("Start", {})
    
    # Process the data
    message = start_data.get("message", "")
    processed_message = message.upper()
    
    result = {
        "message": processed_message,
        "counter": 1,
        "results": [f"Processed: {processed_message}"]
    }
    
    print(f"✓ ProcessMessage: {message} -> {processed_message}")
    
    return {"graph_data": result, "metahistory": None}


def analyze_message(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    An analysis node that counts words and characters
    """
    # Access data from ProcessMessage node
    process_data = input_data.get("ProcessMessage", {})
    
    message = process_data.get("message", "")
    word_count = len(message.split())
    char_count = len(message)
    
    result = {
        "message": message,
        "counter": process_data.get("counter", 0) + 1,
        "results": process_data.get("results", []) + [
            f"Analysis: {word_count} words, {char_count} characters"
        ]
    }
    
    print(f"✓ AnalyzeMessage: {word_count} words, {char_count} chars")
    
    return {"graph_data": result, "metahistory": None}


def agent_responder(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    An agent node with memory that can track conversation history
    
    Args:
        input_data: Dictionary containing outputs from previous nodes
        agentic_memory: List of previous messages (agent's memory)
    
    Returns:
        Dictionary with 'graph_data' and 'metahistory'
    """
    # Access data from previous node
    analyze_data = input_data.get("AnalyzeMessage", {})
    
    # Check if we have previous context
    memory_context = ""
    if agentic_memory:
        memory_context = f" (I remember {len(agentic_memory)} previous interactions)"
    
    response = f"Acknowledged: {analyze_data.get('message', '')}{memory_context}"
    
    result = {
        "message": response,
        "counter": analyze_data.get("counter", 0) + 1,
        "results": analyze_data.get("results", []) + [
            f"Agent response: {response}"
        ]
    }
    
    print(f"✓ AgentResponder: Generated response with {len(agentic_memory)} memory items")
    
    # Update agent memory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=result,
        agent_msgs=[
            {"role": "user", "content": analyze_data.get("message", "")},
            {"role": "assistant", "content": response}
        ]
    )
    
    return {"graph_data": result, "metahistory": metahistory}


async def main():
    """Main function demonstrating graph creation and execution"""
    
    print("=" * 60)
    print("NightSky AgentGraph - Quick Start Example")
    print("=" * 60)
    
    # Step 3: Create the graph
    print("\n📊 Creating graph...")
    graph = AgenticGraph(
        graph_id="quickstart_example",
        data_schema=SimpleWorkflowState,
        max_parallel=3
    )
    
    # Step 4: Add nodes
    print("➕ Adding nodes...")
    graph.add_node(StartNode())
    graph.add_node("ProcessMessage", process_message)
    graph.add_node("AnalyzeMessage", analyze_message)
    graph.add_node("AgentResponder", agent_responder, is_agent=True)
    graph.add_node(EndNode())
    
    # Step 5: Connect nodes with edges
    print("🔗 Connecting nodes...")
    graph.add_edge("Start", "ProcessMessage")
    graph.add_edge("ProcessMessage", "AnalyzeMessage")
    graph.add_edge("AnalyzeMessage", "AgentResponder")
    graph.add_edge("AgentResponder", "End")
    
    print(f"   Graph has {len(graph.nodes)} nodes and {len(graph.edges)} edge connections")
    
    # Step 6: Execute the graph (First run)
    print("\n🚀 Executing graph (First run)...")
    print("-" * 60)
    initial_data = {
        "message": "Hello NightSky!",
        "counter": 0,
        "results": []
    }
    
    await graph.execute(initial_data, chat_id="demo_session")
    
    # Step 7: Get results
    print("-" * 60)
    print("\n📋 Results from first run:")
    final_state = graph.get_graph_data()
    print(f"   Final message: {final_state.get('message', 'N/A')}")
    print(f"   Processing steps: {final_state.get('counter', 0)}")
    print(f"   Results:")
    for result in final_state.get('results', []):
        print(f"      - {result}")
    
    # Step 8: Check agent memory
    print("\n🧠 Agent Memory:")
    if graph.agent_ids:
        agent_id = graph.agent_ids[0]
        memory = graph.get_agentic_memory(agent_id)
        print(f"   Agent has {len(memory)} messages in memory")
        for msg in memory:
            print(f"      - {msg['role']}: {msg['content']}")
    
    # Step 9: Execute again to demonstrate memory persistence
    print("\n" + "=" * 60)
    print("🚀 Executing graph (Second run with same chat_id)...")
    print("-" * 60)
    second_data = {
        "message": "This is the second execution",
        "counter": 0,
        "results": []
    }
    
    await graph.execute(second_data, chat_id="demo_session")
    
    # Step 10: Check updated memory
    print("-" * 60)
    print("\n🧠 Updated Agent Memory:")
    if graph.agent_ids:
        agent_id = graph.agent_ids[0]
        memory = graph.get_agentic_memory(agent_id)
        print(f"   Agent now has {len(memory)} messages in memory")
        for msg in memory:
            print(f"      - {msg['role']}: {msg['content'][:50]}...")
    
    # Step 11: Get execution history
    print("\n📜 Execution History:")
    metahistory, entry_order = graph.get_metahistory(chat_id="demo_session")
    print(f"   Total executions: {len(entry_order)}")
    print(f"   Execution IDs tracked: {len(set(m.execution_id for m in metahistory.values()))}")
    
    print("\n" + "=" * 60)
    print("✅ Quick Start Example Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Try modifying the node functions")
    print("  2. Add conditional branching with add_branching_edge()")
    print("  3. Create multiple graphs and connect them")
    print("  4. Explore parallel execution with multiple paths")
    print("  5. Check out more examples in the test/ directory")


if __name__ == "__main__":
    asyncio.run(main())

