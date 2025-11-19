"""
API Server - Hosts workflows via HTTP in hosted mode

Uses FastAPI + Uvicorn for serving workflows.
"""

import uvicorn
from pathlib import Path


def serve_workflow(workflow_path: str, host: str = "0.0.0.0", port: int = 8000):
    """Start FastAPI server for workflow

    Args:
        workflow_path: Path to workflow file
        host: Host to bind to
        port: Port to run on
    """
    from api.app import app

    # Store workflow path in app state
    app.state.workflow_path = str(Path(workflow_path).resolve())
    app.state.workflow_name = Path(workflow_path).stem

    print(f"[lgp] Workflow loaded: {app.state.workflow_name}")
    print(f"[lgp] ✅ Server ready")
    print()
    print(f"API Endpoints:")
    print(f"  GET  {host}:{port}/health")
    print(f"  POST {host}:{port}/workflows/{{name}}/invoke")
    print(f"  GET  {host}:{port}/sessions/{{thread_id}}")
    print()

    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
