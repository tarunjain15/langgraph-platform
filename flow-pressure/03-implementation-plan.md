```yaml
name: LangGraph Platform - Implementation Plan
description: 26 tasks across 7 phases. Structural knowledge (task definitions, witnesses, code patterns) with volatile references (Linear).
created: 2025-11-18
```

# LangGraph Platform: Implementation Plan

## Execution Model

**Sequential Phases:** R1 → R2 → R3 → R4 → R5 → R6 → R7
**Parallel Tasks:** Within each phase, tasks can run in parallel
**Witness-Based Completion:** Phase advances only when all witnesses observed

---

## Phase R1: CLI Runtime (Experiment Mode)

**Constraint Removed:** Manual execution, no hot reload
**What Emerges:** `lgp run <workflow>` with file watching

### Task R1.1: CLI Command Structure
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- `lgp --help` shows available commands
- `lgp run --help` shows command options
- Command parsing works with arguments

**Acceptance Criteria:**
```bash
$ lgp --help
Usage: lgp [OPTIONS] COMMAND [ARGS]...

Commands:
  run     Execute workflow in experiment mode
  serve   Start workflow API server
  create  Create workflow from template

$ lgp run --help
Usage: lgp run [OPTIONS] WORKFLOW

Options:
  --watch    Enable hot reload
  --verbose  Show detailed logs
```

**Code Pattern:**
```python
# cli/main.py
import click

@click.group()
def cli():
    """LangGraph Platform CLI"""
    pass

@cli.command()
@click.argument('workflow')
@click.option('--watch', is_flag=True)
def run(workflow, watch):
    """Execute workflow in experiment mode"""
    executor = WorkflowExecutor(environment="experiment")
    executor.execute(workflow)
```

---

### Task R1.2: Workflow Loading & Execution
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- Workflow Python file loads successfully
- `workflow` object extracted from module
- Execution completes with result
- Errors show clear traceback

**Acceptance Criteria:**
```bash
$ lgp run workflows/basic_workflow.py
[lgp] Loading workflow: basic_workflow
[lgp] Executing...
[lgp] ✅ Complete (2.3s)
Result: {"status": "success"}
```

**Code Pattern:**
```python
# runtime/executor.py
import importlib.util

class WorkflowExecutor:
    def execute(self, workflow_path):
        # Load module
        spec = importlib.util.spec_from_file_location("workflow", workflow_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Extract workflow
        workflow = module.workflow

        # Execute
        result = workflow.invoke({"input": "test"})
        return result
```

---

### Task R1.3: Hot Reload File Watching
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- File modification detected <500ms
- Workflow reload triggered
- New execution uses updated code
- Session continuity preserved (checkpoints intact)
- Total reload latency <2s

**Acceptance Criteria:**
```bash
$ lgp run workflows/my_workflow.py --watch
[lgp] Hot reload: ON
[lgp] Watching: workflows/my_workflow.py
[lgp] Executing...
[lgp] ✅ Complete (2.1s)

# User edits file, saves
[lgp] File changed detected (0.3s)
[lgp] Reloading workflow... (1.2s)
[lgp] Executing...
[lgp] ✅ Complete (2.0s)
```

**Code Pattern:**
```python
# runtime/hot_reload.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorkflowWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # Flush checkpoints
            checkpointer.flush()

            # Reload module
            importlib.reload(workflow_module)

            # Resume session
            checkpointer.resume()
```

---

## Phase R2: API Runtime (Hosted Mode)

**Constraint Removed:** CLI-only execution, no HTTP API
**What Emerges:** `lgp serve <workflow>` with REST API

### Task R2.1: FastAPI Server Setup
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- `lgp serve` starts HTTP server
- Server responds to GET /health
- Server logs show startup
- Graceful shutdown on Ctrl+C

