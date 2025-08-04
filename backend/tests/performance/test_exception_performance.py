"""
Performance tests for exception handling system.

This module tests the performance characteristics of the custom exception
system to ensure no significant regression was introduced during refactoring.
"""
import pytest
import time
import statistics
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from typing import List, Dict, Any
import asyncio
import psutil
import os

from app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    InfrastructureError,
    TransientAIError,
    classify_ai_exception,
    get_http_status_for_exception,
)


class TestExceptionCreationPerformance:
    """Test performance of exception creation and basic operations."""
    
    def test_exception_creation_performance(self):
        """Test that exception creation is fast."""
        iterations = 1000
        
        # Test simple exception creation
        start_time = time.perf_counter()
        for i in range(iterations):
            exc = ValidationError(f"Test error {i}")
        simple_duration = time.perf_counter() - start_time
        
        # Test exception creation with context
        start_time = time.perf_counter()
        for i in range(iterations):
            exc = ValidationError(
                f"Test error {i}",
                {
                    "request_id": f"req-{i}",
                    "endpoint": "/test/endpoint",
                    "operation": "validation",
                    "error_code": f"E{i:04d}"
                }
            )
        context_duration = time.perf_counter() - start_time
        
        # Assertions - exception creation should be very fast
        avg_simple = simple_duration / iterations
        avg_context = context_duration / iterations
        
        assert avg_simple < 0.001, f"Simple exception creation too slow: {avg_simple:.6f}s per exception"
        assert avg_context < 0.002, f"Context exception creation too slow: {avg_context:.6f}s per exception"
        
        # Context creation should not be more than 3x slower than simple
        assert avg_context < avg_simple * 3, f"Context exceptions disproportionately slow: {avg_context:.6f}s vs {avg_simple:.6f}s"
        
    def test_exception_string_representation_performance(self):
        """Test performance of exception string conversion."""
        iterations = 1000
        
        # Create exceptions with varying context sizes
        exceptions = []
        for i in range(iterations):
            context = {
                "request_id": f"req-{i}",
                "endpoint": f"/test/endpoint/{i}",
                "operation": "validation",
                "timestamp": time.time(),
                "additional_data": {"key": f"value-{i}", "nested": {"data": i}}
            }
            exceptions.append(ValidationError(f"Test error {i}", context))
            
        # Test string conversion performance
        start_time = time.perf_counter()
        for exc in exceptions:
            str_repr = str(exc)
        duration = time.perf_counter() - start_time
        
        avg_duration = duration / iterations
        assert avg_duration < 0.001, f"Exception string conversion too slow: {avg_duration:.6f}s per exception"


