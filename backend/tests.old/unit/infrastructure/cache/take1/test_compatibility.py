"""
Comprehensive unit tests for cache compatibility wrapper system.

This module tests all compatibility components following docstring-driven
test development methodology. Tests verify documented contracts in Args, Returns,
Raises, and Behavior sections, focusing on WHAT should happen rather than HOW
it's implemented.

Test Classes:
    - TestCacheCompatibilityWrapperInitialization: Wrapper initialization and configuration
    - TestCacheCompatibilityWrapperAttributeAccess: Dynamic attribute proxying to inner cache  
    - TestCacheCompatibilityWrapperDeprecationWarnings: Deprecation warning system behavior
    - TestCacheCompatibilityWrapperLegacyMethods: Legacy method compatibility and forwarding
    - TestCacheCompatibilityWrapperEdgeCases: Error handling and boundary conditions
    - TestCacheCompatibilityWrapperIntegration: Integration with various cache implementations

Coverage Requirements:
    >90% coverage for infrastructure modules per project standards
    
Testing Philosophy:
    - Test WHAT should happen per docstring contracts
    - Focus on behavior verification, not implementation details
    - Mock only external dependencies (warnings, logging, AsyncMock detection)
    - Test edge cases and error conditions documented in docstrings
    - Validate backwards compatibility and migration support during refactoring
    - Test behavioral equivalence between legacy and new cache patterns
"""

import asyncio
import inspect
import logging
import warnings
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
from typing import Any, Dict, Optional

from app.infrastructure.cache.compatibility import CacheCompatibilityWrapper


class TestCacheCompatibilityWrapperInitialization:
    """Test compatibility wrapper initialization per docstring contracts."""

    def test_wrapper_initialization_with_defaults(self):
        """
        Test CacheCompatibilityWrapper initialization with defaults per docstring.

        Verifies:
            Wrapper initializes with inner_cache and default emit_warnings=True as documented

        Business Impact:
            Ensures compatibility wrapper properly wraps cache implementations during migration

        Scenario:
            Given: Inner cache implementation
            When: CacheCompatibilityWrapper is created with defaults
            Then: Wrapper stores inner cache and enables warnings by default
        """
        inner_cache = MagicMock()
        wrapper = CacheCompatibilityWrapper(inner_cache)

        assert wrapper._inner_cache is inner_cache
        assert wrapper._emit_warnings is True

    def test_wrapper_initialization_with_warnings_disabled(self):
        """
        Test CacheCompatibilityWrapper initialization with warnings disabled per docstring.

        Verifies:
            Wrapper can be initialized with emit_warnings=False for production usage

        Business Impact:
            Allows production deployments to use compatibility layer without warning noise

        Scenario:
            Given: Inner cache implementation and emit_warnings=False
            When: CacheCompatibilityWrapper is created
            Then: Wrapper disables deprecation warnings as specified
        """
        inner_cache = MagicMock()
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        assert wrapper._inner_cache is inner_cache
        assert wrapper._emit_warnings is False


