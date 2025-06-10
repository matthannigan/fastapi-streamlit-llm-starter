"""Backend configuration settings with resilience support."""

import os
import json
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

class Settings(BaseSettings):
    """Application settings with environment variable support and validation."""
    
    # AI Configuration
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    ai_model: str = Field(default="gemini-2.0-flash-exp", description="Default AI model to use")
    ai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="AI model temperature")
    
    # Batch Processing Configuration
    MAX_BATCH_REQUESTS_PER_CALL: int = Field(default=50, gt=0, description="Maximum batch requests per call")
    BATCH_AI_CONCURRENCY_LIMIT: int = Field(default=5, gt=0, description="Batch AI concurrency limit")
    
    # API Configuration
    host: str = Field(default="0.0.0.0", description="Backend host address")
    port: int = Field(default=8000, gt=0, le=65535, description="Backend port number")
    
    # Authentication Configuration
    api_key: str = Field(default="", description="Primary API key")
    additional_api_keys: str = Field(default="", description="Additional API keys (comma-separated)")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:8501", "http://frontend:8501"],
        description="Allowed CORS origins"
    )
    
    # Application Settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Redis Configuration
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")
    
    # Cache Key Generator Configuration
    cache_text_hash_threshold: int = Field(
        default=1000, gt=0, description="Character count threshold for cache key text hashing"
    )
    
    # Cache Compression Configuration  
    cache_compression_threshold: int = Field(
        default=1000, gt=0, description="Size threshold in bytes for compressing cache data"
    )
    cache_compression_level: int = Field(
        default=6, ge=1, le=9, description="Compression level (1-9, where 9 is highest compression)"
    )
    
    # Cache Text Size Tiers Configuration
    # Controls how different text sizes are cached with varying strategies for optimal performance
    cache_text_size_tiers: dict = Field(
        default={
            'small': 500,      # < 500 chars - cache with full text and use memory cache for fast access
            'medium': 5000,    # 500-5000 chars - cache with text hash for moderate performance
            'large': 50000,    # 5000-50000 chars - cache with content hash + metadata for large texts
        },
        description="Text size tiers for caching strategy optimization. Defines character thresholds for small, medium, and large text categories."
    )
    
    # Memory Cache Configuration
    cache_memory_cache_size: int = Field(
        default=100, gt=0, description="Maximum number of items to store in the in-memory cache for small texts. Higher values improve hit rates but use more memory."
    )
    
    # Cache TTL (Time To Live) Configuration  
    cache_default_ttl: int = Field(
        default=3600, gt=0, description="Default cache TTL in seconds (1 hour). Controls how long cached responses remain valid before expiration."
    )
    
    # Resilience Configuration - Preset System
    resilience_preset: str = Field(
        default="simple",
        description="Resilience configuration preset (simple, development, production)"
    )
    
    resilience_custom_config: Optional[str] = Field(
        default=None,
        description="Custom resilience configuration as JSON string (overrides preset)"
    )
    
    # Legacy Resilience Configuration (for backward compatibility)
    # Enable/disable resilience features
    resilience_enabled: bool = Field(default=True, description="Enable resilience features")
    circuit_breaker_enabled: bool = Field(default=True, description="Enable circuit breaker")
    retry_enabled: bool = Field(default=True, description="Enable retry mechanism")
    
    # Default resilience strategy for AI operations
    default_resilience_strategy: str = Field(
        default="balanced", 
        description="Default resilience strategy"
    )
    
    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = Field(
        default=5, gt=0, description="Circuit breaker failure threshold"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60, gt=0, description="Circuit breaker recovery timeout in seconds"
    )
    
    # Retry Settings
    retry_max_attempts: int = Field(default=3, gt=0, description="Maximum retry attempts")
    retry_max_delay: int = Field(default=30, gt=0, description="Maximum retry delay in seconds")
    retry_exponential_multiplier: float = Field(
        default=1.0, gt=0.0, description="Exponential backoff multiplier"
    )
    retry_exponential_min: float = Field(
        default=2.0, gt=0.0, description="Minimum exponential backoff delay"
    )
    retry_exponential_max: float = Field(
        default=10.0, gt=0.0, description="Maximum exponential backoff delay"
    )
    retry_jitter_enabled: bool = Field(default=True, description="Enable retry jitter")
    retry_jitter_max: float = Field(default=2.0, gt=0.0, description="Maximum jitter value")
    
    # Operation-specific resilience strategies
    summarize_resilience_strategy: str = Field(
        default="balanced",
        description="Resilience strategy for summarize operations"
    )
    sentiment_resilience_strategy: str = Field(
        default="aggressive",
        description="Resilience strategy for sentiment analysis"
    )
    key_points_resilience_strategy: str = Field(
        default="balanced",
        description="Resilience strategy for key points extraction"
    )
    questions_resilience_strategy: str = Field(
        default="balanced",
        description="Resilience strategy for question generation"
    )
    qa_resilience_strategy: str = Field(
        default="conservative",
        description="Resilience strategy for Q&A operations"
    )
    
    # Monitoring and health check settings
    resilience_metrics_enabled: bool = Field(default=True, description="Enable resilience metrics")
    resilience_health_check_enabled: bool = Field(default=True, description="Enable resilience health checks")
    
    # Pydantic V2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True
    )

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of: {', '.join(allowed_levels)}")
        return v.upper()

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins format."""
        if not v:
            raise ValueError("At least one allowed origin must be specified")
        return v

    @field_validator('resilience_preset')
    @classmethod
    def validate_resilience_preset(cls, v: str) -> str:
        """Validate resilience preset name."""
        allowed_presets = {"simple", "development", "production"}
        if v not in allowed_presets:
            raise ValueError(f"Invalid resilience_preset '{v}'. Allowed values: {', '.join(allowed_presets)}")
        return v

    @field_validator('default_resilience_strategy', 'summarize_resilience_strategy', 'sentiment_resilience_strategy', 
                     'key_points_resilience_strategy', 'questions_resilience_strategy', 'qa_resilience_strategy', mode='before')
    @classmethod
    def validate_resilience_strategy(cls, v, info) -> str:
        """Validate resilience strategy with graceful fallback for environment variables."""
        import logging
        import os
        
        logger = logging.getLogger(__name__)
        
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
            # We'll check if the problematic value comes from environment variables
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
                logger.warning(f"Invalid resilience strategy '{v}' from environment variable {env_var}, falling back to '{default_value}'")
                return default_value
            else:
                # Value was passed directly - strict validation
                raise ValueError(f"Invalid resilience strategy '{v}'. Allowed values: {', '.join(allowed_strategies)}")
        return v

    @field_validator('circuit_breaker_failure_threshold', 'circuit_breaker_recovery_timeout', 'retry_max_attempts', 'retry_max_delay', mode='before')
    @classmethod
    def validate_positive_integers(cls, v, info) -> int:
        """Validate positive integers with strict validation for completely invalid values."""
        import logging
        import os
        logger = logging.getLogger(__name__)
        
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
                raise ValueError(f"Invalid empty value for {info.field_name}. Must be a positive integer.")
            
            try:
                v = int(v)
            except (ValueError, TypeError):
                # Check if we're in a context with legacy environment variables
                legacy_vars = ["RETRY_MAX_ATTEMPTS", "CIRCUIT_BREAKER_FAILURE_THRESHOLD", 
                              "CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "RETRY_MAX_DELAY"]
                has_any_legacy = any(var in os.environ for var in legacy_vars)
                
                if has_any_legacy:
                    # Be graceful in legacy mode for non-empty invalid values
                    logger.warning(f"Invalid value for {info.field_name}: '{v}', using default: {default_value}")
                    return default_value
                else:
                    # Strict validation in normal mode
                    raise ValueError(f"Invalid value for {info.field_name}: '{v}'. Must be a positive integer.")
        
        # Handle negative/zero values - be graceful for these
        if isinstance(v, (int, float)) and v <= 0:
            logger.warning(f"Invalid value for {info.field_name}: {v}, using default: {default_value}")
            return default_value
            
        return int(v) if isinstance(v, (int, float)) else default_value

    @field_validator('retry_exponential_multiplier', 'retry_exponential_min', 'retry_exponential_max', 'retry_jitter_max')
    @classmethod
    def validate_positive_floats(cls, v: float, info) -> float:
        """Validate positive floats with fallback for invalid values."""
        if v <= 0:
            import logging
            logger = logging.getLogger(__name__)
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

    def _clear_legacy_config_cache(self):
        """Clear the legacy configuration cache."""
        if hasattr(self, '_legacy_config_cache'):
            delattr(self, '_legacy_config_cache')
    
    def _has_legacy_resilience_config(self) -> bool:
        """Check if legacy resilience configuration variables are present."""
        # Cache the result to avoid repeated expensive checks
        if hasattr(self, '_legacy_config_cache'):
            return self._legacy_config_cache
        
        # Check the most common legacy environment variables first for faster detection
        # Use direct os.environ access which is faster than os.getenv()
        import os
        env = os.environ
        
        # Check most common legacy vars first (ordered by usage frequency)
        if ("RETRY_MAX_ATTEMPTS" in env or 
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD" in env or 
            "DEFAULT_RESILIENCE_STRATEGY" in env):
            self._legacy_config_cache = True
            return True
        
        # Check remaining legacy environment variables
        other_legacy_vars = [
            "SUMMARIZE_RESILIENCE_STRATEGY",
            "SENTIMENT_RESILIENCE_STRATEGY", 
            "KEY_POINTS_RESILIENCE_STRATEGY",
            "QUESTIONS_RESILIENCE_STRATEGY",
            "QA_RESILIENCE_STRATEGY"
        ]
        
        for var in other_legacy_vars:
            if var in env:
                self._legacy_config_cache = True
                return True
        
        # Only check field values if no environment variables are set
        # This is the expensive part, so we avoid it when possible
        default_values = {
            'circuit_breaker_failure_threshold': 5,
            'retry_max_attempts': 3,
            'retry_max_delay': 30,
            'circuit_breaker_recovery_timeout': 60,
            'retry_exponential_multiplier': 1.0,
            'retry_exponential_min': 2.0,
            'retry_exponential_max': 10.0,
            'retry_jitter_max': 2.0,
            'default_resilience_strategy': 'balanced',
            'summarize_resilience_strategy': 'balanced',
            'sentiment_resilience_strategy': 'aggressive',
            'key_points_resilience_strategy': 'balanced',
            'questions_resilience_strategy': 'balanced',
            'qa_resilience_strategy': 'conservative',
        }
        
        for field_name, default_value in default_values.items():
            current_value = getattr(self, field_name)
            if current_value != default_value:
                self._legacy_config_cache = True
                return True
        
        self._legacy_config_cache = False
        return False

    def get_resilience_config(self, session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Get resilience configuration from preset or legacy settings.
        
        Returns appropriate resilience configuration based on:
        1. Legacy environment variables (if present) - for backward compatibility
        2. Custom configuration JSON (if provided)
        3. Preset configuration (default)
        
        Args:
            session_id: Optional session identifier for monitoring
            user_context: Optional user context for monitoring
        """
        # Import here to avoid circular imports
        from app.resilience_presets import preset_manager
        from app.services.resilience import ResilienceConfig, RetryConfig, CircuitBreakerConfig, ResilienceStrategy
        from app.config_monitoring import config_metrics_collector
        
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
            # This ensures we get fresh results when environment variables change during testing
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
                # Custom config is ignored to maintain backward compatibility
                # This ensures legacy environment variables always override custom JSON config
                if self.resilience_custom_config:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info("Legacy environment variables detected - custom config will be ignored to maintain backward compatibility")
                    
                    # Record that custom config was ignored due to legacy mode
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
                import os
                env_preset = os.getenv("RESILIENCE_PRESET")
                
                # Use environment variable if present, otherwise use field value
                preset_name = env_preset if env_preset else self.resilience_preset
                
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
                
                # Apply custom overrides if provided
                # Use environment variable if present, otherwise use field value
                env_custom_config = os.getenv("RESILIENCE_CUSTOM_CONFIG")
                custom_config_json = env_custom_config if env_custom_config else self.resilience_custom_config
                
                if custom_config_json:
                    try:
                        custom_config = json.loads(custom_config_json)
                        resilience_config = self._apply_custom_overrides(resilience_config, custom_config)
                        
                        # Record custom configuration usage
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
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Invalid JSON in resilience_custom_config: {e}")
                        
                        # Record configuration error
                        config_metrics_collector.record_config_error(
                            preset_name=preset_name,
                            operation="parse_custom_config",
                            error_message=f"JSON decode error: {str(e)}",
                            session_id=session_id,
                            user_context=user_context
                        )
                        # Fall back to preset without custom config
                
                return resilience_config
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error loading resilience preset '{self.resilience_preset}': {e}")
                
                # Record configuration error
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
        """Load resilience configuration from legacy environment variables."""
        from app.services.resilience import ResilienceConfig, RetryConfig, CircuitBreakerConfig, ResilienceStrategy
        
        # Map legacy strategy strings to enum values
        strategy_mapping = {
            "aggressive": ResilienceStrategy.AGGRESSIVE,
            "balanced": ResilienceStrategy.BALANCED,
            "conservative": ResilienceStrategy.CONSERVATIVE,
            "critical": ResilienceStrategy.CRITICAL
        }
        
        # Read values directly from environment variables, with fallbacks to field values
        default_strategy_str = os.getenv("DEFAULT_RESILIENCE_STRATEGY", self.default_resilience_strategy)
        default_strategy = strategy_mapping.get(default_strategy_str, ResilienceStrategy.BALANCED)
        
        # Helper function to safely convert environment variables with fallbacks
        def safe_int(env_var: str, fallback: int) -> int:
            try:
                value = os.getenv(env_var)
                if value is None:
                    return fallback
                result = int(value)
                # Validate positive values for certain fields
                if env_var in ["RETRY_MAX_ATTEMPTS", "CIRCUIT_BREAKER_FAILURE_THRESHOLD", "CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "RETRY_MAX_DELAY"] and result <= 0:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid negative/zero value for {env_var}: {result}, using fallback: {fallback}")
                    return fallback
                return result
            except (ValueError, TypeError):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Invalid value for {env_var}: {os.getenv(env_var)}, using fallback: {fallback}")
                return fallback
        
        def safe_float(env_var: str, fallback: float) -> float:
            try:
                value = os.getenv(env_var)
                if value is None:
                    return fallback
                result = float(value)
                # Validate positive values for certain fields
                if env_var in ["RETRY_EXPONENTIAL_MULTIPLIER", "RETRY_EXPONENTIAL_MIN", "RETRY_EXPONENTIAL_MAX", "RETRY_JITTER_MAX"] and result <= 0:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid negative/zero value for {env_var}: {result}, using fallback: {fallback}")
                    return fallback
                return result
            except (ValueError, TypeError):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Invalid value for {env_var}: {os.getenv(env_var)}, using fallback: {fallback}")
                return fallback
        
        # Read retry configuration from environment with safe conversion
        retry_max_attempts = safe_int("RETRY_MAX_ATTEMPTS", self.retry_max_attempts)
        retry_max_delay = safe_int("RETRY_MAX_DELAY", self.retry_max_delay)
        retry_exponential_multiplier = safe_float("RETRY_EXPONENTIAL_MULTIPLIER", self.retry_exponential_multiplier)
        retry_exponential_min = safe_float("RETRY_EXPONENTIAL_MIN", self.retry_exponential_min)
        retry_exponential_max = safe_float("RETRY_EXPONENTIAL_MAX", self.retry_exponential_max)
        retry_jitter_enabled = os.getenv("RETRY_JITTER_ENABLED", str(self.retry_jitter_enabled)).lower() in ("true", "1", "yes")
        retry_jitter_max = safe_float("RETRY_JITTER_MAX", self.retry_jitter_max)
        
        # Read circuit breaker configuration from environment with safe conversion
        circuit_breaker_failure_threshold = safe_int("CIRCUIT_BREAKER_FAILURE_THRESHOLD", self.circuit_breaker_failure_threshold)
        circuit_breaker_recovery_timeout = safe_int("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", self.circuit_breaker_recovery_timeout)
        
        # Read feature flags from environment
        circuit_breaker_enabled = os.getenv("CIRCUIT_BREAKER_ENABLED", str(self.circuit_breaker_enabled)).lower() in ("true", "1", "yes")
        retry_enabled = os.getenv("RETRY_ENABLED", str(self.retry_enabled)).lower() in ("true", "1", "yes")
        
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
        """Apply custom configuration overrides to base preset config."""
        from app.services.resilience import ResilienceStrategy, ResilienceConfig, RetryConfig, CircuitBreakerConfig
        from app.validation_schemas import config_validator
        
        # Validate custom configuration
        validation_result = config_validator.validate_custom_config(custom_config)
        if not validation_result.is_valid:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid custom configuration: {validation_result.errors}")
            # Log warnings but continue
            for warning in validation_result.warnings:
                logger.warning(f"Custom configuration warning: {warning}")
            # Return base config without applying invalid overrides
            return base_config
        
        # Log any warnings
        if validation_result.warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in validation_result.warnings:
                logger.warning(f"Custom configuration warning: {warning}")
        
        # Create new configuration objects with overrides applied
        # Start with base config values
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
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Invalid default strategy '{custom_config['default_strategy']}', keeping original")
        
        # Apply operation-specific strategy overrides
        if "operation_overrides" in custom_config:
            for operation, strategy_str in custom_config["operation_overrides"].items():
                try:
                    strategy_enum = ResilienceStrategy(strategy_str)
                    # Note: Operation-specific strategies would be handled by AIServiceResilience
                    # For now, we just validate the strategy is valid
                except ValueError:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid strategy '{strategy_str}' for operation '{operation}'")
        
        # Create new resilience config with all overrides applied
        return ResilienceConfig(
            strategy=strategy,
            retry_config=new_retry_config,
            circuit_breaker_config=new_circuit_breaker_config,
            enable_circuit_breaker=base_config.enable_circuit_breaker,
            enable_retry=base_config.enable_retry
        )

    def validate_custom_config(self, json_string: Optional[str] = None) -> dict:
        """
        Validate custom resilience configuration.
        
        Args:
            json_string: JSON string to validate (if None, uses current resilience_custom_config)
            
        Returns:
            Dictionary with validation results
        """
        from app.validation_schemas import config_validator
        
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

    def get_operation_strategy(self, operation: str) -> str:
        """
        Get resilience strategy for a specific operation.
        
        Args:
            operation: Operation name (summarize, sentiment, key_points, questions, qa)
            
        Returns:
            Strategy name as string
        """
        # If using legacy configuration, return operation-specific strategy
        if self._has_legacy_resilience_config():
            # Read operation strategies directly from environment variables
            env_var_mapping = {
                "summarize": "SUMMARIZE_RESILIENCE_STRATEGY",
                "sentiment": "SENTIMENT_RESILIENCE_STRATEGY", 
                "key_points": "KEY_POINTS_RESILIENCE_STRATEGY",
                "questions": "QUESTIONS_RESILIENCE_STRATEGY",
                "qa": "QA_RESILIENCE_STRATEGY"
            }
            
            # Get the environment variable for this operation
            env_var = env_var_mapping.get(operation)
            if env_var and os.getenv(env_var):
                return os.getenv(env_var)
            
            # Fall back to field values if environment variable not set
            operation_strategies = {
                "summarize": self.summarize_resilience_strategy,
                "sentiment": self.sentiment_resilience_strategy,
                "key_points": self.key_points_resilience_strategy,
                "questions": self.questions_resilience_strategy,
                "qa": self.qa_resilience_strategy
            }
            return operation_strategies.get(operation, self.default_resilience_strategy)
        
        # For preset configuration, get operation override or default
        try:
            from app.resilience_presets import preset_manager
            preset = preset_manager.get_preset(self.resilience_preset)
            
            # Check for custom configuration overrides first
            env_custom_config = os.getenv("RESILIENCE_CUSTOM_CONFIG")
            custom_config_json = env_custom_config if env_custom_config else self.resilience_custom_config
            
            if custom_config_json:
                try:
                    custom_config = json.loads(custom_config_json)
                    operation_overrides = custom_config.get("operation_overrides", {})
                    if operation in operation_overrides:
                        return operation_overrides[operation]
                except json.JSONDecodeError:
                    pass  # Fall through to preset logic
            
            # Check for operation-specific override in preset
            if operation in preset.operation_overrides:
                return preset.operation_overrides[operation].value
            else:
                return preset.default_strategy.value
                
        except Exception:
            return "balanced"  # Safe fallback


# Global settings instance for dependency injection
settings = Settings()