# Middleware Integration Test Plan (FINAL)
## Comprehensive Test Plan for Middleware Integration Testing

**Date**: 2025-01-21
**Version**: 1.0 (Final)
**Scope**: Middleware integration testing for FastAPI backend
**Philosophy**: Test critical seams, execution order, and HTTP-level behavior per TEST_RECS.md
**Status**: Ready for Implementation

---

## Executive Summary

**Critical Insight**: Middleware testing is fundamentally different from other infrastructure testing because:
- Middleware operates at the **ASGI/HTTP boundary** (not business logic)
- **Execution order (LIFO)** is critical and must be validated
- **Side effects** (headers, state, contextvars) are pervasive and must be tested
- **Integration tests are primary** (70-80% of test suite, not unit tests)

**Test Coverage Target**: 70-80% integration tests, 20-30% unit tests (inverse of typical infrastructure)

**Total Seams**: 11 critical integration points
- **P0 (Critical)**: 6 seams - Must implement first
- **P1 (Important)**: 4 seams - Implement second
- **P2 (Nice-to-have)**: 1 seam - Implement if time permits

**Estimated Implementation Effort**:
- P0: ~10-12 hours
- P1: ~6-8 hours
- P2: ~2-3 hours
- **Total**: ~18-23 hours

---

## Consolidation Summary

### Seams from Architectural Analysis (Prompt 1)

This test plan identifies **11 critical integration seams** from architectural analysis of:
- Middleware contracts (`backend/contracts/core/middleware/*.pyi`)
- Middleware implementation (`backend/app/core/middleware/*.py`)
- Main application setup (`backend/app/main.py`)
- Middleware initialization (`backend/app/core/middleware/__init__.py`)

**Analysis Method**:
1. **Application boundary analysis**: HTTP request/response cycle through middleware stack
2. **LIFO execution order analysis**: Middleware registration order and dependencies
3. **Infrastructure abstraction analysis**: Redis integration, settings configuration
4. **Data flow tracking**: Contextvars, request.state, response headers
5. **Contract verification**: Documented behavior in `.pyi` stub files

**Key Architectural Findings**:
- Middleware stack uses LIFO (Last-In-First-Out) execution order
- 10 middleware components with complex dependencies
- Critical contextvars for correlation IDs and timing
- Redis-backed rate limiting with local fallback
- Endpoint-aware security policies (docs vs API)
- Multi-strategy API versioning with internal bypass

### Seam Classification

**SOURCE Distribution**:
- `CONFIRMED`: 11 seams (all identified from contracts and implementation)
- `NEW`: 0 seams (no new seams beyond architectural analysis)

**Priority Distribution**:
- **P0 (Critical)**: 6 seams focusing on security, resilience, and foundational infrastructure
- **P1 (Important)**: 4 seams focusing on observability, performance, and data integrity
- **P2 (Nice-to-have)**: 1 seam focusing on browser compatibility

**Test Scope**:
- Small, dense suite: ~30-40 integration tests total
- Each seam: 3-5 focused scenarios
- Avoids E2E chains spanning too many components
- High-fidelity infrastructure (fakeredis, TestClient)

---

## Deferred/Eliminated Tests

### Appropriately Deferred

**1. Middleware Health Check Endpoint** (`/internal/middleware/health`)
- **Rationale**: Operational tooling, not critical path. Health endpoint can be validated through unit tests of `create_middleware_health_check()` function
- **Components**: `create_middleware_health_check()` → `/internal/middleware/health`
- **Business Impact**: Low - operational visibility, not user-facing
- **When to revisit**: After P0/P1 implementation, if operational monitoring gaps identified

**2. Compression Algorithm Micro-benchmarks**
- **Rationale**: Performance benchmarking of Brotli vs gzip vs deflate is not integration testing. This is better suited for performance tests or eliminated
- **Components**: Compression algorithms (br, gzip, deflate)
- **Business Impact**: Low - algorithm selection based on Accept-Encoding is tested; relative performance is not critical

**3. CORS Preflight Complex Scenarios** (beyond basic preflight)
- **Rationale**: Edge cases like multiple origins, credential handling variations are lower priority unless browser clients explicitly require them
- **Deferred until**: Browser client requirements confirmed
- **Currently in plan as**: P2 with conditional promotion to P1

### Eliminated Tests

**1. Individual Middleware Unit Tests for HTTP Behavior**
- **Rationale**: Middleware behavior is fundamentally about HTTP request/response transformation. Testing individual middleware with mocked `call_next` defeats the purpose. All middleware tests should be integration tests
- **Alternative**: Test helper functions and configuration logic as unit tests; HTTP behavior as integration tests

**2. Middleware Performance Benchmarks**
- **Rationale**: Integration tests verify correctness, not performance. Performance testing is a separate concern
- **Alternative**: Dedicated performance test suite with load testing tools

---

## Critical Integration Seams (Detailed)

### SEAM 1: Complete Middleware Stack Execution Order (LIFO Validation)

**SOURCE**: `CONFIRMED` (from `backend/app/core/middleware/__init__.py:88-103, 577-661`)

**COMPONENTS**:
- `setup_enhanced_middleware()` → All middleware components in LIFO order
- Request flow: CORS → Performance → Logging → Compression → Versioning → Security → Size Limit → Rate Limit
- Response flow: Reverse order

**CRITICAL PATH**: Request → Full middleware stack → Response with all headers and modifications

**TEST SCENARIOS**:
1. **Full stack integration - request processing**:
   - Make request to `/v1/health` endpoint
   - Verify CORS headers appear on response (added last, runs first on response)
   - Verify `X-Request-ID` correlation ID generated by logging middleware
   - Verify `Strict-Transport-Security` and other security headers added
   - Verify `X-Response-Time` header from performance middleware
   - Verify all middleware ran in correct order

2. **Middleware dependencies**:
   - Logging middleware sets `request.state.request_id` BEFORE security middleware logs security events
   - Performance middleware sets `request_start_time_context` BEFORE logging middleware calculates duration
   - Versioning middleware sets `request.state.api_version` for downstream use
   - Verify dependency chain: Logging → Performance → Security → Versioning

3. **Error propagation through stack**:
   - Trigger exception in endpoint handler
   - Verify global exception handler catches exception
   - Verify error response includes CORS headers
   - Verify error response includes security headers
   - Verify request logging captures failed request with correlation ID
   - Verify 500 status with structured error response

**INFRASTRUCTURE NEEDS**: TestClient with full app created via `create_app()`

**BUSINESS VALUE**: Validates core architectural pattern (LIFO execution order). Middleware stack misconfiguration can break all requests or create security vulnerabilities

**INTEGRATION RISK**: **HIGH** - Execution order bugs are subtle and only manifest under integration. Unit tests cannot catch ordering issues

**IMPLEMENTATION NOTES**:
- Use `create_app()` to get full middleware stack
- Single test file: `test_middleware_stack_integration.py`
- Fixture: Reuse `integration_client` from `backend/tests/integration/conftest.py:66-74`
- Test both successful and error paths

**PRIORITY**: **P0** (Critical - Validates core architectural pattern)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (`__init__.py` documents LIFO order)
- [x] Business value articulated (architectural foundation)
- [x] Integration risk assessed (HIGH - order-dependent behavior)
- [x] Infrastructure needs identified (TestClient)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (cannot be unit tested)

---

### SEAM 2: Request Logging → Performance Monitoring Integration (Contextvar Propagation)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/request_logging.pyi:60-79, performance_monitoring.pyi`)

**COMPONENTS**:
- `RequestLoggingMiddleware` (generates correlation IDs via contextvars)
- `PerformanceMonitoringMiddleware` (uses correlation IDs for timing logs)
- Contextvars: `request_id_context`, `request_start_time_context`

