---
sidebar_label: Resilience
---
# Resilience Infrastructure Service

The Resilience Infrastructure Service provides production-ready, comprehensive resilience patterns for AI service operations within the FastAPI-Streamlit-LLM Starter Template. This infrastructure service implements circuit breaker patterns, intelligent retry mechanisms, configuration presets, and performance monitoring to handle transient failures and ensure robust service operations.

## Overview

The Resilience Infrastructure Service is a **production-ready infrastructure component** (>90% test coverage) designed to provide comprehensive fault tolerance for AI-powered applications. It follows the template's infrastructure vs domain service separation, serving as a foundational component that domain services leverage for reliable operations under adverse conditions.

### Exception Handling Integration

The Resilience Infrastructure Service is fully integrated with the custom exception handling system, providing:

- **Structured Error Context**: All 38 API endpoints use custom exceptions with rich context data for debugging and monitoring
- **Resilience Classification**: Automatic exception classification determines transient vs permanent failures for proper retry behavior
- **Circuit Breaker Integration**: Exception types directly influence circuit breaker state transitions and recovery patterns
- **Consistent Error Response Format**: Unified error handling across all resilience management endpoints

### Architecture Position

```mermaid
graph TB
    subgraph "Domain Services Layer"
        DS[Text Processor Service] --> RESILIENCE_INFRA[Resilience Infrastructure Service]
        VAL[Response Validator] --> RESILIENCE_INFRA
    end
    
    subgraph "Resilience Infrastructure Service"
        RESILIENCE_INFRA --> ORCHESTRATOR[AI Service Resilience]
        RESILIENCE_INFRA --> CIRCUIT_BREAKER[Circuit Breaker]
        RESILIENCE_INFRA --> RETRY[Retry Logic]
        RESILIENCE_INFRA --> CONFIG[Configuration System]
        
        subgraph "Configuration Management"
            CONFIG --> PRESETS[Preset Manager]
            CONFIG --> VALIDATOR[Config Validator]
            CONFIG --> MONITOR[Config Monitoring]
        end
        
        subgraph "Resilience Patterns"
            ORCHESTRATOR --> STRATEGIES[Strategy Engine]
            CIRCUIT_BREAKER --> METRICS[Circuit Metrics]
            RETRY --> CLASSIFICATION[Exception Classification]
        end
    end
    
    subgraph "Internal API Layer"
        INT_API[Internal API /internal/resilience/] --> RESILIENCE_INFRA
    end
    
    subgraph "External Dependencies"
        RESILIENCE_INFRA --> AI_SERVICES[AI Services]
        RESILIENCE_INFRA --> REDIS["Redis (optional)"]
    end
```

### Key Features

- ✅ **Layered Resilience Architecture**: Circuit breakers, retry logic, and orchestration working together
- ✅ **Preset-Based Configuration**: Simplified configuration reducing 47+ variables to single preset selection
- ✅ **Intelligent Exception Classification**: Automatic categorization of transient vs permanent failures with custom exception integration
- ✅ **Strategy-Based Operations**: Multiple resilience strategies (aggressive, balanced, conservative, critical)
- ✅ **Comprehensive API**: 38 endpoints across 8 focused modules with custom exception handling
- ✅ **Performance Monitoring**: Real-time metrics, benchmarking, and health monitoring with structured error context
- ✅ **Environment Detection**: Automatic environment detection with intelligent preset recommendations
- ✅ **Graceful Degradation**: Fallback mechanisms and safe failure modes with proper exception propagation

## Core Components

### AI Service Resilience (`orchestrator.py`)

Main coordination layer that combines circuit breakers, retry logic, and configuration management into a unified resilience solution.

#### Key Features

| Feature | Description | Benefits |
|---------|-------------|----------|
| **Strategy Management** | Multiple resilience strategies with operation-specific overrides | Flexible fault tolerance based on operation criticality |
| **Decorator Interface** | Easy-to-use decorators for applying resilience patterns | Simple integration with existing code |
| **Fallback Support** | Configurable fallback functions for failed operations | Graceful degradation and user experience preservation |
| **Metrics Aggregation** | Centralized metrics collection and health monitoring | Comprehensive observability and diagnostics |
| **Configuration Hot-Reload** | Runtime configuration updates without restart | Dynamic tuning for optimal performance |

#### Global Decorators

```python
from app.infrastructure.resilience import (
    with_operation_resilience,
    with_aggressive_resilience,
    with_conservative_resilience,
    with_critical_resilience
)

# Operation-specific resilience with automatic strategy selection
@with_operation_resilience("ai_summarize")
async def summarize_text(text: str) -> str:
    """Summarize text with balanced resilience strategy."""
    return await ai_service.summarize(text)

# Fast-fail for development and testing
@with_aggressive_resilience("dev_sentiment", fallback=lambda x: {"sentiment": "neutral"})
async def analyze_sentiment_dev(text: str) -> dict:
    """Quick sentiment analysis with fallback for development."""
    return await ai_service.analyze_sentiment(text)

# High reliability for production critical operations
@with_critical_resilience("prod_qa")
async def answer_question_prod(question: str, context: str) -> str:
    """Production Q&A with maximum reliability."""
    return await ai_service.answer_question(question, context)
```

### Circuit Breaker (`circuit_breaker.py`)

Implements the Circuit Breaker pattern to prevent cascading failures by monitoring service calls and automatically opening circuits when failure rates exceed thresholds.

#### Request Flow Through Resilience System

