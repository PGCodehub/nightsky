# NightSky Agentic FrameWork🌙

A powerful Python framework for building and orchestrating complex agentic workflows with support for parallel execution, conditional branching, inter-graph communication, and real-time streaming updates.

## 🌟 Features

- **Graph-Based Execution**: Build workflows as directed graphs with nodes and edges
- **Agent Memory Management**: Automatic conversation history tracking per agent
- **Parallel Execution**: Run multiple branches concurrently with async/await
- **Conditional Branching**: Dynamic routing based on execution results
- **Multi-Graph Orchestration**: Connect multiple graphs and share data between them
- **Real-Time Updates**: Server-Sent Events (SSE) for live execution monitoring
- **Type Safety**: Built on Pydantic for robust data validation
- **Dependency Management**: Automatic handling of node dependencies
- **Execution Tracking**: Complete history with unique execution IDs
- **Flexible Agent Schemas**: Customizable agent message formats

## 📦 Installation

```bash
pip install -r requirements.txt
```

### Dependencies

```
pydantic
fastapi
sse-starlette
asyncio
```

For AI model integrations:
```bash
pip install openai anthropic  # Optional, based on your needs
```

## 🚀 Quick Start

Here's a simple example to get you started:

```python
from NightSky.AgentGraph import AgenticGraph, StartNode, EndNode, MessageDict
from pydantic import BaseModel
from typing import Dict, Any, List

# Define your data schema
class MyWorkflowState(BaseModel):
    input_text: str
    result: str = ""

# Define node functions
def process_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Access data from previous nodes
    start_data = input_data.get("Start", {})
    
    # Process the data
    result = {
        "input_text": start_data.get("input_text", ""),
        "result": "Processed!"
    }
    
    return {"graph_data": result, "metahistory": None}

# Create the graph
graph = AgenticGraph(
    graph_id="my_workflow",
    data_schema=MyWorkflowState,
    max_parallel=3
)

# Add nodes
graph.add_node(StartNode())
graph.add_node("ProcessNode", process_node)
graph.add_node(EndNode())

# Connect nodes
graph.add_edge("Start", "ProcessNode")
graph.add_edge("ProcessNode", "End")

# Execute
import asyncio
initial_data = {"input_text": "Hello, NightSky!"}
asyncio.run(graph.execute(initial_data))

# Get results
final_state = graph.get_graph_data()
print(f"Final result: {final_state}")
```

## 📚 Core Concepts

### 1. Nodes

Nodes are the building blocks of your workflow. There are three types:

- **StartNode**: Entry point of the graph
- **Regular Node**: Custom processing units
- **EndNode**: Terminal nodes that conclude execution
- **Agent Node**: Nodes with conversation memory

```python
# Regular node
def my_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Your logic here
    return {"graph_data": result, "metahistory": None}

graph.add_node("MyNode", my_node)

# Agent node with memory
def my_agent(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Agent can access its conversation history
    context = agentic_memory[-5:]  # Last 5 messages
    
    # Process with context
    result = process_with_context(input_data, context)
    
    # Return with metahistory to update memory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=result,
        agent_msgs=[{"role": "assistant", "content": "Response"}]
    )
    
    return {"graph_data": result, "metahistory": metahistory}

graph.add_node("MyAgent", my_agent, is_agent=True)
```

### 2. Edges

Edges define the flow between nodes:

```python
# Simple edge
graph.add_edge("NodeA", "NodeB")

# Conditional edge
graph.add_edge(
    "NodeA", 
    "NodeB", 
    condition=lambda data: data.get("should_proceed", False)
)

# Optional edge (non-blocking)
graph.add_edge("NodeA", "NodeB", is_required=False)
```

### 3. Branching

Dynamic routing based on execution results:

```python
def route_condition(graph_data: Dict[str, Any]) -> str:
    score = graph_data.get("NodeA", {}).get("score", 0)
    if score > 80:
        return "high"
    elif score > 50:
        return "medium"
    else:
        return "low"

graph.add_branching_edge(
    source_id="NodeA",
    condition=route_condition,
    branches={
        "high": "PremiumPath",
        "medium": "StandardPath",
        "low": ["BasicPath", "SupportPath"]  # Multiple targets
    }
)
```

### 4. Data Flow

Data flows through the graph via `node_graph_state`:

```python
def node_b(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Access output from NodeA
    node_a_output = input_data["NodeA"]
    
    # Access output from multiple previous nodes
    node_x_output = input_data.get("NodeX", {})
    node_y_output = input_data.get("NodeY", {})
    
    # Process and return
    result = {
        "combined": node_a_output["value"] + node_x_output["value"]
    }
    
    return {"graph_data": result, "metahistory": None}
```

### 5. Agent Memory

Agents maintain conversation history across executions:

