"""Tests for dependency injection providers."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

from app.dependencies import get_cache_service, get_text_processor_service, get_settings
from app.services.cache import AIResponseCache
from app.services.text_processor import TextProcessorService
from app.config import Settings


class TestDependencyInjection:
    """Test dependency injection providers."""
    
    @pytest.mark.asyncio
    async def test_get_cache_service_creates_configured_instance(self):
        """Test that get_cache_service creates a properly configured cache instance and calls connect."""
        # Create a mock settings object
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://test-host:6379"
        
        # Mock the AIResponseCache class and its connect method
        with patch('app.dependencies.AIResponseCache') as mock_cache_class:
            mock_cache_instance = MagicMock(spec=AIResponseCache)
            mock_cache_instance.connect = AsyncMock()
            mock_cache_class.return_value = mock_cache_instance
            
            # Get cache service with mock settings
            cache_service = await get_cache_service(mock_settings)
            
            # Verify AIResponseCache was called with correct parameters
            mock_cache_class.assert_called_once_with(
                redis_url="redis://test-host:6379",
                default_ttl=3600
            )
            
            # Verify connect was called
            mock_cache_instance.connect.assert_called_once()
            
            # Verify the correct instance is returned
            assert cache_service is mock_cache_instance

    @pytest.mark.asyncio
    async def test_get_cache_service_graceful_degradation_when_redis_unavailable(self):
        """Test that get_cache_service works gracefully when Redis connection fails."""
        # Create a mock settings object
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://unavailable-host:6379"
        
        # Mock the AIResponseCache class and make connect() return False (Redis unavailable)
        with patch('app.dependencies.AIResponseCache') as mock_cache_class:
            mock_cache_instance = MagicMock(spec=AIResponseCache)
            mock_cache_instance.connect = AsyncMock(return_value=False)  # Redis unavailable
            mock_cache_class.return_value = mock_cache_instance
            
            # Get cache service with mock settings - should not raise exception
            cache_service = await get_cache_service(mock_settings)
            
            # Verify AIResponseCache was called with correct parameters
            mock_cache_class.assert_called_once_with(
                redis_url="redis://unavailable-host:6379",
                default_ttl=3600
            )
            
            # Verify connect was called (and returned False)
            mock_cache_instance.connect.assert_called_once()
            
            # Verify the cache instance is still returned (for graceful degradation)
            assert cache_service is mock_cache_instance

    @pytest.mark.asyncio
    async def test_get_cache_service_when_connect_raises_exception(self):
        """Test that get_cache_service handles exceptions during connect gracefully."""
        # Create a mock settings object
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://bad-config:6379"
        
        # Mock the AIResponseCache class and make connect() raise an exception
        with patch('app.dependencies.AIResponseCache') as mock_cache_class:
            mock_cache_instance = MagicMock(spec=AIResponseCache)
            mock_cache_instance.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_cache_class.return_value = mock_cache_instance
            
            # Mock logger to verify warning is logged
            with patch('app.dependencies.logger') as mock_logger:
                # Should not raise exception - should handle gracefully
                cache_service = await get_cache_service(mock_settings)
                
                # Verify connect was attempted
                mock_cache_instance.connect.assert_called_once()
                
                # Verify warning was logged
                mock_logger.warning.assert_called_once_with(
                    "Failed to connect to Redis: Connection failed. Cache will operate without persistence."
                )
                
                # Verify the cache instance is still returned (graceful degradation)
                assert cache_service is mock_cache_instance

    @pytest.mark.asyncio
    async def test_get_cache_service_real_integration_with_unavailable_redis(self):
        """Test real integration with unavailable Redis server (no mocking)."""
        # Create settings with an unavailable Redis URL
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://nonexistent-host:6379"
        
        # Don't mock anything - use real AIResponseCache
        cache_service = await get_cache_service(mock_settings)
        
        # Verify we get a cache service instance even with unavailable Redis
        assert isinstance(cache_service, AIResponseCache)
        assert cache_service.redis_url == "redis://nonexistent-host:6379"
        assert cache_service.default_ttl == 3600
        
        # Verify cache operations work gracefully without Redis
        # These should not raise exceptions
        result = await cache_service.get_cached_response("test", "summarize", {})
        assert result is None  # Should return None when Redis unavailable
        
        # This should not raise an exception
        await cache_service.cache_response("test", "summarize", {}, {"result": "test"})
        
        # Cache stats should indicate unavailable
        stats = await cache_service.get_cache_stats()
        assert stats["status"] == "unavailable"
        assert stats["keys"] == 0
        
    def test_get_text_processor_service_uses_injected_cache(self):
        """Test that get_text_processor_service uses the injected cache service."""
        # Create a mock cache service
        mock_cache = MagicMock(spec=AIResponseCache)
        
        # Mock the environment variable for text processor
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock the Agent constructor to avoid actual AI initialization
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Get text processor service with mock cache
                text_processor = get_text_processor_service(mock_cache)
                
                # Verify it's the right type and uses the injected cache
                assert isinstance(text_processor, TextProcessorService)
                assert text_processor.cache_service is mock_cache
                
    @pytest.mark.asyncio        
    async def test_dependency_chain_integration(self):
        """Test that the full dependency chain works together."""
        # Mock environment variable
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock Agent constructor
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Mock AIResponseCache to avoid actual Redis connection
                with patch('app.dependencies.AIResponseCache') as mock_cache_class:
                    mock_cache_instance = MagicMock(spec=AIResponseCache)
                    mock_cache_instance.connect = AsyncMock()
                    mock_cache_class.return_value = mock_cache_instance
                    
                    # Get settings
                    settings = get_settings()
                    
                    # Get cache service using settings
                    cache_service = await get_cache_service(settings)
                    
                    # Get text processor using cache service
                    text_processor = get_text_processor_service(cache_service)
                    
                    # Verify the chain is properly connected
                    assert cache_service is mock_cache_instance
                    assert isinstance(text_processor, TextProcessorService)
                    assert text_processor.cache_service is cache_service
                    
                    # Verify cache was created with settings redis_url
                    mock_cache_class.assert_called_once_with(
                        redis_url=settings.redis_url,
                        default_ttl=3600
                    )
                
    @pytest.mark.asyncio
    async def test_cache_service_uses_settings_redis_url(self):
        """Test that cache service uses redis_url from settings."""
        # Create settings with custom redis URL
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://custom-redis:9999"
        
        # Mock AIResponseCache
        with patch('app.dependencies.AIResponseCache') as mock_cache_class:
            mock_cache_instance = MagicMock(spec=AIResponseCache)
            mock_cache_instance.connect = AsyncMock()
            mock_cache_class.return_value = mock_cache_instance
            
            cache_service = await get_cache_service(mock_settings)
            
            # Verify cache was created with custom redis URL
            mock_cache_class.assert_called_once_with(
                redis_url="redis://custom-redis:9999",
                default_ttl=3600
            )
            assert cache_service is mock_cache_instance 