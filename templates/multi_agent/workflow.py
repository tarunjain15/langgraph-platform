"""
Multi-Agent Workflow Template

A 3-agent pipeline pattern: Agent 1 → Agent 2 → Agent 3

CUSTOMIZE THIS TEMPLATE:
1. Update WorkflowState with your data schema
2. Rename agents (researcher, writer, reviewer → your agent names)
3. Modify agent logic for your use case
4. Add/remove agents as needed

USAGE:
    lgp run workflows/my_workflow.py
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END


class WorkflowState(TypedDict):
    """
    State that flows through all agents.

    CUSTOMIZE: Add your own fields here
    """
    # Input
    topic: str

    # Agent 1 (Researcher)
    research_task: str
    research_output: str

    # Agent 2 (Writer)
    writing_task: str
    writing_output: str

    # Agent 3 (Reviewer)
    review_task: str
    review_output: str

    # Metadata
    current_step: str


async def researcher_node(state: WorkflowState) -> WorkflowState:
    """
    Agent 1: Research

    CUSTOMIZE: Replace with your first agent logic

    Args:
        state: Current workflow state

    Returns:
        Updated state with research results
    """
    topic = state.get("topic", "")

    # ← CUSTOMIZE: Add your research logic here
    research_result = f"Research findings on: {topic}\n\n- Key point 1\n- Key point 2\n- Key point 3"

    return {
        **state,
        "research_output": research_result,
        "current_step": "research_complete"
    }


async def writer_node(state: WorkflowState) -> WorkflowState:
    """
    Agent 2: Writing

    CUSTOMIZE: Replace with your second agent logic

    Args:
        state: Current workflow state

    Returns:
        Updated state with written content
    """
    research = state.get("research_output", "")

    # ← CUSTOMIZE: Add your writing logic here
    article = f"Article Draft:\n\nBased on the research:\n{research}\n\nThis article explores the key findings..."

    return {
        **state,
        "writing_output": article,
        "current_step": "writing_complete"
    }


async def reviewer_node(state: WorkflowState) -> WorkflowState:
    """
    Agent 3: Review

    CUSTOMIZE: Replace with your third agent logic

    Args:
        state: Current workflow state

    Returns:
        Updated state with review feedback
    """
    article = state.get("writing_output", "")

    # ← CUSTOMIZE: Add your review logic here
    review = f"Review Feedback:\n\nThe article is well-structured. Suggestions:\n- Expand section 2\n- Add more examples"

    return {
        **state,
        "review_output": review,
        "current_step": "review_complete"
    }


def create_workflow():
    """Create and compile the multi-agent workflow"""
    # Build graph
    graph = StateGraph(WorkflowState)

    # Add agent nodes
    # ← CUSTOMIZE: Rename agents or add more nodes
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)

    # Define sequential flow
    # ← CUSTOMIZE: Modify agent execution order
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "reviewer")
    graph.add_edge("reviewer", END)

    # Compile and return
    return graph.compile()


# Export compiled workflow (required by lgp runtime)
workflow = create_workflow()
