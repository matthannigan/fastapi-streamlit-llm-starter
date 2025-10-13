"""
Infrastructure-specific fixtures for testing.

This module provides shared fixtures used across multiple test modules including
encryption, startup, and other infrastructure components.

Fixture Categories:
    - Settings fixtures (test_settings, development_settings, production_settings)
    - Encryption key fixtures (valid_fernet_key, invalid keys, empty key)
    - Mock logger fixtures (mock_logger)
    - Cryptography availability fixtures (mock_cryptography_unavailable)
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import threading as real_threading


@pytest.fixture
def mock_infrastructure_config():
    """Mock configuration for infrastructure components."""
    return {
        "cache_enabled": True,
        "resilience_enabled": True,
        "monitoring_enabled": True
    }

# =============================================================================
# Mock Settings Fixtures
# =============================================================================

@pytest.fixture
def test_settings():
    """
    Real Settings instance with test configuration for testing actual configuration behavior.

    Provides a Settings instance loaded from test configuration, enabling tests
    to verify actual configuration loading, validation, and environment detection
    instead of using hardcoded mock values.

    This fixture represents behavior-driven testing where we test the actual
    Settings class functionality rather than mocking its behavior.
    """
    import tempfile
    import json
    import os
    from app.core.config import Settings

    # Create test configuration with realistic values
    test_config = {
        "gemini_api_key": "test-gemini-api-key-12345",
        "ai_model": "gemini-2.0-flash-exp",
        "ai_temperature": 0.7,
        "host": "0.0.0.0",
        "port": 8000,
        "api_key": "test-api-key-12345",
        "additional_api_keys": "key1,key2,key3",
        "debug": False,
        "log_level": "INFO",
        "cache_preset": "development",
        "resilience_preset": "simple",
        "health_check_timeout_ms": 2000
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_config, f, indent=2)
        config_file = f.name

    try:
        # Create Settings instance with test config
        # Override environment variables to ensure test isolation
        test_env = {
            "GEMINI_API_KEY": "test-gemini-api-key-12345",
            "API_KEY": "test-api-key-12345",
            "CACHE_PRESET": "development",
            "RESILIENCE_PRESET": "simple"
        }

        # Temporarily set test environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        # Create real Settings instance
        settings = Settings()

        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

        return settings

    finally:
        # Clean up temporary config file
        os.unlink(config_file)


@pytest.fixture
def development_settings():
    """
    Real Settings instance configured for development environment testing.

    Provides Settings with development preset for testing development-specific behavior.
    """
    import os

    # Set development environment variables
    test_env = {
        "GEMINI_API_KEY": "test-dev-api-key",
        "API_KEY": "test-dev-api-key",
        "CACHE_PRESET": "development",
        "RESILIENCE_PRESET": "development",
        "DEBUG": "true"
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture
def production_settings():
    """
    Real Settings instance configured for production environment testing.

    Provides Settings with production preset for testing production-specific behavior.
    """
    import os

    # Set production environment variables
    test_env = {
        "GEMINI_API_KEY": "test-prod-api-key",
        "API_KEY": "test-prod-api-key",
        "CACHE_PRESET": "production",
        "RESILIENCE_PRESET": "production",
        "DEBUG": "false"
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


# =============================================================================
# Shared Encryption Key Fixtures (Used by encryption and startup modules)
# =============================================================================


@pytest.fixture
def valid_fernet_key():
    """
    Valid Fernet encryption key for testing encryption functionality.

    Provides a properly formatted base64-encoded Fernet key (44 characters)
    that can be used across any module testing encryption behavior.

    Returns:
        Base64-encoded Fernet key as string

    Use Cases:
        - Testing encryption initialization (cache encryption module)
        - Testing encryption key validation (startup security module)
        - Testing encryption/decryption operations
        - Cross-module encryption testing

    Example:
        def test_encryption_with_valid_key(valid_fernet_key):
            encryption = EncryptedCacheLayer(encryption_key=valid_fernet_key)
            assert encryption.is_enabled is True

    Note:
        This is a real Fernet key generated for testing only.
        Do NOT use in production.
    """
    try:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    except ImportError:
        # Fallback to static test key if cryptography not available
        return "dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ=="


@pytest.fixture
def invalid_fernet_key_short():
    """
    Invalid encryption key (too short) for testing error handling.

    Provides a key that's too short to be a valid Fernet key (< 44 chars)
    for testing key length validation across modules.

    Returns:
        String that's too short to be a valid Fernet key

    Use Cases:
        - Testing key length validation in encryption module
        - Testing key validation in startup security module
        - Testing ConfigurationError raising
        - Testing error messages for invalid keys

    Example:
        def test_rejects_short_key(invalid_fernet_key_short):
            with pytest.raises(ConfigurationError):
                EncryptedCacheLayer(encryption_key=invalid_fernet_key_short)
    """
    return "too-short-key"


@pytest.fixture
def invalid_fernet_key_format():
    """
    Invalid encryption key (wrong format) for testing base64 validation.

    Provides a 44-character string that isn't valid base64 encoding
    for testing format validation logic.

    Returns:
        44-character string that isn't valid base64

    Use Cases:
        - Testing key format validation
        - Testing base64 decoding errors
        - Testing error message clarity
        - Cross-module format validation testing

    Example:
        def test_rejects_invalid_format(invalid_fernet_key_format):
            with pytest.raises(ConfigurationError):
                validator.validate_encryption_key(invalid_fernet_key_format)
    """
    return "!" * 44  # 44 chars but invalid base64


@pytest.fixture
def empty_encryption_key():
    """
    None encryption key for testing disabled encryption scenarios.

    Returns None to simulate missing or disabled encryption configuration
    for testing graceful degradation and warning generation.

    Returns:
        None (no encryption key)

    Use Cases:
        - Testing disabled encryption behavior in cache module
        - Testing missing encryption key handling in startup module
        - Testing warning message generation
        - Testing development mode flexibility

    Example:
        def test_encryption_disabled_without_key(empty_encryption_key):
            encryption = EncryptedCacheLayer(encryption_key=empty_encryption_key)
            assert encryption.is_enabled is False
    """
    return


# =============================================================================
# Shared Mock Date/Time Fixtures
# =============================================================================


@pytest.fixture
def fake_time_module():
    """
    Fake time module implementation for deterministic timing testing.

    Provides a controllable time implementation that allows tests to control
    time progression without using real time delays. This enables deterministic
    testing of timeout behavior, validation timing, performance measurements,
    and time-dependent configuration validation without making tests slow.

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
        - Testing circuit breaker recovery timeout behavior
        - Testing validation timeout behavior
        - Testing performance measurement accuracy
        - Testing time-based circuit breaker behavior
        - Testing retry backoff timing logic
        - Testing configuration reload timing
        - Testing background validation scheduling
        - Any time-dependent resilience logic testing

    Test Customization:
        def test_timeout_behavior(fake_time_module):
            # Start at known time
            fake_time_module.reset()

            # Simulate operation taking 5 seconds
            fake_time_module.advance(5.0)

            # Test timeout logic
            assert fake_time_module.time() >= 5.0

    Example:
        def test_circuit_breaker_recovery_timing(fake_time_module, monkeypatch):
            # Replace time module with our fake
            monkeypatch.setattr('app.infrastructure.resilience.circuit_breaker.time', fake_time_module)

            cb = EnhancedCircuitBreaker(recovery_timeout=60)

            # Trigger failure at t=0
            fake_time_module.reset()
            # ... cause circuit to open ...

            # Advance time past recovery timeout
            fake_time_module.advance(61)

            # Circuit should now allow recovery attempts
            assert cb.state == "HALF_OPEN"

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
        This fake enables fast, deterministic testing of time-dependent logic
        without making tests slow or flaky due to real timing variations.
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

    fake_time = FakeTimeModule()
    return fake_time


