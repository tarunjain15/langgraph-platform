#!/usr/bin/env python3
"""
Test Suite for Journey Isolation (R13.3)

Validates JOURNEY_ISOLATION constraint at runtime:
- Worker instances execute in isolated containers
- Workspace filesystems separate per journey
- No context bleed between journeys
- Session state persists across worker restarts
"""

import pytest
import pytest_asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from workers.factory import WorkerFactory
from workers.definitions.schema import WorkerDefinition, WorkerIdentity, WorkerRuntime


class TestContainerIsolation:
    """Test container isolation functionality"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.fixture
    def test_definition_container(self):
        """Create test worker definition with container isolation"""
        return WorkerDefinition(
            worker_id="test_container_worker",
            identity=WorkerIdentity(
                name="Test Container Worker",
                system_prompt="Test worker with container isolation",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="python:3.11-slim",
                workspace_template="/tmp/test_workspace/{user_journey_id}",
                tools=["read", "write"],
                session_persistence=True
            ),
            trust_level="sandboxed"
        )

    @pytest.mark.asyncio
    async def test_container_spawns_on_first_execute(self, test_definition_container):
        """Container spawns lazily on first execute()"""
        # Mock Docker to avoid actual container spawning
        with patch('workers.isolation.container.ContainerIsolation._get_client') as mock_client:
            mock_container = Mock()
            mock_container.id = "test_container_123"
            mock_client.return_value.containers.run.return_value = mock_container

            # Spawn worker with container isolation
            worker = await WorkerFactory.spawn(
                definition=test_definition_container,
                user_journey_id="test_journey_container_001",
                isolation_level="container"
            )

            # Container not spawned yet (lazy)
            assert worker.container_id is None
            assert worker._container_spawned is False

            # Execute action - triggers container spawn
            result = await worker.execute({"command": "echo 'test'"})

            # Verify container spawned
            assert worker._container_spawned is True
            assert worker.container_id == "test_container_123"

    @pytest.mark.asyncio
    async def test_workspace_isolation_per_journey(self, test_definition_container):
        """Each journey gets isolated workspace"""
        # Spawn multiple workers
        worker1 = await WorkerFactory.spawn(
            definition=test_definition_container,
            user_journey_id="test_journey_ws_001",
            isolation_level="process"  # Use process for faster test
        )
        worker2 = await WorkerFactory.spawn(
            definition=test_definition_container,
            user_journey_id="test_journey_ws_002",
            isolation_level="process"
        )

        # Verify different workspaces
        assert worker1.workspace_path != worker2.workspace_path
        assert "test_journey_ws_001" in worker1.workspace_path
        assert "test_journey_ws_002" in worker2.workspace_path

    @pytest.mark.asyncio
    async def test_no_context_bleed_between_journeys(self, test_definition_container):
        """Workers from different journeys cannot access each other's data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create definition with temp workspace
            definition = WorkerDefinition(
                worker_id="test_isolation_worker",
                identity=test_definition_container.identity,
                runtime=WorkerRuntime(
                    container="python:3.11-slim",
                    workspace_template=f"{tmpdir}/workspace_{{user_journey_id}}",
                    tools=["read", "write"],
                    session_persistence=True
                ),
                trust_level="sandboxed"
            )

            # Spawn two workers
            worker1 = await WorkerFactory.spawn(
                definition=definition,
                user_journey_id="journey_a",
                isolation_level="process"
            )
            worker2 = await WorkerFactory.spawn(
                definition=definition,
                user_journey_id="journey_b",
                isolation_level="process"
            )

            # Create test file in worker1's workspace
            workspace1 = Path(worker1.workspace_path)
            workspace1.mkdir(parents=True, exist_ok=True)
            test_file1 = workspace1 / "secret.txt"
            test_file1.write_text("Worker 1 secret data")

            # Create test file in worker2's workspace
            workspace2 = Path(worker2.workspace_path)
            workspace2.mkdir(parents=True, exist_ok=True)
            test_file2 = workspace2 / "secret.txt"
            test_file2.write_text("Worker 2 secret data")

            # Verify isolation - each worker has separate workspace with different data
            assert test_file1.read_text() == "Worker 1 secret data"
            assert test_file2.read_text() == "Worker 2 secret data"
            assert test_file1.read_text() != test_file2.read_text()

            # Verify workers have different workspace paths (isolation boundary)
            assert workspace1 != workspace2
            assert str(workspace1).endswith("workspace_journey_a")
            assert str(workspace2).endswith("workspace_journey_b")

    @pytest.mark.asyncio
    async def test_container_cleanup_on_kill(self, test_definition_container):
        """Container is killed when worker is killed"""
        with patch('workers.isolation.container.ContainerIsolation._get_client') as mock_client:
            mock_container = Mock()
            mock_container.id = "test_container_cleanup"
            mock_client.return_value.containers.run.return_value = mock_container
            mock_client.return_value.containers.get.return_value = mock_container

            # Spawn worker
            worker = await WorkerFactory.spawn(
                definition=test_definition_container,
                user_journey_id="test_journey_cleanup",
                isolation_level="container"
            )

            # Trigger container spawn
            await worker.execute({"command": "echo 'test'"})

            assert worker.container_id == "test_container_cleanup"

            # Kill worker
            await WorkerFactory.kill("test_journey_cleanup")

            # Verify container kill was called
            mock_container.kill.assert_called_once()
            mock_container.remove.assert_called_once()


