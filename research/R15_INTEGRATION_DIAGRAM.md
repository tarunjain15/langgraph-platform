# R15: Claude Code Integration - Visual Architecture

## Overview: Three-Role Model

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                     CLAUDE CODE CONTAINERIZED INSTANCE                    ║
║                      (Docker: claude-mcp container)                       ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────┐    ║
║  │  ROLE 1: MCP SERVER                                             │    ║
║  │  ────────────────────                                           │    ║
║  │  Exposes: mesh_execute tool                                     │    ║
║  │  Transport: stdio                                               │    ║
║  │  Protocol: MCP (list_tools, call_tool)                          │    ║
║  │  Returns: Session ID + Output + Metadata                        │    ║
║  │                                                                  │    ║
║  │  Example:                                                        │    ║
║  │  ┌────────────────────────────────────────────────────────┐     │    ║
║  │  │ await session.call_tool('mesh_execute', {             │     │    ║
║  │  │   'repository': '/workspace/research',                │     │    ║
║  │  │   'task': 'Analyze Python best practices',            │     │    ║
║  │  │   'session_id': 'abc-123',  # Resume existing session │     │    ║
║  │  │   'timeout': 60000                                     │     │    ║
║  │  │ })                                                     │     │    ║
║  │  └────────────────────────────────────────────────────────┘     │    ║
║  └─────────────────────────────────────────────────────────────────┘    ║
║                                    ↕                                     ║
║  ┌─────────────────────────────────────────────────────────────────┐    ║
║  │  ROLE 2: MCP CLIENT                                             │    ║
║  │  ─────────────────                                              │    ║
║  │  Connects to: Worker Marketplace MCP Server                     │    ║
║  │  Uses: spawn_worker, execute_in_worker, get_worker_state        │    ║
║  │  Access: Filesystem, Git, Database workers                      │    ║
║  │  Pattern: Recursive composition (workers use workers)           │    ║
║  │                                                                  │    ║
║  │  Example:                                                        │    ║
║  │  ┌────────────────────────────────────────────────────────┐     │    ║
║  │  │ # Claude Code calls Worker Marketplace                │     │    ║
║  │  │ await mcp_client.call_tool('spawn_worker', {          │     │    ║
║  │  │   'worker_id': 'filesystem_research_v1',              │     │    ║
║  │  │   'journey_id': 'claude_task_123',                    │     │    ║
║  │  │   'isolation_level': 'container'                      │     │    ║
║  │  │ })                                                     │     │    ║
║  │  │                                                        │     │    ║
║  │  │ await mcp_client.call_tool('execute_in_worker', {     │     │    ║
║  │  │   'journey_id': 'claude_task_123',                    │     │    ║
║  │  │   'action': {'type': 'read', 'target': 'README.md'}  │     │    ║
║  │  │ })                                                     │     │    ║
║  │  └────────────────────────────────────────────────────────┘     │    ║
║  └─────────────────────────────────────────────────────────────────┘    ║
║                                    ↕                                     ║
║  ┌─────────────────────────────────────────────────────────────────┐    ║
║  │  ROLE 3: LANGGRAPH NODE                                         │    ║
║  │  ─────────────────────                                          │    ║
║  │  Integration: Via create_claude_code_node() factory             │    ║
║  │  State: Session ID persisted via checkpointer                   │    ║
║  │  Isolation: Repository workspace per agent role                 │    ║
║  │  Observability: Full Langfuse traces                            │    ║
║  │                                                                  │    ║
║  │  Example:                                                        │    ║
║  │  ┌────────────────────────────────────────────────────────┐     │    ║
║  │  │ researcher_node = create_claude_code_node(            │     │    ║
║  │  │   config={'role_name': 'researcher',                  │     │    ║
║  │  │           'repository': 'research_workspace',         │     │    ║
║  │  │           'timeout': 120000},                         │     │    ║
║  │  │   mcp_manager=session_manager                         │     │    ║
║  │  │ )                                                      │     │    ║
║  │  │                                                        │     │    ║
║  │  │ # Node executes via mesh_execute                      │     │    ║
║  │  │ # Session ID stored in LangGraph state                │     │    ║
║  │  │ # Next invocation resumes same session                │     │    ║
║  │  └────────────────────────────────────────────────────────┘     │    ║
║  └─────────────────────────────────────────────────────────────────┘    ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Integration Flow 1: Worker Marketplace → Claude Code

