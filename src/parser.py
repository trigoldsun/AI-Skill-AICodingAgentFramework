#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser - 自然语言解析器

将用户输入解析为结构化的意图和实体
灵感来源: claw-code/src/query_engine.py
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import re


class IntentType(Enum):
    """意图类型"""
    CREATE = "create"           # 创建文件/项目
    READ = "read"              # 读取文件
    UPDATE = "update"           # 更新文件
    DELETE = "delete"          # 删除文件
    SEARCH = "search"           # 搜索
    REFACTOR = "refactor"       # 重构
    TEST = "test"              # 测试
    DEPLOY = "deploy"          # 部署
    QUERY = "query"            # 查询信息
    HELP = "help"              # 帮助
    UNKNOWN = "unknown"        # 未知


@dataclass
class Entity:
    """实体"""
    name: str
    type: str  # file, project, function, class, variable, etc.
    path: Optional[str] = None
    attributes: dict = field(default_factory=dict)


@dataclass
class Intent:
    """用户意图"""
    type: IntentType
    original_text: str
    entities: list[Entity] = field(default_factory=list)
    modifiers: dict = field(default_factory=dict)
    confidence: float = 1.0


class Parser:
    """
    自然语言解析器
    
    将自然语言转换为结构化意图
    """
    
    # 意图关键词映射
    INTENT_PATTERNS = {
        IntentType.CREATE: [
            r"创建", r"新建", r"添加", r"生成", r"make", r"create", r"new", r"add", r"generate"
        ],
        IntentType.READ: [
            r"读取", r"查看", r"打开", r"显示", r"read", r"view", r"show", r"open", r"display"
        ],
        IntentType.UPDATE: [
            r"更新", r"修改", r"编辑", r"改变", r"update", r"modify", r"edit", r"change"
        ],
        IntentType.DELETE: [
            r"删除", r"移除", r"清理", r"delete", r"remove", r"clean"
        ],
        IntentType.SEARCH: [
            r"搜索", r"查找", r"查询", r"搜索", r"search", r"find", r"lookup", r"grep"
        ],
        IntentType.REFACTOR: [
            r"重构", r"优化", r"改进", r"refactor", r"optimize", r"improve"
        ],
        IntentType.TEST: [
            r"测试", r"测试", r"单元测试", r"test", r"unit test"
        ],
        IntentType.DEPLOY: [
            r"部署", r"发布", r"上线", r"deploy", r"release", r"publish"
        ],
        IntentType.HELP: [
            r"帮助", r"使用", r"说明", r"help", r"usage", r"how to"
        ]
    }
    
    # 实体类型模式
    ENTITY_PATTERNS = {
        "file": [
            r"(?P<name>\w+\.(?:py|js|ts|rs|go|java|cpp|c|md|json|yaml|yml|toml))",
        ],
        "function": [
            r"函数\s*(?P<name>\w+)",
            r"方法\s*(?P<name>\w+)",
            r"def\s+(?P<name>\w+)",
            r"func\s+(?P<name>\w+)",
            r"function\s+(?P<name>\w+)",
        ],
        "class": [
            r"类\s*(?P<name>\w+)",
            r"class\s+(?P<name>\w+)",
        ],
        "project": [
            r"项目\s*(?P<name>\w+)",
            r"应用\s*(?P<name>\w+)",
            r"app\s+(?P<name>\w+)",
        ]
    }
    
    def __init__(self):
        self.intent_cache = {}
    
    def parse(self, text: str) -> Intent:
        """
        解析用户输入
        
        Args:
            text: 用户输入的自然语言
            
        Returns:
            Intent: 结构化的意图对象
        """
        text = text.strip()
        
        # 检测意图类型
        intent_type = self._detect_intent(text)
        
        # 提取实体
        entities = self._extract_entities(text)
        
        # 提取修饰符
        modifiers = self._extract_modifiers(text)
        
        return Intent(
            type=intent_type,
            original_text=text,
            entities=entities,
            modifiers=modifiers,
            confidence=0.9
        )
    
    def _detect_intent(self, text: str) -> IntentType:
        """检测意图类型"""
        text_lower = text.lower()
        
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent_type
        
        return IntentType.UNKNOWN
    
    def _extract_entities(self, text: str) -> list[Entity]:
        """提取实体"""
        entities = []
        
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if match.groupdict():
                        entities.append(Entity(
                            name=match.group("name"),
                            type=entity_type,
                            attributes=dict(match.groupdict())
                        ))
        
        return entities
    
    def _extract_modifiers(self, text: str) -> dict:
        """提取修饰符"""
        modifiers = {}
        
        # 优先级
        priority_keywords = {
            r"紧急": "urgent",
            r"重要": "important", 
            r"普通": "normal",
            r"低优先级": "low"
        }
        
        for keyword, priority in priority_keywords.items():
            if keyword in text:
                modifiers["priority"] = priority
        
        # 强制执行
        if any(kw in text for kw in ["强制", "force", "forced"]):
            modifiers["force"] = True
        
        # 递归
        if any(kw in text for kw in ["递归", "recursive", "all"]):
            modifiers["recursive"] = True
        
        return modifiers
    
    def batch_parse(self, texts: list[str]) -> list[Intent]:
        """批量解析"""
        return [self.parse(text) for text in texts]


class SimpleParser:
    """
    简单解析器 - 轻量级实现
    
    不依赖LLM，基于规则解析
    """
    
    def __init__(self):
        self.parser = Parser()
    
    def parse_command(self, command: str) -> dict:
        """
        解析命令为结构化字典
        
        Examples:
            "创建用户认证API" 
            -> {"action": "create", "target": "api", "subject": "用户认证"}
        """
        intent = self.parser.parse(command)
        
        return {
            "action": intent.type.value,
            "entities": [
                {"name": e.name, "type": e.type} 
                for e in intent.entities
            ],
            "modifiers": intent.modifiers,
            "confidence": intent.confidence
        }
