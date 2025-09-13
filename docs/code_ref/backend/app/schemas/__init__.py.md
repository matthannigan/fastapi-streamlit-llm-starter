---
sidebar_label: __init__
---

# API Schema Definitions Package

  file_path: `backend/app/schemas/__init__.py`

This package serves as the central registry for all Pydantic schemas used throughout the FastAPI
backend application, providing type-safe data contracts, comprehensive validation, and consistent
API documentation generation. The schemas are organized by functional domain and integrate
seamlessly with FastAPI's automatic OpenAPI documentation system.

## Package Architecture

The schema package follows a domain-driven design with clear separation of concerns:

### Core Schema Categories
- **Common Schemas**: Reusable response patterns and pagination structures
- **Health Monitoring**: System health and service availability schemas
- **Domain-Specific**: Business logic schemas (text processing, future domains)
- **Shared Integration**: Cross-application schemas via shared models package

### Design Principles
- **Type Safety**: Comprehensive type hints and Pydantic validation
- **API Documentation**: Rich schema descriptions for automatic OpenAPI generation
- **Consistency**: Standardized response formats across all endpoints
- **Validation**: Robust input validation with clear error messages
- **Future-Proof**: Extensible design for additional domains and use cases

## Available Schema Categories

### Common API Schemas (`common.py`)
Foundational schemas for consistent API responses:
- **ErrorResponse**: Standardized error response with structured context and error codes
- **SuccessResponse**: Generic success response wrapper for simple operations
- **PaginationInfo**: Comprehensive pagination metadata for list endpoints with navigation flags

### Health & Monitoring Schemas (`health.py`)
System health and operational monitoring:
- **HealthResponse**: Comprehensive health status including service dependencies,
  performance indicators, and version information for monitoring integration

### Text Processing Domain Schemas (`text_processing.py`)
AI-powered text analysis operations (re-exported from shared models):
- **TextProcessingOperation**: Enumeration of available AI operations (summarize, sentiment, qa, etc.)
- **TextProcessingRequest**: Single operation request with validation and optional parameters
- **TextProcessingResponse**: Operation results with metadata and performance tracking
- **BatchTextProcessingRequest**: Multi-operation batch processing with concurrency control
- **BatchTextProcessingResponse**: Batch results with aggregated status and individual item tracking
- **BatchTextProcessingItem**: Individual batch item status and results
- **BatchTextProcessingStatus**: Batch operation status enumeration
- **SentimentResult**: Structured sentiment analysis with confidence scoring and polarity

## Schema Integration Patterns

### FastAPI Integration
```python
from fastapi import FastAPI
from app.schemas import ErrorResponse, TextProcessingRequest, HealthResponse

@app.post("/api/v1/process", response_model=TextProcessingResponse)
async def process_text(request: TextProcessingRequest):
    # Automatic request validation and response serialization
    pass

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Consistent error responses using ErrorResponse schema
    return ErrorResponse(error=str(exc), error_code="INTERNAL_ERROR")
```

### Cross-Service Schema Sharing
```python
from shared.models import TextProcessingRequest
from app.schemas import ErrorResponse

# Schemas are shared between FastAPI backend and Streamlit frontend
# through the shared.models package for type consistency
```

### Validation and Serialization
```python
from app.schemas.common import PaginationInfo
from app.schemas.health import HealthResponse

# Automatic validation with clear error messages
pagination = PaginationInfo(
    page=1, page_size=20, total_items=150,
    total_pages=8, has_next=True, has_previous=False
)

# Automatic serialization with ISO timestamp formatting
health = HealthResponse(status="healthy", ai_model_available=True)
```

## Usage Patterns

### Basic Schema Usage
```python
from app.schemas import ErrorResponse, SuccessResponse, TextProcessingRequest

# Error response creation
error_response = ErrorResponse(
    error="Invalid input data",
    error_code="VALIDATION_ERROR",
    details={"field": "text", "reason": "required"}
)

# Success response for simple operations
success_response = SuccessResponse(
    message="Operation completed successfully"
)

# Text processing request validation
request = TextProcessingRequest(
    text="Sample text for analysis",
    operation="summarize",
    options={"max_length": 100}
)
```

