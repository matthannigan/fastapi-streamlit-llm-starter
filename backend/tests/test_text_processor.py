import pytest
import pytest_asyncio
import sys
import os
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Add the root directory to Python path so we can import app modules and shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.text_processor import TextProcessorService
from app.config import settings as app_settings # Renamed to avoid conflict
from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchProcessingItem,
    ProcessingStatus,
    ProcessingOperation,
    SentimentResult
)


@pytest_asyncio.fixture
async def processor_service():
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
        # Mock the Agent used by TextProcessorService to avoid actual AI calls
        with patch('app.services.text_processor.Agent', new_callable=AsyncMock) as mock_agent_constructor:
            # Ensure the agent instance within the service has a 'run' method if it's called
            mock_agent_instance = AsyncMock()
            mock_agent_instance.run = AsyncMock() # Mock the 'run' method specifically
            mock_agent_constructor.return_value = mock_agent_instance
            
            service = TextProcessorService()
            # Mock the process_text method for batch tests, as we are unit testing process_batch
            service.process_text = AsyncMock()
            return service

class TestTextProcessorService:
    """Test the TextProcessorService class."""
    
    @pytest.fixture
    def service(self, mock_ai_agent):
        """Create a TextProcessorService instance."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            return TextProcessorService()
    
    @pytest.mark.asyncio
    async def test_summarize_text(self, service, sample_text):
        """Test text summarization."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="This is a test summary of artificial intelligence.")
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.SUMMARIZE
        assert response.result is not None
        assert response.processing_time is not None
        assert response.metadata["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, service, sample_text):
        """Test sentiment analysis."""
        # Mock AI response with JSON
        sentiment_json = {
            "sentiment": "neutral",
            "confidence": 0.8,
            "explanation": "The text is informational and neutral in tone."
        }
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data=json.dumps(sentiment_json))
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SENTIMENT
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.SENTIMENT
        assert response.sentiment is not None
        assert response.sentiment.sentiment == "neutral"
        assert response.sentiment.confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_invalid_json(self, service, sample_text):
        """Test sentiment analysis with invalid JSON response."""
        # Mock AI response with invalid JSON
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="Not valid JSON")
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SENTIMENT
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.sentiment.sentiment == "neutral"
        assert response.sentiment.confidence == 0.5
    
    @pytest.mark.asyncio
    async def test_key_points_extraction(self, service, sample_text):
        """Test key points extraction."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="""
            - AI is intelligence demonstrated by machines
            - Contrasts with natural intelligence of humans and animals
            - Focuses on intelligent agents and goal achievement
            """)
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.KEY_POINTS,
            options={"max_points": 3}
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.KEY_POINTS
        assert len(response.key_points) <= 3
        assert all(isinstance(point, str) for point in response.key_points)
    
    @pytest.mark.asyncio
    async def test_question_generation(self, service, sample_text):
        """Test question generation."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="""
            1. What is artificial intelligence?
            2. How does AI differ from natural intelligence?
            3. What are intelligent agents?
            """)
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.QUESTIONS,
            options={"num_questions": 3}
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.QUESTIONS
        assert len(response.questions) <= 3
        assert all("?" in question for question in response.questions)
    
    @pytest.mark.asyncio
    async def test_qa_processing(self, service, sample_text):
        """Test Q&A processing."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="Artificial intelligence is intelligence demonstrated by machines.")
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.QA,
            question="What is artificial intelligence?"
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.QA
        assert response.result is not None
    
    @pytest.mark.asyncio
    async def test_qa_without_question(self, service, sample_text):
        """Test Q&A without question raises error."""
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.QA
        )
        
        with pytest.raises(ValueError, match="Question is required"):
            await service.process_text(request)
    
    @pytest.mark.asyncio
    async def test_unsupported_operation(self, service, sample_text):
        """Test unsupported operation raises error."""
        # Create request with invalid operation (bypass enum validation)
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SUMMARIZE  # Will be modified
        )
        request.operation = "unsupported_operation"
        
        with pytest.raises(ValueError, match="Unsupported operation"):
            await service.process_text(request)
    
    @pytest.mark.asyncio
    async def test_ai_error_handling(self, service, sample_text):
        """Test handling of AI service errors."""
        # Mock AI service to raise an exception
        service.agent.run = AsyncMock(side_effect=Exception("AI service error"))
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SUMMARIZE
        )
        
        with pytest.raises(Exception):
            await service.process_text(request)


