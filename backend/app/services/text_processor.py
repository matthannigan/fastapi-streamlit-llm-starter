"""Text Processing Service with Resilience Integration

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

# Only import for type checking to avoid circular dependencies
if TYPE_CHECKING:
    from app.infrastructure.cache.redis_ai import AIResponseCache
    from app.infrastructure.cache.memory import InMemoryCache
    from app.infrastructure.resilience.orchestrator import AIResilienceOrchestrator

from app.schemas import (
    TextProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    SentimentResult,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchTextProcessingItem,
    BatchTextProcessingStatus
)
from app.core.config import Settings
from app.infrastructure.ai import create_safe_prompt, sanitize_options, PromptSanitizer # Enhanced import
from app.core.exceptions import (
    ServiceUnavailableError,
    TransientAIError,
    AIServiceException,
    ValidationError,
    InfrastructureError
)
from tenacity import RetryError
from app.infrastructure.resilience import (
    ai_resilience,
    ResilienceStrategy,
    with_balanced_resilience,
    with_aggressive_resilience,
    with_conservative_resilience,
)
from app.services.response_validator import ResponseValidator

logger = logging.getLogger(__name__)


# Operation Registry - Centralized configuration for all text processing operations
OPERATION_CONFIG: Dict[TextProcessingOperation, Dict[str, Any]] = {
    TextProcessingOperation.SUMMARIZE: {
        "handler": "_summarize_text_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 7200,  # 2 hours
        "fallback_type": "string",
        "requires_question": False,
        "response_field": "result",
        "accepts_options": True,
        "description": "Generate concise summaries of input text"
    },
    TextProcessingOperation.SENTIMENT: {
        "handler": "_analyze_sentiment_with_resilience",
        "resilience_strategy": "aggressive",
        "cache_ttl": 3600,  # 1 hour
        "fallback_type": "sentiment_result",
        "requires_question": False,
        "response_field": "sentiment",
        "accepts_options": False,
        "description": "Analyze emotional tone and confidence levels"
    },
    TextProcessingOperation.KEY_POINTS: {
        "handler": "_extract_key_points_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 5400,  # 1.5 hours
        "fallback_type": "list",
        "requires_question": False,
        "response_field": "key_points",
        "accepts_options": True,
        "description": "Extract main ideas and important concepts"
    },
    TextProcessingOperation.QUESTIONS: {
        "handler": "_generate_questions_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 3600,  # 1 hour
        "fallback_type": "list",
        "requires_question": False,
        "response_field": "questions",
        "accepts_options": True,
        "description": "Generate questions about the text content"
    },
    TextProcessingOperation.QA: {
        "handler": "_answer_question_with_resilience",
        "resilience_strategy": "conservative",
        "cache_ttl": 1800,  # 30 minutes
        "fallback_type": "string",
        "requires_question": True,
        "response_field": "result",
        "accepts_options": False,
        "description": "Answer specific questions about the text"
    },
}


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

    def __init__(
        self,
        settings: Settings,
        cache: Union["AIResponseCache", "InMemoryCache"],
        sanitizer: Optional[PromptSanitizer] = None,
        response_validator: Optional[ResponseValidator] = None,
        ai_resilience: Optional["AIResilienceOrchestrator"] = None,
    ):
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
        self.settings = settings
        self.cache = cache

        # During tests with mocked AI agent, we don't need the actual API key
        # Check if we're in a test environment by looking for pytest or mock_ai_agent
        import sys
        is_testing = "pytest" in sys.modules

        if not self.settings.gemini_api_key and not is_testing:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.agent = Agent(
            model=self.settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )

        # Use provided cache service
        self.cache_service = cache

        # Use provided dependencies or create defaults (dependency injection pattern)
        self.sanitizer = sanitizer if sanitizer is not None else PromptSanitizer()
        self.response_validator = response_validator if response_validator is not None else ResponseValidator()

        # For ai_resilience, use provided parameter or module-level singleton
        # The module-level ai_resilience (imported at top) respects test patches
        if ai_resilience is not None:
            self._ai_resilience = ai_resilience
        else:
            # Access module-level ai_resilience through current module
            import sys
            current_module = sys.modules[__name__]
            self._ai_resilience = getattr(current_module, 'ai_resilience')

        # Register operations with resilience service
        self._register_operations()

        # Validate operation registry
        self._validate_operation_registry()

    def _get_operation_config(self, operation: TextProcessingOperation) -> Dict[str, Any]:
        """
        Get complete configuration for an operation.

        Args:
            operation: The operation to get configuration for

        Returns:
            Configuration dictionary with all metadata

        Raises:
            ValueError: If operation not in registry

        Examples:
            >>> config = self._get_operation_config(TextProcessingOperation.SUMMARIZE)
            >>> print(config["resilience_strategy"])  # "balanced"
        """
        if operation not in OPERATION_CONFIG:
            raise ValueError(f"Operation {operation} not found in registry")
        return OPERATION_CONFIG[operation]

    def _get_handler_name(self, operation: TextProcessingOperation) -> str:
        """
        Get handler method name for operation.

        Args:
            operation: The operation to get handler for

        Returns:
            Handler method name (string)

        Examples:
            >>> handler_name = self._get_handler_name(TextProcessingOperation.SUMMARIZE)
            >>> # Returns: "_summarize_text_with_resilience"
        """
        return self._get_operation_config(operation)["handler"]

    def _get_resilience_strategy(self, operation: TextProcessingOperation) -> str:
        """
        Get resilience strategy name for operation.

        Args:
            operation: The operation to get strategy for

        Returns:
            Strategy name: "aggressive", "balanced", or "conservative"

        Examples:
            >>> strategy = self._get_resilience_strategy(TextProcessingOperation.SENTIMENT)
            >>> # Returns: "aggressive"
        """
        return self._get_operation_config(operation)["resilience_strategy"]

    def _get_cache_ttl_from_registry(self, operation: TextProcessingOperation) -> int:
        """
        Get cache TTL for operation from registry.

        Args:
            operation: The operation to get TTL for

        Returns:
            TTL in seconds

        Examples:
            >>> ttl = self._get_cache_ttl_from_registry(TextProcessingOperation.SUMMARIZE)
            >>> # Returns: 7200 (2 hours)
        """
        return self._get_operation_config(operation)["cache_ttl"]

    def _get_fallback_type(self, operation: TextProcessingOperation) -> str:
        """
        Get fallback response type for operation.

        Args:
            operation: The operation to get fallback type for

        Returns:
            Fallback type: "string", "list", "sentiment_result"

        Examples:
            >>> fallback_type = self._get_fallback_type(TextProcessingOperation.KEY_POINTS)
            >>> # Returns: "list"
        """
        return self._get_operation_config(operation)["fallback_type"]

    def _get_response_field(self, operation: TextProcessingOperation) -> str:
        """
        Get response field name for operation.

        Args:
            operation: The operation to get response field for

        Returns:
            Field name in TextProcessingResponse

        Examples:
            >>> field = self._get_response_field(TextProcessingOperation.SENTIMENT)
            >>> # Returns: "sentiment"
        """
        return self._get_operation_config(operation)["response_field"]

    def _validate_operation_registry(self) -> None:
        """
        Validate operation registry consistency at initialization.

        Validates:
            - All enum operations have registry entries
            - Handler methods exist on service instance
            - Resilience strategies are valid
            - TTL values are positive integers
            - Response fields match TextProcessingResponse model

        Raises:
            ConfigurationError: If registry is invalid

        Called from:
            __init__() method during service initialization
        """
        from app.core.exceptions import ConfigurationError

        # Check all enum operations have registry entries
        for operation in TextProcessingOperation:
            if operation not in OPERATION_CONFIG:
                raise ConfigurationError(
                    f"Operation {operation.value} missing from OPERATION_CONFIG registry"
                )

        # Validate each registry entry
        for operation, config in OPERATION_CONFIG.items():
            # Validate handler method exists
            handler_name = config["handler"]
            if not hasattr(self, handler_name):
                raise ConfigurationError(
                    f"Handler method '{handler_name}' for operation {operation.value} "
                    f"not found on {self.__class__.__name__}"
                )

            # Validate resilience strategy
            strategy = config["resilience_strategy"]
            valid_strategies = {"aggressive", "balanced", "conservative"}
            if strategy not in valid_strategies:
                raise ConfigurationError(
                    f"Invalid resilience strategy '{strategy}' for operation {operation.value}. "
                    f"Must be one of: {valid_strategies}"
                )

            # Validate TTL
            ttl = config["cache_ttl"]
            if not isinstance(ttl, int) or ttl <= 0:
                raise ConfigurationError(
                    f"Invalid cache TTL {ttl} for operation {operation.value}. "
                    f"Must be positive integer"
                )

            # Validate response field
            response_field = config["response_field"]
            valid_fields = {"result", "sentiment", "key_points", "questions"}
            if response_field not in valid_fields:
                raise ConfigurationError(
                    f"Invalid response field '{response_field}' for operation {operation.value}. "
                    f"Must be one of: {valid_fields}"
                )

        logger.info(
            f"Operation registry validated successfully: {len(OPERATION_CONFIG)} operations registered"
        )

    def _register_operations(self) -> None:
        """
        Register text processing operations with resilience service using registry.

        Uses the operation registry to look up resilience strategies and register
        all operations with the resilience service. Supports settings overrides
        for custom strategy configuration.
        """
        # Map operation enum values to resilience operation names
        operation_name_map = {
            TextProcessingOperation.SUMMARIZE: "summarize_text",
            TextProcessingOperation.SENTIMENT: "analyze_sentiment",
            TextProcessingOperation.KEY_POINTS: "extract_key_points",
            TextProcessingOperation.QUESTIONS: "generate_questions",
            TextProcessingOperation.QA: "answer_question",
        }

        for operation, operation_name in operation_name_map.items():
            # Get strategy from registry
            default_strategy = self._get_resilience_strategy(operation)

            # Allow settings override (e.g., summarize_resilience_strategy)
            setting_name = f"{operation.value}_resilience_strategy"
            strategy_name = getattr(self.settings, setting_name, default_strategy)

            try:
                # Convert string strategy to enum
                strategy = ResilienceStrategy(strategy_name)
                self._ai_resilience.register_operation(operation_name, strategy)
                logger.info(f"Registered operation '{operation_name}' with strategy '{strategy_name}'")
            except ValueError:
                logger.warning(f"Unknown strategy '{strategy_name}' for operation '{operation_name}', using {default_strategy}")
                # Fall back to registry default
                strategy = ResilienceStrategy(default_strategy)
                self._ai_resilience.register_operation(operation_name, strategy)

    async def _dispatch_operation(
            self,
            operation: TextProcessingOperation,
            sanitized_text: str,
            sanitized_options: Dict[str, Any],
            sanitized_question: str | None = None
    ) -> Any:
        """
        Central dispatch mechanism for operation execution.

        Routes operation requests to appropriate handler methods using the operation
        registry. Provides unified error handling and argument preparation for all
        text processing operations.

        Args:
            operation: The text processing operation to execute (enum value)
            sanitized_text: Pre-sanitized input text for processing
            sanitized_options: Pre-sanitized options dictionary for the operation
            sanitized_question: Pre-sanitized question string for Q&A operations

        Returns:
            Operation result in the appropriate format:
                - str: For SUMMARIZE and QA operations
                - SentimentResult: For SENTIMENT operation
                - List[str]: For KEY_POINTS and QUESTIONS operations

        Raises:
            ValueError: If operation not found in registry or handler method missing
            ServiceUnavailableError: If AI service is unavailable after retries
            TransientAIError: For retryable AI service errors

        Behavior:
            - Validates operation exists in registry
            - Retrieves handler method name from registry
            - Prepares handler arguments based on operation requirements
            - Invokes handler method with prepared arguments
            - Propagates exceptions for proper resilience handling

        Examples:
            >>> # Summarize operation dispatch
            >>> result = await self._dispatch_operation(
            ...     operation=TextProcessingOperation.SUMMARIZE,
            ...     sanitized_text="Sample text",
            ...     sanitized_options={"max_length": 100},
            ...     sanitized_question=None
            ... )
            >>> # Returns: "Summary string"

            >>> # Q&A operation dispatch with question
            >>> result = await self._dispatch_operation(
            ...     operation=TextProcessingOperation.QA,
            ...     sanitized_text="Document content",
            ...     sanitized_options={},
            ...     sanitized_question="What is the main topic?"
            ... )
            >>> # Returns: "Answer string"
        """
        # Validate operation exists in registry
        if operation not in OPERATION_CONFIG:
            raise ValueError(f"Operation {operation} not found in registry")

        # Get handler method name from registry
        handler_name = self._get_handler_name(operation)

        # Verify handler method exists
        if not hasattr(self, handler_name):
            raise ValueError(f"Handler method '{handler_name}' not found on service")

        # Get handler method
        handler_method = getattr(self, handler_name)

        # Prepare arguments for handler
        handler_args = self._prepare_handler_arguments(
            operation=operation,
            sanitized_text=sanitized_text,
            sanitized_options=sanitized_options,
            sanitized_question=sanitized_question
        )

        # Invoke handler with prepared arguments
        return await handler_method(**handler_args)

    def _prepare_handler_arguments(
            self,
            operation: TextProcessingOperation,
            sanitized_text: str,
            sanitized_options: Dict[str, Any],
            sanitized_question: str | None = None
    ) -> Dict[str, Any]:
        """
        Prepare arguments for operation handler methods.

        Builds argument dictionary based on operation requirements defined in the
        registry. Different operations require different argument combinations.

        Args:
            operation: The text processing operation being executed
            sanitized_text: Pre-sanitized input text for processing
            sanitized_options: Pre-sanitized options dictionary for the operation
            sanitized_question: Pre-sanitized question string for Q&A operations

        Returns:
            Dictionary of arguments to pass to handler method

        Behavior:
            - All operations receive sanitized text
            - Operations accepting options receive sanitized_options
            - Q&A operation receives sanitized question as required parameter
            - Argument names match handler method signatures

        Examples:
            >>> # Summarize operation (text + options)
            >>> args = self._prepare_handler_arguments(
            ...     operation=TextProcessingOperation.SUMMARIZE,
            ...     sanitized_text="Sample text",
            ...     sanitized_options={"max_length": 100},
            ...     sanitized_question=None
            ... )
            >>> # Returns: {"text": "Sample text", "options": {"max_length": 100}}

            >>> # Sentiment operation (text only)
            >>> args = self._prepare_handler_arguments(
            ...     operation=TextProcessingOperation.SENTIMENT,
            ...     sanitized_text="Sample text",
            ...     sanitized_options={},
            ...     sanitized_question=None
            ... )
            >>> # Returns: {"text": "Sample text"}

            >>> # Q&A operation (text + question)
            >>> args = self._prepare_handler_arguments(
            ...     operation=TextProcessingOperation.QA,
            ...     sanitized_text="Document content",
            ...     sanitized_options={},
            ...     sanitized_question="What is the topic?"
            ... )
            >>> # Returns: {"text": "Document content", "question": "What is the topic?"}
        """
        # Get operation configuration
        config = self._get_operation_config(operation)

        # Start with text (all operations need it)
        handler_args: Dict[str, Any] = {"text": sanitized_text}

        # Add options if operation accepts them
        if config.get("accepts_options", False):
            handler_args["options"] = sanitized_options

        # Add question if operation requires it
        if config.get("requires_question", False):
            handler_args["question"] = sanitized_question

        return handler_args

    def _set_response_field(
            self,
            response: TextProcessingResponse,
            operation: TextProcessingOperation,
            result: Any
    ) -> None:
        """
        Route operation result to appropriate response field using registry.

        Sets the correct field on the TextProcessingResponse object based on the
        operation type defined in the registry. This eliminates the need for
        if/elif chains when assigning results.

        Args:
            response: TextProcessingResponse object to update
            operation: The text processing operation that was executed
            result: The result value to assign to the appropriate field

        Behavior:
            - Uses registry to determine correct response field
            - Sets result on response object using setattr
            - Handles all operation types consistently
            - Maintains type safety for response fields

        Examples:
            >>> # Set summarize result
            >>> response = TextProcessingResponse(operation="summarize")
            >>> self._set_response_field(response, TextProcessingOperation.SUMMARIZE, "Summary text")
            >>> # Sets: response.result = "Summary text"

            >>> # Set sentiment result
            >>> response = TextProcessingResponse(operation="sentiment")
            >>> sentiment = SentimentResult(sentiment="positive", confidence=0.9)
            >>> self._set_response_field(response, TextProcessingOperation.SENTIMENT, sentiment)
            >>> # Sets: response.sentiment = sentiment

            >>> # Set key points result
            >>> response = TextProcessingResponse(operation="key_points")
            >>> points = ["Point 1", "Point 2", "Point 3"]
            >>> self._set_response_field(response, TextProcessingOperation.KEY_POINTS, points)
            >>> # Sets: response.key_points = points
        """
        # Get response field name from registry
        field_name = self._get_response_field(operation)

        # Set the field on the response object
        setattr(response, field_name, result)

    async def _get_fallback_response(
            self,
            operation: TextProcessingOperation,
            text: str,
            question: str | None = None) -> Union[str, List[str], SentimentResult]:
        """
        Provide fallback responses when AI service is unavailable using registry.

        This method returns cached responses or generates simple fallback messages
        when the circuit breaker is open or retries are exhausted. Uses the operation
        registry to determine appropriate fallback types and response field routing.

        Args:
            operation: The text processing operation that failed
            text: Input text for potential cache key lookup
            question: Question for Q&A operations (used in cache key)

        Returns:
            Fallback response in the appropriate format based on operation type:
                - str: For SUMMARIZE and QA operations
                - SentimentResult: For SENTIMENT operation
                - List[str]: For KEY_POINTS and QUESTIONS operations

        Behavior:
            - Attempts to retrieve cached response first (best fallback)
            - Uses registry to determine fallback type (string, list, sentiment_result)
            - Generates appropriate default fallback based on operation type
            - Logs fallback usage for monitoring and debugging

        Examples:
            >>> # String fallback for summarize
            >>> result = await self._get_fallback_response(
            ...     operation=TextProcessingOperation.SUMMARIZE,
            ...     text="Sample text"
            ... )
            >>> # Returns: "Service temporarily unavailable..."

            >>> # SentimentResult fallback for sentiment
            >>> result = await self._get_fallback_response(
            ...     operation=TextProcessingOperation.SENTIMENT,
            ...     text="Sample text"
            ... )
            >>> # Returns: SentimentResult(sentiment="neutral", confidence=0.0, ...)

            >>> # List fallback for key_points
            >>> result = await self._get_fallback_response(
            ...     operation=TextProcessingOperation.KEY_POINTS,
            ...     text="Sample text"
            ... )
            >>> # Returns: ["Service temporarily unavailable", "Please try again later"]
        """
        logger.warning(f"Providing fallback response for {operation}")

        # Try to get cached response first
        operation_value = operation.value if hasattr(operation, "value") else operation
        cache_key = await self._build_cache_key(text, operation_value, {}, question)
        # Wrap cache.get() in try-catch for resilience
        try:
            cached_response = await self.cache_service.get(cache_key)
        except InfrastructureError as e:
            logger.warning(f"Cache get failed in fallback: {e}, proceeding with default fallback")
            cached_response = None

        if cached_response:
            logger.info(f"Using cached fallback for {operation}")
            # Extract the appropriate field from cached response dict using registry
            if isinstance(cached_response, dict):
                response_field = self._get_response_field(operation)
                cached_field = cached_response.get(response_field)

                # For sentiment operations, ensure we return SentimentResult instance, not dict
                if (operation == TextProcessingOperation.SENTIMENT and
                    isinstance(cached_field, dict) and
                    'sentiment' in cached_field):
                    return SentimentResult(**cached_field)

                return cached_field if cached_field is not None else self._get_default_fallback(operation)
            return cached_response

        # Generate fallback based on registry-defined type
        return self._get_default_fallback(operation)

    def _get_default_fallback(self, operation: TextProcessingOperation) -> Union[str, List[str], SentimentResult]:
        """
        Get default fallback response based on operation type from registry.

        Args:
            operation: The text processing operation requiring fallback

        Returns:
            Default fallback response in appropriate format

        Behavior:
            - Uses registry fallback_type to determine response format
            - Returns string fallback for string operations
            - Returns list fallback for list operations
            - Returns SentimentResult fallback for sentiment operation
        """
        fallback_type = self._get_fallback_type(operation)

        if fallback_type == "string":
            if operation == TextProcessingOperation.QA:
                return "I'm sorry, I cannot answer your question right now. The service is temporarily unavailable. Please try again later."
            return "Service temporarily unavailable. Please try again later for text processing."

        elif fallback_type == "list":
            if operation == TextProcessingOperation.QUESTIONS:
                return ["What is the main topic of this text?", "Can you provide more details?"]
            return ["Service temporarily unavailable", "Please try again later"]

        elif fallback_type == "sentiment_result":
            return SentimentResult(
                sentiment="neutral",
                confidence=0.0,
                explanation="Unable to analyze sentiment - service temporarily unavailable"
            )

        else:
            # Default to string fallback for unknown types
            logger.warning(f"Unknown fallback type '{fallback_type}' for operation {operation}, using string fallback")
            return "Service temporarily unavailable. Please try again later."

    async def _get_fallback_sentiment(self) -> SentimentResult:
        """Provide fallback sentiment when AI service is unavailable."""
        return SentimentResult(
            sentiment="neutral",
            confidence=0.0,
            explanation="Unable to analyze sentiment - service temporarily unavailable"
        )

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
        # Generate unique processing ID for internal tracing
        processing_id = str(uuid.uuid4())

        logger.info(f"PROCESSING_START - ID: {processing_id}, Operation: {request.operation}, Text Length: {len(request.text)}")

        # Check cache first
        operation_value = request.operation.value if hasattr(request.operation, "value") else request.operation
        cache_key = await self._build_cache_key(
            request.text,
            operation_value,
            request.options or {},
            request.question
        )
        # Wrap cache.get() in try-catch for resilience
        try:
            cached_response = await self.cache_service.get(cache_key)
        except InfrastructureError as e:
            logger.warning(f"Cache get failed: {e}, proceeding with AI processing")
            cached_response = None

        if cached_response:
            logger.info(f"Cache hit for operation: {request.operation}")
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: CACHE_HIT")
            # Ensure the response being returned matches the TextProcessingResponse structure
            # If cached_response is a dict, it needs to be converted
            if isinstance(cached_response, dict):
                cached_response["cache_hit"] = True
                return TextProcessingResponse(**cached_response)
            if isinstance(cached_response, TextProcessingResponse): # Or if it's already the correct type
                cached_response.cache_hit = True
                return cached_response
            # Handle cases where cache might return a simple string or other type not directly convertible
            # This part depends on how the cache stores data. Assuming it stores a dict.
            logger.warning(f"Unexpected cache response type: {type(cached_response)}")
            # Attempt to recreate response, or handle error
            # For now, let's assume it's a dict as per Pydantic model usage
            cached_response["cache_hit"] = True
            return TextProcessingResponse(**cached_response)


        # Sanitize inputs for processing with enhanced security for AI operations
        # Use advanced sanitization for text going to AI models to prevent prompt injection
        sanitized_text = self.sanitizer.sanitize_input(request.text)
        sanitized_options = sanitize_options(request.options or {})
        sanitized_question = self.sanitizer.sanitize_input(request.question) if request.question else None

        start_time = time.time()

        try:
            logger.info(f"Processing text with operation: {request.operation}")

            if request.operation not in [op.value for op in TextProcessingOperation]:
                raise ValueError(f"Unsupported operation: {request.operation}")

            processing_time = time.time() - start_time
            response = TextProcessingResponse(
                operation=request.operation,
                processing_time=processing_time,
                cache_hit=False,
                metadata={"word_count": len(sanitized_text.split())} # Use sanitized_text for word_count
            )

            try:
                # Dispatch operation using registry-based routing
                operation_result = await self._dispatch_operation(
                    operation=request.operation,
                    sanitized_text=sanitized_text,
                    sanitized_options=sanitized_options,
                    sanitized_question=sanitized_question
                )

                # Route result to appropriate response field using registry
                self._set_response_field(response, request.operation, operation_result)

            except (ServiceUnavailableError, TransientAIError, RetryError) as e:
                # Get fallback response using registry for transient AI service failures
                # This includes service unavailable, transient errors, and retry exhaustion
                # NOTE: PermanentAIError (e.g., invalid input) is NOT caught - it should propagate
                # to inform the client of non-recoverable errors
                fallback_result = await self._get_fallback_response(
                    request.operation,
                    sanitized_text,
                    sanitized_question
                )

                # Route fallback to appropriate response field using registry
                self._set_response_field(response, request.operation, fallback_result)

                # Mark as degraded service
                response.metadata["service_status"] = "degraded"
                response.metadata["fallback_used"] = True
                logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: FALLBACK_USED")

            # Cache the successful response (even fallback responses) with failure resilience
            # Reuse the cache_key from above to avoid redundant key generation
            ttl = self._get_ttl_for_operation(operation_value)
            try:
                await self.cache_service.set(cache_key, response.model_dump(), ttl)
            except InfrastructureError as e:
                logger.warning(f"Cache set failed: {e}, response delivery unaffected")

            processing_time = time.time() - start_time
            response.processing_time = processing_time
            logger.info(f"Processing completed in {processing_time:.2f}s")
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: SUCCESS, Duration: {processing_time:.2f}s")
            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing text: {e!s}")
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: ERROR, Duration: {processing_time:.2f}s")
            raise

    @with_balanced_resilience("summarize_text")  # type: ignore[misc]
    async def _summarize_text_with_resilience(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize text with resilience patterns."""
        return await self._summarize_text(text, options)

    @with_aggressive_resilience("analyze_sentiment")  # type: ignore[misc]
    async def _analyze_sentiment_with_resilience(self, text: str) -> SentimentResult:
        """Analyze sentiment with resilience patterns."""
        return await self._analyze_sentiment(text)

    @with_balanced_resilience("extract_key_points")  # type: ignore[misc]
    async def _extract_key_points_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points with resilience patterns."""
        return await self._extract_key_points(text, options)

    @with_balanced_resilience("generate_questions")  # type: ignore[misc]
    async def _generate_questions_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions with resilience patterns."""
        return await self._generate_questions(text, options)

    @with_conservative_resilience("answer_question")  # type: ignore[misc]
    async def _answer_question_with_resilience(self, text: str, question: str) -> str:
        """Answer question with resilience patterns."""
        return await self._answer_question(text, question)

    async def _summarize_text(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize the provided text."""
        # Options are sanitized by process_text before being passed here or to the _with_resilience wrapper
        max_length = options.get("max_length", 100)

        # User text is already pre-sanitized by process_text
        additional_instructions = f"Keep the summary to approximately {max_length} words."

        prompt = create_safe_prompt(
            template_name="summarize",
            user_input=text,
            additional_instructions=additional_instructions
        )

        try:
            try:
                result = await self.agent.run(prompt)
                # Use the validator instance
                validated_output = self.response_validator.validate(
                    result.output.strip(), "summary", text, "summarization"
                )
                return validated_output
            except ValueError as ve:
                logger.error(f"AI response validation failed in summarization: {ve}. Problematic response: {result.output.strip()[:200]}...")
                raise ValidationError(
                    f"Response validation failed for summarization: {ve}",
                    context={
                        "original_error": str(ve),
                        "operation": "summarize",
                        "text_length": len(text)
                    }
                )
        except ValidationError:
            # Let validation errors pass through without retrying
            raise
        except Exception as e:
            logger.error(f"AI agent error in summarization: {e}")
            # Convert to our custom exception for proper retry handling
            raise TransientAIError(f"Failed to summarize text: {e!s}")

    async def _analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of the provided text."""
        # User text is already pre-sanitized

        prompt = create_safe_prompt(
            template_name="sentiment",
            user_input=text
        )

        try:
            result = await self.agent.run(prompt)
            raw_output = result.output.strip()
            # Validate the raw string output before JSON parsing
            try:
                validated_raw_output = self.response_validator.validate(raw_output, "sentiment", text, "sentiment analysis")
            except ValueError as ve:
                logger.error(f"AI response validation failed in sentiment analysis: {ve}. Problematic response: {raw_output[:200]}...")
                raise ValidationError(
                    f"Response validation failed for sentiment analysis: {ve}",
                    context={
                        "original_error": str(ve),
                        "operation": "sentiment",
                        "text_length": len(text)
                    }
                )

            import json
            try:
                sentiment_data = json.loads(validated_raw_output)
                # Further validation specific to SentimentResult structure can be added here if needed
                # e.g., checking if all required fields are present. Pydantic does this on instantiation.
                return SentimentResult(**sentiment_data)
            except (json.JSONDecodeError, ValueError) as e: # PydanticError could also be caught if using strict parsing
                logger.warning(f"Failed to parse sentiment JSON or invalid structure: {e}. Output: {validated_raw_output}")
                return SentimentResult(
                    sentiment="neutral",
                    confidence=0.5,
                    explanation=f"Unable to analyze sentiment accurately. Validation or parsing failed. Raw: {validated_raw_output[:100]}" # Include part of raw output for debugging
                )
        except ValidationError:
            # Let validation errors pass through without retrying
            raise
        except Exception as e:
            logger.error(f"AI agent error in sentiment analysis: {e}")
            raise TransientAIError(f"Failed to analyze sentiment: {e!s}")

    async def _extract_key_points(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points from the text."""
        # Options are sanitized by process_text before being passed here or to the _with_resilience wrapper
        max_points = options.get("max_points", 5)
        # User text is already pre-sanitized

        additional_instructions = f"Extract the {max_points} most important key points."

        prompt = create_safe_prompt(
            template_name="key_points",
            user_input=text,
            additional_instructions=additional_instructions
        )

        try:
            result = await self.agent.run(prompt)
            try:
                validated_output_str = self.response_validator.validate(result.output.strip(), "key_points", text, "key points extraction")
            except ValueError as ve:
                logger.error(f"AI response validation failed in key points extraction: {ve}. Problematic response: {result.output.strip()[:200]}...")
                raise ValidationError(
                    f"Response validation failed for key points extraction: {ve}",
                    context={
                        "original_error": str(ve),
                        "operation": "key_points",
                        "text_length": len(text)
                    }
                )

            points = []
            # Process the validated string
            for line in validated_output_str.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    points.append(line[1:].strip())
                elif line and not line.startswith("Key Points:"): # Avoid including the "Key Points:" header if AI repeats it
                    points.append(line)
            return points[:max_points]
        except ValidationError:
            # Let validation errors pass through without retrying
            raise
        except Exception as e:
            logger.error(f"AI agent error in key points extraction: {e}")
            raise TransientAIError(f"Failed to extract key points: {e!s}")

    async def _generate_questions(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions about the text."""
        # Options are sanitized by process_text before being passed here or to the _with_resilience wrapper
        num_questions = options.get("num_questions", 5)
        # User text is already pre-sanitized

        additional_instructions = f"Generate {num_questions} thoughtful questions."

        prompt = create_safe_prompt(
            template_name="questions",
            user_input=text,
            additional_instructions=additional_instructions
        )

        try:
            result = await self.agent.run(prompt)
            try:
                validated_output_str = self.response_validator.validate(result.output.strip(), "questions", text, "question generation")
            except ValueError as ve:
                logger.error(f"AI response validation failed in question generation: {ve}. Problematic response: {result.output.strip()[:200]}...")
                raise ValidationError(
                    f"Response validation failed for question generation: {ve}",
                    context={
                        "original_error": str(ve),
                        "operation": "questions",
                        "text_length": len(text)
                    }
                )

            questions = []
            # Process the validated string
            for line in validated_output_str.split("\n"):
                line = line.strip()
                if line and not line.startswith("Questions:"): # Avoid including the "Questions:" header
                    if line[0].isdigit() and "." in line[:5]: # Basic check for numbered lists
                        line = line.split(".", 1)[1].strip()
                    questions.append(line)
            return questions[:num_questions]
        except ValidationError:
            # Let validation errors pass through without retrying
            raise
        except Exception as e:
            logger.error(f"AI agent error in question generation: {e}")
            raise TransientAIError(f"Failed to generate questions: {e!s}")

    async def _answer_question(self, text: str, question: str) -> str:
        """Answer a question about the text."""
        # User text and question are already pre-sanitized
        if not question: # Should be sanitized question now
            raise ValueError("Question is required for Q&A operation")

        prompt = create_safe_prompt(
            template_name="question_answer",
            user_input=text,
            user_question=question
        )

        try:
            result = await self.agent.run(prompt)
            # Pass `text` (sanitized user context) and `system_instruction`.
            # `question` is also part of the prompt but `text` is the primary user-generated free-form content.
            try:
                validated_output = self.response_validator.validate(result.output.strip(), "qa", text, "question answering")
                return validated_output
            except ValueError as ve:
                logger.error(f"AI response validation failed in question answering: {ve}. Problematic response: {result.output.strip()[:200]}...")
                raise ValidationError(
                    f"Response validation failed for question answering: {ve}",
                    context={
                        "original_error": str(ve),
                        "operation": "qa",
                        "text_length": len(text),
                        "question_length": len(question)
                    }
                )
        except ValidationError:
            # Let validation errors pass through without retrying
            raise
        except Exception as e:
            logger.error(f"AI agent error in question answering: {e}")
            raise TransientAIError(f"Failed to answer question: {e!s}")

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
        # Generate unique processing ID for internal batch tracing
        batch_processing_id = str(uuid.uuid4())

        start_time = time.time()
        total_requests = len(batch_request.requests)
        batch_id = batch_request.batch_id or f"batch_{int(time.time())}"

        logger.info(f"BATCH_PROCESSING_START - ID: {batch_processing_id}, Batch ID: {batch_id}, Total Requests: {total_requests}")
        logger.info(f"Processing batch of {total_requests} requests for batch_id: {batch_id}")

        semaphore = asyncio.Semaphore(self.settings.BATCH_AI_CONCURRENCY_LIMIT)
        tasks = []

        async def _process_single_request_in_batch(index: int, item_request: TextProcessingRequest) -> BatchTextProcessingItem:
            """Helper function to process a single request within the batch with resilience."""
            async with semaphore:
                try:
                    # Ensure the operation is valid before processing
                    # No sanitization needed for item_request.operation itself as it's an enum/string check
                    if not hasattr(TextProcessingOperation, item_request.operation.upper()):
                        raise ValueError(f"Unsupported operation: {item_request.operation}")

                    # Create a new TextProcessingRequest object for process_text
                    # process_text will handle the sanitization of its inputs
                    current_request = TextProcessingRequest(
                        text=item_request.text, # Pass original text
                        operation=TextProcessingOperation[item_request.operation.upper()],
                        options=item_request.options, # Pass original options
                        question=item_request.question # Pass original question
                    )

                    # Process with resilience (this will use the resilience decorators)
                    # process_text will sanitize
                    response = await self.process_text(current_request)
                    return BatchTextProcessingItem(request_index=index, status=BatchTextProcessingStatus.COMPLETED, response=response)

                except ServiceUnavailableError as e:
                    logger.warning(f"Batch item {index} (batch_id: {batch_id}) degraded service: {e!s}")
                    return BatchTextProcessingItem(request_index=index, status=BatchTextProcessingStatus.FAILED, error=str(e))

                except Exception as e:
                    logger.error(f"Batch item {index} (batch_id: {batch_id}) failed: {e!s}")
                    return BatchTextProcessingItem(request_index=index, status=BatchTextProcessingStatus.FAILED, error=str(e))

        for i, request_item in enumerate(batch_request.requests):
            task = _process_single_request_in_batch(i, request_item)
            tasks.append(task)

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out any exceptions and ensure we only have BatchTextProcessingItem objects
        results: List[BatchTextProcessingItem] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, Exception):
                logger.error(f"Batch item {i} (batch_id: {batch_id}) failed with exception: {result!s}")
                results.append(BatchTextProcessingItem(request_index=i, status=BatchTextProcessingStatus.FAILED, error=str(result)))
            elif isinstance(result, BatchTextProcessingItem):
                results.append(result)
            else:
                logger.error(f"Batch item {i} (batch_id: {batch_id}) returned unexpected type: {type(result)}")
                results.append(BatchTextProcessingItem(request_index=i, status=BatchTextProcessingStatus.FAILED, error="Unexpected result type"))

        completed_count = sum(1 for r in results if r.status == BatchTextProcessingStatus.COMPLETED)
        failed_count = total_requests - completed_count
        total_time = time.time() - start_time

        logger.info(f"BATCH_PROCESSING_END - ID: {batch_processing_id}, Batch ID: {batch_id}, Completed: {completed_count}/{total_requests}, Duration: {total_time:.2f}s")
        logger.info(f"Batch (batch_id: {batch_id}) completed. Successful: {completed_count}/{total_requests}. Time: {total_time:.2f}s")

        return BatchTextProcessingResponse(
            batch_id=batch_id,
            total_requests=total_requests,
            completed=completed_count,
            failed=failed_count,
            results=results,
            total_processing_time=total_time
        )

    # =============================================================================
    # DOMAIN CACHE KEY BUILDING LOGIC
    # =============================================================================

    async def _build_cache_key(
        self,
        text: str,
        operation: str,
        options: Dict[str, Any],
        question: str | None = None
    ) -> str:
        """
        Build cache key using domain-specific logic and question parameter handling.

        This method encapsulates domain-specific cache key building logic, properly
        embedding question parameters in the options dictionary before delegating
        to the infrastructure layer's generic key generation.

        Args:
            text: Input text for key generation
            operation: Operation type (summarize, sentiment, key_points, questions, qa)
            options: Options dictionary containing operation-specific parameters
            question: Question for Q&A operations, embedded in options if present

        Returns:
            Generated cache key string

        Behavior:
            - Embeds question parameter in options dictionary if present
            - Delegates to infrastructure layer's build_key() method for actual generation
            - Maintains backwards compatibility with existing key generation logic
            - Handles all operation types with consistent key generation patterns

        Examples:
            >>> # Standard operation without question
            >>> key = await service._build_cache_key(
            ...     text="Sample text",
            ...     operation="summarize",
            ...     options={"max_length": 100}
            ... )

            >>> # Q&A operation with question embedded in options
            >>> key = await service._build_cache_key(
            ...     text="Document content",
            ...     operation="qa",
            ...     options={"max_tokens": 150},
            ...     question="What are the main conclusions?"
            ... )
        """
        # Embed question in options dictionary if present
        if question:
            options = {**options, "question": question}

        # Use generic infrastructure cache key building
        return self.cache_service.build_key(text, operation, options)

    def _get_ttl_for_operation(self, operation: str) -> int | None:
        """
        Get operation-specific TTL for cache storage using registry.

        This method provides domain-specific TTL logic for different operation types,
        ensuring appropriate cache lifetimes based on the nature of each operation.
        Uses the operation registry for centralized TTL configuration.

        Args:
            operation: Operation type (summarize, sentiment, key_points, questions, qa)

        Returns:
            TTL in seconds for the operation, or None if operation not found

        Behavior:
            - Returns operation-specific TTL values from registry
            - Summarization has longer TTL as summaries change less frequently
            - Q&A operations have shorter TTL as answers may need fresher context
            - Sentiment analysis has moderate TTL balancing accuracy and performance

        Examples:
            >>> ttl = service._get_ttl_for_operation("summarize")
            >>> # Returns 7200 (2 hours) for summary operations

            >>> ttl = service._get_ttl_for_operation("qa")
            >>> # Returns 1800 (30 minutes) for Q&A operations
        """
        # Try to convert string operation to enum and get TTL from registry
        try:
            operation_enum = TextProcessingOperation(operation)
            return self._get_cache_ttl_from_registry(operation_enum)
        except (ValueError, KeyError):
            # Fall back to None if operation not recognized
            logger.warning(f"Unknown operation '{operation}' for TTL lookup, using cache default")
            return None
