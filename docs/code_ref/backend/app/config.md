# Backend application configuration settings.

This module provides centralized configuration management for the FastAPI backend application,
including AI service settings, resilience configurations, caching options, and security settings.

## Classes

Settings: Main configuration class that handles environment variables, validation,
and provides methods for resilience configuration management.

## Module Variables

settings: Global Settings instance for dependency injection throughout the application.

## Features

- Environment variable support with .env file loading
- Pydantic-based validation and type checking
- AI model configuration (Gemini, temperature, batch processing)
- Authentication and CORS settings
- Redis caching configuration with compression and tiering
- Comprehensive resilience configuration with preset and legacy support
- Circuit breaker and retry mechanism settings
- Operation-specific resilience strategy configuration
- Configuration monitoring and metrics collection

## Configuration Sources

- Environment variables from .env file in project root
- Resilience presets (simple, development, production)
- Custom JSON configuration overrides
- Legacy environment variable support for backward compatibility

## Example

Basic usage for accessing configuration:
```python
from app.core.config import settings

# Access AI configuration
api_key = settings.gemini_api_key
model = settings.ai_model

# Get resilience configuration
resilience_config = settings.get_resilience_config()

# Check operation strategy
strategy = settings.get_operation_strategy("summarize")
```

## Note

The Settings class automatically loads configuration from environment variables
and provides extensive validation. Legacy resilience configuration is supported
for backward compatibility when legacy environment variables are detected.
