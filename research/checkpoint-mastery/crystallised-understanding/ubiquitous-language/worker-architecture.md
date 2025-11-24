# Worker Architecture: Interface + Implementation

## The Complete Picture

A **Worker** is an autonomous domain specialist that:
1. Exposes **7-tool interface** to Manager (external contract)
2. Implements via **4-channel coordination** (internal architecture)
3. Coordinates around **external stateful systems** (GitHub, databases, K8s, etc.)

**Three actors, two boundaries:**

```
Manager (agentic, rhythm-aware)
    │
    │ ┌─────────────────────────────┐
    │ │    7-Tool Interface         │
    │ │  (intent → outcome)         │
    └─┼─────────────────────────────┼─→ Worker
      │                             │    (domain specialist)
      │  state(), pressure(),       │      │
      │  constraints(), flow(),     │      │ ┌────────────────────┐
      │  void(), execute(), evolve()│      │ │ 4-Channel Pattern  │
      └─────────────────────────────┘      │ │ (internal coord)   │
                                           └─┼────────────────────┼─→ External System
                                             │                    │    (GitHub, DB, K8s)
                                             │ Observer, Agent,   │
                                             │ Coordinator,       │
                                             │ Executor nodes     │
                                             └────────────────────┘
```

**Manager sees:** Intent → Outcome (black box)

**Worker implements:** Observer → Channels → Agent → Coordinator → Executor (white box)

**External system sees:** API calls (GitHub commits, DB writes, K8s applies)

---

## Layer 1: The 7-Tool Interface (Manager's View)

Every worker exposes identical interface regardless of domain.

### Query Tools (5) - Awareness Maintenance

| Tool | Returns | Reads From (Internal) |
|------|---------|----------------------|
| `state()` | Current reality | Observation channels |
| `pressure()` | Unfulfilled demands | Intent channels |
| `constraints()` | Sacred limits | Coordination channels (locks, conflicts) |
| `flow()` | Current motion | Coordination channels (execution queue) |
| `void()` | Conscious gaps | Execution channels (errors, incomplete ops) |

### Command Tool (1) - Action Issuance

| Tool | Input | Effect |
|------|-------|--------|
| `execute(intent)` | Natural language intent | Triggers internal graph execution |

Intent is **NOT** operation-specific:
- ❌ Wrong: `commit_files(files, message)`
- ✅ Right: `execute("commit these changes with message X")`

Worker interprets intent within domain context.

### Meta Tool (1) - Capability Improvement

| Tool | Input | Effect |
|------|-------|--------|
| `evolve(feedback)` | Manager feedback | Updates worker procedures/prompts |

---

## Layer 2: The 4-Channel Implementation (Worker's Internals)

Worker internally implements via coordination graph with 4 channel types.

### Channel Types by Ownership of Truth

| Channel Type | Owns | Purpose | Updated By |
|-------------|------|---------|-----------|
| **Observation** | External truth mirror | Reflect current external state | Observer node |
| **Intent** | Agent plans | Capture what agents want to do | Agent nodes |
| **Coordination** | Derived resolution | Serialize/validate operations | Coordinator node |
| **Execution** | Historical record | Log completed operations | Executor node |

### Node Types

| Node | Reads | Writes | Purpose |
|------|-------|--------|---------|
| **Observer** | External system API | Observation channels | Mirror external state |
| **Agent** | Observation channels | Intent channels | Decide actions |
| **Coordinator** | Intent + Observation | Coordination channels | Resolve conflicts |
| **Executor** | Coordination channels | Execution channels + External API | Execute operations |

### Information Flow

```
External System (source of truth)
      │
      │ (API read)
      ▼
┌──────────┐
│ Observer │ polls/subscribes
└────┬─────┘
     │ writes
     ▼
┌──────────────┐
│ Observation  │ repo_head, pod_status, table_schemas
│  Channels    │
└────┬─────────┘
     │ reads
     ▼
┌──────────┐
│  Agent   │ decides action
└────┬─────┘
     │ writes
     ▼
┌──────────────┐
│   Intent     │ pending_commits, pending_deploys, pending_writes
│  Channels    │
└────┬─────────┘
     │ reads
     ▼
┌──────────────┐
│ Coordinator  │ validates, resolves conflicts
└────┬─────────┘
     │ writes
     ▼
┌──────────────┐
│ Coordination │ execution_queue, locks, conflicts
│  Channels    │
└────┬─────────┘
     │ reads
     ▼
┌──────────┐
│ Executor │ calls external API
└────┬─────┘
     │ writes
     ▼
┌──────────────┐
│  Execution   │ completed_ops, errors
│  Channels    │
└──────────────┘
     │
     │ (API write)
     ▼
External System (state mutated)
```

