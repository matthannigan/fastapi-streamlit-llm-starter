# API Documentation

## Overview

The AI Text Processor API provides endpoints for processing text using various AI models.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

## Authentication

Currently, no authentication is required. In production, consider adding API key authentication.

## Endpoints

### Health Check

**GET** `/health`

Check if the API is running and AI models are available.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "ai_model_available": true
}
```

### Get Operations

**GET** `/operations`

Get list of available text processing operations.

**Response:**
```json
{
  "operations": [
    {
      "id": "summarize",
      "name": "Summarize",
      "description": "Generate a concise summary of the text",
      "options": ["max_length"]
    }
  ]
}
```

### Process Text

**POST** `/process`

Process text using specified operation.

**Request Body:**
```json
{
  "text": "Your text content here...",
  "operation": "summarize",
  "question": "Optional question for Q&A",
  "options": {
    "max_length": 100
  }
}
```

**Response:**
```json
{
  "operation": "summarize",
  "success": true,
  "result": "Summary of the text...",
  "metadata": {
    "word_count": 150
  },
  "processing_time": 2.3,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Responses

All endpoints return error responses in this format:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

- API requests: 10 requests per second
- Burst: up to 5 additional requests

## Examples

See `examples/` directory for code samples in various languages.
