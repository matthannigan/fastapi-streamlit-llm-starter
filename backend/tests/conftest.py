import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.text_processor import TextProcessorService
from app.services.cache import AIResponseCache
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

@pytest.fixture
def mock_processor():
    """Mock TextProcessorService for testing."""
    mock = AsyncMock(spec=TextProcessorService)
    
    # Configure default return values for process_text method
    async def mock_process_text(request):
        from shared.models import TextProcessingResponse, SentimentResult
        
        response = TextProcessingResponse(
            operation=request.operation,
            processing_time=0.1,
            metadata={"word_count": len(request.text.split())}
        )
        
        if request.operation == "summarize":
            response.result = "Mock summary of the text"
        elif request.operation == "sentiment":
            response.sentiment = SentimentResult(
                sentiment="positive",
                confidence=0.85,
                explanation="Mock sentiment analysis"
            )
        elif request.operation == "qa":
            response.result = "Mock answer to the question"
        elif request.operation == "key_points":
            response.key_points = ["Mock key point 1", "Mock key point 2"]
        elif request.operation == "questions":
            response.questions = ["Mock question 1?", "Mock question 2?"]
        
        return response
    
    mock.process_text = AsyncMock(side_effect=mock_process_text)
    return mock

@pytest.fixture
def mock_cache_service():
    """Mock AIResponseCache for testing."""
    mock_cache = AsyncMock(spec=AIResponseCache)
    # if connect is async and called by provider, mock it as async
    mock_cache.connect = AsyncMock() 
    mock_cache.get_cached_response = AsyncMock(return_value=None)
    mock_cache.cache_response = AsyncMock()
    mock_cache.invalidate_pattern = AsyncMock()
    mock_cache.get_cache_stats = AsyncMock(return_value={"status": "connected", "keys": 0})
    return mock_cache

