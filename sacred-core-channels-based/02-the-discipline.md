```yaml
name: LangGraph Platform - The Discipline
description: Sacred constraints protecting the workflow runtime primitive. Eternal truth (constraint names, witness protocol) + learned thresholds (versioned, tightening).
created: 2025-11-24
version: 2.0.0
```

# LangGraph Platform: The Discipline

## What This Protects (ETERNAL)

**Threat to Primitive:**
```
Workflow Runtime Corruption = Workflows become environment-aware, destroying isolation boundary
```

**Symptoms of Corruption:**
- Workflows check `os.getenv("ENVIRONMENT")`
- Workflows import runtime internals (`from runtime.executor import...`)
- Workflows hardcode checkpointer/tracer instantiation
- Environment config lives in workflow code
- Experiment mode ≠ Hosted mode requires code changes
- Workflows spread state with `{**state, "field": value}` pattern

**Result:** Runtime becomes useless library, environment boundary collapses, concurrent update errors emerge

---

## The Six Sacred Constraints (ETERNAL)

### 1. ENVIRONMENT_ISOLATION

**Definition:**
```
Workflows MUST be environment-agnostic. Runtime injects all infrastructure.
```

**Witness (Observable, Automatic, Continuous, Actionable):**
```python
# Test runs on every workflow execution
def test_environment_isolation(workflow_code):
    forbidden_patterns = [
        "from runtime.",
        "from lgp.config",
        "os.getenv(\"ENVIRONMENT\")",
        "if environment ==",
        "SqliteSaver(",
        "PostgresSaver(",
        "Langfuse(",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in workflow_code, \
            f"ENVIRONMENT_ISOLATION violation: {pattern} found in workflow"
```

**Violation Example:**
```python
# ❌ VIOLATION
import os
from lgp.checkpointing.factory import create_checkpointer

def my_workflow(state):
    env = os.getenv("ENVIRONMENT")  # ❌ Environment-aware
    if env == "hosted":
        checkpointer = create_checkpointer("postgresql", ...)  # ❌ Infrastructure in workflow
    return {"result": process(state)}
```

**Correct Pattern:**
```python
# ✅ CORRECT
def my_workflow(state: WorkflowState) -> dict:
    # Pure logic, zero infrastructure awareness
    return {"result": process(state)}

# Runtime handles via config/experiment.yaml:
# checkpointer: {type: sqlite, path: ./checkpoints.db}

# Runtime handles via config/hosted.yaml:
# checkpointer: {type: postgresql, url: ${DATABASE_URL}}
```

**Enforcement:** 100% (workflow loader validates before execution)

---

### 2. CONFIG_DRIVEN_INFRASTRUCTURE

**Definition:**
```
All infrastructure (checkpointing, observability, auth) configured in YAML, not coded.
```

**Witness:**
```python
def test_config_driven():
    workflow_file = load_workflow("my_workflow.py")

    # Workflow code must not contain infrastructure
    forbidden_imports = [
        "SqliteSaver", "PostgresSaver",
        "Langfuse(", "LangfuseTracer",
        "FastAPI", "APIRouter"
    ]
    for pattern in forbidden_imports:
        assert pattern not in workflow_file, \
            f"CONFIG_DRIVEN_INFRASTRUCTURE violation: {pattern} in workflow"

    # Config file must define infrastructure
    config = load_config(environment)
    assert "checkpointer" in config
    assert "observability" in config
```

**Violation Example:**
```python
# ❌ VIOLATION
from langfuse import Langfuse
from langgraph.checkpoint.sqlite import SqliteSaver

def my_workflow(state):
    # ❌ Hardcoded infrastructure
    tracer = Langfuse(public_key="...", secret_key="...")
    checkpointer = SqliteSaver.from_conn_string("./db.sqlite")
    ...
```

