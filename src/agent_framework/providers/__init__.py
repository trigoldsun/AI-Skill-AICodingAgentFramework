"""
providers - LLM Provider 抽象层
Inspired by claw-code's provider auto-routing
支持 Anthropic/OpenAI/xAI/DashScope，自动检测模型并路由
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .base import BaseLLMProvider

MODEL_ALIASES = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251213",
    "grok": "grok-3",
    "grok-mini": "grok-3-mini",
    "grok-2": "grok-2",
}


def create_provider(
    model: str = "sonnet",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> "BaseLLMProvider":
    """
    创建合适的 LLM Provider，自动检测模型类型并路由
    需要先安装: pip install aiohttp
    """
    resolved_model = MODEL_ALIASES.get(model, model)

    if resolved_model.startswith("claude"):
        from .anthropic import AnthropicProvider
        return AnthropicProvider(resolved_model, api_key, base_url)
    elif resolved_model.startswith("grok"):
        from .openai_compat import OpenAICompatibleProvider
        return OpenAICompatibleProvider(
            resolved_model,
            api_key or os.environ.get("XAI_API_KEY", ""),
            base_url or os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
        )
    elif resolved_model.startswith(("qwen/", "qwq-")):
        from .openai_compat import OpenAICompatibleProvider
        return OpenAICompatibleProvider(
            resolved_model,
            api_key or os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    elif resolved_model.startswith(("gpt-", "openai/")):
        from .openai_compat import OpenAICompatibleProvider
        return OpenAICompatibleProvider(
            resolved_model,
            api_key or os.environ.get("OPENAI_API_KEY", ""),
            base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
    else:
        from .anthropic import AnthropicProvider
        return AnthropicProvider(resolved_model, api_key, base_url)


def get_available_providers() -> list:
    providers = []
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        providers.append("anthropic")
    if os.environ.get("OPENAI_API_KEY"):
        providers.append("openai")
    if os.environ.get("XAI_API_KEY"):
        providers.append("xai")
    if os.environ.get("DASHSCOPE_API_KEY"):
        providers.append("dashscope")
    return providers
