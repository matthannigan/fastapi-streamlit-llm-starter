"""
Core Application Configuration

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

Note:
    This module represents a critical infrastructure component. All configuration changes
    should undergo thorough testing across different environment scenarios to ensure
    backward compatibility and proper fallback behavior.
"""

import os
import sys
import json
import logging
from typing import List, Optional, Union
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from app.core.exceptions import ConfigurationError

# Load .env from project root, but avoid loading during pytest to prevent
# ambient env from overriding test instance settings
project_root = Path(__file__).parent.parent.parent.parent
# Detect pytest robustly at import time
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))
if not _IS_PYTEST:
    load_dotenv(project_root / ".env")
else:
    # During pytest, prevent ambient env from overriding test instance settings
    # for preset/custom config keys. Other env vars remain available for
    # legacy-focused tests that intentionally set them.
    os.environ.pop("RESILIENCE_PRESET", None)
    os.environ.pop("RESILIENCE_CUSTOM_CONFIG", None)

logger = logging.getLogger(__name__)


# ========================================
# JUMP TO A SPECIFIC CONFIGURATION SECTION
# ========================================
# 
#                           Approx Line #
# AI Configuration                    352
# API Configuration                   383
# Application Settings                398
# Authentication & CORS               411
# Cache Configuration                 429
# Health Check Configuration          465
# Middleware Configuration            530
# Monitoring Configuration            631
# Pydantic Configuration              644
# Resilience Configuration            713
#
# Field Validators                    821
#
# Main Public Interface Methods      1117
# Authentication & Utility Methods   1590
# Internal Configuration Processing  1698
# Backward Compatibility Methods     1984
#
# ========================================