```mermaid
graph TD
    START[Incoming Request] --> CHECK_CIRCUIT{Circuit Breaker<br/>State Check}
    
    CHECK_CIRCUIT -->|CLOSED<br/>Normal Operation| EXECUTE[Execute Request]
    CHECK_CIRCUIT -->|OPEN<br/>Fail Fast| CIRCUIT_FAIL[Circuit Breaker<br/>Exception]
    CHECK_CIRCUIT -->|HALF-OPEN<br/>Testing| LIMITED_EXECUTE[Limited Execution<br/>Testing Recovery]
    
    EXECUTE --> SUCCESS{Request<br/>Successful?}
    LIMITED_EXECUTE --> SUCCESS
    
    SUCCESS -->|Yes| RECORD_SUCCESS[Record Success<br/>Reset Failure Count]
    SUCCESS -->|No| CLASSIFY{Classify<br/>Exception}
    
    CLASSIFY -->|Transient Error<br/>Network timeout, Service unavailable| RETRY_LOGIC[Enter Retry Logic]
    CLASSIFY -->|Permanent Error<br/>Invalid API key, Bad request| PERMANENT_FAIL[Permanent Failure<br/>No Retry]
    CLASSIFY -->|Rate Limit Error| EXTENDED_RETRY[Extended Backoff<br/>Retry Logic]
    
    RETRY_LOGIC --> RETRY_CHECK{Retry Attempts<br/>Remaining?}
    EXTENDED_RETRY --> RETRY_CHECK
    
    RETRY_CHECK -->|Yes| BACKOFF[Exponential Backoff<br/>with Jitter]
    RETRY_CHECK -->|No| RECORD_FAILURE[Record Failure<br/>Update Circuit Breaker]
    
    BACKOFF --> WAIT[Wait Period<br/>1s → 2s → 4s → 8s]
    WAIT --> EXECUTE
    
    RECORD_SUCCESS --> RETURN_SUCCESS[Return Success<br/>Response]
    RECORD_FAILURE --> THRESHOLD_CHECK{Failure Count ≥<br/>Circuit Threshold?}
    PERMANENT_FAIL --> RETURN_ERROR[Return Error<br/>Response]
    CIRCUIT_FAIL --> FALLBACK{Fallback<br/>Available?}
    
    THRESHOLD_CHECK -->|Yes| OPEN_CIRCUIT[Open Circuit<br/>Start Recovery Timer]
    THRESHOLD_CHECK -->|No| RETURN_ERROR
    
    OPEN_CIRCUIT --> RETURN_ERROR
    
    FALLBACK -->|Yes| EXECUTE_FALLBACK[Execute Fallback<br/>Function]
    FALLBACK -->|No| RETURN_ERROR
    
    EXECUTE_FALLBACK --> RETURN_SUCCESS
    
    subgraph "Circuit Breaker States"
        CLOSED_STATE[CLOSED<br/>Normal Operation]
        OPEN_STATE[OPEN<br/>Fail Fast Mode]
        HALF_OPEN_STATE[HALF-OPEN<br/>Testing Recovery]
    end
    
    subgraph "Retry Strategies"
        AGGRESSIVE[Aggressive<br/>Fast failures, minimal delays]
        BALANCED[Balanced<br/>Moderate retries, reasonable delays]
        CONSERVATIVE[Conservative<br/>Maximum retries, longer delays]
        CRITICAL[Critical<br/>Extensive retries, highest reliability]
    end
```

#### Circuit States & Flow

```mermaid
graph LR
    CLOSED[CLOSED State<br/>Normal Operation] --> OPEN[OPEN State<br/>Fail Fast]
    OPEN --> HALF_OPEN[HALF-OPEN State<br/>Testing Recovery]
    HALF_OPEN --> CLOSED
    HALF_OPEN --> OPEN
    
    CLOSED --> |"Failure Count ≥ Threshold"| OPEN
    OPEN --> |"Recovery Timeout Elapsed"| HALF_OPEN
    HALF_OPEN --> |"Success"| CLOSED
    HALF_OPEN --> |"Failure"| OPEN
```

#### Configuration & Usage

```python
from app.infrastructure.resilience.circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig
)

# Create circuit breaker with custom configuration
config = CircuitBreakerConfig(
    failure_threshold=5,      # Failures before opening circuit
    recovery_timeout=60,      # Seconds to wait before half-open state
    half_open_max_calls=1     # Max calls allowed in half-open state
)

circuit_breaker = EnhancedCircuitBreaker(
    failure_threshold=config.failure_threshold,
    recovery_timeout=config.recovery_timeout,
    name="ai_service_circuit_breaker"
)

# Use circuit breaker protection
try:
    result = circuit_breaker.call(ai_service_function, param1, param2)
    logger.info(f"Success rate: {circuit_breaker.metrics.success_rate}%")
except Exception as e:
    logger.error(f"Circuit breaker protected call failed: {e}")
```

#### Performance Characteristics

| Metric | Target | Typical Performance |
|--------|--------|-------------------|
| **Call Overhead** | <1ms | ~0.1-0.5ms |
| **State Check** | <0.1ms | ~0.01-0.05ms |
| **Metrics Update** | <0.5ms | ~0.1-0.3ms |
| **Memory Usage** | <1MB per breaker | ~100-500KB typical |

### Retry Logic (`retry.py`)

Intelligent retry logic with exception classification, exponential backoff, and jitter to handle transient failures effectively.

#### Exception Classification System

The retry system automatically classifies exceptions to determine retry eligibility:

```python
from app.infrastructure.resilience.retry import (
    classify_exception,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError
)

# Automatic exception classification
try:
    result = await risky_ai_operation()
except Exception as e:
    if classify_exception(e):
        # Transient error - will be retried automatically
        logger.info(f"Transient error detected: {e}")
    else:
        # Permanent error - won't be retried
        logger.error(f"Permanent error detected: {e}")
        raise
```

#### Exception Hierarchy

| Exception Type | Retry Behavior | Use Cases |
|---------------|----------------|-----------|
| **TransientAIError** | Automatic retry with backoff | Network timeouts, temporary service issues |
| **PermanentAIError** | No retry | Invalid API keys, malformed requests |
| **RateLimitError** | Retry with extended backoff | API rate limiting |
| **ServiceUnavailableError** | Retry with circuit breaker coordination | Service maintenance, overload |

#### Retry Configuration

```python
from app.infrastructure.resilience.retry import RetryConfig

config = RetryConfig(
    max_attempts=3,              # Maximum retry attempts
    max_delay_seconds=60,        # Maximum delay between retries
    exponential_multiplier=1.0,  # Backoff multiplier
    exponential_min=2.0,         # Minimum delay
    exponential_max=10.0,        # Maximum delay
    jitter=True,                 # Add randomization
    jitter_max=2.0              # Maximum jitter
)
```

### Configuration Preset System (`config_presets.py`)

Predefined configuration templates and intelligent environment-based preset recommendations for different deployment scenarios.

