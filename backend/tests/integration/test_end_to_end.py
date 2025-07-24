"""
Comprehensive backward compatibility integration tests.

This module provides end-to-end integration tests for backward compatibility,
covering real-world migration scenarios, API compatibility, and system integration.
"""

import pytest
import json
import os
import asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings
from app.infrastructure.resilience.config_presets import preset_manager, PRESETS
from app.infrastructure.resilience import AIServiceResilience
from app.schemas import TextProcessingRequest, TextProcessingOperation


class TestEndToEndBackwardCompatibility:
    """Test end-to-end backward compatibility across the entire system."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Headers with authentication for protected endpoints."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_legacy_environment_api_functionality(self, client, auth_headers):
        """Test that API functions correctly with legacy environment configuration."""
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative",
            "SENTIMENT_RESILIENCE_STRATEGY": "aggressive"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Clear the legacy config cache so it re-evaluates with new environment variables
            from app.core.config import settings
            if hasattr(settings, '_legacy_config_cache'):
                delattr(settings, '_legacy_config_cache')
            
            # Test resilience configuration endpoint
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config_data = response.json()
            assert config_data["is_legacy_config"] is True
            assert config_data["configuration"]["retry_attempts"] == 4
            assert config_data["configuration"]["circuit_breaker_threshold"] == 8
            
            # Test operation strategies
            assert config_data["operation_strategies"]["summarize"] == "conservative"
            assert config_data["operation_strategies"]["sentiment"] == "aggressive"
    
    def test_preset_environment_api_functionality(self, client, auth_headers):
        """Test that API functions correctly with preset configuration."""
        preset_env = {
            "RESILIENCE_PRESET": "production"
        }
        
        # Clear any legacy variables that might interfere
        legacy_vars_to_clear = [
            "RETRY_MAX_ATTEMPTS", 
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "DEFAULT_RESILIENCE_STRATEGY",
            "SUMMARIZE_RESILIENCE_STRATEGY",
            "SENTIMENT_RESILIENCE_STRATEGY",
            "KEY_POINTS_RESILIENCE_STRATEGY",
            "QUESTIONS_RESILIENCE_STRATEGY",
            "QA_RESILIENCE_STRATEGY"
        ]
        
        with patch.dict(os.environ, preset_env, clear=False):
            # Clear legacy variables specifically
            for var in legacy_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config_data = response.json()
            
            # Debug output (can be removed in production)
            # print(f"DEBUG: config_data = {config_data}")
            # print(f"DEBUG: is_legacy_config = {config_data.get('is_legacy_config')}")
            # print(f"DEBUG: preset_name = {config_data.get('preset_name')}")
            # print(f"DEBUG: retry_attempts = {config_data['configuration']['retry_attempts']}")
            
            assert config_data["is_legacy_config"] is False
            assert config_data["preset_name"] == "production"
            
            production_preset = PRESETS["production"]
            assert config_data["configuration"]["retry_attempts"] == production_preset.retry_attempts
            assert config_data["configuration"]["circuit_breaker_threshold"] == production_preset.circuit_breaker_threshold
    
    def test_mixed_configuration_api_functionality(self, client, auth_headers):
        """Test API functionality with mixed legacy and preset configuration."""
        mixed_env = {
            "RESILIENCE_PRESET": "development",  # Should be ignored
            "RETRY_MAX_ATTEMPTS": "6",           # Legacy takes precedence
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "9"
        }
        
        with patch.dict(os.environ, mixed_env):
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config_data = response.json()
            assert config_data["is_legacy_config"] is True
            # Legacy values should be used, not preset
            assert config_data["configuration"]["retry_attempts"] == 6
            assert config_data["configuration"]["circuit_breaker_threshold"] == 9
    
    def test_configuration_validation_api_backward_compatibility(self, client, auth_headers):
        """Test configuration validation API with backward compatibility."""
        # Test validation of legacy-like configuration
        legacy_style_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "default_strategy": "balanced"
        }
        
        response = client.post(
            "/resilience/validate",
            json={"configuration": legacy_style_config},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        validation_result = response.json()
        assert validation_result["is_valid"] is True
        
        # Test validation with preset-style advanced configuration
        advanced_config = {
            "retry_attempts": 5,
            "circuit_breaker_threshold": 8,
            "operation_overrides": {
                "summarize": "critical",
                "sentiment": "aggressive"
            },
            "exponential_multiplier": 1.5,
            "jitter_enabled": True
        }
        
        response = client.post(
            "/resilience/validate",
            json={"configuration": advanced_config},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        validation_result = response.json()
        assert validation_result["is_valid"] is True
    
    def test_preset_recommendation_with_legacy_context(self, client, auth_headers):
        """Test preset recommendations work with legacy configuration context."""
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "2",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "3",
            "DEFAULT_RESILIENCE_STRATEGY": "aggressive"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Test auto-recommendation
            response = client.get("/resilience/recommend-auto", headers=auth_headers)
            assert response.status_code == 200
            
            recommendation = response.json()
            # Should recommend development preset for these aggressive settings
            assert recommendation["recommended_preset"] == "development"
            
            # Test manual environment recommendation
            response = client.get("/resilience/recommend/development", headers=auth_headers)
            assert response.status_code == 200
            
            manual_recommendation = response.json()
            assert manual_recommendation["recommended_preset"] == "development"


class TestMigrationWorkflowIntegration:
    """Test complete migration workflows from legacy to preset configuration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Headers with authentication for protected endpoints."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def _preserve_essential_env_vars(self, env_dict):
        """Preserve essential environment variables when clearing environment."""
        import os
        preserved_vars = {}
        for key in ["API_KEY", "ADDITIONAL_API_KEYS", "GEMINI_API_KEY", "PYTEST_CURRENT_TEST"]:
            if key in os.environ:
                preserved_vars[key] = os.environ[key]
        
        env_dict.update(preserved_vars)
        return env_dict
    
    def test_complete_migration_workflow(self, client, auth_headers):
        """Test complete migration workflow from legacy to preset configuration."""
        # Phase 1: Start with legacy configuration
        initial_legacy_env = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "7",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "90",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative",
            "QA_RESILIENCE_STRATEGY": "critical"
        }
        
        with patch.dict(os.environ, initial_legacy_env):
            # Step 1: Analyze current configuration
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            current_config = response.json()
            assert current_config["is_legacy_config"] is True
            
            # Step 2: Get migration recommendation
            response = client.get("/resilience/recommend-auto", headers=auth_headers)
            assert response.status_code == 200
            
            recommendation = response.json()
            suggested_preset = recommendation["recommended_preset"]
            
            # Step 3: Create migration configuration
            migration_config = {
                "retry_attempts": current_config["configuration"]["retry_attempts"],
                "circuit_breaker_threshold": current_config["configuration"]["circuit_breaker_threshold"],
                "recovery_timeout": current_config["configuration"]["recovery_timeout"],
                "default_strategy": current_config["configuration"]["default_strategy"],
                "operation_overrides": {
                    "summarize": current_config["operation_strategies"]["summarize"],
                    "qa": current_config["operation_strategies"]["qa"]
                }
            }
            
            # Step 4: Validate migration configuration
            response = client.post(
                "/resilience/validate",
                json={"configuration": migration_config},
                headers=auth_headers
            )
            assert response.status_code == 200
            
            validation_result = response.json()
            assert validation_result["is_valid"] is True
        
        # Phase 2: Test with preset + custom config (migration complete)
        migration_env = {
            "RESILIENCE_PRESET": suggested_preset,
            "RESILIENCE_CUSTOM_CONFIG": json.dumps(migration_config)
        }
        
        migration_env = self._preserve_essential_env_vars(migration_env)
        
        with patch.dict(os.environ, migration_env, clear=True):
            # Verify migrated configuration works
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            migrated_config = response.json()
            assert migrated_config["is_legacy_config"] is False
            assert migrated_config["preset_name"] == suggested_preset
            
            # Verify behavior is preserved
            assert migrated_config["configuration"]["retry_attempts"] == migration_config["retry_attempts"]
            assert migrated_config["configuration"]["circuit_breaker_threshold"] == migration_config["circuit_breaker_threshold"]
            assert migrated_config["operation_strategies"]["summarize"] == migration_config["operation_overrides"]["summarize"]
    
    def test_gradual_migration_with_rollback(self, client, auth_headers):
        """Test gradual migration with rollback capability."""
        # Original legacy configuration
        original_legacy = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced"
        }
        
        # Phase 1: Baseline with legacy
        with patch.dict(os.environ, original_legacy):
            baseline_response = client.get("/resilience/config", headers=auth_headers)
            baseline_config = baseline_response.json()
        
        # Phase 2: Migrate to preset
        preset_env = {"RESILIENCE_PRESET": "simple"}
        preset_env = self._preserve_essential_env_vars(preset_env)
        
        with patch.dict(os.environ, preset_env, clear=True):
            preset_response = client.get("/resilience/config", headers=auth_headers)
            preset_config = preset_response.json()
            
            # Verify preset configuration
            assert preset_config["is_legacy_config"] is False
            assert preset_config["preset_name"] == "simple"
        
        # Phase 3: Rollback to legacy (simulate rollback scenario)
        rollback_env = self._preserve_essential_env_vars(original_legacy.copy())
        with patch.dict(os.environ, rollback_env, clear=True):
            rollback_response = client.get("/resilience/config", headers=auth_headers)
            rollback_config = rollback_response.json()
            
            # Should match original baseline
            assert rollback_config["is_legacy_config"] is True
            assert rollback_config["configuration"]["retry_attempts"] == baseline_config["configuration"]["retry_attempts"]
            assert rollback_config["configuration"]["circuit_breaker_threshold"] == baseline_config["configuration"]["circuit_breaker_threshold"]
    
    def test_zero_downtime_migration_simulation(self, client, auth_headers):
        """Test zero-downtime migration simulation."""
        # Simulate a zero-downtime migration by testing configuration
        # changes without service restart
        
        # Phase 1: Legacy configuration
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "6"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Test API availability
            response = client.get("/health")
            assert response.status_code == 200
            
            # Test resilience endpoints
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            legacy_config = response.json()
            assert legacy_config["is_legacy_config"] is True
        
        # Phase 2: Switch to preset (simulating hot reload)
        preset_env = {"RESILIENCE_PRESET": "production"}
        preset_env = self._preserve_essential_env_vars(preset_env)
        
        with patch.dict(os.environ, preset_env, clear=True):
            # API should still be available
            response = client.get("/health")
            assert response.status_code == 200
            
            # Configuration should update
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            preset_config = response.json()
            assert preset_config["is_legacy_config"] is False
            assert preset_config["preset_name"] == "production"


