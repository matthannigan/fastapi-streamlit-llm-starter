"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.text_processor import router as text_processor_router
from shared.models import HealthResponse

# Create FastAPI app
app = FastAPI(
    title="FastAPI Streamlit LLM Starter",
    description="A starter template for FastAPI backend with Streamlit frontend and LLM integration",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(text_processor_router, prefix="/api/v1", tags=["text-processing"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FastAPI Streamlit LLM Starter API", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Check if AI model is available
    ai_model_available = bool(settings.gemini_api_key)
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ai_model_available=ai_model_available
    ) 