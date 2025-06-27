"""
Integration tests for cache API endpoints.

Tests the FastAPI endpoints for configuration monitoring including
usage statistics, performance metrics, alerts, and data export.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app
from app.infrastructure.cache.monitoring import (
    CachePerformanceMonitor, 
    PerformanceMetric, 
    CompressionMetric, 
    MemoryUsageMetric,
    InvalidationMetric
)


class TestCacheEndpoints:
    """Test cache-related endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_cache_status(self, client: TestClient):
        """Test cache status endpoint."""
        response = client.get("/cache/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "redis" in data
        assert "memory" in data
        assert "performance" in data
        # Should work even if Redis is unavailable
        assert data["redis"]["status"] in ["connected", "unavailable", "error"]
    
    def test_cache_invalidate(self, client: TestClient):
        """Test cache invalidation endpoint without auth (should fail)."""
        response = client.post("/cache/invalidate", params={"pattern": "test"})
        assert response.status_code == 401  # Should require authentication
    
    def test_cache_invalidate_empty_pattern(self, client: TestClient):
        """Test cache invalidation with empty pattern without auth (should fail)."""
        response = client.post("/cache/invalidate")
        assert response.status_code == 401  # Should require authentication
    
    def test_cache_status_with_mock(self, client: TestClient):
        """Test cache status with mocked cache stats."""
        from app.dependencies import get_cache_service
        from app.main import app
        
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "status": "connected",
            "keys": 42,
            "memory_used": "2.5M",
            "connected_clients": 3
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            response = client.get("/cache/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "connected"
            assert data["keys"] == 42
            assert data["memory_used"] == "2.5M"
            assert data["connected_clients"] == 3
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_cache_invalidate_with_mock(self, client: TestClient, auth_headers):
        """Test cache invalidation with mocked cache."""
        from app.dependencies import get_cache_service
        from app.main import app
        
        # Create a mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.invalidate_pattern = AsyncMock(return_value=None)
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            response = client.post("/cache/invalidate", params={"pattern": "summarize"}, headers=auth_headers)
            assert response.status_code == 200
            
            # Verify the cache invalidation was called with correct pattern
            mock_cache_service.invalidate_pattern.assert_called_once_with("summarize", operation_context="api_endpoint")
        finally:
            # Clean up the override
            app.dependency_overrides.clear()
    
    def test_cache_invalidate_with_auth_success(self, client: TestClient, auth_headers):
        """Test cache invalidation endpoint with authentication."""
        response = client.post("/cache/invalidate", params={"pattern": "test"}, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "test" in data["message"]
    
    def test_cache_invalidate_empty_pattern_with_auth(self, client: TestClient, auth_headers):
        """Test cache invalidation with empty pattern and authentication."""
        response = client.post("/cache/invalidate", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data


class TestCachePerformanceAPIEndpoint:
    """Comprehensive tests for the cache performance API endpoint with mocked monitor."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_cache_metrics_endpoint_with_mock_monitor(self, client_with_mock_monitor, mock_performance_monitor):
        """Test the cache metrics endpoint returns expected data structure."""
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic response structure
        assert "timestamp" in data
        assert "retention_hours" in data
        assert "cache_hit_rate" in data
        assert "total_cache_operations" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        
        # Verify data matches mock return values
        assert data["retention_hours"] == 1
        assert data["cache_hit_rate"] == 85.5
        assert data["total_cache_operations"] == 150
        assert data["cache_hits"] == 128
        assert data["cache_misses"] == 22
        
        # Verify key generation statistics are included
        assert "key_generation" in data
        key_gen = data["key_generation"]
        assert key_gen["total_operations"] == 75
        assert key_gen["avg_duration"] == 0.002
        assert key_gen["max_duration"] == 0.012
        assert key_gen["slow_operations"] == 2
        
        # Verify mock monitor method was called
        mock_performance_monitor.get_performance_stats.assert_called_once()
    
    def test_cache_metrics_endpoint_handles_monitor_none(self, client):
        """Test endpoint handles case where performance monitor is None."""
        # Import here to avoid circular imports
        from app.api.internal.cache import get_performance_monitor
        from app.main import app
        
        # Override dependency to return None
        app.dependency_overrides[get_performance_monitor] = lambda: None
        
        try:
            response = client.get("/cache/metrics")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Performance monitor not available" in data["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_cache_metrics_endpoint_handles_stats_computation_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles statistics computation errors."""
        # Configure mock to raise ValueError during stats computation
        mock_performance_monitor.get_performance_stats.side_effect = ValueError("Division by zero in stats calculation")
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Statistics computation failed" in data["detail"]
    
    def test_cache_metrics_endpoint_handles_attribute_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles missing performance monitor methods."""
        # Configure mock to raise AttributeError (method not available)
        mock_performance_monitor.get_performance_stats.side_effect = AttributeError("'NoneType' object has no attribute 'get_performance_stats'")
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "monitoring is temporarily disabled" in data["detail"]
    
    def test_cache_metrics_endpoint_handles_unexpected_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles unexpected errors during stats retrieval."""
        # Configure mock to raise unexpected error
        mock_performance_monitor.get_performance_stats.side_effect = RuntimeError("Unexpected error in monitoring system")
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Unexpected error in monitoring system" in data["detail"]
    
    def test_cache_metrics_endpoint_validates_stats_format(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint validates that stats are returned in correct format."""
        # Configure mock to return invalid format (not a dict)
        mock_performance_monitor.get_performance_stats.return_value = "invalid_format"
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Invalid statistics format" in data["detail"]
    
    def test_cache_metrics_endpoint_handles_response_validation_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles Pydantic validation errors."""
        # Configure mock to return data that doesn't match the expected schema
        invalid_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": "invalid_number",  # Should be int, not string
            "cache_hit_rate": 85.5,
            "total_cache_operations": 150,
            "cache_hits": 128,
            "cache_misses": 22
        }
        mock_performance_monitor.get_performance_stats.return_value = invalid_stats
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Response format validation failed" in data["detail"]
    
    def test_cache_metrics_endpoint_with_optional_fields(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint correctly handles response with optional fields missing."""
        # Configure mock to return minimal valid stats (some optional fields missing)
        minimal_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": 1,
            "cache_hit_rate": 0.0,
            "total_cache_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0
            # No optional fields like key_generation, cache_operations, etc.
        }
        mock_performance_monitor.get_performance_stats.return_value = minimal_stats
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields are present
        assert data["timestamp"] == "2024-01-15T10:30:00.123456"
        assert data["retention_hours"] == 1
        assert data["cache_hit_rate"] == 0.0
        assert data["total_cache_operations"] == 0
        assert data["cache_hits"] == 0
        assert data["cache_misses"] == 0
        
        # Verify optional fields are handled correctly (should be None)
        assert data.get("key_generation") is None
        assert data.get("cache_operations") is None
        assert data.get("compression") is None
        assert data.get("memory_usage") is None
        assert data.get("invalidation") is None
    
    def test_cache_metrics_endpoint_with_all_optional_fields(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint correctly handles response with all optional fields present."""
        # Configure mock to return comprehensive stats with all optional sections
        comprehensive_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": 1,
            "cache_hit_rate": 85.5,
            "total_cache_operations": 150,
            "cache_hits": 128,
            "cache_misses": 22,
            "key_generation": {
                "total_operations": 75,
                "avg_duration": 0.002,
                "median_duration": 0.0015,
                "max_duration": 0.012,
                "min_duration": 0.0008,
                "avg_text_length": 1250,
                "max_text_length": 5000,
                "slow_operations": 2
            },
            "cache_operations": {
                "total_operations": 150,
                "avg_duration": 0.0045,
                "median_duration": 0.003,
                "max_duration": 0.025,
                "min_duration": 0.001,
                "slow_operations": 5,
                "by_operation_type": {
                    "get": {"count": 100, "avg_duration": 0.003, "max_duration": 0.015},
                    "set": {"count": 50, "avg_duration": 0.007, "max_duration": 0.025}
                }
            },
            "compression": {
                "total_operations": 25,
                "avg_compression_ratio": 0.65,
                "median_compression_ratio": 0.62,
                "best_compression_ratio": 0.45,
                "worst_compression_ratio": 0.89,
                "avg_compression_time": 0.003,
                "max_compression_time": 0.015,
                "total_bytes_processed": 524288,
                "total_bytes_saved": 183500,
                "overall_savings_percent": 35.0
            },
            "memory_usage": {
                "current": {
                    "total_cache_size_mb": 25.5,
                    "memory_cache_size_mb": 5.2,
                    "cache_entry_count": 100,
                    "memory_cache_entry_count": 20,
                    "avg_entry_size_bytes": 2048,
                    "process_memory_mb": 150.0,
                    "cache_utilization_percent": 51.0,
                    "warning_threshold_reached": True
                },
                "thresholds": {
                    "warning_threshold_mb": 50.0,
                    "critical_threshold_mb": 100.0
                }
            },
            "invalidation": {
                "total_invalidations": 10,
                "total_keys_invalidated": 50,
                "rates": {
                    "last_hour": 5,
                    "last_24_hours": 10
                }
            }
        }
        mock_performance_monitor.get_performance_stats.return_value = comprehensive_stats
        
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all sections are present and correctly structured
        assert "key_generation" in data
        assert "cache_operations" in data
        assert "compression" in data
        assert "memory_usage" in data
        assert "invalidation" in data
        
        # Verify detailed structure of complex sections
        assert data["cache_operations"]["by_operation_type"]["get"]["count"] == 100
        assert data["compression"]["total_bytes_saved"] == 183500
        assert data["memory_usage"]["current"]["cache_entry_count"] == 100
        assert data["invalidation"]["rates"]["last_hour"] == 5
    
    def test_cache_metrics_endpoint_content_type_and_headers(self, client_with_mock_monitor):
        """Test endpoint returns correct content type and response headers."""
        response = client_with_mock_monitor.get("/cache/metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Verify response is valid JSON
        data = response.json()
        assert isinstance(data, dict)
    
    def test_cache_metrics_endpoint_with_auth_headers(self, client_with_mock_monitor, auth_headers):
        """Test endpoint works correctly with authentication headers."""
        response = client_with_mock_monitor.get("/cache/metrics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "cache_hit_rate" in data
    
    def test_cache_metrics_endpoint_performance_with_large_dataset(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint performance with large mock dataset."""
        # Configure mock to simulate large dataset response
        large_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": 24,  # Longer retention for large dataset
            "cache_hit_rate": 92.3,
            "total_cache_operations": 10000,
            "cache_hits": 9230,
            "cache_misses": 770,
            "key_generation": {
                "total_operations": 5000,
                "avg_duration": 0.0025,
                "median_duration": 0.002,
                "max_duration": 0.150,
                "min_duration": 0.0005,
                "avg_text_length": 2500,
                "max_text_length": 50000,
                "slow_operations": 125
            },
            "cache_operations": {
                "total_operations": 10000,
                "avg_duration": 0.003,
                "median_duration": 0.0025,
                "max_duration": 0.080,
                "min_duration": 0.0008,
                "slow_operations": 89,
                "by_operation_type": {
                    "get": {"count": 7500, "avg_duration": 0.002, "max_duration": 0.050},
                    "set": {"count": 2000, "avg_duration": 0.006, "max_duration": 0.080},
                    "delete": {"count": 300, "avg_duration": 0.003, "max_duration": 0.025},
                    "invalidate": {"count": 200, "avg_duration": 0.008, "max_duration": 0.040}
                }
            }
        }
        mock_performance_monitor.get_performance_stats.return_value = large_stats
        
        import time
        start_time = time.time()
        response = client_with_mock_monitor.get("/cache/metrics")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the large dataset is handled correctly
        assert data["total_cache_operations"] == 10000
        assert data["key_generation"]["total_operations"] == 5000
        assert len(data["cache_operations"]["by_operation_type"]) == 4
        
        # Performance should still be reasonable (< 1 second for API response)
        assert response_time < 1.0
