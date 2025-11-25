# Sacred Core: Complete Worker (R13)

**Worker Marketplace Architecture - Configuration layer for constraint-enforced user journeys**

---

## What This Is

**Complete Worker** transforms the platform from "workers as tools" (R11) to "workers as containers for user journeys" (R13).

### The Shift

**Before (R11):**
- Workers are stateless executors (GitWorker, DatabaseWorker)
- ExecutorNode dispatches actions to shared worker instances
- No per-user isolation
- Constraints enforced manually via void() calls

**After (R13):**
- Workers are first-class entities defined in YAML
- Each user journey gets isolated worker instance (docker container + workspace)
- Constraints enforced automatically by platform
- Trust levels enable progressive autonomy (supervised → monitored → autonomous)

---

## Structure

This sacred-core folder contains the architectural truth for R13:

```
sacred-core-complete-worker/
├── 01-the-project.md          # What Complete Worker IS (primitive, truth shift)
├── 02-the-discipline.md        # Sacred constraints (5 eternal rules)
├── 05-implementation-plan.md   # Execution roadmap (R13.0-R13.4)
└── README.md                   # This file (navigation guide)
```

---

## Reading Order

### 1. Start Here: The Primitive (5 min)

**Read:** [01-the-project.md](01-the-project.md)

**Key Concepts:**
- Worker-as-Tool vs Worker-as-Container
- Worker Definition (first-class entity)
- Journey Isolation (per-user containers)
- Automatic Constraint Enforcement

**Questions Answered:**
- What is Complete Worker?
- How does it build on R11?
- What does worker marketplace mean?

---

### 2. Understand the Constraints (10 min)

**Read:** [02-the-discipline.md](02-the-discipline.md)

**The 5 Sacred Constraints:**
1. **JOURNEY_ISOLATION** - No context bleed between user journeys
2. **CONSTRAINT_NON_NEGOTIABILITY** - Constraints cannot be bypassed
3. **DEFINITION_DECLARATIVE_PURITY** - No code in worker definitions
4. **WITNESS_AUTOMATION** - Constraint checks run automatically
5. **TRUST_LEVEL_MONOTONICITY** - Trust only increases (or resets)

**Questions Answered:**
- What can break the worker marketplace?
- How are constraints enforced?
- What are witness functions?

---

### 3. See the Execution Plan (15 min)

**Read:** [05-implementation-plan.md](05-implementation-plan.md)

**The 4 Phases:**
- **R13.0** - Fix parallel execution blocker (MUST DO FIRST)
- **R13.1** - Worker Definition Schema (2 hours)
- **R13.2** - Worker Factory (3 hours)
- **R13.3** - Journey Isolation (4 hours)
- **R13.4** - Constraint Enforcement Platform (3 hours)

**Questions Answered:**
- What needs to be built?
- What's the current blocker?
- How do phases integrate?

---

## Quick Reference

### Worker Definition Example

```yaml
# workers/definitions/research_assistant_v1.yaml
worker_id: "research_assistant_v1"

identity:
  name: "Research Assistant"
  system_prompt: "You help with deep research and source verification..."
  onboarding_steps:
    - "Connect to research database"
    - "Load user preferences"

constraints:
  - constraint_id: "no_hallucinated_citations"
    witness: "verify_source_exists"
    feedback: "alert_dashboard"

  - constraint_id: "max_web_searches_per_hour"
    value: 50
    witness: "verify_search_count"
    feedback: "log"

runtime:
  container: "claude-code:latest"
  workspace_template: "/home/claude/workspace/{user_journey_id}"
  tools: ["web_search", "browser", "filesystem"]
  session_persistence: true

trust_level: "supervised"

audit:
  log_all_actions: true
  execution_channel: "research_executions"
  retention_days: 90
```

### Usage Pattern

