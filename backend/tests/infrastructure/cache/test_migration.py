"""
Comprehensive tests for cache migration utilities.

Tests all migration functionality with Docker Redis instances and mock caches
to ensure high test coverage (≥90%) and robust functionality validation.
"""
import gzip
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional

import pytest
import pytest_asyncio

from app.infrastructure.cache.migration import (
    CacheMigrationManager,
    DetailedValidationResult,
    BackupResult,
    MigrationResult,
    RestoreResult
)
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.redis import AIResponseCache
from app.infrastructure.cache.redis_generic import GenericRedisCache


class MockCache(CacheInterface):
    """Mock cache implementation for testing."""
    
    def __init__(self):
        self.data = {}
        self.ttls = {}
        
    async def get(self, key: str):
        return self.data.get(key)
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self.data[key] = value
        if ttl:
            self.ttls[key] = ttl
            
    async def delete(self, key: str):
        self.data.pop(key, None)
        self.ttls.pop(key, None)


class MockRedisCache(CacheInterface):
    """Mock Redis-like cache for testing."""
    
    def __init__(self):
        self.data = {}
        self.ttls = {}
        self.redis = AsyncMock()
        self.memory_cache = {}
        
        # Setup redis mock methods
        self.redis.scan = AsyncMock()
        self.redis.ttl = AsyncMock()
        
    async def get(self, key: str):
        return self.data.get(key)
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self.data[key] = value
        if ttl:
            self.ttls[key] = ttl
            
    async def delete(self, key: str):
        self.data.pop(key, None)
        self.ttls.pop(key, None)


class TestDetailedValidationResult:
    """Test the DetailedValidationResult dataclass."""
    
    def test_detailed_validation_result_properties(self):
        """Test computed properties of DetailedValidationResult."""
        result = DetailedValidationResult(
            success=True,
            total_keys_checked=100,
            keys_matched=80,
            keys_mismatched=10,
            keys_missing_source={'key1', 'key2'},
            keys_missing_target={'key3', 'key4', 'key5'}
        )
        
        assert result.total_mismatches == 17  # 10 + 2 + 5
        assert result.match_percentage == 80.0  # 80/100 * 100
        
    def test_detailed_validation_result_zero_keys(self):
        """Test properties with zero keys checked."""
        result = DetailedValidationResult(
            success=False,
            total_keys_checked=0,
            keys_matched=0,
            keys_mismatched=0
        )
        
        assert result.total_mismatches == 0
        assert result.match_percentage == 0.0


class TestBackupResult:
    """Test the BackupResult dataclass."""
    
    def test_backup_result_compression_ratio(self):
        """Test compression ratio calculation."""
        result = BackupResult(
            success=True,
            total_size_bytes=1000,
            compressed_size_bytes=300
        )
        
        assert result.compression_ratio == 0.7  # 1 - (300/1000)
        
    def test_backup_result_no_compression(self):
        """Test compression ratio with zero size."""
        result = BackupResult(
            success=True,
            total_size_bytes=0,
            compressed_size_bytes=0
        )
        
        assert result.compression_ratio == 0.0


class TestMigrationResult:
    """Test the MigrationResult dataclass."""
    
    def test_migration_result_success_rate(self):
        """Test success rate calculation."""
        result = MigrationResult(
            success=False,
            keys_processed=100,
            keys_migrated=85,
            keys_failed=15,
            migration_time=60.0
        )
        
        assert result.success_rate == 85.0  # 85/100 * 100
        
    def test_migration_result_zero_processed(self):
        """Test success rate with zero keys processed."""
        result = MigrationResult(
            success=True,
            keys_processed=0,
            keys_migrated=0,
            keys_failed=0,
            migration_time=0.0
        )
        
        assert result.success_rate == 0.0


