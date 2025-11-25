```yaml
name: LangGraph Platform - Templates
description: Progressive workflow templates encoding mental models. STRUCTURAL truth (template patterns, mental models) that changes only when architecture shifts.
created: 2025-11-24
version: 1.0.0
```

# LangGraph Platform: Templates

## Sacred Principle (ETERNAL)

```
Templates = Mental Model Crystallization
         + Anti-Pattern Protection
         + Progressive Complexity
         + Zero-Ceremony Start
```

**What Templates ARE:**
- Mental model teaching instruments
- Architecture pattern encoders
- Rapid-start accelerators
- Constraint enforcers

**What Templates ARE NOT:**
- Boilerplate copiers
- Feature showcases
- Framework abstractions
- Tutorial playgrounds

---

## The Three Template Tiers (STRUCTURAL)

### Tier 1: Basic (⭐ Beginner)
**Location:** `templates/basic/workflow.py`

**Mental Model:**
```
Single-Node Workflow = State schema (input → output)
                     + One processing node
                     + Linear flow (START → process → END)
```

**Teaches:**
- StateGraph basics
- TypedDict state schema
- Async node functions
- Return dict updates (not full state)

**Use Cases:**
- Simple data pipelines
- Quick prototyping
- Learning LangGraph fundamentals
- One-step transformations

**Complexity:** ~70 lines
**Time to Running:** <1 minute

**Template Structure:**
```python
"""
Basic Workflow Template

Mental Model:
  State = TypedDict (input/output fields)
  Node = Async function (returns dict update)
  Flow = Linear (START → process → END)

Anti-Patterns to Avoid:
  ❌ return {**state, "output": value}  # State spreading
  ❌ def process(state): ... # Sync (use async)
  ❌ return state # Return full state (use dict update)
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class WorkflowState(TypedDict):
    input: str      # ← CUSTOMIZE: Add your input fields
    output: str     # ← CUSTOMIZE: Add your output fields

async def process_node(state: WorkflowState) -> dict:
    """Process the input and return output"""
    # ← CUSTOMIZE: Add your processing logic here
    output = f"Processed: {state['input']}"

    # ✅ Return only what this node produces
    return {"output": output}

# Build workflow graph
workflow = StateGraph(WorkflowState)
workflow.add_node("process", process_node)  # ← CUSTOMIZE: Add more nodes
workflow.add_edge(START, "process")
workflow.add_edge("process", END)

# Export uncompiled workflow
app = workflow
```

---

### Tier 2: Multi-Agent (⭐⭐ Intermediate)
**Location:** `templates/multi_agent/workflow.py`

**Mental Model:**
```
Multi-Agent Workflow = 3 agents (Researcher, Writer, Reviewer)
                     + Sequential collaboration
                     + Agent-to-agent data flow
                     + Independent state fields per agent
```

**Teaches:**
- Multiple node coordination
- State field ownership (each agent owns its fields)
- Sequential execution order
- Agent collaboration patterns

**Use Cases:**
- Research → Writing → Review pipelines
- Multi-step processing
- Agent collaboration workflows
- Team simulation patterns

**Complexity:** ~150 lines
**Time to Running:** <2 minutes

**Key Pattern:**
```python
class MultiAgentState(TypedDict):
    # Input
    topic: str

    # Researcher fields (researcher owns these)
    researcher_task: str
    researcher_output: str

    # Writer fields (writer owns these)
    writer_task: str
    writer_output: str

    # Reviewer fields (reviewer owns these)
    reviewer_task: str
    reviewer_output: str

async def prepare_researcher(state: MultiAgentState) -> dict:
    # ✅ Returns only researcher's task field
    return {
        "researcher_task": f"Research: {state['topic']}"
    }

async def researcher(state: MultiAgentState) -> dict:
    # ✅ Returns only researcher's output field
    return {
        "researcher_output": f"Research results for {state['researcher_task']}"
    }

# Flow: prepare_researcher → researcher → prepare_writer → writer → ...
```

**Truth:** Each agent is a producer, not a transformer. Owns its output fields.

---

### Tier 3: With Claude Code (⭐⭐⭐ Advanced)
**Location:** `templates/with_claude_code/workflow.py`

**Mental Model:**
```
Claude Code Workflow = Stateful MCP agents
                     + Repository isolation (each agent in separate workspace)
                     + Session continuity (via checkpointer)
                     + Runtime injection (nodes created by executor)
```

**Teaches:**
- Stateful agent sessions
- Repository-based isolation
- Session ID persistence
- Runtime node injection pattern
- Fixed cost model ($20/month Claude Pro)

**Use Cases:**
- Complex tasks requiring Claude Code capabilities
- Multi-repository workflows
- Stateful agent interactions
- Long-running sessions with memory

**Complexity:** ~200 lines
**Time to Running:** <5 minutes (requires mesh-mcp setup)

**Requirements:**
```yaml
dependencies:
  - mesh-mcp server running (claude-mcp container)
  - Repository workspaces configured
  - R4 checkpointer enabled
  - Langfuse configured (optional)
```

