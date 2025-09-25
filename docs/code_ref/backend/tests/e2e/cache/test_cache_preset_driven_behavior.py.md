---
sidebar_label: test_cache_preset_driven_behavior
---

## TestPresetDrivenBehavior

End-to-end test for verifying configuration-driven behavior via presets.

Scope:
    Validates that the `CACHE_PRESET` environment variable correctly alters
    the running state and observable behavior of the cache service.
    
External Dependencies:
    - Uses client_with_preset fixture for environment isolation
    - Assumes proper Redis/memory cache configuration
    
Known Limitations:
    - Does not test actual Redis connectivity (uses mocked connections)
    - Preset transitions tested via app factory, not live server restarts
    - Performance impact of preset changes not measured

### test_preset_influences_cache_status()

```python
async def test_preset_influences_cache_status(self, client_with_preset, preset, expected_redis, expected_memory):
```

Test that different cache presets result in different observable statuses.

Test Purpose:
    To verify that the application's configuration system works end-to-end,
    from an environment variable setting to a change in API behavior.

Business Impact:
    Provides confidence that we can reliably configure our application for
    different environments (development, production, disabled) and that these
    configurations are being correctly applied, which is critical for performance,
    stability, and cost management.

Test Scenario:
    1.  GIVEN the application is configured with a specific CACHE_PRESET.
    2.  WHEN a request is made to `GET /internal/cache/status`.
    3.  THEN the response should indicate the expected Redis and memory status
        according to the preset configuration.

Success Criteria:
    - Each preset returns expected Redis connection status
    - Each preset returns expected memory cache status  
    - Status endpoint responds gracefully with 200 for all presets
    - Response structure contains required status fields

### test_preset_configuration_persistence()

```python
async def test_preset_configuration_persistence(self, client_with_preset):
```

Test that preset configuration remains consistent across multiple requests.

Test Purpose:
    Verifies that configuration changes are properly applied and persist
    across multiple API calls within the same application instance.
    
Business Impact:
    Ensures configuration stability and prevents unexpected behavior changes
    during application runtime due to configuration inconsistencies.
    
Test Scenario:
    1.  GIVEN an application configured with 'ai-production' preset.
    2.  WHEN multiple status requests are made sequentially.
    3.  THEN all responses should show consistent configuration state.
    
Success Criteria:
    - Multiple status calls return identical configuration state
    - Redis connection status remains stable across requests
    - Memory cache configuration persists between calls

### test_disabled_preset_prevents_cache_operations()

```python
async def test_disabled_preset_prevents_cache_operations(self, client_with_preset):
```

Test that 'disabled' preset properly prevents cache operations.

Test Purpose:
    Validates that disabled cache configuration actually prevents
    cache operations and provides appropriate error responses.
    
Business Impact:
    Critical for cost management and ensuring cache resources are
    not consumed when caching is intentionally disabled.
    
Test Scenario:
    1.  GIVEN an application configured with 'disabled' preset.
    2.  WHEN cache operations are attempted via API endpoints.
    3.  THEN operations should fail gracefully with appropriate errors.
    
Success Criteria:
    - Cache status shows disabled state
    - Cache operations return appropriate error responses
    - System remains stable despite disabled cache
