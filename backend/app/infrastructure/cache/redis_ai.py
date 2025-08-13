"""
AI Response Cache Implementation with Generic Redis Cache Inheritance

This module provides the refactored AIResponseCache that properly inherits from 
GenericRedisCache while maintaining all AI-specific features and backward compatibility.

Classes:
    AIResponseCache: Refactored AI cache implementation that extends GenericRedisCache
                    with AI-specific functionality including intelligent key generation,
                    operation-specific TTLs, and comprehensive AI metrics collection.

Key Features:
    - **Clean Inheritance**: Proper inheritance from GenericRedisCache for core functionality
    - **Parameter Mapping**: Uses CacheParameterMapper for clean parameter separation
    - **AI-Specific Features**: Maintains all original AI functionality including:
        - Intelligent cache key generation with text hashing
        - Operation-specific TTLs and text size tiers
        - Comprehensive AI metrics and performance monitoring
        - Graceful degradation and pattern-based invalidation
    - **Backward Compatibility**: Maintains existing API contracts and functionality

Architecture:
    This refactored implementation follows the inheritance pattern where:
    - GenericRedisCache provides core Redis functionality (L1 cache, compression, monitoring)
    - AIResponseCache adds AI-specific features and customizations
    - CacheParameterMapper handles parameter separation and validation
    - AI-specific callbacks integrate with the generic cache event system

Usage Examples:
    Basic Usage (maintains backward compatibility):
        >>> cache = AIResponseCache(redis_url="redis://localhost:6379")
        >>> await cache.connect()
        >>> 
        >>> # Cache an AI response
        >>> await cache.cache_response(
        ...     text="Long document to summarize...",
        ...     operation="summarize",
        ...     options={"max_length": 100},
        ...     response={"summary": "Brief summary", "confidence": 0.95}
        ... )

    Advanced Configuration:
        >>> cache = AIResponseCache(
        ...     redis_url="redis://production:6379",
        ...     default_ttl=7200,
        ...     text_hash_threshold=500,
        ...     memory_cache_size=200,
        ...     text_size_tiers={
        ...         'small': 300,
        ...         'medium': 3000, 
        ...         'large': 30000
        ...     }
        ... )

Dependencies:
    Required:
        - app.infrastructure.cache.redis_generic.GenericRedisCache: Parent cache class
        - app.infrastructure.cache.parameter_mapping.CacheParameterMapper: Parameter handling
        - app.infrastructure.cache.key_generator.CacheKeyGenerator: AI key generation
        - app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking
        - app.core.exceptions: Custom exception handling

Performance Considerations:
    - Inherits efficient L1 memory cache and compression from GenericRedisCache
    - AI-specific callbacks add minimal overhead (<1ms per operation)
    - Key generation optimized for large texts with streaming hashing
    - Metrics collection designed for minimal performance impact

Error Handling:
    - Uses custom exceptions following established patterns
    - Graceful degradation when Redis unavailable
    - Comprehensive logging with proper context
    - All Redis operations wrapped with error handling
"""

import hashlib
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Optional Redis import for graceful degradation
try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None  # type: ignore

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
from app.infrastructure.cache.key_generator import CacheKeyGenerator
from app.infrastructure.cache.monitoring import CachePerformanceMonitor

# Configure module-level logging
logger = logging.getLogger(__name__)


