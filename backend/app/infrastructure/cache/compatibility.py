"""[REFACTORED] Compatibility wrapper for maintaining backwards compatibility during cache transitions.

This module provides wrapper classes and utilities that ensure existing code
continues to work during the cache infrastructure refactoring. It acts as a
bridge between old and new cache implementations, allowing gradual migration
without breaking existing functionality.

Classes:
    CompatibilityWrapper: Main wrapper class that provides backwards compatibility
                         for existing cache interfaces while delegating to new
                         implementations internally.

Key Features:
    - Seamless integration with existing codebase during transition period
    - Method mapping between old and new cache interface signatures
    - Deprecation warnings for old patterns with migration guidance
    - Configurable compatibility modes (strict, permissive, migration)
    - Performance metrics to track usage of legacy vs new patterns
    - Automatic fallback mechanisms for unsupported operations

Example:
    ```python
    >>> # Existing code continues to work unchanged
    >>> old_cache = AIResponseCache()  # Legacy interface
    >>> wrapper = CompatibilityWrapper(
    ...     legacy_cache=old_cache,
    ...     new_cache=GenericRedisCache(),
    ...     mode="migration"  # Provides warnings but maintains compatibility
    ... )
    >>> 
    >>> # Legacy methods still work but internally use new implementation
    >>> result = await wrapper.get_ai_response(prompt_hash)
    >>> await wrapper.store_ai_response(prompt_hash, response, ttl=3600)
    ```

Note:
    This is a Phase-1 scaffolding stub. Implementation will be added in
    subsequent phases of the cache refactoring project. This wrapper is
    intended to be temporary and will be deprecated once migration is complete.
"""


import asyncio
import inspect
import logging
import warnings
from typing import Any, Dict, Optional

try:  # Optional typing aid in async detection during tests
    from unittest.mock import AsyncMock  # type: ignore
except Exception:  # pragma: no cover - not critical at runtime
    AsyncMock = None  # type: ignore

logger = logging.getLogger(__name__)


