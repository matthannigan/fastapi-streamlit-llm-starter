"""
Cache configuration presets and strategy management system.

This module provides a comprehensive preset system for managing cache configurations
across different deployment environments, reducing complexity by replacing dozens of
individual environment variables with simple preset selections.

## Core Components

- **CacheStrategy**: Enum defining cache strategies (fast, balanced, robust, ai_optimized)
- **CacheConfig**: Main configuration combining Redis settings and AI features
- **CachePreset**: Predefined configuration templates for deployment scenarios
- **CachePresetManager**: Advanced manager with validation and environment detection

## Preset System

- **Predefined Presets**: Common scenarios (disabled, development, production, ai-production)
- **Environment Detection**: Automatic environment detection and recommendations
- **Confidence Scoring**: Environment-aware preset recommendations with confidence levels
- **Pattern Matching**: Intelligent environment classification for complex deployments

## Strategy Configurations

- **Optimized Defaults**: Strategy presets with optimal TTL, compression, and connection settings
- **AI Optimizations**: Specialized configurations for text processing and AI workloads
- **Validation**: Comprehensive configuration integrity validation

## Key Features

- **Simplified Setup**: Single preset replaces 28+ individual environment variables
- Intelligent environment detection and preset recommendation
- Comprehensive validation with fallback to basic validation
- Pattern matching for complex environment naming schemes
- Extensible preset system for custom deployment scenarios

**Usage:**
- Use preset_manager.recommend_preset() for automatic environment-based selection
- Access predefined presets via CACHE_PRESETS dictionary or preset_manager.get_preset()
- Convert presets to full CacheConfig objects via to_cache_config()
- Leverage DEFAULT_PRESETS for direct strategy-based configuration access

This module serves as the central configuration hub for all cache-related
settings across the application, providing both simplified preset-based configuration
and advanced customization capabilities.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, NamedTuple
from enum import Enum
import logging
import os
import re

logger = logging.getLogger(__name__)


class EnvironmentRecommendation(NamedTuple):
    """Environment-based preset recommendation with confidence and reasoning."""
    preset_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    environment_detected: str


class CacheStrategy(str, Enum):
    """
    Cache strategy enumeration defining optimized configurations for different deployment scenarios.

    Provides predefined strategy types that automatically configure TTL values, compression settings,
    and performance parameters for common deployment patterns. Each strategy balances performance,
    reliability, and resource usage for specific use cases.

    Values:
        FAST: Development and testing strategy with minimal TTLs (60-300s) and fast access
        BALANCED: Production default with moderate TTLs (3600-7200s) and balanced performance
        ROBUST: High-reliability strategy with extended TTLs (7200-86400s) for stability
        AI_OPTIMIZED: AI workload strategy with text hashing and intelligent caching (1800-14400s)

    Behavior:
        - String enum supporting direct comparison and serialization
        - Each strategy maps to specific configuration parameters in DEFAULT_PRESETS
        - Provides consistent configuration across different deployment environments
        - Enables easy strategy switching without manual parameter tuning

    Examples:
        >>> strategy = CacheStrategy.BALANCED
        >>> print(f"Using {strategy} strategy")
        Using balanced strategy

        >>> # Strategy-based configuration
        >>> config = DEFAULT_PRESETS[CacheStrategy.AI_OPTIMIZED]
        >>> print(f"Default TTL: {config.default_ttl}s")

        >>> # Environment-based strategy selection
        >>> if is_production():
        ...     strategy = CacheStrategy.ROBUST
        ... else:
        ...     strategy = CacheStrategy.FAST
    """
    FAST = "fast"                    # Fast access, minimal TTLs, development-friendly
    BALANCED = "balanced"            # Default strategy, balanced TTL and performance
    ROBUST = "robust"               # Long TTLs, high reliability, production-ready
    AI_OPTIMIZED = "ai_optimized"   # AI-specific optimizations with text hashing


@dataclass
class CacheConfig:
    """
    Comprehensive cache configuration with Redis settings, performance tuning, and AI optimizations.

    Provides complete configuration management for cache systems with validation, environment
    integration, and strategy-based presets. Supports both simple Redis caching and advanced
    AI-optimized configurations with text processing capabilities.

    Attributes:
        strategy: CacheStrategy enum defining the caching approach and default parameters
        redis_url: Optional[str] Redis connection URL (redis://, rediss://, unix://)
        redis_password: Optional[str] Redis authentication password
        use_tls: bool enable TLS encryption for Redis connections
        tls_cert_path: Optional[str] path to TLS certificate file
        default_ttl: int default time-to-live in seconds (60-86400)
        enable_compression: bool enable automatic data compression
        compression_threshold: int bytes threshold for triggering compression (1024-65536)
        max_connections: int maximum Redis connection pool size (1-100)
        connection_timeout: int connection timeout in seconds (1-30)
        enable_ai_features: bool enable AI-specific caching optimizations
        text_hash_threshold: int character threshold for text hashing (500-10000)
        operation_specific_ttls: Dict[str, int] TTL overrides per operation type

    State Management:
        - Immutable configuration after creation for consistent behavior
        - Validation methods ensure configuration integrity
        - Strategy-based defaults provide production-ready configurations
        - Environment integration supports deployment-specific customization

    Usage:
        # Strategy-based configuration
        config = CacheConfig(strategy=CacheStrategy.AI_OPTIMIZED)

        # Custom configuration with overrides
        config = CacheConfig(
            strategy=CacheStrategy.BALANCED,
            redis_url="redis://cache-cluster:6379",
            default_ttl=7200,
            enable_ai_features=True
        )

        # Production configuration with security
        config = CacheConfig(
            strategy=CacheStrategy.ROBUST,
            use_tls=True,
            tls_cert_path="/etc/ssl/redis.crt",
            redis_password=os.environ["REDIS_PASSWORD"]
        )
    """
    strategy: CacheStrategy = CacheStrategy.BALANCED

    # Redis configuration
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    max_connections: int = 10
    connection_timeout: int = 5

    # Cache behavior
    default_ttl: int = 3600  # 1 hour
    memory_cache_size: int = 100
    compression_threshold: int = 1000
    compression_level: int = 6

    # AI features
    enable_ai_cache: bool = False
    text_hash_threshold: int = 1000
    hash_algorithm: str = "sha256"
    text_size_tiers: Dict[str, int] = field(default_factory=lambda: {
        "small": 1000,
        "medium": 5000,
        "large": 20000
    })
    operation_ttls: Dict[str, int] = field(default_factory=lambda: {
        "summarize": 7200,  # 2 hours
        "sentiment": 3600,  # 1 hour
        "key_points": 5400,  # 1.5 hours
        "questions": 4800,  # 1.33 hours
        "qa": 3600         # 1 hour
    })
    enable_smart_promotion: bool = True
    max_text_length: int = 100000

    # Monitoring and logging
    enable_monitoring: bool = True
    log_level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for factory usage."""
        config_dict = asdict(self)

        # Convert enum to string for JSON serialization
        config_dict["strategy"] = self.strategy.value

        # Create SecurityConfig from security-related fields
        security_config = None
        if any([config_dict["redis_password"], config_dict["use_tls"], 
                config_dict["tls_cert_path"], config_dict["tls_key_path"]]):
            try:
                from app.infrastructure.cache.security import SecurityConfig
                security_config = SecurityConfig(
                    redis_auth=config_dict["redis_password"],
                    use_tls=config_dict["use_tls"],
                    tls_cert_path=config_dict["tls_cert_path"],
                    tls_key_path=config_dict["tls_key_path"],
                    connection_timeout=config_dict["connection_timeout"],
                    max_retries=3  # Default retry attempts
                )
            except ImportError as e:
                # SecurityConfig not available, fall back to individual parameters
                # This maintains compatibility during development/testing
                security_config = None
            except Exception as e:
                # SecurityConfig creation failed, fall back to individual parameters
                security_config = None
        
        # Map fields to factory-expected names
        factory_dict = {
            # Redis configuration (core connectivity)
            "redis_url": config_dict["redis_url"],
            
            # Security configuration (proper architecture)
            "security_config": security_config,

            # Cache behavior (factory expects these names)
            "default_ttl": config_dict["default_ttl"],
            "l1_cache_size": config_dict["memory_cache_size"],  # Factory expects l1_cache_size
            "enable_l1_cache": True,  # Enable L1 cache by default
            "compression_threshold": config_dict["compression_threshold"],
            "compression_level": config_dict["compression_level"],

            # AI features (only include if AI is enabled)
            "text_hash_threshold": config_dict["text_hash_threshold"] if config_dict["enable_ai_cache"] else None,
            "operation_ttls": config_dict["operation_ttls"] if config_dict["enable_ai_cache"] else None,
            "text_size_tiers": config_dict["text_size_tiers"] if config_dict["enable_ai_cache"] else None,
            "hash_algorithm": config_dict["hash_algorithm"] if config_dict["enable_ai_cache"] else None,
            "enable_smart_promotion": config_dict["enable_smart_promotion"] if config_dict["enable_ai_cache"] else None,
            "max_text_length": config_dict["max_text_length"] if config_dict["enable_ai_cache"] else None,

            # Additional factory parameters
            "enable_ai_cache": config_dict["enable_ai_cache"],
            "enable_monitoring": config_dict["enable_monitoring"],
            "log_level": config_dict["log_level"],

            # Strategy for logging/debugging
            "cache_strategy": config_dict["strategy"]
        }

        # Remove None values to avoid passing them to factory
        factory_dict = {k: v for k, v in factory_dict.items() if v is not None}

        return factory_dict

    def validate(self):
        """
        Validate cache configuration settings.

        Returns:
            ValidationResult with any errors or warnings found
        """
        try:
            from app.infrastructure.cache.cache_validator import cache_validator
            return cache_validator.validate_configuration(self.to_dict())
        except ImportError:
            # Fallback to basic validation if validator not available
            return self._basic_validate()

    def _basic_validate(self):
        """Basic configuration validation without full validator."""
        from app.infrastructure.cache.cache_validator import ValidationResult

        result = ValidationResult(is_valid=True, validation_type="basic")

        # Validate TTL
        if self.default_ttl < 60 or self.default_ttl > 604800:
            result.add_error("default_ttl must be between 60 and 604800 seconds")

        # Validate connections
        if self.max_connections < 1 or self.max_connections > 100:
            result.add_error("max_connections must be between 1 and 100")

        # Validate timeout
        if self.connection_timeout < 1 or self.connection_timeout > 60:
            result.add_error("connection_timeout must be between 1 and 60 seconds")

        # Validate cache size
        if self.memory_cache_size < 1 or self.memory_cache_size > 10000:
            result.add_error("memory_cache_size must be between 1 and 10000")

        # Validate compression
        if self.compression_level < 1 or self.compression_level > 9:
            result.add_error("compression_level must be between 1 and 9")

        return result


@dataclass
class CachePreset:
    """
    Predefined cache configuration preset with validation and environment-specific optimization.

    Encapsulates complete cache configuration including Redis settings, performance parameters,
    and AI-specific features for streamlined deployment across different environments.
    Provides validation, conversion methods, and intelligent defaults.

    Attributes:
        name: str unique preset identifier for reference and logging
        description: str human-readable preset description for documentation
        strategy: CacheStrategy base strategy defining performance characteristics
        redis_settings: Dict[str, Any] Redis connection and performance parameters
        performance_settings: Dict[str, Any] caching performance and optimization settings
        ai_settings: Dict[str, Any] AI-specific configuration for text processing

    Public Methods:
        to_cache_config(): Convert preset to full CacheConfig instance
        validate(): Validate preset configuration integrity
        merge_with(): Merge with another preset for configuration inheritance

    State Management:
        - Immutable preset configuration after initialization
        - Comprehensive validation with detailed error reporting
        - Environment-specific parameter optimization
        - Strategy-based intelligent defaults

    Usage:
        # Access predefined presets
        preset = CACHE_PRESETS['production']
        config = preset.to_cache_config()

        # Custom preset creation
        custom_preset = CachePreset(
            name="high_performance",
            description="High-performance caching for real-time applications",
            strategy=CacheStrategy.FAST,
            redis_settings={
                "max_connections": 50,
                "connection_timeout": 5
            }
        )

        # Preset validation and conversion
        if custom_preset.validate():
            cache_config = custom_preset.to_cache_config()
            cache = initialize_cache(cache_config)
    """
    name: str
    description: str
    strategy: CacheStrategy
    default_ttl: int
    max_connections: int
    connection_timeout: int
    memory_cache_size: int
    compression_threshold: int
    compression_level: int
    enable_ai_cache: bool
    enable_monitoring: bool
    log_level: str
    environment_contexts: List[str]
    ai_optimizations: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization."""
        return asdict(self)

    def to_cache_config(self):
        """Convert preset to cache configuration object compatible with config.py CacheConfig."""
        # Import the actual CacheConfig from config.py to ensure compatibility
        from app.infrastructure.cache.config import CacheConfig as ConfigCacheConfig, AICacheConfig

        # Create AI configuration if AI features are enabled
        ai_config = None
        if self.enable_ai_cache:
            ai_config = AICacheConfig(
                text_hash_threshold=self.ai_optimizations.get('text_hash_threshold', 1000),
                hash_algorithm=self.ai_optimizations.get('hash_algorithm', 'sha256'),
                text_size_tiers=self.ai_optimizations.get('text_size_tiers', {
                    "small": 1000,
                    "medium": 5000,
                    "large": 20000
                }),
                operation_ttls=self.ai_optimizations.get('operation_ttls', {
                    "summarize": 7200,
                    "sentiment": 3600,
                    "key_points": 5400,
                    "questions": 4800,
                    "qa": 3600
                }),
                enable_smart_promotion=self.ai_optimizations.get('enable_smart_promotion', True),
                max_text_length=self.ai_optimizations.get('max_text_length', 100000)
            )

        # Create base configuration using config.py CacheConfig structure
        config = ConfigCacheConfig(
            # Redis configuration (no strategy field in config.py CacheConfig)
            redis_url=None,  # Will be set by environment overrides
            redis_password=None,
            use_tls=False,
            tls_cert_path=None,
            tls_key_path=None,

            # Cache behavior
            default_ttl=self.default_ttl,
            memory_cache_size=self.memory_cache_size,
            compression_threshold=self.compression_threshold,
            compression_level=self.compression_level,

            # Environment
            environment=self.environment_contexts[0] if self.environment_contexts else "development",

            # AI configuration (nested structure)
            ai_config=ai_config,
            enable_ai_cache=self.enable_ai_cache
        )

        return config


# Preset definitions based on PRD specifications
CACHE_PRESETS = {
    "disabled": CachePreset(
        name="Disabled",
        description="Cache completely disabled, no Redis connection, memory-only fallback",
        strategy=CacheStrategy.FAST,
        default_ttl=300,     # 5 minutes for minimal memory usage
        max_connections=1,    # Minimal connection pool
        connection_timeout=1,  # Fast timeout
        memory_cache_size=10,  # Very small memory cache
        compression_threshold=10000,  # High threshold, minimal compression
        compression_level=1,  # Minimal compression
        enable_ai_cache=False,
        enable_monitoring=False,
        log_level="WARNING",
        environment_contexts=["testing", "minimal"],
        ai_optimizations={}
    ),

    "minimal": CachePreset(
        name="Minimal",
        description="Ultra-lightweight caching for resource-constrained environments",
        strategy=CacheStrategy.FAST,
        default_ttl=900,     # 15 minutes - longer than disabled but still short
        max_connections=2,   # Very minimal connection pool
        connection_timeout=3,  # Short timeout to avoid hanging
        memory_cache_size=25,  # Small but functional memory cache
        compression_threshold=5000,  # High threshold, minimal compression usage
        compression_level=1,  # Fastest compression level
        enable_ai_cache=False,  # No AI features to save resources
        enable_monitoring=False,  # Minimal monitoring to save overhead
        log_level="ERROR",   # Only log errors to reduce I/O
        environment_contexts=["minimal", "embedded", "iot", "container", "serverless"],
        ai_optimizations={}
    ),

    "simple": CachePreset(
        name="Simple",
        description="Basic cache configuration suitable for most use cases",
        strategy=CacheStrategy.BALANCED,
        default_ttl=3600,    # 1 hour
        max_connections=5,
        connection_timeout=5,
        memory_cache_size=100,
        compression_threshold=1000,
        compression_level=6,
        enable_ai_cache=False,
        enable_monitoring=True,
        log_level="INFO",
        environment_contexts=["development", "testing", "staging", "production"],
        ai_optimizations={}
    ),

    "development": CachePreset(
        name="Development",
        description="Fast-feedback configuration optimized for development speed",
        strategy=CacheStrategy.FAST,
        default_ttl=600,     # 10 minutes for quick development cycles
        max_connections=3,   # Minimal connections for local development
        connection_timeout=2,  # Fast timeout for quick feedback
        memory_cache_size=50,  # Smaller cache for memory efficiency
        compression_threshold=2000,  # Higher threshold, less CPU usage
        compression_level=3,  # Lower compression for speed
        enable_ai_cache=False,
        enable_monitoring=True,
        log_level="DEBUG",   # Detailed logging for development
        environment_contexts=["development", "local"],
        ai_optimizations={}
    ),

    "production": CachePreset(
        name="Production",
        description="High-performance configuration for production workloads",
        strategy=CacheStrategy.ROBUST,
        default_ttl=7200,    # 2 hours for production efficiency
        max_connections=20,   # High connection pool for production load
        connection_timeout=10,  # Longer timeout for reliability
        memory_cache_size=500,  # Large memory cache for performance
        compression_threshold=500,  # Low threshold, aggressive compression
        compression_level=9,  # Maximum compression for network efficiency
        enable_ai_cache=False,
        enable_monitoring=True,
        log_level="INFO",
        environment_contexts=["production", "staging"],
        ai_optimizations={}
    ),

    "ai-development": CachePreset(
        name="AI Development",
        description="AI-optimized configuration for development with text processing features",
        strategy=CacheStrategy.AI_OPTIMIZED,
        default_ttl=1800,    # 30 minutes for AI development
        max_connections=5,   # Moderate connections
        connection_timeout=5,
        memory_cache_size=100,
        compression_threshold=1000,
        compression_level=6,
        enable_ai_cache=True,
        enable_monitoring=True,
        log_level="DEBUG",
        environment_contexts=["development", "ai-development"],
        ai_optimizations={
            "text_hash_threshold": 500,  # Lower threshold for development
            "hash_algorithm": "sha256",
            "text_size_tiers": {
                "small": 500,
                "medium": 2000,
                "large": 10000
            },
            "operation_ttls": {
                "summarize": 1800,  # 30 minutes for development
                "sentiment": 900,   # 15 minutes
                "key_points": 1200,  # 20 minutes
                "questions": 1500,  # 25 minutes
                "qa": 900          # 15 minutes
            },
            "enable_smart_promotion": True,
            "max_text_length": 50000
        }
    ),

    "ai-production": CachePreset(
        name="AI Production",
        description="AI-optimized configuration for production with advanced text processing",
        strategy=CacheStrategy.AI_OPTIMIZED,
        default_ttl=14400,   # 4 hours for production AI workloads
        max_connections=25,  # High connection pool for AI workloads
        connection_timeout=15,  # Longer timeout for AI operations
        memory_cache_size=1000,  # Large memory cache for AI data
        compression_threshold=300,  # Aggressive compression for large AI payloads
        compression_level=9,  # Maximum compression
        enable_ai_cache=True,
        enable_monitoring=True,
        log_level="INFO",
        environment_contexts=["production", "ai-production"],
        ai_optimizations={
            "text_hash_threshold": 1000,
            "hash_algorithm": "sha256",
            "text_size_tiers": {
                "small": 1000,
                "medium": 5000,
                "large": 25000
            },
            "operation_ttls": {
                "summarize": 14400,  # 4 hours for production
                "sentiment": 7200,  # 2 hours
                "key_points": 10800,  # 3 hours
                "questions": 9600,  # 2.67 hours
                "qa": 7200         # 2 hours
            },
            "enable_smart_promotion": True,
            "max_text_length": 200000
        }
    )
}


class CachePresetManager:
    """
    Manager for cache presets with validation and recommendation capabilities.
    """

    def __init__(self):
        """Initialize preset manager with default presets."""
        self.presets = CACHE_PRESETS.copy()
        logger.info(f"Initialized CachePresetManager with {len(self.presets)} presets")

    def get_preset(self, name: str) -> CachePreset:
        """
        Get preset by name with validation.

        Args:
            name: Preset name (disabled, simple, development, production, ai-development, ai-production)

        Returns:
            CachePreset object

        Raises:
            ValueError: If preset name is not found
        """
        if name not in self.presets:
            from app.core.exceptions import ConfigurationError
            available = list(self.presets.keys())
            raise ConfigurationError(
                f"Unknown preset '{name}'. Available presets: {available}",
                context={"requested_preset": name, "available": available}
            )
        return self.presets[name]

    def list_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list(self.presets.keys())

    def get_preset_details(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a preset."""
        preset = self.get_preset(name)
        return {
            "name": preset.name,
            "description": preset.description,
            "configuration": {
                "strategy": preset.strategy.value,
                "default_ttl": preset.default_ttl,
                "max_connections": preset.max_connections,
                "memory_cache_size": preset.memory_cache_size,
                "enable_ai_cache": preset.enable_ai_cache,
                "enable_monitoring": preset.enable_monitoring,
                "log_level": preset.log_level
            },
            "environment_contexts": preset.environment_contexts,
            "ai_optimizations": preset.ai_optimizations if preset.enable_ai_cache else None
        }

    def validate_preset(self, preset: CachePreset) -> bool:
        """
        Validate preset configuration values.

        Args:
            preset: Preset to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            from app.infrastructure.cache.cache_validator import cache_validator

            # Convert preset to dict for validation
            preset_dict = preset.to_dict()

            # Use JSON schema validation if available
            validation_result = cache_validator.validate_preset(preset_dict)

            if not validation_result.is_valid:
                for error in validation_result.errors:
                    logger.error(f"Cache preset validation error: {error}")
                return False

            # Log any warnings
            for warning in validation_result.warnings:
                logger.warning(f"Cache preset validation warning: {warning}")

            return True

        except ImportError:
            # Fallback to basic validation if cache_validator not available
            return self._basic_validate_preset(preset)

    def _basic_validate_preset(self, preset: CachePreset) -> bool:
        """Basic preset validation without JSON schema."""
        # Validate TTL
        if preset.default_ttl < 1 or preset.default_ttl > 604800:  # 1 second to 1 week
            logger.error(f"Invalid default_ttl: {preset.default_ttl} (must be 1-604800)")
            return False

        # Validate connection settings
        if preset.max_connections < 1 or preset.max_connections > 100:
            logger.error(f"Invalid max_connections: {preset.max_connections} (must be 1-100)")
            return False

        if preset.connection_timeout < 1 or preset.connection_timeout > 60:
            logger.error(f"Invalid connection_timeout: {preset.connection_timeout} (must be 1-60)")
            return False

        # Validate cache size
        if preset.memory_cache_size < 1 or preset.memory_cache_size > 10000:
            logger.error(f"Invalid memory_cache_size: {preset.memory_cache_size} (must be 1-10000)")
            return False

        # Validate compression settings
        if preset.compression_level < 1 or preset.compression_level > 9:
            logger.error(f"Invalid compression_level: {preset.compression_level} (must be 1-9)")
            return False

        # Validate AI optimizations if AI is enabled
        if preset.enable_ai_cache and preset.ai_optimizations:
            operation_ttls = preset.ai_optimizations.get('operation_ttls', {})
            for operation, ttl in operation_ttls.items():
                if not isinstance(ttl, int) or ttl < 1:
                    logger.error(f"Invalid AI operation TTL for {operation}: {ttl}")
                    return False

        return True

    def recommend_preset(self, environment: Optional[str] = None) -> str:
        """
        Recommend appropriate preset for given environment.

        Args:
            environment: Environment name (dev, test, staging, prod, etc.)
            If None, will auto-detect from environment variables

        Returns:
            Recommended preset name
        """
        recommendation = self.recommend_preset_with_details(environment)
        return recommendation.preset_name

    def recommend_preset_with_details(self, environment: Optional[str] = None) -> EnvironmentRecommendation:
        """
        Get detailed environment-aware preset recommendation.

        Args:
            environment: Environment name or None for auto-detection

        Returns:
            EnvironmentRecommendation with preset, confidence, and reasoning
        """
        if environment is None:
            return self._auto_detect_environment()

        env_lower = environment.lower().strip()

        # High-confidence exact matches
        exact_matches = {
            "development": ("development", 0.95, "Exact match for development environment"),
            "dev": ("development", 0.90, "Standard abbreviation for development"),
            "testing": ("development", 0.85, "Testing typically uses development-like settings"),
            "test": ("development", 0.85, "Test environment should fail fast"),
            "staging": ("production", 0.90, "Staging should mirror production settings"),
            "stage": ("production", 0.85, "Stage environment abbreviation"),
            "production": ("production", 0.95, "Exact match for production environment"),
            "prod": ("production", 0.90, "Standard abbreviation for production"),
            "live": ("production", 0.85, "Live environment implies production"),
            "ai-development": ("ai-development", 0.95, "Exact match for AI development"),
            "ai-dev": ("ai-development", 0.90, "AI development abbreviation"),
            "ai-production": ("ai-production", 0.95, "Exact match for AI production"),
            "ai-prod": ("ai-production", 0.90, "AI production abbreviation"),
        }

        if env_lower in exact_matches:
            preset, confidence, reasoning = exact_matches[env_lower]
            return EnvironmentRecommendation(
                preset_name=preset,
                confidence=confidence,
                reasoning=reasoning,
                environment_detected=environment
            )

        # Pattern-based matching for complex environment names
        preset, confidence, reasoning = self._pattern_match_environment(env_lower)

        return EnvironmentRecommendation(
            preset_name=preset,
            confidence=confidence,
            reasoning=reasoning,
            environment_detected=environment
        )

    def _auto_detect_environment(self) -> EnvironmentRecommendation:
        """
        Auto-detect environment from environment variables with deterministic precedence.
        
        Uses explicit environment signals with strict precedence to avoid contamination
        from parallel test execution. Falls back to file system indicators only when
        no explicit environment variables are present.

        Returns:
            EnvironmentRecommendation based on detected environment
        """
        # Check for AI cache enablement first
        enable_ai = os.getenv('ENABLE_AI_CACHE', '').lower() in ('true', '1', 'yes')

        # Define explicit environment variables in strict precedence order
        # Only consider the highest priority variable that is present
        env_sources = [
            ('ENVIRONMENT', os.getenv('ENVIRONMENT')),
            ('NODE_ENV', os.getenv('NODE_ENV')),
            ('FLASK_ENV', os.getenv('FLASK_ENV')),
            ('APP_ENV', os.getenv('APP_ENV')),
            ('ENV', os.getenv('ENV')),
            ('DEPLOYMENT_ENV', os.getenv('DEPLOYMENT_ENV')),
            ('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE')),
            ('RAILS_ENV', os.getenv('RAILS_ENV'))
        ]

        # Find the first (highest priority) explicit environment signal
        for source_name, env_value in env_sources:
            if not env_value:
                continue
                
            env_lower = env_value.lower().strip()
            
            # Handle AI-specific environment values (ENVIRONMENT with "ai")
            if source_name == 'ENVIRONMENT' and 'ai' in env_lower:
                if any(prod_indicator in env_lower for prod_indicator in ['prod', 'production', 'live']):
                    base_preset = 'ai-production'
                    reasoning = f"Explicit AI production environment from {source_name}={env_value}"
                    confidence = 0.90
                else:
                    base_preset = 'ai-development'
                    reasoning = f"Explicit AI development environment from {source_name}={env_value}"
                    confidence = 0.90
                    
                return EnvironmentRecommendation(
                    preset_name=base_preset,
                    confidence=confidence,
                    reasoning=reasoning,
                    environment_detected=f"{env_value} (auto-detected)"
                )
            
            # Handle standard environment values
            # Use the pattern matching logic for the detected environment
            details = self.recommend_preset_with_details(env_lower)
            base_rec = EnvironmentRecommendation(
                preset_name=details.preset_name,
                confidence=min(0.90, details.confidence),  # Cap at 0.90 for explicit env vars
                reasoning=f"{details.reasoning} (from {source_name}={env_value})",
                environment_detected=f"{env_value} (auto-detected)"
            )
            
            # Apply AI override if enabled and not already AI preset
            if enable_ai and not base_rec.preset_name.startswith('ai-'):
                ai_preset = f"ai-{base_rec.preset_name}"
                if ai_preset in self.presets:
                    return EnvironmentRecommendation(
                        preset_name=ai_preset,
                        confidence=base_rec.confidence,
                        reasoning=f"{base_rec.reasoning} with ENABLE_AI_CACHE=true",
                        environment_detected=f"{env_value} (auto-detected, AI-enabled)"
                    )
            
            return base_rec

        # Only if NO explicit environment variables found, check system indicators
        # This prevents contamination from stray environment variables in parallel tests
        
        # Check for production indicators first (higher precedence)
        prod_indicators = [
            os.getenv('PRODUCTION', '').lower() == 'true',
            os.getenv('PROD', '').lower() == 'true',  
            os.getenv('DEBUG', '').lower() == 'false',
            os.getenv('DEBUG') == '0',
        ]

        if any(prod_indicators):
            preset_name = "ai-production" if enable_ai else "production"
            return EnvironmentRecommendation(
                preset_name=preset_name,
                confidence=0.65,  # Moderate confidence for generic indicators
                reasoning="Production indicators detected (PRODUCTION=true, DEBUG=false, etc.)",
                environment_detected="production (auto-detected from system flags)"
            )
        
        # Check for development indicators (only basic, reliable indicators)
        dev_indicators = [
            os.getenv('DEBUG', '').lower() == 'true',
            os.getenv('DEBUG') == '1',
            os.path.exists('.env'),  # Local development file
            os.path.exists('.git'),  # Local development repository
        ]

        if any(dev_indicators):
            preset_name = "ai-development" if enable_ai else "development"
            return EnvironmentRecommendation(
                preset_name=preset_name,
                confidence=0.60,  # Lower confidence for file-based detection
                reasoning="Development indicators detected (DEBUG=true, .env file, .git directory)",
                environment_detected="development (auto-detected from system flags)"
            )

        # Fallback to simple cache preset if no other signals
        cache_preset = os.getenv('CACHE_PRESET')
        if cache_preset and cache_preset in self.presets:
            return EnvironmentRecommendation(
                preset_name=cache_preset,
                confidence=0.60,
                reasoning=f"Using explicit CACHE_PRESET={cache_preset} as fallback override",
                environment_detected=f"{cache_preset} (CACHE_PRESET)"
            )

        # Default fallback
        preset_name = "ai-development" if enable_ai else "simple"
        return EnvironmentRecommendation(
            preset_name=preset_name,
            confidence=0.50,
            reasoning="No clear environment indicators found, using simple preset as safe default",
            environment_detected="unknown (auto-detected)"
        )

    def _pattern_match_environment(self, env_str: str) -> tuple[str, float, str]:
        """
        Use pattern matching to classify environment strings.

        Args:
            env_str: Environment string to classify

        Returns:
            Tuple of (preset_name, confidence, reasoning)
        """
        # Check for AI patterns first
        if 'ai' in env_str:
            # AI Production patterns
            ai_prod_patterns = [
                r'.*ai.*prod.*',
                r'.*ai.*production.*',
                r'.*ai.*live.*'
            ]

            for pattern in ai_prod_patterns:
                if re.match(pattern, env_str, re.IGNORECASE):
                    return ("ai-production", 0.80, f"Environment name '{env_str}' matches AI production pattern")

            # AI Development patterns (default for AI environments)
            return ("ai-development", 0.75, f"Environment name '{env_str}' contains 'ai', using AI development preset")

        # Staging patterns (check first to avoid conflicts with other patterns)
        staging_patterns = [
            r'.*stag.*',
            r'.*pre-?prod.*',
            r'.*preprod.*',
            r'.*uat.*',
            r'.*integration.*'
        ]

        for pattern in staging_patterns:
            if re.match(pattern, env_str, re.IGNORECASE):
                return ("production", 0.70, f"Environment name '{env_str}' matches staging pattern, using production preset")

        # Development patterns
        dev_patterns = [
            r'.*dev.*',
            r'.*local.*',
            r'.*test.*',
            r'.*sandbox.*',
            r'.*demo.*'
        ]

        for pattern in dev_patterns:
            if re.match(pattern, env_str, re.IGNORECASE):
                return ("development", 0.75, f"Environment name '{env_str}' matches development pattern")

        # Production patterns
        prod_patterns = [
            r'.*prod.*',
            r'.*live.*',
            r'.*release.*',
            r'.*stable.*',
            r'.*main.*',
            r'.*master.*'
        ]

        for pattern in prod_patterns:
            if re.match(pattern, env_str, re.IGNORECASE):
                return ("production", 0.75, f"Environment name '{env_str}' matches production pattern")

        # Unknown pattern
        return ("simple", 0.40, f"Unknown environment pattern '{env_str}', defaulting to simple preset")

    def get_all_presets_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all available presets."""
        summary = {}
        for name in self.presets.keys():
            summary[name] = self.get_preset_details(name)
        return summary


def get_default_presets() -> Dict[CacheStrategy, CacheConfig]:
    """Returns a dictionary of default cache strategy configurations."""
    return {
        CacheStrategy.FAST: CacheConfig(
            strategy=CacheStrategy.FAST,
            default_ttl=600,     # 10 minutes
            max_connections=3,
            connection_timeout=2,
            memory_cache_size=50,
            compression_threshold=2000,
            compression_level=3,
            enable_monitoring=True,
            log_level="DEBUG"
        ),
        CacheStrategy.BALANCED: CacheConfig(
            strategy=CacheStrategy.BALANCED,
            default_ttl=3600,    # 1 hour
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=100,
            compression_threshold=1000,
            compression_level=6,
            enable_monitoring=True,
            log_level="INFO"
        ),
        CacheStrategy.ROBUST: CacheConfig(
            strategy=CacheStrategy.ROBUST,
            default_ttl=7200,    # 2 hours
            max_connections=20,
            connection_timeout=10,
            memory_cache_size=500,
            compression_threshold=500,
            compression_level=9,
            enable_monitoring=True,
            log_level="INFO"
        ),
        CacheStrategy.AI_OPTIMIZED: CacheConfig(
            strategy=CacheStrategy.AI_OPTIMIZED,
            default_ttl=14400,   # 4 hours
            max_connections=25,
            connection_timeout=15,
            memory_cache_size=1000,
            compression_threshold=300,
            compression_level=9,
            enable_ai_cache=True,
            text_hash_threshold=1000,
            enable_monitoring=True,
            log_level="INFO"
        )
    }


# Default presets for easy access
DEFAULT_PRESETS = get_default_presets()

# Global preset manager instance
cache_preset_manager = CachePresetManager()