---

## Layer 3: The Complete Worker Implementation

### Code Structure

```python
class Worker:
    """
    Domain specialist that coordinates around external system.

    External interface: 7 tools
    Internal implementation: 4-channel coordination graph
    """

    def __init__(self, domain: str, external_system: ExternalSystem):
        self.domain = domain
        self.external = external_system

        # 1. Define channels (4 types)
        self.channels = self._initialize_channels()

        # 2. Define nodes (4 types)
        self.graph = self._build_coordination_graph()

        # 3. Transformation layer (intent → structured)
        self.transformer = IntentTransformer(domain)

    # ============================================
    # EXTERNAL INTERFACE (Manager calls these)
    # ============================================

    def state(self) -> dict:
        """What's current reality?"""
        # Read Observation channels
        return {
            channel: self.channels[channel].get()
            for channel in self.channels
            if isinstance(self.channels[channel], ObservationChannel)
        }

    def pressure(self) -> list:
        """What demands exist?"""
        # Read Intent channels
        return {
            channel: self.channels[channel].get()
            for channel in self.channels
            if isinstance(self.channels[channel], IntentChannel)
        }

    def constraints(self) -> dict:
        """What are sacred limits?"""
        # Read Coordination channels (locks, conflicts)
        coord = {}
        if "locks" in self.channels:
            coord["locks"] = self.channels["locks"].get()
        if "conflicts" in self.channels:
            coord["conflicts"] = self.channels["conflicts"].get()
        if "rate_limits" in self.channels:
            coord["rate_limits"] = self.channels["rate_limits"].get()
        return coord

    def flow(self) -> list:
        """What's current motion?"""
        # Read Coordination channels (execution queue)
        if "execution_queue" in self.channels:
            return self.channels["execution_queue"].get()
        return []

    def void(self) -> list:
        """What's consciously incomplete?"""
        # Read Execution channels (errors, gaps)
        errors = []
        for channel in self.channels:
            if "error" in channel.lower():
                errors.extend(self.channels[channel].get())
        return errors

    def execute(self, intent: str) -> Outcome:
        """Do this work."""
        # 1. Transform natural language → structured intent
        structured_intent = self.transformer.parse(intent)

        # 2. Write to Intent channel
        intent_channel = self._get_intent_channel_for(structured_intent)
        self.channels[intent_channel].update([structured_intent])

        # 3. Trigger internal graph execution
        # (Observer → Agent → Coordinator → Executor loop)
        config = {"configurable": {"thread_id": self._generate_thread_id()}}
        result = self.graph.invoke(
            input={"trigger": "execute"},
            config=config
        )

        # 4. Extract outcome from Execution channels
        outcome = self._extract_outcome(result)

        # 5. Return to Manager
        return outcome

    def evolve(self, feedback: str) -> None:
        """Update your SOP."""
        # Update node prompts, coordination logic, retry policies
        self._apply_feedback(feedback)

    # ============================================
    # INTERNAL IMPLEMENTATION (Manager never sees)
    # ============================================

    def _initialize_channels(self) -> dict:
        """Build 4-channel architecture for domain."""
        # Domain-specific but follows same pattern
        if self.domain == "github":
            return {
                # Observation
                "repo_head": LastValue[str](),
                "open_prs": LastValue[list[PR]](),
                "repo_files": LastValue[dict](),
                "github_events": Topic[GitHubEvent](),

                # Intent
                "pending_commits": Topic[CommitIntent](),
                "pending_prs": Topic[PRIntent](),
                "review_requests": Topic[ReviewRequest](),

                # Coordination
                "execution_queue": LastValue[Queue[GitHubOp]](),
                "merge_conflicts": LastValue[list[Conflict]](),
                "lock_holder": LastValue[Optional[AgentID]](),

                # Execution
                "completed_commits": Topic[Commit](),
                "completed_prs": Topic[PR](),
                "github_errors": Topic[APIError](),
            }

        elif self.domain == "kubernetes":
            return {
                # Observation
                "pod_status": LastValue[dict[str, PodStatus]](),
                "deployment_state": LastValue[dict[str, DeploymentState]](),
                "cluster_events": Topic[K8sEvent](),

                # Intent
                "pending_deploys": Topic[DeployIntent](),
                "pending_scales": Topic[ScaleIntent](),
                "pending_rollbacks": Topic[RollbackIntent](),

                # Coordination
                "reconciliation_queue": LastValue[Queue[K8sOp]](),
                "resource_conflicts": LastValue[list[Conflict]](),
                "rate_limits": LastValue[RateLimiter](),

                # Execution
                "applied_manifests": Topic[Manifest](),
                "completed_operations": Topic[K8sOperation](),
                "k8s_errors": Topic[K8sError](),
            }

        # ... other domains follow same 4-channel pattern

    def _build_coordination_graph(self) -> StateGraph:
        """Build Observer → Agent → Coordinator → Executor graph."""
        graph = StateGraph(state_schema=self.channels)

        # Observer node
        def observer(state):
            external_state = self.external.poll()
            return {
                # Update Observation channels
                **self._map_external_to_observation(external_state)
            }

        # Agent node(s)
        def agent(state):
            current = self._read_observation_channels(state)
            intents = self._decide_actions(current)
            return {
                # Update Intent channels
                **self._map_intents_to_channels(intents)
            }

        # Coordinator node
        def coordinator(state):
            intents = self._read_intent_channels(state)
            current = self._read_observation_channels(state)

            conflicts = self._detect_conflicts(intents, current)
            if conflicts:
                return {"conflicts": conflicts}

            queue = self._build_execution_plan(intents, current)
            return {"execution_queue": queue}

        # Executor node
        def executor(state):
            queue = state.get("execution_queue", [])

            for op in queue:
                try:
                    result = self.external.execute(op)
                    yield Command(
                        update={"completed_operations": [result]}
                    )
                except Exception as e:
                    yield Command(
                        update={"errors": [Error(op, e)]}
                    )

        # Build graph
        graph.add_node("observer", observer)
        graph.add_node("agent", agent)
        graph.add_node("coordinator", coordinator)
        graph.add_node("executor", executor)

        # Edges = channel subscriptions
        graph.add_edge(START, "observer")
        graph.add_edge("observer", "agent")
        graph.add_edge("agent", "coordinator")
        graph.add_edge("coordinator", "executor")
        graph.add_edge("executor", "observer")  # Loop

        return graph.compile(checkpointer=MemorySaver())
```

