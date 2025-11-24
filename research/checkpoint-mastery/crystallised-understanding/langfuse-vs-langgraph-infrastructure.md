# Langfuse vs LangGraph: Infrastructure & Multi-Repo Architecture Comparison

## Executive Summary

**Langfuse** = Observability platform (SaaS product with self-hosting)
**LangGraph** = Agent orchestration framework (open-source library with optional platform)

Both are monorepos, but serve fundamentally different purposes and have radically different infrastructure requirements.

---

## Infrastructure Stack Comparison

### Langfuse Infrastructure (Full Application Stack)

From `/docker-compose.yml:6-150`:

```yaml
Services Required:
├── langfuse-web (Next.js app on port 3000)
├── langfuse-worker (Background job processor on port 3030)
├── postgres (Relational DB for metadata)
├── clickhouse (Analytics/OLAP database)
├── redis (Queue + cache)
└── minio (S3-compatible object storage)
```

**Dependencies:**
- **PostgreSQL**: User auth, project config, metadata, relational queries
- **ClickHouse**: High-volume trace storage, analytics queries, time-series data
- **Redis**: Job queues (BullMQ), caching, rate limiting
- **MinIO/S3**: Large payloads, batch exports, media uploads

**Why this stack?**
- Handles **millions of traces/month** with fast analytics
- Separates OLTP (Postgres) from OLAP (ClickHouse)
- Async background processing (worker + Redis queues)
- Scales horizontally (multiple workers, ClickHouse clusters)

### LangGraph Infrastructure (Minimal Runtime)

From my earlier research of `/libs/checkpoint-*`:

```yaml
Optional Services (Choose Your Storage):
├── SQLite (embedded, single-file)
├── PostgreSQL (client-server)
└── Redis/MongoDB/Custom (DIY)

Required at Runtime:
└── Just your Python/JS process (that's it)
```

**Dependencies:**
- **Checkpointer** (your choice): InMemory, SQLite, Postgres, or custom
- **No analytics DB required** - just state persistence
- **No worker queues** - execution is synchronous or async in-process
- **No object storage** - checkpoints are serialized state blobs

**Why this stack?**
- Agent execution framework, not a platform
- State persistence is the only requirement
- Can run completely offline (SQLite)
- Infrastructure scales with your app, not framework

---

## Monorepo Structure Comparison

### Langfuse Monorepo (TypeScript/Next.js Monorepo)

From workspace root structure:

```
langfuse/
├── web/                    # Next.js frontend (port 3000)
│   ├── src/
│   │   ├── pages/         # Next.js pages
│   │   ├── components/    # UI components
│   │   └── server/        # tRPC API, Prisma ORM
│   ├── package.json       # Dependencies
│   └── Dockerfile         # Web container
│
├── worker/                 # Background job processor (port 3030)
│   ├── src/
│   │   └── queues/        # BullMQ job handlers
│   ├── package.json
│   └── Dockerfile         # Worker container
│
├── packages/
│   ├── shared/            # Shared utilities, Prisma schema, types
│   ├── config-eslint/     # Shared linting config
│   └── config-typescript/ # Shared TS config
│
├── ee/                     # Enterprise Edition features
│   ├── src/
│   └── package.json
│
├── docker-compose.yml      # Full stack orchestration
├── pnpm-workspace.yaml     # Monorepo config
└── turbo.json              # Build orchestration (Turborepo)
```

**Package Manager**: `pnpm` + Turborepo
**Language**: TypeScript (Node 24)
**Monorepo Type**: Application monorepo (web app + worker service + shared libs)

### LangGraph Monorepo (Python Monorepo)

From `/libs/` structure:

