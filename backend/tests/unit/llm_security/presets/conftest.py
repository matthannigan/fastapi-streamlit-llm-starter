"""
Presets module test fixtures providing test data for preset configurations.

This module provides test data fixtures for the LLM security presets module.
Since the presets module contains only functions with standard library dependencies,
the fixtures focus on providing representative test data for different preset
configurations and validation scenarios.
"""

from typing import Dict, Any, List
import pytest


@pytest.fixture
def preset_names():
    """Available preset names for testing preset functionality."""
    return ["development", "production", "testing"]


@pytest.fixture
def preset_descriptions():
    """Human-readable descriptions for available presets."""
    return {
        "development": "Development preset with lenient settings for fast iteration",
        "production": "Production preset with strict security settings",
        "testing": "Testing preset with minimal scanners for fast execution"
    }


@pytest.fixture
def development_preset_data():
    """Complete development preset configuration for testing."""
    return {
        "preset": "development",
        "input_scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.9,  # Very lenient
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 15,
                "model_name": "dev-prompt-injection"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.8,
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 20
            },
            "pii_detection": {
                "enabled": True,
                "threshold": 0.9,
                "action": "flag",
                "use_onnx": False,
                "scan_timeout": 25
            }
        },
        "output_scanners": {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.8,
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 20
            },
            "bias_detection": {
                "enabled": True,
                "threshold": 0.9,
                "action": "flag",
                "use_onnx": False,
                "scan_timeout": 30
            }
        },
        "performance": {
            "onnx_providers": ["CPUExecutionProvider"],
            "cache_enabled": True,
            "cache_ttl_seconds": 300,  # 5 minutes for fast iteration
            "max_concurrent_scans": 2,
            "memory_limit_mb": 1024,
            "batch_processing": False
        },
        "logging": {
            "enabled": True,
            "level": "DEBUG",
            "include_scanned_text": True,
            "log_scan_operations": True,
            "log_format": "text",
            "sanitize_pii_in_logs": False
        },
        "service": {
            "environment": "development",
            "debug_mode": True,
            "api_key_required": False,
            "rate_limit_enabled": False
        },
        "features": {
            "experimental_features": True,
            "verbose_output": True,
            "performance_monitoring": True
        }
    }


@pytest.fixture
def production_preset_data():
    """Complete production preset configuration for testing."""
    return {
        "preset": "production",
        "input_scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.6,  # Strict
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30,
                "model_name": "prod-prompt-injection"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 25
            },
            "pii_detection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "redact",
                "use_onnx": True,
                "scan_timeout": 40,
                "redact": True
            },
            "malicious_url": {
                "enabled": True,
                "threshold": 0.5,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 20
            }
        },
        "output_scanners": {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 25
            },
            "bias_detection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "flag",
                "use_onnx": True,
                "scan_timeout": 30
            },
            "harmful_content": {
                "enabled": True,
                "threshold": 0.5,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 35
            }
        },
        "performance": {
            "onnx_providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],
            "cache_enabled": True,
            "cache_ttl_seconds": 7200,  # 2 hours
            "max_concurrent_scans": 20,
            "memory_limit_mb": 4096,
            "batch_processing": True,
            "batch_size": 10
        },
        "logging": {
            "enabled": True,
            "level": "INFO",
            "include_scanned_text": False,  # Privacy
            "log_scan_operations": True,
            "log_format": "json",
            "sanitize_pii_in_logs": True
        },
        "service": {
            "environment": "production",
            "debug_mode": False,
            "api_key_required": True,
            "rate_limit_enabled": True,
            "rate_limit_requests_per_minute": 120
        },
        "features": {
            "experimental_features": False,
            "verbose_output": False,
            "performance_monitoring": True,
            "health_checks": True
        }
    }


@pytest.fixture
def testing_preset_data():
    """Complete testing preset configuration for testing."""
    return {
        "preset": "testing",
        "input_scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.95,  # Very lenient to avoid test failures
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 5,
                "model_name": "test-prompt-injection"
            }
        },
        "output_scanners": {},  # No output scanners for speed
        "performance": {
            "onnx_providers": ["CPUExecutionProvider"],
            "cache_enabled": True,
            "cache_ttl_seconds": 1,  # Very short TTL for test isolation
            "max_concurrent_scans": 1,
            "memory_limit_mb": 256,
            "batch_processing": False
        },
        "logging": {
            "enabled": False,  # Disabled for speed
            "level": "ERROR",
            "include_scanned_text": False,
            "log_scan_operations": False,
            "log_format": "text",
            "sanitize_pii_in_logs": False
        },
        "service": {
            "environment": "testing",
            "debug_mode": True,
            "api_key_required": False,
            "rate_limit_enabled": False
        },
        "features": {
            "experimental_features": False,
            "verbose_output": False,
            "performance_monitoring": False
        }
    }


@pytest.fixture
def custom_preset_scanner_configs():
    """Custom scanner configurations for testing custom preset creation."""
    return {
        "content_moderation_input": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.4,  # Very sensitive
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 15,
                "model_name": "moderation-prompt-injection"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.3,  # Extremely sensitive
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 20
            },
            "hate_speech": {
                "enabled": True,
                "threshold": 0.2,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 25
            }
        },
        "content_moderation_output": {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.2,  # Maximum sensitivity
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 25
            },
            "violence": {
                "enabled": True,
                "threshold": 0.1,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }
    }