#### Available Presets

| Preset | Best For | Retry Attempts | Circuit Breaker Threshold | Recovery Timeout | Default Strategy |
|--------|----------|----------------|---------------------------|------------------|------------------|
| **simple** | General use, testing, staging | 3 | 5 failures | 60 seconds | Balanced |
| **development** | Local development, fast feedback | 2 | 3 failures | 30 seconds | Aggressive |
| **production** | Production workloads, high reliability | 5 | 10 failures | 120 seconds | Conservative |

#### Resilience Strategies

Each preset employs different resilience strategies optimized for specific scenarios:

```python
from app.infrastructure.resilience.config_presets import ResilienceStrategy

# Available strategies with characteristics
strategies = {
    ResilienceStrategy.AGGRESSIVE: {
        "description": "Fast failures, minimal delays, quick recovery",
        "use_case": "Development, testing, fast feedback loops",
        "characteristics": ["Low latency", "Quick failure detection", "Minimal retry delays"]
    },
    ResilienceStrategy.BALANCED: {
        "description": "Moderate approach balancing speed and reliability",
        "use_case": "General production use, default choice",
        "characteristics": ["Balanced performance", "Good for most scenarios", "Reasonable fault tolerance"]
    },
    ResilienceStrategy.CONSERVATIVE: {
        "description": "Higher reliability with longer delays and more retries",
        "use_case": "Critical operations, high reliability requirements",
        "characteristics": ["Maximum fault tolerance", "Higher latency tolerance", "Comprehensive retry coverage"]
    },
    ResilienceStrategy.CRITICAL: {
        "description": "Maximum resilience for mission-critical operations",
        "use_case": "Business-critical operations, maximum uptime required",
        "characteristics": ["Highest reliability", "Extensive retry attempts", "Long recovery timeouts"]
    }
}
```

#### Environment Detection & Recommendations

```python
from app.infrastructure.resilience.config_presets import preset_manager

# Automatic environment detection with intelligent recommendations
recommendation = preset_manager.recommend_preset_with_details()
print(f"Detected Environment: {recommendation.environment_detected}")
print(f"Recommended Preset: {recommendation.preset_name}")
print(f"Confidence: {recommendation.confidence}")
print(f"Reasoning: {recommendation.reasoning}")

# Use recommended preset
preset = preset_manager.get_preset(recommendation.preset_name)
resilience_config = preset.to_resilience_config()
```

### Configuration Validation (`config_validator.py`)

Comprehensive JSON schema validation with security checks, rate limiting, and configuration templates for safe custom configurations.

#### Security Features

| Feature | Description | Protection |
|---------|-------------|-----------|
| **Content Size Limits** | 4KB maximum configuration size | Prevents resource exhaustion |
| **Pattern-Based Filtering** | Forbidden content detection | Blocks malicious patterns |
| **Unicode Character Filtering** | Control character removal | Prevents injection attacks |
| **Field Whitelisting** | Strict field validation | Ensures configuration integrity |
| **Rate Limiting** | 60 validations/minute per IP | Prevents abuse |

#### Validation Usage

```python
from app.infrastructure.resilience.config_validator import (
    ResilienceConfigValidator,
    ValidationResult
)

# Validate custom configuration
validator = ResilienceConfigValidator()
custom_config = {
    "retry_attempts": 7,
    "circuit_breaker_threshold": 12,
    "recovery_timeout": 180,
    "default_strategy": "conservative"
}

result: ValidationResult = validator.validate_custom_config(custom_config)

if result.is_valid:
    print("Configuration is valid")
    print(f"Warnings: {result.warnings}")
    print(f"Suggestions: {result.suggestions}")
else:
    print(f"Validation errors: {result.errors}")
```

### Performance Monitoring (`config_monitoring.py`)

Real-time monitoring of configuration usage patterns, performance metrics, and operational health with alerting capabilities.

#### Metrics Tracked

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Usage Analytics** | Preset usage frequency, operation patterns | Optimize preset configurations |
| **Performance Monitoring** | Load times, configuration processing | Identify performance bottlenecks |
| **Alert System** | Threshold violations, anomaly detection | Proactive issue detection |
| **Trend Analysis** | Historical patterns, usage evolution | Capacity planning and optimization |

```python
from app.infrastructure.resilience.config_monitoring import ConfigurationMetricsCollector

# Set up comprehensive monitoring
collector = ConfigurationMetricsCollector(
    max_events=50000, 
    retention_hours=48
)

# Track configuration operations
with collector.track_config_operation("load_preset", "production"):
    preset = preset_manager.get_preset("production")

# Get usage statistics and insights
stats = collector.get_usage_statistics()
print(f"Most used preset: {stats.most_used_preset}")
print(f"Average load time: {stats.avg_load_time_ms:.2f}ms")
print(f"Current alerts: {len(stats.active_alerts)}")

# Export metrics for external monitoring
metrics_json = collector.export_metrics("json", time_window_hours=24)
```

## Exception Classification for Resilience

The Resilience Infrastructure Service integrates with the custom exception handling system to provide intelligent error classification and response strategies:

### Transient vs Permanent Error Classification

```python
from app.core.exceptions import (
    ValidationError,
    BusinessLogicError, 
    InfrastructureError,
    classify_ai_exception
)

# Transient errors - eligible for retry with circuit breaker coordination
transient_errors = [
    InfrastructureError,  # Service failures, connectivity issues
    # Network timeouts, temporary service unavailability
    # Redis connection failures, performance monitoring issues
]

# Permanent errors - no retry, immediate failure
permanent_errors = [
    ValidationError,      # Configuration format errors, invalid parameters
    BusinessLogicError,   # Resource not found, invalid state transitions
    # Authentication/authorization failures
]
```

### Exception-Driven Resilience Behavior