**Key Pattern:**
```python
# Workflow defines preparation nodes (not agent nodes)
async def prepare_researcher_task(state: ClaudeCodeState) -> dict:
    return {
        "researcher_task": f"Research: {state['topic']}"
    }

# Agent nodes injected at runtime via claude_code_config
claude_code_config = {
    "enabled": True,
    "agents": [
        {
            "role_name": "researcher",
            "repository": "sample-app",  # ← Isolated workspace
            "timeout": 60000,
            "inject_after": "prepare_research",
            "inject_before": "prepare_write"  # ← Sequential flow
        }
    ]
}

# Executor detects config and creates Claude Code nodes dynamically
# Nodes execute via MCP: mesh_execute(repository, task, session_id)
# Session ID persisted via checkpointer for continuity
```

**Truth:** Claude Code nodes are runtime infrastructure, not workflow logic.

---

## Template Selection Guide (STRUCTURAL)

```
Choose template based on complexity level:

┌─────────────────────────────────────────────────────┐
│                                                     │
│   START: What are you building?                    │
│                                                     │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
        ┌───────────────────┐
        │ Single-step       │ Yes → templates/basic
        │ processing?       │
        └───────┬───────────┘
                │ No
                ▼
        ┌───────────────────┐
        │ Multi-agent       │ Yes → templates/multi_agent
        │ collaboration?    │
        └───────┬───────────┘
                │ No
                ▼
        ┌───────────────────┐
        │ Need Claude Code  │ Yes → templates/with_claude_code
        │ capabilities?     │
        └───────┬───────────┘
                │ No
                ▼
        Build custom workflow
        (Start from basic, add complexity)
```

---

## Customization Points (STRUCTURAL)

### Every Template Has 3 Core Customization Zones

**Zone 1: State Schema**
```python
class WorkflowState(TypedDict):
    input: str      # ← CUSTOMIZE: Your input fields
    output: str     # ← CUSTOMIZE: Your output fields
    # Add more fields as needed
```

**Zone 2: Node Logic**
```python
async def process_node(state: WorkflowState) -> dict:
    # ← CUSTOMIZE: Add your processing logic here
    result = your_business_logic(state)

    # ✅ Return only what this node produces
    return {"output": result}
```

**Zone 3: Graph Structure**
```python
workflow.add_node("process", process_node)  # ← CUSTOMIZE: Add more nodes
workflow.add_edge(START, "process")         # ← CUSTOMIZE: Modify flow
workflow.add_edge("process", END)
```

**Markers:** All customization points marked with `← CUSTOMIZE` comments

---

## Mental Model Encoding (ETERNAL)

### Template Headers MUST Include

**1. Mental Model Summary**
```python
"""
Mental Model:
  - State = TypedDict schema (fields declared upfront)
  - Nodes = Producers (return only owned fields)
  - Edges = Coordination (define execution order)
  - Channels = Implicit (LastValue semantics)
"""
```

**2. Anti-Patterns**
```python
"""
Anti-Patterns to Avoid:
  ❌ return {**state, "field": value}  # State spreading → concurrent writes
  ❌ Multiple nodes writing same field  # Collision → InvalidUpdateError
  ❌ Sequential function thinking       # Wrong model → errors
"""
```

**3. Correct Patterns**
```python
"""
Correct Patterns:
  ✅ return {"field": value}           # Return only what node produces
  ✅ Use Annotated[list, add]          # For multi-writer fields
  ✅ Trust channel coordination        # Let LangGraph handle ordering
"""
```

**4. Reference Links**
```python
"""
See Also:
  - Mental models: sacred-core/01-the-project.md
  - Constraints: sacred-core/02-the-discipline.md
  - Ubiquitous language: research/ubiquitous-language/ (future R10+)
"""
```

---

## Template Evolution Protocol (LEARNED)

### When to Add New Template

**Trigger:** New architectural pattern emerges and repeats across 3+ workflows

**Process:**
```yaml
1. Identify: Pattern used in >= 3 production workflows
2. Crystallize: Extract common structure, remove specifics
3. Document: Encode mental model, anti-patterns, correct patterns
4. Validate: Test template → running workflow in <5 minutes
5. Integrate: Add to templates/, update README, update CLI
```

**Example:**
```
Pattern: 4-channel reactive agent coordination (R10+)
Status: Observed in research/, not yet production-ready
Action: Hold until >= 3 production workflows adopt pattern
Template: templates/agent_coordination/ (future)
```

### When to Deprecate Template

**Trigger:** Template no longer aligns with platform primitive

**Process:**
```yaml
1. Detect: Template violates sacred constraints
2. Analyze: Can it be fixed? Or is pattern fundamentally broken?
3. Deprecate: Move to templates/deprecated/, update docs
4. Migrate: Provide migration guide to replacement template
```

**Example:**
```
Template: templates/sync_workflow/ (hypothetical)
Violation: Uses sync functions (not async) → breaks runtime
Action: Deprecate, migrate to async pattern
```

---

## Template Testing (WITNESS-BASED)

### Every Template MUST Pass