class TestExceptionClassificationPerformance:
    """Test performance of exception classification utilities."""
    
    def test_classify_ai_exception_performance(self):
        """Test performance of exception classification."""
        iterations = 1000
        
        # Create mix of different exception types
        exceptions = [
            ValidationError("Validation error"),
            TransientAIError("Transient error"),
            InfrastructureError("Infrastructure error"),
            RuntimeError("Runtime error"),
            ConnectionError("Connection error"),
        ] * (iterations // 5)
        
        # Test classification performance
        start_time = time.perf_counter()
        for exc in exceptions:
            result = classify_ai_exception(exc)
        duration = time.perf_counter() - start_time
        
        avg_duration = duration / len(exceptions)
        assert avg_duration < 0.0001, f"Exception classification too slow: {avg_duration:.6f}s per classification"
        
    def test_http_status_mapping_performance(self):
        """Test performance of HTTP status code mapping."""
        iterations = 1000
        
        # Create mix of different exception types
        exceptions = [
            ValidationError("Validation error"),
            AuthenticationError("Auth error"),
            InfrastructureError("Infrastructure error"),
            TransientAIError("Transient error"),
            Exception("Generic error"),
        ] * (iterations // 5)
        
        # Test HTTP status mapping performance
        start_time = time.perf_counter()
        for exc in exceptions:
            status_code = get_http_status_for_exception(exc)
        duration = time.perf_counter() - start_time
        
        avg_duration = duration / len(exceptions)
        assert avg_duration < 0.0001, f"HTTP status mapping too slow: {avg_duration:.6f}s per mapping"


class TestGlobalExceptionHandlerPerformance:
    """Test performance of the global exception handler."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.__str__ = lambda: "http://test.com/api/test"
        mock_request.state = Mock()
        mock_request.state.request_id = "test-req-123"
        return mock_request
        
    def test_exception_handler_response_time(self, mock_request):
        """Test response time of global exception handler."""
        from app.core.middleware import setup_global_exception_handler
        from fastapi import FastAPI
        from app.core.config import Settings
        
        # Create test app and setup exception handler
        test_app = FastAPI()
        test_settings = Settings()
        setup_global_exception_handler(test_app, test_settings)
        
        # Get the exception handler
        exception_handlers = test_app.exception_handlers
        global_handler = exception_handlers.get(Exception)
        
        if global_handler is None:
            pytest.skip("Global exception handler not found")
            
        # Test different exception types
        test_exceptions = [
            ValidationError("Test validation error", {"request_id": "test-123"}),
            InfrastructureError("Test infrastructure error", {"service": "test"}),
            TransientAIError("Test AI error", {"operation": "test"}),
            Exception("Generic exception"),
        ]
        
        response_times = []
        
        async def run_handler_test(handler, request, exc):
            """Helper to run handler and return result."""
            return await handler(request, exc)
        
        for exc in test_exceptions:
            start_time = time.perf_counter()
            
            # Run the exception handler
            try:
                asyncio.run(run_handler_test(global_handler, mock_request, exc))
            except Exception:
                # Handler may raise exceptions during testing - that's ok
                pass
            
            duration = time.perf_counter() - start_time
            response_times.append(duration)
            
        # Analyze performance
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 0.01, f"Average exception handler response time too slow: {avg_response_time:.6f}s"
        assert max_response_time < 0.05, f"Maximum exception handler response time too slow: {max_response_time:.6f}s"


class TestAPIEndpointExceptionPerformance:
    """Test performance of exception handling in actual API endpoints."""
    
    def test_text_processing_exception_performance(self, authenticated_client: TestClient):
        """Test exception handling performance in text processing endpoints."""
        iterations = 50  # Fewer iterations for actual API calls
        
        # Test validation error performance (Q&A without question)
        validation_times = []
        for i in range(iterations):
            payload = {
                "text": f"Sample text {i}",
                "operation": "qa"
                # Missing required "question" field
            }
            
            start_time = time.perf_counter()
            try:
                response = authenticated_client.post("/v1/text_processing/process", json=payload)
            except Exception:
                pass
            duration = time.perf_counter() - start_time
            validation_times.append(duration)
            
        avg_validation_time = statistics.mean(validation_times)
        assert avg_validation_time < 0.1, f"Validation exception handling too slow: {avg_validation_time:.4f}s"
        
    def test_auth_exception_performance(self, client: TestClient):
        """Test authentication exception handling performance."""
        iterations = 50
        
        auth_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                response = client.get("/v1/auth/status")
            except Exception:
                pass
            duration = time.perf_counter() - start_time
            auth_times.append(duration)
            
        avg_auth_time = statistics.mean(auth_times)
        assert avg_auth_time < 0.1, f"Authentication exception handling too slow: {avg_auth_time:.4f}s"
        
    def test_resilience_api_exception_performance(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test exception handling performance in resilience APIs."""
        iterations = 20  # Fewer iterations for complex endpoints
        
        endpoint_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                response = client.get("/internal/resilience/metrics", headers=auth_headers)
            except Exception:
                pass
            duration = time.perf_counter() - start_time
            endpoint_times.append(duration)
            
        avg_endpoint_time = statistics.mean(endpoint_times)
        assert avg_endpoint_time < 0.2, f"Resilience API exception handling too slow: {avg_endpoint_time:.4f}s"


class TestMemoryUsageRegression:
    """Test that exception handling doesn't cause memory leaks or excessive usage."""
    
    def test_exception_memory_usage(self):
        """Test memory usage of exception creation and handling."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many exceptions with context
        exceptions = []
        for i in range(1000):
            exc = ValidationError(
                f"Test error {i}",
                {
                    "request_id": f"req-{i}",
                    "endpoint": f"/test/endpoint/{i}",
                    "operation": "validation",
                    "timestamp": time.time(),
                    "large_context": {
                        "data": [j for j in range(100)],  # Some bulk data
                        "metadata": {f"key_{k}": f"value_{k}" for k in range(50)}
                    }
                }
            )
            exceptions.append(exc)
            
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        
        # Clean up exceptions
        exceptions.clear()
        
        # Memory increase should be reasonable (less than 50MB for 1000 exceptions)
        max_allowed_increase = 50 * 1024 * 1024  # 50MB
        assert memory_increase < max_allowed_increase, f"Exception memory usage too high: {memory_increase / 1024 / 1024:.2f}MB"
        
    def test_exception_cleanup(self):
        """Test that exceptions are properly garbage collected."""
        import gc
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and process many exceptions
        for batch in range(10):
            exceptions = []
            for i in range(100):
                exc = InfrastructureError(
                    f"Batch {batch} error {i}",
                    {
                        "batch": batch,
                        "index": i,
                        "large_data": ["x" * 1000]  # 1KB of data per exception
                    }
                )
                exceptions.append(exc)
                
            # Process exceptions (simulate exception handling)
            for exc in exceptions:
                str(exc)  # Force string conversion
                get_http_status_for_exception(exc)
                classify_ai_exception(exc)
                
            # Clear batch and force garbage collection
            exceptions.clear()
            gc.collect()
            
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly after cleanup
        max_allowed_increase = 10 * 1024 * 1024  # 10MB
        assert memory_increase < max_allowed_increase, f"Memory leak detected: {memory_increase / 1024 / 1024:.2f}MB increase"


class TestConcurrentExceptionHandling:
    """Test exception handling under concurrent load."""
    
    def test_concurrent_exception_handling(self):
        """Test concurrent exception handling performance."""
        # This is an alias for the main concurrent test
        return self.test_concurrent_exception_creation()
    
    def test_concurrent_exception_creation(self):
        """Test concurrent exception creation performance."""
        import threading
        import concurrent.futures
        
        def create_exceptions(thread_id: int, count: int) -> List[float]:
            times = []
            for i in range(count):
                start_time = time.perf_counter()
                exc = ValidationError(
                    f"Thread {thread_id} error {i}",
                    {
                        "thread_id": thread_id,
                        "index": i,
                        "timestamp": time.time()
                    }
                )
                duration = time.perf_counter() - start_time
                times.append(duration)
            return times
            
        # Test with multiple threads
        num_threads = 4
        exceptions_per_thread = 250
        
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(create_exceptions, thread_id, exceptions_per_thread)
                for thread_id in range(num_threads)
            ]
            
            all_times = []
            for future in concurrent.futures.as_completed(futures):
                thread_times = future.result()
                all_times.extend(thread_times)
                
        total_duration = time.perf_counter() - start_time
        
        # Analyze results
        avg_exception_time = statistics.mean(all_times)
        total_exceptions = num_threads * exceptions_per_thread
        
        assert avg_exception_time < 0.001, f"Concurrent exception creation too slow: {avg_exception_time:.6f}s"
        assert total_duration < 2.0, f"Total concurrent test took too long: {total_duration:.2f}s for {total_exceptions} exceptions"
        
    def test_concurrent_api_exception_handling(self, authenticated_client: TestClient):
        """Test concurrent API exception handling."""
        import concurrent.futures
        
        def make_failing_request(client: TestClient, request_id: int) -> float:
            start_time = time.perf_counter()
            try:
                # Make request that will cause validation error
                response = client.post("/v1/text_processing/process", json={
                    "text": f"Request {request_id} text",
                    "operation": "qa"  # Missing question
                })
            except Exception:
                pass
            return time.perf_counter() - start_time
            
        # Test with concurrent requests
        num_requests = 20
        
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_failing_request, authenticated_client, i)
                for i in range(num_requests)
            ]
            
            request_times = []
            for future in concurrent.futures.as_completed(futures):
                request_time = future.result()
                request_times.append(request_time)
                
        total_duration = time.perf_counter() - start_time
        
        # Analyze results
        avg_request_time = statistics.mean(request_times)
        max_request_time = max(request_times)
        
        assert avg_request_time < 0.2, f"Concurrent exception handling too slow: {avg_request_time:.4f}s"
        assert max_request_time < 1.0, f"Some requests took too long: {max_request_time:.4f}s"
        assert total_duration < 10.0, f"Total concurrent test took too long: {total_duration:.2f}s"