@pytest.fixture
def fake_datetime():
    """
    Fake datetime implementation for deterministic timestamp testing.

    Provides a controllable datetime implementation that allows tests
    to control time progression without using real time delays.
    This enables deterministic testing of time-dependent circuit breaker
    behavior like recovery timeouts and metrics timestamps.

    State Management:
        - Current time starts at a fixed datetime (2023-01-01 12:00:00)
        - Time can be advanced programmatically for testing
        - All datetime operations return consistent, predictable results
        - Maintains realistic datetime interface compatibility

    Public Methods:
        now(): Returns current fake datetime
        advance_timedelta(delta): Advances time by specified timedelta
        advance_seconds(seconds): Advances time by specified seconds
        reset(): Resets time to initial value

    Use Cases:
        - Testing circuit breaker recovery timeout behavior
        - Testing metrics timestamp recording and accuracy
        - Testing time-based state transitions without real delays
        - Any time-dependent resilience logic testing

    Test Customization:
        def test_recovery_timeout(fake_datetime):
            # Start at known time
            fake_datetime.reset()

            # Trigger failure and advance time
            # ... circuit breaker opens ...
            fake_datetime.advance_seconds(61)  # Past 60s timeout

            # Test recovery behavior

    Example:
        def test_circuit_breaker_recovery_timing(fake_datetime, monkeypatch):
            # Replace datetime with our fake
            monkeypatch.setattr('app.infrastructure.resilience.circuit_breaker.datetime', fake_datetime)

            cb = EnhancedCircuitBreaker(recovery_timeout=60)

            # Trigger failure at t=0
            fake_datetime.reset()
            # ... cause circuit to open ...

            # Advance time past recovery timeout
            fake_datetime.advance_seconds(61)

            # Circuit should now allow recovery attempts
            assert cb.state == "HALF_OPEN"

    State Behavior:
        - Time starts at 2023-01-01 12:00:00 UTC for consistency
        - Time can be advanced positively but not backwards
        - All datetime objects are real datetime instances with fake times
        - Maintains thread safety for concurrent test scenarios
    """

    class FakeDatetime:
        def __init__(self):
            self._current_time = datetime(2023, 1, 1, 12, 0, 0)
            self._initial_time = self._current_time
            # Attributes to make this behave like datetime module
            self.datetime: "FakeDatetime" = None  # type: ignore
            self.timedelta = timedelta

        def now(self):
            """Return current fake datetime."""
            return self._current_time

        def advance_timedelta(self, delta: timedelta):
            """Advance time by specified timedelta."""
            if delta.total_seconds() >= 0:
                self._current_time += delta

        def advance_seconds(self, seconds: float):
            """Advance time by specified seconds."""
            if seconds >= 0:
                self._current_time += timedelta(seconds=seconds)

        def reset(self):
            """Reset time to initial value."""
            self._current_time = self._initial_time

        def __call__(self):
            """Make the fake datetime callable like datetime class."""
            return self

        # Support datetime class methods
        @classmethod
        def from_real_datetime(cls, real_dt):
            """Create fake datetime from real datetime value."""
            fake = cls()
            fake._current_time = real_dt
            fake._initial_time = real_dt
            return fake

    fake_datetime = FakeDatetime()
    # Set self-reference after instantiation
    fake_datetime.datetime = fake_datetime

    return fake_datetime


