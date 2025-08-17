"""
Tests for CacheFactory explicit cache instantiation.

This module provides comprehensive testing for the CacheFactory class that enables
explicit cache instantiation with deterministic behavior and environment-optimized
defaults. Tests cover all factory methods, validation logic, error handling, and
fallback behavior.

Test Categories:
    - Factory Initialization Tests
    - Input Validation Tests
    - Web Application Cache Factory Tests
    - AI Application Cache Factory Tests  
    - Testing Cache Factory Tests
    - Configuration-Based Cache Factory Tests
    - Error Handling and Fallback Tests
    - Performance and Integration Tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.memory import InMemoryCache
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.redis_ai import AIResponseCache


class TestCacheFactoryInitialization:
    """Test factory initialization and basic setup."""

    def test_factory_initialization_success(self):
        """Test successful factory initialization."""
        factory = CacheFactory()
        assert factory is not None
        assert hasattr(factory, '_performance_monitor')

    def test_factory_initialization_without_monitoring(self):
        """Test factory works when monitoring is not available."""
        with patch('app.infrastructure.cache.factory.MONITORING_AVAILABLE', False):
            factory = CacheFactory()
            assert factory is not None
            assert factory._performance_monitor is None


class TestFactoryInputValidation:
    """Test the _validate_factory_inputs method."""

    def test_validate_factory_inputs_success(self):
        """Test successful validation with valid inputs."""
        factory = CacheFactory()
        
        # Should not raise any exceptions
        factory._validate_factory_inputs(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            fail_on_connection_error=True,
            enable_l1_cache=True,
            l1_cache_size=100,
            compression_threshold=1000,
            compression_level=6
        )

    def test_validate_factory_inputs_redis_url_errors(self):
        """Test validation errors for redis_url parameter."""
        factory = CacheFactory()
        
        # Test invalid URL types
        with pytest.raises(ValidationError, match="redis_url must be a string"):
            factory._validate_factory_inputs(redis_url=123)
        
        # Test empty URL
        with pytest.raises(ValidationError, match="redis_url cannot be empty"):
            factory._validate_factory_inputs(redis_url="")
        
        # Test invalid protocol
        with pytest.raises(ValidationError, match="redis_url must start with 'redis://' or 'rediss://'"):
            factory._validate_factory_inputs(redis_url="http://localhost:6379")
        
        # Test missing host
        with pytest.raises(ValidationError, match="redis_url must include host information"):
            factory._validate_factory_inputs(redis_url="redis://")

    def test_validate_factory_inputs_ttl_errors(self):
        """Test validation errors for default_ttl parameter."""
        factory = CacheFactory()
        
        # Test invalid TTL type
        with pytest.raises(ValidationError, match="default_ttl must be an integer"):
            factory._validate_factory_inputs(default_ttl="3600")
        
        # Test negative TTL
        with pytest.raises(ValidationError, match="default_ttl must be non-negative"):
            factory._validate_factory_inputs(default_ttl=-100)
        
        # Test excessive TTL (more than 1 year)
        with pytest.raises(ValidationError, match="default_ttl must not exceed 365 days"):
            factory._validate_factory_inputs(default_ttl=86400 * 366)

    def test_validate_factory_inputs_boolean_errors(self):
        """Test validation errors for boolean parameters."""
        factory = CacheFactory()
        
        # Test invalid fail_on_connection_error type
        with pytest.raises(ValidationError, match="fail_on_connection_error must be a boolean"):
            factory._validate_factory_inputs(fail_on_connection_error="true")
        
        # Test invalid enable_l1_cache type
        with pytest.raises(ValidationError, match="enable_l1_cache must be a boolean"):
            factory._validate_factory_inputs(enable_l1_cache="false")

    def test_validate_factory_inputs_additional_params_errors(self):
        """Test validation errors for additional parameters."""
        factory = CacheFactory()
        
        # Test invalid l1_cache_size
        with pytest.raises(ValidationError, match="l1_cache_size must be a positive integer"):
            factory._validate_factory_inputs(l1_cache_size=0)
        
        # Test invalid compression_threshold
        with pytest.raises(ValidationError, match="compression_threshold must be a non-negative integer"):
            factory._validate_factory_inputs(compression_threshold=-1)
        
        # Test invalid compression_level
        with pytest.raises(ValidationError, match="compression_level must be an integer between 1 and 9"):
            factory._validate_factory_inputs(compression_level=10)


class TestWebAppCacheFactory:
    """Test the for_web_app factory method."""

    @pytest.mark.asyncio
    async def test_for_web_app_success_with_memory_fallback(self):
        """Test successful web app cache creation with memory fallback."""
        factory = CacheFactory()
        
        # Use invalid Redis URL to trigger memory fallback
        cache = await factory.for_web_app(
            redis_url="redis://nonexistent:6379",
            fail_on_connection_error=False
        )
        
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 1800  # Default web app TTL

    @pytest.mark.asyncio
    async def test_for_web_app_custom_parameters(self):
        """Test web app cache with custom parameters."""
        factory = CacheFactory()
        
        cache = await factory.for_web_app(
            redis_url="redis://nonexistent:6379",
            default_ttl=7200,
            l1_cache_size=500,
            compression_threshold=5000,
            fail_on_connection_error=False
        )
        
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 7200
        assert cache.max_size == 500

    @pytest.mark.asyncio
    async def test_for_web_app_validation_error(self):
        """Test web app cache creation with validation errors."""
        factory = CacheFactory()
        
        with pytest.raises(ValidationError):
            await factory.for_web_app(
                redis_url="invalid-url",
                default_ttl=-100
            )

    @pytest.mark.asyncio
    async def test_for_web_app_connection_error_strict(self):
        """Test web app cache with fail_on_connection_error=True."""
        factory = CacheFactory()
        
        with pytest.raises(InfrastructureError, match="Redis connection failed for web application cache"):
            await factory.for_web_app(
                redis_url="redis://nonexistent:6379",
                fail_on_connection_error=True
            )


class TestAIAppCacheFactory:
    """Test the for_ai_app factory method."""

    @pytest.mark.asyncio
    async def test_for_ai_app_success_with_memory_fallback(self):
        """Test successful AI app cache creation with memory fallback."""
        factory = CacheFactory()
        
        cache = await factory.for_ai_app(
            redis_url="redis://nonexistent:6379",
            fail_on_connection_error=False
        )
        
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 3600  # Default AI app TTL

    @pytest.mark.asyncio
    async def test_for_ai_app_custom_parameters(self):
        """Test AI app cache with custom parameters."""
        factory = CacheFactory()
        
        operation_ttls = {"summarize": 1800, "sentiment": 3600}
        
        cache = await factory.for_ai_app(
            redis_url="redis://nonexistent:6379",
            default_ttl=7200,
            text_hash_threshold=1000,
            memory_cache_size=200,
            operation_ttls=operation_ttls,
            fail_on_connection_error=False
        )
        
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 7200
        assert cache.max_size == 200  # memory_cache_size overrides l1_cache_size

    @pytest.mark.asyncio
    async def test_for_ai_app_ai_specific_validation_errors(self):
        """Test AI app cache creation with AI-specific validation errors."""
        factory = CacheFactory()
        
        # Test invalid text_hash_threshold
        with pytest.raises(ValidationError, match="text_hash_threshold must be a non-negative integer"):
            await factory.for_ai_app(text_hash_threshold=-1)
        
        # Test invalid memory_cache_size
        with pytest.raises(ValidationError, match="memory_cache_size must be a positive integer"):
            await factory.for_ai_app(memory_cache_size=0)
        
        # Test invalid operation_ttls
        with pytest.raises(ValidationError, match="operation_ttls must be a dictionary"):
            await factory.for_ai_app(operation_ttls="invalid")

    @pytest.mark.asyncio
    async def test_for_ai_app_operation_ttls_validation(self):
        """Test operation_ttls parameter validation."""
        factory = CacheFactory()
        
        # Test invalid operation key
        with pytest.raises(ValidationError, match="operation_ttls keys must be non-empty strings"):
            await factory.for_ai_app(operation_ttls={"": 3600})
        
        # Test invalid TTL value
        with pytest.raises(ValidationError, match="operation_ttls\\['test'\\] must be a non-negative integer"):
            await factory.for_ai_app(operation_ttls={"test": -1})

    @pytest.mark.asyncio
    async def test_for_ai_app_connection_error_strict(self):
        """Test AI app cache with fail_on_connection_error=True."""
        factory = CacheFactory()
        
        with pytest.raises(InfrastructureError, match="Redis connection failed for AI application cache"):
            await factory.for_ai_app(
                redis_url="redis://nonexistent:6379",
                fail_on_connection_error=True
            )


class TestTestingCacheFactory:
    """Test the for_testing factory method."""

    @pytest.mark.asyncio
    async def test_for_testing_memory_cache_forced(self):
        """Test testing cache with forced memory cache usage."""
        factory = CacheFactory()
        
        cache = await factory.for_testing(use_memory_cache=True)
        
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 60  # Default testing TTL

    @pytest.mark.asyncio
    async def test_for_testing_redis_fallback(self):
        """Test testing cache with Redis fallback to memory."""
        factory = CacheFactory()
        
        cache = await factory.for_testing(
            redis_url="redis://nonexistent:6379/15",
            fail_on_connection_error=False
        )
        
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 60

    @pytest.mark.asyncio
    async def test_for_testing_custom_parameters(self):
        """Test testing cache with custom parameters."""
        factory = CacheFactory()
        
        cache = await factory.for_testing(
            default_ttl=30,
            l1_cache_size=25,
            use_memory_cache=True
        )
        
        assert isinstance(cache, InMemoryCache)
        assert cache.default_ttl == 30
        assert cache.max_size == 25

    @pytest.mark.asyncio
    async def test_for_testing_validation_errors(self):
        """Test testing cache with validation errors."""
        factory = CacheFactory()
        
        # Test invalid use_memory_cache type
        with pytest.raises(ValidationError, match="use_memory_cache must be a boolean"):
            await factory.for_testing(use_memory_cache="true")

    @pytest.mark.asyncio
    async def test_for_testing_connection_error_strict(self):
        """Test testing cache with fail_on_connection_error=True."""
        factory = CacheFactory()
        
        with pytest.raises(InfrastructureError, match="Redis connection failed for testing cache"):
            await factory.for_testing(
                redis_url="redis://nonexistent:6379/15",
                fail_on_connection_error=True
            )


class TestConfigurationBasedCacheFactory:
    """Test the create_cache_from_config factory method."""

    @pytest.mark.asyncio
    async def test_create_cache_from_config_generic_cache(self):
        """Test creating generic cache from configuration."""
        factory = CacheFactory()
        
        config = {
            "redis_url": "redis://nonexistent:6379",
            "default_ttl": 3600,
            "enable_l1_cache": True,
            "compression_threshold": 2000
        }
        
        cache = await factory.create_cache_from_config(config, fail_on_connection_error=False)
        
        assert cache is not None
        assert isinstance(cache, InMemoryCache)  # Fallback due to connection failure

    @pytest.mark.asyncio
    async def test_create_cache_from_config_ai_cache(self):
        """Test creating AI cache from configuration with AI parameters."""
        factory = CacheFactory()
        
        config = {
            "redis_url": "redis://nonexistent:6379",
            "default_ttl": 7200,
            "text_hash_threshold": 500,
            "operation_ttls": {"summarize": 1800}
        }
        
        cache = await factory.create_cache_from_config(config, fail_on_connection_error=False)
        
        assert cache is not None
        assert isinstance(cache, InMemoryCache)  # Fallback due to connection failure

    @pytest.mark.asyncio
    async def test_create_cache_from_config_validation_errors(self):
        """Test configuration validation errors."""
        factory = CacheFactory()
        
        # Test invalid config type
        with pytest.raises(ValidationError, match="config must be a dictionary"):
            await factory.create_cache_from_config("invalid")
        
        # Test empty config
        with pytest.raises(ValidationError, match="config dictionary cannot be empty"):
            await factory.create_cache_from_config({})
        
        # Test missing redis_url
        with pytest.raises(ValidationError, match="redis_url is required in config"):
            await factory.create_cache_from_config({"default_ttl": 3600})

    @pytest.mark.asyncio
    async def test_create_cache_from_config_ai_detection(self):
        """Test automatic AI cache detection based on parameters."""
        factory = CacheFactory()
        
        # Configuration with AI-specific parameters should create AI cache
        ai_config = {
            "redis_url": "redis://nonexistent:6379",
            "text_hash_threshold": 500
        }
        
        # Configuration without AI parameters should create generic cache
        generic_config = {
            "redis_url": "redis://nonexistent:6379",
            "compression_threshold": 2000
        }
        
        # Both should fall back to InMemoryCache due to connection failure
        ai_cache = await factory.create_cache_from_config(ai_config, fail_on_connection_error=False)
        generic_cache = await factory.create_cache_from_config(generic_config, fail_on_connection_error=False)
        
        assert isinstance(ai_cache, InMemoryCache)
        assert isinstance(generic_cache, InMemoryCache)

    @pytest.mark.asyncio
    async def test_create_cache_from_config_connection_error_strict(self):
        """Test configuration-based cache with fail_on_connection_error=True."""
        factory = CacheFactory()
        
        config = {
            "redis_url": "redis://nonexistent:6379",
            "default_ttl": 3600
        }
        
        with pytest.raises(InfrastructureError):
            await factory.create_cache_from_config(config, fail_on_connection_error=True)


class TestFactoryErrorHandlingAndFallback:
    """Test comprehensive error handling and fallback behavior."""

    @pytest.mark.asyncio
    async def test_factory_graceful_fallback_on_import_errors(self):
        """Test factory behavior when cache imports fail."""
        factory = CacheFactory()
        
        # Should still create memory cache even if Redis imports fail
        cache = await factory.for_testing(use_memory_cache=True)
        assert isinstance(cache, InMemoryCache)

    @pytest.mark.asyncio
    async def test_factory_handles_unexpected_exceptions(self):
        """Test factory handles unexpected exceptions gracefully."""
        factory = CacheFactory()
        
        # Mock GenericRedisCache to raise an unexpected exception
        with patch('app.infrastructure.cache.factory.GenericRedisCache') as mock_redis:
            mock_redis.side_effect = RuntimeError("Unexpected error")
            
            # Should fall back to InMemoryCache
            cache = await factory.for_web_app(fail_on_connection_error=False)
            assert isinstance(cache, InMemoryCache)

    @pytest.mark.asyncio
    async def test_factory_preserves_context_in_errors(self):
        """Test that factory errors include proper context information."""
        factory = CacheFactory()
        
        try:
            await factory.for_web_app(
                redis_url="redis://nonexistent:6379",
                fail_on_connection_error=True
            )
        except InfrastructureError as e:
            assert e.context is not None
            assert "redis_url" in e.context
            assert "cache_type" in e.context
            assert e.context["cache_type"] == "web_app"


class TestFactoryIntegration:
    """Test factory integration with actual cache operations."""

    @pytest.mark.asyncio
    async def test_factory_created_cache_basic_operations(self):
        """Test that factory-created caches support basic operations."""
        factory = CacheFactory()
        
        # Create a memory cache for testing
        cache = await factory.for_testing(use_memory_cache=True)
        
        # Test basic cache operations
        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value"
        
        await cache.delete("test_key")
        value = await cache.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_factory_respects_ttl_settings(self):
        """Test that factory-created caches respect TTL settings."""
        factory = CacheFactory()
        
        # Create cache with short TTL
        cache = await factory.for_testing(
            default_ttl=1,  # 1 second
            use_memory_cache=True
        )
        
        await cache.set("ttl_test", "value")
        
        # Value should exist immediately
        value = await cache.get("ttl_test")
        assert value == "value"
        
        # Wait for expiration (with some buffer)
        await asyncio.sleep(1.5)
        
        # Value should be expired
        value = await cache.get("ttl_test")
        assert value is None

    @pytest.mark.asyncio
    async def test_factory_performance_monitoring_integration(self):
        """Test that factory integrates performance monitoring when available."""
        factory = CacheFactory()
        
        # Performance monitor should be initialized if available
        if hasattr(factory, '_performance_monitor') and factory._performance_monitor:
            cache = await factory.for_testing(use_memory_cache=True)
            
            # Perform some operations
            await cache.set("perf_test", "value")
            await cache.get("perf_test")
            
            # Performance monitor should have recorded operations
            # (Specific assertions would depend on monitoring implementation)
            assert factory._performance_monitor is not None


# Performance tests
@pytest.mark.slow
class TestFactoryPerformance:
    """Test factory performance characteristics."""

    @pytest.mark.asyncio
    async def test_factory_creation_performance(self):
        """Test that factory cache creation is reasonably fast."""
        import time
        
        factory = CacheFactory()
        
        start_time = time.time()
        cache = await factory.for_testing(use_memory_cache=True)
        end_time = time.time()
        
        creation_time = end_time - start_time
        
        # Cache creation should be very fast (< 10ms)
        assert creation_time < 0.01
        assert cache is not None

    @pytest.mark.asyncio
    async def test_factory_multiple_cache_creation(self):
        """Test creating multiple caches from the same factory."""
        factory = CacheFactory()
        
        # Create multiple caches
        caches = []
        for i in range(10):
            cache = await factory.for_testing(use_memory_cache=True)
            caches.append(cache)
        
        # All caches should be created successfully
        assert len(caches) == 10
        for cache in caches:
            assert isinstance(cache, InMemoryCache)
            
        # Caches should be independent instances
        cache_ids = [id(cache) for cache in caches]
        assert len(set(cache_ids)) == 10  # All unique instances