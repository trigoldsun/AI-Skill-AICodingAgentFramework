#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime - 运行时引擎

核心编排引擎，灵感来源: claw-code/src/runtime.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from enum import Enum
import logging


class ExecutionMode(Enum):
    """执行模式"""
    SYNC = "sync"           # 同步执行
    ASYNC = "async"         # 异步执行
    STREAM = "stream"       # 流式执行


@dataclass
class ExecutionContext:
    """执行上下文"""
    session_id: str
    user_id: str = ""
    working_dir: str = "."
    env: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: Any = None
    error: str = ""
    duration: float = 0.0
    steps: list[dict] = field(default_factory=list)


class Runtime:
    """
    运行时引擎
    
    核心编排组件，协调各模块工作
    """
    
    def __init__(
        self,
        name: str = "agent",
        version: str = "1.0.0",
        llm_client: Optional[Any] = None
    ):
        self.name = name
        self.version = version
        self.llm_client = llm_client
        self.logger = logging.getLogger(f"runtime.{name}")
        
        # 组件
        self.parser = None
        self.query_engine = None
        self.tool_pool = None
        self.plugin_registry = None
        self.task_manager = None
        self.execution_registry = None
        
        # 状态
        self._initialized = False
        self._running = False
    
    def setup(self, config: dict = None):
        """
        初始化运行时
        
        Args:
            config: 配置字典
        """
        config = config or {}
        
        self.logger.info(f"Setting up runtime: {self.name} v{self.version}")
        
        # 初始化组件
        from .parser import Parser
        from .query_engine import QueryEngine
        from .tool_pool import ToolPool
        from .plugin_registry import PluginRegistry
        from .task_manager import TaskManager
        from .execution_registry import ExecutionRegistry
        
        self.parser = Parser()
        self.query_engine = QueryEngine(llm_enabled=self.llm_client is not None)
        self.tool_pool = ToolPool()
        self.plugin_registry = PluginRegistry()
        self.task_manager = TaskManager()
        self.execution_registry = ExecutionRegistry()
        
        # 注册默认命令
        self._register_default_commands()
        
        self._initialized = True
        self.logger.info("Runtime setup complete")
    
    def _register_default_commands(self):
        """注册默认命令"""
        from .tool_pool import ToolPool, Tool, ToolCategory, ToolResult
        
        # 注册基础命令
        self.execution_registry.register_command({
            "name": "parse",
            "description": "解析用户输入",
            "handler": lambda ctx, **kw: self.parser.parse(kw.get("query", ""))
        })
        
        self.execution_registry.register_command({
            "name": "analyze",
            "description": "分析查询",
            "handler": lambda ctx, **kw: self.query_engine.analyze(kw.get("query", ""))
        })
        
        self.execution_registry.register_command({
            "name": "route",
            "description": "路由决策",
            "handler": lambda ctx, **kw: self.query_engine.route(ctx.get("query_context", {}))
        })
        
        self.execution_registry.register_command({
            "name": "execute_tool",
            "description": "执行工具",
            "handler": lambda ctx, **kw: self.tool_pool.execute(
                kw.get("tool_name", ""),
                **kw.get("params", {})
            )
        })
    
    async def execute_async(
        self,
        query: str,
        context: ExecutionContext = None,
        mode: ExecutionMode = ExecutionMode.SYNC
    ) -> ExecutionResult:
        """
        异步执行查询
        
        Args:
            query: 用户查询
            context: 执行上下文
            mode: 执行模式
            
        Returns:
            ExecutionResult: 执行结果
        """
        import time
        start_time = time.time()
        
        if not self._initialized:
            self.setup()
        
        context = context or ExecutionContext(session_id="default")
        
        steps = []
        
        try:
            # 1. 解析
            steps.append({"name": "parse", "status": "running"})
            intent = self.parser.parse(query)
            steps[-1]["status"] = "completed"
            steps[-1]["output"] = intent.type.value
            
            # 2. 分析
            steps.append({"name": "analyze", "status": "running"})
            query_context = self.query_engine.analyze(query)
            steps[-1]["status"] = "completed"
            steps[-1]["output"] = query_context.query_type.value
            
            # 3. 路由
            steps.append({"name": "route", "status": "running"})
            route_result = self.query_engine.route(query_context)
            steps[-1]["status"] = "completed"
            steps[-1]["output"] = route_result.routing_path
            
            # 4. 执行计划
            if route_result.execution_plan:
                for plan_step in route_result.execution_plan:
                    steps.append({"name": plan_step, "status": "pending"})
            
            # 5. 工具执行
            if query_context.tools_needed:
                steps.append({"name": "execute_tools", "status": "running"})
                tool_outputs = []
                for tool_name in query_context.tools_needed:
                    result = self.tool_pool.execute(tool_name, query=query)
                    tool_outputs.append({"tool": tool_name, "result": result})
                steps[-1]["status"] = "completed"
                steps[-1]["output"] = tool_outputs
            
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                output={"intent": intent, "context": query_context},
                duration=duration,
                steps=steps
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                duration=duration,
                steps=steps
            )
    
    def execute(
        self,
        query: str,
        context: ExecutionContext = None
    ) -> ExecutionResult:
        """
        同步执行查询
        
        Args:
            query: 用户查询
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        import asyncio
        
        if not asyncio.get_event_loop().is_running():
            return asyncio.run(self.execute_async(query, context))
        else:
            # 如果已经在事件循环中，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute_async(query, context))
            finally:
                loop.close()
    
    def add_tool(self, name: str, handler: Callable, category: str = "generic"):
        """添加工具"""
        from .tool_pool import Tool, ToolCategory, ToolPool
        tool = Tool(
            name=name,
            description=f"Custom tool: {name}",
            category=ToolCategory(category),
            handler=handler
        )
        self.tool_pool.register(tool)
    
    def add_plugin(self, plugin):
        """添加插件"""
        self.plugin_registry.register(plugin)
    
    def get_status(self) -> dict:
        """获取状态"""
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "tools": len(self.tool_pool.tools) if self.tool_pool else 0,
            "plugins": len(self.plugin_registry.plugins) if self.plugin_registry else 0,
            "tasks": self.task_manager.get_stats() if self.task_manager else {}
        }
    
    def start(self):
        """启动运行时"""
        if not self._initialized:
            self.setup()
        self._running = True
        self.logger.info("Runtime started")
    
    def stop(self):
        """停止运行时"""
        self._running = False
        self.logger.info("Runtime stopped")


class Agent(Runtime):
    """
    智能体 - Runtime的高级封装
    
    提供更友好的接口
    """
    
    def __init__(
        self,
        name: str = "agent",
        model: str = "claude-3-5-sonnet",
        plugins: list = None,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.model = model
        self.plugins = plugins or []
    
    def run(self, query: str, **kwargs) -> Any:
        """
        运行查询
        
        Args:
            query: 用户查询
            **kwargs: 额外参数
            
        Returns:
            Any: 执行结果
        """
        result = self.execute(query, **kwargs)
        if result.success:
            return result.output
        else:
            raise RuntimeError(result.error)
