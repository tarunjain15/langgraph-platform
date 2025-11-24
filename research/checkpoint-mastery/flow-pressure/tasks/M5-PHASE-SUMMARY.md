```yaml
phase: M5
name: Advanced Optimization (Performance)
constraint_removed: Connection overhead + full table scans → Pooling + indexed queries
tasks: 4
status: pending
created: 2025-11-17
```

# Phase 5: Advanced Optimization - Task Summary

## The Sacred Truth

**Optimization unlocks 25x speedup.**

M5.1-M5.2 remove database bottlenecks (connection pooling + indexes). M5.3-M5.4 remove operational risks (monitoring + backups). Together: 50ms → 2ms queries, disaster recovery ready.

---

## Task Execution Order

```
M5.1 (Connection Pooling) ┐
M5.2 (Index Creation)     ├── All parallel (independent optimizations)
M5.3 (Dashboard)          │
M5.4 (Backup/Restore)     ┘
```

**Time Estimate:** 6 hours (all tasks parallelizable)

---

## The Four Tasks

### M5.1: Connection Pooling
**Witness:** Connection acquisition 50ms → 5ms (10x improvement)

### M5.2: Index Creation
**Witness:** Query time 50ms → 2ms (25x improvement)

### M5.3: Performance Dashboard
**Witness:** 6-panel Grafana dashboard showing real-time PostgreSQL metrics

### M5.4: Backup & Restore
**Witness:** Restore from 24h-old backup succeeds, data verified

---

## Success Metrics

```yaml
M5_complete:
  connection_time: <10ms (was 50ms)
  query_time: <5ms (was 50ms)
  dashboard: operational
  backup_tested: true
```

---

## Migration to M6 Trigger

**When:** M5 complete + need for cross-thread knowledge sharing

**M6 unlocks:** LangGraph Store, hybrid memory architecture, cross-thread learning
