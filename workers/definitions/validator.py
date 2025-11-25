"""
Worker Definition Validator (R13.1)

Security validation enforcing DEFINITION_DECLARATIVE_PURITY.
Layers 3 & 4 of Defense in Depth: pattern detection and semantic validation.
"""

import re
from typing import Optional

from .schema import WorkerDefinition


# Layer 3: Forbidden patterns that suggest code execution
FORBIDDEN_PATTERNS = [
    # Python code execution
    r'__import__',
    r'exec\s*\(',
    r'eval\s*\(',
    r'compile\s*\(',
    r'globals\s*\(',
    r'locals\s*\(',

    # Shell commands
    r'os\.system',
    r'subprocess\.',
    r'popen',

    # File system manipulation
    r'open\s*\(',
    r'__file__',

    # Lambda and function definitions
    r'lambda\s+',
    r'def\s+\w+\s*\(',

    # Class definitions
    r'class\s+\w+',

    # Import statements
    r'^\s*import\s+',
    r'^\s*from\s+.+\s+import',
]


# Witness function registry (declarative witness implementations)
WITNESS_REGISTRY = {
    'response_time_under_5s': lambda state: state.get('response_time', float('inf')) < 5.0,
    'all_actions_logged': lambda state: state.get('actions_logged', 0) > 0,
    'session_persisted': lambda state: state.get('session_id') is not None,
}


def validate_worker_definition(worker: WorkerDefinition) -> tuple[bool, Optional[str]]:
    """
    Validate worker definition for security and correctness.

    Args:
        worker: WorkerDefinition instance to validate

    Returns:
        (is_valid, error_message) tuple
        - is_valid: True if validation passed
        - error_message: None if valid, error description if invalid

    Security Layers:
        Layer 3: Forbidden pattern detection (blocks code strings)
        Layer 4: Worker ID validation (blocks injection)
    """

    # Layer 4: Worker ID validation
    if not worker.worker_id:
        return False, "worker_id cannot be empty"

    if not re.match(r'^[a-zA-Z0-9_]+$', worker.worker_id):
        return False, f"Invalid worker_id '{worker.worker_id}': Only alphanumeric and underscore allowed"

    # Layer 3: Scan all text fields for forbidden patterns
    text_fields = [
        ('identity.name', worker.identity.name),
        ('identity.system_prompt', worker.identity.system_prompt),
        ('runtime.container', worker.runtime.container),
        ('runtime.workspace_template', worker.runtime.workspace_template),
    ]

    # Add onboarding steps
    for i, step in enumerate(worker.identity.onboarding_steps):
        text_fields.append((f'identity.onboarding_steps[{i}]', step))

    # Add constraint fields
    for i, constraint in enumerate(worker.constraints):
        text_fields.append((f'constraints[{i}].witness', constraint.witness))
        text_fields.append((f'constraints[{i}].feedback', constraint.feedback))
        text_fields.append((f'constraints[{i}].value', constraint.value))

    # Scan for forbidden patterns
    for field_name, text in text_fields:
        if not isinstance(text, str):
            continue

        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                return False, (
                    f"Forbidden code pattern detected in {field_name}: '{pattern}'. "
                    f"Worker definitions must be declarative (no executable code)."
                )

    # Validate witness references
    for constraint in worker.constraints:
        if constraint.witness and constraint.witness not in WITNESS_REGISTRY:
            return False, (
                f"Unknown witness function '{constraint.witness}'. "
                f"Available witnesses: {', '.join(WITNESS_REGISTRY.keys())}"
            )

    # Validate trust level
    valid_trust_levels = ['trusted', 'sandboxed', 'restricted']
    if worker.trust_level not in valid_trust_levels:
        return False, (
            f"Invalid trust_level '{worker.trust_level}'. "
            f"Must be one of: {', '.join(valid_trust_levels)}"
        )

    return True, None


def validate_worker_file(yaml_path: str) -> tuple[bool, Optional[str], Optional[WorkerDefinition]]:
    """
    Validate worker definition YAML file (end-to-end validation).

    Args:
        yaml_path: Path to YAML file

    Returns:
        (is_valid, error_message, worker) tuple
        - is_valid: True if all validation passed
        - error_message: None if valid, error description if invalid
        - worker: WorkerDefinition instance if valid, None if invalid

    Validation Layers:
        1. yaml.safe_load() in loader (blocks code execution)
        2. Dataclass validation (blocks malformed structures)
        3. Pattern detection (blocks code strings)
        4. Semantic validation (blocks invalid references)
    """
    from .loader import load_worker_definition

    try:
        # Layers 1 & 2: Load and parse
        worker = load_worker_definition(yaml_path)

        # Layers 3 & 4: Security validation
        is_valid, error_msg = validate_worker_definition(worker)

        if not is_valid:
            return False, error_msg, None

        return True, None, worker

    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}", None
