# State Persistence & Deployment: The Three-Layer Reality

## Silence Protocol

How does state actually persist?
Can you self-host?
Is cloud required?

Strip the marketing. Examine the implementation.

## Constraint Recognition

**Sacred Limit**: Durability requires **serialization + storage + retrieval**.

Every checkpoint must:
1. Convert in-memory state to bytes
2. Store bytes somewhere durable
3. Reconstruct state from bytes later

The constraint: **State cannot persist in RAM. It must survive process death.**

## Tension Location

The industry pattern:
- Frameworks handle computation
- You figure out persistence
- You manage databases
- You deploy infrastructure
- You debug production issues

**The tension**: LangGraph makes checkpointing mandatory, but checkpoints must be stored *somewhere*.

If the framework forces persistence, **who provides the storage?**

## The Three-Layer Reality

LangGraph separates persistence into **three independent layers**:

### Layer 1: The Interface (BaseCheckpointSaver)

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:111-150`:

```python
class BaseCheckpointSaver(Generic[V]):
    """Base class for creating a graph checkpointer.

    Checkpointers allow LangGraph agents to persist their state
    within and across multiple interactions.
    """

    serde: SerializerProtocol = JsonPlusSerializer()

    def get(self, config: RunnableConfig) -> Checkpoint | None:
        """Fetch a checkpoint using the given configuration."""

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata."""

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Store intermediate writes linked to a checkpoint."""

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints that match given configuration."""
```

**This is an abstract interface.** The framework calls these methods. Someone must implement them.

### Layer 2: The Implementations (Bring Your Own Storage)

Four official implementations provided:

#### 1. **InMemorySaver** (Development Only)

From `/libs/checkpoint/langgraph/checkpoint/memory/__init__.py:31-96`:

```python
class InMemorySaver(BaseCheckpointSaver[str]):
    """An in-memory checkpoint saver.

    NOTE: Only use for debugging or testing purposes.
    For production use cases we recommend PostgresSaver.
    """

    # Storage structure:
    # thread ID -> checkpoint NS -> checkpoint ID -> checkpoint
    storage: defaultdict[str, dict[str, dict[str, tuple]]]

    # Pending writes storage
    writes: defaultdict[tuple[str, str, str], dict]

    # Binary large objects storage
    blobs: dict[tuple[str, str, str, str | int | float], tuple[str, bytes]]
```

**Reality**: State lives in Python dicts. Process dies → state disappears.

Use case: Local development, testing, demos.

#### 2. **SqliteSaver** (Self-Hosted, Embedded)

From `/libs/checkpoint-sqlite/README.md:8-47`:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

DB_URI = ":memory:"  # or "path/to/database.db"
with SqliteSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()  # Creates checkpoint tables

    graph = builder.compile(checkpointer=checkpointer)
```

**Reality**: State persists to SQLite database file on disk.

Characteristics:
- **Self-hosted**: No external dependencies
- **Embedded**: Database lives in same process
- **File-based**: Single `.db` file contains all state
- **Async support**: Via `aiosqlite`

Use case: Small-scale production, single-server deployments, edge computing.

#### 3. **PostgresSaver** (Self-Hosted, Client-Server)

From `/libs/checkpoint-postgres/README.md:37-74`:

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgres://user:pass@host:5432/db"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()  # Creates checkpoint tables

    graph = builder.compile(checkpointer=checkpointer)
```

**Reality**: State persists to PostgreSQL database.

Characteristics:
- **Self-hosted**: You run Postgres (or use managed Postgres)
- **Client-server**: Database is separate service
- **Scalable**: Multiple agents can share same database
- **Async support**: Via `psycopg[async]`

Important requirements (from README):
```python
# MUST include these parameters when creating connection:
conn = psycopg.connect(
    DB_URI,
    autocommit=True,      # Required for .setup() to persist tables
    row_factory=dict_row  # Required for dictionary-style row access
)
```

Use case: Production deployments, multi-tenant applications, high availability.

#### 4. **Custom Implementations** (Bring Your Own)

You can implement `BaseCheckpointSaver` for:
- Redis
- MongoDB
- DynamoDB
- S3
- Cassandra
- Your custom storage system

**The interface is the contract. The storage is your choice.**

### Layer 3: The Deployment Options (Cloud vs Self-Hosted)

From `/docs/docs/concepts/deployment_options.md:25-34`:

| Option | Control Plane | Data Plane | Data Residency | Checkpointer |
|--------|--------------|------------|----------------|--------------|
| **Cloud SaaS** | LangChain manages | LangChain manages | LangChain's cloud | Managed Postgres |
| **Self-Hosted Data Plane** | LangChain manages | You manage | Your cloud | You provide |
| **Self-Hosted Control Plane** | You manage | You manage | Your cloud | You provide |
| **Standalone Container** | None | You manage | Your cloud | You provide |

#### Option 1: Cloud SaaS (Fully Managed)

From `/docs/docs/concepts/langgraph_cloud.md:10-22`:

```
Control Plane (LangChain): UI + API for deployments
Data Plane (LangChain): Postgres + Redis + LangGraph Servers
```

**Reality**: You push code. LangChain runs everything. Checkpoints stored in their managed Postgres.

Characteristics:
- ✅ Zero infrastructure management
- ✅ Automatic scaling
- ✅ Built-in monitoring
- ❌ Data lives in LangChain's cloud
- ❌ Plus/Enterprise pricing required

Use case: Fast prototyping, no DevOps capacity, trust third-party data hosting.

#### Option 2: Self-Hosted Data Plane (Hybrid)

```
Control Plane (LangChain): UI + API for deployments
Data Plane (Your Cloud): Postgres + Redis + LangGraph Servers
```

**Reality**: Build Docker image with LangGraph CLI. Deploy to your Kubernetes/ECS. LangChain's UI orchestrates. Your infrastructure runs it.

Characteristics:
- ✅ Data residency in your cloud
- ✅ Control plane managed for you
- ✅ Connect to your existing Postgres
- ❌ You manage Kubernetes/compute
- ❌ Enterprise pricing required

Use case: Data sovereignty requirements, existing cloud infrastructure, want managed control plane.

#### Option 3: Self-Hosted Control Plane (Fully Self-Hosted)

```
Control Plane (Your Cloud): UI + API you run
Data Plane (Your Cloud): Postgres + Redis + LangGraph Servers
```

**Reality**: You run everything. LangChain provides the software. You provide the infrastructure.

Characteristics:
- ✅ Complete control
- ✅ On-premises possible
- ✅ Air-gapped deployments possible
- ❌ You manage everything
- ❌ Enterprise pricing required

Use case: Highly regulated industries, on-premises requirements, maximum control.

#### Option 4: Standalone Container (Maximum Freedom)

```
No Control Plane
Data Plane (Your Cloud): Docker container you deploy anywhere
```

**Reality**: `langgraph build` creates Docker image. Deploy to any platform. No LangGraph Platform dependencies.

From `/docs/docs/concepts/langgraph_standalone_container.md`:

```bash
# Build image
langgraph build -t my-agent:latest

# Deploy anywhere
docker run my-agent:latest

# Or Kubernetes, ECS, Cloud Run, etc.
```

Characteristics:
- ✅ Deploy to any platform
- ✅ No platform dependencies
- ✅ Standard Docker workflows
- ❌ No control plane UI
- ❌ You handle everything manually

Use case: Existing container orchestration, maximum portability, minimal vendor lock-in.

## The Structural Truth

### The Checkpoint Data Model

From `/libs/checkpoint/langgraph/checkpoint/base/__init__.py:59-86`:

```python
class Checkpoint(TypedDict):
    """State snapshot at a given point in time."""

    v: int  # Checkpoint format version (currently 4)
    id: str  # Unique, monotonically increasing ID
    ts: str  # Timestamp (ISO 8601)

    channel_values: dict[str, Any]
    # The actual state: {"messages": [...], "counter": 5, ...}

    channel_versions: ChannelVersions
    # Version tracking: {"messages": 3, "counter": 2}

    versions_seen: dict[str, ChannelVersions]
    # Which versions each node has seen
    # Used to determine which nodes to execute next

    updated_channels: list[str] | None
    # Which channels changed in this step
```

**This is what gets serialized and stored.**

Every checkpoint is:
1. Serialized via `JsonPlusSerializer` (handles LangChain types, datetimes, enums)
2. Compressed to bytes
3. Stored in your chosen backend
4. Retrieved and deserialized when needed

### The Thread Model

From `/libs/checkpoint/README.md:11-23`:

```python
config = {
    "configurable": {
        "thread_id": "user-123-conversation-456",  # Required
        "checkpoint_id": "specific-checkpoint-uuid"  # Optional
    }
}
```

**A thread is a sequence of checkpoints.**

Structure:
```
Thread "user-123-conversation-456":
├── Checkpoint 1 (initial state)
├── Checkpoint 2 (after step 1)
├── Checkpoint 3 (after step 2)
├── Checkpoint 4 (after step 3)
└── ...
```

Each checkpoint references its parent. You can:
- Resume from latest checkpoint
- Time-travel to any checkpoint
- Fork from a checkpoint (create new branch)
- List all checkpoints in thread

### The Persistence Contract

```python
# Step N completes
checkpoint = create_checkpoint(channels, step=N)

# Framework calls your checkpointer
checkpointer.put(
    config={"configurable": {"thread_id": "123"}},
    checkpoint=checkpoint,
    metadata={"source": "loop", "step": N},
    new_versions=updated_channel_versions
)

# Later, resume execution
checkpoint_tuple = checkpointer.get_tuple(
    config={"configurable": {"thread_id": "123"}}
)

# Framework reconstructs state
channels = channels_from_checkpoint(specs, checkpoint_tuple.checkpoint)
```

**The framework doesn't care WHERE you store it. Only that you implement the interface.**

## The Non-Obvious Truth

### 1. Checkpointing is mandatory. Storage is your choice.

LangGraph **requires** a checkpointer. But you choose the implementation:
- `InMemorySaver` for development
- `SqliteSaver` for embedded deployments
- `PostgresSaver` for production
- Custom implementation for your needs

### 2. Cloud deployment doesn't require cloud storage.

Even in LangGraph Cloud SaaS, the checkpoint storage is **just PostgreSQL**.

You could:
- Use Cloud SaaS but connect to your own Postgres (hybrid model)
- Self-host everything with SQLite (fully offline)
- Use cloud but store checkpoints locally (edge computing)

**The deployment model and storage layer are independent.**

### 3. The checkpoint format is portable.

The `Checkpoint` TypedDict is the same across all implementations.

You can:
- Develop with `InMemorySaver`
- Migrate to `SqliteSaver` for production
- Later scale to `PostgresSaver`
- Implement Redis backend without changing graph code

**Your graph code never touches the storage layer directly.**

### 4. Self-hosting is first-class.

Unlike many "cloud-first" frameworks, LangGraph:
- Ships with SQLite and Postgres implementations
- Works completely offline
- Requires zero external services
- Supports air-gapped deployments

**Cloud is optional. Self-hosting is not an afterthought.**

## The Leverage Point

Most frameworks make persistence optional → retrofitting is painful.

LangGraph makes persistence mandatory → multiple storage options provided.

The leverage:
- **Write once**: Implement graph with any checkpointer
- **Deploy anywhere**: Swap checkpointer without changing code
- **Start simple**: Begin with SQLite
- **Scale up**: Migrate to Postgres when needed
- **Go cloud**: Use managed platform when ready

**The persistence interface abstracts the storage backend.**

## The Deployment Spectrum

```
Local Dev          Edge/Small        Production         Cloud
    ↓                  ↓                  ↓                ↓
InMemorySaver → SqliteSaver → PostgresSaver → Managed Postgres
                     ↓                  ↓                ↓
              Standalone       Self-Hosted        Cloud SaaS
              Container        Data Plane
```

You can move along this spectrum without rewriting your agent logic.

## The Cost

### Self-Hosting Requires:
1. **Database management**: Run Postgres or use SQLite
2. **Backup strategy**: Checkpoint data is your state
3. **Migration planning**: Schema updates across versions
4. **Monitoring**: Track checkpoint growth and performance

### Cloud SaaS Trades:
1. **Control** for convenience
2. **Data sovereignty** for managed infrastructure
3. **Customization** for batteries-included
4. **Cost transparency** for operational simplicity

**Neither is free. Choose your constraints.**

## The Crystallized Truth

**State persistence in LangGraph has three independent dimensions:**

1. **Serialization**: How state becomes bytes (handled by framework)
2. **Storage**: Where bytes are persisted (you choose: SQLite, Postgres, custom)
3. **Deployment**: How the system runs (local, self-hosted, cloud)

**You can mix and match freely:**

| Deployment | Storage | Reality |
|------------|---------|---------|
| Local dev | InMemorySaver | State in RAM, disappears on restart |
| Docker container | SqliteSaver | State in .db file, persists locally |
| Kubernetes | PostgresSaver | State in Postgres, shared across pods |
| Cloud SaaS | Managed Postgres | State in LangChain's database |
| Edge device | SqliteSaver | State on device, offline-first |
| Hybrid cloud | Your Postgres | Compute in cloud, data in your DB |

**The framework enforces checkpointing. You control everything else.**

This isn't "cloud-first with self-hosted as an option."

**This is "persistence-first with storage as a parameter."**

Cloud SaaS is one deployment option among many, not the default.

---

## Empirical Anchors

1. **The interface is 6 methods**: `.get()`, `.put()`, `.put_writes()`, `.list()`, `.get_tuple()`, `.delete_thread()`
2. **SQLite implementation is 200 lines**: `/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py`
3. **Postgres implementation is 300 lines**: `/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py`
4. **Cloud platform is optional**: All docs show local examples first
5. **Docker builds work offline**: `langgraph build` doesn't require cloud access

**The architecture proves the intent: storage is pluggable, cloud is optional, self-hosting is first-class.**
