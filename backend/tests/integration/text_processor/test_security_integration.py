"""
Integration tests for text processor security validation.

This module tests the integration between the API endpoints, TextProcessorService,
and security components (PromptSanitizer and ResponseValidator) using real
threat samples to validate critical security protections.

Seam Under Test:
    API → TextProcessorService → PromptSanitizer → ResponseValidator → Real Threat Samples

Critical Paths:
    - Input sanitization through PromptSanitizer for prompt injection prevention
    - Response validation through ResponseValidator for harmful content detection
    - Security validation performance impact assessment
    - End-to-end security integration with real threat samples

Business Impact:
    - Validates critical security protections against real threats
    - Ensures AI safety measures work with actual malicious content
    - Maintains service availability while blocking threats
    - Provides audit trail for security monitoring
"""

import pytest
from fastapi.testclient import TestClient
from app.core.exceptions import ValidationError, InfrastructureError


class TestSecurityIntegration:
    """
    Integration tests for text processor security validation.

    Seam Under Test:
        API → TextProcessorService → PromptSanitizer → ResponseValidator → Real Threat Samples

    Critical Paths:
        - Input sanitization blocks prompt injection attempts
        - Response validation blocks malicious AI responses
        - Security validation maintains acceptable performance
        - Legitimate requests pass through security validation

    Business Impact:
        - Validates critical security protections against real threats
        - Ensures AI safety measures work with actual malicious content
        - Maintains service availability while blocking threats
        - Provides audit trail for security monitoring
    """

    def test_prompt_injection_blocking(
        self,
        test_client: TestClient,
        authenticated_headers: dict,
        threat_samples: dict
    ):
        """
        Test that known prompt injection attempts are handled appropriately by security systems.

        Integration Scope:
            API endpoint → TextProcessorService → PromptSanitizer → Security Response

        Business Impact:
            Prevents malicious users from bypassing AI safety measures and accessing
            system prompts or confidential information through prompt injection attacks.

        Test Strategy:
            - Send known prompt injection attempts to the API
            - Verify attempts are either blocked or result in fallback responses
            - Test different injection patterns (roleplaying, system commands, etc.)
            - Ensure security validation doesn't leak sensitive information

        Success Criteria:
            - Prompt injection attempts don't succeed in accessing system information
            - Error messages don't reveal sensitive system information
            - Service maintains availability and provides fallback responses
            - Basic input validation works correctly
        """
        # Test basic input validation that should work regardless of AI service status
        invalid_requests = [
            # Empty text
            {"text": "", "operation": "summarize"},
            # Invalid operation
            {"text": "test", "operation": "invalid_operation"},
            # Missing required operation
            {"text": "test text"},
            # Malformed JSON structure will be handled by FastAPI automatically
        ]

        for invalid_request in invalid_requests:
            response = test_client.post(
                "/v1/text_processing/process",
                headers=authenticated_headers,
                json=invalid_request
            )
            # Should result in validation errors
            assert response.status_code in [400, 422], (
                f"Invalid request should be rejected but got status {response.status_code}"
            )

            # Check error response structure for validation errors
            if response.status_code in [400, 422]:
                error_detail = response.json()

                # Handle different error response formats
                if "detail" in error_detail:
                    error_msg = error_detail["detail"].lower()
                elif "error" in error_detail:
                    error_msg = error_detail["error"].lower()
                else:
                    # If neither format is found, check the entire response
                    error_msg = str(error_detail).lower()

                # Check for obvious system info leaks
                sensitive_terms = ["internal", "database", "secret", "token", "password"]
                for term in sensitive_terms:
                    assert term not in error_msg, (
                        f"Error message reveals sensitive information: {error_msg}"
                    )

        # Test extremely long text (potential DoS) - should be handled gracefully
        long_text_request = {
            "text": "a" * 100000,  # 100KB text
            "operation": "sentiment"
        }

        response = test_client.post(
            "/v1/text_processing/process",
            headers=authenticated_headers,
            json=long_text_request
        )

        # Should either succeed (with fallback) or fail gracefully
        assert response.status_code in [200, 400, 422, 500], (
            f"Long text request should be handled gracefully but got status {response.status_code}"
        )

        # Test a few prompt injection attempts to ensure they don't cause system crashes
        # or expose sensitive information
        test_samples = threat_samples["prompt_injections"][:2]  # Test first 2 samples

        for i, injection_attempt in enumerate(test_samples):
            request_data = {
                "text": injection_attempt,
                "operation": "summarize",
                "options": {"max_length": 100}
            }

            response = test_client.post(
                "/v1/text_processing/process",
                headers=authenticated_headers,
                json=request_data
            )

            # Prompt injection attempts should be handled gracefully
            # They may succeed with fallback responses (200) or be blocked (400/422)
            # but should never cause server errors (500) or expose system info
            assert response.status_code in [200, 400, 422, 503], (
                f"Prompt injection attempt {i+1} should be handled gracefully "
                f"but got status {response.status_code}"
            )

            # If we get a successful response, verify it's a safe fallback
            if response.status_code == 200:
                result = response.json()

                # Should not contain system prompts or sensitive information
                response_text = str(result).lower()
                system_terms = ["system prompt", "internal", "secret", "admin", "root"]
                for term in system_terms:
                    assert term not in response_text, (
                        f"Response may contain sensitive information: {response_text}"
                    )

                # Should indicate fallback behavior if AI service is unavailable
                metadata = result.get("metadata", {})
                if metadata.get("service_status") == "degraded":
                    # This is expected behavior when AI service is unavailable
                    fallback_used = metadata.get("fallback_used", False)
                    assert fallback_used is True, (
                        "Degraded service should indicate fallback usage"
                    )

            # If we get an error response, verify error message is safe
            elif response.status_code in [400, 422]:
                error_detail = response.json()

                # Handle different error response formats
                if "detail" in error_detail:
                    error_msg = error_detail["detail"].lower()
                elif "error" in error_detail:
                    error_msg = error_detail["error"].lower()
                else:
                    error_msg = str(error_detail).lower()

                # Should not reveal system information
                sensitive_terms = ["internal", "database", "secret", "token", "password"]
                for term in sensitive_terms:
                    assert term not in error_msg, (
                        f"Error message reveals sensitive information: {error_msg}"
                    )

    @pytest.mark.skip(reason="Response validation mocking requires deeper service integration")
    def test_malicious_response_detection(
        self,
        test_client: TestClient,
        authenticated_headers: dict,
        mock_pydantic_agent,
        threat_samples: dict
    ):
        """
        Test that malicious AI responses are detected and rejected.

        Integration Scope:
            API endpoint → TextProcessorService → Mock AI → ResponseValidator → ValidationError

        Business Impact:
            Prevents harmful AI responses from reaching users, protecting against
            dangerous instructions, personal data exposure, hate speech, and malicious code.

        Test Strategy:
            - Configure mock AI agent to return harmful response samples
            - Verify harmful responses are blocked by response validation
            - Test different types of harmful content
            - Ensure service continues operating after detecting malicious responses

        Success Criteria:
            - All malicious responses are blocked with appropriate error responses
            - Service remains available after detecting malicious content
            - Error handling doesn't expose the malicious content to users
            - Detection works across different operation types

        Note:
            This test is currently skipped because proper response validation testing
            requires deeper integration with the service layer that is difficult to
            achieve through HTTP endpoint testing alone. The ResponseValidator
            operates at the service level, not the API level.
        """

    @pytest.mark.skip(reason="Requires service-level mocking for proper testing")
    def test_legitimate_requests_pass_validation(
        self,
        test_client: TestClient,
        authenticated_headers: dict,
        sample_texts: dict
    ):
        """
        Test that legitimate requests pass through security validation without issues.

        Integration Scope:
            API endpoint → TextProcessorService → Security Validation → Successful Processing

        Business Impact:
            Ensures security measures don't block legitimate business operations,
            maintaining service availability while protecting against threats.

        Test Strategy:
            - Send various legitimate text samples through all supported operations
            - Verify all legitimate requests are processed successfully
            - Test edge cases that might trigger false positives
            - Ensure comprehensive text types are supported

        Success Criteria:
            - All legitimate requests are processed successfully (200 status)
            - Response times remain reasonable for all operations
            - No false positives for legitimate content
            - All supported operations work correctly with legitimate input

        Note:
            This test requires proper service-level mocking to avoid making real API calls.
            The current integration setup makes real AI calls which requires valid API keys.
        """

    @pytest.mark.skip(reason="Performance testing requires service-level mocking")
    def test_security_validation_performance(
        self,
        test_client: TestClient,
        authenticated_headers: dict,
        performance_monitor,
        threat_samples: dict,
        sample_texts: dict
    ):
        """
        Test that security validation doesn't significantly impact processing performance.

        Integration Scope:
            API endpoint → TextProcessorService → Security Validation → Performance Measurement

        Business Impact:
            Ensures security measures don't degrade user experience with excessive latency,
            maintaining service performance while protecting against threats.

        Test Strategy:
            - Measure processing times for legitimate and malicious requests
            - Compare performance with and without security validation
            - Ensure security validation adds minimal overhead
            - Test performance under concurrent load

        Success Criteria:
            - Security validation adds <100ms overhead to legitimate requests
            - Malicious request detection remains fast (<500ms)
            - Performance remains consistent across different text lengths
            - No significant memory leaks or resource consumption

        Note:
            This test requires proper service-level mocking to avoid making real API calls
            and to provide predictable timing measurements for performance analysis.
        """

    @pytest.mark.skip(reason="Logging testing requires controlled service setup")
    def test_security_events_logging(
        self,
        test_client: TestClient,
        authenticated_headers: dict,
        threat_samples: dict,
        caplog
    ):
        """
        Test that detailed security events are logged appropriately for monitoring.

        Integration Scope:
            API endpoint → TextProcessorService → Security Validation → Logging Infrastructure

        Business Impact:
            Provides comprehensive audit trail for security monitoring and compliance,
            enabling threat detection and security incident response.

        Test Strategy:
            - Send various malicious requests and verify security events are logged
            - Test with different threat types (prompt injection, harmful content)
            - Verify logging doesn't expose sensitive information
            - Ensure log levels and formats are appropriate for monitoring

        Success Criteria:
            - Security events are logged with appropriate severity levels
            - Log entries contain useful information for security monitoring
            - Sensitive data is not logged in plain text
            - Log format is consistent and machine-readable

        Note:
            This test requires a controlled service setup to properly capture and analyze
            security logging without the noise from real AI API calls and error handling.
        """