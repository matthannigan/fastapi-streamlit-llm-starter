---
sidebar_label: test_memory_lru_eviction
---

# Unit tests for InMemoryCache LRU eviction and memory management behavior.

  file_path: `backend/tests/infrastructure/cache/memory/test_memory_lru_eviction.py`

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

## Coverage Focus

- LRU (Least Recently Used) eviction policy implementation
- Memory management and size limit enforcement
- Access order tracking and eviction decisions
- Cache size management and statistics

## External Dependencies

All external dependencies are mocked using fixtures from conftest.py following
the documented public contracts to ensure accurate behavior simulation.
