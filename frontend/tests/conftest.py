import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.utils.api_client import APIClient
from shared.models import TextProcessingRequest, TextProcessingResponse, TextProcessingOperation

@pytest.fixture
def api_client():
    """Create an API client instance."""
    return APIClient()

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "This is a sample text for testing the API client functionality."

@pytest.fixture
def sample_request(sample_text):
    """Sample processing request."""
    return TextProcessingRequest(
        text=sample_text,
        operation=TextProcessingOperation.SUMMARIZE,
        options={"max_length": 100}
    )

@pytest.fixture
def sample_response():
    """Sample processing response."""
    return TextProcessingResponse(
        operation=TextProcessingOperation.SUMMARIZE,
        success=True,
        result="This is a test summary.",
        processing_time=1.5,
        metadata={"word_count": 50}
    ) 