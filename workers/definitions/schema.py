"""
Worker Definition Schema (R13.1)

Dataclass definitions for declarative worker configuration.
Enforces DEFINITION_DECLARATIVE_PURITY - no executable code in definitions.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class WorkerIdentity:
    """Worker identity and purpose definition"""
    name: str
    system_prompt: str
    onboarding_steps: list[str] = field(default_factory=list)


@dataclass
class WorkerConstraint:
    """Sacred constraint definition with witness"""
    constraint_id: str
    witness: str  # Observable condition that proves constraint is met
    feedback: str  # Message shown when constraint is violated
    value: str  # Target value or threshold


@dataclass
class WorkerRuntime:
    """Worker runtime configuration"""
    container: str  # e.g., "claude-code:mcp-session"
    workspace_template: str  # Repository or workspace path
    tools: list[str] = field(default_factory=list)  # Tool names (e.g., ["read", "write", "grep"])
    session_persistence: bool = True


@dataclass
class WorkerAudit:
    """Audit and observability configuration"""
    log_all_actions: bool = True
    execution_channel: str = "langfuse"  # Where to send traces
    retention_days: int = 90


@dataclass
class WorkerDefinition:
    """Complete worker definition (loaded from YAML)"""
    worker_id: str  # Unique identifier (e.g., "researcher_v1")
    identity: WorkerIdentity
    constraints: list[WorkerConstraint] = field(default_factory=list)
    runtime: WorkerRuntime = field(default_factory=lambda: WorkerRuntime(
        container="claude-code:mcp-session",
        workspace_template=""
    ))
    trust_level: Literal["trusted", "sandboxed", "restricted"] = "sandboxed"
    audit: WorkerAudit = field(default_factory=WorkerAudit)
    tools: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate worker_id format"""
        if not self.worker_id:
            raise ValueError("worker_id cannot be empty")

        # Validate worker_id format (alphanumeric + underscore only)
        if not all(c.isalnum() or c == '_' for c in self.worker_id):
            raise ValueError(
                f"Invalid worker_id '{self.worker_id}': "
                "Only alphanumeric characters and underscores allowed"
            )
