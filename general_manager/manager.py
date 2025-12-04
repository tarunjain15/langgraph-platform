"""
Conversational Manager with LangGraph.

Core manager implementation using LangGraph state machine.
Enforces all 5 sacred constraints.
"""

import json
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Callable
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END

from .config import ManagerConfig
from .llm_providers import LLMProvider
from .tool_registry import ToolRegistry

# Type alias for event callbacks
ToolEventCallback = Callable[[str, str, Dict[str, Any]], None]


def message_reducer(left: List[Dict[str, Any]], right: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Simple message list reducer that appends new messages."""
    if not left:
        return right
    if not right:
        return left
    return left + right


class ManagerState(TypedDict):
    """State for manager conversation graph."""
    messages: Annotated[List[Dict[str, Any]], message_reducer]
    tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
    iteration: int
    max_iterations: int


class ConversationalManager:
    """
    Config-driven conversational manager with MCP tools.

    Uses LangGraph for conversation flow:
    - reason: LLM decides what to do
    - execute_tools: Execute any requested tools
    - respond: Generate final response

    Enforces all 5 sacred constraints:
    - TERMINAL_CONVERSATION_REQUIRED: Via terminal session
    - CONFIG_DRIVEN_INSTANTIATION: Via factory pattern
    - SOVEREIGN_TOOL_ACCESS: Via tool registry
    - LLM_PROVIDER_ABSTRACTION: Via provider interface
    - MCP_PROTOCOL_COMPLIANCE: Via MCP connections
    """

    def __init__(
        self,
        config: ManagerConfig,
        llm: LLMProvider,
        tool_registry: ToolRegistry
    ):
        self.config = config
        self.llm = llm
        self.tool_registry = tool_registry
        self._conversation_history: List[Dict[str, str]] = []
        self._graph = self._build_graph()
        self._tool_event_callback: Optional[ToolEventCallback] = None

    def set_tool_event_callback(self, callback: ToolEventCallback) -> None:
        """
        Set callback for tool execution events.

        Callback signature: (event_type, tool_name, details) -> None
        Event types: 'calling', 'success', 'error'
        """
        self._tool_event_callback = callback

    def _emit_tool_event(self, event_type: str, tool_name: str, details: Dict[str, Any]) -> None:
        """Emit tool event to registered callback."""
        if self._tool_event_callback:
            self._tool_event_callback(event_type, tool_name, details)

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine for conversation."""
        graph = StateGraph(ManagerState)

        # Add nodes
        graph.add_node("reason", self._reason_node)
        graph.add_node("execute_tools", self._execute_tools_node)
        graph.add_node("respond", self._respond_node)

        # Set entry point
        graph.set_entry_point("reason")

        # Add conditional edges
        graph.add_conditional_edges(
            "reason",
            self._should_execute_tools,
            {
                "execute": "execute_tools",
                "respond": "respond"
            }
        )

        graph.add_edge("execute_tools", "reason")
        graph.add_edge("respond", END)

        return graph.compile()

    async def _reason_node(self, state: ManagerState) -> Dict[str, Any]:
        """LLM reasoning node - decide what to do."""
        messages = list(state["messages"])

        # Build message list with system prompt
        full_messages = [
            {"role": "system", "content": self.config.system_prompt}
        ] + messages

        # Get tool schemas for LLM
        tools = self.tool_registry.get_tool_schemas() if self.tool_registry.list_available_tools() else None

        # Generate response
        response = await self.llm.generate(full_messages, tools)

        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        # Update state
        updates = {
            "iteration": state["iteration"] + 1,
            "tool_results": None
        }

        if tool_calls:
            # Add assistant message WITH tool_calls to history (OpenAI requires this)
            # Ensure each tool_call has the required 'type' field
            formatted_tool_calls = [
                {
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": tc.get("function", {})
                }
                for tc in tool_calls
            ]
            assistant_msg = {
                "role": "assistant",
                "content": content or "",
                "tool_calls": formatted_tool_calls
            }
            updates["messages"] = [assistant_msg]
            updates["tool_calls"] = tool_calls
        else:
            updates["tool_calls"] = None
            if content:
                updates["messages"] = [{"role": "assistant", "content": content}]

        return updates

    def _should_execute_tools(self, state: ManagerState) -> str:
        """Decide whether to execute tools or respond."""
        # Check iteration limit
        if state["iteration"] >= state["max_iterations"]:
            return "respond"

        # Check for tool calls
        if state.get("tool_calls"):
            return "execute"

        return "respond"

    async def _execute_tools_node(self, state: ManagerState) -> Dict[str, Any]:
        """Execute requested tools and add results to messages."""
        tool_calls = state.get("tool_calls", [])
        tool_messages = []

        for call in tool_calls:
            tool_call_id = call.get("id", "")
            name = call.get("function", {}).get("name", "")
            arguments = call.get("function", {}).get("arguments", {})

            # Parse arguments if string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            # Emit 'calling' event
            self._emit_tool_event("calling", name, {"arguments": arguments})

            try:
                result = await self.tool_registry.execute_tool(name, arguments)

                # Emit 'success' event
                self._emit_tool_event("success", name, {"result_preview": str(result)[:200]})

                # Add tool result message to history (OpenAI format)
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(result) if isinstance(result, dict) else str(result)
                })
            except Exception as e:
                # Emit 'error' event
                self._emit_tool_event("error", name, {"error": str(e)})

                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"error": str(e)})
                })

        return {
            "messages": tool_messages,
            "tool_calls": None,
            "tool_results": None
        }

    async def _respond_node(self, state: ManagerState) -> Dict[str, Any]:
        """Generate final response - this node is reached when no more tool calls."""
        # The conversation should already have assistant response from reason node
        # This node just ensures we have a clean exit
        return {}

    async def chat(self, user_message: str) -> str:
        """
        Send a message and get a response.

        Args:
            user_message: User's input message

        Returns:
            Assistant's response
        """
        # Add user message to history
        self._conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build initial state
        initial_state: ManagerState = {
            "messages": self._conversation_history.copy(),
            "tool_calls": None,
            "tool_results": None,
            "iteration": 0,
            "max_iterations": self.config.runtime.max_iterations
        }

        # Run graph
        final_state = await self._graph.ainvoke(initial_state)

        # Extract response
        messages = final_state.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                response = msg["content"]
                self._conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response

        return "I'm not sure how to respond to that."

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history.clear()

    def list_tools(self) -> List[str]:
        """List available tool names."""
        return self.tool_registry.list_available_tools()

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        return {
            "llm": await self.llm.health_check(),
            "tools": len(self.tool_registry.connections) > 0
        }
