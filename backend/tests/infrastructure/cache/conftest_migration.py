"""
Configuration and fixtures for cache migration tests.

Provides pytest-redis fixtures and other test infrastructure needed
for comprehensive migration testing.
"""
import pytest
import pytest_redis

# Configure pytest-redis for Docker-based Redis instances
pytest_plugins = ['pytest_redis']


@pytest.fixture(scope='session')
def redis_proc():
    """Create a Redis process for testing."""
    # This will start a Redis server in a Docker container
    # The pytest-redis plugin handles the lifecycle
    return pytest_redis.factories.redis_proc(
        port=None,  # Use random port
        timeout=60,
        redis_exec='redis-server'
    )


@pytest.fixture(scope='session')
def redis_db(redis_proc):
    """Create Redis database connection."""
    return pytest_redis.factories.redisdb(
        'redis_proc',
        db=0
    )
