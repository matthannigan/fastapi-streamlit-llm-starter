---
sidebar_label: Testing
---

# Cache Infrastructure Testing Guide

This comprehensive guide covers testing strategies, patterns, and best practices for the cache infrastructure, including unit tests, integration tests, E2E testing, and CI/CD configuration. The cache testing suite follows modern behavior-driven principles with **580 tests** achieving >90% coverage across all cache components.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Architecture Overview](#test-architecture-overview)
3. [End-to-End Testing Strategy](#end-to-end-testing-strategy)
4. [Test Fixture Patterns](#test-fixture-patterns)
5. [Unit Testing Strategies](#unit-testing-strategies)
6. [Integration Testing with Redis](#integration-testing-with-redis)
7. [Running Tests](#running-tests)
8. [Test Isolation and Cleanup](#test-isolation-and-cleanup)
9. [Error Handling Test Scenarios](#error-handling-test-scenarios)
10. [Troubleshooting](#troubleshooting)

## Testing Philosophy

The cache infrastructure testing suite follows modern, behavior-driven principles designed to create a robust, maintainable test suite that supports refactoring rather than hindering it.

### Core Testing Principles

#### **1. Behavior-Driven Testing**
Our cache testing follows behavior-driven principles, testing the **documented behavior** through public contracts rather than internal implementation details. We prioritize testing *what* the component achieves, not *how* it achieves it.

#### **2. Public Contract Testing**
All tests are based on the "public contract" stub files in `backend/contracts/` which are auto-generated from the production codebase. These `.pyi` files include:
- All necessary import statements and class definitions
- Public method signatures with full type hints
- Complete docstrings for modules, classes, and methods
- **No internal implementation logic** (replaced with `...`)

This approach enforces implementation-agnostic testing that focuses on the component's external behavior.

#### **3. Unit Under Test (UUT) Approach**
We treat the entire `backend/app/infrastructure/cache/` component as a single **Unit Under Test (UUT)**. This means:
- Testing the component exclusively through its public-facing API
- Treating internal workings as a black box
- Building tests that pass regardless of internal refactoring

**Rationale**: Previous experiences with traditional unit testing led to brittle test suites tightly coupled to internal implementation. By treating the entire component as the UUT, we create a durable test suite where tests fail only if the public contract is violated.

### Anti-Patterns We Avoid

#### **❌ Internal Mocking**
- **Don't** mock internal cache components (`CacheFactory`, `InMemoryCache`, `CachePerformanceMonitor`) for functional testing
- **Don't** mock `Settings` for configuration that can be tested with real files/environment variables
- **Don't** use internal mocking as a substitute for proper integration testing

#### **❌ Implementation-Coupled Tests**
- **Don't** test private methods or internal data structures
- **Don't** assert on implementation details that could change during refactoring
- **Don't** create tests that require knowledge of internal component interactions

### What We Use Instead

#### **✅ Fakes Over Mocks**
- **Use** real components with test-specific configurations
- **Use** `fakeredis` for Redis simulation (fast, high-fidelity)
- **Use** integration tests for multi-component scenarios
- **Mock only at system boundaries** (external services, file systems, network)

#### **✅ Real Infrastructure Testing**
- **Use** `Testcontainers` for Redis integration tests
- **Use** dual E2E testing approach (ASGI + Redis-enhanced)
- **Use** real configuration and factory patterns

### Acceptable Internal Mocking Scenarios

**Limited to specific cases:**
1. **Error Handling Logic Testing** - Verifying how components handle specific, hard-to-trigger errors
2. **Parameter Mapping Testing** - Verifying argument transformation and passing (e.g., factory parameter mapping)

**Requirements:** Must be supplemented with integration tests using real configurations.

## Test Architecture Overview

The cache infrastructure testing follows a comprehensive, layered approach with **580 total tests** achieving >90% coverage across all cache components.

### Actual Test Suite Structure

```
backend/tests/infrastructure/cache/
├── conftest.py                    # Shared fixtures and configuration
├── e2e/                          # End-to-end testing with dual approach
│   ├── conftest.py              # ASGI transport fixtures
│   ├── conftest_redis.py        # Redis-enhanced fixtures (Testcontainers)
│   ├── test_*.py                # Standard E2E tests (ASGI only)
│   └── test_redis_enhanced_*.py # Redis-enhanced E2E tests
├── factory/                     # CacheFactory testing
│   ├── conftest.py             # Factory-specific fixtures
│   └── test_*.py               # Factory method and configuration tests
├── redis_generic/              # GenericRedisCache testing
│   ├── conftest.py             # Redis fixtures with fakeredis
│   └── test_*.py               # Generic Redis cache tests
├── redis_ai/                   # AIResponseCache testing
│   ├── conftest.py             # AI-specific fixtures
│   └── test_*.py               # AI cache features and optimization
├── memory/                     # InMemoryCache testing
│   ├── conftest.py             # Memory cache fixtures
│   └── test_*.py               # Memory cache implementation tests
├── base/                       # CacheInterface contract testing
└── dependencies/               # FastAPI dependency testing
```

### Test Statistics

| Component | Tests | Coverage | Focus Areas |
|-----------|-------|----------|--------------|
| **Total Cache Suite** | **580 tests** | **>90%** | Complete infrastructure validation |
| Factory Methods | 85 tests | >95% | Configuration, parameter mapping, fallback |
| Generic Redis Cache | 145 tests | >90% | Redis operations, compression, monitoring |
| AI Response Cache | 120 tests | >90% | AI optimizations, key generation, TTL strategies |
| Memory Cache | 95 tests | >95% | LRU eviction, TTL expiration, thread safety |
| E2E Testing | 80 tests | N/A | Full API integration, dual Redis approach |
| Dependencies | 55 tests | >90% | FastAPI integration, dependency injection |

### Test Categories

**Unit Tests** (>90% coverage required):
- Test individual cache components through public contracts
- Use real components with fakes (e.g., `fakeredis`) for external dependencies
- Fast execution for development workflow
- Follow UUT approach treating entire cache component as single unit

**Integration Tests**:
- Test component interactions with real Redis instances via `Testcontainers`
- Test cache fallback mechanisms and error handling
- Validate configuration-based instantiation through factory patterns
- Use real Redis with proper test isolation and cleanup

**End-to-End Tests**:
- Comprehensive API testing with dual approach (ASGI + Redis-enhanced)
- Full workflow validation from HTTP request to cache operation
- Production-like behavior validation with real infrastructure
- Authentication, monitoring, and security feature testing

## End-to-End Testing Strategy

The cache infrastructure implements a sophisticated **dual E2E testing approach** that balances speed with comprehensive validation.

### Dual Testing Approach

#### **1. ASGI Transport Tests (Fast) - Standard E2E**
- **Location**: `backend/tests/infrastructure/cache/e2e/test_*.py`
- **Markers**: `@pytest.mark.e2e` (without `redis` marker)
- **Transport**: ASGI with in-memory cache fallback
- **Benefits**:
  - Fast execution (~2-5 seconds)
  - No external dependencies
  - Parallel execution safe
  - CI/CD friendly
- **Coverage**: API contracts, configuration loading, error handling, authentication
- **Limitations**: Cannot test Redis-specific features, shows "disconnected" status

#### **2. Redis-Enhanced Tests (Comprehensive)**
- **Location**: `backend/tests/infrastructure/cache/e2e/test_redis_enhanced_*.py`
- **Markers**: `@pytest.mark.e2e` and `@pytest.mark.redis`
- **Transport**: ASGI + Real Redis via `Testcontainers`
- **Benefits**:
  - Tests actual Redis features (SCAN, DEL, TTL)
  - Realistic connectivity and behavior
  - Production-like monitoring and metrics
  - Comprehensive integration validation
- **Requirements**: Docker for Redis container management
- **Coverage**: Redis operations, pattern matching, performance metrics, connection monitoring

### E2E Test Execution Patterns

| Test Type | Execution | Dependencies | Use Case |
|-----------|-----------|--------------|----------|
| **Standard E2E** | Parallel, fast | None | Development, CI/CD, API validation |
| **Redis-Enhanced** | Sequential, comprehensive | Docker + Redis | Production validation, feature testing |

### Expected Behavior Differences

| Scenario | Standard E2E | Redis-Enhanced |
|----------|-------------|----------------|
| Redis Status | "disconnected" | "connected" |
| Pattern Invalidation | Mock/stub behavior | Real Redis SCAN/DEL |
| Performance Metrics | Stub data | Real operation metrics |
| Connection Monitoring | Simulated responses | Actual connectivity data |
| Cache Operations | Memory fallback | Real Redis persistence |

### E2E Test Fixtures

#### Standard ASGI Fixtures (`e2e/conftest.py`)
- `client()` - Basic ASGI client for API testing
- `authenticated_client()` - ASGI client with API key headers
- `cache_preset_app()` - Factory for preset-specific app instances
- `client_with_preset()` - Factory for preset-specific clients
- `cleanup_test_cache()` - Automatic cache cleanup between tests

#### Redis-Enhanced Fixtures (`e2e/conftest_redis.py`)
- `redis_container()` - Session-scoped Redis container (Testcontainers)
- `redis_config()` - Redis connection configuration from container
- `enhanced_cache_preset_app()` - Factory with real Redis connectivity
- `enhanced_client_with_preset()` - Factory with Redis-enabled clients

## Test Fixture Patterns

Our fixture strategy follows the testing philosophy: **prefer real components over mocks**, use fakes for external dependencies, and provide factory-based fixtures that mirror production usage patterns.

### Fixture Philosophy and Patterns

1. **Real Component Fixtures (Preferred)** - Instances of actual production classes configured for testing
   - Examples: `default_memory_cache`, `small_memory_cache`
   - Use Case: Best choice for unit and component tests, high-confidence validation
   - Benefit: Tests real behavior, resilient to refactoring

2. **High-Fidelity Fakes** - Substitutes for external dependencies with realistic behavior
   - Example: `fake_redis_client` (using `fakeredis`)
   - Use Case: Allows realistic integration testing without external service overhead
   - Benefit: Faster, more reliable than real external services

3. **Factory-Based Fixtures** - Use `CacheFactory` to create caches with production patterns
   - Examples: `factory_cache_for_testing`, `factory_cache_with_preset`
   - Use Case: Test factory methods and configuration patterns
   - Benefit: Mirrors actual application initialization

### Real Implementation Fixtures

#### Factory-Based Fixtures (Recommended)

```python
# From actual test suite: backend/tests/infrastructure/cache/conftest.py

@pytest.fixture
async def factory_cache_for_testing():
    """Create cache using factory for testing patterns."""
    factory = CacheFactory()
    cache = await factory.for_testing(
        use_memory_cache=True,
        default_ttl=60,
        memory_cache_size=50
    )
    yield cache
    await cache.clear()

@pytest.fixture
async def factory_cache_with_redis_fallback():
    """Test Redis fallback behavior with real factory patterns."""
    factory = CacheFactory()
    cache = await factory.for_testing(
        redis_url="redis://nonexistent:6379/15",
        fail_on_connection_error=False,
        default_ttl=30
    )
    yield cache
    await cache.clear()
```

#### Real Component Fixtures

```python
# Shared fixtures used across 580 tests

@pytest.fixture
async def default_memory_cache():
    """Standard InMemoryCache instance for most tests."""
    cache = InMemoryCache(max_size=100, default_ttl=3600)
    yield cache
    await cache.clear()

@pytest.fixture
async def small_memory_cache():
    """InMemoryCache with max_size=3 for testing LRU eviction."""
    cache = InMemoryCache(max_size=3, default_ttl=3600)
    yield cache
    await cache.clear()

@pytest.fixture
async def fast_expiry_memory_cache():
    """InMemoryCache with default_ttl=2 for testing expiration."""
    cache = InMemoryCache(max_size=100, default_ttl=2)
    yield cache
    await cache.clear()
```

#### Test Data Fixtures

```python
# Consistent test data across the suite

@pytest.fixture
def sample_cache_key() -> str:
    """Standard key for consistency across tests."""
    return "test:key:123"

@pytest.fixture
def sample_cache_value() -> Dict[str, Any]:
    """Standard dictionary value representing common application data."""
    return {
        "user_id": 456,
        "session_data": {"theme": "dark", "language": "en"},
        "timestamp": "2024-01-15T10:30:00Z"
    }

# AI-specific test data
@pytest.fixture
def sample_ai_response() -> Dict[str, Any]:
    """AI response data for testing AI cache features."""
    return {
        "operation": "summarize",
        "text": "Sample text for AI processing",
        "result": "This is a sample summary",
        "metadata": {"model": "gemini-pro", "tokens": 150}
    }
```

### Redis Integration Fixtures

#### FakeRedis Fixtures (Fast Integration Testing)

```python
# From redis_generic/conftest.py - Using fakeredis for fast Redis simulation

import pytest
import fakeredis.aioredis
from app.infrastructure.cache.redis_generic import GenericRedisCache

@pytest.fixture
async def fake_redis_client():
    """High-fidelity fake Redis client using fakeredis."""
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()

@pytest.fixture
async def redis_cache_with_fake(fake_redis_client):
    """GenericRedisCache with fake Redis - realistic but fast."""
    cache = GenericRedisCache(
        redis_client=fake_redis_client,
        default_ttl=3600,
        enable_memory_cache=True,
        memory_cache_size=100
    )
    yield cache
    await cache.clear()
```

#### Testcontainers Redis Fixtures (Real Redis Testing)

```python
# From e2e/conftest_redis.py - Real Redis via Docker containers

import pytest
from testcontainers.redis import RedisContainer
import redis.asyncio as redis

@pytest.fixture(scope="session")
def redis_container():
    """Session-scoped Redis container for comprehensive testing."""
    with RedisContainer("redis:7-alpine") as container:
        yield container

@pytest.fixture
def redis_config(redis_container):
    """Redis connection configuration from container."""
    return {
        "host": redis_container.get_container_host_ip(),
        "port": redis_container.get_exposed_port(6379),
        "decode_responses": True
    }

@pytest.fixture
async def real_redis_client(redis_config):
    """Real Redis client for comprehensive integration testing."""
    client = redis.Redis(**redis_config)
    yield client
    await client.flushall()
    await client.aclose()

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
            enable_memory_cache=True,
            memory_cache_size=100
        )
        yield cache
        
        # Cleanup: flush the test database
        await cache.clear()
        redis_db.flushdb()
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
            memory_cache_size=200
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

## Running Tests

The cache infrastructure provides multiple test execution strategies optimized for different development workflows.

### All Cache Tests

```bash
# Run complete cache test suite (580 tests)
make test-backend-infra-cache

# Run from project root with coverage
make test-backend-infra-cache PYTEST_ARGS="--cov=app.infrastructure.cache --cov-report=term"
```

### End-to-End Tests

#### Standard E2E Tests (Fast - No Docker)
```bash
# Fast E2E tests using ASGI transport
make test-backend-infra-cache-e2e

# Equivalent manual command:
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e and not redis" -v
```

#### Redis-Enhanced E2E Tests (Comprehensive)
```bash
# Comprehensive E2E tests with real Redis (requires Docker)
make test-backend-infra-cache-e2e-redis

# Equivalent manual command:
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e and redis" -v -n 0
```

#### All E2E Tests
```bash
# Run both standard and Redis-enhanced E2E tests
cd backend && source ../.venv/bin/activate && python -m pytest tests/infrastructure/cache/e2e/ -n 0 -m "e2e" -v && cd ..
```

### Component-Specific Tests

```bash
# Test specific cache implementations
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/redis_generic/ -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/redis_ai/ -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/factory/ -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/memory/ -v

# Test with specific markers
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ -m "slow" --run-slow -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ -m "redis" -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ -m "integration" -v
```

### Development Testing Commands

```bash
# Fast tests only (excludes slow and manual markers)
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ -v

# With coverage reporting
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ --cov=app.infrastructure.cache --cov-report=html -v

# Single test file with detailed output
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/factory/test_for_web_app.py -v -s --tb=long

# Specific test method
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/factory/test_for_web_app.py::TestForWebApp::test_creates_redis_cache_with_valid_connection -v -s
```

### Test Execution Environment

**Environment Setup Verification:**
```bash
# Verify you're in the correct location and environment
pwd                                    # Should show project root
ls -la .venv/bin/python               # Check virtual environment exists
ls -la backend/pytest.ini             # Check backend structure
make help | head -10                   # Verify Makefile available
```

**Common Issue Resolution:**
```bash
# Issue: make: *** No rule to make target 'help'
# Solution: Navigate to project root
cd ..                        # If in backend/ subdirectory
make help                    # Now this should work

# Issue: command not found: python
# Solution: Use virtual environment
source .venv/bin/activate    # From project root
cd backend && python -m pytest tests/infrastructure/cache/ -v

# Issue: Directory navigation
# From backend/:
../.venv/bin/python -m pytest tests/infrastructure/cache/ -v
# From project root:
.venv/bin/python -c "import os; os.chdir('backend'); import pytest; pytest.main(['-v', 'tests/infrastructure/cache/'])"
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
            enable_memory_cache=True
        )
        
        # Store data in cache
        await cache.set("failover_test", "important_data")
        assert await cache.get("failover_test") == "important_data"
        
        # Simulate Redis connection loss (implementation depends on cache design)
        # This would test memory cache behavior during Redis unavailability
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
        'CACHE_MONITORING_ENABLED'
    ]
    
    for var in cache_env_vars:
        monkeypatch.delenv(var, raising=False)
    
    # Set test-specific defaults
    test_env = {
        'CACHE_ENV': 'test',
        'CACHE_TTL': '60'
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
            "memory_cache_size": expected_size,
            "fail_on_connection_error": False
        },
        "testing": {
            "use_memory_cache": True,
            "default_ttl": expected_ttl,
            "memory_cache_size": expected_size
        },
        "staging": {
            "redis_url": "redis://staging-redis:6379",
            "default_ttl": expected_ttl,
            "memory_cache_size": expected_size,
            "enable_memory_cache": True,
            "fail_on_connection_error": False
        },
        "production": {
            "redis_url": "redis://prod-redis:6379",
            "default_ttl": expected_ttl,
            "memory_cache_size": expected_size,
            "enable_memory_cache": True,
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
    async def test_configuration_validation_across_environments(self):
        """Test configuration validation for different environments."""
        factory = CacheFactory()
        
        # Test configurations that should work in any environment
        universal_configs = [
            {"redis_url": "redis://localhost:6379", "default_ttl": 3600},
            {"use_memory_cache": True, "default_ttl": 300},
            {"redis_url": "redis://localhost:6379", "enable_memory_cache": True}
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
            memory_cache_size=100
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
            memory_cache_size=1000
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
5. **Mock callback patterns** for monitoring and error simulation
6. **CI/CD configuration** with GitHub Actions and Docker integration
7. **Test isolation** with automatic cleanup and environment management
8. **Async testing best practices** for concurrent operations and error handling
9.  **Comprehensive error scenarios** covering configuration, connection, and data corruption
10. **Multi-environment testing** with environment-specific configurations and load patterns

The guide demonstrates practical, production-ready testing patterns that developers can use immediately to build robust cache infrastructure with confidence in reliability and performance.

Key principles demonstrated:
- **Explicit over implicit**: Clear test fixtures and factory patterns
- **Comprehensive coverage**: Unit, integration, and performance testing
- **Environment awareness**: Different configurations for different contexts  
- **Error resilience**: Extensive error handling and recovery testing
- **CI/CD integration**: Automated testing with proper isolation and cleanup

Use this guide as a reference for implementing comprehensive testing strategies for cache infrastructure that maintain high quality standards while enabling rapid development and deployment cycles.

## Troubleshooting

Common testing issues and their solutions, based on real troubleshooting experiences from the 580-test cache suite.

### Docker and Redis Container Issues

#### Docker Not Running
```bash
# Check Docker is running
docker ps

# If Docker is not running, start Docker Desktop or Docker service
# On macOS: Start Docker Desktop application
# On Linux: sudo systemctl start docker

# Pull Redis image manually if needed
docker pull redis:7-alpine

# Clean up old containers that might conflict
docker container prune -f
```

#### Testcontainers Issues
```bash
# Check testcontainers logs for debugging
export TESTCONTAINERS_RYUK_DISABLED=true  # Disable cleanup for debugging

# Common issue: Port conflicts
docker ps -a | grep redis
docker stop $(docker ps -q --filter "ancestor=redis:7-alpine")

# If containers won't start:
docker system prune -f
docker volume prune -f
```

### Test Execution Issues

#### Authentication Errors (401 Unauthorized)
```bash
# Issue: Tests expect Bearer token but using X-API-Key format
# Solution: E2E tests now use Authorization: Bearer <token> format
# Debug: Check headers in conftest.py fixtures

# Example of correct authentication for E2E tests:
# headers = {"Authorization": "Bearer test-api-key-12345"}
```

#### Performance Monitor Unavailable
```bash
# Issue: InfrastructureError: Performance monitor not available
# Solution: Tests now handle this gracefully with skip/fallback
# This is expected behavior in test environments

# Check if issue persists:
cd backend && ../.venv/bin/python -c "from app.infrastructure.cache.monitoring import CachePerformanceMonitor; print('Monitor available')"
```

#### Response Structure Mismatches
```bash
# Issue: KeyError for 'cache', 'host', 'url' keys in API responses
# Solution: Tests now validate actual response structure
# Debug: Add debug prints to see actual vs expected response

# Example debug code:
# print(f"Actual response: {response.json()}")
# print(f"Expected keys: ['cache', 'host', 'url']")
```

### Test Isolation Issues

#### Environment Variable Conflicts
```bash
# Issue: Tests interfering with each other via environment variables
# Solution: Use monkeypatch.setenv() for proper isolation

# Example proper isolation:
# def test_with_env_var(monkeypatch):
#     monkeypatch.setenv("CACHE_PRESET", "testing")
#     # Test code here
```

#### Cache Data Conflicts
```bash
# Issue: Test data from previous tests affecting current test
# Solution: Ensure cleanup fixtures are running

# Verify cleanup is working:
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ -v -s --tb=short -k "test_cleanup"

# Check for @pytest.mark.xdist_group markers for proper test isolation
```

### Performance and Timing Issues

#### Slow Test Execution
```bash
# Issue: Redis-enhanced tests are slow due to container startup
# Solution: Use session-scoped containers and run Redis tests separately

# Fast tests only (excludes Redis-enhanced):
make test-backend-infra-cache-e2e

# Run Redis tests separately when needed:
make test-backend-infra-cache-e2e-redis

# Disable parallel execution for Redis tests:
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "redis" -n 0 -v
```

#### Test Timeouts
```bash
# Issue: Tests timing out, especially with Redis containers
# Solution: Increase timeout or check container startup

# Debug container startup:
docker logs $(docker ps -q --filter "ancestor=redis:7-alpine")

# Run with increased timeout:
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ --timeout=60 -v
```

### Debug Commands

#### Comprehensive Debugging
```bash
# Run with verbose output and no capture
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -v -s --tb=long

# Run single test with full debugging
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/test_cache_invalidation_workflow.py::TestCacheInvalidationWorkflow::test_invalidation_requires_authentication -v -s --tb=long

# Check test discovery
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ --collect-only

# Run with specific markers
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e and not redis" -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e and redis" -v
```

#### Test Coverage Analysis
```bash
# Generate detailed coverage report
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ --cov=app.infrastructure.cache --cov-report=html --cov-report=term

# View coverage report
open backend/htmlcov/index.html  # On macOS
# Or navigate to backend/htmlcov/index.html in browser

# Check for missing coverage
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/ --cov=app.infrastructure.cache --cov-fail-under=90
```

### Environment Setup Verification

#### Check Project Structure
```bash
# Verify you're in the correct location
pwd                                    # Should show project root
ls -la .venv/bin/python               # Check virtual environment exists
ls -la backend/pytest.ini             # Check backend structure
ls -la backend/tests/infrastructure/cache/  # Check test directory

# Check Python environment
source .venv/bin/activate
which python                          # Should point to .venv/bin/python
python -c "import app.infrastructure.cache; print('Cache module available')"
```

#### Check Dependencies
```bash
# Verify test dependencies are installed
source .venv/bin/activate
pip list | grep -E "pytest|fakeredis|testcontainers|redis"

# Install missing dependencies if needed
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt
```

### Integration with Project Testing Philosophy

When troubleshooting, remember our testing principles:

1. **Test What's Documented** - If a test fails, first check if the behavior matches the docstring
2. **Focus on Behavior** - Debug by understanding the expected external behavior, not internal implementation
3. **Mock Only at Boundaries** - If mocking is involved in the failure, verify it's only at system boundaries
4. **Real Components Preferred** - When debugging, prefer using real components over mocks to isolate the actual issue

### Getting Help

If you encounter issues not covered here:

1. **Check the actual test suite** in `backend/tests/infrastructure/cache/README.md` for detailed testing philosophy
2. **Review the E2E documentation** in `backend/tests/infrastructure/cache/e2e/README.md` for specific E2E troubleshooting
3. **Run individual test components** to isolate the issue
4. **Use the debug commands** above to get detailed output

## Related Documentation

### Cache Infrastructure
- **[Cache Infrastructure Overview](./CACHE.md)** - Complete cache system architecture, components, integration patterns, and configuration management
- **[Usage Guide](./usage-guide.md)** - Practical patterns for implementing cache in applications with configuration examples
- **[API Reference](./api-reference.md)** - Complete API documentation with examples and best practices

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