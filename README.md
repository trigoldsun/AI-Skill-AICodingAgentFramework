# AI Coding Agent Framework

<p align="center">
  <img src="assets/hero.png" alt="AI Coding Agent Framework" width="300" />
</p>

<p align="center">
  <strong>A next-generation autonomous software development framework</strong>
</p>

<p align="center">
  <a href="https://github.com/trigoldsun/AI-Skill-AICodingAgentFramework">
    <img src="https://img.shields.io/badge/GitHub-Repository-blue" alt="GitHub">
  </a>
  <a href="./docs/PHILOSOPHY.md">
    <img src="https://img.shields.io/badge/Philosophy-Events%20over%20Logs-green" alt="Philosophy">
  </a>
  <a href="./docs/ARCHITECTURE.md">
    <img src="https://img.shields.io/badge/Architecture-Event%20Driven-orange" alt="Architecture">
  </a>
  <a href="./docs/ROADMAP.md">
    <img src="https://img.shields.io/badge/Status-Roadmap%20v1.0-red" alt="Status">
  </a>
</p>

---

## Philosophy

> **"Humans provide direction; agents perform the labor."**

AI Coding Agent Framework is built on a fundamental insight: as coding agents become capable enough to rebuild codebases autonomously, the scarce resource shifts from typing speed to **architectural clarity**, **task decomposition**, and **judgment about what deserves to exist**.

This framework demonstrates what happens when:
- A human provides clear direction via natural language
- Multiple coding agents coordinate in parallel
- Event routing is pushed outside the agent context window
- Planning, execution, review, and retry loops are automated
- The human does **not** sit micromanaging every step

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Coding Agent Framework                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │  Human CLI   │───▶│  Event Bus   │───▶│    Agent     │        │
│  │  (Discord/   │    │  (clawhip)   │    │   Runtime    │        │
│  │   Terminal)  │    └──────────────┘    └──────────────┘        │
│  └──────────────┘           │                   │                 │
│                              ▼                   ▼                 │
│                      ┌──────────────┐    ┌──────────────┐        │
│                      │    Task      │    │    Skill     │        │
│                      │   Registry   │    │   Registry   │        │
│                      └──────────────┘    └──────────────┘        │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   Session     │    │   Tool       │    │  Permission  │        │
│  │   Manager     │    │   Pool       │    │   Enforcer    │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Three-Layer System

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Coordination** | Event Bus | Event routing, notification delivery |
| **Execution** | Agent Runtime | State machine, tool execution, session management |
| **Capability** | Skill Registry | Composable, versioned skill definitions |

## Features

| Feature | Status | Description |
|---------|--------|-------------|
| Natural Language Interface | ✅ | Direct human指令 via CLI or Discord |
| Event-Driven Architecture | ✅ | Typed events over log scraping |
| State Machine Lifecycle | ✅ | Explicit agent states (spawning → running → finished) |
| Task Registry | ✅ | In-memory task lifecycle management |
| Session Persistence | ✅ | JSONL + SQLite for resume across restarts |
| Permission Enforcement | ✅ | read-only / workspace-write / danger-full-access |
| Skill System | ✅ | Composable skill definitions with versioning |
| Tool Pool | ✅ | Dynamic tool registration and execution |
| Plugin Architecture | ✅ | External plugin discovery and loading |
| Telemetry | ✅ | Usage tracking and cost estimation |
| Slash Commands | ✅ | REPL commands: `/doctor`, `/compact`, `/skills`, etc. |

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/trigoldsun/AI-Skill-AICodingAgentFramework.git
cd AI-Skill-AICodingAgentFramework

# Install dependencies
pip install -e .

# Verify setup
python -m agent_framework doctor
```

### Basic Usage

```python
from agent_framework import Agent, PermissionMode

# Create an agent
agent = Agent(
    name="dev-assistant",
    model="claude-sonnet-4",
    permission_mode=PermissionMode.WORKSPACE_WRITE
)

# Natural language driven
result = agent.execute("Create a REST API for user authentication")
```

### CLI Usage

```bash
# Interactive REPL
python -m agent_framework

# One-shot prompt
python -m agent_framework prompt "Explain this codebase"

# With model selection
python -m agent_framework --model sonnet prompt "Review this code"

# Session resume
python -m agent_framework --resume latest /doctor
```

## Documentation

| Document | Purpose |
|----------|---------|
| [PHILOSOPHY.md](./docs/PHILOSOPHY.md) | Project intent, system design rationale |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Technical architecture deep-dive |
| [DESIGN.md](./docs/DESIGN.md) | Design decisions and patterns |
| [ROADMAP.md](./docs/ROADMAP.md) | Current status and future roadmap |

## Ecosystem

This framework is inspired by and integrates with:

- [claw-code](https://github.com/ultraworkers/claw-code) — Rust CLI agent harness
- [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) — Workflow layer for agent coordination
- [clawhip](https://github.com/Yeachan-Heo/clawhip) — Event and notification router
- [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) — Multi-agent coordination

## License

MIT

---

## v1.1.0 新特性（基于 Claw Code 思路）

### 🆕 LLM Provider 抽象层

```python
from agent_framework import Agent, create_provider

# 自动路由到 Anthropic/OpenAI/xAI/DashScope
agent = Agent(name="dev", model="sonnet")
```

### 🛠️ 8 个真实可执行工具

| 工具 | 说明 |
|------|------|
| `bash` | 执行 Shell 命令 |
| `read` | 读取文件 |
| `write` | 写入文件 |
| `edit` | 编辑文件（替换） |
| `grep` | 正则搜索 |
| `glob` | 文件匹配 |
| `web_search` | 网页搜索 |
| `web_fetch` | 抓取网页 |

### 🤖 LLM 驱动的任务规划

```python
from agent_framework import Planner
planner = Planner(llm_provider)
plan = await planner.plan("创建一个 REST API")
```

### 🧪 Mock Parity Harness

```bash
python -m agent_framework test
```

### 📊 /doctor 健康检查

```bash
python -m agent_framework doctor
```
