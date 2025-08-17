---
sidebar_label: Troubleshooting
---

# Troubleshooting Guide

This guide provides systematic troubleshooting workflows for common issues in the FastAPI-Streamlit-LLM Starter Template. It includes decision trees, diagnostic procedures, and resolution steps for operational teams.

## Overview

The troubleshooting procedures are organized by issue category with escalating diagnostic steps. Each section includes symptoms, diagnostic commands, and resolution procedures.

## Quick Diagnostic Commands

### System Health Check
```bash
# Immediate health status
curl -f http://localhost:8000/health

# Comprehensive system status
curl -s http://localhost:8000/internal/monitoring/overview | jq '.'

# Infrastructure component health
curl -s http://localhost:8000/internal/monitoring/health | jq '.components[]'
```

### Service Connectivity
```bash
# Backend API connectivity
curl -f http://localhost:8000/docs

# Frontend accessibility
curl -f http://localhost:8501/

# Internal API accessibility
curl -f http://localhost:8000/internal/docs
```

### Component Status
```bash
# Cache system status
curl -s http://localhost:8000/internal/cache/stats | jq '.health'

# Resilience system status
curl -s http://localhost:8000/internal/resilience/health | jq '.'

# Circuit breaker states
curl -s http://localhost:8000/internal/resilience/circuit-breakers | jq '.'
```

## Application Startup Issues

### Service Won't Start

#### Symptoms
- Application fails to start
- Container exits immediately
- Port binding errors
- Import/dependency errors

#### Diagnostic Steps

**Step 1: Check Basic Requirements**
```bash
# Verify Python environment
python --version
which python

# Check virtual environment
source .venv/bin/activate || echo "Virtual environment not found"

# Verify dependencies
pip list | grep -E "(fastapi|streamlit|pydantic|redis)"
```

**Step 2: Check Configuration**
```bash
# Verify environment variables
echo $GEMINI_API_KEY
echo $API_KEY
echo $REDIS_URL

# Check configuration validity
cd backend && python -c "from app.core.config import get_settings; print(get_settings())"
```

**Step 3: Check Port Availability**
```bash
# Check if ports are available
netstat -tlnp | grep -E ":8000|:8501|:6379"
lsof -i :8000
lsof -i :8501
```

#### Resolution Steps

**Missing Dependencies:**
```bash
# Reinstall dependencies
make install

# Or manually:
cd backend && pip install -r requirements.txt
cd frontend && pip install -r requirements.txt
```

**Configuration Issues:**
```bash
# Create .env file with required variables
cat > .env << EOF
GEMINI_API_KEY=your-api-key-here
API_KEY=your-api-key-here
REDIS_URL=redis://localhost:6379
RESILIENCE_PRESET=development
EOF
```

**Port Conflicts:**
```bash
# Kill processes using required ports
sudo kill $(lsof -t -i:8000)
sudo kill $(lsof -t -i:8501)

# Or use different ports
export BACKEND_PORT=8001
export FRONTEND_PORT=8502
```

### Database/Redis Connection Issues

#### Symptoms
- Redis connection errors
- Cache operations failing
- "Connection refused" errors

#### Diagnostic Steps

**Step 1: Verify Redis Service**
```bash
# Check Redis service status
redis-cli ping

# Check Redis connectivity
telnet localhost 6379

# Verify Redis configuration
redis-cli info server
```

**Step 2: Check Network Configuration**
```bash
# Test Redis connection with URL
redis-cli -u $REDIS_URL ping

# Check firewall/network rules
iptables -L | grep 6379
```

#### Resolution Steps

**Redis Not Running:**
```bash
# Start Redis service
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:alpine

# Or with Docker Compose
docker-compose up -d redis
```

**Connection Configuration:**
```bash
# Update Redis URL for Docker
export REDIS_URL=redis://localhost:6379

# For Docker Compose
export REDIS_URL=redis://redis:6379

# Test connection
redis-cli -u $REDIS_URL ping
```

**Redis Memory Issues:**
```bash
# Check Redis memory usage
redis-cli info memory

# Clear Redis cache if needed
redis-cli flushall

# Configure memory policy
redis-cli config set maxmemory-policy allkeys-lru
```

### Phase 2 Cache Architecture Issues (NEW)

