---
sidebar_label: conftest
---

# Test fixtures for InMemoryCache unit tests.

  file_path: `backend/tests/infrastructure/cache/memory/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the memory.pyi file.

## Fixture Categories

- Basic test data fixtures (sample keys, values, TTL values)
- InMemoryCache instance fixtures (various configurations)
- Mock dependency fixtures (if needed for external integrations)
- Test scenario fixtures (cache state setups for specific tests)

## Design Philosophy

- Fixtures represent 'happy path' successful behavior only
- Error scenarios are configured within individual test functions
- All fixtures use public contracts from backend/contracts/ directory
- Stateful mocks maintain internal state for realistic behavior