**Acceptance Criteria:**
```bash
$ lgp serve workflows/my_workflow.py
[lgp] Starting API server...
[lgp] Environment: hosted
[lgp] Server: http://0.0.0.0:8000
[lgp] ✅ Ready

$ curl http://localhost:8000/health
{"status": "healthy", "workflow": "my_workflow"}
```

**Code Pattern:**
```python
# api/app.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

# runtime/server.py
import uvicorn

def serve(workflow_name):
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### Task R2.2: Workflow Invocation Endpoint
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- POST /workflows/{name}/invoke accepts input
- Workflow executes asynchronously
- Response includes thread_id for session tracking
- Execution result returned in response

**Acceptance Criteria:**
```bash
$ curl -X POST http://localhost:8000/workflows/my_workflow/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "test", "thread_id": "session-001"}'

{
  "status": "complete",
  "thread_id": "session-001",
  "result": {"output": "processed"},
  "duration_ms": 2134
}
```

**Code Pattern:**
```python
# api/routes/workflows.py
@app.post("/workflows/{workflow_name}/invoke")
async def invoke_workflow(workflow_name: str, request: InvokeRequest):
    executor = WorkflowExecutor(environment="hosted")
    result = await executor.execute(workflow_name, request.dict())
    return result
```

---

### Task R2.3: Session Query Endpoint
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- GET /sessions/{thread_id} returns session state
- Checkpoint history visible
- Traversal through checkpoints works
- 404 on non-existent thread_id

**Acceptance Criteria:**
```bash
$ curl http://localhost:8000/sessions/session-001

{
  "thread_id": "session-001",
  "checkpoints": 5,
  "latest_state": {"step": 3, "status": "complete"},
  "created_at": "2025-11-18T10:00:00Z"
}
```

**Code Pattern:**
```python
# api/routes/sessions.py
@app.get("/sessions/{thread_id}")
async def get_session(thread_id: str):
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}

    checkpoints = []
    async for cp in checkpointer.alist(config):
        checkpoints.append(cp)

    return {"thread_id": thread_id, "checkpoints": len(checkpoints)}
```

---

### Task R2.4: API Authentication
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- Requests without API key rejected (401)
- Requests with valid key accepted
- API key configured in config/hosted.yaml
- Rate limiting enforced (100 req/min default)

**Acceptance Criteria:**
```bash
# No API key
$ curl http://localhost:8000/workflows/my_workflow/invoke
{"error": "Unauthorized", "status": 401}

# With API key
$ curl -H "Authorization: Bearer ${API_KEY}" \
  http://localhost:8000/workflows/my_workflow/invoke
{"status": "complete", ...}
```

**Code Pattern:**
```python
# api/middleware/auth.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## Phase R3: Observability Integration (Langfuse)

**Constraint Removed:** Console-only logging, no trace persistence
**What Emerges:** Langfuse tracer injection, dashboard visibility

### Task R3.1: Langfuse Tracer Integration
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- Langfuse client initialized from config
- Workflow execution creates trace
- Trace visible in Langfuse dashboard
- Trace includes workflow name, duration, status

**Acceptance Criteria:**
```bash
$ lgp serve my_workflow
[lgp] Observability: Langfuse enabled
[lgp] Trace URL: https://cloud.langfuse.com/trace/{trace_id}
```

**Code Pattern:**
```python
# platform/observability/tracers.py
from langfuse import observe

def create_tracer(config):
    if config.observability.langfuse:
        return LangfuseTracer(
            secret_key=config.langfuse.secret_key,
            public_key=config.langfuse.public_key
        )
    return ConsoleTracer()
```

---

### Task R3.2: Output Sanitization
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- Outputs >2000 chars truncated
- Full length preserved in metadata
- Dashboard loads <1s
- No rendering errors or timeouts

**Acceptance Criteria:**
```python
# Large output from workflow
output = "..." * 5000  # 15,000 chars

# Sanitized for dashboard
sanitized = sanitize_for_dashboard(output)
assert len(sanitized) == 2000
assert "truncated" in sanitized
assert metadata["output_full_length"] == 15000
```

