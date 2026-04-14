#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models - 数据模型

核心数据模型定义
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class Session:
    """会话"""
    id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    messages: list[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class Project:
    """项目"""
    name: str
    path: str
    language: str = ""
    framework: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class CodeFile:
    """代码文件"""
    path: str
    language: str
    content: str = ""
    modified_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class CodeSnippet:
    """代码片段"""
    code: str
    language: str
    start_line: int = 0
    end_line: int = 0
    file_path: str = ""


@dataclass
class AnalysisResult:
    """分析结果"""
    file_path: str
    language: str
    functions: list[dict] = field(default_factory=list)
    classes: list[dict] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    complexity: int = 0
    metrics: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    code: str = ""
    language: str = ""
    file_path: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    duration: float = 0.0
    stdout: str = ""
    stderr: str = ""


@dataclass
class TestResult:
    """测试结果"""
    success: bool
    test_count: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    details: list[dict] = field(default_factory=list)


@dataclass
class DeploymentResult:
    """部署结果"""
    success: bool
    environment: str = ""
    url: str = ""
    version: str = ""
    duration: float = 0.0
    logs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
