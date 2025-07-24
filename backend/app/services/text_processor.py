"""Text processing service with resilience integration.

This module provides a comprehensive text processing service that leverages AI models
to perform various natural language processing operations with built-in resilience,
caching, and security features.

The TextProcessorService class is the main entry point for all text processing operations,
supporting both individual requests and batch processing with concurrent execution.

Key Features:
    * Multiple AI-powered text operations (summarization, sentiment analysis, etc.)
    * Resilience patterns including circuit breakers, retries, and fallback responses
    * Intelligent caching to reduce API calls and improve performance
    * Input sanitization and output validation for security
    * Batch processing with configurable concurrency limits
    * Comprehensive logging and monitoring integration
    * Graceful degradation when AI services are unavailable

Supported Operations:
    * SUMMARIZE: Generate concise summaries of input text
    * SENTIMENT: Analyze emotional tone and confidence levels
    * KEY_POINTS: Extract the most important points from text
    * QUESTIONS: Generate thoughtful questions about the content
    * QA: Answer specific questions based on provided context

Architecture:
    The service is built around a resilience-first design with multiple layers:
    
    1. Input Layer: Sanitizes and validates all user inputs using PromptSanitizer
    2. Caching Layer: Checks for cached responses before making AI calls
    3. AI Processing Layer: Uses Pydantic AI agents with configurable models
    4. Resilience Layer: Applies circuit breakers, retries, and timeouts
    5. Validation Layer: Validates AI responses for safety and correctness
    6. Fallback Layer: Provides degraded responses when services are unavailable

Resilience Strategies:
    Different operations use tailored resilience strategies:
    * Aggressive: Fast failures with immediate fallbacks (sentiment analysis)
    * Balanced: Moderate retries with reasonable timeouts (most operations)
    * Conservative: Extended retries for critical operations (Q&A)

Security Features:
    * Prompt injection prevention through input sanitization
    * Output validation to ensure safe AI responses
    * Secure prompt templates with parameterized inputs
    * Comprehensive logging for audit trails

Usage:
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

Dependencies:
    * pydantic-ai: AI agent framework for model interactions
    * shared.models: Pydantic models for request/response validation
    * app.infrastructure: Resilience, caching, and AI infrastructure
    * app.config: Application settings and configuration

Exceptions:
    * ServiceUnavailableError: Raised when AI services are temporarily unavailable
    * TransientAIError: Raised for retryable AI service errors
    * ValueError: Raised for invalid operations or missing required parameters

Thread Safety:
    The service is designed to be thread-safe and supports concurrent processing
    through asyncio semaphores and proper resource management.

Performance Considerations:
    * Caching significantly reduces redundant AI calls
    * Batch processing optimizes concurrent request handling
    * Configurable concurrency limits prevent resource exhaustion
    * Circuit breakers prevent cascading failures

Monitoring:
    The service provides comprehensive metrics and health checks:
    * Processing times and success rates per operation
    * Cache hit ratios and performance metrics
    * Resilience pattern statistics (circuit breaker states, retry counts)
    * Error rates and fallback usage patterns

Author:
    FastAPI-Streamlit-LLM-Starter Team

Version:
    1.0.0
"""

import time
import asyncio
import uuid
import re
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging
from pydantic_ai import Agent

# Only import for type checking to avoid circular dependencies
if TYPE_CHECKING:
    from app.infrastructure.cache import AIResponseCache

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
    TransientAIError
)
from app.infrastructure.resilience import (
    ai_resilience,
    ResilienceStrategy,
    with_balanced_resilience,
    with_aggressive_resilience,
    with_conservative_resilience,
)
from app.services.response_validator import ResponseValidator

logger = logging.getLogger(__name__)


