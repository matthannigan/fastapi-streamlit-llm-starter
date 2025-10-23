# Core Middleware Unit Tests

Unit tests for the `middleware` component's utility functions following our **behavior-driven contract testing** philosophy. These tests verify the pure utility functions and configuration validation logic of the middleware infrastructure in complete isolation, ensuring they fulfill their documented contracts.

## Component Overview

**Component Under Test**: `middleware` (`app.core.middleware.*`)

**Component Type**: Infrastructure Service (Multi Module)

**Architecture**: Layered middleware infrastructure with multiple specialized middleware components providing HTTP request/response processing capabilities

**Primary Responsibilities**:
- API versioning with flexible version detection strategies
- Rate limiting with distributed coordination support
- Request size validation with hierarchical limit configuration
- Security headers and CORS policy enforcement
- Performance monitoring and slow request detection
- Configuration validation and middleware integration

**Public Contracts**: Each middleware module provides specific contracts for request/response processing, security enforcement, and performance monitoring.

**Filesystem Locations:**
  - Production Code: `backend/app/core/middleware/*.py`
  - Public Contract: `backend/contracts/core/middleware/*.pyi`
  - Test Suite:      `backend/tests/unit/middleware/test_*.py`
  - Test Fixtures:   `backend/tests/unit/middleware/conftest.py`

## Architecture Overview

