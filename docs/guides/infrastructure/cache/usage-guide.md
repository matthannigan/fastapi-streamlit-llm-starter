---
sidebar_position: 1
sidebar_label: Usage
title: Cache Infrastructure Comprehensive Usage Guide
description: Complete practical usage guide for the cache infrastructure - from 5-minute quickstart to advanced optimization patterns with preset-based configuration
---

# Cache Infrastructure Comprehensive Usage Guide

This comprehensive guide provides developers with everything needed to be immediately productive with the cache infrastructure. From instant setup patterns to advanced optimization strategies, this guide delivers actionable solutions for all cache usage scenarios.

> **🚀 Latest Enhancement**: The cache system now uses `CACHE_PRESET` for simplified configuration, reducing 28+ environment variables to 1-4 variables. This follows the successful pattern from the resilience system.

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

**📖 For complete implementation examples, see:**
- Cache module docstrings in `app.infrastructure.cache.dependencies`
- Cache factory patterns in `app.infrastructure.cache.factory`
- Real-world usage patterns in production endpoints

### Simple Preset Configuration

```bash
# NEW: Preset-based configuration (replaces 28+ CACHE_* variables)
CACHE_PRESET=development                    # Choose preset for your use case
CACHE_REDIS_URL=redis://localhost:6379     # Essential Redis connection override
ENABLE_AI_CACHE=true                        # AI features toggle

# Available presets:
# disabled, minimal, simple, development, production, ai-development, ai-production
```

## 🎯 Factory Method Selection Guide

### Choose Your Cache Type

```
┌─ What are you building?
│
├─ 🌐 **Web Application**
│   ├─ Sessions, API responses, page cache
│   ├─ → Use: `factory.for_web_app()`
│   └─ Features: Redis + memory tier, 30min TTL, balanced compression
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

### Cache Characteristics

| Cache Type | Speed | Persistence | Memory Usage | Best For |
|------------|-------|-------------|--------------|----------|
| **InMemoryCache** | ⚡ Fastest | ❌ No | 🟡 Medium | Testing, dev |
| **GenericRedisCache** | 🚀 Fast | ✅ Yes | 🟢 Low | Web apps |
| **AIResponseCache** | 🚀 Fast | ✅ Yes | 🟡 Medium | AI apps |

### Factory Method Details

#### for_web_app() - Web Application Cache

**Purpose**: Optimized for web applications with balanced performance and moderate resource usage.

```python
# Basic web application cache
web_cache = await factory.for_web_app(
    redis_url="redis://localhost:6379",
    default_ttl=1800,              # 30 minutes - good for session data
    enable_memory_cache=True,      # Enable fast memory tier
    memory_cache_size=200,         # 200 items in memory
    compression_threshold=2000,     # Compress larger responses
    compression_level=6,           # Balanced compression
    fail_on_connection_error=False # Graceful degradation
)

# Production web cache with enhanced settings
production_web_cache = await factory.for_web_app(
    redis_url="redis://redis-cluster:6379",
    default_ttl=3600,              # 1 hour for production stability
    memory_cache_size=500,         # Larger memory cache
    compression_threshold=1000,     # More aggressive compression
    compression_level=7,           # Higher compression level
    fail_on_connection_error=True  # Strict error handling
)
```

**When to Use `for_web_app()`:**
- Building traditional web applications
- Caching API responses, session data, or user profiles
- Need balanced performance between speed and memory usage
- Working with structured data and standard web patterns
- Require moderate TTLs (30 minutes to 2 hours)

#### for_ai_app() - AI Application Cache

**Purpose**: Specialized for AI workloads with text processing, operation-specific TTLs, and intelligent compression.

```python
# Basic AI application cache
ai_cache = await factory.for_ai_app(
    redis_url="redis://ai-redis:6379",
    default_ttl=3600,              # 1 hour base TTL
    memory_cache_size=100,         # Smaller memory cache for AI responses
    compression_threshold=1000,     # Aggressive compression
    text_hash_threshold=500,       # Hash text over 500 characters
    operation_ttls={               # Operation-specific TTLs
        "summarize": 7200,         # 2 hours - summaries are stable
        "sentiment": 86400,        # 24 hours - sentiment rarely changes
        "key_points": 5400,        # 1.5 hours - moderately stable
        "questions": 3600,         # 1 hour - context-dependent
        "qa": 1800                 # 30 minutes - highly context-dependent
    },
    fail_on_connection_error=False
)
```

**When to Use `for_ai_app()`:**
- Processing AI/ML workloads with LLM responses
- Handling large text content that benefits from intelligent hashing
- Need operation-specific TTL strategies (summarize vs. sentiment analysis)
- Require enhanced compression for large responses
- Working with text-heavy content that varies significantly in size

#### for_testing() - Testing Environment Cache

**Purpose**: Optimized for testing scenarios with short TTLs, test isolation, and predictable behavior.

```python
# Memory-only test cache (completely isolated)
memory_test_cache = await factory.for_testing(
    use_memory_cache=True,         # Force memory-only mode
    default_ttl=60,                # 1 minute expiration
    memory_cache_size=50           # Small cache for testing
)

