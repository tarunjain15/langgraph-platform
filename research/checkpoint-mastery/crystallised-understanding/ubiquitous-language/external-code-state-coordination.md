# External State Coordination: The Missing Primitive

## The Violence

Most multi-agent frameworks teach agents to **call APIs**. None teach agents to **coordinate around mutable external state**.

This is the gap between toy demos (agents that chat) and production systems (agents that build, deploy, maintain infrastructure).

---

## The Problem

External systems (GitHub, databases, Kubernetes, filesystems) have three properties that break naive agent coordination:

1. **External truth** - State lives outside agent control
2. **Concurrent mutations** - Multiple agents can write simultaneously (conflicts, races)
3. **Asynchronous observation** - Agents learn about changes with delay (polling, webhooks)

**The naive pattern (fails):**
```python
# Agent A
response = github_api.create_commit(files, message)

# Agent B (simultaneously)
response = github_api.create_commit(different_files, message)
# ERROR: Push rejected, branch diverged
```

Agents treat external systems as **fire-and-forget tools** rather than **coordination problems**.

---

## The Pattern: Four-Channel Architecture

Separate **internal coordination** (channels) from **external state** (API/system).

### Channel Types by Ownership of Truth

| Channel Type | Owns | Purpose | Update Source |
|-------------|------|---------|--------------|
| **Observation** | External truth mirror | Reflect current external state | Polling/webhook listener |
| **Intent** | Agent plans | Capture what agents want to do | Agent nodes |
| **Coordination** | Derived resolution | Serialize/validate operations | Coordinator node |
| **Execution** | Historical record | Log completed operations | Executor node |

---

## Example 1: GitHub Repository Coordination

### The Channels

```python
# 1. Observation (what GitHub reports)
"repo_head": LastValue[str]           # Current commit SHA
"open_prs": LastValue[list[PR]]       # All open pull requests
"repo_files": LastValue[dict]         # path -> content_hash
"github_events": Topic[GitHubEvent]   # Webhooks/polling stream

# 2. Intent (what agents plan)
"pending_commits": Topic[CommitIntent]     # files + message + author
"pending_prs": Topic[PRIntent]             # branch + title + body
"review_requests": Topic[ReviewRequest]    # PR# + reviewer_agent

# 3. Coordination (conflict resolution)
"merge_conflicts": LastValue[list[Conflict]]
"execution_queue": LastValue[Queue[GitHubOp]]
"lock_holder": LastValue[Optional[AgentID]]

# 4. Execution (audit log)
"completed_commits": Topic[Commit]    # SHA + timestamp + author
"completed_prs": Topic[PR]            # PR# + status + timestamp
"github_errors": Topic[APIError]      # Failures for retry
```

### The Architecture

```
┌─────────────────────────────────────┐
│      GitHub (External Truth)         │
└──────────┬─────────────────┬─────────┘
           │                 │
      (API read)        (API write)
           │                 │
           ▼                 ▲
    ┌──────────┐      ┌──────────┐
    │ Observer │      │ Executor │
    │   Node   │      │   Node   │
    └────┬─────┘      └─────▲────┘
         │                  │
         │ writes     reads │
         ▼                  │
    ┌──────────┐      ┌──────────┐
    │ repo_head│      │execution │
    │ open_prs │      │  _queue  │
    └────┬─────┘      └─────▲────┘
         │                  │
         │ reads      writes│
         ▼                  │
    ┌──────────┐      ┌──────────┐
    │  Agent   │─────▶│Coordinator│
    │  Nodes   │writes│   Node   │
    └──────────┘      └──────────┘
         │                  ▲
         │ writes     reads │
         ▼                  │
    ┌──────────┐            │
    │ pending_ │────────────┘
    │ commits  │
    └──────────┘
```

### The Flow