**Code Pattern:**
```python
# platform/observability/sanitizers.py
def sanitize_for_dashboard(data: dict, max_length: int = 2000) -> dict:
    """Truncate large outputs while preserving metadata"""
    result = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > max_length:
            result[key] = value[:max_length] + f"... (truncated, full: {len(value)} chars)"
            result[f"{key}_full_length"] = len(value)
        else:
            result[key] = value
    return result
```

---

### Task R3.3: Automatic Trace Tagging
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- All traces tagged with workflow name
- Environment (experiment/hosted) visible in metadata
- Cost tracking enabled (if using OpenAI)
- Trace filtering works by tag

**Acceptance Criteria:**
```python
# Every trace automatically tagged
trace_metadata = {
    "workflow_name": "my_workflow",
    "environment": "hosted",
    "runtime_version": "0.1.0",
    "repository": "langgraph-platform"
}
```

**Code Pattern:**
```python
# runtime/executor.py
with propagate_attributes(
    metadata=get_metadata(workflow_name, environment),
    tags=["langgraph-platform", environment]
):
    result = await workflow.ainvoke(input_data)
```

---

## Phase R4: Checkpointer Management (PostgreSQL)

**Constraint Removed:** SQLite-only (single-server limit)
**What Emerges:** PostgreSQL checkpointer, multi-server deployment

### Task R4.1: Checkpointer Factory
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- `create_checkpointer(type, config)` works
- SQLite checkpointer created (experiment mode)
- PostgreSQL checkpointer created (hosted mode)
- Config-driven selection (no code changes)

**Acceptance Criteria:**
```python
# experiment mode
checkpointer = create_checkpointer(
    type="sqlite",
    config={"path": "./checkpoints.db", "async": True}
)

# hosted mode
checkpointer = create_checkpointer(
    type="postgresql",
    config={"url": os.getenv("DATABASE_URL"), "pool_size": 10}
)
```

**Code Pattern:**
```python
# platform/checkpointing/factory.py
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

def create_checkpointer(type: str, config: dict):
    if type == "sqlite":
        return AsyncSqliteSaver.from_conn_string(config["path"])
    elif type == "postgresql":
        return AsyncPostgresSaver.from_conn_string(config["url"])
    else:
        raise ValueError(f"Unknown checkpointer type: {type}")
```

---

### Task R4.2: PostgreSQL Schema Migration
**Type:** Migration Step
**Linear:** TBD

**Witness Outcome:**
- Migration script creates tables
- Schema matches LangGraph spec
- Indexes created on thread_id, checkpoint_id
- WAL mode equivalent (PostgreSQL)

**Acceptance Criteria:**
```bash
$ lgp migrate sqlite-to-postgres --source checkpoints.db --dest ${DATABASE_URL}
[lgp] Reading SQLite checkpoints... (1250 found)
[lgp] Creating PostgreSQL schema...
[lgp] Migrating data... (1250/1250)
[lgp] ✅ Migration complete (0 data loss)
```

**Code Pattern:**
```python
# migrations/sqlite_to_postgresql.py
def migrate(source_db, dest_db):
    # Read SQLite
    sqlite_conn = sqlite3.connect(source_db)
    checkpoints = read_all_checkpoints(sqlite_conn)

    # Write PostgreSQL
    pg_conn = psycopg2.connect(dest_db)
    for checkpoint in checkpoints:
        write_checkpoint(pg_conn, checkpoint)
```

---

### Task R4.3: Connection Pooling (PgBouncer)
**Type:** Optimization
**Linear:** TBD

**Witness Outcome:**
- PgBouncer configured (max 100 connections)
- Connection acquisition <5ms (p99)
- No connection exhaustion under load
- Graceful degradation at limit

**Acceptance Criteria:**
```bash
# Load test: 100 concurrent requests
$ lgp load-test my_workflow --concurrent 100
[lgp] Connection pool: 100 max, 95 active, 5 idle
[lgp] Connection acquisition p99: 3.2ms ✅
[lgp] No connection timeouts ✅
```

