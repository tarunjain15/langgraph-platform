#!/usr/bin/env python3
"""
Run a General Manager from config.

Usage:
    python run_manager.py managers/research_manager.yaml

Enforces TERMINAL_CONVERSATION_REQUIRED constraint.
"""

import asyncio
import argparse
import sys


async def main():
    parser = argparse.ArgumentParser(
        description="Run a General Manager from config file."
    )
    parser.add_argument(
        "config",
        help="Path to manager YAML config file"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check and exit"
    )

    args = parser.parse_args()

    # Import here to avoid startup delay
    from general_manager.factory import ManagerFactory
    from general_manager.terminal import run_terminal_session

    try:
        print(f"Loading manager from: {args.config}")
        manager = await ManagerFactory.from_config(args.config)

        if args.health_check:
            health = await manager.health_check()
            print(f"Health check: {health}")
            sys.exit(0 if all(health.values()) else 1)

        # Run terminal session
        await run_terminal_session(manager)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
