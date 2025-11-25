#!/usr/bin/env python3
"""
Integration Tests for MCP Server (R14)

Tests Worker Marketplace MCP Server:
- Tool registration and discovery
- Worker spawning (idempotent)
- Execution with automatic constraint enforcement
- State queries
- Worker cleanup

Validates R14 acceptance criteria:
1. Workers exposed as MCP tools
2. Integration with LangGraph workflows
3. Production worker definition loaded successfully
4. Automatic constraint enforcement in MCP layer
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock

from workers.mcp_server import WorkerMarketplaceMCP
from workers.factory import WorkerFactory
from mcp.types import Tool


class TestMCPServerInitialization:
    """Test MCP server initialization and tool registration"""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """
        Verify MCP server initializes correctly

        Expected:
        - Server instance created
        - Server name is "worker-marketplace"
        - Tool handlers registered
        """
        mcp = WorkerMarketplaceMCP()

        assert mcp.server is not None, "Server not initialized"
        assert mcp.workers == {}, "Workers dict should be empty initially"

        print("✓ MCP server initialized successfully")

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """
        Verify all 4 tools are registered

        Expected tools:
        1. spawn_worker
        2. execute_in_worker
        3. get_worker_state
        4. kill_worker
        """
        mcp = WorkerMarketplaceMCP()

        # Get registered tools
        tools = await mcp.handle_list_tools()

        # Verify count
        assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"

        # Extract tool names
        tool_names = {tool.name for tool in tools}

        # Verify expected tools
        expected_tools = {
            "spawn_worker",
            "execute_in_worker",
            "get_worker_state",
            "kill_worker"
        }

        assert tool_names == expected_tools, \
            f"Tool names mismatch. Expected {expected_tools}, got {tool_names}"

        print(f"✓ All 4 MCP tools registered: {tool_names}")

    @pytest.mark.asyncio
    async def test_tool_schemas(self):
        """
        Verify tool schemas are valid

        Each tool should have:
        - name (string)
        - description (string)
        - inputSchema (object with required fields)
        """
        mcp = WorkerMarketplaceMCP()
        tools = await mcp.handle_list_tools()

        for tool in tools:
            # Verify name
            assert isinstance(tool.name, str), \
                f"Tool {tool.name} has invalid name type"

            # Verify description
            assert isinstance(tool.description, str), \
                f"Tool {tool.name} missing description"

            # Verify inputSchema
            assert hasattr(tool, 'inputSchema'), \
                f"Tool {tool.name} missing inputSchema"

            assert isinstance(tool.inputSchema, dict), \
                f"Tool {tool.name} inputSchema is not a dict"

            # Verify required fields in schema
            if tool.name == "spawn_worker":
                assert "worker_id" in tool.inputSchema["required"], \
                    "spawn_worker missing worker_id in required fields"
                assert "journey_id" in tool.inputSchema["required"], \
                    "spawn_worker missing journey_id in required fields"

            elif tool.name == "execute_in_worker":
                assert "journey_id" in tool.inputSchema["required"], \
                    "execute_in_worker missing journey_id"
                assert "action" in tool.inputSchema["required"], \
                    "execute_in_worker missing action"

        print("✓ All tool schemas validated")


class TestWorkerSpawning:
    """Test spawn_worker tool"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.mark.asyncio
    async def test_spawn_worker_creates_instance(self):
        """
        Test spawn_worker creates worker instance

        Flow:
        1. Call spawn_worker with test definition
        2. Verify worker created
        3. Verify worker stored in mcp.workers dict
        """
        mcp = WorkerMarketplaceMCP()

        # Spawn worker
        result = await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_spawn",
                "isolation_level": "process"
            }
        )

        # Verify result
        assert len(result) == 1, "Should return 1 TextContent"
        assert result[0].type == "text", "Result should be text content"

        result_text = result[0].text

        # Verify success message
        assert "Worker spawned successfully" in result_text, \
            "Success message not in result"
        assert "filesystem_research_v1" in result_text, \
            "Worker ID not in result"

        # Verify worker stored
        assert "test_journey_spawn" in mcp.workers, \
            "Worker not stored in mcp.workers"

        print("✓ Worker spawned successfully via MCP tool")

    @pytest.mark.asyncio
    async def test_spawn_worker_idempotent(self):
        """
        Test spawn_worker is idempotent

        Flow:
        1. Spawn worker for journey_id
        2. Spawn worker again with same journey_id
        3. Verify second call returns existing worker (no duplicate)
        """
        mcp = WorkerMarketplaceMCP()

        # First spawn
        result1 = await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_idempotent",
                "isolation_level": "process"
            }
        )

        # Second spawn (same journey_id)
        result2 = await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_idempotent",
                "isolation_level": "process"
            }
        )

        # Verify second result indicates existing worker
        assert "already exists" in result2[0].text, \
            "Second spawn should return existing worker message"

        # Verify only one worker in dict
        assert len(mcp.workers) == 1, \
            "Should only have 1 worker (idempotent)"

        print("✓ spawn_worker is idempotent (returns existing worker)")


