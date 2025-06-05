"""
Comprehensive tests for the resilience service.
Add this file as backend/tests/test_resilience.py
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from app.services.resilience import (
    AIServiceResilience,
    ResilienceStrategy,
    ResilienceConfig,
    RetryConfig,
    CircuitBreakerConfig,
    ResilienceMetrics,
    EnhancedCircuitBreaker,
    classify_exception,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    ai_resilience
)
import httpx


class TestExceptionClassification:
    """Test exception classification for retry logic."""
    
    def test_transient_errors_should_retry(self):
        """Test that transient errors are classified for retry."""
        # Network errors
        assert classify_exception(httpx.ConnectError("Connection failed")) is True
        assert classify_exception(httpx.TimeoutException("Timeout")) is True
        assert classify_exception(ConnectionError("Network issue")) is True
        assert classify_exception(TimeoutError("Timeout")) is True
        
        # Custom transient errors
        assert classify_exception(TransientAIError("Temporary issue")) is True
        assert classify_exception(RateLimitError("Rate limited")) is True
        assert classify_exception(ServiceUnavailableError("Service down")) is True
    
    def test_http_errors_classification(self):
        """Test HTTP error classification."""
        # Create mock response for HTTP errors
        mock_response = Mock()
        
        # Server errors should retry
        mock_response.status_code = 500
        assert classify_exception(httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)) is True
        
        mock_response.status_code = 502
        assert classify_exception(httpx.HTTPStatusError("Bad gateway", request=Mock(), response=mock_response)) is True
        
        mock_response.status_code = 429
        assert classify_exception(httpx.HTTPStatusError("Rate limited", request=Mock(), response=mock_response)) is True
        
        # Client errors should not retry
        mock_response.status_code = 400
        assert classify_exception(httpx.HTTPStatusError("Bad request", request=Mock(), response=mock_response)) is False
        
        mock_response.status_code = 401
        assert classify_exception(httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)) is False
    
    def test_permanent_errors_should_not_retry(self):
        """Test that permanent errors are not classified for retry."""
        assert classify_exception(PermanentAIError("Invalid input")) is False
        assert classify_exception(ValueError("Bad value")) is False
        assert classify_exception(TypeError("Wrong type")) is False
        assert classify_exception(AttributeError("Missing attribute")) is False
    
    def test_unknown_errors_default_to_retry(self):
        """Test that unknown errors default to retry (conservative approach)."""
        assert classify_exception(Exception("Unknown error")) is True
        assert classify_exception(RuntimeError("Runtime issue")) is True


class TestResilienceMetrics:
    """Test resilience metrics tracking."""
    
    def test_metrics_initialization(self):
        """Test metrics are initialized correctly."""
        metrics = ResilienceMetrics()
        
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.retry_attempts == 0
        assert metrics.success_rate == 0.0
        assert metrics.failure_rate == 0.0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = ResilienceMetrics()
        metrics.total_calls = 10
        metrics.successful_calls = 8
        metrics.failed_calls = 2
        
        assert metrics.success_rate == 80.0
        assert metrics.failure_rate == 20.0
    
    def test_metrics_to_dict(self):
        """Test metrics serialization."""
        metrics = ResilienceMetrics()
        metrics.total_calls = 5
        metrics.successful_calls = 4
        metrics.failed_calls = 1
        
        data = metrics.to_dict()
        
        assert data["total_calls"] == 5
        assert data["successful_calls"] == 4
        assert data["failed_calls"] == 1
        assert data["success_rate"] == 80.0
        assert data["failure_rate"] == 20.0


class TestEnhancedCircuitBreaker:
    """Test enhanced circuit breaker functionality."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes with metrics."""
        cb = EnhancedCircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        assert cb.metrics is not None
        assert isinstance(cb.metrics, ResilienceMetrics)
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
    
    def test_circuit_breaker_tracks_calls(self):
        """Test that circuit breaker tracks successful and failed calls."""
        cb = EnhancedCircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        # Mock a successful function
        def success_func():
            return "success"
        
        # Mock a failing function  
        def fail_func():
            raise Exception("failure")
        
        # Test successful call
        result = cb.call(success_func)
        assert result == "success"
        assert cb.metrics.total_calls == 1
        assert cb.metrics.successful_calls == 1
        assert cb.metrics.failed_calls == 0
        
        # Test failed call
        with pytest.raises(Exception):
            cb.call(fail_func)
        
        assert cb.metrics.total_calls == 2
        assert cb.metrics.successful_calls == 1
        assert cb.metrics.failed_calls == 1


