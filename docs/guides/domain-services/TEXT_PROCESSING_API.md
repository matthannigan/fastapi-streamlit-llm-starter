# Text Processing Domain Service API Reference

## Overview

The Text Processing Domain Service provides a comprehensive REST API for AI-powered text analysis operations. This service demonstrates a production-ready implementation of domain-specific AI processing with robust infrastructure integration, showcasing best practices in API design, error handling, and resilience.

### Key Features

- **Multiple AI Operations**: Support for various text processing tasks
- **Dual API Architecture**: Public and authenticated endpoints
- **Comprehensive Error Handling**: Structured error responses
- **Batch Processing**: Efficient multi-request processing
- **Authentication**: Secure API key validation
- **Resilience Integration**: Circuit breakers and error management

## Available Operations

The Text Processing API supports the following AI-powered operations:

| Operation | Description | Configurable Options | Example Use Case |
|-----------|-------------|---------------------|-----------------|
| `summarize` | Generate concise text summary | `max_length` | Long article condensation |
| `sentiment` | Analyze text emotional tone | None | Customer feedback analysis |
| `key_points` | Extract main points from text | `max_points` | Document quick insights |
| `questions` | Generate relevant questions | `num_questions` | Study material creation |
| `qa` | Answer specific text-based questions | Requires `question` | Comprehension support |

## Authentication

### API Key Authentication

- **Required for**: Single text processing, batch processing, batch status
- **Method**: API key verification via `X-API-Key` header
- **Authorization Types**:
  - Strict authentication for processing endpoints
  - Optional authentication for metadata endpoints

### Authorization Headers

```http
X-API-Key: your_api_key_here
```

## Endpoint Reference

### 1. Operations Discovery
```http
GET /v1/text_processing/operations
```

#### Description
Retrieve available text processing operations and their configurations.

#### Response Example
```json
{
    "operations": [
        {
            "id": "summarize",
            "name": "Summarize",
            "description": "Generate a concise summary of the text",
            "options": ["max_length"]
        }
        // ... other operations
    ]
}
```

### 2. Single Text Processing
```http
POST /v1/text_processing/process
```

#### Request Body
```json
{
    "text": "Your text to process here",
    "operation": "summarize", 
    "options": {"max_length": 150}
}
```

#### Response Example
```json
{
    "result": "Generated summary of the input text...",
    "operation": "summarize",
    "metadata": {"processing_time": 1.23}
}
```

### 3. Batch Text Processing
```http
POST /v1/text_processing/batch_process
```

#### Request Body
```json
{
    "requests": [
        {"text": "First document", "operation": "sentiment"},
        {"text": "Second document", "operation": "key_points", "options": {"max_points": 5}}
    ],
    "batch_id": "my-batch-2024"
}
```

#### Response Example
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

### 4. Batch Status Check
```http
GET /v1/text_processing/batch_status/{batch_id}
```

#### Response Example
```json
{
    "batch_id": "my-batch-2024",
    "status": "COMPLETED_SYNC",
    "message": "Batch processing is synchronous."
}
```

### 5. Service Health Check
```http
GET /v1/text_processing/health
```

#### Response Example
```json
{
    "overall_healthy": true,
    "service_type": "domain", 
    "infrastructure": {
        "resilience": {
            "healthy": true,
            "circuit_breakers": {"status": "closed"},
            "rate_limiters": {"active": false}
        }
    },
    "domain_services": {
        "text_processing": {
            "healthy": true,
            "response_time_ms": 150,
            "requests_processed": 1024
        }
    }
}
```

## Integration Examples

### cURL
```bash
# Single Text Processing
curl -X POST https://api.example.com/v1/text_processing/process \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key" \
     -d '{
         "text": "Your text goes here...",
         "operation": "summarize",
         "options": {"max_length": 100}
     }'

# Batch Processing
curl -X POST https://api.example.com/v1/text_processing/batch_process \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key" \
     -d '{
         "requests": [
             {"text": "First document", "operation": "sentiment"},
             {"text": "Second document", "operation": "key_points"}
         ]
     }'
```

### Python (with `httpx`)
```python
import httpx

async def process_text():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/v1/text_processing/process",
            headers={
                "X-API-Key": "your_api_key",
                "Content-Type": "application/json"
            },
            json={
                "text": "Your text goes here...",
                "operation": "summarize",
                "options": {"max_length": 100}
            }
        )
        return response.json()
```

### JavaScript (with `axios`)
```javascript
import axios from 'axios';

async function processText() {
    try {
        const response = await axios.post(
            'https://api.example.com/v1/text_processing/process',
            {
                text: 'Your text goes here...',
                operation: 'summarize',
                options: { max_length: 100 }
            },
            {
                headers: {
                    'X-API-Key': 'your_api_key',
                    'Content-Type': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Processing error:', error.response.data);
    }
}
```

## Error Handling

### Exception Types
| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `ValidationError` | 400/422 | Invalid request, missing fields |
| `BusinessLogicError` | 400 | Violation of domain rules |
| `InfrastructureError` | 500/502/503 | AI service or backend failures |

### Error Response Structure
```json
{
    "error": "Descriptive error message",
    "code": "ERROR_CODE",
    "details": {
        "context": "Additional error context",
        "request_id": "unique-request-identifier"
    }
}
```

## Performance & Limitations

### Rate Limiting
- Maximum of `MAX_BATCH_REQUESTS_PER_CALL` requests per batch
- Configurable via environment settings
- Default: 10 requests per batch call

### Processing Timeouts
- Single text processing: Configurable, default ~30 seconds
- Batch processing: Total timeout proportional to number of requests

## Security Considerations

- Input text is sanitized to prevent prompt injection
- API key required for processing operations
- Optional authentication for metadata endpoints
- Comprehensive logging with request tracing
- Circuit breakers protect against service degradation

## Related Documentation

- [Infrastructure Services Overview](/docs/guides/infrastructure/README.md)
- [Resilience Patterns](/docs/reference/key-concepts/RESILIENCE.md)
- [Authentication Guide](/docs/guides/developer/AUTHENTICATION.md)

## Customization & Extensibility

This text processing service is designed as an **educational example**. To customize:

1. Replace domain service logic in `app/services/text_processor.py`
2. Add or modify operations in `TextProcessorService`
3. Update Pydantic schemas in `app/schemas/text_processing.py`
4. Integrate with your preferred AI provider

**Note**: Maintain the established error handling and resilience patterns when extending the service.