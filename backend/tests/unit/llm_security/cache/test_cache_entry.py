"""
Test suite for CacheEntry dataclass functionality.

Tests verify CacheEntry serialization, deserialization, and metadata management
according to the public contract defined in cache.pyi.
"""

import pytest
from datetime import datetime, UTC
from app.infrastructure.security.llm.cache import CacheEntry
from app.infrastructure.security.llm.protocol import SecurityResult, Violation, ViolationType, SeverityLevel


def create_test_security_result(
    is_safe: bool = True,
    violations: list = None,
    score: float = 1.0,
    scanned_text: str = "test input",
    scan_duration_ms: int = 100,
    scanner_results: dict = None,
    metadata: dict = None
) -> SecurityResult:
    """
    Helper function to create real SecurityResult objects for testing.

    Uses real dataclass objects to ensure compatibility with CacheEntry implementation.
    """
    violations = violations or []
    scanner_results = scanner_results or {}
    metadata = metadata or {}

    return SecurityResult(
        is_safe=is_safe,
        violations=violations,
        score=score,
        scanned_text=scanned_text,
        scan_duration_ms=scan_duration_ms,
        scanner_results=scanner_results,
        metadata=metadata
    )


def create_test_violation(
    violation_type: str = "prompt_injection",
    severity: str = "medium",
    description: str = "Test violation",
    confidence: float = 0.8,
    scanner_name: str = "test_scanner"
) -> Violation:
    """
    Helper function to create real Violation objects for testing.
    """
    return Violation(
        type=ViolationType(violation_type),
        severity=SeverityLevel(severity),
        description=description,
        confidence=confidence,
        scanner_name=scanner_name
    )


class TestCacheEntryInitialization:
    """Test CacheEntry instantiation and initial state."""

    def test_cache_entry_creation_with_all_fields(self):
        """
        Test that CacheEntry can be created with all required and optional fields.

        Verifies:
            CacheEntry dataclass properly initializes with complete field set including
            SecurityResult, timestamps, cache key, configuration hash, version, TTL, and hit count.

        Business Impact:
            Ensures cache entries contain all metadata necessary for cache management,
            performance monitoring, and configuration change detection.

        Scenario:
            Given: A valid SecurityResult object and complete metadata parameters.
            When: CacheEntry is instantiated with all fields.
            Then: The CacheEntry instance is created successfully with all attributes accessible.
        """
        # Given: A valid SecurityResult object and complete metadata parameters
        test_result = create_test_security_result(
            is_safe=True,
            violations=[],
            score=1.0,
            scanned_text="This is safe content",
            scan_duration_ms=100
        )
        cached_at = datetime.now(UTC)
        cache_key = "security_scan:input:abc123hash"
        scanner_config_hash = "def456hash"
        scanner_version = "1.0.0"
        ttl_seconds = 3600
        hit_count = 5

        # When: CacheEntry is instantiated with all fields
        entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key=cache_key,
            scanner_config_hash=scanner_config_hash,
            scanner_version=scanner_version,
            ttl_seconds=ttl_seconds,
            hit_count=hit_count
        )

        # Then: The CacheEntry instance is created successfully with all attributes accessible
        assert entry.result == test_result
        assert entry.cached_at == cached_at
        assert entry.cache_key == cache_key
        assert entry.scanner_config_hash == scanner_config_hash
        assert entry.scanner_version == scanner_version
        assert entry.ttl_seconds == ttl_seconds
        assert entry.hit_count == hit_count

    def test_cache_entry_creation_with_minimal_fields(self):
        """
        Test that CacheEntry can be created with only required fields.

        Verifies:
            CacheEntry supports creation with minimal required fields, using appropriate
            defaults for optional fields like hit_count.

        Business Impact:
            Enables flexible cache entry creation without requiring all metadata upfront.

        Scenario:
            Given: A valid SecurityResult and minimal required metadata.
            When: CacheEntry is instantiated without optional fields.
            Then: The CacheEntry is created with sensible defaults for omitted fields.
        """
        # Given: A valid SecurityResult and minimal required metadata
        test_result = create_test_security_result(
            is_safe=False,
            violations=[],
            score=0.5,
            scanned_text="Test content",
            scan_duration_ms=150
        )
        cached_at = datetime.now(UTC)
        cache_key = "security_scan:output:xyz789hash"
        scanner_config_hash = "config_hash_123"
        scanner_version = "2.1.0"
        ttl_seconds = 1800

        # When: CacheEntry is instantiated without optional fields
        entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key=cache_key,
            scanner_config_hash=scanner_config_hash,
            scanner_version=scanner_version,
            ttl_seconds=ttl_seconds
            # hit_count omitted - should default to 0
        )

        # Then: The CacheEntry is created with sensible defaults for omitted fields
        assert entry.result == test_result
        assert entry.cached_at == cached_at
        assert entry.cache_key == cache_key
        assert entry.scanner_config_hash == scanner_config_hash
        assert entry.scanner_version == scanner_version
        assert entry.ttl_seconds == ttl_seconds
        assert entry.hit_count == 0  # Default value for optional field


