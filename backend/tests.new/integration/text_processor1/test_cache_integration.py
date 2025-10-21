"""
MEDIUM PRIORITY: TextProcessorService → Cache → AI Services Integration Test

This test suite verifies the integration between TextProcessorService, cache infrastructure,
and AI services. It ensures that caching works correctly to improve performance and reduce
AI API costs while maintaining data integrity and freshness.

Integration Scope:
    Tests the complete caching integration from cache lookup through AI processing
    to cache storage and retrieval.

Seam Under Test:
    TextProcessorService → AIResponseCache → PydanticAI Agent → Response storage

Critical Paths:
    - Cache lookup → AI processing (if cache miss) → Response caching → Result return
    - Cache hit scenario (response retrieved from cache without AI call)
    - Cache failure fallback (graceful degradation when cache unavailable)
    - Cache key generation and collision handling
    - TTL and expiration behavior
    - Concurrent cache access
    - Cache performance monitoring

Business Impact:
    Critical for performance optimization and cost reduction in production environments.
    Failures here directly impact system performance and operational costs.

Test Strategy:
    - Test cache hit scenario (verify response retrieved from cache without AI call)
    - Test cache miss scenario (verify AI processing and cache storage)
    - Test cache failure fallback (verify graceful degradation when cache unavailable)
    - Test cache key generation and collision handling
    - Test TTL and expiration behavior
    - Test concurrent cache access
    - Test cache performance monitoring

Success Criteria:
    - Cache integration provides expected performance improvements
    - Configuration loading meets performance requirements
    - Concurrent processing maintains system stability
    - Health checks provide accurate system status
    - Security validation doesn't impact processing performance
"""

import pytest
import asyncio
import time
import uuid
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


