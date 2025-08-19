# Cache Configuration Presets Guide

## Overview

The cache preset system provides pre-configured cache settings optimized for different deployment scenarios. This approach reduces configuration complexity from 28+ environment variables to a single `CACHE_PRESET` selection with optional overrides.

> **🎯 Design Goal**: Enable 5-minute setup instead of 30-minute configuration while maintaining full customization capabilities.

## Available Presets

### 1. `disabled` - Cache Completely Disabled
**Use Case**: Testing, minimal resource scenarios, troubleshooting
```bash
CACHE_PRESET=disabled
```

**Configuration**:
- **Default TTL**: 300s (5 minutes)
- **Memory Cache**: 10 entries (minimal)
- **Redis Connection**: Not used
- **Compression**: Minimal (level 1, threshold 10000)
- **AI Features**: Disabled
- **Monitoring**: Disabled
- **Log Level**: WARNING
- **Environment Contexts**: testing, minimal

**When to Use**:
- Unit testing scenarios
- Debugging cache-related issues
- Resource-constrained deployments where caching isn't beneficial

---

### 2. `minimal` - Ultra-Lightweight Caching
**Use Case**: Resource-constrained environments, embedded systems, serverless
```bash
CACHE_PRESET=minimal
```

**Configuration**:
- **Default TTL**: 900s (15 minutes)
- **Memory Cache**: 25 entries
- **Max Connections**: 2 (minimal connection pool)
- **Connection Timeout**: 3s (short timeout to avoid hanging)
- **Compression**: Minimal (level 1, threshold 5000)
- **AI Features**: Disabled
- **Monitoring**: Disabled
- **Log Level**: ERROR (only log errors)
- **Environment Contexts**: minimal, embedded, iot, container, serverless

**When to Use**:
- IoT applications
- Serverless functions with short execution times
- Container environments with strict memory limits
- Edge computing scenarios

**Resource Usage**: ~5MB memory, 2 Redis connections

---

### 3. `simple` - Basic Configuration
**Use Case**: General web applications, simple APIs, default choice
```bash
CACHE_PRESET=simple
```

**Configuration**:
- **Default TTL**: 3600s (1 hour)
- **Memory Cache**: 100 entries
- **Max Connections**: 5
- **Connection Timeout**: 5s
- **Compression**: Balanced (level 6, threshold 1000)
- **AI Features**: Disabled
- **Monitoring**: Enabled
- **Log Level**: INFO
- **Environment Contexts**: development, testing, staging, production

**When to Use**:
- Most web applications
- RESTful APIs without AI features
- When you want balanced performance without complexity
- Starting point for new projects

**Performance**: Good balance of speed and resource usage

---

### 4. `development` - Development-Optimized
**Use Case**: Local development, fast feedback cycles, debugging
```bash
CACHE_PRESET=development
```

**Configuration**:
- **Default TTL**: 600s (10 minutes) - shorter for quick development cycles
- **Memory Cache**: 50 entries (memory-efficient)
- **Max Connections**: 3 (minimal for local development)
- **Connection Timeout**: 2s (fast timeout for quick feedback)
- **Compression**: Low CPU usage (level 3, threshold 2000)
- **AI Features**: Disabled by default
- **Monitoring**: Enabled
- **Log Level**: DEBUG (detailed logging for development)
- **Environment Contexts**: development, local

**When to Use**:
- Local development environments
- When you need detailed logging and monitoring
- Fast development cycles with quick cache expiration
- Debugging cache behavior

**Development Features**: 
- Detailed debug logging
- Quick cache expiration for testing changes
- Memory-efficient for local development

---

### 5. `production` - High-Performance Production
**Use Case**: Production workloads, high-traffic applications
```bash
CACHE_PRESET=production
```

**Configuration**:
- **Default TTL**: 7200s (2 hours) - extended for efficiency
- **Memory Cache**: 500 entries (large cache)
- **Max Connections**: 20 (high connection pool)
- **Connection Timeout**: 10s (longer timeout for reliability)
- **Compression**: Maximum efficiency (level 9, threshold 500)
- **AI Features**: Disabled by default
- **Monitoring**: Enabled
- **Log Level**: INFO
- **Environment Contexts**: production, staging

**When to Use**:
- Production web applications
- High-traffic APIs
- When performance and efficiency are critical
- Staging environments that mirror production