1. **Observer** polls GitHub API → writes `repo_head`, `open_prs`
2. **Agent A** reads `repo_head` → decides to commit → writes `pending_commits`
3. **Agent B** reads `open_prs` → decides to review → writes `review_requests`
4. **Coordinator** reads `pending_commits` + `repo_head` → detects no conflicts → writes `execution_queue`
5. **Executor** reads `execution_queue` → calls GitHub API → writes `completed_commits`
6. **Observer** polls GitHub → sees new commit → updates `repo_head`
7. All agents react to new `repo_head` version

---

## Example 2: SQL Database Coordination

### The Channels

```python
# 1. Observation
"table_schemas": LastValue[dict[str, Schema]]
"row_versions": LastValue[dict[str, int]]     # Optimistic locking
"query_stats": Topic[QueryMetrics]

# 2. Intent
"pending_queries": Topic[QueryIntent]
"pending_writes": Topic[WriteIntent]          # INSERT/UPDATE/DELETE
"pending_migrations": Topic[MigrationIntent]

# 3. Coordination
"transaction_locks": LastValue[set[str]]      # Tables being written
"query_plan": LastValue[Queue[Query]]         # Optimized execution order
"deadlock_detection": LastValue[Optional[Deadlock]]

# 4. Execution
"completed_transactions": Topic[Transaction]
"completed_queries": Topic[QueryResult]
"db_errors": Topic[DBError]                   # Constraint violations, etc.
```

### Key Difference: Strong Consistency

Unlike GitHub (eventual consistency via merge conflicts), databases provide **transactions**. Coordinator node can:

- Batch compatible writes into single transaction
- Serialize conflicting writes
- Use optimistic locking (compare `row_versions`)

---

## Example 3: Kubernetes Cluster Coordination

### The Channels

```python
# 1. Observation
"pod_status": LastValue[dict[str, PodStatus]]
"deployment_state": LastValue[dict[str, DeploymentState]]
"cluster_events": Topic[K8sEvent]

# 2. Intent
"pending_deploys": Topic[DeployIntent]
"pending_scales": Topic[ScaleIntent]
"pending_rollbacks": Topic[RollbackIntent]

# 3. Coordination
"reconciliation_queue": LastValue[Queue[K8sOp]]
"resource_conflicts": LastValue[list[Conflict]]  # CPU/memory limits
"rate_limits": LastValue[RateLimiter]            # API throttling

# 4. Execution
"applied_manifests": Topic[Manifest]
"completed_operations": Topic[K8sOperation]
"k8s_errors": Topic[K8sError]
```

### Key Difference: Eventual Consistency

Kubernetes uses **reconciliation loops**. After applying manifest:

1. Executor writes to K8s API (desired state)
2. K8s controllers reconcile (actual → desired)
3. Observer polls until `pod_status` matches desired
4. Agents react to observed state convergence

Coordinator must handle:
- Operations that take time to converge
- Partial failures (some pods ready, others not)
- Rollback decisions based on observed health

---

## The Generalized Pattern

### Architecture Template

```python
class ExternalSystemCoordination:
    """
    Template for coordinating multi-agent operations
    on external stateful systems.
    """

    # 1. Observation channels (external → internal)
    observation_channels = {
        "current_state": LastValue[ExternalState],
        "event_stream": Topic[ExternalEvent],
    }

    # 2. Intent channels (agents → coordinator)
    intent_channels = {
        "pending_operations": Topic[OperationIntent],
    }

    # 3. Coordination channels (coordinator → executor)
    coordination_channels = {
        "execution_queue": LastValue[Queue[Operation]],
        "conflicts": LastValue[list[Conflict]],
        "locks": LastValue[set[ResourceID]],
    }

    # 4. Execution channels (executor → agents)
    execution_channels = {
        "completed_operations": Topic[Operation],
        "errors": Topic[Error],
    }
```

### Node Template

