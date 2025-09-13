---
sidebar_label: factory
---

# Factory for explicit cache instantiation with environment-optimized defaults.

  file_path: `backend/app/infrastructure/cache/factory.py`

This module provides a comprehensive factory system for creating cache instances
with explicit configuration and deterministic behavior. It offers clear factory
methods for different use cases, eliminating ambiguity in cache selection.

## Classes

**CacheFactory**: Main factory class providing explicit cache creation methods
for web applications, AI applications, testing environments, and configuration-based
instantiation.

## Key Features

- **Explicit Creation**: Clear, deterministic factory methods for specific use cases
- **Environment Defaults**: Pre-configured settings optimized for different environments
- **Configuration Support**: Flexible creation from configuration objects
- **Graceful Fallback**: Automatic fallback to InMemoryCache when Redis unavailable
- **Input Validation**: Comprehensive validation with detailed error messages
- **Type Safety**: Full type annotations for IDE support

## Factory Methods

- `for_web_app()`: Web applications with balanced performance settings
- `for_ai_app()`: AI applications with optimized storage and compression
- `for_testing()`: Testing environments with short TTLs and test databases
- `create_cache_from_config()`: Flexible configuration-based creation

## Usage

```python
factory = CacheFactory()

# Web application cache
cache = await factory.for_web_app(redis_url="redis://localhost:6379")
await cache.set("session:123", {"user_id": 456})

# AI application cache
ai_cache = await factory.for_ai_app(
    redis_url="redis://ai-cache:6379",
    default_ttl=7200
)

# Configuration-based creation
config = {
    "redis_url": "redis://production:6379",
    "default_ttl": 3600,
    "compression_threshold": 2000
}
cache = await factory.create_cache_from_config(config)
```

## Factory vs Direct Instantiation Patterns

### When to Use Factory Methods (Recommended)

**✅ Use factory methods for:**

1. **Application Initialization** - When setting up cache at application startup
2. **Environment-Specific Configurations** - Different settings per deployment environment
3. **Cross-Team Development** - Provides consistent, validated configurations
4. **Preset-Based Configuration** - Leverage optimized defaults for specific use cases
5. **Production Deployments** - Built-in error handling and graceful fallback
6. **Security-Conscious Applications** - Integrated security configuration validation

**Factory Method Benefits:**
- **Optimized Defaults**: Environment-specific presets (web, AI, testing)
- **Input Validation**: Comprehensive parameter validation with detailed error messages
- **Graceful Fallback**: Automatic fallback to InMemoryCache when Redis unavailable
- **Security Integration**: Built-in security configuration and validation
- **Error Handling**: Structured error handling with proper context
- **Connection Testing**: Automatic Redis connection validation

**Example - Application Startup:**
```python
# ✅ Recommended: Factory method with environment-specific defaults
async def setup_cache_layer():
    factory = CacheFactory()
    
    # Production web application
    cache = await factory.for_web_app(
        redis_url=settings.redis_url,
        default_ttl=1800,  # 30 minutes
        security_config=security_config,
        fail_on_connection_error=True
    )
    
    return cache
```

### When to Use Direct Instantiation

**⚠️ Use direct instantiation for:**

1. **Fine-Grained Control** - When you need specific parameter combinations
2. **Custom Cache Implementations** - Building specialized cache behaviors
3. **Testing Scenarios** - When you need exact control over cache behavior
4. **Library/Framework Development** - When building reusable cache components
5. **Performance-Critical Paths** - When you need to bypass factory validation overhead
6. **Legacy Code Migration** - Maintaining compatibility during migration

**Direct Instantiation Considerations:**
- **Manual Parameter Management**: You handle all parameter validation
- **No Automatic Fallback**: Must implement your own error handling
- **Security Configuration**: Must manually configure security settings
- **Connection Management**: Must handle Redis connection testing yourself

**Example - Custom Cache Implementation:**
```python
# ⚠️ Direct instantiation: When you need fine-grained control
async def setup_custom_cache():
    # Custom AIResponseCache with specific parameters
    cache = AIResponseCache(
        redis_url="redis://custom-host:6380/5",
        default_ttl=7200,
        text_hash_threshold=2000,
        compression_threshold=500,
        compression_level=9,
        l1_cache_size=300,
        enable_l1_cache=True,
        operation_ttls={"custom_op": 1800},
        performance_monitor=custom_monitor,
        security_config=custom_security,
        fail_on_connection_error=True
    )
    
    # Manual connection handling (no automatic fallback)
    connected = await cache.connect()
    if not connected:
        raise InfrastructureError("Cache connection required for this service")
    
    return cache
```

