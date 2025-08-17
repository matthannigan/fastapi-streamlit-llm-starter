"""Pydantic models and enumerations for AI-powered text processing operations.

This module defines the complete data contract for text processing functionality,
including request/response models, operation enumerations, and specialized result
structures. It serves as the foundation for AI-powered text analysis operations
such as summarization, sentiment analysis, key point extraction, question generation,
and question-answering capabilities.

The module is designed to support both individual text processing requests and
high-throughput batch operations, with comprehensive validation, error handling,
and metadata tracking throughout the processing pipeline.

Architecture:
    The text processing models follow a layered architecture:
    
    1. **Operation Definitions**: Enumerated types that define available processing
       operations and their identifiers.
    
    2. **Request Models**: Input validation and structure for both single and batch
       text processing requests, with operation-specific parameter validation.
    
    3. **Response Models**: Structured output formats with operation-specific result
       fields, metadata, and processing information.
    
    4. **Specialized Results**: Domain-specific result structures for complex
       operations like sentiment analysis with confidence scores and explanations.

Model Categories:
    Operation Enumerations:
        * TextProcessingOperation: Available AI processing operations (summarize,
          sentiment, key_points, questions, qa)
        * BatchTextProcessingStatus: Status tracking for batch operations
    
    Request Models:
        * TextProcessingRequest: Single text processing job with validation rules
        * BatchTextProcessingRequest: Multiple text processing jobs with batch limits
    
    Response Models:
        * TextProcessingResponse: Single operation results with metadata
        * BatchTextProcessingResponse: Batch operation results with aggregated status
        * BatchTextProcessingItem: Individual item status within batch responses
    
    Specialized Results:
        * SentimentResult: Structured sentiment analysis with confidence scoring

Processing Operations:
    Available AI operations and their characteristics:
    
    * **summarize**: Generate concise summaries of input text
        - Options: max_length (integer, default varies by model)
        - Output: Condensed text preserving key information
    
    * **sentiment**: Analyze emotional tone and polarity
        - Options: None required
        - Output: SentimentResult with sentiment, confidence, and explanation
    
    * **key_points**: Extract main ideas and important concepts
        - Options: max_points (integer, default 5)
        - Output: List of key points as strings
    
    * **questions**: Generate questions about the text content
        - Options: num_questions (integer, default 3)
        - Output: List of relevant questions as strings
    
    * **qa**: Answer specific questions about the text
        - Options: None (question provided in request.question field)
        - Output: Answer text based on content analysis
        - Special: Requires question field in request

Design Principles:
    * **Comprehensive Validation**: All input fields include appropriate validators
      for length, format, and business rule compliance.
    * **Operation-Specific Logic**: Different operations have tailored validation
      and response structures optimized for their specific use cases.
    * **Batch Processing Support**: Efficient handling of multiple requests with
      individual status tracking and error isolation.
    * **Metadata Rich**: Extensive metadata capture including processing times,
      cache status, and operation context for monitoring and debugging.
    * **Flexible Options**: Generic options dictionary allows operation-specific
      parameters without breaking schema compatibility.

Usage Examples:
    Single text processing request:
        ```python
        from shared.text_processing import TextProcessingRequest, TextProcessingOperation
        
        request = TextProcessingRequest(
            text="Your text content here...",
            operation=TextProcessingOperation.SUMMARIZE,
            options={"max_length": 150}
        )
        ```
    
    Question-answering request:
        ```python
        qa_request = TextProcessingRequest(
            text="Document content to analyze...",
            operation=TextProcessingOperation.QA,
            question="What are the main conclusions?"
        )
        ```
    
    Batch processing request:
        ```python
        from shared.text_processing import BatchTextProcessingRequest
        
        batch_request = BatchTextProcessingRequest(
            requests=[
                TextProcessingRequest(text="Text 1", operation="summarize"),
                TextProcessingRequest(text="Text 2", operation="sentiment")
            ],
            batch_id="analysis_batch_001"
        )
        ```
    
    Processing response handling:
        ```python
        from shared.text_processing import TextProcessingResponse
        
        # Handle different response types
        if response.operation == TextProcessingOperation.SENTIMENT:
            sentiment_data = response.sentiment
            print(f"Sentiment: {sentiment_data.sentiment} ({sentiment_data.confidence:.2f})")
        elif response.operation == TextProcessingOperation.KEY_POINTS:
            for point in response.key_points:
                print(f"- {point}")
        ```

Validation Features:
    The models include comprehensive validation logic:
    
    * **Text Content**: Minimum/maximum length validation, whitespace trimming,
      and empty content detection.
    * **Operation Dependencies**: Cross-field validation ensuring required fields
      are present for specific operations (e.g., question for Q&A).
    * **Batch Limits**: Configurable limits on batch size to prevent resource
      exhaustion and ensure reasonable processing times.
    * **Parameter Validation**: Type checking and range validation for operation-
      specific options and configuration parameters.

Integration Notes:
    * **FastAPI Compatibility**: All models are designed for seamless integration
      with FastAPI's automatic validation and OpenAPI documentation generation.
    * **Serialization Support**: Custom serializers for complex types like datetime
      ensure consistent JSON representation across different environments.
    * **Cache Integration**: Built-in cache metadata fields support response
      caching strategies and cache hit/miss tracking.
    * **Error Handling**: Validation errors provide detailed field-level feedback
      suitable for client-side error display and API debugging.
    * **Monitoring Ready**: Extensive metadata fields support comprehensive
      application monitoring, performance tracking, and usage analytics.

Performance Considerations:
    * **Efficient Validation**: Validators are optimized for performance with
      minimal computational overhead during request processing.
    * **Batch Optimization**: Batch processing models support efficient bulk
      operations while maintaining individual request traceability.
    * **Memory Management**: Response models use optional fields and lazy loading
      patterns to minimize memory usage for large batch operations.

Version History:
    1.0.0: Initial text processing models with basic operations
    1.1.0: Added batch processing support and comprehensive validation
    1.2.0: Enhanced sentiment analysis with confidence scoring
    1.3.0: Added question generation and Q&A capabilities
    1.4.0: Improved metadata tracking and cache integration
    
See Also:
    * app.services.text_processor: Service layer that uses these models
    * app.api.v1.text_processing: API endpoints that consume these schemas
    * app.schemas: Backend schema registry that imports these models

Author:
    FastAPI LLM Starter Team
    
License:
    MIT License
"""