```
my-langgraph/
├── libs/
│   ├── langgraph/          # Core framework
│   │   ├── langgraph/
│   │   │   ├── graph/      # StateGraph, MessageGraph
│   │   │   ├── pregel/     # Execution engine
│   │   │   ├── channels/   # Communication primitives
│   │   │   └── types.py    # Core types
│   │   ├── pyproject.toml
│   │   └── tests/
│   │
│   ├── checkpoint/         # Base checkpoint interface
│   ├── checkpoint-postgres/  # Postgres implementation
│   ├── checkpoint-sqlite/    # SQLite implementation
│   ├── prebuilt/           # High-level APIs (ReAct agent)
│   ├── sdk-py/             # Python SDK for LangGraph Platform
│   ├── sdk-js/             # JavaScript SDK
│   └── cli/                # LangGraph CLI (Docker builds)
│
├── docs/                   # Documentation site
├── examples/               # 60+ Jupyter notebooks
├── Makefile                # Cross-package build commands
└── README.md
```

**Package Manager**: `uv` (fast Python package installer)
**Language**: Python 3.10+
**Monorepo Type**: Library monorepo (framework + implementations + SDKs)

---

## Multi-Repo Strategy Comparison

### Langfuse: All-in-One Monorepo

**Philosophy**: Ship one product with multiple services

```
Single Repo:
└── langfuse/langfuse
    ├── Web UI
    ├── Worker
    ├── API (tRPC)
    └── Shared code
```

**Why all-in-one?**
- **Unified versioning**: Web + Worker always in sync
- **Atomic changes**: Update API + UI + Worker in single PR
- **Simplified deployment**: One version number, one Docker tag
- **Type safety**: Shared types across frontend/backend

**Trade-offs:**
- ✅ No version mismatches between services
- ✅ Refactoring across services is easy
- ❌ Large repo (complicated for contributors)
- ❌ Can't version web/worker independently

### LangGraph: Multi-Package Monorepo

**Philosophy**: Framework with pluggable implementations

```
Single Repo with Independent Packages:
└── langchain-ai/langgraph
    ├── langgraph (core) → pip install langgraph
    ├── checkpoint-postgres → pip install langgraph-checkpoint-postgres
    ├── checkpoint-sqlite → pip install langgraph-checkpoint-sqlite
    ├── prebuilt → pip install langgraph-prebuilt
    └── cli → pip install langgraph-cli
```

**Why multi-package?**
- **Independent versioning**: Core can release without checkpoint updates
- **Optional dependencies**: Use only what you need (langgraph + sqlite, no Postgres)
- **Clear boundaries**: Checkpoint interface is stable, implementations evolve
- **Ecosystem-friendly**: Other devs can publish their own checkpoint implementations

**Trade-offs:**
- ✅ Users install minimal dependencies
- ✅ Third-party extensions possible (custom checkpointers)
- ❌ Version compatibility matrix (which checkpoint version works with which core?)
- ❌ More complex dependency management

---

## Deployment Model Comparison

### Langfuse Deployment: Platform as Product

**Options:**

| Deployment | Infrastructure Managed By | Use Case |
|------------|--------------------------|----------|
| **Cloud SaaS** | Langfuse team | Fast start, no ops |
| **Self-Hosted Docker** | You (Docker Compose) | Small teams, VM deployment |
| **Self-Hosted K8s** | You (Helm charts) | Production, multi-tenant |
| **Terraform (AWS/Azure/GCP)** | You (IaC templates) | Enterprise, compliance |

**What you deploy:**
```bash
docker compose up  # Starts 6 services (web, worker, postgres, clickhouse, redis, minio)
```

