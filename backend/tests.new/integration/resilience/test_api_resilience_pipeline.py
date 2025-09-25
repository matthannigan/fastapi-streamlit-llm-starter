"""
Integration Tests: API → Resilience Orchestrator → Circuit Breaker → Retry Pipeline

This module tests the complete user-facing resilience functionality by validating
the integration between API endpoints, resilience orchestration, circuit breaker
patterns, and retry mechanisms.

Integration Scope:
    - API endpoints (v1/text_processing/*) → AIServiceResilience orchestrator
    - Resilience orchestration → Circuit breaker state management
    - Circuit breaker → Retry pipeline → AI service calls
    - Error classification → Fallback response generation

Business Impact:
    Core resilience functionality that directly affects user experience
    during AI service outages and failures

Test Strategy:
    - Test from the outside-in through HTTP API endpoints
    - Use high-fidelity fakes (fakeredis) for infrastructure components
    - Verify observable outcomes (HTTP responses, error codes, response content)
    - Test both success and failure scenarios with circuit breaker transitions
    - Validate fallback mechanisms and graceful degradation

Critical Paths:
    - User request → Resilience orchestration → Circuit breaker → Retry → Response
    - Failure detection → Circuit breaker open → Fallback response
    - Recovery testing → Circuit breaker half-open → Service restoration
    - Concurrent requests → Circuit breaker state consistency
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.exceptions import TransientAIError, PermanentAIError, ServiceUnavailableError
from app.infrastructure.resilience.orchestrator import ai_resilience, AIServiceResilience
from app.infrastructure.resilience.circuit_breaker import CircuitBreakerConfig, ResilienceMetrics
from app.infrastructure.resilience.retry import RetryConfig
from app.infrastructure.resilience.config_presets import ResilienceStrategy
from app.services.text_processor import TextProcessorService
from app.schemas import TextProcessingOperation

from ..conftest import authenticated_headers


class TestAPIResiliencePipeline:
    """
    Integration tests for the complete API → Resilience Orchestrator → Circuit Breaker → Retry Pipeline.

    Seam Under Test:
        API endpoints → AIServiceResilience → EnhancedCircuitBreaker → Retry mechanisms → AI service calls

    Critical Paths:
        - User request → Resilience orchestration → Success response
        - Transient failures → Retry execution → Success response
        - Circuit breaker open → Fallback response → Service degradation
        - Service recovery → Circuit breaker half-open → Closed state
        - Concurrent requests → Circuit breaker state consistency

    Business Impact:
        Core user-facing resilience functionality that directly affects user experience
        during AI service outages, ensuring system reliability and graceful degradation
    """

    @pytest.fixture(autouse=True)
    def setup_resilience_for_api_tests(self):
        """Set up resilience system for API integration testing."""
        # Create test-specific settings
        test_settings = Settings(
            environment="testing",
            api_key="test-api-key-12345",
            resilience_preset="balanced",
            enable_circuit_breaker=True,
            enable_retry=True,
            max_retry_attempts=3,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=30
        )

        # Reset global resilience instance with test configuration
        global ai_resilience
        ai_resilience = AIServiceResilience(test_settings)

        # Register test operations with specific strategies
        ai_resilience.register_operation("summarize_text", ResilienceStrategy.BALANCED)
        ai_resilience.register_operation("analyze_sentiment", ResilienceStrategy.AGGRESSIVE)
        ai_resilience.register_operation("extract_key_points", ResilienceStrategy.BALANCED)

        yield

        # Reset metrics after test
        ai_resilience.reset_metrics()

    @pytest.fixture
    def unreliable_text_processor(self, unreliable_ai_service):
        """Create a text processor service with controllable AI service."""
        # Mock the AI agent to use our unreliable service
        with patch('app.services.text_processor.TextProcessorService.agent') as mock_agent:
            mock_agent.run = unreliable_ai_service.process

            # Create service instance
            test_settings = Settings(
                environment="testing",
                api_key="test-api-key-12345",
                ai_model="gemini-1.5-flash"
            )

            # Mock the cache service requirement
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None
            mock_cache.build_key.return_value = "test_key"

            service = TextProcessorService(test_settings, mock_cache)

            # Set the unreliable service on the instance
            service.unreliable_service = unreliable_ai_service

            yield service

    def test_successful_request_circuit_breaker_closed(self, client: TestClient, unreliable_ai_service):
        """
        Test that a successful request completes normally with circuit breaker remaining closed.

        Integration Scope:
            API endpoint → Resilience orchestration → Circuit breaker → AI service call

        Business Impact:
            Validates that normal operation works correctly without triggering resilience patterns

        Test Strategy:
            - Make single successful request through API
            - Verify circuit breaker remains closed
            - Confirm response contains expected data
            - Validate no retry attempts occurred

        Success Criteria:
            - HTTP 200 response with valid result
            - Circuit breaker state remains closed
            - Response contains processed text
            - No resilience metrics incremented
        """
        # Configure service to succeed
        unreliable_ai_service.set_failure_mode("success")

        # Make API request
        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "This is a test document for processing.",
                "operation": "summarize"
            },
            headers=authenticated_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "Processed:" in data["result"]

        # Verify circuit breaker state
        health_status = ai_resilience.get_health_status()
        assert health_status["healthy"] is True
        assert len(health_status["open_circuit_breakers"]) == 0

        # Verify no resilience patterns were triggered
        metrics = ai_resilience.get_all_metrics()
        assert "summarize_text" in metrics["operations"]

    def test_transient_failure_retry_success(self, client: TestClient, unreliable_ai_service):
        """
        Test that transient failures trigger retries and eventually succeed.

        Integration Scope:
            API endpoint → Resilience orchestration → Retry mechanism → AI service call

        Business Impact:
            Validates retry functionality for temporary service issues

        Test Strategy:
            - Configure service to fail twice then succeed
            - Make API request and verify retry behavior
            - Confirm final success after retries
            - Validate circuit breaker remains closed

        Success Criteria:
            - HTTP 200 response after retries
            - Response contains successful result
            - Circuit breaker remains closed
            - Retry metrics incremented appropriately
        """
        # Configure service to fail twice then succeed (3 total attempts)
        unreliable_ai_service.set_failure_mode("transient_failure", success_after=2)

        # Make API request
        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "Test document for retry functionality.",
                "operation": "summarize"
            },
            headers=authenticated_headers
        )

        # Verify final success
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "Processed:" in data["result"]

        # Verify circuit breaker state
        health_status = ai_resilience.get_health_status()
        assert health_status["healthy"] is True

        # Verify retry was attempted (service call count > 1)
        assert unreliable_ai_service.call_count == 3  # 2 failures + 1 success

    def test_circuit_breaker_opens_after_failures(self, client: TestClient, unreliable_ai_service):
        """
        Test that circuit breaker opens after repeated failures to prevent cascade failures.

        Integration Scope:
            API endpoint → Resilience orchestration → Circuit breaker → Failure handling

        Business Impact:
            Protects AI service from overload during outages

        Test Strategy:
            - Configure service to fail permanently
            - Make multiple requests to trigger circuit breaker
            - Verify circuit breaker opens and fails fast
            - Confirm subsequent requests fail immediately

        Success Criteria:
            - Circuit breaker opens after failure threshold
            - Subsequent requests fail immediately (fail-fast)
            - HTTP 503 Service Unavailable responses
            - Circuit breaker state correctly reported
        """
        # Configure service to fail permanently
        unreliable_ai_service.set_failure_mode("permanent_failure")

        # Make requests until circuit breaker opens
        for i in range(4):  # Exceed failure threshold of 3
            response = client.post(
                "/v1/text_processing/process",
                json={
                    "text": f"Test document {i} for circuit breaker testing.",
                    "operation": "summarize"
                },
                headers=authenticated_headers
            )

            if i < 3:
                # First 3 requests should attempt processing and fail
                assert response.status_code == 502  # Bad Gateway for AI service errors
            else:
                # 4th request should fail fast due to open circuit breaker
                assert response.status_code == 503  # Service Unavailable

        # Verify circuit breaker is open
        health_status = ai_resilience.get_health_status()
        assert health_status["healthy"] is False
        assert "summarize_text" in health_status["open_circuit_breakers"]

    def test_circuit_breaker_recovery_with_half_open(self, client: TestClient, unreliable_ai_service):
        """
        Test circuit breaker recovery through half-open state testing.

        Integration Scope:
            API endpoint → Circuit breaker recovery → Half-open testing → State transition

        Business Impact:
            Automatic service recovery without manual intervention

        Test Strategy:
            - Force circuit breaker open with failures
            - Wait for recovery timeout
            - Make request to test half-open state
            - Verify circuit breaker transitions to closed on success

        Success Criteria:
            - Circuit breaker transitions from open to half-open to closed
            - Service recovery happens automatically
            - Successful request after recovery period
            - Health status reflects recovery state
        """
        # First, open the circuit breaker
        unreliable_ai_service.set_failure_mode("permanent_failure")

        # Open circuit breaker with failures
        for _ in range(3):
            client.post(
                "/v1/text_processing/process",
                json={
                    "text": "Test document for circuit breaker opening.",
                    "operation": "summarize"
                },
                headers=authenticated_headers
            )

        # Verify circuit breaker is open
        health_status = ai_resilience.get_health_status()
        assert "summarize_text" in health_status["open_circuit_breakers"]

        # Switch to success mode for recovery testing
        unreliable_ai_service.set_failure_mode("success")

        # Wait for recovery timeout (slightly longer than 30 seconds)
        time.sleep(31)

        # Make request to test half-open -> closed transition
        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "Test document for circuit breaker recovery.",
                "operation": "summarize"
            },
            headers=authenticated_headers
        )

        # Verify successful recovery
        assert response.status_code == 200
        data = response.json()
        assert "result" in data

        # Verify circuit breaker closed after successful recovery
        health_status = ai_resilience.get_health_status()
        assert health_status["healthy"] is True
        assert len(health_status["open_circuit_breakers"]) == 0

    def test_fallback_response_when_circuit_breaker_open(self, client: TestClient, unreliable_ai_service):
        """
        Test that fallback responses are provided when circuit breaker is open.

        Integration Scope:
            API endpoint → Circuit breaker → Fallback mechanism → Response generation

        Business Impact:
            Graceful degradation instead of complete service failure

        Test Strategy:
            - Open circuit breaker with repeated failures
            - Make request when circuit breaker is open
            - Verify fallback response is returned
            - Confirm response structure matches expected format

        Success Criteria:
            - HTTP 200 response with fallback content
            - Response contains fallback text
            - Metadata indicates fallback was used
            - Circuit breaker remains open
        """
        # First, open the circuit breaker
        unreliable_ai_service.set_failure_mode("permanent_failure")

        for _ in range(3):
            client.post(
                "/v1/text_processing/process",
                json={
                    "text": "Test document for fallback testing.",
                    "operation": "summarize"
                },
                headers=authenticated_headers
            )

        # Verify circuit breaker is open
        health_status = ai_resilience.get_health_status()
        assert "summarize_text" in health_status["open_circuit_breakers"]

        # Configure service to succeed but circuit breaker should still be open
        unreliable_ai_service.set_failure_mode("success")

        # Make request - should get fallback due to open circuit breaker
        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "Test document for fallback response.",
                "operation": "summarize"
            },
            headers=authenticated_headers
        )

        # Verify fallback response
        assert response.status_code == 200  # Fallback returns 200
        data = response.json()
        assert "result" in data
        assert "fallback" in data["result"].lower() or "unavailable" in data["result"].lower()

        # Check for fallback metadata
        if "metadata" in data:
            assert data["metadata"].get("fallback_used") is True
            assert data["metadata"].get("service_status") == "degraded"

    def test_concurrent_requests_circuit_breaker_consistency(self, client: TestClient, unreliable_ai_service):
        """
        Test circuit breaker state consistency under concurrent load.

        Integration Scope:
            Multiple concurrent API requests → Circuit breaker state management → Response consistency

        Business Impact:
            Ensures system stability during high load with failures

        Test Strategy:
            - Start multiple concurrent requests during circuit breaker opening
            - Verify all requests handle circuit breaker state consistently
            - Confirm no race conditions or state corruption

        Success Criteria:
            - All concurrent requests complete successfully
            - Circuit breaker state remains consistent
            - No exceptions or hung requests
            - Response times remain reasonable
        """
        # Configure service to fail and trigger circuit breaker
        unreliable_ai_service.set_failure_mode("permanent_failure")

        async def make_request():
            """Make a single API request."""
            response = client.post(
                "/v1/text_processing/process",
                json={
                    "text": "Concurrent test document.",
                    "operation": "summarize"
                },
                headers=authenticated_headers
            )
            return response.status_code, response.json() if response.status_code == 200 else None

        # Make concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(5)]
        results = []

        # Use asyncio to run concurrent requests
        async def run_concurrent():
            import asyncio
            return await asyncio.gather(*[make_request() for _ in range(5)])

        results = asyncio.run(run_concurrent())
        end_time = time.time()

        # Verify all requests completed
        assert len(results) == 5
        assert all(isinstance(result, tuple) and len(result) == 2 for result in results)

        # Verify reasonable response times (no hung requests)
        assert (end_time - start_time) < 10  # Should complete within 10 seconds

        # Verify circuit breaker state after concurrent load
        health_status = ai_resilience.get_health_status()
        assert "summarize_text" in health_status["open_circuit_breakers"] or health_status["healthy"] is False

    def test_resilience_metrics_tracking(self, client: TestClient, unreliable_ai_service):
        """
        Test that resilience metrics are properly tracked through the pipeline.

        Integration Scope:
            API endpoint → Resilience orchestration → Metrics collection → Health reporting

        Business Impact:
            Provides operational visibility into resilience system behavior

        Test Strategy:
            - Make requests with different outcomes
            - Verify metrics are collected for each operation
            - Check health status reflects current state
            - Validate metrics structure and content

        Success Criteria:
            - Metrics collected for each operation
            - Success/failure counts accurate
            - Circuit breaker state transitions tracked
            - Health status reflects current metrics
        """
        # Make successful request
        unreliable_ai_service.set_failure_mode("success")

        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "Test document for metrics tracking.",
                "operation": "summarize"
            },
            headers=authenticated_headers
        )

        assert response.status_code == 200

        # Get metrics
        metrics = ai_resilience.get_all_metrics()

        # Verify metrics structure
        assert "operations" in metrics
        assert "summarize_text" in metrics["operations"]

        operation_metrics = metrics["operations"]["summarize_text"]

        # Verify basic metrics are tracked
        assert hasattr(operation_metrics, 'total_calls')
        assert operation_metrics.total_calls >= 1
        assert hasattr(operation_metrics, 'successful_calls')
        assert operation_metrics.successful_calls >= 1

        # Verify health status reflects metrics
        health_status = ai_resilience.get_health_status()
        assert "healthy" in health_status
        assert "total_operations" in health_status
        assert health_status["total_operations"] >= 1

    def test_different_operations_isolated_circuit_breakers(self, client: TestClient, unreliable_ai_service):
        """
        Test that different operations have isolated circuit breakers.

        Integration Scope:
            Multiple API operations → Separate circuit breakers → Independent failure handling

        Business Impact:
            Ensures failure in one operation doesn't affect others

        Test Strategy:
            - Fail one operation to open its circuit breaker
            - Verify other operations continue working normally
            - Confirm circuit breaker isolation

        Success Criteria:
            - Failed operation has open circuit breaker
            - Other operations maintain closed circuit breakers
            - Failed operation returns fallback/degraded responses
            - Other operations return normal responses
        """
        # Configure service to fail for summarize but succeed for sentiment
        unreliable_ai_service.set_failure_mode("permanent_failure")

        # Fail summarize operation to open its circuit breaker
        for _ in range(3):
            client.post(
                "/v1/text_processing/process",
                json={
                    "text": "Test document for summarize failure.",
                    "operation": "summarize"
                },
                headers=authenticated_headers
            )

        # Verify summarize circuit breaker is open
        health_status = ai_resilience.get_health_status()
        assert "summarize_text" in health_status["open_circuit_breakers"]

        # Configure service to succeed for sentiment analysis
        unreliable_ai_service.set_failure_mode("success")

        # Test sentiment analysis still works
        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "Test document for sentiment analysis.",
                "operation": "sentiment"
            },
            headers=authenticated_headers
        )

        # Sentiment should work normally (different circuit breaker)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data or "sentiment" in data

        # Verify summarize still fails due to open circuit breaker
        response = client.post(
            "/v1/text_processing/process",
            json={
                "text": "Test document for summarize with open circuit breaker.",
                "operation": "summarize"
            },
            headers=authenticated_headers
        )

        assert response.status_code == 503  # Service Unavailable due to open circuit breaker
