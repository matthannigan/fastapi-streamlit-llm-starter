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

import pytest
import hashlib
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional


# =============================================================================
# Mock Dependency Fixtures
# =============================================================================

# TODO: move this to a parent `conftest.py` file as other unit tests beyond cache will need it
@pytest.fixture
def mock_settings():
    """
    Mock Settings for testing configuration access behavior.
    
    Provides 'happy path' mock of the Settings contract with all methods
    returning successful configuration behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.core.config import Settings
    
    mock_settings = MagicMock(spec=Settings)
    
    # Mock basic configuration attributes per contract
    mock_settings.gemini_api_key = "test-gemini-api-key-12345"
    mock_settings.ai_model = "gemini-2.0-flash-exp"
    mock_settings.ai_temperature = 0.7
    mock_settings.MAX_BATCH_REQUESTS_PER_CALL = 50
    mock_settings.BATCH_AI_CONCURRENCY_LIMIT = 5
    mock_settings.host = "0.0.0.0"
    mock_settings.port = 8000
    mock_settings.api_key = "test-api-key-12345"
    mock_settings.additional_api_keys = "key1,key2,key3"
    mock_settings.allowed_origins = ["http://localhost:3000", "http://localhost:8501"]
    mock_settings.debug = False
    mock_settings.log_level = "INFO"
    mock_settings.cache_preset = "development"
    mock_settings.cache_custom_config = None
    mock_settings.resilience_preset = "simple"
    mock_settings.resilience_custom_config = None
    mock_settings.health_check_timeout_ms = 2000
    mock_settings.health_check_enabled_components = ["ai_model", "cache", "resilience"]
    
    # Mock cache configuration method per contract with successful behavior
    mock_cache_config = MagicMock()
    mock_cache_config.redis_url = "redis://localhost:6379"
    mock_cache_config.enable_ai_cache = True
    mock_cache_config.default_ttl = 3600
    mock_cache_config.compression_threshold = 1000
    mock_cache_config.text_size_tiers = {"small": 300, "medium": 3000, "large": 30000}
    mock_settings.get_cache_config.return_value = mock_cache_config
    
    # Mock resilience configuration method per contract with successful behavior
    mock_resilience_config = MagicMock()
    mock_resilience_config.strategy = MagicMock()
    mock_resilience_config.strategy.name = "BALANCED"
    mock_resilience_config.retry_config = MagicMock()
    mock_resilience_config.retry_config.max_attempts = 3
    mock_resilience_config.circuit_breaker_config = MagicMock()
    mock_resilience_config.circuit_breaker_config.failure_threshold = 5
    mock_resilience_config.enable_circuit_breaker = True
    mock_resilience_config.enable_retry = True
    mock_settings.get_resilience_config.return_value = mock_resilience_config
    
    # Mock operation strategy method per contract with successful behavior
    mock_settings.get_operation_strategy.return_value = "balanced"
    
    # Mock custom config validation method per contract with successful behavior
    mock_settings.validate_resilience_custom_config.return_value = {
        "is_valid": True,
        "errors": [],
        "warnings": ["No custom configuration provided"]
    }
    
    # Mock API keys method per contract with successful behavior
    mock_settings.get_valid_api_keys.return_value = ["test-api-key-12345", "key1", "key2", "key3"]
    
    # Mock development mode property per contract with successful behavior
    mock_settings.is_development = True
    
    # Mock additional compatibility methods per contract
    mock_settings.get_registered_operations.return_value = ["summarize", "sentiment", "key_points", "questions", "qa"]
    mock_settings.register_operation.return_value = None
    mock_settings.is_legacy_config = False
    mock_settings.get_operation_configs.return_value = {
        "summarize": {"strategy": "balanced"},
        "sentiment": {"strategy": "balanced"},
        "key_points": {"strategy": "balanced"},
        "questions": {"strategy": "balanced"},
        "qa": {"strategy": "balanced"}
    }
    mock_settings.get_preset_operations.return_value = ["summarize", "sentiment", "key_points", "questions", "qa"]
    mock_settings.get_all_operation_strategies.return_value = {
        "summarize": "balanced",
        "sentiment": "balanced", 
        "key_points": "balanced",
        "questions": "balanced",
        "qa": "balanced"
    }
    
    return mock_settings


@pytest.fixture
def mock_cache_factory():
    """
    Mock CacheFactory for testing cache creation behavior.
    
    Provides 'happy path' mock of the CacheFactory contract with all methods
    returning successful cache creation behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.factory import CacheFactory
    from app.infrastructure.cache.memory import InMemoryCache
    
    mock_factory = MagicMock(spec=CacheFactory)
    
    # Create a mock cache to return from factory methods
    mock_cache = AsyncMock(spec=InMemoryCache)
    mock_cache._internal_storage = {}
    
    async def mock_get(key):
        return mock_cache._internal_storage.get(key)
    
    async def mock_set(key, value, ttl=None):
        mock_cache._internal_storage[key] = value
        
    async def mock_delete(key):
        if key in mock_cache._internal_storage:
            del mock_cache._internal_storage[key]
            return True
        return False
    
    mock_cache.get.side_effect = mock_get
    mock_cache.set.side_effect = mock_set
    mock_cache.delete.side_effect = mock_delete
    
    # Mock factory methods per contract with successful cache creation
    mock_factory.for_web_app = AsyncMock(return_value=mock_cache)
    mock_factory.for_ai_app = AsyncMock(return_value=mock_cache)
    mock_factory.for_testing = AsyncMock(return_value=mock_cache)
    mock_factory.create_cache_from_config = AsyncMock(return_value=mock_cache)
    
    return mock_factory


