"""
Config validator module test fixtures providing external dependency isolation.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the config validator component from systems outside its boundary.

External Dependencies Handled:
    - threading: Standard library threading module (fake implementation)
    - time: Standard library time module (fake implementation)
    - logging: Standard library logging system (mocked)
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading as real_threading
import time as real_time


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
def fake_threading_module():
    """
    Fake threading module implementation for deterministic thread testing.

    Provides a controllable threading implementation that allows tests to simulate
    thread behavior without creating actual threads. This enables deterministic
    testing of concurrent validation, background processing, and thread-safe
    configuration validation without making tests slow or non-deterministic.

    State Management:
        - Thread creation and management simulation
        - Lock acquisition and release tracking
        - Thread state monitoring without actual thread creation
        - Realistic threading interface compatibility

    Thread Simulation:
        - Threads are created but not actually started
        - Thread states can be manipulated programmatically for testing
        - Lock behavior is simulated with state tracking
        - Thread lifecycle events are captured for assertions

    Public Methods:
        Thread(*args, **kwargs): Create fake thread instance
        Lock(): Create fake lock instance
        current_thread(): Return fake current thread info
        active_count(): Return simulated active thread count
        enumerate(): List all simulated active threads

    Configuration Methods:
        set_thread_state(thread_id, state): Set thread state for testing
        simulate_thread_completion(thread_id): Simulate thread finishing
        set_lock_acquired(lock_id, acquired): Simulate lock state
        advance_thread_progress(thread_id, progress): Simulate thread progress

    Use Cases:
        - Testing concurrent validation without actual threading complexity
        - Testing thread-safe configuration access patterns
        - Testing background validation processing
        - Testing lock contention and resolution behavior
        - Any threading-dependent validation logic testing

    Test Customization:
        def test_concurrent_validation(fake_threading_module):
            # Create fake threads for concurrent validation
            threads = []
            for i in range(3):
                thread = fake_threading_module.Thread(target=validate_config, args=(config,))
                threads.append(thread)

            # Simulate thread execution
            for thread in threads:
                fake_threading_module.set_thread_state(thread.ident, "running")
                fake_threading_module.simulate_thread_completion(thread.ident)

    Example:
        def test_config_validator_thread_safety(fake_threading_module, monkeypatch):
            from app.infrastructure.resilience.config_validator import ConfigValidator

            # Replace threading with our fake
            monkeypatch.setattr('app.infrastructure.resilience.config_validator.threading', fake_threading_module)

            validator = ConfigValidator()

            # Test concurrent validation
            fake_lock = fake_threading_module.Lock()

            # Simulate concurrent access
            fake_threading_module.set_lock_acquired(id(fake_lock), True)

            # Test thread-safe validation
            result = validator.validate_concurrently(config_data)

            # Verify thread safety mechanisms were used
            assert fake_lock.acquire.called or fake_lock.__enter__.called

    Thread States Simulated:
        - "new": Thread created but not started
        - "running": Thread currently executing
        - "finished": Thread completed execution
        - "blocked": Thread waiting for lock or resource

    Lock Behavior:
        - Lock acquisition can be simulated for testing contention
        - Lock release tracking for verification
        - Context manager support (with statement)
        - Recursive lock behavior simulation

    Performance Benefits:
        - No actual thread creation overhead
        - Deterministic test execution regardless of thread scheduling
        - Fast test execution without thread synchronization delays
        - Complete control over thread timing and behavior

    Note:
        This fake enables testing of threading-dependent validation logic
        without the complexity and non-determinism of actual threading.
    """

    class FakeThread:
        def __init__(self, target=None, args=None, kwargs=None, name=None):
            self.target = target
            self.args = args or ()
            self.kwargs = kwargs or {}
            self.name = name or f"FakeThread-{id(self)}"
            self.ident = id(self)
            self._state = "new"
            self._result = None
            self._exception = None

        def start(self):
            """Simulate thread start without actual thread creation."""
            self._state = "running"

        def run(self):
            """Simulate thread execution."""
            if self.target:
                try:
                    self._result = self.target(*self.args, **self.kwargs)
                except Exception as e:
                    self._exception = e
                self._state = "finished"

        def join(self, timeout=None):
            """Simulate thread join without blocking."""
            # Simulate thread completion if not already finished
            if self._state == "running":
                self._state = "finished"

        def is_alive(self):
            """Check if thread is simulated as alive."""
            return self._state == "running"

        def get_state(self):
            """Get current simulated thread state."""
            return self._state

        def get_result(self):
            """Get thread execution result if available."""
            return self._result

        def get_exception(self):
            """Get thread execution exception if available."""
            return self._exception

    class FakeLock:
        def __init__(self):
            self._locked = False
            self._owner = None
            self._acquisition_count = 0

        def acquire(self, blocking=True, timeout=-1):
            """Simulate lock acquisition."""
            if not self._locked or self._owner == real_threading.current_thread():
                self._locked = True
                self._owner = real_threading.current_thread()
                self._acquisition_count += 1
                return True
            return False

        def release(self):
            """Simulate lock release."""
            if self._locked and self._owner == real_threading.current_thread():
                self._acquisition_count -= 1
                if self._acquisition_count == 0:
                    self._locked = False
                    self._owner = None

        def __enter__(self):
            """Context manager entry."""
            self.acquire()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Context manager exit."""
            self.release()

        def locked(self):
            """Check if lock is currently held."""
            return self._locked

        def get_owner(self):
            """Get current lock owner."""
            return self._owner

    class FakeThreadingModule:
        def __init__(self):
            self._threads = {}
            self._locks = {}
            self._current_thread = FakeThread(name="MainThread")
            self._active_count = 1

        def Thread(self, target=None, args=None, kwargs=None, name=None):
            """Create fake thread instance."""
            thread = FakeThread(target, args, kwargs, name)
            self._threads[thread.ident] = thread
            return thread

        def Lock(self):
            """Create fake lock instance."""
            lock = FakeLock()
            self._locks[id(lock)] = lock
            return lock

        def current_thread(self):
            """Return fake current thread."""
            return self._current_thread

        def active_count(self):
            """Return simulated active thread count."""
            active = sum(1 for t in self._threads.values() if t.is_alive())
            return active + 1  # +1 for main thread

        def enumerate(self):
            """List all simulated active threads."""
            active_threads = [t for t in self._threads.values() if t.is_alive()]
            active_threads.append(self._current_thread)
            return active_threads

        def set_thread_state(self, thread_id, state):
            """Set thread state for testing."""
            if thread_id in self._threads:
                self._threads[thread_id]._state = state

        def simulate_thread_completion(self, thread_id):
            """Simulate thread completion."""
            if thread_id in self._threads:
                thread = self._threads[thread_id]
                if thread._state == "running":
                    thread.run()

        def set_lock_acquired(self, lock_id, acquired, owner=None):
            """Set lock acquisition state for testing."""
            if lock_id in self._locks:
                lock = self._locks[lock_id]
                lock._locked = acquired
                lock._owner = owner or real_threading.current_thread()
                if acquired:
                    lock._acquisition_count += 1

        def advance_thread_progress(self, thread_id, progress_ratio=0.5):
            """Simulate thread progress for testing."""
            if thread_id in self._threads:
                thread = self._threads[thread_id]
                # For simulation purposes, we could add progress tracking
                thread._progress = progress_ratio

        def get_thread_by_id(self, thread_id):
            """Get thread instance by ID."""
            return self._threads.get(thread_id)

        def get_lock_by_id(self, lock_id):
            """Get lock instance by ID."""
            return self._locks.get(lock_id)

        # Simulate common threading utilities
        def Event(self):
            """Create fake event object."""
            class FakeEvent:
                def __init__(self):
                    self._is_set = False

                def set(self):
                    self._is_set = True

                def clear(self):
                    self._is_set = False

                def is_set(self):
                    return self._is_set

                def wait(self, timeout=None):
                    return self._is_set

            return FakeEvent()

        def Condition(self, lock=None):
            """Create fake condition object."""
            class FakeCondition:
                def __init__(self, lock=None):
                    self._lock = lock or FakeLock()
                    self._waiters = []

                def acquire(self):
                    return self._lock.acquire()

                def release(self):
                    return self._lock.release()

                def wait(self, timeout=None):
                    self._waiters.append(real_threading.current_thread())
                    return True

                def notify(self):
                    if self._waiters:
                        self._waiters.pop(0)

                def notify_all(self):
                    self._waiters.clear()

                def __enter__(self):
                    self.acquire()
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    self.release()

            return FakeCondition(lock)

    return FakeThreadingModule()


