#!/usr/bin/env python3
"""
Interactive REPL for Claude Code Provider.

Repeated stateless calls - each query is independent.
No memory between calls.

Usage:
    python playground/repl.py
    python playground/repl.py --model haiku
"""

import os
import sys
import json
import asyncio
import readline  # Enables arrow keys and history
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lgp.agents.claude_code_provider import ClaudeCodeProvider


class ClaudeREPL:
    """Interactive REPL for stateless Claude Code calls."""

    def __init__(self, model: str = "sonnet", cwd: str = ".", container: str = None):
        self.model = model
        self.cwd = cwd
        self.container = container
        self.provider = ClaudeCodeProvider({
            "role_name": "repl",
            "model": model,
            "max_turns": 10,
            "allowed_tools": ["Read", "Grep", "Glob", "Bash"],
            "cwd": cwd,
            "container": container
        })
        self.history = []

    def execute(self, prompt: str) -> dict:
        """Execute single stateless call."""
        result = asyncio.run(self.provider.execute_task(prompt, {}, {}))
        return {
            "output": result.get("repl_output", ""),
            "cost": result.get("repl_tokens", {}).get("cost", 0),
            "duration_ms": result.get("repl_tokens", {}).get("duration_ms", 0),
            "turns": result.get("repl_tokens", {}).get("turns", 0)
        }

    def run(self):
        """Run interactive loop."""
        print("=" * 60)
        mode = f"container: {self.container}" if self.container else "local CLI"
        print(f"Claude Code REPL (model: {self.model}, {mode})")
        print("=" * 60)
        print("Each query is stateless - no memory between calls.")
        print("Commands: /quit, /model <name>, /json, /help")
        print("=" * 60)
        print()

        json_mode = False

        while True:
            try:
                prompt = input(">>> ").strip()

                if not prompt:
                    continue

                # Commands
                if prompt == "/quit" or prompt == "/exit":
                    print("Goodbye.")
                    break

                if prompt == "/help":
                    print("Commands:")
                    print("  /quit       - Exit REPL")
                    print("  /model X    - Switch model (haiku/sonnet/opus)")
                    print("  /json       - Toggle JSON output")
                    print("  /history    - Show query history")
                    print("  /clear      - Clear history")
                    continue

                if prompt.startswith("/model "):
                    new_model = prompt.split(" ", 1)[1].strip()
                    if new_model in ["haiku", "sonnet", "opus"]:
                        self.model = new_model
                        self.provider = ClaudeCodeProvider({
                            "role_name": "repl",
                            "model": new_model,
                            "max_turns": 10,
                            "allowed_tools": ["Read", "Grep", "Glob", "Bash"],
                            "cwd": self.cwd,
                            "container": self.container
                        })
                        print(f"Switched to {new_model}")
                    else:
                        print("Invalid model. Use: haiku, sonnet, opus")
                    continue

                if prompt == "/json":
                    json_mode = not json_mode
                    print(f"JSON mode: {'ON' if json_mode else 'OFF'}")
                    continue

                if prompt == "/history":
                    for i, h in enumerate(self.history[-10:], 1):
                        print(f"  {i}. {h[:50]}...")
                    continue

                if prompt == "/clear":
                    self.history = []
                    print("History cleared.")
                    continue

                # Execute query
                self.history.append(prompt)
                print("...")

                result = self.execute(prompt)

                if json_mode:
                    print(json.dumps(result, indent=2))
                else:
                    print()
                    print(result["output"])
                    print()
                    print(f"[cost: ${result['cost']:.4f}, turns: {result['turns']}, time: {result['duration_ms']}ms]")

                print()

            except KeyboardInterrupt:
                print("\n(Use /quit to exit)")
                continue

            except EOFError:
                print("\nGoodbye.")
                break

            except Exception as e:
                print(f"Error: {e}")
                continue


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code Interactive REPL")
    parser.add_argument("--model", "-m", default="sonnet",
                        choices=["haiku", "sonnet", "opus"],
                        help="Model to use (default: sonnet)")
    parser.add_argument("--cwd", "-c", default=".",
                        help="Working directory")
    parser.add_argument("--container", "-d", default=None,
                        help="Docker container name (e.g., claude-mcp)")

    args = parser.parse_args()

    repl = ClaudeREPL(model=args.model, cwd=args.cwd, container=args.container)
    repl.run()


if __name__ == "__main__":
    main()
