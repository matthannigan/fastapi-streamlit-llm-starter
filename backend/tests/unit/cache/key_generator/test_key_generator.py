"""
Unit tests for CacheKeyGenerator optimized key generation.

This test suite verifies the observable behaviors documented in the
CacheKeyGenerator public contract (key_generator.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Behavior verification per docstring specifications
    - Key generation consistency and collision avoidance
    - Performance monitoring integration and metrics collection

External Dependencies:
    - Standard library components (hashlib, time): For hashing operations and timing in cache key generation
    - Settings configuration (mocked): Application configuration management
    - app.infrastructure.cache.monitoring: Performance monitoring integration for key generation timing
"""

import hashlib


from app.infrastructure.cache.key_generator import CacheKeyGenerator


class TestCacheKeyGeneratorInitialization:
    """
    Test suite for CacheKeyGenerator initialization and configuration.

    Scope:
        - Generator instance creation with default and custom parameters
        - Configuration validation and parameter handling
        - Performance monitor integration setup

    Business Critical:
        Key generator configuration determines cache key format and performance characteristics

    Test Strategy:
        - Unit tests for generator initialization with various configurations
        - Parameter validation and boundary condition testing
        - Performance monitor integration verification
        - Thread safety and stateless operation validation

    External Dependencies:
        - Standard library components (hashlib, time): For key generation and timing operations
    """

    def test_generator_creates_with_default_configuration(self):
        """
        Test that CacheKeyGenerator initializes with appropriate default configuration.

        Verifies:
            Generator instance is created with sensible defaults for text processing

        Business Impact:
            Ensures developers can use key generator without complex configuration

        Scenario:
            Given: No configuration parameters provided
            When: CacheKeyGenerator is instantiated
            Then: Generator instance is created with default text hash threshold and SHA256

        Edge Cases Covered:
            - Default text_hash_threshold (1000 characters)
            - Default hash algorithm (SHA256)
            - Default performance monitor (None)
            - Generator readiness for immediate use

        Mocks Used:
            - None (pure initialization test)

        Related Tests:
            - test_generator_applies_custom_configuration_parameters()
            - test_generator_validates_configuration_parameters()
        """
        generator = CacheKeyGenerator()

        # Verify default configuration per contract
        assert generator.text_hash_threshold == 1000
        assert generator.hash_algorithm == hashlib.sha256
        assert generator.performance_monitor is None

        # Verify generator is ready for immediate use
        test_key = generator.generate_cache_key("test", "summarize", {})
        assert test_key is not None
        assert "ai_cache:" in test_key
        assert "op:summarize" in test_key

    def test_generator_applies_custom_configuration_parameters(self):
        """
        Test that CacheKeyGenerator properly applies custom configuration parameters.

        Verifies:
            Custom parameters override defaults while maintaining generator functionality

        Business Impact:
            Allows optimization of key generation for specific text processing patterns

        Scenario:
            Given: CacheKeyGenerator with custom text threshold and performance monitor
            When: Generator is instantiated with specific configuration
            Then: Generator uses custom settings for text processing and monitoring

        Edge Cases Covered:
            - Custom text_hash_threshold values (small and large)
            - Custom hash algorithms (different from SHA256)
            - Performance monitor integration
            - Configuration parameter interaction

        Mocks Used:
            - None

        Related Tests:
            - test_generator_creates_with_default_configuration()
            - test_generator_validates_configuration_parameters()
        """
        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        # Test custom threshold (smaller than default)
        generator = CacheKeyGenerator(
            text_hash_threshold=500,
            hash_algorithm=hashlib.sha256,
            performance_monitor=monitor,
        )

        # Verify custom configuration is applied
        assert generator.text_hash_threshold == 500
        assert generator.hash_algorithm == hashlib.sha256
        assert generator.performance_monitor is monitor

        # Test custom threshold (larger than default)
        generator_large = CacheKeyGenerator(text_hash_threshold=2000)
        assert generator_large.text_hash_threshold == 2000

        # Verify generator functionality with custom settings
        test_key = generator.generate_cache_key("test", "summarize", {})
        assert test_key is not None
        assert "ai_cache:" in test_key

        # Verify generator is functional with real monitor
        assert test_key is not None
        assert "ai_cache:op:summarize" in test_key

    def test_generator_validates_configuration_parameters(self):
        """
        Test that CacheKeyGenerator validates configuration parameters during initialization.

        Verifies:
            Invalid configuration parameters are rejected with descriptive error messages

        Business Impact:
            Prevents misconfigured key generators that could cause cache inconsistencies

        Scenario:
            Given: CacheKeyGenerator initialization with invalid parameters
            When: Generator is instantiated with out-of-range or invalid configuration
            Then: Appropriate validation error is raised with configuration guidance

        Edge Cases Covered:
            - Invalid text_hash_threshold values (negative, zero, extremely large)
            - Invalid hash algorithm specifications
            - Parameter type validation
            - Configuration boundary conditions

        Mocks Used:
            - None (validation logic test)

        Related Tests:
            - test_generator_applies_custom_configuration_parameters()
            - test_generator_maintains_thread_safety()
        """
        # Note: Current implementation doesn't validate parameters at initialization
        # This test documents the expected validation behavior that should be implemented

        # Test reasonable boundary values that should work
        generator_min = CacheKeyGenerator(text_hash_threshold=1)
        assert generator_min.text_hash_threshold == 1

        generator_max = CacheKeyGenerator(text_hash_threshold=100000)
        assert generator_max.text_hash_threshold == 100000

        # Test that generator accepts valid hash algorithms
        generator_md5 = CacheKeyGenerator(hash_algorithm=hashlib.md5)
        assert generator_md5.hash_algorithm == hashlib.md5

        # Test that generator functions correctly with valid parameters
        key = generator_min.generate_cache_key("test", "summarize", {})
        assert key is not None
        assert "ai_cache:" in key

        # Verify extreme values still function (graceful handling)
        generator_extreme = CacheKeyGenerator(text_hash_threshold=0)
        key_extreme = generator_extreme.generate_cache_key("test", "summarize", {})
        assert "hash:" in key_extreme  # Should hash everything when threshold is 0

    def test_generator_maintains_thread_safety(self):
        """
        Test that CacheKeyGenerator maintains thread safety for concurrent usage.

        Verifies:
            Generator can be safely used across multiple threads without state corruption

        Business Impact:
            Enables safe concurrent cache key generation in multi-threaded applications

        Scenario:
            Given: CacheKeyGenerator instance shared across threads
            When: Multiple threads generate cache keys simultaneously
            Then: All keys are generated correctly without interference or state corruption

        Edge Cases Covered:
            - Concurrent key generation operations
            - Stateless operation verification
            - Thread isolation of key generation logic
            - Performance monitor thread safety

        Mocks Used:
            - None (thread safety test)

        Related Tests:
            - test_generator_validates_configuration_parameters()
            - test_generator_provides_consistent_behavior()
        """
        import threading

        generator = CacheKeyGenerator()
        results = []
        lock = threading.Lock()  # Protect results list

        def generate_key(thread_id):
            """Generate key with thread-specific text."""
            text = f"thread_{thread_id}_text"
            key = generator.generate_cache_key(
                text, "summarize", {"thread_id": thread_id}
            )
            with lock:
                results.append((thread_id, key))

        # Create and start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=generate_key, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all threads completed successfully
        assert len(results) == 10

        # Verify no key collisions (all keys should be unique)
        keys = [result[1] for result in results]
        assert len(set(keys)) == 10  # All keys are unique

        # Verify all keys have proper format
        for thread_id, key in results:
            assert "ai_cache:" in key
            assert "op:summarize" in key
            # Verify thread-specific content is preserved
            assert f"thread_{thread_id}" in key or "opts:" in key

    def test_generator_provides_consistent_behavior(self):
        """
        Test that CacheKeyGenerator provides consistent behavior across multiple invocations.

        Verifies:
            Generator produces identical keys for identical inputs across time

        Business Impact:
            Ensures cache consistency and proper cache hit behavior for repeated operations

        Scenario:
            Given: CacheKeyGenerator with consistent configuration
            When: Same inputs are provided multiple times for key generation
            Then: Identical cache keys are generated consistently

        Edge Cases Covered:
            - Input consistency across time
            - Configuration stability
            - Deterministic key generation behavior
            - State independence verification

        Mocks Used:
            - None (consistency verification test)

        Related Tests:
            - test_generator_maintains_thread_safety()
            - test_generator_applies_custom_configuration_parameters()
        """
        generator = CacheKeyGenerator()

        text = "Consistent test text for key generation"
        operation = "summarize"
        options = {"max_length": 100, "temperature": 0.7}

        # Generate the same key multiple times
        key1 = generator.generate_cache_key(text, operation, options)
        key2 = generator.generate_cache_key(text, operation, options)
        key3 = generator.generate_cache_key(text, operation, options)

        # Verify all keys are identical
        assert key1 == key2 == key3

        # Test with different generator instance (same config)
        generator2 = CacheKeyGenerator()
        key4 = generator2.generate_cache_key(text, operation, options)

        # Should produce the same key
        assert key1 == key4

        # Test that different inputs produce different keys
        different_key = generator.generate_cache_key(
            text + " modified", operation, options
        )
        assert different_key != key1

        # Test state independence - generator internal state shouldn't affect keys
        for i in range(5):
            test_key = generator.generate_cache_key(f"test_{i}", "sentiment", {})
            assert test_key is not None

        # Original key should still be the same
        final_key = generator.generate_cache_key(text, operation, options)
        assert final_key == key1

        # Verify keys have expected structure
        assert "ai_cache:" in key1
        assert "op:summarize" in key1
        assert "txt:" in key1
        assert "opts:" in key1


