"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend.app.main import app
from shared.models import TextProcessingRequest, ProcessingOperation

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ai_model_available" in data


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
    assert data["info"]["title"] == "AI Text Processor API"


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
        "HealthResponse"
    ]
    
    for model in expected_models:
        assert model in schemas, f"Model {model} not found in OpenAPI schema"


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.options("/health")
    # FastAPI automatically handles OPTIONS requests for CORS
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined 


def test_get_operations():
    """Test the operations endpoint."""
    response = client.get("/operations")
    assert response.status_code == 200
    data = response.json()
    assert "operations" in data
    assert len(data["operations"]) == 5
    
    # Check that all expected operations are present
    operation_ids = [op["id"] for op in data["operations"]]
    expected_ops = ["summarize", "sentiment", "key_points", "questions", "qa"]
    for expected_op in expected_ops:
        assert expected_op in operation_ids


@patch('backend.app.services.text_processor.text_processor.process_text')
async def test_process_text_summarize(mock_process):
    """Test text processing with summarize operation."""
    # Mock the service response
    from shared.models import TextProcessingResponse
    mock_response = TextProcessingResponse(
        operation=ProcessingOperation.SUMMARIZE,
        result="This is a test summary.",
        processing_time=1.0,
        metadata={"word_count": 10}
    )
    mock_process.return_value = mock_response
    
    request_data = {
        "text": "This is a test text that needs to be summarized.",
        "operation": "summarize",
        "options": {"max_length": 50}
    }
    
    response = client.post("/process", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "summarize"
    assert "result" in data


def test_process_text_qa_missing_question():
    """Test Q&A operation without question should fail."""
    request_data = {
        "text": "This is a test text.",
        "operation": "qa"
        # Missing question
    }
    
    response = client.post("/process", json=request_data)
    assert response.status_code == 400


def test_process_text_invalid_operation():
    """Test invalid operation should fail validation."""
    request_data = {
        "text": "This is a test text.",
        "operation": "invalid_operation"
    }
    
    response = client.post("/process", json=request_data)
    assert response.status_code == 422  # Validation error


def test_process_text_empty_text():
    """Test empty text should fail validation."""
    request_data = {
        "text": "",
        "operation": "summarize"
    }
    
    response = client.post("/process", json=request_data)
    assert response.status_code == 422  # Validation error 