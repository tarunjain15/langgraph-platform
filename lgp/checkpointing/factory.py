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
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Configure logging
logger = logging.getLogger(__name__)


class ResilientPostgresCheckpointer:
    """
    Async context manager wrapper that adds retry logic and SQLite fallback
    to PostgreSQL checkpointer connections.
    """

    def __init__(self, url: str, max_retries: int = 3, retry_delays: list = None):
        self.url = url
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [1, 2, 4]
        self._checkpointer = None
        self._postgres_cm = None

    async def __aenter__(self):
        """Attempt PostgreSQL connection with retries, fall back to SQLite on failure."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"[lgp] Attempting PostgreSQL connection (attempt {attempt + 1}/{self.max_retries})...")
                self._postgres_cm = AsyncPostgresSaver.from_conn_string(self.url)
                self._checkpointer = await self._postgres_cm.__aenter__()
                logger.info(f"[lgp] ✓ PostgreSQL connection established")
                return self._checkpointer

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[lgp] PostgreSQL connection failed (attempt {attempt + 1}/{self.max_retries}): {type(e).__name__}: {str(e)[:100]}"
                )

                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.info(f"[lgp] Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        # All retries exhausted - fall back to SQLite
        logger.error(
            f"[lgp] ⚠️  PostgreSQL connection failed after {self.max_retries} attempts. "
            f"Falling back to SQLite (degraded mode)."
        )
        logger.error(f"[lgp] Last error: {type(last_error).__name__}: {str(last_error)[:200]}")

        # Create fallback SQLite checkpointer
        fallback_path = "./checkpoints/fallback.sqlite"
        Path(fallback_path).parent.mkdir(parents=True, exist_ok=True)

        logger.warning(
            f"[lgp] Using SQLite fallback: {fallback_path} "
            f"(state will NOT be shared across servers)"
        )

        self._postgres_cm = AsyncSqliteSaver.from_conn_string(fallback_path)
        self._checkpointer = await self._postgres_cm.__aenter__()
        return self._checkpointer

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the checkpointer context manager."""
        if self._postgres_cm:
            return await self._postgres_cm.__aexit__(exc_type, exc_val, exc_tb)
        return None


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

        # Return resilient checkpointer with retry logic and SQLite fallback
        # This context manager will attempt PostgreSQL connection with exponential backoff,
        # and gracefully degrade to SQLite if all retries fail
        return ResilientPostgresCheckpointer(url, max_retries=3, retry_delays=[1, 2, 4])

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
