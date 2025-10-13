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
        self.performance = performance or {"max_concurrent_scans": 10}
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization testing."""
        return {
            "scanners": self.scanners,
            "performance": self.performance,
            "logging": self.logging,
            "service_name": self.service_name,
            "version": self.version,
            "preset": self.preset,
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "custom_settings": self.custom_settings
        }


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
    """Factory fixture to create MockSecurityConfig instances for testing."""
    def _create_config(**kwargs) -> MockSecurityConfig:
        return MockSecurityConfig(**kwargs)
    return _create_config
