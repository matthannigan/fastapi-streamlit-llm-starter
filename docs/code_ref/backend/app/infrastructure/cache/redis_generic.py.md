---
sidebar_label: redis_generic
---

# Generic Redis cache implementation with L1 memory cache and advanced features.

  file_path: `backend/app/infrastructure/cache/redis_generic.py`

This module provides a flexible Redis-backed cache implementation that serves as the
foundation for specialized caches. It includes a two-tier architecture with memory
cache (L1) and Redis persistence (L2), along with compression and monitoring.

## Classes

**GenericRedisCache**: Flexible Redis cache with L1 memory cache, compression,
and comprehensive monitoring. Serves as the base class for specialized implementations
like AIResponseCache.

## Key Features

- **Two-Tier Architecture**: L1 memory cache + L2 Redis persistence
- **Intelligent Compression**: Configurable compression with performance monitoring
- **Graceful Degradation**: Falls back to memory-only mode when Redis unavailable
- **Advanced Monitoring**: Comprehensive metrics and performance analytics
- **Flexible Serialization**: Support for JSON and pickle serialization
- **Connection Management**: Robust Redis connection handling with retry logic

## Usage Patterns

### Factory Method (Recommended)

**Most applications should use factory methods for optimized defaults and built-in validation:**

```python
from app.infrastructure.cache import CacheFactory

factory = CacheFactory()

# Web applications - recommended approach
cache = await factory.for_web_app(
    redis_url="redis://localhost:6379",
    default_ttl=1800,  # 30 minutes
    compression_threshold=2000
)

# Production with security
from app.infrastructure.security import SecurityConfig
security_config = SecurityConfig(redis_auth="secure-password", use_tls=True)
cache = await factory.for_web_app(
    redis_url="rediss://production:6380",
    security_config=security_config,
    fail_on_connection_error=True
)
```

**Factory Method Benefits:**
- Environment-optimized defaults for web applications
- Comprehensive parameter validation with detailed error messages
- Automatic fallback to InMemoryCache when Redis unavailable
- Built-in security configuration and TLS support
- Structured error handling with proper context

### Direct Instantiation (Advanced Use Cases)

**Use direct instantiation for fine-grained control or custom implementations:**

```python
cache = GenericRedisCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    enable_l1_cache=True,
    l1_cache_size=200,
    compression_threshold=2000,
    compression_level=6
)

# Manual connection handling required
connected = await cache.connect()
if not connected:
    raise InfrastructureError("Redis connection required for this service")

# Standard cache operations
await cache.set("user:123", {"name": "John", "age": 30}, ttl=3600)
user_data = await cache.get("user:123")
await cache.delete("user:123")
```

**Use direct instantiation when:**
- Building custom cache implementations with specialized requirements
- Requiring exact parameter combinations not supported by factory methods
- Developing reusable cache components or frameworks
- Migrating legacy code with specific configuration needs

**📖 For comprehensive factory usage patterns and configuration examples, see [Cache Usage Guide](../../../docs/guides/infrastructure/cache/usage-guide.md).**

## GenericRedisCache

Generic Redis cache with L1 memory tier, compression, and monitoring.

### Overview
This class provides a generic Redis-backed cache with an optional L1 in-memory
cache for improved performance. It supports automatic data compression,
comprehensive performance monitoring, and an extensible callback system.

### Parameters
- `redis_url` (str): URL for the Redis server.
- `default_ttl` (int): Default time-to-live for cache entries in seconds.
- `enable_l1_cache` (bool): If True, use an in-memory L1 cache.
- `l1_cache_size` (int): Maximum number of items in the L1 cache.
- `compression_threshold` (int): Data size in bytes above which to compress.
- `compression_level` (int): Zlib compression level (1-9).
- `performance_monitor` (CachePerformanceMonitor): Instance for tracking metrics.
- `security_config` (SecurityConfig): Optional security configuration.
- `fail_on_connection_error` (bool): If True, raise InfrastructureError when Redis unavailable.
                                    If False (default), gracefully fallback to memory-only mode.

### Returns
A `GenericRedisCache` instance.

### Examples
```python
monitor = CachePerformanceMonitor()
cache = GenericRedisCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    enable_l1_cache=True,
    performance_monitor=monitor
)
await cache.connect()
await cache.set("my_key", {"data": "value"})
result = await cache.get("my_key")
print(result)
# Output: {'data': 'value'}
```

### __init__()

```python
def __init__(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 3600, enable_l1_cache: bool = True, l1_cache_size: int = 100, compression_threshold: int = 1000, compression_level: int = 6, performance_monitor: Optional[CachePerformanceMonitor] = None, security_config: Optional['SecurityConfig'] = None, fail_on_connection_error: bool = False, **kwargs):
```

### register_callback()

```python
def register_callback(self, event: str, callback: Callable):
```

Register a callback for cache events.

### Overview
Registers a callback function to be executed when specific cache events
occur. Supported events: get_success, get_miss, set_success, delete_success.

### Parameters
- `event` (str): The event name to register for.
- `callback` (Callable): The callback function to execute.

