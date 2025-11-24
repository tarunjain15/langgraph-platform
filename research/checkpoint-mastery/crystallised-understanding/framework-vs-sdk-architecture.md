# LangGraph: Framework vs SDK Architecture - State Persistence at Scale

## The Critical Distinction

**LangGraph has TWO completely different execution models:**

1. **LangGraph Framework** (Library): Your code directly imports and executes graphs
2. **LangGraph SDK** (Client): Thin HTTP client talking to LangGraph Server

**This is NOT just a deployment difference - it's a fundamental architectural split.**

---

## Architecture 1: LangGraph as a Framework (Direct Execution)

### What It Is

From `/libs/langgraph/langgraph/`:

```python
# You import the framework
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

# You define the graph
graph = StateGraph(State)
graph.add_node("agent", agent_function)
graph = graph.compile(checkpointer=SqliteSaver.from_conn_string("agent.db"))

# You execute directly in your process
result = graph.invoke({"input": "Hello"}, config={"configurable": {"thread_id": "1"}})
```

### Execution Model

```
┌─────────────────────────────────────────────┐
│         Your Python/JS Process              │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Your Application Code                │ │
│  │                                       │ │
│  │  graph = StateGraph(State)            │ │
│  │  graph.compile(checkpointer=...)      │ │
│  │  graph.invoke(...)  ←─ Direct call   │ │
│  │                                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │   LangGraph Framework          │ │ │
│  │  │   (Pregel execution engine)    │ │ │
│  │  │                                 │ │ │
│  │  │   - Actors (PregelNodes)       │ │ │
│  │  │   - Channels (state)           │ │ │
│  │  │   - Checkpoint creation        │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │            ↓                          │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │   Checkpointer                  │ │ │
│  │  │   (SqliteSaver/PostgresSaver)  │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └───────────────────────────────────────┘ │
│                   ↓                         │
└───────────────────┼─────────────────────────┘
                    ↓
            ┌───────────────┐
            │   SQLite DB   │
            │  (agent.db)   │
            │               │
            │  Checkpoints  │
            │  stored here  │
            └───────────────┘
```

### State Persistence

**Where state lives**: In YOUR database (SQLite file or Postgres connection)

**How it works**:
1. Graph executes step N
2. Framework calls `checkpointer.put(checkpoint)`
3. Checkpointer writes to YOUR database
4. State persists in YOUR infrastructure

**Scaling model**:
```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Agent 1     │       │  Agent 2     │       │  Agent 3     │
│  (Process)   │       │  (Process)   │       │  (Process)   │
│              │       │              │       │              │
│  graph.      │       │  graph.      │       │  graph.      │
│  invoke()    │       │  invoke()    │       │  invoke()    │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       │                      │                      │
       └──────────────────────┴──────────────────────┘
                              │
                              ↓
                    ┌─────────────────────┐
                    │  Shared Postgres DB │
                    │                     │
                    │  All checkpoints    │
                    └─────────────────────┘
```

**You manage:**
- ✅ Process scaling (Kubernetes pods, EC2 instances, etc.)
- ✅ Database scaling (Postgres HA, read replicas)
- ✅ Connection pooling
- ✅ Backup strategy
- ✅ Monitoring

**Framework provides:**
- ✅ Checkpoint creation (automatic)
- ✅ State serialization
- ✅ Graph execution logic
- ❌ HTTP API (you build if needed)
- ❌ Task queue (you build if needed)
- ❌ Multi-tenancy (you implement)

### When to Use

✅ **Maximum control**: You own the entire stack
✅ **Embedded deployments**: Edge devices, desktop apps
✅ **Custom infrastructure**: Existing k8s, custom load balancing
✅ **Offline-first**: No internet required
✅ **Cost optimization**: No platform fees, minimal overhead

---

## Architecture 2: LangGraph SDK (Client-Server Model)

### What It Is

From `/libs/sdk-py/README.md:16-35`:

```python
# You import the SDK (thin HTTP client)
from langgraph_sdk import get_client

# You connect to a running server
client = get_client(url="http://localhost:2024")  # or remote URL

# You send commands via HTTP
thread = await client.threads.create()
async for chunk in client.runs.stream(
    thread['thread_id'],
    assistant_id,
    input={"messages": [{"role": "human", "content": "Hello"}]}
):
    print(chunk)
```

### Execution Model

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Application                          │
│                                                                  │
│  from langgraph_sdk import get_client                           │
│  client = get_client(url="http://server:2024")                 │
│  client.runs.stream(...)  ←─ HTTP request                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ HTTP/SSE
                               │ (REST API)
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Server                              │
│                    (Docker container)                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LangGraph Server API (FastAPI)                           │ │
│  │                                                            │ │
│  │  Endpoints:                                                │ │
│  │  - POST /threads                                           │ │
│  │  - POST /threads/{id}/runs                                 │ │
│  │  - GET  /threads/{id}/state                                │ │
│  │  - POST /assistants                                        │ │
│  │                                                            │ │
│  │  Request → Enqueue to Task Queue                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Task Queue (Redis)                                        │ │
│  │                                                            │ │
│  │  Pending runs, background jobs, webhooks                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Worker Processes                                          │ │
│  │                                                            │ │
│  │  Pull tasks → Execute graphs → Write checkpoints          │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │   LangGraph Framework (embedded in server)          │ │ │
│  │  │                                                      │ │ │
│  │  │   graph.invoke() called by worker                   │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            ↓
                 ┌──────────────────────┐
                 │   PostgreSQL         │
                 │                      │
                 │   Checkpoints        │
                 │   Threads            │
                 │   Assistants         │
                 │   Runs metadata      │
                 └──────────────────────┘
```

### State Persistence

From `/docs/docs/concepts/langgraph_server.md:40-48`:

**Where state lives**: In the **LangGraph Server's PostgreSQL database**

**Required infrastructure:**
- **PostgreSQL**: For persistence (checkpoints, threads, assistants)
- **Redis**: For task queue

**How it works**:
1. Client sends HTTP request: `POST /threads/{id}/runs`
2. Server enqueues task to Redis
3. Worker pulls task from queue
4. Worker executes graph (framework embedded in server)
5. Framework writes checkpoint to **server's Postgres**
6. Client receives streaming response via SSE

**Scaling model**:
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Client 1    │  │  Client 2    │  │  Client 3    │
│              │  │              │  │              │
│  SDK         │  │  SDK         │  │  SDK         │
│  HTTP calls  │  │  HTTP calls  │  │  HTTP calls  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                         ↓ (HTTP/REST)
               ┌──────────────────────┐
               │  Load Balancer       │
               └──────────┬───────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ↓               ↓               ↓
  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
  │ Server Pod 1  │ │ Server Pod 2  │ │ Server Pod 3  │
  │               │ │               │ │               │
  │ API + Workers │ │ API + Workers │ │ API + Workers │
  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ↓
          ┌───────────────────────────────┐
          │  Shared Infrastructure         │
          │                               │
          │  - PostgreSQL (HA cluster)    │
          │  - Redis (sentinel/cluster)   │
          └───────────────────────────────┘
```

**Platform manages:**
- ✅ HTTP API (RESTful endpoints)
- ✅ Task queue (Redis-backed)
- ✅ Worker scaling (auto-scale workers)
- ✅ Database management (Postgres HA)
- ✅ Multi-tenancy (built-in isolation)
- ✅ Monitoring (built-in metrics)

**You manage:**
- ✅ Client code (SDK calls)
- ✅ Business logic in graph definitions
- ❌ Server infrastructure (handled by platform)
- ❌ Database scaling (managed)
- ❌ Task queue (managed)

### When to Use

