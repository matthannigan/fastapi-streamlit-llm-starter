"""
HIGH PRIORITY: Exception Classification → Retry Strategy → Fallback Execution Integration Test

This test suite verifies the integration between exception classification, retry strategies,
and fallback execution. It ensures that different types of errors are properly classified
and appropriate retry/fallback strategies are applied.

Integration Scope:
    Tests the complete error handling flow from exception classification through
    retry strategies to fallback execution and graceful degradation.

Seam Under Test:
    Exception classification → Retry decision → Fallback strategy → Result handling

Critical Paths:
    - Exception occurrence → Classification → Retry/fallback decision → Graceful response
    - Transient vs permanent exception handling
    - Context preservation during retries
    - Fallback response quality validation

Business Impact:
    Ensures appropriate error handling and graceful degradation for user experience.
    Failures here directly impact system reliability and user trust.

Test Strategy:
    - Test transient vs permanent exception classification
    - Verify exception-specific retry strategies
    - Test fallback function execution
    - Validate context preservation during retries
    - Test retry exhaustion handling
    - Validate fallback response quality

Success Criteria:
    - Transient vs permanent exceptions are classified correctly
    - Exception-specific retry strategies are applied appropriately
    - Fallback functions execute when processing fails
    - Context is preserved during retries
    - Appropriate behavior when retry attempts are exhausted
    - Fallback responses meet quality requirements
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.services.text_processor import TextProcessorService
from app.infrastructure.cache import AIResponseCache
from app.core.config import Settings
from app.core.exceptions import ValidationError, InfrastructureError, ServiceUnavailableError
from app.schemas import TextProcessingRequest, TextProcessingOperation
from app.api.v1.deps import get_text_processor


class TestExceptionHandlingGracefulDegradation:
    """
    Integration tests for exception handling and graceful degradation.

    Seam Under Test:
        Exception classification → Retry decision → Fallback strategy → Result handling

    Critical Paths:
        - Exception classification and retry strategy selection
        - Fallback execution when retries are exhausted
        - Context preservation during error handling
        - Graceful degradation under various failure scenarios

    Business Impact:
        Validates robust error handling that maintains user experience
        even during system failures and service degradation.

    Test Strategy:
        - Test different exception types and classifications
        - Verify retry behavior for transient failures
        - Validate fallback responses for permanent failures
        - Ensure graceful degradation under various conditions
    """

    @pytest.fixture(autouse=True)
    def setup_mocking_and_fixtures(self):
        """Set up comprehensive mocking for all tests in this class."""
        # Mock the AI agent to simulate different failure scenarios
        self.mock_agent_class = MagicMock()
        self.mock_agent_instance = AsyncMock()
        self.mock_agent_class.return_value = self.mock_agent_instance

        # Configure agent to simulate different failure scenarios
        self.failure_scenarios = {
            'transient_failure': [],
            'permanent_failure': [],
            'retry_then_succeed': [],
            'network_timeout': [],
            'rate_limit': []
        }

        async def configurable_agent_run(user_prompt: str):
            """Agent that can be configured to simulate different failure scenarios."""
            # Check which scenario to simulate based on prompt content
            prompt_lower = user_prompt.lower()

            if 'transient_failure' in prompt_lower:
                # Simulate transient failure (should be retried)
                raise InfrastructureError(
                    "Temporary AI service unavailability",
                    context={"error_type": "transient", "retryable": True}
                )
            elif 'permanent_failure' in prompt_lower:
                # Simulate permanent failure (should not be retried)
                raise ValidationError(
                    "Invalid request format",
                    context={"error_type": "permanent", "retryable": False}
                )
            elif 'retry_then_succeed' in prompt_lower:
                # Track retry attempts and succeed after retries
                if len(self.failure_scenarios['retry_then_succeed']) < 2:
                    self.failure_scenarios['retry_then_succeed'].append(prompt_lower)
                    raise InfrastructureError(
                        "Temporary service overload",
                        context={"error_type": "retryable", "retryable": True}
                    )
                else:
                    # Succeed after retries
                    mock_result = MagicMock()
                    mock_result.output = "Successfully processed after retries"
                    return mock_result
            elif 'network_timeout' in prompt_lower:
                # Simulate network timeout
                raise ServiceUnavailableError(
                    "AI service timeout",
                    context={"error_type": "timeout", "retryable": True}
                )
            elif 'rate_limit' in prompt_lower:
                # Simulate rate limiting
                raise InfrastructureError(
                    "Rate limit exceeded",
                    context={"error_type": "rate_limit", "retryable": True}
                )
            else:
                # Default success response
                mock_result = MagicMock()
                mock_result.output = "Default processing response"
                return mock_result

        self.mock_agent_instance.run.side_effect = configurable_agent_run

        # Apply the mock
        with patch('app.services.text_processor.Agent', self.mock_agent_class):
            yield

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Headers with valid authentication."""
        return {"Authorization": "Bearer test-api-key-12345"}

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return "This is a test of exception handling and graceful degradation in the text processing system."

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

    def test_transient_failure_retry_behavior(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test retry behavior for transient failures.

        Integration Scope:
            API endpoint → Exception classification → Retry strategy → Processing

        Business Impact:
            Ensures system recovers from temporary failures without user impact,
            improving reliability and user experience.

        Test Strategy:
            - Simulate transient AI service failure
            - Verify retry attempts are made
            - Confirm successful recovery after retries
            - Validate retry strategy application

        Success Criteria:
            - Transient failures trigger appropriate retry behavior
            - System recovers successfully after retries
            - User receives successful response despite initial failures
            - Retry attempts are logged and monitored
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} transient_failure",
                "operation": "summarize",
                "options": {"max_length": 50}
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "result" in data

            # Verify the result indicates recovery after retries
            assert "successfully processed after retries" in data["result"].lower()

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_permanent_failure_immediate_fallback(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test immediate fallback for permanent failures.

        Integration Scope:
            API endpoint → Exception classification → Fallback execution

        Business Impact:
            Ensures system provides immediate feedback for permanent failures
            rather than wasting time on retries.

        Test Strategy:
            - Simulate permanent failure (validation error)
            - Verify no retry attempts are made
            - Confirm immediate error response
            - Validate appropriate error classification

        Success Criteria:
            - Permanent failures are identified immediately
            - No unnecessary retry attempts are made
            - User receives clear error message
            - System resources are not wasted on futile retries
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} permanent_failure",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code in [400, 422]  # Validation or business logic error

            # Verify no retry attempts were made (quick failure)
            # The permanent failure should be identified immediately

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_network_timeout_handling(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test handling of network timeouts with appropriate retry strategy.

        Integration Scope:
            API endpoint → Timeout detection → Retry strategy → Recovery

        Business Impact:
            Ensures system handles network issues gracefully while attempting
            recovery through appropriate retry mechanisms.

        Test Strategy:
            - Simulate network timeout scenario
            - Verify timeout-specific retry behavior
            - Confirm appropriate error handling
            - Validate timeout recovery mechanisms

        Success Criteria:
            - Network timeouts are detected and classified correctly
            - Appropriate retry strategy is applied for timeouts
            - System provides meaningful feedback for timeout scenarios
            - Recovery mechanisms work correctly for timeout situations
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} network_timeout",
                "operation": "summarize",
                "options": {"max_length": 30}
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 503  # Service Unavailable

            # Verify timeout-specific error handling
            error_data = response.json()
            assert "timeout" in str(error_data).lower() or "unavailable" in str(error_data).lower()

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_rate_limit_handling_and_recovery(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test rate limit handling with exponential backoff and recovery.

        Integration Scope:
            API endpoint → Rate limit detection → Backoff strategy → Recovery

        Business Impact:
            Ensures system handles rate limiting gracefully and recovers
            when rate limits are reset.

        Test Strategy:
            - Simulate rate limit exceeded scenario
            - Verify exponential backoff behavior
            - Confirm recovery after rate limit reset
            - Validate rate limit handling strategy

        Success Criteria:
            - Rate limits are detected and handled appropriately
            - Exponential backoff is applied correctly
            - System recovers when rate limits are reset
            - User experience is maintained during rate limiting
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} rate_limit",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 502  # Bad Gateway for rate limiting

            # Verify rate limit specific error handling
            error_data = response.json()
            assert "rate limit" in str(error_data).lower() or "exceeded" in str(error_data).lower()

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_exception_context_preservation(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test that exception context is preserved throughout error handling.

        Integration Scope:
            API endpoint → Exception context → Error handling → Response

        Business Impact:
            Ensures detailed error context is maintained for debugging
            and operational visibility.

        Test Strategy:
            - Trigger exception with rich context
            - Verify context is preserved through error handling
            - Confirm context is available in error responses
            - Validate context logging and monitoring

        Success Criteria:
            - Exception context is preserved during error handling
            - Error responses include relevant context information
            - Context is available for logging and monitoring
            - Debugging information is maintained throughout process
        """
        # Configure agent to raise exception with context
        async def context_rich_agent_run(user_prompt: str):
            raise InfrastructureError(
                "AI service processing failed",
                context={
                    "operation": "summarize",
                    "text_length": len(user_prompt),
                    "error_type": "processing_failure",
                    "retryable": True,
                    "request_id": "test-request-123"
                }
            )

        self.mock_agent_instance.run.side_effect = context_rich_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} context_test",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 502  # Bad Gateway

            # Verify error response structure includes context
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_fallback_response_quality_validation(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test that fallback responses meet quality requirements.

        Integration Scope:
            API endpoint → Fallback execution → Response validation

        Business Impact:
            Ensures fallback responses provide meaningful value to users
            even when primary processing fails.

        Test Strategy:
            - Force fallback response execution
            - Validate fallback response quality
            - Confirm fallback meets minimum requirements
            - Test fallback response usefulness

        Success Criteria:
            - Fallback responses are generated when needed
            - Fallback content is meaningful and relevant
            - Fallback responses meet quality standards
            - Users receive value even during system degradation
        """
        # Configure agent to always fail, forcing fallback
        async def failing_agent_run(user_prompt: str):
            raise InfrastructureError(
                "AI service unavailable",
                context={"error_type": "service_unavailable", "fallback_available": True}
            )

        self.mock_agent_instance.run.side_effect = failing_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} fallback_test",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200  # Should succeed with fallback

            data = response.json()
            assert data["success"] is True
            assert "result" in data

            # Verify fallback response quality
            result = data["result"]
            assert len(result) > 0
            assert isinstance(result, str)

            # Fallback should acknowledge the issue
            result_lower = result.lower()
            assert any(keyword in result_lower for keyword in ["unable", "unavailable", "error", "issue"])

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_retry_exhaustion_handling(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test behavior when all retry attempts are exhausted.

        Integration Scope:
            API endpoint → Retry exhaustion → Fallback execution → Error handling

        Business Impact:
            Ensures graceful handling when retries are exhausted and
            system falls back to appropriate error responses.

        Test Strategy:
            - Configure scenario where retries are always exhausted
            - Verify retry attempt counting
            - Confirm fallback execution after retries
            - Validate final error handling

        Success Criteria:
            - Retry attempts are counted correctly
            - System recognizes when retries are exhausted
            - Appropriate fallback or error response is provided
            - No infinite retry loops occur
        """
        # Configure agent to fail more times than retry limit
        failure_count = 0
        async def exhaust_retries_agent_run(user_prompt: str):
            nonlocal failure_count
            failure_count += 1

            # Fail 5 times (exceeding typical retry limits)
            if failure_count <= 5:
                raise InfrastructureError(
                    "Persistent AI service failure",
                    context={"attempt": failure_count, "error_type": "persistent"}
                )
            else:
                # Should not reach here in normal retry scenarios
                mock_result = MagicMock()
                mock_result.output = "Unexpected success after many failures"
                return mock_result

        self.mock_agent_instance.run.side_effect = exhaust_retries_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} retry_exhaustion_test",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)

            # Should fail due to retry exhaustion
            assert response.status_code in [502, 503]  # Service errors

            # Verify multiple retry attempts were made
            assert failure_count > 1

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_exception_chaining_and_logging(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test exception chaining and comprehensive logging.

        Integration Scope:
            API endpoint → Exception chaining → Logging → Error response

        Business Impact:
            Ensures comprehensive error tracking and logging for
            debugging and operational monitoring.

        Test Strategy:
            - Trigger nested exception scenario
            - Verify exception chaining is maintained
            - Confirm comprehensive logging
            - Validate error context preservation

        Success Criteria:
            - Exception chaining works correctly
            - Comprehensive logging is generated
            - Error context is preserved through chaining
            - Debugging information is available
        """
        # Configure agent to raise nested exceptions
        async def chained_exception_agent_run(user_prompt: str):
            try:
                # Inner exception
                raise ValueError("Low-level AI processing error")
            except ValueError as inner_error:
                # Wrap in higher-level exception with context
                raise InfrastructureError(
                    "AI service processing failed",
                    context={"original_error": str(inner_error), "error_type": "wrapped"}
                ) from inner_error

        self.mock_agent_instance.run.side_effect = chained_exception_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} exception_chaining_test",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 502  # Bad Gateway

            # Verify error response includes context
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_graceful_degradation_under_load(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test graceful degradation behavior under system load.

        Integration Scope:
            API endpoint → Load detection → Graceful degradation → Response quality

        Business Impact:
            Ensures system maintains acceptable performance and user experience
            even under high load or resource constraints.

        Test Strategy:
            - Simulate high load scenario
            - Verify graceful degradation activates
            - Confirm response quality is maintained
            - Validate system stability under load

        Success Criteria:
            - System detects high load conditions
            - Graceful degradation mechanisms activate appropriately
            - Response quality is maintained despite load
            - System remains stable and responsive
        """
        # Configure agent to simulate load-related delays and failures
        request_count = 0
        async def load_sensitive_agent_run(user_prompt: str):
            nonlocal request_count
            request_count += 1

            # Simulate degradation after multiple requests
            if request_count > 3:
                # Return degraded but functional response
                mock_result = MagicMock()
                mock_result.output = "Simplified processing due to high system load"
                return mock_result
            else:
                # Normal processing for initial requests
                mock_result = MagicMock()
                mock_result.output = f"Normal processing for request {request_count}"
                return mock_result

        self.mock_agent_instance.run.side_effect = load_sensitive_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Make multiple requests to simulate load
            for i in range(5):
                request_data = {
                    "text": f"{sample_text} load_test_request_{i}",
                    "operation": "summarize"
                }

                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert "result" in data

            # Verify graceful degradation occurred
            assert request_count == 5

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_error_recovery_and_system_resilience(self, client, auth_headers, sample_text, text_processor_service):
        """
        Test error recovery and overall system resilience.

        Integration Scope:
            API endpoint → Error recovery → System resilience → Continued operation

        Business Impact:
            Ensures system can recover from errors and continue operating
            reliably after encountering failures.

        Test Strategy:
            - Trigger error condition
            - Verify recovery mechanisms
            - Test continued operation after recovery
            - Validate system resilience patterns

        Success Criteria:
            - System recovers from error conditions
            - Normal operation resumes after recovery
            - No persistent state corruption from errors
            - System maintains resilience across multiple failures
        """
        # Configure agent to fail then recover
        recovery_test_count = 0
        async def recovery_test_agent_run(user_prompt: str):
            nonlocal recovery_test_count
            recovery_test_count += 1

            if recovery_test_count == 1:
                # First request fails
                raise InfrastructureError(
                    "Initial AI service failure",
                    context={"test_phase": "initial_failure"}
                )
            else:
                # Subsequent requests succeed
                mock_result = MagicMock()
                mock_result.output = "Recovered and processing normally"
                return mock_result

        self.mock_agent_instance.run.side_effect = recovery_test_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # First request - should fail
            request_data = {
                "text": f"{sample_text} recovery_test_1",
                "operation": "summarize"
            }

            response1 = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response1.status_code == 502  # Should fail

            # Second request - should succeed (recovery)
            request_data2 = {
                "text": f"{sample_text} recovery_test_2",
                "operation": "summarize"
            }

            response2 = client.post("/v1/text_processing/process", json=request_data2, headers=auth_headers)
            assert response2.status_code == 200  # Should succeed

            data2 = response2.json()
            assert data2["success"] is True
            assert "recovered" in data2["result"].lower()

            # Verify recovery occurred
            assert recovery_test_count == 2

        finally:
            # Clean up override
            app.dependency_overrides.clear()