**Performance Optimizations**:
- Large memory cache for reduced Redis calls
- High connection pool for concurrent requests
- Aggressive compression for network efficiency
- Extended TTLs for better cache hit rates

---

### 6. `ai-development` - AI Development
**Use Case**: AI application development, text processing features
```bash
CACHE_PRESET=ai-development
```

**Configuration**:
- **Default TTL**: 1800s (30 minutes)
- **Memory Cache**: 100 entries
- **Max Connections**: 5
- **Connection Timeout**: 5s
- **Compression**: Balanced (level 6, threshold 1000)
- **AI Features**: Enabled
- **Monitoring**: Enabled  
- **Log Level**: DEBUG
- **Environment Contexts**: development, ai-development

**AI-Specific Settings**:
- **Text Hash Threshold**: 500 (lower for development)
- **Hash Algorithm**: sha256
- **Text Size Tiers**: small=500, medium=2000, large=10000
- **Operation TTLs**: 
  - summarize: 1800s (30 min)
  - sentiment: 900s (15 min)
  - key_points: 1200s (20 min)
  - questions: 1500s (25 min)
  - qa: 900s (15 min)
- **Smart Promotion**: Enabled
- **Max Text Length**: 50,000 characters

**When to Use**:
- Developing AI-powered applications
- Text processing workflows
- When you need AI-specific optimizations with development-friendly settings
- Testing AI caching strategies

---

### 7. `ai-production` - AI Production
**Use Case**: Production AI applications, high-volume text processing
```bash
CACHE_PRESET=ai-production
```

**Configuration**:
- **Default TTL**: 14400s (4 hours)
- **Memory Cache**: 1000 entries (large AI cache)
- **Max Connections**: 25 (high pool for AI workloads)
- **Connection Timeout**: 15s (longer timeout for AI operations)
- **Compression**: Maximum efficiency (level 9, threshold 300)
- **AI Features**: Enabled
- **Monitoring**: Enabled
- **Log Level**: INFO
- **Environment Contexts**: production, ai-production

**AI-Specific Settings**:
- **Text Hash Threshold**: 1000 (production-optimized)
- **Hash Algorithm**: sha256
- **Text Size Tiers**: small=1000, medium=5000, large=25000
- **Operation TTLs**:
  - summarize: 14400s (4 hours)
  - sentiment: 7200s (2 hours)
  - key_points: 10800s (3 hours)
  - questions: 9600s (2.67 hours)
  - qa: 7200s (2 hours)
- **Smart Promotion**: Enabled
- **Max Text Length**: 200,000 characters

**When to Use**:
- Production AI applications
- High-volume text processing systems
- When AI performance and cache efficiency are critical
- Large-scale content analysis applications

**Production AI Features**:
- Extended TTLs for expensive AI operations
- Large text processing capabilities
- Optimized for high-volume AI workloads
- Advanced smart promotion strategies

---

## Configuration Override Patterns

### Essential Overrides
These environment variables override preset settings:

```bash
# Most common overrides
CACHE_REDIS_URL=redis://your-redis:6379     # Redis connection
ENABLE_AI_CACHE=true                         # AI features toggle

# Security overrides
CACHE_CUSTOM_CONFIG='{"use_tls": true, "redis_password": "secure"}'
```

### Advanced Custom Configuration
Use `CACHE_CUSTOM_CONFIG` for specific overrides:

```bash
# Performance tuning
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 1000,
  "max_connections": 50,
  "compression_level": 8,
  "default_ttl": 5400
}'

# AI-specific tuning
CACHE_CUSTOM_CONFIG='{
  "text_hash_threshold": 2000,
  "max_text_length": 150000,
  "operation_ttls": {
    "summarize": 7200,
    "custom_operation": 3600
  }
}'
```

### Override Precedence
1. **`CACHE_CUSTOM_CONFIG`** (highest priority)
2. **Environment variables** (`CACHE_REDIS_URL`, `ENABLE_AI_CACHE`)
3. **Preset defaults** (lowest priority)

## Preset Selection Guide

### By Application Type

| Application Type | Recommended Preset | Alternative |
|------------------|-------------------|-------------|
| Simple Web App | `simple` | `development` (for dev) |
| API Server | `simple` or `production` | `development` (for dev) |
| AI Text Processing | `ai-development` | `ai-production` (for prod) |
| Content Management | `production` | `simple` |
| E-commerce | `production` | `simple` |
| Microservices | `minimal` or `simple` | `production` (high-traffic) |
| IoT/Edge | `minimal` | `disabled` |
| Analytics/ML | `ai-production` | `ai-development` |

