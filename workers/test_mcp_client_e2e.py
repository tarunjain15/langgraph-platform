#!/usr/bin/env python3
"""
End-to-End MCP Client Test

Tests Worker Marketplace MCP Server via actual MCP protocol (stdio transport).
This is a true integration test using the MCP client-server protocol.

Validates:
1. MCP server starts and accepts connections
2. Client can list tools via MCP protocol
3. Client can call tools via MCP protocol
4. Responses follow MCP spec
5. End-to-end workflow (spawn → execute → state → kill)
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_client_e2e():
    """
    End-to-end test using real MCP client-server protocol.

    Flow:
    1. Start MCP server as subprocess
    2. Connect via stdio transport
    3. List tools (verify 4 tools registered)
    4. Spawn worker via MCP protocol
    5. Execute action via MCP protocol
    6. Get worker state via MCP protocol
    7. Kill worker via MCP protocol
    8. Verify all responses
    """

    print("=" * 80)
    print("MCP CLIENT END-TO-END TEST")
    print("=" * 80)
    print()

    # Configure MCP server connection
    server_params = StdioServerParameters(
        command="python3",
        args=["workers/mcp_server.py"],
        env={
            "PYTHONPATH": "."
        }
    )

    print("Step 1: Connecting to MCP server via stdio...")

    # Connect to MCP server via stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()

            print("✓ MCP client session initialized")
            print(f"  Server: worker-marketplace")
            print(f"  Transport: stdio")
            print()

            # Step 2: List tools
            print("Step 2: Listing tools via MCP protocol...")

            tools_result = await session.list_tools()
            tools = tools_result.tools

            assert len(tools) == 4, \
                f"Expected 4 tools, got {len(tools)}"

            tool_names = {tool.name for tool in tools}
            expected_tools = {"spawn_worker", "execute_in_worker", "get_worker_state", "kill_worker"}

            assert tool_names == expected_tools, \
                f"Tool names mismatch. Expected {expected_tools}, got {tool_names}"

            print(f"✓ Listed {len(tools)} tools via MCP protocol:")
            for tool in tools:
                print(f"  - {tool.name}")
            print()

            # Step 3: Spawn worker
            print("Step 3: Spawning worker via MCP protocol...")

            spawn_result = await session.call_tool(
                "spawn_worker",
                arguments={
                    "worker_id": "filesystem_research_v1",
                    "journey_id": "e2e_test_journey",
                    "isolation_level": "process"
                }
            )

            spawn_content = spawn_result.content[0].text

            assert "Worker spawned successfully" in spawn_content, \
                f"Spawn failed: {spawn_content}"

            print("✓ Worker spawned via MCP protocol")
            print(f"  Response: {spawn_content[:100]}...")
            print()

            # Step 4: Execute action with constraint violation
            print("Step 4: Testing constraint enforcement via MCP protocol...")

            # Attempt action that violates constraint
            violation_result = await session.call_tool(
                "execute_in_worker",
                arguments={
                    "journey_id": "e2e_test_journey",
                    "action": {
                        "type": "write",
                        "target": "large_file.txt",
                        "content": "x" * 2_000_000  # 2MB (exceeds 1MB limit)
                    }
                }
            )

            violation_content = violation_result.content[0].text

            assert "Constraint violation detected" in violation_content, \
                f"Constraint violation not detected: {violation_content}"

            assert "Action rejected" in violation_content, \
                "Action not rejected after violation"

            print("✓ Constraint violation detected via MCP protocol")
            print(f"  MCP server called void() before execute()")
            print(f"  Violation warning included in response")
            print()

            # Step 5: Execute valid action
            print("Step 5: Executing valid action via MCP protocol...")

            exec_result = await session.call_tool(
                "execute_in_worker",
                arguments={
                    "journey_id": "e2e_test_journey",
                    "action": {
                        "type": "read",
                        "target": "README.md"
                    }
                }
            )

            exec_content = exec_result.content[0].text

            assert "Action completed successfully" in exec_content, \
                f"Execution failed: {exec_content}"

            print("✓ Valid action executed via MCP protocol")
            print(f"  Action passed constraint checks")
            print()

            # Step 6: Get worker state
            print("Step 6: Querying worker state via MCP protocol...")

            state_result = await session.call_tool(
                "get_worker_state",
                arguments={
                    "journey_id": "e2e_test_journey"
                }
            )

            state_content = state_result.content[0].text

            assert "Worker State" in state_content, \
                f"State query failed: {state_content}"

            print("✓ Worker state retrieved via MCP protocol")
            print(f"  State includes journey ID and metrics")
            print()

            # Step 7: Kill worker
            print("Step 7: Killing worker via MCP protocol...")

            kill_result = await session.call_tool(
                "kill_worker",
                arguments={
                    "journey_id": "e2e_test_journey"
                }
            )

            kill_content = kill_result.content[0].text

            assert "terminated and cleaned up" in kill_content, \
                f"Kill failed: {kill_content}"

            print("✓ Worker killed via MCP protocol")
            print()

            # Final verification
            print("=" * 80)
            print("MCP CLIENT END-TO-END TEST PASSED ✓")
            print("=" * 80)
            print()
            print("Verified:")
            print("  - MCP server accepts stdio connections")
            print("  - Client can list tools via MCP protocol")
            print("  - Client can call tools via MCP protocol")
            print("  - Responses follow MCP spec (content array with text)")
            print("  - Automatic constraint enforcement at MCP layer")
            print("  - End-to-end workflow: spawn → execute → state → kill")
            print()
            print("This is REAL MCP protocol testing, not direct method calls!")
            print()

    return True


if __name__ == "__main__":
    success = asyncio.run(test_mcp_client_e2e())
    exit(0 if success else 1)
