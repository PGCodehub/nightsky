# Contributing to NightSky AgentGraph

Thank you for your interest in contributing to NightSky AgentGraph! This document provides guidelines and instructions for contributing.

## 🌟 Ways to Contribute

- **Report Bugs**: Submit detailed bug reports with reproduction steps
- **Suggest Features**: Propose new features or enhancements
- **Improve Documentation**: Fix typos, add examples, clarify explanations
- **Write Code**: Fix bugs, implement features, optimize performance
- **Create Examples**: Share your use cases and workflows
- **Answer Questions**: Help other users in issues and discussions

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/nightsky.git
cd nightsky

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/nightsky.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
# Create a new branch for your feature or fix
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and modular
- Use meaningful variable and function names

Example:

```python
def process_node_data(
    input_data: Dict[str, Any],
    node_name: str,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Process data from a node in the graph.

    Args:
        input_data: Dictionary containing node outputs
        node_name: Name of the node to process
        validate: Whether to validate the data schema

    Returns:
        Processed data dictionary

    Raises:
        ValueError: If node_name is not found in input_data
    """
    if node_name not in input_data:
        raise ValueError(f"Node '{node_name}' not found in input data")

    # Your implementation here
    return processed_data
```

### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for high code coverage

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=NightSky --cov-report=html
```

### Documentation

- Update README.md if adding new features
- Add docstrings to new functions/classes
- Include examples for complex features
- Update type hints

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal code to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: Python version, OS, dependency versions
6. **Logs/Errors**: Full error messages and stack traces

Example:

````markdown
**Bug Description**
Graph execution hangs when using circular dependencies

**Steps to Reproduce**

```python
graph = AgenticGraph(graph_id="test")
graph.add_node("NodeA", func_a)
graph.add_node("NodeB", func_b)
graph.add_edge("NodeA", "NodeB")
graph.add_edge("NodeB", "NodeA")  # Circular!
await graph.execute(data)
```
````

**Expected Behavior**
Should raise a validation error about circular dependencies

**Actual Behavior**
Execution hangs indefinitely

**Environment**

- Python 3.10.5
- Windows 11
- nightsky-agentgraph 0.1.0

````

## 💡 Feature Requests

When suggesting features, please include:

1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches you considered
4. **Examples**: Code examples of how it would be used

Example:

```markdown
**Feature Request: Graph Checkpointing**

**Use Case**
For long-running workflows, I want to save progress and resume later if the process crashes.

**Proposed Solution**
Add methods to save/load graph state:
```python
# Save checkpoint
await graph.save_checkpoint("checkpoint.json")

# Resume from checkpoint
graph = AgenticGraph.load_checkpoint("checkpoint.json")
await graph.resume()
````

**Alternatives**

- Manual state serialization (current workaround)
- Database-backed state storage

**Benefits**

- Fault tolerance
- Easier debugging
- Resume interrupted workflows

````

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

```bash
# Update your branch
git fetch upstream
git rebase upstream/main
````

### 2. Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add support for parallel branching in multi-graphs"
git commit -m "Fix memory leak in SSE sender cleanup"
git commit -m "Update README with cross-graph examples"

# Bad
git commit -m "fix bug"
git commit -m "updates"
git commit -m "WIP"
```

### 3. Submit Pull Request

1. Push your branch to your fork
2. Open a Pull Request on GitHub
3. Fill out the PR template
4. Link related issues
5. Wait for review

### 4. PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

How has this been tested?

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
- [ ] All tests passing
```

## 📋 Code Review Process

### For Contributors

- Respond to feedback promptly
- Be open to suggestions
- Ask questions if unclear
- Update based on feedback
- Be patient and respectful

### For Reviewers

- Be constructive and kind
- Explain the "why" behind suggestions
- Acknowledge good work
- Test the changes if possible
- Approve when ready

## 🎯 Priority Areas

We especially welcome contributions in these areas:

1. **Performance Optimization**

   - Reduce memory usage for large graphs
   - Optimize parallel execution
   - Improve SSE throughput

2. **Testing & Quality**

   - Increase test coverage
   - Add integration tests
   - Stress testing for large graphs

3. **Documentation**

   - More real-world examples
   - Tutorial series
   - API reference improvements
   - Video tutorials

4. **Features**

   - Graph persistence and resumption
   - Enhanced visualization
   - More AI model integrations
   - Monitoring and metrics

5. **Tools & Infrastructure**
   - CI/CD improvements
   - Docker support
   - Benchmarking suite
   - Debug tooling

## 📚 Resources

- **Main Documentation**: [README.md](README.md)
- **Examples**: [examples/](examples/) and [test/](test/)
- **API Source**: [NightSky/AgentGraph.py](NightSky/AgentGraph.py)
- **Development Notes**: [Steps.md](Steps.md)

## ❓ Questions?

- Open a GitHub issue with the "question" label
- Check existing issues and discussions
- Review the documentation and examples

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone.

### Our Standards

**Positive Behaviors:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy towards others

**Unacceptable Behaviors:**

- Harassment or discriminatory language
- Personal attacks or insults
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Violations can be reported to project maintainers. All complaints will be reviewed and investigated promptly and fairly.

## 🙏 Thank You!

Your contributions make NightSky AgentGraph better for everyone. We appreciate your time and effort!

---

**Happy Contributing! 🚀**
