---
sidebar_label: ai_config
---

# [REFACTORED] AI Response Cache Configuration Module

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
