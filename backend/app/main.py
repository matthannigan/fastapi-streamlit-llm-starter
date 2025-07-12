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

from shared.models import (
    ErrorResponse,
    HealthResponse,
)

from app.core.config import settings
from app.infrastructure.security import verify_api_key
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
    """Global exception handler for unhandled application errors.
    
    Provides a centralized error handling mechanism that catches all unhandled
    exceptions across the application and returns a consistent error response
    format. This handler ensures that client applications receive predictable
    error responses even when unexpected server errors occur.
    
    The handler logs all exceptions for debugging and monitoring purposes while
    returning a generic error message to clients to avoid exposing internal
    implementation details or sensitive information.
    
    Args:
        request: The FastAPI request object that triggered the exception
        exc (Exception): The unhandled exception that was raised during
            request processing
    
    Returns:
        JSONResponse: A standardized error response containing:
            - error (str): Generic error message for client consumption
            - error_code (str): Standardized error code for programmatic handling
            - success (bool): Always False for error responses
            - timestamp (datetime): When the error occurred
    
    Example:
        >>> # Any unhandled exception returns:
        >>> {
        ...   "success": false,
        ...   "error": "Internal server error",
        ...   "error_code": "INTERNAL_ERROR",
        ...   "timestamp": "2025-06-28T00:06:39.130848"
        ... }
    
    Note:
        This handler is registered globally and will catch any exception not
        handled by more specific exception handlers. All exceptions are logged
        with full details for debugging while client responses remain generic
        for security purposes.
    """
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

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with comprehensive system monitoring.
    
    Performs health checks on all critical application components including AI model
    configuration, resilience infrastructure, and cache system status. This endpoint
    provides a comprehensive view of system health and can be used for monitoring,
    load balancer health checks, and operational dashboards.
    
    The health check evaluates three main components:
    
    - **AI Model**: Verifies that the Google Gemini API key is properly configured
      and available for text processing operations.
    - **Resilience Infrastructure**: Checks the operational status of circuit breakers,
      failure detection mechanisms, and resilience orchestration services.
    - **Cache System**: Validates Redis connectivity, memory cache operations, and
      overall cache service availability with graceful degradation support.
    
    The overall system status is determined as "healthy" when the AI model is available
    and no critical components report explicit failures. Optional components (resilience
    and cache services) may be unavailable (None) without affecting overall system
    health, as the application can continue operating with reduced functionality.
    
    Returns:
        HealthResponse: A comprehensive health status response containing:
            - status (str): Overall system health status, either "healthy" or "degraded"
            - ai_model_available (bool): Whether the AI model is properly configured
            - resilience_healthy (Optional[bool]): Resilience infrastructure status,
              None if service is unavailable
            - cache_healthy (Optional[bool]): Cache system operational status,
              None if service is unavailable  
            - timestamp (datetime): When the health check was performed (ISO format)
            - version (str): Current API version identifier
    
    Raises:
        Exception: Internal errors are caught and handled gracefully. Component
            failures result in None values rather than endpoint failures, ensuring
            the health check remains available even when subsystems are down.
    
    Example:
        >>> # GET /health
        >>> {
        ...   "status": "healthy",
        ...   "timestamp": "2025-06-28T00:06:39.130848",
        ...   "version": "1.0.0",
        ...   "ai_model_available": true,
        ...   "resilience_healthy": true,
        ...   "cache_healthy": true
        ... }
        
    Note:
        This endpoint does not require authentication and should be used by monitoring
        systems, load balancers, and operational tools. Cache health checks create
        temporary connections that are automatically cleaned up.
    """
    ai_healthy = bool(settings.gemini_api_key)
    resilience_healthy = None
    cache_healthy = None
    
    # Check resilience health
    try:
        from app.infrastructure.resilience import ai_resilience
        resilience_healthy = ai_resilience.is_healthy()
    except Exception:
        logger.warning("Resilience service is not available")
        resilience_healthy = None
    
    # Check cache health
    try:
        from app.infrastructure.cache import AIResponseCache
        
        # Create cache service instance manually (not using dependency injection)
        cache_service = AIResponseCache(
            redis_url=settings.redis_url,
            default_ttl=settings.cache_default_ttl,
            text_hash_threshold=settings.cache_text_hash_threshold,
            compression_threshold=settings.cache_compression_threshold,
            compression_level=settings.cache_compression_level,
            text_size_tiers=settings.cache_text_size_tiers,
            memory_cache_size=settings.cache_memory_cache_size
        )
        
        # Try to connect and get stats
        await cache_service.connect()
        cache_stats = await cache_service.get_cache_stats()
        
        # Determine cache health based on status indicators
        cache_healthy = (
            cache_stats.get("redis", {}).get("status") != "error" and
            cache_stats.get("memory", {}).get("status") != "unavailable" and
            cache_stats.get("performance", {}).get("status") != "unavailable" and
            "error" not in cache_stats
        )
                
    except Exception as e:
        logger.warning(f"Cache service is not available: {e}")
        cache_healthy = None
    
    # Overall health determination
    # Consider healthy if AI is available and no critical components are explicitly unhealthy
    # Allow for optional components (resilience, cache) to be None without affecting overall health
    overall_healthy = ai_healthy and (
        resilience_healthy is not False and cache_healthy is not False
    )
    
    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        ai_model_available=ai_healthy,
        resilience_healthy=resilience_healthy,
        cache_healthy=cache_healthy
    )

@app.get("/auth/status")
async def auth_status(api_key: str = Depends(verify_api_key)):
    """Verify authentication status and return API key validation information.
    
    This endpoint validates the provided API key and returns authentication status
    information. It serves as a secure health check for authentication systems and
    provides a safe method to validate API keys without exposing sensitive data.
    
    The endpoint requires a valid API key provided through the standard authentication
    mechanism (Authorization header with "Bearer <token>" format or X-API-Key header).
    Upon successful authentication, it returns confirmation details with a safely
    truncated version of the API key for verification purposes.
    
    Args:
        api_key (str): The validated API key obtained through the verify_api_key
            dependency. This parameter is automatically injected by FastAPI's
            dependency injection system after successful authentication validation.
    
    Returns:
        dict: Authentication status information containing:
            - authenticated (bool): Always True when the request reaches this endpoint,
              confirming successful authentication
            - api_key_prefix (str): Safely truncated API key showing only the first
              8 characters followed by "..." for security verification purposes.
              Keys with 8 characters or fewer display the complete key
            - message (str): Human-readable confirmation message indicating successful
              authentication
    
    Raises:
        HTTPException: Authentication failures raise HTTP exceptions:
            - 401 Unauthorized: No API key provided in request headers
            - 401 Unauthorized: Invalid or malformed API key provided
            - 401 Unauthorized: API key format is incorrect or unrecognized
    
    Example:
        >>> # GET /auth/status
        >>> # Headers: Authorization: Bearer your-api-key-here
        >>> {
        ...   "authenticated": true,
        ...   "api_key_prefix": "abcd1234...",
        ...   "message": "Authentication successful"
        ... }
    
    Note:
        This endpoint is designed for:
        - API key validation in client applications and SDKs
        - Authentication system health monitoring and diagnostics
        - Debugging authentication configuration issues
        - Integration testing of authentication workflows
        - Verifying API key rotation and management processes
    """
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
