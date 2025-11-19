"""
Basic Workflow Template

A simple single-node workflow for quick experimentation.

CUSTOMIZE THIS TEMPLATE:
1. Update WorkflowState with your data schema
2. Modify process_node logic for your use case
3. Add more nodes if needed (workflow.add_node)
4. Update edges to define execution flow

USAGE:
    lgp run workflows/my_workflow.py
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END


class WorkflowState(TypedDict):
    """
    State that flows through the workflow.

    CUSTOMIZE: Add your own fields here
    """
    input: str      # ← Input data
    output: str     # ← Output result
    step: int       # ← Processing step counter


def process_node(state: WorkflowState) -> WorkflowState:
    """
    Main processing node.

    CUSTOMIZE: Replace this logic with your processing code

    Args:
        state: Current workflow state

    Returns:
        Updated state with new values
    """
    input_text = state.get("input", "")
    step = state.get("step", 0)

    # ← CUSTOMIZE: Add your processing logic here
    output = f"Processed: {input_text} (step {step + 1})"

    return {
        "input": input_text,
        "output": output,
        "step": step + 1
    }


def create_workflow():
    """Create and compile the workflow graph"""
    # Build graph
    graph = StateGraph(WorkflowState)

    # Add nodes
    # ← CUSTOMIZE: Add more nodes with graph.add_node("name", function)
    graph.add_node("process", process_node)

    # Define edges
    # ← CUSTOMIZE: Modify flow with graph.add_edge(from, to)
    graph.set_entry_point("process")
    graph.add_edge("process", END)

    # Compile and return
    return graph.compile()


# Export compiled workflow (required by lgp runtime)
workflow = create_workflow()
