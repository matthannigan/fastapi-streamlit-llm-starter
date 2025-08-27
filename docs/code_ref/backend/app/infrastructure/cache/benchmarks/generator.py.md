---
sidebar_label: generator
---

# [REFACTORED] Comprehensive cache benchmark data generator with realistic workload simulation.

  file_path: `backend/app/infrastructure/cache/benchmarks/generator.py`

This module provides sophisticated test data generation for cache performance benchmarking
with realistic workload patterns that closely simulate production cache usage scenarios.
Generates varied datasets across multiple dimensions including size, complexity, content types,
and access patterns for comprehensive cache performance evaluation.

## Classes

CacheBenchmarkDataGenerator: Advanced data generator with realistic workload simulation

## Key Features

- **Realistic Data Patterns**: Multiple data types simulating real-world cache usage
including small key-value pairs, medium text content, large documents, and JSON objects.

- **Size Variation**: Comprehensive size distribution from small (30 bytes) to large
(multi-KB) entries with configurable scaling factors for memory pressure testing.

- **Content Diversity**: Natural language text, structured JSON data, repetitive content,
and random data for comprehensive compression and performance testing.

- **Workload Simulation**: Memory pressure scenarios, concurrent access patterns,
and operation type distribution matching production usage patterns.

- **Compression Testing**: Specialized data generation for compression efficiency analysis
with varying compressibility characteristics from highly compressible to random content.

- **Configurable Generation**: Flexible data generation with customizable iteration counts,
size distributions, and content complexity for different testing scenarios.

## Data Generation Categories

1. **Small Data Sets**: Simple key-value pairs (30 bytes) for basic operation testing
2. **Medium Data Sets**: Moderate text content (100-500 bytes) for typical cache usage
3. **Large Data Sets**: Extended documents (5-50KB) with structured content and lists
4. **JSON Data Sets**: Complex structured objects with metadata and processing history
5. **Realistic Data Sets**: Natural language content using template-based generation
6. **Memory Pressure Data**: Variable-sized content targeting specific memory usage
7. **Concurrent Patterns**: Multi-threaded access simulation with timing variations
8. **Compression Test Data**: Content with known compression characteristics

## Usage Examples

### Basic Data Generation

```python
generator = CacheBenchmarkDataGenerator()
basic_data = generator.generate_basic_operations_data(100)
print(f"Generated {len(basic_data)} test items")
for item in basic_data[:3]:
    print(f"Key: {item['key']}, Size: {item['expected_size_bytes']} bytes")
```

### Memory Pressure Testing

```python
memory_data = generator.generate_memory_pressure_data(10.0)  # 10MB target
total_size = sum(item['size_bytes'] for item in memory_data)
print(f"Generated {total_size / (1024*1024):.1f}MB of test data")
```

### Concurrent Access Simulation

```python
patterns = generator.generate_concurrent_access_patterns(5)
for pattern in patterns:
    print(f"Pattern {pattern['pattern_id']}: {len(pattern['operations'])} ops, "
          f"{pattern['concurrency_level']} threads")
```

### Compression Efficiency Testing

```python
compression_data = generator.generate_compression_test_data()
for item in compression_data:
    print(f"{item['type']}: expected ratio {item['expected_compression_ratio']}")
```

## Performance Considerations

- Data generation is optimized for realistic patterns without excessive computation
- Template-based text generation provides natural language characteristics
- Memory-efficient generation for large datasets using streaming approaches
- Configurable complexity allows balancing realism with generation speed

## Thread Safety

The data generator is stateless and thread-safe for concurrent benchmark execution.
Multiple generator instances can be used safely across threads without interference.
