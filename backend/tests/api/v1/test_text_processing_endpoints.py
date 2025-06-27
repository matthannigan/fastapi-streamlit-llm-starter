"""
Tests for the text processing endpoints of the FastAPI application.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.config import settings
from app.api.v1.deps import get_text_processor
from app.services.text_processor import TextProcessorService
from shared.models import (
    ProcessingOperation,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    TextProcessingRequest,
    BatchProcessingItem,
    ProcessingStatus,
    TextProcessingResponse,
    SentimentResult
)

# Default headers for authenticated requests
AUTH_HEADERS = {"Authorization": "Bearer test-api-key-12345"}

class TestOperationsEndpoint:
    """Test operations endpoint."""
    
    def test_get_operations(self, client: TestClient):
        """Test getting available operations."""
        response = client.get("/text_processing/operations")
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
    
    def test_process_summarize(self, authenticated_client, sample_text, mock_processor):
        """Test text summarization with authentication using DI override."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize",
                "options": {"max_length": 100}
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert "result" in data
            assert "processing_time" in data
            assert "timestamp" in data
            
            # Verify the mock was called
            mock_processor.process_text.assert_called_once()
            call_args = mock_processor.process_text.call_args[0][0]
            assert call_args.text == sample_text.strip()  # Text gets sanitized/stripped
            assert call_args.operation == ProcessingOperation.SUMMARIZE
            assert call_args.options == {"max_length": 100}
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_sentiment(self, authenticated_client, sample_text, mock_processor):
        """Test sentiment analysis with authentication using DI override."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "sentiment"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "sentiment"
            assert "sentiment" in data
            
            # Verify the mock was called
            mock_processor.process_text.assert_called_once()
            call_args = mock_processor.process_text.call_args[0][0]
            assert call_args.text == sample_text.strip()  # Text gets sanitized/stripped
            assert call_args.operation == ProcessingOperation.SENTIMENT
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_qa_without_question(self, authenticated_client, sample_text, mock_processor):
        """Test Q&A without question returns error."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "qa"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 400
            
            # Mock should not be called for invalid requests
            mock_processor.process_text.assert_not_called()
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_qa_with_question(self, authenticated_client, sample_text, mock_processor):
        """Test Q&A with question and authentication using DI override."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "qa",
                "question": "What is artificial intelligence?"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "qa"
            assert "result" in data
            
            # Verify the mock was called
            mock_processor.process_text.assert_called_once()
            call_args = mock_processor.process_text.call_args[0][0]
            assert call_args.text == sample_text.strip()  # Text gets sanitized/stripped
            assert call_args.operation == ProcessingOperation.QA
            assert call_args.question == "What is artificial intelligence?"
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_invalid_operation(self, authenticated_client, sample_text, mock_processor):
        """Test invalid operation returns error."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "invalid_operation"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 422  # Validation error
            
            # Mock should not be called for invalid requests
            mock_processor.process_text.assert_not_called()
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_empty_text(self, authenticated_client, mock_processor):
        """Test empty text returns validation error."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            request_data = {
                "text": "",
                "operation": "summarize"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 422
            
            # Mock should not be called for invalid requests
            mock_processor.process_text.assert_not_called()
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_text_too_long(self, authenticated_client, mock_processor):
        """Test text too long returns validation error."""
        # Override the dependency with our mock
        app.dependency_overrides[get_text_processor] = lambda: mock_processor
        
        try:
            long_text = "A" * 15000  # Exceeds max length
            request_data = {
                "text": long_text,
                "operation": "summarize"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 422
            
            # Mock should not be called for invalid requests
            mock_processor.process_text.assert_not_called()
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

class TestCacheIntegration:
    """Test cache integration with processing endpoints."""
    
    def test_process_with_cache_miss(self, authenticated_client, sample_text):
        """Test processing with cache miss."""
        from app.dependencies import get_cache_service
        from app.main import app
        
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.get_cached_response = AsyncMock(return_value=None)  # Cache miss
        mock_cache_service.cache_response = AsyncMock(return_value=None)
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize",
                "options": {"max_length": 100}
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 200
            
            # Verify cache was checked and response was stored
            mock_cache_service.get_cached_response.assert_called_once()
            mock_cache_service.cache_response.assert_called_once()
            
            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_process_with_cache_hit(self, authenticated_client, sample_text):
        """Test processing with cache hit."""
        from app.dependencies import get_cache_service
        from app.main import app
        
        # Mock cache hit
        cached_response = {
            "operation": "summarize",
            "result": "Cached summary from Redis",
            "success": True,
            "processing_time": 0.1,
            "metadata": {"word_count": 25},
            "cached_at": "2024-01-01T12:00:00",
            "cache_hit": True
        }
        
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.get_cached_response = AsyncMock(return_value=cached_response)
        mock_cache_service.cache_response = AsyncMock(return_value=None)
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }
            
            response = authenticated_client.post("/text_processing/process", json=request_data)
            assert response.status_code == 200
            
            # Verify cache was checked but not stored again
            mock_cache_service.get_cached_response.assert_called_once()
            mock_cache_service.cache_response.assert_not_called()
            
            data = response.json()
            assert data["success"] is True
            assert data["result"] == "Cached summary from Redis"
            assert data["processing_time"] == 0.1
            assert data.get("cache_hit") is True
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

class TestBatchProcessEndpoint:
    """Test the /text_processing/batch_process endpoint."""

    def test_batch_process_success(self, authenticated_client: TestClient, sample_text):
        """Test successful batch processing."""
        from app.api.v1.deps import get_text_processor
        from app.main import app
        
        request_payload_dict = {
            "requests": [
                {"text": sample_text, "operation": "summarize"},
                {"text": "Another text", "operation": "sentiment"}
            ],
            "batch_id": "test_success_batch"
        }

        mock_batch_response_dict = {
            "batch_id": "test_success_batch",
            "total_requests": 2,
            "completed": 2,
            "failed": 0,
            "results": [
                {
                    "request_index": 0, "status": "completed",
                    "response": {"operation": "summarize", "success": True, "result": "Summary."}
                },
                {
                    "request_index": 1, "status": "completed",
                    "response": {"operation": "sentiment", "success": True, "sentiment": {"sentiment": "neutral", "confidence": 0.7, "explanation": "Neutral."}}
                }
            ],
            "total_processing_time": 1.23
        }
        mock_batch_response_obj = BatchTextProcessingResponse(**mock_batch_response_dict)
        
        # Create a mock text processor service
        mock_text_processor = MagicMock()
        mock_text_processor.process_batch = AsyncMock(return_value=mock_batch_response_obj)
        
        # Override the dependency
        app.dependency_overrides[get_text_processor] = lambda: mock_text_processor
        
        try:
            response = authenticated_client.post("/text_processing/batch_process", json=request_payload_dict)

            assert response.status_code == status.HTTP_200_OK
            
            # Get the response JSON
            api_response_json = response.json()
            
            # Remove timestamp from comparison as it's generated on the fly
            if 'timestamp' in api_response_json.get('results', [{}])[0].get('response', {}):
                 for res_item in api_response_json.get('results',[]):
                     if res_item.get('response') and 'timestamp' in res_item['response']:
                        del res_item['response']['timestamp']

            # We compare the model_dump() of the mock_batch_response_obj with the response.json()
            expected_json = mock_batch_response_obj.model_dump(mode='json')
            
            # Remove timestamps from results in expected_json for comparison
            for item_result in expected_json.get("results", []):
                if item_result.get("response") and "timestamp" in item_result["response"]:
                    del item_result["response"]["timestamp"]
            if "timestamp" in expected_json: # Top-level timestamp
                del expected_json["timestamp"]
            if "timestamp" in api_response_json: # Top-level timestamp
                del api_response_json["timestamp"]

            assert api_response_json == expected_json
            
            # Verify the mock was called
            mock_text_processor.process_batch.assert_called_once()
            called_arg = mock_text_processor.process_batch.call_args[0][0]
            assert isinstance(called_arg, BatchTextProcessingRequest)
            assert called_arg.batch_id == "test_success_batch"
            assert len(called_arg.requests) == 2
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

    def test_batch_process_exceeds_limit(self, authenticated_client: TestClient, sample_text):
        """Test batch processing with too many requests."""
        original_limit = settings.MAX_BATCH_REQUESTS_PER_CALL
        settings.MAX_BATCH_REQUESTS_PER_CALL = 2  # Temporarily lower limit for test
        
        payload = {
            "requests": [
                {"text": sample_text, "operation": "summarize"},
                {"text": sample_text, "operation": "summarize"},
                {"text": sample_text, "operation": "summarize"} # 3 requests, limit is 2
            ]
        }
        response = authenticated_client.post("/text_processing/batch_process", json=payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds maximum limit" in response.json()["detail"]
        
        settings.MAX_BATCH_REQUESTS_PER_CALL = original_limit # Reset limit

    def test_batch_process_empty_requests_list(self, authenticated_client: TestClient):
        """Test batch processing with an empty requests list."""
        payload = {"requests": []}
        response = authenticated_client.post("/text_processing/batch_process", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  # Pydantic validation error
        # Check that the error is related to the empty list validation
        error_detail = response.json()
        assert "detail" in error_detail
        # The error should mention the validation issue with the requests list
        assert any("too_short" in str(error).lower() or "at least 1" in str(error).lower() 
                  for error in error_detail["detail"])

    def test_batch_process_no_auth(self, client: TestClient, sample_text):
        """Test batch processing without authentication."""
        payload = {
            "requests": [{"text": sample_text, "operation": "summarize"}]
        }
        response = client.post("/text_processing/batch_process", json=payload) # No headers
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_batch_process_invalid_auth(self, client: TestClient, sample_text):
        """Test batch processing with invalid authentication."""
        payload = {
            "requests": [{"text": sample_text, "operation": "summarize"}]
        }
        headers = {"Authorization": "Bearer invalid-api-key"}
        response = client.post("/text_processing/batch_process", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_batch_process_service_exception(self, authenticated_client: TestClient, sample_text):
        """Test batch processing when the service raises an exception."""
        from app.api.v1.deps import get_text_processor
        from app.main import app
        
        # Create a mock text processor service that raises an exception
        mock_text_processor = MagicMock()
        mock_text_processor.process_batch = AsyncMock(side_effect=Exception("Service layer error"))
        
        # Override the dependency
        app.dependency_overrides[get_text_processor] = lambda: mock_text_processor
        
        try:
            payload = {
                "requests": [{"text": sample_text, "operation": "summarize"}],
                "batch_id": "test_service_exception"
            }
            response = authenticated_client.post("/text_processing/batch_process", json=payload)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            # FastAPI HTTPException returns "detail" field, not "error"
            assert "internal server error" in response.json()["detail"].lower()
        finally:
            # Clean up the override
            app.dependency_overrides.clear()

class TestBatchStatusEndpoint:
    """Test the /text_processing/batch_status/{batch_id} endpoint."""

    def test_get_batch_status_success(self, authenticated_client: TestClient):
        """Test getting batch status successfully."""
        batch_id_test = "test_batch_123"
        response = authenticated_client.get(f"/text_processing/batch_status/{batch_id_test}")
        
        assert response.status_code == status.HTTP_200_OK
        expected_json = {
            "batch_id": batch_id_test,
            "status": "COMPLETED_SYNC",
            "message": "Batch processing is synchronous. If your request to /text_processing/batch_process completed, the results were returned then."
        }
        assert response.json() == expected_json

    def test_get_batch_status_no_auth(self, client: TestClient):
        """Test getting batch status without authentication."""
        response = client.get("/text_processing/batch_status/some_id") # No headers
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_batch_status_invalid_auth(self, client: TestClient):
        """Test getting batch status with invalid authentication."""
        headers = {"Authorization": "Bearer invalid-api-key"}
        response = client.get("/text_processing/batch_status/some_id", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_process_with_explicit_auth(self, client, sample_text):
        """Test process endpoint with explicit authentication."""
        request_data = {
            "text": sample_text,
            "operation": "summarize"
        }
        
        headers = {"Authorization": "Bearer test-api-key-12345"}
        response = client.post("/text_processing/process", json=request_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "summarize"
    
    def test_process_with_invalid_auth(self, client, sample_text):
        """Test that invalid API keys are rejected."""
        request_data = {
            "text": sample_text,
            "operation": "summarize"
        }
        
        headers = {"Authorization": "Bearer definitely-invalid-key-that-should-fail"}
        response = client.post("/text_processing/process", json=request_data, headers=headers)
        # This should fail even with Option C because it's an explicitly invalid key
        assert response.status_code == 401
        
        data = response.json()
        assert "Invalid API key" in data["detail"]
    
    def test_authenticated_client_fixture(self, authenticated_client, sample_text):
        """Test that the authenticated_client fixture works correctly."""
        request_data = {
            "text": sample_text,
            "operation": "summarize"
        }
        
        response = authenticated_client.post("/text_processing/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_operations_endpoint_with_auth(self, authenticated_client):
        """Test operations endpoint with authentication (optional auth)."""
        response = authenticated_client.get("/text_processing/operations")
        assert response.status_code == 200
        
        data = response.json()
        assert "operations" in data
        assert len(data["operations"]) > 0
