"""
Event Bus - Typed event system for agent coordination

Inspired by clawhip philosophy:
- Events over scraped prose
- Keep monitoring and delivery outside agent context window
- Typed events enable clawhip to route notifications correctly

Event Types:
- AGENT_STATE_CHANGED: Agent lifecycle state transitions
- TASK_CREATED/TASK_COMPLETED/TASK_FAILED: Task lifecycle
- ERROR: Recoverable and non-recoverable errors
- SESSION_STARTED/SESSION_ENDED: Session lifecycle
- TOOL_CALLED/TOOL_RESULT: Tool execution events
- NOTIFICATION: Human-facing notifications
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict
import json


class EventType(Enum):
    """
    Canonical event types for agent coordination.

    These typed events enable clawhip to:
    - Route notifications to appropriate channels (Discord, Slack, etc.)
    - Filter noisy event streams into actionable summaries
    - Trigger recovery workflows based on event patterns
    """
    # Agent lifecycle
    AGENT_STATE_CHANGED = "agent.state.changed"
    AGENT_SPAWNED = "agent.spawned"
    AGENT_READY = "agent.ready"
    AGENT_BLOCKED = "agent.blocked"
    AGENT_FINISHED = "agent.finished"
    AGENT_FAILED = "agent.failed"

    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Session lifecycle
    SESSION_STARTED = "session.started"
    SESSION_RESUMED = "session.resumed"
    SESSION_COMPACTED = "session.compacted"
    SESSION_ENDED = "session.ended"

    # Tool events
    TOOL_CALLED = "tool.called"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"

    # Permission events
    PERMISSION_REQUESTED = "permission.requested"
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_DENIED = "permission.denied"

    # Error events
    ERROR = "error"
    RECOVERY_ATTEMPTED = "recovery.attempted"
    RECOVERY_SUCCEEDED = "recovery.succeeded"
    RECOVERY_FAILED = "recovery.failed"

    # Notification events (for clawhip routing to humans)
    NOTIFICATION_INFO = "notification.info"
    NOTIFICATION_WARNING = "notification.warning"
    NOTIFICATION_ERROR = "notification.error"
    NOTIFICATION_SUCCESS = "notification.success"

    # Lane events (for CI/CD coordination)
    LANE_STARTED = "lane.started"
    LANE_RED = "lane.red"
    LANE_GREEN = "lane.green"
    LANE_COMMIT_CREATED = "lane.commit.created"
    LANE_PR_OPENED = "lane.pr.opened"
    LANE_MERGE_READY = "lane.merge.ready"
    LANE_FINISHED = "lane.finished"

    # Custom events
    CUSTOM = "custom"


@dataclass(frozen=True)
class Event:
    """
    Immutable event with typed payload.

    Events are the canonical source of truth for clawhip routing.
    Instead of scraping logs, claws consume typed events.

    Attributes:
        type: Event type enum
        source: Source agent/component ID
        data: Event payload (must be JSON-serializable)
        timestamp: Event creation time
        correlation_id: Optional ID for event tracing
    """
    type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON transport"""
        return {
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        }

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict) -> Event:
        """Deserialize from dictionary"""
        return cls(
            type=EventType(d["type"]),
            source=d["source"],
            data=d.get("data", {}),
            timestamp=d.get("timestamp", datetime.now().isoformat()),
            correlation_id=d.get("correlation_id")
        )


class EventHandler:
    """Typed event handler function"""

    def __init__(self, callback: Callable[[Event], None], event_type: EventType):
        self.callback = callback
        self.event_type = event_type

    def __repr__(self) -> str:
        return f"EventHandler({self.event_type.value}, {self.callback.__name__})"