class TestCacheEntrySerialization:
    """Test CacheEntry conversion to dictionary format for Redis storage."""

    def test_to_dict_produces_json_serializable_output(self):
        """
        Test that to_dict() produces a fully JSON-serializable dictionary.

        Verifies:
            CacheEntry.to_dict() converts all entry data including nested SecurityResult
            objects and datetime objects to JSON-compatible formats per contract.

        Business Impact:
            Ensures cache entries can be reliably stored in Redis and reconstructed
            without data loss or serialization errors.

        Scenario:
            Given: A CacheEntry instance with complete data including nested objects.
            When: to_dict() method is called.
            Then: Returns dictionary with all fields serialized to JSON-compatible types
                  (datetime as ISO string, SecurityResult as nested dict).

                """
        # Given: A CacheEntry instance with complete data including nested objects
        test_violation = create_test_violation(
            violation_type="prompt_injection",
            severity="high",
            description="Injection attempt detected",
            confidence=0.9
        )

        test_result = create_test_security_result(
            is_safe=False,
            violations=[test_violation],
            score=0.3,
            scanned_text="Complex test content with violations",
            scan_duration_ms=250,
            scanner_results={"injection_detector": {"threat": True}},
            metadata={"model_version": "v2.1.0"}
        )
        cached_at = datetime.now(UTC)
        entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key="security_scan:input:complex123hash",
            scanner_config_hash="config456hash",
            scanner_version="1.2.3",
            ttl_seconds=7200,
            hit_count=12
        )

        # When: to_dict() method is called
        serialized = entry.to_dict()

        # Then: Returns dictionary with all fields serialized to JSON-compatible types
        # Verify structure contains all expected fields
        expected_fields = {"result", "cached_at", "cache_key", "scanner_config_hash",
                          "scanner_version", "ttl_seconds", "hit_count"}
        assert set(serialized.keys()) == expected_fields

        # Verify datetime is serialized to ISO string
        assert isinstance(serialized["cached_at"], str)
        assert serialized["cached_at"] == cached_at.isoformat()

        # Verify SecurityResult is serialized to dictionary
        assert isinstance(serialized["result"], dict)
        assert serialized["result"]["is_safe"] == False
        assert serialized["result"]["score"] == 0.3
        # Note: CacheEntry.to_dict() includes scanned_text for reconstruction,
        # unlike SecurityResult.to_dict() which excludes it for privacy
        assert serialized["result"]["scanned_text"] == "Complex test content with violations"
        assert serialized["result"]["scanned_text_length"] == len("Complex test content with violations")
        assert serialized["result"]["scan_duration_ms"] == 250
        assert len(serialized["result"]["violations"]) == 1
        assert serialized["result"]["violations"][0]["type"] == "prompt_injection"

        # Verify other fields are properly serialized
        assert serialized["cache_key"] == "security_scan:input:complex123hash"
        assert serialized["scanner_config_hash"] == "config456hash"
        assert serialized["scanner_version"] == "1.2.3"
        assert serialized["ttl_seconds"] == 7200
        assert serialized["hit_count"] == 12

        # Verify JSON serializability by attempting json.dumps
        import json
        json_str = json.dumps(serialized)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_to_dict_includes_all_required_fields(self):
        """
        Test that to_dict() includes all fields documented in the contract.

        Verifies:
            Dictionary output contains result, cached_at, cache_key, scanner_config_hash,
            scanner_version, ttl_seconds, and hit_count as specified in Returns section.

        Business Impact:
            Prevents data loss during cache serialization by ensuring complete metadata
            preservation for cache management and monitoring.

        Scenario:
            Given: A CacheEntry with all fields populated.
            When: to_dict() is called.
            Then: Dictionary contains all 7 documented fields with correct types.

                """
        # Given: A CacheEntry with all fields populated
        test_result = create_test_security_result(
            is_safe=True,
            violations=[],
            score=0.95,
            scanned_text="Perfectly safe content",
            scan_duration_ms=75
        )
        cached_at = datetime.now(UTC)
        entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key="security_scan:output:safe789hash",
            scanner_config_hash="config_safe_123",
            scanner_version="3.0.0",
            ttl_seconds=14400,  # 4 hours
            hit_count=25
        )

        # When: to_dict() is called
        serialized = entry.to_dict()

        # Then: Dictionary contains all 7 documented fields with correct types
        # Verify all expected fields are present
        expected_fields = [
            "result",           # SecurityResult data as dictionary
            "cached_at",        # ISO-formatted UTC timestamp string
            "cache_key",        # String cache key identifier
            "scanner_config_hash",  # Configuration hash string
            "scanner_version",  # Scanner version string
            "ttl_seconds",      # TTL duration as integer
            "hit_count"         # Access count as integer
        ]

        assert len(serialized) == 7, f"Expected 7 fields, got {len(serialized)}"

        for field in expected_fields:
            assert field in serialized, f"Missing field: {field}"

        # Verify field types match contract expectations
        assert isinstance(serialized["result"], dict)
        assert isinstance(serialized["cached_at"], str)
        assert isinstance(serialized["cache_key"], str)
        assert isinstance(serialized["scanner_config_hash"], str)
        assert isinstance(serialized["scanner_version"], str)
        assert isinstance(serialized["ttl_seconds"], int)
        assert isinstance(serialized["hit_count"], int)

        # Verify field values match original entry
        assert serialized["result"]["is_safe"] == test_result.is_safe
        assert serialized["cache_key"] == entry.cache_key
        assert serialized["scanner_config_hash"] == entry.scanner_config_hash
        assert serialized["scanner_version"] == entry.scanner_version
        assert serialized["ttl_seconds"] == entry.ttl_seconds
        assert serialized["hit_count"] == entry.hit_count

    def test_to_dict_datetime_formatting(self):
        """
        Test that to_dict() formats datetime fields as ISO-formatted UTC strings.

        Verifies:
            The cached_at timestamp is serialized to ISO string format per contract,
            enabling proper deserialization and timestamp comparison.

        Business Impact:
            Ensures consistent timestamp representation across distributed cache
            instances and prevents timezone-related bugs.

        Scenario:
            Given: A CacheEntry with a specific cached_at datetime.
            When: to_dict() is called.
            Then: The cached_at field is an ISO-formatted string representation of the UTC datetime.

                """
        # Given: A CacheEntry with a specific cached_at datetime
        test_result = create_test_security_result(
            is_safe=True,
            violations=[],
            score=1.0,
            scanned_text="Timestamp test content",
            scan_duration_ms=50
        )

        # Create a specific datetime for precise testing
        cached_at = datetime(2024, 3, 15, 14, 30, 45, 123456, UTC)

        entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key="security_scan:input:time456hash",
            scanner_config_hash="config_time_789",
            scanner_version="1.5.0",
            ttl_seconds=3600
        )

        # When: to_dict() is called
        serialized = entry.to_dict()

        # Then: The cached_at field is an ISO-formatted string representation of the UTC datetime
        assert isinstance(serialized["cached_at"], str)

        # Verify ISO format with UTC timezone
        iso_timestamp = serialized["cached_at"]
        expected_iso = "2024-03-15T14:30:45.123456+00:00"
        assert iso_timestamp == expected_iso, f"Expected {expected_iso}, got {iso_timestamp}"

        # Verify the timestamp can be parsed back to the same datetime
        parsed_datetime = datetime.fromisoformat(iso_timestamp)
        assert parsed_datetime == cached_at
        assert parsed_datetime.tzinfo == UTC