**The Phase 2 cache architecture** introduces inheritance-based caching with GenericRedisCache and AIResponseCache. This section covers troubleshooting issues specific to the new architecture.

#### Symptoms
- AIResponseCacheConfig validation errors
- Cache inheritance hierarchy issues
- Parameter mapping failures
- Migration between cache implementations
- Performance degradation after upgrade

#### Diagnostic Steps

**Step 1: Verify Cache Configuration**
```bash
# Test AIResponseCacheConfig validation
curl -s "http://localhost:8000/internal/cache/config/validate" | jq '.'

# Check cache inheritance setup
curl -s "http://localhost:8000/internal/cache/inheritance-status" | jq '.'

# Verify parameter mapping
curl -s "http://localhost:8000/internal/cache/parameter-mapping" | jq '.'
```

**Step 2: Check Cache Component Status**
```bash
# Check GenericRedisCache status
curl -s "http://localhost:8000/internal/cache/generic/status" | jq '.'

# Check AIResponseCache status
curl -s "http://localhost:8000/internal/cache/ai/status" | jq '.'

# Verify supporting components
curl -s "http://localhost:8000/internal/cache/components/status" | jq '.'
```

**Step 3: Performance Analysis**
```bash
# Compare performance between cache types
curl -s "http://localhost:8000/internal/cache/performance/comparison" | jq '.'

# Check for inheritance overhead
curl -s "http://localhost:8000/internal/cache/performance/inheritance-metrics" | jq '.'

# Analyze text tier performance
curl -s "http://localhost:8000/internal/cache/ai/text-tier-analysis" | jq '.'
```

#### Resolution Steps

**Configuration Validation Failures:**
```bash
# Check specific validation errors
curl -X POST "http://localhost:8000/internal/cache/config/validate" \
  -H "Content-Type: application/json" \
  -d '{"redis_url": "redis://localhost:6379", "default_ttl": 3600}' | jq '.'

# Use configuration presets for known-good configurations
export CACHE_CONFIG_PRESET=development  # or production, testing

# Validate current environment configuration
curl -s "http://localhost:8000/internal/cache/config/current" | jq '.validation_result'
```

**Cache Inheritance Issues:**
```bash
# Reset cache to use inheritance properly
curl -X POST "http://localhost:8000/internal/cache/reset-inheritance"

# Force cache reinitialization
curl -X POST "http://localhost:8000/internal/cache/reinitialize" \
  -H "Content-Type: application/json" \
  -d '{"use_inheritance": true, "validate_config": true}'

# Check inheritance chain
curl -s "http://localhost:8000/internal/cache/inheritance-chain" | jq '.'
```

**Parameter Mapping Problems:**
```bash
# Test parameter mapping with current configuration
curl -X POST "http://localhost:8000/internal/cache/parameter-mapping/test" \
  -H "Content-Type: application/json" \
  -d '{"redis_url": "redis://localhost:6379", "operation_ttls": {"summarize": 7200}}'

# Get parameter mapping recommendations
curl -s "http://localhost:8000/internal/cache/parameter-mapping/recommendations" | jq '.'

# Validate specific parameter combinations
curl -X POST "http://localhost:8000/internal/cache/parameter-mapping/validate" \
  -H "Content-Type: application/json" \
  -d '{"ai_params": {...}, "generic_params": {...}}'
```

**Cache Migration Issues:**
```bash
# Check migration status
curl -s "http://localhost:8000/internal/cache/migration/status" | jq '.'

# Test migration compatibility
curl -X POST "http://localhost:8000/internal/cache/migration/compatibility-check" \
  -H "Content-Type: application/json" \
  -d '{"source_type": "legacy", "target_type": "phase2"}'

# Run safe migration with validation
curl -X POST "http://localhost:8000/internal/cache/migration/execute" \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 100, "validate_data": true, "dry_run": true}'
```

**Performance Regression:**
```bash
# Get performance benchmarks
curl -s "http://localhost:8000/internal/cache/performance/benchmarks" | jq '.'

# Compare with baseline performance
curl -X POST "http://localhost:8000/internal/cache/performance/compare" \
  -H "Content-Type: application/json" \
  -d '{"compare_with": "baseline", "include_inheritance_metrics": true}'

# Optimize cache configuration based on usage patterns
curl -X POST "http://localhost:8000/internal/cache/optimize" \
  -H "Content-Type: application/json" \
  -d '{"analyze_inheritance_patterns": true, "optimize_text_tiers": true}'
```

