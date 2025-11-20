"""
Agent node factory - Creates LangGraph nodes for different LLM providers.

Dispatches to correct provider (Claude Code, Ollama, etc.) based on
configuration while maintaining unified workflow interface.
"""

from typing import Dict, Any, Callable
from lgp.agents.base import LLMProvider
from lgp.agents.ollama_provider import OllamaProvider


def create_agent_node(
    provider_type: str,
    config: Dict[str, Any],
    provider_config: Dict[str, Any]
) -> Callable:
    """
    Create a LangGraph node function for the specified provider.

    This factory function creates agent nodes that can be injected into workflows.
    The returned function has the signature: async def node(state) -> state_updates

    Args:
        provider_type: Provider identifier ("ollama", "claude_code", etc.)
        config: Agent configuration (role_name, model, timeout, etc.)
        provider_config: Global provider configuration from YAML

    Returns:
        Async function that executes agent task and returns state updates

    Raises:
        ValueError: If provider_type is unknown or not enabled

    Example:
        # Create Ollama writer node
        node = create_agent_node(
            provider_type="ollama",
            config={"role_name": "writer", "model": "llama3.2", "timeout": 120000},
            provider_config={"base_url": "http://localhost:11434/v1"}
        )

        # Use in workflow
        workflow.add_node("writer_agent", node)
    """
    # Validate provider is enabled
    if not provider_config.get("enabled", False):
        raise ValueError(
            f"Provider '{provider_type}' is configured but not enabled. "
            f"Set llm_providers.{provider_type}.enabled: true in config"
        )

    # Dispatch to correct provider
    if provider_type == "ollama":
        return create_ollama_node(config, provider_config)
    elif provider_type == "claude_code":
        # Import here to avoid circular dependency
        from lgp.claude_code.node_factory import create_claude_code_node as create_cc_node
        from lgp.claude_code.session_manager import get_default_manager

        # Claude Code uses MCP manager, not provider_config
        return create_cc_node(config, get_default_manager())
    else:
        raise ValueError(
            f"Unknown provider: '{provider_type}'. "
            f"Supported providers: ollama, claude_code"
        )


def create_ollama_node(
    config: Dict[str, Any],
    provider_config: Dict[str, Any]
) -> Callable:
    """
    Create Ollama agent node.

    Args:
        config: Agent configuration with role_name, model, timeout
        provider_config: Ollama provider configuration from YAML

    Returns:
        Async function for LangGraph node
    """
    # Extract Ollama-specific settings from provider config
    base_url = provider_config.get("base_url", "http://localhost:11434/v1")
    default_model = provider_config.get("default_model", "llama3.2")

    # Use model from config, fall back to default
    if "model" not in config:
        config["model"] = default_model

    # Create provider instance
    provider = OllamaProvider(config, base_url=base_url)

    # Return async node function that matches LangGraph signature
    async def ollama_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ollama agent node for LangGraph workflow.

        Reads task from state (e.g., writer_task or validator_task),
        executes via Ollama, and returns state updates.

        Args:
            state: Current workflow state

        Returns:
            State updates from provider execution
        """
        role_name = config["role_name"]
        task_key = f"{role_name}_task"

        # Get task from state
        task = state.get(task_key, "")

        if not task:
            # No task provided - return empty output
            return {
                f"{role_name}_output": f"No task provided for {role_name}",
                f"{role_name}_session_id": "no-session"
            }

        # Execute task via Ollama provider
        state_updates = await provider.execute_task(
            task=task,
            state=state,
            config={}  # Ollama doesn't use LangGraph config
        )

        return state_updates

    return ollama_node
