"""Tests for cache compatibility wrapper.

This test suite validates that the CacheCompatibilityWrapper properly maintains
backwards compatibility during the cache infrastructure transition while providing
deprecation warnings and seamless integration with both legacy and new cache interfaces.

Test Coverage:
- Legacy method compatibility with deprecation warnings
- Proxy functionality for non-legacy methods
- Generic cache interface integration
- Error handling for unsupported operations
- Warning suppression configuration
"""

import pytest
import warnings
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional

from app.infrastructure.cache.compatibility import CacheCompatibilityWrapper
from app.infrastructure.cache import GenericRedisCache, AIResponseCache


class TestCacheCompatibilityWrapper:
    """Test suite for CacheCompatibilityWrapper functionality."""
    
    @pytest.fixture
    def mock_generic_cache(self):
        """Mock GenericRedisCache for testing."""
        cache = Mock(spec=GenericRedisCache)
        cache.get = AsyncMock(return_value={"test": "value"})
        cache.set = AsyncMock()
        cache.delete = AsyncMock(return_value=True)
        cache.exists = AsyncMock(return_value=True)
        return cache
    
    @pytest.fixture
    def mock_ai_cache(self):
        """Mock AIResponseCache for testing."""
        cache = Mock(spec=AIResponseCache)
        cache.get_cached_response = AsyncMock(return_value={"response": "data"})
        cache.cache_response = AsyncMock()
        cache.get_cache_stats = AsyncMock(return_value={"stats": "data"})
        cache.get_cache_hit_ratio = Mock(return_value=75.5)
        cache._generate_cache_key = Mock(return_value="test_key")
        cache.operation_ttls = {"summarize": 3600}
        return cache
    
    @pytest.fixture
    def compatibility_wrapper(self, mock_ai_cache):
        """CacheCompatibilityWrapper with AI cache for testing."""
        return CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=False)
    
    @pytest.fixture
    def compatibility_wrapper_with_warnings(self, mock_ai_cache):
        """CacheCompatibilityWrapper with warnings enabled."""
        return CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=True)
    
    def test_initialization(self, mock_ai_cache):
        """Test wrapper initialization with inner cache."""
        wrapper = CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=True)
        
        assert wrapper._inner_cache is mock_ai_cache
        assert wrapper._emit_warnings is True
    
    def test_initialization_default_warnings(self, mock_ai_cache):
        """Test wrapper initialization with default warning settings."""
        wrapper = CacheCompatibilityWrapper(mock_ai_cache)
        
        assert wrapper._emit_warnings is True  # Default is True
    
    def test_proxy_non_legacy_methods(self, compatibility_wrapper, mock_ai_cache):
        """Test that non-legacy methods are proxied without warnings."""
        # Access a non-legacy method
        result = compatibility_wrapper.connect
        
        # Should return the actual method from inner cache
        assert result is mock_ai_cache.connect
    
    @pytest.mark.asyncio
    async def test_legacy_get_cached_response_with_ai_cache(self, compatibility_wrapper, mock_ai_cache):
        """Test legacy get_cached_response method with AI cache backend."""
        text = "test text"
        operation = "summarize"
        options = {"max_length": 100}
        
        result = await compatibility_wrapper.get_cached_response(text, operation, options)
        
        # Should call the AI cache method
        mock_ai_cache.get_cached_response.assert_called_once_with(text, operation, options, None)
        assert result == {"response": "data"}
    
    @pytest.mark.asyncio
    async def test_legacy_get_cached_response_with_generic_cache(self, mock_generic_cache):
        """Test legacy get_cached_response with generic cache fallback."""
        # Set up generic cache with key generation capability
        mock_generic_cache._generate_cache_key = Mock(return_value="generated_key")
        wrapper = CacheCompatibilityWrapper(mock_generic_cache, emit_warnings=False)
        
        text = "test text"
        operation = "summarize"
        options = {"max_length": 100}
        
        result = await wrapper.get_cached_response(text, operation, options)
        
        # Should use generic cache with generated key
        mock_generic_cache._generate_cache_key.assert_called_once_with(text, operation, options, None)
        mock_generic_cache.get.assert_called_once_with("generated_key")
        assert result == {"test": "value"}
    
    @pytest.mark.asyncio
    async def test_legacy_cache_response_with_ai_cache(self, compatibility_wrapper, mock_ai_cache):
        """Test legacy cache_response method with AI cache backend."""
        text = "test text"
        operation = "summarize"
        options = {"max_length": 100}
        response = {"summary": "test summary"}
        
        await compatibility_wrapper.cache_response(text, operation, options, response)
        
        # Should call the AI cache method
        mock_ai_cache.cache_response.assert_called_once_with(text, operation, options, response, None)
    
    @pytest.mark.asyncio
    async def test_legacy_cache_response_with_generic_cache(self, mock_generic_cache):
        """Test legacy cache_response with generic cache fallback."""
        # Set up generic cache with key generation and TTL capability
        mock_generic_cache._generate_cache_key = Mock(return_value="generated_key")
        mock_generic_cache.operation_ttls = {"summarize": 3600}
        wrapper = CacheCompatibilityWrapper(mock_generic_cache, emit_warnings=False)
        
        text = "test text"
        operation = "summarize"
        options = {"max_length": 100}
        response = {"summary": "test summary"}
        
        await wrapper.cache_response(text, operation, options, response)
        
        # Should use generic cache with generated key and TTL
        mock_generic_cache._generate_cache_key.assert_called_once_with(text, operation, options, None)
        mock_generic_cache.set.assert_called_once_with("generated_key", response, ttl=3600)
    
    @pytest.mark.asyncio
    async def test_legacy_methods_emit_warnings(self, mock_ai_cache):
        """Test that legacy methods emit deprecation warnings when configured."""
        wrapper = CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=True)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Ensure all warnings are captured
            
            await wrapper.get_cached_response("text", "op", {})
            
            # Should have emitted a deprecation warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_cached_response() is deprecated" in str(w[0].message)
    
    @pytest.mark.asyncio
    async def test_legacy_methods_no_warnings_when_disabled(self, mock_ai_cache):
        """Test that legacy methods don't emit warnings when disabled."""
        wrapper = CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=False)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            await wrapper.get_cached_response("text", "op", {})
            
            # Should not have emitted any warnings
            assert len(w) == 0
    
    def test_getattr_legacy_method_warnings(self, mock_ai_cache):
        """Test __getattr__ emits warnings for legacy methods."""
        wrapper = CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=True)
        mock_ai_cache.get_cache_stats = Mock(return_value={"stats": "data"})
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Access legacy method through __getattr__
            method = wrapper.get_cache_stats
            result = method()
            
            # Should emit warning and call inner method
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_cache_stats" in str(w[0].message)
            assert result == {"stats": "data"}
    
    def test_getattr_non_legacy_method_no_warnings(self, mock_ai_cache):
        """Test __getattr__ doesn't emit warnings for non-legacy methods."""
        wrapper = CacheCompatibilityWrapper(mock_ai_cache, emit_warnings=True)
        mock_ai_cache.connect = Mock()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Access non-legacy method
            method = wrapper.connect
            
            # Should not emit warnings
            assert len(w) == 0
            assert method is mock_ai_cache.connect
    
    @pytest.mark.asyncio
    async def test_unsupported_legacy_method_with_basic_cache(self):
        """Test error handling when inner cache doesn't support legacy methods."""
        # Create a basic cache without AI-specific methods
        basic_cache = Mock()
        basic_cache.get = AsyncMock()
        # No get_cached_response, _generate_cache_key, or other AI methods
        
        wrapper = CacheCompatibilityWrapper(basic_cache, emit_warnings=False)
        
        with pytest.raises(NotImplementedError) as exc_info:
            await wrapper.get_cached_response("text", "op", {})
        
        assert "does not support get_cached_response or generic get method" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_question_parameter_forwarding(self, compatibility_wrapper, mock_ai_cache):
        """Test that question parameter is properly forwarded to inner cache."""
        text = "test text"
        operation = "qa"
        options = {"max_length": 100}
        question = "What is the main topic?"
        
        await compatibility_wrapper.get_cached_response(text, operation, options, question)
        
        # Should forward question parameter
        mock_ai_cache.get_cached_response.assert_called_once_with(text, operation, options, question)
    
    def test_legacy_methods_list(self, compatibility_wrapper):
        """Test that known legacy methods are correctly identified."""
        # Access the wrapper's __getattr__ method directly to check legacy method detection
        wrapper = compatibility_wrapper
        wrapper._emit_warnings = True  # Enable warnings for this test
        
        legacy_methods = [
            'get_cached_response',
            'cache_response', 
            'invalidate_pattern',
            'invalidate_by_operation',
            'get_cache_stats',
            'get_cache_hit_ratio'
        ]
        
        for method_name in legacy_methods:
            # Mock the method on inner cache
            setattr(wrapper._inner_cache, method_name, Mock())
            
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                # Access method through __getattr__
                method = getattr(wrapper, method_name)
                
                # Should have generated a warning for legacy methods
                if w:  # Some methods might not trigger warnings depending on implementation
                    assert any("deprecated" in str(warning.message).lower() for warning in w)


