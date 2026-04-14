#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Coding Agent Framework - 核心框架

基于claw-code架构的智能软件开发框架
"""

__version__ = "1.0.0"
__author__ = "AI-Skill-AICodingAgentFramework"

from .parser import Parser, IntentType
from .query_engine import QueryEngine, QueryContext
from .tool_pool import ToolPool, Tool, ToolResult
from .plugin_registry import PluginRegistry, Plugin, Port
from .task_manager import TaskManager, Task, TaskStatus
from .runtime import Runtime, ExecutionContext
from .execution_registry import ExecutionRegistry, Command

__all__ = [
    # Parser
    "Parser",
    "IntentType",
    # QueryEngine
    "QueryEngine",
    "QueryContext",
    # ToolPool
    "ToolPool",
    "Tool",
    "ToolResult",
    # PluginRegistry
    "PluginRegistry",
    "Plugin",
    "Port",
    # TaskManager
    "TaskManager",
    "Task",
    "TaskStatus",
    # Runtime
    "Runtime",
    "ExecutionContext",
    # ExecutionRegistry
    "ExecutionRegistry",
    "Command",
]
