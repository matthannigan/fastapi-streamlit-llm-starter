"""
Environment Integration Test Fixtures

This module provides fixtures for environment detection integration testing, including
environment isolation, configuration management, module reloading utilities, and
integration with infrastructure components like security, cache, and resilience systems.
"""

import pytest
import os
import importlib
import sys
from typing import Dict, List, Optional
from unittest.mock import patch, Mock
from pathlib import Path

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentDetector,
    DetectionConfig,
    get_environment_info,
    is_production_environment,
    is_development_environment
)


@pytest.fixture(scope="function")
def clean_environment(monkeypatch):
    """
    Provides a clean environment for testing by backing up and restoring os.environ.

    This fixture ensures test isolation by:
    1. Backing up the current environment variables
    2. Clearing variables that affect environment detection
    3. Restoring the original environment after the test

    Use this fixture in ALL environment detection tests to prevent test pollution.

    Business Impact:
        Critical for test reliability and preventing test interference

    Use Cases:
        - Testing environment detection in controlled conditions
        - Verifying environment-specific behavior
        - Ensuring test isolation between different environment scenarios

    Cleanup:
        Original environment is completely restored after test completion
    """
    # Clear environment variables that affect detection
    env_vars_to_clear = [
        "ENVIRONMENT", "ENV", "APP_ENV", "STAGE", "DEPLOYMENT_ENVIRONMENT",
        "NODE_ENV", "FLASK_ENV", "DJANGO_SETTINGS_MODULE", "RAILS_ENV",
        "API_KEY", "ADDITIONAL_API_KEYS", "AUTH_MODE",
        "ENABLE_USER_TRACKING", "ENABLE_REQUEST_LOGGING",
        "ENABLE_AI_CACHE", "ENFORCE_AUTH", "DEBUG", "PRODUCTION",
        "PROD", "HOSTNAME", "CI", "RATE_LIMITING_ENABLED"
    ]

    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Disable rate limiting for testing
    monkeypatch.setenv('RATE_LIMITING_ENABLED', 'false')

    yield monkeypatch


# Note: The reload_environment_module fixture and its dependent fixtures have been removed
# as they are no longer needed with the app factory pattern. Each test now gets a fresh
# app instance that automatically picks up the current environment variables without
# requiring manual module reloading.


@pytest.fixture(scope="function")
def development_environment(clean_environment):
    """
    Configures environment variables for a development environment.

    This fixture sets ENVIRONMENT=development and development-specific indicators.
    The app factory pattern ensures these changes are automatically picked up
    by fresh app instances in each test.

    Business Impact:
        Enables testing of development-specific behaviors and configurations

    Use Cases:
        - Testing development-specific behavior
        - Verifying relaxed security in development
        - Testing cache optimization for development
    """
    os.environ["ENVIRONMENT"] = "development"

    yield Environment.DEVELOPMENT


@pytest.fixture(scope="function")
def production_environment(clean_environment):
    """
    Configures environment variables for a production environment.

    This fixture sets ENVIRONMENT=production and API keys for production security.
    The app factory pattern ensures these changes are automatically picked up
    by fresh app instances in each test.

    Business Impact:
        Enables testing of production security enforcement and configurations

    Use Cases:
        - Testing production security enforcement
        - Verifying API key requirements
        - Testing production-specific resilience settings
    """
    os.environ["ENVIRONMENT"] = "production"
    os.environ["API_KEY"] = "test-api-key-12345"
    os.environ["ADDITIONAL_API_KEYS"] = "test-key-2,test-key-3"

    yield Environment.PRODUCTION


@pytest.fixture(scope="function")
def staging_environment(clean_environment):
    """
    Configures environment variables for a staging environment.

    Business Impact:
        Enables testing of staging-specific configurations and behaviors

    Use Cases:
        - Testing staging-specific behavior
        - Verifying pre-production configurations
        - Testing integration with staging systems
    """
    os.environ["ENVIRONMENT"] = "staging"
    os.environ["API_KEY"] = "test-staging-api-key"

    yield Environment.STAGING


@pytest.fixture(scope="function")
def testing_environment(clean_environment):
    """
    Configures environment variables for a testing environment.

    Business Impact:
        Enables testing of CI/CD pipeline behaviors

    Use Cases:
        - Testing CI/CD pipeline behavior
        - Verifying automated test configurations
        - Testing environment detection in test scenarios
    """
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["CI"] = "true"

    yield Environment.TESTING


@pytest.fixture(scope="function")
def ai_enabled_environment(clean_environment):
    """
    Set up environment with AI features enabled.

    Business Impact:
        Enables testing of AI-specific feature contexts and optimizations

    Configuration:
        - ENABLE_AI_CACHE=true
        - AI-specific feature context testing
        - Cache optimization for AI workloads
    """
    os.environ["ENABLE_AI_CACHE"] = "true"

    yield


@pytest.fixture(scope="function")
def security_enforcement_environment(clean_environment):
    """
    Set up environment with security enforcement enabled.

    Business Impact:
        Enables testing of security context overrides and enforcement

    Configuration:
        - ENFORCE_AUTH=true
        - Security enforcement feature context
        - Production security requirements
    """
    os.environ["ENFORCE_AUTH"] = "true"

    yield