class TestCacheCompatibilityWrapperAttributeAccess:
    """Test compatibility wrapper attribute access behavior per docstring contracts."""

    def test_has_real_attr_with_instance_attributes(self):
        """
        Test _has_real_attr detects instance attributes per docstring.

        Verifies:
            _has_real_attr returns True for attributes in object's __dict__

        Business Impact:
            Prevents auto-creation of attributes on Mock objects during testing

        Scenario:
            Given: Object with instance attributes
            When: _has_real_attr is called on instance attribute
            Then: Returns True for existing instance attributes
        """
        obj = MagicMock()
        obj.__dict__ = {"real_attr": "value"}

        result = CacheCompatibilityWrapper._has_real_attr(obj, "real_attr")

        assert result is True

    def test_has_real_attr_with_class_attributes(self):
        """
        Test _has_real_attr detects class attributes per docstring.

        Verifies:
            _has_real_attr returns True for attributes on object's class

        Business Impact:
            Correctly identifies methods and class attributes for proxying

        Scenario:
            Given: Object with class-defined attributes
            When: _has_real_attr is called on class attribute
            Then: Returns True for existing class attributes
        """
        class TestClass:
            class_attr = "value"

        obj = TestClass()
        result = CacheCompatibilityWrapper._has_real_attr(obj, "class_attr")

        assert result is True

    def test_has_real_attr_with_nonexistent_attribute(self):
        """
        Test _has_real_attr returns False for nonexistent attributes per docstring.

        Verifies:
            _has_real_attr returns False for attributes that don't exist

        Business Impact:
            Prevents Mock objects from auto-creating attributes during attribute access

        Scenario:
            Given: Object without specific attribute
            When: _has_real_attr is called on nonexistent attribute
            Then: Returns False for missing attributes
        """
        obj = MagicMock()
        obj.__dict__ = {}

        result = CacheCompatibilityWrapper._has_real_attr(obj, "nonexistent")

        assert result is False

    def test_has_real_attr_with_exception_handling(self):
        """
        Test _has_real_attr handles exceptions gracefully per docstring.

        Verifies:
            _has_real_attr returns False when attribute access raises exceptions

        Business Impact:
            Ensures robust attribute detection even with problematic objects

        Scenario:
            Given: Object that raises exceptions on attribute access
            When: _has_real_attr is called
            Then: Exception is caught and False is returned
        """
        obj = MagicMock()
        obj.__dict__ = None  # This will cause exceptions in getattr

        result = CacheCompatibilityWrapper._has_real_attr(obj, "any_attr")

        assert result is False

    def test_getattr_proxies_existing_attribute(self):
        """
        Test __getattr__ proxies existing attributes per docstring.

        Verifies:
            __getattr__ returns attributes from inner cache when they exist

        Business Impact:
            Enables transparent access to inner cache methods and attributes

        Scenario:
            Given: Inner cache with existing attribute
            When: Attribute is accessed through wrapper
            Then: Inner cache attribute is returned
        """
        inner_cache = MagicMock()
        inner_cache.existing_method = MagicMock(return_value="result")
        wrapper = CacheCompatibilityWrapper(inner_cache)

        result = wrapper.existing_method

        assert result is inner_cache.existing_method

    def test_getattr_raises_attribute_error_for_missing_attribute(self):
        """
        Test __getattr__ raises AttributeError for missing attributes per docstring.

        Verifies:
            __getattr__ raises AttributeError when attribute doesn't exist on inner cache

        Business Impact:
            Maintains proper attribute access semantics for missing methods

        Scenario:
            Given: Inner cache without specific attribute
            When: Non-existent attribute is accessed through wrapper
            Then: AttributeError is raised with appropriate message
        """
        inner_cache = MagicMock()
        inner_cache.__dict__ = {}
        wrapper = CacheCompatibilityWrapper(inner_cache)

        with pytest.raises(AttributeError) as exc_info:
            _ = wrapper.nonexistent_method

        assert "nonexistent_method" in str(exc_info.value)


