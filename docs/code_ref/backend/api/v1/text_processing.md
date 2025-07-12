# REST API endpoints for text processing operations.

This module provides a comprehensive set of endpoints for AI-powered text processing
operations including summarization, sentiment analysis, key point extraction,
question generation, and Q&A functionality.

## Endpoints

GET /text_processing/operations:
Retrieve available text processing operations and their configurations.

POST /text_processing/process:
Process a single text request using specified AI operations.

POST /text_processing/batch_process:
Process multiple text requests in a single batch operation.

GET /text_processing/batch_status/{batch_id}:
Check the status of a batch processing job (synchronous implementation).

GET /text_processing/health:
Get comprehensive health status for the text processing service,
including domain service and underlying resilience infrastructure.

## Authentication

Most endpoints require API key authentication via the Authorization header
or api_key parameter. The /operations and /health endpoints support
optional authentication.

## Features

- Multiple AI processing operations (summarize, sentiment, key_points, etc.)
- Batch processing with configurable limits
- Comprehensive error handling and logging
- Request tracing with unique IDs
- Resilience infrastructure integration
- Input validation and sanitization

## Examples

Single text processing:
POST /text_processing/process
{
"text": "Your text here",
"operation": "summarize",
"options": {"max_length": 150}
}

### Batch processing

POST /text_processing/batch_process
{
"requests": [
{"text": "Text 1", "operation": "sentiment"},
{"text": "Text 2", "operation": "summarize"}
],
"batch_id": "optional-batch-id"
}
