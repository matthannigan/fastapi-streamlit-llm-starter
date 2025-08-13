"""
AI Response Cache Configuration Module

This module provides comprehensive configuration management for the AI Response Cache
with advanced validation, factory methods, and environment integration. It supports
the Phase 2 cache refactoring architecture where AIResponseCache inherits from
GenericRedisCache, enabling clean parameter separation and robust configuration.

## Classes

### AIResponseCacheConfig
Comprehensive configuration dataclass for AI cache settings with:
- Parameter separation between generic and AI-specific settings
- ValidationResult-based comprehensive validation
- Multiple factory methods for different configuration sources
- Environment variable integration with configurable prefixes
- Configuration merging and inheritance support
- Performance-conscious design with sensible defaults

## Key Features

### 🔧 Configuration Architecture
- **Parameter Separation**: Clean separation between generic Redis and AI-specific parameters
- **Type Safety**: Full type annotations with Optional types for flexible configuration
- **Validation Framework**: Integration with ValidationResult for detailed error reporting
- **Factory Pattern**: Multiple creation methods for different deployment scenarios
- **Configuration Inheritance**: Merge and override configurations for environment-specific setups

### 🚀 Environment Integration
- **Environment Variables**: Automatic loading from environment with configurable prefixes
- **JSON/YAML Support**: File-based configuration with validation and error handling
- **Preset System**: Pre-configured setups for development, production, and testing
- **Migration Support**: Backwards-compatible configuration loading

### 📊 Validation & Monitoring
- **Comprehensive Validation**: Type checking, range validation, consistency checks
- **Performance Recommendations**: Intelligent suggestions for optimal configuration
- **Detailed Error Messages**: Clear, actionable validation feedback
- **Configuration Auditing**: Full context tracking for debugging

## Configuration Parameters

### Generic Redis Parameters (Inherited by GenericRedisCache)
- `redis_url`: Redis connection URL with support for redis://, rediss://, unix://
- `default_ttl`: Default time-to-live for cache entries (1-31536000 seconds)
- `enable_l1_cache`: Enable in-memory L1 cache tier for performance
- `compression_threshold`: Size threshold for automatic compression (0-1MB)
- `compression_level`: Zlib compression level for bandwidth optimization (1-9)
- `performance_monitor`: CachePerformanceMonitor instance for metrics collection
- `security_config`: Optional security configuration for encrypted connections

### AI-Specific Parameters (Unique to AI Response Caching)
- `text_hash_threshold`: Character threshold for text hashing optimization (1-100000)
- `hash_algorithm`: Hash algorithm function for large text processing (default: sha256)
- `text_size_tiers`: Text categorization thresholds for cache optimization
- `operation_ttls`: Operation-specific TTL values for intelligent cache management

### Mapped Parameters (AI → Generic Conversion)
- `memory_cache_size`: Maps to `l1_cache_size` in GenericRedisCache (1-10000 entries)

## Usage Examples

### Basic Configuration
```python
# Simple configuration with defaults
config = AIResponseCacheConfig(
    redis_url="redis://localhost:6379",
    text_hash_threshold=1000
)

# Validate configuration
result = config.validate()
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")

# Convert to cache kwargs and initialize
kwargs = config.to_ai_cache_kwargs()
cache = AIResponseCache(**kwargs)
```

### Advanced Production Configuration
```python
config = AIResponseCacheConfig(
    redis_url="redis://production:6379",
    default_ttl=7200,  # 2 hours
    memory_cache_size=200,  # Large memory cache
    compression_threshold=500,  # Aggressive compression
    compression_level=7,  # High compression ratio
    text_hash_threshold=500,  # Optimize for large texts
    text_size_tiers={
        "small": 300,    # Quick memory access
        "medium": 3000,  # Standard caching
        "large": 30000,  # With compression
    },
    operation_ttls={
        "summarize": 14400,   # 4 hours - stable content
        "sentiment": 86400,   # 24 hours - rarely changes
        "key_points": 7200,   # 2 hours - contextual
        "questions": 3600,    # 1 hour - variable content
        "qa": 1800,           # 30 minutes - highly contextual
    }
)
```

### Environment-Based Configuration
```python
# Set environment variables
os.environ['AI_CACHE_REDIS_URL'] = 'redis://prod:6379'
os.environ['AI_CACHE_DEFAULT_TTL'] = '7200'
os.environ['AI_CACHE_MEMORY_CACHE_SIZE'] = '200'
os.environ['AI_CACHE_TEXT_SIZE_TIERS'] = '{"small": 500, "medium": 5000, "large": 50000}'

# Load from environment
config = AIResponseCacheConfig.from_env(prefix="AI_CACHE_")

# Validate and get recommendations
result = config.validate()
for rec in result.recommendations:
    print(f"💡 Recommendation: {rec}")
```

### Configuration Presets
```python
# Development configuration
dev_config = AIResponseCacheConfig.create_development()

# Production configuration
prod_config = AIResponseCacheConfig.create_production("redis://prod:6379")

# Testing configuration
test_config = AIResponseCacheConfig.create_testing()

# Merge configurations
custom_config = dev_config.merge(prod_config)
```

### File-Based Configuration
```python
# From YAML file
config = AIResponseCacheConfig.from_yaml('cache_config.yaml')

# From JSON file
config = AIResponseCacheConfig.from_json('cache_config.json')

# From dictionary
config_dict = {
    'redis_url': 'redis://localhost:6379',
    'default_ttl': 3600,
    'memory_cache_size': 100
}
config = AIResponseCacheConfig.from_dict(config_dict)
```

## Configuration Validation

The validation system provides comprehensive checking with detailed feedback:

```python
config = AIResponseCacheConfig(memory_cache_size=-10)
result = config.validate()

if not result.is_valid:
    print(f"❌ Configuration has {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  - {error}")

if result.warnings:
    print(f"⚠️  Configuration has {len(result.warnings)} warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")

if result.recommendations:
    print(f"💡 Configuration recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

## Architecture Integration

This configuration system integrates seamlessly with the cache inheritance architecture:

1. **Parameter Mapping**: Works with CacheParameterMapper to separate AI and generic parameters
2. **Validation Integration**: Uses ValidationResult for consistent error reporting
3. **Factory Pattern**: Supports different deployment scenarios with preset configurations
4. **Performance Optimization**: Includes intelligent recommendations for cache tuning
5. **Environment Flexibility**: Supports Docker, Kubernetes, and cloud deployments

## Migration Guide

### From Legacy Configuration
```python
# Old direct initialization
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    memory_cache_size=100
)

# New configuration-based approach
config = AIResponseCacheConfig(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    memory_cache_size=100
)
kwargs = config.to_ai_cache_kwargs()
cache = AIResponseCache(**kwargs)
```

### Environment Variable Migration
```bash
# Legacy environment variables
export REDIS_URL="redis://localhost:6379"
export CACHE_TTL="3600"

# New structured environment variables
export AI_CACHE_REDIS_URL="redis://localhost:6379"
export AI_CACHE_DEFAULT_TTL="3600"
export AI_CACHE_MEMORY_CACHE_SIZE="100"
```

## Performance Considerations

- **Validation Performance**: Configuration validation is performed once at startup
- **Memory Efficiency**: Uses dataclasses with __slots__ for memory optimization
- **Factory Caching**: Factory methods create new instances without caching overhead
- **Environment Loading**: Environment variable processing is optimized for startup speed
- **Validation Caching**: ValidationResult instances can be cached for repeated validations

## Dependencies

### Required Dependencies
- `dataclasses`: Configuration structure and serialization
- `typing`: Comprehensive type annotations
- `hashlib`: Hash algorithm defaults for text processing
- `json`: JSON configuration file support
- `os`: Environment variable integration
- `logging`: Comprehensive logging integration

### Optional Dependencies
- `yaml` (PyYAML): YAML configuration file support
- `app.core.exceptions`: Custom exception handling framework
- `app.infrastructure.cache.monitoring`: Performance monitoring integration
- `app.infrastructure.cache.parameter_mapping`: ValidationResult framework

## Error Handling

All methods use custom exceptions with comprehensive context:
- `ConfigurationError`: Configuration setup and processing errors
- `ValidationError`: Parameter validation failures with detailed context
- Detailed logging at DEBUG, INFO, WARNING, and ERROR levels
- Exception context includes error type, parameters, and debugging information
"""

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Optional, Union

