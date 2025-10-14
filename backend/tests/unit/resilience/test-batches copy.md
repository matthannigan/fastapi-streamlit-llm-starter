Comprehensive Unit Test Inventory for backend/tests/unit/resilience

Module Analysis:

- config_monitoring: 3 files
- config_presets: 5 files
- config_validator: 7 files → Split into 2 batches (4 + 3)
- retry: 3 files
- circuit_breaker: 6 files → Split into 2 batches (3 + 3)
- orchestrator: 7 files → Split into 2 batches (4 + 3)
- performance_benchmarks: 6 files → Split into 2 batches (3 + 3)

---
Batch 1: Config Monitoring Module (3 files)

Contract:
- backend/contracts/infrastructure/resilience/config_monitoring.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/config_monitoring/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/config_monitoring/test_metrics_collector_initialization.py
2. backend/tests/unit/resilience/config_monitoring/test_metrics_collector_tracking.py
3. backend/tests/unit/resilience/config_monitoring/test_metrics_collector_analysis.py

---
Batch 2: Config Presets Module (5 files)

Contract:
- backend/contracts/infrastructure/resilience/config_presets.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/config_presets/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/config_presets/test_preset_manager_initialization.py
2. backend/tests/unit/resilience/config_presets/test_preset_manager_retrieval.py
3. backend/tests/unit/resilience/config_presets/test_preset_manager_validation.py
4. backend/tests/unit/resilience/config_presets/test_preset_manager_recommendation.py
5. backend/tests/unit/resilience/config_presets/test_resilience_preset_conversion.py

---
Batch 3: Config Validator Module - Part 1 (4 files)

Contract:
- backend/contracts/infrastructure/resilience/config_validator.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/config_validator/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/config_validator/test_validator_initialization.py
2. backend/tests/unit/resilience/config_validator/test_validator_custom_config.py
3. backend/tests/unit/resilience/config_validator/test_validator_security.py
4. backend/tests/unit/resilience/config_validator/test_validator_templates.py

---
Batch 4: Config Validator Module - Part 2 (3 files)

Contract:
- backend/contracts/infrastructure/resilience/config_validator.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/config_validator/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/config_validator/test_validator_rate_limiting.py
2. backend/tests/unit/resilience/config_validator/test_validator_json.py
3. backend/tests/unit/resilience/config_validator/test_validator_preset_validation.py

---
Batch 5: Retry Module (3 files)

Contract:
- backend/contracts/infrastructure/resilience/retry.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/retry/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/retry/test_should_retry_on_exception.py
2. backend/tests/unit/resilience/retry/test_classify_exception.py
3. backend/tests/unit/resilience/retry/test_retry_config.py

---
Batch 6: Circuit Breaker Module - Part 1 (3 files)

Contract:
- backend/contracts/infrastructure/resilience/circuit_breaker.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/circuit_breaker/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/circuit_breaker/test_metrics.py
2. backend/tests/unit/resilience/circuit_breaker/test_config.py
3. backend/tests/unit/resilience/circuit_breaker/test_enhanced_circuit_breaker_initialization.py

---
Batch 7: Circuit Breaker Module - Part 2 (3 files)

Contract:
- backend/contracts/infrastructure/resilience/circuit_breaker.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/circuit_breaker/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/circuit_breaker/test_enhanced_circuit_breaker_state_transitions.py
2. backend/tests/unit/resilience/circuit_breaker/test_enhanced_circuit_breaker_metrics_integration.py
3. backend/tests/unit/resilience/circuit_breaker/test_enhanced_circuit_breaker_call_protection.py

---
Batch 8: Orchestrator Module - Part 1 (4 files)

Contract:
- backend/contracts/infrastructure/resilience/orchestrator.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/orchestrator/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/orchestrator/test_orchestrator_initialization.py
2. backend/tests/unit/resilience/orchestrator/test_orchestrator_circuit_breaker.py
3. backend/tests/unit/resilience/orchestrator/test_orchestrator_configuration.py
4. backend/tests/unit/resilience/orchestrator/test_orchestrator_resilience_decorator.py

---
Batch 9: Orchestrator Module - Part 2 (3 files)

Contract:
- backend/contracts/infrastructure/resilience/orchestrator.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/orchestrator/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/orchestrator/test_orchestrator_global_decorators.py
2. backend/tests/unit/resilience/orchestrator/test_orchestrator_metrics.py
3. backend/tests/unit/resilience/orchestrator/test_orchestrator_registration.py

---
Batch 10: Performance Benchmarks Module - Part 1 (3 files)

Contract:
- backend/contracts/infrastructure/resilience/performance_benchmarks.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/performance_benchmarks/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/performance_benchmarks/test_resilience_benchmark_initialization.py
2. backend/tests/unit/resilience/performance_benchmarks/test_measure_performance.py
3. backend/tests/unit/resilience/performance_benchmarks/test_specific_benchmarks.py

---
Batch 11: Performance Benchmarks Module - Part 2 (3 files)

Contract:
- backend/contracts/infrastructure/resilience/performance_benchmarks.pyi

Shared Fixtures:
- backend/tests/unit/resilience/conftest.py (component-level)
- backend/tests/unit/resilience/performance_benchmarks/conftest.py (module-level)

Test Files:
1. backend/tests/unit/resilience/performance_benchmarks/test_comprehensive_benchmark.py
2. backend/tests/unit/resilience/performance_benchmarks/test_analysis_and_reporting.py
3. backend/tests/unit/resilience/performance_benchmarks/test_data_structures.py

---
Summary

- Total Test Files: 36 files
- Total Batches: 11 batches
- Modules: 7 modules (config_monitoring, config_presets, config_validator, retry, circuit_breaker, orchestrator, performance_benchmarks)
- Module Splits: 4 modules split into 2 batches each (config_validator: 4+3, circuit_breaker: 3+3, orchestrator: 4+3, performance_benchmarks: 3+3)
