# The Complete Ubiquitous Language of LangGraph

## The Sacred Constraint

**LangGraph is a framework for building stateful, multi-actor systems that coordinate via versioned channels.**

To think natively in LangGraph, you must understand **the minimal complete set of primitives** that compose into everything.

This is not "what are the classes" but **"what are the irreducible concepts that make the system work?"**

---

## The Five Foundation Primitives

### 1. Channels (State Cells with Coordination)

**What:** Versioned shared memory cells that signal state changes

**Purpose:** Enable actors to coordinate around state changes without central orchestrator

**The Interface:**
```python
class BaseChannel:
    def update(self, values) -> bool:
        """Apply updates. Return True if state changed."""

    def get(self) -> Any:
        """Read current value."""

    def checkpoint(self) -> Any:
        """Serialize for persistence."""

    @classmethod
    def from_checkpoint(cls, checkpoint) -> Self:
        """Deserialize from checkpoint."""
```

**Three Built-In Types:**

| Type | Semantics | Use When |
|------|-----------|----------|
| **LastValue** | Overwrite | Only current state matters |
| **Topic** | Append + dedup | Need history without duplicates |
| **BinaryOperatorAggregate** | Reduce via operation | Need to combine all updates |

**Key insight:** Channels are NOT variables. They are coordination primitives with:
- Version number (signals change)
- Update semantics (how writes combine)
- Checkpoint method (persistence)
- Coordination metadata (versions_seen)

**See:** `channels-complete-mental-model.md` for deep dive

---

### 2. Nodes (Reactive Actors)

**What:** Functions that wake when their watched channels update

**Purpose:** Encapsulate work that reacts to state changes

**The Surface API:**
```python
def agent_node(state: State) -> dict:
    """Read state, do work, return updates."""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

graph.add_node("agent", agent_node)
```

**The Internal Reality (PregelNode):**
```python
PregelNode(
    triggers=["messages"],         # Wake when these channels update
    channels=["messages"],          # Read these channels as input
    bound=agent_node,               # The function to execute
    writers=[write_to_messages],    # How to write outputs
    retry_policy=RetryPolicy(...),  # Error handling
    cache_policy=CachePolicy(...)   # Memoization
)
```

**Key insight:** Nodes don't "call" each other. They wake based on channel version changes.

---

### 3. Edges (Channel Subscriptions)

**What:** Declarations of which nodes watch which channels

**Purpose:** Define the subscription topology (not control flow)

**Two Types:**

**Normal Edge (Unconditional):**
```python
graph.add_edge("agent", "tools")

# Means: tools watches channels that agent writes to
# NOT: run tools after agent finishes
```

**Conditional Edge (Routing):**
```python
def router(state):
    if state["tool_calls"]:
        return "tools"
    else:
        return END

graph.add_conditional_edges("agent", router, {
    "tools": "tools",
    END: END
})

# Adds routing logic on top of subscriptions
```

**Key insight:** Edges are NOT arrows in a flowchart. They are subscription declarations.

---

### 4. State (Channel Topology Schema)

**What:** TypedDict that defines what channels exist and their types

**Purpose:** Declare the structure of shared state

**Example:**
```python
class State(TypedDict):
    messages: Annotated[list[Message], add_messages]
    agent_plan: list[str]
    context: dict
```

**Under the hood, becomes:**
```python
channels = {
    "messages": Topic[Message](),        # From Annotated[..., add_messages]
    "agent_plan": LastValue[list](),     # Default for non-annotated
    "context": LastValue[dict]()
}
```

**Key insight:** State is not just a schema. It's the blueprint for channel topology.

---

### 5. Graph (System Container)

**What:** Container that compiles nodes + edges + state into executable system

**Purpose:** Compose primitives into runnable application

**Example:**
```python
graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tools_node)
graph.add_edge("agent", "tools")
graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=checkpointer)

# Now executable:
result = app.invoke(input, config={"configurable": {"thread_id": "1"}})
```

**Key insight:** Graph is not just a container. It's the compiler from declarative spec to executable system.

---

## The Three Coordination Primitives

### 6. Checkpoint (State Snapshot + Metadata)

