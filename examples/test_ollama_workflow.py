#!/usr/bin/env python3
"""
Test script for Ollama-powered optimize-evaluate workflow (R8 Multi-Provider).

This script demonstrates:
- $0 cost workflow execution with self-hosted Ollama
- Multi-provider agency (Ollama instead of Claude Code)
- Langfuse tracing with $0.00 cost attribution
- Offline capability after model download

Prerequisites:
    1. Ollama installed and running:
       brew install ollama  # macOS
       ollama serve

    2. Model downloaded:
       ollama pull llama3.2

    3. Langfuse credentials in .env:
       LANGFUSE_PUBLIC_KEY=pk-...
       LANGFUSE_SECRET_KEY=sk-...

Usage:
    python3 examples/test_ollama_workflow.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.executor import WorkflowExecutor


async def main():
    """Run Ollama workflow test."""
    print("\n" + "="*70)
    print("🦙 Ollama Workflow Test - R8 Multi-Provider Agency")
    print("="*70)

    # Create executor for experiment environment
    executor = WorkflowExecutor(environment="experiment", verbose=True)

    # Workflow input
    input_data = {
        "target_file": "optimize-test/slow_code.py",
        "optimization_goal": "Optimize both find_duplicates and count_frequency to O(n) time complexity. All tests including performance tests must pass.",
        "max_iterations": 1,  # Single iteration for testing
        "thread_id": "ollama-test-001"
    }

    print("\n[test] Input:", input_data)
    print()

    # Execute workflow
    result = await executor.aexecute(
        workflow_path="workflows/optimize_evaluate_ollama.py",
        input_data=input_data
    )

    print("\n" + "="*70)
    print("✅ Ollama Workflow Test Complete")
    print("="*70)
    print(f"\nIteration: {result.get('iteration', 0)}")
    print(f"Converged: {result.get('converged', False)}")
    print(f"Writer Output: {result.get('writer_output', 'N/A')[:200]}...")
    print(f"Validator Output: {result.get('validator_output', 'N/A')[:200]}...")

    print("\n💰 Cost Analysis:")
    print("   Ollama (self-hosted): $0.00")
    print("   vs Claude Code cloud: ~$0.05")
    print("   Savings: 100%")

    print("\n📊 Next Steps:")
    print("   1. Visit https://cloud.langfuse.com")
    print("   2. Filter by metadata.provider = 'ollama'")
    print("   3. Verify cost shows as $0.00")
    print("   4. Compare with Claude Code workflow traces")
    print()


if __name__ == "__main__":
    asyncio.run(main())
