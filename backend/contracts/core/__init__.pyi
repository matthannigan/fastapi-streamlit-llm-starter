"""
Core Application Package

This package contains the foundational components of the FastAPI backend application,
providing centralized configuration management, comprehensive exception handling, and
middleware infrastructure that serves as the architectural backbone for the entire
application ecosystem.

## Package Architecture

The core package follows a layered foundation architecture that supports both
infrastructure and domain services:

### Foundation Layer
- **Configuration Management**: Centralized, validated, type-safe settings
- **Exception Hierarchy**: Comprehensive error classification and handling
- **Middleware Stack**: Request/response processing pipeline

### Integration Layer  
- **Infrastructure Integration**: Seamless integration with cache, resilience, AI, security
- **Domain Service Support**: Foundation for business logic implementation
- **Cross-Cutting Concerns**: Logging, monitoring, performance tracking

## Package Components

### Configuration Management (`config.py`)
Comprehensive configuration system with environment variable support:
- **Settings Class**: Main configuration class with Pydantic validation
- **Resilience Configuration**: Circuit breaker, retry, and strategy management
- **AI Integration**: Google Gemini API configuration and batch processing
- **Cache Configuration**: Redis, compression, and performance tuning
- **Authentication & CORS**: Security, multi-key auth, and cross-origin settings
- **Health Check Configuration**: Component-specific timeouts and retry logic
- **Environment Support**: Development, testing, and production configurations

### Exception Hierarchy (`exceptions.py`)
Sophisticated exception classification system for error handling:
- **ApplicationError Hierarchy**: Business logic, validation, and authentication errors
- **InfrastructureError Hierarchy**: External system, network, and service errors  
- **AI Service Exceptions**: Comprehensive AI service error classification with retry logic
- **Classification Utilities**: Intelligent exception classification for resilience patterns
- **HTTP Status Mapping**: Consistent HTTP status code mapping for API responses

### Middleware Infrastructure (`middleware/`)
Production-ready middleware stack for request/response processing:
- **Security Middleware**: Security headers, CORS, and request validation
- **Performance Monitoring**: Resource tracking, slow request detection, and metrics
- **Request Logging**: Comprehensive HTTP request/response logging with correlation IDs
- **Global Exception Handling**: Centralized error handling and structured error responses
- **Rate Limiting**: Request rate limiting and abuse protection
- **Compression**: Response compression for improved performance
- **API Versioning**: Version management and backward compatibility

## Integration Patterns

### Infrastructure Service Integration
```python
from app.core import settings
from app.core.exceptions import ValidationError, classify_ai_exception
from app.infrastructure.cache import get_cache_service
from app.infrastructure.resilience import with_operation_resilience

# Configuration-driven service initialization
cache = get_cache_service()
resilience_config = settings.get_resilience_config()

# Exception-driven error handling
try:
    result = await ai_operation()
except Exception as e:
    if classify_ai_exception(e):
        # Apply retry logic
        pass
    else:
        raise ValidationError("Permanent failure") from e
```

### Domain Service Integration
```python
from app.core import settings, ApplicationError
from app.core.middleware import setup_middleware

# Domain service with core configuration
class TextProcessor:
    def __init__(self):
        self.ai_model = settings.ai_model
        self.temperature = settings.ai_temperature
    
    async def process(self, text: str):
        if not text.strip():
            raise ValidationError("Text cannot be empty")
        # Processing logic here
```

### Middleware Integration
```python
from fastapi import FastAPI
from app.core.middleware import (
    setup_cors_middleware,
    setup_security_middleware,
    setup_logging_middleware
)

app = FastAPI()

# Apply core middleware stack
setup_cors_middleware(app, settings.allowed_origins)
setup_security_middleware(app)
setup_logging_middleware(app)
```

## Configuration Architecture

### Environment-Based Configuration
- **Development**: Debug mode, relaxed security, enhanced logging
- **Testing**: Isolated configuration, mock services, fast execution
- **Production**: Security hardening, performance optimization, monitoring

### Preset-Based Resilience
- **Simple**: Basic retry and circuit breaker settings
- **Development**: Fast feedback, aggressive timeouts
- **Production**: Conservative retry, extended recovery times

### Legacy Compatibility
- **Backward Compatible**: Supports legacy environment variables
- **Migration Path**: Gradual migration to modern preset system
- **Validation**: Comprehensive validation with helpful error messages

## Design Principles

### Stability & Reliability
- **Immutable Configuration**: Thread-safe, validated configuration access
- **Comprehensive Error Handling**: Structured exception hierarchy with retry classification
- **Graceful Degradation**: Fallback behaviors for missing or invalid configuration

### Performance & Efficiency
- **Lazy Loading**: Configuration loaded once and cached
- **Efficient Middleware**: Minimal overhead middleware with async-first design
- **Resource Management**: Proper resource cleanup and memory management

### Security & Compliance
- **Secure Defaults**: Production-ready security configuration out of the box
- **Multi-Key Authentication**: Flexible authentication with key rotation support
- **Audit Logging**: Comprehensive audit trails for security and compliance

### Developer Experience
- **Type Safety**: Full type hints and Pydantic validation
- **Clear Error Messages**: Helpful error messages with debugging context
- **Comprehensive Documentation**: Extensive examples and usage patterns

## Usage Patterns

### Basic Core Usage
```python
from app.core import settings, ApplicationError, ValidationError

# Configuration access
api_key = settings.gemini_api_key
debug_mode = settings.debug

# Exception handling
try:
    validate_input(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
```

### Advanced Configuration
```python
from app.core.config import settings
import json

# Custom resilience configuration
custom_config = {
    "retry_attempts": 5,
    "circuit_breaker_threshold": 10,
    "timeout_seconds": 30
}
settings.RESILIENCE_CUSTOM_CONFIG = json.dumps(custom_config)

# Get computed configuration
resilience_config = settings.get_resilience_config()
operation_strategy = settings.get_operation_strategy("summarize")
```

### Exception Classification
```python
from app.core.exceptions import classify_ai_exception, get_http_status_for_exception

try:
    await risky_ai_operation()
except Exception as e:
    if classify_ai_exception(e):
        # Retry logic
        await retry_operation()
    else:
        # Handle permanent failure
        status_code = get_http_status_for_exception(e)
        return error_response(status_code, str(e))
```
"""

from .config import settings, Settings
from .exceptions import ApplicationError, ValidationError, AuthenticationError, AuthorizationError, ConfigurationError, BusinessLogicError, InfrastructureError, AIServiceException, TransientAIError, PermanentAIError, RateLimitError, ServiceUnavailableError, classify_ai_exception, get_http_status_for_exception