```mermaid
graph TD
    ERROR[Exception Raised] --> CLASSIFY{Exception\nClassification}
    
    CLASSIFY -->|ValidationError<br/>BusinessLogicError| PERMANENT[Permanent Error]
    CLASSIFY -->|InfrastructureError<br/>ServiceUnavailable| TRANSIENT[Transient Error]
    
    PERMANENT --> NO_RETRY[No Retry\nImmediate Failure]
    TRANSIENT --> CIRCUIT_CHECK{Circuit Breaker\nState}
    
    CIRCUIT_CHECK -->|CLOSED| RETRY_LOGIC[Apply Retry Logic]
    CIRCUIT_CHECK -->|OPEN| CIRCUIT_FAIL[Circuit Breaker\nException]
    CIRCUIT_CHECK -->|HALF-OPEN| LIMITED_RETRY[Limited Retry\nTesting]
    
    RETRY_LOGIC --> BACKOFF[Exponential Backoff\nwith Jitter]
    LIMITED_RETRY --> BACKOFF
    
    BACKOFF --> SUCCESS_CHECK{Retry\nSuccessful?}
    SUCCESS_CHECK -->|Yes| RECORD_SUCCESS[Record Success\nReset Circuit]
    SUCCESS_CHECK -->|No| UPDATE_CIRCUIT[Update Circuit\nBreaker Metrics]
    
    UPDATE_CIRCUIT --> THRESHOLD_CHECK{Failure Count ≥\nThreshold?}
    THRESHOLD_CHECK -->|Yes| OPEN_CIRCUIT[Open Circuit\nStart Recovery]
    THRESHOLD_CHECK -->|No| RETRY_LOGIC
    
    subgraph "Exception Context Data"
        CTX_VALIDATION[ValidationError Context:<br/>• endpoint<br/>• validation_errors<br/>• config_type]
        CTX_BUSINESS[BusinessLogicError Context:<br/>• resource_id<br/>• available_options<br/>• current_state]
        CTX_INFRA[InfrastructureError Context:<br/>• service_status<br/>• performance_metrics<br/>• retry_count]
    end
```

### Context-Rich Error Handling

All resilience API endpoints provide structured error context for debugging and monitoring:

```python
# Configuration validation error with detailed context
raise ValidationError(
    "Invalid resilience configuration format",
    context={
        "endpoint": "validate_config",
        "operation": "schema_validation",
        "config_type": "custom_resilience_config",
        "validation_errors": [
            "retry_attempts must be between 1 and 10",
            "circuit_breaker_threshold cannot be negative"
        ],
        "provided_config_size_bytes": 256,
        "max_config_size_bytes": 4096
    }
)

# Circuit breaker operation error with state information
raise InfrastructureError(
    "Circuit breaker reset failed - breaker not found",
    context={
        "endpoint": "reset_circuit_breaker", 
        "operation": "circuit_breaker_reset",
        "breaker_name": "ai_text_processing",
        "available_breakers": ["ai_service", "cache_operations"],
        "current_circuit_states": {
            "ai_service": "CLOSED",
            "cache_operations": "HALF_OPEN"
        }
    }
)

# Performance monitoring error with execution metrics
raise InfrastructureError(
    "Performance benchmark execution exceeded timeout",
    context={
        "endpoint": "run_benchmark",
        "operation": "comprehensive_performance_test",
        "benchmark_type": "resilience_patterns",
        "execution_time_ms": 45000,
        "timeout_limit_ms": 30000,
        "completed_iterations": 150,
        "target_iterations": 1000,
        "memory_usage_mb": 89.5
    }
)
```

## Comprehensive API Reference

The Resilience Infrastructure Service provides **38 endpoints** across **8 focused modules** through the Internal API (`/internal/resilience/`). All endpoints implement custom exception handling with structured error contexts.

### Configuration Management API

#### Configuration Validation (`/internal/resilience/config/`)

**Validate Custom Configuration**:
```http
POST /internal/resilience/config/validate
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "configuration": {
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "timeout_seconds": 30
  }
}
```

**Raises:**
- `ValidationError`: Invalid configuration format, missing required fields, parameter out of range
- `InfrastructureError`: Validation service failure, schema processing error

**Enhanced Security Validation**:
```http
POST /internal/resilience/config/validate-secure
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "configuration": {
    "retry_attempts": 5,
    "circuit_breaker_threshold": 8,
    "default_strategy": "conservative"
  }
}
```

**Raises:**
- `ValidationError`: Configuration exceeds size limits, contains forbidden patterns, invalid field values
- `InfrastructureError`: Security validation system failure, rate limiting service error

**Response Example**:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Consider adding exponential backoff configuration"],
  "suggestions": ["Add jitter_enabled: true for better load distribution"],
  "security_info": {
    "size_bytes": 128,
    "max_size_bytes": 4096,
    "field_count": 3,
    "validation_timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Configuration Presets (`/internal/resilience/config/`)

**List All Presets**:
```http
GET /internal/resilience/config/presets
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Preset loading failure, configuration system unavailable

**Get Preset Details**:
```http
GET /internal/resilience/config/presets/{preset_name}
Authorization: Bearer your-api-key
```

**Raises:**
- `BusinessLogicError`: Preset not found, invalid preset name
- `InfrastructureError`: Preset retrieval system failure

**Environment-Based Recommendation**:
```http
GET /internal/resilience/config/recommend-preset/{environment}
Authorization: Bearer your-api-key
```

**Raises:**
- `ValidationError`: Invalid environment parameter
- `BusinessLogicError`: No suitable preset found for environment
- `InfrastructureError`: Recommendation engine failure

**Auto-Detect Recommendation**:
```http
GET /internal/resilience/config/recommend-preset-auto
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Environment detection failure, recommendation system unavailable

**Response Example**:
```json
{
  "environment_detected": "production (auto-detected)",
  "recommended_preset": "production",
  "confidence": 0.95,
  "reasoning": "High-reliability requirements detected for production environment",
  "available_presets": ["simple", "development", "production"],
  "auto_detected": true
}
```

#### Configuration Templates (`/internal/resilience/config/`)

**List All Templates**:
```http
GET /internal/resilience/config/templates
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Template system failure, configuration templates unavailable

**Validate Template-Based Configuration**:
```http
POST /internal/resilience/config/validate-template
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "template_name": "production",
  "overrides": {
    "retry_attempts": 5
  }
}
```

**Raises:**
- `ValidationError`: Invalid template name, malformed override values
- `BusinessLogicError`: Template not found, incompatible override parameters
- `InfrastructureError`: Template processing system failure

### Operations & Monitoring API

#### Health & Metrics (`/internal/resilience/`)

**Core Health Check**:
```http
GET /internal/resilience/health
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Health monitoring system failure, metrics collection unavailable