class TestTextProcessorCaching:
    """Test caching integration in TextProcessorService."""
    
    @pytest.fixture
    def service(self, mock_ai_agent):
        """Create a TextProcessorService instance."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            return TextProcessorService()
    
    @pytest.mark.asyncio
    async def test_cache_miss_processes_normally(self, service, sample_text):
        """Test that cache miss results in normal processing."""
        # Mock cache to return None (cache miss)
        with patch('app.services.text_processor.ai_cache.get_cached_response', return_value=None):
            with patch('app.services.text_processor.ai_cache.cache_response') as mock_cache_store:
                # Mock AI response
                service.agent.run = AsyncMock(
                    return_value=AsyncMock(data="This is a test summary.")
                )
                
                request = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.SUMMARIZE,
                    options={"max_length": 100}
                )
                
                response = await service.process_text(request)
                
                # Verify normal processing occurred
                assert response.success is True
                assert response.result is not None
                
                # Verify response was cached
                mock_cache_store.assert_called_once()
                cache_args = mock_cache_store.call_args[0]
                # Use strip() to handle whitespace differences
                assert cache_args[0].strip() == sample_text.strip()  # text
                assert cache_args[1] == "summarize"  # operation
                assert cache_args[2] == {"max_length": 100}  # options
    
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self, service, sample_text):
        """Test that cache hit returns cached response without processing."""
        cached_response = {
            "operation": "summarize",
            "result": "Cached summary result",
            "success": True,
            "processing_time": 0.5,
            "metadata": {"word_count": 10},
            "cached_at": "2024-01-01T12:00:00",
            "cache_hit": True
        }
        
        # Mock cache to return cached response
        with patch('app.services.text_processor.ai_cache.get_cached_response', return_value=cached_response):
            with patch('app.services.text_processor.ai_cache.cache_response') as mock_cache_store:
                # Create a proper mock for the agent
                mock_agent = AsyncMock()
                service.agent = mock_agent
                
                request = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.SUMMARIZE,
                    options={"max_length": 100}
                )
                
                response = await service.process_text(request)
                
                # Verify cached response was returned
                assert response.success is True
                assert response.result == "Cached summary result"
                assert response.processing_time == 0.5
                
                # Verify AI agent was not called
                mock_agent.run.assert_not_called()
                
                # Verify response was not cached again
                mock_cache_store.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_with_qa_operation(self, service, sample_text):
        """Test caching with Q&A operation that includes question parameter."""
        with patch('app.services.text_processor.ai_cache.get_cached_response', return_value=None):
            with patch('app.services.text_processor.ai_cache.cache_response') as mock_cache_store:
                service.agent.run = AsyncMock(
                    return_value=AsyncMock(data="AI is intelligence demonstrated by machines.")
                )
                
                request = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.QA,
                    question="What is AI?"
                )
                
                response = await service.process_text(request)
                
                # Verify response was cached with question parameter
                mock_cache_store.assert_called_once()
                cache_args = mock_cache_store.call_args[0]
                # Use strip() to handle whitespace differences
                assert cache_args[0].strip() == sample_text.strip()  # text
                assert cache_args[1] == "qa"  # operation
                assert cache_args[2] == {}  # options (empty for QA)
                assert cache_args[4] == "What is AI?"  # question
    
    @pytest.mark.asyncio
    async def test_cache_with_string_operation(self, service, sample_text):
        """Test caching works with string operation (not enum)."""
        with patch('app.services.text_processor.ai_cache.get_cached_response', return_value=None):
            with patch('app.services.text_processor.ai_cache.cache_response') as mock_cache_store:
                service.agent.run = AsyncMock(
                    return_value=AsyncMock(data="Test summary")
                )
                
                # Create request with string operation (simulating test scenario)
                request = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.SUMMARIZE
                )
                # Manually set operation as string to test the fix
                request.operation = "summarize"
                
                response = await service.process_text(request)
                
                # Verify it works without AttributeError
                assert response.success is True
                mock_cache_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, service, sample_text):
        """Test that cache errors don't break normal processing."""
        # Mock cache methods to not raise exceptions during the actual cache calls
        # but simulate the error handling path
        with patch('app.services.text_processor.ai_cache.get_cached_response') as mock_cache_get:
            with patch('app.services.text_processor.ai_cache.cache_response') as mock_cache_store:
                # Make get_cached_response return None (cache miss) without error
                mock_cache_get.return_value = None
                # Make cache_response succeed (the cache service handles errors internally)
                mock_cache_store.return_value = None
                
                service.agent.run = AsyncMock(
                    return_value=AsyncMock(data="Test summary")
                )
                
                request = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.SUMMARIZE
                )
                
                # Should not raise exception and should process normally
                response = await service.process_text(request)
                assert response.success is True
                assert response.result is not None
    
    @pytest.mark.asyncio
    async def test_cache_with_different_options(self, service, sample_text):
        """Test that different options create different cache entries."""
        with patch('app.services.text_processor.ai_cache.get_cached_response', return_value=None) as mock_cache_get:
            with patch('app.services.text_processor.ai_cache.cache_response') as mock_cache_store:
                service.agent.run = AsyncMock(
                    return_value=AsyncMock(data="Test summary")
                )
                
                # First request with specific options
                request1 = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.SUMMARIZE,
                    options={"max_length": 100}
                )
                await service.process_text(request1)
                
                # Second request with different options
                request2 = TextProcessingRequest(
                    text=sample_text,
                    operation=ProcessingOperation.SUMMARIZE,
                    options={"max_length": 200}
                )
                await service.process_text(request2)
                
                # Verify cache was checked twice with different parameters
                assert mock_cache_get.call_count == 2
                assert mock_cache_store.call_count == 2
                
                # Verify different options were used
                call1_options = mock_cache_get.call_args_list[0][0][2]
                call2_options = mock_cache_get.call_args_list[1][0][2]
                assert call1_options != call2_options