**CRITICAL PATH**: Request → Logging sets contextvar → Performance uses contextvar → Response headers

**TEST SCENARIOS**:
1. **Contextvar propagation**:
   - Make request to endpoint
   - Verify `request.state.request_id` is set by logging middleware
   - Verify performance middleware can access correlation ID
   - Verify correlation ID appears in both middleware logs (requires log capture)
   - Verify `X-Request-ID` header in response

2. **Timing coordination**:
   - `request_start_time_context` set by performance middleware
   - Logging middleware reads duration from performance context
   - Response includes `X-Response-Time` header
   - Response includes `X-Memory-Delta` header (if memory monitoring enabled)
   - Verify timing values are reasonable (> 0ms, < request timeout)

3. **Sensitive data redaction in logs** (Security-critical):
   - Make request with `Authorization: Bearer secret-token` header
   - Make request with `x-api-key: secret-key` header
   - Capture logs from logging middleware
   - Verify sensitive headers are redacted/filtered from logs
   - Verify `password`, `token`, `api_key` parameters redacted from query strings

4. **Thread safety and isolation**:
   - Make 10 concurrent requests using `async_integration_client`
   - Verify each request has unique correlation ID
   - Verify no context leakage between concurrent requests
   - Use `asyncio.gather()` to simulate concurrent load

**INFRASTRUCTURE NEEDS**:
- TestClient with full middleware stack
- Async client for concurrent requests (`async_integration_client`)
- Log capture fixture (pytest `caplog`)
- Performance monitoring enabled in settings

**BUSINESS VALUE**: **CRITICAL** - Foundation for distributed tracing and debugging. Without correlation ID propagation, diagnosing middleware failures in production is extremely difficult. Enables correlation of logs across services and request lifecycle tracking

**INTEGRATION RISK**: **HIGH** - Contextvar isolation bugs only appear under concurrent load. Sensitive data leakage is security-critical

**IMPLEMENTATION NOTES**:
- File: `test_logging_performance_integration.py`
- Use `caplog` fixture to capture and verify log output
- Use `async_integration_client` for concurrency tests
- Mock `psutil` if memory monitoring creates flakiness
- Verify contextvar cleanup after request completes

**PRIORITY**: **P0** (Critical - Distributed tracing foundation + security redaction)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (request_logging.pyi:44-47, 100-139)
- [x] Business value articulated (distributed tracing + security)
- [x] Integration risk assessed (HIGH - concurrency + security)
- [x] Infrastructure needs identified (async client, log capture)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (contextvars span middleware)

---

### SEAM 3: Security Middleware → Documentation Endpoints Integration (Endpoint-Aware CSP)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/security.pyi:10-21, 38-39, 74-77`)

**COMPONENTS**:
- `SecurityMiddleware._is_docs_endpoint()` → Endpoint-aware CSP policy
- Documentation endpoints: `/docs`, `/internal/docs`, `/redoc`
- API endpoints: `/v1/*`, `/internal/*` (non-docs)
- CSP policies: Strict for API, relaxed for docs

**CRITICAL PATH**: Request → Security middleware → CSP policy selection → Response headers

**TEST SCENARIOS**:
1. **Endpoint-specific CSP policies**:
   - Request to `/v1/health` → Verify strict CSP: `default-src 'self'`
   - Request to `/v1/text_processing/process` → Verify strict CSP
   - Request to `/docs` → Verify relaxed CSP allowing inline scripts for Swagger UI
   - Request to `/internal/docs` → Verify relaxed CSP
   - Request to `/redoc` → Verify relaxed CSP
   - Verify `Content-Security-Policy` header differs correctly

2. **Security headers consistency across all endpoints**:
   - All endpoints receive base security headers regardless of CSP:
     - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
     - `X-Frame-Options: DENY`
     - `X-Content-Type-Options: nosniff`
     - `X-XSS-Protection: 1; mode=block`
     - `Referrer-Policy: strict-origin-when-cross-origin`
     - `Permissions-Policy: geolocation=(), microphone=(), camera=()`
   - CSP is the only header that varies by endpoint type

3. **Request validation and rejection**:
   - Oversized request (> max_request_size) → 413 Request Entity Too Large
   - Excessive headers (> max_headers_count) → 400 Bad Request
   - Invalid `Content-Length` header → 400 Bad Request
   - Verify error responses still include security headers

4. **Production mode security hardening**:
   - Set `ENVIRONMENT=production` via monkeypatch
   - Create app with production settings
   - Request to `/internal/docs` → Verify 404 (internal docs disabled in production)
   - Verify stricter security headers in production environment
   - Verify Swagger UI still functional at `/docs` with relaxed CSP

**INFRASTRUCTURE NEEDS**:
- TestClient with security middleware enabled
- `production_environment_integration` fixture for production testing
- Monkeypatch for environment variables

**BUSINESS VALUE**: **CRITICAL** - Security headers protect against XSS, clickjacking, and other web vulnerabilities. Endpoint-aware CSP ensures docs remain functional while maintaining strict API security

**INTEGRATION RISK**: **HIGH** - Incorrect CSP breaks Swagger UI; missing headers expose security vulnerabilities

**IMPLEMENTATION NOTES**:
- File: `test_security_middleware_integration.py`
- Test both development and production environments
- Verify Swagger UI loads successfully with relaxed CSP (manual verification or headless browser)
- Use `production_environment_integration` fixture from conftest
- Test request size limits with actual payloads

**PRIORITY**: **P0** (Critical - Security-critical behavior)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (security.pyi:10-21, 38-39, 74-77)
- [x] Business value articulated (web security + docs functionality)
- [x] Integration risk assessed (HIGH - security + usability)
- [x] Infrastructure needs identified (production env fixture)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (HTTP boundary, environment-aware)

---

### SEAM 4: Rate Limiting → Redis/Local Fallback Integration (Resilience + DoS Protection)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/rate_limiting.pyi:55-201, 347-449`)

**COMPONENTS**:
- `RateLimitMiddleware` (orchestrator)
- `RedisRateLimiter` (distributed limiting via Redis)
- `LocalRateLimiter` (in-memory fallback)
- Redis connection (external infrastructure with graceful degradation)
- Endpoint classification logic

**CRITICAL PATH**: Request → Rate limit check → Redis (or fallback to local) → Allow/Deny with headers

**TEST SCENARIOS**:
1. **Distributed limiting with Redis (high-fidelity fake)**:
   - Use `fakeredis` to simulate Redis backend
   - Make 10 requests with same client ID
   - Verify rate limit enforced across requests
   - Verify Redis counters incremented correctly
   - Multiple app instances (separate clients) share rate limit state via Redis

2. **Graceful degradation - Redis failure triggers local fallback**:
   - Start with Redis-backed rate limiter
   - Force Redis connection error (monkeypatch or kill connection)
   - Verify middleware switches to LocalRateLimiter
   - Verify rate limiting continues to function
   - Verify error logged but request not failed
   - Subsequent requests use local limiter until Redis recovers

3. **Per-endpoint classification and limits**:
   - Health endpoints (`/health`, `/healthz`) → Bypass rate limiting (when `rate_limiting_skip_health=True`)
   - Critical endpoints (`/v1/text_processing/process`) → Stricter limits (e.g., 10 req/60s)
   - Auth endpoints (`/v1/auth/*`) → Separate window (e.g., 5 req/300s)
   - Standard endpoints → Default limits (e.g., 100 req/60s)
   - Verify each classification uses correct limits

4. **Client identification hierarchy**:
   - Request with `x-api-key` header → Identified by API key (priority 1)
   - Request with `request.state.user_id` → Identified by user ID (priority 2)
   - Request with `X-Forwarded-For: 192.168.1.100, 10.0.0.1` → First IP used (priority 3)
   - Request with `X-Real-IP: 192.168.1.200` → Real IP used (priority 4)
   - Direct connection → `request.client.host` used (priority 5)
   - Verify different clients have independent rate limits

