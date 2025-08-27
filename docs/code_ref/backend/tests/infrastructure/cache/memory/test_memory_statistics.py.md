---
sidebar_label: test_memory_statistics
---

# Unit tests for InMemoryCache statistics and monitoring capabilities.

  file_path: `backend/tests/infrastructure/cache/memory/test_memory_statistics.py`

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

## Coverage Focus

- get_stats() method providing comprehensive cache metrics
- get_keys() and get_active_keys() methods for cache introspection
- size() method for current cache entry count
- get_ttl() method for remaining TTL information

## External Dependencies

All external dependencies are mocked using fixtures from conftest.py following
the documented public contracts to ensure accurate behavior simulation.
