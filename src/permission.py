"""
Permission System - Workspace protection and permission enforcement

Inspired by claw-code's permission model:
- read-only: File reads only, no writes
- workspace-write: Write within project boundaries
- danger-full-access: Full filesystem and shell access

Design principles:
1. Deny by default - explicit permission required
2. Workspace boundaries - prevent path traversal
3. Dangerous command detection - warn on destructive operations
4. Tool-specific permission requirements

Permission enforcement happens at multiple layers:
1. Query time: Permission mode attached to context
2. Tool execution: Each tool checks permission
3. Command time: Bash commands validated before execution
"""

from __future__ import annotations

import os
import re
import hashlib
import hmac
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Set


class PermissionMode(Enum):
    """
    Permission modes define what operations are allowed.

    These map to claw-code's permission modes:
    - read-only: Strict read-only, no file modifications
    - workspace-write: Write within project boundaries only
    - danger-full-access: Full filesystem + shell access
    """
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    DANGER_FULL_ACCESS = "danger-full-access"


@dataclass
class PermissionResult:
    """
    Result of a permission check.

    Attributes:
        allowed: Whether the operation is permitted
        reason: Human-readable reason for denial/allowance
        required_mode: Minimum mode required (if denied)
        warnings: List of warnings for the operation
    """
    allowed: bool
    reason: str = ""
    required_mode: Optional[PermissionMode] = None
    warnings: list = field(default_factory=list)


@dataclass
class Permission:
    """
    Permission specification for an operation.

    Attributes:
        mode: Required permission mode
        workspace_root: Root directory for workspace mode
        allowed_paths: Explicitly allowed paths (for exceptions)
        denied_paths: Explicitly denied paths
        allowed_commands: Shell commands allowed (for bash tool)
        denied_commands: Shell commands denied
    """
    mode: PermissionMode = PermissionMode.READ_ONLY
    workspace_root: str = "."
    allowed_paths: Set[str] = field(default_factory=set)
    denied_paths: Set[str] = field=set
    allowed_commands: Set[str] = field(default_factory=set)
    denied_commands: Set[str] = field(default_factory=set)

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",        # Root deletion
        r"rm\s+-rf\s+\*",        # Recursive deletion
        r":\(\)\{",              # Fork bomb
        r"dd\s+if=.*of=/dev/",   # Disk write
        r"mkfs",                 # Format filesystem
        r"chmod\s+-R\s+777",     # World writable
        r"curl.*\|.*sh",         # Pipe to shell
        r"wget.*\|.*sh",         # Pipe to shell
        r">\s*/etc/",            # Write to system config
        r">\s*/var/",            # Write to system var
    ]

    # Read-only safe patterns
    SAFE_PATTERNS = [
        r"^cat\s+",             # Read file
        r"^head\s+",            # Read file head
        r"^tail\s+",            # Read file tail
        r"^grep\s+",            # Search
        r"^ls\s+",              # List directory
        r"^pwd",                # Current directory
        r"^cd\s+",              # Change directory
        r"^find\s+",            # Find files
    ]


