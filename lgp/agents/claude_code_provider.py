"""
Claude Code CLI Provider - Langfuse-native at the same level as Ollama/OpenAI.

The minimal interface that presents Claude Code CLI as a simple method call
compatible with Langfuse tracing and LangGraph workflows.

Key Features:
- Same LLMProvider interface as OllamaProvider
- Direct subprocess + JSON (no MCP bridge complexity)
- Native cost tracking from CLI response
- Optional session continuity via state["session_id"]

Architecture:
    LangGraph → ClaudeCodeProvider.execute_task() → subprocess.run()
        → claude CLI → JSON response → state_updates

Reference: sacred-core-claude-cli/
"""

import json
import subprocess
import asyncio
import os
from typing import Dict, Any, Optional, List
from lgp.agents.base import LLMProvider

# Conditional import - only use @observe if Langfuse is properly configured
def _get_observe_decorator():
    """Get observe decorator only if Langfuse is configured."""
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        from langfuse import observe
        return observe
    else:
        # No-op decorator when Langfuse not configured
        def noop_observe(**kwargs):
            def decorator(func):
                return func
            return decorator
        return noop_observe

observe = _get_observe_decorator()


class ClaudeCodeProvider(LLMProvider):
    """
    Claude Code CLI provider - stateless by default, simple subprocess call.

    Equivalent to Ollama/OpenAI at the Langfuse integration level.
    All statefulness (session continuity) is OPTIONAL via state["session_id"].

    Example configuration:
        {
            "role_name": "researcher",
            "provider": "claude_code",
            "model": "sonnet",
            "allowed_tools": ["Read", "Grep", "Glob"],
            "max_turns": 10,
            "cwd": "/path/to/workspace",
            "container": None  # or "claude-mcp" for isolation
        }
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Claude Code CLI provider.

        Args:
            config: Provider configuration
                - role_name: Agent role identifier
                - model: haiku, sonnet, or opus (default: sonnet)
                - allowed_tools: List of permitted tools
                - max_turns: Maximum conversation turns
                - cwd: Working directory for CLI
                - container: Docker container name for isolation (optional)
                - timeout: Timeout per turn in seconds (default: 30)
        """
        self.role_name = config.get("role_name", "agent")
        self.model = config.get("model", "sonnet")
        self.allowed_tools = config.get("allowed_tools", ["Read", "Grep", "Glob"])
        self.max_turns = config.get("max_turns", 10)
        self.cwd = config.get("cwd", ".")
        self.container = config.get("container")  # None = local CLI
        self.timeout_per_turn = config.get("timeout", 30)  # seconds per turn

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "claude_code"

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Cost estimate - placeholder since CLI provides actual cost.

        Claude Code CLI returns total_cost_usd directly, so this is
        primarily for interface compatibility. Actual cost comes from
        the CLI response.

        Returns:
            Rough estimate based on Sonnet pricing
        """
        # Sonnet pricing as rough estimate: $3/1M input, $15/1M output
        return (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Return metadata for Langfuse tracing.

        This metadata appears in Langfuse dashboard for filtering/analysis.
        """
        return {
            "provider": "claude_code",
            "model": self.model,
            "role": self.role_name,
            "allowed_tools": self.allowed_tools,
            "max_turns": self.max_turns,
            "container": self.container or "local"
        }

    def _build_command(
        self,
        prompt: str,
        session_id: Optional[str] = None
    ) -> List[str]:
        """
        Build claude CLI command with all required flags.

        Args:
            prompt: Task prompt
            session_id: Optional session ID for continuity

        Returns:
            Command list for subprocess.run()
        """
        cmd = []

        # Container prefix if specified
        if self.container:
            cmd = ["docker", "exec", self.container]

        # Core claude command
        cmd.extend([
            "claude",
            "-p", prompt,
            "--output-format", "json",
            "--model", self.model,
            "--max-turns", str(self.max_turns),
            "--allowedTools", ",".join(self.allowed_tools)
        ])

        # Session resume for continuity
        if session_id:
            cmd.extend(["--resume", session_id])

        return cmd

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse CLI JSON response into LangGraph state updates.

        Args:
            response: Parsed JSON from CLI stdout

        Returns:
            State updates dict with {role}_output, {role}_session_id, {role}_tokens
        """
        return {
            f"{self.role_name}_output": response.get("result", ""),
            f"{self.role_name}_session_id": response.get("session_id"),
            f"{self.role_name}_tokens": {
                "cost": response.get("total_cost_usd", 0.0),
                "turns": response.get("num_turns", 0),
                "duration_ms": response.get("duration_ms", 0),
                "duration_api_ms": response.get("duration_api_ms", 0)
            }
        }

    def _handle_error(self, result: subprocess.CompletedProcess) -> None:
        """
        Handle CLI errors with actionable messages.

        Args:
            result: Completed subprocess result

        Raises:
            RuntimeError: If CLI returned error
        """
        if result.returncode != 0:
            # Try to parse error from JSON response
            try:
                error_data = json.loads(result.stdout)
                if error_data.get("is_error"):
                    raise RuntimeError(
                        f"Claude Code error: {error_data.get('result', 'Unknown error')}"
                    )
            except json.JSONDecodeError:
                pass

            # Fall back to stderr message
            stderr = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(
                f"Claude Code CLI failed (exit {result.returncode}): {stderr}"
            )

    @observe(name="claude_code_execute")
    async def execute_task(
        self,
        task: str,
        state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task via Claude Code CLI.

        This is the MINIMAL interface - a single subprocess call
        that returns Langfuse-compatible tracing data.

        Args:
            task: Task description/prompt
            state: Current workflow state (may contain session_id for continuity)
            config: Execution config (unused, for interface compatibility)

        Returns:
            State updates with output, session_id, and token metadata

        Example:
            >>> provider = ClaudeCodeProvider({"role_name": "researcher"})
            >>> result = await provider.execute_task("Analyze README.md", {}, {})
            >>> print(result["researcher_output"])
        """
        # Get session_id for continuity (optional)
        session_key = f"{self.role_name}_session_id"
        session_id = state.get(session_key)

        # Build CLI command
        cmd = self._build_command(task, session_id)

        # Calculate timeout (configurable seconds per turn)
        timeout = self.max_turns * self.timeout_per_turn

        # Determine working directory
        cwd = None if self.container else self.cwd

        # Run CLI in thread pool (subprocess is blocking)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=timeout,
                    env={**os.environ}  # Inherit environment for API keys
                )
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Claude Code CLI timed out after {timeout}s "
                f"(max_turns={self.max_turns}, timeout_per_turn={self.timeout_per_turn}s)"
            )

        # Handle errors
        self._handle_error(result)

        # Parse JSON response
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse CLI response: {e}\n"
                f"Output (first 500 chars): {result.stdout[:500]}"
            )

        return self._parse_response(response)

    def is_available(self) -> bool:
        """
        Check if Claude Code CLI is available.

        Returns:
            True if CLI responds to --version, False otherwise
        """
        try:
            cmd = ["claude", "--version"]
            if self.container:
                cmd = ["docker", "exec", self.container] + cmd

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def __repr__(self) -> str:
        container_str = f", container={self.container}" if self.container else ""
        tools_str = ",".join(self.allowed_tools[:3])
        if len(self.allowed_tools) > 3:
            tools_str += f"...+{len(self.allowed_tools)-3}"
        return (
            f"ClaudeCodeProvider(role={self.role_name}, model={self.model}, "
            f"tools=[{tools_str}]{container_str})"
        )