@pytest.fixture
def custom_preset_performance_overrides():
    """Custom performance overrides for testing custom preset creation."""
    return {
        "content_moderation": {
            "cache_ttl_seconds": 1800,  # 30 minutes
            "max_concurrent_scans": 10,
            "memory_limit_mb": 2048,
            "batch_processing": True,
            "batch_size": 5
        },
        "high_security": {
            "cache_ttl_seconds": 3600,  # 1 hour
            "max_concurrent_scans": 25,
            "memory_limit_mb": 8192,
            "batch_processing": True,
            "batch_size": 15
        },
        "minimal_testing": {
            "cache_ttl_seconds": 1,
            "max_concurrent_scans": 1,
            "memory_limit_mb": 128,
            "batch_processing": False
        }
    }


@pytest.fixture
def custom_preset_logging_overrides():
    """Custom logging overrides for testing custom preset creation."""
    return {
        "content_moderation": {
            "level": "INFO",
            "log_violations": True,
            "sanitize_pii_in_logs": True,
            "log_format": "json"
        },
        "high_security": {
            "level": "WARNING",
            "log_violations": True,
            "sanitize_pii_in_logs": True,
            "log_format": "json",
            "include_scanned_text": False
        },
        "debug_testing": {
            "level": "DEBUG",
            "log_violations": True,
            "sanitize_pii_in_logs": False,
            "log_format": "text",
            "include_scanned_text": True
        }
    }


@pytest.fixture
def invalid_preset_configurations():
    """Various invalid preset configurations for testing validation."""
    return {
        "missing_required_sections": {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn"
                }
            }
            # Missing: output_scanners, performance, logging, service, features
        },
        "invalid_threshold_values": {
            "preset": "invalid",
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 1.5,  # Invalid: > 1.0
                    "action": "warn"
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": -0.1,  # Invalid: < 0.0
                    "action": "block"
                }
            },
            "output_scanners": {},
            "performance": {"max_concurrent_scans": 5},
            "logging": {"enabled": True},
            "service": {"environment": "test"},
            "features": {}
        },
        "invalid_performance_values": {
            "preset": "invalid",
            "input_scanners": {},
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": -1,  # Invalid: negative
                "cache_ttl_seconds": 0,      # Invalid: zero
                "memory_limit_mb": -512      # Invalid: negative
            },
            "logging": {"enabled": True},
            "service": {"environment": "test"},
            "features": {}
        },
        "invalid_scanner_structure": {
            "preset": "invalid",
            "input_scanners": {
                "bad_scanner": {
                    "enabled": True,
                    # Missing required fields: threshold, action
                    "extra_field": "invalid"
                }
            },
            "output_scanners": {},
            "performance": {"max_concurrent_scans": 5},
            "logging": {"enabled": True},
            "service": {"environment": "test"},
            "features": {}
        },
        "wrong_data_types": {
            "preset": 123,  # Should be string
            "input_scanners": "not_a_dict",  # Should be dict
            "output_scanners": {},
            "performance": {"max_concurrent_scans": "not_a_number"},  # Should be int
            "logging": {"enabled": "not_boolean"},  # Should be bool
            "service": {"environment": ["not", "a", "string"]},  # Should be string
            "features": "not_a_dict"  # Should be dict
        }
    }


@pytest.fixture
def preset_validation_issues():
    """Expected validation issues for invalid preset configurations."""
    return {
        "missing_sections": [
            "Missing required section: output_scanners",
            "Missing required section: performance",
            "Missing required section: logging",
            "Missing required section: service",
            "Missing required section: features"
        ],
        "invalid_thresholds": [
            "Invalid threshold value 1.5 for scanner prompt_injection: must be between 0.0 and 1.0",
            "Invalid threshold value -0.1 for scanner toxicity_input: must be between 0.0 and 1.0"
        ],
        "invalid_performance": [
            "Invalid max_concurrent_scans value -1: must be positive integer",
            "Invalid cache_ttl_seconds value 0: must be positive integer",
            "Invalid memory_limit_mb value -512: must be positive integer"
        ],
        "invalid_scanner_structure": [
            "Scanner bad_scanner missing required field: threshold",
            "Scanner bad_scanner missing required field: action"
        ],
        "wrong_types": [
            "Invalid data type for preset: expected str, got int",
            "Invalid data type for input_scanners: expected dict, got str",
            "Invalid data type for max_concurrent_scans: expected int, got str",
            "Invalid data type for enabled: expected bool, got str",
            "Invalid data type for environment: expected str, got list"
        ]
    }


@pytest.fixture
def custom_preset_examples():
    """Complete examples of custom presets for testing custom preset creation."""
    return {
        "content_moderation": {
            "name": "content-moderation",
            "description": "High-sensitivity content moderation for social platforms",
            "expected_features": ["strict_toxicity_detection", "hate_speech_blocking"]
        },
        "educational_platform": {
            "name": "educational-platform",
            "description": "Balanced security for educational content with focus on safety",
            "expected_features": ["educational_content_compatibility", "student_safety"]
        },
        "enterprise_internal": {
            "name": "enterprise-internal",
            "description": "Security optimized for internal enterprise communications",
            "expected_features": ["pii_protection", "data_leak_prevention"]
        },
        "minimal_api": {
            "name": "minimal-api",
            "description": "Lightweight security for API endpoints with performance focus",
            "expected_features": ["low_latency", "high_throughput"]
        }
    }