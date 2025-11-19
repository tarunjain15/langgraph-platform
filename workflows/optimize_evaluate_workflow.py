"""
Optimize-Evaluate Workflow

Autonomous iteration loop with two Claude Code agents:
- Optimizer: Modifies code for performance/correctness
- Evaluator: Runs tests and benchmarks

PATTERN: optimize → evaluate → check_convergence → (loop or end)

This workflow demonstrates:
- Multi-agent coordination with alternating execution
- Session continuity across iterations (R4 checkpointer)
- Repository isolation per agent (R5 Claude Code nodes)
- Observable iteration progress (R3 Langfuse)
- Autonomous convergence detection

USAGE:
    lgp run workflows/optimize_evaluate_workflow.py

INPUT STATE:
    {
        "target_file": "path/to/file.py",
        "optimization_goal": "Make function 2x faster while keeping tests passing",
        "max_iterations": 10
    }
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END


class OptimizeEvaluateState(TypedDict):
    """
    State schema for optimize-evaluate workflow.

    This state is checkpointed after each iteration, enabling:
    - Crash recovery mid-loop
    - Session continuity across agent invocations
    - Observable progress in Langfuse
    """
    # Input configuration
    target_file: str                # File being optimized (e.g., "algorithm.py")
    optimization_goal: str          # What to achieve (e.g., "2x faster, tests pass")
    max_iterations: int             # Stop condition

    # Iteration state
    iteration: int                  # Current iteration number
    converged: bool                 # Has goal been achieved?

    # Agent 1: Optimizer
    optimizer_task: str             # Task for optimizer agent
    optimizer_output: str           # Code modifications made
    optimizer_session_id: str       # Session continuity for optimizer

    # Agent 2: Evaluator
    evaluator_task: str             # Task for evaluator agent
    evaluator_output: str           # Test results and metrics
    evaluator_session_id: str       # Session continuity for evaluator

    # Convergence tracking
    test_results: Dict[str, Any]    # Latest test results (pass/fail, metrics)
    optimization_history: List[str] # What was tried in each iteration

    # Metadata
    current_step: str               # For observability


async def initialize_optimization(state: OptimizeEvaluateState) -> OptimizeEvaluateState:
    """
    Initialize the optimization loop.

    Sets up:
    - Iteration counter
    - Empty history
    - Initial test baseline

    Args:
        state: Input state with target_file and optimization_goal

    Returns:
        State with initialized iteration tracking
    """
    target_file = state.get("target_file", "")
    optimization_goal = state.get("optimization_goal", "")
    max_iterations = state.get("max_iterations", 10)

    return {
        **state,
        "iteration": 0,
        "converged": False,
        "optimization_history": [],
        "test_results": {"status": "not_run"},
        "current_step": "initialization",
        "max_iterations": max_iterations,
        "optimizer_task": f"""Initialize optimization for: {target_file}

Goal: {optimization_goal}

This is iteration 0. First, analyze the current code and identify optimization opportunities.
Create a baseline understanding of the code structure and performance characteristics.

DO NOT modify code yet. Just analyze and report what you found."""
    }


async def prepare_optimizer_task(state: OptimizeEvaluateState) -> OptimizeEvaluateState:
    """
    Prepare task for optimizer agent based on previous evaluation results.

    Args:
        state: Current workflow state

    Returns:
        State with optimizer_task field
    """
    iteration = state.get("iteration", 0)
    target_file = state.get("target_file", "")
    optimization_goal = state.get("optimization_goal", "")
    test_results = state.get("test_results", {})
    evaluator_output = state.get("evaluator_output", "No previous evaluation")
    optimization_history = state.get("optimization_history", [])

    history_summary = "\n".join([f"  - Iteration {i}: {change}" for i, change in enumerate(optimization_history)])

    task = f"""Optimize code in: {target_file}

Goal: {optimization_goal}

Current iteration: {iteration + 1}
Previous test results: {test_results.get('status', 'unknown')}

Evaluator feedback from last iteration:
{evaluator_output}

Optimization history:
{history_summary if history_summary else "  (no previous attempts)"}

TASK:
1. Read the current code in {target_file}
2. Based on the evaluator feedback, make ONE specific optimization
3. Ensure tests will still pass
4. Document what you changed and why

Focus on: {optimization_goal}
"""

    return {
        **state,
        "optimizer_task": task,
        "current_step": f"preparing_optimization_{iteration + 1}"
    }


async def prepare_evaluator_task(state: OptimizeEvaluateState) -> OptimizeEvaluateState:
    """
    Prepare task for evaluator agent to test optimizer's changes.

    Args:
        state: Current workflow state

    Returns:
        State with evaluator_task field
    """
    iteration = state.get("iteration", 0)
    target_file = state.get("target_file", "")
    optimization_goal = state.get("optimization_goal", "")
    optimizer_output = state.get("optimizer_output", "No optimizer output")

    task = f"""Evaluate optimized code in: {target_file}

Iteration: {iteration + 1}
Optimization goal: {optimization_goal}

What the optimizer changed:
{optimizer_output}

