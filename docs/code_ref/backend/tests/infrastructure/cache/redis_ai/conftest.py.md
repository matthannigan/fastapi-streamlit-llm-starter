---
sidebar_label: conftest
---

# Test fixtures for AIResponseCache unit tests.

  file_path: `backend/tests/infrastructure/cache/redis_ai/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_ai.pyi file.

Fixture Categories:
    - Basic test data fixtures (sample texts, operations, responses)
    - Mock dependency fixtures (parameter mapper, key generator, monitor)
    - Configuration fixtures (valid/invalid parameter sets)
    - Error scenario fixtures (exception mocks, connection failures)

## valid_ai_params()

```python
def valid_ai_params():
```

Valid AIResponseCache initialization parameters.

Provides a complete set of valid parameters that should pass
validation and allow successful cache initialization.

## invalid_ai_params()

```python
def invalid_ai_params():
```

Invalid AIResponseCache initialization parameters for testing validation errors.
