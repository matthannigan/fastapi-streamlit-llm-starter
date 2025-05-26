"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.app.main import app
from shared.models import ProcessingOperation

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "ai_model_available" in data

class TestOperationsEndpoint:
    """Test operations endpoint."""
    
    def test_get_operations(self, client: TestClient):
        """Test getting available operations."""
        response = client.get("/operations")
        assert response.status_code == 200
        
        data = response.json()
        assert "operations" in data
        assert len(data["operations"]) > 0
        
        # Check first operation structure
        op = data["operations"][0]
        assert "id" in op
        assert "name" in op
        assert "description" in op
        assert "options" in op

class TestProcessEndpoint:
    """Test text processing endpoint."""
    
    def test_process_summarize(self, client: TestClient, sample_text):
        """Test text summarization."""
        request_data = {
            "text": sample_text,
            "operation": "summarize",
            "options": {"max_length": 100}
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "summarize"
        assert "result" in data
        assert "processing_time" in data
        assert "timestamp" in data
    
    def test_process_sentiment(self, client: TestClient, sample_text):
        """Test sentiment analysis."""
        request_data = {
            "text": sample_text,
            "operation": "sentiment"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "sentiment"
        assert "sentiment" in data
    
    def test_process_qa_without_question(self, client: TestClient, sample_text):
        """Test Q&A without question returns error."""
        request_data = {
            "text": sample_text,
            "operation": "qa"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 400
    
    def test_process_qa_with_question(self, client: TestClient, sample_text):
        """Test Q&A with question."""
        request_data = {
            "text": sample_text,
            "operation": "qa",
            "question": "What is artificial intelligence?"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "qa"
        assert "result" in data
    
    def test_process_invalid_operation(self, client: TestClient, sample_text):
        """Test invalid operation returns error."""
        request_data = {
            "text": sample_text,
            "operation": "invalid_operation"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_process_empty_text(self, client: TestClient):
        """Test empty text returns validation error."""
        request_data = {
            "text": "",
            "operation": "summarize"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 422
    
    def test_process_text_too_long(self, client: TestClient):
        """Test text too long returns validation error."""
        long_text = "A" * 15000  # Exceeds max length
        request_data = {
            "text": long_text,
            "operation": "summarize"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 422

class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are set correctly."""
        response = client.options("/health")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

class TestErrorHandling:
    """Test error handling."""
    
    def test_404_endpoint(self, client: TestClient):
        """Test 404 for non-existent endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_api_docs(self, client: TestClient):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema(self, client: TestClient):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "AI Text Processor API"

 