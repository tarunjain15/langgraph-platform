# LangGraph Platform - R10+ Task Files

**Crystallized execution tasks for Agent Coordination Layer (R10-R12).**

Each task follows witness-based completion protocol from `/templates/00-task-template.md`.

---

## Task Structure

```
tasks/
├── R10.1-observation-channel.md      # External state mirroring
├── R10.2-intent-channel.md           # Agent action planning
├── R10.3-coordination-channel.md     # Conflict resolution
├── R10.4-execution-channel.md        # Action execution + audit
├── R10.5-agent-coordination-template.md  # Template for 4-channel pattern
├── R11.1-seven-tool-interface.md     # Worker abstraction layer
├── R11.2-git-worker.md                # Git operations as Worker
├── R11.3-database-worker.md           # Database operations as Worker
├── R12.1-dynamic-agent-spawning.md    # Runtime agent creation
├── R12.2-event-driven-coordination.md # Pub/sub reactive agents
├── R12.3-agent-negotiation.md         # Decentralized conflict resolution
└── README.md                          # This file
```

---

## Execution Order

### Phase R10: 4-Channel Coordination (Sequential)
1. **R10.1** - Observation Channel (foundation - mirrors external truth)
2. **R10.2** - Intent Channel (agents plan actions)
3. **R10.3** - Coordination Channel (resolve conflicts)
4. **R10.4** - Execution Channel (apply actions + audit)
5. **R10.5** - Agent Coordination Template (pedagogy)

**Dependency:** Must complete R10.1 → R10.2 → R10.3 → R10.4 in order. R10.5 can be done anytime after R10.4.

---

### Phase R11: Worker Architecture (Sequential)
1. **R11.1** - 7-Tool Interface (state/pressure/constraints/flow/void/execute/evolve)
2. **R11.2** - GitWorker Implementation (git operations)
3. **R11.3** - DatabaseWorker Implementation (SQL operations)

**Dependency:** R11.1 must complete first. R11.2 and R11.3 can be parallel.

**Prerequisite:** R10 complete (Workers internally use 4-channel coordination)

---

### Phase R12: Multi-Agent Reactive Orchestration (Parallel possible)
1. **R12.1** - Dynamic Agent Spawning (runtime agent creation)
2. **R12.2** - Event-Driven Coordination (pub/sub pattern)
3. **R12.3** - Agent Negotiation Protocol (decentralized conflict resolution)

**Dependency:** All R12 tasks depend on R10 complete. R12 tasks can be done in any order or parallel.

---

## Task Template Structure

Each task file contains:

### 1. The Constraint
- **Before:** What blocks this capability
- **After:** What emerges when constraint removed

### 2. The Witness
- **Observable Truth:** What can ONLY exist if task succeeded
- **Why This Witness:** Explanation of uniqueness

### 3. Acceptance Criteria
- Measurable conditions (checkbox list)
- Cannot exist without (impossibility → automatic → measurable)

### 4. Code Pattern
- Minimal code to unlock the witness
- NOT full implementation (leverage point only)

### 5. Execution Protocol
- Prerequisites
- Execution steps
- Verification steps

### 6. Completion Signal
- Single sentence proof
- Evidence artifacts required
- State transition (before → after)

### 7. Constraint Compliance
- CONTEXT_PRESERVATION
- CONSTRAINT_INHERITANCE
- TRACE_REQUIRED
- RESOURCE_STEWARDSHIP
- RESIDUE_FREE

### 8. Notes
- Integration points
- Common pitfalls
- Key insights

---

## Witness-Based Completion

**Every task must have observable truth that can ONLY exist if task succeeded.**

❌ **BAD Witnesses:**
- "Implementation finished"
- "Tests pass"
- "Code reviewed"

✅ **GOOD Witnesses:**
- "External file change detected <100ms and logged to observation channel"
- "Agent plan written to intent channel WITHOUT execution side effect"
- "Two conflicting intents resolved, coordination channel contains single approved agent"

**Why:** Good witnesses are impossible before, automatic after, and objectively measurable.

---

## Truth State

**R1-R9:** Platform delivers workflow orchestration runtime (90% production-ready)
**R10-R12:** Agent coordination layer tasks crystallized, ready for execution when prioritized

**Next:** When agent coordination prioritized, execute R10.1 → R10.2 → R10.3 → R10.4 → R10.5 sequentially.

---

## Reference

- **Implementation Plan:** `/sacred-core/05-implementation-plan.md`
- **Task Template:** `/templates/00-task-template.md` (from my-langgraph project)
- **Mental Models:** `/sacred-core/01-the-project.md`
- **Sacred Constraints:** `/sacred-core/02-the-discipline.md`
