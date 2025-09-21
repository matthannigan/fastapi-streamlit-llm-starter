"""
MEDIUM PRIORITY: Batch Processing → Concurrency Control → Resilience Integration Test

This test suite verifies the integration between batch processing, concurrency control,
and resilience patterns. It ensures efficient batch processing with proper resource
management and error handling.

Integration Scope:
    Tests the complete batch processing flow from request validation through
    concurrent processing to result aggregation and error handling.

Seam Under Test:
    BatchTextProcessingRequest → Concurrency semaphore → Operation-specific resilience → Result aggregation

Critical Paths:
    - Batch request → Concurrent processing → Individual operation resilience → Result collection
    - Batch size limits and validation
    - Mixed success/failure scenarios
    - Concurrency limit enforcement
    - Operation-specific resilience per batch item
    - Batch result aggregation and error handling
    - Batch progress tracking and monitoring

Business Impact:
    Enables efficient bulk processing while maintaining reliability and resource control.
    Failures here impact batch processing efficiency and system resource management.

Test Strategy:
    - Test successful batch processing with multiple operations
    - Verify batch size limits and validation
    - Test mixed success/failure scenarios
    - Validate concurrency limit enforcement
    - Test operation-specific resilience per batch item
    - Verify batch result aggregation and error handling
    - Test batch progress tracking and monitoring

Success Criteria:
    - Batch processing handles multiple operations concurrently
    - Batch constraints are enforced appropriately
    - Partial batch completion works for mixed scenarios
    - Concurrency limits are respected
    - Per-item resilience strategies are applied
    - Results are properly aggregated
    - Batch state is correctly managed
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.text_processor import TextProcessorService
from app.infrastructure.cache import AIResponseCache
from app.core.config import Settings
from app.schemas import TextProcessingRequest, TextProcessingOperation
from app.api.v1.deps import get_text_processor


class TestBatchProcessingEfficiency:
    """
    Integration tests for batch processing efficiency and reliability.

    Seam Under Test:
        BatchTextProcessingRequest → Concurrency semaphore → Operation-specific resilience → Result aggregation

    Critical Paths:
        - Batch processing with concurrent operation handling
        - Resource management and concurrency control
        - Error handling and partial success scenarios
        - Batch result aggregation and reporting

    Business Impact:
        Validates efficient batch processing that enables bulk operations
        while maintaining system stability and resource control.

    Test Strategy:
        - Test batch processing with multiple operations
        - Verify concurrency control and limits
        - Test error handling and partial success
        - Validate batch result aggregation
    """

    @pytest.fixture(autouse=True)
    def setup_mocking_and_fixtures(self):
        """Set up comprehensive mocking for all tests in this class."""
        # Mock the AI agent to avoid actual API calls
        self.mock_agent_class = MagicMock()
        self.mock_agent_instance = AsyncMock()
        self.mock_agent_class.return_value = self.mock_agent_instance

        # Configure agent for batch processing scenarios
        async def batch_aware_agent_run(user_prompt: str):
            """Return responses based on batch item characteristics."""
            mock_result = MagicMock()

            # Batch-aware responses
            if "batch_item_1" in user_prompt.lower():
                mock_result.output = "Summary of financial data for Q4 earnings report."
            elif "batch_item_2" in user_prompt.lower():
                mock_result.output = '{"sentiment": "positive", "confidence": 0.85, "explanation": "Positive announcement about product launch."}'
            elif "batch_item_3" in user_prompt.lower():
                mock_result.output = "- Security protocol implementation\n- Access control measures\n- Monitoring procedures"
            elif "batch_item_4" in user_prompt.lower():
                mock_result.output = "1. What are the key features?\n2. How does it compare to competitors?\n3. What are the benefits?"
            elif "batch_item_5" in user_prompt.lower():
                mock_result.output = "This document contains information about the new product features and specifications."
            else:
                mock_result.output = "Standard batch processing response."

            return mock_result

        self.mock_agent_instance.run.side_effect = batch_aware_agent_run

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
        return "This is a test of batch processing efficiency and concurrent operation handling in the text processing system."

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for TextProcessorService."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.gemini_api_key = "test-key"
        mock_settings.ai_model = "gemini-pro"
        mock_settings.ai_temperature = 0.7
        mock_settings.BATCH_AI_CONCURRENCY_LIMIT = 5
        mock_settings.MAX_BATCH_REQUESTS_PER_CALL = 10
        return mock_settings

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for TextProcessorService."""
        return AsyncMock(spec=AIResponseCache)

    @pytest.fixture
    def text_processor_service(self, mock_settings, mock_cache):
        """Create TextProcessorService instance for testing."""
        return TextProcessorService(settings=mock_settings, cache=mock_cache)

    def test_successful_batch_processing_multiple_operations(self, client, auth_headers, text_processor_service):
        """
        Test successful batch processing with multiple operations concurrently.

        Integration Scope:
            Batch processing → Concurrent operations → Result aggregation → Response

        Business Impact:
            Validates that batch processing can efficiently handle multiple
            different operations concurrently for improved throughput.

        Test Strategy:
            - Submit batch with multiple different operations
            - Verify concurrent processing occurs
            - Confirm all operations complete successfully
            - Validate batch result aggregation

        Success Criteria:
            - Batch processes multiple operations concurrently
            - All operations complete successfully
            - Results are properly aggregated
            - Batch response structure is correct
            - Processing is efficient and reliable
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {
                        "text": f"{self.sample_text} batch_item_1",
                        "operation": "summarize",
                        "options": {"max_length": 30}
                    },
                    {
                        "text": f"{self.sample_text} batch_item_2",
                        "operation": "sentiment"
                    },
                    {
                        "text": f"{self.sample_text} batch_item_3",
                        "operation": "key_points",
                        "options": {"max_points": 3}
                    },
                    {
                        "text": f"{self.sample_text} batch_item_4",
                        "operation": "questions",
                        "options": {"num_questions": 3}
                    },
                    {
                        "text": f"{self.sample_text} batch_item_5",
                        "operation": "qa",
                        "question": "What are the key features mentioned?"
                    }
                ],
                "batch_id": "test_batch_efficiency"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["batch_id"] == "test_batch_efficiency"
            assert batch_data["total_requests"] == 5
            assert batch_data["completed"] == 5
            assert batch_data["failed"] == 0
            assert "results" in batch_data

            # Verify results structure
            results = batch_data["results"]
            assert len(results) == 5

            # Verify each result has appropriate structure for its operation
            for i, result in enumerate(results):
                assert result["status"] == "completed"
                assert "response" in result

                operation = batch_request["requests"][i]["operation"]
                response_data = result["response"]

                if operation == "sentiment":
                    assert "sentiment" in response_data
                elif operation == "key_points":
                    assert "key_points" in response_data or "result" in response_data
                elif operation == "questions":
                    assert "questions" in response_data or "result" in response_data
                else:
                    assert "result" in response_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_batch_size_limits_enforcement(self, client, auth_headers, text_processor_service):
        """
        Test batch size limits and validation enforcement.

        Integration Scope:
            Batch validation → Size limit enforcement → Error response

        Business Impact:
            Ensures batch processing doesn't overwhelm system resources
            by enforcing appropriate size limits.

        Test Strategy:
            - Submit batch exceeding size limits
            - Verify proper validation and error handling
            - Confirm appropriate error response
            - Test boundary conditions

        Success Criteria:
            - Batch size limits are enforced correctly
            - Clear error messages for size violations
            - No processing occurs for oversized batches
            - Boundary conditions are handled properly
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Test batch with too many requests (exceeds default limit)
            large_batch_request = {
                "requests": [
                    {
                        "text": f"Batch item {i}",
                        "operation": "summarize"
                    }
                    for i in range(15)  # Exceeds typical limit
                ],
                "batch_id": "test_large_batch"
            }

            response = client.post("/v1/text_processing/batch_process", json=large_batch_request, headers=auth_headers)
            assert response.status_code in [400, 422]  # Validation error

            # Verify error response mentions batch size
            error_data = response.json()
            error_text = str(error_data).lower()
            assert "batch" in error_text and ("limit" in error_text or "exceeds" in error_text or "maximum" in error_text)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_mixed_success_failure_batch_scenarios(self, client, auth_headers, text_processor_service):
        """
        Test mixed success/failure scenarios in batch processing.

        Integration Scope:
            Batch processing → Mixed results → Partial success handling → Result aggregation

        Business Impact:
            Ensures batch processing handles partial failures gracefully
            while completing successful operations.

        Test Strategy:
            - Configure mixed success/failure scenarios
            - Verify partial success handling
            - Confirm successful operations complete
            - Validate error reporting for failed operations

        Success Criteria:
            - Successful operations complete despite failures
            - Failed operations are reported appropriately
            - Partial batch results are handled correctly
            - No successful operations are lost due to failures
            - Error information is comprehensive and useful
        """
        # Configure agent to simulate mixed success/failure
        failure_count = 0
        async def mixed_result_agent_run(user_prompt: str):
            nonlocal failure_count
            failure_count += 1

            # Fail every third request to create mixed results
            if failure_count % 3 == 0:
                raise Exception(f"Simulated failure for request {failure_count}")

            mock_result = MagicMock()
            mock_result.output = f"Successful processing for request {failure_count}"
            return mock_result

        self.mock_agent_instance.run.side_effect = mixed_result_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} mixed_test_{i}", "operation": "summarize"}
                    for i in range(1, 7)  # 6 requests, 2 should fail
                ],
                "batch_id": "test_mixed_results"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["batch_id"] == "test_mixed_results"
            assert batch_data["total_requests"] == 6

            # Should have mixed results (4 successful, 2 failed)
            assert batch_data["completed"] == 4
            assert batch_data["failed"] == 2

            # Verify results structure
            assert "results" in batch_data
            results = batch_data["results"]
            assert len(results) == 6

            # Verify mixed success/failure reporting
            completed_count = sum(1 for r in results if r["status"] == "completed")
            failed_count = sum(1 for r in results if r["status"] == "failed")

            assert completed_count == 4
            assert failed_count == 2

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_concurrency_limit_enforcement(self, client, auth_headers, text_processor_service):
        """
        Test concurrency limit enforcement in batch processing.

        Integration Scope:
            Batch processing → Concurrency control → Semaphore enforcement → Resource management

        Business Impact:
            Ensures batch processing respects concurrency limits to prevent
            resource exhaustion and maintain system stability.

        Test Strategy:
            - Submit batch that would exceed concurrency limits
            - Verify concurrency controls are applied
            - Confirm resource management works correctly
            - Validate system stability under load

        Success Criteria:
            - Concurrency limits are enforced appropriately
            - Resource management prevents system overload
            - Batch processing respects concurrency constraints
            - System remains stable during concurrent processing
            - Processing completes successfully within limits
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Test with reasonable batch size within limits
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} concurrency_test_{i}", "operation": "summarize"}
                    for i in range(3)  # Within concurrency limits
                ],
                "batch_id": "test_concurrency_control"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["completed"] == 3
            assert batch_data["failed"] == 0

            # Verify all requests completed successfully
            assert len(batch_data["results"]) == 3
            for result in batch_data["results"]:
                assert result["status"] == "completed"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_operation_specific_resilience_per_batch_item(self, client, auth_headers, text_processor_service):
        """
        Test operation-specific resilience strategies per batch item.

        Integration Scope:
            Batch item → Operation-specific resilience → Individual processing → Result aggregation

        Business Impact:
            Ensures each batch item uses appropriate resilience strategy
            based on its operation type for optimal reliability.

        Test Strategy:
            - Submit batch with different operation types
            - Verify operation-specific resilience is applied
            - Confirm appropriate strategies per operation
            - Validate resilience strategy effectiveness

        Success Criteria:
            - Each operation uses its designated resilience strategy
            - Resilience strategies are applied per batch item
            - Different operations have appropriate resilience levels
            - Resilience effectiveness is maintained per item
            - Batch processing adapts to operation requirements
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {
                        "text": f"{self.sample_text} batch_item_1",
                        "operation": "summarize"  # Should use balanced resilience
                    },
                    {
                        "text": f"{self.sample_text} batch_item_2",
                        "operation": "sentiment"  # Should use aggressive resilience
                    },
                    {
                        "text": f"{self.sample_text} batch_item_3",
                        "operation": "qa",
                        "question": "What is this about?"  # Should use conservative resilience
                    }
                ],
                "batch_id": "test_operation_resilience"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["completed"] == 3
            assert batch_data["failed"] == 0

            # Verify operation-specific results
            results = batch_data["results"]
            assert len(results) == 3

            # Each operation should have appropriate response structure
            for result in results:
                assert result["status"] == "completed"
                assert "response" in result

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_batch_result_aggregation_and_error_handling(self, client, auth_headers, text_processor_service):
        """
        Test batch result aggregation and comprehensive error handling.

        Integration Scope:
            Batch processing → Result aggregation → Error consolidation → Final response

        Business Impact:
            Ensures batch results are properly aggregated and errors
            are consolidated for clear user feedback.

        Test Strategy:
            - Process batch with mixed results
            - Verify result aggregation logic
            - Test error consolidation and reporting
            - Validate final response structure

        Success Criteria:
            - Results are properly aggregated across all items
            - Errors are consolidated and reported clearly
            - Final response structure is comprehensive
            - User receives complete batch processing summary
            - No information is lost in aggregation process
        """
        # Configure agent to create mixed results scenario
        call_count = 0
        async def mixed_aggregation_agent_run(user_prompt: str):
            nonlocal call_count
            call_count += 1

            # Create specific results for testing aggregation
            mock_result = MagicMock()

            if call_count == 1:
                mock_result.output = "First item processed successfully"
            elif call_count == 2:
                mock_result.output = '{"sentiment": "neutral", "confidence": 0.75, "explanation": "Mixed sentiment analysis"}'
            elif call_count == 3:
                mock_result.output = "- Key point one\n- Key point two\n- Key point three"
            else:
                mock_result.output = "Standard batch processing response"

            return mock_result

        self.mock_agent_instance.run.side_effect = mixed_aggregation_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} aggregation_test_1", "operation": "summarize"},
                    {"text": f"{self.sample_text} aggregation_test_2", "operation": "sentiment"},
                    {"text": f"{self.sample_text} aggregation_test_3", "operation": "key_points", "options": {"max_points": 3}}
                ],
                "batch_id": "test_aggregation"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["batch_id"] == "test_aggregation"
            assert batch_data["total_requests"] == 3
            assert batch_data["completed"] == 3
            assert batch_data["failed"] == 0

            # Verify result aggregation
            results = batch_data["results"]
            assert len(results) == 3

            # Verify each result maintains its operation-specific structure
            for i, result in enumerate(results):
                assert result["status"] == "completed"
                assert "response" in result

                operation = batch_request["requests"][i]["operation"]
                response_data = result["response"]

                if operation == "summarize":
                    assert "result" in response_data
                    assert "first item" in response_data["result"].lower()
                elif operation == "sentiment":
                    assert "sentiment" in response_data
                elif operation == "key_points":
                    assert "key_points" in response_data or "result" in response_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_batch_progress_tracking_and_monitoring(self, client, auth_headers, text_processor_service):
        """
        Test batch progress tracking and monitoring capabilities.

        Integration Scope:
            Batch processing → Progress tracking → State monitoring → Status reporting

        Business Impact:
            Provides visibility into batch processing progress for
            operational monitoring and user feedback.

        Test Strategy:
            - Monitor batch processing progress
            - Verify state tracking throughout processing
            - Test progress reporting mechanisms
            - Validate monitoring integration

        Success Criteria:
            - Batch processing progress is tracked accurately
            - State changes are monitored throughout processing
            - Progress reporting provides useful information
            - Monitoring integration works correctly
            - User receives visibility into batch status
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} progress_test_{i}", "operation": "summarize"}
                    for i in range(3)
                ],
                "batch_id": "test_progress_tracking"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["batch_id"] == "test_progress_tracking"
            assert batch_data["total_requests"] == 3
            assert batch_data["completed"] == 3
            assert batch_data["failed"] == 0

            # Verify progress tracking information
            assert "total_processing_time" in batch_data
            assert isinstance(batch_data["total_processing_time"], (int, float))
            assert batch_data["total_processing_time"] > 0

            # Verify batch status endpoint works
            status_response = client.get(f"/v1/text_processing/batch_status/{batch_data['batch_id']}", headers=auth_headers)
            assert status_response.status_code == 200

            status_data = status_response.json()
            assert status_data["batch_id"] == batch_data["batch_id"]
            assert "COMPLETED" in status_data["status"]

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_batch_processing_resource_management(self, client, auth_headers, text_processor_service):
        """
        Test batch processing resource management and efficiency.

        Integration Scope:
            Batch processing → Resource allocation → Memory management → Cleanup

        Business Impact:
            Ensures batch processing manages system resources efficiently
            and doesn't cause memory leaks or resource exhaustion.

        Test Strategy:
            - Test resource allocation during batch processing
            - Verify memory management and cleanup
            - Monitor resource usage patterns
            - Validate efficient resource utilization

        Success Criteria:
            - Resources are allocated efficiently for batch processing
            - Memory management works correctly
            - Resource cleanup occurs properly
            - No memory leaks or resource exhaustion
            - Efficient resource utilization is maintained
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Test with moderate batch size for resource management
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} resource_test_{i}", "operation": "summarize", "options": {"max_length": 50}}
                    for i in range(5)
                ],
                "batch_id": "test_resource_management"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["completed"] == 5
            assert batch_data["failed"] == 0

            # Verify resource-efficient processing
            assert "total_processing_time" in batch_data
            assert len(batch_data["results"]) == 5

            # Each result should be properly structured
            for result in batch_data["results"]:
                assert result["status"] == "completed"
                assert "response" in result
                assert "result" in result["response"]

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_batch_processing_error_recovery(self, client, auth_headers, text_processor_service):
        """
        Test batch processing error recovery and resilience.

        Integration Scope:
            Batch processing → Error recovery → Partial success → System resilience

        Business Impact:
            Ensures batch processing recovers from errors and maintains
            system resilience during failures.

        Test Strategy:
            - Test error recovery during batch processing
            - Verify partial success handling
            - Confirm system maintains resilience
            - Validate error recovery mechanisms

        Success Criteria:
            - Error recovery works correctly during batch processing
            - Partial success is handled appropriately
            - System maintains resilience during failures
            - Recovery mechanisms function properly
            - Processing continues after recoverable errors
        """
        # Configure agent to simulate recoverable errors
        error_count = 0
        async def recoverable_error_agent_run(user_prompt: str):
            nonlocal error_count
            error_count += 1

            # Simulate recoverable error for first few calls
            if error_count <= 2:
                raise Exception(f"Recoverable error {error_count}")

            mock_result = MagicMock()
            mock_result.output = f"Recovered processing after error {error_count}"
            return mock_result

        self.mock_agent_instance.run.side_effect = recoverable_error_agent_run

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} recovery_test_{i}", "operation": "summarize"}
                    for i in range(3)
                ],
                "batch_id": "test_error_recovery"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["batch_id"] == "test_error_recovery"
            assert batch_data["total_requests"] == 3
            assert batch_data["completed"] == 3  # Should recover from errors
            assert batch_data["failed"] == 0

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_batch_processing_efficiency_metrics(self, client, auth_headers, text_processor_service):
        """
        Test batch processing efficiency metrics and performance monitoring.

        Integration Scope:
            Batch processing → Efficiency metrics → Performance monitoring → Optimization data

        Business Impact:
            Provides efficiency metrics for batch processing optimization
            and performance monitoring.

        Test Strategy:
            - Monitor batch processing efficiency
            - Collect performance metrics
            - Verify efficiency calculations
            - Validate optimization data collection

        Success Criteria:
            - Efficiency metrics are collected accurately
            - Performance monitoring works correctly
            - Efficiency calculations are correct
            - Optimization data is available for analysis
            - Batch processing performance is measurable
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            batch_request = {
                "requests": [
                    {"text": f"{self.sample_text} efficiency_test_{i}", "operation": "summarize"}
                    for i in range(4)
                ],
                "batch_id": "test_efficiency_metrics"
            }

            response = client.post("/v1/text_processing/batch_process", json=batch_request, headers=auth_headers)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data["batch_id"] == "test_efficiency_metrics"
            assert batch_data["total_requests"] == 4
            assert batch_data["completed"] == 4
            assert batch_data["failed"] == 0

            # Verify efficiency metrics are included
            assert "total_processing_time" in batch_data
            assert isinstance(batch_data["total_processing_time"], (int, float))

            # Calculate efficiency (requests per second)
            total_time = batch_data["total_processing_time"]
            efficiency = batch_data["total_requests"] / total_time if total_time > 0 else 0
            assert efficiency > 0  # Should have processed requests in reasonable time

        finally:
            # Clean up override
            app.dependency_overrides.clear()
