"""Shared Pydantic models for the application."""

from pydantic import BaseModel
from typing import Optional


class TextProcessingRequest(BaseModel):
    """Request model for text processing."""
    text: str
    prompt: str = "Please analyze and improve this text:"


class TextProcessingResponse(BaseModel):
    """Response model for text processing."""
    original_text: str
    processed_text: str
    model_used: str


class ModelInfo(BaseModel):
    """Model information response."""
    current_model: str
    temperature: float
    status: str


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    debug: bool 