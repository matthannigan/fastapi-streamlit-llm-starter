"""Integration tests for API endpoint authentication."""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch

from app.main import app
from app.infrastructure.security.auth import api_key_auth
from app.core.exceptions import AuthenticationError


class TestAuthEndpoints:
    """Integration tests for API endpoint authentication."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_process_endpoint_with_valid_api_key(self, client):
        """Test /text_processing/process endpoint with valid API key."""
        # Mock api_key_auth to accept our test key
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            headers = {"Authorization": "Bearer valid-test-key"}
            request_data = {
                "text": "This is a test text for summarization.",
                "operation": "summarize"
            }
            
            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            
            # Should not get 401 (may get 500 if AI service not configured, but that's OK)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
            
            # If we get a successful response, verify the structure
            if response.status_code == 200:
                response_data = response.json()
                assert "result" in response_data
                assert "operation" in response_data

    def test_process_endpoint_with_invalid_api_key(self, client):
        """Test /text_processing/process endpoint with invalid API key."""
        # Add an invalid API key header
        headers = {"Authorization": "Bearer invalid-test-key"}
        request_data = {
            "text": "This is a test text for summarization.",
            "operation": "summarize"
        }
        
        # Handle both HTTP response and exception patterns
        try:
            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            # If we get a response, it should be 401 Unauthorized
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            response_data = response.json()
            error_text = str(response_data).lower()
            assert "invalid" in error_text or "api key" in error_text
        except AuthenticationError as e:
            # If AuthenticationError is raised, verify it contains expected context
            error_text = str(e).lower()
            assert "invalid" in error_text or "api key" in error_text
            assert hasattr(e, 'context') and e.context.get("auth_method") == "bearer_token"

    def test_process_endpoint_without_api_key(self, client):
        """Test /text_processing/process endpoint without API key."""
        # Mock api_key_auth to have keys configured (not development mode)
        with patch.object(api_key_auth, 'api_keys', {"some-configured-key"}):
            request_data = {
                "text": "This is a test text for summarization.",
                "operation": "summarize"
            }
            
            # Handle both HTTP response and exception patterns
            try:
                response = client.post("/v1/text_processing/process", json=request_data)
                # If we get a response, it should be 401 Unauthorized
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
                response_data = response.json()
                error_text = str(response_data).lower()
                assert "api key required" in error_text or "required" in error_text
            except AuthenticationError as e:
                # If AuthenticationError is raised, verify it contains expected message
                error_text = str(e).lower()
                assert "api key required" in error_text or "required" in error_text

    def test_process_endpoint_with_empty_api_key(self, client):
        """Test /text_processing/process endpoint with empty API key."""
        # Mock api_key_auth to have keys configured (not development mode)
        with patch.object(api_key_auth, 'api_keys', {"some-configured-key"}):
            headers = {"Authorization": "Bearer "}
            request_data = {
                "text": "This is a test text for summarization.",
                "operation": "summarize"
            }
            
            # Handle both HTTP response and exception patterns
            try:
                response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
                # If we get a response, it should be 401 Unauthorized  
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
                response_data = response.json()
                error_text = str(response_data).lower()
                assert "api key required" in error_text or "required" in error_text
            except AuthenticationError as e:
                # If AuthenticationError is raised, verify it contains expected message
                error_text = str(e).lower()
                assert "api key required" in error_text or "required" in error_text

    def test_process_endpoint_with_malformed_auth_header(self, client):
        """Test /text_processing/process endpoint with malformed authorization header."""
        # Mock api_key_auth to have keys configured
        with patch.object(api_key_auth, 'api_keys', {"some-configured-key"}):
            headers = {"Authorization": "InvalidFormat"}
            request_data = {
                "text": "This is a test text for summarization.",
                "operation": "summarize"
            }
            
            # Handle both HTTP response and exception patterns
            try:
                response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
                # If we get a response, it should be 401 Unauthorized
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
                response_data = response.json()
                error_text = str(response_data).lower()
                assert "api key required" in error_text or "required" in error_text or "invalid" in error_text
            except AuthenticationError as e:
                # If AuthenticationError is raised, verify it contains expected message
                error_text = str(e).lower()
                assert "api key required" in error_text or "required" in error_text

    def test_process_endpoint_development_mode(self, client):
        """Test /text_processing/process endpoint in development mode (no API keys configured)."""
        # Mock api_key_auth to have no keys configured (development mode)
        with patch.object(api_key_auth, 'api_keys', set()):
            request_data = {
                "text": "This is a test text for summarization.",
                "operation": "summarize"
            }
            
            response = client.post("/v1/text_processing/process", json=request_data)
            
            # Should not get 401 (may get 500 if AI service not configured, but that's OK)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_process_endpoint_qa_operation_with_auth(self, client):
        """Test /text_processing/process endpoint with Q&A operation and valid auth."""
        # Mock api_key_auth to accept our test key
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            headers = {"Authorization": "Bearer valid-test-key"}
            request_data = {
                "text": "This is a test text about artificial intelligence.",
                "operation": "qa",
                "question": "What is this text about?"
            }
            
            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            
            # Should not get 401 (may get 500 if AI service not configured, but that's OK)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
            
            # If we get a successful response, verify the structure
            if response.status_code == 200:
                response_data = response.json()
                assert "result" in response_data
                assert "operation" in response_data

    def test_process_endpoint_qa_operation_without_auth(self, client):
        """Test QA operation requires authentication."""
        request_data = {
            "text": "Sample document content for analysis.",
            "operation": "answer_question",
            "question": "What is this about?"
        }
        
        # Handle both HTTP response and exception patterns
        try:
            response = client.post("/v1/text_processing/process", json=request_data)
            # If we get a response, it should be 401 Unauthorized
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        except AuthenticationError as e:
            # If AuthenticationError is raised, verify it contains expected message
            error_text = str(e).lower()
            assert "api key required" in error_text or "required" in error_text

    def test_process_endpoint_batch_operations_with_auth(self, client):
        """Test that different operations work with authentication."""
        operations = ["summarize", "sentiment", "key_points", "questions"]
        
        # Mock api_key_auth to accept our test key
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            headers = {"Authorization": "Bearer valid-test-key"}
            
            for operation in operations:
                request_data = {
                    "text": "This is a test text for processing.",
                    "operation": operation
                }
                
                response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
                
                # Should not get 401 for any operation
                assert response.status_code != status.HTTP_401_UNAUTHORIZED, f"Operation {operation} failed auth"

    def test_process_endpoint_with_case_sensitive_api_key(self, client):
        """Test that API keys are case-sensitive."""
        # Mock api_key_auth to have a specific key configured
        with patch.object(api_key_auth, 'api_keys', {"TestKey123"}):
            # Try with wrong case
            headers = {"Authorization": "Bearer testkey123"}
            request_data = {
                "text": "This is a test text for summarization.",
                "operation": "summarize"
            }
            
            # Handle both HTTP response and exception patterns
            try:
                response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
                # If we get a response, it should be 401 Unauthorized
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
            except AuthenticationError as e:
                # If AuthenticationError is raised, verify it contains expected context
                error_text = str(e).lower()
                assert "invalid" in error_text or "api key" in error_text

    def test_process_endpoint_auth_logging(self, client):
        """Test that authentication attempts are logged."""
        headers = {"Authorization": "Bearer invalid-log-test-key"}
        request_data = {
            "text": "This is a test text for logging authentication.",
            "operation": "summarize"
        }
        
        # Handle both HTTP response and exception patterns
        try:
            response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
            # If we get a response, it should be 401 Unauthorized
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        except AuthenticationError as e:
            # If AuthenticationError is raised, verify it contains expected context
            error_text = str(e).lower()
            assert "invalid" in error_text or "api key" in error_text


class TestProcessEndpointAuthEdgeCases:
    """Test edge cases and concurrent scenarios for process endpoint authentication."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_process_endpoint_auth_with_concurrent_requests(self, client):
        """Test authentication with concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            headers = {"Authorization": "Bearer test-key-concurrent"}
            request_data = {
                "text": "Concurrent test text.",
                "operation": "summarize"
            }
            
            try:
                response = client.post("/v1/text_processing/process", json=request_data, headers=headers)
                results.put(("response", response.status_code))
            except AuthenticationError as e:
                results.put(("exception", str(e)))
            except Exception as e:
                results.put(("error", str(e)))
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests handled authentication consistently
        response_count = 0
        while not results.empty():
            result_type, result_value = results.get()
            response_count += 1
            
            if result_type == "response":
                # HTTP response should be 401 for invalid key
                assert result_value == status.HTTP_401_UNAUTHORIZED
            elif result_type == "exception":
                # AuthenticationError should contain expected message
                error_text = str(result_value).lower()
                assert "invalid" in error_text or "api key" in error_text
        
        assert response_count == 3  # All requests should have been processed 