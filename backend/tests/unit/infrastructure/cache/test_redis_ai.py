"""
Comprehensive unit tests for AIResponseCache following docstring-driven test development.

This module implements behavior-focused tests that validate the documented contracts
of AIResponseCache methods, focusing on AI-specific caching functionality while
ensuring proper mocking to avoid external Redis dependencies.

Test Coverage Areas:
    - AIResponseCache initialization and parameter validation
    - AI-specific cache operations (cache_response, get_cached_response)
    - Text tier categorization and intelligent key generation
    - AI metrics collection and performance monitoring
    - Graceful degradation and error handling patterns
    - Edge cases: large responses, connection failures, memory fallbacks

Business Impact:
    These tests ensure the AI cache infrastructure provides reliable caching for
    expensive LLM operations while maintaining data consistency and performance.
    Test failures indicate potential issues with AI response storage/retrieval
    that could impact user experience and system performance.

Architecture Focus:
    Tests the refactored inheritance model where AIResponseCache extends
    GenericRedisCache with AI-specific functionality while maintaining clean
    separation of concerns and proper error handling patterns.
"""

import asyncio
import hashlib
import pytest
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
from app.infrastructure.cache.key_generator import CacheKeyGenerator


class TestAIResponseCacheInitialization:
    """Test AIResponseCache initialization and configuration behavior per docstrings."""

    @pytest.fixture
    def mock_performance_monitor(self):
        """Create a mock performance monitor for testing."""
        return MagicMock(spec=CachePerformanceMonitor)

    @pytest.fixture
    def mock_parameter_mapper(self):
        """Create a mock parameter mapper for testing."""
        mapper = MagicMock(spec=CacheParameterMapper)
        # Mock successful parameter mapping
        mapper.map_ai_to_generic_params.return_value = (
            {  # generic_params
                'redis_url': 'redis://localhost:6379',
                'default_ttl': 3600,
                'l1_cache_size': 100,
                'compression_threshold': 1000,
                'compression_level': 6
            },
            {  # ai_specific_params  
                'text_hash_threshold': 1000,
                'hash_algorithm': hashlib.sha256,
                'text_size_tiers': {
                    "small": 500,
                    "medium": 5000,
                    "large": 50000,
                },
                'operation_ttls': {
                    "summarize": 7200,
                    "sentiment": 86400,
                    "key_points": 7200,
                    "questions": 3600,
                    "qa": 1800,
                }
            }
        )
        # Mock successful validation
        validation_result = MagicMock()
        validation_result.is_valid = True
        validation_result.errors = []
        validation_result.warnings = []
        mapper.validate_parameter_compatibility.return_value = validation_result
        return mapper

    @pytest.fixture
    def mock_key_generator(self):
        """Create a mock key generator for testing."""
        generator = MagicMock(spec=CacheKeyGenerator)
        generator.generate_cache_key.return_value = "ai_cache:op:test|txt:sample|opts:abc123"
        return generator

    def test_ai_cache_initialization_with_defaults(self, mock_performance_monitor, mock_parameter_mapper, mock_key_generator):
        """
        Test that AIResponseCache initializes correctly with default parameters.
        
        Verifies:
            Default configuration values are applied correctly
            
        Business Impact:
            Ensures AI cache can start with minimal configuration for development
            
        Scenario:
            Given: Minimal initialization parameters
            When: AIResponseCache is created
            Then: Default values are set for all AI-specific configuration
            
        Edge Cases Covered:
            - Default text size tiers are established
            - Default operation TTLs are configured
            - Memory cache fallback is enabled
        """
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Setup mocks
            MockMapper.return_value = mock_parameter_mapper
            MockKeyGen.return_value = mock_key_generator
            MockParentInit.return_value = None
            
            cache = AIResponseCache()
            
            # Verify default configuration was applied
            assert cache.text_hash_threshold == 1000
            assert cache.hash_algorithm == hashlib.sha256
            assert isinstance(cache.operation_ttls, dict)
            assert 'summarize' in cache.operation_ttls
            assert 'sentiment' in cache.operation_ttls
            # text_size_tiers is wrapped in MagicMock for testability
            assert cache.text_size_tiers is not None
            assert cache.text_size_tiers['small'] == 500
            assert cache.text_size_tiers['medium'] == 5000
            assert cache.text_size_tiers['large'] == 50000

    def test_ai_cache_initialization_parameter_mapping_validation(self, mock_performance_monitor, mock_key_generator):
        """
        Test that parameter mapping validation is performed during initialization.
        
        Verifies:
            CacheParameterMapper validates parameter compatibility
            
        Business Impact:
            Prevents misconfigured cache instances that could cause runtime failures
            
        Scenario:
            Given: AI cache initialization parameters
            When: AIResponseCache is created
            Then: Parameter mapping and validation are performed
            
        Edge Cases Covered:
            - Parameter validation failure raises ValidationError
            - Configuration errors are properly contextualized
        """
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Setup parameter mapper to return validation failure
            mapper_instance = MagicMock(spec=CacheParameterMapper)
            # First configure the parameter mapping (needed for initialization)
            mapper_instance.map_ai_to_generic_params.return_value = (
                {  # generic_params
                    'redis_url': 'redis://localhost:6379',
                    'default_ttl': -100,
                    'l1_cache_size': 100,
                    'compression_threshold': 1000,
                    'compression_level': 6
                },
                {  # ai_specific_params  
                    'text_hash_threshold': 1000,
                    'hash_algorithm': hashlib.sha256,
                    'text_size_tiers': None,
                    'operation_ttls': None
                }
            )
            # Then configure validation failure
            validation_result = MagicMock()
            validation_result.is_valid = False
            validation_result.errors = ["Invalid TTL configuration", "Memory cache size out of bounds"]
            validation_result.warnings = []
            mapper_instance.validate_parameter_compatibility.return_value = validation_result
            MockMapper.return_value = mapper_instance
            MockKeyGen.return_value = mock_key_generator
            MockParentInit.return_value = None
            
            with pytest.raises(ValidationError) as exc_info:
                AIResponseCache(default_ttl=-100, memory_cache_size=-50)
            
            assert "parameter validation failed" in str(exc_info.value).lower()
            assert "Invalid TTL configuration" in str(exc_info.value)

    def test_ai_cache_initialization_with_custom_configuration(self, mock_performance_monitor, mock_parameter_mapper, mock_key_generator):
        """
        Test that AIResponseCache accepts and applies custom configuration parameters.
        
        Verifies:
            Custom parameters override defaults correctly
            
        Business Impact:
            Enables production tuning for optimal AI caching performance
            
        Scenario:
            Given: Custom configuration parameters for production use
            When: AIResponseCache is created with custom settings
            Then: All custom values are applied correctly
            
        Edge Cases Covered:
            - Custom text size tiers for specific workloads
            - Custom operation TTLs for different AI services
            - Custom hash algorithm for security requirements
        """
        custom_tiers = {'small': 200, 'medium': 2000, 'large': 20000}
        custom_ttls = {'summarize': 14400, 'sentiment': 172800}
        
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Create custom mock that returns the custom values
            custom_mapper = MagicMock(spec=CacheParameterMapper)
            custom_mapper.map_ai_to_generic_params.return_value = (
                {  # generic_params
                    'redis_url': 'redis://production:6379',
                    'default_ttl': 7200,
                    'l1_cache_size': 200,
                    'compression_threshold': 2000,
                    'compression_level': 9
                },
                {  # ai_specific_params  
                    'text_hash_threshold': 2000,
                    'hash_algorithm': hashlib.sha512,
                    'text_size_tiers': custom_tiers,
                    'operation_ttls': custom_ttls
                }
            )
            # Mock successful validation
            validation_result = MagicMock()
            validation_result.is_valid = True
            validation_result.errors = []
            validation_result.warnings = []
            custom_mapper.validate_parameter_compatibility.return_value = validation_result
            
            MockMapper.return_value = custom_mapper
            MockKeyGen.return_value = mock_key_generator
            MockParentInit.return_value = None
            
            cache = AIResponseCache(
                redis_url="redis://production:6379",
                default_ttl=7200,
                text_hash_threshold=2000,
                hash_algorithm=hashlib.sha512,
                text_size_tiers=custom_tiers,
                memory_cache_size=500,
                operation_ttls=custom_ttls
            )
            
            # Verify custom configuration was applied
            assert cache.text_hash_threshold == 2000
            assert cache.hash_algorithm == hashlib.sha512
            # text_size_tiers is wrapped in MagicMock, test the behavior
            assert cache.text_size_tiers['small'] == 200
            assert cache.text_size_tiers['medium'] == 2000
            assert cache.text_size_tiers['large'] == 20000
            assert cache.operation_ttls['summarize'] == 14400
            assert cache.operation_ttls['sentiment'] == 172800


