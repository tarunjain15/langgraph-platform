```yaml
name: LangGraph Platform - Implementation Plan
description: Execution map. R1-R9 compressed (complete). R10+ roadmap expanded (agent coordination layer).
created: 2025-11-24
version: 3.0.0
status: R1-R9 complete (90% platform ready), R10+ crystallized
```

# LangGraph Platform: Implementation Plan

## Execution Status

**✅ R1-R9 Complete** - Workflow orchestration runtime (90% production-ready)
**🟡 R7 Deferred** - Operational automation (optional)
**🔮 R10+ Roadmap** - Agent coordination layer (future)

---

## R1-R9: Completed Phases (Compressed)

### R1: CLI Runtime ✅
**Unlocked:** Hot-reload workflow execution via `lgp run <workflow>`
**Witness:** File changes reload <500ms, console logs stream in real-time
**Foundation:** 3 tasks - CLI command structure, dynamic module loading, watchdog file monitoring

---

### R2: API Runtime ✅
**Unlocked:** Hosted mode API server with FastAPI
**Witness:** `lgp serve <workflow>` exposes /invoke endpoint, workflows callable via HTTP
**Infrastructure:** 4 tasks - FastAPI integration, /invoke endpoint, thread management, environment detection

---

### R3: Observability ✅
**Unlocked:** Langfuse tracing integration
**Witness:** Workflow spans visible in Langfuse dashboard, cost tracking automatic
**Capability:** 3 tasks - Langfuse client, trace context, runtime injection

---

### R4: Checkpointing ✅
**Unlocked:** SQLite persistence for workflow state
**Witness:** thread_id enables state recovery across invocations
**Production Ready:** 3 tasks - MemorySaver → SqliteSaver migration, cleanup, validation

---

### R5: Claude Code Nodes ✅
**Unlocked:** Claude Code agents as workflow nodes via MCP
**Witness:** claude_code_config triggers runtime node injection, session continuity works
**Agency:** 4 tasks - mesh-mcp integration, runtime injection, session persistence, repository isolation

---

### R6: Templates ✅
**Unlocked:** `lgp create <workflow> --template <name>` scaffolding
**Witness:** 3 templates (basic, multi_agent, with_claude_code) with mental model headers
**Pedagogy:** 3 tasks - Template creation, lgp create command, customization guides

---

### R6.5: Configuration ✅
**Unlocked:** YAML-driven infrastructure (experiment.yaml, hosted.yaml)
**Witness:** Workflows use load_config() instead of hardcoded settings
**Infrastructure:** 3 tasks - Config files, loader implementation, executor integration

---

### R8: Multi-Provider Agency ✅
**Unlocked:** Multiple LLM providers with cost optimization
**Witness:** Anthropic, OpenAI, Ollama providers work, cost estimates logged
**Expansion:** 7 tasks - Provider abstraction, Anthropic/OpenAI/Ollama implementations, ProviderFactory, cost tracking

---

### R9: PostgreSQL Checkpointer ✅ (90%)
**Unlocked:** Supabase persistence with retry + fallback resilience
**Witness:** State persists to PostgreSQL, 3-attempt retry → SQLite fallback on failure
**Production Ready:** 6 tasks - PostgresCheckpointer, Supabase config, connection validation, setup script, testing, documentation

**Parking Decision:** 90% complete. Retry + fallback = production-ready. Remaining 10%: connection pool wiring, observability metrics, circuit breaker (acceptable debt).

---

### R7: Production Mastery 🟡 Deferred
**Would Unlock:** Autonomous deployment and operations
**Deferred Because:** R1-R9 delivers complete workflow runtime. Deployment automation is optional. Users can deploy manually.
**Future:** 4 tasks - One-command deployment, auto-scaling, anomaly detection, self-healing restarts

---

## R10+: Agent Coordination Layer (Roadmap)

**Context:** Platform currently implements **Workflow Mode** (R1-R9) - sequential execution, known steps. **Agent Mode** (R10+) is next architectural layer - concurrent reactive agents.

**Constraint Shift:** Sequential workflows → Concurrent channel coordination

---

## R10: 4-Channel Coordination Pattern 🔮

### R10.1: Observation Channel
```yaml
task_id: R10.1
phase: R10
type: Integration
status: roadmap
```

**The Constraint:**
- **Before:** Workflows don't track external state changes
- **After:** Observer nodes mirror external truth continuously

**Observable Truth:** Observer node detects file system change, emits event to observation channel <100ms

**Witness Outcome:**
- File modified → observer node detects → observation channel receives event
- External API changes → observer polls → state change recorded
- Database update → observer queries → truth mirrored

