"""
Test fixtures for config module unit tests.

This module provides reusable fixtures specific to cache configuration testing,
focused on providing real configuration instances and test data following
behavior-driven testing principles.

Fixture Categories:
    - Configuration parameter fixtures (basic, comprehensive, invalid)
    - ValidationResult fixtures (valid and invalid states)
    - AI configuration fixtures (valid and invalid AI parameters)
    - Environment variable fixtures for testing environment loading
"""

import pytest
from pathlib import Path
from app.infrastructure.cache.config import ValidationResult, AICacheConfig


# =============================================================================
# Configuration Parameter Fixtures
# =============================================================================

@pytest.fixture
def valid_basic_config_params():
    """Valid basic configuration parameters for minimal CacheConfig testing."""
    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "memory_cache_size": 100,
        "environment": "development"
    }


@pytest.fixture
def valid_comprehensive_config_params():
    """Valid comprehensive configuration parameters including all features."""
    return {
        "redis_url": "redis://prod-redis:6379",
        "redis_password": "secure-password",
        "use_tls": True,
        "tls_cert_path": "/certs/redis.crt",
        "tls_key_path": "/certs/redis.key",
        "default_ttl": 7200,
        "memory_cache_size": 200,
        "compression_threshold": 1000,
        "compression_level": 6,
        "environment": "production",
        "enable_ai_cache": True,
        "ai_config": {
            "text_hash_threshold": 1500,
            "hash_algorithm": "sha256",
            "text_size_tiers": {
                "small": 1000,
                "medium": 10000,
                "large": 100000
            },
            "operation_ttls": {
                "summarize": 7200,
                "sentiment": 3600,
                "key_points": 5400
            },
            "enable_smart_promotion": True,
            "max_text_length": 100000
        }
    }


@pytest.fixture
def invalid_config_params():
    """Invalid configuration parameters that should trigger validation errors."""
    return {
        "redis_url": "invalid-url-format",  # Invalid URL scheme
        "default_ttl": -100,  # Negative TTL
        "memory_cache_size": 0,  # Zero size
        "compression_level": 15,  # Out of range
        "compression_threshold": -50,  # Negative threshold
        "environment": "invalid-env"  # Unsupported environment
    }


# =============================================================================
# ValidationResult Fixtures
# =============================================================================

@pytest.fixture
def sample_validation_result_valid():
    """ValidationResult instance representing successful validation."""
    return ValidationResult(is_valid=True)


@pytest.fixture
def sample_validation_result_invalid():
    """ValidationResult instance with mixed errors and warnings."""
    result = ValidationResult(is_valid=True)
    result.add_error("Configuration parameter is invalid")
    result.add_error("Required field is missing")
    result.add_warning("Configuration could be optimized")
    result.add_warning("Parameter value is suboptimal")
    return result


# =============================================================================
# AI Configuration Fixtures
# =============================================================================

@pytest.fixture
def valid_ai_config_params():
    """Valid AI-specific configuration parameters."""
    return {
        "text_hash_threshold": 1500,
        "hash_algorithm": "sha256",
        "text_size_tiers": {
            "small": 1000,
            "medium": 10000,
            "large": 100000
        },
        "operation_ttls": {
            "summarize": 7200,
            "sentiment": 3600,
            "key_points": 5400,
            "questions": 4800,
            "qa": 3600
        },
        "enable_smart_promotion": True,
        "max_text_length": 100000
    }


@pytest.fixture
def invalid_ai_config_params():
    """Invalid AI configuration parameters for testing validation errors."""
    return {
        "text_hash_threshold": -100,  # Negative threshold
        "hash_algorithm": "invalid-algorithm",  # Unsupported algorithm
        "text_size_tiers": {
            "small": 0,  # Zero size
            "medium": "invalid"  # Wrong type
        },
        "operation_ttls": {
            "summarize": -1000,  # Negative TTL
            "sentiment": 1000000  # Excessively long TTL (>1 week)
        },
        "max_text_length": -1000  # Negative length
    }


# =============================================================================
# Builder State Fixtures
# =============================================================================

@pytest.fixture
def builder_with_basic_config():
    """CacheConfigBuilder with basic configuration for accumulation testing."""
    from app.infrastructure.cache.config import CacheConfigBuilder
    builder = CacheConfigBuilder()
    builder.for_environment("development")
    builder.with_redis("redis://test:6379")
    return builder


@pytest.fixture
def builder_with_comprehensive_config(tmp_path):
    """CacheConfigBuilder with comprehensive configuration for build testing."""
    from app.infrastructure.cache.config import CacheConfigBuilder
    
    # Create temporary cert files for TLS testing
    cert_file = tmp_path / "redis.crt"
    key_file = tmp_path / "redis.key"
    cert_file.write_text("dummy-cert-content")
    key_file.write_text("dummy-key-content")
    
    builder = CacheConfigBuilder()
    builder.for_environment("production")
    builder.with_redis("redis://prod:6379", password="test-password", use_tls=True)
    builder.with_security(str(cert_file), str(key_file))
    builder.with_compression(threshold=1500, level=7)
    builder.with_ai_features(text_hash_threshold=2000, hash_algorithm="sha256")
    return builder


# =============================================================================
# File Operation Fixtures
# =============================================================================

@pytest.fixture
def sample_config_file_content():
    """Sample configuration file content for testing file loading."""
    return {
        "redis_url": "redis://file-config:6379",
        "redis_password": "file-password",
        "use_tls": True,
        "default_ttl": 5400,
        "memory_cache_size": 150,
        "compression_threshold": 800,
        "compression_level": 5,
        "environment": "testing",
        "ai_config": {
            "text_hash_threshold": 1200,
            "hash_algorithm": "sha256",
            "operation_ttls": {
                "summarize": 3600,
                "sentiment": 1800
            }
        }
    }


@pytest.fixture
def temp_config_file(tmp_path, sample_config_file_content):
    """Temporary configuration file for testing file operations."""
    import json
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(sample_config_file_content, indent=2))
    return config_file


@pytest.fixture
def invalid_config_file(tmp_path):
    """Invalid JSON configuration file for testing error handling."""
    config_file = tmp_path / "invalid_config.json"
    config_file.write_text('{"invalid": "json", "missing_closing_brace": true')
    return config_file


# =============================================================================
# Environment Variable Fixtures
# =============================================================================

@pytest.fixture
def environment_variables_basic():
    """Basic environment variables for testing environment loading."""
    return {
        "CACHE_PRESET": "development",
        "CACHE_REDIS_URL": "redis://test:6379",
        "CACHE_DEFAULT_TTL": "1800"
    }


@pytest.fixture
def environment_variables_comprehensive():
    """Comprehensive environment variables including all features."""
    return {
        "CACHE_PRESET": "production",
        "CACHE_REDIS_URL": "redis://prod:6379",
        "CACHE_REDIS_PASSWORD": "prod-password",
        "CACHE_USE_TLS": "true",
        "CACHE_TLS_CERT_PATH": "/certs/redis.crt",
        "CACHE_TLS_KEY_PATH": "/certs/redis.key",
        "CACHE_DEFAULT_TTL": "7200",
        "CACHE_MEMORY_SIZE": "200",
        "CACHE_COMPRESSION_THRESHOLD": "1000",
        "CACHE_COMPRESSION_LEVEL": "6",
        "CACHE_AI_ENABLED": "true",
        "CACHE_AI_TEXT_HASH_THRESHOLD": "1500",
        "CACHE_AI_HASH_ALGORITHM": "sha256"
    }
