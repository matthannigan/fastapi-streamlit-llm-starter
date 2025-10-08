# LLM-Guard Integration Implementation Task Plan

## Context and Rationale

The FastAPI backend currently uses **custom security validation code** for protecting against prompt injection, toxic content, and data leakage. This custom implementation creates technical debt and requires ongoing maintenance of security models that are already well-solved by the open-source community.

**Root Cause**: Building and maintaining custom security models is expensive, time-consuming, and risky. The LLM security landscape evolves rapidly, and keeping custom implementations current with new attack vectors is unsustainable for a starter template.

### Problem Evidence
```
Current State:
- Custom prompt injection detection with limited coverage
- Basic toxicity filtering without fine-tuned models
- Simple PII detection that may miss edge cases
- No bias detection or language validation
- Limited test coverage for security edge cases
- Maintenance burden for keeping security models current

Risks:
- Custom security may miss emerging attack patterns
- Maintenance overhead disproportionate to template scope
- Users may distrust custom security over industry standards
- Limited community vetting of security approaches
```

### Architectural Impact
The LLM-Guard integration addresses multiple concerns:
- **Industry Standards**: Replace custom code with battle-tested open-source security framework
- **Comprehensive Coverage**: 15+ built-in scanners covering prompt injection, toxicity, PII, bias, etc.
- **Performance**: ONNX-optimized models for production deployment
- **Maintainability**: Community-maintained models and regular security updates
- **Educational Value**: Template demonstrates production-ready LLM security patterns

### Desired Outcome
A production-ready security service based on LLM-Guard that replaces custom validation code, providing comprehensive protection against LLM security threats with minimal performance impact. Success metrics: Custom security code completely removed, <50ms p95 scanner latency with ONNX, >80% cache hit rate, 100% security event logging.

---

## Implementation Phases Overview

**Phase 1: Core LLM-Guard Integration (Days 1-2, ~8 hours)**
Install LLM-Guard framework, create security service interface with factory pattern, implement basic scanner integration with async processing.

**Phase 2: Configuration System (Day 2-3, ~6 hours)**
Build YAML-based configuration management with environment-specific overrides, validation, and preset support.

**Phase 3: Performance Optimization (Days 3-4, ~8 hours)**
Enable ONNX runtime acceleration, implement intelligent caching with Redis, add lazy loading for faster startup.

**Phase 4: Production Integration (Days 4-5, ~8 hours)**
Integrate security middleware with FastAPI routes, implement comprehensive error handling, add structured logging and metrics.

**Phase 5: Testing and Validation (Days 5-6, ~8 hours)**
Comprehensive test suite for all security components, performance benchmarks, security effectiveness validation.

**Phase 6: Documentation and Examples (Days 6-7, ~6 hours)**
Migration guide, configuration reference, performance tuning guide, agent guidance updates, usage examples.

**Total Estimated Timeline**: 7 days (1.5 weeks) with comprehensive testing and documentation

---

## Phase 1: Core LLM-Guard Integration

### Deliverable 1: LLM-Guard Installation and Setup (Critical Path)
**Goal**: Install LLM-Guard framework with ONNX runtime support and verify basic functionality.

#### Task 1.1: Dependency Installation and Verification
- [ ] Install LLM-Guard core package in backend dependencies:
  - [ ] Add `llm-guard>=0.3.0` to `backend/requirements.txt`
  - [ ] Add `llm-guard[onnxruntime]>=0.3.0` for ONNX optimization
  - [ ] Verify Python version compatibility (requires 3.9+)
  - [ ] Test installation in clean virtual environment
- [ ] Verify LLM-Guard imports and basic functionality:
  - [ ] Test core scanner imports: `from llm_guard import scan_prompt, scan_output`
  - [ ] Test scanner class imports: `PromptInjection, Toxicity, Anonymize`
  - [ ] Verify ONNX runtime availability and fallback behavior
  - [ ] Document any installation issues or platform-specific requirements
- [ ] Update Docker configuration for LLM-Guard:
  - [ ] Update `backend/Dockerfile` with LLM-Guard dependencies
  - [ ] Ensure ONNX runtime libraries available in container
  - [ ] Test container build and basic scanner functionality
  - [ ] Document memory requirements for production deployment

#### Task 1.2: Security Service Interface Design
- [ ] Create security service protocol in `app/infrastructure/security/`:
  - [ ] Define `SecurityService` protocol with `validate_input()` and `validate_output()` methods
  - [ ] Create `SecurityResult` dataclass for structured validation results
  - [ ] Define `Violation` dataclass for detailed violation information
  - [ ] Add `MetricsSnapshot` dataclass for security metrics
- [ ] Design scanner configuration models:
  - [ ] Create `ScannerConfig` dataclass for scanner-specific configuration
  - [ ] Create `SecurityConfig` dataclass for overall security configuration
  - [ ] Create `PerformanceConfig` dataclass for optimization settings
  - [ ] Add Pydantic validation for all configuration models
- [ ] Create security service factory:
  - [ ] Implement `create_security_service(mode: str)` factory function
  - [ ] Support `"local"` mode for LLM-Guard integration
  - [ ] Add placeholder for future `"saas"` mode (documented but not implemented)
  - [ ] Comprehensive docstring explaining factory pattern and extensibility

#### Task 1.3: Basic Scanner Implementation
- [ ] Create LLM-Guard scanner wrapper in `app/infrastructure/security/scanners/`:
  - [ ] Create `local_scanner.py` with `LocalLLMGuardScanner` class
  - [ ] Implement `SecurityService` protocol methods
  - [ ] Basic scanner initialization with minimal configuration
  - [ ] Error handling for scanner initialization failures
- [ ] Implement input scanner chain:
  - [ ] Integrate `PromptInjection` scanner with threshold configuration
  - [ ] Integrate `Toxicity` scanner for input content filtering
  - [ ] Add basic async processing wrapper for scanner execution
  - [ ] Return structured `SecurityResult` with violation details
- [ ] Implement output scanner chain:
  - [ ] Integrate `Toxicity` scanner for output content filtering
  - [ ] Integrate `Bias` scanner for output fairness validation
  - [ ] Add async processing wrapper for output scanning
  - [ ] Consistent result structure with input scanning
- [ ] Basic logging for security events:
  - [ ] Log all security scan requests with input metadata
  - [ ] Log all security violations with scanner details
  - [ ] Log scanner performance metrics (execution time)
  - [ ] Structured logging format for downstream analysis

---

### Deliverable 2: Security Service Factory Testing
**Goal**: Validate security service factory and basic scanner functionality with comprehensive tests.

#### Task 2.1: Factory Pattern Testing
- [ ] Create test suite in `tests/unit/infrastructure/security/test_security_factory.py`:
  - [ ] Test `create_security_service("local")` creates LocalLLMGuardScanner
  - [ ] Test factory raises error for unknown security modes
  - [ ] Test factory returns consistent interface (SecurityService protocol)
  - [ ] Test factory with different configuration parameters
- [ ] Test security service interface compliance:
  - [ ] Verify `validate_input()` method signature and return type
  - [ ] Verify `validate_output()` method signature and return type
  - [ ] Verify `get_metrics()` method signature and return type
  - [ ] Test async method execution behavior
- [ ] Test configuration models:
  - [ ] Test `SecurityResult` dataclass with various violation scenarios
  - [ ] Test `Violation` dataclass with different violation types
  - [ ] Test `ScannerConfig` validation and defaults
  - [ ] Test `SecurityConfig` validation and nested configuration

