"""
Multi-Backend Checkpointer Factory for LangGraph Platform

Creates and manages checkpointer instances with proper setup and verification.
Supports:
- SQLite (local development, experiment environment)
- PostgreSQL (hosted environment, multi-server deployment via Supabase)

Based on langgraph-checkpoint-mastery M1.1 implementation.
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, Union
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def create_checkpointer(config: Dict[str, Any]) -> Union[AsyncSqliteSaver, AsyncPostgresSaver]:
    """
    Create async checkpointer for async workflow execution.

    Supports multiple backends:
    - SQLite: For local development (experiment environment)
    - PostgreSQL: For hosted deployment (production environment)

    Args:
        config: Configuration dictionary with:
            - type: "sqlite" or "postgresql" (default: "sqlite")
            - path: SQLite database path (for type="sqlite")
            - url: PostgreSQL connection URL (for type="postgresql")
            - async: Use async checkpointer (default: True)

    Returns:
        AsyncSqliteSaver or AsyncPostgresSaver instance

    Examples:
        >>> # SQLite (experiment environment)
        >>> checkpointer = create_checkpointer({"type": "sqlite", "path": "./checkpoints.sqlite"})

        >>> # PostgreSQL (hosted environment with Supabase)
        >>> checkpointer = create_checkpointer({
        ...     "type": "postgresql",
        ...     "url": "postgresql://user:pass@host:6543/db"
        ... })
    """
    checkpointer_type = config.get("type", "sqlite")

    if checkpointer_type == "sqlite":
        path = config.get("path", "./checkpoints.sqlite")

        # Ensure parent directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Create AsyncSqliteSaver with database path
        return AsyncSqliteSaver.from_conn_string(path)

    elif checkpointer_type == "postgresql":
        url = config.get("url")

        if not url:
            # Try to get from environment variable
            url = os.environ.get("DATABASE_URL")

        if not url:
            raise ValueError(
                "PostgreSQL URL not provided. Set 'url' in config or DATABASE_URL environment variable."
            )

        # Create AsyncPostgresSaver with connection URL
        # Note: AsyncPostgresSaver is a context manager, so we need to return it
        # and let the caller handle async context management
        return AsyncPostgresSaver.from_conn_string(url)

    else:
        raise ValueError(f"Unknown checkpointer type: {checkpointer_type}. Use 'sqlite' or 'postgresql'.")


def setup_checkpointer(path: str = "./checkpoints.sqlite", verbose: bool = False) -> bool:
    """
    Setup SQLite checkpointer with schema creation and verification.

    Creates checkpoints.sqlite file with:
    - checkpoints table
    - writes table
    - WAL mode enabled

    Args:
        path: Path to SQLite database file
        verbose: Print detailed setup information

    Returns:
        True if setup successful, False otherwise

    Witness Outcomes:
    - checkpoints.sqlite file exists
    - checkpoints and writes tables created
    - WAL mode enabled
    """
    if verbose:
        print(f"[lgp] Setting up checkpointer: {path}")

    try:
        # Create checkpointer and setup schema
        with SqliteSaver.from_conn_string(path) as checkpointer:
            checkpointer.setup()

        if verbose:
            print(f"[lgp] ✓ Schema created")

        # Verify file exists
        if not os.path.exists(path):
            if verbose:
                print(f"[lgp] ✗ File not found: {path}")
            return False

        if verbose:
            file_size = os.path.getsize(path)
            print(f"[lgp] ✓ File exists ({file_size} bytes)")

        # Verify schema and WAL mode
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Check tables
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        if 'checkpoints' not in table_names:
            if verbose:
                print(f"[lgp] ✗ checkpoints table missing")
            conn.close()
            return False

        if 'writes' not in table_names:
            if verbose:
                print(f"[lgp] ✗ writes table missing")
            conn.close()
            return False

        if verbose:
            print(f"[lgp] ✓ Tables: {table_names}")

        # Check WAL mode
        wal_mode = cursor.execute("PRAGMA journal_mode").fetchone()[0]

        if wal_mode != 'wal':
            if verbose:
                print(f"[lgp] ⚠ WAL mode not enabled (journal_mode: {wal_mode})")
            # Don't fail - WAL mode is optional optimization
        elif verbose:
            print(f"[lgp] ✓ WAL mode enabled")

        conn.close()

        if verbose:
            print(f"[lgp] ✅ Checkpointer setup complete")

        return True

    except Exception as e:
        if verbose:
            print(f"[lgp] ✗ Setup failed: {e}")
        return False


def verify_checkpointer(path: str = "./checkpoints.sqlite") -> bool:
    """
    Verify checkpointer exists and is properly configured.

    Args:
        path: Path to SQLite database file

    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(path):
        return False

    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Check tables exist
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        conn.close()

        return 'checkpoints' in table_names and 'writes' in table_names

    except Exception:
        return False
