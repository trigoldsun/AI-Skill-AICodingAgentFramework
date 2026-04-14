# Design Decisions

## Rationale for Key Design Choices

### 1. Why Event-Driven Architecture?

**Decision**: Use typed events as the primary coordination mechanism.

**Alternatives Considered**:
- Direct function calls: Tight coupling, hard to extend
- Message queues: Over-engineered for single-process
- Log scraping: Fragile, error-prone

**Decision**: Typed events provide:
- Loose coupling between components
- Easy extension without modifying existing code
- Natural integration with clawhip for notification routing
- Debuggable: events are explicit and traceable

### 2. Why State Machine for Agent Lifecycle?

**Decision**: Explicit states for agent lifecycle.

**Alternatives Considered**:
- Implicit states via flags: Hidden complexity, hard to debug
- No states: Cannot track agent progress

**Decision**: State machine provides:
- Clear visibility into agent status
- Eventual consistency for distributed systems
- Explicit transitions prevent invalid states
- Natural integration with UI/status displays

### 3. Why Session Persistence with JSONL + SQLite?

**Decision**: Hybrid storage for sessions.

**Alternatives Considered**:
- Pure JSONL: Simple but slow for large session counts
- Pure SQLite: Fast queries but complex JSON handling
- Database-only: No audit trail

**Decision**: Hybrid provides:
- JSONL: Complete audit trail, easy to parse
- SQLite: Fast session listing and queries
- Best of both worlds

### 4. Why Deny-by-Default Permission Model?

**Decision**: Permissions denied unless explicitly allowed.

**Alternatives Considered**:
- Allow-by-default: Security risk
- Prompt for each operation: User fatigue

**Decision**: Deny-by-default with modes:
- `READ_ONLY`: Safe for untrusted code
- `WORKSPACE_WRITE`: Balance of safety and capability
- `DANGER_FULL_ACCESS`: Explicit opt-in for dangerous operations

### 5. Why Thread-Safe Task Registry?

**Decision**: Use locks for thread safety.

**Alternatives Considered**:
- Async-only: Limits use cases
- Global Interpreter Lock (GIL): Already Python default
- No thread safety: Race conditions

**Decision**: Thread-safe with `threading.RLock`:
- Safe for multi-threaded use
- Minimal performance impact
- Compatible with async code

### 6. Why Immutable Events?

**Decision**: Events are frozen dataclasses.

**Alternatives Considered**:
- Mutable events: Hard to track, potential bugs
- Events as methods: More coupling

**Decision**: Immutable events provide:
- Event sourcing compatibility
- Safe for concurrent access
- Clear contract: events don't change

### 7. Why Skill-Based Extensibility?

**Decision**: Capabilities as composable skills.

**Alternatives Considered**:
- Plugin-only: Too heavy for simple extensions
- Hard-coded capabilities: Not extensible

**Decision**: Skills provide:
- Lightweight extension mechanism
- Version control for capabilities
- Composition of multiple skills
- Easy sharing and reuse

## Anti-Patterns to Avoid

### 1. Don't Block the Event Loop

```python
# BAD: Synchronous operation in async handler
async def on_event(event):
    result = blocking_operation()  # Blocks event loop

# GOOD: Use async or run in thread pool
async def on_event(event):
    result = await async_operation()
    # or
    result = await asyncio.to_thread(blocking_operation)
```

### 2. Don't Swallow Exceptions

```python
# BAD: Silent failure
try:
    risky_operation()
except Exception:
    pass

# GOOD: Log and re-raise or handle explicitly
try:
    risky_operation()
except SpecificError as e:
    logger.warning(f"Expected failure: {e}")
    handle_gracefully()
```

### 3. Don't Use Mutable Global State

```python
# BAD: Global state
GLOBAL_COUNTER = 0

# GOOD: Use context or state objects
class Context:
    counter: int = 0
```

## Performance Considerations

### Event Bus

- Event buffer size: 1000 events default
- Dead letter queue for failed handlers
- Async emission for non-blocking coordination

### Session Manager

- JSONL append-only for audit
- SQLite indexed by updated_at for fast queries
- Automatic compaction at 50+ messages

### Task Registry

- In-memory for speed
- Thread-safe for concurrent access
- Stats computed on-demand
