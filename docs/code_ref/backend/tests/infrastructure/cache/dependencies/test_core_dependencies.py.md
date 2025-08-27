---
sidebar_label: test_core_dependencies
---

# Unit tests for core cache dependency functions.

  file_path: `backend/tests/infrastructure/cache/dependencies/test_core_dependencies.py`

This test suite verifies the observable behaviors documented in the
cache dependencies public contract (dependencies.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

## Coverage Focus

- get_settings() cached settings dependency behavior
- get_cache_config() configuration building from settings
- get_cache_service() main cache service dependency with registry management
- Dependency integration and error handling

## External Dependencies

All external dependencies are mocked using fixtures from conftest.py following
the documented public contracts to ensure accurate behavior simulation.
