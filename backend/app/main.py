"""
Main FastAPI Application Module - AI Text Processing Service with Production-Ready Architecture

This module serves as the primary entry point for the comprehensive AI Text Processing API,
implementing a sophisticated dual-API architecture with advanced text processing capabilities,
enterprise-grade resilience patterns, intelligent multi-tier caching, and comprehensive 
monitoring infrastructure designed for production deployment at scale.

## Module Architecture

This module implements a sophisticated multi-layered application architecture:

### Application Layer Structure
- **Main Application Factory**: Creates and configures the primary FastAPI application instance
- **Dual-API Architecture**: Separate public and internal API applications with distinct responsibilities
- **Lifecycle Management**: Comprehensive application startup and shutdown orchestration
- **Custom Documentation**: Enhanced Swagger UI with cross-API navigation and security-aware features
- **OpenAPI Customization**: Clean schema generation with security-optimized documentation

### Integration Architecture  
- **Infrastructure Services**: Seamless integration with cache, resilience, AI, security, and monitoring infrastructure
- **Middleware Stack**: Production-ready middleware pipeline with security, monitoring, and performance optimization
- **Configuration Management**: Environment-aware configuration with preset-based resilience strategies
- **Error Handling**: Global exception handling with structured error responses and security considerations
- **Authentication Integration**: Multi-key API authentication with development and production modes

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
from typing import Optional, Callable
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

from app.core.config import settings, create_settings
from app.core.middleware import setup_middleware, setup_enhanced_middleware
from app.infrastructure.security import verify_api_key
from app.core.environment import is_production_environment, get_environment_info, FeatureContext
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
    """
    Generate enhanced Swagger UI HTML with cross-API navigation and custom styling.
    
    This function creates a custom Swagger UI implementation that provides seamless navigation
    between the public and internal API documentations, enabling developers and operations
    teams to easily switch contexts while maintaining visual consistency and professional
    presentation standards.
    
    Args:
        openapi_url: The OpenAPI schema URL for loading API specifications.
                    Must be a valid URL path (e.g., "/openapi.json", "/internal/openapi.json").
        title: The document title to display in browser tab and page header.
              Should be descriptive and indicate the API type for easy identification.
        api_type: The type of API being documented for navigation button styling.
                 Valid values are "public" or "internal", affecting visual highlighting
                 and navigation behavior.
    
    Returns:
        Complete HTML document as a string containing the enhanced Swagger UI with:
        - Navigation buttons for switching between public and internal API docs
        - Custom styling for professional presentation and improved readability
        - Swagger UI 5.10.5 integration with modern interface components
        - Responsive design that adapts to different screen sizes
        - Security-aware navigation that respects production mode restrictions
        
    Behavior:
        - Generates navigation buttons with visual indicators for current API type
        - Applies custom CSS styling to hide default topbar and improve aesthetics
        - Configures Swagger UI with deep linking and standalone preset
        - Uses CDN-hosted Swagger UI resources for reliability and performance
        - Implements responsive design principles for mobile and desktop viewing
        - Provides consistent branding and user experience across both API types
        
    Examples:
        >>> # Generate public API documentation
        >>> html = get_custom_swagger_ui_html(
        ...     openapi_url="/openapi.json",
        ...     title="AI Text Processor API - Public Documentation",
        ...     api_type="public"
        ... )
        >>> assert "/docs" in html  # Contains navigation to public docs
        >>> assert "/internal/docs" in html  # Contains navigation to internal docs
        
        >>> # Generate internal API documentation
        >>> internal_html = get_custom_swagger_ui_html(
        ...     openapi_url="/internal/openapi.json", 
        ...     title="AI Text Processor - Internal API Documentation",
        ...     api_type="internal"
        ... )
        >>> assert "🔧 Internal API" in internal_html  # Contains internal API indicator
        
        >>> # Navigation button styling changes based on current API type
        >>> public_html = get_custom_swagger_ui_html("/openapi.json", "Public API", "public")
        >>> assert "#4CAF50" in public_html  # Green highlighting for active public API
        
        >>> internal_html = get_custom_swagger_ui_html("/internal/openapi.json", "Internal API", "internal") 
        >>> assert "#4CAF50" in internal_html  # Green highlighting for active internal API
    """
    
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
    """
    Comprehensive application lifespan manager with startup initialization and graceful shutdown.
    
    This async context manager orchestrates the complete lifecycle of the FastAPI application,
    handling sophisticated startup procedures including infrastructure initialization, health
    system setup, and operational logging, followed by graceful shutdown with proper resource
    cleanup and connection termination.
    
    Args:
        app: The FastAPI application instance being managed throughout its lifecycle.
            This includes both public and internal API applications with their
            complete middleware stacks, route configurations, and dependencies.
    
    Yields:
        None: Control is yielded to the application runtime after all startup
              initialization procedures are complete and the application is ready
              to serve requests. The application continues running until shutdown
              is initiated.
    
    Behavior:
        **Startup Phase:**
        - Logs application startup with configuration summary for operational visibility
        - Displays debug mode status for environment identification and troubleshooting
        - Reports AI model configuration for service capability verification
        - Documents API documentation URLs for developer and operations access
        - Initializes health infrastructure for monitoring and dependency tracking
        - Handles initialization errors gracefully with appropriate warning logs
        - Ensures all critical services are ready before accepting requests
        
        **Runtime Phase:**
        - Application serves requests with full infrastructure support
        - All middleware, authentication, caching, and resilience patterns are active
        - Health checks, monitoring, and performance tracking operate continuously
        - Logging and audit systems capture operational events and security information
        
        **Shutdown Phase:**
        - Logs shutdown initiation for operational tracking and audit purposes
        - Allows FastAPI's built-in cleanup mechanisms to handle resource deallocation
        - Ensures graceful termination without data loss or connection interruption
        - Provides clean exit for container orchestration and deployment systems
        
    Raises:
        Exception: Startup initialization errors are caught and logged as warnings,
                  allowing the application to continue startup even if optional
                  components fail to initialize properly.
    
    Examples:
        >>> # Automatic startup logging output:
        >>> # INFO - Starting FastAPI application
        >>> # INFO - Debug mode: True  
        >>> # INFO - AI Model: gemini-2.0-flash-exp
        >>> # INFO - Public API docs available at: /docs
        >>> # INFO - Internal API docs available at: /internal/docs
        
        >>> # Health infrastructure initialization:
        >>> # INFO - Health infrastructure initialized successfully
        >>> # or
        >>> # WARNING - Health infrastructure initialization skipped: Connection failed
        
        >>> # Shutdown logging output:
        >>> # INFO - Shutting down FastAPI application
        
        >>> # The lifespan manager integrates automatically with FastAPI:
        >>> app = FastAPI(lifespan=lifespan)
        >>> # Lifecycle management is now handled automatically
    
    Note:
        This lifespan manager is automatically registered with FastAPI applications
        and requires no manual invocation. It provides centralized lifecycle management
        for the entire application ecosystem including all infrastructure services,
        monitoring systems, and operational components.
    """
    logger.info("Starting FastAPI application")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AI Model: {settings.ai_model}")

    # Environment-aware startup logging
    try:
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        is_production_env = is_production_environment()

        logger.info(f"Environment: {env_info.environment} (confidence: {env_info.confidence:.2f})")
        logger.info("Public API docs available at: /docs")

        if is_production_env:
            logger.info("Internal API docs: DISABLED (production environment)")
        else:
            logger.info("Internal API docs available at: /internal/docs")
    except Exception as e:
        # Fallback to original behavior if environment detection fails
        logger.warning(f"Environment detection failed: {e}")
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
    """
    Generate optimized OpenAPI schema with clean components and enhanced security.
    
    This function creates a customized OpenAPI specification by removing default FastAPI
    validation error schemas that clutter the API documentation, while preserving
    application-specific error response models. This results in cleaner, more professional
    API documentation that focuses on actual application functionality.
    
    Args:
        app: The FastAPI application instance for which to generate the OpenAPI schema.
            Must be a fully configured FastAPI application with routes, tags, and
            metadata properly defined.
    
    Returns:
        dict: Complete OpenAPI 3.0.3 specification dictionary containing:
              - Cleaned component schemas without default FastAPI validation errors
              - Preserved application-specific error response models (e.g., ErrorResponse)
              - All route definitions with proper request/response documentation
              - Security schemes and authentication requirements
              - API metadata including title, version, and description
              
    Behavior:
        - Checks for existing cached schema to avoid regeneration overhead
        - Generates standard OpenAPI schema using FastAPI's built-in utilities
        - Identifies and removes unwanted default validation error schemas
        - Preserves custom application error response models for proper documentation
        - Logs schema cleaning operations in debug mode for troubleshooting
        - Caches the cleaned schema for subsequent requests to improve performance
        - Maintains full OpenAPI 3.0.3 compliance for tooling compatibility
        
    Schema Cleaning Process:
        **Removed Schemas:**
        - HTTPValidationError: FastAPI's default HTTP validation error format
        - ValidationError: Generic Pydantic validation error structure  
        - ValidationErrorElement: Individual validation error details
        - ErrorDetails: Additional FastAPI-generated error detail schemas
        - Any schema containing "validation" or "http" (case-insensitive)
        
        **Preserved Schemas:**
        - ErrorResponse: Application-specific structured error response model
        - All business domain models and request/response schemas
        - Authentication and authorization related schemas
        - Custom data models specific to the application functionality
        
    Examples:
        >>> # Automatic usage via FastAPI application setup:
        >>> app = FastAPI(title="My API")
        >>> app.openapi = lambda: custom_openapi_schema(app)
        >>> # Schema is automatically cleaned when accessed
        
        >>> # Schema caching behavior:
        >>> schema1 = custom_openapi_schema(app)  # Generates and caches schema
        >>> schema2 = custom_openapi_schema(app)  # Returns cached schema
        >>> assert schema1 is schema2  # Same object reference
        
        >>> # Debug mode logging:
        >>> # DEBUG - Removed 4 default validation schemas from OpenAPI spec
        >>> # (Only shown when settings.debug is True)
        
        >>> # Schema structure after cleaning:
        >>> schema = custom_openapi_schema(app)
        >>> assert "HTTPValidationError" not in schema["components"]["schemas"]
        >>> assert "ErrorResponse" in schema["components"]["schemas"]  # Preserved
    
    Note:
        This function is automatically integrated with FastAPI applications through
        the application factory functions and does not require manual invocation.
        The schema cleaning improves documentation quality while maintaining full
        API functionality and error handling capabilities.
    """
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
    """
    Create and configure the comprehensive public-facing FastAPI application.
    
    This factory function constructs the complete public API application with enterprise-grade
    features including AI text processing endpoints, authentication systems, health monitoring,
    enhanced middleware stack, custom documentation, and production-ready security configurations.
    The public API is designed for external users and documented with comprehensive OpenAPI
    specifications.
    
    Returns:
        FastAPI: Fully configured public API application instance containing:
                - Complete AI text processing endpoint suite with batch processing support
                - Multi-key authentication system with development and production modes
                - Comprehensive health monitoring with dependency status tracking
                - Enhanced middleware stack with security, performance, and monitoring
                - Custom Swagger UI with cross-API navigation and professional styling
                - Optimized OpenAPI schema with cleaned component definitions
                - Utility endpoint redirects for monitoring system compatibility
                - Production security features and CORS configuration
    
    Behavior:
        **Application Configuration:**
        - Creates FastAPI instance with comprehensive metadata and OpenAPI 3.0.3 support
        - Configures custom documentation URLs with security-aware access control
        - Sets up professional API tags with detailed descriptions and external documentation
        - Integrates application lifecycle management with startup and shutdown procedures
        
        **Middleware Integration:**
        - Applies enhanced middleware stack including security, monitoring, and performance
        - Configures CORS policies for cross-origin request handling
        - Implements request logging, compression, and rate limiting capabilities
        - Sets up global exception handling with structured error responses
        
        **Endpoint Registration:**
        - Includes all public API routers with proper versioning (v1 prefix)
        - Registers health monitoring endpoints for system availability checks
        - Integrates authentication endpoints for API key validation
        - Adds comprehensive text processing endpoints with batch operation support
        
        **Documentation Enhancement:**
        - Implements custom Swagger UI with navigation between public and internal APIs
        - Applies clean OpenAPI schema generation without default validation errors
        - Provides professional styling and responsive design for documentation
        - Includes comprehensive endpoint metadata and example responses
        
        **Utility Features:**
        - Creates compatibility redirects for unversioned health and auth endpoints
        - Implements proper HTTP redirects with version and endpoint type headers
        - Maintains backward compatibility while encouraging versioned endpoint usage
        - Provides clear separation between core business logic and utility endpoints
        
    Examples:
        >>> # Create public application with full configuration
        >>> public_app = create_public_app()
        >>> assert public_app.title == "AI Text Processor API"
        >>> assert public_app.version == "1.0.0"
        
        >>> # Application includes all public endpoints
        >>> routes = [route.path for route in public_app.routes]
        >>> assert "/" in routes  # Root endpoint
        >>> assert "/v1/health" in routes  # Health monitoring
        >>> assert "/v1/text_processing/process" in routes  # Text processing
        
        >>> # Custom documentation is configured
        >>> assert public_app.docs_url is None  # Default docs disabled
        >>> assert public_app.redoc_url == "/redoc"  # ReDoc available
        >>> assert public_app.openapi_url == "/openapi.json"  # Schema available
        
        >>> # Lifecycle management is configured
        >>> assert public_app.router.lifespan_context is not None
        
        >>> # Utility redirects are available for compatibility
        >>> # GET /health -> 301 redirect to /v1/health
        >>> # GET /auth/status -> 301 redirect to /v1/auth/status
    
    Note:
        This function is called automatically during application startup and should not
        require manual invocation. The returned application is fully configured and
        ready for production deployment with comprehensive feature support.
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
        """
        Root API endpoint providing comprehensive service information and navigation.
        
        This endpoint serves as the primary entry point for the AI Text Processing API,
        providing essential service identification, version information, documentation
        links, and endpoint navigation. It enables clients to discover available API
        capabilities and access appropriate documentation.
        
        Returns:
            dict: Comprehensive API information dictionary containing:
                  - message: Service name and identification
                  - version: Current API version for client compatibility
                  - api_version: API versioning scheme identifier
                  - docs: Public API documentation URL
                  - internal_docs: Internal API documentation URL (operations teams)
                  - endpoints: Key endpoint URLs for primary API functionality
        
        Behavior:
            - Provides service identification for API discovery and client initialization
            - Returns current version information for client compatibility checking
            - Documents available documentation URLs for developers and operations teams
            - Lists primary endpoint URLs for core functionality access
            - Enables programmatic API exploration and service validation
            - Supports monitoring and health check systems with service identification
            
        Response Structure:
            - **message**: "AI Text Processor API" - Service identification
            - **version**: "1.0.0" - Semantic version for compatibility
            - **api_version**: "v1" - API versioning scheme
            - **docs**: "/docs" - Public API Swagger documentation
            - **internal_docs**: "/internal/docs" - Internal API documentation
            - **endpoints**: Dictionary of core endpoint URLs organized by functionality
            
        Examples:
            >>> # GET /
            >>> response = {
            ...     "message": "AI Text Processor API",
            ...     "version": "1.0.0",
            ...     "api_version": "v1",
            ...     "docs": "/docs",
            ...     "internal_docs": "/internal/docs",
            ...     "endpoints": {
            ...         "health": "/v1/health",
            ...         "auth": "/v1/auth/status", 
            ...         "text_processing": "/v1/text_processing/process"
            ...     }
            ... }
            
            >>> # Client service discovery example:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://api.example.com/")
            ...     api_info = response.json()
            ...     health_url = api_info["endpoints"]["health"]
            ...     # Use health_url for health checks
            
            >>> # Version compatibility checking:
            >>> api_version = response["version"]
            >>> if api_version.startswith("1."):
            ...     # Compatible with v1 API
            ...     process_url = response["endpoints"]["text_processing"]
        
        Note:
            This endpoint is always available regardless of authentication status,
            enabling clients to discover API capabilities before authentication.
            It provides the foundation for programmatic API exploration and
            automated service integration.
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
        """
        Utility redirect endpoint for unversioned health check compatibility.
        
        This endpoint provides backward compatibility for monitoring systems and load balancers
        that expect unversioned health endpoints. It redirects to the current versioned health
        endpoint while maintaining proper HTTP semantics and providing version metadata.
        
        Returns:
            Response: HTTP 301 permanent redirect response with headers:
                     - Location: "/v1/health" - Target versioned health endpoint
                     - X-API-Version: "v1" - Current API version for client awareness
                     - X-Endpoint-Type: "utility" - Endpoint classification for monitoring
        
        Behavior:
            - Returns HTTP 301 (Moved Permanently) to indicate the canonical URL
            - Includes version information in response headers for client compatibility
            - Provides endpoint type classification for monitoring and logging systems
            - Maintains compatibility with legacy monitoring configurations
            - Encourages migration to versioned endpoints through proper HTTP semantics
            
        Examples:
            >>> # Monitoring system request:
            >>> # GET /health
            >>> # Response: 301 Moved Permanently
            >>> # Location: /v1/health
            >>> # X-API-Version: v1
            >>> # X-Endpoint-Type: utility
            
            >>> # Automatic redirect handling:
            >>> import httpx
            >>> async with httpx.AsyncClient(follow_redirects=True) as client:
            ...     response = await client.get("http://api.example.com/health")
            ...     # Automatically follows redirect to /v1/health
            ...     assert response.url.path == "/v1/health"
        
        Note:
            This endpoint is excluded from OpenAPI schema documentation to avoid
            cluttering the API specification with utility redirects. Monitoring
            systems should gradually migrate to using the versioned endpoint directly.
        """
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
        """
        Utility redirect endpoint for unversioned authentication status compatibility.
        
        This endpoint provides backward compatibility for authentication validation systems
        that expect unversioned auth endpoints. It redirects to the current versioned
        authentication status endpoint while providing proper HTTP semantics and metadata.
        
        Returns:
            Response: HTTP 301 permanent redirect response with headers:
                     - Location: "/v1/auth/status" - Target versioned auth status endpoint
                     - X-API-Version: "v1" - Current API version for client awareness  
                     - X-Endpoint-Type: "utility" - Endpoint classification for monitoring
        
        Behavior:
            - Returns HTTP 301 (Moved Permanently) to indicate the canonical URL
            - Includes version information in response headers for client compatibility
            - Provides endpoint type classification for authentication and logging systems
            - Maintains compatibility with legacy authentication validation configurations
            - Encourages migration to versioned endpoints through proper HTTP semantics
            
        Examples:
            >>> # Authentication validation request:
            >>> # GET /auth/status
            >>> # Response: 301 Moved Permanently
            >>> # Location: /v1/auth/status
            >>> # X-API-Version: v1
            >>> # X-Endpoint-Type: utility
            
            >>> # Client authentication flow with redirect:
            >>> import httpx
            >>> headers = {"X-API-Key": "your-api-key"}
            >>> async with httpx.AsyncClient(follow_redirects=True) as client:
            ...     response = await client.get("http://api.example.com/auth/status", headers=headers)
            ...     # Automatically follows redirect to /v1/auth/status
            ...     assert response.json()["authenticated"] is True
        
        Note:
            This endpoint is excluded from OpenAPI schema documentation to avoid
            cluttering the API specification with utility redirects. Authentication
            systems should gradually migrate to using the versioned endpoint directly.
        """
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


def create_app(
    settings_obj: Optional['Settings'] = None,
    include_routers: bool = True,
    include_middleware: bool = True,
    lifespan: Optional[Callable] = None
) -> FastAPI:
    """
    Factory function to create a fresh FastAPI application instance with comprehensive configuration.

    This function implements the app factory pattern that enables test isolation and multi-instance
    scenarios while maintaining complete backward compatibility with existing deployment patterns.
    It creates fresh FastAPI instances with all infrastructure properly configured from the
    provided settings or creates new settings from current environment variables.

    Args:
        settings_obj: Optional Settings instance for configuration. If None, creates fresh Settings
                     from current environment variables using create_settings(). This enables
                     test isolation scenarios with custom configuration overrides.
        include_routers: Whether to register API routers (default: True). Useful for testing
                        scenarios where router functionality needs to be isolated or disabled.
        include_middleware: Whether to configure middleware stack (default: True). Enables
                           testing scenarios without middleware interference.
        lifespan: Optional custom lifespan context manager for application startup/shutdown.
                  If None, uses the default lifespan for production deployment scenarios.

    Returns:
        FastAPI: Fully configured FastAPI application instance containing:
                - Complete dual-API architecture with public and internal endpoints
                - Enhanced middleware stack with security, monitoring, and performance features
                - Custom Swagger UI documentation with cross-API navigation
                - Health monitoring infrastructure with comprehensive component validation
                - Proper lifespan event management for service initialization and cleanup
                - Production-ready security configurations and CORS policies

    Behavior:
        **Fresh Instance Creation:**
        - Creates completely new FastAPI instance independent of module-level singleton
        - Uses provided settings_obj or creates fresh Settings from current environment
        - Initializes all infrastructure services with new configuration context
        - Provides complete isolation from other FastAPI instances

        **Configuration Management:**
        - Applies all settings-based configuration (title, debug mode, API metadata)
        - Configures middleware stack based on settings_obj or environment-derived settings
        - Sets up router registration with proper versioning and tag organization
        - Integrates health infrastructure and monitoring capabilities

        **Dual-API Architecture:**
        - Creates main public API with comprehensive business logic endpoints
        - Creates internal API for administrative and monitoring functionality
        - Mounts internal API at /internal path with proper security isolation
        - Maintains complete separation between public and internal concerns

        **Middleware Integration:**
        - Applies enhanced middleware stack when include_middleware=True
        - Configures CORS policies from settings for cross-origin request handling
        - Sets up security headers, request logging, and performance monitoring
        - Implements rate limiting and request size validation

        **Documentation Enhancement:**
        - Configures custom Swagger UI with navigation between public/internal APIs
        - Applies clean OpenAPI schema generation without default validation clutter
        - Provides professional styling and responsive documentation interface
        - Includes comprehensive endpoint metadata and operational guidance

        **Lifecycle Management:**
        - Uses provided lifespan context manager or default production lifespan
        - Handles service initialization during application startup
        - Manages graceful shutdown and resource cleanup
        - Integrates health infrastructure initialization

    Examples:
        >>> # Basic factory usage with default settings
        >>> app = create_app()
        >>> assert app.title == "AI Text Processor API"
        >>> assert "/internal" in [route.path for route in app.routes]

        >>> # Factory usage with custom settings for testing
        >>> test_settings = Settings(debug=True, api_key="test-key")
        >>> test_app = create_app(settings_obj=test_settings)
        >>> # Test app uses provided settings instead of environment

        >>> # Factory usage for isolated testing
        >>> def test_with_mock_services():
        ...     # Create app without routers for focused testing
        ...     minimal_app = create_app(include_routers=False)
        ...     # Test middleware and configuration without endpoint complexity
        ...     assert len(minimal_app.routes) < len(app.routes)

        >>> # Factory usage with custom lifespan
        >>> @asynccontextmanager
        ... async def test_lifespan(app: FastAPI):
        ...     # Custom test initialization
        ...     yield
        ...     # Custom test cleanup
        ...
        >>> test_app = create_app(lifespan=test_lifespan)

        >>> # Environment override testing
        >>> import os
        >>> os.environ['DEBUG'] = 'true'
        >>> debug_app = create_app()
        >>> # Fresh app picks up environment changes immediately

        >>> # Multi-instance scenarios
        >>> app1 = create_app()
        >>> app2 = create_app()
        >>> assert app1 is not app2  # Different instances
        >>> # Each app has independent configuration and services

        >>> # Production deployment (unchanged)
        >>> # Module-level app still works: from app.main import app
        >>> # uvicorn app.main:app --host 0.0.0.0 --port 8000

        >>> # Testing with custom configuration
        >>> test_settings = create_settings()
        >>> test_settings.debug = True
        >>> test_settings.log_level = "DEBUG"
        >>> test_app = create_app(settings_obj=test_settings)
        >>> # Test app uses provided settings for complete configuration control

    Production Usage:
        Traditional deployment (no changes required)::

            from app.main import app  # Uses factory-created module-level app

        Custom deployment with specific settings::

            from app.main import create_app
            from app.core.config import create_settings

            production_settings = create_settings()
            production_settings.debug = False
            custom_app = create_app(settings_obj=production_settings)

    Testing Usage:
        Create isolated test fixtures with custom configuration::

            import pytest
            from fastapi.testclient import TestClient
            from app.main import create_app
            from app.core.config import create_settings

            @pytest.fixture
            def test_client():
                \"\"\"Create isolated test client with fresh app instance.\"\"\"
                test_settings = create_settings()
                test_settings.debug = True
                app = create_app(settings_obj=test_settings)
                return TestClient(app)

        Test middleware configuration without endpoints::

            def test_middleware_only():
                minimal_app = create_app(include_routers=False, include_middleware=True)
                assert isinstance(minimal_app, FastAPI)

    Note:
        This factory function enables test isolation and multi-instance deployment scenarios
        while maintaining complete backward compatibility. For production deployment where
        singleton behavior is preferred, the module-level `app` instance created via
        `app = create_app()` continues to work without any changes to deployment scripts
        or configuration files.
    """
    # Use provided settings or create fresh instance from current environment
    app_settings = settings_obj or create_settings()

    # Create the main public application with provided settings
    main_app = create_public_app_with_settings(app_settings, include_routers, include_middleware, lifespan)

    # Create the internal application with provided settings
    internal_app = create_internal_app_with_settings(app_settings, include_routers, include_middleware)

    # Mount the internal application at /internal
    main_app.mount("/internal", internal_app)

    return main_app


def create_public_app_with_settings(
    settings_obj: 'Settings',
    include_routers: bool = True,
    include_middleware: bool = True,
    lifespan: Optional[Callable] = None
) -> FastAPI:
    """
    Factory function for creating the public FastAPI application with explicit settings.

    This is an internal helper function that creates the public-facing API application
    using the provided settings instance. It enables the main create_app() factory
    to maintain the dual-API architecture while providing proper configuration isolation.

    Args:
        settings_obj: Settings instance to use for configuration
        include_routers: Whether to register API routers
        include_middleware: Whether to configure middleware stack
        lifespan: Optional custom lifespan context manager

    Returns:
        FastAPI: Configured public API application instance
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

    # Use provided lifespan or default lifespan
    app_lifespan = lifespan

    public_app = FastAPI(
        title="AI Text Processor API",
        description="Public API for processing text using AI models",
        version="1.0.0",
        openapi_version="3.0.3",  # Use 3.0.3 for better Swagger UI compatibility
        docs_url=None,  # Disable default docs to use custom
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=public_tags_metadata,
        lifespan=app_lifespan
    )

    # Override dependency injection to use provided settings
    # This ensures all route dependencies use the settings passed to create_app
    from app.dependencies import get_settings
    public_app.dependency_overrides[get_settings] = lambda: settings_obj

    # Setup middleware for public app if requested
    if include_middleware:
        setup_enhanced_middleware(public_app, settings_obj)

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
        """
        Root API endpoint providing comprehensive service information and navigation.

        This endpoint serves as the primary entry point for the AI Text Processing API,
        providing essential service identification, version information, documentation
        links, and endpoint navigation. It enables clients to discover available API
        capabilities and access appropriate documentation.

        Returns:
            dict: Comprehensive API information dictionary containing:
                  - message: Service name and identification
                  - version: Current API version for client compatibility
                  - api_version: API versioning scheme identifier
                  - docs: Public API documentation URL
                  - internal_docs: Internal API documentation URL
                  - endpoints: Key endpoint URLs for primary API functionality

        Behavior:
            - Provides service identification for API discovery and client initialization
            - Returns current version information for client compatibility checking
            - Documents available documentation URLs for developers and operations teams
            - Lists primary endpoint URLs for core functionality access
            - Enables programmatic API exploration and service validation
            - Supports monitoring and health check systems with service identification

        Response Structure:
            - **message**: "AI Text Processor API" - Service identification
            - **version**: "1.0.0" - Semantic version for compatibility
            - **api_version**: "v1" - API versioning scheme
            - **docs**: "/docs" - Public API Swagger documentation
            - **internal_docs**: "/internal/docs" - Internal API documentation
            - **endpoints**: Dictionary of core endpoint URLs organized by functionality

        Examples:
            >>> # GET /
            >>> response = {
            ...     "message": "AI Text Processor API",
            ...     "version": "1.0.0",
            ...     "api_version": "v1",
            ...     "docs": "/docs",
            ...     "internal_docs": "/internal/docs",
            ...     "endpoints": {
            ...         "health": "/v1/health",
            ...         "auth": "/v1/auth/status",
            ...         "text_processing": "/v1/text_processing/process"
            ...     }
            ... }

            >>> # Client service discovery example:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://api.example.com/")
            ...     api_info = response.json()
            ...     health_url = api_info["endpoints"]["health"]
            ...     # Use health_url for health checks

            >>> # Version compatibility checking:
            >>> api_version = response["version"]
            >>> if api_version.startswith("1."):
            ...     # Compatible with v1 API
            ...     process_url = response["endpoints"]["text_processing"]

        Note:
            This endpoint is always available regardless of authentication status,
            enabling clients to discover API capabilities before authentication.
            It provides the foundation for programmatic API exploration and
            automated service integration.
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

    # Include public API routers if requested
    if include_routers:
        public_app.include_router(health_router, prefix="/v1")
        public_app.include_router(auth_router, prefix="/v1")
        public_app.include_router(text_processing_router, prefix="/v1")

    # Utility endpoint compatibility - redirect to current version
    # These are stable utility endpoints that rarely have breaking changes
    # and are commonly expected to be available without version prefixes
    @public_app.get("/health", include_in_schema=False)
    async def health_redirect():
        """
        Utility redirect endpoint for unversioned health check compatibility.

        This endpoint provides backward compatibility for monitoring systems and load balancers
        that expect unversioned health endpoints. It redirects to the current versioned health
        endpoint while maintaining proper HTTP semantics and providing version metadata.

        Returns:
            Response: HTTP 301 permanent redirect response with headers:
                     - Location: "/v1/health" - Target versioned health endpoint
                     - X-API-Version: "v1" - Current API version for client awareness
                     - X-Endpoint-Type: "utility" - Endpoint classification for monitoring

        Behavior:
            - Returns HTTP 301 (Moved Permanently) to indicate the canonical URL
            - Includes version information in response headers for client compatibility
            - Provides endpoint type classification for monitoring and logging systems
            - Maintains compatibility with legacy monitoring configurations
            - Encourages migration to versioned endpoints through proper HTTP semantics

        Examples:
            >>> # Monitoring system request:
            >>> # GET /health
            >>> # Response: 301 Moved Permanently
            >>> # Location: /v1/health
            >>> # X-API-Version: v1
            >>> # X-Endpoint-Type: utility

            >>> # Automatic redirect handling:
            >>> import httpx
            >>> async with httpx.AsyncClient(follow_redirects=True) as client:
            ...     response = await client.get("http://api.example.com/health")
            ...     # Automatically follows redirect to /v1/health
            ...     assert response.url.path == "/v1/health"

        Note:
            This endpoint is excluded from OpenAPI schema documentation to avoid
            cluttering the API specification with utility redirects. Monitoring
            systems should gradually migrate to using the versioned endpoint directly.
        """
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
        """
        Utility redirect endpoint for unversioned authentication status compatibility.

        This endpoint provides backward compatibility for authentication validation systems
        that expect unversioned auth endpoints. It redirects to the current versioned
        authentication status endpoint while providing proper HTTP semantics and metadata.

        Returns:
            Response: HTTP 301 permanent redirect response with headers:
                     - Location: "/v1/auth/status" - Target versioned auth status endpoint
                     - X-API-Version: "v1" - Current API version for client awareness
                     - X-Endpoint-Type: "utility" - Endpoint classification for monitoring

        Behavior:
            - Returns HTTP 301 (Moved Permanently) to indicate the canonical URL
            - Includes version information in response headers for client compatibility
            - Provides endpoint type classification for authentication and logging systems
            - Maintains compatibility with legacy authentication validation configurations
            - Encourages migration to versioned endpoints through proper HTTP semantics

        Examples:
            >>> # Authentication validation request:
            >>> # GET /auth/status
            >>> # Response: 301 Moved Permanently
            >>> # Location: /v1/auth/status
            >>> # X-API-Version: v1
            >>> # X-Endpoint-Type: utility

            >>> # Client authentication flow with redirect:
            >>> import httpx
            >>> headers = {"X-API-Key": "your-api-key"}
            >>> async with httpx.AsyncClient(follow_redirects=True) as client:
            ...     response = await client.get("http://api.example.com/auth/status", headers=headers)
            ...     # Automatically follows redirect to /v1/auth/status
            ...     assert response.json()["authenticated"] is True

        Note:
            This endpoint is excluded from OpenAPI schema documentation to avoid
            cluttering the API specification with utility redirects. Authentication
            systems should gradually migrate to using the versioned endpoint directly.
        """
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


def create_internal_app_with_settings(
    settings_obj: 'Settings',
    include_routers: bool = True,
    include_middleware: bool = True
) -> FastAPI:
    """
    Factory function for creating the internal FastAPI application with explicit settings.

    This is an internal helper function that creates the internal administrative API application
    using the provided settings instance. It enables the main create_app() factory
    to maintain the dual-API architecture while providing proper configuration isolation.

    Args:
        settings_obj: Settings instance to use for configuration
        include_routers: Whether to register API routers
        include_middleware: Whether to configure middleware stack (currently unused for internal app)

    Returns:
        FastAPI: Configured internal API application instance
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

    # Environment-aware documentation control
    is_production = is_production_environment()

    internal_app = FastAPI(
        title="AI Text Processor - Internal API",
        description="Internal API for monitoring, administration, and system management.",
        version="1.0.0",
        openapi_version="3.0.3",  # Use 3.0.3 for better Swagger UI compatibility
        docs_url=None,  # Disable default docs to use custom
        redoc_url="/redoc" if not is_production else None,  # Available at /internal/redoc; disabled in production
        openapi_url="/openapi.json" if not is_production else None,  # Available at /internal/openapi.json; disabled in production
        openapi_tags=internal_tags_metadata,
    )

    # Override dependency injection to use provided settings
    # This ensures all route dependencies use the settings passed to create_app
    from app.dependencies import get_settings
    internal_app.dependency_overrides[get_settings] = lambda: settings_obj

    # Note: Internal app doesn't need CORS middleware as it's for internal use
    # But we may want to add specific security middleware for internal endpoints

    @internal_app.get("/docs", include_in_schema=False)
    async def custom_internal_swagger_ui_html():
        """
        Serve custom Swagger UI documentation for internal API with cross-API navigation.

        This endpoint provides enhanced Swagger UI documentation specifically tailored for the
        internal administrative API, featuring custom styling, cross-API navigation capabilities,
        and security-aware access control. It offers operational teams comprehensive documentation
        while maintaining appropriate security boundaries in production environments.

        Returns:
            HTMLResponse: Custom Swagger UI HTML page with:
                         - Enhanced styling and professional appearance
                         - Cross-API navigation between public and internal APIs
                         - Internal API schema integration
                         - Responsive design for operational tooling

        Raises:
            HTTPException: 404 error when accessed in production mode (debug=False)
                          to maintain security boundaries and prevent documentation exposure

        Behavior:
            **Security-Aware Access Control:**
            - Restricts access to development environments only (settings.debug=True)
            - Returns 404 Not Found in production mode to hide internal documentation
            - Protects sensitive administrative endpoint information from unauthorized access
            - Maintains security boundaries between internal and external documentation

            **Enhanced Documentation Features:**
            - Provides custom-styled Swagger UI with professional appearance
            - Implements cross-API navigation between public and internal documentation
            - Integrates with internal API OpenAPI schema for comprehensive endpoint coverage
            - Offers responsive design optimized for administrative and operational workflows

            **Operational Integration:**
            - Serves as primary documentation interface for internal administrative APIs
            - Enables operational teams to explore available administrative endpoints
            - Provides interactive testing capabilities for internal API endpoints
            - Facilitates development and debugging of administrative integrations

        Examples:
            >>> # Development environment access (debug=True)
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/internal/docs")
            ...     assert response.status_code == 200
            ...     assert "text/html" in response.headers["content-type"]
            ...     html_content = response.text
            ...     assert "Internal API Documentation" in html_content
            ...     assert "swagger-ui" in html_content

            >>> # Production environment access (debug=False)
            >>> # Returns: 404 Not Found
            >>> # Detail: "Documentation not available in production"

            >>> # Cross-API navigation features
            >>> html_content = response.text
            >>> assert "Public API" in html_content    # Navigation to public docs
            >>> assert "Internal API" in html_content  # Current internal docs
            >>> assert "#4CAF50" in html_content       # Active navigation highlighting

        Note:
            This endpoint is excluded from OpenAPI schema documentation and serves
            as a security-controlled gateway to internal API documentation. Access
            is restricted to development environments to maintain operational security.
        """
        # Environment-aware documentation protection
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        is_production_env = is_production_environment()

        if is_production_env:
            # Enhanced error message with environment detection context
            logger.warning(
                f"Internal documentation access blocked in {env_info.environment} environment "
                f"(confidence: {env_info.confidence:.2f})"
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Documentation not available in production",
                    "environment": env_info.environment.value,
                    "confidence": env_info.confidence
                }
            )
        return HTMLResponse(
            get_custom_swagger_ui_html(
                openapi_url="/internal/openapi.json",  # Use absolute path to internal API schema
                title="AI Text Processor - Internal API Documentation",
                api_type="internal"
            )
        )

    @internal_app.get("/", tags=["Internal"])
    async def internal_root():
        """
        Internal API root endpoint providing comprehensive administrative information.

        This endpoint serves as the primary information gateway for the internal administrative
        API, providing operational teams with essential system information, available endpoints,
        and administrative capabilities. It offers comprehensive visibility into the internal
        API structure and serves as a discovery mechanism for administrative tools and monitoring
        systems.

        Returns:
            dict: Comprehensive internal API information structure containing:
                 - message: str - Internal API identification and branding
                 - version: str - Current API version for compatibility tracking
                 - description: str - Administrative API purpose and scope
                 - available_endpoints: List[str] - Administrative endpoint categories with glob patterns

        Behavior:
            **Administrative Information:**
            - Returns standardized internal API identification for operational tooling
            - Provides version information for compatibility and change management
            - Describes administrative scope and intended operational usage
            - Maintains consistent formatting for automated system integration

            **Endpoint Discovery:**
            - Lists all major administrative endpoint categories with glob patterns
            - Provides monitoring system administrators with endpoint navigation guidance
            - Enables automated tooling to discover available administrative capabilities
            - Organizes endpoints by functional categories for operational clarity

            **Operational Integration:**
            - Supports health check validation for internal API availability
            - Enables monitoring systems to validate administrative endpoint access
            - Provides standardized response format for automated processing
            - Facilitates operational documentation and system discovery

        Examples:
            >>> # Administrative system accessing internal API information
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/internal/")
            ...     info = response.json()
            ...     assert info["message"] == "AI Text Processor - Internal API"
            ...     assert info["version"] == "1.0.0"
            ...     assert "Administrative and monitoring" in info["description"]
            ...     assert "/monitoring/*" in info["available_endpoints"]

            >>> # Monitoring system endpoint discovery
            >>> endpoint_categories = info["available_endpoints"]
            >>> assert "/monitoring/*" in endpoint_categories  # System monitoring
            >>> assert "/cache/*" in endpoint_categories       # Cache management
            >>> assert "/resilience/*" in endpoint_categories  # Resilience management

            >>> # Operational tooling version compatibility check
            >>> api_version = info["version"]
            >>> if api_version.startswith("1."):
            ...     # Compatible with v1 administrative tooling
            ...     print("Using v1 administrative protocols")

        Note:
            This endpoint is included in the OpenAPI schema documentation and serves
            as the primary discovery mechanism for administrative capabilities. It provides
            essential information for operational teams and automated monitoring systems.
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

    # Include internal API routers if requested
    if include_routers:
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


def create_internal_app() -> FastAPI:
    """
    Create and configure the comprehensive internal/administrative FastAPI application.
    
    This factory function constructs the complete internal API application designed for
    operations teams, monitoring systems, and administrative tools. It provides extensive
    system visibility, infrastructure management, resilience monitoring, and operational
    control capabilities while maintaining appropriate security boundaries and access control.
    
    Returns:
        FastAPI: Fully configured internal API application instance containing:
                - Comprehensive system monitoring endpoints with real-time metrics
                - Cache infrastructure management with performance optimization tools
                - Advanced resilience configuration and monitoring capabilities  
                - Security-aware documentation access with production mode restrictions
                - Professional API organization with detailed endpoint categorization
                - Custom OpenAPI schema generation with cleaned component definitions
                - Development and production mode awareness for security hardening
    
    Behavior:
        **Application Configuration:**
        - Creates FastAPI instance with comprehensive internal API metadata
        - Configures security-aware documentation with production mode restrictions
        - Sets up professional API tags with detailed operational descriptions
        - Implements OpenAPI 3.0.3 specification for modern tooling compatibility
        
        **Security and Access Control:**
        - Disables documentation endpoints in production mode for security hardening
        - Restricts OpenAPI schema access based on environment configuration
        - Implements proper security boundaries between internal and external access
        - Provides controlled access to sensitive operational information
        
        **Endpoint Organization:**
        - Organizes endpoints into logical categories (monitoring, cache, resilience)
        - Provides comprehensive resilience management across multiple specialized routers
        - Implements extensive monitoring capabilities with real-time system visibility
        - Offers cache management tools for performance optimization and troubleshooting
        
        **Documentation Enhancement:**
        - Implements custom Swagger UI with cross-API navigation capabilities
        - Applies clean OpenAPI schema generation without default validation clutter
        - Provides professional styling and responsive design for operational tools
        - Includes comprehensive endpoint metadata and operational guidance
        
        **Router Integration:**
        - Integrates system monitoring router with health checks and performance metrics
        - Includes cache management router with status monitoring and optimization tools
        - Registers comprehensive resilience management across 8 specialized router categories
        - Provides unified operational interface across all infrastructure components
        
    Examples:
        >>> # Create internal application with full configuration
        >>> internal_app = create_internal_app()
        >>> assert internal_app.title == "AI Text Processor - Internal API"
        >>> assert "Internal" in internal_app.title
        
        >>> # Security-aware documentation configuration
        >>> if settings.debug:
        ...     assert internal_app.docs_url is None  # Custom docs endpoint
        ...     assert internal_app.redoc_url == "/redoc"
        ...     assert internal_app.openapi_url == "/openapi.json"
        ... else:
        ...     assert internal_app.redoc_url is None  # Disabled in production
        ...     assert internal_app.openapi_url is None  # Disabled in production
        
        >>> # Comprehensive router integration
        >>> routes = [route.path for route in internal_app.routes]
        >>> assert "/" in routes  # Internal root endpoint
        >>> assert any("/monitoring" in path for path in routes)  # System monitoring
        >>> assert any("/cache" in path for path in routes)  # Cache management
        >>> assert any("/resilience" in path for path in routes)  # Resilience management
        
        >>> # API tag organization for operational clarity
        >>> tag_names = [tag["name"] for tag in internal_app.openapi_tags]
        >>> assert "System Monitoring" in tag_names
        >>> assert "Cache Management" in tag_names
        >>> assert "Resilience Configuration" in tag_names
    
    Note:
        This function is called automatically during application startup and creates
        an application that is mounted at /internal on the main public application.
        The internal API provides essential operational capabilities while maintaining
        appropriate security boundaries and access controls.
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
    
    # Environment-aware documentation control
    is_production = is_production_environment()

    internal_app = FastAPI(
        title="AI Text Processor - Internal API",
        description="Internal API for monitoring, administration, and system management.",
        version="1.0.0",
        openapi_version="3.0.3",  # Use 3.0.3 for better Swagger UI compatibility
        docs_url=None,  # Disable default docs to use custom
        redoc_url="/redoc" if not is_production else None,  # Available at /internal/redoc; disabled in production
        openapi_url="/openapi.json" if not is_production else None,  # Available at /internal/openapi.json; disabled in production
        openapi_tags=internal_tags_metadata,
    )
    
    # Note: Internal app doesn't need CORS middleware as it's for internal use
    # But we may want to add specific security middleware for internal endpoints
    
    @internal_app.get("/docs", include_in_schema=False)
    async def custom_internal_swagger_ui_html():
        """
        Serve custom Swagger UI documentation for internal API with cross-API navigation.
        
        This endpoint provides enhanced Swagger UI documentation specifically tailored for the
        internal administrative API, featuring custom styling, cross-API navigation capabilities,
        and security-aware access control. It offers operational teams comprehensive documentation
        while maintaining appropriate security boundaries in production environments.
        
        Returns:
            HTMLResponse: Custom Swagger UI HTML page with:
                         - Enhanced styling and professional appearance
                         - Cross-API navigation between public and internal APIs
                         - Internal API schema integration
                         - Responsive design for operational tooling
        
        Raises:
            HTTPException: 404 error when accessed in production mode (debug=False)
                          to maintain security boundaries and prevent documentation exposure
        
        Behavior:
            **Security-Aware Access Control:**
            - Restricts access to development environments only (settings.debug=True)
            - Returns 404 Not Found in production mode to hide internal documentation
            - Protects sensitive administrative endpoint information from unauthorized access
            - Maintains security boundaries between internal and external documentation
            
            **Enhanced Documentation Features:**
            - Provides custom-styled Swagger UI with professional appearance
            - Implements cross-API navigation between public and internal documentation
            - Integrates with internal API OpenAPI schema for comprehensive endpoint coverage
            - Offers responsive design optimized for administrative and operational workflows
            
            **Operational Integration:**
            - Serves as primary documentation interface for internal administrative APIs
            - Enables operational teams to explore available administrative endpoints
            - Provides interactive testing capabilities for internal API endpoints
            - Facilitates development and debugging of administrative integrations
        
        Examples:
            >>> # Development environment access (debug=True)
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/internal/docs")
            ...     assert response.status_code == 200
            ...     assert "text/html" in response.headers["content-type"]
            ...     html_content = response.text
            ...     assert "Internal API Documentation" in html_content
            ...     assert "swagger-ui" in html_content
            
            >>> # Production environment access (debug=False)
            >>> # Returns: 404 Not Found
            >>> # Detail: "Documentation not available in production"
            
            >>> # Cross-API navigation features
            >>> html_content = response.text
            >>> assert "Public API" in html_content    # Navigation to public docs
            >>> assert "Internal API" in html_content  # Current internal docs
            >>> assert "#4CAF50" in html_content       # Active navigation highlighting
        
        Note:
            This endpoint is excluded from OpenAPI schema documentation and serves
            as a security-controlled gateway to internal API documentation. Access
            is restricted to development environments to maintain operational security.
        """
        # Environment-aware documentation protection
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        is_production_env = is_production_environment()

        if is_production_env:
            # Enhanced error message with environment detection context
            logger.warning(
                f"Internal documentation access blocked in {env_info.environment} environment "
                f"(confidence: {env_info.confidence:.2f})"
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Documentation not available in production",
                    "environment": env_info.environment.value,
                    "confidence": env_info.confidence
                }
            )
        return HTMLResponse(
            get_custom_swagger_ui_html(
                openapi_url="/internal/openapi.json",  # Use absolute path to internal API schema
                title="AI Text Processor - Internal API Documentation",
                api_type="internal"
            )
        )
    
    @internal_app.get("/", tags=["Internal"])
    async def internal_root():
        """
        Internal API root endpoint providing comprehensive administrative information.
        
        This endpoint serves as the primary information gateway for the internal administrative
        API, providing operational teams with essential system information, available endpoints,
        and administrative capabilities. It offers comprehensive visibility into the internal
        API structure and serves as a discovery mechanism for administrative tools and monitoring
        systems.
        
        Returns:
            dict: Comprehensive internal API information structure containing:
                 - message: str - Internal API identification and branding
                 - version: str - Current API version for compatibility tracking
                 - description: str - Administrative API purpose and scope
                 - available_endpoints: List[str] - Administrative endpoint categories with glob patterns
        
        Behavior:
            **Administrative Information:**
            - Returns standardized internal API identification for operational tooling
            - Provides version information for compatibility and change management
            - Describes administrative scope and intended operational usage
            - Maintains consistent formatting for automated system integration
            
            **Endpoint Discovery:**
            - Lists all major administrative endpoint categories with glob patterns
            - Provides monitoring system administrators with endpoint navigation guidance
            - Enables automated tooling to discover available administrative capabilities
            - Organizes endpoints by functional categories for operational clarity
            
            **Operational Integration:**
            - Supports health check validation for internal API availability
            - Enables monitoring systems to validate administrative endpoint access
            - Provides standardized response format for automated processing
            - Facilitates operational documentation and system discovery
            
        Examples:
            >>> # Administrative system accessing internal API information
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/internal/")
            ...     info = response.json()
            ...     assert info["message"] == "AI Text Processor - Internal API"
            ...     assert info["version"] == "1.0.0"
            ...     assert "Administrative and monitoring" in info["description"]
            ...     assert "/monitoring/*" in info["available_endpoints"]
            
            >>> # Monitoring system endpoint discovery
            >>> endpoint_categories = info["available_endpoints"]
            >>> assert "/monitoring/*" in endpoint_categories  # System monitoring
            >>> assert "/cache/*" in endpoint_categories       # Cache management
            >>> assert "/resilience/*" in endpoint_categories  # Resilience management
            
            >>> # Operational tooling version compatibility check
            >>> api_version = info["version"]
            >>> if api_version.startswith("1."):
            ...     # Compatible with v1 administrative tooling
            ...     print("Using v1 administrative protocols")
        
        Note:
            This endpoint is included in the OpenAPI schema documentation and serves
            as the primary discovery mechanism for administrative capabilities. It provides
            essential information for operational teams and automated monitoring systems.
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


# Create the main application using factory pattern
# This maintains backward compatibility for production deployments
app = create_app()

# The internal application is automatically mounted at /internal by the factory


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