class TestRestoreResult:
    """Test the RestoreResult dataclass."""
    
    def test_restore_result_success_rate(self):
        """Test success rate calculation."""
        result = RestoreResult(
            success=False,
            keys_restored=75,
            keys_failed=25,
            restore_time=30.0
        )
        
        assert result.success_rate == 75.0  # 75/100 * 100
        
    def test_restore_result_zero_keys(self):
        """Test success rate with zero keys."""
        result = RestoreResult(
            success=True,
            keys_restored=0,
            keys_failed=0,
            restore_time=0.0
        )
        
        assert result.success_rate == 0.0


class TestCacheMigrationManager:
    """Comprehensive tests for CacheMigrationManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a migration manager instance."""
        return CacheMigrationManager(chunk_size=10, scan_count=100)
    
    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache with test data."""
        cache = MockCache()
        cache.data = {
            'key1': {'value': 'data1'},
            'key2': {'value': 'data2'},
            'key3': {'value': 'data3'}
        }
        cache.ttls = {'key1': 300, 'key2': 600}
        return cache
    
    @pytest.fixture
    def mock_redis_cache(self):
        """Create a mock Redis cache with test data."""
        cache = MockRedisCache()
        cache.data = {
            'ai_cache:test1': {'response': 'result1'},
            'ai_cache:test2': {'response': 'result2'},
            'other:key': {'data': 'value'}
        }
        return cache
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        fd, path = tempfile.mkstemp(suffix='.json.gz')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    # Test create_backup method
    
    @pytest.mark.asyncio
    async def test_create_backup_success(self, manager, mock_cache, temp_file):
        """Test successful backup creation."""
        result = await manager.create_backup(mock_cache, temp_file)
        
        assert result.success is True
        assert result.keys_backed_up == 3
        assert result.backup_file == temp_file
        assert result.backup_time > 0
        assert os.path.exists(temp_file)
        
        # Verify backup content
        with gzip.open(temp_file, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert 'metadata' in backup_data
        assert 'keys' in backup_data
        assert len(backup_data['keys']) == 3
        assert 'key1' in backup_data['keys']
        assert backup_data['keys']['key1']['value'] == {'value': 'data1'}
        
    @pytest.mark.asyncio
    async def test_create_backup_with_pattern(self, manager, mock_cache, temp_file):
        """Test backup creation with key pattern filtering."""
        # Add more keys to test pattern matching
        mock_cache.data.update({
            'prefix:key1': {'data': 'value1'},
            'prefix:key2': {'data': 'value2'},
            'other:key': {'data': 'other'}
        })
        
        result = await manager.create_backup(mock_cache, temp_file, pattern='prefix:*')
        
        assert result.success is True
        assert result.keys_backed_up == 2
        
        # Verify only prefix keys were backed up
        with gzip.open(temp_file, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        backed_up_keys = list(backup_data['keys'].keys())
        assert 'prefix:key1' in backed_up_keys
        assert 'prefix:key2' in backed_up_keys
        assert 'other:key' not in backed_up_keys
    
    @pytest.mark.asyncio
    async def test_create_backup_redis_cache(self, manager, mock_redis_cache, temp_file):
        """Test backup with Redis cache using SCAN."""
        # Mock the Redis SCAN behavior
        mock_redis_cache.redis.scan.side_effect = [
            (0, [b'ai_cache:test1', b'ai_cache:test2', b'other:key'])
        ]
        
        with patch.object(manager, '_scan_redis_keys', return_value=['ai_cache:test1', 'ai_cache:test2', 'other:key']):
            result = await manager.create_backup(mock_redis_cache, temp_file)
        
        assert result.success is True
        assert result.keys_backed_up == 3
    
    @pytest.mark.asyncio
    async def test_create_backup_error_handling(self, manager, temp_file):
        """Test backup error handling."""
        failing_cache = MockCache()
        
        # Make the cache.get method fail
        with patch.object(failing_cache, 'get', side_effect=Exception('Cache error')):
            failing_cache.data = {'key1': 'value1'}
            result = await manager.create_backup(failing_cache, temp_file)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert 'Backup failed' in result.errors[0]

    # Test migrate_ai_cache_data method
    
    @pytest.mark.asyncio
    async def test_migrate_ai_cache_data_success(self, manager):
        """Test successful AI cache migration."""
        source_cache = MockRedisCache()
        target_cache = MockCache()
        
        # Setup source cache data
        source_cache.data = {
            'ai_cache:key1': {'response': 'result1'},
            'ai_cache:key2': {'response': 'result2'}
        }
        source_cache.ttls = {'ai_cache:key1': 300}
        
        # Mock Redis operations
        with patch.object(manager, '_scan_redis_keys', return_value=['ai_cache:key1', 'ai_cache:key2']):
            with patch.object(manager, '_get_key_ttl', side_effect=[300, None]):
                result = await manager.migrate_ai_cache_data(source_cache, target_cache)
        
        assert result.success is True
        assert result.keys_processed == 2
        assert result.keys_migrated == 2
        assert result.keys_failed == 0
        assert result.chunks_processed == 1
        
        # Verify data was migrated to target
        assert len(target_cache.data) == 2
        assert target_cache.data['ai_cache:key1'] == {'response': 'result1'}
        assert target_cache.ttls['ai_cache:key1'] == 300
    
    @pytest.mark.asyncio
    async def test_migrate_ai_cache_data_memory_cache(self, manager):
        """Test migration from memory cache when Redis is unavailable."""
        source_cache = MockCache()
        target_cache = MockCache()
        
        # Setup memory cache data
        source_cache.memory_cache = {
            'ai_cache:key1': {'response': 'result1'},
            'key2': {'response': 'result2'}
        }
        source_cache.data = source_cache.memory_cache
        
        result = await manager.migrate_ai_cache_data(source_cache, target_cache)
        
        assert result.keys_processed == 2
        assert result.keys_migrated == 2
        assert len(result.warnings) == 0
    
    @pytest.mark.asyncio
    async def test_migrate_ai_cache_data_with_errors(self, manager):
        """Test migration with some key failures."""
        source_cache = MockRedisCache()
        target_cache = MockCache()
        
        source_cache.data = {
            'ai_cache:key1': {'response': 'result1'},
            'ai_cache:key2': {'response': 'result2'}
        }
        
        # Make target cache fail on second key
        async def failing_set(key, value, ttl=None):
            if key == 'ai_cache:key2':
                raise Exception('Set failed')
            target_cache.data[key] = value
        
        target_cache.set = failing_set
        
        with patch.object(manager, '_scan_redis_keys', return_value=['ai_cache:key1', 'ai_cache:key2']):
            result = await manager.migrate_ai_cache_data(source_cache, target_cache)
        
        assert result.success is False
        assert result.keys_migrated == 1
        assert result.keys_failed == 1
        assert len(result.errors) == 1

    # Test validate_data_consistency method
    
    @pytest.mark.asyncio
    async def test_validate_data_consistency_perfect_match(self, manager):
        """Test validation with perfectly matching caches."""
        cache1 = MockCache()
        cache2 = MockCache()
        
        # Setup identical data
        test_data = {
            'key1': {'data': 'value1'},
            'key2': {'data': 'value2'}
        }
        cache1.data = test_data.copy()
        cache2.data = test_data.copy()
        
        with patch.object(manager, '_get_all_cache_keys', side_effect=[['key1', 'key2'], ['key1', 'key2']]):
            result = await manager.validate_data_consistency(cache1, cache2)
        
        assert result.success is True
        assert result.total_keys_checked == 2
        assert result.keys_matched == 2
        assert result.keys_mismatched == 0
        assert len(result.keys_missing_source) == 0
        assert len(result.keys_missing_target) == 0
        assert result.match_percentage == 100.0
    
    @pytest.mark.asyncio
    async def test_validate_data_consistency_with_differences(self, manager):
        """Test validation with cache differences."""
        cache1 = MockCache()
        cache2 = MockCache()
        
        cache1.data = {
            'key1': {'data': 'value1'},
            'key2': {'data': 'value2'},
            'key3': {'data': 'value3'}  # Only in cache1
        }
        cache2.data = {
            'key1': {'data': 'value1'},
            'key2': {'data': 'different'},  # Different value
            'key4': {'data': 'value4'}  # Only in cache2
        }
        
        with patch.object(manager, '_get_all_cache_keys', side_effect=[['key1', 'key2', 'key3'], ['key1', 'key2', 'key4']]):
            result = await manager.validate_data_consistency(cache1, cache2)
        
        assert result.success is False
        assert result.keys_matched == 1  # Only key1 matches
        assert result.keys_mismatched == 1  # key2 is different
        assert 'key3' in result.keys_missing_target
        assert 'key4' in result.keys_missing_source
        assert result.total_keys_checked == 4  # 2 common + 1 missing from target + 1 missing from source
    
    @pytest.mark.asyncio
    async def test_validate_data_consistency_with_sampling(self, manager):
        """Test validation with random sampling."""
        cache1 = MockCache()
        cache2 = MockCache()
        
        # Create many keys
        for i in range(20):
            key = f'key{i}'
            cache1.data[key] = {'data': f'value{i}'}
            cache2.data[key] = {'data': f'value{i}'}
        
        with patch.object(manager, '_get_all_cache_keys', side_effect=[list(cache1.data.keys()), list(cache2.data.keys())]):
            result = await manager.validate_data_consistency(cache1, cache2, sample_size=5)
        
        assert result.metadata_flags['sample_validation'] is True
        assert result.metadata_flags['sample_size'] == 5
        assert len(result.warnings) > 0
        assert 'Validating sample' in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_validate_data_consistency_with_ttl_deltas(self, manager):
        """Test validation with TTL differences."""
        cache1 = MockRedisCache()
        cache2 = MockRedisCache()
        
        cache1.data = {'key1': {'data': 'value1'}}
        cache2.data = {'key1': {'data': 'value1'}}
        
        # Mock TTL methods to return different values
        async def get_ttl_cache1(cache, key):
            return 300
        
        async def get_ttl_cache2(cache, key):
            return 250  # 50 second difference
        
        with patch.object(manager, '_get_all_cache_keys', side_effect=[['key1'], ['key1']]):
            with patch.object(manager, '_get_key_ttl', side_effect=[300, 250]):
                result = await manager.validate_data_consistency(cache1, cache2)
        
        assert 'key1' in result.ttl_deltas
        assert result.ttl_deltas['key1'] == -50  # target - source

    # Test restore_backup method
    
    @pytest.mark.asyncio
    async def test_restore_backup_success(self, manager, temp_file):
        """Test successful backup restoration."""
        # Create a backup file
        backup_data = {
            'metadata': {
                'created_at': '2023-01-01T12:00:00',
                'source_cache_type': 'MockCache'
            },
            'keys': {
                'key1': {'value': {'data': 'value1'}, 'ttl': 300},
                'key2': {'value': {'data': 'value2'}, 'ttl': None}
            }
        }
        
        with gzip.open(temp_file, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        target_cache = MockCache()
        result = await manager.restore_backup(temp_file, target_cache, overwrite=True)
        
        assert result.success is True
        assert result.keys_restored == 2
        assert result.keys_failed == 0
        assert result.backup_file == temp_file
        
        # Verify data was restored
        assert len(target_cache.data) == 2
        assert target_cache.data['key1'] == {'data': 'value1'}
        assert target_cache.ttls['key1'] == 300
    
    @pytest.mark.asyncio
    async def test_restore_backup_no_overwrite(self, manager, temp_file):
        """Test restoration without overwriting existing keys."""
        # Create backup
        backup_data = {
            'keys': {
                'key1': {'value': {'data': 'new_value'}},
                'key2': {'value': {'data': 'value2'}}
            }
        }
        
        with gzip.open(temp_file, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        # Setup target cache with existing data
        target_cache = MockCache()
        target_cache.data['key1'] = {'data': 'existing_value'}
        
        result = await manager.restore_backup(temp_file, target_cache, overwrite=False)
        
        assert result.keys_restored == 1  # Only key2 restored
        assert target_cache.data['key1'] == {'data': 'existing_value'}  # Unchanged
        assert target_cache.data['key2'] == {'data': 'value2'}  # Restored
    
    @pytest.mark.asyncio
    async def test_restore_backup_invalid_file(self, manager, temp_file):
        """Test restoration with invalid backup file."""
        # Create invalid backup file
        with gzip.open(temp_file, 'wt', encoding='utf-8') as f:
            json.dump({'invalid': 'structure'}, f)
        
        target_cache = MockCache()
        result = await manager.restore_backup(temp_file, target_cache)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert 'missing' in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_restore_backup_with_failures(self, manager, temp_file):
        """Test restoration with some key failures."""
        backup_data = {
            'keys': {
                'key1': {'value': {'data': 'value1'}},
                'key2': {'value': {'data': 'value2'}}
            }
        }
        
        with gzip.open(temp_file, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        target_cache = MockCache()
        
        # Make cache fail on second key
        async def failing_set(key, value, ttl=None):
            if key == 'key2':
                raise Exception('Set failed')
            target_cache.data[key] = value
        
        target_cache.set = failing_set
        
        result = await manager.restore_backup(temp_file, target_cache)
        
        assert result.success is False
        assert result.keys_restored == 1
        assert result.keys_failed == 1
        assert len(result.errors) == 1

    # Test helper methods
    
    @pytest.mark.asyncio
    async def test_scan_redis_keys(self, manager):
        """Test Redis key scanning with pagination."""
        mock_redis = AsyncMock()
        
        # Mock SCAN to return results across multiple pages
        mock_redis.scan.side_effect = [
            (10, [b'key1', b'key2']),  # First page
            (0, [b'key3']),           # Last page (cursor 0)
        ]
        
        keys = await manager._scan_redis_keys(mock_redis, 'test:*')
        
        assert keys == ['key1', 'key2', 'key3']
        assert mock_redis.scan.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_all_cache_keys_redis(self, manager):
        """Test getting all keys from Redis cache."""
        cache = MockRedisCache()
        
        with patch.object(manager, '_scan_redis_keys', return_value=['key1', 'key2']) as mock_scan:
            keys = await manager._get_all_cache_keys(cache)
        
        assert keys == ['key1', 'key2']
        mock_scan.assert_called_once_with(cache.redis, '*')
    
    @pytest.mark.asyncio
    async def test_get_all_cache_keys_memory(self, manager):
        """Test getting all keys from memory cache."""
        cache = MockCache()
        cache.memory_cache = {'key1': 'value1', 'key2': 'value2'}
        
        keys = await manager._get_all_cache_keys(cache)
        
        assert set(keys) == {'key1', 'key2'}
    
    @pytest.mark.asyncio
    async def test_get_key_ttl_redis(self, manager):
        """Test getting TTL from Redis cache."""
        cache = MockRedisCache()
        cache.redis.ttl.return_value = 300
        
        ttl = await manager._get_key_ttl(cache, 'test_key')
        
        assert ttl == 300
        cache.redis.ttl.assert_called_once_with('test_key')
    
    @pytest.mark.asyncio
    async def test_get_key_ttl_no_redis(self, manager):
        """Test getting TTL from non-Redis cache."""
        cache = MockCache()
        
        ttl = await manager._get_key_ttl(cache, 'test_key')
        
        assert ttl is None
    
    def test_match_pattern(self, manager):
        """Test pattern matching functionality."""
        assert manager._match_pattern('test:key1', 'test:*') is True
        assert manager._match_pattern('other:key1', 'test:*') is False
        assert manager._match_pattern('key123', 'key*') is True
        assert manager._match_pattern('key123', '*123') is True


# Integration tests with Redis (requires pytest-redis)

@pytest.mark.redis
class TestMigrationWithRedis:
    """Integration tests using actual Redis instances."""
    
    @pytest_asyncio.fixture
    async def redis_cache(self, redis_proc):
        """Create Redis cache with actual Redis instance."""
        cache = AIResponseCache(redis_url=f"redis://localhost:{redis_proc.port}")
        await cache.connect()
        yield cache
        # Cleanup
        if cache.redis:
            await cache.redis.flushall()
            await cache.redis.close()
    
    @pytest_asyncio.fixture
    async def generic_redis_cache(self, redis_proc):
        """Create generic Redis cache with actual Redis instance."""
        cache = GenericRedisCache(redis_url=f"redis://localhost:{redis_proc.port}")
        await cache.connect()
        yield cache
        # Cleanup
        if cache.redis:
            await cache.redis.flushall()
            await cache.redis.close()
    
    @pytest.mark.asyncio
    async def test_full_migration_workflow(self, redis_cache, generic_redis_cache, tmp_path):
        """Test complete migration workflow with real Redis."""
        manager = CacheMigrationManager(chunk_size=5)
        
        # Setup source data
        test_data = {
            'ai_cache:test1': {'response': 'result1', 'confidence': 0.95},
            'ai_cache:test2': {'response': 'result2', 'confidence': 0.89},
            'ai_cache:test3': {'response': 'result3', 'confidence': 0.92}
        }
        
        for key, value in test_data.items():
            await redis_cache.set(key, value, ttl=300)
        
        # Create backup
        backup_file = tmp_path / 'test_backup.json.gz'
        backup_result = await manager.create_backup(redis_cache, str(backup_file))
        
        assert backup_result.success is True
        assert backup_result.keys_backed_up >= 3
        
        # Migrate data
        migration_result = await manager.migrate_ai_cache_data(redis_cache, generic_redis_cache)
        
        assert migration_result.success is True
        assert migration_result.keys_migrated >= 3
        
        # Validate consistency
        validation_result = await manager.validate_data_consistency(redis_cache, generic_redis_cache)
        
        assert validation_result.success is True
        assert validation_result.keys_matched >= 3
        
        # Test restore to new cache
        new_cache = GenericRedisCache(redis_url=f"redis://localhost:{redis_cache.redis._address[1]}")
        await new_cache.connect()
        
        try:
            restore_result = await manager.restore_backup(str(backup_file), new_cache, overwrite=True)
            assert restore_result.success is True
            assert restore_result.keys_restored >= 3
        finally:
            if new_cache.redis:
                await new_cache.redis.flushall()
                await new_cache.redis.close()
    
    @pytest.mark.asyncio
    async def test_migration_with_large_dataset(self, redis_cache, generic_redis_cache):
        """Test migration performance with larger dataset."""
        manager = CacheMigrationManager(chunk_size=10)
        
        # Create larger test dataset
        for i in range(50):
            key = f'ai_cache:large_test_{i}'
            value = {'response': f'result_{i}', 'data': 'x' * 100}
            await redis_cache.set(key, value, ttl=300)
        
        migration_result = await manager.migrate_ai_cache_data(redis_cache, generic_redis_cache)
        
        assert migration_result.success is True
        assert migration_result.keys_migrated == 50
        assert migration_result.chunks_processed == 5  # 50 keys / 10 chunk_size
        assert migration_result.migration_time > 0
    
    @pytest.mark.asyncio
    async def test_backup_restore_round_trip(self, redis_cache, tmp_path):
        """Test backup and restore round trip preserves data integrity."""
        manager = CacheMigrationManager()
        
        # Setup test data with various types
        test_data = {
            'key1': {'string': 'value', 'number': 42, 'boolean': True},
            'key2': {'list': [1, 2, 3], 'dict': {'nested': 'value'}},
            'key3': None  # Test null values
        }
        
        for key, value in test_data.items():
            await redis_cache.set(key, value, ttl=600)
        
        # Create backup
        backup_file = tmp_path / 'round_trip_backup.json.gz'
        backup_result = await manager.create_backup(redis_cache, str(backup_file))
        assert backup_result.success is True
        
        # Clear cache
        if redis_cache.redis:
            await redis_cache.redis.flushall()
        
        # Restore backup
        restore_result = await manager.restore_backup(str(backup_file), redis_cache, overwrite=True)
        assert restore_result.success is True
        
        # Verify data integrity
        for key, expected_value in test_data.items():
            restored_value = await redis_cache.get(key)
            assert restored_value == expected_value
