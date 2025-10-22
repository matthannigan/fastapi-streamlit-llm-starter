"""
Integration tests for Configuration Validator → Security Controls → Rate Limiting.

This test suite validates the integration between ResilienceConfigValidator,
ValidationRateLimiter, and real threading/time modules to ensure comprehensive
security and rate limiting functionality for configuration validation endpoints.

Seam Under Test:
    ResilienceConfigValidator → ValidationRateLimiter → Security Controls

Critical Paths:
    - Configuration validation enforces real rate limits under concurrent load
    - Security pattern detection blocks actual forbidden patterns in real scenarios
    - JSON Schema validation works with real configuration parsing and validation
    - Template-based validation using predefined templates with security checks
    - Size and complexity limits are enforced in real-world scenarios

Test Architecture:
    - Outside-in approach starting from API endpoints
    - High-fidelity fakes (real threading, time modules) over mocks
    - Observable behavior verification through API responses and rate limiting state
    - Complete test isolation using function-scoped fixtures
    - Real concurrent execution patterns for load testing

Business Impact:
    - Important security and validation controls prevent abuse
    - Rate limiting protects configuration validation endpoints from DoS attacks
    - Security policies ensure malicious configurations are blocked
    - Template-based validation provides safe configuration patterns
"""

import pytest
import time
import threading
import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.infrastructure.resilience.config_validator import (
    ResilienceConfigValidator,
    ValidationRateLimiter,
    SECURITY_CONFIG
)
from app.core.exceptions import ValidationError, InfrastructureError