class PermissionEnforcer:
    """
    Permission enforcement layer.

    Inspired by claw-code's PermissionEnforcer:
    - check(): Core permission check
    - check_file_write(): File write boundary checks
    - check_bash(): Command safety validation

    The enforcer implements deny-by-default:
    - Every operation must pass permission checks
    - Workspace mode restricts writes to project boundaries
    - Dangerous commands require full access
    """

    def __init__(self, config: Permission = None):
        self.config = config or Permission()
        self.logger = logging.getLogger("permission_enforcer")

        # Salt for HMAC validation (prevents tampering)
        self._salt = "AI-Coding-Agent:v1.0:permission"

    def check(
        self,
        query: str,
        mode: PermissionMode = PermissionMode.READ_ONLY
    ) -> PermissionResult:
        """
        Check if a query is allowed under the given permission mode.

        Args:
            query: Natural language query or command
            mode: Current permission mode

        Returns:
            PermissionResult with allowed status and reasoning
        """
        # Detect required permission from query content
        required = self._detect_required_permission(query)

        # Check if current mode is sufficient
        if not self._is_mode_sufficient(mode, required):
            return PermissionResult(
                allowed=False,
                reason=f"Operation requires {required.value}, current mode is {mode.value}",
                required_mode=required
            )

        # Generate warnings for dangerous operations
        warnings = self._generate_warnings(query, mode)

        return PermissionResult(
            allowed=True,
            warnings=warnings
        )

    def check_file_write(
        self,
        path: str,
        mode: PermissionMode = PermissionMode.READ_ONLY
    ) -> PermissionResult:
        """
        Check if writing to a path is allowed.

        Args:
            path: Target file path
            mode: Current permission mode

        Returns:
            PermissionResult
        """
        # Read-only mode never allows writes
        if mode == PermissionMode.READ_ONLY:
            return PermissionResult(
                allowed=False,
                reason="Write operations are not allowed in read-only mode"
            )

        # Check workspace boundaries
        if mode == PermissionMode.WORKSPACE_WRITE:
            if not self._is_in_workspace(path):
                return PermissionResult(
                    allowed=False,
                    reason=f"Path '{path}' is outside the workspace boundary",
                    required_mode=PermissionMode.DANGER_FULL_ACCESS
                )

        # Check explicit denials
        if path in self.config.denied_paths:
            return PermissionResult(
                allowed=False,
                reason=f"Path '{path}' is explicitly denied"
            )

        return PermissionResult(allowed=True)

    def check_bash(
        self,
        command: str,
        mode: PermissionMode = PermissionMode.READ_ONLY
    ) -> PermissionResult:
        """
        Check if a bash command is allowed.

        Inspired by claw-code's bash validation:
        - Read-only mode: Only safe read commands
        - Workspace mode: Read + limited write
        - Danger mode: All commands allowed (with warnings)

        Args:
            command: Bash command string
            mode: Current permission mode

        Returns:
            PermissionResult
        """
        # Read-only mode: only safe patterns allowed
        if mode == PermissionMode.READ_ONLY:
            for pattern in Permission.SAFE_PATTERNS:
                if re.match(pattern, command.strip()):
                    return PermissionResult(allowed=True)

            return PermissionResult(
                allowed=False,
                reason="Only read operations are allowed in read-only mode",
                required_mode=PermissionMode.WORKSPACE_WRITE
            )

        # Check for dangerous patterns (always blocked)
        for pattern in Permission.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return PermissionResult(
                    allowed=False,
                    reason=f"Command matches dangerous pattern: {pattern}"
                )

        # Check explicit denials
        for denied in self.config.denied_commands:
            if denied in command:
                return PermissionResult(
                    allowed=False,
                    reason=f"Command contains denied pattern: {denied}"
                )

        # Generate warnings for potentially dangerous commands
        warnings = []
        danger_keywords = ["rm", "mv", "dd", "chmod", "chown", "kill"]
        for kw in danger_keywords:
            if kw in command:
                warnings.append(f"Potentially dangerous command: {kw}")

        return PermissionResult(
            allowed=True,
            warnings=warnings
        )

    def check_tool_access(
        self,
        tool_name: str,
        mode: PermissionMode = PermissionMode.READ_ONLY
    ) -> PermissionResult:
        """
        Check if a tool is accessible under the given mode.

        Args:
            tool_name: Name of the tool
            mode: Current permission mode

        Returns:
            PermissionResult
        """
        # Tool permission requirements
        TOOL_REQUIREMENTS = {
            "bash": PermissionMode.DANGER_FULL_ACCESS,
            "shell": PermissionMode.DANGER_FULL_ACCESS,
            "execute": PermissionMode.DANGER_FULL_ACCESS,
            "read_file": PermissionMode.READ_ONLY,
            "write_file": PermissionMode.WORKSPACE_WRITE,
            "edit_file": PermissionMode.WORKSPACE_WRITE,
            "grep": PermissionMode.READ_ONLY,
            "glob": PermissionMode.READ_ONLY,
            "web_search": PermissionMode.READ_ONLY,
            "web_fetch": PermissionMode.READ_ONLY,
        }

        required = TOOL_REQUIREMENTS.get(tool_name, PermissionMode.WORKSPACE_WRITE)

        if not self._is_mode_sufficient(mode, required):
            return PermissionResult(
                allowed=False,
                reason=f"Tool '{tool_name}' requires {required.value}",
                required_mode=required
            )

        return PermissionResult(allowed=True)

    def _detect_required_permission(self, query: str) -> PermissionMode:
        """Detect required permission from query content"""
        query_lower = query.lower()

        # Write indicators
        write_keywords = [
            "create", "write", "modify", "update", "edit", "delete",
            "implement", "generate", "build", "deploy", "install"
        ]
        for kw in write_keywords:
            if kw in query_lower:
                return PermissionMode.WORKSPACE_WRITE

        # Danger indicators
        danger_keywords = [
            "sudo", "rm", "chmod", "kill", "fork", "exec", "shell"
        ]
        for kw in danger_keywords:
            if kw in query_lower:
                return PermissionMode.DANGER_FULL_ACCESS

        return PermissionMode.READ_ONLY

    def _is_mode_sufficient(
        self,
        current: PermissionMode,
        required: PermissionMode
    ) -> bool:
        """Check if current mode satisfies required mode"""
        hierarchy = {
            PermissionMode.READ_ONLY: 1,
            PermissionMode.WORKSPACE_WRITE: 2,
            PermissionMode.DANGER_FULL_ACCESS: 3,
        }
        return hierarchy[current] >= hierarchy[required]

    def _is_in_workspace(self, path: str) -> bool:
        """Check if path is within workspace boundaries"""
        workspace_root = os.path.abspath(self.config.workspace_root)

        try:
            abs_path = os.path.abspath(path)
            return abs_path.startswith(workspace_root)
        except Exception:
            return False

    def _generate_warnings(
        self,
        query: str,
        mode: PermissionMode
    ) -> list:
        """Generate warnings for potentially dangerous operations"""
        warnings = []
        query_lower = query.lower()

        # Warning for destructive keywords
        destructive_keywords = ["delete", "remove", "drop", "truncate"]
        for kw in destructive_keywords:
            if kw in query_lower:
                warnings.append(f"Operation may be destructive: {kw}")

        # Warning for system modifications
        system_keywords = ["sudo", "chmod", "chown", "systemctl"]
        for kw in system_keywords:
            if kw in query_lower:
                warnings.append(f"System modification detected: {kw}")

        return warnings

    def authorize(
        self,
        query: str,
        mode: PermissionMode,
        hmac_key: str = None
    ) -> PermissionResult:
        """
        Authorize an operation with optional HMAC validation.

        HMAC validation prevents permission escalation through
        tampered context. The key should be session-specific.

        Args:
            query: Operation query
            mode: Permission mode
            hmac_key: Optional HMAC key for validation

        Returns:
            PermissionResult
        """
        result = self.check(query, mode)

        if hmac_key:
            # Validate HMAC to prevent tampering
            expected = hmac.new(
                self._salt.encode(),
                f"{query}:{mode.value}".encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected, hmac_key):
                return PermissionResult(
                    allowed=False,
                    reason="HMAC validation failed - possible permission tampering"
                )

        return result


def create_permission_checker(
    mode: PermissionMode,
    workspace_root: str = "."
) -> Callable[[str], PermissionResult]:
    """
    Create a permission checker function for a specific mode.

    Usage:
        check = create_permission_checker(PermissionMode.WORKSPACE_WRITE, "/project")
        result = check("create a new file")
    """
    enforcer = PermissionEnforcer(
        Permission(mode=mode, workspace_root=workspace_root)
    )
    return lambda query: enforcer.check(query, mode)
