```yaml
phase: M4
name: PostgreSQL Migration (IRREVERSIBLE)
constraint_removed: File-based local storage → Network-accessible database
tasks: 6
status: pending
created: 2025-11-17
```

# Phase 4: PostgreSQL Migration - Task Summary

## The Sacred Truth

**This is the IRREVERSIBLE phase shift.**

Once M4.6 completes (100% traffic on PostgreSQL, SQLite decommissioned), there is no going back. PostgreSQL becomes the source of truth. File-based → Network database is a one-way door.

---

## Task Execution Order

**Sequential Dependency:**
```
M4.1 (PostgreSQL Provisioning) ┐
M4.2 (Schema Creation)         ┘ Parallel setup
  ↓
M4.3 (Export from SQLite) ← Sequential migration
  ↓
M4.4 (Import to PostgreSQL)
  ↓
M4.5 (Integrity Check)
  ↓
M4.6 (Blue-Green Cutover) ← IRREVERSIBLE TRANSITION
```

**Execution Strategy:**
1. M4.1-M4.2 in parallel (infrastructure + schema)
2. M4.3-M4.6 sequential (migration pipeline)
3. Do NOT proceed to M4.6 until M4.5 shows 100% integrity

**Time Estimate:**
- M4.1: 30 min (Terraform + provisioning wait)
- M4.2: 15 min (schema creation + verification)
- M4.3: 1-2 hours (export with verification)
- M4.4: 2-4 hours (import with batching)
- M4.5: 30 min (random sample verification)
- M4.6: 26+ hours (progressive cutover + stabilization)
- **Total: ~30-33 hours** (mostly automated waiting)

---

## The Six Tasks

### M4.1: PostgreSQL Provisioning
**Witness:** `psql` connection succeeds from app server

### M4.2: Schema Creation
**Witness:** `\dt` shows `checkpoints` and `writes` tables

### M4.3: Export from SQLite
**Witness:** Export count = SQLite count

### M4.4: Import to PostgreSQL
**Witness:** PostgreSQL count = SQLite count

### M4.5: Integrity Check
**Witness:** 100% of sampled threads match exactly

### M4.6: Blue-Green Cutover
**Witness:** 100% traffic on PostgreSQL, zero errors, blue decommissioned

---

## Phase Completion Witness

**The irreversible transition complete:**

```bash
# Evidence 1: PostgreSQL is production database
psql $PG_CONN -c "SELECT COUNT(*) FROM checkpoints"
# Returns: checkpoint count

# Evidence 2: SQLite version decommissioned
docker ps | grep app-blue
# Returns: nothing (blue environment gone)

# Evidence 3: All traffic on PostgreSQL
curl http://lb/weights
# Returns: green=100%, blue=0%

# Evidence 4: Zero errors in past 24 hours
# Check Grafana: http_requests_total{status=~"5.."} = 0
```

**If all 4 pieces of evidence exist, M4 is complete and IRREVERSIBLE.**

---

## Success Metrics (Non-Negotiable)

```yaml
M4.1_witness:
  postgresql_accessible: true
  network_connection: verified

M4.2_witness:
  schema_created: true
  tables_exist: [checkpoints, writes]

M4.3_witness:
  export_count_match: 100%
  data_exported: true

M4.4_witness:
  import_count_match: 100%
  zero_data_loss: true

M4.5_witness:
  integrity_check: passed
  sample_match_rate: 100%

M4.6_witness:
  traffic_on_postgresql: 100%
  error_rate: 0%
  blue_decommissioned: true
```

---

## Anti-Patterns (Emergence Violations)

**DO NOT BUILD:**
- ❌ Custom migration tools (use LangGraph checkpointers)
- ❌ Manual cutover (blue-green is proven strategy)
- ❌ Big-bang migration (progressive rollout required)
- ❌ Skipping integrity check (non-negotiable)

**ONLY BUILD:**
- ✅ Terraform for RDS provisioning
- ✅ Export/import scripts using checkpointer APIs
- ✅ Verification script with random sampling
- ✅ Load balancer configuration for blue-green
- ✅ Monitoring dashboard for cutover

---

## Constraint Compliance

**CONTEXT_PRESERVATION:** Migration preserves all checkpoint history - threads, branches, metadata intact across database systems.

**CONSTRAINT_INHERITANCE:** PostgreSQL inherits all SQLite constraints - schema compatibility ensures continuity.

**TRACE_REQUIRED:** Every migration step logged - export counts, import batches, integrity checks, cutover stages. Full audit trail.

**RESOURCE_STEWARDSHIP:** Right-sized PostgreSQL instance prevents overprovisioning. Blue-green minimizes risk. Batch import efficient.

**RESIDUE_FREE:** Blue environment decommissioned - no orphaned infrastructure. SQLite file archived but not in production path.

---

## Migration to M5 Trigger

**When to move to M5:**
- M4.6 complete (100% traffic on PostgreSQL stable for 24+ hours)
- Performance baseline established
- Ready to optimize (connection pooling, indexing)

**Do NOT migrate if:**
- Still in cutover stabilization period
- Error rate >0% (investigate first)
- Performance issues observed (fix first)

**M5 unlocks:**
- Connection pooling (5ms → 50ms improvement)
- Index optimization (50ms → 2ms queries)
- Performance monitoring dashboard
- Backup/restore automation

---

## The Irreversibility Principle Proven

**Before M4:** File-based SQLite, single-server only
**After M4:** Network PostgreSQL, multi-server capable, IRREVERSIBLE

**Total Constraints Removed:** 1 massive constraint
- File-based → Network database (one-way door)

**This is the proof of irreversibility: Some phase shifts cannot be undone. Choose wisely.**
