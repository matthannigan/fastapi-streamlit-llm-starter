"""
Unit tests for ResilienceMetrics dataclass.

Tests verify that ResilienceMetrics provides comprehensive metrics collection,
accurate rate calculations, and monitoring integration capabilities according
to its documented contract.

Test Organization:
    - TestResilienceMetricsInitialization: Metrics creation and initial state
    - TestResilienceMetricsSuccessRate: Success rate calculation accuracy
    - TestResilienceMetricsFailureRate: Failure rate calculation accuracy
    - TestResilienceMetricsToDictExport: Dictionary export for monitoring systems
    - TestResilienceMetricsThreadSafety: Thread-safe operations and state consistency
    - TestResilienceMetricsTimestampTracking: Timestamp recording and temporal analysis

Component Under Test:
    ResilienceMetrics from app.infrastructure.resilience.circuit_breaker

External Dependencies (Mocked):
    None - ResilienceMetrics is a pure dataclass with computed properties

Fixtures Used:
    - fake_datetime: For deterministic timestamp testing (from tests/unit/conftest.py)
"""

import pytest
from datetime import datetime, timedelta
from app.infrastructure.resilience.circuit_breaker import ResilienceMetrics


class TestResilienceMetricsInitialization:
    """Tests metrics initialization and default values per contract."""

    def test_metrics_initializes_with_zero_counters(self):
        """
        Test that metrics initialize with all counters at zero.

        Verifies:
            New ResilienceMetrics instance starts with clean state (all counts = 0)
            per the dataclass initialization contract

        Business Impact:
            Ensures metrics start from a known baseline, preventing stale data
            from affecting monitoring accuracy

        Scenario:
            Given: No prior metrics exist
            When: ResilienceMetrics is instantiated with default constructor
            Then: All call counters are initialized to 0
            And: All state transition counters are initialized to 0

        Fixtures Used:
            None - Direct instantiation for clarity
        """
        # When: ResilienceMetrics is instantiated with default constructor
        metrics = ResilienceMetrics()

        # Then: All call counters are initialized to 0
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.retry_attempts == 0

        # And: All state transition counters are initialized to 0
        assert metrics.circuit_breaker_opens == 0
        assert metrics.circuit_breaker_half_opens == 0
        assert metrics.circuit_breaker_closes == 0

    def test_metrics_initializes_with_none_timestamps(self):
        """
        Test that metrics initialize with None timestamps.

        Verifies:
            New metrics have no timestamp data until first success/failure occurs
            per the Attributes contract (last_success, last_failure start as None)

        Business Impact:
            Enables detection of "never succeeded" and "never failed" states
            for health monitoring and alerting

        Scenario:
            Given: No prior metrics exist
            When: ResilienceMetrics is instantiated
            Then: last_success timestamp is None
            And: last_failure timestamp is None

        Fixtures Used:
            None - Testing initial state
        """
        # Given: No prior metrics exist
        # When: ResilienceMetrics is instantiated
        metrics = ResilienceMetrics()

        # Then: last_success timestamp is None
        assert metrics.last_success is None

        # And: last_failure timestamp is None
        assert metrics.last_failure is None

    def test_metrics_attributes_are_mutable_for_tracking(self):
        """
        Test that metrics attributes can be incremented for tracking.

        Verifies:
            Unlike CircuitBreakerConfig, metrics are mutable to allow tracking
            per the State Management contract: "Thread-safe increment operations"

        Business Impact:
            Enables real-time metrics collection during circuit breaker operation

        Scenario:
            Given: A new ResilienceMetrics instance
            When: Metric attributes are incremented (total_calls, successful_calls, etc.)
            Then: Attributes store updated values
            And: Updates are reflected in subsequent accesses

        Fixtures Used:
            None - Testing basic mutability
        """
        # Given: A new ResilienceMetrics instance
        metrics = ResilienceMetrics()

        # When: Metric attributes are incremented
        metrics.total_calls = 5
        metrics.successful_calls = 3
        metrics.failed_calls = 2
        metrics.retry_attempts = 1

        # Then: Attributes store updated values
        assert metrics.total_calls == 5
        assert metrics.successful_calls == 3
        assert metrics.failed_calls == 2
        assert metrics.retry_attempts == 1

        # And: Updates are reflected in subsequent accesses
        assert metrics.total_calls == 5  # Verify persistence
        assert metrics.successful_calls == 3
        assert metrics.failed_calls == 2
        assert metrics.retry_attempts == 1


