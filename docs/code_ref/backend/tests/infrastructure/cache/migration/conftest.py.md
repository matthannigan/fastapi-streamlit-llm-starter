---
sidebar_label: conftest
---

# Test fixtures for migration module unit tests.

  file_path: `backend/tests/infrastructure/cache/migration/conftest.py`

This module provides reusable fixtures specific to cache migration testing.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the migration module's dependencies
(ValidationError, CacheInterface) are already available in the shared
cache conftest.py file.
