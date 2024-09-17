import asyncio
import aiohttp

async def listen_for_sse_updates(chat_id):
    url = f"http://localhost:8000/sse/{chat_id}"
    print(f"Connecting to SSE endpoint: {url}")
    
    while True:  # Keep trying to reconnect if the connection is lost
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"SSE connection established. Status: {response.status}")
                    async for line in response.content:
                        if line:
                            line = line.decode('utf-8').strip()
                            print(f"Received: {line}")
                            if line.startswith('data: '):
                                data = line[6:]
                                print(f"Data: {data}")
        except aiohttp.ClientError as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

async def main():
    chat_id = "test_chat_12345"  # Make sure this matches the chat_id you use in graph_executor.py
    await listen_for_sse_updates(chat_id)

if __name__ == "__main__":
    asyncio.run(main())