```python
# First execution
await graph.execute(data1, chat_id="user_123")

# Second execution - agent remembers previous conversation
await graph.execute(data2, chat_id="user_123")

# Get agent memory
agent_id = graph.agent_ids[0]
memory = graph.get_agentic_memory(agent_id)
```

### 6. Execution History

Track all executions with metahistory:

```python
# Get execution history
metahistory, entry_order = graph.get_metahistory(chat_id="user_123")

# Each entry contains:
# - role: The role (system, user, assistant, etc.)
# - input_data: Input to the node
# - agent_msgs: Agent conversation messages
# - output_state: Node output
# - execution_id: Unique ID for this run
```

## 🔥 Advanced Features

### Multi-Graph Workflows

Connect multiple graphs to build complex, modular workflows:

```python
# Create two graphs
graph1 = AgenticGraph(graph_id="analysis", data_schema=AnalysisSchema)
graph2 = AgenticGraph(graph_id="reporting", data_schema=ReportSchema)

# Connect them
graph1.connect_graph(graph2)

# Add cross-graph edge
graph1.add_edge("AnalysisNode", ("reporting", "ReportNode"))

# Data is automatically shared based on common schema fields
```

### Real-Time SSE Updates

Stream execution progress to clients:

```python
# Configure which fields to send via SSE
graph.set_sse_fields({
    'common': ['status', 'timestamp'],
    'AnalysisNode': ['analysis_result', 'confidence'],
    'ReportNode': ['report_url']
})

# Start execution (SSE sender starts automatically)
await graph.execute(data)

# In your FastAPI app
from NightSky.sse_manager import sse_endpoint

@app.get("/stream/{chat_id}")
async def stream(request: Request, chat_id: str):
    return await sse_endpoint(request, chat_id)
```

### Dependency Management

Control execution order with required dependencies:

```python
# NodeC waits for both NodeA and NodeB
graph.add_edge("NodeA", "NodeC", is_required=True)
graph.add_edge("NodeB", "NodeC", is_required=True)

# NodeC executes only after both NodeA and NodeB complete
```

### Parallel Execution

Execute multiple branches simultaneously:

```python
# Set maximum parallel tasks
graph = AgenticGraph(
    graph_id="parallel_workflow",
    max_parallel=5  # Run up to 5 branches concurrently
)

# When a node has multiple next nodes, they run in parallel
graph.add_edge("Start", "TaskA")
graph.add_edge("Start", "TaskB")
graph.add_edge("Start", "TaskC")
# TaskA, TaskB, TaskC run concurrently
```

### Stop and Resume Execution

Control execution flow programmatically:

```python
# Stop at current node
graph.stop_at_current_node()

# Resume from current node
graph.resume_execution()

# Get current position
current = graph.get_current_node()
print(f"Stopped at: {current.name}")
```

### Custom Agent Schemas

Define custom message formats for agents:

```python
from pydantic import BaseModel

class CustomAgentSchema(BaseModel):
    role: str
    content: str
    confidence: float
    metadata: Dict[str, Any]

graph = AgenticGraph(
    graph_id="custom_agents",
    agent_schema_type=CustomAgentSchema
)
```

## 🎯 Complete Example: Marketing Workflow

Here's a real-world example with multiple agents and branching:

