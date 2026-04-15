"""
Telemetry - Usage tracking and cost estimation

Inspired by claw-code's telemetry:
- Session trace events
- Token usage tracking
- Cost estimation per provider
- Usage statistics and reports
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(Enum):
    """Telemetry event types"""
    SESSION_START = "session.start"
    SESSION_END = "session.end"
    PROMPT = "prompt"
    COMPLETION = "completion"
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    ERROR = "error"


@dataclass
class UsageRecord:
    """Record of a single usage event"""
    query: str
    duration: float
    tools_used: List[str]
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    error: str = ""


@dataclass
class TraceEvent:
    """A trace event in a session"""
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]


class Telemetry:
    """
    Usage telemetry and cost tracking.

    Inspired by claw-code's telemetry:
    - Track token usage per model
    - Cost estimation
    - Session traces
    - Usage statistics

    Supported providers for cost estimation:
    - Anthropic
    - OpenAI
    - Azure OpenAI
    - Local models
    """

    # Cost per 1M tokens (input, output)
    COST_MATRIX = {
        # Anthropic
        "claude-opus-4-6": (15.0, 75.0),
        "claude-sonnet-4-6": (3.0, 15.0),
        "claude-haiku-4-5-20251213": (0.8, 4.0),
        # OpenAI
        "gpt-4o": (5.0, 15.0),
        "gpt-4o-mini": (0.15, 0.6),
        "gpt-4-turbo": (10.0, 30.0),
        # Anthropic-Compatible / Local
        "default": (1.0, 4.0),
    }

    def __init__(self, db_path: str = None):
        self._records: List[UsageRecord] = []
        self._traces: Dict[str, List[TraceEvent]] = {}
        self._lock = None  # Will init in thread-safe way
        self._logger = logging.getLogger("telemetry")

    def record(self, usage: UsageRecord) -> None:
        """Record a usage event"""
        if self._lock is None:
            import threading
            self._lock = threading.Lock()

        with self._lock:
            self._records.append(usage)
            self._logger.debug(
                f"Recorded usage: {usage.query[:50]}... "
                f"({usage.input_tokens} in, {usage.output_tokens} out, ${usage.cost:.4f})"
            )

    def start_trace(self, session_id: str) -> str:
        """
        Start a new trace session.

        Args:
            session_id: Session identifier

        Returns:
            Trace ID
        """
        if self._lock is None:
            import threading
            self._lock = threading.Lock()

        trace_id = str(uuid.uuid4())[:8]
        with self._lock:
            self._traces[trace_id] = []
            self.add_trace(trace_id, EventType.SESSION_START, {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
        return trace_id

    def add_trace(
        self,
        trace_id: str,
        event_type: EventType,
        data: Dict[str, Any]
    ) -> None:
        """Add event to trace"""
        with self._lock:
            if trace_id in self._traces:
                self._traces[trace_id].append(TraceEvent(
                    event_type=event_type,
                    timestamp=datetime.now().isoformat(),
                    data=data
                ))

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a completion.

        Args:
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            Estimated cost in USD
        """
        # Look up cost matrix
        input_cost, output_cost = self.COST_MATRIX.get(
            model,
            self.COST_MATRIX["default"]
        )

        return (
            (input_tokens / 1_000_000) * input_cost +
            (output_tokens / 1_000_000) * output_cost
        )

    def get_stats(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Dict with usage stats
        """
        if self._lock is None:
            import threading
            self._lock = threading.Lock()

        with self._lock:
            if not self._records:
                return {
                    "total_queries": 0,
                    "successful_queries": 0,
                    "failed_queries": 0,
                    "total_tokens_in": 0,
                    "total_tokens_out": 0,
                    "total_cost": 0.0,
                    "avg_duration": 0.0
                }

            successful = sum(1 for r in self._records if r.success)
            total_tokens_in = sum(r.input_tokens for r in self._records)
            total_tokens_out = sum(r.output_tokens for r in self._records)
            total_cost = sum(r.cost for r in self._records)
            total_duration = sum(r.duration for r in self._records)

            return {
                "total_queries": len(self._records),
                "successful_queries": successful,
                "failed_queries": len(self._records) - successful,
                "total_tokens_in": total_tokens_in,
                "total_tokens_out": total_tokens_out,
                "total_cost": total_cost,
                "avg_duration": total_duration / len(self._records),
                "success_rate": successful / len(self._records)
            }

    def get_recent(self, limit: int = 10) -> List[UsageRecord]:
        """Get recent usage records"""
        with self._lock:
            return self._records[-limit:]

    def export(self, path: str) -> None:
        """Export usage data to JSON file"""
        with self._lock:
            data = {
                "exported_at": datetime.now().isoformat(),
                "stats": self.get_stats(),
                "records": [
                    {
                        "query": r.query,
                        "duration": r.duration,
                        "tools_used": r.tools_used,
                        "success": r.success,
                        "timestamp": r.timestamp,
                        "model": r.model,
                        "input_tokens": r.input_tokens,
                        "output_tokens": r.output_tokens,
                        "cost": r.cost
                    }
                    for r in self._records
                ]
            }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def clear(self) -> None:
        """Clear all telemetry data"""
        with self._lock:
            self._records.clear()
            self._traces.clear()


class CostTracker:
    """Helper for tracking costs during a session"""

    def __init__(self, telemetry: Telemetry, model: str = "default"):
        self.telemetry = telemetry
        self.model = model
        self.start_time = time.time()
        self.input_tokens = 0
        self.output_tokens = 0

    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Add token counts"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def record_usage(
        self,
        query: str,
        tools_used: List[str],
        success: bool = True,
        error: str = ""
    ) -> UsageRecord:
        """Record final usage"""
        duration = time.time() - self.start_time
        cost = self.telemetry.estimate_cost(
            self.model,
            self.input_tokens,
            self.output_tokens
        )

        usage = UsageRecord(
            query=query,
            duration=duration,
            tools_used=tools_used,
            success=success,
            model=self.model,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cost=cost,
            error=error
        )

        self.telemetry.record(usage)
        return usage