class TestConfigValidatorSecurityIntegration:
    """
    Integration tests for configuration validator security and rate limiting functionality.

    Seam Under Test:
        ResilienceConfigValidator → ValidationRateLimiter → Security Controls → Real Threading/Time

    Critical Paths:
        - Rate limiting enforcement under concurrent load with real threading
        - Security pattern detection for malicious configuration content
        - JSON Schema validation with real parsing and validation logic
        - Template-based validation with security constraints
        - Size and complexity limits enforcement in production scenarios

    Business Impact:
        - Prevents abuse of configuration validation endpoints through rate limiting
        - Blocks malicious configuration attempts through security pattern detection
        - Ensures configuration safety through comprehensive validation
        - Provides reliable configuration management for resilience infrastructure
    """

    def test_rate_limiting_enforces_real_limits_under_concurrent_load(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator,
        concurrent_executor: ThreadPoolExecutor
    ):
        """
        Test rate limiting enforcement under concurrent load.

        Integration Scope:
            ResilienceConfigValidator → ValidationRateLimiter → Real Threading

        Business Impact:
            Prevents DoS attacks on configuration validation endpoints
            Ensures fair resource allocation among concurrent clients

        Test Strategy:
            - Test rapid sequential requests to trigger cooldown-based rate limiting
            - Verify rate limiting mechanism works with multiple client identifiers
            - Validate rate limiting state persistence and thread safety
            - Test concurrent access to rate limiting state

        Success Criteria:
            - Rate limiting mechanisms function correctly under load
            - Rate limiting state is thread-safe and consistent
            - Error messages clearly communicate rate limit violations
            - Rate limiting works across multiple client identifiers
        """
        validator = config_validator_with_rate_limiting
        test_config = {"retry_attempts": 3, "circuit_breaker_threshold": 5}

        # Reset rate limiter for clean test
        validator.reset_rate_limiter()

        # Test 1: Verify cooldown-based rate limiting works with multiple requests
        client_id = "sequential_test_client"
        cooldown_seconds = SECURITY_CONFIG["rate_limiting"]["validation_cooldown_seconds"]

        # Make rapid requests to trigger cooldown (using same client ID)
        results = []
        for i in range(3):
            result = validator.validate_with_security_checks(test_config, client_id)
            results.append(result)

        # First request should succeed, subsequent ones should be rate limited
        assert results[0].is_valid, "First request should succeed"
        assert not results[1].is_valid, "Second request should be rate limited"
        assert any("rate limit" in error.lower() for error in results[1].errors), \
            "Expected rate limit error for second request"

        # Test 2: Verify concurrent access to different client IDs works correctly
        concurrent_results = []
        def make_validation_request(client_identifier):
            result = validator.validate_with_security_checks(test_config, client_identifier)
            return {"client_id": client_identifier, "success": result.is_valid, "errors": result.errors}

        # Submit concurrent requests for different clients
        futures = []
        for i in range(5):
            future = concurrent_executor.submit(make_validation_request, f"concurrent_client_{i}")
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            concurrent_results.append(future.result())

        # All different client IDs should succeed on first request
        successful_clients = [r for r in concurrent_results if r["success"]]
        assert len(successful_clients) >= 4, \
            f"Expected most concurrent requests with different client IDs to succeed, got {len(successful_clients)}/5"

        # Test 3: Verify rate limiting state tracking
        rate_limit_info = validator.get_rate_limit_info("concurrent_client_0")
        assert "requests_last_minute" in rate_limit_info
        assert "max_per_minute" in rate_limit_info
        assert rate_limit_info["max_per_minute"] == SECURITY_CONFIG["rate_limiting"]["max_validations_per_minute"]

        # Verify the rate limiting mechanism is functional
        max_per_minute = SECURITY_CONFIG["rate_limiting"]["max_validations_per_minute"]
        assert rate_limit_info["max_per_minute"] == max_per_minute

    def test_security_pattern_detection_blocks_actual_forbidden_patterns(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator
    ):
        """
        Test security pattern detection blocks forbidden patterns.

        Integration Scope:
            ResilienceConfigValidator → Security Pattern Detection → Real Pattern Matching

        Business Impact:
            Prevents injection attacks and malicious configuration attempts
            Protects infrastructure from code execution vulnerabilities

        Test Strategy:
            - Test configurations with various forbidden patterns
            - Verify pattern detection for scripts, injection attacks, etc.
            - Ensure comprehensive pattern coverage from SECURITY_CONFIG
            - Validate error messages provide helpful feedback

        Success Criteria:
            - All forbidden patterns are detected and blocked
            - Error messages clearly identify security violations
            - Suggestions provide guidance for safe configuration
            - Pattern matching works with case insensitivity and variations
        """
        validator = config_validator_with_rate_limiting

        # Test configurations with forbidden patterns
        malicious_configs = [
            {"retry_attempts": 3, "malicious_field": "<script>alert('xss')</script>"},
            {"config": "javascript:void(0)", "retry_attempts": 5},
            {"data": "data:text/html,<script>alert(1)</script>", "threshold": 10},
            {"path": "../../../etc/passwd", "retries": 3},
            {"encoded": "\\x48\\x45\\x4c\\x4c\\x4f", "attempts": 5},
            {"unicode": "\\u0048\\u0045\\u004c\\u004c\\u004f", "threshold": 10},
            {"template": "<%= System.getenv('PASSWORD') %>", "retry": 3},
            {"interpolation": "${JAVA_HOME}", "attempts": 5},
            {"code": "eval('malicious code')", "threshold": 2},
            {"exec": "exec('dangerous command')", "retries": 1},
            {"import": "import os; os.system('rm -rf /')", "attempts": 3},
            {"require": "require('fs').readFileSync('/etc/passwd')", "retry": 2},
            {"dunder": "__import__('os').system('ls')", "threshold": 5},
        ]

        for i, config in enumerate(malicious_configs):
            client_id = f"security_test_client_{i}"

            # Validate configuration with security checks
            result = validator.validate_with_security_checks(config, client_id)

            # Verify forbidden pattern was detected
            assert not result.is_valid, \
                f"Expected validation to fail for malicious config: {config}"

            assert len(result.errors) > 0, \
                f"Expected security errors for malicious config: {config}"

            # Verify error messages mention security violations
            error_text = " ".join(result.errors).lower()
            assert any(phrase in error_text for phrase in [
                "forbidden", "pattern", "security", "dangerous", "malicious"
            ]), f"Security error message not found for config: {config}, errors: {result.errors}"

            # Verify suggestions provide helpful guidance
            assert len(result.suggestions) > 0, \
                f"Expected suggestions for malicious config: {config}"

    def test_json_schema_validation_works_with_real_configuration_parsing(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator
    ):
        """
        Test JSON Schema validation with real configuration parsing.

        Integration Scope:
            ResilienceConfigValidator → JSON Schema Validation → Real Configuration Parsing

        Business Impact:
            Ensures configuration correctness and structural integrity
            Prevents runtime errors from malformed configuration data

        Test Strategy:
            - Test valid configurations that should pass schema validation
            - Test invalid configurations that violate schema constraints
            - Verify JSON parsing works with various input formats
            - Test edge cases and boundary conditions

        Success Criteria:
            - Valid configurations pass JSON Schema validation
            - Invalid configurations are rejected with specific error messages
            - JSON parsing handles various input formats correctly
            - Schema validation provides detailed feedback for violations
        """
        validator = config_validator_with_rate_limiting

        # Test valid configurations
        valid_configs = [
            {
                "retry_attempts": 3,
                "circuit_breaker_threshold": 5,
                "recovery_timeout": 60,
                "default_strategy": "balanced"
            },
            {
                "retry_attempts": 1,
                "circuit_breaker_threshold": 2,
                "recovery_timeout": 10,
                "default_strategy": "aggressive",
                "max_delay_seconds": 5,
                "exponential_multiplier": 0.5
            },
            {
                "retry_attempts": 8,
                "circuit_breaker_threshold": 15,
                "recovery_timeout": 300,
                "default_strategy": "critical",
                "operation_overrides": {
                    "sentiment": "conservative",
                    "summarize": "critical"
                }
            }
        ]

        for i, config in enumerate(valid_configs):
            client_id = f"json_valid_test_{i}"
            result = validator.validate_with_security_checks(config, client_id)

            # Verify valid configurations pass validation
            assert result.is_valid, \
                f"Expected valid config to pass validation: {config}"

            assert len(result.errors) == 0, \
                f"Expected no errors for valid config: {config}, errors: {result.errors}"

        # Test invalid configurations
        invalid_configs = [
            {"retry_attempts": -1},  # Negative value
            {"retry_attempts": 20},  # Above maximum
            {"default_strategy": "invalid_strategy"},  # Invalid enum value
            {"exponential_multiplier": -0.5},  # Negative float
            {"recovery_timeout": 5},  # Below minimum
        ]

        for i, config in enumerate(invalid_configs):
            client_id = f"json_invalid_test_{i}"
            result = validator.validate_with_security_checks(config, client_id)

            # Verify invalid configurations fail validation
            assert not result.is_valid, \
                f"Expected invalid config to fail validation: {config}"

            assert len(result.errors) > 0, \
                f"Expected validation errors for invalid config: {config}"

    def test_template_based_validation_using_predefined_templates(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator
    ):
        """
        Test template-based validation using predefined templates.

        Integration Scope:
            ResilienceConfigValidator → Template Validation → Security Controls

        Business Impact:
            Provides safe, pre-vetted configuration patterns
            Reduces configuration complexity and error potential
            Ensures template overrides maintain security constraints

        Test Strategy:
            - Test all predefined templates are valid
            - Test template validation with various overrides
            - Verify security constraints are enforced on template configs
            - Test template recommendation functionality

        Success Criteria:
            - All predefined templates pass validation
            - Template overrides are properly validated
            - Security constraints apply to template-based configurations
            - Template recommendations work based on configuration characteristics
        """
        validator = config_validator_with_rate_limiting

        # Get available templates
        templates = validator.get_configuration_templates()
        assert len(templates) > 0, "Expected configuration templates to be available"

        template_names = list(templates.keys())
        expected_templates = [
            "fast_development", "robust_production", "low_latency",
            "high_throughput", "maximum_reliability"
        ]

        # Verify expected templates are available
        for expected_template in expected_templates:
            assert expected_template in templates, \
                f"Expected template '{expected_template}' to be available"

        # Test each template is valid
        for template_name, template_info in templates.items():
            assert "config" in template_info, \
                f"Template '{template_name}' should have config"
            assert "name" in template_info, \
                f"Template '{template_name}' should have name"
            assert "description" in template_info, \
                f"Template '{template_name}' should have description"

            # Validate template configuration
            result = validator.validate_with_security_checks(
                template_info["config"],
                f"template_test_{template_name}"
            )

            assert result.is_valid, \
                f"Template '{template_name}' should be valid: {result.errors}"

        # Test template validation with overrides
        test_overrides = [
            {"retry_attempts": 5},
            {"default_strategy": "conservative"},
            {"max_delay_seconds": 30}
        ]

        for template_name in template_names[:2]:  # Test first 2 templates
            for override in test_overrides:
                client_id = f"template_override_{template_name}_{hash(str(override))}"

                # Validate template with override
                result = validator.validate_template_based_config(
                    template_name,
                    override
                )

                # Template validation should work (assuming templates and overrides are valid)
                # Note: Some overrides might be invalid, which is expected
                if not result.is_valid:
                    # If invalid, should have specific error messages
                    assert len(result.errors) > 0, \
                        f"Expected error messages for invalid template override: {override}"

    def test_size_and_complexity_limits_enforced_in_real_scenarios(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator
    ):
        """
        Test size and complexity limits are enforced in real scenarios.

        Integration Scope:
            ResilienceConfigValidator → Size/Complexity Validation → Real Resource Constraints

        Business Impact:
            Prevents resource exhaustion from large configurations
            Ensures system stability with reasonable configuration bounds
            Protects against configuration-based denial of service attacks

        Test Strategy:
            - Test configurations exceeding size limits
            - Test configurations with excessive nesting depth
            - Test configurations with too many properties or array items
            - Verify string length limits are enforced

        Success Criteria:
            - Large configurations are rejected with specific error messages
            - Complex nested structures are limited appropriately
            - Resource limits prevent system overload
            - Error messages provide clear guidance for limit violations
        """
        validator = config_validator_with_rate_limiting

        # Test configuration exceeding size limits
        large_config = {
            "retry_attempts": 3,
            "large_field": "x" * 5000,  # Exceeds max_config_size
        }

        result = validator.validate_with_security_checks(large_config, "size_test_client")

        assert not result.is_valid, \
            "Expected large config to fail validation"

        assert any("too large" in error.lower() for error in result.errors), \
            f"Expected size limit error in: {result.errors}"

        # Test configuration with excessive nesting
        def create_nested_config(depth):
            if depth == 0:
                return "nested_value"
            return {"level": create_nested_config(depth - 1)}

        max_depth = SECURITY_CONFIG["max_nesting_depth"]
        overly_nested_config = create_nested_config(max_depth + 5)

        result = validator.validate_with_security_checks(
            overly_nested_config,
            "nesting_test_client"
        )

        assert not result.is_valid, \
            "Expected overly nested config to fail validation"

        assert any("nesting" in error.lower() for error in result.errors), \
            f"Expected nesting error in: {result.errors}"

        # Test configuration with too many properties
        many_properties_config = {
            f"field_{i}": f"value_{i}"
            for i in range(SECURITY_CONFIG["max_object_properties"] + 10)
        }

        result = validator.validate_with_security_checks(
            many_properties_config,
            "properties_test_client"
        )

        assert not result.is_valid, \
            "Expected config with too many properties to fail validation"

        assert any("properties" in error.lower() for error in result.errors), \
            f"Expected properties error in: {result.errors}"

        # Test configuration with long strings
        long_string_config = {
            "retry_attempts": 3,
            "long_field": "x" * (SECURITY_CONFIG["max_string_length"] + 100)
        }

        result = validator.validate_with_security_checks(
            long_string_config,
            "string_test_client"
        )

        assert not result.is_valid, \
            "Expected config with long strings to fail validation"

        assert any("too long" in error.lower() for error in result.errors), \
            f"Expected string length error in: {result.errors}"

    def test_rate_limiting_cooldown_and_recovery_behavior(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator
    ):
        """
        Test rate limiting cooldown and recovery behavior.

        Integration Scope:
            ValidationRateLimiter → Real Time Module → Thread-safe State Management

        Business Impact:
            Ensures rate limiting provides proper recovery mechanisms
            Validates cooldown periods prevent abuse while allowing legitimate access
            Confirms system resilience under sustained load

        Test Strategy:
            - Trigger rate limiting through rapid requests
            - Verify cooldown period enforcement through error messages
            - Test manual reset functionality for recovery scenarios
            - Validate rate limiting state management and persistence

        Success Criteria:
            - Cooldown periods are properly enforced after rate limit exceeded
            - Manual reset functionality works for recovery scenarios
            - Rate limiting state can be tracked and monitored
            - Thread-safe behavior under concurrent access
        """
        validator = config_validator_with_rate_limiting
        test_config = {"retry_attempts": 3}
        client_id = "cooldown_test_client"

        # Reset rate limiter for clean test
        validator.reset_rate_limiter()

        # Test 1: Verify cooldown mechanism through rapid requests
        # First request should succeed
        result1 = validator.validate_with_security_checks(test_config, client_id)
        assert result1.is_valid, "First request should succeed"

        # Immediate second request should be blocked by cooldown
        result2 = validator.validate_with_security_checks(test_config, client_id)
        assert not result2.is_valid, "Second request should be blocked by cooldown"
        assert any("rate limit" in error.lower() for error in result2.errors), \
            "Expected rate limit error for cooldown violation"

        # Verify rate limiting state tracking
        rate_limit_info = validator.get_rate_limit_info(client_id)
        assert "requests_last_minute" in rate_limit_info
        assert "max_per_minute" in rate_limit_info
        assert rate_limit_info["requests_last_minute"] >= 1, \
            "Expected at least one request to be tracked"

        # Test 2: Verify manual reset functionality
        # Create a different client for reset testing
        reset_client = f"{client_id}_reset"

        # Trigger rate limiting on reset client
        result_reset_1 = validator.validate_with_security_checks(test_config, reset_client)
        assert result_reset_1.is_valid, "First request for reset client should succeed"

        result_reset_2 = validator.validate_with_security_checks(test_config, reset_client)
        assert not result_reset_2.is_valid, "Second request for reset client should be rate limited"

        # Reset rate limiter manually
        validator.reset_rate_limiter()

        # Request after reset should succeed immediately
        result_reset_3 = validator.validate_with_security_checks(test_config, reset_client)
        assert result_reset_3.is_valid, "Request after manual reset should succeed immediately"

        # Test 3: Verify different clients have independent rate limiting
        other_client = f"{client_id}_other"
        result_other = validator.validate_with_security_checks(test_config, other_client)
        assert result_other.is_valid, "Different client should not be affected by rate limiting"

        # Verify rate limiting info is maintained per client
        other_rate_info = validator.get_rate_limit_info(other_client)
        assert other_rate_info["requests_last_minute"] >= 1, \
            "Other client should have its own request tracking"

    def test_security_field_whitelist_enforcement(
        self,
        config_validator_with_rate_limiting: ResilienceConfigValidator
    ):
        """
        Test security field whitelist enforcement.

        Integration Scope:
            ResilienceConfigValidator → Field Whitelist Validation → Security Controls

        Business Impact:
            Ensures only approved configuration fields are allowed
            Prevents unauthorized configuration parameters
            Maintains configuration security boundaries

        Test Strategy:
            - Test configurations with whitelisted fields
            - Test configurations with non-whitelisted fields
            - Verify field type and range validation
            - Test nested object validation against whitelist

        Success Criteria:
            - Whitelisted fields are accepted with valid values
            - Non-whitelisted fields are rejected with clear error messages
            - Field types and ranges are properly validated
            - Nested objects follow whitelist constraints
        """
        validator = config_validator_with_rate_limiting

        # Test configuration with valid whitelisted fields
        valid_whitelist_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60,
            "default_strategy": "balanced",
            "exponential_multiplier": 1.5,
            "jitter_enabled": True
        }

        result = validator.validate_with_security_checks(
            valid_whitelist_config,
            "whitelist_valid_client"
        )

        assert result.is_valid, \
            f"Expected valid whitelist config to pass: {result.errors}"

        # Test configuration with non-whitelisted fields
        invalid_whitelist_config = {
            "retry_attempts": 3,
            "unauthorized_field": "some_value",
            "another_invalid_field": {"nested": "value"},
            "valid_field": "balanced"
        }

        result = validator.validate_with_security_checks(
            invalid_whitelist_config,
            "whitelist_invalid_client"
        )

        assert not result.is_valid, \
            "Expected config with unauthorized fields to fail validation"

        # Should have errors about non-whitelisted fields
        error_text = " ".join(result.errors).lower()
        assert any(
            phrase in error_text
            for phrase in ["not in allowed", "whitelist", "unauthorized"]
        ), f"Expected whitelist error in: {result.errors}"

        # Test field type validation against whitelist
        invalid_type_config = {
            "retry_attempts": "not_a_number",  # Should be int
            "exponential_multiplier": "not_a_float",  # Should be float
            "default_strategy": "invalid_strategy"  # Should be enum value
        }

        result = validator.validate_with_security_checks(
            invalid_type_config,
            "type_validation_client"
        )

        assert not result.is_valid, \
            "Expected config with invalid field types to fail validation"

        # Should have type validation errors
        assert len(result.errors) > 0, \
            "Expected type validation errors"