**Use Case:** External MCP client spawns worker that uses Claude Code for execution

```
┌──────────────────────┐
│  External MCP Client │  (Claude Desktop, VS Code, LangGraph)
│  (stdio transport)   │
└──────────┬───────────┘
           │ call_tool("spawn_worker", {worker_id: "claude_code_assistant_v1", ...})
           ↓
┌─────────────────────────────────────────────────────────────┐
│  Worker Marketplace MCP Server                              │
│  (workers/mcp_server.py)                                    │
│                                                              │
│  @server.call_tool()                                        │
│  async def handle_call_tool(name: str, arguments: dict):   │
│    if name == "spawn_worker":                               │
│      return await self._spawn_worker(arguments)             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  WorkerFactory.spawn()                                      │
│  (workers/factory.py)                                       │
│                                                              │
│  1. Load worker definition (YAML)                           │
│  2. Create isolated workspace                               │
│  3. Spawn container (if needed)                             │
│  4. Initialize ClaudeCodeWorker instance                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  ClaudeCodeWorker                                           │
│  (workers/claude_code_worker.py)                            │
│                                                              │
│  - workspace_path: /tmp/workers/claude_code/{journey_id}    │
│  - container_id: worker_{journey_id}                        │
│  - mcp_manager: MCPSessionManager(container="claude-mcp")   │
│  - session_id: None (initially)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ call_tool("execute_in_worker", {action: ...})
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  ClaudeCodeWorker.execute(action)                           │
│                                                              │
│  Step 1: Constraint Check                                   │
│  ┌────────────────────────────────────────┐                 │
│  │ violations = self.void(action)         │                 │
│  │ if violations:                         │                 │
│  │   return constraint_violation_response │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  Step 2: Convert Action to Task                             │
│  ┌────────────────────────────────────────┐                 │
│  │ task = self._action_to_task(action)    │                 │
│  │ # {"type": "read", "target": "README"} │                 │
│  │ # → "Read README.md"                   │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  Step 3: Invoke Claude Code via MCP                         │
│  ┌─────────────────────────────────────────────────┐        │
│  │ async with self.mcp_manager.create_session()    │        │
│  │                                 as session:      │        │
│  │   result = await session.call_tool(             │        │
│  │     'mesh_execute',                             │        │
│  │     arguments={                                 │        │
│  │       'repository': self.workspace_path,        │        │
│  │       'task': task,                             │        │
│  │       'session_id': self.session_id,  # Resume  │        │
│  │       'timeout': 60000                          │        │
│  │     }                                            │        │
│  │   )                                              │        │
│  └─────────────────────────────────────────────────┘        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  MCPSessionManager → Docker Exec                            │
│  (lgp/claude_code/session_manager.py)                       │
│                                                              │
│  stdio_client(                                              │
│    command="docker",                                        │
│    args=["exec", "-i", "claude-mcp",                        │
│           "node", "/app/dist/index.js"]                     │
│  )                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Claude Code Container (claude-mcp)                         │
│                                                              │
│  mesh-mcp server running (node /app/dist/index.js)          │
│                                                              │
│  Tool: mesh_execute                                         │
│  ┌─────────────────────────────────────────┐                │
│  │ DockerClaudeService.execute()           │                │
│  │ ├─ Spawn/Resume Claude CLI session      │                │
│  │ ├─ Execute task in repository workspace │                │
│  │ ├─ Capture output                       │                │
│  │ └─ Return: session_id + output          │                │
│  └─────────────────────────────────────────┘                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ Result
┌─────────────────────────────────────────────────────────────┐
│  Parse mesh_execute Result                                  │
│  (workers/claude_code_worker.py)                            │
│                                                              │
│  ┌────────────────────────────────────────┐                 │
│  │ output, session_id = self._parse_mesh_result(result)     │
│  │ self.session_id = session_id  # Save for continuity      │
│  │                                                           │
│  │ return {                                                  │
│  │   "executed": True,                                       │
│  │   "output": output,                                       │
│  │   "session_id": session_id,                               │
│  │   "action_type": action.get("type"),                      │
│  │   "workspace": self.workspace_path                        │
│  │ }                                                          │
│  └───────────────────────────────────────────────────────────┘
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ Return via MCP protocol
┌──────────────────────┐
│  External MCP Client │  Receives result
└──────────────────────┘
```

