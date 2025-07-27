"""API Schema Definitions

Central registry for all Pydantic schemas used in the FastAPI application's public API.

## Available Schemas

### Common Schemas
- `ErrorResponse`: Standardized error response format
- `SuccessResponse`: Generic success response wrapper
- `PaginationInfo`: Pagination metadata for list endpoints

### Health & Monitoring
- `HealthResponse`: System health check response structure

### Text Processing Domain
- `TextProcessingOperation`: Enumeration of AI processing operations
- `TextProcessingRequest`: Single text processing request structure
- `TextProcessingResponse`: Single text processing response
- `BatchTextProcessingRequest`: Batch processing request
- `BatchTextProcessingResponse`: Batch processing response
- `BatchTextProcessingItem`: Individual batch item
- `BatchTextProcessingStatus`: Batch job status enumeration
- `SentimentResult`: Structured sentiment analysis results

## Usage

```python
from app.schemas import ErrorResponse, TextProcessingRequest
```

Note: Text processing schemas are currently re-exported from shared models for compatibility.
"""

# Health monitoring schemas
from .health import (
    HealthResponse,
)

# Common response schemas used across multiple endpoints
from .common import (
    ErrorResponse,
    SuccessResponse,
    PaginationInfo,
)

# Text processing domain schemas
from .text_processing import (
    TextProcessingOperation,
    TextProcessingRequest,
    BatchTextProcessingRequest,
    SentimentResult,
    TextProcessingResponse,
    BatchTextProcessingStatus,
    BatchTextProcessingItem,
    BatchTextProcessingResponse,
)

__all__ = [
    # Health schemas
    "HealthResponse",
    
    # Common schemas
    "ErrorResponse",
    "SuccessResponse", 
    "PaginationInfo",
    
    # Text Processing schemas
    "TextProcessingOperation",
    "BatchTextProcessingStatus", 
    "TextProcessingRequest",
    "TextProcessingResponse",
    "BatchTextProcessingRequest",
    "BatchTextProcessingResponse",
    "BatchTextProcessingItem",
    "SentimentResult",
]
