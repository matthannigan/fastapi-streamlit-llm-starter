"""
Test suite for ScanMetrics dataclass tracking security scan performance.

This module tests the ScanMetrics dataclass that accumulates comprehensive
performance and operational statistics about security scanning operations
including scan counts, timing data, success rates, and violation detection.

Test Strategy:
    - Verify initialization with default zero values
    - Test update() method for metric accumulation
    - Validate average scan time calculation logic
    - Test reset() method for clearing accumulated data
    - Verify metric integrity across multiple updates
"""

import pytest
from app.infrastructure.security.llm.protocol import ScanMetrics


class TestScanMetricsInitialization:
    """
    Test suite for ScanMetrics initialization and default values.
    
    Scope:
        - Default initialization with all counters at zero
        - Field accessibility and type correctness
        - Initial state for new metrics tracking
        
    Business Critical:
        Proper metrics initialization ensures accurate performance
        tracking from the start of security service operation.
        
    Test Coverage:
        - All counter fields start at zero
        - Average scan time starts at 0.0
        - Metrics are ready for immediate updates
    """
    
    def test_scan_metrics_initializes_with_zero_scan_count(self):
        """
        Test that ScanMetrics initializes with scan_count of 0.

        Verifies:
            New metrics instance starts with zero total scans per contract

        Business Impact:
            Ensures accurate scan counting from service startup without
            inheriting stale data from previous runs

        Scenario:
            Given: No parameters provided to ScanMetrics
            When: Creating new ScanMetrics instance
            Then: scan_count equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: No parameters provided to ScanMetrics
        # When: Creating new ScanMetrics instance
        metrics = ScanMetrics()

        # Then: scan_count equals 0
        assert metrics.scan_count == 0
    
    def test_scan_metrics_initializes_with_zero_total_scan_time(self):
        """
        Test that ScanMetrics initializes with total_scan_time_ms of 0.

        Verifies:
            New metrics instance starts with zero cumulative scan time

        Business Impact:
            Enables accurate performance tracking from first scan without
            contamination from previous data

        Scenario:
            Given: New ScanMetrics instance
            When: Accessing total_scan_time_ms
            Then: Value equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: New ScanMetrics instance
        metrics = ScanMetrics()

        # When: Accessing total_scan_time_ms
        # Then: Value equals 0
        assert metrics.total_scan_time_ms == 0
    
    def test_scan_metrics_initializes_with_zero_successful_scans(self):
        """
        Test that ScanMetrics initializes with successful_scans of 0.

        Verifies:
            Success counter starts at zero per contract requirements

        Business Impact:
            Ensures accurate success rate calculation from service startup

        Scenario:
            Given: New ScanMetrics instance
            When: Accessing successful_scans
            Then: Value equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: New ScanMetrics instance
        metrics = ScanMetrics()

        # When: Accessing successful_scans
        # Then: Value equals 0
        assert metrics.successful_scans == 0
    
    def test_scan_metrics_initializes_with_zero_failed_scans(self):
        """
        Test that ScanMetrics initializes with failed_scans of 0.

        Verifies:
            Failure counter starts at zero per contract requirements

        Business Impact:
            Enables accurate failure rate tracking and alerting thresholds

        Scenario:
            Given: New ScanMetrics instance
            When: Accessing failed_scans
            Then: Value equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: New ScanMetrics instance
        metrics = ScanMetrics()

        # When: Accessing failed_scans
        # Then: Value equals 0
        assert metrics.failed_scans == 0

    def test_scan_metrics_initializes_with_zero_violations_detected(self):
        """
        Test that ScanMetrics initializes with violations_detected of 0.

        Verifies:
            Violation detection counter starts at zero

        Business Impact:
            Ensures accurate threat detection statistics from startup

        Scenario:
            Given: New ScanMetrics instance
            When: Accessing violations_detected
            Then: Value equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: New ScanMetrics instance
        metrics = ScanMetrics()

        # When: Accessing violations_detected
        # Then: Value equals 0
        assert metrics.violations_detected == 0

    def test_scan_metrics_initializes_with_zero_average_scan_time(self):
        """
        Test that ScanMetrics initializes with average_scan_time_ms of 0.0.

        Verifies:
            Average scan time starts at 0.0 when no scans recorded

        Business Impact:
            Prevents undefined average calculations before first scan

        Scenario:
            Given: New ScanMetrics instance
            When: Accessing average_scan_time_ms
            Then: Value equals 0.0 (float)

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: New ScanMetrics instance
        metrics = ScanMetrics()

        # When: Accessing average_scan_time_ms
        # Then: Value equals 0.0 (float)
        assert metrics.average_scan_time_ms == 0.0


class TestScanMetricsUpdate:
    """
    Test suite for ScanMetrics update() method for metric accumulation.
    
    Scope:
        - Scan count increment per update
        - Total scan time accumulation
        - Success/failure counter updates
        - Violations detected tracking
        - Average scan time recalculation
        - Multiple sequential updates
        
    Business Critical:
        Accurate metric updates drive performance monitoring, alerting,
        and capacity planning for security infrastructure.
        
    Test Coverage:
        - Single update with various parameters
        - Multiple sequential updates
        - Success and failure tracking
        - Average calculation correctness
        - Edge cases (zero values, large numbers)
    """
    
    def test_scan_metrics_update_increments_scan_count(self):
        """
        Test that update() increments scan_count by 1.

        Verifies:
            Each update call increments total scan count per contract

        Business Impact:
            Ensures accurate tracking of total scan volume for capacity
            planning and performance analysis

        Scenario:
            Given: ScanMetrics with scan_count = 0
            When: Calling update(scan_duration_ms=50, violations_count=0, success=True)
            Then: scan_count equals 1

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with scan_count = 0
        metrics = ScanMetrics()
        assert metrics.scan_count == 0

        # When: Calling update(scan_duration_ms=50, violations_count=0, success=True)
        metrics.update(scan_duration_ms=50, violations_count=0, success=True)

        # Then: scan_count equals 1
        assert metrics.scan_count == 1
    
    def test_scan_metrics_update_adds_scan_duration_to_total_time(self):
        """
        Test that update() accumulates scan duration to total_scan_time_ms.

        Verifies:
            Scan durations are added to cumulative total per contract

        Business Impact:
            Enables total processing time tracking for cost analysis
            and resource utilization monitoring

        Scenario:
            Given: ScanMetrics with total_scan_time_ms = 0
            When: Calling update(scan_duration_ms=100, violations_count=0, success=True)
            Then: total_scan_time_ms equals 100

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with total_scan_time_ms = 0
        metrics = ScanMetrics()
        assert metrics.total_scan_time_ms == 0

        # When: Calling update(scan_duration_ms=100, violations_count=0, success=True)
        metrics.update(scan_duration_ms=100, violations_count=0, success=True)

        # Then: total_scan_time_ms equals 100
        assert metrics.total_scan_time_ms == 100

    def test_scan_metrics_update_increments_successful_scans_on_success(self):
        """
        Test that update() increments successful_scans when success=True.

        Verifies:
            Success parameter controls successful_scans counter per contract

        Business Impact:
            Enables success rate calculation and reliability monitoring

        Scenario:
            Given: ScanMetrics with successful_scans = 0
            When: Calling update(scan_duration_ms=50, violations_count=0, success=True)
            Then: successful_scans equals 1
            And: failed_scans remains 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with successful_scans = 0
        metrics = ScanMetrics()
        assert metrics.successful_scans == 0
        assert metrics.failed_scans == 0

        # When: Calling update(scan_duration_ms=50, violations_count=0, success=True)
        metrics.update(scan_duration_ms=50, violations_count=0, success=True)

        # Then: successful_scans equals 1
        # And: failed_scans remains 0
        assert metrics.successful_scans == 1
        assert metrics.failed_scans == 0

    def test_scan_metrics_update_increments_failed_scans_on_failure(self):
        """
        Test that update() increments failed_scans when success=False.

        Verifies:
            Failure tracking operates independently of success tracking

        Business Impact:
            Enables failure rate monitoring and alerting for service
            health and reliability

        Scenario:
            Given: ScanMetrics with failed_scans = 0
            When: Calling update(scan_duration_ms=100, violations_count=0, success=False)
            Then: failed_scans equals 1
            And: successful_scans remains 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with failed_scans = 0
        metrics = ScanMetrics()
        assert metrics.failed_scans == 0
        assert metrics.successful_scans == 0

        # When: Calling update(scan_duration_ms=100, violations_count=0, success=False)
        metrics.update(scan_duration_ms=100, violations_count=0, success=False)

        # Then: failed_scans equals 1
        # And: successful_scans remains 0
        assert metrics.failed_scans == 1
        assert metrics.successful_scans == 0

    def test_scan_metrics_update_adds_violations_count_to_total(self):
        """
        Test that update() accumulates violations_count to violations_detected.

        Verifies:
            Violation counts are summed across all scans per contract

        Business Impact:
            Tracks total threat detection volume for security analytics
            and trend analysis

        Scenario:
            Given: ScanMetrics with violations_detected = 0
            When: Calling update(scan_duration_ms=50, violations_count=3, success=True)
            Then: violations_detected equals 3

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with violations_detected = 0
        metrics = ScanMetrics()
        assert metrics.violations_detected == 0

        # When: Calling update(scan_duration_ms=50, violations_count=3, success=True)
        metrics.update(scan_duration_ms=50, violations_count=3, success=True)

        # Then: violations_detected equals 3
        assert metrics.violations_detected == 3

    def test_scan_metrics_update_recalculates_average_scan_time(self):
        """
        Test that update() recalculates average_scan_time_ms correctly.

        Verifies:
            Average is computed as total_scan_time_ms / scan_count per
            documented formula

        Business Impact:
            Provides real-time average performance metric for SLA
            monitoring and performance optimization

        Scenario:
            Given: ScanMetrics with one scan (duration=100ms)
            When: Adding second scan (duration=50ms) via update()
            Then: average_scan_time_ms equals 75.0 (150ms / 2 scans)

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with one scan (duration=100ms)
        metrics = ScanMetrics()
        metrics.update(scan_duration_ms=100, violations_count=1, success=True)
        assert metrics.scan_count == 1
        assert metrics.total_scan_time_ms == 100
        assert metrics.average_scan_time_ms == 100.0

        # When: Adding second scan (duration=50ms) via update()
        metrics.update(scan_duration_ms=50, violations_count=0, success=True)

        # Then: average_scan_time_ms equals 75.0 (150ms / 2 scans)
        assert metrics.scan_count == 2
        assert metrics.total_scan_time_ms == 150
        assert metrics.average_scan_time_ms == 75.0
    
    def test_scan_metrics_update_handles_multiple_sequential_updates(self):
        """
        Test that update() correctly accumulates metrics across multiple calls.

        Verifies:
            Metrics remain accurate through repeated update operations

        Business Impact:
            Ensures reliable long-term performance tracking without
            metric drift or accumulation errors

        Scenario:
            Given: New ScanMetrics instance
            When: Calling update() multiple times with varying parameters
            Then: All counters reflect cumulative totals correctly
            And: Average scan time reflects all scans

        Fixtures Used:
            None - Direct dataclass testing

        Edge Cases Covered:
            - 3 successful scans with different durations
            - 2 failed scans mixed with successful ones
            - Various violation counts (0, 1, 5)
        """
        # Given: New ScanMetrics instance
        metrics = ScanMetrics()

        # When: Calling update() multiple times with varying parameters
        # Scan 1: Successful, 50ms, 1 violation
        metrics.update(scan_duration_ms=50, violations_count=1, success=True)

        # Scan 2: Successful, 75ms, 0 violations
        metrics.update(scan_duration_ms=75, violations_count=0, success=True)

        # Scan 3: Failed, 100ms, 0 violations
        metrics.update(scan_duration_ms=100, violations_count=0, success=False)

        # Scan 4: Successful, 25ms, 5 violations
        metrics.update(scan_duration_ms=25, violations_count=5, success=True)

        # Scan 5: Failed, 150ms, 2 violations
        metrics.update(scan_duration_ms=150, violations_count=2, success=False)

        # Then: All counters reflect cumulative totals correctly
        assert metrics.scan_count == 5
        assert metrics.total_scan_time_ms == 400  # 50 + 75 + 100 + 25 + 150
        assert metrics.successful_scans == 3
        assert metrics.failed_scans == 2
        assert metrics.violations_detected == 8  # 1 + 0 + 0 + 5 + 2

        # And: Average scan time reflects all scans
        assert metrics.average_scan_time_ms == 80.0  # 400ms / 5 scans

    def test_scan_metrics_update_accepts_zero_violations_count(self):
        """
        Test that update() accepts violations_count=0 for safe content scans.

        Verifies:
            Zero violations is valid input representing safe content per
            contract requirements

        Business Impact:
            Ensures metrics accurately reflect safe content processing
            without artificially inflating violation statistics

        Scenario:
            Given: ScanMetrics instance
            When: Calling update(scan_duration_ms=50, violations_count=0, success=True)
            Then: Update succeeds without errors
            And: violations_detected remains unchanged

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics instance
        metrics = ScanMetrics()
        initial_violations = metrics.violations_detected

        # When: Calling update(scan_duration_ms=50, violations_count=0, success=True)
        metrics.update(scan_duration_ms=50, violations_count=0, success=True)

        # Then: Update succeeds without errors
        # And: violations_detected remains unchanged (still 0)
        assert metrics.violations_detected == initial_violations
        assert metrics.scan_count == 1
        assert metrics.successful_scans == 1

    def test_scan_metrics_update_tracks_success_and_failure_independently(self):
        """
        Test that update() maintains independent success/failure counters.

        Verifies:
            Success and failure tracking are mutually exclusive but both
            contribute to total scan count

        Business Impact:
            Enables accurate success rate calculation: successful_scans / scan_count

        Scenario:
            Given: ScanMetrics with mixed successful and failed scans
            When: Recording both successes and failures
            Then: successful_scans + failed_scans equals scan_count
            And: Both counters are independently accurate

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with mixed successful and failed scans
        metrics = ScanMetrics()

        # When: Recording both successes and failures
        # Record 2 successful scans
        metrics.update(scan_duration_ms=30, violations_count=1, success=True)
        metrics.update(scan_duration_ms=45, violations_count=0, success=True)

        # Record 1 failed scan
        metrics.update(scan_duration_ms=60, violations_count=0, success=False)

        # Then: successful_scans + failed_scans equals scan_count
        assert metrics.successful_scans + metrics.failed_scans == metrics.scan_count

        # And: Both counters are independently accurate
        assert metrics.successful_scans == 2
        assert metrics.failed_scans == 1
        assert metrics.scan_count == 3


