# Main FastAPI application for AI Text Processing with comprehensive resilience features.

This module serves as the primary entry point for the AI Text Processing API, providing
a robust and scalable FastAPI application with advanced text processing capabilities.
The application integrates AI-powered text analysis, comprehensive resilience patterns,
intelligent caching, and extensive monitoring to deliver a production-ready service.

The application architecture is designed for high availability and fault tolerance,
incorporating industry best practices for API design, error handling, and operational
monitoring. It supports graceful degradation when dependencies are unavailable and
provides comprehensive observability for production environments.

## Key Features

- **AI Text Processing**: Powered by Google Gemini API for advanced text analysis
including summarization, sentiment analysis, key point extraction, and Q&A
- **Resilience Infrastructure**: Circuit breaker patterns, retry mechanisms, and
failure detection to handle API failures and service degradation gracefully
- **Intelligent Caching**: Redis-backed response caching with compression, memory
tiering, and performance monitoring for improved response times and cost efficiency
- **Comprehensive Monitoring**: Health checks, performance metrics, circuit breaker
status, and cache analytics for operational visibility
- **Security**: API key authentication, CORS configuration, and input validation
to protect against unauthorized access and malicious inputs
- **Structured Logging**: Comprehensive logging with configurable levels for
debugging, monitoring, and audit trails

## API Endpoints

### Core Endpoints

- `GET /`: Root endpoint providing API information and version details
- `GET /health`: Comprehensive health check with AI, resilience, and cache status
- `GET /auth/status`: Authentication validation and API key verification

### Text Processing

- `POST /api/v1/text-processing/process`: Main text processing endpoint
- `POST /api/v1/text-processing/batch`: Batch text processing operations

### Monitoring & Administration

- `GET /api/internal/monitoring/*`: System metrics and performance data
- `GET /api/internal/cache/*`: Cache status, metrics, and management
- `GET /api/internal/resilience/*`: Circuit breaker status and configuration

## Configuration

The application uses environment-based configuration through the Settings class,
supporting deployment flexibility across different environments. Key configuration
areas include:

- AI model selection and API credentials
- Cache settings (Redis URL, TTL, compression)
- Resilience parameters (timeouts, retry counts, circuit breaker thresholds)
- Logging levels and output formats
- CORS origins and security settings
- Authentication tokens and access control

## Usage

### Development

python main.py

### Production

uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

### Docker

docker run -p 8000:8000 your-image:tag

## Environment Variables

### Required

- `GEMINI_API_KEY`: Google Gemini API key for text processing
- `API_KEYS`: Comma-separated list of valid API keys for authentication

### Optional

- `REDIS_URL`: Redis connection string for caching (defaults to memory-only)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS`: Allowed CORS origins for cross-origin requests

## Note

This application is designed for production use and includes comprehensive error
handling, monitoring, and resilience features. Ensure all required environment
variables are properly configured before deployment.