5. **Rate limit response headers (429 contract completeness)**:
   - Make requests until rate limit exceeded
   - Verify 429 Too Many Requests status
   - Verify response headers present:
     - `X-RateLimit-Limit: 100` (maximum allowed)
     - `X-RateLimit-Remaining: 0` (requests remaining)
     - `X-RateLimit-Window: 60` (window in seconds)
     - `X-RateLimit-Reset: <timestamp>` (when window resets)
     - `X-RateLimit-Rule: standard` (rule applied)
     - `Retry-After: 60` (seconds to wait)
   - Verify response body includes error code `RATE_LIMIT_EXCEEDED`

6. **Rate limit reset after window expires**:
   - Exceed rate limit → 429 response
   - Wait for window to expire (or mock time.time())
   - Make new request → 200 response (limit reset)

**INFRASTRUCTURE NEEDS**:
- `fakeredis` for Redis simulation (reuse `fakeredis_client` from conftest)
- Custom fixture: `client_with_fakeredis_rate_limit` (monkeypatch Redis to fakeredis)
- Custom fixture: `failing_rate_limiter` (force Redis errors)
- Time mocking for window expiration tests (`freezegun` or similar)

**BUSINESS VALUE**: **CRITICAL** - DoS protection and abuse prevention. Rate limiting protects API availability and prevents resource exhaustion. Graceful degradation ensures availability during Redis outages

**INTEGRATION RISK**: **HIGH** - Redis fallback logic only testable via integration. Incorrect client identification can bypass rate limits. Missing headers break client retry logic

**IMPLEMENTATION NOTES**:
- File: `test_rate_limiting_integration.py`
- Use `fakeredis.aioredis.FakeRedis` for high-fidelity Redis simulation
- Monkeypatch `redis.asyncio.Redis.from_url` to return fakeredis instance
- For failure tests, monkeypatch `redis.asyncio.Redis.incr` to raise `ConnectionError`
- Test both Redis and local limiter code paths
- Verify cleanup of local limiter expired entries

**PRIORITY**: **P0** (Critical - DoS protection + resilience)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (rate_limiting.pyi:55-201, 347-449)
- [x] Business value articulated (DoS protection + availability)
- [x] Integration risk assessed (HIGH - resilience + client identification)
- [x] Infrastructure needs identified (fakeredis, fixtures)
- [x] Implementation notes provided (monkeypatch patterns)
- [x] Test scenarios are integration-appropriate (Redis integration + HTTP headers)

---

### SEAM 5: API Versioning → Internal API Bypass Integration (Routing Protection)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/api_versioning.pyi:11-56, 71-203`)

**COMPONENTS**:
- `APIVersioningMiddleware` (version detection and routing)
- Internal API routes (`/internal/*`) with bypass logic
- Public API routes (`/v1/*`, `/v2/*`)
- Version detection strategies: path, header, query, Accept media type
- Version validation and error responses

**CRITICAL PATH**: Request → Internal path check → Bypass OR version detection → Path rewrite → Response headers

**TEST SCENARIOS**:
1. **Internal API bypass (no version rewriting)**:
   - Request to `/internal/resilience/health` → No version detection, no path rewrite
   - Request to `/internal/monitoring/metrics` → Bypass versioning
   - Request to `/internal/cache/stats` → Bypass versioning
   - Verify path remains unchanged (not rewritten to `/v1/internal/...`)
   - Verify `X-API-Version` header NOT added for internal routes
   - Health check endpoints (`/health`, `/healthz`) also bypass versioning

2. **Public API multi-strategy version detection**:
   - **Path-based**: Request to `/v1/health` → Detected version "1.0"
   - **Header-based**: Request to `/health` with `X-API-Version: 1.0` → Version "1.0"
   - **Query-based**: Request to `/health?version=1.0` → Version "1.0"
   - **Accept-based**: Request to `/health` with `Accept: application/vnd.api+json;version=1.0` → Version "1.0"
   - Verify detection method stored in `request.state.api_version_detection_method`
   - Verify priority: path > header > query > Accept > default

3. **Version validation and error responses**:
   - Supported version (1.0) → Request proceeds normally
   - Unsupported version (5.0) → 400 Bad Request
   - Verify error response includes:
     - `X-API-Supported-Versions: 1.0, 2.0` header
     - `X-API-Current-Version: 2.0` header
     - Structured JSON error with `error_code: API_VERSION_NOT_SUPPORTED`
     - Error message indicating requested vs supported versions

4. **Version information in response headers (all responses)**:
   - All public API responses include:
     - `X-API-Version: 1.0` (version used for request)
     - `X-API-Version-Detection: path` (detection method)
     - `X-API-Supported-Versions: 1.0, 2.0`
     - `X-API-Current-Version: 2.0`
   - Deprecated versions also include:
     - `Deprecation: true`
     - `Sunset: <date>` (if configured)
     - `Link: <migration-docs-url>` (if configured)

5. **Path rewriting for versioned routing**:
   - Request to `/users` with `X-API-Version: 1.0` → Path rewritten to `/v1/users`
   - Verify router receives rewritten path
   - Verify request.state.api_version = "1.0"

**INFRASTRUCTURE NEEDS**:
- TestClient with versioning middleware enabled
- Mock or real endpoints at different version paths
- Settings with version configuration (supported versions, deprecation dates)

**BUSINESS VALUE**: **CRITICAL** - API versioning enables backward compatibility and gradual migration. Internal bypass prevents accidental version pollution of admin endpoints. Clear version headers guide client migration

**INTEGRATION RISK**: **MEDIUM-HIGH** - Incorrect bypass breaks internal endpoints; missing version headers confuse clients; path rewriting bugs break routing

**IMPLEMENTATION NOTES**:
- File: `test_api_versioning_integration.py`
- Configure settings with: `api_versioning_enabled=True`, `default_api_version="1.0"`, `supported_versions=["1.0", "2.0"]`
- Test all detection strategies explicitly
- Verify internal routes use exact path matching (not startswith pattern)
- Mock deprecation configuration for deprecated version tests

**PRIORITY**: **P0** (Critical - API evolution + internal API protection)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (api_versioning.pyi:11-56, 71-203)
- [x] Business value articulated (backward compatibility + routing)
- [x] Integration risk assessed (MEDIUM-HIGH - routing logic)
- [x] Infrastructure needs identified (TestClient, version config)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (HTTP routing + headers)

---

### SEAM 6: Global Exception Handler → All Middleware Integration (Error Handling)

**SOURCE**: `CONFIRMED` (from `backend/app/core/middleware/global_exception_handler.py`, `__init__.py:567, 654`)

**COMPONENTS**:
- `setup_global_exception_handler()` (exception handler registration)
- All middleware components (potential exception sources)
- Custom exceptions: `ValidationError`, `RateLimitError`, `ConfigurationError`, `InfrastructureError`
- Exception-to-HTTP-status mapping logic

**CRITICAL PATH**: Exception anywhere in middleware stack → Global handler → Structured error response with headers

**TEST SCENARIOS**:
1. **Exception handling across middleware layers**:
   - Trigger exception in security middleware (e.g., invalid config) → 500 response
   - Trigger exception in rate limiting middleware → 500 response (or fallback)
   - Trigger exception in compression middleware → 500 response
   - Trigger exception in endpoint handler → Caught and formatted
   - Verify all exceptions return structured JSON error response

2. **Error response includes security and CORS headers**:
   - Trigger any exception
   - Verify error response includes:
     - CORS headers (if CORS middleware ran)
     - Security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.)
     - `X-Request-ID` correlation header (from logging middleware)
   - Verify headers applied AFTER exception handling (response phase)

