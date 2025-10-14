"""
Test suite for Violation dataclass representing security violation details.

This module tests the Violation dataclass that encapsulates comprehensive
information about detected security threats, including type classification,
severity assessment, confidence scoring, and contextual location data.

Test Strategy:
    - Verify dataclass initialization and field assignments
    - Test validation logic in __post_init__ for data integrity
    - Validate serialization/deserialization (to_dict/from_dict)
    - Test optional field handling and defaults
    - Ensure timestamp generation and metadata management
"""

import pytest
from datetime import datetime, UTC
from app.infrastructure.security.llm.protocol import (
    Violation,
    ViolationType,
    SeverityLevel
)


class TestViolationInitialization:
    """
    Test suite for Violation dataclass initialization and validation.
    
    Scope:
        - Required field initialization (type, severity, description, confidence, scanner_name)
        - Optional field handling (text_snippet, start_index, end_index, metadata)
        - Automatic timestamp generation
        - Data validation in __post_init__
        
    Business Critical:
        Proper violation initialization ensures accurate security threat
        documentation for logging, reporting, and incident response.
        
    Test Coverage:
        - Successful initialization with valid data
        - Validation failures for invalid confidence scores
        - Validation failures for empty required fields
        - Default value handling for optional fields
    """
    
    def test_violation_initialization_with_required_fields_only(self):
        """
        Test that Violation initializes successfully with only required fields.

        Verifies:
            Violation can be created with minimal required parameters and
            optional fields default to appropriate None or empty values

        Business Impact:
            Enables simple violation creation for scanners that only provide
            basic threat classification without detailed location context

        Scenario:
            Given: Required violation parameters (type, severity, description, confidence, scanner_name)
            When: Creating Violation with only required fields
            Then: Violation instance is created successfully
            And: Optional fields (text_snippet, indices, metadata) are None or empty
            And: Timestamp is automatically generated

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Required violation parameters
        violation_type = ViolationType.PROMPT_INJECTION
        severity = SeverityLevel.HIGH
        description = "System instruction override attempt detected"
        confidence = 0.92
        scanner_name = "injection_detector"

        # When: Creating Violation with only required fields
        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name
        )

        # Then: Violation instance is created successfully
        assert violation is not None
        assert isinstance(violation, Violation)

        # And: Required fields are correctly set
        assert violation.type == violation_type
        assert violation.severity == severity
        assert violation.description == description
        assert violation.confidence == confidence
        assert violation.scanner_name == scanner_name

        # And: Optional fields default to None or empty values
        assert violation.text_snippet is None
        assert violation.start_index is None
        assert violation.end_index is None
        assert violation.metadata == {}

        # And: Timestamp is automatically generated
        assert violation.timestamp is not None
        assert isinstance(violation.timestamp, datetime)
        # Note: Implementation uses datetime.utcnow() which creates naive datetime
    
    def test_violation_initialization_with_all_fields(self):
        """
        Test that Violation initializes successfully with all fields provided.

        Verifies:
            Violation captures complete threat context including location data
            and scanner-specific metadata when available

        Business Impact:
            Supports comprehensive violation reporting for detailed security
            analysis, debugging, and evidence collection

        Scenario:
            Given: Complete violation parameters including optional fields
            When: Creating Violation with all fields specified
            Then: Violation instance is created with all data preserved
            And: All fields are accessible and correctly typed

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Complete violation parameters including optional fields
        violation_type = ViolationType.PII_LEAKAGE
        severity = SeverityLevel.MEDIUM
        description = "Email address detected in user input"
        confidence = 0.87
        scanner_name = "pii_scanner"
        text_snippet = "Contact me at user@example.com for more info"
        start_index = 15
        end_index = 35
        metadata = {"detection_method": "regex_pattern", "pattern_used": "email_regex"}
        custom_timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)

        # When: Creating Violation with all fields specified
        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name,
            text_snippet=text_snippet,
            start_index=start_index,
            end_index=end_index,
            metadata=metadata,
            timestamp=custom_timestamp
        )

        # Then: Violation instance is created with all data preserved
        assert violation is not None
        assert isinstance(violation, Violation)

        # And: Required fields are correctly set
        assert violation.type == violation_type
        assert violation.severity == severity
        assert violation.description == description
        assert violation.confidence == confidence
        assert violation.scanner_name == scanner_name

        # And: Optional fields are correctly preserved
        assert violation.text_snippet == text_snippet
        assert violation.start_index == start_index
        assert violation.end_index == end_index
        assert violation.metadata == metadata
        assert violation.timestamp == custom_timestamp

        # And: All fields are correctly typed
        assert isinstance(violation.text_snippet, str)
        assert isinstance(violation.start_index, int)
        assert isinstance(violation.end_index, int)
        assert isinstance(violation.metadata, dict)
        assert isinstance(violation.timestamp, datetime)
    
    def test_violation_initialization_generates_timestamp_automatically(self):
        """
        Test that Violation automatically generates UTC timestamp when not provided.

        Verifies:
            Every violation has a timestamp marking when it was detected,
            defaulting to current UTC time if not explicitly set

        Business Impact:
            Ensures accurate temporal tracking for security incident analysis,
            audit trails, and time-based violation pattern detection

        Scenario:
            Given: Violation parameters without explicit timestamp
            When: Creating Violation instance
            Then: timestamp field is automatically set to current UTC time
            And: Timestamp is a datetime object (naive, as per implementation)

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation parameters without explicit timestamp
        violation_type = ViolationType.TOXIC_INPUT
        severity = SeverityLevel.LOW
        description = "Mild offensive language detected"
        confidence = 0.65
        scanner_name = "toxicity_classifier"

        # Record time before violation creation (using UTC to match implementation)
        before_creation = datetime.utcnow()

        # When: Creating Violation instance
        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name
        )

        # Record time after violation creation (using UTC to match implementation)
        after_creation = datetime.utcnow()

        # Then: timestamp field is automatically set
        assert violation.timestamp is not None

        # And: Timestamp is a datetime object (naive, as per implementation uses datetime.utcnow())
        assert isinstance(violation.timestamp, datetime)

        # And: Timestamp is within reasonable creation time window (using UTC times)
        # Convert naive timestamps to comparable format by removing microseconds
        before_ts = before_creation.replace(microsecond=0)
        after_ts = after_creation.replace(microsecond=0)
        violation_ts = violation.timestamp.replace(microsecond=0)
        assert before_ts <= violation_ts <= after_ts
    
    def test_violation_initialization_accepts_custom_timestamp(self):
        """
        Test that Violation accepts custom timestamp for historical violations.

        Verifies:
            Violations can be created with specific timestamps for batch
            processing, historical analysis, or violation reconstruction

        Business Impact:
            Supports importing historical security data and maintaining
            accurate temporal sequences during violation analysis

        Scenario:
            Given: Violation parameters with explicit historical timestamp
            When: Creating Violation with custom timestamp
            Then: Provided timestamp is preserved exactly
            And: No automatic timestamp generation occurs

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation parameters with explicit historical timestamp
        violation_type = ViolationType.SUSPICIOUS_PATTERN
        severity = SeverityLevel.CRITICAL
        description = "Suspicious pattern detected in user input"
        confidence = 0.95
        scanner_name = "pattern_scanner"
        historical_timestamp = datetime(2023, 6, 15, 14, 30, 22, tzinfo=UTC)

        # When: Creating Violation with custom timestamp
        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name,
            timestamp=historical_timestamp
        )

        # Then: Provided timestamp is preserved exactly
        assert violation.timestamp == historical_timestamp
        assert violation.timestamp.year == 2023
        assert violation.timestamp.month == 6
        assert violation.timestamp.day == 15

        # And: No automatic timestamp generation occurs
        # (timestamp is not current time)
        current_time = datetime.now(UTC)
        assert violation.timestamp != current_time
        assert violation.timestamp < current_time
    
    def test_violation_initialization_accepts_metadata_dictionary(self):
        """
        Test that Violation accepts and preserves custom metadata dictionary.

        Verifies:
            Scanner-specific information and contextual data can be attached
            to violations for enhanced analysis and debugging

        Business Impact:
            Enables scanners to provide implementation-specific details,
            detection confidence breakdowns, and diagnostic information

        Scenario:
            Given: Violation parameters with custom metadata dictionary
            When: Creating Violation with metadata
            Then: Metadata dictionary is stored and accessible
            And: Dictionary is mutable for post-creation enrichment

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation parameters with custom metadata dictionary
        violation_type = ViolationType.BIAS_DETECTED
        severity = SeverityLevel.MEDIUM
        description = "Potential bias detected in content"
        confidence = 0.78
        scanner_name = "bias_detector"
        custom_metadata = {
            "detection_model": "bert-base-bias-detector",
            "confidence_breakdown": {
                "gender_bias": 0.6,
                "racial_bias": 0.3,
                "age_bias": 0.1
            },
            "trigger_phrases": ["certain demographic", "typical for"],
            "processing_time_ms": 145
        }

        # When: Creating Violation with metadata
        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name,
            metadata=custom_metadata
        )

        # Then: Metadata dictionary is stored and accessible
        assert violation.metadata == custom_metadata
        assert isinstance(violation.metadata, dict)
        assert violation.metadata["detection_model"] == "bert-base-bias-detector"
        assert violation.metadata["confidence_breakdown"]["gender_bias"] == 0.6

        # And: Dictionary is mutable for post-creation enrichment
        original_length = len(violation.metadata)
        violation.metadata["additional_info"] = "Added after creation"
        assert violation.metadata["additional_info"] == "Added after creation"
        assert len(violation.metadata) == original_length + 1
    
    def test_violation_initialization_defaults_metadata_to_empty_dict(self):
        """
        Test that Violation initializes metadata to empty dict when not provided.

        Verifies:
            Metadata field always exists as an empty dictionary for
            consistent access patterns without None checks

        Business Impact:
            Simplifies violation handling code by guaranteeing metadata
            is always a dictionary, preventing AttributeError exceptions

        Scenario:
            Given: Violation parameters without metadata
            When: Creating Violation without specifying metadata
            Then: metadata field is empty dictionary, not None
            And: Dictionary can be populated after creation

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation parameters without metadata
        violation_type = ViolationType.HARMFUL_CONTENT
        severity = SeverityLevel.HIGH
        description = "Harmful content detected in generated text"
        confidence = 0.89
        scanner_name = "content_safety_scanner"

        # When: Creating Violation without specifying metadata
        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name
        )

        # Then: metadata field is empty dictionary, not None
        assert violation.metadata is not None
        assert violation.metadata == {}
        assert isinstance(violation.metadata, dict)

        # And: Dictionary can be populated after creation
        violation.metadata["added_later"] = "test value"
        assert violation.metadata["added_later"] == "test value"
        assert len(violation.metadata) == 1

        # And: Can safely access metadata without None checks
        keys = list(violation.metadata.keys())
        assert keys == ["added_later"]


