#!/usr/bin/env python3
"""
Witness Checkpoint Creation in Supabase

This script creates FRESH checkpoint data with timestamped thread_id
so you can witness new data appearing in Supabase dashboard in real-time.

Usage:
    python3 examples/witness_checkpoint_creation.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.executor import WorkflowExecutor


async def main():
    """Run workflow with timestamped thread_id to witness new checkpoint creation."""

    # Create unique thread_id with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    thread_id = f"witness-{timestamp}"

    print("\n" + "="*70)
    print("🔍 Witness Checkpoint Creation in Supabase")
    print("="*70)
    print()
    print(f"🆔 Thread ID: {thread_id}")
    print("📍 Environment: hosted (PostgreSQL via Supabase)")
    print()
    print("=" * 70)
    print("WITNESS STEPS:")
    print("=" * 70)
    print()
    print("1. Open Supabase Dashboard:")
    print("   https://supabase.com/dashboard/project/fjvsrzppgykdrtnrwqsr")
    print()
    print("2. Navigate to: Table Editor → checkpoints table")
    print()
    print("3. Filter by thread_id:")
    print(f"   thread_id = '{thread_id}'")
    print()
    print("4. Watch for NEW row appearing during workflow execution")
    print()
    print("=" * 70)
    print()

    input("Press ENTER when ready to create checkpoint data...")
    print()

    # Create executor for HOSTED environment (PostgreSQL)
    executor = WorkflowExecutor(environment="hosted", verbose=True)

    # Test workflow input with timestamped thread_id
    input_data = {
        "input": f"Witness checkpoint creation at {timestamp}",
        "thread_id": thread_id
    }

    print("[witness] Creating checkpoint...")
    print()

    # Execute workflow
    result = await executor.aexecute(
        workflow_path="workflows/simple_echo.py",
        input_data=input_data
    )

    print()
    print("=" * 70)
    print("✅ Checkpoint Created!")
    print("=" * 70)
    print()
    print(f"Result: {result}")
    print()
    print("=" * 70)
    print("VERIFICATION STEPS:")
    print("=" * 70)
    print()
    print("1. Go to Supabase Table Editor → checkpoints")
    print()
    print("2. Run this query in SQL Editor:")
    print()
    print(f"   SELECT thread_id, checkpoint_id, created_at")
    print(f"   FROM checkpoints")
    print(f"   WHERE thread_id = '{thread_id}'")
    print(f"   ORDER BY created_at DESC;")
    print()
    print("3. You should see checkpoint data with:")
    print(f"   - thread_id: {thread_id}")
    print("   - checkpoint_id: (auto-generated UUID)")
    print("   - created_at: (timestamp just now)")
    print()
    print("4. Click on the row to see full checkpoint blob (state data)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
