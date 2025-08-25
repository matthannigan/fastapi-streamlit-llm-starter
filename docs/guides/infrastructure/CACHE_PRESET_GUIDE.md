# Cache Preset Configuration Guide

This guide explains the cache preset system that simplifies cache configuration from 28+ individual environment variables to a single `CACHE_PRESET` variable with optional overrides.

## Overview

The cache preset system provides pre-configured cache settings optimized for different deployment scenarios. Instead of manually configuring dozens of environment variables, you choose a preset that matches your use case and optionally override specific settings.

## Quick Start

```bash
# Choose your preset (this is all you need for basic setup)
CACHE_PRESET=development     # For local development
CACHE_PRESET=production      # For web applications
CACHE_PRESET=ai-production   # For AI-powered applications

# Optional overrides (only when needed)
CACHE_REDIS_URL=redis://localhost:6379  # Custom Redis URL
ENABLE_AI_CACHE=true                     # Toggle AI features
```

## Available Presets

### `disabled` - Testing & Minimal Overhead
**Use Case:** Unit tests, minimal deployments, troubleshooting

**Key Settings:**
- Cache completely disabled, memory-only fallback
- TTL: 5 minutes (300s) for minimal memory usage  
- Compression: Minimal (threshold 10KB, level 1)
- Monitoring: Disabled for maximum performance
- AI features: Disabled

**When to Use:**
- Running unit tests that don't need caching
- Debugging cache-related issues
- Extremely resource-constrained environments
- Temporary troubleshooting scenarios

```bash
CACHE_PRESET=disabled
```

### `minimal` - Resource-Constrained Environments
**Use Case:** Small deployments, microservices, edge computing

**Key Settings:**
- TTL: 15 minutes (900s) for lightweight caching
- Memory cache: 10 entries maximum
- Compression: Conservative (threshold 5KB, level 3)
- Monitoring: Basic logging only
- AI features: Disabled for simplicity

**When to Use:**
- Docker containers with memory constraints
- Edge deployments
- Simple web applications
- Development environments with limited resources

```bash
CACHE_PRESET=minimal
```

### `simple` - Quick Setup for Small Applications
**Use Case:** Personal projects, prototypes, small web applications

**Key Settings:**
- TTL: 1 hour (3600s) for general web caching
- Memory cache: 100 entries
- Compression: Balanced (threshold 2KB, level 6)
- Monitoring: Basic performance tracking
- AI features: Disabled by default

**When to Use:**
- Getting started with the template quickly
- Non-AI web applications
- Prototyping and proof-of-concepts
- Small-scale deployments

```bash
CACHE_PRESET=simple
```

### `development` - Local Development
**Use Case:** Local development, debugging, experimentation

**Key Settings:**
- TTL: 30 minutes (1800s) for fast iteration
- Memory cache: 100 entries for development testing
- Compression: Moderate (threshold 1KB, level 6)
- Monitoring: Full monitoring with DEBUG logging
- AI features: Enabled for full feature testing

**When to Use:**
- Local development environment
- Testing cache functionality
- Debugging cache behavior
- Feature development and testing

```bash
CACHE_PRESET=development
# Optional development overrides
CACHE_REDIS_URL=redis://localhost:6379
ENABLE_AI_CACHE=true
```

### `production` - High-Performance Web Applications
**Use Case:** Production web applications, APIs, general workloads

**Key Settings:**
- TTL: 2 hours (7200s) for production efficiency
- Memory cache: 500 entries for high performance
- Compression: Optimized (threshold 1KB, level 6)
- Monitoring: Production monitoring with INFO logging
- AI features: Disabled (use `ai-production` for AI workloads)
- Connection pool: 20 connections for high concurrency

**When to Use:**
- Production web applications
- REST APIs without AI features
- High-traffic websites
- Standard production deployments

```bash
CACHE_PRESET=production
CACHE_REDIS_URL=redis://production-redis:6379
```

### `ai-development` - AI Application Development
**Use Case:** Developing AI-powered applications locally

**Key Settings:**
- TTL: 30 minutes (1800s) for development iteration
- Memory cache: 200 entries for AI data
- Text processing: Optimized for AI workloads
- Operation-specific TTLs: Shorter for development
  - Summarize: 30 minutes
  - Sentiment: 15 minutes
  - Q&A: 15 minutes
- Monitoring: Full monitoring with AI-specific metrics
- AI features: Fully enabled with development-friendly settings

**When to Use:**
- Developing AI-powered applications
- Testing AI text processing features
- Local AI experimentation
- AI feature debugging

```bash
CACHE_PRESET=ai-development
GEMINI_API_KEY=your-development-api-key
```

### `ai-production` - Production AI Workloads
**Use Case:** Production AI applications with high performance requirements

**Key Settings:**
- TTL: 4 hours (14400s) for AI efficiency
- Memory cache: 1000 entries for large AI datasets
- Text processing: Maximum AI optimization
- Operation-specific TTLs: Production-optimized
  - Summarize: 4 hours (stable results)
  - Sentiment: 2 hours (rarely changes)
  - Q&A: 2 hours (context-dependent)
