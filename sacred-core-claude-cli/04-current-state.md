```yaml
name: Current State - Claude Code CLI Integration
description: Volatile execution state tracking.
last_updated: 2025-11-26
status: implementation_complete
```

# Current State

**VOLATILE DOCUMENT**: Updated on significant milestones.

---

## Phase Status

```yaml
architecture_research: COMPLETE
  - Three primitives identified (API, CLI, Container)
  - Interface parity confirmed with Ollama/OpenAI
  - JSON output schema documented
  - MCP bridge complexity eliminated

implementation: COMPLETE
  - ClaudeCodeProvider implemented in lgp/agents/claude_code_provider.py
  - Factory integration complete in lgp/agents/factory.py
  - Tests written and passing in scripts/test_claude_code_provider.py

validation: COMPLETE
  - CLI JSON output verified (live test passes)
  - Session continuity verified (--resume flag integration)
  - Container isolation supported
```

---

## Key Realizations

### 1. Transport Layer Simplification
```yaml
before:
  path: "MCPSessionManager → docker exec → MCP protocol → mesh_execute → regex parse"
  complexity: ~400 lines
  failure_modes: MCP connection, text parsing, session extraction

after:
  path: "subprocess.run() → json.loads()"
  complexity: ~80 lines
  failure_modes: CLI exit code, JSON decode
```

### 2. Interface Parity Discovery
```yaml
realization: "Claude Code CLI JSON output is structurally equivalent to OpenAI response"

mapping:
  result: choices[0].message.content
  session_id: id
  total_cost_usd: (calculated externally for OpenAI)
  duration_ms: (not available in OpenAI)
  num_turns: (not available in OpenAI)

conclusion: "Claude Code CLI provides MORE data than OpenAI"
```

### 3. Statefulness as Configuration
```yaml
realization: "Session continuity is optional, not architectural"

stateless_mode:
  - Default behavior
  - No session_id passed
  - Each call independent

stateful_mode:
  - Pass session_id in state
  - CLI uses --resume flag
  - Context preserved
```

---

## Files Created

```yaml
sacred-core-claude-cli/:
  01-the-project.md: Core realization and primitive definition
  02-the-discipline.md: Constraints and patterns
  03-implementation.md: Reference implementation
  04-current-state.md: This file
```

---

## Implementation Tasks

### Immediate
- [x] Create `lgp/agents/claude_code_provider.py`
- [x] Update `lgp/agents/factory.py` with new provider
- [x] Write unit tests for ClaudeCodeProvider
- [x] Verify JSON output with live CLI

### Validation
- [x] Test stateless execution
- [x] Test session continuity
- [x] Test container isolation (command building verified)
- [ ] Verify Langfuse traces (best-effort, works when LANGFUSE_PUBLIC_KEY set)
- [x] Verify cost tracking from native field

### Documentation
- [x] Create sacred-core-claude-cli/
- [x] Document architecture
- [x] Document implementation
- [ ] Update main README

---

## Obsolete Code

The following code is now OBSOLETE and can be archived:

```yaml
lgp/claude_code/session_manager.py:
  reason: "MCP bridge no longer needed"
  replacement: "Direct subprocess call"

lgp/claude_code/node_factory.py:
  reason: "Complex MCP parsing replaced by JSON"
  replacement: "ClaudeCodeProvider._parse_response()"

research/R15_*.md:
  reason: "MCP bridge architecture abandoned"
  replacement: "sacred-core-claude-cli/"
```

---

## Decision Log

### 2025-11-26: Transport Simplification
```yaml
decision: "Use subprocess + JSON instead of MCP bridge"
rationale:
  - CLI provides JSON output natively
  - MCP bridge adds 300+ lines of complexity
  - No functional benefit from MCP layer
  - Same capabilities with simpler code
```

### 2025-11-26: Interface Parity
```yaml
decision: "Implement ClaudeCodeProvider as LLMProvider"
rationale:
  - Same interface as OllamaProvider
  - Same state_updates contract
  - Same @observe pattern
  - Interchangeable in workflows
```

### 2025-11-26: Stateless Default
```yaml
decision: "Make session continuity optional"
rationale:
  - LangGraph manages state, not providers
  - Simpler mental model
  - Session passed via state dict when needed
  - No initialization required
```

---

## Next Steps

### Implementation Phase (COMPLETE)
1. ~~Copy `03-implementation.md` code to `lgp/agents/claude_code_provider.py`~~
2. ~~Update factory with new provider~~
3. ~~Write tests~~
4. ~~Validate with live CLI~~

### Cleanup Phase (OPTIONAL)
1. Archive `lgp/claude_code/` directory (old MCP-based code)
2. Archive `research/R15_*.md` files (old MCP research)
3. Update `sacred-core-complete-worker/04-current-state.md`

### Integration Phase (NEXT)
1. Use ClaudeCodeProvider in actual workflows
2. Test multi-agent scenarios with different repositories
3. Benchmark against Ollama provider for comparison

---

## Archive Notice

This file will be updated when:
- Implementation complete
- Tests passing
- Integration validated

Post-completion: Merge findings into `sacred-core-complete-worker/` as appropriate.
