"""
Cache Benchmark Data Generator

This module provides realistic test data generation for cache performance benchmarking.
It generates varied datasets that simulate real-world cache usage patterns including
different sizes, types, and complexity levels.

Classes:
    CacheBenchmarkDataGenerator: Main data generator for benchmarks

The generator creates different types of test data:
- Small data sets for basic operations
- Medium and large data sets for performance testing
- JSON structured data for complex objects
- Memory pressure data for load testing
- Concurrent access patterns for multi-threading tests
- Compression test data with varying compressibility
"""

import json
import random
import string
from datetime import datetime
from typing import Any, Dict, List


class CacheBenchmarkDataGenerator:
    """
    Generate realistic test data for cache performance benchmarking.
    
    This class provides various methods to generate test data that closely
    matches real-world cache usage patterns. It supports different data sizes,
    types, and access patterns to comprehensively test cache performance.
    
    The generator creates data with realistic characteristics including:
    - Variable text sizes (short, medium, long)
    - Different operation types (summarize, sentiment, etc.)
    - JSON structured data
    - Compression-friendly and compression-resistant content
    - Concurrent access patterns
    - Memory pressure scenarios
    
    Example:
        >>> generator = CacheBenchmarkDataGenerator()
        >>> basic_data = generator.generate_basic_operations_data(100)
        >>> memory_data = generator.generate_memory_pressure_data(10.0)
        >>> compression_data = generator.generate_compression_test_data()
    """
    
    def __init__(self):
        """Initialize the data generator with predefined templates and patterns."""
        self.text_samples = [
            "Short text for basic testing.",
            "Medium length text that represents typical cache content with some additional words to make it more realistic for testing purposes.",
            "Long text content that simulates larger cache entries with substantial content that might be encountered in real-world applications. " * 10,
            "Very long text content that tests the limits of cache performance with extensive data. " * 50
        ]
        
        self.operation_types = ["summarize", "sentiment", "key_points", "questions", "qa"]
        self.sample_options = {
            "length": ["short", "medium", "long"],
            "style": ["formal", "casual", "technical"],
            "detail_level": ["brief", "detailed", "comprehensive"]
        }
    
    def _generate_test_data_sets(self, test_operations: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate varied test data sets for comprehensive benchmarking.
        
        Creates five different types of test data sets:
        1. Small data: Simple key-value pairs for basic testing
        2. Medium data: Moderate-sized content with options
        3. Large data: Large content with lists and complex structure
        4. JSON data: Complex structured objects
        5. Realistic data: Generated using sentence templates for natural text
        
        Args:
            test_operations: Total number of test operations to generate
            
        Returns:
            Dictionary containing five data sets with different characteristics
        """
        # Small data set (simple key-value pairs)
        small_data = []
        for i in range(min(25, test_operations // 4)):
            small_data.append({
                "key": f"small_key_{i}",
                "text": "Short text for basic testing.",
                "operation": random.choice(self.operation_types),
                "options": {"length": "short"},
                "expected_size_bytes": 30,
                "cache_ttl": 300
            })
        
        # Medium data set (100x repetitions)
        medium_data = []
        for i in range(min(50, test_operations // 2)):
            text = self.text_samples[1] * random.randint(1, 3)
            medium_data.append({
                "key": f"medium_key_{i}",
                "text": text,
                "operation": random.choice(self.operation_types),
                "options": {"length": "medium", "detail_level": "detailed"},
                "expected_size_bytes": len(text.encode('utf-8')),
                "cache_ttl": random.randint(600, 1800)
            })
        
        # Large data set (1000x repetitions with lists)
        large_data = []
        for i in range(min(20, test_operations // 5)):
            base_text = self.text_samples[2]
            text_with_lists = base_text + "\\n" + "\\n".join([f"Item {j}: {base_text[:50]}" for j in range(random.randint(5, 15))])
            large_data.append({
                "key": f"large_key_{i}",
                "text": text_with_lists,
                "operation": random.choice(self.operation_types),
                "options": {"length": "long", "detail_level": "comprehensive"},
                "expected_size_bytes": len(text_with_lists.encode('utf-8')),
                "cache_ttl": random.randint(1800, 3600)
            })
        
        # JSON data set (complex objects)
        json_data = []
        for i in range(min(30, test_operations // 3)):
            complex_obj = {
                "user_id": random.randint(1, 10000),
                "content": random.choice(self.text_samples),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "tags": [f"tag_{j}" for j in range(random.randint(1, 5))],
                    "scores": {op: random.uniform(0.1, 1.0) for op in self.operation_types}
                },
                "processing_history": [{
                    "operation": random.choice(self.operation_types),
                    "timestamp": datetime.now().isoformat(),
                    "duration_ms": random.randint(10, 500)
                } for _ in range(random.randint(1, 3))]
            }
            json_text = json.dumps(complex_obj)
            json_data.append({
                "key": f"json_key_{i}",
                "text": json_text,
                "operation": "qa",  # More complex operation for JSON data
                "options": {"format": "json", "detail_level": "comprehensive"},
                "expected_size_bytes": len(json_text.encode('utf-8')),
                "cache_ttl": random.randint(900, 2700)
            })
        
        # Realistic data generation using sentence-like patterns
        realistic_data = []
        sentence_templates = [
            "The {adjective} {noun} {verb} {adverb} in the {location}.",
            "During {time_period}, we observed that {subject} {action} {object} with {result}.",
            "Analysis of {data_type} reveals {finding} which {implication} for {domain}."
        ]
        
        vocab = {
            "adjective": ["complex", "efficient", "robust", "scalable", "innovative"],
            "noun": ["system", "algorithm", "process", "framework", "solution"],
            "verb": ["processes", "analyzes", "transforms", "optimizes", "manages"],
            "adverb": ["effectively", "rapidly", "consistently", "accurately", "reliably"],
            "location": ["production environment", "test suite", "cache layer", "data pipeline"],
            "time_period": ["Q1 2024", "the past month", "recent testing", "initial deployment"],
            "subject": ["the cache system", "our algorithm", "the benchmark suite"],
            "action": ["improved performance by", "reduced latency to", "achieved throughput of"],
            "object": ["25% over baseline", "sub-millisecond levels", "1000+ requests/second"],
            "result": ["significant improvements", "optimal efficiency", "enhanced reliability"],
            "data_type": ["performance metrics", "cache statistics", "response times"],
            "finding": ["consistent patterns", "notable improvements", "optimal configurations"],
            "implication": ["suggests optimization opportunities", "indicates successful refactoring"],
            "domain": ["AI applications", "web services", "data processing"]
        }
        
        for i in range(min(25, test_operations // 4)):
            template = random.choice(sentence_templates)
            # Generate varied, sentence-like text
            filled_template = template
            for placeholder, options in vocab.items():
                if f"{{{placeholder}}}" in filled_template:
                    filled_template = filled_template.replace(f"{{{placeholder}}}", random.choice(options))
            
            # Create multiple sentences for more realistic content
            realistic_text = " ".join([filled_template for _ in range(random.randint(2, 5))])
            
            realistic_data.append({
                "key": f"realistic_key_{i}",
                "text": realistic_text,
                "operation": random.choice(self.operation_types),
                "options": {k: random.choice(v) for k, v in self.sample_options.items()},
                "expected_size_bytes": len(realistic_text.encode('utf-8')),
                "cache_ttl": random.randint(300, 3600)
            })
        
        return {
            "small": small_data,
            "medium": medium_data,
            "large": large_data,
            "json": json_data,
            "realistic": realistic_data
        }

    def generate_basic_operations_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Generate test data for basic cache operations.
        
        Creates a mixed dataset combining all data types (small, medium, large,
        JSON, and realistic) to provide comprehensive coverage of cache operations.
        
        Args:
            count: Number of test data items to generate
            
        Returns:
            List of dictionaries containing test data with keys, text, operations,
            and metadata suitable for cache benchmarking
            
        Example:
            >>> generator = CacheBenchmarkDataGenerator()
            >>> data = generator.generate_basic_operations_data(50)
            >>> print(f"Generated {len(data)} test items")
            >>> print(f"First item: {data[0]['key']}")
        """
        # Use the new varied data generation but flatten for backward compatibility
        data_sets = self._generate_test_data_sets(count)
        
        # Combine all data sets and shuffle
        all_data = []
        for data_set in data_sets.values():
            all_data.extend(data_set)
        
        random.shuffle(all_data)
        
        # Return the requested count
        return all_data[:count]
    
    def generate_memory_pressure_data(self, total_size_mb: float = 10.0) -> List[Dict[str, Any]]:
        """
        Generate large dataset for memory cache pressure testing.
        
        Creates a dataset that targets a specific total memory size to test
        how the cache performs under memory pressure. Varies entry sizes
        to simulate realistic memory usage patterns.
        
        Args:
            total_size_mb: Target total size of generated data in megabytes
            
        Returns:
            List of test data items that collectively approach the target size
            
        Example:
            >>> generator = CacheBenchmarkDataGenerator()
            >>> data = generator.generate_memory_pressure_data(5.0)  # 5MB of data
            >>> total_bytes = sum(item['size_bytes'] for item in data)
            >>> print(f"Generated {total_bytes / (1024*1024):.1f}MB of test data")
        """
        target_bytes = int(total_size_mb * 1024 * 1024)
        test_data = []
        current_size = 0
        index = 0
        
        while current_size < target_bytes:
            # Generate variable-sized content
            size_factor = random.randint(1, 20)
            text = "Large cache entry content for memory pressure testing. " * size_factor
            text_bytes = len(text.encode('utf-8'))
            
            test_data.append({
                "key": f"memory_test_{index}",
                "text": text,
                "operation": random.choice(self.operation_types),
                "size_bytes": text_bytes,
                "priority": random.choice(["high", "medium", "low"])
            })
            
            current_size += text_bytes
            index += 1
        
        return test_data
    
    def generate_concurrent_access_patterns(self, num_patterns: int = 10) -> List[Dict[str, Any]]:
        """
        Generate patterns for concurrent cache access testing.
        
        Creates realistic concurrent access patterns that simulate multiple
        threads or processes accessing the cache simultaneously with different
        operation mixes and timing patterns.
        
        Args:
            num_patterns: Number of different access patterns to generate
            
        Returns:
            List of access pattern dictionaries, each containing operation
            sequences and concurrency parameters
            
        Example:
            >>> generator = CacheBenchmarkDataGenerator()
            >>> patterns = generator.generate_concurrent_access_patterns(5)
            >>> for pattern in patterns:
            >>>     print(f"Pattern {pattern['pattern_id']}: "
            >>>           f"{len(pattern['operations'])} operations, "
            >>>           f"{pattern['concurrency_level']} threads")
        """
        patterns = []
        base_keys = [f"concurrent_key_{i}" for i in range(20)]
        
        for i in range(num_patterns):
            pattern = {
                "pattern_id": f"pattern_{i}",
                "operations": [],
                "concurrency_level": random.randint(5, 20),
                "duration_seconds": random.randint(10, 60)
            }
            
            # Generate sequence of operations for this pattern
            for j in range(random.randint(50, 200)):
                operation = {
                    "type": random.choice(["get", "set", "delete"]),
                    "key": random.choice(base_keys),
                    "delay_ms": random.randint(1, 100),
                    "text": random.choice(self.text_samples) if random.random() > 0.3 else None
                }
                pattern["operations"].append(operation)
            
            patterns.append(pattern)
        
        return patterns
    
    def generate_compression_test_data(self) -> List[Dict[str, Any]]:
        """
        Generate diverse data for compression efficiency testing.
        
        Creates different types of content that have varying compression
        characteristics to test cache compression performance:
        - Highly compressible (repetitive text)
        - Moderately compressible (natural language)
        - Poorly compressible (random content)
        - Structured data (JSON-like)
        
        Returns:
            List of test data items with expected compression ratios and
            descriptions of their compression characteristics
            
        Example:
            >>> generator = CacheBenchmarkDataGenerator()
            >>> compression_data = generator.generate_compression_test_data()
            >>> for item in compression_data:
            >>>     print(f"{item['type']}: "
            >>>           f"expected ratio {item['expected_compression_ratio']}")
        """
        test_data = []
        
        # Highly compressible data (repetitive text)
        repetitive_text = "This is a highly repetitive text pattern. " * 100
        test_data.append({
            "type": "highly_compressible",
            "text": repetitive_text,
            "expected_compression_ratio": 0.1,  # Very good compression
            "description": "Repetitive text with high compression potential"
        })
        
        # Moderately compressible data (natural text)
        natural_text = """
        Natural language text typically compresses moderately well due to patterns in
        language structure, common word usage, and repeated phrases. This type of content
        represents typical cache entries for text processing applications.
        """ * 20
        test_data.append({
            "type": "moderately_compressible",
            "text": natural_text,
            "expected_compression_ratio": 0.4,  # Moderate compression
            "description": "Natural language with moderate compression potential"
        })
        
        # Poorly compressible data (random-like content)
        random_text = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=10000))
        test_data.append({
            "type": "poorly_compressible",
            "text": random_text,
            "expected_compression_ratio": 0.9,  # Poor compression
            "description": "Random text with low compression potential"
        })
        
        # JSON-like structured data
        json_like_text = '''{"users": [{"id": %d, "name": "User %d", "email": "user%d@example.com", "data": "%s"}''' % (
            random.randint(1, 1000), random.randint(1, 1000), random.randint(1, 1000), "x" * 100
        ) + "]} " * 50
        test_data.append({
            "type": "structured_data",
            "text": json_like_text,
            "expected_compression_ratio": 0.3,  # Good compression for structured data
            "description": "JSON-like structured data with good compression potential"
        })
        
        return test_data