# Redis test cache with isolated database
redis_test_cache = await factory.for_testing(
    redis_url="redis://localhost:6379/15",  # Database 15 for tests
    default_ttl=60,                # 1 minute TTL
    enable_memory_cache=False,     # Disable memory cache for predictable behavior
    compression_level=1,           # Fast compression for speed
    fail_on_connection_error=False # Allow fallback during tests
)
```

**When to Use `for_testing()`:**
- Running automated tests that need cache isolation
- Developing locally with rapid iteration cycles
- Need predictable cache behavior with short TTLs
- Require memory-only mode for test consistency
- Testing cache failure scenarios

## 🔧 Configuration with Presets

### Preset Selection Guide

| Application Type | Development | Production | 
|------------------|-------------|------------|
| **Simple Web App** | `simple` or `development` | `production` |
| **AI Applications** | `ai-development` | `ai-production` |
| **Microservices** | `minimal` or `simple` | `production` |
| **Resource-Constrained** | `minimal` | `minimal` |
| **Testing/Debug** | `disabled` or `minimal` | N/A |

### Preset-Based Configuration Examples

**Modern Preset Approach (Recommended):**
```bash
# For AI applications in development
CACHE_PRESET=ai-development
CACHE_REDIS_URL=redis://localhost:6379

# For AI applications in production  
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://production:6379

# For simple web applications
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379

# Advanced JSON overrides for complex scenarios
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 1000,
  "memory_cache_size": 100,
  "default_ttl": 3600,
  "use_tls": true
}'
```

### Configuration Builder Pattern

For programmatic configuration, use the `CacheConfigBuilder`:

```python
from app.infrastructure.cache.config import CacheConfigBuilder

# Development environment configuration
dev_config = (CacheConfigBuilder()
    .for_environment("development")
    .with_redis("redis://localhost:6379")
    .with_compression(threshold=2000, level=4)
    .with_memory_cache(size=50)
    .build())

# Production environment with AI features
prod_ai_config = (CacheConfigBuilder()
    .for_environment("production")
    .with_redis("redis://prod-redis:6379", use_tls=True)
    .with_compression(threshold=1000, level=6)
    .with_memory_cache(size=200)
    .with_ai_features(
        text_hash_threshold=1000,
        operation_ttls={
            "summarize": 14400,
            "sentiment": 86400,
            "translate": 43200
        }
    )
    .build())
```

## 🌐 Practical Implementation Patterns

### Web Application Patterns

**Session Management Pattern**:
```python
from app.infrastructure.cache.dependencies import get_web_cache_service
from fastapi import Depends

async def manage_user_session(
    session_id: str,
    cache: CacheInterface = Depends(get_web_cache_service)
):
    """Manage user sessions with web cache."""
    
    session_key = f"session:active:{session_id}"
    
    # Check if session exists
    session_data = await cache.get(session_key)
    if not session_data:
        return {"error": "Session expired or invalid"}
    
    # Extend session expiration
    await cache.set(session_key, session_data, ttl=3600)  # 1 hour extension
    
    return {
        "session_id": session_id,
        "user_id": session_data.get("user_id"),
        "expires_in": 3600
    }
