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
    """Generic health check error."""


class HealthCheckTimeoutError(HealthCheckError):
    """Raised when a health check exceeds its timeout."""


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


async def check_cache_health() -> ComponentStatus:
    from app.infrastructure.cache import AIResponseCache

    name = "cache"
    start = time.perf_counter()
    try:
        cache_service = AIResponseCache(
            redis_url=settings.redis_url,
            default_ttl=settings.cache_default_ttl,
            text_hash_threshold=settings.cache_text_hash_threshold,
            compression_threshold=settings.cache_compression_threshold,
            compression_level=settings.cache_compression_level,
            text_size_tiers=settings.cache_text_size_tiers,
            memory_cache_size=settings.cache_memory_cache_size,
        )

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
    name = "database"
    start = time.perf_counter()
    return ComponentStatus(
        name=name,
        status=HealthStatus.HEALTHY,
        message="Not implemented",
        response_time_ms=(time.perf_counter() - start) * 1000.0,
    )