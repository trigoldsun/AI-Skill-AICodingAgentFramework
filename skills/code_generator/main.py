#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Generator Skill - 代码生成技能

示例技能实现
"""

from agent_framework import (
    Plugin, 
    Port, 
    PortType,
    Tool,
    ToolPool,
    ToolCategory
)


class CodeGeneratorPlugin(Plugin):
    """代码生成插件"""
    
    name = "code_generator"
    version = "1.0.0"
    description = "智能代码生成技能"
    author = "AI-Skill-AICodingAgentFramework"
    
    ports = [
        Port(
            name="generate.python",
            port_type=PortType.CODE_GENERATOR,
            description="生成Python代码",
            handler=generate_python_code,
            schema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "language": {"type": "string", "default": "python"}
                }
            }
        ),
        Port(
            name="generate.javascript",
            port_type=PortType.CODE_GENERATOR,
            description="生成JavaScript代码",
            handler=generate_javascript_code
        ),
        Port(
            name="generate.template",
            port_type=PortType.CODE_GENERATOR,
            description="使用模板生成代码",
            handler=generate_from_template
        )
    ]
    
    dependencies = ["llm_client"]


def generate_python_code(context, **params) -> dict:
    """
    生成Python代码
    
    Args:
        context: 执行上下文
        **params: 参数
        
    Returns:
        dict: 生成结果
    """
    description = params.get("description", "")
    
    # 简单的模板匹配
    templates = {
        "user": '''class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
    
    def to_dict(self):
        return {"username": self.username, "email": self.email}
''',
        "api": '''from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/endpoint", methods=["GET"])
def endpoint():
    return jsonify({"status": "ok"})
''',
        "crud": '''class CRUD:
    def create(self, data):
        pass
    
    def read(self, id):
        pass
    
    def update(self, id, data):
        pass
    
    def delete(self, id):
        pass
'''
    }
    
    # 匹配模板
    code = "// 请描述您需要的代码功能"
    for key, template in templates.items():
        if key in description.lower():
            code = template
            break
    
    return {
        "success": True,
        "code": code,
        "language": "python",
        "template_used": key if key in description.lower() else None
    }


def generate_javascript_code(context, **params) -> dict:
    """生成JavaScript代码"""
    description = params.get("description", "")
    
    templates = {
        "class": '''class MyClass {
    constructor() {
        // 初始化
    }
    
    method() {
        // 方法实现
    }
}
''',
        "function": '''async function handleRequest(req, res) {
    // 处理请求
    return { status: "ok" };
}
''',
        "api": '''const express = require("express");
const app = express();

app.get("/api/endpoint", (req, res) => {
    res.json({ status: "ok" });
});

module.exports = app;
'''
    }
    
    code = "// 请描述您需要的代码功能"
    for key, template in templates.items():
        if key in description.lower():
            code = template
            break
    
    return {
        "success": True,
        "code": code,
        "language": "javascript"
    }


def generate_from_template(context, **params) -> dict:
    """使用模板生成代码"""
    template_name = params.get("template", "")
    variables = params.get("variables", {})
    
    # 模板引擎逻辑
    code = f"# Template: {template_name}\n"
    code += f"# Variables: {variables}\n"
    
    return {
        "success": True,
        "code": code,
        "template": template_name
    }


def get_tools() -> list[Tool]:
    """获取工具列表"""
    return [
        Tool(
            name="code_gen.python",
            description="生成Python代码",
            category=ToolCategory.EDITOR,
            handler=generate_python_code,
            capabilities=["generate", "python"]
        ),
        Tool(
            name="code_gen.javascript",
            description="生成JavaScript代码",
            category=ToolCategory.EDITOR,
            handler=generate_javascript_code,
            capabilities=["generate", "javascript"]
        )
    ]
