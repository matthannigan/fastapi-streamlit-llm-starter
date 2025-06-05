# Refactor TextProcessorService for dependency injection
_Exported on 6/2/2025 at 14:24:00 EDT from Cursor (0.50.7)_

---

**User**

Execute Task 7: Refactor `TextProcessorService.__init__` for DI

---

**Cursor**

I'll help you execute Task 7 for refactoring the `TextProcessorService.__init__` method for dependency injection. Let me first get the details of this task and then examine the current implementation.

Now let me examine the current `TextProcessorService` implementation to understand what needs to be changed:

Now let me look at the current implementation in detail:

Now, let me also check the dependencies.py file to see how it's currently being used:

Now let me check the imports to understand what Settings class is available:

Perfect! Now I understand the current implementation and what needs to be changed. Let me analyze the task:

**Current situation:**
- `TextProcessorService.__init__` currently takes `cache_service: AIResponseCache` as parameter
- The service is currently accessing `settings` as a global import from `app.config`
- Task 7 wants me to change it to accept both `settings: Settings` and `cache: AIResponseCache` as constructor arguments

Let me now update the task status to "in-progress" and then implement the refactoring:

Now let me implement the refactoring. I need to:

1. Update the `TextProcessorService.__init__` method to accept `settings: Settings` and `cache: AIResponseCache` 
2. Update the dependency provider in `dependencies.py` to pass the settings
3. Update any tests that need to be modified

Let's start with the main service file:

```python
from shared.models import (
    ProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    SentimentResult,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchProcessingItem,
    ProcessingStatus
)
from app.config import Settings
from app.services.cache import AIResponseCache
from app.utils.sanitization import sanitize_options, PromptSanitizer # Enhanced import
from app.services.prompt_builder import create_safe_prompt
from app.services.resilience import (
    ai_resilience,
    ResilienceStrategy,
    with_balanced_resilience,
    with_aggressive_resilience,
    with_conservative_resilience,
    ServiceUnavailableError,
    TransientAIError
)
from app.security.response_validator import validate_ai_response

// ... existing code ...

class TextProcessorService:
    """Service for processing text using AI models with resilience patterns."""
    
    def __init__(self, settings: Settings, cache: AIResponseCache):
        """
        Initialize the text processor with AI agent and resilience.
        
        Args:
            settings: Application settings instance for configuration.
            cache: Cache service instance for storing AI responses.
        """
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.settings = settings
        self.cache = cache
        
        self.agent = Agent(
            model=settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
        
        # Use provided cache service
        self.cache_service = cache
        
        # Initialize the advanced sanitizer
        self.sanitizer = PromptSanitizer()
        
        # Configure resilience strategies for different operations
        self._configure_resilience_strategies()

    def _configure_resilience_strategies(self):
        """Configure resilience strategies based on settings."""
        self.resilience_strategies = {
            ProcessingOperation.SUMMARIZE: self.settings.summarize_resilience_strategy,
            ProcessingOperation.SENTIMENT: self.settings.sentiment_resilience_strategy,
            ProcessingOperation.KEY_POINTS: self.settings.key_points_resilience_strategy,
            ProcessingOperation.QUESTIONS: self.settings.questions_resilience_strategy,
            ProcessingOperation.QA: self.settings.qa_resilience_strategy,
        }
        
        logger.info(f"Configured resilience strategies: {self.resilience_strategies}")
```

Now I need to update the dependency provider in `dependencies.py` to pass the settings to the TextProcessorService:

```python
def get_text_processor_service(
    settings: Settings = Depends(get_settings),
    cache_service: AIResponseCache = Depends(get_cache_service)
) -> TextProcessorService:
    """
    Dependency provider for text processor service.
    
    Creates and returns a configured TextProcessorService instance that uses
    the injected settings and cache service. Note: Does not use lru_cache since 
    AIResponseCache objects are not hashable.
    
    Args:
        settings: Injected application settings dependency
        cache_service: Injected cache service dependency
        
    Returns:
        TextProcessorService: Configured text processor service instance
    """
    return TextProcessorService(settings=settings, cache=cache_service)
```

Now let me check if there are any tests that need to be updated to accommodate the new constructor signature:

I can see that the tests need to be updated. They're currently instantiating `TextProcessorService` with only `cache_service` but now need both `settings` and `cache`. Let me fix the test fixtures:

```python
@pytest_asyncio.fixture
async def processor_service(mock_cache_service, mock_settings):
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
        # Mock the Agent used by TextProcessorService to avoid actual AI calls
        with patch('app.services.text_processor.Agent') as mock_agent_constructor:
            # Create a proper mock agent instance
            mock_agent_instance = MagicMock()
            mock_agent_instance.run = AsyncMock() # Mock the 'run' method specifically
            mock_agent_constructor.return_value = mock_agent_instance
            
            service = TextProcessorService(settings=mock_settings, cache=mock_cache_service)
            # Mock the process_text method for batch tests, as we are unit testing process_batch
            service.process_text = AsyncMock()
            return service

class TestTextProcessorService:
    """Test the TextProcessorService class."""
    
    @pytest.fixture
    def service(self, mock_ai_agent, mock_cache_service, mock_settings):
        """Create a TextProcessorService instance."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            return TextProcessorService(settings=mock_settings, cache=mock_cache_service)
```

Now I need to update the other test class fixtures as well:

Now I need to update the remaining test fixtures. Let me update them one by one:

```python
class TestTextProcessorCaching:
    """Test caching integration in TextProcessorService."""
    
    @pytest.fixture
    def service(self, mock_ai_agent, mock_cache_service, mock_settings):
        """Create a TextProcessorService instance."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            return TextProcessorService(settings=mock_settings, cache=mock_cache_service)
```

Now let me update the TestServiceInitialization class:

```python
class TestServiceInitialization:
    """Test service initialization."""
    
    def test_initialization_without_api_key(self, mock_cache_service, mock_settings):
        """Test initialization fails without API key."""
        # Create a mock settings with empty API key
        mock_settings.gemini_api_key = ""
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            TextProcessorService(settings=mock_settings, cache=mock_cache_service)
    
    def test_initialization_with_api_key(self, mock_ai_agent, mock_cache_service, mock_settings):
        """Test successful initialization with API key."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            service = TextProcessorService(settings=mock_settings, cache=mock_cache_service)
            assert service.settings is not None
            assert service.cache is not None
            assert service.cache_service is not None
```

Now let me update the remaining test fixtures that are still using the old constructor:

```python
class TestTextProcessorSanitization:
    """Test prompt sanitization in TextProcessorService."""
    
    @pytest.fixture
    def text_processor_service(self, mock_cache_service, mock_settings):
        # Reset mocks for each test if necessary, or ensure Agent is stateless
        # For pydantic-ai Agent, it's typically instantiated with config.
        # If it were truly stateful across calls in an undesired way, we'd re-init or mock reset.
        
        # Mock the Agent to avoid actual AI API calls
        with patch('app.services.text_processor.Agent') as mock_agent_constructor:
            mock_agent_instance = MagicMock()
            mock_agent_instance.run = AsyncMock()
            mock_agent_constructor.return_value = mock_agent_instance
            
            # Mock os.environ to provide GEMINI_API_KEY
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
                service = TextProcessorService(settings=mock_settings, cache=mock_cache_service)
                service.agent = mock_agent_instance  # Ensure the agent is mocked
                return service
```

Now let me update the TestPRDAttackScenarios fixture:

```python
class TestPRDAttackScenarios:
    """
    Test the AI system's resistance to sophisticated prompt injection and security attacks
    as outlined in the PRD security requirements.
    """
    
    @pytest.fixture
    def text_processor_service(self, mock_cache_service, mock_settings):
        # Mock the Agent to avoid actual AI API calls
        with patch('app.services.text_processor.Agent') as mock_agent_constructor:
            mock_agent_instance = MagicMock()
            mock_agent_instance.run = AsyncMock()
            mock_agent_constructor.return_value = mock_agent_instance
            
            # Mock os.environ to provide GEMINI_API_KEY
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
                service = TextProcessorService(settings=mock_settings, cache=mock_cache_service)
                service.agent = mock_agent_instance  # Ensure the agent is mocked
                return service
```

Finally, let me update the TestSecurityTestConsolidation fixture:

```python
class TestSecurityTestConsolidation:
    """
    Comprehensive security testing that validates all security components work together
    to provide defense-in-depth against various attack vectors.
    """
    
    @pytest.fixture
    def text_processor_service(self, mock_cache_service, mock_settings):
        """Create a TextProcessorService instance for comprehensive security testing."""
        with patch('app.services.text_processor.Agent') as mock_agent_constructor:
            mock_agent_instance = MagicMock()
            mock_agent_instance.run = AsyncMock()
            mock_agent_constructor.return_value = mock_agent_instance
            
            # Mock os.environ to provide GEMINI_API_KEY
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
                service = TextProcessorService(settings=mock_settings, cache=mock_cache_service)
                service.agent = mock_agent_instance  # Ensure the agent is mocked
                return service
```

Now let's run the tests to make sure our refactoring worked correctly:

I see the issue. The test is trying to patch `app.services.text_processor.settings` but we've removed that global import from the module. Let me fix the mock settings fixture:

```python
@pytest.fixture(scope="module", autouse=True)
def mock_settings():
    """Mock the Settings configuration class for tests."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.gemini_api_key = "test_api_key"
    mock_settings_obj.ai_model = "gemini-2.0-flash-exp"
    mock_settings_obj.ai_temperature = 0.7
    mock_settings_obj.redis_url = "redis://localhost:6379"
    mock_settings_obj.resilience_enabled = True
    mock_settings_obj.circuit_breaker_enabled = True
    mock_settings_obj.retry_enabled = True
    mock_settings_obj.default_resilience_strategy = "balanced"
    mock_settings_obj.summarize_resilience_strategy = "balanced"
    mock_settings_obj.sentiment_resilience_strategy = "aggressive"
    mock_settings_obj.key_points_resilience_strategy = "balanced"
    mock_settings_obj.questions_resilience_strategy = "balanced"
    mock_settings_obj.qa_resilience_strategy = "conservative"
    mock_settings_obj.BATCH_AI_CONCURRENCY_LIMIT = 5
    yield mock_settings_obj
```

Now let's test it again:

Great! Now let's run a few more tests to make sure everything is working correctly:

The test is failing because the mock settings doesn't have a truthy `gemini_api_key`. Let me fix this:

```python
    def test_initialization_with_api_key(self, mock_ai_agent, mock_cache_service, mock_settings):
        """Test successful initialization with API key."""
        # Ensure the mock settings has a valid API key
        mock_settings.gemini_api_key = "test-api-key"
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            service = TextProcessorService(settings=mock_settings, cache=mock_cache_service)
            assert service.settings is not None
            assert service.cache is not None
            assert service.cache_service is not None
```

Let's run the test again:

Excellent! Now let's run a broader test to ensure our refactoring is working correctly:

Great! The tests are passing. Now let's run a quick test of the dependency injection to make sure the FastAPI dependency system still works:



Let me create a simple test file instead:

```python
#!/usr/bin/env python3
"""Test dependency injection for TextProcessorService."""

import asyncio
from app.dependencies import get_text_processor_service, get_settings, get_cache_service

async def test_dependency_injection():
    """Test that dependency injection works correctly."""
    print("Testing dependency injection...")
    
    # Get dependencies
    settings = get_settings()
    cache = await get_cache_service(settings)
    service = get_text_processor_service(settings, cache)
    
    # Verify the service has the expected attributes
    print(f"Service has settings: {hasattr(service, 'settings')}")
    print(f"Service has cache: {hasattr(service, 'cache')}")
    print(f"Service has cache_service: {hasattr(service, 'cache_service')}")
    
    # Verify the injected dependencies are the same objects
    print(f"Settings match: {service.settings is settings}")
    print(f"Cache match: {service.cache is cache}")
    print(f"Cache service match: {service.cache_service is cache}")
    
    # Verify settings attributes are accessible
    print(f"Settings has gemini_api_key: {hasattr(service.settings, 'gemini_api_key')}")
    print(f"Settings has ai_model: {hasattr(service.settings, 'ai_model')}")
    
    print("Dependency injection test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_dependency_injection())
```

Perfect! The dependency injection is working correctly. Let me clean up the test file and then mark the task as complete:

Now let me run one final comprehensive test to make sure everything is working:

Excellent! All tests are passing. Now let me mark the task as complete and update the task with implementation details:

Perfect! Task 7 has been completed successfully. Let me provide a summary of what was accomplished:

## Task 7 Completion Summary

✅ **Successfully refactored `TextProcessorService.__init__` for dependency injection**

### Key Changes Made:

1. **Constructor Signature Updated**:
   - Changed from: `def __init__(self, cache_service: AIResponseCache)`
   - Changed to: `def __init__(self, settings: Settings, cache: AIResponseCache)`

2. **Instance Attributes Added**:
   - Added `self.settings = settings` 
   - Added `self.cache = cache`
   - Maintained `self.cache_service = cache` for backward compatibility

3. **Global Dependencies Removed**:
   - Removed global `settings` import usage
   - Updated all internal references to use `self.settings`

4. **Dependency Provider Updated**:
   - Modified `get_text_processor_service()` to inject both settings and cache
   - Ensured proper dependency chain: `Settings` → `AIResponseCache` → `TextProcessorService`

5. **Tests Updated**:
   - Fixed all test fixtures to use new constructor signature
   - Updated mock settings to work with new dependency injection pattern
   - All existing tests pass without functional changes

### Verification Results:
- ✅ All unit tests pass (9/9 in main test class)
- ✅ Dependency injection works correctly 
- ✅ Service properly stores and uses injected dependencies
- ✅ No breaking changes to external API
- ✅ Backward compatibility maintained

The refactoring successfully implements proper dependency injection following SOLID principles while maintaining all existing functionality. The service is now more testable, maintainable, and follows proper dependency inversion patterns.

**Next Task**: Task 8 is ready to work on - "Update `TextProcessorService` Internals" which will ensure all internal methods properly use the injected dependencies.

