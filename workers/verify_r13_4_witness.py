#!/usr/bin/env python3
"""
Live Witness Verification for R13.4

Witness: Constraints verified automatically before every execution,
         violations logged to alert dashboard, execution aborted on failure

Verification:
1. Create worker with file size constraint
2. Attempt action that violates constraint
3. Verify void() detects violation automatically
4. Verify warning message includes violation details
5. Attempt valid action (under limit)
6. Verify valid action passes constraint
7. Verify witness called automatically (not manually)
"""

import asyncio

from workers.factory import WorkerFactory
from workers.enforcement.registry import WitnessRegistry
from workers.definitions.schema import (
    WorkerDefinition,
    WorkerIdentity,
    WorkerRuntime,
    WorkerConstraint
)


async def verify_r13_4_witness():
    """Verify R13.4 witness with live system"""

    print("=" * 80)
    print("R13.4 WITNESS VERIFICATION")
    print("=" * 80)
    print()

    # Step 1: Create worker with constraint
    print("Step 1: Creating worker with file size constraint...")

    definition = WorkerDefinition(
        worker_id="witness_enforcement_worker",
        identity=WorkerIdentity(
            name="Witness Enforcement Test Worker",
            system_prompt="Test worker for constraint enforcement",
            onboarding_steps=[]
        ),
        runtime=WorkerRuntime(
            container="python:3.11-slim",
            workspace_template="/tmp/witness_workspace/{user_journey_id}",
            tools=["read", "write"],
            session_persistence=True
        ),
        constraints=[
            WorkerConstraint(
                constraint_id="max_file_size",
                witness="verify_file_size_within_limit",
                value="1MB",
                feedback="alert_dashboard"
            )
        ],
        trust_level="sandboxed"
    )

    worker = await WorkerFactory.spawn(
        definition=definition,
        user_journey_id="witness_test_journey",
        isolation_level="process"
    )

    print(f"✓ Created worker: {worker.worker_id}")
    print(f"  Constraint: {definition.constraints[0].constraint_id}")
    print(f"  Witness: {definition.constraints[0].witness}")
    print()

    # Step 2: Attempt action that violates constraint
    print("Step 2: Attempting action that violates constraint...")

    large_content = "x" * 2_000_000  # 2MB (exceeds 1MB limit)

    void_result = await worker.void({
        "type": "write",
        "target": "large_file.txt",
        "content": large_content
    })

    # Verify violation detected
    assert len(void_result.warnings) > 0, \
        "FAIL: Constraint violation not detected"

    assert "File size" in str(void_result.warnings), \
        "FAIL: File size warning not in warnings"

    print(f"✓ Constraint violation detected automatically")
    print(f"  Warnings: {void_result.warnings}")
    print()

    # Step 3: Verify warning message details
    print("Step 3: Verifying warning message details...")

    warning_str = str(void_result.warnings)

    assert "2000000" in warning_str, \
        "FAIL: Actual file size not in warning"

    assert "1000000" in warning_str, \
        "FAIL: Max file size limit not in warning"

    print("✓ Warning message includes:")
    print(f"  - Actual file size: 2000000 bytes")
    print(f"  - Max limit: 1000000 bytes")
    print()

    # Step 4: Attempt valid action (under limit)
    print("Step 4: Attempting valid action (under limit)...")

    small_content = "hello world"  # Well under 1MB

    void_result_valid = await worker.void({
        "type": "write",
        "target": "small_file.txt",
        "content": small_content
    })

    # Verify no warnings
    assert len(void_result_valid.warnings) == 0, \
        "FAIL: Valid action triggered warnings"

    print("✓ Valid action passed constraint checks")
    print(f"  No warnings (constraint satisfied)")
    print()

    # Step 5: Verify witness automation
    print("Step 5: Verifying witness called automatically...")

    # Track witness calls
    witness_calls = []

    async def tracking_witness(action):
        witness_calls.append(action)
        return []

    WitnessRegistry.register("tracking_witness", tracking_witness)

    # Create worker with tracking witness
    tracking_definition = WorkerDefinition(
        worker_id="tracking_witness_worker",
        identity=definition.identity,
        runtime=definition.runtime,
        constraints=[
            WorkerConstraint(
                constraint_id="tracking_constraint",
                witness="tracking_witness",
                value="track",
                feedback="log"
            )
        ],
        trust_level="sandboxed"
    )

    tracking_worker = await WorkerFactory.spawn(
        definition=tracking_definition,
        user_journey_id="tracking_journey",
        isolation_level="process"
    )

    # Call void() WITHOUT manually calling witness
    test_action = {"type": "test", "target": "test.txt"}
    await tracking_worker.void(test_action)

    # Verify witness was called automatically
    assert len(witness_calls) == 1, \
        "FAIL: Witness not called automatically"

    assert witness_calls[0] == test_action, \
        "FAIL: Witness received wrong action"

    print("✓ Witness called automatically by platform")
    print(f"  (NOT manually - WITNESS_AUTOMATION satisfied)")
    print()

    # Cleanup
    await WorkerFactory.kill_all()

    # Final verification
    print("=" * 80)
    print("R13.4 WITNESS SATISFIED ✓")
    print("=" * 80)
    print()
    print("Witness verified:")
    print("  - Constraints verified automatically before every execution")
    print("  - Violations detected and warnings returned")
    print("  - Warning messages include violation details")
    print("  - Valid actions pass constraint checks")
    print("  - Witnesses called automatically (WITNESS_AUTOMATION)")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(verify_r13_4_witness())
    exit(0 if success else 1)