- Compression: Maximum (threshold 300B, level 9)
- Connection pool: 25 connections for AI workloads
- Monitoring: Production AI monitoring

**When to Use:**
- Production AI applications
- High-volume text processing
- AI-powered APIs
- Performance-critical AI workloads

```bash
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://production-ai-redis:6379
GEMINI_API_KEY=your-production-api-key
```

## Override Patterns

### Basic Overrides

```bash
# Use production preset with custom Redis
CACHE_PRESET=production
CACHE_REDIS_URL=redis://custom-server:6379

# Use AI preset without AI features (for testing)
CACHE_PRESET=ai-development
ENABLE_AI_CACHE=false
```

### Advanced JSON Overrides

Use `CACHE_CUSTOM_CONFIG` for complex customizations:

```bash
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 500,
  "memory_cache_size": 2000,
  "operation_ttls": {
    "summarize": 7200,
    "sentiment": 3600,
    "key_points": 5400
  },
  "text_size_tiers": {
    "small": 1000,
    "medium": 10000,
    "large": 100000
  }
}'
```

### Environment-Specific Overrides

**Development Environment:**
```bash
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379
ENABLE_AI_CACHE=true
CACHE_CUSTOM_CONFIG='{"default_ttl": 900}'  # 15 minutes for fast iteration
```

**Staging Environment:**
```bash
CACHE_PRESET=production
CACHE_REDIS_URL=redis://staging-redis:6379
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 200}'  # Moderate resources
```

**Production Environment:**
```bash
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://prod-ai-redis:6379
CACHE_CUSTOM_CONFIG='{"max_connections": 50}'  # High concurrency
```

## Preset Selection Guide

### Decision Tree

1. **Do you need AI features?**
   - Yes → Go to step 2
   - No → Go to step 3

2. **AI Applications:**
   - Development/Testing → `ai-development`
   - Production → `ai-production`

3. **Non-AI Applications:**
   - Testing/Debugging → `disabled`
   - Resource-constrained → `minimal`
   - Quick prototype → `simple`
   - Development → `development`
   - Production → `production`

### Use Case Matrix

| Use Case | Preset | Redis Required | AI Features | Performance |
|----------|--------|----------------|-------------|-------------|
| Unit Testing | `disabled` | No | No | Fastest |
| Edge Computing | `minimal` | Optional | No | Fast |
| Prototyping | `simple` | Optional | No | Fast |
| Local Dev | `development` | Recommended | Yes | Balanced |
| Web Production | `production` | Required | No | High |
| AI Development | `ai-development` | Recommended | Yes | Balanced |
| AI Production | `ai-production` | Required | Yes | Maximum |

## Configuration Validation

### Validate Your Preset

Use the built-in validation tools:

```bash
# List available presets
make list-cache-presets

# Show preset details
make show-cache-preset PRESET=production

# Validate current configuration
make validate-cache-config

# Get preset recommendation
make recommend-cache-preset ENV=production
```

### Common Validation Issues

**Missing Redis URL:**
```bash
# Problem: Redis required but not configured
CACHE_PRESET=production  # Requires Redis

# Solution: Add Redis URL
CACHE_PRESET=production
CACHE_REDIS_URL=redis://localhost:6379
```

**Invalid JSON Override:**
```bash
# Problem: Malformed JSON
CACHE_CUSTOM_CONFIG='{"invalid": json}'

# Solution: Validate JSON
CACHE_CUSTOM_CONFIG='{"compression_threshold": 1000}'
```

**Preset Not Found:**
```bash
# Problem: Typo in preset name
CACHE_PRESET=prodcution

# Solution: Use correct preset name
CACHE_PRESET=production
```

## Performance Characteristics

### Preset Performance Comparison

| Preset | Memory Usage | CPU Usage | Network I/O | Startup Time |
|--------|--------------|-----------|-------------|--------------|
| `disabled` | Minimal | Minimal | None | Instant |
| `minimal` | Low | Low | Low | Fast |
| `simple` | Low | Low | Moderate | Fast |
| `development` | Moderate | Moderate | Moderate | Moderate |
| `production` | High | Moderate | High | Moderate |
| `ai-development` | Moderate | High | High | Slow |
| `ai-production` | High | High | High | Slow |

### Performance Tuning

**High Traffic Applications:**
```bash
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "max_connections": 50,
  "connection_timeout": 10,
  "memory_cache_size": 2000
}'
```

**Memory-Constrained Environments:**
```bash
CACHE_PRESET=minimal
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 50,
  "compression_threshold": 100
}'
```

**AI Performance Optimization:**
```bash
CACHE_PRESET=ai-production
CACHE_CUSTOM_CONFIG='{
  "text_hash_threshold": 500,
  "compression_level": 9,
  "operation_ttls": {
    "summarize": 28800  // 8 hours for stable summaries
  }
}'
```

