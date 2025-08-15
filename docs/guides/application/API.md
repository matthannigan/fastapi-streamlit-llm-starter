# API Documentation

## Overview

The FastAPI Backend provides a comprehensive set of REST API endpoints for AI-powered text processing operations, system monitoring, and resilience management. The API is built with FastAPI and follows a clear architectural distinction between public-facing domain services and internal infrastructure management endpoints.

## Architecture

### API Organization

The API is organized into two main sections:

- **`/v1/`** - Version 1 public API endpoints (domain services)
- **`/internal/`** - Internal/administrative API endpoints (infrastructure services)

### Infrastructure vs Domain Services

- **Domain Services** (`v1/`): Example implementations that demonstrate infrastructure usage patterns and are expected to be replaced in actual projects
- **Infrastructure Services** (`internal/`): Stable APIs with backward compatibility guarantees that provide reusable technical capabilities

## Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

### API Key Authentication

The API uses **API Key authentication** with support for multiple authentication methods:

- **Authorization Header**: `Authorization: Bearer your_api_key`
- **X-API-Key Header**: `X-API-Key: your_api_key`
- **Query Parameter**: `?api_key=your_api_key`

### API Key Setup

1. Set your primary API key in environment variables:
   ```bash
   export API_KEY=your_secure_api_key_here
   ```

2. Optional: Set additional API keys:
   ```bash
   export ADDITIONAL_API_KEYS=key1,key2,key3
   ```

### Authentication Types

- **Required Authentication**: Endpoints that require valid API key authentication
- **Optional Authentication**: Endpoints that work with or without authentication (may provide limited functionality without auth)

## API Endpoints

### Version 1 Public API (`/v1/`)

#### Health Check
**GET `/v1/health`** - No authentication required

**Enhanced health check endpoint powered by infrastructure health checker** that provides comprehensive system monitoring with component-level status reporting, configurable timeouts, and graceful degradation.

**Enhanced Implementation Features:**
- **Infrastructure Health Checker Integration**: Uses `app.infrastructure.monitoring.health.HealthChecker` for standardized component monitoring
- **Component-Level Monitoring**: Individual health status for AI model, cache, resilience, and database components
- **Configurable Timeouts**: Per-component timeout configuration via environment variables
- **Automatic Retry Logic**: Configurable retry attempts with exponential backoff
- **Parallel Component Checking**: Components checked concurrently for optimal performance
- **Graceful Degradation**: Never fails the endpoint - component failures result in degraded status
- **Response Time Measurement**: Tracks individual component response times for performance monitoring
- **Dependency Injection**: Uses `get_health_checker()` from `app.dependencies` for consistent service lifecycle

**Health Check Components:**
- **AI Model**: Verifies Google Gemini API key configuration
- **Resilience Infrastructure**: Checks circuit breakers, failure detection, and orchestration services
- **Cache System**: Validates Redis connectivity and memory cache operations with fallback support
- **Database**: Placeholder for future database connectivity checks

**Health Status Algorithm:**
- **"healthy"**: All enabled components are healthy or gracefully degraded
- **"degraded"**: One or more components are degraded or timed out, but system can operate
- **Component Isolation**: Individual component failures don't break the overall health endpoint

**Configuration Support:**
```bash
# Health Check Configuration
HEALTH_CHECK_TIMEOUT_MS=2000                    # Default timeout for all components
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=2000           # AI model check timeout
HEALTH_CHECK_CACHE_TIMEOUT_MS=2000              # Cache system check timeout  
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=2000         # Resilience infrastructure timeout
HEALTH_CHECK_RETRY_COUNT=1                      # Number of retry attempts
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience"]  # Active components
```

**Performance Characteristics:**
- **Target Response Time**: <100ms for overall health check
- **Component Timeout**: <2000ms default per component (configurable)
- **Parallel Execution**: Components checked concurrently for optimal performance
- **Retry Impact**: Failed checks automatically retried with exponential backoff
- **Memory Efficient**: Uses async patterns and proper resource cleanup

Status codes:
- 200 OK: Health check executed successfully. Response body indicates health state.

