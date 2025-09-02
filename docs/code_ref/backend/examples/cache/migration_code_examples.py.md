---
sidebar_label: migration_code_examples
---

# Migration Code Examples: Before/After Patterns

  file_path: `backend/examples/cache/migration_code_examples.py`

This module provides concrete before/after code examples for migrating from
auto-detection patterns to explicit factory methods. These examples demonstrate
practical migration strategies for different application patterns.

Migration Areas Covered:
- Auto-detection to explicit factory methods
- Environment-based selection to explicit configuration
- FastAPI dependency injection updates
- Environment variable migration
- Test fixture migration to for_testing() method
- Health check endpoint conversion

## LegacyAutoDetectionPattern

BEFORE: Legacy auto-detection pattern (DEPRECATED)

This class demonstrates the old pattern that should be migrated away from.

### get_cache_instance()

```python
def get_cache_instance():
```

OLD PATTERN: Auto-detection based on environment variables.

This approach is deprecated because:
- Magic behavior is hard to debug
- Configuration is scattered across environment variables
- Fallback behavior is implicit and unpredictable
- Testing is difficult due to environment coupling

## ModernExplicitPattern

AFTER: Modern explicit factory pattern (RECOMMENDED)

This class demonstrates the new explicit pattern that provides:
- Clear intent and predictable behavior
- Centralized configuration
- Graceful degradation with explicit control
- Easy testing with dedicated factory methods

### get_web_cache()

```python
def get_web_cache() -> CacheInterface:
```

NEW PATTERN: Explicit web application cache.

Clear intent: This creates a cache optimized for web applications.

### get_ai_cache()

```python
def get_ai_cache() -> CacheInterface:
```

NEW PATTERN: Explicit AI application cache.

Clear intent: This creates a cache optimized for AI operations.

### get_test_cache()

```python
def get_test_cache() -> CacheInterface:
```

NEW PATTERN: Explicit testing cache.

Clear intent: This creates a cache for testing scenarios.

### get_config_based_cache()

```python
def get_config_based_cache() -> CacheInterface:
```

NEW PATTERN: Configuration-based cache creation.

Ultimate flexibility: Use configuration objects for complex setups.

## LegacyFastAPIDependencies

BEFORE: Manual dependency injection (DEPRECATED)

### get_cache_dependency()

```python
async def get_cache_dependency(cls):
```

OLD: Manual singleton management with auto-detection.

## ModernFastAPIDependencies

AFTER: Comprehensive dependency injection system (RECOMMENDED)

### example_endpoint_old_style()

```python
def example_endpoint_old_style():
```

OLD: Manual dependency management in FastAPI endpoints.

### example_endpoint_new_style()

```python
def example_endpoint_new_style():
```

NEW: Automatic dependency injection with lifecycle management.

## LegacyEnvironmentVariables

BEFORE: Scattered environment variables (DEPRECATED)

### get_legacy_config()

```python
def get_legacy_config():
```

OLD: Multiple scattered environment variables.

## ModernEnvironmentVariables

AFTER: Centralized configuration with presets (RECOMMENDED)

### get_modern_config()

```python
def get_modern_config():
```

NEW: Centralized configuration with environment presets.

### get_builder_config()

```python
def get_builder_config():
```

NEW: Use builder pattern with environment loading.

### get_hybrid_config()

```python
def get_hybrid_config():
```

NEW: Combine presets with custom overrides.

## LegacyTestFixtures

BEFORE: Manual test setup (DEPRECATED)

### setup_test_cache()

```python
async def setup_test_cache():
```

OLD: Manual test cache setup with environment coupling.

### cleanup_test_cache()

```python
async def cleanup_test_cache(cache):
```

OLD: Manual cleanup with potential issues.

## ModernTestFixtures

AFTER: Factory-based test fixtures (RECOMMENDED)

### setup_unit_test_cache()

```python
async def setup_unit_test_cache():
```

NEW: Memory cache for fast unit tests.

### setup_integration_test_cache()

```python
async def setup_integration_test_cache():
```

NEW: Redis cache for integration tests.

### cleanup_test_cache()

```python
async def cleanup_test_cache(cache):
```

NEW: Automatic cleanup with proper isolation.

## LegacyHealthChecks

BEFORE: Manual health check implementation (DEPRECATED)

### manual_health_check()

```python
async def manual_health_check():
```

OLD: Manual health check with hardcoded logic.

## ModernHealthChecks

AFTER: Dependency-based health checks (RECOMMENDED)

### dependency_health_check()

```python
async def dependency_health_check():
```

NEW: Use dependency injection for health checks.

## demo_migration_example_1()

```python
async def demo_migration_example_1():
```

Demonstrate migration from auto-detection to explicit patterns.

## demo_migration_example_2()

```python
async def demo_migration_example_2():
```

Demonstrate FastAPI dependency injection migration.

## demo_environment_variable_migration()

```python
def demo_environment_variable_migration():
```

Demonstrate environment variable migration patterns.

## demo_migration_example_4()

```python
async def demo_migration_example_4():
```

Demonstrate test fixture migration.

## demo_migration_example_5()

```python
async def demo_migration_example_5():
```

Demonstrate health check endpoint migration.

## run_all_migration_examples()

```python
async def run_all_migration_examples():
```

Run all migration examples to demonstrate the complete
transition from legacy patterns to modern explicit patterns.
