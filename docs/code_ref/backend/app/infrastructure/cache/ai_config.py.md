---
sidebar_label: ai_config
---

# AI Response Cache Configuration Module

  file_path: `backend/app/infrastructure/cache/ai_config.py`

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

### Preset-Based Configuration (RECOMMENDED)
```python
# Use preset-based configuration (replaces 28+ individual variables)
os.environ['CACHE_PRESET'] = 'ai-production'
os.environ['CACHE_REDIS_URL'] = 'redis://prod:6379'  # Optional override
os.environ['ENABLE_AI_CACHE'] = 'true'  # Optional override

# Load from preset system via Settings
from app.core.config import settings
cache_config = settings.get_cache_config()

# Advanced customization with JSON overrides
os.environ['CACHE_CUSTOM_CONFIG'] = '''{
    "compression_threshold": 500,
    "text_size_tiers": {"small": 500, "medium": 5000, "large": 50000},
    "memory_cache_size": 200
}'''
```

### Legacy Environment-Based Configuration (DEPRECATED)
```python
# DEPRECATED: Individual environment variables no longer supported
# Use CACHE_PRESET with preset-based configuration instead

# OLD WAY (no longer works):
# os.environ['AI_CACHE_DEFAULT_TTL'] = '7200'
# os.environ['AI_CACHE_MEMORY_CACHE_SIZE'] = '200'

# NEW WAY (recommended):
os.environ['CACHE_PRESET'] = 'ai-development'
cache_config = settings.get_cache_config()
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
# Preset-based configuration (RECOMMENDED)
export CACHE_PRESET="ai-development"
export CACHE_REDIS_URL="redis://localhost:6379"  # Optional override
export ENABLE_AI_CACHE="true"  # Optional override

# Legacy environment variables (DEPRECATED - no longer supported)
# export AI_CACHE_REDIS_URL="redis://localhost:6379"
# export AI_CACHE_DEFAULT_TTL="3600"
# export AI_CACHE_MEMORY_CACHE_SIZE="100"
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

## AIResponseCacheConfig

Comprehensive AI Response Cache configuration with validation, factory methods, and parameter mapping.

Provides structured configuration management for AI caching with clear parameter separation between
generic Redis functionality and AI-specific optimizations. Includes comprehensive validation,
multiple factory methods, and seamless integration with inheritance-based cache architecture.

Attributes:
    redis_url: Optional[str] Redis connection URL (redis://, rediss://, unix://)
    default_ttl: int default time-to-live (1-31536000 seconds, default: 3600)
    enable_l1_cache: bool enable in-memory L1 cache tier (default: True)
    memory_cache_size: int maximum L1 cache entries (1-10000, default: 1000)
    compression_threshold: int bytes threshold for compression (0-1048576, default: 1024)
    compression_level: int zlib compression level (1-9, default: 6)
    text_hash_threshold: int characters threshold for text hashing (1-100000, default: 1000)
    hash_algorithm: str hash algorithm for text processing (default: 'sha256')
    operation_ttls: Dict[str, int] operation-specific TTL overrides
    performance_monitor: Optional cache performance monitor instance
    security_config: Optional security configuration for encrypted connections

Public Methods:
    validate(): Comprehensive validation with detailed error reporting
    to_generic_config(): Convert to GenericRedisCache configuration
    merge_config(): Merge with another configuration for inheritance
    from_environment(): Factory method loading from environment variables
    from_dict(): Factory method loading from dictionary data
    from_preset(): Factory method loading from preset configurations

State Management:
    - Immutable configuration after validation for consistent behavior
    - Thread-safe parameter access for concurrent cache operations
    - Comprehensive validation with actionable error messages
    - Factory methods support various configuration sources

Usage:
    # Basic configuration with defaults
    config = AIResponseCacheConfig(
        redis_url="redis://localhost:6379/0"
    )

    # Advanced configuration with AI optimizations
    config = AIResponseCacheConfig(
        redis_url="redis://ai-cache:6379/1",
        default_ttl=7200,
        text_hash_threshold=5000,
        operation_ttls={
            "summarize": 3600,
            "analyze": 7200,
            "translate": 1800
        }
    )

    # Environment-based configuration
    config = AIResponseCacheConfig.from_environment(
        prefix="AI_CACHE_",
        fallback_redis_url="redis://localhost:6379"
    )

    # Validation and conversion
    validation_result = config.validate()
    if validation_result.is_valid:
        generic_config = config.to_generic_config()
        cache = AIResponseCache(generic_config)
    else:
        logger.error(f"Configuration errors: {validation_result.errors}")

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

### __post_init__()

```python
def __post_init__(self):
```

Post-initialization setup with defaults and validation.

Sets up default values for complex fields and performs basic validation
to catch configuration errors early in the initialization process.

Raises:
    ConfigurationError: If critical configuration setup fails

### validate()

```python
def validate(self) -> ValidationResult:
```

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

### to_ai_cache_kwargs()

```python
def to_ai_cache_kwargs(self) -> Dict[str, Any]:
```

Convert configuration to kwargs suitable for AIResponseCache initialization.

Creates a dictionary of all configuration parameters with proper naming
for use with the AIResponseCache constructor. This method provides the
bridge between the structured configuration and the cache initialization.

**Compatibility Note**: This method returns kwargs compatible with the legacy
AIResponseCache constructor, which expects `memory_cache_size` instead of
`enable_l1_cache` and `l1_cache_size` parameters.

Returns:
    Dict[str, Any]: Complete parameter dictionary for AIResponseCache

Examples:
    >>> config = AIResponseCacheConfig(redis_url="redis://localhost:6379")
    >>> kwargs = config.to_ai_cache_kwargs()
    >>> cache = AIResponseCache(**kwargs)  # Direct usage with constructor

    >>> # Or with parameter mapping
    >>> mapper = CacheParameterMapper()
    >>> generic_params, ai_params = mapper.map_ai_to_generic_params(kwargs)

### to_generic_cache_kwargs()

```python
def to_generic_cache_kwargs(self) -> Dict[str, Any]:
```

Convert configuration to kwargs suitable for GenericRedisCache initialization.

Creates a dictionary with parameters properly mapped for the new modular
GenericRedisCache architecture (enable_l1_cache, l1_cache_size, etc.).

Returns:
    Dict[str, Any]: Complete parameter dictionary for GenericRedisCache

Examples:
    >>> config = AIResponseCacheConfig(redis_url="redis://localhost:6379")
    >>> kwargs = config.to_generic_cache_kwargs()
    >>> cache = GenericRedisCache(**kwargs)  # New modular architecture

### create_default()

```python
def create_default(cls) -> 'AIResponseCacheConfig':
```

Create a default configuration suitable for development and testing.

Returns:
    AIResponseCacheConfig: Configuration with sensible defaults

Examples:
    >>> config = AIResponseCacheConfig.create_default()
    >>> cache = AIResponseCache(config)

### create_production()

```python
def create_production(cls, redis_url: str) -> 'AIResponseCacheConfig':
```

Create a production-optimized configuration.

Args:
    redis_url: Production Redis connection URL

Returns:
    AIResponseCacheConfig: Production-optimized configuration

Examples:
    >>> config = AIResponseCacheConfig.create_production("redis://prod:6379")
    >>> cache = AIResponseCache(config)

### create_development()

```python
def create_development(cls) -> 'AIResponseCacheConfig':
```

Create a development-friendly configuration.

Returns:
    AIResponseCacheConfig: Development-optimized configuration

Examples:
    >>> config = AIResponseCacheConfig.create_development()
    >>> cache = AIResponseCache(config)

### create_testing()

```python
def create_testing(cls) -> 'AIResponseCacheConfig':
```

Create a testing-optimized configuration.

Returns:
    AIResponseCacheConfig: Testing-optimized configuration with fast operations

Examples:
    >>> config = AIResponseCacheConfig.create_testing()
    >>> cache = AIResponseCache(config)

### from_dict()

```python
def from_dict(cls, config_dict: Dict[str, Any], convert_hash_algorithm: bool = True) -> 'AIResponseCacheConfig':
```

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

### from_env()

```python
def from_env(cls, prefix: str = 'AI_CACHE_') -> 'AIResponseCacheConfig':
```

Create configuration from environment variables.

Args:
    prefix: Prefix for environment variable names

Returns:
    AIResponseCacheConfig: Configuration instance from environment

DEPRECATED: Individual environment variables are no longer supported.
Use CACHE_PRESET with preset-based configuration instead.

Preset System (RECOMMENDED):
    CACHE_PRESET: Cache preset name (ai-development, ai-production, etc.)
    CACHE_REDIS_URL: Optional Redis URL override
    ENABLE_AI_CACHE: Optional AI features toggle
    CACHE_CUSTOM_CONFIG: Optional JSON configuration override

Examples:
    >>> os.environ['CACHE_PRESET'] = 'ai-development'
    >>> os.environ['CACHE_REDIS_URL'] = 'redis://localhost:6379'  # Optional
    >>> from app.core.config import settings
    >>> config = settings.get_cache_config()  # Use preset system instead

### from_yaml()

```python
def from_yaml(cls, yaml_path: str) -> 'AIResponseCacheConfig':
```

Create configuration from YAML file.

Args:
    yaml_path: Path to YAML configuration file

Returns:
    AIResponseCacheConfig: Configuration instance from YAML

Raises:
    ConfigurationError: If YAML library is not available or file cannot be loaded

Examples:
    >>> config = AIResponseCacheConfig.from_yaml('config.yaml')

### from_json()

```python
def from_json(cls, json_path: str) -> 'AIResponseCacheConfig':
```

Create configuration from JSON file.

Args:
    json_path: Path to JSON configuration file

Returns:
    AIResponseCacheConfig: Configuration instance from JSON

Examples:
    >>> config = AIResponseCacheConfig.from_json('config.json')

### merge_with()

```python
def merge_with(self, **overrides) -> 'AIResponseCacheConfig':
```

Merge this configuration with explicit override values.

This method allows merging with only the values that should actually
be overridden, avoiding the issue where dataclass fields are automatically
filled with defaults.

Args:
    **overrides: Keyword arguments for values to override

Returns:
    AIResponseCacheConfig: New configuration with merged values

Example:
    >>> base_config = AIResponseCacheConfig(redis_url="redis://base:6379")
    >>> merged = base_config.merge_with(
    ...     redis_url="redis://override:6379",
    ...     default_ttl=3600
    ... )

### merge()

```python
def merge(self, other: 'AIResponseCacheConfig') -> 'AIResponseCacheConfig':
```

Merge this configuration with another configuration.

Args:
    other: Another configuration to merge with this one

Returns:
    AIResponseCacheConfig: New configuration with merged values

Note:
    Values from 'other' configuration take precedence over this configuration,
    but only if they differ from the default values.

Examples:
    >>> base_config = AIResponseCacheConfig.create_default()
    >>> prod_config = AIResponseCacheConfig(redis_url='redis://prod:6379')
    >>> merged = base_config.merge(prod_config)

### __repr__()

```python
def __repr__(self) -> str:
```

String representation for debugging and logging.