class TestViolationValidation:
    """
    Test suite for Violation field validation in __post_init__.
    
    Scope:
        - Confidence score range validation (0.0 to 1.0)
        - Description non-empty validation
        - Scanner name non-empty validation
        - Error messages for validation failures
        
    Business Critical:
        Field validation prevents malformed violations from corrupting
        security logs, analytics, and automated response systems.
        
    Test Coverage:
        - Invalid confidence scores (negative, > 1.0)
        - Empty or whitespace-only required string fields
        - Proper ValueError exceptions with descriptive messages
    """
    
    def test_violation_validation_rejects_confidence_above_one(self):
        """
        Test that Violation validation rejects confidence scores greater than 1.0.

        Verifies:
            Confidence score validation enforces maximum value of 1.0 per
            documented contract (0.0 to 1.0 range)

        Business Impact:
            Prevents invalid confidence scores that would corrupt risk
            assessment calculations and security decision thresholds

        Scenario:
            Given: Violation parameters with confidence > 1.0
            When: Attempting to create Violation
            Then: ValueError is raised with confidence range error message
            And: No Violation instance is created

        Fixtures Used:
            None - Direct dataclass testing

        Edge Cases Covered:
            - confidence = 1.5 (clearly above limit)
            - confidence = 2.0 (well above limit)
            - confidence = 100.0 (extreme case)
        """
        # Test multiple confidence values above 1.0
        invalid_confidences = [1.5, 2.0, 100.0, 1.001]

        for invalid_confidence in invalid_confidences:
            # Given: Violation parameters with confidence > 1.0
            violation_type = ViolationType.PROMPT_INJECTION
            severity = SeverityLevel.HIGH
            description = "Test violation"
            scanner_name = "test_scanner"

            # When: Attempting to create Violation with invalid confidence
            # Then: ValueError is raised
            with pytest.raises(ValueError) as exc_info:
                Violation(
                    type=violation_type,
                    severity=severity,
                    description=description,
                    confidence=invalid_confidence,
                    scanner_name=scanner_name
                )

            # And: Error message indicates confidence range issue
            error_message = str(exc_info.value).lower()
            assert "confidence" in error_message
            assert ("range" in error_message or "0.0" in error_message or "1.0" in error_message)

            # And: No Violation instance was created (cannot test directly, but validation ran)
    
    def test_violation_validation_rejects_negative_confidence(self):
        """
        Test that Violation validation rejects negative confidence scores.

        Verifies:
            Confidence score validation enforces minimum value of 0.0 per
            documented contract (0.0 to 1.0 range)

        Business Impact:
            Prevents nonsensical negative confidence values that would
            invalidate statistical analysis and risk scoring

        Scenario:
            Given: Violation parameters with confidence < 0.0
            When: Attempting to create Violation
            Then: ValueError is raised with confidence range error message
            And: Violation instance is not created

        Fixtures Used:
            None - Direct dataclass testing

        Edge Cases Covered:
            - confidence = -0.1 (slightly below zero)
            - confidence = -1.0 (clearly invalid)
        """
        # Test multiple negative confidence values
        invalid_confidences = [-0.1, -1.0, -10.5, -0.001]

        for invalid_confidence in invalid_confidences:
            # Given: Violation parameters with confidence < 0.0
            violation_type = ViolationType.TOXIC_INPUT
            severity = SeverityLevel.MEDIUM
            description = "Test violation"
            scanner_name = "test_scanner"

            # When: Attempting to create Violation with negative confidence
            # Then: ValueError is raised
            with pytest.raises(ValueError) as exc_info:
                Violation(
                    type=violation_type,
                    severity=severity,
                    description=description,
                    confidence=invalid_confidence,
                    scanner_name=scanner_name
                )

            # And: Error message indicates confidence range issue
            error_message = str(exc_info.value).lower()
            assert "confidence" in error_message
            assert ("range" in error_message or "0.0" in error_message or "1.0" in error_message)
    
    def test_violation_validation_accepts_confidence_at_boundaries(self):
        """
        Test that Violation accepts valid boundary confidence values (0.0 and 1.0).

        Verifies:
            Boundary values 0.0 and 1.0 are valid confidence scores per
            documented inclusive range requirements

        Business Impact:
            Ensures scanners can express absolute certainty (1.0) and
            minimum threshold detection (0.0) without validation errors

        Scenario:
            Given: Violation parameters with confidence = 0.0 or 1.0
            When: Creating Violation instances at boundary values
            Then: Violations are created successfully without validation errors
            And: Confidence values are preserved exactly

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Test boundary confidence values
        boundary_confidences = [0.0, 1.0]

        for confidence in boundary_confidences:
            # Given: Violation parameters with confidence at boundary
            violation_type = ViolationType.PII_LEAKAGE
            severity = SeverityLevel.LOW if confidence == 0.0 else SeverityLevel.HIGH
            description = f"Test violation with confidence {confidence}"
            scanner_name = "boundary_test_scanner"

            # When: Creating Violation with boundary confidence
            # Then: Violation is created successfully without validation errors
            violation = Violation(
                type=violation_type,
                severity=severity,
                description=description,
                confidence=confidence,
                scanner_name=scanner_name
            )

            # And: Confidence values are preserved exactly
            assert violation.confidence == confidence
            assert isinstance(violation.confidence, float)
    
    def test_violation_validation_rejects_empty_description(self):
        """
        Test that Violation validation rejects empty description strings.

        Verifies:
            Description field validation prevents empty strings per
            documented contract requirements for debugging information

        Business Impact:
            Ensures every violation has meaningful description for security
            analysts, incident responders, and automated systems

        Scenario:
            Given: Violation parameters with empty string description
            When: Attempting to create Violation
            Then: ValueError is raised indicating description cannot be empty
            And: No Violation instance is created

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation parameters with empty string description
        violation_type = ViolationType.PROMPT_INJECTION
        severity = SeverityLevel.HIGH
        empty_description = ""
        confidence = 0.8
        scanner_name = "test_scanner"

        # When: Attempting to create Violation with empty description
        # Then: ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=violation_type,
                severity=severity,
                description=empty_description,
                confidence=confidence,
                scanner_name=scanner_name
            )

        # And: Error message indicates description cannot be empty
        error_message = str(exc_info.value).lower()
        assert "description" in error_message
        assert ("empty" in error_message or "blank" in error_message or "required" in error_message)
    
    def test_violation_validation_rejects_whitespace_only_description(self):
        """
        Test that Violation validation rejects whitespace-only descriptions.

        Verifies:
            Description validation strips whitespace and rejects empty result,
            preventing effectively meaningless descriptions

        Business Impact:
            Prevents creation of violations with no actual descriptive
            content that would hinder security analysis and reporting

        Scenario:
            Given: Violation parameters with whitespace-only description
            When: Attempting to create Violation
            Then: ValueError is raised for empty description after stripping
            And: Violation is not created

        Fixtures Used:
            None - Direct dataclass testing

        Edge Cases Covered:
            - Single space " "
            - Multiple spaces "   "
            - Tabs and newlines "\t\n"
        """
        # Test various whitespace-only descriptions
        whitespace_descriptions = [" ", "   ", "\t", "\n", "\t\n", "  \n\t  "]

        for whitespace_desc in whitespace_descriptions:
            # Given: Violation parameters with whitespace-only description
            violation_type = ViolationType.PROMPT_INJECTION
            severity = SeverityLevel.HIGH
            confidence = 0.8
            scanner_name = "test_scanner"

            # When: Attempting to create Violation with whitespace-only description
            # Then: ValueError is raised
            with pytest.raises(ValueError) as exc_info:
                Violation(
                    type=violation_type,
                    severity=severity,
                    description=whitespace_desc,
                    confidence=confidence,
                    scanner_name=scanner_name
                )

            # And: Error message indicates description cannot be empty
            error_message = str(exc_info.value).lower()
            assert "description" in error_message
            assert ("empty" in error_message or "blank" in error_message or "required" in error_message)
    
    def test_violation_validation_rejects_empty_scanner_name(self):
        """
        Test that Violation validation rejects empty scanner_name strings.

        Verifies:
            Scanner name validation prevents empty strings per contract
            requirements for identifying the detection source

        Business Impact:
            Ensures violations can be traced to their detecting scanner for
            debugging, performance analysis, and scanner tuning

        Scenario:
            Given: Violation parameters with empty string scanner_name
            When: Attempting to create Violation
            Then: ValueError is raised indicating scanner_name cannot be empty
            And: No Violation instance is created

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation parameters with empty string scanner_name
        violation_type = ViolationType.PROMPT_INJECTION
        severity = SeverityLevel.HIGH
        description = "Test violation"
        confidence = 0.8
        empty_scanner_name = ""

        # When: Attempting to create Violation with empty scanner_name
        # Then: ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            Violation(
                type=violation_type,
                severity=severity,
                description=description,
                confidence=confidence,
                scanner_name=empty_scanner_name
            )

        # And: Error message indicates scanner_name cannot be empty
        error_message = str(exc_info.value).lower()
        assert "scanner" in error_message or "name" in error_message
        assert ("empty" in error_message or "blank" in error_message or "required" in error_message)
    
    def test_violation_validation_rejects_whitespace_only_scanner_name(self):
        """
        Test that Violation validation rejects whitespace-only scanner names.

        Verifies:
            Scanner name validation strips whitespace and rejects empty result

        Business Impact:
            Prevents violations with no identifiable source scanner,
            ensuring complete violation traceability and accountability

        Scenario:
            Given: Violation parameters with whitespace-only scanner_name
            When: Attempting to create Violation
            Then: ValueError is raised for empty scanner_name after stripping
            And: Violation is not created

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Test various whitespace-only scanner names
        whitespace_scanner_names = [" ", "   ", "\t", "\n", "\t\n", "  \n\t  "]

        for whitespace_name in whitespace_scanner_names:
            # Given: Violation parameters with whitespace-only scanner_name
            violation_type = ViolationType.PROMPT_INJECTION
            severity = SeverityLevel.HIGH
            description = "Test violation"
            confidence = 0.8

            # When: Attempting to create Violation with whitespace-only scanner_name
            # Then: ValueError is raised
            with pytest.raises(ValueError) as exc_info:
                Violation(
                    type=violation_type,
                    severity=severity,
                    description=description,
                    confidence=confidence,
                    scanner_name=whitespace_name
                )

            # And: Error message indicates scanner_name cannot be empty
            error_message = str(exc_info.value).lower()
            assert "scanner" in error_message or "name" in error_message
            assert ("empty" in error_message or "blank" in error_message or "required" in error_message)


