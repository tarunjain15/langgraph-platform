#!/usr/bin/env python3
"""
Test Suite for Constraint Enforcement (R13.4)

Validates WITNESS_AUTOMATION and CONSTRAINT_NON_NEGOTIABILITY at runtime:
- Constraints verified automatically before every execution
- Violations logged to alert dashboard
- Execution aborted on constraint failure
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock

from workers.factory import WorkerFactory
from workers.enforcement.registry import WitnessRegistry
from workers.definitions.schema import (
    WorkerDefinition,
    WorkerIdentity,
    WorkerRuntime,
    WorkerConstraint
)


class TestConstraintViolationDetection:
    """Test constraint violation detection and warnings"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.fixture
    def definition_with_file_size_constraint(self):
        """Create test definition with file size constraint"""
        return WorkerDefinition(
            worker_id="test_file_size_worker",
            identity=WorkerIdentity(
                name="File Size Test Worker",
                system_prompt="Test worker with file size constraint",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="python:3.11-slim",
                workspace_template="/tmp/test_workspace/{user_journey_id}",
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

    @pytest.mark.asyncio
    async def test_constraint_violation_detected_in_void(
        self,
        definition_with_file_size_constraint
    ):
        """
        Test CONSTRAINT_NON_NEGOTIABILITY

        Verify:
        1. Worker has max_file_size constraint
        2. Attempt to write file exceeding limit
        3. void() returns warnings (constraint violated)
        4. Warnings contain file size violation message
        """
        worker = await WorkerFactory.spawn(
            definition=definition_with_file_size_constraint,
            user_journey_id="test_constraint_violation",
            isolation_level="process"
        )

        # Attempt to write large file (exceeds 1MB limit)
        large_content = "x" * 2_000_000  # 2MB

        void_result = await worker.void({
            "type": "write",
            "target": "large.txt",
            "content": large_content
        })

        # Verify: void() detected violation
        assert len(void_result.warnings) > 0, \
            "Constraint violation not detected"

        assert "File size" in str(void_result.warnings), \
            "File size constraint not triggered"

        # Verify warning contains expected message
        assert "2000000" in str(void_result.warnings), \
            "Warning should include actual file size"

        assert "1000000" in str(void_result.warnings), \
            "Warning should include max file size limit"

        print(f"✓ Constraint violation detected: {void_result.warnings}")

    @pytest.mark.asyncio
    async def test_valid_action_passes_constraint(
        self,
        definition_with_file_size_constraint
    ):
        """
        Test constraint passes for valid actions

        Verify:
        1. Worker has max_file_size constraint
        2. Write small file (under limit)
        3. void() returns no warnings
        """
        worker = await WorkerFactory.spawn(
            definition=definition_with_file_size_constraint,
            user_journey_id="test_valid_action",
            isolation_level="process"
        )

        # Write small file (under 1MB limit)
        small_content = "hello world"

        void_result = await worker.void({
            "type": "write",
            "target": "small.txt",
            "content": small_content
        })

        # Verify: No warnings (constraint passed)
        assert len(void_result.warnings) == 0, \
            "Valid action should not trigger warnings"

        print("✓ Valid action passed constraint checks")


class TestWitnessAutomation:
    """Test automatic witness invocation (WITNESS_AUTOMATION)"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers and registry after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.mark.asyncio
    async def test_witness_called_automatically(self):
        """
        Test WITNESS_AUTOMATION constraint

        Verify witnesses called automatically (not manually)

        Flow:
        1. Register mock witness function
        2. Create worker with constraint using mock witness
        3. Call worker.void() WITHOUT manually calling witness
        4. Verify witness was called automatically by platform
        """
        # Track witness calls
        witness_calls = []

        async def mock_witness_auto(action):
            """Mock witness that tracks calls"""
            witness_calls.append(action)
            return []  # No warnings

        # Register mock witness
        WitnessRegistry.register("mock_witness_auto", mock_witness_auto)

        # Create worker with mock witness constraint
        definition = WorkerDefinition(
            worker_id="test_auto_worker",
            identity=WorkerIdentity(
                name="Auto Witness Test Worker",
                system_prompt="Test worker for automatic witness invocation",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="python:3.11-slim",
                workspace_template="/tmp/test_workspace/{user_journey_id}",
                tools=["read", "write"],
                session_persistence=True
            ),
            constraints=[
                WorkerConstraint(
                    constraint_id="test_auto_constraint",
                    witness="mock_witness_auto",
                    value="automatic",
                    feedback="log"
                )
            ],
            trust_level="sandboxed"
        )

        worker = await WorkerFactory.spawn(
            definition=definition,
            user_journey_id="test_auto_journey",
            isolation_level="process"
        )

        # Call void() WITHOUT manually calling witness
        # This is the key - witness should be called automatically
        test_action = {"type": "test_action", "target": "test.txt"}
        void_result = await worker.void(test_action)

        # Verify: Witness was called automatically
        assert len(witness_calls) == 1, \
            "WITNESS_AUTOMATION violated: Witness not called automatically"

        assert witness_calls[0] == test_action, \
            "Witness received wrong action"

        print("✓ Witness called automatically by platform")
        print(f"  Witness received action: {witness_calls[0]}")

    @pytest.mark.asyncio
    async def test_witness_called_for_every_action(self):
        """
        Test witness called for every void() invocation

        Verify:
        1. Multiple void() calls
        2. Witness called each time
        3. Call count matches action count
        """
        witness_calls = []

        async def counting_witness(action):
            witness_calls.append(action)
            return []

        WitnessRegistry.register("counting_witness", counting_witness)

        definition = WorkerDefinition(
            worker_id="test_counting_worker",
            identity=WorkerIdentity(
                name="Counting Witness Worker",
                system_prompt="Test worker",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="python:3.11-slim",
                workspace_template="/tmp/test_workspace/{user_journey_id}",
                tools=["read", "write"],
                session_persistence=True
            ),
            constraints=[
                WorkerConstraint(
                    constraint_id="count_constraint",
                    witness="counting_witness",
                    value="count",
                    feedback="log"
                )
            ],
            trust_level="sandboxed"
        )

        worker = await WorkerFactory.spawn(
            definition=definition,
            user_journey_id="test_counting_journey",
            isolation_level="process"
        )

        # Execute multiple actions
        actions = [
            {"type": "action_1"},
            {"type": "action_2"},
            {"type": "action_3"}
        ]

        for action in actions:
            await worker.void(action)

        # Verify: Witness called for each action
        assert len(witness_calls) == len(actions), \
            "Witness not called for every action"

        print(f"✓ Witness called {len(witness_calls)} times for {len(actions)} actions")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
