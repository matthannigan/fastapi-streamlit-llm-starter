"""
Config module test fixtures providing test data for configuration classes.

This module provides realistic test data fixtures for the LLM security configuration
components. Since the config module contains only Pydantic models with enum/stdlib
dependencies, the fixtures focus on providing representative test data rather than
mocking external dependencies.
"""

from typing import Dict, Any
import pytest
from pydantic import BaseModel

# Import the configuration classes from the contract
# Note: These would normally be imported from the actual implementation
# from app.infrastructure.security.llm.config import (
#     ScannerConfig, PerformanceConfig, LoggingConfig, SecurityConfig,
#     ScannerType, ViolationAction, PresetName
# )


class MockScannerType:
    """Mock ScannerType enum for testing."""
    PROMPT_INJECTION = "prompt_injection"
    TOXICITY_INPUT = "toxicity_input"
    PII_DETECTION = "pii_detection"
    MALICIOUS_URL = "malicious_url"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    TOXICITY_OUTPUT = "toxicity_output"
    BIAS_DETECTION = "bias_detection"
    HARMFUL_CONTENT = "harmful_content"
    FACTUALITY_CHECK = "factuality_check"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


class MockViolationAction:
    """Mock ViolationAction enum for testing."""
    NONE = "none"
    WARN = "warn"
    BLOCK = "block"
    REDACT = "redact"
    FLAG = "flag"


class MockPresetName:
    """Mock PresetName enum for testing."""
    STRICT = "strict"
    BALANCED = "balanced"
    LENIENT = "lenient"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


@pytest.fixture
def scanner_type():
    """Mock ScannerType enum providing access to scanner type constants."""
    return MockScannerType()


@pytest.fixture
def violation_action():
    """Mock ViolationAction enum providing access to action constants."""
    return MockViolationAction()


@pytest.fixture
def preset_name():
    """Mock PresetName enum providing access to preset constants."""
    return MockPresetName()


@pytest.fixture
def minimal_scanner_config():
    """
    Minimal ScannerConfig with only required fields for basic testing.

    Provides a simple configuration suitable for testing scanner functionality
    without complex parameter validation or performance considerations.
    """
    return {
        "enabled": True,
        "threshold": 0.7,
        "action": MockViolationAction.WARN,
        "model_name": None,
        "model_params": {},
        "scan_timeout": 30,
        "enabled_violation_types": [],
        "metadata": {}
    }


@pytest.fixture
def strict_scanner_config():
    """
    Strict ScannerConfig with high sensitivity for security-critical testing.

    Provides a configuration suitable for testing security scenarios where
    maximum detection sensitivity is required, such as high-risk environments
    or security validation testing.
    """
    return {
        "enabled": True,
        "threshold": 0.3,  # Lower threshold = more sensitive
        "action": MockViolationAction.BLOCK,
        "model_name": "strict-security-model-v1",
        "model_params": {
            "sensitivity": "high",
            "context_window": 1024,
            "language": "en"
        },
        "scan_timeout": 60,
        "enabled_violation_types": [],  # All violation types enabled
        "metadata": {
            "security_level": "maximum",
            "environment": "production"
        }
    }


@pytest.fixture
def custom_model_scanner_config():
    """
    ScannerConfig with custom model configuration for model testing scenarios.

    Provides a configuration suitable for testing custom model integration,
    parameter validation, and model-specific behavior scenarios.
    """
    return {
        "enabled": True,
        "threshold": 0.5,
        "action": MockViolationAction.REDACT,
        "model_name": "custom-toxicity-model-v2",
        "model_params": {
            "language": "en",
            "context_window": 512,
            "threshold_adjustment": 0.1,
            "specialized_detection": True
        },
        "scan_timeout": 45,
        "enabled_violation_types": ["harassment", "hate_speech", "violence"],
        "metadata": {
            "model_version": "v2.1.0",
            "training_data": "diverse-dataset-2024",
            "specialization": "content_moderation"
        }
    }


