# Cache Infrastructure Module

This directory provides a comprehensive caching infrastructure with multiple implementations, performance monitoring, and advanced features specifically designed for AI response caching.

## Directory Structure

```
cache/
├── __init__.py          # Module exports and comprehensive documentation
├── base.py             # Abstract interface defining cache contract
├── memory.py           # In-memory cache implementation with TTL and LRU
├── redis.py            # Redis-based AIResponseCache with advanced features
├── monitoring.py       # Comprehensive performance monitoring and analytics
├── redis.py.md         # Additional Redis cache documentation
├── redis.py.txt        # Redis cache implementation notes
└── README.md           # This documentation file
```

## Core Architecture

### `base.py` - The Foundation Interface

The `CacheInterface` abstract base class defines the contract that all cache implementations must follow:

```python
class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str):
        """Retrieve a value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store a value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """Remove a value from cache"""
        pass
```

**Architecture Role:**
- **Interface Compliance**: Provides common contract for dependency injection
- **Implementation Flexibility**: Ensures consistent behavior across cache types  
- **Seamless Integration**: Enables switching between cache implementations
- **Async Pattern**: Enforces async/await pattern for all cache operations
- **Type Safety**: Supports proper type hints for development and testing

## Cache Implementations Comparison

### `memory.py` - InMemoryCache

**Purpose:** Lightweight, fast in-memory caching for development, testing, and scenarios where Redis is unavailable.

**Key Features:**
- ✅ **Storage**: Pure Python dictionaries in RAM with metadata tracking
- ✅ **TTL Support**: Automatic expiration with configurable time-to-live per entry
- ✅ **LRU Eviction**: Intelligent memory management with access order tracking
- ✅ **Performance**: Sub-millisecond access times with O(1) operations
- ✅ **Statistics**: Built-in metrics including utilization and performance tracking
- ✅ **Thread Safety**: Safe for asyncio concurrent usage within single event loop
- ✅ **Automatic Cleanup**: Periodic cleanup of expired entries during operations
- ✅ **Comprehensive API**: Additional methods like `exists()`, `get_ttl()`, `get_active_keys()`

**Configuration:**
```python
cache = InMemoryCache(
    default_ttl=3600,      # 1 hour default expiration
    max_size=1000          # Maximum 1000 entries before LRU eviction
)
```

**Best For:**
- Development and testing environments
- Applications with moderate caching needs (<10,000 entries)  
- Scenarios where external dependencies are not desired
- Microservices with minimal infrastructure requirements
- Temporary caching during application startup

**Limitations:**
- ❌ **No Persistence:** Data lost on application restart
- ❌ **Single Process:** Cannot share cache between application instances
- ❌ **Memory Constraints:** Limited by available RAM

### `redis.py` - AIResponseCache

**Purpose:** Production-ready, feature-rich caching system specifically optimized for AI response caching with persistence and advanced monitoring.

**Key Features:**
- ✅ **Persistent Storage**: Redis-backed with data persistence across application restarts
- ✅ **Tiered Caching**: Memory cache for hot data + Redis for persistence layer
- ✅ **Intelligent Compression**: Automatic zlib compression with configurable thresholds
- ✅ **Smart Key Generation**: Optimized cache keys using `CacheKeyGenerator` for large texts
- ✅ **Graceful Degradation**: Falls back to memory-only when Redis unavailable
- ✅ **Advanced Monitoring**: Comprehensive analytics via `CachePerformanceMonitor`
- ✅ **Pattern Invalidation**: Flexible cache invalidation with pattern matching support
- ✅ **Operation-Specific TTLs**: Different expiration times per AI operation type
- ✅ **Memory Management**: Configurable memory cache size with intelligent eviction
- ✅ **Performance Optimization**: Streaming compression and efficient key hashing

**Configuration:**
```python
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,                    # Base TTL
    text_hash_threshold=1000,            # Hash texts over 1000 chars
    compression_threshold=1000,          # Compress responses over 1KB
    compression_level=6,                 # zlib compression level
    memory_cache_size=100,              # In-memory cache entries
    text_size_tiers={                   # Text categorization
        'small': 500,
        'medium': 5000, 
        'large': 50000
    }
)
```

