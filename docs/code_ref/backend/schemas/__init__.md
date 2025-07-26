# Public API data contracts and Pydantic schema definitions.

This module serves as the central registry for all Pydantic schemas used in the FastAPI
application's public API. It provides a single import point for all data models that
define the structure of API requests, responses, and internal data representations.

The schemas module follows a domain-driven organization pattern, grouping related
models by functional area while providing common utilities that can be reused across
different domains. All schemas are designed with API-first principles, ensuring
consistent data structures, comprehensive validation, and excellent documentation
for automatic OpenAPI generation.

## Architecture

The schemas are organized into three main categories:

1. **Common Schemas**: Reusable models for cross-cutting concerns like error
handling, success responses, and pagination that are used across multiple
endpoints and domains.

2. **Domain-Specific Schemas**: Models that represent specific business domains
such as text processing, health monitoring, and authentication.

3. **System Schemas**: Infrastructure-related models for health checks, monitoring,
and system status reporting.

## Schema Categories

### Common Response Models

- ErrorResponse: Standardized error response format for all API endpoints
- SuccessResponse: Generic success response wrapper for simple operations
- PaginationInfo: Metadata for paginated list responses

### Health & Monitoring

- HealthResponse: System health check response structure

### Text Processing Domain

- TextProcessingOperation: Enumeration of available AI processing operations
- TextProcessingRequest: Single text processing job request structure
- TextProcessingResponse: Single text processing operation response
- BatchTextProcessingRequest: Multiple text processing jobs request
- BatchTextProcessingResponse: Batch processing results response
- BatchTextProcessingItem: Individual item within batch responses
- BatchTextProcessingStatus: Enumeration of batch job statuses
- SentimentResult: Structured sentiment analysis results

## Design Principles

- **API-First Design**: All schemas are designed to provide excellent API
documentation and client library generation capabilities.
- **Validation-Rich**: Comprehensive Pydantic validators ensure data integrity
and provide clear error messages for invalid inputs.
- **Documentation-Complete**: Every field includes detailed descriptions for
automatic OpenAPI documentation generation.
- **Example-Driven**: All schemas include realistic examples for better
understanding and testing capabilities.
- **Consistency**: Common patterns and naming conventions are maintained
across all schemas for predictable developer experience.

## Usage Examples

Importing common schemas:
```python
from app.schemas import ErrorResponse, SuccessResponse

# Use in endpoint response models
@router.post("/example", responses={
400: {"model": ErrorResponse, "description": "Validation Error"}
})
async def example_endpoint():
return SuccessResponse(message="Operation completed")
```

Importing domain-specific schemas:
```python
from app.schemas import TextProcessingRequest, TextProcessingResponse

@router.post("/process", response_model=TextProcessingResponse)
async def process_text(request: TextProcessingRequest):
# Process the request...
return TextProcessingResponse(...)
```

Bulk import for complex endpoints:
```python
from app.schemas import (
BatchTextProcessingRequest,
BatchTextProcessingResponse,
ErrorResponse
)
```

## FastAPI Integration

These schemas are designed to work seamlessly with FastAPI's features:

- **Automatic Validation**: Pydantic models provide request/response validation
- **OpenAPI Generation**: Rich field documentation generates comprehensive API docs
- **Type Safety**: Full typing support for IDE completion and static analysis
- **Serialization**: Automatic JSON serialization/deserialization
- **Error Handling**: Integration with custom exception handlers for consistent
error responses across all endpoints

## Migration Notes

This module is part of a migration from shared models to domain-specific schemas.
Legacy imports from the `shared` package are gradually being moved here to
improve code organization and maintainability. The migration maintains backward
compatibility while providing a cleaner architectural separation.

## Version History

1.0.0: Initial schema organization with common, health, and text processing domains
1.1.0: Enhanced error response schemas with structured context data
1.2.0: Added comprehensive batch processing support

## See Also

- app.core.exceptions: Custom exception hierarchy that works with ErrorResponse
- app.api.v1: API endpoints that use these schema definitions
- shared.models: Legacy shared models being migrated to this module

## Author

FastAPI LLM Starter Team

## License

MIT License
