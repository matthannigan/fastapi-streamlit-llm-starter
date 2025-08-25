---
sidebar_label: Cache Migration
---

# Cache Infrastructure Migration Guide

This comprehensive migration guide covers the transition from inheritance-based cache patterns to the new callback composition and factory-based cache architecture introduced in Phase 3 of the cache refactoring project. This guide ensures smooth migration with minimal downtime and provides step-by-step instructions for upgrading existing implementations.

## Migration Overview

### What's Changing

The cache infrastructure has undergone a significant architectural evolution to improve maintainability, testability, and performance:

**From: Inheritance-Based Patterns**
```python
# Legacy pattern - auto-detection based cache creation
from app.infrastructure.cache import get_cache_instance

# Environment-based auto-detection (deprecated)
cache = get_cache_instance()  # Automatically detects Redis/Memory
```

**To: Explicit Factory Methods**
```python
# New pattern - explicit cache factory methods
from app.infrastructure.cache import CacheFactory

# Explicit cache creation with clear intent
factory = CacheFactory()
cache = await factory.for_web_app(redis_url="redis://localhost:6379")
```

### Key Architectural Changes

| Aspect | Legacy Approach | New Approach | Benefits |
|--------|----------------|--------------|----------|
| **Cache Creation** | Auto-detection via environment | Explicit factory methods | Deterministic behavior, clear intent |
| **Configuration** | Scattered environment variables | Centralized `CacheConfig` with builder | Type safety, validation, easier testing |
| **Dependency Injection** | Direct instantiation in endpoints | FastAPI dependencies with lifecycle | Proper connection management, reusability |
| **Testing** | Manual cache setup in tests | `for_testing()` factory method | Isolated test environment, predictable behavior |
| **Error Handling** | Generic exceptions | Structured exception hierarchy | Better debugging, contextual error information |

### Migration Benefits

✅ **Improved Reliability**: Explicit cache creation eliminates configuration guessing  
✅ **Better Testing**: Dedicated test patterns with `for_testing()` method  
✅ **Enhanced Performance**: Optimized factory methods for specific use cases  
✅ **Simplified Configuration**: Centralized configuration management with validation  
✅ **Backward Compatibility**: Legacy patterns continue to work during transition  

## Pre-Migration Assessment

### Compatibility Check

Before starting migration, assess your current implementation:

**1. Identify Current Cache Usage Patterns**
```bash
# Find direct cache instantiations
grep -r "AIResponseCache\|GenericRedisCache\|InMemoryCache" src/
grep -r "get_cache_instance\|get_ai_cache" src/

# Find environment-based cache configuration
grep -r "CACHE_TYPE\|REDIS_URL\|CACHE_" config/ .env*
```

**2. Inventory FastAPI Dependencies**
```python
# Look for these patterns in your endpoints
@app.get("/endpoint")
async def handler(cache = Depends(some_cache_dependency)):
    pass
```

**3. Review Test Fixtures**
```python
# Find test cache setups
@pytest.fixture
def cache():
    return SomeCache(...)
```

### Migration Complexity Assessment

| Current Pattern | Migration Complexity | Estimated Effort |
|----------------|---------------------|------------------|
| **Direct instantiation** | Low | 1-2 hours |
| **Environment-based auto-detection** | Medium | 2-4 hours |
| **Custom cache wrappers** | High | 4-8 hours |
| **Complex test setups** | Medium | 2-3 hours |

## Step-by-Step Migration Guide

### Phase 1: Update Cache Instantiation (Breaking Changes)

**Step 1.1: Replace Direct Cache Instantiation**

**Before (Legacy)**:
```python
from app.infrastructure.cache import AIResponseCache, InMemoryCache

# Direct instantiation - deprecated
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    text_hash_threshold=1000
)

# Environment-based auto-detection - deprecated
cache = get_cache_instance()
```

**After (New Pattern)**:
```python
from app.infrastructure.cache import CacheFactory

# Explicit factory usage for AI applications
factory = CacheFactory()
cache = await factory.for_ai_app(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    text_hash_threshold=1000
)

# Or for web applications
cache = await factory.for_web_app(
    redis_url="redis://localhost:6379",
    default_ttl=1800,  # 30 minutes
    compression_threshold=2000
)
```