---

## Integration Flow 2: Claude Code → Worker Marketplace (Recursive)

**Use Case:** Claude Code uses Worker Marketplace to spawn specialized workers

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code Container                                      │
│  (Executing task: "Research Python best practices")         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Claude Code decides: "I need a filesystem research worker"
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Claude Code as MCP Client                                  │
│                                                              │
│  Connects to: Worker Marketplace MCP Server                 │
│  Transport: stdio (docker exec → mcp_server.py)             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ call_tool("spawn_worker", ...)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Worker Marketplace MCP Server                              │
│  (Running in separate container or host)                    │
│                                                              │
│  Receives: spawn_worker request from Claude Code            │
│  Validates: Journey isolation, constraint checks            │
│  Spawns: filesystem_research_v1 worker                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Nested Worker: filesystem_research_v1                      │
│                                                              │
│  - workspace: /tmp/workers/research/claude_task_123         │
│  - constraints: max_file_size=1MB, readonly=true            │
│  - tools: read, search, list                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Claude Code: call_tool("execute_in_worker", ...)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Nested Worker Executes                                     │
│                                                              │
│  1. void() → Constraint check (max_file_size, readonly)     │
│  2. execute() → Read files in isolated workspace            │
│  3. return → Research summary                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ Result
┌─────────────────────────────────────────────────────────────┐
│  Claude Code Receives Result                                │
│                                                              │
│  Processes: Research summary from nested worker             │
│  Continues: Writes report based on research                 │
│  Returns: Final output to original caller                   │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** Claude Code can delegate to specialized workers, creating a self-composing system.

---

## Integration Flow 3: LangGraph Workflow → Claude Code Workers

**Use Case:** Multi-agent LangGraph workflow with Claude Code nodes

