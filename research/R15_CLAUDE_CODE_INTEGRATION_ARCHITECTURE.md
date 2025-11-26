# R15: Claude Code Integration Architecture

**Research ID:** R15
**Created:** 2025-11-25
**Status:** Architecture & Implementation Plan
**Dependencies:** R13 (Worker Marketplace), R14 (MCP Integration)

---

## Problem Statement

**Current Gap:** Worker Marketplace MCP server (R14) has all infrastructure working but doesn't actually invoke Claude Code. The `execute()` method returns mock data instead of calling real Claude Code instances.

**User Observation:** "Claude-code is being accessed correctly in the tools in the interactive mcp client? ... Yes. But it is all over the place right now. Need clear articulation, architecture and plan for integrating claude-code containerised instance already coded in claude-mesh repo."

**Core Insight:** The same Claude Code instance can operate in **three roles**:
1. **MCP Client** - Calling other MCP servers (tools)
2. **MCP Server** - Exposing its own capabilities
3. **LangGraph Node** - Integrated into workflows

---

## Architecture Overview

### The Three-Role Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE INSTANCE                          │
│                  (Containerized via Docker)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Role 1: MCP Server                                             │
│  ┌────────────────────────────────────────────┐                 │
│  │ Exposes: mesh_execute tool                 │                 │
│  │ Accepts: stdio transport                   │                 │
│  │ Returns: Session ID + Output               │                 │
│  └────────────────────────────────────────────┘                 │
│                       ↕                                          │
│  Role 2: MCP Client                                             │
│  ┌────────────────────────────────────────────┐                 │
│  │ Calls: External MCP servers                │                 │
│  │ Uses: Tools from marketplace               │                 │
│  │ Access: Database, Git, Filesystem, etc.    │                 │
│  └────────────────────────────────────────────┘                 │
│                       ↕                                          │
│  Role 3: LangGraph Node                                         │
│  ┌────────────────────────────────────────────┐                 │
│  │ Maintains: Session continuity (session_id) │                 │
│  │ Isolated: Repository workspace per role    │                 │
│  │ Observed: Full Langfuse traces             │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current State Analysis

### ✅ What Works (R13 + R14)

#### 1. **MCP Server Infrastructure** (workers/mcp_server.py)
```python
# MCP server exposing 4 tools via stdio transport
@server.list_tools()  # Lists: spawn_worker, execute_in_worker, get_worker_state, kill_worker
@server.call_tool()   # Handles tool invocations

# Tests passing:
- 13/13 integration tests ✅
- E2E MCP protocol test ✅
- Interactive CLI working ✅
```

#### 2. **Worker Definition System** (workers/definitions/)
```yaml
# Production definition: filesystem_research_v1.yaml
worker_id: filesystem_research_v1
identity:
  name: "Filesystem Research Assistant"
  system_prompt: "You are a Filesystem Research Assistant..."

runtime:
  container: "python:3.11-slim"
  workspace_template: "/tmp/workers/research/{user_journey_id}"
  tools: ["read", "search", "list"]

constraints:
  - constraint_id: "max_file_size"
    witness: "verify_file_size_within_limit"
    value: "1MB"
    feedback: "alert_dashboard"
```

#### 3. **Journey Isolation** (workers/isolation/container.py)
```python
# Docker-based isolation per user journey
- Spawn container: user_journey_id → dedicated container
- Bind mount: workspace volume (persistent state)
- Network isolation: bridge mode
- Read-only root filesystem
```

#### 4. **Constraint Enforcement** (workers/claude_code_worker.py)
```python
# Automatic verification before execution
async def execute(action):
    violations = self.void(action)  # Pre-execution check
    if violations:
        return constraint_violation_response
    # Execute action...
```

#### 5. **Existing Claude Code Integration** (lgp/claude_code/)
```python
# MCPSessionManager - Connects to claude-mcp container
session_manager = MCPSessionManager(container_name="claude-mcp")

async with session_manager.create_session() as session:
    result = await session.call_tool('mesh_execute', {
        'repository': 'sample-app',
        'task': 'Research topic X',
        'session_id': '...'  # Session continuity
    })
```

