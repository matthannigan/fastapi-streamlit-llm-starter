# Operational Monitoring Guide

This guide provides operational procedures for monitoring the FastAPI-Streamlit-LLM Starter Template in production environments. It consolidates monitoring practices from infrastructure services into actionable runbooks for operations teams.

## Overview

The starter template includes comprehensive monitoring capabilities through the [Monitoring Infrastructure Service](../infrastructure/MONITORING.md). This operational guide focuses on day-to-day monitoring procedures, alert management, and system health verification.

## Core Monitoring Components

### System Health Checks

#### Automated Health Endpoints

| Endpoint | Purpose | Expected Response Time | Critical Threshold |
|----------|---------|----------------------|-------------------|
| `/health` | Basic application health | <100ms | >1000ms |
| `/internal/monitoring/overview` | Comprehensive system status | <500ms | >2000ms |
| `/internal/monitoring/health` | Infrastructure health checks | <300ms | >1500ms |

#### Health Check Procedures

**Daily Health Verification:**
```bash
# Basic health check
curl -w "@curl-format.txt" http://localhost:8000/health

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

#### Morning Health Check (5 minutes)
```bash
#!/bin/bash
# Daily health check script

echo "=== Daily Health Check $(date) ==="

# 1. Basic health verification
echo "Checking basic health..."
curl -f http://localhost:8000/health || echo "❌ Basic health check failed"

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
# Quick status check
curl -s http://localhost:8000/internal/monitoring/health | jq '.overall_status'

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

# 2. Verify service startup
curl http://localhost:8000/health
curl http://localhost:8501/

# 3. Run post-recovery health check
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