```

**API Response Caching Pattern**:
```python
async def get_user_profile(
    user_id: int,
    cache: CacheInterface = Depends(get_web_cache_service)
):
    """Get user profile with web-optimized caching."""
    
    # Check cache first
    cache_key = f"user:profile:{user_id}"
    cached_profile = await cache.get(cache_key)
    
    if cached_profile:
        return {
            **cached_profile,
            "from_cache": True,
            "cache_type": "web_optimized"
        }
    
    # Load from database
    profile = await load_user_profile_from_db(user_id)
    
    # Cache for 30 minutes (web-optimized TTL)
    await cache.set(cache_key, profile, ttl=1800)
    
    return {
        **profile,
        "from_cache": False
    }
```

### AI Application Patterns

**AI Response Caching Pattern**:
```python
from app.infrastructure.cache.dependencies import get_ai_cache_service

async def process_ai_request(
    request: AIProcessRequest,
    ai_cache: CacheInterface = Depends(get_ai_cache_service)
):
    """Process AI request with AI-optimized caching."""
    
    # AI cache automatically handles intelligent key generation
    cached_result = await ai_cache.get_cached_response(
        text=request.text,
        operation=request.operation,
        options=request.options
    )
    
    if cached_result:
        return {
            **cached_result,
            "from_cache": True,
            "cache_type": "ai_optimized",
            "operation_ttl": get_operation_ttl(request.operation)
        }
    
    # Process with AI service
    ai_result = await ai_service.process(
        text=request.text,
        operation=request.operation,
        **request.options
    )
    
    # Cache the result (uses operation-specific TTL automatically)
    await ai_cache.cache_response(
        text=request.text,
        operation=request.operation,
        options=request.options,
        response=ai_result
    )
    
    return {
        **ai_result,
        "from_cache": False,
        "processing_time": ai_result.get("processing_time"),
        "text_length": len(request.text)
    }
```

**Batch AI Processing Pattern**:
```python
async def batch_process_documents(
    documents: List[Document],
    operation: str,
    ai_cache: CacheInterface = Depends(get_ai_cache_service)
):
    """Process multiple documents with AI cache optimization."""
    
    results = []
    cache_hits = 0
    cache_misses = 0
    
    for doc in documents:
        # Check cache for each document
        cached_result = await ai_cache.get_cached_response(
            text=doc.content,
            operation=operation,
            options={"batch_mode": True}
        )
        
        if cached_result:
            results.append({
                **cached_result,
                "document_id": doc.id,
                "from_cache": True
            })
            cache_hits += 1
        else:
            # Process document
            result = await ai_service.process_document(doc, operation)
            
            # Cache result
            await ai_cache.cache_response(
                text=doc.content,
                operation=operation,
                options={"batch_mode": True},
                response=result
            )
            
            results.append({
                **result,
                "document_id": doc.id,
                "from_cache": False
            })
            cache_misses += 1
    
    return {
        "results": results,
        "cache_statistics": {
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_ratio": cache_hits / len(documents) if documents else 0
        }
    }
```

### Integration Patterns

**FastAPI Dependency Injection**:
```python
from app.infrastructure.cache.dependencies import (
    get_web_cache_service, 
    get_ai_cache_service
)

# Web cache dependency
async def cached_api_endpoint(
    cache: CacheInterface = Depends(get_web_cache_service)
):
    return await cache.get("api_data")

# AI cache dependency
async def ai_processing_endpoint(
    ai_cache: CacheInterface = Depends(get_ai_cache_service)
):
    return await ai_cache.get_cached_response("text", "operation", {})
```

**Domain Service Integration**:
```python
class UserDomainService:
    def __init__(self, cache: CacheInterface):
        self.cache = cache
    
    async def get_user_with_cache(self, user_id: int):
        """Domain service with integrated caching."""
        cache_key = f"domain:user:{user_id}"
        cached_user = await self.cache.get(cache_key)
        
        if cached_user:
            return User.from_dict(cached_user)
        
        # Load from repository
        user = await self.user_repository.get_by_id(user_id)
        
        # Cache domain object
        await self.cache.set(cache_key, user.to_dict(), ttl=3600)
        
        return user
```

## 📊 Environment-Specific Setup

### Development Environment

```python
# Development cache with debugging features
dev_cache = await factory.for_web_app(
    redis_url="redis://localhost:6379",
    default_ttl=900,               # 15 minutes for rapid testing
    memory_cache_size=50,          # Small memory footprint
    compression_threshold=5000,     # Less aggressive compression
    compression_level=3,           # Fast compression
    fail_on_connection_error=False # Continue without Redis
)