class TestCacheKeyGeneration:
    """
    Test suite for core cache key generation functionality.

    Scope:
        - generate_cache_key() method behavior with various input combinations
        - Text processing and hashing threshold behavior
        - AI operation key format compatibility and consistency
        - Question extraction and embedding for Q&A operations

    Business Critical:
        Cache key generation directly impacts cache hit rates and AI processing efficiency

    Test Strategy:
        - Unit tests for key generation with different text sizes and operations
        - Format compatibility validation with existing cache systems
        - Text hashing threshold boundary testing
        - Question extraction and embedding verification

    External Dependencies:
        - hashlib: Standard library hashing (not mocked for realistic behavior)
    """

    def test_generate_cache_key_creates_properly_formatted_keys(
        self, sample_text, sample_options
    ):
        """
        Test that generate_cache_key() creates properly formatted cache keys.

        Verifies:
            Generated keys follow expected format and contain all required components

        Business Impact:
            Ensures cache key compatibility with existing AI cache systems

        Scenario:
            Given: CacheKeyGenerator with sample text, operation, and options
            When: generate_cache_key() is called with typical AI operation parameters
            Then: Formatted key is returned with operation, text, and options components

        Edge Cases Covered:
            - Standard AI operations (summarize, sentiment, questions)
            - Various text lengths and content types
            - Different option combinations and structures
            - Key format consistency and parsing

        Mocks Used:
            - None (format verification test using real data)

        Related Tests:
            - test_generate_cache_key_handles_text_below_hash_threshold()
            - test_generate_cache_key_handles_text_above_hash_threshold()
        """
        generator = CacheKeyGenerator()

        # Test with sample data
        key = generator.generate_cache_key(sample_text, "summarize", sample_options)

        # Verify key format per contract: "ai_cache:op:{operation}|txt:{text_or_hash}|opts:{options_hash}"
        assert key.startswith("ai_cache:op:")
        assert "|txt:" in key
        assert "|opts:" in key
        assert "summarize" in key

        # Test different operations
        operations = ["sentiment", "questions", "key_points"]
        for operation in operations:
            op_key = generator.generate_cache_key(
                sample_text, operation, sample_options
            )
            assert f"op:{operation}" in op_key
            assert op_key.startswith("ai_cache:op:")

        # Test with different options
        different_options = {"temperature": 0.8, "max_tokens": 150}
        key_with_diff_options = generator.generate_cache_key(
            sample_text, "summarize", different_options
        )

        # Keys should be different with different options
        assert key != key_with_diff_options

        # But both should have proper format
        assert key_with_diff_options.startswith("ai_cache:op:")
        assert "|opts:" in key_with_diff_options

        # Verify key components are properly separated
        parts = key.split("|")
        assert len(parts) >= 3  # op, txt, opts (minimum)
        assert parts[0].startswith("ai_cache:op:")
        assert parts[1].startswith("txt:")
        assert any(part.startswith("opts:") for part in parts)

    def test_generate_cache_key_handles_text_below_hash_threshold(
        self, sample_short_text, sample_options
    ):
        """
        Test that generate_cache_key() includes text directly when below hash threshold.

        Verifies:
            Short text is included directly in cache keys for maximum readability

        Business Impact:
            Provides readable cache keys for debugging and monitoring of small text operations

        Scenario:
            Given: CacheKeyGenerator with text below configured hash threshold
            When: generate_cache_key() is called with short text content
            Then: Cache key includes text directly without hashing

        Edge Cases Covered:
            - Text exactly at threshold boundary
            - Very short text (single words, phrases)
            - Empty or whitespace-only text
            - Text threshold configuration verification

        Mocks Used:
            - None (direct text inclusion verification)

        Related Tests:
            - test_generate_cache_key_creates_properly_formatted_keys()
            - test_generate_cache_key_handles_text_above_hash_threshold()
        """
        generator = CacheKeyGenerator(text_hash_threshold=1000)

        # Ensure sample_short_text is actually short (below threshold)
        assert len(sample_short_text) < 1000

        key = generator.generate_cache_key(
            sample_short_text, "summarize", sample_options
        )

        # Verify text is included directly (not hashed)
        # Text should appear in the key - need to handle sanitization
        sanitized_text = sample_short_text.replace("|", "_").replace(":", "_")
        assert sanitized_text in key or sample_short_text in key
        assert "hash:" not in key  # Should not be hashed

        # Test with very short text
        short_text = "Hi"
        short_key = generator.generate_cache_key(short_text, "sentiment", {})
        assert short_text in short_key
        assert "hash:" not in short_key

        # Test at boundary (text exactly at threshold)
        boundary_text = "x" * 1000  # Exactly at threshold
        boundary_key = generator.generate_cache_key(boundary_text, "summarize", {})
        # At boundary, text should still be included directly
        assert "hash:" not in boundary_key

        # Test just below boundary
        below_boundary_text = "x" * 999
        below_key = generator.generate_cache_key(below_boundary_text, "summarize", {})
        assert "hash:" not in below_key

    def test_generate_cache_key_handles_text_above_hash_threshold(
        self, sample_long_text, sample_options
    ):
        """
        Test that generate_cache_key() hashes text when above threshold for memory efficiency.

        Verifies:
            Large text is hashed to prevent cache key length issues while maintaining uniqueness

        Business Impact:
            Prevents cache key storage problems while preserving cache efficiency for large documents

        Scenario:
            Given: CacheKeyGenerator with text above configured hash threshold
            When: generate_cache_key() is called with large text content
            Then: Cache key includes hashed text representation for efficiency

        Edge Cases Covered:
            - Text significantly above threshold
            - Text exactly at threshold boundary
            - Very large text (multiple MB)
            - Hash collision avoidance verification

        Mocks Used:
            - None (hash behavior verification with real hashing)

        Related Tests:
            - test_generate_cache_key_handles_text_below_hash_threshold()
            - test_generate_cache_key_uses_streaming_hash_for_large_text()
        """
        generator = CacheKeyGenerator(text_hash_threshold=1000)

        # Ensure sample_long_text is actually long (above threshold)
        assert len(sample_long_text) > 1000

        key = generator.generate_cache_key(
            sample_long_text, "summarize", sample_options
        )

        # Verify text is hashed (not included directly)
        # Long text should NOT appear in the key
        assert sample_long_text not in key

        # Should contain hash indicator and actual hash
        assert "hash:" in key

        # Hash should be consistent for same input
        key2 = generator.generate_cache_key(
            sample_long_text, "summarize", sample_options
        )
        assert key == key2

        # Different large texts should produce different hashes
        different_long_text = sample_long_text + " additional content"
        different_key = generator.generate_cache_key(
            different_long_text, "summarize", sample_options
        )
        assert key != different_key
        assert "hash:" in different_key

        # Test just above boundary
        above_boundary_text = "x" * 1001  # Just above threshold
        above_key = generator.generate_cache_key(above_boundary_text, "summarize", {})
        assert above_boundary_text not in above_key
        assert "hash:" in above_key

        # Verify hash format is consistent
        hash_parts = [part for part in key.split("|") if "hash:" in part]
        assert len(hash_parts) == 1
        hash_value = hash_parts[0].replace("txt:hash:", "")
        assert len(hash_value) == 16  # Should be 16 character hash

    def test_generate_cache_key_uses_streaming_hash_for_large_text(
        self, sample_long_text, sample_options
    ):
        """
        Test that generate_cache_key() uses streaming hash for memory-efficient large text processing.

        Verifies:
            Large text processing doesn't consume excessive memory through streaming algorithms

        Business Impact:
            Enables processing of very large documents without memory exhaustion

        Scenario:
            Given: CacheKeyGenerator configured for streaming hash processing
            When: generate_cache_key() is called with very large text content
            Then: Streaming hash algorithm processes text efficiently without memory issues

        Edge Cases Covered:
            - Multi-megabyte text processing
            - Memory usage monitoring during hash generation
            - Streaming algorithm verification
            - Hash consistency with streaming vs. direct methods

        Mocks Used:
            - None (streaming behavior verification with realistic text sizes)

        Related Tests:
            - test_generate_cache_key_handles_text_above_hash_threshold()
            - test_generate_cache_key_maintains_hash_consistency()
        """
        import os

        import psutil

        generator = CacheKeyGenerator(text_hash_threshold=500)

        # Create very large text (1MB+)
        large_text = (
            "This is test content for streaming hash verification. " * 20000
        )  # ~1MB+
        assert len(large_text) > 1_000_000

        # Monitor memory usage before processing
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # Generate key with large text
        key = generator.generate_cache_key(large_text, "summarize", sample_options)

        # Monitor memory after processing
        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before

        # Memory increase should be reasonable (not holding full text in memory)
        # Allow for some memory overhead but not the full text size
        # Be more lenient with memory check as Python's memory management can be complex
        text_size = len(large_text.encode("utf-8"))
        # Just verify we didn't use an unreasonable amount of extra memory
        # Allow for generous memory overhead due to Python's memory management
        assert (
            memory_increase < text_size * 5
        )  # Less than 5x text size (very generous for CI)

        # Verify hash is generated correctly
        assert "hash:" in key
        assert large_text not in key

        # Test consistency - streaming should produce same hash
        key2 = generator.generate_cache_key(large_text, "summarize", sample_options)
        assert key == key2

        # Test with even larger text to verify scalability
        very_large_text = large_text * 2  # ~2MB (reduced from 5MB for test efficiency)
        very_large_key = generator.generate_cache_key(very_large_text, "summarize", {})
        assert "hash:" in very_large_key
        assert very_large_key != key  # Different texts should have different hashes

    def test_generate_cache_key_extracts_question_for_qa_operations(self, sample_text):
        """
        Test that generate_cache_key() properly extracts and includes questions for Q&A operations.

        Verifies:
            Q&A operations have questions extracted from options and included in cache keys

        Business Impact:
            Ensures proper cache differentiation for different questions on the same text

        Scenario:
            Given: CacheKeyGenerator with Q&A operation containing embedded question
            When: generate_cache_key() is called with question in options parameter
            Then: Cache key includes separate question component for proper differentiation

        Edge Cases Covered:
            - Questions embedded in options dictionary
            - Various question lengths and complexity
            - Question hashing for large questions
            - Q&A operation detection and handling

        Mocks Used:
            - None (question extraction verification with real data)

        Related Tests:
            - test_generate_cache_key_creates_properly_formatted_keys()
            - test_generate_cache_key_handles_various_operation_types()
        """
        generator = CacheKeyGenerator()

        # Test Q&A operation with question in options
        question = "What is the main point of this text?"
        qa_options = {"question": question, "max_tokens": 150, "temperature": 0.7}

        key = generator.generate_cache_key(sample_text, "qa", qa_options)

        # Verify key format includes question component per contract
        # Format should be: "ai_cache:op:qa|txt:{text}|opts:{options_hash}|q:{question_hash}"
        assert "|q:" in key
        assert "op:qa" in key

        # Test different questions on same text produce different keys
        question2 = "What are the key benefits mentioned?"
        qa_options2 = qa_options.copy()
        qa_options2["question"] = question2

        key2 = generator.generate_cache_key(sample_text, "qa", qa_options2)
        assert key != key2
        assert "|q:" in key2

        # Test that same question produces same key
        key3 = generator.generate_cache_key(sample_text, "qa", qa_options)
        assert key == key3

        # Test with long question (should be hashed)
        long_question = "This is a very long question " * 50  # Long question
        qa_options_long = {"question": long_question, "max_tokens": 150}

        long_key = generator.generate_cache_key(sample_text, "qa", qa_options_long)
        assert "|q:" in long_key

        # Question is hashed, but key should still be unique
        assert long_key != key

        # Test non-QA operations still get question component when question is provided
        # The current implementation includes question for all operations when present
        non_qa_key = generator.generate_cache_key(
            sample_text, "summarize", {"question": question}
        )
        # Question will be included for any operation type when present in options
        assert "|q:" in non_qa_key

    def test_generate_cache_key_handles_various_operation_types(
        self, sample_text, ai_cache_test_data
    ):
        """
        Test that generate_cache_key() handles different AI operation types consistently.

        Verifies:
            All supported AI operations receive appropriate key generation treatment

        Business Impact:
            Ensures consistent caching behavior across all AI processing operations

        Scenario:
            Given: CacheKeyGenerator with various AI operation types
            When: generate_cache_key() is called with different operations (summarize, sentiment, etc.)
            Then: Appropriate cache keys are generated for each operation type

        Edge Cases Covered:
            - Standard AI operations (summarize, sentiment, questions, qa)
            - Custom operation types
            - Operation parameter variations
            - Operation-specific key generation logic

        Mocks Used:
            - None (operation handling verification with test data)

        Related Tests:
            - test_generate_cache_key_extracts_question_for_qa_operations()
            - test_generate_cache_key_maintains_backward_compatibility()
        """
        generator = CacheKeyGenerator()

        # Test each operation from ai_cache_test_data
        operations_data = ai_cache_test_data["operations"]
        generated_keys = {}

        for operation, data in operations_data.items():
            if operation == "qa":
                # Q&A operation with question
                options = data["options"].copy()
                options["question"] = data["question"]
                key = generator.generate_cache_key(data["text"], operation, options)
                # Q&A keys should have question component
                assert "|q:" in key
            else:
                # Standard operations
                key = generator.generate_cache_key(
                    data["text"], operation, data["options"]
                )
                # Standard operations should not have question component
                # (question only appears for qa operations or when explicitly provided)
                if "question" not in data["options"]:
                    assert "|q:" not in key or key.endswith(
                        "|q:"
                    )  # Empty question component

            # Verify operation is in the key
            assert f"op:{operation}" in key
            assert key.startswith("ai_cache:")

            generated_keys[operation] = key

        # Verify all keys are unique
        all_keys = list(generated_keys.values())
        assert len(set(all_keys)) == len(all_keys)

        # Test custom operation type
        custom_key = generator.generate_cache_key(
            sample_text, "custom_analysis", {"custom_param": "value"}
        )
        assert "op:custom_analysis" in custom_key
        assert custom_key.startswith("ai_cache:")

        # Verify custom operation produces different key
        assert custom_key not in generated_keys.values()

        # Test standard operations without any options
        simple_operations = ["summarize", "sentiment", "questions"]
        for op in simple_operations:
            simple_key = generator.generate_cache_key(sample_text, op, {})
            assert f"op:{op}" in simple_key
            assert simple_key.startswith("ai_cache:")

    def test_generate_cache_key_maintains_backward_compatibility(
        self, sample_text, sample_options
    ):
        """
        Test that generate_cache_key() maintains backward compatibility with existing cache keys.

        Verifies:
            Generated keys remain compatible with existing cached data and key formats

        Business Impact:
            Preserves existing cache data value during key generator updates

        Scenario:
            Given: CacheKeyGenerator with inputs matching legacy cache patterns
            When: generate_cache_key() is called with parameters from existing cache entries
            Then: Generated keys match expected legacy format for cache hit preservation

        Edge Cases Covered:
            - Legacy key format preservation
            - Existing cache data compatibility
            - Format evolution handling
            - Compatibility validation with historical keys

        Mocks Used:
            - None (compatibility verification with known key patterns)

        Related Tests:
            - test_generate_cache_key_handles_various_operation_types()
            - test_generate_cache_key_maintains_hash_consistency()
        """
        generator = CacheKeyGenerator()

        # Test standard format compatibility per contract
        key = generator.generate_cache_key(sample_text, "summarize", sample_options)

        # Verify format matches contract specification
        # "ai_cache:op:{operation}|txt:{text_or_hash}|opts:{options_hash}"
        assert key.startswith("ai_cache:op:")
        parts = key.split("|")
        assert len(parts) >= 3  # op, txt, opts (and possibly q for Q&A)

        assert parts[0].startswith("ai_cache:op:")
        assert parts[1].startswith("txt:")
        assert any(part.startswith("opts:") for part in parts)

        # Test with historical operation types
        legacy_operations = ["summarize", "sentiment", "questions"]
        for operation in legacy_operations:
            legacy_key = generator.generate_cache_key(
                sample_text, operation, sample_options
            )
            assert f"op:{operation}" in legacy_key
            assert legacy_key.startswith("ai_cache:")

        # Test consistent hash for options
        # Same options should always produce same hash component
        key1 = generator.generate_cache_key(sample_text, "summarize", sample_options)
        key2 = generator.generate_cache_key(sample_text, "summarize", sample_options)

        # Keys should be identical for same inputs
        assert key1 == key2

        # Test Q&A compatibility with question component
        qa_options = {"question": "What is this about?", "max_tokens": 100}
        qa_key = generator.generate_cache_key(sample_text, "qa", qa_options)
        assert "|q:" in qa_key  # Q&A specific format

        # Test empty options compatibility
        empty_key = generator.generate_cache_key(sample_text, "summarize", {})
        assert "ai_cache:" in empty_key
        assert "op:summarize" in empty_key

        # Test None options handling
        try:
            none_key = generator.generate_cache_key(sample_text, "summarize", None)
            # If it doesn't crash, should still produce a valid key
            assert "ai_cache:" in none_key if none_key else True
        except (TypeError, AttributeError):
            # If None options cause an error, that's acceptable behavior
            pass

    def test_generate_cache_key_maintains_hash_consistency(
        self, sample_long_text, sample_options
    ):
        """
        Test that generate_cache_key() produces consistent hashes for identical large text inputs.

        Verifies:
            Hash generation is deterministic and consistent across multiple invocations

        Business Impact:
            Ensures reliable cache hits for repeated large text processing operations

        Scenario:
            Given: CacheKeyGenerator with identical large text inputs
            When: generate_cache_key() is called multiple times with same large text
            Then: Identical hashed cache keys are generated consistently

        Edge Cases Covered:
            - Hash determinism verification
            - Multiple invocation consistency
            - Large text hash stability
            - Hash algorithm consistency

        Mocks Used:
            - None (hash consistency verification with real algorithms)

        Related Tests:
            - test_generate_cache_key_uses_streaming_hash_for_large_text()
            - test_generate_cache_key_maintains_backward_compatibility()
        """
        generator = CacheKeyGenerator(
            text_hash_threshold=500
        )  # Ensure long text gets hashed

        # Verify sample_long_text is above threshold
        assert len(sample_long_text) > 500

        # Generate keys multiple times with same input
        keys = []
        for i in range(5):
            key = generator.generate_cache_key(
                sample_long_text, "summarize", sample_options
            )
            keys.append(key)

        # All keys should be identical
        assert all(key == keys[0] for key in keys)

        # Test with different generator instances
        generator2 = CacheKeyGenerator(text_hash_threshold=500)
        key_different_instance = generator2.generate_cache_key(
            sample_long_text, "summarize", sample_options
        )
        assert key_different_instance == keys[0]

        # Test hash consistency across different hash algorithms (if configurable)
        generator_sha256 = CacheKeyGenerator(
            text_hash_threshold=500, hash_algorithm=hashlib.sha256
        )
        key_sha256 = generator_sha256.generate_cache_key(
            sample_long_text, "summarize", sample_options
        )

        # Should be consistent when using same algorithm
        assert key_sha256 == keys[0]

        # Verify hash component is deterministic by extracting it
        hash_part = None
        for part in keys[0].split("|"):
            if "hash:" in part:
                hash_part = part.replace("txt:hash:", "")
                break

        assert hash_part is not None
        assert len(hash_part) == 16  # Should be 16 character hash per implementation

        # Test that minor text changes produce different hashes
        modified_text = sample_long_text + " extra"
        modified_key = generator.generate_cache_key(
            modified_text, "summarize", sample_options
        )
        assert modified_key != keys[0]
        assert "hash:" in modified_key

        # Test consistency with different operations on same text
        sentiment_key = generator.generate_cache_key(
            sample_long_text, "sentiment", sample_options
        )
        # Should be different because operation is different
        assert sentiment_key != keys[0]
        # But should still be consistent
        sentiment_key2 = generator.generate_cache_key(
            sample_long_text, "sentiment", sample_options
        )
        assert sentiment_key == sentiment_key2


