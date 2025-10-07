"""
Test fixtures shared across cache infrastructure unit tests.

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
that are commonly used across multiple cache module test suites.

Fixture Categories:
    - Mock dependency fixtures (settings, cache factory, cache interface, performance monitor, memory cache)
    - Custom exception fixtures
    - Basic test data fixtures (keys, values, TTL values, text samples)
    - AI-specific data fixtures (responses, operations, options)
    - Statistics fixtures (sample performance data)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateful mocks maintain internal state for realistic behavior
"""

from unittest.mock import patch

import pytest

# =============================================================================
# Mock Settings Fixtures
# =============================================================================
#
# Moved to parent `backend/tests/unit/conftest.py`

# =============================================================================
# Real Factory Fixtures (Replace Mock-Based Fixtures)
# =============================================================================


@pytest.fixture
async def real_cache_factory():
    """
    Real CacheFactory instance for testing factory behavior.

    Provides an actual CacheFactory instance to test real factory logic,
    parameter mapping, and cache creation behavior rather than mocking
    the factory's internal operations.

    This enables behavior-driven testing of the factory's actual logic.
    """
    from app.infrastructure.cache.factory import CacheFactory

    return CacheFactory()


@pytest.fixture
async def factory_memory_cache(real_cache_factory):
    """
    Cache created via real factory using memory cache for testing.

    Creates a cache through the real factory using memory cache option,
    enabling testing of factory integration while avoiding Redis dependencies.
    """
    cache = await real_cache_factory.for_testing(use_memory_cache=True)
    yield cache
    await cache.clear()


@pytest.fixture
async def factory_web_cache(real_cache_factory):
    """
    Cache created via real factory for web application testing.

    Creates a cache through the real factory for web application use case,
    with graceful fallback to memory cache if Redis is unavailable.
    """
    cache = await real_cache_factory.for_web_app(fail_on_connection_error=False)
    yield cache
    if hasattr(cache, "clear"):
        await cache.clear()


@pytest.fixture
async def factory_ai_cache(real_cache_factory):
    """
    Cache created via real factory for AI application testing.

    Creates a cache through the real factory for AI application use case,
    with graceful fallback to memory cache if Redis is unavailable.
    """
    cache = await real_cache_factory.for_ai_app(fail_on_connection_error=False)
    yield cache
    if hasattr(cache, "clear"):
        await cache.clear()


@pytest.fixture
async def real_performance_monitor():
    """
    Real performance monitor instance for integration testing.

    Provides an actual CachePerformanceMonitor instance to test real
    monitoring behavior, metric accuracy, and integration patterns
    rather than mocking monitoring operations.
    """
    from app.infrastructure.cache.monitoring import CachePerformanceMonitor

    return CachePerformanceMonitor()


@pytest.fixture
def cache_implementations():
    """
    Real cache implementations for polymorphism testing.

    Provides a list of actual cache implementations to test polymorphic
    behavior and interface compliance across different cache types.

    Uses real implementations rather than mocked interfaces to verify
    actual polymorphic behavior and interface adherence.
    """
    from app.infrastructure.cache.memory import InMemoryCache
    from app.infrastructure.cache.redis_generic import GenericRedisCache

    implementations = [InMemoryCache(max_size=100, default_ttl=3600)]

    # Add Redis implementations when available (graceful degradation)
    # In CI/testing environments without Redis, this will only test InMemoryCache
    # which is still valuable for polymorphism verification
    try:
        redis_cache = GenericRedisCache(
            redis_url="redis://localhost:6379/15",  # Test database
            default_ttl=3600,
            enable_l1_cache=True,
            fail_on_connection_error=False,  # Allow fallback
        )
        implementations.append(redis_cache)
    except Exception:
        # Redis not available, continue with memory cache only
        pass

    return implementations


# =============================================================================
# Additional Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_empty_value():
    """
    Empty cache value for testing edge cases.

    Provides an empty dictionary value to test cache behavior
    with empty data structures and edge case handling.
    """
    return {}


@pytest.fixture
def sample_unicode_value():
    """
    Unicode cache value for testing international character support.

    Provides a dictionary containing various Unicode characters,
    emojis, and international text for testing proper encoding
    and decoding of cached values.
    """
    return {
        "id": 789,
        "emoji_text": "Testing with emojis! 🚀 🌟 ✨ 🎯",
        "international": {
            "chinese": "测试文本",
            "japanese": "テストテキスト",
            "russian": "тестовый текст",
            "arabic": "نص الاختبار",
            "emoji_mixed": "Hello 世界 🌍 Привет мир!",
        },
        "special_chars": "Special chars: àáâãäåæçèéêëìíîïñòóôõöøùúûüý",
        "mathematical": "Math symbols: ∑∏∫∮∆∇∂∞≠≤≥±×÷√∝∈∉∪∩",
    }


