"""
Comprehensive tests for Rate Limiting Middleware

Tests cover Redis-backed distributed rate limiting, local cache fallback,
endpoint classification, and DoS protection features.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from app.core.middleware.rate_limiting import (
    RateLimitMiddleware,
    RedisRateLimiter,
    LocalRateLimiter,
    RateLimitExceeded,
    get_client_identifier,
    get_endpoint_classification
)
from app.core.config import Settings


class TestRateLimitMiddleware:
    """Test the main rate limiting middleware."""
    
    @pytest.fixture(autouse=True)
    async def cleanup_async_resources(self):
        """Ensure proper cleanup of async resources to prevent event loop conflicts."""
        yield
        # Allow any pending async operations to complete
        await asyncio.sleep(0.1)
        # Force garbage collection of any remaining async objects
        import gc
        gc.collect()
    
    @pytest.fixture
    def settings(self):
        """Test settings with rate limiting enabled."""
        settings = Mock(spec=Settings)
        settings.rate_limiting_enabled = True
        settings.redis_url = "redis://localhost:6379"
        settings.rate_limit_requests_per_minute = 60
        settings.rate_limit_burst_size = 10
        settings.rate_limit_window_seconds = 60
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI test app with rate limiting middleware."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.post("/v1/text_processing/process")
        async def text_processing():
            return {"result": "processed"}
        
        @app.get("/health")
        async def health_check():
            return {"status": "ok"}
        
        app.add_middleware(RateLimitMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with different configurations."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.enabled == True
        assert middleware.requests_per_minute == 60
        assert middleware.burst_size == 10
        assert middleware.window_seconds == 60
    
    def test_disabled_middleware(self):
        """Test middleware when rate limiting is disabled."""
        settings = Mock(spec=Settings)
        settings.rate_limiting_enabled = False
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app, settings)
        
        assert middleware.enabled == False
    
    @pytest.mark.asyncio
    async def test_rate_limit_bypass_for_health_checks(self, app):
        """Test that health check endpoints bypass rate limiting."""
        client = TestClient(app)
        
        # Make many requests to health endpoint
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, app, settings):
        """Test rate limit enforcement for regular endpoints."""
        client = TestClient(app)
        
        # Mock the rate limiter to trigger rate limit exceeded
        with patch.object(RateLimitMiddleware, '_check_rate_limit') as mock_check:
            mock_check.return_value = (False, 0)  # Return tuple: not allowed, 0 remaining
            
            response = client.get("/test")
            assert response.status_code == 429
            assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    
    @pytest.mark.asyncio
    async def test_redis_connection_fallback(self, app):
        """Test fallback to local rate limiter when Redis fails."""
        client = TestClient(app)
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = RedisConnectionError("Connection failed")
            
            # Should still work with local fallback
            response = client.get("/test")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_client_identification(self, app):
        """Test client identification from request headers and IP."""
        with TestClient(app) as client:
            # Test with API key
            response = client.get("/test", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            
            # Test with custom IP headers
            response = client.get("/test", headers={"X-Forwarded-For": "192.168.1.1"})
            assert response.status_code == 200
            
            response = client.get("/test", headers={"X-Real-IP": "10.0.0.1"})
            assert response.status_code == 200
            
        # Explicit cleanup after TestClient usage
        await asyncio.sleep(0.05)


class TestRedisRateLimiter:
    """Test Redis-backed distributed rate limiter."""
    
    @pytest.fixture(autouse=True)
    async def cleanup_redis_resources(self):
        """Ensure proper cleanup of Redis-related async resources."""
        yield
        # Allow Redis connections and pipelines to cleanup
        await asyncio.sleep(0.1)
        import gc
        gc.collect()
    
    @pytest.fixture
    async def redis_client(self):
        """Mock Redis client."""
        client = AsyncMock(spec=redis.Redis)
        return client
    
    @pytest.fixture
    def rate_limiter(self, redis_client):
        """Redis rate limiter instance."""
        return RedisRateLimiter(
            redis_client=redis_client,
            requests_per_minute=60,
            window_seconds=60
        )
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_allow(self, rate_limiter, redis_client):
        """Test allowing requests within rate limit."""
        # Mock Redis pipeline
        pipeline_mock = AsyncMock()
        pipeline_mock.execute.return_value = [1, 3600]  # count=1, ttl=3600
        
        # Pipeline methods should be regular mocks, not async mocks
        # since they just queue commands and don't return coroutines
        pipeline_mock.incr = Mock(return_value=None)
        pipeline_mock.ttl = Mock(return_value=None)
        
        redis_client.pipeline.return_value = pipeline_mock
        
        # Should allow the request
        result = await rate_limiter.is_allowed("test-key", 1)
        assert result == True
        
        # Verify Redis operations
        pipeline_mock.incr.assert_called_once_with("rate_limit: test-key")
        pipeline_mock.ttl.assert_called_once_with("rate_limit: test-key")
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_deny(self, rate_limiter, redis_client):
        """Test denying requests that exceed rate limit."""
        # Mock Redis pipeline to return count > limit
        pipeline_mock = AsyncMock()
        pipeline_mock.execute.return_value = [61, 3600]  # count=61 > 60 limit
        
        # Pipeline methods should be regular mocks, not async mocks
        pipeline_mock.incr = Mock(return_value=None)
        pipeline_mock.ttl = Mock(return_value=None)
        
        redis_client.pipeline.return_value = pipeline_mock
        
        # Should deny the request
        result = await rate_limiter.is_allowed("test-key", 1)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self, rate_limiter, redis_client):
        """Test handling Redis connection errors."""
        redis_client.pipeline.side_effect = RedisConnectionError("Connection lost")
        
        # Should raise exception to trigger fallback
        with pytest.raises(RedisError):
            await rate_limiter.is_allowed("test-key", 1)
    
    @pytest.mark.asyncio
    async def test_redis_sliding_window(self, rate_limiter, redis_client):
        """Test sliding window rate limiting logic."""
        pipeline_mock = AsyncMock()
        
        # First request - fresh window
        pipeline_mock.execute.return_value = [1, -1]  # New key, no TTL
        
        # Pipeline methods should be regular mocks, not async mocks
        pipeline_mock.incr = Mock(return_value=None)
        pipeline_mock.ttl = Mock(return_value=None)
        
        redis_client.pipeline.return_value = pipeline_mock
        redis_client.expire = AsyncMock()  # Mock the expire method
        
        result = await rate_limiter.is_allowed("test-key", 1)
        assert result == True
        
        # Verify TTL was set for new key
        redis_client.expire.assert_called_with("rate_limit: test-key", 60)


class TestLocalRateLimiter:
    """Test local in-memory rate limiter fallback."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Local rate limiter instance."""
        return LocalRateLimiter(
            requests_per_minute=60,
            window_seconds=60
        )
    
    def test_local_rate_limit_allow(self, rate_limiter):
        """Test allowing requests within rate limit."""
        # First request should be allowed
        result = rate_limiter.is_allowed("test-key", 1)
        assert result == True
    
    @pytest.mark.slow
    def test_local_rate_limit_deny(self, rate_limiter):
        """Test denying requests that exceed rate limit."""
        # Fill up the bucket
        for i in range(60):
            result = rate_limiter.is_allowed("test-key", 1)
            assert result == True
        
        # 61st request should be denied
        result = rate_limiter.is_allowed("test-key", 1)
        assert result == False
    
    def test_local_rate_limit_window_reset(self, rate_limiter):
        """Test rate limit window reset over time."""
        with patch('app.core.middleware.rate_limiting.time.time') as mock_time:
            current_time = 1000.0
            mock_time.return_value = current_time
            
            # Fill up the bucket
            for i in range(60):
                result = rate_limiter.is_allowed("test-key", 1)
                assert result == True
            
            # Should be denied
            assert rate_limiter.is_allowed("test-key", 1) == False
            
            # Advance time by window duration to reset window
            mock_time.return_value = current_time + 61
            
            # Should be allowed again
            result = rate_limiter.is_allowed("test-key", 1)
            assert result == True
    
    def test_local_rate_limit_cleanup(self, rate_limiter):
        """Test cleanup of expired entries."""
        with patch('app.core.middleware.rate_limiting.time.time') as mock_time:
            current_time = 1000.0
            mock_time.return_value = current_time
            
            # Set the rate limiter's initial cleanup time
            rate_limiter.last_cleanup = current_time
            
            # Create entries for multiple keys
            rate_limiter.is_allowed("key1", 1)
            rate_limiter.is_allowed("key2", 1) 
            rate_limiter.is_allowed("key3", 1)
            
            assert len(rate_limiter.clients) == 3
            
            # Advance time by enough to trigger cleanup (cleanup_interval + window)
            mock_time.return_value = current_time + 400  # 300 (cleanup_interval) + 100
            
            # Trigger cleanup by making new request
            rate_limiter.is_allowed("new-key", 1)
            
            # Old entries should be cleaned up since they're outside the window
            assert len(rate_limiter.clients) == 1
            assert "new-key" in rate_limiter.clients


