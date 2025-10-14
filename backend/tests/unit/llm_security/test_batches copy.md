LLM Security Unit Test Implementation Inventory

---

Batch 1: Cache Module (3 files)

- Public Contract: backend/contracts/infrastructure/security/llm/cache.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/cache/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/cache/test_cache_entry.py
  b. backend/tests/unit/llm_security/cache/test_cache_statistics.py
  c. backend/tests/unit/llm_security/cache/test_security_result_cache.py

---

Batch 2: Config Loader Module (3 files)

- Public Contract: backend/contracts/infrastructure/security/llm/config_loader.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/config_loader/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/config_loader/test_configuration_error.py
  b. backend/tests/unit/llm_security/config_loader/test_security_config_loader.py
  c. backend/tests/unit/llm_security/config_loader/test_convenience_functions.py

---

Batch 3: Config Module - Part 1 (4 files)

- Public Contract: backend/contracts/infrastructure/security/llm/config.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/config/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/config/test_scanner_type_enum.py
  b. backend/tests/unit/llm_security/config/test_violation_action_enum.py
  c. backend/tests/unit/llm_security/config/test_preset_name_enum.py
  d. backend/tests/unit/llm_security/config/test_scanner_config.py

Batch 4: Config Module - Part 2 (3 files)

- Public Contract: backend/contracts/infrastructure/security/llm/config.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/config/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/config/test_performance_config.py
  b. backend/tests/unit/llm_security/config/test_logging_config.py
  c. backend/tests/unit/llm_security/config/test_security_config.py

---

Batch 5: Factory Module (1 file)

- Public Contract: backend/contracts/infrastructure/security/llm/factory.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/factory/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/factory/test_scanner_factory.py

---

Batch 6: Presets Module (4 files)

- Public Contract: backend/contracts/infrastructure/security/llm/presets.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/presets/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/presets/test_preset_generators.py
  b. backend/tests/unit/llm_security/presets/test_custom_presets.py
  c. backend/tests/unit/llm_security/presets/test_preset_retrieval.py
  d. backend/tests/unit/llm_security/presets/test_preset_integration.py

---

Batch 7: ONNX Utils Module (4 files)

- Public Contract: backend/contracts/infrastructure/security/llm/onnx_utils.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/onnx_utils/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/onnx_utils/test_onnx_provider_manager.py
  b. backend/tests/unit/llm_security/onnx_utils/test_onnx_model_manager.py
  c. backend/tests/unit/llm_security/onnx_utils/test_onnx_model_downloader.py
  d. backend/tests/unit/llm_security/onnx_utils/test_utility_functions.py

---

Batch 8: Local Scanner - Part 1 (3 files)

- Public Contract: backend/contracts/infrastructure/security/llm/scanners/local_scanner.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/scanners/local_scanner/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/scanners/local_scanner/test_model_cache_operations.py
  b. backend/tests/unit/llm_security/scanners/local_scanner/test_model_cache_initialization.py
  c. backend/tests/unit/llm_security/scanners/local_scanner/test_local_scanner_warmup_and_health.py

Batch 9: Local Scanner - Part 2 (3 files)

- Public Contract: backend/contracts/infrastructure/security/llm/scanners/local_scanner.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/scanners/local_scanner/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/scanners/local_scanner/test_local_scanner_initialization.py
  b. backend/tests/unit/llm_security/scanners/local_scanner/test_local_scanner_operations.py
  c. backend/tests/unit/llm_security/scanners/local_scanner/test_local_scanner_validate_input.py

---

Batch 10: Protocol Module - Part 1 (4 files)

- Public Contract: backend/contracts/infrastructure/security/llm/protocol.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/protocol/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/protocol/test_security_result.py
  b. backend/tests/unit/llm_security/protocol/test_enums.py
  c. backend/tests/unit/llm_security/protocol/test_violation.py
  d. backend/tests/unit/llm_security/protocol/test_security_service_protocol.py

Batch 11: Protocol Module - Part 2 (3 files)

- Public Contract: backend/contracts/infrastructure/security/llm/protocol.pyi
- Component Fixtures: backend/tests/unit/llm_security/conftest.py
- Module Fixtures: backend/tests/unit/llm_security/protocol/conftest.py
- Test Files:
  a. backend/tests/unit/llm_security/protocol/test_scan_metrics.py
  b. backend/tests/unit/llm_security/protocol/test_metrics_snapshot.py
  c. backend/tests/unit/llm_security/protocol/test_exceptions.py

---
Summary

- Total Test Files: 35
- Total Batches: 11
- Modules: 8 (cache, config_loader, config, factory, presets, onnx_utils, scanners/local_scanner, protocol)
- Multi-batch Modules: 3 (config: 7 files → 4+3, scanners/local_scanner: 6 files → 3+3, protocol: 7 files → 4+3)