@pytest.fixture
def disabled_scanner_config():
    """
    ScannerConfig with scanner disabled for testing disabled behavior.

    Provides a configuration suitable for testing scanner bypass behavior,
    configuration validation, and enabled/disabled state management.
    """
    return {
        "enabled": False,
        "threshold": 0.8,
        "action": MockViolationAction.NONE,
        "model_name": None,
        "model_params": {},
        "scan_timeout": 10,
        "enabled_violation_types": ["critical_only"],
        "metadata": {
            "disabled_reason": "maintenance",
            "disabled_until": "2024-12-31T23:59:59Z"
        }
    }


@pytest.fixture
def development_performance_config():
    """
    PerformanceConfig optimized for development environment testing.

    Provides a configuration suitable for development testing with relaxed
    performance constraints, minimal caching, and debug-friendly settings.
    """
    return {
        "enable_model_caching": False,
        "enable_result_caching": False,
        "cache_ttl_seconds": 60,
        "cache_redis_url": None,
        "max_concurrent_scans": 2,
        "max_memory_mb": 1024,
        "enable_batch_processing": False,
        "batch_size": 1,
        "enable_async_processing": False,
        "queue_size": 10,
        "metrics_collection_interval": 30,
        "health_check_interval": 30
    }


@pytest.fixture
def production_performance_config():
    """
    PerformanceConfig optimized for production environment testing.

    Provides a configuration suitable for production testing with optimized
    caching, higher concurrency limits, and performance monitoring enabled.
    """
    return {
        "enable_model_caching": True,
        "enable_result_caching": True,
        "cache_ttl_seconds": 1800,  # 30 minutes
        "cache_redis_url": "redis://localhost:6379/1",
        "max_concurrent_scans": 20,
        "max_memory_mb": 4096,
        "enable_batch_processing": True,
        "batch_size": 10,
        "enable_async_processing": True,
        "queue_size": 100,
        "metrics_collection_interval": 60,
        "health_check_interval": 10
    }


@pytest.fixture
def memory_constrained_performance_config():
    """
    PerformanceConfig for memory-constrained environment testing.

    Provides a configuration suitable for testing scenarios with limited
    memory resources, featuring minimal caching and reduced concurrency.
    """
    return {
        "enable_model_caching": False,
        "enable_result_caching": True,
        "cache_ttl_seconds": 300,  # 5 minutes
        "cache_redis_url": None,
        "max_concurrent_scans": 3,
        "max_memory_mb": 512,
        "enable_batch_processing": True,
        "batch_size": 5,
        "enable_async_processing": False,
        "queue_size": 20,
        "metrics_collection_interval": 120,
        "health_check_interval": 60
    }


@pytest.fixture
def privacy_first_logging_config():
    """
    LoggingConfig optimized for privacy-sensitive production environments.

    Provides a configuration suitable for testing privacy-focused logging
    with PII sanitization, minimal content logging, and structured output.
    """
    return {
        "enable_scan_logging": True,
        "enable_violation_logging": True,
        "enable_performance_logging": False,
        "log_level": "INFO",
        "log_format": "json",
        "include_scanned_text": False,
        "sanitize_pii_in_logs": True,
        "log_retention_days": 90
    }


@pytest.fixture
def development_logging_config():
    """
    LoggingConfig optimized for development debugging.

    Provides a configuration suitable for development testing with verbose
    logging, detailed content inclusion, and text-based formatting.
    """
    return {
        "enable_scan_logging": True,
        "enable_violation_logging": True,
        "enable_performance_logging": True,
        "log_level": "DEBUG",
        "log_format": "text",
        "include_scanned_text": True,
        "sanitize_pii_in_logs": False,
        "log_retention_days": 7
    }


@pytest.fixture
def minimal_logging_config():
    """
    Minimal LoggingConfig for privacy-sensitive or resource-constrained testing.

    Provides a configuration suitable for testing scenarios with minimal
    logging requirements, focusing only on critical violations.
    """
    return {
        "enable_scan_logging": False,
        "enable_violation_logging": True,
        "enable_performance_logging": False,
        "log_level": "WARNING",
        "log_format": "json",
        "include_scanned_text": False,
        "sanitize_pii_in_logs": True,
        "log_retention_days": 30
    }


