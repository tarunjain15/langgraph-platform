"""
Workers Package: 7-Tool Interface for Manager-Worker Coordination

ARCHITECTURE:
  - base.py: Worker Protocol definition (7 tools)
  - git_worker.py: Git operations via 7-tool interface
  - database_worker.py: Database operations via 7-tool interface

KEY ABSTRACTION:
  Manager sees: state, pressure, constraints, flow, void, execute, evolve
  Manager CANNOT see: Internal 4-channel coordination, SQL queries, git commands

CRITICAL TOOLS:
  - void(): Simulate action WITHOUT side effects (what-if analysis)
  - execute(): Apply action WITH side effects (actual work)
"""

from workers.base import (
    Worker,
    BaseWorker,
    WorkerState,
    Pressure,
    Constraint,
    FlowAction,
    VoidResult,
    ExecutionResult,
)
from workers.git_worker import GitWorker
from workers.database_worker import DatabaseWorker

__all__ = [
    "Worker",
    "BaseWorker",
    "WorkerState",
    "Pressure",
    "Constraint",
    "FlowAction",
    "VoidResult",
    "ExecutionResult",
    "GitWorker",
    "DatabaseWorker",
]
