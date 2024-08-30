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
    products: List[str] = Field(default_factory=list)
    analyses: List[ProductAnalysis] = Field(default_factory=list)
    strategies: List[MarketingStrategy] = Field(default_factory=list)

# Existing functions (updated as needed)

def market_analyst(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = WorkflowState(**(input_data.get('Start', {})))

    system_prompt = """As the Lead Market Analyst at a premier digital marketing firm, you specialize in dissecting online business landscapes. Your goal:
    Conduct amazing analysis of the products and competitors, providing in-depth
    insights to guide marketing strategies. Include market size and target audience in your analysis."""

    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for product in state.products:
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
    state = WorkflowState(**(input_data.get('MarketAnalyst', {})))

    system_prompt = """You are the Chief Marketing Strategist at a leading digital marketing agency, known for crafting bespoke strategies that drive success. Your goal:
    Synthesize amazing insights from product analysis to formulate incredible
    marketing strategies."""

    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for analysis in state.analyses:
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
    state = WorkflowState(**(input_data.get('MarketingStrategist', {})))

    system_prompt = """As a Niche Market Specialist, your expertise lies in tailoring strategies for products with smaller, highly specific target audiences. Your goal:
    Refine the existing marketing strategies to better suit niche markets and specialized consumer groups."""

    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for analysis, strategy in zip(state.analyses, state.strategies):
        if analysis.market_size == "Small" or "niche" in analysis.target_audience.lower():
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

# New function for NonNicheMarketSpecialist
def non_niche_market_specialist(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = WorkflowState(**(input_data.get('MarketingStrategist', {})))

    system_prompt = """As a Broad Market Specialist, your expertise lies in optimizing strategies for products with larger, more diverse target audiences. Your goal:
    Enhance the existing marketing strategies to maximize reach and impact in broader markets."""

    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in agentic_memory[-5:]])

    for analysis, strategy in zip(state.analyses, state.strategies):
        if analysis.market_size == "Large" or "general" in analysis.target_audience.lower():
            existing_enhanced_strategy = next((msg for msg in reversed(agentic_memory) if msg['role'] == 'assistant' and f"Enhanced strategy for {analysis.product_name}" in msg['content']), None)

            if existing_enhanced_strategy:
                print(f"Using existing enhanced strategy for {analysis.product_name}")
                enhanced_strategy = existing_enhanced_strategy['content']
            else:
                print(f"Generating new enhanced strategy for {analysis.product_name}")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Previous context:\n{context}\n\nEnhance this strategy for a broad market:\nProduct: {analysis.product_name}\nAnalysis: {analysis.analysis}\nCurrent Strategy: {strategy.strategy}"}
                    ]
                )
                enhanced_strategy = response.choices[0].message.content

            strategy.strategy = enhanced_strategy

    metahistory = MessageDict(
        role="assistant",
        content=f"Enhanced strategies for broad markets",
        result=len([s for s in state.strategies if "broad" in s.strategy.lower()]),
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}

