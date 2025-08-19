# Redis Environment Variables Guide

## Overview

The cache infrastructure has been simplified through a **preset-based configuration system** that reduces 28+ environment variables to 1-4 variables. This guide explains the new preset approach alongside legacy variable usage patterns.

> **🚀 New in Phase 4**: The cache system now uses `CACHE_PRESET` for simplified configuration, following the successful pattern from the resilience system. This reduces configuration complexity by 96% (28+ variables → 1-4 variables).

## Quick Start (Preset-Based Configuration)

### Simple Configuration (Recommended)
```bash
# NEW WAY: Preset-based (1-4 variables)
CACHE_PRESET=development                    # Choose your preset
CACHE_REDIS_URL=redis://localhost:6379     # Redis connection override
ENABLE_AI_CACHE=true                        # AI features toggle
```

### Available Presets
- **`disabled`**: Cache completely disabled, memory-only fallback
- **`minimal`**: Ultra-lightweight caching for resource-constrained environments
- **`simple`**: Basic cache configuration suitable for most use cases
- **`development`**: Fast-feedback configuration optimized for development speed
- **`production`**: High-performance configuration for production workloads
- **`ai-development`**: AI-optimized configuration for development with text processing
- **`ai-production`**: AI-optimized configuration for production with advanced text processing

### Before/After Comparison

**OLD WAY (28+ environment variables)**:
```bash
CACHE_REDIS_URL=redis://localhost:6379
CACHE_DEFAULT_TTL=1800  
CACHE_MEMORY_CACHE_SIZE=200
CACHE_COMPRESSION_THRESHOLD=2000
CACHE_COMPRESSION_LEVEL=4
CACHE_TEXT_HASH_THRESHOLD=1000
CACHE_HASH_ALGORITHM=sha256
CACHE_MAX_TEXT_LENGTH=50000
CACHE_ENABLE_SMART_PROMOTION=true
CACHE_OPERATION_TTLS={"summarize": 3600, "sentiment": 1800}
CACHE_TEXT_SIZE_TIERS={"small": 1000, "medium": 5000}
CACHE_USE_TLS=false
CACHE_MAX_CONNECTIONS=50
CACHE_CONNECTION_TIMEOUT=5
CACHE_SOCKET_TIMEOUT=5
CACHE_MAX_BATCH_SIZE=100
CACHE_ENABLE_MONITORING=true
CACHE_LOG_LEVEL=INFO
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
ENABLE_AI_CACHE=true
# ... plus 6+ more security variables
```

**NEW WAY (1-4 environment variables)**:
```bash
CACHE_PRESET=development                    # Replaces most CACHE_* variables
CACHE_REDIS_URL=redis://localhost:6379     # Essential override
ENABLE_AI_CACHE=true                        # Feature toggle
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 500}'  # Advanced overrides (optional)
```

**Result**: 96% reduction in configuration complexity!

## Preset Override Patterns

### Common Override Scenarios

#### Scenario 1: Different Redis for Cache vs General App
```bash
# General app Redis (rate limiting, sessions)
REDIS_URL=redis://general-redis:6379

# High-performance cache Redis  
CACHE_PRESET=production
CACHE_REDIS_URL=redis://cache-redis:6379
ENABLE_AI_CACHE=true
```

#### Scenario 2: Development with Custom Settings
```bash
# Development preset with custom memory size
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 200, "default_ttl": 900}'
```

#### Scenario 3: Production with Security
```bash
# Production with TLS and authentication
CACHE_PRESET=production
CACHE_REDIS_URL=rediss://secure-cache:6380
CACHE_CUSTOM_CONFIG='{"use_tls": true, "redis_password": "secure_pass"}'
```

### Override Precedence
The preset system follows this precedence order:
1. **`CACHE_CUSTOM_CONFIG`** - JSON overrides (highest priority)
2. **Essential environment variables** - `CACHE_REDIS_URL`, `ENABLE_AI_CACHE`
3. **Preset defaults** - Configuration from chosen preset

### Management Commands
```bash
# List all available presets
make list-cache-presets

# Show detailed preset configuration
make show-cache-preset PRESET=production

# Validate current configuration
make validate-cache-config

# Get preset recommendations
make recommend-cache-preset ENV=staging

# Migrate from legacy configuration
make migrate-cache-config
```

## Legacy Environment Variables (Phase 3 and Earlier)