@pytest.fixture
def fake_time_module():
    """
    Fake time module implementation for deterministic timing testing.

    Provides a controllable time implementation that allows tests to control
    time progression without using real time delays. This enables deterministic
    testing of timeout behavior, validation timing, and time-dependent
    configuration validation without making tests slow.

    State Management:
        - Current time starts at a fixed timestamp (1000000000.0 seconds)
        - Time can be advanced programmatically for testing
        - All time operations return consistent, predictable results
        - Maintains realistic time interface compatibility

    Public Methods:
        time(): Returns current fake timestamp
        sleep(seconds): Advances time by specified seconds (no real delay)
        monotonic(): Returns monotonic time from same base
        advance(seconds): Advances time by specified amount
        reset(): Resets time to initial value

    Use Cases:
        - Testing validation timeout behavior
        - Testing configuration reload timing
        - Testing background validation scheduling
        - Testing time-based validation policies
        - Any time-dependent validation logic testing

    Test Customization:
        def test_validation_timeout(fake_time_module):
            # Start validation at known time
            fake_time_module.reset()

            # Simulate validation taking longer than timeout
            fake_time_module.advance(10.0)

            # Test timeout logic
            assert validation_timed_out()

    Example:
        def test_config_validation_timing(fake_time_module, monkeypatch):
            from app.infrastructure.resilience.config_validator import ConfigValidator

            # Replace time module with our fake
            monkeypatch.setattr('app.infrastructure.resilience.config_validator.time', fake_time_module)

            validator = ConfigValidator(validation_timeout=5.0)

            start_time = fake_time_module.time()
            fake_time_module.advance(3.0)  # Validation takes 3 seconds

            result = validator.validate_with_timeout(config_data)

            # Verify timing was measured correctly
            elapsed = fake_time_module.time() - start_time
            assert elapsed == 3.0
            assert result.status != "timeout"

    Default Behavior:
        - Time starts at timestamp 1000000000.0 (approximately 2001-09-09)
        - Time only moves forward (no backwards time travel)
        - sleep() advances time without actual delay
        - monotonic() shares same time base as time() for consistency

    Time Precision:
        - Supports microsecond precision for realistic timing
        - Maintains floating-point time values like real time module
        - Provides consistent behavior across all time functions

    Note:
        This fake enables fast, deterministic testing of time-dependent validation
        logic without making tests slow or flaky due to real timing variations.
    """

    class FakeTimeModule:
        def __init__(self):
            self._current_time = 1000000000.0  # Fixed base timestamp
            self._start_time = self._current_time
            self._monotonic_base = 0.0

        def time(self) -> float:
            """Return current fake time as Unix timestamp."""
            return self._current_time

        def monotonic(self) -> float:
            """Return monotonic time from fixed base."""
            return self._current_time - self._monotonic_base

        def sleep(self, seconds: float) -> None:
            """Advance time without real delay."""
            if seconds >= 0:
                self._current_time += seconds

        def advance(self, seconds: float) -> None:
            """Advance time by specified amount for testing."""
            if seconds >= 0:
                self._current_time += seconds

        def reset(self) -> None:
            """Reset time to initial value."""
            self._current_time = self._start_time

        def set_time(self, timestamp: float) -> None:
            """Set absolute time for specific test scenarios."""
            if timestamp >= self._start_time:
                self._current_time = timestamp

        def get_elapsed_since(self, start_time: float) -> float:
            """Get elapsed time since given timestamp."""
            return max(0.0, self._current_time - start_time)

        # Context manager for timeout testing
        def with_timeout(self, timeout_seconds):
            """Context manager that fails if timeout exceeded."""
            class TimeoutContext:
                def __init__(self, time_module, timeout):
                    self.time_module = time_module
                    self.timeout = timeout
                    self.start_time = None

                def __enter__(self):
                    self.start_time = self.time_module.time()
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    elapsed = self.time_module.time() - self.start_time
                    if elapsed > self.timeout:
                        raise TimeoutError(f"Operation exceeded timeout: {elapsed}s > {self.timeout}s")
                    return False

            return TimeoutContext(self, timeout_seconds)

    fake_time = FakeTimeModule()
    return fake_time


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing config validator logging behavior.

    Provides a spec'd mock logger that simulates logging.Logger
    for testing log message generation without actual I/O. Config validator
    components log validation results, errors, warnings, and operational
    messages for monitoring and debugging.

    Default Behavior:
        - All log methods available (info, warning, error, debug)
        - No actual logging output (mocked)
        - Call tracking for assertions in tests
        - Realistic method signatures matching logging.Logger

    Use Cases:
        - Testing validation result logging
        - Testing configuration error and warning logging
        - Testing validation status change logging
        - Testing operational monitoring and debugging messages

    Test Customization:
        def test_validation_logging(mock_logger):
            # Configure mock to capture specific log calls
            mock_logger.error.assert_called_with("Configuration validation failed: Invalid timeout value")

    Example:
        def test_config_validator_logs_results(mock_logger, monkeypatch):
            # Replace the module logger with our mock
            monkeypatch.setattr('app.infrastructure.resilience.config_validator.logger', mock_logger)

            validator = ConfigValidator()
            result = validator.validate_config(invalid_config)

            # Verify validation errors were logged
            mock_logger.error.assert_called()
            assert any("validation" in str(call).lower() for call in mock_logger.error.call_args_list)

    Log Messages Captured:
        - Configuration validation results (success/failure)
        - Validation errors with specific field information
        - Validation warnings for deprecated or suboptimal settings
        - Configuration reload and update notifications
        - Security-related validation concerns
        - Performance optimization recommendations

    Log Levels Used:
        - info: Successful validation, configuration updates
        - warning: Validation warnings, deprecated settings
        - error: Validation failures, security issues
        - debug: Detailed validation process information
        - critical: Critical configuration security issues

    Note:
        This is a proper system boundary mock - logging performs I/O
        and should be mocked for unit tests to avoid actual log output.
    """
    mock = MagicMock()
    mock.info = Mock(return_value=None)
    mock.warning = Mock(return_value=None)
    mock.error = Mock(return_value=None)
    mock.debug = Mock(return_value=None)
    mock.critical = Mock(return_value=None)
    return mock


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