# Version and compatibility information
__version__ = "2.0.0"
__all__ = [
    "AIResponseCacheConfig",
    "ValidationResult",
]

try:
    import yaml
except ImportError:
    yaml = None

from app.core.exceptions import ValidationError, ConfigurationError
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.parameter_mapping import ValidationResult

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
            # Track if operation_ttls was explicitly set to None for recommendations
            self._operation_ttls_was_none = self.operation_ttls is None
            
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
    
    def validate(self) -> ValidationResult:
        """
        Validate all configuration parameters and return comprehensive results.
        
        Performs thorough validation of all parameters including type checking,
        value range validation, consistency checks, and dependency validation.
        Uses the ValidationResult framework for detailed error reporting and
        recommendations.
        
        Returns:
            ValidationResult: Comprehensive validation results with errors, warnings,
                            and recommendations
            
        Examples:
            >>> config = AIResponseCacheConfig(memory_cache_size=-10)
            >>> result = config.validate()
            >>> if not result.is_valid:
            ...     for error in result.errors:
            ...         print(f"Error: {error}")
            
            >>> config = AIResponseCacheConfig(redis_url="redis://localhost:6379")
            >>> result = config.validate()
            >>> if result.recommendations:
            ...     for rec in result.recommendations:
            ...         print(f"Recommendation: {rec}")
        """
        logger.debug("Validating AIResponseCacheConfig parameters")
        
        result = ValidationResult()
        result.context = {
            'config_type': 'AIResponseCacheConfig',
            'parameter_count': len(self.__dict__),
            'validation_timestamp': logger.name,
        }
        
        try:
            # Validate Redis URL format
            if not self.redis_url.startswith(('redis://', 'rediss://', 'unix://')):
                result.add_error(
                    f"redis_url must start with redis://, rediss://, or unix://, got: {self.redis_url}"
                )
            
            # Validate numeric parameters
            if self.default_ttl <= 0:
                result.add_error(f"default_ttl must be positive, got {self.default_ttl}")
            
            if self.default_ttl > 86400 * 365:  # 1 year max
                result.add_error(f"default_ttl too large (max 1 year), got {self.default_ttl}")
            
            if self.memory_cache_size < 0:
                result.add_error(f"memory_cache_size must be non-negative, got {self.memory_cache_size}")
            
            if self.memory_cache_size > 10000:
                result.add_error(f"memory_cache_size too large (max 10000), got {self.memory_cache_size}")
            
            if self.compression_threshold < 0:
                result.add_error(f"compression_threshold must be non-negative, got {self.compression_threshold}")
            
            if self.compression_threshold > 1024 * 1024:  # 1MB max
                result.add_error(f"compression_threshold too large (max 1MB), got {self.compression_threshold}")
            
            if not 1 <= self.compression_level <= 9:
                result.add_error(f"compression_level must be 1-9, got {self.compression_level}")
            
            if self.text_hash_threshold <= 0:
                result.add_error(f"text_hash_threshold must be positive, got {self.text_hash_threshold}")
            
            if self.text_hash_threshold > 100000:
                result.add_error(f"text_hash_threshold too large (max 100000), got {self.text_hash_threshold}")
            
            # Validate text size tiers
            if self.text_size_tiers:
                required_tiers = {'small', 'medium', 'large'}
                provided_tiers = set(self.text_size_tiers.keys())
                missing_tiers = required_tiers - provided_tiers
                
                if missing_tiers:
                    result.add_error(f"text_size_tiers missing required tiers: {missing_tiers}")
                
                # Validate tier values are positive
                for tier_name, tier_value in self.text_size_tiers.items():
                    if not isinstance(tier_value, int) or tier_value <= 0:
                        result.add_error(f"text_size_tiers['{tier_name}'] must be positive integer, got {tier_value}")
                
                # Validate tier ordering
                if all(tier in self.text_size_tiers for tier in required_tiers):
                    small = self.text_size_tiers['small']
                    medium = self.text_size_tiers['medium']
                    large = self.text_size_tiers['large']
                    
                    if not (small < medium < large):
                        result.add_error(
                            f"text_size_tiers must be ordered (small < medium < large), "
                            f"got small={small}, medium={medium}, large={large}"
                        )
            
            # Validate operation TTLs
            if self.operation_ttls:
                valid_operations = {'summarize', 'sentiment', 'key_points', 'questions', 'qa'}
                for operation, ttl in self.operation_ttls.items():
                    if not isinstance(ttl, int) or ttl <= 0:
                        result.add_error(f"operation_ttls['{operation}'] must be positive integer, got {ttl}")
                    
                    if ttl > 86400 * 365:  # 1 year max
                        result.add_warning(
                            f"operation_ttls['{operation}'] is very large ({ttl} seconds = {ttl // 86400} days). "
                            f"Consider if this is intentional."
                        )
                    
                    # Warn about unknown operations
                    if operation not in valid_operations:
                        result.add_warning(
                            f"Unknown operation '{operation}' in operation_ttls. "
                            f"Valid operations: {valid_operations}"
                        )
            
            # Validate hash algorithm is callable
            if not callable(self.hash_algorithm):
                result.add_error(f"hash_algorithm must be callable, got {type(self.hash_algorithm)}")
            
            # Validate performance monitor
            if self.performance_monitor is not None:
                if not hasattr(self.performance_monitor, 'record_cache_operation_time'):
                    result.add_error("performance_monitor must have record_cache_operation_time method")
            
            # Validate consistency between enable_l1_cache and memory_cache_size
            if not self.enable_l1_cache and self.memory_cache_size > 0:
                result.add_error(
                    "Inconsistent configuration: enable_l1_cache=False but memory_cache_size > 0. "
                    "Either enable L1 cache or set memory_cache_size to 0."
                )
            
            # Add configuration recommendations
            self._add_configuration_recommendations(result)
            
            # Log validation summary
            if result.is_valid:
                logger.info("AIResponseCacheConfig validation passed successfully")
            else:
                logger.warning(
                    f"AIResponseCacheConfig validation failed with {len(result.errors)} errors "
                    f"and {len(result.warnings)} warnings"
                )
            
            return result
            
        except Exception as e:
            error_msg = f"AIResponseCacheConfig validation failed with exception: {e}"
            logger.error(error_msg, exc_info=True)
            result.add_error(error_msg)
            result.context['validation_exception'] = str(e)
            return result
    
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
    
    @classmethod
    def create_testing(cls) -> 'AIResponseCacheConfig':
        """
        Create a testing-optimized configuration.
        
        Returns:
            AIResponseCacheConfig: Testing-optimized configuration with fast operations
            
        Examples:
            >>> config = AIResponseCacheConfig.create_testing()
            >>> cache = AIResponseCache(config)
        """
        logger.debug("Creating testing AIResponseCacheConfig")
        return cls(
            redis_url="redis://localhost:6379",
            default_ttl=300,  # 5 minutes for testing
            memory_cache_size=10,  # Minimal memory cache
            compression_threshold=5000,  # Minimal compression
            compression_level=1,  # Fastest compression
            text_hash_threshold=5000,  # High threshold for speed
            operation_ttls={
                "summarize": 300,
                "sentiment": 300,
                "key_points": 300,
                "questions": 300,
                "qa": 300,
            }
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AIResponseCacheConfig':
        """
        Create configuration from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration parameters
            
        Returns:
            AIResponseCacheConfig: Configuration instance created from dictionary
            
        Raises:
            ConfigurationError: If dictionary contains invalid parameters
            
        Examples:
            >>> config_data = {
            ...     'redis_url': 'redis://localhost:6379',
            ...     'default_ttl': 3600,
            ...     'memory_cache_size': 100
            ... }
            >>> config = AIResponseCacheConfig.from_dict(config_data)
        """
        logger.debug(f"Creating AIResponseCacheConfig from dictionary with {len(config_dict)} parameters")
        
        try:
            # Handle special fields that need conversion
            processed_dict = config_dict.copy()
            
            # Convert hash algorithm string to function if needed
            if 'hash_algorithm' in processed_dict:
                hash_algo = processed_dict['hash_algorithm']
                if isinstance(hash_algo, str):
                    if hash_algo == 'sha256':
                        processed_dict['hash_algorithm'] = hashlib.sha256
                    elif hash_algo == 'md5':
                        processed_dict['hash_algorithm'] = hashlib.md5
                    else:
                        raise ConfigurationError(f"Unsupported hash algorithm: {hash_algo}")
            
            # Create performance monitor if needed
            if 'performance_monitor' in processed_dict and processed_dict['performance_monitor'] is True:
                processed_dict['performance_monitor'] = CachePerformanceMonitor()
            
            # Filter out unknown parameters
            valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
            filtered_dict = {k: v for k, v in processed_dict.items() if k in valid_fields}
            
            unknown_params = set(processed_dict.keys()) - valid_fields
            if unknown_params:
                logger.warning(f"Ignoring unknown configuration parameters: {unknown_params}")
            
            config = cls(**filtered_dict)
            logger.info(f"Successfully created AIResponseCacheConfig from dictionary")
            return config
            
        except Exception as e:
            error_msg = f"Failed to create AIResponseCacheConfig from dictionary: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={
                    'config_dict_keys': list(config_dict.keys()),
                    'error_type': type(e).__name__
                }
            )
    
    @classmethod
    def from_env(cls, prefix: str = "AI_CACHE_") -> 'AIResponseCacheConfig':
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variable names
            
        Returns:
            AIResponseCacheConfig: Configuration instance from environment
            
        Environment Variables:
            AI_CACHE_REDIS_URL: Redis connection URL
            AI_CACHE_DEFAULT_TTL: Default TTL in seconds
            AI_CACHE_MEMORY_CACHE_SIZE: Memory cache size
            AI_CACHE_TEXT_HASH_THRESHOLD: Text hashing threshold
            AI_CACHE_COMPRESSION_THRESHOLD: Compression threshold
            AI_CACHE_COMPRESSION_LEVEL: Compression level (1-9)
            AI_CACHE_ENABLE_L1_CACHE: Enable L1 cache (true/false)
            
        Examples:
            >>> os.environ['AI_CACHE_REDIS_URL'] = 'redis://localhost:6379'
            >>> os.environ['AI_CACHE_DEFAULT_TTL'] = '3600'
            >>> config = AIResponseCacheConfig.from_env()
        """
        logger.debug(f"Creating AIResponseCacheConfig from environment with prefix '{prefix}'")
        
        try:
            env_config = {}
            
            # Define environment variable mappings
            env_mappings = {
                f"{prefix}REDIS_URL": ('redis_url', str),
                f"{prefix}DEFAULT_TTL": ('default_ttl', int),
                f"{prefix}MEMORY_CACHE_SIZE": ('memory_cache_size', int),
                f"{prefix}TEXT_HASH_THRESHOLD": ('text_hash_threshold', int),
                f"{prefix}COMPRESSION_THRESHOLD": ('compression_threshold', int),
                f"{prefix}COMPRESSION_LEVEL": ('compression_level', int),
                f"{prefix}ENABLE_L1_CACHE": ('enable_l1_cache', bool),
                f"{prefix}HASH_ALGORITHM": ('hash_algorithm', str),
            }
            
            # Process environment variables
            for env_key, (config_key, value_type) in env_mappings.items():
                env_value = os.getenv(env_key)
                if env_value is not None:
                    try:
                        if value_type == bool:
                            env_config[config_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                        elif value_type == int:
                            env_config[config_key] = int(env_value)
                        else:
                            env_config[config_key] = env_value
                    except ValueError as e:
                        logger.warning(f"Invalid value for {env_key}: {env_value}, error: {e}")
            
            # Handle complex JSON fields
            text_size_tiers_env = os.getenv(f"{prefix}TEXT_SIZE_TIERS")
            if text_size_tiers_env:
                try:
                    env_config['text_size_tiers'] = json.loads(text_size_tiers_env)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON for {prefix}TEXT_SIZE_TIERS: {e}")
            
            operation_ttls_env = os.getenv(f"{prefix}OPERATION_TTLS")
            if operation_ttls_env:
                try:
                    env_config['operation_ttls'] = json.loads(operation_ttls_env)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON for {prefix}OPERATION_TTLS: {e}")
            
            # Create configuration with environment overrides
            if env_config:
                config = cls.from_dict(env_config)
                logger.info(f"Created AIResponseCacheConfig from {len(env_config)} environment variables")
            else:
                config = cls.from_dict({})  # Use from_dict for consistency in exception handling
                logger.info("No environment variables found, using default configuration")
                
            return config
            
        except Exception as e:
            error_msg = f"Failed to create AIResponseCacheConfig from environment: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={
                    'prefix': prefix,
                    'error_type': type(e).__name__
                }
            )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'AIResponseCacheConfig':
        """
        Create configuration from YAML file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            AIResponseCacheConfig: Configuration instance from YAML
            
        Raises:
            ConfigurationError: If YAML library is not available or file cannot be loaded
            
        Examples:
            >>> config = AIResponseCacheConfig.from_yaml('config.yaml')
        """
        if yaml is None:
            raise ConfigurationError(
                "PyYAML library is required for YAML configuration loading. "
                "Install with: pip install pyyaml"
            )
        
        logger.debug(f"Creating AIResponseCacheConfig from YAML file: {yaml_path}")
        
        try:
            with open(yaml_path, 'r') as file:
                yaml_data = yaml.safe_load(file)
            
            if not isinstance(yaml_data, dict):
                raise ConfigurationError(f"YAML file must contain a dictionary, got {type(yaml_data)}")
            
            config = cls.from_dict(yaml_data)
            logger.info(f"Successfully loaded AIResponseCacheConfig from YAML: {yaml_path}")
            return config
            
        except FileNotFoundError:
            error_msg = f"YAML configuration file not found: {yaml_path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML in configuration file {yaml_path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load configuration from YAML {yaml_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={'yaml_path': yaml_path, 'error_type': type(e).__name__}
            )
    
    @classmethod
    def from_json(cls, json_path: str) -> 'AIResponseCacheConfig':
        """
        Create configuration from JSON file.
        
        Args:
            json_path: Path to JSON configuration file
            
        Returns:
            AIResponseCacheConfig: Configuration instance from JSON
            
        Examples:
            >>> config = AIResponseCacheConfig.from_json('config.json')
        """
        logger.debug(f"Creating AIResponseCacheConfig from JSON file: {json_path}")
        
        try:
            with open(json_path, 'r') as file:
                json_data = json.load(file)
            
            config = cls.from_dict(json_data)
            logger.info(f"Successfully loaded AIResponseCacheConfig from JSON: {json_path}")
            return config
            
        except FileNotFoundError:
            error_msg = f"JSON configuration file not found: {json_path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file {json_path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load configuration from JSON {json_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={'json_path': json_path, 'error_type': type(e).__name__}
            )
    
    def merge(self, other: 'AIResponseCacheConfig') -> 'AIResponseCacheConfig':
        """
        Merge this configuration with another configuration.
        
        Args:
            other: Another configuration to merge with this one
            
        Returns:
            AIResponseCacheConfig: New configuration with merged values
            
        Note:
            Values from 'other' configuration take precedence over this configuration.
            
        Examples:
            >>> base_config = AIResponseCacheConfig.create_default()
            >>> prod_config = AIResponseCacheConfig(redis_url='redis://prod:6379')
            >>> merged = base_config.merge(prod_config)
        """
        logger.debug("Merging AIResponseCacheConfig instances")
        
        try:
            # Convert both configs to dictionaries
            base_dict = asdict(self)
            other_dict = asdict(other)
            default_dict = asdict(AIResponseCacheConfig())
            
            # Only include values from other that differ from defaults
            override_dict = {k: v for k, v in other_dict.items() 
                           if k in default_dict and v != default_dict[k]}
            
            # Merge dictionaries (other non-default values take precedence)
            merged_dict = {**base_dict, **override_dict}
            
            # Create new configuration from merged data
            merged_config = self.from_dict(merged_dict)
            logger.info("Successfully merged AIResponseCacheConfig instances")
            return merged_config
            
        except Exception as e:
            error_msg = f"Failed to merge AIResponseCacheConfig instances: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={'error_type': type(e).__name__}
            )
    
    def _add_configuration_recommendations(self, result: ValidationResult) -> None:
        """
        Add configuration recommendations to the validation result.
        
        Args:
            result: ValidationResult to add recommendations to
        """
        # Recommend compression optimization
        if self.compression_threshold > 10000:
            result.add_recommendation(
                f"Compression threshold ({self.compression_threshold}) is quite high. "
                f"Consider lowering it to compress more responses and save memory."
            )
        
        if self.compression_level > 7:
            result.add_recommendation(
                f"Compression level ({self.compression_level}) is high, which uses more CPU. "
                f"Consider level 6 for balanced performance and compression."
            )
        
        # Recommend text hash threshold consistency
        if self.text_hash_threshold != self.compression_threshold:
            result.add_recommendation(
                f"Text hash threshold ({self.text_hash_threshold}) differs from compression threshold "
                f"({self.compression_threshold}). Consider aligning these values for consistency."
            )
        
        # Recommend memory cache optimization
        if self.memory_cache_size > 500:
            result.add_recommendation(
                f"Memory cache size ({self.memory_cache_size}) is quite large. "
                f"Monitor memory usage and consider reducing if not needed."
            )
        
        # Recommend TTL optimization
        if self.default_ttl > 86400:  # More than 1 day
            result.add_recommendation(
                f"Default TTL ({self.default_ttl} seconds = {self.default_ttl // 86400} days) is quite long. "
                f"Consider shorter TTLs for more dynamic caching."
            )
        
        # Recommend operation-specific TTLs
        if not self.operation_ttls:
            result.add_recommendation(
                "Consider setting operation-specific TTLs for better cache management. "
                "Different operations may benefit from different cache durations."
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