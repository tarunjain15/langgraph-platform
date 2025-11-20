#!/usr/bin/env python3
"""
Cleanup Supabase Test Data

This script deletes test artifacts from Supabase PostgreSQL checkpoints table.

Test data found:
- thread_id: postgres-test-001 (3 checkpoints)

Usage:
    python3 scripts/cleanup_supabase_test_data.py

WARNING: This will permanently delete test data from Supabase.
"""

import os
import asyncio
from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def cleanup_test_data():
    """Delete test thread_ids from Supabase checkpoints table."""

    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return False

    print("=" * 70)
    print("🧹 Supabase Test Data Cleanup")
    print("=" * 70)
    print()

    # List of test thread_ids to delete
    test_thread_ids = [
        "postgres-test-001",
    ]

    print(f"Will delete {len(test_thread_ids)} test thread_id(s):")
    for thread_id in test_thread_ids:
        print(f"  - {thread_id}")
    print()

    # Confirm deletion
    confirm = input("⚠️  Delete these test threads from Supabase? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Cleanup cancelled")
        return False

    print()
    print("🔧 Connecting to Supabase...")

    async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
        conn = checkpointer.conn

        for thread_id in test_thread_ids:
            print(f"🗑️  Deleting thread_id: {thread_id}")

            # Delete from checkpoints table
            delete_checkpoints = """
            DELETE FROM checkpoints
            WHERE thread_id = $1;
            """

            # Delete from checkpoint_writes table
            delete_writes = """
            DELETE FROM checkpoint_writes
            WHERE thread_id = $1;
            """

            async with conn.cursor() as cur:
                # Delete checkpoint_writes first (foreign key constraint)
                await cur.execute(delete_writes, (thread_id,))
                writes_deleted = cur.rowcount

                # Delete checkpoints
                await cur.execute(delete_checkpoints, (thread_id,))
                checkpoints_deleted = cur.rowcount

                print(f"   ✓ Deleted {checkpoints_deleted} checkpoints, {writes_deleted} writes")

        print()
        print("=" * 70)
        print("✅ Cleanup Complete")
        print("=" * 70)
        print()
        print("Supabase checkpoints table is now clean of test data.")
        print()

        return True


if __name__ == "__main__":
    success = asyncio.run(cleanup_test_data())
    exit(0 if success else 1)
