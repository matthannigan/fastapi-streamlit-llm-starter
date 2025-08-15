"""Main FastAPI application for AI Text Processing with comprehensive resilience features.

This module serves as the primary entry point for the AI Text Processing API, providing
a robust and scalable FastAPI application with advanced text processing capabilities.
The application implements a dual-API architecture with separate public and internal
interfaces, comprehensive resilience patterns, intelligent caching, and extensive
monitoring to deliver a production-ready service.

## Architecture

The application follows a **dual-API architecture pattern**:

- **Public API** (`/`): External-facing endpoints for AI text processing operations
- **Internal API** (`/internal/`): Administrative endpoints for monitoring and management

This separation provides security isolation, allows independent scaling, and enables
different documentation and authentication strategies for different user types.

## Key Features

### AI Text Processing
- **Powered by Google Gemini API** for advanced text analysis
- **Supported Operations**: summarization, sentiment analysis, key point extraction, 
  question generation, and question answering
- **Batch Processing**: Efficient handling of multiple text processing requests
- **Input Sanitization**: Protection against prompt injection and malicious inputs

### Resilience Infrastructure
- **Circuit Breaker Patterns**: Prevent cascade failures during API outages
- **Intelligent Retry Logic**: Exponential backoff with jitter for transient failures
- **Exception Classification**: Smart categorization of permanent vs transient errors
- **Graceful Degradation**: Continued operation during partial service failures

### Intelligent Caching
- **Redis-backed Storage**: Persistent caching with automatic failover to memory-only
- **Compression Support**: Automatic compression for large responses
- **Memory Tiering**: Two-tier caching with memory and Redis backends
- **Performance Monitoring**: Real-time cache metrics and optimization recommendations

### Monitoring & Observability
- **Health Checks**: Comprehensive system and dependency health monitoring
- **Performance Metrics**: Operation timing, success rates, and failure patterns
- **Circuit Breaker Status**: Real-time resilience pattern monitoring
- **Cache Analytics**: Hit rates, memory usage, and performance statistics

### Security
- **API Key Authentication**: Bearer token authentication with multi-key support
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation and sanitization
- **Internal API Protection**: Restricted access to administrative endpoints

## API Endpoints

### Public API (`/docs`)
- `GET /`: Root endpoint with API information and navigation links
- `GET /v1/health`: Comprehensive health check with component status
- `GET /v1/auth/status`: Authentication validation and API key verification
- `POST /v1/text_processing/process`: Single text processing operations
- `POST /v1/text_processing/batch_process`: Batch text processing operations

### Internal API (`/internal/docs`)
- `GET /internal/`: Internal API root with administrative information
- `GET /internal/monitoring/*`: System metrics and performance data
- `GET /internal/cache/*`: Cache status, metrics, and management operations
- `GET /internal/resilience/*`: Resilience configuration and monitoring endpoints

### Utility Redirects
- `GET /health` → `/v1/health` (for monitoring system compatibility)
- `GET /auth/status` → `/v1/auth/status` (for auth validation compatibility)

## Configuration

The application uses environment-based configuration through the `Settings` class:

### AI Configuration
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `AI_MODEL`: AI model selection (default: gemini-1.5-flash)

### Authentication
- `API_KEY`: Primary API key for authentication
- `ADDITIONAL_API_KEYS`: Comma-separated additional valid keys

### Caching
- `REDIS_URL`: Redis connection string (optional, defaults to memory-only)
- Cache TTL and compression settings

### Resilience
- `RESILIENCE_PRESET`: Resilience configuration preset (simple, development, production)
- Circuit breaker and retry parameters

### Server Configuration
- `HOST`: Server bind address (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode flag
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS`: Allowed CORS origins

## Application Lifecycle

The application uses an async context manager for proper lifecycle management:

1. **Startup**: Logs configuration, initializes services, validates connections
2. **Runtime**: Handles requests with resilience patterns and monitoring
3. **Shutdown**: Graceful cleanup of resources and connections

## Documentation Access

### Development Mode
- Public API Docs: `http://localhost:8000/docs`
- Internal API Docs: `http://localhost:8000/internal/docs` 
- ReDoc: `http://localhost:8000/redoc` and `http://localhost:8000/internal/redoc`

### Production Mode
- Public API Docs: Available at `/docs`
- Internal API Docs: **Disabled for security** (404 response)
- OpenAPI Schemas: **Disabled for security**

## Usage Examples

### Development
```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
```bash
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key your-image:tag
```

## Custom Features

### Custom Swagger UI
- **Navigation Between APIs**: Built-in navigation between public and internal docs
- **Enhanced Styling**: Custom styling and branding
- **Security-aware**: Internal docs disabled in production mode

### OpenAPI Schema Customization
- **Clean Schemas**: Removes default FastAPI validation error schemas
- **Custom Error Responses**: Maintains application-specific error schemas
- **Version-aware**: Separate schemas for public and internal APIs

## Error Handling

The application implements comprehensive error handling:
- **Global Exception Handlers**: Centralized error processing
- **Structured Error Responses**: Consistent error format across all endpoints  
- **Security-aware Errors**: No sensitive information exposure in production
- **Logging Integration**: All errors logged with appropriate detail levels

## Security Considerations

- **Production Hardening**: Internal API documentation disabled in production
- **API Key Protection**: Secure handling of authentication credentials
- **Input Sanitization**: Protection against injection attacks
- **CORS Configuration**: Controlled cross-origin access
- **Audit Logging**: Security event tracking and monitoring
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

from app.core.config import settings
from app.core.middleware import setup_middleware, setup_enhanced_middleware
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

# Suppress INFO messages from middleware module
middleware_logger = logging.getLogger('app.core.middleware')
middleware_logger.setLevel(logging.WARNING)  # Only show WARNING and above

# Custom Swagger UI HTML with navigation between public and internal APIs
def get_custom_swagger_ui_html(
    openapi_url: str,
    title: str,
    api_type: str = "public"
) -> str:
    """Generate custom Swagger UI HTML with navigation between APIs."""
    
    navigation_buttons = """
    <div style="
        position: fixed; 
        top: 10px; 
        right: 10px; 
        z-index: 1000; 
        display: flex; 
        gap: 10px;
        background: white;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <a href="/docs" style="
            padding: 8px 16px; 
            background: """ + ("#4CAF50" if api_type == "public" else "#2196F3") + """; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
        ">🌐 Public API</a>
        <a href="/internal/docs" style="
            padding: 8px 16px; 
            background: """ + ("#4CAF50" if api_type == "internal" else "#2196F3") + """; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
        ">🔧 Internal API</a>
    </div>
    """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css" />
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}
            *, *:before, *:after {{
                box-sizing: inherit;
            }}
            body {{
                margin:0;
                background: #fafafa;
            }}
            .topbar {{
                display: none;
            }}
        </style>
    </head>
    <body>
        {navigation_buttons}
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: '{openapi_url}',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                }});
            }};
        </script>
    </body>
    </html>
    """


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
    logger.info("Public API docs available at: /docs")
    logger.info("Internal API docs available at: /internal/docs")
    # Initialize health infrastructure
    try:
        from app.dependencies import initialize_health_infrastructure
        await initialize_health_infrastructure()
    except Exception as e:
        logger.warning(f"Health infrastructure initialization skipped: {e}")
    yield
    logger.info("Shutting down FastAPI application")