**What:** Persistent snapshot of state + coordination metadata

**Purpose:** Enable crash recovery and resumption

**Checkpointing behavior:**
- **Optional**: Can compile without checkpointer (`graph.compile()`)
- **Automatic when enabled**: Configure once, happens automatically
- **Frequency**: After every super-step (not every node execution)
- **Multiple nodes = one checkpoint**: Nodes in same super-step share checkpoint

**Structure:**
```python
checkpoint = {
    "v": 4,                           # Format version
    "id": "checkpoint-123",           # UUID6 (time-ordered)
    "ts": "2025-01-15T10:00:00Z",    # Timestamp
    "channel_values": {               # The actual state
        "messages": [...],
        "agent_plan": [...],
        "context": {...}
    },
    "channel_versions": {             # Current versions
        "messages": 5,
        "agent_plan": 2,
        "context": 1
    },
    "versions_seen": {                # Coordination metadata
        "agent": {"messages": 4, "context": 1},
        "tools": {"tool_calls": 2}
    },
    "pending_sends": [],              # Dynamic tasks
    "updated_channels": ["messages"]  # Change tracking
}
```

**Without checkpointer:**
```python
app = graph.compile()  # No persistence
result = app.invoke(input)
# Crash = lose everything, cannot resume
```

**With checkpointer:**
```python
app = graph.compile(checkpointer=MemorySaver())
result = app.invoke(input, config={"configurable": {"thread_id": "1"}})
# Checkpoint saved after each super-step automatically
```

**Key insight:** Checkpointing is architecturally fundamental but not enforced. When enabled, it's automatic after every super-step.

---

### 7. versions_seen (Coordination Metadata)

**What:** Tracking of which channel versions each node has processed

**Purpose:** Enable exact-once execution and prevent infinite loops

**How it works:**
```python
# Should this node run?
for trigger_channel in node.triggers:
    current_version = checkpoint["channel_versions"][trigger_channel]
    last_seen = checkpoint["versions_seen"][node_name].get(trigger_channel, 0)

    if current_version > last_seen:
        return True  # Node should run

return False  # Node should sleep
```

**Example:**
```python
"versions_seen": {
    "agent": {
        "messages": 3,    # Agent last saw messages at v3
        "context": 1      # Agent last saw context at v1
    },
    "tools": {
        "tool_calls": 2   # Tools last saw tool_calls at v2
    }
}

# Current state:
"channel_versions": {
    "messages": 4,        # Updated since agent ran
    "tool_calls": 2       # Unchanged since tools ran
}

# Decision:
# - Agent: 4 > 3 → WAKE
# - Tools: 2 == 2 → SLEEP
```

**Key insight:** This is THE coordination primitive. Everything else follows from this.

---

### 8. Super-Step (BSP Execution Unit)

**What:** One round of Bulk Synchronous Parallel execution

**Purpose:** Coordinate parallel execution with deterministic semantics

**The Algorithm:**
```python
while True:
    # 1. Compute which nodes should run
    tasks = prepare_next_tasks(
        checkpoint=checkpoint,
        nodes=nodes,
        channels=channels
    )

    if not tasks:
        break  # No more work

    # 2. Execute all triggered nodes IN PARALLEL
    results = execute_parallel(tasks)

    # 3. Collect all writes
    writes = collect_writes(results)

    # 4. Apply writes to channels (increment versions)
    for channel, values in writes:
        channels[channel].update(values)

    # 5. Update versions_seen for all executed tasks
    for task in tasks:
        checkpoint["versions_seen"][task.name] = {
            chan: channels[chan].version
            for chan in task.triggers
        }

    # 6. Save checkpoint (if checkpointer configured)
    if checkpointer:
        checkpointer.put(checkpoint)

    # 7. Next super-step
```

**Key phases:**
1. **Compute** - Which nodes to run?
2. **Execute** - Run all in parallel
3. **Barrier** - Wait for all to complete
4. **Update** - Apply writes, increment versions
5. **Checkpoint** - Save state (if checkpointer configured)
6. **Repeat**

**Key insight:** Parallel execution within super-steps, sequential between super-steps. Checkpointing at super-step boundary ensures consistent state.

