#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plugin Registry - 插件注册表

插件发现和管理，灵感来源: claw-code/src/port_manifest.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum
import logging


class PortType(Enum):
    """端口类型"""
    CODE_GENERATOR = "code_generator"     # 代码生成
    FILE_OPERATOR = "file_operator"       # 文件操作
    TEST_RUNNER = "test_runner"         # 测试运行
    DEPLOYER = "deployer"              # 部署
    ANALYZER = "analyzer"              # 分析
    CUSTOM = "custom"                  # 自定义


@dataclass
class Port:
    """
    端口定义 - 插件暴露的能力接口
    """
    name: str
    port_type: PortType
    description: str
    handler: Callable[..., Any]
    schema: dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Plugin:
    """
    插件定义
    """
    name: str
    version: str
    description: str
    author: str = ""
    ports: list[Port] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # 为每个port设置plugin信息
        for port in self.ports:
            port.metadata["plugin"] = self.name


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    ports: list[str]
    enabled: bool = True


class PluginRegistry:
    """
    插件注册表
    
    管理所有插件的注册、发现和生命周期
    """
    
    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self.ports: dict[str, Port] = {}  # port_name -> Port
        self.logger = logging.getLogger(__name__)
        self._register_builtin_ports()
    
    def _register_builtin_ports(self):
        """注册内置端口"""
        self.register_port(Port(
            name="builtin.echo",
            port_type=PortType.CUSTOM,
            description="内置回显端口",
            handler=lambda ctx, **kw: {"echo": kw.get("message", "")}
        ))
    
    def register(self, plugin: Plugin) -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
        """
        if plugin.name in self.plugins:
            self.logger.warning(f"Plugin {plugin.name} already registered, replacing")
        
        self.plugins[plugin.name] = plugin
        
        # 注册所有端口
        for port in plugin.ports:
            self.ports[port.name] = port
        
        self.logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def unregister(self, name: str) -> bool:
        """
        注销插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        if name not in self.plugins:
            return False
        
        plugin = self.plugins.pop(name)
        
        # 注销所有端口
        ports_to_remove = [
            port_name for port_name, port in self.ports.items()
            if port.metadata.get("plugin") == name
        ]
        for port_name in ports_to_remove:
            self.ports.pop(port_name)
        
        self.logger.info(f"Unregistered plugin: {name}")
        return True
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def get_port(self, name: str) -> Optional[Port]:
        """获取端口"""
        return self.ports.get(name)
    
    def find_ports(self, port_type: PortType) -> list[Port]:
        """查找指定类型的端口"""
        return [
            port for port in self.ports.values()
            if port.port_type == port_type and port.enabled
        ]
    
    def list_plugins(self) -> list[PluginInfo]:
        """列出所有插件"""
        return [
            PluginInfo(
                name=p.name,
                version=p.version,
                description=p.description,
                ports=[port.name for port in p.ports],
                enabled=all(port.enabled for port in p.ports)
            )
            for p in self.plugins.values()
        ]
    
    def list_ports(self, plugin_name: str = None) -> list[Port]:
        """列出端口"""
        if plugin_name:
            return [
                port for port in self.ports.values()
                if port.metadata.get("plugin") == plugin_name
            ]
        return list(self.ports.values())
    
    def enable_plugin(self, name: str) -> bool:
        """启用插件"""
        if name not in self.plugins:
            return False
        for port in self.plugins[name].ports:
            port.enabled = True
        return True
    
    def disable_plugin(self, name: str) -> bool:
        """禁用插件"""
        if name not in self.plugins:
            return False
        for port in self.plugins[name].ports:
            port.enabled = False
        return True
    
    def call_port(self, port_name: str, context: dict, **kwargs) -> Any:
        """
        调用端口
        
        Args:
            port_name: 端口名称
            context: 执行上下文
            **kwargs: 传递给handler的参数
            
        Returns:
            Any: 端口执行结果
        """
        port = self.get_port(port_name)
        if not port:
            raise ValueError(f"Port not found: {port_name}")
        
        if not port.enabled:
            raise RuntimeError(f"Port is disabled: {port_name}")
        
        return port.handler(context, **kwargs)


def plugin(name: str, version: str, description: str):
    """
    插件装饰器
    
    用法:
        @plugin("my_plugin", "1.0.0", "My plugin description")
        class MyPlugin(Plugin):
            ...
    """
    def decorator(cls):
        cls.name = name
        cls.version = version
        cls.description = description
        return cls
    return decorator


def port(name: str, port_type: PortType, description: str):
    """
    端口装饰器
    
    用法:
        @port("generate", PortType.CODE_GENERATOR, "生成代码")
        def generate_code(context, **kwargs):
            ...
    """
    def decorator(func):
        func._port_name = name
        func._port_type = port_type
        func._port_description = description
        return func
    return decorator
