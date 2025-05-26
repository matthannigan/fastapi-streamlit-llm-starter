"""Text processing service with LLM integration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_ai import Agent
from app.config import settings
import logging

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


class TextRequest(BaseModel):
    """Request model for text processing."""
    text: str
    prompt: str = "Please analyze and improve this text:"


class TextResponse(BaseModel):
    """Response model for text processing."""
    original_text: str
    processed_text: str
    model_used: str


@router.post("/process-text", response_model=TextResponse)
async def process_text(request: TextRequest):
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
    
    try:
        # Combine prompt and text
        full_prompt = f"{request.prompt}\n\nText to process:\n{request.text}"
        
        # Process with AI agent
        result = await agent.run(full_prompt)
        
        return TextResponse(
            original_text=request.text,
            processed_text=result.data,
            model_used=settings.ai_model
        )
    
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """Get information about available models."""
    return {
        "current_model": settings.ai_model,
        "temperature": settings.ai_temperature,
        "status": "configured" if settings.gemini_api_key else "not_configured"
    } 