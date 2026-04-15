"""
providers.openai_compat - OpenAI Compatible Provider
支持 OpenAI、OpenRouter、Ollama、DashScope
"""
from __future__ import annotations
import os
import json
from typing import Any, AsyncIterator, Optional
from .base import BaseLLMProvider, Provider, Message, LLMResponse, ToolCall


class OpenAICompatibleProvider(BaseLLMProvider):
    provider = Provider.OPENAI
    
    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        actual_model = model
        for prefix in ["openai/", "gpt-"]:
            if model.startswith(prefix):
                actual_model = model[len(prefix):]
                break
        super().__init__(actual_model, api_key, base_url)
        self.original_model = model
    
    def _get_default_key(self) -> str:
        return os.environ.get("OPENAI_API_KEY", "")
    
    def _get_default_base_url(self) -> str:
        return os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    async def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> LLMResponse:
        import aiohttp
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        chat_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        body: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"OpenAI API error {resp.status}: {error_text}")
                
                data = await resp.json()
                choice = data["choices"][0]
                message = choice.get("message", {})
                
                tool_calls = []
                for tc in message.get("tool_calls", []):
                    func = tc.get("function", {})
                    tool_calls.append(ToolCall(name=func.get("name", ""), input_json=func.get("arguments", "{}")))
                
                usage = data.get("usage", {})
                return LLMResponse(
                    content=message.get("content", ""),
                    tool_calls=tool_calls,
                    model=data.get("model", self.model),
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    stop_reason=choice.get("finish_reason", ""),
                )
    
    async def chat_stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        import aiohttp
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        chat_messages = [{"role": m.role, "content": m.content} for m in messages]
        body: dict[str, Any] = {"model": self.model, "messages": chat_messages, "max_tokens": 1024, "stream": True, "temperature": 1.0}
        
        if tools:
            body["tools"] = tools
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as resp:
                async for line in resp.content:
                    line = line.decode().strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