**Code Pattern:**
```yaml
# config/hosted.yaml
checkpointer:
  type: postgresql
  url: ${DATABASE_URL}
  pool:
    min_size: 10
    max_size: 100
    timeout: 5000
```

---

### Task R4.4: Multi-Server Deployment Test
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- 2 API servers running simultaneously
- Both share same PostgreSQL checkpointer
- Session continuity across servers
- No checkpoint conflicts (optimistic locking works)

**Acceptance Criteria:**
```bash
# Server 1
$ lgp serve my_workflow --port 8000
[lgp] Checkpointer: PostgreSQL (shared)

# Server 2
$ lgp serve my_workflow --port 8001
[lgp] Checkpointer: PostgreSQL (shared)

# Client request to server 1
$ curl http://localhost:8000/workflows/my_workflow/invoke \
  -d '{"thread_id": "session-001", "step": 1}'

# Client request to server 2 (same session)
$ curl http://localhost:8001/sessions/session-001
{"checkpoints": 1, "latest_state": {"step": 1}}
# ✅ Session visible across servers
```

---

### Task R4.5: Size Limit Wrapper
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- Checkpoints >10MB rejected before serialization
- Clear error message with guidance
- Metadata includes checkpoint size estimate
- Warning at 5MB threshold

**Acceptance Criteria:**
```python
# Large checkpoint rejected
try:
    checkpointer.aput(config, large_checkpoint)
except CheckpointSizeLimitError as e:
    print(e)
    # "Checkpoint size (12.5 MB) exceeds limit (10 MB).
    #  Consider externalizing large files to blob storage."
```

**Code Pattern:**
```python
# platform/checkpointing/wrappers.py
class SizeLimitedCheckpointer:
    def __init__(self, checkpointer, max_size_mb=10):
        self.checkpointer = checkpointer
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def aput(self, config, checkpoint, metadata, new_versions):
        size = estimate_size(checkpoint)
        if size > self.max_size_bytes:
            raise CheckpointSizeLimitError(f"Size {size/1024/1024:.1f} MB exceeds {self.max_size_mb} MB")
        return await self.checkpointer.aput(config, checkpoint, metadata, new_versions)
```

---

## Phase R5: Claude Code Nodes (Stateful Agents)

**Constraint Removed:** Stateless LLM calls only
**What Emerges:** `create_claude_code_node()` factory, MCP integration

### Task R5.1: MCP Session Management
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- MCP client connects to mesh-mcp server
- Session initialization successful
- `mesh_execute` tool callable
- Session cleanup on shutdown

**Acceptance Criteria:**
```python
# MCP session
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # ✅ Connected to mesh-mcp

        result = await session.call_tool("mesh_execute", {
            "repository": "sample-repo",
            "task": "List files"
        })
        # ✅ Tool execution works
```

**Code Pattern:**
```python
# platform/agents/mcp_session.py
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def create_mcp_session():
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", "claude-mesh-workspace", "node", "/app/dist/index.js"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
```

---

### Task R5.2: Claude Code Node Factory
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- `create_claude_code_node(role, repo)` returns async function
- Node executes in specified repository
- Session ID preserved across invocations
- Output sanitized for observability

**Acceptance Criteria:**
```python
# Create node
research_node = create_claude_code_node(
    role="researcher",
    repository="research-repo",
    mcp_session=session
)

# Execute node
result = await research_node({"task": "Research AI safety"})

# ✅ Returns session_id for continuity
assert "session_id" in result
assert "output" in result
```

**Code Pattern:**
```python
# platform/agents/claude_code_node.py
def create_claude_code_node(role, repository, mcp_session):
    async def node(state):
        result = await mcp_session.call_tool("mesh_execute", {
            "repository": repository,
            "task": state["task"],
            "session_id": state.get(f"{role}_session_id")
        })

        output = extract_output(result)
        session_id = extract_session_id(result)

        return {
            f"{role}_output": output,
            f"{role}_session_id": session_id
        }

    return node
```

