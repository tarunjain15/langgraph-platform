```yaml
name: Task Index - Complete Execution Map
description: All 28 tasks across 7 irreversible phase shifts, from SQLite foundation to production mastery
created: 2025-11-17
```

# Task Index

## Overview

**Total Tasks:** 28
**Total Phases:** 7
**Methodology:** Witness-Completion (each task proven by observable truth)
**Framework:** Filesystem-based (no external tracking systems)

---

## The 7 Phase Shifts

### Phase 1: Foundation (M1) - 5 Tasks
**Constraint Removed:** No persistent state → File-based SQLite checkpointing
**What Emerges:** Session Memory, Time Travel, HITL, Fault Tolerance

**Tasks:**
- [M1.1](M1.1-sqlite-checkpointer-setup.md) - SQLite Checkpointer Setup (Integration)
- [M1.2](M1.2-session-memory-unlocked.md) - Session Memory Unlocked (Feature)
- [M1.3](M1.3-time-travel-unlocked.md) - Time Travel Unlocked (Feature)
- [M1.4](M1.4-human-in-the-loop-unlocked.md) - Human-in-the-Loop Unlocked (Feature)
- [M1.5](M1.5-fault-tolerance-unlocked.md) - Fault Tolerance Unlocked (Feature)

**Phase Summary:** [M1-PHASE-SUMMARY.md](M1-PHASE-SUMMARY.md)

**Key Witness:** 3-line SQLite setup unlocks all 4 emergent features

---

### Phase 2: Production Ready (M2) - 5 Tasks
**Constraint Removed:** Synchronous blocking I/O → Async non-blocking + blob externalization
**What Changes:** 10+ concurrent invocations, 5MB → 50 bytes checkpoints, 500ms → <10ms serialization

**Tasks:**
- [M2.1](M2.1-async-checkpointer-migration.md) - Async Checkpointer Migration (Integration)
- [M2.2](M2.2-blob-storage-integration.md) - Blob Storage Integration (Integration)
- [M2.3](M2.3-checkpoint-metadata-filtering.md) - Checkpoint Metadata Filtering (Integration)
- [M2.4](M2.4-checkpoint-pruning-strategy.md) - Checkpoint Pruning Strategy (Feature)
- [M2.5](M2.5-size-limit-enforcement.md) - Size Limit Enforcement (Constraint)

**Phase Summary:** [M2-PHASE-SUMMARY.md](M2-PHASE-SUMMARY.md)

**Key Witness:** 10 concurrent async invocations succeed without database locks

---

### Phase 3: Migration Trigger (M3) - 2 Tasks
**Constraint Recognized:** Hidden capacity ceiling → Measured metrics with thresholds
**What Changes:** Observability layer, migration thresholds, decision automation

**Tasks:**
- [M3.1](M3.1-write-throughput-monitor.md) - Write Throughput Monitor (Measurement)
- [M3.2](M3.2-migration-trigger-evaluated.md) - Migration Trigger Evaluated (Decision)

**Phase Summary:** [M3-PHASE-SUMMARY.md](M3-PHASE-SUMMARY.md)

**Key Witness:** Dashboard shows real-time metrics, alert triggers at migration threshold

---

### Phase 4: PostgreSQL Migration (M4) - 6 Tasks
**Constraint Removed:** File-based local storage → Network-accessible database (IRREVERSIBLE)
**What Changes:** Distributed deployment, 500+ writes/sec, multi-server architecture

**Tasks:**
- [M4.1](M4.1-postgresql-provisioning.md) - PostgreSQL Provisioning (Integration)
- [M4.2](M4.2-postgresql-schema-creation.md) - PostgreSQL Schema Creation (Integration)
- [M4.3](M4.3-data-export-from-sqlite.md) - Data Export from SQLite (Migration)
- [M4.4](M4.4-data-import-to-postgresql.md) - Data Import to PostgreSQL (Migration)
- [M4.5](M4.5-data-integrity-check.md) - Data Integrity Check (Verification)
- [M4.6](M4.6-blue-green-cutover.md) - Blue-Green Cutover (Integration - IRREVERSIBLE)

**Phase Summary:** [M4-PHASE-SUMMARY.md](M4-PHASE-SUMMARY.md)

**Key Witness:** 100% production traffic on PostgreSQL with zero data loss

---

