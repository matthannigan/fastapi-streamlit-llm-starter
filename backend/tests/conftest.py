import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.text_processor import TextProcessorService
from app.services.cache import AIResponseCache
from app.services.monitoring import CachePerformanceMonitor
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

@pytest.fixture
def mock_performance_monitor():
    """Mock CachePerformanceMonitor for testing."""
    mock_monitor = Mock(spec=CachePerformanceMonitor)
    
    # Mock basic initialization properties
    mock_monitor.retention_hours = 1
    mock_monitor.max_measurements = 1000
    mock_monitor.memory_warning_threshold_bytes = 50 * 1024 * 1024
    mock_monitor.memory_critical_threshold_bytes = 100 * 1024 * 1024
    
    # Mock measurement lists
    mock_monitor.key_generation_times = []
    mock_monitor.cache_operation_times = []
    mock_monitor.compression_ratios = []
    mock_monitor.memory_usage_measurements = []
    mock_monitor.invalidation_events = []
    
    # Mock counter properties
    mock_monitor.cache_hits = 0
    mock_monitor.cache_misses = 0
    mock_monitor.total_operations = 0
    mock_monitor.total_invalidations = 0
    mock_monitor.total_keys_invalidated = 0
    
    # Mock method return values
    mock_monitor.get_performance_stats.return_value = {
        "timestamp": "2024-01-15T10:30:00.123456",
        "retention_hours": 1,
        "cache_hit_rate": 85.5,
        "total_cache_operations": 150,
        "cache_hits": 128,
        "cache_misses": 22,
        "key_generation": {
            "total_operations": 75,
            "avg_duration": 0.002,
            "median_duration": 0.0015,
            "max_duration": 0.012,
            "min_duration": 0.0008,
            "avg_text_length": 1250,
            "max_text_length": 5000,
            "slow_operations": 2
        }
    }
    
    mock_monitor.get_memory_usage_stats.return_value = {
        "current": {
            "total_cache_size_mb": 25.5,
            "memory_cache_size_mb": 5.2,
            "cache_entry_count": 100,
            "memory_cache_entry_count": 20,
            "avg_entry_size_bytes": 2048,
            "process_memory_mb": 150.0,
            "cache_utilization_percent": 51.0,
            "warning_threshold_reached": True
        }
    }
    
    mock_monitor.get_invalidation_frequency_stats.return_value = {
        "total_invalidations": 10,
        "total_keys_invalidated": 50,
        "rates": {
            "last_hour": 5,
            "last_24_hours": 10
        }
    }
    
    return mock_monitor

@pytest.fixture
def cache_performance_monitor():
    """Real CachePerformanceMonitor instance for testing."""
    return CachePerformanceMonitor(
        retention_hours=1,
        max_measurements=100,  # Smaller for testing
        memory_warning_threshold_bytes=10 * 1024 * 1024,  # 10MB for testing
        memory_critical_threshold_bytes=20 * 1024 * 1024   # 20MB for testing
    )

@pytest.fixture
def app_with_mock_performance_monitor(mock_performance_monitor):
    """FastAPI app with mock performance monitor dependency override."""
    from app.routers.monitoring import get_performance_monitor
    
    # Override the dependency
    app.dependency_overrides[get_performance_monitor] = lambda: mock_performance_monitor
    
    # Yield the app for testing
    yield app
    
    # Clean up dependency overrides after test
    app.dependency_overrides.clear()

@pytest.fixture
def client_with_mock_monitor(app_with_mock_performance_monitor):
    """Test client with mocked performance monitor."""
    return TestClient(app_with_mock_performance_monitor)

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
    parser.addoption(
        "--run-manual", 
        action="store_true", 
        default=False, 
        help="run manual tests"
    )

def pytest_configure(config):
    """Configure pytest based on command line options."""
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "manual: mark test as manual to run")
    
    run_slow = config.getoption("--run-slow")
    run_manual = config.getoption("--run-manual")
    
    # Modify the default marker expression if special flags are provided
    if run_slow or run_manual:
        # Get the current marker expression (from pytest.ini: "not slow and not manual")
        current_markexpr = getattr(config.option, 'markexpr', None)
        if current_markexpr:
            new_markexpr = current_markexpr
            
            # Remove "not slow" part if --run-slow is specified
            if run_slow:
                new_markexpr = new_markexpr.replace("not slow and ", "").replace(" and not slow", "").replace("not slow", "")
            
            # Remove "not manual" part if --run-manual is specified  
            if run_manual:
                new_markexpr = new_markexpr.replace("not manual and ", "").replace(" and not manual", "").replace("not manual", "")
            
            # Clean up any remaining "and" artifacts
            new_markexpr = new_markexpr.strip().replace("  ", " ")
            if new_markexpr.startswith("and "):
                new_markexpr = new_markexpr[4:]
            if new_markexpr.endswith(" and"):
                new_markexpr = new_markexpr[:-4]
            
            # Set the cleaned marker expression
            config.option.markexpr = new_markexpr if new_markexpr.strip() else None

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    run_slow = config.getoption("--run-slow")
    run_manual = config.getoption("--run-manual")
    
    # Skip markers for tests that need special flags
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    skip_manual = pytest.mark.skip(reason="need --run-manual option to run")
    
    for item in items:
        # Skip slow tests unless --run-slow is specified
        if "slow" in item.keywords and not run_slow:
            item.add_marker(skip_slow)
        
        # Skip manual tests unless --run-manual is specified
        if "manual" in item.keywords and not run_manual:
            item.add_marker(skip_manual) 