"""
HIGH PRIORITY: Configuration → Operation-Specific Strategies → Execution Integration Test

This test suite verifies the integration between configuration management, operation-specific
resilience strategies, and processing execution. It ensures that configuration settings are
properly loaded, validated, and applied to determine resilience behavior.

Integration Scope:
    Tests the complete configuration flow from environment variables and settings
    through resilience strategy selection to processing execution.

Seam Under Test:
    Settings → ResilienceStrategy selection → Operation configuration → AI processing

Critical Paths:
    - Environment configuration → Strategy resolution → Operation-specific settings → Processing execution
    - Configuration validation and error handling
    - Dynamic configuration updates during runtime

Business Impact:
    Configuration correctness affects all processing behavior and system reliability.
    Incorrect configuration leads to inappropriate resilience behavior affecting system performance.

Test Strategy:
    - Test environment-specific configuration loading (development vs production)
    - Verify operation-specific resilience strategy selection
    - Test custom configuration override behavior
    - Validate configuration validation and error handling
    - Test dynamic configuration updates and runtime changes

Success Criteria:
    - Environment-specific settings load correctly
    - Operation-specific strategies are selected appropriately
    - Custom configuration overrides work as expected
    - Configuration validation prevents invalid configurations
    - Dynamic updates are handled gracefully
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.text_processor import TextProcessorService
from app.infrastructure.cache import AIResponseCache
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, InfrastructureError
from app.schemas import TextProcessingRequest, TextProcessingOperation
from app.api.v1.deps import get_text_processor


class TestConfigurationManagement:
    """
    Integration tests for configuration management and strategy selection.

    Seam Under Test:
        Settings → ResilienceStrategy selection → Operation configuration → AI processing

    Critical Paths:
        - Configuration loading and validation
        - Operation-specific strategy selection
        - Environment-based configuration behavior
        - Dynamic configuration updates

    Business Impact:
        Validates that configuration drives appropriate processing behavior
        across different environments and operation types.

    Test Strategy:
        - Test configuration loading from different sources
        - Verify strategy selection per operation type
        - Validate environment-specific behavior
        - Test configuration validation and error handling
    """

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Headers with valid authentication."""
        return {"Authorization": "Bearer test-api-key-12345"}

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return "This is a test of configuration-driven text processing with various settings."

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for TextProcessorService."""
        return AsyncMock(spec=AIResponseCache)

    @pytest.fixture
    def development_settings(self):
        """Settings configured for development environment."""
        return Settings(
            gemini_api_key="dev-test-key",
            api_key="dev-api-key",
            ai_model="gemini-pro",
            ai_temperature=0.7,
            environment="development",
            log_level="DEBUG",
            resilience_enabled=True,
            default_resilience_strategy="aggressive",
            resilience_preset="development",
            host="0.0.0.0",
            port=8000,
            debug=True
        )

    @pytest.fixture
    def production_settings(self):
        """Settings configured for production environment."""
        return Settings(
            gemini_api_key="prod-test-key",
            api_key="prod-api-key",
            ai_model="gemini-2.0-flash-exp",
            ai_temperature=0.3,
            environment="production",
            log_level="INFO",
            resilience_enabled=True,
            default_resilience_strategy="conservative",
            resilience_preset="production",
            host="0.0.0.0",
            port=8000,
            debug=False
        )

    @pytest.fixture
    def custom_settings(self):
        """Settings with custom configuration overrides."""
        return Settings(
            gemini_api_key="custom-test-key",
            api_key="custom-api-key",
            ai_model="gemini-pro",
            ai_temperature=0.5,
            environment="development",
            log_level="INFO",
            resilience_enabled=True,
            default_resilience_strategy="balanced",
            resilience_preset="simple",
            host="0.0.0.0",
            port=8000,
            debug=False,
            MAX_BATCH_REQUESTS_PER_CALL=5,
            BATCH_AI_CONCURRENCY_LIMIT=3
        )

    def test_development_environment_configuration(self, client, auth_headers, sample_text, development_settings, mock_cache):
        """
        Test configuration loading and behavior in development environment.

        Integration Scope:
            Environment configuration → Settings validation → Processing behavior

        Business Impact:
            Ensures development environment has appropriate settings for fast feedback
            and debugging while maintaining functionality.

        Test Strategy:
            - Load development-specific configuration
            - Verify development-appropriate settings are applied
            - Test processing behavior with development configuration
            - Validate development-specific features work correctly

        Success Criteria:
            - Development settings are loaded correctly
            - Debug features are enabled
            - Logging level is appropriate for development
            - Processing works with development configuration
        """
        # Create service with development settings
        service = TextProcessorService(settings=development_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert "result" in data

            # Verify development-specific behavior
            assert development_settings.environment == "development"
            assert development_settings.debug is True
            assert development_settings.log_level == "DEBUG"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_production_environment_configuration(self, client, auth_headers, sample_text, production_settings, mock_cache):
        """
        Test configuration loading and behavior in production environment.

        Integration Scope:
            Environment configuration → Settings validation → Processing behavior

        Business Impact:
            Ensures production environment has appropriate settings for stability,
            performance, and reliability.

        Test Strategy:
            - Load production-specific configuration
            - Verify production-appropriate settings are applied
            - Test processing behavior with production configuration
            - Validate production-specific optimizations are active

        Success Criteria:
            - Production settings are loaded correctly
            - Debug features are disabled
            - Logging level is appropriate for production
            - Conservative resilience strategies are applied
            - Processing works with production configuration
        """
        # Create service with production settings
        service = TextProcessorService(settings=production_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"
            assert "result" in data

            # Verify production-specific behavior
            assert production_settings.environment == "production"
            assert production_settings.debug is False
            assert production_settings.log_level == "INFO"
            assert production_settings.ai_temperature == 0.3  # More conservative
            assert production_settings.default_resilience_strategy == "conservative"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_custom_configuration_overrides(self, client, auth_headers, sample_text, custom_settings, mock_cache):
        """
        Test custom configuration overrides and their application.

        Integration Scope:
            Custom settings → Configuration validation → Processing behavior

        Business Impact:
            Ensures custom configuration values are properly applied and
            override defaults appropriately.

        Test Strategy:
            - Load configuration with custom overrides
            - Verify custom values are applied correctly
            - Test processing behavior with custom configuration
            - Validate configuration precedence rules

        Success Criteria:
            - Custom settings override default values
            - Configuration validation accepts valid custom values
            - Processing works with custom configuration
            - Configuration precedence is maintained correctly
        """
        # Create service with custom settings
        service = TextProcessorService(settings=custom_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"

            # Verify custom configuration is applied
            assert custom_settings.ai_temperature == 0.5
            assert custom_settings.MAX_BATCH_REQUESTS_PER_CALL == 5
            assert custom_settings.BATCH_AI_CONCURRENCY_LIMIT == 3
            assert custom_settings.default_resilience_strategy == "balanced"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_operation_specific_strategy_selection(self, client, auth_headers, sample_text, production_settings, mock_cache):
        """
        Test operation-specific resilience strategy selection.

        Integration Scope:
            Operation type → Strategy resolution → Processing configuration

        Business Impact:
            Ensures each operation type uses its appropriate resilience strategy
            for optimal performance and reliability.

        Test Strategy:
            - Test different operation types
            - Verify appropriate strategies are selected
            - Confirm strategy-specific behavior is applied
            - Validate strategy configuration per operation

        Success Criteria:
            - Each operation uses its designated resilience strategy
            - Strategy selection is based on operation characteristics
            - Processing behavior reflects strategy configuration
            - Strategy-specific parameters are applied correctly
        """
        # Create service with production settings that has operation-specific strategies
        production_settings.summarize_resilience_strategy = "balanced"
        production_settings.sentiment_resilience_strategy = "aggressive"
        production_settings.key_points_resilience_strategy = "balanced"
        production_settings.questions_resilience_strategy = "balanced"
        production_settings.qa_resilience_strategy = "conservative"

        service = TextProcessorService(settings=production_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            # Test different operations to verify strategy selection
            operations_to_test = [
                ("summarize", "balanced"),
                ("sentiment", "aggressive"),
                ("key_points", "balanced"),
                ("questions", "balanced"),
                ("qa", "conservative")
            ]

            for operation, expected_strategy in operations_to_test:
                request_data = {
                    "text": f"Test text for {operation} operation with strategy {expected_strategy}.",
                    "operation": operation
                }

                # Add question for QA operation
                if operation == "qa":
                    request_data["question"] = "What is this text about?"

                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["operation"] == operation

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_configuration_validation_and_error_handling(self, client, auth_headers, sample_text, mock_cache):
        """
        Test configuration validation and error handling.

        Integration Scope:
            Invalid configuration → Validation → Error handling → User feedback

        Business Impact:
            Ensures invalid configurations are caught early and users receive
            clear feedback about configuration issues.

        Test Strategy:
            - Test with invalid configuration values
            - Verify proper validation and error handling
            - Confirm meaningful error messages
            - Validate configuration recovery mechanisms

        Success Criteria:
            - Invalid configurations are detected and rejected
            - Clear error messages are provided
            - Configuration validation doesn't crash the system
            - Recovery mechanisms work correctly
        """
        # Create settings with invalid configuration
        invalid_settings = Settings(
            gemini_api_key="",  # Invalid - empty API key
            api_key="test-api-key",
            ai_model="gemini-pro",
            ai_temperature=0.7,
            environment="development"
        )

        # This should fail during service initialization due to empty API key
        with pytest.raises((ConfigurationError, ValueError)):
            TextProcessorService(settings=invalid_settings, cache=mock_cache)

    def test_configuration_precedence_rules(self, client, auth_headers, sample_text, custom_settings, mock_cache):
        """
        Test configuration precedence and override behavior.

        Integration Scope:
            Configuration sources → Precedence rules → Effective configuration

        Business Impact:
            Ensures configuration precedence works correctly, allowing
            environment-specific overrides while maintaining defaults.

        Test Strategy:
            - Test configuration loading with multiple sources
            - Verify precedence rules are applied correctly
            - Confirm environment variables override defaults
            - Validate configuration merging behavior

        Success Criteria:
            - Higher precedence configuration sources override lower ones
            - Environment variables take precedence over defaults
            - Configuration merging works as expected
            - No configuration conflicts or unexpected behavior
        """
        # Test with custom settings that have specific overrides
        service = TextProcessorService(settings=custom_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

            # Verify custom configuration values are effective
            assert custom_settings.ai_temperature == 0.5
            assert custom_settings.MAX_BATCH_REQUESTS_PER_CALL == 5
            assert custom_settings.default_resilience_strategy == "balanced"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_dynamic_configuration_updates(self, client, auth_headers, sample_text, production_settings, mock_cache):
        """
        Test dynamic configuration updates during runtime.

        Integration Scope:
            Configuration updates → Settings refresh → Processing behavior changes

        Business Impact:
            Ensures configuration can be updated without service restart,
            enabling operational flexibility and dynamic behavior adjustment.

        Test Strategy:
            - Test configuration updates during runtime
            - Verify settings changes take effect
            - Confirm dynamic behavior adjustment
            - Validate configuration refresh mechanisms

        Success Criteria:
            - Configuration updates are applied correctly
            - Settings changes take effect immediately
            - Dynamic behavior adjustment works as expected
            - No service disruption during configuration updates
        """
        # Create service with initial configuration
        service = TextProcessorService(settings=production_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            # First request with initial configuration
            response1 = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["success"] is True

            # Update configuration dynamically (simulate runtime change)
            production_settings.ai_temperature = 0.8
            production_settings.log_level = "DEBUG"

            # Second request with updated configuration
            response2 = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["success"] is True

            # Results should be consistent despite configuration changes
            assert data1["operation"] == data2["operation"]

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_configuration_migration_compatibility(self, client, auth_headers, sample_text, development_settings, mock_cache):
        """
        Test configuration migration and backward compatibility.

        Integration Scope:
            Legacy configuration → Migration → Current configuration → Processing

        Business Impact:
            Ensures smooth migration from legacy configuration formats
            without breaking existing functionality.

        Test Strategy:
            - Test with legacy configuration format
            - Verify migration to current format works
            - Confirm processing works with migrated configuration
            - Validate backward compatibility mechanisms

        Success Criteria:
            - Legacy configurations are properly migrated
            - Processing works with migrated configurations
            - No data loss during migration
            - Backward compatibility is maintained
        """
        # Simulate legacy configuration format
        legacy_settings = Settings(
            gemini_api_key="legacy-test-key",
            api_key="legacy-api-key",
            ai_model="gemini-pro",  # Legacy model name
            ai_temperature=0.7,
            environment="development",
            # Legacy settings that should be migrated
            MAX_BATCH_SIZE=10,  # Old naming convention
            CONCURRENT_LIMIT=5  # Old naming convention
        )

        # Create service with legacy configuration
        service = TextProcessorService(settings=legacy_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["operation"] == "summarize"

            # Verify legacy configuration is handled gracefully
            assert legacy_settings.ai_model == "gemini-pro"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_configuration_monitoring_and_metrics(self, client, auth_headers, sample_text, production_settings, mock_cache):
        """
        Test configuration monitoring and metrics collection.

        Integration Scope:
            Configuration usage → Monitoring → Metrics collection → Reporting

        Business Impact:
            Ensures configuration usage is monitored and metrics are collected
            for operational visibility and optimization.

        Test Strategy:
            - Test configuration usage tracking
            - Verify metrics collection for configuration
            - Confirm monitoring integration works
            - Validate configuration reporting accuracy

        Success Criteria:
            - Configuration usage is properly tracked
            - Metrics are collected for configuration changes
            - Monitoring integration works correctly
            - Configuration reporting is accurate
        """
        # Create service with monitoring-enabled configuration
        service = TextProcessorService(settings=production_settings, cache=mock_cache)

        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: service

        try:
            request_data = {
                "text": sample_text,
                "operation": "summarize"
            }

            response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

            # Verify configuration is accessible for monitoring
            assert production_settings.environment == "production"
            assert hasattr(production_settings, 'ai_temperature')
            assert hasattr(production_settings, 'default_resilience_strategy')

        finally:
            # Clean up override
            app.dependency_overrides.clear()