✅ **Multi-tenant applications**: Built-in isolation, API keys
✅ **Background processing**: Task queue handles long-running jobs
✅ **Webhooks**: Asynchronous notifications when runs complete
✅ **Managed infrastructure**: Don't want to manage Postgres/Redis
✅ **API-first**: Need REST API for multiple clients (web, mobile, etc.)
✅ **Studio integration**: Visual debugging with LangGraph Studio

---

## State Persistence at Scale: The Critical Difference

### Framework Model (You Scale)

**Challenge**: Your responsibility to handle scale

```python
# 1000 concurrent agents
for i in range(1000):
    agent_process = spawn(execute_agent, agent_id=i)

# Each process needs:
# - Connection to shared Postgres
# - Connection pooling
# - Handling connection limits
# - Transaction management
```

**You must handle:**
1. **Connection pooling**: PgBouncer, connection pool exhaustion
2. **Database locks**: Concurrent writes to same thread
3. **Checkpoint versioning**: Race conditions on state updates
4. **Backup/restore**: Your backup strategy
5. **Monitoring**: Track checkpoint writes, query performance

**Example scaling pain points:**
```python
# Problem 1: Connection pool exhaustion
# 1000 agents × 10 connections each = 10,000 connections
# Postgres max_connections default = 100 (uh oh)

# Problem 2: Hot threads
# Multiple agents writing to same thread_id simultaneously
# Need pessimistic locking:
checkpointer.put(checkpoint, thread_id="hot-thread")  # Can block

# Problem 3: Checkpoint bloat
# Thread with 10,000 steps = 10,000 checkpoint rows
# Full history stored, need pruning strategy
```

**Solutions you build:**
```python
# Connection pooling
from sqlalchemy.pool import QueuePool
engine = create_engine(
    "postgresql://...",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

# Distributed locking
import redis
lock = redis_client.lock(f"thread:{thread_id}", timeout=30)
with lock:
    checkpoint = checkpointer.put(...)

# Checkpoint pruning
def prune_old_checkpoints(thread_id: str, keep_last_n: int = 100):
    # Your code to delete old checkpoints
    pass
```

### SDK Model (Platform Scales)

**Challenge**: Platform responsibility to handle scale

From LangGraph Server architecture:

```python
# Client code (simple)
client = get_client()
await client.runs.create(thread_id, assistant_id, input)

# Server handles (abstracted away):
# - Connection pooling (built-in)
# - Task queue (Redis-backed)
# - Worker auto-scaling
# - Database optimization
# - Rate limiting
```

**Platform handles:**
1. **Connection pooling**: Managed connection pool per worker
2. **Task serialization**: Redis queue prevents concurrent writes to same thread
3. **Checkpoint optimization**: Background cleanup, archival
4. **Backup/restore**: Managed database backups
5. **Monitoring**: Built-in metrics, dashboards

**How platform solves scaling:**

```
Request flow with built-in safeguards:

Client → HTTP → Server → Redis Queue → Worker Pool → Postgres
                  │         │             │            │
                  │         │             │            │
              Rate limit  Prevents    Connection    Optimized
                       concurrent    pooling       queries
                       writes
```

**Example: Concurrent runs on same thread**

**Framework (your problem):**
```python
# Two agents writing to thread "123" simultaneously
# Agent 1
graph1.invoke(input1, config={"configurable": {"thread_id": "123"}})

# Agent 2 (same time)
graph2.invoke(input2, config={"configurable": {"thread_id": "123"}})

# Risk: Race condition on checkpoint versions
# You need distributed locking
```

**SDK (platform problem, already solved):**
```python
# Two clients sending to same thread
# Client 1
await client.runs.create("thread-123", assistant_id, input1)

# Client 2 (same time)
await client.runs.create("thread-123", assistant_id, input2)

# Server serializes via queue:
# Run 1 → Queue → Execute → Checkpoint → Complete
# Run 2 → Queue → Wait → Execute → Checkpoint → Complete
# No race conditions
```

---

## The Persistence Architecture Split

### Framework: Direct Database Access