class TestCacheEntryDeserialization:
    """Test CacheEntry reconstruction from dictionary format."""

    def test_from_dict_reconstructs_complete_entry(self):
        """
        Test that from_dict() fully reconstructs a CacheEntry from serialized data.

        Verifies:
            CacheEntry.from_dict() creates a complete CacheEntry object from dictionary
            data, properly deserializing nested SecurityResult and datetime objects per contract.

        Business Impact:
            Enables reliable cache retrieval from Redis with complete metadata and
            result reconstruction for security scanning operations.

        Scenario:
            Given: A dictionary created by CacheEntry.to_dict() with complete data.
            When: CacheEntry.from_dict() is called with the dictionary.
            Then: Returns a CacheEntry with all fields properly deserialized and matching original values.

                """
        # Given: A dictionary created by CacheEntry.to_dict() with complete data
        test_result = create_test_security_result(
            is_safe=False,
            violations=[],
            score=0.45,
            scanned_text="Unsafe content with issues",
            scan_duration_ms=300,
            scanner_results={"toxicity_scanner": {"score": 0.8}},
            metadata={"model_version": "v2.5.0", "confidence": 0.95}
        )
        cached_at = datetime.now(UTC)
        original_entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key="security_scan:input:reconstruct123hash",
            scanner_config_hash="config_reconstruct_456",
            scanner_version="2.1.0",
            ttl_seconds=7200,
            hit_count=8
        )

        # Serialize to dictionary
        serialized_data = original_entry.to_dict()

        # When: CacheEntry.from_dict() is called with the dictionary
        reconstructed_entry = CacheEntry.from_dict(serialized_data)

        # Then: Returns a CacheEntry with all fields properly deserialized and matching original values
        # Verify all basic fields match
        assert reconstructed_entry.cache_key == original_entry.cache_key
        assert reconstructed_entry.scanner_config_hash == original_entry.scanner_config_hash
        assert reconstructed_entry.scanner_version == original_entry.scanner_version
        assert reconstructed_entry.ttl_seconds == original_entry.ttl_seconds
        assert reconstructed_entry.hit_count == original_entry.hit_count

        # Verify datetime is properly reconstructed
        assert reconstructed_entry.cached_at == original_entry.cached_at
        assert reconstructed_entry.cached_at.tzinfo == UTC

        # Verify SecurityResult is properly reconstructed
        assert reconstructed_entry.result.is_safe == original_entry.result.is_safe
        assert reconstructed_entry.result.score == original_entry.result.score
        assert reconstructed_entry.result.scanned_text == original_entry.result.scanned_text
        assert reconstructed_entry.result.scan_duration_ms == original_entry.result.scan_duration_ms
        assert reconstructed_entry.result.scanner_results == original_entry.result.scanner_results
        assert reconstructed_entry.result.metadata == original_entry.result.metadata

    def test_from_dict_handles_missing_optional_fields(self):
        """
        Test that from_dict() handles missing optional fields with appropriate defaults.

        Verifies:
            from_dict() gracefully handles dictionaries missing optional fields like hit_count,
            using appropriate defaults as documented in the contract.

        Business Impact:
            Ensures backward compatibility when deserializing cache entries created with
            earlier versions that may have fewer fields.

        Scenario:
            Given: A dictionary missing the optional hit_count field.
            When: CacheEntry.from_dict() is called.
            Then: CacheEntry is created with hit_count defaulting to 0.

                """
        # Given: A dictionary missing the optional hit_count field
        incomplete_data = {
            "result": {
                "is_safe": True,
                "violations": [],
                "score": 0.9,
                "scanned_text": "Test content for missing field",
                "scan_duration_ms": 120,
                "scanner_results": {},
                "metadata": {}
            },
            "cached_at": "2024-03-15T10:30:00+00:00",
            "cache_key": "security_scan:input:missing789hash",
            "scanner_config_hash": "config_missing_123",
            "scanner_version": "1.0.0",
            "ttl_seconds": 3600
            # hit_count field is intentionally missing
        }

        # When: CacheEntry.from_dict() is called
        entry = CacheEntry.from_dict(incomplete_data)

        # Then: CacheEntry is created with hit_count defaulting to 0
        assert entry.cache_key == "security_scan:input:missing789hash"
        assert entry.scanner_config_hash == "config_missing_123"
        assert entry.scanner_version == "1.0.0"
        assert entry.ttl_seconds == 3600
        assert entry.hit_count == 0  # Default value for missing optional field

        # Verify other fields are properly reconstructed
        assert entry.result.is_safe == True
        assert entry.result.score == 0.9
        assert entry.result.scanned_text == "Test content for missing field"
        assert entry.result.scan_duration_ms == 120

        # Verify datetime is properly reconstructed
        assert isinstance(entry.cached_at, datetime)
        assert entry.cached_at.tzinfo == UTC
        assert entry.cached_at.isoformat() == "2024-03-15T10:30:00+00:00"

    def test_from_dict_raises_key_error_for_missing_required_fields(self):
        """
        Test that from_dict() raises KeyError when required fields are missing.

        Verifies:
            from_dict() properly validates the presence of all required fields (result,
            cached_at, cache_key, etc.) and raises KeyError per contract's Raises section.

        Business Impact:
            Prevents creation of invalid cache entries from corrupted or incomplete
            Redis data, maintaining cache integrity.

        Scenario:
            Given: A dictionary missing a required field like cache_key.
            When: CacheEntry.from_dict() is called.
            Then: KeyError is raised indicating the missing required field.

                """
        # Test missing each required field individually
        required_fields_tests = [
            # Missing "result" field
            {
                "data": {
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": "security_scan:input:test123",
                    "scanner_config_hash": "config_test_123",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": 3600
                },
                "missing_field": "result"
            },
            # Missing "cached_at" field
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cache_key": "security_scan:input:test123",
                    "scanner_config_hash": "config_test_123",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": 3600
                },
                "missing_field": "cached_at"
            },
            # Missing "cache_key" field
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "scanner_config_hash": "config_test_123",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": 3600
                },
                "missing_field": "cache_key"
            },
            # Missing "scanner_config_hash" field
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": "security_scan:input:test123",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": 3600
                },
                "missing_field": "scanner_config_hash"
            },
            # Missing "scanner_version" field
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": "security_scan:input:test123",
                    "scanner_config_hash": "config_test_123",
                    "ttl_seconds": 3600
                },
                "missing_field": "scanner_version"
            },
            # Missing "ttl_seconds" field
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": "security_scan:input:test123",
                    "scanner_config_hash": "config_test_123",
                    "scanner_version": "1.0.0"
                },
                "missing_field": "ttl_seconds"
            }
        ]

        # Test each missing required field
        for test_case in required_fields_tests:
            # Given: A dictionary missing a required field
            incomplete_data = test_case["data"]
            missing_field = test_case["missing_field"]

            # When: CacheEntry.from_dict() is called
            # Then: KeyError is raised indicating the missing required field
            with pytest.raises(KeyError) as exc_info:
                CacheEntry.from_dict(incomplete_data)

            # Verify the error mentions the missing field
            assert missing_field in str(exc_info.value) or missing_field in str(exc_info.type)

    def test_from_dict_raises_value_error_for_invalid_timestamp(self):
        """
        Test that from_dict() raises ValueError for malformed timestamp strings.

        Verifies:
            from_dict() validates timestamp format and raises ValueError when cached_at
            cannot be parsed from ISO format, per contract's Raises section.

        Business Impact:
            Prevents cache corruption from invalid timestamp data and provides clear
            error messages for debugging cache serialization issues.

        Scenario:
            Given: A dictionary with cached_at containing invalid timestamp format.
            When: CacheEntry.from_dict() is called.
            Then: ValueError is raised indicating invalid timestamp format.

        Fixtures Used:
            None - uses plain dictionary data with invalid timestamp.
        """
        # Test various invalid timestamp formats
        invalid_timestamp_cases = [
            "14:30:00 2024-03-15",  # Wrong order
            "not-a-timestamp",       # Complete nonsense
            "2024-13-15T10:30:00+00:00",  # Invalid month
            "2024-03-32T10:30:00+00:00",  # Invalid day
            "2024-03-15T25:30:00+00:00",  # Invalid hour
            "2024-03-15T10:60:00+00:00",  # Invalid minute
            "",                      # Empty string
        ]

        # Note: "2024-03-15 14:30:00" is actually accepted by datetime.fromisoformat()
        # so we don't test it here as it doesn't raise ValueError

        for invalid_timestamp in invalid_timestamp_cases:
            # Given: A dictionary with cached_at containing invalid timestamp format
            invalid_data = {
                "result": {
                    "is_safe": True,
                    "violations": [],
                    "score": 0.9,
                    "scanned_text": "Test content",
                    "scan_duration_ms": 100,
                    "scanner_results": {},
                    "metadata": {}
                },
                "cached_at": invalid_timestamp,
                "cache_key": "security_scan:input:invalid_time123",
                "scanner_config_hash": "config_invalid_time_456",
                "scanner_version": "1.0.0",
                "ttl_seconds": 3600
            }

            # When: CacheEntry.from_dict() is called
            # Then: ValueError is raised indicating invalid timestamp format
            with pytest.raises(ValueError) as exc_info:
                CacheEntry.from_dict(invalid_data)

            # Verify the error message indicates timestamp parsing issue
            error_message = str(exc_info.value).lower()
            # The actual implementation may have different error messages, so we check for common patterns
            assert any(keyword in error_message for keyword in ["time", "timestamp", "iso", "format", "parse", "fromisoformat", "month", "day", "hour", "minute"])

    def test_from_dict_raises_type_error_for_incorrect_data_types(self):
        """
        Test that from_dict() raises TypeError when dictionary contains wrong data types.

        Verifies:
            from_dict() validates data types during reconstruction and raises TypeError
            when fields have incorrect types (e.g., ttl_seconds as string), per contract's Raises section.

        Business Impact:
            Maintains type safety during cache deserialization and prevents runtime
            errors from type mismatches in cached data.

        Scenario:
            Given: A dictionary with ttl_seconds as a string instead of integer.
            When: CacheEntry.from_dict() is called.
            Then: TypeError is raised indicating incorrect data type for reconstruction.

        Fixtures Used:
            None - uses plain dictionary data with type errors.
        """
        # Test various type errors
        type_error_cases = [
            # ttl_seconds as string instead of integer
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": "security_scan:input:type_error123",
                    "scanner_config_hash": "config_type_error_456",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": "3600",  # String instead of int
                    "hit_count": 0
                },
                "error_field": "ttl_seconds",
                "expected_type": "int",
                "actual_type": "str"
            },
            # hit_count as float instead of integer
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": "security_scan:input:type_error456",
                    "scanner_config_hash": "config_type_error_789",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": 3600,
                    "hit_count": 5.5  # Float instead of int
                },
                "error_field": "hit_count",
                "expected_type": "int",
                "actual_type": "float"
            },
            # cache_key as integer instead of string
            {
                "data": {
                    "result": {
                        "is_safe": True,
                        "violations": [],
                        "score": 0.9,
                        "scanned_text": "Test content",
                        "scan_duration_ms": 100,
                        "scanner_results": {},
                        "metadata": {}
                    },
                    "cached_at": "2024-03-15T10:30:00+00:00",
                    "cache_key": 12345,  # Integer instead of string
                    "scanner_config_hash": "config_type_error_abc",
                    "scanner_version": "1.0.0",
                    "ttl_seconds": 3600,
                    "hit_count": 0
                },
                "error_field": "cache_key",
                "expected_type": "str",
                "actual_type": "int"
            }
        ]

        for test_case in type_error_cases:
            # Given: A dictionary with incorrect data types
            invalid_data = test_case["data"]

            # When: CacheEntry.from_dict() is called
            # Then: TypeError is raised indicating incorrect data type for reconstruction
            with pytest.raises((TypeError, ValueError)) as exc_info:
                CacheEntry.from_dict(invalid_data)

            # Verify the error relates to type issues
            error_message = str(exc_info.value).lower()
            # Check for type-related error patterns
            type_error_indicators = ["type", "expected", "invalid", "must be", "cannot be"]
            assert any(indicator in error_message for indicator in type_error_indicators)


