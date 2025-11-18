```yaml
name: LangGraph Platform - The Project
description: Workflow runtime for rapid experimentation and hosting. Eternal truth (primitive, emergence) + structural architecture (phases, entities).
created: 2025-11-18
```

# LangGraph Platform: The Project

## Sacred Primitive (ETERNAL)

```
Workflow Runtime = Environment-isolated execution engine for LangGraph graphs
```

**What This Means:**
- **NOT** a library (you import and build)
- **IS** a runtime (you declare and execute)
- Workflows are **data** (Python files loaded by runtime)
- Environments are **boundaries** (experiment vs hosted)
- Execution is **isolated** (hot reload, observability, checkpointing injected)

**Why Sacred:**
- This defines **what the system is**
- Changing this changes **system identity**
- No alternative preserves "environment-isolated rapid iteration → stable hosting"

**Cannot Be:**
- Relaxed ("just use LangGraph directly" = no runtime)
- Augmented ("add library mode" = destroys environment boundary)
- Conditionally applied ("optional runtime" = loses isolation)

---

## Emergence Principle (ETERNAL)

```
Capabilities emerge from runtime boundaries, not from feature implementation
```

**What Emerges:**
- Hot reload emerges when runtime watches files (experiment mode)
- API hosting emerges when runtime serves HTTP (hosted mode)
- Observability emerges when runtime injects tracers
- Checkpointing emerges when runtime manages persistence

**Direct Implementation = Violation:**
```python
# WRONG: Feature in workflow code
def my_workflow(state):
    with hot_reload():  # ❌ Workflow aware of runtime
        ...

# RIGHT: Feature from runtime
# Workflow code:
def my_workflow(state):
    ...  # ✅ Environment-agnostic

# Runtime provides hot reload transparently
```

---

## The 7 Phase Shifts (STRUCTURAL)

### Phase 0: No Runtime (Initial State)

**Constraint:**
```
Workflows = Python scripts, manually executed, no environment boundary
```

**What's Missing:**
- No hot reload (manual restart)
- No environment isolation (experiment = hosted)
- No observability injection
- No checkpointer management
- No API hosting

---

### Phase 1: CLI Runtime (R1 - Experiment Mode)

**Constraint Removed:** Manual execution, no hot reload

**What Emerges:**
- `lgp run <workflow>` command
- File watching + automatic restart
- Console-based observability
- Local SQLite checkpointer (automatic)

**Witness Outcomes:**
```yaml
experiment_mode_working: true
hot_reload_latency: <2s
console_logs_visible: true
workflow_completes: true
```

**Tasks:** 3 tasks (R1.1-R1.3)

---

### Phase 2: API Runtime (R2 - Hosted Mode)

**Constraint Removed:** CLI-only execution, no HTTP API

**What Emerges:**
- `lgp serve <workflow>` command
- POST /workflows/{name}/invoke endpoint
- GET /sessions/{thread_id} endpoint
- Multi-worker concurrency
- API key authentication

**Witness Outcomes:**
```yaml
api_responds: true
concurrent_requests: 10+
auth_enforced: true
sessions_queryable: true
```

**Tasks:** 4 tasks (R2.1-R2.4)

---

### Phase 3: Observability Integration (R3 - Langfuse)

**Constraint Removed:** Console-only logging, no trace persistence

**What Emerges:**
- Langfuse tracer injection (hosted mode)
- Output sanitization (dashboard performance)
- Trace metadata automatic tagging
- Cost tracking (if using OpenAI)

**Witness Outcomes:**
```yaml
traces_in_langfuse: true
dashboard_loads: <1s
outputs_sanitized: true
workflow_cost_visible: true
```

**Tasks:** 3 tasks (R3.1-R3.3)

---

### Phase 4: Checkpointer Management (R4 - PostgreSQL)

**Constraint Removed:** SQLite-only (single-server limit)

**What Emerges:**
- PostgreSQL checkpointer (config-driven)
- Connection pooling (PgBouncer)
- Multi-server deployment enabled
- Zero-downtime migration from SQLite

**Witness Outcomes:**
```yaml
postgres_checkpointer_working: true
multi_server_deployment: true
write_throughput: 500+ writes/sec
migration_data_loss: 0
```

**Tasks:** 5 tasks (R4.1-R4.5)

---

### Phase 5: Claude Code Nodes (R5 - Stateful Agents)

**Constraint Removed:** Stateless LLM calls only

**What Emerges:**
- `create_claude_code_node()` factory
- MCP session management
- Repository-isolated agents
- Session continuity across invocations

**Witness Outcomes:**
```yaml
claude_code_nodes_working: true
session_continuity: true
repository_isolation: true
cost_model: fixed ($20/month)
```

**Tasks:** 4 tasks (R5.1-R5.4)

---

### Phase 6: Workflow Templates (R6 - Rapid Start)

**Constraint Removed:** Empty project, manual setup

**What Emerges:**
- `lgp create <name> --template <type>` command
- 5+ workflow templates
- Progressive complexity (basic → multi-agent)
- Template registry

**Witness Outcomes:**
```yaml
templates_available: 5+
create_to_run: <2 minutes
template_customization: true
```

**Tasks:** 3 tasks (R6.1-R6.3)

---

### Phase 7: Production Mastery (R7 - Autonomous Operations)

