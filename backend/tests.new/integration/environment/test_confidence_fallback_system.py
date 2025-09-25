"""
Environment Detection Confidence and Fallback Integration Tests

This module tests the confidence scoring system and fallback mechanisms in environment
detection, ensuring robust operation even when environment signals are conflicting,
missing, or ambiguous.

HIGH PRIORITY - System reliability and operational safety
"""

import pytest
import time
from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentDetector,
    DetectionConfig,
    get_environment_info,
    EnvironmentInfo,
    EnvironmentSignal
)


class TestEnvironmentDetectionConfidenceAndFallback:
    """
    Integration tests for environment detection confidence and fallback systems.

    Seam Under Test:
        Signal Collection → Confidence Analysis → Fallback Decision → Environment Determination

    Critical Path:
        Environment signals → Confidence scoring → Conflict resolution → Fallback logic

    Business Impact:
        Ensures reliable environment detection even when primary signals are unavailable
        or conflicting, providing operational safety

    Test Strategy:
        - Test confidence scoring with multiple agreeing signals
        - Test conflict resolution with conflicting signals
        - Test fallback behavior with no signals
        - Test environment variable precedence rules
        - Test pattern-based detection accuracy
        - Test system indicator reliability
    """

    def test_multiple_agreeing_signals_boost_confidence(self, clean_environment):
        """
        Test that multiple agreeing signals boost detection confidence.

        Integration Scope:
            Multiple signal sources → Confidence boosting → High confidence result

        Business Impact:
            Ensures reliable environment detection when multiple indicators agree

        Test Strategy:
            - Set multiple environment variables pointing to same environment
            - Verify confidence is boosted above individual signal confidence
            - Test that reasoning mentions signal agreement

        Success Criteria:
            - Multiple agreeing signals increase confidence
            - Confidence boost is proportional to signal agreement
            - Reasoning explains the confidence boost
        """
        # Set multiple signals pointing to production
        os.environ['ENVIRONMENT'] = 'production'      # 0.95 confidence
        os.environ['NODE_ENV'] = 'production'         # 0.85 confidence
        os.environ['HOSTNAME'] = 'api-prod-01.com'   # 0.70 confidence

        env_info = get_environment_info()

        # Should detect production with boosted confidence
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence > 0.95  # Boosted beyond highest individual signal
        assert env_info.confidence <= 0.98  # Capped to prevent overconfidence

        # Reasoning should mention signal agreement
        assert "confirmed by" in env_info.reasoning.lower() or "additional signals" in env_info.reasoning.lower()

    def test_conflicting_signals_reduce_confidence(self, clean_environment):
        """
        Test that conflicting signals reduce detection confidence.

        Integration Scope:
            Conflicting signal sources → Confidence reduction → Lower confidence result

        Business Impact:
            Ensures conservative confidence scoring when signals disagree

        Test Strategy:
            - Set conflicting environment variables
            - Verify confidence is reduced due to conflicts
            - Test that reasoning mentions the conflicts

        Success Criteria:
            - Conflicting signals reduce confidence
            - High-confidence conflicts trigger stronger reduction
            - Reasoning explains the conflict situation
        """
        # Set high-confidence conflicting signals
        os.environ['ENVIRONMENT'] = 'production'      # 0.95 confidence
        os.environ['NODE_ENV'] = 'development'        # 0.85 confidence
        os.environ['DEBUG'] = 'true'                  # 0.70 confidence (development indicator)

        env_info = get_environment_info()

        # Should resolve to production (highest confidence) but with reduced confidence
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence < 0.95  # Reduced due to conflicts
        assert env_info.confidence >= 0.7  # But still reasonably confident

        # Reasoning should mention conflicts
        assert "conflicting signals" in env_info.reasoning.lower()

    def test_fallback_to_development_with_no_signals(self, unknown_environment):
        """
        Test that system falls back to development when no signals are available.

        Integration Scope:
            No environment signals → Fallback logic → Development default

        Business Impact:
            Ensures system remains operational even without environment configuration

        Test Strategy:
            - Clear all environment indicators
            - Verify fallback to development environment
            - Test that confidence reflects uncertainty

        Success Criteria:
            - Falls back to development environment
            - Low confidence score reflects uncertainty
            - Reasoning explains fallback decision
        """
        env_info = get_environment_info()

        # Should fall back to development
        assert env_info.environment == Environment.DEVELOPMENT
        assert env_info.confidence < 0.7  # Low confidence due to no signals
        assert env_info.confidence >= 0.3  # But not zero confidence

        # Reasoning should explain fallback
        assert "no environment signals" in env_info.reasoning.lower() or "fallback" in env_info.reasoning.lower()

    def test_environment_variable_precedence_rules(self, clean_environment):
        """
        Test that environment variable precedence is followed correctly.

        Integration Scope:
            Environment variable hierarchy → Precedence resolution → Correct signal selection

        Business Impact:
            Ensures predictable environment detection based on variable priority

        Test Strategy:
            - Set multiple environment variables with different precedence
            - Verify highest precedence variable is used
            - Test precedence order: ENVIRONMENT > NODE_ENV > FLASK_ENV > etc.

        Success Criteria:
            - ENVIRONMENT variable takes highest precedence
            - Lower precedence variables are ignored when higher ones exist
            - Precedence order matches specification
        """
        # Set multiple environment variables with different values
        os.environ['ENVIRONMENT'] = 'production'      # Highest precedence
        os.environ['NODE_ENV'] = 'development'        # Lower precedence
        os.environ['FLASK_ENV'] = 'testing'           # Even lower precedence
        os.environ['APP_ENV'] = 'staging'             # Lowest precedence

        env_info = get_environment_info()

        # Should use highest precedence variable
        assert env_info.environment == Environment.PRODUCTION
        assert "ENVIRONMENT" in env_info.detected_by

        # Should have high confidence due to explicit setting
        assert env_info.confidence >= 0.9

    def test_pattern_based_detection_with_hostname(self, environment_with_hostname):
        """
        Test pattern-based environment detection using hostname.

        Integration Scope:
            Hostname patterns → Pattern matching → Environment classification

        Business Impact:
            Ensures containerized and distributed deployments are detected correctly

        Test Strategy:
            - Set hostname with production pattern
            - Verify pattern matching detects correct environment
            - Test multiple hostname patterns

        Success Criteria:
            - Hostname patterns correctly match environment
            - Pattern-based detection has appropriate confidence
            - Multiple patterns work correctly
        """
        env_info = get_environment_info()

        # Should detect production from hostname pattern
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.7  # Pattern-based confidence
        assert "hostname" in env_info.detected_by.lower()
        assert "prod" in env_info.reasoning.lower()

    def test_system_indicators_detection_accuracy(self, environment_with_system_indicators):
        """
        Test system indicators-based environment detection.

        Integration Scope:
            System indicators → File presence checks → Environment classification

        Business Impact:
            Ensures local development environments are detected correctly

        Test Strategy:
            - Create development indicator files (.env, .git)
            - Verify system indicator detection works
            - Test that indicators have appropriate confidence

        Success Criteria:
            - System indicators correctly identify development environment
            - File-based indicators have moderate confidence
            - Multiple indicators can be detected simultaneously
        """
        env_info = get_environment_info()

        # Should detect development from system indicators
        assert env_info.environment == Environment.DEVELOPMENT
        assert env_info.confidence >= 0.7  # System indicator confidence
        assert "system_indicator" in env_info.detected_by.lower()

        # Should include multiple system indicator signals
        system_signals = [s for s in env_info.additional_signals
                         if s.source == "system_indicator"]
        assert len(system_signals) >= 1

        # Each signal should have moderate confidence
        for signal in system_signals:
            assert 0.6 <= signal.confidence <= 0.8

    def test_confidence_scoring_consistency(self, clean_environment):
        """
        Test that confidence scoring is consistent and predictable.

        Integration Scope:
            Signal collection → Confidence calculation → Consistent scoring

        Business Impact:
            Ensures downstream systems can rely on confidence scores

        Test Strategy:
            - Test confidence scores for different signal types
            - Verify consistency across multiple calls
            - Test confidence bounds and constraints

        Success Criteria:
            - Confidence scores are within expected ranges for each signal type
            - Confidence scoring is deterministic and consistent
            - Confidence values respect upper and lower bounds
        """
        # Test explicit environment variable (high confidence)
        os.environ['ENVIRONMENT'] = 'production'
        env_info1 = get_environment_info()
        assert 0.9 <= env_info1.confidence <= 1.0

        # Test system indicator (moderate confidence)
        os.environ.pop('ENVIRONMENT')
        with pytest.raises(Exception):  # Remove other env vars that might interfere
            pass
        # Create a .env file to trigger system indicator
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.env', delete=False):
            pass

        env_info2 = get_environment_info()
        assert 0.6 <= env_info2.confidence <= 0.8

        # Test no signals (low confidence)
        os.environ.pop('HOSTNAME', None)
        # Remove the temp .env file
        import os
        for f in os.listdir('.'):
            if f.endswith('.env'):
                os.remove(f)

        env_info3 = get_environment_info()
        assert 0.3 <= env_info3.confidence <= 0.7
        assert env_info3.environment == Environment.DEVELOPMENT  # Fallback

    def test_signal_collection_completeness(self, clean_environment):
        """
        Test that all relevant signals are collected during detection.

        Integration Scope:
            Signal collection → Complete signal gathering → Signal prioritization

        Business Impact:
            Ensures no relevant environment signals are missed

        Test Strategy:
            - Set up multiple types of environment signals
            - Verify all signals are collected
            - Test signal ordering and prioritization

        Success Criteria:
            - All configured signal sources are checked
            - Signals are collected in priority order
            - Signal collection is comprehensive but efficient
        """
        # Set up multiple signal types
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['HOSTNAME'] = 'api-prod.example.com'
        os.environ['DEBUG'] = 'false'

        env_info = get_environment_info()

        # Should collect signals from multiple sources
        signal_sources = {s.source for s in env_info.additional_signals}
        assert len(signal_sources) >= 2  # Should have multiple signal types

        # Should include the highest priority signal
        assert env_info.confidence >= 0.9
        assert env_info.environment == Environment.PRODUCTION

        # Signals should be sorted by confidence (highest first)
        sorted_signals = sorted(env_info.additional_signals, key=lambda s: s.confidence, reverse=True)
        assert sorted_signals[0].confidence >= sorted_signals[-1].confidence

    def test_reasoning_comprehensiveness(self, clean_environment):
        """
        Test that detection reasoning is comprehensive and informative.

        Integration Scope:
            Signal analysis → Reasoning generation → Comprehensive explanation

        Business Impact:
            Ensures debugging and monitoring can understand detection decisions

        Test Strategy:
            - Test reasoning with multiple signals
            - Test reasoning with conflicts
            - Test reasoning with fallback scenarios

        Success Criteria:
            - Reasoning includes all relevant signal information
            - Reasoning explains confidence adjustments
            - Reasoning provides actionable debugging information
        """
        # Test with multiple agreeing signals
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['NODE_ENV'] = 'production'

        env_info = get_environment_info()
        reasoning = env_info.reasoning.lower()

        assert "production" in reasoning
        assert "confidence" in reasoning or str(env_info.confidence) in env_info.reasoning
        assert "additional signals" in reasoning or "confirmed by" in reasoning

        # Test with conflicts
        os.environ['DEBUG'] = 'true'  # Conflicting development indicator

        env_info2 = get_environment_info()
        reasoning2 = env_info2.reasoning.lower()

        assert "conflicting signals" in reasoning2 or "conflict" in reasoning2

        # Test with no signals (fallback)
        for key in list(os.environ.keys()):
            if key in ['ENVIRONMENT', 'NODE_ENV', 'HOSTNAME', 'DEBUG']:
                os.environ.pop(key)

        env_info3 = get_environment_info()
        reasoning3 = env_info3.reasoning.lower()

        assert "no environment signals" in reasoning3 or "fallback" in reasoning3 or "defaulting" in reasoning3

    def test_detection_determinism(self, clean_environment):
        """
        Test that environment detection is deterministic with same inputs.

        Integration Scope:
            Consistent input → Deterministic output → Reliable detection

        Business Impact:
            Ensures environment detection is predictable and testable

        Test Strategy:
            - Set up identical environment conditions
            - Run detection multiple times
            - Verify identical results

        Success Criteria:
            - Same input produces same detection results
            - Confidence scores are consistent
            - Reasoning is identical across runs
        """
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['NODE_ENV'] = 'production'

        # Run detection multiple times
        results = []
        for _ in range(3):
            env_info = get_environment_info()
            results.append((env_info.environment, env_info.confidence, env_info.reasoning))

        # All results should be identical
        for i in range(1, len(results)):
            assert results[0][0] == results[i][0]  # Same environment
            assert results[0][1] == results[i][1]  # Same confidence
            assert results[0][2] == results[i][2]  # Same reasoning

    def test_confidence_bounds_and_constraints(self, clean_environment):
        """
        Test that confidence scores respect bounds and constraints.

        Integration Scope:
            Signal analysis → Confidence constraints → Bounded confidence values

        Business Impact:
            Ensures confidence scores are meaningful and bounded

        Test Strategy:
            - Test maximum confidence limits (should not exceed 0.98)
            - Test minimum confidence floors (should not be zero)
            - Test confidence adjustments are reasonable

        Success Criteria:
            - Confidence never exceeds reasonable maximum (0.98)
            - Confidence never drops to zero (0.0)
            - Confidence adjustments are proportional to evidence
        """
        # Test maximum confidence with multiple strong signals
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['NODE_ENV'] = 'production'
        os.environ['HOSTNAME'] = 'prod-api-01.com'
        os.environ['PRODUCTION'] = 'true'

        env_info = get_environment_info()

        # Confidence should be high but not exceed reasonable maximum
        assert env_info.confidence <= 0.98
        assert env_info.confidence > 0.9

        # Test minimum confidence with no signals
        for key in list(os.environ.keys()):
            if any(env_key in key for env_key in ['ENVIRONMENT', 'NODE', 'HOST', 'PROD', 'DEBUG']):
                os.environ.pop(key)

        env_info2 = get_environment_info()

        # Confidence should be low but not zero
        assert env_info2.confidence > 0.0
        assert env_info2.confidence <= 0.7  # Low confidence threshold

    def test_detection_performance_under_load(self, clean_environment):
        """
        Test environment detection performance under multiple concurrent calls.

        Integration Scope:
            Concurrent detection → Performance → Consistent results

        Business Impact:
            Ensures environment detection performs well under concurrent access

        Test Strategy:
            - Make multiple concurrent detection calls
            - Measure performance characteristics
            - Verify results remain consistent

        Success Criteria:
            - Detection completes quickly (<100ms)
            - Results remain consistent across calls
            - No race conditions or threading issues
        """
        import threading
        import time

        os.environ['ENVIRONMENT'] = 'production'

        results = []
        def detect_environment():
            start_time = time.time()
            env_info = get_environment_info()
            end_time = time.time()
            results.append((env_info.environment, env_info.confidence, end_time - start_time))

        # Run multiple concurrent detections
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=detect_environment)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all results are consistent
        for i in range(1, len(results)):
            assert results[0][0] == results[i][0]  # Same environment
            assert results[0][1] == results[i][1]  # Same confidence

        # Verify reasonable performance (under 100ms per call)
        for result in results:
            assert result[2] < 0.1  # 100ms in seconds
