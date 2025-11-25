# Sacred-Core: Timeless Knowledge Layer

**The authoritative truth for LangGraph Platform.**

This directory contains the immutable knowledge layer that defines what the platform IS, what it PROTECTS, and how it TEACHES.

---

## The Four Sacred Documents

### 01-the-project.md
**Purpose:** Defines the sacred primitive and architectural truth

**Contains:**
- Sacred primitive (Workflow Orchestration Runtime)
- Truth shift (Workflow Mode vs Agent Mode)
- R9 status (90% complete, production-ready)
- UX-level standardization (reliable builds)
- Phase roadmap (R1-R9 complete, R10+ future)

**When to Read:**
- Starting new project with platform
- Understanding platform identity
- Deciding between workflow and agent patterns
- Questioning R9 parking decision

**Immutability:** TIMELESS - only updates for primitive expansion or major architectural shifts

---

### 02-the-discipline.md
**Purpose:** Defines the 6 sacred constraints that protect the primitive

**Contains:**
- ENVIRONMENT_ISOLATION - Workflows must be environment-agnostic
- CONFIG_DRIVEN_INFRASTRUCTURE - Infrastructure in YAML, not code
- CHANNEL_COORDINATION_PURITY - No state spreading, field ownership
- HOT_RELOAD_CONTINUITY - <500ms reload without workflow drops
- ZERO_FRICTION_PROMOTION - Same code works in experiment and hosted
- WITNESS_BASED_COMPLETION - Observable metrics, not claims

