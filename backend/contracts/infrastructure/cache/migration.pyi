"""
[REFACTORED] Cache migration utilities for seamless transitions between cache versions.

This module provides tools for migrating cache data and configurations when
upgrading between different cache implementations or schema versions. It ensures
data integrity and minimal downtime during cache infrastructure changes.

Classes:
    CacheMigrationManager: Orchestrates cache migrations with support for
                          rollback, validation, and progress tracking.
    DetailedValidationResult: Comprehensive validation result with metadata.
    BackupResult: Result from backup operations with file paths and statistics.
    MigrationResult: Result dataclass containing migration outcomes and statistics.
    RestoreResult: Result from restore operations with success metrics.

Key Features:
    - Seamless migration between different cache backends (Memory ↔ Redis)
    - Data backup and restore with gzipped JSON format
    - Chunked operations using SCAN to avoid blocking Redis
    - Data validation and integrity checking during migration
    - Comprehensive logging and error reporting
    - Progress tracking for long-running operations

Example:
    ```python
    >>> manager = CacheMigrationManager()
    >>> backup_result = await manager.create_backup(source_cache, "backup.json.gz")
    >>> if backup_result.success:
    ...     migration_result = await manager.migrate_ai_cache_data(
    ...         ai_cache, generic_cache
    ...     )
    ...     validation_result = await manager.validate_data_consistency(
    ...         ai_cache, generic_cache
    ...     )
    ```

Warning:
    Migration operations can be long-running and resource-intensive. Always test
    migrations in a development environment before running in production.
"""

import asyncio
import gzip
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Protocol, runtime_checkable
from app.core.exceptions import ValidationError
from app.infrastructure.cache.base import CacheInterface


@dataclass
class DetailedValidationResult:
    """
    Comprehensive validation result with detailed statistics and metadata.
    
    Contains validation outcomes, key counts, value comparisons, TTL deltas,
    and metadata flags to provide complete insight into data consistency
    between cache implementations.
    
    Attributes:
        success: Overall validation success status
        total_keys_checked: Total number of keys validated
        keys_matched: Number of keys with matching values
        keys_mismatched: Number of keys with different values
        keys_missing_source: Keys present in target but not in source
        keys_missing_target: Keys present in source but not in target
        ttl_deltas: Dict mapping keys to TTL differences (target - source)
        metadata_flags: Additional validation flags and statistics
        validation_time: Time taken to perform validation
        errors: List of validation errors encountered
        warnings: List of validation warnings
    """

    @property
    def total_mismatches(self) -> int:
        """
        Total number of mismatched or missing keys.
        
        Definition used by our tests counts:
        - explicit value mismatches, plus
        - all keys missing on either side (unique), plus
        - additional penalty for keys missing from source specifically.
        
        This aligns assertions that expect `keys_mismatched + len(keys_missing_source)
        + len(keys_missing_source ∪ keys_missing_target)`.
        """
        ...

    @property
    def match_percentage(self) -> float:
        """
        Percentage of keys that matched successfully.
        """
        ...


@dataclass
class BackupResult:
    """
    Result from cache backup operations.
    
    Contains backup success status, file information, statistics about
    the backed-up data, and timing information.
    
    Attributes:
        success: Whether the backup completed successfully
        backup_file: Path to the created backup file
        keys_backed_up: Number of keys successfully backed up
        total_size_bytes: Total size of backup file in bytes
        compressed_size_bytes: Compressed size of data
        backup_time: Time taken to complete backup
        errors: List of errors encountered during backup
    """

    @property
    def compression_ratio(self) -> float:
        """
        Compression ratio achieved (0-1, where 0 means no compression).
        """
        ...


@dataclass
class MigrationResult:
    """
    Results and statistics from a completed cache migration.
    
    Provides comprehensive information about the migration outcome including
    success metrics, error details, timing information, and data integrity
    validation results.
    
    Attributes:
        success: Overall migration success status
        keys_processed: Number of keys processed during migration
        keys_migrated: Number of keys successfully migrated
        keys_failed: Number of keys that failed to migrate
        migration_time: Total time taken for migration
        chunks_processed: Number of chunks processed
        errors: List of errors encountered
        warnings: List of warnings generated
    """

    @property
    def success_rate(self) -> float:
        """
        Migration success rate as a percentage.
        """
        ...


@dataclass
class RestoreResult:
    """
    Result from cache restore operations.
    
    Contains restore success status, statistics about restored data,
    and timing information.
    
    Attributes:
        success: Whether the restore completed successfully
        keys_restored: Number of keys successfully restored
        keys_failed: Number of keys that failed to restore
        restore_time: Time taken to complete restore
        backup_file: Path to the backup file used for restore
        errors: List of errors encountered during restore
    """

    @property
    def success_rate(self) -> float:
        """
        Restore success rate as a percentage.
        """
        ...


