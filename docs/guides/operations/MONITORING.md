---
sidebar_label: Monitoring
---

# Operational Monitoring Guide

This guide provides operational procedures for monitoring the FastAPI-Streamlit-LLM Starter Template in production environments. It consolidates monitoring practices from infrastructure services into actionable runbooks for operations teams.

## Overview

The starter template includes comprehensive monitoring capabilities through the [Monitoring Infrastructure Service](../infrastructure/MONITORING.md). This operational guide focuses on day-to-day monitoring procedures, alert management, and system health verification.

## Core Monitoring Components

### Enhanced Health Check Infrastructure

The application uses a standardized `HealthChecker` infrastructure service that provides component-level monitoring with configurable timeouts, retry mechanisms, and graceful degradation.

#### Enhanced `/v1/health` Endpoint

The primary health endpoint now leverages the infrastructure health checker to provide comprehensive system status:

**Component-Level Monitoring:**
- **AI Model**: Verifies Google Gemini API key configuration  
- **Cache System**: Validates Redis connectivity with graceful fallback to memory cache
- **Resilience Infrastructure**: Checks circuit breakers and failure detection systems
- **Database**: Placeholder for future database health checks

**Enhanced Response Format:**
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

**Graceful Degradation Features:**
- Never fails the endpoint due to infrastructure issues
- Returns component-specific status information
- Configurable timeouts per component
- Automatic retry mechanisms with exponential backoff
- Maps internal `SystemHealthStatus` to backward-compatible `HealthResponse` format

#### Health Check Configuration

The health check system is fully configurable via environment variables:

```bash
# Global Health Check Settings
HEALTH_CHECK_TIMEOUT_MS=2000                    # Default timeout for all components
HEALTH_CHECK_RETRY_COUNT=1                      # Number of retry attempts per component
HEALTH_CHECK_ENABLED_COMPONENTS=["ai_model", "cache", "resilience"]

# Per-Component Timeout Overrides
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=2000          # AI model specific timeout
HEALTH_CHECK_CACHE_TIMEOUT_MS=2000             # Cache health check timeout
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=2000        # Resilience infrastructure timeout
```

### System Health Checks

#### Automated Health Endpoints

| Endpoint | Purpose | Expected Response Time | Critical Threshold |
|----------|---------|----------------------|-------------------|
| `/v1/health` | Enhanced component-level health checks | <100ms | >1000ms |
| `/internal/monitoring/overview` | Comprehensive system status | <500ms | >2000ms |
| `/internal/monitoring/health` | Infrastructure health checks | <300ms | >1500ms |
| `/internal/monitoring/middleware` | Middleware health and metrics | <200ms | >1000ms |

#### Health Check Procedures

**Daily Health Verification:**
```bash
# Enhanced health check with infrastructure monitoring
curl -w "@curl-format.txt" http://localhost:8000/v1/health

# Comprehensive monitoring overview
curl -s http://localhost:8000/internal/monitoring/overview | jq '.system_health'

# Infrastructure health status
curl -s http://localhost:8000/internal/monitoring/health | jq '.overall_status'
```

**Weekly Health Assessment:**
```bash
# Get detailed system metrics
curl -s http://localhost:8000/internal/monitoring/metrics?time_window_hours=168 | jq '.'

# Check performance trends
curl -s http://localhost:8000/internal/resilience/performance-metrics | jq '.trends'

# Review alert history
curl -s http://localhost:8000/internal/monitoring/alerts | jq '.by_severity'
```

### Middleware Monitoring

The enhanced middleware stack provides comprehensive monitoring capabilities for rate limiting, compression, security headers, request size limits, and API versioning. Monitoring these components is crucial for maintaining optimal performance and security.

> **📖 For complete middleware monitoring procedures**, see the **[Middleware Operations Guide](./MIDDLEWARE.md)** which provides:
> - Detailed middleware health check procedures
> - Performance optimization monitoring workflows
> - Security monitoring and incident response
> - Troubleshooting guidance for middleware issues

#### Middleware Health Endpoints