## Troubleshooting

### Common Issues

**Cache Not Working:**
1. Check preset name spelling
2. Verify Redis connection (if required)
3. Check logs for connection errors
4. Validate environment variables

**Poor Performance:**
1. Consider higher-performance preset
2. Check Redis connection latency
3. Optimize compression settings
4. Monitor memory usage

**AI Features Not Available:**
1. Ensure `ENABLE_AI_CACHE=true`
2. Use AI-specific presets (`ai-development`, `ai-production`)
3. Check AI model API keys
4. Verify text processing configuration

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
CACHE_PRESET=development
CACHE_CUSTOM_CONFIG='{"log_level": "DEBUG"}'
```

### Health Checks

Monitor cache health through API endpoints:

```bash
# Check cache health
curl http://localhost:8000/internal/cache/health

# Check cache configuration
curl http://localhost:8000/internal/cache/config
```

## Migration Guide

### From Individual Variables

**Old Approach (28+ variables):**
```bash
REDIS_URL=redis://localhost:6379
CACHE_DEFAULT_TTL=3600
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=6
CACHE_MEMORY_CACHE_SIZE=100
CACHE_TEXT_HASH_THRESHOLD=500
ENABLE_AI_CACHE=true
# ... 20+ more variables
```

**New Approach (1-3 variables):**
```bash
CACHE_PRESET=ai-development
CACHE_REDIS_URL=redis://localhost:6379  # Optional override
ENABLE_AI_CACHE=true                     # Optional override
```

### Migration Steps

1. **Identify Current Configuration**
   ```bash
   # Run migration analyzer
   python scripts/migrate_cache_config.py --analyze
   ```

2. **Get Preset Recommendation**
   ```bash
   # Get recommended preset
   python scripts/migrate_cache_config.py --recommend
   ```

3. **Apply Migration**
   ```bash
   # Apply recommended changes
   python scripts/migrate_cache_config.py --migrate
   ```

4. **Validate Migration**
   ```bash
   # Test new configuration
   make validate-cache-config
   ```

## Best Practices

### Environment Management

1. **Use Environment-Specific Presets**
   ```bash
   # Development
   CACHE_PRESET=development
   
   # Staging
   CACHE_PRESET=production
   
   # Production
   CACHE_PRESET=ai-production
   ```

2. **Override Only When Necessary**
   ```bash
   # Good: Minimal overrides
   CACHE_PRESET=production
   CACHE_REDIS_URL=redis://prod-redis:6379
   
   # Avoid: Too many overrides (use custom config instead)
   ```

3. **Use JSON for Complex Overrides**
   ```bash
   # For multiple overrides, use CACHE_CUSTOM_CONFIG
   CACHE_PRESET=production
   CACHE_CUSTOM_CONFIG='{"compression_level": 9, "memory_cache_size": 1000}'
   ```

### Security Considerations

1. **Use TLS in Production**
   ```bash
   CACHE_PRESET=production
   CACHE_REDIS_URL=rediss://secure-redis:6379  # Note: rediss:// for TLS
   ```

2. **Secure Redis Credentials**
   ```bash
   CACHE_REDIS_URL=redis://username:password@redis:6379
   ```

3. **Disable Debug in Production**
   - Production presets automatically use INFO level logging
   - Avoid DEBUG logging in production environments

### Monitoring and Observability

1. **Enable Monitoring**
   - All presets except `disabled` include monitoring
   - Use `/internal/cache/health` for health checks
   - Monitor cache hit ratios and performance metrics

2. **Set Up Alerts**
   - Monitor Redis connectivity
   - Track cache hit ratios
   - Alert on performance degradation

3. **Performance Baselines**
   - Establish baselines for each preset
   - Monitor for performance regressions
   - Optimize based on usage patterns

## Advanced Topics

### Custom Presets

While not recommended for most users, you can create custom presets by modifying the preset system. This requires code changes and is typically only needed for specialized deployment scenarios.

### Preset Inheritance

Some presets build on others:
- `ai-development` extends `development` with AI features
- `ai-production` extends `production` with AI optimizations

### Dynamic Preset Selection

For advanced use cases, you can dynamically select presets based on runtime conditions:

```python
import os
from app.infrastructure.cache.dependencies import get_cache_config

# Dynamic preset selection
if os.getenv("ENVIRONMENT") == "production":
    os.environ["CACHE_PRESET"] = "production"
else:
    os.environ["CACHE_PRESET"] = "development"

config = get_cache_config()
```

## Conclusion

The cache preset system dramatically simplifies cache configuration while providing the flexibility to customize settings when needed. Start with the appropriate preset for your use case, and only add overrides for specific requirements.

For most users:
- **Development**: Use `development` or `ai-development`
- **Production**: Use `production` or `ai-production`
- **Testing**: Use `minimal` or `disabled`

The preset system ensures optimal performance and reliability while reducing configuration complexity from 28+ variables to just a few essential settings.