```python
from NightSky.AgentGraph import AgenticGraph, StartNode, EndNode, MessageDict
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import openai

# Define state schema
class ProductAnalysis(BaseModel):
    product_name: str
    analysis: str
    market_size: str
    target_audience: str

class WorkflowState(BaseModel):
    products: List[str]
    analyses: List[ProductAnalysis] = Field(default_factory=list)
    strategies: List[Dict[str, str]] = Field(default_factory=list)

# Define agent functions
def market_analyst(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    start_data = input_data["Start"]
    state = WorkflowState(**start_data)
    
    # Use OpenAI or other LLM
    client = openai.OpenAI()
    
    for product in state.products:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=agentic_memory + [
                {"role": "user", "content": f"Analyze product: {product}"}
            ]
        )
        
        analysis_text = response.choices[0].message.content
        
        state.analyses.append(ProductAnalysis(
            product_name=product,
            analysis=analysis_text,
            market_size="Large",
            target_audience="General consumers"
        ))
    
    # Update agent memory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=state.dict(),
        agent_msgs=[
            {"role": "user", "content": f"Analyze products: {state.products}"},
            {"role": "assistant", "content": f"Completed analysis of {len(state.products)} products"}
        ]
    )
    
    return {"graph_data": state.dict(), "metahistory": metahistory}

def marketing_strategist(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    analyst_data = input_data["MarketAnalyst"]
    state = WorkflowState(**analyst_data)
    
    # Generate strategies based on analyses
    # ... (implementation)
    
    return {"graph_data": state.dict(), "metahistory": metahistory}

# Branching condition
def needs_niche_specialist(graph_data: Dict[str, Any]) -> bool:
    state = WorkflowState(**graph_data["MarketingStrategist"])
    return any(a.market_size == "Small" for a in state.analyses)

# Build graph
async def main():
    graph = AgenticGraph(
        graph_id="marketing_workflow",
        data_schema=WorkflowState,
        max_parallel=3
    )
    
    # Add nodes
    graph.add_node(StartNode())
    graph.add_node("MarketAnalyst", market_analyst, is_agent=True)
    graph.add_node("MarketingStrategist", marketing_strategist, is_agent=True)
    graph.add_node("NicheSpecialist", niche_specialist, is_agent=True)
    graph.add_node(EndNode())
    
    # Add edges
    graph.add_edge("Start", "MarketAnalyst")
    graph.add_edge("MarketAnalyst", "MarketingStrategist")
    
    # Conditional branching
    graph.add_branching_edge(
        "MarketingStrategist",
        condition=needs_niche_specialist,
        branches={
            True: "NicheSpecialist",
            False: "End"
        }
    )
    graph.add_edge("NicheSpecialist", "End")
    
    # Configure SSE
    graph.set_sse_fields({
        'common': ['status'],
        'MarketAnalyst': ['analyses'],
        'MarketingStrategist': ['strategies']
    })
    
    # Execute
    initial_data = {
        "products": ["Smartphone", "Smart Watch", "Custom Keyboard"]
    }
    
    await graph.execute(initial_data, chat_id="session_123")
    
    # Get results
    final_state = graph.get_graph_data()
    print(f"Analysis complete: {len(final_state['analyses'])} products analyzed")
    
    # Get agent memories
    for agent_id in graph.agent_ids:
        memory = graph.get_agentic_memory(agent_id)
        print(f"Agent {agent_id} has {len(memory)} messages in memory")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 📖 API Reference

### AgenticGraph

**Constructor:**
```python
AgenticGraph(
    graph_id: str,
    chat_id: Optional[str] = None,
    data_schema: Type[BaseModel] = DataSchema,
    max_parallel: int = 3,
    metahistory_type: Type = MessageDict,
    agent_schema_type: Type[BaseModel] = AgentSchema,
    max_sse_size: int = 1000000
)
```

**Key Methods:**

- `add_node(node_or_name, function=None, is_agent=False, agent_schema=None)` - Add a node
- `add_edge(source, target, condition=None, is_required=True)` - Add an edge
- `add_branching_edge(source_id, condition, branches)` - Add conditional branching
- `connect_graph(other_graph)` - Connect to another graph
- `async execute(initial_data, max_parallel=3, chat_id=None)` - Execute the graph
- `get_graph_data(chat_id=None)` - Get current graph state
- `get_metahistory(chat_id=None)` - Get execution history
- `get_agentic_memory(agent_id)` - Get agent conversation history
- `set_sse_fields(fields)` - Configure SSE data filtering
- `update_sse_fields(fields, remove=False)` - Update SSE fields
- `stop_at_current_node()` - Stop execution
- `resume_execution()` - Resume from stopped node
- `visualize_graph()` - Generate DOT format visualization
- `save_graph_visualization(filename)` - Save graph as PNG

## 🛠️ Development

### Running Tests

```bash
cd test
python test.py
```

### Project Structure

```
nightsky/
├── NightSky/
│   ├── AgentGraph.py          # Core graph engine
│   ├── sse_manager.py         # SSE handling
│   ├── api.py                 # FastAPI endpoints
│   ├── function_registry.py   # Function management
│   └── json_to_agentgraph_parser.py  # JSON graph loader
├── test/                      # Test files
├── notebooks/                 # Example notebooks
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🌐 Use Cases

- **Multi-Agent AI Systems**: Coordinate multiple LLM agents
- **Data Pipelines**: Build complex ETL workflows
- **Workflow Automation**: Automate business processes
- **Research Workflows**: Chain analysis and reporting tasks
- **Customer Service**: Multi-step support automation
- **Content Generation**: Orchestrate writing, editing, and publishing

## 🔮 Future Roadmap

- [ ] Graph versioning and rollback
- [ ] Built-in RAG examples
- [ ] Enhanced visualization UI
- [ ] More AI model integrations
- [ ] Workflow templates library
- [ ] Performance monitoring dashboard
- [ ] Human-in-the-loop approvals
- [ ] Distributed execution support

## 💡 Tips

1. **Use descriptive node names** - Makes debugging easier
2. **Start simple** - Build complex graphs incrementally
3. **Monitor memory** - Use `get_agentic_memory()` to inspect agent state
4. **Filter SSE data** - Only send necessary data to reduce bandwidth
5. **Use chat_id** - Separate sessions for different users/contexts
6. **Handle errors gracefully** - Node functions should validate inputs
7. **Test branches individually** - Verify each path before combining

## 📞 Support

For questions and support:
- Open an issue on GitHub

---

Built with ❤️ for the AI agent community by PGCODEHUB

