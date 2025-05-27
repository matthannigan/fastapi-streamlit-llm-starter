"""Main FastAPI application."""

import sys
import os
# Add the root directory to Python path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    ErrorResponse,
    HealthResponse
)
from app.config import settings
from app.services.text_processor import text_processor
from app.auth import verify_api_key, optional_verify_api_key

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting FastAPI application")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AI Model: {settings.ai_model}")
    yield
    logger.info("Shutting down FastAPI application")

# Create FastAPI app
app = FastAPI(
    title="AI Text Processor API",
    description="API for processing text using AI models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# Note: mypy has issues with FastAPI's add_middleware and CORSMiddleware
# This is a known issue and the code works correctly at runtime
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.allowed_origins,  # type: ignore[call-arg]
    allow_credentials=True,  # type: ignore[call-arg]
    allow_methods=["*"],  # type: ignore[call-arg]
    allow_headers=["*"],  # type: ignore[call-arg]
)

# No routers needed - using direct service integration

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Text Processor API", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        ai_model_available=bool(settings.gemini_api_key)
    )

@app.get("/auth/status")
async def auth_status(api_key: str = Depends(verify_api_key)):
    """Check authentication status."""
    return {
        "authenticated": True,
        "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
        "message": "Authentication successful"
    }

@app.post("/process", response_model=TextProcessingResponse)
async def process_text(
    request: TextProcessingRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process text using AI models."""
    try:
        logger.info(f"Received request for operation: {request.operation}")
        
        # Validate Q&A request
        if request.operation.value == "qa" and not request.question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question is required for Q&A operation"
            )
        
        # Process the text
        result = await text_processor.process_text(request)
        
        logger.info("Request processed successfully")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process text"
        )

@app.get("/operations")
async def get_operations(api_key: str = Depends(optional_verify_api_key)):
    """Get available processing operations."""
    return {
        "operations": [
            {
                "id": "summarize",
                "name": "Summarize",
                "description": "Generate a concise summary of the text",
                "options": ["max_length"]
            },
            {
                "id": "sentiment",
                "name": "Sentiment Analysis",
                "description": "Analyze the emotional tone of the text",
                "options": []
            },
            {
                "id": "key_points",
                "name": "Key Points",
                "description": "Extract the main points from the text",
                "options": ["max_points"]
            },
            {
                "id": "questions",
                "name": "Generate Questions",
                "description": "Create questions about the text content",
                "options": ["num_questions"]
            },
            {
                "id": "qa",
                "name": "Question & Answer",
                "description": "Answer a specific question about the text",
                "options": [],
                "requires_question": True
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
