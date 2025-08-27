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


# Note: sample_text, sample_short_text, sample_long_text, sample_ai_response, 
# and sample_options fixtures are now provided by the parent conftest.py


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
    
    Provides 'happy path' mock of the CacheParameterMapper contract with all methods
    returning successful parameter mapping behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.parameter_mapping import CacheParameterMapper, ValidationResult
    
    mapper = MagicMock(spec=CacheParameterMapper)
    
    # Mock successful parameter mapping per contract
    def mock_map_params(ai_params):
        generic_params = {
            "redis_url": ai_params.get("redis_url", "redis://localhost:6379"),
            "default_ttl": ai_params.get("default_ttl", 3600),
            "enable_l1_cache": True,
            "l1_cache_size": ai_params.get("memory_cache_size", 100),
            "compression_threshold": ai_params.get("compression_threshold", 1000),
            "compression_level": ai_params.get("compression_level", 6),
            "performance_monitor": ai_params.get("performance_monitor")
        }
        ai_specific_params = {
            "text_hash_threshold": ai_params.get("text_hash_threshold", 1000),
            "hash_algorithm": ai_params.get("hash_algorithm", hashlib.sha256),
            "text_size_tiers": ai_params.get("text_size_tiers", {
                "small": 500,
                "medium": 5000, 
                "large": 50000
            }),
            "operation_ttls": ai_params.get("operation_ttls", {})
        }
        return generic_params, ai_specific_params
    
    mapper.map_ai_to_generic_params.side_effect = mock_map_params
    
    # Mock validation results per contract - successful validation
    def mock_validation(ai_params):
        result = MagicMock(spec=ValidationResult)
        result.is_valid = True
        result.errors = []
        result.warnings = []
        result.recommendations = []
        result.parameter_conflicts = {}
        result.ai_specific_params = set(["text_hash_threshold", "hash_algorithm", "text_size_tiers", "operation_ttls"])
        result.generic_params = set(["redis_url", "default_ttl", "l1_cache_size", "compression_threshold", "compression_level"])
        result.context = {"validation_timestamp": "2023-01-01T12:00:00Z"}
        
        # Mock methods per ValidationResult contract
        result.add_error = MagicMock()
        result.add_warning = MagicMock()
        result.add_recommendation = MagicMock()
        result.add_conflict = MagicMock()
        
        return result
    
    mapper.validate_parameter_compatibility.side_effect = mock_validation
    
    # Mock information method per contract
    mapper.get_parameter_info.return_value = {
        "generic_parameters": ["redis_url", "default_ttl", "l1_cache_size", "compression_threshold", "compression_level"],
        "ai_specific_parameters": ["text_hash_threshold", "hash_algorithm", "text_size_tiers", "operation_ttls"],
        "parameter_mappings": {
            "memory_cache_size": "l1_cache_size"
        },
        "validation_rules": {
            "redis_url": "Must be valid Redis URL",
            "default_ttl": "Must be positive integer",
            "text_hash_threshold": "Must be positive integer between 100-100000"
        }
    }
    
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
    
    Provides 'happy path' mock of the CacheKeyGenerator contract with all methods
    returning successful behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.key_generator import CacheKeyGenerator
    
    generator = MagicMock(spec=CacheKeyGenerator)
    
    # Mock initialization behavior per contract
    generator.text_hash_threshold = 1000
    generator.hash_algorithm = hashlib.sha256
    generator.performance_monitor = None
    
    # Mock key generation method per contract - returns properly formatted cache keys
    def mock_generate_key(text, operation, options):
        # Simulate the documented key format: "ai_cache:op:{operation}|txt:{text_or_hash}|opts:{options_hash}"
        if len(text) > generator.text_hash_threshold:
            text_part = f"hash:{hashlib.sha256(text.encode()).hexdigest()[:12]}"
        else:
            text_part = text[:50] + ("..." if len(text) > 50 else "")
        
        options_hash = hashlib.sha256(str(sorted(options.items())).encode()).hexdigest()[:8]
        key = f"ai_cache:op:{operation}|txt:{text_part}|opts:{options_hash}"
        
        # Extract question from options for Q&A operations
        if options and "question" in options:
            question_hash = hashlib.sha256(options["question"].encode()).hexdigest()[:8]
            key += f"|q:{question_hash}"
            
        return key
    
    generator.generate_cache_key.side_effect = mock_generate_key
    
    # Mock statistics method per contract
    generator.get_key_generation_stats.return_value = {
        "total_keys_generated": 150,
        "average_generation_time": 0.001,
        "text_size_distribution": {
            "small": 60,
            "medium": 70,
            "large": 20
        },
        "operation_distribution": {
            "summarize": 80,
            "sentiment": 45,
            "questions": 25
        },
        "recent_performance": {
            "last_100_avg_time": 0.0008,
            "fastest_time": 0.0001,
            "slowest_time": 0.005
        }
    }
    
    return generator


# Note: mock_performance_monitor fixture is now provided by the parent conftest.py

# Note: mock_generic_redis_cache fixture is now provided by the parent conftest.py


@pytest.fixture 
def mock_redis_connection_failure():
    """
    Mock Redis connection failure for testing graceful degradation behavior.
    
    Provides mock that simulates Redis connection failures as documented in the
    GenericRedisCache contract for testing error handling and graceful degradation.
    """
    from app.infrastructure.cache.redis_generic import GenericRedisCache
    
    with patch('app.infrastructure.cache.redis_generic.GenericRedisCache') as mock_class:
        mock_instance = AsyncMock(spec=GenericRedisCache)
        
        # Mock connection failure per contract
        mock_instance.connect.return_value = False  # Connection failed
        
        # Mock operations fail with appropriate infrastructure errors
        mock_instance.get.side_effect = InfrastructureError(
            "Redis connection failed", 
            {"operation": "get", "redis_url": "redis://localhost:6379"}
        )
        mock_instance.set.side_effect = InfrastructureError(
            "Redis connection failed", 
            {"operation": "set", "redis_url": "redis://localhost:6379"}
        )
        mock_instance.delete.side_effect = InfrastructureError(
            "Redis connection failed", 
            {"operation": "delete", "redis_url": "redis://localhost:6379"}
        )
        mock_instance.exists.side_effect = InfrastructureError(
            "Redis connection failed", 
            {"operation": "exists", "redis_url": "redis://localhost:6379"}
        )
        
        # Mock security methods still work (they don't depend on Redis connection)
        mock_instance.validate_security.return_value = None
        mock_instance.get_security_status.return_value = {
            "security_level": "basic", 
            "connection_encrypted": False,
            "redis_connected": False
        }
        
        mock_class.return_value = mock_instance
        yield mock_instance


# Note: ai_cache_test_data fixture is now provided by the parent conftest.py


# Note: mock_memory_cache fixture is now provided by the parent conftest.py


# Note: cache_statistics_sample fixture is now provided by the parent conftest.py