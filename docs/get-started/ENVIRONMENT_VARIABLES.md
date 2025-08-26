# Environment Variables

**Essential environment variables for configuration:**

### Development/Local Recommendations
```bash
# Basic Configuration
RESILIENCE_PRESET=development
API_KEY=dev-test-key
GEMINI_API_KEY=your-gemini-api-key

# Cache Configuration (choose one preset)
CACHE_PRESET=development              # Choose: disabled, minimal, simple, development, production, ai-development, ai-production

# Optional Cache Overrides (only when needed)
CACHE_REDIS_URL=redis://localhost:6379  # Override Redis connection URL
ENABLE_AI_CACHE=true                     # Toggle AI cache features

# Frontend Configuration
API_BASE_URL=http://localhost:8000
SHOW_DEBUG_INFO=true
INPUT_MAX_LENGTH=10000

# Health Check Configuration
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=1

# Development Features
DEBUG=true
LOG_LEVEL=DEBUG
```

### Production Recommendations
```bash
# Production Configuration
RESILIENCE_PRESET=production
API_KEY=your-secure-production-key
ADDITIONAL_API_KEYS=key1,key2,key3
GEMINI_API_KEY=your-production-gemini-key

# Cache Configuration
CACHE_PRESET=production               # Production-optimized cache settings

# Infrastructure
CACHE_REDIS_URL=redis://your-redis-instance:6379  # Production Redis instance
CORS_ORIGINS=["https://your-frontend-domain.com"]

# Frontend Configuration
API_BASE_URL=https://api.your-domain.com
SHOW_DEBUG_INFO=false
INPUT_MAX_LENGTH=50000

# Health Check Configuration  
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=2

# Security
DISABLE_INTERNAL_DOCS=true
LOG_LEVEL=INFO
```

**Advanced Configuration:**
```bash
# Custom Resilience Configuration
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 5, "circuit_breaker_threshold": 10}'

# Custom Cache Configuration (JSON overrides)
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 500,
  "memory_cache_size": 2000,
  "operation_ttls": {
    "summarize": 7200,
    "sentiment": 3600
  }
}'

# Performance Tuning
MAX_CONCURRENT_REQUESTS=50
```
