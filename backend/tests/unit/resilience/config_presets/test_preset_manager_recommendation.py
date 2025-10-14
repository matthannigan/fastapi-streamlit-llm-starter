"""
Test suite for PresetManager environment-aware preset recommendation.

Verifies that the PresetManager correctly detects environments and recommends
appropriate presets with confidence scoring and reasoning.
"""

import pytest
from app.infrastructure.resilience.config_presets import (
    PresetManager,
    EnvironmentRecommendation
)


class TestPresetManagerRecommendation:
    """
    Test suite for recommend_preset() method behavior.
    
    Scope:
        - recommend_preset() for common environment names
        - Auto-detection when environment=None
        - Environment name normalization and abbreviations
        - Fallback to 'simple' for unknown environments
        
    Business Critical:
        Accurate environment detection and preset recommendation enables
        automated deployment with appropriate resilience configurations.
        
    Test Strategy:
        - Test exact environment name matching
        - Test environment abbreviation handling
        - Test auto-detection behavior
        - Test fallback for unknown environments
    """
    
    def test_recommend_preset_for_production_environment(self):
        """
        Test that recommend_preset() returns 'production' for production environment.

        Verifies:
            The recommend_preset() method returns "production" preset name
            when called with environment="production" as documented in method contract.

        Business Impact:
            Ensures production deployments automatically receive high-reliability
            configuration with conservative strategies.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset("production") is called
            Then: Method returns "production" string
            And: Recommendation matches documented environment contexts

        Fixtures Used:
            - None (tests recommendation logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset("production") is called
        result = manager.recommend_preset("production")

        # Then: Method returns "production" string
        assert result == "production"
    
    def test_recommend_preset_for_development_environment(self):
        """
        Test that recommend_preset() returns 'development' for development environment.

        Verifies:
            The recommend_preset() method returns "development" preset name
            when called with environment="development".

        Business Impact:
            Ensures development environments automatically receive fast-fail
            configuration optimized for rapid iteration.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset("development") is called
            Then: Method returns "development" string
            And: Recommendation uses aggressive strategy

        Fixtures Used:
            - None (tests recommendation logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset("development") is called
        result = manager.recommend_preset("development")

        # Then: Method returns "development" string
        assert result == "development"
    
    def test_recommend_preset_for_staging_environment(self):
        """
        Test that recommend_preset() returns appropriate preset for staging.

        Verifies:
            The recommend_preset() method returns a suitable preset
            (typically 'production') for staging environments.

        Business Impact:
            Ensures staging environments use production-like configurations
            for accurate production behavior testing.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset("staging") is called
            Then: Method returns "production" string
            And: Staging uses production-grade resilience settings

        Fixtures Used:
            - None (tests recommendation logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset("staging") is called
        result = manager.recommend_preset("staging")

        # Then: Method returns "production" string (staging mirrors production)
        assert result == "production"
    
    def test_recommend_preset_with_auto_detection(self, monkeypatch):
        """
        Test that recommend_preset() auto-detects environment when None provided.

        Verifies:
            The recommend_preset() method uses unified environment detection
            when environment parameter is None as documented in Args section.

        Business Impact:
            Enables zero-configuration preset selection based on
            deployment environment variables and indicators.

        Scenario:
            Given: An initialized PresetManager instance
            And: Environment variables indicating production deployment
            When: recommend_preset(None) is called
            Then: Method returns appropriate preset based on detection
            And: Auto-detection uses unified environment detection service

        Fixtures Used:
            - monkeypatch: Sets up environment variables for detection
        """
        # Given: Environment variables indicating production deployment
        monkeypatch.setenv("ENVIRONMENT", "production")

        # And: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset(None) is called
        result = manager.recommend_preset(None)

        # Then: Method returns appropriate preset based on detection
        # (production environment should map to production preset)
        assert result == "production"
    
    def test_recommend_preset_handles_case_insensitive_environment(self):
        """
        Test that recommend_preset() handles case-insensitive environment names.

        Verifies:
            The recommend_preset() method normalizes environment names
            and handles variations in casing (Production, PRODUCTION, production).

        Business Impact:
            Ensures reliable recommendations regardless of environment
            name casing conventions in different deployment systems.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset("PRODUCTION") is called
            Then: Method returns "production" string
            And: Recommendation is same as lowercase "production"

        Fixtures Used:
            - None (tests normalization logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset("PRODUCTION") is called
        result = manager.recommend_preset("PRODUCTION")

        # Then: Method returns "production" string (case-insensitive)
        assert result == "production"
    
    def test_recommend_preset_handles_environment_abbreviations(self):
        """
        Test that recommend_preset() handles common environment abbreviations.

        Verifies:
            The recommend_preset() method recognizes common abbreviations
            like "dev", "prod", "test" as documented in method contract.

        Business Impact:
            Provides flexible environment naming supporting different
            organizational conventions and deployment tools.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset("dev") is called
            Then: Method returns "development" string
            And: Abbreviation is correctly expanded

        Fixtures Used:
            - None (tests abbreviation handling)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset("dev") is called
        result = manager.recommend_preset("dev")

        # Then: Method returns "development" string
        assert result == "development"

        # Test other common abbreviations
        assert manager.recommend_preset("prod") == "production"
        assert manager.recommend_preset("test") == "development"
        assert manager.recommend_preset("stage") == "production"
    
    def test_recommend_preset_returns_simple_for_unknown_environment(self):
        """
        Test that recommend_preset() returns 'simple' for unknown environments.

        Verifies:
            The recommend_preset() method returns "simple" as fallback
            when environment doesn't match known patterns.

        Business Impact:
            Provides safe default configuration for unknown deployment
            scenarios, preventing configuration failures.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset("unknown_env_12345") is called
            Then: Method returns "simple" string
            And: Fallback preset provides balanced configuration

        Fixtures Used:
            - None (tests fallback behavior)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset("unknown_env_12345") is called
        result = manager.recommend_preset("unknown_env_12345")

        # Then: Method returns "simple" string
        assert result == "simple"

        # Test other unknown environment patterns
        assert manager.recommend_preset("custom_environment") == "simple"
        assert manager.recommend_preset("random-name-XYZ") == "simple"


class TestPresetManagerRecommendationWithDetails:
    """
    Test suite for recommend_preset_with_details() detailed recommendation.
    
    Scope:
        - EnvironmentRecommendation structure and fields
        - Confidence scoring (0.0-1.0)
        - Reasoning text generation
        - Environment detection integration
        - Pattern-based matching for complex names
        
    Business Critical:
        Detailed recommendations with confidence and reasoning enable
        informed configuration decisions and operational transparency.
        
    Test Strategy:
        - Test EnvironmentRecommendation structure completeness
        - Verify confidence scoring accuracy
        - Test reasoning clarity and accuracy
        - Validate pattern matching for complex environments
    """
    
    def test_recommend_preset_with_details_returns_complete_recommendation(self):
        """
        Test that recommend_preset_with_details() returns EnvironmentRecommendation.

        Verifies:
            The method returns an EnvironmentRecommendation namedtuple with
            all required fields as documented in return contract.

        Business Impact:
            Provides comprehensive recommendation information for
            administrative interfaces and decision support systems.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset_with_details("production") is called
            Then: An EnvironmentRecommendation object is returned
            And: Object has preset_name, confidence, reasoning, environment_detected fields
            And: All fields contain valid, non-empty values

        Fixtures Used:
            - None (tests return structure)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details("production") is called
        result = manager.recommend_preset_with_details("production")

        # Then: An EnvironmentRecommendation object is returned
        assert isinstance(result, EnvironmentRecommendation)

        # And: Object has all required fields
        assert hasattr(result, 'preset_name')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'reasoning')
        assert hasattr(result, 'environment_detected')

        # And: All fields contain valid, non-empty values
        assert result.preset_name == "production"
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
        assert isinstance(result.environment_detected, str)
        assert len(result.environment_detected) > 0
    
    def test_recommend_preset_with_details_has_high_confidence_for_exact_match(self):
        """
        Test that exact environment matches result in high confidence scores.

        Verifies:
            The confidence score is high (>0.8) for exact environment name
            matches as documented in Behavior section.

        Business Impact:
            Enables automated deployment systems to trust recommendations
            for well-known environments without human validation.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset_with_details("production") is called
            Then: Confidence score is greater than 0.8
            And: Exact match results in high-confidence recommendation

        Fixtures Used:
            - None (tests confidence calculation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details("production") is called
        result = manager.recommend_preset_with_details("production")

        # Then: Confidence score is greater than 0.8
        assert result.confidence > 0.8

        # And: Exact match results in high-confidence recommendation
        # Test other exact matches
        dev_result = manager.recommend_preset_with_details("development")
        assert dev_result.confidence > 0.8

        staging_result = manager.recommend_preset_with_details("staging")
        assert staging_result.confidence > 0.8
    
    def test_recommend_preset_with_details_provides_clear_reasoning(self):
        """
        Test that reasoning field explains the recommendation basis.

        Verifies:
            The reasoning field contains a human-readable explanation
            of why the preset was recommended as documented in return contract.

        Business Impact:
            Provides operational transparency for audit purposes and
            helps operators understand configuration decisions.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset_with_details("production") is called
            Then: reasoning field is non-empty string
            And: Reasoning mentions environment detection or matching
            And: Reasoning explains why preset was selected

        Fixtures Used:
            - None (tests reasoning generation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details("production") is called
        result = manager.recommend_preset_with_details("production")

        # Then: reasoning field is non-empty string
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

        # And: Reasoning mentions environment detection or matching
        # Check that reasoning contains relevant keywords
        reasoning_lower = result.reasoning.lower()
        assert any(keyword in reasoning_lower for keyword in ["exact match", "environment", "production"])

        # And: Reasoning explains why preset was selected
        assert "production" in reasoning_lower

        # Test with different environment
        dev_result = manager.recommend_preset_with_details("development")
        assert len(dev_result.reasoning) > 0
        dev_reasoning_lower = dev_result.reasoning.lower()
        assert any(keyword in dev_reasoning_lower for keyword in ["exact match", "environment", "development"])
        assert "development" in dev_reasoning_lower
    
    def test_recommend_preset_with_details_handles_pattern_matching(self):
        """
        Test that complex environment names are matched via patterns.

        Verifies:
            The method applies pattern-based matching for complex environment
            naming schemes as documented in Behavior section.

        Business Impact:
            Supports diverse organizational naming conventions without
            requiring exact string matching.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset_with_details("staging-environment-v2") is called
            Then: Method recognizes "staging" pattern
            And: Returns appropriate preset (production)
            And: environment_detected field shows pattern matched

        Fixtures Used:
            - None (tests pattern matching)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details("staging-environment-v2") is called
        result = manager.recommend_preset_with_details("staging-environment-v2")

        # Then: Method recognizes "staging" pattern
        # And: Returns appropriate preset (production)
        assert result.preset_name == "production"

        # And: environment_detected field shows pattern matched
        assert result.environment_detected == "staging-environment-v2"

        # And: Reasoning mentions pattern matching
        assert "pattern" in result.reasoning.lower()
        assert "staging" in result.reasoning.lower()

        # Test other complex patterns
        dev_patterns = [
            ("dev-local-machine", "development"),
            ("test-environment", "development"),
            ("prod-server-main", "production"),
            ("preprod-uat", "production")
        ]

        for env_name, expected_preset in dev_patterns:
            pattern_result = manager.recommend_preset_with_details(env_name)
            assert pattern_result.preset_name == expected_preset
            assert pattern_result.environment_detected == env_name
            assert "pattern" in pattern_result.reasoning.lower()
    
    def test_recommend_preset_with_details_with_auto_detection(self, monkeypatch):
        """
        Test that auto-detection provides detailed recommendation information.

        Verifies:
            When environment=None, method uses unified environment detection
            and provides detailed reasoning as documented in Behavior section.

        Business Impact:
            Enables zero-configuration deployments with full transparency
            into environment detection and recommendation logic.

        Scenario:
            Given: An initialized PresetManager instance
            And: Environment variables indicating production deployment
            When: recommend_preset_with_details(None) is called
            Then: EnvironmentRecommendation includes auto-detected environment
            And: Reasoning explains detection method
            And: Confidence reflects detection certainty

        Fixtures Used:
            - monkeypatch: Sets up environment for detection
        """
        # Given: Environment variables indicating production deployment
        monkeypatch.setenv("ENVIRONMENT", "production")

        # And: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details(None) is called
        try:
            result = manager.recommend_preset_with_details(None)

            # Then: EnvironmentRecommendation includes auto-detected environment
            assert isinstance(result, EnvironmentRecommendation)
            assert "auto-detected" in result.environment_detected.lower()

            # And: Reasoning explains detection method
            assert len(result.reasoning) > 0

            # And: Confidence reflects detection certainty
            assert isinstance(result.confidence, float)
            assert 0.0 <= result.confidence <= 1.0

        except ImportError:
            # If unified environment detection service is not available,
            # the method should handle this gracefully
            pytest.skip("Unified environment detection service not available")
    
    def test_recommend_preset_with_details_has_low_confidence_for_unknown(self):
        """
        Test that unknown environments result in low confidence scores.

        Verifies:
            The confidence score is low (<0.5) when environment doesn't
            match known patterns, indicating fallback behavior.

        Business Impact:
            Signals to operators that manual configuration review may
            be needed for optimal resilience settings.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset_with_details("unknown_custom_env") is called
            Then: Confidence score is less than 0.5
            And: preset_name is "simple" (fallback)
            And: Reasoning mentions unknown environment

        Fixtures Used:
            - None (tests low-confidence fallback)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details("unknown_custom_env") is called
        result = manager.recommend_preset_with_details("unknown_custom_env")

        # Then: Confidence score is less than 0.5
        assert result.confidence < 0.5

        # And: preset_name is "simple" (fallback)
        assert result.preset_name == "simple"

        # And: Reasoning mentions unknown environment
        reasoning_lower = result.reasoning.lower()
        assert "unknown" in reasoning_lower
        assert "pattern" in reasoning_lower

        # Test other unknown environments
        unknown_environments = ["random_name", "custom-env-XYZ", "nonexistent"]
        for env_name in unknown_environments:
            unknown_result = manager.recommend_preset_with_details(env_name)
            assert unknown_result.confidence < 0.5
            assert unknown_result.preset_name == "simple"
    
    def test_recommend_preset_with_details_handles_abbreviations(self):
        """
        Test that abbreviations are resolved with appropriate confidence.

        Verifies:
            Common abbreviations like "dev", "prod" are recognized and
            resolved with appropriate confidence and reasoning.

        Business Impact:
            Supports flexible naming while maintaining recommendation
            quality and confidence accuracy.

        Scenario:
            Given: An initialized PresetManager instance
            When: recommend_preset_with_details("dev") is called
            Then: preset_name is "development"
            And: Confidence is high for recognized abbreviation
            And: Reasoning mentions abbreviation resolution

        Fixtures Used:
            - None (tests abbreviation handling)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: recommend_preset_with_details("dev") is called
        result = manager.recommend_preset_with_details("dev")

        # Then: preset_name is "development"
        assert result.preset_name == "development"

        # And: Confidence is high for recognized abbreviation
        assert result.confidence > 0.8  # Should be high for common abbreviations

        # And: Reasoning mentions abbreviation resolution
        reasoning_lower = result.reasoning.lower()
        assert "abbreviation" in reasoning_lower or "standard" in reasoning_lower

        # Test other abbreviations
        abbreviations = [
            ("prod", "production"),
            ("test", "development"),
            ("stage", "production"),
            ("dev", "development")
        ]

        for abbr, expected_preset in abbreviations:
            abbr_result = manager.recommend_preset_with_details(abbr)
            assert abbr_result.preset_name == expected_preset
            assert abbr_result.confidence > 0.8  # High confidence for standard abbreviations
            assert abbr_result.environment_detected == abbr
            assert len(abbr_result.reasoning) > 0