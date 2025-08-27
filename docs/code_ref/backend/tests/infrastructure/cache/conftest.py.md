---
sidebar_label: conftest
---

# Test fixtures shared across cache infrastructure unit tests.

  file_path: `backend/tests/infrastructure/cache/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
that are commonly used across multiple cache module test suites.

## Fixture Categories

- Mock dependency fixtures (settings, cache factory, cache interface, performance monitor, memory cache)
- Custom exception fixtures
- Basic test data fixtures (keys, values, TTL values, text samples)
- AI-specific data fixtures (responses, operations, options)
- Statistics fixtures (sample performance data)

## Design Philosophy

- Fixtures represent 'happy path' successful behavior only
- Error scenarios are configured within individual test functions
- All fixtures use public contracts from backend/contracts/ directory
- Stateful mocks maintain internal state for realistic behavior