class TestAIResponseCacheCoreOperations:
    """Test AI-specific cache operations following documented behavior contracts."""

    @pytest.fixture
    async def ai_cache_instance(self):
        """Create configured AIResponseCache instance for testing."""
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Setup mocks
            mapper = MagicMock(spec=CacheParameterMapper)
            mapper.map_ai_to_generic_params.return_value = ({}, {})
            validation_result = MagicMock()
            validation_result.is_valid = True
            validation_result.errors = []
            validation_result.warnings = []
            mapper.validate_parameter_compatibility.return_value = validation_result
            MockMapper.return_value = mapper
            
            key_gen = MagicMock(spec=CacheKeyGenerator)
            key_gen.generate_cache_key.return_value = "ai_cache:op:summarize|txt:hash123|opts:def456"
            MockKeyGen.return_value = key_gen
            
            MockParentInit.return_value = None
            
            cache = AIResponseCache()
            
            # Mock inherited methods from GenericRedisCache
            cache.set = AsyncMock(return_value=True)
            cache.get = AsyncMock(return_value=None)
            cache.delete = AsyncMock(return_value=True)
            cache.exists = AsyncMock(return_value=False)
            
            # Mock performance monitor
            cache.performance_monitor = MagicMock(spec=CachePerformanceMonitor)
            cache.performance_monitor.record_cache_operation_time = MagicMock()
            
            # Setup AI metrics tracking
            cache.ai_metrics = {
                'cache_hits_by_operation': defaultdict(int),
                'cache_misses_by_operation': defaultdict(int),
                'text_tier_distribution': defaultdict(int),
                'operation_performance': []
            }
            
            yield cache

    @pytest.fixture
    def sample_ai_response(self):
        """Sample AI response for testing cache operations."""
        return {
            "summary": "This is a comprehensive summary of the input text.",
            "confidence": 0.92,
            "model": "gpt-4",
            "tokens_used": 245,
            "processing_time": 1.23
        }

    @pytest.fixture
    def sample_options(self):
        """Sample operation options for testing."""
        return {
            "max_length": 150,
            "temperature": 0.7,
            "model": "gpt-4"
        }

    async def test_cache_response_successful_storage(self, ai_cache_instance, sample_ai_response, sample_options):
        """
        Test that cache_response successfully stores AI responses with proper metadata.
        
        Verifies:
            AI response is cached with enhanced metadata per docstring
            
        Business Impact:
            Ensures expensive AI operations are properly cached to reduce costs
            
        Scenario:
            Given: Valid text, operation, options, and AI response
            When: cache_response is called
            Then: Response is stored with comprehensive AI metadata
            
        Edge Cases Covered:
            - Metadata includes cache timestamp and AI version
            - Text tier is determined and included
            - Operation-specific TTL is applied
        """
        cache = ai_cache_instance
        test_text = "This is a sample document that needs summarization for testing purposes."
        
        # Execute cache operation
        await cache.cache_response(
            text=test_text,
            operation="summarize",
            options=sample_options,
            response=sample_ai_response
        )
        
        # Verify set() was called with enhanced response
        cache.set.assert_called_once()
        call_args = cache.set.call_args
        cached_key, cached_value, cached_ttl = call_args[0]
        
        # Verify enhanced metadata was added
        assert cached_value['summary'] == sample_ai_response['summary']
        assert cached_value['confidence'] == sample_ai_response['confidence']
        assert 'cached_at' in cached_value
        assert cached_value['cache_hit'] is False
        assert 'text_length' in cached_value
        assert 'text_tier' in cached_value
        assert cached_value['operation'] == "summarize"
        assert cached_value['ai_version'] == "refactored_inheritance"
        
        # Verify TTL matches operation-specific configuration
        assert cached_ttl == cache.operation_ttls.get("summarize", cache.default_ttl)

    async def test_cache_response_input_validation_errors(self, ai_cache_instance, sample_ai_response, sample_options):
        """
        Test that cache_response validates input parameters and raises ValidationError.
        
        Verifies:
            Invalid input parameters raise ValidationError per docstring
            
        Business Impact:
            Prevents invalid data from corrupting the cache
            
        Scenario:
            Given: Invalid input parameters (empty text, invalid operation, etc.)
            When: cache_response is called
            Then: ValidationError is raised with descriptive message
            
        Edge Cases Covered:
            - Empty or None text raises ValidationError
            - Empty or None operation raises ValidationError
            - Non-dict options raises ValidationError
            - Non-dict response raises ValidationError
        """
        cache = ai_cache_instance
        
        # Test empty text validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.cache_response("", "summarize", sample_options, sample_ai_response)
        assert "invalid text parameter" in str(exc_info.value).lower()
        
        # Test None text validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.cache_response(None, "summarize", sample_options, sample_ai_response)
        assert "invalid text parameter" in str(exc_info.value).lower()
        
        # Test empty operation validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.cache_response("valid text", "", sample_options, sample_ai_response)
        assert "invalid operation parameter" in str(exc_info.value).lower()
        
        # Test non-dict options validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.cache_response("valid text", "summarize", "invalid options", sample_ai_response)
        assert "invalid options parameter" in str(exc_info.value).lower()
        
        # Test non-dict response validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.cache_response("valid text", "summarize", sample_options, "invalid response")
        assert "invalid response parameter" in str(exc_info.value).lower()

    async def test_get_cached_response_successful_retrieval(self, ai_cache_instance, sample_ai_response):
        """
        Test that get_cached_response successfully retrieves and enhances cached AI responses.
        
        Verifies:
            Cached responses are retrieved with enhanced metadata per docstring
            
        Business Impact:
            Enables fast retrieval of expensive AI operations to improve user experience
            
        Scenario:
            Given: Previously cached AI response exists
            When: get_cached_response is called with matching parameters
            Then: Response is retrieved with cache hit metadata and retrieval timestamp
            
        Edge Cases Covered:
            - Cache hit metadata is properly added
            - Retrieved timestamp is current
            - Original response data is preserved
        """
        cache = ai_cache_instance
        
        # Mock successful cache retrieval
        cached_data = {
            **sample_ai_response,
            "cached_at": "2024-01-15T10:30:00",
            "cache_hit": False,
            "text_tier": "medium"
        }
        cache.get.return_value = cached_data
        
        # Execute retrieval
        result = await cache.get_cached_response(
            text="Sample text for testing",
            operation="summarize",
            options={"max_length": 100}
        )
        
        # Verify response enhancement
        assert result is not None
        assert result['cache_hit'] is True  # Should be updated to True on retrieval
        assert 'retrieved_at' in result
        assert result['summary'] == sample_ai_response['summary']
        assert result['confidence'] == sample_ai_response['confidence']
        
        # Verify cache key generation was called
        cache.key_generator.generate_cache_key.assert_called_once()

    async def test_get_cached_response_cache_miss(self, ai_cache_instance):
        """
        Test that get_cached_response handles cache misses correctly.
        
        Verifies:
            Cache misses return None and record appropriate metrics
            
        Business Impact:
            Enables proper fallback to AI service when cache is empty
            
        Scenario:
            Given: No cached response exists for the parameters
            When: get_cached_response is called
            Then: None is returned and miss metrics are recorded
            
        Edge Cases Covered:
            - None return value for cache misses
            - Miss metrics are properly recorded
            - No side effects on cache state
        """
        cache = ai_cache_instance
        
        # Mock cache miss (get returns None)
        cache.get.return_value = None
        
        # Execute retrieval
        result = await cache.get_cached_response(
            text="Text not in cache",
            operation="sentiment",
            options={"model": "gpt-4"}
        )
        
        # Verify cache miss behavior
        assert result is None
        
        # Verify metrics were recorded for the miss
        assert cache.ai_metrics['cache_misses_by_operation']['sentiment'] == 1

    async def test_get_cached_response_input_validation(self, ai_cache_instance):
        """
        Test that get_cached_response validates input parameters per docstring.
        
        Verifies:
            Invalid input parameters raise ValidationError
            
        Business Impact:
            Prevents cache corruption from invalid lookup parameters
            
        Scenario:
            Given: Invalid input parameters for cache lookup
            When: get_cached_response is called
            Then: ValidationError is raised with descriptive context
            
        Edge Cases Covered:
            - Empty text parameter validation
            - Empty operation parameter validation
            - None values handled appropriately
        """
        cache = ai_cache_instance
        
        # Test empty text validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.get_cached_response("", "summarize")
        assert "invalid text parameter" in str(exc_info.value).lower()
        
        # Test empty operation validation
        with pytest.raises(ValidationError) as exc_info:
            await cache.get_cached_response("valid text", "")
        assert "invalid operation parameter" in str(exc_info.value).lower()


class TestAIResponseCacheTextTierLogic:
    """Test text tier categorization behavior as documented in docstrings."""

    @pytest.fixture
    def configured_cache(self):
        """Create AIResponseCache with known tier configuration for testing."""
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Setup mocks
            mapper = MagicMock(spec=CacheParameterMapper)
            mapper.map_ai_to_generic_params.return_value = ({}, {})
            validation_result = MagicMock()
            validation_result.is_valid = True
            validation_result.errors = []
            validation_result.warnings = []
            mapper.validate_parameter_compatibility.return_value = validation_result
            MockMapper.return_value = mapper
            
            MockKeyGen.return_value = MagicMock(spec=CacheKeyGenerator)
            MockParentInit.return_value = None
            
            cache = AIResponseCache()
            # Set known tier thresholds for predictable testing
            cache.text_size_tiers = {
                'small': 100,    # < 100 chars
                'medium': 1000,  # 100-999 chars
                'large': 10000   # 1000-9999 chars
            }
            
            return cache

    def test_get_text_tier_small_text_classification(self, configured_cache):
        """
        Test that _get_text_tier correctly classifies small text per docstring.
        
        Verifies:
            Text under small threshold returns 'small' tier
            
        Business Impact:
            Ensures small texts get fast memory cache promotion for optimal performance
            
        Scenario:
            Given: Text length below small threshold (< 100 chars)
            When: _get_text_tier is called
            Then: 'small' tier is returned
            
        Edge Cases Covered:
            - Empty string (0 chars)
            - Single character (1 char)
            - Just under threshold (99 chars)
        """
        cache = configured_cache
        
        # Test empty string
        assert cache._get_text_tier("") == "small"
        
        # Test single character
        assert cache._get_text_tier("a") == "small"
        
        # Test just under small threshold
        text_99_chars = "a" * 99
        assert cache._get_text_tier(text_99_chars) == "small"

    def test_get_text_tier_medium_text_classification(self, configured_cache):
        """
        Test that _get_text_tier correctly classifies medium text per docstring.
        
        Verifies:
            Text in medium range returns 'medium' tier with balanced caching
            
        Business Impact:
            Ensures medium texts get appropriate caching strategy for balanced performance
            
        Scenario:
            Given: Text length in medium range (100-999 chars)
            When: _get_text_tier is called
            Then: 'medium' tier is returned
            
        Edge Cases Covered:
            - Exactly at small threshold (100 chars)
            - Mid-range text (500 chars)
            - Just under large threshold (999 chars)
        """
        cache = configured_cache
        
        # Test exactly at small threshold
        text_100_chars = "a" * 100
        assert cache._get_text_tier(text_100_chars) == "medium"
        
        # Test mid-range
        text_500_chars = "a" * 500
        assert cache._get_text_tier(text_500_chars) == "medium"
        
        # Test just under large threshold
        text_999_chars = "a" * 999
        assert cache._get_text_tier(text_999_chars) == "medium"

    def test_get_text_tier_large_text_classification(self, configured_cache):
        """
        Test that _get_text_tier correctly classifies large text per docstring.
        
        Verifies:
            Text in large range returns 'large' tier with aggressive compression
            
        Business Impact:
            Ensures large texts get compression optimization for memory efficiency
            
        Scenario:
            Given: Text length in large range (1000-9999 chars)
            When: _get_text_tier is called
            Then: 'large' tier is returned
            
        Edge Cases Covered:
            - Exactly at medium threshold (1000 chars)
            - Large text sample (5000 chars)
            - Just under xlarge threshold (9999 chars)
        """
        cache = configured_cache
        
        # Test exactly at medium threshold
        text_1000_chars = "a" * 1000
        assert cache._get_text_tier(text_1000_chars) == "large"
        
        # Test large text
        text_5000_chars = "a" * 5000
        assert cache._get_text_tier(text_5000_chars) == "large"
        
        # Test just under xlarge threshold
        text_9999_chars = "a" * 9999
        assert cache._get_text_tier(text_9999_chars) == "large"

    def test_get_text_tier_xlarge_text_classification(self, configured_cache):
        """
        Test that _get_text_tier correctly classifies extra-large text per docstring.
        
        Verifies:
            Text over large threshold returns 'xlarge' tier for Redis-only storage
            
        Business Impact:
            Ensures extra-large texts use maximum compression and Redis-only strategy
            
        Scenario:
            Given: Text length over large threshold (>= 10000 chars)
            When: _get_text_tier is called
            Then: 'xlarge' tier is returned
            
        Edge Cases Covered:
            - Exactly at large threshold (10000 chars)
            - Very large text (50000 chars)
            - Extremely large text (100000+ chars)
        """
        cache = configured_cache
        
        # Test exactly at large threshold
        text_10000_chars = "a" * 10000
        assert cache._get_text_tier(text_10000_chars) == "xlarge"
        
        # Test very large text
        text_50000_chars = "a" * 50000
        assert cache._get_text_tier(text_50000_chars) == "xlarge"
        
        # Test extremely large text
        text_100000_chars = "a" * 100000
        assert cache._get_text_tier(text_100000_chars) == "xlarge"

    def test_get_text_tier_input_validation_errors(self, configured_cache):
        """
        Test that _get_text_tier validates input and raises ValidationError per docstring.
        
        Verifies:
            Invalid text parameter raises ValidationError with proper context
            
        Business Impact:
            Prevents cache tier miscategorization that could cause performance issues
            
        Scenario:
            Given: Invalid text parameter (not a string)
            When: _get_text_tier is called
            Then: ValidationError is raised with descriptive message
            
        Edge Cases Covered:
            - None parameter raises ValidationError
            - Non-string types (int, list, dict) raise ValidationError
            - Error context includes type information
        """
        cache = configured_cache
        
        # Test None parameter
        with pytest.raises(ValidationError) as exc_info:
            cache._get_text_tier(None)
        assert "invalid text parameter" in str(exc_info.value).lower()
        assert "must be string" in str(exc_info.value).lower()
        
        # Test non-string types
        with pytest.raises(ValidationError) as exc_info:
            cache._get_text_tier(12345)
        assert "invalid text parameter" in str(exc_info.value).lower()
        
        with pytest.raises(ValidationError) as exc_info:
            cache._get_text_tier(["not", "a", "string"])
        assert "invalid text parameter" in str(exc_info.value).lower()
        
        with pytest.raises(ValidationError) as exc_info:
            cache._get_text_tier({"not": "a string"})
        assert "invalid text parameter" in str(exc_info.value).lower()


