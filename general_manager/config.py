"""
Config Schema & Loader for General Manager.

Transforms YAML config files into Python dataclasses.
Enforces CONFIG_DRIVEN_INSTANTIATION constraint.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional
import yaml


class AgencyProvider(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"


class ToolType(Enum):
    """Supported MCP tool types."""
    PLAYWRIGHT = "playwright"
    FILESYSTEM = "filesystem"
    BRAVE_SEARCH = "brave_search"


@dataclass
class AgencyConfig:
    """LLM provider configuration."""
    provider: AgencyProvider
    model: str
    temperature: float = 0.7


@dataclass
class TerminalConfig:
    """Terminal session configuration."""
    enabled: bool = True
    prompt_style: str = "minimal"  # minimal | rich


@dataclass
class RuntimeConfig:
    """Runtime limits configuration."""
    max_iterations: int = 10
    timeout_seconds: int = 300


@dataclass
class ManagerConfig:
    """
    Complete manager configuration.

    Loaded from YAML, used by ManagerFactory to instantiate managers.
    """
    name: str
    version: str
    system_prompt: str
    agency: AgencyConfig
    tools: List[ToolType]
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    terminal: TerminalConfig = field(default_factory=TerminalConfig)


class ConfigValidationError(Exception):
    """Raised when config validation fails."""
    pass


def load_manager_config(config_path: str) -> ManagerConfig:
    """
    Load manager config from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        ManagerConfig instance

    Raises:
        ConfigValidationError: If config is invalid
        FileNotFoundError: If config or prompt file not found
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    # Validate required fields
    _validate_required_fields(raw)

    # Load system prompt from referenced file
    prompt_ref = raw["identity"]["system_prompt"]
    prompt_path = path.parent / prompt_ref

    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {prompt_path}")

    with open(prompt_path) as f:
        system_prompt = f.read()

    # Parse agency config
    agency_raw = raw["agency"]
    try:
        provider = AgencyProvider(agency_raw["provider"])
    except ValueError:
        valid = [p.value for p in AgencyProvider]
        raise ConfigValidationError(
            f"Invalid provider '{agency_raw['provider']}'. Valid: {valid}"
        )

    agency = AgencyConfig(
        provider=provider,
        model=agency_raw["model"],
        temperature=agency_raw.get("temperature", 0.7)
    )

    # Parse tools
    tools = []
    for tool_name in raw.get("tools", []):
        try:
            tools.append(ToolType(tool_name))
        except ValueError:
            valid = [t.value for t in ToolType]
            raise ConfigValidationError(
                f"Invalid tool '{tool_name}'. Valid: {valid}"
            )

    # Parse runtime config
    runtime_raw = raw.get("runtime", {})
    runtime = RuntimeConfig(
        max_iterations=runtime_raw.get("max_iterations", 10),
        timeout_seconds=runtime_raw.get("timeout_seconds", 300)
    )

    # Parse terminal config
    terminal_raw = raw.get("terminal", {})
    terminal = TerminalConfig(
        enabled=terminal_raw.get("enabled", True),
        prompt_style=terminal_raw.get("prompt_style", "minimal")
    )

    # Enforce TERMINAL_CONVERSATION_REQUIRED
    if not terminal.enabled:
        raise ConfigValidationError(
            "TERMINAL_CONVERSATION_REQUIRED: terminal.enabled must be true"
        )

    return ManagerConfig(
        name=raw["name"],
        version=raw["version"],
        system_prompt=system_prompt,
        agency=agency,
        tools=tools,
        runtime=runtime,
        terminal=terminal
    )


def _validate_required_fields(raw: dict) -> None:
    """Validate required config fields exist."""
    required = ["name", "version", "identity", "agency", "tools"]

    for field in required:
        if field not in raw:
            raise ConfigValidationError(f"Missing required field: {field}")

    if "system_prompt" not in raw.get("identity", {}):
        raise ConfigValidationError("Missing required field: identity.system_prompt")

    if "provider" not in raw.get("agency", {}):
        raise ConfigValidationError("Missing required field: agency.provider")

    if "model" not in raw.get("agency", {}):
        raise ConfigValidationError("Missing required field: agency.model")
