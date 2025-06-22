"""
Tests for shared models and enums.
Extracted from test_models.py
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models import (
    ErrorResponse,
    HealthResponse
)

class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_basic_error(self):
        """Test basic error response."""
        error = ErrorResponse(
            error="Something went wrong",
            error_code="PROCESSING_ERROR"
        )
        
        assert error.success is False
        assert error.error == "Something went wrong"
        assert error.error_code == "PROCESSING_ERROR"
        assert isinstance(error.timestamp, datetime)
    
    def test_error_with_details(self):
        """Test error with additional details."""
        error = ErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"field": "text", "issue": "too short"}
        )
        
        assert error.details["field"] == "text"

class TestHealthResponse:
    """Test HealthResponse model."""
    
    def test_healthy_response(self):
        """Test healthy response."""
        health = HealthResponse(
            ai_model_available=True
        )
        
        assert health.status == "healthy"
        assert health.ai_model_available is True
        assert health.version == "1.0.0"
    
    def test_unhealthy_response(self):
        """Test unhealthy response."""
        health = HealthResponse(
            status="unhealthy",
            ai_model_available=False
        )
        
        assert health.status == "unhealthy"
        assert health.ai_model_available is False
