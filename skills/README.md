# AI Coding Agent Framework - 技能开发指南

## 概述

本框架采用插件化架构，每个功能模块都是可插拔的技能（Skill）。

## 技能结构

```
skill_name/
├── SKILL.md          # 技能描述文件
├── main.py           # 技能入口
├── config.py         # 技能配置
└── handlers/         # 处理器
    ├── __init__.py
    ├── code_gen.py
    └── ...
```

## 创建技能

```python
# skill_example/main.py
from agent_framework import Plugin, Port, PortType

class CodeGeneratorPlugin(Plugin):
    name = "code_generator"
    version = "1.0.0"
    description = "代码生成技能"
    
    ports = [
        Port(
            name="generate",
            port_type=PortType.CODE_GENERATOR,
            description="生成代码",
            handler=generate_code
        )
    ]

def generate_code(context, **params):
    # 实现代码生成逻辑
    return {"code": "// generated code"}
```

## 注册技能

```python
from agent_framework import Runtime

runtime = Runtime()
runtime.add_plugin(CodeGeneratorPlugin())
```

## 技能列表

| 技能 | 说明 |
|------|------|
| code_generator | 代码生成 |
| file_operator | 文件操作 |
| git_manager | Git管理 |
| test_runner | 测试运行 |
| deployer | 应用部署 |
