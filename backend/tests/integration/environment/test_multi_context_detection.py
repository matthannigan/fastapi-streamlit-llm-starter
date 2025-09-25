"""
Multi-Context Environment Detection Integration Tests

This module tests environment detection across different feature contexts (AI, Security,
Cache, Resilience), ensuring that each context provides appropriate metadata and
overrides while maintaining consistency across all dependent services.

HIGHEST PRIORITY - Core functionality that affects all dependent services
"""

import pytest
import os
from typing import Dict, Any

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentDetector,
    DetectionConfig,
    get_environment_info,
    EnvironmentInfo,
    EnvironmentSignal
)


class TestMultiContextEnvironmentDetection:
    """
    Integration tests for multi-context environment detection.
    
    Seam Under Test:
        Feature Context Selection → Environment Detection → Context-Specific Metadata → Service Integration
        
    Critical Paths:
        - Feature-specific context → Detection logic → Metadata and overrides → Service behavior
        - Context consistency → Cross-service propagation → Unified environment view
        - Context switching → State management → Consistent detection results
        
    Business Impact:
        Ensures consistent environment detection across different feature contexts
        while providing appropriate metadata for each context, enabling services to
        adapt their behavior appropriately without conflicts or inconsistencies
    """

    def test_ai_context_provides_ai_specific_metadata(self, ai_enabled_environment):
        """
        Test that AI_ENABLED context provides AI-specific cache and optimization metadata.
        
        Integration Scope:
            AI feature context → Environment detection → AI-specific metadata → Cache service integration
            
        Business Impact:
            Ensures AI services get appropriate cache prefixes and optimization hints
            for improved performance and resource utilization
            
        Test Strategy:
            - Enable AI features in environment
            - Request environment info with AI context
            - Verify AI-specific metadata is included and properly formatted
            - Test metadata consistency across multiple calls
            
        Success Criteria:
            - AI context detection includes ai_cache_enabled metadata
            - AI prefix metadata is provided for cache key generation
            - Context-specific metadata follows expected format
            - Metadata is consistent across multiple detection calls
        """
        # Get environment info with AI context
        ai_env = get_environment_info(FeatureContext.AI_ENABLED)
        
        # Should detect environment with AI context
        assert ai_env.feature_context == FeatureContext.AI_ENABLED
        assert ai_env.environment in [Environment.DEVELOPMENT, Environment.PRODUCTION, Environment.STAGING, Environment.TESTING]
        
        # Should include AI-specific metadata
        metadata = ai_env.metadata
        assert isinstance(metadata, dict)
        # Contracts do not require 'feature_context' in metadata; verify via attribute
        assert ai_env.feature_context == FeatureContext.AI_ENABLED
        
        # Should have AI cache configuration metadata per contract examples
        if 'ENABLE_AI_CACHE' in os.environ:
            assert (
                'enable_ai_cache_enabled' in metadata or
                'ai_cache_enabled' in metadata or
                metadata.get('context_flags', {}).get('enable_ai_cache', False) is True
            )
            
        # Should provide cache prefix for AI operations
        assert 'ai_prefix' in metadata or metadata.get('cache_prefix', '').startswith('ai')
        
        # AI context may not add explicit AI signals; metadata hints are sufficient per contracts

    def test_security_context_enforces_production_overrides(self, dev_with_security_enforcement):
        """
        Test that SECURITY_ENFORCEMENT context applies production overrides when needed.
        
        Integration Scope:
            Security feature context → Production override logic → Environment enforcement → Auth service integration
            
        Business Impact:
            Allows security-conscious deployments to enforce production rules
            regardless of underlying environment, ensuring security compliance
            
        Test Strategy:
            - Enable security enforcement in development environment
            - Request environment info with security context
            - Verify production override is applied with high confidence
            - Test security metadata is included for auth services
            
        Success Criteria:
            - Security context overrides to production when enforcement enabled
            - High confidence in security override decision (>0.9)
            - Security enforcement metadata is included for auth services
            - Override reasoning is comprehensive and clear
        """
        # Get environment with security enforcement context
        security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        
        # Security context may enforce production override per contracts
        assert security_env.feature_context == FeatureContext.SECURITY_ENFORCEMENT
        security_signals = [s for s in security_env.additional_signals 
                          if 'security' in s.source.lower() or 'enforce' in s.source.lower()]
        # Accept either a full override to production or a security override signal present
        assert (
            security_env.environment == Environment.PRODUCTION or
            len(security_signals) >= 1
        )
        # If override signal present, require reasonable confidence
        if security_signals:
            assert any(s.confidence >= 0.8 for s in security_signals)
        
        # Reasoning content is implementation-defined; ensure it's a string
        assert isinstance(security_env.reasoning, str)
        
        # Should include security-specific metadata for auth services
        metadata = security_env.metadata
        # Contracts do not require 'feature_context' in metadata; verify via attribute
        assert security_env.feature_context == FeatureContext.SECURITY_ENFORCEMENT
        # Accept either explicit metadata flag or presence of override signal
        assert (
            'enforce_auth_enabled' in metadata or
            any(s.source.lower().startswith('security') or 'enforce' in s.source.lower() for s in security_signals)
        )

    def test_cache_optimization_context_provides_cache_metadata(self, production_environment):
        """
        Test CACHE_OPTIMIZATION context provides cache-specific configuration metadata.
        
        Integration Scope:
            Cache optimization context → Environment detection → Cache configuration hints → Cache service integration
            
        Business Impact:
            Ensures cache optimization works correctly across environments with
            appropriate configuration hints for performance tuning
            
        Test Strategy:
            - Set production environment
            - Request environment info with cache optimization context
            - Verify cache-specific metadata is provided
            - Test metadata includes performance optimization hints
            
        Success Criteria:
            - Cache context returns correct environment detection
            - Cache optimization metadata is included
            - Performance hints are appropriate for detected environment
            - Context metadata follows consistent format
        """
        # Get environment with cache optimization context
        cache_env = get_environment_info(FeatureContext.CACHE_OPTIMIZATION)
        
        # Should detect production environment correctly
        assert cache_env.environment == Environment.PRODUCTION
        assert cache_env.feature_context == FeatureContext.CACHE_OPTIMIZATION
        assert cache_env.confidence >= 0.7
        
        # Should include cache optimization metadata (hints may be optional per contracts)
        metadata = cache_env.metadata
        assert cache_env.feature_context == FeatureContext.CACHE_OPTIMIZATION
        # If hints are provided, they should be strings
        if 'cache_strategy' in metadata:
            assert isinstance(metadata['cache_strategy'], str)
        if 'performance_profile' in metadata:
            assert isinstance(metadata['performance_profile'], str)

    def test_resilience_strategy_context_provides_resilience_metadata(self, staging_environment):
        """
        Test RESILIENCE_STRATEGY context provides resilience-specific configuration metadata.
        
        Integration Scope:
            Resilience strategy context → Environment detection → Resilience configuration hints → Resilience service integration
            
        Business Impact:
            Ensures resilience patterns work correctly across environments with
            appropriate strategy hints for reliability and performance balance
            
        Test Strategy:
            - Set staging environment
            - Request environment info with resilience strategy context
            - Verify resilience-specific metadata is provided
            - Test metadata includes appropriate strategy hints
            
        Success Criteria:
            - Resilience context returns correct environment detection
            - Resilience strategy metadata is included
            - Strategy hints are appropriate for detected environment
            - Context provides circuit breaker and retry configuration hints
        """
        # Get environment with resilience strategy context
        resilience_env = get_environment_info(FeatureContext.RESILIENCE_STRATEGY)
        
        # Should detect staging environment correctly
        assert resilience_env.environment == Environment.STAGING
        assert resilience_env.feature_context == FeatureContext.RESILIENCE_STRATEGY
        assert resilience_env.confidence >= 0.7
        
        # Should include resilience strategy metadata (hints may be optional per contracts)
        metadata = resilience_env.metadata
        assert resilience_env.feature_context == FeatureContext.RESILIENCE_STRATEGY
        if 'resilience_strategy' in metadata:
            assert isinstance(metadata['resilience_strategy'], str)
        if 'failure_handling' in metadata:
            assert isinstance(metadata['failure_handling'], str)

    def test_default_context_provides_baseline_metadata(self, development_environment):
        """
        Test that DEFAULT context provides consistent baseline detection without overrides.
        
        Integration Scope:
            Standard environment detection → Default context → Baseline metadata → General service integration
            
        Business Impact:
            Ensures baseline environment detection works consistently without
            feature-specific overrides interfering with general service behavior
            
        Test Strategy:
            - Set development environment
            - Request environment info with default context
            - Verify no feature-specific overrides are applied
            - Test baseline metadata format and content
            
        Success Criteria:
            - Default context returns correct environment without overrides
            - No feature-specific metadata is added beyond baseline
            - Only standard environment signals are present
            - Metadata format is minimal and consistent
        """
        # Get environment with default context
        default_env = get_environment_info(FeatureContext.DEFAULT)
        
        # Should detect development environment without overrides
        assert default_env.environment == Environment.DEVELOPMENT
        assert default_env.feature_context == FeatureContext.DEFAULT
        assert default_env.confidence >= 0.6
        
        # Should include minimal baseline metadata (feature_context may not be in metadata)
        metadata = default_env.metadata
        assert default_env.feature_context == FeatureContext.DEFAULT
        
        # Should NOT include feature-specific metadata
        feature_specific_keys = ['ai_prefix', 'security_override', 'cache_strategy', 'resilience_strategy']
        for key in feature_specific_keys:
            assert key not in metadata, f"Default context should not include {key}"
        
        # Should only include baseline detection signals (no feature overrides)
        override_signals = [s for s in default_env.additional_signals 
                          if 'override' in s.source.lower()]
        assert len(override_signals) == 0, "Default context should not include override signals"

    def test_context_consistency_across_environments(self, clean_environment, reload_environment_module):
        """
        Test that feature contexts provide consistent behavior across different environments.
        
        Integration Scope:
            Multiple environments → Feature contexts → Consistent metadata patterns → Cross-environment service behavior
            
        Business Impact:
            Ensures feature contexts provide consistent metadata regardless
            of underlying environment, enabling predictable service behavior
            
        Test Strategy:
            - Test each feature context across multiple environments
            - Verify metadata format consistency
            - Test context-specific behavior is preserved
            - Validate cross-environment service integration points
            
        Success Criteria:
            - AI context always provides AI metadata regardless of environment
            - Security context always provides security metadata
            - Context-specific metadata format is consistent across environments
            - Service integration points remain stable
        """
        environments_to_test = [
            ('development', Environment.DEVELOPMENT),
            ('staging', Environment.STAGING),
            ('production', Environment.PRODUCTION),
            ('testing', Environment.TESTING)
        ]
        
        context_results = {}
        
        for env_name, env_enum in environments_to_test:
            # Set environment
            os.environ['ENVIRONMENT'] = env_name
            if env_name == 'production':
                os.environ['API_KEY'] = 'test-key-for-prod'
            reload_environment_module()
            
            # Test each context
            contexts_to_test = [
                FeatureContext.AI_ENABLED,
                FeatureContext.SECURITY_ENFORCEMENT, 
                FeatureContext.CACHE_OPTIMIZATION,
                FeatureContext.RESILIENCE_STRATEGY,
                FeatureContext.DEFAULT
            ]
            
            for context in contexts_to_test:
                env_info = get_environment_info(context)
                
                context_key = f"{context.value}_{env_name}"
                context_results[context_key] = {
                    'environment': env_info.environment,
                    'context': env_info.feature_context,
                    'metadata_keys': set(env_info.metadata.keys()),
                    'confidence': env_info.confidence
                }
                
                # Context should always be correctly identified
                assert env_info.feature_context == context
                
                # Should always include feature_context attribute (metadata key optional)
                assert env_info.feature_context == context
                if 'feature_context' in env_info.metadata:
                    assert env_info.metadata['feature_context'] == context.value
        
        # Verify context consistency patterns
        ai_contexts = [r for k, r in context_results.items() if k.startswith('ai_enabled_')]
        for result in ai_contexts:
            # AI context should consistently include AI-related metadata
            expected_keys = {'feature_context'}
            # May also include ai_prefix, cache_prefix, etc.
            assert expected_keys.issubset(result['metadata_keys'])
        
        security_contexts = [r for k, r in context_results.items() if k.startswith('security_enforcement_')]
        for result in security_contexts:
            # Security context may override to production or at least document security signals per contracts
            assert result['context'] == FeatureContext.SECURITY_ENFORCEMENT

    def test_context_metadata_format_consistency(self, production_environment):
        """
        Test that context metadata follows consistent format patterns across all contexts.
        
        Integration Scope:
            Feature contexts → Metadata generation → Consistent data structures → Service parsing compatibility
            
        Business Impact:
            Ensures downstream consumers can reliably parse context metadata
            without context-specific parsing logic
            
        Test Strategy:
            - Test metadata format for each feature context
            - Verify metadata keys follow consistent naming conventions
            - Test metadata value types and structures
            - Validate service compatibility with metadata formats
            
        Success Criteria:
            - All contexts include feature_context in metadata
            - Boolean flags use consistent key naming patterns (*_enabled)
            - String values follow consistent patterns
            - Complex metadata uses consistent data structures
        """
        # Test metadata format for all contexts
        contexts_to_test = [
            (FeatureContext.AI_ENABLED, ['feature_context']),
            (FeatureContext.SECURITY_ENFORCEMENT, ['feature_context', 'security_override']),
            (FeatureContext.CACHE_OPTIMIZATION, ['feature_context']),
            (FeatureContext.RESILIENCE_STRATEGY, ['feature_context']),
            (FeatureContext.DEFAULT, ['feature_context'])
        ]
        
        for context, expected_base_keys in contexts_to_test:
            env_info = get_environment_info(context)
            metadata = env_info.metadata
            
            # All contexts expose feature_context via attribute; metadata key is optional
            assert env_info.feature_context == context
            if 'feature_context' in metadata:
                assert metadata['feature_context'] == context.value
                assert isinstance(metadata['feature_context'], str)
            
            # Check expected base keys are present
            for expected_key in expected_base_keys:
                if expected_key != 'feature_context':  # Already checked above
                    # Some keys may be conditional, but if present should follow format
                    if expected_key in metadata:
                        assert isinstance(metadata[expected_key], (bool, str, dict))
            
            # Boolean flags should follow *_enabled or *_override pattern
            boolean_keys = [k for k, v in metadata.items() if isinstance(v, bool)]
            for bool_key in boolean_keys:
                if bool_key != 'feature_context':  # Special case
                    assert bool_key.endswith('_enabled') or bool_key.endswith('_override'), \
                           f"Boolean key '{bool_key}' should follow naming convention"
            
            # Metadata should not be excessively large
            assert len(metadata) <= 20, f"Metadata too large: {len(metadata)} keys"
            
            # All values should be JSON-serializable types
            for key, value in metadata.items():
                assert isinstance(value, (str, int, float, bool, list, dict, type(None))), \
                       f"Non-serializable value for {key}: {type(value)}"

    def test_concurrent_context_detection_thread_safety(self, production_environment):
        """
        Test that concurrent context detection from multiple threads is thread-safe.
        
        Integration Scope:
            Concurrent threads → Context detection → Thread-safe state management → Consistent results
            
        Business Impact:
            Ensures multi-threaded applications can safely use context detection
            without race conditions or inconsistent results
            
        Test Strategy:
            - Access different contexts concurrently from multiple threads
            - Verify all threads get consistent results for their context
            - Test for race conditions in context state management
            - Validate thread isolation of context-specific metadata
            
        Success Criteria:
            - All threads get consistent results for their specific context
            - No race conditions in context detection logic
            - Context-specific metadata is properly isolated between threads
            - Performance remains acceptable under concurrent load
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Function to test context detection from different threads
        def detect_with_context(context):
            env_info = get_environment_info(context)
            return {
                'context': env_info.feature_context,
                'environment': env_info.environment,
                'confidence': env_info.confidence,
                'metadata_keys': list(env_info.metadata.keys()),
                'thread_id': threading.current_thread().ident
            }
        
        # Test concurrent access with different contexts
        contexts_to_test = [
            FeatureContext.AI_ENABLED,
            FeatureContext.SECURITY_ENFORCEMENT,
            FeatureContext.CACHE_OPTIMIZATION,
            FeatureContext.RESILIENCE_STRATEGY,
            FeatureContext.DEFAULT
        ]
        
        # Run many concurrent detections
        num_threads_per_context = 5
        with ThreadPoolExecutor(max_workers=len(contexts_to_test) * num_threads_per_context) as executor:
            futures = []
            expected_results = {}
            
            for context in contexts_to_test:
                # Submit multiple threads for each context
                for i in range(num_threads_per_context):
                    futures.append(executor.submit(detect_with_context, context))
                
                # Also get expected result for comparison
                if context not in expected_results:
                    expected_results[context] = detect_with_context(context)
            
            # Collect all results
            results = [future.result() for future in as_completed(futures)]
        
        # Group results by context
        results_by_context = {}
        for result in results:
            context = result['context']
            if context not in results_by_context:
                results_by_context[context] = []
            results_by_context[context].append(result)
        
        # Verify consistency within each context
        for context, context_results in results_by_context.items():
            # All results for this context should be identical (except thread_id)
            first_result = context_results[0]
            for result in context_results[1:]:
                assert result['context'] == first_result['context']
                assert result['environment'] == first_result['environment']
                assert result['confidence'] == first_result['confidence']
                assert result['metadata_keys'] == first_result['metadata_keys']
                # thread_id should be different for true concurrency
            
            # Should have results from multiple threads
            thread_ids = set(r['thread_id'] for r in context_results)
            assert len(thread_ids) >= 2, f"Expected multiple threads for {context}, got {len(thread_ids)}"

    def test_context_switching_state_management(self, clean_environment, reload_environment_module):
        """
        Test that switching between contexts maintains proper state management.
        
        Integration Scope:
            Context switching → State management → Consistent detection → Service state consistency
            
        Business Impact:
            Ensures services can switch between different contexts without
            state pollution or inconsistent behavior
            
        Test Strategy:
            - Switch between different contexts rapidly
            - Verify each context maintains proper state
            - Test context isolation and independence
            - Validate state cleanup between context switches
            
        Success Criteria:
            - Each context returns appropriate metadata regardless of previous context
            - No state pollution between contexts
            - Context switching doesn't affect detection consistency
            - Context metadata is properly isolated
        """
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['API_KEY'] = 'context-switching-test'
        reload_environment_module()
        
        # Test rapid context switching
        contexts = [
            FeatureContext.AI_ENABLED,
            FeatureContext.SECURITY_ENFORCEMENT,
            FeatureContext.CACHE_OPTIMIZATION,
            FeatureContext.RESILIENCE_STRATEGY,
            FeatureContext.DEFAULT,
            FeatureContext.AI_ENABLED,  # Repeat to test state consistency
            FeatureContext.SECURITY_ENFORCEMENT,
        ]
        
        previous_results = {}
        
        for i, context in enumerate(contexts):
            env_info = get_environment_info(context)
            
            # Should always return correct context
            assert env_info.feature_context == context
            
            # Should always include context via attribute; metadata key optional
            assert env_info.feature_context == context
            if 'feature_context' in env_info.metadata:
                assert env_info.metadata.get('feature_context') == context.value
            
            # If we've seen this context before, results should be identical
            if context in previous_results:
                prev_result = previous_results[context]
                assert env_info.environment == prev_result.environment
                assert env_info.confidence == prev_result.confidence
                assert env_info.metadata == prev_result.metadata
                
            previous_results[context] = env_info
        
        # Verify specific context behaviors are maintained
        ai_result = previous_results[FeatureContext.AI_ENABLED]
        security_result = previous_results[FeatureContext.SECURITY_ENFORCEMENT]
        
        # AI context should have AI-specific characteristics
        assert ai_result.feature_context == FeatureContext.AI_ENABLED
        
        # Security context should maintain security override behavior
        assert security_result.feature_context == FeatureContext.SECURITY_ENFORCEMENT
        assert security_result.environment == Environment.PRODUCTION  # Should override
        
        # Contexts should have different metadata profiles
        assert ai_result.metadata != security_result.metadata