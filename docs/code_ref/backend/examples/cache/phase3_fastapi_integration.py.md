---
sidebar_label: phase3_fastapi_integration
---

# Example FastAPI Application Integration with Phase 4 Preset-Based Cache Configuration

  file_path: `backend/examples/cache/phase3_fastapi_integration.py`

This example demonstrates how to integrate Phase 4 preset-based cache configuration
with FastAPI applications, showcasing the simplified approach that reduces 28+
environment variables to 1-4 variables.

🚀 NEW in Phase 4: Preset-Based Configuration
OLD WAY (28+ environment variables):
CACHE_DEFAULT_TTL=1800, CACHE_MEMORY_CACHE_SIZE=200, CACHE_COMPRESSION_THRESHOLD=2000, ...

NEW WAY (1-4 environment variables):
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379  # Override if needed
ENABLE_AI_CACHE=true                     # Feature toggle

## Features Demonstrated

- Preset-based cache configuration (Phase 4 enhancement)
- FastAPI dependency injection with cache services
- Cache lifecycle management (startup/shutdown)
- Health check endpoints with cache status
- Explicit cache factory usage with preset loading
- Configuration-based cache setup via presets
- Cache monitoring and status endpoints
- Graceful degradation patterns

## Environment Setup

# Simplified configuration using presets
export CACHE_PRESET=development              # Choose: disabled, minimal, simple, development, production, ai-development, ai-production
export CACHE_REDIS_URL=redis://localhost:6379   # Essential override
export ENABLE_AI_CACHE=true                  # AI features toggle

## Usage

python backend/examples/cache/phase3_fastapi_integration.py

# Then visit:
# http://localhost:8080/docs - API documentation
# http://localhost:8080/health - Health check
# http://localhost:8080/cache/status - Cache status
# http://localhost:8080/cache/test - Test cache operations