# Environment variables for development
# CACHE_PRESET=development
# CACHE_REDIS_URL=redis://localhost:6379
```

### Testing Environment

```python
# Unit test cache (memory-only for isolation)
unit_test_cache = await factory.for_testing(
    use_memory_cache=True,
    default_ttl=60,
    memory_cache_size=25
)

# Integration test cache with Redis test database
integration_cache = await factory.for_testing(
    redis_url="redis://localhost:6379/15",
    default_ttl=120,
    enable_memory_cache=False,     # Disable for predictable behavior
    compression_level=1,           # Fast compression
    fail_on_connection_error=True  # Fail fast in tests
)

# Environment variables for testing
# CACHE_PRESET=minimal
# CACHE_REDIS_URL=redis://localhost:6379/15
```

### Production Environment

```python
# Production web cache with high availability
prod_web_cache = await factory.for_web_app(
    redis_url="redis://redis-cluster:6379",
    default_ttl=3600,              # 1 hour for stability
    memory_cache_size=500,         # Large memory cache
    compression_threshold=1000,     # Aggressive compression
    compression_level=7,           # High compression level
    fail_on_connection_error=True  # Strict error handling
)

# Production AI cache with enhanced features
prod_ai_cache = await factory.for_ai_app(
    redis_url="redis://ai-redis-cluster:6379",
    default_ttl=7200,              # 2 hours base TTL
    compression_threshold=500,      # Very aggressive compression
    compression_level=8,           # High compression level
    text_hash_threshold=1000,
    memory_cache_size=200,
    operation_ttls={
        "summarize": 28800,        # 8 hours for stable summaries
        "sentiment": 172800,       # 48 hours for sentiment
        "translate": 86400,        # 24 hours for translations
        "extract": 14400,          # 4 hours for extraction
        "classify": 43200          # 12 hours for classification
    },
    fail_on_connection_error=True
)

# Environment variables for production
# CACHE_PRESET=production
# CACHE_REDIS_URL=redis://redis-cluster:6379
# For AI workloads:
# CACHE_PRESET=ai-production
# CACHE_REDIS_URL=redis://ai-redis-cluster:6379
```

## ⚠️ Best Practices & Anti-patterns

### Best Practices

#### 1. Consistent Key Generation
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

#### 2. TTL Strategy Based on Data Characteristics
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

#### 3. Proper Error Handling
```python
# ✅ GOOD: Comprehensive error handling
async def robust_cache_get(key: str, default=None):
    """Cache get with comprehensive error handling"""
    try:
        result = await cache.get(key)
        return result if result is not None else default
    except InfrastructureError as e:
        logger.error(f"Cache infrastructure error for key {key}: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected cache error for key {key}: {e}")
        return default
```

#### 4. Efficient Batch Operations
```python
# ✅ GOOD: Concurrent batch operations
async def cache_multiple_users(users: List[User]):
    """Efficiently cache multiple users"""
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
```

### Anti-patterns to Avoid

#### ❌ Cache Key Inconsistency
```python
# ❌ BAD: Inconsistent key formats
await cache.set(f"user_{user_id}", data)
await cache.set(f"user:{user_id}", data)  # Different format!
```

#### ❌ No TTL Strategy
```python
# ❌ BAD: No TTL strategy
await cache.set("user_prefs", data)  # Uses default, may be wrong
await cache.set("api_response", data, ttl=86400)  # 24h too long for dynamic data
```

#### ❌ Memory Leaks in Development
```python
# ❌ BAD: No size limits in dev
cache = InMemoryCache()  # Unlimited growth
for i in range(100000):
    await cache.set(f"test_{i}", large_data)  # Memory explosion!
```

#### ❌ Unhandled Redis Connection Errors
```python
# ❌ BAD: No error handling
cache = GenericRedisCache(redis_url="redis://redis:6379")
await cache.connect()  # May throw unhandled exception
```

#### ❌ AI Cache Parameter Mismatches
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

## 🔧 Performance Optimization

### Memory Tier Optimization

**Configure Memory Cache Size Based on Usage Patterns**:

```python
# Profile your cache usage first
cache_stats = await cache.get_cache_stats()
hit_ratio = cache_stats.get("hit_ratio", 0)
memory_usage = cache_stats.get("memory_usage", {})

