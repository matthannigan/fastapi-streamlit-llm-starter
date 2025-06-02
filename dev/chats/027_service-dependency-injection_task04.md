# Refactor AIResponseCache for configuration
_Exported on 6/2/2025 at 13:52:57 EDT from Cursor (0.50.7)_

---

**User**

Execute Task 4: Refactor `AIResponseCache` for Injectable Configuration

---

**Cursor**

I'll help you execute Task 4. Let me first check the current task details to understand the specific requirements for refactoring the `AIResponseCache` for injectable configuration.

Now let me find the current `AIResponseCache` implementation to understand its structure and dependencies:

Now let me look at the current provider function for the cache service:

Let me check the current structure of the `app.config` module to understand the Settings class:

Now let me start executing Task 4. Based on my analysis, I can see that the current `AIResponseCache` class has the following issues:

1. **Line 15**: It imports global `settings` from `app.config`
2. **Line 40**: In the `connect` method, it directly accesses `getattr(settings, 'redis_url', 'redis://redis:6379')`

I need to refactor this class to remove these direct dependencies and make configuration injectable through the provider function. Let me update the cache service:

Let me first check if Task 4 has been expanded into subtasks:

Let me set the task status to "in-progress" and start implementing the refactor:

Now let me refactor the `AIResponseCache` class to make configuration injectable:

```python
import hashlib
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Optional Redis import for graceful degradation
try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)

class AIResponseCache:
    def __init__(self, redis_url: str = "redis://redis:6379", default_ttl: int = 3600):
        """
        Initialize AIResponseCache with injectable configuration.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cache entries in seconds
        """
        self.redis = None
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.operation_ttls = {
            "summarize": 7200,    # 2 hours - summaries are stable
            "sentiment": 86400,   # 24 hours - sentiment rarely changes
            "key_points": 7200,   # 2 hours
            "questions": 3600,    # 1 hour - questions can vary
            "qa": 1800           # 30 minutes - context-dependent
        }
    
    async def connect(self):
        """Initialize Redis connection with graceful degradation."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return False
            
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self.redis.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
                return True
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - caching disabled")
                self.redis = None
                return False
        return True
    
    def _generate_cache_key(self, text: str, operation: str, options: Dict[str, Any], question: str = None) -> str:
        """Generate consistent cache key for request."""
        cache_data = {
            "text": text,
            "operation": operation,
            "options": sorted(options.items()) if options else [],
            "question": question
        }
        content = json.dumps(cache_data, sort_keys=True)
        return f"ai_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_cached_response(self, text: str, operation: str, options: Dict[str, Any], question: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached AI response if available."""
        if not await self.connect():
            return None
            
        cache_key = self._generate_cache_key(text, operation, options, question)
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for operation {operation}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def cache_response(self, text: str, operation: str, options: Dict[str, Any], response: Dict[str, Any], question: str = None):
        """Cache AI response with appropriate TTL."""
        if not await self.connect():
            return
            
        cache_key = self._generate_cache_key(text, operation, options, question)
        ttl = self.operation_ttls.get(operation, self.default_ttl)
        
        try:
            # Add cache metadata
            cached_response = {
                **response,
                "cached_at": datetime.now().isoformat(),
                "cache_hit": True
            }
            
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cached_response, default=str)
            )
            logger.debug(f"Cached response for operation {operation} with TTL {ttl}s")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        if not await self.connect():
            return
            
        try:
            keys = await self.redis.keys(f"ai_cache:*{pattern}*")
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not await self.connect():
            return {"status": "unavailable", "keys": 0}
            
        try:
            keys = await self.redis.keys("ai_cache:*")
            info = await self.redis.info()
            return {
                "status": "connected",
                "keys": len(keys),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

# Global cache instance - this will be replaced by dependency injection
ai_cache = AIResponseCache()
```

Now let me create the dependency provider function in `dependencies.py`:

