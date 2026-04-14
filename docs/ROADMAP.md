# Roadmap

## Version 1.0 - Foundation (Current)

### Core Runtime ✅

- [x] State machine lifecycle
- [x] Event bus with typed events
- [x] Task registry
- [x] Session persistence
- [x] Permission enforcement
- [x] Slash commands

### Documentation ✅

- [x] CLAUDE.md for AI agent guidance
- [x] README.md with overview
- [x] PHILOSOPHY.md with design rationale
- [x] ARCHITECTURE.md technical deep-dive
- [x] DESIGN.md design decisions
- [x] ROADMAP.md (this file)

## Version 1.1 - Capability Expansion

### Skills System

- [ ] Skill discovery from filesystem
- [ ] Skill versioning
- [ ] Skill composition
- [ ] Skill marketplace integration

### Tool Enhancements

- [ ] Web search tool
- [ ] Web fetch tool
- [ ] Git integration tool
- [ ] Docker integration tool

### LLM Integration

- [ ] Claude API integration
- [ ] OpenAI API integration
- [ ] Local model support (Ollama)
- [ ] Multi-model routing

## Version 1.2 - Multi-Agent Coordination

### Team System

- [ ] Team creation and management
- [ ] Agent handoff
- [ ] Shared context
- [ ] Conflict resolution

### Parallel Execution

- [ ] Task parallelization
- [ ] Result aggregation
- [ ] Dependency management
- [ ] Load balancing

## Version 1.3 - Production Hardening

### Reliability

- [ ] Automatic recovery recipes
- [ ] Circuit breaker pattern
- [ ] Rate limiting
- [ ] Retry with backoff

### Observability

- [ ] Distributed tracing
- [ ] Metrics dashboard
- [ ] Log aggregation
- [ ] Alert routing

## Version 2.0 - Ecosystem

### IDE Integration

- [ ] VS Code extension
- [ ] JetBrains plugin
- [ ] Neovim plugin

### Platform Integration

- [ ] GitHub Actions integration
- [ ] Slack integration
- [ ] Discord bot
- [ ] Web dashboard

### Cloud Deployment

- [ ] Docker deployment
- [ ] Kubernetes operator
- [ ] Cloud provider templates
- [ ] Serverless option

## Open Questions

### Long-term

1. Should we support multiple simultaneous sessions per agent?
2. How to handle agent "personality" or specialized roles?
3. What is the right abstraction for agent memory?
4. How to enable agent-to-agent negotiation?

### Medium-term

1. When to use tools vs. skills?
2. How to version skills without breaking compatibility?
3. Should we support imperative vs. declarative skill definitions?

---

## Legend

- [ ] Not started
- [w] In progress
- [x] Completed