**Test 1: Zero-Friction Promotion**
```python
def test_template_zero_friction(template_name):
    # Create workflow from template
    create_workflow(f"test_{template_name}", template=template_name)

    # Test in experiment mode
    result_exp = execute_workflow(
        f"workflows/test_{template_name}.py",
        environment="experiment",
        input_data=test_input
    )

    # Test in hosted mode (zero code changes)
    result_hosted = execute_workflow(
        f"workflows/test_{template_name}.py",
        environment="hosted",
        input_data=test_input
    )

    # Results must be identical
    assert result_exp == result_hosted
```

**Test 2: Time to Running**
```python
def test_template_time_to_running(template_name, max_seconds):
    start = time.time()

    # Create workflow from template
    create_workflow(f"test_{template_name}", template=template_name)

    # Execute workflow
    result = execute_workflow(
        f"workflows/test_{template_name}.py",
        input_data=test_input
    )

    elapsed = time.time() - start

    assert elapsed < max_seconds, \
        f"Template {template_name} took {elapsed}s (max: {max_seconds}s)"
    assert result["status"] == "success"
```

**Test 3: Constraint Compliance**
```python
def test_template_constraints(template_name):
    workflow_code = load_template(template_name)

    # ENVIRONMENT_ISOLATION
    assert "os.getenv" not in workflow_code
    assert "from runtime" not in workflow_code

    # CONFIG_DRIVEN_INFRASTRUCTURE
    assert "SqliteSaver" not in workflow_code
    assert "Langfuse(" not in workflow_code

    # CHANNEL_COORDINATION_PURITY
    assert "{**state" not in workflow_code
```

**Enforcement:** CI runs all tests on every template change

---

## Template Graduation Path (STRUCTURAL)

```
User Journey:

1. Start with Basic Template
   ├─ Learn: State = TypedDict, Nodes = Async functions
   ├─ Time: <1 minute to running workflow
   └─ Outcome: Understand fundamental pattern

2. Graduate to Multi-Agent Template
   ├─ Learn: Multiple nodes, field ownership, sequential flow
   ├─ Time: <2 minutes to 3-agent pipeline
   └─ Outcome: Multi-step collaboration pattern

3. Graduate to Claude Code Template
   ├─ Learn: Stateful agents, repository isolation, session continuity
   ├─ Time: <5 minutes to stateful agent workflow
   └─ Outcome: Advanced agent orchestration

4. Build Custom Patterns (R10+)
   ├─ Learn: 4-channel coordination, reactive agents, worker architecture
   ├─ Time: TBD (not yet implemented)
   └─ Outcome: Agent mode mastery
```

**Truth:** Templates are pedagogy, not just starting points.

---

## Integration with Disciplines (STRUCTURAL)

Templates MUST enforce all 6 sacred constraints:

**1. ENVIRONMENT_ISOLATION**
```python
# ✅ Templates never import runtime internals
# ✅ Templates never check environment variables
# ✅ Templates work identically in experiment and hosted modes
```

**2. CONFIG_DRIVEN_INFRASTRUCTURE**
```python
# ✅ Templates never hardcode checkpointers
# ✅ Templates never instantiate Langfuse
# ✅ Infrastructure configured in config/{environment}.yaml
```

**3. CHANNEL_COORDINATION_PURITY**
```python
# ✅ Templates never spread state: {**state, ...}
# ✅ Templates return only owned fields
# ✅ Templates document multi-writer pattern: Annotated[list, add]
```

**4. HOT_RELOAD_CONTINUITY**
```python
# ✅ Templates work with hot reload (no reload-breaking patterns)
# ✅ File changes trigger <500ms reload
# ✅ Active workflows continue during reload
```

**5. ZERO_FRICTION_PROMOTION**
```python
# ✅ Templates work in both experiment and hosted modes
# ✅ Zero code changes required for environment switch
# ✅ Infrastructure injected by runtime, not workflow
```

**6. WITNESS_BASED_COMPLETION**
```python
# ✅ Template quality measured by time-to-running
# ✅ Template correctness verified by constraint tests
# ✅ Template pedagogy validated by user graduation rate
```

---

## Knowledge Layer Compliance

**This document contains:**
- ✅ Template tiers (STRUCTURAL - 3 levels, fixed)
- ✅ Mental model encoding (ETERNAL - always required)
- ✅ Selection guide (STRUCTURAL - decision tree)
- ✅ Customization zones (STRUCTURAL - 3 zones per template)
- ✅ Evolution protocol (LEARNED - when to add/deprecate)

**This document excludes:**
- ❌ Template source code (→ templates/*/)
- ❌ Usage statistics (→ 04-current-state.md)
- ❌ Specific user workflows (→ workflows/)
- ❌ Implementation details (→ source code)

---

## Archive Notice

**This document is MOSTLY TIMELESS.**

Update only when:
1. New template tier added (e.g., Agent Coordination ⭐⭐⭐⭐)
2. Mental model encoding requirements change
3. Selection criteria evolve (new decision points)
4. Constraint compliance requirements tighten

**This document describes template ARCHITECTURE, not template CONTENT.**

When someone asks "How do I choose a template?", this document answers.
When someone asks "What should a template teach?", this document answers.