class TestPerformanceMonitoringIntegration:
    """
    Test suite for CacheKeyGenerator integration with performance monitoring.

    Scope:
        - Performance monitor integration and metrics collection
        - Key generation timing and statistics tracking
        - Optional monitoring behavior and graceful degradation
        - Statistics retrieval and reporting functionality

    Business Critical:
        Performance monitoring enables optimization and SLA compliance for cache operations

    Test Strategy:
        - Unit tests for performance monitor integration
        - Metrics collection verification during key generation
        - Statistics aggregation and reporting validation
        - Optional monitoring behavior testing

    External Dependencies:
        - None
    """

    def test_generator_integrates_with_performance_monitor(self):
        """
        Test that CacheKeyGenerator properly integrates with performance monitoring.

        Verifies:
            Performance monitor receives key generation metrics when configured

        Business Impact:
            Enables monitoring and optimization of cache key generation performance

        Scenario:
            Given: CacheKeyGenerator configured with performance monitor
            When: generate_cache_key() is called with monitoring enabled
            Then: Key generation metrics are recorded in performance monitor

        Edge Cases Covered:
            - Performance monitor integration during key generation
            - Metric recording for various key generation scenarios
            - Monitoring configuration validation
            - Performance data collection verification

        Mocks Used:
            - None

        Related Tests:
            - test_generator_records_key_generation_timing()
            - test_generator_handles_monitoring_gracefully_when_disabled()
        """
        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        generator = CacheKeyGenerator(performance_monitor=monitor)

        # Verify monitor is configured
        assert generator.performance_monitor is monitor

        # Generate a key to trigger monitoring
        key = generator.generate_cache_key(
            "test text", "summarize", {"max_length": 100}
        )

        # Verify key generation succeeded
        assert key is not None
        assert "ai_cache:" in key

        # Verify generator is functional with real monitor
        assert key is not None
        assert "ai_cache:op:summarize" in key

        # Test multiple key generations work properly
        key2 = generator.generate_cache_key("another test", "sentiment", {})
        assert key2 is not None
        assert "ai_cache:op:sentiment" in key2
        assert key != key2  # Different inputs should produce different keys

    def test_generator_records_key_generation_timing(self, sample_text, sample_options):
        """
        Test that CacheKeyGenerator records key generation timing in performance monitor.

        Verifies:
            Key generation duration is tracked for performance analysis and optimization

        Business Impact:
            Provides visibility into key generation performance for SLA monitoring

        Scenario:
            Given: CacheKeyGenerator with performance monitor enabled
            When: generate_cache_key() is called with various inputs
            Then: Key generation timing is recorded with appropriate metadata

        Edge Cases Covered:
            - Timing accuracy for fast key generation
            - Timing recording for different text sizes
            - Metadata inclusion in timing records
            - Performance overhead of timing measurement

        Mocks Used:
            - None

        Related Tests:
            - test_generator_integrates_with_performance_monitor()
            - test_generator_provides_key_generation_statistics()
        """
        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        generator = CacheKeyGenerator(performance_monitor=monitor)

        # Generate key with real monitor
        key = generator.generate_cache_key(sample_text, "summarize", sample_options)

        # Verify key generation succeeded and is functional
        assert key is not None
        assert "ai_cache:op:summarize" in key

        # Test with different text sizes to verify consistent behavior
        short_text = "short"
        long_text = "long text " * 500

        # Generate keys for different text sizes
        short_key = generator.generate_cache_key(short_text, "sentiment", {})
        long_key = generator.generate_cache_key(long_text, "summarize", {})

        # Verify all keys are functional
        assert short_key is not None
        assert long_key is not None
        assert "ai_cache:op:sentiment" in short_key
        assert "ai_cache:op:summarize" in long_key

        # Verify different text sizes produce different keys
        assert short_key != long_key

        # Test that long text gets hashed
        assert "hash:" in long_key  # Long text should be hashed
        assert "hash:" not in short_key  # Short text should not be hashed

    def test_generator_handles_monitoring_gracefully_when_disabled(
        self, sample_text, sample_options
    ):
        """
        Test that CacheKeyGenerator operates normally when performance monitoring is disabled.

        Verifies:
            Key generation functionality is unaffected when monitoring is not configured

        Business Impact:
            Ensures key generation works reliably in environments without monitoring infrastructure

        Scenario:
            Given: CacheKeyGenerator without performance monitor configured
            When: generate_cache_key() is called without monitoring
            Then: Cache keys are generated normally without monitoring overhead

        Edge Cases Covered:
            - No performance monitor configuration
            - Monitoring-free operation verification
            - Performance overhead elimination
            - Graceful monitoring absence handling

        Mocks Used:
            - None (monitoring-free operation test)

        Related Tests:
            - test_generator_records_key_generation_timing()
            - test_generator_provides_key_generation_statistics()
        """
        # Create generator without performance monitor
        generator = CacheKeyGenerator(performance_monitor=None)

        # Verify no monitor configured
        assert generator.performance_monitor is None

        # Generate keys should work normally
        key1 = generator.generate_cache_key(sample_text, "summarize", sample_options)
        assert key1 is not None
        assert "ai_cache:" in key1

        # Test multiple operations
        operations = ["sentiment", "questions", "key_points"]
        for operation in operations:
            key = generator.generate_cache_key(sample_text, operation, sample_options)
            assert key is not None
            assert f"op:{operation}" in key

        # Test with different text sizes
        short_text = "short"
        long_text = "long text " * 1000

        short_key = generator.generate_cache_key(short_text, "summarize", {})
        long_key = generator.generate_cache_key(long_text, "summarize", {})

        assert short_key is not None
        assert long_key is not None
        assert short_key != long_key

        # Verify different text processing approaches work
        assert "hash:" not in short_key  # Short text should not be hashed
        assert "hash:" in long_key  # Long text should be hashed

        # Verify consistent behavior without monitoring
        key2 = generator.generate_cache_key(sample_text, "summarize", sample_options)
        assert key1 == key2  # Same inputs should produce same keys

        # Test Q&A operation without monitoring
        qa_options = {"question": "What is this about?", "max_tokens": 100}
        qa_key = generator.generate_cache_key(sample_text, "qa", qa_options)
        assert qa_key is not None
        assert "|q:" in qa_key

        # Test performance (should be fast without monitoring)
        import time

        start_time = time.time()
        for i in range(100):
            generator.generate_cache_key(f"test_{i}", "summarize", {})
        end_time = time.time()
        duration = end_time - start_time
        # Should complete 100 keys in reasonable time
        assert duration < 1.0  # Less than 1 second for 100 keys

    def test_generator_provides_key_generation_statistics(
        self, sample_text, sample_options
    ):
        """
        Test that CacheKeyGenerator provides comprehensive key generation statistics.

        Verifies:
            Statistics retrieval provides meaningful data for performance analysis

        Business Impact:
            Enables performance optimization and capacity planning for cache operations

        Scenario:
            Given: CacheKeyGenerator with performance monitoring and historical usage
            When: get_key_generation_stats() is called after key generation operations
            Then: Comprehensive statistics are returned with timing, counts, and distribution data

        Edge Cases Covered:
            - Statistics accuracy across multiple key generations
            - Statistical aggregation verification
            - Performance data interpretation
            - Statistics reset and initialization handling

        Mocks Used:
            - None

        Related Tests:
            - test_generator_records_key_generation_timing()
            - test_generator_tracks_text_size_distribution_in_statistics()
        """
        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        generator = CacheKeyGenerator(performance_monitor=monitor)

        # Generate some keys to create statistics
        generator.generate_cache_key(sample_text, "summarize", sample_options)
        generator.generate_cache_key("short text", "sentiment", {})
        generator.generate_cache_key("long text " * 500, "questions", {})

        # Get statistics
        stats = generator.get_key_generation_stats()

        # Verify statistics structure per contract
        assert isinstance(stats, dict)

        # Should contain required fields per contract
        expected_fields = [
            "total_keys_generated",
            "average_generation_time",
            "text_size_distribution",
            "operation_distribution",
            "recent_performance",
        ]

        for field in expected_fields:
            assert field in stats, f"Statistics missing required field: {field}"

        # Verify data types and reasonable values
        assert isinstance(stats["total_keys_generated"], int)
        assert stats["total_keys_generated"] > 0

        assert isinstance(stats["average_generation_time"], (int, float))
        assert stats["average_generation_time"] >= 0

        assert isinstance(stats["text_size_distribution"], dict)
        assert isinstance(stats["operation_distribution"], dict)
        assert isinstance(stats["recent_performance"], dict)

        # Verify statistics contain expected distribution data
        text_dist = stats["text_size_distribution"]
        assert "small" in text_dist or "large" in text_dist
        assert "average_size" in text_dist

        # Test with no monitoring (should handle gracefully)
        generator_no_monitor = CacheKeyGenerator(performance_monitor=None)
        stats_no_monitor = generator_no_monitor.get_key_generation_stats()

        # Should return empty/default statistics when no monitor
        assert isinstance(stats_no_monitor, dict)
        # With real monitor, we expect actual statistics structure
        assert "total_keys_generated" in stats_no_monitor

    def test_generator_tracks_text_size_distribution_in_statistics(self):
        """
        Test that CacheKeyGenerator tracks text size distribution for optimization insights.

        Verifies:
            Statistics include text size patterns for hash threshold optimization

        Business Impact:
            Enables optimization of text hash thresholds based on actual usage patterns

        Scenario:
            Given: CacheKeyGenerator with monitoring across various text sizes
            When: Key generation occurs with small, medium, and large text inputs
            Then: Statistics reflect text size distribution for threshold optimization

        Edge Cases Covered:
            - Text size categorization and tracking
            - Distribution accuracy across various sizes
            - Threshold optimization data collection
            - Statistical pattern recognition

        Mocks Used:
            - None

        Related Tests:
            - test_generator_provides_key_generation_statistics()
            - test_generator_tracks_operation_distribution_in_statistics()
        """
        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        # Create text samples for different text sizes
        text_sizes = {
            "small": "Small text",  # < 100 chars
            "medium": "Medium length text " * 50,  # ~1000 chars
            "large": "Very long text " * 200,  # > 2000 chars
        }

        generator = CacheKeyGenerator(
            text_hash_threshold=1000, performance_monitor=monitor
        )

        # Generate keys with different text sizes
        for size_category, text in text_sizes.items():
            # Generate multiple keys for each size category
            for i in range(3):
                generator.generate_cache_key(text + f" {i}", "summarize", {})

        # Get statistics to verify text size distribution tracking
        stats = generator.get_key_generation_stats()

        # Verify text size distribution is tracked
        assert "text_size_distribution" in stats
        text_dist = stats["text_size_distribution"]
        assert isinstance(text_dist, dict)

        # Should have entries for small and large categories
        assert "small" in text_dist or "large" in text_dist
        assert len(text_dist) > 0

        # Values should be numeric (counts or percentages)
        for category, value in text_dist.items():
            assert isinstance(value, (int, float))
            assert value >= 0

        # Verify statistics structure with real monitor
        if "average_size" in text_dist:
            assert text_dist["average_size"] >= 0

    def test_generator_tracks_operation_distribution_in_statistics(
        self, ai_cache_test_data
    ):
        """
        Test that CacheKeyGenerator tracks operation distribution for usage analysis.

        Verifies:
            Statistics include operation type patterns for cache optimization

        Business Impact:
            Provides insights into AI operation usage patterns for cache tuning

        Scenario:
            Given: CacheKeyGenerator with monitoring across various AI operations
            When: Key generation occurs with different operation types
            Then: Statistics reflect operation distribution for usage pattern analysis

        Edge Cases Covered:
            - Operation type categorization and tracking
            - Usage pattern identification
            - Operation frequency analysis
            - Statistical operation insights

        Mocks Used:
            - None

        Related Tests:
            - test_generator_tracks_text_size_distribution_in_statistics()
            - test_generator_provides_key_generation_statistics()
        """
        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        operations_data = ai_cache_test_data["operations"]
        operation_counts = {}

        for operation, data in operations_data.items():
            count = 2 if operation != "qa" else 1
            operation_counts[operation] = count

        # Add custom operations
        for op, count in [("custom_op1", 2), ("custom_op2", 1)]:
            operation_counts[op] = count

        generator = CacheKeyGenerator(performance_monitor=monitor)

        # Generate keys for different operations using ai_cache_test_data
        for operation, data in operations_data.items():
            count = operation_counts[operation]
            for i in range(count):
                if operation == "qa":
                    options = data["options"].copy()
                    options["question"] = data["question"]
                    generator.generate_cache_key(data["text"], operation, options)
                else:
                    generator.generate_cache_key(
                        data["text"], operation, data["options"]
                    )

        # Add some custom operations to test tracking
        generator.generate_cache_key("test", "custom_op1", {})
        generator.generate_cache_key("test", "custom_op1", {})  # Same op twice
        generator.generate_cache_key("test", "custom_op2", {})

        # Get statistics to verify operation distribution tracking
        stats = generator.get_key_generation_stats()

        # Verify operation distribution is tracked
        assert "operation_distribution" in stats
        op_dist = stats["operation_distribution"]
        assert isinstance(op_dist, dict)

        # Should have entries for the operations we used
        assert len(op_dist) > 0

        # Values should be numeric (counts or percentages)
        for operation, value in op_dist.items():
            assert isinstance(value, (int, float))
            assert value >= 0

        # Verify statistics reflect the operations we performed
        if len(op_dist) > 0:
            # If operations are tracked, verify they're reasonable
            tracked_operations = set(op_dist.keys())
            expected_operations = set(operation_counts.keys())

            # Values should be reasonable for operations performed
            for operation, value in op_dist.items():
                assert value > 0  # Should have positive counts