**Core Middleware Monitoring Endpoints:**

| Endpoint | Component | Purpose | Key Metrics |
|----------|-----------|---------|-------------|
| `/internal/monitoring/middleware` | All middleware | Overall middleware status | Stack health, execution order |
| `/internal/monitoring/rate-limiting` | Rate limiting | Rate limit violations and performance | Request rates, blocks, latency |
| `/internal/monitoring/compression` | Compression | Compression efficiency and performance | Compression ratio, CPU usage |
| `/internal/monitoring/request-size` | Request size limits | Request size violations and blocking | Size limits, violations, blocked requests |
| `/internal/monitoring/security-headers` | Security middleware | Security header compliance | Header presence, policy violations |
| `/internal/monitoring/api-versioning` | API versioning | Version detection and compatibility | Version distribution, detection errors |

#### Daily Middleware Monitoring

**Comprehensive Middleware Health Check:**
```bash
#!/bin/bash
# daily_middleware_monitoring.sh

echo "=== Daily Middleware Monitoring $(date) ==="

# 1. Overall middleware stack health
echo "=== Middleware Stack Status ==="
curl -s http://localhost:8000/internal/monitoring/middleware | jq '{
  status: .overall_status,
  active_middleware: .active_middleware,
  execution_time_ms: .total_execution_time,
  errors_today: .errors.today
}'

# 2. Rate limiting monitoring
echo "=== Rate Limiting Status ==="
curl -s http://localhost:8000/internal/monitoring/rate-limiting | jq '{
  status: .status,
  requests_per_minute_avg: .metrics.requests_per_minute.average,
  violations_today: .violations.today,
  blocked_clients: .blocked_clients.active_count,
  redis_health: .redis_connection.status
}'

# 3. Compression monitoring
echo "=== Compression Performance ==="
curl -s http://localhost:8000/internal/monitoring/compression | jq '{
  status: .status,
  compression_ratio_avg: .metrics.compression_ratio.average,
  cpu_overhead_percent: .performance.cpu_overhead,
  bandwidth_saved_mb: .metrics.bandwidth_saved.total_mb,
  errors_today: .errors.compression_errors.today
}'

# 4. Request size monitoring
echo "=== Request Size Limits ==="
curl -s http://localhost:8000/internal/monitoring/request-size | jq '{
  status: .status,
  violations_today: .violations.today,
  largest_request_mb: .metrics.largest_request.size_mb,
  blocked_requests: .blocked_requests.today,
  average_request_size_kb: .metrics.average_size.kb
}'

# 5. Security headers monitoring
echo "=== Security Headers Status ==="
curl -s http://localhost:8000/internal/monitoring/security-headers | jq '{
  status: .status,
  compliance_percentage: .compliance.percentage,
  missing_headers: .compliance.missing_headers,
  policy_violations: .violations.today
}'

# 6. API versioning monitoring
echo "=== API Versioning Status ==="
curl -s http://localhost:8000/internal/monitoring/api-versioning | jq '{
  status: .status,
  version_distribution: .metrics.version_usage,
  detection_errors: .errors.detection_errors.today,
  compatibility_issues: .compatibility.issues_today
}'

echo "=== Middleware monitoring completed ==="
```

#### Middleware Performance KPIs

**Key Performance Indicators for Middleware:**

| Metric | Target | Good | Needs Attention |
|--------|--------|------|-----------------|
| **Middleware Execution Time** | < 50ms | < 20ms | > 100ms |
| **Rate Limit Violations** | < 5% of requests | < 1% | > 10% |
| **Compression Ratio** | > 60% | > 75% | < 40% |
| **Request Size Violations** | < 1% | < 0.1% | > 2% |
| **Security Header Compliance** | 100% | 100% | < 95% |
| **Version Detection Success** | > 99% | > 99.5% | < 98% |

#### Enhanced Health Check Performance KPIs

**Health Check Infrastructure Performance:**

