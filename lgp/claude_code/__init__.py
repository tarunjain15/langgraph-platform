"""
Claude Code Integration for LangGraph Platform

Enables stateful Claude Code sessions as LangGraph nodes with:
- Session continuity (session_id persistence via checkpointer)
- Repository isolation (each node in separate workspace)
- Fixed cost model ($20/month Claude Pro subscription)
- Full Langfuse observability

Example:
    >>> from lgp.claude_code import create_claude_code_node, MCPSessionManager
    >>>
    >>> manager = MCPSessionManager()
    >>> async with manager.create_session() as session:
    >>>     researcher_node = create_claude_code_node(
    >>>         {'role_name': 'researcher', 'repository': 'sample-app', 'timeout': 60000},
    >>>         session
    >>>     )
    >>>     result = await researcher_node({'task': 'Research topic'})
"""

from .session_manager import MCPSessionManager, get_default_manager
from .node_factory import (
    create_claude_code_node,
    AgentRoleConfig,
    sanitize_for_dashboard
)

__all__ = [
    "MCPSessionManager",
    "get_default_manager",
    "create_claude_code_node",
    "AgentRoleConfig",
    "sanitize_for_dashboard"
]
