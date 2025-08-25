---
sidebar_label: test_compatibility
---

# Tests for cache compatibility wrapper.

  file_path: `backend/tests/infrastructure/cache/test_compatibility.py`

This test suite validates that the CacheCompatibilityWrapper properly maintains
backwards compatibility during the cache infrastructure transition while providing
deprecation warnings and seamless integration with both legacy and new cache interfaces.

## Test Coverage

- Legacy method compatibility with deprecation warnings
- Proxy functionality for non-legacy methods
- Generic cache interface integration
- Error handling for unsupported operations
- Warning suppression configuration