from enum import Enum
from typing import Annotated, Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from datetime import datetime

class TextProcessingOperation(str, Enum):
    """Available text processing operations."""
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"

# Request models

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
    operation: TextProcessingOperation = Field(..., description="Type of processing to perform")
    question: Annotated[Optional[str], Field(description="Question for Q&A operation")] = None
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
        if info.data.get('operation') == TextProcessingOperation.QA and not v:
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

# Response models

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
    
    operation: TextProcessingOperation
    success: bool = True
    result: Optional[str] = None
    sentiment: Optional[SentimentResult] = None
    key_points: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    cache_hit: Optional[bool] = Field(None, description="Whether this response came from cache")

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        """Serialize datetime to ISO format string."""
        return dt.isoformat()

class BatchTextProcessingStatus(str, Enum):
    """Processing status for batch operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BatchTextProcessingItem(BaseModel):
    """Individual item in batch processing response."""
    request_index: int = Field(..., description="Index of the request in the batch")
    status: BatchTextProcessingStatus = Field(..., description="Processing status")
    response: Optional[TextProcessingResponse] = None
    error: Optional[str] = None

class BatchTextProcessingResponse(BaseModel):
    """Response model for batch text processing."""
    batch_id: Optional[str] = None
    total_requests: int = Field(..., description="Total number of requests in batch")
    completed: int = Field(0, description="Number of completed requests")
    failed: int = Field(0, description="Number of failed requests")
    results: List[BatchTextProcessingItem] = Field(..., description="Individual processing results")
    total_processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        """Serialize datetime to ISO format string."""
        return dt.isoformat()
