#!/usr/bin/env python3
"""
Live Witness Verification for R13.2

Witness: WorkerFactory.spawn() creates worker instance from definition,
         instance has isolated workspace, constraints loaded

Verification:
1. Load worker definition from YAML
2. Spawn worker instance for test journey
3. Verify worker carries definition (identity, constraints, runtime)
4. Verify worker has isolated workspace path
5. Verify JOURNEY_ISOLATION constraint (reject duplicate journey)
6. Clean up worker
"""

import asyncio
from pathlib import Path

from workers.factory import WorkerFactory
from workers.definitions.loader import load_worker_definition


async def verify_r13_2_witness():
    """Verify R13.2 witness with live system"""

    print("=" * 80)
    print("R13.2 WITNESS VERIFICATION")
    print("=" * 80)
    print()

    # Step 1: Load worker definition from YAML
    print("Step 1: Loading worker definition from YAML...")
    definition_path = "workers/definitions/examples/research_assistant_v1.yaml"
    definition = load_worker_definition(definition_path)
    print(f"✓ Loaded definition: {definition.worker_id}")
    print(f"  - Identity: {definition.identity.name}")
    print(f"  - Constraints: {len(definition.constraints)} loaded")
    print(f"  - Trust level: {definition.trust_level}")
    print()

    # Step 2: Spawn worker instance for test journey
    print("Step 2: Spawning worker instance for test journey...")
    user_journey_id = "witness_test_journey_001"
    worker = await WorkerFactory.spawn(
        definition=definition,
        user_journey_id=user_journey_id
    )
    print(f"✓ Spawned worker: {worker.worker_id}")
    print()

    # Step 3: Verify worker carries definition
    print("Step 3: Verifying worker carries definition...")
    assert worker.definition == definition, "Worker should carry original definition"
    assert worker.definition.worker_id == "research_assistant_v1", "Worker ID mismatch"
    assert worker.definition.identity.name == "Research Assistant", "Identity name mismatch"
    assert len(worker.definition.constraints) == 3, "Constraints not loaded"
    assert worker.definition.trust_level == "sandboxed", "Trust level mismatch"
    print("✓ Worker carries complete definition:")
    print(f"  - Worker ID: {worker.definition.worker_id}")
    print(f"  - Identity: {worker.definition.identity.name}")
    print(f"  - Constraints: {len(worker.definition.constraints)}")
    print(f"  - Trust level: {worker.definition.trust_level}")
    print()

    # Step 4: Verify worker has isolated workspace path
    print("Step 4: Verifying worker has isolated workspace...")
    assert worker.user_journey_id == user_journey_id, "Journey ID mismatch"
    assert user_journey_id in worker.workspace_path, "Workspace not isolated per journey"
    print("✓ Worker has isolated workspace:")
    print(f"  - User journey ID: {worker.user_journey_id}")
    print(f"  - Workspace path: {worker.workspace_path}")
    print()

    # Step 5: Verify JOURNEY_ISOLATION constraint
    print("Step 5: Verifying JOURNEY_ISOLATION constraint...")
    try:
        duplicate_worker = await WorkerFactory.spawn(
            definition=definition,
            user_journey_id=user_journey_id  # Same journey ID
        )
        print("✗ FAILED: Allowed duplicate worker for same journey!")
        await WorkerFactory.kill_all()
        return False
    except ValueError as e:
        if "JOURNEY_ISOLATION violation" in str(e):
            print("✓ JOURNEY_ISOLATION enforced:")
            print(f"  - Error message: {str(e)[:80]}...")
        else:
            print(f"✗ FAILED: Wrong error: {e}")
            await WorkerFactory.kill_all()
            return False
    print()

    # Step 6: Clean up worker
    print("Step 6: Cleaning up worker...")
    await WorkerFactory.kill(user_journey_id)
    assert WorkerFactory.get(user_journey_id) is None, "Worker not cleaned up"
    print("✓ Worker cleaned up successfully")
    print()

    # Final verification
    print("=" * 80)
    print("R13.2 WITNESS SATISFIED ✓")
    print("=" * 80)
    print()
    print("Witness verified:")
    print("  - WorkerFactory.spawn() creates worker instance from definition")
    print("  - Worker instance has isolated workspace per journey")
    print("  - Worker carries constraints loaded from definition")
    print("  - JOURNEY_ISOLATION constraint enforced (one worker per journey)")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(verify_r13_2_witness())
    exit(0 if success else 1)
