"""Main FastAPI application for AI Text Processing with comprehensive resilience features.

This module serves as the primary entry point for the AI Text Processing API, providing
a robust and scalable FastAPI application with advanced text processing capabilities.
The application integrates AI-powered text analysis, comprehensive resilience patterns,
intelligent caching, and extensive monitoring to deliver a production-ready service.

The application architecture is designed for high availability and fault tolerance,
incorporating industry best practices for API design, error handling, and operational
monitoring. It supports graceful degradation when dependencies are unavailable and
provides comprehensive observability for production environments.

Key Features:
    * **AI Text Processing**: Powered by Google Gemini API for advanced text analysis
      including summarization, sentiment analysis, key point extraction, and Q&A
    * **Resilience Infrastructure**: Circuit breaker patterns, retry mechanisms, and
      failure detection to handle API failures and service degradation gracefully
    * **Intelligent Caching**: Redis-backed response caching with compression, memory
      tiering, and performance monitoring for improved response times and cost efficiency
    * **Comprehensive Monitoring**: Health checks, performance metrics, circuit breaker
      status, and cache analytics for operational visibility
    * **Security**: API key authentication, CORS configuration, and input validation
      to protect against unauthorized access and malicious inputs
    * **Structured Logging**: Comprehensive logging with configurable levels for
      debugging, monitoring, and audit trails

API Endpoints:
    Core Endpoints:
        * GET /: Root endpoint providing API information and version details
        * GET /health: Comprehensive health check with AI, resilience, and cache status
        * GET /auth/status: Authentication validation and API key verification
    
    Text Processing:
        * POST /api/v1/text-processing/process: Main text processing endpoint
        * POST /api/v1/text-processing/batch: Batch text processing operations
    
    Monitoring & Administration:
        * GET /api/internal/monitoring/*: System metrics and performance data
        * GET /api/internal/cache/*: Cache status, metrics, and management
        * GET /api/internal/resilience/*: Circuit breaker status and configuration

Configuration:
    The application uses environment-based configuration through the Settings class,
    supporting deployment flexibility across different environments. Key configuration
    areas include:
    
    * AI model selection and API credentials
    * Cache settings (Redis URL, TTL, compression)
    * Resilience parameters (timeouts, retry counts, circuit breaker thresholds)
    * Logging levels and output formats
    * CORS origins and security settings
    * Authentication tokens and access control

Usage:
    Development:
        python main.py
        
    Production:
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
        
    Docker:
        docker run -p 8000:8000 your-image:tag

Environment Variables:
    Required:
        * GEMINI_API_KEY: Google Gemini API key for text processing
        * API_KEYS: Comma-separated list of valid API keys for authentication
    
    Optional:
        * REDIS_URL: Redis connection string for caching (defaults to memory-only)
        * LOG_LEVEL: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
        * CORS_ORIGINS: Allowed CORS origins for cross-origin requests

Note:
    This application is designed for production use and includes comprehensive error
    handling, monitoring, and resilience features. Ensure all required environment
    variables are properly configured before deployment.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.middleware import setup_middleware
from app.infrastructure.security import verify_api_key
from app.api.v1.health import health_router
from app.api.v1.auth import auth_router
from app.api.v1.text_processing import router as text_processing_router
from app.api.internal.cache import router as cache_router
from app.api.internal.monitoring import monitoring_router
from app.api.internal.resilience import (
    resilience_config_presets_router,
    resilience_config_templates_router,
    resilience_config_validation_router,
    resilience_circuit_breakers_router,
    resilience_health_router,
    resilience_config_router,
    resilience_monitoring_router,
    resilience_performance_router
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown operations.
    
    Manages the complete lifecycle of the FastAPI application, handling both
    startup initialization and graceful shutdown procedures. This context manager
    ensures proper resource allocation and cleanup throughout the application's
    runtime.
    
    During startup, the manager logs essential configuration information including
    debug mode status and AI model configuration for operational visibility.
    During shutdown, it ensures graceful termination with appropriate logging.
    
    Args:
        app (FastAPI): The FastAPI application instance being managed
    
    Yields:
        None: Control is yielded to the application runtime after startup
            initialization is complete
    
    Example:
        The lifespan manager automatically handles:
        >>> # Startup logs:
        >>> "Starting FastAPI application"
        >>> "Debug mode: True"
        >>> "AI Model: gemini-pro"
        >>> 
        >>> # Shutdown logs:
        >>> "Shutting down FastAPI application"
    
    Note:
        This lifespan manager is automatically registered with the FastAPI
        application and does not require manual invocation. It provides
        centralized lifecycle management for the entire application.
    """
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

# Setup all middleware components
setup_middleware(app, settings)

@app.get("/")
async def root():
    """Root endpoint providing basic API information and version details.
    
    This endpoint serves as the main entry point for the API, providing basic
    identification information about the service. It can be used to verify
    that the API is running and accessible.
    
    Returns:
        dict: A dictionary containing:
            - message (str): The API name and description
            - version (str): Current API version identifier
    
    Example:
        >>> # GET /
        >>> {
        ...   "message": "AI Text Processor API",
        ...   "version": "1.0.0"
        ... }
    """
    return {"message": "AI Text Processor API", "version": "1.0.0"}

# Include the health router
app.include_router(health_router)

# Include the auth router
app.include_router(auth_router)

# Include the text processing router
app.include_router(text_processing_router)

# Include the monitoring router
app.include_router(monitoring_router)

# Include the cache router
app.include_router(cache_router)

# Include the resilience routers
app.include_router(resilience_health_router)
app.include_router(resilience_circuit_breakers_router)
app.include_router(resilience_config_router)
app.include_router(resilience_config_presets_router)
app.include_router(resilience_config_templates_router)
app.include_router(resilience_config_validation_router)
app.include_router(resilience_monitoring_router)
app.include_router(resilience_performance_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
