"""Text processing service with LLM integration."""

from fastapi import APIRouter, HTTPException
from pydantic_ai import Agent
from app.config import settings
from shared.models import (
    TextProcessingRequest, 
    TextProcessingResponse, 
    ProcessingOperation,
    SentimentResult,
    ErrorResponse,
    ModelInfo
)
import logging
import time
from datetime import datetime
from typing import List

# Set up logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the AI agent
try:
    agent = Agent(
        model=settings.ai_model,
        system_prompt="You are a helpful AI assistant that processes text and provides useful responses.",
    )
except Exception as e:
    logger.error(f"Failed to initialize AI agent: {e}")
    agent = None


async def process_summarize(text: str, options: dict) -> str:
    """Process text summarization."""
    max_length = options.get("max_length", 150)
    prompt = f"Summarize the following text in approximately {max_length} words:\n\n{text}"
    result = await agent.run(prompt)
    return result.data


async def process_sentiment(text: str, options: dict) -> SentimentResult:
    """Process sentiment analysis."""
    prompt = f"""Analyze the sentiment of the following text and provide:
    1. Overall sentiment (positive, negative, or neutral)
    2. Confidence score (0.0 to 1.0)
    3. Brief explanation
    
    Text: {text}
    
    Respond in this format:
    Sentiment: [positive/negative/neutral]
    Confidence: [0.0-1.0]
    Explanation: [brief explanation]"""
    
    result = await agent.run(prompt)
    response = result.data
    
    # Parse the response (simplified parsing - in production, use more robust parsing)
    lines = response.split('\n')
    sentiment = "neutral"
    confidence = 0.5
    explanation = "Unable to determine sentiment"
    
    for line in lines:
        if line.startswith("Sentiment:"):
            sentiment = line.split(":", 1)[1].strip().lower()
        elif line.startswith("Confidence:"):
            try:
                confidence = float(line.split(":", 1)[1].strip())
            except ValueError:
                confidence = 0.5
        elif line.startswith("Explanation:"):
            explanation = line.split(":", 1)[1].strip()
    
    return SentimentResult(
        sentiment=sentiment,
        confidence=confidence,
        explanation=explanation
    )


async def process_key_points(text: str, options: dict) -> List[str]:
    """Extract key points from text."""
    max_points = options.get("max_points", 5)
    prompt = f"Extract the {max_points} most important key points from the following text. Return each point as a separate line starting with '- ':\n\n{text}"
    result = await agent.run(prompt)
    
    # Parse key points from response
    points = []
    for line in result.data.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            points.append(line[2:])
        elif line and not points:  # If no bullet points, treat each line as a point
            points.append(line)
    
    return points[:max_points]


async def process_questions(text: str, options: dict) -> List[str]:
    """Generate questions from text."""
    max_questions = options.get("max_questions", 3)
    prompt = f"Generate {max_questions} thoughtful questions based on the following text. Return each question on a separate line:\n\n{text}"
    result = await agent.run(prompt)
    
    # Parse questions from response
    questions = []
    for line in result.data.split('\n'):
        line = line.strip()
        if line and line.endswith('?'):
            questions.append(line)
    
    return questions[:max_questions]


async def process_qa(text: str, question: str, options: dict) -> str:
    """Answer a question based on the provided text."""
    prompt = f"Based on the following text, answer this question: {question}\n\nText:\n{text}"
    result = await agent.run(prompt)
    return result.data


@router.post("/process-text", response_model=TextProcessingResponse)
async def process_text(request: TextProcessingRequest):
    """Process text using the configured LLM."""
    if not agent:
        raise HTTPException(
            status_code=503, 
            detail="AI service is not available. Please check your configuration."
        )
    
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI API key is not configured."
        )
    
    start_time = time.time()
    
    try:
        response = TextProcessingResponse(
            operation=request.operation,
            metadata={"word_count": len(request.text.split())}
        )
        
        if request.operation == ProcessingOperation.SUMMARIZE:
            response.result = await process_summarize(request.text, request.options)
            
        elif request.operation == ProcessingOperation.SENTIMENT:
            response.sentiment = await process_sentiment(request.text, request.options)
            
        elif request.operation == ProcessingOperation.KEY_POINTS:
            response.key_points = await process_key_points(request.text, request.options)
            
        elif request.operation == ProcessingOperation.QUESTIONS:
            response.questions = await process_questions(request.text, request.options)
            
        elif request.operation == ProcessingOperation.QA:
            if not request.question:
                raise HTTPException(
                    status_code=400,
                    detail="Question is required for Q&A operation"
                )
            response.result = await process_qa(request.text, request.question, request.options)
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported operation: {request.operation}"
            )
        
        response.processing_time = time.time() - start_time
        response.metadata["model_used"] = settings.ai_model
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text: {str(e)}"
        )


@router.get("/models", response_model=ModelInfo)
async def get_available_models():
    """Get information about available models."""
    return ModelInfo(
        current_model=settings.ai_model,
        temperature=settings.ai_temperature,
        status="configured" if settings.gemini_api_key else "not_configured"
    ) 