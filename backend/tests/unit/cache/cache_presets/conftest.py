"""
Test fixtures for cache presets unit tests.

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the cache_presets.pyi file.

Fixture Categories:
    - Basic test data fixtures (environment names, preset configurations)
    - Mock dependency fixtures (ValidationResult, CacheValidator)
    - Configuration test data (preset definitions, strategy configurations)
    - Environment detection fixtures (environment variables and contexts)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateless mocks for validation utilities (no state management needed)
    - Mock dependencies are spec'd against real classes for accuracy
"""

import os
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def sample_environment_names():
    """
    Sample environment names for testing environment detection.

    Provides a variety of environment naming patterns used to test
    the environment detection and recommendation functionality.
    """
    return [
        "development",
        "dev",
        "test",
        "testing",
        "staging",
        "stage",
        "production",
        "prod",
        "local",
        "ai-development",
        "ai-prod",
        "minimal",
        "embedded",
    ]


@pytest.fixture
def sample_preset_names():
    """
    Available preset names from the cache presets system.

    Provides the standard preset names as defined in the contract
    for testing preset retrieval and validation.
    """
    return [
        "disabled",
        "minimal",
        "simple",
        "development",
        "production",
        "ai-development",
        "ai-production",
    ]


@pytest.fixture
def sample_cache_strategy_values():
    """
    Sample CacheStrategy enum values for testing strategy-based functionality.

    Provides the available cache strategy values as defined in the contract
    for testing strategy-based configuration and validation.
    """
    return {
        "FAST": "fast",
        "BALANCED": "balanced",
        "ROBUST": "robust",
        "AI_OPTIMIZED": "ai_optimized",
    }


@pytest.fixture
def sample_cache_config_data():
    """
    Sample CacheConfig data for testing configuration functionality.

    Provides realistic cache configuration data matching the structure
    documented in the CacheConfig contract for testing configuration
    creation, validation, and conversion.
    """
    return {
        "strategy": "balanced",
        "redis_url": "redis://localhost:6379",
        "redis_password": None,
        "use_tls": False,
        "tls_cert_path": None,
        "default_ttl": 3600,
        "enable_compression": True,
        "compression_threshold": 1000,
        "max_connections": 10,
        "connection_timeout": 5,
        "enable_ai_features": False,
        "text_hash_threshold": 1000,
        "operation_specific_ttls": {"summarize": 7200, "sentiment": 3600},
    }


@pytest.fixture
def sample_secure_cache_config_data():
    """
    Sample secure CacheConfig data for testing TLS functionality.

    Provides cache configuration with security features enabled
    for testing secure configuration scenarios.
    """
    return {
        "strategy": "robust",
        "redis_url": "rediss://secure-redis:6380",
        "redis_password": "secure_password",
        "use_tls": True,
        "tls_cert_path": "/etc/ssl/certs/redis.crt",
        "default_ttl": 7200,
        "enable_compression": True,
        "compression_threshold": 500,
        "max_connections": 20,
        "connection_timeout": 10,
        "enable_ai_features": False,
        "text_hash_threshold": 1000,
        "operation_specific_ttls": {},
    }


@pytest.fixture
def sample_ai_cache_config_data():
    """
    Sample AI-optimized CacheConfig data for testing AI features.

    Provides cache configuration with AI features enabled
    for testing AI-specific configuration scenarios.
    """
    return {
        "strategy": "ai_optimized",
        "redis_url": "redis://ai-cache:6379",
        "redis_password": None,
        "use_tls": False,
        "tls_cert_path": None,
        "default_ttl": 1800,
        "enable_compression": True,
        "compression_threshold": 1000,
        "max_connections": 15,
        "connection_timeout": 8,
        "enable_ai_features": True,
        "text_hash_threshold": 500,
        "operation_specific_ttls": {
            "summarize": 1800,
            "sentiment": 900,
            "key_points": 1200,
            "questions": 1500,
            "qa": 900,
        },
    }


@pytest.fixture
def sample_cache_preset_data():
    """
    Sample CachePreset data for testing preset functionality.

    Provides realistic preset configuration data matching the structure
    documented in the CachePreset contract for testing preset creation,
    validation, and conversion.
    """
    return {
        "name": "test_preset",
        "description": "Test preset for unit testing",
        "strategy": "balanced",
        "default_ttl": 3600,
        "max_connections": 10,
        "connection_timeout": 5,
        "memory_cache_size": 100,
        "compression_threshold": 1000,
        "compression_level": 6,
        "enable_ai_cache": False,
        "enable_monitoring": True,
        "log_level": "INFO",
        "environment_contexts": ["testing"],
        "ai_optimizations": {},
    }


