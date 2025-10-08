# LLM-Guard Backend Integration - Primary Implementation

## Overview

This PRD focuses on the **Primary Backend Implementation** of LLM-Guard integration for the FastAPI + Streamlit Starter Template. The goal is to replace our custom LLM security validation code with the industry-standard open-source LLM-Guard framework, providing robust protection against prompt injection, toxic content, and data leakage through a proven, maintained solution.

**Priority:** Replace custom security code with LLM-Guard to reduce technical debt and leverage battle-tested security models maintained by the community.

**Scope:** This implementation focuses exclusively on the backend security service integration. All Streamlit-based UI work (dashboards, configuration management, monitoring interfaces) is deferred to a future phase.

## Core Features

### Security Scanner Integration
Replace the existing custom security implementation with LLM-Guard's comprehensive scanner suite:
- **Input Scanners**: PromptInjection, Toxicity, PII detection, Bias, Language validation, Malicious URL detection
- **Output Scanners**: Validate LLM responses before returning to users
- **Async Processing**: All scanning operates asynchronously to maintain API performance
- **Detailed Responses**: Return structured error responses with violation categories, risk scores, and scanner-specific feedback

### Configuration System
YAML-based configuration management with environment variable support:
- **Scanner Configuration**: Define which scanners to enable and their thresholds
- **Environment Overrides**: Development vs production scanner profiles
- **Security Mode**: Support for `SECURITY_MODE` environment variable (default: "local")
- **Factory Pattern**: Unified security service interface with scanner factory for future extensibility

### Performance Optimization
Ensure minimal performance impact through intelligent optimization:
- **ONNX Runtime**: CPU/GPU acceleration for model inference
- **Intelligent Caching**: Cache scan results for repeated content patterns
- **Lazy Loading**: Load models on-demand for faster application startup
- **Target Latency**: Sub-50ms for ONNX-optimized scanners

### Logging and Metrics
Comprehensive audit trail and performance monitoring:
- **Security Event Logging**: Detailed logs of all security decisions
- **Basic Metrics**: Track trigger frequencies, response times, block rates
- **Structured Errors**: Clear, actionable error messages for debugging
- **Audit Compliance**: Maintain logs for compliance purposes

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Application                    │
├─────────────────────────────────────────────────────┤
│         Security Middleware Layer                   │
│  ┌───────────────────────────────────────────────┐  │
│  │   Security Service Interface (Factory)        │  │
│  │                                               │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │   Local LLM-Guard Scanner               │  │  │
│  │  │                                         │  │  │
│  │  │  • Input Scanners (async)               │  │  │
│  │  │  • Output Scanners (async)              │  │  │
│  │  │  • ONNX Runtime Optimization            │  │  │
│  │  │  • Intelligent Caching Layer            │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │                                               │  │
│  │  [Future: SaaS Scanner Implementation]        │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│         Configuration Management                    │
│  • YAML-based scanner config                        │
│  • Environment variable overrides                   │
│  • Validation and error handling                    │
└─────────────────────────────────────────────────────┘
```

### Data Models

```python
# Security Configuration
@dataclass
class SecurityConfig:
    mode: str  # "local" or future "saas"
    scanners: Dict[str, ScannerConfig]
    performance: PerformanceConfig
    logging: LoggingConfig

# Scanner Configuration
@dataclass
class ScannerConfig:
    enabled: bool
    threshold: float
    async_mode: bool
    use_onnx: bool

# Security Result
@dataclass
class SecurityResult:
    is_valid: bool
    risk_score: float
    violations: List[Violation]
    scan_time_ms: float
```

### APIs and Integrations

**Internal Security Service API:**
```python
# Unified interface for all security modes
class SecurityService(Protocol):
    async def validate_input(self, text: str) -> SecurityResult
    async def validate_output(self, text: str) -> SecurityResult
    async def get_metrics(self) -> MetricsSnapshot
