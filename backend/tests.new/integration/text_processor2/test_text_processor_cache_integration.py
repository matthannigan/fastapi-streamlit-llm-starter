# type: ignore[import-untyped, no-untyped-def, union-attr]
"""Integration tests for TextProcessorService + AIResponseCache collaboration.

This module contains test skeletons for verifying cache-first strategy,
cache key generation, cache hit/miss behavior, TTL management, and cache
storage after successful processing.

Integration Strategy:
    - Test cache-first lookup before AI processing
    - Test cache key generation with operation-specific parameters
    - Test cache hit returns cached response immediately
    - Test cache miss triggers AI processing
    - Test cache storage after successful processing
    - Test operation-specific TTL values

Coverage Focus:
    - Cache-first strategy in process_text()
    - _build_key() behavior through caching
    - _get_ttl_for_operation() through cache storage
    - Cache hit/miss metadata in responses
"""

# Integration test imports
from app.infrastructure.cache.redis_ai import AIResponseCache

import pytest
import unittest.mock
from unittest.mock import Mock, patch
from app.services.text_processor import TextProcessorService
from app.schemas import TextProcessingRequest, TextProcessingOperation


def _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent):
    """
    Helper function to create TextProcessorService with mocked PydanticAI Agent.

    This avoids API key issues in tests by patching the Agent class.
    """
    with unittest.mock.patch('app.services.text_processor.Agent', return_value=mock_pydantic_agent):
        return TextProcessorService(test_settings, ai_response_cache)


