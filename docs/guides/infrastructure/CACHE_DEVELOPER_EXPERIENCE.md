---
sidebar_label: Cache Developer Experience
title: Cache Infrastructure Developer Experience Guide
description: Comprehensive developer experience guide for immediate cache productivity with quick setup patterns, decision trees, debugging workflows, and optimization strategies
---

# Cache Infrastructure Developer Experience Guide

This guide provides developers with everything needed to be immediately productive with the cache infrastructure, from instant setup patterns to advanced optimization strategies. Whether you're new to the project or optimizing production performance, this guide delivers actionable solutions.

## 🚀 5-Minute Quickstart

### One-Line Cache Setup

Get a working cache in seconds with sensible defaults:

```python
# Web Application (most common)
from app.infrastructure.cache import CacheFactory
factory = CacheFactory()
cache = await factory.for_web_app()  # Redis + memory fallback

# AI Application  
cache = await factory.for_ai_app()  # AI-optimized with compression

# Testing/Development
cache = await factory.for_testing(use_memory_cache=True)  # Memory-only
```

### Instant Productivity Examples

**Session Storage (Web Apps)**:
```python
# Store user session
await cache.set(f"session:{session_id}", {
    "user_id": 123,
    "role": "admin",
    "preferences": {"theme": "dark"}
}, ttl=1800)  # 30 minutes

# Retrieve session
session = await cache.get(f"session:{session_id}")
if session:
    print(f"Welcome back, user {session['user_id']}")
```

**API Response Caching**:
```python
# Cache expensive API calls
cache_key = f"api:weather:{city}:{date}"
weather_data = await cache.get(cache_key)

if not weather_data:
    weather_data = await expensive_weather_api(city, date)
    await cache.set(cache_key, weather_data, ttl=3600)  # 1 hour

return weather_data
```

**AI Response Caching**:
```python
# Cache AI responses automatically
await cache.cache_response(
    text="Analyze this document...",
    operation="summarize",
    options={"max_length": 100},
    response={"summary": "Brief overview..."}
)

# Retrieve cached AI response
cached = await cache.get_cached_response(
    text="Analyze this document...",
    operation="summarize", 
    options={"max_length": 100}
)
```

## 🎯 Cache Type Decision Tree

### Choose Your Cache Type

```
┌─ What are you building?
│
├─ 🌐 **Web Application**
│   ├─ Sessions, API responses, page cache
│   ├─ → Use: `factory.for_web_app()`
│   └─ Features: Redis + L1 memory, 30min TTL, balanced compression
│
├─ 🤖 **AI/LLM Application**  
│   ├─ AI responses, model outputs, embeddings
│   ├─ → Use: `factory.for_ai_app()`
│   └─ Features: Smart compression, operation TTLs, text hashing
│
├─ 🧪 **Testing/Development**
│   ├─ Unit tests, integration tests, local dev
│   ├─ → Use: `factory.for_testing(use_memory_cache=True)`
│   └─ Features: Memory-only, fast operations, 1min TTL
│
└─ ⚙️ **Custom Requirements**
    ├─ Specific config, existing Redis setup, microservices
    ├─ → Use: `factory.create_cache_from_config(config)`
    └─ Features: Full control, parameter validation, auto-detection
```

### Performance Characteristics

| Cache Type | Speed | Persistence | Memory Usage | Best For |
|------------|-------|-------------|--------------|----------|
| **InMemoryCache** | ⚡ Fastest (~0.1ms) | ❌ No | 🟡 Medium | Testing, dev |
| **GenericRedisCache** | 🚀 Fast (~2-5ms) | ✅ Yes | 🟢 Low | Web apps |
| **AIResponseCache** | 🚀 Fast (~2-5ms) | ✅ Yes | 🟡 Medium | AI apps |

### Environment-Based Recommendations

```python
# Development Environment
if settings.debug:
    cache = await factory.for_testing(use_memory_cache=True)
    
# Staging Environment  
elif settings.environment == "staging":
    cache = await factory.for_web_app(
        redis_url="redis://staging-redis:6379",
        default_ttl=900  # 15 minutes
    )
    
# Production Environment
else:
    cache = await factory.for_web_app(
        redis_url=settings.redis_url,
        default_ttl=3600,  # 1 hour
        fail_on_connection_error=True,
        l1_cache_size=500  # Larger memory cache
    )
```

