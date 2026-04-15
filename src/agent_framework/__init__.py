"""
AI Coding Agent Framework - Core Package v1.1.0

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

# v1.1.0 新增组件
try:
    from .providers import create_provider, get_available_providers, MODEL_ALIASES
    from .providers.base import Provider, LLMMessage
    HAS_PROVIDERS = True
except ImportError:
    HAS_PROVIDERS = False

try:
    from .tools import create_default_pool
    from .tools.base import ToolResult as RealToolResult
    HAS_TOOLS = True
except ImportError:
    HAS_TOOLS = False

try:
    from .planning import Planner, ExecutionPlan, PlanStep, AVAILABLE_STEPS
    HAS_PLANNING = True
except ImportError:
    HAS_PLANNING = False

try:
    from .mocks import run_parity_harness, ParityHarness, MockAnthropicService
    HAS_MOCKS = True
except ImportError:
    HAS_MOCKS = False

try:
    from .cli import run_doctor
    HAS_CLI = True
except ImportError:
    HAS_CLI = False

__version__ = "1.1.0"

__all__ = [
    # Core Runtime
    "Agent", "AgentRuntime", "AgentState", "ExecutionContext", "ExecutionResult",
    # Events
    "Event", "EventBus", "EventType", "EventSummary",
    # Permission
    "Permission", "PermissionMode", "PermissionResult", "PermissionEnforcer",
    # Tasks
    "Task", "TaskStatus", "TaskPriority", "TaskManager", "TaskRegistry",
    # Session
    "Session", "SessionState", "SessionManager", "Message",
    # Telemetry
    "Telemetry", "UsageRecord", "CostTracker",
    # Commands
    "SlashCommandHandler", "Command", "CommandResult",
    # Query
    "QueryEngine", "QueryType", "Complexity", "QueryContext", "QueryResult",
    # Tools
    "ToolPool", "Tool", "ToolCategory", "ToolResult",
    # Skills
    "SkillRegistry", "Skill",
    # v1.1.0 新增
    "create_provider", "get_available_providers", "MODEL_ALIASES", "Provider", "LLMMessage",
    "create_default_pool",
    "Planner", "ExecutionPlan", "PlanStep", "AVAILABLE_STEPS",
    "run_parity_harness", "ParityHarness", "MockAnthropicService",
    "run_doctor",
    "HAS_PROVIDERS", "HAS_TOOLS", "HAS_PLANNING", "HAS_MOCKS", "HAS_CLI",
    "__version__",
]
