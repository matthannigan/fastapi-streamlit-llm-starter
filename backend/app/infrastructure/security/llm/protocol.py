"""
Security Service Protocol

This module defines the abstract protocol interface for security scanning services.
All security scanner implementations must adhere to this protocol to ensure
consistent behavior and integration across the system.

## Protocol Overview

The SecurityService protocol defines the contract for all security scanning
implementations, providing a standardized interface for input validation,
output validation, and monitoring capabilities.

## Protocol Methods

### Core Security Operations
- **validate_input()**: Scan user inputs for security threats
- **validate_output()**: Scan AI outputs for harmful content
- **health_check()**: Verify service health and availability

### Monitoring and Metrics
- **get_metrics()**: Retrieve performance and security metrics
- **get_configuration()**: Get current scanner configuration
- **reset_metrics()**: Reset performance counters

## Data Structures

### SecurityResult
Standardized result format for all security scans:
- **is_safe**: Boolean indicating if content passed security checks
- **violations**: List of detected security violations
- **score**: Overall security score (0.0 to 1.0)
- **metadata**: Additional scan metadata

### Violation
Detailed information about security violations:
- **type**: Type of security violation detected
- **severity**: Severity level of the violation
- **description**: Human-readable description
- **confidence**: Confidence score of the detection
- **metadata**: Additional violation context

### MetricsSnapshot
Performance and operational metrics:
- **scan_counts**: Number of scans performed
- **execution_times**: Performance timing data
- **violation_rates**: Security violation statistics
- **system_health**: System health indicators
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class ViolationType(str, Enum):
    """
    Enumeration of security violation types detected during scanning operations.

    This enum categorizes security threats and policy violations that can be
    identified in user inputs or AI-generated outputs. Each type represents
    a specific category of security concern with distinct handling requirements
    and severity implications.

    Input Violations:
        Detected in user-provided content before processing by AI models.
        These violations prevent potentially harmful inputs from reaching
        the AI system and protect against various attack vectors.

    Output Violations:
        Detected in AI-generated responses before being returned to users.
        These violations ensure that AI outputs meet safety standards and
        comply with content policies.

    System Violations:
        Relate to the scanning system itself rather than content issues.
        These indicate operational problems that may affect security coverage.

    Examples:
        >>> # Check if a violation is input-related
        >>> violation_type = ViolationType.PROMPT_INJECTION
        >>> assert violation_type.value == "prompt_injection"
        >>>
        >>> # Group violations by category
        >>> input_violations = [
        ...     ViolationType.PROMPT_INJECTION,
        ...     ViolationType.MALICIOUS_PROMPT,
        ...     ViolationType.TOXIC_INPUT
        ... ]
        >>> assert ViolationType.PROMPT_INJECTION in input_violations
        >>>
        >>> # Check system-related violations
        >>> system_violations = [
        ...     ViolationType.SCAN_TIMEOUT,
        ...     ViolationType.SCAN_ERROR,
        ...     ViolationType.SERVICE_UNAVAILABLE
        ... ]
        >>> assert ViolationType.SCAN_TIMEOUT in system_violations
    """

    # Input violations
    PROMPT_INJECTION = "prompt_injection"
    """Attempt to manipulate AI behavior through carefully crafted prompts."""

    MALICIOUS_PROMPT = "malicious_prompt"
    """Intentionally harmful or deceptive input designed to exploit system vulnerabilities."""

    TOXIC_INPUT = "toxic_input"
    """Content containing hate speech, harassment, or other toxic language."""

    PII_LEAKAGE = "pii_leakage"
    """Unintentional exposure of personally identifiable information in input."""

    SUSPICIOUS_PATTERN = "suspicious_pattern"
    """Content matching known attack patterns or anomalous behavior indicators."""

    # Output violations
    TOXIC_OUTPUT = "toxic_output"
    """AI-generated content containing toxic or harmful language."""

    HARMFUL_CONTENT = "harmful_content"
    """Content that could cause harm to users or promote dangerous activities."""

    BIAS_DETECTED = "bias_detected"
    """Content demonstrating unfair bias or discriminatory patterns."""

    UNETHICAL_CONTENT = "unethical_content"
    """Content violating ethical guidelines or moral standards."""

    POLICY_VIOLATION = "policy_violation"
    """Content that violates established usage policies or terms of service."""

    # System violations
    SCAN_TIMEOUT = "scan_timeout"
    """Security scan exceeded maximum allowed time limit."""

    SCAN_ERROR = "scan_error"
    """Technical error occurred during security scanning process."""

    SERVICE_UNAVAILABLE = "service_unavailable"
    """Security scanning service is temporarily unavailable."""


class SeverityLevel(str, Enum):
    """
    Enumeration of violation severity levels for security threat classification.

    This enum defines the severity hierarchy for security violations, enabling
    risk-based decision making and appropriate response strategies. Each level
    represents increasing levels of danger and urgency for security incident
    response and content moderation workflows.

    Severity Hierarchy:
        The levels progress from LOW (minimal impact) to CRITICAL (severe threat),
    with each level having specific implications for content handling, user
    notifications, and system responses. Higher severity violations typically
    require immediate attention and may trigger automated blocking actions.

    Risk Assessment:
        Severity levels combine with violation types to determine overall risk
    scores and guide content moderation decisions. Multiple violations of
    varying severities can be aggregated to assess total content risk.

    Examples:
        >>> # Compare severity levels
        >>> assert SeverityLevel.CRITICAL > SeverityLevel.HIGH
        >>> assert SeverityLevel.HIGH > SeverityLevel.MEDIUM
        >>> assert SeverityLevel.MEDIUM > SeverityLevel.LOW
        >>>
        >>> # Use in violation filtering
        >>> high_severity_levels = [
        ...     SeverityLevel.HIGH,
        ...     SeverityLevel.CRITICAL
        ... ]
        >>> assert SeverityLevel.CRITICAL in high_severity_levels
        >>>
        >>> # Check severity priority
        >>> def should_block_content(severity: SeverityLevel) -> bool:
        ...     return severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        >>> assert should_block_content(SeverityLevel.CRITICAL)
        >>> assert not should_block_content(SeverityLevel.LOW)
    """

    LOW = "low"
    """Minimal security risk with limited potential for harm."""

    MEDIUM = "medium"
    """Moderate security risk requiring attention and possible mitigation."""

    HIGH = "high"
    """Significant security risk requiring immediate action and possible content blocking."""

    CRITICAL = "critical"
    """Severe security threat requiring immediate blocking and incident response."""


@dataclass
class Violation:
    """
    Represents a security violation detected during content scanning operations.

    This dataclass encapsulates all information about a security threat or policy
    violation identified by security scanners. It provides structured data for
    logging, reporting, and decision-making processes in the security pipeline.
    Each violation includes context about what was detected, where it was found,
    and how confident the scanner is in the detection.

    Attributes:
        type: Categorized type of security violation detected
        severity: Severity level indicating the danger level of the violation
        description: Human-readable explanation of the security issue
        confidence: Scanner's confidence in the detection accuracy (0.0 to 1.0)
        scanner_name: Identifier of the security scanner that made the detection
        text_snippet: Exact text segment where the violation was identified
        start_index: Character position where violation begins in original text
        end_index: Character position where violation ends in original text
        metadata: Additional scanner-specific information and context
        timestamp: UTC timestamp when the violation was first detected

    State Management:
        - Validation occurs automatically during initialization via __post_init__
        - Confidence scores are enforced to be within valid range (0.0 to 1.0)
        - Required fields (description, scanner_name) cannot be empty strings
        - Timestamp defaults to current UTC time if not provided
        - Metadata dictionary is mutable for post-creation enrichment

    Usage:
        # Create a basic violation
        violation = Violation(
            type=ViolationType.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            description="Attempt to override system instructions",
            confidence=0.95,
            scanner_name="prompt_guard_v1"
        )

        # Create violation with location context
        violation_with_context = Violation(
            type=ViolationType.TOXIC_INPUT,
            severity=SeverityLevel.MEDIUM,
            description="Offensive language detected in user input",
            confidence=0.87,
            scanner_name="toxicity_classifier",
            text_snippet="This is offensive content",
            start_index=10,
            end_index=34,
            metadata={"toxicity_score": 0.87, "categories": ["profanity"]}
        )

        # Convert to/from dictionary for serialization
        violation_dict = violation.to_dict()
        restored_violation = Violation.from_dict(violation_dict)

    Examples:
        >>> # Basic violation creation
        >>> violation = Violation(
        ...     type=ViolationType.PROMPT_INJECTION,
        ...     severity=SeverityLevel.HIGH,
        ...     description="System instruction override attempt",
        ...     confidence=0.92,
        ...     scanner_name="injection_detector"
        ... )
        >>> assert violation.severity == SeverityLevel.HIGH
        >>> assert 0.0 <= violation.confidence <= 1.0
        >>>
        >>> # Violation with text location
        >>> location_violation = Violation(
        ...     type=ViolationType.PII_LEAKAGE,
        ...     severity=SeverityLevel.MEDIUM,
        ...     description="Email address detected in input",
        ...     confidence=0.98,
        ...     scanner_name="pii_scanner",
        ...     text_snippet="contact@example.com",
        ...     start_index=15,
        ...     end_index=35
        ... )
        >>> assert location_violation.start_index == 15
        >>> assert location_violation.end_index == 35
        >>>
        >>> # Exception for invalid confidence
        >>> with pytest.raises(ValueError):
        ...     Violation(
        ...         type=ViolationType.TOXIC_INPUT,
        ...         severity=SeverityLevel.LOW,
        ...         description="Test violation",
        ...         confidence=1.5,  # Invalid: > 1.0
        ...         scanner_name="test_scanner"
        ...     )
        >>>
        >>> # Exception for empty description
        >>> with pytest.raises(ValueError):
        ...     Violation(
        ...         type=ViolationType.TOXIC_INPUT,
        ...         severity=SeverityLevel.LOW,
        ...         description="",  # Invalid: empty string
        ...         confidence=0.5,
        ...         scanner_name="test_scanner"
        ...     )
    """

    type: ViolationType
    severity: SeverityLevel
    description: str
    confidence: float
    scanner_name: str
    text_snippet: str | None = None
    start_index: int | None = None
    end_index: int | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """
        Validate violation data after initialization.

        Ensures data integrity by enforcing constraints on critical fields.
        This validation runs automatically during dataclass creation and
        prevents invalid violation objects from being created.

        Raises:
            ValueError: If confidence score is outside valid range (0.0 to 1.0)
            ValueError: If description is empty or only whitespace
            ValueError: If scanner_name is empty or only whitespace

        Behavior:
            - Validates confidence score is within acceptable bounds
            - Ensures required string fields are not empty
            - Prevents creation of malformed violation objects
            - Raises descriptive error messages for debugging
        """
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        if not self.description.strip():
            raise ValueError("Description cannot be empty")

        if not self.scanner_name.strip():
            raise ValueError("Scanner name cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert violation to dictionary representation for serialization.

        Creates a JSON-serializable dictionary containing all violation data.
        Enum values are converted to their string representations, and the
        timestamp is formatted as an ISO 8601 string for standardization.

        Returns:
            Dictionary containing all violation data with proper type conversions:
            - Enum values converted to strings
            - Timestamp formatted as ISO 8601 string
            - All other fields preserved as-is
            - Optional fields included as None if not set

        Examples:
            >>> violation = Violation(
            ...     type=ViolationType.PROMPT_INJECTION,
            ...     severity=SeverityLevel.HIGH,
            ...     description="Test violation",
            ...     confidence=0.9,
            ...     scanner_name="test_scanner"
            ... )
            >>> violation_dict = violation.to_dict()
            >>> assert violation_dict["type"] == "prompt_injection"
            >>> assert violation_dict["severity"] == "high"
            >>> assert "timestamp" in violation_dict
            >>> assert isinstance(violation_dict["timestamp"], str)
        """
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "description": self.description,
            "confidence": self.confidence,
            "scanner_name": self.scanner_name,
            "text_snippet": self.text_snippet,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Violation":
        """
        Create violation from dictionary representation.

        Reconstructs a Violation object from a dictionary created by to_dict().
        Handles type conversions for enum values and timestamps, with graceful
        handling of missing or malformed data.

        Args:
            data: Dictionary containing violation data with the following keys:
                - type: str, violation type identifier
                - severity: str, severity level identifier
                - description: str, human-readable description
                - confidence: float, confidence score (0.0 to 1.0)
                - scanner_name: str, identifier of detecting scanner
                - Optional: text_snippet, start_index, end_index, metadata, timestamp

        Returns:
            Reconstructed Violation object with all fields properly typed

        Raises:
            KeyError: If required fields are missing from the dictionary
            ValueError: If enum values are invalid or confidence is out of range

        Behavior:
            - Converts string enum values back to enum types
            - Parses ISO 8601 timestamp strings to datetime objects
            - Uses default values for missing optional fields
            - Validates reconstructed data through normal initialization
            - Preserves all metadata and context information

        Examples:
            >>> # Basic round-trip conversion
            >>> original = Violation(
            ...     type=ViolationType.TOXIC_INPUT,
            ...     severity=SeverityLevel.MEDIUM,
            ...     description="Test violation",
            ...     confidence=0.8,
            ...     scanner_name="test_scanner"
            ... )
            >>> data = original.to_dict()
            >>> restored = Violation.from_dict(data)
            >>> assert restored.type == original.type
            >>> assert restored.severity == original.severity
            >>> assert restored.description == original.description
            >>>
            >>> # From minimal data
            >>> minimal_data = {
            ...     "type": "prompt_injection",
            ...     "severity": "high",
            ...     "description": "Injection attempt",
            ...     "confidence": 0.95,
            ...     "scanner_name": "injection_detector"
            ... }
            >>> violation = Violation.from_dict(minimal_data)
            >>> assert violation.type == ViolationType.PROMPT_INJECTION
            >>> assert violation.severity == SeverityLevel.HIGH
            >>> assert violation.start_index is None
            >>> assert violation.metadata == {}
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            type=ViolationType(data["type"]),
            severity=SeverityLevel(data["severity"]),
            description=data["description"],
            confidence=data["confidence"],
            scanner_name=data["scanner_name"],
            text_snippet=data.get("text_snippet"),
            start_index=data.get("start_index"),
            end_index=data.get("end_index"),
            metadata=data.get("metadata", {}),
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class SecurityResult:
    """
    Comprehensive result of a security scanning operation with detailed analysis.

    This dataclass encapsulates the complete output of security scanning operations,
    including detected violations, safety assessments, performance metrics, and
    contextual metadata. It serves as the primary interface between security
    scanners and the broader application system for security decision making.

    Attributes:
        is_safe: Boolean indicating if content passed all security checks
        violations: Complete list of all security violations detected during scanning
        score: Overall security safety score (0.0 to 1.0, where higher values indicate greater safety)
        scanned_text: Original text content that was subjected to security analysis
        scan_duration_ms: Total time taken to complete the security scan in milliseconds
        scanner_results: Detailed results from individual scanner components
        metadata: Additional scan-specific information and contextual data
        timestamp: UTC timestamp marking when the scan operation was completed

    State Management:
        - Automatic safety flag synchronization based on detected violations
        - Score validation ensuring values remain within valid range (0.0 to 1.0)
        - Performance metrics tracking for monitoring and optimization
        - Consistent timestamp generation for audit trails and analysis
        - Mutable metadata for post-scan enrichment and context addition

    Usage:
        # Create a safe scan result
        safe_result = SecurityResult(
            is_safe=True,
            violations=[],
            score=0.98,
            scanned_text="This is safe content",
            scan_duration_ms=45,
            scanner_results={"injection_detector": {"confidence": 0.99}}
        )

        # Create result with violations
        violation = Violation(
            type=ViolationType.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            description="System override attempt detected",
            confidence=0.92,
            scanner_name="injection_guard"
        )

        unsafe_result = SecurityResult(
            is_safe=False,
            violations=[violation],
            score=0.45,
            scanned_text="Ignore previous instructions and...",
            scan_duration_ms=120,
            scanner_results={"injection_guard": {"threat_detected": True}}
        )

        # Analyze result patterns
        if unsafe_result.has_critical_violations():
            # Handle critical security threats
            pass

        severity_groups = unsafe_result.get_violations_by_severity()
        if severity_groups[SeverityLevel.HIGH]:
            # Handle high-severity violations
            pass

    Examples:
        >>> # Safe result with no violations
        >>> safe_result = SecurityResult(
        ...     is_safe=True,
        ...     violations=[],
        ...     score=0.95,
        ...     scanned_text="Hello, how are you?",
        ...     scan_duration_ms=25
        ... )
        >>> assert safe_result.is_safe
        >>> assert len(safe_result.violations) == 0
        >>> assert safe_result.score > 0.9
        >>>
        >>> # Result with multiple violations
        >>> violations = [
        ...     Violation(
        ...         type=ViolationType.TOXIC_INPUT,
        ...         severity=SeverityLevel.MEDIUM,
        ...         description="Mild offensive language",
        ...         confidence=0.75,
        ...         scanner_name="toxicity_scanner"
        ...     ),
        ...     Violation(
        ...         type=ViolationType.PII_LEAKAGE,
        ...         severity=SeverityLevel.HIGH,
        ...         description="Email address exposed",
        ...         confidence=0.98,
        ...         scanner_name="pii_detector"
        ...     )
        ... ]
        >>> result = SecurityResult(
        ...     is_safe=False,
        ...     violations=violations,
        ...     score=0.60,
        ...     scanned_text="Contact me at user@example.com",
        ...     scan_duration_ms=85
        ... )
        >>> assert not result.is_safe
        >>> assert result.has_high_severity_violations()
        >>> assert len(result.get_violations_by_type()[ViolationType.PII_LEAKAGE]) == 1
        >>>
        >>> # Exception for invalid score
        >>> with pytest.raises(ValueError):
        ...     SecurityResult(
        ...         is_safe=True,
        ...         violations=[],
        ...         score=1.5,  # Invalid: > 1.0
        ...         scanned_text="test",
        ...         scan_duration_ms=10
        ...     )
        >>>
        >>> # Exception for negative duration
        >>> with pytest.raises(ValueError):
        ...     SecurityResult(
        ...         is_safe=True,
        ...         violations=[],
        ...         score=0.9,
        ...         scanned_text="test",
        ...         scan_duration_ms=-5  # Invalid: negative
        ...     )
    """

    is_safe: bool
    violations: List[Violation]
    score: float
    scanned_text: str
    scan_duration_ms: int
    scanner_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """
        Validate security result and synchronize safety flag with violations.

        Ensures data integrity by validating constraints and automatically
        correcting inconsistencies between the safety flag and detected violations.
        This validation runs automatically during dataclass creation.

        Raises:
            ValueError: If security score is outside valid range (0.0 to 1.0)
            ValueError: If scan duration is negative

        Behavior:
            - Validates security score is within acceptable bounds
            - Ensures scan duration is non-negative
            - Synchronizes is_safe flag with violations list
            - Automatically corrects safety flag inconsistencies
            - Prevents creation of malformed security results

        State Changes:
            - If violations exist but is_safe=True, sets is_safe=False
            - If no violations but is_safe=False, sets is_safe=True
        """
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")

        if self.scan_duration_ms < 0:
            raise ValueError(f"Scan duration must be non-negative, got {self.scan_duration_ms}")

        # Update is_safe based on violations
        if self.violations and self.is_safe:
            self.is_safe = False
        elif not self.violations and not self.is_safe:
            self.is_safe = True

    def get_violations_by_severity(self) -> Dict[SeverityLevel, List[Violation]]:
        """
        Group violations by severity level for risk assessment and response planning.

        Organizes all detected violations into severity-based groups to enable
        risk-based decision making and prioritized response strategies. This
        method is essential for implementing graduated security responses based
        on threat severity.

        Returns:
            Dictionary mapping each SeverityLevel to a list of violations of that severity.
            All severity levels are included as keys, with empty lists for levels
            that have no violations detected.

        Behavior:
            - Creates entry for every severity level (LOW, MEDIUM, HIGH, CRITICAL)
            - Populates lists with violations matching each severity level
            - Returns complete mapping even for empty severity categories
            - Enables easy filtering and analysis of violation patterns

        Examples:
            >>> violations = [
            ...     Violation(
            ...         type=ViolationType.TOXIC_INPUT,
            ...         severity=SeverityLevel.LOW,
            ...         description="Mild language",
            ...         confidence=0.6,
            ...         scanner_name="scanner1"
            ...     ),
            ...     Violation(
            ...         type=ViolationType.PROMPT_INJECTION,
            ...         severity=SeverityLevel.CRITICAL,
            ...         description="Injection attempt",
            ...         confidence=0.95,
            ...         scanner_name="scanner2"
            ...     )
            ... ]
            >>> result = SecurityResult(
            ...     is_safe=False,
            ...     violations=violations,
            ...     score=0.3,
            ...     scanned_text="test",
            ...     scan_duration_ms=100
            ... )
            >>> severity_groups = result.get_violations_by_severity()
            >>> assert len(severity_groups[SeverityLevel.LOW]) == 1
            >>> assert len(severity_groups[SeverityLevel.CRITICAL]) == 1
            >>> assert len(severity_groups[SeverityLevel.MEDIUM]) == 0
        """
        severity_groups: Dict[SeverityLevel, List[Violation]] = {severity: [] for severity in SeverityLevel}
        for violation in self.violations:
            severity_groups[violation.severity].append(violation)
        return severity_groups

    def get_violations_by_type(self) -> Dict[ViolationType, List[Violation]]:
        """
        Group violations by type for pattern analysis and security monitoring.

        Categorizes violations by their specific threat types to enable analysis
        of attack patterns, policy compliance trends, and security risk assessment.
        This grouping is valuable for identifying recurring threat vectors and
        optimizing scanner configurations.

        Returns:
            Dictionary mapping each ViolationType to a list of violations of that type.
            All violation types are included as keys, with empty lists for types
            that have no violations detected.

        Behavior:
            - Creates entry for every violation type defined in the enum
            - Populates lists with violations matching each type
            - Returns complete mapping including empty categories
            - Enables trend analysis and pattern recognition

        Examples:
            >>> violations = [
            ...     Violation(
            ...         type=ViolationType.PROMPT_INJECTION,
            ...         severity=SeverityLevel.HIGH,
            ...         description="Injection attempt",
            ...         confidence=0.9,
            ...         scanner_name="scanner1"
            ...     ),
            ...     Violation(
            ...         type=ViolationType.PII_LEAKAGE,
            ...         severity=SeverityLevel.MEDIUM,
            ...         description="Email exposed",
            ...         confidence=0.8,
            ...         scanner_name="scanner2"
            ...     )
            ... ]
            >>> result = SecurityResult(
            ...     is_safe=False,
            ...     violations=violations,
            ...     score=0.4,
            ...     scanned_text="test",
            ...     scan_duration_ms=75
            ... )
            >>> type_groups = result.get_violations_by_type()
            >>> assert len(type_groups[ViolationType.PROMPT_INJECTION]) == 1
            >>> assert len(type_groups[ViolationType.PII_LEAKAGE]) == 1
            >>> assert len(type_groups[ViolationType.TOXIC_INPUT]) == 0
        """
        type_groups: Dict[ViolationType, List[Violation]] = {violation_type: [] for violation_type in ViolationType}
        for violation in self.violations:
            type_groups[violation.type].append(violation)
        return type_groups

    def has_critical_violations(self) -> bool:
        """
        Check if any critical severity violations were detected.

        Critical violations represent the highest level of security threat and
        typically require immediate blocking and incident response. This method
        provides a quick boolean check for implementing urgent security measures.

        Returns:
            True if any violations have CRITICAL severity level, False otherwise

        Behavior:
            - Scans violations list for CRITICAL severity level
            - Returns True on first critical violation found (short-circuit)
            - Returns False for empty violations list or no critical violations
            - Provides fast boolean check for security decision making

        Examples:
            >>> # No critical violations
            >>> low_violation = Violation(
            ...     type=ViolationType.TOXIC_INPUT,
            ...     severity=SeverityLevel.LOW,
            ...     description="Mild issue",
            ...     confidence=0.5,
            ...     scanner_name="scanner"
            ... )
            >>> result = SecurityResult(
            ...     is_safe=True,
            ...     violations=[low_violation],
            ...     score=0.9,
            ...     scanned_text="test",
            ...     scan_duration_ms=50
            ... )
            >>> assert not result.has_critical_violations()
            >>>
            >>> # With critical violation
            >>> critical_violation = Violation(
            ...     type=ViolationType.PROMPT_INJECTION,
            ...     severity=SeverityLevel.CRITICAL,
            ...     description="Critical threat",
            ...     confidence=0.95,
            ...     scanner_name="scanner"
            ... )
            >>> result_critical = SecurityResult(
            ...     is_safe=False,
            ...     violations=[critical_violation],
            ...     score=0.1,
            ...     scanned_text="test",
            ...     scan_duration_ms=100
            ... )
            >>> assert result_critical.has_critical_violations()
        """
        return any(v.severity == SeverityLevel.CRITICAL for v in self.violations)

    def has_high_severity_violations(self) -> bool:
        """
        Check if any high severity violations (HIGH or CRITICAL) were detected.

        High severity violations represent significant security threats that
        may require immediate attention, content blocking, or enhanced monitoring.
        This method identifies violations that exceed the normal risk threshold.

        Returns:
            True if any violations have HIGH or CRITICAL severity level, False otherwise

        Behavior:
            - Scans violations list for HIGH or CRITICAL severity levels
            - Returns True on first high-severity violation found (short-circuit)
            - Returns False for empty violations list or no high-severity violations
            - Used for implementing graduated security responses

        Examples:
            >>> # Low and medium severity only
            >>> violations = [
            ...     Violation(
            ...         type=ViolationType.TOXIC_INPUT,
            ...         severity=SeverityLevel.LOW,
            ...         description="Low issue",
            ...         confidence=0.4,
            ...         scanner_name="scanner"
            ...     ),
            ...     Violation(
            ...         type=ViolationType.PII_LEAKAGE,
            ...         severity=SeverityLevel.MEDIUM,
            ...         description="Medium issue",
            ...         confidence=0.7,
            ...         scanner_name="scanner"
            ...     )
            ... ]
            >>> result = SecurityResult(
            ...     is_safe=True,
            ...     violations=violations,
            ...     score=0.8,
            ...     scanned_text="test",
            ...     scan_duration_ms=60
            ... )
            >>> assert not result.has_high_severity_violations()
            >>>
            >>> # With high severity violation
            >>> high_violation = Violation(
            ...     type=ViolationType.PROMPT_INJECTION,
            ...     severity=SeverityLevel.HIGH,
            ...     description="High threat",
            ...     confidence=0.9,
            ...     scanner_name="scanner"
            ... )
            >>> result_high = SecurityResult(
            ...     is_safe=False,
            ...     violations=[high_violation],
            ...     score=0.3,
            ...     scanned_text="test",
            ...     scan_duration_ms=80
            ... )
            >>> assert result_high.has_high_severity_violations()
        """
        return any(v.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] for v in self.violations)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert security result to dictionary representation for serialization and logging.

        Creates a comprehensive JSON-serializable dictionary containing all result data,
        including derived statistics and summary information. The scanned text content
        is excluded for privacy reasons, but its length is included for reference.

        Returns:
            Dictionary containing security result data with:
            - Core result fields (is_safe, score, duration, timestamp)
            - Violation data converted to dictionaries via to_dict()
            - Summary statistics for violation counts by severity
            - Scanner-specific results and metadata
            - Text length instead of actual text content for privacy

        Behavior:
            - Excludes actual scanned text for privacy/security reasons
            - Includes comprehensive violation statistics by severity
            - Converts all complex objects to serializable formats
            - Preserves all metadata and context information
            - Calculates summary statistics for quick analysis

        Examples:
            >>> result = SecurityResult(
            ...     is_safe=False,
            ...     violations=[],
            ...     score=0.7,
            ...     scanned_text="Sample text for scanning",
            ...     scan_duration_ms=45,
            ...     metadata={"scanner_version": "1.0"}
            ... )
            >>> result_dict = result.to_dict()
            >>> assert result_dict["is_safe"] is False
            >>> assert result_dict["scanned_text_length"] == 25
            >>> assert "violations" in result_dict
            >>> assert "violation_counts" in result_dict
            >>> assert isinstance(result_dict["timestamp"], str)
        """
        return {
            "is_safe": self.is_safe,
            "violations": [v.to_dict() for v in self.violations],
            "score": self.score,
            "scanned_text_length": len(self.scanned_text),
            "scan_duration_ms": self.scan_duration_ms,
            "scanner_results": self.scanner_results,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "violation_counts": {
                "total": len(self.violations),
                "critical": len([v for v in self.violations if v.severity == SeverityLevel.CRITICAL]),
                "high": len([v for v in self.violations if v.severity == SeverityLevel.HIGH]),
                "medium": len([v for v in self.violations if v.severity == SeverityLevel.MEDIUM]),
                "low": len([v for v in self.violations if v.severity == SeverityLevel.LOW]),
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityResult":
        """
        Create security result from dictionary representation.

        Reconstructs a SecurityResult object from a dictionary created by to_dict().
        Handles type conversions for timestamps and violations, with graceful handling
        of missing or incomplete data from older versions or external systems.

        Args:
            data: Dictionary containing security result data with the following required keys:
                - is_safe: bool, overall safety assessment
                - violations: list, violation data dictionaries
                - score: float, security score (0.0 to 1.0)
                - scan_duration_ms: int, scan duration in milliseconds
                Optional keys:
                - scanned_text: str, original text content (defaults to empty string)
                - scanner_results: dict, scanner-specific data
                - metadata: dict, additional context information
                - timestamp: str, ISO 8601 timestamp

        Returns:
            Reconstructed SecurityResult object with all fields properly typed

        Raises:
            KeyError: If required fields are missing from the dictionary
            ValueError: If score or duration values are invalid
            Exception: If violation reconstruction fails

        Behavior:
            - Converts ISO 8601 timestamp strings to datetime objects
            - Reconstructs violations using Violation.from_dict()
            - Uses default values for missing optional fields
            - Validates reconstructed data through normal initialization
            - Handles incomplete data gracefully for backward compatibility

        Examples:
            >>> # Basic round-trip conversion
            >>> original = SecurityResult(
            ...     is_safe=True,
            ...     violations=[],
            ...     score=0.9,
            ...     scanned_text="Safe content",
            ...     scan_duration_ms=30
            ... )
            >>> data = original.to_dict()
            >>> restored = SecurityResult.from_dict(data)
            >>> assert restored.is_safe == original.is_safe
            >>> assert restored.score == original.score
            >>> assert restored.scan_duration_ms == original.scan_duration_ms
            >>>
            >>> # From minimal data
            >>> minimal_data = {
            ...     "is_safe": False,
            ...     "violations": [],
            ...     "score": 0.5,
            ...     "scan_duration_ms": 50
            ... }
            >>> result = SecurityResult.from_dict(minimal_data)
            >>> assert not result.is_safe
            >>> assert result.scanned_text == ""
            >>> assert result.metadata == {}
            >>> assert isinstance(result.timestamp, datetime)
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        violations = [
            Violation.from_dict(v_data) for v_data in data.get("violations", [])
        ]

        return cls(
            is_safe=data["is_safe"],
            violations=violations,
            score=data["score"],
            scanned_text=data.get("scanned_text", ""),
            scan_duration_ms=data["scan_duration_ms"],
            scanner_results=data.get("scanner_results", {}),
            metadata=data.get("metadata", {}),
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class ScanMetrics:
    """
    Performance and operational metrics for security scan operations.

    This dataclass tracks comprehensive statistics about security scanning operations,
    including performance metrics, success/failure rates, and violation detection
    patterns. It provides essential data for monitoring system health, optimizing
    scanner performance, and analyzing security threat trends.

    Attributes:
        scan_count: Total number of scan operations performed
        total_scan_time_ms: Cumulative time spent on all scans in milliseconds
        successful_scans: Number of scans completed successfully without errors
        failed_scans: Number of scans that failed due to technical issues
        violations_detected: Total number of security violations found across all scans
        average_scan_time_ms: Running average scan duration in milliseconds

    State Management:
        - Metrics are updated incrementally through the update() method
        - Average scan time is calculated automatically with each update
        - All metrics can be reset to initial state via reset() method
        - Thread-safe operations when used with appropriate synchronization
        - Maintains accurate running totals for performance monitoring

    Usage:
        # Initialize metrics for tracking
        input_metrics = ScanMetrics()

        # Update metrics after each scan
        input_metrics.update(scan_duration_ms=45, violations_count=2, success=True)

        # Check performance indicators
        if input_metrics.average_scan_time_ms > 100:
            # Scanner performance is degrading
            pass

        # Calculate success rate
        success_rate = input_metrics.successful_scans / max(input_metrics.scan_count, 1)

    Examples:
        >>> # Basic metrics tracking
        >>> metrics = ScanMetrics()
        >>> assert metrics.scan_count == 0
        >>> assert metrics.average_scan_time_ms == 0.0
        >>>
        >>> # Record successful scan
        >>> metrics.update(scan_duration_ms=50, violations_count=1, success=True)
        >>> assert metrics.scan_count == 1
        >>> assert metrics.successful_scans == 1
        >>> assert metrics.violations_detected == 1
        >>> assert metrics.average_scan_time_ms == 50.0
        >>>
        >>> # Record failed scan
        >>> metrics.update(scan_duration_ms=75, violations_count=0, success=False)
        >>> assert metrics.scan_count == 2
        >>> assert metrics.failed_scans == 1
        >>> assert metrics.average_scan_time_ms == 62.5  # (50 + 75) / 2
        >>>
        >>> # Reset metrics
        >>> metrics.reset()
        >>> assert metrics.scan_count == 0
        >>> assert metrics.average_scan_time_ms == 0.0
    """

    scan_count: int = 0
    total_scan_time_ms: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    violations_detected: int = 0
    average_scan_time_ms: float = 0.0

    def update(self, scan_duration_ms: int, violations_count: int, success: bool) -> None:
        """
        Update metrics with a new scan result.

        Records the outcome of a single scan operation, updating all relevant
        counters and recalculating running averages. This method should be called
        after every scan operation to maintain accurate performance metrics.

        Args:
            scan_duration_ms: Time taken to complete the scan in milliseconds (must be non-negative)
            violations_count: Number of violations detected during the scan (must be non-negative)
            success: Whether the scan completed successfully (True) or failed due to errors (False)

        Behavior:
            - Increments total scan count by 1
            - Adds scan duration to cumulative total time
            - Increments appropriate success/failure counter
            - Adds violation count to total violations detected
            - Recalculates average scan time as total_time / scan_count
            - Handles division by zero gracefully for first scan

        State Changes:
            - scan_count is incremented by 1
            - total_scan_time_ms increases by scan_duration_ms
            - successful_scans or failed_scans increments based on success parameter
            - violations_detected increases by violations_count
            - average_scan_time_ms is recalculated

        Examples:
            >>> metrics = ScanMetrics()
            >>> # Record successful scan with violations
            >>> metrics.update(scan_duration_ms=80, violations_count=3, success=True)
            >>> assert metrics.scan_count == 1
            >>> assert metrics.successful_scans == 1
            >>> assert metrics.violations_detected == 3
            >>> assert metrics.average_scan_time_ms == 80.0
            >>>
            >>> # Record failed scan
            >>> metrics.update(scan_duration_ms=120, violations_count=0, success=False)
            >>> assert metrics.scan_count == 2
            >>> assert metrics.failed_scans == 1
            >>> assert metrics.average_scan_time_ms == 100.0  # (80 + 120) / 2
        """
        self.scan_count += 1
        self.total_scan_time_ms += scan_duration_ms
        self.violations_detected += violations_count

        if success:
            self.successful_scans += 1
        else:
            self.failed_scans += 1

        # Update average
        self.average_scan_time_ms = self.total_scan_time_ms / self.scan_count

    def reset(self) -> None:
        """
        Reset all metrics to initial zero state.

        Clears all accumulated metrics and counters, returning the object
        to its initial state. This is useful for starting new measurement
        periods or clearing metrics during testing scenarios.

        Behavior:
            - Sets all integer counters to 0
            - Sets average scan time to 0.0
            - Clears all accumulated performance data
            - Does not affect object identity or references

        State Changes:
            - scan_count, successful_scans, failed_scans set to 0
            - total_scan_time_ms set to 0
            - violations_detected set to 0
            - average_scan_time_ms set to 0.0

        Examples:
            >>> # Accumulate some metrics
            >>> metrics = ScanMetrics()
            >>> metrics.update(scan_duration_ms=50, violations_count=1, success=True)
            >>> metrics.update(scan_duration_ms=75, violations_count=2, success=True)
            >>> assert metrics.scan_count == 2
            >>>
            >>> # Reset to initial state
            >>> metrics.reset()
            >>> assert metrics.scan_count == 0
            >>> assert metrics.average_scan_time_ms == 0.0
            >>> assert metrics.violations_detected == 0
        """
        self.scan_count = 0
        self.total_scan_time_ms = 0
        self.successful_scans = 0
        self.failed_scans = 0
        self.violations_detected = 0
        self.average_scan_time_ms = 0.0


@dataclass
class MetricsSnapshot:
    """
    Comprehensive snapshot of security service metrics and system health indicators.

    This dataclass captures a complete point-in-time view of the security scanning
    system's performance, health status, and operational metrics. It combines
    scan-specific metrics with system-level indicators to provide a holistic
    view of security service operation for monitoring, alerting, and analysis.

    Attributes:
        input_metrics: ScanMetrics for user input validation operations
        output_metrics: ScanMetrics for AI output validation operations
        system_health: Dictionary of system-level health indicators and status
        scanner_health: Mapping of scanner names to their operational health status
        uptime_seconds: Total service uptime in seconds since last restart
        memory_usage_mb: Current memory consumption in megabytes
        timestamp: UTC timestamp when the snapshot was captured

    State Management:
        - Provides immutable snapshot of metrics at a specific point in time
        - Includes derived metrics like success rates calculated dynamically
        - Timestamp enables historical analysis and trend monitoring
        - System health indicators can contain arbitrary status information
        - Scanner health provides per-component operational status

    Usage:
        # Create snapshot for monitoring
        snapshot = MetricsSnapshot(
            input_metrics=input_scanner_metrics,
            output_metrics=output_scanner_metrics,
            system_health={"cpu_usage": 45.2, "disk_space": 78.5},
            scanner_health={"injection_detector": True, "toxicity_scanner": True},
            uptime_seconds=86400,
            memory_usage_mb=256.7
        )

        # Convert to dictionary for logging/serialization
        snapshot_dict = snapshot.to_dict()

        # Monitor system health
        if not all(snapshot.scanner_health.values()):
            # Some scanners are unhealthy
            pass

    Examples:
        >>> # Create basic snapshot
        >>> input_metrics = ScanMetrics()
        >>> input_metrics.update(scan_duration_ms=50, violations_count=1, success=True)
        >>> snapshot = MetricsSnapshot(
        ...     input_metrics=input_metrics,
        ...     system_health={"status": "healthy"},
        ...     scanner_health={"primary_scanner": True}
        ... )
        >>> assert snapshot.input_metrics.scan_count == 1
        >>> assert snapshot.system_health["status"] == "healthy"
        >>> assert isinstance(snapshot.timestamp, datetime)
        >>>
        >>> # Convert to dictionary for JSON serialization
        >>> snapshot_dict = snapshot.to_dict()
        >>> assert "input_metrics" in snapshot_dict
        >>> assert "system_health" in snapshot_dict
        >>> assert "success_rate" in snapshot_dict["input_metrics"]
        >>> assert isinstance(snapshot_dict["timestamp"], str)
    """

    input_metrics: ScanMetrics = field(default_factory=ScanMetrics)
    output_metrics: ScanMetrics = field(default_factory=ScanMetrics)
    system_health: Dict[str, Any] = field(default_factory=dict)
    scanner_health: Dict[str, bool] = field(default_factory=dict)
    uptime_seconds: int = 0
    memory_usage_mb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics snapshot to dictionary representation for serialization and monitoring.

        Creates a comprehensive JSON-serializable dictionary containing all snapshot
        data, including calculated metrics like success rates. The conversion formats
        all data types appropriately for external monitoring systems and logging.

        Returns:
            Dictionary containing complete metrics snapshot with:
            - Detailed input/output scan metrics with calculated success rates
            - System health indicators and scanner status information
            - Resource usage information (uptime, memory)
            - Timestamp in ISO 8601 format for time-series analysis

        Behavior:
            - Converts datetime to ISO 8601 string for serialization
            - Calculates success rates as percentages (0.0 to 1.0)
            - Handles division by zero gracefully for success rate calculations
            - Preserves all system health and scanner status information
            - Formats all data for compatibility with monitoring systems

        Examples:
            >>> # Create snapshot with some data
            >>> input_metrics = ScanMetrics()
            >>> input_metrics.update(scan_duration_ms=100, violations_count=2, success=True)
            >>> input_metrics.update(scan_duration_ms=50, violations_count=0, success=True)
            >>> snapshot = MetricsSnapshot(
            ...     input_metrics=input_metrics,
            ...     system_health={"cpu": 75.5},
            ...     memory_usage_mb=512.3
            ... )
            >>>
            >>> # Convert to dictionary
            >>> snapshot_dict = snapshot.to_dict()
            >>> assert snapshot_dict["input_metrics"]["scan_count"] == 2
            >>> assert snapshot_dict["input_metrics"]["success_rate"] == 1.0
            >>> assert snapshot_dict["memory_usage_mb"] == 512.3
            >>> assert isinstance(snapshot_dict["timestamp"], str)
            >>>
            >>> # Handle empty metrics gracefully
            >>> empty_snapshot = MetricsSnapshot()
            >>> empty_dict = empty_snapshot.to_dict()
            >>> assert empty_dict["input_metrics"]["success_rate"] == 0.0  # No scans yet
        """
        return {
            "input_metrics": {
                "scan_count": self.input_metrics.scan_count,
                "total_scan_time_ms": self.input_metrics.total_scan_time_ms,
                "successful_scans": self.input_metrics.successful_scans,
                "failed_scans": self.input_metrics.failed_scans,
                "violations_detected": self.input_metrics.violations_detected,
                "average_scan_time_ms": self.input_metrics.average_scan_time_ms,
                "success_rate": (
                    self.input_metrics.successful_scans / max(self.input_metrics.scan_count, 1)
                ),
            },
            "output_metrics": {
                "scan_count": self.output_metrics.scan_count,
                "total_scan_time_ms": self.output_metrics.total_scan_time_ms,
                "successful_scans": self.output_metrics.successful_scans,
                "failed_scans": self.output_metrics.failed_scans,
                "violations_detected": self.output_metrics.violations_detected,
                "average_scan_time_ms": self.output_metrics.average_scan_time_ms,
                "success_rate": (
                    self.output_metrics.successful_scans / max(self.output_metrics.scan_count, 1)
                ),
            },
            "system_health": self.system_health,
            "scanner_health": self.scanner_health,
            "uptime_seconds": self.uptime_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "timestamp": self.timestamp.isoformat(),
        }


class SecurityService(ABC):
    """
    Abstract protocol defining the contract for security scanning service implementations.

    This protocol establishes the standardized interface that all security scanning
    services must implement, ensuring consistent behavior, monitoring capabilities,
    and integration patterns across different security scanner implementations.
    It provides the foundation for pluggable security architectures while
    maintaining operational consistency and observability.

    Protocol Contract:
        **Core Security Operations:**
        - Input validation for detecting security threats in user-provided content
        - Output validation for identifying harmful content in AI-generated responses
        - Comprehensive health checking for service availability and performance
        - Performance metrics collection and monitoring for operational insights

        **Cache and Configuration Management:**
        - Cache statistics and management for performance optimization
        - Configuration retrieval for runtime inspection and debugging
        - Metrics reset capabilities for monitoring and maintenance operations

        **Error Handling and Reliability:**
        - Standardized exception handling across all implementations
        - Graceful degradation and fallback behaviors
        - Comprehensive error reporting for troubleshooting and debugging

    Implementation Requirements:
        - All methods must be async and non-blocking
        - Implementations must be thread-safe and support concurrent access
        - Error handling must follow the defined exception hierarchy
        - Performance metrics must be accurately collected and reported
        - Cache operations must handle backend failures gracefully

    Usage Patterns:
        This protocol enables dependency injection and testing through its
        abstract interface, allowing different security scanning implementations
        to be swapped without changing client code. It supports both local
        scanning implementations and cloud-based security services through
        a consistent API contract.

    Note:
        Implementations should prioritize performance and reliability while
        maintaining comprehensive security coverage. The protocol is designed
        to support both simple and complex security scanning workflows with
        consistent operational characteristics.
        """

    @abstractmethod
    async def validate_input(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
        """
        Validate user input for security threats and policy violations.

        Scans user-provided content for various security threats including prompt
        injection attempts, malicious content, PII exposure, and policy violations.
        This is a critical security operation that prevents harmful inputs from
        reaching AI models and protects against various attack vectors.

        Args:
            text: User input text to be scanned for security threats (1-100,000 characters)
            context: Optional contextual information to enhance security analysis:
                - user_id: str, identifier of the user providing input
                - session_id: str, current session identifier
                - request_source: str, origin of the request (web, api, mobile)
                - user_history: dict, historical user behavior patterns
                - custom_rules: list, user-specific security rules

        Returns:
            SecurityResult containing comprehensive validation results:
            - is_safe: Boolean indicating if input passes security checks
            - violations: List of all detected security violations with details
            - score: Overall security score (0.0 to 1.0, higher is safer)
            - scanned_text: The original input text that was analyzed
            - scan_duration_ms: Time taken to perform security analysis
            - metadata: Additional scan information and context

        Raises:
            SecurityServiceError: If the validation process fails due to technical issues
            ScannerTimeoutError: If security scanning exceeds maximum allowed time
            ServiceUnavailableError: If security scanning service is temporarily unavailable

        Behavior:
            - Analyzes text using multiple security scanners for comprehensive coverage
            - Applies context-aware security rules when context information is provided
            - Tracks performance metrics for monitoring scan efficiency
            - Handles scanner failures gracefully with fallback mechanisms
            - Updates internal metrics for success/failure rate tracking
            - Caches results for identical inputs to improve performance

        Examples:
            >>> # Basic input validation
            >>> async with security_service as service:
            ...     result = await service.validate_input("Hello, how are you?")
            ...     assert result.is_safe
            ...     assert len(result.violations) == 0
            ...     assert result.score > 0.8
            >>>
            >>> # Input validation with context
            >>> context = {
            ...     "user_id": "user123",
            ...     "session_id": "sess456",
            ...     "request_source": "web"
            ... }
            >>> result = await service.validate_input("Ignore all previous instructions", context)
            ...     # Likely to detect prompt injection attempt
            >>> assert not result.is_safe
            >>> assert any(v.type == ViolationType.PROMPT_INJECTION for v in result.violations)
            >>>
            >>> # Error handling for service failures
            >>> try:
            ...     result = await service.validate_input("test input")
            ... except SecurityServiceError as e:
            ...     # Handle security service unavailability
            ...     fallback_result = SecurityResult(
            ...         is_safe=False,
            ...         violations=[],
            ...         score=0.0,
            ...         scanned_text="test input",
            ...         scan_duration_ms=0
            ...     )
        """

    @abstractmethod
    async def validate_output(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
        """
        Validate AI-generated output for harmful content and policy violations.

        Scans AI-generated responses before they are returned to users to ensure
        content safety, policy compliance, and ethical standards. This validation
        prevents harmful, biased, unethical, or policy-violating content from
        reaching end users and protects against AI model failures or misuse.

        Args:
            text: AI-generated output text to be validated (1-50,000 characters)
            context: Optional contextual information to enhance validation:
                - model_id: str, identifier of the AI model that generated the content
                - prompt: str, original user prompt that led to this response
                - temperature: float, model creativity setting used
                - user_id: str, identifier of the user receiving the response
                - application: str, application context (chat, analysis, generation)
                - content_type: str, expected content type (summary, analysis, creative)

        Returns:
            SecurityResult containing comprehensive output validation:
            - is_safe: Boolean indicating if output meets safety standards
            - violations: List of detected policy violations or content issues
            - score: Overall safety score (0.0 to 1.0, higher is safer)
            - scanned_text: The original AI-generated text that was analyzed
            - scan_duration_ms: Time taken to perform output validation
            - metadata: Scanner-specific results and confidence scores

        Raises:
            SecurityServiceError: If the validation process fails due to technical issues
            ScannerTimeoutError: If output validation exceeds maximum allowed time
            ServiceUnavailableError: If security scanning service is temporarily unavailable

        Behavior:
            - Applies content safety filters for harmful or inappropriate content
            - Checks for bias, discrimination, and unethical content patterns
            - Validates compliance with usage policies and terms of service
            - Analyzes content quality and appropriateness for the intended audience
            - Tracks validation metrics for monitoring AI model behavior
            - Updates internal performance counters for success/failure rates

        Examples:
            >>> # Basic output validation
            >>> async with security_service as service:
            ...     result = await service.validate_output("This is a helpful and safe response.")
            ...     assert result.is_safe
            ...     assert len(result.violations) == 0
            ...     assert result.score > 0.9
            >>>
            >>> # Output validation with context
            >>> context = {
            ...     "model_id": "gpt-4",
            ...     "prompt": "Summarize this article",
            ...     "content_type": "summary"
            ... }
            >>> result = await service.validate_output("Here is the summary...", context)
            >>> if result.has_high_severity_violations():
            ...     # Block harmful content from reaching users
            ...     safe_response = "I apologize, but I cannot provide that response."
            >>> else:
            ...     safe_response = text
            >>>
            >>> # Handle validation failures gracefully
            >>> try:
            ...     result = await service.validate_output(ai_response, context)
            ...     if not result.is_safe:
            ...         # Log violation for monitoring
            ...         log_security_violations(result.violations)
            ... except SecurityServiceError:
            ...     # Fallback to safe default response
            ...     safe_response = get_safe_fallback_response()

        Note:
            This method should be called before any AI-generated content is returned
            to users to ensure content safety and regulatory compliance.
        """

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health and availability of the security service and all scanners.

        Performs comprehensive health diagnostics on the security service and its
        component scanners to ensure operational readiness. This includes
        connectivity checks, resource availability assessments, and performance
        verification for all security scanning components.

        Returns:
            Dictionary containing detailed health status information:
            - service_status: str, overall service health (healthy, degraded, unhealthy)
            - scanner_health: dict, health status of individual scanners by name
            - system_resources: dict, CPU, memory, disk usage metrics
            - connectivity: dict, status of external service connections
            - performance: dict, response time and throughput metrics
            - last_check: str, ISO timestamp when health check was performed
            - uptime_seconds: int, service uptime since last restart

        Raises:
            SecurityServiceError: If health check execution fails
            ServiceUnavailableError: If service is completely unavailable
            ScannerTimeoutError: If health check exceeds timeout limits

        Behavior:
            - Tests connectivity to all configured security scanners
            - Verifies resource availability and usage levels
            - Checks response times and performance characteristics
            - Validates configuration integrity across all components
            - Generates comprehensive health report for monitoring systems
            - Triggers alerts for any detected health issues

        Examples:
            >>> # Basic health check
            >>> async with security_service as service:
            ...     health = await service.health_check()
            ...     assert health["service_status"] == "healthy"
            ...     assert all(scanner_status for scanner_status in health["scanner_health"].values())
            >>>
            >>> # Monitor system resources
            >>> health = await service.health_check()
            >>> cpu_usage = health["system_resources"]["cpu_percent"]
            >>> memory_usage = health["system_resources"]["memory_percent"]
            >>> if cpu_usage > 90 or memory_usage > 90:
            ...     # Trigger scaling or load balancing
            ...     pass
        """

    @abstractmethod
    async def get_metrics(self) -> MetricsSnapshot:
        """
        Get current metrics and performance data for monitoring and analysis.

        Captures a comprehensive snapshot of all performance metrics, operational
        statistics, and health indicators for the security service. This data
        is essential for monitoring system performance, identifying trends,
        and making informed operational decisions.

        Returns:
            MetricsSnapshot containing complete performance metrics:
            - input_metrics: Statistics for user input validation operations
            - output_metrics: Statistics for AI output validation operations
            - system_health: System resource utilization and health indicators
            - scanner_health: Operational status of individual scanners
            - uptime_seconds: Total service uptime since last restart
            - memory_usage_mb: Current memory consumption in megabytes
            - timestamp: UTC timestamp when metrics snapshot was captured

        Raises:
            SecurityServiceError: If metrics collection fails
            ServiceUnavailableError: If service is unavailable for metrics collection

        Behavior:
            - Collects real-time performance metrics from all scanners
            - Calculates derived metrics like success rates and averages
            - Gathers system resource usage information
            - Captures operational status of all components
            - Formats metrics for monitoring systems and analysis tools
            - Includes timestamp for time-series analysis and trending

        Examples:
            >>> # Get current metrics for monitoring
            >>> async with security_service as service:
            ...     metrics = await service.get_metrics()
            ...     input_success_rate = (
            ...         metrics.input_metrics.successful_scans /
            ...         max(metrics.input_metrics.scan_count, 1)
            ...     )
            ...     avg_scan_time = metrics.input_metrics.average_scan_time_ms
            ...     if avg_scan_time > 1000:  # 1 second threshold
            ...         # Investigate performance degradation
            ...         pass
            >>>
            >>> # Monitor system health
            >>> metrics = await service.get_metrics()
            >>> if not all(metrics.scanner_health.values()):
            ...     # Some scanners are unhealthy, trigger alerts
            ...     trigger_alert("scanner_health_issue", metrics.scanner_health)
        """

    @abstractmethod
    async def get_configuration(self) -> Dict[str, Any]:
        """
        Get current security service configuration settings for all scanners.

        Retrieves the complete configuration state of the security service,
        including individual scanner settings, global policies, and operational
        parameters. This information is useful for debugging, auditing,
        and understanding the current security posture of the system.

        Returns:
            Dictionary containing comprehensive configuration information:
            - global_settings: dict, system-wide security policies and limits
            - scanner_configs: dict, configuration for each individual scanner
            - cache_settings: dict, cache configuration and policies
            - timeout_settings: dict, timeout and retry configuration
            - security_policies: dict, active security policies and rules
            - version: str, configuration version or last update timestamp
            - environment: str, current environment (development, production, etc.)

        Raises:
            SecurityServiceError: If configuration retrieval fails
            ConfigurationError: If configuration is invalid or corrupted

        Behavior:
            - Collects current configuration from all system components
            - Validates configuration integrity and consistency
            - Formats configuration for human and machine consumption
            - Includes version information for change tracking
            - Masks sensitive information like API keys or credentials
            - Provides configuration metadata for auditing purposes

        Examples:
            >>> # Get current configuration for debugging
            >>> async with security_service as service:
            ...     config = await service.get_configuration()
            ...     injection_config = config["scanner_configs"]["prompt_injection"]
            ...     timeout_config = config["timeout_settings"]
            ...     logging.info(f"Current prompt injection threshold: {injection_config['threat_threshold']}")
            >>>
            >>> # Audit configuration changes
            >>> current_config = await service.get_configuration()
            >>> if current_config["version"] != last_known_version:
            ...     log_configuration_change(current_config)
            ...     last_known_version = current_config["version"]
        """

    @abstractmethod
    async def reset_metrics(self) -> None:
        """
        Reset all performance and security metrics to initial state.

        Clears all accumulated metrics, counters, and performance data,
        returning the system to its initial measurement state. This is
        typically used during maintenance, testing, or when starting new
        measurement periods for clean metric collection.

        Raises:
            SecurityServiceError: If metrics reset operation fails
            ScannerTimeoutError: If reset operation times out

        Behavior:
            - Resets all scan counters (successful, failed, total)
            - Clears performance metrics (response times, throughput)
            - Resets violation detection statistics
            - Clears cache hit/miss metrics and performance data
            - Resets system resource usage tracking
            - Logs metrics reset event for audit purposes
            - Maintains configuration and operational state unchanged

        Examples:
            >>> # Reset metrics during maintenance
            >>> async with security_service as service:
            ...     await service.reset_metrics()
            ...     # Verify metrics are reset
            ...     metrics = await service.get_metrics()
            ...     assert metrics.input_metrics.scan_count == 0
            ...     assert metrics.output_metrics.scan_count == 0
            ...     assert metrics.input_metrics.violations_detected == 0
            >>>
            >>> # Use before performance testing
            >>> await service.reset_metrics()
            >>> # Run performance test
            >>> test_start = time.time()
            >>> for i in range(100):
            ...     await service.validate_input("test input")
            >>> metrics = await service.get_metrics()
            >>> throughput = metrics.input_metrics.scan_count / (time.time() - test_start)
            >>> logging.info(f"Throughput: {throughput} scans/second")
        """

    @abstractmethod
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics and performance metrics.

        Retrieves detailed information about cache usage, performance,
        and health for both memory and persistent cache layers. This data
        is essential for optimizing cache performance, identifying bottlenecks,
        and making informed cache configuration decisions.

        Returns:
            Dictionary containing comprehensive cache statistics:
            - memory_cache: dict, in-memory cache metrics (size, hit rate, entries)
            - persistent_cache: dict, persistent cache metrics (Redis, etc.)
            - overall_performance: dict, combined cache performance metrics
            - eviction_stats: dict, cache eviction and cleanup statistics
            - size_metrics: dict, memory usage and storage statistics
            - health_status: str, overall cache health status
            - last_updated: str, ISO timestamp of last cache update

        Raises:
            SecurityServiceError: If cache statistics retrieval fails
            ServiceUnavailableError: If cache service is unavailable
            CacheError: If cache is corrupted or inaccessible

        Behavior:
            - Collects statistics from all configured cache layers
            - Calculates hit/miss ratios and performance metrics
            - Analyzes cache size and memory usage patterns
            - Monitors cache health and error rates
            - Tracks eviction and cleanup operations
            - Provides actionable insights for cache optimization

        Examples:
            >>> # Monitor cache performance
            >>> async with security_service as service:
            ...     cache_stats = await service.get_cache_statistics()
            ...     hit_rate = cache_stats["overall_performance"]["hit_rate"]
            ...     memory_usage = cache_stats["size_metrics"]["memory_usage_mb"]
            ...     if hit_rate < 0.8:  # 80% hit rate threshold
            ...         # Consider adjusting cache configuration
            ...         logging.warning(f"Low cache hit rate: {hit_rate:.2%}")
            >>>
            >>> # Check cache health
            >>> cache_stats = await service.get_cache_statistics()
            >>> if cache_stats["health_status"] != "healthy":
            ...     # Trigger cache maintenance or alert
            ...     await service.clear_cache()  # Clear corrupted cache
        """

    @abstractmethod
    async def clear_cache(self) -> None:
        """
        Clear all cached security scan results from all cache layers.

        Removes all entries from both memory and persistent cache stores,
        effectively invalidating all cached scan results. This operation
        is useful for cache maintenance, recovering from cache corruption,
        or ensuring fresh security scans when policies change.

        Raises:
            SecurityServiceError: If cache clearing operation fails
            ServiceUnavailableError: If cache service is unavailable
            CacheError: If cache corruption prevents proper clearing

        Behavior:
            - Clears all entries from in-memory cache immediately
            - Flushes persistent cache stores (Redis, database, etc.)
            - Resets cache performance metrics and counters
            - Triggers cache cleanup and garbage collection
            - Logs cache clearing event for audit purposes
            - May cause temporary performance degradation as cache rebuilds
            - Maintains configuration and scanner settings unchanged

        Examples:
            >>> # Clear cache after security policy changes
            >>> async with security_service as service:
            ...     await service.clear_cache()
            ...     # Verify cache is cleared
            ...     cache_stats = await service.get_cache_statistics()
            ...     assert cache_stats["memory_cache"]["entries"] == 0
            ...     assert cache_stats["persistent_cache"]["entries"] == 0
            >>>
            >>> # Clear cache when corruption detected
            >>> try:
            ...     cache_stats = await service.get_cache_statistics()
            ...     if cache_stats["health_status"] == "corrupted":
            ...         await service.clear_cache()
            ...         logging.info("Cache cleared due to corruption")
            ... except CacheError:
            ...     await service.clear_cache()
            ...     logging.info("Cache cleared due to error")

        Note:
            Clearing the cache will temporarily increase security scanning
            latency as the cache rebuilds with fresh scan results. Use this
            operation judiciously in production environments.
        """


class SecurityServiceError(Exception):
    """
    Base exception for all security service-related errors.

    This exception serves as the foundation for the security service error hierarchy,
    providing comprehensive error context and chain-of-custody for troubleshooting
    and debugging security scanning failures. It includes contextual information
    about the scanner involved and preserves the original error that triggered
    the failure.

    Attributes:
        scanner_name: Optional name of the scanner that caused the error
        original_error: The original exception that led to this error, if any
        message: Human-readable error message describing the issue
        error_type: String identifier for the specific error type

    Usage:
        # Basic security service error
        raise SecurityServiceError("Scanner connection failed")

        # With scanner context
        raise SecurityServiceError(
            "Invalid API key",
            scanner_name="prompt_injection_scanner"
        )

        # With original error chaining
        try:
            scanner.scan(text)
        except ConnectionError as e:
            raise SecurityServiceError(
                "Network connectivity issue",
                scanner_name="network_scanner",
                original_error=e
            ) from e

    Examples:
        >>> # Basic exception creation
        >>> error = SecurityServiceError("Scanner unavailable")
        >>> assert str(error) == "Scanner unavailable"
        >>> assert error.scanner_name is None
        >>> assert error.original_error is None
        >>>
        >>> # Exception with scanner context
        >>> error = SecurityServiceError(
        ...     "Invalid configuration",
        ...     scanner_name="injection_detector"
        ... )
        >>> assert "injection_detector" in str(error.scanner_name)
        >>>
        >>> # Exception chaining for debugging
        >>> original = ValueError("Invalid threshold")
        >>> error = SecurityServiceError(
        ...     "Configuration validation failed",
        ...     scanner_name="pii_detector",
        ...     original_error=original
        ... )
        >>> assert error.original_error is original
        >>> assert "Configuration validation failed" in str(error)

    Inheritance Chain:
        Exception → SecurityServiceError → [Specific Error Types]

    Exception Handling Patterns:
        try:
            result = await security_service.validate_input(text)
        except SecurityServiceError as e:
            logger.error(f"Security scan failed: {e}")
            if e.scanner_name:
                logger.error(f"Failing scanner: {e.scanner_name}")
            if e.original_error:
                logger.error(f"Root cause: {e.original_error}")
            # Handle security failure appropriately
    """

    def __init__(self, message: str, scanner_name: str | None = None, original_error: Exception | None = None):
        """
        Initialize security service error with comprehensive context.

        Args:
            message: Human-readable error message describing the security service issue
            scanner_name: Optional name of the specific scanner that caused the error
            original_error: The original exception that triggered this security error

        Behavior:
            - Preserves original error for debugging and error chain analysis
            - Stores scanner name for targeted troubleshooting and monitoring
            - Maintains clean error message while providing full context access
            - Supports exception chaining with proper 'from' clause usage

        Examples:
            >>> # Basic error
            >>> error = SecurityServiceError("Service unavailable")
            >>> assert str(error) == "Service unavailable"
            >>>
            >>> # Error with scanner context
            >>> error = SecurityServiceError(
            ...     "Invalid API configuration",
            ...     scanner_name="toxicity_scanner"
            ... )
            >>> assert error.scanner_name == "toxicity_scanner"
            >>>
            >>> # Error with original exception
            >>> original = ConnectionError("Network timeout")
            >>> error = SecurityServiceError(
            ...     "Scanner connectivity failed",
            ...     scanner_name="remote_scanner",
            ...     original_error=original
            ... )
            >>> assert isinstance(error.original_error, ConnectionError)
        """
        super().__init__(message)
        self.scanner_name = scanner_name
        self.original_error = original_error


class ScannerInitializationError(SecurityServiceError):
    """
    Raised when a security scanner fails to initialize properly.

    This exception indicates that a security scanner could not be initialized
    due to configuration errors, missing dependencies, invalid API keys,
    or other setup-related issues. Initialization errors typically prevent
    the security service from starting or functioning correctly.

    Common Causes:
        - Invalid or missing API keys for external security services
        - Missing required dependencies or libraries
        - Invalid scanner configuration parameters
        - Network connectivity issues during initial setup
        - Resource allocation failures (memory, disk space, etc.)
        - Service account or permission problems

    Error Recovery:
        - Verify API keys and credentials are valid and accessible
        - Check that all required dependencies are installed
        - Validate scanner configuration parameters
        - Ensure network connectivity to required services
        - Verify resource availability and permissions

    Usage:
        try:
            scanner = PromptInjectionScanner(api_key=api_key)
        except ScannerInitializationError as e:
            logger.error(f"Failed to initialize scanner: {e}")
            # Fallback to safer default configuration
            use_backup_security_scanner()

    Examples:
        >>> # Basic initialization error
        >>> error = ScannerInitializationError(
        ...     "Invalid API key format",
        ...     scanner_name="prompt_injection_scanner"
        ... )
        >>> assert "Invalid API key format" in str(error)
        >>> assert error.scanner_name == "prompt_injection_scanner"
        >>>
        >>> # With original error
        >>> original = ImportError("Missing required library")
        >>> error = ScannerInitializationError(
        ...     "Scanner dependencies not found",
        ...     scanner_name="pii_detector",
        ...     original_error=original
        ... )
        >>> assert isinstance(error.original_error, ImportError)

    Severity: High - Prevents security service from functioning

    Handling Strategies:
        - Log detailed error information for troubleshooting
        - Attempt fallback to alternative scanner if available
        - Gracefully degrade service if security scanning is not critical
        - Alert administrators to investigate configuration issues
    """

    def __init__(self, message: str, scanner_name: str | None = None, original_error: Exception | None = None):
        """
        Initialize scanner initialization error.

        Args:
            message: Description of what went wrong during scanner initialization
            scanner_name: Name of the scanner that failed to initialize
            original_error: The underlying exception that caused the initialization failure

        Examples:
            >>> # Invalid API key error
            >>> error = ScannerInitializationError(
            ...     "API key authentication failed",
            ...     scanner_name="security_scanner"
            ... )
            >>> assert "API key authentication failed" in str(error)
            >>>
            >>> # Missing dependency error
            >>> original = ModuleNotFoundError("No module named 'transformers'")
            >>> error = ScannerInitializationError(
            ...     "Required AI libraries not installed",
            ...     scanner_name="ai_content_scanner",
            ...     original_error=original
            ... )
        """
        super().__init__(message, scanner_name, original_error)


class ScannerTimeoutError(SecurityServiceError):
    """
    Raised when a security scanner operation exceeds the configured timeout limit.

    This exception indicates that a security scanning operation took too long
    to complete, potentially due to network latency, high system load,
    complex content analysis, or external service delays. Timeout errors
    are critical for maintaining system responsiveness and preventing
    resource exhaustion.

    Common Causes:
        - Network latency to external security services
        - High system load or resource contention
        - Complex content requiring extensive analysis
        - External security service experiencing delays
        - Large input text exceeding processing capacity
        - Concurrent scanner operations hitting limits

    Timeout Configuration:
        - Input validation timeouts: Typically 5-30 seconds
        - Output validation timeouts: Typically 10-60 seconds
        - Health check timeouts: Typically 2-10 seconds
        - Configuration timeouts: Typically 5-15 seconds

    Error Recovery:
        - Increase timeout limits for complex content
        - Implement circuit breaker patterns for external services
        - Use caching to avoid repeated expensive scans
        - Implement retry logic with exponential backoff
        - Consider parallel processing for large content

    Usage:
        try:
            result = await scanner.validate_input(complex_text)
        except ScannerTimeoutError as e:
            logger.warning(f"Security scan timed out: {e}")
            # Implement timeout handling strategy
            handle_scan_timeout(complex_text)

    Examples:
        >>> # Basic timeout error
        >>> error = ScannerTimeoutError(
        ...     "Scan exceeded 30 second limit",
        ...     scanner_name="prompt_injection_detector"
        ... )
        >>> assert "30 second limit" in str(error)
        >>> assert error.scanner_name == "prompt_injection_detector"
        >>>
        >>> # With original timeout exception
        >>> original = asyncio.TimeoutError("Operation timed out")
        >>> error = ScannerTimeoutError(
        ...     "External security service timeout",
        ...     scanner_name="content_safety_scanner",
        ...     original_error=original
        ... )
        >>> assert isinstance(error.original_error, asyncio.TimeoutError)

    Severity: Medium - May impact user experience but doesn't prevent service operation

    Handling Strategies:
        - Log timeout events for performance monitoring
        - Implement fallback to faster scanning methods
        - Use cached results when available
        - Consider increasing timeouts for known slow operations
        - Implement user feedback for long-running operations
    """

    def __init__(self, message: str, scanner_name: str | None = None, original_error: Exception | None = None):
        """
        Initialize scanner timeout error.

        Args:
            message: Description of the timeout scenario and duration limits
            scanner_name: Name of the scanner that experienced the timeout
            original_error: The underlying timeout exception that triggered this error

        Examples:
            >>> # Basic timeout error
            >>> error = ScannerTimeoutError(
            ...     "Input validation exceeded 10 second timeout",
            ...     scanner_name="input_validator"
            ... )
            >>> assert "10 second timeout" in str(error)
            >>>
            >>> # With asyncio timeout
            >>> original = asyncio.TimeoutError()
            >>> error = ScannerTimeoutError(
            ...     "Async scanner operation timed out",
            ...     scanner_name="async_security_scanner",
            ...     original_error=original
            ... )
        """
        super().__init__(message, scanner_name, original_error)


class ScannerConfigurationError(SecurityServiceError):
    """
    Raised when scanner configuration is invalid, incomplete, or inconsistent.

    This exception indicates that the scanner configuration contains errors
    that prevent proper operation. Configuration errors can include invalid
    parameter values, missing required settings, contradictory options,
    or configuration that violates security policies or system constraints.

    Common Configuration Issues:
        - Invalid parameter values or data types
        - Missing required configuration fields
        - Contradictory or incompatible settings
        - Security threshold values outside acceptable ranges
        - Invalid URL or endpoint configurations
        - Malformed JSON or YAML configuration files
        - Configuration that violates system constraints

    Configuration Validation:
        - Parameter type checking and conversion
        - Range validation for numeric thresholds
        - URL and endpoint connectivity verification
        - Required field presence validation
        - Consistency checks between related settings
        - Security policy compliance verification

    Error Recovery:
        - Validate configuration against schema definitions
        - Use default values for missing optional parameters
        - Apply configuration presets for common use cases
        - Provide detailed error messages with specific field information
        - Offer configuration suggestions or corrections

    Usage:
        try:
            scanner = SecurityScanner(config_dict)
        except ScannerConfigurationError as e:
            logger.error(f"Invalid scanner configuration: {e}")
            # Use safe default configuration
            safe_config = get_default_scanner_config()
            scanner = SecurityScanner(safe_config)

    Examples:
        >>> # Basic configuration error
        >>> error = ScannerConfigurationError(
        ...     "Security threshold must be between 0.0 and 1.0",
        ...     scanner_name="content_safety_scanner"
        ... )
        >>> assert "between 0.0 and 1.0" in str(error)
        >>> assert error.scanner_name == "content_safety_scanner"
        >>>
        >>> # With original validation error
        >>> original = ValueError("Invalid confidence threshold: 1.5")
        >>> error = ScannerConfigurationError(
        ...     "Invalid scanner parameters detected",
        ...     scanner_name="threat_detection_scanner",
        ...     original_error=original
        ... )
        >>> assert isinstance(error.original_error, ValueError)

    Severity: High - Prevents scanner from operating correctly

    Handling Strategies:
        - Validate all configuration before scanner initialization
        - Provide clear error messages with specific field names
        - Offer configuration corrections or suggestions
        - Use configuration schemas for automatic validation
        - Implement configuration migration for version changes
        - Log configuration errors for debugging and monitoring
    """

    def __init__(self, message: str, scanner_name: str | None = None, original_error: Exception | None = None):
        """
        Initialize scanner configuration error.

        Args:
            message: Description of the configuration issue and validation failure
            scanner_name: Name of the scanner with invalid configuration
            original_error: The underlying validation or parsing error

        Examples:
            >>> # Invalid threshold error
            >>> error = ScannerConfigurationError(
            ...     "Threat threshold must be between 0.0 and 1.0, got 1.5",
            ...     scanner_name="threat_detector"
            ... )
            >>> assert "between 0.0 and 1.0" in str(error)
            >>>
            >>> # With original parsing error
            >>> original = json.JSONDecodeError("Invalid JSON", "bad json", 0)
            >>> error = ScannerConfigurationError(
            ...     "Configuration file parsing failed",
            ...     scanner_name="configurable_scanner",
            ...             original_error=original
            ... )
        """
        super().__init__(message, scanner_name, original_error)