@pytest.fixture
def sample_ai_preset_data():
    """
    Sample AI-optimized CachePreset data for testing AI preset functionality.

    Provides AI-specific preset configuration with AI optimizations
    for testing AI-related preset scenarios.
    """
    return {
        "name": "test_ai_preset",
        "description": "AI-optimized test preset",
        "strategy": "ai_optimized",
        "default_ttl": 1800,
        "max_connections": 15,
        "connection_timeout": 8,
        "memory_cache_size": 200,
        "compression_threshold": 500,
        "compression_level": 6,
        "enable_ai_cache": True,
        "enable_monitoring": True,
        "log_level": "DEBUG",
        "environment_contexts": ["ai-development", "testing"],
        "ai_optimizations": {
            "text_hash_threshold": 500,
            "hash_algorithm": "sha256",
            "text_size_tiers": {"small": 500, "medium": 2000, "large": 10000},
            "operation_ttls": {"summarize": 1800, "sentiment": 900, "key_points": 1200},
            "enable_smart_promotion": True,
            "max_text_length": 50000,
        },
    }


@pytest.fixture
def sample_environment_recommendation():
    """
    Sample EnvironmentRecommendation for testing recommendation functionality.

    Provides a realistic environment recommendation result matching the
    EnvironmentRecommendation contract structure.
    """
    return {
        "preset_name": "development",
        "confidence": 0.95,
        "reasoning": [
            "Environment variable NODE_ENV=development detected",
            "Development context indicators found",
            "Fast feedback configuration recommended",
        ],
        "environment_detected": "development",
        "fallback_used": False,
    }


@pytest.fixture
def mock_environment_variables():
    """
    Mock environment variables for testing environment detection.

    Provides a controlled set of environment variables that can be
    used to test environment detection without affecting the actual
    system environment.
    """
    return {
        "NODE_ENV": "development",
        "ENVIRONMENT": "dev",
        "STAGE": "testing",
        "DEPLOYMENT_ENV": "local",
        "CACHE_PRESET": "simple",
    }


@pytest.fixture
def preset_manager_test_data():
    """
    Test data for CachePresetManager functionality.

    Provides comprehensive test data including presets, recommendations,
    and validation scenarios for testing the preset manager.
    """
    return {
        "available_presets": [
            "disabled",
            "minimal",
            "simple",
            "development",
            "production",
            "ai-development",
            "ai-production",
        ],
        "environment_mappings": {
            "dev": "development",
            "development": "development",
            "test": "simple",
            "testing": "simple",
            "stage": "production",
            "staging": "production",
            "prod": "production",
            "production": "production",
            "ai-dev": "ai-development",
            "ai-prod": "ai-production",
        },
        "validation_scenarios": {
            "valid_preset": {
                "name": "custom_valid",
                "strategy": "balanced",
                "default_ttl": 3600,
            },
            "invalid_preset": {
                "name": "custom_invalid",
                "strategy": "unknown_strategy",
                "default_ttl": -1,
            },
        },
    }


@pytest.fixture
def default_presets_sample():
    """
    Sample DEFAULT_PRESETS data for testing strategy-based configurations.

    Provides sample strategy-based preset configurations as would be
    returned by get_default_presets() function for testing.
    """
    return {
        "fast": {
            "strategy": "fast",
            "default_ttl": 300,
            "max_connections": 5,
            "compression_level": 1,
            "enable_ai_features": False,
        },
        "balanced": {
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "compression_level": 6,
            "enable_ai_features": False,
        },
        "robust": {
            "strategy": "robust",
            "default_ttl": 7200,
            "max_connections": 20,
            "compression_level": 9,
            "enable_ai_features": False,
        },
        "ai_optimized": {
            "strategy": "ai_optimized",
            "default_ttl": 1800,
            "max_connections": 15,
            "compression_level": 6,
            "enable_ai_features": True,
        },
    }


@pytest.fixture
def configuration_conversion_test_data():
    """
    Test data for configuration conversion functionality.

    Provides before/after data for testing preset to configuration
    conversion and dictionary serialization methods.
    """
    return {
        "preset_input": {
            "name": "conversion_test",
            "description": "Test preset for conversion",
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "enable_ai_cache": False,
        },
        "expected_config_output": {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "max_connections": 10,
            "enable_compression": True,
            "enable_ai_features": False,
        },
        "expected_dict_output": {
            "name": "conversion_test",
            "description": "Test preset for conversion",
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "enable_ai_cache": False,
        },
    }