@pytest.fixture
def minimal_security_config(scanner_type, minimal_scanner_config, development_performance_config, minimal_logging_config):
    """
    Minimal SecurityConfig with basic configuration for simple testing scenarios.

    Provides a simple security configuration suitable for basic functionality
    testing without complex scanner setups or performance optimizations.
    """
    return {
        "scanners": {
            scanner_type.PROMPT_INJECTION: minimal_scanner_config
        },
        "performance": development_performance_config,
        "logging": minimal_logging_config,
        "service_name": "test-security-service",
        "version": "1.0.0",
        "preset": None,
        "environment": "testing",
        "debug_mode": True,
        "custom_settings": {}
    }


@pytest.fixture
def strict_security_config(scanner_type, strict_scanner_config, production_performance_config, privacy_first_logging_config):
    """
    Strict SecurityConfig with maximum security settings for high-risk testing.

    Provides a comprehensive security configuration suitable for testing
    security-critical scenarios with maximum detection sensitivity and
    comprehensive scanner coverage.
    """
    # Create strict configs for multiple scanner types
    strict_configs = {
        scanner_type.PROMPT_INJECTION: strict_scanner_config,
        scanner_type.TOXICITY_INPUT: {
            **strict_scanner_config,
            "model_name": "strict-toxicity-model",
            "action": MockViolationAction.BLOCK
        },
        scanner_type.PII_DETECTION: {
            **strict_scanner_config,
            "threshold": 0.2,  # Even more sensitive for PII
            "action": MockViolationAction.REDACT
        },
        scanner_type.MALICIOUS_URL: {
            **strict_scanner_config,
            "action": MockViolationAction.BLOCK,
            "scan_timeout": 30
        }
    }

    return {
        "scanners": strict_configs,
        "performance": production_performance_config,
        "logging": privacy_first_logging_config,
        "service_name": "strict-security-service",
        "version": "1.0.0",
        "preset": MockPresetName.STRICT,
        "environment": "production",
        "debug_mode": False,
        "custom_settings": {
            "security_level": "maximum",
            "compliance_mode": "gdpr_strict"
        }
    }


@pytest.fixture
def development_security_config(scanner_type, custom_model_scanner_config, development_performance_config, development_logging_config):
    """
    Development SecurityConfig with debug-friendly settings for development testing.

    Provides a comprehensive security configuration suitable for development
    testing with verbose logging, relaxed security settings, and debug features.
    """
    dev_configs = {
        scanner_type.PROMPT_INJECTION: {
            "enabled": True,
            "threshold": 0.8,  # More lenient for development
            "action": MockViolationAction.WARN,
            "model_name": "dev-prompt-injection-model",
            "model_params": {"debug_mode": True},
            "scan_timeout": 15,
            "enabled_violation_types": [],
            "metadata": {}
        },
        scanner_type.TOXICITY_INPUT: custom_model_scanner_config,
        scanner_type.BIAS_DETECTION: {
            "enabled": True,
            "threshold": 0.6,
            "action": MockViolationAction.FLAG,
            "model_name": "dev-bias-detection-model",
            "model_params": {"detailed_analysis": True},
            "scan_timeout": 25,
            "enabled_violation_types": ["gender_bias", "racial_bias", "age_bias"],
            "metadata": {"debug": True}
        }
    }

    return {
        "scanners": dev_configs,
        "performance": development_performance_config,
        "logging": development_logging_config,
        "service_name": "development-security-service",
        "version": "1.0.0-dev",
        "preset": MockPresetName.DEVELOPMENT,
        "environment": "development",
        "debug_mode": True,
        "custom_settings": {
            "debug_mode": True,
            "verbose_logging": True,
            "test_data_mode": True
        }
    }


