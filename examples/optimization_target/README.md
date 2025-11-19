# Algorithm Optimization Example

This directory contains a sample optimization target for the `optimize_evaluate_workflow.py`.

## Files

- **algorithm.py**: Intentionally inefficient implementations of common algorithms
- **test_algorithm.py**: Test suite with correctness and performance tests

## Optimization Targets

### 1. find_duplicates()
- **Current**: O(n²) with nested loops
- **Target**: O(n) using set-based approach
- **Goal**: 10x faster while maintaining correctness

### 2. fibonacci()
- **Current**: Exponential time with naive recursion
- **Target**: O(n) with memoization or dynamic programming
- **Goal**: 100x faster for n=20

### 3. is_prime()
- **Current**: O(n) checking all numbers up to n
- **Target**: O(√n) checking only up to square root
- **Goal**: 10x faster for large primes

## Running Tests

```bash
cd examples/optimization_target
pytest test_algorithm.py -v
```

## Using with Optimize-Evaluate Workflow

```python
# Example invocation
input_state = {
    "target_file": "examples/optimization_target/algorithm.py",
    "optimization_goal": "Optimize find_duplicates to O(n) time complexity. All tests must pass.",
    "max_iterations": 5
}

# Run workflow
lgp run workflows/optimize_evaluate_workflow.py
```

## Expected Results

The workflow should:
1. **Iteration 1**: Analyze current implementation, identify O(n²) complexity
2. **Iteration 2**: Optimize to use set for O(n) lookup
3. **Iteration 3**: Run tests, verify correctness and performance improvement
4. **Convergence**: Goal achieved when tests pass and performance target met

## Observability

View the optimization progress in Langfuse:
- Each iteration visible as separate trace
- Optimizer and evaluator outputs captured
- Convergence metrics tracked
