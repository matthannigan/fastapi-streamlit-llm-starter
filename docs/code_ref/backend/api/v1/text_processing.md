# Domain Service: AI Text Processing REST API

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project
💡 **Demonstrates infrastructure usage patterns**
🔄 **Expected to be modified/replaced**

This module provides comprehensive REST API endpoints for AI-powered text processing
operations, demonstrating how to build domain services that leverage infrastructure
services for AI processing, caching, resilience, and security. It serves as a complete
example for implementing AI-powered domain APIs with proper error handling,
authentication, and monitoring.

## Core Components

### API Endpoints
- `GET /v1/text_processing/operations`: Available operations and configurations (optional auth)
- `POST /v1/text_processing/process`: Single text processing with AI operations (requires auth)
- `POST /v1/text_processing/batch_process`: Batch text processing with limits (requires auth)
- `GET /v1/text_processing/batch_status/{batch_id}`: Batch status checking (requires auth)
- `GET /v1/text_processing/health`: Service health with infrastructure status (optional auth)

### Processing Operations
- **summarize**: Text summarization with configurable length
- **sentiment**: Sentiment analysis with confidence scores
- **key_points**: Key point extraction with configurable count
- **questions**: Question generation from text content
- **qa**: Question answering (requires question parameter)

### Features
- **Batch Processing**: Configurable limits with comprehensive error handling
- **Request Tracing**: Unique IDs for logging and debugging
- **Resilience Integration**: Circuit breakers, retries, and graceful degradation
- **Input Validation**: Pydantic models with sanitization
- **Error Handling**: Structured exceptions with proper HTTP status codes

## Dependencies & Integration

### Infrastructure Dependencies
- `app.infrastructure.security`: API key authentication services
- `app.services.text_processor.TextProcessorService`: AI text processing with resilience
- `app.core.exceptions`: Structured exception handling
- `app.schemas`: Pydantic request/response models

### Domain Logic
- Operation validation and business rule enforcement
- Batch size limits and concurrent processing management
- Request tracing and logging for operational visibility
- Health monitoring that combines domain and infrastructure status

## Usage Examples

### Single Text Processing
```bash
POST /v1/text_processing/process
Content-Type: application/json
Authorization: Bearer your-api-key

{
"text": "Your text to process here",
"operation": "summarize",
"options": {"max_length": 150}
}
```

### Batch Processing
```bash
POST /v1/text_processing/batch_process
Content-Type: application/json
Authorization: Bearer your-api-key

{
"requests": [
{"text": "First document", "operation": "sentiment"},
{"text": "Second document", "operation": "key_points", "options": {"max_points": 5}}
],
"batch_id": "my-batch-2024"
}
```

### Operations Discovery
```bash
GET /v1/text_processing/operations
# No auth required - returns available operations and their options
```

## Response Examples

### Successful Processing
```json
{
"result": "Generated summary of the input text...",
"operation": "summarize",
"metadata": {"processing_time": 1.23}
}
```

### Batch Response
```json
{
"batch_id": "my-batch-2024",
"total_requests": 2,
"completed": 2,
"failed": 0,
"results": [
{"result": "Positive sentiment", "operation": "sentiment"},
{"result": "Key points: 1. Point one...", "operation": "key_points"}
]
}
```

## Error Handling

### Exception Types
- `ValidationError`: Invalid requests, missing required fields
- `BusinessLogicError`: Domain rule violations, operation constraints
- `InfrastructureError`: AI service failures, cache issues, network problems

### HTTP Status Codes
- `200 OK`: Successful processing
- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Authentication failures
- `422 Unprocessable Entity`: Request validation errors
- `500 Internal Server Error`: Infrastructure failures
- `502 Bad Gateway`: AI service errors
- `503 Service Unavailable`: Service temporarily unavailable

## Implementation Notes

This service demonstrates domain-level text processing APIs that:
- Compose multiple infrastructure services for comprehensive functionality
- Implement proper authentication and authorization patterns
- Provide structured error handling with appropriate HTTP status codes
- Support both single and batch processing with configurable limits
- Include comprehensive logging and request tracing for operations

**Replace in your project** - This is a complete example of an AI-powered domain service.
Customize the operations, validation logic, and business rules based on your specific
text processing requirements and use cases.
