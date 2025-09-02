---
sidebar_label: test_compatibility
---

# Tests for cache compatibility wrapper.

  file_path: `backend/tests.old/infrastructure/cache/test_compatibility.py`

This test suite validates that the CacheCompatibilityWrapper properly maintains
backwards compatibility during the cache infrastructure transition while providing
deprecation warnings and seamless integration with both legacy and new cache interfaces.

Test Coverage:
- Legacy method compatibility with deprecation warnings
- Proxy functionality for non-legacy methods
- Generic cache interface integration
- Error handling for unsupported operations
- Warning suppression configuration

## TestCacheCompatibilityWrapper

Test suite for CacheCompatibilityWrapper functionality.

### mock_generic_cache()

```python
def mock_generic_cache(self):
```

Mock GenericRedisCache for testing.

### mock_ai_cache()

```python
def mock_ai_cache(self):
```

Mock AIResponseCache for testing.

### compatibility_wrapper()

```python
def compatibility_wrapper(self, mock_ai_cache):
```

CacheCompatibilityWrapper with AI cache for testing.

### compatibility_wrapper_with_warnings()

```python
def compatibility_wrapper_with_warnings(self, mock_ai_cache):
```

CacheCompatibilityWrapper with warnings enabled.

### test_initialization()

```python
def test_initialization(self, mock_ai_cache):
```

Test wrapper initialization with inner cache.

### test_initialization_default_warnings()

```python
def test_initialization_default_warnings(self, mock_ai_cache):
```

Test wrapper initialization with default warning settings.

### test_proxy_non_legacy_methods()

```python
def test_proxy_non_legacy_methods(self, compatibility_wrapper, mock_ai_cache):
```

Test that non-legacy methods are proxied without warnings.

### test_legacy_get_cached_response_with_ai_cache()

```python
async def test_legacy_get_cached_response_with_ai_cache(self, compatibility_wrapper, mock_ai_cache):
```

Test legacy get_cached_response method with AI cache backend.

### test_legacy_get_cached_response_with_generic_cache()

```python
async def test_legacy_get_cached_response_with_generic_cache(self, mock_generic_cache):
```

Test legacy get_cached_response with generic cache fallback.

### test_legacy_cache_response_with_ai_cache()

```python
async def test_legacy_cache_response_with_ai_cache(self, compatibility_wrapper, mock_ai_cache):
```

Test legacy cache_response method with AI cache backend.

### test_legacy_cache_response_with_generic_cache()

```python
async def test_legacy_cache_response_with_generic_cache(self, mock_generic_cache):
```

Test legacy cache_response with generic cache fallback.

### test_legacy_methods_emit_warnings()

```python
async def test_legacy_methods_emit_warnings(self, mock_ai_cache):
```

Test that legacy methods emit deprecation warnings when configured.

### test_legacy_methods_no_warnings_when_disabled()

```python
async def test_legacy_methods_no_warnings_when_disabled(self, mock_ai_cache):
```

Test that legacy methods don't emit warnings when disabled.

### test_getattr_legacy_method_warnings()

```python
def test_getattr_legacy_method_warnings(self, mock_ai_cache):
```

Test __getattr__ emits warnings for legacy methods.

### test_getattr_non_legacy_method_no_warnings()

```python
def test_getattr_non_legacy_method_no_warnings(self, mock_ai_cache):
```

Test __getattr__ doesn't emit warnings for non-legacy methods.

### test_unsupported_legacy_method_with_basic_cache()

```python
async def test_unsupported_legacy_method_with_basic_cache(self):
```

Test error handling when inner cache doesn't support legacy methods.

### test_question_parameter_forwarding()

```python
async def test_question_parameter_forwarding(self, compatibility_wrapper, mock_ai_cache):
```

Test that question parameter is properly forwarded to inner cache.

### test_legacy_methods_list()

```python
def test_legacy_methods_list(self, compatibility_wrapper):
```

Test that known legacy methods are correctly identified.

## TestCacheCompatibilityIntegration

Integration tests for compatibility wrapper with real cache classes.

### test_wrapper_with_real_ai_cache()

```python
def test_wrapper_with_real_ai_cache(self):
```

Test wrapper integration with actual AIResponseCache.

### test_wrapper_with_real_generic_cache()

```python
def test_wrapper_with_real_generic_cache(self):
```

Test wrapper integration with actual GenericRedisCache.

### test_new_generic_methods_accessible()

```python
async def test_new_generic_methods_accessible(self):
```

Test that new generic cache methods are accessible through wrapper.

## TestCacheCompatibilityErrorHandling

Test error handling and edge cases in compatibility wrapper.

### test_missing_attribute_error()

```python
def test_missing_attribute_error(self):
```

Test that missing attributes raise appropriate errors.

### test_legacy_method_with_no_fallback()

```python
async def test_legacy_method_with_no_fallback(self):
```

Test legacy method behavior when neither AI nor generic methods exist.

### test_wrapper_preserves_inner_cache_errors()

```python
def test_wrapper_preserves_inner_cache_errors(self):
```

Test that errors from inner cache are properly propagated.