class TestCacheCompatibilityWrapperDeprecationWarnings:
    """Test compatibility wrapper deprecation warning system per docstring contracts."""

    def test_getattr_emits_deprecation_warning_for_legacy_methods(self):
        """
        Test __getattr__ emits deprecation warnings for legacy methods per docstring.

        Verifies:
            Legacy methods trigger DeprecationWarning with migration guidance when warnings enabled

        Business Impact:
            Provides clear migration path guidance to developers using legacy cache patterns

        Scenario:
            Given: Wrapper with warnings enabled accessing legacy method
            When: Legacy method is accessed through wrapper
            Then: DeprecationWarning is emitted with specific guidance
        """
        inner_cache = MagicMock()
        inner_cache.get_cached_response = MagicMock(return_value="response")
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=True)

        with pytest.warns(DeprecationWarning, match="get_cached_response.*deprecated"):
            method = wrapper.get_cached_response
            # Call the wrapped method to trigger the warning
            method("args")

    def test_getattr_logs_legacy_method_usage(self):
        """
        Test __getattr__ logs legacy method usage per docstring.

        Verifies:
            Legacy method access generates warning logs for monitoring migration progress

        Business Impact:
            Enables tracking of legacy usage patterns for migration planning

        Scenario:
            Given: Wrapper with logging and legacy method access
            When: Legacy method is accessed
            Then: Warning is logged about legacy usage
        """
        inner_cache = MagicMock()
        inner_cache.invalidate_pattern = MagicMock(return_value=None)
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=True)

        with patch('app.infrastructure.cache.compatibility.logger') as mock_logger:
            method = wrapper.invalidate_pattern
            method("pattern")

            mock_logger.warning.assert_called_once()
            log_call = mock_logger.warning.call_args[0][0]
            assert "Legacy cache method 'invalidate_pattern' used" in log_call

    def test_getattr_suppresses_warnings_when_disabled(self):
        """
        Test __getattr__ suppresses warnings when emit_warnings=False per docstring.

        Verifies:
            Legacy methods don't emit warnings when wrapper is configured for production use

        Business Impact:
            Allows production deployments without deprecation warning noise

        Scenario:
            Given: Wrapper with warnings disabled
            When: Legacy method is accessed
            Then: No deprecation warnings are emitted
        """
        inner_cache = MagicMock()
        inner_cache.get_cache_stats = MagicMock(return_value={})
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        # Should not emit any warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            method = wrapper.get_cache_stats
            method()

        # Filter to only DeprecationWarnings about our method
        deprecation_warnings = [w for w in warning_list 
                              if issubclass(w.category, DeprecationWarning) 
                              and "get_cache_stats" in str(w.message)]
        assert len(deprecation_warnings) == 0

    def test_getattr_returns_unwrapped_method_for_non_legacy(self):
        """
        Test __getattr__ returns unwrapped methods for non-legacy attributes per docstring.

        Verifies:
            Non-legacy methods are returned as-is without deprecation wrapper

        Business Impact:
            Ensures new cache methods work normally without warning overhead

        Scenario:
            Given: Wrapper accessing non-legacy method
            When: Modern method is accessed
            Then: Original method is returned without deprecation wrapper
        """
        inner_cache = MagicMock()
        inner_cache.get = MagicMock(return_value="value")
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=True)

        method = wrapper.get

        # Should be the original method, not wrapped
        assert method is inner_cache.get


