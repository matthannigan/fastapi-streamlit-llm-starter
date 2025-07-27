# Common API Response Schemas

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