### Batch Processing Integration
```python
from app.schemas.text_processing import (
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchTextProcessingStatus
)

# Batch request creation
batch_request = BatchTextProcessingRequest(
    requests=[
        TextProcessingRequest(text="Text 1", operation="summarize"),
        TextProcessingRequest(text="Text 2", operation="sentiment")
    ],
    batch_id="analysis_batch_001"
)

# Batch response tracking
batch_response = BatchTextProcessingResponse(
    batch_id="analysis_batch_001",
    status=BatchTextProcessingStatus.COMPLETED,
    total_items=2,
    completed_items=2,
    failed_items=0
)
```

### Health Monitoring Integration
```python
from app.schemas.health import HealthResponse

# Comprehensive health status
health_status = HealthResponse(
    status="healthy",
    ai_model_available=True,
    resilience_healthy=True,
    cache_healthy=True,
    version="1.0.0"
)
```

## Validation Features

### Input Validation
- **Type Safety**: Automatic type conversion and validation
- **Range Validation**: Numeric ranges, string lengths, list sizes
- **Format Validation**: Email formats, URLs, custom patterns
- **Business Rules**: Domain-specific validation logic
- **Clear Errors**: Descriptive validation error messages

### Serialization Features
- **JSON Compatibility**: Automatic JSON serialization with proper formatting
- **Timestamp Formatting**: ISO 8601 timestamp serialization
- **Enum Handling**: Proper enumeration serialization and validation
- **Optional Fields**: Flexible handling of optional and default values
- **Custom Serializers**: Domain-specific serialization logic

## OpenAPI Documentation Integration

### Automatic Documentation
- **Schema Descriptions**: Rich field descriptions for API documentation
- **Examples**: Realistic examples for better API understanding
- **Validation Rules**: Automatic constraint documentation
- **Response Models**: Clear response structure documentation

### Documentation Quality
```python
class ErrorResponse(BaseModel):
    """Standardized error response model for all API endpoints."""
    
    error: str = Field(
        ..., 
        description="Human-readable error message",
        min_length=1,
        example="Invalid input data: text field is required"
    )
    
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code for programmatic handling",
        example="VALIDATION_ERROR"
    )
```

## Performance Considerations

### Validation Performance
- **Fast Validation**: Optimized Pydantic validation for high-throughput APIs
- **Lazy Loading**: Efficient schema loading and compilation
- **Memory Efficient**: Minimal memory overhead for schema definitions
- **Caching**: Schema compilation caching for improved performance

### Serialization Performance
- **Efficient JSON**: Fast JSON serialization with minimal overhead
- **Streaming Support**: Support for streaming large responses
- **Compression Ready**: Compatible with response compression middleware
- **Batch Optimization**: Efficient batch processing support

## Testing Support

### Schema Testing
```python
from app.schemas.common import ErrorResponse
import pytest

def test_error_response_validation():
    # Valid error response
    error = ErrorResponse(error="Test error", error_code="TEST_ERROR")
    assert error.success is False
    assert error.error == "Test error"
    
    # Invalid error response (empty error message)
    with pytest.raises(ValidationError):
        ErrorResponse(error="")
```

### Mock Data Generation
```python
from app.schemas.text_processing import TextProcessingRequest

# Generate test data
test_request = TextProcessingRequest(
    text="Sample test content",
    operation="summarize",
    options={"max_length": 50}
)

# Validate test data matches schema requirements
assert test_request.text == "Sample test content"
assert test_request.operation == "summarize"
```

## Migration and Compatibility

### Schema Evolution
- **Backward Compatibility**: Careful schema evolution with deprecation paths
- **Version Management**: Schema versioning for API evolution
- **Migration Support**: Tools for migrating between schema versions
- **Legacy Support**: Compatibility with existing API consumers

### Shared Model Integration
- **Cross-Service Consistency**: Shared schemas between FastAPI and Streamlit
- **Type Safety**: Consistent types across service boundaries
- **Validation Consistency**: Same validation rules across services
- **Documentation Sync**: Synchronized API documentation
