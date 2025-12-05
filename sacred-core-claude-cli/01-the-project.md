```yaml
name: Claude Code CLI Integration
description: Minimal interface for Claude Code CLI as a Langfuse-native LLM provider at the same level as Ollama/OpenAI.
created: 2025-11-26
status: architecture_complete
```

# The Project: Claude Code CLI as LLM Provider

## Sacred Primitive

```
Claude Code CLI = LLMProvider
Same interface as Ollama. Same interface as OpenAI.
The transport is subprocess + JSON. The contract is identical.
```

## The Core Realization

**Claude Code CLI returns EXACTLY what Langfuse needs:**

```json
{
  "session_id": "abc123",
  "result": "...",
  "total_cost_usd": 0.003,
  "num_turns": 6,
  "duration_ms": 1234
}
```

**This IS the same interface as OpenAI/Ollama `chat.completions`:**

| Field | Ollama/OpenAI | Claude Code CLI |
|-------|---------------|-----------------|
| Output | `choices[0].message.content` | `result` |
| Session ID | `id` | `session_id` |
| Cost | Calculated externally | **Native: `total_cost_usd`** |
| Duration | N/A | **Native: `duration_ms`** |
| Turns | N/A | **Native: `num_turns`** |

**Claude Code CLI provides MORE observability data than OpenAI/Ollama.**

---

## The Three Primitives (Clean Distinction)

### 1. Claude API (Thin-Client)
```yaml
what: LLM completions only (Messages API)
tools: None (you build in LangGraph)
session: Stateless
cost: Per-token ($3/$15 per 1M tokens)
langfuse: Native via langfuse.openai.OpenAI
use_when: Simple LLM calls without tool use
```

### 2. Claude Code CLI (Agent Runtime)
```yaml
what: Full agent runtime via CLI subprocess
tools: 7+ built-in (Read, Write, Bash, Git, Browser, MCP)
session: Optional (--resume session_id)
cost: Per-token (from CLI response)
langfuse: Native via @observe + JSON response
use_when: Agentic tasks requiring filesystem/tools
```

### 3. Claude Code Container (Isolated Agent)
```yaml
what: Same as CLI but in Docker container
tools: Same as CLI
session: Same as CLI
cost: Same as CLI
langfuse: Same as CLI
use_when: Multi-tenant isolation, sandboxed execution
```

**The CLI and Container use the SAME interface. The only difference is the isolation boundary.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│                   (State management)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLMProvider Interface                     │
│          execute_task(task, state, config) → state_updates   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ OllamaProvider│   │ ClaudeAPI     │   │ClaudeCodeProv.│
├───────────────┤   ├───────────────┤   ├───────────────┤
│ OpenAI compat │   │ OpenAI compat │   │ subprocess    │
│ HTTP API      │   │ HTTP API      │   │ + JSON parse  │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ @observe      │   │ @observe      │   │ @observe      │
│ (Langfuse)    │   │ (Langfuse)    │   │ (Langfuse)    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   localhost:11434   api.anthropic.com    claude CLI
   (Ollama server)   (Anthropic API)      (subprocess)
```

---

## The Interface Contract

### LLMProvider Base Class
```python
class LLMProvider(ABC):
    @abstractmethod
    async def execute_task(
        self,
        task: str,
        state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Returns state updates with {role}_output, {role}_session_id, {role}_tokens"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    @abstractmethod
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        pass
```

### State Updates Contract
```python
# All providers return the same structure
{
    f"{role_name}_output": str,       # The response content
    f"{role_name}_session_id": str,   # Session/request ID
    f"{role_name}_tokens": {          # Usage metadata
        "cost": float,                # USD cost
        "input": int,                 # Input tokens (optional)
        "output": int,                # Output tokens (optional)
        "duration_ms": int,           # Execution time (optional)
        "turns": int                  # Conversation turns (optional)
    }
}
```

---

## Statefulness Model

### Stateless Mode (Default)
```python
# Every call is independent - no session passed
result = await provider.execute_task("analyze code", state={}, config={})
```

### Stateful Mode (Optional)
```python
# Pass session_id in state for continuity
result = await provider.execute_task(
    "now optimize it",
    state={"writer_session_id": "abc123"},
    config={}
)
# Claude Code resumes context via --resume flag
```

**Statefulness is a CONFIGURATION CHOICE, not an architectural requirement.**

---

## Why This Matters

### Before (Complex MCP Bridge)
```
LangGraph → MCPSessionManager → docker exec → mesh_execute
    → parse text output → regex extract session_id
```

### After (Simple Subprocess)
```
LangGraph → subprocess.run(['claude', '-p', ...]) → json.loads()
    → native session_id, cost, duration in JSON
```

**Reduction:** ~400 lines of MCP bridge code → ~80 lines of subprocess wrapper.

---

## Key Files

```yaml
implementation:
  - lgp/agents/base.py                  # LLMProvider interface
  - lgp/agents/ollama_provider.py       # Reference implementation
  - lgp/agents/claude_code_provider.py  # NEW: Claude Code CLI provider

documentation:
  - sacred-core-claude-cli/01-the-project.md  # This file
  - sacred-core-claude-cli/02-the-discipline.md
  - sacred-core-claude-cli/03-implementation.md

reference:
  - https://code.claude.com/docs/en/headless
  - https://github.com/anthropics/claude-agent-sdk-python
```

---

## Truth State

```yaml
revelation:
  claude_code_cli_is: "Just another LLMProvider"
  interface_parity: "Identical to Ollama/OpenAI"
  observability: "BETTER than OpenAI (native cost, duration, turns)"

decision:
  use_cli_directly: "Not MCP bridge"
  json_output: "Native structured data"
  session_optional: "Stateless by default, --resume for continuity"

outcome:
  complexity_reduction: "400 lines → 80 lines"
  langfuse_integration: "Native @observe"
  provider_parity: "Same interface as Ollama"
```