**Step 1.2: Update Configuration Management**

**Before (Legacy)**:
```python
# Scattered configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
```

**After (New Pattern)**:
```python
from app.infrastructure.cache import CacheConfigBuilder

# Centralized configuration with validation
config = (CacheConfigBuilder()
    .for_environment("production")
    .with_redis("redis://production:6379")
    .with_ai_features()
    .with_compression(threshold=1000, level=6)
    .build())

factory = CacheFactory()
cache = await factory.create_cache_from_config(config.to_dict())
```

### Phase 2: Update FastAPI Dependencies

**Step 2.1: Replace Custom Cache Dependencies**

**Before (Legacy)**:
```python
from fastapi import Depends

async def get_cache():
    """Legacy cache dependency."""
    return AIResponseCache(redis_url="redis://localhost:6379")

@app.get("/api/data")
async def get_data(cache = Depends(get_cache)):
    # Cache logic here
    pass
```

**After (New Pattern)**:
```python
from fastapi import Depends
from app.infrastructure.cache.dependencies import get_cache_service, get_ai_cache_service

# Use built-in dependencies with lifecycle management
@app.get("/api/data")
async def get_data(cache = Depends(get_cache_service)):
    # Automatically managed cache with connection lifecycle
    pass

@app.post("/ai/summarize")
async def summarize(ai_cache = Depends(get_ai_cache_service)):
    # AI-optimized cache with proper configuration
    pass
```

**Step 2.2: Configure Application Settings Integration**

**Before (Legacy)**:
```python
# Manual settings integration
class Settings:
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600
```

**After (New Pattern)**:
```python
# Settings automatically integrated via dependencies
class Settings:
    redis_url: str = "redis://localhost:6379"
    debug: bool = False  # Used for environment detection

# Dependencies automatically build configuration from settings
@app.get("/endpoint")
async def handler(cache = Depends(get_cache_service)):
    # Cache configuration built from settings + environment detection
    pass
```

### Phase 3: Update Test Patterns

**Step 3.1: Replace Test Cache Fixtures**

**Before (Legacy)**:
```python
@pytest.fixture
def test_cache():
    """Legacy test cache fixture."""
    return InMemoryCache(default_ttl=60, max_size=10)

@pytest.fixture
async def redis_test_cache():
    """Legacy Redis test fixture."""
    cache = AIResponseCache(redis_url="redis://localhost:6379/15")
    await cache.connect()
    yield cache
    await cache.disconnect()
```

**After (New Pattern)**:
```python
from app.infrastructure.cache.dependencies import get_test_cache, get_test_redis_cache

@pytest.fixture
async def test_cache():
    """Simplified test cache fixture."""
    return await get_test_cache()  # Always InMemoryCache for isolation

@pytest.fixture
async def redis_test_cache():
    """Redis integration test fixture."""
    return await get_test_redis_cache()  # Handles connection lifecycle

# Or use factory directly
@pytest.fixture
async def custom_test_cache():
    factory = CacheFactory()
    return await factory.for_testing(
        default_ttl=30,
        use_memory_cache=True
    )
```

**Step 3.2: Update Test Configuration**

**Before (Legacy)**:
```python
# Manual test environment setup
@pytest.fixture(scope="session")
async def test_setup():
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["CACHE_TYPE"] = "memory"
```

**After (New Pattern)**:
```python
# Environment detection handles test configuration
@pytest.fixture(scope="session")
async def test_setup():
    # Factory methods automatically use test-optimized defaults
    # No manual environment manipulation needed
    pass
```

### Phase 4: Error Handling Migration

**Step 4.1: Update Exception Handling**

**Before (Legacy)**:
```python
try:
    cache = AIResponseCache(redis_url="invalid://url")
    await cache.connect()
except Exception as e:
    # Generic error handling
    logger.error(f"Cache failed: {e}")
    cache = InMemoryCache()
```

**After (New Pattern)**:
```python
from app.core.exceptions import ConfigurationError, InfrastructureError, ValidationError

try:
    factory = CacheFactory()
    cache = await factory.for_ai_app(
        redis_url="redis://production:6379",
        fail_on_connection_error=True
    )
except ValidationError as e:
    # Configuration validation failed
    logger.error(f"Configuration error: {e.message}")
    logger.debug(f"Context: {e.context}")
except InfrastructureError as e:
    # Redis connection failed
    logger.error(f"Infrastructure error: {e.message}")
    # Automatic fallback already handled by factory
except ConfigurationError as e:
    # Configuration building failed
    logger.error(f"Config error: {e.message}")
```

