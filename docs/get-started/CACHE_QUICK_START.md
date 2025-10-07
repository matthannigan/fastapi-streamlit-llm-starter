# Cache Quick Start Guide - 5 Minutes to Caching

Get up and running with the cache system in under 5 minutes using the new preset-based configuration.

## ⚡ Super Quick Start (30 seconds)

```bash
# 1. Choose your preset
export CACHE_PRESET=development

# 2. That's it! Your cache is configured.
make run-backend
```

Your application now has intelligent caching with zero manual configuration.

## 🚀 Choose Your Adventure (2 minutes)

### For Web Applications
```bash
export CACHE_PRESET=development    # Local development
export CACHE_PRESET=production     # Production web apps
```

### For AI Applications  
```bash
export CACHE_PRESET=ai-development   # AI app development
export CACHE_PRESET=ai-production    # Production AI apps
```

### For Testing/Minimal Usage
```bash
export CACHE_PRESET=disabled         # Testing without cache
export CACHE_PRESET=minimal          # Lightweight caching
```

## 🔒 Secure Redis Setup (Recommended - 1 minute)

**Security is mandatory and always enabled.** All Redis connections use TLS encryption.

```bash
# One-command secure Redis setup for development
./scripts/setup-secure-redis.sh

# This automatically:
# ✅ Generates TLS certificates (4096-bit RSA)
# ✅ Creates secure password
# ✅ Generates encryption key
# ✅ Starts TLS-enabled Redis container
# ✅ Creates .env.secure configuration

# Your cache is now secure by default
export CACHE_PRESET=development
# CACHE_REDIS_URL=rediss://localhost:6380 (auto-configured)
```

**Security Features:**
- 🔐 TLS 1.2+ encryption for all connections
- 🔑 Data encrypted at rest (Fernet/AES-128)
- 🛡️ Password authentication required
- 🌐 Docker network isolation

Without Redis, the cache automatically falls back to memory-only mode.

## ✅ Verify It's Working (1 minute)

### Option 1: Check Health Endpoint
```bash
curl http://localhost:8000/internal/cache/health
```

### Option 2: Run Example Application
```bash
python backend/examples/cache/preset_scenarios_simple_webapp.py
curl http://localhost:8081/cache/info
```

### Option 3: Quick Code Test
```python
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory

# Load your preset configuration
config = get_cache_config()
factory = CacheFactory()
cache = await factory.create_cache_from_config(config)

# Test caching
await cache.set("test", "it works!")
result = await cache.get("test")
print(f"Cache result: {result}")  # Should print: Cache result: it works!
```

## 🎯 Common Scenarios

### Local Development
```bash
export CACHE_PRESET=development
# Automatic: debug logging, 30min TTL, monitoring enabled
```

### Production Web App
```bash
export CACHE_PRESET=production
export CACHE_REDIS_URL=rediss://production-redis:6380
# Automatic: 2hr TTL, optimized performance, production logging
```

### AI Application Development
```bash
export CACHE_PRESET=ai-development
export GEMINI_API_KEY=your-api-key
# Automatic: AI text processing, shorter TTLs, AI-specific features
```

### AI Production Deployment
```bash
export CACHE_PRESET=ai-production
export CACHE_REDIS_URL=rediss://ai-redis:6380
export GEMINI_API_KEY=your-production-api-key
# Automatic: AI optimizations, 4hr TTL, maximum performance
```

### Resource-Constrained Environment
```bash
export CACHE_PRESET=minimal
# Automatic: minimal memory usage, basic caching, essential features only
```

## 🛠️ Advanced Configuration (When Needed)

### Override Specific Settings
```bash
export CACHE_PRESET=production
export CACHE_REDIS_URL=rediss://custom-redis:6380  # Custom Redis
export ENABLE_AI_CACHE=false                      # Disable AI features
```

### JSON Override for Complex Scenarios
```bash
export CACHE_PRESET=production
export CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 500,
  "memory_cache_size": 1000,
  "default_ttl": 7200
}'
```

## 📊 Monitor Your Cache

### Built-in Monitoring
```bash
# Health status
curl http://localhost:8000/internal/cache/health

# Configuration details
curl http://localhost:8000/internal/cache/config

# Performance metrics (if monitoring enabled)
curl http://localhost:8000/internal/cache/metrics
```

### Command Line Tools
```bash
# List all available presets
make list-cache-presets

# Show details for a specific preset
make show-cache-preset PRESET=production

# Validate current configuration
make validate-cache-config

# Get preset recommendation for your environment
make recommend-cache-preset ENV=production
```

