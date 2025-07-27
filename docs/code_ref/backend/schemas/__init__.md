# API Schema Definitions

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
