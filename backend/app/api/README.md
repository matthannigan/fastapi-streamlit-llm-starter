# API Documentation

## Overview

The AI Text Processor API provides endpoints for processing text using various AI models. The API is built with FastAPI and uses Google's Gemini AI model for text processing operations.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses **Bearer Token authentication** with API keys to protect sensitive endpoints.

### API Key Setup

1. Set your API key in environment variables:
   ```bash
   export API_KEY=your_secure_api_key_here
   ```

2. Include the API key in requests using the Authorization header:
   ```bash
   Authorization: Bearer your_api_key_here
   ```

### Protected Endpoints

- `POST /process` - Requires authentication
- `GET /auth/status` - Requires authentication

### Public Endpoints

- `GET /` - No authentication required
- `GET /health` - No authentication required
- `GET /operations` - Optional authentication

### Authentication Examples

**Using curl:**
```bash
curl -X POST "http://localhost:8000/v1/text_processing/process" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "operation": "summarize"}'
```

**Using Python requests:**
```python
import requests

headers = {"Authorization": "Bearer your_api_key_here"}
response = requests.post(
    "http://localhost:8000/v1/text_processing/process",
    headers=headers,
    json={"text": "Hello world", "operation": "summarize"}
)
```

### Authentication Errors

**401 Unauthorized - Missing API Key:**
```json
{
  "detail": "API key required. Please provide a valid API key in the Authorization header."
}
```

**401 Unauthorized - Invalid API Key:**
```json
{
  "detail": "Invalid API key"
}
```

For detailed authentication setup and security best practices, see [AUTHENTICATION.md](AUTHENTICATION.md).

## Endpoints

### Root Endpoint

**GET** `/`

Get basic API information.

**Response:**
```json
{
  "message": "AI Text Processor API",
  "version": "1.0.0"
}
```

### Health Check

**GET** `/v1/health`

Check if the API is running and AI models are available.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.123456",
  "version": "1.0.0",
  "ai_model_available": true
}
```

### Authentication Status

**GET** `/auth/status`

Check authentication status. **Requires authentication.**

**Headers:**
```
Authorization: Bearer your_api_key_here
```

**Response:**
```json
{
  "authenticated": true,
  "api_key_prefix": "sk-12345...",
  "message": "Authentication successful"
}
```

### Get Operations

**GET** `/v1/text_processing/operations`

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
    },
    {
      "id": "sentiment",
      "name": "Sentiment Analysis",
      "description": "Analyze the emotional tone of the text",
      "options": []
    },
    {
      "id": "key_points",
      "name": "Key Points",
      "description": "Extract the main points from the text",
      "options": ["max_points"]
    },
    {
      "id": "questions",
      "name": "Generate Questions",
      "description": "Create questions about the text content",
      "options": ["num_questions"]
    },
    {
      "id": "qa",
      "name": "Question & Answer",
      "description": "Answer a specific question about the text",
      "options": [],
      "requires_question": true
    }
  ]
}
```

### Process Text

**POST** `/v1/text_processing/process`

Process text using specified operation.

**Request Body:**
```json
{
  "text": "Your text content here (minimum 10 characters, maximum 10,000)...",
  "operation": "summarize",
  "question": "Optional question for Q&A operation",
  "options": {
    "max_length": 100,
    "max_points": 5,
    "num_questions": 3
  }
}
```

**Validation Rules:**
- `text`: Required, 10-10,000 characters, cannot be empty or only whitespace
- `operation`: Required, must be one of: "summarize", "sentiment", "key_points", "questions", "qa"
- `question`: Required for "qa" operation, optional for others
- `options`: Optional object with operation-specific parameters

