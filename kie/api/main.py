"""
KIE v3 FastAPI Application

Main API server for KIE v3 backend.
"""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kie.api.routes import charts, health, projects
from kie.config import get_config
from kie.exceptions import KIEError

# Initialize FastAPI app
app = FastAPI(
    title="KIE v3 API",
    description="Kearney Insight Engine v3 - Backend API",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get configuration
config = get_config()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(KIEError)
async def kie_error_handler(request: Request, exc: KIEError):
    """Handle KIE-specific errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


# Import routes (will create these next)

app.include_router(health.router, prefix="/api/v3", tags=["health"])
app.include_router(charts.router, prefix="/api/v3/charts", tags=["charts"])
app.include_router(projects.router, prefix="/api/v3/projects", tags=["projects"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "KIE v3 API",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/api/v3/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "kie.api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
    )
