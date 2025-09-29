"""
Health Check Infrastructure Module

Async-first, standardized health checking for system components with timeouts,
graceful degradation, and response time measurement. Used by API endpoints and
external monitoring systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

import asyncio
import logging
import time

from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthCheckError(Exception):
    """
    Base exception for health check operations with contextual error information.
    
    Provides the foundation for health check error handling, enabling specific error
    classification and appropriate response strategies for monitoring system failures.
    
    Usage:
        >>> try:
        ...     await health_checker.check_component("database")
        ... except HealthCheckError as e:
        ...     logger.error(f"Health check failed: {e}")
    """


class HealthCheckTimeoutError(HealthCheckError):
    """
    Exception raised when health check operations exceed configured timeout limits.
    
    Indicates that a component health check took longer than the allowed time,
    suggesting potential system performance issues or component unavailability.
    
    Behavior:
        - Inherits from HealthCheckError for consistent exception hierarchy
        - Automatically raised by timeout mechanisms in health check execution
        - Includes timing context for debugging performance issues
        
    Usage:
        >>> try:
        ...     status = await health_checker.check_component("slow_service")
        ... except HealthCheckTimeoutError:
        ...     # Handle timeout with degraded response
        ...     status = ComponentStatus("slow_service", HealthStatus.DEGRADED, "Timeout")
    """


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentStatus:
    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealthStatus:
    overall_status: HealthStatus
    components: List[ComponentStatus]
    timestamp: float


HealthCheckFunc = Callable[[], Awaitable[ComponentStatus]]


class HealthChecker:
    def __init__(
        self,
        default_timeout_ms: int = 2000,
        per_component_timeouts_ms: Optional[Dict[str, int]] = None,
        retry_count: int = 1,
        backoff_base_seconds: float = 0.1,
    ) -> None:
        self._checks: Dict[str, HealthCheckFunc] = {}
        self._default_timeout_ms = default_timeout_ms
        self._per_component_timeouts_ms = per_component_timeouts_ms or {}
        self._retry_count = max(0, retry_count)
        self._backoff_base_seconds = max(0.0, backoff_base_seconds)

    def register_check(self, name: str, check_func: HealthCheckFunc) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("Component name must be a non-empty string")
        if not asyncio.iscoroutinefunction(check_func):
            raise TypeError("check_func must be an async function")
        self._checks[name] = check_func

    async def check_component(self, name: str) -> ComponentStatus:
        if name not in self._checks:
            raise ValueError(f"Component '{name}' is not registered")

        timeout_ms = self._per_component_timeouts_ms.get(name, self._default_timeout_ms)
        attempt = 0
        last_error: Optional[Exception] = None
        start_overall = time.perf_counter()
        while attempt <= self._retry_count:
            try:
                result = await asyncio.wait_for(self._checks[name](), timeout=timeout_ms / 1000.0)
                elapsed_ms = (time.perf_counter() - start_overall) * 1000.0
                result.response_time_ms = max(result.response_time_ms, elapsed_ms)
                return result
            except asyncio.TimeoutError:
                last_error = HealthCheckTimeoutError(f"Health check '{name}' timed out after {timeout_ms}ms")
                logger.warning(str(last_error))
            except Exception as e:  # noqa: BLE001
                last_error = HealthCheckError(f"Health check '{name}' failed: {e}")
                logger.warning(str(last_error))

            attempt += 1
            if attempt <= self._retry_count:
                backoff = self._backoff_base_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        elapsed_ms = (time.perf_counter() - start_overall) * 1000.0
        message = str(last_error) if last_error else "Unknown health check error"
        status = HealthStatus.DEGRADED if isinstance(last_error, HealthCheckTimeoutError) else HealthStatus.UNHEALTHY
        return ComponentStatus(name=name, status=status, message=message, response_time_ms=elapsed_ms)

    async def check_all_components(self) -> SystemHealthStatus:
        tasks = [self.check_component(name) for name in self._checks]
        components = await asyncio.gather(*tasks, return_exceptions=False)
        overall = self._determine_overall_status(components)
        return SystemHealthStatus(overall_status=overall, components=components, timestamp=time.time())

    @staticmethod
    def _determine_overall_status(components: List[ComponentStatus]) -> HealthStatus:
        if any(c.status is HealthStatus.UNHEALTHY for c in components):
            return HealthStatus.UNHEALTHY
        if any(c.status is HealthStatus.DEGRADED for c in components):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY


# Built-in checks

async def check_ai_model_health() -> ComponentStatus:
    name = "ai_model"
    start = time.perf_counter()
    try:
        ai_available = bool(settings.gemini_api_key)
        status = HealthStatus.HEALTHY if ai_available else HealthStatus.DEGRADED
        message = "AI model configured" if ai_available else "Missing Gemini API key"
        return ComponentStatus(
            name=name,
            status=status,
            message=message,
            response_time_ms=(time.perf_counter() - start) * 1000.0,
            metadata={"provider": "gemini", "has_api_key": ai_available},
        )
    except Exception as e:  # noqa: BLE001
        return ComponentStatus(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"AI model health check failed: {e}",
            response_time_ms=(time.perf_counter() - start) * 1000.0,
        )


async def check_cache_health(cache_service=None) -> ComponentStatus:
    """
    Check cache system health and operational status using dependency injection for optimal performance.

    This function provides efficient cache health monitoring by accepting an optional cache service
    parameter for dependency injection. When a cache service is provided, it reuses existing
    connections and avoids redundant instantiation, making it ideal for frequent health checks.
    For backward compatibility, it falls back to creating a new cache service when none is provided.

    Args:
        cache_service: Optional AIResponseCache instance for optimal performance.
                      When provided, reuses existing connections and avoids instantiation overhead.
                      If None, creates a new cache service for backward compatibility.

    Returns:
        ComponentStatus with cache connectivity and operational status

    Performance Notes:
        - ✅ OPTIMAL: When cache_service is provided, no instantiation overhead
        - ⚠️ FALLBACK: When cache_service is None, creates new service instance (less efficient)
        - For best performance, use dependency injection in get_health_checker()
    """
    # Removed individual cache imports - now using factory pattern

    name = "cache"
    start = time.perf_counter()
    try:
        # Use injected cache service if provided (optimal performance)
        if cache_service is not None:
            stats = await cache_service.get_cache_stats()
        else:
            # Fallback: create cache service for backward compatibility
            from app.dependencies import get_cache_service
            cache_service = await get_cache_service(settings)

            try:
                await cache_service.connect()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Cache Redis connection failed, using memory-only: {e}")

            stats = await cache_service.get_cache_stats()
        redis_status = stats.get("redis", {}).get("status")
        memory_status = stats.get("memory", {}).get("status")
        error_present = "error" in stats

        is_healthy = not error_present and redis_status != "error" and memory_status != "unavailable"
        cache_type = "redis" if redis_status == "ok" else "memory"

        return ComponentStatus(
            name=name,
            status=HealthStatus.HEALTHY if is_healthy else HealthStatus.DEGRADED,
            message="Cache operational" if is_healthy else "Cache degraded",
            response_time_ms=(time.perf_counter() - start) * 1000.0,
            metadata={"cache_type": cache_type},
        )
    except Exception as e:  # noqa: BLE001
        return ComponentStatus(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Cache health check failed: {e}",
            response_time_ms=(time.perf_counter() - start) * 1000.0,
        )


async def check_resilience_health() -> ComponentStatus:
    name = "resilience"
    start = time.perf_counter()
    try:
        from app.infrastructure.resilience.orchestrator import ai_resilience

        health = ai_resilience.get_health_status()
        is_healthy: bool = bool(health.get("healthy"))
        open_breakers = list(health.get("open_circuit_breakers", []))
        half_open_breakers = list(health.get("half_open_circuit_breakers", []))
        total_breakers = int(health.get("total_circuit_breakers", 0))

        has_open = len(open_breakers) > 0
        status = HealthStatus.HEALTHY if (is_healthy and not has_open) else HealthStatus.DEGRADED
        message = "Resilience healthy" if status is HealthStatus.HEALTHY else "Open circuit breakers detected"

        return ComponentStatus(
            name=name,
            status=status,
            message=message,
            response_time_ms=(time.perf_counter() - start) * 1000.0,
            metadata={
                "open_circuit_breakers": open_breakers,
                "half_open_circuit_breakers": half_open_breakers,
                "total_circuit_breakers": total_breakers,
            },
        )
    except Exception as e:  # noqa: BLE001
        return ComponentStatus(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Resilience health check failed: {e}",
            response_time_ms=(time.perf_counter() - start) * 1000.0,
        )


async def check_database_health() -> ComponentStatus:
    """
    ⚠️ PLACEHOLDER DATABASE HEALTH CHECK - Always returns healthy!
    
    This function is NOT a functional health check. It always returns HEALTHY
    regardless of actual database state. This could mislead operators about
    system health.
    
    Replace with actual database connectivity validation for production:
    
    async def check_database_health() -> ComponentStatus:
        name = "database"
        start = time.perf_counter()
        try:
            async with get_database_connection() as conn:
                await conn.execute("SELECT 1")  # Test connectivity
            return ComponentStatus(
                name=name, status=HealthStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=(time.perf_counter() - start) * 1000.0
            )
        except Exception as e:
            return ComponentStatus(
                name=name, status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}",
                response_time_ms=(time.perf_counter() - start) * 1000.0
            )
    
    Returns:
        ComponentStatus: Always HEALTHY with "Not implemented" message
    """
    name = "database"
    start = time.perf_counter()
    return ComponentStatus(
        name=name,
        status=HealthStatus.HEALTHY,
        message="Not implemented",
        response_time_ms=(time.perf_counter() - start) * 1000.0,
    )