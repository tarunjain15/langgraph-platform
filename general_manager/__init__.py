"""
General Manager (GM) - Config-driven conversational managers with MCP tools.

Usage:
    from gm.factory import ManagerFactory
    from gm.terminal import run_terminal_session

    manager = await ManagerFactory.from_config("managers/research_manager.yaml")
    response = await manager.chat("Hello!")

    # Or run interactive terminal session
    await run_terminal_session(manager)
"""

from .config import ManagerConfig, load_manager_config, AgencyProvider, ToolType
from .factory import ManagerFactory
from .manager import ConversationalManager
from .llm_providers import LLMProvider, OllamaProvider, create_llm_provider
from .tool_registry import ToolRegistry, create_tool_registry

__all__ = [
    # Config
    "ManagerConfig",
    "load_manager_config",
    "AgencyProvider",
    "ToolType",
    # Factory
    "ManagerFactory",
    # Manager
    "ConversationalManager",
    # LLM Providers
    "LLMProvider",
    "OllamaProvider",
    "create_llm_provider",
    # Tool Registry
    "ToolRegistry",
    "create_tool_registry",
]
