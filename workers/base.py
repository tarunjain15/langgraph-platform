"""
Worker Protocol: 7-Tool Interface for Manager-Worker Coordination

ABSTRACTION BOUNDARY:
  Manager sees: state, pressure, constraints, flow, void, execute, evolve
  Manager CANNOT see: Internal 4-channel coordination, permissions, validation

CRITICAL DISTINCTION:
  void()    = Simulate action WITHOUT side effects (what-if analysis)
  execute() = Apply action WITH side effects (actual work)

INTERNAL IMPLEMENTATION:
  Workers internally use 4-channel coordination from R10:
  - Observation Channel (Topic): External state changes
  - Intent Channel (Topic): Planned actions
  - Coordination Channel (LastValue): Conflict resolution
  - Execution Channel (Topic): Audit trail

  But Manager only sees 7 tools - internals are hidden.
"""

from typing import Protocol, Dict, List, Any, Optional
from dataclasses import dataclass
import time


@dataclass
class WorkerState:
    """Current state snapshot"""
    worker_id: str
    worker_type: str
    timestamp: float
    data: Dict[str, Any]


@dataclass
class Pressure:
    """Unfulfilled demand or constraint violation"""
    pressure_id: str
    source: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    timestamp: float


@dataclass
class Constraint:
    """Sacred limit that must not be violated"""
    constraint_id: str
    rule: str
    enforcement: str  # "hard" (blocks execution), "soft" (warning only)
    rationale: str


@dataclass
class FlowAction:
    """Possible action in current flow"""
    action_id: str
    action_type: str
    description: str
    estimated_cost: Optional[float]
    prerequisites: List[str]


@dataclass
class VoidResult:
    """Simulation result WITHOUT side effects"""
    action_id: str
    success: bool
    predicted_outcome: Dict[str, Any]
    side_effect_occurred: bool  # MUST be False
    simulation_timestamp: float
    warnings: List[str]


@dataclass
class ExecutionResult:
    """Actual execution result WITH side effects"""
    action_id: str
    success: bool
    actual_outcome: Dict[str, Any]
    side_effect_occurred: bool  # MUST be True if success=True
    execution_timestamp: float
    duration_ms: float
    audit_log_id: str


class Worker(Protocol):
    """
    Worker Protocol: Manager's ONLY interface to workers

    7 Tools = Complete abstraction boundary
    Manager never accesses worker internals directly
    """

    async def state(self) -> WorkerState:
        """
        What is current reality?

        Returns snapshot of worker's current state:
        - Connection status
        - Resource availability
        - Current values

        Example: GitWorker.state() → {branch: "main", uncommitted: 3, remote_ahead: 2}
        """
        ...

    async def pressure(self) -> List[Pressure]:
        """
        What demands exist that aren't being fulfilled?

        Returns list of pressures:
        - Unresolved conflicts
        - Blocked operations
        - Constraint violations

        Example: DatabaseWorker.pressure() → [{type: "connection_timeout", severity: "high"}]
        """
        ...

    async def constraints(self) -> List[Constraint]:
        """
        What are the sacred limits?

        Returns list of constraints that must not be violated:
        - Hard constraints (block execution)
        - Soft constraints (warn only)

        Example: GitWorker.constraints() → [{rule: "no_force_push_to_main", enforcement: "hard"}]
        """
        ...

    async def flow(self, context: Dict[str, Any]) -> List[FlowAction]:
        """
        What actions are possible right now?

        Given current context, returns list of actions worker can perform.

        Example: GitWorker.flow(context) → [{action: "commit"}, {action: "push"}, {action: "pull"}]
        """
        ...

    async def void(self, action: Dict[str, Any]) -> VoidResult:
        """
        What WOULD happen if we executed this action? (NO side effects)

        CRITICAL: Simulates action WITHOUT actually executing.
        Enables safe what-if analysis before committing to execution.

        MUST return side_effect_occurred=False

        Example: DatabaseWorker.void({"type": "delete", "where": "age > 90"})
                 → {affected_rows: 42, side_effect_occurred: False}
        """
        ...

    async def execute(self, action: Dict[str, Any]) -> ExecutionResult:
        """
        Do the work. (WITH side effects)

        Actually executes the action, produces side effects.
        Returns audit trail for execution channel.

        MUST return side_effect_occurred=True if success=True

        Example: GitWorker.execute({"type": "commit", "message": "Fix bug"})
                 → {committed: True, side_effect_occurred: True, sha: "abc123"}
        """
        ...

    async def evolve(self, feedback: Dict[str, Any]) -> None:
        """
        Improve capability based on feedback.

        Worker adjusts internal behavior based on execution outcomes.
        Example: Learn better conflict resolution policies.
        """
        ...


class BaseWorker:
    """
    Base implementation providing common infrastructure.
    Concrete workers (GitWorker, DatabaseWorker) inherit from this.
    """

    def __init__(self, worker_id: str, worker_type: str):
        self.worker_id = worker_id
        self.worker_type = worker_type
        self._constraints: List[Constraint] = []
        self._pressures: List[Pressure] = []

    def _current_timestamp(self) -> float:
        """Helper for consistent timestamps"""
        return time.time()

    def _validate_void_result(self, result: VoidResult) -> None:
        """Ensure void() did NOT produce side effects"""
        if result.side_effect_occurred:
            raise ValueError(
                f"CONSTRAINT VIOLATION: void() produced side effect for action {result.action_id}. "
                f"void() MUST simulate without side effects."
            )

    def _validate_execute_result(self, result: ExecutionResult) -> None:
        """Ensure execute() contract is correct"""
        if result.success and not result.side_effect_occurred:
            raise ValueError(
                f"CONSTRAINT VIOLATION: execute() succeeded but side_effect_occurred=False for action {result.action_id}. "
                f"Successful execution MUST produce side effects."
            )
