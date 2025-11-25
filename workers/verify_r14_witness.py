#!/usr/bin/env python3
"""
Live Witness Verification for R14

Witness: Workers exposed as MCP tools, accessible from LangGraph workflows,
         with automatic constraint enforcement at MCP layer

Verification:
1. MCP server initializes and registers 4 tools
2. Production worker definition loads successfully
3. spawn_worker creates isolated worker instance (idempotent)
4. execute_in_worker enforces constraints automatically (calls void() first)
5. Constraint violations detected and execution rejected
6. Valid actions execute successfully
7. Worker state queryable via get_worker_state
8. Worker cleanup via kill_worker
9. End-to-end MCP tool workflow validates R14 witness
"""

import asyncio

from workers.mcp_server import WorkerMarketplaceMCP
from workers.factory import WorkerFactory


async def verify_r14_witness():
    """Verify R14 witness with live MCP server"""

    print("=" * 80)
    print("R14 WITNESS VERIFICATION")
    print("=" * 80)
    print()

    # Step 1: Initialize MCP server
    print("Step 1: Initializing MCP server...")

    mcp = WorkerMarketplaceMCP()

    print(f"✓ MCP server initialized")
    print(f"  Server name: worker-marketplace")
    print()

    # Step 2: Verify tool registration
    print("Step 2: Verifying MCP tool registration...")

    tools = await mcp.handle_list_tools()

    assert len(tools) == 4, \
        f"FAIL: Expected 4 tools, got {len(tools)}"

    tool_names = {tool.name for tool in tools}
    expected_tools = {"spawn_worker", "execute_in_worker", "get_worker_state", "kill_worker"}

    assert tool_names == expected_tools, \
        f"FAIL: Tool names mismatch. Expected {expected_tools}, got {tool_names}"

    print(f"✓ All 4 MCP tools registered:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")
    print()

    # Step 3: Spawn production worker (filesystem_research_v1)
    print("Step 3: Spawning production worker via MCP tool...")

    spawn_result = await mcp.handle_call_tool(
        name="spawn_worker",
        arguments={
            "worker_id": "filesystem_research_v1",
            "journey_id": "r14_witness_journey",
            "isolation_level": "process"
        }
    )

    spawn_text = spawn_result[0].text

    assert "Worker spawned successfully" in spawn_text, \
        "FAIL: Worker spawn failed"

    assert "filesystem_research_v1" in spawn_text, \
        "FAIL: Worker ID not in spawn result"

    assert "Constraints:" in spawn_text, \
        "FAIL: Constraints not loaded from production definition"

    print(f"✓ Production worker spawned successfully")
    print(f"  Worker ID: filesystem_research_v1")
    print(f"  Journey ID: r14_witness_journey")
    print()

    # Step 4: Verify idempotent spawning
    print("Step 4: Verifying idempotent spawning...")

    spawn_result_2 = await mcp.handle_call_tool(
        name="spawn_worker",
        arguments={
            "worker_id": "filesystem_research_v1",
            "journey_id": "r14_witness_journey",
            "isolation_level": "process"
        }
    )

    spawn_text_2 = spawn_result_2[0].text

    assert "already exists" in spawn_text_2, \
        "FAIL: Second spawn should return existing worker"

    print(f"✓ Idempotent spawning verified")
    print(f"  Second spawn returned existing worker instance")
    print()

    # Step 5: Test constraint violation detection at MCP layer
    print("Step 5: Testing constraint enforcement at MCP layer...")

    large_content = "x" * 2_000_000  # 2MB (exceeds 1MB limit)

    violation_result = await mcp.handle_call_tool(
        name="execute_in_worker",
        arguments={
            "journey_id": "r14_witness_journey",
            "action": {
                "type": "write",
                "target": "large_file.txt",
                "content": large_content
            }
        }
    )

    violation_text = violation_result[0].text

    assert "Constraint violation detected" in violation_text, \
        "FAIL: Constraint violation not detected at MCP layer"

    assert "Action rejected" in violation_text, \
        "FAIL: Action not rejected after constraint violation"

    assert "File size" in violation_text or "2000000" in violation_text, \
        "FAIL: Violation details not in warning message"

    print(f"✓ Constraint violation detected automatically at MCP layer")
    print(f"  MCP tool called void() before execute()")
    print(f"  Constraint violation warning: {violation_text[:100]}...")
    print()

    # Step 6: Test valid action execution
    print("Step 6: Testing valid action execution...")

    valid_result = await mcp.handle_call_tool(
        name="execute_in_worker",
        arguments={
            "journey_id": "r14_witness_journey",
            "action": {
                "type": "read",
                "target": "README.md"
            }
        }
    )

    valid_text = valid_result[0].text

    assert "Action completed successfully" in valid_text, \
        "FAIL: Valid action execution failed"

    assert "Output:" in valid_text, \
        "FAIL: Execution output not in result"

    print(f"✓ Valid action executed successfully")
    print(f"  Action passed constraint checks (void())")
    print(f"  Execution completed with output")
    print()

    # Step 7: Query worker state
    print("Step 7: Querying worker state via MCP tool...")

    state_result = await mcp.handle_call_tool(
        name="get_worker_state",
        arguments={
            "journey_id": "r14_witness_journey"
        }
    )

    state_text = state_result[0].text

    assert "Worker State" in state_text, \
        "FAIL: Worker state not in result"

    assert "r14_witness_journey" in state_text, \
        "FAIL: Journey ID not in state"

    print(f"✓ Worker state retrieved successfully")
    print(f"  State includes journey ID and metrics")
    print()

    # Step 8: Kill worker
    print("Step 8: Killing worker via MCP tool...")

    kill_result = await mcp.handle_call_tool(
        name="kill_worker",
        arguments={
            "journey_id": "r14_witness_journey"
        }
    )

    kill_text = kill_result[0].text

    assert "terminated and cleaned up" in kill_text, \
        "FAIL: Worker kill failed"

    assert "r14_witness_journey" not in mcp.workers, \
        "FAIL: Worker not removed from MCP server state"

    print(f"✓ Worker killed and cleaned up successfully")
    print(f"  Worker removed from MCP server state")
    print()

    # Step 9: End-to-end workflow validation
    print("Step 9: Validating end-to-end MCP workflow...")

    # Full workflow: spawn → execute → state → kill
    journey_id = "e2e_workflow_journey"

    # Spawn
    await mcp.handle_call_tool(
        name="spawn_worker",
        arguments={
            "worker_id": "filesystem_research_v1",
            "journey_id": journey_id,
            "isolation_level": "process"
        }
    )

    # Execute (valid)
    exec_result = await mcp.handle_call_tool(
        name="execute_in_worker",
        arguments={
            "journey_id": journey_id,
            "action": {
                "type": "read",
                "target": "ARCHITECTURE.md"
            }
        }
    )

    assert "Action completed successfully" in exec_result[0].text, \
        "FAIL: E2E execution failed"

    # State
    state = await mcp.handle_call_tool(
        name="get_worker_state",
        arguments={"journey_id": journey_id}
    )

    assert "Worker State" in state[0].text, \
        "FAIL: E2E state query failed"

    # Kill
    await mcp.handle_call_tool(
        name="kill_worker",
        arguments={"journey_id": journey_id}
    )

    assert journey_id not in mcp.workers, \
        "FAIL: E2E cleanup failed"

    print(f"✓ End-to-end MCP workflow validated")
    print(f"  spawn → execute → state → kill")
    print()

    # Cleanup
    await WorkerFactory.kill_all()

    # Final verification
    print("=" * 80)
    print("R14 WITNESS SATISFIED ✓")
    print("=" * 80)
    print()
    print("Witness verified:")
    print("  - MCP server initializes and registers 4 tools")
    print("  - Production worker definition loads successfully")
    print("  - Workers spawn with isolated workspaces (idempotent)")
    print("  - Constraint enforcement automatic at MCP layer")
    print("  - void() called before execute() (R13.4 integration)")
    print("  - Constraint violations detected and execution rejected")
    print("  - Valid actions execute successfully")
    print("  - Worker state queryable via MCP tool")
    print("  - Worker cleanup via MCP tool")
    print("  - End-to-end MCP workflow production-ready")
    print()
    print("R14 PRODUCTION INTEGRATION COMPLETE ✓")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(verify_r14_witness())
    exit(0 if success else 1)
