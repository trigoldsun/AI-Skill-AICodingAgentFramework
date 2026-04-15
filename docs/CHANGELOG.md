
---

## v1.1.0 (2026-04-15)

### 新增组件

#### `providers/` - LLM Provider 抽象层
- 自动检测模型类型路由到对应 Provider
- 支持 Anthropic (Claude)、OpenAI (GPT)、xAI (Grok)、DashScope (Qwen)
- 模型别名：opus、sonnet、haiku、grok、grok-mini
- 需要 `pip install aiohttp`

#### `tools/` - 真实可执行工具集
- `BashTool`: 真正执行 Shell 命令（带超时和安全检查）
- `ReadFileTool`: 读取文件（支持 offset/limit）
- `WriteFileTool`: 写入文件（自动创建父目录）
- `EditFileTool`: 替换文件内容
- `GrepSearchTool`: 正则搜索
- `GlobSearchTool`: 文件匹配
- `WebSearchTool`: 网页搜索
- `WebFetchTool`: 网页抓取

#### `planning/` - LLM 驱动的任务规划
- 替代关键词匹配，让 LLM 分析意图并生成执行步骤
- `Planner` 类接收 LLM Provider，自动规划

#### `mocks/` - Mock Parity Harness
- `MockAnthropicService`: 确定性 Mock 服务
- `ParityHarness`: 端到端测试框架
- 无需真实 API Key 也能验证框架正确性

#### `cli/` - 命令行界面
- `/doctor` 健康检查命令

### 改进

- `runtime.py`: 集成新 Provider 和工具池，`_step_generate_code` 真正调用 LLM
- `__init__.py`: 版本升至 1.1.0，导出所有新组件
- 正确的包结构 (`src/agent_framework/`)
- `pyproject.toml`: 支持 `pip install -e .`
