```yaml
phase: M3
name: Migration Trigger (Measurement)
constraint_removed: Hidden capacity ceiling → Measured metrics with thresholds
tasks: 2
status: pending
created: 2025-11-17
```

# Phase 3: Migration Trigger - Task Summary

## The Sacred Truth

**Visibility unlocks proactive scaling.**

M3.1 removes blind operation (metrics dashboard). M3.2 removes reactive decision-making (objective triggers). Together they unlock knowing WHEN to migrate before hitting capacity ceiling. No crisis scaling.

---

## Task Execution Order

**Sequential Dependency:**
```
M3.1 (Throughput Monitor) ← Must complete first
  ↓
M3.2 (Decision Trigger) ← Depends on M3.1 metrics
```

**Execution Strategy:**
1. Complete M3.1 first (establishes metrics collection)
2. Complete M3.2 second (consumes M3.1 metrics for decisions)

**Time Estimate:**
- M3.1: 3 hours (Prometheus setup + dashboard + alerts)
- M3.2: 2 hours (Decision logic + testing + logging)
- **Total: 5 hours** (sequential execution required)

---

## The Two Tasks

### M3.1: [Integration] Write Throughput Monitor
**Type:** Integration Pressure Point
**File:** `M3.1-write-throughput-monitor.md`

**Witness:** Dashboard displays writes/second, error rate (%), P99 latency with alerts firing at thresholds

**Critical Insight:** You cannot manage what you cannot measure. Metrics remove the "operating blind" constraint. Visibility is the prerequisite for all optimization.

---

### M3.2: [Decision] Migration Trigger Evaluated
**Type:** Business Logic
**File:** `M3.2-migration-trigger-evaluated.md`

**Witness:** Decision matrix returns "MIGRATE NOW - Write errors >1%" when metrics exceed threshold

**Critical Insight:** Objective thresholds remove guesswork. Decision logic converts metrics into action. No more "when should we migrate?" debates - metrics decide.

---

## Phase Completion Witness

**Both features working together:**

```python
from prometheus_api_client import PrometheusConnect

# M3.1: Metrics collection working
prom = PrometheusConnect(url="http://localhost:9090")

error_rate_query = 'rate(checkpoint_writes_total{status="error"}[5m]) / rate(checkpoint_writes_total[5m]) * 100'
throughput_query = 'rate(checkpoint_writes_total[1m])'

error_rate = float(prom.custom_query(error_rate_query)[0]['value'][1])
throughput = float(prom.custom_query(throughput_query)[0]['value'][1])
file_size_gb = os.path.getsize("checkpoints.sqlite") / (1024 ** 3)

# M3.2: Decision logic consuming metrics
metrics = MigrationMetrics(
    error_rate=error_rate,
    writes_per_second=throughput,
    deployment="single-server",
    file_size_gb=file_size_gb,
    timestamp=datetime.now()
)

decision = should_migrate_to_postgresql(metrics)

# Witness: Decision based on real metrics
print(f"Current metrics:")
print(f"  Error rate: {error_rate:.2f}%")
print(f"  Throughput: {throughput:.1f} writes/sec")
print(f"  File size: {file_size_gb:.2f} GB")
print(f"\nDecision: {decision.decision}")
print(f"Justification: {decision.justification}")

# If error_rate >1% or throughput >100/sec:
#   Decision = "MIGRATE NOW"
#   Evidence = M3.2 working
# Else:
#   Decision = "SQLite sufficient"
#   Evidence = M3.2 working (safe condition)
```

**If decision logic responds correctly to all threshold conditions, M3 is complete.**

---

## Success Metrics (Non-Negotiable)

```yaml
M3.1_witness:
  metrics_collection_working: true
  dashboard_showing_data: true
  alerts_configured: true
  alert_firing_tested: true

M3.2_witness:
  decision_logic_implemented: true
  all_triggers_tested: true
  decisions_logged: true
  metric_integration_working: true
```

---

## Anti-Patterns (Emergence Violations)

**DO NOT BUILD:**
- ❌ Custom metrics aggregation (Prometheus does this)
- ❌ Complex ML-based anomaly detection (thresholds work)
- ❌ Custom alerting infrastructure (AlertManager exists)
- ❌ Manual decision spreadsheets (decision logic automates)

**If you built ANY of the above, you violated simplicity.**

**ONLY BUILD:**
- ✅ Prometheus instrumentation (M3.1)
- ✅ Grafana dashboard (M3.1)
- ✅ AlertManager rules (M3.1)
- ✅ Decision function with thresholds (M3.2)
- ✅ Decision logging (M3.2)

---

## Constraint Compliance

**CONTEXT_PRESERVATION:**
- Metrics retained 7 days (temporal analysis possible)
- Decision history logged (understand scaling decisions over time)
- Historical context enables learning from past triggers

**CONSTRAINT_INHERITANCE:**
- Instrumentation inherited by all checkpoint operations
- Decision framework inherited by future scaling decisions
- Threshold patterns reusable for PostgreSQL → distributed DB

**TRACE_REQUIRED:**
- Every checkpoint write measured and traceable
- Every decision logged with metrics and justification
- Full audit trail of system performance and scaling choices

**RESOURCE_STEWARDSHIP:**
- Minimal instrumentation overhead (<1ms per write)
- Metrics auto-expire after 7 days (no unbounded growth)
- Decision logic runs daily (low CPU cost)

**RESIDUE_FREE:**
- Metrics expire automatically (no manual cleanup)
- Decisions logged in structured format (no cruft)
- Clean separation: metrics in Prometheus, decisions in log

---

## Migration to M4 Trigger

**When to move to M4:**
- M3 complete (metrics + decision logic working)
- Decision function returns "MIGRATE NOW" based on actual metrics
- Production deployment approaching capacity ceiling
- Multi-server deployment planned

**Do NOT migrate if:**
- Decision function returns "SQLite sufficient"
- Error rate <1%, throughput <80/sec, single-server
- No production scaling pressure

**M4 unlocks:**
- PostgreSQL migration (network-accessible DB)
- Multi-server deployment capability
- 1000+ writes/sec capacity
- Horizontal scaling

---

## Documentation Updates After M3

**Files to Update:**
- `04-current-state.md` - Mark M3 tasks complete, record decision
- Evidence artifacts (dashboard screenshots, decision logs, metric data)

**Files NOT to Update:**
- `01-the-project.md` (eternal/structural only)
- `02-the-discipline.md` (eternal/learned only)
- `03-implementation-plan.md` (structural task definitions)

**Archive:**
- Grafana dashboard JSON
- Prometheus configuration
- AlertManager rules
- Decision log history
- Metric data snapshots

---

## The Visibility Principle Proven

**Before M3:** Operating blind, reactive scaling, crisis-driven migration
**After M3:** Full visibility, proactive scaling, metric-driven decisions

**Total Constraints Removed:** 2
- Operating blind → Metrics dashboard
- Reactive decisions → Objective triggers

**This is the proof of visibility: Measurement enables proactive operation, not reactive firefighting.**

---

## Critical Decision Point

**M3 is the decision phase - M4 is the action phase.**

If M3.2 returns "MIGRATE NOW", proceed to M4 (PostgreSQL migration).
If M3.2 returns "SQLite sufficient", stay on M2 (production ready with SQLite).

**The metrics decide, not opinions.**
