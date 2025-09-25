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
- **Configuration Presets**: Simplified preset-based configuration system
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
- **Preset System**: Intelligent defaults with simple environment variable selection
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
from app.infrastructure.resilience.config_validator import config_validator

try:
    # Load cache configuration with session tracking
    cache_config = settings.get_cache_config(
        session_id="user_123",
        user_context="production_deployment"
    )
    
    # Validate custom resilience configuration if needed
    custom_json = '{"retry_attempts": 5, "circuit_breaker_threshold": 10}'
    validation_result = config_validator.validate_json_string(custom_json)
    if not validation_result.is_valid:
        logger.error(f"Configuration errors: {validation_result.errors}")
        
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
- Resilience presets provide simplified configuration with intelligent defaults
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
    preset-based configuration and proper fallback behavior.
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
        - Applies preset-based resilience configuration with optional custom overrides
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

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        """
        Customize settings sources to ignore OS env vars during pytest.
        
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
        ...

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate log level is one of the allowed values.
        """
        ...

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """
        Validate CORS origins format.
        """
        ...

    @field_validator('cache_preset')
    @classmethod
    def validate_cache_preset(cls, v: str) -> str:
        """
        Validate cache preset name.
        """
        ...

    @field_validator('resilience_preset')
    @classmethod
    def validate_resilience_preset(cls, v: str) -> str:
        """
        Validate resilience preset name.
        """
        ...

    @field_validator('health_check_timeout_ms', 'health_check_ai_model_timeout_ms', 'health_check_cache_timeout_ms', 'health_check_resilience_timeout_ms', 'health_check_retry_count')
    @classmethod
    def validate_health_check_numbers(cls, v: int | float, info) -> int:
        """
        Ensure health check numeric settings are valid, and warn about suboptimal values.
        """
        ...

    @field_validator('health_check_enabled_components')
    @classmethod
    def validate_enabled_health_components(cls, v: List[str]) -> List[str]:
        """
        Checks that all enabled components are valid and warns if none are enabled.
        """
        ...

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
            - Maps 'testing' preset alias to 'development' preset for convenience
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
        ...

    def get_resilience_config(self, session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Get complete resilience configuration from preset with custom overrides.
        
        This is the main entry point for resilience configuration that implements the
        preset-based architecture. It automatically resolves configuration from presets
        and provides comprehensive monitoring and error handling with fallback behavior.
        
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
            - Resolves resilience_preset field to load base configuration from preset system
            - Applies resilience_custom_config JSON overrides if provided and valid
            - Falls back to 'simple' preset if primary preset loading fails
            - Logs all configuration resolution steps and applied overrides for debugging
            - Records preset usage metrics and monitoring data for analytics
            - Provides session and user context tracking for operational monitoring
            - Returns identical configuration for identical parameters and environment state
        
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
        
            >>> # Custom JSON configuration mode
            >>> settings.resilience_custom_config = '{"retry_attempts": 7, "circuit_breaker_threshold": 15}'
            >>> config = settings.get_resilience_config()
            >>> assert config.retry_config.max_attempts == 7
            >>> assert config.circuit_breaker_config.failure_threshold == 15
        """
        ...

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
        ...

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
        ...

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
        ...

    def get_registered_operations(self) -> List[str]:
        """
        Get list of operations that should be registered with resilience service.
        """
        ...

    def register_operation(self, operation_name: str, strategy: str):
        """
        Register an operation with a strategy (no-op for backward compatibility with tests).
        """
        ...

    @property
    def is_legacy_config(self) -> bool:
        """
        Check if using legacy configuration (for test compatibility).
        """
        ...

    def get_operation_configs(self) -> dict:
        """
        Get all operation configurations (for test compatibility).
        """
        ...

    def get_preset_operations(self, preset_name: Optional[str] = None) -> List[str]:
        """
        Get operations for a specific preset (for test compatibility).
        """
        ...

    def get_all_operation_strategies(self) -> dict:
        """
        Get all operation strategy mappings (for test compatibility).
        """
        ...