Response schema: `HealthResponse`

**Response Examples:**

**All Components Healthy:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-28T00:06:39.130848",
  "version": "1.0.0",
  "ai_model_available": true,
  "resilience_healthy": true,
  "cache_healthy": true
}
```

**Mixed Component Status (AI degraded, cache healthy):**
```json
{
  "status": "degraded",
  "timestamp": "2025-06-28T00:06:39.130848",
  "version": "1.0.0",
  "ai_model_available": false,
  "resilience_healthy": null,
  "cache_healthy": true
}
```

**AI Model Unavailable (missing GEMINI_API_KEY):**
```json
{
  "status": "degraded",
  "timestamp": "2025-06-28T00:06:39.130848",
  "version": "1.0.0",
  "ai_model_available": false,
  "resilience_healthy": true,
  "cache_healthy": true
}
```

**Cache Degraded (Redis unavailable, memory cache active):**
```json
{
  "status": "degraded",
  "timestamp": "2025-06-28T00:06:39.130848",
  "version": "1.0.0",
  "ai_model_available": true,
  "resilience_healthy": true,
  "cache_healthy": false
}
```

**Multiple Components Degraded:**
```json
{
  "status": "degraded",
  "timestamp": "2025-06-28T00:06:39.130848",
  "version": "1.0.0",
  "ai_model_available": false,
  "resilience_healthy": false,
  "cache_healthy": false
}
```

**Component Timeout Scenarios:**
```json
{
  "status": "degraded",
  "timestamp": "2025-06-28T00:06:39.130848",
  "version": "1.0.0",
  "ai_model_available": true,
  "resilience_healthy": null,
  "cache_healthy": null
}
```

**Error Handling & Resilience:**
- **Never-Failing Endpoint**: Component failures are caught and mapped to degraded status
- **Timeout Management**: Components that exceed timeout limits are marked as degraded
- **Fallback Behavior**: When health checker itself fails, falls back to basic AI model check
- **Component Isolation**: Individual component failures don't affect other component checks
- **Graceful Logging**: All failures logged at appropriate levels without exposing sensitive information

#### Authentication Status
**GET `/v1/auth/status`** - Requires authentication

Verify API key authentication and return validation information.

**Response:**
```json
{
    "authenticated": true,
    "api_key_prefix": "abcd1234...",
    "message": "Authentication successful"
}
```

#### Text Processing Operations

**GET `/v1/text_processing/operations`** - Optional authentication

Get available AI text processing operations and their configurations.

**Response:**
```json
{
    "operations": [
        {
            "id": "summarize",
            "name": "Summarize",
            "description": "Generate a concise summary of the text",
            "options": ["max_length"]
        },
        {
            "id": "sentiment",
            "name": "Sentiment Analysis", 
            "description": "Analyze the emotional tone of the text",
            "options": []
        },
        {
            "id": "key_points",
            "name": "Key Points",
            "description": "Extract the main points from the text",
            "options": ["max_points"]
        },
        {
            "id": "questions",
            "name": "Generate Questions",
            "description": "Create questions about the text content",
            "options": ["num_questions"]
        },
        {
            "id": "qa",
            "name": "Question & Answer",
            "description": "Answer a specific question about the text",
            "options": [],
            "requires_question": true
        }
    ]
}
```

**POST `/v1/text_processing/process`** - Requires authentication

Process a single text request using specified AI operations with request tracing and comprehensive error handling.

**Request:**
```json
{
    "text": "Your text to process here",
    "operation": "summarize",
    "options": {"max_length": 150},
    "question": "Required for Q&A operation"
}
```

**Response:**
```json
{
    "result": "Generated summary of the input text...",
    "operation": "summarize", 
    "metadata": {"processing_time": 1.23}
}
```

**POST `/v1/text_processing/batch_process`** - Requires authentication

Process multiple text requests in a single batch operation with configurable limits.

**Request:**
```json
{
    "requests": [
        {"text": "First document", "operation": "sentiment"},
        {"text": "Second document", "operation": "summarize", "options": {"max_length": 100}}
    ],
    "batch_id": "my-batch-2024"
}
```

**Response:**
```json
{
    "batch_id": "my-batch-2024",
    "total_requests": 2,
    "completed": 2,
    "failed": 0,
    "results": [
        {"result": "Positive sentiment", "operation": "sentiment"},
        {"result": "Brief summary...", "operation": "summarize"}
    ]
}
```

**GET `/v1/text_processing/batch_status/{batch_id}`** - Requires authentication

Get the status of a batch processing job (synchronous implementation).

**GET `/v1/text_processing/health`** - Optional authentication

Get comprehensive health status for the text processing service including domain service and underlying resilience infrastructure.

### Internal API (`/internal/`)

#### System Monitoring

**GET `/internal/monitoring/health`** - Optional authentication

Comprehensive health check of all monitoring subsystems including cache performance monitoring, cache service monitoring, and resilience monitoring.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00.123456",
    "components": {
        "cache_performance_monitor": {
            "status": "healthy",
            "total_operations_tracked": 1250,
            "has_recent_data": true
        },
        "cache_service_monitoring": {
            "status": "healthy",
            "redis_monitoring": "connected",
            "memory_monitoring": "available"
        },
        "resilience_monitoring": {
            "status": "healthy",
            "circuit_breaker_tracked": true,
            "retry_metrics_available": true
        }
    },
    "available_endpoints": [
        "GET /internal/monitoring/health",
        "GET /internal/cache/status",
        "GET /internal/cache/metrics",
        "GET /internal/cache/invalidation-stats",
        "GET /internal/resilience/health"
    ]
}
```

