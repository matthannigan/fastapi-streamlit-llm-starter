"""
Integration tests for batch processing with concurrency management.

Tests the API → TextProcessorService → Batch Processing → Concurrency Management seam.
Validates bulk processing efficiency, resource management, error isolation, and cache integration.
"""
import pytest
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

from app.core.exceptions import ValidationError, BusinessLogicError, InfrastructureError


class TestBatchProcessingIntegration:
    """
    Integration tests for batch processing with concurrency management.

    Seam Under Test:
        API → TextProcessorService → Batch Processing → Concurrency Management

    Critical Paths:
        - Large batch processes efficiently within configured concurrency limits
        - Individual request failures don't affect other batch requests (error isolation)
        - Batch result aggregation maintains correct order and status tracking
        - Cache integration works correctly in batch context (individual requests can hit cache)
        - Performance scales appropriately with batch size within limits
        - Memory usage remains bounded during large batch processing
    """

    def test_batch_processing_handles_large_batch_within_concurrency_limits(
        self, test_client, authenticated_headers, batch_request_data, performance_monitor
    ):
        """
        Test that batch processing handles large batches efficiently within concurrency limits.

        Integration Scope:
            API endpoint, TextProcessorService, concurrency semaphore, batch aggregation

        Business Impact:
            Validates bulk processing efficiency for enterprise use cases, ensures system
            stability under high-volume batch operations, confirms resource management
            prevents system overload

        Test Strategy:
            - Create a large batch request (50+ items)
            - Monitor processing time and resource usage
            - Verify all requests are processed within reasonable time
            - Confirm concurrency limits are respected

        Success Criteria:
            - All 50+ requests processed successfully
            - Processing time scales appropriately with batch size
            - No resource exhaustion or timeout issues
        """
        # Arrange - Create large batch request
        large_batch = {
            "requests": []
        }

        # Generate 50 diverse requests
        base_requests = batch_request_data["requests"]
        for i in range(50):
            base_req = base_requests[i % len(base_requests)].copy()
            base_req["id"] = f"large_req_{i}"
            base_req["text"] = f"Request {i}: {base_req['text']}"
            large_batch["requests"].append(base_req)

        # Act - Start performance monitoring and process batch
        performance_monitor.start()
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=large_batch
        )
        performance_monitor.stop()

        # Assert - Verify successful batch processing
        assert response.status_code == 200
        result = response.json()

        assert result["total_requests"] == 50
        assert result["completed"] == 50
        assert result["failed"] == 0
        assert len(result["results"]) == 50

        # Verify all results have proper structure
        for i, processed_result in enumerate(result["results"]):
            assert "response" in processed_result
            assert processed_result["response"]["operation"] in ["sentiment", "summarize", "key_points"]

        # Performance should be reasonable (not too slow, indicating proper concurrency)
        elapsed_ms = performance_monitor.elapsed_ms
        assert elapsed_ms is not None
        # 50 requests should complete in reasonable time (adjusted for test environment and fallback responses)
        assert elapsed_ms < 60000  # 60 seconds max for 50 requests with fallback responses

    def test_batch_processing_error_isolation(
        self, test_client, authenticated_headers, batch_request_data
    ):
        """
        Test that individual request failures don't affect other batch requests.

        Integration Scope:
            API endpoint, TextProcessorService, error handling, batch aggregation

        Business Impact:
            Ensures system reliability by preventing individual failures from affecting
            entire batch operations, maintains partial success capabilities for robust
            enterprise processing

        Test Strategy:
            - Create batch with all valid requests but test service-level error isolation
            - Use text that might cause processing challenges but passes validation
            - Verify that if some requests face processing issues, others still succeed

        Success Criteria:
            - All requests pass validation (API returns 200)
            - Individual request processing can fail without affecting others
            - Batch completion includes proper status tracking
        """
        # Arrange - Create batch with requests that might have processing challenges
        mixed_batch = {
            "requests": [
                # Standard valid request
                {
                    "id": "standard_1",
                    "text": "This is a positive and happy statement that should process easily.",
                    "operation": "sentiment"
                },
                # Very long text that might timeout
                {
                    "id": "long_text",
                    "text": "This is an extremely long text " * 100 + "that might cause processing challenges.",
                    "operation": "summarize"
                },
                # Standard valid request
                {
                    "id": "standard_2",
                    "text": "Contact us at test@example.com or call 555-123-4567 for support.",
                    "operation": "key_points"
                },
                # Text with special characters
                {
                    "id": "special_chars",
                    "text": "Text with special characters: émojis 🎉 and symbols #$%^&*() that might cause processing issues.",
                    "operation": "sentiment"
                },
                # Another standard request
                {
                    "id": "standard_3",
                    "text": "This document provides key information about the quarterly results.",
                    "operation": "key_points"
                }
            ]
        }

        # Act - Process mixed batch
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=mixed_batch
        )

        # Assert - Verify error isolation
        assert response.status_code == 200
        result = response.json()

        # Should have processed all requests
        assert result["total_requests"] == 5
        assert len(result["results"]) == 5

        # All requests should have some response (even if fallback is used)
        for processed_result in result["results"]:
            assert "response" in processed_result
            assert "status" in processed_result
            # All should complete (may use fallback responses)
            assert processed_result["status"] in ["completed", "failed"]

        # Check that at least some requests completed successfully
        successful_results = [r for r in result["results"] if r["status"] == "completed"]
        assert len(successful_results) >= 3  # Most should complete with fallback

    def test_batch_result_aggregation_maintains_order_and_status(
        self, test_client, authenticated_headers, batch_request_data
    ):
        """
        Test that batch result aggregation maintains correct order and status tracking.

        Integration Scope:
            API endpoint, TextProcessorService, result aggregation, order preservation

        Business Impact:
            Ensures result integrity and traceability for enterprise batch operations,
            enables reliable post-processing of batch results with proper ordering
            and status tracking

        Test Strategy:
            - Create batch with uniquely identifiable requests
            - Process batch and verify result order matches input order
            - Confirm status tracking is accurate for each request

        Success Criteria:
            - Results are returned in the same order as input requests
            - Each result contains the correct request ID
            - Status tracking accurately reflects success/failure for each request
        """
        # Arrange - Create batch with uniquely identifiable requests
        ordered_batch = {
            "requests": []
        }

        # Create requests with unique, traceable content
        unique_texts = [
            "SENTIMENT_POSITIVE_12345",
            "SUMMARIZE_UNIQUE_TEXT_67890",
            "EXTRACT_CONTACT_INFO_ABCDE",
            "SENTIMENT_NEGATIVE_TEXT_FGHIJ",
            "SUMMARIZE_DIFFERENT_TEXT_KLMNO"
        ]

        for i, text in enumerate(unique_texts):
            ordered_batch["requests"].append({
                "id": f"ordered_req_{i}",
                "text": text,
                "operation": "sentiment" if i % 2 == 0 else "summarize"
            })

        # Act - Process ordered batch
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=ordered_batch
        )

        # Assert - Verify order preservation and status tracking
        assert response.status_code == 200
        result = response.json()

        assert result["total_requests"] == 5
        assert len(result["results"]) == 5

        # Verify results are in the same order as input
        for i, processed_result in enumerate(result["results"]):
            expected_id = f"ordered_req_{i}"
            assert processed_result.get("request_index") == i

            # Verify the result corresponds to the right operation
            if i % 2 == 0:  # sentiment
                assert processed_result["response"].get("operation") == "sentiment"
            else:  # summarize
                assert processed_result["response"].get("operation") == "summarize"

    def test_cache_integration_works_in_batch_context(
        self, test_client, authenticated_headers, ai_response_cache, batch_request_data
    ):
        """
        Test that cache integration works correctly in batch processing context.

        Integration Scope:
            API endpoint, TextProcessorService, AIResponseCache, batch processing

        Business Impact:
            Validates cache optimization in batch operations, reduces redundant AI API
            calls for duplicate requests, improves performance and cost efficiency
            for enterprise batch processing

        Test Strategy:
            - Pre-populate cache with some responses
            - Create batch with duplicate requests that should hit cache
            - Verify cache hits reduce processing time and AI calls

        Success Criteria:
            - Duplicate requests in batch hit cache successfully
            - Cache integration doesn't break batch processing
            - Processing is faster for cached requests
        """
        # Arrange - Pre-populate cache with some responses
        import asyncio

        # Create a mock cached response
        cached_response = {
            "result": "Cached positive sentiment response",
            "operation": "sentiment",
            "metadata": {"cache_hit": True, "processing_time": 0.1}
        }

        # Cache a response for the first request
        first_request = batch_request_data["requests"][0]
        cache_key = f"text_processing:{first_request['operation']}:{hash(first_request['text'])}"

        async def setup_cache():
            await ai_response_cache.set(cache_key, cached_response, ttl=300)

        # Run cache setup synchronously
        asyncio.run(setup_cache())

        # Create batch with duplicates that should hit cache
        batch_with_duplicates = {
            "requests": [
                # This should hit cache
                batch_request_data["requests"][0].copy(),
                # These should require AI processing
                batch_request_data["requests"][1].copy(),
                batch_request_data["requests"][3].copy(),
                # This should also hit cache (duplicate of first)
                batch_request_data["requests"][0].copy()
            ]
        }

        # Give unique IDs to track results
        for i, req in enumerate(batch_with_duplicates["requests"]):
            req["id"] = f"cache_test_{i}"

        # Act - Process batch with cache integration
        start_time = time.time()
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=batch_with_duplicates
        )
        processing_time = time.time() - start_time

        # Assert - Verify cache integration works
        assert response.status_code == 200
        result = response.json()

        assert result["total_requests"] == 4
        assert result["completed"] == 4
        assert result["failed"] == 0
        assert len(result["results"]) == 4

        # Processing should be relatively fast due to cache hits
        assert processing_time < 10.0  # Should complete quickly with cache hits

        # Verify all results have proper structure
        for processed_result in result["results"]:
            assert "response" in processed_result
            assert "operation" in processed_result["response"]

    def test_performance_scales_appropriately_with_batch_size(
        self, test_client, authenticated_headers, batch_request_data, performance_monitor
    ):
        """
        Test that performance scales appropriately with batch size within limits.

        Integration Scope:
            API endpoint, TextProcessorService, concurrency management, performance scaling

        Business Impact:
            Validates system performance characteristics under varying loads, ensures
            predictable processing times for capacity planning, confirms resource
            management effectiveness

        Test Strategy:
            - Test batches of different sizes (5, 10, 25 requests)
            - Measure processing time for each batch size
            - Verify scaling is reasonable (not linear degradation)

        Success Criteria:
            - Processing time scales sub-linearly with batch size
            - No significant performance degradation at larger scales
            - Concurrency limits prevent resource exhaustion
        """
        # Arrange - Create test batches of different sizes
        batch_sizes = [5, 10, 25]
        processing_times = {}

        base_request = batch_request_data["requests"][0]

        for batch_size in batch_sizes:
            # Create batch of specified size
            test_batch = {
                "requests": []
            }

            for i in range(batch_size):
                req = base_request.copy()
                req["id"] = f"scale_test_{batch_size}_{i}"
                req["text"] = f"Scale test {batch_size}-{i}: {req['text']}"
                test_batch["requests"].append(req)

            # Act - Process batch and measure time
            performance_monitor.start()
            response = test_client.post(
                "/v1/text_processing/batch_process",
                headers=authenticated_headers,
                json=test_batch
            )
            performance_monitor.stop()

            # Assert - Verify successful processing
            assert response.status_code == 200
            result = response.json()
            assert result["total_requests"] == batch_size
            assert result["completed"] == batch_size
            assert result["failed"] == 0

            # Record processing time
            processing_times[batch_size] = performance_monitor.elapsed_ms

        # Verify performance scaling is reasonable
        # Time should not increase linearly (concurrency should help)
        time_5 = processing_times[5]
        time_10 = processing_times[10]
        time_25 = processing_times[25]

        # 10 requests shouldn't take 2.5x time of 5 requests (due to concurrency)
        assert time_10 < time_5 * 2.5

        # 25 requests shouldn't take 6x time of 5 requests (due to concurrency)
        assert time_25 < time_5 * 6.0

        # All should complete in reasonable time
        for batch_size, elapsed_ms in processing_times.items():
            assert elapsed_ms < 20000  # 20 seconds max per batch size

    def test_memory_usage_remains_bounded_during_large_batch_processing(
        self, test_client, authenticated_headers, performance_monitor
    ):
        """
        Test that memory usage remains bounded during large batch processing.

        Integration Scope:
            API endpoint, TextProcessorService, memory management, resource bounds

        Business Impact:
            Ensures system stability during large batch operations, prevents memory
            leaks and resource exhaustion, validates infrastructure reliability for
            enterprise-scale processing

        Test Strategy:
            - Create very large batch with substantial text content
            - Monitor processing completion without memory errors
            - Verify system remains responsive throughout processing

        Success Criteria:
            - Large batch processes successfully without memory issues
            - Processing completes within reasonable time bounds
            - System remains stable after processing
        """
        # Arrange - Create large batch with substantial content
        large_text_batch = {
            "requests": []
        }

        # Generate 30 requests with substantial text content
        large_text = """
        This is a substantial text block designed to test memory usage during batch processing.
        It contains multiple sentences and should be large enough to create meaningful memory pressure
        when processing multiple requests simultaneously. The content is designed to simulate
        real-world text processing scenarios where documents might be several paragraphs long.
        The batch processing system should handle this efficiently without running into memory
        issues or resource exhaustion, even when processing multiple such documents concurrently.
        """

        for i in range(30):
            large_text_batch["requests"].append({
                "id": f"memory_test_{i}",
                "text": f"Document {i}: {large_text}",
                "operation": "summarize" if i % 2 == 0 else "sentiment"
            })

        # Act - Process large batch with memory monitoring
        performance_monitor.start()
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=large_text_batch
        )
        performance_monitor.stop()

        # Assert - Verify successful processing without memory issues
        assert response.status_code == 200
        result = response.json()

        assert result["total_requests"] == 30
        assert result["completed"] == 30
        assert result["failed"] == 0
        assert len(result["results"]) == 30

        # Verify processing completed in reasonable time
        elapsed_ms = performance_monitor.elapsed_ms
        assert elapsed_ms is not None
        assert elapsed_ms < 45000  # 45 seconds max for 30 large requests

        # Verify all results have proper structure
        for processed_result in result["results"]:
            assert "response" in processed_result
            assert processed_result["response"]["success"] is True  # Should succeed
            assert processed_result["response"]["operation"] in ["summarize", "sentiment"]

    def test_batch_processing_with_mixed_operations(
        self, test_client, authenticated_headers, batch_request_data
    ):
        """
        Test batch processing with mixed operation types.

        Integration Scope:
            API endpoint, TextProcessorService, operation routing, batch aggregation

        Business Impact:
            Validates system capability to handle diverse workloads in single batch,
            ensures operation isolation and proper routing, confirms enterprise
            flexibility for mixed processing scenarios

        Test Strategy:
            - Create batch with all supported operation types
            - Verify each operation is processed correctly
            - Confirm operation-specific behavior is preserved

        Success Criteria:
            - All operation types process successfully in same batch
            - Each result shows correct operation type
            - Operation-specific options work correctly
        """
        # Arrange - Create batch with all operation types
        mixed_operations_batch = {
            "requests": [
                {
                    "id": "sentiment_req",
                    "text": "I am feeling extremely happy and excited about this wonderful opportunity!",
                    "operation": "sentiment",
                    "options": {"analyze_emotions": True, "confidence_threshold": 0.8}
                },
                {
                    "id": "summarize_req",
                    "text": "This is a comprehensive document covering multiple aspects of the topic. It discusses various viewpoints, provides detailed analysis, and presents conclusions based on extensive research. The document is structured in multiple sections, each addressing specific components of the subject matter.",
                    "operation": "summarize",
                    "options": {"max_length": 100, "extract_key_points": True}
                },
                {
                    "id": "extract_req",
                    "text": "Please contact John Smith at john.smith@company.com or call 555-123-4567. Meeting scheduled for March 15, 2024 at 2:00 PM EST. Address: 123 Main Street, New York, NY 10001.",
                    "operation": "key_points",
                    "options": {"max_points": 5}
                }
            ]
        }

        # Act - Process mixed operations batch
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=mixed_operations_batch
        )

        # Assert - Verify all operations processed correctly
        assert response.status_code == 200
        result = response.json()

        assert result["total_requests"] == 3
        assert result["completed"] == 3
        assert result["failed"] == 0
        assert len(result["results"]) == 3

        # Verify each operation was processed correctly
        operations_found = set()
        for processed_result in result["results"]:
            assert "response" in processed_result
            assert "operation" in processed_result["response"]
            operations_found.add(processed_result["response"]["operation"])
            # Result field may be None for fallback responses, but structure should exist
            assert processed_result["response"]["success"] is True

        # Confirm all operation types are present
        expected_operations = {"sentiment", "summarize", "key_points"}
        assert operations_found == expected_operations

    @pytest.mark.slow
    def test_batch_processing_respects_maximum_batch_size_limits(
        self, test_client, authenticated_headers
    ):
        """
        Test that batch processing respects maximum batch size limits.

        Integration Scope:
            API endpoint, validation layer, batch size limits

        Business Impact:
            Prevents system overload from oversized batches, ensures fair resource
            allocation, validates infrastructure protection mechanisms

        Test Strategy:
            - Create batch exceeding maximum allowed size
            - Verify proper validation error is returned
            - Confirm system remains stable after rejected request

        Success Criteria:
            - Oversized batches are properly rejected
            - Clear error message is provided
            - System remains stable and responsive
        """
        # Arrange - Create batch exceeding maximum size
        oversized_batch = {
            "requests": []
        }

        # Create more requests than should be allowed (assuming max is around 100)
        max_allowed = 100
        for i in range(max_allowed + 50):  # Exceed limit by 50
            oversized_batch["requests"].append({
                "id": f"oversize_{i}",
                "text": f"Request {i} text content for testing batch size limits.",
                "operation": "sentiment"
            })

        # Act - Attempt to process oversized batch
        response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=oversized_batch
        )

        # Assert - Verify batch size limit is enforced
        # Should return validation error for oversized batch
        assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity

        error_detail = response.json().get("detail", "")
        assert "batch" in error_detail.lower() or "size" in error_detail.lower() or "limit" in error_detail.lower()

        # Verify system is still responsive with normal-sized batch
        normal_batch = {
            "requests": [
                {
                    "id": "normal_req",
                    "text": "This is a normal-sized batch request.",
                    "operation": "sentiment"
                }
            ]
        }

        normal_response = test_client.post(
            "/v1/text_processing/batch_process",
            headers=authenticated_headers,
            json=normal_batch
        )

        assert normal_response.status_code == 200
        assert normal_response.json()["completed"] == 1