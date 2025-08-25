---
sidebar_label: test_key_generator
---

# Tests for standalone CacheKeyGenerator component.

  file_path: `backend/tests/infrastructure/cache/test_key_generator.py`

This module provides comprehensive tests for the CacheKeyGenerator class,
including edge cases for very small text, >10 MB text, Unicode handling,
and performance monitoring integration.

The tests validate:
- Basic key generation functionality
- Streaming SHA-256 hashing for large texts
- Performance monitoring integration
- Edge cases (empty text, boundary conditions, Unicode)
- Backward compatibility with existing key formats
- Thread safety and concurrent access
