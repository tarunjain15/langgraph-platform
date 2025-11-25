"""
MockWorker: Test double for Worker interface

TESTING PATTERNS:
  - Test coordination without side effects
  - Verify void() called before execute()
  - Simulate constraint violations
  - Verify ExecutorNode abort logic

CONFIGURATION:
  - Set void_should_fail=True to test rejection flow
  - Set void_warnings=[...] to test warning handling
  - Set execute_should_fail=True to test failure logging
"""

import time
from typing import Dict, List, Any, Optional

from workers.base import (
    BaseWorker,
    WorkerState,
    Pressure,
    Constraint,
    FlowAction,
    VoidResult,
    ExecutionResult,
)


class MockWorker(BaseWorker):
    """
    Mock Worker for testing ExecutorNode integration

    Implements Worker interface with controllable behavior:
    - void() can be configured to succeed/fail/warn
    - execute() can be configured to succeed/fail
    - Tracks all method calls for verification
    """

    def __init__(
        self,
        worker_id: str = "mock_worker_1",
        worker_type: str = "mock",
        void_should_fail: bool = False,
        void_warnings: Optional[List[str]] = None,
        execute_should_fail: bool = False,
    ):
        super().__init__(worker_id=worker_id, worker_type=worker_type)

        # Configuration
        self.void_should_fail = void_should_fail
        self.void_warnings = void_warnings or []
        self.execute_should_fail = execute_should_fail

        # Call tracking
        self.state_calls = 0
        self.pressure_calls = 0
        self.constraints_calls = 0
        self.flow_calls = 0
        self.void_calls = []
        self.execute_calls = []
        self.evolve_calls = []

        # Constraints
        self._constraints = [
            Constraint(
                constraint_id="mock_constraint_1",
                rule="no_dangerous_operations",
                enforcement="hard",
                rationale="Test constraint enforcement",
            )
        ]

    async def state(self) -> WorkerState:
        """Track state() calls"""
        self.state_calls += 1
        return WorkerState(
            worker_id=self.worker_id,
            worker_type=self.worker_type,
            timestamp=self._current_timestamp(),
            data={
                "mock": True,
                "call_count": self.state_calls,
            },
        )

    async def pressure(self) -> List[Pressure]:
        """Track pressure() calls"""
        self.pressure_calls += 1
        return []

    async def constraints(self) -> List[Constraint]:
        """Track constraints() calls"""
        self.constraints_calls += 1
        return self._constraints

    async def flow(self, context: Dict[str, Any]) -> List[FlowAction]:
        """Track flow() calls"""
        self.flow_calls += 1
        return [
            FlowAction(
                action_id="mock_action",
                action_type="mock",
                description="Mock action for testing",
                estimated_cost=1.0,
                prerequisites=[],
            )
        ]

    async def void(self, action: Dict[str, Any]) -> VoidResult:
        """
        Simulate action WITHOUT side effects

        Configurable:
        - void_should_fail: Make void() return success=False
        - void_warnings: Add warnings to result
        """
        self.void_calls.append(action)

        result = VoidResult(
            action_id=action.get("action_id", f"void_mock_{int(time.time())}"),
            success=not self.void_should_fail,
            predicted_outcome={
                "mock_result": "simulation",
                "action": action,
                "call_number": len(self.void_calls),
            },
            side_effect_occurred=False,  # MUST be False
            simulation_timestamp=self._current_timestamp(),
            warnings=self.void_warnings.copy(),
        )

        # Validate void contract
        self._validate_void_result(result)
        return result

    async def execute(self, action: Dict[str, Any]) -> ExecutionResult:
        """
        Execute action WITH side effects

        Configurable:
        - execute_should_fail: Make execute() return success=False
        """
        start_time = time.time()
        self.execute_calls.append(action)

        if self.execute_should_fail:
            result = ExecutionResult(
                action_id=action.get("action_id", f"exec_mock_{int(time.time())}"),
                success=False,
                actual_outcome={
                    "error": "Mock execution failure (configured)",
                    "action": action,
                },
                side_effect_occurred=False,
                execution_timestamp=self._current_timestamp(),
                duration_ms=(time.time() - start_time) * 1000,
                audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
            )
        else:
            result = ExecutionResult(
                action_id=action.get("action_id", f"exec_mock_{int(time.time())}"),
                success=True,
                actual_outcome={
                    "mock_result": "executed",
                    "action": action,
                    "call_number": len(self.execute_calls),
                },
                side_effect_occurred=True,  # MUST be True if success
                execution_timestamp=self._current_timestamp(),
                duration_ms=(time.time() - start_time) * 1000,
                audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
            )

        return result

    async def evolve(self, feedback: Dict[str, Any]) -> None:
        """Track evolve() calls"""
        self.evolve_calls.append(feedback)

    # Test helpers

    def was_void_called(self) -> bool:
        """Check if void() was called"""
        return len(self.void_calls) > 0

    def was_execute_called(self) -> bool:
        """Check if execute() was called"""
        return len(self.execute_calls) > 0

    def void_called_before_execute(self) -> bool:
        """Verify void() was called before execute()"""
        return len(self.void_calls) > 0 and len(self.execute_calls) >= 0

    def reset_calls(self):
        """Reset call tracking"""
        self.state_calls = 0
        self.pressure_calls = 0
        self.constraints_calls = 0
        self.flow_calls = 0
        self.void_calls = []
        self.execute_calls = []
        self.evolve_calls = []
