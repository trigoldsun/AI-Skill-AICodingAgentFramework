# Code Generator Skill

代码生成技能

## 功能

- 根据自然语言描述生成代码
- 支持多种编程语言
- 代码模板系统
- LLM增强生成

## 使用

```python
from agent_framework import Runtime

runtime = Runtime()
runtime.add_plugin(CodeGeneratorPlugin())

result = runtime.execute("创建一个用户认证的REST API")
```

## 配置

```json
{
  "code_generator": {
    "default_language": "python",
    "template_dir": "./templates"
  }
}
```