```
Your Code → LangGraph Framework → Checkpointer Interface → Database
                                      │
                                      ├─ SqliteSaver → SQLite file
                                      ├─ PostgresSaver → Postgres DB
                                      └─ CustomSaver → Your storage
```

**Characteristics:**
- **Direct writes**: No intermediary, immediate persistence
- **Your database**: You provision, you manage
- **Checkpoint format**: Dict → JSON → Bytes → DB row
- **Versioning**: You handle concurrent writes
- **Cleanup**: You implement pruning logic

### SDK: Server-Managed Persistence

```
SDK → HTTP API → LangGraph Server → Task Queue → Worker → Framework → Postgres
                                                              │
                                                              └─ Server's Checkpointer
```

**Characteristics:**
- **Queued writes**: Through task queue, serialized
- **Platform database**: Managed Postgres
- **Checkpoint format**: Same (dict → JSON → bytes → row)
- **Versioning**: Server handles concurrency
- **Cleanup**: Platform handles pruning

---

## Multi-Tenancy at Scale

### Framework Model

**You implement multi-tenancy:**

```python
# Option 1: Schema per tenant (Postgres)
checkpointer = PostgresSaver(
    connection_string=f"postgresql://...?schema={tenant_id}"
)

# Option 2: Tenant ID in thread_id
config = {"configurable": {"thread_id": f"{tenant_id}:{user_thread_id}"}}

# Option 3: Separate database per tenant
checkpointer = get_tenant_checkpointer(tenant_id)
```

**Challenges:**
- Connection limits scale with tenants
- Need tenant isolation in queries
- Backup strategy per tenant
- Monitoring per tenant

### SDK Model

**Platform implements multi-tenancy:**

```python
# Built-in via API keys
client = get_client(api_key="tenant_123_key")

# Server automatically isolates:
# - Threads scoped to API key
# - Assistants scoped to project
# - Rate limits per tenant
# - Usage tracking per tenant
```

**Platform provides:**
- Automatic tenant isolation
- Built-in API key management
- Per-tenant usage metrics
- Shared infrastructure efficiency

---

## Performance Characteristics

### Framework (Embedded Execution)

**Latency:**
- ✅ **Zero network overhead**: In-process execution
- ✅ **Direct DB writes**: No queue latency
- ✅ **Local state**: Memory access is fast

**Throughput:**
- Limited by your process/database capacity
- Scale by adding more processes + connection pooling
- Database becomes bottleneck at high concurrency

**Example:**
```
Single agent run:
- Graph execution: 100ms
- Checkpoint write: 10ms
- Total: 110ms (pure execution time)
```

### SDK (Client-Server Execution)

**Latency:**
- ❌ **Network overhead**: HTTP request + response
- ❌ **Queue latency**: Task waits in Redis queue
- ✅ **Async execution**: Client doesn't block on execution

**Throughput:**
- Limited by worker pool size
- Scale by adding more workers
- Queue absorbs burst traffic

**Example:**
```
Single agent run:
- HTTP request: 5ms
- Queue wait: 50ms (under load)
- Graph execution: 100ms
- Checkpoint write: 10ms
- HTTP response: 5ms
- Total: 170ms (includes infrastructure overhead)
```

**Trade-off:**
- **Framework**: Lower latency, you manage scaling
- **SDK**: Higher latency, platform handles scaling

---

## Cost Model Comparison

### Framework (Pay for What You Use)

```
Infrastructure costs:
├── Compute: Your EC2/K8s nodes
├── Database: Your Postgres instance
├── Storage: Your disk/S3
└── Network: Your data transfer

Cost scales with:
- Number of processes running
- Database size
- Query volume
```

**Example monthly cost (self-hosted):**
```
- 4 CPU compute (ECS/EC2): $150
- RDS Postgres (db.t3.medium): $50
- Storage (100GB): $10
- Network egress: $20
Total: ~$230/month (fixed, regardless of usage)
```

