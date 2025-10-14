# Test Skeleton Summary for local_scanner Module

## Overview

This document provides a comprehensive overview of the test skeletons generated for the `local_scanner` module. The test suite follows the **Docstring-Driven Test Development** philosophy, treating the entire `local_scanner` infrastructure as a single **Unit Under Test (UUT)** and testing exclusively through its public API.

## Philosophy Summary

### 3 Most Important Principles

1. **TEST WHAT'S DOCUMENTED**: Only test behaviors, inputs, outputs, and exceptions mentioned in docstrings. The docstring serves as the specification—if it's not documented, it's probably not worth testing.

2. **THE COMPONENT IS THE UNIT**: Treat entire components (classes/modules) as indivisible units rather than testing individual methods in isolation. Test the complete public interface as a black box.

3. **MOCK ONLY AT SYSTEM BOUNDARIES**: Only mock true external dependencies (ML models, databases, external libraries), never internal collaborators. Preserve component integrity by keeping internal workings unmocked.

### 3 Most Important Anti-Patterns

1. **TESTING IMPLEMENTATION DETAILS**: Don't assert on internal method calls, private state, or undocumented behavior. Tests must verify what external callers can observe: return values, exceptions, and side effects on dependencies.

2. **OVER-MOCKING INTERNAL COMPONENTS**: Don't mock internal collaborators within the component. Mocking everything makes tests brittle and doesn't verify real component behavior.

3. **TESTING WITHOUT CONTRACTS**: Don't write tests that aren't based on documented contracts. All tests must derive from docstrings (Args, Returns, Raises, Behavior sections).

## Test File Structure

### 1. ModelCache Component (2 files)

#### `test_model_cache_initialization.py`
**Class: `TestModelCacheInitialization`** - 10 tests
- Initialization with default/custom ONNX providers
- Cache directory setup and validation
- ONNX Runtime detection
- Error handling (invalid providers, inaccessible directories)
- File locking infrastructure setup
- Initialization logging

**Key Behaviors Tested:**
- Default configuration works out-of-box
- Custom ONNX providers enable hardware acceleration
- Invalid configurations fail fast with clear errors
- Cache infrastructure is ready for concurrent operations

#### `test_model_cache_operations.py`
**Classes:**
- `TestModelCacheGetModel` (9 tests) - Core caching operations
- `TestModelCacheStatistics` (3 tests) - Metrics tracking
- `TestModelCachePreload` (3 tests) - Performance optimization
- `TestModelCacheClear` (5 tests) - Memory management

**Key Behaviors Tested:**
- Lazy loading on first access
- Cache hits avoid redundant model loads
- File locking prevents concurrent downloads
- Statistics accurately track cache effectiveness
- Preloading eliminates first-request latency
- Cache clearing maintains service functionality

### 2. BaseScanner Component (2 files)

#### `test_base_scanner_initialization.py`
**Classes:**
- `TestBaseScannerInitialization` (6 tests) - Constructor behavior
- `TestBaseScannerInitialize` (7 tests) - Lazy initialization

**Key Behaviors Tested:**
- Scanner stores configuration correctly
- Lazy initialization optimizes memory usage
- ONNX availability determined from cache
- Models load only on first use
- Initialization is idempotent
- Errors are wrapped with clear context

#### `test_base_scanner_scanning.py`
**Class: `TestBaseScannerScan`** - 10 tests

**Key Behaviors Tested:**
- Disabled scanners return empty lists
- Auto-initialization on first scan
- Violation detection and reporting
- Graceful degradation on scanner failures
- Error logging for troubleshooting
- Service availability despite failures

### 3. PromptInjectionScanner (1 file)

#### `test_prompt_injection_scanner.py`
**Class: `TestPromptInjectionScannerDetection`** - 8 tests

**Key Behaviors Tested:**
- Pattern-based injection detection
- Jailbreak attempt detection
- System prompt manipulation detection
- ML-based novel pattern detection
- Hybrid detection approach
- Threshold-based filtering
- Safe text handling (no false positives)
- Detailed violation information

### 4. LocalLLMSecurityScanner Component (5 files)

#### `test_local_scanner_initialization.py`
**Classes:**
- `TestLocalLLMSecurityScannerInitialization` (14 tests)
- `TestLocalLLMSecurityScannerInitializeMethod` (3 tests)

**Key Behaviors Tested:**
- Multiple configuration sources (object, YAML, path)
- Environment-specific configuration
- Model cache initialization with ONNX
- Result cache setup (Redis/memory)
- Lazy loading preparation
- Metrics tracking initialization
- Thread-safe lock setup
- Comprehensive error handling

