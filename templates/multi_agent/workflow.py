"""
Multi-Agent Workflow Template (⭐⭐ Intermediate)

MENTAL MODEL:
  State = TypedDict with field ownership (each agent owns its output fields)
  Nodes = Producers (agents return only their owned fields)
  Flow = Sequential (researcher → writer → reviewer)
  Coordination = Channel-based (LangGraph coordinates via LastValue channels)

ANTI-PATTERNS TO AVOID:
  ❌ return {**state, "field": value}       # State spreading → concurrent writes
  ❌ Multiple nodes writing same field      # Collision → InvalidUpdateError
  ❌ current_step shared by all nodes       # Concurrent writes
  ❌ Returning fields from other nodes      # Violates field ownership

CORRECT PATTERNS:
  ✅ Each agent owns its output fields      # researcher owns research_output
  ✅ return {"research_output": value}      # Return only owned fields
  ✅ Read from any field, write to owned    # Read topic, write research_output
  ✅ Sequential flow via edges              # Prevents concurrent execution

FIELD OWNERSHIP PATTERN:
  researcher_node:
    reads: topic
    owns: research_output

  writer_node:
    reads: research_output
    owns: writing_output

  reviewer_node:
    reads: writing_output
    owns: review_output

CUSTOMIZE THIS TEMPLATE:
  1. Rename agents for your domain (Zone 1: State Schema)
  2. Modify agent logic (Zone 2: Node Functions)
  3. Adjust execution flow (Zone 3: Graph Structure)

USAGE:
  lgp run workflows/my_workflow.py         # Experiment mode
  lgp serve workflows/my_workflow.py       # Hosted mode

SEE ALSO:
  - Mental models: sacred-core/01-the-project.md#workflow-mode
  - Field ownership: sacred-core/02-the-discipline.md#channel-coordination-purity
  - Template guide: sacred-core/03-templates.md#tier-2-multi-agent
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ========================================
# ZONE 1: State Schema
# ← CUSTOMIZE: Rename agents, add/remove fields
# ========================================

class WorkflowState(TypedDict):
    """
    State schema with field ownership.

    Pattern: Each agent owns its output fields
    """
    # Input
    topic: str                # ← CUSTOMIZE: Your input fields

    # Researcher fields (researcher owns these)
    research_output: str      # ← CUSTOMIZE: Agent 1 output

    # Writer fields (writer owns these)
    writing_output: str       # ← CUSTOMIZE: Agent 2 output

    # Reviewer fields (reviewer owns these)
    review_output: str        # ← CUSTOMIZE: Agent 3 output


# ========================================
# ZONE 2: Node Functions
# ← CUSTOMIZE: Replace with your agent logic
# ========================================

async def researcher_node(state: WorkflowState) -> dict:
    """
    Agent 1: Research

    Ownership:
      - Reads: topic
      - Owns: research_output

    ✅ Returns only fields this agent owns
    ✅ No state spreading
    """
    topic = state["topic"]

    # ← CUSTOMIZE: Add your research logic here
    research_result = (
        f"Research findings on: {topic}\n\n"
        "- Key point 1\n"
        "- Key point 2\n"
        "- Key point 3"
    )

    # ✅ CORRECT: Return only owned field
    return {"research_output": research_result}

    # ❌ WRONG: Don't spread state
    # return {**state, "research_output": research_result}


async def writer_node(state: WorkflowState) -> dict:
    """
    Agent 2: Writing

    Ownership:
      - Reads: research_output
      - Owns: writing_output

    ✅ Returns only fields this agent owns
    ✅ Reads from previous agent's output
    """
    research = state["research_output"]

    # ← CUSTOMIZE: Add your writing logic here
    article = (
        f"Article Draft:\n\n"
        f"Based on the research:\n{research}\n\n"
        "This article explores the key findings..."
    )

    # ✅ CORRECT: Return only owned field
    return {"writing_output": article}


async def reviewer_node(state: WorkflowState) -> dict:
    """
    Agent 3: Review

    Ownership:
      - Reads: writing_output
      - Owns: review_output

    ✅ Returns only fields this agent owns
    ✅ Final agent in pipeline
    """
    article = state["writing_output"]

    # ← CUSTOMIZE: Add your review logic here
    review = (
        "Review Feedback:\n\n"
        "The article is well-structured. Suggestions:\n"
        "- Expand section 2\n"
        "- Add more examples"
    )

    # ✅ CORRECT: Return only owned field
    return {"review_output": review}


# ========================================
# ZONE 3: Graph Structure
# ← CUSTOMIZE: Add/remove agents, modify flow
# ========================================

# Build workflow graph
workflow = StateGraph(WorkflowState)

# Add agent nodes
# ← CUSTOMIZE: Rename agents or add more nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)

# Define sequential flow
# ← CUSTOMIZE: Modify agent execution order
workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "reviewer")
workflow.add_edge("reviewer", END)

# Export uncompiled workflow (runtime compiles with infrastructure)
# ✅ CORRECT: Export uncompiled
app = workflow

# ❌ WRONG: Don't compile in workflow code
# app = workflow.compile()  # Runtime handles this


# ========================================
# PATTERN EXPLANATION
# ========================================

# Why field ownership matters:
#
# ❌ BAD (causes concurrent writes):
#   State has: current_step: str
#   researcher returns: {**state, "current_step": "research"}
#   writer returns: {**state, "current_step": "writing"}
#   → LangGraph sees: "Both nodes want to write current_step!"
#   → Result: InvalidUpdateError
#
# ✅ GOOD (no conflicts):
#   researcher owns: research_output
#   writer owns: writing_output
#   reviewer owns: review_output
#   → Each agent writes to different field
#   → Result: No conflicts, clean coordination
#
# Key insight: Channels coordinate BETWEEN nodes.
# You don't need to manually pass state through.
# Trust LangGraph to route values via channels.
