---
sidebar_label: test_memory_core_operations
---

# Unit tests for InMemoryCache core operations (get, set, delete, exists).

  file_path: `backend/tests/infrastructure/cache/memory/test_memory_core_operations.py`

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

## Coverage Focus

- Core CacheInterface implementation (get, set, delete, exists)
- TTL handling and expiration behavior
- Value storage and retrieval accuracy
- Key existence checking and validation

## External Dependencies

All external dependencies are mocked using fixtures from conftest.py following
the documented public contracts to ensure accurate behavior simulation.
