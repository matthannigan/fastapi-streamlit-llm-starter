"""
Factory module test fixtures providing mocks and fakes for external dependencies.

This module provides test doubles for external dependencies of the LLM security factory
module, following the "Prefer Fakes, Mock at Boundaries" philosophy. The factory
module has cross-module dependencies that require careful mocking for isolated testing.

SHARED MOCKS: MockConfigurationError, MockInfrastructureError, MockSecurityConfig are imported from parent conftest.py
"""

from typing import Dict, Any, Optional, Union
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from pathlib import Path

# Import shared mocks from parent conftest - these are used across multiple modules
# MockConfigurationError, MockInfrastructureError, MockSecurityConfig, and their fixtures
# are now defined in backend/tests/unit/llm_security/conftest.py

# Import exceptions that the factory depends on
# Note: These would normally be imported from the actual implementation
# from app.core.exceptions import ConfigurationError, InfrastructureError


# NOTE: MockConfigurationError, MockInfrastructureError removed
# These are now shared fixtures in parent conftest.py


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


# NOTE: MockSecurityConfig removed - now shared fixture in parent conftest.py
# The factory module uses the shared MockSecurityConfig which has most of the same methods


class MockSecurityServiceFactory:
    """Mock SecurityServiceFactory for testing factory patterns.
    
    Uses shared MockSecurityConfig from parent conftest.py.
    """

    def __init__(self, mock_security_config_factory=None):
        self._service_cache = {}
        self._creation_calls = []
        self._clear_cache_calls = []
        # Store the factory for creating MockSecurityConfig instances
        self._config_factory = mock_security_config_factory

    def create_service(self,
                      mode: str = 'local',
                      config=None,
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
            # Use factory if available, otherwise import at runtime
            if self._config_factory:
                config = self._config_factory(
                    scanners={"prompt_injection": {"enabled": True, "threshold": 0.7}},
                    performance={"max_concurrent_scans": 15},
                    logging={"log_level": "INFO"},
                    service_name="balanced-security-service",
                    preset="balanced",
                    environment="development",
                    debug_mode=True
                )
            else:
                from ..conftest import MockSecurityConfig
                config = MockSecurityConfig(
                    scanners={"prompt_injection": {"enabled": True, "threshold": 0.7}},
                    performance={"max_concurrent_scans": 15},
                    logging={"log_level": "INFO"},
                    service_name="balanced-security-service",
                    preset="balanced",
                    environment="development",
                    debug_mode=True
                )

        # Apply environment overrides if provided (simplified)
        if environment_overrides:
            # For simplicity, just update service_name
            if hasattr(config, 'service_name'):
                config.service_name = environment_overrides.get("SECURITY_SERVICE_NAME", config.service_name)

        # Create service based on mode
        config_dict = config.to_dict() if hasattr(config, 'to_dict') else {
            "scanners": getattr(config, 'scanners', {}),
            "performance": getattr(config, 'performance', {}),
            "service_name": getattr(config, 'service_name', 'default-service')
        }
        
        service = MockSecurityService(
            service_name=f"{mode}-security-service",
            config=config_dict
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


# NOTE: mock_configuration_error, mock_infrastructure_error, mock_security_config fixtures removed
# These are now shared fixtures in parent conftest.py


@pytest.fixture
def mock_security_service():
    """Factory fixture to create MockSecurityService instances for testing."""
    def _create_service(service_name: str = "test-security-service",
                       config: Optional[Dict] = None) -> MockSecurityService:
        return MockSecurityService(service_name=service_name, config=config)
    return _create_service


@pytest.fixture
def mock_security_service_factory(mock_security_config):
    """Factory fixture to create MockSecurityServiceFactory instances for testing.
    
    Injects shared mock_security_config fixture from parent conftest.
    """
    def _create_factory() -> MockSecurityServiceFactory:
        return MockSecurityServiceFactory(mock_security_config_factory=mock_security_config)
    return _create_factory


@pytest.fixture
def minimal_security_config():
    """Minimal SecurityConfig for basic factory testing with proper ScannerType enum keys."""
    from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ScannerConfig

    return SecurityConfig(
        service_name="minimal-test-service",
        environment="testing",
        debug_mode=True,
        scanners={
            ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True, threshold=0.7)
        }
    )


@pytest.fixture
def strict_security_config():
    """Strict SecurityConfig for security-critical factory testing with proper ScannerType enum keys."""
    from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ScannerConfig, PresetName

    return SecurityConfig(
        service_name="strict-security-service",
        preset=PresetName.STRICT,
        environment="production",
        debug_mode=False,
        scanners={
            ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True, threshold=0.3)
        }
    )


@pytest.fixture
def development_security_config():
    """Development SecurityConfig for development environment factory testing with proper ScannerType enum keys."""
    from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ScannerConfig, PresetName

    return SecurityConfig(
        service_name="development-security-service",
        preset=PresetName.DEVELOPMENT,
        environment="development",
        debug_mode=True,
        scanners={
            ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True, threshold=0.8)
        }
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
    # Import at runtime to avoid circular imports
    from ..conftest import MockConfigurationError
    
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
def cached_service_scenario(mock_security_service_factory):
    """
    Pre-configured factory with cached services for testing cache behavior.

    Sets up a factory with multiple cached services to test cache statistics,
    cache clearing, and cache key management functionality.

    Uses SecurityConfig with proper ScannerType enum keys.
    """
    from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ScannerConfig

    factory = mock_security_service_factory()

    # Create configs with proper ScannerType enum keys
    config1 = SecurityConfig(
        service_name="cached-service-1",
        environment="testing",
        scanners={ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)}
    )

    config2 = SecurityConfig(
        service_name="cached-service-2",
        environment="testing",
        scanners={ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)}
    )

    config3 = SecurityConfig(
        service_name="cached-service-3",
        environment="testing",
        scanners={ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)}
    )

    # Create and cache multiple services
    service1 = factory.create_service(
        mode="local",
        config=config1,
        cache_key="test_service_1"
    )

    service2 = factory.create_service(
        mode="local",
        config=config2,
        cache_key="test_service_2"
    )

    service3 = factory.create_service(
        mode="saas",
        config=config3,
        cache_key="test_service_3"
    )

    return {
        "factory": factory,
        "services": [service1, service2, service3],
        "cache_keys": ["test_service_1", "test_service_2", "test_service_3"]
    }