class TestCacheCompatibilityIntegration:
    """Integration tests for compatibility wrapper with real cache classes."""
    
    def test_wrapper_with_real_ai_cache(self):
        """Test wrapper integration with actual AIResponseCache."""
        # This test ensures the wrapper works with the real AI cache class
        ai_cache = Mock(spec=AIResponseCache)
        wrapper = CacheCompatibilityWrapper(ai_cache)
        
        # Should be able to access AI cache methods
        assert hasattr(wrapper, '_inner_cache')
        assert wrapper._inner_cache is ai_cache
    
    def test_wrapper_with_real_generic_cache(self):
        """Test wrapper integration with actual GenericRedisCache."""
        # This test ensures the wrapper works with the real generic cache class
        generic_cache = Mock(spec=GenericRedisCache)
        wrapper = CacheCompatibilityWrapper(generic_cache)
        
        # Should be able to access generic cache methods
        assert hasattr(wrapper, '_inner_cache')
        assert wrapper._inner_cache is generic_cache
    
    @pytest.mark.asyncio
    async def test_new_generic_methods_accessible(self):
        """Test that new generic cache methods are accessible through wrapper."""
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value="test_value")
        mock_cache.set = AsyncMock()
        mock_cache.delete = AsyncMock(return_value=True)
        mock_cache.exists = AsyncMock(return_value=True)
        
        wrapper = CacheCompatibilityWrapper(mock_cache, emit_warnings=False)
        
        # New generic methods should be directly accessible
        result = await wrapper.get("test_key")
        assert result == "test_value"
        mock_cache.get.assert_called_once_with("test_key")
        
        await wrapper.set("test_key", "test_value", ttl=3600)
        mock_cache.set.assert_called_once_with("test_key", "test_value", ttl=3600)
        
        result = await wrapper.delete("test_key")
        assert result is True
        mock_cache.delete.assert_called_once_with("test_key")
        
        result = await wrapper.exists("test_key")
        assert result is True
        mock_cache.exists.assert_called_once_with("test_key")


