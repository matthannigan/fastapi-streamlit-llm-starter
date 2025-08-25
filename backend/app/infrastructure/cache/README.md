---
sidebar_label: cache
---

# Cache Infrastructure Module

This directory provides a comprehensive caching infrastructure with multiple implementations, performance monitoring, and advanced features specifically designed for AI response caching.

## Directory Structure

```
cache/
├── __init__.py                    # Module exports and comprehensive documentation
├── base.py                       # Abstract interface defining cache contract
├── memory.py                     # In-memory cache implementation with TTL and LRU
├── redis_generic.py              # Generic Redis cache for web applications
├── redis_ai.py                   # AI-optimized Redis cache with text processing
├── monitoring.py                 # Comprehensive performance monitoring and analytics
├── factory.py                    # CacheFactory for explicit cache instantiation
├── config.py                     # Configuration management with builder pattern
├── dependencies.py               # FastAPI dependency injection with lifecycle management
├── benchmarks.py                 # Performance benchmarking suite with comparison tools
├── parameter_mapping.py          # Advanced parameter mapping for cache inheritance
├── compatibility_wrapper.py      # Backward compatibility and migration support
├── migration_helper.py           # Migration utilities for smooth transitions
├── security.py                   # Security features and prompt injection protection
├── redis.py.md                   # Additional Redis cache documentation
├── redis.py.txt                  # Redis cache implementation notes
└── README.md                     # This documentation file
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

## Phase 3 Features: Enhanced Developer Experience

### CacheFactory - Explicit Cache Instantiation

The `CacheFactory` provides deterministic, explicit cache creation methods that eliminate auto-detection ambiguity and improve developer experience.

**Key Benefits:**
- **Explicit Selection:** Clear intent with `for_web_app()`, `for_ai_app()`, `for_testing()`
- **Graceful Degradation:** Configurable fallback behavior with `fail_on_connection_error` parameter
- **Optimized Defaults:** Environment-specific configurations built-in
- **Configuration-Based Creation:** Support for `CacheConfig` objects

**Factory Methods with Preset Support:**
```python
from app.infrastructure.cache import CacheFactory
from app.infrastructure.cache.dependencies import get_cache_config

# Preset-based factory creation (RECOMMENDED)
config = get_cache_config()  # Uses CACHE_PRESET environment variable
cache = CacheFactory.create_cache_from_config(config)

# Web application cache (uses "production" preset)
os.environ["CACHE_PRESET"] = "production"
web_cache = CacheFactory.create_cache_from_config(get_cache_config())

# AI application cache (uses "ai-production" preset)
os.environ["CACHE_PRESET"] = "ai-production" 
ai_cache = CacheFactory.create_cache_from_config(get_cache_config())

# Development cache (uses "development" preset)
os.environ["CACHE_PRESET"] = "development"
dev_cache = CacheFactory.create_cache_from_config(get_cache_config())

# Testing cache (uses "minimal" preset)
os.environ["CACHE_PRESET"] = "minimal"
test_cache = CacheFactory.create_cache_from_config(get_cache_config())

# Legacy factory methods (still supported)
legacy_web_cache = CacheFactory.for_web_app(
    redis_url="redis://localhost:6379/0",
    fail_on_connection_error=False
)
legacy_ai_cache = CacheFactory.for_ai_app(
    redis_url="redis://localhost:6379/1", 
    fail_on_connection_error=False
)
```

### Configuration Management with Builder Pattern

The `CacheConfigBuilder` provides a fluent interface for complex cache configuration across environments.

**Builder Pattern Features:**
- **Fluent Interface:** Method chaining for readable configuration
- **Environment Presets:** Development, testing, production defaults
- **Validation:** Built-in configuration validation with detailed error messages
- **File Support:** Load from/save to JSON configuration files
- **Environment Loading:** Automatic environment variable detection

```python
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache.cache_presets import CachePresetManager

# Preset-based configuration (RECOMMENDED)
preset_manager = CachePresetManager()

# Get preset configuration directly
config = preset_manager.get_preset("production").to_cache_config()

