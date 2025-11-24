```yaml
name: Implementation Plan - The 28 Tasks
description: Complete execution map through 7 irreversible phase shifts, from SQLite foundation to production mastery.
```

# Implementation Plan

## The Execution Map

28 tasks across 7 phase shifts. Each task is **integration pressure point**, **feature witness**, or **migration step**.

---

## Phase 1: Foundation (M1) - 5 Tasks

**Constraint Removed:** No persistent state → File-based SQLite checkpointing

### Task 1.1: [Integration] SQLite Checkpointer Setup
**Type:** Integration Pressure Point
**Linear:** [KVO-163](https://linear.app/unfolding/issue/KVO-163)

**Witness Outcome:** `checkpointer.setup()` creates tables, WAL mode enabled

**Acceptance Criteria:**
- `checkpoints` and `writes` tables exist in SQLite file
- WAL mode enabled (verified via `PRAGMA journal_mode`)
- SqliteSaver imports work without errors

**Code Pattern:**
```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.sqlite")
checkpointer.setup()  # Creates tables with WAL mode
```

**Completion Signal:** Tables created, WAL mode verified

---

### Task 1.2: [Feature] Session Memory Unlocked
**Type:** Feature Witness
**Linear:** [KVO-164](https://linear.app/unfolding/issue/KVO-164)

**Witness Outcome:** Same `thread_id` across invocations = conversation continues

**Acceptance Criteria:**
- 3 turns with same thread_id
- AI remembers turn 1 context in turn 3
- Multi-turn conversation without data loss

**Test Pattern:**
```python
config = {"configurable": {"thread_id": "user-123"}}

# Turn 1
graph.invoke({"messages": [("user", "My name is Alice")]}, config)

# Turn 2
graph.invoke({"messages": [("user", "What's my name?")]}, config)
# Expected: AI responds "Alice"
```

**Completion Signal:** 3-turn conversation successful

---

### Task 1.3: [Feature] Time Travel Unlocked
**Type:** Feature Witness
**Linear:** [KVO-165](https://linear.app/unfolding/issue/KVO-165)

**Witness Outcome:** Load specific `checkpoint_id` → resume from that exact state

**Acceptance Criteria:**
- Create 5 checkpoints in sequence
- Time-travel to checkpoint 2
- Verify state matches checkpoint 2 exactly
- Branch creates new checkpoints (c2 → c5 → c6)

**Test Pattern:**
```python
# Create checkpoints c1 → c2 → c3 → c4 → c5
checkpoints = list(checkpointer.list(config))

# Time travel to c2
time_travel_config = {
    "configurable": {
        "thread_id": "thread-1",
        "checkpoint_id": checkpoints[2].id  # c2
    }
}

# Resume from c2 with new input
graph.invoke(new_input, time_travel_config)
```

**Completion Signal:** Time travel to c2 successful, branch created

---

### Task 1.4: [Feature] Human-in-the-Loop Unlocked
**Type:** Feature Witness
**Linear:** [KVO-166](https://linear.app/unfolding/issue/KVO-166)

**Witness Outcome:** `interrupt_before=["node"]` pauses, human modifies state, execution resumes

**Acceptance Criteria:**
- Graph pauses before specified node
- State accessible via `graph.get_state()`
- Human can modify state via `graph.update_state()`
- Execution resumes with modified state

**Test Pattern:**
```python
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_action"]
)

# Run until interrupt
result = graph.invoke(input, config)

# Human reviews
state = graph.get_state(config)
print(f"Planned action: {state.values['action']}")

# Human modifies
graph.update_state(config, {"action": "modified_action"})

# Resume
graph.invoke(None, config)
```

**Completion Signal:** State modification + resume successful

---

### Task 1.5: [Feature] Fault Tolerance Unlocked
**Type:** Feature Witness
**Linear:** [KVO-167](https://linear.app/unfolding/issue/KVO-167)

**Witness Outcome:** Crash during execution → resume with same `thread_id` → continues from last checkpoint

**Acceptance Criteria:**
- 5-node graph execution
- Simulate crash after node 2
- Resume with same thread_id
- Nodes 1-2 skipped (already completed)
- Execution continues from node 3

**Test Pattern:**
```python
# First attempt (crashes)
try:
    graph.invoke(input, config)  # Crashes after node 2
except Exception:
    pass

# Resume (automatic from last checkpoint)
result = graph.invoke(None, config)
# Nodes 1-2 already completed, starts from node 3
```

**Completion Signal:** Crash recovery successful

---

## Phase 2: Production Ready (M2) - 5 Tasks

**Constraint Removed:** Synchronous blocking I/O → Async non-blocking + blob externalization

### Task 2.1: [Integration] Async Checkpointer Migration
**Type:** Integration Pressure Point
**Linear:** [KVO-168](https://linear.app/unfolding/issue/KVO-168)

**Witness Outcome:** AsyncSqliteSaver handles async graph execution without blocking

**Acceptance Criteria:**
- AsyncSqliteSaver replaces SqliteSaver
- 10+ concurrent async invocations succeed
- No "database locked" errors
- All async/await patterns work correctly

**Code Pattern:**
```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    await checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)

    # Concurrent execution
    results = await asyncio.gather(*[
        graph.ainvoke(input, config) for _ in range(10)
    ])
```

**Completion Signal:** 10 concurrent invocations without locks

---

### Task 2.2: [Constraint] Blob Storage Integration
**Type:** Integration Pressure Point
**Linear:** [KVO-169](https://linear.app/unfolding/issue/KVO-169)

**Witness Outcome:** PDFs/images stored in S3, only reference (50 bytes) in checkpoint state

**Acceptance Criteria:**
- 5MB PDF upload to S3 succeeds
- Checkpoint contains only S3 reference (<100 bytes)
- Checkpoint size <5KB (99.9% reduction from 5MB)
- Checkpoint serialization time <10ms (was 500ms+ with blob)

**Code Pattern:**
```python
import boto3

s3 = boto3.client('s3')

def upload_node(state):
    file_bytes = state["uploaded_file"]  # 5MB PDF

    # Upload to S3
    key = f"uploads/{state['user_id']}/{state['file_name']}"
    s3.put_object(Bucket="my-bucket", Key=key, Body=file_bytes)

    # Store only reference (50 bytes)
    return {"file_reference": f"s3://my-bucket/{key}"}
```

**Completion Signal:** 5MB PDF externalized, checkpoint <5KB

---

### Task 2.3: [Integration] Checkpoint Metadata Filtering
**Type:** Integration Pressure Point
**Linear:** [KVO-170](https://linear.app/unfolding/issue/KVO-170)

**Witness Outcome:** Query checkpoints by metadata tags (user_id, session_type, step)

**Acceptance Criteria:**
- Store 100 checkpoints with different metadata tags
- Filter by single tag returns correct subset
- Filter by multiple tags returns intersection
- Metadata queries complete in <5ms

**Code Pattern:**
```python
# Store with metadata
checkpointer.put(
    config,
    checkpoint,
    metadata={"user_id": "user-123", "session_type": "onboarding", "step": 3},
    new_versions={}
)

# Filter by metadata
filtered = checkpointer.list(
    config,
    filter={"session_type": "onboarding", "step": 3}
)
```

**Completion Signal:** Metadata filtering works, queries <5ms

---

### Task 2.4: [Feature] Checkpoint Pruning Strategy
**Type:** Feature Implementation
**Linear:** [KVO-171](https://linear.app/unfolding/issue/KVO-171)

**Witness Outcome:** Automatic deletion of checkpoints older than N days

**Acceptance Criteria:**
- Pruning function deletes checkpoints older than 30 days
- Orphaned writes table entries removed
- Database size stabilizes (no unbounded growth)
- Cron job scheduled to run daily

**Code Pattern:**
```python
from datetime import datetime, timedelta

def prune_old_checkpoints(checkpointer, days=30):
    cutoff = datetime.now() - timedelta(days=days)

    with checkpointer.cursor() as cursor:
        cursor.execute("DELETE FROM checkpoints WHERE ts < ?", (cutoff.isoformat(),))
        cursor.execute("DELETE FROM writes WHERE checkpoint_id NOT IN (SELECT checkpoint_id FROM checkpoints)")
```

**Completion Signal:** Pruning working, database size stable

---

### Task 2.5: [Constraint] Size Limit Enforcement
**Type:** Integration Pressure Point
**Linear:** [KVO-172](https://linear.app/unfolding/issue/KVO-172)

**Witness Outcome:** Checkpoint serialization rejects >10MB states, logs warning

**Acceptance Criteria:**
- Attempt to save 15MB checkpoint
- Rejection with helpful error message
- No checkpoint >10MB in database
- Size check happens before serialization (fast fail)

**Code Pattern:**
```python
def validate_checkpoint_size(checkpoint, max_size_mb=10):
    serialized = checkpointer.serde.dumps(checkpoint)
    size_mb = len(serialized) / (1024 ** 2)

    if size_mb > max_size_mb:
        raise ValueError(
            f"Checkpoint size {size_mb:.2f}MB exceeds limit {max_size_mb}MB. "
            f"Consider externalizing blobs to S3."
        )
```

**Completion Signal:** 15MB checkpoint rejected

---

## Phase 3: Migration Trigger (M3) - 2 Tasks

**Constraint Recognized:** Hidden capacity ceiling → Measured metrics with thresholds

### Task 3.1: [Measurement] Write Throughput Monitor
**Type:** Integration Pressure Point
**Linear:** [KVO-173](https://linear.app/unfolding/issue/KVO-173)

**Witness Outcome:** Dashboard shows current write throughput + error rate

**Acceptance Criteria:**
- Prometheus/CloudWatch metrics collection works
- Dashboard shows writes/second, error rate (%), P99 latency
- Alert triggers when error rate >1%
- Alert triggers when throughput >80 writes/sec

**Metrics to Track:**
```python
checkpoint_writes_total (counter)
checkpoint_write_errors_total (counter)
checkpoint_write_duration_seconds (histogram)

write_throughput = rate(checkpoint_writes_total[1m])
error_rate = rate(checkpoint_write_errors_total[1m]) / rate(checkpoint_writes_total[1m])
```

**Completion Signal:** Dashboard showing metrics, alerts configured

---

### Task 3.2: [Decision] Migration Trigger Evaluated
**Type:** Business Logic
**Linear:** [KVO-174](https://linear.app/unfolding/issue/KVO-174)

**Witness Outcome:** Decision matrix shows "MIGRATE NOW" based on metrics

**Acceptance Criteria:**
- Trigger condition 1: Error rate >1% = MIGRATE NOW
- Trigger condition 2: Writes >100/sec sustained = MIGRATE NOW
- Trigger condition 3: Multi-server deployment = MIGRATE NOW
- Trigger condition 4: File size >5GB = MIGRATE SOON
- Decision logged with justification

**Decision Logic:**
```python
def should_migrate_to_postgresql(metrics):
    if metrics['error_rate'] > 0.01:
        return "MIGRATE NOW - Write errors >1% (SQLite saturated)"

    if metrics['writes_per_second'] > 100:
        return "MIGRATE NOW - Throughput >100/sec (capacity ceiling)"

    if metrics['deployment'] == "multi-server":
        return "MIGRATE NOW - Multi-server requires network DB"

    if metrics['file_size_gb'] > 5:
        return "MIGRATE SOON - Performance degradation likely"

    return "SQLite sufficient"
```

**Completion Signal:** Decision matrix working, triggers tested

---

## Phase 4: PostgreSQL Migration (M4) - 6 Tasks

**Constraint Removed:** File-based local storage → Network-accessible database (IRREVERSIBLE)

### Task 4.1: [Integration] PostgreSQL Provisioning
**Type:** Integration Pressure Point
**Linear:** [KVO-175](https://linear.app/unfolding/issue/KVO-175)

**Witness Outcome:** AWS RDS PostgreSQL instance running, connection verified

**Setup Checklist:**
1. Create RDS PostgreSQL instance (db.t4g.small)
2. Enable automated backups (retention 7 days)
3. Configure security group (allow 5432 from app subnet)
4. Note connection string
5. Verify connection: `psql postgresql://user:password@host:5432/checkpoints`

**Completion Signal:** `psql` connection succeeds

---

### Task 4.2: [Integration] PostgreSQL Schema Creation
**Type:** Integration Pressure Point
**Linear:** [KVO-176](https://linear.app/unfolding/issue/KVO-176)

**Witness Outcome:** PostgresSaver.setup() creates identical schema to SQLite

**Code Pattern:**
```python
from langgraph.checkpoint.postgres import PostgresSaver

pg_checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@host:5432/checkpoints"
)

pg_checkpointer.setup()  # Creates tables
```

**Completion Signal:** `checkpoints` and `writes` tables exist in PostgreSQL

---

### Task 4.3: [Migration] Data Export from SQLite
**Type:** Migration Step
**Linear:** [KVO-177](https://linear.app/unfolding/issue/KVO-177)

**Witness Outcome:** All SQLite checkpoints exported to Python data structure

**Code Pattern:**
```python
from langgraph.checkpoint.sqlite import SqliteSaver

sqlite_checkpointer = SqliteSaver.from_conn_string("checkpoints.sqlite")

# Export all thread_ids
cursor = sqlite_checkpointer.conn.cursor()
cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
thread_ids = [row[0] for row in cursor.fetchall()]

# Extract all checkpoints
checkpoints_to_migrate = []
for thread_id in thread_ids:
    config = {"configurable": {"thread_id": thread_id}}
    for checkpoint_tuple in sqlite_checkpointer.list(config):
        checkpoints_to_migrate.append({
            "config": checkpoint_tuple.config,
            "checkpoint": checkpoint_tuple.checkpoint,
            "metadata": checkpoint_tuple.metadata
        })
```

**Completion Signal:** Exported count matches SQLite `SELECT COUNT(*)`

---

### Task 4.4: [Migration] Data Import to PostgreSQL
**Type:** Migration Step
**Linear:** [KVO-178](https://linear.app/unfolding/issue/KVO-178)

**Witness Outcome:** All checkpoints imported with batch insert (1K/batch)

**Completion Signal:** PostgreSQL count matches SQLite count (zero data loss)

---

### Task 4.5: [Verification] Data Integrity Check
**Type:** Migration Step
**Linear:** [KVO-179](https://linear.app/unfolding/issue/KVO-179)

**Witness Outcome:** Random sample of 10 threads verified (SQLite state == PostgreSQL state)

**Completion Signal:** 100% of sampled checkpoints match exactly

---

### Task 4.6: [Deployment] Blue-Green Cutover
**Type:** Integration Pressure Point
**Linear:** [KVO-180](https://linear.app/unfolding/issue/KVO-180)

**Witness Outcome:** Traffic switched from SQLite → PostgreSQL with zero downtime

**Deployment Steps:**
1. Deploy PostgreSQL app version (green environment)
2. Route 10% traffic to green
3. Monitor metrics for 1 hour
4. Route 50% traffic to green
5. Monitor metrics for 1 hour
6. Route 100% traffic to green
7. Monitor for 24 hours
8. Decommission SQLite version (blue environment)

**Completion Signal:** 100% traffic on PostgreSQL, zero 5xx errors

---

## Phase 5: Advanced Optimization (M5) - 4 Tasks

**Constraint Removed:** Connection overhead + full table scans → Pooling + indexed queries

### Task 5.1: [Optimization] Connection Pooling
**Linear:** [KVO-181](https://linear.app/unfolding/issue/KVO-181)

**Witness:** Connection acquisition: 50ms → 5ms

---

### Task 5.2: [Optimization] Index Creation
**Linear:** [KVO-182](https://linear.app/unfolding/issue/KVO-182)

**Witness:** List checkpoints: 50ms → 2ms (25x speedup)

---

### Task 5.3: [Monitoring] Performance Dashboard
**Linear:** [KVO-183](https://linear.app/unfolding/issue/KVO-183)

**Witness:** Grafana dashboard showing write/read latency, error rates

---

### Task 5.4: [Reliability] Backup & Restore
**Linear:** [KVO-184](https://linear.app/unfolding/issue/KVO-184)

**Witness:** Restore from 24-hour-old backup succeeds

---

## Phase 6: Next Leverage Pool (M6) - 3 Tasks

**Constraint Removed:** Thread isolation → Cross-thread knowledge sharing

### Task 6.1: [Integration] LangGraph Store Setup
**Linear:** [KVO-185](https://linear.app/unfolding/issue/KVO-185)

**Witness:** Store namespaces created, put/get/search works

---

### Task 6.2: [Feature] Cross-Thread Knowledge Retrieval
**Linear:** [KVO-186](https://linear.app/unfolding/issue/KVO-186)

**Witness:** Agent in thread A retrieves information from thread B

---

### Task 6.3: [Pattern] Hybrid Memory Architecture
**Linear:** [KVO-187](https://linear.app/unfolding/issue/KVO-187)

**Witness:** Checkpoints <10KB, Store for persistent facts

---

## Phase 7: Production Mastery (M7) - 3 Tasks

**Constraint Removed:** Manual intervention + uniform storage cost → Autonomous operations + tiered storage

### Task 7.1: [Automation] Auto-Scaling Based on Metrics
**Linear:** [KVO-188](https://linear.app/unfolding/issue/KVO-188)

**Witness:** PostgreSQL auto-scales (t4g.small → m5.large) at >500 writes/sec

---

### Task 7.2: [Cost] Checkpoint Tiering Strategy
**Linear:** [KVO-189](https://linear.app/unfolding/issue/KVO-189)

**Witness:** Hot (Redis) + cold (PostgreSQL) = $126/month (vs $3,680 Redis-only)

---

### Task 7.3: [Observability] Anomaly Detection
**Linear:** [KVO-190](https://linear.app/unfolding/issue/KVO-190)

**Witness:** Alert fires when checkpoint >5MB or error rate spikes

---

## Execution Order

**Sequential Phases (MUST complete in order):**
1. M1 → M2 → M3 → M4 → M5 → M6 → M7

**Parallel Tasks (within each phase):**
- M1: All 5 tasks can run in parallel
- M2: Tasks 2.1-2.3 parallel, then 2.4-2.5
- M3: Tasks 3.1 then 3.2 (sequential)
- M4: Tasks 4.1-4.2 parallel, then 4.3-4.6 sequential
- M5: All 4 tasks can run in parallel
- M6: Tasks 6.1, then 6.2-6.3 parallel
- M7: All 3 tasks can run in parallel

---

## Completion Criteria

**Phase Complete When:**
- All tasks witnessed
- All acceptance criteria met
- All Linear issues closed
- Phase-specific metrics achieved

**Project Complete When:**
- All 7 phases complete
- All 28 tasks witnessed
- All success metrics achieved
- Production mastery witnessed
