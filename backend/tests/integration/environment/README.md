# Environment Detection Integration Tests

Integration tests for the unified environment detection service following our **small, dense suite with maximum confidence** philosophy. These tests validate the complete chain from environment variables to observable service behavior across the entire application stack.

## Test Organization

### Critical Integration Seams (5 Tests Total)

#### **HIGHEST PRIORITY** (Critical for system startup and security)

1. **`test_module_initialization.py`** (HIGHEST PRIORITY)
   - Module import behavior, global state management, and cross-service consistency
   - Module Import System → Global Detector Instance → Service Startup
   - Tests concurrent access, performance SLAs, and module reloading

2. **`test_multi_context_detection.py`** (HIGHEST PRIORITY)
   - Feature-specific contexts (AI, Security, Cache, Resilience) and service integration
   - Feature Context Selection → Environment Detection → Service Metadata
   - Tests context consistency, metadata format, and cross-service propagation

3. **`test_security_environment_enforcement.py`** (HIGHEST PRIORITY)
   - Security policy enforcement based on environment detection
   - Environment Detection → Security Policy → Authentication Behavior → API Access
   - Tests production enforcement, development workflow, and fail-secure behavior

#### **HIGH PRIORITY** (Critical for system reliability)

4. **`test_confidence_fallback_system.py`** (HIGH PRIORITY)
   - Service behavior under various confidence scenarios and failure conditions
   - Signal Collection → Confidence Analysis → Fallback Decision → Service Behavior
   - Tests low confidence handling, signal resolution, and service recovery

5. **`test_end_to_end_validation.py`** (HIGH PRIORITY)
   - Complete environment propagation from variables to observable API behavior
   - Environment Variables → Environment Detection → All Services → Observable API Behavior
   - Tests full stack behavior, environment changes, and concurrent consistency

## Testing Philosophy Applied

- **Outside-In Testing**: All tests start from environment variables and API boundaries
- **High-Fidelity Infrastructure**: Real environment variables, actual module imports, live HTTP clients
- **Behavior Focus**: Observable API responses, service behaviors, not internal detection logic
- **No Internal Mocking**: Tests real component collaboration across environment detection seams
- **Fail-Secure Validation**: Ensures security and reliability during detection failures

## Running Tests

```bash
# Run all environment integration tests
make test-backend PYTEST_ARGS="tests/integration/environment/ -v"

# Run by priority level
make test-backend PYTEST_ARGS="tests/integration/environment/ -v -k 'module_initialization or multi_context or security_environment'"

# Run specific test file
make test-backend PYTEST_ARGS="tests/integration/environment/test_end_to_end_validation.py -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/integration/environment/ --cov=app.core.environment"

# Run performance-sensitive tests
make test-backend PYTEST_ARGS="tests/integration/environment/test_module_initialization.py::TestModuleInitializationIntegration::test_module_initialization_performance_sla -v"
```

## Test Fixtures

### Environment Management
- **`clean_environment`**: Complete environment variable isolation and restoration
- **`reload_environment_module`**: Module reloading for testing runtime changes
- **Environment-Specific**: Production, development, staging, testing configurations

### Feature Contexts
- **`ai_enabled_environment`**: AI features and cache optimization testing
- **`security_enforcement_environment`**: Security context override testing
- **`conflicting_signals_environment`**: Mixed environment signals for fallback testing

### Infrastructure
- **`test_client`**: FastAPI TestClient for API behavior validation
- **`performance_monitor`**: Performance measurement for SLA compliance
- **`custom_detection_config`**: Custom configuration for specialized scenarios

## Success Criteria

### **System Startup and Reliability**
- ✅ Module imports work consistently across multiple services without race conditions
- ✅ Environment detection completes within performance SLA (<100ms) during startup
- ✅ Services continue operating with safe defaults during detection failures
- ✅ Thread safety maintained under concurrent access from multiple services

### **Security and Environment Enforcement**
- ✅ Production environments enforce strict API key requirements without bypass
- ✅ Development environments enable productive workflows without authentication overhead
- ✅ Security enforcement context overrides environment for compliance requirements
- ✅ System defaults to fail-secure behavior when environment detection is uncertain

### **Service Consistency and Integration**
- ✅ All dependent services see identical environment determination across contexts
- ✅ Feature contexts (AI, Cache, Security, Resilience) provide consistent metadata
- ✅ Environment changes propagate to all services within one request cycle
- ✅ API behavior reflects environment configuration end-to-end

### **Confidence and Fallback Behavior**
- ✅ High confidence signals enable normal service operation with full functionality
- ✅ Low confidence detection triggers appropriate fallback behavior across all services
- ✅ Conflicting signals are resolved consistently and deterministically
- ✅ Services recover automatically when environment signals become available

### **End-to-End Validation**
- ✅ Complete environment stack (ENVIRONMENT=production) exhibits production behavior
- ✅ Complex deployment scenarios with mixed signals handled predictably
- ✅ Concurrent requests receive consistent environment-based responses
- ✅ Background tasks and scheduled jobs respect environment configuration

