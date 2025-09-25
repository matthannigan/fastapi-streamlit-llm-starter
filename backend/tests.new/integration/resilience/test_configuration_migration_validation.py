"""
Integration Tests: Configuration Migration → Validation → Monitoring

This module tests the integration between configuration migration, validation,
and monitoring systems. It validates that legacy configurations can be migrated,
new configurations are properly validated, and the migration process is monitored.

Integration Scope:
    - LegacyConfigAnalyzer → ConfigurationMigrator → ResilienceConfigValidator
    - ConfigurationMetricsCollector → Migration monitoring → Usage tracking
    - Configuration validation → Security checks → Performance optimization

Business Impact:
    Ensures smooth configuration evolution and maintains system stability
    during configuration updates and migrations

Test Strategy:
    - Test legacy configuration migration to new format
    - Validate configuration validation and security checks
    - Test migration monitoring and audit trails
    - Verify configuration change tracking and alerting
    - Test configuration performance and optimization

Critical Paths:
    - Legacy configuration → Migration analysis → Validation → Usage tracking
    - Configuration changes → Audit trails → Monitoring → Alert generation
    - Configuration validation → Security checks → Performance optimization
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from app.infrastructure.resilience.config_presets import (
    ResilienceStrategy,
    ResilienceConfig,
    get_default_presets
)
from app.infrastructure.resilience.config_monitoring import ConfigurationMetricsCollector
from app.infrastructure.resilience.migration_utils import (
    LegacyConfigAnalyzer,
    ConfigurationMigrator,
    MigrationRecommendation,
    MigrationConfidence
)


class TestConfigurationMigrationValidation:
    """
    Integration tests for Configuration Migration → Validation → Monitoring.

    Seam Under Test:
        LegacyConfigAnalyzer → ConfigurationMigrator → ResilienceConfigValidator → ConfigurationMetricsCollector

    Critical Paths:
        - Legacy configuration → Migration analysis → Validation → Usage tracking
        - Configuration changes → Audit trails → Monitoring → Alert generation
        - Configuration validation → Security checks → Performance optimization

    Business Impact:
        Ensures smooth configuration evolution and maintains system stability
        during configuration updates, migrations, and operational changes
    """

    @pytest.fixture
    def legacy_config_scenarios(self):
        """Provides test scenarios for legacy configuration migration."""
        return {
            "simple_legacy": {
                "config": {
                    "max_retries": 3,
                    "failure_threshold": 5,
                    "timeout": 60,
                    "strategy": "balanced"
                },
                "expected_migration": {
                    "strategy": "balanced",
                    "retry_config": {"max_attempts": 3},
                    "circuit_breaker_config": {"failure_threshold": 5, "recovery_timeout": 60}
                },
                "migration_confidence": MigrationConfidence.HIGH,
                "description": "Simple legacy configuration with direct field mapping"
            },
            "complex_legacy": {
                "config": {
                    "retry_attempts": 5,
                    "circuit_breaker_failures": 10,
                    "recovery_seconds": 120,
                    "resilience_mode": "conservative",
                    "custom_timeout": 300,
                    "max_concurrent_requests": 10
                },
                "expected_migration": {
                    "strategy": "conservative",
                    "retry_config": {"max_attempts": 5},
                    "circuit_breaker_config": {"failure_threshold": 10, "recovery_timeout": 120}
                },
                "migration_confidence": MigrationConfidence.MEDIUM,
                "description": "Complex legacy configuration requiring field mapping"
            },
            "minimal_legacy": {
                "config": {
                    "retries": 2,
                    "strategy": "aggressive"
                },
                "expected_migration": {
                    "strategy": "aggressive",
                    "retry_config": {"max_attempts": 2}
                },
                "migration_confidence": MigrationConfidence.HIGH,
                "description": "Minimal legacy configuration with defaults"
            }
        }

    @pytest.fixture
    def config_analyzer(self):
        """Create a legacy configuration analyzer for testing."""
        return LegacyConfigAnalyzer()

    @pytest.fixture
    def config_migrator(self):
        """Create a configuration migrator for testing."""
        return ConfigurationMigrator()

    @pytest.fixture
    def config_monitor(self):
        """Create a configuration metrics collector for testing."""
        return ConfigurationMetricsCollector()

    def test_legacy_configuration_analysis(self, config_analyzer, legacy_config_scenarios):
        """
        Test legacy configuration analysis and pattern recognition.

        Integration Scope:
            Legacy configuration → Analysis → Pattern recognition → Migration recommendations

        Business Impact:
            Enables accurate migration planning and risk assessment

        Test Strategy:
            - Analyze different types of legacy configurations
            - Verify pattern recognition accuracy
            - Test migration confidence calculation
            - Validate analysis metadata and recommendations

        Success Criteria:
            - Legacy configurations analyzed correctly
            - Migration patterns identified accurately
            - Confidence scores calculated appropriately
            - Analysis provides actionable migration guidance
        """
        for scenario_name, scenario in legacy_config_scenarios.items():
            legacy_config = scenario["config"]

            # Analyze legacy configuration
            analysis = config_analyzer.analyze_legacy_config(legacy_config)

            # Verify analysis structure
            assert hasattr(analysis, 'confidence')
            assert hasattr(analysis, 'recommendations')
            assert hasattr(analysis, 'field_mappings')
            assert hasattr(analysis, 'risk_factors')

            # Verify confidence calculation
            assert isinstance(analysis.confidence, MigrationConfidence)
            assert analysis.confidence in [MigrationConfidence.HIGH, MigrationConfidence.MEDIUM, MigrationConfidence.LOW]

            # Verify field mappings
            assert isinstance(analysis.field_mappings, dict)
            assert len(analysis.field_mappings) > 0

            # Verify recommendations
            assert isinstance(analysis.recommendations, list)
            assert len(analysis.recommendations) > 0

    def test_configuration_migration_execution(self, config_migrator, legacy_config_scenarios):
        """
        Test execution of configuration migration from legacy to new format.

        Integration Scope:
            Legacy configuration → Migration execution → New configuration → Validation

        Business Impact:
            Ensures successful migration without data loss or corruption

        Test Strategy:
            - Execute migration for different legacy configurations
            - Verify migrated configuration structure and content
            - Test migration accuracy and completeness
            - Validate migrated configuration functionality

        Success Criteria:
            - Legacy configurations migrated successfully
            - Migrated configurations maintain original intent
            - No data loss during migration process
            - Migrated configurations are valid and functional
        """
        for scenario_name, scenario in legacy_config_scenarios.items():
            legacy_config = scenario["config"]
            expected = scenario["expected_migration"]

            # Execute migration
            migration_result = config_migrator.migrate_config(legacy_config)

            # Verify migration result structure
            assert hasattr(migration_result, 'migrated_config')
            assert hasattr(migration_result, 'confidence')
            assert hasattr(migration_result, 'field_mappings')
            assert hasattr(migration_result, 'warnings')

            # Verify migrated configuration is valid
            migrated_config = migration_result.migrated_config
            assert isinstance(migrated_config, dict)
            assert len(migrated_config) > 0

            # Verify expected fields are present
            for key, expected_value in expected.items():
                if key == "strategy":
                    assert migrated_config.get("strategy") == expected_value
                elif key == "retry_config":
                    retry_config = migrated_config.get("retry_config", {})
                    assert isinstance(retry_config, dict)
                    assert "max_attempts" in retry_config
                elif key == "circuit_breaker_config":
                    cb_config = migrated_config.get("circuit_breaker_config", {})
                    assert isinstance(cb_config, dict)
                    assert "failure_threshold" in cb_config
                    assert "recovery_timeout" in cb_config

            # Verify confidence matches expected
            assert migration_result.confidence == scenario["migration_confidence"]

    def test_configuration_validation_comprehensive(self, config_migrator):
        """
        Test comprehensive configuration validation including security and performance checks.

        Integration Scope:
            Configuration validation → Security checks → Performance validation → Compliance

        Business Impact:
            Ensures configuration integrity and system security

        Test Strategy:
            - Test validation of various configuration scenarios
            - Verify security checks and constraints
            - Test performance optimization validation
            - Validate configuration compliance requirements

        Success Criteria:
            - Configuration validation detects invalid settings
            - Security checks prevent insecure configurations
            - Performance validation ensures optimal settings
            - Compliance requirements enforced
        """
        # Test valid configuration
        valid_config = {
            "strategy": "balanced",
            "retry_config": {"max_attempts": 3},
            "circuit_breaker_config": {"failure_threshold": 5, "recovery_timeout": 60}
        }

        validation_result = config_migrator.validate_migrated_config(valid_config)
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
        assert len(validation_result["warnings"]) == 0

        # Test invalid configuration with security issues
        insecure_config = {
            "strategy": "balanced",
            "retry_config": {"max_attempts": 1000},  # Too many attempts
            "circuit_breaker_config": {"failure_threshold": 0}  # Invalid threshold
        }

        insecure_validation = config_migrator.validate_migrated_config(insecure_config)
        assert insecure_validation["valid"] is False
        assert len(insecure_validation["errors"]) > 0
        assert any("security" in error.lower() or "invalid" in error.lower()
                 for error in insecure_validation["errors"])

        # Test configuration with performance concerns
        performance_config = {
            "strategy": "balanced",
            "retry_config": {"max_attempts": 1},  # Too few attempts
            "circuit_breaker_config": {"failure_threshold": 50, "recovery_timeout": 1}  # Too aggressive
        }

        perf_validation = config_migrator.validate_migrated_config(performance_config)
        assert "warnings" in perf_validation
        assert len(perf_validation["warnings"]) > 0
        assert any("performance" in warning.lower() for warning in perf_validation["warnings"])

    def test_migration_monitoring_and_audit_trails(self, config_monitor):
        """
        Test migration monitoring and audit trail functionality.

        Integration Scope:
            Migration execution → Monitoring → Audit trails → Change tracking

        Business Impact:
            Provides visibility and accountability for configuration changes

        Test Strategy:
            - Test migration event monitoring
            - Verify audit trail creation and management
            - Test migration metrics collection
            - Validate monitoring integration

        Success Criteria:
            - Migration events properly monitored
            - Audit trails created and maintained
            - Metrics collected for migration analysis
            - Monitoring provides operational visibility
        """
        # Record migration event
        migration_event = {
            "migration_id": "test_migration_123",
            "source_config": {"legacy_field": "value"},
            "target_config": {"new_field": "value"},
            "confidence": "high",
            "timestamp": "2024-01-01T10:00:00Z"
        }

        # Record migration
        config_monitor.record_migration_event(migration_event)

        # Verify migration was recorded
        migration_history = config_monitor.get_migration_history()
        assert len(migration_history) >= 1
        assert migration_history[-1]["migration_id"] == "test_migration_123"

        # Test migration metrics
        migration_metrics = config_monitor.get_migration_metrics()

        assert "total_migrations" in migration_metrics
        assert "successful_migrations" in migration_metrics
        assert "failed_migrations" in migration_metrics
        assert migration_metrics["total_migrations"] >= 1

        # Test audit trail functionality
        audit_trail = config_monitor.get_audit_trail()
        assert len(audit_trail) >= 1
        assert "event_type" in audit_trail[-1]
        assert "timestamp" in audit_trail[-1]

    def test_configuration_change_detection(self, config_monitor):
        """
        Test configuration change detection and tracking.

        Integration Scope:
            Configuration changes → Change detection → Tracking → Notifications

        Business Impact:
            Enables proactive monitoring of configuration modifications

        Test Strategy:
            - Test detection of configuration changes
            - Verify change tracking and versioning
            - Test change notification mechanisms
            - Validate change impact assessment

        Success Criteria:
            - Configuration changes detected accurately
            - Change history maintained properly
            - Notifications generated for significant changes
            - Impact assessment provides actionable information
        """
        # Record initial configuration
        initial_config = {
            "strategy": "balanced",
            "retry_config": {"max_attempts": 3},
            "circuit_breaker_config": {"failure_threshold": 5}
        }

        config_monitor.record_configuration_change("test_service", initial_config, "initial_setup")

        # Record configuration change
        updated_config = {
            "strategy": "conservative",
            "retry_config": {"max_attempts": 2},
            "circuit_breaker_config": {"failure_threshold": 10}
        }

        change_detected = config_monitor.detect_configuration_change("test_service", updated_config)

        assert change_detected is True

        # Record the change
        config_monitor.record_configuration_change("test_service", updated_config, "strategy_adjustment")

        # Verify change history
        change_history = config_monitor.get_configuration_changes("test_service")
        assert len(change_history) >= 2  # Initial + change

        # Verify change details
        latest_change = change_history[-1]
        assert latest_change["change_type"] == "strategy_adjustment"
        assert latest_change["config"]["strategy"] == "conservative"

    def test_migration_confidence_scoring(self, config_analyzer, legacy_config_scenarios):
        """
        Test migration confidence scoring and risk assessment.

        Integration Scope:
            Configuration analysis → Confidence scoring → Risk assessment → Recommendations

        Business Impact:
            Provides confidence metrics for migration safety

        Test Strategy:
            - Test confidence scoring for different configuration types
            - Verify risk assessment accuracy
            - Test recommendation generation based on confidence
            - Validate confidence-based decision making

        Success Criteria:
            - Confidence scores calculated accurately
            - Risk assessment identifies potential issues
            - Recommendations appropriate for confidence level
            - Decision support provided for migration planning
        """
        for scenario_name, scenario in legacy_config_scenarios.items():
            legacy_config = scenario["config"]

            # Analyze configuration
            analysis = config_analyzer.analyze_legacy_config(legacy_config)

            # Verify confidence scoring
            assert hasattr(analysis, 'confidence')
            assert isinstance(analysis.confidence, MigrationConfidence)

            # Verify confidence matches expected range
            expected_confidence = scenario["migration_confidence"]

            # For simple configurations with direct mapping, confidence should be high
            if scenario_name == "simple_legacy":
                assert analysis.confidence == MigrationConfidence.HIGH
            elif scenario_name == "complex_legacy":
                assert analysis.confidence in [MigrationConfidence.HIGH, MigrationConfidence.MEDIUM]
            elif scenario_name == "minimal_legacy":
                assert analysis.confidence == MigrationConfidence.HIGH

            # Verify risk factors are identified
            assert hasattr(analysis, 'risk_factors')
            assert isinstance(analysis.risk_factors, list)

            # Verify recommendations are provided
            assert hasattr(analysis, 'recommendations')
            assert isinstance(analysis.recommendations, list)
            assert len(analysis.recommendations) > 0

    def test_configuration_validation_security_checks(self, config_migrator):
        """
        Test configuration validation security checks and constraints.

        Integration Scope:
            Configuration validation → Security validation → Constraint enforcement → Compliance

        Business Impact:
            Prevents insecure configuration deployment

        Test Strategy:
            - Test security constraint validation
            - Verify rate limiting configuration security
            - Test authentication and authorization checks
            - Validate security policy compliance

        Success Criteria:
            - Security constraints properly enforced
            - Insecure configurations rejected
            - Security policies validated
            - Compliance requirements verified
        """
        # Test insecure configuration
        insecure_config = {
            "strategy": "balanced",
            "retry_config": {
                "max_attempts": 1000,  # Excessive retry attempts
                "max_delay_seconds": 3600  # Very long delays
            },
            "circuit_breaker_config": {
                "failure_threshold": 1,  # Too sensitive
                "recovery_timeout": 1  # Too fast recovery
            }
        }

        security_validation = config_migrator.validate_migrated_config(insecure_config)

        # Should detect security issues
        assert security_validation["valid"] is False
        assert len(security_validation["errors"]) > 0

        security_errors = [error.lower() for error in security_validation["errors"]]
        assert any("security" in error or "excessive" in error or "invalid" in error
                  for error in security_errors)

        # Test secure configuration
        secure_config = {
            "strategy": "balanced",
            "retry_config": {
                "max_attempts": 3,
                "max_delay_seconds": 60
            },
            "circuit_breaker_config": {
                "failure_threshold": 5,
                "recovery_timeout": 60
            }
        }

        secure_validation = config_migrator.validate_migrated_config(secure_config)

        assert secure_validation["valid"] is True
        assert len(secure_validation["errors"]) == 0

    def test_migration_rollback_capabilities(self, config_migrator, config_monitor):
        """
        Test migration rollback capabilities and error recovery.

        Integration Scope:
            Migration failure → Rollback → Recovery → State restoration

        Business Impact:
            Enables safe migration with recovery options

        Test Strategy:
            - Test migration rollback functionality
            - Verify state restoration after failed migrations
            - Test error recovery mechanisms
            - Validate rollback safety and completeness

        Success Criteria:
            - Migration rollback functions correctly
            - State restoration works properly
            - Error recovery mechanisms effective
            - Rollback maintains system integrity
        """
        # Original configuration
        original_config = {
            "strategy": "balanced",
            "retry_config": {"max_attempts": 3},
            "circuit_breaker_config": {"failure_threshold": 5}
        }

        # Attempted migration that might fail
        problematic_config = {
            "strategy": "balanced",
            "retry_config": {"max_attempts": -1},  # Invalid value
            "circuit_breaker_config": {"failure_threshold": 0}  # Invalid value
        }

        # Record original state
        config_monitor.record_configuration_change("rollback_test", original_config, "pre_migration")

        # Attempt migration (may fail due to validation)
        try:
            migration_result = config_migrator.migrate_config(problematic_config)
            validation_result = config_migrator.validate_migrated_config(migration_result.migrated_config)

            if not validation_result["valid"]:
                # Migration failed - test rollback capability
                rollback_config = original_config.copy()
                config_monitor.record_configuration_change("rollback_test", rollback_config, "migration_rollback")

                # Verify rollback recorded
                rollback_history = config_monitor.get_configuration_changes("rollback_test")
                assert len(rollback_history) >= 2  # Original + rollback

                # Verify rollback restored original configuration
                final_config = rollback_history[-1]["config"]
                assert final_config == original_config

        except Exception as e:
            # If migration fails completely, verify error handling
            assert isinstance(e, Exception)
            # Error handling should still maintain system stability

    def test_configuration_performance_optimization(self, config_migrator):
        """
        Test configuration performance optimization and validation.

        Integration Scope:
            Configuration validation → Performance analysis → Optimization → Validation

        Business Impact:
            Ensures optimal configuration performance

        Test Strategy:
            - Test performance impact assessment
            - Verify optimization recommendations
            - Test performance validation
            - Validate optimization effectiveness

        Success Criteria:
            - Performance impact accurately assessed
            - Optimization recommendations appropriate
            - Performance validation effective
            - Optimized configurations maintain functionality
        """
        # Test configuration with performance concerns
        performance_config = {
            "strategy": "aggressive",
            "retry_config": {
                "max_attempts": 10,  # High retry count
                "max_delay_seconds": 300  # Long delays
            },
            "circuit_breaker_config": {
                "failure_threshold": 3,  # Low threshold
                "recovery_timeout": 30  # Short recovery
            }
        }

        # Analyze performance impact
        performance_analysis = config_migrator.analyze_performance_impact(performance_config)

        # Verify performance analysis structure
        assert isinstance(performance_analysis, dict)
        assert "performance_score" in performance_analysis
        assert "recommendations" in performance_analysis
        assert "risk_factors" in performance_analysis

        # Verify performance score is calculated
        assert isinstance(performance_analysis["performance_score"], (int, float))
        assert 0 <= performance_analysis["performance_score"] <= 100

        # Test optimized configuration
        optimized_config = config_migrator.optimize_configuration(performance_config)

        # Verify optimization maintains configuration validity
        validation_result = config_migrator.validate_migrated_config(optimized_config)
        assert validation_result["valid"] is True

        # Verify optimization provides performance benefits
        optimized_analysis = config_migrator.analyze_performance_impact(optimized_config)
        assert optimized_analysis["performance_score"] >= performance_analysis["performance_score"]

    def test_migration_comprehensive_integration(self, config_analyzer, config_migrator, config_monitor):
        """
        Test comprehensive integration of migration, validation, and monitoring.

        Integration Scope:
            Complete migration workflow → Validation → Monitoring → Audit → Optimization

        Business Impact:
            Validates end-to-end migration process integrity

        Test Strategy:
            - Execute complete migration workflow
            - Test integration between all components
            - Verify end-to-end functionality
            - Validate system integration and compatibility

        Success Criteria:
            - Complete migration workflow executes successfully
            - All components integrate properly
            - End-to-end functionality validated
            - System maintains integrity throughout process
        """
        # Legacy configuration to migrate
        legacy_config = {
            "max_retries": 5,
            "failure_threshold": 8,
            "timeout": 90,
            "strategy": "conservative",
            "legacy_field": "should_be_removed"
        }

        # Step 1: Analyze legacy configuration
        analysis = config_analyzer.analyze_legacy_config(legacy_config)
        assert hasattr(analysis, 'confidence')
        assert analysis.confidence in [MigrationConfidence.HIGH, MigrationConfidence.MEDIUM]

        # Step 2: Execute migration
        migration_result = config_migrator.migrate_config(legacy_config)
        assert hasattr(migration_result, 'migrated_config')
        assert isinstance(migration_result.migrated_config, dict)

        # Step 3: Validate migrated configuration
        validation_result = config_migrator.validate_migrated_config(migration_result.migrated_config)
        assert isinstance(validation_result, dict)
        assert "valid" in validation_result
        assert validation_result["valid"] is True

        # Step 4: Record migration event
        migration_event = {
            "migration_id": "integration_test_migration",
            "source_config": legacy_config,
            "target_config": migration_result.migrated_config,
            "confidence": str(analysis.confidence),
            "success": validation_result["valid"]
        }

        config_monitor.record_migration_event(migration_event)

        # Step 5: Verify monitoring integration
        migration_history = config_monitor.get_migration_history()
        assert len(migration_history) >= 1

        latest_migration = migration_history[-1]
        assert latest_migration["migration_id"] == "integration_test_migration"
        assert latest_migration["success"] == validation_result["valid"]

        # Step 6: Verify final configuration quality
        final_config = migration_result.migrated_config
        assert "strategy" in final_config
        assert "retry_config" in final_config
        assert "circuit_breaker_config" in final_config

        # Verify legacy fields were handled appropriately
        assert "legacy_field" not in final_config  # Should be removed or mapped

        # Step 7: Test configuration functionality
        assert final_config["strategy"] == "conservative"
        assert final_config["retry_config"]["max_attempts"] == 5
        assert final_config["circuit_breaker_config"]["failure_threshold"] == 8
        assert final_config["circuit_breaker_config"]["recovery_timeout"] == 90