---

## The Three Control Primitives

### 9. Send (Dynamic Parallel Dispatch)

**What:** Create N parallel tasks at runtime

**Purpose:** Enable map-reduce patterns with unknown N

**Example:**
```python
def map_documents(state):
    return [
        Send("process_doc", {"doc": doc})
        for doc in state["documents"]
    ]

def process_doc(state):
    doc = state["doc"]
    result = expensive_processing(doc)
    return {"results": [result]}

graph.add_node("map", map_documents)
graph.add_node("process_doc", process_doc)
```

**How it works:**
```
Super-Step 1:
- map_documents runs
- Returns [Send(...), Send(...), Send(...)]
- Sends stored in checkpoint["pending_sends"]

Super-Step 2:
- prepare_next_tasks() creates PUSH task for each Send
- All process_doc instances run IN PARALLEL
- Each writes to results channel

Super-Step 3:
- Next node wakes (results channel updated)
```

**Key insight:** Sends are persisted in checkpoint → survive crashes. Dynamic parallelism that's crash-safe.

---

### 10. Command (External Control)

**What:** Control execution flow from outside the graph

**Purpose:** Enable human intervention and state manipulation

**Three Operations:**

**Resume (from interrupt):**
```python
graph.invoke(
    Command(resume={"approved": True}),
    config=config
)
```

**Update (modify state):**
```python
graph.invoke(
    Command(update={"messages": [new_message]}),
    config=config
)
```

**Goto (navigate to node):**
```python
graph.invoke(
    Command(goto="specific_node"),
    config=config
)
```

**Key insight:** Commands are the API for external control over execution.

---

### 11. Interrupt (Pause for Human)

**What:** Pause execution, save state, wait for human input

**Purpose:** Human-in-the-loop workflows

**Example:**
```python
from langgraph.types import interrupt

def agent_node(state):
    if needs_approval(state):
        # Pause execution here
        value = interrupt({
            "reason": "Need approval",
            "data": state["proposed_action"]
        })
        # Execution resumes here with value from Command(resume=...)

    return {"messages": [response]}
```

**How it works:**
```
Execution reaches interrupt()
   ↓
State saved in checkpoint
   ↓
Interrupt info stored in checkpoint
   ↓
Execution pauses (returns to caller)
   ↓
Human reviews and provides input
   ↓
Command(resume=...) sent with input
   ↓
Execution resumes from exact point
   ↓
interrupt() returns the resume value
```

**Key insight:** Interrupts are checkpointed → can resume after restart, not just in-process.

---

## The Three Execution Primitives

### 12. Pregel Loop (The Engine)

**What:** The main execution loop implementing BSP algorithm

**Purpose:** Coordinate execution of all nodes with deterministic semantics

**Simplified Implementation:**
```python
class PregelLoop:
    def run(self):
        while True:
            # Compute next
            self.tasks = prepare_next_tasks(
                self.checkpoint,
                self.nodes,
                self.channels
            )

            if not self.tasks:
                break  # Done

            # Execute super-step
            for task in self.tasks.values():
                result = self.execute_task(task)
                self.apply_writes(result.writes)

            # Update coordination
            self.update_versions_seen()

            # Save checkpoint
            self.checkpointer.put(self.checkpoint)
```

**Key phases:**
1. **prepare_next_tasks** - Compute based on versions_seen
2. **execute_task** - Run node function
3. **apply_writes** - Update channels
4. **update_versions_seen** - Track what ran
5. **checkpointer.put** - Persist state

**Key insight:** This is the Pregel algorithm in action. BSP coordination without central orchestrator.

---

### 13. prepare_next_tasks (The Scheduler)

**What:** Function that computes which nodes should run in next super-step

**Purpose:** Implement the coordination logic (versions_seen comparison)