## What's NOT Tested (Unit Test Concerns)

### **Internal Implementation Details**
- Individual signal parsing and weighting algorithms
- Internal confidence calculation mathematics
- Private method behavior and internal state management
- Specific environment variable precedence rules

### **Component Isolation**
- Single environment detector instance behavior in isolation
- Individual signal source reliability and accuracy
- Internal caching mechanisms and memory optimization
- Pattern matching regular expression performance

### **Framework Integration**
- FastAPI dependency injection mechanics
- HTTP middleware integration details  
- Database connection pooling with environment-specific settings
- Third-party library configuration management

## Environment Variables for Testing

```bash
# Production Environment
ENVIRONMENT=production
API_KEY=test-api-key-12345
ADDITIONAL_API_KEYS=service-key-1,service-key-2

# Development Environment  
ENVIRONMENT=development

# Feature Flags
ENABLE_AI_CACHE=true
ENFORCE_AUTH=true

# Complex Scenarios
ENVIRONMENT=production
NODE_ENV=development  # Conflicting signal
DEBUG=true           # Mixed signals
```

## Integration Points Tested

### **Module Initialization Seam**
- Module import system → Global detector instance → Service startup
- Cross-service consistency during application initialization
- Concurrent access patterns and thread safety validation

### **Multi-Context Detection Seam**
- Feature context selection → Environment detection → Context-specific metadata
- Service integration with AI, security, cache, and resilience contexts
- Metadata format consistency and cross-service propagation

### **Security Environment Enforcement Seam**
- Environment detection → Security policy enforcement → Authentication behavior
- API access control based on environment configuration
- Fail-secure defaults during environment detection uncertainty

### **Confidence and Fallback Seam**
- Signal collection → Confidence analysis → Fallback decision → Service behavior
- Service continuity during detection failures and signal conflicts
- Recovery mechanisms when environment becomes properly detectable

### **End-to-End Validation Seam**
- Environment variables → Environment detection → All services → Observable API behavior
- Complete stack behavior validation across all environments
- Consistency under concurrent load and during environment changes

## Performance Expectations

- **Module Initialization**: <100ms for initial import and detector setup
- **Environment Detection**: <50ms for subsequent detection calls with caching
- **Concurrent Access**: Consistent performance under 20+ concurrent requests
- **Environment Changes**: Propagation to all services within 1 request cycle
- **Memory Usage**: Stable memory consumption during extended operation

## Debugging Failed Tests

### **Module Initialization Issues**
```bash
# Check for import-time dependencies
make test-backend PYTEST_ARGS="tests/integration/environment/test_module_initialization.py::TestModuleInitializationIntegration::test_circular_dependency_handling -v -s"

# Verify environment variable isolation
make test-backend PYTEST_ARGS="tests/integration/environment/test_module_initialization.py::TestModuleInitializationIntegration::test_module_state_isolation_across_tests -v -s"
```

### **Context Detection Problems**
```bash
# Test context consistency
make test-backend PYTEST_ARGS="tests/integration/environment/test_multi_context_detection.py::TestMultiContextEnvironmentDetection::test_context_consistency_across_environments -v -s"

# Verify metadata format compliance
make test-backend PYTEST_ARGS="tests/integration/environment/test_multi_context_detection.py::TestMultiContextEnvironmentDetection::test_context_metadata_format_consistency -v -s"
```

### **Security Enforcement Failures**
```bash
# Test production security enforcement  
make test-backend PYTEST_ARGS="tests/integration/environment/test_security_environment_enforcement.py::TestSecurityEnvironmentEnforcement::test_production_environment_enforces_api_key_requirements -v -s"

# Verify fail-secure behavior
make test-backend PYTEST_ARGS="tests/integration/environment/test_security_environment_enforcement.py::TestSecurityEnvironmentEnforcement::test_environment_detection_failure_defaults_to_secure_mode -v -s"
```

### **End-to-End Validation Issues**
```bash
# Test complete production stack
make test-backend PYTEST_ARGS="tests/integration/environment/test_end_to_end_validation.py::TestEndToEndEnvironmentValidation::test_production_environment_enables_complete_production_stack -v -s"

# Verify concurrent consistency
make test-backend PYTEST_ARGS="tests/integration/environment/test_end_to_end_validation.py::TestEndToEndEnvironmentValidation::test_concurrent_requests_see_consistent_environment_across_entire_stack -v -s"
```

## Test Architecture

These integration tests follow our **behavior-focused testing** principles:

1. **Test Critical Paths**: Focus on high-value environment detection workflows
2. **Trust Contracts**: Use `.pyi` contracts to define expected interfaces
3. **Test from Outside-In**: Start from environment variables and API boundaries
4. **Verify Integrations**: Test real component collaboration, not mocked interactions

The tests ensure environment detection works reliably in production, fails safely during problems, and provides consistent behavior across all dependent services.