**Component Integration Issues:**
```bash
# Reset all cache components
curl -X POST "http://localhost:8000/internal/cache/components/reset"

# Test individual component functionality
curl -X POST "http://localhost:8000/internal/cache/components/test" \
  -H "Content-Type: application/json" \
  -d '{"component": "key_generator", "test_text_sizes": [100, 1000, 10000]}'

# Validate component integration
curl -s "http://localhost:8000/internal/cache/components/integration-test" | jq '.'
```

#### Common Phase 2 Issues and Solutions

**Issue**: AIResponseCacheConfig validation fails with "operation_ttls must be dict"
```bash
# Solution: Ensure operation_ttls is properly formatted
export CACHE_OPERATION_TTLS='{"summarize": 7200, "sentiment": 86400}'

# Or use API to set configuration
curl -X POST "http://localhost:8000/internal/cache/config/set" \
  -H "Content-Type: application/json" \
  -d '{"operation_ttls": {"summarize": 7200, "sentiment": 86400}}'
```

**Issue**: Cache performance degraded after Phase 2 upgrade
```bash
# Solution: Run inheritance performance analysis
curl -s "http://localhost:8000/internal/cache/performance/inheritance-overhead" | jq '.'

# Optimize text tier configuration
curl -X POST "http://localhost:8000/internal/cache/ai/optimize-text-tiers" \
  -H "Content-Type: application/json" \
  -d '{"analyze_usage_patterns": true, "adjust_thresholds": true}'
```

**Issue**: GenericRedisCache not falling back to memory properly
```bash
# Solution: Test fallback mechanism
curl -X POST "http://localhost:8000/internal/cache/generic/test-fallback" \
  -H "Content-Type: application/json" \
  -d '{"simulate_redis_failure": true}'

# Check fallback configuration
curl -s "http://localhost:8000/internal/cache/generic/fallback-config" | jq '.'
```

**Issue**: Cache parameter mapping errors between AI and generic parameters
```bash
# Solution: Use parameter mapper validation
curl -X POST "http://localhost:8000/internal/cache/parameter-mapping/fix" \
  -H "Content-Type: application/json" \
  -d '{"auto_correct": true, "validate_result": true}'

# Get corrected parameter mapping
curl -s "http://localhost:8000/internal/cache/parameter-mapping/corrected" | jq '.'
```

## API Response Issues

### Slow API Responses

#### Symptoms
- API responses > 5 seconds
- Timeout errors
- High response time alerts

#### Diagnostic Steps

**Step 1: Identify Bottlenecks**
```bash
# Check current performance metrics
curl -s http://localhost:8000/internal/monitoring/performance | jq '.'

# Analyze response time patterns
curl -s http://localhost:8000/internal/monitoring/metrics | jq '.request_metrics'

# Check cache performance
curl -s http://localhost:8000/internal/cache/performance-analysis | jq '.'
```

**Step 2: Check Resource Usage**
```bash
# CPU and memory usage
top -p $(pgrep -f "uvicorn")
ps aux | grep uvicorn

# Check system load
uptime
iostat -x 1 5
```

**Step 3: Analyze Circuit Breaker States**
```bash
# Check for open circuit breakers
curl -s http://localhost:8000/internal/resilience/circuit-breakers | jq '.[] | select(.state == "open")'

# Review recent failures
curl -s http://localhost:8000/internal/resilience/metrics | jq '.recent_failures'
```

#### Resolution Steps

**Cache Optimization:**
```bash
# Check cache hit ratio
curl -s http://localhost:8000/internal/cache/stats | jq '.hit_ratio'

# Clear cache if corrupted
curl -X POST http://localhost:8000/internal/cache/clear

# Optimize cache configuration
curl -X POST http://localhost:8000/internal/cache/optimize
```