class TestViolationSerialization:
    """
    Test suite for Violation to_dict() serialization method.
    
    Scope:
        - Dictionary conversion for JSON serialization
        - Enum value conversion to strings
        - Timestamp formatting as ISO 8601 string
        - Optional field handling in dictionary output
        - Metadata preservation
        
    Business Critical:
        Proper serialization enables violations to be stored in databases,
        transmitted via APIs, and logged for security analysis systems.
        
    Test Coverage:
        - Complete field serialization
        - Enum to string conversion
        - Timestamp to ISO 8601 conversion
        - None value handling for optional fields
        - Metadata dictionary inclusion
    """
    
    def test_violation_to_dict_includes_all_required_fields(self):
        """
        Test that to_dict() includes all required violation fields.

        Verifies:
            Serialized dictionary contains type, severity, description,
            confidence, scanner_name, and timestamp per contract

        Business Impact:
            Ensures complete violation data for API responses, database
            storage, and security information systems integration

        Scenario:
            Given: Violation instance with all required fields
            When: Calling to_dict() method
            Then: Dictionary contains all required field keys
            And: All values match the original violation data

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation instance with all required fields
        violation_type = ViolationType.PROMPT_INJECTION
        severity = SeverityLevel.HIGH
        description = "System instruction override attempt detected"
        confidence = 0.92
        scanner_name = "injection_detector"

        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name
        )

        # When: Calling to_dict() method
        result_dict = violation.to_dict()

        # Then: Dictionary contains all required field keys
        required_fields = ["type", "severity", "description", "confidence", "scanner_name", "timestamp"]
        for field in required_fields:
            assert field in result_dict, f"Missing required field: {field}"

        # And: All values match the original violation data
        assert result_dict["type"] == violation_type.value
        assert result_dict["severity"] == severity.value
        assert result_dict["description"] == description
        assert result_dict["confidence"] == confidence
        assert result_dict["scanner_name"] == scanner_name
        assert isinstance(result_dict["timestamp"], str)
    
    def test_violation_to_dict_converts_enums_to_strings(self):
        """
        Test that to_dict() converts ViolationType and SeverityLevel enums to strings.

        Verifies:
            Enum values are serialized as their string representations
            for JSON compatibility and human readability

        Business Impact:
            Enables JSON serialization for API responses and prevents
            serialization errors from enum objects

        Scenario:
            Given: Violation with ViolationType and SeverityLevel enums
            When: Calling to_dict() method
            Then: "type" and "severity" are strings, not enum objects
            And: String values match enum.value attributes

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation with ViolationType and SeverityLevel enums
        violation_type = ViolationType.PII_LEAKAGE
        severity = SeverityLevel.MEDIUM
        description = "Email address detected in user input"
        confidence = 0.87
        scanner_name = "pii_scanner"

        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name
        )

        # When: Calling to_dict() method
        result_dict = violation.to_dict()

        # Then: "type" and "severity" are strings, not enum objects
        assert isinstance(result_dict["type"], str)
        assert isinstance(result_dict["severity"], str)

        # And: String values match enum.value attributes
        assert result_dict["type"] == violation_type.value
        assert result_dict["severity"] == severity.value

        # Verify specific expected values
        assert result_dict["type"] == "pii_leakage"
        assert result_dict["severity"] == "medium"
    
    def test_violation_to_dict_formats_timestamp_as_iso_8601(self):
        """
        Test that to_dict() formats timestamp as ISO 8601 string.

        Verifies:
            Timestamp datetime object is converted to standardized
            ISO 8601 format for universal date/time representation

        Business Impact:
            Ensures consistent timestamp format across systems and
            enables reliable temporal analysis in security logs

        Scenario:
            Given: Violation with UTC timestamp
            When: Calling to_dict() method
            Then: "timestamp" is string in ISO 8601 format
            And: Timestamp can be parsed back to original datetime

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation with UTC timestamp
        violation_type = ViolationType.TOXIC_INPUT
        severity = SeverityLevel.LOW
        description = "Mild offensive language detected"
        confidence = 0.65
        scanner_name = "toxicity_classifier"
        custom_timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)

        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name,
            timestamp=custom_timestamp
        )

        # When: Calling to_dict() method
        result_dict = violation.to_dict()

        # Then: "timestamp" is string in ISO 8601 format
        timestamp_str = result_dict["timestamp"]
        assert isinstance(timestamp_str, str)
        assert "T" in timestamp_str  # ISO 8601 date/time separator
        assert "Z" in timestamp_str or "+" in timestamp_str  # UTC timezone indicator

        # And: Timestamp can be parsed back to original datetime
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert parsed_timestamp == custom_timestamp

        # Verify the exact format
        assert timestamp_str == "2024-01-15T10:30:45+00:00"
    
    def test_violation_to_dict_includes_optional_fields_when_present(self):
        """
        Test that to_dict() includes optional fields when they have values.

        Verifies:
            text_snippet, start_index, end_index are included in dictionary
            when provided during violation creation

        Business Impact:
            Preserves complete violation context for detailed security
            analysis and evidence documentation

        Scenario:
            Given: Violation with text_snippet and index values
            When: Calling to_dict() method
            Then: Dictionary includes text_snippet, start_index, end_index
            And: Values match the original violation data

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation with text_snippet and index values
        violation_type = ViolationType.PII_LEAKAGE
        severity = SeverityLevel.MEDIUM
        description = "Email address detected in user input"
        confidence = 0.87
        scanner_name = "pii_scanner"
        text_snippet = "Contact me at user@example.com for more info"
        start_index = 15
        end_index = 35
        metadata = {"detection_method": "regex_pattern"}

        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name,
            text_snippet=text_snippet,
            start_index=start_index,
            end_index=end_index,
            metadata=metadata
        )

        # When: Calling to_dict() method
        result_dict = violation.to_dict()

        # Then: Dictionary includes text_snippet, start_index, end_index
        optional_fields = ["text_snippet", "start_index", "end_index", "metadata"]
        for field in optional_fields:
            assert field in result_dict, f"Missing optional field: {field}"

        # And: Values match the original violation data
        assert result_dict["text_snippet"] == text_snippet
        assert result_dict["start_index"] == start_index
        assert result_dict["end_index"] == end_index
        assert result_dict["metadata"] == metadata
    
    def test_violation_to_dict_includes_none_for_missing_optional_fields(self):
        """
        Test that to_dict() includes None values for unset optional fields.

        Verifies:
            Optional fields are present in dictionary with None values
            when not provided, maintaining consistent dictionary structure

        Business Impact:
            Ensures predictable API responses and simplifies client-side
            violation processing with consistent field presence

        Scenario:
            Given: Violation without optional fields (text_snippet, indices)
            When: Calling to_dict() method
            Then: Dictionary contains keys for optional fields
            And: Values are None for unset optional fields

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation without optional fields (text_snippet, indices)
        violation_type = ViolationType.PROMPT_INJECTION
        severity = SeverityLevel.HIGH
        description = "System instruction override attempt detected"
        confidence = 0.92
        scanner_name = "injection_detector"

        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name
        )

        # When: Calling to_dict() method
        result_dict = violation.to_dict()

        # Then: Dictionary contains keys for optional fields
        optional_fields = ["text_snippet", "start_index", "end_index"]
        for field in optional_fields:
            assert field in result_dict, f"Missing optional field key: {field}"

        # And: Values are None for unset optional fields
        assert result_dict["text_snippet"] is None
        assert result_dict["start_index"] is None
        assert result_dict["end_index"] is None

        # Note: metadata should still be present as empty dict (default factory)
        assert "metadata" in result_dict
        assert result_dict["metadata"] == {}
    
    def test_violation_to_dict_preserves_metadata_dictionary(self):
        """
        Test that to_dict() includes metadata dictionary exactly as stored.

        Verifies:
            Custom metadata is preserved in serialized output for
            scanner-specific information and diagnostic data

        Business Impact:
            Enables rich violation context with scanner-specific details
            for enhanced security analysis and debugging

        Scenario:
            Given: Violation with custom metadata dictionary
            When: Calling to_dict() method
            Then: Dictionary includes "metadata" key with original dictionary
            And: Nested metadata values are preserved

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Violation with custom metadata dictionary
        violation_type = ViolationType.BIAS_DETECTED
        severity = SeverityLevel.MEDIUM
        description = "Potential bias detected in content"
        confidence = 0.78
        scanner_name = "bias_detector"
        custom_metadata = {
            "detection_model": "bert-base-bias-detector",
            "confidence_breakdown": {
                "gender_bias": 0.6,
                "racial_bias": 0.3,
                "age_bias": 0.1
            },
            "trigger_phrases": ["certain demographic", "typical for"],
            "processing_time_ms": 145,
            "nested_object": {
                "inner_key": "inner_value",
                "number": 42
            }
        }

        violation = Violation(
            type=violation_type,
            severity=severity,
            description=description,
            confidence=confidence,
            scanner_name=scanner_name,
            metadata=custom_metadata
        )

        # When: Calling to_dict() method
        result_dict = violation.to_dict()

        # Then: Dictionary includes "metadata" key with original dictionary
        assert "metadata" in result_dict
        assert isinstance(result_dict["metadata"], dict)

        # And: Nested metadata values are preserved
        assert result_dict["metadata"] == custom_metadata
        assert result_dict["metadata"]["detection_model"] == "bert-base-bias-detector"
        assert result_dict["metadata"]["confidence_breakdown"]["gender_bias"] == 0.6
        assert result_dict["metadata"]["trigger_phrases"] == ["certain demographic", "typical for"]
        assert result_dict["metadata"]["nested_object"]["inner_key"] == "inner_value"


