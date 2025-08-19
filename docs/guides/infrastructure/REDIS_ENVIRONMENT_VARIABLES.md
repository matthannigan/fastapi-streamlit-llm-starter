# Redis Environment Variables Guide

## Overview

The cache infrastructure currently uses multiple Redis-related environment variables that serve different purposes. This guide clarifies the differences, usage patterns, and consolidation strategy.

## Current Environment Variables

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

### Development (Single Redis)
```yaml
services:
  backend:
    environment:
      - REDIS_URL=redis://redis:6379
      - CACHE_REDIS_URL=redis://redis:6379
      - TEST_REDIS_URL=redis://redis:6379/15
```

### Production (Dedicated Cache Redis)
```yaml
services:
  backend:
    environment:
      - REDIS_URL=redis://general-redis:6379
      - CACHE_REDIS_URL=redis://cache-redis:6379
      - TEST_REDIS_URL=redis://test-redis:6379/15
  
  cache-redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
  
  general-redis:
    image: redis:7-alpine
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