---

### ❌ The Gap (What's Missing)

#### **workers/claude_code_worker.py:258-266**
```python
# Current execute() method (MOCK DATA)
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

**Problem:** No actual Claude Code invocation happens. The worker just returns mock data.

---

## Integration Architecture

### Layer 1: MCP Server → Worker Factory → Claude Code

```
External MCP Client (Claude Desktop, VS Code, LangGraph)
    ↓ (stdio transport)
Worker Marketplace MCP Server (workers/mcp_server.py)
    ↓ (call_tool: execute_in_worker)
WorkerFactory (workers/factory.py)
    ↓ (loads worker definition)
ClaudeCodeWorker instance (workers/claude_code_worker.py)
    ↓ (void() → constraint check)
    ↓ (execute() → INVOKE CLAUDE CODE HERE)
Claude Code Container Execution
    ↓ (docker exec → mesh_execute)
Claude Code Session
    ↓ (uses Worker Marketplace tools as MCP client)
Execution Result
    ↓ (returns via MCP protocol)
External MCP Client receives response
```

### Layer 2: Claude Code as Worker Tool User

```
Worker Marketplace MCP Server
    ↓ (exposes: spawn_worker, execute_in_worker, etc.)
Claude Code Container (role: MCP client)
    ↓ (connects to Worker Marketplace via stdio)
    ↓ (calls: spawn_worker → creates isolated worker)
    ↓ (calls: execute_in_worker → runs action with constraints)
Worker Instance Execution
    ↓ (filesystem read/write in isolated workspace)
    ↓ (automatic constraint verification)
Results returned to Claude Code
    ↓ (Claude Code continues task execution)
Final output returned to original caller
```

### Layer 3: LangGraph Node Integration

```
LangGraph Workflow
    ↓ (defines: researcher_node, writer_node, reviewer_node)
create_claude_code_node() factory
    ↓ (config: role_name, repository, timeout)
MCPSessionManager
    ↓ (creates session to claude-mcp container)
mesh_execute tool call
    ↓ (invokes Claude Code with session_id for continuity)
Claude Code executes in repository workspace
    ↓ (can use Worker Marketplace as MCP client)
    ↓ (constraint enforcement automatic)
Result with session_id
    ↓ (stored in state via checkpointer)
Next node execution resumes session
```

---

## Implementation Plan

### Phase 1: Direct Integration (Simplest Path)
**Goal:** Make workers actually call Claude Code CLI in container

**Changes Required:**
1. **Update `workers/claude_code_worker.py:execute()`**
   - Replace mock data with actual Claude Code invocation
   - Use `ContainerIsolation.exec_in_container()` pattern
   - Pass action as task to Claude Code CLI

2. **Add Claude Code Container Spawn**
   - Extend `ContainerIsolation.spawn_container()`
   - Use `claude-code:latest` image (or equivalent)
   - Mount workspace as `/workspace`

3. **Action → Task Translation**
   - Convert worker action dict to Claude Code task string
   - Example: `{"type": "read", "target": "README.md"}` → `"Read README.md"`

**Code Pattern:**
```python
# workers/claude_code_worker.py (updated execute method)
async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
    """Execute action in Claude Code container"""

    # 1. Constraint check (already works)
    violations = self.void(action)
    if violations:
        return self._violation_response(violations)

    # 2. Convert action to Claude Code task
    task = self._action_to_task(action)

    # 3. Execute in Claude Code container
    if self.isolation_level == "container" and self.container_id:
        result = await ContainerIsolation.exec_in_container(
            container_id=self.container_id,
            command=["claude", "execute", task],
            workdir="/workspace",
            timeout=60
        )

        return {
            "executed": result["exit_code"] == 0,
            "output": result["output"],
            "action_type": action.get("type"),
            "workspace": self.workspace_path,
            "user_journey_id": self.user_journey_id
        }
