#!/usr/bin/env python3
"""
Example FastAPI Application Integration with Phase 4 Preset-Based Cache Configuration

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

Features Demonstrated:
    - Preset-based cache configuration (Phase 4 enhancement)
    - FastAPI dependency injection with cache services
    - Cache lifecycle management (startup/shutdown)
    - Health check endpoints with cache status
    - Explicit cache factory usage with preset loading
    - Configuration-based cache setup via presets
    - Cache monitoring and status endpoints
    - Graceful degradation patterns

Environment Setup:
    # Simplified configuration using presets
    export CACHE_PRESET=development              # Choose: disabled, minimal, simple, development, production, ai-development, ai-production
    export CACHE_REDIS_URL=redis://localhost:6379   # Essential override
    export ENABLE_AI_CACHE=true                  # AI features toggle

Usage:
    python backend/examples/cache/phase3_fastapi_integration.py
    
    # Then visit:
    # http://localhost:8080/docs - API documentation
    # http://localhost:8080/health - Health check
    # http://localhost:8080/cache/status - Cache status
    # http://localhost:8080/cache/test - Test cache operations
"""

import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Phase 3 cache imports
from app.infrastructure.cache import (
    CacheFactory,
    CacheConfig,
    CacheConfigBuilder,
    get_cache_service,
    get_web_cache_service,
    get_ai_cache_service,
    get_cache_health_status,
    cleanup_cache_registry,
    CacheDependencyManager,
    CacheInterface
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class CacheTestRequest(BaseModel):
    key: str
    value: str
    ttl: Optional[int] = 300

class CacheTestResponse(BaseModel):
    success: bool
    message: str
    cached_value: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    cache_status: Dict[str, Any]
    timestamp: str

class CacheStatusResponse(BaseModel):
    cache_type: str
    connected: bool
    performance_stats: Dict[str, Any]
    configuration: Dict[str, Any]

# Global cache instances for demonstration
_demo_caches: Dict[str, CacheInterface] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler demonstrating cache initialization and cleanup
    """
    # Startup: Initialize cache instances using Phase 3 factory methods
    logger.info("🚀 Starting FastAPI app with Phase 3 cache infrastructure")
    
    try:
        # Initialize different cache types using explicit factory methods
        factory = CacheFactory()
        
        # Web application cache (optimized for web workloads)
        logger.info("Creating web cache using for_web_app() factory method")
        _demo_caches["web"] = await factory.for_web_app(
            redis_url=None,  # Will fallback to memory cache
            fail_on_connection_error=False
        )
        
        # AI application cache (optimized for AI workloads)  
        logger.info("Creating AI cache using for_ai_app() factory method")
        _demo_caches["ai"] = await factory.for_ai_app(
            redis_url=None,  # Will fallback to memory cache
            fail_on_connection_error=False
        )
        
        # Testing cache (minimal configuration)
        logger.info("Creating test cache using for_testing() factory method")
        _demo_caches["test"] = await factory.for_testing(use_memory_cache=True)
        
        # Configuration-based cache (legacy builder pattern)
        logger.info("Creating config-based cache using builder pattern")
        config = (CacheConfigBuilder()
                 .for_environment("development")
                 .with_memory_cache(200)
                 .build())
        _demo_caches["config"] = await factory.create_cache_from_config(config)
        
        # 🚀 NEW: Preset-based cache (Phase 4 enhancement)
        logger.info("Creating preset-based cache using new dependency injection")
        from app.infrastructure.cache.dependencies import get_cache_config
        
        # Load configuration from preset system (CACHE_PRESET environment variable)
        preset_config = get_cache_config()
        _demo_caches["preset"] = await factory.create_cache_from_config(preset_config)
        logger.info(f"Loaded preset-based cache with configuration: {preset_config.__class__.__name__}")
        
        logger.info(f"✅ Initialized {len(_demo_caches)} cache instances successfully")
        
        # Store in app state for access in dependencies
        app.state.demo_caches = _demo_caches
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize caches: {e}")
        yield
    
    finally:
        # Shutdown: Cleanup cache resources
        logger.info("🧹 Cleaning up cache resources")
        
        try:
            # Disconnect all cache instances
            for cache_name, cache in _demo_caches.items():
                try:
                    if hasattr(cache, 'disconnect'):
                        await cache.disconnect()
                        logger.info(f"Disconnected {cache_name} cache")
                except Exception as e:
                    logger.warning(f"Error disconnecting {cache_name} cache: {e}")
            
            # Cleanup the cache registry
            await cleanup_cache_registry()
            logger.info("✅ Cache cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during cache cleanup: {e}")

# FastAPI app with lifespan management
app = FastAPI(
    title="Phase 3 Cache Integration Example",
    description="Demonstration of Phase 3 cache infrastructure with FastAPI",
    version="3.0.0",
    lifespan=lifespan
)

# Dependency to get demo cache instances
async def get_demo_cache(cache_type: str = "web") -> CacheInterface:
    """Get a demo cache instance by type"""
    if not hasattr(app.state, 'demo_caches'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache services not initialized"
        )
    
    if cache_type not in app.state.demo_caches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cache type '{cache_type}' not available. Available: {list(app.state.demo_caches.keys())}"
        )
    
    return app.state.demo_caches[cache_type]

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Phase 3 Cache Integration Example",
        "version": "3.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "cache_status": "/cache/status",
        "cache_test": "/cache/test"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check including cache status
    
    Demonstrates integration with Phase 3 health monitoring
    """
    from datetime import datetime
    
    try:
        # Check if caches are available
        if not hasattr(app.state, 'demo_caches'):
            return HealthResponse(
                status="unhealthy",
                cache_status={"error": "Cache services not initialized"},
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Check each cache instance
        cache_statuses = {}
        overall_healthy = True
        
        for cache_name, cache in app.state.demo_caches.items():
            try:
                # Use Phase 3 health check dependency
                health_status = await get_cache_health_status(cache)
                cache_statuses[cache_name] = health_status
                
                if not health_status.get("healthy", False):
                    overall_healthy = False
                    
            except Exception as e:
                cache_statuses[cache_name] = {
                    "healthy": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return HealthResponse(
            status="healthy" if overall_healthy else "degraded",
            cache_status=cache_statuses,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            cache_status={"error": str(e)},
            timestamp=datetime.utcnow().isoformat()
        )

@app.get("/cache/status", response_model=Dict[str, CacheStatusResponse])
async def cache_status():
    """
    Detailed cache status information
    
    Shows configuration and performance stats for each cache type
    """
    if not hasattr(app.state, 'demo_caches'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache services not initialized"
        )
    
    status_info = {}
    
    for cache_name, cache in app.state.demo_caches.items():
        try:
            # Get cache type
            cache_type = type(cache).__name__
            
            # Check connection status
            connected = True
            try:
                if hasattr(cache, 'ping'):
                    connected = await cache.ping()
                else:
                    # Test with a simple operation
                    await cache.set("_health_check", "ok", ttl=1)
                    await cache.delete("_health_check")
            except Exception:
                connected = False
            
            # Get performance stats if available
            perf_stats = {}
            if hasattr(cache, '_performance_monitor') and cache._performance_monitor:
                monitor = cache._performance_monitor
                if hasattr(monitor, 'get_performance_summary'):
                    perf_stats = monitor.get_performance_summary()
            
            # Get configuration info
            config_info = {
                "type": cache_type,
                "has_monitoring": hasattr(cache, '_performance_monitor'),
                "has_l1_cache": hasattr(cache, '_l1_cache'),
            }
            
            if hasattr(cache, 'default_ttl'):
                config_info["default_ttl"] = cache.default_ttl
            if hasattr(cache, 'max_size'):
                config_info["max_size"] = cache.max_size
            
            status_info[cache_name] = CacheStatusResponse(
                cache_type=cache_type,
                connected=connected,
                performance_stats=perf_stats,
                configuration=config_info
            )
            
        except Exception as e:
            logger.error(f"Error getting status for {cache_name}: {e}")
            status_info[cache_name] = CacheStatusResponse(
                cache_type="unknown",
                connected=False,
                performance_stats={},
                configuration={"error": str(e)}
            )
    
    return status_info

@app.post("/cache/test", response_model=CacheTestResponse)
async def test_cache_operations(
    request: CacheTestRequest,
    cache_type: str = "web",
    cache: CacheInterface = Depends(get_demo_cache)
):
    """
    Test cache operations with a specific cache type
    
    Demonstrates basic cache operations with the Phase 3 infrastructure
    """
    try:
        # Store the value
        await cache.set(request.key, request.value, ttl=request.ttl)
        logger.info(f"Stored key '{request.key}' in {cache_type} cache")
        
        # Retrieve the value
        cached_value = await cache.get(request.key)
        
        if cached_value == request.value:
            return CacheTestResponse(
                success=True,
                message=f"Successfully stored and retrieved value using {cache_type} cache",
                cached_value=cached_value
            )
        else:
            return CacheTestResponse(
                success=False,
                message=f"Value mismatch: stored '{request.value}', retrieved '{cached_value}'",
                cached_value=cached_value
            )
            
    except Exception as e:
        logger.error(f"Cache test failed: {e}")
        return CacheTestResponse(
            success=False,
            message=f"Cache operation failed: {str(e)}",
            cached_value=None
        )

@app.delete("/cache/clear")
async def clear_cache(
    cache_type: str = "web",
    cache: CacheInterface = Depends(get_demo_cache)
):
    """
    Clear all entries from a specific cache
    """
    try:
        if hasattr(cache, 'clear'):
            await cache.clear()
            message = f"Cleared {cache_type} cache"
        else:
            message = f"Cache type {cache_type} does not support clear operation"
        
        return {"success": True, "message": message}
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return {"success": False, "message": f"Clear failed: {str(e)}"}

# Demonstration of using standard Phase 3 dependencies
@app.get("/dependencies/demo")
async def dependency_demo(
    # These dependencies use the actual Phase 3 dependency system
    web_cache: CacheInterface = Depends(get_web_cache_service),
    ai_cache: CacheInterface = Depends(get_ai_cache_service),
    main_cache: CacheInterface = Depends(get_cache_service)
):
    """
    Demonstrate using the actual Phase 3 dependency injection system
    
    This endpoint shows how to use the dependency functions in a real application
    """
    cache_info = {}
    
    for cache_name, cache in [("web", web_cache), ("ai", ai_cache), ("main", main_cache)]:
        cache_info[cache_name] = {
            "type": type(cache).__name__,
            "id": id(cache),
            "has_monitoring": hasattr(cache, '_performance_monitor')
        }
    
    return {
        "message": "Phase 3 dependency injection working",
        "caches": cache_info,
        "note": "These caches are managed by the Phase 3 dependency system"
    }

def main():
    """
    Main function to run the example application
    """
    print("🚀 Starting Phase 3 Cache Integration Example")
    print("📖 Visit http://localhost:8080/docs for API documentation")
    print("🔍 Visit http://localhost:8080/health for health status")
    print("📊 Visit http://localhost:8080/cache/status for cache details")
    print("🧪 Visit http://localhost:8080/cache/test for testing cache operations")
    print()
    
    # Run the FastAPI application
    uvicorn.run(
        "phase3_fastapi_integration:app",
        host="0.0.0.0", 
        port=8080,
        reload=False,  # Disable reload to prevent issues with lifespan
        log_level="info"
    )

if __name__ == "__main__":
    main()