**Detailed Health Status**:
```http
GET /internal/resilience/health/detailed
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Detailed health assessment failure, system monitoring error

**Service Metrics**:
```http
GET /internal/resilience/metrics
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Metrics collection failure, monitoring system unavailable

**Operation-Specific Metrics**:
```http
GET /internal/resilience/metrics/{operation_name}
Authorization: Bearer your-api-key
```

**Raises:**
- `ValidationError`: Invalid operation name parameter
- `BusinessLogicError`: Operation not found, no metrics available for operation
- `InfrastructureError`: Metrics retrieval system failure

#### Circuit Breaker Management (`/internal/resilience/`)

**List Circuit Breakers**:
```http
GET /internal/resilience/circuit-breakers
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Circuit breaker monitoring failure, state retrieval error

**Response Example**:
```json
{
  "circuit_breakers": {
    "text_processing": {
      "state": "closed",
      "failure_count": 2,
      "threshold": 5,
      "recovery_timeout": 60,
      "last_failure": "2024-01-15T10:25:00Z"
    }
  },
  "total_count": 1,
  "healthy_count": 1,
  "open_count": 0
}
```

**Get Circuit Breaker Details**:
```http
GET /internal/resilience/circuit-breakers/{breaker_name}
Authorization: Bearer your-api-key
```

**Raises:**
- `BusinessLogicError`: Circuit breaker not found, invalid breaker name
- `InfrastructureError`: Circuit breaker state retrieval failure

**Reset Circuit Breaker**:
```http
POST /internal/resilience/circuit-breakers/{breaker_name}/reset
Authorization: Bearer your-api-key
```

**Raises:**
- `BusinessLogicError`: Circuit breaker not found, reset not allowed in current state
- `InfrastructureError`: Circuit breaker reset operation failure

#### Monitoring & Analytics (`/internal/resilience/monitoring/`)

**Usage Statistics**:
```http
GET /internal/resilience/monitoring/usage-statistics
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Usage statistics collection failure, monitoring system error

**Preset Trends**:
```http
GET /internal/resilience/monitoring/preset-trends/{preset_name}
Authorization: Bearer your-api-key
```

**Raises:**
- `ValidationError`: Invalid preset name parameter
- `BusinessLogicError`: Preset not found, insufficient trend data available
- `InfrastructureError`: Trend analysis system failure