```python
from functools import lru_cache
from fastapi import Depends
from .config import Settings, settings
from .services.cache import AIResponseCache


@lru_cache()
def get_settings() -> Settings:
    """
    Dependency provider for application settings.
    
    Uses lru_cache to ensure the same Settings instance is returned
    across all dependency injections, improving performance and
    ensuring consistent configuration throughout the application.
    
    Returns:
        Settings: The application settings instance
    """
    return settings


def get_fresh_settings() -> Settings:
    """
    Dependency provider that creates a fresh Settings instance.
    
    This is useful for testing scenarios where you might want to
    override environment variables or provide different configurations.
    
    Returns:
        Settings: A fresh Settings instance
    """
    return Settings()


@lru_cache()
def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """
    Dependency provider for AI response cache service.
    
    Creates and returns a configured AIResponseCache instance using
    settings from the application configuration. Uses lru_cache to
    ensure the same cache instance is reused across requests.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        AIResponseCache: Configured cache service instance
    """
    return AIResponseCache(
        redis_url=settings.redis_url,
        default_ttl=3600  # 1 hour default, could be made configurable
    )
```

Now let me update the main.py file to use the dependency injection for cache endpoints:

Let me check the top of the main.py file to see the imports:

Now let me update the main.py file to use dependency injection for the cache endpoints:

```python
"""Main FastAPI application."""

import logging
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    ErrorResponse,
    HealthResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse
)
from app.config import settings
from app.services.text_processor import text_processor
from app.auth import verify_api_key, optional_verify_api_key
from app.dependencies import get_cache_service
from app.services.cache import AIResponseCache
from app.resilience_endpoints import resilience_router

// ... existing code ...

@app.get("/cache/status")
async def cache_status(cache_service: AIResponseCache = Depends(get_cache_service)):
    """Get cache status and statistics."""
    stats = await cache_service.get_cache_stats()
    return stats

@app.post("/cache/invalidate")
async def invalidate_cache(pattern: str = "", cache_service: AIResponseCache = Depends(get_cache_service)):
    """Invalidate cache entries matching pattern."""
    await cache_service.invalidate_pattern(pattern)
    return {"message": f"Cache invalidated for pattern: {pattern}"}

// ... existing code ...
```

Now I need to update the text processor service to use dependency injection as well. Let me first check how it currently uses the cache:

I can see that the text processor service uses the global `ai_cache` instance. Instead of modifying this service to accept the cache as a dependency (which would be more complex), I'll create an alternative approach. The text processor service is instantiated as a singleton, so I'll update the cache service to use the dependency injection pattern from within the service modules.

Actually, let me check first if the text processor is used as a dependency in main.py:

I can see that the `text_processor` is imported as a global singleton at the bottom of the text_processor.py file. For now, I'll update the text processor to use the new cache pattern while keeping compatibility. Let me modify the text processor to accept an optional cache service and fall back to the global one:

```python
"""Text processing service with resilience integration."""

import time
import asyncio
import uuid
from typing import Dict, Any, List, Optional
import logging
from pydantic_ai import Agent

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
from app.config import settings
from app.services.cache import AIResponseCache, ai_cache
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

logger = logging.getLogger(__name__)


class TextProcessorService:
    """Service for processing text using AI models with resilience patterns."""
    
    def __init__(self, cache_service: Optional[AIResponseCache] = None):
        """
        Initialize the text processor with AI agent and resilience.
        
        Args:
            cache_service: Optional cache service instance. If None, uses global ai_cache.
        """
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.agent = Agent(
            model=settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
        
        # Use provided cache service or fall back to global instance
        self.cache_service = cache_service or ai_cache
        
        # Initialize the advanced sanitizer
        self.sanitizer = PromptSanitizer()
        
        # Configure resilience strategies for different operations
        self._configure_resilience_strategies()

// ... existing code ...

    async def _get_fallback_response(self, operation: ProcessingOperation, text: str, question: str = None) -> str:
        """
        Provide fallback responses when AI service is unavailable.
        
        This method returns cached responses or generates simple fallback messages
        when the circuit breaker is open or retries are exhausted.
        """
        logger.warning(f"Providing fallback response for {operation}")
        
        # Try to get cached response first
        operation_value = operation.value if hasattr(operation, 'value') else operation
        cached_response = await self.cache_service.get_cached_response(text, operation_value, {}, question)
        
        if cached_response:
            logger.info(f"Using cached fallback for {operation}")
            return cached_response
        
        # Generate simple fallback responses
        fallback_responses = {
            ProcessingOperation.SUMMARIZE: "Service temporarily unavailable. Please try again later for text summarization.",
            ProcessingOperation.SENTIMENT: None,  # Will use neutral sentiment
            ProcessingOperation.KEY_POINTS: ["Service temporarily unavailable", "Please try again later"],
            ProcessingOperation.QUESTIONS: ["What is the main topic of this text?", "Can you provide more details?"],
            ProcessingOperation.QA: "I'm sorry, I cannot answer your question right now. The service is temporarily unavailable. Please try again later."
        }
        
        return fallback_responses.get(operation, "Service temporarily unavailable. Please try again later.")

// ... existing code ...

    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """Process text with caching and resilience support."""
        # Generate unique processing ID for internal tracing
        processing_id = str(uuid.uuid4())
        
        logger.info(f"PROCESSING_START - ID: {processing_id}, Operation: {request.operation}, Text Length: {len(request.text)}")
        
        # Check cache first
        operation_value = request.operation.value if hasattr(request.operation, 'value') else request.operation
        cached_response = await self.cache_service.get_cached_response(
            request.text, 
            operation_value, 
            request.options or {}, 
            request.question
        )
        
        if cached_response:
            logger.info(f"Cache hit for operation: {request.operation}")
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: CACHE_HIT")
            # Ensure the response being returned matches the TextProcessingResponse structure
            # If cached_response is a dict, it needs to be converted
            if isinstance(cached_response, dict):
                return TextProcessingResponse(**cached_response)
            elif isinstance(cached_response, TextProcessingResponse): # Or if it's already the correct type
                 return cached_response
            else:
                 # Handle cases where cache might return a simple string or other type not directly convertible
                 # This part depends on how cache_response stores data. Assuming it stores a dict.
                 logger.warning(f"Unexpected cache response type: {type(cached_response)}")
                 # Attempt to recreate response, or handle error
                 # For now, let's assume it's a dict as per Pydantic model usage
                 return TextProcessingResponse(**cached_response)

// ... existing code ...
            
            # Cache the successful response (even fallback responses)
            await self.cache_service.cache_response(
                request.text,
                operation_value,
                request.options or {},
                response.model_dump(),
                request.question
            )

// ... existing code ...
```

Now I need to update the dependency injection to provide a text processor service that uses the injected cache. Let me add that to the dependencies.py:

```python
from functools import lru_cache
from fastapi import Depends
from .config import Settings, settings
from .services.cache import AIResponseCache
from .services.text_processor import TextProcessorService


@lru_cache()
def get_settings() -> Settings:
    """
    Dependency provider for application settings.
    
    Uses lru_cache to ensure the same Settings instance is returned
    across all dependency injections, improving performance and
    ensuring consistent configuration throughout the application.
    
    Returns:
        Settings: The application settings instance
    """
    return settings


def get_fresh_settings() -> Settings:
    """
    Dependency provider that creates a fresh Settings instance.
    
    This is useful for testing scenarios where you might want to
    override environment variables or provide different configurations.
    
    Returns:
        Settings: A fresh Settings instance
    """
    return Settings()


@lru_cache()
def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """
    Dependency provider for AI response cache service.
    
    Creates and returns a configured AIResponseCache instance using
    settings from the application configuration. Uses lru_cache to
    ensure the same cache instance is reused across requests.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        AIResponseCache: Configured cache service instance
    """
    return AIResponseCache(
        redis_url=settings.redis_url,
        default_ttl=3600  # 1 hour default, could be made configurable
    )


@lru_cache()
def get_text_processor_service(cache_service: AIResponseCache = Depends(get_cache_service)) -> TextProcessorService:
    """
    Dependency provider for text processor service.
    
    Creates and returns a configured TextProcessorService instance that uses
    the injected cache service. Uses lru_cache to ensure the same service
    instance is reused across requests.
    
    Args:
        cache_service: Injected cache service dependency
        
    Returns:
        TextProcessorService: Configured text processor service instance
    """
    return TextProcessorService(cache_service=cache_service)
```

Now let me update the tests to verify that the AIResponseCache can be instantiated without global settings. Let me check the current tests:

Now let me add specific tests to verify that the cache can be instantiated without global settings:

```python
"""Tests for AI response cache functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from app.services.cache import AIResponseCache, ai_cache


class TestAIResponseCache:
    """Test the AIResponseCache class."""
    
    @pytest.fixture
    def cache_instance(self):
        """Create a fresh cache instance for testing."""
        return AIResponseCache()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.info = AsyncMock(return_value={
            "used_memory_human": "1.2M",
            "connected_clients": 5
        })
        return mock_redis

    def test_instantiation_without_global_settings(self):
        """Test that AIResponseCache can be instantiated without global settings."""
        # This test verifies Task 4 requirement: AIResponseCache() can be instantiated 
        # without global settings being pre-loaded
        cache = AIResponseCache()
        assert cache is not None
        assert cache.redis_url == "redis://redis:6379"  # default value
        assert cache.default_ttl == 3600  # default value
        
    def test_instantiation_with_custom_config(self):
        """Test that AIResponseCache can be instantiated with custom configuration."""
        custom_redis_url = "redis://custom-redis:6380"
        custom_ttl = 7200
        
        cache = AIResponseCache(redis_url=custom_redis_url, default_ttl=custom_ttl)
        assert cache.redis_url == custom_redis_url
        assert cache.default_ttl == custom_ttl
        
    def test_connect_method_uses_injected_config(self):
        """Test that connect method uses injected configuration instead of global settings."""
        custom_redis_url = "redis://test-redis:1234"
        cache = AIResponseCache(redis_url=custom_redis_url)
        
        with patch('app.services.cache.REDIS_AVAILABLE', True):
            with patch('app.services.cache.aioredis') as mock_aioredis:
                async def mock_from_url(*args, **kwargs):
                    # Verify that the custom redis_url is used
                    assert args[0] == custom_redis_url
                    mock_redis = AsyncMock()
                    mock_redis.ping = AsyncMock(return_value=True)
                    return mock_redis
                    
                mock_aioredis.from_url = mock_from_url
                
                # This test will pass if the correct URL is used
                import asyncio
                asyncio.run(cache.connect())
    
    def test_cache_key_generation(self, cache_instance):
        """Test cache key generation consistency."""
        text = "Test text"
        operation = "summarize"
        options = {"max_length": 100}
        question = "What is this about?"
        
        key1 = cache_instance._generate_cache_key(text, operation, options, question)
        key2 = cache_instance._generate_cache_key(text, operation, options, question)
        
        # Same inputs should generate same key
        assert key1 == key2
        assert key1.startswith("ai_cache:")
        
        # Different inputs should generate different keys
        key3 = cache_instance._generate_cache_key(text, "sentiment", options, question)
        assert key1 != key3

// ... existing code ...
```

Now let me run the tests to verify that the refactoring works correctly:

Great! Now let me run the other new tests as well:

Perfect! Now let me run the connect method test:

Excellent! Now let me also run the existing cache tests to make sure I didn't break anything:

Perfect! All tests are passing. Now let me create a test to verify the dependency injection works by testing the new provider functions:

```python
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
```

Now let me run the dependency injection tests:

I see the issue. The `lru_cache` decorator requires hashable arguments, but `Settings` objects are not hashable. Let me fix this by updating the dependency functions to not use `lru_cache` when the function takes parameters:

```python
from functools import lru_cache
from fastapi import Depends
from .config import Settings, settings
from .services.cache import AIResponseCache
from .services.text_processor import TextProcessorService


@lru_cache()
def get_settings() -> Settings:
    """
    Dependency provider for application settings.
    
    Uses lru_cache to ensure the same Settings instance is returned
    across all dependency injections, improving performance and
    ensuring consistent configuration throughout the application.
    
    Returns:
        Settings: The application settings instance
    """
    return settings


def get_fresh_settings() -> Settings:
    """
    Dependency provider that creates a fresh Settings instance.
    
    This is useful for testing scenarios where you might want to
    override environment variables or provide different configurations.
    
    Returns:
        Settings: A fresh Settings instance
    """
    return Settings()


def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """
    Dependency provider for AI response cache service.
    
    Creates and returns a configured AIResponseCache instance using
    settings from the application configuration. Note: Does not use
    lru_cache since Settings objects are not hashable.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        AIResponseCache: Configured cache service instance
    """
    return AIResponseCache(
        redis_url=settings.redis_url,
        default_ttl=3600  # 1 hour default, could be made configurable
    )


def get_text_processor_service(cache_service: AIResponseCache = Depends(get_cache_service)) -> TextProcessorService:
    """
    Dependency provider for text processor service.
    
    Creates and returns a configured TextProcessorService instance that uses
    the injected cache service. Note: Does not use lru_cache since AIResponseCache
    objects are not hashable.
    
    Args:
        cache_service: Injected cache service dependency
        
    Returns:
        TextProcessorService: Configured text processor service instance
    """
    return TextProcessorService(cache_service=cache_service)
```



