"""
AI Coding Agent Framework - Core Package

A next-generation autonomous software development framework
inspired by claw-code's coordination philosophy.

Usage:
    from agent_framework import Agent, PermissionMode

    agent = Agent(name="dev", model="sonnet")
    result = agent.run("Create a REST API")
"""

from .runtime import AgentRuntime, Agent, AgentState, ExecutionContext, ExecutionResult
from .event_bus import Event, EventBus, EventType, EventSummary
from .permission import Permission, PermissionMode, PermissionResult, PermissionEnforcer
from .task_manager import Task, TaskStatus, TaskPriority, TaskManager, TaskRegistry
from .session import Session, SessionState, SessionManager, Message
from .telemetry import Telemetry, UsageRecord, CostTracker
from .slash_commands import SlashCommandHandler, Command, CommandResult
from .query_engine import QueryEngine, QueryType, Complexity, QueryContext, QueryResult
from .tool_pool import ToolPool, Tool, ToolCategory, ToolResult
from .skill_registry import SkillRegistry, Skill

__version__ = "1.0.0"
__all__ = [
    # Runtime
    "AgentRuntime",
    "Agent",
    "AgentState",
    "ExecutionContext",
    "ExecutionResult",
    # Events
    "Event",
    "EventBus",
    "EventType",
    "EventSummary",
    # Permission
    "Permission",
    "PermissionMode",
    "PermissionResult",
    "PermissionEnforcer",
    # Tasks
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskManager",
    "TaskRegistry",
    # Session
    "Session",
    "SessionState",
    "SessionManager",
    "Message",
    # Telemetry
    "Telemetry",
    "UsageRecord",
    "CostTracker",
    # Commands
    "SlashCommandHandler",
    "Command",
    "CommandResult",
    # Query
    "QueryEngine",
    "QueryType",
    "Complexity",
    "QueryContext",
    "QueryResult",
    # Tools
    "ToolPool",
    "Tool",
    "ToolCategory",
    "ToolResult",
    # Skills
    "SkillRegistry",
    "Skill",
]
