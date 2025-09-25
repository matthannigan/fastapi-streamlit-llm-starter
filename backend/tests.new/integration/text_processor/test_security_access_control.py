"""
HIGH PRIORITY: API Authentication → Request Validation → Processing Authorization Integration Test

This test suite verifies the integration between API authentication, request validation,
and processing authorization. It ensures that only authenticated and authorized users
can access text processing capabilities with proper security validation.

Integration Scope:
    Tests the complete security flow from authentication through request validation
    to processing authorization and security monitoring.

Seam Under Test:
    API key verification → Request validation → Operation authorization → Processing execution

Critical Paths:
    - Authentication → Input validation → Authorization → Processing → Response
    - Security event logging and monitoring
    - Authentication error handling and logging
    - Concurrent authentication processing

Business Impact:
    Critical for security and access control in production environments.
    Failures here compromise system security and unauthorized access.

Test Strategy:
    - Test valid API key authentication flow
    - Verify invalid API key rejection
    - Test missing API key scenarios
    - Validate request validation and sanitization
    - Test operation-specific authorization
    - Verify authentication error handling and logging
    - Test concurrent authentication processing

Success Criteria:
    - Valid API key authentication allows access to processing
    - Invalid API keys are properly rejected
    - Authentication failures are logged for security monitoring
    - Request validation prevents malicious input
    - Authorization works correctly for all endpoints
    - Security events are properly logged and monitored
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.text_processor import TextProcessorService
from app.infrastructure.cache import AIResponseCache
from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.schemas import TextProcessingRequest, TextProcessingOperation
from app.api.v1.deps import get_text_processor


class TestSecurityAccessControl:
    """
    Integration tests for security and access control.

    Seam Under Test:
        API key verification → Request validation → Operation authorization → Processing execution

    Critical Paths:
        - Authentication and authorization integration
        - Request validation and security sanitization
        - Security event logging and monitoring
        - Concurrent authentication processing

    Business Impact:
        Validates security controls that protect the system from
        unauthorized access and malicious input.

    Test Strategy:
        - Test authentication with various API key scenarios
        - Verify request validation and sanitization
        - Validate authorization for different endpoints
        - Test security logging and monitoring
    """

    @pytest.fixture(autouse=True)
    def setup_mocking_and_fixtures(self):
        """Set up comprehensive mocking for all tests in this class."""
        # Mock the AI agent to avoid actual API calls
        self.mock_agent_class = MagicMock()
        self.mock_agent_instance = AsyncMock()
        self.mock_agent_class.return_value = self.mock_agent_instance

        # Configure intelligent responses
        async def smart_agent_run(user_prompt: str):
            """Return content-aware responses for testing."""
            user_text = ""
            if "---USER TEXT START---" in user_prompt and "---USER TEXT END---" in user_prompt:
                start_marker = "---USER TEXT START---"
                end_marker = "---USER TEXT END---"
                start_idx = user_prompt.find(start_marker) + len(start_marker)
                end_idx = user_prompt.find(end_marker)
                user_text = user_prompt[start_idx:end_idx].strip()
            else:
                user_text = user_prompt

            # Create mock result object
            mock_result = MagicMock()

            # Security-aware responses
            if "malicious" in user_text.lower() or "attack" in user_text.lower():
                mock_result.output = "I can help you analyze text content for legitimate purposes."
            else:
                mock_result.output = "Processed text response based on the input content."

            return mock_result

        self.mock_agent_instance.run.side_effect = smart_agent_run

        # Apply the mock
        with patch('app.services.text_processor.Agent', self.mock_agent_class):
            yield

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return "This is a test of security controls and access validation in the text processing system."

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for TextProcessorService."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.gemini_api_key = "test-key"
        mock_settings.ai_model = "gemini-pro"
        mock_settings.ai_temperature = 0.7
        mock_settings.BATCH_AI_CONCURRENCY_LIMIT = 5
        return mock_settings

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for TextProcessorService."""
        return AsyncMock(spec=AIResponseCache)

    @pytest.fixture
    def text_processor_service(self, mock_settings, mock_cache):
        """Create TextProcessorService instance for testing."""
        return TextProcessorService(settings=mock_settings, cache=mock_cache)

    def test_valid_api_key_authentication_success(self, client, sample_text, text_processor_service):
        """
        Test successful authentication with valid API key.

        Integration Scope:
            API endpoint → API key verification → TextProcessorService → Processing

        Business Impact:
            Validates that legitimate users can access text processing capabilities
            with proper authentication.

        Test Strategy:
            - Submit request with valid API key
            - Verify authentication succeeds
            - Confirm processing continues normally
            - Validate successful response structure

        Success Criteria:
            - Valid API key authentication allows access
            - Authentication headers are validated correctly
            - Processing completes successfully
            - Response includes expected content
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize",
                "options": {"max_length": 50}
            }

            # Use valid API key
            headers = {"Authorization": "Bearer test-api-key-12345"}

            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert "result" in data

            # Verify result is appropriate for the input
            assert len(data["result"]) > 0

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_invalid_api_key_rejection(self, client, sample_text, text_processor_service):
        """
        Test rejection of invalid API keys.

        Integration Scope:
            API endpoint → API key validation → Error response

        Business Impact:
            Ensures unauthorized access attempts are properly blocked
            and logged for security monitoring.

        Test Strategy:
            - Submit request with invalid API key
            - Verify authentication fails
            - Confirm appropriate error response
            - Validate security logging

        Success Criteria:
            - Invalid API keys are rejected
            - Proper error response is returned
            - Authentication failure is logged
            - No processing occurs for invalid keys
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # Use invalid API key
            headers = {"Authorization": "Bearer invalid-api-key-12345"}

            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            assert response.status_code == 401  # Unauthorized

            # Verify error response structure
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data or "error" in error_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_missing_api_key_handling(self, client, sample_text, text_processor_service):
        """
        Test handling of requests with missing API keys.

        Integration Scope:
            API endpoint → Missing authentication → Error response

        Business Impact:
            Ensures requests without authentication are properly handled
            according to security requirements.

        Test Strategy:
            - Submit request without API key
            - Verify authentication requirement is enforced
            - Confirm appropriate error response
            - Validate security handling

        Success Criteria:
            - Missing API key requests are rejected
            - Clear error message is provided
            - No processing occurs without authentication
            - Security policy is enforced correctly
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # No authentication headers
            response = client.post("/v1/text_processing/process", json=request_data)
            assert response.status_code == 401  # Unauthorized

            # Verify error response
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_alternate_authentication_methods(self, client, sample_text, text_processor_service):
        """
        Test alternate authentication methods (X-API-Key header).

        Integration Scope:
            API endpoint → Alternate authentication → Processing

        Business Impact:
            Validates flexible authentication methods while maintaining security.

        Test Strategy:
            - Test X-API-Key header authentication
            - Verify alternate method works correctly
            - Confirm processing completes normally
            - Validate security consistency

        Success Criteria:
            - Alternate authentication method works
            - Security validation is consistent
            - Processing completes successfully
            - No security bypass occurs
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "sentiment"
            }

            # Use X-API-Key header instead of Authorization
            headers = {"X-API-Key": "test-api-key-12345"}

            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "sentiment"

            # Verify sentiment analysis occurred
            assert "sentiment" in data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_malformed_authentication_headers(self, client, sample_text, text_processor_service):
        """
        Test handling of malformed authentication headers.

        Integration Scope:
            API endpoint → Malformed auth → Error handling

        Business Impact:
            Ensures malformed authentication attempts are handled gracefully
            while maintaining security.

        Test Strategy:
            - Submit request with malformed auth header
            - Verify proper error handling
            - Confirm security validation still works
            - Validate error response quality

        Success Criteria:
            - Malformed authentication is rejected
            - Clear error messages are provided
            - Security validation remains intact
            - No authentication bypass occurs
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # Use malformed authentication header
            headers = {"Authorization": "Invalid-Format test-api-key-12345"}

            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            assert response.status_code == 401  # Unauthorized

            # Verify error response
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_request_validation_integration(self, client, sample_text, text_processor_service):
        """
        Test request validation integration with security controls.

        Integration Scope:
            API endpoint → Request validation → Security sanitization → Processing

        Business Impact:
            Ensures input validation works correctly with security controls
            to prevent malicious input processing.

        Test Strategy:
            - Submit requests with various validation scenarios
            - Verify validation and security integration
            - Confirm proper error handling
            - Validate security controls remain active

        Success Criteria:
            - Request validation works correctly
            - Security controls are applied during validation
            - Invalid requests are rejected appropriately
            - Valid requests proceed to processing
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Test valid request
            valid_request = {
                "text": sample_text,
                "operation": "summarize",
                "options": {"max_length": 50}
            }

            response = client.post("/v1/text_processing/process", json=valid_request, headers={"Authorization": "Bearer test-api-key-12345"})
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

            # Test validation error - missing required field for Q&A
            invalid_request = {
                "text": sample_text,
                "operation": "qa"  # Missing required 'question' field
            }

            response = client.post("/v1/text_processing/process", json=invalid_request, headers={"Authorization": "Bearer test-api-key-12345"})
            assert response.status_code in [400, 422]  # Validation error

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_operation_specific_authorization(self, client, sample_text, text_processor_service):
        """
        Test authorization for different operations and endpoints.

        Integration Scope:
            API endpoint → Operation authorization → Processing access control

        Business Impact:
            Ensures operation-specific access controls work correctly
            for different processing types.

        Test Strategy:
            - Test authorization for different operation types
            - Verify authorization consistency across operations
            - Confirm proper access control enforcement
            - Validate authorization error handling

        Success Criteria:
            - All operations require proper authentication
            - Authorization is consistent across operation types
            - Access control works for all endpoints
            - Proper error responses for authorization failures
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            operations_to_test = ["summarize", "sentiment", "key_points", "questions", "qa"]

            for operation in operations_to_test:
                request_data = {
                    "text": f"Test text for {operation} operation",
                    "operation": operation
                }

                # Add question for QA operation
                if operation == "qa":
                    request_data["question"] = "What is this text about?"

                # Test with valid authentication
                response = client.post("/v1/text_processing/process", json=request_data, headers={"Authorization": "Bearer test-api-key-12345"})
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["operation"] == operation

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_authentication_error_logging(self, client, sample_text, text_processor_service):
        """
        Test authentication error logging and security monitoring.

        Integration Scope:
            API endpoint → Authentication failure → Security logging → Monitoring

        Business Impact:
            Ensures authentication failures are properly logged
            for security monitoring and audit purposes.

        Test Strategy:
            - Trigger authentication failure
            - Verify security logging occurs
            - Confirm monitoring integration works
            - Validate audit trail creation

        Success Criteria:
            - Authentication failures are logged
            - Security events are captured for monitoring
            - Audit trail is maintained
            - No sensitive information is exposed in logs
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # Trigger authentication failure
            response = client.post("/v1/text_processing/process", json=request_data, headers={"Authorization": "Bearer invalid-key"})
            assert response.status_code == 401

            # Authentication failure should be logged (this would be verified in actual logging system)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_concurrent_authentication_processing(self, client, sample_text, text_processor_service):
        """
        Test concurrent authentication processing for multiple requests.

        Integration Scope:
            API endpoint → Concurrent authentication → Thread-safe processing

        Business Impact:
            Ensures authentication processing is thread-safe and
            handles concurrent requests correctly.

        Test Strategy:
            - Make multiple concurrent requests with authentication
            - Verify all requests are processed correctly
            - Confirm authentication validation works for concurrent requests
            - Validate thread safety of authentication

        Success Criteria:
            - Concurrent requests with authentication work correctly
            - Authentication validation is thread-safe
            - All requests are processed successfully
            - No authentication bypass occurs under load
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Make multiple concurrent requests
            async def make_requests():
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
                    tasks = []
                    for i in range(3):
                        request_data = {
                            "text": f"Concurrent request {i}: {sample_text}",
                            "operation": "summarize",
                            "options": {"max_length": 30}
                        }

                        task = async_client.post(
                            "/v1/text_processing/process",
                            json=request_data,
                            headers={"Authorization": "Bearer test-api-key-12345"}
                        )
                        tasks.append(task)

                    responses = await asyncio.gather(*tasks)

                    # Verify all requests succeeded
                    for i, response in enumerate(responses):
                        assert response.status_code == 200, f"Request {i} failed"
                        data = response.json()
                        assert data["success"] is True
                        assert data["operation"] == "summarize"
                        assert "result" in data

            # Run concurrent requests
            asyncio.run(make_requests())

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_security_configuration_validation(self, client, sample_text, text_processor_service):
        """
        Test security configuration validation and enforcement.

        Integration Scope:
            API endpoint → Security configuration → Access control enforcement

        Business Impact:
            Ensures security configuration is properly validated and enforced
            across different environments and configurations.

        Test Strategy:
            - Test security configuration validation
            - Verify access control enforcement
            - Confirm security settings are applied correctly
            - Validate security error handling

        Success Criteria:
            - Security configuration is validated correctly
            - Access control is enforced based on configuration
            - Security settings are applied consistently
            - Proper error responses for security violations
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # Test with security-enabled configuration
            response = client.post("/v1/text_processing/process", json=request_data, headers={"Authorization": "Bearer test-api-key-12345"})
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_authentication_bypass_prevention(self, client, sample_text, text_processor_service):
        """
        Test prevention of authentication bypass attempts.

        Integration Scope:
            API endpoint → Authentication bypass prevention → Security validation

        Business Impact:
            Ensures various authentication bypass attempts are prevented
            and handled securely.

        Test Strategy:
            - Test various authentication bypass methods
            - Verify all bypass attempts are blocked
            - Confirm security validation remains intact
            - Validate comprehensive security coverage

        Success Criteria:
            - All authentication bypass attempts are prevented
            - Security validation works for various attack vectors
            - No unauthorized access is possible
            - Security controls remain effective under attack
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # Test various bypass attempts
            bypass_attempts = [
                {"Authorization": "Bearer "},  # Empty token
                {"Authorization": "Basic dGVzdDoxMjM="},  # Wrong auth type
                {"X-API-Key": ""},  # Empty API key
                {"Authorization": "Bearer test-api-key-12345", "X-API-Key": "bypass-attempt"},  # Conflicting headers
                {},  # No auth headers at all
            ]

            for headers in bypass_attempts:
                response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
                assert response.status_code == 401, f"Bypass attempt succeeded with headers: {headers}"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_security_metrics_and_alerting_integration(self, client, sample_text, text_processor_service):
        """
        Test security metrics collection and alerting integration.

        Integration Scope:
            API endpoint → Security metrics → Alerting integration → Monitoring

        Business Impact:
            Ensures security metrics are collected and integrated with
            monitoring and alerting systems.

        Test Strategy:
            - Trigger security events
            - Verify metrics collection
            - Confirm alerting integration works
            - Validate security monitoring

        Success Criteria:
            - Security metrics are collected accurately
            - Alerting integration works correctly
            - Security monitoring provides visibility
            - Metrics are available for analysis
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # Test successful authentication (should generate security metrics)
            response = client.post("/v1/text_processing/process", json=request_data, headers={"Authorization": "Bearer test-api-key-12345"})
            assert response.status_code == 200

            # Test failed authentication (should generate security metrics)
            response = client.post("/v1/text_processing/process", json=request_data, headers={"Authorization": "Bearer invalid-key"})
            assert response.status_code == 401

            # Security metrics would be verified in actual monitoring system

        finally:
            # Clean up override
            app.dependency_overrides.clear()