**What This Unlocks:**
- Reactive workflows triggered by external events
- Continuous monitoring without manual polling
- Event-driven architecture foundation

**Code Pattern:**
```python
# Observation channel observes external state
class ObserverNode:
    def __init__(self, observation_channel):
        self.channel = observation_channel

    async def observe(self, external_state):
        # Mirror external truth
        delta = self.detect_change(external_state)
        if delta:
            await self.channel.send(delta)
```

**Acceptance Criteria:**
- [ ] ObserverNode class implements observe() method
- [ ] observation_channel receives state deltas <100ms
- [ ] Multiple observers can write to same channel
- [ ] Channel implements Topic reducer (all messages retained)

**Completion Signal:** External file changes detected, logged to observation channel, verified

**Reference:** research/ubiquitous-language/external-code-state-coordination.md

---

### R10.2: Intent Channel
```yaml
task_id: R10.2
phase: R10
type: Integration
status: roadmap
```

**The Constraint:**
- **Before:** Nodes execute immediately without planning
- **After:** Agent nodes generate action plans before execution

**Observable Truth:** Agent node writes action plan to intent channel, execution deferred

**Witness Outcome:**
- Agent generates plan: `{"action": "modify_file", "target": "test.py", "reason": "fix bug"}`
- Intent channel receives plan
- Coordinator reviews before execution

**What This Unlocks:**
- Action preview before execution
- Coordination between multiple agents
- Conflict detection and resolution

**Code Pattern:**
```python
# Intent channel stores action plans
class AgentNode:
    def __init__(self, intent_channel):
        self.channel = intent_channel

    async def plan(self, observation):
        # Generate action plan
        action = self.decide_action(observation)
        await self.channel.send({
            "agent_id": self.id,
            "action": action,
            "reason": "...",
            "timestamp": now()
        })
```

**Acceptance Criteria:**
- [ ] AgentNode generates action plan as dict
- [ ] intent_channel receives plans from multiple agents
- [ ] Plans include agent_id, action, reason, timestamp
- [ ] Channel implements Topic reducer (all plans retained)

**Completion Signal:** Multiple agents write plans, intent channel logs all, verified

**Reference:** research/ubiquitous-language/external-code-state-coordination.md

---

### R10.3: Coordination Channel
```yaml
task_id: R10.3
phase: R10
type: Integration
status: roadmap
```

**The Constraint:**
- **Before:** Multiple agents can write same field → concurrent write errors
- **After:** Coordinator node resolves conflicts, serializes execution

**Observable Truth:** Coordinator detects conflicting intents, resolves via priority/timestamp, emits decision

**Witness Outcome:**
- Agent A plans: modify test.py
- Agent B plans: delete test.py
- Coordinator detects conflict → resolves via policy → emits decision: "Agent A executes, Agent B waits"

**What This Unlocks:**
- Concurrent agent planning without collisions
- Policy-based conflict resolution
- Serialized execution guarantees

**Code Pattern:**
```python
# Coordination channel resolves conflicts
class CoordinatorNode:
    def __init__(self, intent_channel, coordination_channel):
        self.intent = intent_channel
        self.coordination = coordination_channel

    async def coordinate(self):
        intents = await self.intent.read_all()
        conflicts = self.detect_conflicts(intents)

        for conflict in conflicts:
            decision = self.resolve(conflict)  # Policy: priority, timestamp, etc.
            await self.coordination.send(decision)
```

**Acceptance Criteria:**
- [ ] CoordinatorNode reads all intents from intent channel
- [ ] Conflict detection algorithm identifies overlapping actions
- [ ] Resolution policy (priority-based, timestamp-based, or custom)
- [ ] coordination_channel receives decisions
- [ ] Channel implements LastValue reducer (latest decision wins)

**Completion Signal:** Conflicting intents detected, resolved, decision logged to coordination channel

**Reference:** research/ubiquitous-language/external-code-state-coordination.md

---

### R10.4: Execution Channel
```yaml
task_id: R10.4
phase: R10
type: Integration
status: roadmap
```

**The Constraint:**
- **Before:** Actions execute without audit trail
- **After:** Executor node logs all actions to execution channel (immutable audit)

**Observable Truth:** Executed action appears in execution channel with result, timestamp, agent_id

**Witness Outcome:**
- Coordinator approves action
- Executor executes action
- Execution channel receives: `{"agent": "A", "action": "modify_file", "result": "success", "timestamp": ...}`

**What This Unlocks:**
- Complete audit trail of all actions
- Rollback capabilities (future)
- Observability into agent behavior