class Settings(BaseSettings):
    """
    Centralized application configuration class with comprehensive preset-based configuration management.
    
    This class serves as the single source of truth for all application configuration,
    providing organized, validated, and type-safe access to environment-specific settings.
    It implements a preset-based architecture that dramatically simplifies configuration
    management while maintaining full customization capabilities.
    
    Attributes:
        gemini_api_key: Google Gemini API key for AI service integration
        ai_model: Default AI model identifier for processing requests (default: "gemini-2.0-flash-exp")
        ai_temperature: AI model temperature for creativity control (0.0-2.0, default: 0.7)
        MAX_BATCH_REQUESTS_PER_CALL: Maximum batch size for concurrent processing (default: 50)
        BATCH_AI_CONCURRENCY_LIMIT: Concurrent AI request limit in batch operations (default: 5)
        host: Server host address for binding (default: "0.0.0.0")
        port: Server port number for binding (1-65535, default: 8000)
        api_key: Primary API key for authentication
        additional_api_keys: Comma-separated additional API keys for multi-client access
        allowed_origins: List of allowed CORS origins for cross-origin requests
        debug: Debug mode flag for development environments (default: False)
        log_level: Application logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: "INFO")
        cache_preset: Cache configuration preset selection - disabled, simple, development, production, ai-development, ai-production (default: "development")
        cache_custom_config: Custom JSON configuration for advanced cache settings (optional)
        resilience_preset: Resilience configuration preset - simple, development, production (default: "simple")
        resilience_custom_config: Custom JSON configuration for advanced resilience settings (optional)
        health_check_timeout_ms: Default timeout for health checks in milliseconds (default: 2000)
        health_check_enabled_components: List of components to include in health checks (default: ["ai_model", "cache", "resilience"])
        
    Public Methods:
        get_cache_config(): Get complete cache configuration from preset with overrides applied
        get_resilience_config(): Get complete resilience configuration from preset with overrides applied
        get_operation_strategy(): Get resilience strategy for specific operation types
        validate_custom_config(): Validate custom JSON configuration strings
        get_valid_api_keys(): Get list of all valid API keys (primary + additional)
        
    State Management:
        - Immutable configuration once loaded (Pydantic BaseSettings behavior)
        - Thread-safe read access to all configuration values
        - Automatic environment variable type conversion and constraint validation
        - Graceful fallback for invalid environment values with warning logs
        - Test environment isolation prevents ambient variable interference
        - Configuration loading is performed once at startup for optimal performance
        
    Behavior:
        - Validates all environment variables against type constraints at startup
        - Applies preset-based configuration with override precedence: Custom JSON > Environment Variables > Preset Defaults
        - Auto-detects legacy resilience environment variables for backward compatibility
        - Logs all configuration loading actions and applied overrides for debugging
        - Raises ConfigurationError for invalid preset names with available preset suggestions
        - Falls back to 'simple' presets when primary preset loading fails
        - Caches configuration resolution results to avoid repeated computation
        - Provides session and user context tracking for monitoring and analytics
        - Maintains configuration consistency across all application components
        
    Usage:
        # Basic preset-based configuration
        from app.core.config import settings
        
        # Direct field access for simple values
        api_key = settings.gemini_api_key
        model = settings.ai_model
        temperature = settings.ai_temperature
        debug_mode = settings.debug
        
        # Preset-based complex configuration
        cache_config = settings.get_cache_config()
        redis_url = cache_config.redis_url
        ttl_settings = cache_config.default_ttl
        
        resilience_config = settings.get_resilience_config()
        retry_attempts = resilience_config.retry_config.max_attempts
        circuit_threshold = resilience_config.circuit_breaker_config.failure_threshold
        
        # Environment-specific setup patterns
        import os
        
        # Development environment
        os.environ['CACHE_PRESET'] = 'development'
        os.environ['RESILIENCE_PRESET'] = 'development'
        
        # Production environment with overrides
        os.environ['CACHE_PRESET'] = 'production'
        os.environ['CACHE_REDIS_URL'] = 'redis://prod-cluster:6379'
        os.environ['RESILIENCE_PRESET'] = 'production'
        
        # Advanced customization with JSON
        custom_cache = {
            "default_ttl": 7200,
            "compression_threshold": 500,
            "enable_ai_cache": True
        }
        os.environ['CACHE_CUSTOM_CONFIG'] = json.dumps(custom_cache)
        
        # Configuration validation
        validation_result = settings.validate_custom_config(custom_json)
        if not validation_result['is_valid']:
            logger.error(f"Configuration errors: {validation_result['errors']}")
        
        # Session-aware configuration loading
        cache_config = settings.get_cache_config(
            session_id="user_123",
            user_context="api_endpoint_processing"
        )
        
        # Authentication helpers
        all_valid_keys = settings.get_valid_api_keys()
        operation_strategy = settings.get_operation_strategy("summarize")
        
        # Health check configuration access
        health_timeouts = {
            "ai_model": settings.health_check_ai_model_timeout_ms,
            "cache": settings.health_check_cache_timeout_ms,
            "resilience": settings.health_check_resilience_timeout_ms
        }
        enabled_components = settings.health_check_enabled_components
        retry_count = settings.health_check_retry_count
        
        # Error handling patterns
        try:
            cache_config = settings.get_cache_config()
        except ConfigurationError as e:
            logger.error(f"Cache configuration failed: {e}")
            # Application should handle fallback or fail gracefully
    """

    # ========================================
    # AI CONFIGURATION
    # ========================================

    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key for AI service integration"
    )
    ai_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Default AI model to use for processing requests"
    )
    ai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="AI model temperature for controlling response creativity"
    )

    # Batch Processing Configuration
    MAX_BATCH_REQUESTS_PER_CALL: int = Field(
        default=50,
        gt=0,
        description="Maximum number of requests allowed per batch call"
    )
    BATCH_AI_CONCURRENCY_LIMIT: int = Field(
        default=5,
        gt=0,
        description="Maximum concurrent AI requests in batch processing"
    )

    # ========================================
    # API CONFIGURATION
    # ========================================

    host: str = Field(
        default="0.0.0.0",
        description="Backend host address for server binding"
    )
    port: int = Field(
        default=8000,
        gt=0,
        le=65535,
        description="Backend port number for server binding"
    )

    # ========================================
    # APPLICATION SETTINGS
    # ========================================

    debug: bool = Field(
        default=False,
        description="Enable debug mode for development"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # ========================================
    # AUTHENTICATION & CORS
    # ========================================

    api_key: str = Field(
        default="",
        description="Primary API key for authentication"
    )
    additional_api_keys: str = Field(
        default="",
        description="Additional API keys (comma-separated) for multi-client access"
    )

    allowed_origins: List[str] = Field(
        default=["http://localhost:8501", "http://frontend:8501"],
        description="Allowed CORS origins for cross-origin requests"
    )

    # ========================================
    # CACHE CONFIGURATION
    # ========================================
    #
    # Cache configuration uses a preset-based system to simplify setup and maintenance.
    # Instead of configuring 28+ individual CACHE_* environment variables, users select
    # a preset that provides optimal settings for their use case.
    #
    # Available Presets:
    # - disabled: Cache completely disabled
    # - simple: Basic caching with minimal features
    # - development: Development-friendly settings with debugging enabled
    # - production: High-performance production settings
    # - ai-development: Development settings optimized for AI operations
    # - ai-production: Production settings optimized for AI operations
    #
    # Configuration Sources (in order of precedence):
    # 1. Custom JSON configuration (CACHE_CUSTOM_CONFIG)
    # 2. Environment variable overrides (CACHE_REDIS_URL, ENABLE_AI_CACHE)
    # 3. Preset defaults (CACHE_PRESET)
    #
    # Usage:
    #   CACHE_PRESET=production
    #   CACHE_REDIS_URL=redis://custom-redis:6379  # Optional override
    #   ENABLE_AI_CACHE=true                       # Optional override

    # Cache Preset System Configuration
    cache_preset: str = Field(
        default="development",
        description="Cache configuration preset (disabled, simple, development, production, ai-development, ai-production)"
    )
    cache_custom_config: Optional[str] = Field(
        default=None,
        description="Custom cache configuration as JSON string (overrides preset)"
    )

    # ========================================
    # HEALTH CHECK CONFIGURATION
    # ========================================
    #
    # Health checks provide real-time monitoring of critical application components.
    # Each component can be individually configured with specific timeouts and retry logic.
    #
    # Supported Components:
    # - ai_model: Tests AI model connectivity and response capability
    # - cache: Validates Redis cache operations and fallback behavior
    # - resilience: Verifies circuit breaker and retry mechanism functionality
    # - database: Database connectivity (if applicable to your implementation)
    #
    # Performance Recommendations:
    # - Development: 1000-2000ms timeouts, 0-1 retries for fast feedback
    # - Production: 2000-5000ms timeouts, 1-2 retries for reliability
    # - Load Testing: Higher timeouts to account for increased latency
    #
    # Component-Specific Considerations:
    # - AI Model: May require longer timeouts due to external API latency
    # - Cache: Should have fast timeouts as Redis operations are typically quick
    # - Resilience: Moderate timeouts to test circuit breaker functionality

    health_check_timeout_ms: int = Field(
        default=2000,
        gt=0,
        description="Default timeout in milliseconds for each health check operation. "
                   "Used when component-specific timeouts are not configured. "
                   "Recommended: 1000ms (development), 2000ms (production), 5000ms (high-latency)"
    )
    health_check_ai_model_timeout_ms: int = Field(
        default=2000,
        gt=0,
        description="Timeout override in milliseconds specifically for AI model health checks. "
                   "AI model checks may require longer timeouts due to external API latency. "
                   "Consider network conditions and API provider response times."
    )
    health_check_cache_timeout_ms: int = Field(
        default=2000,
        gt=0,
        description="Timeout override in milliseconds specifically for cache health checks. "
                   "Cache operations should typically be fast. Lower timeouts help detect issues quickly. "
                   "Redis operations usually complete within 100-500ms under normal conditions."
    )
    health_check_resilience_timeout_ms: int = Field(
        default=2000,
        gt=0,
        description="Timeout override in milliseconds specifically for resilience health checks. "
                   "Tests circuit breaker and retry mechanism functionality. "
                   "Moderate timeout allows comprehensive testing without excessive delays."
    )
    health_check_retry_count: int = Field(
        default=1,
        ge=0,
        description="Number of retry attempts for failing health checks before marking as unhealthy. "
                   "0 = no retries (fail fast), 1-2 = recommended for production, >3 may mask real issues. "
                   "Higher values increase check duration but improve reliability."
    )
    health_check_enabled_components: List[str] = Field(
        default=["ai_model", "cache", "resilience"],
        description="List of components to include in health checks. "
                   "Available: ['ai_model', 'cache', 'resilience', 'database']. "
                   "Disable unused components to improve check performance and reduce false positives."
    )

    # ========================================
    # MIDDLEWARE CONFIGURATION
    # ========================================

    # Core Middleware Settings
    security_headers_enabled: bool = Field(
        default=True,
        description="Enable security headers middleware"
    )
    request_logging_enabled: bool = Field(
        default=True,
        description="Enable request logging middleware"
    )
    performance_monitoring_enabled: bool = Field(
        default=True,
        description="Enable performance monitoring middleware"
    )

    # Rate Limiting Middleware
    rate_limiting_enabled: bool = Field(
        default=True,
        description="Enable rate limiting middleware"
    )
    rate_limiting_skip_health: bool = Field(
        default=True,
        description="Skip rate limiting for health check endpoints"
    )

    # Request Size Limiting Middleware
    request_size_limiting_enabled: bool = Field(
        default=True,
        description="Enable request size limiting middleware"
    )
    max_request_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        gt=0,
        description="Default maximum request size in bytes"
    )

    # API Versioning Middleware
    api_versioning_enabled: bool = Field(
        default=True,
        description="Enable API versioning middleware"
    )
    default_api_version: str = Field(
        default="1.0",
        description="Default API version when none specified"
    )
    current_api_version: str = Field(
        default="1.0",
        description="Current/latest API version"
    )
    min_api_version: str = Field(
        default="1.0",
        description="Minimum supported API version"
    )
    max_api_version: str = Field(
        default="1.0",
        description="Maximum supported API version"
    )
    api_version_compatibility_enabled: bool = Field(
        default=False,
        description="Enable version compatibility transformations"
    )
    version_analytics_enabled: bool = Field(
        default=True,
        description="Enable version analytics and logging"
    )

    # Compression Middleware
    compression_enabled: bool = Field(
        default=True,
        description="Enable compression middleware"
    )
    compression_min_size: int = Field(
        default=1024,  # 1KB
        gt=0,
        description="Minimum response size to compress in bytes"
    )
    compression_level: int = Field(
        default=6,
        ge=1,
        le=9,
        description="Compression level (1-9, higher = better compression but slower)"
    )

    # Performance and Monitoring Settings
    slow_request_threshold: int = Field(
        default=1000,  # milliseconds
        gt=0,
        description="Threshold for slow request warnings in milliseconds"
    )
    memory_monitoring_enabled: bool = Field(
        default=True,
        description="Enable memory usage monitoring"
    )
    middleware_monitoring_enabled: bool = Field(
        default=False,
        description="Enable periodic middleware health monitoring"
    )

    # ========================================
    # MONITORING CONFIGURATION
    # ========================================

    resilience_metrics_enabled: bool = Field(
        default=True,
        description="Enable collection of resilience metrics"
    )
    resilience_health_check_enabled: bool = Field(
        default=True,
        description="Enable resilience health check endpoints"
    )

    # ========================================
    # PYDANTIC CONFIGURATION
    # ========================================

    model_config = SettingsConfigDict(
        env_file=None if _IS_PYTEST else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,  # pydantic-settings v2 passes the settings class here
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):  # type: ignore[override]
        """Customize settings sources to ignore OS env vars during pytest.

        This ensures tests use explicit constructor args and class defaults,
        avoiding leakage from developer machine environment variables like
        RESILIENCE_PRESET.
        
        Implementation Note: This method appears complex due to pydantic-settings
        version compatibility handling and the need to maintain test isolation
        while preserving the ability to test environment variable behavior
        through explicit monkeypatch.setenv() calls in test fixtures.
        
        The complexity handles:
        - Different pydantic-settings version signatures
        - Selective environment variable filtering during tests 
        - Graceful fallbacks for various callable return types
        - Preservation of legacy environment variable mappings needed by tests
        """
        try:
            if 'PYTEST_CURRENT_TEST' in os.environ:
                # In tests, ignore .env files; use init args and OS env vars
                # But filter out preset-specific env so defaults remain deterministic.
                def filtered_env(settings_cls_inner=None):
                    try:
                        data = env_settings(settings_cls)  # type: ignore[call-arg]
                    except Exception:
                        try:
                            data = env_settings()  # type: ignore[misc]
                        except Exception:
                            data = {}
                    if callable(data):
                        try:
                            data = data()
                        except Exception:
                            try:
                                data = data(settings_cls)
                            except Exception:
                                data = {}
                    if isinstance(data, dict):
                        # Remove only these keys; keep legacy env mappings for tests
                        data.pop('resilience_preset', None)
                        data.pop('resilience_custom_config', None)
                    return data
                return (init_settings, filtered_env)
        except Exception:
            pass
        # Normal: use init args, .env, OS env vars, and file secrets (standard order)
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)

    # ========================================
    # RESILIENCE CONFIGURATION
    # ========================================

    # Preset System Configuration
    resilience_preset: str = Field(
        default="simple",
        description="Resilience configuration preset (simple, development, production)"
    )
    resilience_custom_config: Optional[str] = Field(
        default=None,
        description="Custom resilience configuration as JSON string (overrides preset)"
    )

    # Legacy Resilience Configuration (for backward compatibility)
    # These settings are maintained for applications migrating from manual configuration

    # Feature Toggles
    resilience_enabled: bool = Field(
        default=True,
        description="Master toggle for resilience features"
    )
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker pattern for failure protection"
    )
    retry_enabled: bool = Field(
        default=True,
        description="Enable retry mechanism for transient failures"
    )

    # Default Strategy
    default_resilience_strategy: str = Field(
        default="balanced",
        description="Default resilience strategy for operations"
    )

    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        gt=0,
        description="Number of failures before circuit breaker opens"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60,
        gt=0,
        description="Seconds to wait before attempting circuit breaker recovery"
    )

    # Retry Mechanism Settings
    retry_max_attempts: int = Field(
        default=3,
        gt=0,
        description="Maximum number of retry attempts for failed operations"
    )
    retry_max_delay: int = Field(
        default=30,
        gt=0,
        description="Maximum delay between retries in seconds"
    )
    retry_exponential_multiplier: float = Field(
        default=1.0,
        gt=0.0,
        description="Multiplier for exponential backoff calculations"
    )
    retry_exponential_min: float = Field(
        default=2.0,
        gt=0.0,
        description="Minimum delay for exponential backoff in seconds"
    )
    retry_exponential_max: float = Field(
        default=10.0,
        gt=0.0,
        description="Maximum delay for exponential backoff in seconds"
    )
    retry_jitter_enabled: bool = Field(
        default=True,
        description="Enable random jitter to prevent thundering herd"
    )
    retry_jitter_max: float = Field(
        default=2.0,
        gt=0.0,
        description="Maximum jitter value in seconds"
    )

    # Operation-Specific Resilience Strategies
    # These allow fine-tuning resilience behavior per operation type
    summarize_resilience_strategy: str = Field(
        default="balanced",
        description="Resilience strategy for text summarization operations"
    )
    sentiment_resilience_strategy: str = Field(
        default="aggressive",
        description="Resilience strategy for sentiment analysis operations"
    )
    key_points_resilience_strategy: str = Field(
        default="balanced",
        description="Resilience strategy for key points extraction operations"
    )
    questions_resilience_strategy: str = Field(
        default="balanced",
        description="Resilience strategy for question generation operations"
    )
    qa_resilience_strategy: str = Field(
        default="conservative",
        description="Resilience strategy for question answering operations"
    )

    # ========================================
    # FIELD VALIDATORS
    # ========================================

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ConfigurationError(
                f"Invalid log_level: must be one of {', '.join(allowed_levels)}",
                context={
                    "field": "log_level",
                    "provided_value": v,
                    "allowed_values": list(allowed_levels),
                    "validation_context": "pydantic_field_validator"
                }
            )
        return v.upper()

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins format."""
        if not v:
            raise ConfigurationError(
                "At least one allowed origin must be specified",
                context={
                    "field": "allowed_origins",
                    "provided_value": v,
                    "validation_context": "pydantic_field_validator",
                    "requirement": "minimum_one_origin"
                }
            )
        return v

    @field_validator('cache_preset')
    @classmethod
    def validate_cache_preset(cls, v: str) -> str:
        """Validate cache preset name."""
        allowed_presets = {"disabled", "simple", "development", "production", "ai-development", "ai-production"}
        if v not in allowed_presets:
            raise ConfigurationError(
                f"Invalid cache_preset '{v}': must be one of {', '.join(allowed_presets)}",
                context={
                    "field": "cache_preset",
                    "provided_value": v,
                    "allowed_values": list(allowed_presets),
                    "validation_context": "pydantic_field_validator"
                }
            )
        return v

    @field_validator('resilience_preset')
    @classmethod
    def validate_resilience_preset(cls, v: str) -> str:
        """Validate resilience preset name."""
        allowed_presets = {"simple", "development", "production"}
        if v not in allowed_presets:
            raise ConfigurationError(
                f"Invalid resilience_preset '{v}': must be one of {', '.join(allowed_presets)}",
                context={
                    "field": "resilience_preset",
                    "provided_value": v,
                    "allowed_values": list(allowed_presets),
                    "validation_context": "pydantic_field_validator"
                }
            )
        return v

    @field_validator(
        'default_resilience_strategy', 'summarize_resilience_strategy', 'sentiment_resilience_strategy',
        'key_points_resilience_strategy', 'questions_resilience_strategy', 'qa_resilience_strategy',
        mode='before'
    )
    @classmethod
    def validate_resilience_strategy(cls, v, info) -> str:
        """Validate resilience strategy with graceful fallback for environment variables."""
        # Get default values based on field name
        defaults = {
            'default_resilience_strategy': 'balanced',
            'summarize_resilience_strategy': 'balanced',
            'sentiment_resilience_strategy': 'aggressive',
            'key_points_resilience_strategy': 'balanced',
            'questions_resilience_strategy': 'balanced',
            'qa_resilience_strategy': 'conservative'
        }
        default_value = defaults.get(info.field_name, 'balanced')

        # Handle None or empty values
        if v is None or v == "":
            return default_value

        # Convert to string if needed
        if not isinstance(v, str):
            v = str(v)

        allowed_strategies = {"conservative", "balanced", "aggressive"}
        if v not in allowed_strategies:
            # Check if we're in a context where we should be graceful
            strategy_env_vars = {
                'default_resilience_strategy': 'DEFAULT_RESILIENCE_STRATEGY',
                'summarize_resilience_strategy': 'SUMMARIZE_RESILIENCE_STRATEGY',
                'sentiment_resilience_strategy': 'SENTIMENT_RESILIENCE_STRATEGY',
                'key_points_resilience_strategy': 'KEY_POINTS_RESILIENCE_STRATEGY',
                'questions_resilience_strategy': 'QUESTIONS_RESILIENCE_STRATEGY',
                'qa_resilience_strategy': 'QA_RESILIENCE_STRATEGY'
            }

            env_var = strategy_env_vars.get(info.field_name)
            env_value = os.getenv(env_var) if env_var else None

            # If the invalid value matches what's in the environment, be graceful
            if env_value == v:
                logger.warning(
                    f"Invalid resilience strategy '{v}' from environment variable {env_var}, "
                    f"falling back to '{default_value}'"
                )
                return default_value
            else:
                # Value was passed directly - strict validation
                raise ConfigurationError(
                    f"Invalid resilience strategy '{v}': must be one of {', '.join(allowed_strategies)}",
                    context={
                        "field": info.field_name,
                        "provided_value": v,
                        "allowed_values": list(allowed_strategies),
                        "validation_context": "pydantic_field_validator",
                        "validation_mode": "strict"
                    }
                )
        return v

    @field_validator(
        'circuit_breaker_failure_threshold', 'circuit_breaker_recovery_timeout',
        'retry_max_attempts', 'retry_max_delay', mode='before'
    )
    @classmethod
    def validate_positive_integers(cls, v, info) -> int:
        """Validate positive integers with strict validation for completely invalid values."""
        # Get default values based on field name
        defaults = {
            'circuit_breaker_failure_threshold': 5,
            'circuit_breaker_recovery_timeout': 60,
            'retry_max_attempts': 3,
            'retry_max_delay': 30
        }
        default_value = defaults.get(info.field_name, 1)

        # Handle string conversion
        if isinstance(v, str):
            # Empty strings should always fail validation
            if v.strip() == "":
                raise ConfigurationError(
                    f"Invalid empty value for {info.field_name}: must be a positive integer",
                    context={
                        "field": info.field_name,
                        "provided_value": v,
                        "expected_type": "positive_integer",
                        "validation_context": "pydantic_field_validator",
                        "error_type": "empty_string"
                    }
                )

            try:
                v = int(v)
            except (ValueError, TypeError):
                # Check if we're in a context with legacy environment variables
                legacy_vars = [
                    "RETRY_MAX_ATTEMPTS", "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
                    "CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "RETRY_MAX_DELAY"
                ]
                has_any_legacy = any(var in os.environ for var in legacy_vars)

                if has_any_legacy:
                    # Be graceful in legacy mode for non-empty invalid values
                    logger.warning(f"Invalid value for {info.field_name}: '{v}', using default: {default_value}")
                    return default_value
                else:
                    # Strict validation in normal mode
                    raise ConfigurationError(
                        f"Invalid value for {info.field_name}: '{v}' must be a positive integer",
                        context={
                            "field": info.field_name,
                            "provided_value": v,
                            "expected_type": "positive_integer",
                            "validation_context": "pydantic_field_validator",
                            "error_type": "invalid_conversion",
                            "validation_mode": "strict"
                        }
                    )

        # Handle negative/zero values - be graceful for these
        if isinstance(v, (int, float)) and v <= 0:
            logger.warning(f"Invalid value for {info.field_name}: {v}, using default: {default_value}")
            return default_value

        return int(v) if isinstance(v, (int, float)) else default_value

    @field_validator(
        'retry_exponential_multiplier', 'retry_exponential_min',
        'retry_exponential_max', 'retry_jitter_max'
    )
    @classmethod
    def validate_positive_floats(cls, v: float, info) -> float:
        """Validate positive floats with fallback for invalid values."""
        if v <= 0:
            # Get default values based on field name
            defaults = {
                'retry_exponential_multiplier': 1.0,
                'retry_exponential_min': 2.0,
                'retry_exponential_max': 10.0,
                'retry_jitter_max': 2.0
            }
            default_value = defaults.get(info.field_name, 1.0)
            logger.warning(f"Invalid value for {info.field_name}: {v}, using default: {default_value}")
            return default_value
        return v

    # Health Check Configuration Validation
    @field_validator(
        'health_check_timeout_ms', 'health_check_ai_model_timeout_ms',
        'health_check_cache_timeout_ms', 'health_check_resilience_timeout_ms',
        'health_check_retry_count'
    )
    @classmethod
    def validate_health_check_numbers(cls, v: Union[int, float], info) -> int:
        """
        Ensure health check numeric settings are valid, and warn about suboptimal values.
        """
        field_name = info.field_name

        # First, handle type conversion for all numeric fields
        try:
            iv = int(v)
        except (ValueError, TypeError):
            raise ConfigurationError(
                f"{field_name} must be a valid integer",
                context={"field": field_name, "provided_value": v}
            )

        if field_name == 'health_check_retry_count':
            # Validate range (ge=0)
            if iv < 0:
                raise ConfigurationError(
                    "health_check_retry_count must be >= 0",
                    context={"field": field_name, "provided_value": v}
                )
            # Warn about suboptimal settings
            if iv == 0:
                logger.warning(
                    "Configuration Warning: health_check_retry_count is set to 0. "
                    "Failing health checks will not be retried."
                )
            elif iv > 5:
                logger.warning(
                    f"Configuration Warning: health_check_retry_count is set to {iv}. "
                    "A high number of retries may conceal underlying issues."
                )
        else: # Timeouts
            # Validate range (gt=0)
            if iv <= 0:
                raise ConfigurationError(
                    f"{field_name} must be > 0",
                    context={"field": field_name, "provided_value": v}
                )
            # Warn about suboptimal settings
            if iv > 10000:  # Warn if timeout is longer than 10 seconds
                logger.warning(
                    f"Configuration Warning: {field_name} is set to {iv}ms, "
                    "which is a very long timeout and may impact system responsiveness."
                )
        return iv

    @field_validator('health_check_enabled_components')
    @classmethod
    def validate_enabled_health_components(cls, v: List[str]) -> List[str]:
        """
        Checks that all enabled components are valid and warns if none are enabled.
        """
        # Check component configurations
        allowed = {"ai_model", "cache", "resilience", "database"}
        invalid = [name for name in v if name not in allowed]
        if invalid:
            raise ConfigurationError(
                f"Invalid health check components found: {invalid}. "
                f"Allowed components are: {sorted(list(allowed))}",
                context={"field": "health_check_enabled_components", "invalid_components": invalid}
            )
        # Warn about suboptimal settings
        if not v:
            logger.warning("Configuration Warning: No health check components are enabled in health_check_enabled_components.")
        return v


    # ========================================
    # MAIN PUBLIC INTERFACE METHODS
    # ========================================
    #
    # Primary configuration access methods mentioned in the module docstring

    def get_cache_config(self, session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Get complete cache configuration from preset with custom overrides applied.
        
        This is the main entry point for cache configuration that implements the preset-based
        architecture. It automatically resolves configuration from multiple sources with proper
        precedence handling and provides comprehensive error handling with fallback behavior.

        Args:
            session_id: Optional session identifier for monitoring and analytics (default: None)
            user_context: Optional user context string for monitoring and analytics (default: None)

        Returns:
            CacheConfig object containing complete cache configuration with all settings:
            - redis_url: Redis connection URL for cache backend
            - enable_ai_cache: Boolean flag for AI-specific caching features
            - default_ttl: Default time-to-live for cache entries in seconds
            - compression_threshold: Size threshold for enabling compression in bytes
            - text_size_tiers: Dictionary defining size tiers for caching strategies
            - All other cache-specific configuration parameters from the preset
            
        Raises:
            ConfigurationError: When preset loading fails and fallback preset also fails
            
        Behavior:
            - Resolves cache_preset field to load base configuration from preset system
            - Maps 'testing' preset alias to 'development' preset for backward compatibility
            - Applies CACHE_REDIS_URL environment variable override if present
            - Applies ENABLE_AI_CACHE environment variable override if present (true/false/1/0)
            - Applies CACHE_CUSTOM_CONFIG JSON overrides if provided and valid
            - Logs all applied overrides and configuration loading actions
            - Falls back to 'simple' preset if primary preset loading fails
            - Raises ConfigurationError only if both primary and fallback preset loading fails
            - Preserves session and user context for monitoring and analytics
            - Returns identical configuration for identical input parameters (deterministic)
            
        Examples:
            >>> # Basic preset-based configuration
            >>> config = settings.get_cache_config()
            >>> assert config.redis_url == "redis://localhost:6379"  # development preset default
            >>> assert config.enable_ai_cache is True
            
            >>> # Configuration with session tracking
            >>> config = settings.get_cache_config(
            ...     session_id="user_123",
            ...     user_context="api_endpoint_processing"
            ... )
            >>> assert isinstance(config.default_ttl, int)
            
            >>> # Environment override behavior
            >>> import os
            >>> os.environ['CACHE_REDIS_URL'] = 'redis://custom:6379'
            >>> config = settings.get_cache_config()
            >>> assert config.redis_url == "redis://custom:6379"
            
            >>> # Error handling for invalid preset
            >>> settings.cache_preset = "invalid_preset"
            >>> try:
            ...     config = settings.get_cache_config()
            ... except ConfigurationError as e:
            ...     assert "Failed to load cache configuration" in str(e)
        """
        # Import here to avoid circular imports
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        
        try:
            # Load preset configuration
            # Map testing alias to development; leave others as-is
            preset_name = self.cache_preset
            if preset_name == "testing":
                preset_name = "development"
            preset = cache_preset_manager.get_preset(preset_name)
            cache_config = preset.to_cache_config()
            
            logger.info(f"Loaded cache preset '{preset_name}' successfully")
            
            # Apply environment variable overrides if provided
            # These take precedence over preset defaults
            redis_url = os.getenv('CACHE_REDIS_URL')
            if redis_url:
                cache_config.redis_url = redis_url
                logger.info(f"Applied CACHE_REDIS_URL override: {redis_url}")
            
            enable_ai_cache = os.getenv('ENABLE_AI_CACHE', '').lower() in ('true', '1', 'yes')
            if enable_ai_cache and not cache_config.enable_ai_cache:
                cache_config.enable_ai_cache = True
                logger.info("Applied ENABLE_AI_CACHE override: enabled AI features")
            elif not enable_ai_cache and cache_config.enable_ai_cache:
                # If preset enables AI but env var explicitly disables it
                env_disable = os.getenv('ENABLE_AI_CACHE', '').lower() in ('false', '0', 'no')
                if env_disable:
                    cache_config.enable_ai_cache = False
                    logger.info("Applied ENABLE_AI_CACHE override: disabled AI features")
            
            # Apply custom overrides if provided
            custom_config_json = self.cache_custom_config
            if not custom_config_json:
                env_custom_config = os.getenv("CACHE_CUSTOM_CONFIG")
                if env_custom_config:
                    custom_config_json = env_custom_config
            
            if custom_config_json:
                try:
                    custom_config = json.loads(custom_config_json)
                    cache_config = self._apply_cache_custom_overrides(cache_config, custom_config)
                    logger.info(f"Applied custom cache configuration overrides: {list(custom_config.keys())}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in cache_custom_config: {e}")
                    # Continue with preset configuration without custom overrides
            
            return cache_config
            
        except Exception as e:
            logger.error(f"Error loading cache preset '{self.cache_preset}': {e}")
            
            # Fallback to simple preset on error
            logger.warning("Falling back to 'simple' cache preset due to configuration error")
            try:
                fallback_preset = cache_preset_manager.get_preset("simple")
                return fallback_preset.to_cache_config()
            except Exception as fallback_error:
                logger.error(f"Fallback cache configuration also failed: {fallback_error}")
                raise ConfigurationError(
                    f"Failed to load cache configuration and fallback failed: {str(e)}",
                    context={
                        "original_error": str(e),
                        "fallback_error": str(fallback_error),
                        "cache_preset": self.cache_preset
                    }
                )

    def get_resilience_config(self, session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Get complete resilience configuration from preset or legacy settings with monitoring.
        
        This is the main entry point for resilience configuration that implements both
        preset-based architecture and legacy environment variable compatibility. It
        automatically detects the appropriate configuration source and provides
        comprehensive monitoring and error handling with fallback behavior.

        Args:
            session_id: Optional session identifier for monitoring and analytics (default: None)
            user_context: Optional user context string for monitoring and analytics (default: None)

        Returns:
            ResilienceConfig object containing complete resilience configuration:
            - strategy: ResilienceStrategy enum value (CONSERVATIVE, BALANCED, AGGRESSIVE, CRITICAL)
            - retry_config: RetryConfig with max_attempts, delays, exponential backoff settings
            - circuit_breaker_config: CircuitBreakerConfig with failure thresholds and recovery timeouts
            - enable_circuit_breaker: Boolean flag for circuit breaker pattern activation
            - enable_retry: Boolean flag for retry mechanism activation
            
        Raises:
            ConfigurationError: When both primary preset loading and fallback preset loading fail
            
        Behavior:
            - Auto-detects legacy environment variables and prioritizes them for backward compatibility
            - Resolves resilience_preset field to load base configuration from preset system
            - Applies resilience_custom_config JSON overrides if provided and valid
            - Falls back to 'simple' preset if primary preset loading fails
            - Logs all configuration resolution steps and applied overrides for debugging
            - Records preset usage metrics and monitoring data for analytics
            - Ignores custom config in legacy mode to maintain strict backward compatibility
            - Provides session and user context tracking for operational monitoring
            - Returns identical configuration for identical parameters and environment state
            - Caches legacy environment variable detection to avoid repeated filesystem checks
            
        Examples:
            >>> # Basic preset-based configuration
            >>> config = settings.get_resilience_config()
            >>> assert config.strategy.name in ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"]
            >>> assert config.retry_config.max_attempts > 0
            
            >>> # Configuration with session tracking
            >>> config = settings.get_resilience_config(
            ...     session_id="api_request_123",
            ...     user_context="text_processing_endpoint"
            ... )
            >>> assert config.circuit_breaker_config.failure_threshold > 0
            
            >>> # Legacy environment variable mode
            >>> import os
            >>> os.environ['RETRY_MAX_ATTEMPTS'] = '5'
            >>> os.environ['CIRCUIT_BREAKER_FAILURE_THRESHOLD'] = '10'
            >>> config = settings.get_resilience_config()
            >>> assert config.retry_config.max_attempts == 5
            >>> assert config.circuit_breaker_config.failure_threshold == 10
            
            >>> # Custom JSON configuration mode
            >>> settings.resilience_custom_config = '{"retry_attempts": 7, "circuit_breaker_threshold": 15}'
            >>> config = settings.get_resilience_config()
            >>> assert config.retry_config.max_attempts == 7
            >>> assert config.circuit_breaker_config.failure_threshold == 15
        """
        # Import here to avoid circular imports
        from app.infrastructure.resilience import preset_manager
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector

        # Determine configuration type for monitoring
        config_type = "legacy" if self._has_legacy_resilience_config() else "preset"
        if self.resilience_custom_config:
            config_type = "custom"

        # Track configuration loading with monitoring
        with config_metrics_collector.track_config_operation(
            operation="load_config",
            preset_name=self.resilience_preset,
            session_id=session_id,
            user_context=user_context
        ):
            # Clear cache and check if using legacy configuration
            self._clear_legacy_config_cache()
            if self._has_legacy_resilience_config():
                config_metrics_collector.record_preset_usage(
                    preset_name="legacy",
                    operation="load_legacy_config",
                    session_id=session_id,
                    user_context=user_context,
                    metadata={"config_type": "legacy"}
                )
                resilience_config = self._load_legacy_resilience_config()

                # In legacy mode, environment variables take highest priority
                if self.resilience_custom_config:
                    logger.info(
                        "Legacy environment variables detected - custom config will be ignored "
                        "to maintain backward compatibility"
                    )

                    config_metrics_collector.record_preset_usage(
                        preset_name="legacy",
                        operation="ignore_custom_config",
                        session_id=session_id,
                        user_context=user_context,
                        metadata={
                            "config_type": "legacy_only",
                            "reason": "legacy_environment_variables_take_precedence"
                        }
                    )

                return resilience_config

            # Load preset configuration
            try:
                # Always prefer the instance's preset; do not let env override during tests
                preset_name = self.resilience_preset

                preset = preset_manager.get_preset(preset_name)
                resilience_config = preset.to_resilience_config()

                # Record preset usage
                config_metrics_collector.record_preset_usage(
                    preset_name=preset_name,
                    operation="load_preset",
                    session_id=session_id,
                    user_context=user_context,
                    metadata={"config_type": config_type}
                )

                # Apply custom overrides if provided. During pytest, do not read
                # RESILIENCE_CUSTOM_CONFIG from the environment; always prefer instance.
                custom_config_json = self.resilience_custom_config
                if not _IS_PYTEST and not custom_config_json:
                    env_custom_config = os.getenv("RESILIENCE_CUSTOM_CONFIG")
                    if env_custom_config:
                        custom_config_json = env_custom_config

                if custom_config_json:
                    try:
                        custom_config = json.loads(custom_config_json)
                        resilience_config = self._apply_resilience_custom_overrides(resilience_config, custom_config)

                        config_metrics_collector.record_preset_usage(
                            preset_name=preset_name,
                            operation="apply_custom_config",
                            session_id=session_id,
                            user_context=user_context,
                            metadata={
                                "config_type": "custom",
                                "custom_keys": list(custom_config.keys())
                            }
                        )

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in resilience_custom_config: {e}")

                        config_metrics_collector.record_config_error(
                            preset_name=preset_name,
                            operation="parse_custom_config",
                            error_message=f"JSON decode error: {str(e)}",
                            session_id=session_id,
                            user_context=user_context
                        )

                return resilience_config

            except Exception as e:
                logger.error(f"Error loading resilience preset '{self.resilience_preset}': {e}")

                config_metrics_collector.record_config_error(
                    preset_name=preset_name,
                    operation="load_preset",
                    error_message=str(e),
                    session_id=session_id,
                    user_context=user_context
                )

                # Fall back to simple preset
                try:
                    fallback_preset = preset_manager.get_preset("simple")
                    config_metrics_collector.record_preset_usage(
                        preset_name="simple",
                        operation="fallback_preset",
                        session_id=session_id,
                        user_context=user_context,
                        metadata={"original_preset": self.resilience_preset, "config_type": "fallback"}
                    )
                    return fallback_preset.to_resilience_config()
                except Exception as fallback_error:
                    config_metrics_collector.record_config_error(
                        preset_name="simple",
                        operation="fallback_preset",
                        error_message=str(fallback_error),
                        session_id=session_id,
                        user_context=user_context
                    )
                    raise

    def get_operation_strategy(self, operation_name: str) -> str:
        """
        Get resilience strategy for a specific AI operation type.
        
        This method maps AI operation names to their configured resilience strategies,
        providing operation-specific resilience behavior while maintaining backward
        compatibility with multiple operation name variations.

        Args:
            operation_name: Name of the AI operation to get strategy for.
                          Supported operations include:
                          - "summarize" or "summarize_text": Text summarization operations
                          - "sentiment" or "analyze_sentiment": Sentiment analysis operations  
                          - "key_points" or "extract_key_points": Key point extraction operations
                          - "questions" or "generate_questions": Question generation operations
                          - "qa" or "answer_question": Question answering operations

        Returns:
            String resilience strategy name, one of:
            - "conservative": High retry attempts, long timeouts, robust error handling
            - "balanced": Moderate retry attempts and timeouts, good for most operations
            - "aggressive": Low retry attempts, short timeouts, fail-fast behavior
            Returns "balanced" for unknown operation names (default fallback)
            
        Behavior:
            - Maps operation names to corresponding resilience strategy configuration fields
            - Supports both short names ("summarize") and full names ("summarize_text") for compatibility
            - Uses getattr with default fallback to handle missing strategy configurations gracefully
            - Returns "balanced" strategy for any unrecognized operation names
            - Operation name matching is case-sensitive
            - Does not modify internal state or trigger any side effects
            
        Examples:
            >>> # Get strategy for different operation types
            >>> strategy = settings.get_operation_strategy("summarize")
            >>> assert strategy in ["conservative", "balanced", "aggressive"]
            
            >>> # Both short and full names work
            >>> short_strategy = settings.get_operation_strategy("sentiment")
            >>> full_strategy = settings.get_operation_strategy("analyze_sentiment") 
            >>> assert short_strategy == full_strategy
            
            >>> # Unknown operations return default
            >>> unknown_strategy = settings.get_operation_strategy("unknown_operation")
            >>> assert unknown_strategy == "balanced"
            
            >>> # Case sensitivity
            >>> strategy = settings.get_operation_strategy("SUMMARIZE")  # Won't match
            >>> assert strategy == "balanced"  # Falls back to default
        """
        # Map operation names to their strategy attributes
        operation_strategies = {
            "summarize": getattr(self, 'summarize_resilience_strategy', 'balanced'),
            "summarize_text": getattr(self, 'summarize_resilience_strategy', 'balanced'),
            "sentiment": getattr(self, 'sentiment_resilience_strategy', 'balanced'),
            "analyze_sentiment": getattr(self, 'sentiment_resilience_strategy', 'balanced'),
            "key_points": getattr(self, 'key_points_resilience_strategy', 'balanced'),
            "extract_key_points": getattr(self, 'key_points_resilience_strategy', 'balanced'),
            "questions": getattr(self, 'questions_resilience_strategy', 'balanced'),
            "generate_questions": getattr(self, 'questions_resilience_strategy', 'balanced'),
            "qa": getattr(self, 'qa_resilience_strategy', 'balanced'),
            "answer_question": getattr(self, 'qa_resilience_strategy', 'balanced'),
        }

        return operation_strategies.get(operation_name, 'balanced')

    # TODO: move/dedupe this to backend/app/infrastructure/resilience/
    def validate_resilience_custom_config(self, json_string: Optional[str] = None) -> dict:
        """
        Validate custom resilience configuration JSON string against schema.
        
        This method provides comprehensive validation of custom resilience configuration
        JSON strings, ensuring they conform to the expected schema and contain valid
        values before application to the resilience system.

        Args:
            json_string: JSON string to validate (default: None).
                        If None, validates the current resilience_custom_config field value.
                        If empty string or None, returns success with warning message.

        Returns:
            Dictionary with validation results containing:
            - "is_valid": Boolean indicating overall validation success
            - "errors": List of error messages for validation failures
            - "warnings": List of warning messages for non-critical issues
            
        Behavior:
            - Uses resilience_custom_config field value when json_string parameter is None
            - Returns successful validation with warning when no configuration provided
            - Parses JSON string and validates against resilience configuration schema
            - Checks value types, ranges, and allowed enumeration values
            - Validates nested configuration objects and their relationships
            - Provides detailed error messages with field names and expected values
            - Catches and reports JSON parsing errors with helpful error descriptions
            - Does not modify any configuration state during validation
            
        Examples:
            >>> # Validate current configuration
            >>> result = settings.validate_custom_config()
            >>> assert result["is_valid"] is True
            >>> assert "No custom configuration" in result["warnings"][0]
            
            >>> # Validate valid JSON configuration
            >>> valid_config = '{"retry_attempts": 5, "circuit_breaker_threshold": 10}'
            >>> result = settings.validate_custom_config(valid_config)
            >>> assert result["is_valid"] is True
            >>> assert len(result["errors"]) == 0
            
            >>> # Validate invalid JSON configuration
            >>> invalid_config = '{"retry_attempts": "not_a_number"}'
            >>> result = settings.validate_custom_config(invalid_config)
            >>> assert result["is_valid"] is False
            >>> assert len(result["errors"]) > 0
            >>> assert "retry_attempts" in str(result["errors"])
            
            >>> # Handle JSON parsing errors
            >>> malformed_json = '{"retry_attempts": 5,}'  # Trailing comma
            >>> result = settings.validate_custom_config(malformed_json)
            >>> assert result["is_valid"] is False
            >>> assert "Validation error" in result["errors"][0]
        """
        from app.infrastructure.resilience.config_validator import config_validator

        config_to_validate = json_string or self.resilience_custom_config
        if not config_to_validate:
            return {"is_valid": True, "errors": [], "warnings": ["No custom configuration to validate"]}

        try:
            validation_result = config_validator.validate_json_string(config_to_validate)
            return validation_result.to_dict()
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }


    # ========================================
    # AUTHENTICATION & UTILITY METHODS
    # ========================================
    #
    # Core utility methods for application operation

    def get_valid_api_keys(self) -> List[str]:
        """
        Get list of all valid API keys for authentication.
        
        This method combines the primary API key with additional API keys to provide
        a complete list of valid authentication keys for the application.
        
        Returns:
            List of valid API key strings. Empty list if no keys are configured.
            Primary API key is included first if present, followed by additional keys.
            
        Behavior:
            - Includes primary api_key field value if not empty
            - Parses additional_api_keys field (comma-separated string) and includes individual keys
            - Strips whitespace from all keys during parsing
            - Filters out empty strings from additional keys list
            - Maintains order: primary key first, then additional keys in original order
            - Returns empty list if no valid keys are configured
            
        Examples:
            >>> # With primary key only
            >>> settings.api_key = "primary-key-123"
            >>> settings.additional_api_keys = ""
            >>> keys = settings.get_valid_api_keys()
            >>> assert keys == ["primary-key-123"]
            
            >>> # With primary and additional keys
            >>> settings.api_key = "primary-key"
            >>> settings.additional_api_keys = "key1,key2,key3"
            >>> keys = settings.get_valid_api_keys()
            >>> assert keys == ["primary-key", "key1", "key2", "key3"]
            
            >>> # With whitespace handling
            >>> settings.additional_api_keys = " key1 , key2 , key3 "
            >>> keys = settings.get_valid_api_keys()
            >>> assert "key1" in keys and "key2" in keys
            
            >>> # No keys configured
            >>> settings.api_key = ""
            >>> settings.additional_api_keys = ""
            >>> keys = settings.get_valid_api_keys()
            >>> assert keys == []
        """
        valid_keys = []
        
        # Add primary key if present
        if self.api_key.strip():
            valid_keys.append(self.api_key.strip())
            
        # Add additional keys if present
        if self.additional_api_keys.strip():
            additional = [key.strip() for key in self.additional_api_keys.split(',') if key.strip()]
            valid_keys.extend(additional)
            
        return valid_keys
    
    @property
    def is_development(self) -> bool:
        """
        Check if the application is running in development mode.
        
        This property provides a convenient way to check if the application is
        configured for development, which affects logging, error handling, and
        various operational behaviors.
        
        Returns:
            Boolean indicating if running in development mode.
            True when debug=True or cache_preset/resilience_preset contain 'development'
            
        Behavior:
            - Returns True if debug field is True (primary development indicator)
            - Returns True if cache_preset contains 'development' (cache-based detection)
            - Returns True if resilience_preset contains 'development' (resilience-based detection)
            - Returns False only when all development indicators are absent
            - Case-sensitive string matching for preset names
            
        Examples:
            >>> # Debug mode enabled
            >>> settings.debug = True
            >>> assert settings.is_development is True
            
            >>> # Development presets
            >>> settings.debug = False
            >>> settings.cache_preset = "development"
            >>> assert settings.is_development is True
            
            >>> settings.resilience_preset = "ai-development"
            >>> assert settings.is_development is True
            
            >>> # Production configuration
            >>> settings.debug = False
            >>> settings.cache_preset = "production"
            >>> settings.resilience_preset = "production"
            >>> assert settings.is_development is False
        """
        return (
            self.debug or
            'development' in self.cache_preset.lower() or
            'development' in self.resilience_preset.lower()
        )


    # ========================================
    # INTERNAL CONFIGURATION PROCESSING
    # ========================================
    #
    # Private/internal methods that support the public interface

    def _clear_legacy_config_cache(self):
        """Clear the cached legacy configuration detection result for fresh evaluation."""
        if hasattr(self, '_legacy_config_cache'):
            delattr(self, '_legacy_config_cache')

    def _has_legacy_resilience_config(self) -> bool:
        """
        Check if legacy resilience configuration variables are present.

        This method detects whether the application is using legacy environment
        variables for resilience configuration, which triggers backward compatibility mode.
        """
        # Cache the result to avoid repeated checks
        if hasattr(self, '_legacy_config_cache'):
            return self._legacy_config_cache

        # Only treat explicit legacy environment variables as legacy mode triggers
        env = os.environ
        legacy_vars = [
            "RETRY_MAX_ATTEMPTS",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT",
            "RETRY_MAX_DELAY",
            "RETRY_EXPONENTIAL_MULTIPLIER",
            "RETRY_EXPONENTIAL_MIN",
            "RETRY_EXPONENTIAL_MAX",
            "RETRY_JITTER_ENABLED",
            "RETRY_JITTER_MAX",
            "DEFAULT_RESILIENCE_STRATEGY",
            "SUMMARIZE_RESILIENCE_STRATEGY",
            "SENTIMENT_RESILIENCE_STRATEGY",
            "KEY_POINTS_RESILIENCE_STRATEGY",
            "QUESTIONS_RESILIENCE_STRATEGY",
            "QA_RESILIENCE_STRATEGY",
            "CIRCUIT_BREAKER_ENABLED",
            "RETRY_ENABLED",
        ]

        has_legacy = any(var in env for var in legacy_vars)
        self._legacy_config_cache = has_legacy
        return has_legacy

    def _load_legacy_resilience_config(self):
        """
        Load resilience configuration from legacy environment variables.

        This method provides backward compatibility for applications that were
        using individual environment variables for resilience configuration
        before the preset system was introduced.
        """
        from app.infrastructure.resilience import (
            ResilienceConfig, RetryConfig, CircuitBreakerConfig, ResilienceStrategy
        )

        # Map legacy strategy strings to enum values
        strategy_mapping = {
            "aggressive": ResilienceStrategy.AGGRESSIVE,
            "balanced": ResilienceStrategy.BALANCED,
            "conservative": ResilienceStrategy.CONSERVATIVE,
            "critical": ResilienceStrategy.CRITICAL
        }

        default_strategy_str = os.getenv(
            "DEFAULT_RESILIENCE_STRATEGY", self.default_resilience_strategy
        )
        default_strategy = strategy_mapping.get(default_strategy_str, ResilienceStrategy.BALANCED)

        # Helper functions for safe environment variable conversion
        def safe_int(env_var: str, fallback: int) -> int:
            try:
                value = os.getenv(env_var)
                if value is None:
                    return fallback
                result = int(value)
                if (env_var in ["RETRY_MAX_ATTEMPTS", "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
                                "CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "RETRY_MAX_DELAY"] and result <= 0):
                    logger.warning(f"Invalid negative/zero value for {env_var}: {result}, using fallback: {fallback}")
                    return fallback
                return result
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid value for {env_var}: {os.getenv(env_var)}, "
                    f"using fallback: {fallback}"
                )
                return fallback

        def safe_float(env_var: str, fallback: float) -> float:
            try:
                value = os.getenv(env_var)
                if value is None:
                    return fallback
                result = float(value)
                if (env_var in ["RETRY_EXPONENTIAL_MULTIPLIER", "RETRY_EXPONENTIAL_MIN",
                                "RETRY_EXPONENTIAL_MAX", "RETRY_JITTER_MAX"] and result <= 0):
                    logger.warning(
                        f"Invalid negative/zero value for {env_var}: {result}, "
                        f"using fallback: {fallback}"
                    )
                    return fallback
                return result
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid value for {env_var}: {os.getenv(env_var)}, "
                    f"using fallback: {fallback}"
                )
                return fallback

        # Load configuration from environment variables with safe conversion
        retry_max_attempts = safe_int("RETRY_MAX_ATTEMPTS", self.retry_max_attempts)
        retry_max_delay = safe_int("RETRY_MAX_DELAY", self.retry_max_delay)
        retry_exponential_multiplier = safe_float("RETRY_EXPONENTIAL_MULTIPLIER", self.retry_exponential_multiplier)
        retry_exponential_min = safe_float("RETRY_EXPONENTIAL_MIN", self.retry_exponential_min)
        retry_exponential_max = safe_float("RETRY_EXPONENTIAL_MAX", self.retry_exponential_max)
        retry_jitter_enabled = os.getenv("RETRY_JITTER_ENABLED", str(self.retry_jitter_enabled)).lower() in ("true", "1", "yes")
        retry_jitter_max = safe_float("RETRY_JITTER_MAX", self.retry_jitter_max)

        circuit_breaker_failure_threshold = safe_int("CIRCUIT_BREAKER_FAILURE_THRESHOLD", self.circuit_breaker_failure_threshold)
        circuit_breaker_recovery_timeout = safe_int("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", self.circuit_breaker_recovery_timeout)

        # In legacy mode, boolean feature toggles should follow legacy env vars exactly, not defaults
        cbe = os.getenv("CIRCUIT_BREAKER_ENABLED")
        re = os.getenv("RETRY_ENABLED")
        res_en = os.getenv("RESILIENCE_ENABLED")
        circuit_breaker_enabled = (str(self.circuit_breaker_enabled) if cbe is None else cbe).lower() in ("true", "1", "yes")
        retry_enabled = (str(self.retry_enabled) if re is None else re).lower() in ("true", "1", "yes")
        # Update master toggle as well
        if res_en is not None:
            try:
                self.resilience_enabled = res_en.lower() in ("true", "1", "yes")
            except Exception:
                self.resilience_enabled = self.resilience_enabled

        return ResilienceConfig(
            strategy=default_strategy,
            retry_config=RetryConfig(
                max_attempts=retry_max_attempts,
                max_delay_seconds=retry_max_delay,
                exponential_multiplier=retry_exponential_multiplier,
                exponential_min=retry_exponential_min,
                exponential_max=retry_exponential_max,
                jitter=retry_jitter_enabled,
                jitter_max=retry_jitter_max
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=circuit_breaker_failure_threshold,
                recovery_timeout=circuit_breaker_recovery_timeout
            ),
            enable_circuit_breaker=circuit_breaker_enabled,
            enable_retry=retry_enabled
        )

    def _apply_cache_custom_overrides(self, base_config, custom_config: dict):
        """
        Apply custom configuration overrides to base cache preset configuration.
        
        This internal method applies user-provided custom configuration overrides
        to the base cache configuration loaded from presets, with special handling
        for nested dictionary structures and comprehensive logging.
        
        Args:
            base_config: Base cache configuration object from preset loading
            custom_config: Dictionary of custom override key-value pairs
            
        Returns:
            Modified cache configuration object with all valid overrides applied
            
        Behavior:
            - Creates deep copy of base configuration to avoid modifying original
            - Applies each override key-value pair if the key exists on the configuration object
            - Handles nested dictionary merging for 'text_size_tiers' and 'operation_ttls' keys
            - Logs debug messages for each successfully applied override
            - Logs warnings for unrecognized configuration keys in custom overrides
            - Preserves original base configuration values for unspecified override keys
        """
        # Create a copy to avoid modifying the original
        from dataclasses import replace
        import copy
        
        # Make a deep copy of the config
        modified_config = copy.deepcopy(base_config)
        
        # Apply each override
        for key, value in custom_config.items():
            if hasattr(modified_config, key):
                # Special handling for nested dictionaries
                if key in ['text_size_tiers', 'operation_ttls']:
                    if hasattr(modified_config, key):
                        current_value = getattr(modified_config, key)
                        if isinstance(current_value, dict) and isinstance(value, dict):
                            current_value.update(value)
                        else:
                            setattr(modified_config, key, value)
                    else:
                        setattr(modified_config, key, value)
                else:
                    setattr(modified_config, key, value)
                logger.debug(f"Applied cache override: {key} = {value}")
            else:
                logger.warning(f"Unknown cache configuration key '{key}' in custom config")
        
        return modified_config

    def _apply_resilience_custom_overrides(self, base_config, custom_config: dict):
        """
        Apply custom configuration overrides to base resilience preset config.

        This method allows fine-tuning of preset configurations through
        JSON configuration overrides while maintaining validation.

        Args:
            base_config: Base ResilienceConfig from preset
            custom_config: Dictionary of configuration overrides

        Returns:
            ResilienceConfig with custom overrides applied
        """
        from app.infrastructure.resilience import ResilienceStrategy, ResilienceConfig, RetryConfig, CircuitBreakerConfig
        from app.infrastructure.resilience.config_validator import config_validator

        # Validate custom configuration
        validation_result = config_validator.validate_custom_config(custom_config)
        if not validation_result.is_valid:
            logger.error(f"Invalid custom configuration: {validation_result.errors}")
            # Log warnings but continue
            for warning in validation_result.warnings:
                logger.warning(f"Custom configuration warning: {warning}")
            # Return base config without applying invalid overrides
            return base_config

        # Log any warnings
        if validation_result.warnings:
            for warning in validation_result.warnings:
                logger.warning(f"Custom configuration warning: {warning}")

        # Create new configuration objects with overrides applied
        new_retry_config = RetryConfig(
            max_attempts=custom_config.get("retry_attempts", base_config.retry_config.max_attempts),
            max_delay_seconds=custom_config.get("max_delay_seconds", base_config.retry_config.max_delay_seconds),
            exponential_multiplier=custom_config.get("exponential_multiplier", base_config.retry_config.exponential_multiplier),
            exponential_min=custom_config.get("exponential_min", base_config.retry_config.exponential_min),
            exponential_max=custom_config.get("exponential_max", base_config.retry_config.exponential_max),
            jitter=custom_config.get("jitter_enabled", base_config.retry_config.jitter),
            jitter_max=custom_config.get("jitter_max", base_config.retry_config.jitter_max)
        )

        new_circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=custom_config.get("circuit_breaker_threshold", base_config.circuit_breaker_config.failure_threshold),
            recovery_timeout=custom_config.get("recovery_timeout", base_config.circuit_breaker_config.recovery_timeout),
            half_open_max_calls=base_config.circuit_breaker_config.half_open_max_calls  # Not configurable via custom config
        )

        # Apply strategy overrides
        strategy = base_config.strategy
        if "default_strategy" in custom_config:
            try:
                strategy = ResilienceStrategy(custom_config["default_strategy"])
            except ValueError:
                logger.warning(f"Invalid default strategy '{custom_config['default_strategy']}', keeping original")

        # Apply operation-specific strategy overrides
        if "operation_overrides" in custom_config:
            for operation, strategy_str in custom_config["operation_overrides"].items():
                try:
                    # Validate the strategy is valid
                    ResilienceStrategy(strategy_str)
                    # Note: Operation-specific strategies would be handled by AIServiceResilience
                    # For now, we just validate the strategy is valid
                except ValueError:
                    logger.warning(f"Invalid strategy '{strategy_str}' for operation '{operation}'")

        # Create new resilience config with all overrides applied
        return ResilienceConfig(
            strategy=strategy,
            retry_config=new_retry_config,
            circuit_breaker_config=new_circuit_breaker_config,
            enable_circuit_breaker=base_config.enable_circuit_breaker,
            enable_retry=base_config.enable_retry
        )


    # ========================================
    # BACKWARD COMPATIBILITY METHODS
    # ========================================
    # These methods maintain compatibility with existing code and tests

    def get_registered_operations(self) -> List[str]:
        """Get list of operations that should be registered with resilience service."""
        return [
            "summarize_text",
            "analyze_sentiment",
            "extract_key_points",
            "generate_questions",
            "answer_question"
        ]

    def register_operation(self, operation_name: str, strategy: str):
        """Register an operation with a strategy (no-op for backward compatibility with tests)."""
        # This is a no-op for compatibility - actual registration happens in resilience service
        pass

    @property
    def is_legacy_config(self) -> bool:
        """Check if using legacy configuration (for test compatibility)."""
        return self._has_legacy_resilience_config()

    def get_operation_configs(self) -> dict:
        """Get all operation configurations (for test compatibility)."""
        operations = self.get_registered_operations()
        return {op: self.get_operation_strategy(op) for op in operations}

    def get_preset_operations(self, preset_name: Optional[str] = None) -> List[str]:
        """Get operations for a specific preset (for test compatibility)."""
        return self.get_registered_operations()

    def get_all_operation_strategies(self) -> dict:
        """Get all operation strategy mappings (for test compatibility)."""
        return {
            "summarize": self.summarize_resilience_strategy,
            "summarize_text": self.summarize_resilience_strategy,
            "sentiment": self.sentiment_resilience_strategy,
            "analyze_sentiment": self.sentiment_resilience_strategy,
            "key_points": self.key_points_resilience_strategy,
            "extract_key_points": self.key_points_resilience_strategy,
            "questions": self.questions_resilience_strategy,
            "generate_questions": self.questions_resilience_strategy,
            "qa": self.qa_resilience_strategy,
            "answer_question": self.qa_resilience_strategy,
        }
    

# ========================================
# GLOBAL SETTINGS INSTANCE
# ========================================

# Global settings instance for dependency injection throughout the application
settings = Settings()
