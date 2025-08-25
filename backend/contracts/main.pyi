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
from app.api.internal.resilience import resilience_config_presets_router, resilience_config_templates_router, resilience_config_validation_router, resilience_circuit_breakers_router, resilience_health_router, resilience_config_router, resilience_monitoring_router, resilience_performance_router


def get_custom_swagger_ui_html(openapi_url: str, title: str, api_type: str = 'public') -> str:
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
    ...


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
    ...


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
    ...


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
    ...


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
    ...