@pytest.fixture
def sample_null_value():
    """
    Null cache value for testing None handling.

    Provides None value to test cache behavior with null values,
    ensuring proper distinction between "key not found" and
    "key exists but value is None".
    """
    return


@pytest.fixture
def sample_whitespace_key():
    """
    Cache key with whitespace for testing key validation.

    Provides a key containing various whitespace characters
    to test key normalization and validation logic.
    """
    return "test:  key  :with:whitespace  "


@pytest.fixture
def sample_large_key():
    """
    Large cache key for testing key length limits.

    Provides a very long key to test cache behavior with
    keys that might exceed typical length limits.
    """
    return "test:" + "x" * 500 + ":large_key"


# =============================================================================
# Shared Sample Data Integration
# =============================================================================


@pytest.fixture
def shared_sample_texts():
    """
    Sample texts from shared module for consistent cross-component testing.

    Provides access to standardized sample texts used across frontend
    and backend components for consistent testing patterns.
    """
    from shared.sample_data import get_all_sample_texts

    return get_all_sample_texts()


@pytest.fixture
def shared_unicode_text():
    """
    Unicode-rich text from shared data for international testing.

    Combines shared sample data with additional Unicode content
    for comprehensive international character testing.
    """
    from shared.sample_data import get_sample_text

    base_text = get_sample_text("ai_technology")
    return f"{base_text} 🤖 国际化测试 Тестирование التجربة"


@pytest.fixture
def shared_empty_text():
    """
    Empty text value for testing empty input handling.

    Provides empty string to test how cache components handle
    empty text inputs in AI processing contexts.
    """
    return ""


@pytest.fixture
def shared_whitespace_text():
    """
    Text containing only whitespace for edge case testing.

    Provides whitespace-only string to test text normalization
    and validation in cache key generation and AI processing.
    """
    return "   \n\t   \r\n   "


# =============================================================================
# Utilities
# =============================================================================


@pytest.fixture
def default_memory_cache():
    """
    InMemoryCache instance with default configuration for standard testing.

    Provides a fresh InMemoryCache instance with default settings
    suitable for most test scenarios. This represents the 'happy path'
    configuration that should work reliably.

    Configuration:
        - default_ttl: 3600 seconds (1 hour)
        - max_size: 1000 entries
    """
    from app.infrastructure.cache.memory import InMemoryCache

    return InMemoryCache()


@pytest.fixture
def mock_path_exists():
    """
    Fixture that mocks pathlib.Path.exists.

    Uses autospec=True to ensure the mock's signature matches the real
    method, which is crucial for using side_effect correctly. The default
    return_value is True for "happy path" tests.

    Note:
        This is a prime example of a **good mock** because it isolates the test
        from an external system boundary—the filesystem. By mocking
        `pathlib.Path.exists`, tests for `SecurityConfig` can run reliably and
        quickly without requiring actual certificate files to be present on the
        testing machine.
    """
    # The key is adding autospec=True here.
    with patch("pathlib.Path.exists", autospec=True) as mock_patch:
        # Set a default return value for tests that don't need to control it.
        mock_patch.return_value = True
        yield mock_patch


# =============================================================================
# Basic Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_cache_key():
    """
    Standard cache key for basic testing scenarios.

    Provides a typical cache key string used across multiple test scenarios
    for consistency in testing cache interfaces.
    """
    return "test:key:123"


@pytest.fixture
def sample_cache_value():
    """
    Standard cache value for basic testing scenarios.

    Provides a typical cache value (dictionary) that represents common
    data structures cached in production applications.
    """
    return {
        "user_id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": {"theme": "dark", "language": "en"},
        "created_at": "2023-01-01T12:00:00Z",
    }


@pytest.fixture
def sample_ttl():
    """
    Standard TTL value for testing time-to-live functionality.

    Provides a reasonable TTL value (in seconds) for testing
    cache expiration behavior.
    """
    return 3600  # 1 hour


@pytest.fixture
def short_ttl():
    """
    Short TTL value for testing expiration scenarios.

    Provides a very short TTL value useful for testing
    cache expiration without long waits in tests.
    """
    return 1  # 1 second


