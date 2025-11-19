"""
Claude Code Workflow Template

Multi-agent workflow using Claude Code nodes with stateful sessions.

REQUIREMENTS:
- mesh-mcp server running (claude-mcp container)
- Repository workspaces configured in mesh-mcp
- R4 checkpointer enabled for session persistence
- Langfuse configured for observability

CUSTOMIZE THIS TEMPLATE:
1. Update WorkflowState with your data schema
2. Configure agent roles and repositories (agent_configs)
3. Modify preparation nodes to generate tasks
4. Update agent count (add/remove agents)

ARCHITECTURE:
- Each agent executes in isolated repository workspace
- Session IDs persist via R4 checkpointer (thread_id)
- Fixed cost model: $20/month Claude Pro subscription

USAGE:
    lgp run workflows/my_workflow.py
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END


class WorkflowState(TypedDict):
    """
    State schema for Claude Code workflow.

    CUSTOMIZE: Add your own fields here
    """
    # Input
    topic: str

    # Agent 1: Researcher
    researcher_task: str
    researcher_output: str
    researcher_session_id: str

    # Agent 2: Writer
    writer_task: str
    writer_output: str
    writer_session_id: str

    # Agent 3: Reviewer
    reviewer_task: str
    reviewer_output: str
    reviewer_session_id: str

    # Metadata
    current_step: str


async def prepare_researcher_task(state: WorkflowState) -> WorkflowState:
    """
    Prepare task for researcher agent.

    CUSTOMIZE: Modify task generation logic

    Args:
        state: Current workflow state

    Returns:
        State with researcher_task field
    """
    topic = state.get("topic", "")

    return {
        **state,
        "researcher_task": f"Research this topic briefly (2-3 sentences): {topic}",
        "current_step": "preparing_research"
    }


async def prepare_writer_task(state: WorkflowState) -> WorkflowState:
    """
    Prepare task for writer agent based on research.

    CUSTOMIZE: Modify task generation logic

    Args:
        state: Current workflow state

    Returns:
        State with writer_task field
    """
    research = state.get("researcher_output", "No research available")

    return {
        **state,
        "writer_task": f"Based on this research: '{research}', write a short summary (1 paragraph).",
        "current_step": "preparing_write"
    }


async def prepare_reviewer_task(state: WorkflowState) -> WorkflowState:
    """
    Prepare task for reviewer agent based on article.

    CUSTOMIZE: Modify task generation logic

    Args:
        state: Current workflow state

    Returns:
        State with reviewer_task field
    """
    article = state.get("writer_output", "No article available")

    return {
        **state,
        "reviewer_task": f"Review this article and provide brief feedback (1-2 sentences): '{article}'",
        "current_step": "preparing_review"
    }


def create_workflow():
    """
    Create workflow with Claude Code node injection points.

    NOTE: Claude Code nodes will be injected at runtime by the executor.
    The executor detects claude_code_config and creates nodes dynamically.
    """
    # Build graph
    graph = StateGraph(WorkflowState)

    # Add preparation nodes
    # ← CUSTOMIZE: Modify preparation logic
    graph.add_node("prepare_research", prepare_researcher_task)
    graph.add_node("prepare_write", prepare_writer_task)
    graph.add_node("prepare_review", prepare_reviewer_task)

    # Define flow (Claude Code nodes injected after each prepare step)
    # ← CUSTOMIZE: Modify execution order
    graph.set_entry_point("prepare_research")
    graph.add_edge("prepare_research", "prepare_write")
    graph.add_edge("prepare_write", "prepare_review")
    graph.add_edge("prepare_review", END)

    # Return uncompiled graph (executor will compile after injection)
    return graph


# Export uncompiled workflow
app = create_workflow()


# Claude Code configuration for executor injection
# ← CUSTOMIZE: Update agent roles and repositories
claude_code_config = {
    "enabled": True,
    "agents": [
        {
            "role_name": "researcher",
            "repository": "sample-app",      # ← CUSTOMIZE: Your repository name
            "timeout": 60000,                 # 60 seconds
            "inject_after": "prepare_research"
        },
        {
            "role_name": "writer",
            "repository": "sample-api",       # ← CUSTOMIZE: Your repository name
            "timeout": 60000,
            "inject_after": "prepare_write"
        },
        {
            "role_name": "reviewer",
            "repository": "sample-infra",     # ← CUSTOMIZE: Your repository name
            "timeout": 60000,
            "inject_after": "prepare_review"
        }
    ]
}
