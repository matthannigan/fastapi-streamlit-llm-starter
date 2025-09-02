---
sidebar_label: preset_scenarios_production_highperf
---

# High-Performance Production Cache Example

  file_path: `backend/examples/cache/preset_scenarios_production_highperf.py`

This example demonstrates production and ai-production presets for high-traffic
applications with advanced caching patterns, monitoring, and performance optimization.

Environment Setup:
    # High-performance web production
    export CACHE_PRESET=production
    export CACHE_REDIS_URL=redis://production-redis:6379
    export CACHE_CUSTOM_CONFIG='{"max_connections": 50, "memory_cache_size": 2000}'
    
    # AI production with custom optimization
    export CACHE_PRESET=ai-production
    export CACHE_REDIS_URL=redis://ai-redis-cluster:6379
    export CACHE_CUSTOM_CONFIG='{"compression_level": 9, "memory_cache_size": 1500}'

Usage:
    python backend/examples/cache/preset_scenarios_production_highperf.py
    curl http://localhost:8083/api/data/trending
    curl http://localhost:8083/monitoring/performance

## DataPoint

## TrendingResponse

## PerformanceMetrics

## AdvancedCacheStats

## lifespan()

```python
async def lifespan(app: FastAPI):
```

Production-ready lifespan with comprehensive cache initialization

## warmup_cache()

```python
async def warmup_cache(cache: CacheInterface, preset: str):
```

Warm up cache with common production data

## get_cache()

```python
async def get_cache() -> CacheInterface:
```

Get production cache instance

## track_request_metrics()

```python
def track_request_metrics(endpoint: str, response_time_ms: float, cache_hit: bool):
```

Track production request metrics

## generate_mock_data()

```python
def generate_mock_data(category: str, count: int) -> List[DataPoint]:
```

Generate mock data for high-performance testing

## root()

```python
async def root():
```

Root endpoint with production info

## get_trending_data()

```python
async def get_trending_data(period: str = Query('24h', description='Time period: 1h, 24h, 7d'), limit: int = Query(100, le=1000, description='Max items to return'), background_tasks: BackgroundTasks = BackgroundTasks()):
```

Get trending data with production-level caching

Demonstrates high-performance caching patterns with monitoring

## get_category_data()

```python
async def get_category_data(category: str, limit: int = Query(50, le=500), include_metadata: bool = Query(True)):
```

Get category-specific data with optimized caching

## get_bulk_data()

```python
async def get_bulk_data(categories: List[str], limit_per_category: int = Query(20, le=100)):
```

Bulk data retrieval with parallel caching

Demonstrates high-performance parallel cache operations

## get_performance_metrics()

```python
async def get_performance_metrics():
```

Production performance monitoring endpoint

## get_advanced_cache_analysis()

```python
async def get_advanced_cache_analysis():
```

Advanced cache analysis for production optimization

## clear_production_cache()

```python
async def clear_production_cache():
```

Clear production cache with metrics reset

## health_check()

```python
async def health_check():
```

Production health check with comprehensive status

## main()

```python
def main():
```

Run the high-performance production example
