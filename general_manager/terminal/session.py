"""
Terminal Session for General Manager.

Provides interactive conversation loop via terminal.
Enforces TERMINAL_CONVERSATION_REQUIRED constraint.
"""

import asyncio
import sys
from typing import TYPE_CHECKING, Optional, Dict, Any
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..manager import ConversationalManager


@dataclass
class TerminalStyle:
    """Terminal prompt styling configuration."""
    user_prompt: str = "You: "
    assistant_prefix: str = "Assistant: "
    thinking_prefix: str = "Thinking..."
    error_prefix: str = "Error: "
    tool_calling_prefix: str = "🔧 Calling: "
    tool_success_prefix: str = "✅ "
    tool_error_prefix: str = "❌ "


class TerminalSession:
    """
    Interactive terminal session for manager conversation.

    Provides readline-based input with styled output.
    """

    def __init__(
        self,
        manager: "ConversationalManager",
        style: Optional[TerminalStyle] = None
    ):
        self.manager = manager
        self.style = style or TerminalStyle()
        self._running = False

        # Register tool event callback
        self.manager.set_tool_event_callback(self._handle_tool_event)

    def _handle_tool_event(self, event_type: str, tool_name: str, details: Dict[str, Any]) -> None:
        """Handle tool execution events and display to terminal."""
        if event_type == "calling":
            args_preview = str(details.get("arguments", {}))
            if len(args_preview) > 80:
                args_preview = args_preview[:77] + "..."
            print(f"{self.style.tool_calling_prefix}{tool_name}({args_preview})")
        elif event_type == "success":
            print(f"{self.style.tool_success_prefix}{tool_name} completed")
        elif event_type == "error":
            error = details.get("error", "Unknown error")
            print(f"{self.style.tool_error_prefix}{tool_name} failed: {error}")

    async def start(self) -> None:
        """Start interactive terminal session."""
        self._running = True

        # Print welcome message
        print(f"\n{'='*60}")
        print(f"General Manager: {self.manager.config.name}")
        print(f"Model: {self.manager.config.agency.model}")
        print(f"Tools: {', '.join(t.value for t in self.manager.config.tools)}")
        print(f"{'='*60}")
        print("Type 'exit' or 'quit' to end the session.")
        print("Type 'clear' to reset conversation history.")
        print(f"{'='*60}\n")

        while self._running:
            try:
                # Get user input
                user_input = await self._get_input()

                if user_input is None:
                    # EOF received
                    break

                user_input = user_input.strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ("exit", "quit"):
                    print("\nGoodbye!")
                    break

                if user_input.lower() == "clear":
                    self.manager.clear_history()
                    print("\nConversation history cleared.\n")
                    continue

                if user_input.lower() == "tools":
                    tools = self.manager.list_tools()
                    print(f"\nAvailable tools: {', '.join(tools)}\n")
                    continue

                # Process message through manager
                print(f"\n{self.style.thinking_prefix}")

                try:
                    response = await self.manager.chat(user_input)
                    print(f"\r{self.style.assistant_prefix}{response}\n")
                except Exception as e:
                    print(f"\r{self.style.error_prefix}{e}\n")

            except KeyboardInterrupt:
                print("\n\nSession interrupted. Type 'exit' to quit.")
                continue

    async def _get_input(self) -> Optional[str]:
        """Get input from user asynchronously."""
        loop = asyncio.get_event_loop()

        try:
            # Run blocking input in executor
            return await loop.run_in_executor(
                None,
                lambda: input(self.style.user_prompt)
            )
        except EOFError:
            return None

    def stop(self) -> None:
        """Stop the terminal session."""
        self._running = False


async def run_terminal_session(manager: "ConversationalManager") -> None:
    """
    Run a terminal session with a manager.

    Convenience function for quick session startup.

    Args:
        manager: Initialized ConversationalManager
    """
    session = TerminalSession(manager)
    await session.start()