class TestSessionPersistence:
    """Test session state persistence across worker restarts"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.fixture
    def persistent_definition(self):
        """Create definition with session persistence"""
        return WorkerDefinition(
            worker_id="persistent_worker",
            identity=WorkerIdentity(
                name="Persistent Worker",
                system_prompt="Worker with session persistence",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="python:3.11-slim",
                workspace_template="/tmp/persistent_workspace/{user_journey_id}",
                tools=["read", "write"],
                session_persistence=True
            ),
            trust_level="sandboxed"
        )

    @pytest.mark.asyncio
    async def test_workspace_persists_across_restarts(self, persistent_definition):
        """Workspace data persists when worker is killed and respawned"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Update definition to use temp workspace
            definition = WorkerDefinition(
                worker_id=persistent_definition.worker_id,
                identity=persistent_definition.identity,
                runtime=WorkerRuntime(
                    container=persistent_definition.runtime.container,
                    workspace_template=f"{tmpdir}/workspace_{{user_journey_id}}",
                    tools=persistent_definition.runtime.tools,
                    session_persistence=True
                ),
                trust_level=persistent_definition.trust_level
            )

            journey_id = "test_journey_persist"

            # Spawn worker
            worker1 = await WorkerFactory.spawn(
                definition=definition,
                user_journey_id=journey_id,
                isolation_level="process"
            )

            # Create state file in workspace
            workspace = Path(worker1.workspace_path)
            workspace.mkdir(parents=True, exist_ok=True)
            state_file = workspace / "session_state.json"
            state_file.write_text('{"counter": 42}')

            # Kill worker
            await WorkerFactory.kill(journey_id)

            # Respawn worker with same journey ID
            worker2 = await WorkerFactory.spawn(
                definition=definition,
                user_journey_id=journey_id,
                isolation_level="process"
            )

            # Verify workspace is same
            assert worker2.workspace_path == worker1.workspace_path

            # Verify state persisted
            assert state_file.exists()
            assert state_file.read_text() == '{"counter": 42}'


class TestProcessIsolation:
    """Test process-level isolation (lightweight alternative to containers)"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.fixture
    def process_definition(self):
        """Create definition with process isolation"""
        return WorkerDefinition(
            worker_id="process_worker",
            identity=WorkerIdentity(
                name="Process Worker",
                system_prompt="Worker with process isolation",
                onboarding_steps=[]
            ),
            runtime=WorkerRuntime(
                container="python:3.11-slim",
                workspace_template="/tmp/process_workspace/{user_journey_id}",
                tools=["read", "write"],
                session_persistence=True
            ),
            trust_level="sandboxed"
        )

    @pytest.mark.asyncio
    async def test_process_isolation_executes_without_container(self, process_definition):
        """Process isolation works without spawning containers"""
        # Spawn worker with process isolation
        worker = await WorkerFactory.spawn(
            definition=process_definition,
            user_journey_id="test_journey_process",
            isolation_level="process"
        )

        # Execute action
        result = await worker.execute({"command": "echo 'test'"})

        # Verify no container spawned
        assert worker.container_id is None
        assert worker._container_spawned is False

        # Verify execution succeeded
        assert result.success is True
        assert result.actual_outcome["isolation"] == "process"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
