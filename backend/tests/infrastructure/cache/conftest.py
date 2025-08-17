"""Shared test configuration for cache infrastructure tests.

Provides optional Redis integration support. If `pytest_redis` is not
installed, tests marked with `@pytest.mark.redis` will be skipped gracefully.
"""

from __future__ import annotations

import os
import pytest

try:
    import pytest_redis  # type: ignore  # noqa: F401
    HAS_PYTEST_REDIS = True
except Exception:  # pragma: no cover
    HAS_PYTEST_REDIS = False


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    """Modify test collection to handle Redis tests specially.
    
    - Skip Redis tests if pytest_redis is not installed
    - Mark Redis tests to run in the same xdist group (sequential execution)
    """
    for item in items:
        # Check if this is a Redis test (by marker or fixture usage)
        has_redis_marker = item.get_closest_marker("redis")
        uses_redis_fixture = any(fixture in item.fixturenames for fixture in ["redis_db", "redis_proc"])
        
        if has_redis_marker or uses_redis_fixture:
            if not HAS_PYTEST_REDIS:
                # Skip if pytest_redis not installed
                skip_redis = pytest.mark.skip(reason="pytest_redis not installed; skipping Redis integration tests")
                item.add_marker(skip_redis)
            else:
                # Mark for sequential execution in xdist
                # All tests with the same xdist_group run in the same worker
                item.add_marker(pytest.mark.xdist_group(name="redis"))
                # Also ensure it has the redis marker for filtering
                if not has_redis_marker:
                    item.add_marker(pytest.mark.redis)


if HAS_PYTEST_REDIS:
    # Only import and expose factories/fixtures when plugin is available
    import pytest_redis

    # Define fixtures via factory assignment (recommended pattern)
    redis_proc = pytest_redis.factories.redis_proc(port=None, timeout=60)
    # Newer pytest-redis uses `dbnum` instead of `db`
    try:
        redis_db = pytest_redis.factories.redisdb("redis_proc", dbnum=0)
    except TypeError:  # fallback for older versions
        redis_db = pytest_redis.factories.redisdb("redis_proc", db=0)

    @pytest.fixture(autouse=True)
    def cleanup_redis(request):
        """Automatically clean up Redis after each test that uses it.
        
        This fixture ensures test isolation by:
        - Flushing the database after each test
        - Only running for tests that actually use Redis fixtures
        
        Note: When running tests in parallel with pytest-xdist, each worker
        gets its own Redis instance on a different port. However, port conflicts
        may still occur if too many workers try to start simultaneously.
        Use '-n 0' to disable parallel execution if you encounter port conflicts.
        """
        # Only run cleanup if the test uses redis fixtures
        if "redis_db" in request.fixturenames or "redis_proc" in request.fixturenames:
            # Let the test run
            yield
            # Clean up after test completes
            if "redis_db" in request.fixturenames:
                try:
                    redis_db = request.getfixturevalue("redis_db")
                    redis_db.flushdb()
                except Exception as e:
                    # Log but don't fail on cleanup errors
                    # Common reasons: connection already closed, Redis stopped
                    if "redis_db" in str(request.node):
                        print(f"\nWarning: Redis cleanup failed for {request.node.name}: {e}")
        else:
            # For tests that don't use Redis, just pass through
            yield


