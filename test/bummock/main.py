import os
import sys
sys.path.append('/root/nightsky/NightSky')


from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
# from AgentGraph import AgenticGraph
from sse_manager import sse_endpoint
import asyncio
from graph import create_search_workflow_graph

from fastapi.middleware.cors import CORSMiddleware

from sse_starlette.sse import EventSourceResponse
from sse_manager import sse_manager


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Make sure this is available to your route functions
app.state.sse_manager = sse_manager

#graph_instance = AgenticGraph(graph_id="main_graph")

graph_instance = create_search_workflow_graph()

class ExecutionRequest(BaseModel):
    initial_data: Dict[str, Any]

class ExecutionResponse(BaseModel):
    message: str

@app.post("/execute/{chat_id}", response_model=ExecutionResponse)
async def execute_graph(chat_id: str, request: ExecutionRequest):
    try:
        # Start the graph execution asynchronously
        asyncio.create_task(graph_instance.execute(
            initial_data=request.initial_data, 
            chat_id=chat_id
        ))
        
        return ExecutionResponse(message="Graph execution started successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/sse/{chat_id}")
async def sse(request: Request, chat_id: str):
    print(f"SSE endpoint called for chat_id: {chat_id}")
    client_host = request.client.host
    print(f"Client IP: {client_host}")
    try:
        response = await sse_endpoint(request, chat_id)
        print(f"SSE response created for chat_id: {chat_id}")
        return response
    except Exception as e:
        print(f"Error in SSE endpoint for chat_id {chat_id}: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)