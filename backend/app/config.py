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
        description="Default resilience strategy",
        pattern="^(conservative|balanced|aggressive)$"
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
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for summarize operations"
    )
    sentiment_resilience_strategy: str = Field(
        default="aggressive",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for sentiment analysis"
    )
    key_points_resilience_strategy: str = Field(
        default="balanced",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for key points extraction"
    )
    questions_resilience_strategy: str = Field(
        default="balanced",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for question generation"
    )
    qa_resilience_strategy: str = Field(
        default="conservative",
        pattern="^(conservative|balanced|aggressive)$",
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

    def _has_legacy_resilience_config(self) -> bool:
        """Check if legacy resilience configuration variables are present."""
        legacy_env_vars = [
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "RETRY_MAX_ATTEMPTS",
            "DEFAULT_RESILIENCE_STRATEGY",
            "SUMMARIZE_RESILIENCE_STRATEGY",
            "SENTIMENT_RESILIENCE_STRATEGY",
            "KEY_POINTS_RESILIENCE_STRATEGY",
            "QUESTIONS_RESILIENCE_STRATEGY",
            "QA_RESILIENCE_STRATEGY"
        ]
        
        # Check if any legacy environment variables are set
        for var in legacy_env_vars:
            if os.getenv(var) is not None:
                return True
        
        # Also check if any of the current field values differ from defaults
        # (indicating they were set via environment variables)
        if (self.circuit_breaker_failure_threshold != 5 or
            self.retry_max_attempts != 3 or
            self.default_resilience_strategy != "balanced"):
            return True
            
        return False

    def get_resilience_config(self):
        """
        Get resilience configuration from preset or legacy settings.
        
        Returns appropriate resilience configuration based on:
        1. Legacy environment variables (if present) - for backward compatibility
        2. Custom configuration JSON (if provided)
        3. Preset configuration (default)
        """
        # Import here to avoid circular imports
        from app.resilience_presets import preset_manager
        from app.services.resilience import ResilienceConfig, RetryConfig, CircuitBreakerConfig, ResilienceStrategy
        
        # Check if using legacy configuration
        if self._has_legacy_resilience_config():
            return self._load_legacy_resilience_config()
        
        # Load preset configuration
        try:
            preset = preset_manager.get_preset(self.resilience_preset)
            resilience_config = preset.to_resilience_config()
            
            # Apply custom overrides if provided
            if self.resilience_custom_config:
                try:
                    custom_config = json.loads(self.resilience_custom_config)
                    resilience_config = self._apply_custom_overrides(resilience_config, custom_config)
                except json.JSONDecodeError as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Invalid JSON in resilience_custom_config: {e}")
                    # Fall back to preset without custom config
            
            return resilience_config
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading resilience preset '{self.resilience_preset}': {e}")
            # Fall back to simple preset
            fallback_preset = preset_manager.get_preset("simple")
            return fallback_preset.to_resilience_config()

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
        
        default_strategy = strategy_mapping.get(
            self.default_resilience_strategy, 
            ResilienceStrategy.BALANCED
        )
        
        return ResilienceConfig(
            strategy=default_strategy,
            retry_config=RetryConfig(
                max_attempts=self.retry_max_attempts,
                max_delay_seconds=self.retry_max_delay,
                exponential_multiplier=self.retry_exponential_multiplier,
                exponential_min=self.retry_exponential_min,
                exponential_max=self.retry_exponential_max,
                jitter=self.retry_jitter_enabled,
                jitter_max=self.retry_jitter_max
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=self.circuit_breaker_failure_threshold,
                recovery_timeout=self.circuit_breaker_recovery_timeout
            ),
            enable_circuit_breaker=self.circuit_breaker_enabled,
            enable_retry=self.retry_enabled
        )

    def _apply_custom_overrides(self, base_config, custom_config: dict):
        """Apply custom configuration overrides to base preset config."""
        from app.services.resilience import ResilienceStrategy
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
        
        # Create a copy of the base config
        config = base_config
        
        # Apply retry configuration overrides
        if "retry_attempts" in custom_config:
            config.retry_config.max_attempts = custom_config["retry_attempts"]
            
        if "circuit_breaker_threshold" in custom_config:
            config.circuit_breaker_config.failure_threshold = custom_config["circuit_breaker_threshold"]
            
        if "recovery_timeout" in custom_config:
            config.circuit_breaker_config.recovery_timeout = custom_config["recovery_timeout"]
        
        # Apply exponential backoff overrides
        if "exponential_multiplier" in custom_config:
            config.retry_config.exponential_multiplier = custom_config["exponential_multiplier"]
            
        if "exponential_min" in custom_config:
            config.retry_config.exponential_min = custom_config["exponential_min"]
            
        if "exponential_max" in custom_config:
            config.retry_config.exponential_max = custom_config["exponential_max"]
        
        if "jitter_enabled" in custom_config:
            config.retry_config.jitter = custom_config["jitter_enabled"]
            
        if "jitter_max" in custom_config:
            config.retry_config.jitter_max = custom_config["jitter_max"]
            
        if "max_delay_seconds" in custom_config:
            config.retry_config.max_delay_seconds = custom_config["max_delay_seconds"]
        
        # Apply strategy overrides
        if "default_strategy" in custom_config:
            try:
                config.strategy = ResilienceStrategy(custom_config["default_strategy"])
            except ValueError:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Invalid default strategy '{custom_config['default_strategy']}', keeping original")
        
        # Apply operation-specific strategy overrides
        if "operation_overrides" in custom_config:
            for operation, strategy_str in custom_config["operation_overrides"].items():
                try:
                    strategy = ResilienceStrategy(strategy_str)
                    # Note: Operation-specific strategies would be handled by AIServiceResilience
                    # For now, we just validate the strategy is valid
                except ValueError:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid strategy '{strategy_str}' for operation '{operation}'")
        
        return config

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
            if self.resilience_custom_config:
                try:
                    custom_config = json.loads(self.resilience_custom_config)
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