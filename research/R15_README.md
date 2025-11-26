# R15: Claude Code Integration - Research Summary

**Status:** Architecture Complete | Ready for Implementation
**Created:** 2025-11-25
**Dependencies:** R13 (Worker Marketplace), R14 (MCP Integration)

---

## TL;DR

**Problem:** Worker Marketplace MCP server (R14) has all infrastructure working but doesn't actually invoke Claude Code. The `execute()` method returns mock data.

**Solution:** Integrate Claude Code via MCP protocol using existing `MCPSessionManager` pattern from `lgp/claude_code/`.

**Impact:** Enables real Claude Code execution in workers with:
- ✅ Session continuity (session_id persistence)
- ✅ Constraint enforcement (void() before execute)
- ✅ Workspace isolation (per user journey)
- ✅ MCP protocol end-to-end (client → server → Claude Code)

---

## Quick Links

### 📄 Documentation
1. **[R15_CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md](./R15_CLAUDE_CODE_INTEGRATION_ARCHITECTURE.md)**
   - Full architecture overview
   - Three-role model (MCP Server, MCP Client, LangGraph Node)
   - Integration approaches (Phase 1-3)
   - Testing strategy
   - Migration plan

2. **[R15_INTEGRATION_DIAGRAM.md](./R15_INTEGRATION_DIAGRAM.md)**
   - Visual architecture diagrams
   - Data flow charts
   - Integration flows (3 scenarios)
   - Constraint enforcement visualization

3. **[R15_IMPLEMENTATION_CHECKLIST.md](./R15_IMPLEMENTATION_CHECKLIST.md)**
   - Step-by-step implementation guide
   - Code changes (copy-paste ready)
   - Test cases
   - Validation checklist
   - Rollback plan

---

## Key Insights

### The Three-Role Model

Claude Code operates in **three distinct roles**:

```
┌─────────────────────────────────────────┐
│  CLAUDE CODE CONTAINERIZED INSTANCE     │
├─────────────────────────────────────────┤
│  Role 1: MCP Server                     │
│  → Exposes: mesh_execute tool           │
│  → Workers call Claude Code via MCP     │
│                                          │
│  Role 2: MCP Client                     │
│  → Calls: Worker Marketplace tools      │
│  → Claude Code uses workers recursively │
│                                          │
│  Role 3: LangGraph Node                 │
│  → Integration: create_claude_code_node()│
│  → State: session_id via checkpointer   │
└─────────────────────────────────────────┘
```

### The Integration Gap

**Current State (R14):**
```python
# workers/claude_code_worker.py:258-266
else:
    # Process/thread isolation (placeholder)
    actual_outcome = {
        "executed": True,
        "action_type": action.get("type", "unknown"),
        "workspace": self.workspace_path,
        "user_journey_id": self.user_journey_id,
        "isolation": self.isolation_level
    }
    # ❌ This is MOCK DATA - no Claude Code invocation!
```

**Target State (R15 Phase 2):**
```python
else:
    # Execute via Claude Code MCP protocol
    task = self._action_to_task(action)

    async with self.mcp_manager.create_session() as session:
        result = await session.call_tool('mesh_execute', {
            'repository': self.workspace_path,
            'task': task,
            'session_id': self.session_id  # Session continuity
        })

        output, new_session_id = self._parse_mesh_result(result)
        self.session_id = new_session_id

        actual_outcome = {
            "executed": True,
            "output": output,
            "session_id": self.session_id,
            # ... metadata ...
        }
    # ✅ REAL Claude Code execution with session continuity!
```

---

## Architecture Summary

### Layer 1: External MCP Client → Worker Marketplace

```
Claude Desktop/VS Code/LangGraph
    ↓ (stdio MCP protocol)
Worker Marketplace MCP Server (workers/mcp_server.py)
    ↓ (4 tools: spawn_worker, execute_in_worker, get_worker_state, kill_worker)
WorkerFactory.spawn()
    ↓ (loads YAML definition)
ClaudeCodeWorker instance
    ↓ (void() → constraint check)
    ↓ (execute() → INVOKE CLAUDE CODE)
MCPSessionManager → claude-mcp container
    ↓ (mesh_execute via MCP)
Claude Code execution
    ↓ (returns session_id + output)
Result via MCP protocol
```