```

**Pros:**
- Minimal changes to existing code
- Uses already-working container isolation
- No new dependencies

**Cons:**
- Doesn't use MCP protocol for Claude Code (misses session continuity)
- No access to mesh_execute tool
- Limited to single-shot execution

---

### Phase 2: MCP Bridge Integration (Recommended)
**Goal:** Use MCPSessionManager to connect workers to Claude Code via MCP protocol

**Architecture:**
```
Worker execute() → MCPSessionManager → claude-mcp container → mesh_execute
```

**Changes Required:**

1. **Add MCP Session Manager to Workers**
```python
# workers/claude_code_worker.py
from lgp.claude_code import MCPSessionManager

class ClaudeCodeWorker:
    def __init__(self, ...):
        ...
        self.mcp_manager = MCPSessionManager(container_name="claude-mcp")
        self.session_id = None  # For session continuity
```

2. **Update execute() to use mesh_execute**
```python
async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
    # Constraint check
    violations = self.void(action)
    if violations:
        return self._violation_response(violations)

    # Convert action to task
    task = self._action_to_task(action)

    # Execute via MCP protocol
    async with self.mcp_manager.create_session() as session:
        invoke_args = {
            'repository': self.workspace_path,
            'task': task,
            'timeout': 60000
        }

        # Resume session if exists
        if self.session_id:
            invoke_args['session_id'] = self.session_id

        # Call mesh_execute
        result = await session.call_tool('mesh_execute', invoke_args)

        # Parse response
        output, session_id = self._parse_mesh_result(result)
        self.session_id = session_id  # Save for next execution

        return {
            "executed": True,
            "output": output,
            "session_id": session_id,
            "action_type": action.get("type"),
            "workspace": self.workspace_path
        }
```

3. **Add Response Parser**
```python
def _parse_mesh_result(self, result) -> Tuple[str, str]:
    """Parse mesh_execute result for output and session_id"""
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

                # Extract output
                output_match = re.search(
                    r'Session ID: [a-f0-9-]+\n\n(.+?)(?:\n\n--- Execution Metadata ---|$)',
                    text,
                    re.DOTALL
                )
                if output_match:
                    output = output_match.group(1).strip()

    return output, session_id
```

**Pros:**
- Uses proven MCP pattern from lgp/claude_code/
- Session continuity (session_id persistence)
- Claude Code can use Worker Marketplace as MCP client (recursive!)
- Full observability via Langfuse

**Cons:**
- Requires claude-mcp container running
- More complex setup
- Dependency on mesh-mcp server

---

### Phase 3: Marketplace Recursion (Advanced)
**Goal:** Enable Claude Code to use Worker Marketplace tools

**Architecture:**
```
Worker Marketplace MCP Server
    ↓ (spawns worker with Claude Code)
Claude Code Container
    ↓ (connects back to Worker Marketplace as MCP client)
    ↓ (calls: spawn_worker → creates nested worker)
Nested Worker Instance
    ↓ (executes in isolated workspace)
    ↓ (constraints enforced)
```

**Implementation:**
1. Configure Claude Code container with MCP client access to Worker Marketplace
2. Add Worker Marketplace server URL to Claude Code environment
3. Enable constraint verification for nested workers
4. Add recursion depth limits (prevent infinite nesting)

**Use Case:**
- Claude Code task: "Research Python best practices"
- Claude Code spawns: `filesystem_research_v1` worker
- Worker executes: Read files, search code, analyze patterns
- Worker returns: Research summary
- Claude Code continues: Write report

**Pros:**
- Self-composing architecture
- Claude Code can delegate to specialized workers
- Maximum flexibility

**Cons:**
- Complex recursion management
- Potential for confusing execution traces
- Higher resource usage

---

## Recommended Path Forward

### **Milestone 1: Phase 2 Implementation (MCP Bridge)**
**Rationale:**
- Builds on proven patterns (lgp/claude_code/)
- Enables session continuity
- Maintains all R13/R14 guarantees
- Production-ready architecture

**Validation:**
1. Update `workers/claude_code_worker.py:execute()` to use MCPSessionManager
2. Add session_id persistence to worker state
3. Test with existing MCP client CLI
4. Verify constraint enforcement still works
5. Validate session continuity across multiple execute() calls

**Success Criteria:**
- ✅ Interactive MCP client can spawn worker
- ✅ Worker executes tasks via Claude Code (real execution, not mock)
- ✅ Constraints enforced before execution
- ✅ Session ID persists across execute() calls
- ✅ All existing tests still pass

---

### **Milestone 2: Worker Definition for Claude Code**
**Goal:** Create production worker definition using Claude Code runtime

**New Definition:**
```yaml
# workers/definitions/production/claude_code_assistant_v1.yaml
worker_id: claude_code_assistant_v1

