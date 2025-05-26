import pytest
import sys
import os
from unittest.mock import AsyncMock, patch
import json

# Add the root directory to Python path so we can import app modules and shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.text_processor import TextProcessorService
from shared.models import TextProcessingRequest, ProcessingOperation, SentimentResult

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