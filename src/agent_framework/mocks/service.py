"""
mocks.service - 确定性 Mock 服务
Inspired by claw-code's mock_parity_harness
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional


class MockScenario(Enum):
    HELLO = "hello"
    TOOL_CALL = "tool_call"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    ERROR = "error"


@dataclass
class MockRequest:
    messages: list
    model: str = ""
    tools: Optional[list] = None
    max_tokens: int = 4096


@dataclass
class MockResponse:
    content: str
    tool_calls: list = field(default_factory=list)
    model: str = "claude-sonnet-4-6"
    input_tokens: int = 100
    output_tokens: int = 50
    stop_reason: str = ""


class MockAnthropicService:
    """确定性 Mock Anthropic API 服务"""
    
    def __init__(self):
        self.requests: list = []
        self.scenario = MockScenario.HELLO
    
    def set_scenario(self, scenario: MockScenario) -> None:
        self.scenario = scenario
    
    def chat(self, request: MockRequest) -> MockResponse:
        self.requests.append(request)
        
        if self.scenario == MockScenario.HELLO:
            return MockResponse(content="Hello from mock!")
        elif self.scenario == MockScenario.TOOL_CALL:
            user_message = ""
            for msg in reversed(request.messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            tool = "bash"
            args = {"command": "echo 'test'"}
            if "read" in user_message.lower() or "file" in user_message.lower():
                tool = "read"
                args = {"path": "example.txt"}
            elif "search" in user_message.lower():
                tool = "grep"
                args = {"pattern": "test", "path": "."}
            
            return MockResponse(
                content=f"I'll use {tool} tool.",
                tool_calls=[{"id": "toolu_001", "type": "tool_use", "name": tool, "input": args}],
                stop_reason="tool_use",
            )
        elif self.scenario == MockScenario.ERROR:
            raise RuntimeError("Mock error: This is a test error")
        else:
            return MockResponse(content="Hello from mock!")
    
    async def chat_async(self, request: MockRequest) -> MockResponse:
        return self.chat(request)
    
    def stream(self, request: MockRequest) -> AsyncIterator[str]:
        self.requests.append(request)
        response = self.chat(request)
        
        for char in response.content:
            yield f'data: {json.dumps({"type": "content_block_delta", "delta": {"type": "text_delta", "text": char}})}\n\n'
        yield "data: [DONE]\n\n"
    
    def reset(self) -> None:
        self.requests.clear()
    
    def get_stats(self) -> dict:
        return {"total_requests": len(self.requests), "scenario": self.scenario.value}
