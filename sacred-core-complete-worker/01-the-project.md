```yaml
name: Complete Worker - The Project
description: Worker Marketplace Architecture. First-class worker definitions with enforced constraints, witness verification, and user journey isolation.
created: 2025-11-25
version: 1.0.0
phase: R13
```

# Complete Worker: Project Truth Template

**Meta:** This template encodes the architectural shift from "workers as tools" to "workers as containers for user journeys."

## Sacred Primitive

```
Complete Worker = Worker Definition (first-class entity)
                + Runtime Isolation (per user journey)
                + Constraint Enforcement (automatic witness)
                + Trust Escalation (supervised → autonomous)
```

**What Complete Worker IS:**
- Worker marketplace where each worker type is a pre-configured Claude Code instance
- User journey isolation with protected filesystem + session persistence
- Platformized constraint enforcement (witness verification at every LLM chain step)
- Trust-level management from supervised (HITL) to autonomous

**What Complete Worker IS NOT:**
- Replacement for R11 Worker Protocol (builds on top of it)
- Generic worker pool (workers are specialized by definition)
- User-facing workflow builder (workers execute within LangGraph workflows)
- Permission system (trust levels are scoped to worker capabilities)

---

## The Truth Shift: Worker-as-Tool vs Worker-as-Container

### Current State (R11): **Worker-as-Tool**
```
Worker-as-Tool = Execution abstraction
               + 7-tool interface (void, execute, etc.)
               + Manager dispatches to worker
               + Shared across coordination decisions
```

**Characteristics:**
- Workers are stateless executors (GitWorker, DatabaseWorker, FileWorker)
- ExecutorNode selects worker type and dispatches action
- Workers respond to coordination decisions
- No per-user isolation (shared instances)
- Constraints enforced via void() safety gate

**Mental Model:**
```python
# R11 Pattern: Worker as execution tool
executor = ExecutorNode(
    executor_id="exec_1",
    workers={
        "git": GitWorker(),
        "db": DatabaseWorker(),
        "file": FileWorker()
    }
)

# All coordination decisions use same worker instances
result = await executor.execute(coordination_decision)
```

**Key Learning:** Workers execute actions but don't carry user context.

### Future State (R13): **Worker-as-Container**
```
Worker-as-Container = Worker Definition (yaml spec)
                    + Isolated Runtime (docker + workspace)
                    + Constraint Enforcement (platformized witness)
                    + User Journey Context (session persistence)
```

**Characteristics:**
- Worker definition is first-class entity (identity, constraints, tools, trust level)
- Each user journey gets dedicated worker instance
- Worker carries user context across session
- Constraints enforced automatically by platform (not manually)
- Trust levels enable progressive autonomy

**Mental Model (Not Yet Implemented):**
```yaml
# Worker Definition (first-class entity)
worker_definition:
  worker_id: "research_assistant_v1"

  identity:
    name: "Research Assistant"
    system_prompt: "You help with deep research using web search and document analysis..."
    onboarding:
      - "Connect to research database"
      - "Load user preferences"
      - "Review citation style"

  constraints:
    - constraint_id: "no_hallucinated_citations"
      witness: "verify_source_exists"
      feedback: "alert_user"
    - constraint_id: "max_web_searches_per_hour"
      value: 50
      witness: "count_search_api_calls"
    - constraint_id: "require_approval_for_paid_sources"
      witness: "verify_purchase_approval"

  tools:
    - "web_search"
    - "browser"
    - "filesystem"
    - "document_parser"

  trust_level: "supervised"  # supervised | monitored | autonomous

  runtime:
    container: "claude-code:latest"
    workspace: "/home/claude/workspace/{user_journey_id}"
    session_persistence: true
```

**Worker Factory Pattern:**
```python
# R13 Pattern: Worker as user journey container
from workers.factory import WorkerFactory
from workers.definitions.loader import load_worker_definition

# Load worker definition
definition = load_worker_definition("research_assistant_v1.yaml")

# Spawn worker instance for user journey
worker = WorkerFactory.spawn(
    definition=definition,
    user_journey_id="user_123_session_456",
    isolation_level="container"  # container | process | thread
)

# Worker carries user context, constraints enforced automatically
result = await worker.execute(action)  # witness verification runs automatically
```

**Key Learning:** Worker instance = user journey container with enforced constraints.

---

## R13 Status: Roadmap (0% Complete)

### What We Have (R11)
```yaml
worker_protocol: 7-tool interface (state, pressure, constraints, flow, void, execute, evolve)
concrete_workers: GitWorker, DatabaseWorker, MockWorker
integration: ExecutorNode dispatch pattern
safety: void() simulation before execute()
audit: Execution channel logging
```

### What We Need (R13)
```yaml
worker_definitions: YAML schema for worker configs
worker_factory: Spawn worker instances from definitions
journey_isolation: Per-user docker containers + workspaces
constraint_platform: Automatic witness verification at each LLM step
trust_escalation: Supervised → Monitored → Autonomous progression
marketplace: Catalog of pre-configured worker types
```

### Gap Analysis
```
R11 provides EXECUTION LAYER (how workers execute actions)
R13 provides CONFIGURATION LAYER (how workers are defined + isolated)

Missing pieces:
1. Worker Definition Schema (yaml spec + validation)
2. Worker Factory (definition → runtime instance)
3. Journey Isolation (container spawning + workspace management)
4. Constraint Enforcement Platform (witness automation)
5. Trust Level Management (approval workflows)
```