**Code Pattern:**
```python
# Execution channel logs all actions
class ExecutorNode:
    def __init__(self, coordination_channel, execution_channel):
        self.coordination = coordination_channel
        self.execution = execution_channel

    async def execute(self):
        decision = await self.coordination.read()
        result = await self.apply_action(decision["action"])

        await self.execution.send({
            "agent_id": decision["agent_id"],
            "action": decision["action"],
            "result": result,
            "timestamp": now()
        })
```

**Acceptance Criteria:**
- [ ] ExecutorNode reads from coordination channel
- [ ] Action execution happens
- [ ] execution_channel receives log entry with result
- [ ] Channel implements Topic reducer (all executions retained)
- [ ] Audit trail queryable

**Completion Signal:** Action executed, logged to execution channel with timestamp and result

**Reference:** research/ubiquitous-language/external-code-state-coordination.md

---

### R10.5: Template - agent_coordination
```yaml
task_id: R10.5
phase: R10
type: Feature
status: roadmap
```

**The Constraint:**
- **Before:** No template for 4-channel pattern
- **After:** `lgp create workflow --template agent_coordination` scaffolds pattern

**Observable Truth:** Template creates workflow with 4 channels + 4 nodes (Observer, Agent, Coordinator, Executor)

**Witness Outcome:**
- Command: `lgp create test_agents --template agent_coordination`
- File created: workflows/test_agents.py
- Contains: ObserverNode, AgentNode, CoordinatorNode, ExecutorNode
- Contains: observation_channel, intent_channel, coordination_channel, execution_channel
- Executable immediately

**What This Unlocks:**
- 0-cycle agent coordination builds
- Mental model encoded in template
- Progressive learning (workflow → agent mode)

**Acceptance Criteria:**
- [ ] templates/agent_coordination/workflow.py exists
- [ ] Template header documents 4-channel pattern
- [ ] Anti-patterns listed (concurrent writes, no coordination, etc.)
- [ ] Correct patterns shown (channel coordination, conflict resolution)
- [ ] Reference links to sacred-core/

**Completion Signal:** Template created, lgp create command works, workflow executable

---

## R11: Worker Architecture 🔮

### R11.1: 7-Tool Interface
```yaml
task_id: R11.1
phase: R11
type: Integration
status: roadmap
```

**The Constraint:**
- **Before:** Direct execution couples manager to worker internals
- **After:** Manager communicates via 7-tool interface, worker abstracted

**Observable Truth:** Manager invokes state/pressure/constraints/flow/void/execute/evolve tools, worker responds

**Witness Outcome:**
- Manager calls: `worker.state()` → receives current state
- Manager calls: `worker.pressure()` → receives resource usage
- Manager calls: `worker.execute(action)` → worker applies action
- Worker implements 4-channel graph internally (hidden from manager)

**What This Unlocks:**
- External system integration (Git repos, databases, APIs become "workers")
- Manager doesn't need to know worker implementation
- Worker can be swapped without manager changes
- Uniform interface for all external systems

**The 7 Tools:**
```python
class Worker:
    async def state(self) -> dict:
        """Query current worker state"""

    async def pressure(self) -> dict:
        """Check resource usage (memory, CPU, etc.)"""

    async def constraints(self) -> list:
        """Validate boundaries (what's forbidden)"""

    async def flow(self, context: dict) -> list:
        """Suggest possible actions given context"""

    async def void(self, action: dict) -> dict:
        """Hypothetical what-if (no side effects)"""

    async def execute(self, action: dict) -> dict:
        """Apply action (with side effects)"""

    async def evolve(self, feedback: dict) -> None:
        """Learn from execution results"""
```

**Code Pattern:**
```python
# Manager communicates via 7-tool interface
class Manager:
    def __init__(self, worker: Worker):
        self.worker = worker

    async def coordinate(self):
        # Query state
        state = await self.worker.state()

        # Check constraints
        constraints = await self.worker.constraints()

        # Get suggestions
        actions = await self.worker.flow(state)

        # Simulate first
        result = await self.worker.void(actions[0])

        # If safe, execute
        if self.is_safe(result):
            await self.worker.execute(actions[0])
            await self.worker.evolve({"success": True})
```

**Acceptance Criteria:**
- [ ] Worker interface defined with 7 methods
- [ ] GitWorker implements interface (wraps git operations)
- [ ] DatabaseWorker implements interface (wraps SQL)
- [ ] Manager uses only 7-tool interface (no direct calls)
- [ ] Worker internally uses 4-channel coordination

**Completion Signal:** Manager coordinates GitWorker via 7 tools, git operations succeed

