import openai
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import os

import os
import sys
sys.path.append('/root/nightsky/NightSky')

from AgentGraph import AgenticGraph , MessageDict , StartNode , EndNode
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict, Tuple, Type, TypeVar
from pydantic import BaseModel, Field
import json

# # Set up OpenAI client
openapi_key = "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"

client = openai.OpenAI(api_key=openapi_key)


class ProductAnalysis(BaseModel):
    product_name: str
    analysis: str
    market_size: str
    target_audience: str

class MarketingStrategy(BaseModel):
    product_name: str
    strategy: str

class WorkflowState(BaseModel):
    products: List[str]
    analyses: List[ProductAnalysis] = Field(default_factory=list)
    strategies: List[MarketingStrategy] = Field(default_factory=list)

# Updated agent functions
def market_analyst(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Get the state from the input data
    
    state = WorkflowState(**(input_data.get('Start', {})))

    system_prompt = """As the Lead Market Analyst at a premier digital marketing firm, you specialize in dissecting online business landscapes. Your goal:
    Conduct amazing analysis of the products and competitors, providing in-depth
    insights to guide marketing strategies. Include market size and target audience in your analysis."""

    # Use agentic memory to provide context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for product in state.products:
        # Check if analysis for this product already exists in memory
        existing_analysis = next((msg for msg in reversed(agentic_memory) if msg['role'] == 'assistant' and product in msg['content']), None)

        if existing_analysis:
            print(f"Using existing analysis for {product}")
            analysis = existing_analysis['content']
        else:
            print(f"Generating new analysis for {product}")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Previous context:\n{context}\n\nAnalyze the product: {product}"}
                ]
            )
            analysis = response.choices[0].message.content

        # Extract market size and target audience from the analysis
        # For simplicity, we're using placeholder logic here. In a real scenario, you'd want to parse the analysis text.
        market_size = "Large" if "large market" in analysis.lower() else "Small"
        target_audience = "General consumers" if "general" in analysis.lower() else "Niche market"

        state.analyses.append(ProductAnalysis(
            product_name=product,
            analysis=analysis,
            market_size=market_size,
            target_audience=target_audience
        ))

    metahistory = MessageDict(
        role="assistant",
        content=f"Analyzed {len(state.products)} products",
        result=len(state.analyses),
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}

def marketing_strategist(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Get the state from the input data
    state = WorkflowState(**(input_data.get('MarketAnalyst', {})))

    system_prompt = """You are the Chief Marketing Strategist at a leading digital marketing agency, known for crafting bespoke strategies that drive success. Your goal:
    Synthesize amazing insights from product analysis to formulate incredible
    marketing strategies."""

    # Use agentic memory to provide context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for analysis in state.analyses:
        # Check if strategy for this product already exists in memory
        existing_strategy = next((msg for msg in reversed(agentic_memory) if msg['role'] == 'assistant' and analysis.product_name in msg['content']), None)

        if existing_strategy:
            print(f"Using existing strategy for {analysis.product_name}")
            strategy = existing_strategy['content']
        else:
            print(f"Generating new strategy for {analysis.product_name}")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Previous context:\n{context}\n\nCreate a marketing strategy based on this analysis: {analysis.analysis}"}
                ]
            )
            strategy = response.choices[0].message.content

        state.strategies.append(MarketingStrategy(product_name=analysis.product_name, strategy=strategy))

    metahistory = MessageDict(
        role="assistant",
        content=f"Created strategies for {len(state.analyses)} products",
        result=len(state.strategies),
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}

def niche_market_specialist(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Get the state from the input data
    state = WorkflowState(**(input_data.get('MarketingStrategist', {})))

    system_prompt = """As a Niche Market Specialist, your expertise lies in tailoring strategies for products with smaller, highly specific target audiences. Your goal:
    Refine the existing marketing strategies to better suit niche markets and specialized consumer groups."""

    # Use agentic memory to provide context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for analysis, strategy in zip(state.analyses, state.strategies):
        if analysis.market_size == "Small" and "niche" in analysis.target_audience.lower():
            # Check if refined strategy for this product already exists in memory
            existing_refined_strategy = next((msg for msg in reversed(agentic_memory) if msg['role'] == 'assistant' and f"Refined strategy for {analysis.product_name}" in msg['content']), None)

            if existing_refined_strategy:
                print(f"Using existing refined strategy for {analysis.product_name}")
                refined_strategy = existing_refined_strategy['content']
            else:
                print(f"Generating new refined strategy for {analysis.product_name}")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Previous context:\n{context}\n\nRefine this strategy for a niche market:\nProduct: {analysis.product_name}\nAnalysis: {analysis.analysis}\nCurrent Strategy: {strategy.strategy}"}
                    ]
                )
                refined_strategy = response.choices[0].message.content

            strategy.strategy = refined_strategy

    metahistory = MessageDict(
        role="assistant",
        content=f"Refined strategies for niche markets",
        result=len([s for s in state.strategies if "niche" in s.strategy.lower()]),
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}

