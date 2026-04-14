#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Coding Agent Framework - 示例

展示框架的使用方式
"""

from agent_framework import (
    Runtime,
    ExecutionContext,
    Parser,
    IntentType
)


def basic_example():
    """基础示例"""
    print("=== 基础示例 ===")
    
    # 创建运行时
    runtime = Runtime(name="demo-agent", version="1.0.0")
    runtime.setup()
    
    # 执行查询
    result = runtime.execute("创建一个用户认证的REST API")
    
    print(f"Success: {result.success}")
    print(f"Steps: {len(result.steps)}")
    print(f"Duration: {result.duration:.2f}s")


def parser_example():
    """解析器示例"""
    print("\n=== 解析器示例 ===")
    
    parser = Parser()
    
    queries = [
        "创建一个用户登录API",
        "查看项目结构",
        "删除旧文件",
        "搜索bug相关代码"
    ]
    
    for query in queries:
        intent = parser.parse(query)
        print(f"Query: {query}")
        print(f"  Intent: {intent.type.value}")
        print(f"  Entities: {[e.name for e in intent.entities]}")
        print()


def runtime_example():
    """运行时示例"""
    print("\n=== 运行时示例 ===")
    
    # 创建并启动
    runtime = Runtime(name="assistant")
    runtime.start()
    
    # 添加工具
    runtime.add_tool("greet", lambda **kw: {"message": f"Hello, {kw.get('name', 'World')}!"})
    
    # 执行
    result = runtime.execute("greet", name="Alice")
    print(f"Result: {result.output}")
    
    # 获取状态
    status = runtime.get_status()
    print(f"Status: {status}")
    
    runtime.stop()


def plugin_example():
    """插件示例"""
    print("\n=== 插件示例 ===")
    
    from agent_framework import Plugin, Port, PortType
    
    class MyPlugin(Plugin):
        name = "my_plugin"
        version = "1.0.0"
        description = "我的自定义插件"
        
        ports = [
            Port(
                name="my_action",
                port_type=PortType.CUSTOM,
                description="执行自定义操作",
                handler=lambda ctx, **kw: {"result": "Action executed"}
            )
        ]
    
    # 使用插件
    runtime = Runtime()
    runtime.setup()
    runtime.add_plugin(MyPlugin())
    
    result = runtime.execute("my_action")
    print(f"Plugin Result: {result}")


if __name__ == "__main__":
    basic_example()
    parser_example()
    runtime_example()
    plugin_example()
