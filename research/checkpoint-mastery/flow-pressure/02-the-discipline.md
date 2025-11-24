```yaml
name: The Discipline - Sacred Constraints
description: The immutable laws that protect this project from entropy, overbuild, and false emergence.
```

# The Discipline

## What This Protects

This discipline protects against:
- **Feature Creep** - Building what already emerges
- **Premature Optimization** - Solving problems that don't exist yet
- **Constraint Violation** - Breaking sacred limits
- **False Emergence** - Claiming features were built when they emerged
- **Residue Accumulation** - Leaving unclear artifacts

---

## The Five Sacred Constraints

### 1. CONTEXT_PRESERVATION
**Maintain continuity across time**

**What This Means:**
- No conversation memory is lost across invocations
- No state is orphaned
- All checkpoints are traceable to their thread_id
- TTL-based cleanup is automatic, not manual

**What This Prevents:**
- Session recovery failures
- Orphaned state in database
- Context loss across sessions
- Manual cleanup burden

**Witness:**
- Session recovery rate: 100%
- Zero orphaned checkpoints
- All thread_ids traceable
- Automatic TTL cleanup working

**Violation Example:**
```python
# WRONG: Losing context
checkpoint = save_checkpoint(state)
# ... later, context lost because thread_id not preserved

# RIGHT: Context preserved
config = {"configurable": {"thread_id": "user-123"}}
checkpoint = save_checkpoint(state, config)
# ... later, same thread_id = conversation continues
```

---

### 2. CONSTRAINT_INHERITANCE
**Children obey parent constraints**

**What This Means:**
- All child processes inherit parent constraints
- No child can violate parent's sacred limits
- Constraint propagation is automatic, not manual
- Violations are detected and blocked

**What This Prevents:**
- Child processes breaking global limits
- Inconsistent constraint enforcement
- Manual constraint checking
- Cascade failures

**Witness:**
- Zero constraint violations in child agents
- Agent errors isolated (no cascading failures)
- Automatic constraint propagation
- Violation detection <500ms

**Violation Example:**
```python
# WRONG: Child ignores parent constraint
parent_agent.max_cost = 1.00
child_agent = spawn_child()
child_agent.spend(2.00)  # Violates parent constraint

# RIGHT: Child inherits constraint
parent_agent.max_cost = 1.00
child_agent = spawn_child(inherit_constraints=True)
child_agent.spend(2.00)  # Blocked: exceeds inherited limit
```

---

### 3. TRACE_REQUIRED
**Every decision must be traceable**

**What This Means:**
- All LLM calls traced in Langfuse
- All state transitions logged
- All errors tracked with full context
- All decisions have audit trail

**What This Prevents:**
- Unaccountable decisions
- Lost debugging context
- Untraceable failures
- Budget overruns

**Witness:**
- 100% LLM call coverage in traces
- Full state transition history
- Error propagation tracked
- Budget alerts before 90% threshold

**Violation Example:**
```python
# WRONG: Untraced LLM call
response = llm.invoke(prompt)  # No trace

# RIGHT: Traced LLM call
with langfuse.trace(name="decision") as trace:
    response = llm.invoke(prompt)
    trace.log(cost=calculate_cost(response))
```

---

### 4. RESOURCE_STEWARDSHIP
**Use minimum necessary resources**

**What This Means:**
- No overprovisioning
- No premature optimization
- Cost-aware model selection
- Automatic resource cleanup

**What This Prevents:**
- Wasted compute
- Budget exhaustion
- Unbounded growth
- Resource leaks

**Witness:**
- Monthly cost reduction through optimization
- No orphaned resources
- Budget constraints enforced
- Model downgrade on pressure

**Violation Example:**
```python
# WRONG: Always use most expensive model
model = "claude-opus-4"  # Expensive

# RIGHT: Cost-aware model selection
if task.complexity < 0.5:
    model = "claude-haiku-4"  # Cheap
else:
    model = "claude-sonnet-4.5"  # Balanced
```

---

### 5. RESIDUE_FREE
**Leave no unclear artifacts**

**What This Means:**
- No plaintext secrets in logs
- No orphaned temporary files
- No unclear state transitions
- Clean dissolution on shutdown

**What This Prevents:**
- Secret exposure
- Disk space leaks
- Unclear system state
- Memory leaks

**Witness:**
- Zero secrets exposed in logs/git
- No orphaned temp files
- Memory cleared on exit
- Clean shutdown verified

**Violation Example:**
```python
# WRONG: Secret in log
logger.info(f"API key: {api_key}")  # Exposed

# RIGHT: Secret never logged
logger.info("API key loaded from vault")
# api_key used but never logged
```

---

## The Enforcement Mechanism

### Automatic Enforcement
- **Type System** - Constraints encoded in types
- **Runtime Checks** - Violations detected at execution
- **Budget Limits** - Cost constraints enforced
- **TTL Cleanup** - Automatic resource cleanup

### Manual Enforcement
- **Code Review** - Constraint violations caught in review
- **Testing** - Constraint tests in test suite
- **Documentation** - Constraints documented in code
- **Auditing** - Regular constraint audits

---

## The Witness Protocol

Every constraint must have a **witness**—an observable result that proves the constraint is honored.

### Witness Requirements:
1. **Observable** - Can be measured objectively
2. **Automatic** - Does not require manual verification
3. **Continuous** - Verified on every execution
4. **Actionable** - Violation triggers clear action

### Example Witnesses:

**CONTEXT_PRESERVATION:**
- `session_recovery_rate = 100%`
- `orphaned_checkpoints = 0`

**CONSTRAINT_INHERITANCE:**
- `child_constraint_violations = 0`
- `cascade_failures = 0`

**TRACE_REQUIRED:**
- `llm_call_coverage = 100%`
- `trace_ingestion_latency < 1s`

**RESOURCE_STEWARDSHIP:**
- `monthly_cost_trend = decreasing`
- `orphaned_resources = 0`

**RESIDUE_FREE:**
- `secrets_in_logs = 0`
- `temp_files_on_exit = 0`

---

## The Consequence of Violation

When a constraint is violated:

1. **Immediate** - Operation is blocked or rolled back
2. **Visible** - Violation is logged with full context
3. **Traceable** - Violation is traced to source
4. **Actionable** - Clear remediation path provided

**No violations are tolerated. No exceptions are granted.**

---

## The Evolution of Constraints

Constraints can only evolve in **one direction**: **more strict**.

- **Never** relax a constraint without justification
- **Always** tighten constraints when violations detected
- **Document** all constraint changes with rationale
- **Test** constraint changes thoroughly

**Example:**
```
# V1: Checkpoint size limit = 50MB (too loose)
# V2: Checkpoint size limit = 10MB (tightened)
# V3: Checkpoint size limit = 10MB, rejection at 5MB (early warning)
```

---

## The Sacred Primitive

**Checkpoints = BSP state snapshots indexed by thread_id.**

This constraint is **never violated**. This constraint is **never relaxed**. This constraint is **the foundation**.

All other constraints derive from protecting this primitive:
- CONTEXT_PRESERVATION protects thread_id continuity
- CONSTRAINT_INHERITANCE protects checkpoint integrity
- TRACE_REQUIRED protects checkpoint observability
- RESOURCE_STEWARDSHIP protects checkpoint efficiency
- RESIDUE_FREE protects checkpoint security

**The primitive is sacred. The discipline protects the primitive.**
