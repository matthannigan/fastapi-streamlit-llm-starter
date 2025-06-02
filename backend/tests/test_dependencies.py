"""Tests for dependency injection providers."""

import pytest
from unittest.mock import patch, MagicMock
import os

from app.dependencies import get_cache_service, get_text_processor_service, get_settings
from app.services.cache import AIResponseCache
from app.services.text_processor import TextProcessorService
from app.config import Settings


class TestDependencyInjection:
    """Test dependency injection providers."""
    
    def test_get_cache_service_creates_configured_instance(self):
        """Test that get_cache_service creates a properly configured cache instance."""
        # Create a mock settings object
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://test-host:6379"
        
        # Get cache service with mock settings
        cache_service = get_cache_service(mock_settings)
        
        # Verify it's the right type and configured correctly
        assert isinstance(cache_service, AIResponseCache)
        assert cache_service.redis_url == "redis://test-host:6379"
        assert cache_service.default_ttl == 3600  # Default value
        
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
                
    def test_dependency_chain_integration(self):
        """Test that the full dependency chain works together."""
        # Mock environment variable
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            # Mock Agent constructor
            with patch('app.services.text_processor.Agent') as mock_agent:
                mock_agent.return_value = MagicMock()
                
                # Get settings
                settings = get_settings()
                
                # Get cache service using settings
                cache_service = get_cache_service(settings)
                
                # Get text processor using cache service
                text_processor = get_text_processor_service(cache_service)
                
                # Verify the chain is properly connected
                assert isinstance(cache_service, AIResponseCache)
                assert isinstance(text_processor, TextProcessorService)
                assert text_processor.cache_service is cache_service
                assert cache_service.redis_url == settings.redis_url
                
    def test_cache_service_uses_settings_redis_url(self):
        """Test that cache service uses redis_url from settings."""
        # Create settings with custom redis URL
        mock_settings = MagicMock(spec=Settings)
        mock_settings.redis_url = "redis://custom-redis:9999"
        
        cache_service = get_cache_service(mock_settings)
        
        assert cache_service.redis_url == "redis://custom-redis:9999" 