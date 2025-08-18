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
    
    def test_generate_basic_operations_data_default(self, data_generator):
        """Test basic operations data generation with default count."""
        operations_data = data_generator.generate_basic_operations_data()
        
        assert isinstance(operations_data, list)
        assert len(operations_data) == 100  # Default count
        
        # Check structure of first operation
        first_op = operations_data[0]
        assert isinstance(first_op, dict)
        assert "key" in first_op
        assert "text" in first_op
        assert "operation" in first_op
    
    def test_generate_basic_operations_data_custom_count(self, data_generator):
        """Test basic operations data generation with custom count."""
        # Test small count
        small_data = data_generator.generate_basic_operations_data(count=10)
        assert isinstance(small_data, list)
        assert len(small_data) == 10
        
        # Test larger count
        large_data = data_generator.generate_basic_operations_data(count=500)
        assert isinstance(large_data, list)
        assert len(large_data) == 500
    
    def test_generate_basic_operations_data_variety(self, data_generator):
        """Test that generated operations data has variety."""
        operations_data = data_generator.generate_basic_operations_data(count=20)
        
        # Check that we have different operation types
        operation_types = set(op["operation"] for op in operations_data)
        assert len(operation_types) >= 2  # Should have multiple operation types
        
        # Check that keys are different
        keys = [op["key"] for op in operations_data]
        assert len(set(keys)) == len(keys)  # All keys should be unique
    
    def test_generate_compression_test_data(self, data_generator):
        """Test compression test data generation."""
        compression_data = data_generator.generate_compression_test_data()
        
        assert isinstance(compression_data, list)
        assert len(compression_data) > 0
        
        # Check structure of first compression test
        first_test = compression_data[0]
        assert isinstance(first_test, dict)
        assert "key" in first_test
        assert "text" in first_test or "data" in first_test
    
    def test_generate_concurrent_access_patterns(self, data_generator):
        """Test concurrent access patterns generation."""
        access_patterns = data_generator.generate_concurrent_access_patterns()
        
        assert isinstance(access_patterns, list)
        assert len(access_patterns) == 10  # Default num_patterns
        
        # Check structure of patterns
        for pattern in access_patterns:
            assert isinstance(pattern, dict)
            assert "key" in pattern or "pattern_type" in pattern
    
    def test_generate_memory_pressure_data(self, data_generator):
        """Test memory pressure data generation."""
        # Test with different sizes
        small_memory_data = data_generator.generate_memory_pressure_data(total_size_mb=1.0)
        large_memory_data = data_generator.generate_memory_pressure_data(total_size_mb=5.0)
        
        assert isinstance(small_memory_data, list)
        assert isinstance(large_memory_data, list)
        
        # Large data should have more entries or larger entries
        assert len(large_memory_data) >= len(small_memory_data)
        assert len(large_json) > len(small_json)
        assert 400 <= len(small_json) <= 700  # ~0.5KB
        assert 2500 <= len(large_json) <= 3500  # ~3KB
    
    def test_generate_concurrent_access_patterns_custom_count(self, data_generator):
        """Test concurrent access patterns with custom count."""
        patterns = data_generator.generate_concurrent_access_patterns(num_patterns=5)
        
        assert isinstance(patterns, list)
        assert len(patterns) == 5
    
    def test_data_generator_produces_varied_content(self, data_generator):
        """Test that generator produces varied content."""
        # Generate multiple sets of basic operations data
        data1 = data_generator.generate_basic_operations_data(count=10)
        data2 = data_generator.generate_basic_operations_data(count=10)
        
        # Keys should be different between runs
        keys1 = set(item["key"] for item in data1)
        keys2 = set(item["key"] for item in data2)
        assert keys1 != keys2  # Should have different keys
    
    def test_basic_operations_data_structure(self, data_generator):
        """Test structure of generated basic operations data."""
        data = data_generator.generate_basic_operations_data(count=5)
        
        for item in data:
            assert isinstance(item, dict)
            # Check required fields exist
            assert "key" in item
            assert "text" in item or "value" in item
            assert "operation" in item
            
            # Key should be a string
            assert isinstance(item["key"], str)
            assert len(item["key"]) > 0
    
    def test_compression_test_data_structure(self, data_generator):
        """Test structure of compression test data."""
        data = data_generator.generate_compression_test_data()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check each item has expected structure
        for item in data:
            assert isinstance(item, dict)
            # Should have key and either text or data field
            assert "key" in item
            assert any(field in item for field in ["text", "data", "value"])
    
    def test_memory_pressure_data_structure(self, data_generator):
        """Test structure of memory pressure data."""
        data = data_generator.generate_memory_pressure_data(total_size_mb=2.0)
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Each item should be a dictionary with key and large content
        for item in data:
            assert isinstance(item, dict)
            assert "key" in item
            # Should have content field that contributes to memory pressure
            assert any(field in item for field in ["text", "data", "value", "content"])
    
    def test_generator_consistency(self, data_generator):
        """Test that generator produces consistent output structure."""
        # Generate multiple datasets and verify consistent structure
        basic_data = data_generator.generate_basic_operations_data(count=3)
        compression_data = data_generator.generate_compression_test_data()
        memory_data = data_generator.generate_memory_pressure_data(total_size_mb=1.0)
        concurrent_data = data_generator.generate_concurrent_access_patterns(num_patterns=2)
        
        # All should return lists
        assert isinstance(basic_data, list)
        assert isinstance(compression_data, list)
        assert isinstance(memory_data, list)
        assert isinstance(concurrent_data, list)
        
        # All items in lists should be dictionaries
        for dataset in [basic_data, compression_data, memory_data, concurrent_data]:
            for item in dataset:
                assert isinstance(item, dict)
    
    def test_generator_parameter_handling(self, data_generator):
        """Test that generator handles parameters correctly."""
        # Test with edge case parameters
        empty_data = data_generator.generate_basic_operations_data(count=0)
        assert isinstance(empty_data, list)
        assert len(empty_data) == 0
        
        # Test with minimal memory size
        tiny_memory_data = data_generator.generate_memory_pressure_data(total_size_mb=0.1)
        assert isinstance(tiny_memory_data, list)
        
        # Test with single pattern
        single_pattern = data_generator.generate_concurrent_access_patterns(num_patterns=1)
        assert isinstance(single_pattern, list)
        assert len(single_pattern) == 1
    
    def test_data_generator_integration(self, data_generator):
        """Test integration between different data generation methods."""
        # Generate data using all available methods
        basic_ops = data_generator.generate_basic_operations_data(count=5)
        compression_tests = data_generator.generate_compression_test_data()
        memory_pressure = data_generator.generate_memory_pressure_data(total_size_mb=1.0)
        concurrent_patterns = data_generator.generate_concurrent_access_patterns(num_patterns=3)
        
        # Verify all methods work and return expected types
        all_datasets = [basic_ops, compression_tests, memory_pressure, concurrent_patterns]
        
        for dataset in all_datasets:
            assert isinstance(dataset, list)
            assert len(dataset) >= 0
            
            # Each item should be a dict with at least a key field
            for item in dataset:
                assert isinstance(item, dict)
                # Most data should have a key field for cache operations
                if len(item) > 0:
                    assert any(field in item for field in ["key", "pattern_type", "operation"])
    
    def test_all_generator_methods_work(self, data_generator):
        """Test that all generator methods work and return expected structure."""
        # Test all actual methods from the API
        basic_ops = data_generator.generate_basic_operations_data(count=5)
        compression = data_generator.generate_compression_test_data()
        memory_pressure = data_generator.generate_memory_pressure_data(total_size_mb=0.5)
        concurrent = data_generator.generate_concurrent_access_patterns(num_patterns=3)
        
        # All should return lists of dictionaries
        for data_set, name in [(basic_ops, "basic_ops"), 
                               (compression, "compression"), 
                               (memory_pressure, "memory_pressure"), 
                               (concurrent, "concurrent")]:
            assert isinstance(data_set, list), f"{name} should return list"
            
            # Each item should be a dictionary
            for item in data_set:
                assert isinstance(item, dict), f"{name} items should be dicts"