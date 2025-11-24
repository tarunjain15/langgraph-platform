# The Complete Entity Model: Where "Next" Comes From

## The Question

**"Checkpoint can be alone then. What other key entities are there? For example, where is the next expected coming from? Some entity must have it."**

## The Answer

**`next` doesn't live anywhere permanently. It's computed dynamically by `prepare_next_tasks()` based on checkpoint coordination metadata.**

---

## The Five Core Entities

### 1. **Checkpoint** (The State + Coordination Record)

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:58-84`:

```python
class Checkpoint(TypedDict):
    v: int                           # Format version (currently 4)
    id: str                          # UUID6 (time-ordered, monotonic)
    ts: str                          # ISO 8601 timestamp
    channel_values: dict[str, Any]   # The actual state
    channel_versions: ChannelVersions  # Version per channel
    versions_seen: dict[str, ChannelVersions]  # Coordination primitive
    updated_channels: list[str] | None  # Change tracking
```

**Purpose**: Persistent record of state + execution coordination metadata

**Where it lives**: Database (SQLite, Postgres, etc.)

**Key insight**: Contains `versions_seen` which is THE input to compute "next"

---

### 2. **StateSnapshot** (The User-Facing View)

From `/libs/langgraph/langgraph/types.py:249-257`:

```python
class StateSnapshot(NamedTuple):
    values: dict[str, Any] | Any      # Current channel values
    next: tuple[str, ...]              # ← THE ANSWER: Computed nodes to execute
    config: RunnableConfig             # Config used to fetch snapshot
    metadata: CheckpointMetadata | None
    created_at: str | None
    parent_config: RunnableConfig | None
    tasks: tuple[PregelTask, ...]      # Tasks to execute
    interrupts: tuple[Interrupt, ...]  # Pending interrupts
```

**Purpose**: User-facing representation of graph state at a point in time

**Where it lives**: Constructed on-demand when user calls `.get_state()`

**Key insight**: `next` field is **computed**, not stored. It's derived from `tasks`.

**How `next` is populated:**

From observation of the codebase:

```python
# StateSnapshot construction (simplified)
snapshot = StateSnapshot(
    values=checkpoint["channel_values"],
    next=tuple(task.name for task in tasks),  # Extract node names from tasks
    config=config,
    metadata=metadata,
    tasks=tasks,
    interrupts=interrupts
)
```

**The violence**: `next` is not persisted anywhere. It's recomputed every time you ask "what's next?"

---

### 3. **PregelNode** (The Actor Definition)

From `/libs/langgraph/langgraph/pregel/_read.py:94-174`:

```python
class PregelNode:
    """A node in a Pregel graph."""

    channels: str | list[str]
    """The channels that will be passed as input to `bound`."""

    triggers: list[str]
    """If any of these channels is written to, this node will be triggered."""

    mapper: Callable[[Any], Any] | None
    """A function to transform the input before passing it to `bound`."""

    writers: list[Runnable]
    """Writers that execute after `bound`, write output to channels."""

    bound: Runnable[Any, Any]
    """The main logic of the node."""

    retry_policy: Sequence[RetryPolicy] | None
    cache_policy: CachePolicy | None
    tags: Sequence[str] | None
    metadata: Mapping[str, Any] | None
    subgraphs: Sequence[PregelProtocol]
```

**Purpose**: Blueprint for a node - what it reads, what triggers it, what it runs

**Where it lives**: In-memory graph definition (created when you call `graph.add_node()`)

**Key insight**: `triggers` field determines which channels must update for this node to run

---

### 4. **PregelTask** (Lightweight Task Representation)

From `/libs/langgraph/langgraph/types.py:204-214`:

```python
class PregelTask(NamedTuple):
    """A Pregel task."""

    id: str                                  # Task identifier
    name: str                                # Node name
    path: tuple[str | int | tuple, ...]      # Task path (PULL/PUSH + identifiers)
    error: Exception | None = None           # Error if task failed
    interrupts: tuple[Interrupt, ...] = ()   # Interrupts raised by task
    state: None | RunnableConfig | StateSnapshot = None  # Task state (for subgraphs)
    result: Any | None = None                # Task result (if completed)