**Runtime requirements:**
- Always need full stack (can't run without ClickHouse)
- Always need Redis (for queues)
- Always need S3/MinIO (for large payloads)
- Minimum: ~2GB RAM, 2 CPU cores

### LangGraph Deployment: Library in Your App

**Options:**

| Deployment | What You Run | Use Case |
|------------|--------------|----------|
| **Local Python script** | Your app + SQLite file | Development, edge |
| **Docker container** | Your app + Postgres | Single-server production |
| **Kubernetes pods** | Your app + shared Postgres | Multi-tenant, scale |
| **LangGraph Platform** | Managed service (optional) | Platform features (UI, API) |

**What you deploy:**
```bash
python your_agent.py  # Just your code + checkpoint file
# OR
docker run your-agent:latest  # Your container (LangGraph is a library inside)
```

**Runtime requirements:**
- Only need checkpoint storage (SQLite file or Postgres connection)
- No analytics DB required
- No worker processes required
- Minimum: <100MB RAM (depends on your agent)

**Key difference:**
- **Langfuse**: You deploy Langfuse platform
- **LangGraph**: You deploy your app (LangGraph is a dependency)

---

## SDK / Client Library Strategy

### Langfuse SDKs (Separate Repos)

**External Repositories:**
```
langfuse/langfuse-python  → pip install langfuse
langfuse/langfuse-js      → npm install langfuse
```

**Why separate repos?**
- Different release cadences (Python SDK can ship fixes without waiting for main repo)
- Different contributor communities (Python vs JS devs)
- Cleaner dependency management (SDK doesn't need Next.js dependencies)

**Architecture:**
```
Client App → Langfuse SDK → HTTP API → Langfuse Platform
```

SDK is a **thin HTTP client** that sends traces/scores to the platform.

### LangGraph SDKs (In Monorepo)

**In-Monorepo Packages:**
```
langgraph/libs/sdk-py/   → pip install langgraph-sdk
langgraph/libs/sdk-js/   → npm install @langchain/langgraph-sdk
```

**Why in monorepo?**
- SDK tightly coupled to platform API (same team, same versioning)
- SDKs only needed for LangGraph Platform (optional product)
- Framework (langgraph) has **no SDK** - it's the framework itself

**Architecture:**
```
# Without Platform:
Your App → import langgraph → Direct execution

# With Platform (optional):
Your App → LangGraph SDK → HTTP API → LangGraph Server
```

---

## Key Architectural Differences

### 1. **Product Type**

| Langfuse | LangGraph |
|----------|-----------|
| **SaaS Platform** with self-hosting option | **Framework/Library** with optional platform |
| Always runs as a service | Runs in your application process |
| You send data TO Langfuse | Your app IS the execution environment |

### 2. **Infrastructure Complexity**

| Langfuse | LangGraph |
|----------|-----------|
| 6 services minimum (web, worker, 4 databases/caches) | 1 service (your app) + 1 database (checkpoint storage) |
| Requires Postgres + ClickHouse + Redis + S3 | Only requires a checkpointer (even in-memory works) |
| ~$330/month fixed cost for self-hosted | $0 infrastructure cost (runs in your existing app) |

### 3. **Scaling Model**

| Langfuse | LangGraph |
|----------|-----------|
| Horizontal scaling of web/worker pods | Your app scales (LangGraph scales with it) |
| ClickHouse clusters for analytics | No analytics - just checkpoint writes |
| Redis for distributed queues | No queues - execution is in-process |
| Handles millions of traces centrally | Each agent instance handles own execution |

### 4. **Data Residency**

| Langfuse | LangGraph |
|----------|-----------|
| Centralized: All traces flow to Langfuse | Distributed: State lives where agents run |
| Cloud option stores data in Langfuse DB | Self-hosted: Data stays in your database |
| Trace export required for data portability | Checkpoints are already in your DB |

### 5. **Multi-Tenancy Strategy**

| Langfuse | LangGraph |
|----------|-----------|
| Built-in: Organizations, projects, users in DB | DIY: You implement per-user checkpoint isolation |
| Single Langfuse instance serves many tenants | Each tenant can have isolated agent instances |
| Requires complex auth/isolation in platform | No built-in multi-tenancy (framework-level) |

---

## Similarities

### 1. **Both are Monorepos (But Different Kinds)**

- **Langfuse**: Application monorepo (web + worker + shared UI)
- **LangGraph**: Library monorepo (core + implementations + SDKs)

Both use monorepo for code sharing, but different purposes:
- Langfuse shares **UI components and API contracts**
- LangGraph shares **checkpoint interfaces and types**

### 2. **Both Support Self-Hosting**

- **Langfuse**: Docker Compose, Kubernetes, Terraform templates
- **LangGraph**: Just deploy your app (framework is embedded)

But "self-hosting" means different things:
- Langfuse: Run the Langfuse platform yourself
- LangGraph: Run your agent application yourself

### 3. **Both Have Enterprise Editions**

- **Langfuse**: `/ee` directory with SSO, RBAC, audit logs
- **LangGraph**: Enterprise features in LangGraph Platform (control plane, managed hosting)

### 4. **Both Have Cloud + Self-Hosted Options**

| Feature | Langfuse Cloud | LangGraph Cloud |
|---------|----------------|-----------------|
| **Managed hosting** | ✅ | ✅ |
| **Self-host** | ✅ (full platform) | ✅ (agent containers) |
| **Free tier** | ✅ (50k events) | ✅ (development) |
| **Open source** | ✅ (MIT license) | ✅ (MIT license) |

### 5. **Both Use Postgres** (But Differently)

- **Langfuse**: Postgres stores users, projects, metadata (+ ClickHouse for traces)
- **LangGraph**: Postgres stores checkpoints only (if you choose PostgresSaver)

---

## When to Use What

### Use Langfuse When:
- ✅ You need **centralized observability** across multiple agents/apps
- ✅ You want **analytics dashboards** for traces, costs, latency
- ✅ You need **team collaboration** (shared projects, prompt management)
- ✅ You're okay running a **full platform** (6 services)
- ✅ You want **LLM-as-a-judge evaluations** built-in

### Use LangGraph When:
- ✅ You need **durable, stateful agents** that survive failures
- ✅ You want **human-in-the-loop** workflows with interrupts
- ✅ You need **time-travel debugging** (rewind to any checkpoint)
- ✅ You want **minimal infrastructure** (just your app + database)
- ✅ You prefer **framework over platform** (maximum control)

### Use Both Together:
```python
from langgraph import StateGraph
from langfuse import observe

@observe()  # Langfuse traces
def my_agent_node(state):
    # LangGraph execution
    return updated_state

graph = StateGraph(State)
graph.add_node("agent", my_agent_node)
graph = graph.compile(checkpointer=checkpointer)  # LangGraph persistence

# LangGraph handles execution + durability
# Langfuse handles observability + evaluation
```

**The combination:**
- **LangGraph** = Runtime (make agents survive crashes)
- **Langfuse** = Observability (see what agents are doing, evaluate quality)

---

## Infrastructure Decision Tree

```
Do you need centralized observability for multiple apps/agents?
├─ YES → Deploy Langfuse (self-hosted or cloud)
│         ├─ Budget for Postgres + ClickHouse + Redis + S3
│         └─ Instrument apps with Langfuse SDK
│
└─ NO → Skip Langfuse, use lightweight logging

Do you need agents that survive crashes and support human-in-loop?
├─ YES → Use LangGraph framework
│         ├─ Choose checkpointer (SQLite for small, Postgres for scale)
│         └─ Deploy your app (LangGraph is a dependency)
│
└─ NO → Use standard LangChain or custom orchestration

Do you want both observability AND durable agents?
└─ Use LangGraph + Langfuse together
   └─ LangGraph handles execution, Langfuse handles monitoring
```

---

## The Crystallized Truth

**Langfuse and LangGraph solve orthogonal problems:**

| Dimension | Langfuse | LangGraph |
|-----------|----------|-----------|
| **Problem Space** | Observability (monitoring) | Orchestration (execution) |
| **Architecture** | Platform (SaaS + self-hosted) | Library (embedded) |
| **Infrastructure** | Heavy (6 services) | Light (1 checkpoint DB) |
| **Data Flow** | Push traces TO platform | State lives IN your app |
| **Deployment** | Deploy Langfuse | Deploy your app |
| **Cost Model** | Per trace ingested | $0 (framework is free) |
| **Multi-Repo** | Monolith monorepo | Federated monorepo |

**They are complementary, not competitive:**
- LangGraph ensures your agents **don't lose state**
- Langfuse ensures you **understand what they did**

**The infrastructure difference is architectural:**
- **Langfuse** = Centralized analytics platform (like Datadog/Prometheus for LLMs)
- **LangGraph** = Distributed execution framework (like Temporal/Cadence for agents)

One is a **destination** for data. The other is a **runtime** for code.
