"""
Config loader module test fixtures providing mocks for file system and YAML loading.

This module provides test doubles for external dependencies of the LLM security config
loader module, focusing on file system operations, YAML parsing, and environment
variable handling for configuration loading scenarios.
"""

from typing import Dict, Any, Optional, Union
import pytest
from unittest.mock import Mock, MagicMock, mock_open
from pathlib import Path

# Import classes that would normally be from the actual implementation
# from app.infrastructure.security.llm.config_loader import (
#     ConfigurationError, SecurityConfigLoader
# )


class MockConfigurationError(Exception):
    """Mock ConfigurationError for testing config loader error handling."""

    def __init__(self, message: str, suggestion: Optional[str] = None, file_path: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        self.file_path = file_path
        super().__init__(message)


class MockSecurityConfig:
    """Mock SecurityConfig for testing config loader functionality."""

    def __init__(self, **kwargs):
        self.scanners = kwargs.get("scanners", {})
        self.performance = kwargs.get("performance", {})
        self.logging = kwargs.get("logging", {})
        self.service_name = kwargs.get("service_name", "test-service")
        self.environment = kwargs.get("environment", "testing")
        self.version = kwargs.get("version", "1.0.0")
        self.preset = kwargs.get("preset")
        self.debug_mode = kwargs.get("debug_mode", False)
        self.custom_settings = kwargs.get("custom_settings", {})


class MockSecurityConfigLoader:
    """Mock SecurityConfigLoader for testing configuration loading patterns."""

    def __init__(self,
                 config_path: Optional[str] = None,
                 environment: Optional[str] = None,
                 cache_enabled: bool = True,
                 cache_ttl: int = 300,
                 debug_mode: Optional[bool] = None):
        self.config_path = config_path or "config/security"
        self.environment = environment or "testing"
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.debug_mode = debug_mode or False
        self._cache = {}
        self._load_calls = []
        self._cache_clear_calls = []

    def load_config(self,
                    environment: Optional[str] = None,
                    enable_hot_reload: bool = False,
                    cache_bust: bool = False) -> MockSecurityConfig:
        """Mock configuration loading with caching and environment support."""

        load_call = {
            "environment": environment,
            "enable_hot_reload": enable_hot_reload,
            "cache_bust": cache_bust,
            "timestamp": "mock-timestamp"
        }
        self._load_calls.append(load_call)

        env = environment or self.environment

        # Check cache unless cache_bust is True
        cache_key = f"{self.config_path}:{env}"
        if not cache_bust and self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        # Create mock config
        config = MockSecurityConfig(
            service_name=f"{env}-security-service",
            environment=env,
            debug_mode=self.debug_mode,
            scanners={"prompt_injection": {"enabled": True, "threshold": 0.7}},
            performance={"max_concurrent_scans": 10},
            logging={"log_level": "DEBUG" if env == "development" else "INFO"}
        )

        # Cache if enabled
        if self.cache_enabled:
            self._cache[cache_key] = config

        return config

    def clear_cache(self) -> None:
        """Mock cache clearing."""
        self._cache_clear_calls.append({"timestamp": "mock-timestamp"})
        self._cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Mock cache information."""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cached_entries": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }

    def reset_history(self):
        """Reset call history for test isolation."""
        self._load_calls.clear()
        self._cache_clear_calls.clear()

    @property
    def load_history(self) -> list:
        """Get history of load calls for test verification."""
        return self._load_calls.copy()

    @property
    def cache_clear_history(self) -> list:
        """Get history of cache clear calls for test verification."""
        return self._cache_clear_calls.copy()


@pytest.fixture
def mock_configuration_error():
    """Mock ConfigurationError exception for testing config loader error handling."""
    return MockConfigurationError


@pytest.fixture
def mock_security_config():
    """Factory fixture to create MockSecurityConfig instances for testing."""
    def _create_config(**kwargs) -> MockSecurityConfig:
        return MockSecurityConfig(**kwargs)
    return _create_config


@pytest.fixture
def mock_security_config_loader():
    """Factory fixture to create MockSecurityConfigLoader instances for testing."""
    def _create_loader(**kwargs) -> MockSecurityConfigLoader:
        return MockSecurityConfigLoader(**kwargs)
    return _create_loader


@pytest.fixture
def yaml_config_data():
    """Mock YAML configuration data for testing file-based configuration loading."""
    return {
        "scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "warn",
                "model_name": "test-prompt-injection-model"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block"
            },
            "pii_detection": {
                "enabled": False,
                "threshold": 0.8,
                "action": "redact"
            }
        },
        "performance": {
            "enable_model_caching": True,
            "enable_result_caching": True,
            "cache_ttl_seconds": 1800,
            "max_concurrent_scans": 15,
            "max_memory_mb": 2048
        },
        "logging": {
            "enable_scan_logging": True,
            "enable_violation_logging": True,
            "log_level": "INFO",
            "log_format": "json",
            "include_scanned_text": False,
            "sanitize_pii_in_logs": True
        },
        "service": {
            "name": "test-security-service",
            "environment": "testing",
            "version": "1.0.0"
        }
    }


@pytest.fixture
def yaml_environment_overrides():
    """Mock environment-specific YAML override data."""
    return {
        "development": {
            "scanners": {
                "prompt_injection": {"threshold": 0.8},  # More lenient for dev
                "toxicity_input": {"action": "warn"}     # Less strict for dev
            },
            "performance": {
                "max_concurrent_scans": 2,               # Lower for dev
                "enable_caching": False                   # Disable cache for dev
            },
            "logging": {
                "log_level": "DEBUG",
                "include_scanned_text": True              # Include content for debugging
            },
            "service": {
                "debug_mode": True
            }
        },
        "production": {
            "scanners": {
                "prompt_injection": {"threshold": 0.4},  # More strict for prod
                "pii_detection": {"enabled": True}        # Enable PII detection for prod
            },
            "performance": {
                "max_concurrent_scans": 25,              # Higher for prod
                "cache_ttl_seconds": 3600                # Longer cache for prod
            },
            "logging": {
                "log_level": "INFO",
                "include_scanned_text": False,            # Privacy-first for prod
                "sanitize_pii_in_logs": True
            },
            "service": {
                "debug_mode": False
            }
        },
        "testing": {
            "scanners": {
                "prompt_injection": {"enabled": True, "threshold": 0.9},  # Very lenient for testing
                "toxicity_input": {"enabled": False}                     # Disable for testing
            },
            "performance": {
                "max_concurrent_scans": 1,
                "enable_caching": False
            },
            "logging": {
                "log_level": "DEBUG"
            },
            "service": {
                "debug_mode": True
            }
        }
    }


@pytest.fixture
def config_loader_test_environment(tmp_path):
    """
    Temporary directory structure for testing config loader file operations.

    Creates a realistic configuration directory structure with YAML files
    for testing the config loader's file loading and merging capabilities.
    """
    config_dir = tmp_path / "config" / "security"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create base scanners.yaml
    base_config = {
        "scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "warn"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block"
            }
        },
        "performance": {
            "max_concurrent_scans": 10,
            "enable_caching": True
        },
        "logging": {
            "level": "INFO",
            "include_scanned_text": False
        },
        "service": {
            "name": "base-security-service",
            "environment": "base"
        }
    }

    import yaml
    base_file = config_dir / "scanners.yaml"
    base_file.write_text(yaml.dump(base_config, default_flow_style=False))

    # Create environment override files
    env_overrides = {
        "development.yaml": {
            "scanners": {
                "prompt_injection": {"threshold": 0.8},
                "toxicity_input": {"action": "warn"}
            },
            "performance": {"max_concurrent_scans": 2},
            "logging": {"level": "DEBUG"},
            "service": {"debug_mode": True}
        },
        "production.yaml": {
            "scanners": {
                "prompt_injection": {"threshold": 0.4},
                "pii_detection": {"enabled": True, "threshold": 0.8}
            },
            "performance": {"max_concurrent_scans": 20},
            "logging": {"level": "INFO"},
            "service": {"debug_mode": False}
        },
        "testing.yaml": {
            "scanners": {
                "prompt_injection": {"threshold": 0.9},
                "toxicity_input": {"enabled": False}
            },
            "performance": {"max_concurrent_scans": 1},
            "logging": {"level": "DEBUG"}
        }
    }

    for filename, config in env_overrides.items():
        file_path = config_dir / filename
        file_path.write_text(yaml.dump(config, default_flow_style=False))

    # Create invalid configuration files for error testing
    invalid_yaml = config_dir / "invalid.yaml"
    invalid_yaml.write_text("invalid: yaml: content: [")

    missing_dir = config_dir.parent / "nonexistent"
    # Don't create this directory - it should not exist for testing

    return {
        "config_dir": str(config_dir),
        "base_config_path": str(base_file),
        "dev_config_path": str(config_dir / "development.yaml"),
        "prod_config_path": str(config_dir / "production.yaml"),
        "test_config_path": str(config_dir / "testing.yaml"),
        "invalid_config_path": str(invalid_yaml),
        "nonexistent_dir": str(missing_dir)
    }


@pytest.fixture
def mocked_yaml_functions():
    """Mock YAML functions for testing config loader YAML parsing."""
    mock_yaml = Mock()

    def mock_safe_load(file_content):
        """Mock YAML safe_load with different behaviors based on content."""
        content = file_content.read() if hasattr(file_content, 'read') else file_content

        if "invalid" in content and "[" in content:
            raise ValueError("Invalid YAML syntax")

        # Return different configurations based on content
        if "development" in content:
            return {"scanners": {"prompt_injection": {"threshold": 0.8}}}
        elif "production" in content:
            return {"scanners": {"prompt_injection": {"threshold": 0.4}}}
        else:
            return {"scanners": {"prompt_injection": {"threshold": 0.7}}}

    def mock_dump(data, stream=None, **kwargs):
        """Mock YAML dump function."""
        if stream:
            if hasattr(stream, 'write'):
                stream.write("# Mock YAML output")
            return stream
        return "# Mock YAML output"

    mock_yaml.safe_load = mock_safe_load
    mock_yaml.dump = mock_dump
    return mock_yaml


@pytest.fixture
def environment_variable_overrides():
    """Environment variable overrides for testing config loader environment variable handling."""
    return {
        "SECURITY_ENVIRONMENT": "staging",
        "SECURITY_CONFIG_PATH": "/custom/security/config",
        "SECURITY_DEBUG": "true",
        "SECURITY_CACHE_ENABLED": "false",
        "SECURITY_PRESET": "strict",
        "SECURITY_MAX_CONCURRENT_SCANS": "25",
        "SECURITY_LOG_LEVEL": "WARNING"
    }


@pytest.fixture
def config_loader_error_scenarios():
    """Various error scenarios for testing config loader error handling."""
    return {
        "missing_directory": {
            "config_path": "/nonexistent/path/config/security",
            "expected_error": "Configuration directory does not exist"
        },
        "missing_base_config": {
            "config_path": "/tmp/empty_config",
            "expected_error": "Required scanners.yaml file missing"
        },
        "invalid_yaml_syntax": {
            "config_content": "invalid: yaml: content: [",
            "expected_error": "Invalid YAML syntax"
        },
        "missing_required_fields": {
            "config_content": {"logging": {"level": "INFO"}},  # Missing scanners
            "expected_error": "Missing required field: scanners"
        },
        "invalid_values": {
            "config_content": {
                "scanners": {"prompt_injection": {"threshold": 1.5}}  # Invalid threshold
            },
            "expected_error": "Invalid threshold value"
        }
    }


@pytest.fixture
def cached_config_loader_scenario(mock_security_config_loader):
    """
    Pre-configured loader with cached configurations for testing cache behavior.

    Sets up a loader with cached configurations to test cache statistics,
    cache clearing, and cache invalidation functionality.
    """
    loader = mock_security_config_loader(cache_enabled=True, cache_ttl=300)

    # Load and cache configurations for different environments
    dev_config = loader.load_config(environment="development")
    prod_config = loader.load_config(environment="production")
    test_config = loader.load_config(environment="testing")

    return {
        "loader": loader,
        "configs": {
            "development": dev_config,
            "production": prod_config,
            "testing": test_config
        },
        "cache_keys": [
            "config/security:development",
            "config/security:production",
            "config/security:testing"
        ]
    }


@pytest.fixture
def hot_reload_scenario():
    """
    Hot reload configuration for testing development environment hot reload functionality.
    """
    return {
        "environment": "development",
        "enable_hot_reload": True,
        "expected_behavior": "Hot reload monitoring enabled",
        "file_changes": [
            "config/security/scanners.yaml",
            "config/security/development.yaml"
        ]
    }