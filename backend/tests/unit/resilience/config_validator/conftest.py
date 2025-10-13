"""
Config validator module test fixtures providing component-specific test data.

Provides component-specific test data and fixtures for config validator testing
following the philosophy of behavior-driven testing.

Note: Common fixtures (fake_threading_module, fake_time_module, mock_logger)
have been moved to the shared resilience/conftest.py file to eliminate
duplication across modules.

External Dependencies Handled (in shared conftest.py):
    - threading: Standard library threading module (fake implementation)
    - time: Standard library time module (fake implementation)
    - logging: Standard library logging system (mocked)
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Enum for validation status results used in test scenarios."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"
    PENDING = "pending"


class ConfigType(Enum):
    """Enum for configuration types used in test scenarios."""
    RESILIENCE = "resilience"
    CACHE = "cache"
    SECURITY = "security"
    MONITORING = "monitoring"
    AI = "ai"


@dataclass
class ValidationResult:
    """Fake validation result for testing validation behavior."""
    status: ValidationStatus
    config_type: ConfigType
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    timestamp: float


@dataclass
class ConfigValidationScenario:
    """Fake configuration validation scenario for testing."""
    name: str
    config_data: Dict[str, Any]
    expected_status: ValidationStatus
    expected_errors: List[str]
    expected_warnings: List[str]
    description: str


@pytest.fixture
def config_validator_test_data():
    """
    Standardized test data for config validator behavior testing.

    Provides consistent test scenarios and data structures for config validator
    testing across different test modules. Ensures test consistency and reduces
    duplication in validation testing implementations.

    Data Structure:
        - valid_configurations: Examples of valid configurations
        - invalid_configurations: Examples of invalid configurations with expected errors
        - warning_configurations: Valid but suboptimal configurations with warnings
        - security_scenarios: Security-focused validation test cases
        - performance_scenarios: Performance-related validation test cases

    Use Cases:
        - Standardizing config validator test inputs across test modules
        - Providing comprehensive validation scenario coverage
        - Testing different configuration type combinations
        - Reducing test code duplication while ensuring thorough coverage

    Example:
        def test_validator_with_various_configurations(config_validator_test_data):
            for scenario in config_validator_test_data['valid_configurations']:
                # Test validator with each valid configuration
                result = validator.validate(scenario['config'])
                assert result.status == "valid"
    """
    return {
        "valid_configurations": [
            {
                "name": "basic_resilience_config",
                "config_type": "resilience",
                "config": {
                    "retry_attempts": 3,
                    "circuit_breaker_threshold": 5,
                    "timeout_seconds": 30,
                    "backoff_multiplier": 2.0
                },
                "description": "Basic valid resilience configuration"
            },
            {
                "name": "production_cache_config",
                "config_type": "cache",
                "config": {
                    "redis_url": "redis://localhost:6379",
                    "default_ttl": 3600,
                    "max_connections": 10,
                    "fallback_enabled": True
                },
                "description": "Production-ready cache configuration"
            },
            {
                "name": "security_config",
                "config_type": "security",
                "config": {
                    "api_key_required": True,
                    "rate_limit_enabled": True,
                    "max_requests_per_minute": 60,
                    "cors_origins": ["https://example.com"]
                },
                "description": "Valid security configuration"
            },
            {
                "name": "monitoring_config",
                "config_type": "monitoring",
                "config": {
                    "metrics_enabled": True,
                    "health_check_interval": 30,
                    "alert_thresholds": {
                        "error_rate": 0.1,
                        "response_time": 5.0
                    }
                },
                "description": "Comprehensive monitoring configuration"
            }
        ],
        "invalid_configurations": [
            {
                "name": "negative_retry_attempts",
                "config_type": "resilience",
                "config": {
                    "retry_attempts": -1,
                    "circuit_breaker_threshold": 5,
                    "timeout_seconds": 30
                },
                "expected_errors": ["retry_attempts must be non-negative"],
                "description": "Invalid negative retry attempts"
            },
            {
                "name": "zero_timeout",
                "config_type": "resilience",
                "config": {
                    "retry_attempts": 3,
                    "circuit_breaker_threshold": 5,
                    "timeout_seconds": 0
                },
                "expected_errors": ["timeout_seconds must be positive"],
                "description": "Invalid zero timeout configuration"
            },
            {
                "name": "invalid_redis_url",
                "config_type": "cache",
                "config": {
                    "redis_url": "invalid-url",
                    "default_ttl": 3600
                },
                "expected_errors": ["redis_url must be a valid URL"],
                "description": "Invalid Redis URL format"
            },
            {
                "name": "missing_required_field",
                "config_type": "security",
                "config": {
                    "rate_limit_enabled": True,
                    "max_requests_per_minute": 60
                },
                "expected_errors": ["api_key_required is required"],
                "description": "Missing required security field"
            }
        ],
        "warning_configurations": [
            {
                "name": "high_retry_attempts",
                "config_type": "resilience",
                "config": {
                    "retry_attempts": 10,
                    "circuit_breaker_threshold": 5,
                    "timeout_seconds": 30
                },
                "expected_warnings": ["High retry attempts may cause performance issues"],
                "description": "Valid but potentially problematic retry configuration"
            },
            {
                "name": "short_ttl",
                "config_type": "cache",
                "config": {
                    "redis_url": "redis://localhost:6379",
                    "default_ttl": 10,
                    "max_connections": 10
                },
                "expected_warnings": ["Short TTL may cause frequent cache misses"],
                "description": "Very short cache TTL"
            },
            {
                "name": "permissive_cors",
                "config_type": "security",
                "config": {
                    "api_key_required": True,
                    "rate_limit_enabled": True,
                    "cors_origins": ["*"]
                },
                "expected_warnings": ["Permissive CORS policy may security risks"],
                "description": "Overly permissive CORS configuration"
            }
        ],
        "security_scenarios": [
            {
                "name": "hardcoded_credentials",
                "config_type": "security",
                "config": {
                    "api_key": "hardcoded-key-123",
                    "api_key_required": True
                },
                "expected_errors": ["Hardcoded API keys detected"],
                "security_level": "critical",
                "description": "Security violation: hardcoded credentials"
            },
            {
                "name": "disabled_security",
                "config_type": "security",
                "config": {
                    "api_key_required": False,
                    "rate_limit_enabled": False,
                    "cors_origins": ["*"]
                },
                "expected_warnings": [
                    "API key authentication disabled",
                    "Rate limiting disabled",
                    "Permissive CORS policy"
                ],
                "security_level": "warning",
                "description": "Multiple security features disabled"
            },
            {
                "name": "weak_rate_limit",
                "config_type": "security",
                "config": {
                    "api_key_required": True,
                    "rate_limit_enabled": True,
                    "max_requests_per_minute": 10000
                },
                "expected_warnings": ["Very high rate limit may not prevent abuse"],
                "security_level": "info",
                "description": "Weak rate limiting configuration"
            }
        ],
        "performance_scenarios": [
            {
                "name": "large_connection_pool",
                "config_type": "cache",
                "config": {
                    "redis_url": "redis://localhost:6379",
                    "max_connections": 1000,
                    "default_ttl": 3600
                },
                "expected_warnings": ["Large connection pool may consume excessive resources"],
                "performance_impact": "high",
                "description": "Potentially excessive connection pool size"
            },
            {
                "name": "frequent_health_checks",
                "config_type": "monitoring",
                "config": {
                    "metrics_enabled": True,
                    "health_check_interval": 1
                },
                "expected_warnings": ["Frequent health checks may impact performance"],
                "performance_impact": "medium",
                "description": "Very frequent health check interval"
            },
            {
                "name": "aggressive_circuit_breaker",
                "config_type": "resilience",
                "config": {
                    "circuit_breaker_threshold": 1,
                    "recovery_timeout": 1
                },
                "expected_warnings": ["Aggressive circuit breaker may cause frequent tripping"],
                "performance_impact": "medium",
                "description": "Very sensitive circuit breaker configuration"
            }
        ],
        "edge_cases": [
            {
                "name": "empty_configuration",
                "config_type": "resilience",
                "config": {},
                "expected_errors": ["Required configuration missing"],
                "description": "Completely empty configuration"
            },
            {
                "name": "null_values",
                "config_type": "cache",
                "config": {
                    "redis_url": None,
                    "default_ttl": None
                },
                "expected_errors": ["redis_url cannot be null", "default_ttl cannot be null"],
                "description": "Configuration with null values"
            },
            {
                "name": "wrong_data_types",
                "config_type": "resilience",
                "config": {
                    "retry_attempts": "three",
                    "circuit_breaker_threshold": "five",
                    "timeout_seconds": "thirty"
                },
                "expected_errors": [
                    "retry_attempts must be an integer",
                    "circuit_breaker_threshold must be an integer",
                    "timeout_seconds must be a number"
                ],
                "description": "Configuration with wrong data types"
            },
            {
                "name": "extreme_values",
                "config_type": "resilience",
                "config": {
                    "retry_attempts": 999999,
                    "circuit_breaker_threshold": 999999,
                    "timeout_seconds": 999999.999
                },
                "expected_warnings": [
                    "Extremely high retry attempts",
                    "Extremely high circuit breaker threshold",
                    "Extremely long timeout"
                ],
                "description": "Configuration with extreme values"
            }
        ]
    }


@pytest.fixture
def mock_json_schema_validator():
    """
    Mock JSON schema validator for configuration validation testing.

    Provides a mock JSON schema validator that simulates schema validation
    behavior without requiring actual JSON schema library integration. This
    enables testing of schema-based configuration validation logic.

    Mock Components:
        - Mock schema validation engine
        - Mock schema compilation and caching
        - Mock validation error generation
        - Mock schema loading and parsing

    Use Cases:
        - Testing JSON schema validation logic
        - Testing schema compilation and caching
        - Testing validation error generation and formatting
        - Testing schema-based configuration type checking

    Example:
        def test_schema_validation(mock_json_schema_validator):
            # Configure mock schema validation
            mock_json_schema_validator.validate.return_value = ValidationResult(
                status=ValidationStatus.VALID,
                config_type=ConfigType.RESILIENCE,
                errors=[],
                warnings=[],
                metadata={},
                timestamp=1234567890.0
            )

            # Test schema validation
            result = validator.validate_with_schema(config_data, schema_definition)

            # Validate schema validation was called
            mock_json_schema_validator.validate.assert_called_once_with(config_data, schema_definition)
    """
    mock_validator = MagicMock()
    mock_validator.validate = Mock(return_value=ValidationResult(
        status=ValidationStatus.VALID,
        config_type=ConfigType.RESILIENCE,
        errors=[],
        warnings=[],
        metadata={},
        timestamp=1234567890.0
    ))

    mock_validator.compile_schema = Mock(return_value={"compiled": True})
    mock_validator.load_schema = Mock(return_value={"type": "object", "properties": {}})
    mock_validator.get_schema_errors = Mock(return_value=[])
    mock_validator.is_valid_type = Mock(return_value=True)

    return {
        "validator": mock_validator,
        "compile_schema": mock_validator.compile_schema,
        "load_schema": mock_validator.load_schema,
        "get_schema_errors": mock_validator.get_schema_errors,
        "is_valid_type": mock_validator.is_valid_type
    }