### Migration Path: Direct → Factory

**Migrating from direct instantiation to factory methods:**

```python
# Before: Direct instantiation
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    text_hash_threshold=1000,
    memory_cache_size=150,  # deprecated parameter
    compression_threshold=1000
)

# After: Factory method with equivalent configuration
factory = CacheFactory()
cache = await factory.for_ai_app(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    text_hash_threshold=1000,
    l1_cache_size=150,  # modern parameter
    compression_threshold=1000
)
```

### Best Practices Summary

**🎯 Recommended Approach:**
1. **Start with factory methods** for 90% of use cases
2. **Use environment-specific factory methods** (`for_web_app`, `for_ai_app`, `for_testing`)
3. **Leverage configuration-based creation** for dynamic environments
4. **Reserve direct instantiation** for specialized requirements
5. **Always handle connection failures** regardless of approach
6. **Use security configuration** in production environments

**🔒 Security Considerations:**
- Factory methods include built-in security configuration validation
- Direct instantiation requires manual security setup
- Always use `security_config` parameter in production
- Consider `fail_on_connection_error=True` for production deployments

This design provides optimized defaults for different application types.

## Legacy Parameter Migration Guide

### Overview

This guide helps migrate from legacy parameter names to modern equivalents while maintaining backward compatibility. All legacy parameters are still supported but will generate deprecation warnings.

### Parameter Migration Table

| Legacy Parameter | Modern Parameter | Notes |
|-----------------|------------------|--------|
| `memory_cache_size` | `l1_cache_size` | Controls L1 memory cache size |
| `redis_cache_size` | Not applicable | No longer needed, Redis handles capacity |
| `cache_size` | `l1_cache_size` | Generic cache size parameter |

### Migration Examples

#### AIResponseCache Parameter Migration

**Before (Legacy):**
```python
# ⚠️ Uses deprecated parameters
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    memory_cache_size=200,  # DEPRECATED
    compression_threshold=1000
)
```

**After (Modern):**
```python
# ✅ Uses current parameters
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    l1_cache_size=200,  # Modern parameter
    compression_threshold=1000
)

# Or use factory method (recommended)
factory = CacheFactory()
cache = await factory.for_ai_app(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    l1_cache_size=200,
    compression_threshold=1000
)
```

#### Mixed Legacy/Modern Parameters

**Current (Backward Compatible):**
```python
# ✅ Mixing legacy and modern parameters works
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    memory_cache_size=200,  # Legacy (generates warning)
    l1_cache_size=300,      # Modern (takes precedence)
    compression_threshold=1000
)
# Result: l1_cache_size=300 (modern parameter wins)
```

### Migration Strategy

#### Phase 1: Identify Legacy Usage

**Search for legacy parameters in your codebase:**
```bash
# Find legacy parameter usage
grep -r "memory_cache_size" --include="*.py" .
grep -r "redis_cache_size" --include="*.py" .
grep -r "cache_size.*=" --include="*.py" .
```

#### Phase 2: Replace with Modern Equivalents

**Parameter Replacement Rules:**
1. **Replace `memory_cache_size`** → **`l1_cache_size`**
2. **Remove `redis_cache_size`** (no longer needed)
3. **Update constructor calls** to use modern parameters
4. **Consider factory methods** for new code

#### Phase 3: Validate Migration

**Test backward compatibility:**

.. code-block:: python

    import warnings
    import pytest

    def test_legacy_parameter_compatibility():
        '''Test that legacy parameters still work with warnings.'''
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Legacy parameter should work
            cache = AIResponseCache(
                redis_url="redis://localhost:6379",
                memory_cache_size=100  # Legacy parameter
            )
            
            # Should generate deprecation warning
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            
            # Should still function correctly
            assert cache.l1_cache_size == 100

### Deprecation Timeline

| Version | Status | Action Required |
|---------|--------|-----------------|
| Current | **Backward Compatible** | Legacy parameters work with warnings |
| Next Minor | **Deprecation Warnings** | Update code to use modern parameters |
| Next Major | **Legacy Removal** | Legacy parameters will be removed |