#### Cache Management

**GET `/internal/cache/status`** - Optional authentication

Retrieve current cache status and basic statistics including Redis connection status, memory usage, and performance metrics.

**POST `/internal/cache/invalidate`** - Requires authentication

Invalidate cache entries matching a specified pattern.

**Query Parameters:**
- `pattern` (string): Glob-style pattern to match cache keys (empty string matches all)
- `operation_context` (string): Context identifier for tracking invalidation operations

**GET `/internal/cache/invalidation-stats`** - Optional authentication

Get cache invalidation frequency and pattern statistics.

**GET `/internal/cache/invalidation-recommendations`** - Optional authentication

Get optimization recommendations based on cache invalidation patterns.

**GET `/internal/cache/metrics`** - Optional authentication

Get comprehensive cache performance metrics including key generation times, cache operation metrics, compression statistics, memory usage, and invalidation analytics.

**Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00.123456",
    "retention_hours": 1,
    "cache_hit_rate": 85.5,
    "total_cache_operations": 150,
    "cache_hits": 128,
    "cache_misses": 22,
    "key_generation": {
        "total_operations": 75,
        "avg_duration": 0.002,
        "avg_text_length": 1250,
        "slow_operations": 2
    },
    "compression": {
        "avg_compression_ratio": 0.65,
        "total_bytes_saved": 183500,
        "overall_savings_percent": 35.0
    }
}
```

#### Resilience Management

**GET `/internal/resilience/health`** - Optional authentication

Get resilience service health status, configuration, and performance metrics.

**GET `/internal/resilience/config`** - Optional authentication

Retrieve current resilience configuration and operation strategies.

**GET `/internal/resilience/metrics`** - Optional authentication

Get comprehensive resilience metrics for all operations.

**GET `/internal/resilience/metrics/{operation_name}`** - Optional authentication

Get metrics for a specific operation.

**POST `/internal/resilience/metrics/reset`** - Requires authentication

Reset metrics for specific or all operations.

**GET `/internal/resilience/dashboard`** - Optional authentication

Get dashboard-style summary for monitoring systems.

#### Circuit Breaker Management

**GET `/internal/resilience/circuit-breakers`** - Requires authentication

Get comprehensive status information for all circuit breakers.

**GET `/internal/resilience/circuit-breakers/{breaker_name}`** - Requires authentication

Get detailed information about a specific circuit breaker.

**POST `/internal/resilience/circuit-breakers/{breaker_name}/reset`** - Requires authentication

Reset a specific circuit breaker to closed state for emergency recovery.

#### Configuration Management

**GET `/internal/resilience/config/presets`** - Requires authentication

List all available resilience presets with summaries.

**GET `/internal/resilience/config/presets/{preset_name}`** - Requires authentication

Get detailed configuration for a specific preset.

**GET `/internal/resilience/config/presets-summary`** - Requires authentication

Get comprehensive summary of all presets.

**GET `/internal/resilience/config/recommend-preset/{environment}`** - Requires authentication

Get preset recommendation for specific environment.

**GET `/internal/resilience/config/recommend-preset-auto`** - Requires authentication

Auto-detect environment and recommend optimal preset.

#### Configuration Validation

**POST `/internal/resilience/config/validate`** - Requires authentication

Standard custom configuration validation.

**POST `/internal/resilience/config/validate-secure`** - Requires authentication

Enhanced security validation with security metadata.

**POST `/internal/resilience/config/validate-json`** - Requires authentication

Direct JSON string configuration validation.

**POST `/internal/resilience/config/validate/field-whitelist`** - Requires authentication

Validate configuration against field whitelist.

**GET `/internal/resilience/config/validate/security-config`** - Requires authentication

Get security validation configuration and limits.

**GET `/internal/resilience/config/validate/rate-limit-status`** - Requires authentication

Get current rate limiting status and quotas.

#### Template Management

**GET `/internal/resilience/templates`** - Requires authentication

Get available configuration templates catalog.

**GET `/internal/resilience/templates/{template_name}`** - Requires authentication

Get detailed information for a specific template.

**POST `/internal/resilience/templates/validate`** - Requires authentication

Validate configuration using a specific template.

**GET `/internal/resilience/templates/suggest`** - Requires authentication

Get template suggestions based on configuration.

#### Performance Benchmarking

**POST `/internal/resilience/performance/benchmark`** - Requires authentication

Run comprehensive performance benchmarks.

**GET `/internal/resilience/performance/benchmark/results`** - Requires authentication

Get latest benchmark results and analysis.

**GET `/internal/resilience/performance/thresholds`** - Requires authentication

Get current performance thresholds and targets.

**POST `/internal/resilience/performance/thresholds`** - Requires authentication

Update performance thresholds.

**GET `/internal/resilience/performance/reports`** - Requires authentication

Get detailed performance analysis reports.

#### Monitoring and Analytics

**GET `/internal/resilience/monitoring/usage`** - Requires authentication

Get configuration usage patterns and analytics.

**GET `/internal/resilience/monitoring/performance`** - Requires authentication

Get performance monitoring data and trends.

**GET `/internal/resilience/monitoring/alerts`** - Requires authentication

Get current alerts and alert configuration.

**POST `/internal/resilience/monitoring/alerts`** - Requires authentication

Update alert configuration and thresholds.

**GET `/internal/resilience/monitoring/export/{format}`** - Requires authentication

Export monitoring data in specified format.

**GET `/internal/resilience/monitoring/analytics/trends`** - Requires authentication

Get analytics and trend analysis.

**GET `/internal/resilience/monitoring/analytics/insights`** - Requires authentication

Get operational insights and recommendations.

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful operations
- **400 Bad Request**: Validation errors, invalid requests
- **401 Unauthorized**: Authentication failures, missing/invalid API key
- **404 Not Found**: Resource not found, invalid endpoints
- **422 Unprocessable Entity**: Request validation errors
- **500 Internal Server Error**: Infrastructure failures, AI service errors
- **502 Bad Gateway**: AI service errors, external service failures
- **503 Service Unavailable**: Service temporarily unavailable

### Error Response Format

**Validation Error (400/422):**
```json
{
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["body", "text"],
            "msg": "String should have at least 10 characters",
            "input": "short",
            "ctx": {"min_length": 10}
        }
    ]
}
```

**Authentication Error (401):**
```json
{
    "detail": "Authentication Error"
}
```

**Business Logic Error (400):**
```json
{
    "detail": "Question is required for Q&A operation"
}
```

**Infrastructure Error (500):**
```json
{
    "detail": "Failed to process text: Internal server error"
}
```

## Request Examples

### Health Check

**Basic Health Check Request:**
```bash
# No authentication required - enhanced infrastructure monitoring
curl http://localhost:8000/v1/health
```

**Health Check with Response Analysis:**
```bash
# Get health status and analyze components
curl -s http://localhost:8000/v1/health | jq '.'

