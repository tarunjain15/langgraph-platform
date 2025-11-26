# R15: Implementation Checklist

**Goal:** Integrate Claude Code execution into Worker Marketplace (bridge R14 → real execution)

**Approach:** Phase 2 (MCP Bridge) - Use MCPSessionManager pattern from lgp/claude_code/

---

## Prerequisites

### Environment Setup
- [ ] Claude Code container running
  ```bash
  docker ps | grep claude-mcp
  # Should show: claude-mcp container running
  ```

- [ ] Worker Marketplace MCP Server working
  ```bash
  PYTHONPATH=. python3 workers/mcp_client_cli.py
  # Should connect and list 4 tools
  ```

- [ ] All R14 tests passing
  ```bash
  PYTHONPATH=. python3 workers/test_mcp_integration.py      # 13/13 ✅
  PYTHONPATH=. python3 workers/test_mcp_client_e2e.py       # E2E ✅
  ```

---

## Phase 2: MCP Bridge Integration

### Step 1: Update ClaudeCodeWorker Class

**File:** `workers/claude_code_worker.py`

#### 1.1 Add MCPSessionManager Import
```python
# At top of file
from lgp.claude_code import MCPSessionManager
import re
from typing import Tuple
```

#### 1.2 Add MCP Manager to `__init__`
```python
def __init__(
    self,
    definition: Dict[str, Any],
    user_journey_id: str,
    workspace_path: str,
    isolation_level: str = "process",
    container_id: Optional[str] = None
):
    # ... existing code ...

    # ADD: MCP session manager for Claude Code
    self.mcp_manager = MCPSessionManager(container_name="claude-mcp")
    self.session_id = None  # For session continuity
```

#### 1.3 Add Action-to-Task Converter
```python
def _action_to_task(self, action: Dict[str, Any]) -> str:
    """
    Convert worker action dict to Claude Code task string.

    Examples:
        {"type": "read", "target": "README.md"} → "Read README.md"
        {"type": "write", "target": "notes.txt", "content": "..."} → "Write to notes.txt: ..."
        {"type": "search", "query": "TODO"} → "Search for TODO"
    """
    action_type = action.get("type", "unknown")
    target = action.get("target", "")

    if action_type == "read":
        return f"Read {target}"
    elif action_type == "write":
        content_preview = action.get("content", "")[:50]
        return f"Write to {target}: {content_preview}..."
    elif action_type == "search":
        query = action.get("query", target)
        return f"Search for {query}"
    elif action_type == "list":
        return f"List files in {target or 'workspace'}"
    else:
        return f"Execute {action_type} on {target}"
```

#### 1.4 Add Result Parser
```python
def _parse_mesh_result(self, result) -> Tuple[str, str]:
    """
    Parse mesh_execute result for output and session_id.

    mesh_execute returns:
        Session ID: <uuid>

        <output content>

        --- Execution Metadata ---
        ...
    """
    output = None
    session_id = None

    if result.content:
        for item in result.content:
            if hasattr(item, 'text'):
                text = item.text

                # Extract session ID
                session_match = re.search(r'Session ID: ([a-f0-9-]+)', text)
                if session_match:
                    session_id = session_match.group(1)

                # Extract output (between session ID and metadata)
                output_match = re.search(
                    r'Session ID: [a-f0-9-]+\n\n(.+?)(?:\n\n--- Execution Metadata ---|$)',
                    text,
                    re.DOTALL
                )
                if output_match:
                    output = output_match.group(1).strip()

    return output or "", session_id or ""
```

#### 1.5 Replace execute() Implementation (lines 235-280)

**BEFORE (Mock Data):**
```python
else:
    # Process/thread isolation (placeholder)
    actual_outcome = {
        "executed": True,
        "action_type": action.get("type", "unknown"),
        "workspace": self.workspace_path,
        "user_journey_id": self.user_journey_id,
        "isolation": self.isolation_level
    }
```

