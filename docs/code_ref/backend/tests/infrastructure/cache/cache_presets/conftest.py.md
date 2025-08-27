---
sidebar_label: conftest
---

# Test fixtures for cache presets unit tests.

  file_path: `backend/tests/infrastructure/cache/cache_presets/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the cache_presets.pyi file.

## Fixture Categories

- Basic test data fixtures (environment names, preset configurations)
- Mock dependency fixtures (ValidationResult, CacheValidator)
- Configuration test data (preset definitions, strategy configurations)
- Environment detection fixtures (environment variables and contexts)

## Design Philosophy

- Fixtures represent 'happy path' successful behavior only
- Error scenarios are configured within individual test functions
- All fixtures use public contracts from backend/contracts/ directory
- Stateless mocks for validation utilities (no state management needed)
- Mock dependencies are spec'd against real classes for accuracy