### Layer 2: Constraint Enforcement

```
execute_in_worker(action)
    ↓
void(action)  # Pre-execution constraint check
    ↓
violations = [
    check_file_size(action),
    check_workspace_isolation(action),
    check_readonly_filesystem(action),
    ...
]
    ↓
if violations:
    return constraint_violation_response
    # ⚠️ SHORT CIRCUIT - No Claude Code invocation!
    # Cost saved, constraint enforced
else:
    invoke_claude_code_via_mcp(action)
    # ✅ Constraints passed, proceed with execution
```

### Layer 3: Session Continuity

```
First execute():
    session_id = None
    ↓
    mesh_execute(task, session_id=None)
    ↓
    Claude Code creates NEW session
    ↓
    Returns: session_id = "abc-123"
    ↓
    worker.session_id = "abc-123"

Second execute():
    session_id = "abc-123"
    ↓
    mesh_execute(task, session_id="abc-123")
    ↓
    Claude Code RESUMES existing session
    ↓
    Returns: session_id = "abc-123"
    ↓
    worker.session_id = "abc-123"  # Continuity maintained
```

---

## Implementation Approach

### Recommended: Phase 2 (MCP Bridge)

**Why Phase 2?**
- ✅ Uses proven pattern (`lgp/claude_code/session_manager.py`)
- ✅ Enables session continuity (session_id persistence)
- ✅ Maintains all R13/R14 guarantees
- ✅ Production-ready architecture
- ✅ Minimal code changes (~150 lines)

**Core Changes:**
1. Add `MCPSessionManager` to `ClaudeCodeWorker.__init__()`
2. Replace mock data in `execute()` with `mesh_execute` call
3. Add session_id parsing and persistence
4. Update tests to verify real execution

**Estimated Time:** ~6 hours

---

## File Changes Summary

### Modified Files
1. **workers/claude_code_worker.py** (~150 lines changed)
   - Add MCPSessionManager
   - Implement `_action_to_task()`
   - Implement `_parse_mesh_result()`
   - Replace execute() mock data with mesh_execute

2. **workers/test_mcp_client_e2e.py** (~10 lines changed)
   - Add session_id verification

### New Files
1. **workers/test_claude_code_worker_integration.py**
   - Unit tests for Claude Code execution
   - Session continuity tests
   - Constraint enforcement tests

2. **workers/definitions/production/claude_code_assistant_v1.yaml**
   - Production worker definition using Claude Code runtime

---

## Testing Strategy

### Unit Tests (workers/test_claude_code_worker_integration.py)
```python
test_execute_with_claude_code()
    # Verify real execution (not mock)
    assert result["session_id"] != ""

test_session_continuity()
    # Verify session_id persists
    assert session_id_1 == session_id_2

test_constraint_enforcement_with_claude_code()
    # Verify constraints block execution
    assert "violations" in result
    assert "session_id" not in result  # No Claude Code call
```

### Integration Tests (workers/test_mcp_client_e2e.py)
```python
# E2E MCP protocol test
async with stdio_client() as (read, write):
    async with ClientSession(read, write) as session:
        # Spawn worker
        spawn_result = await session.call_tool("spawn_worker", {...})

        # Execute action
        exec_result = await session.call_tool("execute_in_worker", {...})

        # Verify real Claude Code execution
        assert "Session ID:" in exec_result.content[0].text
```

### Manual Test (workers/mcp_client_cli.py)
```bash
PYTHONPATH=. python3 workers/mcp_client_cli.py

mcp> spawn test_journey
mcp> execute test_journey
# Choose option 1 (Read README.md)
# ✅ Verify: "Session ID: abc-123" in output

mcp> execute test_journey
# Choose option 1 again
# ✅ Verify: Same session ID (continuity)

mcp> execute test_journey
# Choose option 2 (Large file - violation)
# ✅ Verify: "Constraint violation detected" (no session ID)
```

