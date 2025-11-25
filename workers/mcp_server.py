#!/usr/bin/env python3
"""
Worker Marketplace MCP Server (R14)

Exposes WorkerFactory as MCP tools for LangGraph integration.

Tools:
- spawn_worker: Create worker instance with workspace
- execute_in_worker: Run action in worker (automatic constraint enforcement)
- get_worker_state: Get current worker status
- kill_worker: Terminate worker and cleanup

Usage:
    python3 workers/mcp_server.py
"""

import asyncio
import logging
from typing import Dict, Any

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Worker imports
from workers.factory import WorkerFactory
from workers.definitions.loader import load_worker_definition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerMarketplaceMCP:
    """
    MCP Server exposing Worker Marketplace.

    Provides persistent, isolated worker instances as MCP tools.
    Workers execute in Docker containers with automatic constraint enforcement.
    """

    def __init__(self):
        self.server = Server("worker-marketplace")
        self.workers: Dict[str, Any] = {}  # journey_id -> worker instance

        # Register tool handlers using decorators
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return await self.handle_list_tools()

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            return await self.handle_call_tool(name, arguments)

    async def handle_list_tools(self) -> list[Tool]:
        """Register available MCP tools"""
        return [
            Tool(
                name="spawn_worker",
                description=(
                    "Spawn isolated worker instance for user journey. "
                    "Workers execute in Docker containers with constrained filesystem. "
                    "Supports workspace pre-seeding and onboarding automation. "
                    "Idempotent - returns existing worker if already spawned for journey."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "worker_id": {
                            "type": "string",
                            "description": "Worker definition ID (e.g., 'research_assistant_v1')"
                        },
                        "journey_id": {
                            "type": "string",
                            "description": "User journey ID (thread_id from checkpointer)"
                        },
                        "isolation_level": {
                            "type": "string",
                            "enum": ["container", "process"],
                            "default": "process",
                            "description": "Isolation boundary (container=Docker, process=lightweight)"
                        }
                    },
                    "required": ["worker_id", "journey_id"]
                }
            ),

            Tool(
                name="execute_in_worker",
                description=(
                    "Execute action in worker workspace with automatic constraint verification. "
                    "Calls void() first to verify constraints, then execute() if safe. "
                    "Returns warnings if constraints violated, output if successful."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "journey_id": {
                            "type": "string",
                            "description": "Journey ID of target worker"
                        },
                        "action": {
                            "type": "object",
                            "description": "Action specification",
                            "properties": {
                                "type": {"type": "string", "description": "Action type (read, write, search, etc.)"},
                                "command": {"type": "string", "description": "Command to execute"},
                                "target": {"type": "string", "description": "Target file/resource"},
                                "content": {"type": "string", "description": "Content for write actions"}
                            },
                            "required": ["type"]
                        }
                    },
                    "required": ["journey_id", "action"]
                }
            ),

            Tool(
                name="get_worker_state",
                description="Get current worker state, metrics, and configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "journey_id": {
                            "type": "string",
                            "description": "Journey ID of target worker"
                        }
                    },
                    "required": ["journey_id"]
                }
            ),

            Tool(
                name="kill_worker",
                description="Terminate worker and cleanup resources (container, workspace)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "journey_id": {
                            "type": "string",
                            "description": "Journey ID of worker to terminate"
                        }
                    },
                    "required": ["journey_id"]
                }
            )
        ]

    async def handle_call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute tool call"""

        logger.info(f"Tool call: {name} with args: {arguments}")

        try:
            if name == "spawn_worker":
                return await self._spawn_worker(
                    worker_id=arguments["worker_id"],
                    journey_id=arguments["journey_id"],
                    isolation_level=arguments.get("isolation_level", "process")
                )

            elif name == "execute_in_worker":
                return await self._execute_in_worker(
                    journey_id=arguments["journey_id"],
                    action=arguments["action"]
                )

            elif name == "get_worker_state":
                return await self._get_worker_state(
                    journey_id=arguments["journey_id"]
                )

            elif name == "kill_worker":
                return await self._kill_worker(
                    journey_id=arguments["journey_id"]
                )

            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    async def _spawn_worker(
        self,
        worker_id: str,
        journey_id: str,
        isolation_level: str
    ) -> list[TextContent]:
        """Spawn worker instance (idempotent)"""

        # Check if worker already exists
        if journey_id in self.workers:
            worker = self.workers[journey_id]
            return [TextContent(
                type="text",
                text=(
                    f"Worker already exists for journey {journey_id}\n"
                    f"Worker ID: {worker.worker_id}\n"
                    f"Workspace: {worker.workspace_path}\n"
                    f"Isolation: {worker.isolation_level}"
                )
            )]

        # Load definition
        # Construct path to definition file
        from pathlib import Path
        definition_path = Path(__file__).parent / "definitions" / "production" / f"{worker_id}.yaml"

        logger.info(f"Loading worker definition: {worker_id} from {definition_path}")
        definition = load_worker_definition(definition_path)

        # Spawn worker
        logger.info(f"Spawning worker {worker_id} for journey {journey_id}")
        worker = await WorkerFactory.spawn(
            definition=definition,
            user_journey_id=journey_id,
            isolation_level=isolation_level
        )

        # Store worker instance
        self.workers[journey_id] = worker

        # Get constraints count
        constraints_count = len(definition.constraints)

        return [TextContent(
            type="text",
            text=(
                f"Worker spawned successfully\n"
                f"Worker ID: {worker.worker_id}\n"
                f"Workspace: {worker.workspace_path}\n"
                f"Isolation: {isolation_level}\n"
                f"Constraints: {constraints_count} enforced\n"
                f"Status: Ready"
            )
        )]

    async def _execute_in_worker(
        self,
        journey_id: str,
        action: Dict[str, Any]
    ) -> list[TextContent]:
        """Execute action in worker with constraint verification"""

        # Get worker
        worker = self.workers.get(journey_id)
        if not worker:
            return [TextContent(
                type="text",
                text=(
                    f"No worker found for journey {journey_id}.\n"
                    f"Call spawn_worker first."
                )
            )]

        # R13.4: Automatic constraint verification
        logger.info(f"Verifying constraints for action: {action.get('type')}")
        void_result = await worker.void(action)

        if void_result.warnings:
            # Constraint violated - abort execution
            warnings_text = "\n".join(f"  - {w}" for w in void_result.warnings)
            return [TextContent(
                type="text",
                text=(
                    f"Constraint violation detected:\n"
                    f"{warnings_text}\n\n"
                    f"Action rejected. Fix violations and retry."
                )
            )]

        # Execute action
        logger.info(f"Executing action in worker {worker.worker_id}")
        exec_result = await worker.execute(action)

        # Format output
        output = exec_result.actual_outcome
        if isinstance(output, dict):
            output_text = "\n".join(f"  {k}: {v}" for k, v in output.items())
        else:
            output_text = str(output)

        return [TextContent(
            type="text",
            text=(
                f"Action completed successfully\n"
                f"Duration: {exec_result.duration_ms:.2f}ms\n"
                f"Output:\n{output_text}"
            )
        )]

    async def _get_worker_state(self, journey_id: str) -> list[TextContent]:
        """Get worker state"""

        worker = self.workers.get(journey_id)
        if not worker:
            return [TextContent(
                type="text",
                text=f"No worker found for journey {journey_id}"
            )]

        state = await worker.state()

        # Format state data
        state_text = "\n".join(f"  {k}: {v}" for k, v in state.data.items())

        return [TextContent(
            type="text",
            text=(
                f"Worker State for {journey_id}:\n"
                f"{state_text}"
            )
        )]

    async def _kill_worker(self, journey_id: str) -> list[TextContent]:
        """Kill worker and cleanup"""

        if journey_id not in self.workers:
            return [TextContent(
                type="text",
                text=f"No worker found for journey {journey_id}"
            )]

        # Kill worker
        await WorkerFactory.kill(journey_id)
        self.workers.pop(journey_id, None)

        return [TextContent(
            type="text",
            text=f"Worker {journey_id} terminated and cleaned up"
        )]

    async def run(self):
        """Run MCP server on stdio"""
        logger.info("Starting Worker Marketplace MCP Server...")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = WorkerMarketplaceMCP()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
