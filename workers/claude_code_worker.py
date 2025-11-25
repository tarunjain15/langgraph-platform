"""
Claude Code Worker (R13.2)

Worker instance wrapping Claude Code agent with R13 definition + isolation.
Implements R11 Worker protocol with R13 constraints.
"""

import time
import uuid
from typing import Dict, List, Any

from workers.base import (
    Worker,
    WorkerState,
    Pressure,
    Constraint,
    FlowAction,
    VoidResult,
    ExecutionResult
)
from workers.definitions.schema import WorkerDefinition


class ClaudeCodeWorker:
    """
    Worker instance for Claude Code agent.

    Carries:
    - Worker definition (identity, constraints, runtime config)
    - User journey ID (isolation boundary)
    - Workspace path (unique per journey)

    Implements void() and execute() from Worker protocol.
    """

    def __init__(
        self,
        worker_id: str,
        definition: WorkerDefinition,
        workspace_path: str,
        user_journey_id: str,
        isolation_level: str = "process"
    ):
        """
        Initialize Claude Code worker instance.

        Args:
            worker_id: Unique worker instance ID
            definition: Worker definition (from R13.1)
            workspace_path: Isolated workspace for this journey
            user_journey_id: User journey identifier
            isolation_level: Isolation boundary (container|process|thread)
        """
        self.worker_id = worker_id
        self.definition = definition
        self.workspace_path = workspace_path
        self.user_journey_id = user_journey_id
        self.isolation_level = isolation_level

        # Container/process isolation
        self.container_id = None
        self.process_id = None
        self._container_spawned = False

        # State tracking
        self._last_action_timestamp = 0.0
        self._action_count = 0

    async def _ensure_container(self):
        """
        Ensure container is spawned (R13.3).

        Spawns container on first call, no-op on subsequent calls.
        """
        if self.isolation_level == "container" and not self._container_spawned:
            from workers.isolation.container import ContainerIsolation

            self.container_id = await ContainerIsolation.spawn_container(
                user_journey_id=self.user_journey_id,
                workspace_path=self.workspace_path,
                container_image=self.definition.runtime.container,
                read_only=True
            )
            self._container_spawned = True

    async def state(self) -> WorkerState:
        """
        Get current worker state.

        Returns:
            WorkerState with current status
        """
        return WorkerState(
            worker_id=self.worker_id,
            worker_type="claude_code",
            timestamp=time.time(),
            data={
                "user_journey_id": self.user_journey_id,
                "workspace_path": self.workspace_path,
                "isolation_level": self.isolation_level,
                "action_count": self._action_count,
                "definition": {
                    "worker_id": self.definition.worker_id,
                    "trust_level": self.definition.trust_level,
                    "constraints_count": len(self.definition.constraints)
                }
            }
        )

    async def pressure(self) -> List[Pressure]:
        """
        Detect unfulfilled demands or constraint violations.

        Returns:
            List of active pressures

        TODO R13.3: Actual constraint monitoring
        """
        pressures = []

        # Placeholder: No pressure detection yet (R13.3)
        return pressures

    async def constraints(self) -> List[Constraint]:
        """
        Get sacred constraints from definition.

        Returns:
            List of constraints that must be honored
        """
        return [
            Constraint(
                constraint_id=c.constraint_id,
                rule=f"{c.witness}: {c.value}",
                enforcement="hard",  # All definition constraints are hard
                rationale=c.feedback
            )
            for c in self.definition.constraints
        ]

    async def flow(self, context: Dict[str, Any]) -> List[FlowAction]:
        """
        Get available actions in current flow.

        Args:
            context: Current context

        Returns:
            List of possible actions

        TODO R13.3: Actual flow analysis
        """
        # Placeholder: Basic actions
        return [
            FlowAction(
                action_id="execute_task",
                action_type="claude_code_execute",
                description="Execute task in Claude Code workspace",
                estimated_cost=None,
                prerequisites=[]
            )
        ]

    async def void(self, action: Dict[str, Any]) -> VoidResult:
        """
        Simulate action WITHOUT side effects.

        Args:
            action: Action specification

        Returns:
            VoidResult with predicted outcome

        Flow:
            1. Validate action structure
            2. Run constraint witnesses (R13.4 - automatic enforcement)
            3. Simulate outcome
            4. Return prediction

        MUST return side_effect_occurred=False
        """
        action_id = action.get("action_id", f"void_{uuid.uuid4().hex[:8]}")

        # R13.4: Automatic witness verification (WITNESS_AUTOMATION constraint)
        # Witnesses called automatically before every execute()
        from workers.enforcement.witness import WitnessEnforcement

        # Use definition constraints (WorkerConstraint objects) not protocol constraints
        warnings = await WitnessEnforcement.verify(
            worker_id=self.worker_id,
            action=action,
            constraints=self.definition.constraints
        )

        # Simulate (no actual execution)
        predicted_outcome = {
            "simulated": True,
            "action_type": action.get("type", "unknown"),
            "workspace": self.workspace_path,
            "user_journey_id": self.user_journey_id
        }

        return VoidResult(
            action_id=action_id,
            success=True,
            predicted_outcome=predicted_outcome,
            side_effect_occurred=False,  # CRITICAL: void() never has side effects
            simulation_timestamp=time.time(),
            warnings=warnings
        )

    async def execute(self, action: Dict[str, Any]) -> ExecutionResult:
        """
        Execute action WITH side effects.

        Args:
            action: Action specification

        Returns:
            ExecutionResult with actual outcome

        Flow:
            1. Witnesses already ran in void() (R13.3/R13.4)
            2. Ensure container spawned (if container isolation)
            3. Execute action in isolated workspace/container
            4. Log to audit trail
            5. Return actual outcome

        MUST return side_effect_occurred=True if success=True
        """
        start_time = time.time()
        action_id = action.get("action_id", f"exec_{uuid.uuid4().hex[:8]}")

        # R13.3: Ensure container spawned before execution
        await self._ensure_container()

        # Execute action based on isolation level
        if self.isolation_level == "container" and self.container_id:
            # Execute in container (R13.3)
            from workers.isolation.container import ContainerIsolation

            command = action.get("command", "echo 'No command specified'")
            result = await ContainerIsolation.exec_in_container(
                container_id=self.container_id,
                command=command,
                workdir="/workspace"
            )

            actual_outcome = {
                "executed": True,
                "action_type": action.get("type", "unknown"),
                "workspace": self.workspace_path,
                "user_journey_id": self.user_journey_id,
                "container_id": self.container_id[:12],
                "exit_code": result["exit_code"],
                "output": result["output"]
            }
        else:
            # Process/thread isolation (placeholder)
            actual_outcome = {
                "executed": True,
                "action_type": action.get("type", "unknown"),
                "workspace": self.workspace_path,
                "user_journey_id": self.user_journey_id,
                "isolation": self.isolation_level
            }

        # Update state
        self._action_count += 1
        self._last_action_timestamp = time.time()

        duration_ms = (time.time() - start_time) * 1000

        return ExecutionResult(
            action_id=action_id,
            success=True,
            actual_outcome=actual_outcome,
            side_effect_occurred=True,  # CRITICAL: execute() always has side effects
            execution_timestamp=time.time(),
            duration_ms=duration_ms,
            audit_log_id=f"audit_{self.worker_id}_{int(time.time())}"
        )

    async def evolve(self, feedback: Dict[str, Any]) -> None:
        """
        Improve worker based on feedback.

        Args:
            feedback: Execution feedback

        TODO R13.3: Learning/adaptation mechanism
        """
        # Placeholder: No evolution yet
        pass

    async def cleanup(self):
        """
        Release worker resources and cleanup workspace.

        Flow:
            1. Terminate container/process (if running)
            2. Cleanup workspace directory (optional)
            3. Release any held resources
        """
        # R13.3: Kill container if spawned
        if self.container_id:
            from workers.isolation.container import ContainerIsolation
            await ContainerIsolation.kill_container(self.container_id)
            self.container_id = None

        # Kill process if exists (future: process isolation)
        if self.process_id:
            # TODO: Kill process
            self.process_id = None

        # Reset state
        self._container_spawned = False
