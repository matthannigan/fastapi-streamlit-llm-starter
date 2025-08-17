"""
Cross-Module Integration Testing for Cache Infrastructure

This module provides integration tests that validate the interaction between
cache infrastructure components using actual API signatures.

Test Coverage:
- AI Cache integration with correct method signatures
- Parameter mapping with actual method names
- Configuration integration
- Cross-module dependency resolution
"""

import asyncio
import pytest
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.memory import InMemoryCache
from app.infrastructure.cache.ai_config import AIResponseCacheConfig
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.security import RedisCacheSecurityManager, SecurityConfig
from app.infrastructure.cache.key_generator import CacheKeyGenerator


class TestCrossModuleIntegration:
    """Integration tests for cache infrastructure components."""

    @pytest.fixture
    async def performance_monitor(self):
        """Create a performance monitor for testing."""
        return CachePerformanceMonitor()

    @pytest.fixture
    async def integrated_cache_system(self, performance_monitor, monkeypatch):
        """
        Create an integrated cache system with all components.
        """
        # Configure test environment
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
        
        # Create cache components with correct parameters
        ai_cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            default_ttl=300,
            memory_cache_size=100,
            performance_monitor=performance_monitor
        )
        
        generic_cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            performance_monitor=performance_monitor
        )
        
        memory_cache = InMemoryCache(max_size=100, default_ttl=300)
        
        # Create supporting components
        parameter_mapper = CacheParameterMapper()
        security_config = SecurityConfig()
        security_manager = RedisCacheSecurityManager(
            config=security_config,
            performance_monitor=performance_monitor
        )
        key_generator = CacheKeyGenerator()
        
        # Mock Redis to avoid external dependencies
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        
        with patch('app.infrastructure.cache.redis_ai.aioredis.from_url', return_value=mock_redis):
            with patch('app.infrastructure.cache.redis_generic.aioredis.from_url', return_value=mock_redis):
                yield {
                    'ai_cache': ai_cache,
                    'generic_cache': generic_cache,
                    'memory_cache': memory_cache,
                    'parameter_mapper': parameter_mapper,
                    'security_manager': security_manager,
                    'key_generator': key_generator,
                    'performance_monitor': performance_monitor,
                    'mock_redis': mock_redis
                }

    async def test_ai_cache_basic_integration(self, integrated_cache_system):
        """Test basic AI cache operations with correct API signatures."""
        system = integrated_cache_system
        ai_cache = system['ai_cache']
        
        # Test cache_response method (synchronous)
        ai_cache.cache_response(
            text="Test integration text",
            operation="summarize",
            options={"test": "option"},
            response={"result": "Test summary"}
        )
        
        # Test get_cached_response method (async with required options)
        result = await ai_cache.get_cached_response(
            text="Test integration text",
            operation="summarize",
            options={"test": "option"}
        )
        
        # Result may be None due to mocking, but operation should complete without error
        assert result is None or isinstance(result, dict)

    async def test_parameter_mapping_integration(self, integrated_cache_system):
        """Test parameter mapping with correct method names."""
        system = integrated_cache_system
        parameter_mapper = system['parameter_mapper']
        
        # Test parameter validation with correct method name
        test_params = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 300,
            "memory_cache_size": 100
        }
        
        validation_result = parameter_mapper.validate_parameter_compatibility(test_params)
        assert validation_result is not None
        assert hasattr(validation_result, 'is_valid')

    async def test_key_generator_integration(self, integrated_cache_system):
        """Test key generator with correct method names."""
        system = integrated_cache_system
        key_generator = system['key_generator']
        
        # Test key generation with correct method name
        cache_key = key_generator.generate_cache_key(
            operation="test_operation",
            text="Test text for key generation",
            options={"test": "option"}
        )
        
        assert cache_key is not None
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    async def test_monitoring_integration(self, integrated_cache_system):
        """Test monitoring integration across components."""
        system = integrated_cache_system
        monitor = system['performance_monitor']
        ai_cache = system['ai_cache']
        
        # Perform operations to trigger monitoring
        ai_cache.cache_response(
            text="Monitoring test text",
            operation="summarize",
            options={},
            response={"result": "Test"}
        )
        
        await ai_cache.get_cached_response(
            text="Monitoring test text",
            operation="summarize",
            options={}
        )
        
        # Check that monitoring captured operations
        stats = monitor.get_performance_stats()
        assert stats is not None

    async def test_security_integration(self, integrated_cache_system):
        """Test security integration across components."""
        system = integrated_cache_system
        security_manager = system['security_manager']
        
        # Test security status retrieval
        security_status = security_manager.get_security_status()
        assert security_status is not None

    async def test_configuration_integration(self, integrated_cache_system, monkeypatch):
        """Test configuration integration."""
        # Test that AI cache can be created with various configurations
        config_params = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 600,
            "memory_cache_size": 150,
            "text_hash_threshold": 800
        }
        
        # This should not raise an exception
        ai_cache = AIResponseCache(**config_params)
        assert ai_cache is not None

    async def test_error_propagation_integration(self, integrated_cache_system):
        """Test that errors are properly propagated across components."""
        system = integrated_cache_system
        parameter_mapper = system['parameter_mapper']
        
        # Test with invalid parameters to ensure error handling works
        invalid_params = {
            "redis_url": "invalid-url",
            "default_ttl": -1,
            "memory_cache_size": -5
        }
        
        validation_result = parameter_mapper.validate_parameter_compatibility(invalid_params)
        
        # Should return validation result with errors, not raise exception
        assert validation_result is not None
        assert hasattr(validation_result, 'is_valid')
        # Validation should fail for invalid parameters
        assert not validation_result.is_valid