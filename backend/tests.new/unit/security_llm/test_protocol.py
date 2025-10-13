"""
Unit tests for Security Service Protocol and Data Models.

This test module verifies that the security protocol and data structures
behave correctly as documented in the public contract.

Test Coverage:
    - SecurityResult dataclass validation and behavior
    - Violation dataclass validation and behavior
    - ScanMetrics functionality
    - MetricsSnapshot data structure
    - SecurityService protocol interface
    - Exception classes and error handling

Business Critical:
    Proper data model validation ensures security scan results are
    accurate and consistent throughout the system.
"""

import pytest
from datetime import datetime

from app.infrastructure.security.llm.protocol import (
    SecurityResult,
    Violation,
    ViolationType,
    SeverityLevel,
    ScanMetrics,
    MetricsSnapshot,
    SecurityService,
    SecurityServiceError,
    ScannerInitializationError,
    ScannerTimeoutError,
    ScannerConfigurationError,
)


class TestViolation:
    """
    Test suite for Violation dataclass behavior.

    Scope:
        Tests violation creation, validation, and serialization.
    """

    def test_violation_creation_with_valid_data(self) -> None:
        """
        Test that violation can be created with valid data.

        Verifies:
            Violation dataclass accepts valid parameters as documented
            in dataclass docstring.
        """
        violation = Violation(
            type=ViolationType.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            description="Prompt injection detected",
            confidence=0.9,
            scanner_name="PromptInjectionScanner"
        )

        assert violation.type == ViolationType.PROMPT_INJECTION
        assert violation.severity == SeverityLevel.HIGH
        assert violation.description == "Prompt injection detected"
        assert violation.confidence == 0.9
        assert violation.scanner_name == "PromptInjectionScanner"
        assert violation.text_snippet is None
        assert violation.start_index is None
        assert violation.end_index is None
        assert violation.metadata == {}
        assert isinstance(violation.timestamp, datetime)

    def test_violation_creation_with_all_parameters(self) -> None:
        """
        Test that violation can be created with all optional parameters.

        Verifies:
            Violation dataclass accepts all optional parameters.
        """
        timestamp = datetime.utcnow()
        metadata = {"pattern": "ignore previous instructions"}

        violation = Violation(
            type=ViolationType.TOXIC_OUTPUT,
            severity=SeverityLevel.MEDIUM,
            description="Toxic content detected",
            confidence=0.8,
            scanner_name="ToxicityScanner",
            text_snippet="toxic content here",
            start_index=10,
            end_index=25,
            metadata=metadata,
            timestamp=timestamp
        )

        assert violation.text_snippet == "toxic content here"
        assert violation.start_index == 10
        assert violation.end_index == 25
        assert violation.metadata == metadata
        assert violation.timestamp == timestamp

    def test_violation_validation_rejects_invalid_confidence(self) -> None:
        """
        Test that violation validation rejects invalid confidence values.

        Verifies:
            Violation raises ValueError for confidence outside 0.0-1.0 range
            as documented in __post_init__ method.
        """
        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=ViolationType.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="Test violation",
                confidence=1.5,  # Invalid confidence
                scanner_name="TestScanner"
            )

        assert "Confidence must be between 0.0 and 1.0" in str(exc_info.value)
        assert "1.5" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=ViolationType.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="Test violation",
                confidence=-0.1,  # Invalid confidence
                scanner_name="TestScanner"
            )

        assert "Confidence must be between 0.0 and 1.0" in str(exc_info.value)

    def test_violation_validation_rejects_empty_description(self) -> None:
        """
        Test that violation validation rejects empty description.

        Verifies:
            Violation raises ValueError for empty description
            as documented in __post_init__ method.
        """
        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=ViolationType.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="   ",  # Empty after stripping
                confidence=0.8,
                scanner_name="TestScanner"
            )

        assert "Description cannot be empty" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=ViolationType.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="",  # Empty string
                confidence=0.8,
                scanner_name="TestScanner"
            )

        assert "Description cannot be empty" in str(exc_info.value)

    def test_violation_validation_rejects_empty_scanner_name(self) -> None:
        """
        Test that violation validation rejects empty scanner name.

        Verifies:
            Violation raises ValueError for empty scanner name
            as documented in __post_init__ method.
        """
        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=ViolationType.PROMPT_INJECTION,
                severity=SeverityLevel.HIGH,
                description="Test violation",
                confidence=0.8,
                scanner_name="   "  # Empty after stripping
            )

        assert "Scanner name cannot be empty" in str(exc_info.value)

    def test_violation_to_dict_returns_correct_structure(self) -> None:
        """
        Test that to_dict returns correct dictionary representation.

        Verifies:
            Violation serialization includes all expected fields
            as documented in to_dict method.
        """
        timestamp = datetime.utcnow()
        violation = Violation(
            type=ViolationType.PII_LEAKAGE,
            severity=SeverityLevel.CRITICAL,
            description="PII detected",
            confidence=0.95,
            scanner_name="PIIScanner",
            text_snippet="john@example.com",
            start_index=5,
            end_index=19,
            metadata={"email_detected": True},
            timestamp=timestamp
        )

        result = violation.to_dict()

        # Verify structure
        assert isinstance(result, dict)
        assert result["type"] == "pii_leakage"
        assert result["severity"] == "critical"
        assert result["description"] == "PII detected"
        assert result["confidence"] == 0.95
        assert result["scanner_name"] == "PIIScanner"
        assert result["text_snippet"] == "john@example.com"
        assert result["start_index"] == 5
        assert result["end_index"] == 19
        assert result["metadata"] == {"email_detected": True}
        assert result["timestamp"] == timestamp.isoformat()

    def test_violation_from_dict_creates_violation_correctly(self) -> None:
        """
        Test that from_dict creates violation from dictionary correctly.

        Verifies:
            Violation deserialization works correctly
            as documented in from_dict class method.
        """
        timestamp = datetime.utcnow()
        data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "Prompt injection detected",
            "confidence": 0.9,
            "scanner_name": "PromptInjectionScanner",
            "text_snippet": "ignore previous instructions",
            "start_index": 0,
            "end_index": 28,
            "metadata": {"pattern_matched": True},
            "timestamp": timestamp.isoformat(),
        }

        violation = Violation.from_dict(data)

        # Verify violation created correctly
        assert violation.type == ViolationType.PROMPT_INJECTION
        assert violation.severity == SeverityLevel.HIGH
        assert violation.description == "Prompt injection detected"
        assert violation.confidence == 0.9
        assert violation.scanner_name == "PromptInjectionScanner"
        assert violation.text_snippet == "ignore previous instructions"
        assert violation.start_index == 0
        assert violation.end_index == 28
        assert violation.metadata == {"pattern_matched": True}
        assert violation.timestamp == timestamp

    def test_violation_from_dict_handles_missing_timestamp(self) -> None:
        """
        Test that from_dict handles missing timestamp gracefully.

        Verifies:
            Missing timestamp defaults to current time.
        """
        data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "Test violation",
            "confidence": 0.8,
            "scanner_name": "TestScanner",
        }

        violation = Violation.from_dict(data)

        assert isinstance(violation.timestamp, datetime)