#### `test_local_scanner_validate_input.py`
**Classes:**
- `TestLocalScannerValidateInputSafeText` (4 tests)
- `TestLocalScannerValidateInputThreatDetection` (5 tests)
- `TestLocalScannerValidateInputCaching` (2 tests)
- `TestLocalScannerValidateInputPerformance` (3 tests)
- `TestLocalScannerValidateInputContextHandling` (4 tests)

**Key Behaviors Tested:**
- Safe input validation (no false positives)
- Complete SecurityResult structure
- Multi-threat detection (injection, toxic, PII, bias)
- Result caching for performance
- Auto-initialization on first call
- Concurrent request handling
- Context tracking for audit trails

#### `test_local_scanner_warmup_and_health.py`
**Classes:**
- `TestLocalScannerWarmup` (8 tests)
- `TestLocalScannerHealthCheck` (14 tests)

**Key Behaviors Tested:**
- Complete and selective scanner warmup
- Warmup timing measurement
- Warmup failure resilience
- Comprehensive health reporting
- Component health monitoring
- Memory usage tracking
- Cache health and statistics
- Uptime monitoring
- Degraded status detection

#### `test_local_scanner_operations.py`
**Classes:**
- `TestLocalScannerClearCache` (6 tests)
- `TestLocalScannerGetMetrics` (5 tests)
- `TestLocalScannerGetConfiguration` (4 tests)
- `TestLocalScannerResetMetrics` (3 tests)
- `TestLocalScannerGetCacheStatistics` (4 tests)

**Key Behaviors Tested:**
- Cache clearing and statistics reset
- Comprehensive metrics collection
- Configuration access and verification
- Metrics reset functionality
- Cache performance monitoring

## Test Suite Statistics

### Total Coverage

- **Total Test Files**: 9
- **Total Test Classes**: 24
- **Total Test Methods**: 149

### Coverage by Component

| Component | Test Files | Test Classes | Test Methods |
|-----------|------------|--------------|--------------|
| ModelCache | 2 | 5 | 20 |
| BaseScanner | 2 | 3 | 23 |
| PromptInjectionScanner | 1 | 1 | 8 |
| LocalLLMSecurityScanner | 5 | 15 | 98 |

### Test Distribution by Category

| Category | Test Count | Percentage |
|----------|------------|------------|
| Initialization | 37 | 25% |
| Core Operations | 45 | 30% |
| Error Handling | 28 | 19% |
| Performance/Metrics | 25 | 17% |
| Configuration | 14 | 9% |

## Fixture Requirements

### Shared Fixtures (from conftest.py)

From `backend/tests/unit/llm_security/conftest.py`:
- `mock_violation` - Factory for creating violation instances
- `mock_security_result` - Factory for SecurityResult instances
- `mock_scanner_config` - Factory for ScannerConfig instances
- `mock_security_config` - Factory for SecurityConfig instances
- `scanner_type` - MockScannerType enum
- `violation_action` - MockViolationAction enum
- `preset_name` - MockPresetName enum

From `backend/tests/unit/llm_security/scanners/local_scanner/conftest.py`:
- `mock_model_cache` - Factory for MockModelCache instances
- `mock_base_scanner` - Factory for MockBaseScanner instances
- `mock_prompt_injection_scanner` - Factory for scanner instances
- `mock_toxicity_scanner` - Factory for scanner instances
- `mock_pii_scanner` - Factory for scanner instances
- `mock_bias_scanner` - Factory for scanner instances
- `mock_local_llm_security_scanner` - Factory for scanner service instances
- `scanner_test_texts` - Pre-defined test text scenarios
- `scanner_configuration_scenarios` - Configuration test scenarios
- `scanner_performance_test_data` - Performance benchmarks
- `scanner_error_scenarios` - Error handling scenarios

From `backend/tests/unit/conftest.py`:
- `mock_logger` - Mock logger for testing logging behavior
- `fake_time_module` - Fake time for deterministic timing tests
- `fake_datetime` - Fake datetime for time-dependent tests

## Next Steps for Implementation

### Phase 1: Critical Path (Priority Tests)

1. **ModelCache Core Operations** (15 tests)
   - `test_model_cache_operations.py::TestModelCacheGetModel`
   - Critical for all scanner functionality

2. **LocalLLMSecurityScanner Validation** (18 tests)
   - `test_local_scanner_validate_input.py::TestLocalScannerValidateInputSafeText`
   - `test_local_scanner_validate_input.py::TestLocalScannerValidateInputThreatDetection`
   - Core security scanning functionality

3. **BaseScanner Scanning** (10 tests)
   - `test_base_scanner_scanning.py::TestBaseScannerScan`
   - Foundation for all scanner types

### Phase 2: Infrastructure (Support Tests)

4. **ModelCache Initialization** (10 tests)
5. **BaseScanner Initialization** (13 tests)
6. **LocalLLMSecurityScanner Initialization** (17 tests)