### Automated Migration Script

**Use this script to automatically migrate parameters:**

.. code-block:: python

    #!/usr/bin/env python3
    '''
    Automatic migration script for cache parameter updates.
    Run from project root: python scripts/migrate_cache_parameters.py
    '''

    import re
    import os
    from pathlib import Path

    def migrate_file(file_path: Path):
        '''Migrate cache parameters in a single file.'''
        content = file_path.read_text()
        original_content = content
        
        # Replace memory_cache_size with l1_cache_size
        content = re.sub(
            r'\bmemory_cache_size\s*=',
            'l1_cache_size=',
            content
        )
        
        # Remove redis_cache_size parameters
        content = re.sub(
            r',?\s*redis_cache_size\s*=[^,\n)]+',
            '',
            content
        )
        
        if content != original_content:
            file_path.write_text(content)
            print(f"Updated: {file_path}")
            return True
        return False

    def main():
        '''Migrate all Python files in the project.'''
        python_files = list(Path('.').rglob('*.py'))
        updated_count = 0
        
        for file_path in python_files:
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            if migrate_file(file_path):
                updated_count += 1
        
        print(f"Migration complete. Updated {updated_count} files.")

    if __name__ == "__main__":
        main()

### Best Practices for New Code

**✅ Recommended Patterns:**
1. **Use factory methods** instead of direct instantiation
2. **Use modern parameter names** (`l1_cache_size` not `memory_cache_size`)
3. **Include security configuration** for production deployments
4. **Handle connection failures** with appropriate error handling
5. **Use preset-based configuration** where possible

**❌ Avoid These Patterns:**
1. **Don't use legacy parameters** in new code
2. **Don't ignore deprecation warnings** in development
3. **Don't mix legacy and modern parameters** unnecessarily
4. **Don't skip error handling** for connection failures

Performance Considerations:
    - Factory methods execute in <10ms for typical configurations
    - Redis connection validation adds 5-50ms depending on network latency
    - Fallback to InMemoryCache is instantaneous (<1ms)
    - All factory methods are async to support connection validation

Error Handling:
    - ConfigurationError: Invalid parameters or configuration conflicts
    - ValidationError: Input validation failures with specific field information
    - InfrastructureError: Redis connection or infrastructure issues
    - All errors include context data for debugging and monitoring

Dependencies:
    Required:
        - app.infrastructure.cache.base.CacheInterface: Cache interface contract
        - app.infrastructure.cache.redis_generic.GenericRedisCache: Generic Redis cache
        - app.infrastructure.cache.redis_ai.AIResponseCache: AI-specialized cache
        - app.infrastructure.cache.memory.InMemoryCache: Memory fallback cache
        - app.core.exceptions: Custom exception hierarchy

    Optional:
        - redis.asyncio: Redis connectivity (graceful degradation if unavailable)
        - app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking

## CacheFactory

Factory class for explicit cache instantiation with environment-optimized defaults.

This factory provides deterministic cache creation for different use cases,
replacing auto-detection patterns with explicit configuration. Each factory
method returns a fully configured cache instance optimized for specific
application types and environments.

Factory Methods:
    - for_web_app(): Web application cache with balanced performance
    - for_ai_app(): AI application cache with enhanced storage and compression
    - for_testing(): Testing cache with short TTLs and test database support
    - create_cache_from_config(): Configuration-driven cache creation

Error Handling:
    All factory methods include comprehensive error handling with fallback
    to InMemoryCache when Redis is unavailable. Errors are logged with
    context information for debugging and monitoring.

Example:
    >>> factory = CacheFactory()
    >>> cache = await factory.for_web_app(redis_url="redis://localhost:6379")
    >>> isinstance(cache, GenericRedisCache)
    True

### __init__()

```python
def __init__(self):
```

Initialize the CacheFactory with default configuration.

### for_web_app()

```python
async def for_web_app(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 1800, enable_l1_cache: bool = True, l1_cache_size: int = 200, compression_threshold: int = 2000, compression_level: int = 6, security_config: Optional['SecurityConfig'] = None, fail_on_connection_error: bool = False, **kwargs) -> CacheInterface:
```

Create a cache optimized for web applications with balanced performance.

