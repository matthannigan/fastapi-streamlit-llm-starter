import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture(scope="function")
def test_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client for middleware integration tests with isolated app instance.

    Uses App Factory Pattern to create fresh FastAPI app that picks up
    current environment variables set via monkeypatch.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client with fresh app instance

    Note:
        - Environment must be set BEFORE calling this fixture
        - Each test gets completely isolated app instance
        - Settings are loaded fresh from current environment
    """
    # Set default test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")  # Disable for clean testing
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")  # For AI service initialization

    # Create fresh app AFTER environment is configured
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


class TestMiddlewarePerformance:

    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.skip(reason="Performance test - run manually in isolated environment")
    def test_versioning_performance_impact_minimal(self, test_client: TestClient) -> None:
        """
        Performance benchmark for versioning middleware - must run in isolation.
        
        This test measures millisecond-level overhead and is not reliable when run
        in parallel with other tests. Run manually with:
        
            pytest -xvs tests/performance/test_middleware_performance.py::TestMiddlewarePerformance::test_versioning_performance_impact_minimal --run-slow
        
        Integration Scope:
            APIVersioningMiddleware → Performance Impact Measurement
        
        Business Impact:
            Versioning should not significantly impact API response times.
            Essential for maintaining API performance standards.
        """
        import time
        import statistics

        # Test performance with different version strategies
        test_cases = [
            ("/v1/health", None, "path"),
            ("/health", {"X-API-Version": "1.0"}, "header"),
            ("/health?version=1.0", None, "query"),
            ("/health", None, "default"),
        ]

        performance_results = {}

        for endpoint, headers, strategy in test_cases:
            times = []

            # Make multiple requests to get average
            for _ in range(10):
                start_time = time.perf_counter()
                response = test_client.get(endpoint, headers=headers)
                end_time = time.perf_counter()

                if response.status_code == 200:
                    times.append((end_time - start_time) * 1000)  # Convert to ms

            if times:
                avg_time = statistics.mean(times)
                max_time = max(times)
                performance_results[strategy] = {
                    "avg_ms": avg_time,
                    "max_ms": max_time,
                    "samples": len(times),
                    "times": times
                }

        # Verify performance is acceptable
        for strategy, metrics in performance_results.items():
            # assert metrics["avg_ms"] < 50, f"{strategy} versioning too slow: {metrics['avg_ms']:.2f}ms avg"
            # assert metrics["max_ms"] < 100, f"{strategy} versioning too slow: {metrics['max_ms']:.2f}ms max"

            # Use 95th percentile instead of max
            import statistics
            all_times = metrics["times"]
            sorted_times = sorted(all_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_time = sorted_times[p95_index]

            # Assert on 95th percentile (allows for occasional spikes)
            assert p95_time < 0.120, \
                f"95th percentile versioning time too slow: {p95_time*1000:.2f}ms " \
                f"(threshold: 120ms, max observed: {max(all_times)*1000:.2f}ms)"

            # Also check median for typical performance
            median_time = statistics.median(all_times)
            assert median_time < 0.080, \
                f"Median versioning time too slow: {median_time*1000:.2f}ms"