"""
Configuration Loader for LangGraph Platform

Loads environment-specific configuration from YAML files with:
- Environment variable substitution
- Validation
- Merge with .env secrets
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class ConfigLoader:
    """Loads and validates configuration from YAML files"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            project_root: Root directory of the project (auto-detected if None)
        """
        if project_root is None:
            # Auto-detect project root
            # lgp/config/loader.py -> go up 2 levels to project root
            project_root = Path(__file__).resolve().parent.parent.parent

        self.project_root = project_root
        self.config_dir = project_root / "config"

    def load(self, environment: str) -> Dict[str, Any]:
        """
        Load configuration for specified environment.

        Args:
            environment: Environment name (experiment/hosted)

        Returns:
            Dictionary with configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If environment is invalid
        """
        if environment not in ["experiment", "hosted"]:
            raise ValueError(
                f"Invalid environment: {environment}. "
                "Must be 'experiment' or 'hosted'"
            )

        config_file = self.config_dir / f"{environment}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_file}\n"
                f"Expected: config/{environment}.yaml"
            )

        # Load YAML
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        config = self._substitute_env_vars(config)

        # Validate config
        self._validate_config(config, environment)

        return config

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in config.

        Syntax: ${VAR_NAME} or ${VAR_NAME:default_value}

        Args:
            config: Config dict or value

        Returns:
            Config with substituted values
        """
        if isinstance(config, dict):
            return {
                key: self._substitute_env_vars(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Match ${VAR_NAME} or ${VAR_NAME:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2)
                value = os.getenv(var_name)

                if value is None:
                    if default_value is not None:
                        return default_value
                    else:
                        # Keep original ${VAR} if not set and no default
                        return match.group(0)

                return value

            return re.sub(pattern, replacer, config)
        else:
            return config

    def _validate_config(self, config: Dict[str, Any], environment: str):
        """
        Validate configuration structure.

        Args:
            config: Config dictionary
            environment: Environment name

        Raises:
            ValueError: If config is invalid
        """
        # Required top-level keys
        required_keys = ["checkpointer", "observability"]

        for key in required_keys:
            if key not in config:
                raise ValueError(
                    f"Missing required config key: {key} "
                    f"in config/{environment}.yaml"
                )

        # Validate checkpointer
        checkpointer = config.get("checkpointer", {})
        if "type" not in checkpointer:
            raise ValueError("checkpointer.type is required")

        if checkpointer["type"] not in ["sqlite", "postgresql"]:
            raise ValueError(
                f"Invalid checkpointer.type: {checkpointer['type']}. "
                "Must be 'sqlite' or 'postgresql'"
            )

        # Validate observability
        observability = config.get("observability", {})
        if "console" not in observability:
            raise ValueError("observability.console is required")
        if "langfuse" not in observability:
            raise ValueError("observability.langfuse is required")


def load_config(environment: str) -> Dict[str, Any]:
    """
    Load configuration for specified environment.

    Convenience function for simple config loading.

    Args:
        environment: Environment name (experiment/hosted)

    Returns:
        Dictionary with configuration

    Example:
        >>> config = load_config("experiment")
        >>> print(config["checkpointer"]["type"])
        sqlite
    """
    loader = ConfigLoader()
    return loader.load(environment)
