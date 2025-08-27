---
sidebar_label: conftest
---

# Test fixtures for parameter_mapping module unit tests.

  file_path: `backend/tests/infrastructure/cache/parameter_mapping/conftest.py`

This module provides reusable fixtures specific to cache parameter mapping testing.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the parameter_mapping module's dependencies
(ValidationError, ConfigurationError) are already available in the shared
cache conftest.py file. The ValidationResult is defined within the module itself.
