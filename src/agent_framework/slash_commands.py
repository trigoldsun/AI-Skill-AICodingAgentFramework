"""
Slash Commands - REPL command surface

Inspired by claw-code's slash command system:
- Tab completion for commands
- Context-aware help
- JSON/text output formatting
- Session-aware commands

Commands:
    /help, /status, /doctor, /compact, /session
    /skills, /agents, /mcp, /tasks
    /diff, /commit, /pr
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class OutputFormat(Enum):
    """Command output format"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class CommandResult:
    """Result of a slash command"""
    success: bool
    output: Any = None
    error: str = ""
    format: OutputFormat = OutputFormat.TEXT


@dataclass
class Command:
    """
    Slash command definition.

    Attributes:
        name: Command name (without /)
        aliases: Alternative names
        description: Short description
        help_text: Detailed help text
        handler: Command handler function
        category: Command category
        examples: Usage examples
    """
    name: str
    description: str
    handler: Callable[[], CommandResult]
    aliases: List[str] = field(default_factory=list)
    help_text: str = ""
    category: str = "general"
    examples: List[str] = field(default_factory=list)
    requires_session: bool = False


class SlashCommandRegistry:
    """
    Registry for slash commands.

    Inspired by claw-code's command system:
    - Register commands with aliases
    - Tab completion support
    - Context-aware help
    - Category organization
    """

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[str, List[str]] = {}
        self._logger = logging.getLogger("slash_commands")

    def register(self, command: Command) -> None:
        """Register a slash command"""
        # Register primary name
        self._commands[command.name] = command

        # Register aliases
        for alias in command.aliases:
            self._commands[alias] = command

        # Register in category
        if command.category not in self._categories:
            self._categories[command.category] = []
        self._categories[command.category].append(command.name)

        self._logger.debug(f"Registered command: /{command.name}")

    def get(self, name: str) -> Optional[Command]:
        """Get command by name"""
        return self._commands.get(name)

    def list_commands(self, category: str = None) -> List[Command]:
        """List all commands, optionally filtered by category"""
        if category:
            names = self._categories.get(category, [])
            return [self._commands[name] for name in names]
        return list(self._commands.values())

    def list_categories(self) -> List[str]:
        """List all categories"""
        return list(self._categories.keys())

    def get_completions(self, prefix: str) -> List[str]:
        """Get tab completion suggestions"""
        prefix_lower = prefix.lower()
        return [
            name for name in self._commands.keys()
            if name.startswith(prefix_lower)
        ]


