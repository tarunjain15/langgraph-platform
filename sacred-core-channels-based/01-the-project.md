# LangGraph Platform: Project Truth Template

**Meta:** This template encodes architectural truth shifts discovered through building R1-R9.

## Sacred Primitive

```
LangGraph Platform = Workflow Orchestration Runtime
                   + Environment Isolation (experiment | hosted)
                   + Config-Driven Infrastructure
                   + Progressive Capability Emergence
```

**What This Platform IS:**
- Workflow execution engine for LangGraph graphs
- Runtime that injects infrastructure (checkpointing, observability, hot reload)
- Multi-provider agent orchestration (Claude Code, Ollama, future providers)
- Environment-isolated development → production promotion (zero code changes)

**What This Platform IS NOT:**
- LangGraph library replacement (it *uses* LangGraph)
- Full agent coordination system (that's R10+ future work)
- Workflow builder UI (code-first by design)
- General-purpose Python framework

---

## The Truth Shift: Workflow Mode vs Agent Mode

### Platform Current State (R1-R9): **Workflow Mode**
```
Workflow Mode = Sequential execution
              + Known steps defined upfront
              + Coordinator orchestrates order
              + Infrastructure injected by runtime
```

**Characteristics:**
- State is TypedDict schema (fields declared)
- Nodes are Python async functions (return dict updates)
- Edges define execution order (A → B → C → END)
- Graph compiled once, executed many times
- Observability and checkpointing injected transparently

**Mental Model:**
```python
class WorkflowState(TypedDict):
    input: str
    result: str

async def process(state: WorkflowState) -> dict:
    # ✅ Return only what this node produces
    return {"result": f"Processed: {state['input']}"}

    # ❌ ANTI-PATTERN: Don't spread state
    # return {**state, "result": "..."}  # Causes concurrent write errors

workflow = StateGraph(WorkflowState)
workflow.add_node("process", process)
workflow.add_edge(START, "process")
workflow.add_edge("process", END)
```

**Key Learning:** Think in channels (coordination primitives), not sequential functions.

### Future State (R10+): **Agent Mode**
```
Agent Mode = Concurrent execution
           + Reactive actors responding to events
           + 4-channel coordination pattern
           + Worker architecture
```

**Characteristics (Not Yet Implemented):**
- Observation channels (mirror external truth)
- Intent channels (agent plans)
- Coordination channels (conflict resolution)
- Execution channels (audit log)
- Worker abstraction with 7-tool interface

**Why Not Built Yet:**
Platform delivers workflow layer first. Agent coordination layer (R10+) builds on top when needed.

---

## R9 Status: 90% Complete (Production-Ready with Pragmatic Resilience)

### What Works (✅)
```yaml
workflow_runtime: All phases R1-R9 operational
environment_isolation: experiment vs hosted mode working
multi_provider: Claude Code + Ollama integration
checkpointing: SQLite (single-server) + PostgreSQL (multi-server)
observability: Langfuse tracing with cost tracking
hot_reload: <500ms reload latency in experiment mode
api_hosting: FastAPI server with auth + sessions
templates: 3 progressive templates (basic, multi_agent, with_claude_code)
configuration: YAML-based config with env var substitution
resilience: 3-attempt retry + graceful SQLite fallback
```

### What's Missing (Remaining 10%)
```yaml
postgres_optimizations:
  - Connection pool config not wired (yaml fields exist, not used)
  - No observability metrics (connection attempts, fallback events)
  - No circuit breaker (retries on every invocation)

template_enhancements:
  - Error message standardization not complete
  - Mental model documentation needs ubiquitous-language integration
  - Template selection guidance could be more explicit
```

### Parking Decision
**Accept R9 at 90%** - Missing pieces are optimizations, not blockers.

**Rationale:**
- PostgreSQL works with retry logic + SQLite fallback
- Platform is production-ready for single-server and multi-server deployment
- Remaining gaps don't block user value delivery
- Optimization path documented in `research/checkpoint-mastery/` for future needs

---

## UX-Level Standardization (The Art of Reliable Builds)

### 1. Error Messages Follow Cognitive Architecture

**Principle:** Errors should guide toward truth, not just state failure.

**Pattern:**
```python
# ❌ BAD: Technical error dump
raise InvalidUpdateError("At key 'researcher_output': concurrent update detected")

# ✅ GOOD: Cognitive guidance
raise InvalidUpdateError(
    "Concurrent write detected on 'researcher_output'.\n"
    "Cause: Multiple nodes writing same field simultaneously.\n"
    "Fix: Remove {**state} spread, return only fields this node produces.\n"
    "See: Mental model docs at templates/README.md#channel-coordination"
)
```

**Why:** Errors are teaching moments. Guide users toward channel-first thinking.

### 2. Templates Teach Mental Models

**Principle:** Templates should crystallize architecture, not just provide boilerplate.

**Current Templates:**
```
basic/          - Single-node pattern (⭐ Beginner)
multi_agent/    - Sequential 3-agent collaboration (⭐⭐ Intermediate)
with_claude_code/ - Stateful agents with session continuity (⭐⭐⭐ Advanced)
```

**Missing Template (R10+):**
```
agent_coordination/ - 4-channel reactive agents (⭐⭐⭐⭐ Expert)
```

**Each Template Must:**
1. Include inline `← CUSTOMIZE` markers
2. Document mental model in header comments
3. Show anti-patterns as commented warnings
4. Reference canonical knowledge (ubiquitous-language/)

**Example Header:**
```python
"""
Template: Multi-Agent Collaboration (Sequential Workflow Mode)

Mental Model:
  - State = TypedDict schema (all fields declared upfront)
  - Nodes = Producers (return only owned fields)
  - Edges = Coordination (define execution order)
  - Channels = Implicit (LastValue semantics)

Anti-Patterns:
  - ❌ Spreading state: return {**state, "field": value}
  - ❌ Concurrent writes: Multiple nodes writing same field
  - ❌ Sequential thinking: "Pass data through like functions"

Correct Pattern:
  - ✅ Return only what node produces: return {"field": value}
  - ✅ Let LangGraph coordinate via channels
  - ✅ Trust the runtime for ordering
"""
```

### 3. Configuration Follows Emergence Principle

**Principle:** Capabilities emerge from config, workflows remain environment-agnostic.

**Pattern:**
```yaml
# config/experiment.yaml
checkpointer:
  type: sqlite
  path: ./checkpoints/experiment.sqlite

observability:
  enabled: false  # Console logging only

# config/hosted.yaml
checkpointer:
  type: postgresql
  url: ${DATABASE_URL}
  pool_size: 20

observability:
  enabled: true
  provider: langfuse
```

**Workflow Code (Environment-Agnostic):**
```python
# ✅ Workflow never mentions environment
def my_workflow(state):
    # Pure logic, no infrastructure awareness
    return {"result": process(state)}

# Runtime handles:
# - lgp run → experiment.yaml → SQLite + console
# - lgp serve → hosted.yaml → PostgreSQL + Langfuse
```

### 4. Mental Model Documentation

**Principle:** Speed comes from thinking in primitives, not memorizing APIs.

**Required Documentation:**
1. **Channel Coordination Mechanics** (from ubiquitous-language/)
   - LastValue vs Topic vs BinaryOperatorAggregate
   - versions_seen coordination
   - BSP super-step execution

2. **State Design Patterns**
   - Field ownership (which node owns which field)
   - Annotation for multi-writer fields (Annotated[list, add])
   - Avoiding echo-writes ({**state} anti-pattern)

3. **Common Error Patterns**
   - InvalidUpdateError: Multiple writers → solution
   - TypeError: Type mismatch → annotation fix
   - Concurrent execution → inject_before constraint

**Location:** `docs/mental-models/` (to be created)

**Truth:** The 6 debugging cycles we experienced would have been 0 cycles with mental model knowledge.

### 5. Validation and Feedback Loops

**Principle:** System should guide toward truth through witness-based validation.

**Validation Layers:**

**Layer 1: Schema Validation (Type Safety)**
```python
# Validate state schema matches TypedDict
validator.check_state_schema(workflow)
# Catches: Missing fields, type mismatches
```

**Layer 2: Channel Validation (Coordination Safety)**
```python
# Validate no concurrent writes
validator.check_channel_conflicts(workflow)
# Catches: Multiple nodes writing same field without annotation
```

**Layer 3: Flow Validation (Topology Safety)**
```python
# Validate graph topology
validator.check_execution_order(workflow)
# Catches: Circular dependencies, unreachable nodes
```

**Witness Protocol:**
```yaml
validation_coverage: 100% (every workflow validated before execution)
validation_latency: <100ms (non-blocking)
validation_feedback: Actionable guidance (not just "invalid")
```

**Implementation Status:** ❌ Not yet implemented (R10 candidate)

---

## Roadmap: From Workflow Layer to Agent Layer

### Completed (R1-R9): Workflow Orchestration Runtime
```
✅ R1: CLI Runtime (experiment mode)
✅ R2: API Runtime (hosted mode)
✅ R3: Observability (Langfuse)
✅ R4: Checkpointing (SQLite)
✅ R5: Claude Code Nodes (stateful agents)
✅ R6: Templates (rapid start)
✅ R6.5: Configuration Infrastructure
✅ R8: Multi-Provider (Ollama integration)
✅ R9: PostgreSQL (multi-server deployment)
```

### Optional (Deferred): Production Automation
```
🟡 R7: Production Mastery (auto-scaling, anomaly detection, self-healing)
    - Can be done manually for now
    - Not blocking core platform value
```

### Future (R10+): Agent Coordination Layer
```
🔮 R10: 4-Channel Coordination (Observer → Agent → Coordinator → Executor)
🔮 R11: Worker Architecture (7-tool interface for external systems)
🔮 R12: Multi-Agent Reactive Orchestration (concurrent agents, event-driven)
```

**Truth:** Platform is workflow layer *preparing substrate* for agent layer.

---

## Integration with Coded Systems

**Relationship:**
```
langgraph-platform (R1-R9) = Workflow runtime
research/coded-systems/    = MCP tool factory primitive
```

**Coded Systems is NOT part of langgraph-platform.**

**Why Both Exist:**
- `langgraph-platform`: Workflow orchestration for LLM pipelines
- `coded-systems`: Conversational tool negotiation with graduated permissions

**Future Integration (Possible R10+):**
Platform could host coded-systems tools as orchestration layer:
```
Platform Runtime
└── Workflow Orchestration (Current: R1-R9)
    └── Agent Coordination (Future: R10+)
        └── Tool Factory (Potential: coded-systems integration)
```

**Current Status:** Separate concerns, complementary primitives.

---

## Success Metrics (Targets vs Actuals)

### Experimentation Velocity
```yaml
target: idea_to_running_workflow <5 minutes
actual: ✅ <1 minute (workflow executes in <1s)

target: hot_reload_cycle <2 seconds
actual: ✅ <500ms (measured in development)

target: template_to_custom <10 minutes
actual: ✅ <5 minutes (inline customization guides)
```

### Hosting Simplicity
```yaml
target: commands_to_deploy = 1
actual: ✅ 1 (lgp serve <workflow>)

target: code_changes_for_hosting = 0
actual: ✅ 0 (same file works in both modes)

target: api_response_time <500ms
actual: ✅ 2.04ms (POST /workflows/{name}/invoke)
```

### Cost Efficiency
```yaml
claude_code_workflows:
  cost_model: fixed ($20/month Claude Pro subscription)
  cost_per_run: ~$0.05

ollama_workflows:
  cost_model: self-hosted ($0/month)
  cost_per_run: $0.00
  savings: 100% for development/prototyping
```

---

## The Three Architectural Layers

```
┌─────────────────────────────────────────┐
│   Application Layer                    │
│   (Your Workflows)                     │
│   - Business logic                     │
│   - Agent collaboration                │
│   - Domain-specific state              │
└─────────────────────────────────────────┘
              ▲
              │ Uses
              ▼
┌─────────────────────────────────────────┐
│   Platform Layer (R1-R9)               │
│   (LangGraph Platform Runtime)         │
│   - Environment isolation              │
│   - Infrastructure injection           │
│   - Multi-provider orchestration       │
│   - Checkpointing + Observability      │
└─────────────────────────────────────────┘
              ▲
              │ Built On
              ▼
┌─────────────────────────────────────────┐
│   Primitive Layer                      │
│   (LangGraph Library)                  │
│   - StateGraph, Channels, Nodes        │
│   - BSP execution (Pregel algorithm)   │
│   - versions_seen coordination         │
│   - Checkpointer interface             │
└─────────────────────────────────────────┘
```

**Platform Role:** Orchestration runtime *between* application and primitive layers.

---

## Quick Start (For New Projects)

### 1. Choose Template Based on Complexity

```bash
# Simple data pipeline
lgp create my_pipeline --template basic

# Multi-agent collaboration (sequential)
lgp create research_workflow --template multi_agent

# Stateful agents with Claude Code
lgp create advanced_workflow --template with_claude_code
```

### 2. Understand Mental Model BEFORE Coding

**Read First:**
- `templates/README.md` - Template customization guide
- Template header comments - Mental model for chosen pattern
- `docs/mental-models/` (when created) - Channel coordination

**Key Concepts:**
- State = TypedDict (not dict to pass around)
- Nodes = Producers (not transformers)
- Channels = Coordination (not variables)
- Avoid {**state} spread (causes concurrent writes)

### 3. Experiment Locally

```bash
# Hot reload during development
lgp run workflows/my_pipeline.py --watch

# Verify in experiment mode first
# Infrastructure: SQLite + console logging
```

### 4. Test Hosted Mode

```bash
# Serve as API
lgp serve workflows/my_pipeline.py

# Hit endpoints
curl -X POST http://localhost:8000/workflows/my_pipeline/invoke \
  -H "Authorization: Bearer dev-key-12345" \
  -d '{"input": "test"}'
```

### 5. Deploy to Production

```bash
# Set production config
export DATABASE_URL="postgresql://..."  # PostgreSQL for multi-server
export LANGFUSE_PUBLIC_KEY="..."       # Langfuse for observability

# Serve with hosted config
lgp serve workflows/my_pipeline.py
# Infrastructure: PostgreSQL + Langfuse (automatic)
```

**Truth:** Zero code changes between experiment and production.

---

## Knowledge Layer Compliance

**This template contains:**
- ✅ Sacred primitive (what the platform IS)
- ✅ Truth shift (workflow mode vs agent mode)
- ✅ R9 status (90% complete, parking decision)
- ✅ UX-level standardization (reliable builds)
- ✅ Architectural layers (platform position)
- ✅ Quick start (mental model first)

**This template excludes:**
- ❌ Volatile execution state (→ flow-pressure/04-current-state.md)
- ❌ Task completion tracking (→ Linear, Langfuse)
- ❌ Research vertical details (→ research/*)

---

## Version

**Template Version:** 2.0.0 (Truth Shift Integration)
**Platform Version:** R9 (90% Complete)
**Generated:** 2025-11-24
**Status:** Production-ready with documented gaps

**Changes from 1.0:**
- Added mental model guidance (channel-first thinking)
- Clarified workflow mode vs agent mode distinction
- Documented R9 parking decision (90% complete)
- Added UX-level standardization patterns
- Integrated ubiquitous-language truth shifts
- Added anti-pattern documentation

**This template is TIMELESS until next major truth shift.**
