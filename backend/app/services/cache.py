import hashlib
import json
import asyncio
import logging
import zlib
import pickle
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

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
                 text_size_tiers: dict = None, memory_cache_size: int = 100,
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
            text_size_tiers: Text size tiers for caching strategy optimization (None for defaults)
            memory_cache_size: Maximum number of items in the in-memory cache
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
        
        # Tiered caching configuration - use provided or default values
        self.text_size_tiers = text_size_tiers or {
            'small': 500,      # < 500 chars - cache with full text and use memory cache
            'medium': 5000,    # 500-5000 chars - cache with text hash
            'large': 50000,    # 5000-50000 chars - cache with content hash + metadata
        }
        
        # In-memory cache for frequently accessed small items
        self.memory_cache = {}  # Cache storage: {key: value}
        self.memory_cache_size = memory_cache_size  # Maximum number of items in memory cache
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
        """
        Initialize Redis connection with graceful degradation.
        
        Attempts to establish a connection to Redis using the configured URL.
        If Redis is not available or connection fails, the cache will operate
        without persistence (graceful degradation).
        
        Returns:
            bool: True if successfully connected to Redis, False otherwise.
            
        Raises:
            None: All exceptions are caught and logged as warnings.
            
        Example:
            >>> cache = AIResponseCache()
            >>> connected = await cache.connect()
            >>> if connected:
            ...     print("Redis connected successfully")
            ... else:
            ...     print("Operating without Redis persistence")
        """
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
        """
        Generate optimized cache key using CacheKeyGenerator.
        
        This is a wrapper method that delegates to the CacheKeyGenerator instance
        for consistent key generation throughout the cache system.
        
        Args:
            text (str): Input text content to be cached.
            operation (str): Operation type (e.g., 'summarize', 'sentiment').
            options (Dict[str, Any]): Operation-specific options and parameters.
            question (str, optional): Question for Q&A operations. Defaults to None.
            
        Returns:
            str: Optimized cache key suitable for Redis storage.
            
        Example:
            >>> cache = AIResponseCache()
            >>> key = cache._generate_cache_key(
            ...     text="Sample text", 
            ...     operation="summarize", 
            ...     options={"max_length": 100}
            ... )
            >>> print(key)
            'ai_cache:op:summarize|txt:Sample text|opts:abc12345'
        """
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
        """
        Cache AI response with compression for large data and appropriate TTL.
        
        Stores an AI response in the cache with intelligent compression based on
        response size, appropriate TTL based on operation type, and comprehensive
        performance monitoring.
        
        Args:
            text (str): Input text that generated this response.
            operation (str): Operation type (e.g., 'summarize', 'sentiment').
            options (Dict[str, Any]): Operation options used to generate response.
            response (Dict[str, Any]): AI response data to cache.
            question (str, optional): Question for Q&A operations. Defaults to None.
            
        Returns:
            None: This method performs caching as a side effect.
            
        Raises:
            None: All Redis exceptions are caught and logged as warnings.
            
        Note:
            - Responses larger than compression_threshold are automatically compressed
            - TTL varies by operation type (e.g., sentiment: 24h, qa: 30min)
            - Performance metrics are automatically recorded
            
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.cache_response(
            ...     text="Long document...",
            ...     operation="summarize", 
            ...     options={"max_length": 100},
            ...     response={"summary": "Brief summary", "confidence": 0.95}
            ... )
        """
        # Start timing the cache response generation
        start_time = time.time()
        
        if not await self.connect():
            # Record failed cache operation timing
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="set",
                duration=duration,
                cache_hit=False,  # Not applicable for set operations, but tracking as failure
                text_length=len(text),
                additional_data={
                    "operation_type": operation,
                    "reason": "redis_connection_failed",
                    "status": "failed"
                }
            )
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
            
            # Time compression separately if it will be used
            compression_start = time.time()
            cache_data = self._compress_data(cached_response)
            compression_time = time.time() - compression_start
            
            # Record compression metrics if compression was actually used
            if will_compress:
                original_size = len(str(cached_response))
                compressed_size = len(cache_data)
                self.performance_monitor.record_compression_ratio(
                    original_size=original_size,
                    compressed_size=compressed_size,
                    compression_time=compression_time,
                    operation_type=operation
                )
            
            await self.redis.setex(cache_key, ttl, cache_data)
            
            # Record successful cache response generation timing
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="set",
                duration=duration,
                cache_hit=True,  # Successful set operation
                text_length=len(text),
                additional_data={
                    "operation_type": operation,
                    "response_size": response_size,
                    "cache_data_size": len(cache_data),
                    "compression_used": will_compress,
                    "compression_time": compression_time,
                    "ttl": ttl,
                    "status": "success"
                }
            )
            
            logger.debug(f"Cached response for {operation} (size: {len(cache_data)} bytes, compression: {will_compress}, time: {duration:.3f}s)")
            
        except Exception as e:
            # Record failed cache response generation timing
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="set",
                duration=duration,
                cache_hit=False,  # Failed operation
                text_length=len(text),
                additional_data={
                    "operation_type": operation,
                    "reason": "redis_error",
                    "error": str(e),
                    "status": "failed"
                }
            )
            logger.warning(f"Cache storage error: {e}")
    
    async def invalidate_pattern(self, pattern: str, operation_context: str = ""):
        """
        Invalidate cache entries matching a specified pattern.
        
        Searches for cache keys matching the given pattern and removes them
        from Redis. Records invalidation metrics for monitoring and analysis.
        
        Args:
            pattern (str): Pattern to match cache keys (supports wildcards).
                          Example: "summarize" matches keys containing "summarize".
            operation_context (str, optional): Context describing why invalidation
                                             was triggered. Defaults to "".
                                             
        Returns:
            None: This method performs invalidation as a side effect.
            
        Raises:
            None: All Redis exceptions are caught and logged as warnings.
            
        Note:
            - Actual Redis pattern used is "ai_cache:*{pattern}*"
            - Performance metrics are automatically recorded
            - Zero matches is not considered an error
            
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.invalidate_pattern(
            ...     pattern="summarize", 
            ...     operation_context="model_update"
            ... )
            # Invalidates all cache entries with "summarize" in the key
        """
        start_time = time.time()
        
        if not await self.connect():
            # Record failed invalidation attempt
            duration = time.time() - start_time
            self.performance_monitor.record_invalidation_event(
                pattern=pattern,
                keys_invalidated=0,
                duration=duration,
                invalidation_type="manual",
                operation_context=operation_context,
                additional_data={
                    "status": "failed",
                    "reason": "redis_connection_failed"
                }
            )
            return
            
        try:
            keys = await self.redis.keys(f"ai_cache:*{pattern}*".encode('utf-8'))
            keys_count = len(keys) if keys else 0
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {keys_count} cache entries matching {pattern}")
            else:
                logger.debug(f"No cache entries found for pattern {pattern}")
            
            # Record successful invalidation
            duration = time.time() - start_time
            self.performance_monitor.record_invalidation_event(
                pattern=pattern,
                keys_invalidated=keys_count,
                duration=duration,
                invalidation_type="manual",
                operation_context=operation_context,
                additional_data={
                    "status": "success",
                    "search_pattern": f"ai_cache:*{pattern}*"
                }
            )
            
        except Exception as e:
            # Record failed invalidation
            duration = time.time() - start_time
            self.performance_monitor.record_invalidation_event(
                pattern=pattern,
                keys_invalidated=0,
                duration=duration,
                invalidation_type="manual",
                operation_context=operation_context,
                additional_data={
                    "status": "failed",
                    "reason": "redis_error",
                    "error": str(e)
                }
            )
            logger.warning(f"Cache invalidation error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics including Redis and memory cache metrics.
        
        Collects statistics from Redis (if available), in-memory cache, and
        performance monitoring system. Also records current memory usage for tracking.
        
        Returns:
            Dict[str, Any]: Comprehensive cache statistics containing:
                - redis: Redis connection status, key count, memory usage
                - memory: In-memory cache statistics and utilization
                - performance: Hit ratios, operation timings, compression stats
                
        Raises:
            None: Redis errors are caught and logged, returning error status.
            
        Example:
            >>> cache = AIResponseCache()
            >>> stats = await cache.get_cache_stats()
            >>> print(f"Hit ratio: {stats['performance']['hit_ratio']:.2%}")
            >>> print(f"Redis keys: {stats['redis']['keys']}")
            >>> print(f"Memory cache: {stats['memory']['memory_cache_entries']}")
        """
        redis_stats = {"status": "unavailable", "keys": 0}
        
        if await self.connect():
            try:
                keys = await self.redis.keys(b"ai_cache:*")
                info = await self.redis.info()
                redis_stats = {
                    "status": "connected",
                    "keys": len(keys),
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "memory_used_bytes": info.get("used_memory", 0),
                    "connected_clients": info.get("connected_clients", 0)
                }
            except Exception as e:
                logger.warning(f"Cache stats error: {e}")
                redis_stats = {"status": "error", "error": str(e)}
        
        # Record current memory usage for monitoring
        self.record_memory_usage(redis_stats)
        
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
        """
        Get the current cache hit ratio as a percentage.
        
        Calculates the percentage of cache operations that resulted in hits
        (successful retrievals) versus misses.
        
        Returns:
            float: Hit ratio as a percentage (0.0 to 100.0).
                  Returns 0.0 if no operations have been recorded.
                  
        Example:
            >>> cache = AIResponseCache()
            >>> # After some cache operations...
            >>> hit_ratio = cache.get_cache_hit_ratio()
            >>> print(f"Cache hit ratio: {hit_ratio:.1f}%")
            Cache hit ratio: 75.3%
        """
        return self.performance_monitor._calculate_hit_rate()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of cache performance metrics.
        
        Provides a consolidated view of key performance indicators including
        hit ratios, operation counts, timing statistics, and memory usage.
        
        Returns:
            Dict[str, Any]: Performance summary containing:
                - hit_ratio: Cache hit percentage
                - total_operations: Total cache operations performed
                - cache_hits/cache_misses: Breakdown of successful/failed retrievals
                - recent_avg_key_generation_time: Average key generation time
                - recent_avg_cache_operation_time: Average cache operation time
                - total_invalidations/total_keys_invalidated: Invalidation statistics
                - memory_usage: Memory usage statistics (if available)
                
        Example:
            >>> cache = AIResponseCache()
            >>> summary = cache.get_performance_summary()
            >>> print(f"Operations: {summary['total_operations']}")
            >>> print(f"Hit ratio: {summary['hit_ratio']:.1f}%")
            >>> print(f"Avg operation time: {summary['recent_avg_cache_operation_time']:.3f}s")
        """
        summary = {
            "hit_ratio": self.get_cache_hit_ratio(),
            "total_operations": self.performance_monitor.total_operations,
            "cache_hits": self.performance_monitor.cache_hits,
            "cache_misses": self.performance_monitor.cache_misses,
            "recent_avg_key_generation_time": self._get_recent_avg_key_generation_time(),
            "recent_avg_cache_operation_time": self._get_recent_avg_cache_operation_time(),
            "total_invalidations": self.performance_monitor.total_invalidations,
            "total_keys_invalidated": self.performance_monitor.total_keys_invalidated
        }
            
        # Include memory usage stats if any measurements have been recorded
        if self.performance_monitor.memory_usage_measurements:
            summary["memory_usage"] = self.get_memory_usage_stats()
            
        return summary
    
    def _get_recent_avg_key_generation_time(self) -> float:
        """
        Get average key generation time from recent measurements.
        
        Calculates the average time taken to generate cache keys from the
        most recent 10 measurements. Useful for performance monitoring.
        
        Returns:
            float: Average key generation time in seconds from recent measurements.
                  Returns 0.0 if no measurements are available.
                  
        Note:
            Only considers the 10 most recent measurements to provide
            current performance rather than historical averages.
        """
        if not self.performance_monitor.key_generation_times:
            return 0.0
        
        recent_times = [m.duration for m in self.performance_monitor.key_generation_times[-10:]]
        return sum(recent_times) / len(recent_times) if recent_times else 0.0
    
    def _get_recent_avg_cache_operation_time(self) -> float:
        """
        Get average cache operation time from recent measurements.
        
        Calculates the average time taken for cache operations (get/set) from
        the most recent 10 measurements. Useful for performance monitoring.
        
        Returns:
            float: Average cache operation time in seconds from recent measurements.
                  Returns 0.0 if no measurements are available.
                  
        Note:
            Only considers the 10 most recent measurements to provide
            current performance rather than historical averages.
        """
        if not self.performance_monitor.cache_operation_times:
            return 0.0
        
        recent_times = [m.duration for m in self.performance_monitor.cache_operation_times[-10:]]
        return sum(recent_times) / len(recent_times) if recent_times else 0.0
    
    def record_memory_usage(self, redis_stats: Dict[str, Any] = None):
        """
        Record current memory usage of cache components.
        
        Captures a snapshot of memory usage across different cache tiers
        including in-memory cache and Redis (if available). This data is
        used for performance monitoring and capacity planning.
        
        Args:
            redis_stats (Dict[str, Any], optional): Redis statistics from INFO command.
                                                   If None, only memory cache stats are recorded.
                                                   
        Returns:
            None: This method records metrics as a side effect.
            
        Raises:
            None: All exceptions are caught and logged as warnings.
            
        Note:
            Called automatically by get_cache_stats() but can be called
            manually for more frequent memory monitoring.
            
        Example:
            >>> cache = AIResponseCache()
            >>> redis_info = await cache.redis.info() if cache.redis else None
            >>> cache.record_memory_usage(redis_info)
        """
        try:
            self.performance_monitor.record_memory_usage(
                memory_cache=self.memory_cache,
                redis_stats=redis_stats,
                additional_data={
                    "memory_cache_size_limit": self.memory_cache_size,
                    "memory_cache_order_count": len(self.memory_cache_order)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record memory usage: {e}")

    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """
        Get detailed memory usage statistics for cache components.
        
        Returns comprehensive memory usage information including utilization
        percentages, growth trends, and efficiency metrics.
        
        Returns:
            Dict[str, Any]: Memory usage statistics containing:
                - current_usage: Current memory consumption
                - historical_trend: Memory usage over time
                - efficiency_metrics: Memory efficiency indicators
                - warning_indicators: Memory usage warnings if applicable
                
        Example:
            >>> cache = AIResponseCache()
            >>> memory_stats = cache.get_memory_usage_stats()
            >>> print(f"Memory cache utilization: {memory_stats.get('utilization', 0):.1f}%")
        """
        return self.performance_monitor.get_memory_usage_stats()

    def get_memory_warnings(self) -> List[Dict[str, Any]]:
        """
        Get active memory-related warnings and alerts.
        
        Returns any current warnings about memory usage that may indicate
        performance issues or capacity constraints.
        
        Returns:
            List[Dict[str, Any]]: List of active memory warnings, each containing:
                - severity: Warning level ('warning', 'critical')
                - message: Human-readable warning description
                - threshold: The threshold that was exceeded
                - current_value: Current value that triggered the warning
                - recommendations: Suggested actions to resolve the issue
                
        Example:
            >>> cache = AIResponseCache()
            >>> warnings = cache.get_memory_warnings()
            >>> for warning in warnings:
            ...     print(f"{warning['severity'].upper()}: {warning['message']}")
            WARNING: Memory cache approaching size limit (95/100 entries)
        """
        return self.performance_monitor.get_memory_warnings()

    def reset_performance_stats(self):
        """
        Reset all performance statistics and measurements.
        
        Clears all accumulated performance data including hit/miss counts,
        timing measurements, compression statistics, and memory usage history.
        Useful for starting fresh performance analysis periods.
        
        Returns:
            None: This method resets statistics as a side effect.
            
        Warning:
            This action cannot be undone. All historical performance data
            will be lost. Consider exporting metrics before resetting if
            historical data is needed.
            
        Example:
            >>> cache = AIResponseCache()
            >>> # Export current metrics before reset if needed
            >>> metrics = cache.get_performance_summary()
            >>> cache.reset_performance_stats()
            >>> print("Performance statistics reset")
        """
        self.performance_monitor.reset_stats()
        logger.info("Cache performance statistics have been reset")

    def get_invalidation_frequency_stats(self) -> Dict[str, Any]:
        """
        Get invalidation frequency statistics and analysis.
        
        Provides detailed analysis of cache invalidation patterns including
        frequency, timing, and efficiency metrics. Useful for optimizing
        cache management strategies.
        
        Returns:
            Dict[str, Any]: Invalidation statistics containing:
                - frequency_metrics: How often invalidations occur
                - pattern_analysis: Most common invalidation patterns
                - timing_statistics: Time taken for invalidation operations
                - efficiency_indicators: Invalidation effectiveness metrics
                
        Example:
            >>> cache = AIResponseCache()
            >>> stats = cache.get_invalidation_frequency_stats()
            >>> print(f"Invalidations per hour: {stats.get('per_hour', 0)}")
            >>> print(f"Most common pattern: {stats.get('top_patterns', ['None'])[0]}")
        """
        return self.performance_monitor.get_invalidation_frequency_stats()

    def get_invalidation_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations based on invalidation patterns and performance data.
        
        Analyzes invalidation patterns and provides actionable recommendations
        for optimizing cache invalidation strategies and improving performance.
        
        Returns:
            List[Dict[str, Any]]: List of recommendations, each containing:
                - type: Recommendation category ('optimization', 'warning', 'configuration')
                - priority: Importance level ('high', 'medium', 'low')
                - message: Human-readable recommendation
                - action: Specific action to take
                - expected_benefit: Expected performance improvement
                
        Example:
            >>> cache = AIResponseCache()
            >>> recommendations = cache.get_invalidation_recommendations()
            >>> for rec in recommendations:
            ...     if rec['priority'] == 'high':
            ...         print(f"HIGH: {rec['message']}")
            HIGH: Consider increasing TTL for sentiment operations (low invalidation value)
        """
        return self.performance_monitor.get_invalidation_recommendations()

    async def invalidate_all(self, operation_context: str = "manual_clear_all"):
        """
        Invalidate all cache entries in Redis and memory cache.
        
        Clears the entire cache by invalidating all entries. This is a
        comprehensive operation that affects both Redis and in-memory caches.
        
        Args:
            operation_context (str, optional): Context describing why the full
                                             invalidation was triggered. 
                                             Defaults to "manual_clear_all".
                                             
        Returns:
            None: This method performs invalidation as a side effect.
            
        Warning:
            This operation removes ALL cached data and cannot be undone.
            Use with caution in production environments.
            
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.invalidate_all(operation_context="model_deployment")
            >>> print("All cache entries have been cleared")
        """
        await self.invalidate_pattern("", operation_context=operation_context)

    async def invalidate_by_operation(self, operation: str, operation_context: str = ""):
        """
        Invalidate cache entries for a specific operation type.
        
        Removes all cached responses for a particular operation (e.g., 'summarize',
        'sentiment') while leaving other operation types intact.
        
        Args:
            operation (str): Operation type to invalidate (e.g., 'summarize', 'sentiment').
            operation_context (str, optional): Context describing why this operation's
                                             cache was invalidated. Auto-generated if not provided.
                                             
        Returns:
            None: This method performs invalidation as a side effect.
            
        Example:
            >>> cache = AIResponseCache()
            >>> # Invalidate all summarization results due to model update
            >>> await cache.invalidate_by_operation(
            ...     operation="summarize", 
            ...     operation_context="summarization_model_updated"
            ... )
            >>> print("All summarization cache entries cleared")
        """
        if not operation_context:
            operation_context = f"operation_specific_{operation}"
        await self.invalidate_pattern(f"op:{operation}", operation_context=operation_context)

    async def invalidate_memory_cache(self, operation_context: str = "memory_cache_clear"):
        """
        Clear the in-memory cache and record the invalidation event.
        
        Removes all entries from the in-memory cache tier while preserving
        Redis cache entries. Records the invalidation for performance monitoring.
        
        Args:
            operation_context (str, optional): Context describing why the memory cache
                                             was cleared. Defaults to "memory_cache_clear".
                                             
        Returns:
            None: This method performs cache clearing as a side effect.
            
        Note:
            This only affects the in-memory cache tier. Redis cache entries
            remain intact and will repopulate the memory cache on access.
            
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.invalidate_memory_cache(
            ...     operation_context="memory_optimization"
            ... )
            >>> print("Memory cache cleared, Redis cache preserved")
        """
        start_time = time.time()
        
        # Count entries before clearing
        entries_cleared = len(self.memory_cache)
        
        # Clear memory cache
        self.memory_cache.clear()
        self.memory_cache_order.clear()
        
        # Record the invalidation event
        duration = time.time() - start_time
        self.performance_monitor.record_invalidation_event(
            pattern="memory_cache",
            keys_invalidated=entries_cleared,
            duration=duration,
            invalidation_type="memory",
            operation_context=operation_context,
            additional_data={
                "status": "success",
                "invalidation_target": "memory_cache_only"
            }
        )
        
        logger.info(f"Cleared {entries_cleared} entries from memory cache")