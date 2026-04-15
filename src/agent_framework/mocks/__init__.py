"""
mocks - Mock 测试框架
Inspired by claw-code's deterministic mock service
"""
from .harness import ParityHarness, HarnessResult, run_parity_harness
from .service import MockAnthropicService, MockScenario, MockRequest
__all__ = ["ParityHarness", "HarnessResult", "run_parity_harness", "MockAnthropicService", "MockScenario", "MockRequest"]