def custom_openapi_schema(app: FastAPI):
    """Generate custom OpenAPI schema without default validation error schemas."""
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate the default schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    
    # Remove unwanted schemas from components
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas_to_remove = [
            "HTTPValidationError",
            "ValidationError", 
            "ValidationErrorElement",
            "ErrorDetails"  # Sometimes FastAPI generates this
        ]
        
        # Find any other validation-related schemas
        all_schemas = list(openapi_schema["components"]["schemas"].keys())
        for schema_name in all_schemas:
            if "validation" in schema_name.lower() or "http" in schema_name.lower():
                if schema_name not in ["ErrorResponse"]:  # Keep our custom error response
                    schemas_to_remove.append(schema_name)
        
        # Remove the schemas
        removed_count = 0
        for schema_name in schemas_to_remove:
            if openapi_schema["components"]["schemas"].pop(schema_name, None) is not None:
                removed_count += 1
        
        # Log what was removed (only in debug mode)
        if settings.debug and removed_count > 0:
            logger.info(f"Removed {removed_count} default validation schemas from OpenAPI spec")
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_public_app() -> FastAPI:
    """Create the public-facing FastAPI application.
    
    This application contains only the public API endpoints that should be
    accessible to external users and documented in the main API documentation.
    
    Returns:
        FastAPI: Configured public API application
    """
    # Define tags metadata for public API
    public_tags_metadata = [
        {
            "name": "Core",
            "description": "Essential API endpoints including root information and basic functionality."
        },
        {
            "name": "Health",
            "description": "System health monitoring endpoints for availability and dependency status checks."
        },
        {
            "name": "Authentication", 
            "description": "Authentication and authorization endpoints for API key validation and access control.",
            "externalDocs": {
                "description": "FastAPI Security Guide",
                "url": "https://fastapi.tiangolo.com/tutorial/security/"
            }
        },
        {
            "name": "Text Processing",
            "description": "AI-powered text processing operations including summarization, sentiment analysis, and Q&A."
        }
    ]
    
    public_app = FastAPI(
        title="AI Text Processor API",
        description="Public API for processing text using AI models",
        version="1.0.0",
        openapi_version="3.0.3",  # Use 3.0.3 for better Swagger UI compatibility
        docs_url=None,  # Disable default docs to use custom
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=public_tags_metadata,
        lifespan=lifespan
    )
    
    # Setup middleware for public app
    setup_enhanced_middleware(public_app, settings)
    
    @public_app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI with navigation between APIs."""
        return HTMLResponse(
            get_custom_swagger_ui_html(
                openapi_url="/openapi.json",
                title="AI Text Processor API - Public Documentation",
                api_type="public"
            )
        )
    
    @public_app.get("/", tags=["Core"])
    async def root():
        """Root endpoint providing basic API information and version details.
        
        This endpoint serves as the main entry point for the API, providing basic
        identification information about the service. It can be used to verify
        that the API is running and accessible.
        
        Returns:
            dict: A dictionary containing:
                - message (str): The API name and description
                - version (str): Current API version identifier
                - docs (str): Link to API documentation
                - internal_docs (str): Link to internal API documentation
        
        Example:
            >>> # GET /
            >>> {
            ...   "message": "AI Text Processor API",
            ...   "version": "1.0.0",
            ...   "docs": "/docs",
            ...   "internal_docs": "/internal/docs"
            ... }
        """
        return {
            "message": "AI Text Processor API",
            "version": "1.0.0",
            "docs": "/docs",
            "internal_docs": "/internal/docs",
            "api_version": "v1",
            "endpoints": {
                "health": "/v1/health",
                "auth": "/v1/auth/status",
                "text_processing": "/v1/text_processing/process"
            }
        }
    
    # Include public API routers
    public_app.include_router(health_router, prefix="/v1")
    public_app.include_router(auth_router, prefix="/v1")
    public_app.include_router(text_processing_router, prefix="/v1")
    
    # Utility endpoint compatibility - redirect to current version  
    # These are stable utility endpoints that rarely have breaking changes
    # and are commonly expected to be available without version prefixes
    @public_app.get("/health", include_in_schema=False)
    async def health_redirect():
        """Utility redirect - monitoring systems often expect unversioned health endpoints."""
        from fastapi import Response
        return Response(
            status_code=301,
            headers={
                "Location": "/v1/health",
                "X-API-Version": "v1", 
                "X-Endpoint-Type": "utility"
            }
        )

    @public_app.get("/auth/status", include_in_schema=False) 
    async def auth_status_redirect():
        """Utility redirect - auth validation is typically stable across versions."""
        from fastapi import Response
        return Response(
            status_code=301,
            headers={
                "Location": "/v1/auth/status",
                "X-API-Version": "v1",
                "X-Endpoint-Type": "utility" 
            }
        )

    # Note: Text processing endpoints require explicit versioning as they
    # contain core business logic that may have breaking changes between versions
    
    # Apply custom OpenAPI schema generation
    public_app.openapi = lambda: custom_openapi_schema(public_app)
    
    return public_app


def create_internal_app() -> FastAPI:
    """Create the internal/administrative FastAPI application.
    
    This application contains only the internal API endpoints for monitoring,
    administration, and system management. These endpoints are typically used
    by operations teams, monitoring systems, and administrative tools.
    
    Returns:
        FastAPI: Configured internal API application
    """
    # Define tags metadata for internal API
    internal_tags_metadata = [
        {
            "name": "Internal",
            "description": "Internal administrative endpoints providing system information and operational data."
        },
        {
            "name": "System Monitoring",
            "description": "Comprehensive system monitoring including health checks, performance metrics, and component status."
        },
        {
            "name": "Cache Management",
            "description": "Cache infrastructure management including status monitoring, invalidation, and performance optimization."
        },
        {
            "name": "Resilience Core",
            "description": "Core resilience infrastructure endpoints for health monitoring and circuit breaker management."
        },
        {
            "name": "Resilience Configuration",
            "description": "Resilience configuration management including presets, templates, and validation tools."
        },
        {
            "name": "Resilience Monitoring",
            "description": "Advanced resilience monitoring and analytics for performance tracking and failure analysis."
        },
        {
            "name": "Resilience Performance",
            "description": "Performance benchmarking and testing tools for resilience infrastructure optimization."
        }
    ]
    
    internal_app = FastAPI(
        title="AI Text Processor - Internal API",
        description="Internal API for monitoring, administration, and system management.",
        version="1.0.0",
        openapi_version="3.0.3",  # Use 3.0.3 for better Swagger UI compatibility
        docs_url=None,  # Disable default docs to use custom
        redoc_url="/redoc" if settings.debug else None, # Available at /internal/redoc; disabled in production
        openapi_url="/openapi.json" if settings.debug else None,  # Available at /internal/openapi.json disabled in production
        openapi_tags=internal_tags_metadata,
    )
    
    # Note: Internal app doesn't need CORS middleware as it's for internal use
    # But we may want to add specific security middleware for internal endpoints
    
    @internal_app.get("/docs", include_in_schema=False)
    async def custom_internal_swagger_ui_html():
        """Custom Swagger UI with navigation between APIs."""
        if not settings.debug:
            raise HTTPException(status_code=404, detail="Documentation not available in production")
        return HTMLResponse(
            get_custom_swagger_ui_html(
                openapi_url="/internal/openapi.json",  # Use absolute path to internal API schema
                title="AI Text Processor - Internal API Documentation",
                api_type="internal"
            )
        )
    
    @internal_app.get("/", tags=["Internal"])
    async def internal_root():
        """Internal API root endpoint.
        
        Provides information about the internal API and available administrative
        endpoints for system monitoring and management.
        
        Returns:
            dict: Information about the internal API including available endpoints
        """
        return {
            "message": "AI Text Processor - Internal API",
            "version": "1.0.0",
            "description": "Administrative and monitoring endpoints",
            "available_endpoints": [
                "/monitoring/*",
                "/cache/*",
                "/resilience/*"
            ]
        }
    
    # Include internal API routers
    internal_app.include_router(monitoring_router)
    internal_app.include_router(cache_router)
    
    # Include all resilience routers
    internal_app.include_router(resilience_health_router)
    internal_app.include_router(resilience_circuit_breakers_router)
    internal_app.include_router(resilience_config_router)
    internal_app.include_router(resilience_config_presets_router)
    internal_app.include_router(resilience_config_templates_router)
    internal_app.include_router(resilience_config_validation_router)
    internal_app.include_router(resilience_monitoring_router)
    internal_app.include_router(resilience_performance_router)
    
    # Apply custom OpenAPI schema generation
    internal_app.openapi = lambda: custom_openapi_schema(internal_app)
    
    return internal_app


# Create the main public application
app = create_public_app()

# Create the internal application
internal_app = create_internal_app()

# Mount the internal application at /internal
app.mount("/internal", internal_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