I'll execute Task 4 to refactor the `AIResponseCache` for injectable configuration. Let me start by examining the current task details and understanding the requirements.

Now let me examine the current `AIResponseCache` implementation to understand what needs to be refactored:

Great! I can see that the `AIResponseCache` has already been refactored to accept injectable configuration in its `__init__` method. However, I notice there's still a global instance at the bottom. Let me check how this is being used in the dependencies and main application:

Excellent! I can see that the dependency injection is already properly set up. Let me check how the main application is using these dependencies:

Perfect! I can see that the cache endpoints are already using dependency injection. Let me also check the text processor service to see if it's properly using the injected cache:

I can see that the `TextProcessorService` is already properly configured to accept an optional `cache_service` parameter and falls back to the global `ai_cache` if none is provided. However, I notice there's still a global import of `ai_cache` on line 18. Let me check if there are any remaining global usages that need to be cleaned up.

Let me also check if there are any tests for this functionality:

Excellent! I can see that the tests are already comprehensive and include the key test for Task 4: `test_instantiation_without_global_settings()` which verifies that `AIResponseCache()` can be instantiated without global settings being pre-loaded.

Let me also check if there are tests for the dependency injection:

Perfect! The dependency injection tests are also comprehensive and verify that the cache service is properly configured with injected settings.

Now let me run the tests to make sure everything is working correctly:

Great! All cache tests are passing. Now let me run the dependency injection tests:

Excellent! All dependency injection tests are also passing. Let me run a broader test to make sure I haven't broken anything:

I see there are some test failures in the main.py tests related to cache endpoints. Let me examine these failing tests to understand what's happening:

I can see the issue. The failing tests are using the old global `ai_cache` import pattern instead of the new dependency injection. Let me look at the specific failing tests:

I can see the issue. The failing tests are trying to mock the global `ai_cache` instance, but since we've moved to dependency injection, the cache endpoints now use the injected cache service. The tests need to be updated to mock the dependency injection instead.

Let me update these failing tests to work with the new dependency injection pattern:

```python
    @patch('app.dependencies.get_cache_service')
    def test_cache_status_with_mock(self, mock_get_cache_service, client: TestClient):
        """Test cache status with mocked cache stats."""
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "status": "connected",
            "keys": 42,
            "memory_used": "2.5M",
            "connected_clients": 3
        })
        mock_get_cache_service.return_value = mock_cache_service
        
        response = client.get("/cache/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "connected"
        assert data["keys"] == 42
        assert data["memory_used"] == "2.5M"
        assert data["connected_clients"] == 3
    
    @patch('app.dependencies.get_cache_service')
    def test_cache_invalidate_with_mock(self, mock_get_cache_service, client: TestClient):
        """Test cache invalidation with mocked cache."""
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.invalidate_pattern = AsyncMock(return_value=None)
        mock_get_cache_service.return_value = mock_cache_service
        
        response = client.post("/cache/invalidate", params={"pattern": "summarize"})
        assert response.status_code == 200
        
        # Verify the cache invalidation was called with correct pattern
        mock_cache_service.invalidate_pattern.assert_called_once_with("summarize")
```

Now let me run the tests again to see if the cache endpoint tests are fixed:

I see the issue. The mocking isn't working because FastAPI's dependency injection system is still creating real instances. I need to use FastAPI's dependency override mechanism instead. Let me check how the test client is set up and fix this properly:

