import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    ProcessingOperation,
    SentimentResult,
    ErrorResponse,
    HealthResponse
)

class TestTextProcessingRequest:
    """Test TextProcessingRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = TextProcessingRequest(
            text="This is a test text for processing.",
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )
        
        assert request.text == "This is a test text for processing."
        assert request.operation == ProcessingOperation.SUMMARIZE
        assert request.options == {"max_length": 100}
        assert request.question is None
    
    def test_qa_request_with_question(self):
        """Test Q&A request with question."""
        request = TextProcessingRequest(
            text="Sample text",
            operation=ProcessingOperation.QA,
            question="What is this about?"
        )
        
        assert request.question == "What is this about?"
    
    def test_text_too_short(self):
        """Test validation fails for text too short."""
        with pytest.raises(ValidationError):
            TextProcessingRequest(
                text="Short",  # Less than 10 characters
                operation=ProcessingOperation.SUMMARIZE
            )
    
    def test_text_too_long(self):
        """Test validation fails for text too long."""
        long_text = "A" * 10001  # More than 10000 characters
        with pytest.raises(ValidationError):
            TextProcessingRequest(
                text=long_text,
                operation=ProcessingOperation.SUMMARIZE
            )
    
    def test_invalid_operation(self):
        """Test validation fails for invalid operation."""
        with pytest.raises(ValidationError):
            TextProcessingRequest(
                text="Valid text here",
                operation="invalid_operation"
            )

class TestTextProcessingResponse:
    """Test TextProcessingResponse model."""
    
    def test_basic_response(self):
        """Test basic response creation."""
        response = TextProcessingResponse(
            operation=ProcessingOperation.SUMMARIZE,
            result="This is a summary."
        )
        
        assert response.operation == ProcessingOperation.SUMMARIZE
        assert response.success is True
        assert response.result == "This is a summary."
        assert isinstance(response.timestamp, datetime)
    
    def test_sentiment_response(self):
        """Test sentiment analysis response."""
        sentiment = SentimentResult(
            sentiment="positive",
            confidence=0.9,
            explanation="The text has a positive tone."
        )
        
        response = TextProcessingResponse(
            operation=ProcessingOperation.SENTIMENT,
            sentiment=sentiment
        )
        
        assert response.sentiment.sentiment == "positive"
        assert response.sentiment.confidence == 0.9
    
    def test_key_points_response(self):
        """Test key points response."""
        response = TextProcessingResponse(
            operation=ProcessingOperation.KEY_POINTS,
            key_points=["Point 1", "Point 2", "Point 3"]
        )
        
        assert len(response.key_points) == 3
        assert "Point 1" in response.key_points
    
    def test_questions_response(self):
        """Test questions response."""
        response = TextProcessingResponse(
            operation=ProcessingOperation.QUESTIONS,
            questions=["Question 1?", "Question 2?"]
        )
        
        assert len(response.questions) == 2
        assert all("?" in q for q in response.questions)

class TestSentimentResult:
    """Test SentimentResult model."""
    
    def test_valid_sentiment(self):
        """Test valid sentiment result."""
        sentiment = SentimentResult(
            sentiment="positive",
            confidence=0.85,
            explanation="Text expresses positive emotions."
        )
        
        assert sentiment.sentiment == "positive"
        assert sentiment.confidence == 0.85
    
    def test_confidence_bounds(self):
        """Test confidence score bounds validation."""
        # Test valid bounds
        SentimentResult(sentiment="neutral", confidence=0.0, explanation="Test")
        SentimentResult(sentiment="neutral", confidence=1.0, explanation="Test")
        
        # Test invalid bounds
        with pytest.raises(ValidationError):
            SentimentResult(sentiment="neutral", confidence=-0.1, explanation="Test")
        
        with pytest.raises(ValidationError):
            SentimentResult(sentiment="neutral", confidence=1.1, explanation="Test")

class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_basic_error(self):
        """Test basic error response."""
        error = ErrorResponse(
            error="Something went wrong",
            error_code="PROCESSING_ERROR"
        )
        
        assert error.success is False
        assert error.error == "Something went wrong"
        assert error.error_code == "PROCESSING_ERROR"
        assert isinstance(error.timestamp, datetime)
    
    def test_error_with_details(self):
        """Test error with additional details."""
        error = ErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"field": "text", "issue": "too short"}
        )
        
        assert error.details["field"] == "text"

class TestHealthResponse:
    """Test HealthResponse model."""
    
    def test_healthy_response(self):
        """Test healthy response."""
        health = HealthResponse(
            ai_model_available=True
        )
        
        assert health.status == "healthy"
        assert health.ai_model_available is True
        assert health.version == "1.0.0"
    
    def test_unhealthy_response(self):
        """Test unhealthy response."""
        health = HealthResponse(
            status="unhealthy",
            ai_model_available=False
        )
        
        assert health.status == "unhealthy"
        assert health.ai_model_available is False

class TestProcessingOperation:
    """Test ProcessingOperation enum."""
    
    def test_all_operations(self):
        """Test all operation values are valid."""
        operations = [
            ProcessingOperation.SUMMARIZE,
            ProcessingOperation.SENTIMENT,
            ProcessingOperation.KEY_POINTS,
            ProcessingOperation.QUESTIONS,
            ProcessingOperation.QA
        ]
        
        assert len(operations) == 5
        assert ProcessingOperation.SUMMARIZE == "summarize"
        assert ProcessingOperation.SENTIMENT == "sentiment"
        assert ProcessingOperation.KEY_POINTS == "key_points"
        assert ProcessingOperation.QUESTIONS == "questions"
        assert ProcessingOperation.QA == "qa" 