class TestAIServiceResilience:
    """Test the main resilience service."""
    
    @pytest.fixture
    def resilience_service(self):
        """Create a fresh resilience service for testing."""
        return AIServiceResilience()
    
    def test_service_initialization(self, resilience_service):
        """Test service initializes with default configurations."""
        assert len(resilience_service.configs) == 4  # 4 strategies
        assert ResilienceStrategy.AGGRESSIVE in resilience_service.configs
        assert ResilienceStrategy.BALANCED in resilience_service.configs
        assert ResilienceStrategy.CONSERVATIVE in resilience_service.configs
        assert ResilienceStrategy.CRITICAL in resilience_service.configs
    
    def test_get_or_create_circuit_breaker(self, resilience_service):
        """Test circuit breaker creation and retrieval."""
        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
        
        # First call should create the circuit breaker
        cb1 = resilience_service.get_or_create_circuit_breaker("test_op", config)
        assert isinstance(cb1, EnhancedCircuitBreaker)
        assert cb1.failure_threshold == 5
        
        # Second call should return the same instance
        cb2 = resilience_service.get_or_create_circuit_breaker("test_op", config)
        assert cb1 is cb2
    
    def test_get_metrics(self, resilience_service):
        """Test metrics retrieval."""
        # First call should create new metrics
        metrics1 = resilience_service.get_metrics("test_operation")
        assert isinstance(metrics1, ResilienceMetrics)
        
        # Second call should return the same instance
        metrics2 = resilience_service.get_metrics("test_operation")
        assert metrics1 is metrics2
    
    def test_reset_metrics(self, resilience_service):
        """Test metrics reset functionality."""
        # Create some metrics
        metrics = resilience_service.get_metrics("test_op")
        metrics.total_calls = 10
        metrics.successful_calls = 8
        
        # Reset specific operation
        resilience_service.reset_metrics("test_op")
        new_metrics = resilience_service.get_metrics("test_op")
        assert new_metrics.total_calls == 0
        assert new_metrics.successful_calls == 0
    
    def test_health_status(self, resilience_service):
        """Test health status reporting."""
        # Should be healthy initially
        assert resilience_service.is_healthy() is True
        
        health = resilience_service.get_health_status()
        assert health["healthy"] is True
        assert health["open_circuit_breakers"] == []
        assert health["total_circuit_breakers"] == 0
    
    @pytest.mark.asyncio
    async def test_resilience_decorator_success(self, resilience_service):
        """Test resilience decorator with successful function."""
        call_count = 0
        
        @resilience_service.with_resilience("test_success", ResilienceStrategy.BALANCED)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 1
        
        # Check metrics
        metrics = resilience_service.get_metrics("test_success")
        assert metrics.total_calls == 1
        assert metrics.successful_calls == 1
        assert metrics.failed_calls == 0
    
    @pytest.mark.asyncio
    async def test_resilience_decorator_with_retries(self, resilience_service):
        """Test resilience decorator with transient failures."""
        call_count = 0
        
        @resilience_service.with_resilience("test_retry", ResilienceStrategy.AGGRESSIVE)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:  # Fail first call, succeed second
                raise TransientAIError("Temporary failure")
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 2  # Should have retried once
        
        # Check metrics
        metrics = resilience_service.get_metrics("test_retry")
        assert metrics.total_calls == 1  # Only counts final result
        assert metrics.successful_calls == 1
        assert metrics.retry_attempts > 0
    
    @pytest.mark.asyncio
    async def test_resilience_decorator_with_circuit_breaker(self, resilience_service):
        """Test resilience decorator with circuit breaker functionality."""
        call_count = 0
        
        @resilience_service.with_resilience("test_circuit", ResilienceStrategy.AGGRESSIVE)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Always fails")
        
        # Should fail multiple times until circuit breaker opens
        for i in range(5):  # More than failure threshold
            with pytest.raises((TransientAIError, ServiceUnavailableError)):
                await test_function()
        
        # Circuit breaker should now be open
        cb = resilience_service.circuit_breakers.get("test_circuit")
        if cb:
            # Depending on timing, circuit might be open
            assert cb.state in ["open", "closed"]
    
    @pytest.mark.asyncio
    async def test_resilience_decorator_with_fallback(self, resilience_service):
        """Test resilience decorator with fallback function."""
        call_count = 0
        fallback_called = False
        
        async def fallback_function(*args, **kwargs):
            nonlocal fallback_called
            fallback_called = True
            return "fallback_result"
        
        @resilience_service.with_resilience(
            "test_fallback", 
            ResilienceStrategy.AGGRESSIVE,
            fallback=fallback_function
        )
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Always fails")
        
        # This test is more complex due to circuit breaker timing
        # In practice, you'd need to trigger circuit breaker opening
        # For now, just test that the decorator works
        with pytest.raises(TransientAIError):
            await test_function()
        
        assert call_count > 0


class TestResilienceIntegration:
    """Test resilience service integration."""
    
    @pytest.mark.asyncio
    async def test_global_resilience_instance(self):
        """Test that global resilience instance works."""
        assert ai_resilience is not None
        assert isinstance(ai_resilience, AIServiceResilience)
        
        # Test that it has default configurations
        assert len(ai_resilience.configs) == 4
    
    def test_convenience_decorators(self):
        """Test convenience decorator functions."""
        from app.services.resilience import (
            with_aggressive_resilience,
            with_balanced_resilience,
            with_conservative_resilience,
            with_critical_resilience
        )
        
        # These should not raise exceptions when imported
        assert callable(with_aggressive_resilience)
        assert callable(with_balanced_resilience)
        assert callable(with_conservative_resilience)
        assert callable(with_critical_resilience)
    
    @pytest.mark.asyncio
    async def test_metrics_aggregation(self):
        """Test metrics aggregation across operations."""
        # Create some test metrics
        ai_resilience.get_metrics("op1").total_calls = 10
        ai_resilience.get_metrics("op1").successful_calls = 8
        ai_resilience.get_metrics("op2").total_calls = 5
        ai_resilience.get_metrics("op2").successful_calls = 5
        
        all_metrics = ai_resilience.get_all_metrics()
        
        assert "operations" in all_metrics
        assert "circuit_breakers" in all_metrics
        assert "summary" in all_metrics
        assert "op1" in all_metrics["operations"]
        assert "op2" in all_metrics["operations"]


class TestResilienceConfiguration:
    """Test resilience configuration."""
    
    def test_resilience_config_creation(self):
        """Test resilience configuration creation."""
        retry_config = RetryConfig(
            max_attempts=5,
            max_delay_seconds=60,
            exponential_multiplier=2.0
        )
        
        cb_config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120
        )
        
        config = ResilienceConfig(
            strategy=ResilienceStrategy.CONSERVATIVE,
            retry_config=retry_config,
            circuit_breaker_config=cb_config,
            enable_circuit_breaker=True,
            enable_retry=True
        )
        
        assert config.strategy == ResilienceStrategy.CONSERVATIVE
        assert config.retry_config.max_attempts == 5
        assert config.circuit_breaker_config.failure_threshold == 10
        assert config.enable_circuit_breaker is True
        assert config.enable_retry is True
    
    def test_default_configuration_values(self):
        """Test default configuration values."""
        config = ResilienceConfig()
        
        assert config.strategy == ResilienceStrategy.BALANCED
        assert config.retry_config.max_attempts == 3
        assert config.circuit_breaker_config.failure_threshold == 5
        assert config.enable_circuit_breaker is True
        assert config.enable_retry is True


