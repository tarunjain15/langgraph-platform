```yaml
name: LangGraph Platform - The Discipline
description: Sacred constraints protecting the runtime primitive. Eternal truth (constraint names, witness protocol) + learned thresholds (versioned, tightening).
created: 2025-11-18
```

# LangGraph Platform: The Discipline

## What This Protects (ETERNAL)

**Threat to Primitive:**
```
Workflow Runtime Corruption = Workflows become environment-aware, destroying isolation boundary
```

**Symptoms of Corruption:**
- Workflows check `os.getenv("ENVIRONMENT")`
- Workflows import runtime internals
- Workflows hardcode checkpointer/tracer
- Environment config lives in workflow code
- Experiment mode ≠ Hosted mode requires code changes

**Result:** Runtime becomes useless library, environment boundary collapses

---

## The Five Sacred Constraints (ETERNAL)

### 1. ENVIRONMENT_ISOLATION

**Definition:**
```
Workflows MUST be environment-agnostic. Runtime injects all infrastructure.
```

**Witness (Observable, Automatic, Continuous, Actionable):**
```python
# Test runs on every workflow execution
def test_environment_isolation(workflow_code):
    forbidden_imports = [
        "from platform.runtime",
        "from platform.config",
        "os.getenv(\"ENVIRONMENT\")",
        "if environment ==",
    ]
    for pattern in forbidden_imports:
        assert pattern not in workflow_code, f"Violation: {pattern} found in workflow"
```

**Violation Example:**
```python
# ❌ VIOLATION
def my_workflow(state):
    env = os.getenv("ENVIRONMENT")  # ❌ Environment-aware
    if env == "hosted":
        checkpointer = PostgresSaver(...)  # ❌ Infrastructure in workflow
    ...
```

**Correct Pattern:**
```python
# ✅ CORRECT
def my_workflow(state):
    # Pure logic, no environment awareness
    return {"result": process(state)}

# Runtime config (config/experiment.yaml):
# checkpointer:
#   type: sqlite
#   path: ./checkpoints.db

# Runtime config (config/hosted.yaml):
# checkpointer:
#   type: postgresql
#   url: ${DATABASE_URL}
```

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
    assert "SqliteSaver" not in workflow_file
    assert "PostgresSaver" not in workflow_file
    assert "Langfuse(" not in workflow_file
    assert "FastAPI(" not in workflow_file

    # Config file must contain infrastructure
    config = load_config("workflows/config.yaml")
    assert "checkpointer" in config
    assert "observability" in config
```

**Violation Example:**
```python
# ❌ VIOLATION
from langgraph.checkpoint.sqlite import SqliteSaver

def my_workflow(state):
    checkpointer = SqliteSaver("checkpoints.db")  # ❌ Hardcoded infrastructure
    ...
```

**Correct Pattern:**
```yaml
# workflows/config.yaml
workflows:
  my_workflow:
    file: my_workflow.py
    checkpointing:
      enabled: true  # ✅ Config-driven
    observability:
      langfuse: true  # ✅ Config-driven
```

---

### 3. HOT_RELOAD_CONTINUITY

**Definition:**
```
File changes in experiment mode must trigger restart <2s without breaking running workflows.
```

**Witness:**
```python
def test_hot_reload():
    # Start workflow
    start = time.time()
    result1 = run_workflow("my_workflow", {"input": "test"})

    # Modify workflow file
    modify_workflow_file("my_workflow.py", add_log_line)

    # Detect reload
    elapsed = wait_for_reload()
    assert elapsed < 2.0, f"Reload took {elapsed}s (>2s limit)"

    # Verify continuity (session preserved)
    result2 = run_workflow("my_workflow", {"input": "test2"})
    assert result2["session_history"] includes result1
```

**Violation Example:**
```python
# Runtime that loses session state on reload
def hot_reload():
    kill_process()  # ❌ Destroys checkpoints
    start_new_process()  # ❌ New session, lost continuity
```

**Correct Pattern:**
```python
# Runtime preserves checkpoints across reloads
def hot_reload():
    checkpoint_manager.flush()  # ✅ Persist state
    reload_module("workflow")   # ✅ Reload code only
    checkpoint_manager.resume() # ✅ Restore session
```

---

### 4. ZERO_FRICTION_PROMOTION

**Definition:**
```
Experiment → Hosted transition requires ZERO workflow code changes. Config changes only.
```

**Witness:**
```python
def test_zero_friction():
    workflow_code = read_file("workflows/my_workflow.py")

    # Run in experiment mode
    result1 = cli("run my_workflow")
    code_hash1 = hash(workflow_code)

    # Promote to hosted mode
    result2 = cli("serve my_workflow")
    code_hash2 = hash(workflow_code)

    # Code must be identical
    assert code_hash1 == code_hash2, "Code changed during promotion"

    # Environment must be different
    assert result1.checkpointer_type == "sqlite"
    assert result2.checkpointer_type == "postgresql"