# List available presets
available_presets = preset_manager.list_presets()
# Returns: ['disabled', 'minimal', 'simple', 'development', 'production', 'ai-development', 'ai-production']

# Get preset details
preset_details = preset_manager.get_preset_details("ai-production")

# Environment-based preset loading
config = get_cache_config()  # Loads from CACHE_PRESET environment variable

# Custom configuration with preset base + overrides
os.environ["CACHE_PRESET"] = "production"
os.environ["CACHE_REDIS_URL"] = "redis://prod-server:6379/0"
os.environ["CACHE_CUSTOM_CONFIG"] = '{"compression_level": 9, "memory_cache_size": 2000}'
config = get_cache_config()

# Legacy builder pattern (still supported)
# from app.infrastructure.cache import CacheConfigBuilder, EnvironmentPresets
# config = CacheConfigBuilder().for_environment("production").build()
```

### FastAPI Dependency Integration

Comprehensive dependency injection system with lifecycle management and health checking.

**Dependency Features:**
- **Automatic Lifecycle:** Connection management and cleanup
- **Configuration Integration:** Uses `CacheConfig` for consistent setup
- **Health Checking:** Built-in cache health status monitoring  
- **Registry Management:** Weak reference cache registry for multi-worker safety
- **Conditional Dependencies:** Environment-based cache selection

```python
from app.infrastructure.cache.dependencies import (
    get_cache_service,
    get_cache_config,
    get_cache_health_status,
    validate_cache_configuration
)

# FastAPI endpoint with preset-based dependency injection
@app.post("/api/process")
async def process_text(
    request: ProcessRequest,
    cache: CacheInterface = Depends(get_cache_service),  # Automatically uses CACHE_PRESET
    config: CacheConfig = Depends(get_cache_config)      # Loads preset configuration
):
    # Cache is automatically configured from CACHE_PRESET environment variable
    # Example: CACHE_PRESET=ai-production -> AIResponseCache with AI optimizations
    cached_result = await cache.get(f"process:{request.operation}:{hash(request.text)}")
    if cached_result:
        return cached_result
    
    # Process and cache result
    result = await process_service.execute(request)
    await cache.set(f"process:{request.operation}:{hash(request.text)}", result)
    return result

# Health check endpoint with preset info
@app.get("/internal/cache/health")
async def cache_health(
    cache: CacheInterface = Depends(get_cache_service),
    config: CacheConfig = Depends(get_cache_config)
):
    health_status = await get_cache_health_status(cache)
    health_status["preset_used"] = config.preset_name if hasattr(config, 'preset_name') else 'unknown'
    return health_status

# Configuration validation endpoint
@app.get("/internal/cache/config")
async def cache_config_info(
    config: CacheConfig = Depends(get_cache_config)
):
    return {
        "preset": os.getenv("CACHE_PRESET", "development"),
        "redis_url": config.redis_url,
        "default_ttl": config.default_ttl,
        "ai_features_enabled": config.enable_ai_cache
    }
```

### Performance Benchmarking Suite

The `CachePerformanceBenchmark` class provides comprehensive performance testing and comparison tools.

**Benchmarking Features:**
- **Operation Benchmarks:** SET, GET, DELETE performance with statistical analysis
- **Cache Comparison:** Side-by-side performance comparison between cache types
- **Factory Performance:** Benchmark cache creation overhead
- **Environment Testing:** Compare configurations across environments
- **Statistical Analysis:** Percentiles, confidence intervals, outlier detection

```python
from app.infrastructure.cache import CachePerformanceBenchmark

benchmark = CachePerformanceBenchmark()

# Benchmark basic operations
memory_results = await benchmark.benchmark_basic_operations(
    memory_cache, 
    test_operations=1000,
    data_size="medium"
)

redis_results = await benchmark.benchmark_basic_operations(
    redis_cache,
    test_operations=1000, 
    data_size="medium"
)

# Compare caches
comparison = await benchmark.compare_caches(
    baseline_cache=memory_cache,
    comparison_cache=redis_cache,
    test_operations=500
)

