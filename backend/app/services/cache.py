import hashlib
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Optional Redis import for graceful degradation
try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)

class AIResponseCache:
    def __init__(self, redis_url: str = "redis://redis:6379", default_ttl: int = 3600):
        """
        Initialize AIResponseCache with injectable configuration.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cache entries in seconds
        """
        self.redis = None
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.operation_ttls = {
            "summarize": 7200,    # 2 hours - summaries are stable
            "sentiment": 86400,   # 24 hours - sentiment rarely changes
            "key_points": 7200,   # 2 hours
            "questions": 3600,    # 1 hour - questions can vary
            "qa": 1800           # 30 minutes - context-dependent
        }
    
    async def connect(self):
        """Initialize Redis connection with graceful degradation."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return False
            
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self.redis.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
                return True
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - caching disabled")
                self.redis = None
                return False
        return True
    
    def _generate_cache_key(self, text: str, operation: str, options: Dict[str, Any], question: str = None) -> str:
        """Generate consistent cache key for request."""
        cache_data = {
            "text": text,
            "operation": operation,
            "options": sorted(options.items()) if options else [],
            "question": question
        }
        content = json.dumps(cache_data, sort_keys=True)
        return f"ai_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_cached_response(self, text: str, operation: str, options: Dict[str, Any], question: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached AI response if available."""
        if not await self.connect():
            return None
            
        cache_key = self._generate_cache_key(text, operation, options, question)
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for operation {operation}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def cache_response(self, text: str, operation: str, options: Dict[str, Any], response: Dict[str, Any], question: str = None):
        """Cache AI response with appropriate TTL."""
        if not await self.connect():
            return
            
        cache_key = self._generate_cache_key(text, operation, options, question)
        ttl = self.operation_ttls.get(operation, self.default_ttl)
        
        try:
            # Add cache metadata
            cached_response = {
                **response,
                "cached_at": datetime.now().isoformat(),
                "cache_hit": True
            }
            
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cached_response, default=str)
            )
            logger.debug(f"Cached response for operation {operation} with TTL {ttl}s")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        if not await self.connect():
            return
            
        try:
            keys = await self.redis.keys(f"ai_cache:*{pattern}*")
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not await self.connect():
            return {"status": "unavailable", "keys": 0}
            
        try:
            keys = await self.redis.keys("ai_cache:*")
            info = await self.redis.info()
            return {
                "status": "connected",
                "keys": len(keys),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}