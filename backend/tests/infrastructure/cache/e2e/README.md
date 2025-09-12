# Cache Infrastructure E2E Testing Strategy

This directory provides comprehensive end-to-end testing for the cache infrastructure service with both ASGI transport and real Redis connectivity options.

## Test Architecture

### Dual Testing Approach

**1. ASGI Transport Tests (Fast)**
- Located in: `test_*.py` files (without `redis` marker)  
- Uses: ASGI transport with in-memory cache fallback
- Benefits: Fast execution, no external dependencies, parallel execution
- Limitations: Cannot test Redis-specific features, shows "disconnected" status

**2. Redis-Enhanced Tests (Comprehensive)**
- Located in: `test_redis_enhanced_*.py` files (with `redis` marker)
- Uses: Real Redis via Testcontainers + ASGI transport
- Benefits: Tests actual Redis features, realistic connectivity, production-like behavior
- Requirements: Docker for Redis container management

## Running Tests

### Standard E2E Tests (Fast)
```bash
# Run from project root
make test-backend-infra-cache-e2e

# Runs tests marked with "e2e and not redis"
# Uses ASGI transport with memory cache fallback
# Fast execution, no Docker required
```

### Redis-Enhanced E2E Tests (Comprehensive)
```bash
# Run from project root  
make test-backend-infra-cache-e2e-redis

# Runs tests marked with "e2e and redis"
# Uses Testcontainers Redis + ASGI transport
# Requires Docker for Redis container
```

### All E2E Tests
```bash
# Run both standard and Redis-enhanced tests
cd backend
../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e" -v
```

## Test Fixtures

### Standard ASGI Fixtures (`conftest.py`)
- `client()` - Basic ASGI client
- `authenticated_client()` - ASGI client with API key headers
- `cache_preset_app()` - Factory for preset-specific app instances
- `client_with_preset()` - Factory for preset-specific clients
- `cleanup_test_cache()` - Automatic cache cleanup

### Redis-Enhanced Fixtures (`conftest_redis.py`)
- `redis_container()` - Session-scoped Redis container (Testcontainers)
- `redis_config()` - Redis connection configuration
- `enhanced_cache_preset_app()` - Factory with real Redis connectivity
- `enhanced_client_with_preset()` - Factory with Redis-enabled clients

## Test Categories

### Preset Behavior Testing
- **Standard**: Tests preset configuration loading and basic status
- **Redis-Enhanced**: Tests actual Redis connectivity status and real cache operations

### Cache Operations Testing  
- **Standard**: Tests API contracts and error handling
- **Redis-Enhanced**: Tests Redis SCAN/DEL operations, TTL behavior, pattern matching

### Monitoring & Metrics Testing
- **Standard**: Tests endpoint availability and response structure
- **Redis-Enhanced**: Tests real performance metrics, connection monitoring, load testing

### Authentication & Security
- **Standard**: Tests API key authentication and authorization
- **Redis-Enhanced**: Tests Redis AUTH, security configurations, TLS support

## Test Execution Patterns

### Parallel vs Sequential
- **Standard E2E**: Can run in parallel (uses separate ASGI instances)
- **Redis-Enhanced**: Runs sequentially (`redis` marker prevents parallel execution)
- **Cleanup**: Both approaches use automatic cleanup fixtures

### Environment Isolation
- **Monkeypatch**: Proper environment variable isolation using `monkeypatch.setenv()`
- **Test Groups**: Uses `@pytest.mark.xdist_group` for test worker isolation
- **Container Scope**: Redis containers are session-scoped for efficiency

## Test Scenarios

### Expected Behavior Differences

| Scenario | Standard E2E | Redis-Enhanced |
|----------|-------------|----------------|
| Redis Status | "disconnected" | "connected" |
| Pattern Invalidation | Mock/stub behavior | Real Redis SCAN/DEL |
| Performance Metrics | Stub data | Real operation metrics |
| Connection Monitoring | Simulated responses | Actual connectivity data |

### Preset Testing