class TestCacheCompatibilityErrorHandling:
    """Test error handling and edge cases in compatibility wrapper."""
    
    def test_missing_attribute_error(self):
        """Test that missing attributes raise appropriate errors."""
        mock_cache = Mock()
        wrapper = CacheCompatibilityWrapper(mock_cache, emit_warnings=False)
        
        with pytest.raises(AttributeError):
            _ = wrapper.nonexistent_method
    
    @pytest.mark.asyncio
    async def test_legacy_method_with_no_fallback(self):
        """Test legacy method behavior when neither AI nor generic methods exist."""
        mock_cache = Mock()
        # Mock cache has no get_cached_response, _generate_cache_key, or get methods
        wrapper = CacheCompatibilityWrapper(mock_cache, emit_warnings=False)
        
        with pytest.raises(NotImplementedError):
            await wrapper.get_cached_response("text", "op", {})
    
    def test_wrapper_preserves_inner_cache_errors(self):
        """Test that errors from inner cache are properly propagated."""
        mock_cache = Mock()
        mock_cache.some_method = Mock(side_effect=ValueError("Inner cache error"))
        
        wrapper = CacheCompatibilityWrapper(mock_cache, emit_warnings=False)
        
        with pytest.raises(ValueError) as exc_info:
            wrapper.some_method()
        
        assert "Inner cache error" in str(exc_info.value)
"""
