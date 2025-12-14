# Changelog

All notable changes to NightSky AgentGraph will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Graph persistence and checkpoint/resume functionality
- Enhanced visualization UI with interactive graph editor
- Additional AI model integrations (Ollama, Claude, etc.)
- Built-in RAG (Retrieval Augmented Generation) examples
- Performance monitoring dashboard
- Human-in-the-loop approval gates
- Distributed execution support
- Graph versioning and rollback
- Workflow template library

## [0.1.0] - 2024-01-01

### Added
- Initial release of NightSky AgentGraph
- Core graph execution engine with async/await support
- Node system (StartNode, EndNode, Regular Nodes, Agent Nodes)
- Edge management with conditional routing
- Flexible branching with dynamic conditions
- Agent memory management per agent instance
- Multi-graph orchestration and communication
- Server-Sent Events (SSE) for real-time updates
- SSE field filtering (common and node-specific)
- Dependency management for node execution
- Execution tracking with unique execution IDs
- Metahistory for complete execution audit trail
- Parallel execution with configurable max_parallel
- Type safety with Pydantic schemas
- Reverse edge tracking for dependency resolution
- Cross-graph data sharing with field filtering
- Stop/resume execution control
- Graph visualization (DOT format and PNG export)
- Support for required and optional edges
- Chat ID-based session management
- Comprehensive logging system

### Features by Component

#### Core Engine (AgentGraph.py)
- `AgenticGraph` class with full workflow orchestration
- Node execution with retry mechanism
- Branch execution with parallel task support
- Dependency checking before node execution
- Data flow management via `node_graph_state`
- Agent-specific conversation memory
- Execution history tracking

#### Node Types
- `StartNode` - Workflow entry point
- `EndNode` - Workflow termination
- `Node` - Regular processing nodes
- Agent nodes with memory support

#### Edge Types
- Regular edges (unconditional)
- Conditional edges (with boolean conditions)
- Branching edges (multi-way routing)
- Required vs optional edges
- Cross-graph edges

#### SSE System (sse_manager.py)
- Real-time streaming updates
- Client subscription management
- Message queuing and delivery
- Serialization with size limits
- FastAPI integration support

#### Developer Tools
- Graph visualization with Graphviz
- Comprehensive test suite
- Example workflows
- Jupyter notebook examples

### Documentation
- Complete README.md with examples
- API reference documentation
- Quick start guide
- Contributing guidelines
- Code of conduct
- Example scripts (quickstart, branching, multi-agent)
- JSON configuration example

### Dependencies
- pydantic >= 2.0.0
- fastapi >= 0.100.0
- sse-starlette >= 1.6.0
- uvicorn >= 0.23.0

### Known Issues
- SSE queue declared twice in `__init__` (lines 119-125) - minor duplication
- Parallel execution task duplication (lines 492-498) - minor duplication
- No built-in circular dependency detection
- Limited error recovery options

## [0.0.1] - 2023-12-01

### Added
- Initial prototype
- Basic graph structure
- Simple node execution
- Basic OpenAI integration

---

## Version History Summary

- **v0.1.0** - First stable release with core features
- **v0.0.1** - Initial prototype

## Upgrade Guide

### From 0.0.1 to 0.1.0

**Breaking Changes:**
- Renamed `context_history` to `agentic_memory`
- Changed `metahistory` structure to include execution IDs
- Updated node function signature to use `input_data` dictionary

**Migration Example:**

```python
# Old (0.0.1)
def my_node(state):
    return process(state)

# New (0.1.0)
def my_node(input_data: Dict[str, Any]) -> Dict[str, Any]:
    prev_data = input_data.get("PreviousNode", {})
    result = process(prev_data)
    return {"graph_data": result, "metahistory": None}
```

**New Features to Adopt:**
1. Use `chat_id` for session management
2. Configure SSE fields for real-time updates
3. Leverage parallel execution with `max_parallel`
4. Use branching edges for complex routing

## Support

For questions about changes or upgrade help:
- Open an issue on GitHub
- Check the documentation
- Review the examples directory

## Links

- [Repository](https://github.com/yourusername/nightsky)
- [Documentation](README.md)
- [Examples](examples/)
- [Contributing](CONTRIBUTING.md)