```

**Purpose**: Minimal representation of a task for observation/inspection

**Where it lives**: Returned in StateSnapshot.tasks, checkpoint metadata

**Used when**: `for_execution=False` (when you just want to see what would run)

---

### 5. **PregelExecutableTask** (Full Task with Runnable)

From `/libs/langgraph/langgraph/types.py:234-247`:

```python
@dataclass(frozen=True)
class PregelExecutableTask:
    name: str                              # Node name
    input: Any                             # Input to pass to node
    proc: Runnable                         # The runnable to execute
    writes: deque[tuple[str, Any]]         # Where node writes go
    config: RunnableConfig                 # Full execution config
    triggers: Sequence[str]                # Which channels triggered this
    retry_policy: Sequence[RetryPolicy]
    cache_key: CacheKey | None
    id: str                                # Task ID
    path: tuple[str | int | tuple, ...]    # Task path
    writers: Sequence[Runnable] = ()       # Channel writers
    subgraphs: Sequence[PregelProtocol] = ()
```

**Purpose**: Full task ready for execution with all context

**Where it lives**: In-memory during execution

**Used when**: `for_execution=True` (when you're about to actually run tasks)

**Key difference from PregelTask**: Contains the actual `proc: Runnable` to execute

---

## Supporting Entities

### 6. **CheckpointTuple** (Checkpoint + Context)

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:101-109`:

```python
class CheckpointTuple(NamedTuple):
    """A tuple containing a checkpoint and its associated data."""

    config: RunnableConfig              # Config used to create checkpoint
    checkpoint: Checkpoint              # The checkpoint itself
    metadata: CheckpointMetadata        # Metadata about checkpoint
    parent_config: RunnableConfig | None = None
    pending_writes: list[PendingWrite] | None = None
```

**Purpose**: Wraps checkpoint with its retrieval context

**Where it lives**: Returned by `checkpointer.get_tuple(config)`

**Why it exists**: Need to return checkpoint + metadata + pending writes together

---

### 7. **CheckpointMetadata** (Checkpoint Provenance)

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:30-52`:

```python
class CheckpointMetadata(TypedDict, total=False):
    """Metadata associated with a checkpoint."""

    source: Literal["input", "loop", "update", "fork"]
    """The source of the checkpoint.
    - "input": From invoke/stream/batch
    - "loop": From inside Pregel loop
    - "update": From manual state update
    - "fork": Copy of another checkpoint
    """

    step: int
    """The step number of the checkpoint.
    -1 for first "input" checkpoint.
    0 for first "loop" checkpoint.
    """

    parents: dict[str, str]
    """The IDs of the parent checkpoints.
    Mapping from checkpoint namespace to checkpoint ID.
    """
```

**Purpose**: Track where checkpoint came from and its position in execution

**Where it lives**: Stored alongside checkpoint in database

---

### 8. **PendingWrite** (Uncommitted Channel Update)

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:26`:

```python
PendingWrite = tuple[str, str, Any]
# (task_id, channel_name, value)
```

**Purpose**: Track writes that haven't been committed to checkpoint yet

**Example:**
```python
pending_writes = [
    ("task_123", "messages", {"role": "assistant", "content": "Hello"}),
    ("task_456", "counter", 5),
]
```

**Why it exists**: Allows buffering writes before checkpoint commit

---

### 9. **Send** (Dynamic Parallel Dispatch)

From `/libs/langgraph/langgraph/types.py:78-95`:

```python
class Send:
    """A message to send to a node."""

    node: str
    """The name of the target node."""

    arg: Any
    """The input to pass to the target node."""

    callbacks: Callbacks | None = None
    """Callbacks to use for the target node."""
```

**Purpose**: Enable dynamic fan-out (map-reduce patterns)

**Example:**
```python
def route_documents(state):
    return [
        Send("process_doc", {"doc": doc})
        for doc in state["documents"]
    ]
```

**Where it lives**:
- Emitted by nodes as return values
- Stored in `checkpoint["pending_sends"]`
- Consumed by `prepare_next_tasks()` as PUSH tasks

---

### 10. **Interrupt** (Human-in-the-Loop Signal)

From `/libs/langgraph/langgraph/types.py:148-196`:

```python
class Interrupt:
    """An interrupt signal for human-in-the-loop."""

    value: Any
    """The value associated with the interrupt."""

    id: str
    """The ID of the interrupt. Can be used to resume."""
```

**Purpose**: Signal that execution should pause for human input