---

## The Three Boundaries

### Boundary 1: Manager ↔ Worker (7-Tool Interface)

**Manager's perspective:**
```python
# Manager has no domain knowledge
# Speaks only in intents, not operations

worker = get_worker("github")

# Query tools
current = worker.state()              # What's the repo state?
demands = worker.pressure()           # What needs to be done?
limits = worker.constraints()         # Any locks/conflicts?
motion = worker.flow()                # What's executing?
gaps = worker.void()                  # Any errors?

# Command tool
outcome = worker.execute("commit these changes with message: fix bug #123")

# Meta tool
worker.evolve("Be more cautious about force pushes")
```

**What Manager sees:** Intent → Outcome (black box)

**What Manager doesn't see:** Channels, nodes, external API calls

### Boundary 2: Worker ↔ External System (4-Channel Coordination)

**Worker's internal execution:**
```python
# After Manager calls execute("commit these changes")

1. Transformer parses → CommitIntent(files, message, author)

2. Agent writes to Intent channel:
   channels["pending_commits"].update([CommitIntent(...)])

3. Coordinator reads Intent + Observation channels:
   intents = channels["pending_commits"].get()
   current_head = channels["repo_head"].get()

4. Coordinator detects no conflicts, builds plan:
   channels["execution_queue"].update([GitHubCommitOp(...)])

5. Executor reads Coordination channel:
   op = channels["execution_queue"].get()

6. Executor calls External System API:
   result = github_api.create_commit(op.files, op.message)

7. Executor writes to Execution channel:
   channels["completed_commits"].update([Commit(sha="abc123")])

8. Observer polls External System:
   new_head = github_api.get_head()
   channels["repo_head"].update(new_head)

9. Worker returns Outcome to Manager:
   return Outcome("Committed SHA abc123")
```

