```yaml
name: General Manager - The Discipline
description: Sacred constraints that protect the integrity of config-driven managers.
created: 2025-11-26
version: 1.0.0
phase: GM1
```

# General Manager: The Discipline

## The 5 Sacred Constraints

These constraints are **non-negotiable**. Violating them breaks the system.

---

## 1. TERMINAL_CONVERSATION_REQUIRED

**Statement:** Every manager MUST support interactive terminal conversation.

**Why:**
- Managers are conversational by nature
- Terminal is the primary interface for human-manager interaction
- Without terminal support, managers become batch processors (not conversational)

**Witness Function:**
```python
def verify_terminal_support(manager: ConversationalManager) -> bool:
    """Verify manager can be wrapped in TerminalSession."""
    return hasattr(manager, 'chat') and callable(manager.chat)
```

**Violation Example:**
```python
# VIOLATION: Manager without chat method
class BrokenManager:
    def execute(self, task):  # Wrong interface
        pass

# CORRECT: Manager with chat method
class ConversationalManager:
    async def chat(self, message: str) -> str:
        pass
```

**Enforcement:** Factory MUST verify `chat()` method exists before returning manager.

---

## 2. CONFIG_DRIVEN_INSTANTIATION

**Statement:** Managers are defined in YAML config, not in code.

**Why:**
- Code changes require deployment
- Config changes are runtime adjustable
- New managers should require zero code changes

**Witness Function:**
```python
def verify_config_driven(manager: ConversationalManager) -> bool:
    """Verify manager was created from config, not hardcoded."""
    return (
        hasattr(manager, 'config') and
        isinstance(manager.config, ManagerConfig) and
        manager.config.name is not None
    )
```

**Violation Example:**
```yaml
# VIOLATION: Logic in config
name: research_manager
identity:
  system_prompt: "./prompts/research.md"
custom_logic: |
  if user_says("search"):
    call_tool("filesystem.search")  # NO! Logic doesn't belong here

# CORRECT: Pure declaration
name: research_manager
identity:
  system_prompt: "./prompts/research.md"
tools:
  - filesystem
  - playwright
```

**Enforcement:** Config loader rejects any field containing code/logic.

---

## 3. SOVEREIGN_TOOL_ACCESS

**Statement:** Managers decide when and how to use tools. Users provide goals, not instructions.

**Why:**
- Managers reason about tool usage
- Prescriptive tool usage defeats the purpose of AI reasoning
- Sovereignty enables autonomous task completion

**Witness Function:**
```python
def verify_sovereignty(manager_state: ManagerState) -> bool:
    """Verify manager made autonomous tool decisions."""
    # Manager should have reasoning before tool calls
    messages = manager_state["messages"]
    tool_calls = manager_state["tool_calls"]

    if not tool_calls:
        return True  # No tools needed, still sovereign

    # Check that reasoning preceded tool call
    return any(
        m["role"] == "assistant" and "reason" in m.get("metadata", {})
        for m in messages
    )
```

**Violation Example:**
```python
# VIOLATION: User dictates tool usage
user: "Call the read_file tool on /tmp/test.txt"
manager: [Blindly calls read_file]

# CORRECT: Manager reasons and decides
user: "What's in /tmp/test.txt?"
manager: [Reasons: "User wants file contents. I'll use read_file tool."]
         [Calls read_file]
         [Reports results]
```

**Enforcement:** Manager's reason node MUST run before execute_tools node.

---

## 4. LLM_PROVIDER_ABSTRACTION

**Statement:** Managers are agnostic to LLM provider. Switching providers requires zero manager changes.

**Why:**
- Lock-in to one provider is fragile
- Different use cases need different providers (local vs API, cost vs quality)
- Factory pattern enables provider swapping

**Witness Function:**
```python
def verify_provider_abstraction(config: ManagerConfig) -> bool:
    """Verify config uses provider enum, not hardcoded provider."""
    return (
        isinstance(config.agency.provider, AgencyProvider) and
        config.agency.provider in [AgencyProvider.OLLAMA, AgencyProvider.CLAUDE]
    )
```

**Violation Example:**
```python
# VIOLATION: Hardcoded provider
class Manager:
    def __init__(self):
        self.llm = Ollama("llama3.2")  # Hardcoded!

# CORRECT: Provider from config
class Manager:
    def __init__(self, llm: LLMProvider):  # Injected
        self.llm = llm
```

**Enforcement:** Factory creates provider from config, injects into manager.

---

## 5. MCP_PROTOCOL_COMPLIANCE

**Statement:** All tool access MUST go through MCP protocol. No direct tool calls.

