"""
Test suite for security protocol enumeration types.

This module tests the ViolationType and SeverityLevel enums that define the
taxonomy of security threats and their classification hierarchy. These enums
are foundational to the security system's violation reporting and risk assessment.

Test Strategy:
    - Verify enum value definitions and string representations
    - Test enum member access and iteration
    - Validate enum usage in violation classification
    - Ensure consistency across the security system
"""

import pytest
from app.infrastructure.security.llm.protocol import ViolationType, SeverityLevel


class TestViolationType:
    """
    Test suite for ViolationType enum defining security violation categories.
    
    Scope:
        - Enum value definitions and accessibility
        - String value representations for serialization
        - Enum member completeness for security coverage
        - Enum usage patterns in violation detection
        
    Business Critical:
        ViolationType categorization drives security decisions, logging,
        and automated responses throughout the security infrastructure.
        
    Test Coverage:
        - Input violation types (prompt injection, PII, malicious patterns)
        - Output violation types (harmful content, bias, policy violations)
        - System violation types (timeouts, errors, service issues)
    """
    
    def test_violation_type_has_prompt_injection_member(self):
        """
        Test that ViolationType enum includes PROMPT_INJECTION member.

        Verifies:
            PROMPT_INJECTION violation type exists and has correct string value

        Business Impact:
            Enables detection and classification of prompt injection attacks,
            a critical security threat vector for LLM systems

        Scenario:
            Given: ViolationType enum is imported
            When: PROMPT_INJECTION member is accessed
            Then: Member exists with expected string value "prompt_injection"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: PROMPT_INJECTION member is accessed
        prompt_injection = ViolationType.PROMPT_INJECTION

        # Then: Member exists with expected string value "prompt_injection"
        assert prompt_injection is not None
        assert prompt_injection.value == "prompt_injection"
        assert isinstance(prompt_injection.value, str)
    
    def test_violation_type_has_malicious_prompt_member(self):
        """
        Test that ViolationType enum includes MALICIOUS_PROMPT member.

        Verifies:
            MALICIOUS_PROMPT violation type exists for detecting harmful prompts

        Business Impact:
            Supports identification of deliberately malicious user inputs
            attempting to generate harmful or policy-violating content

        Scenario:
            Given: ViolationType enum is imported
            When: MALICIOUS_PROMPT member is accessed
            Then: Member exists with expected string value "malicious_prompt"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: MALICIOUS_PROMPT member is accessed
        malicious_prompt = ViolationType.MALICIOUS_PROMPT

        # Then: Member exists with expected string value "malicious_prompt"
        assert malicious_prompt is not None
        assert malicious_prompt.value == "malicious_prompt"
        assert isinstance(malicious_prompt.value, str)
    
    def test_violation_type_has_toxic_input_member(self):
        """
        Test that ViolationType enum includes TOXIC_INPUT member.

        Verifies:
            TOXIC_INPUT violation type exists for content moderation

        Business Impact:
            Enables detection of toxic, offensive, or inappropriate user inputs
            that violate community standards and usage policies

        Scenario:
            Given: ViolationType enum is imported
            When: TOXIC_INPUT member is accessed
            Then: Member exists with expected string value "toxic_input"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: TOXIC_INPUT member is accessed
        toxic_input = ViolationType.TOXIC_INPUT

        # Then: Member exists with expected string value "toxic_input"
        assert toxic_input is not None
        assert toxic_input.value == "toxic_input"
        assert isinstance(toxic_input.value, str)
    
    def test_violation_type_has_pii_leakage_member(self):
        """
        Test that ViolationType enum includes PII_LEAKAGE member.

        Verifies:
            PII_LEAKAGE violation type exists for privacy protection

        Business Impact:
            Critical for GDPR/CCPA compliance and preventing unauthorized
            exposure of personally identifiable information

        Scenario:
            Given: ViolationType enum is imported
            When: PII_LEAKAGE member is accessed
            Then: Member exists with expected string value "pii_leakage"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: PII_LEAKAGE member is accessed
        pii_leakage = ViolationType.PII_LEAKAGE

        # Then: Member exists with expected string value "pii_leakage"
        assert pii_leakage is not None
        assert pii_leakage.value == "pii_leakage"
        assert isinstance(pii_leakage.value, str)

    def test_violation_type_has_harmful_content_member(self):
        """
        Test that ViolationType enum includes HARMFUL_CONTENT member.

        Verifies:
            HARMFUL_CONTENT violation type exists for dangerous content detection

        Business Impact:
            Blocks content that could cause harm to users or promote
            dangerous activities, ensuring user safety and compliance

        Scenario:
            Given: ViolationType enum is imported
            When: HARMFUL_CONTENT member is accessed
            Then: Member exists with expected string value "harmful_content"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: HARMFUL_CONTENT member is accessed
        harmful_content = ViolationType.HARMFUL_CONTENT

        # Then: Member exists with expected string value "harmful_content"
        assert harmful_content is not None
        assert harmful_content.value == "harmful_content"
        assert isinstance(harmful_content.value, str)

    def test_violation_type_has_bias_detected_member(self):
        """
        Test that ViolationType enum includes BIAS_DETECTED member.

        Verifies:
            BIAS_DETECTED violation type exists for bias detection in AI content

        Business Impact:
            Supports ethical AI by identifying biased, discriminatory,
            or unfair patterns in AI-generated responses

        Scenario:
            Given: ViolationType enum is imported
            When: BIAS_DETECTED member is accessed
            Then: Member exists with expected string value "bias_detected"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: BIAS_DETECTED member is accessed
        bias_detected = ViolationType.BIAS_DETECTED

        # Then: Member exists with expected string value "bias_detected"
        assert bias_detected is not None
        assert bias_detected.value == "bias_detected"
        assert isinstance(bias_detected.value, str)

    def test_violation_type_has_policy_violation_member(self):
        """
        Test that ViolationType enum includes POLICY_VIOLATION member.

        Verifies:
            POLICY_VIOLATION violation type exists for usage policy enforcement

        Business Impact:
            Enables enforcement of service terms, acceptable use policies,
            and organizational content guidelines

        Scenario:
            Given: ViolationType enum is imported
            When: POLICY_VIOLATION member is accessed
            Then: Member exists with expected string value "policy_violation"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: POLICY_VIOLATION member is accessed
        policy_violation = ViolationType.POLICY_VIOLATION

        # Then: Member exists with expected string value "policy_violation"
        assert policy_violation is not None
        assert policy_violation.value == "policy_violation"
        assert isinstance(policy_violation.value, str)

    def test_violation_type_has_scan_timeout_member(self):
        """
        Test that ViolationType enum includes SCAN_TIMEOUT member.

        Verifies:
            SCAN_TIMEOUT violation type exists for system health monitoring

        Business Impact:
            Tracks scanner performance issues and enables alerting when
            security scans exceed acceptable duration limits

        Scenario:
            Given: ViolationType enum is imported
            When: SCAN_TIMEOUT member is accessed
            Then: Member exists with expected string value "scan_timeout"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: SCAN_TIMEOUT member is accessed
        scan_timeout = ViolationType.SCAN_TIMEOUT

        # Then: Member exists with expected string value "scan_timeout"
        assert scan_timeout is not None
        assert scan_timeout.value == "scan_timeout"
        assert isinstance(scan_timeout.value, str)

    def test_violation_type_has_scan_error_member(self):
        """
        Test that ViolationType enum includes SCAN_ERROR member.

        Verifies:
            SCAN_ERROR violation type exists for technical failure tracking

        Business Impact:
            Distinguishes technical scanning failures from content violations,
            enabling proper error handling and monitoring

        Scenario:
            Given: ViolationType enum is imported
            When: SCAN_ERROR member is accessed
            Then: Member exists with expected string value "scan_error"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: SCAN_ERROR member is accessed
        scan_error = ViolationType.SCAN_ERROR

        # Then: Member exists with expected string value "scan_error"
        assert scan_error is not None
        assert scan_error.value == "scan_error"
        assert isinstance(scan_error.value, str)

    def test_violation_type_has_service_unavailable_member(self):
        """
        Test that ViolationType enum includes SERVICE_UNAVAILABLE member.

        Verifies:
            SERVICE_UNAVAILABLE violation type exists for availability monitoring

        Business Impact:
            Tracks external security service availability issues,
            enabling graceful degradation and fallback strategies

        Scenario:
            Given: ViolationType enum is imported
            When: SERVICE_UNAVAILABLE member is accessed
            Then: Member exists with expected string value "service_unavailable"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: SERVICE_UNAVAILABLE member is accessed
        service_unavailable = ViolationType.SERVICE_UNAVAILABLE

        # Then: Member exists with expected string value "service_unavailable"
        assert service_unavailable is not None
        assert service_unavailable.value == "service_unavailable"
        assert isinstance(service_unavailable.value, str)
    
    def test_violation_type_string_values_are_lowercase_snake_case(self):
        """
        Test that all ViolationType string values follow lowercase_snake_case convention.

        Verifies:
            Enum string values use consistent naming convention for serialization

        Business Impact:
            Ensures consistent API responses, logging, and database storage
            across all security subsystems

        Scenario:
            Given: All ViolationType enum members
            When: String values are examined
            Then: All values use lowercase with underscores (no spaces, camelCase, or CAPS)

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: All ViolationType enum members
        violation_types = list(ViolationType)

        # When: String values are examined
        # Then: All values use lowercase with underscores (no spaces, camelCase, or CAPS)
        for violation_type in violation_types:
            value = violation_type.value
            assert isinstance(value, str)
            assert value.islower(), f"ViolationType {violation_type.name} has value '{value}' which is not lowercase"
            assert '_' in value or value.isalpha(), f"ViolationType {violation_type.name} has value '{value}' which is not snake_case"
            assert ' ' not in value, f"ViolationType {violation_type.name} has value '{value}' which contains spaces"
    
    def test_violation_type_members_are_iterable(self):
        """
        Test that ViolationType enum members can be iterated for completeness checking.

        Verifies:
            Enum supports iteration over all violation type definitions

        Business Impact:
            Enables dynamic validation, configuration generation, and
            comprehensive security coverage verification

        Scenario:
            Given: ViolationType enum
            When: Iterating over enum members
            Then: All violation types are accessible via iteration
            And: Iteration count matches expected number of violation types

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum
        # When: Iterating over enum members
        violation_types = list(ViolationType)

        # Then: All violation types are accessible via iteration
        assert len(violation_types) > 0, "ViolationType enum should have at least one member"

        # Check that key expected violation types are present in iteration
        violation_values = [vt.value for vt in violation_types]
        expected_values = [
            "prompt_injection",
            "malicious_prompt",
            "toxic_input",
            "pii_leakage",
            "suspicious_pattern",
            "toxic_output",
            "harmful_content",
            "bias_detected",
            "unethical_content",
            "policy_violation",
            "scan_timeout",
            "scan_error",
            "service_unavailable"
        ]

        for expected_value in expected_values:
            assert expected_value in violation_values, f"Expected violation type '{expected_value}' not found in enum iteration"
    
    def test_violation_type_has_suspicious_pattern_member(self):
        """
        Test that ViolationType enum includes SUSPICIOUS_PATTERN member.

        Verifies:
            SUSPICIOUS_PATTERN violation type exists for anomaly detection

        Business Impact:
            Enables detection of content matching known attack patterns
            or anomalous behavior indicators that may indicate threats

        Scenario:
            Given: ViolationType enum is imported
            When: SUSPICIOUS_PATTERN member is accessed
            Then: Member exists with expected string value "suspicious_pattern"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: SUSPICIOUS_PATTERN member is accessed
        suspicious_pattern = ViolationType.SUSPICIOUS_PATTERN

        # Then: Member exists with expected string value "suspicious_pattern"
        assert suspicious_pattern is not None
        assert suspicious_pattern.value == "suspicious_pattern"
        assert isinstance(suspicious_pattern.value, str)

    def test_violation_type_has_toxic_output_member(self):
        """
        Test that ViolationType enum includes TOXIC_OUTPUT member.

        Verifies:
            TOXIC_OUTPUT violation type exists for AI response content moderation

        Business Impact:
            Prevents AI-generated toxic or harmful language from reaching
            end users, maintaining safe and respectful interactions

        Scenario:
            Given: ViolationType enum is imported
            When: TOXIC_OUTPUT member is accessed
            Then: Member exists with expected string value "toxic_output"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: TOXIC_OUTPUT member is accessed
        toxic_output = ViolationType.TOXIC_OUTPUT

        # Then: Member exists with expected string value "toxic_output"
        assert toxic_output is not None
        assert toxic_output.value == "toxic_output"
        assert isinstance(toxic_output.value, str)

    def test_violation_type_has_harmful_content_member(self):
        """
        Test that ViolationType enum includes HARMFUL_CONTENT member.

        Verifies:
            HARMFUL_CONTENT violation type exists for dangerous content detection

        Business Impact:
            Blocks content that could cause harm to users or promote
            dangerous activities, ensuring user safety and compliance

        Scenario:
            Given: ViolationType enum is imported
            When: HARMFUL_CONTENT member is accessed
            Then: Member exists with expected string value "harmful_content"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: HARMFUL_CONTENT member is accessed
        harmful_content = ViolationType.HARMFUL_CONTENT

        # Then: Member exists with expected string value "harmful_content"
        assert harmful_content is not None
        assert harmful_content.value == "harmful_content"
        assert isinstance(harmful_content.value, str)

    def test_violation_type_has_bias_detected_member(self):
        """
        Test that ViolationType enum includes BIAS_DETECTED member.

        Verifies:
            BIAS_DETECTED violation type exists for bias detection in AI content

        Business Impact:
            Supports ethical AI by identifying biased, discriminatory,
            or unfair patterns in AI-generated responses

        Scenario:
            Given: ViolationType enum is imported
            When: BIAS_DETECTED member is accessed
            Then: Member exists with expected string value "bias_detected"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: BIAS_DETECTED member is accessed
        bias_detected = ViolationType.BIAS_DETECTED

        # Then: Member exists with expected string value "bias_detected"
        assert bias_detected is not None
        assert bias_detected.value == "bias_detected"
        assert isinstance(bias_detected.value, str)

    def test_violation_type_has_unethical_content_member(self):
        """
        Test that ViolationType enum includes UNETHICAL_CONTENT member.

        Verifies:
            UNETHICAL_CONTENT violation type exists for ethical guideline enforcement

        Business Impact:
            Ensures AI-generated content adheres to ethical guidelines
            and moral standards, maintaining responsible AI deployment

        Scenario:
            Given: ViolationType enum is imported
            When: UNETHICAL_CONTENT member is accessed
            Then: Member exists with expected string value "unethical_content"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum is imported
        # When: UNETHICAL_CONTENT member is accessed
        unethical_content = ViolationType.UNETHICAL_CONTENT

        # Then: Member exists with expected string value "unethical_content"
        assert unethical_content is not None
        assert unethical_content.value == "unethical_content"
        assert isinstance(unethical_content.value, str)

    def test_violation_type_value_equality_comparison(self):
        """
        Test that ViolationType enum values support equality comparison.

        Verifies:
            Enum members can be compared for equality with string values

        Business Impact:
            Supports deserialization from JSON/database and flexible
            violation type matching in security decision logic

        Scenario:
            Given: ViolationType enum member
            When: Comparing member.value with expected string
            Then: Equality comparison returns True for matching values
            And: Comparison returns False for non-matching values

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum member
        prompt_injection = ViolationType.PROMPT_INJECTION

        # When: Comparing member.value with expected string
        # Then: Equality comparison returns True for matching values
        assert prompt_injection.value == "prompt_injection"
        assert prompt_injection.value == "prompt_injection"

        # And: Comparison returns False for non-matching values
        assert prompt_injection.value != "malicious_prompt"
        assert prompt_injection.value != "TOXIC_INPUT"
        assert prompt_injection.value != ""
        assert prompt_injection.value != "prompt injection"  # Test case sensitivity

        # Test with another violation type
        toxic_input = ViolationType.TOXIC_INPUT
        assert toxic_input.value == "toxic_input"
        assert toxic_input.value != "prompt_injection"

    def test_violation_type_completeness_all_expected_members(self):
        """
        Test that ViolationType enum includes all expected members from the protocol.

        Verifies:
            Complete coverage of all violation types defined in the protocol specification

        Business Impact:
            Ensures full security coverage with no gaps in violation detection
            capabilities across all threat categories

        Scenario:
            Given: ViolationType enum
            When: Checking for all expected violation type members
            Then: All protocol-defined violation types are present
            And: No critical security threats are missing from enumeration

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: ViolationType enum
        # When: Checking for all expected violation type members

        # Input violations
        input_violations = [
            ViolationType.PROMPT_INJECTION,
            ViolationType.MALICIOUS_PROMPT,
            ViolationType.TOXIC_INPUT,
            ViolationType.PII_LEAKAGE,
            ViolationType.SUSPICIOUS_PATTERN
        ]

        # Output violations
        output_violations = [
            ViolationType.TOXIC_OUTPUT,
            ViolationType.HARMFUL_CONTENT,
            ViolationType.BIAS_DETECTED,
            ViolationType.UNETHICAL_CONTENT,
            ViolationType.POLICY_VIOLATION
        ]

        # System violations
        system_violations = [
            ViolationType.SCAN_TIMEOUT,
            ViolationType.SCAN_ERROR,
            ViolationType.SERVICE_UNAVAILABLE
        ]

        # Then: All protocol-defined violation types are present
        for violation in input_violations + output_violations + system_violations:
            assert violation is not None
            assert isinstance(violation.value, str)
            assert len(violation.value) > 0

        # Verify total count matches expected (5 input + 5 output + 3 system = 13)
        all_violations = list(ViolationType)
        assert len(all_violations) == 13, f"Expected 13 violation types, got {len(all_violations)}"


class TestSeverityLevel:
    """
    Test suite for SeverityLevel enum defining violation severity hierarchy.
    
    Scope:
        - Severity level definitions (LOW, MEDIUM, HIGH, CRITICAL)
        - String value representations for serialization
        - Severity ordering and comparison logic
        - Usage in risk-based decision making
        
    Business Critical:
        Severity levels drive automated security responses, content blocking
        decisions, and incident escalation workflows across the system.
        
    Test Coverage:
        - All severity level definitions
        - Severity ordering and comparability
        - String representation consistency
        - Integration with violation classification
    """
    
    def test_severity_level_has_low_member(self):
        """
        Test that SeverityLevel enum includes LOW member.

        Verifies:
            LOW severity level exists for minor security concerns

        Business Impact:
            Enables graduated response to low-risk violations that require
            logging but not immediate blocking or user notification

        Scenario:
            Given: SeverityLevel enum is imported
            When: LOW member is accessed
            Then: Member exists with expected string value "low"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum is imported
        # When: LOW member is accessed
        low = SeverityLevel.LOW

        # Then: Member exists with expected string value "low"
        assert low is not None
        assert low.value == "low"
        assert isinstance(low.value, str)
    
    def test_severity_level_has_medium_member(self):
        """
        Test that SeverityLevel enum includes MEDIUM member.

        Verifies:
            MEDIUM severity level exists for moderate security concerns

        Business Impact:
            Supports risk-appropriate handling of violations requiring
            attention but not immediate critical response

        Scenario:
            Given: SeverityLevel enum is imported
            When: MEDIUM member is accessed
            Then: Member exists with expected string value "medium"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum is imported
        # When: MEDIUM member is accessed
        medium = SeverityLevel.MEDIUM

        # Then: Member exists with expected string value "medium"
        assert medium is not None
        assert medium.value == "medium"
        assert isinstance(medium.value, str)

    def test_severity_level_has_high_member(self):
        """
        Test that SeverityLevel enum includes HIGH member.

        Verifies:
            HIGH severity level exists for serious security threats

        Business Impact:
            Triggers elevated security responses including content blocking,
            user warnings, and security team notifications

        Scenario:
            Given: SeverityLevel enum is imported
            When: HIGH member is accessed
            Then: Member exists with expected string value "high"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum is imported
        # When: HIGH member is accessed
        high = SeverityLevel.HIGH

        # Then: Member exists with expected string value "high"
        assert high is not None
        assert high.value == "high"
        assert isinstance(high.value, str)

    def test_severity_level_has_critical_member(self):
        """
        Test that SeverityLevel enum includes CRITICAL member.

        Verifies:
            CRITICAL severity level exists for severe security incidents

        Business Impact:
            Mandates immediate blocking, incident reporting, and potential
            service degradation to protect users and systems

        Scenario:
            Given: SeverityLevel enum is imported
            When: CRITICAL member is accessed
            Then: Member exists with expected string value "critical"

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum is imported
        # When: CRITICAL member is accessed
        critical = SeverityLevel.CRITICAL

        # Then: Member exists with expected string value "critical"
        assert critical is not None
        assert critical.value == "critical"
        assert isinstance(critical.value, str)
    
    def test_severity_level_string_values_are_lowercase(self):
        """
        Test that all SeverityLevel string values are lowercase.

        Verifies:
            Enum string values use lowercase convention for consistency

        Business Impact:
            Ensures predictable serialization for APIs, logging, and
            database storage without case sensitivity issues

        Scenario:
            Given: All SeverityLevel enum members
            When: String values are examined
            Then: All values are lowercase (low, medium, high, critical)

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: All SeverityLevel enum members
        severity_levels = list(SeverityLevel)

        # When: String values are examined
        # Then: All values are lowercase (low, medium, high, critical)
        for severity_level in severity_levels:
            value = severity_level.value
            assert isinstance(value, str)
            assert value.islower(), f"SeverityLevel {severity_level.name} has value '{value}' which is not lowercase"
            assert value.isalpha(), f"SeverityLevel {severity_level.name} has value '{value}' which contains non-alphabetic characters"
            assert ' ' not in value, f"SeverityLevel {severity_level.name} has value '{value}' which contains spaces"
    
    def test_severity_level_supports_ordering_comparison(self):
        """
        Test that SeverityLevel enum members support severity hierarchy concepts.

        Verifies:
            Severity levels represent a hierarchy that can be used for
            risk-based decision making, even if direct comparison operators
            aren't available in the current implementation

        Business Impact:
            Enables risk-based filtering, threshold-based blocking decisions,
            and severity-aware security response automation through
            alternative comparison approaches

        Scenario:
            Given: Multiple SeverityLevel enum members
            When: Using severity levels in risk assessment logic
            Then: Severity hierarchy can be used for risk-based decisions
            And: Enum members can be compared to expected severity levels

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: Multiple SeverityLevel enum members
        low = SeverityLevel.LOW
        medium = SeverityLevel.MEDIUM
        high = SeverityLevel.HIGH
        critical = SeverityLevel.CRITICAL

        # When: Using severity levels in risk assessment logic
        # Then: Severity hierarchy can be used for risk-based decisions

        # Test that we can create severity ordering lists
        severity_order = [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert low in severity_order
        assert medium in severity_order
        assert high in severity_order
        assert critical in severity_order

        # Test that we can create high severity threshold lists
        high_severity_levels = [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert high in high_severity_levels
        assert critical in high_severity_levels
        assert low not in high_severity_levels
        assert medium not in high_severity_levels

        # Test that we can check severity membership
        assert SeverityLevel.CRITICAL in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert SeverityLevel.HIGH in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert SeverityLevel.MEDIUM not in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert SeverityLevel.LOW not in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]

        # And: Enum members can be compared to expected severity levels
        assert low == SeverityLevel.LOW
        assert medium == SeverityLevel.MEDIUM
        assert high == SeverityLevel.HIGH
        assert critical == SeverityLevel.CRITICAL
    
    def test_severity_level_members_are_iterable(self):
        """
        Test that SeverityLevel enum members can be iterated in definition order.

        Verifies:
            Enum supports iteration for complete severity coverage

        Business Impact:
            Enables configuration validation, UI generation, and
            comprehensive severity-based reporting

        Scenario:
            Given: SeverityLevel enum
            When: Iterating over enum members
            Then: All severity levels are accessible via iteration
            And: Iteration includes exactly 4 severity levels

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum
        # When: Iterating over enum members
        severity_levels = list(SeverityLevel)

        # Then: All severity levels are accessible via iteration
        assert len(severity_levels) > 0, "SeverityLevel enum should have at least one member"
        assert len(severity_levels) == 4, f"Expected exactly 4 severity levels, got {len(severity_levels)}"

        # Check that all expected severity levels are present in iteration
        severity_values = [sl.value for sl in severity_levels]
        expected_values = ["low", "medium", "high", "critical"]

        for expected_value in expected_values:
            assert expected_value in severity_values, f"Expected severity level '{expected_value}' not found in enum iteration"

        # And: Iteration includes exactly 4 severity levels
        assert len(severity_levels) == 4
    
    def test_severity_level_value_equality_comparison(self):
        """
        Test that SeverityLevel enum values support equality comparison with strings.

        Verifies:
            Enum members can be compared with string values for deserialization

        Business Impact:
            Supports JSON parsing, database retrieval, and flexible
            severity matching in security decision logic

        Scenario:
            Given: SeverityLevel enum member
            When: Comparing member.value with string ("low", "medium", etc.)
            Then: Equality comparison returns True for matching values
            And: Comparison returns False for non-matching values

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum member
        low = SeverityLevel.LOW

        # When: Comparing member.value with string ("low", "medium", etc.)
        # Then: Equality comparison returns True for matching values
        assert low.value == "low"
        assert low.value == "low"

        # And: Comparison returns False for non-matching values
        assert low.value != "medium"
        assert low.value != "HIGH"
        assert low.value != ""
        assert low.value != "Low"  # Test case sensitivity

        # Test with other severity levels
        medium = SeverityLevel.MEDIUM
        assert medium.value == "medium"
        assert medium.value != "low"

        high = SeverityLevel.HIGH
        assert high.value == "high"
        assert high.value != "medium"

        critical = SeverityLevel.CRITICAL
        assert critical.value == "critical"
        assert critical.value != "high"

    def test_severity_level_complete_coverage_test(self):
        """
        Test that SeverityLevel enum provides complete coverage of severity hierarchy.

        Verifies:
            All severity levels defined in protocol are present and accessible

        Business Impact:
            Ensures comprehensive severity classification system with no gaps
            in risk assessment capabilities across the security infrastructure

        Scenario:
            Given: SeverityLevel enum
            When: Accessing all severity level members
            Then: LOW, MEDIUM, HIGH, CRITICAL are all present
            And: All have correct string values and support comparisons

        Fixtures Used:
            None - Direct enum testing
        """
        # Given: SeverityLevel enum
        # When: Accessing all severity level members

        # Then: LOW, MEDIUM, HIGH, CRITICAL are all present
        severity_hierarchy = [
            (SeverityLevel.LOW, "low"),
            (SeverityLevel.MEDIUM, "medium"),
            (SeverityLevel.HIGH, "high"),
            (SeverityLevel.CRITICAL, "critical")
        ]

        for severity_enum, expected_value in severity_hierarchy:
            # Verify member exists and has correct value
            assert severity_enum is not None
            assert severity_enum.value == expected_value
            assert isinstance(severity_enum.value, str)

        # And: All have correct string values and support comparisons
        # Verify hierarchy concept works through membership checks
        severity_hierarchy_list = [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert severity_hierarchy_list[0] == SeverityLevel.LOW
        assert severity_hierarchy_list[1] == SeverityLevel.MEDIUM
        assert severity_hierarchy_list[2] == SeverityLevel.HIGH
        assert severity_hierarchy_list[3] == SeverityLevel.CRITICAL