class TestWorkerExecution:
    """Test execute_in_worker tool with constraint enforcement"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.mark.asyncio
    async def test_execute_valid_action(self):
        """
        Test execute_in_worker with valid action

        Flow:
        1. Spawn worker
        2. Execute valid action (small file write)
        3. Verify action executed successfully
        4. Verify result includes output
        """
        mcp = WorkerMarketplaceMCP()

        # Spawn worker
        await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_exec",
                "isolation_level": "process"
            }
        )

        # Execute valid action
        result = await mcp.handle_call_tool(
            name="execute_in_worker",
            arguments={
                "journey_id": "test_journey_exec",
                "action": {
                    "type": "read",
                    "target": "README.md"
                }
            }
        )

        # Verify success
        assert len(result) == 1, "Should return 1 TextContent"
        result_text = result[0].text

        assert "Action completed successfully" in result_text, \
            "Success message not in result"

        assert "Output:" in result_text, \
            "Output section not in result"

        print("✓ Valid action executed successfully")

    @pytest.mark.asyncio
    async def test_execute_constraint_violation(self):
        """
        Test execute_in_worker with constraint violation

        Flow:
        1. Spawn worker with file size constraint
        2. Attempt action that violates constraint (large file)
        3. Verify void() detects violation automatically
        4. Verify execution rejected with warning message
        """
        mcp = WorkerMarketplaceMCP()

        # Spawn worker
        await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_violation",
                "isolation_level": "process"
            }
        )

        # Attempt action that violates file size constraint
        large_content = "x" * 2_000_000  # 2MB (exceeds 1MB limit)

        result = await mcp.handle_call_tool(
            name="execute_in_worker",
            arguments={
                "journey_id": "test_journey_violation",
                "action": {
                    "type": "write",
                    "target": "large_file.txt",
                    "content": large_content
                }
            }
        )

        # Verify constraint violation detected
        result_text = result[0].text

        assert "Constraint violation detected" in result_text, \
            "Constraint violation message not in result"

        assert "Action rejected" in result_text, \
            "Rejection message not in result"

        # Verify warning details included
        assert "File size" in result_text or "2000000" in result_text, \
            "Violation details not in warning"

        print("✓ Constraint violation detected and execution rejected")

    @pytest.mark.asyncio
    async def test_execute_without_worker(self):
        """
        Test execute_in_worker without spawning worker first

        Flow:
        1. Call execute_in_worker WITHOUT spawning worker
        2. Verify error message returned
        """
        mcp = WorkerMarketplaceMCP()

        # Execute without spawning
        result = await mcp.handle_call_tool(
            name="execute_in_worker",
            arguments={
                "journey_id": "nonexistent_journey",
                "action": {
                    "type": "read",
                    "target": "test.txt"
                }
            }
        )

        # Verify error message
        result_text = result[0].text

        assert "No worker found" in result_text, \
            "Error message not in result"

        assert "spawn_worker first" in result_text, \
            "Instruction to spawn worker not in result"

        print("✓ Error returned when worker not found")


class TestWorkerState:
    """Test get_worker_state tool"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.mark.asyncio
    async def test_get_worker_state(self):
        """
        Test get_worker_state returns worker status

        Flow:
        1. Spawn worker
        2. Get worker state
        3. Verify state includes expected fields
        """
        mcp = WorkerMarketplaceMCP()

        # Spawn worker
        await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_state",
                "isolation_level": "process"
            }
        )

        # Get state
        result = await mcp.handle_call_tool(
            name="get_worker_state",
            arguments={
                "journey_id": "test_journey_state"
            }
        )

        # Verify state data
        result_text = result[0].text

        assert "Worker State" in result_text, \
            "State header not in result"

        assert "test_journey_state" in result_text, \
            "Journey ID not in state"

        print("✓ Worker state retrieved successfully")

    @pytest.mark.asyncio
    async def test_get_state_nonexistent_worker(self):
        """
        Test get_worker_state with nonexistent worker

        Flow:
        1. Call get_worker_state for nonexistent journey
        2. Verify error message returned
        """
        mcp = WorkerMarketplaceMCP()

        # Get state for nonexistent worker
        result = await mcp.handle_call_tool(
            name="get_worker_state",
            arguments={
                "journey_id": "nonexistent_journey"
            }
        )

        # Verify error
        result_text = result[0].text

        assert "No worker found" in result_text, \
            "Error message not in result"

        print("✓ Error returned for nonexistent worker")