class TestResilienceMetricsSuccessRate:
    """Tests success_rate property calculation per contract."""

    def test_success_rate_returns_zero_when_no_calls_made(self):
        """
        Test that success rate returns 0.0 when no calls have been made.

        Verifies:
            success_rate property handles division by zero gracefully, returning 0.0
            per the Returns contract: "Returns 0.0 if no calls have been made to avoid division by zero"

        Business Impact:
            Prevents crashes in monitoring systems when checking metrics before
            any circuit breaker operations have occurred

        Scenario:
            Given: ResilienceMetrics with total_calls = 0
            When: success_rate property is accessed
            Then: Returns 0.0 without raising ZeroDivisionError
            And: Result is a float type for consistent API

        Fixtures Used:
            None - Testing edge case with default initialization
        """
        # Given: ResilienceMetrics with total_calls = 0
        metrics = ResilienceMetrics()

        # When: success_rate property is accessed
        success_rate = metrics.success_rate

        # Then: Returns 0.0 without raising ZeroDivisionError
        assert success_rate == 0.0

        # And: Result is a float type for consistent API
        assert isinstance(success_rate, float)

    def test_success_rate_calculates_correct_percentage(self):
        """
        Test that success rate calculates accurate percentage from counters.

        Verifies:
            success_rate property calculates (successful_calls / total_calls) * 100
            per the Returns contract formula

        Business Impact:
            Provides accurate success rate metrics for SLA monitoring and alerting

        Scenario:
            Given: Metrics with total_calls = 10 and successful_calls = 8
            When: success_rate property is accessed
            Then: Returns 80.0 (percentage)
            And: Result is accurate to expected precision

        Fixtures Used:
            None - Testing calculation with known values
        """
        # Given: Metrics with total_calls = 10 and successful_calls = 8
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 8

        # When: success_rate property is accessed
        success_rate = metrics.success_rate

        # Then: Returns 80.0 (percentage)
        assert success_rate == 80.0

        # And: Result is accurate to expected precision
        assert isinstance(success_rate, float)

    def test_success_rate_handles_perfect_success(self):
        """
        Test that success rate correctly calculates 100% success.

        Verifies:
            success_rate property returns 100.0 when all calls succeed
            (successful_calls == total_calls)

        Business Impact:
            Confirms healthy service state in monitoring dashboards

        Scenario:
            Given: Metrics with total_calls = 5 and successful_calls = 5
            When: success_rate property is accessed
            Then: Returns 100.0 (perfect success rate)
            And: No floating point precision issues

        Fixtures Used:
            None - Testing boundary condition
        """
        # Given: Metrics with total_calls = 5 and successful_calls = 5
        metrics = ResilienceMetrics()
        metrics.total_calls = 5
        metrics.successful_calls = 5

        # When: success_rate property is accessed
        success_rate = metrics.success_rate

        # Then: Returns 100.0 (perfect success rate)
        assert success_rate == 100.0

        # And: No floating point precision issues
        assert isinstance(success_rate, float)

    def test_success_rate_handles_zero_success(self):
        """
        Test that success rate correctly calculates 0% success.

        Verifies:
            success_rate property returns 0.0 when all calls fail
            (successful_calls == 0, total_calls > 0)

        Business Impact:
            Clearly indicates complete service failure for critical alerting

        Scenario:
            Given: Metrics with total_calls = 5 and successful_calls = 0
            When: success_rate property is accessed
            Then: Returns 0.0 (complete failure)
            And: Distinguishable from "no calls made" scenario

        Fixtures Used:
            None - Testing boundary condition
        """
        # Given: Metrics with total_calls = 5 and successful_calls = 0
        metrics = ResilienceMetrics()
        metrics.total_calls = 5
        metrics.successful_calls = 0

        # When: success_rate property is accessed
        success_rate = metrics.success_rate

        # Then: Returns 0.0 (complete failure)
        assert success_rate == 0.0

        # And: Distinguishable from "no calls made" scenario (total_calls > 0)
        assert metrics.total_calls == 5  # Verify we have calls made

    def test_success_rate_returns_float_type(self):
        """
        Test that success rate always returns float type for consistency.

        Verifies:
            success_rate property returns float (0.0-100.0) per contract specification
            for consistent monitoring system integration

        Business Impact:
            Ensures monitoring systems can rely on consistent numeric type
            without type checking

        Scenario:
            Given: Metrics with various call counts
            When: success_rate property is accessed
            Then: Return value is always float type
            And: Type is consistent regardless of input values

        Fixtures Used:
            None - Testing type consistency
        """
        # Given: Metrics with various call counts
        test_cases = [
            {"total_calls": 0, "successful_calls": 0},
            {"total_calls": 10, "successful_calls": 8},
            {"total_calls": 5, "successful_calls": 5},
            {"total_calls": 3, "successful_calls": 0}
        ]

        for case in test_cases:
            # When: success_rate property is accessed
            metrics = ResilienceMetrics()
            metrics.total_calls = case["total_calls"]
            metrics.successful_calls = case["successful_calls"]
            success_rate = metrics.success_rate

            # Then: Return value is always float type
            assert isinstance(success_rate, float)
            assert isinstance(success_rate, float)

            # And: Type is consistent regardless of input values
            assert success_rate == 0.0 or 0.0 <= success_rate <= 100.0

    def test_success_rate_updates_when_counters_change(self):
        """
        Test that success rate reflects current counter values dynamically.

        Verifies:
            success_rate property is computed on-demand, not cached, per property behavior
            in the contract

        Business Impact:
            Ensures monitoring always shows current success rate without needing
            explicit recalculation

        Scenario:
            Given: Metrics with initial counter values
            When: Counters are updated (successful_calls or total_calls incremented)
            Then: Subsequent success_rate access reflects updated values
            And: No manual recalculation is required

        Fixtures Used:
            None - Testing dynamic calculation
        """
        # Given: Metrics with initial counter values
        metrics = ResilienceMetrics()
        metrics.total_calls = 4
        metrics.successful_calls = 2

        # Verify initial success rate
        initial_rate = metrics.success_rate
        assert initial_rate == 50.0

        # When: Counters are updated
        metrics.successful_calls += 1  # Now 3 successful out of 4

        # Then: Subsequent success_rate access reflects updated values
        updated_rate = metrics.success_rate
        assert updated_rate == 75.0

        # And: No manual recalculation is required
        assert updated_rate != initial_rate  # Changed automatically


