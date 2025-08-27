---
sidebar_label: test_factory
---

# Unit tests for CacheFactory explicit cache instantiation.

  file_path: `backend/tests/infrastructure/cache/factory/test_factory.py`

This test suite verifies the observable behaviors documented in the
CacheFactory public contract (factory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

## Coverage Focus

- Infrastructure service (>90% test coverage requirement)
- Behavior verification per docstring specifications
- Factory method cache creation and configuration
- Error handling and graceful fallback patterns

## External Dependencies

All external dependencies are mocked using fixtures from conftest.py following
the documented public contracts to ensure accurate behavior simulation.
