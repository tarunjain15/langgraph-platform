"""
Stateless ask command - single call, no memory.

Each invocation is completely independent.
No session continuity. No state. No workflow overhead.

Usage:
    lgp ask "What is in README.md?"
    lgp ask "List Python files" --model haiku
    echo "Explain this code" | lgp ask
    lgp ask --json "Analyze structure" | jq .output
"""

import os
import sys
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment BEFORE any Langfuse imports
load_dotenv()


def _init_langfuse():
    """Initialize Langfuse with explicit configuration."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        return None

    from langfuse import Langfuse
    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )


def ask(
    prompt: str,
    model: str = "sonnet",
    tools: Optional[list] = None,
    json_output: bool = False,
    cwd: str = "."
) -> dict:
    """
    Single stateless call to Claude Code.

    Args:
        prompt: The question/task
        model: haiku, sonnet, or opus
        tools: Allowed tools (default: Read, Grep, Glob)
        json_output: Return full response dict
        cwd: Working directory

    Returns:
        Response dict with output, cost, duration
    """
    # Initialize Langfuse (returns None if not configured)
    langfuse_client = _init_langfuse()

    from lgp.agents.claude_code_provider import ClaudeCodeProvider

    provider = ClaudeCodeProvider({
        "role_name": "ask",
        "model": model,
        "max_turns": 10,
        "allowed_tools": tools or ["Read", "Grep", "Glob", "Bash"],
        "cwd": cwd
    })

    # Execute - empty state = no session continuity = stateless
    result = asyncio.run(provider.execute_task(prompt, {}, {}))

    # Flush traces if Langfuse is configured
    if langfuse_client:
        langfuse_client.flush()

    return {
        "output": result.get("ask_output", ""),
        "cost": result.get("ask_tokens", {}).get("cost", 0),
        "duration_ms": result.get("ask_tokens", {}).get("duration_ms", 0),
        "turns": result.get("ask_tokens", {}).get("turns", 0)
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Stateless call to Claude Code agency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    lgp ask "What is in README.md?"
    lgp ask "List all Python files" --model haiku
    lgp ask --json "Analyze structure" | jq .output
    echo "Explain this" | lgp ask
        """
    )

    parser.add_argument("prompt", nargs="?", help="Question or task")
    parser.add_argument("--model", "-m", default="sonnet",
                        choices=["haiku", "sonnet", "opus"],
                        help="Model to use (default: sonnet)")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output full JSON response")
    parser.add_argument("--cwd", "-c", default=".",
                        help="Working directory")

    args = parser.parse_args()

    # Get prompt from arg or stdin
    prompt = args.prompt
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if not prompt:
        parser.print_help()
        sys.exit(1)

    try:
        result = ask(
            prompt=prompt,
            model=args.model,
            json_output=args.json,
            cwd=args.cwd
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result["output"])

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