class CacheCompatibilityWrapper:
    """Wrapper class providing backwards compatibility during cache transitions.

    Acts as an adapter between old and new cache implementations, ensuring
    existing code continues to function while internally leveraging new cache
    infrastructure. Provides configurable compatibility modes and migration
    assistance.

    This wrapper is designed to be a temporary bridge during the refactoring
    process and should be removed once all code has been migrated to use the
    new cache interfaces directly.

    ### Parameters
    - `inner_cache` (Any): The underlying cache implementation to proxy to.
    - `emit_warnings` (bool): Whether to emit deprecation warnings. Default: True.

    ### Examples
    ```python
    generic_cache = GenericRedisCache()
    wrapper = CacheCompatibilityWrapper(generic_cache)

    # Legacy method calls emit warnings but still work
    result = await wrapper.get_cached_response(text, operation, options)
    ```
    """

    def __init__(self, inner_cache: Any, emit_warnings: bool = True):
        self._inner_cache = inner_cache
        self._emit_warnings = emit_warnings

    @staticmethod
    def _has_real_attr(obj: Any, name: str) -> bool:
        """Return True only if attribute truly exists on the object or its class.

        This avoids Mock instances auto-creating attributes on access.
        """
        try:
            if name in getattr(obj, "__dict__", {}):
                return True
            return hasattr(type(obj), name)
        except Exception:
            return False

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to inner cache with deprecation warnings.

        For legacy methods that should be migrated, emits a DeprecationWarning
        with guidance on the preferred new approach.

        ### Parameters
        - `name` (str): The attribute name being accessed.

        ### Returns
        The attribute from the inner cache, potentially wrapped with deprecation logic.
        """
        # Check if this is a known legacy method that should emit warnings
        legacy_methods = {
            "get_cached_response": "Use cache.get() with explicit key generation instead",
            "cache_response": "Use cache.set() with explicit key generation instead",
            "invalidate_pattern": "Use cache.delete() or direct Redis operations instead",
            "invalidate_by_operation": "Use cache.delete() with specific keys instead",
            "get_cache_stats": "Use cache performance monitoring methods instead",
            "get_cache_hit_ratio": "Access performance monitor directly instead",
        }

        # For non-legacy methods we want to proxy even on simple Mocks in tests,
        # so we allow attributes that exist on the instance dict OR class,
        # but we do not fabricate undefined attributes.
        if not (name in getattr(self._inner_cache, "__dict__", {}) or self._has_real_attr(self._inner_cache, name)):
            raise AttributeError(f"'{type(self._inner_cache).__name__}' object has no attribute '{name}'")
        attr = getattr(self._inner_cache, name)

        # If this is a legacy method and we should emit warnings
        if name in legacy_methods and self._emit_warnings:

            def wrapper(*args, **kwargs):
                warnings.warn(
                    f"Method '{name}' is deprecated and will be removed in a future version. "
                    f"{legacy_methods[name]}",
                    DeprecationWarning,
                    stacklevel=2,
                )
                logger.warning(
                    f"Legacy cache method '{name}' used. Please migrate to new cache interface."
                )
                return attr(*args, **kwargs)

            return wrapper

        # For non-legacy methods, return as-is
        return attr

    # Legacy methods that forward to new generic interface
    async def get_cached_response(
        self,
        text: str,
        operation: str,
        options: Dict[str, Any],
        question: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Legacy method for retrieving cached AI responses.

        **DEPRECATED**: Use `cache.get()` with explicit key generation instead.

        This method maintains backwards compatibility by forwarding to the AI-specific
        cache interface if available, or attempting to use generic cache methods.
        """
        if self._emit_warnings:
            warnings.warn(
                "get_cached_response() is deprecated. Use cache.get() with explicit key generation instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            logger.warning(
                "Legacy get_cached_response() method used. Please migrate to cache.get()."
            )

        # Try to use AI-specific method if available AND truly awaitable
        method = getattr(self._inner_cache, "get_cached_response", None)
        if method and callable(method) and self._has_real_attr(self._inner_cache, "get_cached_response"):
            is_async = asyncio.iscoroutinefunction(method)
            if not is_async and AsyncMock is not None:
                is_async = isinstance(method, AsyncMock)  # type: ignore[arg-type]
            if is_async:
                return await method(text, operation, options, question)

        # Fallback: attempt to construct key and use generic get
        instance_attrs = vars(self._inner_cache)
        if (
            "_generate_cache_key" in instance_attrs
            and ("get" in instance_attrs or self._has_real_attr(self._inner_cache, "get"))
        ):
            key = self._inner_cache._generate_cache_key(  # type: ignore[attr-defined]
                text, operation, options, question
            )
            return await self._inner_cache.get(key)  # type: ignore[attr-defined]

        raise NotImplementedError(
            "Inner cache does not support get_cached_response or generic get method"
        )

    async def cache_response(
        self,
        text: str,
        operation: str,
        options: Dict[str, Any],
        response: Dict[str, Any],
        question: Optional[str] = None,
    ) -> None:
        """Legacy method for caching AI responses.

        **DEPRECATED**: Use `cache.set()` with explicit key generation instead.

        This method maintains backwards compatibility by forwarding to the AI-specific
        cache interface if available, or attempting to use generic cache methods.
        """
        if self._emit_warnings:
            warnings.warn(
                "cache_response() is deprecated. Use cache.set() with explicit key generation instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            logger.warning(
                "Legacy cache_response() method used. Please migrate to cache.set()."
            )

        # Try to use AI-specific method if available AND truly awaitable
        method = getattr(self._inner_cache, "cache_response", None)
        if method and callable(method) and self._has_real_attr(self._inner_cache, "cache_response"):
            is_async = asyncio.iscoroutinefunction(method)
            if not is_async and AsyncMock is not None:
                is_async = isinstance(method, AsyncMock)  # type: ignore[arg-type]
            if is_async:
                await method(text, operation, options, response, question)
                return

        # Fallback: attempt to construct key and use generic set
        instance_attrs = vars(self._inner_cache)
        if (
            "_generate_cache_key" in instance_attrs
            and ("set" in instance_attrs or self._has_real_attr(self._inner_cache, "set"))
        ):
            key = self._inner_cache._generate_cache_key(  # type: ignore[attr-defined]
                text, operation, options, question
            )
            # Use operation-specific TTL if available
            ttl = None
            operation_ttls = getattr(self._inner_cache, "operation_ttls", None)
            if isinstance(operation_ttls, dict) and operation in operation_ttls:
                ttl = operation_ttls[operation]
            await self._inner_cache.set(key, response, ttl=ttl)  # type: ignore[attr-defined]
            return

        raise NotImplementedError(
            "Inner cache does not support cache_response or generic set method"
        )