| Preset | Standard Expected | Redis-Enhanced Expected |
|--------|------------------|------------------------|
| `ai-production` | disconnected, active | connected, active |
| `development` | disconnected, active | connected, active |
| `simple` | disconnected, active | connected, active |
| `disabled` | disconnected, active | connected, active* |

*Note: Even `disabled` preset shows "connected" with testcontainers since Redis is available

## Business Impact

### Standard E2E Tests
- **Fast Feedback**: Quick validation of API contracts and configuration
- **CI/CD Friendly**: No external dependencies, reliable in CI environments
- **Development Workflow**: Rapid iteration during development

### Redis-Enhanced Tests
- **Production Confidence**: Validates actual Redis integration and behavior
- **Feature Coverage**: Tests Redis-specific features (TTL, pattern matching, monitoring)
- **Operational Readiness**: Ensures monitoring and metrics accuracy

## Maintenance Guidelines

### When to Use Standard Tests
- API contract validation
- Configuration loading testing  
- Error handling verification
- Rapid development feedback

### When to Use Redis-Enhanced Tests
- Production deployment validation
- Redis-specific feature testing
- Performance monitoring validation
- Comprehensive integration verification

### Adding New Tests
1. **Start with Standard**: Create ASGI-based test first for fast feedback
2. **Add Redis-Enhanced**: Create Redis version for comprehensive validation  
3. **Use Appropriate Markers**: `@pytest.mark.e2e` and `@pytest.mark.redis` as needed
4. **Document Benefits**: Explain what additional coverage Redis testing provides

## Troubleshooting

### Docker Issues
```bash
# Check Docker is running
docker ps

# Pull Redis image manually if needed
docker pull redis:7-alpine

# Clean up old containers
docker container prune -f

# Check testcontainers logs
export TESTCONTAINERS_RYUK_DISABLED=true  # Disable cleanup for debugging
```

### Common Test Failures

#### Authentication Errors (401 Unauthorized)
```bash
# Issue: Tests expect Bearer token but using X-API-Key format
# Solution: Tests now use Authorization: Bearer <token> format
# Debug: Check headers in conftest.py fixtures
```

#### Performance Monitor Unavailable
```bash
# Issue: InfrastructureError: Performance monitor not available
# Solution: Tests now handle this gracefully with skip/fallback
# Debug: Monitor components may not initialize in test environment
```

#### Response Structure Mismatches
```bash
# Issue: KeyError for 'cache', 'host', 'url' keys
# Solution: Tests now validate actual response structure
# Debug: Compare expected vs actual response with debug prints
```

#### Docker Container Conflicts
```bash
# Issue: Port already in use or container startup failures
# Solution: Testcontainers automatically handles port allocation
# Debug: Check for conflicting containers or services
docker ps -a | grep redis
```

### Test Isolation Issues
- Ensure `@pytest.mark.xdist_group` markers are properly set
- Verify cleanup fixtures are running (`cleanup_test_cache`)
- Check environment variable isolation (use `monkeypatch.setenv()`)
- Validate test data patterns don't conflict between tests

### Performance Issues
- Redis-enhanced tests are slower due to container startup (~5-10s)
- Session-scoped containers minimize overhead
- Consider running Redis tests separately in CI pipelines
- Use `-n 0` to disable parallel execution for Redis tests

### Debug Commands
```bash
# Run with verbose output and no capture
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -v -s --tb=long

# Run single test with full debugging
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/test_cache_invalidation_workflow.py::TestCacheInvalidationWorkflow::test_invalidation_requires_authentication -v -s --tb=long

# Check test discovery
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ --collect-only

# Run with markers
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e and not redis" -v
cd backend && ../.venv/bin/python -m pytest tests/infrastructure/cache/e2e/ -m "e2e and redis" -v
```

## Integration with Project Testing Philosophy

This dual testing approach aligns with the project's behavior-driven testing principles:

1. **Test What's Documented**: Both approaches test the same API contracts
2. **Focus on Behavior**: Standard tests focus on API behavior, Redis-enhanced tests validate production behavior  
3. **Mock Only at Boundaries**: Redis-enhanced tests eliminate Redis mocking by using real instances
4. **Maintainable Tests**: Clear separation allows choosing appropriate test level for each scenario