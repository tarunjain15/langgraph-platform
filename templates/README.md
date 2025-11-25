# LangGraph Platform - Workflow Templates

**Rapid-start templates encoding mental models for 0-cycle builds.**

> **Mental Model First:** Templates teach channel-first thinking to prevent the 6-cycle debugging pain. Read template headers before coding.

**See Also:**
- Template architecture: [sacred-core/03-templates.md](../sacred-core/03-templates.md)
- Mental models: [sacred-core/01-the-project.md](../sacred-core/01-the-project.md#workflow-mode)
- Constraints: [sacred-core/02-the-discipline.md](../sacred-core/02-the-discipline.md)

---

## Available Templates

### 1. `basic` - Single Node Workflow
**Use Case:** Simple processing pipeline, quick prototyping
**Complexity:** ⭐ Beginner
**Requirements:** None

A single-node workflow for straightforward data processing.

```bash
lgp create my_workflow --template basic
```

**What You Get:**
- Simple state schema (input → output)
- One processing node
- Basic graph structure
- Inline customization guides

**Customize:**
- State schema fields
- Processing logic
- Add more nodes

---

### 2. `multi_agent` - 3-Agent Pipeline
**Use Case:** Sequential agent collaboration (research → write → review)
**Complexity:** ⭐⭐ Intermediate
**Requirements:** None

Three agents working in sequence, each building on previous results.

```bash
lgp create my_workflow --template multi_agent
```

**What You Get:**
- 3-agent state schema (researcher, writer, reviewer)
- Sequential execution flow
- Agent-to-agent data passing
- Extensible agent pattern

**Customize:**
- Agent names and roles
- Agent logic
- Number of agents
- Execution order

---

### 3. `with_claude_code` - Stateful Claude Code Agents
**Use Case:** Complex tasks requiring Claude Code capabilities
**Complexity:** ⭐⭐⭐ Advanced
**Requirements:**
- mesh-mcp server running (claude-mcp container)
- Repository workspaces configured
- R4 checkpointer enabled
- Langfuse configured

Multi-agent workflow where each agent is a Claude Code session with:
- Repository isolation (each agent in separate workspace)
- Session continuity (stateful sessions via checkpointer)
- Fixed cost model ($20/month Claude Pro subscription)

```bash
lgp create my_workflow --template with_claude_code
```

**What You Get:**
- 3 Claude Code agent configurations
- Task preparation nodes
- Session ID persistence
- Repository isolation pattern
- Runtime injection configuration

**Customize:**
- Agent roles and repositories
- Task generation logic
- Number of agents
- Timeout values

---

## Quick Start

### 1. Create Workflow from Template
```bash
lgp create my_workflow --template basic
```

### 2. Edit Your Workflow
```bash
# Workflow created at: workflows/my_workflow.py
# Look for ← CUSTOMIZE comments
```

### 3. Run Workflow
```bash
lgp run workflows/my_workflow.py
```

---

## Template Customization Guide

All templates include inline `← CUSTOMIZE` comments marking modification points.

### Basic Customization Points

1. **State Schema** - Define data structure
```python
class WorkflowState(TypedDict):
    input: str      # ← Add your fields
    output: str
```

2. **Node Logic** - Implement processing
```python
def process_node(state: WorkflowState) -> WorkflowState:
    # ← CUSTOMIZE: Add your logic here
    output = f"Processed: {state['input']}"
    return {"output": output}
```

3. **Graph Structure** - Define execution flow
```python
graph.add_node("process", process_node)  # ← Add more nodes
graph.add_edge("process", END)           # ← Modify flow
```

---

## Progressive Complexity

### Level 1: Basic Template
- Single node
- Simple state
- Linear flow
- ~50 lines of code

### Level 2: Multi-Agent Template
- Multiple nodes
- Agent collaboration
- Sequential flow
- ~150 lines of code

### Level 3: Claude Code Template
- Stateful agents
- Repository isolation
- Session continuity
- External dependencies
- ~200 lines of code

---

## Template Structure

Each template is a standalone Python file:

```
templates/
├── basic/
│   └── workflow.py          # Single-node workflow
├── multi_agent/
│   └── workflow.py          # 3-agent pipeline
├── with_claude_code/
│   └── workflow.py          # Claude Code agents
└── README.md                # This file
```

---

## Next Steps

After creating a workflow from a template:

1. **Experiment Mode** - Test locally with hot reload
```bash
lgp run workflows/my_workflow.py --watch
```

2. **Hosted Mode** - Serve as API
```bash
lgp serve workflows/my_workflow.py
```

3. **Production** - Deploy (R7 feature)
```bash
lgp deploy my_workflow
```

---

## Mental Model Learning Path

**Start here to avoid 6-cycle debugging:**

### 1. Understand the Primitive (5 minutes)
Read: [sacred-core/01-the-project.md](../sacred-core/01-the-project.md)

**Key Concepts:**
- Workflow mode vs Agent mode
- Platform is workflow layer (R1-R9)
- Agent layer is future (R10+)

### 2. Learn Channel Coordination (10 minutes)
Read template headers in order:
1. `basic/workflow.py` - Single node pattern
2. `multi_agent/workflow.py` - Field ownership pattern
3. `with_claude_code/workflow.py` - Runtime injection pattern

**Key Insights:**
- State = TypedDict (not dict to pass around)
- Nodes = Producers (return only owned fields)
- Channels = Coordination (LangGraph handles routing)
- **Never spread state:** `{**state, "field": value}` → concurrent writes

### 3. Know the Constraints (5 minutes)
Read: [sacred-core/02-the-discipline.md](../sacred-core/02-the-discipline.md)

**6 Sacred Constraints:**
1. ENVIRONMENT_ISOLATION - No `os.getenv("ENVIRONMENT")` in workflows
2. CONFIG_DRIVEN_INFRASTRUCTURE - No checkpointer/tracer in code
3. CHANNEL_COORDINATION_PURITY - No state spreading
4. HOT_RELOAD_CONTINUITY - <500ms reload
5. ZERO_FRICTION_PROMOTION - Same code in experiment and hosted
6. WITNESS_BASED_COMPLETION - Observable metrics

### 4. Choose Template (2 minutes)
Decision tree:
- Single step? → `basic`
- Multi-agent collaboration? → `multi_agent`
- Need Claude Code? → `with_claude_code`

### 5. Build Workflow (Variable)
- Read template header completely
- Follow CUSTOMIZE markers
- Trust the runtime for infrastructure
- Test in experiment mode first

**Total Time to 0-Cycle Build:** ~25 minutes (vs 6-cycle trial-and-error: hours)

---

## Common Errors and Fixes

### Error: InvalidUpdateError - Concurrent write detected

**Cause:** State spreading or multiple nodes writing same field

**Fix:**
```python
# ❌ WRONG
return {**state, "output": value}

# ✅ CORRECT
return {"output": value}
```

**Reference:** [sacred-core/02-the-discipline.md#channel-coordination-purity](../sacred-core/02-the-discipline.md#channel-coordination-purity)

### Error: Workflow behaves differently in hosted mode

**Cause:** Environment-aware code in workflow

**Fix:** Remove all `os.getenv()`, checkpointer instantiation, tracer initialization. Let runtime inject infrastructure.

**Reference:** [sacred-core/02-the-discipline.md#environment-isolation](../sacred-core/02-the-discipline.md#environment-isolation)

---

## Support

- Documentation: `lgp --help`
- Sacred Knowledge: [sacred-core/](../sacred-core/)
- Issues: [GitHub Issues](https://github.com/yourusername/langgraph-platform/issues)
- Examples: See `workflows/` directory for reference implementations