```

**LLM-Guard Integration:**
- Install: `llm-guard` and `llm-guard[onnxruntime]`
- Core scanners: Anonymize, PromptInjection, Toxicity, Bias, etc.
- ONNX models for performance optimization

**Middleware Integration:**
- Transparent request/response interception
- Automatic security validation on all LLM endpoints
- Structured error responses on violations

### Infrastructure Requirements

**Dependencies:**
- `llm-guard>=0.3.0` - Core security framework
- `llm-guard[onnxruntime]` - ONNX runtime for optimization
- Compatible with Python 3.9+
- Redis (existing) - For caching scan results

**Configuration Files:**
- `config/security/scanners.yaml` - Scanner configuration
- `config/security/dev.yaml` - Development overrides
- `config/security/prod.yaml` - Production overrides

**Environment Variables:**
```bash
SECURITY_MODE=local  # "local" for this phase, future "saas"
SECURITY_CONFIG_PATH=config/security/scanners.yaml
SECURITY_CACHE_ENABLED=true
SECURITY_ONNX_ENABLED=true
```

## Development Roadmap

### Phase 1: Core Integration (Week 1)

**Objective:** Replace custom security code with LLM-Guard scanners

**Deliverables:**
1. **LLM-Guard Installation & Setup**
   - Install llm-guard with ONNX runtime
   - Create scanner configuration structure
   - Set up model loading and caching

2. **Security Service Interface**
   - Define unified security service protocol
   - Implement factory pattern for scanner creation
   - Create abstraction layer for future extensibility

3. **Local Scanner Implementation**
   - Implement input scanner chain
   - Implement output scanner chain
   - Async processing for all scanners
   - Basic error handling and logging

4. **Configuration Management**
   - YAML-based scanner configuration
   - Environment variable support
   - Configuration validation

**Success Criteria:**
- Custom security code fully replaced with LLM-Guard
- All scanners operate asynchronously
- Basic configuration system functional
- Core tests passing

### Phase 2: Performance & Extensibility (Week 1-2)

**Objective:** Optimize performance and architect for future SaaS integration

**Deliverables:**
1. **ONNX Optimization**
   - Enable ONNX runtime for all compatible scanners
   - GPU acceleration support with CPU fallback
   - Benchmark performance improvements

2. **Intelligent Caching**
   - Implement Redis-based result caching
   - Content hashing for cache keys
   - Configurable TTL and cache invalidation

3. **Lazy Model Loading**
   - On-demand scanner initialization
   - Faster application startup
   - Memory optimization

4. **Extensibility Architecture**
   - Future-proof interface for SaaS integration
   - Environment-based mode switching
   - Graceful degradation patterns (documented for future)

**Success Criteria:**
- Scanner latency <50ms p95 with ONNX
- Cache hit rate >80% for repeated content
- Application startup <5s with lazy loading
- Clear architecture for future SaaS integration

### Phase 3: Production Readiness (Week 2)

**Objective:** Production-ready implementation with comprehensive testing and documentation

**Deliverables:**
1. **Comprehensive Testing**
   - Unit tests for all scanner components
   - Integration tests for middleware
   - Performance benchmarks
   - Security effectiveness tests

2. **Logging & Metrics**
   - Structured security event logging
   - Performance metrics collection
   - Audit trail for compliance
   - Error tracking and reporting

3. **Error Handling**
   - Custom security exceptions
   - Detailed violation responses
   - Fallback strategies
   - Monitoring integration

4. **Documentation**
   - Migration guide from custom to LLM-Guard
   - Configuration reference
   - Performance tuning guide
   - Testing utilities documentation
   - Future SaaS integration architecture

**Success Criteria:**
- 100% test coverage for security components
- All error cases handled gracefully
- Complete migration documentation
- Production deployment checklist ready

## Logical Dependency Chain

**Foundation (Must Build First):**
1. Security service interface and factory pattern
2. YAML configuration system
3. LLM-Guard scanner integration

**Build Upon Foundation:**
4. ONNX optimization (depends on #3)
5. Intelligent caching (depends on #3)
6. Lazy loading (depends on #3)

**Refinement:**
7. Comprehensive error handling (depends on #3-6)
8. Logging and metrics (depends on #3-6)
9. Testing framework (depends on #1-8)

**Pacing Strategy:**
- Week 1: Get basic LLM-Guard integration working (items #1-3)
- Week 1-2: Add performance optimizations (items #4-6)
- Week 2: Production polish and documentation (items #7-9)

Each phase delivers a functional increment that can be tested and validated independently.

## Risks and Mitigations

### Technical Challenges

**Risk:** LLM-Guard model loading increases memory footprint
- **Mitigation:** Lazy loading of scanners, load only what's configured
- **Mitigation:** Monitor memory usage and provide guidelines
- **Mitigation:** Docker container sizing recommendations

**Risk:** ONNX optimization may not work on all platforms
- **Mitigation:** Automatic fallback to non-ONNX models
- **Mitigation:** Platform-specific configuration guidance
- **Mitigation:** Performance benchmarks for both modes

**Risk:** Scanner latency impacts API response times
- **Mitigation:** Aggressive caching strategy
- **Mitigation:** Async processing with proper timeout handling
- **Mitigation:** Performance budgets and monitoring

### MVP Scope Management

**Risk:** Feature creep with UI/dashboard work
- **Mitigation:** Strict scope - backend only, no Streamlit UI
- **Mitigation:** Document future UI features separately
- **Mitigation:** Clear acceptance criteria for "done"

**Risk:** Over-engineering the abstraction layer
- **Mitigation:** Build only what's needed for local mode
- **Mitigation:** Document future SaaS architecture without implementing
- **Mitigation:** Use interface/protocol pattern for clear contracts

**Risk:** Configuration system becomes too complex
- **Mitigation:** Start with simple YAML structure
- **Mitigation:** Add validation to catch errors early
- **Mitigation:** Provide templates for common use cases

### Resource Constraints

**Risk:** Two-week timeline may be tight
- **Mitigation:** Prioritize core replacement over optimization
- **Mitigation:** Phase 3 (production polish) can extend if needed
- **Mitigation:** Clear MVP definition - replace custom code successfully

**Risk:** Testing requires comprehensive security validation
- **Mitigation:** Start with docstring-driven test development
- **Mitigation:** Use LLM-Guard's own test patterns as examples
- **Mitigation:** Focus on integration tests over unit tests initially

## Success Metrics

### Primary Success Criterion
✅ **Custom security validation code completely replaced with LLM-Guard integration**

### Technical Metrics
- **Scanner Latency:** <50ms p95 for ONNX-optimized scanners
- **Memory Footprint:** <500MB idle, <2GB peak under load
- **Cache Hit Rate:** >80% for repeated content patterns
- **Application Startup:** <5s with lazy loading
- **False Positive Rate:** <2% of legitimate requests blocked

### Developer Experience Metrics
- **Migration Effort:** <4 hours to integrate into existing application
- **Configuration Errors:** <5% of deployments require troubleshooting
- **Documentation Quality:** Developers can configure without support

### Operational Metrics
- **Security Event Logging:** 100% of security decisions logged
- **Error Recovery:** Graceful handling of scanner failures
- **Monitoring Integration:** Metrics available in existing observability stack

## Appendix

### Research Findings

**LLM-Guard Evaluation:**
- Mature open-source project with active maintenance
- Comprehensive scanner library (15+ built-in scanners)
- ONNX support for production performance
- Battle-tested by enterprise users
- Strong community support and documentation

**Performance Benchmarks:**
- ONNX optimization: 5-10x speedup vs CPU-only
- Typical latency: 20-40ms per scan with ONNX
- Memory: ~100-200MB per loaded scanner
- Cache effectiveness: 80-90% hit rate in production

### Technical Specifications

**Scanner Configuration Example:**
```yaml
# config/security/scanners.yaml
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

