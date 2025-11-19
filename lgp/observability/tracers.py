"""
Langfuse Tracer Integration for LangGraph Platform

Provides centralized Langfuse client management with automatic trace tagging
and metadata injection for all workflow executions.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables from .env file
load_dotenv()


class LangfuseTracer:
    """Centralized Langfuse tracer manager with singleton pattern."""

    _instance: Optional[Langfuse] = None
    _enabled: bool = False

    @classmethod
    def configure(
        cls,
        secret_key: Optional[str] = None,
        public_key: Optional[str] = None,
        host: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Configure Langfuse client with credentials.

        Args:
            secret_key: Langfuse secret key (default: LANGFUSE_SECRET_KEY env var)
            public_key: Langfuse public key (default: LANGFUSE_PUBLIC_KEY env var)
            host: Langfuse host URL (default: LANGFUSE_BASE_URL or cloud.langfuse.com)
            enabled: Enable/disable tracing (default: True)
        """
        cls._enabled = enabled

        if not enabled:
            return

        secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        host = host or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

        if not secret_key or not public_key:
            print("[lgp] Warning: Langfuse credentials not found. Tracing disabled.")
            cls._enabled = False
            return

        cls._instance = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host
        )

        print(f"[lgp] Observability: Langfuse enabled ({host})")

    @classmethod
    def get_client(cls) -> Optional[Langfuse]:
        """Get the Langfuse client instance."""
        return cls._instance if cls._enabled else None

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if Langfuse tracing is enabled."""
        return cls._enabled

    @classmethod
    def flush(cls):
        """Flush all pending traces to Langfuse."""
        if cls._instance and cls._enabled:
            cls._instance.flush()

    @staticmethod
    def get_metadata(
        workflow_name: str,
        environment: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate standardized metadata for traces.

        Args:
            workflow_name: Name of the workflow being executed
            environment: Runtime environment (experiment/hosted)
            **kwargs: Additional metadata fields

        Returns:
            Dictionary with standardized metadata
        """
        metadata = {
            "workflow_name": workflow_name,
            "environment": environment,
            "runtime_version": "0.1.0",
            "repository": "langgraph-platform",
        }
        metadata.update(kwargs)
        return metadata

    @staticmethod
    def get_tags(workflow_name: str, environment: str) -> list[str]:
        """
        Generate standardized tags for trace filtering.

        Args:
            workflow_name: Name of the workflow
            environment: Runtime environment

        Returns:
            List of tags for Langfuse dashboard filtering
        """
        return [
            "langgraph-platform",
            f"workflow:{workflow_name}",
            f"env:{environment}",
        ]


# Convenience functions
def configure_langfuse(
    secret_key: Optional[str] = None,
    public_key: Optional[str] = None,
    host: Optional[str] = None,
    enabled: bool = True
):
    """Configure Langfuse tracer."""
    LangfuseTracer.configure(
        secret_key=secret_key,
        public_key=public_key,
        host=host,
        enabled=enabled
    )


def get_tracer() -> Optional[Langfuse]:
    """Get the Langfuse client instance."""
    return LangfuseTracer.get_client()


def flush_traces():
    """Flush all pending traces to Langfuse."""
    LangfuseTracer.flush()


def is_tracing_enabled() -> bool:
    """Check if Langfuse tracing is enabled."""
    return LangfuseTracer.is_enabled()
