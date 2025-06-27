"""Main FastAPI application for AI Text Processing with resilience features.

This module contains the primary FastAPI application that provides AI-powered text processing
capabilities with comprehensive resilience, monitoring, and caching features. The application
is designed to be highly available and fault-tolerant with circuit breakers, health checks,
and performance monitoring.

The application includes the following key features:
    - AI text processing using Google Gemini API
    - Circuit breaker patterns for resilience
    - Comprehensive health monitoring and metrics
    - Response caching for improved performance
    - API key authentication for security
    - CORS support for cross-origin requests
    - Structured error handling and logging

Available API endpoints:
    - /: Root endpoint with API information
    - /health: Enhanced health check with resilience status
    - /auth/status: Authentication status verification
    - /api/v1/text-processing/*: Text processing endpoints
    - /api/internal/monitoring/*: System monitoring endpoints
    - /api/internal/cache/*: Cache management endpoints
    - /api/internal/resilience/*: Resilience configuration and monitoring

Configuration:
    The application is configured through environment variables and the settings module,
    including AI model selection, logging levels, CORS origins, and API authentication.

Usage:
    Run the application directly:
        python main.py
    
    Or with uvicorn:
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Note:
    This application requires proper environment configuration including API keys
    for AI services and authentication tokens for API access.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.models import (
    ErrorResponse,
    HealthResponse,
)

from app.config import settings
from app.infrastructure.security import verify_api_key
from app.api.v1.text_processing import router as text_processing_router
from app.api.internal.cache import router as cache_router
from app.api.internal.monitoring import monitoring_router
from app.api.internal.resilience import (
    resilience_advanced_config_router,
    resilience_circuit_breakers_router,
    resilience_health_router,
    resilience_monitoring_router,
    resilience_performance_router,
    resilience_presets_router,
    resilience_security_router,
    resilience_templates_router
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting FastAPI application")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AI Model: {settings.ai_model}")
    yield
    logger.info("Shutting down FastAPI application")

# Create FastAPI app
app = FastAPI(
    title="AI Text Processor API",
    description="API for processing text using AI models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# Note: mypy has issues with FastAPI's add_middleware and CORSMiddleware
# This is a known issue and the code works correctly at runtime
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.allowed_origins,  # type: ignore[call-arg]
    allow_credentials=True,  # type: ignore[call-arg]
    allow_methods=["*"],  # type: ignore[call-arg]
    allow_headers=["*"],  # type: ignore[call-arg]
)

# No routers needed - using direct service integration

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Text Processor API", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with resilience status."""
    try:
        from app.infrastructure.resilience import ai_resilience
        
        ai_healthy = bool(settings.gemini_api_key)
        resilience_healthy = ai_resilience.is_healthy()
        
        return HealthResponse(
            status="healthy" if ai_healthy and resilience_healthy else "degraded",
            ai_model_available=ai_healthy,
            resilience_healthy=resilience_healthy
        )
    except Exception:
        # Fallback if resilience service is not available
        return HealthResponse(
            ai_model_available=bool(settings.gemini_api_key),
            resilience_healthy=None
        )

@app.get("/auth/status")
async def auth_status(api_key: str = Depends(verify_api_key)):
    """Check authentication status."""
    return {
        "authenticated": True,
        "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
        "message": "Authentication successful"
    }

# Include the text processing router
app.include_router(text_processing_router)

# Include the monitoring router
app.include_router(monitoring_router)

# Include the cache router
app.include_router(cache_router)

# Include the resilience routers
app.include_router(resilience_health_router)
app.include_router(resilience_circuit_breakers_router)
app.include_router(resilience_presets_router)
app.include_router(resilience_advanced_config_router)
app.include_router(resilience_monitoring_router)
app.include_router(resilience_performance_router)
app.include_router(resilience_security_router)
app.include_router(resilience_templates_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