# =============================================================================
# AI-Specific Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_text():
    """
    Sample text for AI cache testing.

    Provides typical text content that would be processed by AI operations,
    used across multiple test scenarios for consistency.
    """
    return "This is a sample document for AI processing. It contains enough content to test various text processing operations like summarization, sentiment analysis, and question answering."


@pytest.fixture
def sample_short_text():
    """
    Short sample text below hash threshold for testing text tier behavior.
    """
    return "Short text for testing."


@pytest.fixture
def sample_long_text():
    """
    Long sample text above hash threshold for testing text hashing behavior.
    """
    return "This is a very long document " * 100  # Creates text > 1000 chars


@pytest.fixture
def sample_ai_response():
    """
    Sample AI response data for caching tests.

    Represents typical AI processing results with various data types
    to test serialization and caching behavior.
    """
    return {
        "result": "This is a processed summary of the input text.",
        "confidence": 0.95,
        "metadata": {"model": "test-model", "processing_time": 1.2, "tokens_used": 150},
        "timestamp": "2023-01-01T12:00:00Z",
    }


@pytest.fixture
def sample_options():
    """
    Sample operation options for AI processing.
    """
    return {"max_length": 100, "temperature": 0.7, "language": "en"}


# =============================================================================
# Statistics and Sample Data Fixtures
# =============================================================================


@pytest.fixture
def ai_cache_test_data():
    """
    Comprehensive test data set for AI cache operations.

    Provides various combinations of texts, operations, options, and responses
    for testing different scenarios described in the docstrings.
    """
    return {
        "operations": {
            "summarize": {
                "text": "Long document to summarize with multiple paragraphs and complex content.",
                "options": {"max_length": 100, "style": "concise"},
                "response": {"summary": "Brief summary", "confidence": 0.9},
            },
            "sentiment": {
                "text": "I love this product! It works perfectly.",
                "options": {"detailed": True},
                "response": {"sentiment": "positive", "confidence": 0.95, "score": 0.8},
            },
            "questions": {
                "text": "Climate change is a complex global issue affecting ecosystems.",
                "options": {"count": 3},
                "response": {
                    "questions": [
                        "What are the main causes of climate change?",
                        "How does climate change affect ecosystems?",
                        "What can be done to address climate change?",
                    ]
                },
            },
            "qa": {
                "text": "The company was founded in 2010 and has grown rapidly.",
                "options": {},
                "question": "When was the company founded?",
                "response": {
                    "answer": "The company was founded in 2010.",
                    "confidence": 1.0,
                },
            },
        },
        "text_tiers": {
            "small": "Short text under 500 characters.",
            "medium": "Medium length text " * 50,  # ~1000 chars
            "large": "Very long text " * 500,  # ~5000+ chars
        },
    }


@pytest.fixture
def cache_statistics_sample():
    """
    Sample cache statistics data for testing statistics methods.

    Provides realistic cache statistics data matching the structure documented
    in cache statistics contracts for testing statistics display and monitoring.
    """
    return {
        "redis": {
            "connected": True,
            "keys": 150,
            "memory_usage": "2.5MB",
            "hit_ratio": 0.78,
            "connection_status": "connected",
            "redis_version": "6.2.0",
        },
        "memory": {
            "memory_cache_entries": 85,
            "memory_cache_size": 100,
            "memory_usage": "1.2MB",
            "utilization_percent": 85.0,
            "evictions": 5,
        },
        "performance": {
            "hit_ratio": 75.0,
            "total_operations": 200,
            "cache_hits": 150,
            "cache_misses": 50,
            "recent_avg_cache_operation_time": 0.045,
            "compression_stats": {
                "compressed_entries": 45,
                "compression_ratio": 0.65,
                "compression_savings_bytes": 125000,
            },
        },
        "ai_metrics": {
            "total_operations": 180,
            "overall_hit_rate": 72.2,
            "operations": {
                "summarize": {"total": 80, "hits": 65, "hit_rate": 81.25},
                "sentiment": {"total": 60, "hits": 45, "hit_rate": 75.0},
                "questions": {"total": 40, "hits": 25, "hit_rate": 62.5},
            },
            "text_tiers": {
                "small": {"count": 50, "hit_rate": 85.0},
                "medium": {"count": 90, "hit_rate": 72.0},
                "large": {"count": 60, "hit_rate": 68.0},
            },
            "key_generation_stats": {
                "total_keys_generated": 180,
                "average_generation_time": 0.001,
            },
        },
    }
