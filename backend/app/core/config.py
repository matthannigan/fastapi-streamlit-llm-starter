"""
Core Application Configuration

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
- Health check configuration with component-specific timeouts and retry logic
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

### Health Check Configuration
- Component-specific timeout configuration
- Configurable retry logic for failing checks
- Selective component enabling/disabling
- Performance-tuned defaults for different environments

## Environment Variables

The configuration system supports both modern preset-based configuration and
legacy individual environment variables for backward compatibility:

```bash
# Modern preset approach (recommended)
RESILIENCE_PRESET=production
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 5}'

# Health check configuration
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_RETRY_COUNT=1
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience"]

# Legacy individual variables (supported for compatibility)
RETRY_MAX_ATTEMPTS=3
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
```

## Validation and Error Handling

- Comprehensive field validation using Pydantic validators
- Graceful fallback for invalid values with warning logs
- Strict validation for direct API usage
- Configuration error classification and reporting

Note:
    The Settings class automatically loads configuration from environment variables
    and provides extensive validation. Legacy resilience configuration is supported
    for backward compatibility when legacy environment variables are detected.
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


class Settings(BaseSettings):
    """
    Centralized application configuration class with comprehensive environment variable support and validation.
    
    This class serves as the single source of truth for all application configuration, providing
    organized, validated, and type-safe access to environment-specific settings. It supports
    both modern preset-based configuration and legacy environment variables for backward compatibility.
    
    Attributes:
        gemini_api_key: Google Gemini API key for AI service integration
        ai_model: Default AI model identifier for processing requests
        ai_temperature: AI model temperature (0.0-2.0) for response creativity control
        MAX_BATCH_REQUESTS_PER_CALL: Maximum batch size for concurrent processing
        BATCH_AI_CONCURRENCY_LIMIT: Concurrent AI request limit in batch operations
        host: Server host address for binding (default: "0.0.0.0")
        port: Server port number for binding (1-65535, default: 8000)
        api_key: Primary API key for authentication
        additional_api_keys: Comma-separated additional API keys for multi-client access
        allowed_origins: List of allowed CORS origins for cross-origin requests
        debug: Debug mode flag for development environments
        log_level: Application logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        redis_url: Redis connection URL for caching infrastructure
        cache_compression_threshold: Size threshold (bytes) for enabling compression
        cache_large_text_threshold: Size threshold (bytes) for large text handling
        RESILIENCE_PRESET: Resilience configuration preset (simple, development, production)
        RESILIENCE_CUSTOM_CONFIG: Custom JSON configuration for advanced resilience settings
        
    Public Methods:
        get_resilience_config(): Get complete resilience configuration with preset and custom overrides
        get_operation_strategy(): Get resilience strategy for specific operation types
        _load_resilience_config(): Load and validate resilience configuration from various sources
        get_valid_api_keys(): Get list of all valid API keys (primary + additional)
        is_development(): Check if running in development mode
        model_config: Pydantic configuration for environment variable handling
        
    State Management:
        - Immutable configuration once loaded (Pydantic BaseSettings behavior)
        - Thread-safe access to configuration values
        - Automatic environment variable type conversion and validation
        - Graceful handling of missing or invalid configuration values
        - Support for .env file loading in non-test environments
        
    Usage:
        # Basic configuration access
        from app.core.config import settings
        
        # AI configuration
        api_key = settings.gemini_api_key
        model = settings.ai_model
        temperature = settings.ai_temperature
        
        # Resilience configuration (modern preset approach)
        resilience_config = settings.get_resilience_config()
        strategy = settings.get_operation_strategy("summarize")
        
        # Authentication configuration
        valid_keys = settings.get_valid_api_keys()
        is_dev = settings.is_development()
        
        # Cache configuration
        redis_url = settings.redis_url
        compression_threshold = settings.cache_compression_threshold
        
        # Advanced resilience configuration
        custom_config = {
            "retry_attempts": 5,
            "circuit_breaker_threshold": 10,
            "timeout_seconds": 30
        }
        settings.RESILIENCE_CUSTOM_CONFIG = json.dumps(custom_config)
        updated_config = settings.get_resilience_config()
        
        # Environment-specific configuration
        if settings.debug:
            # Development-specific logic
            logger.setLevel(logging.DEBUG)
        
        # Health check configuration
        timeouts = {
            "ai_model": settings.HEALTH_CHECK_AI_MODEL_TIMEOUT_MS,
            "cache": settings.HEALTH_CHECK_CACHE_TIMEOUT_MS,
            "resilience": settings.HEALTH_CHECK_RESILIENCE_TIMEOUT_MS
        }
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
    # CACHE CONFIGURATION
    # ========================================

    # Redis Connection
    redis_url: str = Field(
        default="redis://redis:6379",
        description="Redis connection URL for caching"
    )

    # Cache Key Generation
    cache_text_hash_threshold: int = Field(
        default=1000,
        gt=0,
        description="Character count threshold for cache key text hashing"
    )

    # Cache Compression Settings
    cache_compression_threshold: int = Field(
        default=1000,
        gt=0,
        description="Size threshold in bytes for compressing cache data"
    )
    cache_compression_level: int = Field(
        default=6,
        ge=1,
        le=9,
        description="Compression level (1-9, where 9 is highest compression)"
    )

    # Cache Text Size Tiers - Controls how different text sizes are cached
    # for optimal performance with varying strategies
    cache_text_size_tiers: dict = Field(
        default={
            'small': 500,      # < 500 chars - cache with full text, use memory cache
            'medium': 5000,    # 500-5000 chars - cache with text hash
            'large': 50000,    # 5000-50000 chars - cache with content hash + metadata
        },
        description="Text size tiers for caching strategy optimization"
    )

    # Memory Cache Settings
    cache_memory_cache_size: int = Field(
        default=100,
        gt=0,
        description="Maximum items in memory cache for small texts"
    )

    # Cache TTL (Time To Live) Settings
    cache_default_ttl: int = Field(
        default=3600,
        gt=0,
        description="Default cache TTL in seconds (1 hour)"
    )

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
    # RESILIENCE CONFIGURATION METHODS
    # ========================================

    def _clear_legacy_config_cache(self):
        """Clear the legacy configuration cache."""
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

    def get_resilience_config(self, session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Get resilience configuration from preset or legacy settings.

        This is the main entry point for resilience configuration. It automatically
        determines the appropriate configuration source and returns a complete
        ResilienceConfig object.

        Returns appropriate resilience configuration based on:
        1. Legacy environment variables (if present) - for backward compatibility
        2. Custom configuration JSON (if provided)
        3. Preset configuration (default)

        Args:
            session_id: Optional session identifier for monitoring
            user_context: Optional user context for monitoring

        Returns:
            ResilienceConfig object with complete configuration
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
                        resilience_config = self._apply_custom_overrides(resilience_config, custom_config)

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

    def _apply_custom_overrides(self, base_config, custom_config: dict):
        """
        Apply custom configuration overrides to base preset config.

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
    # CONFIGURATION UTILITY METHODS
    # ========================================

    def validate_custom_config(self, json_string: Optional[str] = None) -> dict:
        """
        Validate custom resilience configuration.

        Args:
            json_string: JSON string to validate (if None, uses current resilience_custom_config)

        Returns:
            Dictionary with validation results
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

    def get_operation_strategy(self, operation_name: str) -> str:
        """
        Get resilience strategy for a specific operation.

        Args:
            operation_name: Name of the operation

        Returns:
            Strategy name for the operation
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
        """Register an operation with a strategy (for compatibility with tests)."""
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

    def get_cache_config(self, session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Get cache configuration from preset or legacy settings.
        
        This is the main entry point for cache configuration. It automatically
        determines the appropriate configuration source and returns a complete
        CacheConfig object.

        Returns appropriate cache configuration based on:
        1. Custom configuration JSON (if provided)
        2. Preset configuration (default)
        3. Environment variable overrides (CACHE_REDIS_URL, ENABLE_AI_CACHE)

        Args:
            session_id: Optional session identifier for monitoring
            user_context: Optional user context for monitoring

        Returns:
            CacheConfig object with complete configuration
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

    def _apply_cache_custom_overrides(self, base_config, custom_config: dict):
        """
        Apply custom configuration overrides to base cache preset config.
        
        Args:
            base_config: Base cache configuration from preset
            custom_config: Dictionary of custom overrides
            
        Returns:
            Modified cache configuration with overrides applied
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


# ========================================
# GLOBAL SETTINGS INSTANCE
# ========================================

# Global settings instance for dependency injection throughout the application
settings = Settings()
