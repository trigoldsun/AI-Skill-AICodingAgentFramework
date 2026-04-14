# Examples

Usage examples for AI Coding Agent Framework.

## Basic Usage

```python
from agent_framework import Agent, PermissionMode

agent = Agent(name="dev")
result = agent.run("Create a REST API for user authentication")
```

## With Custom Tools

```python
from agent_framework import Agent, Tool, ToolCategory

def my_tool(param: str) -> str:
    return f"Result: {param}"

agent = Agent(name="dev")
agent.add_tool("my_tool", my_tool, ToolCategory.GENERIC)
result = agent.run("Use my_tool to process data")
```