This factory method creates a GenericRedisCache configured with defaults
optimized for typical web application caching patterns. It provides
balanced performance between memory usage and cache hit rates, with
moderate TTLs suitable for session data, API responses, and page caching.

Web Application Optimizations:
    - 30-minute default TTL for reasonable session/data freshness
    - L1 memory cache enabled for fastest access to frequently used data
    - 200-item L1 cache size for good memory usage vs. hit rate balance
    - 2KB compression threshold to optimize network and storage
    - Moderate compression level (6) for balanced speed vs. compression ratio
    - Graceful Redis fallback for high availability

Args:
    redis_url: Redis server URL (default: "redis://redis:6379")
    default_ttl: Default time-to-live in seconds (default: 1800/30min)
    enable_l1_cache: Enable in-memory L1 cache (default: True)
    l1_cache_size: Maximum L1 cache entries (default: 200)
    compression_threshold: Compress data above this size in bytes (default: 2000)
    compression_level: Zlib compression level 1-9 (default: 6)
    fail_on_connection_error: Raise error if Redis unavailable (default: False)
    **kwargs: Additional parameters passed to GenericRedisCache

Returns:
    CacheInterface: Configured cache instance (GenericRedisCache or InMemoryCache fallback)

Raises:
    ValidationError: Invalid parameter values or combinations
    ConfigurationError: Configuration conflicts or missing requirements
    InfrastructureError: Redis connection failed and fail_on_connection_error=True

Examples:
    Basic web application cache:
        >>> factory = CacheFactory()
        >>> cache = await factory.for_web_app()
        >>> await cache.set("session:abc123", {"user_id": 456})

    Production web cache with security configuration:
        >>> from app.infrastructure.security import SecurityConfig
        >>> security_config = SecurityConfig(
        ...     redis_auth="secure-password",
        ...     use_tls=True,
        ...     verify_certificates=True
        ... )
        >>> cache = await factory.for_web_app(
        ...     redis_url="rediss://production:6380",  # TLS connection
        ...     default_ttl=3600,  # 1 hour
        ...     security_config=security_config,
        ...     fail_on_connection_error=True
        ... )

    Development web cache with authentication:
        >>> security_config = SecurityConfig(redis_auth="dev-password")
        >>> cache = await factory.for_web_app(
        ...     redis_url="redis://dev-server:6379",
        ...     security_config=security_config,
        ...     fail_on_connection_error=False  # Fallback to memory
        ... )

    High-performance web cache:
        >>> cache = await factory.for_web_app(
        ...     l1_cache_size=500,
        ...     compression_threshold=5000,
        ...     compression_level=9
        ... )

### for_ai_app()

```python
async def for_ai_app(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 3600, enable_l1_cache: bool = True, l1_cache_size: int = 100, compression_threshold: int = 1000, compression_level: int = 6, text_hash_threshold: int = 500, memory_cache_size: Optional[int] = None, operation_ttls: Optional[Dict[str, int]] = None, security_config: Optional['SecurityConfig'] = None, fail_on_connection_error: bool = False, **kwargs) -> CacheInterface:
```

Create a cache optimized for AI applications with enhanced storage and compression.

This factory method creates an AIResponseCache configured with defaults
optimized for AI workloads. It provides enhanced compression for large AI
responses, operation-specific TTLs, intelligent key generation, and
performance optimizations for typical AI usage patterns.

AI Application Optimizations:
    - 1-hour default TTL for reasonable AI response freshness
    - Lower compression threshold (1KB) for better storage efficiency
    - 100-item L1 cache for frequently accessed AI responses
    - Text hashing threshold for intelligent key generation
    - Operation-specific TTLs for different AI operations
    - Enhanced monitoring for AI-specific metrics

Args:
    redis_url: Redis server URL (default: "redis://redis:6379")
    default_ttl: Default time-to-live in seconds (default: 3600/1hr)
    enable_l1_cache: Enable in-memory L1 cache (default: True)
    l1_cache_size: Maximum L1 cache entries (default: 100)
    compression_threshold: Compress data above this size in bytes (default: 1000)
    compression_level: Zlib compression level 1-9 (default: 6)
    text_hash_threshold: Hash text above this length for keys (default: 500)
    memory_cache_size: Override l1_cache_size if provided
    operation_ttls: Custom TTLs per AI operation type
    fail_on_connection_error: Raise error if Redis unavailable (default: False)
    **kwargs: Additional parameters passed to AIResponseCache

