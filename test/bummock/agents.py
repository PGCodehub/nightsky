import os
import sys
sys.path.append('/root/nightsky/NightSky')
from AgentGraph import MessageDict
from function_registry import register_function, list_registered_functions
from json_to_agentgraph_parser import parse_json_to_graphs


from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import openai
import json
from datetime import datetime
from prompts import *
from agent_state import AgentState , SearchStrategy , TavilySearchState , FirecrawlState , ResearchResult
from tools import tavily_search , firecrawl_scrape
from dotenv import load_dotenv
import logging
load_dotenv()

openapi_key = os.getenv("OPENAI_API_KEY")
# client = openai.OpenAI(api_key=openapi_key)

# Check if the OpenAI API key is set
if openapi_key is None:
    raise ValueError("The OPENAI_API_KEY environment variable is not set.")
    
client = openai.OpenAI(api_key=openapi_key)

@register_function
def search_strategy_planner(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = AgentState(**input_data.get('Start', {}))

    input_query = state.input_query

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": planner_prompt_template.format(input_data=input_data)},
            {"role": "user", "content": "Generate a search strategy for the reseach question {input_query}"}
        ],
        functions=[search_strategy_function],
        function_call={"name": "generate_search_strategy"}
    )

    function_call = response.choices[0].message.function_call
    strategy_json = json.loads(function_call.arguments)
    search_strategy = SearchStrategy(**strategy_json)
    state.search_strategy = search_strategy

    metahistory = MessageDict(
        role="assistant",
        content=f"Created a multi-search strategy with {len(search_strategy.search_phrases)} search phrases",
        result=search_strategy.dict(),
        create_agent_msg=True,
        tool_call=False
    )

    return {"graph_data": state.dict(), "metahistory": metahistory.dict()}