### Layered Middleware Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              MIDDLEWARE ORCHESTRATION LAYER                 │
│  __init__.py                                                │
│  - Middleware registration and ordering                     │
│  - Configuration validation                                 │
│  - Health check request detection                           │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│              REQUEST PROCESSING LAYER                       │
│  api_versioning.py                                          │
│  - Version detection from headers, paths, and query params  │
│  - Version normalization and validation                     │
│  rate_limiting.py                                           │
│  - Client identification with priority hierarchy            │
│  - Endpoint classification for differential limits          │
│  request_size.py                                            │
│  - Hierarchical size limit resolution                       │
│  - Content-Type based size restrictions                     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│              SECURITY AND MONITORING LAYER                  │
│  security.py                                                │
│  - Security header enforcement                              │
│  - CORS policy validation                                   │
│  performance_monitoring.py                                  │
│  - Request timing and slow request detection                │
│  compression.py                                             │
│  - Response compression with configurable levels            │
└─────────────────────────────────────────────────────────────┘
```

## Test Organization

### Multi-Module Test Structure (7 Test Files, ~3,500 Lines Total)

#### **API VERSIONING UTILITIES** (Version string normalization)

**Test File**: `test_middlware_api_versioning_utils.py` (~815 lines)

**Test Class**: `TestNormalizeVersion`

**Functions Tested**:
- `APIVersioningMiddleware._normalize_version(version_str: str) -> str | None`

**Test Coverage**:
1. `test_normalize_v_prefix_removed` - Lowercase 'v' prefix handling
2. `test_normalize_uppercase_v_prefix` - Uppercase 'V' prefix handling
3. `test_normalize_major_only_adds_minor` - Major version to major.minor conversion
4. `test_normalize_major_minor_preserved` - Already normalized version preservation
5. `test_normalize_patch_version_truncated` - Patch version truncation to major.minor
6. `test_normalize_invalid_version_returns_none` - Invalid format rejection
7. `test_normalize_empty_string_returns_none` - Empty string boundary handling
8. `test_normalize_none_returns_none` - None value safety

**Primary Component**: API versioning middleware with flexible version string normalization

#### **RATE LIMITING UTILITIES** (Client identification and endpoint classification)

**Test File**: `test_middlware_rate_limiting_utils.py`

**Test Classes**:
- `TestGetClientIdentifier` - Client identification priority hierarchy
- `TestGetEndpointClassification` - Endpoint classification logic

**Functions Tested**:
- `get_client_identifier(request: Request) -> str`
- `get_endpoint_classification(request: Request) -> str`

**Priority Hierarchy Validated**:
1. API key from 'x-api-key' header (highest priority)
2. API key from 'authorization' header (fallback)
3. User ID from request.state.user_id (authenticated users)
4. IP address from 'x-forwarded-for' header (proxy environments)
5. IP address from 'x-real-ip' header (single proxy)
6. Connection IP address from request.client.host (final fallback)

**Primary Component**: Rate limiting middleware with intelligent client identification

#### **REQUEST SIZE UTILITIES** (Hierarchical size limit resolution)

**Test File**: `test_middlware_request_size_utils.py` (~574 lines)

**Test Classes**:
- `TestGetSizeLimit` - Hierarchical limit resolution logic
- `TestFormatSize` - Human-readable size formatting

**Functions Tested**:
- `RequestSizeLimitMiddleware._get_size_limit(request: Request) -> int`
- `RequestSizeLimitMiddleware._format_size(size: int) -> str`

**Hierarchy Validated**:
1. Endpoint-specific limits (highest priority)
2. Content-Type based limits (fallback)
3. Default limit (final fallback)
4. Content-Type charset parameter stripping

**Primary Component**: Request size limiting with flexible configuration

#### **SECURITY UTILITIES** (Security header and validation functions)

**Test File**: `test_middlware_security_utils.py`

**Test Coverage**:
- Security header generation and validation
- CORS policy enforcement logic
- Content Security Policy (CSP) configuration

**Primary Component**: Security middleware with comprehensive header management

#### **CONFIGURATION VALIDATION** (Middleware configuration validation)

**Test File**: `test_middlware_config_validation.py` (~503 lines)

**Test Class**: `TestValidateMiddlewareConfiguration`

**Function Tested**:
- `validate_middleware_configuration(settings: Settings) -> List[str]`

**Validation Coverage**:
1. `test_rate_limiting_enabled_without_redis_url_warns` - Redis dependency validation
2. `test_invalid_compression_level_warns` - Compression level range validation
3. `test_api_versioning_missing_versions_warns` - Version configuration completeness
4. `test_invalid_max_request_size_warns` - Request size boundary validation
5. `test_invalid_slow_request_threshold_warns` - Performance threshold validation
6. `test_valid_configuration_returns_no_issues` - Complete valid configuration verification

**Primary Component**: Configuration validation for all middleware components

#### **UTILITY FUNCTIONS** (Cross-cutting utility functions)

**Test File**: `test_middlware_utility_functions.py` (~250 lines)

**Test Class**: `TestIsHealthCheckRequest`

**Function Tested**:
- `is_health_check_request(request: Request) -> bool`

**Detection Patterns Validated**:
- Exact health path matching (`/health`, `/healthz`)
- Health path prefix matching (`/health/*`)
- Kubernetes probe user agent detection (`kube-probe`)
- Alternative health endpoints (`/ping`, `/status`, `/readiness`, `/liveness`)

**Primary Component**: Health check detection for optimized request processing

## Testing Philosophy Applied

These unit tests exemplify our **behavior-driven contract testing** principles for middleware utility functions:

- **Pure Function Testing**: Middleware utility functions tested in isolation without HTTP execution
- **Contract Focus**: Tests validate documented public interfaces for utility functions
- **Boundary Mocking**: Mock only HTTP Request objects (system boundary), use real utility logic
- **Observable Outcomes**: Test return values and error conditions visible to callers
- **Edge Case Coverage**: Comprehensive validation of boundary conditions and error handling
- **Configuration Validation**: Early detection of misconfigurations before runtime

## Shared Test Infrastructure

### **Global Fixture Infrastructure** (`conftest.py` - 675 lines)

**Mock ASGI Application Fixtures**:
```python
@pytest.fixture
def mock_asgi_app() -> Mock:
    """Mock ASGI application for middleware testing."""
    mock_app = Mock(spec=ASGIApp)
    async def mock_asgi_callable(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, ...})
        await send({'type': 'http.response.body', 'body': b'{"message": "success"}'})
    mock_app.side_effect = mock_asgi_callable
    return mock_app
```

**Mock Request Factory Fixtures**:
```python
@pytest.fixture
def create_mock_request() -> Callable[..., Mock]:
    """Factory fixture for creating mock Request objects with customizable parameters."""
    def _create(path: str = "/", headers: Optional[Dict[str, str]] = None, 
                client_host: str = "127.0.0.1") -> Mock:
        request = Mock(spec=Request)
        request.url.path = path
        request.headers = headers or {}
        request.client.host = client_host
        request.state = Mock()
        return request
    return _create
```

**Specialized Request Fixtures**:
```python
@pytest.fixture
def mock_request_with_headers() -> Mock:
    """Mock Request with common HTTP headers for testing."""
    # Includes content-type, user-agent, accept headers
    
@pytest.fixture
def mock_request_with_auth() -> Mock:
    """Mock Request with authentication headers for testing."""
    # Includes authorization and x-api-key headers
    
@pytest.fixture
def mock_api_request() -> Mock:
    """Mock Request configured for API endpoint testing."""
    # Configured for /api/v1/* endpoints with JSON payload
```

## Running Tests

### **Module-Specific Test Execution**

```bash
# Run all middleware unit tests
make test-backend PYTEST_ARGS="tests/unit/middleware/ -v"

# Run specific utility function tests
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_api_versioning_utils.py -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_rate_limiting_utils.py -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_request_size_utils.py -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_security_utils.py -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_config_validation.py -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_utility_functions.py -v"

# Run specific test classes
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_api_versioning_utils.py::TestNormalizeVersion -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_rate_limiting_utils.py::TestGetClientIdentifier -v"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_request_size_utils.py::TestGetSizeLimit -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/unit/middleware/ --cov=app.core.middleware"
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_api_versioning_utils.py --cov=app.core.middleware.api_versioning"
```

### **Pattern-Based Test Execution**

```bash
# Run all versioning tests
make test-backend PYTEST_ARGS="tests/unit/middleware/ -v -k 'version'"

# Run all client identification tests
make test-backend PYTEST_ARGS="tests/unit/middleware/ -v -k 'client_identifier'"

# Run all configuration validation tests
make test-backend PYTEST_ARGS="tests/unit/middleware/ -v -k 'config'"

# Run all size limit tests
make test-backend PYTEST_ARGS="tests/unit/middleware/ -v -k 'size_limit or format_size'"
```

## Test Quality Standards

### **Performance Requirements**
- **Execution Speed**: < 10ms per individual unit test
- **Pure Function Tests**: No HTTP execution overhead
- **Determinism**: No timing dependencies or external service calls
- **Isolation**: Each test completely independent

### **Coverage Requirements**
- **Utility Functions**: 100% test coverage for pure functions
- **Configuration Validation**: Complete validation logic coverage
- **Error Handling**: 100% exception condition coverage
- **Edge Cases**: All boundary conditions and invalid inputs tested

### **Test Structure Standards**
- **Pure Function Focus**: Tests verify utility function behavior without middleware execution
- **Contract Documentation**: Each test documents the specific contract being validated
- **Business Impact**: Clear documentation of why each behavior matters
- **Edge Case Coverage**: Comprehensive boundary and error condition testing

## Success Criteria

### **API Versioning Utilities**
- ✅ Version string normalization handles all documented formats correctly
- ✅ Prefix removal (v/V) works consistently across all version patterns
- ✅ Major-only versions converted to major.minor format
- ✅ Patch versions truncated to major.minor
- ✅ Invalid version strings return None for proper error handling
- ✅ Empty string and None inputs handled safely

### **Rate Limiting Utilities**
- ✅ Client identification follows documented priority hierarchy
- ✅ API key headers take precedence over user ID and IP identification
- ✅ X-Forwarded-For header uses first IP in chain
- ✅ Fallback to connection IP when no headers available
- ✅ Endpoint classification logic categorizes requests correctly

### **Request Size Utilities**
- ✅ Hierarchical size limit resolution: endpoint → content-type → default
- ✅ Content-Type charset parameters stripped before lookup
- ✅ Size formatting provides human-readable output (B, KB, MB, GB)
- ✅ Boundary values formatted with correct units
- ✅ One decimal precision maintained across all size units

### **Security Utilities**
- ✅ Security headers generated correctly per configuration
- ✅ CORS policy validation enforces proper access control
- ✅ CSP configuration prevents common security vulnerabilities

### **Configuration Validation**
- ✅ Rate limiting without Redis URL generates appropriate warning
- ✅ Invalid compression levels detected and reported
- ✅ Missing API version configuration flagged when versioning enabled
- ✅ Invalid request size limits identified before runtime
- ✅ Invalid performance thresholds caught during validation
- ✅ Valid configurations pass without false positive warnings

### **Utility Functions**
- ✅ Health check requests identified by path patterns
- ✅ Kubernetes probe user agents detected correctly
- ✅ Alternative health endpoints (/ping, /status) recognized
- ✅ Non-health check requests properly rejected

## What's NOT Tested (Integration Test Concerns)

### **Full Middleware Execution**
- Complete ASGI middleware pipeline execution
- Request/response modification during actual HTTP processing
- Middleware ordering and interaction patterns
- Error response generation and formatting

### **External Service Integration**
- Actual Redis connection for distributed rate limiting
- Real HTTP client interactions
- Production environment configuration
- Container orchestration health check integration

### **System-Level Behavior**
- Middleware performance under load
- Memory usage and resource consumption
- Concurrent request processing
- Thread safety and async execution patterns

## Environment Variables for Testing

```bash
# Middleware Configuration
RATE_LIMITING_ENABLED=true                # Enable/disable rate limiting
API_VERSIONING_ENABLED=true               # Enable/disable API versioning
COMPRESSION_ENABLED=true                  # Enable/disable response compression
COMPRESSION_LEVEL=6                       # Compression level (1-9)

# Rate Limiting Configuration
REDIS_URL=redis://localhost:6379          # Redis URL for distributed rate limiting
RATE_LIMIT_DEFAULT=100                    # Default requests per minute

# Request Size Configuration
MAX_REQUEST_SIZE=10485760                 # Maximum request size in bytes (10MB)
REQUEST_SIZE_ENDPOINT_LIMITS='{"...": ...}' # Endpoint-specific size limits

# API Versioning Configuration
DEFAULT_API_VERSION=1.0                   # Default API version
CURRENT_API_VERSION=1.0                   # Current API version

# Performance Monitoring Configuration
SLOW_REQUEST_THRESHOLD=1000               # Slow request threshold in milliseconds

# Logging Configuration
LOG_LEVEL=INFO                            # Logging level for middleware
```

## Test Method Examples

### **Version Normalization Testing Example**
```python
def test_normalize_v_prefix_removed(self) -> None:
    """
    Test that lowercase 'v' prefix is properly removed from version strings.
    
    Business Impact:
        Ensures API consumers can specify versions using the common 'v' prefix
        format (e.g., "v1.0") without breaking version detection.
    
    Scenario:
        Given: Version string with lowercase 'v' prefix ("v1.0")
        When: _normalize_version processes the input
        Then: Prefix is removed and major.minor format is preserved ("1.0")
    
    Edge Cases Validated:
        - Prefix removal does not affect numeric components
        - Major.minor format is preserved after prefix removal
        - Output format remains consistent with other normalization paths
    """
    result = APIVersioningMiddleware._normalize_version(None, "v1.0")
    assert result == "1.0"
```

### **Client Identification Testing Example**
```python
def test_api_key_header_priority_highest(self, create_mock_request: Callable[..., Mock]) -> None:
    """
    Test that x-api-key header has highest priority in client identification.
    
    Business Impact:
        API keys provide the most reliable client identification for
        authenticated API access. They should override all other identification
        methods to ensure proper rate limiting for API clients.
    
    Scenario:
        Given: Request contains x-api-key header with valid API key
        When: get_client_identifier is called
        Then: Returns API key identifier with highest priority
    
    Contract Reference:
        get_client_identifier() returns "api_key: {key}" for x-api-key header
    """
    request = create_mock_request(
        headers={"x-api-key": "test-key-123"},
        client_host="192.168.1.1"
    )
    
    identifier = get_client_identifier(request)
    
    assert identifier == "api_key: test-key-123"
```

### **Configuration Validation Testing Example**
```python
def test_rate_limiting_enabled_without_redis_url_warns(self) -> None:
    """
    Test that rate limiting enabled without Redis URL generates appropriate warning.
    
    Business Impact:
        Prevents silent degradation of rate limiting functionality in production.
        Distributed rate limiting requires Redis for multi-instance coordination.
    
    Scenario:
        Given: Rate limiting is enabled but Redis URL is not configured
        When: Configuration validation is performed
        Then: Warning is generated indicating local cache fallback usage
    """
    settings = create_settings()
    settings.rate_limiting_enabled = True
    settings.redis_url = ""
    
    issues = validate_middleware_configuration(settings)
    
    assert len(issues) >= 1
    rate_limiting_issues = [issue for issue in issues 
                           if "rate limiting" in issue.lower() and "redis" in issue.lower()]
    assert len(rate_limiting_issues) >= 1
    assert "local cache" in rate_limiting_issues[0].lower()
```

## Debugging Failed Tests

### **Version Normalization Issues**
```bash
# Test specific version format handling
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_api_versioning_utils.py::TestNormalizeVersion::test_normalize_v_prefix_removed -v -s"

# Test invalid version handling
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_api_versioning_utils.py::TestNormalizeVersion::test_normalize_invalid_version_returns_none -v -s"
```

### **Client Identification Problems**
```bash
# Test priority hierarchy
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_rate_limiting_utils.py::TestGetClientIdentifier -v -s"

# Test specific identification methods
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_rate_limiting_utils.py::TestGetClientIdentifier::test_api_key_header_priority_highest -v -s"
```

### **Configuration Validation Issues**
```bash
# Test all validation scenarios
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_config_validation.py -v -s"

# Test specific validation rule
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_config_validation.py::TestValidateMiddlewareConfiguration::test_rate_limiting_enabled_without_redis_url_warns -v -s"
```

### **Size Limit Resolution Problems**
```bash
# Test hierarchical lookup logic
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_request_size_utils.py::TestGetSizeLimit -v -s"

# Test size formatting
make test-backend PYTEST_ARGS="tests/unit/middleware/test_middlware_request_size_utils.py::TestFormatSize -v -s"
```

## Related Documentation

- **Component Contracts**:
  - `app.core.middleware.api_versioning` - API versioning middleware
  - `app.core.middleware.rate_limiting` - Rate limiting middleware
  - `app.core.middleware.request_size` - Request size limiting middleware
  - `app.core.middleware.security` - Security headers middleware
  - `app.core.middleware.performance_monitoring` - Performance monitoring middleware

- **Infrastructure Contracts**: `backend/contracts/core/middleware/` - Complete interface definitions

- **Unit Testing Philosophy**: `docs/guides/testing/UNIT_TESTS.md` - Comprehensive unit testing methodology

- **Middleware Guide**: `docs/guides/backend/MIDDLEWARE.md` - Middleware architecture and patterns

- **Code Standards**: `docs/guides/developer/CODE_STANDARDS.md` - Development standards and best practices

---

## Utility Function Unit Test Quality Assessment

### **Behavior-Driven Excellence for Pure Functions**
These tests exemplify our **behavior-driven contract testing** approach for middleware utility functions:

✅ **Pure Function Focus**: Utility functions tested in complete isolation without HTTP execution overhead  
✅ **Contract Validation**: Tests verify documented public interfaces for all utility functions  
✅ **Boundary Testing**: Comprehensive edge case coverage including invalid inputs and boundary conditions  
✅ **Observable Outcomes**: Tests verify function return values and error conditions visible to callers  
✅ **Configuration Safety**: Early detection of misconfigurations before runtime deployment  

### **Production-Ready Utility Standards**
✅ **100% Coverage**: Complete test coverage for all utility function logic paths  
✅ **Fast Execution**: < 10ms per test with no external dependencies  
✅ **Clear Documentation**: Each test documents business impact and contract being validated  
✅ **Edge Case Coverage**: Comprehensive validation of boundary conditions and error scenarios  
✅ **Type Safety**: Mock objects properly typed for IDE support and type checking  

### **Architectural Clarity**
✅ **Clear Separation**: Utility function tests separate from full middleware integration tests  
✅ **Modular Design**: Each utility function has focused test suite with clear scope  
✅ **Shared Fixtures**: Common mock infrastructure across all middleware utility tests  
✅ **Consistent Patterns**: Uniform testing approach across all middleware components  

These unit tests serve as a comprehensive model for testing middleware utility functions, demonstrating how to validate pure function behavior with thorough contract coverage, edge case testing, and clear business impact documentation while maintaining fast execution and complete isolation.