**Operation-Specific TTLs:**
```python
operation_ttls = {
    "summarize": 7200,    # 2 hours - summaries are stable
    "sentiment": 86400,   # 24 hours - sentiment rarely changes  
    "key_points": 7200,   # 2 hours
    "questions": 3600,    # 1 hour - questions can vary
    "qa": 1800           # 30 minutes - context-dependent
}
```

**Best For:**
- Production environments requiring persistence
- High-volume applications (>100,000 cache entries)
- Multi-process deployments requiring shared cache
- Applications needing advanced monitoring and analytics
- AI response caching with compression needs

**Advanced Features:**

#### Intelligent Key Generation
- **Small texts** (<1000 chars): Uses text directly for readability
- **Large texts** (>1000 chars): Uses SHA256 hash with metadata for uniqueness
- **Efficient processing:** Streaming hash approach for memory efficiency

#### Compression Strategy  
- **Automatic:** Compresses responses larger than threshold
- **Configurable:** Adjustable compression levels (1-9)
- **Monitored:** Tracks compression ratios and timing

#### Performance Monitoring
- **Hit/Miss Ratios:** Real-time cache effectiveness tracking
- **Operation Timing:** Detailed performance analysis  
- **Memory Usage:** Memory consumption monitoring with alerts
- **Compression Analytics:** Efficiency metrics and recommendations

## Usage Examples

### Basic InMemoryCache Usage

```python
from app.infrastructure.cache import InMemoryCache

# Initialize
cache = InMemoryCache(default_ttl=1800, max_size=500)

# Basic operations
await cache.set("user:123", {"name": "John", "role": "admin"})
user_data = await cache.get("user:123")
await cache.delete("user:123")

# Check existence and TTL
exists = await cache.exists("session:abc") 
ttl_remaining = await cache.get_ttl("session:abc")

# Statistics
stats = cache.get_stats()
print(f"Cache utilization: {stats['utilization_percent']:.1f}%")
```

### Advanced AIResponseCache Usage

```python
from app.infrastructure.cache import AIResponseCache

# Initialize with custom configuration
cache = AIResponseCache(
    redis_url="redis://production:6379",
    compression_threshold=2000,
    memory_cache_size=200
)

await cache.connect()

# Cache AI response
await cache.cache_response(
    text="Long document to analyze...",
    operation="summarize", 
    options={"max_length": 100, "model": "gpt-4"},
    response={"summary": "Brief summary", "confidence": 0.95}
)

# Retrieve cached response  
cached = await cache.get_cached_response(
    text="Long document to analyze...",
    operation="summarize",
    options={"max_length": 100, "model": "gpt-4"}
)

# Performance monitoring
stats = await cache.get_cache_stats()
hit_ratio = cache.get_cache_hit_ratio()
summary = cache.get_performance_summary()

# Cache management
await cache.invalidate_by_operation("summarize", 
                                   operation_context="model_update") 
await cache.invalidate_pattern("sentiment",
                               operation_context="batch_invalidation")
```

## Performance Monitoring System

The `monitoring.py` module provides comprehensive analytics through the `CachePerformanceMonitor` class with detailed metrics collection and analysis capabilities:

### Metrics Tracked
- **Key Generation Performance**: Timing analysis with text length correlations and slow operation detection
- **Cache Operations**: Get/Set operation timing, hit/miss ratios, and operation type breakdown
- **Memory Usage**: Total consumption monitoring, growth trends, and threshold-based alerting
- **Compression Efficiency**: Compression ratios, timing analysis, and size savings calculations
- **Cache Invalidation**: Frequency monitoring, pattern analysis, and efficiency metrics

### Advanced Analytics
- **Statistical Analysis**: Mean, median, min/max calculations for all performance metrics
- **Trend Analysis**: Historical performance patterns with growth rate calculations
- **Threshold Monitoring**: Configurable byte thresholds with warning and critical levels
- **Performance Recommendations**: Automated optimization suggestions based on collected data
- **Slow Operation Detection**: Automatic identification of operations exceeding thresholds