# Optimize based on hit ratio
if hit_ratio < 0.7:  # Low hit ratio
    # Increase memory cache size
    cache = await factory.for_web_app(memory_cache_size=500)
elif memory_usage.get("utilization", 0) > 0.9:  # High memory usage
    # Reduce memory cache size
    cache = await factory.for_web_app(memory_cache_size=100)
```

**Hot Data Preloading**:

```python
async def preload_hot_data():
    """Preload frequently accessed data into memory cache"""
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

### Compression Optimization

```python
# Analyze your data sizes first
data_sizes = []
for key in sample_keys:
    data = await cache.get(key)
    if data:
        data_sizes.append(len(json.dumps(data)))

avg_size = sum(data_sizes) / len(data_sizes)

# Optimize compression settings based on data patterns
if avg_size < 1000:  # Small data
    cache = await factory.for_web_app(
        compression_threshold=2000,  # Higher threshold for small data
        compression_level=3          # Faster compression
    )
elif avg_size > 10000:  # Large data
    cache = await factory.for_web_app(
        compression_threshold=500,   # Lower threshold for large data
        compression_level=8          # Higher compression level
    )
```

### Dynamic TTL Strategy

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

## 🐛 Debugging & Monitoring

### Performance Monitoring

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

**Health Check Implementation**:

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

### Cache Miss Investigation

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

## 🔍 Real-World Examples

### E-commerce Application

```python
class EcommerceCartService:
    def __init__(self, web_cache: CacheInterface):
        self.cache = web_cache
    
    async def get_cart_items(self, user_id: int):
        """Get shopping cart with aggressive caching"""
        cache_key = f"cart:items:{user_id}"
        cart_items = await self.cache.get(cache_key)
        
        if cart_items:
            return cart_items
        
        # Load from database
        cart_items = await self.db.get_cart_items(user_id)
        
        # Cache for 15 minutes (cart changes frequently)
        await self.cache.set(cache_key, cart_items, ttl=900)
        
        return cart_items
    
    async def add_item_to_cart(self, user_id: int, item_data: dict):
        """Add item and invalidate cache"""
        # Add to database
        await self.db.add_cart_item(user_id, item_data)
        
        # Invalidate cache to force refresh
        cache_key = f"cart:items:{user_id}"
        await self.cache.delete(cache_key)
        
        # Preload new cart data
        return await self.get_cart_items(user_id)
```

### Content Management System

```python
class CMSContentService:
    def __init__(self, ai_cache: CacheInterface):
        self.ai_cache = ai_cache
    
    async def generate_content_summary(self, article: Article):
        """Generate article summaries with AI cache"""
        
        # Try AI cache first
        cached_summary = await self.ai_cache.get_cached_response(
            text=article.content,
            operation="summarize",
            options={
                "max_length": 150,
                "style": "news"
            }
        )
        
        if cached_summary:
            return {
                **cached_summary,
                "article_id": article.id,
                "from_cache": True
            }
        
        # Generate new summary
        summary = await self.ai_service.summarize(
            text=article.content,
            max_length=150,
            style="news"
        )
        
        # Cache for 4 hours (summaries are stable)
        await self.ai_cache.cache_response(
            text=article.content,
            operation="summarize",
            options={"max_length": 150, "style": "news"},
            response=summary
        )
        
        return {
            **summary,
            "article_id": article.id,
            "from_cache": False
        }
```

### Multi-tenant Application

```python
class MultiTenantDataService:
    def __init__(self, web_cache: CacheInterface):
        self.cache = web_cache
    
    async def get_tenant_config(self, tenant_id: str):
        """Get tenant configuration with namespace isolation"""
        cache_key = f"tenant:{tenant_id}:config"
        
        tenant_config = await self.cache.get(cache_key)
        
        if tenant_config:
            return tenant_config
        
        # Load from database
        config = await self.db.get_tenant_config(tenant_id)
        
        # Cache for 2 hours (configs change rarely)
        await self.cache.set(cache_key, config, ttl=7200)
        
        return config
    
    async def get_tenant_users(self, tenant_id: str, page: int = 1):
        """Get tenant users with pagination cache"""
        cache_key = f"tenant:{tenant_id}:users:page:{page}"
        
        users = await self.cache.get(cache_key)
        
        if users:
            return users
        
        # Load paginated users
        users = await self.db.get_tenant_users(tenant_id, page)
        
        # Cache for 30 minutes (user lists change moderately)
        await self.cache.set(cache_key, users, ttl=1800)
        
        return users
```