class TestCacheCompatibilityWrapperLegacyMethods:
    """Test compatibility wrapper legacy method support per docstring contracts."""

    @pytest.mark.asyncio
    async def test_get_cached_response_with_warnings_enabled(self):
        """
        Test get_cached_response emits deprecation warnings per docstring.

        Verifies:
            get_cached_response method emits DeprecationWarning when warnings enabled

        Business Impact:
            Guides migration from legacy AI cache interface to generic cache methods

        Scenario:
            Given: Wrapper with warnings enabled
            When: get_cached_response is called
            Then: DeprecationWarning and log warning are emitted
        """
        inner_cache = AsyncMock()
        inner_cache.get_cached_response = AsyncMock(return_value={"result": "response"})
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=True)

        with pytest.warns(DeprecationWarning, match="get_cached_response.*deprecated"):
            with patch('app.infrastructure.cache.compatibility.logger') as mock_logger:
                result = await wrapper.get_cached_response("text", "operation", {})

                assert result == {"result": "response"}
                mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_response_forwards_to_ai_method(self):
        """
        Test get_cached_response forwards to AI-specific method per docstring.

        Verifies:
            When inner cache has get_cached_response method, calls are forwarded properly

        Business Impact:
            Maintains compatibility with existing AI cache implementations during transition

        Scenario:
            Given: Inner cache with AI-specific get_cached_response method
            When: Legacy method is called through wrapper
            Then: Call is forwarded with all parameters
        """
        inner_cache = AsyncMock()
        inner_cache.get_cached_response = AsyncMock(return_value={"ai": "response"})
        # Simulate real attribute existence
        inner_cache.__dict__ = {"get_cached_response": inner_cache.get_cached_response}
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        result = await wrapper.get_cached_response("text", "summarize", {"length": 100}, "question")

        assert result == {"ai": "response"}
        inner_cache.get_cached_response.assert_called_once_with("text", "summarize", {"length": 100}, "question")

    @pytest.mark.asyncio
    async def test_get_cached_response_fallback_to_generic_cache(self):
        """
        Test get_cached_response falls back to generic cache methods per docstring.

        Verifies:
            When AI method unavailable, falls back to generic get with key generation

        Business Impact:
            Enables migration to generic cache while maintaining legacy interface compatibility

        Scenario:
            Given: Inner cache with generic methods but no AI-specific methods
            When: Legacy get_cached_response is called
            Then: Generic get is used with generated cache key
        """
        inner_cache = AsyncMock()
        inner_cache.get = AsyncMock(return_value={"generic": "response"})
        inner_cache._generate_cache_key = MagicMock(return_value="generated_key")
        # Simulate instance attributes for fallback detection
        inner_cache.__dict__ = {
            "_generate_cache_key": inner_cache._generate_cache_key,
            "get": inner_cache.get
        }
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        result = await wrapper.get_cached_response("text", "operation", {"opt": "val"})

        assert result == {"generic": "response"}
        inner_cache._generate_cache_key.assert_called_once_with("text", "operation", {"opt": "val"}, None)
        inner_cache.get.assert_called_once_with("generated_key")

    @pytest.mark.asyncio
    async def test_get_cached_response_raises_not_implemented(self):
        """
        Test get_cached_response raises NotImplementedError when methods unavailable per docstring.

        Verifies:
            When neither AI nor generic methods available, NotImplementedError is raised

        Business Impact:
            Prevents silent failures when cache doesn't support expected interface

        Scenario:
            Given: Inner cache without AI-specific or generic cache methods
            When: get_cached_response is called
            Then: NotImplementedError is raised with descriptive message
        """
        inner_cache = MagicMock()  # No async methods
        inner_cache.__dict__ = {}
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        with pytest.raises(NotImplementedError, match="does not support get_cached_response or generic get method"):
            await wrapper.get_cached_response("text", "operation", {})

    @pytest.mark.asyncio
    async def test_cache_response_with_warnings_enabled(self):
        """
        Test cache_response emits deprecation warnings per docstring.

        Verifies:
            cache_response method emits DeprecationWarning when warnings enabled

        Business Impact:
            Guides migration from legacy AI cache storage to generic cache methods

        Scenario:
            Given: Wrapper with warnings enabled
            When: cache_response is called
            Then: DeprecationWarning and log warning are emitted
        """
        inner_cache = AsyncMock()
        inner_cache.cache_response = AsyncMock()
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=True)

        with pytest.warns(DeprecationWarning, match="cache_response.*deprecated"):
            with patch('app.infrastructure.cache.compatibility.logger') as mock_logger:
                await wrapper.cache_response("text", "operation", {}, {"response": "data"})

                mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_response_forwards_to_ai_method(self):
        """
        Test cache_response forwards to AI-specific method per docstring.

        Verifies:
            When inner cache has cache_response method, calls are forwarded properly

        Business Impact:
            Maintains compatibility with existing AI cache storage during transition

        Scenario:
            Given: Inner cache with AI-specific cache_response method
            When: Legacy storage method is called through wrapper
            Then: Call is forwarded with all parameters including response data
        """
        inner_cache = AsyncMock()
        inner_cache.cache_response = AsyncMock()
        # Simulate real attribute existence
        inner_cache.__dict__ = {"cache_response": inner_cache.cache_response}
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        await wrapper.cache_response("text", "summarize", {"length": 50}, {"result": "summary"}, "question")

        inner_cache.cache_response.assert_called_once_with("text", "summarize", {"length": 50}, {"result": "summary"}, "question")

    @pytest.mark.asyncio
    async def test_cache_response_fallback_to_generic_cache(self):
        """
        Test cache_response falls back to generic cache methods per docstring.

        Verifies:
            When AI method unavailable, falls back to generic set with key generation

        Business Impact:
            Enables migration to generic cache while maintaining legacy storage interface

        Scenario:
            Given: Inner cache with generic methods but no AI-specific methods
            When: Legacy cache_response is called
            Then: Generic set is used with generated cache key and operation TTL
        """
        inner_cache = AsyncMock()
        inner_cache.set = AsyncMock()
        inner_cache._generate_cache_key = MagicMock(return_value="cache_key")
        inner_cache.operation_ttls = {"summarize": 1800}
        # Simulate instance attributes for fallback detection
        inner_cache.__dict__ = {
            "_generate_cache_key": inner_cache._generate_cache_key,
            "set": inner_cache.set
        }
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        await wrapper.cache_response("text", "summarize", {"length": 100}, {"summary": "result"})

        inner_cache._generate_cache_key.assert_called_once_with("text", "summarize", {"length": 100}, None)
        inner_cache.set.assert_called_once_with("cache_key", {"summary": "result"}, ttl=1800)

    @pytest.mark.asyncio
    async def test_cache_response_fallback_without_operation_ttls(self):
        """
        Test cache_response fallback uses None TTL when operation_ttls unavailable per docstring.

        Verifies:
            Generic cache fallback works without operation-specific TTL configuration

        Business Impact:
            Ensures compatibility even when inner cache doesn't have AI-specific TTL configuration

        Scenario:
            Given: Inner cache with generic methods but no operation_ttls
            When: Legacy cache_response is called
            Then: Generic set is used with None TTL
        """
        inner_cache = AsyncMock()
        inner_cache.set = AsyncMock()
        inner_cache._generate_cache_key = MagicMock(return_value="key")
        # No operation_ttls attribute
        inner_cache.__dict__ = {
            "_generate_cache_key": inner_cache._generate_cache_key,
            "set": inner_cache.set
        }
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        await wrapper.cache_response("text", "operation", {}, {"data": "result"})

        inner_cache.set.assert_called_once_with("key", {"data": "result"}, ttl=None)

    @pytest.mark.asyncio
    async def test_cache_response_raises_not_implemented(self):
        """
        Test cache_response raises NotImplementedError when methods unavailable per docstring.

        Verifies:
            When neither AI nor generic storage methods available, NotImplementedError is raised

        Business Impact:
            Prevents silent failures when cache doesn't support expected storage interface

        Scenario:
            Given: Inner cache without AI-specific or generic cache storage methods
            When: cache_response is called
            Then: NotImplementedError is raised with descriptive message
        """
        inner_cache = MagicMock()  # No async methods
        inner_cache.__dict__ = {}
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        with pytest.raises(NotImplementedError, match="does not support cache_response or generic set method"):
            await wrapper.cache_response("text", "operation", {}, {"response": "data"})


