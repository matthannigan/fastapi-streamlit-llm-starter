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


class CacheKeyGenerator:
    """Optimized cache key generator for handling large texts efficiently."""
    
    def __init__(self, text_hash_threshold: int = 1000, hash_algorithm=hashlib.sha256):
        """
        Initialize CacheKeyGenerator with configurable parameters.
        
        Args:
            text_hash_threshold: Character count threshold above which text is hashed
            hash_algorithm: Hash algorithm to use (default: SHA256)
        """
        self.text_hash_threshold = text_hash_threshold
        self.hash_algorithm = hash_algorithm
    
    def _hash_text_efficiently(self, text: str) -> str:
        """
        Efficiently hash text using streaming approach for large texts.
        
        Args:
            text: Input text to process
            
        Returns:
            Either the original text (if short) or a hash representation
        """
        if len(text) <= self.text_hash_threshold:
            # For short texts, use text directly to maintain readability in cache keys
            return text.replace("|", "_").replace(":", "_")  # Sanitize special chars
        
        # For large texts, hash efficiently with metadata for uniqueness
        hasher = self.hash_algorithm()
        
        # Add text content in chunks to reduce memory usage
        hasher.update(text.encode('utf-8'))
        
        # Add text metadata for uniqueness and debugging
        hasher.update(f"len:{len(text)}".encode('utf-8'))
        hasher.update(f"words:{len(text.split())}".encode('utf-8'))
        
        # Return shorter hash for efficiency (16 chars should be sufficient for uniqueness)
        return f"hash:{hasher.hexdigest()[:16]}"
    
    def generate_cache_key(
        self, 
        text: str, 
        operation: str, 
        options: Dict[str, Any], 
        question: Optional[str] = None
    ) -> str:
        """
        Generate optimized cache key with efficient text handling.
        
        Args:
            text: Input text content
            operation: Operation type (summarize, sentiment, etc.)
            options: Operation options dictionary
            question: Optional question for Q&A operations
            
        Returns:
            Optimized cache key string
        """
        # Hash text efficiently
        text_identifier = self._hash_text_efficiently(text)
        
        # Create lightweight cache components
        cache_components = [
            f"op:{operation}",
            f"txt:{text_identifier}"
        ]
        
        # Add options efficiently
        if options:
            # Sort and format options more efficiently than JSON serialization
            opts_str = "&".join(f"{k}={v}" for k, v in sorted(options.items()))
            # Use shorter MD5 hash for options since they're typically small
            opts_hash = hashlib.md5(opts_str.encode()).hexdigest()[:8]
            cache_components.append(f"opts:{opts_hash}")
        
        # Add question if present
        if question:
            # Hash question for privacy and efficiency
            q_hash = hashlib.md5(question.encode()).hexdigest()[:8]
            cache_components.append(f"q:{q_hash}")
        
        # Combine components efficiently using pipe separator
        cache_key = "ai_cache:" + "|".join(cache_components)
        
        return cache_key

class AIResponseCache:
    def __init__(self, redis_url: str = "redis://redis:6379", default_ttl: int = 3600, 
                 text_hash_threshold: int = 1000, hash_algorithm=hashlib.sha256):
        """
        Initialize AIResponseCache with injectable configuration.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cache entries in seconds
            text_hash_threshold: Character count threshold for text hashing
            hash_algorithm: Hash algorithm to use for large texts
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
        
        # Initialize optimized cache key generator
        self.key_generator = CacheKeyGenerator(
            text_hash_threshold=text_hash_threshold,
            hash_algorithm=hash_algorithm
        )
        
        # Tiered caching configuration
        self.text_size_tiers = {
            'small': 500,      # < 500 chars - cache with full text and use memory cache
            'medium': 5000,    # 500-5000 chars - cache with text hash
            'large': 50000,    # 5000-50000 chars - cache with content hash + metadata
        }
        
        # In-memory cache for frequently accessed small items
        self.memory_cache = {}  # Cache storage: {key: value}
        self.memory_cache_size = 100  # Maximum number of items in memory cache
        self.memory_cache_order = []  # Track access order for FIFO eviction
    
    def _get_text_tier(self, text: str) -> str:
        """
        Determine caching tier based on text size.
        
        Args:
            text: Input text to categorize
            
        Returns:
            Tier name: 'small', 'medium', 'large', or 'xlarge'
        """
        text_len = len(text)
        if text_len < self.text_size_tiers['small']:
            return 'small'
        elif text_len < self.text_size_tiers['medium']:
            return 'medium'
        elif text_len < self.text_size_tiers['large']:
            return 'large'
        else:
            return 'xlarge'
    
    def _update_memory_cache(self, key: str, value: Dict[str, Any]):
        """
        Update memory cache with simple FIFO eviction.
        
        Args:
            key: Cache key
            value: Cache value to store
        """
        # If key already exists, remove it from order list first
        if key in self.memory_cache:
            self.memory_cache_order.remove(key)
        
        # Check if we need to evict oldest item (FIFO)
        if len(self.memory_cache) >= self.memory_cache_size:
            # Remove oldest item
            oldest_key = self.memory_cache_order.pop(0)
            del self.memory_cache[oldest_key]
            logger.debug(f"Evicted oldest memory cache entry: {oldest_key}")
        
        # Add new item
        self.memory_cache[key] = value
        self.memory_cache_order.append(key)
        logger.debug(f"Added to memory cache: {key}")
    
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
        """Generate optimized cache key using CacheKeyGenerator."""
        return self.key_generator.generate_cache_key(text, operation, options, question)
    
    async def get_cached_response(self, text: str, operation: str, options: Dict[str, Any], question: str = None) -> Optional[Dict[str, Any]]:
        """
        Multi-tier cache retrieval with memory cache optimization for small texts.
        
        Args:
            text: Input text content
            operation: Operation type
            options: Operation options
            question: Optional question for Q&A operations
            
        Returns:
            Cached response if found, None otherwise
        """
        tier = self._get_text_tier(text)
        cache_key = self._generate_cache_key(text, operation, options, question)
        
        # Check memory cache first for small items
        if tier == 'small' and cache_key in self.memory_cache:
            logger.debug(f"Memory cache hit for {operation} (tier: {tier})")
            return self.memory_cache[cache_key]
        
        # Check Redis cache
        if not await self.connect():
            return None
            
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                
                # Populate memory cache for small items on Redis hit
                if tier == 'small':
                    self._update_memory_cache(cache_key, result)
                
                logger.debug(f"Redis cache hit for {operation} (tier: {tier})")
                return result
                
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
        """Get cache statistics including memory cache info."""
        redis_stats = {"status": "unavailable", "keys": 0}
        
        if await self.connect():
            try:
                keys = await self.redis.keys("ai_cache:*")
                info = await self.redis.info()
                redis_stats = {
                    "status": "connected",
                    "keys": len(keys),
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            except Exception as e:
                logger.warning(f"Cache stats error: {e}")
                redis_stats = {"status": "error", "error": str(e)}
        
        # Add memory cache statistics
        memory_stats = {
            "memory_cache_entries": len(self.memory_cache),
            "memory_cache_size_limit": self.memory_cache_size,
            "memory_cache_utilization": f"{len(self.memory_cache)}/{self.memory_cache_size}"
        }
        
        return {
            "redis": redis_stats,
            "memory": memory_stats
        }