## Migration Checklist

### Pre-Migration Verification

- [ ] **Code Inventory**: Identify all cache usage patterns in codebase
- [ ] **Dependency Mapping**: Map current dependencies to new patterns
- [ ] **Test Coverage**: Ensure existing tests cover cache functionality
- [ ] **Environment Review**: Document current configuration approach
- [ ] **Performance Baseline**: Establish current performance metrics

### Phase 1 Migration Steps

- [ ] **Update Imports**: Replace legacy imports with factory imports
- [ ] **Replace Instantiation**: Convert direct cache creation to factory methods
- [ ] **Configuration Migration**: Implement `CacheConfigBuilder` patterns
- [ ] **Validation**: Add proper input validation and error handling
- [ ] **Testing**: Update unit tests for new patterns

### Phase 2 Dependency Updates

- [ ] **FastAPI Dependencies**: Replace custom dependencies with built-in ones
- [ ] **Settings Integration**: Configure settings for automatic environment detection
- [ ] **Lifecycle Management**: Ensure proper connection management
- [ ] **Health Checks**: Implement cache health monitoring
- [ ] **Monitoring**: Add performance monitoring integration

### Phase 3 Test Migration

- [ ] **Test Fixtures**: Replace manual fixtures with factory methods
- [ ] **Test Isolation**: Ensure tests use `for_testing()` method
- [ ] **Integration Tests**: Update Redis integration tests
- [ ] **Performance Tests**: Validate no regression in performance
- [ ] **Error Testing**: Test new exception handling patterns

### Post-Migration Validation

- [ ] **Functionality Testing**: Verify all cache operations work correctly
- [ ] **Performance Testing**: Confirm no performance degradation
- [ ] **Error Handling**: Test error scenarios and fallback behavior
- [ ] **Monitoring**: Validate metrics and health checks
- [ ] **Documentation**: Update internal documentation

## Code Transformation Examples

### Example 1: Simple Web Application Cache

**Before**:
```python
# legacy_cache_setup.py
import os
from app.infrastructure.cache import InMemoryCache, AIResponseCache

def get_cache():
    if os.getenv("USE_REDIS", "false").lower() == "true":
        return AIResponseCache(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            default_ttl=int(os.getenv("CACHE_TTL", "1800"))
        )
    else:
        return InMemoryCache(
            default_ttl=int(os.getenv("CACHE_TTL", "1800")),
            max_size=int(os.getenv("CACHE_SIZE", "100"))
        )

# Usage in endpoint
@app.get("/api/sessions")
async def get_sessions():
    cache = get_cache()
    # ... cache logic
```

**After**:
```python
# new_cache_setup.py
from app.infrastructure.cache import CacheFactory
from app.infrastructure.cache.dependencies import get_web_cache_service
from fastapi import Depends

# Simplified endpoint with dependency injection
@app.get("/api/sessions")
async def get_sessions(cache = Depends(get_web_cache_service)):
    # Cache automatically configured for web usage patterns
    # Handles Redis fallback to memory automatically
    # ... cache logic
```

### Example 2: AI Application Cache

**Before**:
```python
# legacy_ai_cache.py
class TextProcessor:
    def __init__(self):
        self.cache = AIResponseCache(
            redis_url=os.getenv("REDIS_URL"),
            default_ttl=3600,
            text_hash_threshold=1000,
            compression_threshold=1000
        )
    
    async def process_text(self, text: str, operation: str):
        # Manual cache key generation and management
        cache_key = f"ai_cache:op:{operation}|txt:{hash(text)}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Process and cache
        result = await self._ai_process(text, operation)
        await self.cache.set(cache_key, result, ttl=3600)
        return result
```

