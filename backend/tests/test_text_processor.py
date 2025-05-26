"""Tests for the text processor service."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_models_info():
    """Test getting model information."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "current_model" in data
    assert "temperature" in data
    assert "status" in data


def test_process_text_without_api_key():
    """Test text processing without API key (should fail gracefully)."""
    response = client.post("/api/v1/process-text", json={
        "text": "This is a test text.",
        "prompt": "Please summarize this text:"
    })
    # Should return 503 if no API key is configured
    assert response.status_code in [503, 200]


def test_process_text_invalid_request():
    """Test text processing with invalid request."""
    response = client.post("/api/v1/process-text", json={
        "prompt": "Please summarize this text:"
        # Missing required 'text' field
    })
    assert response.status_code == 422  # Validation error


def test_process_text_empty_text():
    """Test text processing with empty text."""
    response = client.post("/api/v1/process-text", json={
        "text": "",
        "prompt": "Please summarize this text:"
    })
    # Should handle empty text gracefully
    assert response.status_code in [400, 422, 503] 