**Correct Pattern:**
```yaml
# config/experiment.yaml
checkpointer:
  type: sqlite
  path: ./checkpoints/experiment.sqlite

observability:
  enabled: false  # Console only

# config/hosted.yaml
checkpointer:
  type: postgresql
  url: ${DATABASE_URL}
  pool_size: 20

observability:
  enabled: true
  provider: langfuse
  public_key: ${LANGFUSE_PUBLIC_KEY}
  secret_key: ${LANGFUSE_SECRET_KEY}
```

**Enforcement:** 100% (executor rejects workflows with infrastructure imports)

---

### 3. CHANNEL_COORDINATION_PURITY

**Definition:**
```
Nodes MUST return only fields they produce. State spreading ({**state, ...}) is forbidden.
```

**Witness:**
```python
def test_channel_purity(workflow):
    for node_name, node_fn in workflow.nodes.items():
        source = inspect.getsource(node_fn)

        # Detect state spreading anti-pattern
        assert "{**state" not in source, \
            f"CHANNEL_COORDINATION_PURITY violation in {node_name}: state spreading detected"

        # Detect echo-writes
        state_schema = workflow.state_schema
        returned_fields = extract_return_fields(node_fn)
        assert len(returned_fields) <= 3, \
            f"CHANNEL_COORDINATION_PURITY violation in {node_name}: returning {len(returned_fields)} fields (likely spreading)"
```

**Violation Example:**
```python
# ❌ VIOLATION
async def prepare_task(state: WorkflowState) -> WorkflowState:
    return {
        **state,  # ❌ State spreading causes concurrent write errors
        "task": f"Process: {state['input']}",
        "current_step": "preparing"  # ❌ Multiple nodes writing = collision
    }
```

**Correct Pattern:**
```python
# ✅ CORRECT
async def prepare_task(state: WorkflowState) -> dict:
    # Return ONLY what this node produces
    return {
        "task": f"Process: {state['input']}"
    }

# If multiple nodes need to update same field, use Annotated:
from typing import Annotated
from operator import add

class WorkflowState(TypedDict):
    input: str
    task: str
    events: Annotated[list, add]  # ✅ Multiple writers supported
```

**Why This Matters:**
- LangGraph sees `{**state, "field": value}` as "node wants to write ALL fields"
- If topology allows concurrency → InvalidUpdateError
- Channel-first thinking prevents this entirely

**Enforcement:** 90% (static analysis + runtime detection)

---

### 4. HOT_RELOAD_CONTINUITY

**Definition:**
```
File changes MUST trigger reload <500ms without dropping active workflows.
```

**Witness:**
```python
def test_hot_reload():
    # Start workflow in experiment mode
    proc = start_workflow("workflows/test.py", watch=True)

    # Modify workflow file
    modify_workflow("workflows/test.py")

    # Measure reload latency
    start_time = time.time()
    wait_for_reload_complete()
    reload_latency = time.time() - start_time

    assert reload_latency < 0.5, \
        f"HOT_RELOAD_CONTINUITY violation: reload took {reload_latency}s (>500ms)"

    # Verify workflow still works
    result = invoke_workflow({"input": "test"})
    assert result["status"] == "success"
```

**Violation Example:**
```python
# ❌ VIOLATION: Manual restart required
# No hot reload mechanism
# Developer must kill and restart process
# Latency: 2-5 seconds
```

**Correct Pattern:**
```python
# ✅ CORRECT: Automatic hot reload
# runtime/hot_reload.py handles file watching
# Debouncing: 500ms
# State preservation: Active workflows continue
# Reload latency: <500ms
```

**Enforcement:** 100% (measured on every file change in experiment mode)

---

### 5. ZERO_FRICTION_PROMOTION

**Definition:**
```
Workflows MUST run in both experiment and hosted mode without code changes.
```

