---
sidebar_label: Middleware
---

# Middleware Operations Guide

This guide provides operational procedures for managing the middleware stack in the FastAPI-Streamlit-LLM Starter Template. It consolidates middleware management practices into actionable runbooks for operations teams managing production deployments.

## Overview

The starter template implements a sophisticated middleware stack comprising production-ready components that handle cross-cutting concerns including security, performance, monitoring, and operational intelligence. This operational guide focuses on deployment procedures, configuration management, performance optimization, and troubleshooting workflows for production environments.

## Execution Order 

The middleware components are applied in a carefully orchestrated order to optimize security, performance, and operational visibility. **FastAPI middleware follows LIFO (Last-In, First-Out) execution order.** The middleware registered last executes first.

1. **[CORS](#cors)** - Handle cross-origin response processing (registered last, runs first)
2. **[Performance Monitoring](#performance-monitoring)** - Track metrics and resource usage
3. **[Request Logging](#request-logging)** - Structured logging with correlation IDs
4. **[Compression](#compression)** - Handle request/response compression
5. **[API Versioning](#api-versioning)** - Version detection, routing, compatibility transforms
6. **[Security](#security)** - Security headers, XSS protection, input validation
7. **[Request Size Limiting](#request-size-limiting)** - Prevent large request DoS attacks
8. **[Rate Limiting](#rate-limiting)** - Protect against abuse and DoS attacks (registered first, runs last)
9. **Application Logic** - App-specific business logic and endpoints
10. **[Global Exception Handler](#global-exception-handler)** - Catch and format unhandled exceptions (*not true middleware*)

Due to FastAPI's LIFO execution order, CORS middleware runs first to handle preflight requests and cross-origin validation, followed by performance monitoring and logging middleware to establish timing context, while rate limiting runs last to provide final request validation.

## Middleware Components

### API Versioning

**Purpose**: Version detection, path rewriting, compatibility layers

**Location**: `/backend/app/core/middleware/api_versioning.py`

**Configuration Key**: `api_versioning_enabled`, `default_api_version`, `current_api_version`, `api_version_compatibility_enabled` (defaults to False)

**Operational Procedures:**
```bash
# Test version detection methods
curl -H "X-API-Version: 1.0" http://localhost:8000/health
curl "http://localhost:8000/v1/health?version=1.0"
curl -H "Accept: application/vnd.api+json;version=1.0" http://localhost:8000/health

# Check version compatibility status
curl -s http://localhost:8000/internal/middleware/health | jq '.middleware.api_versioning'

# Monitor version usage analytics
curl -s http://localhost:8000/internal/api-versioning/analytics

# Get supported versions information
curl -s http://localhost:8000/internal/api-versioning/versions
```

**API Versioning Configuration:**
```bash
# Production versioning settings
export API_VERSIONING_ENABLED=true
export DEFAULT_API_VERSION=1.0
export CURRENT_API_VERSION=1.0
export MIN_API_VERSION=1.0
export MAX_API_VERSION=2.0
export VERSION_ANALYTICS_ENABLED=true
```

### Compression

**Purpose**: Algorithm selection, streaming compression, content-type handling

**Location**: `/backend/app/core/middleware/compression.py`

**Configuration Key**: `compression_enabled`, `compression_level`, `compression_algorithms`

**Operational Procedures:**
```bash
# Test compression capability
curl -H "Accept-Encoding: gzip, br" -v http://localhost:8000/v1/text/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Large text content for compression testing..."}'

# Monitor compression statistics
curl -s http://localhost:8000/internal/compression/stats

# Check compression performance
curl -s http://localhost:8000/internal/middleware/stats | jq '.configuration.compression'

# Test different compression algorithms
curl -H "Accept-Encoding: br" http://localhost:8000/health
curl -H "Accept-Encoding: gzip" http://localhost:8000/health
```

**Compression Configuration:**
```bash
# Production compression settings
export COMPRESSION_ENABLED=true
export COMPRESSION_MIN_SIZE=1024  # 1KB
export COMPRESSION_LEVEL=6  # Balance between speed and ratio
export COMPRESSION_ALGORITHMS='["br", "gzip", "deflate"]'
export STREAMING_COMPRESSION_ENABLED=true
```

### CORS

**Purpose**: Cross-origin resource sharing with security optimizations

**Location**: `/backend/app/core/middleware/cors.py`

**Configuration Key**: `allowed_origins`, `cors_credentials`, `cors_methods`

**Operational Procedures:**
```bash
# Verify CORS configuration
curl -s http://localhost:8000/internal/middleware/stats | jq '.enabled_features[] | select(. == "cors")'

# Test CORS preflight request
curl -X OPTIONS -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/v1/text/summarize

# Production CORS validation
curl -I -H "Origin: https://your-frontend-domain.com" http://localhost:8000/health
```

### Global Exception Handler

**Purpose**: Comprehensive error handling with infrastructure integration

**Location**: `/backend/app/core/middleware/global_exception_handler.py`

**Configuration Key**: Global exception handling is always enabled

**Operational Procedures:**
```bash
# Test exception handling response format
curl -s http://localhost:8000/v1/nonexistent-endpoint | jq '.error'

# Monitor exception rates
curl -s http://localhost:8000/internal/monitoring/overview | jq '.system_health.error_rate'

# Check recent exceptions
curl -s http://localhost:8000/internal/monitoring/alerts | jq '.alerts[] | select(.type == "exception")'
```

**Important Note:** The Global Exception Handler is not true middleware. It uses FastAPI's `@app.exception_handler()` decorator system, NOT Starlette's `app.add_middleware()`. However, it acts like middleware in that it processes all requests/responses and handles concerns across the entire application. Even though it uses different FastAPI mechanisms, it serves the same architectural purpose as middleware. We store it in `/backend/app/core/middleware/` for setup consistency and document it here with other middleware.

### Performance Monitoring

**Purpose**: Metrics collection, slow request detection, resource tracking

**Location**: `/backend/app/core/middleware/performance_monitoring.py`

**Configuration Key**: `performance_monitoring_enabled`, `slow_request_threshold`, `memory_monitoring_enabled`

**Operational Procedures:**
```bash
# Monitor performance metrics in real-time
curl -s http://localhost:8000/internal/middleware/health | jq '.middleware.performance_monitoring'

# Check slow request detection
curl -s http://localhost:8000/internal/monitoring/performance | jq '.slow_requests'

# Memory usage monitoring
curl -s http://localhost:8000/internal/monitoring/overview | jq '.cache_performance.memory_usage'
```

**Rate Limiting Configuration:**
```bash
# Production rate limiting settings
export RATE_LIMITING_ENABLED=true
export REDIS_URL=redis://localhost:6379
export CUSTOM_RATE_LIMITS='{"auth": {"requests": 100, "window": 60}, "api_heavy": {"requests": 10, "window": 60}}'
export RATE_LIMITING_SKIP_HEALTH=true
```

### Rate Limiting

**Purpose**: Redis-backed rate limiting with local cache fallback

**Location**: `/backend/app/core/middleware/rate_limiting.py`

**Configuration Key**: `rate_limiting_enabled`, `redis_url`, `custom_rate_limits`

**Operational Procedures:**
```bash
# Check rate limiting status and Redis connection
curl -s http://localhost:8000/internal/middleware/stats | jq '.enabled_features[] | select(. == "rate_limiting")'

# Test rate limit enforcement
for i in {1..10}; do
  curl -w "%{http_code}\n" -o /dev/null -s http://localhost:8000/health
done

# Monitor rate limit statistics
curl -s http://localhost:8000/internal/monitoring/rate-limits

# Reset rate limits for specific client (emergency)
curl -X POST "http://localhost:8000/internal/rate-limits/reset" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "api-key-12345"}'
```

### Request Logging

**Purpose**: Structured logging with performance monitoring and correlation

**Location**: `/backend/app/core/middleware/request_logging.py`

**Configuration Key**: `request_logging_enabled`, `log_level`, `log_sensitive_data`

**Operational Procedures:**
```bash
# Verify logging middleware status
curl -s http://localhost:8000/internal/middleware/health | jq '.middleware.request_logging'

# Test request ID generation
REQUEST_ID=$(curl -s -D headers.txt http://localhost:8000/health && grep -i "x-request-id" headers.txt)
echo "Generated Request ID: $REQUEST_ID"

# Monitor log volume and performance
curl -s http://localhost:8000/internal/monitoring/performance | jq '.logging_performance'
```

### Request Size Limiting

**Purpose**: Size limits per content-type, DoS protection, streaming validation

**Location**: `/backend/app/core/middleware/request_size.py`

**Configuration Key**: `request_size_limiting_enabled`, `request_size_limits`

**Operational Procedures:**
```bash
# Test request size limits
curl -X POST http://localhost:8000/v1/text/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "'$(python -c 'print("a" * 10485760)')'"}' # 10MB test

# Monitor request size statistics
curl -s http://localhost:8000/internal/monitoring/request-sizes

# Check size limit configuration
curl -s http://localhost:8000/internal/middleware/stats | jq '.configuration.request_size_limits'
```

**Request Size Configuration:**
```bash
# Production size limiting settings
export REQUEST_SIZE_LIMITING_ENABLED=true
export REQUEST_SIZE_LIMITS='{
  "default": 10485760,
  "application/json": 5242880,
  "multipart/form-data": 52428800
}'
```

### Security

**Purpose**: XSS prevention, header injection protection, security headers

**Location**: `/backend/app/core/middleware/security.py`

**Configuration Key**: `security_headers_enabled`, `max_headers_count`

**Operational Procedures:**
```bash
# Verify security headers are applied
curl -I http://localhost:8000/health | grep -E "(X-Content-Type-Options|X-Frame-Options|X-XSS-Protection)"

# Test security header injection
curl -s http://localhost:8000/internal/middleware/health | jq '.middleware.security'

# Monitor security events
curl -s http://localhost:8000/internal/monitoring/alerts | jq '.alerts[] | select(.category == "security")'
```

## Configuration Management

### Environment-Based Configuration

#### Development Configuration
```bash
# Development middleware settings
export RESILIENCE_PRESET=development
export RATE_LIMITING_ENABLED=true
export COMPRESSION_ENABLED=true
export API_VERSIONING_ENABLED=true
export SECURITY_HEADERS_ENABLED=true
export PERFORMANCE_MONITORING_ENABLED=true
export REQUEST_LOGGING_ENABLED=true
export REQUEST_SIZE_LIMITING_ENABLED=true

# Development optimizations
export LOG_LEVEL=DEBUG
export COMPRESSION_LEVEL=4  # Faster compression
export SLOW_REQUEST_THRESHOLD=2000  # 2 seconds
export MEMORY_MONITORING_ENABLED=true
```

#### Production Configuration
```bash
# Production middleware settings
export RESILIENCE_PRESET=production
export RATE_LIMITING_ENABLED=true
export COMPRESSION_ENABLED=true
export API_VERSIONING_ENABLED=true
export SECURITY_HEADERS_ENABLED=true
export PERFORMANCE_MONITORING_ENABLED=true
export REQUEST_LOGGING_ENABLED=true
export REQUEST_SIZE_LIMITING_ENABLED=true

# Production optimizations
export LOG_LEVEL=INFO
export COMPRESSION_LEVEL=6  # Balanced compression
export SLOW_REQUEST_THRESHOLD=5000  # 5 seconds
export MEMORY_MONITORING_ENABLED=false  # Reduce overhead
export LOG_SENSITIVE_DATA=false
export LOG_REQUEST_BODIES=false
export METRICS_EXPORT_ENABLED=true
```

### Configuration Validation

**Middleware Configuration Validation:**
```bash
# Validate current middleware configuration
curl -s http://localhost:8000/internal/middleware/validate-config

# Get configuration warnings
curl -s http://localhost:8000/internal/middleware/config-warnings

# Test middleware setup integrity
curl -s http://localhost:8000/internal/middleware/health | jq '.status'
```

**Configuration Management Script:**
```bash
#!/bin/bash
# validate_middleware_config.sh - Validate middleware configuration

echo "=== Middleware Configuration Validation ==="

# Check middleware health
HEALTH=$(curl -s http://localhost:8000/internal/middleware/health)
STATUS=$(echo "$HEALTH" | jq -r '.status')
echo "Middleware Status: $STATUS"

# Validate individual components
for component in rate_limiting compression api_versioning security performance_monitoring; do
  COMPONENT_STATUS=$(echo "$HEALTH" | jq -r ".middleware.$component.status // \"not_configured\"")
  echo "$component: $COMPONENT_STATUS"
done

# Check for configuration warnings
WARNINGS=$(curl -s http://localhost:8000/internal/middleware/config-warnings)
WARNING_COUNT=$(echo "$WARNINGS" | jq '. | length')
if [ "$WARNING_COUNT" -gt 0 ]; then
  echo "Configuration Warnings:"
  echo "$WARNINGS" | jq -r '.[] | "- \(.)"'
fi

echo "=== Validation Complete ==="
```

## Production Deployment

### Deployment Procedures

#### Pre-Deployment Checklist
```bash
# 1. Validate middleware configuration
curl -s http://localhost:8000/internal/middleware/validate-config | jq '.issues'

# 2. Check Redis connectivity (if using distributed rate limiting)
redis-cli -u $REDIS_URL ping

# 3. Test middleware stack integration
curl -s http://localhost:8000/internal/middleware/integration-test

# 4. Verify security headers configuration
curl -I http://localhost:8000/health | grep -E "X-Content-Type-Options|X-Frame-Options"

# 5. Test compression capabilities
curl -H "Accept-Encoding: gzip,br" -s http://localhost:8000/health | wc -c
```

#### Deployment Steps
```bash
# 1. Enable maintenance mode
curl -X POST http://localhost:8000/internal/monitoring/maintenance-mode/enable

# 2. Deploy enhanced middleware configuration
export MIDDLEWARE_STACK=enhanced  # Use enhanced middleware setup

# 3. Restart application with new middleware
docker-compose restart backend

# 4. Verify middleware initialization
curl -s http://localhost:8000/internal/middleware/stats | jq '.total_middleware'

# 5. Run post-deployment health check
curl -s http://localhost:8000/internal/middleware/health

# 6. Disable maintenance mode
curl -X POST http://localhost:8000/internal/monitoring/maintenance-mode/disable
```

#### Performance Optimization Script

```bash
#!/bin/bash
# optimize_middleware_production.sh - Optimize middleware for production

echo "=== Middleware Production Optimization ==="

# 1. Optimize logging levels
export LOG_LEVEL=WARNING  # Reduce verbosity for performance

# 2. Configure compression for production
export COMPRESSION_LEVEL=4  # Faster compression
export COMPRESSION_MIN_SIZE=2048  # Only compress larger responses

# 3. Optimize performance monitoring
export DETAILED_MONITORING_ENABLED=false
export MEMORY_MONITORING_ENABLED=false

# 4. Configure rate limiting for production load
export RATE_LIMIT_CLEANUP_INTERVAL=300  # 5 minutes

# 5. Restart with optimized settings
docker-compose restart backend

# 6. Verify optimizations
curl -s http://localhost:8000/internal/middleware/performance-stats

echo "=== Optimization Complete ==="
```

### Scaling Considerations

#### Horizontal Scaling
```bash
# Configure Redis for distributed rate limiting across instances
export REDIS_URL=redis://redis-cluster:6379
export RATE_LIMITING_DISTRIBUTED=true

# Configure shared compression cache
export COMPRESSION_CACHE_REDIS=true

# Configure distributed API version analytics
export VERSION_ANALYTICS_REDIS_STORAGE=true
```

#### Load Balancer Configuration
```bash
# Configure health check endpoint for load balancer
# Health check URL: /health (bypasses rate limiting)
# Expected response: 200 OK with {"status": "healthy"}

# Configure sticky sessions if needed for rate limiting
# (Not required with Redis-backed rate limiting)
```

## Integration Patterns

### Custom Middleware Development

#### Adding Custom Middleware
```python
# custom_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.config import Settings

class CustomBusinessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.enabled = getattr(settings, 'custom_middleware_enabled', True)
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        # Custom business logic here
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Custom-Process-Time"] = str(process_time)
        return response
```

#### Integration with Middleware Stack
```python
# In app/core/middleware/__init__.py
from .custom_middleware import CustomBusinessMiddleware

def setup_enhanced_middleware(app: FastAPI, settings: Settings) -> None:
    # ... existing middleware setup ...
    
    # Add custom middleware in appropriate position
    custom_enabled = getattr(settings, 'custom_middleware_enabled', False)
    if custom_enabled:
        app.add_middleware(CustomBusinessMiddleware, settings=settings)
        logger.info("Custom business middleware enabled")
```

### Testing Strategies

#### Unit Testing Middleware
```python
# test_custom_middleware.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_custom_middleware_headers():
    """Test custom middleware adds expected headers."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert "X-Custom-Process-Time" in response.headers
    assert float(response.headers["X-Custom-Process-Time"]) >= 0
```

#### Integration Testing
```bash
# Integration test script
#!/bin/bash
# test_middleware_integration.sh

echo "=== Middleware Integration Testing ==="

# Test middleware order execution
curl -s -D headers.txt http://localhost:8000/health

# Verify all expected headers are present
echo "Security Headers:"
grep -E "(X-Content-Type-Options|X-Frame-Options)" headers.txt

echo "Performance Headers:"
grep -E "(X-Request-ID|X-Process-Time)" headers.txt

echo "Compression Headers:"
curl -H "Accept-Encoding: gzip" -D comp_headers.txt http://localhost:8000/health
grep "Content-Encoding" comp_headers.txt

echo "Rate Limiting Headers:"
curl -D rate_headers.txt http://localhost:8000/health
grep -E "(X-RateLimit|Retry-After)" rate_headers.txt || echo "No rate limits hit"

echo "=== Integration Test Complete ==="
```

## Operational Procedures

### Daily Operations

#### Morning Health Check (10 minutes)
```bash
#!/bin/bash
# daily_middleware_check.sh - Daily middleware health verification

echo "=== Daily Middleware Health Check $(date) ==="

# 1. Overall middleware health
HEALTH=$(curl -s http://localhost:8000/internal/middleware/health)
OVERALL_STATUS=$(echo "$HEALTH" | jq -r '.status')
echo "Overall Middleware Status: $OVERALL_STATUS"

# 2. Check each middleware component
echo "Component Status:"
echo "$HEALTH" | jq -r '.middleware | to_entries[] | "\(.key): \(.value.status // "unknown")"'

# 3. Performance metrics
STATS=$(curl -s http://localhost:8000/internal/middleware/stats)
TOTAL_MIDDLEWARE=$(echo "$STATS" | jq '.total_middleware')
ENABLED_FEATURES=$(echo "$STATS" | jq -r '.enabled_features | join(", ")')
echo "Total Middleware: $TOTAL_MIDDLEWARE"
echo "Enabled Features: $ENABLED_FEATURES"

# 4. Check for any configuration warnings
WARNINGS=$(curl -s http://localhost:8000/internal/middleware/config-warnings)
WARNING_COUNT=$(echo "$WARNINGS" | jq '. | length')
if [ "$WARNING_COUNT" -gt 0 ]; then
    echo "⚠️ Configuration Warnings ($WARNING_COUNT):"
    echo "$WARNINGS" | jq -r '.[] | "  - \(.)"'
else
    echo "✅ No configuration warnings"
fi

# 5. Performance summary
PERF=$(curl -s http://localhost:8000/internal/monitoring/performance)
AVG_RESPONSE_TIME=$(echo "$PERF" | jq '.average_response_time_ms // 0')
SLOW_REQUESTS=$(echo "$PERF" | jq '.slow_requests_count // 0')
echo "Average Response Time: ${AVG_RESPONSE_TIME}ms"
echo "Slow Requests: $SLOW_REQUESTS"

echo "=== Daily Check Complete ==="
```

#### Weekly Operations Review (45 minutes)

```bash
# Generate weekly middleware performance report
curl -s "http://localhost:8000/internal/middleware/performance-report?days=7" > weekly_middleware_report.json

# Analyze middleware performance trends
jq '.performance_trends' weekly_middleware_report.json
jq '.resource_usage' weekly_middleware_report.json
jq '.error_rates' weekly_middleware_report.json
```

**Configuration Optimization Review:**
```bash
# Review middleware configuration effectiveness
curl -s http://localhost:8000/internal/middleware/optimization-recommendations > middleware_recommendations.json

# Check for configuration drift
curl -s http://localhost:8000/internal/middleware/config-drift-analysis
```

### Incident Response

#### Middleware Performance Degradation

**Step 1: Rapid Assessment (< 2 minutes)**
```bash
# Quick middleware health check
curl -s http://localhost:8000/internal/middleware/health | jq '.status'

# Check for performance bottlenecks
curl -s http://localhost:8000/internal/monitoring/performance | jq '.bottlenecks'

# Identify problematic middleware components
curl -s http://localhost:8000/internal/middleware/component-performance
```

**Step 2: Immediate Mitigation (< 5 minutes)**
```bash
# Disable non-critical middleware if needed
curl -X POST http://localhost:8000/internal/middleware/disable-component \
  -H "Content-Type: application/json" \
  -d '{"component": "memory_monitoring", "reason": "performance_issue"}'

# Adjust performance settings
curl -X POST http://localhost:8000/internal/middleware/adjust-settings \
  -d '{"compression_level": 1, "detailed_monitoring": false}'

# Clear middleware caches if applicable
curl -X POST http://localhost:8000/internal/middleware/clear-caches
```

#### Rate Limiting Issues

**High Rate Limit Triggers:**
```bash
# Check rate limiting statistics
curl -s http://localhost:8000/internal/monitoring/rate-limits

# Review blocked clients
curl -s http://localhost:8000/internal/rate-limits/blocked-clients

# Adjust rate limits if needed (emergency)
curl -X POST http://localhost:8000/internal/rate-limits/adjust \
  -d '{"endpoint": "api_heavy", "new_limit": {"requests": 50, "window": 60}}'
```

#### Compression Issues

**Compression Performance Problems:**
```bash
# Check compression statistics
curl -s http://localhost:8000/internal/compression/stats

# Analyze compression efficiency
curl -s http://localhost:8000/internal/compression/efficiency-analysis

# Adjust compression settings
curl -X POST http://localhost:8000/internal/compression/settings \
  -d '{"level": 3, "min_size": 4096}'
```

### Troubleshooting & Monitoring

#### Common Issues

##### Middleware Not Loading
**Symptoms:** Expected middleware features not working
**Diagnosis:**
```bash
curl -s http://localhost:8000/internal/middleware/stats | jq '.middleware_stack'
curl -s http://localhost:8000/internal/middleware/load-errors
```
**Solutions:**
- Check middleware configuration settings
- Verify dependency requirements are met
- Review application startup logs
- Validate middleware order conflicts

##### High Memory Usage
**Symptoms:** Increasing memory consumption over time
**Diagnosis:**
```bash
curl -s http://localhost:8000/internal/monitoring/memory-analysis | jq '.middleware_usage'
curl -s http://localhost:8000/internal/middleware/memory-breakdown
```
**Solutions:**
- Reduce monitoring retention periods
- Disable memory-intensive features
- Clear middleware caches periodically
- Optimize compression settings

##### Performance Impact
**Symptoms:** Increased response times after middleware deployment
**Diagnosis:**
```bash
curl -s http://localhost:8000/internal/middleware/performance-impact
curl -s http://localhost:8000/internal/monitoring/response-time-breakdown
```
**Solutions:**
- Profile individual middleware performance
- Adjust middleware order for optimization
- Enable async processing where possible
- Reduce logging verbosity

#### Debug Utilities

**Middleware Debug Mode:**
```bash
# Enable debug mode for detailed logging
export MIDDLEWARE_DEBUG_MODE=true

# Enable detailed performance profiling
export MIDDLEWARE_PERFORMANCE_PROFILING=true

# Restart with debug configuration
docker-compose restart backend

# Monitor debug output
tail -f logs/middleware_debug.log
```

**Request Tracing:**
```bash
# Enable request tracing through middleware stack
curl -H "X-Debug-Trace: true" -v http://localhost:8000/health

# Get detailed middleware execution trace
curl -s http://localhost:8000/internal/middleware/request-trace?request_id=<request_id>
```

### Escalation Procedures

#### Severity Levels

| Severity | Description | Response Time | Actions |
|----------|-------------|---------------|---------|
| **Critical** | Middleware stack failure, security bypass | < 15 minutes | Immediate escalation, disable affected middleware |
| **Warning** | Performance degradation, configuration issues | < 1 hour | Team notification, investigate and optimize |
| **Info** | Configuration warnings, minor issues | < 4 hours | Log review, scheduled maintenance |

#### Critical Escalation Response
```bash
# Immediate safety measures
curl -X POST http://localhost:8000/internal/middleware/emergency-mode/enable

# Disable problematic middleware
curl -X POST http://localhost:8000/internal/middleware/disable-all-non-essential

# Switch to basic middleware stack
curl -X POST http://localhost:8000/internal/middleware/switch-to-basic-stack

# Monitor recovery
watch -n 5 'curl -s http://localhost:8000/internal/middleware/health | jq ".status"'
```

## Best Practices

### Middleware Management
1. **Layered Configuration**: Use environment-specific configuration files
2. **Performance Monitoring**: Regular performance baseline establishment
3. **Graceful Degradation**: Ensure critical path remains functional if middleware fails
4. **Documentation**: Keep middleware configuration and procedures updated

### Security Considerations
1. **Header Security**: Verify security headers are properly applied
2. **Rate Limiting**: Configure appropriate limits for different client types
3. **Input Validation**: Ensure request size and content validation is active
4. **Monitoring**: Log security events and failed requests

### Performance Optimization
1. **Middleware Order**: Optimize order for performance and security
2. **Selective Enablement**: Only enable middleware features that are needed
3. **Resource Management**: Monitor memory and CPU impact of middleware
4. **Caching Strategy**: Use appropriate caching for middleware data

### Operational Excellence
1. **Health Monitoring**: Regular health checks and automated monitoring
2. **Configuration Management**: Version control all middleware configurations
3. **Incident Response**: Documented procedures for common middleware issues
4. **Performance Baselines**: Regular collection and analysis of performance data

## Related Documentation

- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Architectural context for middleware as infrastructure
- **[Dual API Architecture](../../reference/key-concepts/DUAL_API_ARCHITECTURE.md)**: How middleware applies to both public and internal APIs
- **[Monitoring Operations Guide](./MONITORING.md)**: Integration with monitoring systems for middleware metrics
- **[Security Operations Guide](./SECURITY.md)**: Security considerations and incident response
- **[Performance Optimization Guide](./PERFORMANCE_OPTIMIZATION.md)**: Performance tuning strategies for middleware
- **[Core Module Integration Guide](../developer/CORE_MODULE_INTEGRATION.md)**: Implementation patterns for middleware integration
- **[Exception Handling Guide](../developer/EXCEPTION_HANDLING.md)**: Exception handling patterns in middleware components