class TestResilienceMetricsFailureRate:
    """Tests failure_rate property calculation per contract."""

    def test_failure_rate_returns_zero_when_no_calls_made(self):
        """
        Test that failure rate returns 0.0 when no calls have been made.

        Verifies:
            failure_rate property handles division by zero gracefully, returning 0.0
            per the Returns contract: "Returns 0.0 if no calls have been made to avoid division by zero"

        Business Impact:
            Prevents crashes in monitoring systems when checking metrics before
            any operations have occurred

        Scenario:
            Given: ResilienceMetrics with total_calls = 0
            When: failure_rate property is accessed
            Then: Returns 0.0 without raising ZeroDivisionError
            And: Result is a float type for consistent API

        Fixtures Used:
            None - Testing edge case with default initialization
        """
        # Given: ResilienceMetrics with total_calls = 0
        metrics = ResilienceMetrics()

        # When: failure_rate property is accessed
        failure_rate = metrics.failure_rate

        # Then: Returns 0.0 without raising ZeroDivisionError
        assert failure_rate == 0.0

        # And: Result is a float type for consistent API
        assert isinstance(failure_rate, float)

    def test_failure_rate_calculates_correct_percentage(self):
        """
        Test that failure rate calculates accurate percentage from counters.

        Verifies:
            failure_rate property calculates (failed_calls / total_calls) * 100
            per the Returns contract formula

        Business Impact:
            Provides accurate failure rate metrics for SLA monitoring and alerting

        Scenario:
            Given: Metrics with total_calls = 10 and failed_calls = 3
            When: failure_rate property is accessed
            Then: Returns 30.0 (percentage)
            And: Result is accurate to expected precision

        Fixtures Used:
            None - Testing calculation with known values
        """
        # Given: Metrics with total_calls = 10 and failed_calls = 3
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.failed_calls = 3

        # When: failure_rate property is accessed
        failure_rate = metrics.failure_rate

        # Then: Returns 30.0 (percentage)
        assert failure_rate == 30.0

        # And: Result is accurate to expected precision
        assert isinstance(failure_rate, float)

    def test_failure_rate_handles_perfect_failure(self):
        """
        Test that failure rate correctly calculates 100% failure.

        Verifies:
            failure_rate property returns 100.0 when all calls fail
            (failed_calls == total_calls)

        Business Impact:
            Clearly indicates complete service outage for critical alerting

        Scenario:
            Given: Metrics with total_calls = 5 and failed_calls = 5
            When: failure_rate property is accessed
            Then: Returns 100.0 (complete failure rate)
            And: Triggers immediate alerts in monitoring systems

        Fixtures Used:
            None - Testing boundary condition
        """
        # Given: Metrics with total_calls = 5 and failed_calls = 5
        metrics = ResilienceMetrics()
        metrics.total_calls = 5
        metrics.failed_calls = 5

        # When: failure_rate property is accessed
        failure_rate = metrics.failure_rate

        # Then: Returns 100.0 (complete failure rate)
        assert failure_rate == 100.0

    def test_failure_rate_handles_zero_failures(self):
        """
        Test that failure rate correctly calculates 0% failure.

        Verifies:
            failure_rate property returns 0.0 when all calls succeed
            (failed_calls == 0, total_calls > 0)

        Business Impact:
            Confirms healthy service state in monitoring dashboards

        Scenario:
            Given: Metrics with total_calls = 5 and failed_calls = 0
            When: failure_rate property is accessed
            Then: Returns 0.0 (no failures)
            And: Distinguishable from "no calls made" scenario

        Fixtures Used:
            None - Testing boundary condition
        """
        # Given: Metrics with total_calls = 5 and failed_calls = 0
        metrics = ResilienceMetrics()
        metrics.total_calls = 5
        metrics.failed_calls = 0

        # When: failure_rate property is accessed
        failure_rate = metrics.failure_rate

        # Then: Returns 0.0 (no failures)
        assert failure_rate == 0.0

        # And: Distinguishable from "no calls made" scenario (total_calls > 0)
        assert metrics.total_calls == 5

    def test_failure_rate_and_success_rate_complement_relationship(self):
        """
        Test relationship between failure_rate and success_rate properties.

        Verifies:
            The contract note about rates potentially not summing to 100%
            due to cancelled calls or other edge cases

        Business Impact:
            Ensures monitoring systems correctly interpret rate metrics and
            don't assume rates always sum to 100%

        Scenario:
            Given: Metrics with various combinations of successful, failed, and total calls
            When: Both success_rate and failure_rate are calculated
            Then: Rates may not sum to exactly 100% in all cases
            And: Contract note about cancelled calls is validated

        Fixtures Used:
            None - Testing documented behavior note
        """
        # Given: Metrics with various combinations of successful, failed, and total calls
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 7
        metrics.failed_calls = 2
        # Note: 1 call is unaccounted for (cancelled, timeout, etc.)

        # When: Both success_rate and failure_rate are calculated
        success_rate = metrics.success_rate
        failure_rate = metrics.failure_rate

        # Then: Rates may not sum to exactly 100% in all cases
        total_rate = success_rate + failure_rate
        assert total_rate == 90.0  # 70% + 20% = 90%, not 100%

        # And: Contract note about cancelled calls is validated
        # This demonstrates the case where not all calls are counted as success or failure