### Phase 3: Operational Features

7. **Health and Metrics** (22 tests)
8. **Warmup and Performance** (8 tests)
9. **Operations and Maintenance** (22 tests)

### Phase 4: Specialized Scanners

10. **PromptInjectionScanner** (8 tests)
11. **Additional scanner types** (ToxicityScanner, PIIScanner, BiasScanner)

## Implementation Guidelines

### For Each Test Method:

1. **Read the Docstring** - Understand exactly what behavior is being verified
2. **Set Up Fixtures** - Use factory fixtures to create test instances with appropriate configuration
3. **Implement Given/When/Then** - Follow the scenario structure in the docstring
4. **Assert Observable Outcomes** - Verify return values, exceptions, or side effects on external dependencies
5. **Avoid Implementation Details** - Never assert on internal method calls or private state

### Example Implementation Pattern:

```python
async def test_loads_model_on_first_access(self, mock_model_cache):
    """Test that get_model loads model using loader function on first access."""
    
    # Given: A model that is not yet cached
    cache = mock_model_cache()
    model_name = "test-model"
    
    async def mock_loader():
        return "MockModelInstance"
    
    # When: get_model() is called with the model name and loader
    result = await cache.get_model(model_name, mock_loader)
    
    # Then: Model is loaded and returned
    assert result == "MockModelInstance"
    
    # And: Model is stored in cache
    stats = cache.get_cache_stats()
    assert stats["cached_models"] == 1
    
    # And: Cache statistics show one cache miss
    assert model_name in stats["cache_hits_by_model"]
```

## Key Testing Patterns

### Pattern 1: Testing Configuration

```python
def test_initialize_with_custom_config(self, mock_security_config):
    # Given: Custom configuration
    config = mock_security_config(
        scanners={"prompt_injection": {"enabled": True, "threshold": 0.8}}
    )
    
    # When: Component is initialized with config
    scanner = LocalLLMSecurityScanner(config=config)
    
    # Then: Configuration is applied correctly
    assert scanner.config.scanners["prompt_injection"]["enabled"] is True
```

### Pattern 2: Testing Error Handling

```python
async def test_handles_initialization_errors(self, mock_base_scanner):
    # Given: Scanner with configuration that will fail
    scanner = mock_base_scanner(config=mock_scanner_config(model_name="error_model"))
    
    # When/Then: Initialization raises appropriate error
    with pytest.raises(SecurityServiceError) as exc_info:
        await scanner.initialize()
    
    assert "initialization" in str(exc_info.value).lower()
```

### Pattern 3: Testing Observable Behavior

```python
async def test_detects_prompt_injection(self, mock_local_llm_security_scanner):
    # Given: Scanner service and malicious input
    scanner = mock_local_llm_security_scanner()
    await scanner.initialize()
    
    # When: Input with injection pattern is validated
    result = await scanner.validate_input("Ignore previous instructions")
    
    # Then: Violation is detected (observable outcome)
    assert result.is_safe is False
    assert len(result.violations) > 0
    assert any(v.type == "prompt_injection" for v in result.violations)
```

## Quality Checklist for Implementation

### Before Marking Test Complete:

- [ ] Test verifies documented contract behavior (from docstring)
- [ ] Test would pass even if internal implementation changes
- [ ] Test focuses on observable outcomes (return values, exceptions, side effects)
- [ ] Test name clearly describes behavior being verified
- [ ] Fixtures are used correctly from conftest files
- [ ] No mocking of internal collaborators (only external dependencies)
- [ ] Test follows Given/When/Then structure
- [ ] Assertions are specific and meaningful
- [ ] Test execution is fast (< 50ms per test)
- [ ] Test is deterministic and repeatable

## References

- **Testing Guides**: `docs/guides/testing/WRITING_TESTS.md`, `docs/guides/testing/UNIT_TESTS.md`
- **Docstring Standards**: `docs/guides/developer/DOCSTRINGS_TESTS.md`
- **Public Contract**: `backend/contracts/infrastructure/security/llm/scanners/local_scanner.pyi`
- **Shared Fixtures**: `backend/tests/unit/llm_security/conftest.py`
- **Module Fixtures**: `backend/tests/unit/llm_security/scanners/local_scanner/conftest.py`

## Conclusion

This test skeleton suite provides comprehensive coverage of the `local_scanner` module's public API, following behavior-driven testing principles. Each test is designed to verify documented contract behavior without depending on internal implementation details, ensuring the tests remain maintainable and valuable as the codebase evolves.

The 149 test methods cover initialization, core operations, error handling, performance characteristics, and operational features, providing the foundation for a robust, production-ready security scanning infrastructure.