**Constraint Removed:** Manual deployment, no auto-scaling

**What Emerges:**
- `lgp deploy <workflow>` command
- Auto-scaling (request-based)
- Anomaly detection (error rate spikes)
- Self-healing (automatic restarts)

**Witness Outcomes:**
```yaml
one_command_deploy: true
auto_scaling_triggered: true
anomaly_detected_in: <1 minute
manual_intervention: 0
```

**Tasks:** 4 tasks (R7.1-R7.4)

---

## Entity Hierarchy (STRUCTURAL)

```
Runtime (Executor)
├── Environment (experiment | hosted)
│   ├── Checkpointer (SQLite | PostgreSQL)
│   ├── Tracer (Console | Langfuse)
│   ├── HotReload (enabled | disabled)
│   └── Auth (none | api_key)
│
├── Workflow Registry
│   ├── Workflow Definition (Python file)
│   ├── Config (timeout, checkpointing, observability)
│   └── Metadata (description, author)
│
├── CLI (Command Interface)
│   ├── run (experiment mode)
│   ├── serve (hosted mode)
│   ├── create (from template)
│   └── deploy (production)
│
└── API (HTTP Interface)
    ├── /workflows/{name}/invoke
    ├── /sessions/{thread_id}
    └── /health
```

---

## Success Metrics (STRUCTURAL - Targets Only)

### Experimentation Velocity
```yaml
idea_to_running_workflow: <5 minutes
hot_reload_cycle: <2 seconds
template_to_custom: <10 minutes
```

### Hosting Simplicity
```yaml
commands_to_deploy: 1
code_changes_for_hosting: 0
api_response_time: <500ms
```

### Platform Leverage
```yaml
checkpointing: automatic (configured, not coded)
observability: automatic (injected by runtime)
claude_code_nodes: factory (import, don't implement)
multi_environment: zero-friction (same code)
```

### Cost Efficiency (with Claude Code nodes)
```yaml
cost_model: fixed ($20/month Claude Pro)
cost_per_workflow: $0 (unlimited)
vs_api_cost: 90%+ savings (at scale)
```

---

## Phase Dependencies (STRUCTURAL)

```
R1 (CLI Runtime) → Foundation
├─ R2 (API Runtime) → Requires R1
├─ R3 (Observability) → Requires R1 or R2
└─ R6 (Templates) → Requires R1

R2 (API Runtime) →
├─ R4 (PostgreSQL) → Requires R2 (multi-server needs API)
└─ R7 (Production) → Requires R2 (deployment needs API)

R3 (Observability) → Independent of R4
R5 (Claude Code) → Can run after R1 (independent)
R6 (Templates) → Can run after R1 (independent)

R7 (Production) → Requires R2 + R4 (API + PostgreSQL)
```

**Critical Path:** R1 → R2 → R4 → R7
**Independent:** R3, R5, R6 (can be done in parallel after R1)

---

## What This Project IS and IS NOT

### IS
- ✅ Workflow runtime with environment isolation
- ✅ Rapid experimentation → stable hosting (zero friction)
- ✅ Config-driven infrastructure (checkpointing, observability)
- ✅ CLI + API interface
- ✅ Template-based workflow creation

### IS NOT
- ❌ LangGraph library replacement (uses LangGraph)
- ❌ General-purpose Python framework
- ❌ Cloud service (self-hosted runtime)
- ❌ Workflow builder UI (code-first)
- ❌ Agent orchestration platform (workflow-focused)

---

## The Primitive Protection

**The runtime boundary protects:**
1. **Workflow code** = environment-agnostic (no runtime awareness)
2. **Environment config** = injected by runtime (not hardcoded)
3. **Infrastructure** = automatic (checkpointing, observability)
4. **Execution mode** = transparent (experiment vs hosted)

**Violation Example:**
```python
# ❌ WRONG: Workflow aware of runtime
def my_workflow(state):
    if os.getenv("ENVIRONMENT") == "hosted":
        checkpointer = PostgresSaver(...)
    else:
        checkpointer = SqliteSaver(...)
    # Workflow now coupled to environment

# ✅ RIGHT: Runtime injects checkpointer
def my_workflow(state):
    # Workflow code is pure logic
    return {"result": process(state)}

# Runtime handles:
# - lgp run → SQLite checkpointer
# - lgp serve → PostgreSQL checkpointer
```

---

## Knowledge Layer Compliance

**This document contains:**
- ✅ Sacred primitive (ETERNAL)
- ✅ Emergence principle (ETERNAL)
- ✅ 7 phase shifts (STRUCTURAL)
- ✅ Entity hierarchy (STRUCTURAL)
- ✅ Success metrics (STRUCTURAL targets)

**This document excludes:**
- ❌ Current phase location (→ 04-current-state.md)
- ❌ Task completion status (→ 04-current-state.md)
- ❌ Actual measurements (→ 04-current-state.md)
- ❌ Protective constraints (→ 02-the-discipline.md)
- ❌ Task definitions (→ 03-implementation-plan.md)

---

## Archive Notice

**This document is TIMELESS.**

Once written, this document should NOT be updated except for:
1. Constraint tightening (with versioning + rationale)
2. Phase definition errors (structural fixes only)
3. Entity hierarchy corrections (architectural changes)

**This document will be readable decades from now.**