### 1. `REDIS_URL` (General Application Redis)
- **Purpose**: General Redis connection for non-cache application features
- **Used by**: Rate limiting middleware, health monitoring, legacy cache fallback
- **Default**: `redis://localhost:6379`
- **Database**: Database 0 (default)

### 2. `CACHE_REDIS_URL` (Phase 3 - Cache Infrastructure)
- **Purpose**: Phase 3 cache infrastructure Redis connection
- **Used by**: `CacheFactory`, `CacheConfig`, Phase 3 dependencies
- **Default**: Falls back to `REDIS_URL` if not set
- **Database**: Database 0 (default) or as specified

### 3. `AI_CACHE_REDIS_URL` (Phase 2 - AI-Specific Cache)
- **Purpose**: AI-specific cache configurations (legacy from Phase 2)
- **Used by**: `AIResponseCacheConfig` environment loading
- **Default**: Falls back to general Redis URL
- **Database**: Database 0 (default) or as specified

### 4. `TEST_REDIS_URL` (Testing)
- **Purpose**: Testing Redis connection (isolated database)
- **Used by**: Test suites, factory testing methods
- **Default**: `redis://localhost:6379/15`
- **Database**: Database 15 (test isolation)

## When to Use Different URLs

### Development Environment
```bash
# Single Redis instance for all purposes
REDIS_URL=redis://localhost:6379
CACHE_REDIS_URL=redis://localhost:6379     # Same as REDIS_URL
# AI_CACHE_REDIS_URL not needed (uses CACHE_REDIS_URL)
TEST_REDIS_URL=redis://localhost:6379/15   # Isolated test database
```

### Production Environment - Scenario 1: Single Redis Instance
```bash
# Single high-performance Redis for everything
REDIS_URL=redis://redis-cluster:6379
CACHE_REDIS_URL=redis://redis-cluster:6379
# AI_CACHE_REDIS_URL not needed (uses CACHE_REDIS_URL)
TEST_REDIS_URL=redis://test-redis:6379/15  # Separate test instance
```

### Production Environment - Scenario 2: Dedicated Cache Redis
```bash
# General Redis for resilience/monitoring
REDIS_URL=redis://general-redis:6379

# Dedicated high-performance Redis for caching
CACHE_REDIS_URL=redis://cache-redis:6379

# Optional: AI-specific Redis with specialized configuration
# AI_CACHE_REDIS_URL=redis://ai-cache-redis:6379

# Test Redis
TEST_REDIS_URL=redis://test-redis:6379/15
```

### Production Environment - Scenario 3: Database Separation
```bash
# Same Redis instance, different databases
REDIS_URL=redis://redis-cluster:6379/0         # General (DB 0)
CACHE_REDIS_URL=redis://redis-cluster:6379/1   # Cache (DB 1)
AI_CACHE_REDIS_URL=redis://redis-cluster:6379/2 # AI Cache (DB 2)
TEST_REDIS_URL=redis://redis-cluster:6379/15   # Tests (DB 15)
```

## Configuration Priority and Fallback

The Phase 3 cache infrastructure follows this precedence:

1. **`CACHE_REDIS_URL`** - Highest priority for cache operations
2. **`REDIS_URL`** - Fallback if `CACHE_REDIS_URL` not set
3. **Memory cache** - Final fallback if no Redis available

For AI-specific features:
1. **`AI_CACHE_REDIS_URL`** - AI-specific Redis (if configured)
2. **`CACHE_REDIS_URL`** - General cache Redis
3. **`REDIS_URL`** - Legacy general Redis
4. **Memory cache** - Final fallback

## Recommended Consolidation Strategy

### Option 1: Simplified (Recommended for most cases)
```bash
# Use CACHE_REDIS_URL as the primary cache Redis variable
CACHE_REDIS_URL=redis://your-redis:6379
# Remove AI_CACHE_REDIS_URL (uses CACHE_REDIS_URL)
# Keep REDIS_URL for legacy/resilience components
REDIS_URL=redis://your-redis:6379
TEST_REDIS_URL=redis://your-redis:6379/15
```

### Option 2: Dedicated Infrastructure (High-performance applications)
```bash
# Separate Redis instances for different purposes
REDIS_URL=redis://general-redis:6379          # General app infrastructure
CACHE_REDIS_URL=redis://cache-redis:6379      # High-performance caching
TEST_REDIS_URL=redis://test-redis:6379/15     # Testing
```

## Migration Guide

