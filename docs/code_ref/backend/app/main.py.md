---
sidebar_label: main
---

# Main FastAPI application for AI Text Processing with comprehensive resilience features.

  file_path: `backend/app/main.py`

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
