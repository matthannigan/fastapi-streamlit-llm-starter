import hashlib
import json
import asyncio
import logging
import zlib
import pickle
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Optional Redis import for graceful degradation
try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

from .monitoring import CachePerformanceMonitor

logger = logging.getLogger(__name__)


class CacheKeyGenerator:
    """Optimized cache key generator for handling large texts efficiently."""
    
    def __init__(self, text_hash_threshold: int = 1000, hash_algorithm=hashlib.sha256, 
                 performance_monitor: Optional[CachePerformanceMonitor] = None):
        """
        Initialize CacheKeyGenerator with configurable parameters.
        
        Args:
            text_hash_threshold: Character count threshold above which text is hashed
            hash_algorithm: Hash algorithm to use (default: SHA256)
            performance_monitor: Optional performance monitor for tracking key generation timing
        """
        self.text_hash_threshold = text_hash_threshold
        self.hash_algorithm = hash_algorithm
        self.performance_monitor = performance_monitor
    
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
        start_time = time.time()
        
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
        
        # Record key generation performance if monitor is available
        if self.performance_monitor:
            duration = time.time() - start_time
            self.performance_monitor.record_key_generation_time(
                duration=duration,
                text_length=len(text),
                operation_type=operation,
                additional_data={
                    "text_tier": "large" if len(text) > self.text_hash_threshold else "small",
                    "has_options": bool(options),
                    "has_question": bool(question)
                }
            )
        
        return cache_key