```
┌─────────────────────────────────────────────────────────────┐
│  LangGraph Workflow Execution                               │
│  (workflows/research_pipeline.py)                           │
│                                                              │
│  Graph:                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐            │
│  │researcher│────▶│  writer  │────▶│ reviewer │            │
│  └──────────┘     └──────────┘     └──────────┘            │
│                                                              │
│  State:                                                      │
│  {                                                           │
│    'task': 'Research LangGraph patterns',                   │
│    'researcher_session_id': None,  # Persisted by checkpoint│
│    'writer_session_id': None,                               │
│    'reviewer_session_id': None                              │
│  }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Node: researcher
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  create_claude_code_node() Factory                          │
│  (lgp/claude_code/node_factory.py)                          │
│                                                              │
│  researcher_config = {                                      │
│    'role_name': 'researcher',                               │
│    'repository': 'research_workspace',                      │
│    'timeout': 120000                                        │
│  }                                                           │
│                                                              │
│  researcher_node = create_claude_code_node(                 │
│    config=researcher_config,                                │
│    mcp_manager=MCPSessionManager()                          │
│  )                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Execute node
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  researcher_node(state)                                     │
│                                                              │
│  Step 1: Extract task from state                            │
│  ┌────────────────────────────────────────┐                 │
│  │ task = state.get('task')               │                 │
│  │ session_id = state.get('researcher_session_id')          │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  Step 2: Create MCP session                                 │
│  ┌────────────────────────────────────────┐                 │
│  │ async with mcp_manager.create_session() as session:      │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  Step 3: Call mesh_execute                                  │
│  ┌────────────────────────────────────────┐                 │
│  │ result = await session.call_tool(      │                 │
│  │   'mesh_execute',                      │                 │
│  │   arguments={                          │                 │
│  │     'repository': 'research_workspace',│                 │
│  │     'task': task,                      │                 │
│  │     'session_id': session_id,  # Resume│                 │
│  │     'timeout': 120000                  │                 │
│  │   }                                     │                 │
│  │ )                                       │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  Step 4: Parse and return updated state                     │
│  ┌────────────────────────────────────────┐                 │
│  │ output, new_session_id = parse_result(result)            │
│  │                                                           │
│  │ return {                                                  │
│  │   'researcher_output': output,                            │
│  │   'researcher_session_id': new_session_id,  # Persisted  │
│  │   'current_step': ['researcher']                          │
│  │ }                                                          │
│  └────────────────────────────────────────┘                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ State updated
┌─────────────────────────────────────────────────────────────┐
│  LangGraph Checkpointer                                     │
│  (R4: PostgreSQL checkpointer)                              │
│                                                              │
│  Persists:                                                   │
│  - researcher_session_id: "abc-123"                         │
│  - researcher_output: "Research summary..."                 │
│                                                              │
│  Benefits:                                                   │
│  - Session continuity across workflow executions            │
│  - Crash recovery (resume from last checkpoint)             │
│  - Time travel debugging                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Next node: writer
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  writer_node(state)                                         │
│                                                              │
│  - Uses researcher_output as input                          │
│  - Resumes writer_session_id if exists                      │
│  - Produces writer_output                                   │
│  - Updates writer_session_id in state                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Next node: reviewer
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  reviewer_node(state)                                       │
│                                                              │
│  - Uses writer_output as input                              │
│  - Resumes reviewer_session_id if exists                    │
│  - Produces reviewer_output (final result)                  │
│  - Updates reviewer_session_id in state                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ Workflow complete
┌──────────────────────┐
│  Final State         │
│  {                   │
│    'task': '...',    │
│    'researcher_output': '...',                              │
│    'researcher_session_id': 'abc-123',  # Persisted         │
│    'writer_output': '...',                                  │
│    'writer_session_id': 'def-456',      # Persisted         │
│    'reviewer_output': '...',            # Final result      │
│    'reviewer_session_id': 'ghi-789'     # Persisted         │
│  }                   │
└──────────────────────┘
```

**Key Benefits:**
1. **Session Continuity:** Each agent resumes its session across workflow runs
2. **State Persistence:** LangGraph checkpointer saves session IDs
3. **Crash Recovery:** Workflow can resume from last checkpoint
4. **Cost Efficiency:** $20/month Claude Pro subscription (not per-token API)

---

## Constraint Enforcement Flow

**Sacred Guarantee:** Constraints verified BEFORE Claude Code execution

```
┌─────────────────────────────────────────────────────────────┐
│  MCP Client calls: execute_in_worker                        │
│  action = {                                                  │
│    "type": "write",                                          │
│    "target": "large_file.txt",                              │
│    "content": "x" * 2_000_000  # 2MB                        │
│  }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  ClaudeCodeWorker.execute(action)                           │
│                                                              │
│  STEP 1: CONSTRAINT CHECK (void() safety gate)              │
│  ┌────────────────────────────────────────┐                 │
│  │ violations = self.void(action)         │                 │
│  │                                         │                 │
│  │ Checks:                                 │                 │
│  │ ✓ File size: 2MB > 1MB limit           │ ❌ VIOLATION   │
│  │ ✓ Workspace isolation: valid           │ ✅ PASS        │
│  │ ✓ Readonly filesystem: write allowed   │ ✅ PASS        │
│  │                                         │                 │
│  │ Result: violations = [                  │                 │
│  │   {                                     │                 │
│  │     constraint_id: "max_file_size",    │                 │
│  │     violated: True,                     │                 │
│  │     message: "File size 2MB exceeds limit 1MB"           │
│  │   }                                     │                 │
│  │ ]                                       │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  if violations:                                             │
│    return {  # SHORT CIRCUIT - No Claude Code execution!    │
│      "executed": False,                                      │
│      "violations": violations,                              │
│      "message": "Constraint violation detected..."          │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ↓ Return violation response
┌──────────────────────┐
│  MCP Client          │
│  Receives:           │
│  "Constraint violation detected:                            │
│   - File size 2000000 bytes exceeds limit 1000000 bytes     │
│                                                              │
│  Action rejected. Fix violations and retry."                │
└──────────────────────┘

                    NO CLAUDE CODE INVOCATION!
                    Cost saved, constraint enforced.
```