class TestRealWorldScenarioIntegration:
    """Test real-world deployment scenarios with backward compatibility."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Headers with authentication for protected endpoints."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def _preserve_essential_env_vars(self, env_dict):
        """Preserve essential environment variables when clearing environment."""
        import os
        preserved_vars = {}
        for key in ["API_KEY", "ADDITIONAL_API_KEYS", "GEMINI_API_KEY", "PYTEST_CURRENT_TEST"]:
            if key in os.environ:
                preserved_vars[key] = os.environ[key]
        
        env_dict.update(preserved_vars)
        return env_dict
    
    def test_kubernetes_deployment_scenario(self, client, auth_headers):
        """Test Kubernetes deployment scenario with ConfigMap migration."""
        # Simulate Kubernetes ConfigMap with legacy configuration
        k8s_legacy_config = {
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "120",
            "DEFAULT_RESILIENCE_STRATEGY": "conservative",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative",
            "SENTIMENT_RESILIENCE_STRATEGY": "aggressive",
            "QA_RESILIENCE_STRATEGY": "critical"
        }
        
        with patch.dict(os.environ, k8s_legacy_config):
            # Test pod startup with legacy config
            response = client.get("/health")
            assert response.status_code == 200
            
            # Verify configuration loads correctly
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            assert config["is_legacy_config"] is True
            assert config["configuration"]["retry_attempts"] == 5
            assert config["configuration"]["circuit_breaker_threshold"] == 10
        
        # Simulate ConfigMap update to preset-based configuration
        k8s_preset_config = {
            "RESILIENCE_PRESET": "production",
            "RESILIENCE_CUSTOM_CONFIG": json.dumps({
                "operation_overrides": {
                    "summarize": "conservative",
                    "sentiment": "aggressive", 
                    "qa": "critical"
                }
            })
        }
        
        k8s_preset_config = self._preserve_essential_env_vars(k8s_preset_config)
        with patch.dict(os.environ, k8s_preset_config, clear=True):
            # Test pod with new configuration
            response = client.get("/health")
            assert response.status_code == 200
            
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            assert config["is_legacy_config"] is False
            assert config["preset_name"] == "production"
    
    def test_docker_compose_environment_scenario(self, client, auth_headers):
        """Test Docker Compose environment scenario."""
        # Simulate Docker Compose environment file with mixed configuration
        docker_env = {
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "RESILIENCE_PRESET": "production",
            # Some legacy variables still present (cleanup in progress)
            "RETRY_MAX_ATTEMPTS": "6",  # Should override preset
            "RESILIENCE_METRICS_ENABLED": "true"
        }
        
        with patch.dict(os.environ, docker_env):
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            # Legacy should take precedence
            assert config["is_legacy_config"] is True
            assert config["configuration"]["retry_attempts"] == 6
    
    def test_cloud_deployment_scenario(self, client, auth_headers):
        """Test cloud deployment scenario with environment-based configuration."""
        # Simulate cloud deployment with environment detection
        cloud_prod_env = {
            "CLOUD_PROVIDER": "aws",
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgres://prod-cluster/db",
            "RESILIENCE_PRESET": "production"
        }
        cloud_prod_env = self._preserve_essential_env_vars(cloud_prod_env)
        
        with patch.dict(os.environ, cloud_prod_env, clear=True):
            # Test environment detection
            response = client.get("/resilience/recommend-auto", headers=auth_headers)
            assert response.status_code == 200
            
            recommendation = response.json()
            assert recommendation["recommended_preset"] == "production"
            assert recommendation["environment_detected"] == "production (auto-detected)"
            
            # Test configuration
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            assert config["preset_name"] == "production"
    
    def test_development_environment_scenario(self, client, auth_headers):
        """Test development environment scenario."""
        dev_env = {
            "DEBUG": "true",
            "NODE_ENV": "development",
            "HOST": "localhost:8000",
            "RESILIENCE_PRESET": "development"
        }
        dev_env = self._preserve_essential_env_vars(dev_env)
        
        with patch.dict(os.environ, dev_env, clear=True):
            # Test auto-detection
            response = client.get("/resilience/recommend-auto", headers=auth_headers)
            assert response.status_code == 200
            
            recommendation = response.json()
            assert recommendation["recommended_preset"] == "development"
            assert "development" in recommendation["environment_detected"].lower()
            
            # Development preset should be optimized for fast feedback
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            assert config["preset_name"] == "development"
            # Development should have lower retry attempts for faster feedback
            assert config["configuration"]["retry_attempts"] <= 3


class TestCompatibilityWithExternalSystems:
    """Test compatibility with external monitoring and management systems."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Headers with authentication for protected endpoints."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_monitoring_system_compatibility(self, client, auth_headers):
        """Test compatibility with monitoring systems that depend on configuration."""
        # Simulate monitoring system checking configuration
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8",
            "RESILIENCE_METRICS_ENABLED": "true"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Test metrics endpoint availability
            response = client.get("/resilience/metrics", headers=auth_headers)
            assert response.status_code == 200
            
            # Test configuration export for monitoring
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            
            # Verify monitoring can read configuration format
            assert "configuration" in config
            assert "operation_strategies" in config
            assert "is_legacy_config" in config
            
            # Monitoring system should be able to extract retry attempts
            assert config["configuration"]["retry_attempts"] == 4
    
    def test_configuration_management_system_compatibility(self, client, auth_headers):
        """Test compatibility with configuration management systems."""
        # Test template-based configuration for config management systems
        response = client.get("/resilience/templates", headers=auth_headers)
        assert response.status_code == 200
        
        templates = response.json()
        assert len(templates) > 0
        
        # Test validation of template-based configuration
        template_config = {
            "template_name": "robust_production",
            "overrides": {
                "retry_attempts": 7
            }
        }
        
        response = client.post("/resilience/validate-template", json=template_config, headers=auth_headers)
        assert response.status_code == 200
        
        validation_result = response.json()
        assert validation_result["is_valid"] is True
    
    def test_api_versioning_compatibility(self, client, auth_headers):
        """Test API versioning compatibility for backward compatibility."""
        # Test that old API endpoints still work
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Test legacy-style configuration endpoint
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            config = response.json()
            # Should include backward-compatible fields
            assert "configuration" in config
            assert "retry_attempts" in config["configuration"]
            assert "circuit_breaker_threshold" in config["configuration"]
            
            # Should also include new fields for forward compatibility
            assert "preset_name" in config
            assert "is_legacy_config" in config
    
    def test_configuration_export_import_compatibility(self, client, auth_headers):
        """Test configuration export/import for backup and migration systems."""
        production_env = {"RESILIENCE_PRESET": "production"}
        
        with patch.dict(os.environ, production_env):
            # Export current configuration
            response = client.get("/resilience/config", headers=auth_headers)
            assert response.status_code == 200
            
            exported_config = response.json()
            
            # Configuration should be exportable
            assert "preset_name" in exported_config
            assert "configuration" in exported_config
            assert "operation_strategies" in exported_config
            
            # Extract configuration for reimport
            reimport_config = {
                "retry_attempts": exported_config["configuration"]["retry_attempts"],
                "circuit_breaker_threshold": exported_config["configuration"]["circuit_breaker_threshold"],
                "default_strategy": exported_config["configuration"]["default_strategy"],
                "operation_overrides": exported_config["operation_strategies"]
            }
            
            # Test validation of reimported configuration
            response = client.post(
                "/resilience/validate",
                json={"configuration": reimport_config},
                headers=auth_headers
            )
            assert response.status_code == 200
            
            validation_result = response.json()
            assert validation_result["is_valid"] is True