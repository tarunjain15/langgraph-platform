"""
LLM Provider Abstraction for General Manager.

Supports Ollama (local), OpenAI, and Claude (API) providers.
Enforces LLM_PROVIDER_ABSTRACTION constraint.
Integrates with Langfuse for observability.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .config import AgencyConfig, AgencyProvider


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement generate() method.
    """

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from LLM.

        Args:
            messages: Conversation history
            tools: Optional tool schemas for function calling

        Returns:
            Response dict with 'message' containing 'content' and optionally 'tool_calls'
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama local LLM provider.

    Connects to Ollama server at localhost:11434.
    Supports tool calling with compatible models.
    """

    def __init__(self, model: str, temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.base_url = "http://localhost:11434"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate response using Ollama chat API."""

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }

        # Add tools if provided (Ollama 0.4+ supports tools)
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                return {
                    "message": {
                        "role": "assistant",
                        "content": "Request timed out. Please try again."
                    }
                }
            except httpx.HTTPStatusError as e:
                return {
                    "message": {
                        "role": "assistant",
                        "content": f"Error from Ollama: {e.response.status_code}"
                    }
                }

    async def health_check(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider (GPT-4o, etc.) with Langfuse tracing.

    Uses langfuse.openai.OpenAI wrapper for automatic observability.
    """

    def __init__(self, model: str, temperature: float = 0.7):
        from langfuse.openai import OpenAI

        self.model = model
        self.temperature = temperature
        self.client = OpenAI()  # Auto-loads OPENAI_API_KEY from env

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate response using OpenAI chat API with Langfuse tracing."""
        import asyncio

        # Build kwargs
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }

        # Add tools if provided
        if tools:
            kwargs["tools"] = tools

        try:
            # Run sync client in executor (langfuse wrapper is sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(**kwargs)
            )

            # Convert OpenAI response format to our standard format
            message = response.choices[0].message

            return {
                "message": {
                    "role": message.role,
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in (message.tool_calls or [])
                    ]
                }
            }
        except Exception as e:
            return {
                "message": {
                    "role": "assistant",
                    "content": f"Error from OpenAI: {str(e)}"
                }
            }

    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            # Quick models list check
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.models.list()
            )
            return True
        except Exception:
            return False


class ClaudeProvider(LLMProvider):
    """
    Claude API provider.

    Placeholder for future implementation.
    """

    def __init__(self, model: str, temperature: float = 0.7):
        self.model = model
        self.temperature = temperature

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate response using Claude API."""
        raise NotImplementedError(
            "Claude provider not yet implemented. Use Ollama for now."
        )

    async def health_check(self) -> bool:
        """Check if Claude API is available."""
        return False  # Not implemented


def create_llm_provider(config: AgencyConfig) -> LLMProvider:
    """
    Factory function for LLM providers.

    Args:
        config: Agency configuration with provider and model

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is unknown
    """
    if config.provider == AgencyProvider.OLLAMA:
        return OllamaProvider(config.model, config.temperature)
    elif config.provider == AgencyProvider.OPENAI:
        return OpenAIProvider(config.model, config.temperature)
    elif config.provider == AgencyProvider.CLAUDE:
        return ClaudeProvider(config.model, config.temperature)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
