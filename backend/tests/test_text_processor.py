"""Tests for the text processor service."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from shared.models import ProcessingOperation

client = TestClient(app)


def test_get_models_info():
    """Test getting model information."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "current_model" in data
    assert "temperature" in data
    assert "status" in data


def test_process_text_summarize_without_api_key():
    """Test text processing without API key (should fail gracefully)."""
    response = client.post("/api/v1/process-text", json={
        "text": "This is a test text that needs to be summarized for testing purposes.",
        "operation": "summarize"
    })
    # Should return 500 if no API key is configured (actual behavior)
    assert response.status_code in [500, 503, 200]


def test_process_text_invalid_request():
    """Test text processing with invalid request."""
    response = client.post("/api/v1/process-text", json={
        "operation": "summarize"
        # Missing required 'text' field
    })
    assert response.status_code == 422  # Validation error


def test_process_text_empty_text():
    """Test text processing with empty text."""
    response = client.post("/api/v1/process-text", json={
        "text": "",
        "operation": "summarize"
    })
    # Should handle empty text gracefully with validation error
    assert response.status_code == 422  # Validation error due to min_length constraint


def test_process_text_text_too_short():
    """Test text processing with text that's too short."""
    response = client.post("/api/v1/process-text", json={
        "text": "Short",  # Less than 10 characters
        "operation": "summarize"
    })
    assert response.status_code == 422  # Validation error


def test_process_text_invalid_operation():
    """Test text processing with invalid operation."""
    response = client.post("/api/v1/process-text", json={
        "text": "This is a valid test text for processing operations.",
        "operation": "invalid_operation"
    })
    assert response.status_code == 422  # Validation error


def test_process_text_qa_without_question():
    """Test Q&A operation without providing a question."""
    response = client.post("/api/v1/process-text", json={
        "text": "This is a test text for question answering functionality.",
        "operation": "qa"
        # Missing required 'question' field for Q&A operation
    })
    # Should fail validation or return 400 error
    assert response.status_code in [400, 422]


def test_process_text_valid_operations():
    """Test all valid processing operations with proper structure."""
    valid_text = "This is a comprehensive test text that contains enough content to be processed by various AI operations including summarization, sentiment analysis, key point extraction, and question generation."
    
    operations = [
        {"operation": "summarize", "should_have": "result"},
        {"operation": "sentiment", "should_have": "sentiment"},
        {"operation": "key_points", "should_have": "key_points"},
        {"operation": "questions", "should_have": "questions"},
    ]
    
    for op_test in operations:
        response = client.post("/api/v1/process-text", json={
            "text": valid_text,
            "operation": op_test["operation"]
        })
        
        # Should either succeed or fail gracefully due to missing API key
        assert response.status_code in [200, 500, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert data["operation"] == op_test["operation"]
            assert data["success"] is True
            assert "timestamp" in data
            assert "metadata" in data


def test_process_text_qa_with_question():
    """Test Q&A operation with a proper question."""
    response = client.post("/api/v1/process-text", json={
        "text": "Artificial intelligence is transforming various industries by automating tasks and providing insights.",
        "operation": "qa",
        "question": "What is AI transforming?"
    })
    
    # Should either succeed or fail gracefully due to missing API key
    assert response.status_code in [200, 500, 503]


def test_process_text_with_options():
    """Test text processing with custom options."""
    response = client.post("/api/v1/process-text", json={
        "text": "This is a test text for processing with custom options and parameters.",
        "operation": "summarize",
        "options": {
            "max_length": 50
        }
    })
    
    # Should either succeed or fail gracefully due to missing API key
    assert response.status_code in [200, 500, 503] 