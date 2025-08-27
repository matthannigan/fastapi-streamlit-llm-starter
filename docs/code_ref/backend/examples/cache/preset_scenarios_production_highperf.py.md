---
sidebar_label: preset_scenarios_production_highperf
---

# High-Performance Production Cache Example

  file_path: `backend/examples/cache/preset_scenarios_production_highperf.py`

This example demonstrates production and ai-production presets for high-traffic
applications with advanced caching patterns, monitoring, and performance optimization.

## Environment Setup

# High-performance web production
export CACHE_PRESET=production
export CACHE_REDIS_URL=redis://production-redis:6379
export CACHE_CUSTOM_CONFIG='{"max_connections": 50, "memory_cache_size": 2000}'

# AI production with custom optimization
export CACHE_PRESET=ai-production
export CACHE_REDIS_URL=redis://ai-redis-cluster:6379
export CACHE_CUSTOM_CONFIG='{"compression_level": 9, "memory_cache_size": 1500}'

## Usage

python backend/examples/cache/preset_scenarios_production_highperf.py
curl http://localhost:8083/api/data/trending
curl http://localhost:8083/monitoring/performance
