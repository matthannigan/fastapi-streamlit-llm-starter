---
sidebar_label: config
---

# Core Application Configuration

  file_path: `backend/app/core/config.py`

This module provides centralized configuration management for the FastAPI backend application.
All application settings are consolidated here with comprehensive preset-based configuration,
validation, and environment variable support.

## Classes

**Settings**: Main configuration class that provides preset-based configuration management,
environment variable validation, and methods for accessing resilience and cache configurations.

## Module Variables

**settings**: Global Settings instance for dependency injection throughout the application.

## Architecture Overview

The configuration system uses a **preset-based architecture** that dramatically simplifies
setup and maintenance by reducing complex environment variable configurations to simple
preset selections with optional overrides.

### Core Design Principles
- **Preset-First**: Choose configuration presets instead of managing dozens of variables
- **Override Capable**: Environment variables and JSON overrides for customization
- **Backward Compatible**: Legacy environment variable support for smooth migration
- **Validation-First**: Comprehensive Pydantic validation with clear error messages
- **Observable Behavior**: Configuration loading behavior is logged and monitorable

## Configuration Domains

### AI Configuration
- Google Gemini API integration with model selection
- Temperature control and batch processing limits
- Concurrent request management for optimal performance

### Cache Configuration (Preset-Based)
- **Available Presets**: disabled, simple, development, production, ai-development, ai-production
- **Override Support**: CACHE_REDIS_URL, ENABLE_AI_CACHE environment variables
- **Custom Configuration**: CACHE_CUSTOM_CONFIG for advanced JSON-based customization
- **Fallback Strategy**: Automatic fallback from Redis to in-memory caching

### Resilience Configuration (Preset-Based)
- **Available Presets**: simple, development, production
- **Legacy Support**: Automatic detection and migration from individual variables
- **Operation-Specific**: Different resilience strategies per AI operation type
- **Custom Overrides**: RESILIENCE_CUSTOM_CONFIG for fine-tuning

### Security & Authentication
- Multi-API key support with primary and additional keys
- CORS origin management with environment-specific defaults
- Request size limits and validation rules

### Health Check Configuration
- Component-specific timeout configuration (AI, cache, resilience)
- Configurable retry logic with performance optimization
- Selective component enabling for different deployment scenarios

## Environment Variable Examples

### Modern Preset Approach (Recommended)
```bash
# Cache configuration - single preset replaces 28+ individual variables
CACHE_PRESET=production
CACHE_REDIS_URL=redis://production-redis:6379  # Optional override
ENABLE_AI_CACHE=true                           # Optional override

# Resilience configuration - single preset replaces 47+ individual variables
RESILIENCE_PRESET=production
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 5, "circuit_breaker_threshold": 10}'

# Health checks
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience"]
```

### Advanced Customization
```bash
# Custom cache configuration with JSON overrides
CACHE_PRESET=development
CACHE_CUSTOM_CONFIG='{
"default_ttl": 7200,
"compression_threshold": 500,
"text_size_tiers": {"small": 300, "medium": 3000, "large": 30000}
}'
```

## Usage Patterns

### Basic Configuration Access
```python
from app.core.config import settings

# AI configuration
api_key = settings.gemini_api_key
model = settings.ai_model
temperature = settings.ai_temperature

# Preset-based configurations
resilience_config = settings.get_resilience_config()
cache_config = settings.get_cache_config()
```

### Advanced Configuration with Error Handling
```python
from app.core.config import settings
from app.core.exceptions import ConfigurationError

try:
# Load cache configuration with session tracking
cache_config = settings.get_cache_config(
session_id="user_123",
user_context="production_deployment"
)

# Validate custom configuration
validation_result = settings.validate_custom_config(custom_json)
if not validation_result["is_valid"]:
logger.error(f"Configuration errors: {validation_result['errors']}")

except ConfigurationError as e:
# Handle configuration validation failures
logger.error(f"Configuration error: {e}")
# Fallback to default configuration
```

### Environment-Specific Setup
```python
# Development environment
os.environ['CACHE_PRESET'] = 'development'
os.environ['RESILIENCE_PRESET'] = 'development'

# Production environment
os.environ['CACHE_PRESET'] = 'production'
os.environ['RESILIENCE_PRESET'] = 'production'
os.environ['CACHE_REDIS_URL'] = 'redis://prod-cluster:6379'
```

## Behavior and Guarantees

### Configuration Loading Behavior
- Settings instance is immutable once created (Pydantic BaseSettings behavior)
- Environment variables are loaded from .env file in non-test environments
- Test environments use explicit configuration to prevent ambient variable interference
- Configuration validation occurs at startup with clear error reporting

### Preset Resolution Behavior
- Cache presets resolve configuration precedence: Custom JSON > Environment Variables > Preset Defaults
- Resilience presets auto-detect legacy environment variables for backward compatibility
- Invalid preset names raise ConfigurationError with available preset suggestions
- Fallback presets are automatically applied when primary preset loading fails

### Validation and Error Handling
- All environment variables undergo Pydantic type validation and constraint checking
- Invalid values trigger graceful fallback with warning logs (environment variables) or strict errors (direct API calls)
- Custom JSON configurations are validated against schema before application
- Configuration errors include contextual information for debugging

### Thread Safety and Performance
- Settings instance provides thread-safe read access to all configuration values
- Configuration loading is performed once at startup, not on each access
- Preset resolution includes performance monitoring and metrics collection
- Memory usage remains constant regardless of configuration complexity

## Note

This module represents a critical infrastructure component. All configuration changes
should undergo thorough testing across different environment scenarios to ensure
backward compatibility and proper fallback behavior.