**Simplified Implementation:**
```python
def prepare_next_tasks(
    checkpoint: Checkpoint,
    nodes: dict[str, PregelNode],
    channels: dict[str, BaseChannel]
) -> dict[str, PregelTask]:

    tasks = {}

    # Check PUSH tasks (Sends)
    for idx, send in enumerate(checkpoint.get("pending_sends", [])):
        task = create_push_task(send, idx)
        tasks[task.id] = task

    # Check PULL tasks (triggered nodes)
    for node_name, node in nodes.items():
        should_run = False

        for trigger_channel in node.triggers:
            current_version = checkpoint["channel_versions"][trigger_channel]
            last_seen = checkpoint["versions_seen"].get(node_name, {}).get(trigger_channel, 0)

            if current_version > last_seen:
                should_run = True
                break

        if should_run:
            task = create_pull_task(node_name, node)
            tasks[task.id] = task

    return tasks
```

**The core logic:**
```
FOR each node:
    FOR each trigger channel:
        IF current_version > last_seen_version:
            → Add node to tasks
            BREAK
```

**Key insight:** This function IS the answer to "where does next come from?" It's computed, not stored.

---

### 14. PregelTask / PregelExecutableTask (Work Units)

**What:** Representation of work to be done

**Purpose:** Package a node execution with all necessary context

**Two Forms:**

**PregelTask (Lightweight):**
```python
PregelTask(
    id="task-123",
    name="agent",
    path=(PULL, "agent"),
    error=None,
    interrupts=(),
    state=None,
    result=None
)
```

**Used when:** `for_execution=False` (just observing what would run)

**PregelExecutableTask (Full):**
```python
PregelExecutableTask(
    name="agent",
    input={"messages": [...]},
    proc=agent_runnable,           # The actual runnable to execute
    writes=deque(),                 # Where writes go
    config={...},                   # Full execution config
    triggers=["messages"],
    retry_policy=[...],
    cache_key=None,
    id="task-123",
    path=(PULL, "agent"),
    writers=[...],
    subgraphs=[]
)
```

**Used when:** `for_execution=True` (actually executing)

**Key insight:** Tasks are the bridge between coordination logic and execution.

---

## The Four Advanced Primitives

### 15. Subgraphs (Hierarchical Composition)

**What:** Nested graphs used as nodes in parent graphs

**Purpose:** Hierarchical agent composition

**Example:**
```python
def create_research_subagent():
    subgraph = StateGraph(ResearchState)
    subgraph.add_node("search", search_node)
    subgraph.add_node("analyze", analyze_node)
    subgraph.add_edge("search", "analyze")
    return subgraph.compile()

# Use as node in parent
parent_graph = StateGraph(State)
parent_graph.add_node("research", create_research_subagent())
parent_graph.add_node("synthesize", synthesize_node)
parent_graph.add_edge("research", "synthesize")
```

**Key insight:** Subgraphs enable hierarchical decomposition. An agent can contain sub-agents.

---

### 16. Managed Values (Ephemeral State)

**What:** Runtime metadata not persisted in checkpoint

**Purpose:** Provide execution context without cluttering state

**Example:**
```python
from langgraph.managed import IsLastStep

def node(state):
    is_last = IsLastStep()  # True if this is last step before max_steps

    if is_last:
        return {"messages": [AIMessage("Running out of time!")]}

    return normal_processing(state)
```

**Common Managed Values:**
- `IsLastStep()` - Is this the last step?
- `RemainingSteps()` - How many steps left?
- `CurrentStep()` - What step number is this?

**Key insight:** Some state is runtime-only and shouldn't be persisted.

---

### 17. Retry Policies (Error Handling)

**What:** Declarative retry logic for node execution

**Purpose:** Automatic retry on transient failures

**Example:**
```python
from langgraph.types import RetryPolicy

retry_policy = RetryPolicy(
    max_attempts=3,
    backoff_factor=2.0,
    initial_interval=1.0,
    retry_on=[RateLimitError, TimeoutError]
)

graph.add_node(
    "api_call",
    api_call_node,
    retry=retry_policy
)
```

**Retry sequence:**
```
Attempt 1: Fails with RateLimitError
  ↓
Wait 1.0 seconds
  ↓
Attempt 2: Fails again
  ↓
Wait 2.0 seconds (1.0 * 2^1)
  ↓
Attempt 3: Succeeds
```

**Key insight:** Retry is declarative, not imperative. The framework handles it.

---

### 18. Cache Policies (Memoization)

