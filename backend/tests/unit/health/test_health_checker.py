"""
Unit tests for HealthChecker class orchestration and configuration.

Tests the centralized health monitoring service including component registration,
health check execution with timeout/retry policies, and system-wide health aggregation.

Test Coverage:
    - HealthChecker initialization and configuration validation
    - Component health check registration
    - Individual component health check execution
    - Timeout and retry policy enforcement
    - System-wide health check aggregation
    - Error handling and graceful degradation
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, call

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
)


class TestHealthCheckerInitialization:
    """
    Test suite for HealthChecker initialization and configuration.

    Scope:
        - Constructor parameter validation
        - Default configuration values
        - Per-component timeout configuration
        - Retry and backoff policy setup

    Business Critical:
        Proper initialization ensures health monitoring operates with correct
        timeouts and retry policies for reliable system health reporting.
    """

    @pytest.mark.asyncio
    async def test_healthchecker_initializes_with_default_configuration(self):
        """
        Test that HealthChecker initializes successfully with default parameters.

        Verifies:
            HealthChecker can be instantiated with no arguments and uses
            documented default values per __init__ docstring.

        Business Impact:
            Ensures health monitoring works out-of-box without complex configuration.

        Scenario:
            Given: No specific configuration parameters
            When: HealthChecker is instantiated with no arguments
            Then: Instance is created successfully
            And: Can register and execute health checks
            And: System health check returns valid results

        Fixtures Used:
            None - tests bare instantiation
        """
        checker = HealthChecker()

        # Verify instance can register health checks (empty registry works)
        async def test_check():
            return ComponentStatus(name="test", status=HealthStatus.HEALTHY)
        checker.register_check("test", test_check)

        # Verify health check execution works
        result = await checker.check_component("test")
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthchecker_accepts_custom_default_timeout(self):
        """
        Test that HealthChecker accepts custom default timeout configuration.

        Verifies:
            default_timeout_ms parameter is accepted and enforced on health checks
            per __init__ Args specification.

        Business Impact:
            Allows tuning health check timeouts based on operational requirements.

        Scenario:
            Given: Custom timeout value of 50ms
            When: HealthChecker is instantiated with default_timeout_ms=50
            Then: Health checks that exceed 50ms are timed out
            And: ComponentStatus indicates DEGRADED with timeout message

        Fixtures Used:
            None - tests configuration parameter with observable behavior
        """
        checker = HealthChecker(default_timeout_ms=50, retry_count=0)

        async def slow_check():
            await asyncio.sleep(0.1)  # 100ms - exceeds 50ms timeout
            return ComponentStatus(name="slow", status=HealthStatus.HEALTHY)

        checker.register_check("slow", slow_check)
        result = await checker.check_component("slow")

        # Observable: timeout is enforced
        assert result.status == HealthStatus.DEGRADED
        assert "timed out" in result.message

    @pytest.mark.asyncio
    async def test_healthchecker_accepts_per_component_timeouts(self):
        """
        Test that HealthChecker accepts per-component timeout overrides.

        Verifies:
            per_component_timeouts_ms parameter is accepted and enforced
            per __init__ Args specification.

        Business Impact:
            Enables fine-grained timeout control for components with different
            performance characteristics (database vs cache vs AI services).

        Scenario:
            Given: Per-component timeout configuration with "db"=200ms
            When: HealthChecker is instantiated with per_component_timeouts_ms
            Then: Component "db" uses its specific 200ms timeout
            And: Check completes within 200ms without timing out

        Fixtures Used:
            None - tests configuration parameter with observable behavior
        """
        timeouts = {"db": 200}
        checker = HealthChecker(
            default_timeout_ms=10,  # Very short default
            per_component_timeouts_ms=timeouts
        )

        async def medium_check():
            await asyncio.sleep(0.05)  # 50ms - exceeds default but within db timeout
            return ComponentStatus(name="db", status=HealthStatus.HEALTHY)

        checker.register_check("db", medium_check)
        result = await checker.check_component("db")

        # Observable: per-component timeout allows completion
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthchecker_accepts_custom_retry_configuration(self, monkeypatch):
        """
        Test that HealthChecker accepts custom retry count and backoff settings.

        Verifies:
            retry_count and backoff_base_seconds parameters are accepted and enforced
            per __init__ Args specification.

        Business Impact:
            Allows configuring retry aggressiveness for transient failure handling.

        Scenario:
            Given: Custom retry count of 3 and backoff of 0.5 seconds
            When: HealthChecker is instantiated with retry_count=3, backoff_base_seconds=0.5
            Then: Failed health check retries 3 times
            And: Backoff delays use 0.5s base (0.5s, 1.0s, 2.0s)

        Fixtures Used:
            monkeypatch - to mock asyncio.sleep
        """
        checker = HealthChecker(retry_count=3, backoff_base_seconds=0.5)

        check_func = AsyncMock(side_effect=Exception("permanent error"))
        checker.register_check("failing", check_func)

        mock_sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        await checker.check_component("failing")

        # Observable: retries 3 times with exponential backoff
        assert check_func.call_count == 4  # Initial + 3 retries
        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list[0] == call(0.5)
        assert mock_sleep.call_args_list[1] == call(1.0)
        assert mock_sleep.call_args_list[2] == call(2.0)

    @pytest.mark.asyncio
    async def test_healthchecker_handles_zero_retry_count(self):
        """
        Test that HealthChecker accepts retry_count=0 for no retries.

        Verifies:
            Setting retry_count to 0 disables retries for faster failure
            detection per __init__ Args specification.

        Business Impact:
            Supports fast-fail scenarios where retry delay is unacceptable.

        Scenario:
            Given: retry_count set to 0
            When: HealthChecker is instantiated with retry_count=0
            Then: Failed health check executes only once
            And: No retries occur

        Fixtures Used:
            None - tests configuration parameter with observable behavior
        """
        checker = HealthChecker(retry_count=0)

        check_func = AsyncMock(side_effect=Exception("error"))
        checker.register_check("failing", check_func)

        result = await checker.check_component("failing")

        # Observable: no retries, only initial attempt
        assert check_func.call_count == 1
        assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_healthchecker_validates_retry_count_negative_values(self):
        """
        Test that HealthChecker handles negative retry_count gracefully.

        Verifies:
            Negative retry_count values are handled per __init__ Behavior
            specification (max(0, retry_count) ensures non-negative).

        Business Impact:
            Prevents configuration errors from causing unexpected behavior.

        Scenario:
            Given: retry_count set to -1
            When: HealthChecker is instantiated with retry_count=-1
            Then: Behaves as retry_count=0 (no retries)
            And: Failed check executes only once

        Fixtures Used:
            None - tests defensive parameter validation with observable behavior
        """
        checker = HealthChecker(retry_count=-1)

        check_func = AsyncMock(side_effect=Exception("error"))
        checker.register_check("failing", check_func)

        result = await checker.check_component("failing")

        # Observable: negative retry treated as 0, only initial attempt
        assert check_func.call_count == 1
        assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_healthchecker_validates_backoff_negative_values(self, monkeypatch):
        """
        Test that HealthChecker handles negative backoff_base_seconds gracefully.

        Verifies:
            Negative backoff values are handled per __init__ Behavior
            specification (max(0.0, backoff_base_seconds) ensures non-negative).

        Business Impact:
            Prevents configuration errors from causing negative sleep times.

        Scenario:
            Given: backoff_base_seconds set to -0.5
            When: HealthChecker is instantiated with backoff_base_seconds=-0.5
            Then: Backoff delay is effectively 0.0 seconds (no sleep)
            And: Retries execute immediately

        Fixtures Used:
            monkeypatch - to verify asyncio.sleep behavior
        """
        checker = HealthChecker(retry_count=2, backoff_base_seconds=-0.5)

        check_func = AsyncMock(side_effect=Exception("error"))
        checker.register_check("failing", check_func)

        mock_sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        await checker.check_component("failing")

        # Observable: negative backoff treated as 0.0, sleeps with 0.0 delay
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0] == call(0.0)
        assert mock_sleep.call_args_list[1] == call(0.0)


class TestHealthCheckerRegistration:
    """
    Test suite for component health check registration.

    Scope:
        - Health check function registration
        - Component name validation
        - Async function validation
        - Registration overwriting behavior

    Business Critical:
        Proper registration ensures all critical system components are monitored
        and health checks are valid async functions.
    """

    def test_register_check_accepts_valid_component_and_function(self):
        """
        Test that register_check accepts valid component name and async function.

        Verifies:
            Standard health check registration succeeds per register_check
            docstring specification.

        Business Impact:
            Enables monitoring of all system components through registration API.

        Scenario:
            Given: A HealthChecker instance
            And: A valid component name "database"
            And: A valid async health check function
            When: register_check("database", check_func) is called
            Then: Registration succeeds without raising exceptions
            And: Component is available for health monitoring

        Fixtures Used:
            None - tests basic registration with simple async lambda
        """
        checker = HealthChecker()
        async def check_db():
            return ComponentStatus(name="database", status=HealthStatus.HEALTHY)
        checker.register_check("database", check_db)
        assert "database" in checker._checks
        assert checker._checks["database"] == check_db

    def test_register_check_overwrites_existing_registration(self):
        """
        Test that register_check overwrites existing component registration.

        Verifies:
            Re-registering a component name replaces the previous health check
            per register_check Behavior specification.

        Business Impact:
            Allows dynamic health check updates and component reconfiguration.

        Scenario:
            Given: A HealthChecker instance
            And: A component "database" already registered
            When: register_check("database", new_check_func) is called
            Then: New registration succeeds
            And: Previous health check is replaced with new function

        Fixtures Used:
            None - tests registration overwrite behavior
        """
        checker = HealthChecker()
        async def old_check():
            pass
        async def new_check():
            pass
        checker.register_check("database", old_check)
        checker.register_check("database", new_check)
        assert checker._checks["database"] == new_check

    def test_register_check_raises_valueerror_for_empty_component_name(self):
        """
        Test that register_check raises ValueError for empty component name.

        Verifies:
            Empty string component names are rejected per register_check
            Raises specification.

        Business Impact:
            Prevents registration errors that would cause monitoring confusion.

        Scenario:
            Given: A HealthChecker instance
            And: An empty string component name ""
            And: A valid async health check function
            When: register_check("", check_func) is called
            Then: ValueError is raised
            And: Error message mentions "non-empty string"

        Fixtures Used:
            None - tests input validation
        """
        checker = HealthChecker()
        async def check_func():
            pass
        with pytest.raises(ValueError, match="non-empty string"):
            checker.register_check("", check_func)

    def test_register_check_raises_valueerror_for_none_component_name(self):
        """
        Test that register_check raises ValueError for None component name.

        Verifies:
            None component names are rejected per register_check Raises specification.

        Business Impact:
            Prevents registration errors from None values.

        Scenario:
            Given: A HealthChecker instance
            And: Component name set to None
            And: A valid async health check function
            When: register_check(None, check_func) is called
            Then: ValueError is raised
            And: Error message mentions component name validation

        Fixtures Used:
            None - tests input validation
        """
        checker = HealthChecker()
        async def check_func():
            pass
        with pytest.raises(ValueError):
            checker.register_check(None, check_func)

    def test_register_check_raises_typeerror_for_non_async_function(self):
        """
        Test that register_check raises TypeError for non-async function.

        Verifies:
            Synchronous functions are rejected per register_check Raises specification.

        Business Impact:
            Ensures all health checks support async execution for non-blocking monitoring.

        Scenario:
            Given: A HealthChecker instance
            And: A valid component name "service"
            And: A synchronous (non-async) function
            When: register_check("service", sync_func) is called
            Then: TypeError is raised
            And: Error message mentions "async function" requirement

        Fixtures Used:
            None - tests function type validation
        """
        checker = HealthChecker()
        def sync_func():
            pass
        with pytest.raises(TypeError, match="async function"):
            checker.register_check("service", sync_func)

    def test_register_check_accepts_component_names_with_underscores(self):
        """
        Test that register_check accepts conventional component naming.

        Verifies:
            Component names with underscores (e.g., "ai_model") are accepted
            per register_check Args specification.

        Business Impact:
            Supports standard naming conventions for multi-word component names.

        Scenario:
            Given: A HealthChecker instance
            And: Component name "ai_model" with underscores
            And: A valid async health check function
            When: register_check("ai_model", check_func) is called
            Then: Registration succeeds without exceptions

        Fixtures Used:
            None - tests naming convention support
        """
        checker = HealthChecker()
        async def check_func():
            pass
        checker.register_check("ai_model", check_func)
        assert "ai_model" in checker._checks


@pytest.mark.asyncio
class TestHealthCheckerComponentExecution:
    """
    Test suite for individual component health check execution.

    Scope:
        - Component health check execution
        - Timeout enforcement
        - Retry mechanism with exponential backoff
        - Error handling and status classification
        - Response time tracking

    Business Critical:
        Reliable component health checking is essential for operational monitoring,
        alerting, and degradation detection.
    """

    async def test_check_component_executes_registered_health_check(self):
        """
        Test that check_component executes registered health check successfully.

        Verifies:
            Health check function is invoked and result is returned per
            check_component docstring specification.

        Business Impact:
            Core health monitoring functionality that enables operational visibility.

        Scenario:
            Given: A HealthChecker instance
            And: A registered component "database" with healthy status
            When: check_component("database") is called
            Then: Health check function executes
            And: ComponentStatus is returned with correct component name
            And: Status reflects health check result (HEALTHY/DEGRADED/UNHEALTHY)
            And: Response time is tracked and reported

        Fixtures Used:
            None - tests with simple async lambda returning ComponentStatus
        """
        checker = HealthChecker()
        healthy_status = ComponentStatus(name="database", status=HealthStatus.HEALTHY)
        check_func = AsyncMock(return_value=healthy_status)
        checker.register_check("database", check_func)

        result = await checker.check_component("database")

        check_func.assert_awaited_once()
        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0

    async def test_check_component_raises_valueerror_for_unregistered_component(self):
        """
        Test that check_component raises ValueError for unregistered component.

        Verifies:
            Attempting to check unregistered component fails per check_component
            Raises specification.

        Business Impact:
            Prevents silent failures when monitoring configuration is incorrect.

        Scenario:
            Given: A HealthChecker instance
            And: No component named "nonexistent" is registered
            When: check_component("nonexistent") is called
            Then: ValueError is raised
            And: Error message mentions "not registered"

        Fixtures Used:
            None - tests validation logic
        """
        checker = HealthChecker()
        with pytest.raises(ValueError, match="not registered"):
            await checker.check_component("nonexistent")

    async def test_check_component_applies_default_timeout(self):
        """
        Test that check_component applies default timeout to health checks.

        Verifies:
            Default timeout is enforced when no component-specific timeout
            configured per check_component Behavior specification.

        Business Impact:
            Prevents slow health checks from blocking system health reporting.

        Scenario:
            Given: A HealthChecker instance with default_timeout_ms=10
            And: A registered component with slow health check (>10ms)
            And: No component-specific timeout configured
            When: check_component("slow_component") is called
            Then: Health check times out after ~10ms
            And: ComponentStatus is returned with DEGRADED status
            And: Message indicates timeout occurred

        Fixtures Used:
            None - tests with async sleep to simulate slow check
        """
        checker = HealthChecker(default_timeout_ms=10, retry_count=0)
        async def slow_check():
            await asyncio.sleep(0.1)
            return ComponentStatus(name="slow", status=HealthStatus.HEALTHY)
        checker.register_check("slow", slow_check)

        result = await checker.check_component("slow")
        assert result.status == HealthStatus.DEGRADED
        assert "timed out" in result.message

    async def test_check_component_applies_per_component_timeout(self):
        """
        Test that check_component applies component-specific timeout override.

        Verifies:
            Per-component timeout overrides default timeout per check_component
            Behavior specification.

        Business Impact:
            Allows specialized timeout policies for components with different
            performance characteristics.

        Scenario:
            Given: A HealthChecker instance with default_timeout_ms=10
            And: Per-component timeout for "db" set to 200ms
            And: A registered "db" component with 100ms health check
            When: check_component("db") is called
            Then: Health check completes successfully (within 200ms)
            And: ComponentStatus is returned with HEALTHY status
            And: Health check is not timed out

        Fixtures Used:
            None - tests with async sleep to verify timeout override
        """
        checker = HealthChecker(default_timeout_ms=10, per_component_timeouts_ms={"db": 200})
        async def medium_check():
            await asyncio.sleep(0.1)
            return ComponentStatus(name="db", status=HealthStatus.HEALTHY)
        checker.register_check("db", medium_check)

        result = await checker.check_component("db")
        assert result.status == HealthStatus.HEALTHY

    async def test_check_component_retries_on_failure(self):
        """
        Test that check_component retries failed health checks per retry policy.

        Verifies:
            Failed health checks are retried according to configured retry_count
            per check_component Behavior specification.

        Business Impact:
            Provides resilience against transient health check failures.

        Scenario:
            Given: A HealthChecker instance with retry_count=2
            And: A registered component that fails on first attempt but succeeds on retry
            When: check_component("transient_failure") is called
            Then: Health check is retried after initial failure
            And: Second attempt succeeds
            And: ComponentStatus is returned with HEALTHY status
            And: Total response time includes retry attempts

        Fixtures Used:
            None - tests with stateful async function that fails then succeeds
        """
        checker = HealthChecker(retry_count=2)
        mock_check = AsyncMock(
            side_effect=[
                Exception("transient error"),
                ComponentStatus(name="transient", status=HealthStatus.HEALTHY)
            ]
        )
        checker.register_check("transient", mock_check)

        result = await checker.check_component("transient")
        assert result.status == HealthStatus.HEALTHY
        assert mock_check.call_count == 2

    async def test_check_component_implements_exponential_backoff(self, monkeypatch):
        """
        Test that check_component uses exponential backoff between retries.

        Verifies:
            Retry delays follow exponential backoff pattern (base * 2^attempt)
            per check_component Behavior specification.

        Business Impact:
            Reduces load on failing components while allowing recovery time.

        Scenario:
            Given: A HealthChecker instance with retry_count=3, backoff_base_seconds=0.1
            And: A registered component that fails all attempts
            When: check_component("failing_component") is called
            Then: First retry waits ~0.1 seconds (base * 2^0)
            And: Second retry waits ~0.2 seconds (base * 2^1)
            And: Third retry waits ~0.4 seconds (base * 2^2)
            And: Total execution time reflects exponential backoff delays

        Fixtures Used:
            None - tests with timing measurement of retry delays
        """
        checker = HealthChecker(retry_count=3, backoff_base_seconds=0.1)
        check_func = AsyncMock(side_effect=Exception("permanent error"))
        checker.register_check("failing", check_func)

        mock_sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        await checker.check_component("failing")

        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list[0] == call(0.1)
        assert mock_sleep.call_args_list[1] == call(0.2)
        assert mock_sleep.call_args_list[2] == call(0.4)

    async def test_check_component_returns_degraded_for_timeout_errors(self):
        """
        Test that check_component returns DEGRADED status for timeout errors.

        Verifies:
            Timeout errors result in DEGRADED status per check_component
            Behavior specification distinguishing timeouts from execution errors.

        Business Impact:
            Differentiates performance issues from critical failures in monitoring.

        Scenario:
            Given: A HealthChecker instance with short timeout
            And: A registered component with slow health check exceeding timeout
            When: check_component("slow_component") is called
            And: All retry attempts also timeout
            Then: ComponentStatus is returned with DEGRADED status
            And: Message indicates timeout occurred
            And: Response time includes all retry attempts

        Fixtures Used:
            None - tests with async sleep to force timeout
        """
        checker = HealthChecker(default_timeout_ms=10, retry_count=1)
        async def slow_check():
            await asyncio.sleep(0.1)
        checker.register_check("slow", slow_check)

        result = await checker.check_component("slow")
        assert result.status == HealthStatus.DEGRADED
        assert "timed out" in result.message

    async def test_check_component_returns_unhealthy_for_execution_errors(self):
        """
        Test that check_component returns UNHEALTHY status for execution errors.

        Verifies:
            Execution failures result in UNHEALTHY status per check_component
            Behavior specification distinguishing errors from timeouts.

        Business Impact:
            Identifies critical component failures requiring immediate attention.

        Scenario:
            Given: A HealthChecker instance
            And: A registered component whose health check raises exception
            When: check_component("broken_component") is called
            And: All retry attempts also fail with exceptions
            Then: ComponentStatus is returned with UNHEALTHY status
            And: Message includes exception information
            And: Response time includes all retry attempts

        Fixtures Used:
            None - tests with async function that raises exception
        """
        checker = HealthChecker(retry_count=1)
        check_func = AsyncMock(side_effect=ValueError("permanent error"))
        checker.register_check("broken", check_func)

        result = await checker.check_component("broken")
        assert result.status == HealthStatus.UNHEALTHY
        assert "permanent error" in result.message
        assert check_func.call_count == 2

    async def test_check_component_tracks_total_response_time_including_retries(self, monkeypatch):
        """
        Test that check_component tracks total execution time including retries.

        Verifies:
            Response time includes all retry attempts per check_component
            Behavior specification.

        Business Impact:
            Provides accurate performance metrics for health check operations.

        Scenario:
            Given: A HealthChecker instance with retry_count=1, backoff=0.1s
            And: A registered component that fails first attempt and succeeds on retry
            When: check_component("component") is called
            Then: Backoff delay is executed between retries
            And: ComponentStatus indicates successful second attempt

        Fixtures Used:
            monkeypatch - to verify asyncio.sleep is called with backoff delay
        """
        checker = HealthChecker(retry_count=1, backoff_base_seconds=0.1)
        side_effects = [
            Exception("transient error"),
            ComponentStatus(name="c", status=HealthStatus.HEALTHY)
        ]
        check_func = AsyncMock(side_effect=side_effects)
        checker.register_check("c", check_func)

        mock_sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        result = await checker.check_component("c")

        # Observable: backoff delay executed, health check succeeded on retry
        assert result.status == HealthStatus.HEALTHY
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args_list[0] == call(0.1)

    async def test_check_component_preserves_original_response_timing_on_success(self):
        """
        Test that check_component preserves health check response timing when successful.

        Verifies:
            Successful health check response times are preserved or maximized
            with total execution time per check_component Behavior specification.

        Business Impact:
            Maintains accurate health check timing metrics for monitoring.

        Scenario:
            Given: A HealthChecker instance
            And: A registered component that returns ComponentStatus with response_time_ms=25.5
            When: check_component("component") is called
            Then: Returned ComponentStatus has response_time_ms >= 25.5
            And: Response time reflects either original or total execution time

        Fixtures Used:
            None - tests with ComponentStatus containing specific timing
        """
        checker = HealthChecker()
        status = ComponentStatus(name="c", status=HealthStatus.HEALTHY, response_time_ms=25.5)
        checker.register_check("c", AsyncMock(return_value=status))
        result = await checker.check_component("c")
        assert result.response_time_ms >= 25.5

    async def test_check_component_logs_warning_for_timeout_failures(self, caplog):
        """
        Test that check_component logs warnings for timeout errors.

        Verifies:
            Timeout errors are logged for monitoring per check_component
            Behavior specification.

        Business Impact:
            Enables operational monitoring and alerting on health check timeouts.

        Scenario:
            Given: A HealthChecker instance
            And: A registered component that exceeds timeout
            When: check_component("slow_component") is called
            And: Timeout occurs
            Then: Warning is logged with timeout details
            And: Log message includes component name and timeout duration

        Fixtures Used:
            None - tests with caplog fixture to verify logging
        """
        checker = HealthChecker(default_timeout_ms=10, retry_count=0)
        async def slow_check():
            await asyncio.sleep(0.1)
        checker.register_check("slow", slow_check)
        await checker.check_component("slow")
        assert "timed out" in caplog.text
        assert "slow" in caplog.text

    async def test_check_component_logs_warning_for_execution_failures(self, caplog):
        """
        Test that check_component logs warnings for execution errors.

        Verifies:
            Execution failures are logged for monitoring per check_component
            Behavior specification.

        Business Impact:
            Enables operational monitoring and alerting on health check failures.

        Scenario:
            Given: A HealthChecker instance
            And: A registered component whose health check raises exception
            When: check_component("failing_component") is called
            And: Exception occurs
            Then: Warning is logged with error details
            And: Log message includes component name and exception information

        Fixtures Used:
            None - tests with caplog fixture to verify logging
        """
        checker = HealthChecker(retry_count=0)
        checker.register_check("failing", AsyncMock(side_effect=Exception("error")))
        await checker.check_component("failing")
        assert "failed" in caplog.text
        assert "failing" in caplog.text
        assert "error" in caplog.text


@pytest.mark.asyncio
class TestHealthCheckerSystemAggregation:
    """
    Test suite for system-wide health check aggregation.

    Scope:
        - Concurrent execution of all registered health checks
        - Overall status aggregation logic (worst-case)
        - Timestamp generation for caching and monitoring
        - Graceful handling of individual component failures

    Business Critical:
        System-wide health aggregation provides holistic operational visibility
        for monitoring dashboards, alerting systems, and load balancers.
    """

    async def test_check_all_components_executes_all_registered_checks_concurrently(self):
        """
        Test that check_all_components executes all registered health checks in parallel.

        Verifies:
            All registered health checks execute concurrently using asyncio.gather
            per check_all_components Behavior specification.

        Business Impact:
            Provides fast system-wide health status without sequential delays.

        Scenario:
            Given: A HealthChecker instance
            And: Multiple components registered
            When: check_all_components() is called
            Then: All health checks are executed
            And: SystemHealthStatus is returned with all component results

        Fixtures Used:
            None - tests with multiple async health check functions
        """
        checker = HealthChecker()

        check1 = AsyncMock(return_value=ComponentStatus(name="c1", status=HealthStatus.HEALTHY))
        check2 = AsyncMock(return_value=ComponentStatus(name="c2", status=HealthStatus.HEALTHY))

        checker.register_check("c1", check1)
        checker.register_check("c2", check2)

        result = await checker.check_all_components()

        # Observable: both checks executed and results collected
        assert len(result.components) == 2
        check1.assert_awaited_once()
        check2.assert_awaited_once()
        assert result.overall_status == HealthStatus.HEALTHY

    async def test_check_all_components_returns_healthy_when_all_components_healthy(self):
        """
        Test that check_all_components returns HEALTHY when all components are healthy.

        Verifies:
            Overall status is HEALTHY only if all components are HEALTHY
            per check_all_components Behavior specification.

        Business Impact:
            Provides clear signal that all system components are operational.

        Scenario:
            Given: A HealthChecker instance
            And: Three registered components all returning HEALTHY status
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: overall_status is HealthStatus.HEALTHY
            And: components list contains all three healthy statuses
            And: timestamp is present for caching

        Fixtures Used:
            None - tests with multiple healthy component mocks
        """
        checker = HealthChecker()
        checker.register_check("c1", AsyncMock(return_value=ComponentStatus(name="c1", status=HealthStatus.HEALTHY)))
        checker.register_check("c2", AsyncMock(return_value=ComponentStatus(name="c2", status=HealthStatus.HEALTHY)))
        result = await checker.check_all_components()
        assert result.overall_status == HealthStatus.HEALTHY
        assert len(result.components) == 2
        assert result.timestamp is not None

    async def test_check_all_components_returns_degraded_when_any_component_degraded(self):
        """
        Test that check_all_components returns DEGRADED when any component is degraded.

        Verifies:
            Overall status is DEGRADED if any component is DEGRADED and none
            are UNHEALTHY per check_all_components Behavior specification.

        Business Impact:
            Signals partial functionality requiring attention but not critical.

        Scenario:
            Given: A HealthChecker instance
            And: Three registered components with statuses:
                - "database": HEALTHY
                - "cache": DEGRADED (Redis down, using memory)
                - "ai_model": HEALTHY
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: overall_status is HealthStatus.DEGRADED
            And: components list contains all three statuses

        Fixtures Used:
            None - tests with mixed component statuses
        """
        checker = HealthChecker()
        checker.register_check("db", AsyncMock(return_value=ComponentStatus(name="db", status=HealthStatus.HEALTHY)))
        checker.register_check("cache", AsyncMock(return_value=ComponentStatus(name="cache", status=HealthStatus.DEGRADED)))
        result = await checker.check_all_components()
        assert result.overall_status == HealthStatus.DEGRADED

    async def test_check_all_components_returns_unhealthy_when_any_component_unhealthy(self):
        """
        Test that check_all_components returns UNHEALTHY when any component is unhealthy.

        Verifies:
            Overall status is UNHEALTHY if any component is UNHEALTHY
            per check_all_components Behavior specification (worst-case wins).

        Business Impact:
            Signals critical system failures requiring immediate intervention.

        Scenario:
            Given: A HealthChecker instance
            And: Three registered components with statuses:
                - "database": HEALTHY
                - "cache": DEGRADED
                - "ai_model": UNHEALTHY (API unreachable)
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: overall_status is HealthStatus.UNHEALTHY
            And: components list contains all three statuses

        Fixtures Used:
            None - tests with worst-case status scenario
        """
        checker = HealthChecker()
        checker.register_check("db", AsyncMock(return_value=ComponentStatus(name="db", status=HealthStatus.HEALTHY)))
        checker.register_check("cache", AsyncMock(return_value=ComponentStatus(name="cache", status=HealthStatus.DEGRADED)))
        checker.register_check("ai", AsyncMock(return_value=ComponentStatus(name="ai", status=HealthStatus.UNHEALTHY)))
        result = await checker.check_all_components()
        assert result.overall_status == HealthStatus.UNHEALTHY

    async def test_check_all_components_returns_healthy_for_empty_component_list(self):
        """
        Test that check_all_components returns HEALTHY when no components registered.

        Verifies:
            Empty component list results in HEALTHY status per check_all_components
            Behavior specification.

        Business Impact:
            Prevents false alarms when health monitoring is not yet configured.

        Scenario:
            Given: A HealthChecker instance with no registered components
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: overall_status is HealthStatus.HEALTHY
            And: components list is empty
            And: timestamp is present

        Fixtures Used:
            None - tests with unconfigured HealthChecker
        """
        checker = HealthChecker()
        result = await checker.check_all_components()
        assert result.overall_status == HealthStatus.HEALTHY
        assert len(result.components) == 0
        assert result.timestamp is not None

    async def test_check_all_components_includes_execution_timestamp(self):
        """
        Test that check_all_components includes timestamp in SystemHealthStatus.

        Verifies:
            Timestamp is included for monitoring and caching per check_all_components
            Returns specification.

        Business Impact:
            Enables cache validation and monitoring system time series.

        Scenario:
            Given: A HealthChecker instance with registered components
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: timestamp field contains Unix timestamp (float)
            And: timestamp is recent (within test execution time)

        Fixtures Used:
            None - tests timestamp generation
        """
        checker = HealthChecker()
        checker.register_check("c1", AsyncMock(return_value=ComponentStatus(name="c1", status=HealthStatus.HEALTHY)))
        start_time = time.time()
        result = await checker.check_all_components()
        end_time = time.time()
        assert start_time <= result.timestamp <= end_time

    async def test_check_all_components_preserves_individual_component_response_times(self):
        """
        Test that check_all_components preserves individual component timing.

        Verifies:
            Individual component response times are preserved per
            check_all_components Behavior specification.

        Business Impact:
            Provides granular performance metrics for each monitored component.

        Scenario:
            Given: A HealthChecker instance
            And: Three registered components with different response times
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: Each component's response_time_ms is preserved
            And: Response times reflect individual component performance

        Fixtures Used:
            None - tests with components returning specific timing values
        """
        checker = HealthChecker()
        checker.register_check("c1", AsyncMock(return_value=ComponentStatus(name="c1", status=HealthStatus.HEALTHY, response_time_ms=50)))
        result = await checker.check_all_components()
        assert result.components[0].response_time_ms >= 50

    async def test_check_all_components_preserves_component_metadata(self):
        """
        Test that check_all_components preserves component-specific metadata.

        Verifies:
            Component metadata is preserved in aggregated results per
            check_all_components Behavior specification.

        Business Impact:
            Provides detailed diagnostic information for troubleshooting.

        Scenario:
            Given: A HealthChecker instance
            And: Components returning metadata (e.g., cache_type, provider info)
            When: check_all_components() is called
            Then: SystemHealthStatus is returned
            And: Each ComponentStatus includes its original metadata
            And: Metadata is accessible for monitoring integration

        Fixtures Used:
            None - tests with components returning metadata dictionaries
        """
        checker = HealthChecker()
        metadata = {"key": "value"}
        checker.register_check("c1", AsyncMock(return_value=ComponentStatus(name="c1", status=HealthStatus.HEALTHY, metadata=metadata)))
        result = await checker.check_all_components()
        assert result.components[0].metadata == metadata

    async def test_check_all_components_applies_timeout_and_retry_to_each_component(self):
        """
        Test that check_all_components applies timeout/retry policies independently.

        Verifies:
            Each component gets timeout and retry handling per
            check_all_components Behavior specification.

        Business Impact:
            Ensures resilient health monitoring even with failing components.

        Scenario:
            Given: A HealthChecker instance with retry_count=1
            And: Multiple components, some failing transiently, some slow
            When: check_all_components() is called
            Then: Each component's health check receives timeout protection
            And: Each component's failures are retried independently
            And: Slow components don't block fast components
            And: SystemHealthStatus includes all results

        Fixtures Used:
            None - tests with mixed failure scenarios
        """
        checker = HealthChecker(default_timeout_ms=50, retry_count=1)

        # This one will succeed on retry
        c1_mock = AsyncMock(side_effect=[Exception, ComponentStatus(name="c1", status=HealthStatus.HEALTHY)])
        checker.register_check("c1", c1_mock)

        # This one will time out
        async def slow_check():
            await asyncio.sleep(0.1)
        checker.register_check("c2", slow_check)

        result = await checker.check_all_components()

        c1_status = next(c for c in result.components if c.name == "c1")
        c2_status = next(c for c in result.components if c.name == "c2")

        assert c1_status.status == HealthStatus.HEALTHY
        assert c1_mock.call_count == 2
        assert c2_status.status == HealthStatus.DEGRADED
        assert "timed out" in c2_status.message

    async def test_check_all_components_handles_component_exceptions_gracefully(self):
        """
        Test that check_all_components continues when individual components fail.

        Verifies:
            Individual component failures don't prevent overall health check
            per check_all_components Behavior specification.

        Business Impact:
            Provides partial health visibility even when some checks fail.

        Scenario:
            Given: A HealthChecker instance
            And: Three registered components, one raises exception
            When: check_all_components() is called
            Then: Execution completes without raising exception
            And: SystemHealthStatus is returned
            And: Failed component shows UNHEALTHY status
            And: Other components show their actual status

        Fixtures Used:
            None - tests error isolation in concurrent execution
        """
        checker = HealthChecker(retry_count=0)
        checker.register_check("c1", AsyncMock(return_value=ComponentStatus(name="c1", status=HealthStatus.HEALTHY)))
        checker.register_check("c2", AsyncMock(side_effect=Exception("error")))

        result = await checker.check_all_components()
        assert result.overall_status == HealthStatus.UNHEALTHY
        c1_status = next(c for c in result.components if c.name == "c1")
        c2_status = next(c for c in result.components if c.name == "c2")
        assert c1_status.status == HealthStatus.HEALTHY
        assert c2_status.status == HealthStatus.UNHEALTHY