3. **Custom exception mapping to HTTP status codes**:
   - `ValidationError` → 422 Unprocessable Entity
   - `RateLimitError` → 429 Too Many Requests
   - `ConfigurationError` → 500 Internal Server Error
   - `InfrastructureError` → 500 Internal Server Error
   - Generic `Exception` → 500 with sanitized message
   - Verify correct status code and error structure

4. **Error response structure and information disclosure**:
   - Verify error response contains:
     - `error_code`: Machine-readable error code (e.g., "VALIDATION_ERROR")
     - `message`: Human-readable error message
     - `detail`: Additional context (only if not sensitive)
     - `request_id`: Correlation ID for debugging
   - Verify sensitive information NOT disclosed:
     - No stack traces in production
     - No internal paths or implementation details
     - No database connection strings or credentials

5. **Error logging with correlation**:
   - Trigger exception in endpoint
   - Verify exception logged with correlation ID from request logging
   - Verify log includes request method, path, and error details
   - Use `caplog` to capture and verify log output

**INFRASTRUCTURE NEEDS**:
- TestClient with full middleware stack
- Log capture (`caplog` fixture)
- Mock endpoints that raise various exception types
- Production environment fixture for information disclosure testing

**BUSINESS VALUE**: **CRITICAL** - Consistent error handling prevents information disclosure and provides debuggable errors. Correlation IDs enable incident investigation. Proper HTTP status codes guide client retry logic

**INTEGRATION RISK**: **HIGH** - Missing headers on error responses break CORS or security; information disclosure creates security vulnerabilities; incorrect status codes confuse clients

**IMPLEMENTATION NOTES**:
- File: `test_global_exception_handler_integration.py`
- Create test endpoints that raise specific exception types
- Use `monkeypatch.setenv("ENVIRONMENT", "production")` for disclosure tests
- Verify exception handler is last in chain (catches all middleware exceptions)
- Test both custom exceptions and generic exceptions

**PRIORITY**: **P0** (Critical - Error handling security + consistency)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (global_exception_handler.py, __init__.py)
- [x] Business value articulated (security + debuggability)
- [x] Integration risk assessed (HIGH - security + consistency)
- [x] Infrastructure needs identified (TestClient, log capture)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (exception propagation across middleware)

---

### SEAM 7: Compression Middleware → Content-Type/Size Integration (Performance Optimization)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/compression.pyi:1-57, 73-167`)

**COMPONENTS**:
- `CompressionMiddleware` (orchestrator)
- Content-type detection logic (compressible vs incompressible)
- Size threshold logic (default 1KB minimum)
- Algorithm selection: Brotli → gzip → deflate (based on Accept-Encoding)
- Request decompression logic

**CRITICAL PATH**: Response → Size check → Content-type check → Algorithm negotiation → Compression → Headers

**TEST SCENARIOS**:
1. **Content-aware compression decisions**:
   - JSON response > 1KB → Compressed with selected algorithm
   - JSON response < 1KB → NOT compressed (below threshold)
   - Image response (`image/png`) → NOT compressed (already compressed)
   - Archive response (`application/zip`) → NOT compressed
   - Text response (`text/plain`) → Compressed if > 1KB
   - Verify `Content-Encoding` header only present when compressed

2. **Algorithm negotiation based on Accept-Encoding**:
   - Client sends `Accept-Encoding: br` → Brotli compression used
   - Client sends `Accept-Encoding: gzip` → gzip compression used
   - Client sends `Accept-Encoding: deflate` → deflate compression used
   - Client sends `Accept-Encoding: br, gzip` → Brotli preferred
   - Client sends no `Accept-Encoding` → No compression
   - Verify `Content-Encoding` header matches algorithm used

3. **Compression headers and metadata**:
   - Compressed response includes:
     - `Content-Encoding: gzip` (or br/deflate)
     - `Content-Length: <compressed_size>` (updated to compressed size)
     - `X-Original-Size: <original_size>` (original uncompressed size)
     - `X-Compression-Ratio: 0.65` (compression efficiency as decimal)
   - Verify header values are accurate

4. **Request decompression**:
   - Send POST request with compressed body
   - Include `Content-Encoding: gzip` header
   - Verify middleware decompresses body before passing to endpoint
   - Endpoint receives uncompressed data
   - Verify `Content-Length` updated after decompression

5. **Invalid compressed data handling**:
   - Send POST request with `Content-Encoding: gzip` but invalid gzip data
   - Verify middleware returns 400 Bad Request
   - Verify structured error response with clear message

**INFRASTRUCTURE NEEDS**:
- TestClient with compression middleware enabled
- Response generators of various sizes (< 1KB and > 1KB)
- Various content types (JSON, images, text, archives)
- Compression libraries (brotli, gzip, zlib) for creating compressed request bodies

**BUSINESS VALUE**: **MEDIUM** - Bandwidth optimization for clients. Reduces data transfer costs and improves performance for slow connections. Not security-critical but improves user experience

**INTEGRATION RISK**: **MEDIUM** - Incorrect Content-Length breaks HTTP clients; missing compression for large payloads wastes bandwidth; over-compression of images/archives wastes CPU