**Success Response (Summarize/Q&A):**
```json
{
  "operation": "summarize",
  "success": true,
  "result": "This is the generated summary or answer...",
  "metadata": {
    "word_count": 150
  },
  "processing_time": 2.3,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

**Success Response (Sentiment Analysis):**
```json
{
  "operation": "sentiment",
  "success": true,
  "sentiment": {
    "sentiment": "positive",
    "confidence": 0.85,
    "explanation": "The text expresses optimistic views about future developments"
  },
  "metadata": {
    "word_count": 150
  },
  "processing_time": 1.8,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

**Success Response (Key Points):**
```json
{
  "operation": "key_points",
  "success": true,
  "key_points": [
    "First important point extracted from the text",
    "Second key insight identified",
    "Third main concept discussed"
  ],
  "metadata": {
    "word_count": 150
  },
  "processing_time": 2.1,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

**Success Response (Questions):**
```json
{
  "operation": "questions",
  "success": true,
  "questions": [
    "What are the main themes discussed in this text?",
    "How does this relate to current industry trends?",
    "What implications does this have for the future?"
  ],
  "metadata": {
    "word_count": 150
  },
  "processing_time": 2.5,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

## Error Responses

### Validation Errors (400 Bad Request)

**Pydantic Validation Error:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "text"],
      "msg": "String should have at least 10 characters",
      "input": "short",
      "ctx": {
        "min_length": 10
      }
    }
  ]
}
```

**Business Logic Error:**
```json
{
  "detail": "Question is required for Q&A operation"
}
```

### Processing Errors (500 Internal Server Error)

```json
{
  "detail": "Failed to process text"
}
```

### Not Found (404)

```json
{
  "detail": "Not Found"
}
```

## Request/Response Examples

### Example 1: Text Summarization

**Request:**
```bash
curl -X POST http://localhost:8000/v1/text_processing/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence is transforming industries across the globe. From healthcare diagnostics to autonomous vehicles, AI systems are becoming increasingly sophisticated and capable. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions with remarkable accuracy.",
    "operation": "summarize",
    "options": {"max_length": 50}
  }'
```

**Response:**
```json
{
  "operation": "summarize",
  "success": true,
  "result": "AI is revolutionizing industries through sophisticated machine learning systems that analyze data and make accurate predictions in healthcare, automotive, and other sectors.",
  "metadata": {
    "word_count": 45
  },
  "processing_time": 2.1,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

### Example 2: Sentiment Analysis

**Request:**
```bash
curl -X POST http://localhost:8000/v1/text_processing/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am absolutely thrilled with the new product launch! The features are amazing and the user experience is fantastic.",
    "operation": "sentiment"
  }'
```

**Response:**
```json
{
  "operation": "sentiment",
  "success": true,
  "sentiment": {
    "sentiment": "positive",
    "confidence": 0.92,
    "explanation": "The text contains highly positive language with words like 'thrilled', 'amazing', and 'fantastic'"
  },
  "metadata": {
    "word_count": 20
  },
  "processing_time": 1.5,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

### Example 3: Question & Answer

**Request:**
```bash
curl -X POST http://localhost:8000/v1/text_processing/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Climate change represents one of the most significant challenges facing humanity today. Rising global temperatures are leading to more frequent extreme weather events and rising sea levels.",
    "operation": "qa",
    "question": "What are the main effects of climate change mentioned?"
  }'
```

**Response:**
```json
{
  "operation": "qa",
  "success": true,
  "result": "According to the text, the main effects of climate change are more frequent extreme weather events and rising sea levels, both caused by rising global temperatures.",
  "metadata": {
    "word_count": 32
  },
  "processing_time": 2.8,
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

### Example 4: Error Handling

**Request with invalid input:**
```bash
curl -X POST http://localhost:8000/v1/text_processing/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "short",
    "operation": "summarize"
  }'
```

**Error Response:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "text"],
      "msg": "String should have at least 10 characters",
      "input": "short",
      "ctx": {
        "min_length": 10
      }
    }
  ]
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production environments, consider implementing:
- API requests: 10 requests per second per IP
- Burst: up to 5 additional requests
- Daily limits based on usage tier

## Operation-Specific Options

### Summarize
- `max_length` (integer): Maximum length of summary in words (default: 100)

### Sentiment Analysis
- No additional options

### Key Points
- `max_points` (integer): Maximum number of key points to extract (default: 5)

### Questions
- `num_questions` (integer): Number of questions to generate (default: 5)

### Q&A
- No additional options
- Requires `question` field in request

## Examples

See `examples/` directory for complete code samples in Python demonstrating:
- Basic API usage
- Error handling
- Performance benchmarking
- Integration testing

## Interactive API Documentation

When the API is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
