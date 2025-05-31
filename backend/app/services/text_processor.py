"""Text processing service with resilience integration."""

import time
import asyncio
from typing import Dict, Any, List
import logging
from pydantic_ai import Agent

from shared.models import (
    ProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    SentimentResult,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchProcessingItem,
    ProcessingStatus
)
from app.config import settings
from app.services.cache import ai_cache
from app.utils.sanitization import sanitize_input, sanitize_options # Added import
from app.services.resilience import (
    ai_resilience,
    ResilienceStrategy,
    with_balanced_resilience,
    with_aggressive_resilience,
    with_conservative_resilience,
    ServiceUnavailableError,
    TransientAIError
)

logger = logging.getLogger(__name__)


class TextProcessorService:
    """Service for processing text using AI models with resilience patterns."""
    
    def __init__(self):
        """Initialize the text processor with AI agent and resilience."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.agent = Agent(
            model=settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
        
        # Configure resilience strategies for different operations
        self._configure_resilience_strategies()

    def _validate_ai_output(self, output: str, request_text: str, system_instruction: str) -> str:
        """
        Validates the AI's output.
        - Checks for prompt leakage (system instructions).
        - Basic check for placeholder/error messages from the AI.
        - Returns sanitized output. More aggressive policies might raise errors.
        """
        if not isinstance(output, str):
            logger.warning("AI output is not a string, skipping validation.")
            return output

        sanitized_output = output # Start with the original output

        # Normalize for case-insensitive comparison
        lower_output = sanitized_output.lower()

        # Check for leakage of system instruction
        # This is a simplified check. More advanced NLP techniques could be used for robustness.
        # For example, checking for high token overlap if system_instruction is long.
        lower_system_instruction = system_instruction.lower()
        if lower_system_instruction in lower_output:
            logger.warning("Potential system instruction leakage in AI output.")
            # Policy: For now, we will try to remove it if it's a prefix/suffix or standalone.
            # This is a naive removal and might need refinement.
            # Example: if output starts with instruction, remove it.
            # This is risky if the instruction is generic, e.g., "Answer:"
            # A better approach for critical systems would be to reject the output or use more precise detection.
            # Given the prompt structures, direct prefix/suffix leakage is less likely than it appearing within.
            # For this exercise, we will log and not modify for this specific check,
            # as naive replacement can be destructive.

        # Check for leakage of substantial portions of the user's input if it's very long
        # This is more about detecting if the AI just regurgitated a long input instead of processing it.
        if len(request_text) > 250 and request_text.lower() in lower_output: # Arbitrary length and case-insensitive
             logger.warning("Potential verbatim user input leakage in AI output for long input.")
             # Policy: Log for now. Action depends on specific requirements.

        # Check for common AI error/refusal placeholders
        refusal_phrases = [
            "i cannot fulfill this request", # Standardized to lower case
            "i am unable to",
            "i'm sorry, but as an ai model",
            "as a large language model",
            "i am not able to provide assistance with that",
            "my apologies, but i cannot",
        ]
        for phrase in refusal_phrases:
            if phrase in lower_output: # phrase is already lowercase
                logger.warning(f"AI output contains a potential refusal/error phrase: '{phrase}'")
                # Policy: Log for now. Depending on the operation, this might be an indicator
                # to return a fallback or error. For now, the output is passed through.

        # Future: Add checks for harmful content using a dedicated filter/moderation API if available.
        # Future: Validate response structure more rigorously if specific formats are expected beyond JSON.

        return sanitized_output.strip() # Return the (potentially modified or original) string, stripped
    
    def _configure_resilience_strategies(self):
        """Configure resilience strategies based on settings."""
        self.resilience_strategies = {
            ProcessingOperation.SUMMARIZE: settings.summarize_resilience_strategy,
            ProcessingOperation.SENTIMENT: settings.sentiment_resilience_strategy,
            ProcessingOperation.KEY_POINTS: settings.key_points_resilience_strategy,
            ProcessingOperation.QUESTIONS: settings.questions_resilience_strategy,
            ProcessingOperation.QA: settings.qa_resilience_strategy,
        }
        
        logger.info(f"Configured resilience strategies: {self.resilience_strategies}")
    
    async def _get_fallback_response(self, operation: ProcessingOperation, text: str, question: str = None) -> str:
        """
        Provide fallback responses when AI service is unavailable.
        
        This method returns cached responses or generates simple fallback messages
        when the circuit breaker is open or retries are exhausted.
        """
        logger.warning(f"Providing fallback response for {operation}")
        
        # Try to get cached response first
        operation_value = operation.value if hasattr(operation, 'value') else operation
        cached_response = await ai_cache.get_cached_response(text, operation_value, {}, question)
        
        if cached_response:
            logger.info(f"Using cached fallback for {operation}")
            return cached_response
        
        # Generate simple fallback responses
        fallback_responses = {
            ProcessingOperation.SUMMARIZE: "Service temporarily unavailable. Please try again later for text summarization.",
            ProcessingOperation.SENTIMENT: None,  # Will use neutral sentiment
            ProcessingOperation.KEY_POINTS: ["Service temporarily unavailable", "Please try again later"],
            ProcessingOperation.QUESTIONS: ["What is the main topic of this text?", "Can you provide more details?"],
            ProcessingOperation.QA: "I'm sorry, I cannot answer your question right now. The service is temporarily unavailable. Please try again later."
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
        # Check cache first
        operation_value = request.operation.value if hasattr(request.operation, 'value') else request.operation
        cached_response = await ai_cache.get_cached_response(
            request.text, 
            operation_value, 
            request.options or {}, 
            request.question
        )
        
        if cached_response:
            logger.info(f"Cache hit for operation: {request.operation}")
            # Ensure the response being returned matches the TextProcessingResponse structure
            # If cached_response is a dict, it needs to be converted
            if isinstance(cached_response, dict):
                return TextProcessingResponse(**cached_response)
            elif isinstance(cached_response, TextProcessingResponse): # Or if it's already the correct type
                 return cached_response
            else:
                 # Handle cases where cache might return a simple string or other type not directly convertible
                 # This part depends on how cache_response stores data. Assuming it stores a dict.
                 logger.warning(f"Unexpected cache response type: {type(cached_response)}")
                 # Attempt to recreate response, or handle error
                 # For now, let's assume it's a dict as per Pydantic model usage
                 return TextProcessingResponse(**cached_response)


        # Sanitize inputs for processing
        sanitized_text = sanitize_input(request.text)
        sanitized_options = sanitize_options(request.options or {})
        sanitized_question = sanitize_input(request.question) if request.question else None

        start_time = time.time()
        
        try:
            logger.info(f"Processing text with operation: {request.operation}")
            
            if request.operation not in [op.value for op in ProcessingOperation]:
                raise ValueError(f"Unsupported operation: {request.operation}")
            
            processing_time = time.time() - start_time
            response = TextProcessingResponse(
                operation=request.operation,
                processing_time=processing_time,
                metadata={"word_count": len(sanitized_text.split())} # Use sanitized_text for word_count
            )
            
            try:
                if request.operation == ProcessingOperation.SUMMARIZE:
                    response.result = await self._summarize_text_with_resilience(sanitized_text, sanitized_options)
                elif request.operation == ProcessingOperation.SENTIMENT:
                    response.sentiment = await self._analyze_sentiment_with_resilience(sanitized_text)
                elif request.operation == ProcessingOperation.KEY_POINTS:
                    response.key_points = await self._extract_key_points_with_resilience(sanitized_text, sanitized_options)
                elif request.operation == ProcessingOperation.QUESTIONS:
                    response.questions = await self._generate_questions_with_resilience(sanitized_text, sanitized_options)
                elif request.operation == ProcessingOperation.QA:
                    response.result = await self._answer_question_with_resilience(sanitized_text, sanitized_question)
                else:
                    raise ValueError(f"Unsupported operation: {request.operation}")
            
            except ServiceUnavailableError:
                if request.operation == ProcessingOperation.SENTIMENT:
                    response.sentiment = await self._get_fallback_sentiment()
                elif request.operation == ProcessingOperation.KEY_POINTS:
                    # Fallback should also use sanitized inputs if they are part of the fallback generation logic
                    response.key_points = await self._get_fallback_response(request.operation, sanitized_text)
                elif request.operation == ProcessingOperation.QUESTIONS:
                    response.questions = await self._get_fallback_response(request.operation, sanitized_text)
                else:
                    response.result = await self._get_fallback_response(request.operation, sanitized_text, sanitized_question)
                
                # Mark as degraded service
                response.metadata["service_status"] = "degraded"
                response.metadata["fallback_used"] = True
            
            # Cache the successful response (even fallback responses)
            await ai_cache.cache_response(
                request.text,
                operation_value,
                request.options or {},
                response.model_dump(),
                request.question
            )
                
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            logger.info(f"Processing completed in {processing_time:.2f}s")  # noqa: E231
            return response
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    @ai_resilience.with_resilience("summarize_text", strategy=ResilienceStrategy.BALANCED)
    async def _summarize_text_with_resilience(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize text with resilience patterns."""
        return await self._summarize_text(text, options)
    
    @ai_resilience.with_resilience("analyze_sentiment", strategy=ResilienceStrategy.AGGRESSIVE)
    async def _analyze_sentiment_with_resilience(self, text: str) -> SentimentResult:
        """Analyze sentiment with resilience patterns."""
        return await self._analyze_sentiment(text)
    
    @ai_resilience.with_resilience("extract_key_points", strategy=ResilienceStrategy.BALANCED)
    async def _extract_key_points_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points with resilience patterns."""
        return await self._extract_key_points(text, options)
    
    @ai_resilience.with_resilience("generate_questions", strategy=ResilienceStrategy.BALANCED)
    async def _generate_questions_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions with resilience patterns."""
        return await self._generate_questions(text, options)
    
    @ai_resilience.with_resilience("answer_question", strategy=ResilienceStrategy.CONSERVATIVE)
    async def _answer_question_with_resilience(self, text: str, question: str) -> str:
        """Answer question with resilience patterns."""
        return await self._answer_question(text, question)
    
    async def _summarize_text(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize the provided text."""
        # Options are sanitized by process_text before being passed here or to the _with_resilience wrapper
        max_length = options.get("max_length", 100)
        
        # User text is already pre-sanitized by process_text
        
        system_instruction = f"Please provide a concise summary of the provided text in approximately {max_length} words."
        user_content_marker_start = "---USER TEXT START---"
        user_content_marker_end = "---USER TEXT END---"
        
        prompt = f"""
{system_instruction}

{user_content_marker_start}
{text}
{user_content_marker_end}

Summary:
"""
        try:
            result = await self.agent.run(prompt)
            # Pass the original `text` (sanitized user input) and the specific `system_instruction` for this call
            validated_output = self._validate_ai_output(result.data.strip(), text, system_instruction)
            return validated_output
        except Exception as e:
            logger.error(f"AI agent error in summarization: {e}")
            # Convert to our custom exception for proper retry handling
            raise TransientAIError(f"Failed to summarize text: {str(e)}")
    
    async def _analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of the provided text."""
        # User text is already pre-sanitized
        system_instruction = """Analyze the sentiment of the following text. Respond with a JSON object containing:
- sentiment: "positive", "negative", or "neutral"
- confidence: a number between 0.0 and 1.0
- explanation: a brief explanation of the sentiment"""
        user_content_marker_start = "---USER TEXT START---"
        user_content_marker_end = "---USER TEXT END---"

        prompt = f"""
{system_instruction}

{user_content_marker_start}
{text}
{user_content_marker_end}

Response (JSON only):
"""
        try:
            result = await self.agent.run(prompt)
            raw_output = result.data.strip()
            # Validate the raw string output before JSON parsing
            validated_raw_output = self._validate_ai_output(raw_output, text, system_instruction)
            
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
        
        system_instruction = f"Extract the {max_points} most important key points from the following text. Return each point as a separate line starting with a dash (-)."
        user_content_marker_start = "---USER TEXT START---"
        user_content_marker_end = "---USER TEXT END---"

        prompt = f"""
{system_instruction}

{user_content_marker_start}
{text}
{user_content_marker_end}

Key Points:
"""
        try:
            result = await self.agent.run(prompt)
            validated_output_str = self._validate_ai_output(result.data.strip(), text, system_instruction)
            
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

        system_instruction = f"Generate {num_questions} thoughtful questions about the following text. These questions should help someone better understand or think more deeply about the content. Return each question on a separate line."
        user_content_marker_start = "---USER TEXT START---"
        user_content_marker_end = "---USER TEXT END---"

        prompt = f"""
{system_instruction}

{user_content_marker_start}
{text}
{user_content_marker_end}

Questions:
"""
        try:
            result = await self.agent.run(prompt)
            validated_output_str = self._validate_ai_output(result.data.strip(), text, system_instruction)
            
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

        system_instruction = "Based on the provided text, please answer the given question."
        user_text_marker_start = "---USER TEXT START---"
        user_text_marker_end = "---USER TEXT END---"
        user_question_marker_start = "---USER QUESTION START---"
        user_question_marker_end = "---USER QUESTION END---"

        prompt = f"""
{system_instruction}

{user_text_marker_start}
{text}
{user_text_marker_end}

{user_question_marker_start}
{question}
{user_question_marker_end}

Answer:
"""
        try:
            result = await self.agent.run(prompt)
            # Pass `text` (sanitized user context) and `system_instruction`.
            # `question` is also part of the prompt but `text` is the primary user-generated free-form content.
            validated_output = self._validate_ai_output(result.data.strip(), text, system_instruction)
            return validated_output
        except Exception as e:
            logger.error(f"AI agent error in question answering: {e}")
            raise TransientAIError(f"Failed to answer question: {str(e)}")

    async def process_batch(self, batch_request: BatchTextProcessingRequest) -> BatchTextProcessingResponse:
        """Process a batch of text processing requests concurrently with resilience."""
        start_time = time.time()
        total_requests = len(batch_request.requests)
        batch_id = batch_request.batch_id or f"batch_{int(time.time())}"

        logger.info(f"Processing batch of {total_requests} requests for batch_id: {batch_id}")

        semaphore = asyncio.Semaphore(settings.BATCH_AI_CONCURRENCY_LIMIT)
        tasks = []

        async def _process_single_request_in_batch(index: int, item_request: TextProcessingRequest) -> BatchProcessingItem:
            """Helper function to process a single request within the batch with resilience."""
            async with semaphore:
                try:
                    # Ensure the operation is valid before processing
                    # No sanitization needed for item_request.operation itself as it's an enum/string check
                    if not hasattr(ProcessingOperation, item_request.operation.upper()):
                        raise ValueError(f"Unsupported operation: {item_request.operation}")
                    
                    # Create a new TextProcessingRequest object for process_text
                    # process_text will handle the sanitization of its inputs
                    current_request = TextProcessingRequest(
                        text=item_request.text, # Pass original text
                        operation=ProcessingOperation[item_request.operation.upper()],
                        options=item_request.options, # Pass original options
                        question=item_request.question # Pass original question
                    )
                    
                    # Process with resilience (this will use the resilience decorators)
                    # process_text will sanitize
                    response = await self.process_text(current_request)
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.COMPLETED, response=response)
                    
                except ServiceUnavailableError as e:
                    logger.warning(f"Batch item {index} (batch_id: {batch_id}) degraded service: {str(e)}")
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.FAILED, error=str(e))

                except Exception as e:
                    logger.error(f"Batch item {index} (batch_id: {batch_id}) failed: {str(e)}")
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.FAILED, error=str(e))

        for i, request_item in enumerate(batch_request.requests):
            task = _process_single_request_in_batch(i, request_item)
            tasks.append(task)

        results: List[BatchProcessingItem] = await asyncio.gather(*tasks, return_exceptions=False)

        completed_count = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
        failed_count = total_requests - completed_count
        total_time = time.time() - start_time

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


# Global service instance
text_processor = TextProcessorService()