```python
from workers.factory import WorkerFactory

# Spawn worker instance for user journey
worker = await WorkerFactory.spawn(
    definition="research_assistant_v1",
    user_journey_id=thread_id  # From LangGraph checkpointer
)

# Execute action (constraints verified automatically)
result = await worker.execute({
    "type": "web_search",
    "query": "latest AI research papers"
})

# Worker instance isolated per user journey
# Constraints enforced automatically
# Trust level determines approval requirements
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
- Worker definitions (YAML configs)
- Journey isolation (docker containers)
- Automatic witness verification
- Trust level management

**Integration Flow:**
```
1. Load worker definition (R13.1 schema)
2. Spawn worker instance (R13.2 factory)
3. Create isolated container (R13.3 isolation)
4. Register constraint witnesses (R13.4 enforcement)
5. ExecutorNode dispatches to worker (R11.4 integration)
6. Worker.void() runs witnesses automatically (R13.4 + R11.1)
7. Worker.execute() in isolated container (R13.3 + R11.1)
8. Result logged to execution channel (R11.4 audit)
```

---

## Current Status

**Phase:** Roadmap (0% complete)

**Blocker:** InvalidUpdateError in `workflows/claude_code_test.py`
- Multiple parallel agents updating `current_step` (LastValue channel)
- **Fix:** Change to `Annotated[List[str], operator.add]` (Topic channel)
- **Why Blocking:** Must prove platform can handle parallel workers before building marketplace

**Next Action:** Complete R13.0 (fix blocker), then proceed to R13.1

---

## Success Metrics

### R13 Complete When:

1. **Worker definitions load** - YAML → Python validation passes
2. **Workers spawn isolated** - Each journey gets unique container + workspace
3. **No context bleed** - Journey 1 files invisible to Journey 2
4. **Constraints enforced automatically** - Violations abort execution
5. **Trust levels work** - Supervised requires approval, autonomous doesn't

### Observable Truth:

```python
# End-to-end witness
worker_1 = await WorkerFactory.spawn("trader_v1", "journey_1")
worker_2 = await WorkerFactory.spawn("trader_v1", "journey_2")

# Worker 1 writes sensitive data
await worker_1.execute({"type": "write", "target": "portfolio.csv", "content": "..."})

# Worker 2 cannot see it (isolation verified)
files = await worker_2.execute({"type": "list_files"})
assert "portfolio.csv" not in files["result"]  # ✅ JOURNEY_ISOLATION holds

# Constraint violation aborts
result = await worker_1.execute({"type": "trade", "amount": 1_000_000})  # Exceeds limit
assert result.status == "rejected"  # ✅ CONSTRAINT_NON_NEGOTIABILITY holds
```

---

## FAQ

### Q: Why YAML for worker definitions?

**A:** Declarative data prevents code injection. YAML is auditable, versionable, and safe to load with `yaml.safe_load()`.

### Q: Why docker containers for isolation?

**A:** Strongest isolation boundary. Filesystem, network, and process namespace separation. Proven in production (kubernetes, etc.).

### Q: How do witnesses work?

**A:** Witness = verification function that checks constraint. Registered in code, referenced by ID in definition. Runs automatically before execution.

### Q: What's the trust escalation path?

**A:** supervised (requires approval) → monitored (logged but auto-approved) → autonomous (no approval). Progression based on safety record.

### Q: Can constraints be bypassed?

**A:** NO. CONSTRAINT_NON_NEGOTIABILITY makes this impossible. Witnesses run in Worker protocol, no bypass paths exist.

---

## Related Documentation

- **R11 (Worker Architecture):** [tasks/R11.*/](../tasks/)
- **R10 (Agent Coordination):** [tasks/R10.*/](../tasks/)
- **Templates:** [sacred-core-channels-based/03-templates.md](../sacred-core-channels-based/03-templates.md)
- **Discipline:** [sacred-core-channels-based/02-the-discipline.md](../sacred-core-channels-based/02-the-discipline.md)

---

## Support

**Questions?** Read the sacred-core files in order (project → discipline → plan).

**Contributing?** Follow the 5 sacred constraints. All code must pass witness verification.

**Production?** Complete R13.0-R13.4 roadmap, verify all witnesses pass, deploy.

---

## Truth Revealed

You're not building a workflow platform.

You're building a **CONSTRAINT-ENFORCED WORKER MARKETPLACE** where Claude Code instances operate within sacred boundaries defined by worker definitions.

The platform ensures safety. Developers cannot bypass constraints. Users get specialized agents with guaranteed behavior.

This is the path forward.