## ⚠️ Common Pitfalls & Solutions

### Pitfall 1: Cache Key Inconsistency

**Problem**: Different key formats causing cache misses

```python
# ❌ BAD: Inconsistent key generation
await cache.set(f"user_{user_id}", data)
await cache.set(f"user:{user_id}", data)  # Different format!
```

**Solution**: Use consistent key patterns

```python
# ✅ GOOD: Consistent hierarchical keys
def user_cache_key(user_id: int) -> str:
    return f"user:profile:{user_id}"

def session_cache_key(session_id: str) -> str:
    return f"session:active:{session_id}"

# Use consistently throughout app
await cache.set(user_cache_key(123), user_data)
cached_user = await cache.get(user_cache_key(123))
```

### Pitfall 2: TTL Confusion

**Problem**: Data expires too quickly or stays too long

```python
# ❌ BAD: No TTL strategy
await cache.set("user_prefs", data)  # Uses default, may be wrong
await cache.set("api_response", data, ttl=86400)  # 24h too long for dynamic data
```

**Solution**: Match TTL to data characteristics

```python
# ✅ GOOD: TTL based on data type
TTL_STRATEGIES = {
    "session": 1800,        # 30 minutes - user activity
    "user_profile": 3600,   # 1 hour - changes occasionally  
    "api_weather": 1800,    # 30 minutes - changes frequently
    "static_config": 86400, # 24 hours - rarely changes
    "ai_summary": 7200,     # 2 hours - content-dependent
}

await cache.set(session_key, session_data, ttl=TTL_STRATEGIES["session"])
await cache.set(weather_key, weather_data, ttl=TTL_STRATEGIES["api_weather"])
```

### Pitfall 3: Memory Leaks in Development

**Problem**: InMemoryCache grows without bounds

```python
# ❌ BAD: No size limits in dev
cache = InMemoryCache()  # Unlimited growth
for i in range(100000):
    await cache.set(f"test_{i}", large_data)  # Memory explosion!
```

**Solution**: Always set memory limits

```python
# ✅ GOOD: Bounded memory usage
cache = InMemoryCache(
    max_size=1000,     # Limit entries
    default_ttl=300    # 5 minute expiration
)

# Or use factory defaults
cache = await factory.for_testing()  # Already has limits
```

### Pitfall 4: Redis Connection Errors

**Problem**: App crashes when Redis unavailable

```python
# ❌ BAD: No error handling
cache = GenericRedisCache(redis_url="redis://redis:6379")
await cache.connect()  # May throw unhandled exception
```

**Solution**: Use factory with graceful fallback

```python
# ✅ GOOD: Automatic fallback
cache = await factory.for_web_app(
    redis_url="redis://redis:6379",
    fail_on_connection_error=False  # Falls back to memory
)

# App continues working even if Redis is down
await cache.set("key", "value")  # Works with memory fallback
```

### Pitfall 5: AI Cache Parameter Mismatches

**Problem**: AI cache not working due to parameter inconsistency

```python
# ❌ BAD: Inconsistent options format
await cache.cache_response(
    text="Analyze this",
    operation="summarize",
    options={"length": 100},  # Different key name
    response=summary
)

# Later retrieval with different options
cached = await cache.get_cached_response(
    text="Analyze this", 
    operation="summarize",
    options={"max_length": 100}  # Won't match!
)
```

**Solution**: Use consistent option schemas

```python
# ✅ GOOD: Standardized options schema
OPERATION_SCHEMAS = {
    "summarize": {"max_length": int, "style": str},
    "sentiment": {"confidence_threshold": float},
    "qa": {"question": str, "context_limit": int}
}

def normalize_options(operation: str, options: dict) -> dict:
    """Ensure consistent option format"""
    schema = OPERATION_SCHEMAS.get(operation, {})
    return {k: v for k, v in options.items() if k in schema}

# Use normalized options
options = normalize_options("summarize", {"max_length": 100})
await cache.cache_response(text, "summarize", options, response)
```

## 🔧 Performance Optimization Tips

### 1. Memory Tier Optimization

**Configure L1 Cache Size Based on Usage Patterns**:

