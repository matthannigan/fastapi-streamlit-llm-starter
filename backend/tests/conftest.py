import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Add the root directory to Python path so we can import app modules and shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from shared.models import TextProcessingRequest, ProcessingOperation

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Artificial intelligence (AI) is intelligence demonstrated by machines, 
    in contrast to the natural intelligence displayed by humans and animals. 
    Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize 
    its chance of successfully achieving its goals.
    """

@pytest.fixture
def sample_request(sample_text):
    """Sample request for testing."""
    return TextProcessingRequest(
        text=sample_text,
        operation=ProcessingOperation.SUMMARIZE,
        options={"max_length": 100}
    )

@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing."""
    return AsyncMock(return_value=AsyncMock(data="This is a test summary."))

@pytest.fixture(autouse=True)
def mock_ai_agent():
    """Mock the AI agent to avoid actual API calls during testing."""
    with patch('backend.app.services.text_processor.Agent') as mock:
        mock_instance = AsyncMock()
        mock_instance.run = AsyncMock(return_value=AsyncMock(data="Mock AI response"))
        mock.return_value = mock_instance
        yield mock_instance 