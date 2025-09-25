"""
Comprehensive tests for Request Logging middleware.

Tests cover request/response logging, correlation IDs, timing information,
sensitive data filtering, and structured logging.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, call
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware.request_logging import (
    RequestLoggingMiddleware,
    request_id_context,
    request_start_time_context
)
from app.core.config import Settings


class TestRequestLoggingMiddleware:
    """Test Request Logging middleware functionality."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with request logging configuration."""
        settings = Mock(spec=Settings)
        settings.request_logging_enabled = True
        settings.log_level = "INFO"
        settings.slow_request_threshold = 100  # 100ms for testing
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI app with request logging middleware."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test response"}
        
        @app.post("/api/data")
        async def api_endpoint():
            return {"result": "success", "data": {"id": 123}}
        
        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.15)  # 150ms - should trigger slow request warning
            return {"message": "slow response"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        @app.get("/client-error")
        async def client_error_endpoint():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Bad request")
        
        app.add_middleware(RequestLoggingMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with settings."""
        app = FastAPI()
        middleware = RequestLoggingMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.slow_request_threshold == 100
        assert 'authorization' in middleware.sensitive_headers
        assert 'x-api-key' in middleware.sensitive_headers
        assert 'cookie' in middleware.sensitive_headers
    
    def test_middleware_initialization_defaults(self):
        """Test middleware initialization with default values."""
        settings = Mock(spec=Settings)
        # Remove attributes to test defaults
        if hasattr(settings, 'slow_request_threshold'):
            delattr(settings, 'slow_request_threshold')
        
        app = FastAPI()
        middleware = RequestLoggingMiddleware(app, settings)
        
        # Should use default value
        assert middleware.slow_request_threshold == 1000  # 1000ms default
    
    @patch('app.core.middleware.request_logging.logger')
    def test_request_start_logging(self, mock_logger, app):
        """Test request start logging with correlation ID."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Should log request start
        mock_logger.info.assert_called()
        info_call_args, info_call_kwargs = mock_logger.info.call_args
        log_message = info_call_args[0]
        
        assert "Request started: GET /test [req_id:" in log_message
        
        # Check extra data
        extra_data = info_call_kwargs.get('extra', {})
        assert extra_data['method'] == 'GET'
        assert extra_data['path'] == '/test'
        assert 'request_id' in extra_data
        assert len(extra_data['request_id']) == 8  # 8-char UUID prefix
    
    @patch('app.core.middleware.request_logging.logger')
    def test_request_completion_logging(self, mock_logger, app):
        """Test successful request completion logging."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Should log request completion
        completion_calls = [call for call in mock_logger.log.call_args_list 
                          if "Request completed" in str(call)]
        assert len(completion_calls) > 0
    
    @patch('app.core.middleware.request_logging.logger')
    def test_request_id_generation_and_context(self, mock_logger, app):
        """Test request ID generation and context variable setting."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Verify that request ID was generated and used in logs
        start_call = mock_logger.info.call_args_list[0] if mock_logger.info.call_args_list else None
        assert start_call is not None
        
        # Extract request_id from the log call
        start_message = start_call[0][0]
        assert "Request started: GET /test [req_id:" in start_message
        assert "req_id:" in start_message
    
    def test_request_state_integration(self, app):
        """Test that request ID is stored in request state."""
        request_ids = []
        
        @app.middleware("http")
        async def capture_request_id(request, call_next):
            response = await call_next(request)
            if hasattr(request.state, 'request_id'):
                request_ids.append(request.state.request_id)
            return response
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert len(request_ids) == 1
        assert len(request_ids[0]) == 8  # Request ID should be 8 characters (first 8 of UUID)
    
    @patch('app.core.middleware.request_logging.logger')
    def test_slow_request_warning(self, mock_logger, app):
        """Test slow request detection and warning logging."""
        client = TestClient(app)
        
        response = client.get("/slow")
        
        assert response.status_code == 200
        
        # Should log at WARNING level for slow requests
        warning_calls = [call for call in mock_logger.log.call_args_list
                        if call[0][0] == 30]  # WARNING level is 30
        assert len(warning_calls) > 0
    
    @patch('app.core.middleware.request_logging.logger')
    def test_client_error_logging_level(self, mock_logger, app):
        """Test logging level for client errors (4xx)."""
        client = TestClient(app)
        
        response = client.get("/client-error")
        
        assert response.status_code == 400
        
        # Should log at WARNING level for client errors
        warning_calls = [call for call in mock_logger.log.call_args_list
                        if call[0][0] == 30]  # WARNING level is 30
        assert len(warning_calls) > 0
    
    @patch('app.core.middleware.request_logging.logger')
    def test_server_error_logging_level(self, mock_logger, app):
        """Test logging level for server errors (5xx)."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/error")
        
        assert response.status_code == 500
        
        # Without global exception handler, exception is caught in middleware's except block
        # Should log using logger.error() method
        mock_logger.error.assert_called()
        
        # Verify the error log contains expected information
        error_call_args, error_call_kwargs = mock_logger.error.call_args
        error_message = error_call_args[0]
        assert "Request failed: GET /error" in error_message
        assert "ValueError" in error_message
    
    @patch('app.core.middleware.request_logging.logger')
    def test_exception_handling_logging(self, mock_logger, app):
        """Test logging when exceptions occur during request processing."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/error")
        
        # Without global exception handler, exception is caught in middleware's except block
        # Should log using logger.error() method
        assert response.status_code == 500
        
        # Should log exception using logger.error() method with exc_info
        mock_logger.error.assert_called()
        
        # Check structured logging data
        error_call_args, error_call_kwargs = mock_logger.error.call_args
        error_message = error_call_args[0]
        assert "Request failed: GET /error" in error_message
        assert "ValueError" in error_message
        
        extra_data = error_call_kwargs.get('extra', {})
        assert extra_data['method'] == 'GET'
        assert extra_data['path'] == '/error'
        assert extra_data['exception_type'] == 'ValueError'
        assert 'duration_ms' in extra_data
        
        # Should include exc_info for stack trace
        assert error_call_kwargs.get('exc_info') is True
    
    @patch('app.core.middleware.request_logging.logger')
    def test_post_request_with_body_logging(self, mock_logger, app):
        """Test logging POST requests with request body."""
        client = TestClient(app)
        
        response = client.post("/api/data", json={"test": "data"})
        
        assert response.status_code == 200
        
        # Should log request start with method and path
        start_calls = [call for call in mock_logger.info.call_args_list
                      if "Request started: POST /api/data" in str(call)]
        assert len(start_calls) > 0
    
    @patch('app.core.middleware.request_logging.logger')
    def test_query_parameters_logging(self, mock_logger, app):
        """Test logging of query parameters."""
        client = TestClient(app)
        
        response = client.get("/test?param1=value1&param2=value2")
        
        assert response.status_code == 200
        
        # Check that query parameters are included in log extra data
        info_calls = mock_logger.info.call_args_list
        start_call = next((call for call in info_calls if "Request started" in str(call)), None)
        assert start_call is not None
        
        extra_data = start_call[1].get('extra', {})
        assert 'query_params' in extra_data
        assert extra_data['query_params']['param1'] == 'value1'
        assert extra_data['query_params']['param2'] == 'value2'
    
    @patch('app.core.middleware.request_logging.logger')
    def test_user_agent_logging(self, mock_logger, app):
        """Test user agent header logging."""
        client = TestClient(app)
        
        response = client.get("/test", headers={"User-Agent": "CustomAgent/1.0"})
        
        assert response.status_code == 200
        
        # Check that user agent is included in log extra data
        info_calls = mock_logger.info.call_args_list
        start_call = next((call for call in info_calls if "Request started" in str(call)), None)
        assert start_call is not None
        
        extra_data = start_call[1].get('extra', {})
        assert 'user_agent' in extra_data
        assert extra_data['user_agent'] == 'CustomAgent/1.0'
    
    @patch('app.core.middleware.request_logging.logger')
    def test_response_size_logging(self, mock_logger, app):
        """Test response size calculation and logging."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that response size is included in completion log
        log_calls = mock_logger.log.call_args_list
        completion_call = next((call for call in log_calls 
                               if "Request completed" in str(call)), None)
        assert completion_call is not None
        
        extra_data = completion_call[1].get('extra', {})
        assert 'response_size' in extra_data
    
    @patch('app.core.middleware.request_logging.logger')
    def test_timing_accuracy(self, mock_logger, app):
        """Test request timing accuracy in logs."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check timing information in logs
        log_calls = mock_logger.log.call_args_list
        completion_call = next((call for call in log_calls 
                               if "Request completed" in str(call)), None)
        assert completion_call is not None
        
        extra_data = completion_call[1].get('extra', {})
        assert 'duration_ms' in extra_data
        assert isinstance(extra_data['duration_ms'], (int, float))
        assert extra_data['duration_ms'] >= 0
    
    @patch('app.core.middleware.request_logging.logger')
    def test_different_http_methods_logging(self, mock_logger, app):
        """Test logging across different HTTP methods."""
        client = TestClient(app)
        
        # Test different methods
        methods_and_paths = [
            ('GET', '/test'),
            ('POST', '/api/data'),
        ]
        
        for method, path in methods_and_paths:
            if method == 'GET':
                response = client.get(path)
            elif method == 'POST':
                response = client.post(path, json={"test": "data"})
            
            assert response.status_code == 200
            
            # Verify method is logged correctly
            start_calls = [call for call in mock_logger.info.call_args_list
                          if f"Request started: {method} {path}" in str(call)]
            assert len(start_calls) > 0
    
    def test_context_variables_isolation(self, settings):
        """Test that context variables are properly isolated between requests."""
        from concurrent.futures import ThreadPoolExecutor
        import time
        
        # Create fresh app with context capture middleware
        app = FastAPI()
        
        captured_request_ids = []
        
        @app.middleware("http")
        async def capture_context_middleware(request, call_next):
            # Capture context value before calling next
            context_id = request_id_context.get('unknown')
            response = await call_next(request)
            # Capture final context ID after processing
            final_id = getattr(request.state, 'request_id', 'none')
            captured_request_ids.append(final_id)
            return response
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test response"}
        
        app.add_middleware(RequestLoggingMiddleware, settings=settings)
        
        def make_request(delay=0):
            if delay:
                time.sleep(delay)
            client = TestClient(app)
            response = client.get("/test")
            return response.status_code
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i * 0.01) for i in range(3)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        
        # Each request should have captured a unique request ID
        assert len(captured_request_ids) == 3
        assert len(set(captured_request_ids)) == 3  # All should be unique
    
    @patch('app.core.middleware.request_logging.logger')
    def test_sensitive_headers_filtering(self, mock_logger, app):
        """Test that sensitive headers are not logged."""
        client = TestClient(app)
        
        response = client.get("/test", headers={
            "Authorization": "Bearer secret-token",
            "X-API-Key": "secret-api-key",
            "Cookie": "session=secret-session",
            "User-Agent": "TestClient/1.0"
        })
        
        assert response.status_code == 200
        
        # Check that sensitive headers are not present in logs
        all_log_calls = []
        all_log_calls.extend(mock_logger.info.call_args_list)
        all_log_calls.extend(mock_logger.log.call_args_list)
        
        log_content = str(all_log_calls)
        
        # Sensitive values should not appear in logs
        assert "secret-token" not in log_content
        assert "secret-api-key" not in log_content
        assert "secret-session" not in log_content
        
        # Non-sensitive header should be logged
        assert "TestClient/1.0" in log_content
    
    @patch('app.core.middleware.request_logging.logger')
    def test_client_ip_logging(self, mock_logger, app):
        """Test client IP address logging."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that client IP is included in log extra data
        info_calls = mock_logger.info.call_args_list
        start_call = next((call for call in info_calls if "Request started" in str(call)), None)
        assert start_call is not None
        
        extra_data = start_call[1].get('extra', {})
        assert 'client_ip' in extra_data
        # TestClient typically uses 'testclient' as client IP
        assert extra_data['client_ip'] in ['testclient', 'unknown']
    
    @patch('app.core.middleware.request_logging.logger')
    def test_request_id_correlation(self, mock_logger, app):
        """Test request ID correlation between start and completion logs."""
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Extract request IDs from start and completion logs
        info_calls = mock_logger.info.call_args_list
        log_calls = mock_logger.log.call_args_list
        
        start_call = next((call for call in info_calls if "Request started" in str(call)), None)
        completion_call = next((call for call in log_calls if "Request completed" in str(call)), None)
        
        assert start_call is not None
        assert completion_call is not None
        
        # Both should have the same request_id in extra data
        start_extra = start_call[1].get('extra', {})
        completion_extra = completion_call[1].get('extra', {})
        
        assert 'request_id' in start_extra
        assert 'request_id' in completion_extra
        assert start_extra['request_id'] == completion_extra['request_id']
