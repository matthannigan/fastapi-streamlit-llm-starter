---
sidebar_label: conftest
---

# Test fixtures for key_generator module unit tests.

  file_path: `backend/tests/unit/cache/key_generator/conftest.py`

This module provides reusable fixtures specific to cache key generation testing.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the key_generator module's dependencies
(CachePerformanceMonitor) are already available in the shared cache conftest.py file.