identity:
  name: "Claude Code Assistant"
  system_prompt: |
    You are a Claude Code assistant with access to filesystem tools.
    Execute tasks in isolated workspace with constraint enforcement.

runtime:
  container: "claude-mcp:latest"  # Claude Code container
  workspace_template: "/tmp/workers/claude_code/{user_journey_id}"
  tools: ["mesh_execute"]  # MCP tool for Claude Code invocation
  session_persistence: true

constraints:
  - constraint_id: "workspace_isolation"
    witness: "verify_workspace_path"
    value: "/tmp/workers/claude_code/{user_journey_id}"
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

**Validation:**
- Load definition via WorkerFactory
- Spawn worker for user journey
- Execute actions via mesh_execute
- Verify constraints enforced
- Confirm workspace isolation

---

### **Milestone 3: LangGraph Integration**
**Goal:** Use workers as LangGraph nodes

**Pattern:**
```python
# workflows/worker_research_pipeline.py
from lgp.claude_code import create_claude_code_node, MCPSessionManager

# Create MCP session manager
mcp_manager = MCPSessionManager(container_name="claude-mcp")

# Define worker as LangGraph node
researcher_config = {
    'role_name': 'filesystem_researcher',
    'repository': 'research_workspace',  # Maps to worker workspace
    'timeout': 120000
}

researcher_node = create_claude_code_node(researcher_config, mcp_manager)

# Add to LangGraph workflow
workflow.add_node("researcher", researcher_node)
```

**Integration Points:**
1. Worker spawned via MCP server
2. Node execution calls worker.execute()
3. Worker uses Claude Code via MCPSessionManager
4. Session ID persisted in LangGraph state
5. Constraints enforced automatically

---

## Testing Strategy

### Unit Tests
```python
# test_claude_code_worker_integration.py

async def test_execute_with_claude_code():
    """Test worker executes via Claude Code (not mock data)"""
    worker = ClaudeCodeWorker(...)

    action = {"type": "read", "target": "README.md"}
    result = await worker.execute(action)

    assert result["executed"] == True
    assert "session_id" in result  # Proves Claude Code invocation
    assert result["output"] != ""  # Real output, not mock

async def test_session_continuity():
    """Test session_id persists across executions"""
    worker = ClaudeCodeWorker(...)

    result1 = await worker.execute({"type": "read", "target": "file1.txt"})
    session_id_1 = result1["session_id"]

    result2 = await worker.execute({"type": "read", "target": "file2.txt"})
    session_id_2 = result2["session_id"]

    assert session_id_1 == session_id_2  # Same session

async def test_constraint_enforcement_with_claude_code():
    """Test constraints enforced before Claude Code invocation"""
    worker = ClaudeCodeWorker(...)

    # Violating action (large file write)
    action = {
        "type": "write",
        "target": "large_file.txt",
        "content": "x" * 2_000_000  # 2MB
    }

    result = await worker.execute(action)

    assert "Constraint violation detected" in result["output"]
    assert result["executed"] == False  # Action rejected
```

### Integration Tests
```python
# test_mcp_client_claude_code_e2e.py

async def test_mcp_client_spawns_claude_code_worker():
    """E2E test: MCP client → spawn worker → Claude Code execution"""

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Spawn worker
            spawn_result = await session.call_tool(
                "spawn_worker",
                arguments={
                    "worker_id": "claude_code_assistant_v1",
                    "journey_id": "e2e_test",
                    "isolation_level": "container"
                }
            )

            assert "Worker spawned successfully" in spawn_result.content[0].text

            # Execute via Claude Code
            exec_result = await session.call_tool(
                "execute_in_worker",
                arguments={
                    "journey_id": "e2e_test",
                    "action": {"type": "read", "target": "README.md"}
                }
            )

            content = exec_result.content[0].text
            assert "Action completed successfully" in content
            assert "Session ID:" in content  # Proves Claude Code invocation
```

