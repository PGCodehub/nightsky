from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from typing import Dict, AsyncGenerator, Dict, Any
import asyncio
import json
import uuid

class SSEManager:
    def __init__(self):
        self.clients: Dict[str, Dict[str, asyncio.Queue]] = {}

    async def push(self, chat_id: str, data: Dict[str, Any]):
        if chat_id not in self.clients:
            return
        message = json.dumps(data)
        tasks = [asyncio.create_task(queue.put(message)) for queue in self.clients[chat_id].values()]
        await asyncio.gather(*tasks)

    async def subscribe(self, chat_id: str, client_id: str) -> AsyncGenerator:
        if chat_id not in self.clients:
            self.clients[chat_id] = {}
        
        queue = asyncio.Queue()
        self.clients[chat_id][client_id] = queue
        
        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            del self.clients[chat_id][client_id]
            if not self.clients[chat_id]:
                del self.clients[chat_id]


# This function will be used in api.py
async def sse_endpoint(request: Request, chat_id: str):
    client_id = str(uuid.uuid4())
    generator = sse_manager.subscribe(chat_id, client_id)
    return EventSourceResponse(generator)


sse_manager = SSEManager()

# This function will be called from AgentGraph to push updates
async def push_update(chat_id: str, data: Dict[str, Any]):
    await sse_manager.push(chat_id, data)

