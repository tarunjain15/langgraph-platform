"""
Claude Code Node Factory for LangGraph Integration

Creates LangGraph nodes that execute as stateful Claude Code sessions.
Each node maintains session continuity via session_id in workflow state.

Based on proven patterns from langfuse-langgraph-demo/claude_code_workflow.py
"""

import re
from typing import TypedDict, Dict, Any, Callable


class AgentRoleConfig(TypedDict):
    """Configuration for a Claude Code agent role"""
    role_name: str      # Agent identifier (e.g., "researcher", "writer")
    repository: str     # Repository workspace for isolation
    timeout: int        # Execution timeout in milliseconds


def create_claude_code_node(config: AgentRoleConfig, mcp_session) -> Callable:
    """
    Factory function that creates LangGraph nodes executing as Claude Code sessions.

    Each node:
    - Executes in its own repository workspace (isolation)
    - Maintains a persistent session_id (continuity via checkpointer)
    - Communicates via mesh-mcp → Docker → Claude Code CLI

    Args:
        config: Agent role configuration
        mcp_session: Initialized MCP client session

    Returns:
        Async node function compatible with LangGraph

    Example:
        >>> researcher_config = {
        >>>     'role_name': 'researcher',
        >>>     'repository': 'sample-app',
        >>>     'timeout': 60000
        >>> }
        >>> async with mcp_manager.create_session() as session:
        >>>     researcher_node = create_claude_code_node(researcher_config, session)
        >>>     result = await researcher_node({'task': 'Research topic X'})
    """

    async def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Node function that invokes Claude Code via mesh_execute"""

        # Extract task from state
        task_key = f'{config["role_name"]}_task'
        task = state.get('task') or state.get(task_key)

        if not task:
            raise ValueError(
                f"No task provided for {config['role_name']} "
                f"(expected key: '{task_key}' or 'task')"
            )

        # Get session_id for continuity (stored by R4 checkpointer)
        session_key = f"{config['role_name']}_session_id"
        session_id = state.get(session_key)

        # Prepare mesh_execute arguments
        invoke_args = {
            'repository': config['repository'],
            'task': task,
            'timeout': config['timeout']
        }

        # Resume existing session if available
        if session_id:
            invoke_args['session_id'] = session_id

        # Invoke Claude Code session via mesh-mcp
        # Path: mcp_session.call_tool() → mesh-mcp server
        #       → DockerClaudeService → claude CLI in container
        result = await mcp_session.call_tool(
            'mesh_execute',
            arguments=invoke_args
        )

        # Parse result - mesh-mcp returns text with embedded metadata
        output = None
        returned_session_id = None

        if result.content:
            for item in result.content:
                if hasattr(item, 'text'):
                    text = item.text

                    # Parse session ID from "Session ID: <uuid>"
                    session_match = re.search(r'Session ID: ([a-f0-9-]+)', text)
                    if session_match:
                        returned_session_id = session_match.group(1)

                    # Parse output - comes after "Session ID: <uuid>\n\n<content>"
                    # Stop at metadata section if present
                    output_match = re.search(
                        r'Session ID: [a-f0-9-]+\n\n(.+?)(?:\n\n--- Execution Metadata ---|$)',
                        text,
                        re.DOTALL
                    )
                    if output_match:
                        output = output_match.group(1).strip()

        # Return updated state with output and session_id
        result_state = {
            f'{config["role_name"]}_output': output,
            session_key: returned_session_id,
            'current_step': config['role_name']
        }

        return result_state

    # Attach metadata to node function
    agent_node.__name__ = f"{config['role_name']}_node"
    agent_node.role_name = config['role_name']
    agent_node.repository = config['repository']

    return agent_node


def sanitize_for_dashboard(data: Dict[str, Any], max_string_length: int = 2000) -> Dict[str, Any]:
    """
    Sanitize trace data to prevent Langfuse dashboard errors.

    Large outputs from Claude Code (8-10KB) can cause:
    - Dashboard rendering timeouts
    - React component errors
    - Failed API calls

    This truncates large strings while preserving metadata.

    Args:
        data: Dictionary to sanitize
        max_string_length: Maximum string length before truncation

    Returns:
        Sanitized dictionary with truncated strings
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > max_string_length:
            # Truncate long strings
            result[key] = value[:max_string_length] + f"... (truncated, full length: {len(value)} chars)"
            result[f"{key}_full_length"] = len(value)
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            result[key] = sanitize_for_dashboard(value, max_string_length)
        else:
            result[key] = value

    return result