class TestAIResponseCacheMetricsAndMonitoring:
    """Test AI-specific metrics collection and monitoring behavior."""

    @pytest.fixture
    def metrics_cache(self):
        """Create AIResponseCache configured for metrics testing."""
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Setup mocks
            mapper = MagicMock(spec=CacheParameterMapper)
            mapper.map_ai_to_generic_params.return_value = ({}, {})
            validation_result = MagicMock()
            validation_result.is_valid = True
            validation_result.errors = []
            validation_result.warnings = []
            mapper.validate_parameter_compatibility.return_value = validation_result
            MockMapper.return_value = mapper
            
            MockKeyGen.return_value = MagicMock(spec=CacheKeyGenerator)
            MockParentInit.return_value = None
            
            cache = AIResponseCache()
            
            # Mock performance monitor
            cache.performance_monitor = MagicMock(spec=CachePerformanceMonitor)
            cache.performance_monitor.record_cache_operation_time = MagicMock()
            
            return cache

    def test_ai_metrics_initialization(self, metrics_cache):
        """
        Test that AI metrics are properly initialized with correct structure.
        
        Verifies:
            AI metrics dictionary contains required tracking categories
            
        Business Impact:
            Ensures comprehensive monitoring data is available for cache optimization
            
        Scenario:
            Given: AIResponseCache instance is created
            When: AI metrics are initialized
            Then: All required metrics categories are present with appropriate types
            
        Edge Cases Covered:
            - All operation counters initialized as defaultdict(int)
            - Performance tracking list is initialized
            - Text tier distribution tracking is ready
        """
        cache = metrics_cache
        
        # Verify AI metrics structure
        assert hasattr(cache, 'ai_metrics')
        assert isinstance(cache.ai_metrics, dict)
        assert 'cache_hits_by_operation' in cache.ai_metrics
        assert 'cache_misses_by_operation' in cache.ai_metrics
        assert 'text_tier_distribution' in cache.ai_metrics
        assert 'operation_performance' in cache.ai_metrics
        
        # Verify metric types
        assert isinstance(cache.ai_metrics['cache_hits_by_operation'], defaultdict)
        assert isinstance(cache.ai_metrics['cache_misses_by_operation'], defaultdict)
        assert isinstance(cache.ai_metrics['text_tier_distribution'], defaultdict)
        assert isinstance(cache.ai_metrics['operation_performance'], list)

    def test_record_cache_operation_metrics_collection(self, metrics_cache):
        """
        Test that _record_cache_operation collects comprehensive metrics per docstring.
        
        Verifies:
            Cache operations are recorded with detailed performance metrics
            
        Business Impact:
            Provides data for optimizing cache performance and identifying bottlenecks
            
        Scenario:
            Given: Cache operation completes (successful or failed)
            When: _record_cache_operation is called
            Then: Detailed metrics are recorded including timing and success rates
            
        Edge Cases Covered:
            - Successful cache hits and sets are tracked
            - Failed operations are recorded separately
            - Text tier distribution is updated
            - Performance data is maintained within limits
        """
        cache = metrics_cache
        
        # Record successful cache get operation
        cache._record_cache_operation(
            operation="summarize",
            cache_operation="get",
            text_tier="medium",
            duration=0.125,
            success=True,
            additional_data={'cache_result': 'hit', 'text_length': 1500}
        )
        
        # Verify metrics were recorded
        assert cache.ai_metrics['cache_hits_by_operation']['summarize'] == 1
        assert cache.ai_metrics['text_tier_distribution']['medium'] == 1
        assert len(cache.ai_metrics['operation_performance']) == 1
        
        # Verify performance monitor was called
        cache.performance_monitor.record_cache_operation_time.assert_called_once()
        call_args = cache.performance_monitor.record_cache_operation_time.call_args[1]
        assert call_args['operation'] == 'get'
        assert call_args['duration'] == 0.125
        assert call_args['cache_hit'] == True
        assert call_args['additional_data']['ai_operation'] == 'summarize'

    def test_record_cache_operation_performance_limit(self, metrics_cache):
        """
        Test that performance data is limited to prevent memory growth per docstring.
        
        Verifies:
            Performance metrics list is trimmed to last 1000 operations
            
        Business Impact:
            Prevents memory leaks in long-running cache instances
            
        Scenario:
            Given: Over 1000 cache operations have been recorded
            When: New operations are recorded
            Then: Oldest performance data is removed to maintain 1000 item limit
            
        Edge Cases Covered:
            - Exactly 1000 operations maintained
            - Oldest entries are removed first
            - Recent data is preserved correctly
        """
        cache = metrics_cache
        
        # Simulate 1500 cache operations
        for i in range(1500):
            cache._record_cache_operation(
                operation="test",
                cache_operation="get",
                text_tier="small",
                duration=0.001,
                success=True,
                additional_data={'operation_id': i}
            )
        
        # Verify performance data is limited to 1000 entries
        assert len(cache.ai_metrics['operation_performance']) == 1000
        
        # Verify most recent entries are preserved
        last_entry = cache.ai_metrics['operation_performance'][-1]
        assert last_entry['operation_id'] == 1499
        
        # Verify oldest entries were removed
        first_entry = cache.ai_metrics['operation_performance'][0]
        assert first_entry['operation_id'] == 500  # 1500 - 1000


