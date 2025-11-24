# The Anatomy of a Checkpoint: The Five Components That Enable Time-Travel

## Constraint Recognition

**Sacred Limit**: A checkpoint must contain **EXACTLY enough information** to resurrect execution at that precise moment.

Not too much (waste storage). Not too little (cannot resume).

The constraint: **State + Coordination metadata = Resumability**

## The Tension

Most systems checkpoint **only state values**.

But execution isn't just "what are the values?" It's also:
- **Which nodes have seen which data?**
- **What was the execution order?**
- **What work is still pending?**
- **Where in the graph are we?**

The tension: **State alone is insufficient. Coordination context is required.**

---

## The Five Components of a Checkpoint

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:59-85`:

```python
class Checkpoint(TypedDict):
    """State snapshot at a given point in time."""

    v: int
    id: str
    ts: str
    channel_values: dict[str, Any]
    channel_versions: ChannelVersions
    versions_seen: dict[str, ChannelVersions]
    updated_channels: list[str] | None
```

### Component 1: Administrative Metadata

```python
v: int          # Version of checkpoint format (currently 4)
id: str         # Unique, monotonically increasing ID (UUID6-based)
ts: str         # Timestamp (ISO 8601)
```

**Purpose**: Checkpoint identity and ordering

**The ID is critical:**
- Uses UUID version 6 (time-ordered UUIDs)
- Generated via `uuid6(clock_seq=step)`
- Monotonically increasing → natural sort order
- First checkpoint: `uuid6(clock_seq=-2)` (empty checkpoint)
- Step N checkpoint: `uuid6(clock_seq=N)`

**Why time-ordered UUIDs?**
```python
# From _checkpoint.py:19
id=str(uuid6(clock_seq=-2))  # Empty checkpoint
id=str(uuid6(clock_seq=step))  # Step checkpoint
```

Time-ordered UUIDs ensure:
- Checkpoints sort correctly by creation time
- Database indexes stay performant
- No need for separate sequence counter

---

### Component 2: Channel Values (The Actual State)

```python
channel_values: dict[str, Any]
```

**Purpose**: The actual application state

**Structure:**
```python
{
    "messages": [
        {"role": "human", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    "user_id": "user-123",
    "session_context": {"authenticated": True},
    "agent_plan": ["retrieve_docs", "generate_answer"],
    "current_step": 2
}
```

**Key characteristics:**
- Maps channel name → serialized value
- Each channel calls `.checkpoint()` to serialize itself
- Missing channels are omitted (only active channels stored)
- Deserialized via `channel.from_checkpoint(value)`

**How channels checkpoint themselves:**

From `/libs/langgraph/langgraph/channels/last_value.py:77-78`:
```python
def checkpoint(self) -> Value:
    return self.value  # Just return the current value
```

From `/libs/langgraph/langgraph/channels/topic.py` (more complex):
```python
def checkpoint(self) -> tuple[Sequence[Value], set[Value]]:
    return (self.accumulator, self.seen)  # Return both accumulator and dedup set
```

**The violence**: Each channel type defines its own serialization format. The checkpoint doesn't care about channel semantics - it just stores what each channel says to store.

---

### Component 3: Channel Versions (Optimistic Concurrency Control)

```python
channel_versions: ChannelVersions  # dict[str, str | int | float]
```

**Purpose**: Track which version of each channel this checkpoint represents

**Structure:**
```python
{
    "__start__": 2,
    "messages": 5,
    "user_id": 1,
    "agent_plan": 3,
    "current_step": 2
}
```

**How versioning works:**

From `/libs/langgraph/langgraph/pregel/_algo.py:146-153`:
```python
def should_interrupt(checkpoint: Checkpoint, ...):
    version_type = type(next(iter(checkpoint["channel_versions"].values()), None))
    null_version = version_type()  # 0 for int, 0.0 for float, "" for str
    seen = checkpoint["versions_seen"].get(INTERRUPT, {})

    # Check if any channel has been updated since last interrupt
    any_updates_since_prev_interrupt = any(
        version > seen.get(chan, null_version)
        for chan, version in checkpoint["channel_versions"].items()
    )
```

**Why versions matter:**

1. **Optimistic concurrency control**: Know if channel changed since you last read it
2. **Conditional execution**: Only trigger nodes if their input channels updated
3. **Interrupt detection**: Check if state changed since last checkpoint
4. **Deduplication**: Avoid re-processing same data

**Version increment strategy:**
```python
# Each channel update increments its version
channel_versions["messages"] = 4  # Before update
# ... update happens ...
channel_versions["messages"] = 5  # After update
```

**The non-obvious truth**: Versions are NOT timestamps. They're monotonic counters per channel. Two channels can have different version types (int vs float vs str).

---

### Component 4: Versions Seen (Execution Coordination)

```python
versions_seen: dict[str, ChannelVersions]
```

**Purpose**: Track which channel versions each node has processed

**Structure:**
```python
{
    "__input__": {},  # Input node hasn't seen anything yet

    "__start__": {
        "__start__": 1  # Start node has seen start channel version 1
    },

    "retrieve_context": {
        "messages": 4,      # This node last saw messages at version 4
        "__start__": 2      # and start channel at version 2
    },

    "generate_answer": {
        "messages": 5,      # This node saw messages at version 5
        "agent_plan": 3     # and agent_plan at version 3
    },

    INTERRUPT: {            # Special key for interrupt tracking
        "messages": 5,      # Last interrupt was at messages version 5
        "current_step": 2
    }
}
```

**This is the coordination primitive that enables the Pregel algorithm.**

**How it determines what to execute next:**

From `/libs/langgraph/langgraph/pregel/_algo.py` logic:

```python
# Pseudo-code for execution planning
def which_nodes_to_execute_next(checkpoint: Checkpoint) -> list[str]:
    nodes_to_run = []

    for node_name, node in graph.nodes.items():
        # Get which versions this node has seen
        seen = checkpoint["versions_seen"].get(node_name, {})

        # Check each channel this node subscribes to
        for channel_name in node.triggers:
            current_version = checkpoint["channel_versions"][channel_name]
            last_seen_version = seen.get(channel_name, null_version)

            # If channel updated since node last ran, trigger node
            if current_version > last_seen_version:
                nodes_to_run.append(node_name)
                break

    return nodes_to_run
```

**Example execution flow:**

```
Initial state:
channel_versions = {"messages": 3}
versions_seen = {
    "agent": {"messages": 2}  # Agent last saw version 2
}

Question: Should "agent" node run?
Answer: YES, because:
- Current version: 3
- Last seen version: 2
- 3 > 2 → Node triggered

After agent runs:
versions_seen["agent"]["messages"] = 3  # Update what agent has seen

Next question: Should "agent" run again?
Answer: NO, because:
- Current version: 3
- Last seen version: 3
- 3 == 3 → No trigger
```

**The violence**: `versions_seen` is **THE** mechanism that prevents infinite loops. Without it, nodes would re-execute forever on the same data.

---

### Component 5: Updated Channels (Change Tracking)

```python
updated_channels: list[str] | None
```

**Purpose**: Record which channels changed in this super-step

**Structure:**
```python
[
    "messages",      # Messages channel was updated
    "current_step"   # Current_step channel was updated
]
```

**When it's set:**

From `/libs/langgraph/langgraph/pregel/_checkpoint.py:54`:
```python
updated_channels=None if updated_channels is None else sorted(updated_channels)
```

**Usage:**
- Debugging: See exactly what changed
- Optimization: Skip reading unchanged channels
- Auditing: Track which nodes modified which state

**The non-obvious truth**: This is **metadata about the step**, not required for execution. It's for observability, not resumability.

---

## Hidden Component 6: Pending Sends (Found in Practice)

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:96`:

```python
pending_sends=checkpoint.get("pending_sends", []).copy()
```

**Not in the TypedDict, but used in practice:**

```python
pending_sends: list[tuple[str, Any]]  # (target_node, data)
```

**Purpose**: Queue of `Send` commands that haven't been processed yet

**Example:**
```python
# Node emits Send commands for map-reduce
pending_sends = [
    ("process_doc", {"doc_id": 1}),
    ("process_doc", {"doc_id": 2}),
    ("process_doc", {"doc_id": 3}),
]
```

**Why this exists**: The `Send` API allows dynamic parallelization. These sends must persist across checkpoints so they survive crashes.

---

## The Execution Protocol: How Components Work Together

### Step N Execution:

```python
# 1. Load checkpoint N-1
checkpoint = checkpointer.get_tuple(config)

# 2. Determine which nodes to run based on versions_seen
tasks = prepare_next_tasks(
    checkpoint,
    nodes,
    checkpoint["channel_versions"],
    checkpoint["versions_seen"]
)

# 3. Execute tasks in parallel
for task in tasks:
    result = task.run()
    writes = task.writes

# 4. Apply writes to channels
for channel, value in writes:
    channels[channel].update([value])
    channel_versions[channel] = increment(channel_versions[channel])

# 5. Update versions_seen for each executed node
for task in tasks:
    versions_seen[task.name] = {
        ch: channel_versions[ch]
        for ch in task.triggers
    }

# 6. Create checkpoint N
new_checkpoint = create_checkpoint(
    checkpoint=checkpoint,
    channels=channels,
    step=N,
    updated_channels=set(writes.keys())
)

# 7. Persist
checkpointer.put(config, new_checkpoint, metadata, channel_versions)
```

---

## The Storage Format

From observation of the implementations:

**PostgreSQL schema:**
```sql
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BLOB,  -- Serialized Checkpoint dict
    metadata BLOB,    -- Serialized CheckpointMetadata
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
```

**The checkpoint BLOB contains:**
```python
{
    "v": 4,
    "id": "0191e123-4567-89ab-cdef-0123456789ab",
    "ts": "2025-01-15T10:30:45.123456+00:00",
    "channel_values": {
        "messages": [...],  # Serialized via JsonPlusSerializer
        "counter": 5
    },
    "channel_versions": {
        "messages": 3,
        "counter": 2
    },
    "versions_seen": {
        "agent": {"messages": 3},
        "tool": {"counter": 2}
    },
    "updated_channels": ["messages"]
}
```

**Serialization path:**
```
Python dict → JsonPlusSerializer → JSON bytes → Compress → BLOB
```

**Deserialization path:**
```
BLOB → Decompress → JSON bytes → JsonPlusSerializer → Python dict
```

---

## The Non-Obvious Truths

### 1. Checkpoints Are Immutable

Once written, checkpoints NEVER change. Time-travel works because past checkpoints remain untouched.

### 2. Channel Values Are Snapshots, Not Diffs

Each checkpoint contains the **full state**, not deltas. This makes resumption simple but increases storage.

**Trade-off:**
- ✅ Simple resumption (just load checkpoint)
- ❌ Storage grows linearly with steps

**Why not diffs?**
- Diffs require replaying history to reconstruct state
- Checkpoint loading would be O(N) instead of O(1)
- Complexity explosion for time-travel

### 3. Versions Seen Is the Coordination Primitive

Without `versions_seen`, the system cannot determine:
- Which nodes to run next
- Whether execution is complete
- If interrupts should trigger

**It's the "smart" part of checkpointing.**

### 4. Channel Versions Enable Optimistic Concurrency

Multiple processes can read the same checkpoint. Only when writing do they check:

```python
if current_checkpoint.channel_versions["messages"] != expected_version:
    raise ConflictError("Channel was modified by another process")
```

This is how LangGraph Server prevents race conditions.

### 5. The Checkpoint Format Is Versioned (v=4)

**Version history:**
- v1: Initial format
- v2: Added `versions_seen`
- v3: Added `updated_channels`
- v4: Current (added `pending_sends` support)

**Migration strategy**: Old checkpoints can be read and auto-upgraded to new format.

---

## The Crystallized Truth

**A checkpoint is NOT just "state at a point in time."**

**It's five layers:**

1. **Identity**: `v`, `id`, `ts` → Who is this checkpoint?
2. **State**: `channel_values` → What are the values?
3. **Versioning**: `channel_versions` → What iteration of each channel?
4. **Coordination**: `versions_seen` → What has each node processed?
5. **Metadata**: `updated_channels` → What changed in this step?

**The leverage point**: `versions_seen` is the key.

Without it, you'd need external orchestration to track "which nodes have run."

With it, **the checkpoint itself knows how to resume execution.**

**The violent truth**:

Most checkpoint systems store state and let you figure out coordination.

LangGraph checkpoints **ARE the coordination mechanism**.

The checkpoint doesn't just say "here's the state."

It says: "Here's the state, here's what each node has seen, here's what needs to run next."

**Resumption isn't "load state and guess."**

**Resumption is: "Load checkpoint, read `versions_seen`, execute precisely what's needed."**

That's why LangGraph can guarantee:
- Exactly-once execution per super-step
- Deterministic replay
- Optimal re-execution after crashes

**The checkpoint is self-describing, self-coordinating state.**

Not a snapshot. A blueprint for continuation.