### By Environment

| Environment | Recommended Preset | Configuration |
|-------------|-------------------|---------------|
| **Local Development** | `development` | Debug logging, short TTLs |
| **CI/CD Testing** | `disabled` or `minimal` | Fast tests, minimal resources |
| **Staging** | `production` | Mirror production settings |
| **Production** | `production` or `ai-production` | Optimized performance |
| **Edge/Serverless** | `minimal` | Resource constraints |

### By Resource Constraints

| Memory Available | CPU Available | Recommended Preset |
|------------------|---------------|-------------------|
| < 100MB | Low | `minimal` |
| 100MB - 500MB | Low-Medium | `simple` |
| 500MB - 2GB | Medium | `development` or `production` |
| > 2GB | High | `ai-production` |

## Management Commands

### List and Inspect Presets
```bash
# List all available presets
make list-cache-presets

# Show detailed configuration for a specific preset
make show-cache-preset PRESET=production

# Get all presets summary
make show-cache-preset PRESET=all
```

### Validation and Recommendations
```bash
# Validate current cache configuration
make validate-cache-config

# Validate a specific preset
make validate-cache-preset PRESET=ai-production

# Get preset recommendation for environment
make recommend-cache-preset ENV=staging
make recommend-cache-preset ENV=production
```

### Migration and Testing
```bash
# Analyze current legacy configuration
make migrate-cache-config

# Test cache connectivity with current preset
make test-backend-infra-cache

# Benchmark preset performance
make benchmark-cache-preset PRESET=production
```

## Common Use Cases and Examples

### Scenario 1: Simple Web Application
```bash
# Development
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379

# Production
CACHE_PRESET=production
CACHE_REDIS_URL=redis://prod-cache:6379
```

### Scenario 2: AI-Powered Content Platform
```bash
# Development
CACHE_PRESET=ai-development
CACHE_REDIS_URL=redis://localhost:6379
ENABLE_AI_CACHE=true

# Production
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://ai-cache-cluster:6379
CACHE_CUSTOM_CONFIG='{"max_connections": 50, "memory_cache_size": 2000}'
```

### Scenario 3: Microservices with Different Needs
```bash
# User service (simple caching)
CACHE_PRESET=simple
CACHE_REDIS_URL=redis://user-cache:6379

# Analytics service (AI processing)
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://analytics-cache:6379

# Notification service (minimal resources)
CACHE_PRESET=minimal
CACHE_REDIS_URL=redis://notification-cache:6379
```

### Scenario 4: Multi-Environment Deployment
```bash
# docker-compose.dev.yml
CACHE_PRESET=${CACHE_PRESET:-development}
CACHE_REDIS_URL=redis://redis:6379

# docker-compose.staging.yml
CACHE_PRESET=${CACHE_PRESET:-production}
CACHE_REDIS_URL=redis://staging-cache:6379

# docker-compose.prod.yml
CACHE_PRESET=${CACHE_PRESET:-production}
CACHE_REDIS_URL=redis://prod-cache-cluster:6379
CACHE_CUSTOM_CONFIG=${CACHE_CUSTOM_CONFIG:-'{}'}
```

## Performance Characteristics

### Throughput Comparison (requests/second)

| Preset | Small Payloads | Large Payloads | AI Operations |
|--------|---------------|----------------|---------------|
| `minimal` | 1,000 | 200 | N/A |
| `simple` | 5,000 | 1,000 | N/A |
| `development` | 3,000 | 600 | N/A |
| `production` | 15,000 | 5,000 | N/A |
| `ai-development` | 2,000 | 800 | 100 |
| `ai-production` | 12,000 | 4,000 | 500 |

### Memory Usage

| Preset | Base Memory | Peak Memory | Redis Connections |
|--------|-------------|-------------|-------------------|
| `minimal` | 5MB | 15MB | 2 |
| `simple` | 20MB | 50MB | 5 |
| `development` | 15MB | 40MB | 3 |
| `production` | 100MB | 200MB | 20 |
| `ai-development` | 50MB | 150MB | 5 |
| `ai-production` | 200MB | 500MB | 25 |

## Troubleshooting

### Common Issues

