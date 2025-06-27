"""Tests for dependency injection providers."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

from app.dependencies import get_cache_service, get_settings
from app.api.v1.deps import get_text_processor, get_text_processor_service
from app.infrastructure.cache import AIResponseCache
from app.services.text_processor import TextProcessorService
from app.config import Settings


def create_mock_settings(**overrides):
    """Create a properly mocked Settings object with all required attributes."""
    mock_settings = MagicMock(spec=Settings)
    
    # Set default values for all required attributes
    mock_settings.gemini_api_key = "test_gemini_key"
    mock_settings.ai_model = "gemini-2.0-flash-exp"
    mock_settings.redis_url = "redis://test:6379"
    
    # Cache configuration attributes
    mock_settings.cache_text_hash_threshold = 1000
    mock_settings.cache_compression_threshold = 1000
    mock_settings.cache_compression_level = 6
    mock_settings.cache_default_ttl = 3600
    mock_settings.cache_text_size_tiers = {'small': 500, 'medium': 5000, 'large': 50000}
    mock_settings.cache_memory_cache_size = 100
    
    # Resilience strategy attributes
    mock_settings.summarize_resilience_strategy = "balanced"
    mock_settings.sentiment_resilience_strategy = "aggressive"
    mock_settings.key_points_resilience_strategy = "balanced"
    mock_settings.questions_resilience_strategy = "balanced"
    mock_settings.qa_resilience_strategy = "conservative"
    
    # Apply any overrides
    for key, value in overrides.items():
        setattr(mock_settings, key, value)
    
    return mock_settings


class TestDependencyInjection:
    """Test dependency injection providers."""
    
    @pytest.mark.asyncio
    async def test_get_cache_service_creates_configured_instance(self):
        """Test that get_cache_service creates a properly configured cache instance and calls connect."""
        # Create a mock settings object
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://test-host:6379"
        mock_settings.cache_text_hash_threshold = 1000
        mock_settings.cache_compression_threshold = 1000
        mock_settings.cache_compression_level = 6
        mock_settings.cache_default_ttl = 3600
        mock_settings.cache_text_size_tiers = {'small': 500, 'medium': 5000, 'large': 50000}
        mock_settings.cache_memory_cache_size = 100
        
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
                default_ttl=3600,
                text_hash_threshold=1000,
                compression_threshold=1000,
                compression_level=6,
                text_size_tiers={'small': 500, 'medium': 5000, 'large': 50000},
                memory_cache_size=100
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
        mock_settings.cache_text_hash_threshold = 1000
        mock_settings.cache_compression_threshold = 1000
        mock_settings.cache_compression_level = 6
        mock_settings.cache_default_ttl = 3600
        mock_settings.cache_text_size_tiers = {'small': 500, 'medium': 5000, 'large': 50000}
        mock_settings.cache_memory_cache_size = 100
        
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
                default_ttl=3600,
                text_hash_threshold=1000,
                compression_threshold=1000,
                compression_level=6,
                text_size_tiers={'small': 500, 'medium': 5000, 'large': 50000},
                memory_cache_size=100
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
        mock_settings.cache_text_hash_threshold = 1000
        mock_settings.cache_compression_threshold = 1000
        mock_settings.cache_compression_level = 6
        mock_settings.cache_default_ttl = 3600
        mock_settings.cache_text_size_tiers = {'small': 500, 'medium': 5000, 'large': 50000}
        mock_settings.cache_memory_cache_size = 100
        
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
        mock_settings.cache_text_hash_threshold = 1000
        mock_settings.cache_compression_threshold = 1000
        mock_settings.cache_compression_level = 6
        mock_settings.cache_default_ttl = 3600
        mock_settings.cache_text_size_tiers = {'small': 500, 'medium': 5000, 'large': 50000}
        mock_settings.cache_memory_cache_size = 100
        
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
        assert stats["redis"]["status"] == "unavailable"
        assert stats["redis"]["keys"] == 0
        
    def test_get_text_processor_service_uses_injected_cache(self):
        """Test that get_text_processor_service uses the injected cache service."""
        # Create mock dependencies
        mock_settings = create_mock_settings()
        mock_cache = MagicMock(spec=AIResponseCache)
        
        # Mock the environment variable for text processor
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock the Agent constructor to avoid actual AI initialization
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Get text processor service with mock dependencies
                text_processor = get_text_processor_service(mock_settings, mock_cache)
                
                # Verify it's the right type and uses the injected cache
                assert isinstance(text_processor, TextProcessorService)
                assert text_processor.settings is mock_settings
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
                    
                    # Get text processor using both settings and cache service
                    text_processor = get_text_processor_service(settings, cache_service)
                    
                    # Verify the chain is properly connected
                    assert cache_service is mock_cache_instance
                    assert isinstance(text_processor, TextProcessorService)
                    assert text_processor.cache_service is cache_service
                    
                    # Verify cache was created with settings redis_url
                    mock_cache_class.assert_called_once_with(
                        redis_url=settings.redis_url,
                        default_ttl=settings.cache_default_ttl,
                        text_hash_threshold=settings.cache_text_hash_threshold,
                        compression_threshold=settings.cache_compression_threshold,
                        compression_level=settings.cache_compression_level,
                        text_size_tiers=settings.cache_text_size_tiers,
                        memory_cache_size=settings.cache_memory_cache_size
                    )
                
    @pytest.mark.asyncio
    async def test_cache_service_uses_settings_redis_url(self):
        """Test that cache service uses redis_url from settings."""
        # Create settings with custom redis URL
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://custom-redis:9999"
        mock_settings.cache_text_hash_threshold = 1000
        mock_settings.cache_compression_threshold = 1000
        mock_settings.cache_compression_level = 6
        mock_settings.cache_default_ttl = 3600
        mock_settings.cache_text_size_tiers = {'small': 500, 'medium': 5000, 'large': 50000}
        mock_settings.cache_memory_cache_size = 100
        
        # Mock AIResponseCache
        with patch('app.dependencies.AIResponseCache') as mock_cache_class:
            mock_cache_instance = MagicMock(spec=AIResponseCache)
            mock_cache_instance.connect = AsyncMock()
            mock_cache_class.return_value = mock_cache_instance
            
            cache_service = await get_cache_service(mock_settings)
            
            # Verify cache was created with custom redis URL
            mock_cache_class.assert_called_once_with(
                redis_url="redis://custom-redis:9999",
                default_ttl=3600,
                text_hash_threshold=1000,
                compression_threshold=1000,
                compression_level=6,
                text_size_tiers={'small': 500, 'medium': 5000, 'large': 50000},
                memory_cache_size=100
            )
            assert cache_service is mock_cache_instance
    
    @pytest.mark.asyncio
    async def test_get_text_processor_creates_configured_instance(self):
        """Test that get_text_processor creates a properly configured TextProcessorService instance."""
        # Create mock dependencies
        mock_settings = create_mock_settings()
        mock_cache = MagicMock(spec=AIResponseCache)
        
        # Mock environment variable for text processor
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock the Agent constructor to avoid actual AI initialization
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Call the async dependency provider
                text_processor = await get_text_processor(mock_settings, mock_cache)
                
                # Verify it's the right type and uses the injected dependencies
                assert isinstance(text_processor, TextProcessorService)
                assert text_processor.settings is mock_settings
                assert text_processor.cache_service is mock_cache

    @pytest.mark.asyncio
    async def test_get_text_processor_with_dependency_injection(self):
        """Test that get_text_processor works with actual dependency injection chain."""
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
                    
                    # Get settings (using real dependency)
                    settings = get_settings()
                    
                    # Get cache service using real dependency
                    cache_service = await get_cache_service(settings)
                    
                    # Get text processor using new async dependency
                    text_processor = await get_text_processor(settings, cache_service)
                    
                    # Verify the chain is properly connected
                    assert cache_service is mock_cache_instance
                    assert isinstance(text_processor, TextProcessorService)
                    assert text_processor.settings is settings
                    assert text_processor.cache_service is cache_service

    @pytest.mark.asyncio
    async def test_get_text_processor_uses_injected_dependencies_correctly(self):
        """Test that get_text_processor correctly uses both settings and cache dependencies."""
        # Create specific mock objects with identifiable properties
        mock_settings = create_mock_settings(
            redis_url="redis://test-from-settings:6379",
            gemini_api_key="test-gemini-key"
        )
        
        mock_cache = MagicMock(spec=AIResponseCache)
        mock_cache.redis_url = "redis://test-from-cache:6379"
        
        # Mock environment variable
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock Agent constructor
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Call the dependency provider
                text_processor = await get_text_processor(mock_settings, mock_cache)
                
                # Verify both dependencies are correctly injected
                assert text_processor.settings is mock_settings
                assert text_processor.cache_service is mock_cache
                
                # Verify the correct instances are used (not mixed up)
                assert text_processor.settings.redis_url == "redis://test-from-settings:6379"
                assert text_processor.cache_service.redis_url == "redis://test-from-cache:6379"

    @pytest.mark.asyncio
    async def test_get_text_processor_async_behavior(self):
        """Test that get_text_processor is properly async and can be awaited."""
        # Create mock dependencies
        mock_settings = create_mock_settings()
        mock_cache = MagicMock(spec=AIResponseCache)
        
        # Mock environment variable
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock Agent constructor
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Verify this is an async function by calling it with await
                import asyncio
                
                # This should not raise any errors if it's properly async
                result = await get_text_processor(mock_settings, mock_cache)
                
                # Verify we get a valid result
                assert isinstance(result, TextProcessorService)
                
                # Verify that calling without await would return a coroutine
                coro = get_text_processor(mock_settings, mock_cache)
                assert asyncio.iscoroutine(coro)
                
                # Clean up the coroutine
                await coro

    @pytest.mark.asyncio
    async def test_get_text_processor_comparison_with_sync_version(self):
        """Test that async get_text_processor produces equivalent results to sync version."""
        # Create mock dependencies
        mock_settings = create_mock_settings()
        mock_cache = MagicMock(spec=AIResponseCache)
        
        # Mock environment variable
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock Agent constructor to ensure consistent behavior
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent_instance = MagicMock()
                mock_agent.return_value = mock_agent_instance
                
                # Get instances from both dependency providers
                async_text_processor = await get_text_processor(mock_settings, mock_cache)
                sync_text_processor = get_text_processor_service(mock_settings, mock_cache)
                
                # Both should be TextProcessorService instances
                assert isinstance(async_text_processor, TextProcessorService)
                assert isinstance(sync_text_processor, TextProcessorService)
                
                # Both should use the same dependencies
                assert async_text_processor.settings is mock_settings
                assert sync_text_processor.settings is mock_settings
                assert async_text_processor.cache_service is mock_cache
                assert sync_text_processor.cache_service is mock_cache
                
                # Both should have the same underlying agent (same mock instance)
                assert async_text_processor.agent is mock_agent_instance
                assert sync_text_processor.agent is mock_agent_instance 