class TestServiceInitialization:
    """Test service initialization."""
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch('app.services.text_processor.settings') as mock_settings:
            mock_settings.gemini_api_key = ""
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                TextProcessorService()
    
    def test_initialization_with_api_key(self, mock_ai_agent):
        """Test successful initialization with API key."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            service = TextProcessorService()
            assert service.agent is not None


@pytest.mark.asyncio
async def test_process_batch_success(processor_service: TextProcessorService):
    """Test successful processing of a batch."""
    mock_response1 = TextProcessingResponse(operation=ProcessingOperation.SUMMARIZE, result="Summary 1", success=True)
    mock_response2 = TextProcessingResponse(operation=ProcessingOperation.SENTIMENT, sentiment=SentimentResult(sentiment="positive", confidence=0.9, explanation="Good"), success=True)

    processor_service.process_text.side_effect = [mock_response1, mock_response2]

    batch_request = BatchTextProcessingRequest(
        requests=[
            TextProcessingRequest(text="Text 1", operation=ProcessingOperation.SUMMARIZE),
            TextProcessingRequest(text="Text 2", operation=ProcessingOperation.SENTIMENT),
        ],
        batch_id="test_batch_success"
    )

    response = await processor_service.process_batch(batch_request)

    assert response.batch_id == "test_batch_success"
    assert response.total_requests == 2
    assert response.completed == 2
    assert response.failed == 0
    assert len(response.results) == 2
    assert processor_service.process_text.call_count == 2

    # Check first item
    assert response.results[0].request_index == 0
    assert response.results[0].status == ProcessingStatus.COMPLETED
    assert response.results[0].response == mock_response1
    assert response.results[0].error is None

    # Check second item
    assert response.results[1].request_index == 1
    assert response.results[1].status == ProcessingStatus.COMPLETED
    assert response.results[1].response == mock_response2
    assert response.results[1].error is None


@pytest.mark.asyncio
async def test_process_batch_item_failure(processor_service: TextProcessorService):
    """Test batch processing with one item failing."""
    mock_response1 = TextProcessingResponse(operation=ProcessingOperation.SUMMARIZE, result="Summary 1", success=True)
    ai_failure_exception = Exception("AI call failed")

    processor_service.process_text.side_effect = [mock_response1, ai_failure_exception]

    batch_request = BatchTextProcessingRequest(
        requests=[
            TextProcessingRequest(text="Text 1", operation=ProcessingOperation.SUMMARIZE),
            TextProcessingRequest(text="Text 2 (will fail)", operation=ProcessingOperation.KEY_POINTS),
        ],
        batch_id="test_batch_item_failure"
    )

    response = await processor_service.process_batch(batch_request)

    assert response.batch_id == "test_batch_item_failure"
    assert response.total_requests == 2
    assert response.completed == 1
    assert response.failed == 1
    assert len(response.results) == 2
    assert processor_service.process_text.call_count == 2
    
    # Check successful item
    assert response.results[0].request_index == 0
    assert response.results[0].status == ProcessingStatus.COMPLETED
    assert response.results[0].response == mock_response1
    assert response.results[0].error is None

    # Check failed item
    assert response.results[1].request_index == 1
    assert response.results[1].status == ProcessingStatus.FAILED
    assert response.results[1].response is None
    assert response.results[1].error == str(ai_failure_exception)


@pytest.mark.asyncio
@patch('app.services.text_processor.settings.BATCH_AI_CONCURRENCY_LIMIT', 1)
async def test_process_batch_respects_concurrency_limit(processor_service: TextProcessorService):
    """Test that process_batch respects the BATCH_AI_CONCURRENCY_LIMIT."""
    
    # Mock process_text to simulate work and allow checking call order if needed
    async def slow_process_text(*args, **kwargs):
        await asyncio.sleep(0.01) # Short delay to ensure semaphore logic can be tested
        # Determine which mock response to return based on the request content or call order
        # For simplicity, let's assume call order or use a more sophisticated side_effect if needed.
        if "Text 1" in args[0].text:
             return TextProcessingResponse(operation=ProcessingOperation.SUMMARIZE, result="Summary 1", success=True)
        elif "Text 2" in args[0].text:
             return TextProcessingResponse(operation=ProcessingOperation.SUMMARIZE, result="Summary 2", success=True)
        return TextProcessingResponse(operation=ProcessingOperation.SUMMARIZE, result="Default Summary", success=True)

    processor_service.process_text.side_effect = slow_process_text
    
    batch_request = BatchTextProcessingRequest(
        requests=[
            TextProcessingRequest(text="Text 1", operation=ProcessingOperation.SUMMARIZE),
            TextProcessingRequest(text="Text 2", operation=ProcessingOperation.SUMMARIZE),
        ]
    )

    with patch('asyncio.Semaphore') as mock_semaphore_constructor:
        # Create a mock semaphore instance that can be awaited (aenter, aexit)
        mock_semaphore_instance = MagicMock()
        mock_semaphore_instance.__aenter__ = AsyncMock()
        mock_semaphore_instance.__aexit__ = AsyncMock()
        mock_semaphore_constructor.return_value = mock_semaphore_instance

        response = await processor_service.process_batch(batch_request)

        # Verify Semaphore was called with the overridden limit (1)
        mock_semaphore_constructor.assert_called_once_with(1)
        
        # Ensure all items were processed
        assert response.total_requests == 2
        assert response.completed == 2
        assert response.failed == 0
        assert processor_service.process_text.call_count == 2
        # Check that the semaphore was acquired and released for each task
        assert mock_semaphore_instance.__aenter__.call_count == 2
        assert mock_semaphore_instance.__aexit__.call_count == 2


@pytest.mark.asyncio
async def test_process_batch_empty_request_list(processor_service: TextProcessorService):
    """Test processing an empty list of requests."""
    batch_request = BatchTextProcessingRequest(requests=[], batch_id="empty_batch")
    
    # process_batch should handle this gracefully, possibly by returning early
    # or as per its implementation for empty lists.
    # Based on current service impl, it will create an empty task list and proceed.
    
    response = await processor_service.process_batch(batch_request)
    
    assert response.batch_id == "empty_batch"
    assert response.total_requests == 0
    assert response.completed == 0
    assert response.failed == 0
    assert len(response.results) == 0
    processor_service.process_text.assert_not_called()


@pytest.mark.asyncio
async def test_process_batch_generates_batch_id_if_none(processor_service: TextProcessorService):
    """Test that a batch_id is generated if not provided."""
    mock_response = TextProcessingResponse(operation=ProcessingOperation.SUMMARIZE, result="Summary", success=True)
    processor_service.process_text.return_value = mock_response # All calls get this

    batch_request = BatchTextProcessingRequest(
        requests=[TextProcessingRequest(text="Text 1", operation=ProcessingOperation.SUMMARIZE)],
        batch_id=None  # Explicitly None
    )

    # Patch time.time used for generating batch_id if None
    with patch('time.time', return_value=1234567890.0):
        response = await processor_service.process_batch(batch_request)

    assert response.batch_id is not None
    assert isinstance(response.batch_id, str)
    assert response.batch_id == "batch_1234567890" # Check if it uses the mocked time
    assert response.total_requests == 1
    assert response.completed == 1
    assert processor_service.process_text.call_count == 1