@pytest.fixture(autouse=True)
def mock_ai_agent():
    """Mock the AI agent to avoid actual API calls during testing."""
    # Create a smart mock that returns different responses based on the prompt
    async def smart_run(prompt):
        # Extract the user input from the prompt to make intelligent responses
        user_text = ""
        if "---USER TEXT START---" in prompt and "---USER TEXT END---" in prompt:
            start_marker = "---USER TEXT START---"
            end_marker = "---USER TEXT END---"
            start_idx = prompt.find(start_marker) + len(start_marker)
            end_idx = prompt.find(end_marker)
            user_text = prompt[start_idx:end_idx].strip()
        else:
            # Fallback: use the entire prompt
            user_text = prompt
        
        user_text_lower = user_text.lower()
        
        # Check the type of task based on the task instruction section
        if "JSON object containing" in prompt and "sentiment" in prompt:
            # Return valid JSON for sentiment analysis
            if "positive" in user_text_lower or "good" in user_text_lower or "great" in user_text_lower:
                return AsyncMock(data='{"sentiment": "positive", "confidence": 0.85, "explanation": "Test sentiment analysis"}')
            elif "negative" in user_text_lower or "bad" in user_text_lower or "terrible" in user_text_lower:
                return AsyncMock(data='{"sentiment": "negative", "confidence": 0.85, "explanation": "Test sentiment analysis"}')
            else:
                return AsyncMock(data='{"sentiment": "neutral", "confidence": 0.75, "explanation": "Test sentiment analysis"}')
        elif "Return each point as a separate line starting with a dash" in prompt:
            # This is specifically for key points extraction
            if "cooking" in user_text_lower:
                return AsyncMock(data="- Cooking techniques\n- Recipe ingredients\n- Food preparation")
            elif "weather" in user_text_lower:
                return AsyncMock(data="- Weather patterns\n- Climate change\n- Meteorological data")
            else:
                return AsyncMock(data="- First key point\n- Second key point\n- Third key point")
        elif "Generate thoughtful questions" in prompt:
            # This is specifically for question generation
            if "ai" in user_text_lower or "artificial intelligence" in user_text_lower:
                return AsyncMock(data="1. What is AI?\n2. How does it work?\n3. What are the applications?")
            elif "cooking" in user_text_lower:
                return AsyncMock(data="1. What ingredients are needed?\n2. How long does it take to cook?\n3. What cooking method is used?")
            else:
                return AsyncMock(data="1. What is the main topic?\n2. How does it work?\n3. What are the key benefits?")
        else:
            # Default response for summarization and Q&A - make it content-aware
            if "cooking" in user_text_lower and ("recipes" in user_text_lower or "ingredients" in user_text_lower):
                return AsyncMock(data="This text discusses cooking recipes and ingredients for food preparation.")
            elif "weather" in user_text_lower and "climate" in user_text_lower:
                return AsyncMock(data="This text covers weather patterns and climate change topics.")
            elif "alice" in user_text_lower and "secret" in user_text_lower:
                return AsyncMock(data="This text contains information about Alice and sensitive data.")
            elif "financial" in user_text_lower and "earnings" in user_text_lower:
                return AsyncMock(data="This text discusses financial data and earnings information.")
            elif "injection" in user_text_lower or "ignore" in user_text_lower:
                return AsyncMock(data="I can help you analyze text content for legitimate purposes.")
            elif "error_context" in user_text_lower:
                return AsyncMock(data="This text contains error context and special characters.")
            elif "cache isolation testing" in user_text_lower:
                return AsyncMock(data="This is a summary about cache isolation and testing mechanisms.")
            elif "completely different content" in user_text_lower:
                return AsyncMock(data="This is a summary about different content and cache verification.")
            elif "unique_content_" in user_text_lower:
                # Extract the content number for unique responses
                import re
                match = re.search(r'unique_content_(\d+)', user_text_lower)
                if match:
                    num = match.group(1)
                    return AsyncMock(data=f"This is a unique summary about topic {num} from request number {num}.")
                return AsyncMock(data="This is a unique summary about specific content.")
            elif "batch_item_" in user_text_lower:
                # Extract the batch item number for unique responses
                import re
                match = re.search(r'batch_item_(\d+)', user_text_lower)
                if match:
                    num = match.group(1)
                    if "financial" in user_text_lower:
                        return AsyncMock(data=f"Summary about financial data from batch item {num}.")
                    elif "announcement" in user_text_lower:
                        return AsyncMock(data=f"Summary about product announcement from batch item {num}.")
                    elif "memo" in user_text_lower:
                        return AsyncMock(data=f"Summary about security protocols from batch item {num}.")
                return AsyncMock(data="This is a batch processing summary.")
            else:
                # Generic fallback that tries to be somewhat relevant
                words = user_text_lower.split()
                if len(words) > 3:
                    key_words = [w for w in words[:5] if len(w) > 3]
                    if key_words:
                        return AsyncMock(data=f"This is a summary about {' and '.join(key_words[:2])}.")
                return AsyncMock(data="This is a test summary response from the mocked AI.")
    
    # Mock the Agent class constructor to return a mock agent with the smart_run method
    with patch('app.services.text_processor.Agent') as mock_agent_class:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run = AsyncMock(side_effect=smart_run)
        mock_agent_class.return_value = mock_agent_instance
        yield mock_agent_instance 

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", 
        action="store_true", 
        default=False, 
        help="run slow tests"
    )

def pytest_configure(config):
    """Configure pytest based on command line options."""
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    
    # If --run-slow is specified, don't filter out slow tests
    if config.getoption("--run-slow"):
        # Remove the default marker expression that excludes slow tests
        markexpr = config.getoption("-m", default="")
        if markexpr == "not slow":
            config.option.markexpr = ""

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    if config.getoption("--run-slow"):
        # If --run-slow is specified, run all tests
        return
    
    # Default behavior: skip slow tests unless explicitly requested
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow) 