@pytest.fixture
def environment_override_data():
    """
    Environment variable override data for testing environment-based configuration.

    Provides realistic environment variable data that would be used to override
    configuration settings via environment variables in deployment scenarios.
    """
    return {
        "SECURITY_DEBUG": "true",
        "SECURITY_SERVICE_NAME": "overridden-security-service",
        "SECURITY_ENVIRONMENT": "staging",
        "SECURITY_MAX_CONCURRENT_SCANS": "15",
        "SECURITY_ENABLE_MODEL_CACHING": "false",
        "SECURITY_ENABLE_RESULT_CACHING": "true",
        "SECURITY_CACHE_TTL_SECONDS": "1200",
        "SECURITY_LOG_LEVEL": "DEBUG",
        "SECURITY_INCLUDE_SCANNED_TEXT": "false",
        "SECURITY_SANITIZE_PII_IN_LOGS": "true",
        "SECURITY_PRESET": "balanced"
    }


@pytest.fixture
def legacy_config_data(scanner_type, violation_action):
    """
    Legacy configuration data for testing backward compatibility.

    Provides configuration data in the legacy format that might be found
    in older configuration files, ensuring backward compatibility testing.
    """
    return {
        "scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "block"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.6,
                "action": "warn"
            }
        },
        "service": {
            "name": "legacy-security-scanner",
            "environment": "production"
        },
        "performance": {
            "enable_caching": True,
            "max_concurrent": 10
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        }
    }


@pytest.fixture
def nested_config_data(scanner_type, violation_action):
    """
    Nested configuration data for testing modern configuration format.

    Provides configuration data in the modern nested format with separate
    input_scanners and output_scanners sections for testing current format.
    """
    return {
        "input_scanners": {
            scanner_type.PROMPT_INJECTION: {
                "enabled": True,
                "threshold": 0.5,
                "action": MockViolationAction.BLOCK,
                "model_name": "nested-prompt-injection-model",
                "scan_timeout": 30
            },
            scanner_type.TOXICITY_INPUT: {
                "enabled": True,
                "threshold": 0.6,
                "action": MockViolationAction.WARN,
                "model_params": {"language": "en"}
            },
            scanner_type.PII_DETECTION: {
                "enabled": True,
                "threshold": 0.3,
                "action": MockViolationAction.REDACT
            }
        },
        "output_scanners": {
            scanner_type.TOXICITY_OUTPUT: {
                "enabled": True,
                "threshold": 0.7,
                "action": MockViolationAction.WARN
            },
            scanner_type.BIAS_DETECTION: {
                "enabled": True,
                "threshold": 0.8,
                "action": MockViolationAction.FLAG
            }
        },
        "service": {
            "environment": "production",
            "name": "nested-security-service"
        },
        "performance": {
            "enable_model_caching": True,
            "enable_result_caching": True,
            "max_concurrent_scans": 15,
            "max_memory_mb": 2048
        },
        "logging": {
            "enable_scan_logging": True,
            "enable_violation_logging": True,
            "log_level": "INFO",
            "log_format": "json",
            "sanitize_pii_in_logs": True
        }
    }


@pytest.fixture
def invalid_config_data():
    """
    Invalid configuration data for testing validation error handling.

    Provides intentionally invalid configuration data for testing
    configuration validation, error handling, and edge cases.
    """
    return {
        "scanners": {
            "invalid_scanner": {
                "enabled": "not_boolean",  # Should be boolean
                "threshold": 1.5,  # Should be 0.0 to 1.0
                "action": "invalid_action",  # Should be valid enum
                "scan_timeout": 0  # Should be at least 1
            }
        },
        "performance": {
            "max_concurrent_scans": 0,  # Should be at least 1
            "max_memory_mb": -1,  # Should be positive
            "cache_ttl_seconds": 3599  # Should be at least 3600 (1 hour)
        },
        "logging": {
            "log_level": "INVALID_LEVEL",  # Should be valid logging level
            "log_retention_days": 400  # Should be max 365
        }
    }