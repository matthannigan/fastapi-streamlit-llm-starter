"""
Tests for monitoring endpoints.

Tests the monitoring health endpoint that checks the health of monitoring
subsystems including cache performance monitoring, cache service monitoring,
and resilience metrics collection.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock

from app.main import app
from app.dependencies import get_cache_service


class TestMonitoringHealthEndpoint:
    """Test the /monitoring/health endpoint."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_monitoring_health_success(self, client: TestClient):
        """Test monitoring health endpoint returns healthy status when all components work."""
        # Create mock cache service
        mock_cache_service = MagicMock()
        
        # Mock performance monitor
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 150
        }
        mock_performance_monitor.cache_operation_times = [{"duration": 0.01}]  # Has recent data
        mock_cache_service.performance_monitor = mock_performance_monitor
        
        # Mock cache service stats
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "connected"},
            "memory": {"memory_cache_entries": 10}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Mock resilience system
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {
                    "failures": 0,
                    "retries": 5
                }
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Check overall status
                assert data["status"] == "healthy"
                assert "timestamp" in data
                assert "components" in data
                assert "available_endpoints" in data
                
                # Check cache performance monitor component
                cache_perf = data["components"]["cache_performance_monitor"]
                assert cache_perf["status"] == "healthy"  
                assert cache_perf["total_operations_tracked"] == 150
                assert cache_perf["has_recent_data"] is True
                
                # Check cache service monitoring component
                cache_service = data["components"]["cache_service_monitoring"]
                assert cache_service["status"] == "healthy"
                assert cache_service["redis_monitoring"] == "connected"
                assert cache_service["memory_monitoring"] == "available"
                
                # Check resilience monitoring component
                resilience = data["components"]["resilience_monitoring"]
                assert resilience["status"] == "healthy"
                assert resilience["circuit_breaker_tracked"] is True
                assert resilience["retry_metrics_available"] is True
                
                # Check available endpoints
                endpoints = data["available_endpoints"]
                assert "GET /monitoring/health" in endpoints
                assert "GET /cache/status" in endpoints
                assert "GET /cache/metrics" in endpoints
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_with_auth(self, client: TestClient, auth_headers):
        """Test monitoring health endpoint works with authentication."""
        # Create minimal mock setup
        mock_cache_service = MagicMock()
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 0
        }
        mock_performance_monitor.cache_operation_times = []
        mock_cache_service.performance_monitor = mock_performance_monitor
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "unavailable"},
            "memory": {"memory_cache_entries": 0}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {"failures": 0}
                
                response = client.get("/monitoring/health", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert "components" in data
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
                
    def test_monitoring_health_cache_performance_monitor_failure(self, client: TestClient):
        """Test monitoring health when cache performance monitor fails."""
        # Create mock cache service with failing performance monitor
        mock_cache_service = MagicMock()
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.side_effect = Exception("Performance monitor error")
        mock_cache_service.performance_monitor = mock_performance_monitor
        
        # Keep cache service monitoring working
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "connected"},
            "memory": {"memory_cache_entries": 10}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Keep resilience monitoring working
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {"failures": 0}
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Overall status should be degraded
                assert data["status"] == "degraded"
                
                # Cache performance monitor should be degraded
                cache_perf = data["components"]["cache_performance_monitor"]
                assert cache_perf["status"] == "degraded" 
                assert "error" in cache_perf
                assert "Performance monitor error" in cache_perf["error"]
                
                # Other components should still be healthy
                cache_service = data["components"]["cache_service_monitoring"]
                assert cache_service["status"] == "healthy"
                
                resilience = data["components"]["resilience_monitoring"]
                assert resilience["status"] == "healthy"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_cache_service_monitoring_failure(self, client: TestClient):
        """Test monitoring health when cache service monitoring fails."""
        # Create mock cache service 
        mock_cache_service = MagicMock()
        
        # Keep performance monitor working
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 50
        }
        mock_performance_monitor.cache_operation_times = []
        mock_cache_service.performance_monitor = mock_performance_monitor
        
        # Make cache service stats fail
        mock_cache_service.get_cache_stats = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Keep resilience monitoring working
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {"retries": 3}
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Overall status should be degraded
                assert data["status"] == "degraded"
                
                # Cache performance monitor should be healthy
                cache_perf = data["components"]["cache_performance_monitor"]
                assert cache_perf["status"] == "healthy"
                
                # Cache service monitoring should be degraded
                cache_service = data["components"]["cache_service_monitoring"]
                assert cache_service["status"] == "degraded"
                assert "error" in cache_service
                assert "Redis connection failed" in cache_service["error"]
                
                # Resilience monitoring should be healthy
                resilience = data["components"]["resilience_monitoring"]
                assert resilience["status"] == "healthy"
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_resilience_monitoring_failure(self, client: TestClient):
        """Test monitoring health when resilience monitoring fails."""
        # Create mock cache service with working components
        mock_cache_service = MagicMock()
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 25
        }
        mock_performance_monitor.cache_operation_times = []
        mock_cache_service.performance_monitor = mock_performance_monitor
        
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "connected"},
            "memory": {}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Make resilience monitoring fail
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.side_effect = Exception("Circuit breaker not initialized")
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Overall status should be degraded
                assert data["status"] == "degraded"
                
                # Cache components should be healthy
                cache_perf = data["components"]["cache_performance_monitor"]
                assert cache_perf["status"] == "healthy"
                
                cache_service = data["components"]["cache_service_monitoring"]
                assert cache_service["status"] == "healthy"
                
                # Resilience monitoring should be degraded
                resilience = data["components"]["resilience_monitoring"]
                assert resilience["status"] == "degraded"
                assert "error" in resilience
                assert "Circuit breaker not initialized" in resilience["error"]
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_multiple_component_failures(self, client: TestClient):
        """Test monitoring health when multiple components fail."""
        # Create mock cache service with failing components
        mock_cache_service = MagicMock()
        
        # Make performance monitor fail
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.side_effect = Exception("Monitor failure")
        mock_cache_service.performance_monitor = mock_performance_monitor
        
        # Make cache service stats fail
        mock_cache_service.get_cache_stats = AsyncMock(side_effect=Exception("Cache failure"))
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Make resilience monitoring fail
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.side_effect = Exception("Resilience failure")
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Overall status should be degraded
                assert data["status"] == "degraded"
                
                # All components should be degraded
                for component_name in ["cache_performance_monitor", "cache_service_monitoring", "resilience_monitoring"]:
                    component = data["components"][component_name]
                    assert component["status"] == "degraded"
                    assert "error" in component
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_complete_failure(self, client: TestClient):
        """Test monitoring health when all components fail but endpoint still responds gracefully."""
        # Create a mock cache service that will cause all component checks to fail 
        mock_cache_service = MagicMock()
        
        # Make the performance_monitor access fail
        type(mock_cache_service).performance_monitor = PropertyMock(side_effect=Exception("Performance monitor failure"))
        
        # Make cache service stats fail (can't await a MagicMock)
        mock_cache_service.get_cache_stats = AsyncMock(side_effect=Exception("Cache stats failure"))
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.side_effect = Exception("Resilience failure")
                
                response = client.get("/monitoring/health")
                
                # Should still return 200 with degraded status (graceful degradation)
                assert response.status_code == 200
                data = response.json()
                
                # Overall status should be degraded
                assert data["status"] == "degraded"
                
                # All components should be degraded
                for component_name in ["cache_performance_monitor", "cache_service_monitoring", "resilience_monitoring"]:
                    component = data["components"][component_name]
                    assert component["status"] == "degraded"
                    assert "error" in component
                
                # Should still include available endpoints
                assert "available_endpoints" in data
                assert len(data["available_endpoints"]) > 0
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_no_recent_cache_data(self, client: TestClient):
        """Test monitoring health when there's no recent cache performance data."""
        # Create mock cache service
        mock_cache_service = MagicMock()
        
        # Performance monitor with no recent data
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 0
        }
        mock_performance_monitor.cache_operation_times = []  # No recent data
        mock_cache_service.performance_monitor = mock_performance_monitor
        
        # Cache service working
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "unavailable"},
            "memory": {"memory_cache_entries": 0}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Resilience monitoring working
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {"failures": 0}
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Should still be healthy even without recent data
                assert data["status"] == "healthy"
                
                cache_perf = data["components"]["cache_performance_monitor"]
                assert cache_perf["status"] == "healthy"
                assert cache_perf["has_recent_data"] is False
                assert cache_perf["total_operations_tracked"] == 0
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_resilience_stats_partial_data(self, client: TestClient):
        """Test monitoring health when resilience stats have partial data."""
        # Create minimal working cache service 
        mock_cache_service = MagicMock()
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 10
        }
        mock_performance_monitor.cache_operation_times = []
        mock_cache_service.performance_monitor = mock_performance_monitor
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "connected"}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            # Resilience monitoring with partial data (missing failures)
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {"retries": 5}  # No "failures" key
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["status"] == "healthy"
                
                resilience = data["components"]["resilience_monitoring"]
                assert resilience["status"] == "healthy"
                assert resilience["circuit_breaker_tracked"] is False  # No failures key
                assert resilience["retry_metrics_available"] is True  # Has retries key
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_invalid_auth_still_works(self, client: TestClient):
        """Test monitoring health endpoint returns 401 for invalid auth (auth is validated when provided)."""
        invalid_headers = {"Authorization": "Bearer invalid-key"}
        
        response = client.get("/monitoring/health", headers=invalid_headers)
        
        # Should return 401 since invalid credentials were provided
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid API key" in data["detail"]
    
    def test_monitoring_health_no_auth_works(self, client: TestClient):
        """Test monitoring health endpoint works with no auth headers (optional auth)."""
        # Create minimal mock setup
        mock_cache_service = MagicMock()
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 5
        }
        mock_performance_monitor.cache_operation_times = []
        mock_cache_service.performance_monitor = mock_performance_monitor
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "connected"}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {"failures": 1}
                
                # No auth headers at all
                response = client.get("/monitoring/health")
                
                # Should work since no credentials were provided (optional auth)
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert "components" in data
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    def test_monitoring_health_response_structure_complete(self, client: TestClient):
        """Test monitoring health endpoint returns complete expected structure."""
        # Create comprehensive mock setup
        mock_cache_service = MagicMock()
        mock_performance_monitor = MagicMock()
        mock_performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 100,
            "cache_hits": 85,
            "cache_misses": 15
        }
        mock_performance_monitor.cache_operation_times = [{"duration": 0.01}, {"duration": 0.02}]
        mock_cache_service.performance_monitor = mock_performance_monitor
        mock_cache_service.get_cache_stats = AsyncMock(return_value={
            "redis": {"status": "connected", "keys": 50, "memory_used": "2MB"},
            "memory": {"memory_cache_entries": 25, "total_size": "1MB"}
        })
        
        # Override the dependency
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
        
        try:
            with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
                mock_resilience.get_stats.return_value = {
                    "failures": 2,
                    "retries": 8,
                    "success_rate": 0.95
                }
                
                response = client.get("/monitoring/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify top-level structure
                required_fields = ["status", "timestamp", "components", "available_endpoints"]
                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"
                
                # Verify components structure
                expected_components = ["cache_performance_monitor", "cache_service_monitoring", "resilience_monitoring"]
                for component in expected_components:
                    assert component in data["components"], f"Missing component: {component}"
                    component_data = data["components"][component]
                    assert "status" in component_data, f"Component {component} missing status"
                    
                # Verify detailed component data for healthy components
                cache_perf = data["components"]["cache_performance_monitor"]
                assert cache_perf["status"] == "healthy"
                assert "total_operations_tracked" in cache_perf
                assert "has_recent_data" in cache_perf
                
                cache_service = data["components"]["cache_service_monitoring"]
                assert cache_service["status"] == "healthy"
                assert "redis_monitoring" in cache_service
                assert "memory_monitoring" in cache_service
                
                resilience = data["components"]["resilience_monitoring"]
                assert resilience["status"] == "healthy"
                assert "circuit_breaker_tracked" in resilience
                assert "retry_metrics_available" in resilience
                
                # Verify available endpoints
                assert isinstance(data["available_endpoints"], list)
                assert len(data["available_endpoints"]) > 0
                assert all(endpoint.startswith("GET ") for endpoint in data["available_endpoints"])
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