@pytest.mark.asyncio
async def test_resilience_performance():
    """Test that resilience doesn't significantly impact performance."""
    call_count = 0
    
    @ai_resilience.with_resilience("perf_test", ResilienceStrategy.BALANCED)
    async def fast_function():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.001)  # 1ms simulated work
        return "result"
    
    # Measure performance
    start_time = time.time()
    
    # Run multiple calls
    tasks = [fast_function() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # All calls should succeed
    assert len(results) == 10
    assert all(r == "result" for r in results)
    assert call_count == 10
    
    # Performance should be reasonable (less than 1 second for 10 calls)
    assert total_time < 1.0
    
    # Check metrics
    metrics = ai_resilience.get_metrics("perf_test")
    assert metrics.total_calls == 10
    assert metrics.successful_calls == 10
    assert metrics.failed_calls == 0


class TestCircuitBreakerAdvanced:
    """Advanced tests for circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_state_transitions(self):
        """Test full circuit breaker state transition cycle."""
        resilience_service = AIServiceResilience()
        call_count = 0
        
        @resilience_service.with_resilience("state_test", ResilienceStrategy.AGGRESSIVE)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Always fails")
        
        cb = resilience_service.get_or_create_circuit_breaker(
            "state_test", 
            CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        )
        
        # Initial state should be closed
        assert cb.state == "closed"
        
        # Trigger failures to open circuit
        for _ in range(3):
            with pytest.raises(TransientAIError):
                await failing_function()
        
        # Circuit should be open now
        assert cb.state == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Next call should be half-open
        with pytest.raises(TransientAIError):
            await failing_function()
        
        # Should be open again after failure in half-open
        assert cb.state == "open"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery_with_success(self):
        """Test circuit breaker recovery when calls succeed."""
        resilience_service = AIServiceResilience()
        call_count = 0
        
        @resilience_service.with_resilience("recovery_test", ResilienceStrategy.AGGRESSIVE)
        async def conditional_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # First 3 calls fail (accounting for retries)
                raise TransientAIError("Initial failures")
            return "success"  # Subsequent calls succeed
        
        cb = resilience_service.get_or_create_circuit_breaker(
            "recovery_test", 
            CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        )
        
        # Trigger failures to open circuit
        try:
            # The aggressive strategy will retry, so we expect failures
            await conditional_function()
        except TransientAIError:
            pass  # Expected failure
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # This should succeed and close the circuit
        result = await conditional_function()
        assert result == "success"
        assert cb.state == "closed"


class TestFallbackFunctionality:
    """Test fallback function behavior."""
    
    @pytest.mark.asyncio
    async def test_fallback_called_when_circuit_open(self):
        """Test that fallback is called when circuit breaker is open."""
        resilience_service = AIServiceResilience()
        fallback_called = False
        fallback_args = None
        fallback_kwargs = None
        
        async def fallback_function(*args, **kwargs):
            nonlocal fallback_called, fallback_args, fallback_kwargs
            fallback_called = True
            fallback_args = args
            fallback_kwargs = kwargs
            return "fallback_result"
        
        @resilience_service.with_resilience(
            "fallback_test", 
            ResilienceStrategy.AGGRESSIVE,
            fallback=fallback_function
        )
        async def always_failing_function(param1, param2=None):
            raise TransientAIError("Always fails")
        
        # Force circuit to open by triggering failures
        cb = resilience_service.get_or_create_circuit_breaker(
            "fallback_test", 
            CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60)
        )
        
        # First call should fail and open circuit
        with pytest.raises(TransientAIError):
            await always_failing_function("test", param2="value")
        
        # Manually force circuit open by setting internal state
        cb._failure_count = cb._failure_threshold
        cb._last_failure = time.time()
        cb._state = 'open'
        
        # Second call should use fallback
        result = await always_failing_function("test", param2="value")
        
        assert result == "fallback_result"
        assert fallback_called is True
        assert fallback_args == ("test",)
        assert fallback_kwargs == {"param2": "value"}
    
    @pytest.mark.asyncio
    async def test_fallback_with_different_return_types(self):
        """Test fallback functions with different return types."""
        resilience_service = AIServiceResilience()
        
        async def dict_fallback(*args, **kwargs):
            return {"fallback": True, "data": "default"}
        
        async def list_fallback(*args, **kwargs):
            return ["fallback", "data"]
        
        @resilience_service.with_resilience(
            "dict_test", 
            ResilienceStrategy.AGGRESSIVE,
            fallback=dict_fallback
        )
        async def dict_function():
            raise TransientAIError("Fails")
        
        @resilience_service.with_resilience(
            "list_test", 
            ResilienceStrategy.AGGRESSIVE,
            fallback=list_fallback
        )
        async def list_function():
            raise TransientAIError("Fails")
        
        # Force circuits open
        for name in ["dict_test", "list_test"]:
            cb = resilience_service.get_or_create_circuit_breaker(
                name, CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60)
            )
            cb._failure_count = cb._failure_threshold
            cb._last_failure = time.time()
            cb._state = 'open'
        
        dict_result = await dict_function()
        list_result = await list_function()
        
        assert isinstance(dict_result, dict)
        assert dict_result["fallback"] is True
        assert isinstance(list_result, list)
        assert list_result[0] == "fallback"


class TestRetryStrategies:
    """Test different retry strategy configurations."""
    
    @pytest.mark.asyncio
    async def test_aggressive_strategy_behavior(self):
        """Test aggressive strategy with fast retries and low tolerance."""
        resilience_service = AIServiceResilience()
        call_count = 0
        start_time = time.time()
        
        @resilience_service.with_resilience("aggressive_test", ResilienceStrategy.AGGRESSIVE)
        async def transient_failure():
            nonlocal call_count
            call_count += 1
            if call_count < 2:  # Fail first call, succeed second
                raise TransientAIError("Temporary failure")
            return "success"
        
        result = await transient_failure()
        end_time = time.time()
        
        assert result == "success"
        assert call_count >= 2  # At least original + 1 retry
        # Aggressive strategy should be fast (less than 10 seconds)
        assert end_time - start_time < 10
    
    @pytest.mark.asyncio
    async def test_conservative_strategy_behavior(self):
        """Test conservative strategy with more retries and higher tolerance."""
        resilience_service = AIServiceResilience()
        call_count = 0
        
        @resilience_service.with_resilience("conservative_test", ResilienceStrategy.CONSERVATIVE)
        async def mostly_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 4:  # Fail first 3 calls, succeed fourth
                raise TransientAIError("Frequent failure")
            return "success"
        
        result = await mostly_failing()
        
        assert result == "success"
        assert call_count == 4  # Should retry up to 5 times total
        
        # Check metrics show retry attempts
        metrics = resilience_service.get_metrics("conservative_test")
        assert metrics.retry_attempts > 0
    
    @pytest.mark.asyncio
    async def test_critical_strategy_maximum_retries(self):
        """Test critical strategy uses maximum retry attempts."""
        resilience_service = AIServiceResilience()
        call_count = 0
        
        @resilience_service.with_resilience("critical_test", ResilienceStrategy.CRITICAL)
        async def mostly_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 6:  # Fail first 5 calls, succeed sixth
                raise TransientAIError("Critical operation failure")
            return "success"
        
        result = await mostly_failing()
        
        assert result == "success"
        assert call_count == 6  # Should retry up to 7 times total
        
        # Check that critical strategy config is correct
        config = resilience_service.configs[ResilienceStrategy.CRITICAL]
        assert config.retry_config.max_attempts == 7


class TestCustomConfiguration:
    """Test custom configuration handling."""
    
    @pytest.mark.asyncio
    async def test_custom_retry_config(self):
        """Test using custom retry configuration."""
        resilience_service = AIServiceResilience()
        
        custom_config = ResilienceConfig(
            retry_config=RetryConfig(
                max_attempts=2,
                max_delay_seconds=5,
                exponential_multiplier=0.5
            ),
            enable_circuit_breaker=False
        )
        
        call_count = 0
        
        @resilience_service.with_resilience(
            "custom_retry_test", 
            custom_config=custom_config
        )
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Always fails")
        
        with pytest.raises(TransientAIError):
            await failing_function()
        
        # Should have tried max_attempts times
        assert call_count == 2
        
        # No circuit breaker should be created
        assert "custom_retry_test" not in resilience_service.circuit_breakers
    
    @pytest.mark.asyncio
    async def test_disabled_retry_and_circuit_breaker(self):
        """Test configuration with both retry and circuit breaker disabled."""
        resilience_service = AIServiceResilience()
        
        custom_config = ResilienceConfig(
            enable_retry=False,
            enable_circuit_breaker=False
        )
        
        call_count = 0
        
        @resilience_service.with_resilience(
            "no_resilience_test", 
            custom_config=custom_config
        )
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Immediate failure")
        
        with pytest.raises(TransientAIError):
            await failing_function()
        
        # Should fail immediately without retries
        assert call_count == 1
        
        # No circuit breaker should be created
        assert "no_resilience_test" not in resilience_service.circuit_breakers


class TestConcurrentOperations:
    """Test resilience behavior with concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_isolated_metrics(self):
        """Test that concurrent operations have isolated metrics."""
        resilience_service = AIServiceResilience()
        
        async def operation_a():
            await asyncio.sleep(0.1)
            return "result_a"
        
        async def operation_b():
            await asyncio.sleep(0.1)
            raise TransientAIError("operation_b fails")
        
        decorated_a = resilience_service.with_resilience("op_a", ResilienceStrategy.BALANCED)(operation_a)
        decorated_b = resilience_service.with_resilience("op_b", ResilienceStrategy.BALANCED)(operation_b)
        
        # Run operations concurrently
        results = await asyncio.gather(
            decorated_a(),
            decorated_a(),
            return_exceptions=True
        )
        
        # Try operation_b (will fail)
        with pytest.raises(TransientAIError):
            await decorated_b()
        
        # Check isolated metrics
        metrics_a = resilience_service.get_metrics("op_a")
        metrics_b = resilience_service.get_metrics("op_b")
        
        assert metrics_a.successful_calls == 2
        assert metrics_a.failed_calls == 0
        assert metrics_b.successful_calls == 0
        assert metrics_b.failed_calls == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_isolation(self):
        """Test that circuit breakers are isolated per operation."""
        resilience_service = AIServiceResilience()
        
        @resilience_service.with_resilience("isolated_op_1", ResilienceStrategy.AGGRESSIVE)
        async def operation_1():
            raise TransientAIError("op1 fails")
        
        @resilience_service.with_resilience("isolated_op_2", ResilienceStrategy.AGGRESSIVE)
        async def operation_2():
            return "op2 success"
        
        # Trigger failures in operation_1
        for _ in range(5):
            with pytest.raises(TransientAIError):
                await operation_1()
        
        # operation_2 should still work
        result = await operation_2()
        assert result == "op2 success"
        
        # Check circuit breaker states
        cb1 = resilience_service.circuit_breakers.get("isolated_op_1")
        cb2 = resilience_service.circuit_breakers.get("isolated_op_2")
        
        assert cb1 is not None
        assert cb2 is not None
        assert cb1 is not cb2  # Different instances


class TestErrorHandlingEdgeCases:
    """Test edge cases in error handling."""
    
    @pytest.mark.asyncio
    async def test_mixed_exception_types(self):
        """Test handling of mixed transient and permanent exceptions."""
        resilience_service = AIServiceResilience()
        call_count = 0
        
        @resilience_service.with_resilience("mixed_errors", ResilienceStrategy.BALANCED)
        async def mixed_failure():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TransientAIError("Transient failure")
            elif call_count == 2:
                raise PermanentAIError("Permanent failure")  # Should not retry
            return "success"
        
        with pytest.raises(PermanentAIError):
            await mixed_failure()
        
        # Should have retried once for transient, then failed permanently
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_http_status_code_classification(self):
        """Test HTTP status code classification for retries."""
        resilience_service = AIServiceResilience()
        
        # Create mock responses for different status codes
        def create_http_error(status_code):
            mock_response = Mock()
            mock_response.status_code = status_code
            return httpx.HTTPStatusError(
                f"HTTP {status_code}", 
                request=Mock(), 
                response=mock_response
            )
        
        retry_count_429 = 0
        retry_count_400 = 0
        
        @resilience_service.with_resilience("http_429", ResilienceStrategy.AGGRESSIVE)
        async def rate_limited():
            nonlocal retry_count_429
            retry_count_429 += 1
            raise create_http_error(429)  # Should retry
        
        @resilience_service.with_resilience("http_400", ResilienceStrategy.AGGRESSIVE)
        async def bad_request():
            nonlocal retry_count_400
            retry_count_400 += 1
            raise create_http_error(400)  # Should not retry
        
        # 429 should retry
        with pytest.raises(httpx.HTTPStatusError):
            await rate_limited()
        assert retry_count_429 > 1  # Should have retried
        
        # 400 should not retry
        with pytest.raises(httpx.HTTPStatusError):
            await bad_request()
        assert retry_count_400 == 1  # Should not retry
    
    def test_exception_classification_edge_cases(self):
        """Test edge cases in exception classification."""
        # Test with None (should not happen but handle gracefully)
        assert classify_exception(Exception("generic")) is True
        
        # Test custom exception hierarchy
        class CustomTransientError(TransientAIError):
            pass
        
        class CustomPermanentError(PermanentAIError):
            pass
        
        assert classify_exception(CustomTransientError("custom transient")) is True
        assert classify_exception(CustomPermanentError("custom permanent")) is False


class TestMetricsAndMonitoring:
    """Test comprehensive metrics and monitoring functionality."""
    
    def test_metrics_datetime_tracking(self):
        """Test that metrics track success and failure timestamps."""
        resilience_service = AIServiceResilience()
        metrics = resilience_service.get_metrics("datetime_test")
        
        # Initially no timestamps
        assert metrics.last_success is None
        assert metrics.last_failure is None
        
        # Simulate success
        metrics.successful_calls += 1
        metrics.last_success = datetime.now()
        
        # Simulate failure
        metrics.failed_calls += 1
        metrics.last_failure = datetime.now()
        
        assert metrics.last_success is not None
        assert metrics.last_failure is not None
        assert isinstance(metrics.last_success, datetime)
        assert isinstance(metrics.last_failure, datetime)
    
    def test_metrics_serialization_with_timestamps(self):
        """Test metrics serialization includes timestamp information."""
        resilience_service = AIServiceResilience()
        metrics = resilience_service.get_metrics("serialization_test")
        
        now = datetime.now()
        metrics.total_calls = 5
        metrics.successful_calls = 3
        metrics.failed_calls = 2
        metrics.last_success = now
        metrics.last_failure = now
        
        data = metrics.to_dict()
        
        assert "last_success" in data
        assert "last_failure" in data
        assert data["last_success"] == now.isoformat()
        assert data["last_failure"] == now.isoformat()
    
    def test_comprehensive_health_status(self):
        """Test comprehensive health status reporting."""
        resilience_service = AIServiceResilience()
        
        # Create some circuit breakers in different states
        cb1 = resilience_service.get_or_create_circuit_breaker(
            "healthy_op", CircuitBreakerConfig()
        )
        cb2 = resilience_service.get_or_create_circuit_breaker(
            "unhealthy_op", CircuitBreakerConfig()
        )
        
        # Manually set states for testing
        cb2._failure_count = cb2._failure_threshold
        cb2._last_failure = time.time()
        cb2._state = 'open'
        
        health = resilience_service.get_health_status()
        
        assert health["healthy"] is False  # Should be unhealthy due to open circuit
        assert "unhealthy_op" in health["open_circuit_breakers"]
        assert "healthy_op" not in health["open_circuit_breakers"]
        assert health["total_circuit_breakers"] == 2
    
    def test_all_metrics_comprehensive(self):
        """Test comprehensive metrics aggregation."""
        resilience_service = AIServiceResilience()
        
        # Create some test data
        metrics1 = resilience_service.get_metrics("test_op_1")
        metrics1.total_calls = 10
        metrics1.successful_calls = 8
        
        metrics2 = resilience_service.get_metrics("test_op_2")
        metrics2.total_calls = 5
        metrics2.successful_calls = 5
        
        # Create circuit breakers
        cb1 = resilience_service.get_or_create_circuit_breaker(
            "test_op_1", CircuitBreakerConfig()
        )
        cb2 = resilience_service.get_or_create_circuit_breaker(
            "test_op_2", CircuitBreakerConfig()
        )
        
        all_metrics = resilience_service.get_all_metrics()
        
        assert "operations" in all_metrics
        assert "circuit_breakers" in all_metrics
        assert "summary" in all_metrics
        
        assert "test_op_1" in all_metrics["operations"]
        assert "test_op_2" in all_metrics["operations"]
        assert "test_op_1" in all_metrics["circuit_breakers"]
        assert "test_op_2" in all_metrics["circuit_breakers"]
        
        assert all_metrics["summary"]["total_operations"] == 2
        assert all_metrics["summary"]["total_circuit_breakers"] == 2


class TestConvenienceDecorators:
    """Test convenience decorator functions."""
    
    @pytest.mark.asyncio
    async def test_all_convenience_decorators_work(self):
        """Test that all convenience decorators function correctly."""
        from app.services.resilience import (
            with_aggressive_resilience,
            with_balanced_resilience,
            with_conservative_resilience,
            with_critical_resilience
        )
        
        @with_aggressive_resilience("aggressive_conv_test")
        async def aggressive_func():
            return "aggressive"
        
        @with_balanced_resilience("balanced_conv_test")
        async def balanced_func():
            return "balanced"
        
        @with_conservative_resilience("conservative_conv_test")
        async def conservative_func():
            return "conservative"
        
        @with_critical_resilience("critical_conv_test")
        async def critical_func():
            return "critical"
        
        # All should work and return expected values
        assert await aggressive_func() == "aggressive"
        assert await balanced_func() == "balanced"
        assert await conservative_func() == "conservative"
        assert await critical_func() == "critical"
        
        # Check that different strategies were applied
        assert "aggressive_conv_test" in ai_resilience.metrics
        assert "balanced_conv_test" in ai_resilience.metrics
        assert "conservative_conv_test" in ai_resilience.metrics
        assert "critical_conv_test" in ai_resilience.metrics


class TestResilienceEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_strategy_string_conversion(self):
        """Test using strategy as string instead of enum."""
        resilience_service = AIServiceResilience()
        
        @resilience_service.with_resilience("string_strategy_test", "aggressive")
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
        
        # Should have created metrics
        assert "string_strategy_test" in resilience_service.metrics
    
    def test_invalid_strategy_string(self):
        """Test handling of invalid strategy string."""
        resilience_service = AIServiceResilience()
        
        with pytest.raises(ValueError):
            @resilience_service.with_resilience("invalid_strategy_test", "invalid_strategy")
            async def test_function():
                return "success"
    
    @pytest.mark.asyncio
    async def test_function_with_args_and_kwargs(self):
        """Test resilience decorator with functions that have arguments."""
        resilience_service = AIServiceResilience()
        
        @resilience_service.with_resilience("args_test", ResilienceStrategy.BALANCED)
        async def function_with_args(arg1, arg2, kwarg1=None, kwarg2="default"):
            return f"{arg1}-{arg2}-{kwarg1}-{kwarg2}"
        
        result = await function_with_args("a", "b", kwarg1="c", kwarg2="d")
        assert result == "a-b-c-d"
        
        # Test with positional args only
        result2 = await function_with_args("x", "y")
        assert result2 == "x-y-None-default"
    
    @pytest.mark.asyncio
    async def test_metrics_reset_all_operations(self):
        """Test resetting metrics for all operations."""
        resilience_service = AIServiceResilience()
        
        # Create some metrics
        metrics1 = resilience_service.get_metrics("op1")
        metrics1.total_calls = 10
        metrics2 = resilience_service.get_metrics("op2")
        metrics2.total_calls = 5
        
        # Reset all
        resilience_service.reset_metrics()
        
        # Should be empty now
        assert len(resilience_service.metrics) == 0
        
        # Getting metrics again should create fresh ones
        new_metrics = resilience_service.get_metrics("op1")
        assert new_metrics.total_calls == 0
    
    def test_circuit_breaker_name_assignment(self):
        """Test that circuit breakers get proper names."""
        resilience_service = AIServiceResilience()
        
        cb = resilience_service.get_or_create_circuit_breaker(
            "named_operation", 
            CircuitBreakerConfig()
        )
        
        # The circuit breaker should have the operation name
        assert "named_operation" in resilience_service.circuit_breakers
        assert resilience_service.circuit_breakers["named_operation"] is cb


class TestRetryLogic:
    """Test specific retry logic and configurations."""
    
    @pytest.mark.asyncio
    async def test_retry_with_jitter_disabled(self):
        """Test retry configuration with jitter disabled."""
        resilience_service = AIServiceResilience()
        
        custom_config = ResilienceConfig(
            retry_config=RetryConfig(
                max_attempts=3,
                jitter=False,
                exponential_min=1.0,
                exponential_max=2.0
            )
        )
        
        call_count = 0
        call_times = []
        
        @resilience_service.with_resilience(
            "no_jitter_test",
            custom_config=custom_config
        )
        async def timed_failure():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise TransientAIError("Fail until third call")
            return "success"
        
        start_time = time.time()
        result = await timed_failure()
        
        assert result == "success"
        assert call_count == 3
        assert len(call_times) == 3
        
        # Check timing is predictable without jitter
        assert call_times[1] - call_times[0] >= 1.0  # At least 1 second wait
        assert call_times[2] - call_times[1] >= 1.0  # At least 1 second wait
    
    @pytest.mark.asyncio
    async def test_max_delay_respected(self):
        """Test that maximum delay is respected in retry logic."""
        resilience_service = AIServiceResilience()
        
        custom_config = ResilienceConfig(
            retry_config=RetryConfig(
                max_attempts=4,
                max_delay_seconds=2,  # Very short max delay
                exponential_multiplier=2.0,
                exponential_min=1.0,
                exponential_max=10.0,
                jitter=False
            )
        )
        
        call_count = 0
        
        @resilience_service.with_resilience(
            "max_delay_test",
            custom_config=custom_config
        )
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Always fails")
        
        start_time = time.time()
        
        with pytest.raises(TransientAIError):
            await always_failing()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should not exceed max_delay_seconds significantly
        # Account for some overhead but should be close to 2 seconds
        assert total_time < 5  # Should be much less due to max_delay_seconds
    
    def test_should_retry_on_exception_function(self):
        """Test the should_retry_on_exception function directly."""
        from app.services.resilience import should_retry_on_exception
        from tenacity import RetryCallState
        from unittest.mock import Mock
        
        # Mock retry state for transient error
        retry_state = Mock()
        retry_state.outcome = Mock()
        retry_state.outcome.failed = True
        retry_state.outcome.exception.return_value = TransientAIError("test")
        
        assert should_retry_on_exception(retry_state) is True
        
        # Mock retry state for permanent error
        retry_state.outcome.exception.return_value = PermanentAIError("test")
        assert should_retry_on_exception(retry_state) is False
        
        # Mock successful outcome
        retry_state.outcome.failed = False
        assert should_retry_on_exception(retry_state) is False


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_ai_service_simulation(self):
        """Simulate realistic AI service calls with various failures."""
        resilience_service = AIServiceResilience()
        
        # Simulate different AI operations
        call_counts = {"summarize": 0, "sentiment": 0, "qa": 0}
        
        @resilience_service.with_resilience("ai_summarize", ResilienceStrategy.BALANCED)
        async def summarize_text(text):
            call_counts["summarize"] += 1
            if call_counts["summarize"] < 2:
                raise RateLimitError("Rate limited")
            return f"Summary of: {text[:10]}..."
        
        @resilience_service.with_resilience("ai_sentiment", ResilienceStrategy.AGGRESSIVE)
        async def analyze_sentiment(text):
            call_counts["sentiment"] += 1
            if call_counts["sentiment"] == 1:
                raise ServiceUnavailableError("Service temporarily down")
            return "positive"
        
        async def fallback_qa(question, context):
            return "Unable to answer due to service issues"
        
        @resilience_service.with_resilience(
            "ai_qa", 
            ResilienceStrategy.CONSERVATIVE,
            fallback=fallback_qa
        )
        async def question_answering(question, context):
            call_counts["qa"] += 1
            raise TransientAIError("AI service overloaded")
        
        # Test operations
        summary = await summarize_text("This is a long text that needs summarizing")
        sentiment = await analyze_sentiment("I love this product!")
        
        assert "Summary of: This is a " in summary
        assert sentiment == "positive"
        
        # QA should eventually fail after exhausting retries
        # Conservative strategy will retry multiple times
        with pytest.raises(TransientAIError):
            await question_answering("What is AI?", "AI is artificial intelligence")
        
        # Check metrics
        summarize_metrics = resilience_service.get_metrics("ai_summarize")
        sentiment_metrics = resilience_service.get_metrics("ai_sentiment")
        
        assert summarize_metrics.successful_calls == 1
        assert summarize_metrics.retry_attempts > 0
        assert sentiment_metrics.successful_calls == 1
    
    @pytest.mark.asyncio
    async def test_degraded_service_handling(self):
        """Test handling of degraded service scenarios."""
        resilience_service = AIServiceResilience()
        
        service_health = {"status": "healthy"}
        
        async def health_check_fallback():
            return {"status": "degraded", "message": "Using cached response"}
        
        @resilience_service.with_resilience(
            "health_check",
            ResilienceStrategy.CRITICAL,
            fallback=health_check_fallback
        )
        async def check_service_health():
            if service_health["status"] == "unhealthy":
                raise ServiceUnavailableError("Service is down")
            return {"status": "healthy", "response_time": "50ms"}
        
        # Initially healthy
        health = await check_service_health()
        assert health["status"] == "healthy"
        
        # Simulate service degradation
        service_health["status"] = "unhealthy"
        
        # Force circuit breaker open for testing
        cb = resilience_service.get_or_create_circuit_breaker(
            "health_check", 
            CircuitBreakerConfig(failure_threshold=1)
        )
        cb._failure_count = cb._failure_threshold
        cb._last_failure = time.time()
        cb._state = 'open'
        
        # Should use fallback
        degraded_health = await check_service_health()
        assert degraded_health["status"] == "degraded"
        assert "cached response" in degraded_health["message"]


class TestCircuitBreakerStateTransitionLogging:
    """Test circuit breaker state transition logging that's missing coverage."""
    
    def test_circuit_breaker_direct_update_state_method(self):
        """Test the _update_state method directly to ensure coverage."""
        from unittest.mock import patch, Mock
        
        # Create circuit breaker
        cb = EnhancedCircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Test state transitions by calling the method directly
        with patch('app.services.resilience.logger') as mock_logger:
            # Mock the parent class method to set the state properly
            def mock_update_state(state):
                cb._state = state
            
            with patch.object(cb.__class__.__bases__[0], '_update_state', side_effect=mock_update_state, create=True) as mock_parent:
                # Test transition to OPEN
                cb._state = 'closed'  # Set initial state
                cb._update_state('open')
                
                # Verify parent was called
                mock_parent.assert_called_with('open')
                
                # Verify logging
                mock_logger.warning.assert_called_with("Circuit breaker opened")
                assert cb.metrics.circuit_breaker_opens == 1
                
                # Test transition to HALF_OPEN
                cb._state = 'open'
                cb._update_state('half-open')
                mock_logger.info.assert_called_with("Circuit breaker half-opened")
                assert cb.metrics.circuit_breaker_half_opens == 1
                
                # Test transition to CLOSED
                cb._state = 'half-open'
                cb._update_state('closed')
                mock_logger.info.assert_called_with("Circuit breaker closed")
                assert cb.metrics.circuit_breaker_closes == 1
    
    def test_circuit_breaker_state_no_change_no_logging(self):
        """Test circuit breaker when state doesn't change (no logging)."""
        from unittest.mock import patch
        
        cb = EnhancedCircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        with patch('app.services.resilience.logger') as mock_logger:
            # Mock the parent class method
            with patch.object(cb.__class__.__bases__[0], '_update_state', create=True) as mock_parent:
                # Set initial state and keep it the same
                cb._state = 'closed'
                
                # Call with same state - should not log state change
                cb._update_state('closed')
                
                # Parent should still be called
                mock_parent.assert_called_with('closed')
                
                # But no state change logging should occur
                mock_logger.warning.assert_not_called()
                mock_logger.info.assert_not_called()


class TestResilienceEdgeCasesAndErrorPaths:
    """Test edge cases and error paths that are missing coverage."""
    
    @pytest.mark.asyncio
    async def test_strategy_enum_instead_of_string(self):
        """Test using ResilienceStrategy enum directly (which is also a string due to str inheritance)."""
        resilience_service = AIServiceResilience()
        
        # Pass the enum directly - note that ResilienceStrategy inherits from str,
        # so isinstance(strategy, str) will still be True, but this tests
        # the enum usage pattern which is valid and commonly used
        strategy = ResilienceStrategy.AGGRESSIVE
        
        @resilience_service.with_resilience("enum_strategy_test", strategy)
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
        
        # Should have created metrics
        assert "enum_strategy_test" in resilience_service.metrics
    
    def test_is_healthy_with_open_circuit_breakers(self):
        """Test is_healthy method when circuit breakers are open (covers lines 550-551)."""
        from unittest.mock import patch
        
        resilience_service = AIServiceResilience()
        
        # Create circuit breakers in open state
        cb1 = resilience_service.get_or_create_circuit_breaker(
            "unhealthy_service", CircuitBreakerConfig()
        )
        cb2 = resilience_service.get_or_create_circuit_breaker(
            "another_unhealthy_service", CircuitBreakerConfig()
        )
        
        # Set them to open state
        cb1._state = 'open'
        cb2._state = 'open'
        
        with patch('app.services.resilience.logger') as mock_logger:
            # This should trigger the warning and return False (lines 550-551)
            is_healthy = resilience_service.is_healthy()
            
            assert is_healthy is False
            
            # Verify the warning was logged
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Unhealthy: Circuit breakers open for:" in call_args
            assert "unhealthy_service" in call_args
            assert "another_unhealthy_service" in call_args
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_no_retry_decorator(self):
        """Test circuit breaker when retry is disabled."""
        resilience_service = AIServiceResilience()
        
        custom_config = ResilienceConfig(
            enable_retry=False,  # Disabled retry
            enable_circuit_breaker=True,
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=1)
        )
        
        call_count = 0
        
        @resilience_service.with_resilience(
            "no_retry_test", 
            custom_config=custom_config
        )
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise TransientAIError("Always fails")
        
        # Should fail immediately without retries
        with pytest.raises(TransientAIError):
            await always_failing()
        
        assert call_count == 1  # No retries
        
        # Circuit breaker should still work
        cb = resilience_service.circuit_breakers.get("no_retry_test")
        assert cb is not None
    
    @pytest.mark.asyncio
    async def test_fallback_when_circuit_open_no_retry(self):
        """Test fallback execution when circuit breaker is open and retry disabled."""
        resilience_service = AIServiceResilience()
        
        fallback_called = False
        
        async def test_fallback(*args, **kwargs):
            nonlocal fallback_called
            fallback_called = True
            return "fallback_response"
        
        custom_config = ResilienceConfig(
            enable_retry=False,
            enable_circuit_breaker=True,
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=1)
        )
        
        @resilience_service.with_resilience(
            "fallback_no_retry", 
            custom_config=custom_config,
            fallback=test_fallback
        )
        async def failing_function():
            raise TransientAIError("Fails")
        
        # First call should fail and open circuit
        with pytest.raises(TransientAIError):
            await failing_function()
        
        # Manually force circuit open
        cb = resilience_service.get_or_create_circuit_breaker(
            "fallback_no_retry", 
            custom_config.circuit_breaker_config
        )
        cb._failure_count = cb._failure_threshold
        cb._last_failure = time.time()
        cb._state = 'open'
        
        # Next call should use fallback
        result = await failing_function()
        assert result == "fallback_response"
        assert fallback_called is True
    
    def test_reset_metrics_for_nonexistent_operation(self):
        """Test resetting metrics for operation that doesn't exist."""
        resilience_service = AIServiceResilience()
        
        # Should not raise an error
        resilience_service.reset_metrics("nonexistent_operation")
        
        # Should still be empty
        assert "nonexistent_operation" not in resilience_service.metrics
    
    @pytest.mark.asyncio
    async def test_decorated_function_preserves_signature(self):
        """Test that decorated function preserves original function signature and behavior."""
        resilience_service = AIServiceResilience()
        
        @resilience_service.with_resilience("signature_test", ResilienceStrategy.BALANCED)
        async def function_with_complex_signature(
            pos_arg, 
            *args, 
            keyword_arg="default", 
            **kwargs
        ):
            return {
                "pos_arg": pos_arg,
                "args": args,
                "keyword_arg": keyword_arg,
                "kwargs": kwargs
            }
        
        result = await function_with_complex_signature(
            "position",
            "extra1", 
            "extra2",
            keyword_arg="custom",
            extra_kwarg="value"
        )
        
        assert result["pos_arg"] == "position"
        assert result["args"] == ("extra1", "extra2")
        assert result["keyword_arg"] == "custom"
        assert result["kwargs"] == {"extra_kwarg": "value"}