**Reference:** research/ubiquitous-language/worker-architecture.md

---

### R11.2: GitWorker Implementation
```yaml
task_id: R11.2
phase: R11
type: Feature
status: roadmap
```

**The Constraint:**
- **Before:** Direct git commands in workflows
- **After:** GitWorker wraps git, exposed via 7-tool interface

**Observable Truth:** `git_worker.execute({"action": "commit", "message": "..."})` commits changes

**Witness Outcome:**
- Manager: `git_worker.state()` → `{"branch": "main", "uncommitted": 5}`
- Manager: `git_worker.flow(...)` → `[{"action": "commit"}, {"action": "push"}]`
- Manager: `git_worker.execute({"action": "commit"})` → commit happens
- Manager: `git_worker.void({"action": "push"})` → simulates push without executing

**What This Unlocks:**
- Git operations as first-class workflow nodes
- Hypothetical what-if (void tool)
- Constraint checking (can't push with uncommitted changes)

**Acceptance Criteria:**
- [ ] GitWorker implements Worker interface
- [ ] state() returns branch, uncommitted files, remote status
- [ ] constraints() returns git rules (e.g., "no force push to main")
- [ ] execute() wraps git commit, push, pull, checkout
- [ ] void() simulates without side effects

**Completion Signal:** GitWorker executes commit via 7-tool interface, verified

---

### R11.3: DatabaseWorker Implementation
```yaml
task_id: R11.3
phase: R11
type: Feature
status: roadmap
```

**The Constraint:**
- **Before:** Direct SQL in workflows
- **After:** DatabaseWorker wraps database, exposed via 7-tool interface

**Observable Truth:** `db_worker.execute({"action": "insert", "table": "users", "data": {...}})` inserts row

**Witness Outcome:**
- Manager: `db_worker.state()` → `{"connected": true, "table_count": 12}`
- Manager: `db_worker.constraints()` → `["no_drop_tables", "read_only_prod"]`
- Manager: `db_worker.void({"action": "delete"})` → simulates deletion, shows affected rows
- Manager: `db_worker.execute({"action": "insert"})` → actual insertion

**What This Unlocks:**
- Database operations as workflow nodes
- Constraint enforcement (no DROP in production)
- Hypothetical queries (void tool shows results without applying)

**Acceptance Criteria:**
- [ ] DatabaseWorker implements Worker interface
- [ ] state() returns connection status, table list
- [ ] constraints() returns database policies
- [ ] execute() wraps INSERT, UPDATE, DELETE, SELECT
- [ ] void() simulates queries, returns affected rows

**Completion Signal:** DatabaseWorker inserts row via 7-tool interface, verified

---

## R12: Multi-Agent Reactive Orchestration 🔮

### R12.1: Dynamic Agent Spawning
```yaml
task_id: R12.1
phase: R12
type: Feature
status: roadmap
```

**The Constraint:**
- **Before:** Workflow topology fixed at compile time
- **After:** Agents spawn other agents dynamically at runtime

**Observable Truth:** Agent A spawns Agent B mid-execution, both coordinate via channels

**Witness Outcome:**
- Manager agent running
- Manager detects: "Need specialist for task X"
- Manager spawns: SpecialistAgent(task_x)
- SpecialistAgent joins coordination channels
- Both agents coordinate via 4-channel pattern

**What This Unlocks:**
- Adaptive workflows (respond to complexity)
- Specialist agents on demand
- Scalable orchestration (N agents)

**Code Pattern:**
```python
# Dynamic agent spawning
class ManagerAgent:
    async def coordinate(self):
        state = await self.observe()

        if self.needs_specialist(state):
            # Spawn specialist
            specialist = await self.spawn_agent(
                agent_type=SpecialistAgent,
                channels=self.channels  # Share coordination channels
            )

            # Specialist joins coordination
            await specialist.start()
```

**Acceptance Criteria:**
- [ ] ManagerAgent can spawn agents at runtime
- [ ] Spawned agents receive coordination channels
- [ ] Multiple agents coordinate without conflicts
- [ ] Agents can terminate when task complete

**Completion Signal:** Manager spawns specialist, both coordinate, task completes

---

### R12.2: Event-Driven Coordination
```yaml
task_id: R12.2
phase: R12
type: Feature
status: roadmap
```

**The Constraint:**
- **Before:** Polling-based coordination (inefficient)
- **After:** Event-driven coordination (reactive)

**Observable Truth:** External event triggers agent without polling

**Witness Outcome:**
- File system watcher emits event → observation channel
- Agent subscribed to observation channel → receives event <100ms
- Agent generates plan → intent channel
- Coordinator → coordination decision
- No polling loops

**What This Unlocks:**
- Real-time responsiveness
- Reduced resource usage (no polling)
- Scalable to many event sources

**Acceptance Criteria:**
- [ ] Channels support pub/sub pattern
- [ ] Agents subscribe to specific channel topics
- [ ] Events trigger agent execution <100ms
- [ ] No polling loops in codebase

**Completion Signal:** File change triggers agent execution via event, <100ms latency

---

### R12.3: Agent Negotiation Protocol
```yaml
task_id: R12.3
phase: R12
type: Feature
status: roadmap
```

**The Constraint:**
- **Before:** Coordinator resolves all conflicts centrally
- **After:** Agents negotiate directly via coordination channel

**Observable Truth:** Two agents negotiate action order without coordinator intervention

**Witness Outcome:**
- Agent A plans: modify test.py
- Agent B plans: read test.py
- Agent B checks intent channel, sees Agent A's plan
- Agent B negotiates: "I'll wait for you to finish"
- Agent A acknowledges: "Done, you can proceed"
- Coordination channel logs negotiation

**What This Unlocks:**
- Decentralized coordination (no single point of failure)
- Agent autonomy
- Scalable to N agents (no central bottleneck)

**Code Pattern:**
```python
# Agent negotiation
class Agent:
    async def negotiate(self):
        # Check for conflicting intents
        other_intents = await self.intent_channel.read_all()
        conflicts = self.find_conflicts(other_intents, self.my_intent)

        if conflicts:
            # Negotiate directly
            for conflict in conflicts:
                proposal = self.propose_resolution(conflict)
                await self.coordination_channel.send(proposal)

            # Wait for agreement
            agreement = await self.coordination_channel.wait_for_agreement()
```

**Acceptance Criteria:**
- [ ] Agents read intent channel to detect conflicts
- [ ] Agents send proposals to coordination channel
- [ ] Negotiation protocol defined (propose, accept, reject)
- [ ] Agents reach agreement without coordinator

**Completion Signal:** Two agents negotiate action order, coordination channel logs agreement

---

## Implementation Principles (ETERNAL)

### 1. Witness-Based Completion
**Every task must have observable truth that can ONLY exist if task succeeded.**

❌ BAD: "Implementation finished", "Tests pass", "Code reviewed"
✅ GOOD: "External file change detected <100ms and logged to observation channel"

### 2. Constraint-First Thinking
**Every task removes a constraint to unlock emergent capability.**

Pattern: Before (constraint) → After (capability unlocked)

### 3. Minimal Leverage Points
**Code pattern should be the MINIMUM required to make witness observable.**

Focus on: What single change makes the impossible possible?

### 4. Progressive Emergence
**Each phase builds on previous, no skipping.**

R1 → R2 → R3 → ... → R10 → R11 → R12
Cannot implement R11 before R10.

---

## Phase Dependency Graph

```
R1 (CLI) ─┬─→ R3 (Observability)
          │
          ├─→ R4 (Checkpointing) ─→ R9 (PostgreSQL)
          │
          └─→ R6 (Templates)

R2 (API) ─→ R5 (Claude Code)

R6.5 (Config) ─→ R8 (Multi-Provider)

R1-R9 ─→ R10 (4-Channel) ─→ R11 (Worker) ─→ R12 (Multi-Agent)

R7 (Production Mastery) - Optional, no dependencies
```

---

## Task Crystallization

**All R10-R12 tasks now crystallized in tasks/ folder:**

```
tasks/
├── R10.1-observation-channel.md
├── R10.2-intent-channel.md
├── R10.3-coordination-channel.md
├── R10.4-execution-channel.md
├── R10.5-agent-coordination-template.md
├── R11.1-seven-tool-interface.md
├── R11.2-git-worker.md
├── R11.3-database-worker.md
├── R12.1-dynamic-agent-spawning.md
├── R12.2-event-driven-coordination.md
└── R12.3-agent-negotiation.md
```

Each task file follows template structure with:
- The Constraint (Before/After)
- The Witness (Observable truth)
- Acceptance Criteria (measurable)
- Code Pattern (minimal leverage)
- Execution Protocol
- Completion Signal

---

## Truth State

**R1-R9:** Platform delivers workflow orchestration runtime (90% production-ready)
**R10+:** Roadmap crystallized, tasks defined, ready for execution when prioritized
**Sacred-Core:** Knowledge layer complete, mental models encoded, templates aligned

**Next:** When agent coordination layer prioritized, execute R10.1-R10.5 sequentially.