---

## Architecture Components

### 1. Worker Definition (First-Class Entity)

**File:** `workers/definitions/schema.py`

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Literal

@dataclass
class WorkerIdentity:
    name: str
    system_prompt: str
    onboarding_steps: List[str]

@dataclass
class WorkerConstraint:
    constraint_id: str
    witness: str  # Function name for verification
    feedback: str  # Where to send violations (alert_dashboard, log, email)
    value: Any = None  # Optional constraint value

@dataclass
class WorkerRuntime:
    container: str = "claude-code:latest"
    workspace_template: str = "/home/claude/workspace/{user_journey_id}"
    tools: List[str] = None
    session_persistence: bool = True

@dataclass
class WorkerAudit:
    log_all_actions: bool = True
    execution_channel: str = "worker_executions"
    retention_days: int = 90

@dataclass
class WorkerDefinition:
    worker_id: str
    identity: WorkerIdentity
    constraints: List[WorkerConstraint]
    runtime: WorkerRuntime
    trust_level: Literal["supervised", "monitored", "autonomous"]
    audit: WorkerAudit
    tools: List[str]
```

### 2. Worker Factory (Definition → Instance)

**File:** `workers/factory.py`

```python
class WorkerFactory:
    """Spawn worker instances from definitions"""

    @staticmethod
    async def spawn(
        definition: WorkerDefinition,
        user_journey_id: str,
        isolation_level: Literal["container", "process", "thread"] = "container"
    ) -> "Worker":
        """
        Spawn worker instance for user journey

        Flow:
        1. Create isolated workspace (docker container or filesystem)
        2. Inject worker definition (system prompt, constraints, tools)
        3. Initialize session persistence
        4. Register constraint witnesses
        5. Return worker instance
        """
        # Implementation in R13.2
        pass
```

### 3. Constraint Enforcement Platform

**File:** `workers/enforcement/witness.py`

```python
class WitnessEnforcement:
    """Platformized constraint verification"""

    @staticmethod
    async def verify(
        worker_id: str,
        action: Dict[str, Any],
        constraints: List[WorkerConstraint]
    ) -> List[str]:
        """
        Run all constraint witnesses for action

        Returns:
            List of warning messages (empty if all constraints pass)

        Called automatically before every worker.execute()
        """
        # Implementation in R13.4
        pass
```

### 4. Journey Isolation

**File:** `workers/isolation/container.py`

```python
class ContainerIsolation:
    """Docker-based user journey isolation"""

    @staticmethod
    async def create_workspace(
        user_journey_id: str,
        workspace_template: str
    ) -> str:
        """
        Create isolated workspace for user journey

        Returns:
            Path to workspace (e.g., /home/claude/workspace/user_123_session_456)
        """
        # Implementation in R13.3
        pass
```

---

## Integration with Existing Platform

### How R13 Builds on R11

**R11 Provides:**
- Worker Protocol (7-tool interface)
- void() safety gate
- execute() actual operations
- Execution channel audit

**R13 Adds:**
- Worker definitions (configuration layer)
- Journey isolation (per-user containers)
- Automatic witness verification
- Trust level management

**Integration Point:**
```python
# R11: ExecutorNode dispatches to workers
executor = ExecutorNode(workers={"git": GitWorker()})

# R13: ExecutorNode dispatches to worker instances (per user journey)
worker_instance = WorkerFactory.spawn(
    definition=load_worker_definition("research_assistant_v1.yaml"),
    user_journey_id=thread_id  # From LangGraph checkpointer
)

executor = ExecutorNode(
    workers={"research": worker_instance}
)
```

### Constraint Enforcement Flow

```
1. Coordination Decision (R10) → ExecutorNode (R11.4)
2. ExecutorNode selects worker instance (R13 spawned)
3. Worker.void() simulation (R11.1 protocol)
4. WitnessEnforcement.verify() runs (R13.4 automatic)
5. If witnesses pass → Worker.execute() (R11.1 protocol)
6. Execution result logged (R10.4 execution channel)
```

---

## Progressive Complexity

### Level 1: Single Worker Definition
- Define one worker type (e.g., research_assistant_v1.yaml)
- Load definition and spawn instance
- Manual constraint verification

### Level 2: Worker Marketplace
- Multiple worker types (research, code_review, trading, etc.)
- Worker selection by user
- Catalog/registry of available workers

### Level 3: Automatic Witness Verification
- Platformized constraint enforcement
- Witness functions registered and called automatically
- Alert dashboard for violations

### Level 4: Trust Escalation
- Track worker safety record
- Auto-promote: supervised → monitored → autonomous
- Approval workflows for high-trust actions

---

## What This Unlocks

Once R13 is complete:

1. **Worker Templates** - Pre-configured workers for common use cases
2. **User Journey Isolation** - Each conversation in protected environment
3. **Constraint Marketplace** - Reusable constraint definitions
4. **Automatic Safety** - Witness verification without manual checks
5. **Progressive Trust** - Workers earn autonomy through safety record

**Truth:** The platform becomes a WORKER MARKETPLACE where safety is automatic, not negotiated.

---

## Mental Model Summary

**R11 (Current):** Workers are tools that execute actions.

**R13 (Future):** Workers are containers for user journeys with enforced constraints.

**Integration:** R13 configuration layer sits on top of R11 execution layer.

**Leverage:** Worker definitions enable rapid creation of specialized agents with guaranteed safety.
