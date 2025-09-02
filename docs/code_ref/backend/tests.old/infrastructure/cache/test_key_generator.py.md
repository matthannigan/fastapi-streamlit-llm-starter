---
sidebar_label: test_key_generator
---

# Tests for standalone CacheKeyGenerator component.

  file_path: `backend/tests.old/infrastructure/cache/test_key_generator.py`

This module provides comprehensive tests for the CacheKeyGenerator class,
including edge cases for very small text, >10 MB text, Unicode handling,
and performance monitoring integration.

The tests validate:
- Basic key generation functionality
- Streaming SHA-256 hashing for large texts
- Performance monitoring integration
- Edge cases (empty text, boundary conditions, Unicode)
- Backward compatibility with existing key formats
- Thread safety and concurrent access

## TestCacheKeyGeneratorBasics

Test basic functionality of CacheKeyGenerator.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### custom_key_generator()

```python
def custom_key_generator(self):
```

Create a CacheKeyGenerator with custom settings.

### test_initialization_default()

```python
def test_initialization_default(self):
```

Test CacheKeyGenerator initialization with default parameters.

### test_initialization_custom()

```python
def test_initialization_custom(self):
```

Test CacheKeyGenerator initialization with custom parameters.

### test_short_text_handling()

```python
def test_short_text_handling(self, key_generator):
```

Test that short texts are used directly with sanitization.

### test_text_sanitization()

```python
def test_text_sanitization(self, key_generator):
```

Test that special characters are properly sanitized.

### test_long_text_hashing()

```python
def test_long_text_hashing(self, key_generator):
```

Test that long texts are properly hashed.

### test_boundary_threshold_conditions()

```python
def test_boundary_threshold_conditions(self, key_generator):
```

Test behavior at exact threshold boundaries.

### test_hash_consistency()

```python
def test_hash_consistency(self, key_generator):
```

Test that identical texts produce identical hashes.

### test_hash_uniqueness()

```python
def test_hash_uniqueness(self, key_generator):
```

Test that different texts produce different hashes.

### test_hash_metadata_inclusion()

```python
def test_hash_metadata_inclusion(self, key_generator):
```

Test that hash includes metadata for uniqueness.

## TestCacheKeyGeneration

Test cache key generation functionality.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### test_basic_cache_key_generation()

```python
def test_basic_cache_key_generation(self, key_generator):
```

Test basic cache key generation.

### test_cache_key_with_question()

```python
def test_cache_key_with_question(self, key_generator):
```

Test cache key generation with question parameter.

### test_cache_key_without_options()

```python
def test_cache_key_without_options(self, key_generator):
```

Test cache key generation without options.

### test_cache_key_consistency()

```python
def test_cache_key_consistency(self, key_generator):
```

Test that identical inputs produce identical cache keys.

### test_cache_key_options_order_independence()

```python
def test_cache_key_options_order_independence(self, key_generator):
```

Test that options order doesn't affect cache key.

### test_cache_key_with_long_text()

```python
def test_cache_key_with_long_text(self, key_generator):
```

Test cache key generation with long text that gets hashed.

### test_cache_key_structure_validation()

```python
def test_cache_key_structure_validation(self, key_generator):
```

Test the structure and format of generated cache keys.

### test_cache_key_length_constraints()

```python
def test_cache_key_length_constraints(self, key_generator):
```

Test that cache keys don't become excessively long.

## TestEdgeCases

Test edge cases and boundary conditions.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### test_empty_string_handling()

```python
def test_empty_string_handling(self, key_generator):
```

Test CacheKeyGenerator behavior with empty strings.

### test_unicode_and_special_characters()

```python
def test_unicode_and_special_characters(self, key_generator):
```

Test CacheKeyGenerator with Unicode and special characters.

### test_very_small_text_edge_case()

```python
def test_very_small_text_edge_case(self, key_generator):
```

Test with single character text.

### test_large_text_over_10mb()

```python
def test_large_text_over_10mb(self, key_generator):
```

Test with text larger than 10 MB.

### test_various_option_value_types()

```python
def test_various_option_value_types(self, key_generator):
```

Test cache key generation with different option value types.

### test_none_and_invalid_inputs_handling()

```python
def test_none_and_invalid_inputs_handling(self, key_generator):
```

Test CacheKeyGenerator behavior with None and edge case inputs.

## TestPerformanceMonitoring

Test performance monitoring integration.

### test_performance_monitor_integration()

```python
def test_performance_monitor_integration(self):
```

Test CacheKeyGenerator with performance monitor integration.

### test_performance_monitor_data_integrity()

```python
def test_performance_monitor_data_integrity(self):
```

Test that performance monitor receives accurate data.

### test_get_key_generation_stats_without_monitor()

```python
def test_get_key_generation_stats_without_monitor(self):
```

Test get_key_generation_stats without performance monitor.

### test_get_key_generation_stats_with_monitor()

```python
def test_get_key_generation_stats_with_monitor(self):
```

Test get_key_generation_stats with performance monitor.

## TestSecurityAndPrivacy

Test security and privacy aspects of key generation.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### test_question_parameter_hashing_consistency()

```python
def test_question_parameter_hashing_consistency(self, key_generator):
```

Test that question parameter hashing is consistent and secure.

### test_options_hashing_security()

```python
def test_options_hashing_security(self, key_generator):
```

Test that sensitive options are properly hashed.

## TestConcurrencyAndThreadSafety

Test concurrent access and thread safety.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### test_concurrent_key_generation_consistency()

```python
def test_concurrent_key_generation_consistency(self, key_generator):
```

Test that concurrent key generation produces consistent results.

## TestDifferentHashAlgorithms

Test different hash algorithms.

### test_different_hash_algorithms()

```python
def test_different_hash_algorithms(self):
```

Test CacheKeyGenerator with different hash algorithms.

## TestBackwardCompatibility

Test backward compatibility with existing key formats.

### test_key_format_compatibility()

```python
def test_key_format_compatibility(self):
```

Test that generated keys maintain expected format.

## TestPerformanceCharacteristics

Test performance characteristics of the key generator.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### test_performance_scalability_with_text_size()

```python
def test_performance_scalability_with_text_size(self, key_generator):
```

Test that performance scales reasonably with text size.

### test_memory_efficiency_large_text()

```python
def test_memory_efficiency_large_text(self, key_generator):
```

Test that memory usage is efficient for large texts.
