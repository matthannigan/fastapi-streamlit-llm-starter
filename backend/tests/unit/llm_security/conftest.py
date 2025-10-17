"""
LLM security infrastructure test fixtures providing dependencies for llm security module testing.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the security component from systems outside its boundary.

This module contains SHARED fixtures and mock classes used across multiple LLM security
test modules. Module-specific fixtures remain in their respective conftest.py files.
"""

from typing import Dict, Any, Optional, List
import pytest
from datetime import datetime, UTC

# Import real SecurityConfig for test fixtures
from app.infrastructure.security.llm.config import SecurityConfig


# ============================================================================
# SHARED EXCEPTION MOCKS
# ============================================================================


class MockConfigurationError(Exception):
    """Mock ConfigurationError for testing configuration-related error handling."""

    def __init__(self, message: str, suggestion: Optional[str] = None, file_path: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        self.file_path = file_path
        super().__init__(message)

    def __str__(self) -> str:
        """Format error message with file context and suggestions."""
        parts = [self.message]

        if self.file_path:
            parts.append(f"File: {self.file_path}")

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        return " | ".join(parts) if len(parts) > 1 else self.message


class MockInfrastructureError(Exception):
    """Mock InfrastructureError for testing infrastructure-related error handling."""

    def __init__(self, message: str, context: Optional[Dict] = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)


# ============================================================================
# SHARED ENUM MOCKS
# ============================================================================


class MockScannerType:
    """Mock ScannerType enum for testing scanner type definitions."""
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
    """Mock ViolationAction enum for testing violation action types."""
    NONE = "none"
    WARN = "warn"
    BLOCK = "block"
    REDACT = "redact"
    FLAG = "flag"


class MockPresetName:
    """Mock PresetName enum for testing preset configurations."""
    STRICT = "strict"
    BALANCED = "balanced"
    LENIENT = "lenient"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


# ============================================================================
# SHARED PROTOCOL MOCKS
# ============================================================================


class MockViolation:
    """Mock Violation for testing security violation scenarios.
    
    Shared across cache, scanners, and result processing modules.
    """

    def __init__(self,
                 violation_type: str = "injection",
                 severity: str = "medium",
                 description: str = "Test violation",
                 confidence: float = 0.8,
                 start_index: int = 0,
                 end_index: int = 10,
                 text: str = "test"):
        self.type = violation_type
        self.severity = severity
        self.description = description
        self.confidence = confidence
        self.start_index = start_index
        self.end_index = end_index
        self.text = text
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization testing."""
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "confidence": self.confidence,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "text": self.text,
            "timestamp": self.timestamp.isoformat()
        }


class MockSecurityResult:
    """Mock SecurityResult for testing security scan results.
    
    Shared across cache, scanners, and service modules.
    """

    def __init__(self,
                 is_safe: bool = True,
                 violations: Optional[List] = None,
                 score: float = 1.0,
                 scanned_text: str = "test input",
                 scan_duration_ms: int = 150,
                 scanner_results: Optional[Dict] = None,
                 metadata: Optional[Dict] = None):
        self.is_safe = is_safe
        self.violations = violations or []
        self.score = score
        self.scanned_text = scanned_text
        self.scan_duration_ms = scan_duration_ms
        self.scanner_results = scanner_results or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization testing."""
        return {
            "is_safe": self.is_safe,
            "violations": [v.to_dict() if hasattr(v, 'to_dict') else v for v in self.violations],
            "score": self.score,
            "scanned_text": self.scanned_text,
            "scan_duration_ms": self.scan_duration_ms,
            "scanner_results": self.scanner_results,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class MockScannerConfig:
    """Mock ScannerConfig for testing scanner configuration.
    
    Shared across config, factory, and scanner modules.
    """

    def __init__(self,
                 enabled: bool = True,
                 threshold: float = 0.7,
                 action: str = "warn",
                 model_name: Optional[str] = None,
                 model_params: Optional[Dict] = None,
                 scan_timeout: int = 30,
                 enabled_violation_types: Optional[List[str]] = None,
                 metadata: Optional[Dict] = None):
        self.enabled = enabled
        self.threshold = threshold
        self.action = action
        self.model_name = model_name
        self.model_params = model_params or {}
        self.scan_timeout = scan_timeout
        self.enabled_violation_types = enabled_violation_types or []
        self.metadata = metadata or {}


class MockPerformanceConfig:
    """Mock performance configuration for testing."""

    def __init__(self, max_concurrent_scans: int = 10, max_memory_mb: int = 1024):
        self.max_concurrent_scans = max_concurrent_scans
        self.max_memory_mb = max_memory_mb

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "max_concurrent_scans": self.max_concurrent_scans,
            "max_memory_mb": self.max_memory_mb
        }


class MockSecurityConfig:
    """Mock SecurityConfig for testing security service configuration.

    Shared across cache, config_loader, factory, and scanner modules.
    """

    def __init__(self,
                 scanners: Optional[Dict] = None,
                 performance: Optional[Dict] = None,
                 logging: Optional[Dict] = None,
                 service_name: str = "test-security-service",
                 version: str = "1.0.0",
                 preset: Optional[str] = None,
                 environment: str = "testing",
                 debug_mode: bool = False,
                 custom_settings: Optional[Dict] = None):
        self.scanners = scanners or {}
        if isinstance(performance, MockPerformanceConfig):
            self.performance = performance
        elif isinstance(performance, dict):
            self.performance = MockPerformanceConfig(
                max_concurrent_scans=performance.get("max_concurrent_scans", 10),
                max_memory_mb=performance.get("max_memory_mb", 1024)
            )
        else:
            self.performance = MockPerformanceConfig()
        self.logging = logging or {"enabled": True, "level": "DEBUG"}
        self.service_name = service_name
        self.version = version
        self.preset = preset
        self.environment = environment
        self.debug_mode = debug_mode
        self.custom_settings = custom_settings or {}

    def get_scanner_config(self, scanner_type: str) -> MockScannerConfig:
        """Get scanner configuration by type."""
        config_data = self.scanners.get(scanner_type, {})
        if isinstance(config_data, MockScannerConfig):
            return config_data
        return MockScannerConfig(**config_data) if config_data else MockScannerConfig()

    def get_scanner_config_hash(self) -> str:
        """Mock scanner configuration hash generation."""
        return "mock_scanner_config_hash_1234567890abc"

    def get_scanner_version(self) -> str:
        """Mock scanner version."""
        return "1.0.0-test"

    def get_enabled_scanners(self) -> List[str]:
        """Get list of enabled scanner types."""
        enabled = []
        for scanner_type, config in self.scanners.items():
            if isinstance(config, dict) and config.get("enabled", True):
                enabled.append(scanner_type)
            elif hasattr(config, "enabled") and config.enabled:
                enabled.append(scanner_type)
        # Default to at least one scanner for testing
        return enabled or ["prompt_injection"]

    def merge_with_environment_overrides(self, overrides: Dict[str, Any]) -> 'MockSecurityConfig':
        """Create new config with environment overrides applied."""
        # Create new performance config with overrides
        new_performance = MockPerformanceConfig(
            max_concurrent_scans=overrides.get("max_concurrent_scans", self.performance.max_concurrent_scans),
            max_memory_mb=self.performance.max_memory_mb
        )

        # Create a copy with overrides applied
        new_config = MockSecurityConfig(
            scanners=self.scanners.copy(),
            performance=new_performance,
            logging=self.logging.copy(),
            service_name=overrides.get("SECURITY_SERVICE_NAME", self.service_name),
            version=self.version,
            preset=self.preset,
            environment=self.environment,
            debug_mode=overrides.get("SECURITY_DEBUG", self.debug_mode),
            custom_settings=self.custom_settings.copy()
        )

        # Apply logging overrides
        if "log_level" in overrides:
            new_config.logging["level"] = overrides["log_level"]

        return new_config

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization testing."""
        return {
            "scanners": self.scanners,
            "performance": self.performance.dict() if hasattr(self.performance, 'dict') else self.performance,
            "logging": self.logging,
            "service_name": self.service_name,
            "version": self.version,
            "preset": self.preset,
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "custom_settings": self.custom_settings
        }


# ============================================================================
# SHARED ASYNC CACHE MOCKS
# ============================================================================


class MockCacheInterface:
    """Mock cache interface with async support for testing cache operations."""
    
    def __init__(self, available: bool = True):
        self.storage = {}
        self.operation_history = []
        self.available = available
    
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Mock async set operation matching CacheInterface signature."""
        if not self.available:
            raise Exception("Cache unavailable")
        self.storage[key] = value
        self.operation_history.append({
            "operation": "set",
            "key": key,
            "value": value,
            "ttl": ttl
        })
    
    async def get(self, key: str) -> Any | None:
        """Mock async get operation matching CacheInterface signature."""
        if not self.available:
            raise Exception("Cache unavailable")
        self.operation_history.append({
            "operation": "get",
            "key": key
        })
        return self.storage.get(key)
    
    async def delete(self, key: str) -> None:
        """Mock async delete operation matching CacheInterface signature."""
        if not self.available:
            raise Exception("Cache unavailable")
        self.operation_history.append({
            "operation": "delete",
            "key": key
        })
        if key in self.storage:
            del self.storage[key]
    
    def reset_history(self):
        """Reset operation history for testing."""
        self.operation_history = []


class MockCacheFactory:
    """Mock cache factory with async support for testing cache initialization."""
    
    def __init__(self, redis_available: bool = True):
        self.created_caches = []
        self.redis_available = redis_available
    
    async def for_ai_app(self, redis_url: str, default_ttl: int):
        """Mock async factory method that returns a working Redis cache mock."""
        mock_cache = MockCacheInterface(available=self.redis_available)
        self.created_caches.append(mock_cache)
        return mock_cache
    
    def create_redis_cache(self, redis_url: str):
        """Synchronous method for creating a mock Redis cache (for legacy tests)."""
        mock_cache = MockCacheInterface(available=self.redis_available)
        self.created_caches.append(mock_cache)
        return mock_cache


# ============================================================================
# SHARED PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_configuration_error():
    """Mock ConfigurationError exception for testing configuration error handling."""
    return MockConfigurationError


@pytest.fixture
def mock_infrastructure_error():
    """Mock InfrastructureError exception for testing infrastructure error handling."""
    return MockInfrastructureError


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
def mock_violation():
    """Factory fixture to create MockViolation instances for testing."""
    def _create_violation(**kwargs) -> MockViolation:
        return MockViolation(**kwargs)
    return _create_violation


@pytest.fixture
def mock_security_result():
    """Factory fixture to create MockSecurityResult instances for testing."""
    def _create_result(**kwargs) -> MockSecurityResult:
        return MockSecurityResult(**kwargs)
    return _create_result


@pytest.fixture
def mock_scanner_config():
    """Factory fixture to create MockScannerConfig instances for testing."""
    def _create_config(**kwargs) -> MockScannerConfig:
        return MockScannerConfig(**kwargs)
    return _create_config


@pytest.fixture
def mock_security_config():
    """Factory fixture to create SecurityConfig instances for testing.

    Provides valid default scanner configuration to ensure configs pass factory validation.
    Tests can override scanners parameter to test specific scenarios.
    """
    def _create_config(**kwargs) -> SecurityConfig:
        # Import the real SecurityConfig and related types
        from app.infrastructure.security.llm.config import (
            SecurityConfig,
            ScannerType,
            ScannerConfig,
        )

        # Default configuration with at least one scanner to pass factory validation
        default_kwargs = {
            "service_name": "test-security-service",
            "environment": "testing",
            "debug_mode": False,
            "scanners": {
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True,
                    threshold=0.7
                )
            }
        }

        # Override with provided kwargs
        default_kwargs.update(kwargs)

        return SecurityConfig(**default_kwargs)
    return _create_config


@pytest.fixture
def invalid_security_config_no_scanners():
    """Invalid SecurityConfig with no scanners for testing validation errors.

    This fixture creates a SecurityConfig that intentionally violates the
    "at least one scanner must be enabled" requirement for testing factory
    validation error handling.
    """
    from app.infrastructure.security.llm.config import SecurityConfig

    return SecurityConfig(
        service_name="invalid-no-scanners",
        environment="testing",
        scanners={}  # Explicitly empty - will fail factory validation
    )


@pytest.fixture
def mock_cache_interface():
    """Factory fixture to create MockCacheInterface instances for testing."""
    def _create_cache(available: bool = True) -> MockCacheInterface:
        return MockCacheInterface(available=available)
    return _create_cache


@pytest.fixture
def mock_cache_factory():
    """Factory fixture to create MockCacheFactory instances for testing."""
    def _create_factory(redis_available: bool = True) -> MockCacheFactory:
        return MockCacheFactory(redis_available=redis_available)
    return _create_factory


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging behavior."""
    from unittest.mock import Mock
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger
