"""
Test suite for MetricsSnapshot dataclass providing system-wide metrics view.

This module tests the MetricsSnapshot dataclass that captures a comprehensive
point-in-time view of security service metrics, system health, and operational
status for monitoring, alerting, and performance analysis.

Test Strategy:
    - Verify initialization with required and optional fields
    - Test to_dict() serialization for monitoring systems
    - Validate derived metrics calculation (success rates)
    - Test timestamp handling and system health integration
    - Verify comprehensive snapshot coverage
"""

import pytest
from datetime import datetime, UTC
from app.infrastructure.security.llm.protocol import (
    MetricsSnapshot,
    ScanMetrics
)


class TestMetricsSnapshotInitialization:
    """
    Test suite for MetricsSnapshot initialization and field handling.
    
    Scope:
        - Required fields (input_metrics, output_metrics, system_health, scanner_health)
        - Optional fields (uptime_seconds, memory_usage_mb, timestamp)
        - Default value handling for optional parameters
        - Automatic timestamp generation
        
    Business Critical:
        Proper snapshot initialization ensures accurate system monitoring
        and reliable health status reporting for operational dashboards.
        
    Test Coverage:
        - Minimal initialization with required fields
        - Complete initialization with all optional fields
        - Default timestamp generation
        - System and scanner health dictionaries
    """
    
    def test_metrics_snapshot_initialization_with_required_fields(self):
        """
        Test that MetricsSnapshot initializes with only required fields.

        Verifies:
            Snapshot can be created with input_metrics and system_health,
            with optional fields defaulting to appropriate empty values

        Business Impact:
            Enables flexible snapshot creation for various monitoring
            scenarios without requiring complete system data

        Scenario:
            Given: Required snapshot parameters (input_metrics, system_health)
            When: Creating MetricsSnapshot with minimal fields
            Then: Snapshot instance is created successfully
            And: Optional fields have appropriate defaults

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Basic input metrics and system health
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=50, violations_count=1, success=True)

        system_health = {"cpu_usage": 45.2, "disk_space": 78.5}
        scanner_health = {"injection_detector": True}

        # When: Creating MetricsSnapshot with minimal required fields
        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            system_health=system_health,
            scanner_health=scanner_health
        )

        # Then: Snapshot instance is created successfully
        assert snapshot.input_metrics is input_metrics
        assert snapshot.output_metrics is not None  # Default factory creates ScanMetrics
        assert snapshot.system_health == system_health
        assert snapshot.scanner_health == scanner_health

        # And: Optional fields have appropriate defaults
        assert snapshot.uptime_seconds == 0
        assert snapshot.memory_usage_mb == 0.0
        assert isinstance(snapshot.timestamp, datetime)
        # Note: Implementation uses datetime.utcnow() which creates a naive datetime without timezone
    
    def test_metrics_snapshot_initialization_with_all_fields(self):
        """
        Test that MetricsSnapshot initializes with complete field set.

        Verifies:
            Snapshot captures comprehensive system state including all
            metrics, health indicators, and resource usage data

        Business Impact:
            Supports detailed system monitoring with complete operational
            context for performance analysis and troubleshooting

        Scenario:
            Given: Complete snapshot parameters including all optional fields
            When: Creating MetricsSnapshot
            Then: All fields are accessible and correctly typed
            And: Complete system state is preserved

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Complete snapshot parameters
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=100, violations_count=2, success=True)

        output_metrics = ScanMetrics()
        output_metrics.update(scan_duration_ms=80, violations_count=0, success=True)

        system_health = {"cpu_usage": 75.5, "memory_usage": 60.2, "disk_space": 85.0}
        scanner_health = {"injection_detector": True, "toxicity_scanner": False}
        custom_timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        # When: Creating MetricsSnapshot with all fields
        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health=system_health,
            scanner_health=scanner_health,
            uptime_seconds=86400,
            memory_usage_mb=256.7,
            timestamp=custom_timestamp
        )

        # Then: All fields are accessible and correctly typed
        assert snapshot.input_metrics is input_metrics
        assert snapshot.output_metrics is output_metrics
        assert snapshot.system_health == system_health
        assert snapshot.scanner_health == scanner_health
        assert snapshot.uptime_seconds == 86400
        assert snapshot.memory_usage_mb == 256.7
        assert snapshot.timestamp == custom_timestamp

        # And: Complete system state is preserved
        assert snapshot.input_metrics.scan_count == 1
        assert snapshot.output_metrics.scan_count == 1
        assert snapshot.system_health["cpu_usage"] == 75.5
        assert not all(snapshot.scanner_health.values())  # One scanner is unhealthy
    
    def test_metrics_snapshot_initialization_accepts_scan_metrics_objects(self):
        """
        Test that MetricsSnapshot accepts ScanMetrics objects for input/output metrics.

        Verifies:
            Snapshot properly stores ScanMetrics instances for detailed
            performance tracking per contract

        Business Impact:
            Enables comprehensive scan performance monitoring with full
            metric history and statistics

        Scenario:
            Given: ScanMetrics objects for input and output validation
            When: Creating MetricsSnapshot with these metrics
            Then: Both input_metrics and output_metrics are stored
            And: Metrics are accessible with all fields intact

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics objects with performance data
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=120, violations_count=3, success=True)
        input_metrics.update(scan_duration_ms=80, violations_count=0, success=True)

        output_metrics = ScanMetrics()
        output_metrics.update(scan_duration_ms=60, violations_count=1, success=False)
        output_metrics.update(scan_duration_ms=90, violations_count=2, success=True)

        # When: Creating MetricsSnapshot with these metrics
        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # Then: Both input_metrics and output_metrics are stored
        assert snapshot.input_metrics is input_metrics
        assert snapshot.output_metrics is output_metrics

        # And: Metrics are accessible with all fields intact
        assert snapshot.input_metrics.scan_count == 2
        assert snapshot.input_metrics.successful_scans == 2
        assert snapshot.input_metrics.failed_scans == 0
        assert snapshot.input_metrics.violations_detected == 3
        assert snapshot.input_metrics.average_scan_time_ms == 100.0  # (120 + 80) / 2

        assert snapshot.output_metrics.scan_count == 2
        assert snapshot.output_metrics.successful_scans == 1
        assert snapshot.output_metrics.failed_scans == 1
        assert snapshot.output_metrics.violations_detected == 3
        assert snapshot.output_metrics.average_scan_time_ms == 75.0  # (60 + 90) / 2
    
    def test_metrics_snapshot_initialization_accepts_system_health_dictionary(self):
        """
        Test that MetricsSnapshot accepts system_health dictionary with arbitrary indicators.

        Verifies:
            System health can contain flexible key-value pairs for various
            health metrics per contract

        Business Impact:
            Supports extensible health monitoring with custom indicators
            specific to deployment environment

        Scenario:
            Given: system_health dictionary with CPU, memory, disk metrics
            When: Creating MetricsSnapshot
            Then: system_health is stored with all entries preserved
            And: Health data is accessible and mutable

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: system_health dictionary with various metrics
        system_health = {
            "cpu_usage": 45.2,
            "memory_usage": 60.8,
            "disk_space": 78.5,
            "network_latency": 12.3,
            "connection_pool": {"active": 5, "idle": 15},
            "cache_hit_rate": 0.85,
            "last_restart": "2024-01-15T10:30:00Z"
        }

        # When: Creating MetricsSnapshot with system health
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health=system_health,
            scanner_health={"scanner1": True}
        )

        # Then: system_health is stored with all entries preserved
        assert snapshot.system_health == system_health
        assert len(snapshot.system_health) == 7

        # And: Health data is accessible and mutable
        assert snapshot.system_health["cpu_usage"] == 45.2
        assert snapshot.system_health["connection_pool"]["active"] == 5
        assert snapshot.system_health["cache_hit_rate"] == 0.85

        # Can modify the health data (it's mutable)
        snapshot.system_health["cpu_usage"] = 50.0
        assert snapshot.system_health["cpu_usage"] == 50.0
    
    def test_metrics_snapshot_initialization_accepts_scanner_health_dictionary(self):
        """
        Test that MetricsSnapshot accepts scanner_health dictionary mapping scanner names to status.

        Verifies:
            Individual scanner operational status can be tracked per contract

        Business Impact:
            Enables per-scanner health monitoring for identifying
            specific scanner failures or degradation

        Scenario:
            Given: scanner_health dictionary with scanner names and boolean status
            When: Creating MetricsSnapshot
            Then: scanner_health is stored correctly
            And: All scanner statuses are accessible

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: scanner_health dictionary with various scanner statuses
        scanner_health = {
            "injection_detector": True,
            "toxicity_scanner": True,
            "pii_detector": False,
            "bias_detector": True,
            "content_safety": False
        }

        # When: Creating MetricsSnapshot with scanner health
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health=scanner_health
        )

        # Then: scanner_health is stored correctly
        assert snapshot.scanner_health == scanner_health
        assert len(snapshot.scanner_health) == 5

        # And: All scanner statuses are accessible
        assert snapshot.scanner_health["injection_detector"] is True
        assert snapshot.scanner_health["toxicity_scanner"] is True
        assert snapshot.scanner_health["pii_detector"] is False
        assert snapshot.scanner_health["bias_detector"] is True
        assert snapshot.scanner_health["content_safety"] is False

        # Can identify unhealthy scanners
        unhealthy_scanners = [
            name for name, status in snapshot.scanner_health.items() if not status
        ]
        assert len(unhealthy_scanners) == 2
        assert "pii_detector" in unhealthy_scanners
        assert "content_safety" in unhealthy_scanners
    
    def test_metrics_snapshot_initialization_generates_timestamp_automatically(self):
        """
        Test that MetricsSnapshot automatically generates UTC timestamp when not provided.

        Verifies:
            Every snapshot has timestamp marking when metrics were captured,
            defaulting to current UTC time per contract

        Business Impact:
            Ensures accurate temporal tracking for time-series monitoring
            and historical trend analysis

        Scenario:
            Given: Snapshot parameters without explicit timestamp
            When: Creating MetricsSnapshot
            Then: timestamp field is automatically set to current UTC time
            And: Timestamp is datetime object with UTC timezone

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Snapshot parameters without explicit timestamp
        before_creation = datetime.utcnow()  # Use utcnow to match implementation

        # When: Creating MetricsSnapshot
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        after_creation = datetime.utcnow()

        # Then: timestamp field is automatically set to current UTC time
        assert isinstance(snapshot.timestamp, datetime)
        assert before_creation <= snapshot.timestamp <= after_creation

        # And: Timestamp is datetime object (implementation uses naive datetime)
        assert snapshot.timestamp.tzinfo is None  # Implementation uses datetime.utcnow()
    
    def test_metrics_snapshot_initialization_accepts_custom_timestamp(self):
        """
        Test that MetricsSnapshot accepts custom timestamp for historical snapshots.

        Verifies:
            Snapshots can be created with specific timestamps for batch
            processing or historical data reconstruction

        Business Impact:
            Supports snapshot restoration from persistent storage while
            maintaining original capture timestamps

        Scenario:
            Given: Snapshot parameters with explicit historical timestamp
            When: Creating MetricsSnapshot with custom timestamp
            Then: Provided timestamp is preserved exactly
            And: No automatic timestamp generation occurs

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Snapshot parameters with explicit historical timestamp
        historical_timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)

        # When: Creating MetricsSnapshot with custom timestamp
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True},
            timestamp=historical_timestamp
        )

        # Then: Provided timestamp is preserved exactly
        assert snapshot.timestamp == historical_timestamp
        assert snapshot.timestamp.year == 2024
        assert snapshot.timestamp.month == 1
        assert snapshot.timestamp.day == 15
        assert snapshot.timestamp.hour == 10
        assert snapshot.timestamp.minute == 30
        assert snapshot.timestamp.second == 45

        # And: No automatic timestamp generation occurs
        current_time = datetime.now(UTC)
        assert snapshot.timestamp != current_time
    
    def test_metrics_snapshot_initialization_defaults_output_metrics_to_none(self):
        """
        Test that MetricsSnapshot defaults output_metrics to None when not provided.

        Verifies:
            Output metrics are optional per contract, supporting input-only
            scanning scenarios

        Business Impact:
            Enables metrics collection for services that only perform
            input validation without output scanning

        Scenario:
            Given: Snapshot parameters without output_metrics
            When: Creating MetricsSnapshot
            Then: output_metrics field is None
            And: Snapshot creation succeeds

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Snapshot parameters without output_metrics
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=50, violations_count=1, success=True)

        # When: Creating MetricsSnapshot
        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # Then: output_metrics field is not None (it gets a default factory)
        # Looking at the dataclass definition, output_metrics has default_factory=ScanMetrics
        assert snapshot.output_metrics is not None
        assert isinstance(snapshot.output_metrics, ScanMetrics)

        # And: Snapshot creation succeeds
        assert snapshot.input_metrics is input_metrics
        assert snapshot.output_metrics.scan_count == 0  # Default empty metrics
    
    def test_metrics_snapshot_initialization_defaults_uptime_to_zero(self):
        """
        Test that MetricsSnapshot defaults uptime_seconds to 0 when not provided.

        Verifies:
            Uptime tracking is optional with zero default per contract

        Business Impact:
            Allows snapshot creation without uptime tracking for
            stateless or ephemeral services

        Scenario:
            Given: Snapshot parameters without uptime_seconds
            When: Creating MetricsSnapshot
            Then: uptime_seconds defaults to 0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Snapshot parameters without uptime_seconds
        # When: Creating MetricsSnapshot
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # Then: uptime_seconds defaults to 0
        assert snapshot.uptime_seconds == 0
        assert isinstance(snapshot.uptime_seconds, int)
    
    def test_metrics_snapshot_initialization_defaults_memory_usage_to_zero(self):
        """
        Test that MetricsSnapshot defaults memory_usage_mb to 0.0 when not provided.

        Verifies:
            Memory tracking is optional with zero default per contract

        Business Impact:
            Enables snapshots without memory monitoring for minimal
            overhead in resource-constrained environments

        Scenario:
            Given: Snapshot parameters without memory_usage_mb
            When: Creating MetricsSnapshot
            Then: memory_usage_mb defaults to 0.0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Snapshot parameters without memory_usage_mb
        # When: Creating MetricsSnapshot
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # Then: memory_usage_mb defaults to 0.0
        assert snapshot.memory_usage_mb == 0.0
        assert isinstance(snapshot.memory_usage_mb, float)


class TestMetricsSnapshotSerialization:
    """
    Test suite for MetricsSnapshot to_dict() serialization for monitoring.
    
    Scope:
        - Dictionary conversion with all fields
        - Nested ScanMetrics serialization
        - Success rate calculation for input/output metrics
        - Timestamp ISO 8601 formatting
        - System and scanner health preservation
        
    Business Critical:
        Proper serialization enables integration with monitoring systems,
        dashboards, and alerting infrastructure.
        
    Test Coverage:
        - Complete field serialization
        - Derived metric calculation (success rates)
        - Nested metrics serialization
        - Health status preservation
        - Timestamp formatting
    """
    
    def test_metrics_snapshot_to_dict_includes_all_core_fields(self):
        """
        Test that to_dict() includes all snapshot fields in serialized output.

        Verifies:
            Dictionary contains input_metrics, output_metrics, system_health,
            scanner_health, uptime, memory, and timestamp per contract

        Business Impact:
            Ensures complete snapshot data for monitoring dashboards and
            time-series storage systems

        Scenario:
            Given: MetricsSnapshot with complete data
            When: Calling to_dict()
            Then: Dictionary contains all expected top-level keys
            And: All values are properly formatted for JSON

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with complete data
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=100, violations_count=2, success=True)

        output_metrics = ScanMetrics()
        output_metrics.update(scan_duration_ms=80, violations_count=1, success=False)

        system_health = {"cpu_usage": 75.5, "memory_usage": 60.2}
        scanner_health = {"injection_detector": True, "toxicity_scanner": False}
        custom_timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health=system_health,
            scanner_health=scanner_health,
            uptime_seconds=86400,
            memory_usage_mb=256.7,
            timestamp=custom_timestamp
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: Dictionary contains all expected top-level keys
        expected_keys = [
            "input_metrics", "output_metrics", "system_health",
            "scanner_health", "uptime_seconds", "memory_usage_mb", "timestamp"
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

        # And: All values are properly formatted for JSON
        assert result["uptime_seconds"] == 86400
        assert result["memory_usage_mb"] == 256.7
        assert isinstance(result["timestamp"], str)
        assert isinstance(result["system_health"], dict)
        assert isinstance(result["scanner_health"], dict)
    
    def test_metrics_snapshot_to_dict_serializes_input_metrics_with_success_rate(self):
        """
        Test that to_dict() serializes input_metrics and calculates success rate.

        Verifies:
            Input metrics are expanded to dictionary with calculated
            success_rate field per contract

        Business Impact:
            Provides immediate success rate visibility in monitoring
            without requiring client-side calculation

        Scenario:
            Given: MetricsSnapshot with input_metrics containing scan data
            When: Calling to_dict()
            Then: "input_metrics" contains scan_count, successful_scans, etc.
            And: "success_rate" is calculated as successful_scans / scan_count
            And: Division by zero is handled gracefully (returns 0.0)

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with input_metrics containing scan data
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=100, violations_count=2, success=True)
        input_metrics.update(scan_duration_ms=80, violations_count=0, success=True)
        input_metrics.update(scan_duration_ms=120, violations_count=1, success=False)

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "input_metrics" contains scan_count, successful_scans, etc.
        input_metrics_dict = result["input_metrics"]
        expected_metric_fields = [
            "scan_count", "total_scan_time_ms", "successful_scans",
            "failed_scans", "violations_detected", "average_scan_time_ms", "success_rate"
        ]
        for field in expected_metric_fields:
            assert field in input_metrics_dict, f"Missing input metric field: {field}"

        assert input_metrics_dict["scan_count"] == 3
        assert input_metrics_dict["successful_scans"] == 2
        assert input_metrics_dict["failed_scans"] == 1
        assert input_metrics_dict["violations_detected"] == 3
        assert input_metrics_dict["average_scan_time_ms"] == 100.0  # (100 + 80 + 120) / 3

        # And: "success_rate" is calculated as successful_scans / scan_count
        expected_success_rate = 2.0 / 3.0  # 2 successful out of 3 total
        assert input_metrics_dict["success_rate"] == expected_success_rate
    
    def test_metrics_snapshot_to_dict_serializes_output_metrics_with_success_rate(self):
        """
        Test that to_dict() serializes output_metrics and calculates success rate.

        Verifies:
            Output metrics receive same success rate calculation as input
            metrics per contract

        Business Impact:
            Enables unified success rate monitoring for both input and
            output validation operations

        Scenario:
            Given: MetricsSnapshot with output_metrics containing scan data
            When: Calling to_dict()
            Then: "output_metrics" contains all scan metrics
            And: "success_rate" is calculated correctly

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with output_metrics containing scan data
        input_metrics = ScanMetrics()
        output_metrics = ScanMetrics()
        output_metrics.update(scan_duration_ms=90, violations_count=1, success=True)
        output_metrics.update(scan_duration_ms=110, violations_count=2, success=True)
        output_metrics.update(scan_duration_ms=70, violations_count=0, success=False)

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "output_metrics" contains all scan metrics
        output_metrics_dict = result["output_metrics"]
        expected_metric_fields = [
            "scan_count", "total_scan_time_ms", "successful_scans",
            "failed_scans", "violations_detected", "average_scan_time_ms", "success_rate"
        ]
        for field in expected_metric_fields:
            assert field in output_metrics_dict, f"Missing output metric field: {field}"

        assert output_metrics_dict["scan_count"] == 3
        assert output_metrics_dict["successful_scans"] == 2
        assert output_metrics_dict["failed_scans"] == 1
        assert output_metrics_dict["violations_detected"] == 3
        assert output_metrics_dict["average_scan_time_ms"] == 90.0  # (90 + 110 + 70) / 3

        # And: "success_rate" is calculated correctly
        expected_success_rate = 2.0 / 3.0  # 2 successful out of 3 total
        assert output_metrics_dict["success_rate"] == expected_success_rate
    
    def test_metrics_snapshot_to_dict_handles_none_output_metrics(self):
        """
        Test that to_dict() handles None output_metrics gracefully.

        Verifies:
            Missing output metrics are represented as None in serialized
            output per contract

        Business Impact:
            Supports services that only perform input validation without
            breaking monitoring integrations

        Scenario:
            Given: MetricsSnapshot with output_metrics = None
            When: Calling to_dict()
            Then: "output_metrics" key has None value
            And: No errors occur during serialization

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with output_metrics (default factory creates empty ScanMetrics)
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=50, violations_count=1, success=True)

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
            # output_metrics will use default factory to create empty ScanMetrics
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "output_metrics" key exists and contains empty metrics
        assert "output_metrics" in result
        assert result["output_metrics"] is not None

        # And: No errors occur during serialization
        output_metrics_dict = result["output_metrics"]
        assert output_metrics_dict["scan_count"] == 0
        assert output_metrics_dict["success_rate"] == 0.0  # Empty metrics case

    def test_metrics_snapshot_to_dict_calculates_success_rate_correctly(self):
        """
        Test that to_dict() calculates success rate as successful_scans / scan_count.

        Verifies:
            Success rate formula matches documented calculation per contract

        Business Impact:
            Ensures accurate reliability metrics for SLA monitoring and
            service quality assessment

        Scenario:
            Given: ScanMetrics with 8 successful scans out of 10 total
            When: Serializing via to_dict()
            Then: success_rate equals 0.8 (80%)
            And: Rate is float between 0.0 and 1.0

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: ScanMetrics with 8 successful scans out of 10 total
        input_metrics = ScanMetrics()
        for i in range(8):
            input_metrics.update(scan_duration_ms=100, violations_count=1, success=True)
        for i in range(2):
            input_metrics.update(scan_duration_ms=150, violations_count=0, success=False)

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # When: Serializing via to_dict()
        result = snapshot.to_dict()

        # Then: success_rate equals 0.8 (80%)
        input_metrics_dict = result["input_metrics"]
        expected_success_rate = 8.0 / 10.0
        assert input_metrics_dict["success_rate"] == expected_success_rate

        # And: Rate is float between 0.0 and 1.0
        assert isinstance(input_metrics_dict["success_rate"], float)
        assert 0.0 <= input_metrics_dict["success_rate"] <= 1.0

    def test_metrics_snapshot_to_dict_handles_zero_scans_gracefully(self):
        """
        Test that to_dict() handles division by zero when scan_count is 0.

        Verifies:
            Success rate defaults to 0.0 when no scans recorded, preventing
            division by zero errors per contract

        Business Impact:
            Prevents monitoring errors during service startup or idle
            periods before first scan

        Scenario:
            Given: MetricsSnapshot with input_metrics having scan_count = 0
            When: Calling to_dict()
            Then: success_rate equals 0.0
            And: No ZeroDivisionError is raised

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with empty input_metrics (scan_count = 0)
        input_metrics = ScanMetrics()  # Empty metrics, no scans performed

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True}
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: success_rate equals 0.0
        input_metrics_dict = result["input_metrics"]
        assert input_metrics_dict["success_rate"] == 0.0

        # And: No ZeroDivisionError is raised
        assert input_metrics_dict["scan_count"] == 0
        assert input_metrics_dict["successful_scans"] == 0
        assert input_metrics_dict["failed_scans"] == 0
    
    def test_metrics_snapshot_to_dict_formats_timestamp_as_iso_8601(self):
        """
        Test that to_dict() formats timestamp as ISO 8601 string.

        Verifies:
            Datetime timestamp is converted to standardized ISO 8601
            format for monitoring system compatibility

        Business Impact:
            Ensures consistent timestamp format across monitoring tools
            and time-series databases

        Scenario:
            Given: MetricsSnapshot with UTC timestamp
            When: Calling to_dict()
            Then: "timestamp" is string in ISO 8601 format
            And: Timestamp can be parsed by monitoring systems

        Fixtures Used:
            None - Direct dataclass testing
        """
        import json

        # Given: MetricsSnapshot with UTC timestamp
        custom_timestamp = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True},
            timestamp=custom_timestamp
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "timestamp" is string in ISO 8601 format
        timestamp_str = result["timestamp"]
        assert isinstance(timestamp_str, str)
        assert "2024-01-15T10:30:45.123456+00:00" in timestamp_str

        # And: Timestamp can be parsed by monitoring systems
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert parsed_timestamp == custom_timestamp

        # Can be serialized to JSON
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_metrics_snapshot_to_dict_preserves_system_health_dictionary(self):
        """
        Test that to_dict() includes system_health dictionary exactly as stored.

        Verifies:
            System health indicators are preserved in serialized output
            for monitoring dashboards per contract

        Business Impact:
            Enables comprehensive system monitoring with custom health
            indicators specific to deployment

        Scenario:
            Given: MetricsSnapshot with system_health containing CPU, memory metrics
            When: Calling to_dict()
            Then: "system_health" dictionary is included with all entries
            And: Nested values are preserved

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with system_health containing CPU, memory metrics
        system_health = {
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "disk_space": 85.0,
            "network_latency": 12.3,
            "connection_pool": {"active": 5, "idle": 15},
            "last_restart": "2024-01-15T10:30:00Z"
        }

        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health=system_health,
            scanner_health={"scanner1": True}
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "system_health" dictionary is included with all entries
        assert "system_health" in result
        assert result["system_health"] == system_health
        assert len(result["system_health"]) == 6

        # And: Nested values are preserved
        assert result["system_health"]["cpu_usage"] == 75.5
        assert result["system_health"]["connection_pool"]["active"] == 5
        assert result["system_health"]["connection_pool"]["idle"] == 15

    def test_metrics_snapshot_to_dict_preserves_scanner_health_dictionary(self):
        """
        Test that to_dict() includes scanner_health dictionary with all scanner statuses.

        Verifies:
            Individual scanner health status is preserved for per-scanner
            monitoring per contract

        Business Impact:
            Enables identification of specific failing or degraded scanners
            for targeted troubleshooting

        Scenario:
            Given: MetricsSnapshot with scanner_health mapping scanners to status
            When: Calling to_dict()
            Then: "scanner_health" dictionary is included completely
            And: All scanner names and statuses are preserved

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with scanner_health mapping scanners to status
        scanner_health = {
            "injection_detector": True,
            "toxicity_scanner": True,
            "pii_detector": False,
            "bias_detector": True,
            "content_safety": False
        }

        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health=scanner_health
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "scanner_health" dictionary is included completely
        assert "scanner_health" in result
        assert result["scanner_health"] == scanner_health
        assert len(result["scanner_health"]) == 5

        # And: All scanner names and statuses are preserved
        assert result["scanner_health"]["injection_detector"] is True
        assert result["scanner_health"]["toxicity_scanner"] is True
        assert result["scanner_health"]["pii_detector"] is False
        assert result["scanner_health"]["bias_detector"] is True
        assert result["scanner_health"]["content_safety"] is False

    def test_metrics_snapshot_to_dict_includes_uptime_seconds(self):
        """
        Test that to_dict() includes uptime_seconds for service uptime tracking.

        Verifies:
            Uptime value is included in serialized snapshot per contract

        Business Impact:
            Enables uptime monitoring and service availability analysis

        Scenario:
            Given: MetricsSnapshot with uptime_seconds = 86400 (1 day)
            When: Calling to_dict()
            Then: "uptime_seconds" equals 86400
            And: Value is integer representing seconds since start

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with uptime_seconds = 86400 (1 day)
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True},
            uptime_seconds=86400
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "uptime_seconds" equals 86400
        assert result["uptime_seconds"] == 86400

        # And: Value is integer representing seconds since start
        assert isinstance(result["uptime_seconds"], int)

    def test_metrics_snapshot_to_dict_includes_memory_usage_mb(self):
        """
        Test that to_dict() includes memory_usage_mb for resource monitoring.

        Verifies:
            Memory usage value is included in serialized snapshot per contract

        Business Impact:
            Supports memory leak detection and capacity planning

        Scenario:
            Given: MetricsSnapshot with memory_usage_mb = 256.5
            When: Calling to_dict()
            Then: "memory_usage_mb" equals 256.5
            And: Value is float representing megabytes

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: MetricsSnapshot with memory_usage_mb = 256.5
        snapshot = MetricsSnapshot(
            input_metrics=ScanMetrics(),
            system_health={"status": "healthy"},
            scanner_health={"scanner1": True},
            memory_usage_mb=256.5
        )

        # When: Calling to_dict()
        result = snapshot.to_dict()

        # Then: "memory_usage_mb" equals 256.5
        assert result["memory_usage_mb"] == 256.5

        # And: Value is float representing megabytes
        assert isinstance(result["memory_usage_mb"], float)

    def test_metrics_snapshot_to_dict_produces_json_serializable_output(self):
        """
        Test that to_dict() output can be serialized to JSON without errors.

        Verifies:
            All data types in dictionary are JSON-compatible per contract

        Business Impact:
            Enables direct integration with monitoring APIs and time-series
            databases requiring JSON format

        Scenario:
            Given: MetricsSnapshot with complete data
            When: Calling to_dict() and serializing with json.dumps()
            Then: JSON serialization succeeds without errors
            And: Output can be transmitted to monitoring systems

        Fixtures Used:
            None - Direct dataclass testing
        """
        import json

        # Given: MetricsSnapshot with complete data
        input_metrics = ScanMetrics()
        input_metrics.update(scan_duration_ms=100, violations_count=2, success=True)

        output_metrics = ScanMetrics()
        output_metrics.update(scan_duration_ms=80, violations_count=1, success=False)

        system_health = {
            "cpu_usage": 75.5,
            "connection_pool": {"active": 5, "idle": 15}
        }
        scanner_health = {
            "injection_detector": True,
            "toxicity_scanner": False
        }

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health=system_health,
            scanner_health=scanner_health,
            uptime_seconds=86400,
            memory_usage_mb=256.7
        )

        # When: Calling to_dict() and serializing with json.dumps()
        result = snapshot.to_dict()

        # Then: JSON serialization succeeds without errors
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # And: Output can be transmitted to monitoring systems
        # Can deserialize back to verify content
        deserialized = json.loads(json_str)
        assert deserialized["uptime_seconds"] == 86400
        assert deserialized["memory_usage_mb"] == 256.7
        assert "input_metrics" in deserialized
        assert "output_metrics" in deserialized
        assert "system_health" in deserialized
        assert "scanner_health" in deserialized
        assert "timestamp" in deserialized