**After**:
```python
# new_ai_cache.py
from app.infrastructure.cache.dependencies import get_ai_cache_service
from fastapi import Depends

class TextProcessor:
    def __init__(self, ai_cache = Depends(get_ai_cache_service)):
        self.cache = ai_cache
    
    async def process_text(self, text: str, operation: str):
        # Built-in AI cache methods handle key generation and TTL management
        cached = await self.cache.get_cached_response(
            text=text,
            operation=operation,
            options={}
        )
        if cached:
            return cached
        
        # Process and cache
        result = await self._ai_process(text, operation)
        await self.cache.cache_response(
            text=text,
            operation=operation,
            options={},
            response=result
        )
        return result
```

### Example 3: Test Migration

**Before**:
```python
# legacy_test_cache.py
@pytest.fixture
async def test_cache():
    cache = InMemoryCache(default_ttl=60, max_size=10)
    return cache

@pytest.fixture
async def redis_cache():
    cache = AIResponseCache(redis_url="redis://localhost:6379/15")
    connected = await cache.connect()
    if not connected:
        pytest.skip("Redis not available")
    yield cache
    await cache.disconnect()

async def test_cache_operations(test_cache):
    await test_cache.set("key", "value")
    result = await test_cache.get("key")
    assert result == "value"
```

**After**:
```python
# new_test_cache.py
from app.infrastructure.cache import CacheFactory

@pytest.fixture
async def test_cache():
    factory = CacheFactory()
    return await factory.for_testing(use_memory_cache=True)

@pytest.fixture
async def redis_cache():
    factory = CacheFactory()
    return await factory.for_testing(
        redis_url="redis://localhost:6379/15",
        fail_on_connection_error=False  # Automatic fallback
    )

async def test_cache_operations(test_cache):
    await test_cache.set("key", "value")
    result = await test_cache.get("key")
    assert result == "value"
```

## Backward Compatibility & Transition Strategies

### Gradual Migration Strategy

**Option 1: Service-by-Service Migration**
1. Start with test environments
2. Migrate non-critical services first
3. Monitor performance and stability
4. Gradually migrate production services

**Option 2: Feature Flag Migration**
```python
# Transition with feature flags
USE_NEW_CACHE = os.getenv("USE_NEW_CACHE_FACTORY", "false").lower() == "true"

if USE_NEW_CACHE:
    # New factory-based approach
    factory = CacheFactory()
    cache = await factory.for_web_app()
else:
    # Legacy approach
    cache = get_legacy_cache()
```

**Option 3: Parallel Deployment**
- Deploy new factory alongside legacy patterns
- Route traffic gradually to new implementation
- Monitor metrics and performance
- Complete cutover once validated

### Legacy Pattern Support

The new architecture maintains compatibility for legacy patterns during transition:

```python
# Legacy patterns continue to work
from app.infrastructure.cache.compatibility import LegacyCacheWrapper

# Wraps new factory methods with legacy interface
legacy_cache = LegacyCacheWrapper.create_ai_cache()
```

## Performance Validation During Migration

### Baseline Metrics

Before migration, establish baseline performance metrics:

```python
# pre_migration_benchmark.py
import time
import asyncio
from app.infrastructure.cache import LegacyCache

async def benchmark_cache_operations(cache, iterations=1000):
    # Measure baseline performance
    start_time = time.time()
    
    for i in range(iterations):
        await cache.set(f"key_{i}", f"value_{i}")
        result = await cache.get(f"key_{i}")
        assert result == f"value_{i}"
    
    duration = time.time() - start_time
    ops_per_second = (iterations * 2) / duration  # 2 ops per iteration
    
    return {
        "total_duration": duration,
        "operations_per_second": ops_per_second,
        "avg_operation_time": duration / (iterations * 2)
    }
```

### Post-Migration Validation

After migration, validate performance hasn't regressed:

```python
# post_migration_benchmark.py
from app.infrastructure.cache import CacheFactory

async def validate_migration_performance():
    # Test new factory patterns
    factory = CacheFactory()
    new_cache = await factory.for_web_app()
    
    new_metrics = await benchmark_cache_operations(new_cache)
    
    # Compare with baseline (should be within 10% of original performance)
    assert new_metrics["operations_per_second"] >= baseline_ops * 0.9
    
    return new_metrics
```

### Performance Monitoring Integration