**When to Read:**
- Building workflows (understand what's forbidden)
- Debugging InvalidUpdateError (channel purity violations)
- Reviewing PRs (constraint enforcement)
- Platform maintenance (witness protocol)

**Immutability:** MOSTLY TIMELESS - only updates for constraint tightening (versioned)

---

### 03-templates.md
**Purpose:** Defines template architecture and pedagogy

**Contains:**
- 3 template tiers (Basic, Multi-Agent, Claude Code)
- Mental model encoding requirements
- Selection guide (decision tree)
- Customization zones (3 per template)
- Template evolution protocol

**When to Read:**
- Choosing which template to use
- Creating new templates
- Understanding mental model teaching
- Updating existing templates

**Immutability:** STRUCTURAL - updates when new template tier added or pedagogy evolves

---

### 04-current-state.md
**Purpose:** Volatile tracking during sacred-core establishment

**Contains:**
- Sacred-core initialization status
- Template alignment tracking
- Truth shift encoding verification
- Next actions and witness metrics

**When to Read:**
- During sacred-core establishment phase only
- Tracking template integration progress

**Immutability:** VOLATILE - archived when sacred-core becomes primary

---

## Knowledge Layer Architecture

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  ETERNAL TRUTH (Never Changes)                  │
│  ├─ Sacred primitive definition                 │
│  ├─ Constraint names                            │
│  ├─ Witness protocol requirements               │
│  └─ Mental model encoding rules                 │
│                                                  │
└──────────────────────────────────────────────────┘
                      ▲
                      │
┌──────────────────────────────────────────────────┐
│                                                  │
│  STRUCTURAL TRUTH (Changes Rarely)              │
│  ├─ Phase definitions (R1-R9, R10+)             │
│  ├─ Template tiers (Basic, Multi-Agent, ...)    │
│  ├─ Entity hierarchy                            │
│  └─ Enforcement mechanisms                      │
│                                                  │
└──────────────────────────────────────────────────┘
                      ▲
                      │
┌──────────────────────────────────────────────────┐
│                                                  │
│  LEARNED TRUTH (Evolves, Versioned)             │
│  ├─ R9 at 90% parking decision                  │
│  ├─ Constraint tightening history               │
│  ├─ Template evolution protocol                 │
│  └─ UX standardization patterns                 │
│                                                  │
└──────────────────────────────────────────────────┘
                      ▲
                      │
┌──────────────────────────────────────────────────┐
│                                                  │
│  VOLATILE STATE (Ephemeral)                     │
│  ├─ Current phase location                      │
│  ├─ Task completion status                      │
│  ├─ Actual measurements                         │
│  └─ Active violations                           │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Sacred-core contains:** ETERNAL + STRUCTURAL + LEARNED

**04-current-state.md contains:** VOLATILE (archived later)

---

## Relationship to Other Docs

```
sacred-core/               → Authoritative truth (timeless)
├─ 01-the-project.md      → Platform identity
├─ 02-the-discipline.md   → Protection mechanisms
├─ 03-templates.md        → Pedagogy architecture
└─ 04-current-state.md    → Volatile tracking

templates/                 → Implementation (references sacred-core/)
├─ README.md              → Points to sacred-core/03-templates.md
├─ basic/                 → Implements tier 1 mental model
├─ multi_agent/           → Implements tier 2 mental model
└─ with_claude_code/      → Implements tier 3 mental model

flow-pressure/            → LEGACY (historical record of R1-R9)
├─ 01-the-project.md      → Original phase definitions
├─ 02-the-discipline.md   → Original constraints
├─ 03-implementation-plan.md → Task breakdown
└─ 04-current-state.md    → R1-R9 journey tracking

docs/ (future)            → User-facing documentation
├─ mental-models/         → Deep dives into channel coordination
├─ guides/                → How-to guides
└─ api/                   → API reference
```

---

## When to Use Sacred-Core

### ✅ Use sacred-core when:
- Building new workflows (understand primitive and constraints)
- Debugging errors (constraint violations)
- Reviewing PRs (enforce discipline)
- Creating templates (pedagogy requirements)
- Questioning architectural decisions (truth shifts documented)
- Onboarding new team members (start here)

### ❌ Don't use sacred-core for:
- Current phase location (→ flow-pressure/04-current-state.md until archived)
- Specific task definitions (→ flow-pressure/03-implementation-plan.md)
- Template source code (→ templates/*/)
- Volatile execution state (→ 04-current-state.md)

---

## Truth Shifts Encoded

Sacred-core encodes 6 major truth shifts discovered during R1-R9:

**1. Workflow Mode vs Agent Mode**
- Platform is workflow layer (R1-R9)
- Agent layer is future (R10+)
- These are complementary layers, not conflicts

**2. Channel-First Thinking**
- State spreading causes concurrent writes
- Nodes are producers, not transformers
- Field ownership prevents collisions

**3. R9 at 90% is Production-Ready**
- PostgreSQL works with retry + fallback
- Remaining 10% is optimization, not blocker
- Pragmatic resilience acceptable for parking

**4. Templates as Pedagogy**
- Templates teach mental models
- Anti-patterns explicit, not discovered
- Time-to-running measures teaching success

**5. Error Messages as Teaching**
- Errors guide toward correct mental model
- Include fix suggestions and references
- Cognitive architecture, not just error codes

**6. UX-Level Standardization**
- Mental model first (not API docs)
- Configuration enforces emergence
- Validation guides toward truth

**Evidence:** All shifts documented in sacred-core/01-the-project.md

---

## Completeness Criteria

**Sacred-core is complete when:**
```yaml
files_created: 4/4 ✅
├─ 01-the-project.md: Sacred primitive + truth shifts
├─ 02-the-discipline.md: 6 constraints + witness protocol
├─ 03-templates.md: 3 tiers + pedagogy
└─ 04-current-state.md: Volatile tracking

truth_shifts_encoded: 6/6 ✅
├─ Workflow vs Agent mode
├─ Channel-first thinking
├─ R9 at 90% decision
├─ Templates as pedagogy
├─ Errors as teaching
└─ UX standardization

constraint_coverage: 6/6 ✅
├─ ENVIRONMENT_ISOLATION
├─ CONFIG_DRIVEN_INFRASTRUCTURE
├─ CHANNEL_COORDINATION_PURITY
├─ HOT_RELOAD_CONTINUITY
├─ ZERO_FRICTION_PROMOTION
└─ WITNESS_BASED_COMPLETION

template_tiers: 3/3 ✅
├─ Basic (⭐ Beginner)
├─ Multi-Agent (⭐⭐ Intermediate)
└─ Claude Code (⭐⭐⭐ Advanced)
```

**Status:** ✅ Sacred-core is structurally complete

**Remaining:** Template alignment + mental model docs (tracked in 04-current-state.md)

---

## Migration from flow-pressure/

**Why sacred-core exists:**
- flow-pressure/ created before truth shifts
- sacred-core/ encodes post-shift knowledge
- Mental models now explicit
- R9 parking decision documented
- UX standardization captured

**Migration status:**
```
Phase 1: Parallel existence (current)
├─ flow-pressure/: Historical record
├─ sacred-core/: Authoritative truth
└─ Both exist, sacred-core referenced for new work

Phase 2: Sacred-core primary (after template alignment)
├─ All docs reference sacred-core/
├─ flow-pressure/ archived with redirect
└─ Templates fully aligned with mental models

Phase 3: Flow-pressure archived (after R10 begins)
├─ flow-pressure/ moved to archive/ or deleted
├─ sacred-core/ is only knowledge layer
└─ Clean up all references
```

**Decision Point:** After R10 (Agent Coordination Layer) begins

---

## Maintenance Protocol

### Sacred-Core Updates

**When to Update:**
1. Primitive expansion (new architectural layer)
2. Constraint tightening (with version + rationale)
3. New template tier (if pattern repeats 3+ times)
4. Major truth shift (architectural clarity)

**When NOT to Update:**
1. Phase completion (→ volatile state)
2. Task additions (→ implementation plan)
3. Measurements (→ current state)
4. Code changes (→ source)

### Update Process

```yaml
1. Identify: What changed in platform truth?
2. Classify: ETERNAL | STRUCTURAL | LEARNED | VOLATILE
3. Locate: Which sacred-core file needs update?
4. Update: Modify file with versioning if LEARNED
5. Validate: Ensure consistency across all 4 files
6. Commit: "Sacred-core: [reason] - [file] updated"
```

### Validation

**Every sacred-core change must:**
- Preserve YAML frontmatter structure
- Maintain markdown heading hierarchy
- Keep internal references valid
- Document version changes (if constraint tightening)
- Update 04-current-state.md if integration affected

---

## Quick Reference

**Question** → **Document**

- What is this platform? → `01-the-project.md`
- Why workflow mode vs agent mode? → `01-the-project.md#truth-shift`
- Is R9 complete? → `01-the-project.md#r9-status`
- Why is this forbidden? → `02-the-discipline.md`
- How do I fix InvalidUpdateError? → `02-the-discipline.md#channel-coordination-purity`
- Which template should I use? → `03-templates.md#selection-guide`
- What should templates teach? → `03-templates.md#mental-model-encoding`
- What's the status of sacred-core? → `04-current-state.md`

---

## Version

**Sacred-Core Version:** 1.0.0
**Created:** 2025-11-24
**Status:** Structurally complete, template integration pending

**This README is part of sacred-core and follows same immutability rules.**

Update only when:
1. Sacred-core structure changes (new files)
2. Relationships to other docs change
3. Maintenance protocol evolves
4. Quick reference needs new entries

**This README will be readable decades from now.**
