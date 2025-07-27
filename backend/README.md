# FastAPI Backend with PydanticAI Integration

A robust FastAPI application that provides AI-powered text processing capabilities using PydanticAI and Google's Gemini models.

## Features

- **Text Summarization**: Generate concise summaries of long texts
- **Sentiment Analysis**: Analyze emotional tone with confidence scores
- **Key Points Extraction**: Extract main points from text content
- **Question Generation**: Create thoughtful questions about text
- **Question & Answer**: Answer specific questions based on text content
- **Health Monitoring**: Built-in health checks and monitoring
- **Comprehensive Error Handling**: Robust error handling with detailed logging
- **CORS Support**: Configured for frontend integration
- **Docker Support**: Containerized deployment ready

## API Endpoints

### Core Endpoints

- `GET  /v1/health` - Health check endpoint
- `GET  /v1/text_processing/operations` - List available text processing operations
- `POST /v1/text_processing/process` - Process text with specified operation

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "ai_model_available": true
}
```

### Text Processing Request
```json
{
  "text": "Your text content here...",
  "operation": "summarize",
  "options": {
    "max_length": 100
  },
  "question": "Optional question for Q&A operation"
}
```

### Text Processing Response
```json
{
  "operation": "summarize",
  "success": true,
  "result": "Generated summary...",
  "metadata": {
    "word_count": 150
  },
  "processing_time": 2.3,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Available Operations

1. **Summarize** (`summarize`)
   - Options: `max_length` (default: 100)
   - Returns: Concise summary in `result` field

2. **Sentiment Analysis** (`sentiment`)
   - Options: None
   - Returns: Sentiment data in `sentiment` field with confidence score

3. **Key Points** (`key_points`)
   - Options: `max_points` (default: 5)
   - Returns: List of key points in `key_points` field

4. **Generate Questions** (`questions`)
   - Options: `num_questions` (default: 5)
   - Returns: List of questions in `questions` field

5. **Question & Answer** (`qa`)
   - Options: None
   - Required: `question` field
   - Returns: Answer in `result` field

## Setup and Installation

### Prerequisites

- Python 3.11+
- Google Gemini API key

### Environment Variables

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t backend .
```

2. Run the container:
```bash
docker run -p 8000:8000 --env-file .env backend
```

### Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
# Fast unit tests (mocked AI services - default)
pytest tests/ -v

# Unit tests only
pytest unit/ -v

# Integration tests
pytest integration/ -v

# Slow tests (requires --run-slow flag)
pytest tests/ -v -m "slow" --run-slow

# Manual integration tests (requires running server and --run-manual flag)
pytest tests/ -v -m "manual" --run-manual

# All tests including slow ones (excluding manual)
pytest tests/ -v -m "not manual" --run-slow

# All tests with coverage
pytest tests/ --cov=app --cov-report=html
```

Manual testing requirements:
```bash
# Set up environment for manual tests
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# Start the server
uvicorn app.main:app --reload --port 8000

# Run manual tests (in another terminal)
pytest tests/ -v -m "manual" --run-manual
```

## Architecture

### Project Structure
```
backend/
├── app/
│   ├── main.py                  \# FastAPI app setup, middleware, top-level routers  
│   ├── dependencies.py          \# Global dependency injection functions  
│   │  
│   ├── api/                     \# API Layer: Request/Response handling (thin layer)  
│   │   ├── v1/  
│   │   │   ├── text\_processing.py      \# Endpoints for the main business logic  
│   │   │   ├── health.py                \# /health, /operations, system endpoints  
│   │   │   ├── auth.py                  \# Authentication endpoints (/auth/*)
│   │   │   └── deps.py                  \# API-specific dependencies  
│   │   └── internal/            \# Internal/admin endpoints  
│   │       ├── monitoring.py          \# /monitoring/\* endpoints  
│   │       ├── cache.py               \# /cache/\* and admin endpoints
│   │       └── resilience/           \# Resilience management endpoints
│   │  
│   ├── core/                    \# Application-wide setup & cross-cutting concerns  
│   │   ├── config.py              \# Centralized Pydantic settings  
│   │   └── exceptions.py          \# Custom exception classes  
│   │  
│   ├── services/ (Domain)       \# Business-specific, replaceable logic  
│   │   ├── text\_processor.py         \# Main text processing service (composes infrastructure)
│   │   └── response\_validator.py     \# AI response validation and security service
│   │  
│   ├── infrastructure/          \# Reusable, business-agnostic technical services  
│   │   ├── ai/                    \# AI provider abstractions, prompt building  
│   │   ├── cache/                 \# Caching logic and implementation  
│   │   ├── resilience/            \# Circuit breakers, retries, presets  
│   │   ├── security/              \# Auth, input/output validation logic  
│   │   └── monitoring/            \# Monitoring logic and metrics collection  
│   │  
│   └── schemas/                 \# Pydantic models (data contracts)  
│       ├── text\_processing.py      \# Request/Response models for text processing  
│       ├── health.py                \# Models for health check endpoints  
│       └── common.py                \# Shared response models (errors, success, pagination)
├── scripts/                 # Helper scripts
├── shared/                  # Shared models and utilities
├── tests/                   # Backend tests
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development dependencies
├── requirements-docker.txt  # Docker dependencies
├── Dockerfile               # Docker configuration
├── pytest.ini               # Pytest configuration
└── README.md                # This file
```

### Service Architecture

The application follows a service-oriented architecture with integrated caching:

- **FastAPI Application** (`main.py`): Handles HTTP requests, validation, and responses
- **Text Processor Service** (`text_processor.py`): Manages AI model interactions with caching integration
- **Cache Service** (`cache.py`): Multi-tiered caching system with intelligent key generation
- **Performance Monitor** (`monitoring.py`): Comprehensive cache performance tracking and metrics
- **Configuration** (`config.py`): Centralized settings management including cache configuration
- **Shared Models** (`../shared/models.py`): Pydantic models for data validation

### Error Handling

The application includes comprehensive error handling:

- **Global Exception Handler**: Catches unhandled exceptions
- **Validation Errors**: Automatic Pydantic validation
- **Service Errors**: Graceful handling of AI service failures
- **Logging**: Structured logging for debugging and monitoring

## Configuration

### AI Model Settings

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `AI_MODEL`: Gemini model to use (default: gemini-2.0-flash-exp)
- `AI_TEMPERATURE`: Model temperature for response variability (0.0-2.0)

### Server Settings

- `BACKEND_HOST`: Server host (default: 0.0.0.0)
- `BACKEND_PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: INFO)

### Cache Settings

- `REDIS_URL`: Redis connection URL (default: redis://redis:6379)
- `CACHE_TEXT_HASH_THRESHOLD`: Character threshold for text hashing (default: 1000)
- `CACHE_MEMORY_CACHE_SIZE`: Maximum items in memory cache (default: 100)
- `CACHE_COMPRESSION_THRESHOLD`: Size threshold for compression in bytes (default: 1000)
- `CACHE_COMPRESSION_LEVEL`: Compression level 1-9 (default: 6)
- `CACHE_DEFAULT_TTL`: Default cache TTL in seconds (default: 3600)

> **📖 Detailed Cache Documentation**: For comprehensive information about the multi-tiered caching system, architecture, monitoring, troubleshooting, and performance optimization, see [`docs/CACHE.md`](../docs/CACHE.md).

### CORS Settings

The application is configured to allow requests from:
- `http://localhost:8501` (Streamlit frontend)
- `http://frontend:8501` (Docker frontend)

## Monitoring and Health Checks

### Health Endpoint

The `/health` endpoint provides:
- Application status
- AI model availability
- Version information
- Timestamp

### Docker Health Check

The Docker container includes a health check that:
- Runs every 30 seconds
- Has a 30-second timeout
- Allows 3 retries
- Checks the `/health` endpoint

### Logging

Structured logging includes:
- Request processing times
- Error details and stack traces
- AI model interactions
- Application lifecycle events

## Performance Considerations

- **Async Processing**: All AI operations are asynchronous
- **Connection Pooling**: HTTP client connection reuse
- **Error Recovery**: Graceful handling of AI service failures
- **Resource Management**: Proper cleanup of resources

## Security

- **Input Validation**: Comprehensive Pydantic validation
- **Error Sanitization**: Safe error messages without sensitive data
- **CORS Configuration**: Restricted to known origins
- **Environment Variables**: Secure configuration management

## Troubleshooting

### Common Issues

1. **AI Service Unavailable**
   - Check `GEMINI_API_KEY` is set correctly
   - Verify API key has proper permissions
   - Check network connectivity

2. **Import Errors**
   - Ensure `PYTHONPATH` includes the project root
   - Verify all dependencies are installed

3. **CORS Errors**
   - Check frontend URL is in `allowed_origins`
   - Verify CORS middleware configuration

### Debug Mode

Enable debug mode for development:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

This provides:
- Detailed error messages
- Request/response logging
- Auto-reload on code changes

## Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Handle errors gracefully

## License

This project is licensed under the MIT License. 