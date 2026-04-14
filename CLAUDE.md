# CLAUDE.md

This file provides guidance to AI coding agents (Claude Code, OpenAI Codex, etc.) when working with this repository.

## Project Overview

**AI-Skill-AICodingAgentFramework** — A next-generation autonomous software development framework inspired by claw-code's coordination philosophy.

The core insight: **humans provide direction; agents perform the labor.**

## Detected Stack

- **Language**: Python 3.10+
- **Architecture**: Event-driven, multi-agent coordination
- **Inspiration**: claw-code (Rust), oh-my-codex, clawhip

## Key Principles

1. **State machine first** — Every agent has explicit lifecycle states
2. **Events over logs** — Typed events instead of scraped prose
3. **Recovery before escalation** — Auto-heal known failures once
4. **Natural language interface** — Human-readable directives
5. **Skill-based extensibility** — Capabilities as composable skills

## Repository Structure

```
AI-Skill-AICodingAgentFramework/
├── src/                    # Core framework modules
│   ├── runtime.py          # AgentRuntime with state machine
│   ├── session.py          # Session persistence
│   ├── task_manager.py     # TaskRegistry lifecycle
│   ├── event_bus.py        # Event-driven coordination
│   ├── permission.py       # Permission enforcement
│   ├── telemetry.py        # Usage tracking
│   ├── slash_commands.py   # CLI command surface
│   ├── query_engine.py     # Intent routing
│   ├── tool_pool.py        # Tool registry
│   └── plugin_registry.py  # Plugin discovery
├── skills/                 # Skill definitions
├── docs/                   # Architecture documentation
├── examples/               # Usage examples
└── tests/                  # Test suite
```

## Development Commands

```bash
# Run tests
python -m pytest tests/

# Lint
python -m ruff check src/

# Format
python -m ruff format src/

# Type check
python -m mypy src/
```

## Coding Standards

- All public APIs must have type hints
- Docstrings follow Google style
- Error handling: raise specific exceptions, never swallow silently
- Thread safety for all shared state
- Events are immutable dataclasses

## Session Behavior

- Sessions persist across restarts (JSONL + SQLite)
- Resume with `--resume latest` or session ID
- `/compact` reduces context window size
- `/session` shows current session state

## Tool Safety

- **Read-only mode**: File reads only, no writes
- **Workspace mode**: Write within project only
- **Danger mode**: Full filesystem + shell access
- Always validate workspace boundaries
- Respect `.gitignore` and sensitive files