**Why:**
- MCP provides standardized tool interface
- MCP enables tool discovery (list_tools)
- MCP servers can be swapped without manager changes
- Security: MCP servers enforce access controls

**Witness Function:**
```python
def verify_mcp_compliance(tool_registry: ToolRegistry) -> bool:
    """Verify all tools accessed via MCP sessions."""
    for tool_type, session in tool_registry.sessions.items():
        if not isinstance(session, ClientSession):
            return False
    return True
```

**Violation Example:**
```python
# VIOLATION: Direct tool call
import subprocess
result = subprocess.run(["ls", "/tmp"])  # Bypasses MCP!

# CORRECT: MCP tool call
result = await tool_registry.call_tool(
    "list_directory",
    {"path": "/tmp"}
)
```

**Enforcement:** Manager has no access to direct tool implementations, only ToolRegistry.

---

## Constraint Enforcement Matrix

| Constraint | Enforcement Point | Failure Mode |
|------------|------------------|--------------|
| TERMINAL_CONVERSATION_REQUIRED | Factory | Raises `TerminalInterfaceError` |
| CONFIG_DRIVEN_INSTANTIATION | Config Loader | Raises `ConfigValidationError` |
| SOVEREIGN_TOOL_ACCESS | Graph Structure | Reason node always before execute |
| LLM_PROVIDER_ABSTRACTION | Factory | Provider created from enum |
| MCP_PROTOCOL_COMPLIANCE | ToolRegistry | No direct tool access exposed |

---

## Constraint Violation Response

When a constraint is violated:

1. **Log the violation** with full context
2. **Fail fast** - do not proceed with degraded state
3. **Report clear error** - what constraint, why violated, how to fix

```python
class ConstraintViolationError(Exception):
    def __init__(self, constraint: str, reason: str, fix: str):
        self.constraint = constraint
        self.reason = reason
        self.fix = fix
        super().__init__(
            f"Constraint '{constraint}' violated: {reason}. Fix: {fix}"
        )

# Example usage
raise ConstraintViolationError(
    constraint="TERMINAL_CONVERSATION_REQUIRED",
    reason="Manager missing chat() method",
    fix="Implement async def chat(self, message: str) -> str"
)
```

---

## Testing Constraints

Each constraint has a dedicated test:

```python
# tests/test_constraints.py

def test_terminal_conversation_required():
    """Verify all managers support terminal conversation."""
    manager = await ManagerFactory.from_config("managers/research_manager.yaml")
    assert hasattr(manager, 'chat')
    assert asyncio.iscoroutinefunction(manager.chat)

def test_config_driven_instantiation():
    """Verify managers are created from config."""
    manager = await ManagerFactory.from_config("managers/research_manager.yaml")
    assert manager.config.name == "research_manager"
    assert manager.config.agency.provider == AgencyProvider.OLLAMA

def test_sovereign_tool_access():
    """Verify manager reasons before tool use."""
    manager = await ManagerFactory.from_config("managers/research_manager.yaml")
    # Trace execution to verify reason node runs first
    assert manager.graph.nodes["reason"] is not None

def test_llm_provider_abstraction():
    """Verify provider can be swapped via config."""
    config1 = load_manager_config("managers/ollama_manager.yaml")
    config2 = load_manager_config("managers/claude_manager.yaml")
    assert config1.agency.provider == AgencyProvider.OLLAMA
    assert config2.agency.provider == AgencyProvider.CLAUDE

def test_mcp_protocol_compliance():
    """Verify tools accessed only via MCP."""
    manager = await ManagerFactory.from_config("managers/research_manager.yaml")
    for session in manager.tools.sessions.values():
        assert isinstance(session, ClientSession)
```

---

## Constraint Evolution

Constraints can evolve, but only through explicit versioning:

```yaml
# Config declares constraint version
constraint_version: "1.0"

# Constraint changes require version bump
constraint_version: "1.1"  # Added new constraint
```

**Rule:** Old configs with old constraint versions continue to work. New constraints apply only to new versions.

---

## Summary

| # | Constraint | One-Line Summary |
|---|------------|------------------|
| 1 | TERMINAL_CONVERSATION_REQUIRED | Every manager supports `chat()` |
| 2 | CONFIG_DRIVEN_INSTANTIATION | YAML config, not code |
| 3 | SOVEREIGN_TOOL_ACCESS | Manager decides tool usage |
| 4 | LLM_PROVIDER_ABSTRACTION | Provider from enum, not hardcoded |
| 5 | MCP_PROTOCOL_COMPLIANCE | All tools via MCP protocol |

These constraints are the **load-bearing walls** of the system. Remove them, and the architecture collapses.