**AFTER (Real Claude Code Execution):**
```python
else:
    # Process isolation: Execute via Claude Code MCP

    # Convert action to task
    task = self._action_to_task(action)

    try:
        # Execute via mesh_execute (Claude Code MCP protocol)
        async with self.mcp_manager.create_session() as session:
            invoke_args = {
                'repository': self.workspace_path,
                'task': task,
                'timeout': 60000  # 60 seconds
            }

            # Resume existing session if available
            if self.session_id:
                invoke_args['session_id'] = self.session_id

            # Call mesh_execute via MCP protocol
            result = await session.call_tool('mesh_execute', invoke_args)

            # Parse response
            output, new_session_id = self._parse_mesh_result(result)

            # Save session ID for continuity
            if new_session_id:
                self.session_id = new_session_id

            actual_outcome = {
                "executed": True,
                "output": output,
                "session_id": self.session_id,
                "action_type": action.get("type", "unknown"),
                "workspace": self.workspace_path,
                "user_journey_id": self.user_journey_id,
                "isolation": self.isolation_level
            }

    except Exception as e:
        # Handle Claude Code invocation errors
        actual_outcome = {
            "executed": False,
            "error": str(e),
            "action_type": action.get("type", "unknown"),
            "workspace": self.workspace_path,
            "user_journey_id": self.user_journey_id,
            "isolation": self.isolation_level
        }
```

**Checklist:**
- [ ] Add imports (MCPSessionManager, re, Tuple)
- [ ] Add mcp_manager to `__init__`
- [ ] Add session_id attribute
- [ ] Implement `_action_to_task()`
- [ ] Implement `_parse_mesh_result()`
- [ ] Replace execute() else block with MCP invocation

---

### Step 2: Update Worker State Retrieval

**File:** `workers/claude_code_worker.py`

#### 2.1 Add Session ID to State
```python
def get_state(self) -> Dict[str, Any]:
    """Get current worker state"""
    return {
        "user_journey_id": self.user_journey_id,
        "workspace_path": self.workspace_path,
        "isolation_level": self.isolation_level,
        "container_id": self.container_id,
        "definition": self.definition,
        "session_id": self.session_id,  # ADD THIS
        "action_count": self.action_count
    }
```

**Checklist:**
- [ ] Add session_id to get_state() return dict

---

### Step 3: Test Integration

#### 3.1 Update Unit Tests

