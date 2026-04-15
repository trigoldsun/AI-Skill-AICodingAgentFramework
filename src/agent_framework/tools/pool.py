"""
tools.pool - 工具注册与管理
Inspired by claw-code's tool execution framework
"""
from __future__ import annotations
from typing import Optional
from .base import Tool, ToolResult, ToolCategory


class ToolPool:
    """工具池 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: dict = {}
        self._categories: dict = {}
    
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)
    
    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)
    
    def list_all(self) -> list:
        return list(self._tools.keys())
    
    def list_by_category(self, category: ToolCategory) -> list:
        return self._categories.get(category, [])
    
    def get_tools_spec(self) -> list:
        return [tool.get_spec() for tool in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}", tool_name=name)
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=name)


def create_default_pool() -> ToolPool:
    """创建默认工具池"""
    from .bash import BashTool
    from .file_ops import ReadFileTool, WriteFileTool, EditFileTool
    from .search import GrepSearchTool, GlobSearchTool
    from .web import WebSearchTool, WebFetchTool
    
    pool = ToolPool()
    pool.register(BashTool())
    pool.register(ReadFileTool())
    pool.register(WriteFileTool())
    pool.register(EditFileTool())
    pool.register(GrepSearchTool())
    pool.register(GlobSearchTool())
    pool.register(WebSearchTool())
    pool.register(WebFetchTool())
    
    return pool
