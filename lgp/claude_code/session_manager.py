"""
MCP Session Manager for Claude Code Integration

Manages MCP client session lifecycle for Claude Code nodes.
Based on mesh-mcp architecture with claude-mcp Docker container.
"""

from typing import Optional
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPSessionManager:
    """Manages MCP client session for Claude Code interactions"""

    def __init__(self, container_name: str = "claude-mcp"):
        """
        Initialize MCP session manager.

        Args:
            container_name: Docker container name running mesh-mcp server
        """
        self.container_name = container_name
        self.server_params = StdioServerParameters(
            command="docker",
            args=[
                "exec",
                "-i",
                container_name,
                "node",
                "/app/dist/index.js"
            ]
        )

    @asynccontextmanager
    async def create_session(self):
        """
        Create MCP client session with lifecycle management.

        Yields:
            ClientSession: Initialized MCP session for mesh_execute calls

        Example:
            >>> manager = MCPSessionManager()
            >>> async with manager.create_session() as session:
            >>>     result = await session.call_tool('mesh_execute', {...})
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()

                # Yield session for use
                yield session


def get_default_manager() -> MCPSessionManager:
    """
    Get default MCP session manager instance.

    Returns:
        MCPSessionManager configured for claude-mcp container
    """
    return MCPSessionManager(container_name="claude-mcp")