class TestScanMetricsReset:
    """
    Test suite for ScanMetrics reset() method for clearing accumulated data.
    
    Scope:
        - All counter fields reset to zero
        - Average scan time reset to 0.0
        - Complete state restoration to initial values
        - Reset after various accumulated metrics
        
    Business Critical:
        Reset functionality enables clean metric collection periods for
        testing, monitoring windows, and service maintenance.
        
    Test Coverage:
        - Reset from initial state
        - Reset after single update
        - Reset after multiple updates
        - All fields return to zero state
    """
    
    def test_scan_metrics_reset_clears_scan_count_to_zero(self):
        """
        Test that reset() sets scan_count back to 0.

        Verifies:
            Total scan count is cleared by reset per contract

        Business Impact:
            Enables fresh metric collection periods without creating
            new metrics instances

        Scenario:
            Given: ScanMetrics with scan_count = 10
            When: Calling reset()
            Then: scan_count equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with scan_count = 10
        metrics = ScanMetrics()
        # Accumulate some scans first
        for i in range(10):
            metrics.update(scan_duration_ms=50, violations_count=0, success=True)
        assert metrics.scan_count == 10

        # When: Calling reset()
        metrics.reset()

        # Then: scan_count equals 0
        assert metrics.scan_count == 0
    
    def test_scan_metrics_reset_clears_total_scan_time_to_zero(self):
        """
        Test that reset() sets total_scan_time_ms back to 0.

        Verifies:
            Cumulative time tracking is cleared by reset

        Business Impact:
            Ensures clean timing statistics for new measurement periods

        Scenario:
            Given: ScanMetrics with total_scan_time_ms = 5000
            When: Calling reset()
            Then: total_scan_time_ms equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with total_scan_time_ms = 5000
        metrics = ScanMetrics()
        # Accumulate some scan time
        for i in range(10):
            metrics.update(scan_duration_ms=500, violations_count=0, success=True)
        assert metrics.total_scan_time_ms == 5000

        # When: Calling reset()
        metrics.reset()

        # Then: total_scan_time_ms equals 0
        assert metrics.total_scan_time_ms == 0

    def test_scan_metrics_reset_clears_successful_scans_to_zero(self):
        """
        Test that reset() sets successful_scans back to 0.

        Verifies:
            Success counter is cleared by reset per contract

        Business Impact:
            Enables fresh success rate tracking for new time periods

        Scenario:
            Given: ScanMetrics with successful_scans = 8
            When: Calling reset()
            Then: successful_scans equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with successful_scans = 8
        metrics = ScanMetrics()
        # Accumulate some successful scans
        for i in range(8):
            metrics.update(scan_duration_ms=50, violations_count=0, success=True)
        assert metrics.successful_scans == 8

        # When: Calling reset()
        metrics.reset()

        # Then: successful_scans equals 0
        assert metrics.successful_scans == 0

    def test_scan_metrics_reset_clears_failed_scans_to_zero(self):
        """
        Test that reset() sets failed_scans back to 0.

        Verifies:
            Failure counter is cleared by reset per contract

        Business Impact:
            Enables fresh failure rate tracking without stale data

        Scenario:
            Given: ScanMetrics with failed_scans = 2
            When: Calling reset()
            Then: failed_scans equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with failed_scans = 2
        metrics = ScanMetrics()
        # Add some successful and failed scans
        for i in range(5):
            metrics.update(scan_duration_ms=50, violations_count=0, success=True)
        for i in range(2):
            metrics.update(scan_duration_ms=75, violations_count=0, success=False)
        assert metrics.failed_scans == 2

        # When: Calling reset()
        metrics.reset()

        # Then: failed_scans equals 0
        assert metrics.failed_scans == 0

    def test_scan_metrics_reset_clears_violations_detected_to_zero(self):
        """
        Test that reset() sets violations_detected back to 0.

        Verifies:
            Violation detection tracking is cleared by reset

        Business Impact:
            Enables fresh threat detection statistics for new periods

        Scenario:
            Given: ScanMetrics with violations_detected = 15
            When: Calling reset()
            Then: violations_detected equals 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with violations_detected = 15
        metrics = ScanMetrics()
        # Accumulate some violations
        metrics.update(scan_duration_ms=50, violations_count=5, success=True)
        metrics.update(scan_duration_ms=75, violations_count=10, success=True)
        assert metrics.violations_detected == 15

        # When: Calling reset()
        metrics.reset()

        # Then: violations_detected equals 0
        assert metrics.violations_detected == 0

    def test_scan_metrics_reset_clears_average_scan_time_to_zero(self):
        """
        Test that reset() sets average_scan_time_ms back to 0.0.

        Verifies:
            Average calculation is cleared by reset per contract

        Business Impact:
            Prevents stale average values from confusing new period metrics

        Scenario:
            Given: ScanMetrics with average_scan_time_ms = 125.5
            When: Calling reset()
            Then: average_scan_time_ms equals 0.0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with average_scan_time_ms = 125.5
        metrics = ScanMetrics()
        # Accumulate some scans to get an average
        for i in range(4):
            metrics.update(scan_duration_ms=125, violations_count=0, success=True)
        assert metrics.average_scan_time_ms == 125.0

        # When: Calling reset()
        metrics.reset()

        # Then: average_scan_time_ms equals 0.0
        assert metrics.average_scan_time_ms == 0.0
    
    def test_scan_metrics_reset_returns_to_initial_state(self):
        """
        Test that reset() returns metrics to exact initial state.

        Verifies:
            After reset, metrics match newly created ScanMetrics instance

        Business Impact:
            Ensures complete state cleanup for reliable metric restart

        Scenario:
            Given: ScanMetrics with various accumulated metrics
            When: Calling reset()
            Then: All fields match new ScanMetrics() initial values
            And: Instance is ready for fresh metric accumulation

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with various accumulated metrics
        metrics = ScanMetrics()
        # Accumulate various metrics
        metrics.update(scan_duration_ms=100, violations_count=3, success=True)
        metrics.update(scan_duration_ms=75, violations_count=0, success=False)
        metrics.update(scan_duration_ms=150, violations_count=1, success=True)

        # When: Calling reset()
        metrics.reset()

        # Then: All fields match new ScanMetrics() initial values
        fresh_metrics = ScanMetrics()
        assert metrics.scan_count == fresh_metrics.scan_count
        assert metrics.total_scan_time_ms == fresh_metrics.total_scan_time_ms
        assert metrics.successful_scans == fresh_metrics.successful_scans
        assert metrics.failed_scans == fresh_metrics.failed_scans
        assert metrics.violations_detected == fresh_metrics.violations_detected
        assert metrics.average_scan_time_ms == fresh_metrics.average_scan_time_ms

        # And: Instance is ready for fresh metric accumulation
        metrics.update(scan_duration_ms=50, violations_count=1, success=True)
        assert metrics.scan_count == 1
        assert metrics.average_scan_time_ms == 50.0

    def test_scan_metrics_reset_can_be_called_multiple_times(self):
        """
        Test that reset() can be called repeatedly without errors.

        Verifies:
            Reset is idempotent and safe to call on already-reset metrics

        Business Impact:
            Prevents errors from redundant reset calls in complex
            monitoring workflows

        Scenario:
            Given: ScanMetrics already at zero state
            When: Calling reset() again
            Then: No errors occur
            And: All fields remain at zero

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics already at zero state
        metrics = ScanMetrics()
        metrics.reset()  # First reset

        # When: Calling reset() again
        metrics.reset()  # Second reset
        metrics.reset()  # Third reset - should still work

        # Then: No errors occur
        # And: All fields remain at zero
        assert metrics.scan_count == 0
        assert metrics.total_scan_time_ms == 0
        assert metrics.successful_scans == 0
        assert metrics.failed_scans == 0
        assert metrics.violations_detected == 0
        assert metrics.average_scan_time_ms == 0.0

    def test_scan_metrics_reset_followed_by_update_works_correctly(self):
        """
        Test that metrics can be updated normally after reset.

        Verifies:
            Reset doesn't corrupt metrics, allowing normal operation to resume

        Business Impact:
            Ensures reset operation doesn't break metric tracking,
            enabling reliable periodic resets

        Scenario:
            Given: ScanMetrics with accumulated data, then reset
            When: Calling update() after reset
            Then: Metrics accumulate correctly from zero
            And: All counters and averages compute properly

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with accumulated data, then reset
        metrics = ScanMetrics()
        # Accumulate some data first
        metrics.update(scan_duration_ms=200, violations_count=5, success=True)
        metrics.update(scan_duration_ms=100, violations_count=2, success=False)
        assert metrics.scan_count == 2

        # Reset the metrics
        metrics.reset()
        assert metrics.scan_count == 0

        # When: Calling update() after reset
        metrics.update(scan_duration_ms=75, violations_count=1, success=True)

        # Then: Metrics accumulate correctly from zero
        assert metrics.scan_count == 1
        assert metrics.total_scan_time_ms == 75
        assert metrics.successful_scans == 1
        assert metrics.failed_scans == 0
        assert metrics.violations_detected == 1

        # And: All counters and averages compute properly
        assert metrics.average_scan_time_ms == 75.0

        # Add another update to verify continued normal operation
        metrics.update(scan_duration_ms=125, violations_count=0, success=True)
        assert metrics.scan_count == 2
        assert metrics.total_scan_time_ms == 200  # 75 + 125
        assert metrics.successful_scans == 2
        assert metrics.violations_detected == 1
        assert metrics.average_scan_time_ms == 100.0  # 200ms / 2 scans

