# Redis Testing Guide

This guide explains how to work with Redis tests in the cache infrastructure test suite.

## Setup

### Prerequisites
- Redis server installed (`brew install redis` on macOS)
- pytest-redis package installed (`pip install pytest-redis`)

### Configuration
Redis test fixtures are configured in `conftest.py`:
- **redis_proc**: Manages the Redis server process lifecycle
- **redis_db**: Provides a Redis client connection
- **cleanup_redis**: Automatically cleans up after each test (flushes the database)

## Running Tests

### Using the Makefile (Recommended)
```bash
# Run all Redis tests sequentially
make -f Makefile.redis test-redis

# Run non-Redis tests in parallel
make -f Makefile.redis test-non-redis

# Clean environment and run Redis tests
make -f Makefile.redis test-redis-clean

# Run all tests optimally (non-Redis parallel, Redis sequential)
make -f Makefile.redis test-all
```

### Direct pytest commands

#### Run all Redis tests without parallelization (recommended)
```bash
pytest tests/ -m "redis" -n 0 -v
```

#### Run non-Redis tests in parallel
```bash
pytest tests/ -m "not redis" -n auto -v
```

#### Run specific test class
```bash
pytest tests/infrastructure/cache/test_migration.py::TestMigrationWithRedis -n 0 -v
```

#### Run single test method
```bash
pytest tests/infrastructure/cache/test_migration.py::TestMigrationWithRedis::test_migration_with_large_dataset -xvs
```

## Troubleshooting

### Port Conflicts
If you encounter "Address already in use" errors:

1. **Use the cleanup script**:
   ```bash
   ./scripts/clean_redis_test_env.sh
   ```

2. **Disable parallel execution**:
   ```bash
   pytest -n 0  # Runs tests sequentially
   ```

3. **Check for stale processes**:
   ```bash
   pgrep -f redis-server
   pkill -f "redis-server.*pytest"
   ```

### Test Isolation
The `cleanup_redis` fixture automatically:
- Flushes the Redis database after each test
- Only runs for tests that actually use Redis fixtures
- Handles cleanup errors gracefully

### Parallel Execution Issues
pytest-xdist may cause port conflicts when running tests in parallel. Each worker tries to start its own Redis instance, which can lead to conflicts. Solutions:
- Use `-n 0` to disable parallelization for Redis tests
- Use `-n 2` or `-n 3` for limited parallelization
- Run Redis tests separately from other tests

## Test Markers

Tests that require Redis should be marked appropriately:
```python
@pytest.mark.redis
class TestMigrationWithRedis:
    def test_something(self, redis_db):
        # Test implementation
```

This allows skipping Redis tests when pytest-redis is not available.

## Best Practices

1. **Always use fixtures**: Don't manually start Redis servers in tests
2. **Clean up data**: The cleanup fixture handles this automatically
3. **Use meaningful test data**: Make tests self-documenting
4. **Test error cases**: Include tests for connection failures and data corruption
5. **Avoid hardcoded ports**: Let pytest-redis assign random ports

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| "pytest_redis not installed" | Install with `pip install pytest-redis` |
| Port already in use | Run cleanup script or use `-n 0` |
| Tests hang | Check for deadlocks in Redis operations |
| Cleanup warnings | Normal if Redis connection closes early |
| Slow test startup | Redis server initialization time, use test fixtures efficiently |

## Additional Resources

- [pytest-redis documentation](https://pypi.org/project/pytest-redis/)
- [Redis testing best practices](https://redis.io/docs/manual/patterns/testing/)
- Project-specific cache documentation: `backend/app/infrastructure/cache/README.md`
