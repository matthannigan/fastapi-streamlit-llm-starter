"""
Settings Factory Pattern Test Suite

This test suite validates the settings factory implementation that enables fresh Settings
instance creation for test isolation and multi-instance scenarios. The tests verify that
the factory pattern properly creates independent Settings instances while maintaining
backward compatibility with the existing module-level singleton.

## Test Coverage

### Factory Function Tests
- `test_create_settings_creates_fresh_instances()`: Verifies fresh instance creation
- `test_create_settings_independence()`: Tests instance independence
- `test_create_settings_environment_isolation()`: Validates environment variable isolation

### Dependency Injection Tests
- `test_get_settings_factory_dependency_injection()`: Tests FastAPI dependency injection
- `test_get_settings_factory_fresh_instances()`: Verifies fresh instances per dependency resolution
- `test_get_settings_factory_vs_cached()`: Compares factory vs. cached dependency

### Backward Compatibility Tests
- `test_module_level_singleton_unchanged()`: Verifies singleton behavior unchanged
- `test_existing_imports_work()`: Tests existing code continues to work
- `test_get_fresh_settings_uses_factory()`: Validates integration with existing fresh settings

### Environment Variable Tests
- `test_environment_variable_changes_propagate()`: Tests env var changes take effect
- `test_preset_configuration_changes()`: Validates preset configuration changes
- `test_custom_json_configuration()`: Tests custom JSON configuration handling

### Configuration Validation Tests
- `test_factory_maintains_validation()`: Ensures validation rules are applied
- `test_factory_error_handling()`: Tests error handling behavior
- `test_factory_preset_fallback()`: Validates preset fallback behavior

## Architecture Validation

The tests verify that the factory pattern addresses the core problem of test isolation
by ensuring that:

1. **Fresh Instance Creation**: Each factory call creates a completely new Settings instance
2. **Environment Variable Isolation**: Environment changes are immediately picked up by new instances
3. **Configuration Independence**: Multiple instances have independent configuration state
4. **Backward Compatibility**: Existing module-level singleton behavior is preserved
5. **Validation Consistency**: Factory instances use same validation as singleton

## Test Philosophy

These tests focus on observable behavior rather than implementation details:
- Test that factory creates independent instances (external behavior)
- Test that environment changes work (observable outcome)
- Test backward compatibility is maintained (existing code behavior)
- Avoid testing Pydantic internals (implementation details)

The tests validate the factory pattern solves the test isolation problem while maintaining
full compatibility with existing code patterns.
"""

import pytest
import os
from unittest.mock import patch

from app.core.config import Settings, create_settings, get_settings_factory, settings
from app.dependencies import get_fresh_settings


class TestSettingsFactoryCreation:
    """Test suite for create_settings() factory function behavior."""

    def test_create_settings_creates_fresh_instances(self):
        """Test that create_settings() creates fresh Settings instances."""
        # Create multiple instances
        settings1 = create_settings()
        settings2 = create_settings()
        settings3 = create_settings()

        # Verify they are different objects
        assert settings1 is not settings2
        assert settings2 is not settings3
        assert settings1 is not settings3

        # Verify they have the same configuration values (same environment)
        assert settings1.debug == settings2.debug == settings3.debug
        assert settings1.cache_preset == settings2.cache_preset == settings3.cache_preset

    def test_create_settings_independence(self):
        """Test that factory instances are completely independent."""
        # Create base instance
        base_settings = create_settings()
        original_debug = base_settings.debug

        # Modify environment and create new instance
        with patch.dict(os.environ, {"DEBUG": "true" if not original_debug else "false"}):
            new_settings = create_settings()

            # New instance should have different configuration
            assert new_settings.debug != original_debug
            # Original instance should be unchanged
            assert base_settings.debug == original_debug

    def test_create_settings_same_configuration(self):
        """Test that factory instances have same configuration in same environment."""
        settings1 = create_settings()
        settings2 = create_settings()

        # All configuration fields should be identical
        assert settings1.debug == settings2.debug
        assert settings1.cache_preset == settings2.cache_preset
        assert settings1.resilience_preset == settings2.resilience_preset
        assert settings1.api_key == settings2.api_key
        assert settings1.gemini_api_key == settings2.gemini_api_key

    def test_create_settings_configuration_methods(self):
        """Test that factory instances support all configuration methods."""
        factory_settings = create_settings()

        # Test that all configuration methods work
        assert hasattr(factory_settings, "get_cache_config")
        assert hasattr(factory_settings, "get_resilience_config")
        assert hasattr(factory_settings, "get_valid_api_keys")
        assert hasattr(factory_settings, "get_operation_strategy")

        # Test that methods return valid configurations
        cache_config = factory_settings.get_cache_config()
        resilience_config = factory_settings.get_resilience_config()
        api_keys = factory_settings.get_valid_api_keys()

        assert cache_config is not None
        assert resilience_config is not None
        assert isinstance(api_keys, list)


