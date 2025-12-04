"""
MCP Tool Registry for General Manager.

Manages connections to MCP servers (Playwright, Filesystem, Brave Search).
Enforces SOVEREIGN_TOOL_ACCESS and MCP_PROTOCOL_COMPLIANCE constraints.
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .config import ToolType


@dataclass
class ToolSchema:
    """Schema for a tool available via MCP."""
    name: str
    description: str
    parameters: Dict[str, Any]


class MCPConnection(ABC):
    """Abstract base class for MCP server connections."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[ToolSchema]:
        """List available tools from this server."""
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return result."""
        pass


class StdioMCPConnection(MCPConnection):
    """
    MCP connection via stdio transport.

    Spawns MCP server as subprocess and communicates via stdin/stdout.
    Supports environment variable injection per MCP specification.
    """

    def __init__(self, command: List[str], name: str, env: Optional[Dict[str, str]] = None):
        self.command = command
        self.name = name
        self.env = env  # Custom env vars for this server
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._tools_cache: List[ToolSchema] = []

    async def connect(self) -> bool:
        """Start MCP server subprocess with optional custom environment."""
        import os

        try:
            # Merge custom env with current environment
            process_env = os.environ.copy()
            if self.env:
                process_env.update(self.env)

            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env
            )

            # Send initialize request
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "general-manager",
                    "version": "1.0"
                }
            })

            if init_response and "result" in init_response:
                # Send initialized notification
                await self._send_notification("notifications/initialized", {})
                return True

            return False

        except Exception as e:
            print(f"Failed to connect to {self.name}: {e}", file=sys.stderr)
            return False

    async def disconnect(self) -> None:
        """Terminate MCP server subprocess."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None

    async def list_tools(self) -> List[ToolSchema]:
        """Get available tools from MCP server."""
        if self._tools_cache:
            return self._tools_cache

        response = await self._send_request("tools/list", {})

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            self._tools_cache = [
                ToolSchema(
                    name=t["name"],
                    description=t.get("description", ""),
                    parameters=t.get("inputSchema", {})
                )
                for t in tools
            ]

        return self._tools_cache

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool via MCP protocol."""
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"Tool error: {response['error']}")

        return None

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Send JSON-RPC request and wait for response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }

        message = json.dumps(request) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()

        # Read response
        try:
            line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=30.0
            )
            if line:
                return json.loads(line.decode())
        except asyncio.TimeoutError:
            print(f"Timeout waiting for response from {self.name}", file=sys.stderr)

        return None

    async def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send JSON-RPC notification (no response expected)."""
        if not self.process or not self.process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        message = json.dumps(notification) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()


class ToolRegistry:
    """
    Registry of MCP tool connections.

    Manages multiple MCP servers and provides unified tool access.
    Enforces SOVEREIGN_TOOL_ACCESS constraint.
    """

    # MCP server configs: (command, env_vars)
    # Matches Claude Desktop config for compatibility
    MCP_SERVERS: Dict[ToolType, Dict[str, Any]] = {
        ToolType.PLAYWRIGHT: {
            "command": ["npx", "@playwright/mcp@latest"],
            "env": None
        },
        ToolType.FILESYSTEM: {
            "command": [
                "npx", "-y", "@modelcontextprotocol/server-filesystem",
                "/Users/tarun/workspace/",
                "/tmp"
            ],
            "env": None
        },
        ToolType.BRAVE_SEARCH: {
            "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")}
        }
    }

    def __init__(self):
        self.connections: Dict[ToolType, MCPConnection] = {}
        self._all_tools: Dict[str, tuple[ToolType, ToolSchema]] = {}

    async def register_tools(self, tool_types: List[ToolType]) -> None:
        """
        Connect to MCP servers for specified tool types.

        Args:
            tool_types: List of tool types to register
        """
        for tool_type in tool_types:
            if tool_type not in self.MCP_SERVERS:
                print(f"Unknown tool type: {tool_type}", file=sys.stderr)
                continue

            config = self.MCP_SERVERS[tool_type]
            command = config["command"]
            env = config.get("env")

            connection = StdioMCPConnection(command, tool_type.value, env=env)

            if await connection.connect():
                self.connections[tool_type] = connection

                # Cache tools with their source
                tools = await connection.list_tools()
                for tool in tools:
                    self._all_tools[tool.name] = (tool_type, tool)

                print(f"Connected to {tool_type.value}: {len(tools)} tools available")
            else:
                print(f"Failed to connect to {tool_type.value}", file=sys.stderr)

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for connection in self.connections.values():
            await connection.disconnect()
        self.connections.clear()
        self._all_tools.clear()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all tool schemas in OpenAI function format.

        Used for LLM tool calling.
        """
        schemas = []
        for name, (_, tool) in self._all_tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return schemas

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool execution fails
        """
        if name not in self._all_tools:
            raise ValueError(f"Unknown tool: {name}")

        tool_type, _ = self._all_tools[name]
        connection = self.connections.get(tool_type)

        if not connection:
            raise RuntimeError(f"No connection for tool type: {tool_type}")

        return await connection.call_tool(name, arguments)

    def list_available_tools(self) -> List[str]:
        """List names of all available tools."""
        return list(self._all_tools.keys())


async def create_tool_registry(tool_types: List[ToolType]) -> ToolRegistry:
    """
    Factory function to create and initialize a tool registry.

    Args:
        tool_types: List of tool types to register

    Returns:
        Initialized ToolRegistry
    """
    registry = ToolRegistry()
    await registry.register_tools(tool_types)
    return registry