```python
# continuous_performance_monitoring.py
from app.infrastructure.cache.monitoring import CachePerformanceMonitor

async def setup_migration_monitoring():
    monitor = CachePerformanceMonitor()
    
    # Set up alerts for performance regression
    monitor.set_performance_threshold(
        max_operation_time=0.1,  # 100ms max
        min_hit_rate=0.7,        # 70% hit rate minimum
        max_memory_usage=100_000_000  # 100MB max
    )
    
    return monitor
```

## Troubleshooting Common Migration Issues

### Issue 1: Configuration Validation Errors

**Problem**: `ValidationError` during cache creation
```
ValidationError: redis_url must start with 'redis://' or 'rediss://'
```

**Solution**:
```python
# Check configuration format
from app.infrastructure.cache import CacheConfigBuilder

try:
    config = CacheConfigBuilder().with_redis("invalid-url").build()
except ValidationError as e:
    print(f"Configuration error: {e.message}")
    print(f"Context: {e.context}")
    
    # Fix configuration
    config = CacheConfigBuilder().with_redis("redis://localhost:6379").build()
```

### Issue 2: Redis Connection Failures

**Problem**: Cache creation fails with Redis connection errors

**Solution**:
```python
# Enable graceful fallback
factory = CacheFactory()
cache = await factory.for_web_app(
    redis_url="redis://unreachable:6379",
    fail_on_connection_error=False  # Enable fallback to InMemoryCache
)

# Check cache type after creation
if isinstance(cache, InMemoryCache):
    logger.warning("Using InMemoryCache fallback - Redis unavailable")
```

### Issue 3: Test Isolation Problems

**Problem**: Tests interfere with each other due to shared cache state

**Solution**:
```python
# Use isolated test cache for each test
@pytest.fixture
async def isolated_cache():
    factory = CacheFactory()
    return await factory.for_testing(
        use_memory_cache=True,  # Ensures isolation
        default_ttl=10  # Short TTL for test cleanup
    )

# Or use Redis test database with cleanup
@pytest.fixture
async def redis_test_cache():
    factory = CacheFactory()
    cache = await factory.for_testing(
        redis_url="redis://localhost:6379/15"  # Dedicated test DB
    )
    yield cache
    
    # Clean up test data
    if hasattr(cache, 'invalidate_all'):
        await cache.invalidate_all()
```

### Issue 4: Dependency Injection Errors

**Problem**: FastAPI dependency resolution fails

**Solution**:
```python
# Ensure proper dependency order
from app.infrastructure.cache.dependencies import get_cache_service
from app.core.config import Settings
from fastapi import Depends

@app.get("/endpoint")
async def handler(
    cache = Depends(get_cache_service),  # Dependency resolves automatically
    settings: Settings = Depends()  # Available if needed
):
    # Cache properly injected with lifecycle management
    pass
```

### Issue 5: Performance Regression

**Problem**: New cache implementation is slower than legacy

**Diagnosis**:
```python
# Enable performance monitoring
from app.infrastructure.cache.monitoring import CachePerformanceMonitor

monitor = CachePerformanceMonitor()
factory = CacheFactory()
cache = await factory.for_web_app(performance_monitor=monitor)

# Check performance metrics
await cache.set("test", "value")
stats = monitor.get_performance_summary()
print(f"Operation timing: {stats}")
```

**Solutions**:
- Check compression settings (reduce level if too high)
- Verify L1 cache is enabled for frequently accessed data
- Ensure Redis connection pooling is working
- Review text hashing thresholds for AI caches

### Issue 6: Memory Usage Increase

**Problem**: New cache implementation uses more memory

**Diagnosis**:
```python
# Monitor memory usage
import psutil
import gc

def check_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.1f}MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.1f}MB")
    
    # Force garbage collection
    gc.collect()
```

**Solutions**:
- Reduce L1 cache size: `l1_cache_size=50` instead of default 100
- Enable compression: `compression_threshold=500`
- Use memory cache only for testing: `use_memory_cache=True`
- Review cache TTL settings for faster eviction

## Migration Timeline & Planning

### Recommended Migration Schedule

**Week 1: Preparation**
- [ ] Code audit and compatibility assessment
- [ ] Performance baseline establishment
- [ ] Test environment setup
- [ ] Team training on new patterns

**Week 2: Test Environment Migration**
- [ ] Update test fixtures and patterns
- [ ] Migrate development environment
- [ ] Performance validation
- [ ] Integration test verification

