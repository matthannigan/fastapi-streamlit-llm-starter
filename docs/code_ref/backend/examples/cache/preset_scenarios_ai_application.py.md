---
sidebar_label: preset_scenarios_ai_application
---

# AI Application Cache Example with AI-Optimized Presets

  file_path: `backend/examples/cache/preset_scenarios_ai_application.py`

This example demonstrates how to use ai-development and ai-production presets
for AI-powered applications with text processing and caching.

Environment Setup:
    # For AI development
    export CACHE_PRESET=ai-development
    export GEMINI_API_KEY=your-api-key
    
    # For AI production
    export CACHE_PRESET=ai-production
    export CACHE_REDIS_URL=redis://production:6379
    export GEMINI_API_KEY=your-production-api-key

Usage:
    python backend/examples/cache/preset_scenarios_ai_application.py
    curl -X POST http://localhost:8082/ai/summarize -H "Content-Type: application/json" -d '{"text":"Long text to summarize..."}'
    curl http://localhost:8082/ai/cache/stats

## AIRequest

## SummarizeRequest

## SentimentRequest

## AIResponse

## CacheStats

## lifespan()

```python
async def lifespan(app: FastAPI):
```

Application lifespan with AI-optimized cache initialization

## get_cache()

```python
async def get_cache() -> CacheInterface:
```

Get AI cache instance from app state

## update_operation_stats()

```python
def update_operation_stats(operation: str, cache_hit: bool):
```

Update operation statistics

## generate_ai_cache_key()

```python
def generate_ai_cache_key(operation: str, text: str, options: Dict[str, Any] = None) -> tuple[str, str]:
```

Generate cache key for AI operations with text hashing

Returns:
    tuple: (cache_key, text_hash)

## mock_ai_processing()

```python
async def mock_ai_processing(operation: str, text: str, options: Dict[str, Any] = None) -> Any:
```

Mock AI processing (replace with real AI service calls)

Simulates processing time based on text length

## root()

```python
async def root():
```

Root endpoint

## summarize_text()

```python
async def summarize_text(request: SummarizeRequest):
```

Summarize text with AI-optimized caching

Demonstrates AI cache with operation-specific TTLs

## analyze_sentiment()

```python
async def analyze_sentiment(request: SentimentRequest):
```

Analyze text sentiment with AI-optimized caching

## extract_key_points()

```python
async def extract_key_points(request: AIRequest):
```

Extract key points from text with AI-optimized caching

## get_ai_cache_stats()

```python
async def get_ai_cache_stats():
```

Get AI cache statistics and performance metrics

## clear_ai_cache()

```python
async def clear_ai_cache():
```

Clear AI cache and reset statistics

## health_check()

```python
async def health_check():
```

Health check for AI application

## main()

```python
def main():
```

Run the AI application example