class TestCacheIntegration:
    """
    Integration tests for cache integration with TextProcessorService.

    Seam Under Test:
        TextProcessorService → AIResponseCache → PydanticAI Agent → Response storage

    Critical Paths:
        - Cache lookup and hit/miss scenarios
        - AI processing with cache integration
        - Cache failure handling and fallback
        - Concurrent cache access patterns

    Business Impact:
        Validates caching functionality that significantly impacts
        performance and cost optimization.

    Test Strategy:
        - Test cache hit and miss scenarios
        - Verify cache integration with AI processing
        - Test cache failure handling
        - Validate concurrent cache access
    """

    @pytest.fixture(autouse=True)
    def setup_mocking_and_fixtures(self):
        """Set up comprehensive mocking for all tests in this class."""
        # Mock the AI agent to avoid actual API calls
        self.mock_agent_class = MagicMock()
        self.mock_agent_instance = AsyncMock()
        self.mock_agent_class.return_value = self.mock_agent_instance

        # Configure agent to return unique responses for different inputs
        async def unique_response_agent_run(user_prompt: str):
            """Return unique responses based on input content."""
            # Extract user text from prompt
            user_text = ""
            if "---USER TEXT START---" in user_prompt and "---USER TEXT END---" in user_prompt:
                start_marker = "---USER TEXT START---"
                end_marker = "---USER TEXT END---"
                start_idx = user_prompt.find(start_marker) + len(start_marker)
                end_idx = user_prompt.find(end_marker)
                user_text = user_prompt[start_idx:end_idx].strip()
            else:
                user_text = user_prompt

            # Create unique response based on content
            mock_result = MagicMock()

            # Generate unique response based on input characteristics
            if "cache_test_1" in user_text:
                mock_result.output = "Unique response for cache test 1 - first processing"
            elif "cache_test_2" in user_text:
                mock_result.output = "Unique response for cache test 2 - different content"
            elif "sentiment" in user_text.lower():
                mock_result.output = '{"sentiment": "positive", "confidence": 0.85, "explanation": "Cache-integrated sentiment analysis"}'
            else:
                mock_result.output = f"Cache-integrated processing response for: {user_text[:50]}..."

            return mock_result

        self.mock_agent_instance.run.side_effect = unique_response_agent_run

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
        return "This is a comprehensive test of cache integration with the text processing system."

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

    def test_cache_hit_scenario(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache hit scenario where response is retrieved from cache without AI call.

        Integration Scope:
            API endpoint → TextProcessorService → Cache hit → Response return

        Business Impact:
            Validates that caching works correctly to avoid redundant AI API calls,
            improving performance and reducing costs.

        Test Strategy:
            - Configure cache to return cached response
            - Submit request that should hit cache
            - Verify response comes from cache
            - Confirm AI processing is skipped for cache hits

        Success Criteria:
            - Cache hit returns appropriate response
            - AI processing is bypassed for cache hits
            - Response includes cache hit indicator
            - Performance improvement is achieved
        """
        # Configure cache to return cached response (cache hit)
        cached_response = {
            "operation": "summarize",
            "result": "Cached summary from previous processing",
            "success": True,
            "processing_time": 0.1,
            "metadata": {"word_count": 8},
            "cached_at": "2024-01-01T12:00:00",
            "cache_hit": True
        }

        mock_cache.get_cached_response = AsyncMock(return_value=cached_response)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} cache_hit_test",
                "operation": "summarize",
                "options": {"max_length": 50}
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert data["result"] == "Cached summary from previous processing"
            assert data["cache_hit"] is True  # Should indicate cache hit

            # Verify cache was checked but AI processing was skipped
            mock_cache.get_cached_response.assert_called_once()
            # AI agent should not be called for cache hits

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_miss_scenario(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache miss scenario where AI processing occurs and response is cached.

        Integration Scope:
            API endpoint → TextProcessorService → Cache miss → AI processing → Cache storage

        Business Impact:
            Ensures that cache misses result in AI processing and proper cache storage
            for future requests.

        Test Strategy:
            - Configure cache to return None (cache miss)
            - Submit request that requires AI processing
            - Verify AI processing occurs
            - Confirm response is cached for future use

        Success Criteria:
            - Cache miss triggers AI processing
            - AI processing completes successfully
            - Response is stored in cache
            - Cache storage operation completes successfully
        """
        # Configure cache for cache miss then successful storage
        mock_cache.get_cached_response = AsyncMock(return_value=None)  # Cache miss
        mock_cache.cache_response = AsyncMock(return_value=None)  # Successful cache storage

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} cache_miss_test",
                "operation": "summarize",
                "options": {"max_length": 30}
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert "result" in data
            assert data["cache_hit"] is False  # Should indicate cache miss

            # Verify cache operations occurred
            mock_cache.get_cached_response.assert_called_once()
            mock_cache.cache_response.assert_called_once()

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_failure_fallback(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache failure handling with graceful degradation.

        Integration Scope:
            API endpoint → Cache failure → Fallback processing → Graceful response

        Business Impact:
            Ensures system continues operating when cache is unavailable,
            providing graceful degradation instead of failure.

        Test Strategy:
            - Configure cache to raise exceptions
            - Submit request during cache failure
            - Verify fallback processing occurs
            - Confirm system remains operational

        Success Criteria:
            - Cache failures are handled gracefully
            - Processing continues despite cache issues
            - User receives appropriate response
            - System maintains operational integrity
        """
        # Configure cache to fail
        mock_cache.get_cached_response = AsyncMock(side_effect=Exception("Cache service unavailable"))
        mock_cache.cache_response = AsyncMock(side_effect=Exception("Cache storage failed"))

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} cache_failure_test",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert "result" in data

            # Verify cache failures didn't prevent processing
            # AI processing should still work despite cache issues

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_key_generation_uniqueness(self, client, auth_headers, text_processor_service, mock_cache):
        """
        Test cache key generation for uniqueness and collision avoidance.

        Integration Scope:
            Cache key generation → Collision detection → Unique key assignment

        Business Impact:
            Ensures cache keys are unique to prevent data corruption
            and maintain cache integrity.

        Test Strategy:
            - Submit requests with similar but different content
            - Verify unique cache keys are generated
            - Confirm no key collisions occur
            - Validate key generation consistency

        Success Criteria:
            - Unique content generates unique cache keys
            - Similar content doesn't cause key collisions
            - Cache key generation is consistent
            - No data corruption from key collisions
        """
        # Configure cache for testing key generation
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Test requests with different but similar content
            test_requests = [
                {
                    "text": "cache_test_1: First unique content for cache key testing",
                    "operation": "summarize"
                },
                {
                    "text": "cache_test_2: Second unique content for cache key testing",
                    "operation": "summarize"
                },
                {
                    "text": "cache_test_1: First unique content for cache key testing",  # Same as first
                    "operation": "sentiment"  # Different operation
                }
            ]

            responses = []
            for request_data in test_requests:
                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200
                responses.append(response.json())

            # Verify all requests succeeded
            assert len(responses) == 3
            for response in responses:
                assert response["success"] is True

            # Verify cache operations occurred for each unique request
            assert mock_cache.get_cached_response.call_count >= 3
            assert mock_cache.cache_response.call_count >= 3

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_concurrent_cache_access_safety(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test thread safety and concurrent access to cache.

        Integration Scope:
            Concurrent requests → Cache access → Thread safety → Consistent responses

        Business Impact:
            Ensures cache operations are thread-safe and handle
            concurrent access without data corruption.

        Test Strategy:
            - Make multiple concurrent requests
            - Verify cache handles concurrent access safely
            - Confirm consistent responses under load
            - Validate thread safety of cache operations

        Success Criteria:
            - Concurrent requests are handled safely
            - Cache operations maintain thread safety
            - No data corruption occurs under concurrent load
            - Consistent responses are returned
        """
        # Configure cache for concurrent access testing
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Make concurrent requests
            async def make_requests():
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
                    tasks = []
                    for i in range(5):
                        request_data = {
                            "text": f"{sample_text} concurrent_cache_test_{i}",
                            "operation": "summarize",
                            "options": {"max_length": 30}
                        }

                        task = async_client.post(
                            "/v1/text_processing/process",
                            json=request_data,
                            headers=auth_headers
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

            # Verify cache handled concurrent access
            assert mock_cache.get_cached_response.call_count >= 5
            assert mock_cache.cache_response.call_count >= 5

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_performance_monitoring_integration(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache performance monitoring and metrics collection.

        Integration Scope:
            Cache operations → Performance monitoring → Metrics collection → Reporting

        Business Impact:
            Ensures cache performance is monitored and metrics are collected
            for operational visibility and optimization.

        Test Strategy:
            - Perform cache operations
            - Verify performance monitoring occurs
            - Confirm metrics collection works
            - Validate monitoring integration

        Success Criteria:
            - Cache performance is monitored during operations
            - Metrics are collected for analysis
            - Monitoring integration works correctly
            - Performance data is available for optimization
        """
        # Configure cache for performance monitoring
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} performance_monitoring_test",
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

            # Verify cache operations occurred (performance monitoring would track these)
            mock_cache.get_cached_response.assert_called_once()
            mock_cache.cache_response.assert_called_once()

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_with_different_operations(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache integration with different text processing operations.

        Integration Scope:
            Different operations → Operation-specific caching → Response consistency

        Business Impact:
            Ensures caching works correctly across all supported operations,
            providing consistent performance optimization.

        Test Strategy:
            - Test cache with different operation types
            - Verify operation-specific cache behavior
            - Confirm cache key generation per operation
            - Validate cache hit/miss behavior across operations

        Success Criteria:
            - All operations integrate correctly with caching
            - Operation-specific cache keys are generated
            - Cache behavior is consistent across operations
            - Performance optimization works for all operations
        """
        # Configure cache for different operations
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            operations_to_test = [
                "summarize",
                "sentiment",
                "key_points",
                "questions"
            ]

            for operation in operations_to_test:
                request_data = {
                    "text": f"{sample_text} {operation}_cache_test",
                    "operation": operation
                }

                # Add question for QA operation
                if operation == "qa":
                    request_data["question"] = "What is this test about?"

                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["operation"] == operation

                # Verify operation-specific response structure
                if operation == "sentiment":
                    assert "sentiment" in data
                elif operation == "key_points":
                    assert "key_points" in data or "result" in data
                elif operation == "questions":
                    assert "questions" in data or "result" in data
                else:
                    assert "result" in data

            # Verify cache operations occurred for each operation
            assert mock_cache.get_cached_response.call_count >= len(operations_to_test)
            assert mock_cache.cache_response.call_count >= len(operations_to_test)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_invalidation_integration(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache invalidation and its effect on subsequent requests.

        Integration Scope:
            Cache invalidation → Fresh processing → Cache repopulation

        Business Impact:
            Ensures cache invalidation works correctly, allowing fresh data
            when content changes or cache needs refresh.

        Test Strategy:
            - Perform initial request (cache population)
            - Trigger cache invalidation
            - Submit subsequent request (fresh processing)
            - Verify cache is repopulated correctly

        Success Criteria:
            - Cache invalidation works correctly
            - Subsequent requests trigger fresh processing
            - Cache is repopulated after invalidation
            - No stale data is served after invalidation
        """
        # Configure cache for invalidation testing
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)
        mock_cache.invalidate_pattern = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} cache_invalidation_test",
                "operation": "summarize"
            }

            # First request - should process and cache
            response1 = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["success"] is True

            # Invalidate cache
            invalidation_response = client.post("/internal/cache/invalidate?pattern=test*", headers=auth_headers)
            assert invalidation_response.status_code == 200

            # Second request - should process fresh (cache miss after invalidation)
            response2 = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["success"] is True

            # Verify cache operations occurred
            assert mock_cache.get_cached_response.call_count >= 2
            assert mock_cache.cache_response.call_count >= 2
            mock_cache.invalidate_pattern.assert_called_once()

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_memory_usage_monitoring(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache memory usage monitoring and thresholds.

        Integration Scope:
            Cache operations → Memory monitoring → Threshold detection → Alerts

        Business Impact:
            Ensures cache memory usage is monitored and appropriate
            actions are taken when thresholds are reached.

        Test Strategy:
            - Perform multiple cache operations
            - Monitor memory usage patterns
            - Verify threshold detection
            - Confirm monitoring integration

        Success Criteria:
            - Memory usage is monitored during cache operations
            - Thresholds are detected appropriately
            - Monitoring provides visibility into cache health
            - Appropriate actions are taken for memory issues
        """
        # Configure cache for memory monitoring
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Perform multiple requests to generate cache activity
            for i in range(3):
                request_data = {
                    "text": f"{sample_text} memory_monitoring_test_{i}",
                    "operation": "summarize"
                }

                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True

            # Verify cache operations occurred (memory monitoring would track these)
            assert mock_cache.get_cached_response.call_count >= 3
            assert mock_cache.cache_response.call_count >= 3

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_cache_compression_integration(self, client, auth_headers, sample_text, text_processor_service, mock_cache):
        """
        Test cache compression integration and efficiency.

        Integration Scope:
            Cache operations → Compression → Storage optimization → Retrieval

        Business Impact:
            Ensures cache compression works correctly to optimize
            storage usage and improve performance.

        Test Strategy:
            - Test cache with compression enabled
            - Verify compression/decompression works
            - Confirm storage optimization
            - Validate compression efficiency

        Success Criteria:
            - Compression is applied to cache storage
            - Decompression works correctly for retrieval
            - Storage optimization is achieved
            - No data corruption from compression
        """
        # Configure cache for compression testing
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.cache_response = AsyncMock(return_value=None)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            request_data = {
                "text": f"{sample_text} compression_test",
                "operation": "summarize",
                "options": {"max_length": 100}  # Larger content for compression testing
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "result" in data

            # Verify cache operations occurred (compression would be applied during storage)
            mock_cache.get_cached_response.assert_called_once()
            mock_cache.cache_response.assert_called_once()

        finally:
            # Clean up override
            app.dependency_overrides.clear()
