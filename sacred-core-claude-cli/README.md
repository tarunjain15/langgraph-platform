# Sacred Core: Claude Code CLI Integration

## The Core Realization

```
Claude Code CLI = Just another LLMProvider
Same interface as Ollama. Same interface as OpenAI.
The transport is subprocess + JSON. The contract is identical.
```

## Quick Summary

| Aspect | Before | After |
|--------|--------|-------|
| Transport | MCP Bridge (~400 lines) | subprocess.run() (~80 lines) |
| Parsing | Regex extraction | json.loads() |
| Session ID | Parse from text | Native JSON field |
| Cost | External calculation | Native `total_cost_usd` |
| Interface | Custom | Same as OllamaProvider |

## Files

| File | Purpose |
|------|---------|
| `01-the-project.md` | Core realization, architecture, three primitives |
| `02-the-discipline.md` | Constraints, patterns, anti-patterns |
| `03-implementation.md` | Complete ClaudeCodeProvider code |
| `04-current-state.md` | Implementation status, next steps |

## The Three Primitives

```
1. Claude API (Thin-Client)
   - LLM completions only
   - No tools
   - Langfuse native via langfuse.openai.OpenAI

2. Claude Code CLI (Agent Runtime)
   - Full agent with tools
   - subprocess + JSON
   - Langfuse native via @observe

3. Claude Code Container (Isolated Agent)
   - Same as CLI
   - Docker isolation
   - Multi-tenant safe
```

## Key Decision

**Use subprocess + JSON, NOT MCP bridge.**

```python
# CORRECT: Simple, native
result = subprocess.run(['claude', '-p', prompt, '--output-format', 'json'], ...)
response = json.loads(result.stdout)
session_id = response["session_id"]

# WRONG: Complex, unnecessary
mcp_session.call_tool('mesh_execute', {...})
session_id = re.search(r'Session ID: ([a-f0-9-]+)', text).group(1)
```

## Implementation Status

- [x] Architecture documented
- [x] Constraints defined
- [x] Code drafted
- [x] Implementation in `lgp/agents/claude_code_provider.py`
- [x] Factory updated in `lgp/agents/factory.py`
- [x] Tests written in `scripts/test_claude_code_provider.py`
- [x] Integration validated (live test passing)

## References

- [Claude Code Headless Docs](https://code.claude.com/docs/en/headless)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
- [workflow-factory examples](../../../workflow-factory/examples-collection/)