**Performance Metrics**:
```http
GET /internal/resilience/monitoring/performance-metrics
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Performance metrics collection failure, monitoring system unavailable

**Alerts**:
```http
GET /internal/resilience/monitoring/alerts
Authorization: Bearer your-api-key
```

**Raises:**
- `InfrastructureError`: Alert system failure, notification service unavailable

#### Performance Benchmarking (`/internal/resilience/performance/`)

**Run Performance Benchmark**:
```http
POST /internal/resilience/performance/benchmark
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "operation_name": "text_processing",
  "iterations": 1000,
  "concurrency": 10
}
```

**Raises:**
- `ValidationError`: Invalid benchmark parameters, iterations/concurrency out of range
- `BusinessLogicError`: Operation not found, benchmark not supported for operation
- `InfrastructureError`: Benchmark execution failure, performance testing system error

**Response Example**:
```json
{
  "benchmark_id": "bench_20240115_103000",
  "operation_name": "text_processing",
  "results": {
    "total_time": 45.2,
    "average_response_time": 0.045,
    "requests_per_second": 22.1,
    "success_rate": 0.998,
    "p95_response_time": 0.089
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration Patterns

### Domain Service Integration

The Resilience Infrastructure Service is designed to be used by domain services:

```python
from app.infrastructure.resilience import ai_resilience

class AITextProcessingService:
    """Domain service using resilience infrastructure."""
    
    def __init__(self):
        # Resilience is automatically configured from environment/presets
        pass
    
    @ai_resilience.with_operation_resilience("text_summarization")
    async def summarize(self, text: str) -> str:
        """Summarize text with automatic resilience."""
        return await self._call_ai_service("summarize", text)
    
    @ai_resilience.with_operation_resilience("sentiment_analysis") 
    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment with automatic resilience."""
        return await self._call_ai_service("sentiment", text)
    
    async def _call_ai_service(self, operation: str, text: str):
        # Your AI service implementation here
        pass
```

### FastAPI Dependency Injection

```python
from app.infrastructure.resilience import AIServiceResilience
from fastapi import Depends

async def get_resilience_service() -> AIServiceResilience:
    """Factory function for dependency injection."""
    return AIServiceResilience()

@app.post("/v1/text_processing/process")
async def process_text(
    request: ProcessRequest,
    resilience: AIServiceResilience = Depends(get_resilience_service)
):
    """Process text with resilience patterns."""
    
    @resilience.with_operation_resilience("api_text_processing")
    async def process():
        return await ai_service.process(request.text)
    
    return await process()
```

### Environment-Based Configuration

```python
import os
from app.infrastructure.resilience import preset_manager

# Automatic configuration based on environment
if os.getenv("RESILIENCE_PRESET"):
    # Use preset-based configuration (recommended)
    preset_name = os.getenv("RESILIENCE_PRESET", "simple")
    preset = preset_manager.get_preset(preset_name)
    resilience_config = preset.to_resilience_config()
elif os.getenv("RESILIENCE_CUSTOM_CONFIG"):
    # Use custom JSON configuration
    import json
    custom_config = json.loads(os.getenv("RESILIENCE_CUSTOM_CONFIG"))
    # Apply custom configuration
else:
    # Use automatic recommendation
    recommendation = preset_manager.recommend_preset_with_details()
    preset = preset_manager.get_preset(recommendation.preset_name)
    resilience_config = preset.to_resilience_config()
```

## Configuration Management

### Preset-Based Configuration (Recommended)

The resilience system uses a **preset-based configuration approach** that automatically detects environment and recommends appropriate settings:

```bash
# Set a single environment variable based on your deployment context
export RESILIENCE_PRESET=simple         # For general use, testing, staging
export RESILIENCE_PRESET=development    # For local development, fast feedback
export RESILIENCE_PRESET=production     # For production workloads, high reliability
```

### Environment Variables

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `RESILIENCE_PRESET` | `simple` | Resilience configuration preset | `simple`, `development`, `production` |
| `RESILIENCE_CUSTOM_CONFIG` | None | Custom JSON configuration | JSON string with custom settings |

### Custom Configuration Override

For advanced users who need fine-tuned control:

```bash
# Basic custom configuration
export RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 4,
  "circuit_breaker_threshold": 8,
  "recovery_timeout": 90,
  "default_strategy": "balanced"
}'

# Advanced custom configuration with operation-specific overrides
export RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 4,
  "circuit_breaker_threshold": 8,
  "recovery_timeout": 90,
  "default_strategy": "conservative",
  "operation_overrides": {
    "qa": "critical",
    "sentiment": "aggressive",
    "summarize": "balanced"
  },
  "exponential_multiplier": 1.5,
  "exponential_min": 2.0,
  "exponential_max": 30.0,
  "jitter_enabled": true,
  "jitter_max": 3.0
}'
```

### Configuration Schema

Valid configuration parameters:

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `retry_attempts` | integer | 1-10 | Number of retry attempts |
| `circuit_breaker_threshold` | integer | 1-20 | Failures before circuit opens |
| `recovery_timeout` | integer | 10-300 | Circuit recovery time (seconds) |
| `default_strategy` | string | aggressive, balanced, conservative, critical | Default resilience strategy |
| `operation_overrides` | object | - | Strategy overrides per operation |
| `exponential_multiplier` | number | 0.1-5.0 | Exponential backoff multiplier |
| `exponential_min` | number | 0.5-10.0 | Minimum backoff delay |
| `exponential_max` | number | 5.0-120.0 | Maximum backoff delay |
| `jitter_enabled` | boolean | - | Enable jitter in delays |
| `jitter_max` | number | 0.1-10.0 | Maximum jitter value |

## Performance Characteristics

### Benchmarking System

The resilience infrastructure includes comprehensive performance benchmarking:

```python
from app.infrastructure.resilience.performance_benchmarks import (
    ConfigurationPerformanceBenchmark
)

# Run performance benchmarks
benchmark = ConfigurationPerformanceBenchmark()
suite = benchmark.run_comprehensive_benchmark()

print(f"Overall pass rate: {suite.pass_rate:.1f}%")
for result in suite.results:
    print(f"{result.operation}: {result.avg_duration_ms:.2f}ms avg")
```

### Performance Targets

| Component | Target Performance | Actual Performance | Complexity |
|-----------|-------------------|-------------------|------------|
| **Preset Loading** | <10ms | ~2-5ms typical | O(1) |
| **Configuration Loading** | <100ms | ~15-50ms typical | O(n) |
| **Service Initialization** | <200ms | ~50-150ms typical | O(n) |
| **Validation** | <50ms | ~10-30ms typical | O(n) |
| **Circuit Breaker Call** | <1ms overhead | ~0.1-0.5ms typical | O(1) |

### Memory Usage

- **Base Memory**: ~2-5MB for core resilience infrastructure
- **Per-Operation**: ~100-500KB additional memory per registered operation
- **Metrics Storage**: ~1-10MB depending on retention settings
- **Configuration Cache**: ~50-200KB per preset configuration

### Optimization Features

- **Pre-compiled Patterns**: Exception patterns compiled once for efficiency
- **Connection Pooling**: Efficient resource reuse
- **Batch Operations**: Multiple operations in single request
- **Intelligent Eviction**: LRU with access pattern optimization
- **Streaming Processing**: Memory-efficient processing for large configurations

## Error Response Format

All Resilience API endpoints return consistent error responses using the custom exception system:

### Standard Error Response Structure

```json
{
  "error": "Human-readable error message",
  "error_code": "ValidationError",
  "context": {
    "endpoint": "validate_config",
    "operation": "schema_validation",
    "request_id": "req_abc12345",
    "timestamp": "2025-01-04T12:30:45.123Z",
    "additional_context": "Endpoint-specific debugging information"
  }
}
```

### Resilience-Specific Error Examples

**Configuration Validation Error (400)**:
```json
{
  "error": "Invalid resilience configuration format",
  "error_code": "ValidationError",
  "context": {
    "endpoint": "validate_config",
    "operation": "schema_validation",
    "config_type": "custom_resilience_config",
    "validation_errors": [
      "retry_attempts must be between 1 and 10",
      "circuit_breaker_threshold cannot be negative"
    ],
    "provided_config_size_bytes": 256,
    "max_config_size_bytes": 4096
  }
}
```

**Circuit Breaker Operation Error (422)**:
```json
{
  "error": "Circuit breaker not found",
  "error_code": "BusinessLogicError",
  "context": {
    "endpoint": "reset_circuit_breaker",
    "operation": "circuit_breaker_reset",
    "breaker_name": "nonexistent_breaker",
    "available_breakers": ["ai_service", "cache_operations"],
    "current_circuit_states": {
      "ai_service": "CLOSED",
      "cache_operations": "HALF_OPEN"
    }
  }
}
```

**Performance Monitoring Error (500)**:
```json
{
  "error": "Performance benchmark execution failed",
  "error_code": "InfrastructureError",
  "context": {
    "endpoint": "run_benchmark",
    "operation": "comprehensive_performance_test",
    "benchmark_type": "resilience_patterns",
    "execution_time_ms": 15000,
    "failure_reason": "Memory allocation exceeded limits",
    "memory_usage_mb": 512.7,
    "system_resources": {
      "cpu_usage_percent": 85.2,
      "available_memory_mb": 128.5
    }
  }
}
```

## Error Handling & Resilience Integration

### Exception Classification for Retry Logic

The system provides comprehensive error handling with intelligent classification that directly integrates with resilience patterns:

```python
from app.core.exceptions import (
    classify_ai_exception,
    ValidationError,
    BusinessLogicError,
    InfrastructureError
)

try:
    result = await risky_ai_operation()
except (ValidationError, BusinessLogicError) as e:
    # Permanent errors - do not retry
    logger.error(f"Permanent error detected: {e}")
    # Circuit breaker will not count this as a failure
    raise
except InfrastructureError as e:
    # Transient error - eligible for retry
    logger.info(f"Transient error detected: {e}")
    # Circuit breaker will count this failure and apply retry logic
    if classify_ai_exception(e):
        await apply_retry_with_backoff()
    raise
```

### Circuit Breaker Exception Integration

```python
from app.infrastructure.resilience.circuit_breaker import EnhancedCircuitBreaker
from app.core.exceptions import InfrastructureError

cb = EnhancedCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="ai_service_protection"
)

try:
    result = cb.call(ai_service_function, param1, param2)
except InfrastructureError as e:
    # Circuit breaker state transitions based on exception type
    if e.context.get("circuit_breaker_triggered"):
        logger.warning(f"Circuit breaker opened: {e}")
        # Implement fallback logic
        return await fallback_operation()
    else:
        # Service failure, circuit breaker tracks this
        logger.error(f"Service failure tracked by circuit breaker: {e}")
        raise
```

### Graceful Degradation with Exception Handling

```python
from app.infrastructure.resilience import with_operation_resilience
from app.core.exceptions import InfrastructureError, BusinessLogicError

@with_operation_resilience("ai_processing", fallback=safe_fallback_function)
async def ai_processing_with_fallback(text: str) -> str:
    """AI processing with automatic fallback on failure."""
    try:
        return await ai_service.process(text)
    except BusinessLogicError:
        # Don't trigger circuit breaker for business logic errors
        raise
    except InfrastructureError as e:
        # Let resilience system handle infrastructure failures
        logger.warning(f"Infrastructure failure in AI processing: {e}")
        raise

def safe_fallback_function(text: str, exception: Exception = None) -> str:
    """Safe fallback when AI service fails with exception context."""
    fallback_context = {
        "fallback_triggered": True,
        "original_exception": str(exception) if exception else None,
        "fallback_timestamp": "2025-01-04T12:30:45.123Z"
    }
    
    if isinstance(exception, InfrastructureError):
        # Infrastructure failure - service temporarily unavailable
        return f"Service temporarily unavailable. Please try again later."
    else:
        # Generic fallback
        return f"Processing temporarily unavailable for: {text[:50]}..."
```

### Circuit Breaker Protection with Custom Exceptions

```python
from app.infrastructure.resilience.circuit_breaker import EnhancedCircuitBreaker
from app.core.exceptions import InfrastructureError, BusinessLogicError, ValidationError

# Create circuit breaker with exception-aware behavior
cb = EnhancedCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="ai_service_protection"
)

# Protected service call with structured exception handling
try:
    result = cb.call(ai_service_function, param1, param2)
    logger.info(f"Success rate: {cb.metrics.success_rate}%")
except InfrastructureError as e:
    # Infrastructure errors count towards circuit breaker failures
    logger.error(
        f"Infrastructure failure tracked by circuit breaker: {e}",
        extra={
            "circuit_breaker": cb.name,
            "failure_count": cb.metrics.failure_count,
            "state": cb.state,
            "context": e.context
        }
    )
    
    # Enrich exception context with circuit breaker information
    e.context.update({
        "circuit_breaker_name": cb.name,
        "circuit_breaker_state": cb.state,
        "failure_count": cb.metrics.failure_count,
        "success_rate": cb.metrics.success_rate
    })
    raise
except (BusinessLogicError, ValidationError) as e:
    # Business logic and validation errors don't affect circuit breaker
    logger.warning(f"Non-infrastructure error (not counted by circuit breaker): {e}")
    raise
except Exception as e:
    # Convert unexpected exceptions to InfrastructureError
    raise InfrastructureError(
        f"Unexpected error in circuit breaker protected operation: {str(e)}",
        context={
            "circuit_breaker_name": cb.name,
            "circuit_breaker_state": cb.state,
            "original_exception": str(e),
            "circuit_breaker_metrics": cb.metrics.to_dict()
        }
    )
```

## Migration Guide

### From Legacy Environment Variables to Presets

1. **Analyze Current Configuration**:
```bash
# Use the Internal API to check current configuration
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/internal/resilience/config/presets

# Get environment-based recommendation
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/internal/resilience/config/recommend-preset-auto
```

2. **Update Configuration**:
```bash
# Set environment variable for preset-based configuration
export RESILIENCE_PRESET=production

# Remove legacy environment variables
unset RETRY_MAX_ATTEMPTS
unset CIRCUIT_BREAKER_FAILURE_THRESHOLD
unset CIRCUIT_BREAKER_RECOVERY_TIMEOUT
unset DEFAULT_RESILIENCE_STRATEGY
# ... remove other legacy variables
```

3. **Verify Migration**:
```bash
# Check current configuration via Internal API
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/internal/resilience/health/detailed
```

### Legacy Variable Mapping

| Legacy Variable | Preset Parameter | Notes |
|-----------------|------------------|-------|
| `RETRY_MAX_ATTEMPTS` | `retry_attempts` | Direct mapping |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `circuit_breaker_threshold` | Direct mapping |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | `recovery_timeout` | Direct mapping |
| `DEFAULT_RESILIENCE_STRATEGY` | `default_strategy` | Direct mapping |
| `SUMMARIZE_RESILIENCE_STRATEGY` | `operation_overrides.summarize` | Operation-specific |
| `SENTIMENT_RESILIENCE_STRATEGY` | `operation_overrides.sentiment` | Operation-specific |
| `QA_RESILIENCE_STRATEGY` | `operation_overrides.qa` | Operation-specific |

## Advanced Features

### Custom Strategy Definition

```python
from app.infrastructure.resilience.config_presets import ResiliencePreset, ResilienceStrategy

# Define custom preset
custom_preset = ResiliencePreset(
    name="HighThroughput",
    description="Optimized for high throughput scenarios",
    retry_attempts=2,
    circuit_breaker_threshold=20,
    recovery_timeout=30,
    default_strategy=ResilienceStrategy.AGGRESSIVE,
    operation_overrides={
        "batch_processing": ResilienceStrategy.BALANCED
    },
    environment_contexts=["production", "staging"]
)

# Register custom preset
preset_manager.presets["high_throughput"] = custom_preset
```

### Monitoring Integration

```python
from app.infrastructure.resilience.config_monitoring import (
    ConfigurationMetricsCollector,
    MetricType
)

# Set up monitoring
collector = ConfigurationMetricsCollector(
    max_events=50000, 
    retention_hours=48
)

# Custom metrics tracking
collector.record_preset_usage(
    preset_name="production",
    operation="batch_processing",
    metadata={"batch_size": 100, "processing_time_ms": 1500}
)

# Export metrics for external monitoring
metrics_json = collector.export_metrics("json", time_window_hours=24)
```

### Health Check Integration

```python
from app.infrastructure.resilience import ai_resilience

async def comprehensive_health_check():
    """System health check including resilience status."""
    health_status = ai_resilience.get_health_status()
    
    return {
        "status": "healthy" if health_status["overall_health"] else "unhealthy",
        "resilience": health_status,
        "metrics": ai_resilience.get_all_metrics(),
        "circuit_breakers": ai_resilience.get_circuit_breaker_states(),
        "configuration": ai_resilience.get_current_configuration()
    }
```

## Best Practices

### Configuration Guidelines

1. **Use Presets for Standard Deployments**: Leverage built-in presets for common deployment scenarios
2. **Environment Detection**: Use automatic environment detection for intelligent configuration
3. **Custom Configuration for Specific Needs**: Only use custom configuration when presets don't meet requirements
4. **Monitor Configuration Health**: Regularly check configuration health via Internal API
5. **Validate Custom Configurations**: Always validate custom configurations before deployment

### Performance Guidelines

1. **Monitor Success Rates**: Aim for >95% success rates across operations
2. **Track Circuit Breaker States**: Monitor circuit breaker health and recovery patterns  
3. **Optimize Retry Strategies**: Balance latency requirements with fault tolerance needs
4. **Use Operation-Specific Strategies**: Apply different strategies based on operation criticality
5. **Regular Performance Benchmarking**: Run benchmarks to validate configuration effectiveness

### Development Guidelines

1. **Environment-Specific Configuration**: Use appropriate presets for each environment
2. **Testing Strategy**: Include resilience testing in test suites
3. **Error Handling**: Implement proper exception handling for resilience failures
4. **Monitoring Integration**: Include resilience metrics in application monitoring
5. **Documentation**: Document custom configurations and operation strategies

## Troubleshooting

### Invalid Preset Name
**Error**: `Invalid preset 'prod'. Available: ['simple', 'development', 'production']`

**Solution**: Use the Internal API to check available presets:
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/internal/resilience/config/presets
export RESILIENCE_PRESET=production  # not 'prod'
```

### Configuration Validation Failures
**Error**: `retry_attempts must be between 1 and 10`

**Solution**: Use validation endpoints for detailed guidance:
```bash
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"configuration": {"retry_attempts": 15}}' \
     http://localhost:8000/internal/resilience/config/validate-secure
```

### Circuit Breaker Stuck Open
**Symptoms**: All requests failing immediately

**Diagnosis**:
```bash
# Check circuit breaker states
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/internal/resilience/circuit-breakers
```

**Solution**:
```bash
# Reset specific circuit breaker
curl -H "X-API-Key: your-api-key" \
     -X POST \
     http://localhost:8000/internal/resilience/circuit-breakers/ai_service/reset
```

### Performance Issues
**Symptoms**: High latency or low throughput

**Diagnosis**:
```bash
# Run performance benchmark
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"operation_name": "text_processing", "iterations": 100}' \
     -X POST \
     http://localhost:8000/internal/resilience/performance/benchmark