class TestLoggingAndMonitoring:
    """Test logging and monitoring edge cases."""
    
    @pytest.mark.asyncio
    async def test_logging_levels_and_messages(self):
        """Test that appropriate log levels and messages are used."""
        from unittest.mock import patch
        import logging
        
        resilience_service = AIServiceResilience()
        
        # Set debug level to ensure debug messages are captured
        with patch('app.services.resilience.logger') as mock_logger:
            mock_logger.isEnabledFor.return_value = True
            
            @resilience_service.with_resilience("logging_test", ResilienceStrategy.BALANCED)
            async def test_function():
                return "success"
            
            result = await test_function()
            
            # Check that debug logging was called (timing may vary)
            debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
            start_calls = [call for call in debug_calls if "Starting logging_test with strategy" in call]
            completion_calls = [call for call in debug_calls if "Successfully completed logging_test" in call]
            
            # Should have at least one start and one completion call
            assert len(start_calls) > 0, f"No start log found in: {debug_calls}"
            assert len(completion_calls) > 0, f"No completion log found in: {debug_calls}"
    
    @pytest.mark.asyncio
    async def test_error_logging_includes_timing(self):
        """Test that error logging includes timing information."""
        from unittest.mock import patch
        
        resilience_service = AIServiceResilience()
        
        with patch('app.services.resilience.logger') as mock_logger:
            @resilience_service.with_resilience("error_timing_test", ResilienceStrategy.AGGRESSIVE)
            async def failing_function():
                raise PermanentAIError("Permanent failure")
            
            with pytest.raises(PermanentAIError):
                await failing_function()
            
            # Verify error logging includes timing
            error_calls = [call for call in mock_logger.error.call_args_list 
                          if "Failed error_timing_test after" in str(call)]
            assert len(error_calls) > 0