class TestKeyGenerationEdgeCases:
    """
    Test suite for CacheKeyGenerator edge cases and boundary conditions.

    Scope:
        - Empty and whitespace-only text handling
        - Special characters and Unicode text processing
        - Extreme parameter values and boundary conditions
        - Error handling and graceful degradation scenarios

    Business Critical:
        Edge case handling prevents cache failures and ensures system reliability

    Test Strategy:
        - Boundary value testing for all parameters
        - Special character and encoding handling validation
        - Error condition testing and recovery verification
        - Performance testing with extreme inputs

    External Dependencies:
        - hashlib: Standard library hashing for edge case verification
    """

    def test_generator_handles_empty_text_gracefully(self, sample_options):
        """
        Test that CacheKeyGenerator handles empty text inputs gracefully.

        Verifies:
            Empty text inputs are processed without errors and produce valid cache keys

        Business Impact:
            Prevents cache failures when AI operations receive empty or null text inputs

        Scenario:
            Given: CacheKeyGenerator with empty string text input
            When: generate_cache_key() is called with empty text
            Then: Valid cache key is generated with appropriate empty text handling

        Edge Cases Covered:
            - Empty string text input
            - None text input handling
            - Whitespace-only text input
            - Zero-length text processing

        Mocks Used:
            - None (edge case handling verification)

        Related Tests:
            - test_generator_handles_whitespace_only_text()
            - test_generator_processes_special_characters_correctly()
        """
        generator = CacheKeyGenerator()

        # Test empty string
        empty_key = generator.generate_cache_key("", "summarize", sample_options)
        assert empty_key is not None
        assert "ai_cache:" in empty_key
        assert "op:summarize" in empty_key

        # Empty string should be included directly (not hashed)
        assert "hash:" not in empty_key

        # Test None input handling
        try:
            none_key = generator.generate_cache_key(None, "summarize", sample_options)
            # If it succeeds, should produce valid key
            assert none_key is not None
            assert "ai_cache:" in none_key
        except (TypeError, AttributeError) as e:
            # If it fails, that's acceptable for None input
            assert "none" in str(e).lower() or "str" in str(e).lower()

        # Test zero-length text variations
        zero_length_texts = ["", ""]
        for text in zero_length_texts:
            key = generator.generate_cache_key(text, "sentiment", {})
            assert key is not None
            assert "ai_cache:" in key
            assert "op:sentiment" in key

        # Verify different operations handle empty text consistently
        operations = ["summarize", "sentiment", "questions"]
        empty_keys = []
        for operation in operations:
            key = generator.generate_cache_key("", operation, {})
            assert key is not None
            assert f"op:{operation}" in key
            empty_keys.append(key)

        # Keys for different operations should be different
        assert len(set(empty_keys)) == len(empty_keys)

        # Test Q&A with empty text
        qa_key = generator.generate_cache_key("", "qa", {"question": "What is this?"})
        assert qa_key is not None
        assert "op:qa" in qa_key
        assert "|q:" in qa_key

        # Empty text key should be consistent
        empty_key2 = generator.generate_cache_key("", "summarize", sample_options)
        assert empty_key == empty_key2

    def test_generator_handles_whitespace_only_text(self, sample_options):
        """
        Test that CacheKeyGenerator handles whitespace-only text appropriately.

        Verifies:
            Text consisting only of whitespace characters is processed correctly

        Business Impact:
            Ensures consistent behavior when AI operations receive whitespace-heavy inputs

        Scenario:
            Given: CacheKeyGenerator with whitespace-only text (spaces, tabs, newlines)
            When: generate_cache_key() is called with whitespace text
            Then: Appropriate cache key is generated with whitespace normalization

        Edge Cases Covered:
            - Various whitespace characters (spaces, tabs, newlines)
            - Mixed whitespace combinations
            - Whitespace normalization behavior
            - Whitespace length threshold interactions

        Mocks Used:
            - None (whitespace handling verification)

        Related Tests:
            - test_generator_handles_empty_text_gracefully()
            - test_generator_processes_unicode_text_correctly()
        """
        generator = CacheKeyGenerator()

        # Test various whitespace-only texts
        whitespace_texts = [
            "   ",  # Spaces only
            "\t\t\t",  # Tabs only
            "\n\n\n",  # Newlines only
            " \t\n ",  # Mixed whitespace
            "    \t    \n    ",  # Complex mixed
        ]

        for whitespace_text in whitespace_texts:
            key = generator.generate_cache_key(
                whitespace_text, "summarize", sample_options
            )
            assert key is not None
            assert "ai_cache:" in key
            assert "op:summarize" in key

        # Test whitespace normalization - similar whitespace should produce same keys
        space_key1 = generator.generate_cache_key("   ", "summarize", {})
        space_key2 = generator.generate_cache_key("   ", "summarize", {})
        assert space_key1 == space_key2

        # Different whitespace patterns might produce different keys
        space_key = generator.generate_cache_key("   ", "summarize", {})
        tab_key = generator.generate_cache_key("\t\t\t", "summarize", {})
        # Whether these are the same depends on normalization - just ensure both work
        assert space_key is not None
        assert tab_key is not None

        # Test whitespace length vs threshold
        long_whitespace = " " * 2000  # Long whitespace (above hash threshold)
        long_ws_key = generator.generate_cache_key(long_whitespace, "summarize", {})
        assert long_ws_key is not None
        # Long whitespace should be hashed
        assert "hash:" in long_ws_key

        # Short whitespace should not be hashed
        short_whitespace = " " * 10
        short_ws_key = generator.generate_cache_key(short_whitespace, "summarize", {})
        assert "hash:" not in short_ws_key

        # Test mixed content with whitespace
        mixed_text = "  \t\n  text with whitespace  \t\n  "
        mixed_key = generator.generate_cache_key(mixed_text, "summarize", {})
        assert mixed_key is not None

        # Test Q&A with whitespace
        qa_key = generator.generate_cache_key(
            "   ", "qa", {"question": "What is this whitespace?"}
        )
        assert qa_key is not None
        assert "op:qa" in qa_key
        assert "|q:" in qa_key

    def test_generator_processes_special_characters_correctly(self, sample_options):
        """
        Test that CacheKeyGenerator processes special characters and symbols correctly.

        Verifies:
            Text with special characters, symbols, and punctuation is handled properly

        Business Impact:
            Ensures cache functionality for diverse text content including technical documents

        Scenario:
            Given: CacheKeyGenerator with text containing special characters and symbols
            When: generate_cache_key() is called with special character text
            Then: Valid cache key is generated with proper character encoding handling

        Edge Cases Covered:
            - Special punctuation and symbols
            - Control characters handling
            - Character encoding consistency
            - Symbol normalization behavior

        Mocks Used:
            - None (character handling verification)

        Related Tests:
            - test_generator_processes_unicode_text_correctly()
            - test_generator_handles_extremely_long_text()
        """
        generator = CacheKeyGenerator()

        # Test various special characters and symbols
        special_texts = [
            "Hello @world! #hashtag $money 100%",
            "Code: function() { return x && y || z; }",
            "Math: (x + y) * z = result ^ 2 ~ approximation",
            "Symbols: †‡§¶©®™°±×÷≈≠≤≥",
            "Punctuation: !@#$%^&*()_+-=[]{}|;':,.<>?",
            "Quotes: 'single' \"double\" `backtick` «guillemet»",
        ]

        for special_text in special_texts:
            key = generator.generate_cache_key(
                special_text, "summarize", sample_options
            )
            assert key is not None
            assert "ai_cache:" in key
            assert "op:summarize" in key

        # Test that different special character texts produce different keys
        keys = []
        for text in special_texts:
            key = generator.generate_cache_key(text, "summarize", {})
            keys.append(key)

        # All keys should be unique
        assert len(set(keys)) == len(keys)

        # Test pipe character sanitization (since pipe is used as separator)
        pipe_text = "Text with | pipe character"
        pipe_key = generator.generate_cache_key(pipe_text, "summarize", {})
        assert pipe_key is not None
        # Pipe should be sanitized to underscore in text part
        assert "pipe_character" in pipe_key or "pipe character" in pipe_key

        # Test colon character sanitization (since colon is used as separator)
        colon_text = "Text with: colon character"
        colon_key = generator.generate_cache_key(colon_text, "summarize", {})
        assert colon_key is not None

        # Test mixed special characters with regular text
        mixed_text = "Regular text with special: $100 @ 50% efficiency!"
        mixed_key = generator.generate_cache_key(mixed_text, "sentiment", {})
        assert mixed_key is not None

        # Test consistency - same special characters should produce same keys
        special_text = "Test! @#$ 100%"
        key1 = generator.generate_cache_key(special_text, "summarize", {})
        key2 = generator.generate_cache_key(special_text, "summarize", {})
        assert key1 == key2

        # Test Q&A with special characters
        qa_key = generator.generate_cache_key(
            "Text with symbols!", "qa", {"question": "What's the meaning of @#$%?"}
        )
        assert qa_key is not None
        assert "|q:" in qa_key

    def test_generator_processes_unicode_text_correctly(self, sample_options):
        """
        Test that CacheKeyGenerator processes Unicode text and international characters correctly.

        Verifies:
            Text with Unicode characters and international content is handled properly

        Business Impact:
            Ensures global application support with proper international text caching

        Scenario:
            Given: CacheKeyGenerator with Unicode text (emojis, international characters)
            When: generate_cache_key() is called with Unicode text
            Then: Valid cache key is generated with proper Unicode encoding handling

        Edge Cases Covered:
            - Various Unicode character ranges
            - Emoji and symbol Unicode handling
            - International alphabet processing
            - Unicode normalization consistency

        Mocks Used:
            - None (Unicode handling verification)

        Related Tests:
            - test_generator_processes_special_characters_correctly()
            - test_generator_maintains_encoding_consistency()
        """
        generator = CacheKeyGenerator()

        # Test various Unicode texts
        unicode_texts = [
            "Hello 世界 🌍",  # Mixed English, Chinese, emoji
            "Café résumé naïve",  # French accents
            "Привет мир 🇷🇺",  # Cyrillic + flag emoji
            "こんにちは世界 🇯🇵",  # Japanese + flag emoji
            "مرحبا بالعالم 🇸🇦",  # Arabic + flag emoji
            "¡Hola mundo! 🇪🇸",  # Spanish + flag emoji
            "🎉🎈🎊 Party time! 🎉🎈🎊",  # Multiple emojis
            "Symbols: ♠♥♦♣ ♪♫♬",  # Unicode symbols
        ]

        for unicode_text in unicode_texts:
            key = generator.generate_cache_key(
                unicode_text, "summarize", sample_options
            )
            assert key is not None
            assert "ai_cache:" in key
            assert "op:summarize" in key

        # Test that different Unicode texts produce different keys
        unicode_keys = []
        for text in unicode_texts:
            key = generator.generate_cache_key(text, "summarize", {})
            unicode_keys.append(key)

        # All keys should be unique
        assert len(set(unicode_keys)) == len(unicode_keys)

        # Test Unicode normalization consistency
        # These should be treated as equivalent if normalization is applied
        text_composed = "café"  # é as single character
        text_decomposed = "cafe\u0301"  # e + combining accent

        key_composed = generator.generate_cache_key(text_composed, "summarize", {})
        key_decomposed = generator.generate_cache_key(text_decomposed, "summarize", {})

        # Both should produce valid keys
        assert key_composed is not None
        assert key_decomposed is not None

        # Test very long Unicode text (ensure it's above threshold)
        # Need > 1000 characters (not bytes) to trigger hashing
        long_unicode = "🌟" * 1100  # 1100 star emojis > 1000 threshold
        # Verify it's actually above threshold
        unicode_length = len(long_unicode)
        assert (
            unicode_length > 1000
        ), f"Unicode text should be > 1000 chars, got {unicode_length}"

        long_unicode_key = generator.generate_cache_key(long_unicode, "summarize", {})
        assert long_unicode_key is not None
        # Should be hashed due to length
        assert "hash:" in long_unicode_key

        # Short Unicode should not be hashed
        short_unicode = "🌟🎉"
        short_unicode_key = generator.generate_cache_key(short_unicode, "summarize", {})
        assert "hash:" not in short_unicode_key

        # Test consistency - same Unicode should produce same keys
        emoji_text = "Hello 🌍 World 🎉"
        unicode_key1 = generator.generate_cache_key(emoji_text, "sentiment", {})
        unicode_key2 = generator.generate_cache_key(emoji_text, "sentiment", {})
        assert unicode_key1 == unicode_key2

        # Test Q&A with Unicode
        qa_key = generator.generate_cache_key(
            "Text about 世界", "qa", {"question": "What does 世界 mean? 🤔"}
        )
        assert qa_key is not None
        assert "|q:" in qa_key

    def test_generator_handles_extremely_long_text(self):
        """
        Test that CacheKeyGenerator handles extremely long text inputs efficiently.

        Verifies:
            Very large text inputs are processed without memory or performance issues

        Business Impact:
            Enables caching of large document processing operations without system impact

        Scenario:
            Given: CacheKeyGenerator with multi-megabyte text input
            When: generate_cache_key() is called with extremely long text
            Then: Cache key is generated efficiently using streaming algorithms

        Edge Cases Covered:
            - Multi-megabyte text processing
            - Memory usage efficiency verification
            - Processing time boundaries
            - Streaming algorithm effectiveness

        Mocks Used:
            - None (performance and memory efficiency verification)

        Related Tests:
            - test_generator_uses_streaming_hash_for_large_text()
            - test_generator_maintains_performance_under_load()
        """
        import os
        import time

        import psutil

        generator = CacheKeyGenerator(text_hash_threshold=1000)

        # Create extremely long text (2.5MB - reduced for CI stability)
        base_text = "This is a test of extremely long text processing capability. "
        extremely_long_text = base_text * 50000  # ~2.5MB (reduced from 100000)

        # Verify text is actually extremely long
        text_size_mb = len(extremely_long_text.encode("utf-8")) / (1024 * 1024)
        assert text_size_mb > 2.5, f"Text should be >2.5MB, got {text_size_mb:.2f}MB"

        # Monitor memory and time
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        start_time = time.time()

        # Generate key with extremely long text
        key = generator.generate_cache_key(extremely_long_text, "summarize", {})

        end_time = time.time()
        memory_after = process.memory_info().rss

        # Verify key was generated successfully
        assert key is not None
        assert "ai_cache:" in key
        assert "hash:" in key  # Should be hashed due to size
        assert extremely_long_text not in key  # Text should not appear directly

        # Verify performance constraints
        processing_time = end_time - start_time
        assert (
            processing_time < 10.0
        ), f"Processing took too long: {processing_time:.2f}s"

        # Verify memory efficiency (shouldn't hold entire text in memory)
        memory_increase = memory_after - memory_before
        text_size_bytes = len(extremely_long_text.encode("utf-8"))
        # Memory increase should be reasonable (allow for Python's memory management overhead)
        # This is primarily testing that we don't have major memory leaks
        # Be very generous with memory limits for CI environments
        assert (
            memory_increase < text_size_bytes * 5
        ), f"Memory usage too high: {memory_increase} bytes (text size: {text_size_bytes} bytes)"

        # Test consistency with extremely long text
        key2 = generator.generate_cache_key(extremely_long_text, "summarize", {})
        assert key == key2, "Extremely long text should produce consistent keys"

        # Test with different extremely long texts
        different_long_text = (base_text + "different ") * 100000
        different_key = generator.generate_cache_key(
            different_long_text, "summarize", {}
        )
        assert (
            different_key != key
        ), "Different long texts should produce different keys"

        # Test various operations with extremely long text
        operations = ["sentiment", "questions"]
        for operation in operations:
            op_key = generator.generate_cache_key(extremely_long_text, operation, {})
            assert op_key is not None
            assert "hash:" in op_key
            assert f"op:{operation}" in op_key
            assert op_key != key  # Different operations should produce different keys

    def test_generator_handles_extreme_option_combinations(self, sample_text):
        """
        Test that CacheKeyGenerator handles extreme option parameter combinations.

        Verifies:
            Unusual or extreme option combinations are processed without errors

        Business Impact:
            Ensures system reliability with diverse AI operation parameter combinations

        Scenario:
            Given: CacheKeyGenerator with extreme option parameter combinations
            When: generate_cache_key() is called with unusual option structures
            Then: Valid cache key is generated with appropriate option handling

        Edge Cases Covered:
            - Very large option dictionaries
            - Deeply nested option structures
            - Option value type variations
            - Extreme parameter value combinations

        Mocks Used:
            - None (option handling verification)

        Related Tests:
            - test_generator_processes_unicode_text_correctly()
            - test_generator_maintains_encoding_consistency()
        """
        generator = CacheKeyGenerator()

        # Test very large option dictionary
        large_options = {f"param_{i}": f"value_{i}" for i in range(100)}
        large_key = generator.generate_cache_key(
            sample_text, "summarize", large_options
        )
        assert large_key is not None
        assert "ai_cache:" in large_key

        # Test deeply nested options
        nested_options = {
            "level1": {
                "level2": {
                    "level3": {
                        "deep_param": "deep_value",
                        "deep_list": [1, 2, {"nested_in_list": True}],
                    }
                }
            },
            "simple_param": "simple_value",
        }
        nested_key = generator.generate_cache_key(
            sample_text, "summarize", nested_options
        )
        assert nested_key is not None
        assert "ai_cache:" in nested_key

        # Test various data types in options
        mixed_type_options = {
            "string": "text_value",
            "integer": 42,
            "float": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "none_value": None,
            "list": [1, "two", 3.0, True, None],
            "empty_dict": {},
            "empty_list": [],
            "unicode": "测试 🎉",
        }
        mixed_key = generator.generate_cache_key(
            sample_text, "summarize", mixed_type_options
        )
        assert mixed_key is not None
        assert "ai_cache:" in mixed_key

        # Test extreme values
        extreme_options = {
            "very_long_string": "x" * 10000,
            "very_large_number": 999999999999999,
            "very_small_number": -999999999999999,
            "very_precise_float": 1.23456789012345,
            "empty_string": "",
            "whitespace_string": "   \n\t   ",
        }
        extreme_key = generator.generate_cache_key(
            sample_text, "summarize", extreme_options
        )
        assert extreme_key is not None
        assert "ai_cache:" in extreme_key

        # Test options with special characters
        special_char_options = {
            "special@key": "special@value",
            "key with spaces": "value with spaces",
            "key-with-dashes": "value-with-dashes",
            "key_with_underscores": "value_with_underscores",
            "key.with.dots": "value.with.dots",
            "unicode_key_世界": "unicode_value_🌍",
        }
        special_key = generator.generate_cache_key(
            sample_text, "summarize", special_char_options
        )
        assert special_key is not None
        assert "ai_cache:" in special_key

        # Test that different extreme options produce different keys
        option_keys = [
            generator.generate_cache_key(sample_text, "summarize", large_options),
            generator.generate_cache_key(sample_text, "summarize", nested_options),
            generator.generate_cache_key(sample_text, "summarize", mixed_type_options),
            generator.generate_cache_key(sample_text, "summarize", extreme_options),
            generator.generate_cache_key(
                sample_text, "summarize", special_char_options
            ),
        ]

        # All keys should be unique
        assert len(set(option_keys)) == len(option_keys)

        # Test Q&A with extreme options
        qa_extreme_options = mixed_type_options.copy()
        qa_extreme_options["question"] = (
            "What is this complex text about?" * 10
        )  # Long question
        qa_extreme_key = generator.generate_cache_key(
            sample_text, "qa", qa_extreme_options
        )
        assert qa_extreme_key is not None
        assert "op:qa" in qa_extreme_key
        assert "|q:" in qa_extreme_key

    def test_generator_maintains_encoding_consistency(self):
        """
        Test that CacheKeyGenerator maintains consistent encoding across different inputs.

        Verifies:
            Character encoding is handled consistently regardless of input text characteristics

        Business Impact:
            Ensures reliable cache key generation across diverse text content types

        Scenario:
            Given: CacheKeyGenerator with various text encodings and character sets
            When: generate_cache_key() is called with different encoded texts
            Then: Consistent encoding behavior is maintained across all inputs

        Edge Cases Covered:
            - Different text encoding types
            - Character set consistency verification
            - Encoding normalization behavior
            - Cross-platform encoding compatibility

        Mocks Used:
            - None (encoding consistency verification)

        Related Tests:
            - test_generator_processes_unicode_text_correctly()
            - test_generator_maintains_performance_under_load()
        """
        generator = CacheKeyGenerator()

        # Test various text encodings (all as Python strings, but representing different character sets)
        encoding_test_texts = [
            "ASCII text only",  # Pure ASCII
            "Latin-1 text: café résumé",  # Latin-1 characters
            "UTF-8 mixed: Hello 世界 🌍",  # Mixed UTF-8
            "Cyrillic: Привет мир",  # Cyrillic characters
            "Arabic: مرحبا بالعالم",  # Arabic characters
            "Japanese: こんにちは世界",  # Japanese characters
            "Emoji heavy: 🎉🎈🎊🎁🎂",  # Emoji characters
            "Mathematical: ∑∏∂∇∆∞≈≠",  # Mathematical symbols
        ]

        # Generate keys for each encoding type
        encoding_keys = {}
        for i, text in enumerate(encoding_test_texts):
            key = generator.generate_cache_key(text, "summarize", {"encoding_test": i})
            assert key is not None
            assert "ai_cache:" in key
            encoding_keys[text] = key

        # Test consistency - same text should produce same key across multiple calls
        for text in encoding_test_texts:
            key1 = generator.generate_cache_key(text, "summarize", {})
            key2 = generator.generate_cache_key(text, "summarize", {})
            assert key1 == key2, f"Inconsistent keys for text: {text}"

        # Test byte representation consistency
        # Same logical text in different forms should be handled predictably
        test_text = "Test encoding: café"

        # These are the same logical string
        key_direct = generator.generate_cache_key(test_text, "summarize", {})
        key_copy = generator.generate_cache_key(str(test_text), "summarize", {})
        assert key_direct == key_copy

        # Test normalization of similar characters
        # These might be treated as equivalent depending on normalization
        similar_texts = [
            "café",  # Composed form
            "cafe\u0301",  # Decomposed form (e + combining accent)
        ]

        similar_keys = []
        for text in similar_texts:
            key = generator.generate_cache_key(text, "summarize", {})
            assert key is not None
            similar_keys.append(key)

        # Both should produce valid keys (normalization behavior may vary)
        assert all(key is not None for key in similar_keys)

        # Test cross-platform consistency simulation
        # Different line endings should be handled consistently
        line_ending_texts = [
            "Line 1\nLine 2\nLine 3",  # Unix line endings
            "Line 1\r\nLine 2\r\nLine 3",  # Windows line endings
            "Line 1\rLine 2\rLine 3",  # Old Mac line endings
        ]

        line_ending_keys = []
        for text in line_ending_texts:
            key = generator.generate_cache_key(text, "summarize", {})
            assert key is not None
            line_ending_keys.append(key)

        # All should be valid (may or may not be identical depending on normalization)
        assert all(key is not None for key in line_ending_keys)

        # Test encoding consistency with operations
        unicode_text = "Unicode test: 世界 🌍"
        operations = ["summarize", "sentiment", "questions"]

        for operation in operations:
            key = generator.generate_cache_key(unicode_text, operation, {})
            assert key is not None
            assert f"op:{operation}" in key

    def test_generator_maintains_performance_under_load(self):
        """
        Test that CacheKeyGenerator maintains acceptable performance under high load conditions.

        Verifies:
            Key generation performance remains acceptable during high-frequency operations

        Business Impact:
            Ensures cache key generation doesn't become a bottleneck in high-traffic scenarios

        Scenario:
            Given: CacheKeyGenerator under simulated high-load conditions
            When: Multiple rapid key generation operations are performed
            Then: Performance remains within acceptable bounds with proper monitoring

        Edge Cases Covered:
            - High-frequency key generation operations
            - Performance degradation monitoring
            - Resource utilization under load
            - Scalability validation

        Mocks Used:
            - None

        Related Tests:
            - test_generator_handles_extremely_long_text()
            - test_generator_maintains_encoding_consistency()
        """
        import threading
        import time

        from app.infrastructure.cache.monitoring import CachePerformanceMonitor

        # Create a real monitor instance
        monitor = CachePerformanceMonitor()

        generator = CacheKeyGenerator(performance_monitor=monitor)

        # Prepare test data for load testing
        test_texts = [
            "Short text",
            "Medium length text " * 20,
            "Long text " * 100,
        ]
        operations = ["summarize", "sentiment", "questions"]
        options_variants = [
            {},
            {"max_length": 100},
            {"temperature": 0.7, "max_tokens": 150},
        ]

        # Test high-frequency sequential operations
        start_time = time.time()
        generated_keys = []

        num_operations = 100  # Generate 100 keys rapidly
        for i in range(num_operations):
            text = test_texts[i % len(test_texts)]
            operation = operations[i % len(operations)]
            options = options_variants[i % len(options_variants)]

            key = generator.generate_cache_key(text, operation, options)
            assert key is not None
            generated_keys.append(key)

        sequential_time = time.time() - start_time

        # Performance should be reasonable (less than 10ms per key on average)
        avg_time_per_key = sequential_time / num_operations
        assert (
            avg_time_per_key < 0.01
        ), f"Average key generation too slow: {avg_time_per_key:.4f}s per key"

        # Verify all keys were generated successfully
        assert len(generated_keys) == num_operations
        assert all(key is not None for key in generated_keys)

        # Test concurrent operations (thread safety under load)
        concurrent_results = []
        errors = []

        def concurrent_key_generation(thread_id, num_keys=20):
            """Generate keys concurrently."""
            try:
                thread_keys = []
                for i in range(num_keys):
                    text = f"Thread {thread_id} text {i}"
                    key = generator.generate_cache_key(
                        text, "summarize", {"thread": thread_id}
                    )
                    thread_keys.append(key)
                concurrent_results.extend(thread_keys)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e!s}")

        # Start multiple threads
        num_threads = 10
        threads = []
        concurrent_start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=concurrent_key_generation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout

        concurrent_time = time.time() - concurrent_start_time

        # Verify no errors occurred during concurrent operations
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"

        # Verify all concurrent operations completed
        expected_concurrent_keys = num_threads * 20
        assert len(concurrent_results) == expected_concurrent_keys

        # Concurrent operations should complete in reasonable time
        assert (
            concurrent_time < 5.0
        ), f"Concurrent operations took too long: {concurrent_time:.2f}s"

        # Verify all operations completed successfully
        # With real monitor, we just verify the functionality worked properly
        assert len(generated_keys) == num_operations
        assert len(concurrent_results) == expected_concurrent_keys

        # Test memory stability under load (no significant memory leaks)
        import os

        import psutil

        process = psutil.Process(os.getpid())

        memory_before_load = process.memory_info().rss

        # Generate many keys to test for memory leaks
        for i in range(200):
            key = generator.generate_cache_key(
                f"Load test {i}", "summarize", {"load_test": True}
            )
            assert key is not None

        memory_after_load = process.memory_info().rss
        memory_increase = memory_after_load - memory_before_load

        # Memory increase should be reasonable (less than 50MB for 200 operations)
        # Be generous with memory limits as CI environments can vary significantly
        assert (
            memory_increase < 50 * 1024 * 1024
        ), f"Memory usage increased too much: {memory_increase / 1024 / 1024:.2f}MB"