print(f"Performance difference: {comparison.overall_performance_change:.2f}%")
print(f"Recommendation: {comparison.recommendation}")

# Factory performance
factory_results = await benchmark.benchmark_factory_creation()
```

### Preset-Based Configuration System

The cache infrastructure uses a **preset-based configuration system** that dramatically simplifies setup by reducing 28+ individual environment variables to a single `CACHE_PRESET` variable.

**Quick Configuration (Choose One):**
```bash
# Primary Configuration Variable
CACHE_PRESET=development     # Choose: disabled, minimal, simple, development, production, ai-development, ai-production

# Optional Overrides (only when needed)
CACHE_REDIS_URL=redis://localhost:6379/0  # Override Redis connection
ENABLE_AI_CACHE=true                      # Toggle AI features
CACHE_CUSTOM_CONFIG='{"compression_level": 9}'  # Advanced JSON overrides
```

**Available Presets:**

| Preset | Use Case | Key Features |
|--------|----------|-------------|
| **`disabled`** | Testing, minimal overhead | Cache disabled, memory-only fallback, 5min TTL |
| **`minimal`** | Resource-constrained environments | Lightweight setup, 15min TTL, minimal features |
| **`simple`** | Quick setup, small applications | Basic caching, 1hr TTL, no AI features |
| **`development`** | Local development | Debug-friendly, 30min TTL, monitoring enabled |
| **`production`** | Web applications | High performance, 2hr TTL, optimized settings |
| **`ai-development`** | AI app development | AI features, 30min TTL, text processing optimized |
| **`ai-production`** | Production AI workloads | AI optimized, 4hr TTL, maximum performance |

**Benefits of Preset System:**
- ✅ **Simplicity**: 1 variable instead of 28+ individual variables
- ✅ **Consistency**: Follows the same pattern as resilience system (`RESILIENCE_PRESET`)
- ✅ **Reliability**: Battle-tested configurations for common scenarios
- ✅ **Maintainability**: Easy to add new features without environment variable proliferation
- ✅ **Quick Setup**: 5-minute setup vs 30-minute manual configuration

**Override Patterns:**
```bash
# Base configuration with overrides
CACHE_PRESET=production
CACHE_REDIS_URL=redis://production-server:6379  # Custom Redis URL
ENABLE_AI_CACHE=false                           # Disable AI features

# Advanced JSON overrides
CACHE_PRESET=development
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 500,
  "memory_cache_size": 200,
  "operation_ttls": {
    "summarize": 1800,
    "sentiment": 3600
  }
}'
```

### Advanced Features

#### Security Integration
- **Prompt Injection Protection:** Input sanitization for AI operations
- **TLS Support:** Encrypted Redis connections in production
- **Input Validation:** Comprehensive parameter validation
- **Audit Logging:** Security event tracking

#### Performance Optimization
- **Memory Management:** Intelligent memory cache sizing
- **Compression Strategy:** Adaptive compression based on content type
- **Connection Pooling:** Efficient Redis connection management
- **Batch Operations:** Optimized bulk cache operations

#### Monitoring & Analytics
- **Real-time Metrics:** Performance monitoring with configurable thresholds
- **Health Checking:** Comprehensive cache health status
- **Performance Recommendations:** Automated optimization suggestions
- **Usage Analytics:** Detailed operation statistics and trends

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

### Preset-Based Configuration
```python
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory

# Using preset-based configuration
config = get_cache_config()  # Loads from CACHE_PRESET environment variable
cache = CacheFactory.create_cache_from_config(config)

# Examples with different presets:
# CACHE_PRESET=development -> InMemoryCache with debug settings
# CACHE_PRESET=production -> AIResponseCache with optimized performance
# CACHE_PRESET=ai-production -> AIResponseCache with AI optimizations

# Manual override example
os.environ["CACHE_PRESET"] = "production"
os.environ["CACHE_REDIS_URL"] = "redis://production:6379"
cache = CacheFactory.create_cache_from_config(get_cache_config())
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