---

### Task R5.3: Repository Isolation Test
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- 3 nodes with different repositories run concurrently
- Repository A cannot access Repository B files
- Sessions remain isolated (separate session IDs)
- No cross-contamination of context

**Acceptance Criteria:**
```python
# 3 isolated agents
research_node = create_claude_code_node("researcher", "research-repo")
writer_node = create_claude_code_node("writer", "writer-repo")
reviewer_node = create_claude_code_node("reviewer", "reviewer-repo")

# Execute concurrently
results = await asyncio.gather(
    research_node({"task": "Research topic"}),
    writer_node({"task": "Write article"}),
    reviewer_node({"task": "Review article"})
)

# ✅ All 3 complete successfully
# ✅ Different session IDs
# ✅ No shared context
```

---

### Task R5.4: Cost Tracking (Fixed Model)
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- Workflow count tracked (not token count)
- Cost = $20/month (Claude Pro subscription)
- Metadata shows workflow invocations, not API costs
- Cost model documented in observability

**Acceptance Criteria:**
```yaml
# Langfuse metadata
workflow_invocations: 150
cost_model: "fixed_subscription"
monthly_cost: 20.00
cost_per_invocation: 0.13  # $20 / 150 invocations
```

**Code Pattern:**
```python
# platform/observability/metadata.py
def get_metadata(workflow_name, environment):
    return {
        "workflow_name": workflow_name,
        "environment": environment,
        "cost_model": "fixed_subscription",
        "session_continuity": "enabled"
    }
```

---

## Phase R6: Workflow Templates (Rapid Start)

**Constraint Removed:** Empty project, manual setup
**What Emerges:** `lgp create <name> --template <type>` command

### Task R6.1: Template Registry
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- 5 templates available (basic, with_claude_code, multi_agent, data_pipeline, custom)
- `lgp templates` lists available templates
- Template metadata visible (description, complexity)

**Acceptance Criteria:**
```bash
$ lgp templates

Available Templates:
  basic             Simple workflow with one agent
  with_claude_code  Workflow using Claude Code nodes
  multi_agent       3-agent pipeline (research → write → review)
  data_pipeline     CSV processing workflow
  custom            Empty template for custom workflows
```

---

### Task R6.2: Workflow Creation from Template
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- `lgp create my_workflow --template basic` creates workflow file
- Workflow file added to workflows/
- Config entry added to workflows/config.yaml
- Workflow immediately runnable

**Acceptance Criteria:**
```bash
$ lgp create my_workflow --template basic
[lgp] Creating workflow: my_workflow
[lgp] Template: basic
[lgp] Created: workflows/my_workflow.py
[lgp] Updated: workflows/config.yaml
[lgp] ✅ Ready to run: lgp run my_workflow

$ lgp run my_workflow
[lgp] ✅ Complete (1.2s)
```

---

### Task R6.3: Template Customization Guide
**Type:** Feature Witness
**Linear:** TBD

**Witness Outcome:**
- Each template includes inline comments
- README shows customization points
- Progressive complexity (basic → advanced)
- Example workflow output shown

**Acceptance Criteria:**
```python
# templates/basic/workflow.py

"""
Basic Workflow Template

Customize:
1. Update state schema (WorkflowState)
2. Modify agent logic (agent_node function)
3. Add more nodes (workflow.add_node)
"""

class WorkflowState(TypedDict):
    input: str      # ← Customize state
    output: str
```

---

## Phase R7: Production Mastery (Autonomous Operations)

**Constraint Removed:** Manual deployment, no auto-scaling
**What Emerges:** `lgp deploy <workflow>` with autonomous operations

### Task R7.1: One-Command Deployment
**Type:** Integration Pressure Point
**Linear:** TBD

