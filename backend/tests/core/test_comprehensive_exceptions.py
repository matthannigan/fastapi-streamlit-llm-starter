"""
Comprehensive tests for custom exception handling system.

This module tests the complete exception hierarchy, classification utilities,
HTTP status mapping, and integration with the global exception handler.
"""
import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from unittest.mock import Mock, patch
import httpx
import time
from typing import Dict, Any

from app.core.exceptions import (
    # Base exceptions
    ApplicationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    BusinessLogicError,
    InfrastructureError,
    
    # AI service exceptions
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    
    # Utility functions
    classify_ai_exception,
    get_http_status_for_exception,
)


class TestExceptionHierarchy:
    """Test the custom exception hierarchy and basic functionality."""
    
    def test_application_error_base_class(self):
        """Test ApplicationError base class functionality."""
        exc = ApplicationError("Test message", {"key": "value"})
        assert exc.message == "Test message"
        assert exc.context == {"key": "value"}
        assert str(exc) == "Test message (Context: {'key': 'value'})"
        
        # Test without context
        exc_no_context = ApplicationError("Test message")
        assert exc_no_context.context == {}
        assert str(exc_no_context) == "Test message"
        
    def test_infrastructure_error_base_class(self):
        """Test InfrastructureError base class functionality."""
        exc = InfrastructureError("Infrastructure issue", {"service": "redis"})
        assert exc.message == "Infrastructure issue"
        assert exc.context == {"service": "redis"}
        assert str(exc) == "Infrastructure issue (Context: {'service': 'redis'})"
        
    def test_validation_error(self):
        """Test ValidationError specific functionality."""
        exc = ValidationError("Invalid input", {"field": "email"})
        assert isinstance(exc, ApplicationError)
        assert exc.message == "Invalid input"
        assert exc.context["field"] == "email"
        
    def test_authentication_error(self):
        """Test AuthenticationError specific functionality."""
        exc = AuthenticationError("Missing API key", {"auth_method": "bearer"})
        assert isinstance(exc, ApplicationError)
        assert exc.message == "Missing API key"
        assert exc.context["auth_method"] == "bearer"
        
    def test_authorization_error(self):
        """Test AuthorizationError specific functionality."""
        exc = AuthorizationError("Insufficient permissions", {"required_role": "admin"})
        assert isinstance(exc, ApplicationError)
        assert exc.message == "Insufficient permissions"
        assert exc.context["required_role"] == "admin"
        
    def test_business_logic_error(self):
        """Test BusinessLogicError specific functionality."""
        exc = BusinessLogicError("Business rule violation", {"rule": "max_attempts"})
        assert isinstance(exc, ApplicationError)
        assert exc.message == "Business rule violation"
        assert exc.context["rule"] == "max_attempts"
        
    def test_configuration_error(self):
        """Test ConfigurationError specific functionality."""
        exc = ConfigurationError("Missing config", {"key": "API_URL"})
        assert isinstance(exc, ApplicationError)
        assert exc.message == "Missing config"
        assert exc.context["key"] == "API_URL"
        
    def test_transient_ai_error(self):
        """Test TransientAIError hierarchy."""
        exc = TransientAIError("Temporary AI failure", {"service": "openai"})
        assert isinstance(exc, AIServiceException)
        assert isinstance(exc, InfrastructureError)
        assert exc.message == "Temporary AI failure"
        
    def test_permanent_ai_error(self):
        """Test PermanentAIError hierarchy."""
        exc = PermanentAIError("Permanent AI failure", {"reason": "invalid_key"})
        assert isinstance(exc, AIServiceException)
        assert isinstance(exc, InfrastructureError)
        assert exc.message == "Permanent AI failure"
        
    def test_rate_limit_error(self):
        """Test RateLimitError hierarchy."""
        exc = RateLimitError("Rate limit exceeded", {"retry_after": 60})
        assert isinstance(exc, TransientAIError)
        assert isinstance(exc, AIServiceException)
        assert isinstance(exc, InfrastructureError)
        assert exc.context["retry_after"] == 60
        
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError hierarchy."""
        exc = ServiceUnavailableError("Service down", {"estimated_recovery": "5min"})
        assert isinstance(exc, TransientAIError)
        assert isinstance(exc, AIServiceException)
        assert isinstance(exc, InfrastructureError)
        assert exc.context["estimated_recovery"] == "5min"


class TestExceptionClassification:
    """Test exception classification for retry logic."""
    
    def test_transient_exceptions_should_retry(self):
        """Test that transient exceptions are classified for retry."""
        transient_exceptions = [
            TransientAIError("Temporary failure"),
            RateLimitError("Rate limited"),
            ServiceUnavailableError("Service down"),
            httpx.ConnectError("Connection failed"),
            httpx.TimeoutException("Request timeout"),
            httpx.NetworkError("Network issue"),
            ConnectionError("Connection lost"),
            TimeoutError("Operation timeout"),
        ]
        
        for exc in transient_exceptions:
            assert classify_ai_exception(exc) is True, f"Expected {type(exc).__name__} to be retryable"
            
    def test_permanent_exceptions_should_not_retry(self):
        """Test that permanent exceptions are not classified for retry."""
        permanent_exceptions = [
            PermanentAIError("Permanent failure"),
            ValidationError("Invalid input"),
            ConfigurationError("Bad config"),
            ValueError("Invalid value"),
            TypeError("Type error"),
            AttributeError("Missing attribute"),
        ]
        
        for exc in permanent_exceptions:
            assert classify_ai_exception(exc) is False, f"Expected {type(exc).__name__} to not be retryable"
            
    def test_http_status_error_classification(self):
        """Test HTTP status error classification."""
        # Mock response for testing
        mock_response = Mock()
        
        # Retryable HTTP errors (server errors and rate limits)
        retryable_codes = [429, 500, 502, 503, 504]
        for code in retryable_codes:
            mock_response.status_code = code
            exc = httpx.HTTPStatusError("HTTP error", request=Mock(), response=mock_response)
            assert classify_ai_exception(exc) is True, f"Expected HTTP {code} to be retryable"
            
        # Non-retryable HTTP errors (client errors)
        non_retryable_codes = [400, 401, 403, 404, 422]
        for code in non_retryable_codes:
            mock_response.status_code = code
            exc = httpx.HTTPStatusError("HTTP error", request=Mock(), response=mock_response)
            assert classify_ai_exception(exc) is False, f"Expected HTTP {code} to not be retryable"
            
    def test_unknown_exceptions_default_to_retry(self):
        """Test that unknown exceptions default to retry (conservative approach)."""
        unknown_exceptions = [
            RuntimeError("Runtime error"),
            OSError("OS error"),
            Exception("Generic exception"),
        ]
        
        for exc in unknown_exceptions:
            assert classify_ai_exception(exc) is True, f"Expected {type(exc).__name__} to default to retryable"


class TestHTTPStatusMapping:
    """Test HTTP status code mapping for exceptions."""
    
    def test_application_error_status_codes(self):
        """Test status code mapping for ApplicationError types."""
        test_cases = [
            (ValidationError("Invalid"), 400),
            (AuthenticationError("No auth"), 401),
            (AuthorizationError("No access"), 403),
            (BusinessLogicError("Rule violation"), 422),
            (ConfigurationError("Bad config"), 500),
            (ApplicationError("Generic app error"), 400),
        ]
        
        for exc, expected_status in test_cases:
            actual_status = get_http_status_for_exception(exc)
            assert actual_status == expected_status, f"Expected {type(exc).__name__} to map to {expected_status}, got {actual_status}"
            
    def test_infrastructure_error_status_codes(self):
        """Test status code mapping for InfrastructureError types."""
        test_cases = [
            (InfrastructureError("Generic infra error"), 500),
            (AIServiceException("AI service error"), 502),
            (TransientAIError("Temporary AI error"), 503),
            (PermanentAIError("Permanent AI error"), 502),
            (RateLimitError("Rate limited"), 429),
            (ServiceUnavailableError("Service down"), 503),
        ]
        
        for exc, expected_status in test_cases:
            actual_status = get_http_status_for_exception(exc)
            assert actual_status == expected_status, f"Expected {type(exc).__name__} to map to {expected_status}, got {actual_status}"
            
    def test_unknown_exception_status_code(self):
        """Test that unknown exceptions map to 500."""
        unknown_exceptions = [
            Exception("Generic exception"),
            RuntimeError("Runtime error"),
        ]
        
        for exc in unknown_exceptions:
            actual_status = get_http_status_for_exception(exc)
            assert actual_status == 500, f"Expected {type(exc).__name__} to map to 500, got {actual_status}"


class TestExceptionContext:
    """Test exception context data handling."""
    
    def test_context_data_preservation(self):
        """Test that context data is properly preserved."""
        context = {
            "request_id": "test-123",
            "operation": "validate_config",
            "resource_id": "config-456",
            "timestamp": time.time(),
            "additional_data": {"key": "value"}
        }
        
        exc = ValidationError("Validation failed", context)
        
        assert exc.context == context
        assert exc.context["request_id"] == "test-123"
        assert exc.context["operation"] == "validate_config"
        assert exc.context["additional_data"]["key"] == "value"
        
    def test_empty_context_handling(self):
        """Test handling of exceptions without context."""
        exc = InfrastructureError("No context provided")
        assert exc.context == {}
        
    def test_context_in_string_representation(self):
        """Test that context appears in string representation."""
        context = {"error_code": "E001", "field": "email"}
        exc = ValidationError("Invalid email format", context)
        
        str_repr = str(exc)
        assert "Invalid email format" in str_repr
        assert "error_code" in str_repr
        assert "E001" in str_repr
        assert "field" in str_repr
        assert "email" in str_repr