@register_function
def execute_tavily_search(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a Tavily search based on the search strategy provided by the SearchStrategyPlanner.
    This is a tool node, so it doesn't use agentic_memory.
    """
    state = input_data.get('SearchStrategyPlanner', {})
    tavily_state = TavilySearchState(**state.get('tavily_state', {}))

    #try:
    # Extract the search strategy from the state
    search_strategy = SearchStrategy(**state.get('search_strategy', {}))
    
    # Take only the first search phrase from the list
    search_query = search_strategy.search_phrases[0].phrase if search_strategy.search_phrases else ""
    
    if not search_query:
        raise ValueError("No search query provided in the search strategy")

    # Execute the Tavily search
    new_tavily_state , search_result = tavily_search(search_query, tavily_state)

    if "error" in search_result:
        raise Exception(f"Tavily search error: {search_result['error']}")

    # Update only the fields that exist in AgentState
    updated_state = {
        **state,
        'tavily_state': new_tavily_state.dict()
    }
    metahistory = MessageDict(
        role="tool",
        content=f"Executed Tavily search for query: {search_query}",
        result={"num_results": len(search_result.get('results', []))},
        create_agent_msg=False,
        tool_call=True
    )

    return {
        "graph_data": updated_state,
        "metahistory": metahistory.dict()
    }
    # except Exception as e:
    #     error_message = f"Error in execute_tavily_search: {str(e)}"
    #     metahistory = MessageDict(
    #         role="tool",
    #         content=error_message,
    #         result={"error": str(e)},
    #         create_agent_msg=False,
    #         tool_call=True
    #     )
    #     return {
    #         "graph_data": state,
    #         "metahistory": metahistory.dict()
    #     }



@register_function
def firecrawl_scrape_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scrape URLs from the scrapelist in FirecrawlState using the firecrawl_scrape function.
    """
    state = FirecrawlState(**input_data.get('firecrawl_state', {}))
    
    # Get URLs to scrape
    urls_to_scrape = state.scrapelist[:10]  # Limit to 10 URLs per iteration to avoid long-running tasks
    
    # Call the firecrawl_scrape function
    scrape_results = firecrawl_scrape(urls_to_scrape, state)
    
    # Update the state
    state = FirecrawlState(**scrape_results['state'].dict())
    
    # Remove scraped URLs from the scrapelist
    state.scrapelist = state.scrapelist[len(urls_to_scrape):]
    
    scraped_data = scrape_results['results']
    urls_scraped = len([result for result in scraped_data if result['status'] == 'success'])

    metahistory = MessageDict(
        role="tool",
        content=f"Scraped {urls_scraped} URLs using Firecrawl",
        result={"scraped_urls": urls_scraped, "remaining_urls": len(state.scrapelist)},
        create_agent_msg=False,
        tool_call=True
    )

    return {
        "graph_data": {
            "firecrawl_state": state.dict(),
            "scraped_data": scraped_data
        },
        "metahistory": metahistory.dict()
    }

def analyze_content_with_gpt4_mini(content: str, search_strategy: SearchStrategy) -> Optional[str]:
    prompt = f"""
    Analyze the following content and create a context summary under 1000 words.
    Only include relevant snippets that are directly related to the search phrases.
    If there isn't enough relevant information, return None.

    Content:
    {content[:2000]}  # Limiting to 2000 characters to avoid token limit issues

    Search phrases:
    {', '.join([phrase.phrase for phrase in search_strategy.search_phrases])}

    Additional information:
    {search_strategy.additional_information}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Assuming this is the correct model name
        messages=[
            {"role": "system", "content": "You are an AI assistant that analyzes content and creates relevant context summaries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    context = response.choices[0].message.content.strip()
    return context if context.lower() != "none" else None

@register_function
def researcher(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process search results, analyze content, and decide which URLs to scrape.
    """
    state = AgentState(**input_data.get('ExecuteTavilySearch', {}))
    tavily_state = state.tavily_state
    search_strategy = state.search_strategy
    firecrawl_state = state.firecrawl_state
    
    # Process search results
    latest_query = search_strategy.search_phrases[0].phrase  # Assuming the first phrase was used for the search
    search_results = tavily_state.cache.get(latest_query, {}).get('results', [])

    for result in search_results:
        url = result.get('url', '')
        content = result.get('content', '')
        title = result.get('title', '')
        
        if url not in state.research_results:
            context = analyze_content_with_gpt4_mini(content, search_strategy)
            
            if context is None:
                # Not enough relevant information, need to scrape
                if url not in firecrawl_state.cache and url not in firecrawl_state.scrapelist:
                    firecrawl_state.scrapelist.append(url)
            else:
                state.research_results[url] = ResearchResult(
                    url=url,
                    content=content,
                    title=title,
                    context=context
                )

    # Process any scraped data from previous iterations
    scraped_data = input_data.get('FirecrawlScrape', {}).get('scraped_data', [])
    for scrape_result in scraped_data:
        if scrape_result['status'] == 'success':
            url = scrape_result['url']
            content = scrape_result['markdown']
            title = 'Scraped Content'
            
            context = analyze_content_with_gpt4_mini(content, search_strategy)
            
            state.research_results[url] = ResearchResult(
                url=url,
                content=content,
                title=title,
                context=context
            )

    # Update the state
    state.firecrawl_state = firecrawl_state

    metahistory = MessageDict(
        role="assistant",
        content=f"Processed search results and scraped data. {len(firecrawl_state.scrapelist)} URLs remaining to scrape.",
        result={
            'total_research_results': len(state.research_results),
            'urls_to_scrape': len(firecrawl_state.scrapelist)
        },
        create_agent_msg=True,
        tool_call=False
    )

    return {
        "graph_data": state.dict(),
        "metahistory": metahistory.dict()
    }



@register_function
def reporter(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a final report based on the research results, focusing on the context.
    """
    state = AgentState(**input_data.get('Researcher', {}))  # Changed to take data from Researcher

    try:
        # Prepare the research results for the AI to process, focusing on context
        research_summary = ""
        for i, (url, result) in enumerate(state.research_results.items(), start=1):
            if result.context:
                research_summary += f"[{i}] Title: {result.title}\n"
                research_summary += f"    URL: {url}\n"
                research_summary += f"    Context: {result.context}\n\n"
            else:
                research_summary += f"[{i}] Title: {result.title}\n"
                research_summary += f"    URL: {url}\n"
                research_summary += f"    (No context available)\n\n"

        # Prepare the prompt using the external template
        prompt = REPORTER_PROMPT_TEMPLATE.format(
            query=state.input_query,
            research_summary=research_summary
        )

        # Generate the report using GPT-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI research assistant tasked with summarizing research findings."},
                {"role": "user", "content": prompt}
            ]
        )

        report = response.choices[0].message.content.strip()

        # Update the state with the final report
        state.final_report = report

        metahistory = MessageDict(
            role="assistant",
            content=f"Generated final report for query: {state.input_query}",
            result=report,
            create_agent_msg=True,
            tool_call=False
        )

        return {"graph_data": state.dict(), "metahistory": metahistory.dict()}
    except Exception as e:
        print("Error ")
        logging.error(f"Error in reporter node: {str(e)}")
        raise


def reviewer_old(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Review the report, provide feedback, and determine the next step in the workflow.
    """
    state = AgentState(**input_data.get('Reporter', {}))  # Changed to take data from Researcher

    try:
        # Prepare the prompt
        prompt = REVIEWER_PROMPT_TEMPLATE.format(
            reporter_response=state.final_report,
            current_datetime=datetime.now().isoformat()
        )

        # Generate the review and routing decision using GPT-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant tasked with reviewing research reports and determining workflow steps."},
                {"role": "user", "content": prompt}
            ]
        )

        result = json.loads(response.choices[0].message.content.strip())

        # Update the state with the review results
        state.review_feedback = result.get('feedback')
        state.review_pass = result.get('pass_review')
        state.next_agent = result.get('next_agent')

        # Validate the next_agent
        valid_agents = ["SearchStrategyPlanner", "Researcher", "Reporter", "End"]
        if state.next_agent not in valid_agents:
            raise ValueError(f"Invalid next_agent: {state.next_agent}. Must be one of {valid_agents}")

        metahistory = MessageDict(
            role="assistant",
            content=f"Reviewed report and determined next step: {state.next_agent}",
            result=result,
            create_agent_msg=True,
            tool_call=False
        )

        return {"graph_data": state.dict(), "metahistory": metahistory.dict()}
    except Exception as e:
        print("Error")
        #logging.error(f"Error in reviewer node: {str(e)}")
        raise

