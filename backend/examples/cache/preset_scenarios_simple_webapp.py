#!/usr/bin/env python3
"""
Simple Web Application Cache Example with Presets

This example demonstrates how to use cache presets for a simple web application.
Shows the 'simple' and 'development' presets with basic caching patterns.

Environment Setup:
    # For development/testing
    export CACHE_PRESET=development
    
    # For small production deployment
    export CACHE_PRESET=simple
    export CACHE_REDIS_URL=redis://production:6379

Usage:
    python backend/examples/cache/preset_scenarios_simple_webapp.py
    curl http://localhost:8081/user/123
    curl http://localhost:8081/cache/info
"""

import asyncio
import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

# Cache infrastructure
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory, CacheInterface

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data models
class User(BaseModel):
    id: int
    name: str
    email: str
    last_seen: datetime

class CacheInfo(BaseModel):
    preset_used: str
    cache_type: str
    total_keys: int
    hit_ratio: Optional[float] = None
    performance_stats: Dict[str, Any] = {}

# Global cache instance
_cache: Optional[CacheInterface] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with cache initialization"""
    global _cache
    
    preset_name = os.getenv("CACHE_PRESET", "development")
    logger.info(f"🚀 Starting simple web app with {preset_name} preset")
    
    try:
        # Load preset configuration
        config = get_cache_config()
        factory = CacheFactory()
        _cache = await factory.create_cache_from_config(config)
        
        logger.info(f"✅ Cache initialized successfully with {preset_name} preset")
        logger.info(f"Cache type: {type(_cache).__name__}")
        
        # Store cache reference in app state
        app.state.cache = _cache
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache: {e}")
        yield
    
    finally:
        # Cleanup
        if _cache and hasattr(_cache, 'disconnect'):
            try:
                await _cache.disconnect()
                logger.info("Cache disconnected successfully")
            except Exception as e:
                logger.warning(f"Error disconnecting cache: {e}")

# FastAPI app
app = FastAPI(
    title="Simple Web App Cache Example",
    description="Demonstrates cache presets for simple web applications",
    version="1.0.0",
    lifespan=lifespan
)

# Mock user database
MOCK_USERS = {
    123: User(id=123, name="John Doe", email="john@example.com", last_seen=datetime.now()),
    456: User(id=456, name="Jane Smith", email="jane@example.com", last_seen=datetime.now() - timedelta(hours=2)),
    789: User(id=789, name="Bob Johnson", email="bob@example.com", last_seen=datetime.now() - timedelta(days=1))
}

async def get_cache() -> CacheInterface:
    """Get cache instance from app state"""
    if not hasattr(app.state, 'cache') or app.state.cache is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service not available"
        )
    return app.state.cache

@app.get("/")
async def root():
    """Root endpoint"""
    preset_name = os.getenv("CACHE_PRESET", "development")
    return {
        "message": "Simple Web App Cache Example",
        "preset": preset_name,
        "endpoints": {
            "users": "/user/{user_id}",
            "cache_info": "/cache/info",
            "cache_clear": "/cache/clear"
        },
        "example_usage": [
            "curl http://localhost:8081/user/123",
            "curl http://localhost:8081/cache/info"
        ]
    }

@app.get("/user/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Get user by ID with caching
    
    Demonstrates basic cache usage patterns:
    - Cache hit: Return cached data instantly
    - Cache miss: Fetch from database, cache result
    """
    cache = await get_cache()
    cache_key = f"user:{user_id}"
    
    # Try to get from cache first
    cached_user = await cache.get(cache_key)
    if cached_user:
        logger.info(f"Cache HIT for user {user_id}")
        return User.model_validate(cached_user)
    
    # Cache miss - fetch from "database"
    logger.info(f"Cache MISS for user {user_id}")
    
    if user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    user = MOCK_USERS[user_id]
    
    # Cache the result
    # TTL determined by preset configuration
    await cache.set(cache_key, user.model_dump())
    logger.info(f"Cached user {user_id}")
    
    return user

