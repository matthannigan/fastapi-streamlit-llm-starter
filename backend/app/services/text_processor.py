"""Text processing service with LLM integration."""

import asyncio
import time
from typing import Dict, Any, List
import logging
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

from shared.models import (
    ProcessingOperation, 
    TextProcessingRequest, 
    TextProcessingResponse,
    SentimentResult
)
from backend.app.config import settings

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
        """Process text based on the requested operation."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing text with operation: {request.operation}")
            
            # Route to specific processing method
            if request.operation == ProcessingOperation.SUMMARIZE:
                result = await self._summarize_text(request.text, request.options)
            elif request.operation == ProcessingOperation.SENTIMENT:
                result = await self._analyze_sentiment(request.text)
            elif request.operation == ProcessingOperation.KEY_POINTS:
                result = await self._extract_key_points(request.text, request.options)
            elif request.operation == ProcessingOperation.QUESTIONS:
                result = await self._generate_questions(request.text, request.options)
            elif request.operation == ProcessingOperation.QA:
                result = await self._answer_question(request.text, request.question)
            else:
                raise ValueError(f"Unsupported operation: {request.operation}")
            
            processing_time = time.time() - start_time
            
            # Create response with timing metadata
            response = TextProcessingResponse(
                operation=request.operation,
                processing_time=processing_time,
                metadata={"word_count": len(request.text.split())}
            )
            
            # Set result based on operation type
            if request.operation == ProcessingOperation.SENTIMENT:
                response.sentiment = result
            elif request.operation == ProcessingOperation.KEY_POINTS:
                response.key_points = result
            elif request.operation == ProcessingOperation.QUESTIONS:
                response.questions = result
            else:
                response.result = result
                
            logger.info(f"Processing completed in {processing_time:.2f}s")
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
        """
        
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
        """
        
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
        """
        
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
        """
        
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
        """
        
        result = await self.agent.run(prompt)
        return result.data.strip()

# Global service instance
text_processor = TextProcessorService() 