class EventBus:
    """
    Central event bus for agent coordination.

    Inspired by clawhip's event routing:
    - Subscribe to typed events, not log patterns
    - Async event emission for non-blocking coordination
    - Event buffering for offline/delayed delivery
    - Dead letter queue for failed handlers

    Usage:
        event_bus = EventBus()

        # Subscribe to events
        event_bus.subscribe(EventType.TASK_COMPLETED, on_task_complete)

        # Emit events
        event_bus.emit(Event(type=EventType.TASK_COMPLETED, source="agent-1", data={}))

        # Clawhip integration: route to Discord
        event_bus.subscribe(EventType.NOTIFICATION_SUCCESS, route_to_discord)
    """

    def __init__(self, buffer_size: int = 1000):
        """
        Initialize event bus.

        Args:
            buffer_size: Maximum events to buffer for slow subscribers
        """
        self._subscribers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self._event_buffer: List[Event] = []
        self._buffer_size = buffer_size
        self._dead_letter_queue: List[Event] = []

        self._logger = logging.getLogger("event_bus")
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ) -> EventHandler:
        """
        Subscribe to a specific event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function

        Returns:
            EventHandler instance for unsubscribing
        """
        event_handler = EventHandler(handler, event_type)
        self._subscribers[event_type].append(event_handler)
        self._logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")
        return event_handler

    def subscribe_all(self, handler: Callable[[Event], None]) -> EventHandler:
        """
        Subscribe to all event types (global handler).

        Args:
            handler: Callback function for all events

        Returns:
            EventHandler instance
        """
        event_handler = EventHandler(handler, EventType.CUSTOM)
        self._global_handlers.append(event_handler)
        return event_handler

    def unsubscribe(self, handler: EventHandler) -> None:
        """Unsubscribe a handler"""
        if handler.event_type == EventType.CUSTOM:
            self._global_handlers = [
                h for h in self._global_handlers if h != handler
            ]
        else:
            self._subscribers[handler.event_type] = [
                h for h in self._subscribers[handler.event_type] if h != handler
            ]

    def emit(self, event: Event) -> None:
        """
        Emit an event synchronously.

        For async emission, use emit_async().
        """
        self._event_buffer.append(event)

        # Trim buffer if needed
        if len(self._event_buffer) > self._buffer_size:
            self._event_buffer = self._event_buffer[-self._buffer_size:]

        # Call handlers
        self._dispatch_event(event)

    async def emit_async(self, event: Event) -> None:
        """Emit an event asynchronously"""
        async with self._lock:
            self.emit(event)

    def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to all registered handlers"""
        # Type-specific handlers
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            try:
                handler.callback(event)
            except Exception as e:
                self._logger.error(
                    f"Handler {handler.callback.__name__} failed for {event.type.value}: {e}"
                )
                self._dead_letter_queue.append(event)

        # Global handlers
        for handler in self._global_handlers:
            try:
                handler.callback(event)
            except Exception as e:
                self._logger.error(
                    f"Global handler {handler.callback.__name__} failed: {e}"
                )

    def get_buffer(self, limit: int = 100) -> List[Event]:
        """Get recent events from buffer"""
        return self._event_buffer[-limit:]

    def get_events_by_type(
        self,
        event_type: EventType,
        limit: int = 50
    ) -> List[Event]:
        """Get recent events of a specific type"""
        return [
            e for e in self._event_buffer[-limit:]
            if e.type == event_type
        ]

    def get_dead_letter_queue(self) -> List[Event]:
        """Get events that failed processing"""
        return self._dead_letter_queue.copy()

    def clear_dead_letter_queue(self) -> None:
        """Clear dead letter queue"""
        self._dead_letter_queue.clear()

    def replay_events(
        self,
        events: List[Event],
        handler: Callable[[Event], None]
    ) -> None:
        """
        Replay events through a handler.

        Useful for testing or reprocessing failed events.
        """
        for event in events:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Replay handler failed: {e}")


class EventSummary:
    """
    Compressed event summary for human notification.

    Instead of flooding Discord with raw events,
    claws consume events and produce summaries.
    """

    def __init__(self):
        self.events: List[Event] = []
        self.start_time = time.time()

    def add(self, event: Event) -> None:
        """Add event to summary"""
        self.events.append(event)

    def compress(self) -> dict:
        """
        Compress events into actionable summary.

        Returns:
            Summary with:
            - current_phase: What phase are we in
            - last_checkpoint: Last successful step
            - blocker: Current blocker if any
            - recommended_action: What to do next
        """
        if not self.events:
            return {
                "phase": "idle",
                "checkpoint": None,
                "blocker": None,
                "action": None
            }

        # Find last successful event
        successful = [
            e for e in self.events
            if e.type in (EventType.TASK_COMPLETED, EventType.AGENT_FINISHED)
        ]

        # Find last error
        errors = [
            e for e in self.events
            if e.type == EventType.ERROR
        ]

        # Determine phase
        last_event = self.events[-1]
        phase_map = {
            EventType.AGENT_SPAWNED: "initializing",
            EventType.AGENT_READY: "ready",
            EventType.TASK_CREATED: "planning",
            EventType.TASK_STARTED: "executing",
            EventType.TASK_COMPLETED: "completing",
            EventType.ERROR: "error",
        }
        phase = phase_map.get(last_event.type, "unknown")

        return {
            "phase": phase,
            "checkpoint": successful[-1].data if successful else None,
            "blocker": errors[-1].data if errors else None,
            "action": self._recommend_action(phase, errors)
        }

    def _recommend_action(self, phase: str, errors: list) -> Optional[str]:
        """Generate recommended action based on phase and errors"""
        if errors:
            return "Review error and retry"

        action_map = {
            "initializing": "Waiting for agent ready",
            "planning": "Agent is planning execution",
            "executing": "Agent is executing tasks",
            "completing": "Finalizing results",
            "error": "Escalate to human",
            "ready": "Send next directive",
        }
        return action_map.get(phase)


# Convenience function for creating events
def create_event(
    event_type: EventType,
    source: str,
    data: Dict[str, Any] = None,
    correlation_id: str = None
) -> Event:
    """Create a new event with common defaults"""
    return Event(
        type=event_type,
        source=source,
        data=data or {},
        correlation_id=correlation_id
    )