@pytest.fixture(scope="function")
def conflicting_signals_environment(clean_environment):
    """
    Set up environment with conflicting signals for fallback testing.

    Business Impact:
        Tests system reliability when environment detection is uncertain

    Configuration:
        - Conflicting environment indicators
        - Tests fallback behavior
        - Tests confidence scoring with conflicts
    """
    os.environ["ENVIRONMENT"] = "production"
    os.environ["NODE_ENV"] = "development"
    os.environ["DEBUG"] = "true"  # Usually indicates development

    yield


@pytest.fixture(scope="function")
def unknown_environment(clean_environment):
    """
    Environment with no clear indicators for fallback testing.

    Business Impact:
        Tests system behavior when environment cannot be determined

    Use Cases:
        - Testing fallback behavior
        - Verifying safe defaults
        - Testing low confidence detection
    """
    # Explicitly ensure no environment indicators are present
    yield


@pytest.fixture(scope="function")
def custom_detection_config():
    """
    Custom detection configuration for testing specialized scenarios.
    
    Business Impact:
        Enables testing of deployment flexibility and custom patterns
        
    Use Cases:
        - Testing custom environment detection patterns
        - Verifying custom environment variable precedence
        - Testing specialized deployment configurations
    """
    config = DetectionConfig(
        env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
        production_patterns=[r'.*live.*', r'.*prod.*', r'.*production.*'],
        development_patterns=[r'.*dev.*', r'.*develop.*'],
        staging_patterns=[r'.*stage.*', r'.*staging.*'],
        development_indicators=['.env', '.git', 'node_modules'],
        production_indicators=['/opt/app', '/var/app'],
        feature_contexts={
            FeatureContext.AI_ENABLED: {
                'environment_var': 'ENABLE_AI_FEATURES',
                'true_values': ['true', '1', 'enabled'],
                'metadata': {'ai_prefix': 'ai-'}
            },
            FeatureContext.SECURITY_ENFORCEMENT: {
                'environment_var': 'FORCE_SECURE_MODE', 
                'true_values': ['true', '1', 'yes'],
                'production_override': True
            }
        }
    )
    
    yield config


@pytest.fixture(scope="function")  
def environment_detector_with_config(custom_detection_config):
    """
    Environment detector with custom configuration.
    
    Business Impact:
        Enables testing of custom detection logic and specialized scenarios
        
    Use Cases:
        - Testing custom pattern matching
        - Verifying custom environment variable precedence
        - Testing feature-specific overrides
    """
    detector = EnvironmentDetector(custom_detection_config)
    yield detector


@pytest.fixture(scope="function")
def mock_system_indicators(tmp_path, monkeypatch):
    """
    Mock system indicators for testing file-based detection.
    
    Business Impact:
        Enables testing of system-level environment detection
        
    Use Cases:
        - Testing file-based environment detection
        - Verifying development environment indicators
        - Testing system-level environment detection
    """
    # Create temporary system indicator files
    (tmp_path / ".env").touch()
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()
    
    # Mock the current working directory to point to our temp path
    monkeypatch.chdir(tmp_path)
    
    yield tmp_path


# Convenience fixtures for common testing scenarios

@pytest.fixture(scope="function")
def prod_with_ai_features(clean_environment):
    """Production environment with AI features enabled."""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["ENABLE_AI_CACHE"] = "true"
    os.environ["API_KEY"] = "test-api-key-12345"
    yield


@pytest.fixture(scope="function")
def dev_with_security_enforcement(clean_environment):
    """Development environment with security enforcement enabled."""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["ENFORCE_AUTH"] = "true"
    yield


# Test client fixture for API testing
@pytest.fixture(scope="function")
def test_client():
    """
    Test client for API endpoint testing.

    Uses app factory pattern to ensure each test gets a fresh app instance
    that picks up the current environment configuration without any cached
    state from previous tests.

    Business Impact:
        Enables testing of API behavior under different environment configurations
        with complete test isolation.

    Use Cases:
        - Testing authentication behavior
        - Verifying API response differences by environment
        - Testing environment-aware API functionality
    """
    from fastapi.testclient import TestClient
    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client


# Session-scoped fixtures for expensive resources
@pytest.fixture(scope="session")
def test_database():
    """
    Test database for integration testing.
    
    Business Impact:
        Provides database access for testing environment-driven database configurations
        
    Use Cases:
        - Testing database connection behavior
        - Verifying environment-specific database settings
        - Testing data persistence across environment changes
    """
    # This would normally set up a test database
    # For now, return a mock or None since we don't have DB setup
    yield None


@pytest.fixture(scope="function")
def performance_monitor():
    """
    Performance monitoring for testing environment detection speed.
    
    Business Impact:
        Ensures environment detection meets performance SLAs
        
    Use Cases:
        - Testing detection speed under load
        - Verifying caching performance
        - Testing concurrent detection performance
    """
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.perf_counter()
            
        def stop(self):
            self.end_time = time.perf_counter()
            
        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None
            
    yield PerformanceMonitor()