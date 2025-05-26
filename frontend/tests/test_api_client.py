"""Tests for the API client."""

import pytest
from unittest.mock import AsyncMock, patch
from app.utils.api_client import APIClient


@pytest.fixture
def api_client():
    """Create an API client instance for testing."""
    return APIClient()


@pytest.mark.asyncio
async def test_health_check_success(api_client):
    """Test successful health check."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await api_client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(api_client):
    """Test failed health check."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Connection failed")
        
        result = await api_client.health_check()
        assert result is False


@pytest.mark.asyncio
async def test_get_models_info_success(api_client):
    """Test successful model info retrieval."""
    mock_response_data = {
        "current_model": "gemini-2.0-flash-exp",
        "temperature": 0.7,
        "status": "configured"
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_response_data
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await api_client.get_models_info()
        assert result == mock_response_data


@pytest.mark.asyncio
async def test_process_text_success(api_client):
    """Test successful text processing."""
    mock_response_data = {
        "original_text": "Test text",
        "processed_text": "Processed test text",
        "model_used": "gemini-2.0-flash-exp"
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_response_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await api_client.process_text("Test text", "Summarize this")
        assert result == mock_response_data 