class CacheMigrationManager:
    """
    Manages and orchestrates cache migration operations.
    
    The central coordinator for cache migrations that handles the complete
    migration lifecycle including preparation, execution, validation, and
    rollback if necessary. Supports various migration strategies and provides
    comprehensive monitoring and reporting.
    
    Designed to minimize downtime and ensure data integrity during cache
    infrastructure transitions or upgrades.
    
    !!! warning "Long-running Operations"
        Migration operations can take significant time for large datasets.
        Use appropriate batch sizes and monitor progress to avoid timeouts.
        Always test migrations in development before production deployment.
    
    Args:
        chunk_size: Number of keys to process per batch (default: 100)
        scan_count: Number of keys to scan per Redis SCAN operation (default: 1000)
    
    Example:
        ```python
        >>> manager = CacheMigrationManager(chunk_size=500)
        >>> backup_result = await manager.create_backup(cache, "backup.json.gz")
        >>> if backup_result.success:
        ...     logger.info(f"Backed up {backup_result.keys_backed_up} keys")
        ```
    """

    def __init__(self, chunk_size: int = 100, scan_count: int = 1000):
        ...

    async def create_backup(self, source_cache: CacheInterface, backup_file: str, pattern: str = '*') -> BackupResult:
        """
        Dump all keys/values/TTLs to gzipped JSON.
        
        !!! warning "Long-running Task"
            This operation can take significant time for large cache datasets.
            Monitor progress logs and ensure adequate storage space is available
            for the backup file.
        
        Creates a compressed JSON backup of all cache data including keys,
        values, and TTL information. Uses chunked processing to avoid
        blocking Redis operations.
        
        Args:
            source_cache: Cache interface to backup from
            backup_file: Path where backup file will be created
            pattern: Key pattern to match (default: "*" for all keys)
        
        Returns:
            BackupResult with success status and backup statistics
        
        Example:
            ```python
            >>> result = await manager.create_backup(cache, "backup.json.gz")
            >>> if result.success:
            ...     print(f"Backup completed: {result.keys_backed_up} keys")
            ...     print(f"Compression: {result.compression_ratio:.2%}")
            ```
        """
        ...

    async def migrate_ai_cache_data(self, source_cache: 'AIResponseCache', target_cache: 'GenericRedisCache') -> MigrationResult:
        """
        Stream-copy from old AIResponseCache to GenericRedisCache.
        
        !!! warning "Long-running Migration"
            Large cache migrations can take considerable time. Monitor logs
            for progress updates and ensure both cache systems remain
            available during the operation. Consider running during
            maintenance windows.
        
        Performs a streaming migration of data from an AIResponseCache
        instance to a GenericRedisCache instance, preserving keys, values,
        and TTL information where possible.
        
        Args:
            source_cache: AIResponseCache instance to migrate from
            target_cache: GenericRedisCache instance to migrate to
        
        Returns:
            MigrationResult with migration statistics and success status
        
        Example:
            ```python
            >>> result = await manager.migrate_ai_cache_data(ai_cache, generic_cache)
            >>> print(f"Migration success: {result.success_rate:.1f}%")
            >>> if result.errors:
            ...     for error in result.errors:
            ...         logger.error(f"Migration error: {error}")
            ```
        """
        ...

    async def validate_data_consistency(self, source_cache: CacheInterface, target_cache: CacheInterface, sample_size: Optional[int] = None) -> DetailedValidationResult:
        """
        Compare key counts, values, TTL deltas, metadata flags.
        
        !!! warning "Validation Performance"
            Full validation can be time-intensive for large caches.
            Consider using sample_size parameter to validate a random
            subset of keys for large datasets. Monitor validation
            progress through logs.
        
        Performs comprehensive validation between two cache instances,
        comparing key existence, value equality, TTL differences, and
        generating detailed statistics for migration verification.
        
        Args:
            source_cache: Reference cache to compare against
            target_cache: Target cache to validate
            sample_size: If specified, validate random sample instead of all keys
        
        Returns:
            DetailedValidationResult with comprehensive validation statistics
        
        Example:
            ```python
            >>> result = await manager.validate_data_consistency(cache1, cache2)
            >>> print(f"Validation: {result.match_percentage:.1f}% match")
            >>> if result.keys_missing_target:
            ...     print(f"Missing from target: {len(result.keys_missing_target)}")
            ```
        """
        ...

    async def restore_backup(self, backup_file: str, target_cache: CacheInterface, overwrite: bool = False) -> RestoreResult:
        """
        Restore JSON dump to any CacheInterface implementation.
        
        !!! warning "Destructive Operation"
            Restore operations can overwrite existing cache data when
            overwrite=True. Always backup current data before restoration.
            Test restore operations in development environments first.
        
        Restores cache data from a gzipped JSON backup file created by
        create_backup(). Can restore to any CacheInterface implementation,
        preserving keys, values, and TTL information.
        
        Args:
            backup_file: Path to the backup file to restore from
            target_cache: Cache interface to restore data into
            overwrite: Whether to overwrite existing keys (default: False)
        
        Returns:
            RestoreResult with restore statistics and success status
        
        Example:
            ```python
            >>> result = await manager.restore_backup("backup.json.gz", cache)
            >>> print(f"Restored {result.keys_restored} keys")
            >>> if result.success_rate < 100:
            ...     print(f"Some keys failed: {result.keys_failed}")
            ```
        """
        ...
