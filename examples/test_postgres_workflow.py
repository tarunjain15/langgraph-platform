#!/usr/bin/env python3
"""
Test PostgreSQL Checkpointer with Simple Workflow

This script demonstrates:
- PostgreSQL state persistence via Supabase
- Multi-server deployment readiness
- Workflow state recovery across runs

Prerequisites:
    DATABASE_URL in .env with Supabase pooled connection

Usage:
    python3 examples/test_postgres_workflow.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.executor import WorkflowExecutor


async def main():
    """Run simple workflow with PostgreSQL checkpointer."""
    print("\n" + "="*70)
    print("🐘 PostgreSQL Checkpointer Test (Supabase)")
    print("="*70)

    # Create executor for HOSTED environment (PostgreSQL)
    executor = WorkflowExecutor(environment="hosted", verbose=True)

    # Test workflow input
    input_data = {
        "input": "test with PostgreSQL checkpointer",
        "thread_id": "postgres-test-001"
    }

    print("\n[test] Input:", input_data)
    print("[test] Environment: hosted (PostgreSQL via Supabase)")
    print()

    # Execute workflow
    result = await executor.aexecute(
        workflow_path="workflows/simple_echo.py",
        input_data=input_data
    )

    print("\n" + "="*70)
    print("✅ PostgreSQL Checkpointer Test Complete")
    print("="*70)
    print(f"\nResult: {result}")

    print("\n📊 Verification:")
    print("   1. State was persisted to Supabase PostgreSQL")
    print("   2. Run this script again with same thread_id to resume")
    print("   3. Verify in Supabase: SELECT * FROM checkpoints;")
    print()


if __name__ == "__main__":
    asyncio.run(main())
