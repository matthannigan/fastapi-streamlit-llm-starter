# Core Application Package

This package contains the foundational components of the FastAPI backend application,
providing centralized configuration management, exception handling, and middleware
infrastructure that serves as the backbone for the entire application.

## Package Contents

### Configuration Management (`config.py`)
- **Settings**: Main configuration class with environment variable support
- **Resilience Configuration**: Comprehensive circuit breaker and retry logic configuration
- **AI Integration**: Gemini API configuration and batch processing settings
- **Cache Configuration**: Redis, compression, and tiering settings
- **Authentication & CORS**: Security and cross-origin settings

### Exception Hierarchy (`exceptions.py`)
- **ApplicationError**: Base for business logic and validation errors
- **InfrastructureError**: Base for external system and service errors
- **AI Service Exceptions**: Comprehensive AI service error classification
- **Utility Functions**: Exception classification and HTTP status mapping

### Middleware Infrastructure (`middleware.py`)
- **CORS Middleware**: Cross-origin resource sharing configuration
- **Security Middleware**: Security headers and request validation
- **Request Logging**: HTTP request/response logging with performance metrics
- **Performance Monitoring**: Resource usage tracking and slow request detection
- **Global Exception Handling**: Centralized error handling and response formatting

## Architecture

The core package follows a layered architecture supporting both infrastructure
and domain services:

- **Infrastructure Services**: Business-agnostic, reusable technical capabilities
- **Domain Services**: Business-specific implementations and examples
- **Configuration Layer**: Centralized settings management with validation
- **Error Handling**: Comprehensive exception hierarchy with retry classification

## Usage

Import core components from this package for consistent application behavior:

```python
from app.core import settings, ApplicationError
from app.core.middleware import setup_middleware
from app.core.exceptions import classify_ai_exception
```

## Key Features

- **Environment Variable Support**: Automatic .env file loading and validation
- **Resilience Patterns**: Circuit breakers, retry logic, and graceful degradation
- **Security by Default**: Production-ready security headers and CORS configuration
- **Monitoring Integration**: Request tracking, performance metrics, and health checks
- **Error Consistency**: Standardized error responses across all application components
