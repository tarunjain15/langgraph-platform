"""
Base provider interface for LLM agents in workflows.

Enables multi-provider support (Claude Code, Ollama, future providers)
while maintaining consistent workflow integration.
"""

from typing import Dict, Any, Protocol
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract base class for LLM agent providers.

    All providers (Claude Code, Ollama, GPT, etc.) must implement this interface
    to be compatible with LangGraph workflow injection.
    """

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task and return state updates.

        Args:
            task: Task description/instruction for the agent
            state: Current workflow state
            config: Provider-specific configuration

        Returns:
            Dictionary with state updates to merge into workflow state

        Example:
            {
                "writer_output": "Optimized algorithm...",
                "writer_session_id": "session-123"
            }
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier (e.g., 'ollama', 'claude_code')"""
        pass

    @abstractmethod
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD (0.0 for self-hosted providers)
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Return provider-specific metadata for observability.

        This metadata is automatically attached to Langfuse traces.

        Returns:
            Dictionary with provider metadata (model, version, etc.)
        """
        return {
            "provider": self.get_provider_name()
        }


class ProviderConfig(Protocol):
    """Type hint for provider configuration dictionaries."""

    role_name: str          # Agent role in workflow (e.g., "writer", "validator")
    provider: str           # Provider type ("claude_code", "ollama", etc.)
    timeout: int            # Max execution time in milliseconds

    # Provider-specific fields (not all providers use all fields)
    repository: str         # Claude Code: Repository path
    model: str              # Ollama/GPT: Model name
    base_url: str           # Ollama: API endpoint
    api_key: str            # Cloud providers: API key
