```yaml
name: General Manager - The Project
description: Config-driven conversational managers with MCP tool access. Factory pattern proves composition over construction.
created: 2025-11-26
version: 1.0.0
phase: GM1
```

# General Manager: Project Truth

## Sacred Primitive

```
General Manager = Config (YAML)
                + Factory (instantiation)
                + LLM Provider (ollama | claude)
                + MCP Tools (sovereign access)
                + Terminal Session (conversation)
```

**What General Manager IS:**
- Config-driven manager instantiation (YAML → running manager)
- Factory pattern proving composition: one factory → infinite managers
- LLM-agnostic design (Ollama first, Claude ready)
- MCP tool integration (Playwright + Filesystem MVP)
- Terminal-first conversation interface (critical constraint)

**What General Manager IS NOT:**
- A chatbot framework (managers have sovereign tool access)
- A replacement for Claude Code (managers are specialized, not general)
- An agent framework (managers are config-driven, not code-driven)
- A workflow engine (managers converse, not execute pipelines)

---

## The Truth Shift

### From: Code-Driven Agents
```python
# Old pattern: Agent logic in code
class ResearchAgent:
    def __init__(self):
        self.llm = Ollama("llama3.2")
        self.tools = [playwright, filesystem]
        self.system_prompt = "You are a research agent..."

    async def run(self, task):
        # Hardcoded logic
        pass
```

**Problem:** Every new agent requires code changes.

### To: Config-Driven Managers
```yaml
# New pattern: Manager definition in YAML
name: research_manager
identity:
  system_prompt: "./prompts/research_manager.md"
agency:
  provider: ollama
  model: llama3.2
tools:
  - playwright
  - filesystem
```

**Solution:** New managers require only config files.

```python
# One factory, infinite managers
manager = await ManagerFactory.from_config("managers/research_manager.yaml")
```

---

## Core Concepts

### 1. Manager (not Agent)

**Why "Manager"?**
- Agents execute tasks
- Managers *converse* and *coordinate*
- Managers have sovereign tool access (they decide when/how to use tools)
- Managers maintain session state with users

**Manager Capabilities:**
- Reason about user goals
- Decide which tools to use
- Execute tool calls via MCP
- Report results conversationally
- Maintain context across turns

### 2. Config-Driven Instantiation

**The Factory Pattern:**
```
YAML Config → ManagerFactory.from_config() → Running Manager
```

**Config Components:**
1. **Identity:** System prompt (from .md file)
2. **Agency:** LLM provider + model
3. **Tools:** MCP tool types (enum list)
4. **Runtime:** Limits (iterations, timeout)
5. **Terminal:** Conversation settings

### 3. Sovereign Tool Access

**Sovereignty = Manager decides tool usage**

The manager is not told which tools to use. It:
1. Receives user goal
2. Reasons about approach
3. Decides which tools (if any)
4. Executes tools autonomously
5. Reports results

**MCP Protocol:**
- Manager connects to MCP servers
- Lists available tools
- Calls tools with arguments
- Receives structured results

### 4. Terminal Session (Critical Constraint)

**Every manager MUST support terminal conversation.**

```bash
python run_manager.py managers/research_manager.yaml

==================================================
  research_manager
  Type 'quit' to exit | 'clear' to reset
==================================================

You: Find all Python files in /tmp and count them

Manager: I'll use the filesystem tool to search for Python files.
[Executing: search_files with pattern "*.py"]
Found 12 Python files in /tmp. Here's the breakdown...

You: Now open example.com and get the page title

Manager: I'll navigate to example.com using the browser.
[Executing: browser_navigate to https://example.com]
The page title is "Example Domain".
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Terminal Session                                           │
│  (User conversation loop)                                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  ConversationalManager (LangGraph)                          │
│                                                              │
│  Nodes:                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌─────────┐           │
│  │  reason  │───▶│execute_tools │───▶│ respond │           │
│  └──────────┘    └──────────────┘    └─────────┘           │
│       ↑                 │                                   │
│       └─────────────────┘ (loop if more tools needed)       │
│                                                              │
│  State: messages, tool_calls, tool_results, iteration       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  LLM Provider                                               │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  OllamaProvider │  │  ClaudeProvider │                  │
│  │  (local LLM)    │  │  (API - future) │                  │
│  └─────────────────┘  └─────────────────┘                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  Tool Registry (MCP Connections)                            │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Playwright  │  │ Filesystem  │  │  (future)   │         │
│  │ MCP Server  │  │ MCP Server  │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
general-manager/
├── sacred-core-general-manager/       # Project truth (this folder)
│   ├── 01-the-project.md              # What it IS
│   ├── 02-the-discipline.md           # Constraints
│   └── 03-implementation-plan.md      # Execution map
│
├── managers/                          # Manager configs (YAML)
│   ├── research_manager.yaml
│   └── dev_manager.yaml
│
├── prompts/                           # System prompts (Markdown)
│   ├── research_manager.md
│   └── dev_manager.md
│
├── gm/                                # Core package
│   ├── __init__.py
│   ├── config.py                      # Config loader + schema
│   ├── factory.py                     # ManagerFactory
│   ├── manager.py                     # LangGraph manager
│   ├── llm_providers.py               # Ollama/Claude
│   ├── tool_registry.py               # MCP connections
│   └── terminal/
│       ├── __init__.py
│       └── session.py                 # TerminalSession
│
├── run_manager.py                     # Entry point
├── requirements.txt
└── README.md
```

---

## Success Criteria

### MVP Complete When:

1. **Config loads successfully**
   ```python
   config = load_manager_config("managers/research_manager.yaml")
   assert config.name == "research_manager"
   ```

2. **Factory creates manager**
   ```python
   manager = await ManagerFactory.from_config("managers/research_manager.yaml")
   assert manager.config.name == "research_manager"
   ```

3. **Tools connect via MCP**
   ```python
   assert len(manager.tools.tool_schemas) > 0
   assert "read_file" in manager.tools.tools
   assert "browser_navigate" in manager.tools.tools
   ```

4. **Manager reasons and uses tools**
   ```python
   response = await manager.chat("List files in /tmp")
   assert "files" in response.lower() or manager.tools was called
   ```

5. **Terminal session works**
   ```bash
   python run_manager.py managers/research_manager.yaml
   # Interactive conversation succeeds
   ```

---

## What This Enables

### Immediate (MVP)
- Conversational manager with Ollama + 2 MCP tools
- Terminal-based interaction
- Config-driven instantiation

### Next (Post-MVP)
- Claude provider (API-based LLM)
- More MCP tools (GitHub, database, etc.)
- Session persistence (checkpointer)
- Constraint enforcement (void() pattern)

### Future (Composition)
- Managers as Worker Marketplace workers
- Multi-manager orchestration
- LangGraph workflow integration
- Trust level escalation

---

## The Primitive Proven

```
Config (YAML) → Factory → Manager → Terminal → Conversation
```

**One factory. Infinite managers. Zero code changes per manager.**

This is the leverage point. Everything else is composition.