class TestCacheCompatibilityWrapperEdgeCases:
    """Test compatibility wrapper edge cases and error handling per docstring contracts."""

    def test_async_method_detection_with_async_mock(self):
        """
        Test async method detection works with AsyncMock per docstring.

        Verifies:
            Wrapper correctly identifies AsyncMock instances as async for testing compatibility

        Business Impact:
            Ensures compatibility wrapper works correctly in test environments with mocked async methods

        Scenario:
            Given: Inner cache with AsyncMock methods
            When: Legacy methods are called
            Then: AsyncMock methods are correctly identified as async and called
        """
        inner_cache = MagicMock()
        inner_cache.get_cached_response = AsyncMock(return_value={"test": "data"})
        # Simulate real attribute for _has_real_attr
        inner_cache.__dict__ = {"get_cached_response": inner_cache.get_cached_response}
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)

        # The method should be detected as async and handled properly
        async def test_async():
            result = await wrapper.get_cached_response("text", "op", {})
            return result

        result = asyncio.run(test_async())
        assert result == {"test": "data"}

    def test_async_method_detection_without_async_mock_import(self):
        """
        Test async method detection when AsyncMock unavailable per docstring.

        Verifies:
            Wrapper gracefully handles environments where AsyncMock is not available

        Business Impact:
            Ensures compatibility across different Python versions and test environments

        Scenario:
            Given: Environment where AsyncMock import fails
            When: AsyncMock detection is attempted
            Then: Detection gracefully falls back without AsyncMock support
        """
        # Test the import handling in the module
        # We can't easily test the import failure, but we can test the None case
        from app.infrastructure.cache.compatibility import AsyncMock as ImportedAsyncMock
        
        # The module should handle AsyncMock being None gracefully
        if ImportedAsyncMock is None:
            # If AsyncMock is None, async detection should still work with inspect
            inner_cache = MagicMock()
            
            async def async_method():
                return "result"
            
            inner_cache.get_cached_response = async_method
            inner_cache.__dict__ = {"get_cached_response": async_method}
            wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=False)
            
            # Should still detect as async using inspect.iscoroutinefunction
            result = asyncio.run(wrapper.get_cached_response("text", "op", {}))
            assert result == "result"

    def test_wrapper_with_mock_without_dict_attribute(self):
        """
        Test wrapper handles Mock objects without __dict__ per docstring.

        Verifies:
            Wrapper gracefully handles Mock objects that don't have __dict__ attribute

        Business Impact:
            Ensures robust testing support with various mock object configurations

        Scenario:
            Given: Mock object without __dict__ attribute
            When: Wrapper tries to access attributes
            Then: Fallback attribute detection works correctly
        """
        inner_cache = MagicMock()
        # Remove __dict__ to test fallback
        del inner_cache.__dict__
        inner_cache.test_method = MagicMock(return_value="result")
        wrapper = CacheCompatibilityWrapper(inner_cache)

        result = wrapper.test_method()
        assert result == "result"

    def test_wrapper_preserves_inner_cache_exceptions(self):
        """
        Test wrapper preserves exceptions from inner cache per docstring.

        Verifies:
            Exceptions raised by inner cache methods are properly propagated through wrapper

        Business Impact:
            Maintains proper error handling semantics during cache migration

        Scenario:
            Given: Inner cache that raises exceptions
            When: Methods are called through wrapper
            Then: Original exceptions are propagated unchanged
        """
        inner_cache = MagicMock()
        inner_cache.problem_method = MagicMock(side_effect=ValueError("Cache error"))
        wrapper = CacheCompatibilityWrapper(inner_cache)

        with pytest.raises(ValueError, match="Cache error"):
            wrapper.problem_method()


