"""
Terminal Session Module.

Provides interactive terminal conversation capability.
Enforces TERMINAL_CONVERSATION_REQUIRED constraint.
"""

from .session import TerminalSession, run_terminal_session

__all__ = ["TerminalSession", "run_terminal_session"]
