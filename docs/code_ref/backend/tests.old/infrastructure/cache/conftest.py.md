---
sidebar_label: conftest
---

# Shared test configuration for cache infrastructure tests.

  file_path: `backend/tests.old/infrastructure/cache/conftest.py`

Provides optional Redis integration support. If `pytest_redis` is not
installed, tests marked with `@pytest.mark.redis` will be skipped gracefully.

## pytest_collection_modifyitems()

```python
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
```

Modify test collection to handle Redis tests specially.

- Skip Redis tests if pytest_redis is not installed
- Mark Redis tests to run in the same xdist group (sequential execution)
