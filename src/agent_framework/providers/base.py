"""
providers.base - LLM Provider 基类定义
Inspired by claw-code's provider abstraction
"""
from __future__ import annotations
import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional


class Provider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    XAI = "xai"
    DASHSCOPE = "dashscope"


@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str
    name: Optional[str] = None


@dataclass
class ToolCall:
    name: str
    input_json: str  # JSON string of arguments


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""


class BaseLLMProvider(ABC):
    """LLM Provider 基类"""
    
    provider: Provider = Provider.ANTHROPIC
    
    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key or self._get_default_key()
        self.base_url = base_url or self._get_default_base_url()
    
    @abstractmethod
    def _get_default_key(self) -> str:
        ...
    
    @abstractmethod
    def _get_default_base_url(self) -> str:
        ...
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> LLMResponse:
        ...
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        ...