#### Task 2.2: Basic Scanner Functionality Testing
- [ ] Create test suite in `tests/unit/infrastructure/security/test_local_scanner.py`:
  - [ ] Test scanner initialization with default configuration
  - [ ] Test scanner initialization with custom thresholds
  - [ ] Test scanner handles missing or invalid configuration gracefully
  - [ ] Test scanner initialization failures are properly handled
- [ ] Test input scanning behavior:
  - [ ] Test benign input passes validation (is_valid=True)
  - [ ] Test prompt injection attempt is detected (is_valid=False)
  - [ ] Test toxic content is detected and blocked
  - [ ] Test violation details include scanner name and risk score
- [ ] Test output scanning behavior:
  - [ ] Test benign output passes validation
  - [ ] Test toxic output is detected and blocked
  - [ ] Test biased output is detected with appropriate risk score
  - [ ] Test output scanning returns consistent result structure
- [ ] Test async processing:
  - [ ] Test scanners execute asynchronously (asyncio compatibility)
  - [ ] Test concurrent scanning requests don't interfere
  - [ ] Test async error handling and timeout behavior
  - [ ] Test scanner cleanup on async task cancellation

#### Task 2.3: Integration with Existing Security Infrastructure
- [ ] Audit existing security module in `app/infrastructure/security/`:
  - [ ] Document current `auth.py` implementation (API key authentication)
  - [ ] Identify integration points for content scanning
  - [ ] Map custom security code to LLM-Guard scanner equivalents
  - [ ] Plan migration strategy for existing security features
- [ ] Test coexistence with existing security features:
  - [ ] Test API key authentication works with new security service
  - [ ] Test security scanning doesn't interfere with auth flow
  - [ ] Test error handling when both auth and content validation fail
  - [ ] Test combined security metrics collection

---

## Phase 2: Configuration System

### Deliverable 3: YAML-Based Scanner Configuration (Critical Path)
**Goal**: Create flexible YAML-based configuration system with environment-specific overrides and validation.

#### Task 3.1: Configuration File Structure
- [ ] Create configuration directory structure:
  - [ ] Create `config/security/` directory for security configuration
  - [ ] Create `config/security/scanners.yaml` with default scanner configuration
  - [ ] Create `config/security/dev.yaml` for development environment overrides
  - [ ] Create `config/security/prod.yaml` for production environment overrides
- [ ] Design base scanner configuration schema:
  ```yaml
  input_scanners:
    prompt_injection:
      enabled: true
      threshold: 0.8
      use_onnx: true
    toxicity:
      enabled: true
      threshold: 0.7
      use_onnx: true
    pii_detection:
      enabled: true
      redact: true
      use_onnx: true
  
  output_scanners:
    toxicity:
      enabled: true
      threshold: 0.8
    bias:
      enabled: true
      threshold: 0.7
  
  performance:
    cache_enabled: true
    cache_ttl_seconds: 3600
    lazy_loading: true
    onnx_providers: ["CPUExecutionProvider"]
  ```
- [ ] Create environment-specific override patterns:
  - [ ] Development: More lenient thresholds, CPU-only processing
  - [ ] Production: Stricter thresholds, GPU support with CPU fallback
  - [ ] Testing: Minimal scanners for fast test execution
  - [ ] Document override precedence and merging behavior

#### Task 3.2: Configuration Loading and Validation
- [ ] Implement configuration loader in `app/infrastructure/security/config_loader.py`:
  - [ ] Create `load_security_config()` function with YAML parsing
  - [ ] Implement environment-specific override loading
  - [ ] Support environment variable interpolation in YAML
  - [ ] Validate configuration structure against Pydantic models
- [ ] Add configuration validation:
  - [ ] Validate scanner names match available LLM-Guard scanners
  - [ ] Validate threshold values are in valid range (0.0-1.0)
  - [ ] Validate ONNX provider names are recognized
  - [ ] Raise clear errors for invalid configuration with suggestions
- [ ] Implement configuration merging:
  - [ ] Load base `scanners.yaml` configuration
  - [ ] Merge environment-specific overrides (dev.yaml or prod.yaml)
  - [ ] Apply environment variable overrides (e.g., `SECURITY_MODE`)
  - [ ] Document precedence: ENV vars > env-specific YAML > base YAML
- [ ] Add configuration caching:
  - [ ] Cache loaded configuration to avoid repeated file I/O
  - [ ] Invalidate cache on configuration file changes (development mode)
  - [ ] Support hot reload for development environments
  - [ ] Document production caching behavior

#### Task 3.3: Settings Integration
- [ ] Add security configuration to Settings in `app/core/config.py`:
  - [ ] Add `SECURITY_MODE` environment variable (default: "local")
  - [ ] Add `SECURITY_CONFIG_PATH` environment variable
  - [ ] Add `SECURITY_CACHE_ENABLED` boolean flag
  - [ ] Add `SECURITY_ONNX_ENABLED` boolean flag
- [ ] Integrate configuration loader with Settings:
  - [ ] Load security configuration in Settings initialization
  - [ ] Cache security configuration in Settings instance
  - [ ] Support Settings factory pattern for test isolation
  - [ ] Document Settings fields related to security configuration
- [ ] Create configuration presets:
  - [ ] Create "development" preset with lenient settings
  - [ ] Create "production" preset with strict settings
  - [ ] Create "testing" preset with minimal scanners
  - [ ] Add preset selection via `SECURITY_PRESET` environment variable

#### Task 3.4: Configuration Testing
- [ ] Create test suite in `tests/unit/infrastructure/security/test_config_loader.py`:
  - [ ] Test loading base scanner configuration
  - [ ] Test environment-specific override merging
  - [ ] Test environment variable interpolation
  - [ ] Test configuration validation with invalid inputs
- [ ] Test configuration error handling:
  - [ ] Test missing configuration file handling
  - [ ] Test invalid YAML syntax handling
  - [ ] Test unknown scanner names raise validation errors
  - [ ] Test invalid threshold values raise validation errors
