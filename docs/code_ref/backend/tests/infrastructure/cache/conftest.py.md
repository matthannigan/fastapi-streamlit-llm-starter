---
sidebar_label: conftest
---

# Shared test configuration for cache infrastructure tests.

  file_path: `backend/tests/infrastructure/cache/conftest.py`

Provides optional Redis integration support. If `pytest_redis` is not
installed, tests marked with `@pytest.mark.redis` will be skipped gracefully.
