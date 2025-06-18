import asyncio
import logging
import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from .base import CacheInterface

logger = logging.getLogger(__name__)


class InMemoryCache(CacheInterface):
    """
    In-memory cache implementation with TTL support.
    
    This cache stores data in memory with optional expiration times.
    It's suitable for development, testing, or when Redis is not available.
    """
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Initialize InMemoryCache with configurable parameters.
        
        Args:
            default_ttl: Default time-to-live for cache entries in seconds
            max_size: Maximum number of entries to store (LRU eviction when exceeded)
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order = []  # Track access order for LRU eviction
        
        logger.info(f"InMemoryCache initialized with default_ttl={default_ttl}s, max_size={max_size}")
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry has expired.
        
        Args:
            entry: Cache entry containing 'expires_at' timestamp
            
        Returns:
            True if expired, False otherwise
        """
        if entry.get('expires_at') is None:
            return False
        return time.time() > entry['expires_at']
    
    def _cleanup_expired(self):
        """
        Remove expired entries from cache.
        
        This method is called periodically during cache operations
        to maintain cache hygiene and free up memory.
        """
        expired_keys = []
        current_time = time.time()
        
        for key, entry in self._cache.items():
            if entry.get('expires_at') and current_time > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _update_access_order(self, key: str):
        """
        Update the access order for LRU tracking.
        
        Args:
            key: Cache key that was accessed
        """
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _evict_lru_if_needed(self):
        """
        Evict least recently used entries if cache exceeds max size.
        """
        while len(self._cache) >= self.max_size and self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    async def get(self, key: str) -> Any:
        """
        Get a value from cache by key (implements CacheInterface).
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        try:
            # Clean up expired entries periodically
            self._cleanup_expired()
            
            if key not in self._cache:
                logger.debug(f"Cache miss for key: {key}")
                return None
            
            entry = self._cache[key]
            
            # Check if entry has expired
            if self._is_expired(entry):
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                logger.debug(f"Cache entry expired for key: {key}")
                return None
            
            # Update access order for LRU
            self._update_access_order(key)
            
            logger.debug(f"Cache hit for key: {key}")
            return entry['value']
            
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        Set a value in cache with optional TTL (implements CacheInterface).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional, uses default if not provided)
        """
        try:
            # Clean up expired entries before adding new ones
            self._cleanup_expired()
            
            # Evict LRU entries if needed
            self._evict_lru_if_needed()
            
            # Calculate expiration time
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            elif self.default_ttl > 0:
                expires_at = time.time() + self.default_ttl
            
            # Store the entry
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            
            # Update access order
            self._update_access_order(key)
            
            ttl_info = f"TTL={ttl or self.default_ttl}s" if expires_at else "no expiration"
            logger.debug(f"Set cache key {key} ({ttl_info})")
            
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """
        Delete a key from cache (implements CacheInterface).
        
        Args:
            key: Cache key to delete
        """
        try:
            existed = key in self._cache
            
            if existed:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            
            logger.debug(f"Deleted cache key {key} (existed: {existed})")
            
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
    
    # Additional utility methods
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        entries_count = len(self._cache)
        self._cache.clear()
        self._access_order.clear()
        logger.info(f"Cleared {entries_count} entries from memory cache")
    
    def size(self) -> int:
        """
        Get the current number of entries in the cache.
        
        Returns:
            Number of cache entries
        """
        return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        # Count expired entries without removing them
        current_time = time.time()
        expired_count = sum(
            1 for entry in self._cache.values()
            if entry.get('expires_at') and current_time > entry['expires_at']
        )
        
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired_count,
            'active_entries': len(self._cache) - expired_count,
            'max_size': self.max_size,
            'utilization': f"{len(self._cache)}/{self.max_size}",
            'utilization_percent': (len(self._cache) / self.max_size) * 100 if self.max_size > 0 else 0,
            'default_ttl': self.default_ttl
        }
    
    def get_keys(self) -> list:
        """
        Get all cache keys (including expired ones).
        
        Returns:
            List of cache keys
        """
        return list(self._cache.keys())
    
    def get_active_keys(self) -> list:
        """
        Get all non-expired cache keys.
        
        Returns:
            List of active cache keys
        """
        current_time = time.time()
        return [
            key for key, entry in self._cache.items()
            if not entry.get('expires_at') or current_time <= entry['expires_at']
        ]
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache and is not expired.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and is not expired, False otherwise
        """
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if self._is_expired(entry):
            # Clean up expired entry
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return False
        
        return True
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time-to-live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds, None if key doesn't exist or has no expiration
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        expires_at = entry.get('expires_at')
        
        if expires_at is None:
            return None  # No expiration set
        
        remaining = int(expires_at - time.time())
        return max(0, remaining)  # Don't return negative values