| Metric | Target | Good | Needs Attention |
|--------|--------|------|-----------------|
| **Overall Health Check Response** | < 100ms | < 50ms | > 200ms |
| **Component Check Timeout** | < 2000ms | < 1000ms | > 3000ms |
| **Health Check Success Rate** | > 99% | > 99.5% | < 98% |
| **Component Availability** | > 95% | > 99% | < 90% |
| **Retry Success Rate** | > 80% | > 90% | < 70% |

#### Middleware Alerting

**Critical Middleware Alerts:**
```bash
# Monitor for critical middleware issues
curl -s http://localhost:8000/internal/monitoring/middleware-alerts | jq '.'

# Check for high-severity middleware events
curl -s http://localhost:8000/internal/monitoring/alerts | \
  jq '.alerts[] | select(.component | startswith("middleware")) | select(.severity == "high" or .severity == "critical")'
```

**Automated Middleware Alerting Script:**
```bash
#!/bin/bash
# middleware_alerting.sh

ALERT_WEBHOOK="https://alerts.company.com/middleware"

# Check middleware stack health
MIDDLEWARE_STATUS=$(curl -s http://localhost:8000/internal/monitoring/middleware | jq -r '.overall_status')

if [[ "$MIDDLEWARE_STATUS" != "healthy" ]]; then
    curl -X POST "$ALERT_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{
        \"severity\": \"high\",
        \"component\": \"middleware_stack\",
        \"message\": \"Middleware stack status: $MIDDLEWARE_STATUS\",
        \"timestamp\": \"$(date -Iseconds)\"
      }"
fi

# Check rate limiting violations
RATE_VIOLATIONS=$(curl -s http://localhost:8000/internal/monitoring/rate-limiting | jq -r '.violations.last_hour')

if [[ "$RATE_VIOLATIONS" -gt 100 ]]; then
    curl -X POST "$ALERT_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{
        \"severity\": \"medium\",
        \"component\": \"rate_limiting\",
        \"message\": \"High rate limiting violations: $RATE_VIOLATIONS in last hour\",
        \"timestamp\": \"$(date -Iseconds)\"
      }"
fi

# Check compression performance
COMPRESSION_RATIO=$(curl -s http://localhost:8000/internal/monitoring/compression | jq -r '.metrics.compression_ratio.last_hour')

if [[ $(echo "$COMPRESSION_RATIO < 0.5" | bc) -eq 1 ]]; then
    curl -X POST "$ALERT_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{
        \"severity\": \"low\",
        \"component\": \"compression\",
        \"message\": \"Low compression ratio: $COMPRESSION_RATIO\",
        \"timestamp\": \"$(date -Iseconds)\"
      }"
fi
```

#### Health Check Component Troubleshooting

**AI Model Health Issues:**
```bash
# Symptom: ai_model_available: false
# Diagnosis: Check GEMINI_API_KEY environment variable
echo "Checking AI Model Configuration:"
echo "GEMINI_API_KEY set: ${GEMINI_API_KEY:+YES}"
echo "Key length: ${#GEMINI_API_KEY}"

# Resolution: Set valid Gemini API key and restart application
export GEMINI_API_KEY="your-valid-api-key"
# Restart application
```

**Cache Health Issues:**
```bash
# Symptom: cache_healthy: false
# Diagnosis: Redis connectivity problems
echo "Checking Cache Configuration:"
echo "Redis URL: ${REDIS_URL:-redis://localhost:6379}"
redis-cli ping || echo "Redis not accessible"

# Check cache fallback status
curl -s http://localhost:8000/internal/cache/stats | jq '.redis.status, .memory.status'

# Resolution: Check Redis service status and REDIS_URL configuration
sudo systemctl status redis  # or docker-compose ps redis
```

**Resilience Health Issues:**
```bash
# Symptom: resilience_healthy: false
# Diagnosis: Circuit breakers in open state
echo "Checking Resilience Status:"
curl -s http://localhost:8000/internal/resilience/circuit-breakers | jq '.'

# Check for open circuit breakers
curl -s http://localhost:8000/internal/resilience/health | jq '.open_circuit_breakers[]'

# Resolution: Reset circuit breakers if appropriate
curl -X POST http://localhost:8000/internal/resilience/circuit-breakers/ai_service/reset
```