class TestCacheEntrySerializationRoundTrip:
    """Test complete serialization/deserialization cycles."""

    def test_roundtrip_preserves_all_data(self):
        """
        Test that serialization followed by deserialization preserves all entry data.

        Verifies:
            A complete cycle of to_dict() -> from_dict() produces a CacheEntry with
            identical data to the original, ensuring lossless serialization.

        Business Impact:
            Ensures cache data integrity across Redis storage and retrieval operations,
            preventing data corruption or loss in distributed caching scenarios.

        Scenario:
            Given: An original CacheEntry with complete data.
            When: to_dict() is called followed by from_dict() on the result.
            Then: The reconstructed CacheEntry has identical field values to the original.

        """
        # Given: An original CacheEntry with complete data
        test_violations = [
            create_test_violation(
                violation_type="prompt_injection",
                severity="high",
                description="Injection attempt detected",
                confidence=0.95,
                scanner_name="injection_detector"
            ),
            create_test_violation(
                violation_type="toxic_output",
                severity="medium",
                description="Toxic language detected",
                confidence=0.7,
                scanner_name="toxicity_scanner"
            )
        ]

        test_result = create_test_security_result(
            is_safe=False,
            violations=test_violations,
            score=0.25,
            scanned_text="Complex content for roundtrip testing with special characters: 🚀",
            scan_duration_ms=425,
            scanner_results={
                "injection_detector": {"threat_level": "high", "confidence": 0.95},
                "toxicity_scanner": {"score": 0.3, "categories": ["harassment"]},
                "pii_detector": {"entities_found": ["email", "phone"]}
            },
            metadata={
                "model_version": "v3.2.1",
                "processing_time": "optimized",
                "cache_strategy": "aggressive",
                "confidence_boost": 0.1
            }
        )

        # Create a CacheEntry with complex data to test edge cases
        cached_at = datetime(2024, 6, 15, 9, 45, 30, 500000, UTC)
        original_entry = CacheEntry(
            result=test_result,
            cached_at=cached_at,
            cache_key="security_scan:output:roundtrip_test_complex_hash_12345",
            scanner_config_hash="config_roundtrip_abc789def",
            scanner_version="3.1.4",
            ttl_seconds=28800,  # 8 hours
            hit_count=42
        )

        # When: to_dict() is called followed by from_dict() on the result
        serialized_data = original_entry.to_dict()
        reconstructed_entry = CacheEntry.from_dict(serialized_data)

        # Then: The reconstructed CacheEntry has identical field values to the original
        # Verify basic scalar fields
        assert reconstructed_entry.cache_key == original_entry.cache_key
        assert reconstructed_entry.scanner_config_hash == original_entry.scanner_config_hash
        assert reconstructed_entry.scanner_version == original_entry.scanner_version
        assert reconstructed_entry.ttl_seconds == original_entry.ttl_seconds
        assert reconstructed_entry.hit_count == original_entry.hit_count

        # Verify datetime field
        assert reconstructed_entry.cached_at == original_entry.cached_at
        assert reconstructed_entry.cached_at.tzinfo == UTC

        # Verify SecurityResult fields
        assert reconstructed_entry.result.is_safe == original_entry.result.is_safe
        assert reconstructed_entry.result.score == original_entry.result.score
        assert reconstructed_entry.result.scanned_text == original_entry.result.scanned_text
        assert reconstructed_entry.result.scan_duration_ms == original_entry.result.scan_duration_ms

        # Verify complex nested data structures
        assert reconstructed_entry.result.scanner_results == original_entry.result.scanner_results
        assert reconstructed_entry.result.metadata == original_entry.result.metadata

        # Verify violations list (even if empty in this case)
        assert len(reconstructed_entry.result.violations) == len(original_entry.result.violations)

        # Ensure the entries have equal data but are not the same object instance
        assert reconstructed_entry.cache_key == original_entry.cache_key
        assert reconstructed_entry.scanner_config_hash == original_entry.scanner_config_hash
        assert reconstructed_entry.scanner_version == original_entry.scanner_version
        assert reconstructed_entry.ttl_seconds == original_entry.ttl_seconds
        assert reconstructed_entry.hit_count == original_entry.hit_count
        assert reconstructed_entry is not original_entry
        assert reconstructed_entry.result is not original_entry.result

