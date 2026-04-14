# Architecture

## Overview

AI Coding Agent Framework follows an event-driven, layered architecture inspired by claw-code's design principles.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Human Interface Layer                          │
│   (CLI / Discord / Natural Language / API)                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Coordination Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  Event Bus  │  │   Slash    │  │   Query    │                  │
│  │  (clawhip)  │  │  Commands  │  │   Engine   │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Execution Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   Agent     │  │    Task    │  │  Permission │                  │
│  │   Runtime   │  │   Manager   │  │   Enforcer  │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Persistence Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   Session   │  │  Telemetry  │  │   Skills   │                  │
│  │   Manager   │  │             │  │   Registry  │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### Event Bus

The central nervous system of the framework. All components communicate through typed events.

```python
event_bus = EventBus()

# Subscribe to events
event_bus.subscribe(EventType.TASK_COMPLETED, on_task_complete)

# Emit events
event_bus.emit(Event(type=EventType.TASK_CREATED, source="agent-1", data={}))
```

Key features:
- Typed events over log scraping
- Async event emission
- Dead letter queue for failed handlers
- Event buffering for offline delivery

### Agent Runtime

The core orchestration engine with state machine lifecycle.

```
SPAWNING -> TRUST_REQUIRED -> READY_FOR_PROMPT -> PROMPT_ACCEPTED
                                                        │
                                                        ▼
                                                    RUNNING
                                                        │
                                              ┌─────────┴─────────┐
                                              ▼                   ▼
                                          BLOCKED             FINISHED
                                              │                   │
                                              └───────> FAILED <──┘
```

Features:
- Explicit state transitions
- Event emission on state changes
- Recovery before escalation
- Permission enforcement

### Task Manager

In-memory task registry with lifecycle tracking.

```python
task = task_manager.create_task(
    description="Create REST API",
    priority=TaskPriority.HIGH
)

task_manager.start_task(task.id)
# ... execute ...
task_manager.complete_task(task.id, result=api_code)
```

Features:
- Thread-safe operations
- Status callbacks
- Pipeline support
- Progress tracking

### Session Manager

Session persistence with JSONL + SQLite.

```python
session = session_manager.create_session(
    model="claude-sonnet-4",
    permission_mode="workspace-write"
)

session.add_message("user", "Create a REST API")
session_manager.update_session(session)

# Resume later
session_manager.resume_session(session.id)
```

Features:
- JSONL for audit trail
- SQLite for efficient queries
- Automatic compaction
- Cross-session resume

### Permission Enforcer

Deny-by-default permission system.

```python
enforcer = PermissionEnforcer()

result = enforcer.check_file_write("/project/file.py", mode=WORKSPACE_WRITE)
# Allowed if in workspace boundary

result = enforcer.check_bash("rm -rf /", mode=READ_ONLY)
# Denied: dangerous command
```

Modes:
- `READ_ONLY`: File reads only
- `WORKSPACE_WRITE`: Write within project
- `DANGER_FULL_ACCESS`: Full filesystem + shell

### Telemetry

Usage tracking and cost estimation.

```python
telemetry = Telemetry()

telemetry.record(UsageRecord(
    query="Create REST API",
    duration=5.2,
    tools_used=["editor", "linter", "tester"],
    success=True,
    input_tokens=500,
    output_tokens=2000
))

stats = telemetry.get_stats()
# {"total_queries": 10, "total_cost": 0.45, ...}
```

Features:
- Per-model cost estimation
- Token tracking
- Usage statistics
- Export to JSON

## Design Principles

### 1. State Machine First

Every agent has explicit lifecycle states. No implicit or hidden states.

```python
class AgentState(Enum):
    SPAWNING = "spawning"
    READY_FOR_PROMPT = "ready_for_prompt"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
```

### 2. Events Over Logs

Typed events enable clawhip to route notifications correctly.

```python
# Instead of scraping logs:
# if "error" in log_line:
#     send_alert()

# Use typed events:
event_bus.emit(Event(type=EventType.ERROR, source="agent-1", data={"error": "..."}))
```

### 3. Recovery Before Escalation

Auto-heal known failures once before asking for help.

```python
failure_handlers = {
    "trust_prompt": auto_accept_trust,
    "compile_error": run_fix_compile,
    "test_failure": run_fix_tests,
}
```

### 4. Deny by Default

Permission system denies operations unless explicitly allowed.

```python
# All operations denied by default
# Explicit permission required for each operation type
```

### 5. Composability

Skills and tools are composable building blocks.

```python
skill = Skill(
    name="code_review",
    description="Automated code review",
    tools=["reader", "analyzer", "commenter"],
    steps=["analyze_code", "check_style", "report_issues"]
)
```
