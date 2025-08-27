---
sidebar_label: test_dependencies
---

# Tests for FastAPI cache dependency integration with preset system.

  file_path: `backend/tests.old/infrastructure/cache/test_dependencies.py`

This module tests the cache dependency injection system with the new preset-based
configuration approach, ensuring all preset configurations work correctly with
FastAPI dependencies and override systems.

## Test Categories

- Preset-based configuration loading tests
- Environment variable validation and error handling
- Override precedence tests (Custom Config > Environment Variables > Preset Defaults)
- Invalid preset handling with descriptive error messages
- Fallback behavior when CACHE_PRESET not specified
- Configuration validation after loading

## Key Dependencies Under Test

- get_cache_config(): Main configuration dependency using preset system
- get_cache_service(): Cache service creation with preset configurations
- Settings integration with preset system
- Override handling via CACHE_REDIS_URL, ENABLE_AI_CACHE, CACHE_CUSTOM_CONFIG