**Example:**
```python
# Node raises interrupt
raise NodeInterrupt({"reason": "Need approval", "data": document})

# Later, resume with:
graph.invoke(Command(resume={"approved": True}), config)
```

---

## The Critical Function: `prepare_next_tasks()`

From `/libs/langgraph/langgraph/pregel/_algo.py:367-493`:

```python
def prepare_next_tasks(
    checkpoint: Checkpoint,
    pending_writes: list[PendingWrite],
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, BaseChannel],
    managed: ManagedValueMapping,
    config: RunnableConfig,
    step: int,
    stop: int,
    *,
    for_execution: bool,
    store: BaseStore | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    manager: None | ParentRunManager | AsyncParentRunManager = None,
    trigger_to_nodes: Mapping[str, Sequence[str]] | None = None,
    updated_channels: set[str] | None = None,
    retry_policy: Sequence[RetryPolicy] = (),
    cache_policy: CachePolicy | None = None,
) -> dict[str, PregelTask] | dict[str, PregelExecutableTask]:
    """Prepare the set of tasks that will make up the next Pregel step.

    Returns:
        A dictionary of tasks to be executed. The keys are the task ids and the values
        are the tasks themselves. This is the union of all PUSH tasks (Sends)
        and PULL tasks (nodes triggered by edges).
    """
```

**This is where `next` comes from.**

---

## How `prepare_next_tasks()` Computes "Next"

### Step 1: Check for PUSH Tasks (Send Commands)

From lines 416-441:

```python
# Consume pending tasks (Send commands stored in checkpoint)
tasks_channel = channels.get(TASKS)
if tasks_channel and tasks_channel.is_available():
    for idx, _ in enumerate(tasks_channel.get()):
        if task := prepare_single_task(
            (PUSH, idx),  # Task path for Send
            # ... other params
        ):
            tasks.append(task)
```

**PUSH tasks = Dynamic sends** (map-reduce pattern)

---

### Step 2: Determine Candidate Nodes for PULL Tasks

From lines 443-461:

```python
# Optimization: If we know which channels updated, only check triggered nodes
if updated_channels and trigger_to_nodes:
    triggered_nodes: set[str] = set()
    for channel in updated_channels:
        if node_ids := trigger_to_nodes.get(channel):
            triggered_nodes.update(node_ids)
    candidate_nodes = sorted(triggered_nodes)
elif not checkpoint["channel_versions"]:
    candidate_nodes = ()  # No channels updated yet
else:
    candidate_nodes = processes.keys()  # Check all nodes
```

**Optimization**: Don't check all nodes if we know which channels changed

---

### Step 3: Check Each Candidate Node Using `_triggers()`

From lines 463-482:

```python
for name in candidate_nodes:
    if task := prepare_single_task(
        (PULL, name),  # Task path for regular node
        # ... other params
    ):
        tasks.append(task)
```

Inside `prepare_single_task()` at line 776-782:

```python
# If any of the channels read by this process were updated
if _triggers(
    channels,
    checkpoint["channel_versions"],
    checkpoint["versions_seen"].get(name),
    checkpoint_null_version,
    proc,
):
    # Create and return task
```

---

### The `_triggers()` Decision Function

From `/libs/langgraph/langgraph/pregel/_algo.py:931-948`:

```python
def _triggers(
    channels: Mapping[str, BaseChannel],
    versions: ChannelVersions,          # Current channel versions
    seen: ChannelVersions | None,       # Versions this node has seen
    null_version: V,                    # 0 for int, 0.0 for float, "" for str
    proc: PregelNode,
) -> bool:
    """Determine if a node should be triggered."""

    if seen is None:
        # Node has never run - trigger if any input channel has data
        for chan in proc.triggers:
            if channels[chan].is_available():
                return True
    else:
        # Node has run before - trigger if any input channel updated
        for chan in proc.triggers:
            if channels[chan].is_available() and versions.get(
                chan, null_version
            ) > seen.get(chan, null_version):
                return True

    return False
```

**The algorithm:**

```
FOR each trigger channel of this node:
    current_version = checkpoint["channel_versions"][channel]
    last_seen_version = checkpoint["versions_seen"][node_name].get(channel, 0)

    IF current_version > last_seen_version:
        → Node should run (channel updated since node last ran)
    ELSE:
        → Node should not run (channel unchanged)
```

**This is the Pregel coordination primitive in action.**

---