@pytest.fixture
def mock_cache_interface():
    """
    Mock CacheInterface for testing cache operation behavior.
    
    Provides 'happy path' mock of the CacheInterface contract with all methods
    returning successful cache operation behavior as documented in the public interface.
    This is a stateful mock that maintains an internal dictionary for realistic
    cache behavior where set values can be retrieved later.
    """
    from app.infrastructure.cache.base import CacheInterface
    
    mock_cache = AsyncMock(spec=CacheInterface)
    
    # Create stateful internal storage
    mock_cache._internal_storage = {}
    
    async def mock_get(key):
        return mock_cache._internal_storage.get(key)
    
    async def mock_set(key, value, ttl=None):
        mock_cache._internal_storage[key] = value
        
    async def mock_delete(key):
        if key in mock_cache._internal_storage:
            del mock_cache._internal_storage[key]
            return True
        return False
    
    # Assign mock implementations
    mock_cache.get.side_effect = mock_get
    mock_cache.set.side_effect = mock_set
    mock_cache.delete.side_effect = mock_delete
    
    return mock_cache


@pytest.fixture
def mock_performance_monitor():
    """
    Mock CachePerformanceMonitor for testing metrics collection behavior.
    
    Provides 'happy path' mock of the CachePerformanceMonitor contract with all methods
    returning successful/normal behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.monitoring import CachePerformanceMonitor
    
    monitor = MagicMock(spec=CachePerformanceMonitor)
    
    # Mock initialization behavior per contract
    monitor.retention_hours = 1
    monitor.max_measurements = 1000
    monitor.memory_warning_threshold_bytes = 50 * 1024 * 1024  # 50MB
    monitor.memory_critical_threshold_bytes = 100 * 1024 * 1024  # 100MB
    
    # Mock performance tracking methods per contract
    monitor.record_key_generation_time.return_value = None
    monitor.record_cache_operation_time.return_value = None
    monitor.record_compression_ratio.return_value = None
    monitor.record_memory_usage.return_value = None
    monitor.record_invalidation_event.return_value = None
    
    # Mock async operation recording per contract
    monitor.record_operation = AsyncMock(return_value=None)
    
    # Mock statistics methods per contract with typical successful values
    monitor.get_performance_stats.return_value = {
        "timestamp": "2023-01-01T12:00:00Z",
        "cache_hit_rate": 75.0,
        "key_generation": {
            "avg_duration": 0.001,
            "total_operations": 100
        },
        "cache_operations": {
            "get": {"avg_duration": 0.002, "total_operations": 80},
            "set": {"avg_duration": 0.003, "total_operations": 75}
        },
        "compression": {
            "avg_ratio": 0.65,
            "total_compressed": 25
        },
        "memory_usage": {
            "total_cache_size_mb": 15.5,
            "entries": 100
        },
        "invalidation": {
            "hourly_rate": 5.2,
            "efficiency": 8.5
        }
    }
    
    monitor.get_invalidation_frequency_stats.return_value = {
        "rates": {
            "last_hour": 5.2,
            "last_day": 45.8,
            "average": 6.1
        },
        "thresholds": {
            "warning_threshold": 50,
            "critical_threshold": 100,
            "current_alert_level": "normal"
        },
        "patterns": {
            "most_common_pattern": "summarize",
            "most_common_type": "manual"
        },
        "efficiency": {
            "avg_keys_per_invalidation": 8.5,
            "avg_duration": 0.025
        }
    }
    
    monitor.get_invalidation_recommendations.return_value = []
    
    monitor.get_memory_usage_stats.return_value = {
        "current": {
            "total_cache_size_mb": 15.5,
            "memory_cache_size_mb": 5.2,
            "redis_cache_size_mb": 10.3,
            "entry_count": 100,
            "avg_entry_size_bytes": 160
        },
        "thresholds": {
            "warning_threshold_bytes": 50 * 1024 * 1024,
            "critical_threshold_bytes": 100 * 1024 * 1024,
            "warning_threshold_reached": False,
            "critical_threshold_reached": False
        },
        "trends": {
            "growth_rate_mb_per_hour": 0.5,
            "projected_warning_time_hours": 69.0
        }
    }
    
    monitor.get_memory_warnings.return_value = []
    
    monitor.get_recent_slow_operations.return_value = {
        "key_generation": [],
        "cache_operations": [],
        "compression": []
    }
    
    monitor.reset_stats.return_value = None
    
    monitor.export_metrics.return_value = {
        "key_generation_times": [],
        "cache_operation_times": [],
        "compression_ratios": [],
        "memory_usage_measurements": [],
        "invalidation_events": [],
        "cache_hits": 75,
        "cache_misses": 25,
        "total_operations": 100,
        "export_timestamp": "2023-01-01T12:00:00Z"
    }
    
    return monitor


@pytest.fixture
def mock_memory_cache():
    """
    Mock InMemoryCache for testing memory cache behavior.
    
    Provides 'happy path' mock of the InMemoryCache contract with all methods
    returning successful behavior as documented in the public interface.
    This is a stateful mock that maintains an internal dictionary for realistic
    cache behavior where set values can be retrieved later.
    """
    from app.infrastructure.cache.memory import InMemoryCache
    
    mock_cache = AsyncMock(spec=InMemoryCache)
    
    # Create stateful internal storage
    mock_cache._internal_storage = {}
    mock_cache._internal_stats = {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "deletes": 0
    }
    
    # Mock initialization parameters per contract
    mock_cache.default_ttl = 3600
    mock_cache.max_size = 100
    
    async def mock_get(key):
        if key in mock_cache._internal_storage:
            mock_cache._internal_stats["hits"] += 1
            return mock_cache._internal_storage[key]
        mock_cache._internal_stats["misses"] += 1
        return None
    
    async def mock_set(key, value, ttl=None):
        mock_cache._internal_storage[key] = value
        mock_cache._internal_stats["sets"] += 1
        
    async def mock_delete(key):
        if key in mock_cache._internal_storage:
            del mock_cache._internal_storage[key]
            mock_cache._internal_stats["deletes"] += 1
            return True
        return False
        
    async def mock_exists(key):
        return key in mock_cache._internal_storage
        
    async def mock_get_ttl(key):
        return 3600 if key in mock_cache._internal_storage else None
    
    def mock_clear():
        mock_cache._internal_storage.clear()
        
    def mock_size():
        return len(mock_cache._internal_storage)
        
    def mock_get_keys():
        return list(mock_cache._internal_storage.keys())
        
    def mock_get_active_keys():
        return list(mock_cache._internal_storage.keys())
        
    def mock_get_stats():
        return {
            "active_entries": len(mock_cache._internal_storage),
            "expired_entries": 0,
            "total_entries": len(mock_cache._internal_storage),
            "max_size": mock_cache.max_size,
            "utilization_percent": (len(mock_cache._internal_storage) / mock_cache.max_size) * 100,
            "hit_rate": mock_cache._internal_stats["hits"] / max(1, mock_cache._internal_stats["hits"] + mock_cache._internal_stats["misses"]),
            "hits": mock_cache._internal_stats["hits"],
            "misses": mock_cache._internal_stats["misses"],
            "evictions": 0,
            "memory_usage_bytes": len(str(mock_cache._internal_storage))
        }
    
    # Assign mock implementations
    mock_cache.get.side_effect = mock_get
    mock_cache.set.side_effect = mock_set
    mock_cache.delete.side_effect = mock_delete
    mock_cache.exists.side_effect = mock_exists
    mock_cache.get_ttl.side_effect = mock_get_ttl
    mock_cache.clear.side_effect = mock_clear
    mock_cache.size.side_effect = mock_size
    mock_cache.get_keys.side_effect = mock_get_keys
    mock_cache.get_active_keys.side_effect = mock_get_active_keys
    mock_cache.get_stats.side_effect = mock_get_stats
    
    return mock_cache


# =============================================================================
# Custom Exceptions
# =============================================================================

@pytest.fixture
def mock_validation_error():
    """
    Mock ValidationError for testing validation error handling behavior.
    
    Provides 'happy path' mock of the ValidationError contract as documented
    in the public interface. Uses spec to ensure mock accuracy.
    """
    from app.core.exceptions import ValidationError
    
    mock_error = MagicMock(spec=ValidationError)
    mock_error.__str__.return_value = "Validation failed"
    
    return mock_error


@pytest.fixture  
def mock_configuration_error():
    """
    Mock ConfigurationError for testing configuration error handling behavior.
    
    Provides 'happy path' mock of the ConfigurationError contract as documented
    in the public interface. Uses spec to ensure mock accuracy.
    """
    from app.core.exceptions import ConfigurationError
    
    mock_error = MagicMock(spec=ConfigurationError)
    mock_error.__str__.return_value = "Configuration error"
    
    return mock_error


@pytest.fixture
def mock_infrastructure_error():
    """
    Mock InfrastructureError for testing infrastructure error handling behavior.
    
    Provides 'happy path' mock of the InfrastructureError contract as documented
    in the public interface. Uses spec to ensure mock accuracy.
    """
    from app.core.exceptions import InfrastructureError
    
    mock_error = MagicMock(spec=InfrastructureError)
    mock_error.__str__.return_value = "Infrastructure error"
    
    return mock_error




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
        "preferences": {
            "theme": "dark",
            "language": "en"
        },
        "created_at": "2023-01-01T12:00:00Z"
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
        "metadata": {
            "model": "test-model",
            "processing_time": 1.2,
            "tokens_used": 150
        },
        "timestamp": "2023-01-01T12:00:00Z"
    }


@pytest.fixture
def sample_options():
    """
    Sample operation options for AI processing.
    """
    return {
        "max_length": 100,
        "temperature": 0.7,
        "language": "en"
    }


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
                "response": {"summary": "Brief summary", "confidence": 0.9}
            },
            "sentiment": {
                "text": "I love this product! It works perfectly.",
                "options": {"detailed": True},
                "response": {"sentiment": "positive", "confidence": 0.95, "score": 0.8}
            },
            "questions": {
                "text": "Climate change is a complex global issue affecting ecosystems.",
                "options": {"count": 3},
                "response": {
                    "questions": [
                        "What are the main causes of climate change?",
                        "How does climate change affect ecosystems?",
                        "What can be done to address climate change?"
                    ]
                }
            },
            "qa": {
                "text": "The company was founded in 2010 and has grown rapidly.",
                "options": {},
                "question": "When was the company founded?",
                "response": {"answer": "The company was founded in 2010.", "confidence": 1.0}
            }
        },
        "text_tiers": {
            "small": "Short text under 500 characters.",
            "medium": "Medium length text " * 50,  # ~1000 chars
            "large": "Very long text " * 500  # ~5000+ chars
        }
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
            "redis_version": "6.2.0"
        },
        "memory": {
            "memory_cache_entries": 85,
            "memory_cache_size": 100,
            "memory_usage": "1.2MB",
            "utilization_percent": 85.0,
            "evictions": 5
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
                "compression_savings_bytes": 125000
            }
        },
        "ai_metrics": {
            "total_operations": 180,
            "overall_hit_rate": 72.2,
            "operations": {
                "summarize": {"total": 80, "hits": 65, "hit_rate": 81.25},
                "sentiment": {"total": 60, "hits": 45, "hit_rate": 75.0},
                "questions": {"total": 40, "hits": 25, "hit_rate": 62.5}
            },
            "text_tiers": {
                "small": {"count": 50, "hit_rate": 85.0},
                "medium": {"count": 90, "hit_rate": 72.0},
                "large": {"count": 60, "hit_rate": 68.0}
            },
            "key_generation_stats": {
                "total_keys_generated": 180,
                "average_generation_time": 0.001
            }
        }
    }