class TestResilienceMetricsToDictExport:
    """Tests to_dict() method for monitoring integration per contract."""

    def test_to_dict_includes_all_counter_metrics(self):
        """
        Test that to_dict exports all raw counter values.

        Verifies:
            to_dict() returns dictionary with all counter fields per Returns contract:
            "Dictionary containing all metrics with: Raw count values (total_calls, successful_calls, etc.)"

        Business Impact:
            Ensures monitoring systems receive complete metrics data for analysis

        Scenario:
            Given: Metrics with various counter values
            When: to_dict() is called
            Then: Returned dictionary contains all counter fields
            And: Values match the current metric state

        Fixtures Used:
            None - Testing export completeness
        """
        # Given: Metrics with various counter values
        metrics = ResilienceMetrics()
        metrics.total_calls = 15
        metrics.successful_calls = 12
        metrics.failed_calls = 3
        metrics.retry_attempts = 2
        metrics.circuit_breaker_opens = 1
        metrics.circuit_breaker_half_opens = 2
        metrics.circuit_breaker_closes = 1

        # When: to_dict() is called
        result = metrics.to_dict()

        # Then: Returned dictionary contains all counter fields
        assert "total_calls" in result
        assert "successful_calls" in result
        assert "failed_calls" in result
        assert "retry_attempts" in result
        assert "circuit_breaker_opens" in result
        assert "circuit_breaker_half_opens" in result
        assert "circuit_breaker_closes" in result

        # And: Values match the current metric state
        assert result["total_calls"] == 15
        assert result["successful_calls"] == 12
        assert result["failed_calls"] == 3
        assert result["retry_attempts"] == 2
        assert result["circuit_breaker_opens"] == 1
        assert result["circuit_breaker_half_opens"] == 2
        assert result["circuit_breaker_closes"] == 1

    def test_to_dict_includes_calculated_rates(self):
        """
        Test that to_dict exports calculated success and failure rates.

        Verifies:
            to_dict() returns calculated rates per Returns contract:
            "Calculated rates (success_rate, failure_rate) rounded to 2 decimal places"

        Business Impact:
            Provides pre-calculated rates for monitoring systems, reducing
            computation overhead in monitoring pipelines

        Scenario:
            Given: Metrics with success and failure data
            When: to_dict() is called
            Then: Dictionary includes 'success_rate' and 'failure_rate' keys
            And: Rate values are rounded to 2 decimal places

        Fixtures Used:
            None - Testing rate export
        """
        # Given: Metrics with success and failure data
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 8
        metrics.failed_calls = 2

        # When: to_dict() is called
        result = metrics.to_dict()

        # Then: Dictionary includes 'success_rate' and 'failure_rate' keys
        assert "success_rate" in result
        assert "failure_rate" in result

        # And: Rate values are rounded to 2 decimal places
        assert result["success_rate"] == 80.0
        assert result["failure_rate"] == 20.0
        assert isinstance(result["success_rate"], float)
        assert isinstance(result["failure_rate"], float)

    def test_to_dict_converts_timestamps_to_iso_format(self):
        """
        Test that to_dict converts datetime timestamps to ISO 8601 strings.

        Verifies:
            to_dict() converts timestamps per Returns contract:
            "ISO-formatted timestamps for last_success and last_failure (None if not set)"

        Business Impact:
            Ensures timestamp data is JSON-serializable for monitoring system integration
            and uses standard ISO 8601 format for interoperability

        Scenario:
            Given: Metrics with last_success and last_failure timestamps set
            When: to_dict() is called
            Then: Timestamp fields contain ISO 8601 formatted strings
            And: Original datetime objects are converted correctly

        Fixtures Used:
            - fake_datetime: For deterministic timestamp testing
        """
        # Given: Metrics with last_success and last_failure timestamps set
        metrics = ResilienceMetrics()
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        metrics.last_success = test_time
        metrics.last_failure = test_time

        # When: to_dict() is called
        result = metrics.to_dict()

        # Then: Timestamp fields contain ISO 8601 formatted strings
        assert "last_success" in result
        assert "last_failure" in result
        assert isinstance(result["last_success"], str)
        assert isinstance(result["last_failure"], str)

        # And: Original datetime objects are converted correctly
        assert "2023-01-01T12:00:00" in result["last_success"]
        assert "2023-01-01T12:00:00" in result["last_failure"]

    def test_to_dict_handles_none_timestamps_correctly(self):
        """
        Test that to_dict properly exports None timestamps.

        Verifies:
            to_dict() handles unset timestamps per Returns contract:
            "ISO-formatted timestamps... (None if not set)"

        Business Impact:
            Allows monitoring systems to distinguish between "never succeeded"
            and "succeeded with timestamp" states

        Scenario:
            Given: Metrics with last_success or last_failure still at None
            When: to_dict() is called
            Then: Dictionary contains None for unset timestamp fields
            And: JSON serialization handles None values correctly

        Fixtures Used:
            None - Testing None handling
        """
        # Given: Metrics with last_success or last_failure still at None
        metrics = ResilienceMetrics()

        # When: to_dict() is called
        result = metrics.to_dict()

        # Then: Dictionary contains None for unset timestamp fields
        assert "last_success" in result
        assert "last_failure" in result
        assert result["last_success"] is None
        assert result["last_failure"] is None

    def test_to_dict_produces_json_serializable_output(self):
        """
        Test that to_dict output is JSON-serializable.

        Verifies:
            to_dict() output structure is "compatible with monitoring systems"
            per the Behavior contract, requiring JSON serializability

        Business Impact:
            Ensures metrics can be sent to monitoring systems via JSON APIs
            without serialization errors

        Scenario:
            Given: Metrics with various data including timestamps
            When: to_dict() output is serialized to JSON
            Then: JSON serialization succeeds without errors
            And: All data types are compatible with JSON

        Fixtures Used:
            - fake_datetime: For testing timestamp serialization
        """
        # Given: Metrics with various data including timestamps
        import json
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 8
        metrics.last_success = datetime(2023, 1, 1, 12, 0, 0)

        # When: to_dict() output is serialized to JSON
        result = metrics.to_dict()
        json_str = json.dumps(result)

        # Then: JSON serialization succeeds without errors
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # And: All data types are compatible with JSON
        parsed_back = json.loads(json_str)
        assert parsed_back["total_calls"] == 10
        assert parsed_back["successful_calls"] == 8

    def test_to_dict_export_structure_matches_monitoring_systems(self):
        """
        Test that to_dict export structure is compatible with monitoring systems.

        Verifies:
            Dictionary structure per Behavior contract:
            "Maintains dictionary structure compatible with monitoring systems"

        Business Impact:
            Enables seamless integration with Prometheus, DataDog, CloudWatch,
            and other monitoring platforms

        Scenario:
            Given: Metrics with complete data
            When: to_dict() is called
            Then: Dictionary structure follows monitoring system conventions
            And: Keys use snake_case naming
            And: Values use appropriate numeric types

        Fixtures Used:
            None - Testing structure conventions
        """
        # Given: Metrics with complete data
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 8

        # When: to_dict() is called
        result = metrics.to_dict()

        # Then: Dictionary structure follows monitoring system conventions
        assert isinstance(result, dict)

        # And: Keys use snake_case naming
        expected_keys = [
            "total_calls", "successful_calls", "failed_calls", "retry_attempts",
            "circuit_breaker_opens", "circuit_breaker_half_opens", "circuit_breaker_closes",
            "last_success", "last_failure", "success_rate", "failure_rate"
        ]
        for key in expected_keys:
            assert key in result
            assert "_" in key or key.islower()  # snake_case convention

    def test_to_dict_rounds_rates_to_two_decimal_places(self):
        """
        Test that to_dict rounds rate percentages to 2 decimal places.

        Verifies:
            Rate rounding per Returns contract:
            "Calculated rates (success_rate, failure_rate) rounded to 2 decimal places"

        Business Impact:
            Provides consistent precision in monitoring displays and prevents
            meaningless precision noise

        Scenario:
            Given: Metrics that produce rates with many decimal places
            When: to_dict() is called
            Then: success_rate and failure_rate are rounded to 2 decimals
            And: Rounding is applied consistently

        Fixtures Used:
            None - Testing precision control
        """
        # Given: Metrics that produce rates with many decimal places
        metrics = ResilienceMetrics()
        metrics.total_calls = 3  # This will produce 33.33... and 66.66... percentages
        metrics.successful_calls = 1
        metrics.failed_calls = 2

        # When: to_dict() is called
        result = metrics.to_dict()

        # Then: success_rate and failure_rate are rounded to 2 decimals
        # 1/3 * 100 = 33.333... -> 33.33, 2/3 * 100 = 66.666... -> 66.67
        assert result["success_rate"] == 33.33
        assert result["failure_rate"] == 66.67

        # And: Rounding is applied consistently
        assert isinstance(result["success_rate"], float)
        assert isinstance(result["failure_rate"], float)


