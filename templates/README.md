# LangGraph Platform - Workflow Templates

Rapid-start templates for creating workflows in minutes.

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

## Support

- Documentation: `lgp --help`
- Issues: [GitHub Issues](https://github.com/yourusername/langgraph-platform/issues)
- Examples: See `workflows/` directory for reference implementations
