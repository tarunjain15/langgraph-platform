"""
Claude Code Workflow Template (⭐⭐⭐ Advanced)

MENTAL MODEL:
  State = TypedDict with task/output/session_id fields per agent
  Preparation Nodes = Regular Python functions (generate tasks)
  Agent Nodes = Injected by runtime (execute via MCP)
  Session Continuity = Session IDs persist via checkpointer
  Repository Isolation = Each agent in separate Docker workspace

ANTI-PATTERNS TO AVOID:
  ❌ return {**state, "field": value}       # State spreading → concurrent writes
  ❌ Creating Claude Code nodes in workflow  # Runtime handles injection
  ❌ Manual session ID management            # Checkpointer handles persistence
  ❌ current_step shared by all nodes        # Concurrent writes

CORRECT PATTERNS:
  ✅ Preparation nodes return only task field    # prepare_research → researcher_task
  ✅ Runtime injects agent nodes automatically   # Via claude_code_config
  ✅ Session IDs extracted from agent output     # Persisted by checkpointer
  ✅ inject_after defines insertion point        # Sequential flow control

ARCHITECTURE:
  Workflow Layer:
    - Preparation nodes (your code)
    - Task generation logic
    - Field ownership (each prep owns its task field)

  Runtime Layer (automatic):
    - Claude Code node injection
    - MCP session management
    - Repository isolation
    - Session ID persistence
    - Cost tracking ($20/month fixed)

FIELD OWNERSHIP:
  prepare_researcher_task:
    reads: topic
    owns: researcher_task

  researcher (injected):
    reads: researcher_task
    owns: researcher_output, researcher_session_id

  prepare_writer_task:
    reads: researcher_output
    owns: writer_task

  writer (injected):
    reads: writer_task
    owns: writer_output, writer_session_id

  (pattern continues...)

REQUIREMENTS:
  - mesh-mcp server running (claude-mcp container)
  - Repository workspaces configured
  - R4 checkpointer enabled for session persistence
  - Langfuse configured (optional, for observability)

CUSTOMIZE THIS TEMPLATE:
  1. Update WorkflowState with your fields (Zone 1)
  2. Modify preparation logic (Zone 2)
  3. Configure agent roles and repositories (Zone 3)

USAGE:
  lgp run workflows/my_workflow.py         # Experiment mode
  lgp serve workflows/my_workflow.py       # Hosted mode

SEE ALSO:
  - Mental models: sacred-core/01-the-project.md#workflow-mode
  - Runtime injection: sacred-core/02-the-discipline.md#config-driven-infrastructure
  - Template guide: sacred-core/03-templates.md#tier-3-claude-code
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ========================================
# ZONE 1: State Schema
# ← CUSTOMIZE: Add your agent fields
# ========================================

class WorkflowState(TypedDict):
    """
    State schema for Claude Code workflow.

    Pattern: Each agent has task/output/session_id fields
    """
    # Input
    topic: str                # ← CUSTOMIZE: Your input fields

    # Agent 1: Researcher (preparation node owns task, agent owns output/session_id)
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


# ========================================
# ZONE 2: Preparation Nodes
# ← CUSTOMIZE: Modify task generation logic
# ========================================

async def prepare_researcher_task(state: WorkflowState) -> dict:
    """
    Prepare task for researcher agent.

    Ownership:
      - Reads: topic
      - Owns: researcher_task

    ✅ Returns only task field (not full state)
    ✅ Runtime injects actual agent node after this
    """
    topic = state["topic"]

    # ← CUSTOMIZE: Modify task generation
    task = f"Research this topic briefly (2-3 sentences): {topic}"

    # ✅ CORRECT: Return only owned field
    return {"researcher_task": task}

    # ❌ WRONG: Don't spread state
    # return {**state, "researcher_task": task}


async def prepare_writer_task(state: WorkflowState) -> dict:
    """
    Prepare task for writer agent based on research.

    Ownership:
      - Reads: researcher_output
      - Owns: writer_task

    ✅ Reads from previous agent's output
    ✅ Returns only task field
    """
    research = state["researcher_output"]

    # ← CUSTOMIZE: Modify task generation
    task = f"Based on this research: '{research}', write a short summary (1 paragraph)."

    # ✅ CORRECT: Return only owned field
    return {"writer_task": task}


async def prepare_reviewer_task(state: WorkflowState) -> dict:
    """
    Prepare task for reviewer agent based on article.

    Ownership:
      - Reads: writer_output
      - Owns: reviewer_task

    ✅ Final preparation node in pipeline
    """
    article = state["writer_output"]

    # ← CUSTOMIZE: Modify task generation
    task = f"Review this article and provide brief feedback (1-2 sentences): '{article}'"

    # ✅ CORRECT: Return only owned field
    return {"reviewer_task": task}


# ========================================
# ZONE 3: Graph Structure
# ← CUSTOMIZE: Add/remove agents
# ========================================

# Build workflow graph (preparation nodes only)
workflow = StateGraph(WorkflowState)

# Add preparation nodes
# ← CUSTOMIZE: Modify preparation logic
workflow.add_node("prepare_research", prepare_researcher_task)
workflow.add_node("prepare_write", prepare_writer_task)
workflow.add_node("prepare_review", prepare_reviewer_task)

# Define flow (agent nodes injected by runtime between prepare nodes)
# ← CUSTOMIZE: Modify execution order
workflow.add_edge(START, "prepare_research")
workflow.add_edge("prepare_research", "prepare_write")
workflow.add_edge("prepare_write", "prepare_review")
workflow.add_edge("prepare_review", END)

# Export uncompiled workflow (runtime compiles after agent injection)
# ✅ CORRECT: Export uncompiled
app = workflow

# ❌ WRONG: Don't compile in workflow code
# app = workflow.compile()  # Runtime handles compilation


# ========================================
# ZONE 4: Claude Code Configuration
# ← CUSTOMIZE: Update agent roles and repositories
# ========================================

# Runtime detects this config and injects agent nodes automatically
claude_code_config = {
    "enabled": True,
    "agents": [
        {
            "role_name": "researcher",
            "repository": "sample-app",      # ← CUSTOMIZE: Your repository name
            "timeout": 60000,                 # 60 seconds
            "inject_after": "prepare_research"
            # Runtime injects: researcher node → reads researcher_task
            #                                  → writes researcher_output, researcher_session_id
            #                                  → executes before prepare_write
        },
        {
            "role_name": "writer",
            "repository": "sample-api",       # ← CUSTOMIZE: Your repository name
            "timeout": 60000,
            "inject_after": "prepare_write"
            # Runtime injects: writer node → reads writer_task
            #                               → writes writer_output, writer_session_id
            #                               → executes before prepare_review
        },
        {
            "role_name": "reviewer",
            "repository": "sample-infra",     # ← CUSTOMIZE: Your repository name
            "timeout": 60000,
            "inject_after": "prepare_review"
            # Runtime injects: reviewer node → reads reviewer_task
            #                                 → writes reviewer_output, reviewer_session_id
            #                                 → executes before END
        }
    ]
}


# ========================================
# PATTERN EXPLANATION
# ========================================

# Runtime Injection Flow:
#
# 1. Your workflow defines preparation nodes:
#    START → prepare_research → prepare_write → prepare_review → END
#
# 2. Runtime detects claude_code_config
#
# 3. Runtime injects agent nodes:
#    START → prepare_research → [researcher] → prepare_write → [writer] → prepare_review → [reviewer] → END
#
# 4. Each agent node:
#    - Reads: {role}_task field
#    - Executes: Via MCP (mesh_execute)
#    - Writes: {role}_output, {role}_session_id
#    - Isolated: Each in separate Docker workspace
#    - Stateful: Session ID persisted via checkpointer
#
# 5. Session continuity:
#    - First invocation: Creates new session
#    - Subsequent invocations: Resumes session (if same thread_id)
#    - Checkpointer: Stores session_id → agent can resume context
#
# Cost Model:
#   - Fixed: $20/month Claude Pro subscription
#   - Per run: $0 (unlimited invocations)
#   - vs API: 90%+ savings at scale
#
# Repository Isolation:
#   - researcher: Executes in sample-app workspace
#   - writer: Executes in sample-api workspace
#   - reviewer: Executes in sample-infra workspace
#   - Each agent has separate file system, git repo, dependencies
