"""
Comprehensive tests for Global Exception Handler.

Tests cover exception handling, HTTP status mapping, error response formatting,
request correlation, and special case handling.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError

from app.core.middleware.global_exception_handler import setup_global_exception_handler
from app.core.config import Settings
from app.core.exceptions import (
    ApplicationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    BusinessLogicError,
    InfrastructureError,
    TransientAIError,
    PermanentAIError
)
from app.schemas.common import ErrorResponse


class TestGlobalExceptionHandler:
    """Test Global Exception Handler functionality."""
    
    @pytest.fixture
    def settings(self):
        """Test settings for exception handler configuration."""
        settings = Mock(spec=Settings)
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI app with global exception handler configured."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/validation-error")
        async def validation_error_endpoint():
            raise ValidationError("Invalid input data")
        
        @app.get("/auth-error")
        async def auth_error_endpoint():
            raise AuthenticationError("Invalid credentials")
        
        @app.get("/authz-error")
        async def authz_error_endpoint():
            raise AuthorizationError("Access denied")
        
        @app.get("/config-error")
        async def config_error_endpoint():
            raise ConfigurationError("Missing configuration")
        
        @app.get("/business-error")
        async def business_error_endpoint():
            raise BusinessLogicError("Business rule violated")
        
        @app.get("/infra-error")
        async def infra_error_endpoint():
            raise InfrastructureError("Database connection failed")
        
        @app.get("/transient-ai-error")
        async def transient_ai_error_endpoint():
            raise TransientAIError("AI service temporarily unavailable")
        
        @app.get("/permanent-ai-error")
        async def permanent_ai_error_endpoint():
            raise PermanentAIError("AI service configuration error")
        
        @app.get("/generic-error")
        async def generic_error_endpoint():
            raise Exception("Unexpected error")
        
        @app.get("/api-version-error")
        async def api_version_error_endpoint():
            error = ApplicationError("Unsupported API version")
            error.context = {
                'error_code': 'API_VERSION_NOT_SUPPORTED',
                'requested_version': '3.0',
                'supported_versions': ['1.0', '2.0'],
                'current_version': '2.0'
            }
            raise error
        
        @app.post("/validation")
        async def validation_endpoint(data: dict):
            # This will trigger FastAPI request validation
            return {"received": data}
        
        setup_global_exception_handler(app, settings)
        return app
    
    def test_setup_global_exception_handler(self, settings):
        """Test exception handler setup function."""
        app = FastAPI()
        
        # Count initial exception handlers
        initial_handlers = len(app.exception_handlers)
        
        setup_global_exception_handler(app, settings)
        
        # Should add exception handlers
        assert len(app.exception_handlers) > initial_handlers
    
    def test_successful_request_no_exception(self, app):
        """Test that successful requests are not affected by exception handler."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_validation_error_handling(self, mock_logger, app):
        """Test handling of ValidationError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        # Make the request - the exception handler should catch it and return JSON
        response = client.get("/validation-error")
        
        # The global exception handler should convert the exception to an HTTP response
        assert response.status_code == 400
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert data["error"] == "Invalid request data"  # ValidationError maps to this message
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "timestamp" in data
        
        # Should log the error
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_authentication_error_handling(self, mock_logger, app):
        """Test handling of AuthenticationError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/auth-error")
        
        assert response.status_code == 401  # AuthenticationError -> 401
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "Authentication failed"
        assert data["error_code"] == "AUTHENTICATION_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_authorization_error_handling(self, mock_logger, app):
        """Test handling of AuthorizationError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/authz-error")
        
        assert response.status_code == 403  # AuthorizationError -> 403
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "Access denied"
        assert data["error_code"] == "AUTHORIZATION_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_configuration_error_handling(self, mock_logger, app):
        """Test handling of ConfigurationError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/config-error")
        
        assert response.status_code == 500  # ConfigurationError -> 500
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "Service configuration error"
        assert data["error_code"] == "CONFIGURATION_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_business_logic_error_handling(self, mock_logger, app):
        """Test handling of BusinessLogicError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/business-error")
        
        assert response.status_code == 422  # BusinessLogicError -> 422
        data = response.json()
        
        assert data["success"] is False
        assert "Invalid request data" in data["error"]
        assert data["error_code"] == "VALIDATION_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_infrastructure_error_handling(self, mock_logger, app):
        """Test handling of InfrastructureError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/infra-error")
        
        assert response.status_code == 500  # InfrastructureError -> 500
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "External service error"
        assert data["error_code"] == "INFRASTRUCTURE_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_transient_ai_error_handling(self, mock_logger, app):
        """Test handling of TransientAIError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/transient-ai-error")
        
        assert response.status_code == 503  # TransientAIError -> 503
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "AI service temporarily unavailable"
        assert data["error_code"] == "SERVICE_UNAVAILABLE"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_permanent_ai_error_handling(self, mock_logger, app):
        """Test handling of PermanentAIError exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/permanent-ai-error")
        
        assert response.status_code == 502  # PermanentAIError -> 502
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "AI service error"
        assert data["error_code"] == "AI_SERVICE_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_generic_exception_handling(self, mock_logger, app):
        """Test handling of generic exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/generic-error")
        
        assert response.status_code == 500  # Generic Exception -> 500
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] == "Internal server error"
        assert data["error_code"] == "INTERNAL_ERROR"
        
        mock_logger.error.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_api_version_error_special_case(self, mock_logger, app):
        """Test special case handling for API version errors."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/api-version-error")
        
        assert response.status_code == 400
        data = response.json()
        
        # Should have special API version error format
        assert data["error"] == "Unsupported API version"
        assert data["error_code"] == "API_VERSION_NOT_SUPPORTED"
        assert data["requested_version"] == "3.0"
        assert data["supported_versions"] == ["1.0", "2.0"]
        assert data["current_version"] == "2.0"
        assert "detail" in data
        
        # Should have special headers
        assert response.headers["X-API-Supported-Versions"] == "1.0, 2.0"
        assert response.headers["X-API-Current-Version"] == "2.0"
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_request_validation_error_handling(self, mock_logger, app):
        """Test handling of FastAPI request validation errors."""
        client = TestClient(app, raise_server_exceptions=False)
        
        # Send invalid JSON that will trigger validation error
        response = client.post("/validation", json="invalid")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        
        assert data["success"] is False
        assert "Invalid request data" in data["error"]
        assert data["error_code"] == "VALIDATION_ERROR"
        
        # Should log the validation error
        mock_logger.warning.assert_called()
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_request_id_correlation_in_logs(self, mock_logger, app):
        """Test that request ID is included in exception logs."""
        # Add a middleware to set request_id in state
        @app.middleware("http")
        async def add_request_id(request, call_next):
            request.state.request_id = "test-123"
            response = await call_next(request)
            return response
        
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/generic-error")
        
        assert response.status_code == 500
        
        # Should log with request ID
        mock_logger.error.assert_called()
        log_call_args = mock_logger.error.call_args
        
        # Check that request_id is in the log message
        log_message = log_call_args[0][0]
        assert "test-123" in log_message
        
        # Check structured logging extra data
        extra_data = log_call_args[1].get('extra', {})
        assert extra_data.get('request_id') == 'test-123'
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_exception_logging_structure(self, mock_logger, app):
        """Test structured logging format for exceptions."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/validation-error")
        
        assert response.status_code == 400
        
        mock_logger.error.assert_called()
        log_call_args = mock_logger.error.call_args
        
        # Check structured logging extra data
        extra_data = log_call_args[1].get('extra', {})
        assert 'method' in extra_data
        assert 'url' in extra_data
        assert 'exception_type' in extra_data
        assert 'exception_module' in extra_data
        assert extra_data['method'] == 'GET'
        assert extra_data['exception_type'] == 'ValidationError'
        
        # Should include exc_info for stack trace
        assert log_call_args[1].get('exc_info') is True
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_application_error_with_context(self, mock_logger, app):
        """Test ApplicationError with context data."""
        @app.get("/context-error")
        async def context_error_endpoint():
            error = ApplicationError("Custom error with context")
            error.context = {
                'error_code': 'CUSTOM_ERROR',
                'field': 'username',
                'value': 'invalid'
            }
            raise error
        
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/context-error")
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["success"] is False
        assert "Custom error with context" in data["error"]  # Account for context in string representation
        assert data["error_code"] == "CUSTOM_ERROR"
        assert data["details"] == {
            'error_code': 'CUSTOM_ERROR',
            'field': 'username',
            'value': 'invalid'
        }
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_error_response_timestamp_format(self, mock_logger, app):
        """Test that error responses include properly formatted timestamps."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/validation-error")
        
        assert response.status_code == 400
        data = response.json()
        
        # Should have timestamp in ISO format
        assert "timestamp" in data
        timestamp = data["timestamp"]
        # Basic ISO format validation (YYYY-MM-DDTHH:MM:SS.ffffff)
        assert "T" in timestamp
        assert len(timestamp) >= 19  # Minimum length for ISO format
    
    def test_exception_handler_doesnt_affect_normal_http_exceptions(self, app):
        """Test that normal HTTP exceptions are handled by FastAPI."""
        @app.get("/http-exception")
        async def http_exception_endpoint():
            raise HTTPException(status_code=404, detail="Not found")
        
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/http-exception")
        
        assert response.status_code == 404
        data = response.json()
        
        # Should use FastAPI's default HTTP exception format
        assert data["detail"] == "Not found"
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_concurrent_exception_handling(self, mock_logger, app):
        """Test exception handling with concurrent requests."""
        import threading
        
        client = TestClient(app, raise_server_exceptions=False)
        responses = []
        
        def make_request():
            response = client.get("/validation-error")
            responses.append(response)
        
        # Make multiple concurrent requests that raise exceptions
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should have been handled properly
        assert len(responses) == 5
        for response in responses:
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_error_response_schema_compliance(self, app):
        """Test that error responses comply with ErrorResponse schema."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/validation-error")
        
        assert response.status_code == 400
        data = response.json()
        
        # Validate against ErrorResponse schema
        error_response = ErrorResponse(**data)
        assert error_response.success is False
        assert error_response.error is not None
        assert error_response.error_code is not None
        assert error_response.timestamp is not None
    
    @patch('app.core.middleware.global_exception_handler.logger')
    def test_context_variable_fallback(self, mock_logger, app):
        """Test fallback when request_id is not in state but in context."""
        with patch('app.core.middleware.global_exception_handler.request_id_context') as mock_context:
            mock_context.get.return_value = "context-456"
            
            client = TestClient(app, raise_server_exceptions=False)
            
            response = client.get("/generic-error")
            
            assert response.status_code == 500
            
            # Should use context variable as fallback
            mock_logger.error.assert_called()
            log_call_args = mock_logger.error.call_args
            
            # Check that fallback request_id is used
            extra_data = log_call_args[1].get('extra', {})
            assert extra_data.get('request_id') == 'context-456'
