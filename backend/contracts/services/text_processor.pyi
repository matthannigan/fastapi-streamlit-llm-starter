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

The service integrates with infrastructure monitoring systems:
- Processing times and success rates logged per operation
- Cache hit ratios tracked through cache infrastructure
- Resilience pattern statistics available via Internal API (/internal/resilience/*)
- Error rates and fallback usage logged for operational visibility

## How to Access Resilience Data

1. HTTP Access (recommended): Use Internal API endpoints
- GET /internal/resilience/health - Health status
- GET /internal/resilience/metrics - Performance metrics
- GET /internal/resilience/circuit-breakers - Circuit breaker states

2. Programmatic Access: Direct orchestrator injection
```python
from app.infrastructure.resilience import ai_resilience

health = ai_resilience.get_health_status()
metrics = ai_resilience.get_all_metrics()
```
"""

import time
import asyncio
import uuid
from typing import Dict, Any, List, Union, TYPE_CHECKING, Optional
import logging
from pydantic_ai import Agent
from app.schemas import TextProcessingOperation, TextProcessingRequest, TextProcessingResponse, SentimentResult, BatchTextProcessingRequest, BatchTextProcessingResponse, BatchTextProcessingItem, BatchTextProcessingStatus
from app.core.config import Settings
from app.infrastructure.ai import create_safe_prompt, sanitize_options, PromptSanitizer
from app.core.exceptions import ServiceUnavailableError, TransientAIError, AIServiceException, ValidationError, InfrastructureError
from tenacity import RetryError
from app.infrastructure.resilience import ai_resilience, ResilienceStrategy, with_balanced_resilience, with_aggressive_resilience, with_conservative_resilience
from app.services.response_validator import ResponseValidator

OPERATION_CONFIG: Dict[TextProcessingOperation, Dict[str, Any]] = {TextProcessingOperation.SUMMARIZE: {'handler': '_summarize_text_with_resilience', 'resilience_strategy': 'balanced', 'cache_ttl': 7200, 'fallback_type': 'string', 'requires_question': False, 'response_field': 'result', 'accepts_options': True, 'description': 'Generate concise summaries of input text'}, TextProcessingOperation.SENTIMENT: {'handler': '_analyze_sentiment_with_resilience', 'resilience_strategy': 'aggressive', 'cache_ttl': 3600, 'fallback_type': 'sentiment_result', 'requires_question': False, 'response_field': 'sentiment', 'accepts_options': False, 'description': 'Analyze emotional tone and confidence levels'}, TextProcessingOperation.KEY_POINTS: {'handler': '_extract_key_points_with_resilience', 'resilience_strategy': 'balanced', 'cache_ttl': 5400, 'fallback_type': 'list', 'requires_question': False, 'response_field': 'key_points', 'accepts_options': True, 'description': 'Extract main ideas and important concepts'}, TextProcessingOperation.QUESTIONS: {'handler': '_generate_questions_with_resilience', 'resilience_strategy': 'balanced', 'cache_ttl': 3600, 'fallback_type': 'list', 'requires_question': False, 'response_field': 'questions', 'accepts_options': True, 'description': 'Generate questions about the text content'}, TextProcessingOperation.QA: {'handler': '_answer_question_with_resilience', 'resilience_strategy': 'conservative', 'cache_ttl': 1800, 'fallback_type': 'string', 'requires_question': True, 'response_field': 'result', 'accepts_options': False, 'description': 'Answer specific questions about the text'}}


class TextProcessorService:
    """
    Comprehensive AI-powered text processing service with production-ready resilience and security features.
    
    This domain service demonstrates best practices for integrating AI operations with infrastructure
    services including caching, resilience patterns, security validation, and monitoring. It provides
    complete text analysis operations (summarization, sentiment analysis, key point extraction,
    question generation, and question-answering) as an educational example of domain service architecture.
    
    **Architectural Role**: This is a **domain service example** showcasing how to build business-specific
    functionality on top of infrastructure services. When customizing this template, replace this service
    with your own domain logic while maintaining the infrastructure integration patterns demonstrated here.
    
    Attributes:
        settings: Application configuration containing AI model settings (model name, API keys, temperature),
                  resilience configuration (retry attempts, circuit breaker thresholds), and operational
                  parameters (batch concurrency limits, cache TTLs) for text processing operations
        cache_service: AI-capable cache service (AIResponseCache or InMemoryCache) for storing and
                       retrieving processed results with operation-specific TTLs. Automatically falls back
                       to InMemoryCache when Redis is unavailable (CACHE_PRESET=disabled)
        agent: PydanticAI agent configured with Gemini model for text processing operations, initialized
               with system prompt and model-specific settings (temperature, max_tokens)
        sanitizer: PromptSanitizer instance for input security validation and prompt injection prevention,
                   applies comprehensive sanitization to all user-provided text before AI processing
        response_validator: ResponseValidator instance for output security and quality assurance, validates
                            AI responses for harmful content, injection attempts, and quality issues
        ai_resilience: Global resilience orchestrator (singleton) providing circuit breakers, retry logic,
                       and fallback responses across all text processing operations
        concurrency_semaphore: Asyncio semaphore limiting concurrent batch operations to BATCH_AI_CONCURRENCY_LIMIT,
                               prevents resource exhaustion during high-volume batch processing
    
    Public Methods:
        process_text(): Process single text processing requests with comprehensive resilience, caching,
                        input sanitization, AI processing, output validation, and fallback handling
        process_batch(): Process multiple requests concurrently with automatic concurrency control,
                         individual request isolation, and aggregate success/failure tracking
    
    Private Methods:
        _register_operations(): Register text processing operations with resilience service using
                                operation-specific strategies (aggressive, balanced, conservative)
        _validate_operation_registry(): Validate operation registry consistency at initialization,
                                        ensuring all operations have valid handlers and configuration
        _dispatch_operation(): Central routing mechanism for operation execution, dispatches requests
                               to appropriate handler methods based on operation registry
        _prepare_handler_arguments(): Build argument dictionaries for handler methods based on operation
                                      requirements (text, options, question parameters)
        _set_response_field(): Route operation results to appropriate response fields using registry
                               configuration (result, sentiment, key_points, questions)
        _get_fallback_response(): Provide fallback responses when AI services are unavailable, attempts
                                  cache retrieval first, then generates appropriate default responses
        _get_default_fallback(): Generate default fallback responses based on operation type from registry
                                 (string, list, or SentimentResult based on operation requirements)
        _get_fallback_sentiment(): Generate neutral sentiment result when sentiment analysis fails
        _build_cache_key(): Build cache keys using domain-specific logic, embeds question parameter in
                            options dictionary before delegating to infrastructure cache service
        _get_ttl_for_operation(): Get operation-specific TTL values for cache storage from registry
        Handler methods: _summarize_text_with_resilience(), _analyze_sentiment_with_resilience(),
                        _extract_key_points_with_resilience(), _generate_questions_with_resilience(),
                        _answer_question_with_resilience() - Apply resilience decorators to core operations
        Core AI methods: _summarize_text(), _analyze_sentiment(), _extract_key_points(),
                        _generate_questions(), _answer_question() - Implement AI processing logic
    
    State Management:
        - **Thread Safety**: Service is fully thread-safe for concurrent request processing across multiple
          asyncio workers. Uses immutable configuration after initialization and delegates state management
          to infrastructure services (cache, resilience orchestrator) which handle their own concurrency
        - **Resilience State**: Circuit breaker states and retry counters maintained by global ai_resilience
          orchestrator (singleton), shared across all service instances for consistent failure detection
        - **Cache State**: Cache entries managed by cache_service with operation-specific TTLs (30 minutes to
          2 hours), automatic expiration, and Redis persistence with memory fallback for availability
        - **Resource Management**: Automatic cleanup of AI agent connections, cache connections handled by
          infrastructure layer, no manual cleanup required after service use
        - **Immutable Configuration**: Settings, cache service, and agent configuration are immutable after
          initialization, ensuring consistent behavior across all requests and preventing configuration drift
        - **Monitoring Integration**: Processing metrics (times, success rates, cache hits) logged via
          standard logging, resilience metrics accessible via Internal API endpoints (/internal/resilience/*)
    
    Behavior:
        - **Input Processing Pipeline**: Sanitizes all user-provided text, options, and questions using
          PromptSanitizer before any AI processing to prevent prompt injection attacks
        - **Cache-First Strategy**: Checks cache for existing responses before making AI API calls, returns
          cached response immediately if found (with cache_hit=True in metadata)
        - **Operation Dispatch**: Routes requests to appropriate handler methods based on operation type using
          centralized registry, validates operation support before processing
        - **Resilience Application**: Applies operation-specific resilience strategies (aggressive for sentiment,
          balanced for summarize/key_points/questions, conservative for Q&A) with circuit breakers and retries
        - **AI Processing**: Invokes PydanticAI agent with secure prompt templates, handles model-specific
          response formats, propagates errors for proper resilience handling
        - **Response Validation**: Validates all AI responses for security threats (injection attempts, harmful
          content) and quality issues before returning to caller
        - **Cache Storage**: Stores successful responses (including fallback responses) in cache with operation-
          specific TTLs (30 minutes for Q&A, 2 hours for summaries) for future retrieval
        - **Fallback Handling**: Provides graceful degradation when AI services unavailable, attempts cache
          retrieval first, generates appropriate default responses if cache miss
        - **Batch Processing**: Processes multiple requests concurrently with semaphore-based concurrency
          limiting, isolates failures per request, returns aggregate results with success/failure counts
        - **Comprehensive Logging**: Logs processing start/end with unique IDs, operation types, processing
          times, cache hits, fallback usage, and errors for operational monitoring and debugging
    
    Examples:
        >>> # Basic service initialization with infrastructure services
        >>> from app.services.text_processor import TextProcessorService
        >>> from app.core.config import Settings
        >>> from app.infrastructure.cache import AIResponseCache
        >>>
        >>> settings = Settings()
        >>> cache = AIResponseCache(settings)
        >>> processor = TextProcessorService(settings, cache)
    
        >>> # Single operation processing - summarization
        >>> from app.schemas import TextProcessingRequest, TextProcessingOperation
        >>>
        >>> request = TextProcessingRequest(
        ...     text="Sample text for analysis",
        ...     operation=TextProcessingOperation.SUMMARIZE,
        ...     options={"max_length": 100}
        ... )
        >>> response = await processor.process_text(request)
        >>> print(f"Summary: {response.result}")
        >>> print(f"Cached: {response.cache_hit}")
        >>> print(f"Time: {response.processing_time:.2f}s")
    
        >>> # Sentiment analysis (no options required)
        >>> sentiment_request = TextProcessingRequest(
        ...     text="This product exceeded all my expectations!",
        ...     operation=TextProcessingOperation.SENTIMENT
        ... )
        >>> sentiment_response = await processor.process_text(sentiment_request)
        >>> print(f"Sentiment: {sentiment_response.sentiment.sentiment}")
        >>> print(f"Confidence: {sentiment_response.sentiment.confidence:.2f}")
    
        >>> # Question-answering with required question parameter
        >>> qa_request = TextProcessingRequest(
        ...     text="The company reported strong Q3 earnings with 25% revenue growth.",
        ...     operation=TextProcessingOperation.QA,
        ...     question="What were the Q3 results?"
        ... )
        >>> qa_response = await processor.process_text(qa_request)
        >>> print(f"Answer: {qa_response.result}")
    
        >>> # Batch processing with automatic concurrency control
        >>> from app.schemas import BatchTextProcessingRequest
        >>>
        >>> batch_request = BatchTextProcessingRequest(
        ...     requests=[
        ...         TextProcessingRequest(text="Text 1", operation=TextProcessingOperation.SUMMARIZE),
        ...         TextProcessingRequest(text="Text 2", operation=TextProcessingOperation.SENTIMENT),
        ...         TextProcessingRequest(text="Text 3", operation=TextProcessingOperation.KEY_POINTS,
        ...                             options={"max_points": 5})
        ...     ],
        ...     batch_id="analysis_batch_001"
        ... )
        >>> batch_response = await processor.process_batch(batch_request)
        >>> print(f"Completed: {batch_response.completed}/{batch_response.total_requests}")
        >>> print(f"Failed: {batch_response.failed}")
        >>> print(f"Total time: {batch_response.total_processing_time:.2f}s")
    
        >>> # Handling degraded service with fallback responses
        >>> response = await processor.process_text(request)
        >>> if response.metadata.get("service_status") == "degraded":
        ...     print("Service degraded - using fallback response")
        ...     print(f"Fallback used: {response.metadata.get('fallback_used')}")
    
        >>> # Accessing resilience data via Internal API (not through service methods)
        >>> # Use HTTP endpoints: GET /internal/resilience/health
        >>> #                     GET /internal/resilience/metrics
        >>> # Or direct orchestrator access:
        >>> from app.infrastructure.resilience import ai_resilience
        >>> health = ai_resilience.get_health_status()
        >>> metrics = ai_resilience.get_all_metrics()
    """

    def __init__(self, settings: Settings, cache: Union['AIResponseCache', 'InMemoryCache'], sanitizer: Optional[PromptSanitizer] = None, response_validator: Optional[ResponseValidator] = None, ai_resilience: Optional['AIResilienceOrchestrator'] = None):
        """
        Initialize the text processor with AI agent, resilience patterns, and security validation.
        
        Args:
            settings: Application settings instance containing AI model configuration,
                      resilience parameters, and operational settings for text processing
            cache: AI-capable cache service (AIResponseCache or InMemoryCache) for storing and
                   retrieving processed results. InMemoryCache is used as fallback when Redis is
                   unavailable (CACHE_PRESET=disabled)
            sanitizer: Optional PromptSanitizer for testing (defaults to new instance).
                      Can be injected for test isolation and mock validation.
            response_validator: Optional ResponseValidator for testing (defaults to new instance).
                      Can be injected for test isolation and mock validation.
            ai_resilience: Optional resilience orchestrator for testing (defaults to global singleton).
                      Can be injected to control circuit breaker states and retry behavior in tests.
        
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
        
            >>> # Testing with injected dependencies
            >>> mock_resilience = create_test_resilience_mock()
            >>> processor = TextProcessorService(
            ...     settings, cache_service,
            ...     ai_resilience=mock_resilience
            ... )
        """
        ...

    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """
        Process a single text processing request with comprehensive resilience, caching, and security features.
        
        This is the main entry point for all text processing operations. It orchestrates input sanitization,
        cache lookups, AI processing with resilience patterns, response validation, and cache storage. The
        method provides graceful degradation through fallback responses when AI services are unavailable.
        
        Args:
            request: Text processing request containing:
                - text: str, input text to process (1-50,000 characters)
                - operation: TextProcessingOperation enum, one of [SUMMARIZE, SENTIMENT, KEY_POINTS, QUESTIONS, QA]
                - options: Optional[dict], operation-specific parameters (max_length, max_points, num_questions)
                - question: Optional[str], required for QA operation, ignored for others
        
        Returns:
            TextProcessingResponse containing:
                - operation: str, the operation that was performed
                - processing_time: float, total processing time in seconds
                - cache_hit: bool, True if result retrieved from cache, False if processed
                - metadata: dict, processing metadata including word_count and optional service_status
                - result: Optional[str], text result for SUMMARIZE and QA operations
                - sentiment: Optional[SentimentResult], result for SENTIMENT operation
                - key_points: Optional[List[str]], result for KEY_POINTS operation
                - questions: Optional[List[str]], result for QUESTIONS operation
        
        Raises:
            ValueError: If operation is not supported or question is missing for QA operation
            ServiceUnavailableError: If AI service is unavailable and no cached fallback exists
            TransientAIError: For retryable AI service errors during processing
            ConfigurationError: If service configuration is invalid
        
        Behavior:
            - Generates unique processing ID for request tracing and logging
            - Sanitizes all input text and options using PromptSanitizer for security
            - Checks cache for existing response before making AI calls
            - Returns cached response immediately if found (with cache_hit=True)
            - Dispatches operation to appropriate handler based on operation registry
            - Applies operation-specific resilience strategies (aggressive, balanced, conservative)
            - Validates AI responses for security threats and quality issues
            - Provides fallback responses when AI services unavailable (marks as degraded)
            - Stores successful responses in cache with operation-specific TTLs
            - Logs comprehensive metrics including processing times and status
            - Updates processing time in response before returning
        
        Examples:
            >>> # Basic summarization
            >>> request = TextProcessingRequest(
            ...     text="Long article text here...",
            ...     operation=TextProcessingOperation.SUMMARIZE,
            ...     options={"max_length": 150}
            ... )
            >>> response = await processor.process_text(request)
            >>> print(f"Summary: {response.result}")
            >>> print(f"Cached: {response.cache_hit}")
            >>> print(f"Time: {response.processing_time:.2f}s")
        
            >>> # Sentiment analysis (no options)
            >>> request = TextProcessingRequest(
            ...     text="This product is amazing!",
            ...     operation=TextProcessingOperation.SENTIMENT
            ... )
            >>> response = await processor.process_text(request)
            >>> print(f"Sentiment: {response.sentiment.sentiment}")
            >>> print(f"Confidence: {response.sentiment.confidence}")
        
            >>> # Question answering with required question
            >>> request = TextProcessingRequest(
            ...     text="The company reported strong Q3 earnings...",
            ...     operation=TextProcessingOperation.QA,
            ...     question="What were the Q3 results?"
            ... )
            >>> response = await processor.process_text(request)
            >>> print(f"Answer: {response.result}")
        
            >>> # Handling degraded service (fallback response)
            >>> response = await processor.process_text(request)
            >>> if response.metadata.get("service_status") == "degraded":
            ...     print("Using fallback response due to service unavailability")
            ...     print(f"Fallback used: {response.metadata.get('fallback_used')}")
        """
        ...

    async def process_batch(self, batch_request: BatchTextProcessingRequest) -> BatchTextProcessingResponse:
        """
        Process multiple text processing requests concurrently with automatic concurrency control and resilience.
        
        This method enables efficient batch processing of text operations by executing multiple requests
        concurrently with configurable limits. Each request is processed through the full resilience
        pipeline including caching, sanitization, and fallback handling. Failed requests are isolated
        and don't affect successful ones.
        
        Args:
            batch_request: Batch processing request containing:
                - requests: List[TextProcessingRequest], 1-1000 requests to process concurrently
                - batch_id: Optional[str], identifier for tracking (auto-generated if not provided)
        
        Returns:
            BatchTextProcessingResponse containing:
                - batch_id: str, unique identifier for this batch
                - total_requests: int, total number of requests in batch
                - completed: int, number of successfully completed requests
                - failed: int, number of failed requests
                - results: List[BatchTextProcessingItem], individual results with:
                    - request_index: int, original position in batch
                    - status: BatchTextProcessingStatus, COMPLETED or FAILED
                    - response: Optional[TextProcessingResponse], result if successful
                    - error: Optional[str], error message if failed
                - total_processing_time: float, total batch processing time in seconds
        
        Raises:
            ValueError: If batch request is empty or exceeds maximum batch size
            ConfigurationError: If concurrency limit is invalid
        
        Behavior:
            - Generates unique batch processing ID for tracking and logging
            - Creates batch_id if not provided (format: "batch_TIMESTAMP")
            - Uses asyncio.Semaphore to limit concurrent processing (BATCH_AI_CONCURRENCY_LIMIT)
            - Processes each request through process_text() with full resilience
            - Isolates failures so one failed request doesn't affect others
            - Catches ServiceUnavailableError for graceful degradation per request
            - Captures all exceptions and converts to BatchTextProcessingItem with error
            - Uses asyncio.gather() with return_exceptions=True for parallel execution
            - Validates all results are BatchTextProcessingItem instances
            - Calculates success/failure counts and total processing time
            - Logs batch start, end, and comprehensive metrics
            - Returns results in original request order (preserves request_index)
        
        Examples:
            >>> # Basic batch processing with multiple operations
            >>> batch_request = BatchTextProcessingRequest(
            ...     requests=[
            ...         TextProcessingRequest(text="Text 1", operation="summarize"),
            ...         TextProcessingRequest(text="Text 2", operation="sentiment"),
            ...         TextProcessingRequest(text="Text 3", operation="key_points")
            ...     ],
            ...     batch_id="analysis_batch_001"
            ... )
            >>> batch_response = await processor.process_batch(batch_request)
            >>> print(f"Completed: {batch_response.completed}/{batch_response.total_requests}")
            >>> print(f"Failed: {batch_response.failed}")
            >>> print(f"Total time: {batch_response.total_processing_time:.2f}s")
        
            >>> # Processing results and handling failures
            >>> for item in batch_response.results:
            ...     if item.status == BatchTextProcessingStatus.COMPLETED:
            ...         print(f"Request {item.request_index}: Success")
            ...         print(f"  Result: {item.response.result or item.response.sentiment}")
            ...     else:
            ...         print(f"Request {item.request_index}: Failed - {item.error}")
        
            >>> # Auto-generated batch_id
            >>> batch_request = BatchTextProcessingRequest(
            ...     requests=[req1, req2, req3]
            ... )
            >>> batch_response = await processor.process_batch(batch_request)
            >>> print(f"Batch ID: {batch_response.batch_id}")  # e.g., "batch_1640995200"
        
            >>> # Checking individual request status
            >>> successful_results = [
            ...     item.response for item in batch_response.results
            ...     if item.status == BatchTextProcessingStatus.COMPLETED
            ... ]
            >>> failed_indices = [
            ...     item.request_index for item in batch_response.results
            ...     if item.status == BatchTextProcessingStatus.FAILED
            ... ]
        """
        ...