Returns:
    CacheInterface: Configured AIResponseCache or InMemoryCache fallback

Raises:
    ValidationError: Invalid parameter values or combinations
    ConfigurationError: Configuration conflicts or missing requirements
    InfrastructureError: Redis connection failed and fail_on_connection_error=True

Examples:
    Basic AI application cache:
        >>> factory = CacheFactory()
        >>> cache = await factory.for_ai_app()
        >>> # Use standard interface for caching
        >>> cache_key = cache.build_key("Document to analyze...", "summarize", {"max_length": 100})
        >>> await cache.set(cache_key, {"summary": "Brief summary"}, ttl=3600)

    Production AI cache with security configuration:
        >>> from app.infrastructure.security import SecurityConfig
        >>> security_config = SecurityConfig(
        ...     redis_auth="ai-cache-password",
        ...     use_tls=True,
        ...     verify_certificates=True,
        ...     enable_security_monitoring=True
        ... )
        >>> cache = await factory.for_ai_app(
        ...     redis_url="rediss://ai-production:6380",  # Secure TLS connection
        ...     default_ttl=7200,  # 2 hours
        ...     security_config=security_config,
        ...     operation_ttls={
        ...         "summarize": 1800,  # 30 minutes
        ...         "sentiment": 3600,  # 1 hour
        ...         "translate": 7200   # 2 hours
        ...     },
        ...     fail_on_connection_error=True  # Strict security
        ... )

    Development AI cache with authentication:
        >>> security_config = SecurityConfig(
        ...     redis_auth="dev-ai-password",
        ...     connection_timeout=10
        ... )
        >>> cache = await factory.for_ai_app(
        ...     redis_url="redis://ai-dev:6379",
        ...     security_config=security_config,
        ...     fail_on_connection_error=False  # Allow fallback
        ... )

    High-compression AI cache:
        >>> cache = await factory.for_ai_app(
        ...     compression_threshold=500,
        ...     compression_level=9,
        ...     text_hash_threshold=200
        ... )

### for_testing()

```python
async def for_testing(self, redis_url: str = 'redis://redis:6379/15', default_ttl: int = 60, enable_l1_cache: bool = False, l1_cache_size: int = 50, compression_threshold: int = 1000, compression_level: int = 1, security_config: Optional['SecurityConfig'] = None, fail_on_connection_error: bool = False, use_memory_cache: bool = False, **kwargs) -> CacheInterface:
```

Create a cache optimized for testing environments with short TTLs and fast operations.

This factory method creates a cache configured for testing scenarios with
short TTLs, minimal memory usage, fast operations, and support for Redis
test databases. It can also return a pure InMemoryCache for isolated testing.

Testing Optimizations:
    - 1-minute default TTL for quick test data expiration
    - Redis database 15 by default for test isolation
    - L1 cache disabled to simplify testing behavior
    - Fast compression (level 1) for minimal test overhead
    - Small cache sizes for minimal memory usage
    - Option to use InMemoryCache for isolated tests

Args:
    redis_url: Redis server URL with test DB (default: "redis://redis:6379/15")
    default_ttl: Default time-to-live in seconds (default: 60/1min)
    enable_l1_cache: Enable in-memory L1 cache (default: False)
    l1_cache_size: Maximum L1 cache entries (default: 50)
    compression_threshold: Compress data above this size in bytes (default: 1000)
    compression_level: Zlib compression level 1-9 (default: 1)
    fail_on_connection_error: Raise error if Redis unavailable (default: False)
    use_memory_cache: Force InMemoryCache usage (default: False)
    **kwargs: Additional parameters passed to cache implementation

Returns:
    CacheInterface: Configured cache instance optimized for testing

Raises:
    ValidationError: Invalid parameter values or combinations
    ConfigurationError: Configuration conflicts or missing requirements
    InfrastructureError: Redis connection failed and fail_on_connection_error=True

