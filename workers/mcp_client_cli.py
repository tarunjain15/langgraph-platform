#!/usr/bin/env python3
"""
Interactive MCP Client CLI

Play with the Worker Marketplace MCP server interactively.

Usage:
    python3 workers/mcp_client_cli.py

Commands:
    list                    - List all available tools
    spawn <journey_id>      - Spawn worker for journey
    execute <journey_id>    - Execute action in worker
    state <journey_id>      - Get worker state
    kill <journey_id>       - Kill worker
    help                    - Show this help
    exit                    - Exit CLI
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClientCLI:
    """Interactive MCP client for Worker Marketplace"""

    def __init__(self):
        self.session = None
        self.tools = []

    async def connect(self):
        """Connect to MCP server"""
        print("🔌 Connecting to Worker Marketplace MCP Server...")
        print()

        server_params = StdioServerParameters(
            command="python3",
            args=["workers/mcp_server.py"],
            env={"PYTHONPATH": "."}
        )

        self.client_context = stdio_client(server_params)
        self.streams = await self.client_context.__aenter__()
        read, write = self.streams

        self.session_context = ClientSession(read, write)
        self.session = await self.session_context.__aenter__()

        await self.session.initialize()

        # Load tools
        tools_result = await self.session.list_tools()
        self.tools = tools_result.tools

        print("✅ Connected to Worker Marketplace MCP Server")
        print(f"📦 Loaded {len(self.tools)} tools")
        print()

    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session_context.__aexit__(None, None, None)
            await self.client_context.__aexit__(None, None, None)
        print("👋 Disconnected")

    async def list_tools(self):
        """List available tools"""
        print("📋 Available Tools:")
        print()
        for tool in self.tools:
            print(f"  🔧 {tool.name}")
            print(f"     {tool.description[:80]}...")
            print()

    async def spawn_worker(self, journey_id: str):
        """Spawn worker for journey"""
        print(f"🚀 Spawning worker for journey: {journey_id}")
        print()

        result = await self.session.call_tool(
            "spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": journey_id,
                "isolation_level": "process"
            }
        )

        response = result.content[0].text
        print("📥 Response:")
        print(response)
        print()

    async def execute_action(self, journey_id: str):
        """Execute action in worker"""
        print(f"⚡ Executing action in journey: {journey_id}")
        print()

        # Ask for action type
        print("Choose action:")
        print("  1. Read README.md (valid)")
        print("  2. Write large file (constraint violation)")
        print("  3. Custom action")
        print()

        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            action = {
                "type": "read",
                "target": "README.md"
            }
        elif choice == "2":
            action = {
                "type": "write",
                "target": "large_file.txt",
                "content": "x" * 2_000_000  # 2MB
            }
        elif choice == "3":
            action_type = input("Action type: ").strip()
            target = input("Target: ").strip()
            action = {"type": action_type, "target": target}
        else:
            print("❌ Invalid choice")
            return

        print()
        print(f"📤 Sending action: {action['type']} {action.get('target', '')}")
        print()

        result = await self.session.call_tool(
            "execute_in_worker",
            arguments={
                "journey_id": journey_id,
                "action": action
            }
        )

        response = result.content[0].text
        print("📥 Response:")
        print(response)
        print()

    async def get_state(self, journey_id: str):
        """Get worker state"""
        print(f"📊 Getting state for journey: {journey_id}")
        print()

        result = await self.session.call_tool(
            "get_worker_state",
            arguments={
                "journey_id": journey_id
            }
        )

        response = result.content[0].text
        print("📥 Response:")
        print(response)
        print()

    async def kill_worker(self, journey_id: str):
        """Kill worker"""
        print(f"💀 Killing worker for journey: {journey_id}")
        print()

        result = await self.session.call_tool(
            "kill_worker",
            arguments={
                "journey_id": journey_id
            }
        )

        response = result.content[0].text
        print("📥 Response:")
        print(response)
        print()

    def show_help(self):
        """Show help message"""
        print()
        print("📚 Available Commands:")
        print()
        print("  list                    - List all available tools")
        print("  spawn <journey_id>      - Spawn worker for journey")
        print("  execute <journey_id>    - Execute action in worker")
        print("  state <journey_id>      - Get worker state")
        print("  kill <journey_id>       - Kill worker")
        print("  help                    - Show this help")
        print("  exit                    - Exit CLI")
        print()
        print("💡 Example workflow:")
        print("  1. spawn demo_journey")
        print("  2. execute demo_journey")
        print("  3. state demo_journey")
        print("  4. kill demo_journey")
        print()

    async def run(self):
        """Run interactive CLI"""
        print("=" * 80)
        print("🎮 Worker Marketplace MCP Client CLI")
        print("=" * 80)
        print()

        await self.connect()

        self.show_help()

        while True:
            try:
                # Get command
                command = input("mcp> ").strip()

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0].lower()

                if cmd == "exit" or cmd == "quit":
                    break

                elif cmd == "help":
                    self.show_help()

                elif cmd == "list":
                    await self.list_tools()

                elif cmd == "spawn":
                    if len(parts) < 2:
                        print("❌ Usage: spawn <journey_id>")
                        print()
                        continue
                    journey_id = parts[1]
                    await self.spawn_worker(journey_id)

                elif cmd == "execute":
                    if len(parts) < 2:
                        print("❌ Usage: execute <journey_id>")
                        print()
                        continue
                    journey_id = parts[1]
                    await self.execute_action(journey_id)

                elif cmd == "state":
                    if len(parts) < 2:
                        print("❌ Usage: state <journey_id>")
                        print()
                        continue
                    journey_id = parts[1]
                    await self.get_state(journey_id)

                elif cmd == "kill":
                    if len(parts) < 2:
                        print("❌ Usage: kill <journey_id>")
                        print()
                        continue
                    journey_id = parts[1]
                    await self.kill_worker(journey_id)

                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("💡 Type 'help' for available commands")
                    print()

            except KeyboardInterrupt:
                print()
                print("👋 Use 'exit' to quit")
                print()
            except Exception as e:
                print(f"❌ Error: {e}")
                print()

        await self.disconnect()


async def main():
    """Main entry point"""
    cli = MCPClientCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
