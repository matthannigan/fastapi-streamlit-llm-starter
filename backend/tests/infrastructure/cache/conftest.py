"""Shared test configuration for cache infrastructure tests.

Provides optional Redis integration support. If `pytest_redis` is not
installed, tests marked with `@pytest.mark.redis` will be skipped gracefully.
"""

from __future__ import annotations

import pytest

try:
    import pytest_redis  # type: ignore  # noqa: F401
    HAS_PYTEST_REDIS = True
except Exception:  # pragma: no cover
    HAS_PYTEST_REDIS = False


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    if HAS_PYTEST_REDIS:
        return
    skip_redis = pytest.mark.skip(reason="pytest_redis not installed; skipping Redis integration tests")
    for item in items:
        if item.get_closest_marker("redis"):
            item.add_marker(skip_redis)


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