**Health Check Timeout Issues:**
```bash
# Symptom: Health checks timing out
# Diagnosis: Check timeout configuration
echo "Health Check Timeouts:"
echo "Global: ${HEALTH_CHECK_TIMEOUT_MS:-2000}ms"
echo "AI Model: ${HEALTH_CHECK_AI_MODEL_TIMEOUT_MS:-2000}ms"
echo "Cache: ${HEALTH_CHECK_CACHE_TIMEOUT_MS:-2000}ms"
echo "Resilience: ${HEALTH_CHECK_RESILIENCE_TIMEOUT_MS:-2000}ms"

# Resolution: Increase timeout values for slow components
export HEALTH_CHECK_TIMEOUT_MS=5000
export HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
# Restart application
```

**Component Retry Issues:**
```bash
# Symptom: Components failing intermittently
# Diagnosis: Check retry configuration
echo "Retry Configuration:"
echo "Retry Count: ${HEALTH_CHECK_RETRY_COUNT:-1}"

# Resolution: Increase retry count for unstable components
export HEALTH_CHECK_RETRY_COUNT=3
# Restart application
```

**Health Check Component Enablement:**
```bash
# Disable problematic components temporarily
export HEALTH_CHECK_ENABLED_COMPONENTS='["ai_model", "cache"]'  # Exclude resilience
# Restart application

# Verify component exclusion
curl -s http://localhost:8000/v1/health | jq 'keys[]'
```

#### Troubleshooting Middleware Issues

**Common Middleware Issues and Monitoring:**

1. **Rate Limiting Issues:**
```bash
# Check rate limiting performance
curl -s http://localhost:8000/internal/monitoring/rate-limiting/diagnostics | jq '.'

# Identify clients hitting rate limits
curl -s http://localhost:8000/internal/monitoring/rate-limiting/top-violators | jq '.'
```

2. **Compression Issues:**
```bash
# Analyze compression performance problems
curl -s http://localhost:8000/internal/monitoring/compression/diagnostics | jq '.'

# Check for compression algorithm issues
curl -s http://localhost:8000/internal/monitoring/compression/algorithm-performance | jq '.'
```

3. **Request Size Issues:**
```bash
# Monitor request size patterns
curl -s http://localhost:8000/internal/monitoring/request-size/patterns | jq '.'

# Check for DoS attack indicators
curl -s http://localhost:8000/internal/monitoring/request-size/attack-patterns | jq '.'
```

### Performance Monitoring

#### Key Performance Indicators (KPIs)

**Application Performance:**
- Response time: P95 < 2000ms, P99 < 5000ms
- Error rate: < 1% for API endpoints
- Cache hit ratio: > 70% for text processing
- Memory usage: < 80% of allocated resources

**Infrastructure Performance:**
- Redis connection: < 10ms response time
- AI service latency: P95 < 30000ms (varies by operation)
- Circuit breaker state: All breakers closed (healthy state)
- Configuration load time: < 100ms

#### Performance Monitoring Commands

**Real-time Performance Check:**
```bash
# API performance metrics
curl -s http://localhost:8000/internal/monitoring/overview | jq '.system_health'

# Cache performance analytics
curl -s http://localhost:8000/internal/cache/stats | jq '.performance'

# Resilience system performance
curl -s http://localhost:8000/internal/resilience/metrics | jq '.performance_summary'
```

**Performance Trend Analysis:**
```bash
# 24-hour performance trends
curl -s "http://localhost:8000/internal/monitoring/metrics?time_window_hours=24" \
  | jq '.cache_metrics.performance_trends'

# Configuration usage patterns
curl -s http://localhost:8000/internal/resilience/usage-statistics | jq '.usage_patterns'

# Historical performance comparison
curl -s "http://localhost:8000/internal/resilience/preset-trends/production" | jq '.performance_evolution'
```

### Alert Management