# Conditional function for branching
def is_niche_market(graph_data: Dict[str, Any]) -> bool:
    state = WorkflowState(**graph_data)
    return any(analysis.market_size == "Small" and "niche" in analysis.target_audience.lower() for analysis in state.analyses)

# New function to demonstrate error handling
def error_prone_function(input_data: Dict[str, Any]) -> Dict[str, Any]:
    if random.random() < 0.5:  # 50% chance of error
        raise ExecutionError("Simulated error in error_prone_function")
    return {"graph_data": input_data, "metahistory": None}

# Test function
def test_marketing_workflow():
    initial_state = WorkflowState(products=["Smartphone","Smart Watch"])

    graph = AgenticGraph(initial_state.dict(), chat_id="marketing_workflow")

    # Add nodes
    graph.add_node(StartNode())
    graph.add_node("MarketAnalyst", market_analyst, is_agent=True)
    graph.add_node("MarketingStrategist", marketing_strategist, is_agent=True)
    graph.add_node("NicheMarketSpecialist", niche_market_specialist, is_agent=True)
    # graph.add_node("ErrorProneNode", error_prone_function)
    graph.add_node(EndNode())

    # Add edges
    graph.add_edge("Start", "MarketAnalyst")
    graph.add_edge("MarketAnalyst", "MarketingStrategist")
    graph.add_edge("MarketingStrategist", "NicheMarketSpecialist")

    # # Add branching edge
    # graph.add_branching_edge(
    #     "ErrorProneNode",
    #     condition=is_niche_market, 
    #     branches={
    #         True: "NicheMarketSpecialist",
    #         False: "End"
    #     }
    # )
    graph.add_edge("NicheMarketSpecialist", "End")

    print("Graph structure and dependencies:")
    for node_id, node in graph.nodes.items():
        print(f"Node: {node_id}")
        previous_nodes = graph.get_previous_nodes(node)
        print(f"  Previous nodes: {[prev.name for prev in previous_nodes]}")
        required_deps = graph.required_dependencies.get(node_id, set())
        print(f"  Required dependencies: {required_deps}")


    print("Executing the marketing workflow...")
    graph.execute()  # Test parallel execution

    # Test graph visualization
    # graph.save_graph_visualization("marketing_workflow_graph.png")

    # Test getting execution data
    execution_id = graph.get_execution_ids()[-1]
    execution_data = graph.get_execution_data(execution_id)
    print("\nExecution Data:")
    print(f"Metahistory entries: {len(execution_data['metahistory'][1])}")
    print(f"Agentic memory entries: {sum(len(mem) for mem in execution_data['agentic_memory'].values())}")
    print(f"Node graph state entries: {len(execution_data['node_graph_state'])}")

    # Test stopping and resuming execution
    # print("\nTesting stop and resume functionality...")
    # graph.stop_at_current_node()
    # current_node = graph.get_current_node()
    # print(f"Stopped at node: {current_node.name if current_node else 'None'}")
    # graph.resume_execution()
    # graph.execute()  # Continue execution

    # Print final results
    # final_state = WorkflowState(**graph.get_graph_data())
    # print("\nFinal Workflow State:")
    # print(f"Products analyzed: {len(final_state.products)}")
    # print(f"Analyses created: {len(final_state.analyses)}")
    # print(f"Strategies developed: {len(final_state.strategies)}")

    # # Print agent memories
    # print("\nAgent Memories:")
    # for agent_id in graph.agent_ids:
    #     print(f"\nAgent {agent_id}:")
    #     for message in graph.get_agentic_memory(agent_id):
    #         print(f"- {message['role']}: {message['content'][:50]}...")

    # # Test multiple executions
    # print("\nRunning the workflow again to demonstrate memory usage...")
    # graph.execute()

    # # Print updated agent memories
    # print("\nUpdated Agent Memories after second run:")
    # for agent_id in graph.agent_ids:
    #     print(f"\nAgent {agent_id}:")
    #     for message in graph.get_agentic_memory(agent_id):
    #         print(f"- {message['role']}: {message['content'][:50]}...")

if __name__ == "__main__":
    test_marketing_workflow()