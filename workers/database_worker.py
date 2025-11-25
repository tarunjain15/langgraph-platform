"""
DatabaseWorker: Database operations exposed via 7-tool Worker interface

WITNESS PROOF:
  db_worker.void({"action": "delete", "where": "age > 90"}) → {affected_rows: 42, side_effect: False}
  db_worker.execute({"action": "insert", "data": {...}}) → actual INSERT occurs

KEY PATTERN:
  void() = Use COUNT query to simulate, NO data modification
  execute() = Actually run INSERT/UPDATE/DELETE WITH data modification

PRODUCTION SAFETY:
  void() is CRITICAL for production databases - preview impact before executing
"""

import sqlite3
import time
from pathlib import Path
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


class DatabaseWorker(BaseWorker):
    """
    Worker for database operations via 7-tool interface

    Internally uses SQL connection, but Manager only sees:
    - state(), pressure(), constraints(), flow()
    - void() (simulate), execute() (actual)
    - evolve()
    """

    def __init__(
        self,
        worker_id: str = "db_worker_1",
        db_path: Optional[Path] = None,
        environment: str = "development",
    ):
        super().__init__(worker_id=worker_id, worker_type="database")
        self.db_path = db_path or Path(":memory:")
        self.environment = environment
        self.conn: Optional[sqlite3.Connection] = None

        # Sacred constraints (environment-dependent)
        self._constraints = self._build_constraints()

    def _build_constraints(self) -> List[Constraint]:
        """Build constraints based on environment"""
        base_constraints = [
            Constraint(
                constraint_id="no_truncate_without_backup",
                rule="truncate_requires_backup",
                enforcement="hard",
                rationale="Data loss prevention",
            ),
        ]

        if self.environment == "production":
            base_constraints.extend([
                Constraint(
                    constraint_id="no_drop_tables",
                    rule="no_drop_tables_in_production",
                    enforcement="hard",
                    rationale="Production data must be preserved",
                ),
                Constraint(
                    constraint_id="read_only_mode",
                    rule="read_only",
                    enforcement="soft",
                    rationale="Production writes require explicit approval",
                ),
            ])

        return base_constraints

    def _ensure_connection(self) -> None:
        """Ensure database connection is open"""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

    def _close_connection(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ========================================
    # Tool 1: state() - What is current reality?
    # ========================================

    async def state(self) -> WorkerState:
        """
        Current database state

        Returns:
        - Connection status
        - Number of tables
        - Environment (development/production)
        - Database size
        """
        self._ensure_connection()

        # Get table count
        cursor = self.conn.execute(
            "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
        )
        table_count = cursor.fetchone()[0]

        # Get database size
        db_size = 0
        if self.db_path != Path(":memory:"):
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return WorkerState(
            worker_id=self.worker_id,
            worker_type=self.worker_type,
            timestamp=self._current_timestamp(),
            data={
                "connected": self.conn is not None,
                "table_count": table_count,
                "environment": self.environment,
                "db_path": str(self.db_path),
                "db_size_bytes": db_size,
            },
        )

    # ========================================
    # Tool 2: pressure() - What demands exist?
    # ========================================

    async def pressure(self) -> List[Pressure]:
        """
        Unfulfilled demands in database state

        Pressures:
        - Large table sizes (performance risk)
        - Missing indexes (query slowness)
        - Connection pool exhaustion
        """
        pressures = []

        self._ensure_connection()

        # Check for large tables
        cursor = self.conn.execute("""
            SELECT name,
                   (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
            FROM sqlite_master m
            WHERE type='table'
        """)

        for row in cursor.fetchall():
            table_name = row["name"]
            # Get actual row count
            try:
                count_cursor = self.conn.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = count_cursor.fetchone()[0]

                if row_count > 10000:
                    pressures.append(
                        Pressure(
                            pressure_id=f"large_table_{table_name}",
                            source="table_scan",
                            description=f"Table {table_name} has {row_count} rows (performance risk)",
                            severity="high" if row_count > 100000 else "medium",
                            timestamp=self._current_timestamp(),
                        )
                    )
            except sqlite3.Error:
                # Skip if table doesn't exist or can't be queried
                pass

        return pressures

    # ========================================
    # Tool 3: constraints() - Sacred limits
    # ========================================

    async def constraints(self) -> List[Constraint]:
        """Sacred database constraints that must not be violated"""
        return self._constraints

    # ========================================
    # Tool 4: flow() - Possible actions now
    # ========================================

    async def flow(self, context: Dict[str, Any]) -> List[FlowAction]:
        """
        What database actions are possible right now?

        Context-aware: Returns different actions based on environment
        """
        actions = []

        # Read-only operations (always safe)
        actions.append(
            FlowAction(
                action_id="select",
                action_type="select",
                description="Query data (read-only)",
                estimated_cost=0.5,
                prerequisites=[],
            )
        )

        # Write operations (environment-dependent)
        if self.environment != "production" or context.get("write_approved", False):
            actions.append(
                FlowAction(
                    action_id="insert",
                    action_type="insert",
                    description="Insert new rows",
                    estimated_cost=1.0,
                    prerequisites=["write_permission"],
                )
            )

            actions.append(
                FlowAction(
                    action_id="update",
                    action_type="update",
                    description="Update existing rows",
                    estimated_cost=2.0,
                    prerequisites=["write_permission"],
                )
            )

            actions.append(
                FlowAction(
                    action_id="delete",
                    action_type="delete",
                    description="Delete rows",
                    estimated_cost=2.0,
                    prerequisites=["write_permission", "backup_exists"],
                )
            )

        return actions

    # ========================================
    # Tool 5: void() - Simulate WITHOUT side effects
    # ========================================

    async def void(self, action: Dict[str, Any]) -> VoidResult:
        """
        Simulate database action WITHOUT executing

        CRITICAL: NO data modification
        Uses COUNT queries to predict impact

        Examples:
        - void({"type": "delete", "table": "users", "where": "age > 90"})
          → {affected_rows: 42, side_effect: False}
        - void({"type": "update", "table": "orders", "where": "status = 'pending'"})
          → {affected_rows: 128, side_effect: False}
        """
        self._ensure_connection()
        action_type = action.get("type", "unknown")

        if action_type == "delete":
            table = action.get("table", "")
            where = action.get("where", "")

            if not table:
                return VoidResult(
                    action_id=action.get("action_id", f"void_delete_{int(time.time())}"),
                    success=False,
                    predicted_outcome={},
                    side_effect_occurred=False,
                    simulation_timestamp=self._current_timestamp(),
                    warnings=["Table name required"],
                )

            # Simulate with COUNT query (NO deletion)
            try:
                query = f"SELECT COUNT(*) as count FROM {table}"
                if where:
                    query += f" WHERE {where}"

                cursor = self.conn.execute(query)
                affected_rows = cursor.fetchone()[0]

                warnings = []
                if affected_rows > 1000:
                    warnings.append(f"Large deletion: {affected_rows} rows would be deleted")

                if self.environment == "production":
                    warnings.append("Production environment: deletion requires explicit approval")

                result = VoidResult(
                    action_id=action.get("action_id", f"void_delete_{int(time.time())}"),
                    success=True,
                    predicted_outcome={
                        "affected_rows": affected_rows,
                        "table": table,
                        "where_clause": where or "ALL ROWS",
                    },
                    side_effect_occurred=False,  # MUST be False
                    simulation_timestamp=self._current_timestamp(),
                    warnings=warnings,
                )

            except sqlite3.Error as e:
                result = VoidResult(
                    action_id=action.get("action_id", f"void_delete_{int(time.time())}"),
                    success=False,
                    predicted_outcome={},
                    side_effect_occurred=False,
                    simulation_timestamp=self._current_timestamp(),
                    warnings=[f"SQL error: {str(e)}"],
                )

        elif action_type == "update":
            table = action.get("table", "")
            where = action.get("where", "")

            if not table:
                return VoidResult(
                    action_id=action.get("action_id", f"void_update_{int(time.time())}"),
                    success=False,
                    predicted_outcome={},
                    side_effect_occurred=False,
                    simulation_timestamp=self._current_timestamp(),
                    warnings=["Table name required"],
                )

            # Simulate with COUNT query (NO update)
            try:
                query = f"SELECT COUNT(*) as count FROM {table}"
                if where:
                    query += f" WHERE {where}"

                cursor = self.conn.execute(query)
                affected_rows = cursor.fetchone()[0]

                warnings = []
                if not where:
                    warnings.append("No WHERE clause: ALL rows would be updated")

                if self.environment == "production":
                    warnings.append("Production environment: update requires explicit approval")

                result = VoidResult(
                    action_id=action.get("action_id", f"void_update_{int(time.time())}"),
                    success=True,
                    predicted_outcome={
                        "affected_rows": affected_rows,
                        "table": table,
                        "where_clause": where or "ALL ROWS",
                    },
                    side_effect_occurred=False,
                    simulation_timestamp=self._current_timestamp(),
                    warnings=warnings,
                )

            except sqlite3.Error as e:
                result = VoidResult(
                    action_id=action.get("action_id", f"void_update_{int(time.time())}"),
                    success=False,
                    predicted_outcome={},
                    side_effect_occurred=False,
                    simulation_timestamp=self._current_timestamp(),
                    warnings=[f"SQL error: {str(e)}"],
                )

        elif action_type == "insert":
            table = action.get("table", "")
            data = action.get("data", {})

            warnings = []
            if not table:
                warnings.append("Table name required")

            if not data:
                warnings.append("No data provided")

            result = VoidResult(
                action_id=action.get("action_id", f"void_insert_{int(time.time())}"),
                success=bool(table and data),
                predicted_outcome={
                    "would_insert_rows": 1,
                    "table": table,
                    "fields": list(data.keys()) if data else [],
                },
                side_effect_occurred=False,
                simulation_timestamp=self._current_timestamp(),
                warnings=warnings,
            )

        elif action_type == "select":
            # Select is read-only, always safe
            result = VoidResult(
                action_id=action.get("action_id", f"void_select_{int(time.time())}"),
                success=True,
                predicted_outcome={
                    "operation": "read_only",
                    "table": action.get("table", ""),
                },
                side_effect_occurred=False,
                simulation_timestamp=self._current_timestamp(),
                warnings=[],
            )

        else:
            result = VoidResult(
                action_id=action.get("action_id", f"void_unknown_{int(time.time())}"),
                success=False,
                predicted_outcome={},
                side_effect_occurred=False,
                simulation_timestamp=self._current_timestamp(),
                warnings=[f"Unknown action type: {action_type}"],
            )

        # Validate void contract
        self._validate_void_result(result)
        return result

    # ========================================
    # Tool 6: execute() - Do work WITH side effects
    # ========================================

    async def execute(self, action: Dict[str, Any]) -> ExecutionResult:
        """
        Actually execute database action WITH side effects

        CRITICAL: Data IS modified
        Returns audit trail for execution channel

        Examples:
        - execute({"type": "insert", "table": "users", "data": {...}}) → inserts row
        - execute({"type": "delete", "table": "logs", "where": "age > 90"}) → deletes rows
        """
        self._ensure_connection()
        action_type = action.get("type", "unknown")
        start_time = time.time()

        # Check production constraints
        if self.environment == "production" and action_type in ["delete", "update", "insert"]:
            if not action.get("approved", False):
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_{action_type}_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "Production write blocked (approval required)"},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

        if action_type == "insert":
            table = action.get("table", "")
            data = action.get("data", {})

            if not table or not data:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_insert_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "Table name and data required"},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            # SIDE EFFECT: Actually insert
            try:
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

                cursor = self.conn.execute(query, list(data.values()))
                self.conn.commit()

                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_insert_{int(time.time())}"),
                    success=True,
                    actual_outcome={
                        "inserted": True,
                        "row_id": cursor.lastrowid,
                        "table": table,
                    },
                    side_effect_occurred=True,  # MUST be True
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            except sqlite3.Error as e:
                self.conn.rollback()
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_insert_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": str(e)},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

        elif action_type == "delete":
            table = action.get("table", "")
            where = action.get("where", "")

            if not table:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_delete_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "Table name required"},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            # SIDE EFFECT: Actually delete
            try:
                query = f"DELETE FROM {table}"
                if where:
                    query += f" WHERE {where}"

                cursor = self.conn.execute(query)
                self.conn.commit()
                affected_rows = cursor.rowcount

                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_delete_{int(time.time())}"),
                    success=True,
                    actual_outcome={
                        "deleted": True,
                        "affected_rows": affected_rows,
                        "table": table,
                        "where_clause": where or "ALL ROWS",
                    },
                    side_effect_occurred=True,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            except sqlite3.Error as e:
                self.conn.rollback()
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_delete_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": str(e)},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

        elif action_type == "select":
            table = action.get("table", "")
            where = action.get("where", "")

            if not table:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_select_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "Table name required"},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            # Read-only: No side effect
            try:
                query = f"SELECT * FROM {table}"
                if where:
                    query += f" WHERE {where}"

                cursor = self.conn.execute(query)
                rows = cursor.fetchall()

                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_select_{int(time.time())}"),
                    success=True,
                    actual_outcome={
                        "row_count": len(rows),
                        "table": table,
                    },
                    side_effect_occurred=False,  # SELECT has no side effect
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            except sqlite3.Error as e:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_select_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": str(e)},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

        else:
            return ExecutionResult(
                action_id=action.get("action_id", f"exec_unknown_{int(time.time())}"),
                success=False,
                actual_outcome={"error": f"Unknown action type: {action_type}"},
                side_effect_occurred=False,
                execution_timestamp=self._current_timestamp(),
                duration_ms=(time.time() - start_time) * 1000,
                audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
            )

    # ========================================
    # Tool 7: evolve() - Improve capability
    # ========================================

    async def evolve(self, feedback: Dict[str, Any]) -> None:
        """
        Learn from execution outcomes

        Example: If queries frequently timeout, learn to suggest indexes
        """
        # Future: Implement learning based on feedback
        # For now, this is a placeholder
        pass

    def __del__(self):
        """Cleanup: Close connection on deletion"""
        self._close_connection()