---

## Success Metrics

### Technical Validation
- ✅ All R14 tests pass (no regressions)
- ✅ New integration tests pass (Claude Code invocation)
- ✅ Session continuity works (session_id persistence)
- ✅ Constraint enforcement works (void() before execute())
- ✅ Interactive MCP client works with real execution

### Observable Outcomes
1. **Session ID Present:** Every successful execute() returns session_id
2. **Session Continuity:** Same session_id across multiple execute() calls
3. **Constraint Blocking:** Violations prevent Claude Code invocation (no session_id)
4. **Error Handling:** Claude Code failures return graceful error (not exception)
5. **State Persistence:** get_worker_state() includes session_id

---

## Next Steps

### Immediate (R15 Implementation)
1. Review architecture documents
2. Implement Phase 2 changes (workers/claude_code_worker.py)
3. Write integration tests
4. Create claude_code_assistant_v1.yaml worker definition
5. Validate with interactive CLI
6. Run full test suite

### Future (Post-R15)
1. **LangGraph Integration** - Use workers as LangGraph nodes
2. **Recursive Composition** - Claude Code uses Worker Marketplace
3. **Production Deployment** - Staging → Production rollout
4. **Monitoring** - Langfuse observability, cost tracking
5. **Optimization** - Performance tuning, resource usage

---

## Key Decisions

### ✅ Use MCPSessionManager Pattern
**Rationale:** Proven pattern from lgp/claude_code/, enables session continuity, production-ready

### ✅ Phase 2 (MCP Bridge) over Phase 1 (Direct Integration)
**Rationale:** Session continuity > simplicity, long-term flexibility, maintains all guarantees

### ✅ Session ID in Worker State
**Rationale:** Enables continuity, observable in state queries, debuggable

### ✅ Constraint Check Before Claude Code
**Rationale:** Cost savings, security guarantee, early feedback

---

## Questions Answered

**Q: Does this replace R13/R14?**
A: No, it builds on top. R13/R14 infrastructure stays intact.

**Q: Do all workers need Claude Code?**
A: No, workers can opt-in via runtime.container in YAML definition.

**Q: How does session continuity work?**
A: session_id returned by mesh_execute, stored in worker, passed to next execution.

**Q: What if Claude Code fails?**
A: Error returned in output, not thrown as exception (graceful degradation).

**Q: Can Claude Code use Worker Marketplace?**
A: Yes! That's Phase 3 (Marketplace Recursion). Claude Code as MCP client.

**Q: How to test without claude-mcp container?**
A: Mock MCPSessionManager in tests, or use existing R14 tests (they still pass).

---

## References

### Existing Code Patterns
- `lgp/claude_code/session_manager.py` - MCP session management
- `lgp/claude_code/node_factory.py` - LangGraph node creation
- `workers/isolation/container.py` - Docker container isolation
- `workers/mcp_server.py` - MCP server exposing workers

### Documentation
- `workers/MCP_CLIENT_GUIDE.md` - Interactive client usage
- `sacred-core-complete-worker/01-the-project.md` - Worker marketplace architecture
- `templates/README.md` - Workflow template patterns

### Tests
- `workers/test_mcp_integration.py` - MCP tool registration (13/13 ✅)
- `workers/test_mcp_client_e2e.py` - E2E MCP protocol (✅)
- `workers/mcp_client_cli.py` - Interactive testing client

---

## Contact & Feedback

**Research Lead:** Claude Code Integration Team
**Phase:** R15 (Architecture Complete)
**Next Milestone:** Phase 2 Implementation
**Estimated Completion:** 1 week

**Ready to implement?** Start with [R15_IMPLEMENTATION_CHECKLIST.md](./R15_IMPLEMENTATION_CHECKLIST.md)
