# Getting Started with NightSky AgentGraph

Welcome to NightSky AgentGraph! This guide will walk you through creating your first agentic workflow from scratch.

## Table of Contents

1. [Installation](#installation)
2. [Core Concepts](#core-concepts)
3. [Your First Graph](#your-first-graph)
4. [Adding Agents](#adding-agents)
5. [Conditional Logic](#conditional-logic)
6. [Real-Time Updates](#real-time-updates)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install NightSky (Development Mode)

```bash
# From the project root
pip install -e .
```

### Step 3: Verify Installation

```python
from NightSky.AgentGraph import AgenticGraph
print("✅ NightSky AgentGraph installed successfully!")
```

## Core Concepts

Before we dive in, let's understand the key concepts:

### 1. **Graph**

A workflow containing nodes and edges that define your process flow.

### 2. **Nodes**

Processing units that perform specific tasks. Types:

- **StartNode**: Entry point
- **Regular Node**: Custom logic
- **Agent Node**: AI agent with memory
- **EndNode**: Exit point

### 3. **Edges**

Connections between nodes that control flow:

- **Regular**: Unconditional flow
- **Conditional**: Flow based on conditions
- **Branching**: Multi-way routing

### 4. **Data Flow**

Data passes between nodes via the `node_graph_state` dictionary.

### 5. **Agent Memory**

Agents maintain conversation history across executions.

## Your First Graph

Let's build a simple text processing workflow.

### Step 1: Import Required Modules

```python
import asyncio
from typing import Dict, Any
from pydantic import BaseModel
from NightSky.AgentGraph import AgenticGraph, StartNode, EndNode
```

### Step 2: Define Your Data Schema

```python
class TextProcessingState(BaseModel):
    """Schema defining what data flows through our graph"""
    input_text: str
    processed_text: str = ""
    word_count: int = 0
    status: str = "pending"
```

This schema ensures type safety throughout your workflow.

### Step 3: Create Node Functions

```python
def uppercase_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert text to uppercase"""
    # Get data from the Start node
    start_data = input_data.get("Start", {})

    # Process
    text = start_data.get("input_text", "")
    processed = text.upper()

    # Return result
    result = {
        "input_text": text,
        "processed_text": processed,
        "word_count": 0,
        "status": "uppercase_complete"
    }

    return {"graph_data": result, "metahistory": None}


def count_words_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Count words in processed text"""
    # Get data from previous node
    uppercase_data = input_data.get("UppercaseNode", {})

    # Process
    text = uppercase_data.get("processed_text", "")
    word_count = len(text.split())

    # Return result
    result = {
        "input_text": uppercase_data.get("input_text", ""),
        "processed_text": text,
        "word_count": word_count,
        "status": "complete"
    }

    return {"graph_data": result, "metahistory": None}
```

**Key Points:**

- Node functions receive `input_data` containing outputs from previous nodes
- Each previous node's output is keyed by its node name
- Must return `{"graph_data": ..., "metahistory": ...}`

### Step 4: Build the Graph

```python
async def main():
    # Create graph
    graph = AgenticGraph(
        graph_id="text_processor",
        data_schema=TextProcessingState
    )

    # Add nodes
    graph.add_node(StartNode())
    graph.add_node("UppercaseNode", uppercase_node)
    graph.add_node("CountWordsNode", count_words_node)
    graph.add_node(EndNode())

    # Connect nodes
    graph.add_edge("Start", "UppercaseNode")
    graph.add_edge("UppercaseNode", "CountWordsNode")
    graph.add_edge("CountWordsNode", "End")

    # Execute
    initial_data = {
        "input_text": "Hello NightSky AgentGraph!",
        "processed_text": "",
        "word_count": 0
    }

    await graph.execute(initial_data)

    # Get results
    final_state = graph.get_graph_data()
    print(f"Original: {final_state['input_text']}")
    print(f"Processed: {final_state['processed_text']}")
    print(f"Word count: {final_state['word_count']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Expected Output:**

```
Original: Hello NightSky AgentGraph!
Processed: HELLO NIGHTSKY AGENTGRAPH!
Word count: 3
```

Congratulations! You've built your first workflow! 🎉

## Adding Agents

Agents are nodes with memory that can maintain conversation context.

### Step 1: Define Agent Function

```python
from NightSky.AgentGraph import MessageDict
from typing import List

def chatbot_agent(
    input_data: Dict[str, Any],
    agentic_memory: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Agent that responds to user input with context"""

    start_data = input_data.get("Start", {})
    user_message = start_data.get("input_text", "")

    # Access previous conversation
    context = ""
    if agentic_memory:
        context = f"(Remembering {len(agentic_memory)} previous messages) "

    # Generate response (in real app, call LLM here)
    response = f"{context}You said: {user_message}"

    result = {
        "input_text": user_message,
        "processed_text": response,
        "word_count": len(response.split())
    }

    # Update agent memory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=result,
        agent_msgs=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ]
    )

    return {"graph_data": result, "metahistory": metahistory}
```

### Step 2: Add Agent to Graph

```python
# When adding the node, set is_agent=True
graph.add_node("ChatbotAgent", chatbot_agent, is_agent=True)
```

### Step 3: Test Memory Persistence

```python
# First execution
await graph.execute({"input_text": "Hello!"}, chat_id="user_123")

# Second execution - agent remembers!
await graph.execute({"input_text": "How are you?"}, chat_id="user_123")

# Check memory
agent_id = graph.agent_ids[0]
memory = graph.get_agentic_memory(agent_id)
print(f"Agent has {len(memory)} messages in memory")
```

## Conditional Logic

Add branching logic to create dynamic workflows.

### Simple Conditional Edge

```python
# Only proceed if word count is high
def has_many_words(data: Dict[str, Any]) -> bool:
    word_count = data.get("word_count", 0)
    return word_count > 10

graph.add_edge(
    "CountWordsNode",
    "DetailedAnalysis",
    condition=has_many_words
)
```

### Multi-Way Branching

```python
def classify_length(graph_data: Dict[str, Any]) -> str:
    """Route based on text length"""
    count_data = graph_data.get("CountWordsNode", {})
    count = count_data.get("word_count", 0)

    if count < 5:
        return "short"
    elif count < 20:
        return "medium"
    else:
        return "long"

# Add branching edge
graph.add_branching_edge(
    source_id="CountWordsNode",
    condition=classify_length,
    branches={
        "short": "ShortTextHandler",
        "medium": "MediumTextHandler",
        "long": "LongTextHandler"
    }
)
```

## Real-Time Updates

Stream execution progress to clients using SSE.

### Step 1: Configure SSE Fields

```python
# Set which fields to stream
graph.set_sse_fields({
    'common': ['status'],  # All nodes send status
    'UppercaseNode': ['processed_text'],
    'CountWordsNode': ['word_count']
})
```

### Step 2: Set Up FastAPI Endpoint

```python
from fastapi import FastAPI, Request
from NightSky.sse_manager import sse_endpoint

app = FastAPI()

@app.get("/stream/{chat_id}")
async def stream(request: Request, chat_id: str):
    return await sse_endpoint(request, chat_id)

@app.post("/execute")
async def execute_workflow(data: dict):
    await graph.execute(data, chat_id=data.get("chat_id"))
    return {"status": "started"}
```

### Step 3: Client-Side (JavaScript)

```javascript
const eventSource = new EventSource("/stream/user_123");

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Update:", data);
  // Update UI with data.agent_state
};
```

## Best Practices

### 1. **Data Schema Design**

```python
# ✅ Good - Clear, specific fields
class OrderProcessingState(BaseModel):
    order_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    status: str

# ❌ Bad - Too generic
class State(BaseModel):
    data: Any
    result: Any
```

### 2. **Node Functions**

```python
# ✅ Good - Single responsibility
def validate_order(input_data):
    # Only validates
    pass

def calculate_total(input_data):
    # Only calculates
    pass

# ❌ Bad - Does too much
def process_order(input_data):
    # Validates, calculates, sends emails, updates DB...
    pass
```

### 3. **Error Handling**

```python
def robust_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Your logic
        result = process_data(input_data)
        return {"graph_data": result, "metahistory": None}
    except Exception as e:
        # Return error state
        return {
            "graph_data": {"error": str(e), "status": "failed"},
            "metahistory": None
        }
```

### 4. **Memory Management**

```python
# Limit memory to recent messages
def my_agent(input_data, agentic_memory):
    # Use only last 10 messages
    recent_memory = agentic_memory[-10:]

    # Your logic
    pass
```

### 5. **Testing**

```python
# Test nodes independently
def test_uppercase_node():
    input_data = {
        "Start": {"input_text": "test"}
    }
    result = uppercase_node(input_data)
    assert result["graph_data"]["processed_text"] == "TEST"
```

## Troubleshooting

### Issue: Graph Hangs

**Problem:** Execution never completes

**Causes:**

1. Missing edges to EndNode
2. Circular dependencies
3. Unsatisfied required dependencies

**Solution:**

```python
# Check graph structure
print(f"Nodes: {list(graph.nodes.keys())}")
print(f"Edges: {list(graph.edges.keys())}")

# Verify EndNode exists
end_nodes = [n for n in graph.nodes.values() if isinstance(n, EndNode)]
print(f"End nodes: {len(end_nodes)}")
```

### Issue: No Data in Next Node

**Problem:** `input_data` is empty or missing expected keys

**Causes:**

1. Previous node didn't execute
2. Wrong node name in `input_data.get()`
3. Required dependency not met

**Solution:**

```python
def my_node(input_data: Dict[str, Any]):
    # Debug: print available data
    print(f"Available keys: {list(input_data.keys())}")

    # Use .get() with defaults
    prev_data = input_data.get("PreviousNode", {})
    value = prev_data.get("field", "default")
```

### Issue: Agent Not Remembering

**Problem:** Agent memory is empty on second run

**Causes:**

1. Using different `chat_id`
2. Not returning `metahistory`
3. `agent_msgs` is None or empty

**Solution:**

```python
# Use same chat_id
await graph.execute(data1, chat_id="session_1")
await graph.execute(data2, chat_id="session_1")  # Same!

# Always return metahistory for agents
metahistory = MessageDict(
    role="assistant",
    input_data=input_data,
    toolcall_in_output=False,
    output_state=result,
    agent_msgs=[...]  # Must not be None
)
```

## Next Steps

### 1. **Explore Examples**

```bash
# Run the quickstart example
python examples/quickstart.py

# Try branching
python examples/branching_example.py

# Multi-agent collaboration
python examples/multi_agent_example.py
```

### 2. **Add LLM Integration**

```python
import openai

def ai_agent(input_data, agentic_memory):
    client = openai.OpenAI()

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=agentic_memory + [
            {"role": "user", "content": "..."}
        ]
    )

    # Process response...
```

### 3. **Build Multi-Graph Workflows**

```python
# Create two graphs
graph1 = AgenticGraph(graph_id="analysis")
graph2 = AgenticGraph(graph_id="reporting")

# Connect them
graph1.connect_graph(graph2)

# Cross-graph edge
graph1.add_edge("AnalysisNode", ("reporting", "ReportNode"))
```

### 4. **Add Visualization**

```python
# Generate visualization
graph.save_graph_visualization("my_workflow.png")
```

### 5. **Deploy as API**

See the FastAPI examples in the test directory.

## Resources

- **Full Documentation**: [README.md](../README.md)
- **API Reference**: [AgentGraph.py](../NightSky/AgentGraph.py)
- **Examples**: [examples/](../examples/)
- **Tests**: [test/](../test/)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)

## Get Help

- 📖 Check the documentation
- 💬 Open an issue on GitHub
- 🐛 Report bugs with reproduction steps
- 💡 Share your use cases!

---

**Happy Building! 🚀**

Ready to create amazing agentic workflows with NightSky AgentGraph!