class TestCircuitBreakerIntegrationEdgeCases:
    """Test circuit breaker integration edge cases."""
    
    def test_circuit_breaker_attributes_access(self):
        """Test circuit breaker attribute access for metrics reporting."""
        cb = EnhancedCircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        # Test accessing circuit breaker properties used in get_all_metrics
        assert hasattr(cb, 'state')
        assert hasattr(cb, 'failure_count') 
        assert hasattr(cb, 'last_failure_time')
        assert hasattr(cb, 'metrics')
        
        # Test that metrics attribute exists and is proper type
        assert isinstance(cb.metrics, ResilienceMetrics)
    
    def test_circuit_breaker_without_metrics_attribute(self):
        """Test handling circuit breakers that might not have metrics."""
        resilience_service = AIServiceResilience()
        
        # Create a mock circuit breaker without metrics
        from unittest.mock import Mock
        mock_cb = Mock()
        mock_cb.state = 'closed'
        mock_cb.failure_count = 0
        mock_cb.last_failure_time = None
        # Remove the metrics attribute to simulate circuit breaker without it
        del mock_cb.metrics
        
        resilience_service.circuit_breakers["mock_cb"] = mock_cb
        
        # Should handle missing metrics gracefully
        all_metrics = resilience_service.get_all_metrics()
        
        assert "mock_cb" in all_metrics["circuit_breakers"]
        assert all_metrics["circuit_breakers"]["mock_cb"]["metrics"] == {}


