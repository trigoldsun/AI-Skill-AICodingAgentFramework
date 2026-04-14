#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execution Registry - 执行注册表

命令路由和执行，灵感来源: claw-code/src/execution_registry.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum
import logging


class CommandType(Enum):
    """命令类型"""
    SYSTEM = "system"
    TOOL = "tool"
    PLUGIN = "plugin"
    LLM = "llm"
    CUSTOM = "custom"


@dataclass
class Command:
    """
    命令定义
    """
    name: str
    command_type: CommandType
    description: str
    handler: Callable
    parameters: dict = field(default_factory=dict)
    enabled: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    output: Any = None
    error: str = ""
    duration: float = 0.0
    command: str = ""


class ExecutionRegistry:
    """
    执行注册表
    
    管理命令的注册和路由
    """
    
    def __init__(self):
        self.commands: dict[str, Command] = {}
        self.aliases: dict[str, str] = {}  # alias -> command_name
        self.logger = logging.getLogger(__name__)
        
        self._register_builtin_commands()
    
    def _register_builtin_commands(self):
        """注册内置命令"""
        self.register_command(Command(
            name="help",
            command_type=CommandType.SYSTEM,
            description="显示帮助信息",
            handler=self._help_handler
        ))
        
        self.register_command(Command(
            name="status",
            command_type=CommandType.SYSTEM,
            description="显示状态",
            handler=self._status_handler
        ))
        
        self.register_command(Command(
            name="list",
            command_type=CommandType.SYSTEM,
            description="列出所有命令",
            handler=self._list_handler
        ))
    
    def register_command(self, command: Command) -> None:
        """
        注册命令
        
        Args:
            command: 命令对象
        """
        self.commands[command.name] = command
        self.logger.debug(f"Registered command: {command.name}")
    
    def register_command_dict(self, cmd_dict: dict) -> None:
        """
        从字典注册命令
        
        Args:
            cmd_dict: 命令字典
        """
        command = Command(
            name=cmd_dict["name"],
            command_type=CommandType(cmd_dict.get("type", "custom")),
            description=cmd_dict.get("description", ""),
            handler=cmd_dict.get("handler", lambda ctx, **kw: {})
        )
        self.register_command(command)
    
    def unregister_command(self, name: str) -> bool:
        """注销命令"""
        if name in self.commands:
            self.commands.pop(name)
            return True
        return False
    
    def add_alias(self, alias: str, command_name: str) -> bool:
        """
        添加命令别名
        
        Args:
            alias: 别名
            command_name: 实际命令名
        """
        if command_name not in self.commands:
            self.logger.warning(f"Command not found: {command_name}")
            return False
        
        self.aliases[alias] = command_name
        return True
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        获取命令
        
        Args:
            name: 命令名或别名
            
        Returns:
            Optional[Command]: 命令对象
        """
        # 检查别名
        if name in self.aliases:
            name = self.aliases[name]
        
        return self.commands.get(name)
    
    def list_commands(self, command_type: CommandType = None) -> list[Command]:
        """
        列出命令
        
        Args:
            command_type: 按类型过滤
            
        Returns:
            list[Command]: 命令列表
        """
        commands = self.commands.values()
        if command_type:
            commands = [c for c in commands if c.command_type == command_type]
        return list(commands)
    
    def execute(
        self,
        name: str,
        context: dict = None,
        **kwargs
    ) -> CommandResult:
        """
        执行命令
        
        Args:
            name: 命令名
            context: 执行上下文
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 执行结果
        """
        import time
        start_time = time.time()
        
        command = self.get_command(name)
        
        if not command:
            return CommandResult(
                success=False,
                error=f"Command not found: {name}",
                duration=0.0,
                command=name
            )
        
        if not command.enabled:
            return CommandResult(
                success=False,
                error=f"Command is disabled: {name}",
                duration=0.0,
                command=name
            )
        
        try:
            result = command.handler(context or {}, **kwargs)
            duration = time.time() - start_time
            
            return CommandResult(
                success=True,
                output=result,
                duration=duration,
                command=name
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Command execution failed: {name} - {e}")
            
            return CommandResult(
                success=False,
                error=str(e),
                duration=duration,
                command=name
            )
    
    def _help_handler(self, context: dict, **kwargs) -> dict:
        """帮助处理器"""
        return {
            "type": "help",
            "message": "AI Coding Agent Framework",
            "commands": [c.name for c in self.commands.values()]
        }
    
    def _status_handler(self, context: dict, **kwargs) -> dict:
        """状态处理器"""
        return {
            "type": "status",
            "total_commands": len(self.commands),
            "enabled": sum(1 for c in self.commands.values() if c.enabled)
        }
    
    def _list_handler(self, context: dict, **kwargs) -> dict:
        """列表处理器"""
        return {
            "type": "list",
            "commands": [
                {
                    "name": c.name,
                    "type": c.command_type.value,
                    "description": c.description,
                    "enabled": c.enabled
                }
                for c in self.commands.values()
            ]
        }


class Router:
    """
    命令路由器
    
    根据条件自动路由到合适的命令
    """
    
    def __init__(self, registry: ExecutionRegistry = None):
        self.registry = registry or ExecutionRegistry()
        self.routes: list[dict] = []  # {pattern, command, condition}
    
    def add_route(
        self,
        pattern: str,
        command: str,
        condition: Callable = None
    ):
        """
        添加路由规则
        
        Args:
            pattern: 匹配模式（简单前缀匹配）
            command: 目标命令
            condition: 额外条件函数
        """
        self.routes.append({
            "pattern": pattern,
            "command": command,
            "condition": condition
        })
    
    def route(self, query: str, context: dict = None) -> Optional[CommandResult]:
        """
        路由查询
        
        Args:
            query: 查询字符串
            context: 执行上下文
            
        Returns:
            Optional[CommandResult]: 执行结果
        """
        for route in self.routes:
            if query.startswith(route["pattern"]):
                # 检查条件
                if route["condition"]:
                    if not route["condition"](context or {}):
                        continue
                
                # 执行命令
                return self.registry.execute(
                    route["command"],
                    context,
                    query=query
                )
        
        return None


class SmartRouter(Router):
    """
    智能路由器
    
    支持更多路由策略
    """
    
    def route_by_keywords(self, query: str, context: dict = None) -> Optional[CommandResult]:
        """
        基于关键词路由
        
        Args:
            query: 查询
            context: 上下文
            
        Returns:
            CommandResult: 结果
        """
        keywords = {
            "创建": "create",
            "删除": "delete", 
            "修改": "update",
            "查询": "query",
            "帮助": "help"
        }
        
        for kw, cmd in keywords.items():
            if kw in query:
                return self.registry.execute(cmd, context, query=query)
        
        return None
    
    def route_by_intent(self, intent: dict, context: dict = None) -> Optional[CommandResult]:
        """
        基于意图路由
        
        Args:
            intent: 意图分析结果
            context: 上下文
            
        Returns:
            CommandResult: 结果
        """
        intent_type = intent.get("type", "unknown")
        
        cmd_map = {
            "create": "create",
            "read": "read",
            "update": "update",
            "delete": "delete"
        }
        
        cmd = cmd_map.get(intent_type)
        if cmd:
            return self.registry.execute(cmd, context, **intent)
        
        return None
