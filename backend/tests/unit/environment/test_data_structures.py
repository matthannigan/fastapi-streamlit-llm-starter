"""
Tests for environment detection data structures and enums.

Tests the core data types used in environment detection including enums,
NamedTuples, and dataclasses. Focuses on structure validation, defaults,
string representations, and immutability behavior.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentSignal,
    EnvironmentInfo,
    DetectionConfig,
    EnvironmentDetector,
    get_environment_info,
    is_production_environment,
    is_development_environment,
)


class TestEnvironmentEnum:
    """
    Test suite for Environment enum values and string behavior.

    Scope:
        - Environment enum value consistency and string conversion
        - Integration with configuration systems requiring string values

    Business Critical:
        Environment enum values are used throughout infrastructure services
        for configuration selection and feature enabling
    """

    def test_environment_enum_values_match_strings(self):
        """
        Test that Environment enum values match their string representations.

        Verifies:
            Each Environment enum member's value property matches its string conversion.

        Business Impact:
            Ensures consistent string representation for configuration files and logging.

        Scenario:
            Given: All Environment enum members
            When: Converting enum to string and accessing value property
            Then: Both representations match the expected environment name

        Fixtures Used:
            - None (testing enum behavior only)
        """
        # Given: All Environment enum members
        environments = [
            Environment.DEVELOPMENT,
            Environment.TESTING,
            Environment.STAGING,
            Environment.PRODUCTION,
            Environment.UNKNOWN
        ]

        # When: Converting enum to string and accessing value property
        # Then: Both representations match the expected environment name
        for env in environments:
            # str() returns the enum value directly since it's a str enum
            assert env.value == env.name.lower()
            # Test that the value matches expected string
            assert env == env.value

    def test_environment_enum_contains_all_expected_values(self):
        """
        Test that Environment enum contains all required environment classifications.

        Verifies:
            All documented environment types are available as enum members.

        Business Impact:
            Ensures all deployment contexts have corresponding enum values.

        Scenario:
            Given: The Environment enum class
            When: Checking for required environment classifications
            Then: DEVELOPMENT, TESTING, STAGING, PRODUCTION, and UNKNOWN are present

        Fixtures Used:
            - None (testing enum completeness only)
        """
        # Given: The Environment enum class
        # When: Checking for required environment classifications
        # Then: DEVELOPMENT, TESTING, STAGING, PRODUCTION, and UNKNOWN are present
        expected_environments = {
            'DEVELOPMENT',
            'TESTING',
            'STAGING',
            'PRODUCTION',
            'UNKNOWN'
        }

        actual_environments = {env.name for env in Environment}
        assert actual_environments == expected_environments

        # Verify specific enum access
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.UNKNOWN.value == "unknown"

    def test_environment_enum_supports_equality_comparison(self):
        """
        Test that Environment enum members support equality comparison.

        Verifies:
            Environment enum values can be compared for equality with other enum instances.

        Business Impact:
            Enables reliable conditional logic in infrastructure configuration.

        Scenario:
            Given: Two Environment enum instances with same value
            When: Comparing them for equality
            Then: Comparison returns True for identical values, False for different values

        Fixtures Used:
            - None (testing enum behavior only)
        """
        # Given: Two Environment enum instances with same value
        env1 = Environment.PRODUCTION
        env2 = Environment.PRODUCTION
        different_env = Environment.DEVELOPMENT

        # When: Comparing them for equality
        # Then: Comparison returns True for identical values, False for different values
        assert env1 == env2
        assert env1 != different_env
        assert env2 != different_env

        # Test equality with string values
        assert env1 == "production"
        assert env1 != "development"

        # Test identity (same object reference)
        assert env1 is Environment.PRODUCTION


class TestFeatureContextEnum:
    """
    Test suite for FeatureContext enum values and feature-specific behavior.

    Scope:
        - FeatureContext enum consistency and usage patterns
        - Feature-specific detection context validation

    Business Critical:
        Feature contexts control specialized environment detection logic
        that affects AI, security, cache, and resilience configurations
    """

    def test_feature_context_enum_values_match_strings(self):
        """
        Test that FeatureContext enum values match their string representations.

        Verifies:
            Each FeatureContext enum member's value property matches expected string format.

        Business Impact:
            Ensures consistent context identification in feature-specific detection.

        Scenario:
            Given: All FeatureContext enum members
            When: Converting enum to string and accessing value property
            Then: Both representations match expected feature context names

        Fixtures Used:
            - None (testing enum behavior only)
        """
        # Given: All FeatureContext enum members
        contexts = [
            FeatureContext.AI_ENABLED,
            FeatureContext.SECURITY_ENFORCEMENT,
            FeatureContext.CACHE_OPTIMIZATION,
            FeatureContext.RESILIENCE_STRATEGY,
            FeatureContext.DEFAULT
        ]

        # When: Converting enum to string and accessing value property
        # Then: Both representations match expected feature context names
        for context in contexts:
            # Test that the value matches the enum value for string enum
            assert context == context.value

        # Verify specific expected values
        assert FeatureContext.AI_ENABLED.value == "ai_enabled"
        assert FeatureContext.SECURITY_ENFORCEMENT.value == "security_enforcement"
        assert FeatureContext.CACHE_OPTIMIZATION.value == "cache_optimization"
        assert FeatureContext.RESILIENCE_STRATEGY.value == "resilience_strategy"
        assert FeatureContext.DEFAULT.value == "default"

    def test_feature_context_enum_contains_all_expected_contexts(self):
        """
        Test that FeatureContext enum contains all required feature contexts.

        Verifies:
            All documented feature contexts are available as enum members.

        Business Impact:
            Ensures all infrastructure features have corresponding context values.

        Scenario:
            Given: The FeatureContext enum class
            When: Checking for required feature contexts
            Then: AI_ENABLED, SECURITY_ENFORCEMENT, CACHE_OPTIMIZATION,
                  RESILIENCE_STRATEGY, and DEFAULT are present

        Fixtures Used:
            - None (testing enum completeness only)
        """
        # Given: The FeatureContext enum class
        # When: Checking for required feature contexts
        # Then: AI_ENABLED, SECURITY_ENFORCEMENT, CACHE_OPTIMIZATION, RESILIENCE_STRATEGY, and DEFAULT are present
        expected_contexts = {
            'AI_ENABLED',
            'SECURITY_ENFORCEMENT',
            'CACHE_OPTIMIZATION',
            'RESILIENCE_STRATEGY',
            'DEFAULT'
        }

        actual_contexts = {context.name for context in FeatureContext}
        assert actual_contexts == expected_contexts

        # Verify each context is accessible
        assert hasattr(FeatureContext, 'AI_ENABLED')
        assert hasattr(FeatureContext, 'SECURITY_ENFORCEMENT')
        assert hasattr(FeatureContext, 'CACHE_OPTIMIZATION')
        assert hasattr(FeatureContext, 'RESILIENCE_STRATEGY')
        assert hasattr(FeatureContext, 'DEFAULT')

    def test_feature_context_default_is_baseline_context(self):
        """
        Test that FeatureContext.DEFAULT represents baseline environment detection.

        Verifies:
            DEFAULT feature context serves as the standard detection mode.

        Business Impact:
            Provides reliable baseline behavior for standard environment detection.

        Scenario:
            Given: FeatureContext.DEFAULT enum value
            When: Using it as feature context parameter
            Then: It represents standard detection without feature-specific overrides

        Fixtures Used:
            - None (testing enum behavior only)
        """
        # Given: FeatureContext.DEFAULT enum value
        default_context = FeatureContext.DEFAULT

        # When: Using it as feature context parameter
        # Then: It represents standard detection without feature-specific overrides
        assert default_context.value == "default"
        assert default_context.name == "DEFAULT"

        # Verify DEFAULT is distinct from other contexts
        assert default_context != FeatureContext.AI_ENABLED
        assert default_context != FeatureContext.SECURITY_ENFORCEMENT
        assert default_context != FeatureContext.CACHE_OPTIMIZATION
        assert default_context != FeatureContext.RESILIENCE_STRATEGY

        # Verify equality works
        assert default_context == FeatureContext.DEFAULT
        assert default_context == "default"


class TestEnvironmentSignalStructure:
    """
    Test suite for EnvironmentSignal NamedTuple structure and behavior.

    Scope:
        - EnvironmentSignal creation and attribute access
        - Signal confidence scoring and reasoning validation

    Business Critical:
        Environment signals are the foundation of detection confidence scoring
        and debugging capabilities throughout the detection process
    """

    def test_environment_signal_creation_with_all_fields(self):
        """
        Test that EnvironmentSignal can be created with all required fields.

        Verifies:
            EnvironmentSignal accepts all documented fields during construction.

        Business Impact:
            Ensures signal collection can capture complete detection evidence.

        Scenario:
            Given: Valid signal parameters (source, value, environment, confidence, reasoning)
            When: Creating EnvironmentSignal instance
            Then: All fields are accessible and contain expected values

        Fixtures Used:
            - None (testing data structure creation only)
        """
        # Given: Valid signal parameters
        source = "ENVIRONMENT"
        value = "production"
        environment = Environment.PRODUCTION
        confidence = 0.95
        reasoning = "Explicit environment from ENVIRONMENT=production"

        # When: Creating EnvironmentSignal instance
        signal = EnvironmentSignal(
            source=source,
            value=value,
            environment=environment,
            confidence=confidence,
            reasoning=reasoning
        )

        # Then: All fields are accessible and contain expected values
        assert signal.source == source
        assert signal.value == value
        assert signal.environment == environment
        assert signal.confidence == confidence
        assert signal.reasoning == reasoning

    def test_environment_signal_confidence_range_validation(self):
        """
        Test that EnvironmentSignal accepts confidence values in valid range.

        Verifies:
            Confidence scores can be set within documented 0.0-1.0 range.

        Business Impact:
            Ensures confidence scoring provides meaningful reliability assessment.

        Scenario:
            Given: EnvironmentSignal with confidence values at boundaries
            When: Creating signals with confidence 0.0, 0.5, and 1.0
            Then: All confidence values are preserved accurately

        Fixtures Used:
            - None (testing data structure validation only)
        """
        # Given: EnvironmentSignal with confidence values at boundaries
        # When: Creating signals with confidence 0.0, 0.5, and 1.0
        confidence_values = [0.0, 0.5, 1.0]

        for confidence in confidence_values:
            signal = EnvironmentSignal(
                source="test_source",
                value="test_value",
                environment=Environment.DEVELOPMENT,
                confidence=confidence,
                reasoning=f"Test reasoning with confidence {confidence}"
            )

            # Then: All confidence values are preserved accurately
            assert signal.confidence == confidence
            assert 0.0 <= signal.confidence <= 1.0

        # Test additional valid confidence values
        valid_confidences = [0.01, 0.25, 0.33, 0.67, 0.75, 0.99]
        for conf in valid_confidences:
            signal = EnvironmentSignal(
                source="test",
                value="test",
                environment=Environment.TESTING,
                confidence=conf,
                reasoning="test"
            )
            assert signal.confidence == conf

    def test_environment_signal_immutability(self):
        """
        Test that EnvironmentSignal behaves as immutable NamedTuple.

        Verifies:
            EnvironmentSignal fields cannot be modified after creation.

        Business Impact:
            Ensures signal integrity throughout detection and analysis process.

        Scenario:
            Given: Created EnvironmentSignal instance
            When: Attempting to modify field values
            Then: Modification attempts raise AttributeError

        Fixtures Used:
            - None (testing data structure immutability only)
        """
        # Given: Created EnvironmentSignal instance
        signal = EnvironmentSignal(
            source="ENVIRONMENT",
            value="production",
            environment=Environment.PRODUCTION,
            confidence=0.95,
            reasoning="Test reasoning"
        )

        # When: Attempting to modify field values
        # Then: Modification attempts raise AttributeError
        with pytest.raises(AttributeError):
            signal.source = "NEW_SOURCE"  # type: ignore

        with pytest.raises(AttributeError):
            signal.value = "new_value"  # type: ignore

        with pytest.raises(AttributeError):
            signal.environment = Environment.DEVELOPMENT  # type: ignore

        with pytest.raises(AttributeError):
            signal.confidence = 0.5  # type: ignore

        with pytest.raises(AttributeError):
            signal.reasoning = "new reasoning"  # type: ignore

        # Verify original values are preserved
        assert signal.source == "ENVIRONMENT"
        assert signal.value == "production"
        assert signal.environment == Environment.PRODUCTION
        assert signal.confidence == 0.95
        assert signal.reasoning == "Test reasoning"


class TestEnvironmentInfoStructure:
    """
    Test suite for EnvironmentInfo dataclass structure and behavior.

    Scope:
        - EnvironmentInfo creation with required and optional fields
        - String representation and data access patterns

    Business Critical:
        EnvironmentInfo is the primary result object returned by all detection
        methods and used throughout infrastructure for configuration decisions
    """

    def test_environment_info_creation_with_required_fields(self):
        """
        Test that EnvironmentInfo can be created with all required fields.

        Verifies:
            EnvironmentInfo accepts all mandatory fields for complete detection results.

        Business Impact:
            Ensures detection results provide complete information for configuration decisions.

        Scenario:
            Given: Required EnvironmentInfo fields (environment, confidence, reasoning, detected_by)
            When: Creating EnvironmentInfo instance
            Then: All required fields are accessible and contain expected values

        Fixtures Used:
            - None (testing data structure creation only)
        """
        # Given: Required EnvironmentInfo fields
        environment = Environment.PRODUCTION
        confidence = 0.95
        reasoning = "Explicit environment variable"
        detected_by = "ENVIRONMENT"

        # When: Creating EnvironmentInfo instance
        env_info = EnvironmentInfo(
            environment=environment,
            confidence=confidence,
            reasoning=reasoning,
            detected_by=detected_by
        )

        # Then: All required fields are accessible and contain expected values
        assert env_info.environment == environment
        assert env_info.confidence == confidence
        assert env_info.reasoning == reasoning
        assert env_info.detected_by == detected_by

        # Verify all fields are accessible
        assert hasattr(env_info, 'environment')
        assert hasattr(env_info, 'confidence')
        assert hasattr(env_info, 'reasoning')
        assert hasattr(env_info, 'detected_by')
        assert hasattr(env_info, 'feature_context')
        assert hasattr(env_info, 'additional_signals')
        assert hasattr(env_info, 'metadata')

    def test_environment_info_optional_fields_default_correctly(self):
        """
        Test that EnvironmentInfo optional fields have appropriate defaults.

        Verifies:
            Optional fields (feature_context, additional_signals, metadata) use correct defaults.

        Business Impact:
            Ensures detection results work correctly with minimal configuration.

        Scenario:
            Given: EnvironmentInfo created with only required fields
            When: Accessing optional fields
            Then: feature_context defaults to DEFAULT, lists default to empty, dict defaults to empty

        Fixtures Used:
            - None (testing data structure defaults only)
        """
        # Given: EnvironmentInfo created with only required fields
        env_info = EnvironmentInfo(
            environment=Environment.DEVELOPMENT,
            confidence=0.80,
            reasoning="Test reasoning",
            detected_by="test_source"
        )

        # When: Accessing optional fields
        # Then: feature_context defaults to DEFAULT, lists default to empty, dict defaults to empty
        assert env_info.feature_context == FeatureContext.DEFAULT
        assert env_info.additional_signals == []
        assert env_info.metadata == {}

        # Verify types are correct
        assert isinstance(env_info.feature_context, FeatureContext)
        assert isinstance(env_info.additional_signals, list)
        assert isinstance(env_info.metadata, dict)

        # Verify lists/dicts are empty but mutable
        env_info.additional_signals.append(EnvironmentSignal(
            source="test",
            value="test",
            environment=Environment.TESTING,
            confidence=0.5,
            reasoning="test"
        ))
        assert len(env_info.additional_signals) == 1

        env_info.metadata['test'] = 'value'
        assert env_info.metadata['test'] == 'value'

    def test_environment_info_string_representation(self):
        """
        Test that EnvironmentInfo provides meaningful string representation.

        Verifies:
            __str__ method returns formatted environment and confidence information.

        Business Impact:
            Enables clear logging and debugging of environment detection results.

        Scenario:
            Given: EnvironmentInfo instance with known environment and confidence
            When: Converting to string representation
            Then: String contains environment name and formatted confidence score

        Fixtures Used:
            - None (testing data structure string behavior only)
        """
        # Given: EnvironmentInfo instance with known environment and confidence
        env_info = EnvironmentInfo(
            environment=Environment.PRODUCTION,
            confidence=0.95,
            reasoning="Test reasoning",
            detected_by="test_source"
        )

        # When: Converting to string representation
        str_representation = str(env_info)

        # Then: String contains environment name and formatted confidence score
        assert "production" in str_representation
        assert "0.95" in str_representation
        assert "confidence:" in str_representation

        # Test exact format matches implementation
        expected = "production (confidence: 0.95)"
        assert str_representation == expected

    def test_environment_info_confidence_formatting(self):
        """
        Test that EnvironmentInfo formats confidence scores consistently.

        Verifies:
            Confidence scores are formatted to appropriate decimal places in string output.

        Business Impact:
            Provides consistent confidence reporting across all detection contexts.

        Scenario:
            Given: EnvironmentInfo with various confidence values
            When: Converting to string representation
            Then: Confidence is formatted to 2 decimal places consistently

        Fixtures Used:
            - None (testing data structure formatting only)
        """
        # Given: EnvironmentInfo with various confidence values
        confidence_test_cases = [
            (1.0, "1.00"),
            (0.95, "0.95"),
            (0.666666, "0.67"),
            (0.1, "0.10"),
            (0.0, "0.00"),
            (0.333333, "0.33")
        ]

        for confidence, expected_formatted in confidence_test_cases:
            # When: Converting to string representation
            env_info = EnvironmentInfo(
                environment=Environment.TESTING,
                confidence=confidence,
                reasoning="Test reasoning",
                detected_by="test_source"
            )
            str_representation = str(env_info)

            # Then: Confidence is formatted to 2 decimal places consistently
            assert expected_formatted in str_representation
            assert f"testing (confidence: {expected_formatted})" == str_representation


class TestDetectionConfigStructure:
    """
    Test suite for DetectionConfig dataclass structure and defaults.

    Scope:
        - DetectionConfig creation with default and custom values
        - Pattern list validation and precedence ordering

    Business Critical:
        DetectionConfig controls how environment detection logic operates
        and must provide sensible defaults while supporting customization
    """

    def test_detection_config_default_creation(self):
        """
        Test that DetectionConfig can be created with default values.

        Verifies:
            DetectionConfig provides sensible defaults for all configuration options.

        Business Impact:
            Ensures environment detection works out-of-the-box without configuration.

        Scenario:
            Given: No configuration parameters
            When: Creating DetectionConfig instance
            Then: All configuration lists are populated with default patterns and precedence

        Fixtures Used:
            - None (testing data structure creation only)
        """
        # Given: No configuration parameters
        # When: Creating DetectionConfig instance
        config = DetectionConfig()

        # Then: All configuration lists are populated with default patterns and precedence
        assert isinstance(config.env_var_precedence, list)
        assert len(config.env_var_precedence) > 0
        assert 'ENVIRONMENT' in config.env_var_precedence

        assert isinstance(config.development_patterns, list)
        assert len(config.development_patterns) > 0

        assert isinstance(config.staging_patterns, list)
        assert len(config.staging_patterns) > 0

        assert isinstance(config.production_patterns, list)
        assert len(config.production_patterns) > 0

        assert isinstance(config.development_indicators, list)
        assert len(config.development_indicators) > 0

        assert isinstance(config.production_indicators, list)
        assert len(config.production_indicators) > 0

        assert isinstance(config.feature_contexts, dict)
        assert len(config.feature_contexts) > 0

    def test_detection_config_env_var_precedence_order(self):
        """
        Test that DetectionConfig provides environment variable precedence ordering.

        Verifies:
            env_var_precedence list contains expected variables in priority order.

        Business Impact:
            Ensures highest priority environment variables are checked first.

        Scenario:
            Given: Default DetectionConfig instance
            When: Accessing env_var_precedence field
            Then: List contains ENVIRONMENT first, followed by framework-specific variables

        Fixtures Used:
            - None (testing configuration defaults only)
        """
        # Given: Default DetectionConfig instance
        config = DetectionConfig()

        # When: Accessing env_var_precedence field
        precedence = config.env_var_precedence

        # Then: List contains ENVIRONMENT first, followed by framework-specific variables
        assert precedence[0] == 'ENVIRONMENT'
        assert 'NODE_ENV' in precedence
        assert 'FLASK_ENV' in precedence
        assert 'APP_ENV' in precedence
        assert 'ENV' in precedence

        # Verify ENVIRONMENT has highest priority (first in list)
        environment_index = precedence.index('ENVIRONMENT')
        assert environment_index == 0

        # Verify expected framework variables are present
        expected_vars = ['ENVIRONMENT', 'NODE_ENV', 'FLASK_ENV', 'APP_ENV', 'ENV']
        for var in expected_vars:
            assert var in precedence

    def test_detection_config_pattern_lists_populated(self):
        """
        Test that DetectionConfig provides default patterns for all environments.

        Verifies:
            Development, staging, and production pattern lists contain useful defaults.

        Business Impact:
            Ensures hostname and service name patterns can identify environments.

        Scenario:
            Given: Default DetectionConfig instance
            When: Accessing pattern lists (development_patterns, staging_patterns, production_patterns)
            Then: Each list contains relevant regex patterns for environment identification

        Fixtures Used:
            - None (testing configuration defaults only)
        """
        # Given: Default DetectionConfig instance
        config = DetectionConfig()

        # When: Accessing pattern lists
        dev_patterns = config.development_patterns
        staging_patterns = config.staging_patterns
        prod_patterns = config.production_patterns

        # Then: Each list contains relevant regex patterns for environment identification
        # Development patterns
        assert len(dev_patterns) > 0
        assert any('dev' in pattern for pattern in dev_patterns)
        assert any('local' in pattern for pattern in dev_patterns)
        assert any('test' in pattern for pattern in dev_patterns)

        # Staging patterns
        assert len(staging_patterns) > 0
        assert any('stag' in pattern for pattern in staging_patterns)
        assert any('uat' in pattern for pattern in staging_patterns)

        # Production patterns
        assert len(prod_patterns) > 0
        assert any('prod' in pattern for pattern in prod_patterns)
        assert any('live' in pattern for pattern in prod_patterns)

        # Verify patterns are valid regex (basic check)
        import re
        for pattern_list in [dev_patterns, staging_patterns, prod_patterns]:
            for pattern in pattern_list:
                # This should not raise an exception if pattern is valid
                re.compile(pattern)

    def test_detection_config_custom_field_override(self):
        """
        Test that DetectionConfig accepts custom field overrides.

        Verifies:
            Custom patterns and precedence can override defaults during creation.

        Business Impact:
            Enables specialized deployment scenarios with custom detection logic.

        Scenario:
            Given: Custom configuration values for patterns and precedence
            When: Creating DetectionConfig with custom values
            Then: Custom values override defaults while preserving structure

        Fixtures Used:
            - None (testing data structure customization only)
        """
        # Given: Custom configuration values for patterns and precedence
        custom_precedence = ['CUSTOM_ENV', 'ORG_ENV', 'ENVIRONMENT']
        custom_dev_patterns = [r'.*custom-dev.*', r'.*org-local.*']
        custom_prod_patterns = [r'.*custom-prod.*', r'.*org-live.*']
        custom_indicators = ['CUSTOM_DEBUG=true', '.custom-env']

        # When: Creating DetectionConfig with custom values
        config = DetectionConfig(
            env_var_precedence=custom_precedence,
            development_patterns=custom_dev_patterns,
            production_patterns=custom_prod_patterns,
            development_indicators=custom_indicators
        )

        # Then: Custom values override defaults while preserving structure
        assert config.env_var_precedence == custom_precedence
        assert config.development_patterns == custom_dev_patterns
        assert config.production_patterns == custom_prod_patterns
        assert config.development_indicators == custom_indicators

        # Verify non-overridden fields still have defaults
        assert len(config.staging_patterns) > 0  # Not overridden, should have defaults
        assert len(config.production_indicators) > 0  # Not overridden, should have defaults
        assert len(config.feature_contexts) > 0  # Not overridden, should have defaults

    def test_detection_config_feature_contexts_structure(self):
        """
        Test that DetectionConfig provides feature context configuration structure.

        Verifies:
            feature_contexts field supports feature-specific configuration overrides.

        Business Impact:
            Enables feature-aware detection with specialized environment variable handling.

        Scenario:
            Given: Default DetectionConfig instance
            When: Accessing feature_contexts field
            Then: Dictionary structure supports FeatureContext keys with configuration values

        Fixtures Used:
            - None (testing configuration structure only)
        """
        # Given: Default DetectionConfig instance
        config = DetectionConfig()

        # When: Accessing feature_contexts field
        feature_contexts = config.feature_contexts

        # Then: Dictionary structure supports FeatureContext keys with configuration values
        assert isinstance(feature_contexts, dict)
        assert len(feature_contexts) > 0

        # Verify expected feature contexts are present
        assert FeatureContext.AI_ENABLED in feature_contexts
        assert FeatureContext.SECURITY_ENFORCEMENT in feature_contexts

        # Verify AI context configuration
        ai_config = feature_contexts[FeatureContext.AI_ENABLED]
        assert isinstance(ai_config, dict)
        assert 'environment_var' in ai_config
        assert ai_config['environment_var'] == 'ENABLE_AI_CACHE'
        assert 'true_values' in ai_config
        assert 'preset_modifier' in ai_config
        assert ai_config['preset_modifier'] == 'ai-'

        # Verify security context configuration
        security_config = feature_contexts[FeatureContext.SECURITY_ENFORCEMENT]
        assert isinstance(security_config, dict)
        assert 'environment_var' in security_config
        assert security_config['environment_var'] == 'ENFORCE_AUTH'
        assert 'production_override' in security_config
        assert security_config['production_override'] is True

        # Test that custom feature contexts can be added
        config.feature_contexts[FeatureContext.CACHE_OPTIMIZATION] = {
            'environment_var': 'ENABLE_CACHE',
            'custom_setting': True
        }
        assert FeatureContext.CACHE_OPTIMIZATION in config.feature_contexts
