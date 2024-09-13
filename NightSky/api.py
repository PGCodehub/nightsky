from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from AgentGraph import AgenticGraph
from sse_manager import sse_endpoint
import asyncio

app = FastAPI()

# This would be replaced with your actual graph instance
graph_instance = AgenticGraph(graph_id="main_graph")

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
    return await sse_endpoint(request, chat_id)

# Additional endpoints will be added here