TASK:
1. Run all tests for {target_file}
2. Run performance benchmarks
3. Compare to baseline (if available)
4. Report results in structured format:
   - Tests: PASS/FAIL (which tests failed if any)
   - Performance: Current metrics vs baseline
   - Goal achieved: YES/NO (based on optimization_goal)
   - Recommendations: What to try next if goal not achieved

Be specific about numbers and metrics.
"""

    return {
        **state,
        "evaluator_task": task,
        "current_step": f"preparing_evaluation_{iteration + 1}"
    }


async def check_convergence(state: OptimizeEvaluateState) -> OptimizeEvaluateState:
    """
    Check if optimization goal has been achieved or max iterations reached.

    This node analyzes evaluator output to determine:
    - Has the goal been achieved? (converged = True)
    - Should we continue iterating? (converged = False, iteration < max)
    - Should we stop? (max iterations reached)

    Args:
        state: Current workflow state

    Returns:
        State with updated convergence status and iteration counter
    """
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 10)
    evaluator_output = state.get("evaluator_output", "")
    optimizer_output = state.get("optimizer_output", "")
    optimization_history = state.get("optimization_history", [])

    # Simple heuristic: Check if evaluator says "Goal achieved: YES"
    # In production, this would parse structured output
    goal_achieved = "goal achieved: yes" in evaluator_output.lower()

    # Update history
    new_history = optimization_history + [
        f"Changed: {optimizer_output[:100]}... | Result: {evaluator_output[:100]}..."
    ]

    # Safety: If no optimizer/evaluator output, we're in test mode without Claude Code nodes
    # Converge immediately to prevent infinite loop
    if not optimizer_output and not evaluator_output and iteration > 0:
        converged = True
        convergence_msg = "⚠️ No agent output detected. Workflow running without Claude Code nodes. Stopping."
    else:
        # Check convergence
        converged = goal_achieved or (iteration + 1 >= max_iterations)

        # Prepare convergence message
        if goal_achieved:
            convergence_msg = f"✅ Goal achieved in {iteration + 1} iterations!"
        elif iteration + 1 >= max_iterations:
            convergence_msg = f"⏱️ Max iterations ({max_iterations}) reached. Stopping."
        else:
            convergence_msg = f"🔄 Continuing... ({iteration + 1}/{max_iterations} iterations)"

    return {
        **state,
        "iteration": iteration + 1,
        "converged": converged,
        "optimization_history": new_history,
        "current_step": "checking_convergence",
        "convergence_message": convergence_msg
    }


def should_continue(state: OptimizeEvaluateState) -> str:
    """
    Conditional edge: Continue optimizing or end?

    Args:
        state: Current workflow state

    Returns:
        "continue" if should loop, "end" if converged
    """
    converged = state.get("converged", False)

    if converged:
        return "end"
    else:
        return "continue"


def create_workflow():
    """
    Create optimize-evaluate workflow with Claude Code node injection.

    Flow:
        initialize → prepare_optimizer → [optimizer_agent] →
        prepare_evaluator → [evaluator_agent] → check_convergence →
        (continue → prepare_optimizer) OR (end)

    Claude Code nodes are injected by executor at runtime.

    Returns:
        Uncompiled StateGraph
    """
    # Build graph
    graph = StateGraph(OptimizeEvaluateState)

    # Add nodes
    graph.add_node("initialize", initialize_optimization)
    graph.add_node("prepare_optimizer", prepare_optimizer_task)
    graph.add_node("prepare_evaluator", prepare_evaluator_task)
    graph.add_node("check_convergence", check_convergence)

    # Define flow
    # NOTE: Claude Code agent nodes will be injected by executor
    # The executor will create the complete flow:
    #   initialize → prepare_optimizer → optimizer_agent → prepare_evaluator → evaluator_agent → check_convergence

    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "prepare_optimizer")

    # Do NOT add edges that will be replaced by agent injection
    # The executor will add:
    #   - prepare_optimizer → optimizer_agent → prepare_evaluator
    #   - prepare_evaluator → evaluator_agent → check_convergence

    # Conditional edge: loop or end
    graph.add_conditional_edges(
        "check_convergence",
        should_continue,
        {
            "continue": "prepare_optimizer",  # Loop back
            "end": END                         # Terminate
        }
    )

    return graph


# Export uncompiled workflow for executor
app = create_workflow()


# Claude Code configuration for runtime injection
# The executor detects this and creates Claude Code nodes dynamically
claude_code_config = {
    "enabled": True,
    "agents": [
        {
            "role_name": "optimizer",
            "repository": "optimization-workspace",  # Isolated workspace for code changes
            "timeout": 120000,                       # 2 minutes per optimization attempt
            "inject_after": "prepare_optimizer",     # Injected after prepare_optimizer node
            "inject_before": "prepare_evaluator"     # Connects to prepare_evaluator
        },
        {
            "role_name": "evaluator",
            "repository": "evaluation-workspace",    # Isolated workspace for testing
            "timeout": 120000,                       # 2 minutes per evaluation
            "inject_after": "prepare_evaluator",     # Injected after prepare_evaluator node
            "inject_before": "check_convergence"     # Connects to check_convergence
        }
    ]
}