class TestCacheCompatibilityWrapperIntegration:
    """Test compatibility wrapper integration with various cache implementations per docstring contracts."""

    @pytest.mark.asyncio
    async def test_integration_with_redis_cache(self):
        """
        Test compatibility wrapper integrates with Redis cache per docstring.

        Verifies:
            Wrapper works correctly with Redis-based cache implementations

        Business Impact:
            Ensures legacy code continues working during migration to Redis cache

        Scenario:
            Given: Redis cache implementation as inner cache
            When: Legacy methods are called through wrapper
            Then: Redis cache methods are properly invoked
        """
        # Mock Redis cache with both old and new interfaces
        redis_cache = AsyncMock()
        redis_cache.get = AsyncMock(return_value={"redis": "data"})
        redis_cache.set = AsyncMock()
        redis_cache._generate_cache_key = MagicMock(return_value="redis:key:hash")
        redis_cache.__dict__ = {
            "get": redis_cache.get,
            "set": redis_cache.set,
            "_generate_cache_key": redis_cache._generate_cache_key
        }
        wrapper = CacheCompatibilityWrapper(redis_cache, emit_warnings=False)

        # Test legacy interface using generic fallback
        result = await wrapper.get_cached_response("text", "operation", {"param": "value"})
        
        assert result == {"redis": "data"}
        redis_cache._generate_cache_key.assert_called_once_with("text", "operation", {"param": "value"}, None)
        redis_cache.get.assert_called_once_with("redis:key:hash")

    @pytest.mark.asyncio
    async def test_integration_with_memory_cache(self):
        """
        Test compatibility wrapper integrates with memory cache per docstring.

        Verifies:
            Wrapper works correctly with in-memory cache implementations

        Business Impact:
            Enables legacy code to work with memory cache during development and testing

        Scenario:
            Given: Memory cache implementation as inner cache
            When: Legacy storage methods are called through wrapper
            Then: Memory cache storage methods are properly invoked
        """
        # Mock memory cache with generic interface
        memory_cache = AsyncMock()
        memory_cache.set = AsyncMock()
        memory_cache._generate_cache_key = MagicMock(return_value="mem:key")
        memory_cache.operation_ttls = {"sentiment": 900}
        memory_cache.__dict__ = {
            "set": memory_cache.set,
            "_generate_cache_key": memory_cache._generate_cache_key
        }
        wrapper = CacheCompatibilityWrapper(memory_cache, emit_warnings=False)

        # Test legacy storage using generic fallback
        await wrapper.cache_response("input text", "sentiment", {"confidence": 0.8}, {"sentiment": "positive"})

        memory_cache._generate_cache_key.assert_called_once_with("input text", "sentiment", {"confidence": 0.8}, None)
        memory_cache.set.assert_called_once_with("mem:key", {"sentiment": "positive"}, ttl=900)

    def test_integration_preserves_synchronous_methods(self):
        """
        Test compatibility wrapper preserves synchronous methods per docstring.

        Verifies:
            Wrapper correctly handles synchronous methods from inner cache

        Business Impact:
            Maintains compatibility with mixed sync/async cache implementations

        Scenario:
            Given: Cache with both sync and async methods
            When: Sync methods are accessed through wrapper
            Then: Sync methods work without async conversion
        """
        mixed_cache = MagicMock()
        mixed_cache.get_stats = MagicMock(return_value={"hits": 100, "misses": 20})
        mixed_cache.clear_cache = MagicMock()
        wrapper = CacheCompatibilityWrapper(mixed_cache)

        stats = wrapper.get_stats()
        wrapper.clear_cache()

        assert stats == {"hits": 100, "misses": 20}
        mixed_cache.get_stats.assert_called_once()
        mixed_cache.clear_cache.assert_called_once()

    def test_integration_with_custom_cache_implementation(self):
        """
        Test compatibility wrapper integrates with custom cache implementations per docstring.

        Verifies:
            Wrapper works with any cache implementation following expected patterns

        Business Impact:
            Enables migration flexibility by supporting various cache implementations

        Scenario:
            Given: Custom cache implementation with unique methods
            When: Methods are accessed through wrapper
            Then: Custom implementation methods are properly proxied
        """
        # Custom cache with unique interface
        custom_cache = MagicMock()
        custom_cache.custom_method = MagicMock(return_value="custom_result")
        custom_cache.specialized_operation = MagicMock(return_value={"custom": "data"})
        wrapper = CacheCompatibilityWrapper(custom_cache)

        result1 = wrapper.custom_method("param")
        result2 = wrapper.specialized_operation(option="value")

        assert result1 == "custom_result"
        assert result2 == {"custom": "data"}
        custom_cache.custom_method.assert_called_once_with("param")
        custom_cache.specialized_operation.assert_called_once_with(option="value")

    def test_migration_monitoring_through_warning_system(self):
        """
        Test migration progress monitoring through warning system per docstring.

        Verifies:
            Warning system enables tracking of migration progress across different usage patterns

        Business Impact:
            Provides visibility into migration progress and identifies remaining legacy usage

        Scenario:
            Given: Wrapper with warnings enabled and multiple legacy method calls
            When: Various legacy methods are accessed
            Then: Each legacy usage generates trackable warnings
        """
        inner_cache = MagicMock()
        inner_cache.get_cached_response = MagicMock(return_value="response")
        inner_cache.cache_response = MagicMock()
        inner_cache.invalidate_pattern = MagicMock()
        inner_cache.get_cache_stats = MagicMock(return_value={})
        wrapper = CacheCompatibilityWrapper(inner_cache, emit_warnings=True)

        with patch('app.infrastructure.cache.compatibility.logger') as mock_logger:
            # Access multiple legacy methods
            wrapper.get_cached_response("text", "op", {})("args")
            wrapper.cache_response("text", "op", {}, {})("args") 
            wrapper.invalidate_pattern("pattern")("args")
            wrapper.get_cache_stats()("args")

            # Should have logged warning for each legacy method
            assert mock_logger.warning.call_count == 4
            
            # Check that different methods were logged
            logged_methods = [call_args[0][0] for call_args in mock_logger.warning.call_args_list]
            assert any("get_cached_response" in log for log in logged_methods)
            assert any("cache_response" in log for log in logged_methods)
            assert any("invalidate_pattern" in log for log in logged_methods)
            assert any("get_cache_stats" in log for log in logged_methods)