```

**Violation Example:**
```python
# Workflow requires modification for hosting
def my_workflow(state):
    # ❌ Must change this line for hosted mode
    checkpointer = SqliteSaver("checkpoints.db")
    ...
```

**Correct Pattern:**
```bash
# Same workflow code works in both modes
$ lgp run my_workflow     # → SQLite, console logs
$ lgp serve my_workflow   # → PostgreSQL, Langfuse traces
# Zero code changes
```

---

### 5. WITNESS_BASED_COMPLETION

**Definition:**
```
Task completion proven by observable outcome, not by status checkbox.
```

**Witness:**
```python
def test_task_completion(task_id):
    task = get_task(task_id)

    # Status checkbox is NOT sufficient
    assert task.status == "complete"  # Necessary but not sufficient

    # Witness outcome is REQUIRED
    outcome = task.witness_outcome
    assert outcome is not None, "Task marked complete without witness"
    assert is_observable(outcome), "Witness not observable"
    assert is_automatic(outcome), "Witness not automatic"
```

**Violation Example:**
```markdown
## Task R1.1: CLI Runtime
**Status:** ✅ Complete
**Completed:** 2025-11-18
<!-- ❌ No witness, just status -->
```

**Correct Pattern:**
```markdown
## Task R1.1: CLI Runtime
**Witness Outcome:**
- `lgp run` command executes workflow
- Hot reload triggers on file save (<2s)
- Console logs show execution trace
- SQLite checkpointer creates tables

**Acceptance Criteria:**
```bash
$ lgp run my_workflow
[lgp] Hot reload: ON
[lgp] Workflow complete (5.2s)
```
```

---

## Witness Protocol (ETERNAL)

### The Four Requirements

Every witness MUST be:

1. **Observable:** Can be measured objectively (not "feels fast")
2. **Automatic:** No manual verification required (CI/CD testable)
3. **Continuous:** Verified on every execution (not one-time)
4. **Actionable:** Violation triggers clear action (fix or block)

### Witness Types

**Good Witnesses:**
```yaml
hot_reload_latency: <2s                    # Observable: measured
api_responds: true                         # Automatic: HTTP 200
checkpointer_tables_exist: true            # Continuous: SELECT * FROM checkpoints
environment_isolation_enforced: true       # Actionable: grep workflow for violations
```

**Bad Witnesses:**
```yaml
code_quality: good                         # ❌ Not observable (subjective)
developer_satisfaction: high               # ❌ Not automatic (survey required)
performance: acceptable                    # ❌ Not continuous (one-time test)
best_practices: followed                   # ❌ Not actionable (vague)
```

---

## Enforcement Mechanisms (ETERNAL)

### Automatic Enforcement

**Pre-Commit Hooks:**
```python
# .git/hooks/pre-commit
def check_environment_isolation():
    for workflow in get_workflows():
        code = read_file(workflow)
        violations = scan_for_violations(code)
        if violations:
            print(f"❌ ENVIRONMENT_ISOLATION violated in {workflow}")
            print(f"   Found: {violations}")
            exit(1)
```

**Runtime Guards:**
```python
# runtime/executor.py
def execute_workflow(workflow):
    # Check isolation before execution
    if not is_environment_agnostic(workflow.code):
        raise EnvironmentIsolationViolation(
            f"Workflow {workflow.name} contains environment-aware code"
        )
    ...
```

**CI/CD Tests:**
```python
# tests/test_constraints.py
def test_all_constraints():
    for workflow in discover_workflows():
        assert_environment_isolation(workflow)
        assert_config_driven(workflow)
        assert_zero_friction(workflow)