# Function to define the structure of the reviewer's output
def define_reviewer_function():
    return {
        "name": "review_and_route",
        "description": "Review the report and determine the next step in the workflow",
        "parameters": {
            "type": "object",
            "properties": {
                "feedback": {
                    "type": "string",
                    "description": "Detailed feedback on the report"
                },
                "pass_review": {
                    "type": "boolean",
                    "description": "Whether the report passes the review"
                },
                "comprehensive": {
                    "type": "boolean",
                    "description": "Whether the report is comprehensive"
                },
                "citations_provided": {
                    "type": "boolean",
                    "description": "Whether proper citations are provided"
                },
                "relevant_to_research_question": {
                    "type": "boolean",
                    "description": "Whether the report is relevant to the research question"
                },
                "next_agent": {
                    "type": "string",
                    "enum": ["SearchStrategyPlanner", "Researcher", "Reporter", "End"],
                    "description": "The next agent to route to in the workflow"
                }
            },
            "required": ["feedback", "pass_review", "comprehensive", "citations_provided", "relevant_to_research_question", "next_agent"]
        }
    }

@register_function
def reviewer(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Review the report, provide feedback, and determine the next step in the workflow.
    """
    state = AgentState(**input_data.get('Reporter', {}))  # Changed to take data from Researcher

    try:
        # Prepare the user message
        user_message = f"""
        Please review the following report and provide feedback:

        Reporter's response: {state.final_report}

        Current date and time: {datetime.now().isoformat()}

        Provide your review and routing decision using the review_and_route function.
        """

        # Generate the review and routing decision using GPT-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            functions=[define_reviewer_function()],
            function_call={"name": "review_and_route"}
        )

        # Extract the function call result
        function_call = response.choices[0].message.function_call
        result = json.loads(function_call.arguments)

        # Update the state with the review results
        state.review_feedback = result.get('feedback')
        state.review_pass = result.get('pass_review')
        state.next_agent = result.get('next_agent')

        metahistory = MessageDict(
            role="assistant",
            content=f"Reviewed report and determined next step: {state.next_agent}",
            result=result,
            create_agent_msg=True,
            tool_call=False
        )

        return {"graph_data": state.dict(), "metahistory": metahistory.dict()}
    except Exception as e:
        logging.error(f"Error in reviewer node: {str(e)}")
        raise