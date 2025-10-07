"""
Integration-specific fixtures for testing.
"""
import pytest
import os
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Disable rate limiting during integration tests
os.environ["RATE_LIMITING_ENABLED"] = "false"

from app.main import create_app


@pytest.fixture(autouse=True)
def setup_testing_environment_for_all_integration_tests(monkeypatch):
    """
    Set ENVIRONMENT='testing' for ALL integration tests.

    This prevents SecurityConfig from defaulting to production-level security
    which requires TLS certificates that don't exist in test environments.

    Test isolation is automatic via context-local environment detection.
    Each test context gets its own detector instance with no shared state.

    Applied to ALL integration tests (auth, cache, environment, health, startup).
    Individual tests can override by setting different ENVIRONMENT values.
    """
    # Set default testing environment
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "true")
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "gL/jVnZqgV5uKb/hYq1Jb3d8cZ5fJg6nO8r/d3gH2wA=")



@pytest.fixture(scope="function")
def production_environment_integration(monkeypatch):
    """
    Set up production environment with API keys for integration tests.

    Uses monkeypatch for proper cleanup after each test (function scope).
    This prevents environment pollution that was causing flaky tests.
    """
    # Set production environment with test API keys using monkeypatch
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("ADDITIONAL_API_KEYS", "test-key-2,test-key-3")


    # monkeypatch automatically cleans up after test


@pytest.fixture(scope="function")
def integration_app():
    """
    Fresh application instance for integration testing.

    Uses app factory pattern to ensure complete test isolation.
    Each test gets a fresh app instance that picks up current
    environment variables without any cached state.
    """
    return create_app()


@pytest.fixture(scope="function")
def integration_client(integration_app, production_environment_integration):
    """
    HTTP client for integration testing with production environment setup.

    Uses function scope to ensure each test gets a fresh client with a fresh
    app instance, providing complete test isolation.
    """
    return TestClient(integration_app)


@pytest.fixture(scope="function")
async def async_integration_client(integration_app):
    """
    Async HTTP client for integration testing.

    Uses function scope to ensure each test gets a fresh client with a fresh
    app instance, providing complete test isolation.
    """
    async with AsyncClient(
        transport=ASGITransport(app=integration_app),
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def authenticated_headers():
    """Headers with valid authentication for integration tests."""
    return {
        "Authorization": "Bearer test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_api_key_headers():
    """Headers with invalid API key for integration tests."""
    return {
        "Authorization": "Bearer invalid-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def x_api_key_headers():
    """Headers using X-API-Key instead of Authorization Bearer."""
    return {
        "X-API-Key": "test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def malformed_auth_headers():
    """Headers with malformed authentication."""
    return {
        "Authorization": "Invalid-Format test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def missing_auth_headers():
    """Headers without any authentication."""
    return {"Content-Type": "application/json"}


@pytest.fixture(scope="function")
def validate_environment_state():
    """
    Validates environment state before and after each test to detect pollution.

    This fixture captures the environment state before test execution and
    validates that no unexpected environment changes persist after the test.

    Business Impact:
        Prevents test pollution by detecting environment state changes early

    Use Cases:
        - Debugging flaky tests caused by environment pollution
        - Validating test isolation in complex test scenarios
        - Monitoring environment state during test development

    Returns:
        dict: Environment validation functions for use in tests
    """
    # Capture initial state
    initial_state = {}
    critical_vars = [
        "ENVIRONMENT", "API_KEY", "ADDITIONAL_API_KEYS", "ENFORCE_AUTH",
        "ENABLE_AI_CACHE", "REDIS_INSECURE_ALLOW_PLAINTEXT", "REDIS_ENCRYPTION_KEY",
        "DEBUG", "PRODUCTION", "CI", "RATE_LIMITING_ENABLED"
    ]

    for var in critical_vars:
        initial_state[var] = os.environ.get(var)

    def get_current_state():
        """Get current environment state."""
        current = {}
        for var in critical_vars:
            current[var] = os.environ.get(var)
        return current

    def validate_no_pollution():
        """Validate that environment hasn't been polluted."""
        current = get_current_state()
        polluted = []

        for var, initial_value in initial_state.items():
            current_value = current[var]
            if initial_value != current_value:
                polluted.append({
                    "variable": var,
                    "initial": initial_value,
                    "current": current_value
                })

        if polluted:
            print("\n⚠️  ENVIRONMENT POLLUTION DETECTED:")
            for item in polluted:
                print(f"   {item['variable']}: '{item['initial']}' → '{item['current']}'")
            print("   This may cause test flakiness!")

        return len(polluted) == 0

    return {
        "get_initial_state": lambda: initial_state.copy(),
        "get_current_state": get_current_state,
        "validate_no_pollution": validate_no_pollution,
        "critical_vars": critical_vars.copy()
    }


@pytest.fixture(scope="function")
def environment_state_monitor(validate_environment_state):
    """
    Monitors environment state changes during test execution.

    This fixture provides automatic environment state monitoring and
    reports any changes that might indicate test pollution.

    Business Impact:
        Provides early detection of test isolation issues

    Usage:
        def test_example(environment_state_monitor):
            # Test code here
            # Monitor will automatically report state changes
            pass
    """
    initial_state = validate_environment_state["get_initial_state"]()

    yield validate_environment_state

    # Automatic validation after test
    is_clean = validate_environment_state["validate_no_pollution"]()
    if not is_clean:
        # Add warning without failing the test
        print("\n🔍 Environment state monitoring detected changes - check test isolation")


@pytest.fixture(autouse=True, scope="function")
def environment_state_guard():
    """
    Automatic environment state guard for all integration tests.

    This autouse fixture monitors for unexpected environment state changes
    and provides warnings when potential pollution is detected.

    This is a lightweight guard that doesn't fail tests but provides
    visibility into potential isolation issues.
    """
    # Only monitor critical environment variables that affect test behavior
    critical_vars = ["ENVIRONMENT", "API_KEY", "DEBUG", "PRODUCTION"]

    # Capture state before test
    before_state = {var: os.environ.get(var) for var in critical_vars}

    yield

    # Check state after test
    after_state = {var: os.environ.get(var) for var in critical_vars}

    # Report significant changes
    changes = []
    for var in critical_vars:
        if before_state[var] != after_state[var]:
            changes.append(f"{var}: '{before_state[var]}' → '{after_state[var]}'")

    if changes:
        print("\n🔍 Environment state changes detected:")
        for change in changes:
            print(f"   {change}")
        print("   Note: This may be expected if test intentionally modifies environment")
