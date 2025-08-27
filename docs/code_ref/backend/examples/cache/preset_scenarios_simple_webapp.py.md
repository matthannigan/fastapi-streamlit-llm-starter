---
sidebar_label: preset_scenarios_simple_webapp
---

# Simple Web Application Cache Example with Presets

  file_path: `backend/examples/cache/preset_scenarios_simple_webapp.py`

This example demonstrates how to use cache presets for a simple web application.
Shows the 'simple' and 'development' presets with basic caching patterns.

## Environment Setup

# For development/testing
export CACHE_PRESET=development

# For small production deployment
export CACHE_PRESET=simple
export CACHE_REDIS_URL=redis://production:6379

## Usage

python backend/examples/cache/preset_scenarios_simple_webapp.py
curl http://localhost:8081/user/123
curl http://localhost:8081/cache/info
