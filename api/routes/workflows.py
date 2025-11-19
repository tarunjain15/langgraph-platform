"""
Workflow Routes - HTTP endpoints for workflow invocation
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time


router = APIRouter(prefix="/workflows", tags=["workflows"])


class InvokeRequest(BaseModel):
    """Request model for workflow invocation"""
    input: Any
    thread_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class InvokeResponse(BaseModel):
    """Response model for workflow invocation"""
    status: str
    thread_id: Optional[str] = None
    result: Any
    duration_ms: float


@router.post("/{workflow_name}/invoke")
async def invoke_workflow(
    workflow_name: str,
    request_body: InvokeRequest,
    request: Request
):
    """Invoke workflow with input data

    Args:
        workflow_name: Name of the workflow to invoke
        request_body: Input data and configuration

    Returns:
        InvokeResponse with result and metadata
    """
    start_time = time.time()

    try:
        # Get workflow path from app state
        workflow_path = request.app.state.workflow_path

        # Verify workflow name matches
        if workflow_name != request.app.state.workflow_name:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found. "
                       f"Available: {request.app.state.workflow_name}"
            )

        # Create executor
        from runtime.executor import WorkflowExecutor
        executor = WorkflowExecutor(environment="hosted")

        # Prepare input
        input_data = {"input": request_body.input}
        if request_body.thread_id:
            input_data["thread_id"] = request_body.thread_id

        # Execute workflow
        result = await executor.aexecute(workflow_path, input_data)

        duration_ms = (time.time() - start_time) * 1000

        return InvokeResponse(
            status="complete",
            thread_id=request_body.thread_id,
            result=result,
            duration_ms=duration_ms
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "duration_ms": duration_ms
            }
        )