def strategy_review(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = WorkflowState(**(input_data.get('NicheMarketSpecialist', {}) or input_data.get('NonNicheMarketSpecialist', {})))

    review = "Strategy Review:\n\n"
    for strategy in state.strategies:
        review += f"Product: {strategy.product_name}\n"
        review += f"Strategy Summary: {strategy.strategy[:100]}...\n"
        review += "Review: This strategy has been optimized and aligns with our marketing goals.\n\n"

    metahistory = MessageDict(
        role="assistant",
        content=f"Reviewed {len(state.strategies)} strategies",
        result=review,
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}

def final_report(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    marketing_strategy_state = WorkflowState(**(input_data.get('MarketingStrategist', {})))
    strategy_review_state = WorkflowState(**(input_data.get('StrategyReview', {})))

    all_strategies = marketing_strategy_state.strategies + strategy_review_state.strategies

    report = f"Final Marketing Report:\n\n"
    for strategy in all_strategies:
        report += f"Product: {strategy.product_name}\n"
        report += f"Strategy: {strategy.strategy[:100]}...\n\n"

    if any("niche" in s.strategy.lower() for s in strategy_review_state.strategies):
        report += "Note: Niche market strategies have been included and optimized.\n"
    else:
        report += "Note: Strategies have been optimized for broad market appeal.\n"

    state = WorkflowState(
        products=marketing_strategy_state.products,
        analyses=marketing_strategy_state.analyses,
        strategies=all_strategies
    )

    metahistory = MessageDict(
        role="assistant",
        content=f"Generated final report for {len(all_strategies)} strategies",
        result=report,
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}

# Conditional function for branching
def is_niche_market(graph_data: Dict[str, Dict[str, Any]]) -> bool:
    node_name = next(iter(graph_data))
    node_state = graph_data[node_name]
    
    if not isinstance(node_state, dict):
        return False
    
    state = WorkflowState(**node_state)
    return any(analysis.market_size == "Small" or "niche" in analysis.target_audience.lower() for analysis in state.analyses)

# Test function
def test_marketing_workflow():
    initial_state = WorkflowState(products=["Smartphone", "Smart Watch", "Custom Mechanical Keyboard"])

    graph = AgenticGraph(graph_id="marketing_workflow", data_schema=WorkflowState)

    # Add nodes
    graph.add_node(StartNode())
    graph.add_node("MarketAnalyst", market_analyst, is_agent=True)
    graph.add_node("MarketingStrategist", marketing_strategist, is_agent=True)
    graph.add_node("NicheMarketSpecialist", niche_market_specialist, is_agent=True)
    graph.add_node("NonNicheMarketSpecialist", non_niche_market_specialist, is_agent=True)
    graph.add_node("StrategyReview", strategy_review, is_agent=True)
    graph.add_node("FinalReport", final_report, is_agent=True)
    graph.add_node(EndNode())

    # Add edges
    graph.add_edge("Start", "MarketAnalyst")
    graph.add_edge("MarketAnalyst", "MarketingStrategist")

    # Add branching edge
    graph.add_branching_edge(
        "MarketingStrategist",
        condition=is_niche_market, 
        branches={
            True: "NicheMarketSpecialist",
            False: "NonNicheMarketSpecialist"
        }
    )
    
    graph.add_edge("NicheMarketSpecialist", "StrategyReview")
    graph.add_edge("NonNicheMarketSpecialist", "StrategyReview")
    graph.add_edge("MarketingStrategist", "FinalReport", is_required=True)
    graph.add_edge("StrategyReview", "FinalReport", is_required=True)
    graph.add_edge("FinalReport", "End")

    print("Graph structure and dependencies:")
    for node_id, node in graph.nodes.items():
        print(f"Node: {node_id}")
        previous_nodes = graph.get_previous_nodes(node)
        print(f"  Previous nodes: {[prev.name for prev in previous_nodes]}")
        required_deps = graph.required_dependencies.get(node_id, set())
        print(f"  Required dependencies: {required_deps}")

    print("Executing the marketing workflow...")
    graph.execute(initial_data=initial_state.dict())

    # Test getting execution data
    execution_id = graph.current_execution_id
    execution_data = {
        "metahistory": graph.get_metahistory(),
        "agentic_memory": {agent_id: graph.get_agentic_memory(agent_id) for agent_id in graph.agent_ids},
        "node_graph_state": graph.get_node_graph_state()
    }
    print("\nExecution Data:")
    print(f"Metahistory entries: {len(execution_data['metahistory'][1])}")
    print(f"Agentic memory entries: {sum(len(mem) for mem in execution_data['agentic_memory'].values())}")
    print(f"Node graph state entries: {len(execution_data['node_graph_state'])}")

    
    # Print agent memories
    print("\nAgent Memories:")
    for agent_id in graph.agent_ids:
        print(f"\nAgent {agent_id}:")
        for message in graph.get_agentic_memory(agent_id):
            print(f"- {message['role']}: {message['content'][:50]}...")


    # Print the final report
    final_report_node = graph.nodes.get("FinalReport")
    if final_report_node:
        final_report_data = graph.node_graph_state[graph.chat_id].get("FinalReport", {})
        if final_report_data:
            print("\nFinal Marketing Report:")
            print(final_report_data.get("result", "No final report generated."))
        else:
            print("\nNo final report data available.")
    else:
        print("\nFinal Report node not found in the graph.")

if __name__ == "__main__":
    test_marketing_workflow()