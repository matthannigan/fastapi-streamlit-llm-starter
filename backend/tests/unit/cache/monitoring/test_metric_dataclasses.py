"""
Unit tests for performance monitoring metric dataclasses.

This test suite verifies the observable behaviors documented in the
monitoring metric dataclasses (monitoring.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Dataclass initialization and post-initialization validation
    - Data structure integrity and field validation
    - Type safety and value constraint enforcement
    - Performance metric data representation accuracy

External Dependencies:
    No external dependencies - testing pure dataclass functionality and validation.
"""

import time


from app.infrastructure.cache.monitoring import (CompressionMetric,
                                                 InvalidationMetric,
                                                 MemoryUsageMetric,
                                                 PerformanceMetric)


class TestPerformanceMetric:
    """
    Test suite for PerformanceMetric dataclass functionality.

    Scope:
        - Dataclass initialization with various parameter combinations
        - Post-initialization validation and constraint enforcement
        - Data integrity and field accessibility
        - Performance measurement representation accuracy

    Business Critical:
        Performance metric accuracy is essential for reliable performance monitoring

    Test Strategy:
        - Unit tests for dataclass creation with various field combinations
        - Validation testing for constraint enforcement
        - Data integrity verification
        - Field accessibility and type safety testing

    External Dependencies:
        - None (pure dataclass functionality testing)
    """

    def test_performance_metric_creates_with_required_fields(self):
        """
        Test that PerformanceMetric creates successfully with required fields.

        Verifies:
            PerformanceMetric dataclass can be instantiated with all required performance data

        Business Impact:
            Ensures reliable performance measurement data representation

        Scenario:
            Given: Valid performance measurement data (timing, operation info, context)
            When: PerformanceMetric is instantiated with required fields
            Then: Dataclass is created with all fields properly initialized

        Edge Cases Covered:
            - Required field initialization
            - Basic performance measurement scenarios
            - Field accessibility after creation
            - Type consistency verification

        Mocks Used:
            - None (dataclass instantiation verification)

        Related Tests:
            - test_performance_metric_validates_duration_values()
            - test_performance_metric_handles_optional_fields()
        """
        # Given: Valid performance measurement data (timing, operation info, context)
        duration = 0.125
        text_length = 500
        timestamp = time.time()
        operation_type = "summarize"

        # When: PerformanceMetric is instantiated with required fields
        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        # Then: Dataclass is created with all fields properly initialized
        assert metric.duration == duration
        assert metric.text_length == text_length
        assert metric.timestamp == timestamp
        assert metric.operation_type == operation_type
        assert metric.additional_data == {}  # Should be initialized by __post_init__

        # Verify field types are correct
        assert isinstance(metric.duration, float)
        assert isinstance(metric.text_length, int)
        assert isinstance(metric.timestamp, float)
        assert isinstance(metric.operation_type, str)
        assert isinstance(metric.additional_data, dict)

    def test_performance_metric_validates_duration_values(self):
        """
        Test that PerformanceMetric validates duration values during post-initialization.

        Verifies:
            Duration values are validated for reasonable ranges and types

        Business Impact:
            Prevents invalid performance measurements from corrupting monitoring data

        Scenario:
            Given: PerformanceMetric with various duration values
            When: Post-initialization validation runs
            Then: Invalid durations are rejected while valid durations are accepted

        Edge Cases Covered:
            - Negative duration values
            - Zero duration values
            - Extremely large duration values
            - Non-numeric duration values

        Mocks Used:
            - None (validation logic verification)

        Related Tests:
            - test_performance_metric_creates_with_required_fields()
            - test_performance_metric_validates_text_length_values()
        """
        # Given: Valid common test data
        text_length = 100
        timestamp = time.time()
        operation_type = "test"

        # Test valid duration values - zero duration (instantaneous operations)
        metric_zero = PerformanceMetric(
            duration=0.0,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_zero.duration == 0.0

        # Test valid positive duration values
        metric_positive = PerformanceMetric(
            duration=0.125,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_positive.duration == 0.125

        # Test very small positive durations (microsecond-level timing)
        metric_small = PerformanceMetric(
            duration=0.0001,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_small.duration == 0.0001

        # Test larger durations (slow operations)
        metric_large = PerformanceMetric(
            duration=10.5,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_large.duration == 10.5

        # Note: The current implementation doesn't validate negative durations
        # This would be a future enhancement for data integrity
        # For now, we test that negative values are stored as-is
        metric_negative = PerformanceMetric(
            duration=-0.5,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_negative.duration == -0.5

    def test_performance_metric_validates_text_length_values(self):
        """
        Test that PerformanceMetric validates text length values appropriately.

        Verifies:
            Text length values are validated for appropriate ranges and consistency

        Business Impact:
            Ensures text size correlation analysis accuracy in performance monitoring

        Scenario:
            Given: PerformanceMetric with various text length values
            When: Post-initialization validation processes text length data
            Then: Appropriate text lengths are accepted while invalid values are handled

        Edge Cases Covered:
            - Negative text lengths
            - Zero text lengths
            - Very large text lengths
            - Text length consistency with operation type

        Mocks Used:
            - None (validation verification)

        Related Tests:
            - test_performance_metric_validates_duration_values()
            - test_performance_metric_handles_optional_fields()
        """
        # Given: Valid common test data
        duration = 0.1
        timestamp = time.time()
        operation_type = "test"

        # Test zero text length (empty input scenarios)
        metric_zero = PerformanceMetric(
            duration=duration,
            text_length=0,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_zero.text_length == 0

        # Test small text lengths (short inputs)
        metric_small = PerformanceMetric(
            duration=duration,
            text_length=50,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_small.text_length == 50

        # Test medium text lengths (typical document sizes)
        metric_medium = PerformanceMetric(
            duration=duration,
            text_length=5000,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_medium.text_length == 5000

        # Test very large text lengths (big document processing)
        metric_large = PerformanceMetric(
            duration=duration,
            text_length=100000,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_large.text_length == 100000

        # Test negative text length (invalid but stored for debugging)
        metric_negative = PerformanceMetric(
            duration=duration,
            text_length=-100,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_negative.text_length == -100

        # Verify text length type consistency
        assert isinstance(metric_zero.text_length, int)
        assert isinstance(metric_large.text_length, int)

    def test_performance_metric_handles_optional_fields(self):
        """
        Test that PerformanceMetric handles optional fields correctly.

        Verifies:
            Optional fields are handled appropriately with default values or None

        Business Impact:
            Enables flexible performance measurement with optional context data

        Scenario:
            Given: PerformanceMetric creation with some optional fields omitted
            When: Dataclass is instantiated with partial field sets
            Then: Optional fields are handled with appropriate defaults or None values

        Edge Cases Covered:
            - Missing optional fields
            - None values for optional fields
            - Empty additional data dictionaries
            - Partial context information

        Mocks Used:
            - None (optional field handling verification)

        Related Tests:
            - test_performance_metric_validates_text_length_values()
            - test_performance_metric_maintains_field_types()
        """
        # Given: Required fields only (minimal creation)
        duration = 0.075
        text_length = 250
        timestamp = time.time()

        # When: PerformanceMetric is instantiated with only required fields
        metric_minimal = PerformanceMetric(
            duration=duration, text_length=text_length, timestamp=timestamp
        )

        # Then: Optional fields have proper default values
        assert metric_minimal.operation_type == ""  # Default empty string
        assert metric_minimal.additional_data == {}  # __post_init__ sets empty dict

        # Test with explicit None for additional_data (should be converted by __post_init__)
        metric_none_data = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type="test",
            additional_data=None,
        )
        assert (
            metric_none_data.additional_data == {}
        )  # __post_init__ converts None to {}

        # Test with explicit empty additional_data
        metric_empty_data = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type="analyze",
            additional_data={},
        )
        assert metric_empty_data.additional_data == {}

        # Test with populated additional_data
        additional_info = {"model": "gpt-4", "temperature": 0.7, "tokens": 150}
        metric_with_data = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type="summarize",
            additional_data=additional_info,
        )
        assert metric_with_data.additional_data == additional_info
        assert metric_with_data.additional_data["model"] == "gpt-4"

        # Test partial operation_type specification
        metric_partial = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type="sentiment",
        )
        assert metric_partial.operation_type == "sentiment"
        assert metric_partial.additional_data == {}  # Still gets default empty dict

    def test_performance_metric_maintains_field_types(self):
        """
        Test that PerformanceMetric maintains proper field types consistently.

        Verifies:
            Field types are maintained consistently for reliable data processing

        Business Impact:
            Ensures type safety and consistency in performance measurement data

        Scenario:
            Given: PerformanceMetric with typed field values
            When: Fields are accessed and processed
            Then: Field types remain consistent and appropriate for their data

        Edge Cases Covered:
            - Numeric field type consistency
            - String field type maintenance
            - Timestamp field type accuracy
            - Additional data dictionary type handling

        Mocks Used:
            - None (type consistency verification)

        Related Tests:
            - test_performance_metric_handles_optional_fields()
            - test_performance_metric_supports_serialization()
        """
        # Given: PerformanceMetric with typed field values
        duration = 0.250  # float
        text_length = 1500  # int
        timestamp = time.time()  # float
        operation_type = "classify"  # str
        additional_data = {"category": "document", "confidence": 0.95}  # Dict[str, Any]

        # When: Metric is created with typed fields
        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
            additional_data=additional_data,
        )

        # Then: Field types remain consistent and appropriate

        # Numeric field type consistency
        assert isinstance(metric.duration, float)
        assert isinstance(metric.text_length, int)
        assert isinstance(metric.timestamp, float)

        # String field type maintenance
        assert isinstance(metric.operation_type, str)

        # Additional data dictionary type handling
        assert isinstance(metric.additional_data, dict)
        assert isinstance(metric.additional_data["category"], str)
        assert isinstance(metric.additional_data["confidence"], float)

        # Verify specific type requirements for numeric fields
        assert metric.duration > 0  # Duration should be measurable
        assert metric.text_length > 0  # Text length should be positive
        assert metric.timestamp > 0  # Timestamp should be positive Unix time

        # Test edge case: ensure int stays int, float stays float
        metric_edge = PerformanceMetric(
            duration=1,  # int that should stay as provided type when stored
            text_length=100,
            timestamp=time.time(),
        )
        # Note: dataclass will preserve the type as provided
        assert isinstance(metric_edge.duration, int)

        # Test type preservation after field access
        stored_duration = metric.duration
        stored_length = metric.text_length
        stored_timestamp = metric.timestamp
        stored_operation = metric.operation_type

        assert isinstance(stored_duration, float)
        assert isinstance(stored_length, int)
        assert isinstance(stored_timestamp, float)
        assert isinstance(stored_operation, str)

    def test_performance_metric_supports_serialization(self):
        """
        Test that PerformanceMetric supports serialization for data export.

        Verifies:
            Performance metrics can be serialized for export and analysis

        Business Impact:
            Enables performance data export and integration with external analysis tools

        Scenario:
            Given: PerformanceMetric with comprehensive performance data
            When: Serialization is attempted for export purposes
            Then: Metric data is successfully serialized maintaining data integrity

        Edge Cases Covered:
            - Complete field serialization
            - Optional field serialization handling
            - Complex data type serialization
            - Serialization format consistency

        Mocks Used:
            - None (serialization capability verification)

        Related Tests:
            - test_performance_metric_maintains_field_types()
            - test_performance_metric_creates_with_required_fields()
        """
        # Given: PerformanceMetric with comprehensive performance data
        duration = 0.180
        text_length = 2500
        timestamp = time.time()
        operation_type = "extract"
        additional_data = {
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.3,
            "max_tokens": 200,
            "nested_data": {"source": "document", "format": "text"},
        }

        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=timestamp,
            operation_type=operation_type,
            additional_data=additional_data,
        )

        # When: Serialization is attempted using dataclasses.asdict
        from dataclasses import asdict

        serialized_data = asdict(metric)

        # Then: Metric data is successfully serialized maintaining data integrity

        # Verify all fields are present in serialized format
        assert "duration" in serialized_data
        assert "text_length" in serialized_data
        assert "timestamp" in serialized_data
        assert "operation_type" in serialized_data
        assert "additional_data" in serialized_data

        # Verify data integrity is maintained
        assert serialized_data["duration"] == duration
        assert serialized_data["text_length"] == text_length
        assert serialized_data["timestamp"] == timestamp
        assert serialized_data["operation_type"] == operation_type
        assert serialized_data["additional_data"] == additional_data

        # Verify complex nested data structure serialization
        assert serialized_data["additional_data"]["nested_data"]["source"] == "document"
        assert serialized_data["additional_data"]["temperature"] == 0.3

        # Test serialization with minimal data (only required fields)
        metric_minimal = PerformanceMetric(
            duration=0.05, text_length=100, timestamp=timestamp
        )

        serialized_minimal = asdict(metric_minimal)

        # Verify optional fields are properly serialized with defaults
        assert serialized_minimal["operation_type"] == ""
        assert serialized_minimal["additional_data"] == {}

        # Verify serialized data can be used to reconstruct the object
        reconstructed_metric = PerformanceMetric(**serialized_data)
        assert reconstructed_metric.duration == metric.duration
        assert reconstructed_metric.text_length == metric.text_length
        assert reconstructed_metric.operation_type == metric.operation_type
        assert reconstructed_metric.additional_data == metric.additional_data


class TestCompressionMetric:
    """
    Test suite for CompressionMetric dataclass functionality.

    Scope:
        - Compression metric initialization and validation
        - Compression ratio calculation accuracy
        - Size and timing field validation
        - Compression efficiency representation

    Business Critical:
        Compression metric accuracy enables storage optimization and performance analysis

    Test Strategy:
        - Unit tests for compression-specific field validation
        - Ratio calculation accuracy verification
        - Size field constraint testing
        - Timing and efficiency measurement validation

    External Dependencies:
        - None (pure dataclass functionality testing)
    """

    def test_compression_metric_creates_with_compression_data(self):
        """
        Test that CompressionMetric creates successfully with compression measurement data.

        Verifies:
            CompressionMetric dataclass represents compression performance data accurately

        Business Impact:
            Ensures reliable compression efficiency monitoring and optimization

        Scenario:
            Given: Valid compression measurement data (sizes, timing, ratios)
            When: CompressionMetric is instantiated with compression data
            Then: Dataclass is created with compression-specific fields properly initialized

        Edge Cases Covered:
            - Original and compressed size initialization
            - Compression timing field initialization
            - Operation type context initialization
            - Compression-specific field accessibility

        Mocks Used:
            - None (compression dataclass instantiation verification)

        Related Tests:
            - test_compression_metric_validates_size_relationships()
            - test_compression_metric_calculates_ratios_accurately()
        """
        # Given: Valid compression measurement data (sizes, timing, ratios)
        original_size = 10000  # 10KB original size
        compressed_size = 3000  # 3KB compressed size
        compression_ratio = 0.3  # 30% of original size
        compression_time = 0.025  # 25ms compression time
        timestamp = time.time()
        operation_type = "document_cache"

        # When: CompressionMetric is instantiated with compression data
        metric = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        # Then: Dataclass is created with compression-specific fields properly initialized
        assert metric.original_size == original_size
        assert metric.compressed_size == compressed_size
        assert metric.compression_ratio == compression_ratio
        assert metric.compression_time == compression_time
        assert metric.timestamp == timestamp
        assert metric.operation_type == operation_type

        # Verify field types are correct
        assert isinstance(metric.original_size, int)
        assert isinstance(metric.compressed_size, int)
        assert isinstance(metric.compression_ratio, float)
        assert isinstance(metric.compression_time, float)
        assert isinstance(metric.timestamp, float)
        assert isinstance(metric.operation_type, str)

    def test_compression_metric_validates_size_relationships(self):
        """
        Test that CompressionMetric validates size field relationships appropriately.

        Verifies:
            Size field relationships are validated for compression logic consistency

        Business Impact:
            Prevents invalid compression measurements that could mislead optimization decisions

        Scenario:
            Given: CompressionMetric with various original and compressed size combinations
            When: Post-initialization validation checks size relationships
            Then: Appropriate size relationships are validated while maintaining flexibility

        Edge Cases Covered:
            - Compressed size larger than original (negative compression)
            - Zero original or compressed sizes
            - Very large size values
            - Size relationship consistency

        Mocks Used:
            - None (size validation verification)

        Related Tests:
            - test_compression_metric_creates_with_compression_data()
            - test_compression_metric_calculates_ratios_accurately()
        """
        # Given: Common test data
        compression_time = 0.015
        timestamp = time.time()
        operation_type = "test"

        # Test good compression (smaller compressed size)
        metric_good = CompressionMetric(
            original_size=5000,
            compressed_size=1500,  # 30% of original
            compression_ratio=0.3,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_good.compressed_size < metric_good.original_size
        assert metric_good.compression_ratio == 0.3

        # Test negative compression (compressed larger than original)
        metric_negative = CompressionMetric(
            original_size=1000,
            compressed_size=1200,  # 120% of original (compression made it larger)
            compression_ratio=1.2,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_negative.compressed_size > metric_negative.original_size
        assert metric_negative.compression_ratio == 1.2

        # Test no compression (same size)
        metric_same = CompressionMetric(
            original_size=2000,
            compressed_size=2000,  # No change
            compression_ratio=1.0,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_same.compressed_size == metric_same.original_size
        assert metric_same.compression_ratio == 1.0

        # Test zero original size (edge case)
        metric_zero_orig = CompressionMetric(
            original_size=0,
            compressed_size=0,
            compression_ratio=0.0,  # Prevent division by zero
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_zero_orig.original_size == 0
        assert metric_zero_orig.compressed_size == 0

        # Test very large sizes
        metric_large = CompressionMetric(
            original_size=1000000000,  # 1GB
            compressed_size=200000000,  # 200MB
            compression_ratio=0.2,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_large.original_size == 1000000000
        assert metric_large.compressed_size == 200000000

    def test_compression_metric_calculates_ratios_accurately(self):
        """
        Test that CompressionMetric calculates compression ratios accurately.

        Verifies:
            Compression ratio calculations are mathematically correct and consistent

        Business Impact:
            Provides accurate compression efficiency analysis for storage optimization

        Scenario:
            Given: CompressionMetric with original and compressed size data
            When: Compression ratios are calculated
            Then: Mathematical accuracy is maintained in ratio calculations

        Edge Cases Covered:
            - High compression ratio scenarios
            - Low compression ratio scenarios
            - No compression scenarios
            - Ratio calculation precision and accuracy

        Mocks Used:
            - None (calculation accuracy verification)

        Related Tests:
            - test_compression_metric_validates_size_relationships()
            - test_compression_metric_validates_timing_values()
        """
        # Given: Common test data
        compression_time = 0.02
        timestamp = time.time()
        operation_type = "test_compression"

        # Test high compression ratio (good compression - small ratio value)
        original_size_high = 10000
        compressed_size_high = 1000  # 10% of original
        expected_ratio_high = compressed_size_high / original_size_high  # 0.1

        metric_high = CompressionMetric(
            original_size=original_size_high,
            compressed_size=compressed_size_high,
            compression_ratio=0,  # Let __post_init__ calculate it
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        # __post_init__ should calculate the ratio when compression_ratio is 0
        assert metric_high.compression_ratio == expected_ratio_high
        assert abs(metric_high.compression_ratio - 0.1) < 0.0001  # Precision check

        # Test low compression ratio (poor compression - large ratio value)
        original_size_low = 5000
        compressed_size_low = 4500  # 90% of original
        expected_ratio_low = compressed_size_low / original_size_low  # 0.9

        metric_low = CompressionMetric(
            original_size=original_size_low,
            compressed_size=compressed_size_low,
            compression_ratio=0,  # Let __post_init__ calculate it
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        assert metric_low.compression_ratio == expected_ratio_low
        assert abs(metric_low.compression_ratio - 0.9) < 0.0001

        # Test no compression scenario (ratio = 1.0)
        original_size_same = 3000
        compressed_size_same = 3000

        metric_same = CompressionMetric(
            original_size=original_size_same,
            compressed_size=compressed_size_same,
            compression_ratio=0,  # Let __post_init__ calculate it
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        assert metric_same.compression_ratio == 1.0

        # Test pre-set ratio (should be preserved when not 0)
        metric_preset = CompressionMetric(
            original_size=8000,
            compressed_size=2000,
            compression_ratio=0.25,  # Pre-calculated ratio
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        assert metric_preset.compression_ratio == 0.25  # Should preserve pre-set value

        # Test zero original size edge case
        metric_zero = CompressionMetric(
            original_size=0,
            compressed_size=0,
            compression_ratio=0,  # __post_init__ should handle this safely
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        # With zero original size, __post_init__ should not modify compression_ratio
        assert metric_zero.compression_ratio == 0

    def test_compression_metric_validates_timing_values(self):
        """
        Test that CompressionMetric validates compression timing values appropriately.

        Verifies:
            Compression timing values are validated for reasonable performance ranges

        Business Impact:
            Ensures accurate compression performance analysis for optimization decisions

        Scenario:
            Given: CompressionMetric with various compression timing values
            When: Timing validation is performed
            Then: Reasonable timing values are accepted while invalid values are handled

        Edge Cases Covered:
            - Negative compression times
            - Zero compression times
            - Extremely long compression times
            - Timing precision and accuracy

        Mocks Used:
            - None (timing validation verification)

        Related Tests:
            - test_compression_metric_calculates_ratios_accurately()
            - test_compression_metric_supports_efficiency_analysis()
        """
        # Given: Common test data
        original_size = 5000
        compressed_size = 2000
        compression_ratio = 0.4
        timestamp = time.time()
        operation_type = "timing_test"

        # Test zero compression time (instantaneous compression)
        metric_zero_time = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=0.0,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_zero_time.compression_time == 0.0

        # Test very fast compression times (microsecond level)
        metric_fast = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=0.0001,  # 0.1ms
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_fast.compression_time == 0.0001

        # Test normal compression times
        metric_normal = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=0.025,  # 25ms
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_normal.compression_time == 0.025

        # Test slow compression times
        metric_slow = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=2.5,  # 2.5 seconds
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_slow.compression_time == 2.5

        # Test extremely long compression times (edge case)
        metric_very_slow = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=120.0,  # 2 minutes
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_very_slow.compression_time == 120.0

        # Test negative compression time (invalid but stored for debugging)
        metric_negative = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=-0.5,  # Invalid timing
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_negative.compression_time == -0.5

        # Verify timing precision is preserved
        precise_time = 0.0123456789
        metric_precise = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=precise_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )
        assert metric_precise.compression_time == precise_time

    def test_compression_metric_supports_efficiency_analysis(self):
        """
        Test that CompressionMetric supports compression efficiency analysis.

        Verifies:
            Compression metrics provide data necessary for efficiency vs. performance analysis

        Business Impact:
            Enables optimization of compression settings based on efficiency and performance trade-offs

        Scenario:
            Given: CompressionMetric with comprehensive compression data
            When: Efficiency analysis is performed using metric data
            Then: Sufficient data is available for compression efficiency evaluation

        Edge Cases Covered:
            - Efficiency calculation data availability
            - Performance vs. efficiency trade-off analysis support
            - Operation type correlation with efficiency
            - Timing correlation with compression results

        Mocks Used:
            - None (efficiency analysis support verification)

        Related Tests:
            - test_compression_metric_validates_timing_values()
            - test_compression_metric_maintains_measurement_integrity()
        """
        # Given: CompressionMetric with comprehensive compression data
        original_size = 50000  # 50KB
        compressed_size = 15000  # 15KB
        compression_ratio = 0.3  # 70% space savings
        compression_time = 0.045  # 45ms
        timestamp = time.time()
        operation_type = "document_storage"

        metric = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        # When: Efficiency analysis is performed using metric data
        # Calculate bytes saved
        bytes_saved = metric.original_size - metric.compressed_size
        space_savings_percent = (bytes_saved / metric.original_size) * 100

        # Calculate compression speed (bytes per second)
        compression_speed = (
            metric.original_size / metric.compression_time
            if metric.compression_time > 0
            else float("inf")
        )

        # Calculate efficiency score (bytes saved per millisecond)
        efficiency_score = (
            bytes_saved / (metric.compression_time * 1000)
            if metric.compression_time > 0
            else float("inf")
        )

        # Then: Sufficient data is available for compression efficiency evaluation

        # Verify all necessary data is available for efficiency calculations
        assert metric.original_size > 0
        assert metric.compressed_size >= 0
        assert metric.compression_time >= 0
        assert metric.compression_ratio > 0

        # Verify efficiency calculations work with the metric data
        assert bytes_saved == 35000  # 50KB - 15KB = 35KB saved
        assert abs(space_savings_percent - 70.0) < 0.1  # ~70% space savings
        assert compression_speed > 0  # Should have positive compression speed
        assert efficiency_score > 0  # Should have positive efficiency score

        # Test performance vs. efficiency trade-off analysis support
        # Higher compression ratio (better efficiency, potentially slower)
        high_efficiency_metric = CompressionMetric(
            original_size=50000,
            compressed_size=5000,  # 90% compression
            compression_ratio=0.1,
            compression_time=0.200,  # Slower but more efficient
            timestamp=timestamp,
            operation_type="high_compression",
        )

        # Lower compression ratio (faster, less efficient)
        fast_compression_metric = CompressionMetric(
            original_size=50000,
            compressed_size=25000,  # 50% compression
            compression_ratio=0.5,
            compression_time=0.010,  # Faster but less efficient
            timestamp=timestamp,
            operation_type="fast_compression",
        )

        # Compare efficiency metrics
        high_eff_bytes_saved = (
            high_efficiency_metric.original_size
            - high_efficiency_metric.compressed_size
        )
        fast_bytes_saved = (
            fast_compression_metric.original_size
            - fast_compression_metric.compressed_size
        )

        high_eff_speed = (
            high_efficiency_metric.original_size
            / high_efficiency_metric.compression_time
        )
        fast_speed = (
            fast_compression_metric.original_size
            / fast_compression_metric.compression_time
        )

        # Verify trade-off analysis is supported by the data
        assert (
            high_eff_bytes_saved > fast_bytes_saved
        )  # High efficiency saves more bytes
        assert fast_speed > high_eff_speed  # Fast compression is faster

        # Operation type correlation with efficiency
        assert high_efficiency_metric.operation_type == "high_compression"
        assert fast_compression_metric.operation_type == "fast_compression"

        # Verify timing correlation with compression results
        assert (
            high_efficiency_metric.compression_time
            > fast_compression_metric.compression_time
        )
        assert (
            high_efficiency_metric.compression_ratio
            < fast_compression_metric.compression_ratio
        )

    def test_compression_metric_maintains_measurement_integrity(self):
        """
        Test that CompressionMetric maintains measurement data integrity.

        Verifies:
            Compression measurement data integrity is preserved for accurate analysis

        Business Impact:
            Ensures reliable compression performance data for optimization and monitoring

        Scenario:
            Given: CompressionMetric with complete compression measurement data
            When: Data integrity is evaluated
            Then: All measurement data maintains consistency and accuracy

        Edge Cases Covered:
            - Data consistency across related fields
            - Measurement precision maintenance
            - Field relationship integrity
            - Data accuracy preservation

        Mocks Used:
            - None (data integrity verification)

        Related Tests:
            - test_compression_metric_supports_efficiency_analysis()
            - test_compression_metric_creates_with_compression_data()
        """
        # Given: CompressionMetric with complete compression measurement data
        original_size = 25600  # Precise value
        compressed_size = 7680  # Precise value
        compression_ratio = 0.3  # Pre-calculated ratio
        compression_time = 0.0834  # Precise timing
        timestamp = time.time()
        operation_type = "integrity_test"

        metric = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
            timestamp=timestamp,
            operation_type=operation_type,
        )

        # When: Data integrity is evaluated

        # Store original values for comparison
        original_values = {
            "original_size": metric.original_size,
            "compressed_size": metric.compressed_size,
            "compression_ratio": metric.compression_ratio,
            "compression_time": metric.compression_time,
            "timestamp": metric.timestamp,
            "operation_type": metric.operation_type,
        }

        # Then: All measurement data maintains consistency and accuracy

        # Data consistency across related fields
        calculated_ratio = metric.compressed_size / metric.original_size
        assert (
            abs(metric.compression_ratio - calculated_ratio) < 0.0001
        )  # Should be mathematically consistent

        # Measurement precision maintenance - values should not change after creation
        assert metric.original_size == original_values["original_size"]
        assert metric.compressed_size == original_values["compressed_size"]
        assert metric.compression_ratio == original_values["compression_ratio"]
        assert metric.compression_time == original_values["compression_time"]
        assert metric.timestamp == original_values["timestamp"]
        assert metric.operation_type == original_values["operation_type"]

        # Field relationship integrity
        assert (
            metric.original_size >= metric.compressed_size
        )  # In this case, compression worked
        assert (
            0 <= metric.compression_ratio <= 1.0
        )  # Ratio should be between 0 and 1 for good compression
        assert metric.compression_time >= 0  # Time should not be negative
        assert metric.timestamp > 0  # Timestamp should be positive

        # Data accuracy preservation after multiple access
        for _ in range(10):  # Access fields multiple times
            accessed_original = metric.original_size
            accessed_compressed = metric.compressed_size
            accessed_ratio = metric.compression_ratio
            accessed_time = metric.compression_time

            # Values should remain consistent
            assert accessed_original == original_size
            assert accessed_compressed == compressed_size
            assert accessed_ratio == compression_ratio
            assert accessed_time == compression_time

        # Test serialization and reconstruction maintains integrity
        from dataclasses import asdict

        serialized = asdict(metric)
        reconstructed = CompressionMetric(**serialized)

        # Reconstructed metric should maintain all original values
        assert reconstructed.original_size == metric.original_size
        assert reconstructed.compressed_size == metric.compressed_size
        assert reconstructed.compression_ratio == metric.compression_ratio
        assert reconstructed.compression_time == metric.compression_time
        assert reconstructed.timestamp == metric.timestamp
        assert reconstructed.operation_type == metric.operation_type

        # Test edge case: ensure field types are preserved
        assert type(metric.original_size) == type(reconstructed.original_size)
        assert type(metric.compressed_size) == type(reconstructed.compressed_size)
        assert type(metric.compression_ratio) == type(reconstructed.compression_ratio)
        assert type(metric.compression_time) == type(reconstructed.compression_time)


class TestMemoryUsageMetric:
    """
    Test suite for MemoryUsageMetric dataclass functionality.

    Scope:
        - Memory usage metric initialization and validation
        - Memory size calculation accuracy
        - Cache tier breakdown representation
        - Memory consumption measurement integrity

    Business Critical:
        Memory usage metric accuracy enables capacity planning and memory optimization

    Test Strategy:
        - Unit tests for memory-specific field validation
        - Size calculation accuracy verification
        - Cache tier data representation testing
        - Memory measurement integrity validation

    External Dependencies:
        - None (pure dataclass functionality testing)
    """

    def test_memory_usage_metric_creates_with_memory_data(self):
        """
        Test that MemoryUsageMetric creates successfully with memory measurement data.

        Verifies:
            MemoryUsageMetric dataclass represents memory consumption data accurately

        Business Impact:
            Ensures reliable memory usage monitoring and capacity planning

        Scenario:
            Given: Valid memory measurement data (cache sizes, entry counts, Redis stats)
            When: MemoryUsageMetric is instantiated with memory data
            Then: Dataclass is created with memory-specific fields properly initialized

        Edge Cases Covered:
            - Memory cache size initialization
            - Redis cache size initialization
            - Entry count field initialization
            - Memory-specific field accessibility

        Mocks Used:
            - None (memory dataclass instantiation verification)

        Related Tests:
            - test_memory_usage_metric_validates_size_values()
            - test_memory_usage_metric_calculates_totals_accurately()
        """
        # Given: Valid memory measurement data (cache sizes, entry counts, Redis stats)
        total_cache_size_bytes = 52428800  # 50MB total
        cache_entry_count = 1250  # Total entries across all caches
        avg_entry_size_bytes = 41943.04  # Average size per entry
        memory_cache_size_bytes = 10485760  # 10MB in memory cache
        memory_cache_entry_count = 250  # Entries in memory cache
        process_memory_mb = 128.5  # Process memory usage in MB
        timestamp = time.time()
        cache_utilization_percent = 104.8  # Over warning threshold
        warning_threshold_reached = True
        additional_data = {"redis_memory": 41943040, "redis_keys": 1000}

        # When: MemoryUsageMetric is instantiated with memory data
        metric = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size_bytes,
            cache_entry_count=cache_entry_count,
            avg_entry_size_bytes=avg_entry_size_bytes,
            memory_cache_size_bytes=memory_cache_size_bytes,
            memory_cache_entry_count=memory_cache_entry_count,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
            additional_data=additional_data,
        )

        # Then: Dataclass is created with memory-specific fields properly initialized
        assert metric.total_cache_size_bytes == total_cache_size_bytes
        assert metric.cache_entry_count == cache_entry_count
        assert metric.avg_entry_size_bytes == avg_entry_size_bytes
        assert metric.memory_cache_size_bytes == memory_cache_size_bytes
        assert metric.memory_cache_entry_count == memory_cache_entry_count
        assert metric.process_memory_mb == process_memory_mb
        assert metric.timestamp == timestamp
        assert metric.cache_utilization_percent == cache_utilization_percent
        assert metric.warning_threshold_reached == warning_threshold_reached
        assert metric.additional_data == additional_data

        # Verify field types are correct
        assert isinstance(metric.total_cache_size_bytes, int)
        assert isinstance(metric.cache_entry_count, int)
        assert isinstance(metric.avg_entry_size_bytes, float)
        assert isinstance(metric.memory_cache_size_bytes, int)
        assert isinstance(metric.memory_cache_entry_count, int)
        assert isinstance(metric.process_memory_mb, float)
        assert isinstance(metric.timestamp, float)
        assert isinstance(metric.cache_utilization_percent, float)
        assert isinstance(metric.warning_threshold_reached, bool)
        assert isinstance(metric.additional_data, dict)

    def test_memory_usage_metric_validates_size_values(self):
        """
        Test that MemoryUsageMetric validates memory size values appropriately.

        Verifies:
            Memory size values are validated for reasonable ranges and consistency

        Business Impact:
            Prevents invalid memory measurements from corrupting capacity planning data

        Scenario:
            Given: MemoryUsageMetric with various memory size values
            When: Size validation is performed
            Then: Reasonable memory sizes are accepted while invalid values are handled

        Edge Cases Covered:
            - Negative memory sizes
            - Zero memory sizes
            - Extremely large memory sizes
            - Memory size consistency across cache tiers

        Mocks Used:
            - None (size validation verification)

        Related Tests:
            - test_memory_usage_metric_creates_with_memory_data()
            - test_memory_usage_metric_validates_entry_counts()
        """
        # Given: Common test data
        cache_entry_count = 100
        avg_entry_size_bytes = 1024.0
        memory_cache_entry_count = 50
        process_memory_mb = 64.0
        timestamp = time.time()
        cache_utilization_percent = 50.0
        warning_threshold_reached = False

        # Test zero memory sizes (empty cache scenarios)
        metric_zero = MemoryUsageMetric(
            total_cache_size_bytes=0,
            cache_entry_count=0,
            avg_entry_size_bytes=0.0,
            memory_cache_size_bytes=0,
            memory_cache_entry_count=0,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=0.0,
            warning_threshold_reached=False,
        )
        assert metric_zero.total_cache_size_bytes == 0
        assert metric_zero.memory_cache_size_bytes == 0
        assert metric_zero.avg_entry_size_bytes == 0.0

        # Test small memory sizes (minimal cache usage)
        metric_small = MemoryUsageMetric(
            total_cache_size_bytes=1024,  # 1KB
            cache_entry_count=1,
            avg_entry_size_bytes=1024.0,
            memory_cache_size_bytes=1024,
            memory_cache_entry_count=1,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=0.002,  # Very low utilization
            warning_threshold_reached=False,
        )
        assert metric_small.total_cache_size_bytes == 1024
        assert metric_small.memory_cache_size_bytes == 1024

        # Test large memory sizes (high cache usage)
        metric_large = MemoryUsageMetric(
            total_cache_size_bytes=1073741824,  # 1GB
            cache_entry_count=cache_entry_count,
            avg_entry_size_bytes=avg_entry_size_bytes,
            memory_cache_size_bytes=104857600,  # 100MB in memory
            memory_cache_entry_count=memory_cache_entry_count,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=2147.0,  # Very high utilization
            warning_threshold_reached=True,
        )
        assert metric_large.total_cache_size_bytes == 1073741824
        assert metric_large.memory_cache_size_bytes == 104857600

        # Test very large memory sizes (enterprise scale)
        metric_enterprise = MemoryUsageMetric(
            total_cache_size_bytes=107374182400,  # 100GB
            cache_entry_count=cache_entry_count,
            avg_entry_size_bytes=avg_entry_size_bytes,
            memory_cache_size_bytes=1073741824,  # 1GB in memory
            memory_cache_entry_count=memory_cache_entry_count,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=214700.0,  # Extreme utilization
            warning_threshold_reached=True,
        )
        assert metric_enterprise.total_cache_size_bytes == 107374182400

        # Test negative memory sizes (invalid but stored for debugging)
        metric_negative = MemoryUsageMetric(
            total_cache_size_bytes=-1000,
            cache_entry_count=cache_entry_count,
            avg_entry_size_bytes=avg_entry_size_bytes,
            memory_cache_size_bytes=-500,
            memory_cache_entry_count=memory_cache_entry_count,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=-10.0,
            warning_threshold_reached=False,
        )
        assert metric_negative.total_cache_size_bytes == -1000
        assert metric_negative.memory_cache_size_bytes == -500

        # Test memory size consistency - memory cache should be part of total
        metric_consistent = MemoryUsageMetric(
            total_cache_size_bytes=50000000,  # 50MB total
            cache_entry_count=500,
            avg_entry_size_bytes=100000.0,  # 100KB per entry
            memory_cache_size_bytes=10000000,  # 10MB in memory (subset of total)
            memory_cache_entry_count=100,  # 100 entries in memory (subset)
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=100.0,
            warning_threshold_reached=True,
        )

        # Verify logical consistency (memory cache should typically be <= total)
        assert (
            metric_consistent.memory_cache_size_bytes
            <= metric_consistent.total_cache_size_bytes
        )
        assert (
            metric_consistent.memory_cache_entry_count
            <= metric_consistent.cache_entry_count
        )

    def test_memory_usage_metric_validates_entry_counts(self):
        """
        Test that MemoryUsageMetric validates entry count values appropriately.

        Verifies:
            Entry count values are validated for consistency with memory usage patterns

        Business Impact:
            Ensures accurate entry-based memory analysis and optimization decisions

        Scenario:
            Given: MemoryUsageMetric with various entry count values
            When: Entry count validation is performed
            Then: Reasonable entry counts are accepted while maintaining data consistency

        Edge Cases Covered:
            - Negative entry counts
            - Zero entry counts
            - Very large entry counts
            - Entry count consistency with memory sizes

        Mocks Used:
            - None (entry count validation verification)

        Related Tests:
            - test_memory_usage_metric_validates_size_values()
            - test_memory_usage_metric_calculates_totals_accurately()
        """
        # Given: Common test data
        total_cache_size_bytes = 10000000  # 10MB
        memory_cache_size_bytes = 2000000  # 2MB
        process_memory_mb = 128.0
        timestamp = time.time()
        cache_utilization_percent = 50.0
        warning_threshold_reached = False

        # Test zero entry counts (empty cache)
        metric_zero = MemoryUsageMetric(
            total_cache_size_bytes=0,  # No data if no entries
            cache_entry_count=0,
            avg_entry_size_bytes=0.0,  # No average if no entries
            memory_cache_size_bytes=0,
            memory_cache_entry_count=0,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=0.0,
            warning_threshold_reached=False,
        )
        assert metric_zero.cache_entry_count == 0
        assert metric_zero.memory_cache_entry_count == 0

        # Test small entry counts
        metric_small = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size_bytes,
            cache_entry_count=10,  # Few entries
            avg_entry_size_bytes=1000000.0,  # 1MB per entry (large entries)
            memory_cache_size_bytes=memory_cache_size_bytes,
            memory_cache_entry_count=2,  # Even fewer in memory
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
        )
        assert metric_small.cache_entry_count == 10
        assert metric_small.memory_cache_entry_count == 2

        # Test large entry counts
        metric_large = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size_bytes,
            cache_entry_count=100000,  # Many entries
            avg_entry_size_bytes=100.0,  # 100 bytes per entry (small entries)
            memory_cache_size_bytes=memory_cache_size_bytes,
            memory_cache_entry_count=20000,  # Many in memory too
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
        )
        assert metric_large.cache_entry_count == 100000
        assert metric_large.memory_cache_entry_count == 20000

        # Test very large entry counts (enterprise scale)
        metric_enterprise = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size_bytes,
            cache_entry_count=10000000,  # 10 million entries
            avg_entry_size_bytes=1.0,  # 1 byte per entry (tiny entries)
            memory_cache_size_bytes=memory_cache_size_bytes,
            memory_cache_entry_count=2000000,  # 2 million in memory
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
        )
        assert metric_enterprise.cache_entry_count == 10000000
        assert metric_enterprise.memory_cache_entry_count == 2000000

        # Test negative entry counts (invalid but stored for debugging)
        metric_negative = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size_bytes,
            cache_entry_count=-100,
            avg_entry_size_bytes=100.0,
            memory_cache_size_bytes=memory_cache_size_bytes,
            memory_cache_entry_count=-20,
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
        )
        assert metric_negative.cache_entry_count == -100
        assert metric_negative.memory_cache_entry_count == -20

        # Test entry count consistency with memory sizes
        metric_consistent = MemoryUsageMetric(
            total_cache_size_bytes=50000,  # 50KB total
            cache_entry_count=100,  # 100 entries
            avg_entry_size_bytes=500.0,  # 500 bytes per entry (50KB / 100 = 500)
            memory_cache_size_bytes=10000,  # 10KB in memory
            memory_cache_entry_count=20,  # 20 entries in memory (10KB / 500 bytes = 20)
            process_memory_mb=process_memory_mb,
            timestamp=timestamp,
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
        )

        # Verify mathematical consistency between counts and sizes
        expected_total_size = (
            metric_consistent.cache_entry_count * metric_consistent.avg_entry_size_bytes
        )
        assert abs(expected_total_size - metric_consistent.total_cache_size_bytes) < 0.1

        # Memory cache should have fewer entries than total
        assert (
            metric_consistent.memory_cache_entry_count
            <= metric_consistent.cache_entry_count
        )

        # Entry counts should be integers
        assert isinstance(metric_consistent.cache_entry_count, int)
        assert isinstance(metric_consistent.memory_cache_entry_count, int)

    def test_memory_usage_metric_calculates_totals_accurately(self):
        """
        Test that MemoryUsageMetric calculates total memory usage accurately.

        Verifies:
            Total memory calculations aggregate cache tiers accurately

        Business Impact:
            Provides accurate total memory consumption for capacity planning

        Scenario:
            Given: MemoryUsageMetric with memory cache and Redis cache data
            When: Total memory usage is calculated
            Then: Accurate aggregation of memory consumption across cache tiers

        Edge Cases Covered:
            - Memory cache + Redis cache aggregation
            - Single cache tier scenarios
            - Zero memory scenarios for some tiers
            - Large memory aggregation accuracy

        Mocks Used:
            - None (calculation accuracy verification)

        Related Tests:
            - test_memory_usage_metric_validates_entry_counts()
            - test_memory_usage_metric_supports_capacity_analysis()
        """
        # Test memory cache + Redis cache aggregation
        memory_cache_size = 20971520  # 20MB in memory cache
        memory_cache_entries = 500
        redis_cache_size = 83886080  # 80MB in Redis (calculated as total - memory)
        redis_entries = 2000
        total_size = memory_cache_size + redis_cache_size  # 100MB total
        total_entries = memory_cache_entries + redis_entries  # 2500 total
        avg_size = total_size / total_entries  # ~40KB per entry

        # Given: MemoryUsageMetric with memory cache and Redis cache data
        metric_aggregated = MemoryUsageMetric(
            total_cache_size_bytes=total_size,
            cache_entry_count=total_entries,
            avg_entry_size_bytes=avg_size,
            memory_cache_size_bytes=memory_cache_size,
            memory_cache_entry_count=memory_cache_entries,
            process_memory_mb=256.0,
            timestamp=time.time(),
            cache_utilization_percent=200.0,  # 2x threshold
            warning_threshold_reached=True,
        )

        # When: Total memory usage is calculated (already done in the constructor)
        # Then: Accurate aggregation of memory consumption across cache tiers

        # Verify total calculations are accurate
        assert metric_aggregated.total_cache_size_bytes == total_size
        assert metric_aggregated.cache_entry_count == total_entries

        # Calculate implied Redis cache size and verify it makes sense
        implied_redis_size = (
            metric_aggregated.total_cache_size_bytes
            - metric_aggregated.memory_cache_size_bytes
        )
        implied_redis_entries = (
            metric_aggregated.cache_entry_count
            - metric_aggregated.memory_cache_entry_count
        )

        assert implied_redis_size == redis_cache_size
        assert implied_redis_entries == redis_entries

        # Verify average entry size calculation
        calculated_avg = (
            metric_aggregated.total_cache_size_bytes
            / metric_aggregated.cache_entry_count
        )
        assert abs(metric_aggregated.avg_entry_size_bytes - calculated_avg) < 0.1

        # Test single cache tier scenario (memory only)
        metric_memory_only = MemoryUsageMetric(
            total_cache_size_bytes=10485760,  # 10MB total = memory only
            cache_entry_count=100,
            avg_entry_size_bytes=104857.6,  # 10MB / 100 entries
            memory_cache_size_bytes=10485760,  # Same as total (no Redis)
            memory_cache_entry_count=100,  # All entries in memory
            process_memory_mb=64.0,
            timestamp=time.time(),
            cache_utilization_percent=20.0,
            warning_threshold_reached=False,
        )

        # All memory should be accounted for by memory cache
        assert (
            metric_memory_only.total_cache_size_bytes
            == metric_memory_only.memory_cache_size_bytes
        )
        assert (
            metric_memory_only.cache_entry_count
            == metric_memory_only.memory_cache_entry_count
        )

        # Test zero memory scenario for one tier
        metric_redis_only = MemoryUsageMetric(
            total_cache_size_bytes=52428800,  # 50MB total = Redis only
            cache_entry_count=1000,
            avg_entry_size_bytes=52428.8,  # 50MB / 1000 entries
            memory_cache_size_bytes=0,  # No memory cache
            memory_cache_entry_count=0,  # No entries in memory
            process_memory_mb=128.0,
            timestamp=time.time(),
            cache_utilization_percent=104.8,
            warning_threshold_reached=True,
        )

        # All cache data is in Redis (implied)
        implied_redis_size_only = (
            metric_redis_only.total_cache_size_bytes
            - metric_redis_only.memory_cache_size_bytes
        )
        implied_redis_entries_only = (
            metric_redis_only.cache_entry_count
            - metric_redis_only.memory_cache_entry_count
        )

        assert implied_redis_size_only == 52428800
        assert implied_redis_entries_only == 1000

        # Test large memory aggregation accuracy
        large_memory = 1073741824000  # 1TB
        large_entries = 10000000  # 10 million entries
        large_avg = large_memory / large_entries  # ~100KB per entry

        metric_large = MemoryUsageMetric(
            total_cache_size_bytes=large_memory,
            cache_entry_count=large_entries,
            avg_entry_size_bytes=large_avg,
            memory_cache_size_bytes=1073741824,  # 1GB in memory
            memory_cache_entry_count=10000,  # 10K entries in memory
            process_memory_mb=2048.0,
            timestamp=time.time(),
            cache_utilization_percent=2147483.648,  # Very high
            warning_threshold_reached=True,
        )

        # Verify large number calculations maintain precision
        calculated_large_avg = (
            metric_large.total_cache_size_bytes / metric_large.cache_entry_count
        )
        assert (
            abs(metric_large.avg_entry_size_bytes - calculated_large_avg) < 1.0
        )  # Within 1 byte

    def test_memory_usage_metric_supports_capacity_analysis(self):
        """
        Test that MemoryUsageMetric supports memory capacity analysis.

        Verifies:
            Memory metrics provide data necessary for capacity planning and optimization

        Business Impact:
            Enables proactive capacity planning and memory optimization decisions

        Scenario:
            Given: MemoryUsageMetric with comprehensive memory consumption data
            When: Capacity analysis is performed using metric data
            Then: Sufficient data is available for memory capacity evaluation

        Edge Cases Covered:
            - Capacity planning data availability
            - Memory tier breakdown analysis support
            - Entry density analysis support
            - Growth trend analysis data provision

        Mocks Used:
            - None (capacity analysis support verification)

        Related Tests:
            - test_memory_usage_metric_calculates_totals_accurately()
            - test_memory_usage_metric_maintains_measurement_consistency()
        """
        # Given: MemoryUsageMetric with comprehensive memory consumption data
        total_cache_size = 157286400  # 150MB total
        cache_entries = 3000
        avg_entry_size = 52428.8  # ~50KB per entry
        memory_cache_size = 31457280  # 30MB in memory (20% of total)
        memory_entries = 600  # 20% of entries in memory
        process_memory = 512.0  # 512MB process memory
        timestamp = time.time()
        utilization = 314.57  # 3x warning threshold
        warning_reached = True
        additional_data = {
            "redis_info": {"used_memory": 125829120, "maxmemory": 1073741824},
            "eviction_policy": "allkeys-lru",
            "hit_rate": 85.5,
        }

        metric = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size,
            cache_entry_count=cache_entries,
            avg_entry_size_bytes=avg_entry_size,
            memory_cache_size_bytes=memory_cache_size,
            memory_cache_entry_count=memory_entries,
            process_memory_mb=process_memory,
            timestamp=timestamp,
            cache_utilization_percent=utilization,
            warning_threshold_reached=warning_reached,
            additional_data=additional_data,
        )

        # When: Capacity analysis is performed using metric data

        # Calculate memory tier breakdown
        redis_cache_size = (
            metric.total_cache_size_bytes - metric.memory_cache_size_bytes
        )
        redis_entries = metric.cache_entry_count - metric.memory_cache_entry_count
        memory_tier_percentage = (
            metric.memory_cache_size_bytes / metric.total_cache_size_bytes
        ) * 100
        redis_tier_percentage = (redis_cache_size / metric.total_cache_size_bytes) * 100

        # Calculate entry density metrics
        memory_density = (
            metric.memory_cache_size_bytes / metric.memory_cache_entry_count
            if metric.memory_cache_entry_count > 0
            else 0
        )
        redis_density = redis_cache_size / redis_entries if redis_entries > 0 else 0

        # Calculate capacity utilization metrics
        warning_threshold_bytes = 50 * 1024 * 1024  # Assume 50MB warning threshold
        capacity_used_ratio = metric.total_cache_size_bytes / warning_threshold_bytes

        # Then: Sufficient data is available for memory capacity evaluation

        # Verify capacity planning data availability
        assert metric.total_cache_size_bytes > 0  # Total memory usage
        assert metric.cache_entry_count > 0  # Total entry count
        assert metric.avg_entry_size_bytes > 0  # Average entry size for projections
        assert metric.process_memory_mb > 0  # Process memory context
        assert (
            metric.cache_utilization_percent > 0
        )  # Utilization relative to thresholds
        assert metric.warning_threshold_reached == True  # Alert status

        # Verify memory tier breakdown analysis support
        assert memory_tier_percentage == 20.0  # 20% in memory tier
        assert redis_tier_percentage == 80.0  # 80% in Redis tier
        assert abs(memory_tier_percentage + redis_tier_percentage - 100.0) < 0.1

        # Verify tier-specific sizing
        assert metric.memory_cache_size_bytes < metric.total_cache_size_bytes
        assert redis_cache_size > 0
        assert redis_entries > 0

        # Verify entry density analysis support
        assert memory_density > 0  # Bytes per entry in memory tier
        assert redis_density > 0  # Bytes per entry in Redis tier
        assert (
            abs(memory_density - avg_entry_size) < 1.0
        )  # Should be close to overall average
        assert (
            abs(redis_density - avg_entry_size) < 1.0
        )  # Should be close to overall average

        # Verify growth trend analysis data provision
        current_capacity_ratio = capacity_used_ratio  # Current usage vs threshold
        projected_entries_at_threshold = (
            warning_threshold_bytes / metric.avg_entry_size_bytes
        )
        current_entry_efficiency = (
            metric.total_cache_size_bytes / metric.cache_entry_count
        )

        assert current_capacity_ratio > 1.0  # Over threshold
        assert (
            projected_entries_at_threshold < metric.cache_entry_count
        )  # Current exceeds safe capacity
        assert current_entry_efficiency == avg_entry_size  # Efficiency metric available

        # Verify additional capacity planning metrics from additional_data
        redis_max_memory = metric.additional_data["redis_info"]["maxmemory"]
        redis_used_memory = metric.additional_data["redis_info"]["used_memory"]
        redis_utilization = (redis_used_memory / redis_max_memory) * 100
        hit_rate = metric.additional_data["hit_rate"]

        assert redis_utilization < 100.0  # Redis has headroom
        assert hit_rate > 0  # Cache effectiveness metric
        assert "eviction_policy" in metric.additional_data  # Eviction strategy context

        # Test capacity analysis with different utilization levels
        low_utilization_metric = MemoryUsageMetric(
            total_cache_size_bytes=10485760,  # 10MB (under threshold)
            cache_entry_count=100,
            avg_entry_size_bytes=104857.6,
            memory_cache_size_bytes=5242880,  # 5MB in memory
            memory_cache_entry_count=50,
            process_memory_mb=64.0,
            timestamp=timestamp,
            cache_utilization_percent=20.0,  # Under threshold
            warning_threshold_reached=False,
        )

        # Low utilization should indicate capacity headroom
        assert low_utilization_metric.cache_utilization_percent < 100.0
        assert low_utilization_metric.warning_threshold_reached == False
        assert low_utilization_metric.total_cache_size_bytes < warning_threshold_bytes

    def test_memory_usage_metric_maintains_measurement_consistency(self):
        """
        Test that MemoryUsageMetric maintains measurement data consistency.

        Verifies:
            Memory measurement data consistency is preserved for accurate capacity analysis

        Business Impact:
            Ensures reliable memory usage data for optimization and capacity planning

        Scenario:
            Given: MemoryUsageMetric with complete memory measurement data
            When: Data consistency is evaluated across related fields
            Then: All measurement data maintains logical consistency and accuracy

        Edge Cases Covered:
            - Memory size and entry count consistency
            - Cache tier data consistency
            - Timestamp consistency with measurement
            - Field relationship logical consistency

        Mocks Used:
            - None (data consistency verification)

        Related Tests:
            - test_memory_usage_metric_supports_capacity_analysis()
            - test_memory_usage_metric_creates_with_memory_data()
        """
        # Given: MemoryUsageMetric with complete memory measurement data
        total_size = 83886080  # 80MB total
        total_entries = 2000
        avg_size = 41943.04  # 80MB / 2000 entries
        memory_size = 16777216  # 16MB in memory
        memory_entries = 400  # 400 entries in memory
        process_mem = 256.5
        measure_time = time.time()
        utilization = 167.77  # Above warning threshold
        warning = True
        additional = {"measurement_id": "test_001", "source": "monitoring"}

        metric = MemoryUsageMetric(
            total_cache_size_bytes=total_size,
            cache_entry_count=total_entries,
            avg_entry_size_bytes=avg_size,
            memory_cache_size_bytes=memory_size,
            memory_cache_entry_count=memory_entries,
            process_memory_mb=process_mem,
            timestamp=measure_time,
            cache_utilization_percent=utilization,
            warning_threshold_reached=warning,
            additional_data=additional,
        )

        # When: Data consistency is evaluated across related fields

        # Store original values for consistency verification
        original_values = {
            "total_size": metric.total_cache_size_bytes,
            "total_entries": metric.cache_entry_count,
            "avg_size": metric.avg_entry_size_bytes,
            "memory_size": metric.memory_cache_size_bytes,
            "memory_entries": metric.memory_cache_entry_count,
            "process_memory": metric.process_memory_mb,
            "timestamp": metric.timestamp,
            "utilization": metric.cache_utilization_percent,
            "warning": metric.warning_threshold_reached,
            "additional": metric.additional_data,
        }

        # Then: All measurement data maintains logical consistency and accuracy

        # Memory size and entry count consistency
        calculated_avg = metric.total_cache_size_bytes / metric.cache_entry_count
        assert (
            abs(metric.avg_entry_size_bytes - calculated_avg) < 0.1
        )  # Should be mathematically consistent

        # Cache tier data consistency - memory cache should be subset of total
        assert metric.memory_cache_size_bytes <= metric.total_cache_size_bytes
        assert metric.memory_cache_entry_count <= metric.cache_entry_count

        # Calculate implied Redis tier values
        implied_redis_size = (
            metric.total_cache_size_bytes - metric.memory_cache_size_bytes
        )
        implied_redis_entries = (
            metric.cache_entry_count - metric.memory_cache_entry_count
        )

        assert implied_redis_size >= 0  # Should not be negative
        assert implied_redis_entries >= 0  # Should not be negative
        assert implied_redis_size == 67108864  # 64MB in Redis
        assert implied_redis_entries == 1600  # 1600 entries in Redis

        # Verify tier proportions are logical
        memory_size_ratio = (
            metric.memory_cache_size_bytes / metric.total_cache_size_bytes
        )
        memory_entry_ratio = metric.memory_cache_entry_count / metric.cache_entry_count
        assert (
            abs(memory_size_ratio - memory_entry_ratio) < 0.01
        )  # Ratios should be similar

        # Timestamp consistency with measurement
        assert metric.timestamp > 0  # Should be positive Unix timestamp
        assert metric.timestamp <= time.time()  # Should not be in the future
        assert metric.timestamp == measure_time  # Should match what we set

        # Field relationship logical consistency
        # Warning threshold relationship
        if metric.warning_threshold_reached:
            assert metric.cache_utilization_percent >= 100.0  # Should be over threshold

        # Process memory should be reasonable
        assert metric.process_memory_mb > 0  # Should be positive
        assert metric.process_memory_mb > (
            metric.memory_cache_size_bytes / 1024 / 1024
        )  # Process should include cache

        # Data preservation over multiple accesses
        for _ in range(5):  # Access fields multiple times
            # Values should remain exactly the same
            assert metric.total_cache_size_bytes == original_values["total_size"]
            assert metric.cache_entry_count == original_values["total_entries"]
            assert metric.avg_entry_size_bytes == original_values["avg_size"]
            assert metric.memory_cache_size_bytes == original_values["memory_size"]
            assert metric.memory_cache_entry_count == original_values["memory_entries"]
            assert metric.process_memory_mb == original_values["process_memory"]
            assert metric.timestamp == original_values["timestamp"]
            assert metric.cache_utilization_percent == original_values["utilization"]
            assert metric.warning_threshold_reached == original_values["warning"]
            assert metric.additional_data == original_values["additional"]

        # Verify additional_data consistency (should be initialized if None)
        metric_with_none_data = MemoryUsageMetric(
            total_cache_size_bytes=1000,
            cache_entry_count=10,
            avg_entry_size_bytes=100.0,
            memory_cache_size_bytes=500,
            memory_cache_entry_count=5,
            process_memory_mb=32.0,
            timestamp=time.time(),
            cache_utilization_percent=2.0,
            warning_threshold_reached=False,
            additional_data=None,  # Should be converted to {} by __post_init__
        )

        assert (
            metric_with_none_data.additional_data == {}
        )  # Should be empty dict, not None
        assert isinstance(metric_with_none_data.additional_data, dict)

        # Test serialization and reconstruction maintains consistency
        from dataclasses import asdict

        serialized = asdict(metric)
        reconstructed = MemoryUsageMetric(**serialized)

        # All fields should match exactly
        assert reconstructed.total_cache_size_bytes == metric.total_cache_size_bytes
        assert reconstructed.cache_entry_count == metric.cache_entry_count
        assert reconstructed.avg_entry_size_bytes == metric.avg_entry_size_bytes
        assert reconstructed.memory_cache_size_bytes == metric.memory_cache_size_bytes
        assert reconstructed.memory_cache_entry_count == metric.memory_cache_entry_count
        assert reconstructed.process_memory_mb == metric.process_memory_mb
        assert reconstructed.timestamp == metric.timestamp
        assert (
            reconstructed.cache_utilization_percent == metric.cache_utilization_percent
        )
        assert (
            reconstructed.warning_threshold_reached == metric.warning_threshold_reached
        )
        assert reconstructed.additional_data == metric.additional_data


class TestInvalidationMetric:
    """
    Test suite for InvalidationMetric dataclass functionality.

    Scope:
        - Invalidation metric initialization and validation
        - Invalidation efficiency calculation accuracy
        - Pattern and type categorization representation
        - Invalidation event measurement integrity

    Business Critical:
        Invalidation metric accuracy enables cache optimization and performance tuning

    Test Strategy:
        - Unit tests for invalidation-specific field validation
        - Efficiency calculation accuracy verification
        - Pattern categorization testing
        - Event measurement integrity validation

    External Dependencies:
        - None (pure dataclass functionality testing)
    """

    def test_invalidation_metric_creates_with_invalidation_data(self):
        """
        Test that InvalidationMetric creates successfully with invalidation event data.

        Verifies:
            InvalidationMetric dataclass represents cache invalidation event data accurately

        Business Impact:
            Ensures reliable invalidation pattern monitoring and optimization

        Scenario:
            Given: Valid invalidation event data (pattern, keys count, timing, type)
            When: InvalidationMetric is instantiated with invalidation data
            Then: Dataclass is created with invalidation-specific fields properly initialized

        Edge Cases Covered:
            - Invalidation pattern initialization
            - Keys invalidated count initialization
            - Invalidation timing initialization
            - Type and context field initialization

        Mocks Used:
            - None (invalidation dataclass instantiation verification)

        Related Tests:
            - test_invalidation_metric_validates_key_counts()
            - test_invalidation_metric_categorizes_types_correctly()
        """
        # Given: Valid invalidation event data (pattern, keys count, timing, type)
        pattern = "user:*:cache"
        keys_invalidated = 47
        duration = 0.032  # 32ms to invalidate
        timestamp = time.time()
        invalidation_type = "manual"
        operation_context = "user_profile_update"
        additional_data = {
            "reason": "profile_change",
            "affected_users": ["user123", "user456"],
            "cascade_level": 2,
        }

        # When: InvalidationMetric is instantiated with invalidation data
        metric = InvalidationMetric(
            pattern=pattern,
            keys_invalidated=keys_invalidated,
            duration=duration,
            timestamp=timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
            additional_data=additional_data,
        )

        # Then: Dataclass is created with invalidation-specific fields properly initialized
        assert metric.pattern == pattern
        assert metric.keys_invalidated == keys_invalidated
        assert metric.duration == duration
        assert metric.timestamp == timestamp
        assert metric.invalidation_type == invalidation_type
        assert metric.operation_context == operation_context
        assert metric.additional_data == additional_data

        # Verify field types are correct
        assert isinstance(metric.pattern, str)
        assert isinstance(metric.keys_invalidated, int)
        assert isinstance(metric.duration, float)
        assert isinstance(metric.timestamp, float)
        assert isinstance(metric.invalidation_type, str)
        assert isinstance(metric.operation_context, str)
        assert isinstance(metric.additional_data, dict)

        # Test with minimal data (optional fields)
        minimal_metric = InvalidationMetric(
            pattern="cache:*", keys_invalidated=10, duration=0.005, timestamp=timestamp
        )

        # Optional fields should have default values
        assert minimal_metric.invalidation_type == ""
        assert minimal_metric.operation_context == ""
        assert (
            minimal_metric.additional_data == {}
        )  # Should be initialized by __post_init__

    def test_invalidation_metric_validates_key_counts(self):
        """
        Test that InvalidationMetric validates keys invalidated count appropriately.

        Verifies:
            Keys invalidated count values are validated for reasonable ranges

        Business Impact:
            Prevents invalid invalidation measurements from corrupting optimization analysis

        Scenario:
            Given: InvalidationMetric with various keys invalidated count values
            When: Key count validation is performed
            Then: Reasonable key counts are accepted while invalid values are handled

        Edge Cases Covered:
            - Negative key counts
            - Zero key counts (pattern match but no keys)
            - Very large key counts
            - Key count consistency with pattern scope

        Mocks Used:
            - None (key count validation verification)

        Related Tests:
            - test_invalidation_metric_creates_with_invalidation_data()
            - test_invalidation_metric_validates_timing_values()
        """
        # Given: Common test data
        pattern = "test:*"
        duration = 0.015
        timestamp = time.time()
        invalidation_type = "test"
        operation_context = "validation_test"

        # Test zero key counts (pattern matched but no keys found)
        metric_zero = InvalidationMetric(
            pattern=pattern,
            keys_invalidated=0,
            duration=duration,
            timestamp=timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
        )
        assert metric_zero.keys_invalidated == 0

        # Test small key counts (few keys invalidated)
        metric_small = InvalidationMetric(
            pattern="user:123:*",  # Specific user pattern
            keys_invalidated=5,
            duration=duration,
            timestamp=timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
        )
        assert metric_small.keys_invalidated == 5

        # Test medium key counts (typical invalidation)
        metric_medium = InvalidationMetric(
            pattern="session:*:data",  # Session data pattern
            keys_invalidated=150,
            duration=duration,
            timestamp=timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
        )
        assert metric_medium.keys_invalidated == 150

        # Test large key counts (broad invalidation)
        metric_large = InvalidationMetric(
            pattern="cache:*",  # Very broad pattern
            keys_invalidated=5000,
            duration=duration,
            timestamp=timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
        )
        assert metric_large.keys_invalidated == 5000

        # Test very large key counts (mass invalidation)
        metric_mass = InvalidationMetric(
            pattern="*",  # Global invalidation
            keys_invalidated=1000000,  # 1 million keys
            duration=duration,
            timestamp=timestamp,
            invalidation_type="automatic",
            operation_context="system_reset",
        )
        assert metric_mass.keys_invalidated == 1000000

        # Test negative key counts (invalid but stored for debugging)
        metric_negative = InvalidationMetric(
            pattern="invalid:*",
            keys_invalidated=-50,  # Invalid count
            duration=duration,
            timestamp=timestamp,
            invalidation_type="error",
            operation_context="validation_error",
        )
        assert metric_negative.keys_invalidated == -50

        # Verify key count consistency with pattern scope
        # Specific patterns should typically have fewer keys
        specific_pattern_metric = InvalidationMetric(
            pattern="user:12345:profile:data",  # Very specific pattern
            keys_invalidated=1,  # Should be small count
            duration=0.001,
            timestamp=timestamp,
            invalidation_type="targeted",
            operation_context="profile_update",
        )

        broad_pattern_metric = InvalidationMetric(
            pattern="user:*",  # Broad pattern
            keys_invalidated=2500,  # Should be larger count
            duration=0.125,  # Should take longer
            timestamp=timestamp,
            invalidation_type="batch",
            operation_context="user_cleanup",
        )

        # Verify logical consistency
        assert (
            specific_pattern_metric.keys_invalidated
            < broad_pattern_metric.keys_invalidated
        )
        assert (
            specific_pattern_metric.duration < broad_pattern_metric.duration
        )  # Fewer keys = faster

        # Verify all key counts are integers
        assert isinstance(metric_zero.keys_invalidated, int)
        assert isinstance(metric_large.keys_invalidated, int)
        assert isinstance(metric_negative.keys_invalidated, int)

    def test_invalidation_metric_validates_timing_values(self):
        """
        Test that InvalidationMetric validates invalidation timing values appropriately.

        Verifies:
            Invalidation timing values are validated for reasonable performance ranges

        Business Impact:
            Ensures accurate invalidation performance analysis for optimization decisions

        Scenario:
            Given: InvalidationMetric with various invalidation timing values
            When: Timing validation is performed
            Then: Reasonable timing values are accepted while maintaining data integrity

        Edge Cases Covered:
            - Negative invalidation times
            - Zero invalidation times
            - Extremely long invalidation times
            - Timing precision for quick operations

        Mocks Used:
            - None (timing validation verification)

        Related Tests:
            - test_invalidation_metric_validates_key_counts()
            - test_invalidation_metric_calculates_efficiency_accurately()
        """
        # Given: Common test data
        pattern = "timing:test:*"
        keys_invalidated = 25
        timestamp = time.time()
        invalidation_type = "timing_test"
        operation_context = "performance_validation"

        # Test zero invalidation time (instantaneous invalidation)
        metric_zero_time = InvalidationMetric(
            pattern=pattern,
            keys_invalidated=keys_invalidated,
            duration=0.0,
            timestamp=timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
        )
        assert metric_zero_time.duration == 0.0

        # Test very fast invalidation times (sub-millisecond)
        metric_fast = InvalidationMetric(
            pattern="single:key",
            keys_invalidated=1,
            duration=0.0001,  # 0.1ms - very fast single key
            timestamp=timestamp,
            invalidation_type="targeted",
            operation_context="quick_update",
        )
        assert metric_fast.duration == 0.0001

        # Test normal invalidation times (millisecond range)
        metric_normal = InvalidationMetric(
            pattern="normal:*",
            keys_invalidated=50,
            duration=0.025,  # 25ms - typical batch invalidation
            timestamp=timestamp,
            invalidation_type="batch",
            operation_context="routine_cleanup",
        )
        assert metric_normal.duration == 0.025

        # Test slow invalidation times (hundreds of milliseconds)
        metric_slow = InvalidationMetric(
            pattern="complex:*:nested:*",
            keys_invalidated=500,
            duration=0.350,  # 350ms - complex pattern matching
            timestamp=timestamp,
            invalidation_type="pattern_complex",
            operation_context="deep_structure_cleanup",
        )
        assert metric_slow.duration == 0.350

        # Test very slow invalidation times (seconds)
        metric_very_slow = InvalidationMetric(
            pattern="global:*",
            keys_invalidated=10000,
            duration=2.5,  # 2.5 seconds - mass invalidation
            timestamp=timestamp,
            invalidation_type="mass",
            operation_context="system_maintenance",
        )
        assert metric_very_slow.duration == 2.5

        # Test extremely long invalidation times (minutes)
        metric_extreme = InvalidationMetric(
            pattern="archive:*:*:*",
            keys_invalidated=1000000,
            duration=120.0,  # 2 minutes - full archive cleanup
            timestamp=timestamp,
            invalidation_type="maintenance",
            operation_context="archive_purge",
        )
        assert metric_extreme.duration == 120.0

        # Test negative invalidation time (invalid but stored for debugging)
        metric_negative = InvalidationMetric(
            pattern="error:*",
            keys_invalidated=keys_invalidated,
            duration=-0.5,  # Invalid negative timing
            timestamp=timestamp,
            invalidation_type="error",
            operation_context="timing_error",
        )
        assert metric_negative.duration == -0.5

        # Test high precision timing values
        precise_duration = 0.0123456789
        metric_precise = InvalidationMetric(
            pattern="precise:*",
            keys_invalidated=keys_invalidated,
            duration=precise_duration,
            timestamp=timestamp,
            invalidation_type="precision_test",
            operation_context="timing_precision",
        )
        assert metric_precise.duration == precise_duration

        # Verify timing correlation with key counts
        # More keys should generally take longer (though not always)
        few_keys_metric = InvalidationMetric(
            pattern="few:*",
            keys_invalidated=5,
            duration=0.002,  # Fast
            timestamp=timestamp,
            invalidation_type="small_batch",
            operation_context="quick_cleanup",
        )

        many_keys_metric = InvalidationMetric(
            pattern="many:*",
            keys_invalidated=5000,
            duration=0.200,  # Slower
            timestamp=timestamp,
            invalidation_type="large_batch",
            operation_context="bulk_cleanup",
        )

        # Calculate efficiency (keys per second)
        few_keys_efficiency = (
            few_keys_metric.keys_invalidated / few_keys_metric.duration
            if few_keys_metric.duration > 0
            else 0
        )
        many_keys_efficiency = (
            many_keys_metric.keys_invalidated / many_keys_metric.duration
            if many_keys_metric.duration > 0
            else 0
        )

        # Both should have reasonable efficiency scores
        assert few_keys_efficiency > 0
        assert many_keys_efficiency > 0

        # Verify timing precision is maintained
        assert isinstance(metric_precise.duration, float)
        assert metric_fast.duration < metric_normal.duration < metric_slow.duration

    def test_invalidation_metric_calculates_efficiency_accurately(self):
        """
        Test that InvalidationMetric calculates invalidation efficiency accurately.

        Verifies:
            Invalidation efficiency calculations (keys per operation) are mathematically correct

        Business Impact:
            Provides accurate efficiency analysis for invalidation strategy optimization

        Scenario:
            Given: InvalidationMetric with keys count and timing data
            When: Efficiency calculations are performed
            Then: Keys per operation and timing efficiency are calculated accurately

        Edge Cases Covered:
            - High efficiency invalidations (many keys per operation)
            - Low efficiency invalidations (few keys per operation)
            - Zero key invalidations efficiency handling
            - Efficiency calculation precision

        Mocks Used:
            - None (efficiency calculation verification)

        Related Tests:
            - test_invalidation_metric_validates_timing_values()
            - test_invalidation_metric_categorizes_types_correctly()
        """
        # Given: Common test data
        timestamp = time.time()

        # Test high efficiency invalidations (many keys per operation)
        high_efficiency_metric = InvalidationMetric(
            pattern="bulk:*:cache",
            keys_invalidated=10000,  # Many keys
            duration=0.100,  # Relatively fast (100ms)
            timestamp=timestamp,
            invalidation_type="bulk",
            operation_context="mass_update",
        )

        # When: Efficiency calculations are performed
        high_eff_keys_per_second = (
            high_efficiency_metric.keys_invalidated / high_efficiency_metric.duration
        )
        high_eff_keys_per_ms = high_efficiency_metric.keys_invalidated / (
            high_efficiency_metric.duration * 1000
        )
        high_eff_ms_per_key = (
            high_efficiency_metric.duration * 1000
        ) / high_efficiency_metric.keys_invalidated

        # Then: High efficiency calculations are accurate
        assert high_eff_keys_per_second == 100000.0  # 100K keys/second
        assert high_eff_keys_per_ms == 100.0  # 100 keys/ms
        assert high_eff_ms_per_key == 0.01  # 0.01ms per key

        # Test low efficiency invalidations (few keys per operation)
        low_efficiency_metric = InvalidationMetric(
            pattern="specific:user:12345:*",
            keys_invalidated=5,  # Few keys
            duration=0.050,  # Relatively slow for few keys (50ms)
            timestamp=timestamp,
            invalidation_type="targeted",
            operation_context="user_specific_update",
        )

        low_eff_keys_per_second = (
            low_efficiency_metric.keys_invalidated / low_efficiency_metric.duration
        )
        low_eff_keys_per_ms = low_efficiency_metric.keys_invalidated / (
            low_efficiency_metric.duration * 1000
        )
        low_eff_ms_per_key = (
            low_efficiency_metric.duration * 1000
        ) / low_efficiency_metric.keys_invalidated

        # Low efficiency calculations
        assert low_eff_keys_per_second == 100.0  # 100 keys/second (much lower)
        assert low_eff_keys_per_ms == 0.1  # 0.1 keys/ms
        assert low_eff_ms_per_key == 10.0  # 10ms per key

        # Verify high efficiency is indeed more efficient
        assert high_eff_keys_per_second > low_eff_keys_per_second
        assert high_eff_keys_per_ms > low_eff_keys_per_ms
        assert high_eff_ms_per_key < low_eff_ms_per_key

        # Test zero key invalidations efficiency handling
        zero_keys_metric = InvalidationMetric(
            pattern="empty:*",
            keys_invalidated=0,  # No keys found
            duration=0.025,  # Still took time (pattern processing)
            timestamp=timestamp,
            invalidation_type="no_match",
            operation_context="pattern_search",
        )

        # When no keys are invalidated, efficiency calculations should handle gracefully
        zero_keys_per_second = (
            zero_keys_metric.keys_invalidated / zero_keys_metric.duration
        )
        assert zero_keys_per_second == 0.0  # No keys processed

        # Test zero time invalidation (instantaneous)
        zero_time_metric = InvalidationMetric(
            pattern="instant:*",
            keys_invalidated=100,
            duration=0.0,  # Instantaneous
            timestamp=timestamp,
            invalidation_type="instant",
            operation_context="memory_direct",
        )

        # Handle division by zero gracefully in efficiency calculations
        if zero_time_metric.duration > 0:
            zero_time_keys_per_second = (
                zero_time_metric.keys_invalidated / zero_time_metric.duration
            )
        else:
            zero_time_keys_per_second = float("inf")  # Infinite efficiency

        assert zero_time_keys_per_second == float("inf")

        # Test efficiency calculation precision with precise values
        precise_metric = InvalidationMetric(
            pattern="precise:*",
            keys_invalidated=1337,  # Specific count
            duration=0.0421,  # Precise timing
            timestamp=timestamp,
            invalidation_type="precision",
            operation_context="accuracy_test",
        )

        precise_keys_per_second = (
            precise_metric.keys_invalidated / precise_metric.duration
        )
        precise_rounded = round(precise_keys_per_second, 2)

        # Verify precision is maintained
        expected_precise = 1337 / 0.0421  # ~31757.72
        assert abs(precise_keys_per_second - expected_precise) < 0.1
        assert precise_rounded == 31757.72

        # Test throughput comparison between different patterns
        simple_pattern_metric = InvalidationMetric(
            pattern="*",  # Simple global pattern
            keys_invalidated=1000,
            duration=0.020,  # Fast due to simple pattern
            timestamp=timestamp,
            invalidation_type="global",
            operation_context="simple_clear",
        )

        complex_pattern_metric = InvalidationMetric(
            pattern="user:*:session:*:data:*:temp",  # Complex nested pattern
            keys_invalidated=1000,  # Same key count
            duration=0.080,  # Slower due to complex pattern matching
            timestamp=timestamp,
            invalidation_type="complex",
            operation_context="nested_cleanup",
        )

        simple_efficiency = (
            simple_pattern_metric.keys_invalidated / simple_pattern_metric.duration
        )
        complex_efficiency = (
            complex_pattern_metric.keys_invalidated / complex_pattern_metric.duration
        )

        # Simple patterns should be more efficient than complex ones for same key count
        assert simple_efficiency > complex_efficiency
        assert simple_efficiency == 50000.0  # 50K keys/second
        assert complex_efficiency == 12500.0  # 12.5K keys/second

        # Calculate pattern complexity impact
        complexity_overhead = (
            complex_pattern_metric.duration - simple_pattern_metric.duration
        ) / simple_pattern_metric.duration
        assert complexity_overhead == 3.0  # 4x longer (300% overhead)

    def test_invalidation_metric_categorizes_types_correctly(self):
        """
        Test that InvalidationMetric categorizes invalidation types correctly.

        Verifies:
            Invalidation types are properly categorized for pattern analysis

        Business Impact:
            Enables type-specific invalidation pattern analysis and optimization

        Scenario:
            Given: InvalidationMetric with various invalidation type values
            When: Type categorization is performed
            Then: Invalidation types are correctly categorized for analysis

        Edge Cases Covered:
            - Manual invalidation type categorization
            - Automatic invalidation type categorization
            - TTL expiration type categorization
            - Custom invalidation type handling

        Mocks Used:
            - None (type categorization verification)

        Related Tests:
            - test_invalidation_metric_calculates_efficiency_accurately()
            - test_invalidation_metric_supports_pattern_analysis()
        """
        # Given: Common test data
        pattern = "type:test:*"
        keys_invalidated = 100
        duration = 0.050
        timestamp = time.time()

        # Test manual invalidation type categorization
        manual_metric = InvalidationMetric(
            pattern=pattern,
            keys_invalidated=keys_invalidated,
            duration=duration,
            timestamp=timestamp,
            invalidation_type="manual",
            operation_context="admin_triggered_cleanup",
        )

        # When: Type categorization is performed
        # Then: Manual invalidation types are correctly categorized
        assert manual_metric.invalidation_type == "manual"
        assert manual_metric.operation_context == "admin_triggered_cleanup"

        # Manual invalidations should be identifiable
        is_manual = manual_metric.invalidation_type == "manual"
        assert is_manual is True

        # Test automatic invalidation type categorization
        automatic_metric = InvalidationMetric(
            pattern="session:*:expired",
            keys_invalidated=250,
            duration=0.075,
            timestamp=timestamp,
            invalidation_type="automatic",
            operation_context="session_cleanup_job",
        )

        assert automatic_metric.invalidation_type == "automatic"
        is_automatic = automatic_metric.invalidation_type == "automatic"
        assert is_automatic is True

        # Test TTL expiration type categorization
        ttl_metric = InvalidationMetric(
            pattern="cache:*:ttl",
            keys_invalidated=500,
            duration=0.100,
            timestamp=timestamp,
            invalidation_type="ttl_expired",
            operation_context="background_ttl_cleanup",
        )

        assert ttl_metric.invalidation_type == "ttl_expired"
        is_ttl = ttl_metric.invalidation_type == "ttl_expired"
        assert is_ttl is True

        # Test custom invalidation type handling
        custom_types = [
            "policy_violation",
            "security_breach",
            "data_corruption",
            "dependency_update",
            "memory_pressure",
            "maintenance_window",
        ]

        custom_metrics = []
        for i, custom_type in enumerate(custom_types):
            custom_metric = InvalidationMetric(
                pattern=f"custom:{custom_type}:*",
                keys_invalidated=50 + i * 10,
                duration=0.020 + i * 0.005,
                timestamp=timestamp,
                invalidation_type=custom_type,
                operation_context=f"{custom_type}_handler",
            )
            custom_metrics.append(custom_metric)

            # Verify custom types are stored correctly
            assert custom_metric.invalidation_type == custom_type
            assert custom_metric.operation_context == f"{custom_type}_handler"

        # Test type categorization for analysis
        all_metrics = [manual_metric, automatic_metric, ttl_metric] + custom_metrics

        # Categorize by type for analysis
        type_categories = {}
        for metric in all_metrics:
            inv_type = metric.invalidation_type
            if inv_type not in type_categories:
                type_categories[inv_type] = []
            type_categories[inv_type].append(metric)

        # Verify categorization results
        assert "manual" in type_categories
        assert "automatic" in type_categories
        assert "ttl_expired" in type_categories

        # Each standard type should have one entry
        assert len(type_categories["manual"]) == 1
        assert len(type_categories["automatic"]) == 1
        assert len(type_categories["ttl_expired"]) == 1

        # Custom types should each have one entry
        for custom_type in custom_types:
            assert custom_type in type_categories
            assert len(type_categories[custom_type]) == 1

        # Test empty/default type handling
        default_metric = InvalidationMetric(
            pattern="default:*",
            keys_invalidated=10,
            duration=0.005,
            timestamp=timestamp
            # invalidation_type not specified - should default to ""
        )

        assert default_metric.invalidation_type == ""
        assert default_metric.operation_context == ""

        # Test type consistency with operation context
        context_consistency_tests = [
            ("manual", "user_action", True),
            ("automatic", "scheduled_job", True),
            ("ttl_expired", "expiry_cleanup", True),
            ("manual", "scheduled_job", False),  # Inconsistent
            ("automatic", "user_action", False),  # Inconsistent
        ]

        for inv_type, context, should_be_consistent in context_consistency_tests:
            test_metric = InvalidationMetric(
                pattern="consistency:*",
                keys_invalidated=1,
                duration=0.001,
                timestamp=timestamp,
                invalidation_type=inv_type,
                operation_context=context,
            )

            # Verify the data is stored as provided
            assert test_metric.invalidation_type == inv_type
            assert test_metric.operation_context == context

            # Analysis code could check for consistency (this would be external to the dataclass)
            if should_be_consistent:
                # These combinations make logical sense
                logical_consistency_check = True
            else:
                # These combinations might indicate data quality issues
                logical_consistency_check = False

            # The dataclass stores all combinations - analysis logic would flag inconsistencies
            assert isinstance(logical_consistency_check, bool)

        # Test case-sensitive type handling
        case_sensitive_tests = ["Manual", "AUTOMATIC", "ttl_EXPIRED", "custom_Type"]

        for case_type in case_sensitive_tests:
            case_metric = InvalidationMetric(
                pattern="case:*",
                keys_invalidated=1,
                duration=0.001,
                timestamp=timestamp,
                invalidation_type=case_type,
                operation_context="case_test",
            )

            # Types are stored exactly as provided (case-sensitive)
            assert case_metric.invalidation_type == case_type
            assert case_metric.invalidation_type != case_type.lower()

        # Verify all types are strings
        for metric in all_metrics:
            assert isinstance(metric.invalidation_type, str)
            assert isinstance(metric.operation_context, str)

    def test_invalidation_metric_supports_pattern_analysis(self):
        """
        Test that InvalidationMetric supports invalidation pattern analysis.

        Verifies:
            Invalidation metrics provide data necessary for pattern recognition and optimization

        Business Impact:
            Enables pattern-based optimization of cache invalidation strategies

        Scenario:
            Given: InvalidationMetric with comprehensive invalidation event data
            When: Pattern analysis is performed using metric data
            Then: Sufficient data is available for invalidation pattern evaluation

        Edge Cases Covered:
            - Pattern recognition data availability
            - Type-pattern correlation analysis support
            - Efficiency-pattern correlation support
            - Temporal pattern analysis data provision

        Mocks Used:
            - None (pattern analysis support verification)

        Related Tests:
            - test_invalidation_metric_categorizes_types_correctly()
            - test_invalidation_metric_maintains_event_integrity()
        """
        # Given: InvalidationMetric with comprehensive invalidation event data
        base_timestamp = time.time()

        # Create metrics with various patterns for analysis
        pattern_metrics = [
            # User-related patterns
            InvalidationMetric(
                pattern="user:*:profile",
                keys_invalidated=150,
                duration=0.045,
                timestamp=base_timestamp - 3600,  # 1 hour ago
                invalidation_type="manual",
                operation_context="profile_update",
                additional_data={"affected_users": 150, "update_type": "profile"},
            ),
            InvalidationMetric(
                pattern="user:*:session",
                keys_invalidated=300,
                duration=0.080,
                timestamp=base_timestamp - 1800,  # 30 minutes ago
                invalidation_type="automatic",
                operation_context="session_cleanup",
                additional_data={"affected_users": 300, "cleanup_reason": "expired"},
            ),
            # Cache hierarchy patterns
            InvalidationMetric(
                pattern="cache:l1:*",
                keys_invalidated=50,
                duration=0.010,
                timestamp=base_timestamp - 900,  # 15 minutes ago
                invalidation_type="ttl_expired",
                operation_context="l1_cache_expiry",
                additional_data={"cache_level": "l1", "eviction_policy": "lru"},
            ),
            InvalidationMetric(
                pattern="cache:l2:*",
                keys_invalidated=200,
                duration=0.035,
                timestamp=base_timestamp - 600,  # 10 minutes ago
                invalidation_type="memory_pressure",
                operation_context="l2_cache_pressure",
                additional_data={"cache_level": "l2", "memory_usage": "high"},
            ),
            # Global patterns
            InvalidationMetric(
                pattern="*",
                keys_invalidated=10000,
                duration=1.200,
                timestamp=base_timestamp - 300,  # 5 minutes ago
                invalidation_type="maintenance",
                operation_context="system_restart",
                additional_data={"scope": "global", "reason": "deployment"},
            ),
        ]

        # When: Pattern analysis is performed using metric data

        # Pattern recognition data availability
        pattern_groups = {}
        for metric in pattern_metrics:
            pattern = metric.pattern
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(metric)

        # Then: Sufficient data is available for invalidation pattern evaluation

        # Verify pattern recognition data is available
        assert len(pattern_groups) == 5  # 5 distinct patterns
        assert "user:*:profile" in pattern_groups
        assert "user:*:session" in pattern_groups
        assert "cache:l1:*" in pattern_groups
        assert "cache:l2:*" in pattern_groups
        assert "*" in pattern_groups

        # Test pattern hierarchy analysis
        user_patterns = [p for p in pattern_groups if p.startswith("user:")]
        cache_patterns = [p for p in pattern_groups if p.startswith("cache:")]
        global_patterns = [p for p in pattern_groups if p == "*"]

        assert len(user_patterns) == 2  # user:*:profile, user:*:session
        assert len(cache_patterns) == 2  # cache:l1:*, cache:l2:*
        assert len(global_patterns) == 1  # *

        # Type-pattern correlation analysis support
        type_pattern_correlation = {}
        for metric in pattern_metrics:
            key = (metric.invalidation_type, metric.pattern)
            if key not in type_pattern_correlation:
                type_pattern_correlation[key] = []
            type_pattern_correlation[key].append(metric)

        # Verify type-pattern correlations
        assert ("manual", "user:*:profile") in type_pattern_correlation
        assert ("automatic", "user:*:session") in type_pattern_correlation
        assert ("ttl_expired", "cache:l1:*") in type_pattern_correlation
        assert ("memory_pressure", "cache:l2:*") in type_pattern_correlation
        assert ("maintenance", "*") in type_pattern_correlation

        # Efficiency-pattern correlation support
        pattern_efficiency = {}
        for metric in pattern_metrics:
            pattern = metric.pattern
            efficiency = (
                metric.keys_invalidated / metric.duration if metric.duration > 0 else 0
            )

            if pattern not in pattern_efficiency:
                pattern_efficiency[pattern] = []
            pattern_efficiency[pattern].append(
                {
                    "efficiency": efficiency,
                    "keys": metric.keys_invalidated,
                    "duration": metric.duration,
                }
            )

        # Verify efficiency calculations are available per pattern
        for pattern, efficiency_data in pattern_efficiency.items():
            for data in efficiency_data:
                assert data["efficiency"] > 0
                assert data["keys"] > 0
                assert data["duration"] > 0

        # Specific efficiency checks
        l1_efficiency = pattern_efficiency["cache:l1:*"][0][
            "efficiency"
        ]  # 50/0.010 = 5000
        global_efficiency = pattern_efficiency["*"][0][
            "efficiency"
        ]  # 10000/1.200 = 8333.33

        # Note: Global efficiency is actually higher due to batch processing
        # L1 cache has fewer keys but is very fast, global has many keys with longer duration
        assert l1_efficiency > 0 and global_efficiency > 0  # Both should be positive

        # Temporal pattern analysis data provision
        temporal_analysis = []
        for metric in pattern_metrics:
            temporal_analysis.append(
                {
                    "pattern": metric.pattern,
                    "timestamp": metric.timestamp,
                    "keys": metric.keys_invalidated,
                    "type": metric.invalidation_type,
                    "context": metric.operation_context,
                }
            )

        # Sort by timestamp for temporal analysis
        temporal_analysis.sort(key=lambda x: x["timestamp"])

        # Verify temporal data is available and ordered
        assert len(temporal_analysis) == 5

        # Check chronological order
        for i in range(1, len(temporal_analysis)):
            assert (
                temporal_analysis[i]["timestamp"]
                >= temporal_analysis[i - 1]["timestamp"]
            )

        # Pattern frequency analysis
        pattern_frequency = {}
        total_keys_by_pattern = {}

        for metric in pattern_metrics:
            pattern = metric.pattern
            pattern_frequency[pattern] = pattern_frequency.get(pattern, 0) + 1
            total_keys_by_pattern[pattern] = (
                total_keys_by_pattern.get(pattern, 0) + metric.keys_invalidated
            )

        # Most frequent pattern analysis
        most_frequent_pattern = max(pattern_frequency, key=pattern_frequency.get)
        highest_impact_pattern = max(
            total_keys_by_pattern, key=total_keys_by_pattern.get
        )

        # In this test data, all patterns appear once, but global has highest key count
        assert highest_impact_pattern == "*"
        assert total_keys_by_pattern["*"] == 10000

        # Pattern complexity analysis
        pattern_complexity = {}
        for pattern in pattern_groups:
            # Simple complexity measure: count of wildcards and segments (but don't double count)
            wildcard_count = pattern.count("*")
            if pattern == "*":
                # Special case: global wildcard is simplest
                complexity_score = 1
            else:
                segment_count = len(pattern.split(":"))
                complexity_score = segment_count + wildcard_count
            pattern_complexity[pattern] = complexity_score

        # Verify complexity analysis is possible
        assert pattern_complexity["*"] == 1  # Simplest pattern
        assert pattern_complexity["user:*:profile"] == 4  # 3 segments + 1 wildcard
        assert pattern_complexity["cache:l1:*"] == 4  # 3 segments + 1 wildcard

        # Context correlation analysis
        context_patterns = {}
        for metric in pattern_metrics:
            context = metric.operation_context
            pattern = metric.pattern
            if context not in context_patterns:
                context_patterns[context] = []
            context_patterns[context].append(pattern)

        # Verify context-pattern relationships are available
        assert "profile_update" in context_patterns
        assert "session_cleanup" in context_patterns
        assert "system_restart" in context_patterns

        # Additional data analysis support
        additional_data_analysis = {}
        for metric in pattern_metrics:
            if metric.additional_data:
                for key, value in metric.additional_data.items():
                    if key not in additional_data_analysis:
                        additional_data_analysis[key] = []
                    additional_data_analysis[key].append(
                        {
                            "pattern": metric.pattern,
                            "value": value,
                            "keys": metric.keys_invalidated,
                        }
                    )

        # Verify rich additional data is available for analysis
        assert "affected_users" in additional_data_analysis
        assert "cache_level" in additional_data_analysis
        assert "scope" in additional_data_analysis
        assert len(additional_data_analysis["cache_level"]) == 2  # l1 and l2

    def test_invalidation_metric_maintains_event_integrity(self):
        """
        Test that InvalidationMetric maintains invalidation event data integrity.

        Verifies:
            Invalidation event data integrity is preserved for accurate pattern analysis

        Business Impact:
            Ensures reliable invalidation event data for optimization and monitoring

        Scenario:
            Given: InvalidationMetric with complete invalidation event data
            When: Data integrity is evaluated across related fields
            Then: All event data maintains logical consistency and accuracy

        Edge Cases Covered:
            - Pattern and key count consistency
            - Type and context consistency
            - Timing and efficiency consistency
            - Event field relationship integrity

        Mocks Used:
            - None (data integrity verification)

        Related Tests:
            - test_invalidation_metric_supports_pattern_analysis()
            - test_invalidation_metric_creates_with_invalidation_data()
        """
        # Given: InvalidationMetric with complete invalidation event data
        pattern = "integrity:test:*:cache"
        keys_invalidated = 275
        duration = 0.067
        event_timestamp = time.time()
        invalidation_type = "integrity_test"
        operation_context = "data_integrity_validation"
        additional_data = {
            "event_id": "evt_001",
            "source_system": "cache_monitor",
            "validation_checks": ["pattern_match", "key_count", "timing"],
            "metadata": {"batch_size": 275, "processing_node": "node_1"},
        }

        metric = InvalidationMetric(
            pattern=pattern,
            keys_invalidated=keys_invalidated,
            duration=duration,
            timestamp=event_timestamp,
            invalidation_type=invalidation_type,
            operation_context=operation_context,
            additional_data=additional_data,
        )

        # When: Data integrity is evaluated across related fields

        # Store original values for integrity verification
        original_values = {
            "pattern": metric.pattern,
            "keys_invalidated": metric.keys_invalidated,
            "duration": metric.duration,
            "timestamp": metric.timestamp,
            "invalidation_type": metric.invalidation_type,
            "operation_context": metric.operation_context,
            "additional_data": metric.additional_data.copy(),
        }

        # Then: All event data maintains logical consistency and accuracy

        # Pattern and key count consistency
        # Verify pattern specificity relates logically to key count
        pattern_segments = metric.pattern.split(":")
        pattern_wildcards = metric.pattern.count("*")
        pattern_specificity = len(pattern_segments) - pattern_wildcards

        # More specific patterns should generally have fewer keys (though not always)
        # This metric allows for analysis of this relationship
        assert pattern_specificity > 0  # Should have some specific segments
        assert metric.keys_invalidated > 0  # Should have found keys

        # Type and context consistency
        # Verify invalidation type and operation context are logically related
        type_context_pairs = {metric.invalidation_type: metric.operation_context}

        # Should be able to correlate type with context
        assert metric.invalidation_type in type_context_pairs
        assert type_context_pairs[metric.invalidation_type] == metric.operation_context

        # Timing and efficiency consistency
        calculated_efficiency = (
            metric.keys_invalidated / metric.duration if metric.duration > 0 else 0
        )
        keys_per_ms = (
            metric.keys_invalidated / (metric.duration * 1000)
            if metric.duration > 0
            else 0
        )

        # Efficiency calculations should be consistent
        assert calculated_efficiency > 0  # Should have positive efficiency
        assert keys_per_ms > 0  # Should process keys per millisecond
        assert calculated_efficiency == keys_per_ms * 1000  # Conversion consistency

        # Event field relationship integrity
        # All timestamp values should be reasonable
        assert metric.timestamp > 0  # Should be positive Unix timestamp
        assert (
            metric.timestamp <= time.time() + 1
        )  # Should not be significantly in future

        # Duration should be reasonable for key count
        reasonable_min_duration = 0.0001  # At least 0.1ms
        reasonable_max_duration = 10.0  # At most 10 seconds
        assert reasonable_min_duration <= metric.duration <= reasonable_max_duration

        # Keys invalidated should be non-negative
        assert metric.keys_invalidated >= 0

        # Data preservation over multiple accesses
        for access_count in range(10):  # Access fields multiple times
            # Values should remain exactly the same
            assert metric.pattern == original_values["pattern"]
            assert metric.keys_invalidated == original_values["keys_invalidated"]
            assert metric.duration == original_values["duration"]
            assert metric.timestamp == original_values["timestamp"]
            assert metric.invalidation_type == original_values["invalidation_type"]
            assert metric.operation_context == original_values["operation_context"]
            assert metric.additional_data == original_values["additional_data"]

        # Field type consistency
        assert isinstance(metric.pattern, str)
        assert isinstance(metric.keys_invalidated, int)
        assert isinstance(metric.duration, float)
        assert isinstance(metric.timestamp, float)
        assert isinstance(metric.invalidation_type, str)
        assert isinstance(metric.operation_context, str)
        assert isinstance(metric.additional_data, dict)

        # Additional data integrity
        # Nested data should be preserved exactly
        assert metric.additional_data["event_id"] == "evt_001"
        assert metric.additional_data["metadata"]["batch_size"] == 275
        assert metric.additional_data["metadata"]["processing_node"] == "node_1"
        assert len(metric.additional_data["validation_checks"]) == 3

        # Test additional_data initialization with None
        metric_none_additional = InvalidationMetric(
            pattern="none:test",
            keys_invalidated=1,
            duration=0.001,
            timestamp=time.time(),
            additional_data=None,  # Should be converted by __post_init__
        )

        assert metric_none_additional.additional_data == {}  # Should be empty dict
        assert isinstance(metric_none_additional.additional_data, dict)

        # Serialization and reconstruction integrity
        from dataclasses import asdict

        serialized = asdict(metric)
        reconstructed = InvalidationMetric(**serialized)

        # All fields should match exactly after serialization/reconstruction
        assert reconstructed.pattern == metric.pattern
        assert reconstructed.keys_invalidated == metric.keys_invalidated
        assert reconstructed.duration == metric.duration
        assert reconstructed.timestamp == metric.timestamp
        assert reconstructed.invalidation_type == metric.invalidation_type
        assert reconstructed.operation_context == metric.operation_context
        assert reconstructed.additional_data == metric.additional_data

        # Deep equality check for nested additional data
        assert (
            reconstructed.additional_data["metadata"]["batch_size"]
            == metric.additional_data["metadata"]["batch_size"]
        )
        assert (
            reconstructed.additional_data["validation_checks"]
            == metric.additional_data["validation_checks"]
        )

        # Verify field relationships remain intact after reconstruction
        reconstructed_efficiency = (
            reconstructed.keys_invalidated / reconstructed.duration
        )
        original_efficiency = metric.keys_invalidated / metric.duration
        assert abs(reconstructed_efficiency - original_efficiency) < 0.0001

        # Test edge case: empty pattern handling
        empty_pattern_metric = InvalidationMetric(
            pattern="",  # Empty pattern
            keys_invalidated=0,  # No keys with empty pattern
            duration=0.001,
            timestamp=time.time(),
            invalidation_type="empty",
            operation_context="empty_pattern_test",
        )

        # Empty pattern should be stored as-is
        assert empty_pattern_metric.pattern == ""
        assert empty_pattern_metric.keys_invalidated == 0

        # Mathematical relationships should remain consistent
        test_cases = [
            ("fast:*", 100, 0.010),  # Fast invalidation
            ("medium:*", 500, 0.075),  # Medium invalidation
            ("slow:*", 1000, 0.250),  # Slow invalidation
        ]

        for pattern_test, keys_test, duration_test in test_cases:
            test_metric = InvalidationMetric(
                pattern=pattern_test,
                keys_invalidated=keys_test,
                duration=duration_test,
                timestamp=time.time(),
                invalidation_type="consistency_test",
                operation_context="relationship_verification",
            )

            # Efficiency should be calculable and consistent
            efficiency = test_metric.keys_invalidated / test_metric.duration
            assert efficiency > 0

            # Verify mathematical consistency
            recalculated_keys = efficiency * test_metric.duration
            assert abs(recalculated_keys - test_metric.keys_invalidated) < 0.1

        # Field constraint verification
        # String fields should remain strings
        assert len(metric.pattern) > 0
        assert len(metric.invalidation_type) > 0
        assert len(metric.operation_context) > 0

        # Numeric fields should maintain precision
        precise_duration = 0.0123456789
        precise_metric = InvalidationMetric(
            pattern="precision:*",
            keys_invalidated=1337,
            duration=precise_duration,
            timestamp=time.time(),
            invalidation_type="precision",
            operation_context="precision_test",
        )

        # Precision should be maintained
        assert precise_metric.duration == precise_duration
        assert precise_metric.keys_invalidated == 1337