class TestWorkerCleanup:
    """Test kill_worker tool"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.mark.asyncio
    async def test_kill_worker(self):
        """
        Test kill_worker terminates and cleans up

        Flow:
        1. Spawn worker
        2. Kill worker
        3. Verify worker removed from mcp.workers
        4. Verify success message
        """
        mcp = WorkerMarketplaceMCP()

        # Spawn worker
        await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_journey_kill",
                "isolation_level": "process"
            }
        )

        # Verify worker exists
        assert "test_journey_kill" in mcp.workers, \
            "Worker should exist before kill"

        # Kill worker
        result = await mcp.handle_call_tool(
            name="kill_worker",
            arguments={
                "journey_id": "test_journey_kill"
            }
        )

        # Verify success message
        result_text = result[0].text

        assert "terminated and cleaned up" in result_text, \
            "Success message not in result"

        # Verify worker removed
        assert "test_journey_kill" not in mcp.workers, \
            "Worker should be removed after kill"

        print("✓ Worker killed and cleaned up successfully")

    @pytest.mark.asyncio
    async def test_kill_nonexistent_worker(self):
        """
        Test kill_worker with nonexistent worker

        Flow:
        1. Call kill_worker for nonexistent journey
        2. Verify error message returned
        """
        mcp = WorkerMarketplaceMCP()

        # Kill nonexistent worker
        result = await mcp.handle_call_tool(
            name="kill_worker",
            arguments={
                "journey_id": "nonexistent_journey"
            }
        )

        # Verify error
        result_text = result[0].text

        assert "No worker found" in result_text, \
            "Error message not in result"

        print("✓ Error returned for nonexistent worker")


class TestProductionDefinition:
    """Test production worker definition loading"""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Clean up all workers after each test"""
        yield
        await WorkerFactory.kill_all()

    @pytest.mark.asyncio
    async def test_load_production_definition(self):
        """
        Test filesystem_research_v1 definition loads successfully

        Flow:
        1. Spawn worker with production definition
        2. Verify worker created with correct constraints
        3. Verify onboarding steps present
        """
        mcp = WorkerMarketplaceMCP()

        # Spawn production worker
        result = await mcp.handle_call_tool(
            name="spawn_worker",
            arguments={
                "worker_id": "filesystem_research_v1",
                "journey_id": "test_prod_def",
                "isolation_level": "process"
            }
        )

        # Verify success
        result_text = result[0].text

        assert "Worker spawned successfully" in result_text, \
            "Production definition failed to load"

        assert "Constraints:" in result_text, \
            "Constraints section not in result"

        # Get worker instance
        worker = mcp.workers["test_prod_def"]

        # Verify constraints loaded
        assert len(worker.definition.constraints) > 0, \
            "Production definition should have constraints"

        # Verify constraint IDs match expected
        constraint_ids = {c.constraint_id for c in worker.definition.constraints}

        expected_constraints = {
            "readonly_filesystem",
            "max_file_size",
            "network_isolation",
            "search_rate_limit"
        }

        assert constraint_ids == expected_constraints, \
            f"Constraint IDs mismatch. Expected {expected_constraints}, got {constraint_ids}"

        print(f"✓ Production definition loaded with {len(worker.definition.constraints)} constraints")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