**Contrast: Valid Action**

```
┌─────────────────────────────────────────────────────────────┐
│  MCP Client calls: execute_in_worker                        │
│  action = {                                                  │
│    "type": "read",                                           │
│    "target": "README.md"                                    │
│  }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  ClaudeCodeWorker.execute(action)                           │
│                                                              │
│  STEP 1: CONSTRAINT CHECK                                   │
│  ┌────────────────────────────────────────┐                 │
│  │ violations = self.void(action)         │                 │
│  │                                         │                 │
│  │ Checks:                                 │                 │
│  │ ✓ File size: N/A (read operation)      │ ✅ PASS        │
│  │ ✓ Workspace isolation: valid           │ ✅ PASS        │
│  │ ✓ Readonly filesystem: read allowed    │ ✅ PASS        │
│  │                                         │                 │
│  │ Result: violations = []                 │                 │
│  └────────────────────────────────────────┘                 │
│                                                              │
│  STEP 2: INVOKE CLAUDE CODE (constraints passed!)           │
│  ┌────────────────────────────────────────┐                 │
│  │ async with mcp_manager.create_session() as session:      │
│  │   result = await session.call_tool('mesh_execute', {...})│
│  └────────────────────────────────────────┘                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Claude Code Executes                                       │
│  - Reads README.md                                          │
│  - Returns content                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────┐
│  MCP Client          │
│  Receives:           │
│  "Action completed successfully                             │
│   Output: <README.md content>                               │
│   Session ID: abc-123"                                      │
└──────────────────────┘
```

---

## Data Flow Summary

### Phase 2 Implementation (MCP Bridge)

```
┌─────────────────┐
│   MCP Client    │
│ (External Tool) │
└────────┬────────┘
         │
         ↓ spawn_worker (worker_id, journey_id)
┌────────────────────────────┐
│ Worker Marketplace Server  │
│ (workers/mcp_server.py)    │
└────────┬───────────────────┘
         │
         ↓ WorkerFactory.spawn()
┌────────────────────────────┐
│   ClaudeCodeWorker         │
│ - workspace: /tmp/workers  │
│ - mcp_manager: Ready       │
│ - session_id: None         │
└────────┬───────────────────┘
         │
         ↓ execute_in_worker (action)
┌────────────────────────────┐
│ void() Constraint Check    │
│ - Validates action         │
│ - Returns violations/pass  │
└────────┬───────────────────┘
         │
         ↓ (if valid)
┌────────────────────────────┐
│ MCPSessionManager          │
│ - Connect to claude-mcp    │
│ - Create session           │
└────────┬───────────────────┘
         │
         ↓ call_tool('mesh_execute')
┌────────────────────────────┐
│ Claude Code Container      │
│ - Execute task             │
│ - Return session_id        │
└────────┬───────────────────┘
         │
         ↓ Parse result
┌────────────────────────────┐
│ Save session_id in worker  │
│ Return output via MCP      │
└────────────────────────────┘
```

**Key Points:**
1. **Constraint check BEFORE Claude Code** (void() safety gate)
2. **Session continuity** (session_id persisted in worker)
3. **MCP protocol end-to-end** (client → server → Claude Code)
4. **Workspace isolation** (per user journey)

This architecture provides the missing link between Worker Marketplace infrastructure (R13/R14) and actual Claude Code execution, while maintaining all constraints and guarantees.
