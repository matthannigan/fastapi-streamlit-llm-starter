---
sidebar_label: __init__
---

# Cache Infrastructure E2E Testing Suite

  file_path: `backend/tests/infrastructure/cache/e2e/__init__.py`

This package provides comprehensive end-to-end testing for the cache infrastructure
service using a dual testing approach for optimal coverage and performance.

## Quick Start

### Fast Development Testing (ASGI-only)
```bash
make test-backend-infra-cache-e2e
```
- Uses ASGI transport with in-memory cache fallback
- Fast execution, no external dependencies
- Ideal for development workflow and CI/CD

### Comprehensive Production Testing (Redis-enhanced)  
```bash
make test-backend-infra-cache-e2e-redis
```
- Uses real Redis via Testcontainers + ASGI transport
- Comprehensive validation of Redis-specific features
- Requires Docker for Redis container management

## Test Architecture

### Standard Tests (5 classes, 17 methods)
- **TestCacheInvalidationWorkflow**: Authentication, security, pattern validation
- **TestCacheMonitoringWorkflow**: Metrics, performance monitoring, consistency
- **TestPresetDrivenBehavior**: Configuration presets, status validation

### Redis-Enhanced Tests (2 classes, 12 methods)
- **TestRedisEnhancedPresetBehavior**: Real Redis connectivity, pattern operations
- **TestRedisEnhancedMonitoringWorkflow**: Performance monitoring, load testing

## Test Fixtures

### Standard Fixtures (`conftest.py`)
- `client()`, `authenticated_client()`: Basic and authenticated ASGI clients
- `cache_preset_app()`, `client_with_preset()`: Preset-specific app/client factories
- `cleanup_test_cache()`: Automatic test isolation and cleanup

### Redis Fixtures (`conftest_redis.py`)  
- `redis_container()`: Session-scoped Testcontainers Redis instance
- `enhanced_cache_preset_app()`, `enhanced_client_with_preset()`: Redis-enabled factories

## Developer Guidelines

### When to Add Standard Tests
- API contract validation and error handling
- Configuration loading and preset behavior
- Authentication and authorization workflows
- Rapid development feedback scenarios

### When to Add Redis-Enhanced Tests
- Production deployment validation
- Redis-specific feature testing (TTL, pattern matching, SCAN/DEL)
- Performance monitoring with real metrics
- Comprehensive integration validation

### Test Naming Conventions
- **Standard**: `test_*.py` (no Redis marker)
- **Redis-Enhanced**: `test_redis_enhanced_*.py` (with `@pytest.mark.redis`)
- **Classes**: `Test{Workflow}` (e.g., `TestCacheInvalidationWorkflow`)
- **Methods**: `test_{action}_{condition}` (e.g., `test_invalidation_requires_authentication`)

## Business Impact Testing

All tests include comprehensive business impact documentation:
- **Test Purpose**: What specific behavior is being validated
- **Business Impact**: Why this test matters for production systems
- **Enhanced Testing**: Additional benefits from Redis-enhanced approach

## Integration with Project Standards

Follows the project's behavior-driven testing philosophy:
1. **Test What's Documented**: Validates API contracts from `backend/contracts/`
2. **Focus on Behavior**: Tests external observable behavior, not implementation
3. **Mock Only at Boundaries**: Redis-enhanced tests eliminate Redis mocking
4. **Maintainable Tests**: Clear structure enables easy extension and debugging

## Troubleshooting

### Common Issues
- **Docker not available**: Redis-enhanced tests require Docker daemon
- **Port conflicts**: Testcontainers handles port allocation automatically  
- **Test isolation**: Use proper `@pytest.mark.xdist_group` markers
- **Performance**: Redis tests are slower due to container overhead

See `README.md` for comprehensive troubleshooting guide.
