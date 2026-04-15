"""
providers.anthropic - Anthropic Claude Provider
"""
from __future__ import annotations
import json
from typing import Any, AsyncIterator, Optional
from .base import BaseLLMProvider, Provider, Message, LLMResponse, ToolCall


class AnthropicProvider(BaseLLMProvider):
    provider = Provider.ANTHROPIC
    
    MAX_OUTPUTS = {
        "claude-opus-4-6": 32_000,
        "claude-sonnet-4-6": 64_000,
        "claude-haiku-4-5-20251213": 64_000,
    }
    
    def _get_default_key(self) -> str:
        return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    
    def _get_default_base_url(self) -> str:
        return os.environ.get("ANTHROPIC_BASE_URL", "") or "https://api.anthropic.com"
    
    def _get_header(self) -> dict:
        if self.api_key.startswith("sk-ant-"):
            return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        else:
            return {"authorization": f"Bearer {self.api_key}", "anthropic-version": "2023-06-01", "content-type": "application/json"}
    
    async def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> LLMResponse:
        import aiohttp
        url = f"{self.base_url}/v1/messages"
        headers = self._get_header()
        
        anthropic_messages = []
        for msg in messages:
            if msg.role == "system":
                continue
            anthropic_messages.append({"role": msg.role, "content": msg.content})
        
        body: dict[str, Any] = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": min(max_tokens, self.MAX_OUTPUTS.get(self.model, 4096)),
            "temperature": temperature,
        }
        
        system_msgs = [m.content for m in messages if m.role == "system"]
        if system_msgs:
            body["system"] = "\n\n".join(system_msgs)
        
        if tools:
            body["tools"] = tools
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"Anthropic API error {resp.status}: {error_text}")
                
                data = await resp.json()
                
                content = ""
                tool_calls = []
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls.append(ToolCall(
                            name=block.get("name", ""),
                            input_json=json.dumps(block.get("input", {}))
                        ))
                
                return LLMResponse(
                    content=content,
                    tool_calls=tool_calls,
                    model=data.get("model", self.model),
                    input_tokens=data.get("usage", {}).get("input_tokens", 0),
                    output_tokens=data.get("usage", {}).get("output_tokens", 0),
                    stop_reason=data.get("stop_reason", ""),
                )
    
    async def chat_stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        import aiohttp
        url = f"{self.base_url}/v1/messages"
        headers = self._get_header()
        headers["anthropic-dangerous-direct-browser-access"] = "true"
        
        anthropic_messages = [msg for msg in messages if msg.role != "system"]
        body: dict[str, Any] = {"model": self.model, "messages": anthropic_messages, "max_tokens": 1024, "stream": True}
        
        system_msgs = [m.content for m in messages if m.role == "system"]
        if system_msgs:
            body["system"] = "\n\n".join(system_msgs)
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
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except json.JSONDecodeError:
                            continue
