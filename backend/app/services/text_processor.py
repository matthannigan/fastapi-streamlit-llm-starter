"""Text processing service with resilience integration."""

import sys
import os
# Add the root directory to Python path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

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
            return TextProcessingResponse(**cached_response)
        
        # Process normally if no cache hit
        start_time = time.time()
        
        try:
            logger.info(f"Processing text with operation: {request.operation}")
            
            # Validate operation first to provide better error messages
            if request.operation not in [op.value for op in ProcessingOperation]:
                raise ValueError(f"Unsupported operation: {request.operation}")
            
            # Create response with timing metadata
            processing_time = time.time() - start_time
            response = TextProcessingResponse(
                operation=request.operation,
                processing_time=processing_time,
                metadata={"word_count": len(request.text.split())}
            )
            
            # Route to specific processing method with resilience
            try:
                if request.operation == ProcessingOperation.SUMMARIZE:
                    response.result = await self._summarize_text_with_resilience(request.text, request.options)
                elif request.operation == ProcessingOperation.SENTIMENT:
                    response.sentiment = await self._analyze_sentiment_with_resilience(request.text)
                elif request.operation == ProcessingOperation.KEY_POINTS:
                    response.key_points = await self._extract_key_points_with_resilience(request.text, request.options)
                elif request.operation == ProcessingOperation.QUESTIONS:
                    response.questions = await self._generate_questions_with_resilience(request.text, request.options)
                elif request.operation == ProcessingOperation.QA:
                    response.result = await self._answer_question_with_resilience(request.text, request.question)
                else:
                    raise ValueError(f"Unsupported operation: {request.operation}")
            
            except ServiceUnavailableError:
                # Handle circuit breaker open - provide fallback
                if request.operation == ProcessingOperation.SENTIMENT:
                    response.sentiment = await self._get_fallback_sentiment()
                elif request.operation == ProcessingOperation.KEY_POINTS:
                    response.key_points = await self._get_fallback_response(request.operation, request.text)
                elif request.operation == ProcessingOperation.QUESTIONS:
                    response.questions = await self._get_fallback_response(request.operation, request.text)
                else:
                    response.result = await self._get_fallback_response(request.operation, request.text, request.question)
                
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
        max_length = options.get("max_length", 100)
        
        prompt = f"""
        Please provide a concise summary of the following text in approximately {max_length} words:
        
        Text: {text}
        
        Summary:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            return result.data.strip()
        except Exception as e:
            logger.error(f"AI agent error in summarization: {e}")
            # Convert to our custom exception for proper retry handling
            raise TransientAIError(f"Failed to summarize text: {str(e)}")
    
    async def _analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of the provided text."""
        prompt = f"""
        Analyze the sentiment of the following text. Respond with a JSON object containing:
        - sentiment: "positive", "negative", or "neutral"
        - confidence: a number between 0.0 and 1.0
        - explanation: a brief explanation of the sentiment
        
        Text: {text}
        
        Response (JSON only):
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            
            # Parse the JSON response
            import json
            try:
                sentiment_data = json.loads(result.data.strip())
                return SentimentResult(**sentiment_data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse sentiment JSON: {e}")
                # Fallback response
                return SentimentResult(
                    sentiment="neutral",
                    confidence=0.5,
                    explanation="Unable to analyze sentiment accurately"
                )
        except Exception as e:
            logger.error(f"AI agent error in sentiment analysis: {e}")
            raise TransientAIError(f"Failed to analyze sentiment: {str(e)}")
    
    async def _extract_key_points(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points from the text."""
        max_points = options.get("max_points", 5)
        
        prompt = f"""
        Extract the {max_points} most important key points from the following text.
        Return each point as a separate line starting with a dash (-).
        
        Text: {text}
        
        Key Points:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            
            # Parse the response into a list
            points = []
            for line in result.data.strip().split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    points.append(line[1:].strip())
                elif line and not line.startswith('Key Points:'):
                    points.append(line)
            
            return points[:max_points]
        except Exception as e:
            logger.error(f"AI agent error in key points extraction: {e}")
            raise TransientAIError(f"Failed to extract key points: {str(e)}")
    
    async def _generate_questions(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions about the text."""
        num_questions = options.get("num_questions", 5)
        
        prompt = f"""
        Generate {num_questions} thoughtful questions about the following text.
        These questions should help someone better understand or think more deeply about the content.
        Return each question on a separate line.
        
        Text: {text}
        
        Questions:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            
            # Parse questions into a list
            questions = []
            for line in result.data.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Questions:'):
                    # Remove numbering if present
                    if line[0].isdigit() and '.' in line[:5]:
                        line = line.split('.', 1)[1].strip()
                    questions.append(line)
            
            return questions[:num_questions]
        except Exception as e:
            logger.error(f"AI agent error in question generation: {e}")
            raise TransientAIError(f"Failed to generate questions: {str(e)}")
    
    async def _answer_question(self, text: str, question: str) -> str:
        """Answer a question about the text."""
        if not question:
            raise ValueError("Question is required for Q&A operation")
        
        prompt = f"""
        Based on the following text, please answer this question:
        
        Question: {question}
        
        Text: {text}
        
        Answer:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            return result.data.strip()
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
                    if not hasattr(ProcessingOperation, item_request.operation.upper()):
                        raise ValueError(f"Unsupported operation: {item_request.operation}")
                    
                    # Create a new TextProcessingRequest object
                    current_request = TextProcessingRequest(
                        text=item_request.text,
                        operation=ProcessingOperation[item_request.operation.upper()],
                        options=item_request.options,
                        question=item_request.question
                    )
                    
                    # Process with resilience (this will use the resilience decorators)
                    response = await self.process_text(current_request)
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.COMPLETED, response=response)
                    
                except ServiceUnavailableError as e:
                    logger.warning(f"Batch item {index} (batch_id: {batch_id}) degraded service: {str(e)}")
                    # For circuit breaker open, we might want to return a partial success
                    # depending on business requirements
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
