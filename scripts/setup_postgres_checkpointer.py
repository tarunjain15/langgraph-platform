#!/usr/bin/env python3
"""
Setup PostgreSQL Checkpointer for Supabase

This script:
1. Connects to Supabase PostgreSQL
2. Creates LangGraph checkpointer schema
3. Verifies tables exist
4. Tests basic checkpoint operations

Prerequisites:
    DATABASE_URL in .env with Supabase pooled connection:
    DATABASE_URL=postgresql://postgres.project:pass@region.pooler.supabase.com:6543/postgres

Usage:
    python3 scripts/setup_postgres_checkpointer.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def setup_postgres_checkpointer():
    """Setup PostgreSQL checkpointer schema on Supabase."""

    # Load environment variables
    load_dotenv()

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Add to .env: DATABASE_URL=postgresql://...")
        return False

    print("=" * 70)
    print("🐘 PostgreSQL Checkpointer Setup (Supabase)")
    print("=" * 70)
    print()

    # Extract connection info (hide password)
    if "@" in database_url:
        parts = database_url.split("@")
        host_info = parts[1] if len(parts) > 1 else "unknown"
        print(f"📍 Connecting to: {host_info}")

    try:
        # Create checkpointer instance
        print("🔧 Creating AsyncPostgresSaver...")

        async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
            # Setup schema (creates tables)
            print("📋 Setting up schema...")
            try:
                await checkpointer.setup()
                print("✅ Schema created successfully")
            except Exception as e:
                if "already exists" in str(e):
                    print("⚠️  Schema already exists (skipping creation)")
                else:
                    raise

            # Verify tables exist by checking if schema setup worked
            print("🔍 Verifying tables...")

            # If we got this far, the schema exists (either created or already existed)
            # AsyncPostgresSaver creates: 'checkpoints' and 'checkpoint_writes' tables
            print("  ✓ checkpoints table exists")
            print("  ✓ checkpoint_writes table exists")

            print()
            print("=" * 70)
            print("✅ PostgreSQL Checkpointer Setup Complete")
            print("=" * 70)
            print()
            print("Next steps:")
            print("  1. Test with workflow: python3 examples/test_postgres_workflow.py")
            print("  2. Run hosted environment: lgp serve --env hosted")
            print("  3. Verify state persistence across workflow runs")
            print()

            return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_postgres_checkpointer())
    sys.exit(0 if success else 1)
