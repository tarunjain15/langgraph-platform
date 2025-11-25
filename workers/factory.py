"""
Worker Factory (R13.2)

Spawns worker instances from definitions with isolated workspaces.
Enforces JOURNEY_ISOLATION constraint: one worker per user journey.
"""

from typing import Dict, Literal, Union
from pathlib import Path

from workers.definitions.schema import WorkerDefinition
from workers.definitions.loader import load_worker_definition
from workers.base import Worker


class WorkerFactory:
    """
    Factory for spawning worker instances from definitions.

    Sacred Constraint: JOURNEY_ISOLATION
    - Each user_journey_id gets exactly ONE worker instance
    - Workspace paths are unique per journey
    - No shared state between journeys

    Witness: spawn() creates instance with isolated workspace + loaded constraints
    """

    _instances: Dict[str, Worker] = {}  # user_journey_id → worker instance

    @staticmethod
    async def spawn(
        definition: Union[WorkerDefinition, str],
        user_journey_id: str,
        isolation_level: Literal["container", "process", "thread"] = "process"
    ) -> Worker:
        """
        Spawn worker instance for user journey.

        Args:
            definition: WorkerDefinition instance or path to YAML file
            user_journey_id: Unique journey identifier (e.g., thread_id from checkpointer)
            isolation_level: Isolation boundary (container | process | thread)

        Returns:
            Worker instance with isolated workspace and loaded constraints

        Raises:
            ValueError: If user_journey_id already has a worker instance

        Flow:
            1. Validate journey isolation (no existing instance)
            2. Load definition if YAML path provided
            3. Create isolated workspace path
            4. Instantiate worker with definition
            5. Register in factory
            6. Return worker instance
        """
        # Step 1: Enforce JOURNEY_ISOLATION constraint
        if user_journey_id in WorkerFactory._instances:
            raise ValueError(
                f"JOURNEY_ISOLATION violation: Worker already exists for journey '{user_journey_id}'. "
                f"Use resume() to get existing instance or kill() first."
            )

        # Step 2: Load definition if path provided
        if isinstance(definition, str):
            definition = load_worker_definition(definition)

        # Step 3: Create isolated workspace path
        workspace_template = definition.runtime.workspace_template
        if "{user_journey_id}" in workspace_template:
            workspace_path = workspace_template.format(user_journey_id=user_journey_id)
        else:
            # Fallback: append journey_id to template
            workspace_path = f"{workspace_template}/{user_journey_id}"

        # Step 4: Instantiate worker (import here to avoid circular dependency)
        from workers.claude_code_worker import ClaudeCodeWorker

        worker = ClaudeCodeWorker(
            worker_id=f"{definition.worker_id}_{user_journey_id}",
            definition=definition,
            workspace_path=workspace_path,
            user_journey_id=user_journey_id,
            isolation_level=isolation_level
        )

        # Step 5: Register in factory
        WorkerFactory._instances[user_journey_id] = worker

        # Step 6: Return worker instance
        return worker

    @staticmethod
    def get(user_journey_id: str) -> Worker | None:
        """
        Get existing worker instance for journey.

        Args:
            user_journey_id: Journey identifier

        Returns:
            Worker instance if exists, None otherwise
        """
        return WorkerFactory._instances.get(user_journey_id)

    @staticmethod
    async def kill(user_journey_id: str):
        """
        Terminate worker instance and cleanup workspace.

        Args:
            user_journey_id: Journey identifier

        Raises:
            KeyError: If no worker exists for this journey

        Flow:
            1. Remove instance from registry
            2. Call worker.cleanup() to release resources
        """
        worker = WorkerFactory._instances.pop(user_journey_id)
        await worker.cleanup()

    @staticmethod
    async def resume(user_journey_id: str) -> Worker:
        """
        Resume existing worker instance.

        Args:
            user_journey_id: Journey identifier

        Returns:
            Existing worker instance

        Raises:
            ValueError: If no worker exists for this journey
        """
        existing = WorkerFactory.get(user_journey_id)
        if not existing:
            raise ValueError(
                f"Cannot resume: no worker instance for journey '{user_journey_id}'. "
                f"Use spawn() to create a new instance."
            )
        return existing

    @staticmethod
    def list_active() -> Dict[str, str]:
        """
        List all active worker instances.

        Returns:
            Dict mapping user_journey_id → worker_id
        """
        return {
            journey_id: worker.worker_id
            for journey_id, worker in WorkerFactory._instances.items()
        }

    @staticmethod
    async def kill_all():
        """
        Terminate all worker instances.

        Useful for testing cleanup and graceful shutdown.
        """
        journey_ids = list(WorkerFactory._instances.keys())
        for journey_id in journey_ids:
            await WorkerFactory.kill(journey_id)