class TextProcessorService:
    """Service for processing text using AI models with resilience patterns."""
    
    def __init__(self, settings: Settings, cache: "AIResponseCache"):
        """
        Initialize the text processor with AI agent and resilience.
        
        Args:
            settings: Application settings instance for configuration.
            cache: Cache service instance for storing AI responses.
        """
        self.settings = settings
        self.cache = cache
        
        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.agent = Agent(
            model=self.settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
        
        # Use provided cache service
        self.cache_service = cache
        
        # Initialize the advanced sanitizer
        self.sanitizer = PromptSanitizer()
        self.response_validator = ResponseValidator()
        
        # Register operations with resilience service
        self._register_operations()

    def _register_operations(self):
        """Register text processing operations with resilience service."""
        operations = {
            "summarize_text":     getattr(self.settings, 'summarize_resilience_strategy',  'balanced'),
            "analyze_sentiment":  getattr(self.settings, 'sentiment_resilience_strategy',  'balanced'),
            "extract_key_points": getattr(self.settings, 'key_points_resilience_strategy', 'balanced'),
            "generate_questions": getattr(self.settings, 'questions_resilience_strategy',  'balanced'),
            "answer_question":    getattr(self.settings, 'qa_resilience_strategy',         'balanced'),
        }
        
        for operation_name, strategy_name in operations.items():
            try:
                # Convert string strategy to enum
                strategy = ResilienceStrategy(strategy_name)
                ai_resilience.register_operation(operation_name, strategy)
                logger.info(f"Registered operation '{operation_name}' with strategy '{strategy_name}'")
            except ValueError:
                logger.warning(f"Unknown strategy '{strategy_name}' for operation '{operation_name}', using balanced")
                ai_resilience.register_operation(operation_name, ResilienceStrategy.BALANCED)

    async def _get_fallback_response(
            self, 
            operation: TextProcessingOperation, 
            text: str, 
            question: Optional[str] = None) -> Any:
        """
        Provide fallback responses when AI service is unavailable.
        
        This method returns cached responses or generates simple fallback messages
        when the circuit breaker is open or retries are exhausted.
        """
        logger.warning(f"Providing fallback response for {operation}")
        
        # Try to get cached response first
        operation_value = operation.value if hasattr(operation, 'value') else operation
        cached_response = await self.cache_service.get_cached_response(text, operation_value, {}, question)
        
        if cached_response:
            logger.info(f"Using cached fallback for {operation}")
            # Extract the appropriate field from cached response dict
            if isinstance(cached_response, dict):
                if operation == TextProcessingOperation.SUMMARIZE:
                    return cached_response.get('result', "Service temporarily unavailable. Please try again later for text summarization.")
                elif operation == TextProcessingOperation.SENTIMENT:
                    return cached_response.get('sentiment')
                elif operation == TextProcessingOperation.KEY_POINTS:
                    return cached_response.get('key_points', ["Service temporarily unavailable", "Please try again later"])
                elif operation == TextProcessingOperation.QUESTIONS:
                    return cached_response.get('questions', ["What is the main topic of this text?", "Can you provide more details?"])
                elif operation == TextProcessingOperation.QA:
                    return cached_response.get('result', "I'm sorry, I cannot answer your question right now. The service is temporarily unavailable. Please try again later.")
            return cached_response
        
        # Generate simple fallback responses
        fallback_responses = {
            TextProcessingOperation.SUMMARIZE: "Service temporarily unavailable. Please try again later for text summarization.",
            TextProcessingOperation.SENTIMENT: None,  # Will use neutral sentiment
            TextProcessingOperation.KEY_POINTS: ["Service temporarily unavailable", "Please try again later"],
            TextProcessingOperation.QUESTIONS: ["What is the main topic of this text?", "Can you provide more details?"],
            TextProcessingOperation.QA: "I'm sorry, I cannot answer your question right now. The service is temporarily unavailable. Please try again later."
        }
        
        return fallback_responses.get(operation, "Service temporarily unavailable. Please try again later.")
    
    async def _get_fallback_sentiment(self) -> SentimentResult:
        """Provide fallback sentiment when AI service is unavailable."""
        return SentimentResult(
            sentiment="neutral",
            confidence=0.0,
            explanation="Unable to analyze sentiment - service temporarily unavailable"
        )
    
    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """Process text with caching and resilience support."""
        # Generate unique processing ID for internal tracing
        processing_id = str(uuid.uuid4())
        
        logger.info(f"PROCESSING_START - ID: {processing_id}, Operation: {request.operation}, Text Length: {len(request.text)}")
        
        # Check cache first
        operation_value = request.operation.value if hasattr(request.operation, 'value') else request.operation
        cached_response = await self.cache_service.get_cached_response(
            request.text, 
            operation_value, 
            request.options or {}, 
            request.question
        )
        
        if cached_response:
            logger.info(f"Cache hit for operation: {request.operation}")
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: CACHE_HIT")
            # Ensure the response being returned matches the TextProcessingResponse structure
            # If cached_response is a dict, it needs to be converted
            if isinstance(cached_response, dict):
                cached_response['cache_hit'] = True
                return TextProcessingResponse(**cached_response)
            elif isinstance(cached_response, TextProcessingResponse): # Or if it's already the correct type
                cached_response.cache_hit = True
                return cached_response
            else:
                 # Handle cases where cache might return a simple string or other type not directly convertible
                 # This part depends on how cache_response stores data. Assuming it stores a dict.
                 logger.warning(f"Unexpected cache response type: {type(cached_response)}")
                 # Attempt to recreate response, or handle error
                 # For now, let's assume it's a dict as per Pydantic model usage
                 cached_response['cache_hit'] = True
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
                if request.operation == TextProcessingOperation.SUMMARIZE:
                    response.result = await self._summarize_text_with_resilience(sanitized_text, sanitized_options)
                elif request.operation == TextProcessingOperation.SENTIMENT:
                    response.sentiment = await self._analyze_sentiment_with_resilience(sanitized_text)
                elif request.operation == TextProcessingOperation.KEY_POINTS:
                    response.key_points = await self._extract_key_points_with_resilience(sanitized_text, sanitized_options)
                elif request.operation == TextProcessingOperation.QUESTIONS:
                    response.questions = await self._generate_questions_with_resilience(sanitized_text, sanitized_options)
                elif request.operation == TextProcessingOperation.QA:
                    response.result = await self._answer_question_with_resilience(sanitized_text, sanitized_question)
                else:
                    raise ValueError(f"Unsupported operation: {request.operation}")
            
            except ServiceUnavailableError:
                if request.operation == TextProcessingOperation.SENTIMENT:
                    response.sentiment = await self._get_fallback_sentiment()
                elif request.operation == TextProcessingOperation.KEY_POINTS:
                    # Fallback should also use sanitized inputs if they are part of the fallback generation logic
                    response.key_points = await self._get_fallback_response(request.operation, sanitized_text)
                elif request.operation == TextProcessingOperation.QUESTIONS:
                    response.questions = await self._get_fallback_response(request.operation, sanitized_text)
                else:
                    response.result = await self._get_fallback_response(request.operation, sanitized_text, sanitized_question)
                
                # Mark as degraded service
                response.metadata["service_status"] = "degraded"
                response.metadata["fallback_used"] = True
                logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: FALLBACK_USED")
            
            # Cache the successful response (even fallback responses)
            await self.cache_service.cache_response(
                request.text,
                operation_value,
                request.options or {},
                response.model_dump(),
                request.question
            )
                
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            logger.info(f"Processing completed in {processing_time:.2f}s")  # noqa: E231
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: SUCCESS, Duration: {processing_time:.2f}s")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing text: {str(e)}")
            logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: ERROR, Duration: {processing_time:.2f}s")
            raise
    
    @with_balanced_resilience("summarize_text")
    async def _summarize_text_with_resilience(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize text with resilience patterns."""
        return await self._summarize_text(text, options)
    
    @with_aggressive_resilience("analyze_sentiment")
    async def _analyze_sentiment_with_resilience(self, text: str) -> SentimentResult:
        """Analyze sentiment with resilience patterns."""
        return await self._analyze_sentiment(text)
    
    @with_balanced_resilience("extract_key_points")
    async def _extract_key_points_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points with resilience patterns."""
        return await self._extract_key_points(text, options)
    
    @with_balanced_resilience("generate_questions")
    async def _generate_questions_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions with resilience patterns."""
        return await self._generate_questions(text, options)
    
    @with_conservative_resilience("answer_question")
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
                    result.output.strip(), 'summary', text, "summarization"
                )
                return validated_output
            except ValueError as ve:
                logger.error(f"AI response validation failed in summarization: {ve}. Problematic response: {result.output.strip()[:200]}...")
                return "An error occurred while processing your request. The AI response could not be validated."
        except Exception as e:
            logger.error(f"AI agent error in summarization: {e}")
            # Convert to our custom exception for proper retry handling
            raise TransientAIError(f"Failed to summarize text: {str(e)}")
    
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
                validated_raw_output = self.response_validator.validate(raw_output, 'sentiment', text, "sentiment analysis")
            except ValueError as ve:
                logger.error(f"AI response validation failed in sentiment analysis: {ve}. Problematic response: {raw_output[:200]}...")
                return SentimentResult(
                    sentiment="neutral",
                    confidence=0.0,
                    explanation="An error occurred while processing your request. The AI response could not be validated."
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
        except Exception as e:
            logger.error(f"AI agent error in sentiment analysis: {e}")
            raise TransientAIError(f"Failed to analyze sentiment: {str(e)}")
    
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
                validated_output_str = self.response_validator.validate(result.output.strip(), 'key_points', text, "key points extraction")
            except ValueError as ve:
                logger.error(f"AI response validation failed in key points extraction: {ve}. Problematic response: {result.output.strip()[:200]}...")
                return ["An error occurred while processing your request. The AI response could not be validated."]
            
            points = []
            # Process the validated string
            for line in validated_output_str.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    points.append(line[1:].strip())
                elif line and not line.startswith('Key Points:'): # Avoid including the "Key Points:" header if AI repeats it
                    points.append(line)
            return points[:max_points]
        except Exception as e:
            logger.error(f"AI agent error in key points extraction: {e}")
            raise TransientAIError(f"Failed to extract key points: {str(e)}")
    
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
                validated_output_str = self.response_validator.validate(result.output.strip(), 'questions', text, "question generation")
            except ValueError as ve:
                logger.error(f"AI response validation failed in question generation: {ve}. Problematic response: {result.output.strip()[:200]}...")
                return ["An error occurred while processing your request. The AI response could not be validated."]
            
            questions = []
            # Process the validated string
            for line in validated_output_str.split('\n'):
                line = line.strip()
                if line and not line.startswith('Questions:'): # Avoid including the "Questions:" header
                    if line[0].isdigit() and '.' in line[:5]: # Basic check for numbered lists
                        line = line.split('.', 1)[1].strip()
                    questions.append(line)
            return questions[:num_questions]
        except Exception as e:
            logger.error(f"AI agent error in question generation: {e}")
            raise TransientAIError(f"Failed to generate questions: {str(e)}")
    
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
                validated_output = self.response_validator.validate(result.output.strip(), 'qa', text, "question answering")
                return validated_output
            except ValueError as ve:
                logger.error(f"AI response validation failed in question answering: {ve}. Problematic response: {result.output.strip()[:200]}...")
                return "An error occurred while processing your request. The AI response could not be validated."
        except Exception as e:
            logger.error(f"AI agent error in question answering: {e}")
            raise TransientAIError(f"Failed to answer question: {str(e)}")

    async def process_batch(self, batch_request: BatchTextProcessingRequest) -> BatchTextProcessingResponse:
        """Process a batch of text processing requests concurrently with resilience."""
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
                    logger.warning(f"Batch item {index} (batch_id: {batch_id}) degraded service: {str(e)}")
                    return BatchTextProcessingItem(request_index=index, status=BatchTextProcessingStatus.FAILED, error=str(e))

                except Exception as e:
                    logger.error(f"Batch item {index} (batch_id: {batch_id}) failed: {str(e)}")
                    return BatchTextProcessingItem(request_index=index, status=BatchTextProcessingStatus.FAILED, error=str(e))

        for i, request_item in enumerate(batch_request.requests):
            task = _process_single_request_in_batch(i, request_item)
            tasks.append(task)

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any exceptions and ensure we only have BatchTextProcessingItem objects
        results: List[BatchTextProcessingItem] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, Exception):
                logger.error(f"Batch item {i} (batch_id: {batch_id}) failed with exception: {str(result)}")
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
        logger.info(f"Batch (batch_id: {batch_id}) completed. Successful: {completed_count}/{total_requests}. Time: {total_time:.2f}s")  # noqa: E231

        return BatchTextProcessingResponse(
            batch_id=batch_id,
            total_requests=total_requests,
            completed=completed_count,
            failed=failed_count,
            results=results,
            total_processing_time=total_time
        )
    
    def get_resilience_health(self) -> Dict[str, Any]:
        """Get resilience health status for this service."""
        return ai_resilience.get_health_status()
    
    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Get resilience metrics for this service."""
        return ai_resilience.get_all_metrics()