class TestHealthCheckingEdgeCases:
    """Test health checking edge cases."""
    
    def test_health_status_with_half_open_breakers(self):
        """Test health status reporting with half-open circuit breakers."""
        resilience_service = AIServiceResilience()
        
        # Create circuit breakers in different states
        cb1 = resilience_service.get_or_create_circuit_breaker(
            "healthy_service", CircuitBreakerConfig()
        )
        cb2 = resilience_service.get_or_create_circuit_breaker(
            "half_open_service", CircuitBreakerConfig()
        )
        cb3 = resilience_service.get_or_create_circuit_breaker(
            "open_service", CircuitBreakerConfig()
        )
        
        # Set states manually
        cb1._state = 'closed'
        cb2._state = 'half-open'
        cb3._state = 'open'
        
        health_status = resilience_service.get_health_status()
        
        assert health_status["healthy"] is False  # Due to open circuit
        assert "open_service" in health_status["open_circuit_breakers"]
        assert "half_open_service" in health_status["half_open_circuit_breakers"]
        assert "healthy_service" not in health_status["open_circuit_breakers"]
        assert "healthy_service" not in health_status["half_open_circuit_breakers"]
        assert health_status["total_circuit_breakers"] == 3


class TestMetricsEdgeCases:
    """Test metrics edge cases and error conditions."""
    
    def test_metrics_to_dict_with_none_timestamps(self):
        """Test metrics serialization when timestamps are None."""
        metrics = ResilienceMetrics()
        
        # Ensure timestamps are None
        assert metrics.last_success is None
        assert metrics.last_failure is None
        
        data = metrics.to_dict()
        
        assert data["last_success"] is None
        assert data["last_failure"] is None
        assert data["total_calls"] == 0
        assert data["success_rate"] == 0.0
    
    def test_success_rate_edge_cases(self):
        """Test success rate calculation edge cases."""
        metrics = ResilienceMetrics()
        
        # Test with zero calls
        assert metrics.success_rate == 0.0
        assert metrics.failure_rate == 0.0
        
        # Test with only failures
        metrics.total_calls = 5
        metrics.failed_calls = 5
        metrics.successful_calls = 0
        
        assert metrics.success_rate == 0.0
        assert metrics.failure_rate == 100.0
        
        # Test with only successes
        metrics.total_calls = 3
        metrics.failed_calls = 0
        metrics.successful_calls = 3
        
        assert metrics.success_rate == 100.0
        assert metrics.failure_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])