**Circuit Breaker Recovery:**
```bash
# Reset failed circuit breakers
curl -X POST http://localhost:8000/internal/resilience/circuit-breakers/ai_service/reset

# Switch to conservative configuration
curl -X POST http://localhost:8000/internal/resilience/config/apply-preset \
  -H "Content-Type: application/json" \
  -d '{"preset": "conservative"}'
```

**Resource Optimization:**
```bash
# Increase worker processes (if appropriate)
export WORKERS=4
supervisorctl restart uvicorn

# Optimize memory settings
export CACHE_MAX_SIZE=100MB
export WORKERS_PER_CORE=1
```

### API Errors (4xx/5xx)

#### Symptoms
- HTTP 4xx or 5xx errors
- Authentication failures
- Validation errors

#### Diagnostic Steps

**Step 1: Error Analysis**
```bash
# Check recent errors
curl -s http://localhost:8000/internal/monitoring/overview | jq '.system_health.error_rate'

# Get error details
curl -s http://localhost:8000/internal/monitoring/errors/recent | jq '.'

# Check application logs
docker logs backend_container | tail -50
```

**Step 2: Authentication Issues**
```bash
# Test API key authentication
curl -H "X-API-Key: $API_KEY" http://localhost:8000/v1/health

# Check API key configuration
curl -s http://localhost:8000/internal/monitoring/auth-status | jq '.'
```

**Step 3: Validation Errors**
```bash
# Test API endpoint with valid request
curl -X POST http://localhost:8000/v1/text/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "Sample text", "max_sentences": 3}'
```

#### Resolution Steps

**Authentication Fixes:**
```bash
# Verify API key setting
echo $API_KEY

# Update API key if needed
export API_KEY=your-new-api-key

# Test with correct header
curl -H "X-API-Key: $API_KEY" http://localhost:8000/v1/health
```

**Input Validation:**
```bash
# Check API documentation for correct format
curl http://localhost:8000/docs

# Test with minimal valid request
curl -X POST http://localhost:8000/v1/text/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "Short text"}'
```

## AI Service Issues

### AI Provider Errors

#### Symptoms
- AI service timeout errors
- "Model not available" errors
- Invalid API responses from AI provider

#### Diagnostic Steps

**Step 1: Check AI Service Configuration**
```bash
# Verify AI service configuration
curl -s http://localhost:8000/internal/monitoring/ai-service-status | jq '.'

# Check API key validity
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY"

# Review circuit breaker status for AI service
curl -s http://localhost:8000/internal/resilience/circuit-breakers/ai_service | jq '.'
```

**Step 2: Test AI Connectivity**
```bash
# Simple AI service test
curl -X POST http://localhost:8000/v1/text/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "This is a simple test text.", "max_sentences": 1}'

# Check AI service logs
grep -i "gemini\|ai\|model" backend/logs/app.log | tail -20
```

#### Resolution Steps

**API Key Issues:**
```bash
# Verify Gemini API key
export GEMINI_API_KEY=your-valid-api-key

# Test API key directly
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY"

# Restart application with new key
make restart
```

**Service Recovery:**
```bash
# Reset AI service circuit breaker
curl -X POST http://localhost:8000/internal/resilience/circuit-breakers/ai_service/reset

# Apply conservative configuration
curl -X POST http://localhost:8000/internal/resilience/config/apply-preset \
  -H "Content-Type: application/json" \
  -d '{"preset": "conservative"}'
```

### AI Response Quality Issues

#### Symptoms
- Inconsistent AI responses
- Response validation failures
- Poor quality outputs

#### Diagnostic Steps

**Step 1: Check Input Sanitization**
```bash
# Test input sanitization
curl -X POST http://localhost:8000/v1/text/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "Normal text for testing", "max_sentences": 2}'

# Check for prompt injection alerts
curl -s http://localhost:8000/internal/monitoring/security-alerts | jq '.'
```

**Step 2: Validate AI Configuration**
```bash
# Check AI service configuration
curl -s http://localhost:8000/internal/monitoring/ai-config | jq '.'

# Review recent AI operations
curl -s http://localhost:8000/internal/monitoring/ai-operations/recent | jq '.'
```

#### Resolution Steps

**Configuration Optimization:**
```bash
# Reset AI configuration to defaults
curl -X POST http://localhost:8000/internal/ai/reset-config

# Apply recommended settings
curl -X POST http://localhost:8000/internal/ai/apply-recommended-config
```

