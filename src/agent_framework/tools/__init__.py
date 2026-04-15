"""
tools - 真实可执行工具集
Inspired by claw-code's tool system
"""
from .base import Tool, ToolResult, ToolCategory
from .pool import ToolPool, create_default_pool
from .bash import BashTool
from .file_ops import ReadFileTool, WriteFileTool, EditFileTool
from .search import GrepSearchTool, GlobSearchTool
from .web import WebSearchTool, WebFetchTool

__all__ = [
    "Tool", "ToolResult", "ToolCategory", "ToolPool", "create_default_pool",
    "BashTool", "ReadFileTool", "WriteFileTool", "EditFileTool",
    "GrepSearchTool", "GlobSearchTool", "WebSearchTool", "WebFetchTool",
]
