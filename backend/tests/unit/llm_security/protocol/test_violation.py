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
        pass
    
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
        pass
    
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
            And: Timestamp is a datetime object with UTC timezone
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
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
        pass
    
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
        pass
    
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
        pass


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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass


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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass


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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass
    
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
        pass