## 🔄 Testing Patterns

### Unit Testing with Cache

```python
import pytest
from app.infrastructure.cache import CacheFactory

@pytest.fixture
async def test_cache():
    """Isolated cache for testing"""
    factory = CacheFactory()
    cache = await factory.for_testing(use_memory_cache=True)
    yield cache
    # Cleanup automatically handled by InMemoryCache

async def test_user_service_caching(test_cache):
    """Test user service with cache integration"""
    service = UserService(cache=test_cache)
    
    # First call should hit database
    user1 = await service.get_user_with_cache(123)
    assert user1.from_cache is False
    
    # Second call should hit cache
    user2 = await service.get_user_with_cache(123)
    assert user2.from_cache is True
    assert user1.data == user2.data
```

### Integration Testing

```python
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

@pytest.mark.integration
async def test_cache_persistence(redis_test_cache):
    """Test data persistence across cache instances"""
    
    # Store data
    await redis_test_cache.set("persist_test", {"data": "persistent"})
    
    # Create new cache instance
    factory = CacheFactory()
    new_cache = await factory.for_testing(
        redis_url="redis://localhost:6379/15"
    )
    
    # Data should persist
    result = await new_cache.get("persist_test")
    assert result == {"data": "persistent"}
```

### Performance Testing

```python
@pytest.mark.performance
async def test_cache_performance(test_cache):
    """Test cache performance characteristics"""
    
    import time
    
    # Test set performance
    start_time = time.time()
    for i in range(100):
        await test_cache.set(f"perf_key_{i}", f"value_{i}")
    set_time = time.time() - start_time
    
    # Test get performance
    start_time = time.time()
    for i in range(100):
        await test_cache.get(f"perf_key_{i}")
    get_time = time.time() - start_time
    
    # Assert performance characteristics
    assert set_time < 1.0  # 100 sets should take less than 1 second
    assert get_time < 0.5  # 100 gets should take less than 0.5 seconds
```

## 📋 Production Deployment Checklist

### Pre-deployment Validation

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
            await cache.get(f"perf_test_{i}")
        
        duration = time.time() - start
        if duration < 1.0:  # 20 ops in under 1 second
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

### Production Configuration

```bash
# Production environment variables
CACHE_PRESET=production
CACHE_REDIS_URL=redis://redis-cluster:6379
ENABLE_AI_CACHE=true

# For AI-heavy workloads
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://ai-redis-cluster:6379

# Advanced configuration override (if needed)
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 1000,
  "compression_level": 8,
  "l1_cache_size": 500,
  "default_ttl": 3600,
  "fail_on_connection_error": true
}'
```

### Monitoring Setup

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

## Related Documentation

### Essential Reading
- **[Cache Infrastructure Architecture](./CACHE.md)**: Complete technical documentation and architecture overview
- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Architectural patterns and separation of concerns
- **[Code Standards](../developer/CODE_STANDARDS.md)**: Development patterns and best practices

### Configuration & Setup
- **[Cache API Reference](./api-reference.md)**: Detailed API documentation for all cache methods
- **[Cache Configuration](./configuration.md)**: Complete preset system and configuration options
- **[Cache Testing](./testing.md)**: Testing patterns and test utilities

### Operations & Monitoring
- **[Monitoring Infrastructure](./MONITORING.md)**: Comprehensive monitoring setup and metrics
- **[Resilience Infrastructure](./RESILIENCE.md)**: Fault tolerance and circuit breaker patterns
- **[Performance Optimization](../operations/PERFORMANCE_OPTIMIZATION.md)**: Advanced performance tuning strategies

### Integration Guides
- **[AI Infrastructure](./AI.md)**: AI service integration patterns
- **[Authentication Guide](../developer/AUTHENTICATION.md)**: Security and authentication patterns
- **[Deployment Guide](../developer/DEPLOYMENT.md)**: Production deployment procedures

### Next Steps
- **[API Documentation](../application/API.md)**: Cache management endpoints and web API
- **[Troubleshooting Guide](../operations/TROUBLESHOOTING.md)**: Common issues and resolution procedures
- **[Template Customization](../../get-started/TEMPLATE_CUSTOMIZATION.md)**: Adapting cache infrastructure for your specific needs