class TestRateLimitUtilities:
    """Test utility functions for rate limiting."""
    
    def test_get_client_identifier_api_key(self):
        """Test client identification using API key."""
        request = Mock(spec=Request)
        request.headers = {"x-api-key": "test-api-key-123"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        client_id = get_client_identifier(request)
        assert client_id == "api_key: test-api-key-123"
    
    def test_get_client_identifier_forwarded_ip(self):
        """Test client identification using forwarded IP headers."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        client_id = get_client_identifier(request)
        assert client_id == "ip: 192.168.1.100"
    
    def test_get_client_identifier_real_ip(self):
        """Test client identification using real IP header."""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "203.0.113.42"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        client_id = get_client_identifier(request)
        assert client_id == "ip: 203.0.113.42"
    
    def test_get_client_identifier_fallback(self):
        """Test client identification fallback to direct IP."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.50"
        
        client_id = get_client_identifier(request)
        assert client_id == "ip: 192.168.1.50"
    
    def test_get_endpoint_classification_critical(self):
        """Test endpoint classification for critical endpoints."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/v1/text_processing/process"
        
        classification = get_endpoint_classification(request)
        assert classification == "critical"
    
    def test_get_endpoint_classification_monitoring(self):
        """Test endpoint classification for monitoring endpoints."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/internal/monitoring/metrics"
        
        classification = get_endpoint_classification(request)
        assert classification == "monitoring"
    
    def test_get_endpoint_classification_health(self):
        """Test endpoint classification for health check endpoints."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/health"
        
        classification = get_endpoint_classification(request)
        assert classification == "health"
    
    def test_get_endpoint_classification_default(self):
        """Test endpoint classification for regular endpoints."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/v1/some/other/endpoint"
        
        classification = get_endpoint_classification(request)
        assert classification == "standard"


class TestRateLimitIntegration:
    """Integration tests for rate limiting middleware."""
    
    @pytest.fixture
    def app_with_multiple_endpoints(self):
        """App with various endpoint types for testing."""
        app = FastAPI()
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        @app.get("/v1/text_processing/process")
        async def critical_endpoint():
            return {"result": "processed"}
        
        @app.get("/internal/monitoring/metrics")
        async def monitoring():
            return {"metrics": {}}
        
        @app.get("/v1/regular/endpoint")
        async def regular():
            return {"data": "value"}
        
        # Add middleware with test settings
        settings = Mock(spec=Settings)
        settings.rate_limiting_enabled = True
        settings.redis_url = None  # Force local rate limiter
        settings.rate_limit_requests_per_minute = 5  # Low limit for testing
        settings.rate_limit_burst_size = 2
        settings.rate_limit_window_seconds = 60
        
        app.add_middleware(RateLimitMiddleware, settings=settings)
        return app
    
    def test_different_limits_per_endpoint_type(self, app_with_multiple_endpoints):
        """Test that different endpoint types have different rate limits."""
        client = TestClient(app_with_multiple_endpoints)
        
        # Health checks should never be rate limited
        for _ in range(20):
            response = client.get("/health")
            assert response.status_code == 200
        
        # Regular endpoints should be rate limited after 5 requests
        for i in range(5):
            response = client.get("/v1/regular/endpoint")
            assert response.status_code == 200
        
        # 6th request should be rate limited
        response = client.get("/v1/regular/endpoint")
        assert response.status_code == 429
    
    def test_rate_limit_headers(self, app_with_multiple_endpoints):
        """Test rate limiting headers in responses."""
        client = TestClient(app_with_multiple_endpoints)
        
        response = client.get("/v1/regular/endpoint")
        assert response.status_code == 200
        
        # Check for rate limiting headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_error_response_format(self, app_with_multiple_endpoints):
        """Test the format of rate limit exceeded error responses."""
        client = TestClient(app_with_multiple_endpoints)
        
        # Exhaust rate limit
        for _ in range(5):
            client.get("/v1/regular/endpoint")
        
        # Next request should be rate limited
        response = client.get("/v1/regular/endpoint")
        assert response.status_code == 429
        
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "rate limit exceeded" in data["error"].lower()
        assert "retry_after_seconds" in data
        assert "limit" in data
        assert "window_seconds" in data


@pytest.mark.slow
class TestRateLimitPerformance:
    """Performance tests for rate limiting middleware."""
    
    @pytest.fixture
    def performance_app(self):
        """App configured for performance testing."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        settings = Mock(spec=Settings)
        settings.rate_limiting_enabled = True
        settings.redis_url = None  # Use local rate limiter for consistent testing
        settings.rate_limit_requests_per_minute = 1000
        settings.rate_limit_burst_size = 100
        settings.rate_limit_window_seconds = 60
        
        app.add_middleware(RateLimitMiddleware, settings=settings)
        return app
    
    def test_rate_limit_performance_overhead(self, performance_app):
        """Test performance overhead of rate limiting middleware."""
        client = TestClient(performance_app)
        
        # Measure response time with rate limiting
        start_time = time.time()
        for _ in range(100):
            response = client.get("/test")
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_request = total_time / 100
        
        # Rate limiting should add minimal overhead (< 10ms per request)
        assert avg_time_per_request < 0.01, f"Average time per request: {avg_time_per_request:.3f}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self, performance_app):
        """Test rate limiting under concurrent load."""
        import httpx
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=performance_app), 
            base_url="http://test"
        ) as client:
            # Create concurrent requests
            tasks = []
            for _ in range(50):
                task = asyncio.create_task(client.get("/test"))
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should complete successfully within rate limit
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count == 50