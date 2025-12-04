```yaml
name: General Manager - Implementation Plan
description: Execution map for GM1 (Config-Driven Manager MVP). Four phases building factory pattern with MCP tools.
created: 2025-11-26
version: 1.0.0
phase: GM1
status: Ready to Start
```

# General Manager: Implementation Plan

## Execution Status

**Phase:** GM1 (Config-Driven Manager MVP)
**Status:** Ready to Start
**Estimated Duration:** 4-6 hours
**Dependencies:** Ollama running locally, Node.js for MCP servers

---

## Phase Overview

```
GM1.1: Config Schema & Loader
    ↓
GM1.2: LLM Provider (Ollama)
    ↓
GM1.3: MCP Tool Registry (Playwright + Filesystem)
    ↓
GM1.4: LangGraph Manager + Terminal Session
```

---

## GM1.1: Config Schema & Loader

**Task ID:** GM1.1
**Type:** Foundation
**Status:** Pending
**Estimated Duration:** 45 minutes

### Objective
Create config schema and loader that transforms YAML → Python dataclasses.

### Deliverables

**File: `gm/config.py`**
```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List
import yaml


class AgencyProvider(Enum):
    OLLAMA = "ollama"
    CLAUDE = "claude"


class ToolType(Enum):
    PLAYWRIGHT = "playwright"
    FILESYSTEM = "filesystem"


@dataclass
class AgencyConfig:
    provider: AgencyProvider
    model: str
    temperature: float = 0.7


@dataclass
class TerminalConfig:
    enabled: bool = True
    prompt_style: str = "minimal"


@dataclass
class RuntimeConfig:
    max_iterations: int = 10
    timeout_seconds: int = 300


@dataclass
class ManagerConfig:
    name: str
    version: str
    system_prompt: str
    agency: AgencyConfig
    tools: List[ToolType]
    runtime: RuntimeConfig
    terminal: TerminalConfig


def load_manager_config(config_path: str) -> ManagerConfig:
    """Load manager config from YAML file."""
    path = Path(config_path)

    with open(path) as f:
        raw = yaml.safe_load(f)

    # Load system prompt from referenced file
    prompt_path = path.parent / raw["identity"]["system_prompt"]
    with open(prompt_path) as f:
        system_prompt = f.read()

    return ManagerConfig(
        name=raw["name"],
        version=raw["version"],
        system_prompt=system_prompt,
        agency=AgencyConfig(
            provider=AgencyProvider(raw["agency"]["provider"]),
            model=raw["agency"]["model"],
            temperature=raw["agency"].get("temperature", 0.7)
        ),
        tools=[ToolType(t) for t in raw["tools"]],
        runtime=RuntimeConfig(
            max_iterations=raw.get("runtime", {}).get("max_iterations", 10),
            timeout_seconds=raw.get("runtime", {}).get("timeout_seconds", 300)
        ),
        terminal=TerminalConfig(
            enabled=raw.get("terminal", {}).get("enabled", True),
            prompt_style=raw.get("terminal", {}).get("prompt_style", "minimal")
        )
    )
```

**File: `managers/research_manager.yaml`**
```yaml
name: research_manager
version: "1.0"

identity:
  system_prompt: "../prompts/research_manager.md"

agency:
  provider: ollama
  model: llama3.2
  temperature: 0.7

tools:
  - playwright
  - filesystem

runtime:
  max_iterations: 10
  timeout_seconds: 300

terminal:
  enabled: true
  prompt_style: minimal
```

**File: `prompts/research_manager.md`**
```markdown
You are a research manager with access to browser and filesystem tools.

## Your Capabilities
- Browse websites using Playwright (navigate, screenshot, click, type)
- Manage files using Filesystem (read, write, list, search)

## Your Behavior
1. Think step-by-step before acting
2. Explain your reasoning to the user
3. Use tools when needed to accomplish goals
4. Report results clearly and concisely

## Your Constraints
- Do not modify system files outside /tmp
- Ask for confirmation before destructive actions
- Respect rate limits and timeouts
```

### Acceptance Criteria
- [ ] `load_manager_config()` loads YAML successfully
- [ ] System prompt loaded from referenced .md file
- [ ] Enums validate provider and tool types
- [ ] Invalid config raises clear error

### Validation
```python
config = load_manager_config("managers/research_manager.yaml")
assert config.name == "research_manager"
assert config.agency.provider == AgencyProvider.OLLAMA
assert ToolType.PLAYWRIGHT in config.tools
assert "research manager" in config.system_prompt.lower()
```

---

## GM1.2: LLM Provider (Ollama)

**Task ID:** GM1.2
**Type:** Integration
**Status:** Pending
**Estimated Duration:** 1 hour
**Dependencies:** GM1.1

### Objective
Create LLM provider abstraction with Ollama implementation.

### Deliverables