```python
# Profile your cache usage first
cache_stats = await cache.get_cache_stats()
hit_ratio = cache_stats.get("hit_ratio", 0)
memory_usage = cache_stats.get("memory_usage", {})

# Optimize based on hit ratio
if hit_ratio < 0.7:  # Low hit ratio
    # Increase L1 cache size
    cache = await factory.for_web_app(l1_cache_size=500)
elif memory_usage.get("utilization", 0) > 0.9:  # High memory usage
    # Reduce L1 cache size
    cache = await factory.for_web_app(l1_cache_size=100)
```

**Hot Data Preloading**:

```python
async def preload_hot_data():
    """Preload frequently accessed data into L1 cache"""
    hot_keys = [
        "config:feature_flags",
        "config:rate_limits", 
        "user:profile:active_admin"
    ]
    
    for key in hot_keys:
        # Trigger cache population
        data = await cache.get(key)
        if not data:
            data = await load_from_database(key)
            await cache.set(key, data, ttl=3600)

# Call during app startup
await preload_hot_data()
```

### 2. Compression Optimization

**Tune Compression Based on Data Size**:

```python
# Analyze your data sizes first
data_sizes = []
for key in sample_keys:
    data = await cache.get(key)
    if data:
        data_sizes.append(len(json.dumps(data)))

avg_size = sum(data_sizes) / len(data_sizes)

# Optimize compression threshold
if avg_size < 1000:  # Small data
    cache = await factory.for_web_app(
        compression_threshold=2000,  # Less aggressive
        compression_level=3          # Faster compression
    )
elif avg_size > 10000:  # Large data
    cache = await factory.for_web_app(
        compression_threshold=500,   # More aggressive  
        compression_level=8          # Better compression
    )
```

### 3. TTL Strategy Optimization

**Dynamic TTL Based on Data Freshness**:

```python
def calculate_dynamic_ttl(data_type: str, last_modified: datetime) -> int:
    """Calculate TTL based on data age and type"""
    age_hours = (datetime.now() - last_modified).total_seconds() / 3600
    
    base_ttls = {
        "user_profile": 3600,   # 1 hour base
        "api_response": 1800,   # 30 minutes base
        "static_content": 86400 # 24 hours base
    }
    
    base_ttl = base_ttls.get(data_type, 3600)
    
    # Reduce TTL for stale data
    if age_hours > 24:
        return min(300, base_ttl)  # 5 minutes max
    elif age_hours > 6:
        return base_ttl // 2
    else:
        return base_ttl

# Usage
ttl = calculate_dynamic_ttl("user_profile", user.last_updated)
await cache.set(user_key, user_data, ttl=ttl)
```

### 4. Batch Operations

**Efficient Bulk Cache Operations**:

```python
async def cache_multiple_users(users: List[User]):
    """Efficiently cache multiple users"""
    # Batch processing to reduce Redis round trips
    tasks = []
    for user in users:
        task = cache.set(
            f"user:profile:{user.id}",
            user.dict(),
            ttl=3600
        )
        tasks.append(task)
    
    # Execute all cache operations concurrently
    await asyncio.gather(*tasks)

async def get_multiple_cached(keys: List[str]) -> Dict[str, Any]:
    """Efficiently retrieve multiple cached values"""
    tasks = [cache.get(key) for key in keys]
    results = await asyncio.gather(*tasks)
    
    return {
        key: result 
        for key, result in zip(keys, results)
        if result is not None
    }
```

## 🐛 Monitoring & Debugging Guide

### 1. Performance Monitoring

**Built-in Cache Metrics**:

```python
# Get comprehensive cache statistics
stats = await cache.get_cache_stats()

print(f"Cache Hit Ratio: {stats.get('hit_ratio', 0):.2%}")
print(f"Total Operations: {stats.get('total_operations', 0):,}")
print(f"Memory Usage: {stats.get('memory_usage', {}).get('total_mb', 0):.1f}MB")

# Monitor specific metrics
if stats.get('hit_ratio', 0) < 0.7:
    logger.warning("Low cache hit ratio detected")
    
if stats.get('memory_usage', {}).get('utilization', 0) > 0.9:
    logger.warning("High memory usage detected")
```

**Real-time Monitoring Dashboard**:

```python
async def cache_health_check() -> Dict[str, Any]:
    """Comprehensive cache health check"""
    try:
        # Test basic operations
        test_key = f"health_check_{int(time.time())}"
        await cache.set(test_key, "test_value", ttl=60)
        retrieved = await cache.get(test_key)
        await cache.delete(test_key)
        
        # Get performance stats
        stats = await cache.get_cache_stats()
        
        return {
            "status": "healthy" if retrieved == "test_value" else "degraded",
            "basic_operations": "ok" if retrieved == "test_value" else "failed",
            "hit_ratio": stats.get("hit_ratio", 0),
            "memory_usage_mb": stats.get("memory_usage", {}).get("total_mb", 0),
            "total_operations": stats.get("total_operations", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Use in health check endpoint
@app.get("/health/cache")
async def cache_health():
    return await cache_health_check()
```

### 2. Debugging Cache Misses

**Cache Miss Investigation**:

```python
import logging
from functools import wraps

def debug_cache_operations(func):
    """Decorator to debug cache operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        operation = func.__name__
        cache_key = args[0] if args else "unknown"
        
        logger.debug(f"Cache {operation}: {cache_key}")
        
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        
        if operation == "get":
            status = "HIT" if result is not None else "MISS"
            logger.debug(f"Cache {operation} {status}: {cache_key} ({duration:.3f}s)")
        else:
            logger.debug(f"Cache {operation}: {cache_key} ({duration:.3f}s)")
        
        return result
    return wrapper

# Apply to cache methods
cache.get = debug_cache_operations(cache.get)
cache.set = debug_cache_operations(cache.set)
```

**Key Generation Debugging**:

```python
def debug_ai_cache_key(text: str, operation: str, options: dict) -> str:
    """Debug AI cache key generation"""
    from app.infrastructure.cache import CacheKeyGenerator
    
    key_gen = CacheKeyGenerator()
    key = key_gen.generate_cache_key(text, operation, options)
    
    print(f"Text length: {len(text)}")
    print(f"Operation: {operation}")
    print(f"Options: {options}")
    print(f"Generated key: {key}")
    print(f"Key length: {len(key)}")
    
    # Show text processing decision
    if len(text) > key_gen.text_hash_threshold:
        print(f"Text hashed (>{key_gen.text_hash_threshold} chars)")
    else:
        print(f"Text preserved (<={key_gen.text_hash_threshold} chars)")
    
    return key

# Usage in debugging
key = debug_ai_cache_key(
    text="Long document content...",
    operation="summarize",
    options={"max_length": 100}
)
```

### 3. Error Handling & Recovery

**Comprehensive Error Handling**:

```python
from app.core.exceptions import InfrastructureError, ValidationError

async def robust_cache_get(key: str, default=None):
    """Cache get with comprehensive error handling"""
    try:
        result = await cache.get(key)
        return result if result is not None else default
    except InfrastructureError as e:
        logger.error(f"Cache infrastructure error for key {key}: {e}")
        return default
    except ValidationError as e:
        logger.error(f"Cache validation error for key {key}: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected cache error for key {key}: {e}")
        return default

async def robust_cache_set(key: str, value: Any, ttl: int = None):
    """Cache set with comprehensive error handling"""
    try:
        await cache.set(key, value, ttl=ttl)
        return True
    except InfrastructureError as e:
        logger.error(f"Cache infrastructure error setting {key}: {e}")
        return False
    except ValidationError as e:
        logger.error(f"Cache validation error setting {key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected cache error setting {key}: {e}")
        return False
```

**Circuit Breaker for Cache Operations**:

```python
from app.infrastructure.resilience import CircuitBreaker

class CacheWithCircuitBreaker:
    def __init__(self, cache):
        self.cache = cache
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30
        )
    
    async def get(self, key: str):
        if self.circuit_breaker.is_open():
            logger.warning("Cache circuit breaker open, skipping cache")
            return None
        
        try:
            result = await self.cache.get(key)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Cache operation failed: {e}")
            return None

# Usage
protected_cache = CacheWithCircuitBreaker(cache)
```

## 🔧 Development Workflow Best Practices

### 1. Local Development Setup

**Development Environment Configuration**:

```python
# config/development.py
CACHE_CONFIG = {
    "type": "memory",  # Fast, isolated testing
    "default_ttl": 300,  # 5 minutes for rapid iteration
    "max_size": 100,     # Small memory footprint
    "debug_logging": True
}

# Initialize dev cache
if settings.debug:
    cache = InMemoryCache(
        default_ttl=CACHE_CONFIG["default_ttl"],
        max_size=CACHE_CONFIG["max_size"]
    )
    # Enable debug logging
    logging.getLogger("cache").setLevel(logging.DEBUG)
```

**Development Cache Utilities**:

```python
class DevCacheUtils:
    """Development utilities for cache debugging"""
    
    @staticmethod
    async def clear_all_cache():
        """Clear all cache entries (dev only)"""
        if not settings.debug:
            raise RuntimeError("clear_all_cache only available in debug mode")
        
        if hasattr(cache, 'invalidate_all'):
            await cache.invalidate_all()
        else:
            # InMemoryCache doesn't have invalidate_all
            cache._storage.clear()
    
    @staticmethod
    async def inspect_cache_keys(pattern: str = "*"):
        """Inspect current cache keys (dev only)"""
        if not settings.debug:
            raise RuntimeError("inspect_cache_keys only available in debug mode")
        
        if hasattr(cache, 'get_active_keys'):
            keys = await cache.get_active_keys()
            matching = [k for k in keys if fnmatch.fnmatch(k, pattern)]
            return matching
        return []
    
    @staticmethod
    async def cache_warmup(warmup_data: Dict[str, Any]):
        """Warm up cache with test data (dev only)"""
        if not settings.debug:
            raise RuntimeError("cache_warmup only available in debug mode")
        
        for key, value in warmup_data.items():
            await cache.set(key, value, ttl=3600)

# Usage in development
dev_cache = DevCacheUtils()
await dev_cache.clear_all_cache()
await dev_cache.cache_warmup({
    "user:profile:123": {"name": "Test User", "role": "admin"},
    "config:features": {"new_ui": True, "beta": False}
})
```

### 2. Testing Patterns

**Unit Test Cache Setup**:

```python
# conftest.py
import pytest
from app.infrastructure.cache import CacheFactory

@pytest.fixture
async def test_cache():
    """Isolated cache for testing"""
    factory = CacheFactory()
    cache = await factory.for_testing(use_memory_cache=True)
    yield cache
    # Cleanup automatically handled by InMemoryCache

@pytest.fixture
async def redis_test_cache():
    """Redis cache with test database"""
    factory = CacheFactory()
    cache = await factory.for_testing(
        redis_url="redis://localhost:6379/15",  # Test database
        fail_on_connection_error=False
    )
    yield cache
    # Clear test database
    if hasattr(cache, 'invalidate_all'):
        await cache.invalidate_all()
```

**Test Helpers**:

```python
class CacheTestHelpers:
    """Helper functions for cache testing"""
    
    @staticmethod
    async def assert_cache_hit(cache, key: str, expected_value):
        """Assert that cache contains expected value"""
        actual = await cache.get(key)
        assert actual == expected_value, f"Expected {expected_value}, got {actual}"
    
    @staticmethod
    async def assert_cache_miss(cache, key: str):
        """Assert that cache does not contain key"""
        actual = await cache.get(key)
        assert actual is None, f"Expected cache miss, got {actual}"
    
    @staticmethod
    async def populate_test_cache(cache, data: Dict[str, Any]):
        """Populate cache with test data"""
        for key, value in data.items():
            await cache.set(key, value, ttl=3600)

# Usage in tests
async def test_user_caching(test_cache):
    helpers = CacheTestHelpers()
    
    # Setup
    user_data = {"id": 123, "name": "Test User"}
    await helpers.populate_test_cache(test_cache, {
        "user:profile:123": user_data
    })
    
    # Test
    await helpers.assert_cache_hit(test_cache, "user:profile:123", user_data)
    await helpers.assert_cache_miss(test_cache, "user:profile:999")
```

### 3. IDE Configuration & Tooling

**VS Code Settings (`.vscode/settings.json`)**:

```json
{
    "python.analysis.extraPaths": [
        "backend/app/infrastructure/cache"
    ],
    "python.linting.pylintArgs": [
        "--load-plugins=pylint.extensions.docparams"
    ],
    "files.associations": {
        "*.py": "python"
    },
    "python.testing.pytestArgs": [
        "backend/tests/infrastructure/cache"
    ]
}
```