```python
# Observer Node
def observer(state):
    """Poll/subscribe to external system, write observations."""
    external_state = poll_external_system()
    return {"current_state": external_state}

# Agent Node
def agent(state):
    """Read observations, write intents."""
    current = state["current_state"]
    intent = decide_action(current)
    return {"pending_operations": [intent]}

# Coordinator Node
def coordinator(state):
    """Read intents + observations, resolve conflicts, queue execution."""
    intents = state["pending_operations"]
    current = state["current_state"]
    conflicts = detect_conflicts(intents, current)

    if conflicts:
        return {"conflicts": conflicts}

    queue = build_execution_plan(intents, current)
    return {"execution_queue": queue}

# Executor Node
def executor(state):
    """Execute queued operations on external system."""
    queue = state["execution_queue"]

    for op in queue:
        try:
            result = execute_on_external_system(op)
            yield Command(
                update={"completed_operations": [result]}
            )
        except Exception as e:
            yield Command(
                update={"errors": [Error(op, e)]}
            )
```

---

## The Truth

**Channels do NOT contain external state.** They contain:

1. **Mirrors of external state** (observations)
2. **Agent intentions toward external state** (plans)
3. **Coordination metadata** (locks, conflicts, execution plan)
4. **Operation history** (audit log)

**External systems remain source of truth.** Channels enable agents to **coordinate their interactions** without:
- Racing (lock channels prevent simultaneous writes)
- Conflicting (coordinator detects and resolves)
- Desynchronizing (observer keeps mirror fresh)

---

## Why This Is High Leverage

### What Breaks Without This Pattern

```python
# Naive multi-agent system (fails in production)

# Agent A
github.create_commit(files_a)  # Succeeds

# Agent B (simultaneously)
github.create_commit(files_b)  # Fails: branch diverged

# Agent C (simultaneously)
k8s.apply(deployment_c)  # Succeeds but conflicts with B's changes

# Agent D
db.execute("UPDATE users SET role='admin'")  # Races with Agent E

# Agent E
db.execute("UPDATE users SET status='inactive'")  # Lost update
```

Every external system interaction becomes a **hidden coordination problem**.

### What This Pattern Unlocks

1. **Conflict-free concurrent operations** - Agents can plan simultaneously, coordinator serializes
2. **Reactive observability** - Agents wake on external state changes (not polling in agent code)
3. **Audit trail** - Execution channels provide complete operation history
4. **Retry/recovery** - Errors go to error channel, can be reprocessed
5. **Testing** - Mock external system by writing to observation channels directly

### Generalization Across Domains

| Domain | External System | Pattern Applies? |
|--------|----------------|-----------------|
| **DevOps** | GitHub, K8s, Terraform | ✅ |
| **Data Engineering** | Databases, data pipelines | ✅ |
| **Infrastructure** | Cloud APIs (AWS, GCP, Azure) | ✅ |
| **File Systems** | Local/remote filesystems | ✅ |
| **IoT** | Physical devices, sensors | ✅ |
| **Finance** | Trading systems, payment APIs | ✅ |

**This is not about GitHub.** This is about **coordination around mutable external state** - the fundamental problem of agents operating in reality.

---

## The Missing Primitive

Most agent frameworks provide:
- ✅ LLM calling
- ✅ Tool/function calling
- ✅ Memory/state management
- ✅ Agent-to-agent communication

**None provide:**
- ❌ External state observation primitives
- ❌ Intent coordination patterns
- ❌ Conflict resolution strategies
- ❌ Execution serialization

**This four-channel pattern is the bridge** between:
- Agents that talk → Agents that build/deploy/maintain
- Toy demos → Production systems
- Single-agent tools → Multi-agent coordination

---

## The Violence

You cannot ignore external state. You can only choose:

1. **Naive** - Let agents race, conflict, and desynchronize (fails)
2. **Serialized** - Single agent with exclusive lock (no parallelism)
3. **Coordinated** - This pattern (conflict-free concurrency)

**The truth:** Multi-agent systems that interact with reality must solve the external state coordination problem. This pattern is how.