class AIResponseCache(GenericRedisCache):
    """
    AI Response Cache with enhanced inheritance architecture.
    
    This refactored implementation properly inherits from GenericRedisCache while 
    maintaining all AI-specific functionality. It uses CacheParameterMapper for
    clean parameter separation and provides comprehensive AI metrics collection.
    
    ### Key Improvements
    - Clean inheritance from GenericRedisCache for core functionality
    - Proper parameter mapping using CacheParameterMapper
    - AI-specific callbacks integrated with generic cache events
    - Maintains backward compatibility with existing API
    - Enhanced error handling with custom exceptions
    
    ### Parameters
    All original AIResponseCache parameters are supported with automatic mapping:
    - `redis_url` (str): Redis connection URL
    - `default_ttl` (int): Default time-to-live for cache entries
    - `text_hash_threshold` (int): Character threshold for text hashing
    - `hash_algorithm`: Hash algorithm for large texts
    - `compression_threshold` (int): Size threshold for compression
    - `compression_level` (int): Compression level (1-9)
    - `text_size_tiers` (Dict[str, int]): Text categorization thresholds
    - `memory_cache_size` (int): Maximum L1 cache entries (mapped to l1_cache_size)
    - `performance_monitor` (CachePerformanceMonitor): Performance monitoring instance
    
    ### Returns
    A fully functional AIResponseCache instance with enhanced architecture.
    
    ### Examples
    ```python
    # Basic usage (backward compatible)
    cache = AIResponseCache(redis_url="redis://localhost:6379")
    await cache.connect()
    
    # Advanced configuration
    cache = AIResponseCache(
        redis_url="redis://production:6379",
        text_hash_threshold=1000,
        memory_cache_size=200,
        text_size_tiers={'small': 500, 'medium': 5000, 'large': 50000}
    )
    ```
    """
    
    def __init__(
        self,
        redis_url: str = "redis://redis:6379",
        default_ttl: int = 3600,
        text_hash_threshold: int = 1000,
        hash_algorithm=hashlib.sha256,
        compression_threshold: int = 1000,
        compression_level: int = 6,
        text_size_tiers: Optional[Dict[str, int]] = None,
        memory_cache_size: int = 100,
        performance_monitor: Optional[CachePerformanceMonitor] = None,
        operation_ttls: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize AIResponseCache with parameter mapping and inheritance.
        
        This constructor uses CacheParameterMapper to separate AI-specific parameters
        from generic Redis parameters, then properly initializes the parent class
        and sets up AI-specific features.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cache entries in seconds
            text_hash_threshold: Character count threshold for text hashing
            hash_algorithm: Hash algorithm to use for large texts
            compression_threshold: Size threshold in bytes for compressing cache data
            compression_level: Compression level (1-9, where 9 is highest compression)
            text_size_tiers: Text size tiers for caching strategy optimization
            memory_cache_size: Maximum number of items in the in-memory cache
            performance_monitor: Optional performance monitor for tracking cache metrics
            operation_ttls: TTL values per AI operation type
        
        Raises:
            ConfigurationError: If parameter mapping fails or invalid configuration
            ValidationError: If parameter validation fails
        """
        logger.debug("Initializing AIResponseCache with inheritance architecture")
        
        try:
            # Collect all AI parameters for mapping
            ai_params = {
                'redis_url': redis_url,
                'default_ttl': default_ttl,
                'text_hash_threshold': text_hash_threshold,
                'hash_algorithm': hash_algorithm,
                'compression_threshold': compression_threshold,
                'compression_level': compression_level,
                'text_size_tiers': text_size_tiers,
                'memory_cache_size': memory_cache_size,
                'performance_monitor': performance_monitor,
                'operation_ttls': operation_ttls,
            }
            
            # Remove None values to avoid validation issues
            ai_params = {k: v for k, v in ai_params.items() if v is not None}
            
            # Use CacheParameterMapper to separate parameters
            self._parameter_mapper = CacheParameterMapper()
            generic_params, ai_specific_params = self._parameter_mapper.map_ai_to_generic_params(ai_params)
            
            # Validate parameter compatibility
            validation_result = self._parameter_mapper.validate_parameter_compatibility(ai_params)
            if not validation_result.is_valid:
                error_details = "; ".join(validation_result.errors)
                raise ValidationError(
                    f"AIResponseCache parameter validation failed: {error_details}",
                    context={
                        'validation_errors': validation_result.errors,
                        'validation_warnings': validation_result.warnings,
                        'ai_params': list(ai_params.keys())
                    }
                )
            
            # Log validation warnings
            for warning in validation_result.warnings:
                logger.warning(f"AIResponseCache parameter warning: {warning}")
            
            # Initialize parent GenericRedisCache with mapped parameters
            super().__init__(**generic_params)
            
            # Set up AI-specific configuration
            self._setup_ai_configuration(**ai_specific_params)
            
            # Set up AI-specific components
            self._setup_ai_components()
            
            # Register AI-specific callbacks after parent initialization
            self._register_ai_callbacks()
            
            logger.info("AIResponseCache initialized successfully with inheritance architecture")
            
        except Exception as e:
            error_msg = f"Failed to initialize AIResponseCache: {e}"
            logger.error(error_msg, exc_info=True)
            
            if isinstance(e, (ConfigurationError, ValidationError)):
                raise
            else:
                raise ConfigurationError(
                    error_msg,
                    context={
                        'initialization_params': list(ai_params.keys()) if 'ai_params' in locals() else [],
                        'error_type': type(e).__name__
                    }
                )

    def _setup_ai_configuration(
        self,
        text_hash_threshold: int = 1000,
        hash_algorithm=hashlib.sha256,
        text_size_tiers: Optional[Dict[str, int]] = None,
        operation_ttls: Optional[Dict[str, int]] = None,
        **kwargs
    ):
        """
        Set up AI-specific configuration parameters.
        
        Initializes all AI-specific configuration including text processing thresholds,
        operation TTLs, and text size tiers with validation and defaults.
        
        Args:
            text_hash_threshold: Character threshold for text hashing
            hash_algorithm: Hash algorithm for large texts
            text_size_tiers: Text categorization thresholds
            operation_ttls: TTL values per operation type
            **kwargs: Additional AI-specific parameters (logged but ignored)
        
        Raises:
            ConfigurationError: If configuration setup fails
        """
        logger.debug("Setting up AI-specific configuration")
        
        try:
            # Store text processing configuration
            self.text_hash_threshold = text_hash_threshold
            self.hash_algorithm = hash_algorithm
            
            # Set up operation-specific TTLs with defaults
            self.operation_ttls = operation_ttls or {
                "summarize": 7200,  # 2 hours - summaries are stable
                "sentiment": 86400,  # 24 hours - sentiment rarely changes
                "key_points": 7200,  # 2 hours
                "questions": 3600,  # 1 hour - questions can vary
                "qa": 1800,  # 30 minutes - context-dependent
            }
            
            # Set up text size tiers with defaults
            self.text_size_tiers = text_size_tiers or {
                "small": 500,    # < 500 chars - cache with full text and use memory cache
                "medium": 5000,  # 500-5000 chars - cache with text hash
                "large": 50000,  # 5000-50000 chars - cache with content hash + metadata
            }
            
            # Log any unexpected parameters
            if kwargs:
                logger.debug(f"Additional AI parameters received: {list(kwargs.keys())}")
            
            logger.info(
                f"AI configuration setup complete: text_hash_threshold={text_hash_threshold}, "
                f"operation_ttls={len(self.operation_ttls)} operations, "
                f"text_size_tiers={len(self.text_size_tiers)} tiers"
            )
            
        except Exception as e:
            error_msg = f"Failed to setup AI configuration: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={
                    'text_hash_threshold': text_hash_threshold,
                    'operation_ttls_count': len(operation_ttls) if operation_ttls else 0,
                    'text_size_tiers_count': len(text_size_tiers) if text_size_tiers else 0
                }
            )

    def _setup_ai_components(self):
        """
        Set up AI-specific components and metrics collection.
        
        Initializes the CacheKeyGenerator and AI-specific metrics tracking
        including hit/miss counters, text tier distribution, and operation performance.
        
        Raises:
            InfrastructureError: If component initialization fails
        """
        logger.debug("Setting up AI-specific components")
        
        try:
            # Initialize AI-specific cache key generator with performance monitoring
            self.key_generator = CacheKeyGenerator(
                text_hash_threshold=self.text_hash_threshold,
                hash_algorithm=self.hash_algorithm,
                performance_monitor=self.performance_monitor,
            )
            
            # Initialize AI-specific metrics tracking
            self.ai_metrics = {
                'cache_hits_by_operation': defaultdict(int),
                'cache_misses_by_operation': defaultdict(int),
                'text_tier_distribution': defaultdict(int),
                'operation_performance': [],
            }
            
            # Backward compatibility - all memory cache attributes are provided as properties
            # No assignments needed here since properties handle the compatibility layer
            
            logger.info("AI components setup complete: key generator and metrics initialized")
            
        except Exception as e:
            error_msg = f"Failed to setup AI components: {e}"
            logger.error(error_msg, exc_info=True)
            raise InfrastructureError(
                error_msg,
                context={
                    'text_hash_threshold': getattr(self, 'text_hash_threshold', None),
                    'hash_algorithm': str(getattr(self, 'hash_algorithm', None)),
                    'performance_monitor_available': self.performance_monitor is not None
                }
            )

    def _register_ai_callbacks(self):
        """
        Register AI-specific callbacks with the parent GenericRedisCache.
        
        This method integrates AI-specific behavior with the generic cache system
        by registering callback functions that are executed on cache events.
        """
        logger.debug("Registering AI-specific callbacks")
        
        try:
            # Register callbacks for cache events
            self.register_callback('get_success', self._ai_get_success_callback)
            self.register_callback('get_miss', self._ai_get_miss_callback)
            self.register_callback('set_success', self._ai_set_success_callback)
            
            logger.debug("AI callbacks registered successfully")
            
        except Exception as e:
            logger.warning(f"Failed to register AI callbacks: {e}")

    # AI-Specific Callback Methods for Composition Pattern
    
    def _ai_get_success_callback(self, key: str, value: Any, **kwargs):
        """
        AI-specific callback for successful cache retrievals.
        
        Records AI-specific metrics including operation type, text tier,
        and updates hit counters for comprehensive AI cache analytics.
        
        Args:
            key: Cache key that was retrieved
            value: Retrieved cache value
            **kwargs: Additional callback context
        """
        try:
            # Extract operation and text tier from cache key for metrics
            if key.startswith('ai_cache:'):
                # Parse operation from key format: ai_cache:op:operation|...
                key_parts = key.split('|')
                if len(key_parts) > 0 and key_parts[0].startswith('ai_cache:op:'):
                    operation = key_parts[0].split(':')[2]
                    self.ai_metrics['cache_hits_by_operation'][operation] += 1
                    
                    # Determine text tier if available in context
                    text_tier = kwargs.get('text_tier', 'unknown')
                    self.ai_metrics['text_tier_distribution'][text_tier] += 1
                    
                    logger.debug(f"AI cache hit recorded: operation={operation}, tier={text_tier}")
        except Exception as e:
            logger.warning(f"AI get success callback failed: {e}")
    
    def _ai_get_miss_callback(self, key: str, **kwargs):
        """
        AI-specific callback for cache misses.
        
        Records AI-specific miss metrics including operation type and reason
        for comprehensive cache performance analysis.
        
        Args:
            key: Cache key that was missed
            **kwargs: Additional callback context including miss reason
        """
        try:
            # Extract operation from cache key for metrics
            if key.startswith('ai_cache:'):
                # Parse operation from key format: ai_cache:op:operation|...
                key_parts = key.split('|')
                if len(key_parts) > 0 and key_parts[0].startswith('ai_cache:op:'):
                    operation = key_parts[0].split(':')[2]
                    self.ai_metrics['cache_misses_by_operation'][operation] += 1
                    
                    miss_reason = kwargs.get('reason', 'unknown')
                    logger.debug(f"AI cache miss recorded: operation={operation}, reason={miss_reason}")
        except Exception as e:
            logger.warning(f"AI get miss callback failed: {e}")
    
    def _ai_set_success_callback(self, key: str, value: Any, **kwargs):
        """
        AI-specific callback for successful cache stores.
        
        Records AI-specific set metrics including operation type, data size,
        and performance tracking for cache optimization analysis.
        
        Args:
            key: Cache key that was set
            value: Cached value
            **kwargs: Additional callback context including operation details
        """
        try:
            # Extract operation from cache key for metrics
            if key.startswith('ai_cache:'):
                # Parse operation from key format: ai_cache:op:operation|...
                key_parts = key.split('|')
                if len(key_parts) > 0 and key_parts[0].startswith('ai_cache:op:'):
                    operation = key_parts[0].split(':')[2]
                    
                    # Record operation performance data
                    operation_data = {
                        'operation': operation,
                        'timestamp': time.time(),
                        'data_size': len(str(value)),
                        'ttl': kwargs.get('ttl', self.default_ttl)
                    }
                    self.ai_metrics['operation_performance'].append(operation_data)
                    
                    # Keep only recent performance data (last 1000 operations)
                    if len(self.ai_metrics['operation_performance']) > 1000:
                        self.ai_metrics['operation_performance'] = \
                            self.ai_metrics['operation_performance'][-1000:]
                    
                    logger.debug(f"AI cache set recorded: operation={operation}, size={operation_data['data_size']}")
        except Exception as e:
            logger.warning(f"AI set success callback failed: {e}")

    # AI-Specific Methods
    
    def _generate_cache_key(
        self,
        text: str,
        operation: str,
        options: Dict[str, Any],
        question: Optional[str] = None,
    ) -> str:
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

    def _get_text_tier(self, text: str) -> str:
        """
        Determine caching tier based on text size.

        Args:
            text: Input text to categorize

        Returns:
            Tier name: 'small', 'medium', 'large', or 'xlarge'
        """
        text_len = len(text)
        if text_len < self.text_size_tiers["small"]:
            return "small"
        elif text_len < self.text_size_tiers["medium"]:
            return "medium"
        elif text_len < self.text_size_tiers["large"]:
            return "large"
        else:
            return "xlarge"

    def _get_text_tier_from_key(self, key: str) -> str:
        """
        Extract text tier information from cache key if available.

        Args:
            key: Cache key to analyze

        Returns:
            Text tier name or 'unknown' if not determinable
        """
        # This is a simplified implementation - actual implementation would
        # parse the cache key format to extract tier information
        # For now, return unknown as fallback
        return "unknown"

    def _extract_operation_from_key(self, key: str) -> str:
        """
        Parse cache key to extract operation type.

        Args:
            key: Cache key to parse

        Returns:
            Operation type or 'unknown' if not parseable
        """
        try:
            # Parse cache key format: ai_cache:op:operation|...
            if ":op:" in key:
                parts = key.split(":op:")
                if len(parts) > 1:
                    operation_part = parts[1].split("|")[0]
                    return operation_part
            return "unknown"
        except Exception:
            return "unknown"

    # Public AI-Specific Methods

    async def cache_response(
        self,
        text: str,
        operation: str,
        options: Dict[str, Any],
        response: Dict[str, Any],
        question: Optional[str] = None,
    ) -> None:
        """
        Cache AI response with AI-specific optimizations.

        This method provides the main AI caching functionality, using the inherited
        set() method from GenericRedisCache while adding AI-specific features like
        intelligent key generation, operation-specific TTLs, and metadata enhancement.

        Args:
            text (str): Input text that generated this response
            operation (str): Operation type (e.g., 'summarize', 'sentiment')
            options (Dict[str, Any]): Operation options used to generate response
            response (Dict[str, Any]): AI response data to cache
            question (str, optional): Question for Q&A operations

        Example:
            >>> await cache.cache_response(
            ...     text="Long document...",
            ...     operation="summarize",
            ...     options={"max_length": 100},
            ...     response={"summary": "Brief summary", "confidence": 0.95}
            ... )
        """
        start_time = time.time()

        try:
            # Generate AI-optimized cache key
            cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
            
            # Determine text tier for metrics
            text_tier = self._get_text_tier(text)
            
            # Get operation-specific TTL
            ttl = self.operation_ttls.get(operation, self.default_ttl)
            
            # Build enhanced cached response with AI metadata
            cached_response = {
                **response,
                "cached_at": datetime.now().isoformat(),
                "cache_hit": False,  # Will be set to True when retrieved
                "text_length": len(text),
                "text_tier": text_tier,
                "operation": operation,
                "ai_version": "refactored_inheritance",
                "key_generation_time": getattr(self.key_generator, 'last_generation_time', 0),
            }

            # Use inherited set method from GenericRedisCache
            await self.set(cache_key, cached_response, ttl)

            # Record successful cache operation time
            duration = time.time() - start_time
            logger.debug(
                f"Cached AI response for {operation} (tier: {text_tier}, "
                f"ttl: {ttl}s, time: {duration:.3f}s)"
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.warning(f"Failed to cache AI response: {e}")
            # Don't re-raise - caching failures should not interrupt application flow

    async def get_cached_response(
        self,
        text: str,
        operation: str,
        options: Dict[str, Any],
        question: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached AI response with AI-specific optimizations.

        This method provides AI cache retrieval functionality, using the inherited
        get() method from GenericRedisCache while adding AI-specific features like
        cache hit metadata enhancement and memory cache promotion for small texts.

        Args:
            text (str): Input text content
            operation (str): Operation type
            options (Dict[str, Any]): Operation options
            question (str, optional): Question for Q&A operations

        Returns:
            Cached response if found, None otherwise

        Example:
            >>> cached = await cache.get_cached_response(
            ...     text="Long document...",
            ...     operation="summarize",
            ...     options={"max_length": 100}
            ... )
            >>> if cached:
            ...     print(f"Found cached result: {cached['summary']}")
        """
        start_time = time.time()

        try:
            # Generate AI-optimized cache key
            cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
            
            # Determine text tier for metrics and promotion decisions
            text_tier = self._get_text_tier(text)

            # Use inherited get method from GenericRedisCache
            cached_data = await self.get(cache_key)

            if cached_data:
                # Enhance cached data with retrieval metadata
                cached_data["cache_hit"] = True
                cached_data["retrieved_at"] = datetime.now().isoformat()

                # Check if small text should be promoted to memory cache
                if self._should_promote_to_memory(text_tier, operation):
                    # Memory cache promotion is handled automatically by parent class
                    # via L1 cache integration - no additional action needed
                    pass

                logger.debug(f"AI cache hit for {operation} (tier: {text_tier})")
                return cached_data
            else:
                logger.debug(f"AI cache miss for {operation} (tier: {text_tier})")
                return None

        except Exception as e:
            duration = time.time() - start_time
            logger.warning(f"Cache retrieval error for {operation}: {e}")
            return None

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
                    "reason": "redis_connection_failed",
                },
            )
            return

        try:
            assert (
                self.redis is not None
            )  # Type checker hint: redis is available after successful connect()
            keys = await self.redis.keys(f"ai_cache:*{pattern}*".encode("utf-8"))
            keys_count = len(keys) if keys else 0

            if keys:
                await self.redis.delete(*keys)
                logger.info(
                    f"Invalidated {keys_count} cache entries matching {pattern}"
                )
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
                    "search_pattern": f"ai_cache:*{pattern}*",
                },
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
                    "error": str(e),
                },
            )
            logger.warning(f"Cache invalidation error: {e}")

    async def invalidate_by_operation(
        self, operation: str, operation_context: str = ""
    ) -> int:
        """
        Invalidate cache entries for a specific operation type.

        Removes all cached responses for a particular AI operation type while
        preserving other operation types intact.

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
        await self.invalidate_pattern(
            f"op:{operation}", operation_context=operation_context
        )

    def _should_promote_to_memory(self, text_tier: str, operation: str) -> bool:
        """
        Determine if a cache entry should be promoted to memory cache.

        Uses text tier and operation stability to make promotion decisions,
        favoring small texts and stable operations for memory cache promotion.

        Args:
            text_tier (str): Text tier ('small', 'medium', 'large', 'xlarge')
            operation (str): Operation type

        Returns:
            True if entry should be promoted to memory cache

        Note:
            Actual memory cache promotion is handled by the parent GenericRedisCache
            through L1 cache integration. This method only provides the decision logic.
        """
        # Promote small texts for fast access
        if text_tier == "small":
            return True
        
        # Promote stable operations regardless of size
        stable_operations = {"sentiment", "summarize"}
        if operation in stable_operations:
            return True
        
        return False

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
                - ai_metrics: AI-specific performance metrics

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
                assert (
                    self.redis is not None
                )  # Type checker hint: redis is available after successful connect()
                keys = await self.redis.keys(b"ai_cache:*")
                info = await self.redis.info()
                redis_stats = {
                    "status": "connected",
                    "keys": len(keys),
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "memory_used_bytes": info.get("used_memory", 0),
                    "connected_clients": info.get("connected_clients", 0),
                }
            except Exception as e:
                logger.warning(f"Cache stats error: {e}")
                redis_stats = {"status": "error", "error": str(e)}

        # Add memory cache statistics
        memory_stats = {
            "memory_cache_entries": len(self.memory_cache),
            "memory_cache_size_limit": getattr(self, 'memory_cache_size', 0),
            "memory_cache_utilization": f"{len(self.memory_cache)}/{getattr(self, 'memory_cache_size', 0)}",
        }

        # Add performance statistics
        performance_stats = self.performance_monitor.get_performance_stats()

        return {
            "redis": redis_stats,
            "memory": memory_stats,
            "performance": performance_stats,
            "ai_metrics": self.ai_metrics,
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
        hit ratios, operation counts, timing statistics, memory usage, and
        AI-specific metrics.

        Returns:
            Dict[str, Any]: Performance summary containing:
                - hit_ratio: Cache hit percentage
                - total_operations: Total cache operations performed
                - cache_hits/cache_misses: Breakdown of successful/failed retrievals
                - recent_avg_cache_operation_time: Average cache operation time
                - ai_operation_metrics: AI-specific operation performance data
                - text_tier_distribution: Distribution of cached content by text size

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
            "recent_avg_cache_operation_time": self._get_recent_avg_cache_operation_time(),
            "ai_operation_metrics": dict(self.ai_metrics['cache_hits_by_operation']),
            "ai_miss_metrics": dict(self.ai_metrics['cache_misses_by_operation']),
            "text_tier_distribution": dict(self.ai_metrics['text_tier_distribution']),
            "recent_ai_operations": len(self.ai_metrics['operation_performance']),
        }

        return summary

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

        recent_times = [
            m.duration for m in self.performance_monitor.cache_operation_times[-10:]
        ]
        return sum(recent_times) / len(recent_times) if recent_times else 0.0

    # Override connect method to maintain compatibility with original implementation
    async def connect(self) -> bool:
        """Initialize Redis connection honoring this module's aioredis/flags.

        Mirrors the parent implementation but binds to the aioredis symbol
        defined in this module so unit tests can patch
        `app.infrastructure.cache.redis_ai.aioredis` as expected.
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - operating in memory-only mode")
            return False

        if not self.redis:
            try:
                assert aioredis is not None  # type: ignore[unreachable]
                self.redis = await aioredis.from_url(  # type: ignore[attr-defined]
                    self.redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                assert self.redis is not None
                await self.redis.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
                return True
            except Exception as e:
                logger.warning(
                    f"Redis connection failed: {e} - using memory-only mode"
                )
                self.redis = None
                return False
        return True

    # Legacy compatibility methods and properties
    
    @property
    def memory_cache(self) -> Dict[str, Any]:
        """Legacy compatibility property for memory cache access."""
        return self.l1_cache._cache if self.l1_cache else {}
    
    @property
    def memory_cache_size(self) -> int:
        """Legacy compatibility property for memory cache size."""
        return self.l1_cache.max_size if self.l1_cache else 0
    
    @property
    def memory_cache_order(self) -> List[str]:
        """Legacy compatibility property for memory cache order (not used in new implementation)."""
        return []  # Maintained for compatibility but not used