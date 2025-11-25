"""
Basic Workflow Template (⭐ Beginner)

MENTAL MODEL:
  State = TypedDict schema (fields declared upfront)
  Node = Async function returning dict update (not full state)
  Flow = Linear (START → process → END)
  Channels = Implicit LastValue coordination

ANTI-PATTERNS TO AVOID:
  ❌ return {**state, "field": value}  # State spreading → concurrent writes
  ❌ def process_node(state): ...      # Sync function (use async)
  ❌ return state                       # Returning full state (use dict update)
  ❌ workflow.compile()                 # Compiling (runtime handles this)

CORRECT PATTERNS:
  ✅ async def process_node(state): ...     # Async function
  ✅ return {"output": value}                # Return only what node produces
  ✅ app = workflow                          # Export uncompiled
  ✅ Trust runtime for infrastructure        # No checkpointer/tracer in code

CUSTOMIZE THIS TEMPLATE:
  1. Update WorkflowState with your data schema (Zone 1)
  2. Modify process_node logic for your use case (Zone 2)
  3. Add more nodes if needed (Zone 3)

USAGE:
  lgp run workflows/my_workflow.py         # Experiment mode (hot reload)
  lgp serve workflows/my_workflow.py       # Hosted mode (API server)

SEE ALSO:
  - Mental models: sacred-core/01-the-project.md#workflow-mode
  - Constraints: sacred-core/02-the-discipline.md
  - Templates: sacred-core/03-templates.md#tier-1-basic
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ========================================
# ZONE 1: State Schema
# ← CUSTOMIZE: Add your input/output fields
# ========================================

class WorkflowState(TypedDict):
    """State schema for the workflow"""
    input: str      # ← CUSTOMIZE: Your input fields
    output: str     # ← CUSTOMIZE: Your output fields


# ========================================
# ZONE 2: Node Logic
# ← CUSTOMIZE: Replace with your processing
# ========================================

async def process_node(state: WorkflowState) -> dict:
    """
    Main processing node.

    ✅ Returns only fields this node produces (not full state)
    ✅ Async function (required by runtime)

    Args:
        state: Current workflow state

    Returns:
        Dict with only the fields this node updates
    """
    # ← CUSTOMIZE: Add your processing logic here
    input_text = state["input"]
    output = f"Processed: {input_text}"

    # ✅ CORRECT: Return only what this node produces
    return {"output": output}

    # ❌ WRONG: Don't spread state
    # return {**state, "output": output}

    # ❌ WRONG: Don't return full state
    # return {"input": input_text, "output": output}


# ========================================
# ZONE 3: Graph Structure
# ← CUSTOMIZE: Add more nodes, modify flow
# ========================================

# Build workflow graph
workflow = StateGraph(WorkflowState)

# Add nodes
# ← CUSTOMIZE: Add more nodes with workflow.add_node("name", function)
workflow.add_node("process", process_node)

# Define edges (execution flow)
# ← CUSTOMIZE: Modify flow with workflow.add_edge(from, to)
workflow.add_edge(START, "process")
workflow.add_edge("process", END)

# Export uncompiled workflow (runtime compiles with infrastructure)
# ✅ CORRECT: Export uncompiled
app = workflow

# ❌ WRONG: Don't compile in workflow code
# app = workflow.compile()  # Runtime handles this