**File: `gm/llm_providers.py`**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from .config import AgencyConfig, AgencyProvider


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate response, optionally with tool calls."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider with tool support."""

    def __init__(self, model: str, temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.base_url = "http://localhost:11434"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate response using Ollama chat API."""

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False


class ClaudeProvider(LLMProvider):
    """Claude API provider (placeholder)."""

    def __init__(self, model: str, temperature: float = 0.7):
        self.model = model
        self.temperature = temperature

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("Claude provider not yet implemented")


def create_llm_provider(config: AgencyConfig) -> LLMProvider:
    """Factory function for LLM providers."""
    if config.provider == AgencyProvider.OLLAMA:
        return OllamaProvider(config.model, config.temperature)
    elif config.provider == AgencyProvider.CLAUDE:
        return ClaudeProvider(config.model, config.temperature)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
```

### Acceptance Criteria
- [ ] OllamaProvider connects to localhost:11434
- [ ] generate() returns response with message content
- [ ] Tools schema passed to Ollama when provided
- [ ] health_check() verifies Ollama is running
- [ ] Provider abstraction allows future Claude implementation

### Validation
```python
provider = OllamaProvider("llama3.2")
assert await provider.health_check() == True

response = await provider.generate([
    {"role": "user", "content": "Say hello"}
])
assert "message" in response
assert "content" in response["message"]
```

### Prerequisites
```bash
# Ensure Ollama is running
ollama serve

# Pull model (if not already)
ollama pull llama3.2
```

---

## GM1.3: MCP Tool Registry

**Task ID:** GM1.3
**Type:** Integration
**Status:** Pending
**Estimated Duration:** 1.5 hours
**Dependencies:** GM1.1

### Objective
Create MCP tool registry connecting to Playwright and Filesystem servers.

### Deliverables

**File: `gm/tool_registry.py`**
```python
from typing import Dict, List, Any
from dataclasses import dataclass
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .config import ToolType
import asyncio


@dataclass
class MCPServerConfig:
    command: str
    args: List[str]


TOOL_SERVERS: Dict[ToolType, MCPServerConfig] = {
    ToolType.PLAYWRIGHT: MCPServerConfig(
        command="npx",
        args=["-y", "@anthropic-ai/mcp-server-playwright"]
    ),
    ToolType.FILESYSTEM: MCPServerConfig(
        command="npx",
        args=[
            "-y",
            "@anthropic-ai/mcp-server-filesystem",
            "/tmp/manager-workspace"
        ]
    )
}


class ToolRegistry:
    """
    MCP Tool Registry.

    Connects to MCP servers, discovers tools, routes calls.
    """

    def __init__(self, tool_types: List[ToolType]):
        self.tool_types = tool_types
        self._sessions: Dict[ToolType, ClientSession] = {}
        self._transports: Dict[ToolType, Any] = {}
        self._tools: Dict[str, ToolType] = {}
        self._tool_schemas: List[Dict[str, Any]] = []
        self._connected = False

    async def connect(self):
        """Connect to all configured MCP servers."""
        for tool_type in self.tool_types:
            config = TOOL_SERVERS[tool_type]

            server_params = StdioServerParameters(
                command=config.command,
                args=config.args
            )

            # Start transport
            transport = stdio_client(server_params)
            read, write = await transport.__aenter__()
            self._transports[tool_type] = transport

            # Create and initialize session
            session = ClientSession(read, write)
            await session.__aenter__()
            await session.initialize()
            self._sessions[tool_type] = session

            # Discover tools
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                self._tools[tool.name] = tool_type
                self._tool_schemas.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema or {}
                    }
                })

        self._connected = True

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name."""
        if not self._connected:
            raise RuntimeError("ToolRegistry not connected")

        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        tool_type = self._tools[name]
        session = self._sessions[tool_type]

        result = await session.call_tool(name, arguments)
        return result

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas for LLM."""
        return self._tool_schemas

    def list_tools(self) -> List[str]:
        """List available tool names."""
        return list(self._tools.keys())

    async def disconnect(self):
        """Close all MCP connections."""
        for tool_type, session in self._sessions.items():
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass

        for tool_type, transport in self._transports.items():
            try:
                await transport.__aexit__(None, None, None)
            except Exception:
                pass

        self._sessions.clear()
        self._transports.clear()
        self._connected = False
```

### Acceptance Criteria
- [ ] Connects to Playwright MCP server
- [ ] Connects to Filesystem MCP server
- [ ] Discovers tools from both servers
- [ ] Routes tool calls to correct server
- [ ] Clean disconnect on shutdown

### Validation
```python
registry = ToolRegistry([ToolType.PLAYWRIGHT, ToolType.FILESYSTEM])
await registry.connect()

# Check tools discovered
tools = registry.list_tools()
assert "browser_navigate" in tools
assert "read_file" in tools

# Test tool call
result = await registry.call_tool("read_file", {"path": "/tmp/test.txt"})
assert result is not None

await registry.disconnect()
```

### Prerequisites
```bash
# Node.js required for npx
node --version  # v18+ recommended

# Test MCP servers work
npx -y @anthropic-ai/mcp-server-filesystem /tmp
npx -y @anthropic-ai/mcp-server-playwright
```

---

## GM1.4: LangGraph Manager + Terminal

**Task ID:** GM1.4
**Type:** Core
**Status:** Pending
**Estimated Duration:** 2 hours
**Dependencies:** GM1.1, GM1.2, GM1.3

### Objective
Create LangGraph-based ConversationalManager and TerminalSession.

### Deliverables

**File: `gm/manager.py`**
```python
from typing import TypedDict, List, Dict, Any, Annotated
import operator
import json
from langgraph.graph import StateGraph, END
from .config import ManagerConfig
from .llm_providers import LLMProvider
from .tool_registry import ToolRegistry


class ManagerState(TypedDict):
    messages: Annotated[List[Dict[str, Any]], operator.add]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    iteration: int
    done: bool


class ConversationalManager:
    """
    LangGraph-based conversational manager with MCP tools.

    Flow: reason → (execute_tools?) → respond
    """

    def __init__(
        self,
        config: ManagerConfig,
        llm: LLMProvider,
        tools: ToolRegistry
    ):
        self.config = config
        self.llm = llm
        self.tools = tools
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(ManagerState)

        graph.add_node("reason", self._reason)
        graph.add_node("execute_tools", self._execute_tools)
        graph.add_node("respond", self._respond)

        graph.add_conditional_edges(
            "reason",
            self._route_after_reason,
            {
                "tools": "execute_tools",
                "respond": "respond"
            }
        )
        graph.add_edge("execute_tools", "reason")
        graph.add_edge("respond", END)

        graph.set_entry_point("reason")

        return graph.compile()

    async def _reason(self, state: ManagerState) -> dict:
        """LLM reasons about conversation."""
        messages = [
            {"role": "system", "content": self.config.system_prompt}
        ] + state["messages"]

        # Add tool results if any
        for result in state.get("tool_results", []):
            messages.append({
                "role": "tool",
                "content": json.dumps(result)
            })

        response = await self.llm.generate(
            messages=messages,
            tools=self.tools.get_tool_schemas()
        )

        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            return {
                "tool_calls": tool_calls,
                "tool_results": [],
                "iteration": state["iteration"] + 1
            }
        else:
            content = message.get("content", "")
            return {
                "messages": [{"role": "assistant", "content": content}],
                "tool_calls": [],
                "done": True
            }

    async def _execute_tools(self, state: ManagerState) -> dict:
        """Execute MCP tool calls."""
        results = []

        for call in state["tool_calls"]:
            func = call.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", {})

            if isinstance(args, str):
                args = json.loads(args)

            try:
                result = await self.tools.call_tool(name, args)
                results.append({
                    "tool": name,
                    "success": True,
                    "result": str(result)
                })
            except Exception as e:
                results.append({
                    "tool": name,
                    "success": False,
                    "error": str(e)
                })

        return {"tool_results": results, "tool_calls": []}

    async def _respond(self, state: ManagerState) -> dict:
        """Final response (pass-through)."""
        return {}

    def _route_after_reason(self, state: ManagerState) -> str:
        """Route based on tool calls."""
        if state.get("tool_calls"):
            if state["iteration"] >= self.config.runtime.max_iterations:
                return "respond"
            return "tools"
        return "respond"

    async def chat(self, user_message: str) -> str:
        """Process user message and return response."""
        initial_state: ManagerState = {
            "messages": [{"role": "user", "content": user_message}],
            "tool_calls": [],
            "tool_results": [],
            "iteration": 0,
            "done": False
        }

        result = await self.graph.ainvoke(initial_state)

        for msg in reversed(result["messages"]):
            if msg.get("role") == "assistant":
                return msg.get("content", "")

        return "I couldn't generate a response."

    def reset(self):
        """Reset conversation state."""
        pass  # Stateless for MVP, add checkpointer later
```

**File: `gm/terminal/session.py`**
```python
from typing import Optional
from ..manager import ConversationalManager


class TerminalSession:
    """
    Interactive terminal session for manager conversation.

    Critical Constraint: All managers MUST support this interface.
    """

    def __init__(self, manager: ConversationalManager):
        self.manager = manager
        self._running = False

    async def start(self):
        """Start interactive terminal loop."""
        self._running = True

        self._print_header()

        while self._running:
            user_input = await self._get_input()

            if user_input is None:
                break

            print("\nManager: Thinking...", end="", flush=True)
            response = await self.manager.chat(user_input)
            print(f"\rManager: {response}\n")

    def _print_header(self):
        """Print session header."""
        name = self.manager.config.name
        print(f"\n{'='*50}")
        print(f"  {name}")
        print(f"  Commands: 'quit' to exit | 'clear' to reset")
        print(f"  Tools: {', '.join(self.manager.tools.list_tools()[:5])}...")
        print(f"{'='*50}\n")

    async def _get_input(self) -> Optional[str]:
        """Get user input with command handling."""
        try:
            user_input = input("You: ").strip()

            if not user_input:
                return await self._get_input()

            if user_input.lower() in ["quit", "exit", "q"]:
                self._running = False
                return None

            if user_input.lower() == "clear":
                self.manager.reset()
                print("[Session cleared]\n")
                return await self._get_input()

            if user_input.lower() == "tools":
                self._show_tools()
                return await self._get_input()

            return user_input

        except (KeyboardInterrupt, EOFError):
            self._running = False
            return None

    def _show_tools(self):
        """Show available tools."""
        print("\nAvailable Tools:")
        for tool in self.manager.tools.list_tools():
            print(f"  - {tool}")
        print()
```

**File: `gm/factory.py`**
```python
from .config import load_manager_config
from .llm_providers import create_llm_provider
from .tool_registry import ToolRegistry
from .manager import ConversationalManager


class ManagerFactory:
    """
    Factory for creating managers from config.

    Usage:
        manager = await ManagerFactory.from_config("managers/research.yaml")
        response = await manager.chat("Hello!")
    """

    @staticmethod
    async def from_config(config_path: str) -> ConversationalManager:
        """Create manager from YAML config."""

        # 1. Load config
        config = load_manager_config(config_path)

        # 2. Verify terminal support (constraint check)
        if not config.terminal.enabled:
            raise ValueError("TERMINAL_CONVERSATION_REQUIRED: terminal.enabled must be true")

        # 3. Create LLM provider
        llm = create_llm_provider(config.agency)

        # 4. Create and connect tool registry
        tools = ToolRegistry(config.tools)
        await tools.connect()

        # 5. Create manager
        manager = ConversationalManager(config, llm, tools)

        return manager
```

**File: `run_manager.py`**
```python
#!/usr/bin/env python3
"""Run a manager with terminal conversation."""

import asyncio
import sys
from gm.factory import ManagerFactory
from gm.terminal.session import TerminalSession


async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_manager.py <config>")
        print("Example: python run_manager.py managers/research_manager.yaml")
        sys.exit(1)

    config_path = sys.argv[1]

    print(f"Loading manager from: {config_path}")

    try:
        manager = await ManagerFactory.from_config(config_path)
    except Exception as e:
        print(f"Error loading manager: {e}")
        sys.exit(1)

    session = TerminalSession(manager)

    try:
        await session.start()
    finally:
        print("\nDisconnecting tools...")
        await manager.tools.disconnect()
        print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
```

### Acceptance Criteria
- [ ] Manager graph compiles with reason → tools → respond flow
- [ ] chat() returns string response
- [ ] Tool calls executed via MCP
- [ ] Terminal session provides interactive loop
- [ ] Commands work: quit, clear, tools
- [ ] Factory creates manager from config

### Validation
```bash
# Full integration test
python run_manager.py managers/research_manager.yaml

# Test conversation
You: List files in /tmp
Manager: [Uses filesystem tool, returns results]

You: tools
[Shows available tools]

You: quit
Goodbye!
```

---

## Final Checklist

### Files to Create
```
general-manager/
├── gm/
│   ├── __init__.py
│   ├── config.py           # GM1.1
│   ├── llm_providers.py    # GM1.2
│   ├── tool_registry.py    # GM1.3
│   ├── manager.py          # GM1.4
│   ├── factory.py          # GM1.4
│   └── terminal/
│       ├── __init__.py
│       └── session.py      # GM1.4
├── managers/
│   └── research_manager.yaml
├── prompts/
│   └── research_manager.md
├── run_manager.py
└── requirements.txt
```

### Requirements
```txt
langgraph>=0.2.0
mcp>=1.0.0
pyyaml>=6.0
httpx>=0.25.0
```

### Prerequisites
```bash
# Ollama
ollama serve
ollama pull llama3.2

# Node.js for MCP servers
node --version  # v18+

# Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Config loads | ✓ No errors |
| Ollama connects | ✓ Health check passes |
| MCP tools connect | ✓ 2 servers, 10+ tools |
| Manager chat works | ✓ Response in <30s |
| Terminal interactive | ✓ Commands work |

---

## Next Steps (Post-MVP)

1. **Claude Provider** - API-based LLM option
2. **Session Persistence** - LangGraph checkpointer
3. **More Tools** - GitHub, database, etc.
4. **Constraint Enforcement** - void() pattern from R13
5. **Manager Marketplace** - Managers as workers
