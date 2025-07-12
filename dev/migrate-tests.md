```
backend/tests.new/
├── conftest.py                     # Global fixtures and test configuration - MOVED from backend/tests/conftest.py
├── fixtures.py                     # Reusable test data factories - TODO: EXTRACT fixtures from existing conftest.py
├── mocks.py                        # Common mock objects - TODO: EXTRACT mocks from existing tests
├── assertions.py                   # Custom test assertions - TODO: EXTRACT custom assertions from existing tests
│
├── infrastructure/                 # Tests for reusable template components
│   ├── conftest.py                 # Infrastructure-specific fixtures - TODO?
│   ├── ai/
│   │   ├── test_client.py          # TODO: test AI client interface
│   │   ├── test_gemini.py          # TODO: test Gemini implementation
│   │   ├── test_prompt_builder.py  # Prompt construction tests - MOVED from backend/tests/unit/utils/test_prompt_builder.py
│   │   ├── test_response_validator.py # MOVED from backend/tests/unit/security/test_response_validator.py
│   │   └── test_sanitization.py    # MOVED from backend/tests/unit/test_sanitization.py
│   ├── cache/
│   │   ├── test_base.py            # TODO: test cache interface
│   │   ├── test_redis.py           # TODO: SPLIT parts of backend/tests/unit/services/test_cache.py
│   │   └── test_memory.py          # TODO: SPLIT parts of backend/tests/unit/services/test_cache.py
│   ├── resilience/
│   │   ├── test_circuit_breaker.py # TODO: SPLIT parts of backend/tests/unit/test_resilience.py
│   │   ├── test_retry.py           # TODO: SPLIT parts of backend/tests/unit/test_resilience.py
│   │   └── test_presets.py         # MOVED from backend/tests/unit/test_resilience_presets.py
│   ├── security/
│   │   └── test_auth.py            # MOVED from backend/tests/unit/test_auth.py
│   └── monitoring/
│       ├── test_metrics.py         # TODO: SPLIT parts of backend/tests/unit/services/test_monitoring.py
│       ├── test_health.py          # TODO: EXTRACT health check tests
│       └── test_cache_monitor.py   # TODO: SPLIT parts of backend/tests/unit/services/test_monitoring.py
│
├── core/
│   ├── test_config.py              # TODO: COMBINE backend/tests/unit/test_config.py + test_config_monitoring.py
│   ├── test_exceptions.py          # TODO: EXTRACT exception handling tests
│   ├── test_middleware.py          # TODO: EXTRACT middleware tests
│   └── test_dependencies.py        # TODO: COMBINE backend/tests/unit/test_dependencies.py + test_dependency_injection.py
│
├── services/
│   └── test_text_processing.py     # MOVED from backend/tests/unit/test_text_processor.py
│
├── api/
│   ├── conftest.py                 # TODO: API-specific fixtures
│   ├── v1/
│   │   ├── test_text_processing.py # MOVED from backend/tests/integration/test_main_endpoints.py
│   │   └── test_health.py          # TODO: SPLIT parts of backend/tests/integration/test_main_endpoints.py
│   └── internal/
│       ├── test_monitoring.py      # MOVED from backend/tests/integration/test_config_monitoring_endpoints.py
│       └── test_admin.py           # TODO: admin endpoint tests
│
├── schemas/
│   ├── test_text_processing.py     # TODO: COMBINE backend/tests/unit/test_models.py + test_validation_schemas.py
│   ├── test_monitoring.py          # TODO: SPLIT parts of backend/tests/unit/test_models.py
│   ├── test_resilience.py          # TODO: SPLIT parts of backend/tests/unit/test_models.py
│   └── test_common.py              # TODO: SPLIT parts of backend/tests/unit/test_models.py
│
├── integration/
│   ├── conftest.py                 # TODO: integration-specific fixtures
│   ├── test_end_to_end.py          # MOVED from backend/tests/integration/test_comprehensive_backward_compatibility.py
│   ├── test_auth_endpoints.py      # MOVED from backend/tests/integration/test_auth_endpoints.py
│   ├── test_resilience_integration.py # TODO: COMBINE backend/tests/integration/test_resilience_endpoints.py + test_preset_resilience_integration.py
│   └── test_cache_integration.py   # TODO: cache integration tests
│
├── performance/
│   ├── test_cache_performance.py   # TODO: cache performance tests
│   └── test_api_performance.py     # MOVED from backend/tests/integration/test_performance_benchmark_endpoints.py
│
└── manual/
    ├── test_manual_api.py          # MOVED from backend/tests/test_manual_api.py
    └── test_manual_auth.py         # MOVED from backend/tests/test_manual_auth.py
```