## Execution Flow: From Checkpoint to StateSnapshot

### Full Flow:

```python
# 1. User calls get_state()
config = {"configurable": {"thread_id": "thread-123"}}
snapshot = graph.get_state(config)

# 2. LangGraph loads checkpoint from database
checkpoint_tuple = checkpointer.get_tuple(config)
checkpoint = checkpoint_tuple.checkpoint

# 3. Compute which tasks should run next
tasks = prepare_next_tasks(
    checkpoint=checkpoint,
    pending_writes=checkpoint_tuple.pending_writes,
    processes=graph.nodes,  # PregelNode definitions
    channels=graph.channels,
    step=checkpoint_tuple.metadata["step"],
    for_execution=False,  # Just want task list, not execution
    # ... other params
)

# 4. Extract "next" from tasks
next_nodes = tuple(task.name for task in tasks.values())

# 5. Construct StateSnapshot
snapshot = StateSnapshot(
    values=checkpoint["channel_values"],
    next=next_nodes,  # ← Computed here
    config=config,
    metadata=checkpoint_tuple.metadata,
    tasks=tuple(tasks.values()),
    interrupts=extract_interrupts(checkpoint),
)

# 6. Return to user
return snapshot
```

---

## Example: Computing "Next"

### Initial State:

```python
checkpoint = {
    "v": 4,
    "id": "checkpoint-001",
    "ts": "2025-01-15T10:00:00Z",
    "channel_values": {
        "messages": [{"role": "human", "content": "Hello"}],
        "agent_plan": None,
    },
    "channel_versions": {
        "messages": 1,
        "agent_plan": 0,
    },
    "versions_seen": {
        "__start__": {"messages": 0},  # Start node hasn't seen messages v1 yet
    },
    "updated_channels": ["messages"]
}

graph.nodes = {
    "__start__": PregelNode(
        triggers=["messages"],  # Triggered when messages updates
        channels="messages",
        bound=start_node_runnable
    ),
    "agent": PregelNode(
        triggers=["agent_plan"],
        channels="agent_plan",
        bound=agent_runnable
    )
}
```

### Computing Next:

```python
# Step 1: Check PUSH tasks → None
# Step 2: Candidate nodes → ["__start__", "agent"]

# Step 3: Check __start__ node
_triggers(
    versions={"messages": 1, "agent_plan": 0},
    seen={"messages": 0},  # __start__ last saw messages at v0
    proc.triggers=["messages"]
)
→ current_version (1) > last_seen_version (0)
→ TRIGGER __start__

# Step 4: Check agent node
_triggers(
    versions={"messages": 1, "agent_plan": 0},
    seen=None,  # Agent hasn't run yet
    proc.triggers=["agent_plan"]
)
→ agent_plan version is 0 (no data yet)
→ channels[agent_plan].is_available() → False
→ DO NOT TRIGGER agent

# Result:
tasks = {
    "task_001": PregelTask(id="task_001", name="__start__", path=(PULL, "__start__"))
}

next = ("__start__",)  # Only __start__ will run
```

### After `__start__` Executes:

```python
# __start__ writes to agent_plan channel

checkpoint = {
    # ... same id, ts ...
    "channel_values": {
        "messages": [{"role": "human", "content": "Hello"}],
        "agent_plan": ["retrieve_docs", "generate_answer"],
    },
    "channel_versions": {
        "messages": 1,      # Unchanged
        "agent_plan": 1,    # Updated by __start__
    },
    "versions_seen": {
        "__start__": {"messages": 1},  # __start__ saw messages v1
        # agent hasn't run yet
    },
    "updated_channels": ["agent_plan"]
}

# Computing next again:
_triggers(
    versions={"messages": 1, "agent_plan": 1},
    seen={"messages": 1},
    proc.triggers=["messages"]
)
→ messages version 1 == last_seen 1
→ DO NOT TRIGGER __start__

_triggers(
    versions={"messages": 1, "agent_plan": 1},
    seen=None,  # Agent still hasn't run
    proc.triggers=["agent_plan"]
)
→ agent_plan version is 1 (has data)
→ channels[agent_plan].is_available() → True
→ TRIGGER agent

# Result:
next = ("agent",)  # Only agent will run
```

---