## 🆚 Configuration Comparison

### Traditional Approach (Individual Variables)
```bash
# 28+ environment variables to configure
export CACHE_DEFAULT_TTL=3600
export CACHE_MEMORY_CACHE_SIZE=200
export CACHE_COMPRESSION_THRESHOLD=2000
export CACHE_COMPRESSION_LEVEL=6
export CACHE_TEXT_HASH_THRESHOLD=1000
export CACHE_OPERATION_TTLS='{"summarize": 7200, "sentiment": 1800}'
export CACHE_USE_TLS=false
export CACHE_MAX_CONNECTIONS=20
export CACHE_CONNECTION_TIMEOUT=10
export CACHE_ENABLE_MONITORING=true
export CACHE_LOG_LEVEL=DEBUG
# ... 17+ more variables
```

### Preset System (Recommended)
```bash
# 1-3 environment variables
export CACHE_PRESET=development
export CACHE_REDIS_URL=rediss://localhost:6380  # Optional override
export ENABLE_AI_CACHE=true                     # Optional toggle
```

**Result**: 90%+ reduction in configuration complexity with better defaults and easier maintenance.

## 🔍 Troubleshooting

### Cache Not Working
**Problem**: No cache hits, everything seems to miss cache  
**Solution**: 
```bash
# Check if preset is valid
make validate-cache-config

# Verify preset is loaded
curl http://localhost:8000/internal/cache/config
```

### Redis Connection Issues
**Problem**: Cache works but Redis errors in logs  
**Solution**:
```bash
# Verify Redis URL
echo $CACHE_REDIS_URL

# Test Redis connectivity
redis-cli -u $CACHE_REDIS_URL ping

# Or use memory-only mode (remove CACHE_REDIS_URL)
unset CACHE_REDIS_URL
```

### Performance Issues
**Problem**: Cache is slow or using too much memory  
**Solution**:
```bash
# Try a different preset
export CACHE_PRESET=minimal  # For resource constraints
export CACHE_PRESET=production  # For high performance

# Or tune specific settings
export CACHE_CUSTOM_CONFIG='{"memory_cache_size": 100}'
```

### AI Features Not Working
**Problem**: AI caching not available  
**Solution**:
```bash
# Use AI-specific preset
export CACHE_PRESET=ai-development

# Or explicitly enable AI features
export ENABLE_AI_CACHE=true

# Verify AI model API keys are set
echo $GEMINI_API_KEY
```

## 📚 What's Next?

### Learn More
- **[Configuration Guide](../guides/infrastructure/cache/configuration.md)**: Detailed preset documentation and configuration management
- **[Cache Usage Guide](../guides/infrastructure/cache/usage-guide.md)**: Advanced usage patterns and practical examples
- **[Cache Infrastructure README](../../backend/app/infrastructure/cache/README.md)**: Technical details

### Try Examples
- **Simple Web App**: `python backend/examples/cache/preset_scenarios_simple_webapp.py`
- **AI Application**: `python backend/examples/cache/preset_scenarios_ai_application.py`
- **Production Demo**: `python backend/examples/cache/preset_scenarios_production_highperf.py`

### Integration
- **FastAPI Integration**: See `backend/examples/cache/phase3_fastapi_integration.py`
- **Dependency Injection**: Use `get_cache_service()` in your FastAPI endpoints
- **Configuration**: Load presets via `get_cache_config()` in your application

### Customization
- **Environment-Specific**: Set different presets per environment (dev/staging/prod)
- **Feature Toggles**: Use `ENABLE_AI_CACHE` and other boolean overrides
- **Advanced Tuning**: Use `CACHE_CUSTOM_CONFIG` for JSON-based fine-tuning

## 💡 Pro Tips

1. **Start Simple**: Begin with `development` preset, upgrade to `production` when ready
2. **Use AI Presets**: For AI applications, always use `ai-development` or `ai-production`
3. **Monitor Performance**: Enable monitoring in development to understand cache behavior
4. **Redis in Production**: Always use Redis for production deployments with `CACHE_REDIS_URL`
5. **Environment Parity**: Use same preset across environments, only override URLs and keys
6. **Test Fallbacks**: Ensure your application works even when Redis is unavailable

---

**🎉 You're Done!** Your cache is now configured and ready to boost your application's performance. The preset system handles all the complex configuration automatically while giving you the flexibility to customize when needed.