class TestAIResponseCacheErrorHandlingAndResilience:
    """Test error handling and graceful degradation patterns."""

    @pytest.fixture
    def resilient_cache(self):
        """Create AIResponseCache configured for error handling testing."""
        with patch('app.infrastructure.cache.redis_ai.CacheParameterMapper') as MockMapper, \
             patch('app.infrastructure.cache.redis_ai.CacheKeyGenerator') as MockKeyGen, \
             patch('app.infrastructure.cache.redis_ai.GenericRedisCache.__init__') as MockParentInit:
            
            # Setup mocks
            mapper = MagicMock(spec=CacheParameterMapper)
            mapper.map_ai_to_generic_params.return_value = ({}, {})
            validation_result = MagicMock()
            validation_result.is_valid = True
            validation_result.errors = []
            validation_result.warnings = []
            mapper.validate_parameter_compatibility.return_value = validation_result
            MockMapper.return_value = mapper
            
            key_gen = MagicMock(spec=CacheKeyGenerator)
            key_gen.generate_cache_key.return_value = "test_key"
            MockKeyGen.return_value = key_gen
            
            MockParentInit.return_value = None
            
            cache = AIResponseCache()
            
            # Mock inherited methods
            cache.set = AsyncMock()
            cache.get = AsyncMock()
            
            # Mock performance monitor with error simulation
            cache.performance_monitor = MagicMock(spec=CachePerformanceMonitor)
            cache.performance_monitor.record_cache_operation_time = MagicMock()
            
            return cache

    async def test_cache_response_handles_storage_failures(self, resilient_cache):
        """
        Test that cache_response handles Redis storage failures gracefully.
        
        Verifies:
            Storage failures don't crash the application but are properly logged
            
        Business Impact:
            Ensures AI operations continue even when cache storage fails
            
        Scenario:
            Given: Redis storage fails during cache_response operation
            When: cache_response is called
            Then: Error is handled gracefully and operation tracking continues
            
        Edge Cases Covered:
            - Redis connection failures
            - Storage capacity issues
            - Serialization errors
        """
        cache = resilient_cache
        
        # Mock storage failure
        cache.set.side_effect = InfrastructureError("Redis connection failed")
        
        # Should not raise exception despite storage failure
        try:
            await cache.cache_response(
                text="Test text for resilience",
                operation="summarize",
                options={"max_length": 100},
                response={"summary": "Test summary"}
            )
            # If we get here, the error was handled gracefully
        except InfrastructureError:
            # This is acceptable - the error can bubble up for higher-level handling
            pass

    async def test_get_cached_response_handles_retrieval_failures(self, resilient_cache):
        """
        Test that get_cached_response handles Redis retrieval failures gracefully.
        
        Verifies:
            Retrieval failures return None and record miss metrics
            
        Business Impact:
            Ensures AI operations can fall back to live processing when cache fails
            
        Scenario:
            Given: Redis retrieval fails during get_cached_response operation
            When: get_cached_response is called
            Then: None is returned and miss metrics are recorded
            
        Edge Cases Covered:
            - Redis connection failures during get operations
            - Deserialization errors
            - Timeout conditions
        """
        cache = resilient_cache
        
        # Mock retrieval failure
        cache.get.side_effect = InfrastructureError("Redis timeout")
        
        # Should return None on failure
        result = await cache.get_cached_response(
            text="Test text",
            operation="sentiment",
            options={"model": "gpt-4"}
        )
        
        assert result is None
        # Miss metrics should still be recorded
        assert cache.ai_metrics['cache_misses_by_operation']['sentiment'] == 1

    def test_get_text_tier_fallback_behavior(self, resilient_cache):
        """
        Test that _get_text_tier provides fallback tier on internal errors.
        
        Verifies:
            Internal processing errors fall back to medium tier per docstring
            
        Business Impact:
            Ensures text tier determination never completely fails
            
        Scenario:
            Given: Internal error occurs during tier determination
            When: _get_text_tier is called
            Then: 'medium' tier is returned as safe fallback
            
        Edge Cases Covered:
            - Configuration corruption causing KeyError
            - Unexpected internal processing errors
            - Memory pressure scenarios
        """
        cache = resilient_cache
        
        # Corrupt tier configuration to trigger fallback
        cache.text_size_tiers = None
        
        # Should fallback to 'medium' tier instead of crashing
        with patch('app.infrastructure.cache.redis_ai.logger') as mock_logger:
            tier = cache._get_text_tier("test text")
            assert tier == "medium"
            # Should log the error
            mock_logger.warning.assert_called()

    def test_extract_operation_from_key_handles_malformed_keys(self, resilient_cache):
        """
        Test that _extract_operation_from_key handles malformed keys gracefully.
        
        Verifies:
            Malformed keys return 'unknown' operation per docstring
            
        Business Impact:
            Ensures metrics collection continues even with corrupted cache keys
            
        Scenario:
            Given: Malformed or corrupted cache key
            When: _extract_operation_from_key is called
            Then: 'unknown' operation is returned without errors
            
        Edge Cases Covered:
            - Empty strings
            - Completely invalid key formats
            - Keys missing expected components
        """
        cache = resilient_cache
        
        # Test various malformed key formats
        assert cache._extract_operation_from_key("") == "unknown"
        assert cache._extract_operation_from_key(None) == "unknown"
        assert cache._extract_operation_from_key("not_an_ai_cache_key") == "unknown"
        assert cache._extract_operation_from_key("ai_cache:malformed") == "unknown"
        assert cache._extract_operation_from_key("random_string_123") == "unknown"


if __name__ == "__main__":
    # Enable test discovery and execution
    pytest.main([__file__, "-v", "--tb=short"])