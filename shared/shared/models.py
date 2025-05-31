"""Shared Pydantic models for the application."""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import re

class ProcessingOperation(str, Enum):
    """Available text processing operations."""
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"

class ProcessingStatus(str, Enum):
    """Processing status for batch operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TextProcessingRequest(BaseModel):
    """Request model for text processing operations."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Artificial intelligence is transforming how we work...",
                "operation": "summarize",
                "options": {"max_length": 100}
            }
        }
    )
    
    text: str = Field(..., min_length=10, max_length=10000, description="Text to process")
    operation: ProcessingOperation = Field(..., description="Type of processing to perform")
    question: Optional[str] = Field(None, description="Question for Q&A operation")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Operation-specific options")
    user_metadata: Optional[Dict[str, Any]] = Field(default=None, description="User context metadata")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Validate text content."""
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v, info):
        """Validate question for Q&A operations."""
        if info.data.get('operation') == ProcessingOperation.QA and not v:
            raise ValueError('Question is required for Q&A operation')
        return v

class BatchTextProcessingRequest(BaseModel):
    """Request model for batch text processing operations."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "requests": [
                    {
                        "text": "First text to process...",
                        "operation": "summarize"
                    },
                    {
                        "text": "Second text to analyze...",
                        "operation": "sentiment"
                    }
                ],
                "batch_id": "batch_001"
            }
        }
    )
    
    requests: List[TextProcessingRequest] = Field(..., min_length=1, max_length=200, description="List of processing requests")
    batch_id: Optional[str] = Field(None, description="Optional batch identifier")

class SentimentResult(BaseModel):
    """Result model for sentiment analysis."""
    sentiment: str = Field(..., description="Overall sentiment (positive/negative/neutral)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    explanation: str = Field(..., description="Brief explanation of the sentiment")

class TextProcessingResponse(BaseModel):
    """Response model for text processing results."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operation": "summarize",
                "success": True,
                "result": "This text discusses the impact of artificial intelligence...",
                "metadata": {"word_count": 150},
                "processing_time": 2.3
            }
        }
    )
    
    operation: ProcessingOperation
    success: bool = True
    result: Optional[str] = None
    sentiment: Optional[SentimentResult] = None
    key_points: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    cache_hit: Optional[bool] = Field(None, description="Whether this response came from cache")

class BatchProcessingItem(BaseModel):
    """Individual item in batch processing response."""
    request_index: int = Field(..., description="Index of the request in the batch")
    status: ProcessingStatus = Field(..., description="Processing status")
    response: Optional[TextProcessingResponse] = None
    error: Optional[str] = None

class BatchTextProcessingResponse(BaseModel):
    """Response model for batch text processing."""
    batch_id: Optional[str] = None
    total_requests: int = Field(..., description="Total number of requests in batch")
    completed: int = Field(0, description="Number of completed requests")
    failed: int = Field(0, description="Number of failed requests")
    results: List[BatchProcessingItem] = Field(..., description="Individual processing results")
    total_processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
    resilience_healthy: Optional[bool] = None

class ModelConfiguration(BaseModel):
    """Model configuration settings."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_name": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 0.9
            }
        }
    )
    
    model_name: str = Field(..., description="Name of the AI model")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Maximum tokens for response")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p sampling parameter")

class UsageStatistics(BaseModel):
    """Usage statistics model."""
    total_requests: int = Field(0, description="Total number of requests processed")
    successful_requests: int = Field(0, description="Number of successful requests")
    failed_requests: int = Field(0, description="Number of failed requests")
    average_processing_time: Optional[float] = Field(None, description="Average processing time in seconds")
    operations_count: Dict[str, int] = Field(default_factory=dict, description="Count by operation type")
    last_request_time: Optional[datetime] = Field(None, description="Timestamp of last request")

class APIKeyValidation(BaseModel):
    """API key validation model."""
    api_key: str = Field(..., min_length=10, description="API key to validate")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key_format(cls, v):
        """Basic API key format validation."""
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('API key contains invalid characters')
        return v

class ConfigurationUpdate(BaseModel):
    """Configuration update model."""
    ai_model: Optional[str] = Field(None, description="AI model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Maximum tokens")
    debug_mode: Optional[bool] = Field(None, description="Enable debug mode")

# Legacy models for backward compatibility
class ModelInfo(BaseModel):
    """Model information response."""
    current_model: str
    temperature: float
    status: str

class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    debug: bool 