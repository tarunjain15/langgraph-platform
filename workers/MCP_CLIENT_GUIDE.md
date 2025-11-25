# Interactive MCP Client Guide

Play with the Worker Marketplace MCP server interactively!

## Quick Start

```bash
cd /Users/tarun/claude-workspace/workspace/langgraph-platform
PYTHONPATH=. python3 workers/mcp_client_cli.py
```

## Example Session

```
🎮 Worker Marketplace MCP Client CLI
================================================================================

🔌 Connecting to Worker Marketplace MCP Server...

✅ Connected to Worker Marketplace MCP Server
📦 Loaded 4 tools

📚 Available Commands:

  list                    - List all available tools
  spawn <journey_id>      - Spawn worker for journey
  execute <journey_id>    - Execute action in worker
  state <journey_id>      - Get worker state
  kill <journey_id>       - Kill worker
  help                    - Show this help
  exit                    - Exit CLI

💡 Example workflow:
  1. spawn demo_journey
  2. execute demo_journey
  3. state demo_journey
  4. kill demo_journey

mcp> list
📋 Available Tools:

  🔧 spawn_worker
     Spawn isolated worker instance for user journey. Workers execute in Docke...

  🔧 execute_in_worker
     Execute action in worker workspace with automatic constraint verificatio...

  🔧 get_worker_state
     Get current worker state, metrics, and configuration...

  🔧 kill_worker
     Terminate worker and cleanup resources (container, workspace...


mcp> spawn my_journey
🚀 Spawning worker for journey: my_journey

📥 Response:
Worker spawned successfully
Worker ID: filesystem_research_v1_my_journey
Workspace: /tmp/workers/research/my_journey
Isolation: process
Constraints: 4 enforced
Status: Ready


mcp> execute my_journey
⚡ Executing action in journey: my_journey

Choose action:
  1. Read README.md (valid)
  2. Write large file (constraint violation)
  3. Custom action

Enter choice (1-3): 1

📤 Sending action: read README.md

📥 Response:
Action completed successfully
Duration: 12.34ms
Output:
  executed: True
  action_type: read
  workspace: /tmp/workers/research/my_journey
  ...


mcp> execute my_journey
⚡ Executing action in journey: my_journey

Choose action:
  1. Read README.md (valid)
  2. Write large file (constraint violation)
  3. Custom action

Enter choice (1-3): 2

📤 Sending action: write large_file.txt

📥 Response:
Constraint violation detected:
  - File size 2000000 bytes exceeds limit 1000000 bytes

Action rejected. Fix violations and retry.


mcp> state my_journey
📊 Getting state for journey: my_journey

📥 Response:
Worker State for my_journey:
  user_journey_id: my_journey
  workspace_path: /tmp/workers/research/my_journey
  isolation_level: process
  action_count: 2
  ...


mcp> kill my_journey
💀 Killing worker for journey: my_journey

📥 Response:
Worker my_journey terminated and cleaned up


mcp> exit
👋 Disconnected
```

## Commands Reference

### `list`
List all available MCP tools with descriptions.

### `spawn <journey_id>`
Spawn a worker instance for the specified journey ID.
- Uses production worker definition: `filesystem_research_v1`
- Creates isolated workspace
- Enforces constraints automatically

### `execute <journey_id>`
Execute an action in the worker workspace.
- Choice 1: Read README.md (valid action, passes constraints)
- Choice 2: Write large file (triggers constraint violation)
- Choice 3: Custom action (specify type and target)

### `state <journey_id>`
Get current worker state including:
- Journey ID
- Workspace path
- Isolation level
- Action count
- Definition metadata

### `kill <journey_id>`
Terminate worker and cleanup resources:
- Stops container/process
- Removes worker from registry
- Cleans up workspace

### `help`
Show command reference

### `exit`
Disconnect and exit CLI

## Testing Workflow

### 1. Happy Path
```
mcp> spawn test_journey
mcp> execute test_journey   # Choose option 1 (read)
mcp> state test_journey
mcp> kill test_journey
```

### 2. Constraint Violation
```
mcp> spawn violation_test
mcp> execute violation_test  # Choose option 2 (large file)
# See constraint violation message
mcp> kill violation_test
```

### 3. Idempotent Spawning
```
mcp> spawn same_journey
# First spawn succeeds
mcp> spawn same_journey
# Second spawn returns existing worker
mcp> kill same_journey
```

## Architecture

```
Your Terminal
    ↓
mcp_client_cli.py (Interactive CLI)
    ↓
MCP Client (stdio_client)
    ↓ (stdio transport)
workers/mcp_server.py (MCP Server)
    ↓
WorkerFactory.spawn()
    ↓
ClaudeCodeWorker instance
    ↓
void() → constraint verification
    ↓
execute() → action execution
```

## Notes

- Server runs as subprocess (automatically started by CLI)
- Uses real MCP protocol over stdio
- Automatic constraint enforcement at MCP layer
- Journey-scoped worker isolation
- Persistent workers (spawn once, use many times)

## Troubleshooting

**Connection failed:**
```bash
# Make sure PYTHONPATH is set
PYTHONPATH=. python3 workers/mcp_client_cli.py
```

**Worker not found:**
```bash
# Spawn worker first before executing
mcp> spawn my_journey
mcp> execute my_journey
```

**Constraint violation:**
```bash
# This is expected! Try option 1 for valid action
mcp> execute my_journey
# Choose option 1 (Read README.md)
```
