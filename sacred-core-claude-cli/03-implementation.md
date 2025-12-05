```yaml
name: Claude Code CLI Implementation
description: Reference implementation for ClaudeCodeProvider.
created: 2025-11-26
```

# Implementation: ClaudeCodeProvider

## Complete Provider Implementation

```python
"""
Claude Code CLI Provider - Langfuse-native at the same level as Ollama/OpenAI.

The minimal interface that presents Claude Code CLI as a simple method call
compatible with Langfuse tracing and LangGraph workflows.

File: lgp/agents/claude_code_provider.py
"""

import json
import subprocess
import asyncio
from typing import Dict, Any, Optional, List
from langfuse import observe, get_client
from lgp.agents.base import LLMProvider


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
        """
        self.role_name = config.get("role_name", "agent")
        self.model = config.get("model", "sonnet")
        self.allowed_tools = config.get("allowed_tools", ["Read", "Grep", "Glob"])
        self.max_turns = config.get("max_turns", 10)
        self.cwd = config.get("cwd", ".")
        self.container = config.get("container")  # None = local CLI

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "claude_code"

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Cost estimate - placeholder since CLI provides actual cost.

        Claude Code CLI returns total_cost_usd directly, so this is
        not used for actual cost tracking.
        """
        # Sonnet pricing as rough estimate
        return (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000)

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata for Langfuse tracing."""
        return {
            "provider": "claude_code",
            "model": self.model,
            "role": self.role_name,
            "allowed_tools": self.allowed_tools,
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

            raise RuntimeError(
                f"Claude Code CLI failed (exit {result.returncode}): {result.stderr}"
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
        """
        # Get session_id for continuity (optional)
        session_key = f"{self.role_name}_session_id"
        session_id = state.get(session_key)

        # Build CLI command
        cmd = self._build_command(task, session_id)

        # Calculate timeout (30s per turn as safety margin)
        timeout = self.max_turns * 30

        # Run CLI in thread pool (subprocess is blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.cwd if not self.container else None,
                timeout=timeout
            )
        )

        # Handle errors
        self._handle_error(result)

        # Parse JSON response
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse CLI response: {e}\nOutput: {result.stdout[:500]}")

        # Update Langfuse with native cost (more accurate than estimation)
        try:
            langfuse = get_client()
            langfuse.update_current_observation(
                usage={"total_cost": response.get("total_cost_usd", 0.0)}
            )
        except Exception:
            pass  # Langfuse update is best-effort

        return self._parse_response(response)

    def is_available(self) -> bool:
        """
        Check if Claude Code CLI is available.

        Returns:
            True if CLI responds, False otherwise
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
        return f"ClaudeCodeProvider(role={self.role_name}, model={self.model}{container_str})"
```

---

## Factory Integration

```python
# lgp/agents/factory.py - Add to existing factory

from lgp.agents.claude_code_provider import ClaudeCodeProvider

def create_agent_node(config: Dict[str, Any], state_schema) -> Callable:
    """
    Create agent node based on provider configuration.

    Args:
        config: Agent configuration with provider type
        state_schema: LangGraph state schema

    Returns:
        Async node function for LangGraph
    """
    provider_type = config.get("provider", "claude_code")

    if provider_type == "ollama":
        from lgp.agents.ollama_provider import OllamaProvider
        provider = OllamaProvider(config)

    elif provider_type == "claude_api":
        from lgp.agents.claude_api_provider import ClaudeAPIProvider
        provider = ClaudeAPIProvider(config)

    elif provider_type == "claude_code":
        provider = ClaudeCodeProvider(config)

    elif provider_type == "claude_code_container":
        # Same provider, with container specified
        provider = ClaudeCodeProvider({
            **config,
            "container": config.get("container", "claude-mcp")
        })

    else:
        raise ValueError(f"Unknown provider: {provider_type}")

    # Wrap provider in LangGraph node
    async def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
        task_key = f"{config['role_name']}_task"
        task = state.get("task") or state.get(task_key)

        if not task:
            raise ValueError(f"No task for {config['role_name']}")

        return await provider.execute_task(task, state, {})

    agent_node.__name__ = f"{config['role_name']}_node"
    return agent_node
```

---

## Usage Examples

### Basic Usage (Stateless)
```python
from lgp.agents.claude_code_provider import ClaudeCodeProvider

# Create provider
provider = ClaudeCodeProvider({
    "role_name": "analyzer",
    "model": "sonnet",
    "allowed_tools": ["Read", "Grep", "Glob"]
})

# Execute task (stateless)
result = await provider.execute_task(
    task="Analyze the architecture of this codebase",
    state={},
    config={}
)

print(result["analyzer_output"])
print(f"Cost: ${result['analyzer_tokens']['cost']}")
```

### Session Continuity
```python
# First call
result1 = await provider.execute_task(
    task="Read and summarize README.md",
    state={},
    config={}
)

# Second call - resume session
result2 = await provider.execute_task(
    task="Now find related documentation files",
    state={"analyzer_session_id": result1["analyzer_session_id"]},
    config={}
)
# Claude Code maintains context from first call
```

### Container Isolation
```python
provider = ClaudeCodeProvider({
    "role_name": "sandboxed_agent",
    "model": "sonnet",
    "allowed_tools": ["Read", "Write", "Bash"],
    "container": "claude-mcp"  # Docker container name
})

# Executes in isolated container
result = await provider.execute_task(
    task="Run tests and fix failures",
    state={},
    config={}
)
```

### LangGraph Workflow Integration
```python
from langgraph.graph import StateGraph
from lgp.agents.factory import create_agent_node

# Define state
class WorkflowState(TypedDict):
    task: str
    researcher_output: str
    researcher_session_id: str
    researcher_tokens: dict

# Create workflow
workflow = StateGraph(WorkflowState)

# Add Claude Code node
researcher_node = create_agent_node({
    "role_name": "researcher",
    "provider": "claude_code",
    "model": "sonnet",
    "allowed_tools": ["Read", "Grep", "Glob"]
}, WorkflowState)

workflow.add_node("researcher", researcher_node)
workflow.set_entry_point("researcher")
workflow.set_finish_point("researcher")

# Compile and run
app = workflow.compile()
result = await app.ainvoke({"task": "Research the codebase structure"})
```

---

## Configuration Reference

### Provider Config
```yaml
role_name: string      # Required: Agent identifier
provider: claude_code  # Required: Provider type
model: sonnet          # Optional: haiku, sonnet, opus (default: sonnet)
allowed_tools:         # Optional: Tool whitelist
  - Read
  - Grep
  - Glob
max_turns: 10          # Optional: Max conversation turns (default: 10)
cwd: /path/to/dir      # Optional: Working directory (default: ".")
container: null        # Optional: Docker container name for isolation
```

### CLI Flag Mapping
```yaml
--model: config["model"]
--max-turns: config["max_turns"]
--allowedTools: config["allowed_tools"].join(",")
--resume: state[f"{role_name}_session_id"]
--output-format: always "json"
-p: task argument
```

### Response Field Mapping
```yaml
CLI Response → State Updates:
  result → {role_name}_output
  session_id → {role_name}_session_id
  total_cost_usd → {role_name}_tokens.cost
  num_turns → {role_name}_tokens.turns
  duration_ms → {role_name}_tokens.duration_ms
```
