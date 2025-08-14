# Health Check Infrastructure Guide

This guide explains how to use the standardized health check infrastructure.

## Overview

- Infrastructure module: `app.infrastructure.monitoring.health`
- Data models: `HealthStatus`, `ComponentStatus`, `SystemHealthStatus`
- Engine: `HealthChecker` (async, timeouts, retries, error isolation)
- Built-ins: `check_ai_model_health`, `check_cache_health`, `check_resilience_health`, `check_database_health`

## Quick Start

```python
from app.infrastructure.monitoring import HealthChecker
from app.infrastructure.monitoring import (
  check_ai_model_health, check_cache_health, check_resilience_health
)

checker = HealthChecker()
checker.register_check("ai_model", check_ai_model_health)
checker.register_check("cache", check_cache_health)
checker.register_check("resilience", check_resilience_health)
status = await checker.check_all_components()
```

## FastAPI Integration

- Use `get_health_checker()` from `app.dependencies` to obtain a cached instance.
- The `/v1/health` endpoint maps `SystemHealthStatus` to the public `HealthResponse` schema and returns `degraded` on internal failures.

## Configuration

Configure via `Settings` (env or defaults):

- `HEALTH_CHECK_TIMEOUT_MS` (maps to `health_check_timeout_ms`)
- `HEALTH_CHECK_AI_MODEL_TIMEOUT_MS`, `HEALTH_CHECK_CACHE_TIMEOUT_MS`, `HEALTH_CHECK_RESILIENCE_TIMEOUT_MS`
- `HEALTH_CHECK_RETRY_COUNT` (maps to `health_check_retry_count`)
- `HEALTH_CHECK_ENABLED_COMPONENTS` (CSV; maps to `health_check_enabled_components`)

See `app/core/config.py` for descriptions and defaults.

## Testing

- Unit tests cover engine logic (timeouts, retries, errors) and built-in checks.
- Endpoint tests cover healthy, degraded, and failure scenarios.

Run:

```bash
cd backend
pytest -q tests/infrastructure/monitoring tests/api/v1/test_health_*.py
```

## Extension Points

- Register custom checks with `checker.register_check(name, async_fn)` where `async_fn` returns `ComponentStatus`.
- Include extra metadata in `ComponentStatus.metadata` for downstream diagnostics.


## Troubleshooting

- Redis unavailable or connection errors
  - Symptom: Cache check returns degraded/unhealthy; logs show "Cache Redis connection failed".
  - Fix:
    - Verify `REDIS_URL` in environment matches your compose/service: e.g., `redis://redis:6379`.
    - In dev, bring up Redis: `docker compose up -d redis` from the project root.
    - The cache check gracefully degrades to memory-only; this is expected when Redis is down.

- Missing or invalid Gemini API key
  - Symptom: AI model check returns degraded; `ai_model_available` is false.
  - Fix: Set `GEMINI_API_KEY` in your environment (e.g., `.env`) and restart the backend.
  - Note: Rate limits or auth issues will also surface as degraded/unhealthy depending on error.

- Resilience orchestrator not initialized
  - Symptom: Resilience check shows unhealthy; import errors for `ai_resilience` in logs.
  - Fix: Ensure resilience modules are available and not excluded at build; use default orchestrator wiring.
  - Open circuit breakers will mark resilience as degraded (by design).

- Timeouts on slow checks
  - Symptom: A component returns degraded due to timeout.
  - Fix: Tune timeouts via `health_check_timeout_ms` or per-component overrides:
    - `health_check_ai_model_timeout_ms`
    - `health_check_cache_timeout_ms`
    - `health_check_resilience_timeout_ms`
  - Increase `health_check_retry_count` for transient issues.

- Invalid component names in settings
  - Symptom: Startup validation error for `health_check_enabled_components`.
  - Fix: Use only allowed names: `ai_model`, `cache`, `resilience`, `database`.

- Endpoint returns "degraded" even if a component is unhealthy
  - Explanation: The public `/v1/health` endpoint preserves backward-compatibility by mapping any non-healthy overall status to `degraded` in `HealthResponse`.
  - Action: Inspect component details internally (logs/metadata) if you need stricter semantics.

- Tests fail with event loop or Redis errors
  - Symptom: RuntimeError "Event loop is closed" or Redis pipeline errors during tests.
  - Fix:
    - Prefer unit tests that mock health checks (see `tests/api/v1/test_health_endpoint_scenarios.py`).
    - Ensure rate limiting is skipped for health during tests if middleware interferes.
    - Avoid hitting Redis in tests by monkeypatching cache classes or setting `REDIS_URL` to a test instance.

- Verifying locally
  - Curl: `curl -i http://localhost:8000/v1/health`
  - Logs: set `LOG_LEVEL=DEBUG` to see health messages.
  - Tests: `pytest -q tests/infrastructure/monitoring tests/api/v1/test_health_*.py`