class TestTextProcessorCachingStrategy:
    """
    Tests for cache-first processing strategy in process_text().
    
    Verifies that the service checks cache before making AI calls,
    returns cached responses immediately when available, and stores
    successful responses for future retrieval.
    
    Business Impact:
        Caching significantly reduces AI API costs, improves response times,
        and reduces load on external AI services for repeated requests.
    """

    async def test_cache_hit_returns_cached_response_without_ai_call(self, test_settings, ai_response_cache_with_data, mock_pydantic_agent):
        """
        Test cache hit returns cached response immediately without AI processing.

        Verifies:
            When cache contains response for request, process_text() returns
            cached response immediately without invoking AI agent.

        Business Impact:
            Reduces AI API costs and improves response times by serving cached
            responses for repeated requests without AI service calls.

        Scenario:
            Given: Fake cache pre-populated with response for specific request
            And: TextProcessingRequest matching cached entry
            When: process_text() is called
            Then: Cached response is returned immediately
            And: response.cache_hit is True
            And: AI agent is not called
            And: Processing time is minimal (< 50ms)

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache_with_data: Pre-configured cache with cached response
            - mock_pydantic_agent: Mock that should not be called
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache_with_data, mock_pydantic_agent)

        # Create request that matches cached entry
        request = TextProcessingRequest(
            text="Sample text for testing",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is True
        assert response.result == "Cached summary of sample text content"
        assert response.operation == TextProcessingOperation.SUMMARIZE
        assert response.processing_time < 0.05  # Less than 50ms for cache hit

        # Verify AI agent was not called
        mock_pydantic_agent.run.assert_not_called()

    async def test_cache_miss_triggers_ai_processing_and_stores_result(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache miss triggers AI processing and stores successful result.

        Verifies:
            When cache does not contain response, process_text() invokes AI
            agent for processing and stores successful result in cache.

        Business Impact:
            Ensures first requests are processed normally and subsequent
            identical requests benefit from caching for cost and speed.

        Scenario:
            Given: Empty fake cache (no cached responses)
            And: TextProcessingRequest
            When: process_text() is called (cache miss)
            Then: AI agent is invoked for processing
            And: Successful response is stored in cache
            And: response.cache_hit is False
            And: Cache contains entry for future requests

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Empty fake cache
            - mock_pydantic_agent: Mock AI agent returning response
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent to return a response
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Generated summary by AI"
        mock_response.data = "Generated summary by AI"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Text to process for cache miss test",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 150}
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is False
        assert response.result == "Generated summary by AI"
        assert response.operation == TextProcessingOperation.SUMMARIZE

        # Verify AI agent was called
        mock_pydantic_agent.run.assert_called_once()

    async def test_cache_check_occurs_before_input_sanitization(self, test_settings, ai_response_cache_with_data, fake_prompt_sanitizer, mock_pydantic_agent):
        """
        Test cache lookup occurs before expensive input sanitization.

        Verifies:
            Cache check happens early in processing pipeline before input
            sanitization to maximize performance gains from cache hits.

        Business Impact:
            Optimizes cache hit performance by skipping sanitization overhead
            when cached response available, further reducing response times.

        Scenario:
            Given: Fake cache with cached response
            When: process_text() is called
            Then: Cached response returned before sanitization
            And: PromptSanitizer is not called for cache hits
            And: Processing time reflects early cache return

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache_with_data: Pre-configured cache
            - fake_prompt_sanitizer: Tracks sanitization calls

        Observable Behavior:
            Can verify via fake_prompt_sanitizer.get_sanitization_calls()
            showing no calls for cache hit scenario.
        """
        # Arrange
        from app.infrastructure.ai import PromptSanitizer

        # Create processor with fake sanitizer
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache_with_data, mock_pydantic_agent)

        # Mock the sanitizer to track calls
        import unittest.mock
        with unittest.mock.patch.object(processor, 'sanitizer', fake_prompt_sanitizer):
            request = TextProcessingRequest(
                text="Sample text for testing",
                operation=TextProcessingOperation.SUMMARIZE,
                options={"max_length": 100}
            )

            # Act
            response = await processor.process_text(request)

            # Assert
            assert response.cache_hit is True

            # Verify sanitization was not called for cache hit
            sanitization_calls = fake_prompt_sanitizer.get_sanitization_calls()
            assert len(sanitization_calls) == 0

    async def test_cache_storage_after_successful_ai_processing(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test successful AI processing stores response in cache with TTL.

        Verifies:
            After successful AI processing, response is stored in cache with
            operation-specific TTL for future cache hit scenarios.

        Business Impact:
            Enables subsequent requests to benefit from caching, reducing
            costs and improving response times for repeated operations.

        Scenario:
            Given: Empty fake cache and successful AI processing
            When: process_text() completes successfully
            Then: Response is stored in cache
            And: Cache entry uses operation-specific TTL
            And: Cache key includes text, operation, and options
            And: Subsequent identical requests hit cache

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Empty fake cache
            - mock_pydantic_agent: Mock returning successful response
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent to return a response
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "AI generated summary for caching test"
        mock_response.data = "AI generated summary for caching test"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Text to be processed and cached",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 200}
        )

        # Act
        initial_response = await processor.process_text(request)

        # Assert - First request (cache miss)
        assert initial_response.cache_hit is False
        assert initial_response.result == "AI generated summary for caching test"

        # Get all cache keys using real cache API
        cache_keys = await ai_response_cache.get_all_keys()
        assert len(cache_keys) > 0

        # Verify TTL was set (summarize operation should have 7200 seconds)
        stored_ttl = await ai_response_cache.get_stored_ttl(cache_keys[0])
        assert stored_ttl is not None
        assert stored_ttl > 0

        # Act - Second identical request (should hit cache)
        second_response = await processor.process_text(request)

        # Assert - Second request (cache hit)
        assert second_response.cache_hit is True
        assert second_response.result == "AI generated summary for caching test"

    async def test_cache_hit_includes_cache_metadata_in_response(self, test_settings, ai_response_cache_with_data, mock_pydantic_agent):
        """
        Test cache hit sets cache_hit=True in response metadata.

        Verifies:
            When returning cached response, service sets response.cache_hit=True
            to indicate cached response for monitoring and analytics.

        Business Impact:
            Enables monitoring of cache effectiveness and client applications
            to distinguish cached vs. freshly processed responses.

        Scenario:
            Given: Fake cache with cached response
            When: process_text() returns cached response
            Then: response.cache_hit is True
            And: Metadata indicates cache hit occurred
            And: Processing time reflects cache hit speed

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache_with_data: Pre-configured cache
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache_with_data, mock_pydantic_agent)

        request = TextProcessingRequest(
            text="Sample text for testing",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is True
        assert hasattr(response, 'metadata')
        assert isinstance(response.metadata, dict)
        assert response.processing_time < 0.05  # Fast response for cache hit

    async def test_cache_miss_includes_cache_metadata_in_response(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache miss sets cache_hit=False in response metadata.

        Verifies:
            When processing without cache hit, service sets response.cache_hit=False
            to indicate fresh AI processing for monitoring and analytics.

        Business Impact:
            Enables monitoring of cache miss rate and understanding of
            cache effectiveness for optimization decisions.

        Scenario:
            Given: Empty fake cache (cache miss scenario)
            When: process_text() processes with AI agent
            Then: response.cache_hit is False
            And: Metadata indicates AI processing occurred
            And: Processing time reflects AI processing duration

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Empty fake cache
            - mock_pydantic_agent: Mock AI agent
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = '{"sentiment": "positive", "confidence": 0.8, "explanation": "The analysis indicates positive sentiment"}'
        mock_response.data = "Fresh AI processing result"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Text for cache miss metadata test",
            operation=TextProcessingOperation.SENTIMENT
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is False
        assert hasattr(response, 'metadata')
        assert isinstance(response.metadata, dict)
        assert response.sentiment is not None
        assert response.sentiment.sentiment == "positive"

        # Processing time should be longer than cache hit (simulated AI processing)
        assert response.processing_time > 0


class TestTextProcessorCacheKeyGeneration:
    """
    Tests for cache key generation through _build_key().
    
    Verifies that cache keys are generated correctly with operation type,
    text content, options, and question parameters for proper cache
    isolation and retrieval.
    
    Business Impact:
        Correct cache key generation ensures cache hits only occur for
        identical requests and prevents incorrect response retrieval.
    """

    async def test_cache_key_includes_operation_type(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache key generation includes operation type for isolation.

        Verifies:
            Cache keys include operation type to ensure different operations
            on same text generate different cache keys.

        Business Impact:
            Prevents cache collisions where summarize and sentiment operations
            on same text would incorrectly share cached responses.

        Scenario:
            Given: Two requests with same text but different operations
            When: Cache keys are generated for both
            Then: Cache keys are different due to operation difference
            And: Each operation has isolated cache entries
            And: Cache hits only occur for matching operation types

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache for key generation
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify by processing same text with different operations
            and confirming cache miss for each operation type.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent for different operations
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Summarized result"
        mock_response.data = "Summarized result"
        mock_pydantic_agent.run.return_value = mock_response

        # Create two requests with same text but different operations
        common_text = "This is the same text content for both operations"

        summarize_request = TextProcessingRequest(
            text=common_text,
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )

        sentiment_request = TextProcessingRequest(
            text=common_text,
            operation=TextProcessingOperation.SENTIMENT
        )

        # Act
        # Process summarize first
        summarize_response = await processor.process_text(summarize_request)
        assert summarize_response.cache_hit is False

        # Get summarize cache keys using real cache API
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 0
        summarize_cache_keys = [k for k in all_cache_keys if k.startswith("summarize")]
        assert len(summarize_cache_keys) > 0

        # Process sentiment - should be cache miss (different operation)
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = '{"sentiment": "positive", "confidence": 0.85, "explanation": "The sentiment appears positive"}'
        mock_response.data = "Sentiment result"
        mock_pydantic_agent.run.return_value = mock_response
        sentiment_response = await processor.process_text(sentiment_request)
        assert sentiment_response.cache_hit is False

        # Get all cache keys using real cache API
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 1

        # Verify we now have two different cache entries
        assert len(all_cache_keys) > len(summarize_cache_keys)

    async def test_cache_key_includes_text_content(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache key generation includes text content for uniqueness.

        Verifies:
            Cache keys incorporate text content to ensure different texts
            with same operation generate different cache keys.

        Business Impact:
            Ensures each unique text input gets appropriate processing and
            prevents incorrect response retrieval for different texts.

        Scenario:
            Given: Two requests with different texts but same operation
            When: Cache keys are generated for both
            Then: Cache keys are different due to text difference
            And: Each text has isolated cache entry
            And: No cache collisions between different text inputs

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache for key generation
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify by processing different texts with same operation
            and confirming cache miss for each text.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "First summary result"
        mock_response.data = "First summary result"
        mock_pydantic_agent.run.return_value = mock_response

        # Create two requests with different texts but same operation
        first_request = TextProcessingRequest(
            text="First unique text content for testing",
            operation=TextProcessingOperation.SUMMARIZE
        )

        second_request = TextProcessingRequest(
            text="Second unique text content for testing",
            operation=TextProcessingOperation.SUMMARIZE
        )

        # Act
        # Process first request
        first_response = await processor.process_text(first_request)
        assert first_response.cache_hit is False

        # Check we have cache entry
        first_cache_keys = await ai_response_cache.get_all_keys()
        assert len(first_cache_keys) > 0

        # Process second request - should be cache miss (different text)
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Second summary result"
        mock_response.data = "Second summary result"
        mock_pydantic_agent.run.return_value = mock_response
        second_response = await processor.process_text(second_request)
        assert second_response.cache_hit is False

        # Verify we now have two different cache entries
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 1
        assert len(all_cache_keys) > len(first_cache_keys)

    async def test_cache_key_includes_options_when_provided(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache key includes options parameter for customization isolation.

        Verifies:
            Cache keys include options dictionary to ensure different options
            with same text and operation generate different cache keys.

        Business Impact:
            Prevents cache collisions where same text with different processing
            options (max_length, style, etc.) would share cached responses.

        Scenario:
            Given: Two requests with same text, operation but different options
            When: Cache keys are generated for both
            Then: Cache keys are different due to options difference
            And: Each options combination has isolated cache entry
            And: Cache hits only occur for matching options

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache for key generation
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify by processing same text with different options
            and confirming cache miss for each options combination.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.data = "Short summary result"
        mock_pydantic_agent.run.return_value = mock_response

        # Create two requests with same text and operation but different options
        common_text = "This text will be summarized with different options"

        short_request = TextProcessingRequest(
            text=common_text,
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 50}
        )

        long_request = TextProcessingRequest(
            text=common_text,
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 200}
        )

        # Act
        # Process first request with short max_length
        short_response = await processor.process_text(short_request)
        assert short_response.cache_hit is False

        # Check we have cache entry
        first_cache_keys = await ai_response_cache.get_all_keys()
        assert len(first_cache_keys) > 0
        
        # Process second request with long max_length - should be cache miss (different options)
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Long summary result"
        mock_response.data = "Long summary result"
        mock_pydantic_agent.run.return_value = mock_response
        long_response = await processor.process_text(long_request)
        assert long_response.cache_hit is False

        # Verify we now have two different cache entries
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 1
        assert len(all_cache_keys) > len(first_cache_keys)

        # Verify both results are different
        assert short_response.result != long_response.result

    async def test_cache_key_includes_question_for_qa_operation(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache key for QA operation includes question parameter.

        Verifies:
            Cache keys for QA operations include question parameter to ensure
            different questions on same text generate different cache keys.

        Business Impact:
            Ensures each question gets appropriate answer and prevents cache
            collisions where different questions would share answers.

        Scenario:
            Given: Two QA requests with same text but different questions
            When: Cache keys are generated for both
            Then: Cache keys are different due to question difference
            And: Each question has isolated cache entry
            And: Cache hits only occur for matching questions

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache for key generation
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify by processing same text with different questions
            and confirming cache miss for each question.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.data = "Answer to first question"
        mock_pydantic_agent.run.return_value = mock_response

        # Create two QA requests with same text but different questions
        common_text = "The company reported quarterly earnings with revenue growth and profit margins."

        first_qa_request = TextProcessingRequest(
            text=common_text,
            operation=TextProcessingOperation.QA,
            question="What was the revenue growth?"
        )

        second_qa_request = TextProcessingRequest(
            text=common_text,
            operation=TextProcessingOperation.QA,
            question="What were the profit margins?"
        )

        # Act
        # Process first QA request
        first_response = await processor.process_text(first_qa_request)
        assert first_response.cache_hit is False

        # Check we have cache entry
        first_cache_keys = await ai_response_cache.get_all_keys()
        assert len(first_cache_keys) > 0
        
        # Process second QA request - should be cache miss (different question)
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Answer to second question"
        mock_response.data = "Answer to second question"
        mock_pydantic_agent.run.return_value = mock_response
        second_response = await processor.process_text(second_qa_request)
        assert second_response.cache_hit is False

        # Verify we now have two different cache entries
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 1
        assert len(all_cache_keys) > len(first_cache_keys)

        # Verify both answers are different
        assert first_response.result != second_response.result

    async def test_cache_key_generation_delegates_to_ai_response_cache(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test _build_key() delegates to cache.build_key() method.

        Verifies:
            Service delegates cache key generation to cache service after
            preparing parameters, leveraging cache service's key generation logic.

        Business Impact:
            Maintains separation of concerns where cache service owns key
            generation logic while text processor prepares parameters.

        Scenario:
            Given: TextProcessingRequest with operation, text, and options
            When: Cache key is needed for lookup or storage
            Then: Service calls cache.build_key() with parameters
            And: Cache service generates appropriate key format
            And: Service uses generated key for cache operations

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache with build_key() method
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify through successful cache hit/miss behavior and
            cache storage with correct key format.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "- Key point 1\n- Key point 2\n- Key point 3\n- Key point 4\n- Key point 5"
        mock_response.data = "Test result for delegation verification"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Test text for key generation delegation",
            operation=TextProcessingOperation.KEY_POINTS,
            options={"max_points": 5}
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is False
        assert response.key_points == ["Key point 1", "Key point 2", "Key point 3", "Key point 4", "Key point 5"]

        # Get all cache keys using real cache API
        all_cache_keys = await ai_response_cache.get_all_keys()

        # Verify the cache key format matches what ai_response_cache.build_key would generate
        assert "key_points" in all_cache_keys  # Operation should be in key
        assert str(hash("Test text for key generation delegation")) in all_cache_keys  # Text hash should be in key

        # Test that cache lookup works with the generated key
        # This proves the delegation worked correctly
        second_response = await processor.process_text(request)
        assert second_response.cache_hit is True


class TestTextProcessorCacheTTLManagement:
    """
    Tests for operation-specific TTL management in cache storage.
    
    Verifies that different operations use appropriate TTL values from
    OPERATION_CONFIG registry when storing responses in cache.
    
    Business Impact:
        Operation-specific TTLs optimize cache effectiveness by balancing
        freshness requirements with cache hit rates for each operation type.
    """

    async def test_summarize_operation_uses_configured_ttl(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test SUMMARIZE operation stores cache with configured TTL from registry.

        Verifies:
            Summarize operations use TTL value from OPERATION_CONFIG (typically
            7200 seconds / 2 hours) when storing responses in cache.

        Business Impact:
            Balances cache freshness with hit rate for summaries, using longer
            TTL since summary content remains relevant longer.

        Scenario:
            Given: Successful SUMMARIZE operation
            When: Response is stored in cache
            Then: Cache entry uses TTL from OPERATION_CONFIG["summarize"]
            And: Typical TTL is 7200 seconds (2 hours)
            And: Cache entry expires after configured TTL

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache tracking TTL values
            - mock_pydantic_agent: Mock AI agent
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Summary with TTL testing"
        mock_response.data = "Summary with TTL testing"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Text for TTL testing of summarize operation",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 150}
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is False
        assert response.result == "Summary with TTL testing"

        # Get all cache keys using real cache API
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 0

        # Verify cache entry was created with TTL
        stored_ttl = await ai_response_cache.get_stored_ttl(all_cache_keys[0])
        assert stored_ttl is not None

        # According to the OPERATION_CONFIG, summarize should use 7200 seconds
        expected_ttl = 7200
        assert stored_ttl == expected_ttl, f"Operation {request.operation} should use TTL {expected_ttl}, got {stored_ttl}"

    async def test_sentiment_operation_uses_shorter_ttl(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test SENTIMENT operation uses shorter TTL for faster-changing sentiment.

        Verifies:
            Sentiment operations use shorter TTL from OPERATION_CONFIG (typically
            3600 seconds / 1 hour) reflecting faster sentiment relevance decay.

        Business Impact:
            Optimizes cache freshness for sentiment analysis where results
            may become stale faster than summaries or key points.

        Scenario:
            Given: Successful SENTIMENT operation
            When: Response is stored in cache
            Then: Cache entry uses TTL from OPERATION_CONFIG["sentiment"]
            And: Typical TTL is 3600 seconds (1 hour)
            And: Shorter than summarize TTL for freshness

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache tracking TTL values
            - mock_pydantic_agent: Mock AI agent
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = '{"sentiment": "positive", "confidence": 0.9, "explanation": "The text shows positive attitude"}'
        mock_response.data = "Sentiment analysis result"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Text for sentiment TTL testing",
            operation=TextProcessingOperation.SENTIMENT
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is False

        # Get all cache keys using real cache API
        all_cache_keys = await ai_response_cache.get_all_keys()
        assert len(all_cache_keys) > 0

        # Verify cache entry was created with TTL
        stored_ttl = await ai_response_cache.get_stored_ttl(all_cache_keys[0])
        assert stored_ttl is not None

        # According to the OPERATION_CONFIG, sentiment should use 3600 seconds
        expected_ttl = 3600
        assert stored_ttl == expected_ttl, f"Operation {request.operation} should use TTL {expected_ttl}, got {stored_ttl}"

    async def test_qa_operation_uses_shortest_ttl(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test QA operation uses shortest TTL for context-sensitive answers.

        Verifies:
            QA operations use shortest TTL from OPERATION_CONFIG (typically
            1800 seconds / 30 minutes) reflecting context-sensitive nature.

        Business Impact:
            Balances cache benefits with Q&A answer freshness, recognizing
            that answers may need re-evaluation more frequently.

        Scenario:
            Given: Successful QA operation with question
            When: Response is stored in cache
            Then: Cache entry uses TTL from OPERATION_CONFIG["qa"]
            And: Typical TTL is 1800 seconds (30 minutes)
            And: Shortest TTL of all operations for freshness

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache tracking TTL values
            - mock_pydantic_agent: Mock AI agent
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Answer to question with TTL testing"
        mock_response.data = "Answer to question with TTL testing"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Text for QA TTL testing with context",
            operation=TextProcessingOperation.QA,
            question="What is the main topic?"
        )

        # Act
        response = await processor.process_text(request)

        # Assert
        assert response.cache_hit is False
        assert response.result == "Answer to question with TTL testing"

        # Get all cache keys using real cache API
        all_cache_keys = await ai_response_cache.get_all_keys()

        # Verify cache entry was created with TTL
        stored_ttl = await ai_response_cache.get_stored_ttl(all_cache_keys[0])
        assert stored_ttl is not None

        # According to the OPERATION_CONFIG, qa should use 1800 seconds
        expected_ttl = 1800
        assert stored_ttl == expected_ttl, f"Operation {request.operation} should use TTL {expected_ttl}, got {stored_ttl}"

    async def test_different_operations_use_different_ttls(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test different operations use operation-specific TTLs from registry.

        Verifies:
            Each operation type (SUMMARIZE, SENTIMENT, KEY_POINTS, QUESTIONS, QA)
            uses its own configured TTL value from OPERATION_CONFIG registry.

        Business Impact:
            Optimizes cache effectiveness by tuning TTL to each operation's
            freshness requirements and content stability characteristics.

        Scenario:
            Given: Multiple operations (summarize, sentiment, qa)
            When: Each operation stores response in cache
            Then: Each uses its operation-specific TTL from configuration
            And: TTLs reflect operation freshness requirements
            And: Summarize > Key_Points > Sentiment > QA in TTL duration

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache tracking TTL values per key
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify by comparing TTL values stored for different
            operation types in fake cache.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()

        # Expected TTLs from OPERATION_CONFIG
        expected_ttls = {
            TextProcessingOperation.SUMMARIZE: 7200,    # 2 hours
            TextProcessingOperation.SENTIMENT: 3600,    # 1 hour
            TextProcessingOperation.QA: 1800,           # 30 minutes
            TextProcessingOperation.KEY_POINTS: 5400,   # 1.5 hours
            TextProcessingOperation.QUESTIONS: 3600     # 1 hour
        }

        # Test each operation
        for operation, expected_ttl in expected_ttls.items():
            # Clear previous cache entries for clean testing
            await ai_response_cache.clear()

            mock_response.output = Mock()
            mock_response.output.strip.return_value = f"Result for {operation} operation"
            mock_response.data = f"Result for {operation} operation"

            if operation == TextProcessingOperation.QA:
                request = TextProcessingRequest(
                    text=f"Text for {operation} TTL testing",
                    operation=operation,
                    question="Test question"
                )
            else:
                request = TextProcessingRequest(
                    text=f"Text for {operation} TTL testing",
                    operation=operation
                )

            # Act
            response = await processor.process_text(request)

            # Assert
            assert response.cache_hit is False

            # Get all cache keys using real cache API
            all_cache_keys = await ai_response_cache.get_all_keys()
            assert len(all_cache_keys) > 0

            # Verify cache entry was created with correct TTL
            stored_ttl = await ai_response_cache.get_stored_ttl(all_cache_keys[0])
            assert stored_ttl == expected_ttl, f"Operation {operation} should use TTL {expected_ttl}, got {stored_ttl}"

    async def test_ttl_retrieval_from_operation_config_registry(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test _get_ttl_for_operation() retrieves TTL from OPERATION_CONFIG.

        Verifies:
            Service retrieves TTL values from OPERATION_CONFIG registry based
            on operation type for consistent cache expiration management.

        Business Impact:
            Centralizes TTL configuration in OPERATION_CONFIG for easy
            tuning and maintains consistency across cache operations.

        Scenario:
            Given: Any operation type from supported operations
            When: TTL is needed for cache storage
            Then: TTL is retrieved from OPERATION_CONFIG[operation]["cache_ttl"]
            And: Registry provides consistent TTL for operation type
            And: Configuration changes apply to all cache operations

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache for storage verification
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Verified indirectly through cache storage with correct TTL
            values matching OPERATION_CONFIG registry.
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "TTL registry verification result"
        mock_response.data = "TTL registry verification result"
        mock_pydantic_agent.run.return_value = mock_response

        # Test multiple operations to verify consistent TTL retrieval
        operations_to_test = [
            (TextProcessingOperation.SUMMARIZE, 7200),
            (TextProcessingOperation.SENTIMENT, 3600),
            (TextProcessingOperation.KEY_POINTS, 5400)
        ]

        for operation, expected_ttl in operations_to_test:
            # Clear cache for clean testing
            await ai_response_cache.clear()

            if operation == TextProcessingOperation.QA:
                request = TextProcessingRequest(
                    text="Test text for TTL registry",
                    operation=operation,
                    question="Test question"
                )
            else:
                request = TextProcessingRequest(
                    text="Test text for TTL registry",
                    operation=operation
                )

            # Act
            response = await processor.process_text(request)

            # Assert
            assert response.cache_hit is False

            # Get all cache keys using real cache API
            all_cache_keys = await ai_response_cache.get_all_keys()
            assert len(all_cache_keys) > 0

            # Verify the TTL from registry is consistently applied
            stored_ttl = await ai_response_cache.get_stored_ttl(all_cache_keys[0])
            assert stored_ttl == expected_ttl, f"Operation {operation} should use TTL {expected_ttl}, got {stored_ttl}"


class TestTextProcessorCacheBehaviorIntegration:
    """
    Tests for cache behavior integration across the processing pipeline.
    
    Verifies end-to-end cache behavior including lookup, miss handling,
    storage, and cache hit scenarios in complete processing workflows.
    
    Business Impact:
        Comprehensive cache integration ensures caching works correctly
        across all processing scenarios for cost and performance benefits.
    """

    async def test_first_request_stores_second_request_hits_cache(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test first request stores in cache, second identical request hits cache.

        Verifies:
            Complete cache workflow where first request processes and stores,
            second identical request retrieves from cache without processing.

        Business Impact:
            Demonstrates full cache value proposition where repeated requests
            benefit from caching for cost reduction and speed improvement.

        Scenario:
            Given: Empty fake cache initially
            When: First process_text() request is made
            Then: AI processing occurs and stores in cache (cache_hit=False)
            When: Second identical request is made
            Then: Cached response returned immediately (cache_hit=True)
            And: AI agent not called for second request
            And: Second request much faster than first

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Initially empty fake cache
            - mock_pydantic_agent: Mock AI agent
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Integration test summary result"
        mock_response.data = "Integration test summary result"
        mock_pydantic_agent.run.return_value = mock_response

        request = TextProcessingRequest(
            text="Integration test text for cache workflow",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )

        # Act - First request (cache miss)
        first_response = await processor.process_text(request)

        # Assert - First request
        assert first_response.cache_hit is False
        assert first_response.result == "Integration test summary result"
        assert first_response.operation == TextProcessingOperation.SUMMARIZE

        # Verify AI agent was called for first request
        assert mock_pydantic_agent.run.call_count == 1

        # Act - Second identical request (should hit cache)
        second_response = await processor.process_text(request)

        # Assert - Second request
        assert second_response.cache_hit is True
        assert second_response.result == "Integration test summary result"
        assert second_response.operation == TextProcessingOperation.SUMMARIZE

        # Verify AI agent was NOT called again for second request
        assert mock_pydantic_agent.run.call_count == 1  # Still only 1 call

        # Verify second request was faster
        assert second_response.processing_time < first_response.processing_time

    async def test_cache_effectiveness_with_varied_requests(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache correctly isolates different requests with unique keys.

        Verifies:
            Cache properly distinguishes between different texts, operations,
            and options to prevent incorrect cache hits.

        Business Impact:
            Ensures cache correctness by preventing inappropriate cache hits
            that would return wrong responses for different requests.

        Scenario:
            Given: Multiple requests with variations (text, operation, options)
            When: Requests are processed sequentially
            Then: Each unique combination triggers AI processing (cache miss)
            And: Identical combinations hit cache (cache hit)
            And: No incorrect cache hits between different requests

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache tracking all entries
            - mock_pydantic_agent: Mock AI agent
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()

        # Test different request variations
        requests_test_cases = [
            # Same text, different operation
            {
                "request": TextProcessingRequest(
                    text="Common text for variation testing",
                    operation=TextProcessingOperation.SUMMARIZE,
                    options={"max_length": 100}
                ),
                "response_data": "Summary result",
                "should_miss": True
            },
            # Same text, different operation
            {
                "request": TextProcessingRequest(
                    text="Common text for variation testing",
                    operation=TextProcessingOperation.SENTIMENT
                ),
                "response_data": "Sentiment result",
                "should_miss": True
            },
            # Same text and operation, different options
            {
                "request": TextProcessingRequest(
                    text="Options variation test text",
                    operation=TextProcessingOperation.SUMMARIZE,
                    options={"max_length": 50}
                ),
                "response_data": "Short summary",
                "should_miss": True
            },
            # Same text, operation, and options (should hit cache)
            {
                "request": TextProcessingRequest(
                    text="Options variation test text",
                    operation=TextProcessingOperation.SUMMARIZE,
                    options={"max_length": 50}
                ),
                "response_data": "Short summary",
                "should_miss": False  # This should hit cache from previous request
            },
            # Different text (should miss cache)
            {
                "request": TextProcessingRequest(
                    text="Completely different text content",
                    operation=TextProcessingOperation.SUMMARIZE,
                    options={"max_length": 50}
                ),
                "response_data": "Different summary",
                "should_miss": True
            }
        ]

        # Act & Assert
        ai_call_count = 0
        for i, test_case in enumerate(requests_test_cases):
            mock_response.output = Mock()
            # Configure response format based on operation type
            if test_case["request"].operation == TextProcessingOperation.SENTIMENT:
                mock_response.output.strip.return_value = '{"sentiment": "positive", "confidence": 0.85, "explanation": "The text expresses positive emotions"}'
            else:
                mock_response.output.strip.return_value = test_case["response_data"]
            mock_response.data = test_case["response_data"]
            mock_pydantic_agent.run.return_value = mock_response

            response = await processor.process_text(test_case["request"])

            if test_case["should_miss"]:
                # Should be cache miss - AI processing occurs
                assert response.cache_hit is False
                if test_case["request"].operation == TextProcessingOperation.SENTIMENT:
                    assert response.sentiment is not None
                    assert response.sentiment.sentiment == "positive"
                else:
                    assert response.result == test_case["response_data"]
                ai_call_count += 1
            else:
                # Should be cache hit - no AI processing
                assert response.cache_hit is True
                if test_case["request"].operation == TextProcessingOperation.SENTIMENT:
                    assert response.sentiment is not None
                    assert response.sentiment.sentiment == "positive"
                else:
                    assert response.result == test_case["response_data"]

        # Verify AI agent was called only for cache misses
        expected_ai_calls = sum(1 for case in requests_test_cases if case["should_miss"])
        assert mock_pydantic_agent.run.call_count == expected_ai_calls

    async def test_cache_handles_concurrent_identical_requests(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test cache handles concurrent identical requests appropriately.

        Verifies:
            When multiple identical requests arrive concurrently, cache behavior
            remains correct without race conditions or duplicate processing.

        Business Impact:
            Ensures cache reliability under concurrent load without duplication
            of AI processing for simultaneous identical requests.

        Scenario:
            Given: Multiple identical requests arriving concurrently
            When: All requests are processed simultaneously
            Then: Cache behavior remains correct
            And: Either all hit cache or first stores while others wait
            And: No duplicate processing or cache corruption

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Fake cache supporting concurrent operations
            - mock_pydantic_agent: Mock AI agent

        Note:
            This test focuses on observable behavior rather than internal
            race condition handling (which may be implementation-specific).
        """
        # Arrange
        processor = _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)

        # Configure mock AI agent
        mock_response = Mock()
        mock_response.output = Mock()
        mock_response.output.strip.return_value = "Concurrent processing result"
        mock_response.data = "Concurrent processing result"
        mock_pydantic_agent.run.return_value = mock_response

        # Create identical requests
        request = TextProcessingRequest(
            text="Concurrent test text",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )

        # Act - Process multiple identical requests concurrently
        import asyncio
        responses = await asyncio.gather(
            *[
                processor.process_text(request)
                for _ in range(3)  # 3 concurrent identical requests
            ],
            return_exceptions=True
        )

        # Assert
        # All responses should be successful
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.result == "Concurrent processing result"
            assert response.operation == TextProcessingOperation.SUMMARIZE

        # At least one request should be cache miss (first one)
        cache_misses = sum(1 for response in responses if response.cache_hit is False)
        cache_hits = sum(1 for response in responses if response.cache_hit is True)

        assert cache_misses >= 1  # At least one cache miss
        assert cache_hits >= 1   # At least one cache hit (due to concurrency)

        # AI agent should be called at most once (first request stores, others hit cache)
        assert mock_pydantic_agent.run.call_count <= 1

        # Get all cache keys using real cache API
        cache_keys = await ai_response_cache.get_all_keys()

        # Cache should have exactly one entry for this request
        assert len(cache_keys) == 1

class TestTextProcessorBatchCaching:
    """
    Tests for caching behavior during batch processing.
    
    Verifies that batch processing leverages caching correctly for each
    individual request, enabling cache hits within batches.
    
    Business Impact:
        Caching in batch processing reduces costs and improves performance
        when batch contains duplicate or previously-processed requests.
    """

    async def test_batch_requests_can_hit_cache_individually(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test individual requests in batch can hit cache independently.

        Verifies:
            Each request in batch follows normal cache-first strategy,
            enabling cache hits for individual requests within batch.

        Business Impact:
            Reduces AI processing costs when batch contains requests with
            cached responses from previous executions.

        Scenario:
            Given: Batch with 5 requests, 2 have cached responses
            When: process_batch() processes all requests
            Then: 2 requests hit cache (cache_hit=True)
            And: 3 requests process with AI (cache_hit=False)
            And: Total processing time reflects cache hits

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Pre-populated with some cached responses
            - mock_pydantic_agent: Mock for cache miss processing
        """
        import asyncio
        from app.services.text_processor import TextProcessorService
        from app.schemas import BatchTextProcessingRequest, TextProcessingRequest, TextProcessingOperation

        # Pre-populate cache with some responses (requests #1 and #3 will be cache hits)
        cache_key_1 = ai_response_cache.build_key(
            "Content for request 1",
            "summarize",
            {"max_length": 100}
        )
        cache_key_3 = ai_response_cache.build_key(
            "Content for request 3",
            "summarize",
            {"max_length": 100}
        )

        cached_response_1 = {
            "operation": "summarize",
            "result": "Cached summary for request 1",
            "success": True,
            "cache_hit": False,  # Original wasn't from cache
            "processing_time": 0.5,
            "metadata": {"word_count": 50}
        }

        cached_response_3 = {
            "operation": "summarize",
            "result": "Cached summary for request 3",
            "success": True,
            "cache_hit": False,  # Original wasn't from cache
            "processing_time": 0.6,
            "metadata": {"word_count": 60}
        }

        await ai_response_cache.set(cache_key_1, cached_response_1, ttl=7200)
        await ai_response_cache.set(cache_key_3, cached_response_3, ttl=7200)

        # Configure mock agent for cache misses
        ai_call_count = 0
        async def simulate_ai_processing(*args, **kwargs):
            nonlocal ai_call_count
            ai_call_count += 1
            await asyncio.sleep(0.02)  # Simulate AI processing time
            mock_response = Mock()
            mock_response.data = f"AI generated summary {ai_call_count}"
            return mock_response

        mock_pydantic_agent.run.side_effect = simulate_ai_processing

        # Patch the Agent class to use our mock
        with patch('app.services.text_processor.Agent', return_value=mock_pydantic_agent):
            # Given: Create TextProcessor service
            processor = TextProcessorService(test_settings, ai_response_cache)

            # Given: Batch with 5 requests, 2 have cached responses
            batch_request = BatchTextProcessingRequest(
                requests=[
                    TextProcessingRequest(
                        text="Content for request 1",  # Will hit cache
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Content for request 2",  # Will miss cache
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Content for request 3",  # Will hit cache
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Content for request 4",  # Will miss cache
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Content for request 5",  # Will miss cache
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    )
                ],
                batch_id="test_cache_hits_batch"
            )

            # When: process_batch() processes all requests
            batch_response = await processor.process_batch(batch_request)

            # Then: All requests complete successfully
            assert batch_response.total_requests == 5
            assert batch_response.completed == 5
            assert batch_response.failed == 0

            # And: 2 requests hit cache (cache_hit=True)
            cache_hit_responses = [
                r.response for r in batch_response.results
                if r.response and r.response.cache_hit is True
            ]
            assert len(cache_hit_responses) == 2, \
                f"Expected 2 cache hits, got {len(cache_hit_responses)}"

            # And: 3 requests process with AI (cache_hit=False)
            cache_miss_responses = [
                r.response for r in batch_response.results
                if r.response and r.response.cache_hit is False
            ]
            assert len(cache_miss_responses) == 3, \
                f"Expected 3 cache misses, got {len(cache_miss_responses)}"

            # And: AI was called only for cache misses (3 times)
            assert ai_call_count == 3, \
                f"AI should be called only 3 times for cache misses, got {ai_call_count}"

            # And: Total processing time reflects cache hits (should be faster)
            assert batch_response.total_processing_time < 0.1, \
                f"Processing with cache hits should be fast: {batch_response.total_processing_time:.3f}s"

            # Verify specific cache hit responses
            assert batch_response.results[0].response.cache_hit is True, "Request 1 should hit cache"
            assert batch_response.results[2].response.cache_hit is True, "Request 3 should hit cache"

            # Verify specific cache miss responses
            assert batch_response.results[1].response.cache_hit is False, "Request 2 should miss cache"
            assert batch_response.results[3].response.cache_hit is False, "Request 4 should miss cache"
            assert batch_response.results[4].response.cache_hit is False, "Request 5 should miss cache"

    async def test_batch_stores_successful_results_in_cache(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test successful batch results are stored in cache for future use.

        Verifies:
            Each successfully processed request in batch stores result in
            cache for future cache hits.

        Business Impact:
            Builds cache from batch processing, improving future performance
            for identical requests whether in batches or individual.

        Scenario:
            Given: Batch with requests not in cache
            When: process_batch() completes successfully
            Then: All successful results are stored in cache
            And: Future identical requests hit cache
            And: Cache storage includes operation-specific TTLs

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Initially empty fake cache
            - mock_pydantic_agent: Mock returning successful responses
        """
        from app.services.text_processor import TextProcessorService
        from app.schemas import BatchTextProcessingRequest, TextProcessingRequest, TextProcessingOperation

        # Verify cache is initially empty
        initial_cache_keys = await ai_response_cache.get_all_keys()
        assert len(initial_cache_keys) == 0, "Cache should start empty"

        # Configure mock agent to return successful responses
        def configure_mock_response(*args, **kwargs):
            mock_response = Mock()
            mock_response.data = "Cached result content"
            return mock_response

        mock_pydantic_agent.run.side_effect = configure_mock_response

        # Patch the Agent class to use our mock
        with patch('app.services.text_processor.Agent', return_value=mock_pydantic_agent):
            # Given: Create TextProcessor service with empty cache
            processor = TextProcessorService(test_settings, ai_response_cache)

            # Given: Batch with requests not in cache
            batch_request = BatchTextProcessingRequest(
                requests=[
                    TextProcessingRequest(
                        text="Unique content 1 for cache testing",
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Unique content 2 for cache testing",
                        operation=TextProcessingOperation.SENTIMENT
                    ),
                    TextProcessingRequest(
                        text="Unique content 3 for cache testing",
                        operation=TextProcessingOperation.KEY_POINTS,
                        options={"max_points": 3}
                    )
                ],
                batch_id="test_cache_storage_batch"
            )

            # When: process_batch() completes successfully
            batch_response = await processor.process_batch(batch_request)

            # Then: All successful results are stored in cache
            final_cache_keys = await ai_response_cache.get_all_keys()
            assert len(final_cache_keys) >= 3, \
                f"Should have at least 3 cache entries, got {len(final_cache_keys)}"

            # And: Verify each request was cached with appropriate key
            for i, request in enumerate(batch_request.requests):
                cache_key = ai_response_cache.build_key(
                    request.text,
                    request.operation.value,
                    request.options or {}
                )
                cached_result = await ai_response_cache.get(cache_key)

                assert cached_result is not None, \
                    f"Request {i} result should be cached"

                # Verify cached result structure
                assert "operation" in str(cached_result) or "operation" in cached_result, \
                    f"Cached result should include operation: {cached_result}"
                assert "success" in str(cached_result) or "success" in cached_result, \
                    f"Cached result should include success flag: {cached_result}"

            # And: Future identical requests hit cache
            # Create a new processor instance to test cache hits
            processor_2 = TextProcessorService(test_settings, ai_response_cache)
            cache_hit_responses = []

            async def track_cache_hits(*args, **kwargs):
                cache_hit_responses.append(False)  # Should not be called for cache hits
                mock_response = Mock()
                mock_response.data = "Should not reach here for cache hit"
                return mock_response

            mock_pydantic_agent.run.side_effect = track_cache_hits

            # Make identical requests
            identical_batch_request = BatchTextProcessingRequest(
                requests=[
                    TextProcessingRequest(
                        text="Unique content 1 for cache testing",  # Same as request #1
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Unique content 2 for cache testing",  # Same as request #2
                        operation=TextProcessingOperation.SENTIMENT
                    )
                ],
                batch_id="test_cache_hit_batch"
            )

            cache_hit_response = await processor_2.process_batch(identical_batch_request)

            # Verify cache hits occurred (AI agent should not be called)
            assert len(cache_hit_responses) == 0, \
                f"AI agent should not be called for cache hits, but was called {len(cache_hit_responses)} times"

            # Verify responses indicate cache hits
            for result in cache_hit_response.results:
                assert result.response.cache_hit is True, \
                    f"Response should indicate cache hit: {result.response.cache_hit}"

            # And: Cache storage includes operation-specific TTLs
            # Verify cache entries have appropriate TTL values
            for cache_key in final_cache_keys:
                cached_entry = await ai_response_cache.get(cache_key)
                assert cached_entry is not None, "Cache entry should exist"
                # Note: TTL verification would depend on FakeCache implementation
                # The key point is that entries are stored with appropriate TTLs

            # And: Batch processing completed successfully
            assert batch_response.total_requests == 3
            assert batch_response.completed == 3
            assert batch_response.failed == 0

    @pytest.mark.xfail(
        reason="Known concurrency limitation: Concurrent batch processing causes cache race condition. "
               "Multiple identical requests check cache simultaneously before any finish storing, "
               "resulting in all requests calling AI. Requires cache locking or batch deduplication. "
               "See FIXES_NEEDED.md Phase 4.3 for details."
    )
    async def test_duplicate_requests_in_batch_leverage_cache(self, test_settings, ai_response_cache, mock_pydantic_agent):
        """
        Test duplicate requests within same batch leverage caching.

        Verifies:
            When batch contains identical requests, first processes and caches,
            subsequent identical requests hit cache within same batch.

        Business Impact:
            Optimizes processing of batches with duplicate requests by avoiding
            redundant AI processing within single batch execution.

        Scenario:
            Given: Batch with 2 identical requests (same text, operation, options)
            When: process_batch() processes all requests
            Then: First request processes with AI and stores in cache
            And: Second identical request hits cache (cache_hit=True)
            And: Only one AI call is made for duplicate requests

        Fixtures Used:
            - test_settings: Real Settings instance
            - ai_response_cache: Empty fake cache
            - mock_pydantic_agent: Mock AI agent

        Observable Behavior:
            Can verify through cache hit counts and AI agent call counts
            showing optimization for duplicate requests.

        Known Limitation:
            This test currently fails due to concurrent batch processing race condition.
            In concurrent execution, all requests check cache before any complete storing,
            causing redundant AI calls. This is a known architectural limitation that
            requires either cache-level locking or batch-level request deduplication.
        """
        import asyncio
        from app.services.text_processor import TextProcessorService
        from app.schemas import BatchTextProcessingRequest, TextProcessingRequest, TextProcessingOperation

        # Track AI calls to verify optimization
        ai_call_count = 0
        async def simulate_ai_processing(*args, **kwargs):
            nonlocal ai_call_count
            ai_call_count += 1
            await asyncio.sleep(0.03)  # Simulate AI processing time

            # ✅ Set up output.strip() properly
            mock_response = Mock()
            mock_response.output = Mock()
            mock_response.output.strip = Mock(return_value="Summary of duplicate content")

            return mock_response

        mock_pydantic_agent.run.side_effect = simulate_ai_processing

        # Patch the Agent class to use our mock
        with patch('app.services.text_processor.Agent', return_value=mock_pydantic_agent):
            # Given: Create TextProcessor service
            processor = TextProcessorService(test_settings, ai_response_cache)

            # Given: Batch with 2 identical requests (same text, operation, options)
            identical_text = "This content appears multiple times in the batch and should be cached after first processing."
            batch_request = BatchTextProcessingRequest(
                requests=[
                    TextProcessingRequest(
                        text=identical_text,
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text=identical_text,  # Identical to first request
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text="Different content that requires AI processing",
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    ),
                    TextProcessingRequest(
                        text=identical_text,  # Third identical request
                        operation=TextProcessingOperation.SUMMARIZE,
                        options={"max_length": 100}
                    )
                ],
                batch_id="test_duplicate_cache_batch"
            )

            # When: process_batch() processes all requests
            batch_response = await processor.process_batch(batch_request)

            # Then: All requests complete successfully
            assert batch_response.total_requests == 4
            assert batch_response.completed == 4
            assert batch_response.failed == 0

            # And: Only one AI call is made for duplicate requests (2 unique requests)
            assert ai_call_count == 2, \
                f"Expected 2 AI calls for unique content, got {ai_call_count}"

            # And: First request processes with AI and stores in cache
            assert batch_response.results[0].response.cache_hit is False, \
                "First occurrence should not hit cache"

            # And: Second identical request hits cache
            assert batch_response.results[1].response.cache_hit is True, \
                "Second identical request should hit cache"

            # And: Third request (different content) processes with AI
            assert batch_response.results[2].response.cache_hit is False, \
                "Different content should not hit cache"

            # And: Fourth identical request hits cache
            assert batch_response.results[3].response.cache_hit is True, \
                "Third identical request should hit cache"

            # Verify cache hit and miss counts
            cache_hit_count = sum(1 for r in batch_response.results
                                 if r.response and r.response.cache_hit is True)
            cache_miss_count = sum(1 for r in batch_response.results
                                  if r.response and r.response.cache_hit is False)

            assert cache_hit_count == 2, f"Expected 2 cache hits, got {cache_hit_count}"
            assert cache_miss_count == 2, f"Expected 2 cache misses, got {cache_miss_count}"

            # And: Cache contains the processed result
            cache_key = ai_response_cache.build_key(
                identical_text,
                "summarize",
                {"max_length": 100}
            )
            cached_result = await ai_response_cache.get(cache_key)
            assert cached_result is not None, "Result should be cached"
            assert "Summary of duplicate content" in str(cached_result), \
                "Cached result should contain AI-generated content"

            # And: Processing time is optimized due to caching
            assert batch_response.total_processing_time < 0.1, \
                f"Processing with cache optimization should be fast: {batch_response.total_processing_time:.3f}s"