**Witness:**
```python
def test_zero_friction():
    workflow_file = "workflows/my_workflow.py"

    # Test in experiment mode
    result_experiment = execute_workflow(
        workflow_file,
        environment="experiment",
        input_data={"input": "test"}
    )

    # Test in hosted mode (same file, zero changes)
    result_hosted = execute_workflow(
        workflow_file,
        environment="hosted",
        input_data={"input": "test"}
    )

    # Results must be identical
    assert result_experiment == result_hosted, \
        "ZERO_FRICTION_PROMOTION violation: different behavior across environments"
```

**Violation Example:**
```python
# ❌ VIOLATION
import os

def my_workflow(state):
    if os.getenv("ENVIRONMENT") == "hosted":
        # Different behavior in hosted mode
        return do_hosted_version(state)
    else:
        # Different behavior in experiment mode
        return do_experiment_version(state)
```

**Correct Pattern:**
```python
# ✅ CORRECT
def my_workflow(state: WorkflowState) -> dict:
    # Identical logic regardless of environment
    return {"result": process(state)}

# Environment differences handled by runtime config:
# - experiment: SQLite checkpointer, console logging
# - hosted: PostgreSQL checkpointer, Langfuse tracing
```

**Enforcement:** 100% (CI runs workflows in both modes, asserts identical results)

---

### 6. WITNESS_BASED_COMPLETION

**Definition:**
```
Phase completion requires observable metrics, not implementation claims.
```

**Witness:**
```python
def test_phase_completion(phase: str):
    witness_outcomes = load_witness_outcomes(phase)

    for metric_name, expected_value in witness_outcomes.items():
        actual_value = measure_metric(metric_name)

        assert actual_value == expected_value, \
            f"WITNESS_BASED_COMPLETION violation in {phase}: " \
            f"{metric_name} = {actual_value} (expected {expected_value})"
```

**Examples:**

**R1 (CLI Runtime):**
```yaml
required_witnesses:
  experiment_mode_working: true
  hot_reload_latency: <2s
  console_logs_visible: true
  workflow_completes: true
```

**R4 (Checkpointing):**
```yaml
required_witnesses:
  sqlite_checkpointer_working: true
  state_persistence: true  # Verified across invocations
  session_queryable: true  # GET /sessions/{thread_id} works
  thread_isolation: true   # Different threads = isolated state
```

**Violation Example:**
```
Phase R5 marked complete with:
- ❌ "Implementation finished" (claim, not witness)
- ❌ "Code reviewed and merged" (process, not outcome)
- ❌ "Tests pass" (proxy, not observable behavior)
```

**Correct Pattern:**
```
Phase R5 marked complete with:
- ✅ claude_code_nodes_working: true (measured execution)
- ✅ session_continuity: true (observed state persistence)
- ✅ repository_isolation: true (3 unique repos verified)
- ✅ cost_model: fixed ($20/month documented in metadata)
```

**Enforcement:** 100% (phase gate requires witness measurements)

---

## Constraint Tightening Protocol (LEARNED)

### When to Tighten

**Trigger:** Witness falls below 100% enforcement

**Examples:**
- Hot reload latency exceeds 500ms threshold → reduce debounce timeout
- Environment isolation violated in production → add static analysis check
- Channel purity violations escape detection → strengthen AST analysis

**Process:**
```yaml
1. Detect: Witness metric falls below threshold
2. Analyze: Identify gap in enforcement mechanism
3. Strengthen: Tighten constraint (never relax)
4. Version: Document change with rationale
5. Verify: Confirm witness returns to 100%
```

### Versioning

**Constraint versions track tightening events:**

```yaml
CHANNEL_COORDINATION_PURITY:
  v1.0.0 (2025-11-18): Initial definition
  v1.1.0 (2025-11-24): Added state spreading detection
  v2.0.0 (2025-11-24): Added field count heuristic (<= 3 fields)

  rationale_v2.0: "Multiple workflows violated v1.1 by spreading
    state without literal {**state} pattern. Field count heuristic
    catches 95% of violations. Acceptable false positive rate: 0%."
```

