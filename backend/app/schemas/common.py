"""Common API Response Schemas

This module defines reusable Pydantic models that provide consistent data structures
across all API endpoints. These schemas ensure predictable response formats, improve
API documentation quality, and enable robust client-side integration.

## Models

**ErrorResponse**: Standardized error response format for all API error conditions.
Provides consistent error reporting with structured context data, error codes,
and timestamps for debugging and monitoring.

**SuccessResponse**: Generic success response wrapper for simple operations that
don't return complex data. Includes success indicators and optional messages.

**PaginationInfo**: Standardized pagination metadata for list endpoints. Provides
comprehensive pagination information including page counts, navigation flags,
and item totals.

## Design Patterns

- **Consistent Field Naming**: All schemas use consistent field names (success,
  timestamp, etc.) to provide predictable client experience
- **Rich Documentation**: Each field includes comprehensive descriptions for
  automatic OpenAPI documentation generation
- **JSON Schema Examples**: All schemas include realistic examples for better
  API documentation and testing
- **Validation Rules**: Appropriate Pydantic validators ensure data integrity
  and provide clear validation error messages

## Usage Examples

Basic error response creation:

```python
from app.schemas.common import ErrorResponse

error = ErrorResponse(
    error="Invalid input data",
    error_code="VALIDATION_ERROR",
    details={"field": "email", "reason": "format"}
)
```

Success response for simple endpoints:

```python
from app.schemas.common import SuccessResponse

response = SuccessResponse(
    message="User profile updated successfully"
)
```

Pagination information for list endpoints:

```python
from app.schemas.common import PaginationInfo

pagination = PaginationInfo(
    page=1,
    page_size=20,
    total_items=150,
    total_pages=8,
    has_next=True,
    has_previous=False
)
```

## Integration Notes

- **FastAPI Integration**: These schemas are designed to work seamlessly with
  FastAPI's automatic OpenAPI documentation generation and response validation
- **Global Exception Handler**: The ErrorResponse schema is tightly integrated
  with the application's global exception handling system for consistent error
  reporting across all endpoints
- **Client Libraries**: The standardized format enables robust client library
  generation and simplifies error handling in client applications
- **Monitoring**: Structured error responses with timestamps and context data
  facilitate comprehensive application monitoring and debugging
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_serializer


class ErrorResponse(BaseModel):
    """
    Standardized error response model for all API endpoints.
    
    This model provides a consistent error response format across the entire API,
    ensuring clients receive predictable error information regardless of the
    specific endpoint or error type.
    
    Attributes:
        success (bool): Always False for error responses. Allows clients to 
            easily distinguish success from error responses.
        error (str): Human-readable error message describing what went wrong.
            Should be safe to display to end users.
        error_code (str, optional): Machine-readable error code for programmatic
            error handling. Examples: "VALIDATION_ERROR", "AI_SERVICE_ERROR".
        details (dict, optional): Additional error context for debugging.
            Should not contain sensitive information as it may be logged.
        timestamp (datetime): ISO formatted timestamp when the error occurred.
            Useful for debugging and log correlation.
    
    Example:
        ```json
        {
            "success": false,
            "error": "Question is required for Q&A operation",
            "error_code": "VALIDATION_ERROR",
            "details": {
                "operation": "qa",
                "request_id": "12345-abcde"
            },
            "timestamp": "2025-01-12T10:30:45.123456"
        }
        ```
    """
    success: bool = Field(
        default=False, 
        description="Always false for error responses"
    )
    error: str = Field(
        ..., 
        description="Human-readable error message",
        min_length=1
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code for programmatic handling"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context (no sensitive data)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info) -> str:
        """Serialize datetime to ISO format string for JSON compatibility."""
        return dt.isoformat()

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid request data: text field is required",
                "error_code": "VALIDATION_ERROR",
                "details": {
                    "field": "text",
                    "request_id": "req_12345"
                },
                "timestamp": "2025-01-12T10:30:45.123456"
            }
        }


class SuccessResponse(BaseModel):
    """
    Standardized success response wrapper for simple operations.
    
    For operations that don't return complex data, this provides a consistent
    success response format. More complex operations should define their own
    response models that inherit from this or include these fields.
    
    Attributes:
        success (bool): Always True for success responses.
        message (str, optional): Human-readable success message.
        timestamp (datetime): When the operation completed successfully.
    
    Example:
        ```json
        {
            "success": true,
            "message": "Operation completed successfully",
            "timestamp": "2025-01-12T10:30:45.123456"
        }
        ```
    """
    success: bool = Field(
        default=True,
        description="Always true for success responses"  
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional success message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the operation completed"
    )

    @field_serializer('timestamp') 
    def serialize_timestamp(self, dt: datetime, _info) -> str:
        """Serialize datetime to ISO format string for JSON compatibility."""
        return dt.isoformat()


class PaginationInfo(BaseModel):
    """
    Pagination metadata for list endpoints.
    
    Provides standardized pagination information for endpoints that return
    lists of items. Helps clients implement proper pagination controls.
    
    Attributes:
        page (int): Current page number (1-based).
        page_size (int): Number of items per page.
        total_items (int): Total number of items across all pages.
        total_pages (int): Total number of pages.
        has_next (bool): Whether there are more pages available.
        has_previous (bool): Whether there are previous pages available.
    """
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, le=1000, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total items across all pages")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether more pages are available")
    has_previous: bool = Field(..., description="Whether previous pages exist")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_previous": False
            }
        } 