**Code Snippets (`.vscode/snippets/cache.code-snippets`)**:

```json
{
    "Cache Factory Web App": {
        "scope": "python",
        "prefix": "cache-web",
        "body": [
            "from app.infrastructure.cache import CacheFactory",
            "factory = CacheFactory()",
            "cache = await factory.for_web_app(",
            "    redis_url=\"${1:redis://redis:6379}\",",
            "    default_ttl=${2:1800}",
            ")"
        ]
    },
    "Cache Factory AI App": {
        "scope": "python", 
        "prefix": "cache-ai",
        "body": [
            "from app.infrastructure.cache import CacheFactory",
            "factory = CacheFactory()",
            "cache = await factory.for_ai_app(",
            "    redis_url=\"${1:redis://redis:6379}\",",
            "    default_ttl=${2:3600}",
            ")"
        ]
    },
    "Robust Cache Operations": {
        "scope": "python",
        "prefix": "cache-robust",
        "body": [
            "try:",
            "    result = await cache.get(\"${1:cache_key}\")",
            "    if result is None:",
            "        result = await ${2:load_from_source}()",
            "        await cache.set(\"${1:cache_key}\", result, ttl=${3:3600})",
            "    return result",
            "except Exception as e:",
            "    logger.error(f\"Cache error: {e}\")",
            "    return await ${2:load_from_source}()"
        ]
    }
}
```

### 4. Production Deployment Checklist

**Pre-deployment Validation**:

```python
async def validate_cache_config():
    """Validate cache configuration before deployment"""
    checks = []
    
    # Test Redis connectivity
    try:
        cache = await factory.for_web_app(
            redis_url=settings.redis_url,
            fail_on_connection_error=True
        )
        checks.append(("Redis connectivity", "✅ PASS"))
    except Exception as e:
        checks.append(("Redis connectivity", f"❌ FAIL: {e}"))
    
    # Test basic operations
    try:
        test_key = f"deploy_test_{int(time.time())}"
        await cache.set(test_key, "test", ttl=60)
        result = await cache.get(test_key)
        await cache.delete(test_key)
        
        if result == "test":
            checks.append(("Basic operations", "✅ PASS"))
        else:
            checks.append(("Basic operations", "❌ FAIL: Value mismatch"))
    except Exception as e:
        checks.append(("Basic operations", f"❌ FAIL: {e}"))
    
    # Test performance
    try:
        start = time.time()
        for i in range(10):
            await cache.set(f"perf_test_{i}", f"value_{i}", ttl=60)
        
        for i in range(10):
            await cache.get(f"perf_test_{i}")
        
        duration = time.time() - start
        if duration < 1.0:  # 10 ops in under 1 second
            checks.append(("Performance", f"✅ PASS ({duration:.3f}s)"))
        else:
            checks.append(("Performance", f"⚠️  SLOW ({duration:.3f}s)"))
    except Exception as e:
        checks.append(("Performance", f"❌ FAIL: {e}"))
    
    return checks

# Run before deployment
validation_results = await validate_cache_config()
for check, result in validation_results:
    print(f"{check}: {result}")
```

**Production Monitoring Setup**:

```python
# Enable production monitoring
if not settings.debug:
    from app.infrastructure.cache.monitoring import CachePerformanceMonitor
    
    monitor = CachePerformanceMonitor()
    
    # Set up alerts
    monitor.configure_thresholds({
        "memory_warning": 50_000_000,    # 50MB
        "memory_critical": 100_000_000,  # 100MB
        "hit_ratio_warning": 0.6,        # 60% hit ratio
        "operation_slow": 0.1            # 100ms operations
    })
```

## 🔍 Troubleshooting Workflows

### Issue: Cache Not Working

**Symptoms**: All cache operations return None or fail

**Diagnosis Workflow**:

