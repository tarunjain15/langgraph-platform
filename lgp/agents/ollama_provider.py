"""
Ollama LLM Provider - Self-hosted, $0 cost language models.

Integrates Ollama (local LLM server) with LangGraph workflows using the
proven pattern from langfuse-ollama-test repository.

Key Features:
- Zero cost ($0.00) inference
- Offline capability
- Automatic Langfuse tracing via OpenAI-compatible API
- Multiple model support (Llama 3.2, Mistral, Gemma, etc.)
"""

import os
from typing import Dict, Any, Optional
from langfuse import observe
from langfuse.openai import OpenAI
from lgp.agents.base import LLMProvider


class OllamaProvider(LLMProvider):
    """
    Ollama provider for self-hosted LLM execution.

    Uses Ollama's OpenAI-compatible API (http://localhost:11434/v1) to provide
    drop-in replacement for cloud LLMs with zero cost.

    Example configuration:
        {
            "role_name": "writer",
            "provider": "ollama",
            "model": "llama3.2",
            "timeout": 120000
        }
    """

    def __init__(self, config: Dict[str, Any], base_url: Optional[str] = None):
        """
        Initialize Ollama provider.

        Args:
            config: Agent configuration from workflow claude_code_config
            base_url: Ollama API endpoint (default: http://localhost:11434/v1)
        """
        self.role_name = config.get("role_name")
        self.model = config.get("model", "llama3.2")
        self.timeout = config.get("timeout", 120000)  # milliseconds

        # Initialize OpenAI client pointing to Ollama
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434/v1"
        )

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=os.getenv("OLLAMA_API_KEY", "ollama")  # Dummy key for Ollama
        )

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "ollama"

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Return cost estimate for Ollama.

        Ollama is self-hosted, so cost is always $0.00.
        (Ignoring electricity and hardware depreciation)

        Returns:
            0.0 (zero cost for self-hosted inference)
        """
        return 0.0

    def get_metadata(self) -> Dict[str, Any]:
        """
        Return metadata for Langfuse tracing.

        This metadata appears in Langfuse dashboard for filtering/analysis.
        """
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "role": self.role_name,
            "cost": "$0.00"
        }

    @observe(name="ollama_execute_task")
    async def execute_task(
        self,
        task: str,
        state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task using Ollama LLM.

        Follows the proven pattern from langfuse-ollama-test/src/test_llama32.py:
        - Uses Langfuse OpenAI wrapper for automatic tracing
        - Calls Ollama via OpenAI-compatible API
        - Returns state updates in LangGraph format

        Args:
            task: Task description (from prepare_optimizer/prepare_evaluator)
            state: Current workflow state
            config: Execution config (not used for Ollama)

        Returns:
            State updates with:
                - {role_name}_output: LLM response text
                - {role_name}_session_id: Session identifier (for continuity)
                - {role_name}_tokens: Token usage stats
        """
        # Call Ollama via OpenAI-compatible API
        # Langfuse wrapper automatically creates trace span
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert software engineer helping with code optimization and testing."
                },
                {
                    "role": "user",
                    "content": task
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            # Timeout handling: Ollama doesn't directly support timeout in API
            # The workflow executor's timeout will catch long-running operations
        )

        # Extract response
        output = response.choices[0].message.content
        usage = response.usage

        # Build state updates
        # Key pattern: {role_name}_output, {role_name}_session_id, etc.
        state_updates = {
            f"{self.role_name}_output": output,
            f"{self.role_name}_session_id": response.id,  # Response ID as session
            f"{self.role_name}_tokens": {
                "input": usage.prompt_tokens,
                "output": usage.completion_tokens,
                "total": usage.total_tokens,
                "cost": 0.0  # Self-hosted = $0
            }
        }

        return state_updates

    def is_available(self) -> bool:
        """
        Check if Ollama service is running and model is available.

        Returns:
            True if Ollama responds to test query, False otherwise
        """
        try:
            # Quick test query
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            return False

    def __repr__(self) -> str:
        return f"OllamaProvider(role={self.role_name}, model={self.model}, cost=$0.00)"