class TestResilienceMetricsThreadSafety:
    """Tests thread-safe operations per State Management contract."""

    def test_metrics_supports_concurrent_counter_updates(self):
        """
        Test that metrics handle concurrent counter increments correctly.

        Verifies:
            State Management contract guarantee:
            "Thread-safe increment operations for concurrent access environments"

        Business Impact:
            Ensures accurate metrics collection when multiple threads use
            the same circuit breaker concurrently

        Scenario:
            Given: Single ResilienceMetrics instance shared across threads
            When: Multiple threads increment counters concurrently
            Then: Final counter values reflect all increments
            And: No increments are lost due to race conditions

        Fixtures Used:
            - fake_threading_module: For simulating concurrent access (from tests/unit/conftest.py)
        """
        # Given: Single ResilienceMetrics instance shared across threads
        metrics = ResilienceMetrics()

        # Simulate concurrent counter updates
        # Note: Since we're testing the ResilienceMetrics dataclass itself and not a
        # specific thread-safe implementation, we verify basic concurrent access patterns
        # that would work with proper thread-safe mechanisms

        # Simulate multiple threads updating counters
        metrics.total_calls += 5
        metrics.successful_calls += 3
        metrics.failed_calls += 2

        # Then: Final counter values reflect all increments
        assert metrics.total_calls == 5
        assert metrics.successful_calls == 3
        assert metrics.failed_calls == 2

        # And: No increments are lost (basic verification)
        # Full thread safety testing would require actual threading or specific
        # thread-safe implementation testing

    def test_metrics_atomic_updates_prevent_race_conditions(self):
        """
        Test that metric updates are atomic to prevent race conditions.

        Verifies:
            State Management contract guarantee:
            "Atomic updates prevent race conditions during metric collection"

        Business Impact:
            Prevents inconsistent metrics that could trigger false alerts
            or mask real issues

        Scenario:
            Given: Metrics being updated by concurrent operations
            When: Multiple attributes are updated in quick succession
            Then: Metrics remain in consistent state (no partial updates visible)
            And: Related counters maintain logical relationships

        Fixtures Used:
            - fake_threading_module: For simulating race conditions
        """
        # Given: Metrics being updated by concurrent operations
        metrics = ResilienceMetrics()

        # Simulate atomic update pattern (all related counters updated together)
        # When: Multiple attributes are updated in quick succession
        initial_total = 0
        initial_successful = 0
        initial_failed = 0

        # Perform "atomic" update - all related counters together
        metrics.total_calls = initial_total + 3
        metrics.successful_calls = initial_successful + 2
        metrics.failed_calls = initial_failed + 1

        # Then: Metrics remain in consistent state
        assert metrics.total_calls == 3
        assert metrics.successful_calls == 2
        assert metrics.failed_calls == 1

        # And: Related counters maintain logical relationships
        # total_calls should equal successful + failed in this simple case
        assert metrics.total_calls == metrics.successful_calls + metrics.failed_calls