### Phase 5: Advanced Optimization (M5) - 4 Tasks
**Constraint Removed:** Connection overhead (50ms) + full table scans (50ms) → Pooling (5ms) + indexed queries (2ms)
**What Changes:** 10x connection speed, 25x query speed, all operations <5ms P99

**Tasks:**
- [M5.1](M5.1-connection-pooling.md) - Connection Pooling (Optimization)
- [M5.2](M5.2-index-creation.md) - Index Creation (Optimization)
- [M5.3](M5.3-performance-dashboard.md) - Performance Dashboard (Measurement)
- [M5.4](M5.4-backup-restore.md) - Backup & Restore (Operations)

**Phase Summary:** [M5-PHASE-SUMMARY.md](M5-PHASE-SUMMARY.md)

**Key Witness:** All checkpoint operations <5ms P99 latency

---

### Phase 6: Next Leverage Pool (M6) - 3 Tasks
**Constraint Removed:** Thread isolation → Cross-thread knowledge sharing
**What Emerges:** Two-tier memory architecture, cross-thread retrieval, company knowledge base

**Tasks:**
- [M6.1](M6.1-langraph-store-setup.md) - LangGraph Store Setup (Integration)
- [M6.2](M6.2-cross-thread-knowledge-retrieval.md) - Cross-Thread Knowledge Retrieval (Feature)
- [M6.3](M6.3-hybrid-memory-architecture.md) - Hybrid Memory Architecture (Architecture)

**Phase Summary:** [M6-PHASE-SUMMARY.md](M6-PHASE-SUMMARY.md)

**Key Witness:** Agent in thread A retrieves knowledge from thread B without checkpoint pollution

---

### Phase 7: Production Mastery (M7) - 3 Tasks
**Constraint Removed:** Manual intervention + uniform storage cost → Autonomous operations + tiered storage
**What Changes:** Auto-scaling, 96% cost reduction ($3,680 → $126/month), zero manual intervention

**Tasks:**
- [M7.1](M7.1-auto-scaling-based-on-metrics.md) - Auto-Scaling Based on Metrics (Automation)
- [M7.2](M7.2-checkpoint-tiering-strategy.md) - Checkpoint Tiering Strategy (Optimization)
- [M7.3](M7.3-anomaly-detection.md) - Anomaly Detection (Intelligence)

**Phase Summary:** [M7-PHASE-SUMMARY.md](M7-PHASE-SUMMARY.md)

**Key Witness:** Autonomous operations with 96% cost reduction and proactive anomaly detection

---

## Execution Sequence

### Sequential Phases (MUST complete in order)
```
M1 → M2 → M3 → M4 → M5 → M6 → M7
```

**Why Sequential:**
- M2 requires M1's infrastructure (SQLite checkpointing)
- M3 requires M2's concurrency (measurement under load)
- M4 requires M3's metrics (migration decision)
- M5 requires M4's PostgreSQL (performance optimization)
- M6 requires M5's performance (cross-thread queries)
- M7 requires M6's architecture (autonomous operations)

### Parallel Tasks (within each phase)

**M1 (Foundation):**
```
M1.1 (Setup)
  ↓
M1.2 | M1.3 | M1.4 | M1.5  (All witness emergent features in parallel)
```

**M2 (Production Ready):**
```
M2.1 (Async) → M2.2 | M2.3 (parallel) → M2.4 | M2.5 (parallel)
```

**M3 (Migration Trigger):**
```
M3.1 (Metrics) → M3.2 (Decision)
```

**M4 (PostgreSQL Migration):**
```
M4.1 | M4.2 (parallel) → M4.3 → M4.4 → M4.5 → M4.6
```

**M5 (Advanced Optimization):**
```
M5.1 | M5.2 | M5.3 | M5.4  (All parallel)
```

**M6 (Knowledge Sharing):**
```
M6.1 → M6.2 | M6.3 (parallel)
```

**M7 (Production Mastery):**
```
M7.1 | M7.2 | M7.3  (All parallel)
```

---

## Witness-Completion Methodology

### What is a Witness?

A witness is an **observable truth that can ONLY exist if the task succeeded**.

**Not a witness:**
- Status checkbox ("marked complete")
- Code written ("implementation done")
- Test passed ("unit test green")

**True witnesses:**
- M1.1: `checkpoints.sqlite` file exists with WAL mode (cannot exist without setup)
- M2.2: 5MB PDF → <5KB checkpoint (cannot exist without blob externalization)
- M4.6: 100% traffic on PostgreSQL (cannot exist without cutover)
- M7.2: $126/month cost (cannot exist without tiering strategy)