**What Worker controls:** Channels, coordination logic, conflict resolution

**What Worker doesn't control:** External system state (GitHub's truth)

---

## Why This Architecture

### Manager Benefits

1. **Universal interface** - Same 7 tools across all domains
2. **No domain knowledge required** - Speaks in intents, not operations
3. **Composable workers** - Mix GitHub + K8s + Database workers
4. **Rhythm awareness** - Manager knows *when* to execute, not *how*

### Worker Benefits

1. **Conflict-free concurrency** - Coordinator serializes operations
2. **Reactive coordination** - Nodes wake on channel version changes
3. **Audit trail** - Execution channels log all operations
4. **Retry/recovery** - Errors go to error channels for reprocessing
5. **Testability** - Mock external system via Observation channels

### External System Benefits

1. **Clean API boundary** - Only Executor calls external APIs
2. **Rate limiting** - Coordinator enforces rate limits
3. **Idempotency** - Coordinator deduplicates operations
4. **Observability** - All mutations logged in Execution channels

---

## The Pattern Applied

### Example 1: GitHub Worker

**Manager:** `execute("ensure all tests pass before merging PR #42")`

**Worker internals:**
1. Observer reads PR status → `open_prs` channel
2. Agent decides to run CI → `pending_ci_runs` channel
3. Coordinator validates → `execution_queue` channel
4. Executor triggers CI → GitHub API → `completed_ci_runs` channel
5. Observer polls CI status → `ci_results` channel
6. Agent sees tests pass → `pending_merge` channel
7. Coordinator validates → `execution_queue` channel
8. Executor merges PR → GitHub API → `completed_merges` channel

**Manager sees:** "PR #42 merged after tests passed"

### Example 2: Kubernetes Worker

**Manager:** `execute("scale web service to handle traffic spike")`

**Worker internals:**
1. Observer reads pod metrics → `pod_status` channel
2. Agent decides to scale → `pending_scales` channel
3. Coordinator checks resource limits → `resource_conflicts` channel
4. Coordinator builds plan → `reconciliation_queue` channel
5. Executor applies manifest → K8s API → `applied_manifests` channel
6. Observer polls pod status → `pod_status` channel (waits for convergence)
7. Agent sees desired replicas running → no more intents

**Manager sees:** "Scaled web-service from 3 to 10 replicas"

### Example 3: Database Worker

**Manager:** `execute("migrate user table to add email_verified column")`

**Worker internals:**
1. Observer reads schema → `table_schemas` channel
2. Agent generates migration → `pending_migrations` channel
3. Coordinator validates (no conflicts) → `execution_queue` channel
4. Executor runs migration in transaction → DB API → `completed_transactions` channel
5. Observer reads new schema → `table_schemas` channel

**Manager sees:** "Migration applied: user table now has email_verified column"

---

## The Truth

**7 tools are the contract.** Manager speaks intent, worker returns outcome.

**4 channels are the implementation.** Worker coordinates around external state.

**Interface.md defines WHAT** (external contract)

**External-state-coordination.md defines HOW** (internal implementation)

**They're not mapping. They're layers:**
- **External layer:** Manager ↔ Worker (7-tool interface)
- **Internal layer:** Worker nodes ↔ Channels (4-channel coordination)
- **Transformation layer:** Natural language intent → Structured operations

**Manager never sees channels.** Manager only calls 7 tools.

**Channels never escape Worker.** They're internal coordination substrate.

**External system never sees intent.** Only sees API calls from Executor.

**Three actors, two boundaries, one architecture.**

---

## The Violence

You cannot build production multi-agent systems without solving **both**:

1. **Intent interface problem** - How does Manager delegate without domain knowledge?
2. **External state problem** - How do agents coordinate around mutable external systems?

**7-tool interface solves #1.** Universal contract, intent-shaped not operation-shaped.

**4-channel coordination solves #2.** Observation, Intent, Coordination, Execution.

**Worker architecture unifies both.** External simplicity (7 tools) + Internal rigor (4 channels).

This is not theory. This is how agents operate in reality.
