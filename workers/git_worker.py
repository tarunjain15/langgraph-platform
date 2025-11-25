"""
GitWorker: Git operations exposed via 7-tool Worker interface

WITNESS PROOF:
  git_worker.void({"action": "push"}) → shows commits WITHOUT actual push
  git_worker.execute({"action": "commit"}) → actual commit occurs

KEY PATTERN:
  void() = Read git state, predict outcome, NO repository modification
  execute() = Actually run git commands WITH repository modification
"""

import subprocess
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


class GitWorker(BaseWorker):
    """
    Worker for git operations via 7-tool interface

    Internally uses git commands, but Manager only sees:
    - state(), pressure(), constraints(), flow()
    - void() (simulate), execute() (actual)
    - evolve()
    """

    def __init__(
        self,
        worker_id: str = "git_worker_1",
        repo_path: Optional[Path] = None,
    ):
        super().__init__(worker_id=worker_id, worker_type="git")
        self.repo_path = repo_path or Path.cwd()

        # Sacred constraints
        self._constraints = [
            Constraint(
                constraint_id="no_force_push_main",
                rule="no_force_push_to_main",
                enforcement="hard",
                rationale="Force push to main destroys team's work",
            ),
            Constraint(
                constraint_id="no_commit_without_message",
                rule="commit_message_required",
                enforcement="hard",
                rationale="Audit trail requires commit messages",
            ),
        ]

    # ========================================
    # Tool 1: state() - What is current reality?
    # ========================================

    async def state(self) -> WorkerState:
        """
        Current git repository state

        Returns:
        - Current branch
        - Number of uncommitted files
        - Commits ahead of remote
        - Remote tracking status
        """
        branch = self._get_current_branch()
        uncommitted_count = len(self._get_uncommitted_files())
        ahead_count = self._commits_ahead_of_remote()
        tracking_remote = self._get_tracking_remote()

        return WorkerState(
            worker_id=self.worker_id,
            worker_type=self.worker_type,
            timestamp=self._current_timestamp(),
            data={
                "branch": branch,
                "uncommitted_files": uncommitted_count,
                "commits_ahead_of_remote": ahead_count,
                "tracking_remote": tracking_remote,
                "repo_path": str(self.repo_path),
            },
        )

    # ========================================
    # Tool 2: pressure() - What demands exist?
    # ========================================

    async def pressure(self) -> List[Pressure]:
        """
        Unfulfilled demands in git state

        Pressures:
        - Uncommitted changes (data loss risk)
        - Unpushed commits (collaboration blocked)
        - Merge conflicts (work blocked)
        """
        pressures = []

        uncommitted = self._get_uncommitted_files()
        if uncommitted:
            pressures.append(
                Pressure(
                    pressure_id="uncommitted_changes",
                    source="git_status",
                    description=f"{len(uncommitted)} files uncommitted (data loss risk)",
                    severity="medium",
                    timestamp=self._current_timestamp(),
                )
            )

        ahead = self._commits_ahead_of_remote()
        if ahead > 0:
            pressures.append(
                Pressure(
                    pressure_id="unpushed_commits",
                    source="git_status",
                    description=f"{ahead} commits ahead of remote (collaboration blocked)",
                    severity="medium" if ahead < 5 else "high",
                    timestamp=self._current_timestamp(),
                )
            )

        conflicts = self._check_merge_conflicts()
        if conflicts:
            pressures.append(
                Pressure(
                    pressure_id="merge_conflicts",
                    source="git_status",
                    description=f"{len(conflicts)} files with merge conflicts",
                    severity="critical",
                    timestamp=self._current_timestamp(),
                )
            )

        return pressures

    # ========================================
    # Tool 3: constraints() - Sacred limits
    # ========================================

    async def constraints(self) -> List[Constraint]:
        """Sacred git constraints that must not be violated"""
        return self._constraints

    # ========================================
    # Tool 4: flow() - Possible actions now
    # ========================================

    async def flow(self, context: Dict[str, Any]) -> List[FlowAction]:
        """
        What git actions are possible right now?

        Context-aware: Returns different actions based on git state
        """
        actions = []

        uncommitted = self._get_uncommitted_files()
        if uncommitted:
            actions.append(
                FlowAction(
                    action_id="commit",
                    action_type="commit",
                    description=f"Commit {len(uncommitted)} uncommitted files",
                    estimated_cost=2.0,  # seconds
                    prerequisites=["commit_message_required"],
                )
            )

        ahead = self._commits_ahead_of_remote()
        if ahead > 0:
            actions.append(
                FlowAction(
                    action_id="push",
                    action_type="push",
                    description=f"Push {ahead} commits to remote",
                    estimated_cost=5.0,  # seconds (network)
                    prerequisites=["remote_connection"],
                )
            )

        # Always possible
        actions.append(
            FlowAction(
                action_id="status",
                action_type="status",
                description="Check git status (read-only)",
                estimated_cost=0.1,
                prerequisites=[],
            )
        )

        actions.append(
            FlowAction(
                action_id="pull",
                action_type="pull",
                description="Pull latest from remote",
                estimated_cost=3.0,
                prerequisites=["remote_connection"],
            )
        )

        return actions

    # ========================================
    # Tool 5: void() - Simulate WITHOUT side effects
    # ========================================

    async def void(self, action: Dict[str, Any]) -> VoidResult:
        """
        Simulate git action WITHOUT executing

        CRITICAL: NO repository modification
        Reads git state, predicts outcome, returns simulation

        Examples:
        - void({"type": "push"}) → {would_push_commits: 3, side_effect: False}
        - void({"type": "commit"}) → {would_commit_files: 5, side_effect: False}
        """
        action_type = action.get("type", "unknown")

        if action_type == "push":
            ahead = self._commits_ahead_of_remote()
            result = VoidResult(
                action_id=action.get("action_id", f"void_push_{int(time.time())}"),
                success=True,
                predicted_outcome={
                    "would_push_commits": ahead,
                    "remote": self._get_tracking_remote(),
                    "branch": self._get_current_branch(),
                },
                side_effect_occurred=False,  # MUST be False
                simulation_timestamp=self._current_timestamp(),
                warnings=self._check_push_constraints(action),
            )

        elif action_type == "commit":
            uncommitted = self._get_uncommitted_files()
            message = action.get("message", "")

            warnings = []
            if not message:
                warnings.append("Commit message required (constraint violation)")

            result = VoidResult(
                action_id=action.get("action_id", f"void_commit_{int(time.time())}"),
                success=bool(message),  # Only succeeds if message provided
                predicted_outcome={
                    "would_commit_files": len(uncommitted),
                    "files": uncommitted,
                },
                side_effect_occurred=False,  # MUST be False
                simulation_timestamp=self._current_timestamp(),
                warnings=warnings,
            )

        elif action_type == "status":
            # Status is read-only, always safe
            result = VoidResult(
                action_id=action.get("action_id", f"void_status_{int(time.time())}"),
                success=True,
                predicted_outcome={
                    "branch": self._get_current_branch(),
                    "uncommitted": len(self._get_uncommitted_files()),
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
        Actually execute git action WITH side effects

        CRITICAL: Repository IS modified
        Returns audit trail for execution channel

        Examples:
        - execute({"type": "commit", "message": "Fix bug"}) → commits files
        - execute({"type": "push"}) → pushes to remote
        """
        action_type = action.get("type", "unknown")
        start_time = time.time()

        if action_type == "commit":
            message = action.get("message", "")
            if not message:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_commit_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "Commit message required (constraint violation)"},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            # SIDE EFFECT: Actually commit
            try:
                result = subprocess.run(
                    ["git", "-C", str(self.repo_path), "commit", "-m", message],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Parse commit SHA from output
                commit_sha = "unknown"
                if "create mode" in result.stdout or "[" in result.stdout:
                    # Extract SHA from output like "[main abc1234] Fix bug"
                    parts = result.stdout.split()
                    for i, part in enumerate(parts):
                        if part.startswith("[") and i + 1 < len(parts):
                            commit_sha = parts[i + 1].rstrip("]")
                            break

                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_commit_{int(time.time())}"),
                    success=True,
                    actual_outcome={
                        "committed": True,
                        "commit_sha": commit_sha,
                        "message": message,
                    },
                    side_effect_occurred=True,  # MUST be True
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            except subprocess.CalledProcessError as e:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_commit_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": e.stderr},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

        elif action_type == "push":
            # Check constraints
            if self._get_current_branch() == "main" and action.get("force", False):
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_push_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": "Force push to main blocked (constraint)"},
                    side_effect_occurred=False,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            # SIDE EFFECT: Actually push
            try:
                result = subprocess.run(
                    ["git", "-C", str(self.repo_path), "push"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_push_{int(time.time())}"),
                    success=True,
                    actual_outcome={
                        "pushed": True,
                        "remote": self._get_tracking_remote(),
                        "branch": self._get_current_branch(),
                    },
                    side_effect_occurred=True,
                    execution_timestamp=self._current_timestamp(),
                    duration_ms=(time.time() - start_time) * 1000,
                    audit_log_id=f"audit_{self.worker_id}_{int(time.time())}",
                )

            except subprocess.CalledProcessError as e:
                return ExecutionResult(
                    action_id=action.get("action_id", f"exec_push_{int(time.time())}"),
                    success=False,
                    actual_outcome={"error": e.stderr},
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

        Example: If commits frequently fail due to large files,
                 learn to check file sizes in void()
        """
        # Future: Implement learning based on feedback
        # For now, this is a placeholder
        pass

    # ========================================
    # Internal helpers (NOT visible to Manager)
    # ========================================

    def _get_current_branch(self) -> str:
        """Read current git branch"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _get_uncommitted_files(self) -> List[str]:
        """List uncommitted files"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().split("\n")
            return [line[3:] for line in lines if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def _commits_ahead_of_remote(self) -> int:
        """Count commits ahead of tracking remote"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "rev-list", "--count", "@{u}..HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
            return 0
        except (subprocess.CalledProcessError, ValueError):
            return 0

    def _get_tracking_remote(self) -> Optional[str]:
        """Get tracking remote for current branch"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except subprocess.CalledProcessError:
            return None

    def _check_merge_conflicts(self) -> List[str]:
        """Check for merge conflicts"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "diff", "--name-only", "--diff-filter=U"],
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().split("\n")
            return [line for line in lines if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def _check_push_constraints(self, action: Dict[str, Any]) -> List[str]:
        """Check if push would violate constraints"""
        warnings = []
        if self._get_current_branch() == "main" and action.get("force", False):
            warnings.append("Force push to main violates constraint: no_force_push_to_main")
        return warnings
