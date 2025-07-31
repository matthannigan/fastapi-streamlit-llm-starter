---
sidebar_label: config
---

# Core Application Configuration

  file_path: `backend/app/core/config.py`

This module provides centralized configuration management for the FastAPI backend application.
All application settings are consolidated here with proper organization and validation.

## Classes

**Settings**: Main configuration class that handles environment variables, validation,
and provides methods for resilience configuration management.

## Module Variables

**settings**: Global Settings instance for dependency injection throughout the application.

## Features

- Environment variable support with .env file loading
- Pydantic-based validation and type checking
- Organized configuration sections for maintainability
- AI model configuration with batch processing support
- Authentication and CORS settings
- Redis caching configuration with compression and tiering
- Comprehensive resilience configuration with preset and legacy support
- Configuration monitoring and metrics collection

## Configuration Sources

- Environment variables from .env file in project root
- Resilience presets (simple, development, production)
- Custom JSON configuration overrides
- Legacy environment variable support for backward compatibility

## Usage

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

## Configuration Architecture

The Settings class provides comprehensive configuration management with:

### AI Configuration
- Google Gemini API integration
- Model selection and temperature control
- Batch processing limits and concurrency control

### Resilience Configuration
- **Preset System**: Simple, development, and production presets
- **Legacy Support**: Backward compatibility with individual environment variables
- **Custom Overrides**: JSON-based configuration customization
- **Operation Strategies**: Per-operation resilience strategy configuration

### Cache Configuration
- Redis connection and clustering support
- Compression settings with configurable thresholds
- Text size tiering for optimal performance
- Memory cache integration for small texts

### Security Configuration
- API key management with multi-key support
- CORS origins with production-ready defaults
- Request validation and size limits

## Environment Variables

The configuration system supports both modern preset-based configuration and
legacy individual environment variables for backward compatibility:

```bash
# Modern preset approach (recommended)
RESILIENCE_PRESET=production
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 5}'

# Legacy individual variables (supported for compatibility)
RETRY_MAX_ATTEMPTS=3
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
```

## Validation and Error Handling

- Comprehensive field validation using Pydantic validators
- Graceful fallback for invalid values with warning logs
- Strict validation for direct API usage
- Configuration error classification and reporting

## Note

The Settings class automatically loads configuration from environment variables
and provides extensive validation. Legacy resilience configuration is supported
for backward compatibility when legacy environment variables are detected.
