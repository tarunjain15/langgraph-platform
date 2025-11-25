"""
Worker Definition Loader (R13.1)

Loads YAML worker definitions into Python dataclass instances.
Layer 1 of Defense in Depth: yaml.safe_load() blocks code execution.
"""

import yaml
from pathlib import Path
from typing import Union

from .schema import (
    WorkerDefinition,
    WorkerIdentity,
    WorkerConstraint,
    WorkerRuntime,
    WorkerAudit
)


def load_worker_definition(path: Union[str, Path]) -> WorkerDefinition:
    """
    Load worker definition from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        WorkerDefinition instance

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValueError: If required fields are missing
        TypeError: If field types are incorrect

    Security:
        Uses yaml.safe_load() to prevent code execution in YAML.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Worker definition not found: {path}")

    # Layer 1: safe_load blocks !!python/object and code execution
    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML: expected dict, got {type(data).__name__}")

    # Extract and validate worker_id
    worker_id = data.get('worker_id')
    if not worker_id:
        raise ValueError("Missing required field: worker_id")

    # Load identity section
    identity_data = data.get('identity', {})
    identity = WorkerIdentity(
        name=identity_data.get('name', ''),
        system_prompt=identity_data.get('system_prompt', ''),
        onboarding_steps=identity_data.get('onboarding_steps', [])
    )

    # Load constraints section
    constraints_data = data.get('constraints', [])
    constraints = [
        WorkerConstraint(
            constraint_id=c.get('constraint_id', ''),
            witness=c.get('witness', ''),
            feedback=c.get('feedback', ''),
            value=c.get('value', '')
        )
        for c in constraints_data
    ]

    # Load runtime section
    runtime_data = data.get('runtime', {})
    runtime = WorkerRuntime(
        container=runtime_data.get('container', 'claude-code:mcp-session'),
        workspace_template=runtime_data.get('workspace_template', ''),
        tools=runtime_data.get('tools', []),
        session_persistence=runtime_data.get('session_persistence', True)
    )

    # Load audit section
    audit_data = data.get('audit', {})
    audit = WorkerAudit(
        log_all_actions=audit_data.get('log_all_actions', True),
        execution_channel=audit_data.get('execution_channel', 'langfuse'),
        retention_days=audit_data.get('retention_days', 90)
    )

    # Create worker definition
    # Layer 2: Dataclass validation blocks malformed structures
    worker = WorkerDefinition(
        worker_id=worker_id,
        identity=identity,
        constraints=constraints,
        runtime=runtime,
        trust_level=data.get('trust_level', 'sandboxed'),
        audit=audit,
        tools=data.get('tools', [])
    )

    return worker