class AIResponseCache:
    def __init__(self, redis_url: str = "redis://redis:6379", default_ttl: int = 3600, 
                 text_hash_threshold: int = 1000, hash_algorithm=hashlib.sha256,
                 compression_threshold: int = 1000, compression_level: int = 6,
                 performance_monitor: Optional[CachePerformanceMonitor] = None):
        """
        Initialize AIResponseCache with injectable configuration.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cache entries in seconds
            text_hash_threshold: Character count threshold for text hashing
            hash_algorithm: Hash algorithm to use for large texts
            compression_threshold: Size threshold in bytes for compressing cache data
            compression_level: Compression level (1-9, where 9 is highest compression)
            performance_monitor: Optional performance monitor for tracking cache metrics
        """
        self.redis = None
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level
        self.operation_ttls = {
            "summarize": 7200,    # 2 hours - summaries are stable
            "sentiment": 86400,   # 24 hours - sentiment rarely changes
            "key_points": 7200,   # 2 hours
            "questions": 3600,    # 1 hour - questions can vary
            "qa": 1800           # 30 minutes - context-dependent
        }
        
        # Initialize performance monitor (create default if not provided)
        self.performance_monitor = performance_monitor or CachePerformanceMonitor()
        
        # Initialize optimized cache key generator with performance monitoring
        self.key_generator = CacheKeyGenerator(
            text_hash_threshold=text_hash_threshold,
            hash_algorithm=hash_algorithm,
            performance_monitor=self.performance_monitor
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
    
    def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """
        Compress cache data for large responses using pickle and zlib.
        
        Args:
            data: Cache data to compress
            
        Returns:
            Compressed bytes with appropriate prefix
        """
        # Use pickle for Python objects, then compress
        pickled_data = pickle.dumps(data)
        
        if len(pickled_data) > self.compression_threshold:
            compressed = zlib.compress(pickled_data, self.compression_level)
            logger.debug(f"Compressed cache data: {len(pickled_data)} -> {len(compressed)} bytes")
            return b"compressed:" + compressed
        
        return b"raw:" + pickled_data
    
    def _decompress_data(self, data: bytes) -> Dict[str, Any]:
        """
        Decompress cache data using zlib and pickle.
        
        Args:
            data: Compressed bytes to decompress
            
        Returns:
            Decompressed cache data dictionary
        """
        if data.startswith(b"compressed:"):
            compressed_data = data[11:]  # Remove "compressed:" prefix
            pickled_data = zlib.decompress(compressed_data)
        else:
            pickled_data = data[4:]  # Remove "raw:" prefix
        
        return pickle.loads(pickled_data)
    
    async def connect(self):
        """Initialize Redis connection with graceful degradation."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return False
            
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    decode_responses=False,  # Handle binary data for compression
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
        Includes comprehensive performance monitoring for cache hit ratio tracking.
        
        Args:
            text: Input text content
            operation: Operation type
            options: Operation options
            question: Optional question for Q&A operations
            
        Returns:
            Cached response if found, None otherwise
        """
        start_time = time.time()
        tier = self._get_text_tier(text)
        cache_key = self._generate_cache_key(text, operation, options, question)
        
        # Check memory cache first for small items
        if tier == 'small' and cache_key in self.memory_cache:
            duration = time.time() - start_time
            logger.debug(f"Memory cache hit for {operation} (tier: {tier})")
            
            # Record cache hit for memory cache
            self.performance_monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=True,
                text_length=len(text),
                additional_data={
                    "cache_tier": "memory",
                    "text_tier": tier,
                    "operation_type": operation
                }
            )
            
            return self.memory_cache[cache_key]
        
        # Check Redis cache
        if not await self.connect():
            duration = time.time() - start_time
            
            # Record cache miss due to Redis unavailability
            self.performance_monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=False,
                text_length=len(text),
                additional_data={
                    "cache_tier": "redis_unavailable",
                    "text_tier": tier,
                    "operation_type": operation,
                    "reason": "redis_connection_failed"
                }
            )
            
            return None
            
        try:
            cached_data = await self.redis.get(cache_key)
            duration = time.time() - start_time
            
            if cached_data:
                # Handle both compressed binary data and legacy JSON format
                if isinstance(cached_data, bytes) and (cached_data.startswith(b"compressed:") or cached_data.startswith(b"raw:")):
                    # New compressed format
                    result = self._decompress_data(cached_data)
                elif isinstance(cached_data, bytes):
                    # Legacy binary JSON format
                    result = json.loads(cached_data.decode('utf-8'))
                else:
                    # Legacy string JSON format (for tests/mock Redis)
                    result = json.loads(cached_data)
                
                # Populate memory cache for small items on Redis hit
                if tier == 'small':
                    self._update_memory_cache(cache_key, result)
                
                logger.debug(f"Redis cache hit for {operation} (tier: {tier})")
                
                # Record cache hit for Redis
                self.performance_monitor.record_cache_operation_time(
                    operation="get",
                    duration=duration,
                    cache_hit=True,
                    text_length=len(text),
                    additional_data={
                        "cache_tier": "redis",
                        "text_tier": tier,
                        "operation_type": operation,
                        "populated_memory_cache": tier == 'small'
                    }
                )
                
                return result
            else:
                # Record cache miss for Redis
                self.performance_monitor.record_cache_operation_time(
                    operation="get",
                    duration=duration,
                    cache_hit=False,
                    text_length=len(text),
                    additional_data={
                        "cache_tier": "redis",
                        "text_tier": tier,
                        "operation_type": operation,
                        "reason": "key_not_found"
                    }
                )
                
        except Exception as e:
            duration = time.time() - start_time
            logger.warning(f"Cache retrieval error: {e}")
            
            # Record cache miss due to error
            self.performance_monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=False,
                text_length=len(text),
                additional_data={
                    "cache_tier": "redis",
                    "text_tier": tier,
                    "operation_type": operation,
                    "reason": "redis_error",
                    "error": str(e)
                }
            )
        
        return None
    
    async def cache_response(self, text: str, operation: str, options: Dict[str, Any], response: Dict[str, Any], question: str = None):
        """Cache AI response with compression for large data and appropriate TTL."""
        if not await self.connect():
            return
            
        cache_key = self._generate_cache_key(text, operation, options, question)
        ttl = self.operation_ttls.get(operation, self.default_ttl)
        
        try:
            # Check if compression will be used
            response_size = len(str(response))
            will_compress = response_size > self.compression_threshold
            
            # Add cache metadata including compression information
            cached_response = {
                **response,
                "cached_at": datetime.now().isoformat(),
                "cache_hit": True,
                "text_length": len(text),
                "compression_used": will_compress
            }
            
            # Compress data if beneficial
            cache_data = self._compress_data(cached_response)
            
            await self.redis.setex(cache_key, ttl, cache_data)
            
            logger.debug(f"Cached response for {operation} (size: {len(cache_data)} bytes, compression: {will_compress})")
            
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        if not await self.connect():
            return
            
        try:
            keys = await self.redis.keys(f"ai_cache:*{pattern}*".encode('utf-8'))
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics including memory cache info and performance metrics."""
        redis_stats = {"status": "unavailable", "keys": 0}
        
        if await self.connect():
            try:
                keys = await self.redis.keys(b"ai_cache:*")
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
        
        # Add performance statistics
        performance_stats = self.performance_monitor.get_performance_stats()
        
        return {
            "redis": redis_stats,
            "memory": memory_stats,
            "performance": performance_stats
        }
    
    def get_cache_hit_ratio(self) -> float:
        """Get the current cache hit ratio as a percentage."""
        return self.performance_monitor._calculate_hit_rate()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of cache performance metrics."""
        return {
            "hit_ratio": self.get_cache_hit_ratio(),
            "total_operations": self.performance_monitor.total_operations,
            "cache_hits": self.performance_monitor.cache_hits,
            "cache_misses": self.performance_monitor.cache_misses,
            "recent_avg_key_generation_time": self._get_recent_avg_key_generation_time(),
            "recent_avg_cache_operation_time": self._get_recent_avg_cache_operation_time()
        }
    
    def _get_recent_avg_key_generation_time(self) -> float:
        """Get average key generation time from recent measurements."""
        if not self.performance_monitor.key_generation_times:
            return 0.0
        
        recent_times = [m.duration for m in self.performance_monitor.key_generation_times[-10:]]
        return sum(recent_times) / len(recent_times) if recent_times else 0.0
    
    def _get_recent_avg_cache_operation_time(self) -> float:
        """Get average cache operation time from recent measurements."""
        if not self.performance_monitor.cache_operation_times:
            return 0.0
        
        recent_times = [m.duration for m in self.performance_monitor.cache_operation_times[-10:]]
        return sum(recent_times) / len(recent_times) if recent_times else 0.0
    
    def reset_performance_stats(self):
        """Reset all performance statistics and measurements."""
        self.performance_monitor.reset_stats()
        logger.info("Cache performance statistics have been reset")