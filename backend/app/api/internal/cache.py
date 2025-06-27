"""
REST API endpoints for cache infrastructure.

Provides endpoints for:
- Getting cache status and statistics
- Invalidating cache entries
- Getting invalidation statistics and recommendations
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_cache_service
from app.infrastructure.cache import AIResponseCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.security import verify_api_key, optional_verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


# Pydantic models for cache performance metrics
class CacheKeyGenerationStats(BaseModel):
    """Statistics for cache key generation operations."""
    total_operations: int = Field(..., description="Total number of key generation operations")
    avg_duration: float = Field(..., description="Average key generation time in seconds")
    median_duration: float = Field(..., description="Median key generation time in seconds")
    max_duration: float = Field(..., description="Maximum key generation time in seconds")
    min_duration: float = Field(..., description="Minimum key generation time in seconds")
    avg_text_length: float = Field(..., description="Average text length processed")
    max_text_length: int = Field(..., description="Maximum text length processed")
    slow_operations: int = Field(..., description="Number of operations exceeding threshold")


class CacheOperationTypeStats(BaseModel):
    """Statistics for a specific cache operation type."""
    count: int = Field(..., description="Number of operations of this type")
    avg_duration: float = Field(..., description="Average duration for this operation type")
    max_duration: float = Field(..., description="Maximum duration for this operation type")


class CacheOperationStats(BaseModel):
    """Statistics for cache operations."""
    total_operations: int = Field(..., description="Total number of cache operations")
    avg_duration: float = Field(..., description="Average operation duration in seconds")
    median_duration: float = Field(..., description="Median operation duration in seconds")
    max_duration: float = Field(..., description="Maximum operation duration in seconds")
    min_duration: float = Field(..., description="Minimum operation duration in seconds")
    slow_operations: int = Field(..., description="Number of operations exceeding threshold")
    by_operation_type: Dict[str, CacheOperationTypeStats] = Field(..., description="Stats grouped by operation type")


class CompressionStats(BaseModel):
    """Statistics for compression operations."""
    total_operations: int = Field(..., description="Total number of compression operations")
    avg_compression_ratio: float = Field(..., description="Average compression ratio")
    median_compression_ratio: float = Field(..., description="Median compression ratio")
    best_compression_ratio: float = Field(..., description="Best (lowest) compression ratio")
    worst_compression_ratio: float = Field(..., description="Worst (highest) compression ratio")
    avg_compression_time: float = Field(..., description="Average compression time in seconds")
    max_compression_time: float = Field(..., description="Maximum compression time in seconds")
    total_bytes_processed: int = Field(..., description="Total bytes processed for compression")
    total_bytes_saved: int = Field(..., description="Total bytes saved through compression")
    overall_savings_percent: float = Field(..., description="Overall storage savings percentage")


class CachePerformanceResponse(BaseModel):
    """Comprehensive cache performance metrics response."""
    timestamp: str = Field(..., description="Timestamp when metrics were collected")
    retention_hours: int = Field(..., description="Data retention period in hours")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    total_cache_operations: int = Field(..., description="Total cache operations performed")
    cache_hits: int = Field(..., description="Number of cache hits")
    cache_misses: int = Field(..., description="Number of cache misses")
    key_generation: Optional[CacheKeyGenerationStats] = Field(None, description="Key generation statistics")
    cache_operations: Optional[CacheOperationStats] = Field(None, description="Cache operation statistics")
    compression: Optional[CompressionStats] = Field(None, description="Compression statistics")
    memory_usage: Optional[Dict[str, Any]] = Field(None, description="Memory usage statistics")
    invalidation: Optional[Dict[str, Any]] = Field(None, description="Cache invalidation statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00.123456",
                "retention_hours": 1,
                "cache_hit_rate": 85.5,
                "total_cache_operations": 150,
                "cache_hits": 128,
                "cache_misses": 22,
                "key_generation": {
                    "total_operations": 75,
                    "avg_duration": 0.002,
                    "median_duration": 0.0015,
                    "max_duration": 0.012,
                    "min_duration": 0.0008,
                    "avg_text_length": 1250,
                    "max_text_length": 5000,
                    "slow_operations": 2
                },
                "cache_operations": {
                    "total_operations": 150,
                    "avg_duration": 0.0045,
                    "median_duration": 0.003,
                    "max_duration": 0.025,
                    "min_duration": 0.001,
                    "slow_operations": 5,
                    "by_operation_type": {
                        "get": {
                            "count": 100,
                            "avg_duration": 0.003,
                            "max_duration": 0.015
                        },
                        "set": {
                            "count": 50,
                            "avg_duration": 0.007,
                            "max_duration": 0.025
                        }
                    }
                },
                "compression": {
                    "total_operations": 25,
                    "avg_compression_ratio": 0.65,
                    "median_compression_ratio": 0.62,
                    "best_compression_ratio": 0.45,
                    "worst_compression_ratio": 0.89,
                    "avg_compression_time": 0.003,
                    "max_compression_time": 0.015,
                    "total_bytes_processed": 524288,
                    "total_bytes_saved": 183500,
                    "overall_savings_percent": 35.0
                }
            }
        }


# For cache endpoints, we'll use flexible response models that can handle
# the dynamic nature of cache statistics


# Most cache responses will be flexible dictionaries to accommodate
# the dynamic nature of cache statistics and service responses


# Dependency functions
async def get_performance_monitor(
    cache_service: AIResponseCache = Depends(get_cache_service)
) -> CachePerformanceMonitor:
    """
    Dependency to get the cache performance monitor from the cache service.
    
    Args:
        cache_service: Injected cache service with performance monitor
        
    Returns:
        CachePerformanceMonitor: The performance monitor instance
    """
    return cache_service.performance_monitor


@router.get("/status")
async def get_cache_status(
    cache_service: AIResponseCache = Depends(get_cache_service),
    api_key: str = Depends(optional_verify_api_key)
):
    """
    Get cache status and statistics.
    
    Returns:
        Current cache statistics in the format provided by the cache service
    """
    try:
        stats = await cache_service.get_cache_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        # Return a basic error response 
        return {
            "redis": {"status": "error"},
            "memory": {"status": "unavailable"},
            "performance": {"status": "unavailable"},
            "error": str(e)
        }


@router.post("/invalidate")
async def invalidate_cache(
    pattern: str = Query(default="", description="Pattern to match for cache invalidation"),
    operation_context: str = Query(default="api_endpoint", description="Context for the invalidation operation"),
    cache_service: AIResponseCache = Depends(get_cache_service),
    api_key: str = Depends(verify_api_key)
):
    """
    Invalidate cache entries matching the specified pattern.
    
    Args:
        pattern: Pattern to match for cache invalidation (empty string invalidates all)
        operation_context: Context for the invalidation operation
        
    Returns:
        Confirmation message with invalidation details
    """
    try:
        await cache_service.invalidate_pattern(pattern, operation_context=operation_context)
        
        return {"message": f"Cache invalidated for pattern: {pattern}"}
        
    except Exception as e:
        logger.error(f"Error invalidating cache with pattern '{pattern}': {e}")
        # Return error message in response rather than raising exception
        return {"message": f"Failed to invalidate cache for pattern '{pattern}': {str(e)}"}


@router.get("/invalidation-stats")
async def get_invalidation_stats(
    cache_service: AIResponseCache = Depends(get_cache_service),
    api_key: str = Depends(optional_verify_api_key)
):
    """
    Get cache invalidation frequency statistics.
    
    Returns:
        Statistics about cache invalidation patterns and frequency
    """
    try:
        stats = cache_service.get_invalidation_frequency_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting invalidation stats: {e}")
        # Return empty stats on error rather than raising exception
        return {}


@router.get("/invalidation-recommendations")
async def get_invalidation_recommendations(
    cache_service: AIResponseCache = Depends(get_cache_service),
    api_key: str = Depends(optional_verify_api_key)
):
    """
    Get recommendations based on cache invalidation patterns.
    
    Returns:
        List of recommendations for optimizing cache invalidation
    """
    try:
        recommendations = cache_service.get_invalidation_recommendations()
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"Error getting invalidation recommendations: {e}")
        # Return empty recommendations on error rather than raising exception
        return {"recommendations": []}


@router.get(
    "/metrics",
    response_model=CachePerformanceResponse,
    summary="Get Cache Performance Metrics",
    description="Retrieve comprehensive cache performance statistics including key generation times, cache operation metrics, compression ratios, and memory usage.",
    responses={
        200: {
            "description": "Successfully retrieved cache performance metrics",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2024-01-15T10:30:00.123456",
                        "retention_hours": 1,
                        "cache_hit_rate": 85.5,
                        "total_cache_operations": 150,
                        "cache_hits": 128,
                        "cache_misses": 22,
                        "key_generation": {
                            "total_operations": 75,
                            "avg_duration": 0.002,
                            "median_duration": 0.0015,
                            "max_duration": 0.012,
                            "min_duration": 0.0008,
                            "avg_text_length": 1250,
                            "max_text_length": 5000,
                            "slow_operations": 2
                        },
                        "cache_operations": {
                            "total_operations": 150,
                            "avg_duration": 0.0045,
                            "median_duration": 0.003,
                            "max_duration": 0.025,
                            "min_duration": 0.001,
                            "slow_operations": 5,
                            "by_operation_type": {
                                "get": {"count": 100, "avg_duration": 0.003, "max_duration": 0.015},
                                "set": {"count": 50, "avg_duration": 0.007, "max_duration": 0.025}
                            }
                        },
                        "compression": {
                            "total_operations": 25,
                            "avg_compression_ratio": 0.65,
                            "median_compression_ratio": 0.62,
                            "best_compression_ratio": 0.45,
                            "worst_compression_ratio": 0.89,
                            "avg_compression_time": 0.003,
                            "max_compression_time": 0.015,
                            "total_bytes_processed": 524288,
                            "total_bytes_saved": 183500,
                            "overall_savings_percent": 35.0
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error - Performance monitor unavailable or failed",
            "content": {
                "application/json": {
                    "examples": {
                        "monitor_not_initialized": {
                            "summary": "Performance monitor not initialized",
                            "value": {
                                "detail": "Failed to retrieve cache performance metrics: Performance monitor not available"
                            }
                        },
                        "cache_service_error": {
                            "summary": "Cache service dependency failure",
                            "value": {
                                "detail": "Failed to retrieve cache performance metrics: Cache service not available"
                            }
                        },
                        "stats_computation_error": {
                            "summary": "Error computing statistics",
                            "value": {
                                "detail": "Failed to retrieve cache performance metrics: Statistics computation failed"
                            }
                        }
                    }
                }
            }
        },
        503: {
            "description": "Service temporarily unavailable - Cache monitoring disabled",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cache performance monitoring is temporarily disabled"
                    }
                }
            }
        }
    }
)
async def get_cache_performance_metrics(
    api_key: str = Depends(optional_verify_api_key),
    performance_monitor: CachePerformanceMonitor = Depends(get_performance_monitor)
) -> CachePerformanceResponse:
    """
    Get comprehensive cache performance metrics.
    
    This endpoint retrieves detailed performance statistics from the cache system,
    including:
    
    **Key Generation Metrics:**
    - Average, median, min, and max key generation times
    - Text length statistics for cached content
    - Count of slow operations exceeding performance thresholds
    
    **Cache Operation Metrics:**
    - Hit/miss rates and operation counts
    - Performance timing by operation type (get, set, delete)
    - Identification of slow cache operations
    
    **Compression Statistics:**
    - Compression ratios and efficiency metrics
    - Compression time performance
    - Storage savings achieved through compression
    
    **Memory Usage Information:**
    - Cache memory utilization and entry counts
    - Process memory consumption
    - Memory warning threshold status
    
    **Invalidation Statistics:**
    - Cache invalidation frequency and patterns
    - Invalidation performance metrics
    - Recommendations for optimization
    
    The metrics are collected over the configured retention period (default: 1 hour)
    and provide insights into cache efficiency and performance characteristics.
    Metrics are automatically cleaned up to maintain system performance.
    
    **Performance Considerations:**
    - This endpoint may take longer to respond when computing statistics for large datasets
    - Statistics are computed on-demand and may cause brief CPU spikes
    - Memory usage reporting includes process-level metrics
    
    Returns:
        CachePerformanceResponse: Comprehensive performance metrics including all available statistics
        
    Raises:
        HTTPException: 
            - 500: Performance monitor unavailable, cache service error, or statistics computation failure
            - 503: Cache monitoring temporarily disabled or service unavailable
    """
    try:
        # Check if performance monitor is available
        if performance_monitor is None:
            logger.error("Performance monitor dependency is None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cache performance metrics: Performance monitor not available"
            )
        
        logger.debug("Retrieving cache performance statistics")
        
        # Get performance stats from the monitor with error handling for computation issues
        try:
            stats = performance_monitor.get_performance_stats()
        except (ValueError, ZeroDivisionError) as e:
            # Handle specific mathematical errors that might occur during stats computation
            logger.error(f"Statistics computation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cache performance metrics: Statistics computation failed"
            )
        except AttributeError as e:
            # Handle cases where performance monitor methods are not available
            logger.error(f"Performance monitor method unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache performance monitoring is temporarily disabled"
            )
        except Exception as e:
            # Handle any other unexpected errors during stats retrieval
            logger.error(f"Unexpected error retrieving performance stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve cache performance metrics: {str(e)}"
            )
        
        # Validate that we received stats data
        if not isinstance(stats, dict):
            logger.error(f"Invalid stats format received: {type(stats)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cache performance metrics: Invalid statistics format"
            )
        
        logger.debug(f"Successfully retrieved {len(stats)} performance metrics")
        
        # Convert to Pydantic model for validation and documentation
        try:
            return CachePerformanceResponse(**stats)
        except (ValueError, TypeError) as e:
            # Handle Pydantic validation errors
            logger.error(f"Response model validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cache performance metrics: Response format validation failed"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Catch-all for any other unexpected errors
        logger.error(f"Unexpected error in cache metrics endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache performance metrics: Internal server error"
        )
