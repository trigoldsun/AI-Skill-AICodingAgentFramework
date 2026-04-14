"""
Tool Pool - Dynamic tool registration and execution

Inspired by claw-code's tool system:
- Bash, Read, Write, Edit, Grep, Glob
- Web search and fetch
- Tool discovery and lifecycle
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ToolCategory(Enum):
    """Tool categories"""
    FILE = "file"
    SHELL = "shell"
    SEARCH = "search"
    WEB = "web"
    CODE = "code"
    SYSTEM = "system"
    GENERIC = "generic"


@dataclass
class ToolResult:
    """Result of tool execution"""
    success: bool
    output: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)


class Tool:
    """
    Tool definition.

    Attributes:
        name: Tool identifier
        description: Human-readable description
        category: Tool category
        handler: Execution function
        parameters: Parameter schema
    """

    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory = ToolCategory.GENERIC,
        handler: Callable = None,
        parameters: dict = None
    ):
        self.name = name
        self.description = description
        self.category = category
        self.handler = handler
        self.parameters = parameters or {}

    def execute(self, **params) -> ToolResult:
        """Execute the tool"""
        if not self.handler:
            return ToolResult(success=False, error="No handler configured")
        try:
            result = self.handler(**params)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ToolPool:
    """
    Tool registry and execution pool.

    Manages tool lifecycle and execution.
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, tool: Tool) -> None:
        """Register a tool"""
        self.tools[tool.name] = tool
        self._logger.debug(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def list(self, category: ToolCategory = None) -> List[Tool]:
        """List tools, optionally filtered by category"""
        if category:
            return [t for t in self.tools.values() if t.category == category]
        return list(self.tools.values())

    def execute(self, name: str, **params) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        return tool.execute(**params)


# Built-in tools
class BashTool(Tool):
    def __init__(self):
        super().__init__(
            name="bash",
            description="Execute bash commands",
            category=ToolCategory.SHELL
        )

    def execute(self, command: str, timeout: int = 30, **params) -> ToolResult:
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                text=True
            )
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else ""
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Command timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadFileTool(Tool):
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read file contents",
            category=ToolCategory.FILE
        )

    def execute(self, path: str, offset: int = 0, limit: int = 1000, **params) -> ToolResult:
        try:
            with open(path, 'r') as f:
                f.seek(offset)
                content = f.read(limit)
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(Tool):
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to file",
            category=ToolCategory.FILE
        )

    def execute(self, path: str, content: str, **params) -> ToolResult:
        try:
            with open(path, 'w') as f:
                f.write(content)
            return ToolResult(success=True, output=f"Written to {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditFileTool(Tool):
    def __init__(self):
        super().__init__(
            name="edit_file",
            description="Edit file with old/new string replacement",
            category=ToolCategory.FILE
        )

    def execute(self, path: str, old_string: str, new_string: str, **params) -> ToolResult:
        try:
            with open(path, 'r') as f:
                content = f.read()
            content = content.replace(old_string, new_string)
            with open(path, 'w') as f:
                f.write(content)
            return ToolResult(success=True, output=f"Edited {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GlobSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="glob_search",
            description="Find files matching pattern",
            category=ToolCategory.SEARCH
        )

    def execute(self, pattern: str, **params) -> ToolResult:
        import glob
        try:
            matches = glob.glob(pattern, recursive=True)
            return ToolResult(success=True, output=matches)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GrepSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="grep_search",
            description="Search for pattern in files",
            category=ToolCategory.SEARCH
        )

    def execute(self, pattern: str, path: str = ".", **params) -> ToolResult:
        import subprocess
        try:
            result = subprocess.run(
                ["grep", "-r", pattern, path],
                capture_output=True,
                text=True
            )
            return ToolResult(
                success=True,
                output=result.stdout if result.stdout else "No matches found"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
