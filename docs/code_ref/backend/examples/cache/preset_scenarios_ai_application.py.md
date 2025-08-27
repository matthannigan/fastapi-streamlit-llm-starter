---
sidebar_label: preset_scenarios_ai_application
---

# AI Application Cache Example with AI-Optimized Presets

  file_path: `backend/examples/cache/preset_scenarios_ai_application.py`

This example demonstrates how to use ai-development and ai-production presets
for AI-powered applications with text processing and caching.

## Environment Setup

# For AI development
export CACHE_PRESET=ai-development
export GEMINI_API_KEY=your-api-key

# For AI production
export CACHE_PRESET=ai-production
export CACHE_REDIS_URL=redis://production:6379
export GEMINI_API_KEY=your-production-api-key

## Usage

python backend/examples/cache/preset_scenarios_ai_application.py
curl -X POST http://localhost:8082/ai/summarize -H "Content-Type: application/json" -d '{"text":"Long text to summarize..."}'
curl http://localhost:8082/ai/cache/stats