## Frontend Issues

### Streamlit App Not Loading

#### Symptoms
- Frontend not accessible
- "Application error" messages
- Connection timeouts to backend

#### Diagnostic Steps

**Step 1: Check Streamlit Service**
```bash
# Verify Streamlit is running
ps aux | grep streamlit
curl -f http://localhost:8501/

# Check Streamlit logs
docker logs frontend_container | tail -50
```

**Step 2: Check Backend Connectivity**
```bash
# Test backend connection from frontend container
docker exec frontend_container curl -f http://backend:8000/health

# Check API configuration
grep -r "API_BASE_URL" frontend/
```

#### Resolution Steps

**Service Recovery:**
```bash
# Restart Streamlit
docker-compose restart frontend

# Or manually
cd frontend && streamlit run app/app.py --server.port 8501
```

**Configuration Fix:**
```bash
# Update API base URL
export API_BASE_URL=http://localhost:8000

# Or in Docker Compose environment
export API_BASE_URL=http://backend:8000
```

### Frontend-Backend Communication Issues

#### Symptoms
- API calls failing from frontend
- Authentication errors in UI
- Timeout errors in Streamlit

#### Diagnostic Steps

**Step 1: Test API Connectivity**
```bash
# Test from host machine
curl -H "X-API-Key: $API_KEY" http://localhost:8000/v1/health

# Test from frontend container
docker exec frontend_container curl -H "X-API-Key: $API_KEY" http://backend:8000/v1/health
```

**Step 2: Check Network Configuration**
```bash
# Verify Docker network
docker network ls
docker network inspect fastapi-streamlit-llm-starter_default

# Check container connectivity
docker exec frontend_container ping backend
```

#### Resolution Steps

**Network Fix:**
```bash
# Recreate Docker network
docker-compose down
docker-compose up -d

# Or restart services
docker-compose restart backend frontend
```

## Performance Issues

### High Memory Usage

#### Symptoms
- Memory usage > 80%
- Out of memory errors
- System slowdown

#### Diagnostic Steps

**Step 1: Identify Memory Usage**
```bash
# Check overall memory usage
free -h
top -o %MEM

# Check application memory usage
ps aux --sort=-%mem | head -10

# Check container memory usage
docker stats --no-stream
```

**Step 2: Check Application Memory**
```bash
# Check cache memory usage
curl -s http://localhost:8000/internal/cache/memory-stats | jq '.'

# Check monitoring memory usage
curl -s http://localhost:8000/internal/monitoring/memory-usage | jq '.'

# Review memory alerts
curl -s http://localhost:8000/internal/monitoring/alerts | jq '.alerts[] | select(.message | contains("memory"))'
```

#### Resolution Steps

**Cache Optimization:**
```bash
# Clear cache if too large
curl -X POST http://localhost:8000/internal/cache/clear

# Reduce cache retention
curl -X POST http://localhost:8000/internal/cache/configure \
  -H "Content-Type: application/json" \
  -d '{"retention_hours": 1, "max_size_mb": 50}'
```

**Memory Management:**
```bash
# Force garbage collection
curl -X POST http://localhost:8000/internal/monitoring/gc

# Reduce monitoring retention
curl -X POST http://localhost:8000/internal/monitoring/configure \
  -H "Content-Type: application/json" \
  -d '{"retention_hours": 2}'
```

### High CPU Usage

#### Symptoms
- CPU usage > 90%
- Slow response times
- High load average

#### Diagnostic Steps

**Step 1: Identify CPU Usage**
```bash
# Check CPU usage
top -o %CPU
htop

# Check application CPU usage
ps aux --sort=-%cpu | head -10

# Monitor load average
uptime
```

**Step 2: Application Analysis**
```bash
# Check active requests
curl -s http://localhost:8000/internal/monitoring/active-requests | jq '.'

# Check for CPU-intensive operations
curl -s http://localhost:8000/internal/monitoring/performance | jq '.cpu_intensive_operations'
```

#### Resolution Steps

**Load Balancing:**
```bash
# Increase worker processes
export WORKERS=4
docker-compose restart backend

# Enable request throttling
curl -X POST http://localhost:8000/internal/monitoring/throttle \
  -H "Content-Type: application/json" \
  -d '{"max_concurrent": 10}'
```