**Breakeven:** Low usage still costs $230/month

### SDK (Pay for Platform + Infrastructure)

```
Platform costs:
├── LangGraph Cloud subscription
├── Usage-based billing (runs, tokens)
└── Infrastructure managed by platform

OR

Self-hosted costs:
├── Your Postgres (managed persistence)
├── Your Redis (managed task queue)
├── Your compute (for server containers)
└── LangGraph Server license (enterprise)
```

**Example monthly cost (Cloud SaaS):**
```
- Free tier: 0-10k runs
- Paid tier: $50/month + $0.001 per run
- 100k runs: $50 + $100 = $150/month
```

**Breakeven:** Low usage is cheaper, high usage may be more expensive

---

## When to Use Each Model

### Use Framework (Direct Execution) When:

✅ **Need lowest latency**: In-process execution, no HTTP overhead
✅ **Offline requirements**: Edge devices, air-gapped environments
✅ **Custom infrastructure**: Already have Postgres, want full control
✅ **Cost optimization at scale**: High volume makes platform fees expensive
✅ **Embedded deployments**: Desktop apps, mobile, IoT devices
✅ **Existing orchestration**: Already using Kubernetes, custom autoscaling

**Example use cases:**
- Edge AI agents on IoT devices
- Desktop AI assistants
- High-throughput batch processing (millions of runs/day)
- Multi-cloud deployments with custom routing

### Use SDK (Client-Server) When:

✅ **Multi-tenant SaaS**: Need built-in API key management, isolation
✅ **Don't want to manage infrastructure**: Postgres/Redis/workers managed
✅ **Need background processing**: Long-running jobs, webhooks
✅ **API-first architecture**: Multiple clients (web, mobile, integrations)
✅ **Team collaboration**: LangGraph Studio for debugging
✅ **Rapid prototyping**: Get started without infrastructure setup

**Example use cases:**
- Multi-tenant chatbot platform
- API service for mobile apps
- Enterprise deployment with managed infrastructure
- Teams needing Studio integration

### Use Both (Hybrid) When:

✅ **Development with SDK, production with framework**: Prototype fast, optimize later
✅ **Edge + cloud hybrid**: Edge agents sync to cloud platform
✅ **Critical path on framework, analytics on platform**: Fast execution + observability

---

## The Crystallized Truth

**LangGraph Framework vs SDK is NOT just a deployment choice.**

**It's two fundamentally different execution models:**

| Dimension | Framework (Library) | SDK (Client-Server) |
|-----------|-------------------|---------------------|
| **Execution** | In your process | In server process |
| **State** | Your database | Server's database |
| **Scaling** | You manage | Platform manages |
| **Latency** | <110ms (direct) | ~170ms (HTTP + queue) |
| **Multi-tenancy** | You implement | Built-in |
| **Cost (low volume)** | Fixed ~$230/mo | $0-50/mo (variable) |
| **Cost (high volume)** | Scales linearly | Platform fees + usage |
| **Complexity** | High (you build everything) | Low (platform handles) |

**The persistence difference:**

- **Framework**: State lives in **YOUR** database, written **DIRECTLY** by your code
- **SDK**: State lives in **SERVER'S** database, written **THROUGH** task queue

**The scaling difference:**

- **Framework**: You scale **YOUR PROCESSES** + database connections
- **SDK**: Platform scales **WORKERS** + manages queue

**Neither is "better" - they solve different problems:**

- **Framework** = Maximum control, minimum latency, maximum responsibility
- **SDK** = Managed infrastructure, API-first, platform overhead

**The choice depends on your constraints:**
- Can you manage Postgres + Redis + worker scaling? → Framework
- Do you want to focus on application logic only? → SDK
- Need sub-100ms latency? → Framework
- Need multi-tenant API out of the box? → SDK

Most importantly: **You can start with SDK, migrate to framework later** (or vice versa). The graph code is the same - only the execution environment changes.