#### Alert Severity Levels

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **Critical** | Service outage, data loss risk | < 15 minutes | Immediate escalation |
| **Warning** | Performance degradation | < 1 hour | Team notification |
| **Info** | Operational notices | < 4 hours | Log review |

#### Alert Response Procedures

**Critical Alerts:**
1. **Immediate Assessment:**
   ```bash
   # Check current alert status
   curl -s http://localhost:8000/internal/monitoring/alerts | jq '.alerts[] | select(.severity == "critical")'
   
   # Verify system health
   curl -s http://localhost:8000/internal/monitoring/health
   ```

2. **Circuit Breaker Alerts:**
   ```bash
   # Check circuit breaker states
   curl -s http://localhost:8000/internal/resilience/circuit-breakers
   
   # Reset specific circuit breaker if safe
   curl -X POST http://localhost:8000/internal/resilience/circuit-breakers/{name}/reset
   ```

3. **Memory Alerts:**
   ```bash
   # Check memory usage
   curl -s http://localhost:8000/internal/monitoring/overview | jq '.cache_performance.memory_usage'
   
   # Force cache cleanup if needed
   curl -X POST http://localhost:8000/internal/cache/cleanup
   ```

**Warning Alerts:**
1. **Performance Degradation:**
   ```bash
   # Analyze performance bottlenecks
   curl -s http://localhost:8000/internal/monitoring/performance
   
   # Check resilience system status
   curl -s http://localhost:8000/internal/resilience/health
   ```

2. **Cache Performance Issues:**
   ```bash
   # Detailed cache analytics
   curl -s http://localhost:8000/internal/cache/performance-analysis
   
   # Cache optimization recommendations
   curl -s http://localhost:8000/internal/cache/optimization-recommendations
   ```

### Monitoring Dashboard Setup

#### Grafana Dashboard Configuration

**Prerequisites:**
- Grafana instance configured
- Prometheus metrics collection enabled
- Monitoring webhook notifications configured

**Dashboard Panels:**

1. **System Health Overview:**
   - Overall system status indicator
   - Component health matrix
   - Active alerts summary

2. **Performance Metrics:**
   - API response time trends
   - Cache hit ratio over time
   - Memory usage patterns
   - Error rate tracking

3. **Infrastructure Status:**
   - Circuit breaker states
   - Redis connection health
   - Configuration load performance
   - AI service response times

#### External Monitoring Integration

**Prometheus Metrics Export:**
```bash
# Enable Prometheus metrics
export ENABLE_EXTERNAL_MONITORING=true
export PROMETHEUS_GATEWAY_URL=http://prometheus-gateway:9091

# Verify metrics export
curl http://localhost:8000/internal/monitoring/metrics?format=prometheus
```

**Custom Webhook Alerts:**
```bash
# Configure webhook notifications
export MONITORING_WEBHOOK_URL=https://your-monitoring-system.com/webhooks/alerts

# Test webhook notification
curl -X POST http://localhost:8000/internal/monitoring/test-webhook
```

## Operational Procedures

### Daily Operations

#### Enhanced Component Health Monitoring

**Component-Level Health Check Script:**
```bash
#!/bin/bash
# enhanced_health_monitoring.sh

echo "=== Enhanced Health Check Monitoring $(date) ==="

# 1. Overall system health with component breakdown
echo "=== System Health Status ==="
curl -s http://localhost:8000/v1/health | jq '{
  status: .status,
  ai_model_available: .ai_model_available,
  resilience_healthy: .resilience_healthy,
  cache_healthy: .cache_healthy,
  timestamp: .timestamp
}'

# 2. Component-specific analysis
HEALTH_RESPONSE=$(curl -s http://localhost:8000/v1/health)
AI_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.ai_model_available')
CACHE_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.cache_healthy')  
RESILIENCE_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.resilience_healthy')

echo "=== Component Analysis ==="
echo "AI Model: $AI_STATUS"
echo "Cache: $CACHE_STATUS"  
echo "Resilience: $RESILIENCE_STATUS"

# 3. Alert on component failures
if [ "$AI_STATUS" = "false" ]; then
    echo "🚨 ALERT: AI Model unavailable - check GEMINI_API_KEY configuration"
fi

if [ "$CACHE_STATUS" = "false" ]; then
    echo "🚨 ALERT: Cache unhealthy - check Redis connectivity"
fi

if [ "$RESILIENCE_STATUS" = "false" ]; then
    echo "🚨 ALERT: Resilience degraded - check circuit breakers"
fi

echo "=== Enhanced health monitoring completed ==="
```

