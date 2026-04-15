"""
tools.base - Tool 基类定义
Inspired by claw-code's tool system
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolCategory(Enum):
    FILE = "file"
    EXECUTION = "execution"
    SEARCH = "search"
    WEB = "web"
    GIT = "git"
    AGENT = "agent"


@dataclass
class ToolResult:
    success: bool
    output: Any = ""
    error: str = ""
    tool_name: str = ""
    duration: float = 0.0
    metadata: dict = field(default_factory=dict)


class Tool(ABC):
    name: str = ""
    description: str = ""
    category: ToolCategory = ToolCategory.FILE
    parameters: list = []
    
    def __init__(self):
        self._validate_def()
    
    def _validate_def(self):
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define name")
    
    def get_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self._get_properties(),
                    "required": self._get_required(),
                }
            }
        }
    
    def _get_properties(self) -> dict:
        props = {}
        for param in self.parameters:
            props[param["name"]] = {"description": param.get("description", ""), "type": param.get("type", "string")}
        return props
    
    def _get_required(self) -> list:
        return [p["name"] for p in self.parameters if p.get("required", False)]
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...
    
    def to_claw_code_dict(self) -> dict:
        return {"name": self.name, "description": self.description, "category": self.category.value}
