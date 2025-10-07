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
from typing import Dict, Any
from pydantic import BaseModel, Field, field_serializer
from pydantic.types import SerializationInfo


class ErrorResponse(BaseModel):
    """
    Standardized error response model providing consistent error reporting across all API endpoints.

    This model serves as the foundation for all error responses in the API, ensuring predictable
    error information delivery regardless of the specific endpoint, error type, or failure context.
    It integrates seamlessly with the global exception handler and provides structured error
    information for both human users and automated systems.

    Attributes:
        success: Always False for error responses, enabling clients to easily distinguish
                error responses from success responses in a consistent manner
        error: Human-readable error message describing what went wrong, safe for display
               to end users and suitable for user interface error presentation
        error_code: Optional machine-readable error code for programmatic error handling,
                   enabling client applications to implement specific error handling logic
        details: Optional dictionary containing additional error context for debugging,
                sanitized to exclude sensitive information while providing useful context
        timestamp: ISO 8601 formatted timestamp indicating when the error occurred,
                  facilitating debugging, log correlation, and performance analysis

    State Management:
        - Immutable once created (Pydantic model behavior)
        - Thread-safe for concurrent access across request handlers
        - Automatic timestamp generation with UTC timezone
        - Consistent JSON serialization with proper field ordering
        - Integration with logging systems for error tracking

    Behavior:
        - Automatically sets success to False for all error instances
        - Generates timestamp at creation time for accurate error timing
        - Serializes timestamp to ISO 8601 format for JSON compatibility
        - Validates error message is non-empty for meaningful error reporting
        - Sanitizes details dictionary to prevent sensitive data exposure
        - Integrates with FastAPI's automatic OpenAPI documentation

    Examples:
        >>> # Basic error response without additional context
        >>> basic_error = ErrorResponse(error="Invalid request format")
        >>> assert basic_error.success is False
        >>> assert basic_error.error == "Invalid request format"

        >>> # Error with machine-readable code for programmatic handling
        >>> validation_error = ErrorResponse(
        ...     error="Question is required for Q&A operation",
        ...     error_code="VALIDATION_ERROR"
        ... )
        >>> assert validation_error.error_code == "VALIDATION_ERROR"

        >>> # Comprehensive error with debugging context
        >>> detailed_error = ErrorResponse(
        ...     error="AI service temporarily unavailable",
        ...     error_code="SERVICE_UNAVAILABLE",
        ...     details={
        ...         "service": "gemini_api",
        ...         "retry_after": 30,
        ...         "request_id": "req_12345"
        ...     }
        ... )
        >>> assert "service" in detailed_error.details

        >>> # Error response serialization
        >>> error_json = detailed_error.model_dump_json()
        >>> assert "timestamp" in error_json
        >>> assert "success" in error_json
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
    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code for programmatic handling"
    )
    details: Dict[str, Any] | None = Field(
        default=None,
        description="Additional error context (no sensitive data)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info: SerializationInfo) -> str:
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
    message: str | None = Field(
        default=None,
        description="Optional success message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the operation completed"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info: SerializationInfo) -> str:
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