**Health Check Configuration Validation:**
```bash
#!/bin/bash
# validate_health_config.sh

echo "=== Health Check Configuration ==="
echo "Global Timeout: ${HEALTH_CHECK_TIMEOUT_MS:-2000}ms"
echo "AI Model Timeout: ${HEALTH_CHECK_AI_MODEL_TIMEOUT_MS:-2000}ms"
echo "Cache Timeout: ${HEALTH_CHECK_CACHE_TIMEOUT_MS:-2000}ms"
echo "Resilience Timeout: ${HEALTH_CHECK_RESILIENCE_TIMEOUT_MS:-2000}ms"
echo "Retry Count: ${HEALTH_CHECK_RETRY_COUNT:-1}"
echo "Enabled Components: ${HEALTH_CHECK_ENABLED_COMPONENTS:-['ai_model', 'cache', 'resilience']}"
```

#### Morning Health Check (5 minutes)
```bash
#!/bin/bash
# Daily health check script

echo "=== Daily Health Check $(date) ==="

# 1. Enhanced health verification with component details
echo "Checking enhanced health status..."
curl -f http://localhost:8000/v1/health || echo "❌ Enhanced health check failed"

# 2. System overview
echo "Getting system overview..."
OVERVIEW=$(curl -s http://localhost:8000/internal/monitoring/overview)
STATUS=$(echo "$OVERVIEW" | jq -r '.system_health.status')
echo "System status: $STATUS"

# 3. Active alerts
echo "Checking active alerts..."
ALERTS=$(curl -s http://localhost:8000/internal/monitoring/alerts)
CRITICAL_COUNT=$(echo "$ALERTS" | jq '.by_severity.critical')
WARNING_COUNT=$(echo "$ALERTS" | jq '.by_severity.warning')
echo "Critical alerts: $CRITICAL_COUNT, Warning alerts: $WARNING_COUNT"

# 4. Performance summary
echo "Performance summary..."
CACHE_HIT_RATIO=$(echo "$OVERVIEW" | jq '.cache_performance.stats.hit_ratio')
ERROR_RATE=$(echo "$OVERVIEW" | jq '.system_health.error_rate')
echo "Cache hit ratio: ${CACHE_HIT_RATIO}%, Error rate: ${ERROR_RATE}%"

echo "=== Health check complete ==="
```

#### Weekly Operations Review (30 minutes)

1. **Performance Trend Analysis:**
   ```bash
   # Generate weekly performance report
   curl -s "http://localhost:8000/internal/monitoring/metrics?time_window_hours=168" > weekly_metrics.json
   
   # Analyze trends
   jq '.cache_metrics.performance_trends' weekly_metrics.json
   jq '.request_metrics.avg_response_time' weekly_metrics.json
   ```

2. **Alert Pattern Review:**
   ```bash
   # Review alert patterns
   curl -s http://localhost:8000/internal/monitoring/alerts/history?days=7 | jq '.patterns'
   
   # Check alert frequency trends
   curl -s http://localhost:8000/internal/monitoring/alerts/trends | jq '.weekly_summary'
   ```

3. **Capacity Planning:**
   ```bash
   # Memory usage trends
   curl -s http://localhost:8000/internal/monitoring/memory-trends?days=7
   
   # Performance capacity analysis
   curl -s http://localhost:8000/internal/resilience/capacity-analysis
   ```

### Incident Response

#### Service Degradation Response

