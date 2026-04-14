#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Pool - 工具池

动态工具管理，灵感来源: claw-code/src/tool_pool.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum
import logging


class ToolCategory(Enum):
    """工具类别"""
    EDITOR = "editor"           # 编辑器工具
    READER = "reader"           # 读取工具
    SEARCH = "search"           # 搜索工具
    SYSTEM = "system"           # 系统工具
    TEST = "test"              # 测试工具
    DEPLOY = "deploy"          # 部署工具
    LINTER = "linter"          # 代码检查
    GENERIC = "generic"         # 通用工具


@dataclass
class Tool:
    """
    工具定义
    """
    name: str
    description: str
    category: ToolCategory
    handler: Callable[..., Any]
    parameters: dict = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = True
    metadata: dict = field(default_factory=dict)
    
    def __call__(self, **kwargs) -> ToolResult:
        """执行工具"""
        if not self.enabled:
            return ToolResult(
                success=False,
                output="",
                error="Tool is disabled"
            )
        try:
            result = self.handler(**kwargs)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: Any = ""
    error: str = ""
    metadata: dict = field(default_factory=dict)


class ToolPool:
    """
    工具池
    
    管理所有可用工具，支持动态加载和查询
    """
    
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self.categories: dict[ToolCategory, list[str]] = {
            cat: [] for cat in ToolCategory
        }
        self.logger = logging.getLogger(__name__)
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        # 编辑器工具
        self.register(Tool(
            name="editor",
            description="编辑文件内容",
            category=ToolCategory.EDITOR,
            handler=self._editor_handler,
            capabilities=["create", "update", "delete"]
        ))
        
        # 读取工具
        self.register(Tool(
            name="reader",
            description="读取文件内容",
            category=ToolCategory.READER,
            handler=self._reader_handler,
            capabilities=["read", "list"]
        ))
        
        # 搜索工具
        self.register(Tool(
            name="searcher",
            description="搜索文件和内容",
            category=ToolCategory.SEARCH,
            handler=self._searcher_handler,
            capabilities=["grep", "find", "glob"]
        ))
        
        # 系统工具
        self.register(Tool(
            name="system_info",
            description="获取系统信息",
            category=ToolCategory.SYSTEM,
            handler=self._system_handler,
            capabilities=["info", "status"]
        ))
        
        # 测试工具
        self.register(Tool(
            name="tester",
            description="运行测试",
            category=ToolCategory.TEST,
            handler=self._tester_handler,
            capabilities=["run", "watch"]
        ))
        
        # 代码检查工具
        self.register(Tool(
            name="linter",
            description="代码检查",
            category=ToolCategory.LINTER,
            handler=self._linter_handler,
            capabilities=["check", "fix"]
        ))
        
        # 部署工具
        self.register(Tool(
            name="deployer",
            description="部署应用",
            category=ToolCategory.DEPLOY,
            handler=self._deployer_handler,
            capabilities=["deploy", "rollback"]
        ))
        
        # 项目探索工具
        self.register(Tool(
            name="explorer",
            description="探索项目结构",
            category=ToolCategory.READER,
            handler=self._explorer_handler,
            capabilities=["tree", "deps", "imports"]
        ))
        
        # 代码分析工具
        self.register(Tool(
            name="analyzer",
            description="分析代码",
            category=ToolCategory.READER,
            handler=self._analyzer_handler,
            capabilities=["ast", "metrics", "deps"]
        ))
    
    def register(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool
        self.categories[tool.category].append(tool.name)
        self.logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self.tools:
            tool = self.tools.pop(name)
            self.categories[tool.category].remove(name)
            return True
        return False
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def find(self, capability: str) -> list[Tool]:
        """根据能力查找工具"""
        return [
            tool for tool in self.tools.values()
            if capability in tool.capabilities and tool.enabled
        ]
    
    def list_by_category(self, category: ToolCategory) -> list[Tool]:
        """列出类别的工具"""
        names = self.categories.get(category, [])
        return [self.tools[name] for name in names if name in self.tools]
    
    def list_all(self) -> list[Tool]:
        """列出所有工具"""
        return list(self.tools.values())
    
    def execute(self, name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not found: {name}"
            )
        return tool(**kwargs)
    
    def enable(self, name: str) -> bool:
        """启用工具"""
        if name in self.tools:
            self.tools[name].enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用工具"""
        if name in self.tools:
            self.tools[name].enabled = False
            return True
        return False
    
    # ==================== 内置工具处理器 ====================
    
    def _editor_handler(self, action: str, path: str, content: str = None, **kwargs) -> dict:
        """编辑器处理器"""
        if action == "create":
            return {"status": "created", "path": path}
        elif action == "update":
            return {"status": "updated", "path": path}
        elif action == "delete":
            return {"status": "deleted", "path": path}
        return {"status": "unknown action"}
    
    def _reader_handler(self, path: str, **kwargs) -> dict:
        """读取处理器"""
        return {"status": "read", "path": path, "content": ""}
    
    def _searcher_handler(self, pattern: str, path: str = ".", **kwargs) -> dict:
        """搜索处理器"""
        return {"status": "found", "pattern": pattern, "matches": []}
    
    def _system_handler(self, action: str = "info", **kwargs) -> dict:
        """系统处理器"""
        return {"status": "ok", "action": action}
    
    def _tester_handler(self, path: str = ".", **kwargs) -> dict:
        """测试处理器"""
        return {"status": "passed", "tests": 0}
    
    def _linter_handler(self, path: str = ".", **kwargs) -> dict:
        """代码检查处理器"""
        return {"status": "clean", "issues": []}
    
    def _deployer_handler(self, action: str = "deploy", **kwargs) -> dict:
        """部署处理器"""
        return {"status": "deployed", "action": action}
    
    def _explorer_handler(self, path: str = ".", action: str = "tree", **kwargs) -> dict:
        """项目探索处理器"""
        return {"status": "explored", "tree": {}}
    
    def _analyzer_handler(self, path: str = ".", **kwargs) -> dict:
        """分析处理器"""
        return {"status": "analyzed", "metrics": {}}


class DynamicToolPool(ToolPool):
    """
    动态工具池 - 支持运行时添加工具
    """
    
    def __init__(self):
        super().__init__()
        self.plugin_tools: dict[str, Tool] = {}
    
    def load_from_plugin(self, plugin_name: str, tools: list[Tool]):
        """从插件加载工具"""
        for tool in tools:
            tool.metadata["plugin"] = plugin_name
            self.register(tool)
            self.plugin_tools[tool.name] = tool
    
    def unload_plugin(self, plugin_name: str) -> int:
        """卸载插件的工具"""
        to_remove = [
            name for name, tool in self.plugin_tools.items()
            if tool.metadata.get("plugin") == plugin_name
        ]
        for name in to_remove:
            self.unregister(name)
        return len(to_remove)
