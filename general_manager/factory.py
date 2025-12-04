"""
Manager Factory for General Manager.

Factory pattern for creating managers from config.
Enforces CONFIG_DRIVEN_INSTANTIATION constraint.
"""

from typing import Optional

from .config import ManagerConfig, load_manager_config
from .llm_providers import create_llm_provider, LLMProvider
from .tool_registry import ToolRegistry, create_tool_registry
from .manager import ConversationalManager


class ManagerFactory:
    """
    Factory for creating ConversationalManager instances from config.

    Usage:
        manager = await ManagerFactory.from_config("managers/research_manager.yaml")
        response = await manager.chat("Hello!")

    Enforces CONFIG_DRIVEN_INSTANTIATION constraint:
        All manager instantiation MUST go through factory.
    """

    @staticmethod
    async def from_config(config_path: str) -> ConversationalManager:
        """
        Create manager from YAML config file.

        Args:
            config_path: Path to manager YAML config

        Returns:
            Initialized ConversationalManager

        Raises:
            FileNotFoundError: If config file not found
            ConfigValidationError: If config is invalid
        """
        # Load config
        config = load_manager_config(config_path)

        # Create LLM provider
        llm = create_llm_provider(config.agency)

        # Create tool registry
        tool_registry = await create_tool_registry(config.tools)

        # Create manager
        return ConversationalManager(config, llm, tool_registry)

    @staticmethod
    async def from_config_object(
        config: ManagerConfig,
        llm: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None
    ) -> ConversationalManager:
        """
        Create manager from config object.

        Allows injection of custom LLM provider or tool registry.

        Args:
            config: ManagerConfig object
            llm: Optional custom LLM provider
            tool_registry: Optional custom tool registry

        Returns:
            Initialized ConversationalManager
        """
        # Create LLM provider if not provided
        if llm is None:
            llm = create_llm_provider(config.agency)

        # Create tool registry if not provided
        if tool_registry is None:
            tool_registry = await create_tool_registry(config.tools)

        return ConversationalManager(config, llm, tool_registry)