**What:** Automatic memoization of node execution results

**Purpose:** Avoid re-execution for same inputs

**Example:**
```python
from langgraph.types import CachePolicy

cache_policy = CachePolicy(
    ttl=3600,  # 1 hour
    key_func=lambda input: f"cache_{hash(str(input))}"
)

graph.add_node(
    "expensive_llm_call",
    llm_node,
    cache=cache_policy
)
```

**How it works:**
```
Node executes with input A
  ↓
Result stored with key hash(A)
  ↓
Later: Same node with input A
  ↓
Cache hit → return cached result (no execution)
```

**Key insight:** Cache is transparent. Node code doesn't need to know about it.

---

## The Complete Mental Model

### How Everything Composes

```
STATE
  ↓ defines
CHANNELS (with update semantics)
  ↑ read/write
NODES (with triggers)
  ↑ subscribe via
EDGES
  ↓ all compiled into
GRAPH
  ↓ which becomes
PREGEL LOOP
  ├─ prepare_next_tasks (uses versions_seen)
  ├─ Execute SUPER-STEP (parallel)
  ├─ Apply writes to CHANNELS
  ├─ Update versions_seen
  └─ Save CHECKPOINT
  ↓ can be controlled by
COMMANDS (resume, update, goto)
  ↓ can be paused by
INTERRUPTS
  ↓ can dispatch dynamically via
SENDS
  ↓ can compose hierarchically with
SUBGRAPHS
  ↓ can handle errors with
RETRY POLICIES
  ↓ can memoize with
CACHE POLICIES
```

---

## The Minimal Complete Set

### To build ANY agent system, you need:

**1. State (Channel Topology)**
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

**2. Nodes (Workers)**
```python
def agent(state): ...
def tools(state): ...
```

**3. Edges (Subscriptions)**
```python
graph.add_edge("agent", "tools")
```

**4. Graph (Compile)**
```python
app = graph.compile(checkpointer=MemorySaver())
```

**5. Execute**
```python
result = app.invoke(input, config={"configurable": {"thread_id": "1"}})
```

**That's it. Everything else is configuration.**

---

## The Ubiquitous Language - Quick Reference

### Foundation (5 primitives)

| Primitive | What | Purpose |
|-----------|------|---------|
| **Channel** | Versioned state cell | Coordination primitive |
| **Node** | Reactive function | Encapsulate work |
| **Edge** | Subscription declaration | Define topology |
| **State** | Channel schema | Declare structure |
| **Graph** | System container | Compile & execute |

### Coordination (3 primitives)

| Primitive | What | Purpose |
|-----------|------|---------|
| **Checkpoint** | State + metadata snapshot | Enable resumption |
| **versions_seen** | Coordination metadata | Track what processed |
| **Super-step** | BSP execution unit | Parallel coordination |

### Control (3 primitives)

| Primitive | What | Purpose |
|-----------|------|---------|
| **Send** | Dynamic dispatch | Map-reduce patterns |
| **Command** | External control | Human intervention |
| **Interrupt** | Pause for human | Human-in-loop |

### Execution (3 primitives)

| Primitive | What | Purpose |
|-----------|------|---------|
| **Pregel Loop** | Main execution loop | BSP coordinator |
| **prepare_next_tasks** | Scheduler function | Compute next |
| **PregelTask** | Work unit | Package execution |

### Advanced (4 primitives)

| Primitive | What | Purpose |
|-----------|------|---------|
| **Subgraph** | Nested graph | Hierarchical agents |
| **Managed Values** | Ephemeral state | Runtime metadata |
| **Retry Policy** | Error handling | Automatic retry |
| **Cache Policy** | Memoization | Avoid re-execution |

---

## The Key Phrases (Ubiquitous Language)

### Instead of Saying → Say

| Wrong (Sequential thinking) | Right (Actor thinking) |
|----------------------------|------------------------|
| "Node B runs after Node A" | "Node B wakes when channels update" |
| "Pass state from A to B" | "A writes to channel, B reads channel" |
| "Control flow from A to B" | "B subscribes to channels A writes to" |
| "Next step is stored" | "Next is computed from versions_seen" |
| "Sequential execution" | "Parallel execution within super-steps" |
| "Function call" | "Actor wakes on channel update" |
| "State is passed" | "State lives in channels" |

