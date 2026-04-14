"""
Execution Registry - Command execution routing

Routes commands to appropriate handlers.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional


class ExecutionRegistry:
    """
    Command execution registry.

    Routes commands to their handlers based on name.
    """

    def __init__(self):
        self._commands: Dict[str, Callable] = {}
        self._logger = logging.getLogger(__name__)

    def register_command(self, command: dict) -> None:
        """Register a command"""
        name = command.get("name")
        handler = command.get("handler")
        if name and handler:
            self._commands[name] = handler
            self._logger.debug(f"Registered command: {name}")

    def get_command(self, name: str) -> Optional[Callable]:
        """Get command handler"""
        return self._commands.get(name)

    def execute_command(self, name: str, **params) -> Any:
        """Execute a command"""
        handler = self.get_command(name)
        if not handler:
            raise ValueError(f"Command not found: {name}")
        return handler(**params)

    def list_commands(self) -> list:
        """List all registered commands"""
        return list(self._commands.keys())
