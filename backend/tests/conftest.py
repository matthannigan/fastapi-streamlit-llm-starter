import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from shared.models import TextProcessingRequest, ProcessingOperation

# Test API key for authentication
TEST_API_KEY = "test-api-key-12345"

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
def auth_headers():
    """Headers with authentication for protected endpoints."""
    return {"Authorization": f"Bearer {TEST_API_KEY}"}

@pytest.fixture
def authenticated_client(client, auth_headers):
    """Test client with authentication headers pre-configured."""
    class AuthenticatedTestClient:
        def __init__(self, client, headers):
            self.client = client
            self.headers = headers
        
        def get(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.get(url, **kwargs)
        
        def post(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.post(url, **kwargs)
        
        def put(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.put(url, **kwargs)
        
        def delete(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.delete(url, **kwargs)
        
        def patch(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.patch(url, **kwargs)
        
        def options(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.options(url, **kwargs)
    
    return AuthenticatedTestClient(client, auth_headers)

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
    # Create a smart mock that returns different responses based on the prompt
    async def smart_run(prompt):
        if "JSON object containing" in prompt and "sentiment" in prompt:
            # Return valid JSON for sentiment analysis
            return AsyncMock(data='{"sentiment": "positive", "confidence": 0.85, "explanation": "Test sentiment analysis"}')
        elif "key points" in prompt.lower():
            # Return formatted key points
            return AsyncMock(data="- First key point\n- Second key point\n- Third key point")
        elif "questions" in prompt.lower():
            # Return formatted questions
            return AsyncMock(data="1. What is AI?\n2. How does it work?\n3. What are the applications?")
        else:
            # Default response for summarization and Q&A
            return AsyncMock(data="This is a test summary response from the mocked AI.")
    
    # Mock the agent instance directly on the text_processor service
    with patch('app.services.text_processor.text_processor.agent') as mock_agent:
        mock_agent.run = AsyncMock(side_effect=smart_run)
        yield mock_agent 