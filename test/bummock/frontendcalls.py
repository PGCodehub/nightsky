import requests
import json
from sseclient import SSEClient
import asyncio
import aiohttp
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

import os
import sys
sys.path.append('/root/nightsky/NightSky')

from agent_state import AgentState, SearchStrategy, SearchPhrase , FirecrawlState

async def call_execute_api(chat_id, initial_data):
    url = f"http://localhost:8003/execute/{chat_id}"
    payload = {"initial_data": initial_data.dict()}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                print("Graph execution started successfully")
            else:
                print(f"Failed to start graph execution: {await response.text()}")


async def main():
    chat_id = "test_chat_12345"
    
    # Create the initial data using the provided structure
    initial_data = AgentState(
        input_query="What are the latest developments in quantum computing?",
        search_strategy=SearchStrategy(
            search_phrases=[],
            additional_information=""
        ),
        tavily_state={},
        firecrawl_state={}
    )

    print("Initial data being passed to AgentState:", initial_data.dict())

    
    # Start the graph execution
    await call_execute_api(chat_id, initial_data)



if __name__ == "__main__":
    asyncio.run(main())