```

**Solutions**:
- Adjust retry attempts and timeouts
- Switch to more aggressive strategy for development
- Increase circuit breaker thresholds if appropriate

### Debug Configuration Loading

Enable debug logging to troubleshoot configuration issues:

```bash
export LOG_LEVEL=DEBUG
export SHOW_CONFIG_LOADING=true

# Check configuration loading in application logs
docker-compose logs backend | grep -i resilience
```

### Health Monitoring

Use the comprehensive health check endpoint for system diagnostics:

```bash
# Get detailed health status including resilience configuration
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/internal/resilience/health/detailed
```

## Conclusion

The Resilience Infrastructure Service provides enterprise-grade fault tolerance capabilities specifically designed for AI-powered applications. With its layered architecture, intelligent configuration management, and comprehensive monitoring, it serves as the reliability foundation for the FastAPI-Streamlit-LLM Starter Template.

By implementing industry-standard resilience patterns including circuit breakers, intelligent retry logic, and graceful degradation, this service ensures robust operations while maintaining the flexibility needed for different deployment environments and operational requirements.

For domain-specific resilience needs, leverage this infrastructure service through the established patterns while implementing your business logic in separate domain services that maintain the >70% test coverage standard.

## Related Documentation

### Prerequisites
- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Understanding the architectural separation that defines this infrastructure service
- **[Backend Guide](../BACKEND.md)**: Basic understanding of the backend architecture and resilience integration
- **[Exception Handling Guide](../developer/EXCEPTION_HANDLING.md)**: Essential reading for understanding the custom exception system used throughout all 38 resilience endpoints

### Related Topics
- **[Monitoring Infrastructure](./MONITORING.md)**: Comprehensive monitoring that includes resilience performance analytics with exception tracking
- **[Cache Infrastructure](./CACHE.md)**: Caching strategies that complement resilience patterns with proper exception handling
- **[AI Infrastructure](./AI.md)**: AI service integration that benefits from resilience protection and exception classification
- **[API Documentation](../API.md)**: Complete endpoint documentation including custom exception handling for all 38 resilience management endpoints

### Next Steps
- **[Performance Optimization Guide](../operations/PERFORMANCE_OPTIMIZATION.md)**: Operational performance optimization procedures with exception-based monitoring
- **[Troubleshooting Guide](../operations/TROUBLESHOOTING.md)**: Resilience-focused troubleshooting procedures using structured exception context
- **[Deployment Guide](../DEPLOYMENT.md)**: Production deployment considerations for resilience infrastructure with error handling
- **[Template Customization](../CUSTOMIZATION.md)**: How to leverage resilience infrastructure in your domain services with proper exception handling patterns