# =============================================================================
# Shared Mock Threading Fixtures
# =============================================================================


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

    return FakeThreadingModule()


# =============================================================================
# Shared Mock Logger Fixture (System Boundary)
# =============================================================================


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing logging behavior across all modules.

    Provides a spec'd mock logger that simulates logging.Logger
    for testing log message generation without actual I/O. Used by
    encryption, resilience, startup, and other infrastructure modules.

    Default Behavior:
        - All log methods available (info, warning, error, debug, critical)
        - No actual logging output (mocked)
        - Call tracking for assertions in tests
        - Realistic method signatures matching logging.Logger
        - Can be configured per-test for specific scenarios

    Use Cases:
        - Testing log messages in various modules
        - Testing state change logging
        - Testing metrics logging and monitoring behavior
        - Testing warning/error logging during failures
        - Testing validation result logging
        - Testing performance measurement logging
        - Any component needing to test logging behavior

    Test Customization:
        def test_logs_warning(mock_logger, monkeypatch):
            monkeypatch.setattr('app.some.module.logger', mock_logger)
            # Test code that logs
            mock_logger.warning.assert_called()

    Example:
        def test_encryption_logs_warning(mock_logger, monkeypatch):
            monkeypatch.setattr('app.infrastructure.cache.encryption.logger', mock_logger)
            encryption = EncryptedCacheLayer(encryption_key=None)
            mock_logger.warning.assert_called()

    Note:
        This is a proper system boundary mock - logger performs I/O
        and should not be tested as part of unit tests. Mocking at
        this boundary is appropriate for all modules.
    """
    mock = MagicMock()
    mock.info = Mock()
    mock.warning = Mock()
    mock.error = Mock()
    mock.debug = Mock()
    return mock


# =============================================================================
# Shared Cryptography Library Availability Fixture
# =============================================================================


@pytest.fixture
def mock_cryptography_unavailable(monkeypatch):
    """
    ⚠️ DEPRECATED: Do not use this fixture for new unit tests.

    This fixture attempts to mock cryptography library unavailability but has
    fundamental limitations at the unit test level. It is kept for backwards
    compatibility but should NOT be used for new tests.

    ❌ Why This Fixture Should NOT Be Used for Unit Tests:

    1. **Import-Time Loading Issue**: Cryptography is imported at module load
       time, before test fixtures run. The fixture cannot prevent imports that
       have already occurred.

    2. **Limited Effectiveness**: sys.modules patching doesn't prevent the
       cryptography library from being available when modules import it during
       test collection.

    3. **Test Isolation**: Proper testing of missing library scenarios requires
       an environment where cryptography is actually not installed.

    ✅ Recommended Approach - Integration Tests:

    For testing missing cryptography library scenarios, use integration tests
    with an actual environment where cryptography is not installed:

        # See: tests/integration/startup/TEST_PLAN_cryptography_unavailable.md
        # Use Docker, virtualenv, or tox to create environment without cryptography

    Previous Use Cases (Now Migrated to Integration Tests):
        ❌ Testing encryption initialization without cryptography
        ❌ Testing startup validation without cryptography
        ❌ Testing graceful failure modes and error messages
        ❌ Testing warning messages for missing dependencies

    Migration Guide:
        All tests using this fixture have been marked as skipped with references
        to the integration test plan at:
        tests/integration/startup/TEST_PLAN_cryptography_unavailable.md

    Implementation Note:
        This fixture uses sys.modules patching which is safer than patching
        builtins.__import__ (avoids pytest internal errors), but still cannot
        properly simulate missing libraries at unit test level.

    Status:
        - DEPRECATED for unit tests
        - Kept for backwards compatibility only
        - See integration test plan for proper implementation approach
    """
    import sys

    # Store original cryptography modules if they exist
    original_cryptography = sys.modules.get("cryptography")
    original_fernet = sys.modules.get("cryptography.fernet")

    # Remove cryptography modules from sys.modules to simulate unavailability
    if "cryptography" in sys.modules:
        del sys.modules["cryptography"]
    if "cryptography.fernet" in sys.modules:
        del sys.modules["cryptography.fernet"]

    # Patch the encryption module's Fernet import to raise ImportError
    def mock_fernet_import():
        raise ImportError("No module named 'cryptography'")

    # This will cause imports of cryptography to fail
    monkeypatch.setitem(sys.modules, "cryptography.fernet", None)

    yield

    # Restore original state after test
    if original_cryptography is not None:
        sys.modules["cryptography"] = original_cryptography
    elif "cryptography" in sys.modules:
        del sys.modules["cryptography"]

    if original_fernet is not None:
        sys.modules["cryptography.fernet"] = original_fernet
    elif "cryptography.fernet" in sys.modules:
        del sys.modules["cryptography.fernet"]
