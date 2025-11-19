"""
Pipeline server for Code Pipeline
Provides OpenAI-compatible API endpoints with health checks
"""

import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from .code_pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Code Pipeline",
    description="OpenAI-compatible API for Code agentic coding assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = Pipeline()


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    logger.info("Starting Code Pipeline server...")
    if hasattr(pipeline, 'on_startup'):
        await pipeline.on_startup()
    logger.info("Code Pipeline server ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Code Pipeline server...")
    if hasattr(pipeline, 'on_shutdown'):
        await pipeline.on_shutdown()


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return JSONResponse({
        "status": "healthy",
        "service": "code-pipeline",
        "version": "1.0.0"
    })


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return JSONResponse({
        "service": "Code Pipeline",
        "version": "1.0.0",
        "description": "OpenAI-compatible API for Code agentic coding assistant",
        "endpoints": {
            "health": "/health",
            "chat": "/v1/chat/completions",
            "models": "/v1/models"
        }
    })


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    return JSONResponse({
        "object": "list",
        "data": [
            {
                "id": "code-pipeline",
                "object": "model",
                "created": 1677610602,
                "owned_by": "code-pipeline",
                "permission": [],
                "root": "code-pipeline",
                "parent": None,
            }
        ]
    })


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint
    Proxies to the Code pipeline
    """
    try:
        body = await request.json()

        # Extract user info from headers if available
        user_id = request.headers.get("X-User-Id", "default")

        # Add user info to body for pipeline
        body["user"] = {
            "id": user_id,
            "email": request.headers.get("X-User-Email", ""),
            "name": request.headers.get("X-User-Name", "")
        }

        # Check if streaming is requested
        stream = body.get("stream", False)

        if stream:
            # Return streaming response
            async def generate():
                async for chunk in pipeline.pipe(body):
                    if isinstance(chunk, str):
                        yield chunk
                    else:
                        yield str(chunk)

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # Return non-streaming response
            result = await pipeline.pipe(body)
            return JSONResponse(result)

    except Exception as e:
        logger.error(f"Error in chat completions: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": str(e),
                    "type": "internal_server_error",
                    "code": "internal_error"
                }
            }
        )


def main():
    """Run the pipeline server"""
    import os

    port = int(os.getenv("PIPELINES_PORT", "9099"))
    host = os.getenv("PIPELINES_HOST", "0.0.0.0")

    logger.info(f"Starting Code Pipeline server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
