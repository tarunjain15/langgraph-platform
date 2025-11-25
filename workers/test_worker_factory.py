#!/usr/bin/env python3
"""
Test Suite for Worker Factory (R13.2)

Validates spawn/kill/resume functionality and JOURNEY_ISOLATION constraint.
"""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path

from workers.factory import WorkerFactory
from workers.definitions.schema import WorkerDefinition, WorkerIdentity, WorkerRuntime


class TestWorkerFactory:
    """Test Worker Factory lifecycle management"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.fixture
    def example_definition_path(self):
        """Path to example worker definition"""
        return "workers/definitions/examples/research_assistant_v1.yaml"

    @pytest.fixture
    def test_definition(self):
        """Create test worker definition"""
        return WorkerDefinition(
            worker_id="test_worker_v1",
            identity=WorkerIdentity(
                name="Test Worker",
                system_prompt="Test worker for factory tests",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="test:latest",
                workspace_template="/tmp/test_workspace/{user_journey_id}",
                tools=["read", "write"],
                session_persistence=True
            ),
            trust_level="sandboxed"
        )

    @pytest.mark.asyncio
    async def test_spawn_creates_worker_instance(self, test_definition):
        """Spawn creates worker with isolated workspace"""
        # Spawn worker
        worker = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_001"
        )

        # Verify worker exists
        assert worker is not None
        assert worker.worker_id == "test_worker_v1_test_journey_001"
        assert worker.user_journey_id == "test_journey_001"
        assert worker.workspace_path == "/tmp/test_workspace/test_journey_001"

    @pytest.mark.asyncio
    async def test_spawn_loads_definition_from_yaml(self, example_definition_path):
        """Spawn can load definition from YAML file"""
        # Spawn from YAML path
        worker = await WorkerFactory.spawn(
            definition=example_definition_path,
            user_journey_id="test_journey_002"
        )

        # Verify worker loaded definition
        assert worker is not None
        assert worker.definition.worker_id == "research_assistant_v1"
        assert worker.definition.identity.name == "Research Assistant"

    @pytest.mark.asyncio
    async def test_spawn_enforces_journey_isolation(self, test_definition):
        """JOURNEY_ISOLATION: Cannot spawn multiple workers for same journey"""
        # Spawn first worker
        worker1 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_003"
        )

        # Attempt to spawn second worker for same journey
        with pytest.raises(ValueError, match="JOURNEY_ISOLATION violation"):
            worker2 = await WorkerFactory.spawn(
                definition=test_definition,
                user_journey_id="test_journey_003"  # Same journey ID
            )

    @pytest.mark.asyncio
    async def test_get_retrieves_existing_worker(self, test_definition):
        """Get retrieves spawned worker instance"""
        # Spawn worker
        worker = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_004"
        )

        # Retrieve worker
        retrieved = WorkerFactory.get("test_journey_004")

        # Verify same instance
        assert retrieved is worker
        assert retrieved.worker_id == worker.worker_id

    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent_journey(self):
        """Get returns None for journey without worker"""
        # Get nonexistent worker
        worker = WorkerFactory.get("nonexistent_journey")

        # Verify None
        assert worker is None

    @pytest.mark.asyncio
    async def test_kill_terminates_worker(self, test_definition):
        """Kill terminates worker and removes from registry"""
        # Spawn worker
        worker = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_005"
        )

        # Verify worker exists
        assert WorkerFactory.get("test_journey_005") is not None

        # Kill worker
        await WorkerFactory.kill("test_journey_005")

        # Verify worker removed
        assert WorkerFactory.get("test_journey_005") is None

    @pytest.mark.asyncio
    async def test_kill_raises_for_nonexistent_journey(self):
        """Kill raises KeyError for nonexistent journey"""
        # Attempt to kill nonexistent worker
        with pytest.raises(KeyError):
            await WorkerFactory.kill("nonexistent_journey")

    @pytest.mark.asyncio
    async def test_resume_returns_existing_worker(self, test_definition):
        """Resume returns existing worker instance"""
        # Spawn worker
        worker = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_006"
        )

        # Resume worker
        resumed = await WorkerFactory.resume("test_journey_006")

        # Verify same instance
        assert resumed is worker
        assert resumed.worker_id == worker.worker_id

    @pytest.mark.asyncio
    async def test_resume_raises_for_nonexistent_journey(self):
        """Resume raises ValueError for nonexistent journey"""
        # Attempt to resume nonexistent worker
        with pytest.raises(ValueError, match="Cannot resume"):
            await WorkerFactory.resume("nonexistent_journey")

    @pytest.mark.asyncio
    async def test_list_active_shows_all_workers(self, test_definition):
        """List active shows all spawned workers"""
        # Spawn multiple workers
        worker1 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_007"
        )
        worker2 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_008"
        )

        # List active
        active = WorkerFactory.list_active()

        # Verify both workers listed
        assert len(active) == 2
        assert "test_journey_007" in active
        assert "test_journey_008" in active
        assert active["test_journey_007"] == worker1.worker_id
        assert active["test_journey_008"] == worker2.worker_id

    @pytest.mark.asyncio
    async def test_kill_all_terminates_all_workers(self, test_definition):
        """Kill all terminates all workers"""
        # Spawn multiple workers
        worker1 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_009"
        )
        worker2 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_010"
        )

        # Verify workers exist
        assert len(WorkerFactory.list_active()) == 2

        # Kill all
        await WorkerFactory.kill_all()

        # Verify all workers removed
        assert len(WorkerFactory.list_active()) == 0


class TestWorkerInstance:
    """Test Worker instance carries definition and journey context"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.fixture
    def test_definition(self):
        """Create test worker definition with constraints"""
        from workers.definitions.schema import WorkerConstraint

        return WorkerDefinition(
            worker_id="test_worker_with_constraints",
            identity=WorkerIdentity(
                name="Test Worker",
                system_prompt="Test worker",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="test:latest",
                workspace_template="/tmp/test/{user_journey_id}",
                tools=["read"],
                session_persistence=True
            ),
            constraints=[
                WorkerConstraint(
                    constraint_id="test_constraint",
                    witness="response_time_under_5s",
                    feedback="Too slow",
                    value="5.0"
                )
            ],
            trust_level="sandboxed"
        )

    @pytest.mark.asyncio
    async def test_worker_carries_definition(self, test_definition):
        """Worker instance carries complete definition"""
        # Spawn worker
        worker = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_011"
        )

        # Verify definition carried
        assert worker.definition == test_definition
        assert worker.definition.worker_id == "test_worker_with_constraints"
        assert len(worker.definition.constraints) == 1

    @pytest.mark.asyncio
    async def test_worker_carries_journey_context(self, test_definition):
        """Worker instance carries user journey context"""
        # Spawn worker
        worker = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_012"
        )

        # Verify journey context
        assert worker.user_journey_id == "test_journey_012"
        assert worker.workspace_path == "/tmp/test/test_journey_012"

    @pytest.mark.asyncio
    async def test_worker_has_isolated_workspace(self, test_definition):
        """Each worker has unique isolated workspace"""
        # Spawn multiple workers
        worker1 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_013"
        )
        worker2 = await WorkerFactory.spawn(
            definition=test_definition,
            user_journey_id="test_journey_014"
        )

        # Verify different workspaces
        assert worker1.workspace_path != worker2.workspace_path
        assert "test_journey_013" in worker1.workspace_path
        assert "test_journey_014" in worker2.workspace_path


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