class TestSecurityResult:
    """
    Test suite for SecurityResult dataclass behavior.

    Scope:
        Tests security result creation, validation, and utility methods.
    """

    def test_security_result_creation_with_valid_data(self) -> None:
        """
        Test that security result can be created with valid data.

        Verifies:
            SecurityResult dataclass accepts valid parameters as documented
            in dataclass docstring.
        """
        violation = Violation(
            type=ViolationType.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            description="Test violation",
            confidence=0.9,
            scanner_name="TestScanner"
        )

        result = SecurityResult(
            is_safe=False,
            violations=[violation],
            score=0.3,
            scanned_text="test input",
            scan_duration_ms=150
        )

        assert result.is_safe is False
        assert len(result.violations) == 1
        assert result.violations[0] is violation
        assert result.score == 0.3
        assert result.scanned_text == "test input"
        assert result.scan_duration_ms == 150
        assert result.scanner_results == {}
        assert result.metadata == {}
        assert isinstance(result.timestamp, datetime)

    def test_security_result_validation_rejects_invalid_score(self) -> None:
        """
        Test that security result validation rejects invalid score.

        Verifies:
            SecurityResult raises ValueError for score outside 0.0-1.0 range
            as documented in __post_init__ method.
        """
        violation = Violation(
            type=ViolationType.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            description="Test violation",
            confidence=0.9,
            scanner_name="TestScanner"
        )

        with pytest.raises(ValueError) as exc_info:
            SecurityResult(
                is_safe=False,
                violations=[violation],
                score=1.5,  # Invalid score
                scanned_text="test",
                scan_duration_ms=100
            )

        assert "Score must be between 0.0 and 1.0" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            SecurityResult(
                is_safe=True,
                violations=[],
                score=-0.1,  # Invalid score
                scanned_text="test",
                scan_duration_ms=100
            )

        assert "Score must be between 0.0 and 1.0" in str(exc_info.value)

    def test_security_result_validation_rejects_negative_duration(self) -> None:
        """
        Test that security result validation rejects negative duration.

        Verifies:
            SecurityResult raises ValueError for negative scan duration
            as documented in __post_init__ method.
        """
        with pytest.raises(ValueError) as exc_info:
            SecurityResult(
                is_safe=True,
                violations=[],
                score=1.0,
                scanned_text="test",
                scan_duration_ms=-10  # Negative duration
            )

        assert "Scan duration must be non-negative" in str(exc_info.value)

    def test_security_result_auto_adjusts_is_safe_based_on_violations(self) -> None:
        """
        Test that security result auto-adjusts is_safe based on violations.

        Verifies:
            SecurityResult automatically sets is_safe=False when violations present
            and is_safe=True when no violations exist, as documented in __post_init__.
        """
        violation = Violation(
            type=ViolationType.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            description="Test violation",
            confidence=0.9,
            scanner_name="TestScanner"
        )

        # Case 1: Has violations but is_safe=True - should be corrected to False
        result1 = SecurityResult(
            is_safe=True,  # Contradictory
            violations=[violation],
            score=0.3,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result1.is_safe is False  # Should be auto-corrected

        # Case 2: No violations but is_safe=False - should be corrected to True
        result2 = SecurityResult(
            is_safe=False,  # Contradictory
            violations=[],
            score=1.0,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result2.is_safe is True  # Should be auto-corrected

        # Case 3: Consistent values - should remain unchanged
        result3 = SecurityResult(
            is_safe=False,  # Consistent
            violations=[violation],
            score=0.3,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result3.is_safe is False  # Should remain False

        result4 = SecurityResult(
            is_safe=True,  # Consistent
            violations=[],
            score=1.0,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result4.is_safe is True  # Should remain True

    def test_get_violations_by_severity_groups_violations_correctly(self) -> None:
        """
        Test that get_violations_by_severity groups violations correctly.

        Verifies:
            Method groups violations by severity level as documented.
        """
        violations = [
            Violation(ViolationType.PROMPT_INJECTION, SeverityLevel.CRITICAL, "Critical", 0.9, "Scanner1"),
            Violation(ViolationType.TOXIC_OUTPUT, SeverityLevel.HIGH, "High", 0.8, "Scanner2"),
            Violation(ViolationType.BIAS_DETECTED, SeverityLevel.MEDIUM, "Medium", 0.7, "Scanner3"),
            Violation(ViolationType.PII_LEAKAGE, SeverityLevel.LOW, "Low", 0.6, "Scanner4"),
        ]

        result = SecurityResult(
            is_safe=False,
            violations=violations,
            score=0.2,
            scanned_text="test",
            scan_duration_ms=100
        )

        grouped = result.get_violations_by_severity()

        # Verify all severity levels are present
        assert SeverityLevel.CRITICAL in grouped
        assert SeverityLevel.HIGH in grouped
        assert SeverityLevel.MEDIUM in grouped
        assert SeverityLevel.LOW in grouped

        # Verify correct grouping
        assert len(grouped[SeverityLevel.CRITICAL]) == 1
        assert len(grouped[SeverityLevel.HIGH]) == 1
        assert len(grouped[SeverityLevel.MEDIUM]) == 1
        assert len(grouped[SeverityLevel.LOW]) == 1

        assert grouped[SeverityLevel.CRITICAL][0].severity == SeverityLevel.CRITICAL
        assert grouped[SeverityLevel.HIGH][0].severity == SeverityLevel.HIGH

    def test_get_violations_by_type_groups_violations_correctly(self) -> None:
        """
        Test that get_violations_by_type groups violations correctly.

        Verifies:
            Method groups violations by type as documented.
        """
        violations = [
            Violation(ViolationType.PROMPT_INJECTION, SeverityLevel.HIGH, "PI1", 0.9, "Scanner1"),
            Violation(ViolationType.PROMPT_INJECTION, SeverityLevel.MEDIUM, "PI2", 0.7, "Scanner2"),
            Violation(ViolationType.TOXIC_OUTPUT, SeverityLevel.HIGH, "Toxic", 0.8, "Scanner3"),
        ]

        result = SecurityResult(
            is_safe=False,
            violations=violations,
            score=0.2,
            scanned_text="test",
            scan_duration_ms=100
        )

        grouped = result.get_violations_by_type()

        # Verify correct grouping
        assert len(grouped[ViolationType.PROMPT_INJECTION]) == 2
        assert len(grouped[ViolationType.TOXIC_OUTPUT]) == 1
        assert all(v.type == ViolationType.PROMPT_INJECTION for v in grouped[ViolationType.PROMPT_INJECTION])
        assert all(v.type == ViolationType.TOXIC_OUTPUT for v in grouped[ViolationType.TOXIC_OUTPUT])

    def test_has_critical_violations_detects_critical_violations(self) -> None:
        """
        Test that has_critical_violations detects critical violations.

        Verifies:
            Method correctly identifies presence of critical violations.
        """
        critical_violation = Violation(ViolationType.PROMPT_INJECTION, SeverityLevel.CRITICAL, "Critical", 0.9, "Scanner1")
        high_violation = Violation(ViolationType.TOXIC_OUTPUT, SeverityLevel.HIGH, "High", 0.8, "Scanner2")

        # With critical violation
        result1 = SecurityResult(
            is_safe=False,
            violations=[critical_violation, high_violation],
            score=0.1,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result1.has_critical_violations() is True

        # Without critical violation
        result2 = SecurityResult(
            is_safe=False,
            violations=[high_violation],
            score=0.3,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result2.has_critical_violations() is False

    def test_has_high_severity_violations_detects_high_and_critical(self) -> None:
        """
        Test that has_high_severity_violations detects high and critical violations.

        Verifies:
            Method correctly identifies presence of high or critical violations.
        """
        critical_violation = Violation(ViolationType.PROMPT_INJECTION, SeverityLevel.CRITICAL, "Critical", 0.9, "Scanner1")
        high_violation = Violation(ViolationType.TOXIC_OUTPUT, SeverityLevel.HIGH, "High", 0.8, "Scanner2")
        medium_violation = Violation(ViolationType.BIAS_DETECTED, SeverityLevel.MEDIUM, "Medium", 0.7, "Scanner3")

        # With high and critical violations
        result1 = SecurityResult(
            is_safe=False,
            violations=[critical_violation, high_violation, medium_violation],
            score=0.1,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result1.has_high_severity_violations() is True

        # With only critical violation
        result2 = SecurityResult(
            is_safe=False,
            violations=[critical_violation],
            score=0.2,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result2.has_high_severity_violations() is True

        # With only medium violations
        result3 = SecurityResult(
            is_safe=False,
            violations=[medium_violation],
            score=0.5,
            scanned_text="test",
            scan_duration_ms=100
        )
        assert result3.has_high_severity_violations() is False

    def test_to_dict_returns_comprehensive_representation(self) -> None:
        """
        Test that to_dict returns comprehensive dictionary representation.

        Verifies:
            Serialization includes all expected fields and violation counts
            as documented in to_dict method.
        """
        violations = [
            Violation(ViolationType.PROMPT_INJECTION, SeverityLevel.CRITICAL, "Critical", 0.9, "Scanner1"),
            Violation(ViolationType.TOXIC_OUTPUT, SeverityLevel.HIGH, "High", 0.8, "Scanner2"),
        ]

        result = SecurityResult(
            is_safe=False,
            violations=violations,
            score=0.2,
            scanned_text="test input text",
            scan_duration_ms=150,
            scanner_results={"Scanner1": {"success": True}},
            metadata={"test": True}
        )

        dict_result = result.to_dict()

        # Verify structure
        assert isinstance(dict_result, dict)
        assert dict_result["is_safe"] is False
        assert dict_result["score"] == 0.2
        assert dict_result["scanned_text_length"] == len("test input text")
        assert dict_result["scan_duration_ms"] == 150
        assert dict_result["scanner_results"] == {"Scanner1": {"success": True}}
        assert dict_result["metadata"] == {"test": True}
        assert isinstance(dict_result["timestamp"], str)
        assert isinstance(dict_result["violations"], list)

        # Verify violation counts
        violation_counts = dict_result["violation_counts"]
        assert violation_counts["total"] == 2
        assert violation_counts["critical"] == 1
        assert violation_counts["high"] == 1
        assert violation_counts["medium"] == 0
        assert violation_counts["low"] == 0

    def test_from_dict_creates_security_result_correctly(self) -> None:
        """
        Test that from_dict creates security result from dictionary correctly.

        Verifies:
            SecurityResult deserialization works correctly
            as documented in from_dict class method.
        """
        timestamp = datetime.utcnow()
        violation_data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "Test violation",
            "confidence": 0.8,
            "scanner_name": "TestScanner",
            "timestamp": timestamp.isoformat(),
        }

        data = {
            "is_safe": False,
            "violations": [violation_data],
            "score": 0.3,
            "scanned_text": "test input",
            "scan_duration_ms": 100,
            "scanner_results": {"TestScanner": {"success": True}},
            "metadata": {"test": True},
            "timestamp": timestamp.isoformat(),
        }

        result = SecurityResult.from_dict(data)

        # Verify result created correctly
        assert result.is_safe is False
        assert len(result.violations) == 1
        assert result.score == 0.3
        assert result.scanned_text == "test input"
        assert result.scan_duration_ms == 100
        assert result.scanner_results == {"TestScanner": {"success": True}}
        assert result.metadata == {"test": True}
        assert result.timestamp == timestamp

        # Verify violation created correctly
        violation = result.violations[0]
        assert violation.type == ViolationType.PROMPT_INJECTION
        assert violation.severity == SeverityLevel.HIGH


class TestScanMetrics:
    """
    Test suite for ScanMetrics class behavior.

    Scope:
        Tests metrics collection, updating, and reset functionality.
    """

    def test_scan_metrics_initialization_with_defaults(self) -> None:
        """
        Test that scan metrics initialize with correct defaults.

        Verifies:
            ScanMetrics initializes with zero values as documented.
        """
        metrics = ScanMetrics()

        assert metrics.scan_count == 0
        assert metrics.total_scan_time_ms == 0
        assert metrics.successful_scans == 0
        assert metrics.failed_scans == 0
        assert metrics.violations_detected == 0
        assert metrics.average_scan_time_ms == 0.0

    def test_update_metrics_updates_all_fields_correctly(self) -> None:
        """
        Test that update metrics updates all fields correctly.

        Verifies:
            Update method correctly increments counters and updates averages
            as documented in update method.
        """
        metrics = ScanMetrics()

        # First update
        metrics.update(scan_duration_ms=100, violations_count=1, success=True)
        assert metrics.scan_count == 1
        assert metrics.total_scan_time_ms == 100
        assert metrics.successful_scans == 1
        assert metrics.failed_scans == 0
        assert metrics.violations_detected == 1
        assert metrics.average_scan_time_ms == 100.0

        # Second update
        metrics.update(scan_duration_ms=200, violations_count=0, success=True)
        assert metrics.scan_count == 2
        assert metrics.total_scan_time_ms == 300
        assert metrics.successful_scans == 2
        assert metrics.failed_scans == 0
        assert metrics.violations_detected == 1
        assert metrics.average_scan_time_ms == 150.0  # (100 + 200) / 2

        # Third update (failed)
        metrics.update(scan_duration_ms=50, violations_count=2, success=False)
        assert metrics.scan_count == 3
        assert metrics.total_scan_time_ms == 350
        assert metrics.successful_scans == 2
        assert metrics.failed_scans == 1
        assert metrics.violations_detected == 3
        assert metrics.average_scan_time_ms == 350.0 / 3.0

    def test_reset_metrics_clears_all_values(self) -> None:
        """
        Test that reset metrics clears all values to defaults.

        Verifies:
            Reset method returns all metrics to initial state
            as documented in reset method.
        """
        metrics = ScanMetrics()
        metrics.update(scan_duration_ms=100, violations_count=1, success=True)

        # Verify metrics are set
        assert metrics.scan_count == 1
        assert metrics.total_scan_time_ms == 100

        # Reset metrics
        metrics.reset()

        # Verify all values are reset to defaults
        assert metrics.scan_count == 0
        assert metrics.total_scan_time_ms == 0
        assert metrics.successful_scans == 0
        assert metrics.failed_scans == 0
        assert metrics.violations_detected == 0
        assert metrics.average_scan_time_ms == 0.0


class TestMetricsSnapshot:
    """
    Test suite for MetricsSnapshot class behavior.

    Scope:
        Tests metrics snapshot creation and serialization.
    """

    def test_metrics_snapshot_creation_with_defaults(self) -> None:
        """
        Test that metrics snapshot creates with correct defaults.

        Verifies:
            MetricsSnapshot initializes with default objects as documented.
        """
        snapshot = MetricsSnapshot()

        assert isinstance(snapshot.input_metrics, ScanMetrics)
        assert isinstance(snapshot.output_metrics, ScanMetrics)
        assert snapshot.system_health == {}
        assert snapshot.scanner_health == {}
        assert snapshot.uptime_seconds == 0
        assert snapshot.memory_usage_mb == 0.0
        assert isinstance(snapshot.timestamp, datetime)

    def test_metrics_snapshot_creation_with_custom_values(self) -> None:
        """
        Test that metrics snapshot creates with custom values.

        Verifies:
            MetricsSnapshot accepts custom initialization parameters.
        """
        input_metrics = ScanMetrics()
        input_metrics.update(100, 1, True)

        output_metrics = ScanMetrics()
        output_metrics.update(200, 0, True)

        system_health = {"status": "healthy"}
        scanner_health = {"PromptInjectionScanner": True}
        timestamp = datetime.utcnow()

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health=system_health,
            scanner_health=scanner_health,
            uptime_seconds=3600,
            memory_usage_mb=512.5,
            timestamp=timestamp
        )

        assert snapshot.input_metrics is input_metrics
        assert snapshot.output_metrics is output_metrics
        assert snapshot.system_health == system_health
        assert snapshot.scanner_health == scanner_health
        assert snapshot.uptime_seconds == 3600
        assert snapshot.memory_usage_mb == 512.5
        assert snapshot.timestamp == timestamp

    def test_to_dict_returns_comprehensive_metrics(self) -> None:
        """
        Test that to_dict returns comprehensive metrics dictionary.

        Verifies:
            Serialization includes all metrics with calculated rates
            as documented in to_dict method.
        """
        input_metrics = ScanMetrics()
        input_metrics.update(100, 1, True)
        input_metrics.update(200, 0, False)

        output_metrics = ScanMetrics()
        output_metrics.update(150, 0, True)

        system_health = {"status": "healthy"}
        scanner_health = {"Scanner1": True, "Scanner2": False}

        snapshot = MetricsSnapshot(
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            system_health=system_health,
            scanner_health=scanner_health,
            uptime_seconds=1800,
            memory_usage_mb=256.0
        )

        dict_result = snapshot.to_dict()

        # Verify structure
        assert isinstance(dict_result, dict)
        assert "input_metrics" in dict_result
        assert "output_metrics" in dict_result
        assert "system_health" in dict_result
        assert "scanner_health" in dict_result
        assert "uptime_seconds" in dict_result
        assert "memory_usage_mb" in dict_result
        assert "timestamp" in dict_result

        # Verify input metrics
        input_dict = dict_result["input_metrics"]
        assert input_dict["scan_count"] == 2
        assert input_dict["total_scan_time_ms"] == 300
        assert input_dict["successful_scans"] == 1
        assert input_dict["failed_scans"] == 1
        assert input_dict["violations_detected"] == 1
        assert input_dict["average_scan_time_ms"] == 150.0
        assert input_dict["success_rate"] == 0.5  # 1 / 2

        # Verify output metrics
        output_dict = dict_result["output_metrics"]
        assert output_dict["scan_count"] == 1
        assert output_dict["success_rate"] == 1.0  # 1 / 1


class TestSecurityServiceExceptions:
    """
    Test suite for security service exception classes.

    Scope:
        Tests exception creation and inheritance hierarchy.
    """

    def test_security_service_error_creation(self) -> None:
        """
        Test that SecurityServiceError can be created with parameters.

        Verifies:
            SecurityServiceError accepts all documented parameters.
        """
        original_error = ValueError("Original error")
        error = SecurityServiceError(
            message="Security service failed",
            scanner_name="TestScanner",
            original_error=original_error
        )

        assert str(error) == "Security service failed"
        assert error.scanner_name == "TestScanner"
        assert error.original_error is original_error

    def test_scanner_initialization_error_inheritance(self) -> None:
        """
        Test that ScannerInitializationError inherits from SecurityServiceError.

        Verifies:
            Exception inheritance hierarchy is correct.
        """
        error = ScannerInitializationError("Scanner failed to initialize", "TestScanner")

        assert isinstance(error, SecurityServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Scanner failed to initialize"
        assert error.scanner_name == "TestScanner"

    def test_scanner_timeout_error_inheritance(self) -> None:
        """
        Test that ScannerTimeoutError inherits from SecurityServiceError.

        Verifies:
            Exception inheritance hierarchy is correct.
        """
        error = ScannerTimeoutError("Scanner timed out", "TestScanner")

        assert isinstance(error, SecurityServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Scanner timed out"
        assert error.scanner_name == "TestScanner"

    def test_scanner_configuration_error_inheritance(self) -> None:
        """
        Test that ScannerConfigurationError inherits from SecurityServiceError.

        Verifies:
            Exception inheritance hierarchy is correct.
        """
        error = ScannerConfigurationError("Invalid configuration", "TestScanner")

        assert isinstance(error, SecurityServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid configuration"
        assert error.scanner_name == "TestScanner"


class TestSecurityServiceProtocol:
    """
    Test suite for SecurityService protocol interface.

    Scope:
        Tests protocol method signatures and interface compliance.
    """

    def test_security_service_protocol_is_abstract(self) -> None:
        """
        Test that SecurityService protocol is properly abstract.

        Verifies:
            SecurityService cannot be instantiated directly as it's abstract.
        """
        # SecurityService is an abstract base class with abstract methods
        # It should not be possible to instantiate it directly
        with pytest.raises(TypeError):
            # Use type: ignore to suppress MyPy error for testing abstract instantiation
            SecurityService()  # type: ignore[abstract]

    def test_security_service_protocol_has_required_methods(self) -> None:
        """
        Test that SecurityService protocol defines required methods.

        Verifies:
            Protocol includes all documented abstract methods.
        """
        # Check that SecurityService has the required abstract methods
        abstract_methods = SecurityService.__abstractmethods__

        required_methods = {
            "validate_input",
            "validate_output",
            "health_check",
            "get_metrics",
            "get_configuration",
            "reset_metrics"
        }

        assert required_methods.issubset(abstract_methods)

    def test_security_service_protocol_method_signatures(self) -> None:
        """
        Test that SecurityService protocol methods have correct signatures.

        Verifies:
            Protocol methods have expected signatures as documented.
        """
        # Check method signatures by inspecting the abstract methods
        import inspect

        # validate_input should be async with (self, text: str, context: Optional[Dict[str, Any]] = None)
        validate_input_sig = inspect.signature(SecurityService.validate_input)
        assert "self" in validate_input_sig.parameters
        assert "text" in validate_input_sig.parameters
        assert "context" in validate_input_sig.parameters
        assert inspect.iscoroutinefunction(SecurityService.validate_input)

        # validate_output should be async with similar signature
        validate_output_sig = inspect.signature(SecurityService.validate_output)
        assert "self" in validate_output_sig.parameters
        assert "text" in validate_output_sig.parameters
        assert "context" in validate_output_sig.parameters
        assert inspect.iscoroutinefunction(SecurityService.validate_output)

        # Other methods should also be async
        assert inspect.iscoroutinefunction(SecurityService.health_check)
        assert inspect.iscoroutinefunction(SecurityService.get_metrics)
        assert inspect.iscoroutinefunction(SecurityService.get_configuration)
        assert inspect.iscoroutinefunction(SecurityService.reset_metrics)
