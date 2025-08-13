"""
AI Response Cache Configuration Module

This module provides the AIResponseCacheConfig dataclass for configuring the
refactored AIResponseCache implementation. It separates AI-specific parameters
from generic Redis parameters and provides validation and conversion methods.

Classes:
    AIResponseCacheConfig: Comprehensive configuration dataclass for AI cache settings

Key Features:
    - **Parameter Separation**: Clearly separates AI-specific from generic Redis parameters
    - **Type Safety**: Full type annotations for all configuration parameters
    - **Validation**: Built-in parameter validation with meaningful error messages
    - **Conversion Methods**: Easy conversion to kwargs for cache initialization
    - **Default Values**: Sensible defaults for production and development use
    - **Comprehensive Documentation**: Google-style docstrings for all parameters

Usage Examples:
    Basic Configuration:
        >>> config = AIResponseCacheConfig(
        ...     redis_url="redis://localhost:6379",
        ...     text_hash_threshold=1000
        ... )
        >>> cache = AIResponseCache(config)

    Advanced Configuration:
        >>> config = AIResponseCacheConfig(
        ...     redis_url="redis://production:6379",
        ...     default_ttl=7200,
        ...     text_hash_threshold=500,
        ...     memory_cache_size=200,
        ...     text_size_tiers={'small': 300, 'medium': 3000, 'large': 30000},
        ...     operation_ttls={'summarize': 14400, 'sentiment': 86400}
        ... )

    Validation:
        >>> config = AIResponseCacheConfig(memory_cache_size=-10)
        >>> config.validate()  # Raises ValidationError

Architecture Context:
    This configuration class supports the Phase 2 refactoring where AIResponseCache
    inherits from GenericRedisCache. It enables clean parameter separation and
    proper initialization of both generic and AI-specific functionality.

Dependencies:
    - dataclasses: For configuration structure
    - typing: For comprehensive type annotations
    - hashlib: For hash algorithm defaults
    - app.core.exceptions: For custom validation exceptions
    - app.infrastructure.cache.monitoring: For performance monitor integration
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from app.core.exceptions import ValidationError, ConfigurationError
from app.infrastructure.cache.monitoring import CachePerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class AIResponseCacheConfig:
    """
    Comprehensive configuration for AI Response Cache with parameter separation.
    
    This dataclass provides a structured approach to configuring the AIResponseCache
    with clear separation between generic Redis parameters and AI-specific parameters.
    It includes validation, type safety, and conversion methods for seamless integration
    with the inheritance-based cache architecture.
    
    ### Generic Redis Parameters
    These parameters are used by the parent GenericRedisCache:
    - `redis_url`: Redis connection URL
    - `default_ttl`: Default time-to-live for cache entries
    - `enable_l1_cache`: Enable in-memory L1 cache tier
    - `l1_cache_size`: Maximum entries in L1 cache (maps from memory_cache_size)
    - `compression_threshold`: Size threshold for compression
    - `compression_level`: Zlib compression level
    - `performance_monitor`: Performance monitoring instance
    - `security_config`: Security configuration for Redis connections
    
    ### AI-Specific Parameters
    These parameters are unique to AI response caching:
    - `text_hash_threshold`: Character threshold for text hashing
    - `hash_algorithm`: Hash algorithm for large texts
    - `text_size_tiers`: Text categorization thresholds
    - `operation_ttls`: TTL values per AI operation type
    
    ### Mapped Parameters
    These AI parameters map to generic equivalents:
    - `memory_cache_size` -> `l1_cache_size`
    
    ### Examples
    ```python
    # Basic configuration
    config = AIResponseCacheConfig(
        redis_url="redis://localhost:6379",
        text_hash_threshold=1000
    )
    
    # Production configuration
    config = AIResponseCacheConfig(
        redis_url="redis://production:6379",
        default_ttl=7200,
        memory_cache_size=200,
        compression_threshold=2000,
        text_size_tiers={'small': 500, 'medium': 5000, 'large': 50000}
    )
    
    # Validate and convert
    config.validate()
    cache_kwargs = config.to_ai_cache_kwargs()
    ```
    """
    
    # Generic Redis Parameters
    redis_url: str = "redis://redis:6379"
    default_ttl: int = 3600  # 1 hour default
    enable_l1_cache: bool = True
    compression_threshold: int = 1000  # 1KB threshold
    compression_level: int = 6  # Balanced compression
    performance_monitor: Optional[CachePerformanceMonitor] = None
    security_config: Optional[Any] = None  # SecurityConfig type - optional import
    
    # AI-Specific Parameters
    text_hash_threshold: int = 1000  # 1000 chars before hashing
    hash_algorithm: Callable = field(default_factory=lambda: hashlib.sha256)
    text_size_tiers: Optional[Dict[str, int]] = None
    operation_ttls: Optional[Dict[str, int]] = None
    
    # Mapped Parameters (AI -> Generic)
    memory_cache_size: int = 100  # Maps to l1_cache_size
    
    def __post_init__(self):
        """
        Post-initialization setup with defaults and validation.
        
        Sets up default values for complex fields and performs basic validation
        to catch configuration errors early in the initialization process.
        
        Raises:
            ConfigurationError: If critical configuration setup fails
        """
        logger.debug("Initializing AIResponseCacheConfig with post-init setup")
        
        try:
            # Set up default text size tiers if not provided
            if self.text_size_tiers is None:
                self.text_size_tiers = {
                    "small": 500,    # < 500 chars - memory cache friendly
                    "medium": 5000,  # 500-5000 chars - standard caching
                    "large": 50000,  # 5000-50000 chars - with compression
                }
                logger.debug("Applied default text_size_tiers")
            
            # Set up default operation TTLs if not provided
            if self.operation_ttls is None:
                self.operation_ttls = {
                    "summarize": 7200,   # 2 hours - summaries are stable
                    "sentiment": 86400,  # 24 hours - sentiment rarely changes
                    "key_points": 7200,  # 2 hours - key points are stable
                    "questions": 3600,   # 1 hour - questions can vary
                    "qa": 1800,          # 30 minutes - context-dependent
                }
                logger.debug("Applied default operation_ttls")
            
            # Ensure L1 cache is enabled if memory_cache_size is specified
            if self.memory_cache_size > 0 and not self.enable_l1_cache:
                self.enable_l1_cache = True
                logger.debug("Auto-enabled L1 cache due to memory_cache_size > 0")
            
            # Create default performance monitor if not provided
            if self.performance_monitor is None:
                self.performance_monitor = CachePerformanceMonitor()
                logger.debug("Created default CachePerformanceMonitor")
            
            logger.info("AIResponseCacheConfig post-init setup completed successfully")
            
        except Exception as e:
            error_msg = f"Failed to setup AIResponseCacheConfig defaults: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={
                    'config_stage': 'post_init',
                    'error_type': type(e).__name__
                }
            )
    
    def validate(self) -> None:
        """
        Validate all configuration parameters comprehensively.
        
        Performs thorough validation of all parameters including type checking,
        value range validation, consistency checks, and dependency validation.
        
        Raises:
            ValidationError: If any configuration parameter is invalid
            
        Examples:
            >>> config = AIResponseCacheConfig(memory_cache_size=-10)
            >>> config.validate()  # Raises ValidationError
            ValidationError: memory_cache_size must be positive, got -10
            
            >>> config = AIResponseCacheConfig(redis_url="invalid://url")
            >>> config.validate()  # Raises ValidationError  
            ValidationError: redis_url must start with redis://, rediss://, or unix://
        """
        logger.debug("Validating AIResponseCacheConfig parameters")
        
        errors = []
        
        try:
            # Validate Redis URL format
            if not self.redis_url.startswith(('redis://', 'rediss://', 'unix://')):
                errors.append(
                    f"redis_url must start with redis://, rediss://, or unix://, got: {self.redis_url}"
                )
            
            # Validate numeric parameters
            if self.default_ttl <= 0:
                errors.append(f"default_ttl must be positive, got {self.default_ttl}")
            
            if self.default_ttl > 86400 * 365:  # 1 year max
                errors.append(f"default_ttl too large (max 1 year), got {self.default_ttl}")
            
            if self.memory_cache_size < 0:
                errors.append(f"memory_cache_size must be non-negative, got {self.memory_cache_size}")
            
            if self.memory_cache_size > 10000:
                errors.append(f"memory_cache_size too large (max 10000), got {self.memory_cache_size}")
            
            if self.compression_threshold < 0:
                errors.append(f"compression_threshold must be non-negative, got {self.compression_threshold}")
            
            if self.compression_threshold > 1024 * 1024:  # 1MB max
                errors.append(f"compression_threshold too large (max 1MB), got {self.compression_threshold}")
            
            if not 1 <= self.compression_level <= 9:
                errors.append(f"compression_level must be 1-9, got {self.compression_level}")
            
            if self.text_hash_threshold <= 0:
                errors.append(f"text_hash_threshold must be positive, got {self.text_hash_threshold}")
            
            if self.text_hash_threshold > 100000:
                errors.append(f"text_hash_threshold too large (max 100000), got {self.text_hash_threshold}")
            
            # Validate text size tiers
            if self.text_size_tiers:
                required_tiers = {'small', 'medium', 'large'}
                provided_tiers = set(self.text_size_tiers.keys())
                missing_tiers = required_tiers - provided_tiers
                
                if missing_tiers:
                    errors.append(f"text_size_tiers missing required tiers: {missing_tiers}")
                
                # Validate tier values are positive
                for tier_name, tier_value in self.text_size_tiers.items():
                    if not isinstance(tier_value, int) or tier_value <= 0:
                        errors.append(f"text_size_tiers['{tier_name}'] must be positive integer, got {tier_value}")
                
                # Validate tier ordering
                if all(tier in self.text_size_tiers for tier in required_tiers):
                    small = self.text_size_tiers['small']
                    medium = self.text_size_tiers['medium']
                    large = self.text_size_tiers['large']
                    
                    if not (small < medium < large):
                        errors.append(
                            f"text_size_tiers must be ordered (small < medium < large), "
                            f"got small={small}, medium={medium}, large={large}"
                        )
            
            # Validate operation TTLs
            if self.operation_ttls:
                for operation, ttl in self.operation_ttls.items():
                    if not isinstance(ttl, int) or ttl <= 0:
                        errors.append(f"operation_ttls['{operation}'] must be positive integer, got {ttl}")
                    
                    if ttl > 86400 * 365:  # 1 year max
                        errors.append(f"operation_ttls['{operation}'] too large (max 1 year), got {ttl}")
            
            # Validate hash algorithm is callable
            if not callable(self.hash_algorithm):
                errors.append(f"hash_algorithm must be callable, got {type(self.hash_algorithm)}")
            
            # Validate performance monitor
            if self.performance_monitor is not None:
                if not hasattr(self.performance_monitor, 'record_cache_operation_time'):
                    errors.append("performance_monitor must have record_cache_operation_time method")
            
            # Validate consistency between enable_l1_cache and memory_cache_size
            if not self.enable_l1_cache and self.memory_cache_size > 0:
                errors.append(
                    "Inconsistent configuration: enable_l1_cache=False but memory_cache_size > 0. "
                    "Either enable L1 cache or set memory_cache_size to 0."
                )
            
            if errors:
                error_msg = f"AIResponseCacheConfig validation failed: {'; '.join(errors)}"
                logger.error(error_msg)
                raise ValidationError(
                    error_msg,
                    context={
                        'validation_errors': errors,
                        'parameter_count': len(self.__dict__),
                        'config_values': {k: str(v) for k, v in self.__dict__.items()}
                    }
                )
            
            logger.info("AIResponseCacheConfig validation passed successfully")
            
        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"AIResponseCacheConfig validation failed with exception: {e}"
            logger.error(error_msg, exc_info=True)
            raise ValidationError(
                error_msg,
                context={
                    'validation_stage': 'exception',
                    'error_type': type(e).__name__
                }
            )
    
    def to_ai_cache_kwargs(self) -> Dict[str, Any]:
        """
        Convert configuration to kwargs suitable for AIResponseCache initialization.
        
        Creates a dictionary of all configuration parameters with proper naming
        for use with the AIResponseCache constructor. This method provides the
        bridge between the structured configuration and the cache initialization.
        
        Returns:
            Dict[str, Any]: Complete parameter dictionary for AIResponseCache
            
        Examples:
            >>> config = AIResponseCacheConfig(redis_url="redis://localhost:6379")
            >>> kwargs = config.to_ai_cache_kwargs()
            >>> cache = AIResponseCache(**kwargs)  # Direct usage with constructor
            
            >>> # Or with parameter mapping
            >>> mapper = CacheParameterMapper()
            >>> generic_params, ai_params = mapper.map_ai_to_generic_params(kwargs)
        """
        logger.debug("Converting AIResponseCacheConfig to cache kwargs")
        
        try:
            kwargs = {
                # Generic Redis parameters
                'redis_url': self.redis_url,
                'default_ttl': self.default_ttl,
                'enable_l1_cache': self.enable_l1_cache,
                'compression_threshold': self.compression_threshold,
                'compression_level': self.compression_level,
                'performance_monitor': self.performance_monitor,
                'security_config': self.security_config,
                
                # AI-specific parameters
                'text_hash_threshold': self.text_hash_threshold,
                'hash_algorithm': self.hash_algorithm,
                'text_size_tiers': self.text_size_tiers,
                'operation_ttls': self.operation_ttls,
                
                # Mapped parameters (AI name -> Generic name mapping handled by CacheParameterMapper)
                'memory_cache_size': self.memory_cache_size,
            }
            
            # Remove None values to avoid validation issues
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            logger.debug(f"Generated {len(kwargs)} cache kwargs from configuration")
            return kwargs
            
        except Exception as e:
            error_msg = f"Failed to convert AIResponseCacheConfig to kwargs: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={
                    'conversion_stage': 'to_ai_cache_kwargs',
                    'error_type': type(e).__name__
                }
            )
    
    @classmethod
    def create_default(cls) -> 'AIResponseCacheConfig':
        """
        Create a default configuration suitable for development and testing.
        
        Returns:
            AIResponseCacheConfig: Configuration with sensible defaults
            
        Examples:
            >>> config = AIResponseCacheConfig.create_default()
            >>> cache = AIResponseCache(config)
        """
        logger.debug("Creating default AIResponseCacheConfig")
        return cls()
    
    @classmethod
    def create_production(cls, redis_url: str) -> 'AIResponseCacheConfig':
        """
        Create a production-optimized configuration.
        
        Args:
            redis_url: Production Redis connection URL
            
        Returns:
            AIResponseCacheConfig: Production-optimized configuration
            
        Examples:
            >>> config = AIResponseCacheConfig.create_production("redis://prod:6379")
            >>> cache = AIResponseCache(config)
        """
        logger.debug("Creating production AIResponseCacheConfig")
        return cls(
            redis_url=redis_url,
            default_ttl=7200,  # 2 hours for production
            memory_cache_size=200,  # Larger memory cache
            compression_threshold=500,  # More aggressive compression
            compression_level=7,  # Higher compression for bandwidth savings
            text_hash_threshold=500,  # Lower threshold for optimization
        )
    
    @classmethod
    def create_development(cls) -> 'AIResponseCacheConfig':
        """
        Create a development-friendly configuration.
        
        Returns:
            AIResponseCacheConfig: Development-optimized configuration
            
        Examples:
            >>> config = AIResponseCacheConfig.create_development()
            >>> cache = AIResponseCache(config)
        """
        logger.debug("Creating development AIResponseCacheConfig")
        return cls(
            redis_url="redis://localhost:6379",
            default_ttl=1800,  # 30 minutes for development
            memory_cache_size=50,  # Smaller memory cache
            compression_threshold=2000,  # Less aggressive compression
            compression_level=3,  # Faster compression for development
            text_hash_threshold=2000,  # Higher threshold for readability
        )
    
    def __repr__(self) -> str:
        """String representation for debugging and logging."""
        return (
            f"AIResponseCacheConfig("
            f"redis_url='{self.redis_url}', "
            f"default_ttl={self.default_ttl}, "
            f"memory_cache_size={self.memory_cache_size}, "
            f"text_hash_threshold={self.text_hash_threshold})"
        )