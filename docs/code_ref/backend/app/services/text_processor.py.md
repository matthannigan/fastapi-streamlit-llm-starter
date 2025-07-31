---
sidebar_label: text_processor
---

# Text Processing Service with Resilience Integration

  file_path: `backend/app/services/text_processor.py`

This module provides a comprehensive text processing service that leverages AI models
to perform various natural language processing operations with built-in resilience,
caching, and security features.

The TextProcessorService class is the main entry point for all text processing operations,
supporting both individual requests and batch processing with concurrent execution.

## Key Features

- Multiple AI-powered text operations (summarization, sentiment analysis, etc.)
- Resilience patterns including circuit breakers, retries, and fallback responses
- Intelligent caching to reduce API calls and improve performance
- Input sanitization and output validation for security
- Batch processing with configurable concurrency limits
- Comprehensive logging and monitoring integration
- Graceful degradation when AI services are unavailable

## Supported Operations

- **SUMMARIZE**: Generate concise summaries of input text
- **SENTIMENT**: Analyze emotional tone and confidence levels
- **KEY_POINTS**: Extract the most important points from text
- **QUESTIONS**: Generate thoughtful questions about the content
- **QA**: Answer specific questions based on provided context

## Architecture

The service is built around a resilience-first design with multiple layers:

1. **Input Layer**: Sanitizes and validates all user inputs using PromptSanitizer
2. **Caching Layer**: Checks for cached responses before making AI calls
3. **AI Processing Layer**: Uses Pydantic AI agents with configurable models
4. **Resilience Layer**: Applies circuit breakers, retries, and timeouts
5. **Validation Layer**: Validates AI responses for safety and correctness
6. **Fallback Layer**: Provides degraded responses when services are unavailable

## Resilience Strategies

Different operations use tailored resilience strategies:
- **Aggressive**: Fast failures with immediate fallbacks (sentiment analysis)
- **Balanced**: Moderate retries with reasonable timeouts (most operations)
- **Conservative**: Extended retries for critical operations (Q&A)

## Security Features

- Prompt injection prevention through input sanitization
- Output validation to ensure safe AI responses
- Secure prompt templates with parameterized inputs
- Comprehensive logging for audit trails

## Usage

Basic usage requires a Settings instance and cache service:

```python
from app.core.config import Settings
from app.infrastructure.cache import AIResponseCache
from app.services.text_processor import TextProcessorService

settings = Settings()
cache = AIResponseCache(settings)
processor = TextProcessorService(settings, cache)

# Process individual request
request = TextProcessingRequest(
text="Your text here",
operation=TextProcessingOperation.SUMMARIZE
)
response = await processor.process_text(request)

# Process batch requests
batch_request = BatchTextProcessingRequest(
requests=[request1, request2, request3]
)
batch_response = await processor.process_batch(batch_request)
```

## Dependencies

- `pydantic-ai`: AI agent framework for model interactions
- `shared.models`: Pydantic models for request/response validation
- `app.infrastructure`: Resilience, caching, and AI infrastructure
- `app.config`: Application settings and configuration

## Exceptions

- **ServiceUnavailableError**: Raised when AI services are temporarily unavailable
- **TransientAIError**: Raised for retryable AI service errors
- **ValueError**: Raised for invalid operations or missing required parameters

## Thread Safety

The service is designed to be thread-safe and supports concurrent processing
through asyncio semaphores and proper resource management.

## Performance Considerations

- Caching significantly reduces redundant AI calls
- Batch processing optimizes concurrent request handling
- Configurable concurrency limits prevent resource exhaustion
- Circuit breakers prevent cascading failures

## Monitoring

The service provides comprehensive metrics and health checks:
- Processing times and success rates per operation
- Cache hit ratios and performance metrics
- Resilience pattern statistics (circuit breaker states, retry counts)
- Error rates and fallback usage patterns
