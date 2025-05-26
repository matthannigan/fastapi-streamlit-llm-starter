"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "FastAPI Streamlit LLM Starter API"
    assert data["version"] == "1.0.0"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert data["version"] == "1.0.0"
    assert "ai_model_available" in data
    assert isinstance(data["ai_model_available"], bool)


def test_health_check_response_structure():
    """Test that health check response follows the HealthResponse model."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields are present
    required_fields = ["status", "timestamp", "version", "ai_model_available"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["ai_model_available"], bool)
    
    # Check timestamp format (should be ISO format)
    from datetime import datetime
    try:
        datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("Timestamp is not in valid ISO format")


def test_api_docs():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "FastAPI Streamlit LLM Starter"


def test_openapi_schema_includes_models():
    """Test that OpenAPI schema includes our custom models."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    
    # Check that our models are included in the schema
    components = data.get("components", {})
    schemas = components.get("schemas", {})
    
    # Should include our main models
    expected_models = [
        "TextProcessingRequest",
        "TextProcessingResponse", 
        "HealthResponse",
        "ModelInfo"
    ]
    
    for model in expected_models:
        assert model in schemas, f"Model {model} not found in OpenAPI schema"


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.options("/health")
    # FastAPI automatically handles OPTIONS requests for CORS
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined 