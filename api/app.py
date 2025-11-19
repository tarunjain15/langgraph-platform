"""
FastAPI Application - Hosted Mode API Server

Provides HTTP endpoints for workflow invocation and session management.
"""

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from api.routes import workflows, sessions
from api.middleware.auth import verify_api_key
import os


# Create FastAPI app
app = FastAPI(
    title="LangGraph Platform API",
    description="Workflow runtime API for hosted mode",
    version="0.1.0"
)


# Include routers
app.include_router(workflows.router)
app.include_router(sessions.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LangGraph Platform API",
        "version": "0.1.0",
        "environment": "hosted",
        "status": "running",
        "auth_enabled": os.getenv("LGP_AUTH_ENABLED", "true") == "true"
    }


@app.get("/health")
async def health():
    """Health check endpoint (no auth required)"""
    return {
        "status": "healthy",
        "environment": "hosted"
    }


@app.get("/protected-example")
async def protected_example(api_key: str = Depends(verify_api_key)):
    """Example of protected endpoint requiring API key"""
    return {
        "message": "Access granted",
        "api_key": api_key[:10] + "..." if len(api_key) > 10 else api_key
    }
