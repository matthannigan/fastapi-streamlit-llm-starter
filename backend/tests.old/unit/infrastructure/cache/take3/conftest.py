"""
Test fixtures for AIResponseCache unit tests.

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_ai.pyi file.

Fixture Categories:
    - Basic test data fixtures (sample texts, operations, responses)
    - Mock dependency fixtures (parameter mapper, key generator, monitor)
    - Configuration fixtures (valid/invalid parameter sets)
    - Error scenario fixtures (exception mocks, connection failures)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
import hashlib
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError


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


@pytest.fixture
def valid_ai_params():
    """
    Valid AIResponseCache initialization parameters.
    
    Provides a complete set of valid parameters that should pass
    validation and allow successful cache initialization.
    """
    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "text_hash_threshold": 1000,
        "hash_algorithm": hashlib.sha256,
        "compression_threshold": 1000,
        "compression_level": 6,
        "text_size_tiers": {
            "small": 500,
            "medium": 5000,
            "large": 50000
        },
        "memory_cache_size": 100,
        "operation_ttls": {
            "summarize": 7200,
            "sentiment": 1800,
            "questions": 3600
        }
    }


@pytest.fixture
def invalid_ai_params():
    """
    Invalid AIResponseCache initialization parameters for testing validation errors.
    """
    return {
        "redis_url": "",  # Empty URL should fail validation
        "default_ttl": -1,  # Negative TTL should fail
        "text_hash_threshold": "invalid",  # Wrong type
        "memory_cache_size": 0,  # Zero cache size should fail
        "compression_level": 15  # Out of range (1-9)
    }


@pytest.fixture
def mock_parameter_mapper():
    """
    Mock CacheParameterMapper for testing parameter mapping behavior.
    
    Configured to return expected generic and AI-specific parameter
    separation as documented in the parameter mapping interface.
    """
    mapper = MagicMock()
    
    # Mock successful parameter mapping
    def mock_map_params(ai_params):
        generic_params = {
            "redis_url": ai_params.get("redis_url", "redis://localhost:6379"),
            "default_ttl": ai_params.get("default_ttl", 3600),
            "l1_cache_size": ai_params.get("memory_cache_size", 100),
            "compression_threshold": ai_params.get("compression_threshold", 1000),
            "compression_level": ai_params.get("compression_level", 6)
        }
        ai_specific_params = {
            "text_hash_threshold": ai_params.get("text_hash_threshold", 1000),
            "hash_algorithm": ai_params.get("hash_algorithm", hashlib.sha256),
            "text_size_tiers": ai_params.get("text_size_tiers", {}),
            "operation_ttls": ai_params.get("operation_ttls", {})
        }
        return generic_params, ai_specific_params
    
    mapper.map_ai_to_generic_params.side_effect = mock_map_params
    
    # Mock validation results
    validation_result = MagicMock()
    validation_result.is_valid = True
    validation_result.errors = []
    validation_result.warnings = []
    validation_result.recommendations = []
    mapper.validate_parameter_compatibility.return_value = validation_result
    
    return mapper


@pytest.fixture
def mock_parameter_mapper_with_validation_errors():
    """
    Mock parameter mapper that returns validation errors for testing error handling.
    """
    mapper = MagicMock()
    
    # Mock validation with errors
    validation_result = MagicMock()
    validation_result.is_valid = False
    validation_result.errors = [
        "redis_url cannot be empty",
        "text_hash_threshold must be positive integer"
    ]
    validation_result.warnings = ["Low TTL may impact performance"]
    validation_result.recommendations = ["Consider enabling compression"]
    mapper.validate_parameter_compatibility.return_value = validation_result
    
    # Make mapping raise ValidationError
    mapper.map_ai_to_generic_params.side_effect = ValidationError("Parameter mapping failed")
    
    return mapper


@pytest.fixture
def mock_key_generator():
    """
    Mock CacheKeyGenerator for testing key generation behavior.
    """
    generator = MagicMock()
    
    # Mock key generation methods
    generator.generate_cache_key.return_value = "ai_cache:test_operation:abc123hash"
    generator.determine_text_tier.return_value = "medium"
    
    return generator


@pytest.fixture
def mock_performance_monitor():
    """
    Mock CachePerformanceMonitor for testing metrics collection behavior.
    """
    monitor = MagicMock()
    
    # Mock performance tracking methods
    monitor.record_cache_hit.return_value = None
    monitor.record_cache_miss.return_value = None
    monitor.record_cache_set.return_value = None
    monitor.get_hit_ratio.return_value = 0.75
    monitor.get_performance_summary.return_value = {
        "hit_ratio": 0.75,
        "total_operations": 100,
        "cache_hits": 75,
        "cache_misses": 25,
        "recent_avg_cache_operation_time": 0.05
    }
    
    return monitor


@pytest.fixture
def mock_generic_redis_cache():
    """
    Mock GenericRedisCache parent class for testing inheritance behavior.
    
    Configured with expected parent class methods and their documented behavior.
    """
    with patch('app.infrastructure.cache.redis_generic.GenericRedisCache') as mock_class:
        mock_instance = AsyncMock()
        
        # Mock parent class methods
        mock_instance.connect.return_value = True
        mock_instance.disconnect.return_value = None
        mock_instance.get.return_value = None  # Cache miss by default
        mock_instance.set.return_value = None
        mock_instance.delete.return_value = True
        mock_instance.exists.return_value = False
        mock_instance.register_callback.return_value = None
        
        # Mock callback system
        mock_instance._callbacks = {}
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture 
def mock_redis_connection_failure():
    """
    Mock Redis connection failure for testing graceful degradation behavior.
    """
    with patch('app.infrastructure.cache.redis_generic.GenericRedisCache') as mock_class:
        mock_instance = AsyncMock()
        mock_instance.connect.return_value = False  # Connection failed
        mock_instance.get.side_effect = InfrastructureError("Redis connection failed")
        mock_instance.set.side_effect = InfrastructureError("Redis connection failed")
        
        mock_class.return_value = mock_instance
        yield mock_instance


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
    """
    return {
        "redis": {
            "connected": True,
            "keys": 150,
            "memory_usage": "2.5MB",
            "hit_ratio": 0.78
        },
        "memory": {
            "memory_cache_entries": 85,
            "memory_cache_size": 100,
            "memory_usage": "1.2MB"
        },
        "performance": {
            "hit_ratio": 0.75,
            "total_operations": 200,
            "cache_hits": 150,
            "cache_misses": 50,
            "recent_avg_cache_operation_time": 0.045,
            "compression_stats": {
                "compressed_entries": 45,
                "compression_ratio": 0.65
            }
        },
        "ai_metrics": {
            "operations": {
                "summarize": {"total": 80, "hits": 65, "hit_rate": 0.8125},
                "sentiment": {"total": 60, "hits": 45, "hit_rate": 0.75},
                "questions": {"total": 40, "hits": 25, "hit_rate": 0.625}
            },
            "text_tiers": {
                "small": {"count": 50, "hit_rate": 0.85},
                "medium": {"count": 90, "hit_rate": 0.72},
                "large": {"count": 60, "hit_rate": 0.68}
            }
        }
    }