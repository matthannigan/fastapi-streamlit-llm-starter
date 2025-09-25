---
sidebar_label: test_dependencies
---

# Tests for dependency injection providers.

  file_path: `backend/tests.old/unit/core/test_dependencies.py`

## TestDependencyInjection

Test dependency injection providers.

### test_get_cache_service_creates_configured_instance()

```python
async def test_get_cache_service_creates_configured_instance(self):
```

Test that get_cache_service creates a properly configured cache instance and calls connect.

### test_get_cache_service_graceful_degradation_when_redis_unavailable()

```python
async def test_get_cache_service_graceful_degradation_when_redis_unavailable(self):
```

Test that get_cache_service works gracefully when Redis connection fails.

### test_get_cache_service_when_connect_raises_exception()

```python
async def test_get_cache_service_when_connect_raises_exception(self):
```

Test that get_cache_service handles exceptions during connect gracefully.

### test_get_cache_service_real_integration_with_unavailable_redis()

```python
async def test_get_cache_service_real_integration_with_unavailable_redis(self):
```

Test real integration with unavailable Redis server (no mocking).

### test_get_text_processor_service_uses_injected_cache()

```python
def test_get_text_processor_service_uses_injected_cache(self):
```

Test that get_text_processor_service uses the injected cache service.

### test_dependency_chain_integration()

```python
async def test_dependency_chain_integration(self):
```

Test that the full dependency chain works together.

### test_cache_service_uses_settings_redis_url()

```python
async def test_cache_service_uses_settings_redis_url(self):
```

Test that cache service uses redis_url from settings.

### test_get_text_processor_creates_configured_instance()

```python
async def test_get_text_processor_creates_configured_instance(self):
```

Test that get_text_processor creates a properly configured TextProcessorService instance.

### test_get_text_processor_with_dependency_injection()

```python
async def test_get_text_processor_with_dependency_injection(self):
```

Test that get_text_processor works with actual dependency injection chain.

### test_get_text_processor_uses_injected_dependencies_correctly()

```python
async def test_get_text_processor_uses_injected_dependencies_correctly(self):
```

Test that get_text_processor correctly uses both settings and cache dependencies.

### test_get_text_processor_async_behavior()

```python
async def test_get_text_processor_async_behavior(self):
```

Test that get_text_processor is properly async and can be awaited.

### test_get_text_processor_comparison_with_sync_version()

```python
async def test_get_text_processor_comparison_with_sync_version(self):
```

Test that async get_text_processor produces equivalent results to sync version.

## create_mock_settings()

```python
def create_mock_settings(**overrides):
```

Create a properly mocked Settings object with all required attributes.
