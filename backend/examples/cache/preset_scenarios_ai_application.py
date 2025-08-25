#!/usr/bin/env python3
"""
AI Application Cache Example with AI-Optimized Presets

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
"""

import asyncio
import hashlib
import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Cache infrastructure
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory, CacheInterface

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI operation models
class AIRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text to process")
    options: Optional[Dict[str, Any]] = Field(default={}, description="Processing options")

class SummarizeRequest(AIRequest):
    max_length: Optional[int] = Field(default=100, description="Maximum summary length")
    style: Optional[str] = Field(default="concise", description="Summary style")

class SentimentRequest(AIRequest):
    include_confidence: Optional[bool] = Field(default=True, description="Include confidence score")

class AIResponse(BaseModel):
    operation: str
    result: Any
    cached: bool = False
    processing_time_ms: Optional[float] = None
    cache_key: Optional[str] = None
    text_hash: Optional[str] = None

class CacheStats(BaseModel):
    preset_used: str
    total_operations: int
    cache_hits: int
    cache_misses: int
    hit_ratio: float
    ai_specific_stats: Dict[str, Any]
    performance_summary: Dict[str, Any] = {}

# Global cache instance
_cache: Optional[CacheInterface] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with AI-optimized cache initialization"""
    global _cache
    
    preset_name = os.getenv("CACHE_PRESET", "ai-development")
    logger.info(f"🤖 Starting AI application with {preset_name} preset")
    
    if not preset_name.startswith("ai-"):
        logger.warning(f"⚠️  Using non-AI preset '{preset_name}' for AI application. Consider ai-development or ai-production")
    
    try:
        # Load AI-optimized preset configuration
        config = get_cache_config()
        factory = CacheFactory()
        _cache = await factory.create_cache_from_config(config)
        
        logger.info(f"✅ AI cache initialized with {preset_name} preset")
        logger.info(f"Cache type: {type(_cache).__name__}")
        
        # Log AI-specific features
        if hasattr(_cache, '_text_hash_threshold'):
            logger.info(f"Text hashing threshold: {_cache._text_hash_threshold} chars")
        if hasattr(_cache, '_operation_ttls'):
            logger.info(f"Operation TTLs: {getattr(_cache, '_operation_ttls', {})}")
        
        # Store cache reference in app state
        app.state.cache = _cache
        app.state.operation_stats = {
            "total_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "operations": {}
        }
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI cache: {e}")
        yield
    
    finally:
        # Cleanup
        if _cache and hasattr(_cache, 'disconnect'):
            try:
                await _cache.disconnect()
                logger.info("AI cache disconnected successfully")
            except Exception as e:
                logger.warning(f"Error disconnecting AI cache: {e}")

# FastAPI app
app = FastAPI(
    title="AI Application Cache Example",
    description="Demonstrates AI-optimized cache presets for text processing",
    version="1.0.0",
    lifespan=lifespan
)

async def get_cache() -> CacheInterface:
    """Get AI cache instance from app state"""
    if not hasattr(app.state, 'cache') or app.state.cache is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI cache service not available"
        )
    return app.state.cache

def update_operation_stats(operation: str, cache_hit: bool):
    """Update operation statistics"""
    if not hasattr(app.state, 'operation_stats'):
        return
    
    stats = app.state.operation_stats
    stats["total_operations"] += 1
    
    if cache_hit:
        stats["cache_hits"] += 1
    else:
        stats["cache_misses"] += 1
    
    if operation not in stats["operations"]:
        stats["operations"][operation] = {"hits": 0, "misses": 0}
    
    if cache_hit:
        stats["operations"][operation]["hits"] += 1
    else:
        stats["operations"][operation]["misses"] += 1

def generate_ai_cache_key(operation: str, text: str, options: Dict[str, Any] = None) -> tuple[str, str]:
    """
    Generate cache key for AI operations with text hashing
    
    Returns:
        tuple: (cache_key, text_hash)
    """
    # Create text hash for large texts (mimics AI cache behavior)
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    
    # Include options in cache key
    options_str = ""
    if options:
        # Sort options for consistent cache keys
        sorted_options = sorted(options.items())
        options_str = "_".join(f"{k}:{v}" for k, v in sorted_options)
        options_hash = hashlib.md5(options_str.encode()).hexdigest()[:8]
        options_str = f"_{options_hash}"
    
    # Use text directly for short texts, hash for long texts
    if len(text) <= 1000:  # Threshold similar to AI cache presets
        cache_key = f"ai:{operation}:{text[:50]}{options_str}"
    else:
        cache_key = f"ai:{operation}:{text_hash}{options_str}"
    
    return cache_key, text_hash

async def mock_ai_processing(operation: str, text: str, options: Dict[str, Any] = None) -> Any:
    """
    Mock AI processing (replace with real AI service calls)
    
    Simulates processing time based on text length
    """
    await asyncio.sleep(min(len(text) / 10000, 2.0))  # Simulate processing time
    
    if operation == "summarize":
        max_length = options.get("max_length", 100) if options else 100
        words = text.split()[:max_length//10]  # Rough word limit
        return {
            "summary": " ".join(words) + "...",
            "original_length": len(text),
            "summary_length": len(" ".join(words)),
            "compression_ratio": len(" ".join(words)) / len(text)
        }
    
    elif operation == "sentiment":
        # Mock sentiment analysis
        positive_words = ["good", "great", "excellent", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.9, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative" 
            confidence = min(0.9, 0.5 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.6
        
        result = {"sentiment": sentiment}
        if options and options.get("include_confidence", True):
            result["confidence"] = confidence
            
        return result
    
    elif operation == "key_points":
        # Mock key point extraction
        sentences = text.split(". ")[:5]  # First 5 sentences as key points
        return {
            "key_points": [f"• {sentence.strip()}" for sentence in sentences if sentence.strip()],
            "total_points": len(sentences)
        }
    
    else:
        return {"processed_text": text[:200], "operation": operation}

@app.get("/")
async def root():
    """Root endpoint"""
    preset_name = os.getenv("CACHE_PRESET", "ai-development")
    return {
        "message": "AI Application Cache Example",
        "preset": preset_name,
        "ai_features": preset_name.startswith("ai-"),
        "endpoints": {
            "summarize": "/ai/summarize",
            "sentiment": "/ai/sentiment", 
            "key_points": "/ai/key-points",
            "cache_stats": "/ai/cache/stats",
            "cache_clear": "/ai/cache/clear"
        },
        "example_usage": [
            'curl -X POST http://localhost:8082/ai/summarize -H "Content-Type: application/json" -d \'{"text":"Long text to summarize..."}\'',
            'curl http://localhost:8082/ai/cache/stats'
        ]
    }

@app.post("/ai/summarize", response_model=AIResponse)
async def summarize_text(request: SummarizeRequest):
    """
    Summarize text with AI-optimized caching
    
    Demonstrates AI cache with operation-specific TTLs
    """
    start_time = datetime.now()
    cache = await get_cache()
    
    # Generate AI-optimized cache key
    options = {"max_length": request.max_length, "style": request.style}
    cache_key, text_hash = generate_ai_cache_key("summarize", request.text, options)
    
    # Try to get from cache first
    cached_result = await cache.get(cache_key)
    if cached_result:
        update_operation_stats("summarize", cache_hit=True)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Cache HIT for summarize operation (key: {cache_key[:32]}...)")
        
        return AIResponse(
            operation="summarize",
            result=cached_result,
            cached=True,
            processing_time_ms=processing_time,
            cache_key=cache_key,
            text_hash=text_hash
        )
    
    # Cache miss - process with AI
    update_operation_stats("summarize", cache_hit=False)
    logger.info(f"Cache MISS for summarize operation (key: {cache_key[:32]}...)")
    
    # Mock AI processing
    result = await mock_ai_processing("summarize", request.text, options)
    
    # Cache the result (TTL determined by ai-development/ai-production preset)
    await cache.set(cache_key, result)
    
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    logger.info(f"Cached summarize result for {len(request.text)} chars of text")
    
    return AIResponse(
        operation="summarize",
        result=result,
        cached=False,
        processing_time_ms=processing_time,
        cache_key=cache_key,
        text_hash=text_hash
    )

@app.post("/ai/sentiment", response_model=AIResponse)
async def analyze_sentiment(request: SentimentRequest):
    """Analyze text sentiment with AI-optimized caching"""
    start_time = datetime.now()
    cache = await get_cache()
    
    options = {"include_confidence": request.include_confidence}
    cache_key, text_hash = generate_ai_cache_key("sentiment", request.text, options)
    
    # Check cache
    cached_result = await cache.get(cache_key)
    if cached_result:
        update_operation_stats("sentiment", cache_hit=True)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Cache HIT for sentiment analysis")
        
        return AIResponse(
            operation="sentiment",
            result=cached_result,
            cached=True,
            processing_time_ms=processing_time,
            cache_key=cache_key,
            text_hash=text_hash
        )
    
    # Process and cache
    update_operation_stats("sentiment", cache_hit=False)
    result = await mock_ai_processing("sentiment", request.text, options)
    await cache.set(cache_key, result)
    
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    logger.info(f"Processed and cached sentiment analysis")
    
    return AIResponse(
        operation="sentiment",
        result=result,
        cached=False,
        processing_time_ms=processing_time,
        cache_key=cache_key,
        text_hash=text_hash
    )

@app.post("/ai/key-points", response_model=AIResponse)
async def extract_key_points(request: AIRequest):
    """Extract key points from text with AI-optimized caching"""
    start_time = datetime.now()
    cache = await get_cache()
    
    cache_key, text_hash = generate_ai_cache_key("key_points", request.text, request.options)
    
    # Check cache
    cached_result = await cache.get(cache_key)
    if cached_result:
        update_operation_stats("key_points", cache_hit=True)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return AIResponse(
            operation="key_points",
            result=cached_result,
            cached=True,
            processing_time_ms=processing_time,
            cache_key=cache_key,
            text_hash=text_hash
        )
    
    # Process and cache
    update_operation_stats("key_points", cache_hit=False)
    result = await mock_ai_processing("key_points", request.text, request.options)
    await cache.set(cache_key, result)
    
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return AIResponse(
        operation="key_points",
        result=result,
        cached=False,
        processing_time_ms=processing_time,
        cache_key=cache_key,
        text_hash=text_hash
    )

@app.get("/ai/cache/stats", response_model=CacheStats)
async def get_ai_cache_stats():
    """Get AI cache statistics and performance metrics"""
    cache = await get_cache()
    preset_name = os.getenv("CACHE_PRESET", "ai-development")
    
    # Get operation stats
    stats = getattr(app.state, 'operation_stats', {
        "total_operations": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "operations": {}
    })
    
    hit_ratio = 0.0
    if stats["total_operations"] > 0:
        hit_ratio = stats["cache_hits"] / stats["total_operations"]
    
    # Get AI-specific cache stats
    ai_specific_stats = {
        "text_hashing_enabled": hasattr(cache, '_text_hash_threshold'),
        "operation_ttls_configured": hasattr(cache, '_operation_ttls'),
        "compression_enabled": hasattr(cache, '_compression_threshold'),
        "ai_optimizations": preset_name.startswith("ai-")
    }
    
    if hasattr(cache, '_text_hash_threshold'):
        ai_specific_stats["text_hash_threshold"] = getattr(cache, '_text_hash_threshold', 1000)
    
    # Get performance summary if available
    performance_summary = {}
    if hasattr(cache, '_performance_monitor') and cache._performance_monitor:
        monitor = cache._performance_monitor
        if hasattr(monitor, 'get_performance_summary'):
            performance_summary = monitor.get_performance_summary()
    
    return CacheStats(
        preset_used=preset_name,
        total_operations=stats["total_operations"],
        cache_hits=stats["cache_hits"],
        cache_misses=stats["cache_misses"],
        hit_ratio=hit_ratio,
        ai_specific_stats=ai_specific_stats,
        performance_summary=performance_summary
    )

@app.delete("/ai/cache/clear")
async def clear_ai_cache():
    """Clear AI cache and reset statistics"""
    cache = await get_cache()
    
    try:
        # Clear cache
        if hasattr(cache, 'clear'):
            await cache.clear()
            message = "AI cache cleared successfully"
        else:
            # Manual cleanup for AI-related keys
            if hasattr(cache, 'get_active_keys'):
                keys = await cache.get_active_keys()
                ai_keys = [key for key in keys if key.startswith('ai:')]
                for key in ai_keys:
                    await cache.delete(key)
                message = f"Cleared {len(ai_keys)} AI cache entries"
            else:
                message = "Cache clear not supported"
        
        # Reset stats
        if hasattr(app.state, 'operation_stats'):
            app.state.operation_stats = {
                "total_operations": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "operations": {}
            }
        
        logger.info(message)
        return {"success": True, "message": message}
        
    except Exception as e:
        logger.error(f"AI cache clear failed: {e}")
        return {"success": False, "message": f"Clear failed: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check for AI application"""
    try:
        cache = await get_cache()
        
        # Test AI cache with representative operation
        test_key = "ai:health_check:test"
        test_data = {"status": "ok", "timestamp": datetime.now().isoformat()}
        
        await cache.set(test_key, test_data, ttl=5)
        result = await cache.get(test_key)
        await cache.delete(test_key)
        
        cache_healthy = result is not None
        
        return {
            "status": "healthy" if cache_healthy else "degraded",
            "ai_cache_status": {
                "healthy": cache_healthy,
                "type": type(cache).__name__,
                "preset": os.getenv("CACHE_PRESET", "ai-development"),
                "ai_optimized": os.getenv("CACHE_PRESET", "").startswith("ai-")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "ai_cache_status": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run the AI application example"""
    preset_name = os.getenv("CACHE_PRESET", "ai-development")
    print(f"🤖 Starting AI Application with {preset_name} preset")
    print("📖 API docs: http://localhost:8082/docs")
    print("🔍 Health: http://localhost:8082/health")
    print("📝 Summarize: http://localhost:8082/ai/summarize")
    print("💭 Sentiment: http://localhost:8082/ai/sentiment") 
    print("📊 Cache stats: http://localhost:8082/ai/cache/stats")
    print()
    
    if not preset_name.startswith("ai-"):
        print(f"⚠️  WARNING: Using '{preset_name}' preset for AI application")
        print("💡 Consider using ai-development or ai-production for optimal AI performance")
    else:
        preset_tips = {
            "ai-development": "💡 AI development preset with debug features and shorter TTLs",
            "ai-production": "💡 AI production preset with optimized performance and longer TTLs"
        }
        if preset_name in preset_tips:
            print(preset_tips[preset_name])
    
    print()
    print("💡 Try different AI presets:")
    print("   export CACHE_PRESET=ai-development && python ... (AI development)")
    print("   export CACHE_PRESET=ai-production && python ... (AI production)")
    print()
    print("🧪 Example requests:")
    print('   curl -X POST http://localhost:8082/ai/summarize -H "Content-Type: application/json" \\')
    print('        -d \'{"text":"This is a long text that needs summarizing...","max_length":50}\'')
    print()
    
    # Run the application
    uvicorn.run(
        "preset_scenarios_ai_application:app",
        host="0.0.0.0",
        port=8082,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()