```python
async def diagnose_cache_issues():
    """Comprehensive cache diagnosis"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": []
    }
    
    # 1. Check cache instance type
    cache_type = type(cache).__name__
    report["checks"].append(f"Cache type: {cache_type}")
    
    # 2. Test basic connectivity
    try:
        if hasattr(cache, 'connect'):
            connected = await cache.connect()
            report["checks"].append(f"Connection: {'✅ Connected' if connected else '❌ Failed'}")
        else:
            report["checks"].append("Connection: ✅ Memory cache (no connection needed)")
    except Exception as e:
        report["checks"].append(f"Connection: ❌ Error: {e}")
    
    # 3. Test basic operations
    test_key = f"diag_{int(time.time())}"
    try:
        await cache.set(test_key, "test_value", ttl=60)
        retrieved = await cache.get(test_key)
        await cache.delete(test_key)
        
        if retrieved == "test_value":
            report["checks"].append("Basic operations: ✅ Working")
        else:
            report["checks"].append(f"Basic operations: ❌ Retrieved '{retrieved}' instead of 'test_value'")
    except Exception as e:
        report["checks"].append(f"Basic operations: ❌ Error: {e}")
    
    # 4. Check configuration
    if hasattr(cache, 'redis_url'):
        report["checks"].append(f"Redis URL: {cache.redis_url}")
    if hasattr(cache, 'default_ttl'):
        report["checks"].append(f"Default TTL: {cache.default_ttl}")
    
    return report

# Run diagnosis
diagnosis = await diagnose_cache_issues()
for check in diagnosis["checks"]:
    print(check)
```

### Issue: Low Hit Rates

**Symptoms**: Hit ratio below 50%

**Investigation Steps**:

```python
async def investigate_low_hit_rates():
    """Investigate low cache hit rates"""
    # Get detailed statistics
    stats = await cache.get_cache_stats()
    
    print(f"Current hit ratio: {stats.get('hit_ratio', 0):.2%}")
    print(f"Total operations: {stats.get('total_operations', 0):,}")
    
    # Check TTL settings
    if hasattr(cache, 'default_ttl'):
        print(f"Default TTL: {cache.default_ttl}s ({cache.default_ttl/60:.1f} minutes)")
    
    # Sample key generation consistency
    if hasattr(cache, 'get_active_keys'):
        keys = await cache.get_active_keys()
        print(f"Active keys sample: {keys[:10]}")
        
        # Look for key pattern issues
        key_patterns = {}
        for key in keys[:100]:  # Sample first 100 keys
            pattern = key.split(':')[0] if ':' in key else 'no_pattern'
            key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
        
        print("Key patterns:")
        for pattern, count in sorted(key_patterns.items()):
            print(f"  {pattern}: {count}")
    
    # Recommendations
    hit_ratio = stats.get('hit_ratio', 0)
    if hit_ratio < 0.3:
        print("\n🔧 Recommendations:")
        print("- Check for key generation inconsistencies")
        print("- Verify TTL is appropriate for your data")
        print("- Consider increasing cache size")
    elif hit_ratio < 0.6:
        print("\n🔧 Recommendations:")
        print("- Optimize TTL settings")
        print("- Review cache key strategies")
        print("- Monitor access patterns")

await investigate_low_hit_rates()
```

### Issue: High Memory Usage

**Symptoms**: Memory alerts or out-of-memory errors

**Resolution Steps**:

```python
async def optimize_memory_usage():
    """Analyze and optimize memory usage"""
    stats = await cache.get_cache_stats()
    memory_info = stats.get('memory_usage', {})
    
    print(f"Current memory usage: {memory_info.get('total_mb', 0):.1f}MB")
    print(f"Cache utilization: {memory_info.get('utilization', 0):.1%}")
    
    # Get recommendations
    if memory_info.get('total_mb', 0) > 50:  # Over 50MB
        print("\n🔧 Memory Optimization:")
        
        # 1. Enable compression
        if hasattr(cache, 'compression_threshold'):
            current_threshold = cache.compression_threshold
            print(f"Current compression threshold: {current_threshold} bytes")
            print("Consider lowering to 500-1000 bytes")
        
        # 2. Reduce cache size
        if hasattr(cache, 'l1_cache_size'):
            current_size = cache.l1_cache_size
            print(f"Current L1 cache size: {current_size}")
            print("Consider reducing to 100-200 entries")
        
        # 3. Optimize TTL
        if hasattr(cache, 'default_ttl'):
            current_ttl = cache.default_ttl
            print(f"Current TTL: {current_ttl}s")
            print("Consider reducing TTL for dynamic data")

await optimize_memory_usage()
```

## 📊 Advanced Configuration Examples