```

### Manual Enforcement

**Code Review Checklist:**
- [ ] Workflow code is environment-agnostic
- [ ] Infrastructure in config, not code
- [ ] Hot reload tested (<2s)
- [ ] Experiment → Hosted requires zero code changes
- [ ] Task completion has witness outcome

**Phase Completion Gate:**
```
Phase cannot advance until:
1. All witnesses observed ✅
2. All constraints verified ✅
3. No active violations ✅
```

---

## Constraint Evolution (LEARNED)

### Hot Reload Latency

**V1 (Initial - Too Loose):**
```yaml
hot_reload_latency: <5s
rationale: "Arbitrary guess"
```

**V2 (First Tightening):**
```yaml
hot_reload_latency: <2s
rationale: "5s felt too slow in practice. Developer feedback: 'I lose flow state waiting >2s.'"
date: 2025-11-18
```

**V3 (Future Tightening - Example):**
```yaml
hot_reload_latency: <1s
rationale: "Achieved <1s with incremental module reload. Previous 2s included full restart."
date: TBD
```

**Direction:** One-way tightening (never relax)

---

### Checkpoint Size Limit (PostgreSQL Phase)

**V1 (Initial - Inherited from checkpoint-mastery):**
```yaml
checkpoint_size_limit: 10MB
checkpoint_size_warning: 5MB
rationale: "Proven in M2.5 of checkpoint-mastery. Blob externalization required beyond 10MB."
date: 2025-11-18
```

**V2 (Future Tightening - Example):**
```yaml
checkpoint_size_limit: 5MB
checkpoint_size_warning: 2MB
rationale: "10MB checkpoints caused PostgreSQL write timeouts at 500+ writes/sec. Tightened to 5MB."
date: TBD
previous: V1 (10MB)
```

---

### API Response Time (Hosted Mode)

**V1 (Initial Target):**
```yaml
api_response_p99: <500ms
rationale: "Standard web API expectation. Includes workflow execution + checkpoint write."
date: 2025-11-18
```

**V2 (Future Tightening - Example):**
```yaml
api_response_p99: <200ms
rationale: "Achieved <200ms with connection pooling (PgBouncer). Previous 500ms included connection acquisition overhead."
date: TBD
previous: V1 (500ms)
```

---

## Sacred Primitive Derivation (ETERNAL)

**How constraints protect the primitive:**

```
Workflow Runtime = Environment-isolated execution engine
         ↓
  ENVIRONMENT_ISOLATION
  (Workflows must not be environment-aware)
         ↓
  CONFIG_DRIVEN_INFRASTRUCTURE
  (Infrastructure in config, not code)
         ↓
  ZERO_FRICTION_PROMOTION
  (Same code works in all environments)
         ↓
  HOT_RELOAD_CONTINUITY
  (Experiment mode must enable rapid iteration)
         ↓
  WITNESS_BASED_COMPLETION
  (Completion must be provable, not claimed)
```

**Each constraint derives from protecting the runtime boundary.**

Removing any constraint allows:
- Workflows becoming environment-aware (primitive corruption)
- Infrastructure hardcoded in workflow (environment boundary collapse)
- Code changes required for hosting (friction introduced)
- Lost session state on reload (experiment mode broken)
- False completion claims (no proof)

---

## Constraint Violations (LEARNED - Examples)

### Example 1: Environment Awareness

**Violation:**
```python
def my_workflow(state):
    if os.getenv("ENVIRONMENT") == "production":
        use_postgresql()
    else:
        use_sqlite()
```

**Detection:** Pre-commit hook catches `os.getenv("ENVIRONMENT")`
**Action:** Block commit, show correct pattern
**Resolution:** Move to config, workflow code removed environment logic

---

### Example 2: Hardcoded Infrastructure

**Violation:**
```python
from langfuse import Langfuse

def my_workflow(state):
    langfuse = Langfuse()  # ❌ Hardcoded observability
    ...
```

**Detection:** Runtime scan finds `Langfuse()` import
**Action:** Workflow execution blocked
**Resolution:** Remove Langfuse import, enable in config

---

### Example 3: Slow Hot Reload

**Violation:**
```
File saved → 3.5s → Workflow reloaded
```

**Detection:** Automatic timing test on file watch
**Action:** Alert developer, identify bottleneck
**Resolution:** Switch from full restart to module reload (achieved <1s)

---

## Knowledge Layer Compliance

**This document contains:**
- ✅ Sacred constraints (ETERNAL - names, definitions)
- ✅ Witness protocol (ETERNAL - structure)
- ✅ Enforcement mechanisms (ETERNAL - categories)
- ✅ Constraint evolution (LEARNED - versioned thresholds)
- ✅ Primitive derivation (ETERNAL - how constraints protect primitive)

**This document excludes:**
- ❌ Current violations (→ 04-current-state.md)
- ❌ Incident timestamps (→ 04-current-state.md)
- ❌ Actual measurements (→ 04-current-state.md)
- ❌ Project definition (→ 01-the-project.md)
- ❌ Task definitions (→ 03-implementation-plan.md)

---

## Archive Notice

**This document is MOSTLY TIMELESS.**

**Never Changes:**
- Constraint names
- Witness protocol structure
- Enforcement mechanism categories
- Primitive derivation logic

**Changes Only Through Tightening:**
- Learned thresholds (versioned with rationale)
- Violation examples (add, never remove)

**This document will be readable decades from now.**
