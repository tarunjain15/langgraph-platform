# Sacred Core: General Manager (GM1)

**Config-driven conversational managers with MCP tool access.**

---

## What This Is

**General Manager** is a factory pattern implementation that creates conversational AI managers from YAML config files. Each manager has:
- **Identity** (system prompt from Markdown)
- **Agency** (LLM provider: Ollama or Claude)
- **Tools** (MCP server connections)
- **Terminal** (interactive conversation interface)

---

## Quick Start

```bash
# After implementation complete
python run_manager.py managers/research_manager.yaml

You: List files in /tmp
Manager: [Uses filesystem tool, returns results]

You: Navigate to example.com
Manager: [Uses playwright tool, opens browser]
```

---

## Documents

| Document | Purpose | Read When |
|----------|---------|-----------|
| [01-the-project.md](01-the-project.md) | What General Manager IS | Starting the project |
| [02-the-discipline.md](02-the-discipline.md) | Sacred constraints | Making design decisions |
| [03-implementation-plan.md](03-implementation-plan.md) | Execution roadmap | Implementing features |

---

## Reading Order

1. **Start:** [01-the-project.md](01-the-project.md) - Understand the primitive
2. **Constraints:** [02-the-discipline.md](02-the-discipline.md) - Know the rules
3. **Execute:** [03-implementation-plan.md](03-implementation-plan.md) - Follow the plan

---

## The Primitive

```
Config (YAML) → Factory → Manager → Terminal → Conversation
```

**One factory. Infinite managers. Zero code changes per manager.**

---

## Implementation Phases

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| GM1.1 | Config Schema & Loader | 45 min | Pending |
| GM1.2 | LLM Provider (Ollama) | 1 hour | Pending |
| GM1.3 | MCP Tool Registry | 1.5 hours | Pending |
| GM1.4 | LangGraph Manager + Terminal | 2 hours | Pending |

**Total Estimated:** 4-6 hours

---

## Sacred Constraints

1. **TERMINAL_CONVERSATION_REQUIRED** - Every manager supports `chat()`
2. **CONFIG_DRIVEN_INSTANTIATION** - YAML config, not code
3. **SOVEREIGN_TOOL_ACCESS** - Manager decides tool usage
4. **LLM_PROVIDER_ABSTRACTION** - Provider from enum, not hardcoded
5. **MCP_PROTOCOL_COMPLIANCE** - All tools via MCP protocol

---

## File Structure (Target)

```
general-manager/
├── sacred-core-general-manager/   # This folder
├── managers/                      # YAML configs
├── prompts/                       # System prompts
├── gm/                            # Core package
│   ├── config.py
│   ├── factory.py
│   ├── manager.py
│   ├── llm_providers.py
│   ├── tool_registry.py
│   └── terminal/
└── run_manager.py
```

---

## Prerequisites

```bash
# Ollama (local LLM)
ollama serve
ollama pull llama3.2

# Node.js (for MCP servers)
node --version  # v18+

# Python
python -m venv venv
pip install langgraph mcp pyyaml httpx
```