## The Complete Entity Relationship

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUESTS STATE                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  CheckpointTuple = checkpointer.get_tuple(config)           │
│  ├─ checkpoint: Checkpoint                                  │
│  ├─ metadata: CheckpointMetadata                            │
│  └─ pending_writes: list[PendingWrite]                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  tasks = prepare_next_tasks(                                │
│      checkpoint=checkpoint,                                  │
│      processes=graph.nodes,  ← Map[str, PregelNode]         │
│      ...                                                     │
│  )                                                           │
│                                                              │
│  COMPUTES WHICH NODES TO RUN BASED ON:                      │
│  1. checkpoint["channel_versions"] (current state)          │
│  2. checkpoint["versions_seen"] (what nodes have seen)      │
│  3. PregelNode.triggers (what channels each node watches)   │
│  4. _triggers() decision function                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  IF for_execution=False:                                    │
│      returns dict[str, PregelTask]                          │
│  ELSE:                                                       │
│      returns dict[str, PregelExecutableTask]                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  StateSnapshot(                                             │
│      values=checkpoint["channel_values"],                   │
│      next=tuple(task.name for task in tasks.values()),      │
│      tasks=tuple(tasks.values()),                           │
│      ...                                                     │
│  )                                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    RETURN TO USER                            │
│  User sees:                                                  │
│  - snapshot.values (current state)                          │
│  - snapshot.next (computed nodes to run)                    │
│  - snapshot.tasks (task details)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## The Crystallized Truth

### Where Does "Next" Come From?

**Answer**: `next` is **computed dynamically** by `prepare_next_tasks()` using this algorithm:

```
FOR each node in the graph:
    FOR each trigger channel of that node:
        current_version = checkpoint["channel_versions"][channel]
        last_seen = checkpoint["versions_seen"][node_name][channel]

        IF current_version > last_seen:
            → Add node to "next"
            BREAK  # Don't need to check other triggers
```

**The key entities involved:**

1. **Checkpoint** - Stores `versions_seen` (what each node has processed)
2. **PregelNode** - Defines `triggers` (what channels each node watches)
3. **prepare_next_tasks()** - Compares versions to compute which nodes should run
4. **StateSnapshot** - Presents computed `next` to user

### The Violence

**Most systems store "next" explicitly:**
- Workflow engines store "current step" in state
- State machines store "current state"
- DAG runners store "pending nodes" in queue

**LangGraph computes "next" from coordination metadata:**
- No explicit "current step" variable
- No "pending queue" to manage
- Just: "Compare what nodes have seen vs what channels have"

**This is why LangGraph can:**
- Time-travel to any checkpoint and resume correctly
- Handle dynamic parallelization (Sends)
- Support human-in-the-loop interrupts
- Guarantee exactly-once execution per super-step

**The checkpoint doesn't say "run these nodes next."**

**The checkpoint says "here's what each node has seen" and the system figures out the rest.**

---

## Complete Entity Inventory

| Entity | Purpose | Where It Lives | Contains "next"? |
|--------|---------|---------------|------------------|
| **Checkpoint** | State + coordination | Database | ❌ (has `versions_seen` input) |
| **StateSnapshot** | User view | Computed on-demand | ✅ (computed field) |
| **PregelNode** | Node definition | In-memory graph | ❌ (has `triggers`) |
| **PregelTask** | Lightweight task | Returned in snapshot | ❌ |
| **PregelExecutableTask** | Full task for execution | In-memory during run | ❌ |
| **CheckpointTuple** | Checkpoint + context | Returned by checkpointer | ❌ |
| **CheckpointMetadata** | Checkpoint provenance | Stored with checkpoint | ❌ |
| **PendingWrite** | Uncommitted update | CheckpointTuple | ❌ |
| **Send** | Dynamic dispatch | Checkpoint pending_sends | ❌ |
| **Interrupt** | Human-in-loop signal | Checkpoint + StateSnapshot | ❌ |
| **`prepare_next_tasks()`** | **Computes next** | **Function** | ✅ (computes it) |
| **`_triggers()`** | **Decides if node runs** | **Function** | ✅ (helper) |

**The key insight:**

`next` is not an entity. It's a **derived property** computed by comparing:
- `checkpoint["versions_seen"]` (what nodes have processed)
- `checkpoint["channel_versions"]` (current state of channels)
- `PregelNode.triggers` (what each node watches)

**Resumption isn't "load next from storage."**

**Resumption is "recompute next from coordination metadata."**

This is the Pregel algorithm in action.