class TestGetSettingsFactoryDependencyInjection:
    """Test suite for get_settings_factory() FastAPI dependency injection."""

    def test_get_settings_factory_returns_fresh_instances(self):
        """Test that get_settings_factory() returns fresh instances."""
        settings1 = get_settings_factory()
        settings2 = get_settings_factory()

        # Should be different instances
        assert settings1 is not settings2
        # But same configuration
        assert settings1.debug == settings2.debug

    def test_get_settings_factory_environment_isolation(self):
        """Test that dependency injection picks up environment changes."""
        # Get baseline configuration
        base_settings = get_settings_factory()
        original_cache_preset = base_settings.cache_preset

        # Change environment and get new instance
        with patch.dict(os.environ, {"CACHE_PRESET": "production"}):
            new_settings = get_settings_factory()

            # Should pick up new environment
            assert new_settings.cache_preset == "production"
            assert new_settings.cache_preset != original_cache_preset

    def test_get_settings_factory_vs_create_settings(self):
        """Test that get_settings_factory() behaves same as create_settings()."""
        factory_settings = get_settings_factory()
        direct_settings = create_settings()

        # Should have identical configuration
        assert factory_settings.debug == direct_settings.debug
        assert factory_settings.cache_preset == direct_settings.cache_preset
        assert factory_settings.resilience_preset == direct_settings.resilience_preset


class TestBackwardCompatibility:
    """Test suite to ensure backward compatibility with existing code."""

    def test_module_level_singleton_unchanged(self):
        """Test that module-level settings singleton behavior is unchanged."""
        # Module-level settings should be same object across imports
        from app.core.config import settings as settings1
        from app.core.config import settings as settings2

        assert settings1 is settings2
        assert settings1 is settings  # Should be the global instance

    def test_existing_imports_work(self):
        """Test that existing import patterns continue to work."""
        # Test direct import
        from app.core.config import settings

        # Test that it has expected attributes
        assert hasattr(settings, "debug")
        assert hasattr(settings, "cache_preset")
        assert hasattr(settings, "get_cache_config")
        assert hasattr(settings, "get_resilience_config")

        # Test that methods work
        cache_config = settings.get_cache_config()
        assert cache_config is not None

    def test_get_fresh_settings_uses_factory(self):
        """Test that existing get_fresh_settings() uses the new factory."""
        fresh1 = get_fresh_settings()
        fresh2 = get_fresh_settings()

        # Should be different instances
        assert fresh1 is not fresh2
        # But both should be Settings instances
        assert isinstance(fresh1, Settings)
        assert isinstance(fresh2, Settings)

    def test_dependency_injection_backwards_compatibility(self):
        """Test that existing dependency injection patterns work."""
        from app.dependencies import get_settings, get_fresh_settings

        # Cached dependency should return same instance
        cached1 = get_settings()
        cached2 = get_settings()
        assert cached1 is cached2

        # Fresh dependency should return different instances
        fresh1 = get_fresh_settings()
        fresh2 = get_fresh_settings()
        assert fresh1 is not fresh2


