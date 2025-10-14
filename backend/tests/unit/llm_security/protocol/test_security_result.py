"""
Test suite for SecurityResult dataclass representing comprehensive scan results.

This module tests the SecurityResult dataclass that encapsulates complete security
scanning outcomes including safety assessments, violation details, performance metrics,
and contextual metadata for security decision-making and analysis.

Test Strategy:
    - Verify initialization with required and optional fields
    - Test __post_init__ validation and safety flag synchronization
    - Validate helper methods (get_violations_by_severity, has_critical_violations, etc.)
    - Test serialization/deserialization with complete data preservation
    - Verify edge cases like empty violations and safety flag corrections
"""

import pytest
from datetime import datetime, UTC
from app.infrastructure.security.llm.protocol import (
    SecurityResult,
    Violation,
    ViolationType,
    SeverityLevel
)


class TestSecurityResultInitialization:
    """
    Test suite for SecurityResult initialization and field handling.
    
    Scope:
        - Required field initialization (is_safe, violations, score, scanned_text, scan_duration_ms)
        - Optional field defaults (scanner_results, metadata, timestamp)
        - Automatic timestamp generation
        - Field type correctness and value ranges
        
    Business Critical:
        Proper SecurityResult initialization ensures accurate security
        assessments reach decision-making systems and user interfaces.
        
    Test Coverage:
        - Minimal initialization with required fields
        - Complete initialization with all optional fields
        - Default value handling for optional parameters
        - Timestamp automatic generation
    """
    
    def test_security_result_initialization_with_required_fields_only(self):
        """
        Test that SecurityResult initializes with only required fields.
        
        Verifies:
            SecurityResult can be created with minimal parameters and
            optional fields default to appropriate empty values
            
        Business Impact:
            Enables simple result creation for scanners providing only
            basic safety assessment without detailed metadata
            
        Scenario:
            Given: Required result parameters (is_safe, violations, score, scanned_text, scan_duration_ms)
            When: Creating SecurityResult with only required fields
            Then: Result instance is created successfully
            And: Optional fields default to empty dict, current timestamp
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_initialization_with_empty_violations_list(self):
        """
        Test that SecurityResult accepts empty violations list for safe content.
        
        Verifies:
            Safe scan results with no violations are represented with
            empty list, not None, per contract
            
        Business Impact:
            Ensures consistent violation list handling with guaranteed
            iterable for all security processing workflows
            
        Scenario:
            Given: Result parameters with empty violations list and is_safe=True
            When: Creating SecurityResult
            Then: Result is created successfully with empty violations
            And: violations field is empty list, not None
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_initialization_with_multiple_violations(self):
        """
        Test that SecurityResult accepts list of multiple Violation objects.
        
        Verifies:
            SecurityResult can contain multiple detected violations of
            varying types and severities per contract
            
        Business Impact:
            Supports comprehensive threat reporting when multiple security
            issues are detected in single content scan
            
        Scenario:
            Given: Result parameters with list of multiple Violation objects
            When: Creating SecurityResult
            Then: Result stores all violations correctly
            And: Violations list is accessible and complete
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_initialization_generates_timestamp_automatically(self):
        """
        Test that SecurityResult automatically generates UTC timestamp when not provided.
        
        Verifies:
            Every result has timestamp marking scan completion time,
            defaulting to current UTC time if not specified
            
        Business Impact:
            Ensures accurate temporal tracking for security monitoring,
            audit trails, and time-based analysis
            
        Scenario:
            Given: Result parameters without explicit timestamp
            When: Creating SecurityResult
            Then: timestamp field is automatically set to current UTC time
            And: Timestamp is datetime object with UTC timezone
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_initialization_accepts_custom_timestamp(self):
        """
        Test that SecurityResult accepts custom timestamp for historical results.
        
        Verifies:
            Results can be created with specific timestamps for batch
            processing, caching, or historical data reconstruction
            
        Business Impact:
            Supports result restoration from caches and databases while
            maintaining original scan completion timestamps
            
        Scenario:
            Given: Result parameters with explicit historical timestamp
            When: Creating SecurityResult with custom timestamp
            Then: Provided timestamp is preserved exactly
            And: No automatic timestamp generation occurs
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_initialization_accepts_scanner_results_metadata(self):
        """
        Test that SecurityResult accepts scanner_results dictionary for scanner-specific data.
        
        Verifies:
            Individual scanner outputs can be preserved in result for
            detailed analysis and debugging per contract
            
        Business Impact:
            Enables preservation of scanner-specific confidence scores,
            detection details, and diagnostic information
            
        Scenario:
            Given: Result with scanner_results dictionary containing scanner-specific data
            When: Creating SecurityResult
            Then: scanner_results is stored and accessible
            And: All nested scanner data is preserved
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_initialization_defaults_metadata_to_empty_dict(self):
        """
        Test that SecurityResult defaults metadata to empty dict when not provided.
        
        Verifies:
            Metadata field always exists as dictionary for consistent
            access patterns without None checks
            
        Business Impact:
            Simplifies result handling code by guaranteeing metadata
            dictionary exists and is mutable for enrichment
            
        Scenario:
            Given: Result parameters without metadata
            When: Creating SecurityResult without metadata
            Then: metadata field is empty dictionary, not None
            And: Dictionary can be populated after creation
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass


class TestSecurityResultValidation:
    """
    Test suite for SecurityResult validation in __post_init__.
    
    Scope:
        - Security score range validation (0.0 to 1.0)
        - Scan duration non-negative validation
        - Safety flag synchronization with violations list
        - Automatic correction of inconsistent safety flags
        
    Business Critical:
        Validation prevents malformed results from corrupting security
        decision systems and ensures consistent safety assessments.
        
    Test Coverage:
        - Invalid score values (negative, > 1.0)
        - Negative scan duration
        - Safety flag correction when inconsistent with violations
    """
    
    def test_security_result_validation_rejects_score_above_one(self):
        """
        Test that SecurityResult validation rejects scores greater than 1.0.
        
        Verifies:
            Score validation enforces maximum value of 1.0 per documented
            contract (0.0 to 1.0 safety score range)
            
        Business Impact:
            Prevents invalid safety scores that would corrupt risk
            calculations and security threshold comparisons
            
        Scenario:
            Given: Result parameters with score > 1.0
            When: Attempting to create SecurityResult
            Then: ValueError is raised with score range error message
            And: No SecurityResult instance is created
            
        Fixtures Used:
            None - Direct dataclass testing
            
        Edge Cases Covered:
            - score = 1.5 (clearly above limit)
            - score = 2.0 (well above limit)
        """
        pass
    
    def test_security_result_validation_rejects_negative_score(self):
        """
        Test that SecurityResult validation rejects negative scores.
        
        Verifies:
            Score validation enforces minimum value of 0.0 per contract
            
        Business Impact:
            Prevents nonsensical negative safety scores that would
            invalidate risk assessment and security analytics
            
        Scenario:
            Given: Result parameters with score < 0.0
            When: Attempting to create SecurityResult
            Then: ValueError is raised indicating invalid score
            And: SecurityResult is not created
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_validation_accepts_score_at_boundaries(self):
        """
        Test that SecurityResult accepts valid boundary scores (0.0 and 1.0).
        
        Verifies:
            Boundary values 0.0 and 1.0 are valid safety scores per
            documented inclusive range
            
        Business Impact:
            Allows expression of absolute safety (1.0) and complete
            threat detection (0.0) without validation errors
            
        Scenario:
            Given: Result parameters with score = 0.0 or 1.0
            When: Creating SecurityResult instances at boundaries
            Then: Results are created without validation errors
            And: Score values are preserved exactly
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_validation_rejects_negative_duration(self):
        """
        Test that SecurityResult validation rejects negative scan duration.
        
        Verifies:
            Scan duration validation enforces non-negative values per
            contract requirements
            
        Business Impact:
            Prevents invalid negative duration values that would corrupt
            performance metrics and monitoring systems
            
        Scenario:
            Given: Result parameters with scan_duration_ms < 0
            When: Attempting to create SecurityResult
            Then: ValueError is raised indicating invalid duration
            And: No result instance is created
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_validation_corrects_safety_flag_when_violations_present(self):
        """
        Test that __post_init__ sets is_safe=False when violations exist.
        
        Verifies:
            Safety flag is automatically corrected to False when
            violations list is non-empty, ensuring consistency
            
        Business Impact:
            Prevents inconsistent results where is_safe=True but
            violations exist, protecting security decision logic
            
        Scenario:
            Given: Result with is_safe=True but non-empty violations list
            When: Creating SecurityResult
            Then: is_safe is automatically corrected to False
            And: Warning or correction is logged
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_validation_corrects_safety_flag_when_no_violations(self):
        """
        Test that __post_init__ sets is_safe=True when violations list is empty.
        
        Verifies:
            Safety flag is automatically corrected to True when no
            violations are present, ensuring consistency
            
        Business Impact:
            Prevents false negatives where is_safe=False but no
            violations found, ensuring accurate safety reporting
            
        Scenario:
            Given: Result with is_safe=False but empty violations list
            When: Creating SecurityResult
            Then: is_safe is automatically corrected to True
            And: Inconsistency is resolved automatically
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass


class TestSecurityResultAnalysisMethods:
    """
    Test suite for SecurityResult helper methods for violation analysis.
    
    Scope:
        - get_violations_by_severity() grouping method
        - get_violations_by_type() grouping method
        - has_critical_violations() boolean check
        - has_high_severity_violations() boolean check
        
    Business Critical:
        Analysis methods enable risk-based security decisions, graduated
        responses, and comprehensive violation pattern detection.
        
    Test Coverage:
        - Violation grouping by severity and type
        - Boolean checks for high-severity threats
        - Empty violations list handling
        - Mixed severity/type violation analysis
    """
    
    def test_get_violations_by_severity_returns_all_severity_levels(self):
        """
        Test that get_violations_by_severity() returns dictionary with all severity levels.
        
        Verifies:
            Method returns complete mapping of SeverityLevel to violation
            lists, including empty lists for unused severities per contract
            
        Business Impact:
            Enables predictable severity-based filtering without checking
            for missing keys, simplifying security response logic
            
        Scenario:
            Given: SecurityResult with violations of various severities
            When: Calling get_violations_by_severity()
            Then: Dictionary contains keys for all SeverityLevel members
            And: Each level maps to list of violations with that severity
            And: Unused severity levels map to empty lists
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_get_violations_by_severity_groups_violations_correctly(self):
        """
        Test that get_violations_by_severity() correctly groups violations by severity.
        
        Verifies:
            Violations are properly distributed into severity-based groups
            matching their severity field values
            
        Business Impact:
            Ensures accurate risk assessment and enables graduated
            security responses based on violation severity
            
        Scenario:
            Given: SecurityResult with violations of LOW, MEDIUM, HIGH severities
            When: Calling get_violations_by_severity()
            Then: Each violation appears in correct severity group
            And: No violations appear in wrong severity groups
            And: All violations are accounted for
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_get_violations_by_severity_handles_empty_violations_list(self):
        """
        Test that get_violations_by_severity() handles empty violations gracefully.
        
        Verifies:
            Method returns complete severity mapping with all empty lists
            when result has no violations
            
        Business Impact:
            Prevents errors in security logic when processing safe
            content with no detected violations
            
        Scenario:
            Given: SecurityResult with empty violations list
            When: Calling get_violations_by_severity()
            Then: Dictionary contains all SeverityLevel keys
            And: All severity levels map to empty lists
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_get_violations_by_type_returns_all_violation_types(self):
        """
        Test that get_violations_by_type() returns dictionary with all violation types.
        
        Verifies:
            Method returns complete mapping of ViolationType to violation
            lists, including empty lists for undetected types per contract
            
        Business Impact:
            Enables comprehensive violation type analysis and pattern
            detection without defensive key existence checking
            
        Scenario:
            Given: SecurityResult with violations of various types
            When: Calling get_violations_by_type()
            Then: Dictionary contains keys for all ViolationType members
            And: Each type maps to list of matching violations
            And: Undetected types map to empty lists
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_get_violations_by_type_groups_violations_correctly(self):
        """
        Test that get_violations_by_type() correctly groups violations by type.
        
        Verifies:
            Violations are properly distributed into type-based groups
            matching their type field values
            
        Business Impact:
            Supports attack pattern analysis, scanner performance
            evaluation, and threat trend identification
            
        Scenario:
            Given: SecurityResult with violations of different types
            When: Calling get_violations_by_type()
            Then: Each violation appears in correct type group
            And: No violations appear in wrong type groups
            And: All violations are accounted for
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_get_violations_by_type_handles_empty_violations_list(self):
        """
        Test that get_violations_by_type() handles empty violations gracefully.
        
        Verifies:
            Method returns complete type mapping with all empty lists
            when result has no violations
            
        Business Impact:
            Prevents errors in threat analysis code when processing
            safe content without detected violations
            
        Scenario:
            Given: SecurityResult with empty violations list
            When: Calling get_violations_by_type()
            Then: Dictionary contains all ViolationType keys
            And: All types map to empty lists
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_has_critical_violations_returns_true_when_critical_present(self):
        """
        Test that has_critical_violations() returns True when CRITICAL violations exist.
        
        Verifies:
            Method detects presence of CRITICAL severity violations
            for immediate blocking decisions per contract
            
        Business Impact:
            Enables fast critical threat detection for urgent security
            responses and content blocking automation
            
        Scenario:
            Given: SecurityResult with at least one CRITICAL severity violation
            When: Calling has_critical_violations()
            Then: Method returns True immediately
            And: No need to iterate all violations after first CRITICAL found
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_has_critical_violations_returns_false_when_no_critical(self):
        """
        Test that has_critical_violations() returns False without CRITICAL violations.
        
        Verifies:
            Method correctly identifies absence of CRITICAL severity
            threats even when other violations exist
            
        Business Impact:
            Prevents false critical alerts when only lower-severity
            violations are detected, enabling graduated responses
            
        Scenario:
            Given: SecurityResult with LOW/MEDIUM/HIGH violations but no CRITICAL
            When: Calling has_critical_violations()
            Then: Method returns False
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_has_critical_violations_returns_false_for_empty_violations(self):
        """
        Test that has_critical_violations() returns False for safe content.
        
        Verifies:
            Method handles empty violations list without errors
            
        Business Impact:
            Ensures consistent behavior for safe content without
            defensive programming overhead
            
        Scenario:
            Given: SecurityResult with empty violations list
            When: Calling has_critical_violations()
            Then: Method returns False without errors
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_has_high_severity_violations_returns_true_for_high_or_critical(self):
        """
        Test that has_high_severity_violations() detects HIGH or CRITICAL violations.
        
        Verifies:
            Method identifies high-severity threats (both HIGH and
            CRITICAL levels) per contract requirements
            
        Business Impact:
            Enables detection of serious threats requiring elevated
            security responses without blocking all non-critical content
            
        Scenario:
            Given: SecurityResult with HIGH or CRITICAL severity violations
            When: Calling has_high_severity_violations()
            Then: Method returns True for either HIGH or CRITICAL
            
        Fixtures Used:
            None - Direct dataclass testing
            
        Edge Cases Covered:
            - Only HIGH severity violations present
            - Only CRITICAL severity violations present
            - Mix of HIGH and CRITICAL violations
        """
        pass
    
    def test_has_high_severity_violations_returns_false_for_low_medium_only(self):
        """
        Test that has_high_severity_violations() returns False for LOW/MEDIUM only.
        
        Verifies:
            Method correctly identifies when no high-severity threats
            are present, only lower-risk violations
            
        Business Impact:
            Prevents unnecessary elevated responses for low-risk
            violations, enabling proportionate security measures
            
        Scenario:
            Given: SecurityResult with only LOW or MEDIUM violations
            When: Calling has_high_severity_violations()
            Then: Method returns False
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass


class TestSecurityResultSerialization:
    """
    Test suite for SecurityResult to_dict() serialization.
    
    Scope:
        - Dictionary conversion with all fields
        - Violation list serialization via to_dict()
        - Timestamp ISO 8601 formatting
        - Privacy-preserving exclusion of scanned_text
        - Derived statistics inclusion (violation counts)
        
    Business Critical:
        Proper serialization enables results storage, API transmission,
        and integration with security monitoring systems.
        
    Test Coverage:
        - Complete field serialization
        - Nested violation serialization
        - Privacy-conscious data handling
        - Derived statistics calculation
    """
    
    def test_security_result_to_dict_includes_all_core_fields(self):
        """
        Test that to_dict() includes all core result fields except scanned_text.
        
        Verifies:
            Serialized dictionary contains is_safe, score, scan_duration_ms,
            violations, scanner_results, metadata, and timestamp per contract
            
        Business Impact:
            Ensures complete result data for APIs, storage, and monitoring
            while respecting privacy by excluding sensitive text content
            
        Scenario:
            Given: SecurityResult with complete data
            When: Calling to_dict()
            Then: Dictionary contains all fields except scanned_text
            And: scanned_text_length is included instead
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_to_dict_serializes_violations_to_dictionaries(self):
        """
        Test that to_dict() converts violation objects to dictionaries.
        
        Verifies:
            Nested Violation objects are serialized via their to_dict()
            method for complete JSON compatibility
            
        Business Impact:
            Enables full result serialization including detailed violation
            data for storage and API transmission
            
        Scenario:
            Given: SecurityResult with multiple Violation objects
            When: Calling to_dict()
            Then: "violations" field contains list of dictionaries
            And: Each violation dictionary matches Violation.to_dict() output
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_to_dict_formats_timestamp_as_iso_8601(self):
        """
        Test that to_dict() formats timestamp as ISO 8601 string.
        
        Verifies:
            Datetime timestamp is converted to standardized ISO 8601
            format for universal date/time representation
            
        Business Impact:
            Ensures consistent timestamp format across systems and
            enables reliable temporal analysis in monitoring
            
        Scenario:
            Given: SecurityResult with UTC timestamp
            When: Calling to_dict()
            Then: "timestamp" is string in ISO 8601 format
            And: Timestamp can be parsed back to datetime
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_to_dict_excludes_scanned_text_for_privacy(self):
        """
        Test that to_dict() excludes scanned_text content for privacy protection.
        
        Verifies:
            Actual scanned text is not included in serialized output
            per documented privacy-preserving behavior
            
        Business Impact:
            Prevents sensitive user content from being logged or
            transmitted to external monitoring systems
            
        Scenario:
            Given: SecurityResult with scanned_text containing sensitive data
            When: Calling to_dict()
            Then: Dictionary does not contain "scanned_text" key
            And: Only "scanned_text_length" is included for statistics
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_to_dict_includes_text_length_for_statistics(self):
        """
        Test that to_dict() includes scanned_text_length for performance analysis.
        
        Verifies:
            Text length is included for statistical analysis without
            exposing actual content per contract
            
        Business Impact:
            Enables performance analysis and scanner efficiency metrics
            while maintaining privacy of scanned content
            
        Scenario:
            Given: SecurityResult with scanned_text of known length
            When: Calling to_dict()
            Then: "scanned_text_length" equals len(scanned_text)
            And: No actual text content is present
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_to_dict_includes_violation_statistics(self):
        """
        Test that to_dict() includes violation_counts summary statistics.
        
        Verifies:
            Derived statistics showing violation counts by severity are
            included for quick analysis without processing violations
            
        Business Impact:
            Enables fast violation pattern identification in monitoring
            dashboards without parsing full violation details
            
        Scenario:
            Given: SecurityResult with violations of various severities
            When: Calling to_dict()
            Then: "violation_counts" contains severity breakdown
            And: Counts match actual violations by severity
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass


class TestSecurityResultDeserialization:
    """
    Test suite for SecurityResult from_dict() deserialization.
    
    Scope:
        - Dictionary to SecurityResult reconstruction
        - Nested violation deserialization
        - Timestamp parsing from ISO 8601
        - Optional field handling with defaults
        - Round-trip serialization fidelity
        
    Business Critical:
        Deserialization enables result retrieval from caches, databases,
        and message queues for security analysis and monitoring.
        
    Test Coverage:
        - Complete result reconstruction
        - Nested violation reconstruction
        - Timestamp parsing
        - Missing optional field handling
        - Data fidelity validation
    """
    
    def test_security_result_from_dict_reconstructs_complete_result(self):
        """
        Test that from_dict() reconstructs complete SecurityResult from dictionary.
        
        Verifies:
            All result fields are restored from dictionary with correct
            types and values per contract
            
        Business Impact:
            Enables result retrieval from storage with full fidelity
            for security analysis and incident investigation
            
        Scenario:
            Given: Dictionary from result.to_dict() with all fields
            When: Calling SecurityResult.from_dict(data)
            Then: Reconstructed result matches original completely
            And: All field types are correct (bool, float, list, etc.)
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_from_dict_reconstructs_nested_violations(self):
        """
        Test that from_dict() reconstructs Violation objects from violation dictionaries.
        
        Verifies:
            Nested violation dictionaries are converted back to Violation
            objects using Violation.from_dict() per contract
            
        Business Impact:
            Ensures complete violation data restoration with proper
            types for security analysis workflows
            
        Scenario:
            Given: Dictionary with list of violation dictionaries
            When: Calling SecurityResult.from_dict(data)
            Then: violations list contains Violation objects
            And: Each violation matches original via round-trip
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_from_dict_parses_iso_8601_timestamp(self):
        """
        Test that from_dict() parses ISO 8601 timestamp string to datetime.
        
        Verifies:
            ISO 8601 timestamp string is converted to datetime with
            UTC timezone per contract
            
        Business Impact:
            Enables accurate temporal analysis from stored results
            with proper timezone handling
            
        Scenario:
            Given: Dictionary with ISO 8601 timestamp string
            When: Calling SecurityResult.from_dict(data)
            Then: Reconstructed timestamp is datetime object
            And: Timestamp matches original datetime value
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_from_dict_handles_missing_optional_fields(self):
        """
        Test that from_dict() handles missing optional fields gracefully.
        
        Verifies:
            Results can be reconstructed from minimal dictionaries with
            only required fields, using appropriate defaults
            
        Business Impact:
            Supports backward compatibility with older result data that
            may lack newer optional fields
            
        Scenario:
            Given: Dictionary with only required fields
            When: Calling SecurityResult.from_dict(data)
            Then: Result is created successfully
            And: Optional fields have appropriate defaults (empty dict, etc.)
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass
    
    def test_security_result_from_dict_round_trip_preserves_data(self):
        """
        Test that to_dict() followed by from_dict() preserves result data.
        
        Verifies:
            Complete serialization/deserialization cycle maintains data
            fidelity except for intentionally excluded scanned_text
            
        Business Impact:
            Ensures results can be reliably cached and retrieved without
            data loss or corruption
            
        Scenario:
            Given: Original SecurityResult with complete data
            When: Serializing with to_dict() then deserializing with from_dict()
            Then: Reconstructed result matches original except scanned_text
            And: Violations, metadata, and statistics are preserved
            
        Fixtures Used:
            None - Direct dataclass testing
        """
        pass