**File:** `workers/test_claude_code_worker_integration.py` (create if doesn't exist)

```python
#!/usr/bin/env python3
"""
Integration tests for ClaudeCodeWorker with real Claude Code execution.
"""

import asyncio
import pytest
from pathlib import Path
from workers.claude_code_worker import ClaudeCodeWorker
from workers.definitions.loader import load_worker_definition


@pytest.mark.asyncio
async def test_execute_with_claude_code():
    """Test worker executes via Claude Code (not mock data)"""

    # Load worker definition
    definition_path = Path(__file__).parent / "definitions" / "production" / "filesystem_research_v1.yaml"
    definition = load_worker_definition(definition_path)

    # Create worker
    worker = ClaudeCodeWorker(
        definition=definition,
        user_journey_id="test_journey",
        workspace_path="/tmp/workers/test/test_journey",
        isolation_level="process"
    )

    # Execute action
    action = {"type": "read", "target": "README.md"}
    result = await worker.execute(action)

    # Verify real execution (not mock)
    assert result["executed"] == True
    assert "session_id" in result  # Proves Claude Code invocation
    assert result["session_id"] != ""
    assert "output" in result


@pytest.mark.asyncio
async def test_session_continuity():
    """Test session_id persists across executions"""

    definition_path = Path(__file__).parent / "definitions" / "production" / "filesystem_research_v1.yaml"
    definition = load_worker_definition(definition_path)

    worker = ClaudeCodeWorker(
        definition=definition,
        user_journey_id="test_journey_2",
        workspace_path="/tmp/workers/test/test_journey_2",
        isolation_level="process"
    )

    # First execution
    result1 = await worker.execute({"type": "list", "target": "."})
    session_id_1 = result1.get("session_id")

    # Second execution (should reuse session)
    result2 = await worker.execute({"type": "list", "target": "."})
    session_id_2 = result2.get("session_id")

    # Verify session continuity
    assert session_id_1 == session_id_2
    assert session_id_1 != ""


@pytest.mark.asyncio
async def test_constraint_enforcement_with_claude_code():
    """Test constraints enforced BEFORE Claude Code invocation"""

    definition_path = Path(__file__).parent / "definitions" / "production" / "filesystem_research_v1.yaml"
    definition = load_worker_definition(definition_path)

    worker = ClaudeCodeWorker(
        definition=definition,
        user_journey_id="test_journey_3",
        workspace_path="/tmp/workers/test/test_journey_3",
        isolation_level="process"
    )

    # Violating action (large file write)
    action = {
        "type": "write",
        "target": "large_file.txt",
        "content": "x" * 2_000_000  # 2MB (exceeds 1MB limit)
    }

    result = await worker.execute(action)

    # Verify action was rejected (no Claude Code invocation)
    assert result["executed"] == False
    assert "violations" in result
    assert len(result["violations"]) > 0
    assert "session_id" not in result  # No Claude Code call happened


if __name__ == "__main__":
    asyncio.run(test_execute_with_claude_code())
    print("✓ test_execute_with_claude_code passed")

    asyncio.run(test_session_continuity())
    print("✓ test_session_continuity passed")

    asyncio.run(test_constraint_enforcement_with_claude_code())
    print("✓ test_constraint_enforcement_with_claude_code passed")
```

**Checklist:**
- [ ] Create test file
- [ ] Run test: `PYTHONPATH=. python3 workers/test_claude_code_worker_integration.py`
- [ ] Verify all 3 tests pass

---

#### 3.2 Update E2E MCP Test

**File:** `workers/test_mcp_client_e2e.py`

**Update Step 5 assertion (line 149):**

**BEFORE:**
```python
assert "Action completed successfully" in exec_content, \
    f"Execution failed: {exec_content}"
```

**AFTER:**
```python
assert "Action completed successfully" in exec_content, \
    f"Execution failed: {exec_content}"

# VERIFY: Real Claude Code execution (session_id present)
assert "Session ID:" in exec_content or "session_id" in exec_content, \
    "No session_id in response - Claude Code not actually invoked!"
```

**Checklist:**
- [ ] Add session_id verification to E2E test
- [ ] Run test: `PYTHONPATH=. python3 workers/test_mcp_client_e2e.py`
- [ ] Verify test passes and session_id is present

---

#### 3.3 Test with Interactive CLI

**Manual Test:**
```bash
PYTHONPATH=. python3 workers/mcp_client_cli.py
```

**Commands:**
```
mcp> spawn test_journey
# Verify: Worker spawned successfully

mcp> execute test_journey
# Choose option 1 (Read README.md)
# Verify: "Action completed successfully"
# Verify: "Session ID: <uuid>" appears in output

mcp> execute test_journey
# Choose option 1 again
# Verify: Same session ID (continuity)

mcp> execute test_journey
# Choose option 2 (Large file - constraint violation)
# Verify: "Constraint violation detected"
# Verify: NO session ID (action rejected before Claude Code)

mcp> state test_journey
# Verify: session_id field present

mcp> kill test_journey
# Verify: Worker terminated

mcp> exit
```

**Checklist:**
- [ ] Spawn worker succeeds
- [ ] Execute valid action returns session_id
- [ ] Session ID persists across executions
- [ ] Constraint violation prevents Claude Code invocation
- [ ] State shows session_id
- [ ] Kill worker succeeds

---

### Step 4: Create Production Worker Definition

**File:** `workers/definitions/production/claude_code_assistant_v1.yaml`

```yaml
worker_id: claude_code_assistant_v1

identity:
  name: "Claude Code Assistant"
  system_prompt: |
    You are a Claude Code assistant with access to filesystem tools.
    Execute tasks in isolated workspace with constraint enforcement.

    Available actions:
    - read: Read file contents
    - write: Write file contents
    - search: Search for patterns
    - list: List directory contents

runtime:
  container: "claude-mcp"  # Uses existing claude-mcp container
  workspace_template: "/tmp/workers/claude_code/{user_journey_id}"
  tools: ["mesh_execute"]
  session_persistence: true

constraints:
  - constraint_id: "workspace_isolation"
    witness: "verify_workspace_path"
    value: "/tmp/workers/claude_code/{user_journey_id}"
    feedback: "alert_dashboard"

  - constraint_id: "max_file_size"
    witness: "verify_file_size_within_limit"
    value: "1MB"
    feedback: "alert_dashboard"

  - constraint_id: "max_session_duration"
    witness: "verify_execution_time"
    value: "300s"  # 5 minutes
    feedback: "alert_dashboard"

  - constraint_id: "readonly_system_files"
    witness: "verify_no_system_access"
    value: "blocked"
    feedback: "alert_dashboard"

trust_level: "monitored"
```

**Checklist:**
- [ ] Create worker definition file
- [ ] Test loading:
  ```python
  from workers.definitions.loader import load_worker_definition
  definition = load_worker_definition("workers/definitions/production/claude_code_assistant_v1.yaml")
  print(definition)
  ```
- [ ] Verify definition loads without errors

---

### Step 5: Validation Checklist

#### Code Changes
- [ ] MCPSessionManager imported
- [ ] mcp_manager added to worker __init__
- [ ] session_id attribute added
- [ ] _action_to_task() implemented
- [ ] _parse_mesh_result() implemented
- [ ] execute() updated to use mesh_execute
- [ ] session_id added to get_state()

#### Tests
- [ ] Unit tests created and passing
- [ ] E2E test updated and passing
- [ ] Interactive CLI manual test successful
- [ ] All existing R14 tests still passing

#### Worker Definition
- [ ] claude_code_assistant_v1.yaml created
- [ ] Definition loads successfully
- [ ] Constraints properly configured

#### Integration
- [ ] Claude Code container running
- [ ] Worker spawns successfully
- [ ] Actions execute via Claude Code
- [ ] Session continuity works
- [ ] Constraints enforced before execution
- [ ] No regressions in existing functionality

---

## Success Criteria

### ✅ Must Pass
1. All R14 tests pass (no regressions)
2. Worker executes via Claude Code (not mock data)
3. Session ID persists across executions
4. Constraints enforced before Claude Code invocation
5. Interactive CLI works with real execution

### ✅ Must Verify
1. `session_id` present in execution results
2. Same `session_id` across multiple execute() calls
3. Constraint violations prevent Claude Code invocation
4. Error handling works (Claude Code failures graceful)
5. Worker state includes session_id

### ✅ Must Document
1. Code changes in git commit
2. Test results in CI/CD
3. Integration pattern in architecture docs
4. Migration guide for existing workers

---

## Rollback Plan

If integration fails:

1. **Revert execute() changes**
   ```bash
   git checkout HEAD -- workers/claude_code_worker.py
   ```

2. **Verify R14 tests still pass**
   ```bash
   PYTHONPATH=. python3 workers/test_mcp_integration.py
   PYTHONPATH=. python3 workers/test_mcp_client_e2e.py
   ```

3. **Document issues encountered**
   - What failed?
   - Error messages?
   - Environment issues?

4. **Re-plan approach**
   - Consider Phase 1 (Direct Integration) instead?
   - Missing dependencies?
   - Configuration issues?

---

## Next Phase: LangGraph Integration

After Phase 2 complete and validated:

1. **Create workflow using workers as nodes**
   - Use `create_claude_code_node()` pattern
   - Connect to Worker Marketplace MCP Server
   - Validate session continuity via checkpointer

2. **Test multi-agent workflow**
   - Researcher → Writer → Reviewer
   - Each agent as worker instance
   - Session state persistence

3. **Production deployment**
   - Staging environment validation
   - Performance monitoring
   - Cost tracking
   - Production rollout

---

## Estimated Timeline

- **Step 1 (Code Changes):** 2 hours
- **Step 2 (State Update):** 30 minutes
- **Step 3 (Testing):** 2 hours
- **Step 4 (Worker Definition):** 30 minutes
- **Step 5 (Validation):** 1 hour

**Total:** ~6 hours for complete Phase 2 integration

---

## Key Files Modified

1. `workers/claude_code_worker.py` - Main integration changes
2. `workers/test_claude_code_worker_integration.py` - New test file
3. `workers/test_mcp_client_e2e.py` - Updated E2E test
4. `workers/definitions/production/claude_code_assistant_v1.yaml` - New definition

**Files to Review:**
- `lgp/claude_code/session_manager.py` - Reference pattern
- `lgp/claude_code/node_factory.py` - LangGraph integration pattern
- `workers/isolation/container.py` - Container execution pattern

---

## Questions & Troubleshooting

### Q: Claude Code container not running?
```bash
docker run -d \
  --name claude-mcp \
  -v /tmp/workers:/workspace \
  claude-code:latest
```

### Q: MCP session connection fails?
- Verify container name matches: `claude-mcp`
- Check container logs: `docker logs claude-mcp`
- Verify mesh-mcp server running in container

### Q: Session ID not persisting?
- Check `_parse_mesh_result()` regex
- Verify mesh_execute returns session_id
- Add debug logging to see raw result

### Q: Constraint violations not blocking?
- Verify `void()` called before execute()
- Check constraint definitions in YAML
- Add logging to constraint checks

### Q: Tests fail with import errors?
```bash
export PYTHONPATH=.
pip install mcp
pip install docker
```

---

**Ready to implement?** Start with Step 1.1 (Add imports).