## Security Issues

### Authentication Failures

#### Symptoms
- 401 Unauthorized errors
- API key validation failures
- Authentication bypassed unexpectedly

#### Diagnostic Steps

**Step 1: Verify Authentication Configuration**
```bash
# Test authentication
curl -H "X-API-Key: $API_KEY" http://localhost:8000/v1/health

# Check authentication status
curl -s http://localhost:8000/internal/monitoring/auth-status | jq '.'

# Review security alerts
curl -s http://localhost:8000/internal/monitoring/security-alerts | jq '.'
```

#### Resolution Steps

**API Key Reset:**
```bash
# Generate new API key
openssl rand -hex 32

# Update environment
export API_KEY=new-generated-key

# Restart application
make restart
```

### Security Alerts

#### Symptoms
- Prompt injection alerts
- Suspicious input patterns
- Security monitoring alerts

#### Diagnostic Steps

**Step 1: Review Security Events**
```bash
# Check security alerts
curl -s http://localhost:8000/internal/monitoring/security-alerts | jq '.'

# Review input sanitization logs
grep -i "sanitiz\|inject\|security" backend/logs/app.log | tail -20

# Check recent security events
curl -s http://localhost:8000/internal/security/recent-events | jq '.'
```

#### Resolution Steps

**Security Response:**
```bash
# Enable enhanced security mode
curl -X POST http://localhost:8000/internal/security/enable-enhanced-mode

# Block suspicious IPs (if identified)
curl -X POST http://localhost:8000/internal/security/block-ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "suspicious.ip.address"}'

# Reset security configurations
curl -X POST http://localhost:8000/internal/security/reset-config
```

## Recovery Procedures

### Service Recovery Checklist

**Immediate Actions (< 5 minutes):**
1. ✅ Check service health endpoints
2. ✅ Verify critical alerts
3. ✅ Test basic functionality
4. ✅ Check external dependencies

**Assessment Phase (< 10 minutes):**
1. ✅ Identify root cause
2. ✅ Assess impact scope
3. ✅ Determine recovery strategy
4. ✅ Estimate recovery time

**Recovery Phase (< 30 minutes):**
1. ✅ Apply immediate fixes
2. ✅ Monitor recovery progress
3. ✅ Verify service restoration
4. ✅ Document incident

### Emergency Recovery Commands

**Complete Service Reset:**
```bash
# Stop all services
docker-compose down

# Clear problematic data
docker volume prune -f

# Restart with fresh state
docker-compose up -d

# Verify recovery
curl http://localhost:8000/health
curl http://localhost:8501/
```

**Configuration Reset:**
```bash
# Reset to default configuration
curl -X POST http://localhost:8000/internal/resilience/config/reset

# Apply safe preset
curl -X POST http://localhost:8000/internal/resilience/config/apply-preset \
  -H "Content-Type: application/json" \
  -d '{"preset": "simple"}'

# Clear cache
curl -X POST http://localhost:8000/internal/cache/clear
```

## Escalation Procedures

### When to Escalate

**Immediate Escalation (Critical):**
- Complete service outage > 15 minutes
- Data loss or corruption
- Security breach indicators
- Cannot identify root cause

**Standard Escalation (Major):**
- Performance degradation > 1 hour
- Partial service unavailability
- Repeated issues with same component
- Resource exhaustion

### Escalation Information

**Include in Escalation:**
1. Issue summary and timeline
2. Diagnostic results
3. Attempted resolutions
4. Current service status
5. Business impact assessment

**Escalation Contacts:**
- Development Team: For application bugs
- Infrastructure Team: For deployment/infrastructure issues
- Security Team: For security-related incidents
- Business Team: For business impact assessment

## Related Documentation

- **[Monitoring Guide](./MONITORING.md)**: Operational monitoring procedures
- **[Performance Optimization](./PERFORMANCE_OPTIMIZATION.md)**: Performance tuning procedures
- **[Backup and Recovery](./BACKUP_RECOVERY.md)**: Data backup and recovery procedures
- **[Security Guide](../SECURITY.md)**: Security best practices and procedures
- **[Infrastructure Documentation](../infrastructure/)**: Technical service documentation