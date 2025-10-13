"""
Factory module test fixtures providing mocks and fakes for external dependencies.

This module provides test doubles for external dependencies of the LLM security factory
module, following the "Prefer Fakes, Mock at Boundaries" philosophy. The factory
module has cross-module dependencies that require careful mocking for isolated testing.
"""

from typing import Dict, Any, Optional, Union
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from pathlib import Path

# Import exceptions that the factory depends on
# Note: These would normally be imported from the actual implementation
# from app.core.exceptions import ConfigurationError, InfrastructureError


class MockConfigurationError(Exception):
    """Mock ConfigurationError for testing factory error handling."""
    pass


class MockInfrastructureError(Exception):
    """Mock InfrastructureError for testing factory error handling."""
    pass


class MockSecurityService:
    """Mock SecurityService implementing the protocol interface for testing."""

    def __init__(self, service_name: str = "mock-security-service", config: Optional[Dict] = None):
        self.service_name = service_name
        self.config = config or {}
        self._validation_results = []
        self._scan_results = []

    async def validate_input(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Mock input validation returning configurable results."""
        result = {
            "is_safe": True,
            "violations": [],
            "confidence": 0.95,
            "scan_time_ms": 50,
            "service_name": self.service_name
        }
        self._validation_results.append(result)
        return result

    async def validate_output(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Mock output validation returning configurable results."""
        result = {
            "is_safe": True,
            "violations": [],
            "confidence": 0.92,
            "scan_time_ms": 45,
            "service_name": self.service_name
        }
        self._validation_results.append(result)
        return result

    async def scan_text(self, text: str, scanner_types: Optional[list] = None) -> Dict:
        """Mock text scanning returning configurable results."""
        result = {
            "results": {},
            "overall_safe": True,
            "scan_time_ms": 100,
            "service_name": self.service_name
        }
        self._scan_results.append(result)
        return result

    def get_service_info(self) -> Dict:
        """Mock service info returning configuration details."""
        return {
            "name": self.service_name,
            "version": "1.0.0-test",
            "config": self.config,
            "supported_scanners": ["prompt_injection", "toxicity", "pii_detection"]
        }

    def reset_history(self):
        """Reset validation/scan history for test isolation."""
        self._validation_results.clear()
        self._scan_results.clear()

    @property
    def validation_history(self) -> list:
        """Get history of validation calls for test verification."""
        return self._validation_results.copy()

    @property
    def scan_history(self) -> list:
        """Get history of scan calls for test verification."""
        return self._scan_results.copy()


class MockSecurityConfig:
    """Mock SecurityConfig for testing factory configuration loading."""

    def __init__(self,
                 scanners: Optional[Dict] = None,
                 performance: Optional[Dict] = None,
                 logging: Optional[Dict] = None,
                 service_name: str = "mock-security-service",
                 version: str = "1.0.0",
                 preset: Optional[str] = None,
                 environment: str = "testing",
                 debug_mode: bool = False,
                 custom_settings: Optional[Dict] = None):
        self.scanners = scanners or {}
        self.performance = performance or {}
        self.logging = logging or {}
        self.service_name = service_name
        self.version = version
        self.preset = preset
        self.environment = environment
        self.debug_mode = debug_mode
        self.custom_settings = custom_settings or {}
        self._creation_method = None

    def get_scanner_config(self, scanner_type: str):
        """Mock method to get scanner configuration."""
        return self.scanners.get(scanner_type)

    def is_scanner_enabled(self, scanner_type: str) -> bool:
        """Mock method to check if scanner is enabled."""
        config = self.get_scanner_config(scanner_type)
        return config is not None and config.get("enabled", False)

    def get_enabled_scanners(self) -> list:
        """Mock method to list enabled scanners."""
        return [scanner_type for scanner_type in self.scanners.keys()
                if self.is_scanner_enabled(scanner_type)]

    def merge_with_environment_overrides(self, overrides: Dict[str, Any]) -> 'MockSecurityConfig':
        """Mock method to apply environment overrides."""
        new_config = MockSecurityConfig(
            scanners=self.scanners.copy(),
            performance=self.performance.copy(),
            logging=self.logging.copy(),
            service_name=overrides.get("SECURITY_SERVICE_NAME", self.service_name),
            version=self.version,
            preset=self.preset,
            environment=overrides.get("SECURITY_ENVIRONMENT", self.environment),
            debug_mode=overrides.get("SECURITY_DEBUG", "false").lower() == "true",
            custom_settings=self.custom_settings.copy()
        )
        new_config._creation_method = "environment_override"
        return new_config

    def to_dict(self) -> Dict[str, Any]:
        """Mock method to export configuration to dictionary."""
        return {
            "scanners": self.scanners,
            "performance": self.performance,
            "logging": self.logging,
            "service_name": self.service_name,
            "version": self.version,
            "preset": self.preset,
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "custom_settings": self.custom_settings,
            "enabled_scanners": self.get_enabled_scanners()
        }

    @classmethod
    def create_from_preset(cls, preset: str, environment: str = "development") -> 'MockSecurityConfig':
        """Mock factory method to create config from preset."""
        preset_configs = {
            "strict": {
                "scanners": {"prompt_injection": {"enabled": True, "threshold": 0.3}},
                "performance": {"max_concurrent_scans": 10},
                "logging": {"log_level": "INFO"}
            },
            "balanced": {
                "scanners": {"prompt_injection": {"enabled": True, "threshold": 0.7}},
                "performance": {"max_concurrent_scans": 15},
                "logging": {"log_level": "INFO"}
            },
            "development": {
                "scanners": {"prompt_injection": {"enabled": True, "threshold": 0.8}},
                "performance": {"max_concurrent_scans": 2},
                "logging": {"log_level": "DEBUG"}
            },
            "production": {
                "scanners": {"prompt_injection": {"enabled": True, "threshold": 0.5}},
                "performance": {"max_concurrent_scans": 20},
                "logging": {"log_level": "INFO"}
            }
        }

        config_data = preset_configs.get(preset, preset_configs["balanced"])
        config = cls(
            scanners=config_data["scanners"],
            performance=config_data["performance"],
            logging=config_data["logging"],
            service_name=f"{preset}-security-service",
            preset=preset,
            environment=environment,
            debug_mode=(environment == "development")
        )
        config._creation_method = "preset"
        return config

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockSecurityConfig':
        """Mock factory method to create config from dictionary."""
        config = cls(
            scanners=data.get("scanners", {}),
            performance=data.get("performance", {}),
            logging=data.get("logging", {}),
            service_name=data.get("service_name", "dict-service"),
            version=data.get("version", "1.0.0"),
            preset=data.get("preset"),
            environment=data.get("environment", "testing"),
            debug_mode=data.get("debug_mode", False),
            custom_settings=data.get("custom_settings", {})
        )
        config._creation_method = "dict"
        return config


class MockSecurityServiceFactory:
    """Mock SecurityServiceFactory for testing factory patterns."""

    def __init__(self):
        self._service_cache = {}
        self._creation_calls = []
        self._clear_cache_calls = []

    def create_service(self,
                      mode: str = 'local',
                      config: Optional[MockSecurityConfig] = None,
                      environment_overrides: Optional[Dict[str, Any]] = None,
                      cache_key: Optional[str] = None) -> MockSecurityService:
        """Mock service creation with caching and configuration management."""

        # Record creation call for test verification
        creation_call = {
            "mode": mode,
            "config": config,
            "environment_overrides": environment_overrides,
            "cache_key": cache_key,
            "timestamp": "mock-timestamp"
        }
        self._creation_calls.append(creation_call)

        # Generate cache key if not provided
        if cache_key is None:
            cache_key = f"service_{mode}_{hash(str(config))}_{hash(str(environment_overrides))}"

        # Check cache first
        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        # Create new service
        if config is None:
            config = MockSecurityConfig.create_from_preset("balanced")

        # Apply environment overrides if provided
        if environment_overrides:
            config = config.merge_with_environment_overrides(environment_overrides)

        # Create service based on mode
        service = MockSecurityService(
            service_name=f"{mode}-security-service",
            config=config.to_dict()
        )

        # Cache the service
        self._service_cache[cache_key] = service

        return service

    def clear_cache(self) -> None:
        """Mock cache clearing for testing cache management."""
        self._clear_cache_calls.append({"timestamp": "mock-timestamp"})
        self._service_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Mock cache statistics for testing cache monitoring."""
        return {
            "cached_services": len(self._service_cache),
            "cache_keys": list(self._service_cache.keys()),
            "cache_memory_mb": len(self._service_cache) * 10  # Mock memory usage
        }

    def reset_history(self):
        """Reset factory history for test isolation."""
        self._creation_calls.clear()
        self._clear_cache_calls.clear()

    @property
    def creation_history(self) -> list:
        """Get history of service creation calls for test verification."""
        return self._creation_calls.copy()

    @property
    def clear_cache_history(self) -> list:
        """Get history of cache clearing calls for test verification."""
        return self._clear_cache_calls.copy()


@pytest.fixture
def mock_configuration_error():
    """Mock ConfigurationError exception for testing factory error handling."""
    return MockConfigurationError


@pytest.fixture
def mock_infrastructure_error():
    """Mock InfrastructureError exception for testing factory error handling."""
    return MockInfrastructureError


@pytest.fixture
def mock_security_service():
    """Factory fixture to create MockSecurityService instances for testing."""
    def _create_service(service_name: str = "test-security-service",
                       config: Optional[Dict] = None) -> MockSecurityService:
        return MockSecurityService(service_name=service_name, config=config)
    return _create_service


@pytest.fixture
def mock_security_config():
    """Factory fixture to create MockSecurityConfig instances for testing."""
    def _create_config(**kwargs) -> MockSecurityConfig:
        return MockSecurityConfig(**kwargs)
    return _create_config


@pytest.fixture
def mock_security_service_factory():
    """Factory fixture to create MockSecurityServiceFactory instances for testing."""
    def _create_factory() -> MockSecurityServiceFactory:
        return MockSecurityServiceFactory()
    return _create_factory


@pytest.fixture
def minimal_security_config():
    """Minimal SecurityConfig for basic factory testing."""
    return MockSecurityConfig(
        scanners={"prompt_injection": {"enabled": True, "threshold": 0.7}},
        performance={"max_concurrent_scans": 2},
        logging={"log_level": "DEBUG"},
        service_name="minimal-test-service",
        environment="testing",
        debug_mode=True
    )


@pytest.fixture
def strict_security_config():
    """Strict SecurityConfig for security-critical factory testing."""
    return MockSecurityConfig.create_from_preset(
        preset="strict",
        environment="production"
    )


@pytest.fixture
def development_security_config():
    """Development SecurityConfig for development environment factory testing."""
    return MockSecurityConfig.create_from_preset(
        preset="development",
        environment="development"
    )


@pytest.fixture
def environment_overrides():
    """Environment variable overrides for testing factory configuration loading."""
    return {
        "SECURITY_DEBUG": "true",
        "SECURITY_SERVICE_NAME": "overridden-test-service",
        "SECURITY_ENVIRONMENT": "staging",
        "SECURITY_MAX_CONCURRENT_SCANS": "15",
        "SECURITY_LOG_LEVEL": "INFO"
    }


@pytest.fixture
def factory_test_environment(tmp_path):
    """
    Temporary directory structure for testing YAML configuration loading.

    Creates a realistic configuration directory structure with YAML files
    for testing the factory's file-based configuration loading capabilities.
    """
    config_dir = tmp_path / "config" / "security"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create development configuration
    dev_config = {
        "scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.8,
                "action": "warn"
            }
        },
        "performance": {
            "max_concurrent_scans": 2,
            "enable_caching": False
        },
        "logging": {
            "level": "DEBUG",
            "include_scanned_text": True
        },
        "service": {
            "name": "development-security-service",
            "environment": "development"
        }
    }

    dev_file = config_dir / "development.yaml"
    import yaml
    dev_file.write_text(yaml.dump(dev_config, default_flow_style=False))

    # Create production configuration
    prod_config = {
        "scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.4,
                "action": "block"
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block"
            }
        },
        "performance": {
            "max_concurrent_scans": 20,
            "enable_caching": True,
            "cache_ttl_seconds": 1800
        },
        "logging": {
            "level": "INFO",
            "include_scanned_text": False,
            "sanitize_pii": True
        },
        "service": {
            "name": "production-security-service",
            "environment": "production"
        }
    }

    prod_file = config_dir / "production.yaml"
    prod_file.write_text(yaml.dump(prod_config, default_flow_style=False))

    # Create invalid configuration for error testing
    invalid_file = config_dir / "invalid.yaml"
    invalid_file.write_text("invalid: yaml: content: [")

    return {
        "config_dir": str(config_dir),
        "dev_config_path": str(dev_file),
        "prod_config_path": str(prod_file),
        "invalid_config_path": str(invalid_file)
    }


@pytest.fixture
def preset_names():
    """Mock preset names for testing factory preset functionality."""
    return {
        "STRICT": "strict",
        "BALANCED": "balanced",
        "LENIENT": "lenient",
        "DEVELOPMENT": "development",
        "PRODUCTION": "production"
    }


@pytest.fixture
def service_modes():
    """Mock service modes for testing factory mode selection."""
    return {
        "LOCAL": "local",
        "SAAS": "saas"
    }


@pytest.fixture
def invalid_factory_config_data():
    """Invalid configuration data for testing factory validation and error handling."""
    return {
        "scanners": {},  # No scanners enabled - should cause ConfigurationError
        "performance": {
            "max_concurrent_scans": -1  # Invalid negative value
        },
        "logging": {
            "level": "INVALID_LEVEL"  # Invalid log level
        }
    }


@pytest.fixture
def mocked_yaml_loader():
    """Mock YAML loader for testing factory configuration file loading."""
    mock_loader = Mock()

    # Mock successful loading
    def mock_load_config(config_path: str, environment: str) -> Dict[str, Any]:
        if "nonexistent" in config_path:
            raise MockConfigurationError(f"Configuration file not found: {config_path}")

        if "invalid" in config_path:
            raise MockConfigurationError(f"Invalid YAML configuration in: {config_path}")

        # Return mock configuration based on environment
        base_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.7 if environment == "development" else 0.5
                }
            },
            "performance": {
                "max_concurrent_scans": 5 if environment == "development" else 15
            },
            "logging": {
                "level": "DEBUG" if environment == "development" else "INFO"
            },
            "service": {
                "name": f"yaml-{environment}-service",
                "environment": environment
            }
        }
        return base_config

    mock_loader.load_security_config = mock_load_config
    return mock_loader


@pytest.fixture
def cached_service_scenario(mock_security_service_factory, mock_security_config):
    """
    Pre-configured factory with cached services for testing cache behavior.

    Sets up a factory with multiple cached services to test cache statistics,
    cache clearing, and cache key management functionality.
    """
    factory = mock_security_service_factory()

    # Create and cache multiple services
    service1 = factory.create_service(
        mode="local",
        config=mock_security_config(service_name="cached-service-1"),
        cache_key="test_service_1"
    )

    service2 = factory.create_service(
        mode="local",
        config=mock_security_config(service_name="cached-service-2"),
        cache_key="test_service_2"
    )

    service3 = factory.create_service(
        mode="saas",
        config=mock_security_config(service_name="cached-service-3"),
        cache_key="test_service_3"
    )

    return {
        "factory": factory,
        "services": [service1, service2, service3],
        "cache_keys": ["test_service_1", "test_service_2", "test_service_3"]
    }