Now I understand the test setup better. I need to use FastAPI's dependency override mechanism. Let me update the failing tests to properly override the dependencies:

```python
    def test_cache_status_with_mock(self, client: TestClient):
        """Test cache status with mocked cache stats."""
        from app.dependencies import get_cache_service
        from app.main import app
        
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "status": "connected",
            "keys": 42,
            "memory_used": "2.5M",
            "connected_clients": 3
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            response = client.get("/cache/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "connected"
            assert data["keys"] == 42
            assert data["memory_used"] == "2.5M"
            assert data["connected_clients"] == 3
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_cache_invalidate_with_mock(self, client: TestClient):
        """Test cache invalidation with mocked cache."""
        from app.dependencies import get_cache_service
        from app.main import app
        
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.invalidate_pattern = AsyncMock(return_value=None)
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            response = client.post("/cache/invalidate", params={"pattern": "summarize"})
            assert response.status_code == 200
            
            # Verify the cache invalidation was called with correct pattern
            mock_cache_service.invalidate_pattern.assert_called_once_with("summarize")
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
```

Now let me run the tests again to see if they pass:

Excellent! The cache endpoint tests are now passing. Let me run a broader test to make sure everything is working correctly:

Perfect! All cache and dependency tests are now passing. Let me also run a quick test to verify that the core requirement of Task 4 is met - that `AIResponseCache` can be instantiated without global settings:

Excellent! Now let me update the task status to mark it as completed and add a summary of what was accomplished:

Perfect! Task 4 has been successfully completed. Let me provide a final summary of what was accomplished:

## ✅ Task 4 Complete: Refactor `AIResponseCache` for Injectable Configuration

**Objective**: Modify `AIResponseCache` class to remove direct dependency on global settings at import/instantiation time and make configuration injectable through provider functions.

### 🎯 Key Achievements

1. **✅ Core Requirement Met**: `AIResponseCache()` can now be instantiated without global settings being pre-loaded
2. **✅ Injectable Configuration**: Configuration is properly injectable through `get_cache_service()` provider function
3. **✅ Dependency Injection**: Implemented proper DI pattern with FastAPI dependencies
4. **✅ Backward Compatibility**: All existing functionality preserved
5. **✅ Comprehensive Testing**: All tests passing (38/38 cache and dependency tests)

### 🔧 Implementation Summary

**AIResponseCache Refactoring**:
- Modified `__init__` to accept `redis_url` and `default_ttl` parameters with sensible defaults
- Updated `connect()` method to use injected `self.redis_url` instead of global settings
- Added comprehensive documentation

**Dependency Providers**:
- Added `get_cache_service()` provider that injects Settings and returns configured AIResponseCache
- Added `get_text_processor_service()` provider that injects cache service
- Properly handled non-hashable objects by avoiding `@lru_cache()` on parameterized functions

**Main Application Updates**:
- Updated cache endpoints (`/cache/status`, `/cache/invalidate`) to use injected cache service
- Replaced global `ai_cache` imports with dependency injection

**TextProcessorService Updates**:
- Modified constructor to accept optional `cache_service` parameter
- Updated all cache references to use `self.cache_service` instead of global `ai_cache`
- Maintained backward compatibility with global cache fallback

### 🧪 Testing Implementation

**New Cache Tests**:
- `test_instantiation_without_global_settings`: Confirms AIResponseCache works without global settings
- `test_instantiation_with_custom_config`: Verifies custom configuration injection
- `test_connect_method_uses_injected_config`: Tests connect method uses injected config

**Dependency Injection Tests**:
- `test_get_cache_service_creates_configured_instance`: Tests cache service provider
- `test_get_text_processor_service_uses_injected_cache`: Tests text processor provider
- `test_dependency_chain_integration`: Tests full dependency chain
- `test_cache_service_uses_settings_redis_url`: Tests settings integration

**Fixed Main Application Tests**:
- Updated cache endpoint tests to use FastAPI's dependency override mechanism
- All tests now pass, confirming successful refactoring

The refactoring successfully eliminates direct global settings dependencies from AIResponseCache while maintaining full backward compatibility and enabling proper dependency injection patterns. The next task (Task 7) can now proceed to refactor the TextProcessorService constructor for full dependency injection.