**Truth:** Constraints only tighten, never relax. Decay is visible through witness failures.

---

## Enforcement Mechanisms

### Automatic (100% Coverage)

1. **Workflow Loader:** Validates ENVIRONMENT_ISOLATION before execution
2. **Config Validator:** Enforces CONFIG_DRIVEN_INFRASTRUCTURE at startup
3. **Hot Reload Monitor:** Measures HOT_RELOAD_CONTINUITY on every file change
4. **Integration Tests:** Verify ZERO_FRICTION_PROMOTION in CI
5. **Phase Gates:** Block completion without WITNESS_BASED_COMPLETION

### Manual (Code Review)

1. **PR Template:** Checklist includes all 6 sacred constraints
2. **Reviewer Guide:** Examples of violations and correct patterns
3. **Architecture Review:** Major changes assessed for constraint drift

### Observable (Continuous)

```yaml
# Metrics dashboard tracks constraint health
dashboard_metrics:
  environment_isolation_violations: 0
  config_driven_infrast_violations: 0
  channel_purity_violations: 0
  hot_reload_latency_p99: <500ms
  zero_friction_test_pass_rate: 100%
  witness_coverage: 100%
```

**Alert Threshold:** Any violation count > 0 triggers immediate investigation

---

## Violation Consequences

### Severity Levels

**Level 1: Warning** (Workflow continues, logged)
- Example: Field count heuristic triggered but may be false positive
- Action: Log warning, allow execution, manual review

**Level 2: Rejection** (Workflow blocked, error returned)
- Example: State spreading detected (`{**state, ...}`)
- Action: Refuse execution, return actionable error message

**Level 3: Phase Rollback** (Phase marked incomplete)
- Example: Witness metric falls below threshold after completion
- Action: Revert phase status, re-gate on witness restoration

**Level 4: Primitive Corruption** (Architecture drift detected)
- Example: Runtime becomes environment-aware
- Action: Emergency refactor, all development paused

### User Feedback

**Violations return cognitive guidance, not just error codes:**

```python
# ❌ BAD ERROR MESSAGE
raise InvalidUpdateError("At key 'researcher_output': concurrent update detected")

# ✅ GOOD ERROR MESSAGE
raise InvalidUpdateError(
    "Concurrent write detected on 'researcher_output'.\n\n"
    "Cause: Multiple nodes attempting to write this field simultaneously.\n\n"
    "Common Violations:\n"
    "  1. State spreading: return {**state, 'field': value}\n"
    "  2. Missing inject_before: Topology allows concurrent execution\n\n"
    "Fix:\n"
    "  1. Remove {**state} spread - return only fields this node produces\n"
    "  2. Add inject_before to agent config for sequential execution\n"
    "  3. Use Annotated[list, add] if multiple writers needed\n\n"
    "See: Mental model docs at sacred-core/01-the-project.md#channel-coordination"
)
```

**Truth:** Errors are teaching moments. Guide toward correct mental model.

---

## Knowledge Layer Compliance

**This document contains:**
- ✅ Sacred constraints (ETERNAL - names never change)
- ✅ Witness protocol (ETERNAL - always observable + automatic + continuous + actionable)
- ✅ Enforcement mechanisms (STRUCTURAL - how protection works)
- ✅ Tightening protocol (LEARNED - versioned constraint evolution)

**This document excludes:**
- ❌ Current violation counts (→ 04-current-state.md)
- ❌ Specific measurements (→ 04-current-state.md)
- ❌ Implementation details (→ source code)
- ❌ Phase definitions (→ 01-the-project.md)

---

## Archive Notice

**This document is TIMELESS.**

Once written, this document should NOT be updated except for:
1. Constraint tightening (with versioning + rationale)
2. New sacred constraints (if primitive expands)
3. Witness protocol improvements (with evidence of enforcement gaps)

**This document will be readable decades from now.**

When someone asks "Why does this platform refuse X?", this document answers.