- [ ] Test configuration merging precedence:
  - [ ] Test environment overrides take precedence over base config
  - [ ] Test environment variables override YAML configuration
  - [ ] Test partial overrides merge correctly (don't replace entire sections)
  - [ ] Test override behavior documented and predictable
- [ ] Test preset system:
  - [ ] Test development preset loads correctly
  - [ ] Test production preset loads correctly
  - [ ] Test testing preset loads correctly
  - [ ] Test unknown preset raises clear error

---

### Deliverable 4: Scanner Factory with Configuration
**Goal**: Enhance scanner factory to use YAML configuration and support environment-specific behavior.

#### Task 4.1: Configuration-Driven Scanner Initialization
- [ ] Update `LocalLLMGuardScanner` to use configuration:
  - [ ] Accept `SecurityConfig` parameter in constructor
  - [ ] Initialize scanners based on enabled flags in configuration
  - [ ] Apply threshold values from configuration to scanners
  - [ ] Enable/disable ONNX based on configuration settings
- [ ] Implement dynamic scanner registration:
  - [ ] Load only enabled scanners from configuration
  - [ ] Skip disabled scanners to reduce memory footprint
  - [ ] Log which scanners are enabled on initialization
  - [ ] Support adding custom scanners via configuration
- [ ] Add scanner-specific configuration:
  - [ ] Map YAML scanner config to LLM-Guard scanner parameters
  - [ ] Support scanner-specific options (e.g., PII redaction flag)
  - [ ] Validate scanner parameters before initialization
  - [ ] Document supported parameters for each scanner type
- [ ] Implement ONNX provider configuration:
  - [ ] Support multiple ONNX execution providers (CUDA, CPU)
  - [ ] Implement fallback chain (GPU → CPU)
  - [ ] Log which provider is being used for each scanner
  - [ ] Handle ONNX initialization failures gracefully

#### Task 4.2: Configuration-Based Factory Testing
- [ ] Test configuration-driven initialization:
  - [ ] Test factory with minimal scanner configuration
  - [ ] Test factory with all scanners enabled
  - [ ] Test factory with selective scanner enablement
  - [ ] Test factory respects threshold values from configuration
- [ ] Test ONNX configuration:
  - [ ] Test ONNX enabled loads optimized models
  - [ ] Test ONNX disabled falls back to standard models
  - [ ] Test ONNX provider fallback behavior (GPU → CPU)
  - [ ] Test ONNX initialization error handling
- [ ] Test environment-specific behavior:
  - [ ] Test development configuration loads correctly
  - [ ] Test production configuration loads correctly
  - [ ] Test configuration changes require scanner reinitialization
  - [ ] Test Settings factory pattern with security configuration

---

## Phase 3: Performance Optimization

### Deliverable 5: ONNX Runtime Optimization (Critical Path)
**Goal**: Enable ONNX runtime acceleration for production performance with graceful fallback.

#### Task 5.1: ONNX Model Integration
- [ ] Research LLM-Guard ONNX model requirements:
  - [ ] Document which scanners support ONNX optimization
  - [ ] Identify ONNX model download locations and sizes
  - [ ] Document ONNX runtime system requirements
  - [ ] Research GPU acceleration requirements (CUDA, etc.)
- [ ] Implement ONNX model loading:
  - [ ] Create model download and caching mechanism
  - [ ] Implement automatic ONNX model discovery
  - [ ] Add model verification before loading
  - [ ] Document model storage locations and permissions
- [ ] Add ONNX execution provider configuration:
  - [ ] Support CUDA execution provider for GPU acceleration
  - [ ] Support CPU execution provider as fallback
  - [ ] Implement provider selection based on hardware availability
  - [ ] Log which provider is selected and why
- [ ] Implement graceful ONNX fallback:
  - [ ] Detect ONNX initialization failures
  - [ ] Automatically fall back to non-ONNX models
  - [ ] Log fallback events with reason
  - [ ] Ensure functionality preserved in fallback mode

#### Task 5.2: Performance Benchmarking
- [ ] Create performance benchmark suite in `scripts/benchmark_security.py`:
  - [ ] Benchmark scanner latency with ONNX enabled
  - [ ] Benchmark scanner latency with ONNX disabled
  - [ ] Benchmark end-to-end security validation overhead
  - [ ] Compare performance across different ONNX providers
- [ ] Measure per-scanner performance:
  - [ ] Benchmark PromptInjection scanner latency
  - [ ] Benchmark Toxicity scanner latency
  - [ ] Benchmark PII detection scanner latency
  - [ ] Benchmark Bias scanner latency
- [ ] Create performance reports:
  - [ ] Document p50, p95, p99 latencies for each scanner
  - [ ] Compare ONNX vs non-ONNX performance improvements
  - [ ] Document memory usage with different configurations
  - [ ] Provide recommendations for production optimization
- [ ] Validate performance targets:
  - [ ] Verify <50ms p95 latency for ONNX-optimized scanners
  - [ ] Verify <500MB idle memory usage
  - [ ] Verify <2GB peak memory under load
  - [ ] Document any performance bottlenecks discovered

#### Task 5.3: ONNX Testing
- [ ] Create ONNX-specific test suite:
  - [ ] Test ONNX models load successfully
  - [ ] Test scanning accuracy matches non-ONNX results
  - [ ] Test ONNX fallback behavior on initialization failure
  - [ ] Test ONNX provider selection logic
- [ ] Test platform compatibility:
  - [ ] Test on macOS (CPU-only)
  - [ ] Test on Linux with CPU-only
  - [ ] Test on Linux with GPU (if available)
  - [ ] Document platform-specific requirements and limitations
- [ ] Test error scenarios:
  - [ ] Test missing ONNX runtime library handling
  - [ ] Test CUDA unavailable fallback
  - [ ] Test corrupted ONNX model handling
  - [ ] Test memory exhaustion during model loading

---

### Deliverable 6: Intelligent Caching Layer
**Goal**: Implement Redis-based result caching to minimize redundant security scans and improve performance.

#### Task 6.1: Cache Strategy Design
- [ ] Design cache key strategy:
  - [ ] Use content hash (SHA-256) as cache key
  - [ ] Include scanner configuration in cache key
  - [ ] Include scanner version/model version in cache key
  - [ ] Document cache key format and collision prevention
- [ ] Design cache value structure:
  - [ ] Store complete `SecurityResult` in cache
  - [ ] Include timestamp for cache entry age tracking
  - [ ] Store scanner metadata (which scanners ran)
  - [ ] Serialize efficiently (JSON or MessagePack)
- [ ] Define cache invalidation strategy:
  - [ ] TTL-based expiration (configurable via YAML)
  - [ ] Scanner configuration change invalidates all entries
  - [ ] Scanner version upgrade invalidates all entries
  - [ ] Manual cache flush via internal API endpoint
- [ ] Design cache warming strategy:
  - [ ] No automatic warming (scan-on-demand only)
  - [ ] Optional preload of common prompt patterns
  - [ ] Document cache warming best practices
  - [ ] Consider cache warming for testing scenarios

#### Task 6.2: Cache Implementation
- [ ] Create cache layer in `app/infrastructure/security/cache.py`:
  - [ ] Implement `SecurityResultCache` class using Redis
  - [ ] Support fallback to memory cache if Redis unavailable
  - [ ] Implement async cache operations (get, set, delete)
  - [ ] Add cache statistics tracking (hits, misses, size)
- [ ] Integrate cache with scanner:
  - [ ] Check cache before executing scanners
  - [ ] Store scan results in cache after execution
  - [ ] Log cache hits and misses for monitoring
  - [ ] Measure cache performance impact
- [ ] Implement cache configuration:
  - [ ] Load cache settings from `performance` section in YAML
  - [ ] Support cache enable/disable via configuration
  - [ ] Configure TTL per scanner type
  - [ ] Support cache size limits
- [ ] Add cache management utilities:
  - [ ] Implement cache flush operation
  - [ ] Implement cache statistics retrieval
  - [ ] Add cache health check
  - [ ] Create internal API endpoint for cache management

#### Task 6.3: Cache Testing
- [ ] Create cache test suite in `tests/unit/infrastructure/security/test_security_cache.py`:
  - [ ] Test cache hit returns cached result without scanning
  - [ ] Test cache miss executes scan and stores result
  - [ ] Test cache key generation is consistent
  - [ ] Test cache key includes configuration in hash
- [ ] Test cache invalidation:
  - [ ] Test TTL expiration removes old entries
  - [ ] Test configuration change invalidates cache
  - [ ] Test manual flush clears all entries
  - [ ] Test partial invalidation (specific scanners)
- [ ] Test cache fallback:
  - [ ] Test Redis unavailable falls back to memory cache
  - [ ] Test memory cache has size limits
  - [ ] Test cache disabled mode bypasses caching
  - [ ] Test cache errors don't prevent scanning
- [ ] Test cache performance:
  - [ ] Measure cache lookup latency (<1ms target)
  - [ ] Test cache hit rate with repeated content (>80% target)
  - [ ] Test cache memory usage stays within limits
  - [ ] Test cache doesn't degrade scanner accuracy

---

### Deliverable 7: Lazy Loading for Faster Startup
**Goal**: Implement on-demand scanner initialization to reduce application startup time and memory usage.

#### Task 7.1: Lazy Loading Implementation
- [ ] Refactor scanner initialization in `LocalLLMGuardScanner`:
  - [ ] Initialize scanners as `None` on construction
  - [ ] Load scanner models on first use (lazy initialization)
  - [ ] Cache initialized scanners for subsequent calls
  - [ ] Log scanner initialization with timing information
- [ ] Implement per-scanner lazy loading:
  - [ ] Separate initialization for input vs output scanners
  - [ ] Load only requested scanner types on demand
  - [ ] Thread-safe initialization for concurrent requests
  - [ ] Handle initialization failures per scanner
- [ ] Add warmup mechanism:
  - [ ] Create `warmup()` method to preload scanners
  - [ ] Call warmup during application lifespan startup (optional)
  - [ ] Support selective warmup (only production-critical scanners)
  - [ ] Log warmup completion and timing
- [ ] Optimize model loading:
  - [ ] Download models to shared cache directory
  - [ ] Reuse models across multiple scanner instances
  - [ ] Implement model file locking for concurrent access
  - [ ] Document model storage location and cleanup

#### Task 7.2: Startup Performance Testing
- [ ] Measure application startup time:
  - [ ] Baseline: Eager loading all scanners at startup
  - [ ] Lazy loading: Initialize scanners on-demand
  - [ ] Target: <5s application startup with lazy loading
  - [ ] Compare memory usage: eager vs lazy
- [ ] Test first request performance:
  - [ ] Measure latency of first security scan (includes initialization)
  - [ ] Measure latency of subsequent scans (scanner cached)
  - [ ] Acceptable first request latency: <200ms
  - [ ] Document first-request vs steady-state performance
- [ ] Test concurrent initialization:
  - [ ] Test multiple requests trigger scanner initialization simultaneously
  - [ ] Verify only one initialization occurs per scanner
  - [ ] Test thread safety of lazy initialization
  - [ ] Test initialization under load conditions
- [ ] Create startup benchmarks:
  - [ ] Script to measure application startup time
  - [ ] Script to measure first request latency
  - [ ] Document startup performance improvements
  - [ ] Provide optimization recommendations

#### Task 7.3: Lazy Loading Testing
- [ ] Create lazy loading test suite:
  - [ ] Test scanners not initialized on service creation
  - [ ] Test scanner initialized on first use
  - [ ] Test scanner reused on subsequent calls
  - [ ] Test initialization errors handled gracefully
- [ ] Test warmup behavior:
  - [ ] Test warmup() initializes all configured scanners
  - [ ] Test warmup() is idempotent (can call multiple times)
  - [ ] Test selective warmup (specific scanners only)
  - [ ] Test warmup timing and logging
- [ ] Test concurrent access:
  - [ ] Test concurrent first requests don't duplicate initialization
  - [ ] Test scanner initialization is thread-safe
  - [ ] Test initialization errors in concurrent scenario
  - [ ] Test race conditions in lazy loading logic

---

## Phase 4: Production Integration

### Deliverable 8: FastAPI Middleware Integration (Critical Path)
**Goal**: Integrate security service with FastAPI middleware for transparent request/response scanning.

#### Task 8.1: Security Middleware Implementation
- [ ] Create security middleware in `app/middleware/security.py`:
  - [ ] Implement `SecurityMiddleware` class with ASGI interface
  - [ ] Inject security service via dependency injection
  - [ ] Intercept requests before route handlers
  - [ ] Intercept responses before returning to client
- [ ] Implement request scanning:
  - [ ] Extract request body content for scanning
  - [ ] Support JSON request bodies with text content
  - [ ] Support form data with text fields
  - [ ] Skip scanning for non-text content types
- [ ] Implement response scanning:
  - [ ] Extract response body content for scanning
  - [ ] Support JSON responses with text content
  - [ ] Support streaming responses with chunked scanning
  - [ ] Skip scanning for non-text content types
- [ ] Add middleware configuration:
  - [ ] Support enabling/disabling middleware per route
  - [ ] Support skipping specific endpoints (health checks, etc.)
  - [ ] Configure scan timeout limits
  - [ ] Document middleware registration order

#### Task 8.2: Error Response Handling
- [ ] Design security error response format:
  ```json
  {
    "error": "security_violation",
    "message": "Content failed security validation",
    "violations": [
      {
        "scanner": "PromptInjection",
        "risk_score": 0.92,
        "details": "Potential prompt injection detected"
      }
    ],
    "request_id": "uuid"
  }
  ```
- [ ] Implement security exception handling:
  - [ ] Create `SecurityViolationError` exception class
  - [ ] Raise exception when security scan fails
  - [ ] Include detailed violation information in exception
  - [ ] Add request correlation ID for debugging
- [ ] Add exception handler to FastAPI:
  - [ ] Register exception handler for `SecurityViolationError`
  - [ ] Return 400 Bad Request for input violations
  - [ ] Return 500 Internal Server Error for output violations
  - [ ] Log all security violations with full details
- [ ] Implement security headers:
  - [ ] Add `X-Security-Scanned: true` header to responses
  - [ ] Add `X-Security-Scanners` header listing active scanners
  - [ ] Add timing header `X-Security-Scan-Time-Ms`
  - [ ] Document security headers for API consumers

#### Task 8.3: Route Integration
- [ ] Identify routes requiring security scanning:
  - [ ] All `/v1/text-processing/*` endpoints (LLM interactions)
  - [ ] Any routes accepting user-generated content
  - [ ] Skip health check endpoints (`/health`, `/internal/health`)
  - [ ] Skip authentication endpoints (avoid false positives)
- [ ] Update route handlers to use security scanning:
  - [ ] Add middleware to routes requiring scanning
  - [ ] Update route documentation to mention security
  - [ ] Add security examples to API documentation
  - [ ] Document which scanners apply to which routes
- [ ] Test route integration:
  - [ ] Test protected routes reject malicious input
  - [ ] Test protected routes allow benign input
  - [ ] Test unprotected routes skip scanning
  - [ ] Test route-specific scanner configuration

#### Task 8.4: Middleware Testing
- [ ] Create middleware test suite in `tests/unit/middleware/test_security_middleware.py`:
  - [ ] Test middleware intercepts requests correctly
  - [ ] Test middleware intercepts responses correctly
  - [ ] Test middleware allows benign requests/responses
  - [ ] Test middleware blocks malicious requests/responses
- [ ] Test error handling:
  - [ ] Test security violation returns proper error response
  - [ ] Test scanner failures don't crash application
  - [ ] Test timeout handling for slow scanners
  - [ ] Test error responses include violation details
- [ ] Test integration with existing middleware:
  - [ ] Test security middleware coexists with CORS middleware
  - [ ] Test security middleware coexists with request logging
  - [ ] Test middleware ordering is correct
  - [ ] Test middleware doesn't interfere with authentication
- [ ] Create integration tests:
  - [ ] Test end-to-end security scanning via API
  - [ ] Test request with prompt injection is blocked
  - [ ] Test request with toxic content is blocked
  - [ ] Test request with PII is detected/redacted

---

### Deliverable 9: Logging and Metrics
**Goal**: Comprehensive audit trail and performance monitoring for all security decisions.

#### Task 9.1: Structured Security Logging
- [ ] Design security event log format:
  ```json
  {
    "timestamp": "2025-10-08T12:34:56Z",
    "event_type": "security_scan",
    "scan_type": "input",
    "result": "blocked",
    "violations": [
      {
        "scanner": "PromptInjection",
        "risk_score": 0.92
      }
    ],
    "scan_time_ms": 45,
    "request_id": "uuid",
    "endpoint": "/v1/text-processing/analyze"
  }
  ```
- [ ] Implement security logger in `app/infrastructure/security/logger.py`:
  - [ ] Create `SecurityLogger` class with structured logging
  - [ ] Log all scan requests with metadata
  - [ ] Log all scan results (pass or fail)
  - [ ] Log scanner performance metrics
- [ ] Add log levels for security events:
  - [ ] INFO: Successful scans (pass)
  - [ ] WARNING: Low-risk violations (score < 0.8)
  - [ ] ERROR: High-risk violations (score >= 0.8)
  - [ ] DEBUG: Scanner configuration and initialization
- [ ] Integrate with existing logging infrastructure:
  - [ ] Use existing logger configuration from Settings
  - [ ] Support log level configuration via environment variables
  - [ ] Format logs for downstream log aggregation (JSON)
  - [ ] Add correlation IDs for request tracing

#### Task 9.2: Security Metrics Collection
- [ ] Design security metrics:
  - [ ] Counter: Total scans performed (input/output)
  - [ ] Counter: Total violations detected (by scanner type)
  - [ ] Counter: Total blocks applied (by risk level)
  - [ ] Histogram: Scanner latency distribution
  - [ ] Gauge: Currently active scans
  - [ ] Gauge: Cache hit rate
- [ ] Implement metrics in `app/infrastructure/security/metrics.py`:
  - [ ] Create `SecurityMetrics` class with Prometheus-compatible metrics
  - [ ] Update metrics on every scan operation
  - [ ] Expose metrics via `/internal/security/metrics` endpoint
  - [ ] Support metrics reset for testing
- [ ] Add scanner-specific metrics:
  - [ ] Track trigger frequency per scanner type
  - [ ] Track average risk scores per scanner
  - [ ] Track scanner execution time per scanner type
  - [ ] Track scanner initialization time
- [ ] Create metrics dashboard endpoint:
  - [ ] Add `/internal/security/metrics` for raw metrics
  - [ ] Add `/internal/security/stats` for human-readable stats
  - [ ] Include cache statistics in metrics
  - [ ] Document metrics format and usage

#### Task 9.3: Audit Trail for Compliance
- [ ] Design audit trail requirements:
  - [ ] All security decisions logged persistently
  - [ ] Logs include full context (user, endpoint, timestamp)
  - [ ] Logs support retention policies (30/60/90 days)
  - [ ] Logs support compliance reporting queries
- [ ] Implement audit storage:
  - [ ] Log security events to file with rotation
  - [ ] Support external log shipping (e.g., CloudWatch, Datadog)
  - [ ] Ensure logs are immutable after writing
  - [ ] Document log retention and cleanup policies
- [ ] Create audit query utilities:
  - [ ] Script to query security violations by date range
  - [ ] Script to generate compliance reports
  - [ ] Script to analyze security trends
  - [ ] Document audit trail access and permissions
- [ ] Test audit compliance:
  - [ ] Verify all security decisions are logged
  - [ ] Test log retention policies work correctly
  - [ ] Test log format supports compliance queries
  - [ ] Document compliance validation procedures

#### Task 9.4: Logging and Metrics Testing
- [ ] Create logging test suite:
  - [ ] Test all security events are logged
  - [ ] Test log format is consistent and parseable
  - [ ] Test log levels match event severity
  - [ ] Test correlation IDs work across requests
- [ ] Create metrics test suite:
  - [ ] Test metrics increment correctly on scans
  - [ ] Test metrics reset correctly
  - [ ] Test metrics endpoint returns valid Prometheus format
  - [ ] Test scanner-specific metrics track correctly
- [ ] Test audit trail:
  - [ ] Test audit logs persist across restarts
  - [ ] Test audit logs include all required fields
  - [ ] Test audit query utilities work correctly
  - [ ] Test audit logs support compliance requirements

---

## Phase 5: Testing and Validation

### Deliverable 10: Comprehensive Security Test Suite (Critical Path)
**Goal**: Production-ready test coverage for all security components with behavior-driven validation.

#### Task 10.1: Unit Tests for Core Components
- [ ] Complete scanner factory tests:
  - [ ] Test factory with all configuration variations
  - [ ] Test factory error handling for invalid configs
  - [ ] Test factory creates independent scanner instances
  - [ ] Test factory with different security modes
- [ ] Complete scanner tests:
  - [ ] Test each scanner type individually (PromptInjection, Toxicity, etc.)
  - [ ] Test scanner threshold behavior
  - [ ] Test scanner async execution
  - [ ] Test scanner error handling and fallbacks
- [ ] Complete configuration tests:
  - [ ] Test configuration loading from YAML
  - [ ] Test environment-specific overrides
  - [ ] Test configuration validation
  - [ ] Test configuration merging precedence
- [ ] Complete cache tests:
  - [ ] Test cache hit/miss behavior
  - [ ] Test cache invalidation
  - [ ] Test cache fallback to memory
  - [ ] Test cache performance impact

#### Task 10.2: Integration Tests
- [ ] Create end-to-end security tests in `tests/integration/security/`:
  - [ ] Test complete request flow with security scanning
  - [ ] Test prompt injection detection via API
  - [ ] Test toxic content detection via API
  - [ ] Test PII detection and redaction via API
- [ ] Test middleware integration:
  - [ ] Test security middleware intercepts all requests
  - [ ] Test security violations return proper errors
  - [ ] Test benign requests pass through successfully
  - [ ] Test route-specific security configuration
- [ ] Test error scenarios:
  - [ ] Test scanner initialization failures
  - [ ] Test scanner execution timeouts
  - [ ] Test cache failures don't prevent scanning
  - [ ] Test graceful degradation on component failures
- [ ] Test performance under load:
  - [ ] Test security scanning with concurrent requests
  - [ ] Test cache effectiveness under load
  - [ ] Test scanner resource usage under load
  - [ ] Verify performance targets met under load

#### Task 10.3: Security Effectiveness Testing
- [ ] Create security test dataset:
  - [ ] Collect prompt injection attack examples
  - [ ] Collect toxic content examples
  - [ ] Collect PII-containing examples
  - [ ] Collect benign content for false positive testing
- [ ] Test detection accuracy:
  - [ ] Test prompt injection detection rate (>95% target)
  - [ ] Test toxicity detection rate (>90% target)
  - [ ] Test PII detection rate (>95% target)
  - [ ] Test false positive rate (<2% target)
- [ ] Test edge cases:
  - [ ] Test obfuscated prompt injections
  - [ ] Test context-dependent toxicity
  - [ ] Test edge cases in PII detection
  - [ ] Test scanner behavior with mixed content
- [ ] Document security effectiveness:
  - [ ] Report detection rates for each scanner
  - [ ] Report false positive rates
  - [ ] Document known limitations
  - [ ] Provide recommendations for tuning thresholds

#### Task 10.4: Performance Benchmarks
- [ ] Create comprehensive benchmark suite in `scripts/benchmark_security.py`:
  - [ ] Benchmark scanner latency (p50, p95, p99)
  - [ ] Benchmark end-to-end API latency with security
  - [ ] Benchmark cache performance
  - [ ] Benchmark memory usage
- [ ] Run benchmarks in different configurations:
  - [ ] ONNX enabled vs disabled
  - [ ] Cache enabled vs disabled
  - [ ] Different numbers of scanners
  - [ ] Different ONNX providers (GPU vs CPU)
- [ ] Validate performance targets:
  - [ ] Verify <50ms p95 scanner latency with ONNX
  - [ ] Verify <500MB idle memory usage
  - [ ] Verify <2GB peak memory under load
  - [ ] Verify >80% cache hit rate
- [ ] Create performance report:
  - [ ] Document baseline performance metrics
  - [ ] Compare performance across configurations
  - [ ] Provide tuning recommendations
  - [ ] Document hardware requirements

#### Task 10.5: Test Coverage Validation
- [ ] Measure test coverage for security module:
  - [ ] Run `pytest --cov=app/infrastructure/security`
  - [ ] Target: >90% coverage for infrastructure code
  - [ ] Target: >70% coverage for integration tests
  - [ ] Document coverage gaps and justify
- [ ] Review test quality:
  - [ ] Verify tests follow behavior-driven approach
  - [ ] Verify tests are maintainable and clear
  - [ ] Verify tests don't over-mock
  - [ ] Verify tests cover edge cases
- [ ] Add missing tests:
  - [ ] Identify untested code paths
  - [ ] Add tests for edge cases
  - [ ] Add tests for error scenarios
  - [ ] Add tests for concurrency issues

---

### Deliverable 11: Migration Testing
**Goal**: Validate that custom security code is completely replaced and all functionality preserved.

#### Task 11.1: Custom Code Removal
- [ ] Identify all custom security code to remove:
  - [ ] Locate custom prompt injection detection code
  - [ ] Locate custom toxicity filtering code
  - [ ] Locate custom PII detection code
  - [ ] Document all custom security utilities
- [ ] Create removal plan:
  - [ ] Map custom functions to LLM-Guard equivalents
  - [ ] Identify all call sites of custom security code
  - [ ] Plan deprecation path (remove vs mark deprecated)
  - [ ] Document migration steps for custom code users
- [ ] Remove custom security code:
  - [ ] Delete custom security modules
  - [ ] Update imports throughout codebase
  - [ ] Remove custom security tests
  - [ ] Update documentation references
- [ ] Verify functionality preserved:
  - [ ] Test all endpoints still work with LLM-Guard
  - [ ] Test security detection quality maintained or improved
  - [ ] Test no regressions in API behavior
  - [ ] Test backward compatibility for API consumers

#### Task 11.2: Regression Testing
- [ ] Run full test suite:
  - [ ] All unit tests pass with LLM-Guard
  - [ ] All integration tests pass with LLM-Guard
  - [ ] All infrastructure tests pass with LLM-Guard
  - [ ] No test warnings or failures
- [ ] Test existing features:
  - [ ] API authentication still works
  - [ ] Cache functionality still works
  - [ ] Resilience patterns still work
  - [ ] Monitoring and health checks still work
- [ ] Test API compatibility:
  - [ ] All API endpoints return same response formats
  - [ ] Error responses maintain same structure
  - [ ] API documentation still accurate
  - [ ] No breaking changes for API consumers
- [ ] Performance regression testing:
  - [ ] Compare API latency before/after migration
  - [ ] Compare memory usage before/after migration
  - [ ] Compare throughput before/after migration
  - [ ] Target: No more than 10% degradation

#### Task 11.3: Migration Documentation
- [ ] Create migration guide in `docs/guides/infrastructure/SECURITY_MIGRATION_GUIDE.md`:
  - [ ] Document what changed from custom to LLM-Guard
  - [ ] Provide step-by-step migration instructions
  - [ ] Document configuration changes required
  - [ ] Document API behavior changes (if any)
- [ ] Document breaking changes:
  - [ ] List any API changes (if any)
  - [ ] Document configuration changes
  - [ ] Document environment variable changes
  - [ ] Provide upgrade path for existing deployments
- [ ] Create migration checklist:
  - [ ] Pre-migration: Backup configuration and data
  - [ ] Migration: Update dependencies and configuration
  - [ ] Post-migration: Validate security functionality
  - [ ] Rollback: Document rollback procedure

---

## Phase 6: Documentation and Examples

### Deliverable 12: Comprehensive Documentation (Critical Path)
**Goal**: Complete documentation enabling developers to configure, extend, and troubleshoot the security system.

#### Task 12.1: Configuration Reference Documentation
- [ ] Create configuration reference in `docs/reference/security/CONFIGURATION_REFERENCE.md`:
  - [ ] Document all YAML configuration options
  - [ ] Provide examples for each scanner type
  - [ ] Document environment variable overrides
  - [ ] Document configuration validation rules
- [ ] Document scanner configuration:
  - [ ] List all available scanners
  - [ ] Document scanner-specific parameters
  - [ ] Provide threshold tuning guidance
  - [ ] Document ONNX compatibility per scanner
- [ ] Document presets:
  - [ ] Development preset documentation
  - [ ] Production preset documentation
  - [ ] Testing preset documentation
  - [ ] Guide for creating custom presets
- [ ] Document environment-specific configuration:
  - [ ] Development environment recommendations
  - [ ] Production environment recommendations
  - [ ] Testing environment recommendations
  - [ ] Docker deployment configuration

#### Task 12.2: Security Service Documentation
- [ ] Create security service guide in `docs/guides/infrastructure/SECURITY_SERVICE.md`:
  - [ ] Overview of LLM-Guard integration
  - [ ] Architecture diagram showing components
  - [ ] Security service interface documentation
  - [ ] Scanner factory documentation
- [ ] Document scanners:
  - [ ] PromptInjection scanner usage and tuning
  - [ ] Toxicity scanner usage and tuning
  - [ ] PII detection scanner usage and tuning
  - [ ] Bias scanner usage and tuning
- [ ] Document performance optimization:
  - [ ] ONNX runtime setup and configuration
  - [ ] Caching strategies and tuning
  - [ ] Lazy loading behavior
  - [ ] Performance benchmarking tools
- [ ] Document monitoring and troubleshooting:
  - [ ] Logging configuration and formats
  - [ ] Metrics available and interpretation
  - [ ] Common issues and solutions
  - [ ] Performance tuning guide

#### Task 12.3: Agent Guidance Updates
- [ ] Update `backend/AGENTS.md`:
  - [ ] Add LLM-Guard integration section
  - [ ] Document security service factory pattern
  - [ ] Update infrastructure services list
  - [ ] Add security testing guidance
- [ ] Update root `AGENTS.md`:
  - [ ] Reference LLM-Guard as infrastructure service
  - [ ] Add security configuration guidance
  - [ ] Link to security documentation
  - [ ] Note security as production-ready feature
- [ ] Update testing documentation:
  - [ ] Document security testing patterns
  - [ ] Provide test examples with security
  - [ ] Document mocking strategies for tests
  - [ ] Reference security test suite

#### Task 12.4: API Documentation Updates
- [ ] Update OpenAPI documentation:
  - [ ] Document security scanning in API specs
  - [ ] Add security violation error responses
  - [ ] Document security headers
  - [ ] Add security examples to endpoints
- [ ] Update endpoint documentation:
  - [ ] Note which endpoints use security scanning
  - [ ] Document security validation behavior
  - [ ] Provide example security violations
  - [ ] Document how to handle security errors
- [ ] Create security integration examples:
  - [ ] Example API client handling security errors
  - [ ] Example retry logic for security violations
  - [ ] Example logging security events
  - [ ] Example monitoring security metrics

---

### Deliverable 13: Code Examples and Usage Patterns
**Goal**: Provide clear, tested examples demonstrating security service usage for common scenarios.

#### Task 13.1: Basic Usage Examples
- [ ] Create basic usage example in `app/examples/security/`:
  - [ ] Example: Validating user input before processing
  - [ ] Example: Scanning LLM output before returning
  - [ ] Example: Handling security violations gracefully
  - [ ] Example: Accessing security metrics
- [ ] Create configuration examples:
  - [ ] Example: Development configuration
  - [ ] Example: Production configuration
  - [ ] Example: Custom scanner configuration
  - [ ] Example: Environment-specific overrides
- [ ] Create testing examples:
  - [ ] Example: Testing with security scanning enabled
  - [ ] Example: Testing security violation handling
  - [ ] Example: Mocking security service in tests
  - [ ] Example: Testing different security configurations
- [ ] Document example best practices:
  - [ ] When to use each example pattern
  - [ ] How to adapt examples for specific use cases
  - [ ] Common pitfalls and how to avoid them
  - [ ] Performance considerations for each pattern

#### Task 13.2: Advanced Usage Examples
- [ ] Create advanced usage examples:
  - [ ] Example: Custom scanner implementation
  - [ ] Example: Multi-tier security scanning
  - [ ] Example: Dynamic scanner configuration
  - [ ] Example: Integration with external security services
- [ ] Create performance optimization examples:
  - [ ] Example: ONNX configuration for GPU
  - [ ] Example: Cache tuning for high throughput
  - [ ] Example: Lazy loading optimization
  - [ ] Example: Scanner selection for performance
- [ ] Create integration examples:
  - [ ] Example: Security scanning in middleware
  - [ ] Example: Security scanning in background tasks
  - [ ] Example: Security metrics in monitoring dashboard
  - [ ] Example: Security events in audit logs
- [ ] Document advanced patterns:
  - [ ] Security service customization
  - [ ] Future SaaS integration preparation
  - [ ] Custom error handling strategies
  - [ ] Security testing at scale

#### Task 13.3: Troubleshooting Examples
- [ ] Create troubleshooting guide:
  - [ ] Common issue: ONNX initialization failures
  - [ ] Common issue: Scanner timeout errors
  - [ ] Common issue: False positive detection
  - [ ] Common issue: Performance degradation
- [ ] Provide diagnostic examples:
  - [ ] Example: Checking scanner health
  - [ ] Example: Debugging security violations
  - [ ] Example: Analyzing security metrics
  - [ ] Example: Benchmarking scanner performance
- [ ] Document recovery procedures:
  - [ ] Procedure: Fallback to non-ONNX mode
  - [ ] Procedure: Cache invalidation and reset
  - [ ] Procedure: Scanner reinitialization
  - [ ] Procedure: Emergency security bypass (testing only)
- [ ] Create diagnostic scripts:
  - [ ] Script: Validate security configuration
  - [ ] Script: Test scanner accuracy
  - [ ] Script: Benchmark scanner performance
  - [ ] Script: Generate security report

---

### Deliverable 14: Future SaaS Integration Architecture Documentation
**Goal**: Document architecture for future SaaS integration without implementing it.

#### Task 14.1: SaaS Architecture Design
- [ ] Document SaaS integration interface:
  ```python
  class SaaSSecurityScanner(SecurityService):
      """Future implementation for ProtectAI Guardian or similar."""
      
      async def validate_input(self, text: str) -> SecurityResult:
          # Call SaaS API with fallback to local scanner
          pass
  ```
- [ ] Design fallback strategy:
  - [ ] Primary: SaaS API call
  - [ ] Fallback 1: Cached local results
  - [ ] Fallback 2: Local LLM-Guard scanners
  - [ ] Fallback 3: Allow with warning (configurable)
- [ ] Document configuration:
  - [ ] `SECURITY_MODE=saas` enables SaaS integration
  - [ ] `SAAS_API_KEY` for authentication
  - [ ] `SAAS_API_URL` for endpoint configuration
  - [ ] `SAAS_FALLBACK_MODE` for fallback behavior
- [ ] Document migration path:
  - [ ] How to switch from local to SaaS
  - [ ] Configuration changes required
  - [ ] Testing strategy for SaaS integration
  - [ ] Rollback procedure

#### Task 14.2: SaaS Integration Documentation
- [ ] Create SaaS integration guide in `docs/guides/infrastructure/SECURITY_SAAS_FUTURE.md`:
  - [ ] Overview of SaaS integration architecture
  - [ ] Benefits of SaaS vs local scanning
  - [ ] Implementation requirements (not implemented yet)
  - [ ] Migration strategy for future adoption
- [ ] Document SaaS providers:
  - [ ] ProtectAI Guardian overview
  - [ ] Other potential providers
  - [ ] Comparison of features and pricing
  - [ ] Recommendations for different use cases
- [ ] Document implementation tasks:
  - [ ] API client implementation requirements
  - [ ] Fallback logic implementation
  - [ ] Configuration system updates
  - [ ] Testing requirements
- [ ] Document cost considerations:
  - [ ] SaaS pricing models
  - [ ] Local hosting costs
  - [ ] Performance vs cost trade-offs
  - [ ] Recommendations for different scales

---

## Implementation Notes

### Critical Path Dependencies

**Phase 1 → Phase 2 Dependency**:
Core LLM-Guard integration must be complete before configuration system because configuration drives scanner initialization.

**Phase 2 → Phase 3 Dependency**:
Configuration system must be complete before performance optimization because ONNX and caching settings come from configuration.

**Phase 3 → Phase 4 Dependency**:
Performance optimization should be mostly complete before production integration to ensure middleware has optimized scanners.

**Phase 4 → Phase 5 Dependency**:
Production integration must be complete before comprehensive testing to validate end-to-end functionality.

**All Phases → Phase 6**:
Documentation depends on all implementation phases being complete to ensure examples reflect actual working code.

### Parallel Work Opportunities

**Phase 1 & Configuration Design**: While implementing core integration, can design YAML configuration schema
**Phase 2 & Testing**: While building configuration system, can write configuration tests
**Phase 3 optimization tasks**: ONNX, caching, and lazy loading can be developed in parallel after configuration is stable
**Phase 5 & Phase 6 overlap**: Can start documentation while testing is in progress

### Risk Mitigation Strategies

**Risk: LLM-Guard Memory Footprint Too Large**
- Mitigation: Lazy loading of scanners
- Mitigation: Load only configured scanners
- Validation: Memory benchmarks before production
- Fallback: Document memory requirements and provide minimal configuration

**Risk: ONNX Optimization Not Available on All Platforms**
- Mitigation: Automatic fallback to non-ONNX models
- Validation: Test on macOS, Linux, Windows
- Documentation: Platform-specific configuration guidance
- Fallback: CPU-only mode works everywhere

**Risk: Scanner Latency Exceeds 50ms Target**
- Mitigation: Aggressive caching strategy
- Mitigation: Selective scanner enablement
- Validation: Continuous performance benchmarking
- Fallback: Document acceptable latency ranges per configuration

**Risk: False Positive Rate Too High**
- Mitigation: Configurable thresholds per scanner
- Mitigation: Development vs production preset strategy
- Validation: Extensive effectiveness testing
- Fallback: Document tuning procedures

**Risk: Breaking Changes During Migration**
- Mitigation: Maintain backward-compatible API responses
- Validation: Comprehensive regression testing
- Documentation: Clear migration guide with rollback
- Fallback: Keep custom code commented for quick revert

### Testing Philosophy

**Behavior-Driven Validation**:
- Test that security violations are detected (observable outcome)
- Test that benign content passes (expected behavior)
- Test that errors are handled gracefully (resilience)
- Avoid testing LLM-Guard internals

**Integration Over Unit**:
- Focus on end-to-end security flows
- Test real API requests with security scanning
- Test actual scanner accuracy with real examples
- Mock only external dependencies (Redis, etc.)

**Comprehensive Edge Cases**:
- Test scanner initialization failures
- Test concurrent requests with lazy loading
- Test cache failures don't prevent scanning
- Test graceful degradation across all components

### Success Metrics

**Primary Metric: Complete Custom Code Replacement**
- Target: 100% custom security code removed
- Target: All functionality preserved or improved
- Target: Zero breaking changes to API
- Measurement: Code review and regression tests

**Performance Metrics**:
- Scanner latency: <50ms p95 with ONNX
- Memory usage: <500MB idle, <2GB peak under load
- Cache hit rate: >80% for repeated content
- Application startup: <5s with lazy loading

**Quality Metrics**:
- Test coverage: >90% for infrastructure security code
- Security effectiveness: >95% detection rate for known attacks
- False positive rate: <2% of legitimate requests
- Zero production incidents related to security

**Developer Experience**:
- Migration time: <4 hours for existing application
- Configuration clarity: Developers can configure without support
- Documentation quality: Examples work out of the box
- Troubleshooting: Common issues documented with solutions

### Timeline Estimates

**Phase 1**: 8 hours (LLM-Guard setup and basic integration)
**Phase 2**: 6 hours (Configuration system is straightforward)
**Phase 3**: 8 hours (Performance optimization requires benchmarking)
**Phase 4**: 8 hours (Middleware integration and error handling)
**Phase 5**: 8 hours (Comprehensive testing and validation)
**Phase 6**: 6 hours (Documentation and examples)

**Total**: 44 hours = ~7 working days (1.5 weeks)

**Accelerators**:
- Clear PRD with technical specifications
- Existing infrastructure services provide patterns
- LLM-Guard has good documentation
- App factory pattern provides testing foundation

**Potential Delays**:
- ONNX setup issues on different platforms
- Scanner accuracy tuning taking longer than expected
- Unexpected performance bottlenecks
- Integration issues with existing middleware

### Code Change Estimates

**Files Created** (~15 new files):
- `app/infrastructure/security/scanners/local_scanner.py`: +300 lines
- `app/infrastructure/security/factory.py`: +100 lines
- `app/infrastructure/security/config_loader.py`: +200 lines
- `app/infrastructure/security/cache.py`: +150 lines
- `app/infrastructure/security/logger.py`: +100 lines
- `app/infrastructure/security/metrics.py`: +150 lines
- `app/middleware/security.py`: +200 lines
- `config/security/scanners.yaml`: +100 lines
- `config/security/dev.yaml`: +50 lines
- `config/security/prod.yaml`: +50 lines
- Test files: +1500 lines across 8 test files
- Documentation files: +2000 lines across 6 documentation files

**Files Modified** (~10 files):
- `backend/requirements.txt`: +3 lines
- `backend/Dockerfile`: +5 lines
- `app/core/config.py`: +20 lines (security settings)
- `app/main.py`: +10 lines (middleware registration)
- `app/dependencies.py`: +20 lines (security service injection)
- `backend/AGENTS.md`: +50 lines
- Root `AGENTS.md`: +20 lines

**Files Removed** (custom security code):
- Identify and remove during Phase 5 Task 11.1

**Total LOC**: ~5000 lines (including tests and documentation)
**Net LOC**: ~4500 lines (after removing custom code)

### Validation Checklist

Before declaring Phase complete:
- [ ] All tasks in phase completed and checked off
- [ ] All tests passing in phase scope
- [ ] Code reviewed for quality and standards
- [ ] Documentation updated for phase deliverables
- [ ] No regression in existing functionality
- [ ] Performance benchmarks within acceptable range

Before declaring Project complete:
- [ ] All 6 phases completed
- [ ] Custom security code completely removed
- [ ] All tests passing (unit, integration, effectiveness)
- [ ] Performance targets met (<50ms scanner latency)
- [ ] Documentation complete and accurate
- [ ] Migration guide validated
- [ ] Success metrics achieved
- [ ] Production deployment validated

---

## Additional Considerations

### Production Deployment Checklist

**Pre-Deployment**:
- [ ] Review and customize scanner configuration for production
- [ ] Configure ONNX runtime for production hardware
- [ ] Set up Redis for result caching
- [ ] Configure log aggregation for security events
- [ ] Set up metrics monitoring and alerting
- [ ] Review and adjust scanner thresholds based on testing

**Deployment**:
- [ ] Deploy with lazy loading enabled for faster startup
- [ ] Verify ONNX models downloaded and cached
- [ ] Test scanner initialization and warmup
- [ ] Validate cache connectivity and functionality
- [ ] Verify security headers present in responses
- [ ] Test end-to-end security scanning

**Post-Deployment**:
- [ ] Monitor scanner performance and latency
- [ ] Review security violation logs for false positives
- [ ] Monitor cache hit rate and effectiveness
- [ ] Validate memory usage within expected ranges
- [ ] Review security metrics and adjust thresholds if needed
- [ ] Document any production-specific configuration

### Future Enhancement Opportunities

**Short-term (3-6 months)**:
- Add more scanners (Language, MaliciousURLs, Secrets)
- Implement custom scanner plugins
- Add security violation webhooks
- Create Streamlit dashboard for security monitoring

**Medium-term (6-12 months)**:
- Integrate SaaS security provider (ProtectAI Guardian)
- Add ML-based threshold auto-tuning
- Implement A/B testing for scanner configurations
- Add security violation analytics and trending

**Long-term (12+ months)**:
- Custom fine-tuned security models for specific domains
- Multi-language support for scanners
- Real-time security threat intelligence integration
- Security as a service offering for template users

### Lessons Learned (To Be Completed)

**What Worked Well**:
- (To be filled in during implementation)

**What Could Be Improved**:
- (To be filled in during implementation)

**Key Insights**:
- (To be filled in during implementation)

**Recommendations for Future Projects**:
- (To be filled in during implementation)

---

## 📋 PROJECT STATUS: READY TO BEGIN

**This taskplan provides a comprehensive roadmap for LLM-Guard integration following the proven patterns from the App Factory Pattern implementation.**

**Next Steps:**
1. Review and approve this taskplan
2. Begin Phase 1: Core LLM-Guard Integration
3. Follow deliverable-by-deliverable execution
4. Check off tasks as they are completed
5. Update with lessons learned during implementation

**The template will gain production-ready LLM security powered by industry-standard open-source framework, reducing technical debt while providing comprehensive protection against LLM security threats.**
