# AI Coding Agent Framework

> 基于claw-code架构的智能软件开发框架

## 核心理念

```
用户意图 → 智能解析 → 任务规划 → 工具执行 → 结果验证
```

## 架构设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI Coding Agent Framework                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   User CLI   │───▶│   Router     │───▶│   Engine     │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│         │                   │                   │                    │
│         ▼                   ▼                   ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   Parser     │    │   Query     │    │   Tool       │        │
│  │   (意图理解)  │    │   Engine    │    │   Pool       │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│                              │                   │                    │
│                              ▼                   ▼                    │
│                      ┌──────────────┐    ┌──────────────┐        │
│                      │   Task       │    │   Plugin     │        │
│                      │   Manager    │    │   Registry   │        │
│                      └──────────────┘    └──────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 核心模块

| 模块 | 说明 | 灵感来源 |
|------|------|----------|
| `Parser` | 自然语言解析 | claw-code query_engine |
| `QueryEngine` | 意图理解和路由 | claw-code query_engine |
| `ToolPool` | 动态工具管理 | claw-code tool_pool |
| `PluginRegistry` | 插件注册发现 | claw-code port_manifest |
| `TaskManager` | 任务规划和执行 | claw-code task |
| `Runtime` | 运行时编排 | claw-code runtime |
| `ExecutionRegistry` | 命令执行路由 | claw-code execution_registry |

## 快速开始

```python
from agent_framework import Agent

agent = Agent(
    name="dev-assistant",
    model="claude-3-5-sonnet",
    plugins=["code_generator", "file_operator", "git_manager"]
)

# 自然语言驱动
result = agent.execute("创建一个用户认证的REST API")
```

## 设计原则

1. **自然语言优先** - 用户描述需求，框架自动规划执行
2. **插件化架构** - 能力通过插件动态扩展
3. **工具池化** - 统一管理，智能选择
4. **任务流编排** - 支持复杂多步骤任务
5. **安全执行** - 沙箱隔离，权限控制

## License

MIT