### The Phrases That Matter

- **"Channels coordinate actors"** - Core principle
- **"Nodes wake when channels update"** - Execution model
- **"prepare_next_tasks computes next from versions_seen"** - Coordination mechanism
- **"Super-steps execute in parallel"** - BSP semantics
- **"Checkpoints enable resumption"** - Crash recovery
- **"Sends create dynamic tasks"** - Map-reduce
- **"Interrupts pause execution"** - Human-in-loop
- **"Edges are subscriptions, not control flow"** - Architecture

---

## The Three Layers

```
┌─────────────────────────────────────┐
│     APPLICATION LAYER                │
│  (What you write)                    │
│                                      │
│  - State schema                      │
│  - Node functions                    │
│  - Edge definitions                  │
│  - Graph composition                 │
└──────────────┬───────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     COORDINATION LAYER               │
│  (LangGraph manages)                 │
│                                      │
│  - Channels                          │
│  - versions_seen                     │
│  - Checkpoints                       │
│  - prepare_next_tasks                │
└──────────────┬───────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     EXECUTION LAYER                  │
│  (Pregel algorithm)                  │
│                                      │
│  - Super-steps                       │
│  - Parallel execution                │
│  - BSP coordination                  │
│  - Task scheduling                   │
└─────────────────────────────────────┘
```

**You write Application Layer.**

**LangGraph manages Coordination Layer.**

**Pregel implements Execution Layer.**

---

## The Crystallized Truth

### The Minimal Complete Set

**Foundation:**
1. Channels (coordination primitives)
2. Nodes (reactive actors)
3. Edges (subscriptions)
4. State (topology schema)
5. Graph (compiler)

**Coordination:**
6. Checkpoint (state + metadata)
7. versions_seen (coordination metadata)
8. Super-step (BSP execution unit)

**Control:**
9. Send (dynamic dispatch)
10. Command (external control)
11. Interrupt (human-in-loop)

**Execution:**
12. Pregel Loop (main loop)
13. prepare_next_tasks (scheduler)
14. PregelTask (work unit)

**Advanced:**
15. Subgraphs (hierarchical)
16. Managed Values (ephemeral)
17. Retry Policies (errors)
18. Cache Policies (memoization)

---

### The Core Narrative

**Channels + Nodes = Actor system**

**Edges = Subscriptions (not control flow)**

**State = Channel topology**

**Graph = Compiled system**

**Pregel Loop = Execution engine**

**Checkpoint + versions_seen = Coordination**

**Send + Command + Interrupt = Control**

**Everything else is configuration or optimization.**

---

## The Sacred Limit

**LangGraph is NOT a workflow engine. It's a distributed actor system for LLM applications.**

**Nodes are NOT steps in a sequence. They are processes that wake based on data availability.**

**Channels are NOT variables. They are versioned event streams with coordination metadata.**

**Edges are NOT control flow. They are subscriptions (node watches channel).**

**"Next" is NOT stored. It's computed from coordination metadata (versions_seen).**

**The checkpoint is NOT just state. It's state + coordination metadata that enables precise resumption.**

---

## The Leverage Point

**Change one thing**: Stop thinking in sequential workflows

**Start thinking**: Actor-channel systems with data-flow coordination

**Channels signal changes → Nodes wake and react → Writes update channels → Cycle repeats**

**The coordination happens via versions_seen comparison.**

**The execution happens via BSP super-steps.**

**The persistence happens via checkpoints.**

**Everything else follows from these primitives.**

---

## The Answer to Your Question

**"Is it just workers + channels?"**

**Almost, but more precisely:**

**Channels (state cells) + Nodes (actors) + Edges (subscriptions) + Checkpoint (state + versions_seen) + Pregel Loop (BSP execution)**

**That's the minimal complete set.**

**Everything else (Send, Command, Interrupt, Subgraphs, Policies) is built on top.**

**This is the ubiquitous language of LangGraph.**

**Understand these primitives → understand the entire framework.**