**Step 1: Initial Assessment (< 5 minutes)**
```bash
# Enhanced component status check
curl -s http://localhost:8000/v1/health | jq '{
  overall_status: .status,
  ai_model: .ai_model_available,
  cache: .cache_healthy,
  resilience: .resilience_healthy
}'

# Check for critical alerts
curl -s http://localhost:8000/internal/monitoring/alerts | jq '.alerts[] | select(.severity == "critical")'

# Verify external dependencies
curl -s http://localhost:8000/internal/monitoring/dependencies
```

**Step 2: Identify Root Cause (< 10 minutes)**
```bash
# Check circuit breaker states
curl -s http://localhost:8000/internal/resilience/circuit-breakers

# Analyze performance bottlenecks
curl -s http://localhost:8000/internal/monitoring/performance-analysis

# Review recent configuration changes
curl -s http://localhost:8000/internal/resilience/config/recent-changes
```

**Step 3: Immediate Mitigation (< 15 minutes)**
```bash
# Reset failed circuit breakers (if appropriate)
curl -X POST http://localhost:8000/internal/resilience/circuit-breakers/ai_service/reset

# Clear cache if memory issues
curl -X POST http://localhost:8000/internal/cache/clear

# Switch to fallback configuration if needed
curl -X POST http://localhost:8000/internal/resilience/config/apply-preset -d '{"preset": "conservative"}'
```

**Step 4: Monitor Recovery**
```bash
# Monitor system recovery
watch -n 10 'curl -s http://localhost:8000/internal/monitoring/health | jq ".overall_status"'

# Track performance improvement
curl -s http://localhost:8000/internal/monitoring/recovery-metrics
```

#### Complete Service Outage Response

**Immediate Actions:**
1. Verify external dependencies (Redis, AI services)
2. Check container/process health
3. Review application logs for errors
4. Validate configuration integrity

**Recovery Steps:**
```bash
# 1. Restart services in order
docker-compose restart redis
docker-compose restart backend
docker-compose restart frontend

# 2. Verify service startup with enhanced health checks
curl http://localhost:8000/v1/health
curl http://localhost:8501/

# 3. Verify component-specific recovery
echo "Component Recovery Status:"
curl -s http://localhost:8000/v1/health | jq '.ai_model_available, .cache_healthy, .resilience_healthy'

# 4. Run post-recovery health check
curl -s http://localhost:8000/internal/monitoring/post-recovery-check
```

### Maintenance Procedures

#### Planned Maintenance

**Pre-maintenance Checklist:**
1. Schedule maintenance window
2. Notify stakeholders
3. Backup current configuration
4. Prepare rollback procedures

**Maintenance Procedures:**
```bash
# 1. Enable maintenance mode
curl -X POST http://localhost:8000/internal/monitoring/maintenance-mode/enable

# 2. Backup current state
curl -s http://localhost:8000/internal/cache/backup > cache_backup.json
curl -s http://localhost:8000/internal/resilience/config/export > config_backup.json

# 3. Perform maintenance tasks
# (deployment, configuration updates, etc.)

# 4. Post-maintenance verification
curl http://localhost:8000/internal/monitoring/health
curl -s http://localhost:8000/internal/monitoring/post-maintenance-check

# 5. Disable maintenance mode
curl -X POST http://localhost:8000/internal/monitoring/maintenance-mode/disable
```

## Monitoring Tools and Utilities

### Monitoring Scripts

#### System Health Monitor Script
```bash
#!/bin/bash
# monitor_system.sh - Continuous system monitoring

HEALTH_URL="http://localhost:8000/internal/monitoring/health"
ALERT_URL="http://localhost:8000/internal/monitoring/alerts"
CHECK_INTERVAL=60  # seconds

while true; do
    # Check system health
    HEALTH=$(curl -s "$HEALTH_URL")
    STATUS=$(echo "$HEALTH" | jq -r '.overall_status')
    
    if [ "$STATUS" != "healthy" ]; then
        echo "$(date): System status is $STATUS"
        
        # Get active alerts
        ALERTS=$(curl -s "$ALERT_URL")
        echo "Active alerts:"
        echo "$ALERTS" | jq '.alerts[] | select(.severity == "critical" or .severity == "warning")'
    fi
    
    sleep $CHECK_INTERVAL
done
```