@app.get("/users/active", response_model=Dict[str, Any])
async def get_active_users():
    """
    Get list of recently active users with caching
    
    Demonstrates caching complex queries
    """
    cache = await get_cache()
    cache_key = "users:active"
    
    # Check cache first
    cached_result = await cache.get(cache_key)
    if cached_result:
        logger.info("Cache HIT for active users list")
        return cached_result
    
    # Cache miss - compute active users
    logger.info("Cache MISS for active users list")
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    active_users = [
        {"id": user.id, "name": user.name, "last_seen": user.last_seen.isoformat()}
        for user in MOCK_USERS.values()
        if user.last_seen > cutoff_time
    ]
    
    result = {
        "active_users": active_users,
        "count": len(active_users),
        "generated_at": datetime.now().isoformat(),
        "cutoff_time": cutoff_time.isoformat()
    }
    
    # Cache for 5 minutes (TTL determined by preset)
    await cache.set(cache_key, result, ttl=300)
    logger.info("Cached active users list")
    
    return result

@app.get("/cache/info", response_model=CacheInfo)
async def cache_info():
    """
    Get cache information and statistics
    
    Shows current preset configuration and performance
    """
    cache = await get_cache()
    preset_name = os.getenv("CACHE_PRESET", "development")
    
    try:
        # Get basic cache info
        cache_type = type(cache).__name__
        
        # Try to get performance stats if available
        performance_stats = {}
        hit_ratio = None
        
        if hasattr(cache, '_performance_monitor') and cache._performance_monitor:
            monitor = cache._performance_monitor
            if hasattr(monitor, 'get_performance_summary'):
                performance_stats = monitor.get_performance_summary()
            if hasattr(monitor, 'get_cache_hit_ratio'):
                hit_ratio = monitor.get_cache_hit_ratio()
        
        # Count total keys (if supported)
        total_keys = 0
        if hasattr(cache, 'get_active_keys'):
            try:
                active_keys = await cache.get_active_keys()
                total_keys = len(active_keys)
            except Exception:
                total_keys = 0
        
        return CacheInfo(
            preset_used=preset_name,
            cache_type=cache_type,
            total_keys=total_keys,
            hit_ratio=hit_ratio,
            performance_stats=performance_stats
        )
        
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return CacheInfo(
            preset_used=preset_name,
            cache_type="error",
            total_keys=0,
            performance_stats={"error": str(e)}
        )

@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    cache = await get_cache()
    
    try:
        if hasattr(cache, 'clear'):
            await cache.clear()
            message = "Cache cleared successfully"
        else:
            # Manual cleanup for caches without clear method
            if hasattr(cache, 'get_active_keys'):
                keys = await cache.get_active_keys()
                for key in keys:
                    await cache.delete(key)
                message = f"Manually cleared {len(keys)} cache entries"
            else:
                message = "Cache clear not supported by this cache type"
        
        logger.info(message)
        return {"success": True, "message": message}
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return {"success": False, "message": f"Clear failed: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check with cache status"""
    try:
        cache = await get_cache()
        
        # Test cache connectivity
        test_key = "_health_check"
        await cache.set(test_key, "ok", ttl=1)
        result = await cache.get(test_key)
        await cache.delete(test_key)
        
        cache_healthy = result == "ok"
        
        return {
            "status": "healthy" if cache_healthy else "degraded",
            "cache_status": {
                "healthy": cache_healthy,
                "type": type(cache).__name__,
                "preset": os.getenv("CACHE_PRESET", "development")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "cache_status": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run the simple web app example"""
    preset_name = os.getenv("CACHE_PRESET", "development")
    print(f"🚀 Starting Simple Web App with {preset_name} preset")
    print("📖 API docs: http://localhost:8081/docs")
    print("🔍 Health: http://localhost:8081/health")
    print("👤 User example: http://localhost:8081/user/123")
    print("📊 Cache info: http://localhost:8081/cache/info")
    print()
    
    preset_tips = {
        "development": "💡 Perfect for local development with debug features",
        "simple": "💡 Ideal for small applications and quick prototypes",
        "production": "💡 High-performance settings for production web apps"
    }
    
    if preset_name in preset_tips:
        print(preset_tips[preset_name])
    
    print()
    print("💡 Try different presets:")
    print("   export CACHE_PRESET=simple && python ... (lightweight)")
    print("   export CACHE_PRESET=development && python ... (debug features)")
    print()
    
    # Run the application
    uvicorn.run(
        "preset_scenarios_simple_webapp:app",
        host="0.0.0.0",
        port=8081,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()