# Check specific component status
curl -s http://localhost:8000/v1/health | jq '.ai_model_available'
curl -s http://localhost:8000/v1/health | jq '.cache_healthy'
curl -s http://localhost:8000/v1/health | jq '.resilience_healthy'
```

**Monitoring Script Examples:**
```bash
#!/bin/bash
# Simple health monitoring script
HEALTH_URL="http://localhost:8000/v1/health"
STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

if [[ "$STATUS" == "healthy" ]]; then
    echo "✅ System is healthy"
    exit 0
elif [[ "$STATUS" == "degraded" ]]; then
    echo "⚠️  System is degraded but operational"
    exit 1
else
    echo "❌ System status unknown"
    exit 2
fi
```

**Component-Specific Monitoring:**
```bash
#!/bin/bash
# Check individual components
RESPONSE=$(curl -s http://localhost:8000/v1/health)

AI_STATUS=$(echo $RESPONSE | jq -r '.ai_model_available')
CACHE_STATUS=$(echo $RESPONSE | jq -r '.cache_healthy')
RESILIENCE_STATUS=$(echo $RESPONSE | jq -r '.resilience_healthy')

echo "AI Model: $AI_STATUS"
echo "Cache: $CACHE_STATUS"
echo "Resilience: $RESILIENCE_STATUS"
```

**Load Balancer Configuration:**
```yaml
# HAProxy configuration example
backend api_servers
    option httpchk GET /v1/health
    http-check expect status 200
    http-check expect string "healthy"
    server api1 localhost:8000 check
    server api2 localhost:8001 check
```

**Kubernetes Liveness/Readiness Probes:**
```yaml
# Kubernetes deployment configuration
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: api
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
```

**Docker Compose Health Check:**
```yaml
# docker-compose.yml health check configuration
version: '3.8'
services:
  api:
    image: your-api:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Production Monitoring Integration:**
```bash
# Prometheus metrics collection script
#!/bin/bash
HEALTH_ENDPOINT="http://localhost:8000/v1/health"
RESPONSE=$(curl -s $HEALTH_ENDPOINT)

# Extract metrics for Prometheus
STATUS=$(echo $RESPONSE | jq -r '.status')
AI_AVAILABLE=$(echo $RESPONSE | jq -r '.ai_model_available')
CACHE_HEALTHY=$(echo $RESPONSE | jq -r '.cache_healthy // "null"')
RESILIENCE_HEALTHY=$(echo $RESPONSE | jq -r '.resilience_healthy // "null"')

# Export as Prometheus metrics
echo "api_health_status{status=\"$STATUS\"} 1"
echo "api_component_health{component=\"ai_model\"} $([ "$AI_AVAILABLE" = "true" ] && echo 1 || echo 0)"
echo "api_component_health{component=\"cache\"} $([ "$CACHE_HEALTHY" = "true" ] && echo 1 || echo 0)"
echo "api_component_health{component=\"resilience\"} $([ "$RESILIENCE_HEALTHY" = "true" ] && echo 1 || echo 0)"
```

### Single Text Processing

```bash
curl -X POST "http://localhost:8000/v1/text_processing/process" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text to process here",
    "operation": "summarize",
    "options": {"max_length": 150}
  }'
```

### Batch Processing

```bash
curl -X POST "http://localhost:8000/v1/text_processing/batch_process" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"text": "First document", "operation": "sentiment"},
      {"text": "Second document", "operation": "key_points"}
    ],
    "batch_id": "my-batch-2024"
  }'
```

### Cache Invalidation

```bash
curl -X POST "http://localhost:8000/internal/cache/invalidate?pattern=user:*" \
  -H "Authorization: Bearer your-api-key"
```

### Cache Metrics

```bash
curl "http://localhost:8000/internal/cache/metrics" \
  -H "Authorization: Bearer your-api-key"
```

### Circuit Breaker Status

```bash
curl "http://localhost:8000/internal/resilience/circuit-breakers" \
  -H "Authorization: Bearer your-api-key"
```

## Response Examples

### Successful Text Processing

```json
{
    "result": "Generated summary of the input text...",
    "operation": "summarize",
    "metadata": {"processing_time": 1.23}
}
```

### Batch Processing Response

```json
{
    "batch_id": "my-batch-2024",
    "total_requests": 2,
    "completed": 2,
    "failed": 0,
    "results": [
        {"result": "Positive sentiment", "operation": "sentiment"},
        {"result": "Key points: 1. Point one...", "operation": "key_points"}
    ]
}
```

### Health Check Response

**All Components Healthy:**
```json
{
    "status": "healthy",
    "timestamp": "2025-06-28T00:06:39.130848",
    "version": "1.0.0",
    "ai_model_available": true,
    "resilience_healthy": true,
    "cache_healthy": true
}
```

**AI Model Unavailable (missing GEMINI_API_KEY):**
```json
{
    "status": "degraded",
    "timestamp": "2025-06-28T00:06:39.130848", 
    "version": "1.0.0",
    "ai_model_available": false,
    "resilience_healthy": true,
    "cache_healthy": true
}
```

**Cache Degraded (Redis unavailable, memory cache active):**
```json
{
    "status": "degraded",
    "timestamp": "2025-06-28T00:06:39.130848",
    "version": "1.0.0",
    "ai_model_available": true,
    "resilience_healthy": true,
    "cache_healthy": false
}
```

**Component Timeout Scenarios:**
```json
{
    "status": "degraded", 
    "timestamp": "2025-06-28T00:06:39.130848",
    "version": "1.0.0",
    "ai_model_available": true,
    "resilience_healthy": null,
    "cache_healthy": null
}
```

## Features

### Text Processing Features

- **Multiple AI Operations**: Summarization, sentiment analysis, key point extraction, question generation, Q&A
- **Batch Processing**: Process multiple requests with configurable limits
- **Request Tracing**: Unique IDs for logging and debugging
- **Resilience Integration**: Circuit breakers, retries, graceful degradation
- **Input Validation**: Pydantic models with sanitization
- **Structured Error Handling**: Proper HTTP status codes and error context

### Infrastructure Features

- **Cache Management**: Redis-backed caching with compression and performance monitoring
- **Resilience Orchestration**: Circuit breakers, retry logic, failure detection
- **Configuration Management**: Presets, templates, validation, recommendations
- **Performance Monitoring**: Benchmarking, metrics collection, trend analysis
- **Enhanced Health Monitoring**: Infrastructure-powered health checker with component-level monitoring, configurable timeouts, retry logic, and parallel component checking
- **Security**: API key authentication with multiple key support

### Monitoring and Observability

- **Real-time Metrics**: Cache performance, resilience operations, system health
- **Dashboard APIs**: Monitoring system integration endpoints
- **Alert Management**: Configuration and threshold-based alerting
- **Analytics**: Usage patterns, trends, operational insights
- **Export Capabilities**: Data export in multiple formats for analysis

## Configuration

### Environment Variables

```bash
# Core API Configuration
API_KEY=your_secure_api_key_here
ADDITIONAL_API_KEYS=key1,key2,key3

# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key

# Cache Configuration
REDIS_URL=redis://localhost:6379
CACHE_DEFAULT_TTL=3600
CACHE_COMPRESSION_THRESHOLD=1000

# Resilience Configuration
RESILIENCE_PRESET=simple
# Options: simple, development, production

# Health Check Configuration
HEALTH_CHECK_TIMEOUT_MS=2000                    # Default timeout for all components
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=2000           # AI model check timeout
HEALTH_CHECK_CACHE_TIMEOUT_MS=2000              # Cache system check timeout  
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=2000         # Resilience infrastructure timeout
HEALTH_CHECK_RETRY_COUNT=1                      # Number of retry attempts
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience"]  # Active components

# Batch Processing
MAX_BATCH_REQUESTS_PER_CALL=10
```

### Resilience Presets

- **simple**: 3 retries, 5 failure threshold, 60s recovery, balanced strategy
- **development**: 2 retries, 3 failure threshold, 30s recovery, aggressive strategy  
- **production**: 5 retries, 10 failure threshold, 120s recovery, conservative strategy

### Health Check Configuration

The enhanced health check system supports comprehensive configuration for different environments and monitoring requirements.

#### Basic Configuration

**Default Settings (suitable for most environments):**
```bash
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_RETRY_COUNT=1
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience"]
```

#### Environment-Specific Configuration

**Development Environment:**
```bash
# Faster feedback for development
HEALTH_CHECK_TIMEOUT_MS=1000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=500
HEALTH_CHECK_CACHE_TIMEOUT_MS=800
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=600
HEALTH_CHECK_RETRY_COUNT=0  # No retries for immediate feedback
```

**Production Environment:**
```bash
# More resilient configuration for production
HEALTH_CHECK_TIMEOUT_MS=5000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=3000
HEALTH_CHECK_CACHE_TIMEOUT_MS=4000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=3000
HEALTH_CHECK_RETRY_COUNT=2  # Additional retries for network issues
```

**Load Balancer Optimization:**
```bash
# Optimized for load balancer health checks
HEALTH_CHECK_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=1
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model"]  # Check only critical components
```

#### Component Selection

**Minimal Monitoring (essential services only):**
```bash
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model"]
```

**Comprehensive Monitoring (all components):**
```bash
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience", "database"]
```

**Cache-Optional Configuration:**
```bash
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "resilience"]
```

#### Performance Tuning Guidelines

- **Timeout Configuration**: Set timeouts based on your infrastructure capabilities
  - Local development: 500-1000ms
  - Cloud environments: 2000-3000ms
  - High-latency networks: 5000ms+

- **Retry Strategy**: Balance between reliability and response time
  - Development: 0 retries for immediate feedback
  - Production: 1-2 retries for transient failures
  - Critical systems: 2-3 retries with exponential backoff

- **Component Selection**: Enable only necessary components for your monitoring needs
  - Load balancers: AI model only
  - Operational dashboards: All components
  - Service discovery: Essential components only

## Interactive Documentation

When the API is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Rate Limiting

Currently, no rate limiting is implemented. The resilience infrastructure includes rate limiting configuration support for future implementation.

## Security Considerations

- **API Key Protection**: Never expose API keys in client-side code
- **HTTPS**: Use HTTPS in production environments
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Errors don't expose sensitive system information
- **Security Validation**: Enhanced security validation available for configuration endpoints

## Development and Testing

For development setup, testing procedures, and deployment guidelines, see:
- `backend/README.md` - Backend development setup
- `backend/tests/` - Comprehensive test suite
- `docs/` - Additional documentation and guides

## Support

For issues, feature requests, or questions about the API implementation, please refer to the project documentation or create an issue in the project repository.

## Related Documentation

### Prerequisites
- **[Backend Guide](./BACKEND.md)**: Understanding the dual-API backend architecture
- **[Dual API Architecture](../reference/key-concepts/DUAL_API_ARCHITECTURE.md)**: Architectural concepts behind the API design

### Related Topics
- **[Authentication Guide](./developer/AUTHENTICATION.md)**: Multi-key authentication system used across both APIs
- **[Frontend Guide](./FRONTEND.md)**: How the frontend consumes these API endpoints
- **[Shared Module](./SHARED.md)**: Data models used in API requests and responses

### Next Steps
- **[Monitoring Infrastructure](./infrastructure/MONITORING.md)**: Internal API endpoints for system monitoring
- **[Resilience Infrastructure](./infrastructure/RESILIENCE.md)**: 38 internal API endpoints for resilience management
- **[Cache Infrastructure](./infrastructure/CACHE.md)**: Internal API endpoints for cache management
- **[Deployment Guide](./DEPLOYMENT.md)**: Production API deployment considerations