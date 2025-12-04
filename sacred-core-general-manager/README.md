# Sacred Core: General Manager (GM1)

**Status: ✅ PARKED** - GM1.1-GM1.4 Complete, tested with GPT-4o + Brave Search

**Config-driven conversational managers with MCP tool access.**

---

## What This Is

**General Manager** is a factory pattern implementation that creates conversational AI managers from YAML config files. Each manager has:
- **Identity** (system prompt from Markdown)
- **Agency** (LLM provider: Ollama, OpenAI, or Claude)
- **Tools** (MCP server connections)
- **Terminal** (interactive conversation interface)

---

## Quick Start

```bash
# From langgraph-platform root
cd /Users/tarun/claude-workspace/workspace/langgraph-platform
python3 playground/run_manager.py general_manager/managers/research_manager.yaml

You: Search the web for latest AI news
Manager: [Uses brave_search tool, returns results]

You: List files in /Users/tarun/workspace
Manager: [Uses filesystem tool, returns directory listing]
```

---

## Implementation Status

| Phase | Task | Status |
|-------|------|--------|
| GM1.1 | Config Schema & Loader | ✅ Complete |
| GM1.2 | LLM Provider (Multi) | ✅ Complete (Ollama, OpenAI, Claude) |
| GM1.3 | MCP Tool Registry | ✅ Complete (Brave Search, Filesystem, Playwright) |
| GM1.4 | LangGraph Manager + Terminal | ✅ Complete |

**Branch:** `feature/general-manager`

---

## File Structure (Actual)

```
langgraph-platform/
├── general_manager/              # Core platform module
│   ├── config.py                # YAML schema and loader
│   ├── factory.py               # Manager instantiation
│   ├── manager.py               # LangGraph state machine
│   ├── llm_providers.py         # Multi-provider support
│   ├── tool_registry.py         # MCP tool connections
│   ├── terminal/                # Interactive conversation
│   ├── managers/                # YAML configs
│   │   └── research_manager.yaml
│   └── prompts/                 # System prompts
│       └── research_manager.md
├── playground/                   # Testing tools
│   ├── run_manager.py           # Interactive runner
│   └── mcp-integration-notes.md # MCP notes
└── sacred-core-general-manager/ # This folder
```

---

## Sacred Constraints

1. **TERMINAL_CONVERSATION_REQUIRED** - Every manager supports `chat()`
2. **CONFIG_DRIVEN_INSTANTIATION** - YAML config, not code
3. **SOVEREIGN_TOOL_ACCESS** - Manager decides tool usage
4. **LLM_PROVIDER_ABSTRACTION** - Provider from enum, not hardcoded
5. **MCP_PROTOCOL_COMPLIANCE** - All tools via MCP protocol

---

## Documents

| Document | Purpose |
|----------|---------|
| [01-the-project.md](01-the-project.md) | What General Manager IS |
| [02-the-discipline.md](02-the-discipline.md) | Sacred constraints |
| [03-implementation-plan.md](03-implementation-plan.md) | Implementation roadmap |

---

## Prerequisites

```bash
# Node.js (for MCP servers)
node --version  # v18+

# Python dependencies
pip install langgraph pyyaml httpx python-dotenv langfuse

# API Keys in .env
OPENAI_API_KEY=...
BRAVE_API_KEY=...
```