**Environment-Specific Overrides:**
```yaml
# config/security/dev.yaml
input_scanners:
  prompt_injection:
    threshold: 0.6  # More lenient in dev
  
performance:
  onnx_providers: ["CPUExecutionProvider"]  # CPU only in dev

# config/security/prod.yaml
input_scanners:
  prompt_injection:
    threshold: 0.9  # Stricter in production
  
performance:
  onnx_providers: ["CUDAExecutionProvider", "CPUExecutionProvider"]
```

### Future SaaS Integration Architecture

**Note:** This is documented for future implementation, not built in this phase.

```python
# Future SaaS implementation interface (not implemented now)
class SaaSSecurityScanner:
    """Future implementation for ProtectAI Guardian or similar."""
    
    async def validate_input(self, text: str) -> SecurityResult:
        # Call SaaS API
        # Fallback to local on failure
        pass

# Factory pattern enables future switching
def create_security_service(mode: str) -> SecurityService:
    if mode == "local":
        return LocalLLMGuardScanner()
    elif mode == "saas":
        # Future implementation
        return SaaSSecurityScanner()
    else:
        raise ValueError(f"Unknown security mode: {mode}")
```

### Migration from Custom Security

**Mapping Custom → LLM-Guard:**
- Custom prompt injection detection → LLM-Guard PromptInjection scanner
- Custom toxicity filter → LLM-Guard Toxicity scanner
- Custom PII detection → LLM-Guard Anonymize scanner
- Custom content policy → LLM-Guard Bias + Language scanners

**Code Changes Required:**
1. Remove custom security module
2. Install LLM-Guard dependencies
3. Add scanner configuration
4. Update security middleware to use new service
5. Update tests to use LLM-Guard patterns

**Estimated Migration Time:** 2-4 hours for typical application