class TestViolationDeserialization:
    """
    Test suite for Violation from_dict() deserialization method.
    
    Scope:
        - Dictionary to Violation object reconstruction
        - String to enum conversion for type and severity
        - ISO 8601 string to datetime parsing
        - Optional field handling with defaults
        - Round-trip serialization/deserialization
        
    Business Critical:
        Deserialization enables violations to be reconstructed from
        databases, API responses, and security log files for analysis.
        
    Test Coverage:
        - Complete violation reconstruction
        - String to enum conversion
        - Timestamp parsing from ISO 8601
        - Handling of missing optional fields
        - Error handling for invalid data
    """
    
    def test_violation_from_dict_reconstructs_complete_violation(self):
        """
        Test that from_dict() reconstructs complete Violation from dictionary.

        Verifies:
            All violation fields are restored from dictionary with correct
            types and values matching original violation

        Business Impact:
            Enables violation retrieval from databases and caches with
            full fidelity for security analysis and reporting

        Scenario:
            Given: Dictionary from violation.to_dict() with all fields
            When: Calling Violation.from_dict(data)
            Then: Reconstructed Violation matches original completely
            And: All field types are correct (enums, datetime, etc.)

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Dictionary from violation.to_dict() with all fields
        original_violation = Violation(
            type=ViolationType.PII_LEAKAGE,
            severity=SeverityLevel.MEDIUM,
            description="Email address detected in user input",
            confidence=0.87,
            scanner_name="pii_scanner",
            text_snippet="Contact me at user@example.com for more info",
            start_index=15,
            end_index=35,
            metadata={"detection_method": "regex_pattern", "pattern_used": "email_regex"},
            timestamp=datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        )

        violation_dict = original_violation.to_dict()

        # When: Calling Violation.from_dict(data)
        reconstructed_violation = Violation.from_dict(violation_dict)

        # Then: Reconstructed Violation matches original completely
        assert reconstructed_violation.type == original_violation.type
        assert reconstructed_violation.severity == original_violation.severity
        assert reconstructed_violation.description == original_violation.description
        assert reconstructed_violation.confidence == original_violation.confidence
        assert reconstructed_violation.scanner_name == original_violation.scanner_name
        assert reconstructed_violation.text_snippet == original_violation.text_snippet
        assert reconstructed_violation.start_index == original_violation.start_index
        assert reconstructed_violation.end_index == original_violation.end_index
        assert reconstructed_violation.metadata == original_violation.metadata

        # And: All field types are correct (enums, datetime, etc.)
        assert isinstance(reconstructed_violation.type, ViolationType)
        assert isinstance(reconstructed_violation.severity, SeverityLevel)
        assert isinstance(reconstructed_violation.description, str)
        assert isinstance(reconstructed_violation.confidence, float)
        assert isinstance(reconstructed_violation.scanner_name, str)
        assert isinstance(reconstructed_violation.text_snippet, str)
        assert isinstance(reconstructed_violation.start_index, int)
        assert isinstance(reconstructed_violation.end_index, int)
        assert isinstance(reconstructed_violation.metadata, dict)
        assert isinstance(reconstructed_violation.timestamp, datetime)
    
    def test_violation_from_dict_converts_string_type_to_enum(self):
        """
        Test that from_dict() converts string violation type to ViolationType enum.

        Verifies:
            String "type" field is converted to proper ViolationType enum
            member during deserialization per contract

        Business Impact:
            Ensures violations retrieved from storage have properly typed
            enum values for type-safe security logic

        Scenario:
            Given: Dictionary with "type": "prompt_injection" as string
            When: Calling Violation.from_dict(data)
            Then: Reconstructed violation.type is ViolationType.PROMPT_INJECTION
            And: type field is enum object, not string

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Dictionary with "type": "prompt_injection" as string
        violation_data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "System instruction override attempt",
            "confidence": 0.92,
            "scanner_name": "injection_detector",
            "timestamp": "2024-01-15T10:30:45+00:00"
        }

        # When: Calling Violation.from_dict(data)
        violation = Violation.from_dict(violation_data)

        # Then: Reconstructed violation.type is ViolationType.PROMPT_INJECTION
        assert violation.type == ViolationType.PROMPT_INJECTION

        # And: type field is enum object, not string
        assert isinstance(violation.type, ViolationType)
        assert violation.type.value == "prompt_injection"

        # Test with different violation types
        other_types = [
            ("toxic_input", ViolationType.TOXIC_INPUT),
            ("pii_leakage", ViolationType.PII_LEAKAGE),
            ("harmful_content", ViolationType.HARMFUL_CONTENT),
            ("scan_timeout", ViolationType.SCAN_TIMEOUT)
        ]

        for type_string, expected_enum in other_types:
            violation_data["type"] = type_string
            violation = Violation.from_dict(violation_data)
            assert violation.type == expected_enum
            assert isinstance(violation.type, ViolationType)
    
    def test_violation_from_dict_converts_string_severity_to_enum(self):
        """
        Test that from_dict() converts string severity to SeverityLevel enum.

        Verifies:
            String "severity" field is converted to SeverityLevel enum
            member during deserialization

        Business Impact:
            Ensures violations have properly typed severity for risk
            assessment and security response automation

        Scenario:
            Given: Dictionary with "severity": "high" as string
            When: Calling Violation.from_dict(data)
            Then: Reconstructed violation.severity is SeverityLevel.HIGH
            And: severity field is enum object, not string

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Dictionary with "severity": "high" as string
        violation_data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "System instruction override attempt",
            "confidence": 0.92,
            "scanner_name": "injection_detector",
            "timestamp": "2024-01-15T10:30:45+00:00"
        }

        # When: Calling Violation.from_dict(data)
        violation = Violation.from_dict(violation_data)

        # Then: Reconstructed violation.severity is SeverityLevel.HIGH
        assert violation.severity == SeverityLevel.HIGH

        # And: severity field is enum object, not string
        assert isinstance(violation.severity, SeverityLevel)
        assert violation.severity.value == "high"

        # Test with different severity levels
        severity_levels = [
            ("low", SeverityLevel.LOW),
            ("medium", SeverityLevel.MEDIUM),
            ("high", SeverityLevel.HIGH),
            ("critical", SeverityLevel.CRITICAL)
        ]

        for severity_string, expected_enum in severity_levels:
            violation_data["severity"] = severity_string
            violation = Violation.from_dict(violation_data)
            assert violation.severity == expected_enum
            assert isinstance(violation.severity, SeverityLevel)
    
    def test_violation_from_dict_parses_iso_8601_timestamp(self):
        """
        Test that from_dict() parses ISO 8601 timestamp string to datetime.

        Verifies:
            ISO 8601 formatted timestamp string is converted to datetime
            object with UTC timezone per contract

        Business Impact:
            Enables accurate temporal analysis from stored violations
            with proper timezone handling

        Scenario:
            Given: Dictionary with ISO 8601 timestamp string
            When: Calling Violation.from_dict(data)
            Then: Reconstructed violation.timestamp is datetime object
            And: Timestamp matches original datetime value

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Dictionary with ISO 8601 timestamp string
        original_timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        violation_data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "System instruction override attempt",
            "confidence": 0.92,
            "scanner_name": "injection_detector",
            "timestamp": "2024-01-15T10:30:45+00:00"
        }

        # When: Calling Violation.from_dict(data)
        violation = Violation.from_dict(violation_data)

        # Then: Reconstructed violation.timestamp is datetime object
        assert isinstance(violation.timestamp, datetime)

        # And: Timestamp matches original datetime value
        assert violation.timestamp == original_timestamp

        # Test different ISO 8601 formats
        other_timestamps = [
            "2024-06-15T14:30:22Z",
            "2023-12-01T09:15:00+00:00",
            "2024-01-01T00:00:00.123456+00:00"
        ]

        for timestamp_str in other_timestamps:
            violation_data["timestamp"] = timestamp_str
            violation = Violation.from_dict(violation_data)
            assert isinstance(violation.timestamp, datetime)
            # Note: from_dict parses ISO 8601 timestamps correctly but creates timezone-aware datetime
            # while default timestamp creation uses naive datetime - this is expected behavior

        # Test missing timestamp (should default to current time)
        del violation_data["timestamp"]
        before_creation = datetime.utcnow()
        violation = Violation.from_dict(violation_data)
        after_creation = datetime.utcnow()
        assert isinstance(violation.timestamp, datetime)
        # Note: Default timestamps are naive (implementation uses datetime.utcnow())
        assert before_creation <= violation.timestamp <= after_creation
    
    def test_violation_from_dict_handles_missing_optional_fields(self):
        """
        Test that from_dict() gracefully handles missing optional fields.

        Verifies:
            Violations can be reconstructed from minimal dictionaries
            with only required fields, using appropriate defaults

        Business Impact:
            Supports backward compatibility with older violation data
            that may not include all current optional fields

        Scenario:
            Given: Dictionary with only required fields (no text_snippet, indices)
            When: Calling Violation.from_dict(data)
            Then: Violation is created successfully
            And: Optional fields have appropriate default values (None)

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Dictionary with only required fields (no text_snippet, indices)
        minimal_violation_data = {
            "type": "prompt_injection",
            "severity": "high",
            "description": "Injection attempt",
            "confidence": 0.95,
            "scanner_name": "injection_detector"
        }

        # When: Calling Violation.from_dict(data)
        violation = Violation.from_dict(minimal_violation_data)

        # Then: Violation is created successfully
        assert violation is not None
        assert isinstance(violation, Violation)

        # And: Required fields are correctly set
        assert violation.type == ViolationType.PROMPT_INJECTION
        assert violation.severity == SeverityLevel.HIGH
        assert violation.description == "Injection attempt"
        assert violation.confidence == 0.95
        assert violation.scanner_name == "injection_detector"

        # And: Optional fields have appropriate default values (None)
        assert violation.text_snippet is None
        assert violation.start_index is None
        assert violation.end_index is None

        # And: Metadata defaults to empty dict
        assert violation.metadata == {}
        assert isinstance(violation.metadata, dict)

        # And: Timestamp is generated automatically
        assert isinstance(violation.timestamp, datetime)
        # Note: Implementation uses naive datetime (datetime.utcnow())
    
    def test_violation_from_dict_round_trip_preserves_data(self):
        """
        Test that to_dict() followed by from_dict() preserves all violation data.

        Verifies:
            Complete serialization/deserialization cycle maintains data
            fidelity for storage and retrieval workflows

        Business Impact:
            Ensures violations can be reliably stored and retrieved from
            databases, caches, and message queues without data loss

        Scenario:
            Given: Original Violation instance with all fields
            When: Serializing with to_dict() then deserializing with from_dict()
            Then: Reconstructed violation matches original exactly
            And: All fields (including metadata) are preserved

        Fixtures Used:
            None - Direct dataclass testing
        """
        # Given: Original Violation instance with all fields
        original_violation = Violation(
            type=ViolationType.BIAS_DETECTED,
            severity=SeverityLevel.MEDIUM,
            description="Potential bias detected in content",
            confidence=0.78,
            scanner_name="bias_detector",
            text_snippet="This content may contain biased language",
            start_index=20,
            end_index=65,
            metadata={
                "detection_model": "bert-base-bias-detector",
                "confidence_breakdown": {
                    "gender_bias": 0.6,
                    "racial_bias": 0.3,
                    "age_bias": 0.1
                },
                "trigger_phrases": ["certain demographic", "typical for"],
                "processing_time_ms": 145
            },
            timestamp=datetime(2024, 3, 10, 15, 45, 30, tzinfo=UTC)
        )

        # When: Serializing with to_dict() then deserializing with from_dict()
        violation_dict = original_violation.to_dict()
        reconstructed_violation = Violation.from_dict(violation_dict)

        # Then: Reconstructed violation matches original exactly
        assert reconstructed_violation.type == original_violation.type
        assert reconstructed_violation.severity == original_violation.severity
        assert reconstructed_violation.description == original_violation.description
        assert reconstructed_violation.confidence == original_violation.confidence
        assert reconstructed_violation.scanner_name == original_violation.scanner_name
        assert reconstructed_violation.text_snippet == original_violation.text_snippet
        assert reconstructed_violation.start_index == original_violation.start_index
        assert reconstructed_violation.end_index == original_violation.end_index
        assert reconstructed_violation.timestamp == original_violation.timestamp

        # And: All fields (including metadata) are preserved
        assert reconstructed_violation.metadata == original_violation.metadata
        assert reconstructed_violation.metadata["detection_model"] == "bert-base-bias-detector"
        assert reconstructed_violation.metadata["confidence_breakdown"]["gender_bias"] == 0.6
        assert reconstructed_violation.metadata["trigger_phrases"] == ["certain demographic", "typical for"]

        # Test with minimal violation too
        minimal_violation = Violation(
            type=ViolationType.TOXIC_INPUT,
            severity=SeverityLevel.LOW,
            description="Mild toxic content",
            confidence=0.6,
            scanner_name="toxicity_scanner"
        )

        minimal_dict = minimal_violation.to_dict()
        minimal_reconstructed = Violation.from_dict(minimal_dict)

        assert minimal_reconstructed.type == minimal_violation.type
        assert minimal_reconstructed.severity == minimal_violation.severity
        assert minimal_reconstructed.description == minimal_violation.description
        assert minimal_reconstructed.confidence == minimal_violation.confidence
        assert minimal_reconstructed.scanner_name == minimal_violation.scanner_name
        assert minimal_reconstructed.text_snippet is None
        assert minimal_reconstructed.start_index is None
        assert minimal_reconstructed.end_index is None
        assert minimal_reconstructed.metadata == {}
    
    def test_violation_from_dict_raises_key_error_for_missing_required_fields(self):
        """
        Test that from_dict() raises KeyError when required fields are missing.

        Verifies:
            Deserialization fails appropriately when dictionary lacks
            essential required fields per contract

        Business Impact:
            Prevents creation of incomplete violations from corrupted
            data sources, maintaining data integrity standards

        Scenario:
            Given: Dictionary missing required field (e.g., "description")
            When: Calling Violation.from_dict(data)
            Then: KeyError is raised indicating missing field
            And: No Violation instance is created

        Fixtures Used:
            None - Direct dataclass testing

        Edge Cases Covered:
            - Missing "type" field
            - Missing "severity" field
            - Missing "description" field
            - Missing "confidence" field
            - Missing "scanner_name" field
        """
        # Test each required field missing
        required_fields = ["type", "severity", "description", "confidence", "scanner_name"]

        for missing_field in required_fields:
            # Given: Dictionary missing required field
            incomplete_data = {
                "type": "prompt_injection",
                "severity": "high",
                "description": "Test violation",
                "confidence": 0.8,
                "scanner_name": "test_scanner"
            }
            del incomplete_data[missing_field]

            # When: Calling Violation.from_dict(data)
            # Then: KeyError is raised
            with pytest.raises(KeyError) as exc_info:
                Violation.from_dict(incomplete_data)

            # And: KeyError indicates the missing field
            assert missing_field in str(exc_info.value) or missing_field == exc_info.value.args[0]

        # Test completely empty dictionary
        with pytest.raises(KeyError):
            Violation.from_dict({})

        # Test dictionary with only optional fields
        optional_only_data = {
            "text_snippet": "Some text",
            "start_index": 0,
            "end_index": 10,
            "metadata": {}
        }
        with pytest.raises(KeyError):
            Violation.from_dict(optional_only_data)
    
    def test_violation_from_dict_raises_value_error_for_invalid_enum_values(self):
        """
        Test that from_dict() raises ValueError for invalid enum string values.

        Verifies:
            Deserialization fails when enum strings don't match defined
            ViolationType or SeverityLevel members

        Business Impact:
            Prevents creation of violations with invalid classification
            that would corrupt security analytics and reporting

        Scenario:
            Given: Dictionary with invalid "type" or "severity" string
            When: Calling Violation.from_dict(data)
            Then: ValueError is raised indicating invalid enum value
            And: Error message identifies the problematic field

        Fixtures Used:
            None - Direct dataclass testing

        Edge Cases Covered:
            - Invalid violation type: "unknown_type"
            - Invalid severity: "super_critical"
        """
        # Test invalid violation type
        invalid_type_data = {
            "type": "unknown_type",
            "severity": "high",
            "description": "Test violation",
            "confidence": 0.8,
            "scanner_name": "test_scanner"
        }

        # When: Calling Violation.from_dict(data) with invalid type
        # Then: ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            Violation.from_dict(invalid_type_data)

        # And: Error message indicates invalid enum value
        error_message = str(exc_info.value).lower()
        assert "unknown_type" in error_message or "invalid" in error_message

        # Test invalid severity level
        invalid_severity_data = {
            "type": "prompt_injection",
            "severity": "super_critical",
            "description": "Test violation",
            "confidence": 0.8,
            "scanner_name": "test_scanner"
        }

        # When: Calling Violation.from_dict(data) with invalid severity
        # Then: ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            Violation.from_dict(invalid_severity_data)

        # And: Error message indicates invalid enum value
        error_message = str(exc_info.value).lower()
        assert "super_critical" in error_message or "invalid" in error_message

        # Test multiple invalid enum values
        both_invalid_data = {
            "type": "fake_type",
            "severity": "ultra_high",
            "description": "Test violation",
            "confidence": 0.8,
            "scanner_name": "test_scanner"
        }

        # When: Calling Violation.from_dict(data) with both invalid
        # Then: ValueError is raised (should fail on type first)
        with pytest.raises(ValueError):
            Violation.from_dict(both_invalid_data)

        # Test case sensitivity (enums should be case sensitive)
        wrong_case_data = {
            "type": "Prompt_Injection",  # Wrong case
            "severity": "HIGH",  # Wrong case
            "description": "Test violation",
            "confidence": 0.8,
            "scanner_name": "test_scanner"
        }

        # When: Calling Violation.from_dict(data) with wrong case
        # Then: ValueError is raised
        with pytest.raises(ValueError):
            Violation.from_dict(wrong_case_data)

