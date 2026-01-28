"""
GEO Monitor API - Main Application Entry Point

A real-time monitoring platform for tracking brand presence and accuracy
in AI models like ChatGPT, Claude, and Gemini.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.models.database import init_db, close_db
from app.services.scheduler import init_redis, close_redis
from app.api import tasks_router, metrics_router, alerts_router, config_router

# Configure logging
if settings.LOG_FORMAT == "json":
    log_format = '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
else:
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=log_format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting GEO Monitor API...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Initialize Redis
        init_redis()
        logger.info("Redis initialized")
        
        logger.info("GEO Monitor API started successfully")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down GEO Monitor API...")
        
        close_redis()
        close_db()
        
        logger.info("GEO Monitor API shut down")


# Create FastAPI application
app = FastAPI(
    title="GEO Monitor API",
    description="""
    GEO Monitor API - Real-time brand monitoring platform for AI models.
    
    ## Features
    
    - **Task Management**: Create and manage brand monitoring tasks
    - **Metrics Analysis**: Get SOV, accuracy, and sentiment metrics
    - **Alert Management**: Configure and receive alerts
    - **Model Routing**: Integrated with OpenRouter for multi-model support
    
    ## Authentication
    
    All endpoints require JWT authentication. Include the token in the
    Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
    return {
        "name": "GEO Monitor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
