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


# Note: ai_cache_test_data fixture is now provided by the parent conftest.py


# Note: cache_statistics_sample fixture is now provided by the parent conftest.py