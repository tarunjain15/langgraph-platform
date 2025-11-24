# Channels: The Complete Mental Model

## The Sacred Constraint

**A channel must answer one question: "Has there been a state change that actors need to coordinate around?"**

Not "what is the value?" (that's a variable).

Not "what is the history?" (that's a log).

**"Has the world changed since you last looked, and who needs to know?"**

This is the irreducible function of a channel.

---

## Part 1: What Channels Are NOT

### Channels Are Not Variables

```python
# Variable
state = {"counter": 0}
state["counter"] += 1

# Problem: No coordination
# If actor crashes and restarts, it sees counter=1
# Was its write included? NO WAY TO KNOW.
```

**Variables have no coordination metadata.**

### Channels Are Not Database Tables

```python
# Database table
INSERT INTO events (id, data) VALUES (1, 'event1');
SELECT * FROM events WHERE id = 1;

# Problem: Not a coordination primitive
# Actors must poll or use external pub/sub
# No built-in versioning for coordination
```

**Databases store data. Channels coordinate actors.**

### Channels Are Not Message Queues

```python
# Message queue
queue.push(message)
message = queue.pop()  # Destructive read

# Problem: Once consumed, gone
# Other actors can't see same message
# No shared state, no coordination
```

**Message queues are for task distribution. Channels are for state coordination.**

---

## Part 2: What Channels ARE

**A channel is a versioned shared memory cell with:**

1. **Update semantics** - How multiple writes combine
2. **Version tracking** - Increments on each meaningful update
3. **Checkpoint serialization** - How to save/restore state
4. **Coordination primitive** - Enables `versions_seen` comparison

**The minimal interface:**

```python
class BaseChannel:
    def update(self, values: Sequence[Any]) -> bool:
        """Apply updates. Return True if state changed."""
        pass

    def get(self) -> Any:
        """Read current value."""
        pass

    def checkpoint(self) -> Any:
        """Serialize for persistence."""
        pass

    @classmethod
    def from_checkpoint(cls, checkpoint: Any) -> Self:
        """Deserialize from checkpoint."""
        pass

    def is_available(self) -> bool:
        """Check if channel has data."""
        pass
```

**Everything else is implementation detail.**

---

## Part 3: The Three Built-In Channel Types

### 1. LastValue - "Only Current State Matters"

**Mental model**: A slot that holds one value. History is irrelevant.

**Update semantics**: Overwrite

**Use when**: Only the latest value matters, previous values are discarded

**Implementation:**
```python
class LastValue:
    def __init__(self):
        self.value = None
        self.version = 0

    def update(self, new_values):
        if not new_values:
            return False
        self.value = new_values[-1]  # Take last value
        self.version += 1
        return True

    def get(self):
        return self.value

    def checkpoint(self):
        return self.value  # Just the value
```

**Example: User Session**

```python
session = LastValue[dict]()

# Login user_123
session.update([{"user_id": "user_123", "auth": True}])
# value: {"user_id": "user_123", "auth": True}
# version: 1

# Later: Login user_456
session.update([{"user_id": "user_456", "auth": True}])
# value: {"user_id": "user_456", "auth": True}
# version: 2
# Previous session is GONE

# Actors watching session wake because version changed (1 → 2)
```

**Use cases:**
- Current user session
- Current agent plan
- Active configuration
- Selected tool
- Current state in state machine

**Rule**: If you say "I only need the latest X", use LastValue.

---

### 2. Topic - "Accumulate Events, Never Duplicate"

**Mental model**: An append-only log with automatic deduplication.

**Update semantics**: Append + deduplicate

**Use when**: Need to collect all events without duplicates

**Implementation:**
```python
class Topic:
    def __init__(self):
        self.accumulator = []
        self.seen = set()
        self.version = 0

    def update(self, new_values):
        added_any = False
        for value in new_values:
            value_hash = hash(value)
            if value_hash not in self.seen:
                self.accumulator.append(value)
                self.seen.add(value_hash)
                added_any = True

        if added_any:
            self.version += 1  # Only if actually added
        return added_any

    def get(self):
        return self.accumulator

    def checkpoint(self):
        return (self.accumulator, self.seen)  # Both needed
```

**Example: Message History**

```python
messages = Topic[BaseMessage]()

# User message
messages.update([HumanMessage("Hello")])
# accumulator: [HumanMessage("Hello")]
# version: 1

# Agent response
messages.update([AIMessage("Hi there!")])
# accumulator: [HumanMessage("Hello"), AIMessage("Hi there!")]
# version: 2

# Tool result
messages.update([ToolMessage("Weather: Sunny")])
# accumulator: [HumanMessage(...), AIMessage(...), ToolMessage(...)]
# version: 3

# Attempt to add duplicate (bug)
messages.update([HumanMessage("Hello")])
# accumulator: UNCHANGED (duplicate detected)
# version: UNCHANGED (3)
# No actors wake because version didn't change
```

**Use cases:**
- Message histories
- Event logs
- Task queues
- Audit trails
- Notification lists

**Rule**: If you say "I need to collect all X without duplicates", use Topic.

---

### 3. BinaryOperatorAggregate - "Reduce All Updates"

**Mental model**: A value that accumulates via a binary operation.

**Update semantics**: Reduce via operator (like `+`, `*`, `max`, `|`)

**Use when**: Need to combine all updates into a single aggregated value

**Implementation:**
```python
class BinaryOperatorAggregate:
    def __init__(self, operator):
        self.operator = operator  # e.g., operator.add
        self.value = None
        self.version = 0

    def update(self, new_values):
        if not new_values:
            return False

        for val in new_values:
            if self.value is None:
                self.value = val
            else:
                self.value = self.operator(self.value, val)

        self.version += 1
        return True

    def get(self):
        return self.value

    def checkpoint(self):
        return self.value
```

**Example: Token Counter**

```python
import operator
token_count = BinaryOperatorAggregate[int](operator.add)

# Agent call 1
token_count.update([1500])
# value: 1500
# version: 1

# Agent call 2
token_count.update([2000])
# value: 3500  # 1500 + 2000
# version: 2

# Tool call
token_count.update([500])
# value: 4000  # 3500 + 500
# version: 3

# Final: Total of all token usage across all calls
```

**Example: Error Flags (Set Union)**

```python
error_flags = BinaryOperatorAggregate[set](operator.or_)

# Validator 1
error_flags.update([{"invalid_email", "missing_field"}])
# value: {"invalid_email", "missing_field"}

# Validator 2
error_flags.update([{"unauthorized"}])
# value: {"invalid_email", "missing_field", "unauthorized"}

# Validator 3
error_flags.update([{"invalid_email", "rule_violation"}])
# value: {"invalid_email", "missing_field", "unauthorized", "rule_violation"}
# Duplicate "invalid_email" handled by set union
```

**Use cases:**
- Token/cost counters (sum)
- Max latency tracking (max)
- Error flags (set union)
- Permission intersection (set intersection)
- Aggregated metrics

**Rule**: If you say "I need to combine all X using operation Y", use BinaryOperatorAggregate.

---

## Part 4: Channel Design Patterns

### Pattern 1: Single Source of Truth

**Use LastValue when only current state matters:**

```python
current_user = LastValue[str]()
session_config = LastValue[dict]()
agent_plan = LastValue[list[str]]()
active_tool = LastValue[str]()
current_mode = LastValue[Literal["auto", "manual"]]()
```

**Characteristic**: Previous values are irrelevant to system behavior.

---

### Pattern 2: Event Accumulation

**Use Topic when you need complete history without duplicates:**

```python
messages = Topic[BaseMessage]()
audit_log = Topic[AuditEvent]()
task_queue = Topic[Task]()
notifications = Topic[Notification]()
document_chunks = Topic[str]()
```

**Characteristic**: Order matters, duplicates don't add value.

---

### Pattern 3: Metric Aggregation

**Use BinaryOperatorAggregate when you need to combine all updates:**

```python
# Arithmetic
total_cost = BinaryOperatorAggregate[float](operator.add)
max_latency = BinaryOperatorAggregate[float](max)
min_score = BinaryOperatorAggregate[float](min)

# Set operations
all_errors = BinaryOperatorAggregate[set](operator.or_)  # Union
required_perms = BinaryOperatorAggregate[set](operator.and_)  # Intersection

# String operations
log_output = BinaryOperatorAggregate[str](operator.add)
```

**Characteristic**: Individual updates are less important than the aggregate.

---

## Part 5: Channels Are Coordination Boundaries

### The Key Question

**For any state you're considering making a channel:**

> "Do multiple actors need to coordinate around changes to this state?"

- **YES** → Channel
- **NO** → Local variable or shared resource

---

### Example 1: Coordination Required (Channel)

```python
messages = Topic[Message]()

def agent(state):
    msgs = messages.get()
    response = llm.invoke(msgs)
    messages.update([response])
    # Agent writes → tools needs to wake

def tools(state):
    msgs = messages.get()
    tool_calls = extract_tool_calls(msgs[-1])
    results = execute_tools(tool_calls)
    messages.update([ToolMessage(results)])
    # Tools writes → agent needs to wake
```

**Why channel?** Multiple actors coordinate around message changes.

---

### Example 2: No Coordination (Not a Channel)

```python
def agent_node(state):
    messages = state["messages"]

    # Local computations
    token_count = count_tokens(messages)  # ← Not a channel
    context_window = 4096 - token_count   # ← Not a channel
    truncated = truncate(messages, context_window)  # ← Not a channel

    response = llm.invoke(truncated)
    return {"messages": [response]}  # ← This goes to channel
```

**Why not channels?** No other actor needs to coordinate around these intermediate values.

---

### Example 3: Shared Resource (Not a Channel)

```python
# Global cache (not a channel)
embedding_cache = {}

def embed_documents(state):
    embeddings = []
    for doc in state["documents"]:
        if doc.id in embedding_cache:
            embeddings.append(embedding_cache[doc.id])
        else:
            emb = embed_model.embed(doc.text)
            embedding_cache[doc.id] = emb
            embeddings.append(emb)

    return {"embeddings": embeddings}  # ← This goes to channel
```

**Why not channel?** Cache is opportunistic read, not coordination point.

---

## Part 6: Channels Define Causality

### The Deeper Truth

**A channel doesn't represent "a resource in the domain."**

**A channel represents a causal dependency:**

```
"When X changes → Y must react"
```

The channel IS the causality, not the data.

---

### Example: Document Processing

**The causal chain:**

```
New documents arrive → Extractor must wake
↓ (raw_documents channel)

Extraction completes → Embedder must wake
↓ (extracted_text channel)

Embeddings complete → Indexer must wake
↓ (embeddings channel)

Index updates → Query engine must wake
↓ (search_index channel)
```

**Each arrow is a channel.**

**Channels make causality explicit in the type system.**

---

## Part 7: The Litmus Test

### For any state, ask these three questions:

#### Question 1: "Does this trigger downstream work?"

- **YES** → Might be a channel
- **NO** → Definitely not a channel

#### Question 2: "Do multiple actors need to know when this changes?"

- **YES** → Definitely a channel
- **NO** → Just a variable

#### Question 3: "Is this an intermediate computation?"

- **YES** → Not a channel
- **NO** → Might be a channel

---

### Applied Examples

#### Approval Request

```
Q1: Does this trigger downstream work?
    → YES (when approved, next stage executes)

Q2: Do multiple actors coordinate around this?
    → YES (approver writes, executor waits and reads)

Q3: Is this intermediate computation?
    → NO (it's a coordination point)

VERDICT: Channel ✓
```

#### LLM Temperature Parameter

```
Q1: Does this trigger downstream work?
    → NO (just a parameter to LLM calls)

Q2: Do multiple actors coordinate around this?
    → NO (it's just read, doesn't trigger anything)

Q3: Is this intermediate computation?
    → NO, but it's configuration

VERDICT: NOT a channel (pass in config instead)
```

---

## Part 8: Custom Channels

### When Built-Ins Aren't Enough

**The three built-in types cover ~80% of cases.**

**For the other 20%, implement BaseChannel interface:**

```python
class CustomChannel(BaseChannel):
    def update(self, values) -> bool:
        """Define how updates combine."""
        pass

    def get(self):
        """Define what actors read."""
        pass

    def checkpoint(self):
        """Define how to persist."""
        pass

    @classmethod
    def from_checkpoint(cls, checkpoint):
        """Define how to restore."""
        pass
```

---

### Example: RingBuffer (Keep Last N Values)

```python
from collections import deque

class RingBuffer(BaseChannel):
    """Keep only the last N values."""

    def __init__(self, max_size: int = 100):
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size

    def update(self, values) -> bool:
        if not values:
            return False
        self.buffer.extend(values)
        return True

    def get(self) -> list:
        return list(self.buffer)

    def checkpoint(self) -> dict:
        return {
            "buffer": list(self.buffer),
            "max_size": self.max_size
        }

    @classmethod
    def from_checkpoint(cls, checkpoint):
        channel = cls(max_size=checkpoint["max_size"])
        channel.buffer = deque(checkpoint["buffer"], maxlen=checkpoint["max_size"])
        return channel
```

**Usage:**

```python
class State(TypedDict):
    recent_errors: Annotated[list[str], RingBuffer(max_size=10)]

def error_prone_node(state):
    try:
        result = risky_operation()
    except Exception as e:
        return {"recent_errors": [str(e)]}
```

**Why custom?**
- Topic would keep ALL errors (memory leak)
- LastValue would keep ONE error (lose context)
- RingBuffer keeps recent context with bounded memory

---

### Example: PriorityQueue

```python
import heapq

class PriorityTask(NamedTuple):
    priority: int
    task: Any

    def __lt__(self, other):
        return self.priority < other.priority

class PriorityQueue(BaseChannel):
    """Tasks ordered by priority."""

    def __init__(self):
        self.heap = []
        self.seen = set()

    def update(self, values) -> bool:
        added_any = False
        for task in values:
            task_hash = hash(str(task.task))
            if task_hash not in self.seen:
                heapq.heappush(self.heap, task)
                self.seen.add(task_hash)
                added_any = True
        return added_any

    def get(self) -> list:
        """Returns tasks sorted by priority."""
        return [t.task for t in sorted(self.heap)]

    def checkpoint(self) -> dict:
        return {
            "heap": [(t.priority, t.task) for t in self.heap],
            "seen": list(self.seen)
        }

    @classmethod
    def from_checkpoint(cls, checkpoint):
        channel = cls()
        channel.heap = [PriorityTask(p, t) for p, t in checkpoint["heap"]]
        heapq.heapify(channel.heap)
        channel.seen = set(checkpoint["seen"])
        return channel
```

**Why custom?** Need ordered processing, not FIFO.

---

### When to Create Custom Channels

| Need | Custom Channel |
|------|----------------|
| Different retention policy | RingBuffer, SlidingWindow |
| Different ordering | PriorityQueue, Stack, SortedList |
| Different aggregation | MinMax, Average, Histogram |
| Different semantics | Set, Graph, StateMachine |
| Domain-specific logic | ConflictResolution, Consensus |

**If your coordination needs different semantics → custom channel.**

---

## Part 9: Anti-Patterns

### Anti-Pattern 1: Using LastValue for Growing Lists

```python
# WRONG
task_results = LastValue[list]()

# Node A
task_results.update([[result1]])
# Node B (parallel)
task_results.update([[result2]])  # ← result1 LOST!
```

**Fix**: Use Topic

```python
# CORRECT
task_results = Topic[Result]()
# Both results preserved
```

---

### Anti-Pattern 2: Using Topic for Current State

```python
# WRONG
current_user = Topic[str]()

current_user.update(["user_123"])
current_user.update(["user_456"])
# accumulator: ["user_123", "user_456"]  ← Both in list!
```

**Fix**: Use LastValue

```python
# CORRECT
current_user = LastValue[str]()
# Only latest user
```

---

### Anti-Pattern 3: Manual Aggregation with Race Conditions

```python
# WRONG
totals = LastValue[dict]()

def node_a(state):
    current = totals.get() or {}
    current["count"] = current.get("count", 0) + 1
    totals.update(current)
    # Race condition if node_b runs in parallel!
```

**Fix**: Use BinaryOperatorAggregate

```python
# CORRECT
count = BinaryOperatorAggregate[int](operator.add)
count.update([1])  # Thread-safe
```

---

## Part 10: Channel Coordination Mechanics

### How Channels Enable Coordination

```python
# Initial state
checkpoint = {
    "channel_versions": {"messages": 3},
    "versions_seen": {"agent": {"messages": 2}}
}

# Question: Should agent run?
current_version = 3
last_seen_version = 2
→ 3 > 2 → WAKE AGENT

# Agent runs, reads messages
# After execution:
checkpoint = {
    "channel_versions": {"messages": 3},  # Unchanged (agent didn't write)
    "versions_seen": {"agent": {"messages": 3}}  # Updated
}

# Question: Should agent run again?
current_version = 3
last_seen_version = 3
→ 3 == 3 → SLEEP (no new data)
```

**The channel version + versions_seen = coordination primitive.**

**This prevents:**
- Infinite loops (agent re-running on own output)
- Duplicate work (re-executing completed tasks)
- Race conditions (exactly-once execution)

---

## Part 11: The Complete Picture

### What a Channel Really Is

```
┌─────────────────────────────────────────┐
│           CHANNEL                       │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  VALUE                           │  │
│  │  "The actual state"              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  VERSION                         │  │
│  │  "Coordination signal"           │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  UPDATE SEMANTICS                │  │
│  │  "How writes combine"            │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  CHECKPOINT METHOD               │  │
│  │  "How to persist/restore"        │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**All four components are essential.**

**Remove any one → coordination breaks.**

---

## Part 12: The Crystallized Truth

### Channels Are NOT

- ❌ Variables (no coordination metadata)
- ❌ Databases (not a coordination primitive)
- ❌ Message queues (destructive read, no shared state)
- ❌ Storage for resources (they're coordination boundaries)

### Channels ARE

- ✅ Versioned shared memory cells
- ✅ Coordination primitives for actors
- ✅ Causal dependencies made explicit
- ✅ Update semantics that define how distributed state combines

### The Three Sacred Types

| Type | Semantics | Use When |
|------|-----------|----------|
| **LastValue** | Overwrite | Only current state matters |
| **Topic** | Append + dedup | Need complete history without duplicates |
| **BinaryOperatorAggregate** | Reduce | Need to combine all updates via operation |

### The Design Question

**For any state:**

> "Do multiple actors need to coordinate around changes to this?"

- **YES** → Channel
- **NO** → Variable or shared resource

### The Truth About Coordination

**Channels don't store resources.**

**Channels define causal edges in the actor graph.**

```
Agent writes to messages → Tools reads messages → Tools wakes
```

**The channel IS the arrow (→).**

**The data is what flows through the arrow.**

### Custom Channels

**Built-in types cover 80% of cases.**

**For the other 20%, implement BaseChannel interface.**

**Define custom update semantics for your coordination needs.**

### The Leverage Point

**Change one thing**: Stop thinking "channel = place to store data"

**Start thinking**: "channel = coordination primitive that signals state changes"

**The version is the signal.**

**The update semantics define how signals accumulate.**

**The coordination happens via versions_seen comparison.**

**Everything else follows from this.**

---

## The Sacred Limit

**In distributed systems, coordination requires shared state.**

**Channels are LangGraph's answer to distributed coordination.**

**They combine:**
- State (the value)
- Signaling (the version)
- Semantics (the update rules)
- Persistence (the checkpoint)

**Into a single primitive that enables:**
- Exactly-once execution
- Precise crash recovery
- Natural parallelization
- Time-travel debugging

**This is not a library feature.**

**This is a fundamental architectural decision about how to coordinate distributed actors.**

**Understand channels → understand LangGraph.**
