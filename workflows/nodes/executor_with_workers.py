"""
ExecutorNode with Worker Dispatch (R12 Integration)

ARCHITECTURE:
  Coordination Channel (R10.3) → ExecutorNode → Worker (R11) → Execution Channel (R10.4)

KEY PATTERN:
  1. Get approved action from coordination_decision
  2. Select worker by action type (git, db, file, etc.)
  3. void() safety check (simulate first)
  4. If safe → execute() actual operation
  5. Log result to execution channel

WITNESS:
  void() called before execute() proves safety-first architecture
  void() warnings abort execution proves constraint enforcement
  execute() only called if void() succeeds proves gated execution
"""

import time
from typing import Dict, Optional

from workers.base import Worker


class ExecutorNode:
    """
    Dispatcher: Coordinates workers via 7-tool interface

    Replaces R10.4's direct execution with worker delegation.
    Adds void() safety check before every execute().

    This completes the vertical integration:
    - R10: 4-channel coordination (horizontal multi-agent)
    - R11: Worker abstraction (vertical operation isolation)
    - R12: Coordination → Worker dispatch (integration layer)
    """

    def __init__(self, executor_id: str, workers: Dict[str, Worker]):
        """
        Initialize ExecutorNode with worker registry

        Args:
            executor_id: Unique identifier for this executor
            workers: Dict mapping worker type → Worker instance
                     Example: {"git": GitWorker(), "db": DatabaseWorker()}
        """
        self.executor_id = executor_id
        self.workers = workers

    async def execute(self, state: Dict) -> Dict:
        """
        Dispatch coordination decision to appropriate worker

        Flow:
        1. Get approved action from coordination_decision channel
        2. Select worker by action type
        3. SAFETY: void() check (simulate first)
        4. If void() fails/warns → abort, log rejection
        5. If void() succeeds → execute() actual operation
        6. Log result to execution channel

        Args:
            state: Coordination state with coordination_decision channel

        Returns:
            Dict with "executions" key containing execution log
        """
        decision = state.get("coordination_decision")
        if not decision:
            # No coordination decision yet
            return {}

        action = decision["action"]
        worker_type = action.get("worker_type", "file")

        # Step 1: Get worker
        worker = self.workers.get(worker_type)
        if not worker:
            return {
                "executions": [{
                    "executor_id": self.executor_id,
                    "agent_id": decision.get("approved_agent_id", "unknown"),
                    "action": action,
                    "status": "error",
                    "error": f"No worker registered for type: {worker_type}",
                    "timestamp": time.time()
                }]
            }

        # Step 2: SAFETY CHECK - void() simulation
        void_result = await worker.void(action)

        # Step 3: Check void() result
        if not void_result.success:
            # void() indicates operation would fail
            return {
                "executions": [{
                    "executor_id": self.executor_id,
                    "agent_id": decision["approved_agent_id"],
                    "action": action,
                    "status": "rejected",
                    "reason": "void() simulation failed",
                    "predicted_outcome": void_result.predicted_outcome,
                    "warnings": void_result.warnings,
                    "timestamp": time.time()
                }]
            }

        if void_result.warnings:
            # void() succeeded but has warnings (constraint violations, safety concerns)
            return {
                "executions": [{
                    "executor_id": self.executor_id,
                    "agent_id": decision["approved_agent_id"],
                    "action": action,
                    "status": "rejected",
                    "reason": "void() safety check detected warnings",
                    "warnings": void_result.warnings,
                    "predicted_outcome": void_result.predicted_outcome,
                    "timestamp": time.time()
                }]
            }

        # Step 4: Safe to execute - void() passed
        exec_result = await worker.execute(action)

        # Step 5: Log to execution channel
        return {
            "executions": [{
                "executor_id": self.executor_id,
                "agent_id": decision["approved_agent_id"],
                "action": action,
                "status": "success" if exec_result.success else "failure",
                "result": exec_result.actual_outcome,
                "side_effect_occurred": exec_result.side_effect_occurred,
                "duration_ms": exec_result.duration_ms,
                "audit_log_id": exec_result.audit_log_id,
                "timestamp": exec_result.execution_timestamp
            }]
        }


class FileWorker:
    """
    Simple file worker for basic file operations

    Implements Worker interface for file system operations.
    Used when no specialized worker (git, db) is needed.
    """

    def __init__(self, worker_id: str = "file_worker_1"):
        self.worker_id = worker_id

    async def void(self, action: Dict) -> "VoidResult":
        """Simulate file operation WITHOUT side effects"""
        from workers.base import VoidResult

        action_type = action.get("type", "unknown")

        if action_type == "write":
            target = action.get("target", "")
            content = action.get("content", "")

            warnings = []
            if not target:
                warnings.append("No target file specified")

            return VoidResult(
                action_id=action.get("action_id", f"void_file_{int(time.time())}"),
                success=bool(target),
                predicted_outcome={
                    "would_write_bytes": len(content),
                    "target": target,
                },
                side_effect_occurred=False,
                simulation_timestamp=time.time(),
                warnings=warnings,
            )

        return VoidResult(
            action_id=action.get("action_id", f"void_file_{int(time.time())}"),
            success=False,
            predicted_outcome={},
            side_effect_occurred=False,
            simulation_timestamp=time.time(),
            warnings=[f"Unknown action type: {action_type}"],
        )

    async def execute(self, action: Dict) -> "ExecutionResult":
        """Execute file operation WITH side effects"""
        from pathlib import Path
        from workers.base import ExecutionResult

        start_time = time.time()
        action_type = action.get("type", "unknown")

        if action_type == "write":
            target = action.get("target", "")
            content = action.get("content", "")

            if not target:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_file_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "No target file specified"},
                    side_effect_occurred=False,
                    execution_timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            # SIDE EFFECT: Actually write file
            try:
                Path(target).write_text(content)
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_file_{int(time.time())}"),
                    success=True,
                    actual_outcome={
                        "written": True,
                        "target": target,
                        "bytes": len(content),
                    },
                    side_effect_occurred=True,
                    execution_timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )
            except Exception as e:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_file_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": str(e)},
                    side_effect_occurred=False,
                    execution_timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

        return ExecutionResult(
            action_id=action.get("action_id", f"exec_file_{int(time.time())}"),
            success=False,
            actual_outcome={"error": f"Unknown action type: {action_type}"},
            side_effect_occurred=False,
            execution_timestamp=time.time(),
            duration_ms=(time.time() - start_time) * 1000,
            audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
        )
