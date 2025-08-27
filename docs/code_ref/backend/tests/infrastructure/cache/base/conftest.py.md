---
sidebar_label: conftest
---

# Test fixtures for CacheInterface unit tests.

  file_path: `backend/tests/infrastructure/cache/base/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Since CacheInterface is an abstract base class with no external
dependencies (only standard library imports), there are no dependency mocks
required for testing the interface itself.

The fixtures here primarily provide test data and utilities for testing
concrete implementations of the CacheInterface contract.

## Fixture Categories

- Interface compliance test utilities
- Mock implementations for polymorphism testing

## Design Philosophy

- CacheInterface has no external dependencies requiring mocking
- Fixtures support testing interface compliance and polymorphic behavior
- Test data fixtures are minimal since this is an abstract interface
- Focus on testing that concrete implementations honor the contract
