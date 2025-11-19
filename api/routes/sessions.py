"""
Session Routes - HTTP endpoints for session/checkpoint queries
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from lgp.checkpointing import create_checkpointer


router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    """Response model for session query"""
    thread_id: str
    checkpoints: int
    latest_state: Optional[Any] = None
    created_at: Optional[str] = None


@router.get("/{thread_id}")
async def get_session(thread_id: str):
    """Get session state and checkpoint history

    Args:
        thread_id: Thread ID to query

    Returns:
        SessionResponse with checkpoint count and latest state
    """
    try:
        # Create checkpointer
        checkpointer_cm = create_checkpointer({"path": "./checkpoints.db"})

        async with checkpointer_cm as checkpointer:
            # Get latest checkpoint
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = await checkpointer.aget_tuple(config)

            if checkpoint_tuple:
                # Count total checkpoints for this thread
                checkpoint_count = 0
                async for _ in checkpointer.alist(config):
                    checkpoint_count += 1

                return SessionResponse(
                    thread_id=thread_id,
                    checkpoints=checkpoint_count,
                    latest_state=checkpoint_tuple.checkpoint.get("channel_values", {}),
                    created_at=checkpoint_tuple.checkpoint.get("ts")
                )
            else:
                # No checkpoints found for this thread
                return SessionResponse(
                    thread_id=thread_id,
                    checkpoints=0,
                    latest_state=None,
                    created_at=None
                )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__
            }
        )


@router.get("/{thread_id}/checkpoints")
async def list_checkpoints(thread_id: str, limit: int = 10):
    """List checkpoints for a session

    Args:
        thread_id: Thread ID to query
        limit: Maximum number of checkpoints to return

    Returns:
        List of checkpoints
    """
    try:
        # Create checkpointer
        checkpointer_cm = create_checkpointer({"path": "./checkpoints.db"})

        async with checkpointer_cm as checkpointer:
            config = {"configurable": {"thread_id": thread_id}}

            # List checkpoints
            checkpoints = []
            count = 0
            async for checkpoint_tuple in checkpointer.alist(config):
                if count >= limit:
                    break

                checkpoints.append({
                    "checkpoint_id": checkpoint_tuple.checkpoint.get("id"),
                    "state": checkpoint_tuple.checkpoint.get("channel_values", {}),
                    "timestamp": checkpoint_tuple.checkpoint.get("ts"),
                    "parent_id": checkpoint_tuple.parent_config.get("configurable", {}).get("checkpoint_id") if checkpoint_tuple.parent_config else None
                })
                count += 1

            return {
                "thread_id": thread_id,
                "checkpoints": checkpoints,
                "count": len(checkpoints)
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__
            }
        )