**Week 3: Staging Environment Migration**
- [ ] Deploy new factory patterns to staging
- [ ] Load testing and performance validation
- [ ] Error handling verification
- [ ] Monitoring and alerting setup

**Week 4: Production Migration**
- [ ] Gradual production rollout (25% → 50% → 100%)
- [ ] Real-time monitoring and metrics
- [ ] Rollback procedures ready
- [ ] Post-migration validation

### Risk Mitigation

**High-Risk Areas**:
- **Custom cache wrappers**: May require significant refactoring
- **Complex test setups**: Risk of test behavior changes
- **High-traffic endpoints**: Performance regression risk
- **AI workloads**: Cache key generation changes

**Mitigation Strategies**:
- **Gradual rollout**: Deploy incrementally with monitoring
- **Feature flags**: Enable quick rollback if issues arise
- **Parallel deployment**: Run old and new systems simultaneously
- **Comprehensive testing**: Extensive testing before production

### Rollback Plan

If migration issues arise, follow this rollback procedure:

1. **Immediate Rollback**:
   ```python
   # Quick rollback via feature flag
   USE_LEGACY_CACHE = True
   ```

2. **Diagnostic Collection**:
   ```python
   # Collect metrics and logs
   await cleanup_cache_registry()
   monitor.export_performance_data()
   ```

3. **Issue Analysis**:
   - Review performance metrics
   - Analyze error logs
   - Check configuration differences

4. **Incremental Re-deployment**:
   - Fix identified issues
   - Test in development/staging
   - Re-deploy with monitoring

## Conclusion

The migration from inheritance-based cache patterns to factory-based explicit cache creation provides significant improvements in reliability, testability, and maintainability. Following this guide ensures a smooth transition with minimal risk and maximum benefit.

### Key Success Factors

1. **Thorough Planning**: Complete pre-migration assessment and planning
2. **Gradual Migration**: Incremental rollout with monitoring
3. **Performance Validation**: Continuous performance monitoring
4. **Team Training**: Ensure team understands new patterns
5. **Rollback Readiness**: Have rollback procedures ready

### Post-Migration Benefits

- **Deterministic Behavior**: Explicit cache creation eliminates configuration guessing
- **Improved Testing**: Isolated test environments with predictable behavior
- **Better Monitoring**: Comprehensive health checks and performance metrics
- **Enhanced Reliability**: Structured error handling with graceful degradation
- **Simplified Maintenance**: Centralized configuration and lifecycle management

For additional support during migration, refer to:
- **[Cache Infrastructure Guide](./CACHE.md)**: Comprehensive cache architecture documentation
- **[Code Standards](../developer/CODE_STANDARDS.md)**: Patterns and best practices
- **[Troubleshooting Guide](../operations/TROUBLESHOOTING.md)**: Common issues and solutions

## Related Documentation

### Prerequisites
> Complete these guides before proceeding with cache migration.

- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Understanding the architectural separation is crucial for proper cache usage
- **[Cache Infrastructure Guide](./CACHE.md)**: Comprehensive understanding of the cache architecture and capabilities

### Related Topics  
> Explore these related guides for additional context and complementary information.

- **[Code Standards & Patterns](../developer/CODE_STANDARDS.md)**: Follow established patterns when migrating cache implementations
- **[Testing Strategy](../developer/TESTING.md)**: Maintain test coverage standards during cache migration
- **[Exception Handling](../developer/EXCEPTION_HANDLING.md)**: Understand the new structured exception patterns used in cache factories
- **[Monitoring Infrastructure](./MONITORING.md)**: Performance monitoring during and after migration

### Next Steps
> Continue your journey with these advanced guides and practical applications.

- **[Performance Optimization](../operations/PERFORMANCE_OPTIMIZATION.md)**: Optimize cache performance after migration completion
- **[Troubleshooting Guide](../operations/TROUBLESHOOTING.md)**: Diagnose and resolve post-migration cache issues
- **[Deployment Guide](../developer/DEPLOYMENT.md)**: Deploy migrated cache infrastructure to production environments

---
*💡 **Need help?** Check the [Documentation Index](../../DOCS_INDEX.md) for a complete overview of all available guides.*