**IMPLEMENTATION NOTES**:
- File: `test_compression_integration.py`
- Generate test responses with controlled sizes
- Use `gzip.compress()`, `brotli.compress()` for request body testing
- Verify compression only applied when beneficial (size reduction achieved)
- Skip payload integrity verification (that's better for unit tests of compression logic)
- Focus on HTTP headers and content-type decisions (integration boundary)

**PRIORITY**: **P1** (Important - Performance optimization, not critical path)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (compression.pyi:1-57, 73-167)
- [x] Business value articulated (bandwidth optimization)
- [x] Integration risk assessed (MEDIUM - HTTP semantics)
- [x] Infrastructure needs identified (TestClient, compression libs)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (HTTP negotiation + headers)

---

### SEAM 8: Request Size Limiting → DoS Protection Integration (Streaming Validation)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/request_size.pyi` - contract file existence inferred)

**COMPONENTS**:
- `RequestSizeLimitMiddleware` (streaming size validation)
- Per-content-type size limits (JSON: 5MB, multipart: 50MB, default: 10MB)
- Global size limit enforcement
- Streaming validation to prevent memory exhaustion

**CRITICAL PATH**: Request → Content-Type detection → Size limit selection → Stream validation → Allow/Deny

**TEST SCENARIOS**:
1. **Per-content-type limits enforcement**:
   - POST with `Content-Type: application/json` and 6MB body → 413 Request Entity Too Large
   - POST with `Content-Type: application/json` and 4MB body → 200 OK (within 5MB limit)
   - POST with `Content-Type: multipart/form-data` and 60MB body → 413
   - POST with `Content-Type: multipart/form-data` and 40MB body → 200 OK (within 50MB limit)
   - POST with `Content-Type: text/plain` and 11MB body → 413 (default 10MB limit)

2. **Streaming enforcement prevents memory exhaustion**:
   - Send large request (> limit) with chunked transfer encoding
   - Verify middleware rejects request during streaming (not after full read)
   - Verify middleware does not buffer entire request in memory
   - Monitor memory usage during large request handling

3. **Error responses for oversized requests**:
   - Send request exceeding limit
   - Verify 413 Request Entity Too Large status
   - Verify error response includes:
     - Clear message: "Request body exceeds maximum allowed size"
     - Maximum allowed size in error detail
     - Structured JSON error format
   - Verify security headers still present on error response

4. **Content-Length header validation**:
   - Request with `Content-Length: 20000000` (20MB) → Rejected before body read
   - Request with `Content-Length: 5000000` (5MB) for JSON → Rejected (exceeds JSON limit)
   - Verify early rejection based on Content-Length header

**INFRASTRUCTURE NEEDS**:
- TestClient with request size limiting enabled
- Large payload generators (use generators to avoid memory issues)
- Various content types
- Settings with per-content-type limits configured

**BUSINESS VALUE**: **MEDIUM** - DoS protection against large payload attacks. Prevents memory exhaustion and resource starvation. Less critical than rate limiting but important for resilience

**INTEGRATION RISK**: **MEDIUM** - Streaming validation only testable via HTTP. Incorrect limits break legitimate uploads (e.g., file uploads)

**IMPLEMENTATION NOTES**:
- File: `test_request_size_limiting_integration.py`
- Use generators to create large payloads without consuming memory:
  ```python
  def large_payload(size_mb):
      chunk = b"x" * 1024  # 1KB chunk
      for _ in range(size_mb * 1024):
          yield chunk
  ```
- Test both Content-Length early rejection and streaming enforcement
- Verify middleware doesn't buffer entire request

**PRIORITY**: **P1** (Important - DoS protection, not critical as rate limiting)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (inferred from middleware implementation)
- [x] Business value articulated (DoS protection)
- [x] Integration risk assessed (MEDIUM - streaming behavior)
- [x] Infrastructure needs identified (TestClient, generators)
- [x] Implementation notes provided (generator pattern)
- [x] Test scenarios are integration-appropriate (streaming + HTTP)

---

### SEAM 9: Logging Middleware → Sensitive Data Redaction Integration (Security)

**SOURCE**: `CONFIRMED` (from `backend/contracts/core/middleware/request_logging.pyi:6-8, 44-47`)

**COMPONENTS**:
- `RequestLoggingMiddleware` (log generation and filtering)
- Sensitive header filtering logic
- Query parameter redaction
- Log output (captured via `caplog`)

**CRITICAL PATH**: Request with sensitive data → Logging middleware → Redaction → Log output

**TEST SCENARIOS**:
1. **Sensitive header redaction**:
   - Request with `Authorization: Bearer secret-token` → Header redacted in logs
   - Request with `x-api-key: sk-1234567890` → Header redacted in logs
   - Request with `Cookie: session=abcd1234` → Header redacted in logs
   - Capture logs and verify sensitive values NOT present in log output
   - Verify header names present but values show as `***REDACTED***` or similar

2. **Query parameter redaction**:
   - Request to `/endpoint?password=secret123&user=john` → Password redacted
   - Request to `/endpoint?api_key=sk-1234&page=1` → api_key redacted, page visible
   - Request to `/endpoint?token=abc123` → Token redacted
   - Verify sensitive query params filtered from logged URLs

3. **Request body redaction (if enabled)**:
   - POST with JSON body containing `{"password": "secret", "username": "john"}`
   - Verify password field redacted in logs if `log_request_bodies=True`
   - Verify other fields visible

4. **Non-sensitive data preserved**:
   - Request with `User-Agent`, `Accept`, `Content-Type` headers → All logged
   - Request with normal query params → All logged
   - Verify legitimate debugging information preserved

**INFRASTRUCTURE NEEDS**:
- TestClient with logging middleware enabled
- Log capture fixture (`caplog`)
- Settings with `request_logging_enabled=True`, `log_sensitive_data=False`

**BUSINESS VALUE**: **HIGH** - Security compliance and secret protection. Prevents credential leakage in logs. Required for PCI DSS, GDPR, and security audits

**INTEGRATION RISK**: **HIGH** - Logging without redaction creates security vulnerabilities and compliance violations

**IMPLEMENTATION NOTES**:
- File: `test_logging_redaction_integration.py`
- Use pytest `caplog` fixture to capture log records
- Verify redaction in captured log text, not just log level
- Test with various sensitive header names and query params
- Ensure redaction doesn't break correlation ID logging

**PRIORITY**: **P1** (Important - Security compliance)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (request_logging.pyi:6-8, 44-47)
- [x] Business value articulated (security compliance)
- [x] Integration risk assessed (HIGH - security vulnerability if missing)
- [x] Infrastructure needs identified (caplog)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (log output verification)

---

### SEAM 10: Middleware Configuration → Settings Integration (Feature Toggles)

**SOURCE**: `CONFIRMED` (from `backend/app/core/middleware/__init__.py:448-574, 939-981`)

**COMPONENTS**:
- `Settings` configuration object (`app.core.config.Settings`)
- All middleware components (read settings during initialization)
- `validate_middleware_configuration()` (configuration validation)
- Feature toggle flags: `security_headers_enabled`, `rate_limiting_enabled`, `compression_enabled`, etc.
- `setup_middleware()` and `setup_enhanced_middleware()` functions

**CRITICAL PATH**: Settings → Middleware initialization → Feature toggles applied → Middleware behavior

**TEST SCENARIOS**:
1. **Configuration validation detects issues**:
   - Invalid compression level (10) → Validation warning
   - Missing Redis URL with rate limiting enabled → Validation warning
   - Invalid version configuration → Validation warning
   - Call `validate_middleware_configuration(settings)` and verify warnings returned

2. **Feature toggle disables middleware**:
   - `security_headers_enabled=False` → No security headers in response
   - `rate_limiting_enabled=False` → No rate limiting applied (unlimited requests)
   - `compression_enabled=False` → No compression headers in response
   - `request_logging_enabled=False` → No request logging (verify via caplog)
   - Create app with disabled features and verify behavior change

3. **Middleware not added when disabled**:
   - Disable security middleware via settings
   - Verify `get_middleware_stats(app)` shows middleware not in stack
   - Verify security headers absent from response
   - Confirm middleware truly not registered, not just disabled

4. **Environment-specific configuration**:
   - Production: All security features enabled, logging minimal
   - Development: Some security relaxed, verbose logging
   - Test: Isolated configuration, specific features disabled for testing
   - Use `monkeypatch` to set `ENVIRONMENT` variable before app creation

5. **Settings propagation to all middleware**:
   - Set custom `slow_request_threshold` in settings
   - Verify performance middleware uses custom threshold
   - Set custom rate limit rules in settings
   - Verify rate limit middleware applies custom rules
   - Verify settings flow from config → middleware initialization

**INFRASTRUCTURE NEEDS**:
- `create_settings()` and `create_app(settings_obj=...)` pattern
- Monkeypatch for environment variables
- Multiple app instances with different configurations
- `get_middleware_stats()` utility function

**BUSINESS VALUE**: **HIGH** - Configuration flexibility enables environment-specific behavior. Feature toggles allow gradual rollout and quick disable of problematic features. Validation prevents misconfigurations

**INTEGRATION RISK**: **MEDIUM-HIGH** - Configuration errors can disable security features or break functionality. Must test via app creation, not just middleware constructors

**IMPLEMENTATION NOTES**:
- File: `test_middleware_configuration_integration.py`
- Use `create_settings()` to create custom settings instances
- Pass settings to `create_app(settings_obj=custom_settings)`
- Test that middleware initialization respects settings
- Verify behavior changes via HTTP requests, not just middleware presence
- Use `get_middleware_stats()` to verify middleware registration

**PRIORITY**: **P1** (Important - Configuration errors disable security)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (__init__.py:448-574, 939-981)
- [x] Business value articulated (configuration flexibility + validation)
- [x] Integration risk assessed (MEDIUM-HIGH - security feature toggles)
- [x] Infrastructure needs identified (create_app pattern)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (app-level configuration)

---

### SEAM 11: CORS Middleware → Preflight Request Integration (Browser Compatibility)

**SOURCE**: `CONFIRMED` (from `backend/app/core/middleware/cors.py`, `__init__.py:571, 659`)

**COMPONENTS**:
- `setup_cors_middleware()` (CORS configuration from Starlette)
- Preflight OPTIONS requests
- Allowed origins configuration
- CORS headers: `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, etc.

**CRITICAL PATH**: OPTIONS preflight request → CORS middleware → Preflight response with headers

**TEST SCENARIOS**:
1. **Preflight request handling**:
   - Send OPTIONS request to `/v1/health`
   - Include `Origin: https://example.com` header
   - Include `Access-Control-Request-Method: POST` header
   - Verify response includes:
     - `Access-Control-Allow-Origin: https://example.com` (if allowed)
     - `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
     - `Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key`
     - `Access-Control-Max-Age: 86400` (preflight cache duration)

2. **Origin validation**:
   - Request from allowed origin → CORS headers include origin
   - Request from disallowed origin → No `Access-Control-Allow-Origin` or blocked
   - Request with `Origin: *` (wildcard configured) → Wildcard in response
   - Verify origin matching logic

3. **Credentials handling**:
   - CORS configured with `allow_credentials=True`
   - Verify `Access-Control-Allow-Credentials: true` header present
   - Verify credentials handling respects security policies

4. **CORS headers on actual requests (not just preflight)**:
   - Make actual POST request with `Origin` header
   - Verify response includes `Access-Control-Allow-Origin`
   - Verify CORS headers applied to both preflight and actual requests

**INFRASTRUCTURE NEEDS**:
- TestClient with CORS middleware enabled
- Settings with `allowed_origins` configured
- OPTIONS request testing

**BUSINESS VALUE**: **MEDIUM** - Enables browser-based clients to consume API. Required for web applications making cross-origin requests. Not critical if no browser clients

**INTEGRATION RISK**: **LOW-MEDIUM** - CORS misconfiguration blocks legitimate browser clients but doesn't affect non-browser clients

**IMPLEMENTATION NOTES**:
- File: `test_cors_middleware_integration.py`
- Test with various Origin headers
- Verify preflight response status (usually 200 OK)
- Test both allowed and disallowed origins
- **Conditional Priority**: If browser clients confirmed → raise to P1

**PRIORITY**: **P2** (Nice-to-have - Conditional promotion to P1 if browser requirement confirmed)

**VALIDATION CHECKLIST**:
- [x] Contract source verified (cors.py, __init__.py:571, 659)
- [x] Business value articulated (browser client support)
- [x] Integration risk assessed (LOW-MEDIUM - client compatibility)
- [x] Infrastructure needs identified (TestClient, OPTIONS requests)
- [x] Implementation notes provided
- [x] Test scenarios are integration-appropriate (HTTP preflight)

---

## Infrastructure Requirements

### Required Test Fixtures

#### Existing Fixtures to Reuse

From `backend/tests/integration/conftest.py`:

**1. `fakeredis_client` (lines 229-262)**
```python
@pytest.fixture(scope="function")
async def fakeredis_client():
    """Provides high-fidelity Redis fake for rate limiting/cache tests."""
    # Share across multiple app instances to simulate distributed counters
```
**Use for**: SEAM 4 (Rate Limiting) - Simulate distributed Redis backend

**2. `integration_client` (lines 66-74)**
```python
@pytest.fixture
def integration_client():
    """TestClient with fresh app; production-like env via autouse fixture."""
```
**Use for**: Most integration tests requiring full middleware stack

**3. `async_integration_client` (lines 77-89)**
```python
@pytest.fixture
async def async_integration_client():
    """Async HTTP client; useful for concurrency testing."""
```
**Use for**: SEAM 2 (Logging/Performance concurrency tests)

**4. `authenticated_headers` (lines 92-97)**
```python
@pytest.fixture
def authenticated_headers():
    """Valid API key headers."""
```
**Use for**: Tests requiring authentication

**5. `production_environment_integration` (lines 36-51)**
```python
@pytest.fixture
def production_environment_integration(monkeypatch):
    """Production env setup via monkeypatch before app creation."""
```
**Use for**: SEAM 3 (Security production mode), SEAM 10 (Configuration)

**6. `performance_monitor` (backend/tests/integration/text_processor/conftest.py:604-650)**
```python
@pytest.fixture
def performance_monitor():
    """Simple timing utility helpful for metrics checks."""
```
**Use for**: SEAM 2 (Performance monitoring validation)

#### New Fixtures Needed

**1. `client_minimal_middleware` (New - for isolation testing)**
```python
@pytest.fixture
def client_minimal_middleware():
    """
    TestClient with selective middleware disabled.

    Use to isolate specific middleware behavior by disabling others.
    """
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.core.config import create_settings

    settings = create_settings()
    settings.rate_limiting_enabled = False
    settings.compression_enabled = False
    settings.performance_monitoring_enabled = True
    settings.request_logging_enabled = True
    app = create_app(settings_obj=settings)
    return TestClient(app)
```
**Use for**: SEAM 10 (Configuration toggles)

**2. `client_with_fakeredis_rate_limit` (New - for rate limiting tests)**
```python
@pytest.fixture
def client_with_fakeredis_rate_limit(monkeypatch):
    """
    TestClient with Redis-backed rate limiting using fakeredis.

    Simulates distributed rate limiting without real Redis.
    """
    import fakeredis.aioredis as fredis
    import redis.asyncio as redis
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.core.config import create_settings

    # Redirect Redis.from_url to fakeredis instance
    fake = fredis.FakeRedis(decode_responses=False)
    monkeypatch.setattr(redis.Redis, 'from_url', lambda url, **kw: fake)

    settings = create_settings()
    settings.rate_limiting_enabled = True
    settings.redis_url = 'redis://localhost:6379'
    app = create_app(settings_obj=settings)
    return TestClient(app)
```
**Use for**: SEAM 4 (Rate Limiting with Redis)

**3. `failing_redis_connection` (New - for resilience testing)**
```python
@pytest.fixture
def failing_redis_connection(monkeypatch):
    """
    Force Redis connection errors to validate local fallback.

    Simulates Redis outage for graceful degradation testing.
    """
    def _raise_connection_error(*args, **kwargs):
        raise ConnectionError('Simulated Redis failure')

    monkeypatch.setattr('redis.asyncio.Redis.incr', _raise_connection_error, raising=True)
    monkeypatch.setattr('redis.asyncio.Redis.get', _raise_connection_error, raising=True)
    return True  # Fixture marker
```
**Use for**: SEAM 4 (Rate Limiting fallback testing)

**4. `large_payload_generator` (New - for size limit testing)**
```python
@pytest.fixture
def large_payload_generator():
    """
    Generate large payloads without consuming memory.

    Returns function that yields chunks for streaming tests.
    """
    def generator(size_mb: int):
        chunk = b"x" * 1024  # 1KB chunk
        for _ in range(size_mb * 1024):
            yield chunk
    return generator
```
**Use for**: SEAM 8 (Request Size Limiting)

---

### Test Data Requirements

**1. Various Response Sizes**:
- Small responses (< 1KB) for compression threshold testing
- Large responses (> 1KB) for compression activation
- Very large responses (> 10MB) for size limit testing

**2. Multiple Content Types**:
- `application/json` (compressible)
- `text/plain` (compressible)
- `image/png` (incompressible)
- `application/zip` (incompressible)
- `multipart/form-data` (for upload testing)

**3. Concurrent Request Patterns**:
- 10+ concurrent requests for correlation ID isolation
- Rate limit exhaustion patterns (sequential requests)
- Load testing patterns for performance validation

**4. Sensitive Data Samples**:
- API keys: `x-api-key: sk-1234567890`
- Bearer tokens: `Authorization: Bearer abc123def456`
- Passwords in query params: `?password=secret123`
- Session cookies: `Cookie: session=abcd1234`

---

### External Dependencies

**1. fakeredis** (v2.10.0+)
- High-fidelity Redis fake for rate limiting tests
- Already in test dependencies: `backend/pyproject.toml:75`

**2. pytest-asyncio** (v1.0.0+)
- Async test support for concurrent requests
- Already in test dependencies: `backend/pyproject.toml:70`

**3. pytest fixtures from conftest**
- Monkeypatch for environment variables
- Caplog for log capture
- TestClient for HTTP testing

**4. No additional external dependencies required**
- All middleware infrastructure uses stdlib or existing dependencies

---

## Testing Approach Summary

### Integration Test Dominance (70-80% of test suite)

**Test through HTTP using TestClient**:
- All tests make real HTTP requests
- Verify headers, status codes, response bodies
- Test observable behavior at application boundary
- No mocking of middleware internals

**Test middleware execution order explicitly**:
- Verify LIFO pattern (Last-In-First-Out)
- Validate dependencies between middleware
- Test cumulative effects of middleware stack

**Test side effects**:
- Contextvars propagation between middleware
- `request.state` population
- Response header injection
- Log output (captured via caplog)

### Unit Test Minimalism (20-30% of test suite)

**Unit tests are ONLY for**:
- Configuration validation logic (`validate_middleware_configuration()`)
- Helper functions (`_is_docs_endpoint()`, `get_client_identifier()`)
- Pure functions without HTTP context
- Algorithm selection logic (not HTTP negotiation)

### Anti-patterns to Avoid

❌ **Over-mocking middleware components**
```python
# BAD: Defeats purpose of integration testing
def test_security_with_mocks(mocker):
    mock_call_next = mocker.Mock(return_value=Response())
    middleware = SecurityMiddleware(mock_app, settings)
    # This doesn't test actual HTTP behavior
```

❌ **Testing internal implementation details**
```python
# BAD: Testing internals instead of observable behavior
def test_middleware_internal_state():
    middleware = SecurityMiddleware(mock_app, settings)
    assert middleware._internal_counter == 0  # Don't do this
```

❌ **Ignoring middleware execution order**
```python
# BAD: Testing middleware in isolation when order matters
def test_security_middleware_alone():
    # Misses the fact that logging must run before security
    pass
```

❌ **Testing from inside-out instead of boundary**
```python
# BAD: Calling internal methods directly
def test_internal_method():
    middleware._process_headers(request)  # Don't do this

# GOOD: Test through HTTP boundary
def test_security_headers(client):
    response = client.get("/v1/health")
    assert "X-Frame-Options" in response.headers
```

---

## Critical Testing Considerations

### ⚠️ pytest-randomly Interaction with Middleware Testing

**Configuration**: The project uses `pytest-randomly = "^3.12.0"` (backend/pyproject.toml:78) which **automatically randomizes test execution order by default**.

**Impact on Middleware Tests**:

1. **GOOD NEWS**: Test randomization is EXCELLENT for middleware testing
   - Exposes hidden dependencies between tests
   - Validates that middleware setup is truly isolated per test
   - Ensures no test pollution from shared state
   - Catches bugs where test order accidentally makes tests pass

2. **NOT A PROBLEM for middleware execution order**:
   - `pytest-randomly` randomizes **TEST execution order** (which tests run first)
   - It does NOT affect **middleware execution order** (LIFO pattern within a single request)
   - Each test creates a fresh app via `create_app()` → middleware order is consistent

3. **What we ARE testing**: Middleware LIFO order within a single HTTP request
   - Request flows through: CORS → Performance → Logging → ... → Endpoint
   - Response flows through: Endpoint → ... → Logging → Performance → CORS
   - This order is deterministic and controlled by middleware registration order

4. **What pytest-randomly DOES randomize**: Which integration test runs first
   - Test A (checks CORS headers) might run before Test B (checks security headers)
   - Test B might run before Test A on next run
   - This is DESIRABLE - tests should pass regardless of run order

**Best Practices**:
- ✅ Use `create_app()` factory pattern in every test for isolation
- ✅ Embrace randomization - it improves test quality
- ✅ If a test fails only when run in certain order → FIX THE TEST (it has hidden dependencies)
- ✅ Use `pytest --randomly-dont-shuffle` ONLY for debugging specific order-dependent failures
- ❌ Never disable `pytest-randomly` permanently - it catches real bugs

**Special Case: Concurrent Request Tests**
```python
# This tests middleware behavior under concurrent load
# The REQUEST processing order is deterministic (LIFO)
# The TEST execution order is randomized (pytest-randomly)
async def test_concurrent_requests_maintain_isolation(client):
    """Test that concurrent requests maintain separate correlation IDs."""
    # Each request processes through middleware in same LIFO order
    # But each request has isolated state (contextvars)
    responses = await asyncio.gather(*[
        client.get("/v1/health") for _ in range(10)
    ])
    # All 10 requests went through middleware in same order
    # But pytest-randomly might run this test before or after other tests
```

**Debugging Order-Dependent Failures**:
```bash
# If a middleware test fails randomly:
# 1. Check test uses create_app() for isolation
# 2. Check test doesn't rely on previous test's state
# 3. Run with fixed seed to reproduce
pytest --randomly-seed=12345

# 4. Disable randomization temporarily to debug
pytest --randomly-dont-shuffle

# 5. Once fixed, re-enable randomization
pytest  # Default includes --randomly
```

**Summary**: `pytest-randomly` is a FEATURE, not a bug. It ensures middleware tests are truly isolated and don't accidentally pass due to test execution order. The middleware LIFO execution order is deterministic within each request and unaffected by pytest's test randomization.

---

## Implementation Plan

### Phase 1: P0 - Critical Seams (Must Have)

**Estimated Effort**: ~10-12 hours

**Implementation Order** (by dependency and foundation):

1. **SEAM 1**: Complete Middleware Stack Execution Order (~2 hours)
   - Foundation for all other tests
   - Validates LIFO pattern
   - File: `test_middleware_stack_integration.py`

2. **SEAM 6**: Global Exception Handler Integration (~1.5 hours)
   - Cross-cutting concern affecting all middleware
   - Must work before testing individual middleware error cases
   - File: `test_global_exception_handler_integration.py`

3. **SEAM 2**: Request Logging → Performance Monitoring (~2 hours)
   - Foundation for observability across all other tests
   - Correlation IDs used in debugging other seams
   - File: `test_logging_performance_integration.py`

4. **SEAM 3**: Security → Documentation Endpoints (~2 hours)
   - Security-critical, must validate early
   - Tests environment-aware behavior
   - File: `test_security_middleware_integration.py`

5. **SEAM 4**: Rate Limiting → Redis/Local Fallback (~3 hours)
   - Most complex P0 seam (Redis integration, fallback logic)
   - DoS protection critical for production
   - File: `test_rate_limiting_integration.py`

6. **SEAM 5**: API Versioning → Internal API Bypass (~1.5 hours)
   - Routing protection for internal APIs
   - Multi-strategy version detection
   - File: `test_api_versioning_integration.py`

### Phase 2: P1 - Important Seams (Should Have)

**Estimated Effort**: ~6-8 hours

**Implementation Order**:

7. **SEAM 10**: Middleware Configuration → Settings (~1.5 hours)
   - Configuration flexibility and validation
   - File: `test_middleware_configuration_integration.py`

8. **SEAM 9**: Logging → Sensitive Data Redaction (~2 hours)
   - Security compliance
   - File: `test_logging_redaction_integration.py`

9. **SEAM 7**: Compression → Content-Type/Size (~2 hours)
   - Performance optimization
   - File: `test_compression_integration.py`

10. **SEAM 8**: Request Size Limiting (~1.5 hours)
    - DoS protection (secondary to rate limiting)
    - File: `test_request_size_limiting_integration.py`

### Phase 3: P2 - Nice-to-Have (Could Have)

**Estimated Effort**: ~2-3 hours

11. **SEAM 11**: CORS → Preflight Requests (~2 hours)
    - Browser compatibility
    - Promote to P1 if browser clients confirmed
    - File: `test_cors_middleware_integration.py`

### Total Implementation Effort

- **P0**: ~10-12 hours (6 seams)
- **P1**: ~6-8 hours (4 seams)
- **P2**: ~2-3 hours (1 seam)
- **Total**: ~18-23 hours for complete test suite

### Parallel Implementation Opportunities

**Can implement in parallel** (independent seams):
- SEAM 3 (Security) and SEAM 5 (Versioning) - No shared fixtures
- SEAM 7 (Compression) and SEAM 8 (Request Size) - Similar patterns
- SEAM 9 (Logging Redaction) and SEAM 10 (Configuration) - Different concerns

**Must implement sequentially** (dependent seams):
- SEAM 1 → All others (foundation)
- SEAM 2 → SEAM 9 (logging redaction depends on logging integration)
- SEAM 6 → All others (exception handling must work first)

---

## Test Execution Strategy

### Running Integration Tests

**Full middleware integration test suite**:
```bash
# From backend/ directory
pytest tests/integration/middleware/ -v

# With coverage
pytest tests/integration/middleware/ --cov=app.core.middleware --cov-report=term-missing
```

**Run specific seams**:
```bash
# SEAM 1: Stack execution order
pytest tests/integration/middleware/test_middleware_stack_integration.py -v

# SEAM 4: Rate limiting
pytest tests/integration/middleware/test_rate_limiting_integration.py -v
```

**Run with test randomization**:
```bash
# Default (randomization enabled)
pytest tests/integration/middleware/ -v

# Fixed seed for reproducibility
pytest tests/integration/middleware/ --randomly-seed=12345

# Disable randomization for debugging
pytest tests/integration/middleware/ --randomly-dont-shuffle
```

**Parallel execution**:
```bash
# Parallel execution with xdist (default in pytest.ini)
pytest tests/integration/middleware/ -n auto

# Sequential execution for debugging
pytest tests/integration/middleware/ -n 0
```

### CI/CD Integration

**Recommended CI pipeline**:
```yaml
# Example GitHub Actions workflow
- name: Run middleware integration tests
  run: |
    cd backend
    pytest tests/integration/middleware/ \
      --cov=app.core.middleware \
      --cov-report=xml \
      --cov-fail-under=80 \
      -v
```

**Coverage targets**:
- Overall middleware integration coverage: **≥ 80%**
- Critical seams (P0): **≥ 90%**
- Individual middleware modules: **≥ 75%**

---

## Success Criteria

### Test Suite Quality Metrics

**Coverage**:
- [ ] ≥ 80% integration test coverage of `app/core/middleware/`
- [ ] All P0 seams have ≥ 90% coverage
- [ ] All public contracts (`.pyi` files) validated

**Test Quality**:
- [ ] All tests use `create_app()` factory pattern for isolation
- [ ] No tests mock middleware internal methods
- [ ] All tests verify observable HTTP behavior (headers, status, body)
- [ ] Concurrent tests validate contextvar isolation

**Reliability**:
- [ ] All tests pass with `pytest-randomly` enabled
- [ ] No flaky tests (pass consistently across 10 runs)
- [ ] Tests run in < 30 seconds total (integration suite)

**Documentation**:
- [ ] Each test file has module docstring explaining seam
- [ ] Each test has docstring explaining scenario and business impact
- [ ] README documents how to run tests and interpret failures

### Business Value Delivered

**Security**:
- [ ] Security headers validated across all endpoints
- [ ] Sensitive data redaction verified
- [ ] Rate limiting DoS protection confirmed
- [ ] Error responses don't leak sensitive information

**Reliability**:
- [ ] Middleware execution order validated (LIFO)
- [ ] Redis fallback tested (graceful degradation)
- [ ] Exception handling tested across stack
- [ ] Configuration validation prevents misconfigurations

**Observability**:
- [ ] Correlation IDs propagate correctly
- [ ] Performance metrics headers present
- [ ] Logging captures request lifecycle
- [ ] Error logging includes correlation IDs

**Compatibility**:
- [ ] API versioning supports multiple strategies
- [ ] CORS enables browser clients (if applicable)
- [ ] Compression optimizes bandwidth
- [ ] Request size limits prevent DoS

---

## Next Steps

1. **Review and approve test plan** - Stakeholder sign-off on seams and priorities
2. **Setup test infrastructure** - Create fixtures and test data generators
3. **Implement P0 seams** - Phase 1 (6 critical seams, ~10-12 hours)
4. **Validate P0 coverage** - Ensure ≥ 90% coverage on critical paths
5. **Implement P1 seams** - Phase 2 (4 important seams, ~6-8 hours)
6. **Implement P2 seams** - Phase 3 (1 nice-to-have seam, ~2-3 hours)
7. **CI/CD integration** - Add to automated test pipeline
8. **Documentation** - Create README with test execution guide

---

## Appendices

### A. Contract File References

All middleware contracts located in: `backend/contracts/core/middleware/`

- `__init__.pyi` - Main middleware package contract
- `security.pyi` - Security middleware contract
- `request_logging.pyi` - Request logging middleware contract
- `performance_monitoring.pyi` - Performance monitoring contract (inferred)
- `rate_limiting.pyi` - Rate limiting middleware contract
- `compression.pyi` - Compression middleware contract
- `api_versioning.pyi` - API versioning middleware contract
- `request_size.pyi` - Request size limiting contract (inferred)
- `cors.pyi` - CORS middleware contract (inferred)

### B. Implementation File References

All middleware implementation located in: `backend/app/core/middleware/`

- `__init__.py` - Main middleware setup and orchestration (lines 1-1263)
- `security.py` - Security middleware implementation
- `request_logging.py` - Request logging middleware implementation
- `performance_monitoring.py` - Performance monitoring implementation
- `rate_limiting.py` - Rate limiting middleware implementation
- `compression.py` - Compression middleware implementation
- `api_versioning.py` - API versioning middleware implementation
- `request_size.py` - Request size limiting implementation
- `cors.py` - CORS middleware setup
- `global_exception_handler.py` - Global exception handler

### C. Key Dependencies

**Testing Dependencies** (from `backend/pyproject.toml`):
- pytest = "^8.0.0"
- pytest-asyncio = "^1.0.0"
- pytest-cov = "^4.0"
- pytest-xdist = "^3.7.0"
- pytest-mock = "^3.10.0"
- pytest-timeout = "^2.4.0"
- pytest-randomly = "^3.12.0"
- fakeredis = "^2.10.0"
- httpx = "^0.28.1"

**Runtime Dependencies**:
- fastapi = "^0.116.0"
- starlette (via FastAPI)
- redis = "^6.0.0"
- brotli = "^1.1.0"
- psutil = "^7.0.0"

### D. Related Documentation

**Testing Philosophy**:
- `backend/tests/integration/middleware/TEST_RECS.md` - Middleware testing recommendations
- `docs/guides/testing/INTEGRATION_TESTS.md` - Integration testing philosophy
- `docs/guides/testing/UNIT_TESTS.md` - Unit testing philosophy

**Architecture**:
- `backend/CLAUDE.md` - App Factory Pattern documentation
- `backend/app/core/middleware/__init__.py` - LIFO execution order documentation
- `docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md` - Architectural patterns

**Configuration**:
- `docs/get-started/ENVIRONMENT_VARIABLES.md` - Middleware configuration options
- `backend/app/core/config.py` - Settings implementation

---

**Document Status**: ✅ FINAL - Ready for Implementation
**Last Updated**: 2025-01-21
**Reviewed By**: Integration Test Plan Review (TEST_PLAN_REVIEW.md)
**Approved For**: Implementation