### Production-Ready Configuration

```python
# Production cache configuration
async def create_production_cache():
    """Create production-optimized cache"""
    factory = CacheFactory()
    
    if settings.ai_enabled:
        # AI application with enhanced features
        cache = await factory.for_ai_app(
            redis_url=settings.redis_url,
            default_ttl=3600,           # 1 hour default
            compression_threshold=1000,  # Compress >1KB
            compression_level=7,         # Good compression ratio
            text_hash_threshold=500,     # Hash medium texts
            l1_cache_size=200,          # Larger memory cache
            operation_ttls={
                "summarize": 7200,       # 2 hours - stable
                "sentiment": 14400,      # 4 hours - very stable  
                "qa": 1800,             # 30 minutes - context-dependent
                "translate": 86400       # 24 hours - language stable
            },
            fail_on_connection_error=True
        )
    else:
        # Web application cache
        cache = await factory.for_web_app(
            redis_url=settings.redis_url,
            default_ttl=1800,           # 30 minutes
            compression_threshold=2000,  # Compress >2KB
            compression_level=6,         # Balanced
            l1_cache_size=300,          # Large memory cache
            fail_on_connection_error=True
        )
    
    return cache
```

### Multi-Environment Configuration

```python
# Environment-specific cache configurations
CACHE_CONFIGS = {
    "development": {
        "redis_url": "redis://localhost:6379/1",
        "default_ttl": 300,  # 5 minutes
        "l1_cache_size": 50,
        "compression_threshold": 5000,  # Less compression
        "fail_on_connection_error": False
    },
    "staging": {
        "redis_url": "redis://staging-redis:6379",
        "default_ttl": 1800,  # 30 minutes
        "l1_cache_size": 100,
        "compression_threshold": 2000,
        "fail_on_connection_error": True
    },
    "production": {
        "redis_url": "redis://production-redis:6379",
        "default_ttl": 3600,  # 1 hour
        "l1_cache_size": 500,
        "compression_threshold": 1000,
        "compression_level": 8,
        "fail_on_connection_error": True
    }
}

async def create_environment_cache():
    """Create cache based on current environment"""
    config = CACHE_CONFIGS.get(settings.environment, CACHE_CONFIGS["development"])
    
    factory = CacheFactory()
    return await factory.create_cache_from_config(
        config=config,
        fail_on_connection_error=config["fail_on_connection_error"]
    )
```

### High-Performance Configuration

```python
# High-performance cache for demanding applications
async def create_high_performance_cache():
    """Create cache optimized for high performance"""
    factory = CacheFactory()
    
    # Performance monitoring
    from app.infrastructure.cache.monitoring import CachePerformanceMonitor
    monitor = CachePerformanceMonitor()
    
    cache = await factory.for_web_app(
        redis_url=settings.redis_url,
        default_ttl=7200,             # 2 hours - reduce Redis queries
        l1_cache_size=1000,           # Large memory cache
        compression_threshold=500,     # Aggressive compression
        compression_level=3,           # Fast compression
        enable_l1_cache=True,
        performance_monitor=monitor
    )
    
    # Configure performance thresholds
    monitor.configure_thresholds({
        "memory_warning": 100_000_000,   # 100MB warning
        "memory_critical": 200_000_000,  # 200MB critical
        "hit_ratio_warning": 0.8,        # 80% hit ratio
        "operation_slow": 0.05           # 50ms operations
    })
    
    return cache
```

## Related Documentation

### Essential Reading
- **[Cache Infrastructure Guide](./CACHE.md)**: Complete technical documentation
- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Architectural patterns
- **[Performance Optimization](../operations/PERFORMANCE_OPTIMIZATION.md)**: Production optimization strategies

### Advanced Topics  
- **[Monitoring Infrastructure](./MONITORING.md)**: Comprehensive monitoring setup
- **[Resilience Infrastructure](./RESILIENCE.md)**: Fault tolerance patterns
- **[Security Guide](../operations/SECURITY.md)**: Production security considerations

### Next Steps
- **[API Documentation](../application/API.md)**: Cache management endpoints
- **[Deployment Guide](../developer/DEPLOYMENT.md)**: Production deployment
- **[Troubleshooting Guide](../operations/TROUBLESHOOTING.md)**: Operational procedures