---
sidebar_label: conftest
---

# Test fixtures for factory module unit tests.

  file_path: `backend/tests/infrastructure/cache/factory/conftest.py`

This module provides reusable fixtures specific to cache factory testing.
All fixtures provide 'happy path' behavior based on public contracts from
backend/contracts/ directory.

## Fixtures

- mock_generic_redis_cache: Mock GenericRedisCache for testing factory creation
- mock_ai_response_cache: Mock AIResponseCache for testing factory creation

Note: Exception fixtures and other common mocks are available in the shared
cache conftest.py file.
