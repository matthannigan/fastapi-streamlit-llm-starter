---
sidebar_label: conftest
---

# Test fixtures for GenericRedisCache unit tests.

  file_path: `backend/tests/infrastructure/cache/redis_generic/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_generic.pyi file.

## Fixture Categories

- Basic test data fixtures (keys, values, Redis URLs, TTL values)
- Mock dependency fixtures (InMemoryCache, CachePerformanceMonitor, SecurityConfig)
- Configuration fixtures (various GenericRedisCache configurations)
- Redis operation fixtures (connection states, callback systems)

## Design Philosophy

- Fixtures represent 'happy path' successful behavior only
- Error scenarios are configured within individual test functions
- All fixtures use public contracts from backend/contracts/ directory
- Stateful mocks maintain internal state for realistic behavior
- Mock dependencies are spec'd against real classes for accuracy