### Configurable Alerting
- **Memory Thresholds**: Default 50MB warning, 100MB critical (configurable)
- **Performance Thresholds**: 100ms key generation, 50ms cache operations (configurable)
- **Invalidation Rate Monitoring**: 50/hour warning, 100/hour critical (configurable)
- **Alert Levels**: INFO, WARNING, ERROR, CRITICAL with contextual messages

### Data Management
- **Automatic Cleanup**: Configurable data retention (default: 1 hour, max 1000 measurements)
- **Export Capabilities**: JSON export for external monitoring systems
- **Memory Efficiency**: Bounded data structures prevent unbounded growth
- **Thread Safety**: Safe for concurrent usage within asyncio event loops

## Integration Patterns

### Dependency Injection

The cache system integrates seamlessly with FastAPI's dependency injection:

```python
from app.infrastructure.cache import CacheInterface, InMemoryCache, AIResponseCache

async def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """Dependency provider for AI response cache service."""
    cache = AIResponseCache(
        redis_url=settings.redis_url,
        default_ttl=settings.cache_default_ttl,
        text_hash_threshold=settings.cache_text_hash_threshold,
        compression_threshold=settings.cache_compression_threshold,
        compression_level=settings.cache_compression_level,
        text_size_tiers=settings.cache_text_size_tiers,
        memory_cache_size=settings.cache_memory_cache_size
    )
    
    try:
        await cache.connect()
    except Exception as e:
        # Graceful degradation - cache operates without Redis
        logger.warning(f"Redis connection failed: {e}")
    
    return cache

# Use in FastAPI endpoints
@app.post("/process")
async def process_text(
    request: ProcessRequest,
    cache: AIResponseCache = Depends(get_cache_service)
):
    cached_result = await cache.get_cached_response(
        text=request.text,
        operation=request.operation,
        options=request.options
    )
    
    if cached_result:
        return cached_result
    
    # Process and cache result
    result = await ai_service.process(request)
    await cache.cache_response(
        text=request.text,
        operation=request.operation,
        options=request.options,
        response=result
    )
    return result
```

### Environment-Based Configuration
```python
# Development
cache = InMemoryCache(default_ttl=1800, max_size=100)

# Production  
cache = AIResponseCache(
    redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
    default_ttl=int(os.getenv("CACHE_TTL", "3600")),
    compression_threshold=int(os.getenv("CACHE_COMPRESSION_THRESHOLD", "1000"))
)
```

## Error Handling & Resilience

Both implementations include comprehensive error handling:

- **Redis Connection Failures:** AIResponseCache gracefully degrades to memory-only mode
- **Serialization Errors:** Logged but don't interrupt application flow  
- **Memory Pressure:** InMemoryCache uses LRU eviction to manage memory constraints
- **Corrupted Data:** Automatic cleanup of invalid cache entries

## Testing Considerations

- **InMemoryCache:** Ideal for unit tests (fast, isolated, no external dependencies)
- **AIResponseCache:** Can be configured with Redis test instance or mocked for unit tests
- **Interface Compliance:** Both implementations can be tested against the same interface contract

## Performance Characteristics

| Feature | InMemoryCache | AIResponseCache |
|---------|---------------|-----------------|
| **Get Operations** | O(1) avg, O(n) cleanup | O(1) memory, O(1) Redis + network |
| **Set Operations** | O(1) avg, O(n) eviction | O(1) + compression time |
| **Memory Usage** | ~100-200 bytes/entry | Varies with compression |  
| **Startup Time** | Instant | Redis connection time |
| **Persistence** | None | Full Redis persistence |
| **Multi-Process** | No | Yes (shared Redis) |

## Migration Guide

### From InMemoryCache to AIResponseCache
1. Install Redis and configure connection URL
2. Update initialization code to use AIResponseCache
3. Configure appropriate TTLs and compression thresholds  
4. Monitor performance metrics during transition
5. Implement graceful fallback for Redis unavailability

### Configuration Migration
```python
# Before (InMemoryCache)
cache = InMemoryCache(default_ttl=3600, max_size=1000)

# After (AIResponseCache)  
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    memory_cache_size=100,  # Smaller memory tier
    compression_threshold=1000
)
```

This cache infrastructure provides a solid foundation for scalable, high-performance caching with the flexibility to choose the right implementation for each environment and use case.
