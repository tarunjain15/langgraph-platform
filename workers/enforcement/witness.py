"""
Witness Enforcement (R13.4)

Platformized constraint verification for worker instances.
Automatically runs witness verification before action execution.
"""

import time
import logging
from typing import List, Dict, Any

from workers.definitions.schema import WorkerConstraint
from workers.enforcement.registry import WitnessRegistry

logger = logging.getLogger(__name__)


class WitnessEnforcement:
    """
    Platformized constraint verification.

    Automatically verifies constraints before worker.execute().
    Sacred: WITNESS_AUTOMATION constraint - witnesses called automatically,
    not manually.
    """

    @staticmethod
    async def verify(
        worker_id: str,
        action: Dict[str, Any],
        constraints: List[WorkerConstraint]
    ) -> List[str]:
        """
        Run all constraint witnesses for action.

        Args:
            worker_id: Worker identifier
            action: Action to verify
            constraints: Worker constraints to enforce

        Returns:
            List of warning messages (empty if all constraints pass)

        Called automatically before every worker.execute().
        This is the core of R13.4 - automatic constraint enforcement.
        """
        all_warnings = []

        for constraint in constraints:
            # Check if witness is registered
            if not WitnessRegistry.is_registered(constraint.witness):
                logger.warning(
                    f"Witness not registered: {constraint.witness} "
                    f"(constraint {constraint.constraint_id})"
                )
                continue

            # Run witness verification
            try:
                warnings = await WitnessRegistry.run(constraint.witness, action)

                if warnings:
                    # Log violation
                    await WitnessEnforcement._log_violation(
                        worker_id=worker_id,
                        constraint=constraint,
                        action=action,
                        warnings=warnings
                    )

                    all_warnings.extend(warnings)

            except Exception as e:
                logger.error(
                    f"Witness execution failed: {constraint.witness} - {e}"
                )
                all_warnings.append(
                    f"Witness execution error: {constraint.witness}"
                )

        return all_warnings

    @staticmethod
    async def _log_violation(
        worker_id: str,
        constraint: WorkerConstraint,
        action: Dict[str, Any],
        warnings: List[str]
    ):
        """
        Log constraint violation.

        Routes to appropriate feedback channel:
        - alert_dashboard: Send to alert dashboard
        - log: Write to execution log
        - email: Send email notification

        Args:
            worker_id: Worker identifier
            constraint: Constraint that was violated
            action: Action that violated constraint
            warnings: Warning messages from witness
        """
        violation_event = {
            "timestamp": time.time(),
            "worker_id": worker_id,
            "constraint_id": constraint.constraint_id,
            "witness": constraint.witness,
            "action_type": action.get("type", "unknown"),
            "warnings": warnings
        }

        # Route based on feedback channel
        if constraint.feedback == "alert_dashboard":
            # TODO R13.5: Send to alert dashboard API
            # For now, log to console with alert emoji
            print(f"🚨 CONSTRAINT VIOLATION: {violation_event}")

        elif constraint.feedback == "log":
            # Write to execution log
            logger.warning(f"Constraint violation: {violation_event}")

        elif constraint.feedback == "email":
            # TODO R13.5: Send email notification
            logger.info(f"Email notification (not implemented): {violation_event}")

        else:
            # Unknown feedback channel - log as warning
            logger.warning(f"Unknown feedback channel: {constraint.feedback}")
            logger.warning(f"Constraint violation: {violation_event}")

    @staticmethod
    async def verify_single_constraint(
        worker_id: str,
        action: Dict[str, Any],
        constraint: WorkerConstraint
    ) -> List[str]:
        """
        Verify a single constraint (for testing).

        Args:
            worker_id: Worker identifier
            action: Action to verify
            constraint: Constraint to enforce

        Returns:
            List of warning messages
        """
        return await WitnessEnforcement.verify(
            worker_id=worker_id,
            action=action,
            constraints=[constraint]
        )


class ViolationLogger:
    """
    In-memory violation log for testing and development.

    In production, violations would be sent to:
    - Alert dashboard (Langfuse, Datadog, etc.)
    - Execution logs (CloudWatch, Stackdriver, etc.)
    - Email notifications (SendGrid, AWS SES, etc.)
    """

    _violations: List[Dict[str, Any]] = []

    @staticmethod
    def log(violation: Dict[str, Any]):
        """Log violation to in-memory store"""
        ViolationLogger._violations.append(violation)

    @staticmethod
    def get_violations() -> List[Dict[str, Any]]:
        """Get all logged violations"""
        return ViolationLogger._violations.copy()

    @staticmethod
    def clear():
        """Clear violation log (for testing)"""
        ViolationLogger._violations.clear()

    @staticmethod
    def count() -> int:
        """Get count of violations"""
        return len(ViolationLogger._violations)

    @staticmethod
    def get_by_worker_id(worker_id: str) -> List[Dict[str, Any]]:
        """Get violations for specific worker"""
        return [
            v for v in ViolationLogger._violations
            if v.get("worker_id") == worker_id
        ]

    @staticmethod
    def get_by_constraint_id(constraint_id: str) -> List[Dict[str, Any]]:
        """Get violations for specific constraint"""
        return [
            v for v in ViolationLogger._violations
            if v.get("constraint_id") == constraint_id
        ]
