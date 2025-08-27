---
sidebar_label: conftest
---

# Test fixtures for AIResponseCache unit tests.

  file_path: `backend/tests.old/unit/infrastructure/cache/take3/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_ai.pyi file.

## Fixture Categories

- Basic test data fixtures (sample texts, operations, responses)
- Mock dependency fixtures (parameter mapper, key generator, monitor)
- Configuration fixtures (valid/invalid parameter sets)
- Error scenario fixtures (exception mocks, connection failures)