**Witness Outcome:**
- `lgp deploy my_workflow` pushes to production
- Environment variables validated
- Health check passes
- API accessible at production URL

**Acceptance Criteria:**
```bash
$ lgp deploy my_workflow
[lgp] Validating environment... ✅
[lgp] Pushing to production...
[lgp] Running health checks... ✅
[lgp] ✅ Deployed: https://api.example.com/workflows/my_workflow
```

---

### Task R7.2: Auto-Scaling Configuration
**Type:** Optimization
**Linear:** TBD

**Witness Outcome:**
- Request-based scaling configured
- Min replicas: 1, Max replicas: 10
- Scale-up threshold: 80% CPU or 100 req/sec
- Scale-down latency: 5 minutes

**Acceptance Criteria:**
```yaml
# config/production.yaml
auto_scaling:
  enabled: true
  min_replicas: 1
  max_replicas: 10
  scale_up_threshold:
    cpu_percent: 80
    requests_per_second: 100
  scale_down_delay: 300  # seconds
```

---

### Task R7.3: Anomaly Detection
**Type:** Automation
**Linear:** TBD

**Witness Outcome:**
- Error rate spike detected <1 minute
- Alert sent to configured channel
- Automatic rollback triggered if error rate >10%
- Incident logged in observability platform

**Acceptance Criteria:**
```bash
# Error rate spikes from 0.5% → 12%
[lgp] ⚠️  Anomaly detected: error_rate = 12.0% (threshold: 10%)
[lgp] Triggering rollback to previous version...
[lgp] ✅ Rollback complete (error_rate: 0.5%)
[lgp] Incident logged: INC-2025-001
```

---

### Task R7.4: Self-Healing Restarts
**Type:** Automation
**Linear:** TBD

**Witness Outcome:**
- Workflow crash detected
- Automatic restart triggered
- Session continuity preserved (checkpoint resume)
- Max retries: 3, backoff: exponential

**Acceptance Criteria:**
```bash
# Workflow crashes
[lgp] ❌ Workflow crashed: OOMKilled
[lgp] Restarting... (attempt 1/3)
[lgp] Resuming from checkpoint: session-001
[lgp] ✅ Workflow recovered
```

**Code Pattern:**
```python
# runtime/executor.py
async def execute_with_retry(workflow, state, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await workflow.ainvoke(state)
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

            # Resume from checkpoint
            state = await checkpointer.get_latest(state["thread_id"])
```

---

## Completion Criteria

### Phase Completion
**Phase is complete when:**
1. All tasks have witness outcomes observed ✅
2. All acceptance criteria pass ✅
3. No active constraint violations ✅

### Task Completion
**Task is complete when:**
1. Witness outcome is observable (not claimed)
2. Acceptance criteria automated (CI/CD testable)
3. Code pattern implemented (minimal infrastructure)

### Project Completion
**Project is complete when:**
1. All 7 phases complete ✅
2. All 26 tasks complete ✅
3. Full workflow lifecycle works (experiment → hosted → production)
4. Documentation timeless (no volatile state)
5. Zero manual intervention required (autonomous)

---

## Knowledge Layer Compliance

**This document contains:**
- ✅ Task definitions (STRUCTURAL)
- ✅ Witness outcomes (STRUCTURAL)
- ✅ Acceptance criteria (STRUCTURAL)
- ✅ Code patterns (STRUCTURAL)
- ✅ Execution order (STRUCTURAL)
- ✅ External references (Linear links - acceptable)

**This document excludes:**
- ❌ Task completion status (→ 04-current-state.md)
- ❌ Actual completion dates (→ 04-current-state.md)
- ❌ Assignees (→ Linear)
- ❌ Current phase location (→ 04-current-state.md)

---

## Archive Notice

**This document is TIMELESS.**

Task definitions, witness outcomes, and acceptance criteria do NOT change once written (unless structural error found).

**This document will be readable decades from now.**
