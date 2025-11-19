# Optimize-Evaluate Pattern

## Overview

The **optimize-evaluate workflow** demonstrates autonomous AI-driven iteration loops using two coordinating Claude Code agents.

This pattern showcases the core value proposition of LangGraph Platform: **multi-agent coordination with session continuity**.

## The Pattern

```
Optimizer Agent → Evaluator Agent → Convergence Check → (loop or end)
```

### Agents

1. **Optimizer**: Modifies code based on goals and feedback
   - Repository: `optimization-workspace`
   - Receives: Previous evaluation results
   - Produces: Code modifications
   - Remembers: What was tried before (via session_id)

2. **Evaluator**: Tests code and measures performance
   - Repository: `evaluation-workspace`
   - Receives: Modified code
   - Produces: Test results and metrics
   - Remembers: Previous baselines (via session_id)

### State Flow

```python
OptimizeEvaluateState:
  target_file: str              # What to optimize
  optimization_goal: str        # What to achieve
  max_iterations: int           # Stop condition

  iteration: int                # Current iteration
  converged: bool               # Goal achieved?

  optimizer_session_id: str     # Agent 1 continuity
  evaluator_session_id: str     # Agent 2 continuity

  test_results: dict            # Latest metrics
  optimization_history: list    # What was tried
```

## Why This Demonstrates Platform Value

### Without the Platform

Manual coordination required at every step:
1. Developer modifies code
2. Developer runs tests
3. Developer analyzes results
4. Developer decides next optimization
5. **Repeat** (human in the loop every iteration)

### With the Platform

Autonomous delegation:
1. Define goal: "Make function 2x faster, all tests pass"
2. Start workflow
3. **Walk away**
4. Return to optimized code

### Platform Features Utilized

| Feature | How It's Used | Without Platform |
|---------|---------------|------------------|
| **R4 Checkpointing** | State persists across iterations | Manual state files |
| **R5 Claude Code Nodes** | Two isolated agent sessions | Manual context switching |
| **R3 Langfuse Tracing** | See which iteration stalled | Manual logging |
| **R2 API Runtime** | Delegate and walk away | Must stay in terminal |
| **R1 Hot Reload** | Tweak workflow during execution | Full restart |

## Usage

### 1. Basic Invocation

```bash
cd /Users/tarun/claude-workspace/workspace/langgraph-platform

# Run workflow in experiment mode
lgp run workflows/optimize_evaluate_workflow.py
```

### 2. With Specific Target

```python
# Input state
input_data = {
    "target_file": "examples/optimization_target/algorithm.py",
    "optimization_goal": "Optimize find_duplicates to O(n). All tests must pass.",
    "max_iterations": 5,
    "thread_id": "optimization-session-001"  # For session continuity
}
```

### 3. Via API (Hosted Mode)

```bash
# Start API server
lgp serve workflows/optimize_evaluate_workflow.py

# Invoke via REST
curl -X POST http://localhost:8000/workflows/optimize_evaluate_workflow/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "target_file": "examples/optimization_target/algorithm.py",
    "optimization_goal": "Optimize fibonacci to O(n) using memoization",
    "max_iterations": 5,
    "thread_id": "optimization-session-002"
  }'
```

## Observability

### Langfuse Dashboard

Each iteration creates observable traces:

```
Trace: optimize-evaluate-session-001
├── Span: initialize (0.1s)
├── Span: iteration-1
│   ├── Span: prepare_optimizer (0.2s)
│   ├── Span: optimizer_agent (45.3s) ← Claude Code execution
│   ├── Span: prepare_evaluator (0.1s)
│   ├── Span: evaluator_agent (12.7s) ← Test execution
│   └── Span: check_convergence (0.1s)
├── Span: iteration-2
│   └── ...
└── Final: converged=True, iterations=3
```

### Metadata Tags

- `workflow:optimize-evaluate`
- `iteration:N`
- `agent:optimizer` / `agent:evaluator`
- `converged:true` / `converged:false`

