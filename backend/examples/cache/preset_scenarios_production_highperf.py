#!/usr/bin/env python3
"""
High-Performance Production Cache Example

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
"""

import asyncio
import json
import logging
import os
import time
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Cache infrastructure
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory, CacheInterface

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data models for high-performance API
class DataPoint(BaseModel):
    id: str
    value: float
    category: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class TrendingResponse(BaseModel):
    period: str
    data_points: List[DataPoint]
    total_count: int
    cache_info: Dict[str, Any]
    generation_time_ms: float

class PerformanceMetrics(BaseModel):
    cache_preset: str
    uptime_seconds: float
    total_requests: int
    cache_hit_ratio: float
    avg_response_time_ms: float
    memory_usage: Dict[str, Any]
    connection_pool_stats: Dict[str, Any]
    throughput_per_second: float

class AdvancedCacheStats(BaseModel):
    preset_configuration: Dict[str, Any]
    performance_metrics: PerformanceMetrics
    cache_distribution: Dict[str, int]  # Keys by category
    hot_keys: List[str]  # Most accessed keys
    memory_efficiency: Dict[str, float]

# Global state for production monitoring
_cache: Optional[CacheInterface] = None
_app_start_time: float = 0
_request_count: int = 0
_total_response_time: float = 0
_cache_operations: Dict[str, int] = {"hits": 0, "misses": 0}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Production-ready lifespan with comprehensive cache initialization"""
    global _cache, _app_start_time
    
    _app_start_time = time.time()
    preset_name = os.getenv("CACHE_PRESET", "production")
    
    logger.info(f"🚀 Starting high-performance application with {preset_name} preset")
    
    try:
        # Load production-optimized configuration
        config = get_cache_config()
        factory = CacheFactory()
        _cache = await factory.create_cache_from_config(config)
        
        logger.info(f"✅ Production cache initialized: {type(_cache).__name__}")
        
        # Log production configuration details
        if hasattr(_cache, 'max_connections'):
            logger.info(f"Connection pool size: {getattr(_cache, 'max_connections', 'default')}")
        if hasattr(_cache, '_memory_cache_size'):
            logger.info(f"Memory cache size: {getattr(_cache, '_memory_cache_size', 'default')}")
        if hasattr(_cache, '_compression_threshold'):
            logger.info(f"Compression threshold: {getattr(_cache, '_compression_threshold', 'default')} bytes")
        
        # Warm up cache with common data
        await warmup_cache(_cache, preset_name)
        
        # Store in app state
        app.state.cache = _cache
        app.state.metrics = {
            "requests_by_endpoint": {},
            "cache_operations_by_key_pattern": {},
            "performance_samples": []
        }
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize production cache: {e}")
        yield
    
    finally:
        # Production cleanup with metrics logging
        if _cache:
            try:
                # Log final performance metrics
                uptime = time.time() - _app_start_time
                if _request_count > 0:
                    avg_response_time = _total_response_time / _request_count
                    throughput = _request_count / uptime if uptime > 0 else 0
                    hit_ratio = _cache_operations["hits"] / (_cache_operations["hits"] + _cache_operations["misses"]) if (_cache_operations["hits"] + _cache_operations["misses"]) > 0 else 0
                    
                    logger.info(f"📊 Final performance metrics:")
                    logger.info(f"   Uptime: {uptime:.1f}s")
                    logger.info(f"   Total requests: {_request_count}")
                    logger.info(f"   Avg response time: {avg_response_time:.2f}ms")
                    logger.info(f"   Throughput: {throughput:.2f} req/s")
                    logger.info(f"   Cache hit ratio: {hit_ratio:.2%}")
                
                if hasattr(_cache, 'disconnect'):
                    await _cache.disconnect()
                    logger.info("Production cache disconnected successfully")
                    
            except Exception as e:
                logger.warning(f"Error during production cleanup: {e}")

async def warmup_cache(cache: CacheInterface, preset: str):
    """Warm up cache with common production data"""
    logger.info("🔥 Warming up production cache...")
    
    # Cache common configuration data
    warmup_data = {
        "app:config:version": "1.0.0",
        "app:config:environment": preset,
        "app:config:features": ["caching", "monitoring", "analytics"],
        "categories:list": ["technology", "business", "science", "health", "entertainment"],
        "metadata:schema": {"version": "2.1", "fields": ["id", "value", "category", "timestamp"]}
    }
    
    for key, value in warmup_data.items():
        try:
            await cache.set(key, value, ttl=3600)  # 1 hour TTL for config data
        except Exception as e:
            logger.warning(f"Failed to warm up key {key}: {e}")
    
    logger.info(f"✅ Warmed up {len(warmup_data)} cache entries")

# FastAPI app with production settings
app = FastAPI(
    title="High-Performance Production Cache Example",
    description="Demonstrates production and ai-production presets for high-traffic applications",
    version="1.0.0",
    lifespan=lifespan
)

# Production CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_cache() -> CacheInterface:
    """Get production cache instance"""
    if not hasattr(app.state, 'cache') or app.state.cache is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Production cache service unavailable"
        )
    return app.state.cache

def track_request_metrics(endpoint: str, response_time_ms: float, cache_hit: bool):
    """Track production request metrics"""
    global _request_count, _total_response_time, _cache_operations
    
    _request_count += 1
    _total_response_time += response_time_ms
    
    if cache_hit:
        _cache_operations["hits"] += 1
    else:
        _cache_operations["misses"] += 1
    
    # Track endpoint-specific metrics
    if hasattr(app.state, 'metrics'):
        if endpoint not in app.state.metrics["requests_by_endpoint"]:
            app.state.metrics["requests_by_endpoint"][endpoint] = {
                "count": 0, "total_time": 0, "cache_hits": 0
            }
        
        app.state.metrics["requests_by_endpoint"][endpoint]["count"] += 1
        app.state.metrics["requests_by_endpoint"][endpoint]["total_time"] += response_time_ms
        if cache_hit:
            app.state.metrics["requests_by_endpoint"][endpoint]["cache_hits"] += 1

def generate_mock_data(category: str, count: int) -> List[DataPoint]:
    """Generate mock data for high-performance testing"""
    return [
        DataPoint(
            id=f"{category}_{i}_{int(time.time())}",
            value=random.uniform(10.0, 1000.0),
            category=category,
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 1440)),
            metadata={
                "source": "high_perf_generator",
                "quality_score": random.uniform(0.7, 1.0),
                "trending_score": random.uniform(0, 100)
            }
        ) for i in range(count)
    ]

@app.get("/")
async def root():
    """Root endpoint with production info"""
    preset_name = os.getenv("CACHE_PRESET", "production")
    uptime = time.time() - _app_start_time
    
    return {
        "message": "High-Performance Production Cache Example",
        "preset": preset_name,
        "uptime_seconds": round(uptime, 1),
        "total_requests": _request_count,
        "cache_hit_ratio": round(_cache_operations["hits"] / max(1, _cache_operations["hits"] + _cache_operations["misses"]), 3),
        "endpoints": {
            "trending_data": "/api/data/trending",
            "category_data": "/api/data/category/{category}",
            "bulk_data": "/api/data/bulk",
            "performance_metrics": "/monitoring/performance",
            "cache_analysis": "/monitoring/cache-analysis"
        }
    }

@app.get("/api/data/trending", response_model=TrendingResponse)
async def get_trending_data(
    period: str = Query("24h", description="Time period: 1h, 24h, 7d"),
    limit: int = Query(100, le=1000, description="Max items to return"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get trending data with production-level caching
    
    Demonstrates high-performance caching patterns with monitoring
    """
    start_time = time.time()
    cache = await get_cache()
    
    # Production cache key with multiple parameters
    cache_key = f"trending:period:{period}:limit:{limit}:v2"
    
    # Try cache first (production pattern)
    cached_result = await cache.get(cache_key)
    if cached_result:
        response_time = (time.time() - start_time) * 1000
        track_request_metrics("trending", response_time, cache_hit=True)
        
        logger.info(f"Cache HIT for trending data ({period}, limit={limit}) - {response_time:.1f}ms")
        
        # Add cache info to response
        cached_result["cache_info"]["cache_hit"] = True
        cached_result["cache_info"]["response_time_ms"] = response_time
        
        return TrendingResponse(**cached_result)
    
    # Cache miss - generate data (simulate expensive database query)
    logger.info(f"Cache MISS for trending data ({period}, limit={limit})")
    
    # Simulate data processing time
    await asyncio.sleep(0.1)  # 100ms for "database query"
    
    # Generate trending data across categories
    categories = ["technology", "business", "science", "health", "entertainment"]
    all_data = []
    
    for category in categories:
        category_data = generate_mock_data(category, limit // len(categories))
        all_data.extend(category_data)
    
    # Sort by trending score and limit
    all_data.sort(key=lambda x: x.metadata.get("trending_score", 0), reverse=True)
    trending_data = all_data[:limit]
    
    generation_time = (time.time() - start_time) * 1000
    
    # Prepare response
    response_data = {
        "period": period,
        "data_points": [dp.model_dump() for dp in trending_data],
        "total_count": len(trending_data),
        "cache_info": {
            "cache_hit": False,
            "cache_key": cache_key,
            "generated_at": datetime.now().isoformat(),
            "ttl_hours": 1 if period == "1h" else 4 if period == "24h" else 12
        },
        "generation_time_ms": generation_time
    }
    
    # Cache with period-appropriate TTL
    ttl_map = {"1h": 1800, "24h": 7200, "7d": 14400}  # 30min, 2h, 4h
    ttl = ttl_map.get(period, 3600)
    
    # Background caching to not block response
    background_tasks.add_task(cache.set, cache_key, response_data, ttl)
    
    track_request_metrics("trending", generation_time, cache_hit=False)
    logger.info(f"Generated and cached trending data - {generation_time:.1f}ms")
    
    return TrendingResponse(**response_data)

@app.get("/api/data/category/{category}")
async def get_category_data(
    category: str,
    limit: int = Query(50, le=500),
    include_metadata: bool = Query(True)
):
    """Get category-specific data with optimized caching"""
    start_time = time.time()
    cache = await get_cache()
    
    cache_key = f"category:{category}:limit:{limit}:meta:{include_metadata}"
    
    # Check cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        response_time = (time.time() - start_time) * 1000
        track_request_metrics("category", response_time, cache_hit=True)
        
        return {
            "category": category,
            "data": cached_data,
            "cache_hit": True,
            "response_time_ms": response_time
        }
    
    # Generate category data
    data = generate_mock_data(category, limit)
    
    # Optionally strip metadata for smaller cache size
    if not include_metadata:
        for item in data:
            item.metadata = {}
    
    response_data = [dp.model_dump() for dp in data]
    
    # Cache with category-appropriate TTL
    await cache.set(cache_key, response_data, ttl=3600)  # 1 hour
    
    response_time = (time.time() - start_time) * 1000
    track_request_metrics("category", response_time, cache_hit=False)
    
    return {
        "category": category,
        "data": response_data,
        "cache_hit": False,
        "response_time_ms": response_time
    }

@app.post("/api/data/bulk")
async def get_bulk_data(
    categories: List[str],
    limit_per_category: int = Query(20, le=100)
):
    """
    Bulk data retrieval with parallel caching
    
    Demonstrates high-performance parallel cache operations
    """
    start_time = time.time()
    cache = await get_cache()
    
    # Parallel cache lookups
    tasks = []
    cache_keys = []
    
    for category in categories:
        cache_key = f"bulk:{category}:limit:{limit_per_category}"
        cache_keys.append((category, cache_key))
        tasks.append(cache.get(cache_key))
    
    # Execute parallel cache gets
    cached_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and identify cache misses
    results = {}
    cache_misses = []
    
    for i, (category, cache_key) in enumerate(cache_keys):
        cached_result = cached_results[i]
        if cached_result and not isinstance(cached_result, Exception):
            results[category] = cached_result
            _cache_operations["hits"] += 1
        else:
            cache_misses.append(category)
            _cache_operations["misses"] += 1
    
    # Generate data for cache misses
    if cache_misses:
        logger.info(f"Bulk cache misses for categories: {cache_misses}")
        
        # Parallel data generation
        generation_tasks = []
        for category in cache_misses:
            generation_tasks.append(generate_mock_data(category, limit_per_category))
        
        generated_data = await asyncio.gather(*generation_tasks)
        
        # Cache generated data (parallel)
        cache_tasks = []
        for i, category in enumerate(cache_misses):
            data = [dp.model_dump() for dp in generated_data[i]]
            results[category] = data
            cache_key = f"bulk:{category}:limit:{limit_per_category}"
            cache_tasks.append(cache.set(cache_key, data, ttl=1800))  # 30 min
        
        await asyncio.gather(*cache_tasks, return_exceptions=True)
    
    response_time = (time.time() - start_time) * 1000
    track_request_metrics("bulk", response_time, len(cache_misses) == 0)
    
    return {
        "categories": categories,
        "results": results,
        "cache_hits": len(categories) - len(cache_misses),
        "cache_misses": len(cache_misses),
        "total_items": sum(len(data) for data in results.values()),
        "response_time_ms": response_time
    }

@app.get("/monitoring/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Production performance monitoring endpoint"""
    cache = await get_cache()
    
    uptime = time.time() - _app_start_time
    hit_ratio = 0.0
    if (_cache_operations["hits"] + _cache_operations["misses"]) > 0:
        hit_ratio = _cache_operations["hits"] / (_cache_operations["hits"] + _cache_operations["misses"])
    
    avg_response_time = _total_response_time / max(1, _request_count)
    throughput = _request_count / max(1, uptime)
    
    # Memory usage (mock - would be real in production)
    memory_usage = {
        "cache_memory_mb": random.uniform(50, 200),
        "total_memory_mb": random.uniform(200, 500),
        "memory_utilization": random.uniform(0.3, 0.8)
    }
    
    # Connection pool stats (mock)
    connection_stats = {
        "active_connections": random.randint(5, 25),
        "max_connections": 50,
        "connection_utilization": random.uniform(0.1, 0.5)
    }
    
    return PerformanceMetrics(
        cache_preset=os.getenv("CACHE_PRESET", "production"),
        uptime_seconds=uptime,
        total_requests=_request_count,
        cache_hit_ratio=hit_ratio,
        avg_response_time_ms=avg_response_time,
        memory_usage=memory_usage,
        connection_pool_stats=connection_stats,
        throughput_per_second=throughput
    )

@app.get("/monitoring/cache-analysis", response_model=AdvancedCacheStats)
async def get_advanced_cache_analysis():
    """Advanced cache analysis for production optimization"""
    cache = await get_cache()
    preset_name = os.getenv("CACHE_PRESET", "production")
    
    # Get preset configuration details
    preset_config = {
        "preset_name": preset_name,
        "redis_url": os.getenv("CACHE_REDIS_URL", "not_configured"),
        "custom_config": os.getenv("CACHE_CUSTOM_CONFIG", "none"),
        "ai_features": preset_name.startswith("ai-")
    }
    
    # Performance metrics
    uptime = time.time() - _app_start_time
    hit_ratio = _cache_operations["hits"] / max(1, _cache_operations["hits"] + _cache_operations["misses"])
    
    perf_metrics = PerformanceMetrics(
        cache_preset=preset_name,
        uptime_seconds=uptime,
        total_requests=_request_count,
        cache_hit_ratio=hit_ratio,
        avg_response_time_ms=_total_response_time / max(1, _request_count),
        memory_usage={"estimated_mb": random.uniform(100, 300)},
        connection_pool_stats={"active": random.randint(3, 20)},
        throughput_per_second=_request_count / max(1, uptime)
    )
    
    # Cache distribution analysis (mock)
    cache_distribution = {
        "trending_keys": random.randint(10, 50),
        "category_keys": random.randint(20, 100),
        "bulk_keys": random.randint(5, 30),
        "config_keys": random.randint(3, 10)
    }
    
    # Hot keys analysis (mock)
    hot_keys = [
        "trending:period:24h:limit:100:v2",
        "category:technology:limit:50:meta:True",
        "bulk:business:limit:20",
        "app:config:features"
    ]
    
    # Memory efficiency metrics
    memory_efficiency = {
        "compression_ratio": random.uniform(0.3, 0.7),
        "key_overhead_percent": random.uniform(10, 20),
        "avg_value_size_kb": random.uniform(1, 10)
    }
    
    return AdvancedCacheStats(
        preset_configuration=preset_config,
        performance_metrics=perf_metrics,
        cache_distribution=cache_distribution,
        hot_keys=hot_keys,
        memory_efficiency=memory_efficiency
    )

@app.delete("/monitoring/cache-clear")
async def clear_production_cache():
    """Clear production cache with metrics reset"""
    global _cache_operations, _request_count, _total_response_time
    
    cache = await get_cache()
    
    try:
        if hasattr(cache, 'clear'):
            await cache.clear()
        
        # Reset metrics
        _cache_operations = {"hits": 0, "misses": 0}
        _request_count = 0
        _total_response_time = 0
        
        if hasattr(app.state, 'metrics'):
            app.state.metrics = {
                "requests_by_endpoint": {},
                "cache_operations_by_key_pattern": {},
                "performance_samples": []
            }
        
        logger.info("Production cache and metrics cleared")
        return {"success": True, "message": "Production cache and metrics cleared"}
        
    except Exception as e:
        logger.error(f"Production cache clear failed: {e}")
        return {"success": False, "message": f"Clear failed: {str(e)}"}

@app.get("/health")
async def health_check():
    """Production health check with comprehensive status"""
    try:
        cache = await get_cache()
        
        # Comprehensive cache health test
        health_test_key = "health:production:test"
        health_test_data = {
            "timestamp": datetime.now().isoformat(),
            "test_data": "production_health_check",
            "random": random.randint(1000, 9999)
        }
        
        # Test write, read, delete cycle
        await cache.set(health_test_key, health_test_data, ttl=10)
        retrieved_data = await cache.get(health_test_key)
        await cache.delete(health_test_key)
        
        cache_healthy = retrieved_data is not None
        
        # Additional health metrics
        uptime = time.time() - _app_start_time
        hit_ratio = _cache_operations["hits"] / max(1, _cache_operations["hits"] + _cache_operations["misses"])
        
        return {
            "status": "healthy" if cache_healthy else "degraded",
            "production_cache": {
                "healthy": cache_healthy,
                "preset": os.getenv("CACHE_PRESET", "production"),
                "type": type(cache).__name__,
                "uptime_seconds": round(uptime, 1),
                "total_requests": _request_count,
                "cache_hit_ratio": round(hit_ratio, 3)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Production health check failed: {e}")
        return {
            "status": "unhealthy",
            "production_cache": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run the high-performance production example"""
    preset_name = os.getenv("CACHE_PRESET", "production")
    print(f"🚀 Starting High-Performance Application with {preset_name} preset")
    print("📖 API docs: http://localhost:8083/docs")
    print("🔍 Health: http://localhost:8083/health")
    print("📊 Performance: http://localhost:8083/monitoring/performance")
    print("🔬 Cache Analysis: http://localhost:8083/monitoring/cache-analysis")
    print("📈 Trending Data: http://localhost:8083/api/data/trending")
    print()
    
    preset_tips = {
        "production": "💡 High-performance preset for production web applications",
        "ai-production": "💡 AI-optimized production preset with advanced text processing"
    }
    
    if preset_name in preset_tips:
        print(preset_tips[preset_name])
    
    print()
    print("💡 Production optimization tips:")
    if preset_name == "production":
        print("   export CACHE_CUSTOM_CONFIG='{\"max_connections\": 50, \"memory_cache_size\": 2000}'")
    elif preset_name == "ai-production":
        print("   export CACHE_CUSTOM_CONFIG='{\"compression_level\": 9, \"memory_cache_size\": 1500}'")
    
    print()
    print("🧪 Performance testing:")
    print("   curl http://localhost:8083/api/data/trending?period=24h&limit=500")
    print("   curl http://localhost:8083/monitoring/performance")
    print()
    
    # Run the application
    uvicorn.run(
        "preset_scenarios_production_highperf:app",
        host="0.0.0.0",
        port=8083,
        reload=False,
        log_level="info",
        workers=1  # Single worker for this example
    )

if __name__ == "__main__":
    main()