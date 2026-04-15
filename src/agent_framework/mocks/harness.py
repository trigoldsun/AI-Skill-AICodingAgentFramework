"""
mocks.harness - Parity 测试框架
Inspired by claw-code's mock_parity_harness
"""
import json
from dataclasses import dataclass


@dataclass
class HarnessResult:
    name: str
    passed: bool
    message: str
    details: str = ""


class ParityHarness:
    """端到端测试框架"""
    
    def __init__(self):
        self.results = []
    
    def record(self, name: str, passed: bool, message: str, details: str = "") -> None:
        self.results.append(HarnessResult(name=name, passed=passed, message=message, details=details))
    
    async def test_streaming_text(self) -> HarnessResult:
        from .service import MockAnthropicService, MockScenario, MockRequest
        mock = MockAnthropicService()
        mock.set_scenario(MockScenario.HELLO)
        
        request = MockRequest(messages=[{"role": "user", "content": "Say hello"}])
        
        try:
            chunks = []
            for chunk in mock.stream(request):
                if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                    data = json.loads(chunk[6:])
                    if data.get("type") == "content_block_delta":
                        chunks.append(data["delta"]["text"])
            
            full_text = "".join(chunks)
            
            if full_text:
                return HarnessResult(name="streaming_text", passed=True, message=f"Streaming works ({len(chunks)} chunks)", details=full_text[:80])
            return HarnessResult(name="streaming_text", passed=False, message="No streaming output")
        except Exception as e:
            return HarnessResult(name="streaming_text", passed=False, message="Streaming failed", details=str(e))
    
    async def test_tool_call_roundtrip(self) -> HarnessResult:
        from .service import MockAnthropicService, MockScenario, MockRequest
        mock = MockAnthropicService()
        mock.set_scenario(MockScenario.TOOL_CALL)
        
        request = MockRequest(messages=[{"role": "user", "content": "Read the file"}])
        
        try:
            response = await mock.chat_async(request)
            if response.tool_calls:
                return HarnessResult(
                    name="tool_call_roundtrip", passed=True,
                    message=f"Tool call generated: {response.tool_calls[0].get('name')}",
                    details=str(response.tool_calls[0])
                )
            return HarnessResult(name="tool_call_roundtrip", passed=False, message="No tool call in response")
        except Exception as e:
            return HarnessResult(name="tool_call_roundtrip", passed=False, message="Tool call failed", details=str(e))
    
    async def test_error_recovery(self) -> HarnessResult:
        from .service import MockAnthropicService, MockScenario, MockRequest
        mock = MockAnthropicService()
        mock.set_scenario(MockScenario.ERROR)
        
        request = MockRequest(messages=[{"role": "user", "content": "Test error"}])
        
        try:
            await mock.chat_async(request)
            return HarnessResult(name="error_recovery", passed=False, message="Error not raised")
        except RuntimeError as e:
            return HarnessResult(name="error_recovery", passed=True, message="Error handled correctly", details=str(e))
        except Exception as e:
            return HarnessResult(name="error_recovery", passed=False, message="Unexpected error type", details=str(e))
    
    async def run_all(self) -> list:
        self.results.clear()
        for test in [self.test_streaming_text, self.test_tool_call_roundtrip, self.test_error_recovery]:
            result = await test()
            self.record(result.name, result.passed, result.message, result.details)
        return self.results
    
    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        
        lines = ["=" * 50, "🦞 Parity Harness Results", "=" * 50, ""]
        for r in self.results:
            status = "✅" if r.passed else "❌"
            lines.append(f"{status} {r.name}: {r.message}")
            if r.details:
                lines.append(f"   → {r.details}")
        lines.append("")
        lines.append(f"Summary: {passed}/{total} passed")
        if passed == total:
            lines.append("🎉 All tests passed!")
        lines.append("=" * 50)
        return "\n".join(lines)


async def run_parity_harness() -> int:
    harness = ParityHarness()
    await harness.run_all()
    print(harness.summary())
    return 0 if sum(1 for r in harness.results if not r.passed) == 0 else 1