### Witness Protocol

**For each task:**
1. Read task file
2. Execute code pattern
3. Verify witness exists (observable outcome)
4. Collect evidence artifacts
5. Update `04-current-state.md` with witness outcome
6. Task complete when witness observed (not when status marked)

**Completion is objective:** If the witness exists, the task succeeded. No subjective judgment needed.

---

## File Structure

```
tasks/
├── TEMPLATE.md                     # Universal witness-completion template
├── INDEX.md                        # This file
│
├── M1.1-sqlite-checkpointer-setup.md
├── M1.2-session-memory-unlocked.md
├── M1.3-time-travel-unlocked.md
├── M1.4-human-in-the-loop-unlocked.md
├── M1.5-fault-tolerance-unlocked.md
├── M1-PHASE-SUMMARY.md
│
├── M2.1-async-checkpointer-migration.md
├── M2.2-blob-storage-integration.md
├── M2.3-checkpoint-metadata-filtering.md
├── M2.4-checkpoint-pruning-strategy.md
├── M2.5-size-limit-enforcement.md
├── M2-PHASE-SUMMARY.md
│
├── M3.1-write-throughput-monitor.md
├── M3.2-migration-trigger-evaluated.md
├── M3-PHASE-SUMMARY.md
│
├── M4.1-postgresql-provisioning.md
├── M4.2-postgresql-schema-creation.md
├── M4.3-data-export-from-sqlite.md
├── M4.4-data-import-to-postgresql.md
├── M4.5-data-integrity-check.md
├── M4.6-blue-green-cutover.md
├── M4-PHASE-SUMMARY.md
│
├── M5.1-connection-pooling.md
├── M5.2-index-creation.md
├── M5.3-performance-dashboard.md
├── M5.4-backup-restore.md
├── M5-PHASE-SUMMARY.md
│
├── M6.1-langraph-store-setup.md
├── M6.2-cross-thread-knowledge-retrieval.md
├── M6.3-hybrid-memory-architecture.md
├── M6-PHASE-SUMMARY.md
│
├── M7.1-auto-scaling-based-on-metrics.md
├── M7.2-checkpoint-tiering-strategy.md
├── M7.3-anomaly-detection.md
└── M7-PHASE-SUMMARY.md
```

---

## Success Metrics

### Phase Completion Witnesses

**M1 Complete:**
- [ ] All 4 emergent features working (Session Memory, Time Travel, HITL, Fault Tolerance)

**M2 Complete:**
- [ ] 10+ concurrent async invocations without locks
- [ ] 5MB PDF → <5KB checkpoint
- [ ] Checkpoint pruning operational

**M3 Complete:**
- [ ] Dashboard showing real-time metrics
- [ ] Migration decision = "MIGRATE NOW" triggered

**M4 Complete:**
- [ ] 100% production traffic on PostgreSQL
- [ ] Zero data loss verified

**M5 Complete:**
- [ ] All checkpoint operations <5ms P99
- [ ] Zero-downtime backups configured

**M6 Complete:**
- [ ] Cross-thread knowledge retrieval working
- [ ] Checkpoint size <10KB enforced

**M7 Complete:**
- [ ] Auto-scaling operational
- [ ] 96% cost reduction achieved
- [ ] Zero manual interventions for 30 days

---

## The Emergence Principle

**Total Code for Features:** ~30 lines (M1.1 setup + infrastructure)
**Total Features Unlocked:** 4 (Session Memory, Time Travel, HITL, Fault Tolerance)

**This proves:** Features emerge from removing constraints, not from building features.

**Anti-Pattern Detection:**
- If you write "session memory management" → violation
- If you write "timeline tracking logic" → violation
- If you write "approval workflow" → violation
- If you write "crash recovery handler" → violation

**True Pattern:**
- M1.1 writes infrastructure (SqliteSaver.setup())
- M1.2-M1.5 write witness verification (tests only)
- Features emerge automatically from infrastructure

---

## The Complete Journey

**From:** No persistent state (conversations die with process termination)
**To:** Autonomous, cost-optimized, self-healing production checkpoint persistence

**Achieved Through:** 28 witness-verified tasks across 7 irreversible phase shifts

**Final State:**
- Distributed deployment (500+ writes/sec)
- Cross-thread knowledge sharing
- Auto-scaling based on metrics
- 96% cost reduction ($3,680 → $126/month)
- Proactive anomaly detection
- Zero manual intervention
