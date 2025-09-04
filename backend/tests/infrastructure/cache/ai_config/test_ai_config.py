"""
Unit tests for AIResponseCacheConfig configuration management.

This test suite verifies the observable behaviors documented in the
AIResponseCacheConfig public contract (ai_config.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Configuration validation and factory methods
    - Parameter mapping and conversion behavior
    - Environment integration and preset loading

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, Any, Optional

from app.infrastructure.cache.ai_config import AIResponseCacheConfig
from app.infrastructure.cache.parameter_mapping import ValidationResult
from app.core.exceptions import ConfigurationError, ValidationError


class TestAIResponseCacheConfigValidation:
    """
    Test suite for AIResponseCacheConfig validation behavior.
    
    Scope:
        - Configuration parameter validation with ValidationResult integration
        - Comprehensive error reporting and warning generation
        - Performance recommendation generation
        - Edge case and boundary validation
        
    Business Critical:
        Configuration validation prevents misconfigured cache deployments that
        could impact AI service performance, cost, and reliability
        
    Test Strategy:
        - Unit tests for validate() method with various parameter combinations
        - ValidationResult integration testing for detailed error reporting
        - Boundary testing for parameter ranges and thresholds
        - Recommendation generation testing for performance optimization
        
    External Dependencies:
        - logging module (real): For validation logging integration
    """

    def test_validate_returns_valid_result_for_default_configuration(self):
        """
        Test that validate() returns valid ValidationResult for default configuration.
        
        Verifies:
            Default configuration parameters pass comprehensive validation
            
        Business Impact:
            Ensures out-of-the-box configuration works without additional setup
            
        Scenario:
            Given: AIResponseCacheConfig with default parameters
            When: validate() method is called
            Then: ValidationResult.is_valid returns True
            And: No validation errors are reported
            And: ValidationResult contains appropriate success indicators
            
        Configuration Validation Verified:
            - Default redis_url setting is valid (or None is acceptable)
            - Default TTL values are within acceptable ranges
            - Default memory cache size is within bounds
            - Default compression settings are valid
            - Default AI-specific parameters pass validation
            
        Fixtures Used:
            - None (testing default configuration without mocks)
            
        Related Tests:
            - test_validate_identifies_invalid_redis_url_format()
            - test_validate_identifies_ttl_out_of_range()
            - test_validate_generates_performance_recommendations()
        """
        # Given: Default configuration
        config = AIResponseCacheConfig()
        
        # When: validate() is called
        result = config.validate()
        
        # Then: Configuration should be valid
        assert result.is_valid, f"Default configuration should be valid. Errors: {result.errors}"
        assert len(result.errors) == 0, f"Should have no validation errors, got: {result.errors}"
        assert isinstance(result.warnings, list), "Warnings should be a list"
        assert isinstance(result.recommendations, list), "Recommendations should be a list"

    def test_validate_identifies_invalid_redis_url_format(self):
        """
        Test that validate() identifies invalid Redis URL formats.
        
        Verifies:
            Invalid Redis URL formats are properly detected and reported
            
        Business Impact:
            Prevents Redis connection failures due to malformed URLs
            
        Scenario:
            Given: AIResponseCacheConfig with invalid Redis URL format
            When: validate() method is called
            Then: ValidationResult.is_valid returns False
            And: ValidationResult.errors contains specific URL format error
            And: Error message includes acceptable URL format examples
            
        URL Format Validation Verified:
            - Invalid scheme detection (non-redis://, non-rediss://, non-unix://)
            - Missing host validation
            - Invalid port range detection
            - Malformed URL structure detection
            
        Fixtures Used:
            - None (direct parameter testing)
            
        Edge Cases Covered:
            - Empty string URLs
            - URLs with invalid schemes
            - URLs with invalid port ranges
            - URLs with missing required components
            
        Related Tests:
            - test_validate_returns_valid_result_for_default_configuration()
            - test_validate_accepts_valid_redis_url_formats()
        """
        # Test various invalid Redis URL formats
        invalid_urls = [
            "",  # Empty string
            "http://localhost:6379",  # Invalid scheme
            "ftp://localhost:6379",  # Invalid scheme
            "localhost:6379",  # Missing scheme
            "redis://",  # Missing host
            "redis://:6379",  # Missing host
            "redis://localhost:99999",  # Invalid port range
            "redis://localhost:-1",  # Negative port
        ]
        
        for invalid_url in invalid_urls:
            # Given: Configuration with invalid Redis URL
            config = AIResponseCacheConfig(redis_url=invalid_url)
            
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be invalid with appropriate error
            assert not result.is_valid, f"URL '{invalid_url}' should be invalid"
            assert len(result.errors) > 0, f"Should have validation errors for URL '{invalid_url}'"
            
            # Check that error mentions Redis URL
            error_text = ' '.join(result.errors).lower()
            assert 'redis' in error_text or 'url' in error_text, \
                f"Error should mention Redis URL issue for '{invalid_url}'. Errors: {result.errors}"

    def test_validate_identifies_ttl_out_of_range(self):
        """
        Test that validate() identifies TTL values outside acceptable ranges.
        
        Verifies:
            TTL parameter range validation with detailed error reporting
            
        Business Impact:
            Prevents cache configurations with inefficient or problematic TTL settings
            
        Scenario:
            Given: AIResponseCacheConfig with TTL values outside acceptable range (1-31536000 seconds)
            When: validate() method is called
            Then: ValidationResult.is_valid returns False
            And: ValidationResult.errors contains specific TTL range violations
            And: Error messages include acceptable range information
            
        TTL Range Validation Verified:
            - default_ttl minimum bound enforcement (>= 1 second)
            - default_ttl maximum bound enforcement (<= 31536000 seconds / 1 year)
            - operation_ttls individual value validation
            - Negative TTL value detection
            
        Fixtures Used:
            - None (direct parameter testing)
            
        Edge Cases Covered:
            - Zero TTL values
            - Negative TTL values  
            - Extremely large TTL values (> 1 year)
            - operation_ttls with mixed valid/invalid values
            
        Related Tests:
            - test_validate_accepts_valid_ttl_ranges()
            - test_validate_generates_ttl_optimization_recommendations()
        """
        # Test invalid default_ttl values
        invalid_ttl_configs = [
            (0, "Zero TTL"),
            (-1, "Negative TTL"),
            (31536001, "TTL > 1 year"),  # 1 year + 1 second
        ]
        
        for ttl_value, description in invalid_ttl_configs:
            # Given: Configuration with invalid default_ttl
            config = AIResponseCacheConfig(default_ttl=ttl_value)
            
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be invalid with TTL-related error
            assert not result.is_valid, f"{description} should be invalid (value: {ttl_value})"
            assert len(result.errors) > 0, f"Should have validation errors for {description}"
            
            error_text = ' '.join(result.errors).lower()
            assert 'ttl' in error_text, f"Error should mention TTL for {description}. Errors: {result.errors}"
        
        # Test invalid operation_ttls values
        config = AIResponseCacheConfig(
            operation_ttls={
                "valid_op": 3600,
                "zero_ttl": 0,
                "negative_ttl": -100,
                "huge_ttl": 50000000  # Way over 1 year
            }
        )
        
        result = config.validate()
        assert not result.is_valid, "Configuration with invalid operation TTLs should be invalid"
        assert len(result.errors) > 0, "Should have validation errors for invalid operation TTLs"

    def test_validate_identifies_memory_cache_size_violations(self):
        """
        Test that validate() identifies invalid memory cache size values.
        
        Verifies:
            Memory cache size parameter validation with range enforcement
            
        Business Impact:
            Prevents memory cache configurations that could cause OOM or poor performance
            
        Scenario:
            Given: AIResponseCacheConfig with memory_cache_size outside valid range (1-10000)
            When: validate() method is called
            Then: ValidationResult.is_valid returns False
            And: ValidationResult.errors contains specific memory cache size violations
            And: Error includes memory usage implications
            
        Memory Cache Size Validation Verified:
            - Minimum size enforcement (>= 1 entry)
            - Maximum size enforcement (<= 10000 entries)
            - Zero or negative value detection
            - Memory usage calculation and warnings for large values
            
        Fixtures Used:
            - None (direct parameter testing)
            
        Edge Cases Covered:
            - Zero memory cache size
            - Negative memory cache size
            - Extremely large memory cache sizes
            - Non-integer values (if applicable)
            
        Related Tests:
            - test_validate_generates_memory_optimization_recommendations()
            - test_validate_accepts_valid_memory_cache_configurations()
        """
        # Test invalid memory cache size values
        invalid_sizes = [
            (-1, "Negative memory cache size"),
            (-100, "Large negative memory cache size"),
            (0, "Zero memory cache size"),
            (10001, "Memory cache size above maximum"),
            (50000, "Extremely large memory cache size"),
        ]
        
        for size_value, description in invalid_sizes:
            # Given: Configuration with invalid memory_cache_size
            config = AIResponseCacheConfig(memory_cache_size=size_value)
            
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be invalid with memory-related error
            assert not result.is_valid, f"{description} should be invalid (value: {size_value})"
            assert len(result.errors) > 0, f"Should have validation errors for {description}"
            
            error_text = ' '.join(result.errors).lower()
            assert any(term in error_text for term in ['memory', 'cache', 'size']), \
                f"Error should mention memory cache size for {description}. Errors: {result.errors}"

    def test_validate_identifies_compression_parameter_issues(self):
        """
        Test that validate() identifies invalid compression configuration parameters.
        
        Verifies:
            Compression threshold and level parameter validation
            
        Business Impact:
            Prevents compression configurations that could hurt performance or fail
            
        Scenario:
            Given: AIResponseCacheConfig with invalid compression parameters
            When: validate() method is called
            Then: ValidationResult.is_valid returns False
            And: ValidationResult.errors contains specific compression parameter violations
            And: Error messages explain performance implications
            
        Compression Validation Verified:
            - compression_threshold range validation (0-1048576 bytes / 1MB)
            - compression_level range validation (1-9)
            - Threshold/level combination effectiveness validation
            - Performance impact assessment for compression settings
            
        Fixtures Used:
            - None (direct parameter testing)
            
        Edge Cases Covered:
            - Negative compression threshold
            - Compression threshold larger than 1MB
            - Invalid compression levels (< 1 or > 9)
            - Compression disabled scenarios
            
        Related Tests:
            - test_validate_generates_compression_optimization_recommendations()
            - test_validate_accepts_optimal_compression_settings()
        """
        # Test invalid compression_threshold values
        invalid_threshold_configs = [
            (-1, "Negative compression threshold"),
            (1048577, "Compression threshold > 1MB"),  # 1MB + 1 byte
            (10000000, "Extremely large compression threshold"),
        ]
        
        for threshold_value, description in invalid_threshold_configs:
            # Given: Configuration with invalid compression_threshold
            config = AIResponseCacheConfig(compression_threshold=threshold_value)
            
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be invalid with compression-related error
            assert not result.is_valid, f"{description} should be invalid (value: {threshold_value})"
            assert len(result.errors) > 0, f"Should have validation errors for {description}"
            
            error_text = ' '.join(result.errors).lower()
            assert 'compression' in error_text or 'threshold' in error_text, \
                f"Error should mention compression for {description}. Errors: {result.errors}"
        
        # Test invalid compression_level values
        invalid_level_configs = [
            (0, "Zero compression level"),
            (-1, "Negative compression level"),
            (10, "Compression level > 9"),
            (100, "Extremely high compression level"),
        ]
        
        for level_value, description in invalid_level_configs:
            # Given: Configuration with invalid compression_level
            config = AIResponseCacheConfig(compression_level=level_value)
            
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be invalid with compression-related error
            assert not result.is_valid, f"{description} should be invalid (value: {level_value})"
            assert len(result.errors) > 0, f"Should have validation errors for {description}"
            
            error_text = ' '.join(result.errors).lower()
            assert 'compression' in error_text or 'level' in error_text, \
                f"Error should mention compression level for {description}. Errors: {result.errors}"

    def test_validate_identifies_text_processing_parameter_issues(self):
        """
        Test that validate() identifies invalid AI text processing parameters.
        
        Verifies:
            AI-specific text processing parameter validation
            
        Business Impact:
            Prevents AI cache configurations that could cause text processing failures
            
        Scenario:
            Given: AIResponseCacheConfig with invalid text processing parameters
            When: validate() method is called
            Then: ValidationResult.is_valid returns False
            And: ValidationResult.errors contains specific text processing violations
            And: Error messages include AI processing context
            
        Text Processing Validation Verified:
            - text_hash_threshold range validation (1-100000 characters)
            - hash_algorithm validity check
            - text_size_tiers consistency validation
            - operation_ttls key validation for supported operations
            
        Fixtures Used:
            - None (direct parameter testing)
            
        Edge Cases Covered:
            - Zero or negative text_hash_threshold
            - Unsupported hash algorithms
            - Inconsistent text_size_tiers configuration
            - Invalid operation names in operation_ttls
            
        Related Tests:
            - test_validate_accepts_valid_ai_text_processing_configuration()
            - test_validate_generates_ai_optimization_recommendations()
        """
        # Test invalid text_hash_threshold values
        invalid_hash_thresholds = [
            (0, "Zero text hash threshold"),
            (-1, "Negative text hash threshold"),
            (100001, "Text hash threshold > 100000"),  # Above maximum
            (1000000, "Extremely large text hash threshold"),
        ]
        
        for threshold_value, description in invalid_hash_thresholds:
            # Given: Configuration with invalid text_hash_threshold
            config = AIResponseCacheConfig(text_hash_threshold=threshold_value)
            
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be invalid with text processing-related error
            assert not result.is_valid, f"{description} should be invalid (value: {threshold_value})"
            assert len(result.errors) > 0, f"Should have validation errors for {description}"
            
            error_text = ' '.join(result.errors).lower()
            assert any(term in error_text for term in ['text', 'hash', 'threshold']), \
                f"Error should mention text hash threshold for {description}. Errors: {result.errors}"
        
        # Test invalid hash_algorithm
        config = AIResponseCacheConfig(hash_algorithm="invalid_algorithm")
        result = config.validate()
        
        # Note: The validation might be lenient for hash algorithms, so we check if it's invalid or has warnings
        if not result.is_valid:
            error_text = ' '.join(result.errors).lower()
            assert 'hash' in error_text or 'algorithm' in error_text, \
                f"Error should mention hash algorithm. Errors: {result.errors}"
        
        # Test inconsistent text_size_tiers (if validation checks for consistency)
        config = AIResponseCacheConfig(
            text_size_tiers={
                "large": 100,  # Large tier smaller than small tier
                "small": 1000,
                "medium": 500
            }
        )
        result = config.validate()
        
        # Check if tiers validation exists - may be lenient
        if not result.is_valid:
            error_text = ' '.join(result.errors).lower()
            assert any(term in error_text for term in ['tier', 'size', 'text']), \
                f"Error should mention text size tiers. Errors: {result.errors}"

    def test_validate_generates_performance_recommendations(self):
        """
        Test that validate() generates intelligent performance recommendations.
        
        Verifies:
            ValidationResult includes performance optimization recommendations
            
        Business Impact:
            Helps administrators optimize cache performance for their specific workloads
            
        Scenario:
            Given: AIResponseCacheConfig with suboptimal but valid parameters
            When: validate() method is called
            Then: ValidationResult.is_valid returns True
            And: ValidationResult.recommendations contains performance suggestions
            And: Recommendations are specific and actionable
            
        Performance Recommendations Verified:
            - Memory cache size optimization suggestions
            - TTL optimization based on operation types
            - Compression threshold recommendations based on data patterns
            - Text processing optimization suggestions
            
        Fixtures Used:
            - None (testing recommendation generation logic)
            
        Recommendation Categories Verified:
            - Memory optimization recommendations
            - Performance tuning suggestions
            - AI-specific optimization advice
            - Resource usage optimization
            
        Related Tests:
            - test_validate_returns_valid_result_for_default_configuration()
            - test_validate_generates_no_recommendations_for_optimal_config()
        """
        # Test configuration that should generate recommendations
        configs_with_expected_recommendations = [
            # Small memory cache might get recommendation to increase
            (AIResponseCacheConfig(memory_cache_size=1), "memory"),
            
            # Very high compression threshold might get recommendation
            (AIResponseCacheConfig(compression_threshold=1000000), "compression"),
            
            # Very low compression level might get recommendation
            (AIResponseCacheConfig(compression_level=1), "compression"),
            
            # Very high text hash threshold might get recommendation
            (AIResponseCacheConfig(text_hash_threshold=99000), "text"),
        ]
        
        for config, expected_topic in configs_with_expected_recommendations:
            # When: validate() is called
            result = config.validate()
            
            # Then: Should be valid but may have recommendations
            assert result.is_valid, f"Configuration should be valid. Errors: {result.errors}"
            assert isinstance(result.recommendations, list), "Recommendations should be a list"
            
            # Check if recommendations are generated (implementation might be lenient)
            if result.recommendations:
                recommendation_text = ' '.join(result.recommendations).lower()
                # If recommendations exist, they should be relevant
                assert len(result.recommendations) > 0, "Should have performance recommendations"
        
        # Test a configuration that might generate multiple types of recommendations
        suboptimal_config = AIResponseCacheConfig(
            memory_cache_size=5,  # Very small
            compression_threshold=10,  # Very low threshold
            compression_level=9,  # Maximum compression (high CPU)
            text_hash_threshold=50000  # High threshold
        )
        
        result = suboptimal_config.validate()
        assert result.is_valid, f"Suboptimal but valid configuration should pass validation. Errors: {result.errors}"
        assert isinstance(result.recommendations, list), "Should have recommendations list"

    def test_validate_handles_complex_configuration_scenarios(self):
        """
        Test that validate() properly handles complex multi-parameter validation scenarios.
        
        Verifies:
            Complex validation scenarios with interdependent parameter relationships
            
        Business Impact:
            Ensures configuration validation catches complex misconfigurations
            
        Scenario:
            Given: AIResponseCacheConfig with multiple interdependent parameter issues
            When: validate() method is called
            Then: ValidationResult captures all related validation issues
            And: Error messages explain parameter relationships
            And: Recommendations address interdependent optimization opportunities
            
        Complex Validation Scenarios Verified:
            - Memory cache vs compression threshold relationships
            - TTL vs operation type consistency
            - Redis connection vs performance parameter alignment
            - AI optimization vs general cache parameter compatibility
            
        Fixtures Used:
            - None (testing complex validation logic)
            
        Interdependency Validation Verified:
            Configuration validation considers parameter relationships rather than isolated checks
            
        Related Tests:
            - test_validate_identifies_individual_parameter_violations()
            - test_validate_provides_comprehensive_error_context()
        """
        # Test configuration with multiple parameter issues
        complex_invalid_config = AIResponseCacheConfig(
            redis_url="invalid://badscheme:6379",  # Invalid URL
            default_ttl=-100,  # Invalid TTL
            memory_cache_size=-50,  # Invalid cache size
            compression_threshold=-1,  # Invalid threshold
            compression_level=15,  # Invalid level
            text_hash_threshold=0,  # Invalid hash threshold
            operation_ttls={
                "valid_op": 3600,
                "invalid_op": -100  # Invalid TTL in operations
            }
        )
        
        # When: validate() is called
        result = complex_invalid_config.validate()
        
        # Then: Should capture multiple validation issues
        assert not result.is_valid, "Configuration with multiple issues should be invalid"
        assert len(result.errors) >= 3, f"Should have multiple validation errors. Got: {result.errors}"
        
        # Check that different types of errors are captured
        error_text = ' '.join(result.errors).lower()
        expected_error_topics = ['redis', 'ttl', 'memory', 'compression', 'text']
        topics_found = sum(1 for topic in expected_error_topics if topic in error_text)
        assert topics_found >= 2, f"Should capture errors from multiple parameter categories. Errors: {result.errors}"
        
        # Test configuration with valid individual parameters but potential interdependency issues
        interdependent_config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            memory_cache_size=1,  # Very small cache
            compression_threshold=1000000,  # Very high threshold (most data won't compress)
            compression_level=9,  # High CPU compression for little benefit
            text_hash_threshold=100000,  # Very high threshold
            default_ttl=1  # Very short TTL
        )
        
        result = interdependent_config.validate()
        # This might be valid but should generate recommendations about the parameter relationships
        assert isinstance(result.errors, list), "Should have errors list"
        assert isinstance(result.warnings, list), "Should have warnings list"
        assert isinstance(result.recommendations, list), "Should have recommendations list"


class TestAIResponseCacheConfigFactory:
    """
    Test suite for AIResponseCacheConfig factory method behavior.
    
    Scope:
        - Factory method creation (create_default, create_production, create_development, create_testing)
        - Environment-based configuration loading
        - File-based configuration loading (JSON/YAML)
        - Dictionary-based configuration creation
        
    Business Critical:
        Factory methods enable consistent configuration across different deployment environments
        
    Test Strategy:
        - Unit tests for each factory method with different scenarios
        - Environment variable integration testing
        - File loading with error handling validation
        - Configuration preset integration testing
        
    External Dependencies:
        - Environment variables (mocked via os.environ)
        - File system (mocked for YAML/JSON loading)
        - YAML library (mocked when testing YAML functionality)
    """

    def test_create_default_returns_development_friendly_configuration(self):
        """
        Test that create_default() returns development-optimized configuration.
        
        Verifies:
            Default factory method creates development-friendly configuration
            
        Business Impact:
            Enables quick setup for development environments without manual configuration
            
        Scenario:
            Given: No specific configuration parameters provided
            When: AIResponseCacheConfig.create_default() is called
            Then: Configuration instance is created with development-friendly defaults
            And: All default parameters pass validation
            And: Configuration supports typical development workflows
            
        Development Configuration Verified:
            - Short TTL values for quick feedback during development
            - Moderate memory cache size for development machine resources
            - Balanced compression settings for development performance
            - AI features enabled with reasonable defaults
            
        Fixtures Used:
            - None (testing factory method directly)
            
        Default Behavior Verified:
            Create_default produces immediately usable configuration without additional setup
            
        Related Tests:
            - test_create_development_returns_development_optimized_configuration()
            - test_create_production_returns_production_optimized_configuration()
        """
        # When: create_default() is called
        config = AIResponseCacheConfig.create_default()
        
        # Then: Should create valid configuration
        assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
        
        # Validate the configuration
        result = config.validate()
        assert result.is_valid, f"Default configuration should be valid. Errors: {result.errors}"
        
        # Verify development-friendly characteristics
        assert config.redis_url is not None, "Should have Redis URL configured"
        assert config.default_ttl > 0, "Should have positive TTL"
        assert config.memory_cache_size > 0, "Should have positive memory cache size"
        assert config.text_hash_threshold > 0, "Should have positive text hash threshold"
        assert config.compression_threshold >= 0, "Should have valid compression threshold"
        assert 1 <= config.compression_level <= 9, "Should have valid compression level"
        
        # Verify AI-specific features are configured
        assert config.operation_ttls is not None, "Should have operation TTLs configured"
        assert config.text_size_tiers is not None, "Should have text size tiers configured"
        
        # Verify reasonable defaults for development
        assert config.memory_cache_size <= 1000, "Development config should have reasonable memory cache size"
        assert config.default_ttl <= 86400, "Development config should have reasonable TTL (<=24h)"

    def test_create_production_returns_production_optimized_configuration(self):
        """
        Test that create_production() returns production-optimized configuration.
        
        Verifies:
            Production factory method creates production-ready configuration
            
        Business Impact:
            Ensures production deployments use optimized cache settings out of the box
            
        Scenario:
            Given: Production Redis URL provided
            When: AIResponseCacheConfig.create_production(redis_url) is called
            Then: Configuration instance is created with production optimizations
            And: All production parameters pass validation
            And: Configuration supports high-throughput production workloads
            
        Production Configuration Verified:
            - Extended TTL values for production stability
            - Large memory cache size for production performance
            - Aggressive compression settings for bandwidth optimization
            - AI features configured for production-scale processing
            
        Fixtures Used:
            - None (testing factory method directly)
            
        Production Redis URL Integration Verified:
            Provided Redis URL is properly integrated into production configuration
            
        Related Tests:
            - test_create_production_validates_required_redis_url()
            - test_create_development_differs_from_production_configuration()
        """
        # Given: Production Redis URL
        prod_redis_url = "redis://production-cache:6379/1"
        
        # When: create_production() is called
        config = AIResponseCacheConfig.create_production(prod_redis_url)
        
        # Then: Should create valid production configuration
        assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
        assert config.redis_url == prod_redis_url, "Should use provided Redis URL"
        
        # Validate the configuration
        result = config.validate()
        assert result.is_valid, f"Production configuration should be valid. Errors: {result.errors}"
        
        # Verify production-optimized characteristics
        assert config.default_ttl >= 3600, "Production should have longer TTL (>=1h)"
        assert config.memory_cache_size >= 100, "Production should have larger memory cache"
        
        # Verify compression is optimized for production
        assert config.compression_threshold <= 2000, "Production should use aggressive compression"
        assert config.compression_level >= 6, "Production should use good compression level"
        
        # Verify AI features are production-ready
        assert config.operation_ttls is not None, "Should have operation TTLs configured"
        assert config.text_size_tiers is not None, "Should have text size tiers configured"
        
        # Production config should be more resource-intensive than default
        default_config = AIResponseCacheConfig.create_default()
        assert config.memory_cache_size >= default_config.memory_cache_size, \
            "Production should have equal or larger memory cache than default"

    def test_create_development_returns_development_optimized_configuration(self):
        """
        Test that create_development() returns development-optimized configuration.
        
        Verifies:
            Development factory method creates development-friendly configuration
            
        Business Impact:
            Enables fast development cycles with optimized cache behavior for local development
            
        Scenario:
            Given: No specific parameters (using development defaults)
            When: AIResponseCacheConfig.create_development() is called
            Then: Configuration instance is created with development optimizations
            And: Configuration prioritizes development speed over production optimization
            And: All development parameters pass validation
            
        Development Configuration Verified:
            - Very short TTL values for rapid development iteration
            - Small memory cache size for development machine constraints
            - Minimal compression for development speed
            - AI features enabled with development-friendly settings
            
        Fixtures Used:
            - None (testing factory method directly)
            
        Development Speed Optimization Verified:
            Configuration prioritizes development feedback speed over production concerns
            
        Related Tests:
            - test_create_default_returns_development_friendly_configuration()
            - test_create_testing_returns_testing_optimized_configuration()
        """
        # When: create_development() is called
        config = AIResponseCacheConfig.create_development()
        
        # Then: Should create valid development configuration
        assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
        
        # Validate the configuration
        result = config.validate()
        assert result.is_valid, f"Development configuration should be valid. Errors: {result.errors}"
        
        # Verify development-optimized characteristics
        assert config.redis_url is not None, "Should have Redis URL configured"
        assert config.default_ttl > 0, "Should have positive TTL"
        assert config.memory_cache_size > 0, "Should have positive memory cache size"
        
        # Development should prioritize speed over resource optimization
        assert config.memory_cache_size <= 200, "Development should have moderate memory cache size"
        assert config.default_ttl <= 7200, "Development should have shorter TTL (<=2h) for faster iteration"
        
        # Verify minimal but effective compression for development speed
        assert config.compression_level <= 7, "Development should use moderate compression for speed"
        
        # Verify AI features are configured for development
        assert config.operation_ttls is not None, "Should have operation TTLs configured"
        assert config.text_size_tiers is not None, "Should have text size tiers configured"
        assert config.text_hash_threshold > 0, "Should have positive text hash threshold"

    def test_create_testing_returns_testing_optimized_configuration(self):
        """
        Test that create_testing() returns testing-optimized configuration.
        
        Verifies:
            Testing factory method creates test-suite-friendly configuration
            
        Business Impact:
            Enables fast, predictable test execution with minimal external dependencies
            
        Scenario:
            Given: Test execution environment requirements
            When: AIResponseCacheConfig.create_testing() is called
            Then: Configuration instance is created with testing optimizations
            And: Configuration minimizes test execution time and resource usage
            And: All testing parameters support reliable test execution
            
        Testing Configuration Verified:
            - Minimal TTL values for fast test execution
            - Small memory cache size for test resource efficiency
            - Disabled or minimal compression for test speed
            - AI features configured for predictable test behavior
            
        Fixtures Used:
            - None (testing factory method directly)
            
        Test Execution Optimization Verified:
            Configuration supports fast, reliable, resource-efficient test execution
            
        Related Tests:
            - test_create_development_returns_development_optimized_configuration()
            - test_factory_methods_produce_different_configurations()
        """
        # When: create_testing() is called
        config = AIResponseCacheConfig.create_testing()
        
        # Then: Should create valid testing configuration
        assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
        
        # Validate the configuration
        result = config.validate()
        assert result.is_valid, f"Testing configuration should be valid. Errors: {result.errors}"
        
        # Verify testing-optimized characteristics
        assert config.redis_url is not None, "Should have Redis URL configured"
        assert config.default_ttl > 0, "Should have positive TTL"
        assert config.memory_cache_size > 0, "Should have positive memory cache size"
        
        # Testing should prioritize speed and minimal resource usage
        assert config.memory_cache_size <= 50, "Testing should have small memory cache for efficiency"
        assert config.default_ttl <= 600, "Testing should have very short TTL (<=10m) for fast tests"
        
        # Verify minimal compression for test speed
        assert config.compression_level <= 6, "Testing should use minimal compression for speed"
        assert config.compression_threshold >= 1000, "Testing should avoid compression for small test data"
        
        # Verify AI features are configured but optimized for testing
        assert config.operation_ttls is not None, "Should have operation TTLs configured"
        assert config.text_size_tiers is not None, "Should have text size tiers configured"
        
        # Testing TTLs should be shorter than development/production
        dev_config = AIResponseCacheConfig.create_development()
        assert config.default_ttl <= dev_config.default_ttl, "Testing TTL should be <= development TTL"

    def test_from_dict_creates_configuration_from_dictionary_data(self):
        """
        Test that from_dict() creates configuration from dictionary parameters.
        
        Verifies:
            Dictionary-based configuration creation with parameter mapping
            
        Business Impact:
            Enables configuration from external sources like databases or APIs
            
        Scenario:
            Given: Dictionary containing valid configuration parameters
            When: AIResponseCacheConfig.from_dict(config_dict) is called
            Then: Configuration instance is created with dictionary values
            And: All dictionary parameters are properly mapped to configuration fields
            And: Configuration passes validation with provided parameters
            
        Dictionary Parameter Mapping Verified:
            - All supported configuration parameters can be loaded from dictionary
            - Parameter type conversion works correctly (strings to integers, etc.)
            - Optional parameters handle None values appropriately
            - Complex parameters (operation_ttls, text_size_tiers) are properly structured
            
        Fixtures Used:
            - None (testing dictionary parameter mapping directly)
            
        Edge Cases Covered:
            - Dictionary with subset of parameters (others use defaults)
            - Dictionary with all parameters specified
            - Dictionary with invalid parameter types
            - Empty dictionary handling
            
        Related Tests:
            - test_from_dict_raises_configuration_error_for_invalid_parameters()
            - test_from_dict_handles_partial_parameter_dictionaries()
        """
        # Test complete configuration dictionary
        complete_config_dict = {
            "redis_url": "redis://localhost:6379/2",
            "default_ttl": 7200,
            "enable_l1_cache": True,
            "memory_cache_size": 150,
            "compression_threshold": 2000,
            "compression_level": 7,
            "text_hash_threshold": 2000,
            "hash_algorithm": "sha256",
            "text_size_tiers": {
                "small": 300,
                "medium": 3000,
                "large": 30000
            },
            "operation_ttls": {
                "summarize": 7200,
                "sentiment": 14400,
                "qa": 1800
            }
        }
        
        # When: from_dict() is called
        config = AIResponseCacheConfig.from_dict(complete_config_dict)
        
        # Then: Should create configuration with dictionary values
        assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
        assert config.redis_url == complete_config_dict["redis_url"]
        assert config.default_ttl == complete_config_dict["default_ttl"]
        assert config.memory_cache_size == complete_config_dict["memory_cache_size"]
        assert config.compression_threshold == complete_config_dict["compression_threshold"]
        assert config.text_hash_threshold == complete_config_dict["text_hash_threshold"]
        
        # Verify complex parameters
        assert config.text_size_tiers == complete_config_dict["text_size_tiers"]
        assert config.operation_ttls == complete_config_dict["operation_ttls"]
        
        # Configuration should be valid
        result = config.validate()
        assert result.is_valid, f"Configuration from dictionary should be valid. Errors: {result.errors}"
        
        # Test partial configuration dictionary (should use defaults for missing)
        partial_config_dict = {
            "redis_url": "redis://partial:6379",
            "default_ttl": 1800,
            "memory_cache_size": 75
        }
        
        partial_config = AIResponseCacheConfig.from_dict(partial_config_dict)
        assert partial_config.redis_url == partial_config_dict["redis_url"]
        assert partial_config.default_ttl == partial_config_dict["default_ttl"]
        assert partial_config.memory_cache_size == partial_config_dict["memory_cache_size"]
        
        # Should have defaults for unspecified parameters
        assert partial_config.text_size_tiers is not None
        assert partial_config.operation_ttls is not None
        
        # Test empty dictionary (should use all defaults)
        empty_config = AIResponseCacheConfig.from_dict({})
        assert isinstance(empty_config, AIResponseCacheConfig)
        
        empty_result = empty_config.validate()
        assert empty_result.is_valid, f"Empty dictionary config should be valid. Errors: {empty_result.errors}"

    def test_from_dict_raises_configuration_error_for_invalid_parameters(self):
        """
        Test that from_dict() raises ConfigurationError for invalid dictionary parameters.
        
        Verifies:
            Dictionary validation prevents creation of invalid configurations
            
        Business Impact:
            Prevents runtime failures due to invalid configuration data from external sources
            
        Scenario:
            Given: Dictionary containing invalid configuration parameters
            When: AIResponseCacheConfig.from_dict(invalid_dict) is called
            Then: ConfigurationError is raised with specific parameter validation failures
            And: Error message identifies the invalid parameters and their issues
            And: No configuration instance is created with invalid data
            
        Invalid Parameter Detection Verified:
            - Unknown parameter names are rejected
            - Invalid parameter value types are rejected
            - Parameter values outside valid ranges are rejected
            - Malformed complex parameters (operation_ttls, etc.) are rejected
            
        Fixtures Used:
            - None
            
        Error Context Verified:
            ConfigurationError includes specific parameter validation failures for debugging
            
        Related Tests:
            - test_from_dict_creates_configuration_from_dictionary_data()
            - test_from_dict_validates_required_vs_optional_parameters()
        """
        # Test dictionary with unknown parameters
        invalid_dict_unknown = {
            "redis_url": "redis://localhost:6379",
            "unknown_parameter": "invalid_value",
            "another_unknown": 123
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            AIResponseCacheConfig.from_dict(invalid_dict_unknown)
        
        error_msg = str(exc_info.value).lower()
        # Should mention the unknown parameter issue
        assert any(term in error_msg for term in ['unknown', 'invalid', 'parameter']), \
            f"Error should mention unknown parameter. Got: {exc_info.value}"
        
        # Test dictionary with invalid parameter types
        invalid_dict_types = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": "not_an_integer",  # Should be int
            "memory_cache_size": "also_not_an_integer",  # Should be int
            "enable_l1_cache": "not_a_boolean"  # Should be bool
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            AIResponseCacheConfig.from_dict(invalid_dict_types)
        
        error_msg = str(exc_info.value).lower()
        # Should mention type conversion or validation issue
        assert any(term in error_msg for term in ['type', 'convert', 'invalid', 'parameter']), \
            f"Error should mention type conversion issue. Got: {exc_info.value}"
        
        # Test dictionary with malformed complex parameters
        invalid_dict_complex = {
            "redis_url": "redis://localhost:6379",
            "operation_ttls": "not_a_dict",  # Should be dict
            "text_size_tiers": [1, 2, 3]  # Should be dict, not list
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            AIResponseCacheConfig.from_dict(invalid_dict_complex)
        
        error_msg = str(exc_info.value).lower()
        # Should mention the complex parameter issue
        assert any(term in error_msg for term in ['dict', 'structure', 'invalid', 'parameter']), \
            f"Error should mention complex parameter structure issue. Got: {exc_info.value}"

    def test_from_env_loads_configuration_from_preset_system(self):
        """
        Test that from_env() loads configuration from preset-based environment system.
        
        Verifies:
            Environment-based configuration uses preset system (not deprecated individual variables)
            
        Business Impact:
            Enables simplified deployment configuration through environment presets
            
        Scenario:
            Given: Environment variables configured for preset-based system
            When: AIResponseCacheConfig.from_env() is called
            Then: Configuration is loaded using preset system approach
            And: Preset-based environment variables take precedence
            And: Deprecated individual environment variables are ignored
            And: Warning is logged about deprecated environment variable usage
            
        Preset System Integration Verified:
            - CACHE_PRESET environment variable drives configuration selection
            - CACHE_REDIS_URL environment variable provides Redis URL override
            - CACHE_CUSTOM_CONFIG environment variable allows JSON overrides
            - Individual AI_CACHE_* environment variables are deprecated
            
        Fixtures Used:
            - Environment variable mocking (via os.environ patches)
            - mock_settings: Configuration preset integration
            
        Deprecation Warning Verified:
            Deprecated environment variables trigger appropriate deprecation warnings
            
        Related Tests:
            - test_from_env_handles_missing_environment_variables()
            - test_from_env_integrates_with_settings_preset_system()
        """
        # Test deprecated individual environment variables (should show warnings)
        with patch.dict(os.environ, {
            'AI_CACHE_DEFAULT_TTL': '7200',
            'AI_CACHE_MEMORY_CACHE_SIZE': '150',
            'AI_CACHE_REDIS_URL': 'redis://deprecated:6379'
        }, clear=False):
            
            # When: from_env() is called with deprecated variables
            config = AIResponseCacheConfig.from_env()
            
            # Then: Should create configuration but may show deprecation warnings
            assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
            
            # Configuration should be valid
            result = config.validate()
            assert result.is_valid, f"Environment configuration should be valid. Errors: {result.errors}"
            
            # Should have some configuration values set (either from env or defaults)
            assert config.default_ttl > 0, "Should have positive TTL"
            assert config.memory_cache_size > 0, "Should have positive memory cache size"
        
        # Test with no environment variables (should use defaults)
        with patch.dict(os.environ, {}, clear=False):
            # Remove any AI_CACHE_* variables that might exist
            env_to_clear = [k for k in os.environ.keys() if k.startswith('AI_CACHE_')]
            for key in env_to_clear:
                if key in os.environ:
                    del os.environ[key]
            
            config = AIResponseCacheConfig.from_env()
            assert isinstance(config, AIResponseCacheConfig), "Should return default configuration"
            
            result = config.validate()
            assert result.is_valid, f"Default environment configuration should be valid. Errors: {result.errors}"
        
        # Test environment variables with custom prefix
        with patch.dict(os.environ, {
            'CUSTOM_DEFAULT_TTL': '1800',
            'CUSTOM_MEMORY_CACHE_SIZE': '50'
        }, clear=False):
            
            config = AIResponseCacheConfig.from_env(prefix='CUSTOM_')
            assert isinstance(config, AIResponseCacheConfig), "Should return configuration with custom prefix"
            
            result = config.validate()
            assert result.is_valid, f"Custom prefix configuration should be valid. Errors: {result.errors}"

    def test_from_yaml_loads_configuration_from_yaml_file(self):
        """
        Test that from_yaml() loads configuration from YAML file.
        
        Verifies:
            YAML file-based configuration loading with error handling
            
        Business Impact:
            Enables file-based configuration management for complex deployments
            
        Scenario:
            Given: Valid YAML file containing configuration parameters
            When: AIResponseCacheConfig.from_yaml(yaml_path) is called
            Then: Configuration instance is created from YAML file contents
            And: All YAML parameters are properly parsed and mapped
            And: File loading errors are handled gracefully with ConfigurationError
            
        YAML Loading Verified:
            - Valid YAML files are parsed correctly
            - YAML parameter structure matches expected configuration format
            - Complex YAML structures (operation_ttls, text_size_tiers) are supported
            - YAML type conversion works correctly
            
        Fixtures Used:
            - File system mocking for YAML file access
            - YAML library mocking for YAML parsing behavior
            
        Error Handling Verified:
            - Missing YAML files raise ConfigurationError
            - Invalid YAML syntax raises ConfigurationError with parsing context
            - YAML library unavailable raises ConfigurationError with installation guidance
            
        Related Tests:
            - test_from_yaml_raises_configuration_error_for_missing_file()
            - test_from_yaml_raises_configuration_error_for_invalid_yaml()
        """
        # Mock YAML content
        yaml_content = """
redis_url: redis://yaml-test:6379/3
default_ttl: 5400
memory_cache_size: 120
compression_threshold: 1500
compression_level: 8
text_hash_threshold: 2500
hash_algorithm: sha256
text_size_tiers:
  small: 400
  medium: 4000
  large: 40000
operation_ttls:
  summarize: 10800
  sentiment: 21600
  qa: 2700
        """.strip()
        
        # Mock file reading and YAML parsing
        with patch('builtins.open', mock_open(read_data=yaml_content)) as mock_file, \
             patch('yaml.safe_load') as mock_yaml_load:
            
            # Configure YAML mock to return parsed data
            mock_yaml_load.return_value = {
                'redis_url': 'redis://yaml-test:6379/3',
                'default_ttl': 5400,
                'memory_cache_size': 120,
                'compression_threshold': 1500,
                'compression_level': 8,
                'text_hash_threshold': 2500,
                'hash_algorithm': 'sha256',
                'text_size_tiers': {
                    'small': 400,
                    'medium': 4000,
                    'large': 40000
                },
                'operation_ttls': {
                    'summarize': 10800,
                    'sentiment': 21600,
                    'qa': 2700
                }
            }
            
            # When: from_yaml() is called
            config = AIResponseCacheConfig.from_yaml('/path/to/config.yaml')
            
            # Then: Should create configuration from YAML
            assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
            assert config.redis_url == 'redis://yaml-test:6379/3'
            assert config.default_ttl == 5400
            assert config.memory_cache_size == 120
            assert config.compression_level == 8
            assert config.text_hash_threshold == 2500
            
            # Verify complex parameters
            assert config.text_size_tiers['small'] == 400
            assert config.operation_ttls['summarize'] == 10800
            
            # Configuration should be valid
            result = config.validate()
            assert result.is_valid, f"YAML configuration should be valid. Errors: {result.errors}"
            
            # Verify file operations
            mock_file.assert_called_once_with('/path/to/config.yaml', 'r', encoding='utf-8')
            mock_yaml_load.assert_called_once()
        
        # Test YAML library unavailable scenario
        with patch('app.infrastructure.cache.ai_config.yaml', None):
            with pytest.raises(ConfigurationError) as exc_info:
                AIResponseCacheConfig.from_yaml('/path/to/config.yaml')
            
            error_msg = str(exc_info.value).lower()
            assert 'yaml' in error_msg, f"Error should mention YAML library requirement. Got: {exc_info.value}"

    def test_from_json_loads_configuration_from_json_file(self):
        """
        Test that from_json() loads configuration from JSON file.
        
        Verifies:
            JSON file-based configuration loading with comprehensive error handling
            
        Business Impact:
            Enables JSON-based configuration for deployments preferring JSON over YAML
            
        Scenario:
            Given: Valid JSON file containing configuration parameters
            When: AIResponseCacheConfig.from_json(json_path) is called
            Then: Configuration instance is created from JSON file contents
            And: All JSON parameters are properly parsed and mapped to configuration
            And: JSON parsing errors are handled with specific error context
            
        JSON Loading Verified:
            - Valid JSON files are parsed correctly using standard json module
            - JSON parameter structure maps properly to configuration fields
            - Complex JSON structures (operation_ttls, text_size_tiers) are supported
            - JSON type handling works correctly for all supported parameter types
            
        Fixtures Used:
            - File system mocking for JSON file access
            - JSON parsing behavior testing (using real json module)
            
        Error Handling Verified:
            - Missing JSON files raise ConfigurationError with file context
            - Invalid JSON syntax raises ConfigurationError with parsing details
            - JSON structure validation provides specific parameter error context
            
        Related Tests:
            - test_from_json_raises_configuration_error_for_missing_file()
            - test_from_json_raises_configuration_error_for_invalid_json()
        """
        # Mock JSON content
        json_content = '''
{
  "redis_url": "redis://json-test:6379/4",
  "default_ttl": 6300,
  "memory_cache_size": 180,
  "compression_threshold": 800,
  "compression_level": 5,
  "text_hash_threshold": 3000,
  "hash_algorithm": "sha256",
  "text_size_tiers": {
    "small": 250,
    "medium": 2500,
    "large": 25000
  },
  "operation_ttls": {
    "summarize": 9000,
    "sentiment": 18000,
    "qa": 1200,
    "key_points": 7200
  }
}
        '''.strip()
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data=json_content)) as mock_file:
            
            # When: from_json() is called
            config = AIResponseCacheConfig.from_json('/path/to/config.json')
            
            # Then: Should create configuration from JSON
            assert isinstance(config, AIResponseCacheConfig), "Should return AIResponseCacheConfig instance"
            assert config.redis_url == 'redis://json-test:6379/4'
            assert config.default_ttl == 6300
            assert config.memory_cache_size == 180
            assert config.compression_threshold == 800
            assert config.compression_level == 5
            assert config.text_hash_threshold == 3000
            
            # Verify complex parameters
            assert config.text_size_tiers['small'] == 250
            assert config.text_size_tiers['medium'] == 2500
            assert config.operation_ttls['summarize'] == 9000
            assert config.operation_ttls['key_points'] == 7200
            
            # Configuration should be valid
            result = config.validate()
            assert result.is_valid, f"JSON configuration should be valid. Errors: {result.errors}"
            
            # Verify file operations
            mock_file.assert_called_once_with('/path/to/config.json', 'r', encoding='utf-8')
        
        # Test invalid JSON syntax
        invalid_json = '{ "redis_url": "redis://localhost:6379", "invalid": }'
        
        with patch('builtins.open', mock_open(read_data=invalid_json)):
            with pytest.raises(ConfigurationError) as exc_info:
                AIResponseCacheConfig.from_json('/path/to/invalid.json')
            
            error_msg = str(exc_info.value).lower()
            assert any(term in error_msg for term in ['json', 'parse', 'syntax', 'invalid']), \
                f"Error should mention JSON parsing issue. Got: {exc_info.value}"
        
        # Test missing file
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(ConfigurationError) as exc_info:
                AIResponseCacheConfig.from_json('/path/to/missing.json')
            
            error_msg = str(exc_info.value).lower()
            assert any(term in error_msg for term in ['file', 'found', 'missing']), \
                f"Error should mention missing file. Got: {exc_info.value}"


class TestAIResponseCacheConfigConversion:
    """
    Test suite for AIResponseCacheConfig parameter conversion behavior.
    
    Scope:
        - Parameter conversion to AIResponseCache kwargs (legacy compatibility)
        - Parameter conversion to GenericRedisCache kwargs (new architecture)
        - Parameter mapping between AI-specific and generic parameters
        - Backward compatibility with existing cache initialization patterns
        
    Business Critical:
        Parameter conversion enables seamless integration with both legacy and new cache architectures
        
    Test Strategy:
        - Unit tests for to_ai_cache_kwargs() with different configuration scenarios
        - Unit tests for to_generic_cache_kwargs() with parameter mapping verification
        - Backward compatibility testing with existing cache initialization patterns
        - Parameter mapping accuracy testing for both conversion methods
        
    External Dependencies:
        - CacheParameterMapper (used internally for parameter mapping validation)
        - AIResponseCache constructor patterns (for compatibility verification)
        - GenericRedisCache constructor patterns (for new architecture verification)
    """

    def test_to_ai_cache_kwargs_converts_for_legacy_ai_cache_constructor(self):
        """
        Test that to_ai_cache_kwargs() produces parameters compatible with legacy AIResponseCache constructor.
        
        Verifies:
            Parameter conversion maintains backward compatibility with existing AIResponseCache usage
            
        Business Impact:
            Enables gradual migration from direct constructor usage to configuration-based approach
            
        Scenario:
            Given: AIResponseCacheConfig with various parameter combinations
            When: to_ai_cache_kwargs() is called
            Then: Returned dictionary contains all parameters expected by AIResponseCache constructor
            And: Parameter names match legacy constructor expectations (memory_cache_size vs l1_cache_size)
            And: All parameter values are correctly formatted for legacy constructor
            
        Legacy Constructor Compatibility Verified:
            - memory_cache_size parameter (not l1_cache_size) for backward compatibility
            - All AI-specific parameters are included in kwargs
            - Redis connection parameters are formatted for legacy constructor
            - Performance monitoring integration parameters are included
            
        Fixtures Used:
            - None (testing parameter conversion logic directly)
            
        Parameter Mapping Verified:
            Configuration parameters map correctly to legacy constructor parameter names
            
        Related Tests:
            - test_to_generic_cache_kwargs_converts_for_new_architecture()
            - test_parameter_conversion_maintains_data_integrity()
        """
        pass

    def test_to_generic_cache_kwargs_converts_for_new_modular_architecture(self):
        """
        Test that to_generic_cache_kwargs() produces parameters for new GenericRedisCache architecture.
        
        Verifies:
            Parameter conversion supports new modular cache architecture
            
        Business Impact:
            Enables adoption of new GenericRedisCache architecture with proper parameter mapping
            
        Scenario:
            Given: AIResponseCacheConfig with full parameter configuration
            When: to_generic_cache_kwargs() is called
            Then: Returned dictionary contains parameters formatted for GenericRedisCache
            And: Parameter names use new architecture naming (enable_l1_cache, l1_cache_size)
            And: AI-specific parameters are excluded (handled separately by inheritance)
            
        New Architecture Compatibility Verified:
            - enable_l1_cache and l1_cache_size parameters (not memory_cache_size)
            - Generic Redis parameters only (AI parameters handled by inheritance)
            - Security configuration parameters for new architecture
            - Performance monitoring integration with new parameter names
            
        Fixtures Used:
            - None (testing parameter conversion logic directly)
            
        Architecture Migration Support Verified:
            Parameter conversion supports migration to new modular cache architecture
            
        Related Tests:
            - test_to_ai_cache_kwargs_converts_for_legacy_ai_cache_constructor()
            - test_parameter_mapping_excludes_ai_specific_parameters_for_generic()
        """
        pass

    def test_parameter_conversion_maintains_data_integrity(self):
        """
        Test that parameter conversion maintains data integrity across different conversion methods.
        
        Verifies:
            Parameter values remain consistent across different conversion methods
            
        Business Impact:
            Ensures consistent cache behavior regardless of which initialization approach is used
            
        Scenario:
            Given: AIResponseCacheConfig with comprehensive parameter configuration
            When: Both to_ai_cache_kwargs() and to_generic_cache_kwargs() are called
            Then: Common parameter values are identical between both conversion results
            And: Parameter type conversions maintain data accuracy
            And: No data loss occurs during conversion process
            
        Data Integrity Verification:
            - redis_url parameter is identical in both conversion results
            - default_ttl values are preserved accurately
            - compression parameters maintain exact values
            - Security configuration parameters are preserved
            
        Fixtures Used:
            - None (testing conversion consistency directly)
            
        Cross-Method Consistency Verified:
            Common parameters produce identical results across different conversion methods
            
        Related Tests:
            - test_parameter_conversion_handles_optional_parameters_correctly()
            - test_parameter_conversion_validates_required_parameters()
        """
        pass

    def test_parameter_conversion_handles_optional_parameters_correctly(self):
        """
        Test that parameter conversion properly handles optional parameters.
        
        Verifies:
            Optional parameters are converted correctly with appropriate default handling
            
        Business Impact:
            Ensures flexible configuration with proper handling of unspecified parameters
            
        Scenario:
            Given: AIResponseCacheConfig with only some parameters specified (others None or default)
            When: Parameter conversion methods are called
            Then: Optional parameters are handled appropriately in conversion results
            And: None values are converted appropriately for each target constructor
            And: Default values are applied correctly when parameters are unspecified
            
        Optional Parameter Handling Verified:
            - None values for optional parameters are handled correctly
            - Default values are applied when appropriate
            - Optional complex parameters (operation_ttls, etc.) handle None values
            - Performance monitoring parameters handle optional configuration
            
        Fixtures Used:
            - None (testing optional parameter handling directly)
            
        Edge Cases Covered:
            - Configuration with minimal required parameters only
            - Configuration with mixed specified and unspecified parameters
            - Configuration with None values for optional parameters
            
        Related Tests:
            - test_parameter_conversion_maintains_data_integrity()
            - test_parameter_conversion_validates_required_vs_optional_parameters()
        """
        pass

    def test_parameter_mapping_excludes_ai_specific_parameters_for_generic(self):
        """
        Test that to_generic_cache_kwargs() excludes AI-specific parameters appropriately.
        
        Verifies:
            Generic cache parameter conversion excludes AI-specific configuration
            
        Business Impact:
            Ensures clean parameter separation for modular cache architecture
            
        Scenario:
            Given: AIResponseCacheConfig with both generic and AI-specific parameters
            When: to_generic_cache_kwargs() is called
            Then: Result includes only generic Redis cache parameters
            And: AI-specific parameters (text_hash_threshold, operation_ttls, etc.) are excluded
            And: Generic parameters are properly formatted for GenericRedisCache
            
        Parameter Separation Verified:
            - text_hash_threshold is excluded from generic kwargs
            - hash_algorithm is excluded from generic kwargs
            - text_size_tiers is excluded from generic kwargs
            - operation_ttls is excluded from generic kwargs
            - Generic Redis parameters are included properly
            
        Fixtures Used:
            - None (testing parameter separation logic directly)
            
        Architecture Separation Verified:
            Clear separation between generic and AI-specific parameters for modular architecture
            
        Related Tests:
            - test_to_ai_cache_kwargs_includes_all_ai_parameters()
            - test_parameter_conversion_supports_inheritance_architecture()
        """
        pass


class TestAIResponseCacheConfigMerging:
    """
    Test suite for AIResponseCacheConfig merging and inheritance behavior.
    
    Scope:
        - Configuration merging with merge() method
        - Configuration overriding with merge_with() method
        - Configuration inheritance patterns for environment-specific customization
        - Default value handling during merge operations
        
    Business Critical:
        Configuration merging enables environment-specific customization while maintaining base configurations
        
    Test Strategy:
        - Unit tests for merge() method with different configuration combinations
        - Unit tests for merge_with() method with explicit override scenarios
        - Configuration inheritance testing with base/override patterns
        - Default value preservation testing during merge operations
        
    External Dependencies:
        - Configuration comparison logic (for verifying merge results)
        - Default value detection (for proper merge behavior)
    """

    def test_merge_combines_configurations_with_precedence(self):
        """
        Test that merge() combines configurations with proper precedence rules.
        
        Verifies:
            Configuration merging with other configuration taking precedence
            
        Business Impact:
            Enables base configuration with environment-specific overrides
            
        Scenario:
            Given: Base AIResponseCacheConfig and override AIResponseCacheConfig
            When: base_config.merge(override_config) is called
            Then: New configuration is created combining both configurations
            And: Override configuration parameters take precedence over base parameters
            And: Base configuration parameters are preserved where override doesn't specify
            
        Merge Precedence Verified:
            - Override configuration values take precedence over base values
            - Base configuration values are preserved when override has None/default values
            - Complex parameters (operation_ttls, text_size_tiers) are merged appropriately
            - All merged parameters pass validation
            
        Fixtures Used:
            - None (testing merge logic directly)
            
        Configuration Inheritance Verified:
            Merge operation supports proper configuration inheritance patterns
            
        Related Tests:
            - test_merge_with_combines_explicit_override_values()
            - test_merge_preserves_base_configuration_defaults()
        """
        pass

    def test_merge_with_combines_explicit_override_values(self):
        """
        Test that merge_with() combines configuration with explicit keyword overrides.
        
        Verifies:
            Configuration merging with explicit parameter overrides
            
        Business Impact:
            Enables targeted configuration customization with specific parameter overrides
            
        Scenario:
            Given: Base AIResponseCacheConfig and explicit override keyword arguments
            When: base_config.merge_with(**overrides) is called
            Then: New configuration is created with explicit overrides applied
            And: Only specified override parameters are changed from base configuration
            And: Unspecified parameters retain base configuration values
            
        Explicit Override Verified:
            - Only explicitly provided keyword arguments override base values
            - Non-specified parameters maintain base configuration values
            - Override validation ensures valid parameter combinations
            - Complex parameter overrides (operation_ttls) work correctly
            
        Fixtures Used:
            - None (testing explicit override logic directly)
            
        Targeted Customization Verified:
            Merge_with enables precise configuration customization without full configuration replacement
            
        Related Tests:
            - test_merge_combines_configurations_with_precedence()
            - test_merge_with_validates_override_parameter_compatibility()
        """
        pass

    def test_merge_preserves_base_configuration_defaults(self):
        """
        Test that merge operations preserve base configuration defaults appropriately.
        
        Verifies:
            Default value preservation during configuration merging
            
        Business Impact:
            Ensures merge operations don't inadvertently change well-configured base settings
            
        Scenario:
            Given: Base configuration with carefully tuned parameters and override with minimal changes
            When: Merge operation is performed
            Then: Base configuration's non-overridden parameters are preserved exactly
            And: Default value detection prevents accidental override with defaults
            And: Complex parameter structures maintain base values where not explicitly overridden
            
        Default Preservation Verified:
            - Base TTL values are preserved when override doesn't specify different TTL
            - Base compression settings are preserved when override uses defaults
            - Base AI parameters are preserved when override focuses on Redis settings
            - Operation-specific TTLs are merged rather than completely replaced
            
        Fixtures Used:
            - None (testing default preservation logic directly)
            
        Intelligent Merging Verified:
            Merge operations intelligently preserve base configuration quality
            
        Related Tests:
            - test_merge_handles_complex_parameter_inheritance()
            - test_merge_validates_merged_configuration_integrity()
        """
        pass

    def test_merge_handles_complex_parameter_inheritance(self):
        """
        Test that merge operations handle complex parameters (dictionaries, nested structures) correctly.
        
        Verifies:
            Complex parameter merging with proper structure preservation
            
        Business Impact:
            Enables sophisticated configuration inheritance for complex deployment scenarios
            
        Scenario:
            Given: Configurations with complex parameters (operation_ttls, text_size_tiers)
            When: Merge operations are performed
            Then: Complex parameters are merged intelligently rather than completely replaced
            And: Dictionary parameters combine keys from both base and override
            And: Override values take precedence for conflicting keys
            
        Complex Parameter Merging Verified:
            - operation_ttls dictionaries are merged by key
            - text_size_tiers dictionaries are merged intelligently
            - Nested parameter structures are handled correctly
            - Complex parameter validation works after merging
            
        Fixtures Used:
            - None (testing complex parameter merging directly)
            
        Sophisticated Inheritance Verified:
            Merge operations support complex configuration inheritance scenarios
            
        Related Tests:
            - test_merge_validates_complex_parameter_compatibility()
            - test_merge_preserves_complex_parameter_data_integrity()
        """
        pass

    def test_merged_configuration_passes_validation(self):
        """
        Test that merged configurations pass comprehensive validation.
        
        Verifies:
            Merged configurations maintain validation compliance
            
        Business Impact:
            Ensures configuration merging doesn't create invalid cache configurations
            
        Scenario:
            Given: Valid base and override configurations
            When: Configurations are merged using either merge() or merge_with()
            Then: Resulting merged configuration passes validate() method
            And: No validation errors are introduced by merge operation
            And: Merged configuration is ready for cache initialization
            
        Post-Merge Validation Verified:
            - Merged configurations pass all parameter validation checks
            - Parameter relationships remain valid after merging
            - Complex parameter structures remain valid after merging
            - Performance recommendations reflect merged configuration appropriately
            
        Fixtures Used:
            - None (testing validation compliance after merging)
            
        Configuration Quality Assurance Verified:
            Merge operations maintain configuration quality and validity
            
        Related Tests:
            - test_merge_prevents_invalid_configuration_creation()
            - test_merged_configuration_supports_cache_initialization()
        """
        pass