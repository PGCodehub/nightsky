import os
import sys
sys.path.append('/root/nightsky/NightSky')

from AgentGraph import AgenticGraph, StartNode, EndNode
from agent_state import AgentState, SearchStrategy, SearchPhrase , FirecrawlState
from typing import Dict, Any, List

from agents import search_strategy_planner , execute_tavily_search , researcher , firecrawl_scrape , reporter , reviewer

def create_search_workflow_graph() -> AgenticGraph:
    graph = AgenticGraph(graph_id="search_workflow", data_schema=AgentState)

    # Add nodes
    graph.add_node(StartNode())
    graph.add_node("SearchStrategyPlanner", search_strategy_planner, is_agent=True)
    graph.add_node("ExecuteTavilySearch", execute_tavily_search, is_agent=False)  # This is a tool node
    graph.add_node("Researcher", researcher, is_agent=True)
    graph.add_node("FirecrawlScrape", firecrawl_scrape, is_agent=False)  # This is a tool node
    graph.add_node("Reporter", reporter, is_agent=True)
    graph.add_node("Reviewer", reviewer, is_agent=True)  # New Reviewer node
    graph.add_node(EndNode())

    # Add edges
    graph.add_edge("Start", "SearchStrategyPlanner")
    graph.add_edge("SearchStrategyPlanner", "ExecuteTavilySearch")
    graph.add_edge("ExecuteTavilySearch", "Researcher")

    # Add conditional edge for FirecrawlScrape
    def needs_scraping(input_data):
        state = FirecrawlState(**input_data.get('firecrawl_state', {}))
        return len(state.scrapelist) > 0

    graph.add_branching_edge(
        "Researcher",
        condition=needs_scraping,
        branches={
            True: "FirecrawlScrape",
            False: "Reporter"
        }
    )

    graph.add_edge("FirecrawlScrape", "Researcher", is_required=False)
    graph.add_edge("Reporter", "Reviewer")

    # Add conditional edge from Reviewer to other nodes
    def review_decision(input_data):
        state = AgentState(**input_data.get('Reviewer', {}))
        return state.next_agent

    graph.add_branching_edge(
        "Reviewer",
        condition=review_decision,
        branches={
            "SearchStrategyPlanner": "SearchStrategyPlanner",
            "Researcher": "Researcher",
            "Reporter": "Reporter",
            "End": "End"
        }
    )

    return graph

# Example usage
if __name__ == "__main__":
    graph = create_search_workflow_graph()
    
    # Log the initial data
    initial_data_dict = {
        "input_query": "What are the latest developments in quantum computing?",
        "search_strategy": SearchStrategy(
            search_phrases=[],
            additional_information=""
        ),
        "tavily_state": {},  # Ensure this is provided
        "firecrawl_state": {}  # Ensure this is provided
    }
    print("Initial data being passed to AgentState:", initial_data_dict)

    initial_data = AgentState(**initial_data_dict)  # Unpack the dictionary
    
    graph.execute(initial_data.dict())
    
    final_state = graph.get_graph_data()
    print(final_state.keys())
    
    # print("Final search strategy:", final_state.get("SearchStrategyPlanner", {}).get("search_strategy"))
    # print("Search state:", final_state.get("SearchStrategyPlanner", {}).get("search_state"))
    # print("Scraper state:", final_state.get("SearchStrategyPlanner", {}).get("scraper_state"))