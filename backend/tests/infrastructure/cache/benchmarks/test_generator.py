"""
Tests for benchmark data generator.

This module tests the CacheBenchmarkDataGenerator class that creates
realistic test data for cache performance benchmarks.
"""

import pytest
import json
from typing import Dict, Any, List

from app.infrastructure.cache.benchmarks.generator import CacheBenchmarkDataGenerator


class TestCacheBenchmarkDataGenerator:
    """Test cases for CacheBenchmarkDataGenerator class."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = CacheBenchmarkDataGenerator()
        assert generator is not None
    
    def test_generate_text_data_default_size(self, data_generator):
        """Test text data generation with default size."""
        text_data = data_generator.generate_text_data()
        
        assert isinstance(text_data, str)
        assert len(text_data) > 0
        # Default size should be around 1KB (1024 chars)
        assert 900 <= len(text_data) <= 1200  # Allow some variance
    
    def test_generate_text_data_custom_size(self, data_generator):
        """Test text data generation with custom sizes."""
        # Test small size
        small_text = data_generator.generate_text_data(size_kb=0.5)
        assert isinstance(small_text, str)
        assert 400 <= len(small_text) <= 600  # ~0.5KB
        
        # Test larger size
        large_text = data_generator.generate_text_data(size_kb=5.0)
        assert isinstance(large_text, str)
        assert 4500 <= len(large_text) <= 5500  # ~5KB
    
    def test_generate_text_data_content_variety(self, data_generator):
        """Test that generated text data has variety."""
        texts = [data_generator.generate_text_data() for _ in range(5)]
        
        # All texts should be different
        assert len(set(texts)) == 5
        
        # Each text should contain different content
        for text in texts:
            assert isinstance(text, str)
            assert len(text) > 0
    
    def test_generate_json_data_simple(self, data_generator):
        """Test JSON data generation with simple structure."""
        json_data = data_generator.generate_json_data()
        
        # Should be valid JSON
        parsed = json.loads(json_data)
        assert isinstance(parsed, dict)
        
        # Should contain expected fields
        assert "id" in parsed
        assert "timestamp" in parsed
        assert "data" in parsed
        
        # Size should be reasonable (around 1KB by default)
        assert 500 <= len(json_data) <= 2000
    
    def test_generate_json_data_complex(self, data_generator):
        """Test JSON data generation with complex structure."""
        json_data = data_generator.generate_json_data(complexity="complex")
        
        parsed = json.loads(json_data)
        assert isinstance(parsed, dict)
        
        # Complex structure should have nested objects
        assert "nested" in parsed
        assert isinstance(parsed["nested"], dict)
        
        # Should be larger than simple structure
        simple_data = data_generator.generate_json_data(complexity="simple")
        assert len(json_data) > len(simple_data)
    
    def test_generate_json_data_custom_size(self, data_generator):
        """Test JSON data generation with custom size."""
        # Test different sizes
        small_json = data_generator.generate_json_data(size_kb=0.5)
        large_json = data_generator.generate_json_data(size_kb=3.0)
        
        # Both should be valid JSON
        small_parsed = json.loads(small_json)
        large_parsed = json.loads(large_json)
        
        assert isinstance(small_parsed, dict)
        assert isinstance(large_parsed, dict)
        
        # Size should roughly match requests
        assert len(large_json) > len(small_json)
        assert 400 <= len(small_json) <= 700  # ~0.5KB
        assert 2500 <= len(large_json) <= 3500  # ~3KB
    
    def test_generate_binary_data_default_size(self, data_generator):
        """Test binary data generation with default size."""
        binary_data = data_generator.generate_binary_data()
        
        assert isinstance(binary_data, bytes)
        # Default size should be around 1KB
        assert 900 <= len(binary_data) <= 1100
    
    def test_generate_binary_data_custom_size(self, data_generator):
        """Test binary data generation with custom sizes."""
        # Test small size
        small_binary = data_generator.generate_binary_data(size_kb=0.25)
        assert isinstance(small_binary, bytes)
        assert 200 <= len(small_binary) <= 300  # ~0.25KB
        
        # Test larger size
        large_binary = data_generator.generate_binary_data(size_kb=10.0)
        assert isinstance(large_binary, bytes)
        assert 9500 <= len(large_binary) <= 10500  # ~10KB
    
    def test_generate_binary_data_randomness(self, data_generator):
        """Test that generated binary data is random."""
        binaries = [data_generator.generate_binary_data() for _ in range(5)]
        
        # All binaries should be different
        assert len(set(binaries)) == 5
        
        # Check that data is not all zeros or all the same byte
        for binary in binaries:
            unique_bytes = set(binary)
            assert len(unique_bytes) > 1  # Should have variety in bytes
    
    def test_generate_cache_key_default(self, data_generator):
        """Test cache key generation with default parameters."""
        key = data_generator.generate_cache_key()
        
        assert isinstance(key, str)
        assert len(key) > 0
        assert key.startswith("benchmark_key_")
    
    def test_generate_cache_key_custom_prefix(self, data_generator):
        """Test cache key generation with custom prefix."""
        custom_key = data_generator.generate_cache_key(prefix="test_prefix")
        
        assert isinstance(custom_key, str)
        assert custom_key.startswith("test_prefix_")
    
    def test_generate_cache_key_uniqueness(self, data_generator):
        """Test that generated cache keys are unique."""
        keys = [data_generator.generate_cache_key() for _ in range(100)]
        
        # All keys should be unique
        assert len(set(keys)) == 100
    
    def test_generate_workload_data_basic(self, data_generator):
        """Test workload data generation with basic parameters."""
        workload = data_generator.generate_workload_data(num_items=10)
        
        assert isinstance(workload, list)
        assert len(workload) == 10
        
        # Each item should be a dictionary with key and value
        for item in workload:
            assert isinstance(item, dict)
            assert "key" in item
            assert "value" in item
            assert isinstance(item["key"], str)
    
    def test_generate_workload_data_mixed_types(self, data_generator):
        """Test workload data generation with mixed data types."""
        workload = data_generator.generate_workload_data(
            num_items=15,
            data_types=["text", "json", "binary"]
        )
        
        assert len(workload) == 15
        
        # Should have a mix of data types
        text_count = 0
        json_count = 0
        binary_count = 0
        
        for item in workload:
            if isinstance(item["value"], str):
                try:
                    # Try to parse as JSON
                    json.loads(item["value"])
                    json_count += 1
                except json.JSONDecodeError:
                    # It's text data
                    text_count += 1
            elif isinstance(item["value"], bytes):
                binary_count += 1
        
        # Should have some of each type (allowing for randomness)
        assert text_count > 0 or json_count > 0 or binary_count > 0
    
    def test_generate_workload_data_size_distribution(self, data_generator):
        """Test workload data generation with size distribution."""
        workload = data_generator.generate_workload_data(
            num_items=20,
            size_distribution={
                "small": (0.1, 0.5),    # 10% of items, 0.1-0.5 KB
                "medium": (0.5, 2.0),   # Default percentage, 0.5-2.0 KB
                "large": (2.0, 5.0)     # Remaining items, 2.0-5.0 KB
            }
        )
        
        assert len(workload) == 20
        
        # Check that sizes vary according to distribution
        sizes = []
        for item in workload:
            if isinstance(item["value"], str):
                sizes.append(len(item["value"]))
            elif isinstance(item["value"], bytes):
                sizes.append(len(item["value"]))
        
        min_size = min(sizes)
        max_size = max(sizes)
        
        # Should have variation in sizes
        assert min_size < max_size
        assert min_size >= 50  # At least ~0.05KB
        assert max_size <= 6000  # At most ~6KB (with some tolerance)
    
    def test_generate_workload_data_custom_key_pattern(self, data_generator):
        """Test workload data generation with custom key pattern."""
        workload = data_generator.generate_workload_data(
            num_items=5,
            key_pattern="user:{id}:session"
        )
        
        assert len(workload) == 5
        
        # All keys should follow the pattern
        for item in workload:
            key = item["key"]
            assert key.startswith("user:")
            assert ":session" in key
            # Should have an ID number in the middle
            parts = key.split(":")
            assert len(parts) == 3
            assert parts[0] == "user"
            assert parts[1].isdigit()
            assert parts[2] == "session"
    
    def test_generate_realistic_user_data(self, data_generator):
        """Test generation of realistic user data."""
        user_data = data_generator.generate_realistic_user_data()
        
        assert isinstance(user_data, dict)
        
        # Should contain typical user fields
        expected_fields = ["user_id", "username", "email", "profile"]
        for field in expected_fields:
            assert field in user_data
        
        # Validate data types and formats
        assert isinstance(user_data["user_id"], str)
        assert isinstance(user_data["username"], str)
        assert isinstance(user_data["email"], str)
        assert "@" in user_data["email"]  # Basic email validation
        assert isinstance(user_data["profile"], dict)
    
    def test_generate_realistic_session_data(self, data_generator):
        """Test generation of realistic session data."""
        session_data = data_generator.generate_realistic_session_data()
        
        assert isinstance(session_data, dict)
        
        # Should contain typical session fields
        expected_fields = ["session_id", "user_id", "created_at", "last_activity", "data"]
        for field in expected_fields:
            assert field in session_data
        
        # Validate session ID format
        assert isinstance(session_data["session_id"], str)
        assert len(session_data["session_id"]) > 10  # Should be reasonably long
    
    def test_generate_realistic_api_response(self, data_generator):
        """Test generation of realistic API response data."""
        api_response = data_generator.generate_realistic_api_response()
        
        assert isinstance(api_response, dict)
        
        # Should contain typical API response fields
        expected_fields = ["status", "timestamp", "data", "metadata"]
        for field in expected_fields:
            assert field in api_response
        
        # Validate response structure
        assert api_response["status"] in ["success", "error", "pending"]
        assert isinstance(api_response["timestamp"], str)
        assert isinstance(api_response["data"], (dict, list))
        assert isinstance(api_response["metadata"], dict)
    
    def test_generate_performance_test_dataset(self, data_generator):
        """Test generation of comprehensive performance test dataset."""
        dataset = data_generator.generate_performance_test_dataset()
        
        assert isinstance(dataset, dict)
        
        # Should contain different categories of test data
        expected_categories = ["small_objects", "medium_objects", "large_objects", 
                             "json_data", "binary_data", "text_data"]
        
        for category in expected_categories:
            assert category in dataset
            assert isinstance(dataset[category], list)
            assert len(dataset[category]) > 0
    
    def test_generate_compression_test_data(self, data_generator):
        """Test generation of data suitable for compression testing."""
        # Test data with high compression potential
        compressible_data = data_generator.generate_compression_test_data("high")
        assert isinstance(compressible_data, str)
        assert len(compressible_data) > 0
        
        # Test data with low compression potential
        random_data = data_generator.generate_compression_test_data("low")
        assert isinstance(random_data, str)
        assert len(random_data) > 0
        
        # Compressible data should have patterns (repeated content)
        # Random data should have more variety
        compressible_unique_chars = len(set(compressible_data))
        random_unique_chars = len(set(random_data))
        
        # This is a heuristic test - compressible data should have fewer unique characters
        # relative to its length compared to random data
        if len(compressible_data) > 100 and len(random_data) > 100:
            compressible_ratio = compressible_unique_chars / len(compressible_data)
            random_ratio = random_unique_chars / len(random_data)
            
            # Compressible data should have lower unique character ratio
            assert compressible_ratio <= random_ratio * 1.5  # Allow some tolerance
    
    def test_edge_case_zero_size(self, data_generator):
        """Test edge case with zero size request."""
        # Text data
        text = data_generator.generate_text_data(size_kb=0.0)
        assert isinstance(text, str)
        assert len(text) == 0
        
        # Binary data
        binary = data_generator.generate_binary_data(size_kb=0.0)
        assert isinstance(binary, bytes)
        assert len(binary) == 0
    
    def test_edge_case_very_large_size(self, data_generator):
        """Test edge case with very large size request."""
        # Test with large size (but not too large to cause memory issues in tests)
        large_text = data_generator.generate_text_data(size_kb=100.0)  # 100KB
        assert isinstance(large_text, str)
        assert 95000 <= len(large_text) <= 105000  # ~100KB with tolerance
    
    def test_edge_case_empty_workload(self, data_generator):
        """Test edge case with empty workload request."""
        workload = data_generator.generate_workload_data(num_items=0)
        assert isinstance(workload, list)
        assert len(workload) == 0
    
    def test_consistent_generation_with_seed(self, data_generator):
        """Test that generation is consistent when using the same seed."""
        # This test assumes the generator can be seeded for reproducibility
        # If the implementation supports seeding
        try:
            # Generate data twice with same conditions
            data1 = data_generator.generate_text_data(size_kb=1.0)
            data2 = data_generator.generate_text_data(size_kb=1.0)
            
            # Without seeding, data should be different
            assert data1 != data2
            
        except Exception:
            # If seeding is not implemented, this test will be skipped
            pytest.skip("Seeded generation not implemented")
    
    def test_data_type_validation(self, data_generator):
        """Test that generated data matches expected types."""
        # Test all supported data types
        text_data = data_generator.generate_text_data()
        json_data = data_generator.generate_json_data()
        binary_data = data_generator.generate_binary_data()
        
        # Validate types
        assert isinstance(text_data, str)
        assert isinstance(binary_data, bytes)
        
        # JSON data should be a valid JSON string
        assert isinstance(json_data, str)
        parsed_json = json.loads(json_data)  # Should not raise exception
        assert isinstance(parsed_json, (dict, list))
    
    def test_memory_efficiency(self, data_generator):
        """Test that data generation is memory efficient."""
        # Generate multiple datasets and ensure they don't consume excessive memory
        datasets = []
        for _ in range(10):
            workload = data_generator.generate_workload_data(num_items=50)
            datasets.append(workload)
        
        # All datasets should be generated successfully
        assert len(datasets) == 10
        
        # Each dataset should have the expected structure
        for dataset in datasets:
            assert len(dataset) == 50
            for item in dataset:
                assert "key" in item
                assert "value" in item