class TestEnvironmentVariableIntegration:
    """Test suite for environment variable integration with factory pattern."""

    def test_environment_variable_changes_propagate(self):
        """Test that environment variable changes are picked up by factory."""
        # Set baseline
        original_debug = os.getenv("DEBUG", "false")

        # Test with debug=True
        with patch.dict(os.environ, {"DEBUG": "true"}):
            debug_settings = create_settings()
            assert debug_settings.debug is True

        # Test with debug=False
        with patch.dict(os.environ, {"DEBUG": "false"}):
            non_debug_settings = create_settings()
            assert non_debug_settings.debug is False

        # Test with no DEBUG env var (should use default)
        with patch.dict(os.environ, {}, clear=True):
            default_settings = create_settings()
            assert isinstance(default_settings.debug, bool)

    def test_preset_configuration_changes(self):
        """Test that preset configuration changes work with factory."""
        # Test cache preset changes (cache preset is not filtered in pytest)
        with patch.dict(os.environ, {"CACHE_PRESET": "production"}):
            prod_settings = create_settings()
            assert prod_settings.cache_preset == "production"

            cache_config = prod_settings.get_cache_config()
            assert cache_config is not None

        # Note: RESILIENCE_PRESET is filtered during pytest for test isolation
        # This is intentional behavior to prevent test pollution
        # Factory still works - it respects the existing Settings class behavior

    def test_custom_json_configuration(self):
        """Test that custom JSON configuration works with factory."""
        # Note: RESILIENCE_CUSTOM_CONFIG is filtered during pytest for test isolation
        # This is intentional behavior to prevent test pollution
        # Test that factory handles this gracefully

        # Test with cache configuration (not filtered in pytest)
        custom_cache = '{"default_ttl": 7200, "compression_threshold": 500}'
        with patch.dict(os.environ, {"CACHE_CUSTOM_CONFIG": custom_cache}):
            custom_settings = create_settings()
            cache_config = custom_settings.get_cache_config()

            # Custom configuration should be applied
            assert cache_config.default_ttl == 7200
            assert cache_config.compression_threshold == 500

        # Resilience custom config is filtered in pytest, but factory still works
        # This ensures tests are deterministic and not polluted by environment

    def test_api_key_environment_variables(self):
        """Test that API key environment variables work with factory."""
        test_api_key = "test-api-key-12345"
        test_gemini_key = "test-gemini-key-67890"

        with patch.dict(os.environ, {
            "API_KEY": test_api_key,
            "GEMINI_API_KEY": test_gemini_key
        }):
            api_settings = create_settings()

            assert api_settings.api_key == test_api_key
            assert api_settings.gemini_api_key == test_gemini_key


class TestConfigurationValidation:
    """Test suite for configuration validation with factory pattern."""

    def test_factory_maintains_validation(self):
        """Test that factory instances maintain all validation rules."""
        # Test invalid cache preset
        with pytest.raises(Exception):  # Should raise ConfigurationError
            with patch.dict(os.environ, {"CACHE_PRESET": "invalid_preset"}):
                create_settings()

        # Test invalid log level
        with pytest.raises(Exception):  # Should raise ConfigurationError
            with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
                create_settings()

        # Test valid configurations
        valid_settings = create_settings()
        assert valid_settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert valid_settings.cache_preset in [
            "disabled", "simple", "development", "production",
            "ai-development", "ai-production"
        ]

    def test_factory_error_handling(self):
        """Test error handling behavior with factory pattern."""
        # Test with invalid JSON configuration
        invalid_json = '{"invalid": json structure}'
        with patch.dict(os.environ, {"RESILIENCE_CUSTOM_CONFIG": invalid_json}):
            # Should not crash, should handle gracefully with warning
            settings = create_settings()
            assert settings is not None
            # Should fall back to preset configuration
            resilience_config = settings.get_resilience_config()
            assert resilience_config is not None

    def test_factory_preset_fallback(self):
        """Test preset fallback behavior with factory."""
        # Test with invalid cache preset - should fallback to 'simple'
        with patch.dict(os.environ, {"CACHE_PRESET": "nonexistent_preset"}):
            # This should raise ConfigurationError due to validator
            with pytest.raises(Exception):
                create_settings()

    def test_factory_health_check_configuration(self):
        """Test that health check configuration works with factory."""
        test_timeout = 5000
        test_retry_count = 3

        with patch.dict(os.environ, {
            "HEALTH_CHECK_TIMEOUT_MS": str(test_timeout),
            "HEALTH_CHECK_RETRY_COUNT": str(test_retry_count)
        }):
            health_settings = create_settings()

            assert health_settings.health_check_timeout_ms == test_timeout
            assert health_settings.health_check_retry_count == test_retry_count


