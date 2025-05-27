"""Text processing service with LLM integration."""

import sys
import os
# Add the root directory to Python path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import time
from typing import Dict, Any, List
import logging
from pydantic_ai import Agent

from shared.models import (
    ProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    SentimentResult
)
from app.config import settings
from app.services.cache import ai_cache

logger = logging.getLogger(__name__)

class TextProcessorService:
    """Service for processing text using AI models."""
    
    def __init__(self):
        """Initialize the text processor with AI agent."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.agent = Agent(
            model=settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
    
    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """Process text with caching support."""
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
            
            # Route to specific processing method and set appropriate response field
            if request.operation == ProcessingOperation.SUMMARIZE:
                response.result = await self._summarize_text(request.text, request.options)
            elif request.operation == ProcessingOperation.SENTIMENT:
                response.sentiment = await self._analyze_sentiment(request.text)
            elif request.operation == ProcessingOperation.KEY_POINTS:
                response.key_points = await self._extract_key_points(request.text, request.options)
            elif request.operation == ProcessingOperation.QUESTIONS:
                response.questions = await self._generate_questions(request.text, request.options)
            elif request.operation == ProcessingOperation.QA:
                response.result = await self._answer_question(request.text, request.question)
            else:
                # This should not happen due to the validation above, but keeping for safety
                raise ValueError(f"Unsupported operation: {request.operation}")
            
            # Cache the successful response
            await ai_cache.cache_response(
                request.text,
                operation_value,
                request.options or {},
                response.model_dump(),
                request.question
            )
                
            logger.info(f"Processing completed in {processing_time:.2f}s")  # noqa: E231
            return response
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    async def _summarize_text(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize the provided text."""
        max_length = options.get("max_length", 100)
        
        prompt = f"""
        Please provide a concise summary of the following text in approximately {max_length} words:
        
        Text: {text}
        
        Summary:
        """  # noqa: E231,E221
        
        result = await self.agent.run(prompt)
        return result.data.strip()
    
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
    
    async def _extract_key_points(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points from the text."""
        max_points = options.get("max_points", 5)
        
        prompt = f"""
        Extract the {max_points} most important key points from the following text.
        Return each point as a separate line starting with a dash (-).
        
        Text: {text}
        
        Key Points:
        """  # noqa: E231,E221
        
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
        
        result = await self.agent.run(prompt)
        return result.data.strip()

# Global service instance
text_processor = TextProcessorService()