class SlashCommandHandler:
    """
    Handles slash command parsing and execution.

    Usage:
        handler = SlashCommandHandler()
        handler.register_default_commands()

        result = handler.execute("/doctor")
        result = handler.execute("/skills list")
    """

    def __init__(self, runtime=None):
        self.registry = SlashCommandRegistry()
        self.runtime = runtime
        self._setup_default_commands()

    def _setup_default_commands(self) -> None:
        """Register default commands"""

        # Help command
        self.registry.register(Command(
            name="help",
            description="Show help for commands",
            category="general",
            aliases=["?"],
            examples=["/help", "/help skills"],
            handler=lambda: self._cmd_help()
        ))

        # Status command
        self.registry.register(Command(
            name="status",
            description="Show current runtime status",
            category="session",
            examples=["/status"],
            handler=lambda: self._cmd_status()
        ))

        # Doctor command
        self.registry.register(Command(
            name="doctor",
            description="Run setup and preflight diagnostics",
            category="system",
            examples=["/doctor"],
            handler=lambda: self._cmd_doctor()
        ))

        # Compact command
        self.registry.register(Command(
            name="compact",
            description="Compact session to reduce context size",
            category="session",
            examples=["/compact"],
            handler=lambda: self._cmd_compact()
        ))

        # Session command
        self.registry.register(Command(
            name="session",
            description="Show current session info",
            category="session",
            examples=["/session", "/session list"],
            handler=lambda: self._cmd_session()
        ))

        # Skills command
        self.registry.register(Command(
            name="skills",
            description="List or manage skills",
            category="skills",
            aliases=["skill"],
            examples=["/skills", "/skills list", "/skills install path"],
            handler=lambda args: self._cmd_skills(args)
        ))

        # Tasks command
        self.registry.register(Command(
            name="tasks",
            description="Show task status",
            category="task",
            aliases=["task"],
            examples=["/tasks", "/tasks list", "/tasks 123"],
            handler=lambda args: self._cmd_tasks(args)
        ))

        # Cost command
        self.registry.register(Command(
            name="cost",
            description="Show usage costs",
            category="session",
            aliases=["usage"],
            examples=["/cost"],
            handler=lambda: self._cmd_cost()
        ))

        # Version command
        self.registry.register(Command(
            name="version",
            description="Show version info",
            category="system",
            aliases=["ver"],
            examples=["/version"],
            handler=lambda: self._cmd_version()
        ))

    def execute(self, command_line: str) -> CommandResult:
        """
        Execute a slash command.

        Args:
            command_line: Full command line with arguments

        Returns:
            CommandResult
        """
        command_line = command_line.strip()

        if not command_line.startswith("/"):
            return CommandResult(
                success=False,
                error="Commands must start with /"
            )

        # Parse command and args
        parts = command_line[1:].split(None, 1)
        command_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Look up command
        command = self.registry.get(command_name)
        if not command:
            return CommandResult(
                success=False,
                error=f"Unknown command: /{command_name}"
            )

        # Execute
        try:
            result = command.handler(args)
            return result
        except Exception as e:
            self._logger.error(f"Command failed: {e}")
            return CommandResult(
                success=False,
                error=str(e)
            )

    def _cmd_help(self, topic: str = "") -> CommandResult:
        """Show help"""
        if topic:
            command = self.registry.get(topic)
            if command:
                help_text = f"## /{command.name}\n\n{command.description}\n\n"
                if command.aliases:
                    help_text += f"**Aliases**: {', '.join(command.aliases)}\n"
                if command.help_text:
                    help_text += f"\n{command.help_text}\n"
                if command.examples:
                    help_text += "\n**Examples**:\n"
                    for ex in command.examples:
                        help_text += f"```\n{ex}\n```\n"
                return CommandResult(success=True, output=help_text)
            else:
                return CommandResult(success=False, error=f"Unknown topic: {topic}")

        # Show all commands
        output = "# Available Commands\n\n"
        for category in self.registry.list_categories():
            commands = self.registry.list_commands(category)
            output += f"## {category.title()}\n\n"
            for cmd in commands:
                output += f"- /{cmd.name}: {cmd.description}\n"
            output += "\n"

        return CommandResult(success=True, output=output)

    def _cmd_status(self) -> CommandResult:
        """Show runtime status"""
        if not self.runtime:
            return CommandResult(success=False, error="No runtime configured")

        status = self.runtime.get_status()
        return CommandResult(
            success=True,
            output=json.dumps(status, indent=2),
            format=OutputFormat.JSON
        )

    def _cmd_doctor(self) -> CommandResult:
        """Run diagnostics"""
        checks = []

        # Check Python version
        import sys
        checks.append({
            "name": "python_version",
            "status": "pass" if sys.version_info >= (3, 10) else "fail",
            "message": f"Python {sys.version_info.major}.{sys.version_info.minor}"
        })

        # Check runtime
        checks.append({
            "name": "runtime",
            "status": "pass" if self.runtime else "fail",
            "message": "Runtime initialized" if self.runtime else "Runtime not initialized"
        })

        # Check event bus
        if self.runtime and self.runtime.event_bus:
            checks.append({
                "name": "event_bus",
                "status": "pass",
                "message": "Event bus ready"
            })
        else:
            checks.append({
                "name": "event_bus",
                "status": "fail",
                "message": "Event bus not available"
            })

        # Check tools
        if self.runtime and self.runtime.tool_pool:
            tool_count = len(self.runtime.tool_pool.tools)
            checks.append({
                "name": "tools",
                "status": "pass",
                "message": f"{tool_count} tools registered"
            })
        else:
            checks.append({
                "name": "tools",
                "status": "warn",
                "message": "No tools registered"
            })

        # Summarize
        passed = sum(1 for c in checks if c["status"] == "pass")
        failed = sum(1 for c in checks if c["status"] == "fail")

        output = "# Doctor Check Results\n\n"
        for check in checks:
            icon = {"pass": "✅", "fail": "❌", "warn": "⚠️"}.get(check["status"], "•")
            output += f"{icon} **{check['name']}**: {check['message']}\n"

        output += f"\n**Summary**: {passed} passed, {failed} failed\n"

        return CommandResult(success=(failed == 0), output=output)

    def _cmd_compact(self) -> CommandResult:
        """Compact session"""
        if not self.runtime or not self.runtime.session_manager:
            return CommandResult(success=False, error="Session manager not available")

        session = self.runtime.session_manager.get_latest_session()
        if not session:
            return CommandResult(success=False, error="No active session")

        removed = session.compact()
        self.runtime.session_manager.update_session(session)

        return CommandResult(
            success=True,
            output=f"Compacted session: removed {removed} messages"
        )

    def _cmd_session(self, action: str = "") -> CommandResult:
        """Show session info"""
        if not self.runtime or not self.runtime.session_manager:
            return CommandResult(success=False, error="Session manager not available")

        if action == "list":
            sessions = self.runtime.session_manager.list_sessions(limit=5)
            output = "# Recent Sessions\n\n"
            for s in sessions:
                output += f"- {s.id}: {s.state.value} ({len(s.messages)} messages)\n"
            return CommandResult(success=True, output=output)

        session = self.runtime.session_manager.get_latest_session()
        if not session:
            return CommandResult(success=False, error="No active session")

        return CommandResult(
            success=True,
            output=json.dumps(session.to_dict(), indent=2),
            format=OutputFormat.JSON
        )

    def _cmd_skills(self, action: str = "") -> CommandResult:
        """List or manage skills"""
        if not self.runtime or not self.runtime.skill_registry:
            return CommandResult(success=False, error="Skill registry not available")

        skills = self.runtime.skill_registry.list_skills()

        if not action or action == "list":
            output = "# Available Skills\n\n"
            for skill in skills:
                output += f"- **{skill.get('name', 'unknown')}**: {skill.get('description', '')}\n"
            return CommandResult(success=True, output=output)

        return CommandResult(success=True, output=f"Skills: {len(skills)} loaded")

    def _cmd_tasks(self, action: str = "") -> CommandResult:
        """Show task status"""
        if not self.runtime or not self.runtime.task_manager:
            return CommandResult(success=False, error="Task manager not available")

        stats = self.runtime.task_manager.get_stats()

        if not action:
            output = "# Task Status\n\n"
            for status, count in stats.items():
                output += f"- {status}: {count}\n"
            return CommandResult(success=True, output=output)

        return CommandResult(
            success=True,
            output=json.dumps(stats, indent=2),
            format=OutputFormat.JSON
        )

    def _cmd_cost(self) -> CommandResult:
        """Show usage costs"""
        if not self.runtime or not self.runtime.telemetry:
            return CommandResult(success=False, error="Telemetry not available")

        stats = self.runtime.telemetry.get_stats()

        output = "# Usage Statistics\n\n"
        output += f"- Total queries: {stats['total_queries']}\n"
        output += f"- Successful: {stats['successful_queries']}\n"
        output += f"- Failed: {stats['failed_queries']}\n"
        output += f"- Total cost: ${stats['total_cost']:.4f}\n"
        output += f"- Avg duration: {stats['avg_duration']:.2f}s\n"

        return CommandResult(success=True, output=output)

    def _cmd_version(self) -> CommandResult:
        """Show version"""
        version_info = {
            "framework": "AI Coding Agent Framework",
            "version": "1.0.0",
            "python_min": "3.10"
        }

        return CommandResult(
            success=True,
            output=json.dumps(version_info, indent=2),
            format=OutputFormat.JSON
        )


# Convenience function
def create_handler(runtime=None) -> SlashCommandHandler:
    """Create a command handler with default commands"""
    return SlashCommandHandler(runtime)