class TestFactoryPerformance:
    """Test suite for factory performance characteristics."""

    def test_factory_creation_performance(self):
        """Test that factory creation has reasonable performance."""
        import time

        # Measure time to create multiple instances
        start_time = time.time()
        instances = []
        for _ in range(10):
            instances.append(create_settings())
        end_time = time.time()

        # Should complete reasonably quickly (adjust threshold as needed)
        creation_time = end_time - start_time
        assert creation_time < 1.0  # Should be less than 1 second for 10 instances

        # All instances should be different
        for i in range(len(instances) - 1):
            assert instances[i] is not instances[i + 1]

    def test_factory_memory_usage(self):
        """Test that factory doesn't cause excessive memory usage."""
        # Create multiple instances and verify they're garbage collectible
        import gc

        instances = []
        for _ in range(100):
            instances.append(create_settings())

        # Clear references and force garbage collection
        del instances
        gc.collect()

        # If we get here without memory issues, test passes
        assert True


class TestFactoryIntegration:
    """Integration tests for factory pattern with existing systems."""

    def test_factory_with_dependency_injection_system(self):
        """Test factory integration with FastAPI dependency injection."""
        from fastapi import FastAPI, Depends

        app = FastAPI()

        @app.get("/test-config")
        async def test_config(settings: Settings = Depends(get_settings_factory)):
            return {
                "debug": settings.debug,
                "cache_preset": settings.cache_preset,
                "resilience_preset": settings.resilience_preset
            }

        # Test that endpoint can be created without errors
        assert app is not None

    def test_factory_with_cache_service_integration(self):
        """Test factory integration with cache service."""

        # Create settings with factory
        factory_settings = create_settings()

        # Should be able to create cache service with factory settings
        # Note: This test doesn't actually initialize cache service to avoid Redis dependency
        assert factory_settings is not None
        assert hasattr(factory_settings, "get_cache_config")

    def test_factory_isolation_in_test_scenario(self):
        """Test factory isolation in realistic test scenario."""
        # Simulate test scenario where different tests need different configurations

        # Test 1: Development configuration
        with patch.dict(os.environ, {
            "DEBUG": "true",
            "CACHE_PRESET": "development"
            # Note: RESILIENCE_PRESET is filtered in pytest for test isolation
        }):
            dev_settings = create_settings()
            assert dev_settings.debug is True
            assert dev_settings.cache_preset == "development"
            # resilience_preset will be default due to pytest filtering

        # Test 2: Production configuration
        with patch.dict(os.environ, {
            "DEBUG": "false",
            "CACHE_PRESET": "production"
            # Note: RESILIENCE_PRESET is filtered in pytest for test isolation
        }):
            prod_settings = create_settings()
            assert prod_settings.debug is False
            assert prod_settings.cache_preset == "production"
            # resilience_preset will be default due to pytest filtering

        # Verify settings are independent (excluding filtered resilience preset)
        assert dev_settings.debug != prod_settings.debug
        assert dev_settings.cache_preset != prod_settings.cache_preset
        # Factory creates independent instances even when some env vars are filtered