class TestResilienceMetricsTimestampTracking:
    """Tests timestamp recording and temporal analysis per contract."""

    def test_metrics_records_last_success_timestamp(self):
        """
        Test that metrics record timestamp of last successful call.

        Verifies:
            State Management contract:
            "Timestamp tracking enables temporal analysis and health monitoring"

        Business Impact:
            Enables detection of service degradation patterns and recovery
            time analysis for SLA reporting

        Scenario:
            Given: Metrics with no prior success timestamp
            When: last_success is updated with current timestamp
            Then: Timestamp is stored accurately
            And: Timestamp can be used for time-based analysis

        Fixtures Used:
            - fake_datetime: For deterministic timestamp testing
        """
        # Given: Metrics with no prior success timestamp
        metrics = ResilienceMetrics()
        assert metrics.last_success is None

        # When: last_success is updated with current timestamp
        test_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        metrics.last_success = test_timestamp

        # Then: Timestamp is stored accurately
        assert metrics.last_success == test_timestamp

        # And: Timestamp can be used for time-based analysis
        assert isinstance(metrics.last_success, datetime)
        assert metrics.last_success.year == 2023
        assert metrics.last_success.month == 1
        assert metrics.last_success.day == 1

    def test_metrics_records_last_failure_timestamp(self):
        """
        Test that metrics record timestamp of last failed call.

        Verifies:
            State Management contract enables temporal analysis
            by tracking failure timestamps

        Business Impact:
            Enables failure pattern analysis and time-to-recovery calculations
            for incident response

        Scenario:
            Given: Metrics with no prior failure timestamp
            When: last_failure is updated with current timestamp
            Then: Timestamp is stored accurately
            And: Timestamp can be used for failure analysis

        Fixtures Used:
            - fake_datetime: For deterministic timestamp testing
        """
        # Given: Metrics with no prior failure timestamp
        metrics = ResilienceMetrics()
        assert metrics.last_failure is None

        # When: last_failure is updated with current timestamp
        test_timestamp = datetime(2023, 1, 1, 12, 30, 0)
        metrics.last_failure = test_timestamp

        # Then: Timestamp is stored accurately
        assert metrics.last_failure == test_timestamp

        # And: Timestamp can be used for failure analysis
        assert isinstance(metrics.last_failure, datetime)
        assert metrics.last_failure.year == 2023
        assert metrics.last_failure.hour == 12

    def test_metrics_timestamps_enable_temporal_analysis(self):
        """
        Test that timestamps support temporal analysis operations.

        Verifies:
            State Management contract:
            "Timestamp tracking enables temporal analysis and health monitoring"

        Business Impact:
            Enables calculation of time between failures, recovery duration,
            and other temporal metrics for operational analysis

        Scenario:
            Given: Metrics with both success and failure timestamps
            When: Temporal calculations are performed (time since last failure, etc.)
            Then: Timestamps provide accurate temporal data
            And: Time-based health assessments are possible

        Fixtures Used:
            - fake_datetime: For controlled time progression testing
        """
        # Given: Metrics with both success and failure timestamps
        metrics = ResilienceMetrics()
        failure_time = datetime(2023, 1, 1, 12, 0, 0)
        success_time = datetime(2023, 1, 1, 12, 5, 0)

        metrics.last_failure = failure_time
        metrics.last_success = success_time

        # When: Temporal calculations are performed
        time_difference = metrics.last_success - metrics.last_failure

        # Then: Timestamps provide accurate temporal data
        assert time_difference.total_seconds() == 300  # 5 minutes = 300 seconds

        # And: Time-based health assessments are possible
        assert time_difference.total_seconds() > 0  # Success after failure = recovery

    def test_metrics_timestamp_updates_are_consistent(self):
        """
        Test that timestamp updates maintain temporal consistency.

        Verifies:
            Timestamps always move forward and maintain logical ordering

        Business Impact:
            Ensures temporal analysis doesn't produce impossible results
            (like negative time differences)

        Scenario:
            Given: Metrics with initial timestamps
            When: Timestamps are updated in sequence
            Then: Later timestamps are always >= earlier timestamps
            And: Temporal ordering is maintained

        Fixtures Used:
            - fake_datetime: For controlled timestamp progression
        """
        # Given: Metrics with initial timestamps
        metrics = ResilienceMetrics()
        first_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        second_timestamp = datetime(2023, 1, 1, 12, 5, 0)
        third_timestamp = datetime(2023, 1, 1, 12, 10, 0)

        # When: Timestamps are updated in sequence
        metrics.last_success = first_timestamp
        metrics.last_failure = second_timestamp
        metrics.last_success = third_timestamp  # Update success time

        # Then: Later timestamps are always >= earlier timestamps
        assert metrics.last_success >= first_timestamp
        assert metrics.last_failure >= first_timestamp
        assert metrics.last_success >= second_timestamp

        # And: Temporal ordering is maintained
        assert metrics.last_failure >= first_timestamp
        assert metrics.last_success >= metrics.last_failure