---

## Dependency Requirements

### Container Infrastructure
```bash
# Claude Code container must be running
docker ps | grep claude-mcp

# If not running:
docker run -d \
  --name claude-mcp \
  -v /tmp/workers:/workspace \
  claude-code:latest
```

### Python Dependencies
```python
# Already installed (from R14)
- mcp
- docker

# May need:
- asyncio (stdlib)
- re (stdlib)
```

### Configuration
```bash
# Environment variables for Worker Marketplace
export CLAUDE_MCP_CONTAINER="claude-mcp"
export WORKER_WORKSPACE_ROOT="/tmp/workers"

# For Langfuse observability
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."
```

---

## Migration Strategy

### Backward Compatibility
- R13/R14 workers continue to work (no breaking changes)
- Mock data execution path remains for testing
- New workers opt-in to Claude Code runtime

### Rollout Phases
1. **Week 1:** Phase 2 implementation (MCP bridge)
2. **Week 2:** Worker definition for Claude Code + tests
3. **Week 3:** LangGraph integration + E2E validation
4. **Week 4:** Production deployment + monitoring

---

## Success Metrics

### Technical Validation
- ✅ All R13/R14 tests pass (no regressions)
- ✅ New integration tests pass (Claude Code invocation)
- ✅ Session continuity works (session_id persistence)
- ✅ Constraint enforcement works (void() before execute())
- ✅ Interactive MCP client works with real execution

### User Experience
- ✅ Worker spawns in <2 seconds
- ✅ Actions execute in <30 seconds (depends on task)
- ✅ Clear error messages on constraint violations
- ✅ Session state recoverable after restart

### Observability
- ✅ Langfuse traces show Claude Code invocations
- ✅ Worker metrics visible in dashboard
- ✅ Constraint violations logged
- ✅ Session continuity visible in traces

---

## Next Steps

1. **Review Architecture** - User validates proposed approach
2. **Implement Phase 2** - MCP bridge integration (workers/claude_code_worker.py)
3. **Write Tests** - Unit + integration tests for Claude Code execution
4. **Create Worker Definition** - claude_code_assistant_v1.yaml
5. **Validate E2E** - Interactive MCP client with real Claude Code execution
6. **LangGraph Integration** - Use workers as nodes in workflows
7. **Production Deployment** - Roll out to staging → production

---

## Open Questions

1. **Container Management:** Should workers spawn their own claude-mcp containers or share a pool?
   - **Recommendation:** Share pool initially (simpler), spawn per-journey later (isolation)

2. **Session Persistence:** Where to store session_id for recovery after worker restart?
   - **Recommendation:** LangGraph checkpointer for workflows, in-memory for standalone workers

3. **Recursion Limits:** If Claude Code uses Worker Marketplace, how deep should nesting go?
   - **Recommendation:** Max depth = 2 (Claude Code → Worker → Nested Worker), then error

4. **Error Handling:** How should workers handle Claude Code failures?
   - **Recommendation:** Return error in output, don't throw exception (graceful degradation)

---

## References

### Existing Code
- `lgp/claude_code/session_manager.py` - MCP session management pattern
- `lgp/claude_code/node_factory.py` - LangGraph node creation pattern
- `workers/isolation/container.py` - Docker container isolation
- `workers/claude_code_worker.py` - Worker execution (needs update)
- `workers/mcp_server.py` - MCP server exposing workers

### Documentation
- `workers/MCP_CLIENT_GUIDE.md` - Interactive client usage
- `sacred-core-complete-worker/01-the-project.md` - Worker marketplace architecture
- `templates/README.md` - Workflow template patterns

### Tests
- `workers/test_mcp_integration.py` - MCP tool registration tests
- `workers/test_mcp_client_e2e.py` - E2E MCP protocol test
- `workers/mcp_client_cli.py` - Interactive testing client