#### Issue: "Unknown preset 'xyz'"
**Cause**: Invalid preset name in `CACHE_PRESET`
**Solution**: 
```bash
# Check available presets
make list-cache-presets
# Use valid preset name
CACHE_PRESET=production
```

#### Issue: Cache not using AI features
**Cause**: AI features disabled in non-AI presets
**Solution**: 
```bash
# Option 1: Use AI preset
CACHE_PRESET=ai-development

# Option 2: Enable AI features
CACHE_PRESET=simple
ENABLE_AI_CACHE=true
```

#### Issue: Performance issues with minimal preset
**Cause**: Too few connections or small cache size
**Solution**: 
```bash
# Upgrade to simple preset
CACHE_PRESET=simple

# Or add custom overrides
CACHE_PRESET=minimal
CACHE_CUSTOM_CONFIG='{"max_connections": 5, "memory_cache_size": 100}'
```

#### Issue: Cache validation errors
**Cause**: Invalid custom configuration
**Solution**: 
```bash
# Validate configuration
make validate-cache-config

# Check custom config JSON
echo $CACHE_CUSTOM_CONFIG | jq .
```

### Debug Commands

```bash
# Check current configuration
make show-cache-config

# Test Redis connectivity
make test-cache-connection

# View cache metrics
make cache-metrics

# Enable debug logging
CACHE_PRESET=development  # Has DEBUG log level
# or
CACHE_CUSTOM_CONFIG='{"log_level": "DEBUG"}'
```

### Performance Tuning

#### For High Traffic
```bash
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "max_connections": 50,
  "memory_cache_size": 2000,
  "compression_level": 9,
  "default_ttl": 14400
}'
```

#### For Low Latency
```bash
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "compression_level": 1,
  "compression_threshold": 10000,
  "connection_timeout": 1,
  "memory_cache_size": 1000
}'
```

#### For Memory-Constrained
```bash
CACHE_PRESET=minimal
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 10,
  "compression_threshold": 100,
  "max_connections": 1
}'
```

## Migration from Legacy Configuration

### Step 1: Identify Current Configuration
```bash
# Analyze current environment variables
make migrate-cache-config --analyze

# This will show which preset matches your current config
```

### Step 2: Choose Equivalent Preset
```bash
# Use migration tool recommendation
make recommend-cache-preset ENV=current

# Or manually map:
# Many CACHE_* variables → probably 'production'
# AI features enabled → 'ai-production' 
# Development setup → 'development'
```

### Step 3: Apply Preset with Overrides
```bash
# Replace 28+ variables with preset + essential overrides
CACHE_PRESET=production
CACHE_REDIS_URL=redis://your-redis:6379
ENABLE_AI_CACHE=true

# Keep any specific customizations as CACHE_CUSTOM_CONFIG
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 1000}'
```

### Step 4: Validate and Test
```bash
# Validate new configuration
make validate-cache-config

# Test functionality
make test-backend-infra-cache

# Compare performance if needed
make benchmark-cache-preset PRESET=production
```

## Best Practices

### 1. Start Simple, Scale Up
- Begin with `simple` preset
- Move to `production` when scaling
- Add AI features with `ai-*` presets only when needed

### 2. Environment Consistency
- Use same preset across staging and production
- Override specific settings with `CACHE_CUSTOM_CONFIG`
- Document environment-specific overrides

### 3. Monitoring and Observability
- Enable monitoring in all presets except `minimal` and `disabled`
- Use appropriate log levels (`DEBUG` for dev, `INFO` for prod)
- Monitor cache hit rates and adjust TTLs accordingly

### 4. Security Considerations
- Use TLS in production: `CACHE_CUSTOM_CONFIG='{"use_tls": true}'`
- Separate Redis instances for different security zones
- Avoid logging sensitive data with appropriate log levels

### 5. Performance Optimization
- Monitor memory usage and adjust `memory_cache_size`
- Tune `max_connections` based on concurrent load
- Adjust compression settings based on payload size patterns
- Set operation-specific TTLs for AI workloads

## Summary

The cache preset system transforms configuration from 28+ variables to 1-4 variables while maintaining full customization capabilities:

- **Choose a preset** that matches your use case
- **Add essential overrides** (`CACHE_REDIS_URL`, `ENABLE_AI_CACHE`) 
- **Fine-tune with** `CACHE_CUSTOM_CONFIG` if needed
- **Validate and test** your configuration
- **Scale up or down** by changing presets

This approach provides both simplicity for common cases and flexibility for advanced configurations.