### Examples
```python
def on_cache_hit(key, value):
    print(f"Cache hit for key: {key}")

cache.register_callback('get_success', on_cache_hit)
```

### connect()

```python
async def connect(self) -> bool:
```

Initialize Redis connection with security features and graceful degradation.

### Overview
Attempts to establish a connection to Redis. If a security manager is configured,
it uses secure connection features including authentication, TLS encryption, and
security validation. If Redis is unavailable or the connection fails, the cache
operates in memory-only mode.

### Returns
True if connected to Redis successfully, False otherwise.

### Examples
```python
# Basic connection
cache = GenericRedisCache()
connected = await cache.connect()
if not connected:
    print("Using memory-only mode")

# Secure connection
security_config = SecurityConfig(redis_auth="password", use_tls=True)
cache = GenericRedisCache(security_config=security_config)
connected = await cache.connect()
```

### disconnect()

```python
async def disconnect(self):
```

Disconnect from Redis server.

### Overview
Cleanly closes the Redis connection. This is a no-op if Redis
is not available or not connected.

### Examples
```python
await cache.disconnect()
```

### get()

```python
async def get(self, key: str) -> Any:
```

Get a value from the cache with L1 cache check first.

### Overview
Attempts to retrieve a cached value, first from the L1 memory cache
(if enabled), then from Redis. Includes performance monitoring and
callback notifications.

### Parameters
- `key` (str): The cache key to retrieve.

### Returns
The cached value if found, None otherwise.

### Examples
```python
value = await cache.get("user:123")
if value:
    print(f"Found: {value}")
else:
    print("Cache miss")
```

### set()

```python
async def set(self, key: str, value: Any, ttl: Optional[int] = None):
```

Set a value in the cache with optional TTL.

### Overview
Stores a value in both the L1 memory cache (if enabled) and Redis.
Automatically compresses large values and records performance metrics.

### Parameters
- `key` (str): The cache key.
- `value` (Any): The value to cache.
- `ttl` (Optional[int]): Time-to-live in seconds. Uses default if None.

### Examples
```python
await cache.set("user:123", {"name": "John"}, ttl=3600)
await cache.set("temp_data", "value")  # Uses default TTL
```

### delete()

```python
async def delete(self, key: str) -> bool:
```

Delete a key from both L1 cache and Redis.

### Overview
Removes a key from both cache tiers and records the operation.

### Parameters
- `key` (str): The cache key to delete.

### Returns
True if the key existed and was deleted, False otherwise.

### Examples
```python
deleted = await cache.delete("user:123")
if deleted:
    print("Key deleted successfully")
```

### exists()

```python
async def exists(self, key: str) -> bool:
```

Check if a key exists in either cache tier.

### Overview
Checks for key existence in L1 cache first, then Redis.

### Parameters
- `key` (str): The cache key to check.

### Returns
True if the key exists, False otherwise.

### Examples
```python
if await cache.exists("user:123"):
    print("Key exists")
```

### validate_security()

```python
async def validate_security(self):
```

Validate Redis connection security if security manager is available.

### Overview
Performs comprehensive security validation of the Redis connection
including authentication, encryption, and certificate checks.

### Returns
SecurityValidationResult if security manager is available, None otherwise.

### Examples
```python
cache = GenericRedisCache(security_config=security_config)
await cache.connect()
validation = await cache.validate_security()
if validation and not validation.is_secure:
    print(f"Security issues: {validation.vulnerabilities}")
```

### get_security_status()

```python
def get_security_status(self) -> Dict[str, Any]:
```

Get current security configuration and status.

### Overview
Returns information about the current security configuration,
connection status, and any recent security validations.

### Returns
Dictionary containing security status information.

### Examples
```python
cache = GenericRedisCache(security_config=security_config)
status = cache.get_security_status()
print(f"Security level: {status['security_level']}")
```

### get_security_recommendations()

```python
def get_security_recommendations(self) -> List[str]:
```

Get security recommendations for the current configuration.

### Overview
Returns a list of security recommendations based on the current
configuration and any security validations performed.

### Returns
List of security recommendations.

### Examples
```python
cache = GenericRedisCache(security_config=security_config)
recommendations = cache.get_security_recommendations()
for rec in recommendations:
    print(f"💡 {rec}")
```

### generate_security_report()

```python
async def generate_security_report(self) -> str:
```

Generate comprehensive security assessment report.

### Overview
Creates a detailed security report including configuration status,
validation results, vulnerabilities, and recommendations.

### Returns
Formatted security report string.

### Examples
```python
cache = GenericRedisCache(security_config=security_config)
await cache.connect()
await cache.validate_security()
report = await cache.generate_security_report()
print(report)
```

### test_security_configuration()

```python
async def test_security_configuration(self) -> Dict[str, Any]:
```

Test the security configuration comprehensively.

### Overview
Performs comprehensive testing of the security configuration
including connection tests, authentication validation, and encryption checks.

### Returns
Dictionary with detailed test results.

### Examples
```python
cache = GenericRedisCache(security_config=security_config)
results = await cache.test_security_configuration()
print(f"Overall secure: {results['overall_secure']}")
if results['errors']:
    for error in results['errors']:
        print(f"❌ {error}")
```