#### Performance Baseline Script
```bash
#!/bin/bash
# baseline_performance.sh - Establish performance baselines

OUTPUT_FILE="performance_baseline_$(date +%Y%m%d_%H%M%S).json"

echo "Collecting performance baseline..."

# Collect comprehensive metrics
curl -s "http://localhost:8000/internal/monitoring/metrics?time_window_hours=24" > "$OUTPUT_FILE"

# Extract key metrics
jq '.cache_metrics.hit_ratio' "$OUTPUT_FILE"
jq '.request_metrics.avg_response_time' "$OUTPUT_FILE"
jq '.system_health.error_rate' "$OUTPUT_FILE"

echo "Baseline saved to $OUTPUT_FILE"
```

### Environment-Specific Configurations

#### Development Environment
```bash
# Development monitoring settings
export MONITORING_LOG_LEVEL=DEBUG
export CACHE_MONITORING_RETENTION_HOURS=2
export ALERT_MEMORY_WARNING_MB=50
export METRICS_EXPORT_INTERVAL=30
```

#### Production Environment
```bash
# Production monitoring settings
export MONITORING_LOG_LEVEL=INFO
export CACHE_MONITORING_RETENTION_HOURS=24
export ALERT_MEMORY_WARNING_MB=200
export METRICS_EXPORT_INTERVAL=60
export ENABLE_EXTERNAL_MONITORING=true
```

## Troubleshooting

### Common Monitoring Issues

#### Monitoring Data Not Collecting
**Symptoms:** No metrics visible in endpoints
**Diagnosis:**
```bash
curl http://localhost:8000/internal/monitoring/config
curl http://localhost:8000/internal/monitoring/status
```
**Solutions:**
- Verify `ENABLE_MONITORING=true`
- Check monitoring service initialization
- Review logs for monitoring errors

#### High Memory Usage from Monitoring
**Symptoms:** Continuous memory growth
**Diagnosis:**
```bash
curl http://localhost:8000/internal/monitoring/memory-stats
```
**Solutions:**
- Reduce retention periods
- Enable compression
- Clear old monitoring data

#### Performance Impact from Monitoring
**Symptoms:** Increased response times
**Diagnosis:**
```bash
curl http://localhost:8000/internal/monitoring/performance-impact
```
**Solutions:**
- Enable batch processing
- Reduce monitoring frequency
- Use sampling for high-volume operations

## Best Practices

### Monitoring Strategy
1. **Monitor Critical Paths:** Focus on business-critical operations
2. **Set Realistic Thresholds:** Base alerts on historical performance data
3. **Regular Review:** Weekly review of alert patterns and thresholds
4. **Documentation:** Keep monitoring procedures updated

### Alert Management
1. **Alert Hierarchy:** Use appropriate severity levels
2. **Alert Fatigue Prevention:** Avoid over-alerting on minor issues
3. **Context Information:** Include relevant metadata in alerts
4. **Response Documentation:** Document response procedures for each alert type

### Performance Optimization
1. **Baseline Establishment:** Regular performance baseline collection
2. **Trend Analysis:** Monitor performance trends over time
3. **Capacity Planning:** Use monitoring data for capacity decisions
4. **Optimization Opportunities:** Regular review of optimization recommendations

## Related Documentation

- **[Monitoring Infrastructure Service](../infrastructure/MONITORING.md)**: Technical implementation details
- **[Resilience Infrastructure](../infrastructure/RESILIENCE.md)**: Resilience patterns and configuration
- **[Cache Infrastructure](../infrastructure/CACHE.md)**: Cache performance monitoring
- **[Troubleshooting Guide](./TROUBLESHOOTING.md)**: General troubleshooting procedures
- **[Performance Optimization Guide](./PERFORMANCE_OPTIMIZATION.md)**: Performance tuning procedures