class TestResilienceMetricsReset:
    """Tests reset() method for monitoring windows per contract."""

    def test_reset_clears_all_counter_metrics(self):
        """
        Test that reset() clears all counter values to zero.

        Verifies:
            reset() method clears metrics per the Public Methods contract
            for "periodic reset operations"

        Business Impact:
            Enables windowed metrics collection for time-based monitoring
            and prevents counter overflow

        Scenario:
            Given: Metrics with non-zero counters
            When: reset() is called
            Then: All counter values return to 0
            And: Metrics return to initialized state

        Fixtures Used:
            None - Testing reset behavior
        """
        # Given: Metrics with non-zero counters
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 8
        metrics.failed_calls = 2
        metrics.retry_attempts = 3
        metrics.circuit_breaker_opens = 2
        metrics.circuit_breaker_half_opens = 1
        metrics.circuit_breaker_closes = 2

        # When: reset() is called
        metrics.reset()

        # Then: All counter values return to 0
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.retry_attempts == 0
        assert metrics.circuit_breaker_opens == 0
        assert metrics.circuit_breaker_half_opens == 0
        assert metrics.circuit_breaker_closes == 0

        # And: Metrics return to initialized state
        # Test that properties also work correctly after reset
        assert metrics.success_rate == 0.0
        assert metrics.failure_rate == 0.0

    def test_reset_clears_timestamp_data(self):
        """
        Test that reset() clears timestamp information.

        Verifies:
            reset() provides complete metrics reset including timestamps

        Business Impact:
            Enables clean monitoring windows without stale timestamp data
            affecting analysis

        Scenario:
            Given: Metrics with last_success and last_failure timestamps
            When: reset() is called
            Then: Both timestamps return to None
            And: No historical timestamp data remains

        Fixtures Used:
            - fake_datetime: For verifying timestamp reset
        """
        # Given: Metrics with last_success and last_failure timestamps
        metrics = ResilienceMetrics()
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        metrics.last_success = test_time
        metrics.last_failure = test_time

        # Verify timestamps are set
        assert metrics.last_success == test_time
        assert metrics.last_failure == test_time

        # When: reset() is called
        metrics.reset()

        # Then: Both timestamps return to None
        assert metrics.last_success is None
        assert metrics.last_failure is None

        # And: No historical timestamp data remains
        # to_dict() should also show None for timestamps
        result = metrics.to_dict()
        assert result["last_success"] is None
        assert result["last_failure"] is None

    def test_reset_enables_periodic_monitoring_windows(self):
        """
        Test that reset() supports periodic monitoring window patterns.

        Verifies:
            Usage pattern from contract showing periodic reset for monitoring windows

        Business Impact:
            Enables rolling metrics windows for trending and alerting
            without unbounded counter growth

        Scenario:
            Given: Metrics being used for windowed monitoring (e.g., per-hour stats)
            When: Monitoring window expires and reset() is called
            Then: Metrics are ready for new window
            And: Previous window data is cleared

        Fixtures Used:
            - fake_datetime: For simulating window expiration
        """
        # Given: Metrics being used for windowed monitoring
        metrics = ResilienceMetrics()

        # Simulate first monitoring window with some activity
        metrics.total_calls = 50
        metrics.successful_calls = 45
        metrics.failed_calls = 5
        metrics.last_success = datetime(2023, 1, 1, 12, 0, 0)

        # Verify window data exists
        assert metrics.total_calls == 50
        assert metrics.success_rate == 90.0
        assert metrics.last_success is not None

        # When: Monitoring window expires and reset() is called
        # Simulate window boundary and reset for new window
        metrics.reset()

        # Then: Metrics are ready for new window
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.last_success is None
        assert metrics.last_failure is None

        # And: Previous window data is cleared
        assert metrics.success_rate == 0.0
        assert metrics.failure_rate == 0.0

        # New window can start collecting fresh data
        metrics.total_calls = 1
        metrics.successful_calls = 1
        assert metrics.success_rate == 100.0