## Example: Optimizing find_duplicates

### Initial State (Iteration 0)

```python
def find_duplicates(numbers):
    duplicates = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j]:
                if numbers[i] not in duplicates:
                    duplicates.append(numbers[i])
    return duplicates

# Complexity: O(n²)
# Performance: 0.5s for 1000 numbers
```

### Iteration 1: Optimizer Analysis

```
Optimizer output:
"Identified O(n²) nested loops. Will optimize using set for O(n) lookup.
Change: Replace nested loops with single pass using seen set."
```

### Iteration 2: Evaluator Feedback

```
Evaluator output:
"Tests: PASS (all 6 tests passing)
Performance: 0.05s for 1000 numbers (10x improvement)
Goal achieved: YES (O(n) complexity, tests pass)"
```

### Convergence

```
Iteration 2: converged=True
Final result: Optimized function with O(n) complexity
```

## Advanced Usage

### Custom Convergence Logic

Modify `check_convergence` to add custom goal detection:

```python
async def check_convergence(state):
    evaluator_output = state.get("evaluator_output", "")

    # Parse structured metrics
    metrics = parse_metrics(evaluator_output)

    # Custom goal: 2x speedup AND tests pass
    goal_achieved = (
        metrics["speedup"] >= 2.0 and
        metrics["tests_passed"] == True
    )

    return {**state, "converged": goal_achieved}
```

### Multiple Optimization Targets

Run parallel workflows for different files:

```bash
# Session 1: Optimize algorithm.py
lgp run workflows/optimize_evaluate_workflow.py --thread-id opt-algo

# Session 2: Optimize data_processing.py
lgp run workflows/optimize_evaluate_workflow.py --thread-id opt-data
```

Each session maintains independent state via R4 checkpointer.

## Pattern Generalization

The optimize-evaluate pattern generalizes to any alternating coordination:

### Content Creation

- **Agent 1**: Writer (creates content)
- **Agent 2**: Reviewer (provides feedback)
- **Loop**: Until quality threshold met

### Software Development

- **Agent 1**: Implementer (writes code)
- **Agent 2**: Tester (runs tests, reports bugs)
- **Loop**: Until all tests pass

### Research & Analysis

- **Agent 1**: Researcher (gathers data)
- **Agent 2**: Analyzer (finds insights)
- **Loop**: Until research question answered

## Platform Dependencies

This workflow **requires**:

- ✅ R4: Checkpointer (state persistence across iterations)
- ✅ R5: Claude Code nodes (two isolated agent sessions)
- ✅ R3: Langfuse integration (iteration observability)
- ✅ R2: API server (optional, for remote invocation)
- ✅ R1: Hot reload (optional, for workflow tweaking)

Without the platform, you'd manually implement all coordination infrastructure.

## Troubleshooting

### Workflow Doesn't Loop

**Issue**: Converges after 1 iteration

**Fix**: Check `should_continue` logic. Ensure `converged=False` until goal actually achieved.

### Agent Sessions Don't Persist

**Issue**: Agent "forgets" previous work

**Fix**: Verify checkpointer is configured:
```yaml
# config/experiment.yaml
checkpointer:
  type: sqlite
  path: ./checkpoints.db
  async: true
```

### Langfuse Traces Missing

**Issue**: No traces in dashboard

**Fix**: Set environment variables:
```bash
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

## Next Steps

1. **Run the Example**: Try optimizing `algorithm.py`
2. **Modify Goals**: Change optimization targets
3. **Add Agents**: Extend to 3+ agent coordination
4. **Customize Convergence**: Add domain-specific goal detection

## Related Patterns

- **Research → Write → Review**: Content creation pipeline
- **Design → Implement → Test**: Software development cycle
- **Propose → Evaluate → Refine**: Decision-making loop

All enabled by LangGraph Platform's multi-agent coordination primitives.
