"""
Text Processing Service with Resilience Integration

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
"""

import time
import asyncio
import uuid
import re
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging
from pydantic_ai import Agent
from app.schemas import TextProcessingOperation, TextProcessingRequest, TextProcessingResponse, SentimentResult, BatchTextProcessingRequest, BatchTextProcessingResponse, BatchTextProcessingItem, BatchTextProcessingStatus
from app.core.config import Settings
from app.infrastructure.ai import create_safe_prompt, sanitize_options, PromptSanitizer
from app.core.exceptions import ServiceUnavailableError, TransientAIError
from app.infrastructure.resilience import ai_resilience, ResilienceStrategy, with_balanced_resilience, with_aggressive_resilience, with_conservative_resilience
from app.services.response_validator import ResponseValidator


class TextProcessorService:
    """
    Comprehensive AI-powered text processing service with production-ready resilience and security features.
    
    This service provides a complete solution for AI-powered text analysis operations including
    summarization, sentiment analysis, key point extraction, question generation, and question-answering.
    It integrates seamlessly with infrastructure services to provide caching, resilience patterns,
    security validation, and performance monitoring.
    
    Attributes:
        settings: Application configuration containing AI model settings, resilience configuration,
                 and operational parameters for text processing operations
        cache_service: AI response cache service for storing and retrieving processed results,
                      improving performance and reducing API costs
        agent: PydanticAI agent configured for text processing operations with proper model integration
        sanitizer: Input sanitizer for security validation and prompt injection prevention
        response_validator: Output validator for security and quality assurance of AI responses
        ai_resilience: Resilience orchestrator providing circuit breakers, retry logic, and fallback responses
        concurrency_semaphore: Semaphore for controlling concurrent batch operations and resource management
        
    Public Methods:
        process_text(): Process single text processing requests with full resilience and caching
        process_batch(): Process multiple requests concurrently with automatic batch management
        _configure_resilience_strategies(): Configure operation-specific resilience strategies
        _get_fallback_response(): Provide fallback responses when AI services are unavailable
        _get_fallback_sentiment(): Generate neutral sentiment when sentiment analysis fails
        
    State Management:
        - Thread-safe for concurrent request processing across multiple workers
        - Maintains internal state for resilience patterns and circuit breaker status
        - Automatic resource management with proper cleanup and connection handling
        - Immutable configuration after initialization for consistent behavior
        - Integration with monitoring systems for operational visibility
        
    Behavior:
        - Performs input sanitization on all user-provided text before processing
        - Checks cache for existing responses before making AI API calls
        - Applies operation-specific resilience strategies with circuit breakers and retry logic
        - Validates AI responses for security threats and quality issues
        - Stores successful responses in cache for future retrieval
        - Provides fallback responses when AI services are unavailable
        - Logs comprehensive processing metrics and security events
        - Supports batch processing with configurable concurrency limits
        
    Examples:
        >>> # Basic service initialization
        >>> from app.services import TextProcessorService
        >>> from app.core.config import settings
        >>> from app.infrastructure.cache import get_ai_cache_service
        >>> 
        >>> cache_service = get_ai_cache_service()
        >>> processor = TextProcessorService(settings, cache_service)
        
        >>> # Single operation processing
        >>> from shared.models import TextProcessingRequest, TextProcessingOperation
        >>> 
        >>> request = TextProcessingRequest(
        ...     text="Sample text for analysis",
        ...     operation=TextProcessingOperation.SUMMARIZE,
        ...     options={"max_length": 100}
        ... )
        >>> response = await processor.process_text(request)
        >>> print(f"Summary: {response.result}")
        
        >>> # Question-answering with required question parameter
        >>> qa_request = TextProcessingRequest(
        ...     text="Document content to analyze",
        ...     operation=TextProcessingOperation.QA,
        ...     question="What are the main conclusions?"
        ... )
        >>> qa_response = await processor.process_text(qa_request)
        >>> print(f"Answer: {qa_response.result}")
        
        >>> # Batch processing with automatic concurrency control
        >>> from shared.models import BatchTextProcessingRequest
        >>> 
        >>> batch_request = BatchTextProcessingRequest(
        ...     requests=[
        ...         TextProcessingRequest(text="Text 1", operation="summarize"),
        ...         TextProcessingRequest(text="Text 2", operation="sentiment"),
        ...         TextProcessingRequest(text="Text 3", operation="key_points")
        ...     ],
        ...     batch_id="analysis_batch_001"
        ... )
        >>> batch_response = await processor.process_batch(batch_request)
        >>> print(f"Processed {batch_response.completed_items} of {batch_response.total_items} items")
    """

    def __init__(self, settings: Settings, cache: 'AIResponseCache'):
        """
        Initialize the text processor with AI agent, resilience patterns, and security validation.
        
        Args:
            settings: Application settings instance containing AI model configuration,
                     resilience parameters, and operational settings for text processing
            cache: AI response cache service instance for storing and retrieving processed results,
                  improving performance and reducing redundant API calls
        
        Behavior:
            - Initializes PydanticAI agent with configured model and temperature settings
            - Sets up input sanitizer for security validation and prompt injection prevention
            - Configures response validator for output security and quality assurance
            - Establishes resilience orchestrator with operation-specific strategies
            - Creates concurrency semaphore for batch processing resource management
            - Registers operation-specific resilience strategies from configuration
            - Prepares logging infrastructure for comprehensive request tracking
            
        Raises:
            ConfigurationError: If required settings are missing or invalid
            InfrastructureError: If cache service initialization fails
            ValueError: If AI model configuration is invalid
            
        Examples:
            >>> # Basic initialization with default settings
            >>> processor = TextProcessorService(settings, cache_service)
            
            >>> # Initialization with custom resilience configuration
            >>> custom_settings = Settings(
            ...     gemini_api_key="your-api-key",
            ...     ai_model="gemini-2.0-flash-exp",
            ...     ai_temperature=0.7,
            ...     BATCH_AI_CONCURRENCY_LIMIT=10
            ... )
            >>> processor = TextProcessorService(custom_settings, cache_service)
        """
        ...

    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """
        Process text with caching and resilience support.
        """
        ...

    async def process_batch(self, batch_request: BatchTextProcessingRequest) -> BatchTextProcessingResponse:
        """
        Process a batch of text processing requests concurrently with resilience.
        """
        ...

    def get_resilience_health(self) -> Dict[str, Any]:
        """
        Get resilience health status for this service.
        """
        ...

    def get_resilience_metrics(self) -> Dict[str, Any]:
        """
        Get resilience metrics for this service.
        """
        ...
