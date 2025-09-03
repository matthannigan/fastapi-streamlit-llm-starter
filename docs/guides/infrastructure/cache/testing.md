---
sidebar_label: Testing
---

# Cache Infrastructure Testing Guide

This comprehensive guide covers testing strategies, patterns, and best practices for the cache infrastructure, including unit tests, integration tests, performance benchmarks, and CI/CD configuration.

## Table of Contents

1. [Test Architecture Overview](#test-architecture-overview)
2. [Test Fixture Patterns](#test-fixture-patterns)  
3. [Unit Testing Strategies](#unit-testing-strategies)
4. [Integration Testing with Redis](#integration-testing-with-redis)
5. [Performance Testing Setup](#performance-testing-setup)
6. [Mock Callback Patterns](#mock-callback-patterns)
7. [CI/CD Testing Configuration](#cicd-testing-configuration)
8. [Test Isolation and Cleanup](#test-isolation-and-cleanup)
9. [Async Testing Best Practices](#async-testing-best-practices)
10. [Error Handling Test Scenarios](#error-handling-test-scenarios)
11. [Multi-Environment Testing](#multi-environment-testing)

## Test Architecture Overview

The cache infrastructure testing follows a layered approach aligned with the infrastructure vs domain architecture:

```
backend/tests/infrastructure/cache/
├── conftest.py                    # Shared fixtures and Redis configuration
├── test_factory.py               # CacheFactory consolidated approach tests
├── test_base.py                  # Abstract cache interface tests
├── test_memory.py                # InMemoryCache implementation tests
├── test_redis.py                 # Redis cache integration tests
├── test_monitoring.py            # Performance monitoring tests
├── test_ai_cache_integration.py  # AI-specific cache features
└── benchmarks/                   # Performance benchmark suite
    ├── conftest.py              # Benchmark-specific fixtures
    ├── test_config.py           # Benchmark configuration tests
    ├── test_core.py             # Core benchmark engine tests
    └── test_integration.py      # End-to-end benchmark tests
```

### Test Categories

**Unit Tests** (>90% coverage required):
- Test individual cache components in isolation
- Mock external dependencies (Redis, monitoring)
- Fast execution (<100ms per test)
- Use `InMemoryCache` for deterministic behavior

**Integration Tests**:
- Test component interactions with real Redis instances
- Test cache fallback mechanisms
- Validate configuration-based instantiation
- Use Redis test databases with cleanup

**Performance Tests** (`@pytest.mark.slow`):
- Benchmark cache operations under load
- Memory usage and compression efficiency
- Regression detection for performance
- Configurable thresholds for CI/CD

## Test Fixture Patterns

### Basic Cache Fixtures

```python
# backend/tests/infrastructure/cache/conftest.py

import pytest
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.memory import InMemoryCache

@pytest.fixture
async def memory_cache():
    """Create an in-memory cache for unit testing."""
    cache = InMemoryCache(max_size=100, default_ttl=3600)
    yield cache
    await cache.clear()  # Cleanup after test

@pytest.fixture
async def factory_cache_for_testing():
    """Create a cache using factory for testing patterns."""
    factory = CacheFactory()
    cache = await factory.for_testing(
        use_memory_cache=True,
        default_ttl=60,
        l1_cache_size=50
    )
    yield cache
    await cache.clear()

@pytest.fixture
async def factory_cache_with_redis_fallback():
    """Test Redis fallback behavior with invalid Redis URL."""
    factory = CacheFactory()
    cache = await factory.for_testing(
        redis_url="redis://nonexistent:6379/15",
        fail_on_connection_error=False,
        default_ttl=30
    )
    yield cache
    await cache.clear()
```

### Redis Integration Fixtures

```python
# Redis fixtures (only available when pytest-redis is installed)

if HAS_PYTEST_REDIS:
    import pytest_redis

    # Define fixtures via factory assignment (recommended pattern)
    redis_proc = pytest_redis.factories.redis_proc(port=None, timeout=60)
    
    try:
        redis_db = pytest_redis.factories.redisdb("redis_proc", dbnum=0)
    except TypeError:  # fallback for older versions
        redis_db = pytest_redis.factories.redisdb("redis_proc", db=0)

    @pytest.fixture
    async def redis_cache(redis_db):
        """Create a Redis cache with real Redis instance for integration testing."""
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        
        # Get Redis connection details
        redis_url = f"redis://localhost:{redis_db.connection_pool.connection_kwargs['port']}/0"
        
        cache = GenericRedisCache(
            redis_url=redis_url,
            default_ttl=3600,
            enable_l1_cache=True,
            l1_cache_size=100
        )
        yield cache
        
        # Cleanup: flush the test database
        await cache.clear()
        redis_db.flushdb()
```

### Performance Testing Fixtures

```python
# backend/tests/infrastructure/cache/benchmarks/conftest.py

@pytest.fixture
def performance_test_data():
    """Generate test data for performance benchmarks."""
    return [
        {
            "key": f"test_key_{i}", 
            "value": f"test_value_{i}" * 10, 
            "size_kb": 0.1
        }
        for i in range(50)
    ]

@pytest.fixture
def benchmark_config():
    """Create benchmark configuration for testing."""
    from app.infrastructure.cache.benchmarks.config import BenchmarkConfig
    
    return BenchmarkConfig(
        default_iterations=25,
        warmup_iterations=3,
        timeout_seconds=30,
        enable_memory_tracking=True,
        enable_compression_tests=False
    )

@pytest.fixture
async def benchmark_cache_pair():
    """Create cache pair for benchmark comparison testing."""
    factory = CacheFactory()
    
    baseline_cache = await factory.for_testing(
        use_memory_cache=True,
        default_ttl=3600,
        l1_cache_size=50
    )
    
    optimized_cache = await factory.for_testing(
        use_memory_cache=True,
        default_ttl=3600,
        l1_cache_size=100  # Larger cache for comparison
    )
    
    yield baseline_cache, optimized_cache
    
    await baseline_cache.clear()
    await optimized_cache.clear()
```

## Unit Testing Strategies

### Factory Method Testing

```python
# Test CacheFactory consolidated approach with explicit instantiation patterns

class TestCacheFactoryUnitTests:
    """Unit tests for CacheFactory using the consolidated factory approach with explicit instantiation patterns."""

    @pytest.mark.asyncio
    async def test_for_web_app_memory_fallback(self):
        """Test web app cache creation with memory fallback."""
        factory = CacheFactory()
        
        # Use invalid Redis URL to trigger memory fallback
        cache = await factory.for_web_app(
            redis_url="redis://nonexistent:6379",
            fail_on_connection_error=False,
            default_ttl=1800,
            l1_cache_size=200
        )
        
        # Verify memory fallback occurred
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 1800
        assert cache.max_size == 200

    @pytest.mark.asyncio
    async def test_for_ai_app_custom_parameters(self):
        """Test AI app cache with AI-specific parameters."""
        factory = CacheFactory()
        
        operation_ttls = {"summarize": 1800, "sentiment": 3600}
        
        cache = await factory.for_ai_app(
            redis_url="redis://nonexistent:6379",
            default_ttl=7200,
            text_hash_threshold=1000,
            memory_cache_size=200,
            operation_ttls=operation_ttls,
            fail_on_connection_error=False
        )
        
        assert isinstance(cache, InMemoryCache)  # Fallback due to connection failure
        assert cache.default_ttl == 7200
        assert cache.max_size == 200

    @pytest.mark.asyncio
    async def test_factory_validation_errors(self):
        """Test comprehensive factory input validation."""
        factory = CacheFactory()
        
        # Test invalid redis_url
        with pytest.raises(ValidationError, match="redis_url must start with 'redis://'"):
            await factory.for_web_app(redis_url="http://localhost:6379")
        
        # Test invalid TTL
        with pytest.raises(ValidationError, match="default_ttl must be non-negative"):
            await factory.for_web_app(default_ttl=-100)
        
        # Test AI-specific validation
        with pytest.raises(ValidationError, match="text_hash_threshold must be a non-negative integer"):
            await factory.for_ai_app(text_hash_threshold=-1)
```

### Cache Operations Testing

```python
class TestCacheOperationsUnit:
    """Unit tests for basic cache operations using memory cache."""

    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, memory_cache):
        """Test basic set/get/delete operations."""
        # Test set and get
        await memory_cache.set("test_key", "test_value")
        value = await memory_cache.get("test_key")
        assert value == "test_value"
        
        # Test delete
        await memory_cache.delete("test_key")
        value = await memory_cache.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, memory_cache):
        """Test TTL-based expiration."""
        # Set with short TTL
        await memory_cache.set("ttl_test", "value", ttl=1)
        
        # Value should exist immediately
        value = await memory_cache.get("ttl_test")
        assert value == "value"
        
        # Wait for expiration
        await asyncio.sleep(1.5)
        
        # Value should be expired
        value = await memory_cache.get("ttl_test")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_size_limits(self):
        """Test cache size limit enforcement."""
        cache = InMemoryCache(max_size=3, default_ttl=3600)
        
        # Fill cache to capacity
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Verify all keys exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        
        # Add fourth key (should evict oldest)
        await cache.set("key4", "value4")
        
        # First key should be evicted
        assert await cache.get("key1") is None
        assert await cache.get("key4") == "value4"
```

## Integration Testing with Redis

### Redis Connection Testing

```python
@pytest.mark.redis
class TestRedisIntegration:
    """Integration tests requiring real Redis instances."""

    @pytest.mark.asyncio
    async def test_redis_cache_operations(self, redis_cache):
        """Test cache operations with real Redis."""
        # Test basic operations
        await redis_cache.set("redis_test", {"data": "value"})
        result = await redis_cache.get("redis_test")
        assert result == {"data": "value"}
        
        # Test complex data structures
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "number": 42
        }
        await redis_cache.set("complex", complex_data)
        result = await redis_cache.get("complex")
        assert result == complex_data

    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self):
        """Test graceful handling of Redis connection failures."""
        factory = CacheFactory()
        
        # Test with invalid Redis URL but allow fallback
        cache = await factory.for_web_app(
            redis_url="redis://nonexistent:6379",
            fail_on_connection_error=False
        )
        
        # Should fall back to memory cache
        assert isinstance(cache, InMemoryCache)
        
        # Should still function normally
        await cache.set("fallback_test", "value")
        result = await cache.get("fallback_test")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_redis_failover_behavior(self, redis_db):
        """Test cache behavior during Redis failover scenarios."""
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        
        redis_url = f"redis://localhost:{redis_db.connection_pool.connection_kwargs['port']}/0"
        
        cache = GenericRedisCache(
            redis_url=redis_url,
            default_ttl=3600,
            enable_l1_cache=True
        )
        
        # Store data in cache
        await cache.set("failover_test", "important_data")
        assert await cache.get("failover_test") == "important_data"
        
        # Simulate Redis connection loss (implementation depends on cache design)
        # This would test L1 cache behavior during Redis unavailability
```

### Cross-Module Integration

```python
@pytest.mark.asyncio
async def test_cache_monitoring_integration():
    """Test integration between cache and monitoring systems."""
    factory = CacheFactory()
    cache = await factory.for_testing(use_memory_cache=True)
    
    # Perform cache operations
    await cache.set("monitor_test", "value")
    await cache.get("monitor_test")
    await cache.get("nonexistent_key")  # Cache miss
    
    # Verify monitoring integration (if available)
    if hasattr(factory, '_performance_monitor') and factory._performance_monitor:
        monitor = factory._performance_monitor
        assert monitor.total_operations >= 3
        assert monitor.cache_hits >= 1
        assert monitor.cache_misses >= 1
```

## Performance Testing Setup

### Benchmark Configuration

```python
# Performance testing with configurable thresholds

@pytest.mark.slow
class TestCachePerformance:
    """Performance tests for cache operations."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, benchmark_config, performance_test_data):
        """Test performance of bulk cache operations."""
        from app.infrastructure.cache.benchmarks.core import CacheBenchmarkRunner
        
        factory = CacheFactory()
        cache = await factory.for_testing(use_memory_cache=True, l1_cache_size=200)
        
        runner = CacheBenchmarkRunner(benchmark_config)
        
        # Run bulk set operations benchmark
        set_results = await runner.run_bulk_set_benchmark(
            cache=cache,
            test_data=performance_test_data,
            iterations=benchmark_config.default_iterations
        )
        
        # Verify performance thresholds
        assert set_results.avg_duration_ms < 50.0  # Average < 50ms
        assert set_results.success_rate == 1.0      # 100% success
        assert set_results.operations_per_second > 20  # Minimum throughput

    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self, memory_cache):
        """Test memory usage tracking during cache operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_data = "x" * (1024 * 100)  # 100KB strings
        for i in range(100):
            await memory_cache.set(f"large_key_{i}", large_data)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Verify memory usage is reasonable (< 50MB increase)
        assert memory_increase < 50.0
        
        # Cleanup and verify memory release
        await memory_cache.clear()
        
    @pytest.mark.asyncio
    async def test_compression_performance(self):
        """Test compression performance and efficiency."""
        factory = CacheFactory()
        cache = await factory.for_ai_app(
            use_memory_cache=True,
            compression_threshold=1000,  # Enable compression for data > 1KB
            fail_on_connection_error=False
        )
        
        # Create compressible data
        compressible_data = "This is repeated text. " * 100  # ~2.3KB
        
        start_time = time.time()
        await cache.set("compression_test", compressible_data)
        compression_time = time.time() - start_time
        
        # Verify compression performance
        assert compression_time < 0.1  # Compression should be fast
        
        # Verify data integrity
        result = await cache.get("compression_test")
        assert result == compressible_data
```

### Regression Testing

```python
@pytest.mark.slow
class TestPerformanceRegression:
    """Regression tests for cache performance."""

    @pytest.mark.asyncio
    async def test_performance_regression_detection(self):
        """Test automatic detection of performance regressions."""
        from app.infrastructure.cache.benchmarks.core import CacheBenchmarkRunner
        from app.infrastructure.cache.benchmarks.config import ConfigPresets
        
        # Use CI configuration for consistent results
        config = ConfigPresets.ci_config()
        runner = CacheBenchmarkRunner(config)
        
        # Create baseline and current caches
        factory = CacheFactory()
        baseline_cache = await factory.for_testing(
            use_memory_cache=True,
            l1_cache_size=50  # Smaller cache
        )
        current_cache = await factory.for_testing(
            use_memory_cache=True,
            l1_cache_size=100  # Larger cache (should be faster)
        )
        
        # Run comparison benchmark
        comparison = await runner.run_cache_comparison(
            original_cache=baseline_cache,
            new_cache=current_cache,
            test_suite_name="regression_test"
        )
        
        # Verify regression detection
        assert not comparison.regression_detected
        assert comparison.performance_change_percent < 0  # Improvement expected
```

## Mock Callback Patterns

### Callback Composition Testing

```python
class TestCacheCallbacks:
    """Test cache callback and monitoring integration."""

    @pytest.mark.asyncio
    async def test_performance_callback_mocking(self):
        """Test performance monitoring callbacks with mocks."""
        from unittest.mock import AsyncMock, MagicMock
        
        # Create mock performance monitor
        mock_monitor = MagicMock()
        mock_monitor.record_cache_operation_time = AsyncMock()
        mock_monitor.record_key_generation_time = AsyncMock()
        
        # Create cache with mocked monitoring
        cache = InMemoryCache(max_size=100, default_ttl=3600)
        
        # Patch the monitoring integration
        with patch.object(cache, '_performance_monitor', mock_monitor):
            await cache.set("callback_test", "value")
            await cache.get("callback_test")
        
        # Verify callbacks were invoked
        assert mock_monitor.record_cache_operation_time.call_count >= 2
        
        # Verify callback parameters
        call_args = mock_monitor.record_cache_operation_time.call_args_list
        set_call = call_args[0][1]  # keyword arguments
        assert set_call['operation'] == 'set'
        assert 'duration' in set_call

    @pytest.mark.asyncio
    async def test_error_callback_handling(self):
        """Test error handling in callback chains."""
        from unittest.mock import AsyncMock, MagicMock
        
        # Create mock that raises exception
        mock_callback = AsyncMock(side_effect=Exception("Callback error"))
        
        cache = InMemoryCache(max_size=100, default_ttl=3600)
        
        # Patch callback to raise error
        with patch.object(cache, '_on_cache_operation', mock_callback):
            # Cache operations should continue despite callback errors
            await cache.set("error_test", "value")
            result = await cache.get("error_test")
            assert result == "value"
        
        # Verify callback was attempted
        assert mock_callback.called

    def test_monitoring_callback_composition(self):
        """Test composition of multiple monitoring callbacks."""
        from unittest.mock import MagicMock
        
        # Create multiple mock callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()
        
        # Test callback composition pattern
        def compose_callbacks(*callbacks):
            def composed_callback(*args, **kwargs):
                results = []
                for callback in callbacks:
                    try:
                        result = callback(*args, **kwargs)
                        results.append(result)
                    except Exception as e:
                        results.append(f"Error: {e}")
                return results
            return composed_callback
        
        # Create composed callback
        composed = compose_callbacks(callback1, callback2, callback3)
        
        # Test invocation
        results = composed("test_arg", key="test_value")
        
        # Verify all callbacks were called
        assert len(results) == 3
        callback1.assert_called_once_with("test_arg", key="test_value")
        callback2.assert_called_once_with("test_arg", key="test_value")
        callback3.assert_called_once_with("test_arg", key="test_value")
```

## CI/CD Testing Configuration

### Makefile Integration

```makefile
# Cache infrastructure testing targets

# Run cache infrastructure tests with Redis
test-backend-infra-cache:
	@echo "🧪 Running backend cache infrastructure service tests that use redis..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -m "redis" -n 0 -q --retries 2 --retry-delay 5
	@echo "🧪 Running backend cache infrastructure service tests (excluding redis tests)..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -m "not redis" -n 0 -q --retries 2 --retry-delay 5

# Run cache performance tests
test-backend-cache-performance:
	@echo "🧪 Running cache performance benchmarks..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/benchmarks/ --run-slow -q

# Run cache integration tests
test-backend-cache-integration:
	@echo "🧪 Running cache integration tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -m "integration" -q

# Cache-specific test targets
test-cache-unit:
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -m "not redis and not slow and not integration" -v

test-cache-redis:
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -m "redis" -n 0 -v

test-cache-all:
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ --run-slow -v
```

### GitHub Actions Configuration

```yaml
# .github/workflows/cache-tests.yml
name: Cache Infrastructure Tests

on:
  push:
    paths:
      - 'backend/app/infrastructure/cache/**'
      - 'backend/tests/infrastructure/cache/**'
  pull_request:
    paths:
      - 'backend/app/infrastructure/cache/**'
      - 'backend/tests/infrastructure/cache/**'

jobs:
  cache-unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        make install
    
    - name: Run cache unit tests
      run: make test-cache-unit
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: cache-unit-tests

  cache-integration-tests:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        make install
        pip install pytest-redis
    
    - name: Run Redis integration tests
      run: make test-cache-redis
      env:
        REDIS_URL: redis://localhost:6379
    
    - name: Run cache integration tests
      run: make test-cache-integration

  cache-performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        make install
    
    - name: Run performance benchmarks
      run: make test-backend-cache-performance
      env:
        BENCHMARK_ENV: ci
        BENCHMARK_ENABLE_REGRESSION_DETECTION: true
    
    - name: Upload benchmark results
      uses: actions/upload-artifact@v3
      with:
        name: cache-benchmarks
        path: backend/benchmark_results/
```

### Docker Testing Configuration

```dockerfile
# tests.Dockerfile for cache testing
FROM python:3.10-slim

WORKDIR /app

# Install Redis for integration tests
RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt backend/requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# Copy source code
COPY backend/ ./

# Set environment variables for testing
ENV PYTHONPATH=/app
ENV PYTEST_REDIS_PROC_PORT=6380
ENV BENCHMARK_ENV=docker

# Run cache tests
CMD ["python", "-m", "pytest", "tests/infrastructure/cache/", "-v", "--tb=short"]
```

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  cache-tests:
    build:
      context: .
      dockerfile: tests.Dockerfile
    depends_on:
      - redis-test
    environment:
      - REDIS_URL=redis://redis-test:6379
      - PYTEST_ARGS=tests/infrastructure/cache/
    volumes:
      - ./backend/test-results:/app/test-results
    command: >
      sh -c "
        echo 'Running cache infrastructure tests...' &&
        python -m pytest tests/infrastructure/cache/ 
          --junitxml=/app/test-results/cache-tests.xml
          --cov=app.infrastructure.cache
          --cov-report=xml:/app/test-results/cache-coverage.xml
          -v
      "

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    command: redis-server --appendonly yes
    volumes:
      - cache-test-data:/data

volumes:
  cache-test-data:
```

## Test Isolation and Cleanup

### Automatic Cleanup Patterns

```python
# Comprehensive cleanup fixtures

@pytest.fixture(autouse=True)
async def cache_cleanup():
    """Automatic cleanup fixture for all cache tests."""
    # Setup: Clear any existing cache state
    yield
    
    # Cleanup: Ensure clean state for next test
    import gc
    gc.collect()  # Force garbage collection

@pytest.fixture
async def isolated_cache():
    """Create an isolated cache instance with guaranteed cleanup."""
    cache = InMemoryCache(max_size=50, default_ttl=300)
    
    try:
        yield cache
    finally:
        # Guaranteed cleanup even if test fails
        await cache.clear()
        
        # Additional cleanup for memory cache
        if hasattr(cache, '_data'):
            cache._data.clear()
        if hasattr(cache, '_access_times'):
            cache._access_times.clear()

@pytest.fixture
async def redis_cache_with_cleanup(redis_db):
    """Redis cache with comprehensive cleanup."""
    from app.infrastructure.cache.redis_generic import GenericRedisCache
    
    redis_url = f"redis://localhost:{redis_db.connection_pool.connection_kwargs['port']}/0"
    cache = GenericRedisCache(redis_url=redis_url, default_ttl=3600)
    
    try:
        yield cache
    finally:
        # Clear cache data
        await cache.clear()
        
        # Flush Redis database
        redis_db.flushdb()
        
        # Close connections
        if hasattr(cache, '_redis_client'):
            await cache._redis_client.close()
```

### Environment Isolation

```python
# Environment variable isolation for tests

@pytest.fixture
def clean_environment(monkeypatch):
    """Provide clean environment for cache configuration tests."""
    # Clear cache-related environment variables
    cache_env_vars = [
        'REDIS_URL', 'CACHE_TTL', 'CACHE_SIZE', 'ENABLE_CACHE_COMPRESSION',
        'CACHE_MONITORING_ENABLED', 'BENCHMARK_DEFAULT_ITERATIONS'
    ]
    
    for var in cache_env_vars:
        monkeypatch.delenv(var, raising=False)
    
    # Set test-specific defaults
    test_env = {
        'CACHE_ENV': 'test',
        'CACHE_TTL': '60',
        'BENCHMARK_DEFAULT_ITERATIONS': '10'
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env

@pytest.fixture
def redis_test_environment(monkeypatch, redis_db):
    """Set up Redis-specific test environment."""
    redis_port = redis_db.connection_pool.connection_kwargs['port']
    redis_url = f"redis://localhost:{redis_port}/0"
    
    monkeypatch.setenv('REDIS_URL', redis_url)
    monkeypatch.setenv('REDIS_TEST_DB', '0')
    monkeypatch.setenv('REDIS_CONNECTION_TIMEOUT', '5')
    
    return {'redis_url': redis_url, 'redis_port': redis_port}
```

## Async Testing Best Practices

### Async Fixture Patterns

```python
# Proper async test patterns for cache operations

@pytest.mark.asyncio
class TestAsyncCacheOperations:
    """Demonstrate proper async testing patterns for cache operations."""

    async def test_concurrent_cache_operations(self, memory_cache):
        """Test cache behavior under concurrent access."""
        import asyncio
        
        async def set_operation(key: str, value: str):
            await memory_cache.set(key, value)
            return f"set_{key}"
        
        async def get_operation(key: str):
            result = await memory_cache.get(key)
            return f"get_{key}:{result}"
        
        # Run concurrent operations
        tasks = []
        for i in range(10):
            tasks.append(set_operation(f"concurrent_{i}", f"value_{i}"))
            tasks.append(get_operation(f"concurrent_{i}"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0
        
        # Verify all set operations completed
        set_results = [r for r in results if r.startswith("set_")]
        assert len(set_results) == 10

    async def test_async_context_manager_pattern(self):
        """Test async context manager pattern for cache lifecycle."""
        
        class AsyncCacheContext:
            def __init__(self):
                self.cache = None
            
            async def __aenter__(self):
                self.cache = InMemoryCache(max_size=100, default_ttl=3600)
                return self.cache
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if self.cache:
                    await self.cache.clear()
        
        # Use async context manager
        async with AsyncCacheContext() as cache:
            await cache.set("context_test", "value")
            result = await cache.get("context_test")
            assert result == "value"
        
        # Cache should be cleaned up automatically

    async def test_async_generator_testing(self, memory_cache):
        """Test async generator patterns for cache streaming."""
        
        async def cache_data_generator():
            """Generate test data asynchronously."""
            for i in range(5):
                yield f"key_{i}", f"value_{i}"
                await asyncio.sleep(0.01)  # Simulate async work
        
        # Store data using async generator
        async for key, value in cache_data_generator():
            await memory_cache.set(key, value)
        
        # Verify all data was stored
        for i in range(5):
            result = await memory_cache.get(f"key_{i}")
            assert result == f"value_{i}"

    async def test_timeout_handling(self, memory_cache):
        """Test async timeout handling in cache operations."""
        import asyncio
        
        # Simulate slow operation
        async def slow_cache_operation():
            await asyncio.sleep(2)  # 2 second delay
            await memory_cache.set("slow_key", "slow_value")
        
        # Test timeout handling
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_cache_operation(), timeout=1.0)
        
        # Verify cache state remains consistent
        result = await memory_cache.get("slow_key")
        assert result is None  # Operation didn't complete
```

### Error Handling in Async Tests

```python
@pytest.mark.asyncio
async def test_async_error_propagation():
    """Test proper error propagation in async cache operations."""
    from unittest.mock import AsyncMock, patch
    
    # Create mock that raises async exception
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = asyncio.TimeoutError("Redis timeout")
    
    cache = InMemoryCache(max_size=100, default_ttl=3600)
    
    # Patch Redis client to simulate connection issues
    with patch.object(cache, '_redis_client', mock_redis):
        # Error should be handled gracefully
        with pytest.raises(asyncio.TimeoutError):
            await cache.set("error_test", "value")

@pytest.mark.asyncio
async def test_async_resource_cleanup():
    """Test proper async resource cleanup in error scenarios."""
    
    class ResourceTracker:
        def __init__(self):
            self.resources = []
            self.cleaned_up = False
        
        async def acquire_resource(self):
            resource = f"resource_{len(self.resources)}"
            self.resources.append(resource)
            return resource
        
        async def cleanup(self):
            self.resources.clear()
            self.cleaned_up = True
    
    tracker = ResourceTracker()
    
    try:
        # Acquire resources
        resource1 = await tracker.acquire_resource()
        resource2 = await tracker.acquire_resource()
        
        assert len(tracker.resources) == 2
        
        # Simulate error that should trigger cleanup
        raise ValueError("Simulated error")
        
    except ValueError:
        # Cleanup should happen in finally block
        await tracker.cleanup()
    
    assert tracker.cleaned_up
    assert len(tracker.resources) == 0
```

## Error Handling Test Scenarios

### Configuration Error Testing

```python
class TestCacheConfigurationErrors:
    """Test comprehensive error handling for cache configuration."""

    @pytest.mark.asyncio
    async def test_invalid_redis_url_errors(self):
        """Test various Redis URL validation errors."""
        factory = CacheFactory()
        
        error_cases = [
            ("", "redis_url cannot be empty"),
            ("http://localhost:6379", "must start with 'redis://'"),
            ("redis://", "must include host information"),
            (123, "redis_url must be a string"),
            (None, "redis_url is required")
        ]
        
        for invalid_url, expected_error in error_cases:
            with pytest.raises(ValidationError, match=expected_error):
                if invalid_url is None:
                    await factory.create_cache_from_config({})
                else:
                    await factory.for_web_app(redis_url=invalid_url)

    @pytest.mark.asyncio
    async def test_ttl_validation_errors(self):
        """Test TTL parameter validation."""
        factory = CacheFactory()
        
        ttl_error_cases = [
            (-1, "must be non-negative"),
            ("3600", "must be an integer"),
            (86400 * 366, "must not exceed 365 days"),  # Over 1 year
            (float('inf'), "must be an integer")
        ]
        
        for invalid_ttl, expected_error in ttl_error_cases:
            with pytest.raises(ValidationError, match=expected_error):
                await factory.for_web_app(
                    redis_url="redis://localhost:6379",
                    default_ttl=invalid_ttl
                )

    @pytest.mark.asyncio
    async def test_ai_specific_validation_errors(self):
        """Test AI cache specific parameter validation."""
        factory = CacheFactory()
        
        ai_error_cases = [
            ("text_hash_threshold", -1, "must be a non-negative integer"),
            ("memory_cache_size", 0, "must be a positive integer"),
            ("operation_ttls", "invalid", "must be a dictionary"),
            ("operation_ttls", {"": 3600}, "keys must be non-empty strings"),
            ("operation_ttls", {"test": -1}, "must be a non-negative integer")
        ]
        
        for param, invalid_value, expected_error in ai_error_cases:
            with pytest.raises(ValidationError, match=expected_error):
                kwargs = {
                    "redis_url": "redis://localhost:6379",
                    param: invalid_value
                }
                await factory.for_ai_app(**kwargs)
```

### Connection Error Scenarios

```python
@pytest.mark.asyncio
async def test_redis_connection_error_scenarios():
    """Test various Redis connection error scenarios."""
    factory = CacheFactory()
    
    connection_test_cases = [
        {
            "name": "nonexistent_host",
            "redis_url": "redis://nonexistent.host:6379",
            "expected_error": "Redis connection failed"
        },
        {
            "name": "invalid_port",
            "redis_url": "redis://localhost:99999",
            "expected_error": "Redis connection failed"
        },
        {
            "name": "connection_timeout",
            "redis_url": "redis://1.2.3.4:6379",  # Non-routable IP
            "expected_error": "Redis connection failed"
        }
    ]
    
    for case in connection_test_cases:
        # Test strict mode (should raise error)
        with pytest.raises(InfrastructureError, match=case["expected_error"]):
            await factory.for_web_app(
                redis_url=case["redis_url"],
                fail_on_connection_error=True
            )
        
        # Test fallback mode (should return memory cache)
        cache = await factory.for_web_app(
            redis_url=case["redis_url"],
            fail_on_connection_error=False
        )
        assert isinstance(cache, InMemoryCache)

@pytest.mark.asyncio
async def test_runtime_redis_failures():
    """Test cache behavior when Redis fails during runtime."""
    from unittest.mock import AsyncMock, patch
    import redis.exceptions
    
    # Create cache that starts working
    factory = CacheFactory()
    cache = await factory.for_testing(use_memory_cache=True)
    
    # Verify initial operation
    await cache.set("initial_test", "works")
    assert await cache.get("initial_test") == "works"
    
    # Simulate Redis failure during operation
    with patch.object(cache, '_redis_client') as mock_redis:
        mock_redis.set.side_effect = redis.exceptions.ConnectionError("Connection lost")
        mock_redis.get.side_effect = redis.exceptions.ConnectionError("Connection lost")
        
        # Cache should handle errors gracefully
        # (Specific behavior depends on cache implementation)
        try:
            await cache.set("runtime_failure", "value")
            await cache.get("runtime_failure")
        except Exception as e:
            # Verify it's a handled exception type
            assert isinstance(e, (InfrastructureError, redis.exceptions.ConnectionError))
```

### Data Corruption Scenarios

```python
@pytest.mark.asyncio
async def test_data_corruption_handling():
    """Test cache behavior with corrupted data scenarios."""
    from unittest.mock import patch
    import json
    
    memory_cache = InMemoryCache(max_size=100, default_ttl=3600)
    
    # Test JSON serialization errors
    class UnserializableObject:
        def __init__(self):
            self.circular_ref = self
    
    unserializable = UnserializableObject()
    
    # Cache should handle serialization errors gracefully
    with pytest.raises((TypeError, ValueError)):
        await memory_cache.set("corrupt_data", unserializable)
    
    # Test data retrieval with corrupted stored data
    await memory_cache.set("valid_data", {"key": "value"})
    
    # Simulate data corruption by manually modifying internal storage
    if hasattr(memory_cache, '_data'):
        memory_cache._data["valid_data"] = "corrupted_json_string"
    
    # Cache should handle corruption gracefully
    result = await memory_cache.get("valid_data")
    # Result might be None or raise an exception depending on implementation
    # The key is that it doesn't crash the application

@pytest.mark.asyncio
async def test_memory_pressure_scenarios():
    """Test cache behavior under memory pressure."""
    import psutil
    import os
    
    # Create cache with very small size limit
    small_cache = InMemoryCache(max_size=5, default_ttl=3600)
    
    # Fill cache beyond capacity
    for i in range(10):
        await small_cache.set(f"key_{i}", f"value_{i}")
    
    # Verify cache respects size limits
    # Only 5 items should be present (LRU eviction)
    stored_count = 0
    for i in range(10):
        result = await small_cache.get(f"key_{i}")
        if result is not None:
            stored_count += 1
    
    assert stored_count == 5
    
    # Verify most recent items are preserved
    for i in range(5, 10):  # Last 5 items
        result = await small_cache.get(f"key_{i}")
        assert result == f"value_{i}"
```

## Multi-Environment Testing

### Environment-Specific Configurations

```python
# Test different environment configurations

@pytest.mark.parametrize("environment,expected_ttl,expected_size", [
    ("development", 300, 100),    # Short TTL, small cache for dev
    ("testing", 60, 50),          # Very short TTL, small cache for tests
    ("staging", 1800, 500),       # Medium TTL, medium cache for staging
    ("production", 3600, 1000),   # Long TTL, large cache for production
])
@pytest.mark.asyncio
async def test_environment_specific_cache_creation(environment, expected_ttl, expected_size):
    """Test cache creation with environment-specific defaults."""
    factory = CacheFactory()
    
    # Set environment-specific configuration
    env_configs = {
        "development": {
            "redis_url": "redis://dev-redis:6379",
            "default_ttl": expected_ttl,
            "l1_cache_size": expected_size,
            "fail_on_connection_error": False
        },
        "testing": {
            "use_memory_cache": True,
            "default_ttl": expected_ttl,
            "l1_cache_size": expected_size
        },
        "staging": {
            "redis_url": "redis://staging-redis:6379",
            "default_ttl": expected_ttl,
            "l1_cache_size": expected_size,
            "enable_l1_cache": True,
            "fail_on_connection_error": False
        },
        "production": {
            "redis_url": "redis://prod-redis:6379",
            "default_ttl": expected_ttl,
            "l1_cache_size": expected_size,
            "enable_l1_cache": True,
            "compression_threshold": 1000,
            "fail_on_connection_error": False  # Use False for testing
        }
    }
    
    config = env_configs[environment]
    
    if environment == "testing":
        cache = await factory.for_testing(**config)
    else:
        cache = await factory.for_web_app(**config)
    
    # Verify environment-specific settings
    assert cache.default_ttl == expected_ttl
    if hasattr(cache, 'max_size'):
        assert cache.max_size == expected_size

class TestCrossEnvironmentCompatibility:
    """Test cache compatibility across different environments."""

    @pytest.mark.asyncio
    async def test_cache_migration_between_environments(self):
        """Test cache data migration between different environments."""
        # Create development cache with data
        factory = CacheFactory()
        dev_cache = await factory.for_testing(
            use_memory_cache=True,
            default_ttl=300
        )
        
        # Store test data
        test_data = {"env": "development", "timestamp": "2024-01-01"}
        await dev_cache.set("migration_test", test_data)
        
        # Simulate migration to production cache
        prod_cache = await factory.for_testing(
            use_memory_cache=True,
            default_ttl=3600  # Production TTL
        )
        
        # Migrate data (in practice, this would be more complex)
        migrated_data = await dev_cache.get("migration_test")
        if migrated_data:
            await prod_cache.set("migration_test", migrated_data)
        
        # Verify migration
        result = await prod_cache.get("migration_test")
        assert result == test_data

    @pytest.mark.asyncio
    async def test_configuration_validation_across_environments(self):
        """Test configuration validation for different environments."""
        factory = CacheFactory()
        
        # Test configurations that should work in any environment
        universal_configs = [
            {"redis_url": "redis://localhost:6379", "default_ttl": 3600},
            {"use_memory_cache": True, "default_ttl": 300},
            {"redis_url": "redis://localhost:6379", "enable_l1_cache": True}
        ]
        
        for config in universal_configs:
            # Should work for web app
            if "use_memory_cache" in config:
                cache = await factory.for_testing(**config)
            else:
                cache = await factory.for_web_app(
                    **config, 
                    fail_on_connection_error=False
                )
            assert cache is not None
            
            # Should work for AI app
            cache = await factory.for_ai_app(
                **config, 
                fail_on_connection_error=False
            )
            assert cache is not None
```

### Load Testing Across Environments

```python
@pytest.mark.slow
class TestMultiEnvironmentLoad:
    """Load testing across different environment configurations."""

    @pytest.mark.asyncio
    async def test_development_environment_load(self):
        """Test cache performance under development environment load."""
        factory = CacheFactory()
        cache = await factory.for_testing(
            use_memory_cache=True,
            default_ttl=300,
            l1_cache_size=100
        )
        
        # Development load: smaller, frequent operations
        tasks = []
        for i in range(50):  # Lighter load for development
            tasks.append(cache.set(f"dev_key_{i}", f"dev_value_{i}"))
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Development should handle light load quickly
        assert end_time - start_time < 1.0  # Less than 1 second
        
        # Verify data integrity
        for i in range(50):
            result = await cache.get(f"dev_key_{i}")
            assert result == f"dev_value_{i}"

    @pytest.mark.asyncio
    async def test_production_environment_load_simulation(self):
        """Simulate production environment load patterns."""
        factory = CacheFactory()
        cache = await factory.for_testing(
            use_memory_cache=True,
            default_ttl=3600,
            l1_cache_size=1000
        )
        
        # Production load: larger, sustained operations
        async def sustained_load_worker(worker_id: int, operations: int):
            """Simulate sustained load from a single worker."""
            for i in range(operations):
                key = f"prod_worker_{worker_id}_key_{i}"
                value = f"prod_value_{i}" * 10  # Larger values
                await cache.set(key, value)
                
                # Simulate read-heavy workload (80% reads, 20% writes)
                if i % 5 != 0:  # 80% of operations are reads
                    await cache.get(key)
        
        # Run multiple workers concurrently
        workers = 5
        operations_per_worker = 100
        
        tasks = [
            sustained_load_worker(worker_id, operations_per_worker)
            for worker_id in range(workers)
        ]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_operations = workers * operations_per_worker * 1.8  # Including reads
        operations_per_second = total_operations / (end_time - start_time)
        
        # Production should handle sustained load efficiently
        assert operations_per_second > 100  # Minimum throughput expectation
```

## Summary

This comprehensive testing guide provides:

1. **Complete test architecture** aligned with infrastructure vs domain separation
2. **Practical fixture patterns** for memory, Redis, and performance testing
3. **Unit testing strategies** with >90% coverage patterns for factory methods
4. **Integration testing** with real Redis instances and cleanup automation
5. **Performance benchmarking** with configurable thresholds and regression detection
6. **Mock callback patterns** for monitoring and error simulation
7. **CI/CD configuration** with GitHub Actions and Docker integration
8. **Test isolation** with automatic cleanup and environment management
9. **Async testing best practices** for concurrent operations and error handling
10. **Comprehensive error scenarios** covering configuration, connection, and data corruption
11. **Multi-environment testing** with environment-specific configurations and load patterns

The guide demonstrates practical, production-ready testing patterns that developers can use immediately to build robust cache infrastructure with confidence in reliability and performance.

Key principles demonstrated:
- **Explicit over implicit**: Clear test fixtures and factory patterns
- **Comprehensive coverage**: Unit, integration, and performance testing
- **Environment awareness**: Different configurations for different contexts  
- **Error resilience**: Extensive error handling and recovery testing
- **Performance monitoring**: Built-in benchmarking and regression detection
- **CI/CD integration**: Automated testing with proper isolation and cleanup

Use this guide as a reference for implementing comprehensive testing strategies for cache infrastructure that maintain high quality standards while enabling rapid development and deployment cycles.

## Related Documentation

### Cache Infrastructure
- **[Cache Infrastructure Overview](./CACHE.md)** - Complete cache system architecture, components, integration patterns, and configuration management
- **[Usage Guide](./usage-guide.md)** - Practical patterns for implementing cache in applications with configuration examples
- **[API Reference](./api-reference.md)** - Complete API documentation with examples and best practices
- **[Cache Performance Benchmarking Guide](./benchmarking.md)** - Performance testing tools that complement unit and integration testing strategies

### Related Infrastructure Guides
- **[AI Infrastructure](../AI.md)** - AI service integration patterns and caching strategies
- **[Monitoring Infrastructure](../MONITORING.md)** - Performance monitoring and observability patterns
- **[Resilience Patterns](../RESILIENCE.md)** - Error handling, failover, and recovery strategies
- **[Security Guidelines](../SECURITY.md)** - Security considerations for infrastructure components

### Developer Guidelines
- **[Testing Guide](../../testing/TESTING.md)** - General testing standards and patterns across the project
- **[Code Standards](../../developer/CODE_STANDARDS.md)** - Code quality, formatting, and development standards
- **[Documentation Guidelines](../../developer/DOCUMENTATION_GUIDANCE.md)** - Documentation standards and best practices

### Cross-References
This testing guide complements the cache infrastructure documentation by providing:
- **Implementation details** for the patterns described in the [Cache Infrastructure Overview](./CACHE.md)
- **Testing strategies** for the usage patterns documented in the [Usage Guide](./usage-guide.md)
- **Validation approaches** for the APIs detailed in the [API Reference](./api-reference.md)
- **Quality assurance** for the resilience patterns covered in [Resilience Patterns](../RESILIENCE.md)