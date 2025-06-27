# Cache Infrastructure Module

This directory provides a comprehensive caching infrastructure with multiple implementations, performance monitoring, and advanced features specifically designed for AI response caching.

## Directory Structure

```
cache/
├── __init__.py          # Module exports and documentation
├── base.py             # Abstract interface defining cache contract
├── memory.py           # In-memory cache implementation
├── redis.py            # Redis-based cache with advanced features
├── monitoring.py       # Performance monitoring and analytics
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
    async def set(self, key: str, value: any, ttl: int = None):
        """Store a value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """Remove a value from cache"""
        pass
```

**Role in Construction:**
- Provides a common interface for dependency injection
- Ensures consistent behavior across implementations
- Enables seamless switching between cache types
- Enforces the async/await pattern for all operations

## Cache Implementations Comparison

### `memory.py` - InMemoryCache

**Purpose:** Lightweight, fast in-memory caching for development, testing, and scenarios where Redis is unavailable.

**Key Features:**
- ✅ **Storage:** Pure Python dictionaries in RAM
- ✅ **TTL Support:** Automatic expiration with configurable time-to-live
- ✅ **LRU Eviction:** Intelligent memory management with configurable size limits
- ✅ **Performance:** Sub-millisecond access times
- ✅ **Statistics:** Built-in metrics and cache performance monitoring
- ✅ **Thread Safety:** Safe for asyncio concurrent usage

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
- ✅ **Persistent Storage:** Redis-backed with data persistence across restarts
- ✅ **Tiered Caching:** Memory cache for hot data + Redis for persistence
- ✅ **Intelligent Compression:** Automatic compression of large responses using zlib
- ✅ **Smart Key Generation:** Optimized cache keys that hash large texts efficiently
- ✅ **Graceful Degradation:** Falls back to memory-only when Redis unavailable  
- ✅ **Advanced Monitoring:** Comprehensive performance analytics via `CachePerformanceMonitor`
- ✅ **Pattern Invalidation:** Flexible cache invalidation with pattern matching
- ✅ **Operation-Specific TTLs:** Different expiration times per operation type

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

The `monitoring.py` module provides comprehensive analytics through the `CachePerformanceMonitor` class:

### Metrics Tracked
- **Key Generation Performance:** Timing and text length correlations
- **Cache Operations:** Get/Set timing, hit/miss ratios  
- **Memory Usage:** Total consumption, growth trends, threshold alerts
- **Compression Efficiency:** Ratios, timing, size savings
- **Cache Invalidation:** Frequency, patterns, efficiency metrics

### Alert Thresholds
- **Memory Warnings:** Configurable byte thresholds (default: 50MB warning, 100MB critical)
- **Slow Operations:** Automatic detection of performance degradation
- **Invalidation Frequency:** Alerts for excessive cache churn

### Analytics Features
- **Trend Analysis:** Historical performance patterns
- **Recommendations:** Automated optimization suggestions  
- **Export Capabilities:** Metrics export for external analysis
- **Automatic Cleanup:** Configurable data retention (default: 1 hour)

## Integration Patterns

### Dependency Injection
```python
from app.infrastructure.cache import CacheInterface, InMemoryCache, AIResponseCache

def create_cache() -> CacheInterface:
    if settings.USE_REDIS:
        return AIResponseCache(redis_url=settings.REDIS_URL)
    else:
        return InMemoryCache(default_ttl=settings.CACHE_TTL)

# Inject into services
class TextProcessingService:
    def __init__(self, cache: CacheInterface):
        self.cache = cache
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