Examples:
    Basic testing cache:
        >>> factory = CacheFactory()
        >>> cache = await factory.for_testing()
        >>> await cache.set("test_key", "test_value")

    Memory-only testing cache:
        >>> cache = await factory.for_testing(use_memory_cache=True)
        >>> # Guaranteed to be InMemoryCache

    Testing with security configuration:
        >>> from app.infrastructure.security import SecurityConfig
        >>> security_config = SecurityConfig(
        ...     redis_auth="test-password",
        ...     connection_timeout=5,
        ...     enable_security_monitoring=False  # Reduced overhead for tests
        ... )
        >>> cache = await factory.for_testing(
        ...     redis_url="redis://test-server:6379/10",
        ...     security_config=security_config,
        ...     default_ttl=30,  # 30 seconds
        ...     fail_on_connection_error=False  # Allow fallback in tests
        ... )

    Strict testing with connection requirements:
        >>> security_config = SecurityConfig(redis_auth="strict-test-auth")
        >>> cache = await factory.for_testing(
        ...     redis_url="redis://secure-test:6379/15",
        ...     security_config=security_config,
        ...     fail_on_connection_error=True,
        ...     enable_l1_cache=True
        ... )

### create_cache_from_config()

```python
async def create_cache_from_config(self, config: Dict[str, Any], fail_on_connection_error: bool = False) -> CacheInterface:
```

Create a cache instance from a configuration dictionary with flexible parameter support.

This factory method provides maximum flexibility by accepting a configuration
dictionary and automatically determining the appropriate cache type based on
the provided parameters. It supports both GenericRedisCache and AIResponseCache
configurations with automatic parameter mapping and validation.

Configuration Detection:
    - If AI-specific parameters are present (text_hash_threshold, operation_ttls),
      creates an AIResponseCache
    - Otherwise, creates a GenericRedisCache
    - Automatically handles parameter mapping and validation
    - Provides comprehensive error messages for invalid configurations

Args:
    config: Configuration dictionary with cache parameters
    fail_on_connection_error: Raise error if Redis unavailable (default: False)

Required Configuration Keys:
    - redis_url (str): Redis server URL

Optional Configuration Keys:
    Common parameters:
        - default_ttl (int): Default time-to-live in seconds
        - enable_l1_cache (bool): Enable in-memory L1 cache
        - l1_cache_size (int): Maximum L1 cache entries
        - compression_threshold (int): Compress data above this size
        - compression_level (int): Zlib compression level 1-9

    AI-specific parameters (triggers AIResponseCache):
        - text_hash_threshold (int): Hash text above this length
        - operation_ttls (Dict[str, int]): Custom TTLs per operation
        - memory_cache_size (int): Override l1_cache_size

Returns:
    CacheInterface: Configured cache instance based on configuration

Raises:
    ValidationError: Invalid configuration parameters or missing required keys
    ConfigurationError: Configuration conflicts or incompatible parameters
    InfrastructureError: Redis connection failed and fail_on_connection_error=True

Examples:
    Basic Redis cache configuration:
        >>> config = {
        ...     "redis_url": "redis://localhost:6379",
        ...     "default_ttl": 3600,
        ...     "enable_l1_cache": True,
        ...     "compression_threshold": 2000
        ... }
        >>> cache = await factory.create_cache_from_config(config)
        >>> isinstance(cache, GenericRedisCache)
        True

    AI cache configuration with security:
        >>> from app.infrastructure.security import SecurityConfig
        >>> security_config = SecurityConfig(
        ...     redis_auth="ai-password",
        ...     use_tls=True
        ... )
        >>> config = {
        ...     "redis_url": "rediss://ai-cache:6380",
        ...     "default_ttl": 7200,
        ...     "text_hash_threshold": 500,
        ...     "operation_ttls": {"summarize": 1800, "sentiment": 3600},
        ...     "security_config": security_config
        ... }
        >>> cache = await factory.create_cache_from_config(config)
        >>> isinstance(cache, AIResponseCache)
        True

    Production configuration with strict security:
        >>> security_config = SecurityConfig(
        ...     redis_auth="production-password",
        ...     use_tls=True,
        ...     verify_certificates=True,
        ...     enable_security_monitoring=True
        ... )
        >>> config = {
        ...     "redis_url": "rediss://production:6380",
        ...     "default_ttl": 3600,
        ...     "compression_level": 9,
        ...     "enable_l1_cache": True,
        ...     "l1_cache_size": 500,
        ...     "security_config": security_config
        ... }
        >>> cache = await factory.create_cache_from_config(
        ...     config,
        ...     fail_on_connection_error=True
        ... )
