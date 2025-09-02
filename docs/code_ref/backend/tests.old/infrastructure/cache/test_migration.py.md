---
sidebar_label: test_migration
---

# Comprehensive tests for cache migration utilities.

  file_path: `backend/tests.old/infrastructure/cache/test_migration.py`

Tests all migration functionality with Docker Redis instances and mock caches
to ensure high test coverage (≥90%) and robust functionality validation.

## MockCache

Mock cache implementation for testing.

### __init__()

```python
def __init__(self):
```

### get()

```python
async def get(self, key: str):
```

### set()

```python
async def set(self, key: str, value: Any, ttl: Optional[int] = None):
```

### delete()

```python
async def delete(self, key: str):
```

## MockRedisCache

Mock Redis-like cache for testing.

### __init__()

```python
def __init__(self):
```

### get()

```python
async def get(self, key: str):
```

### set()

```python
async def set(self, key: str, value: Any, ttl: Optional[int] = None):
```

### delete()

```python
async def delete(self, key: str):
```

## TestDetailedValidationResult

Test the DetailedValidationResult dataclass.

### test_detailed_validation_result_properties()

```python
def test_detailed_validation_result_properties(self):
```

Test computed properties of DetailedValidationResult.

### test_detailed_validation_result_zero_keys()

```python
def test_detailed_validation_result_zero_keys(self):
```

Test properties with zero keys checked.

## TestBackupResult

Test the BackupResult dataclass.

### test_backup_result_compression_ratio()

```python
def test_backup_result_compression_ratio(self):
```

Test compression ratio calculation.

### test_backup_result_no_compression()

```python
def test_backup_result_no_compression(self):
```

Test compression ratio with zero size.

## TestMigrationResult

Test the MigrationResult dataclass.

### test_migration_result_success_rate()

```python
def test_migration_result_success_rate(self):
```

Test success rate calculation.

### test_migration_result_zero_processed()

```python
def test_migration_result_zero_processed(self):
```

Test success rate with zero keys processed.

## TestRestoreResult

Test the RestoreResult dataclass.

### test_restore_result_success_rate()

```python
def test_restore_result_success_rate(self):
```

Test success rate calculation.

### test_restore_result_zero_keys()

```python
def test_restore_result_zero_keys(self):
```

Test success rate with zero keys.

## TestCacheMigrationManager

Comprehensive tests for CacheMigrationManager.

### manager()

```python
def manager(self):
```

Create a migration manager instance.

### mock_cache()

```python
def mock_cache(self):
```

Create a mock cache with test data.

### mock_redis_cache()

```python
def mock_redis_cache(self):
```

Create a mock Redis cache with test data.

### temp_file()

```python
def temp_file(self):
```

Create a temporary file for testing.

### test_create_backup_success()

```python
async def test_create_backup_success(self, manager, mock_cache, temp_file):
```

Test successful backup creation.

### test_create_backup_with_pattern()

```python
async def test_create_backup_with_pattern(self, manager, mock_cache, temp_file):
```

Test backup creation with key pattern filtering.

### test_create_backup_redis_cache()

```python
async def test_create_backup_redis_cache(self, manager, mock_redis_cache, temp_file):
```

Test backup with Redis cache using SCAN.

### test_create_backup_error_handling()

```python
async def test_create_backup_error_handling(self, manager, temp_file):
```

Test backup error handling.

### test_migrate_ai_cache_data_success()

```python
async def test_migrate_ai_cache_data_success(self, manager):
```

Test successful AI cache migration.

### test_migrate_ai_cache_data_memory_cache()

```python
async def test_migrate_ai_cache_data_memory_cache(self, manager):
```

Test migration from memory cache when Redis is unavailable.

### test_migrate_ai_cache_data_with_errors()

```python
async def test_migrate_ai_cache_data_with_errors(self, manager):
```

Test migration with some key failures.

### test_validate_data_consistency_perfect_match()

```python
async def test_validate_data_consistency_perfect_match(self, manager):
```

Test validation with perfectly matching caches.

### test_validate_data_consistency_with_differences()

```python
async def test_validate_data_consistency_with_differences(self, manager):
```

Test validation with cache differences.

### test_validate_data_consistency_with_sampling()

```python
async def test_validate_data_consistency_with_sampling(self, manager):
```

Test validation with random sampling.

### test_validate_data_consistency_with_ttl_deltas()

```python
async def test_validate_data_consistency_with_ttl_deltas(self, manager):
```

Test validation with TTL differences.

### test_restore_backup_success()

```python
async def test_restore_backup_success(self, manager, temp_file):
```

Test successful backup restoration.

### test_restore_backup_no_overwrite()

```python
async def test_restore_backup_no_overwrite(self, manager, temp_file):
```

Test restoration without overwriting existing keys.

### test_restore_backup_invalid_file()

```python
async def test_restore_backup_invalid_file(self, manager, temp_file):
```

Test restoration with invalid backup file.

### test_restore_backup_with_failures()

```python
async def test_restore_backup_with_failures(self, manager, temp_file):
```

Test restoration with some key failures.

### test_scan_redis_keys()

```python
async def test_scan_redis_keys(self, manager):
```

Test Redis key scanning with pagination.

### test_get_all_cache_keys_redis()

```python
async def test_get_all_cache_keys_redis(self, manager):
```

Test getting all keys from Redis cache.

### test_get_all_cache_keys_memory()

```python
async def test_get_all_cache_keys_memory(self, manager):
```

Test getting all keys from memory cache.

### test_get_key_ttl_redis()

```python
async def test_get_key_ttl_redis(self, manager):
```

Test getting TTL from Redis cache.

### test_get_key_ttl_no_redis()

```python
async def test_get_key_ttl_no_redis(self, manager):
```

Test getting TTL from non-Redis cache.

### test_match_pattern()

```python
def test_match_pattern(self, manager):
```

Test pattern matching functionality.

## TestMigrationWithRedis

Integration tests using actual Redis instances.

### redis_cache()

```python
async def redis_cache(self, redis_proc):
```

Create Redis cache with actual Redis instance.

### generic_redis_cache()

```python
async def generic_redis_cache(self, redis_proc):
```

Create generic Redis cache with actual Redis instance.

### test_full_migration_workflow()

```python
async def test_full_migration_workflow(self, redis_cache, generic_redis_cache, tmp_path):
```

Test complete migration workflow with real Redis.

### test_migration_with_large_dataset()

```python
async def test_migration_with_large_dataset(self, redis_cache, generic_redis_cache):
```

Test migration performance with larger dataset.

### test_backup_restore_round_trip()

```python
async def test_backup_restore_round_trip(self, redis_cache, tmp_path):
```

Test backup and restore round trip preserves data integrity.
