---
sidebar_label: text_processing
---

# Text Processing Schema Definitions Module

  file_path: `backend/app/schemas/text_processing.py`

This module defines the comprehensive data contract for AI-powered text processing functionality,
providing type-safe schemas for all text analysis operations including summarization, sentiment
analysis, key point extraction, question generation, and question-answering capabilities.

## Module Architecture

The text processing schemas are designed with cross-service compatibility and comprehensive
validation in mind:

### Schema Integration Strategy
- **Shared Model Re-exports**: Schemas are re-exported from the shared.models package to
  ensure consistent data contracts between FastAPI backend and Streamlit frontend
- **Type Safety**: Full type annotations and Pydantic validation for all operations
- **API Documentation**: Rich schema descriptions for automatic OpenAPI generation
- **Validation**: Comprehensive input validation with clear error messages

### Available Schema Categories

#### Operation Management
- **TextProcessingOperation**: Enumeration of available AI operations with clear naming
- **BatchTextProcessingStatus**: Comprehensive status tracking for batch operations

#### Request Models
- **TextProcessingRequest**: Single operation request with optional parameters and validation
- **BatchTextProcessingRequest**: Multi-operation batch processing with concurrency limits

#### Response Models  
- **TextProcessingResponse**: Operation results with metadata and performance tracking
- **BatchTextProcessingResponse**: Batch results with aggregated status and individual tracking
- **BatchTextProcessingItem**: Individual batch item status within batch responses

#### Specialized Results
- **SentimentResult**: Structured sentiment analysis with confidence scoring and polarity

## Text Processing Operations

### Core AI Operations
The schema supports the following AI-powered text analysis operations:

#### Summarization (`summarize`)
- **Purpose**: Generate concise summaries preserving key information
- **Parameters**: `max_length` (optional) - maximum summary length in words
- **Use Cases**: Document summarization, content preview, executive summaries

#### Sentiment Analysis (`sentiment`)
- **Purpose**: Analyze emotional tone and polarity of text
- **Returns**: `SentimentResult` with polarity score and confidence
- **Use Cases**: Customer feedback analysis, social media monitoring, review analysis

#### Key Point Extraction (`key_points`)
- **Purpose**: Extract main ideas and important concepts
- **Parameters**: `max_points` (optional) - maximum number of key points
- **Use Cases**: Meeting notes, research paper analysis, content analysis

#### Question Generation (`questions`)
- **Purpose**: Generate thoughtful questions about text content
- **Parameters**: `max_questions` (optional) - maximum number of questions
- **Use Cases**: Educational content, comprehension testing, interview preparation

#### Question Answering (`qa`)
- **Purpose**: Answer specific questions based on provided text context
- **Required**: `question` parameter with specific question text
- **Use Cases**: Document Q&A, knowledge extraction, automated support

## Schema Usage Patterns

### Single Operation Processing
```python
from app.schemas.text_processing import TextProcessingRequest, TextProcessingOperation

# Basic summarization request
summary_request = TextProcessingRequest(
    text="Long document content to be summarized...",
    operation=TextProcessingOperation.SUMMARIZE,
    options={"max_length": 150}
)

# Sentiment analysis request
sentiment_request = TextProcessingRequest(
    text="Customer feedback text to analyze sentiment...",
    operation=TextProcessingOperation.SENTIMENT
)

# Question-answering request with required question parameter
qa_request = TextProcessingRequest(
    text="Document content to analyze for answers...",
    operation=TextProcessingOperation.QA,
    question="What are the main conclusions from this analysis?"
)
```

### Batch Processing Operations
```python
from app.schemas.text_processing import (
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchTextProcessingStatus
)

# Batch request with multiple operations
batch_request = BatchTextProcessingRequest(
    requests=[
        TextProcessingRequest(text="Document 1", operation="summarize"),
        TextProcessingRequest(text="Review 1", operation="sentiment"),
        TextProcessingRequest(text="Article 1", operation="key_points")
    ],
    batch_id="analysis_batch_20250112_001"
)

# Batch status tracking
batch_response = BatchTextProcessingResponse(
    batch_id="analysis_batch_20250112_001",
    status=BatchTextProcessingStatus.IN_PROGRESS,
    total_items=3,
    completed_items=1,
    failed_items=0,
    results=[
        BatchTextProcessingItem(
            request_index=0,
            status="completed",
            result=TextProcessingResponse(...)
        )
    ]
)
```

### Advanced Configuration Examples
```python
# Customized key point extraction
key_points_request = TextProcessingRequest(
    text="Research paper content...",
    operation="key_points",
    options={
        "max_points": 5,
        "include_supporting_evidence": True,
        "focus_area": "methodology"
    }
)

# Question generation with constraints
questions_request = TextProcessingRequest(
    text="Educational content...",
    operation="questions",
    options={
        "max_questions": 10,
        "difficulty_level": "intermediate",
        "question_types": ["multiple_choice", "short_answer"]
    }
)
```

## Response Structure and Metadata

### Single Operation Responses
```python
# Example TextProcessingResponse structure
{
    "operation": "summarize",
    "result": "Generated summary text...",
    "metadata": {
        "processing_time_ms": 1250,
        "model_used": "gemini-2.0-flash-exp", 
        "cache_hit": False,
        "confidence_score": 0.95
    },
    "timestamp": "2025-01-12T10:30:45.123456Z"
}
```

### Specialized Result Types
```python
# SentimentResult for sentiment analysis
{
    "polarity": "positive",
    "confidence": 0.87,
    "scores": {
        "positive": 0.87,
        "negative": 0.08,
        "neutral": 0.05
    },
    "dominant_emotions": ["joy", "satisfaction"]
}
```

## Validation and Error Handling

### Input Validation
- **Text Content**: Non-empty text validation with length limits
- **Operation Types**: Enum validation for supported operations
- **Required Parameters**: Validation of operation-specific required fields
- **Optional Parameters**: Type validation for optional configuration

### Error Response Integration
```python
# Validation errors integrate with ErrorResponse schema
{
    "success": False,
    "error": "Question is required for Q&A operation",
    "error_code": "VALIDATION_ERROR",
    "details": {
        "operation": "qa",
        "missing_field": "question"
    }
}
```

## Performance and Monitoring

### Request Tracking
- **Unique Request IDs**: Automatic generation for operation correlation
- **Processing Metrics**: Response time, cache hit rates, model performance
- **Batch Analytics**: Aggregated performance across batch operations
- **Error Correlation**: Structured error tracking for failure analysis

### Caching Integration
- **Cache Key Generation**: Automatic cache key generation based on content and parameters
- **Cache Metadata**: Cache hit/miss tracking in response metadata
- **TTL Management**: Configurable cache expiration for different operation types

## Cross-Service Compatibility

### Shared Model Architecture
The schemas are designed for seamless integration across service boundaries:

- **FastAPI Backend**: Server-side validation and response generation
- **Streamlit Frontend**: Client-side type checking and UI generation
- **Shared Validation**: Consistent validation rules across all services
- **API Documentation**: Synchronized OpenAPI documentation generation

### Type Safety Guarantees
- **Compile-Time Checks**: Full type checking in development environments
- **Runtime Validation**: Pydantic validation with clear error messages
- **Schema Evolution**: Backward-compatible schema changes with deprecation paths
- **Documentation Sync**: Automatic documentation updates with schema changes

Note: These schemas are re-exported from shared.models to maintain a single source of truth
for data contracts while providing convenient access through the backend schema package.
