---
sidebar_label: conftest
---

# Test fixtures for config module unit tests.

  file_path: `backend/tests/infrastructure/cache/config/conftest.py`

This module provides reusable fixtures specific to cache configuration testing.
All fixtures provide 'happy path' behavior based on public contracts from
backend/contracts/ directory.

## Fixtures

- mock_validation_result: Mock ValidationResult for configuration validation testing

Note: Exception fixtures (ValidationError, ConfigurationError) are available
in the shared cache conftest.py file.