### Step 1: Audit Current Usage
```bash
# Check which variables are currently used
grep -r "REDIS_URL\|CACHE_REDIS_URL\|AI_CACHE_REDIS_URL" backend/
```

### Step 2: Choose Strategy
- **Single Redis instance**: Use Option 1 (Simplified)
- **Multiple Redis instances**: Use Option 2 (Dedicated)

### Step 3: Update Environment Files
```bash
# Update .env files
cp .env.cache.template .env
# Edit .env with your chosen strategy
```

### Step 4: Validate Configuration
```bash
# Test cache connectivity
make test-backend-infra-cache
```

## Docker Compose Examples

### Development (Preset-Based)
```yaml
services:
  backend:
    environment:
      # NEW: Preset-based approach
      - CACHE_PRESET=${CACHE_PRESET:-development}
      - CACHE_REDIS_URL=redis://redis:6379
      - ENABLE_AI_CACHE=${ENABLE_AI_CACHE:-true}
      
      # Legacy variables still supported
      - REDIS_URL=redis://redis:6379
      - TEST_REDIS_URL=redis://redis:6379/15
```

### Production (Dedicated Cache Redis with Presets)
```yaml
services:
  backend:
    environment:
      # NEW: Production preset with dedicated cache Redis
      - CACHE_PRESET=${CACHE_PRESET:-production}
      - CACHE_REDIS_URL=redis://cache-redis:6379
      - ENABLE_AI_CACHE=${ENABLE_AI_CACHE:-true}
      
      # Legacy/general Redis
      - REDIS_URL=redis://general-redis:6379
      - TEST_REDIS_URL=redis://test-redis:6379/15
  
  cache-redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
  
  general-redis:
    image: redis:7-alpine

### AI-Optimized Production
```yaml
services:
  backend:
    environment:
      # AI-specific production preset
      - CACHE_PRESET=ai-production
      - CACHE_REDIS_URL=redis://ai-cache-redis:6379
      - ENABLE_AI_CACHE=true
      
      # Custom overrides for AI workloads
      - CACHE_CUSTOM_CONFIG={"max_connections": 50, "compression_level": 9}
  
  ai-cache-redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru --save ""
```

## Best Practices

### 1. Environment-Specific Configuration
- **Development**: Single Redis instance with database separation
- **Staging**: Single Redis instance mimicking production
- **Production**: Dedicated Redis instances for performance

### 2. Security Considerations
```bash
# Use TLS in production
CACHE_REDIS_URL=rediss://secure-redis:6380
CACHE_USE_TLS=true
CACHE_USERNAME=cache_user
CACHE_PASSWORD=secure_password
```

### 3. Performance Optimization
```bash
# Cache-specific Redis with optimized settings
CACHE_REDIS_URL=redis://cache-redis:6379
CACHE_MAX_CONNECTIONS=100
CACHE_CONNECTION_TIMEOUT=5
```

### 4. Monitoring and Debugging
```bash
# Enable cache-specific logging
CACHE_LOG_LEVEL=DEBUG
CACHE_ENABLE_MONITORING=true
```

## Troubleshooting

### Issue: "Multiple Redis URLs configured"
**Solution**: Choose one primary strategy and remove redundant variables.

### Issue: "Cache connecting to wrong Redis"
**Solution**: Check `CACHE_REDIS_URL` takes precedence over `REDIS_URL`.

### Issue: "AI cache not using dedicated Redis"
**Solution**: Ensure `AI_CACHE_REDIS_URL` is set if you want AI-specific Redis.

### Issue: "Tests interfering with development data"
**Solution**: Ensure `TEST_REDIS_URL` uses database 15 or separate instance.

## Environment Variable Reference

| Variable | Purpose | Default | Database | Phase |
|----------|---------|---------|----------|-------|
| `REDIS_URL` | General Redis | `redis://localhost:6379` | 0 | Legacy |
| `CACHE_REDIS_URL` | Cache infrastructure | Falls back to `REDIS_URL` | 0 | Phase 3 |
| `AI_CACHE_REDIS_URL` | AI-specific cache | Falls back to cache Redis | 0 | Phase 2 |
| `TEST_REDIS_URL` | Testing | `redis://localhost:6379/15` | 15 | All |

## Summary

- **For most applications**: Use `CACHE_REDIS_URL` as primary, keep `REDIS_URL` for legacy
- **For high-performance**: Use dedicated Redis instances with different URLs
- **For development**: Single Redis with database separation
- **For production**: Consider dedicated cache Redis for optimal performance