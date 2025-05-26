"""Tests for the API client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
import sys
import os

# Add the parent directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.api_client import APIClient, run_async
from shared.models import ProcessingOperation


@pytest.fixture
def api_client():
    """Create an API client instance for testing."""
    return APIClient()


class TestAPIClient:
    """Test the APIClient class."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, api_client):
        """Test successful health check."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.health_check()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, api_client):
        """Test failed health check."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, api_client):
        """Test health check with exception."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            result = await api_client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_operations_success(self, api_client):
        """Test successful get operations."""
        mock_operations = {
            "operations": [
                {
                    "id": "summarize",
                    "name": "Summarize",
                    "description": "Generate summary",
                    "options": ["max_length"]
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_operations
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.get_operations()
            assert result == mock_operations
    
    @pytest.mark.asyncio
    async def test_get_operations_failure(self, api_client):
        """Test failed get operations."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.get_operations()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_process_text_success(self, api_client, sample_request, sample_response):
        """Test successful text processing."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_response.model_dump()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await api_client.process_text(sample_request)
            assert result is not None
            assert result.operation == ProcessingOperation.SUMMARIZE
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_process_text_api_error(self, api_client, sample_request):
        """Test text processing with API error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Bad request"}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with patch('streamlit.error') as mock_error:
                result = await api_client.process_text(sample_request)
                assert result is None
                mock_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_text_timeout(self, api_client, sample_request):
        """Test text processing with timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
            
            with patch('streamlit.error') as mock_error:
                result = await api_client.process_text(sample_request)
                assert result is None
                mock_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_text_general_exception(self, api_client, sample_request):
        """Test text processing with general exception."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            with patch('streamlit.error') as mock_error:
                result = await api_client.process_text(sample_request)
                assert result is None
                mock_error.assert_called_once()

class TestRunAsync:
    """Test the run_async helper function."""
    
    def test_run_async_success(self):
        """Test successful async execution."""
        async def test_coro():
            return "success"
        
        result = run_async(test_coro())
        assert result == "success"
    
    def test_run_async_with_exception(self):
        """Test async execution with exception."""
        async def test_coro():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            run_async(test_coro()) 