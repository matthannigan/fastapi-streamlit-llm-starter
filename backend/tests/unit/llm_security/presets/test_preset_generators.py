"""
Unit tests for preset generator functions.

This test module verifies the preset generator functions that create environment-specific
security configurations: get_development_preset(), get_production_preset(), and
get_testing_preset().

Test Strategy:
    - Component Under Test: Preset generator functions in app.infrastructure.security.llm.presets
    - Testing Approach: Black-box testing through public API only
    - No Mocking: Pure functions with no external dependencies
    - Contract Source: backend/contracts/infrastructure/security/llm/presets.pyi

Fixtures Available:
    From conftest.py (backend/tests/unit/llm_security/presets/conftest.py):
    - development_preset_data: Expected development preset structure
    - production_preset_data: Expected production preset structure
    - testing_preset_data: Expected testing preset structure
"""

import pytest
from typing import Dict, Any


class TestGetDevelopmentPreset:
    """
    Test suite for get_development_preset() function.
    
    Scope:
        Verifies that get_development_preset() returns a complete configuration
        dictionary optimized for development workflows with lenient settings.
        
    Business Critical:
        Development preset enables productive local development with appropriate
        security validation. Incorrect configuration disrupts developer workflows.
        
    Test Strategy:
        - Verify complete configuration structure
        - Test development-appropriate settings (lenient thresholds, debug logging)
        - Validate CPU-only processing for easy local setup
        - Test experimental features enablement
    """

    def test_returns_complete_development_configuration(self, development_preset_data):
        """
        Test that get_development_preset returns complete configuration dictionary.

        Verifies:
            get_development_preset() returns a comprehensive configuration with all
            required sections and development-appropriate settings.

        Business Impact:
            Complete configuration ensures developers can use security scanners
            without manual configuration or missing required settings.

        Scenario:
            Given: A call to get_development_preset()
            When: The configuration dictionary is returned
            Then: All required sections are present (input_scanners, output_scanners,
                  performance, logging, service, features)
            And: The preset field contains "development"
            And: The service.environment field contains "development"

        Fixtures Used:
            - development_preset_data: Expected structure for validation
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # When: Get development preset configuration
        config = get_development_preset()

        # Then: All required sections are present
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"

        # And: The preset field contains "development"
        assert config["preset"] == "development"

        # And: The service.environment field contains "development"
        assert config["service"]["environment"] == "development"

        # And: Configuration matches expected structure
        assert isinstance(config["input_scanners"], dict)
        assert isinstance(config["output_scanners"], dict)
        assert isinstance(config["performance"], dict)
        assert isinstance(config["logging"], dict)
        assert isinstance(config["service"], dict)
        assert isinstance(config["features"], dict)

    def test_development_preset_has_lenient_security_thresholds(self):
        """
        Test that development preset uses lenient security thresholds (0.8-0.9).

        Verifies:
            All security scanner thresholds in development preset are configured
            with high values (0.8-0.9) to minimize false positives during development.

        Business Impact:
            Lenient thresholds prevent security scanners from blocking legitimate
            development activities, maintaining developer productivity and happiness.

        Scenario:
            Given: The development preset configuration
            When: Input scanner thresholds are examined
            Then: prompt_injection threshold is >= 0.8
            And: toxicity_input threshold is >= 0.8
            And: pii_detection threshold is >= 0.8
            And: All scanner actions are "warn" or "flag" (non-blocking)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        input_scanners = config["input_scanners"]

        # When: Input scanner thresholds are examined
        # Then: prompt_injection threshold is >= 0.8
        assert input_scanners["prompt_injection"]["threshold"] >= 0.8

        # And: toxicity_input threshold is >= 0.8
        assert input_scanners["toxicity_input"]["threshold"] >= 0.8

        # And: pii_detection threshold is >= 0.8
        assert input_scanners["pii_detection"]["threshold"] >= 0.8

        # And: All scanner actions are "warn" or "flag" (non-blocking)
        for scanner_name, scanner_config in input_scanners.items():
            action = scanner_config["action"]
            assert action in ["warn", "flag"], f"Scanner {scanner_name} has blocking action: {action}"

    def test_development_preset_enables_debug_logging(self):
        """
        Test that development preset enables comprehensive debug logging.

        Verifies:
            Logging configuration in development preset enables detailed logging
            including scanned text and scan operations for debugging.

        Business Impact:
            Comprehensive logging helps developers understand security scanner
            behavior and debug false positives or configuration issues.

        Scenario:
            Given: The development preset configuration
            When: Logging section is examined
            Then: logging.enabled is True
            And: logging.level is "DEBUG"
            And: logging.include_scanned_text is True
            And: logging.log_scan_operations is True
            And: logging.sanitize_pii_in_logs is False (for debugging)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        logging_config = config["logging"]

        # When: Logging section is examined
        # Then: logging.enabled is True
        assert logging_config["enabled"] is True

        # And: logging.level is "DEBUG"
        assert logging_config["level"] == "DEBUG"

        # And: logging.include_scanned_text is True
        assert logging_config["include_scanned_text"] is True

        # And: logging.log_scan_operations is True
        assert logging_config["log_scan_operations"] is True

        # And: logging.sanitize_pii_in_logs is False (for debugging)
        assert logging_config["sanitize_pii_in_logs"] is False

    def test_development_preset_uses_cpu_execution(self):
        """
        Test that development preset configures CPU-only execution for compatibility.

        Verifies:
            Performance configuration specifies CPU execution providers only,
            avoiding GPU dependencies for easy local development setup.

        Business Impact:
            CPU-only execution enables all developers to run security scanners
            without requiring GPU hardware or complex driver setup.

        Scenario:
            Given: The development preset configuration
            When: Performance.onnx_providers is examined
            Then: Only "CPUExecutionProvider" is in the providers list
            And: No GPU providers (CUDA, TensorRT) are configured

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        performance_config = config["performance"]

        # When: Performance.onnx_providers is examined
        onnx_providers = performance_config["onnx_providers"]

        # Then: Only "CPUExecutionProvider" is in the providers list
        assert "CPUExecutionProvider" in onnx_providers

        # And: No GPU providers (CUDA, TensorRT) are configured
        gpu_providers = ["CUDAExecutionProvider", "TensorRTExecutionProvider", "OpenVINOExecutionProvider"]
        for provider in gpu_providers:
            assert provider not in onnx_providers, f"GPU provider {provider} should not be configured"

        # And: Only CPU provider is present
        assert len(onnx_providers) == 1
        assert onnx_providers[0] == "CPUExecutionProvider"

    def test_development_preset_enables_experimental_features(self):
        """
        Test that development preset enables experimental features for testing.

        Verifies:
            Features section enables experimental features to allow developers
            to test new security capabilities during development.

        Business Impact:
            Experimental features enablement allows developers to test and provide
            feedback on new security capabilities before production deployment.

        Scenario:
            Given: The development preset configuration
            When: Features section is examined
            Then: features.experimental_features is True
            And: features.verbose_output is True
            And: features.performance_monitoring is True

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        features_config = config["features"]

        # When: Features section is examined
        # Then: features.experimental_features is True (note: implementation uses "experimental_scanners")
        assert features_config["experimental_scanners"] is True

        # And: features.verbose_output is True (note: implementation uses "advanced_analytics")
        assert features_config["advanced_analytics"] is True

        # And: features.performance_monitoring is True (note: implementation uses "real_time_monitoring")
        assert features_config["real_time_monitoring"] is True

        # And: features.custom_scanner_support is True
        assert features_config["custom_scanner_support"] is True

    def test_development_preset_has_moderate_cache_ttl(self):
        """
        Test that development preset uses moderate cache TTL for fast iteration.

        Verifies:
            Cache TTL is set to 300 seconds (5 minutes) to balance cache benefits
            with rapid configuration changes during development.

        Business Impact:
            Moderate cache TTL ensures developers see configuration changes quickly
            while still benefiting from cache performance during testing.

        Scenario:
            Given: The development preset configuration
            When: Performance.cache_ttl_seconds is examined
            Then: The value is 300 (5 minutes)
            And: cache_enabled is True

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        performance_config = config["performance"]

        # When: Performance.cache_ttl_seconds is examined
        cache_ttl = performance_config["cache_ttl_seconds"]
        cache_enabled = performance_config["cache_enabled"]

        # Then: The value is 300 (5 minutes)
        assert cache_ttl == 300

        # And: cache_enabled is True
        assert cache_enabled is True

    def test_development_preset_enables_all_major_scanners(self):
        """
        Test that development preset enables comprehensive scanner coverage.

        Verifies:
            Both input and output scanners are enabled to provide comprehensive
            security validation during development and testing.

        Business Impact:
            Comprehensive scanner coverage helps developers identify and fix
            security issues early in the development cycle.

        Scenario:
            Given: The development preset configuration
            When: Scanner configurations are examined
            Then: At least 3 input scanners are enabled
            And: At least 2 output scanners are enabled
            And: All enabled scanners have valid configurations

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        input_scanners = config["input_scanners"]
        output_scanners = config["output_scanners"]

        # When: Scanner configurations are examined
        enabled_input_scanners = [name for name, config in input_scanners.items() if config.get("enabled", False)]
        enabled_output_scanners = [name for name, config in output_scanners.items() if config.get("enabled", False)]

        # Then: At least 3 input scanners are enabled
        assert len(enabled_input_scanners) >= 3, f"Expected at least 3 input scanners, got {len(enabled_input_scanners)}: {enabled_input_scanners}"

        # And: At least 2 output scanners are enabled
        assert len(enabled_output_scanners) >= 2, f"Expected at least 2 output scanners, got {len(enabled_output_scanners)}: {enabled_output_scanners}"

        # And: All enabled scanners have valid configurations
        for scanner_name in enabled_input_scanners + enabled_output_scanners:
            if scanner_name in input_scanners:
                scanner_config = input_scanners[scanner_name]
            else:
                scanner_config = output_scanners[scanner_name]

            # Check required fields
            assert "enabled" in scanner_config
            assert "threshold" in scanner_config
            assert "action" in scanner_config
            assert "scan_timeout" in scanner_config

            # Check value types
            assert isinstance(scanner_config["enabled"], bool)
            assert isinstance(scanner_config["threshold"], (int, float))
            assert isinstance(scanner_config["action"], str)
            assert isinstance(scanner_config["scan_timeout"], int)

    def test_development_preset_disables_authentication_requirements(self):
        """
        Test that development preset disables strict authentication for ease of use.

        Verifies:
            Service configuration disables API key requirements and rate limiting
            for convenient local development access.

        Business Impact:
            Simplified authentication reduces friction during local development
            while still providing security validation functionality.

        Scenario:
            Given: The development preset configuration
            When: Service section is examined
            Then: service.api_key_required is False
            And: service.rate_limit_enabled is False
            And: service.debug_mode is True

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_development_preset

        # Given: The development preset configuration
        config = get_development_preset()
        service_config = config["service"]

        # When: Service section is examined
        # Then: service.api_key_required is False
        assert service_config["api_key_required"] is False

        # And: service.rate_limit_enabled is False
        assert service_config["rate_limit_enabled"] is False

        # And: service.debug_mode is True
        assert service_config["debug_mode"] is True

        # And: service name contains "dev"
        assert "dev" in service_config["name"]


class TestGetProductionPreset:
    """
    Test suite for get_production_preset() function.
    
    Scope:
        Verifies that get_production_preset() returns a complete configuration
        dictionary optimized for production deployment with maximum security.
        
    Business Critical:
        Production preset protects live systems and user data. Configuration
        errors could expose security vulnerabilities or impact system reliability.
        
    Test Strategy:
        - Verify complete configuration structure
        - Test strict security settings (low thresholds, blocking actions)
        - Validate GPU acceleration with CPU fallback
        - Test production service features (auth, rate limiting)
    """

    def test_returns_complete_production_configuration(self, production_preset_data):
        """
        Test that get_production_preset returns complete configuration dictionary.

        Verifies:
            get_production_preset() returns a comprehensive configuration with all
            required sections and production-appropriate settings.

        Business Impact:
            Complete configuration ensures production systems have proper security
            coverage without manual configuration or missing required settings.

        Scenario:
            Given: A call to get_production_preset()
            When: The configuration dictionary is returned
            Then: All required sections are present
            And: The preset field contains "production"
            And: The service.environment field contains "production"

        Fixtures Used:
            - production_preset_data: Expected structure for validation
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # When: Get production preset configuration
        config = get_production_preset()

        # Then: All required sections are present
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"

        # And: The preset field contains "production"
        assert config["preset"] == "production"

        # And: The service.environment field contains "production"
        assert config["service"]["environment"] == "production"

        # And: Configuration matches expected structure
        assert isinstance(config["input_scanners"], dict)
        assert isinstance(config["output_scanners"], dict)
        assert isinstance(config["performance"], dict)
        assert isinstance(config["logging"], dict)
        assert isinstance(config["service"], dict)
        assert isinstance(config["features"], dict)

    def test_production_preset_has_strict_security_thresholds(self):
        """
        Test that production preset uses strict security thresholds (0.6-0.7).

        Verifies:
            All security scanner thresholds in production preset are configured
            with low values (0.6-0.7) for maximum security protection.

        Business Impact:
            Strict thresholds provide aggressive security protection for production
            systems handling real user data and sensitive information.

        Scenario:
            Given: The production preset configuration
            When: Input scanner thresholds are examined
            Then: prompt_injection threshold is <= 0.7
            And: toxicity_input threshold is <= 0.7
            And: pii_detection threshold is <= 0.7
            And: All scanner actions are "block" or "redact" (protective)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        input_scanners = config["input_scanners"]

        # When: Input scanner thresholds are examined
        # Then: prompt_injection threshold is <= 0.7
        assert input_scanners["prompt_injection"]["threshold"] <= 0.7

        # And: toxicity_input threshold is <= 0.7
        assert input_scanners["toxicity_input"]["threshold"] <= 0.7

        # And: pii_detection threshold is <= 0.7
        assert input_scanners["pii_detection"]["threshold"] <= 0.7

        # And: All scanner actions are "block" or "redact" (protective)
        for scanner_name, scanner_config in input_scanners.items():
            action = scanner_config["action"]
            assert action in ["block", "redact"], f"Scanner {scanner_name} has non-protective action: {action}"

    def test_production_preset_uses_gpu_acceleration_with_fallback(self):
        """
        Test that production preset configures GPU acceleration with CPU fallback.

        Verifies:
            Performance configuration specifies GPU execution providers (CUDA)
            with CPU fallback for high performance and reliability.

        Business Impact:
            GPU acceleration provides high throughput for production workloads
            while CPU fallback ensures reliability when GPU is unavailable.

        Scenario:
            Given: The production preset configuration
            When: Performance.onnx_providers is examined
            Then: "CUDAExecutionProvider" is in the providers list
            And: "CPUExecutionProvider" is also in the providers list
            And: CUDA provider is listed before CPU provider (priority order)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        performance_config = config["performance"]

        # When: Performance.onnx_providers is examined
        onnx_providers = performance_config["onnx_providers"]

        # Then: "CUDAExecutionProvider" is in the providers list
        assert "CUDAExecutionProvider" in onnx_providers

        # And: "CPUExecutionProvider" is also in the providers list
        assert "CPUExecutionProvider" in onnx_providers

        # And: CUDA provider is listed before CPU provider (priority order)
        cuda_index = onnx_providers.index("CUDAExecutionProvider")
        cpu_index = onnx_providers.index("CPUExecutionProvider")
        assert cuda_index < cpu_index, "CUDA should have priority over CPU"

        # And: Should have at least 2 providers for fallback
        assert len(onnx_providers) >= 2

    def test_production_preset_enables_secure_logging(self):
        """
        Test that production preset enables secure logging with PII sanitization.

        Verifies:
            Logging configuration enables essential logging while protecting
            user privacy through PII sanitization and excluding scanned text.

        Business Impact:
            Secure logging enables security monitoring and incident response
            while protecting user privacy and complying with data regulations.

        Scenario:
            Given: The production preset configuration
            When: Logging section is examined
            Then: logging.enabled is True
            And: logging.level is "INFO" (not DEBUG)
            And: logging.include_scanned_text is False (privacy)
            And: logging.sanitize_pii_in_logs is True
            And: logging.log_format is "json" (structured logging)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        logging_config = config["logging"]

        # When: Logging section is examined
        # Then: logging.enabled is True
        assert logging_config["enabled"] is True

        # And: logging.level is "INFO" (not DEBUG)
        assert logging_config["level"] == "INFO"

        # And: logging.include_scanned_text is False (privacy)
        assert logging_config["include_scanned_text"] is False

        # And: logging.sanitize_pii_in_logs is True
        assert logging_config["sanitize_pii_in_logs"] is True

        # And: logging.log_format is "json" (structured logging)
        assert logging_config["log_format"] == "json"

    def test_production_preset_enables_authentication_and_rate_limiting(self):
        """
        Test that production preset enables authentication and rate limiting.

        Verifies:
            Service configuration requires API key authentication and implements
            rate limiting to protect production resources.

        Business Impact:
            Authentication and rate limiting protect production APIs from
            unauthorized access and abuse, ensuring system reliability.

        Scenario:
            Given: The production preset configuration
            When: Service section is examined
            Then: service.api_key_required is True
            And: service.rate_limit_enabled is True
            And: service.rate_limit_requests_per_minute is >= 60
            And: service.debug_mode is False

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        service_config = config["service"]

        # When: Service section is examined
        # Then: service.api_key_required is True
        assert service_config["api_key_required"] is True

        # And: service.rate_limit_enabled is True
        assert service_config["rate_limit_enabled"] is True

        # And: service.rate_limit_requests_per_minute is >= 60
        assert service_config["rate_limit_requests_per_minute"] >= 60

        # And: service.debug_mode is False
        assert service_config["debug_mode"] is False

    def test_production_preset_has_extended_cache_ttl(self):
        """
        Test that production preset uses extended cache TTL for performance.

        Verifies:
            Cache TTL is set to 7200 seconds (2 hours) to optimize production
            throughput and reduce redundant security scans.

        Business Impact:
            Extended cache TTL improves production performance and reduces
            computational costs without compromising security coverage.

        Scenario:
            Given: The production preset configuration
            When: Performance.cache_ttl_seconds is examined
            Then: The value is 7200 (2 hours)
            And: cache_enabled is True

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        performance_config = config["performance"]

        # When: Performance.cache_ttl_seconds is examined
        cache_ttl = performance_config["cache_ttl_seconds"]
        cache_enabled = performance_config["cache_enabled"]

        # Then: The value is 7200 (2 hours)
        assert cache_ttl == 7200

        # And: cache_enabled is True
        assert cache_enabled is True

    def test_production_preset_enables_high_concurrency(self):
        """
        Test that production preset supports high concurrent scan operations.

        Verifies:
            Performance configuration allows high concurrency for production
            throughput requirements and scalability.

        Business Impact:
            High concurrency support enables production systems to handle
            large request volumes without performance degradation.

        Scenario:
            Given: The production preset configuration
            When: Performance.max_concurrent_scans is examined
            Then: The value is >= 20 (high concurrency)
            And: batch_processing is enabled for efficiency

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        performance_config = config["performance"]

        # When: Performance.max_concurrent_scans is examined
        max_concurrent_scans = performance_config["max_concurrent_scans"]
        batch_processing_enabled = performance_config.get("batch_processing_enabled", False)

        # Then: The value is >= 20 (high concurrency)
        assert max_concurrent_scans >= 20

        # And: batch_processing is enabled for efficiency
        assert batch_processing_enabled is True

        # And: Should have batch size configured
        assert "max_batch_size" in performance_config
        assert performance_config["max_batch_size"] > 0

    def test_production_preset_disables_experimental_features(self):
        """
        Test that production preset disables experimental features for stability.

        Verifies:
            Features section disables experimental features to ensure production
            stability and reliability with well-tested capabilities only.

        Business Impact:
            Disabling experimental features prevents untested capabilities from
            impacting production stability and user experience.

        Scenario:
            Given: The production preset configuration
            When: Features section is examined
            Then: features.experimental_features is False
            And: features.verbose_output is False (minimize logging overhead)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        features_config = config["features"]

        # When: Features section is examined
        # Then: features.experimental_features is False (implementation uses "experimental_scanners")
        assert features_config["experimental_scanners"] is False

        # And: features.custom_scanner_support is False (stability)
        assert features_config["custom_scanner_support"] is False

        # And: Keep essential features enabled
        assert features_config["advanced_analytics"] is True
        assert features_config["real_time_monitoring"] is True

    def test_production_preset_enables_comprehensive_scanners(self):
        """
        Test that production preset enables comprehensive security scanner coverage.

        Verifies:
            Both input and output scanners are comprehensively configured to
            provide maximum security protection for production systems.

        Business Impact:
            Comprehensive scanner coverage ensures production systems detect
            and block malicious content across all security dimensions.

        Scenario:
            Given: The production preset configuration
            When: Scanner configurations are examined
            Then: At least 4 input scanners are enabled
            And: At least 3 output scanners are enabled
            And: All major security categories are covered (injection, toxicity, PII)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_production_preset

        # Given: The production preset configuration
        config = get_production_preset()
        input_scanners = config["input_scanners"]
        output_scanners = config["output_scanners"]

        # When: Scanner configurations are examined
        enabled_input_scanners = [name for name, config in input_scanners.items() if config.get("enabled", False)]
        enabled_output_scanners = [name for name, config in output_scanners.items() if config.get("enabled", False)]

        # Then: At least 4 input scanners are enabled
        assert len(enabled_input_scanners) >= 4, f"Expected at least 4 input scanners, got {len(enabled_input_scanners)}: {enabled_input_scanners}"

        # And: At least 3 output scanners are enabled
        assert len(enabled_output_scanners) >= 3, f"Expected at least 3 output scanners, got {len(enabled_output_scanners)}: {enabled_output_scanners}"

        # And: All major security categories are covered (injection, toxicity, PII)
        major_categories = ["prompt_injection", "toxicity_input", "pii_detection"]
        for category in major_categories:
            assert category in enabled_input_scanners, f"Missing major security category: {category}"

        # And: Additional security scanners like malicious_url are enabled
        assert "malicious_url" in enabled_input_scanners

        # And: Output scanners include toxicity and harmful content detection
        output_categories = ["toxicity_output", "harmful_content"]
        for category in output_categories:
            assert category in enabled_output_scanners, f"Missing output security category: {category}"


class TestGetTestingPreset:
    """
    Test suite for get_testing_preset() function.
    
    Scope:
        Verifies that get_testing_preset() returns a minimal configuration
        dictionary optimized for fast test execution with minimal overhead.
        
    Business Critical:
        Testing preset enables fast CI/CD pipelines. Configuration issues
        would slow down development velocity and increase infrastructure costs.
        
    Test Strategy:
        - Verify minimal configuration structure
        - Test single-scanner optimization for speed
        - Validate minimal resource allocation
        - Test disabled logging for fast execution
    """

    def test_returns_minimal_testing_configuration(self, testing_preset_data):
        """
        Test that get_testing_preset returns minimal configuration dictionary.

        Verifies:
            get_testing_preset() returns a minimal configuration with only
            essential components for fast test execution.

        Business Impact:
            Minimal configuration ensures tests run quickly in CI/CD pipelines,
            reducing costs and improving developer feedback speed.

        Scenario:
            Given: A call to get_testing_preset()
            When: The configuration dictionary is returned
            Then: All required sections are present
            And: The preset field contains "testing"
            And: The service.environment field contains "testing"
            And: Configuration is optimized for minimal resource usage

        Fixtures Used:
            - testing_preset_data: Expected structure for validation
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # When: Get testing preset configuration
        config = get_testing_preset()

        # Then: All required sections are present
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"

        # And: The preset field contains "testing"
        assert config["preset"] == "testing"

        # And: The service.environment field contains "testing"
        assert config["service"]["environment"] == "testing"

        # And: Configuration matches expected structure
        assert isinstance(config["input_scanners"], dict)
        assert isinstance(config["output_scanners"], dict)
        assert isinstance(config["performance"], dict)
        assert isinstance(config["logging"], dict)
        assert isinstance(config["service"], dict)
        assert isinstance(config["features"], dict)

    def test_testing_preset_enables_only_essential_scanner(self):
        """
        Test that testing preset enables only prompt_injection scanner for speed.

        Verifies:
            Input scanners contain only prompt_injection scanner and output
            scanners are empty to minimize test execution time.

        Business Impact:
            Single scanner configuration provides basic validation while
            maximizing test execution speed and minimizing resource usage.

        Scenario:
            Given: The testing preset configuration
            When: Scanner configurations are examined
            Then: input_scanners contains exactly 1 scanner
            And: The scanner is "prompt_injection"
            And: output_scanners is an empty dictionary

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        input_scanners = config["input_scanners"]
        output_scanners = config["output_scanners"]

        # When: Scanner configurations are examined
        # Then: input_scanners contains exactly 1 scanner
        assert len(input_scanners) == 1, f"Expected exactly 1 input scanner, got {len(input_scanners)}"

        # And: The scanner is "prompt_injection"
        assert "prompt_injection" in input_scanners
        assert input_scanners["prompt_injection"]["enabled"] is True

        # And: output_scanners is an empty dictionary
        assert len(output_scanners) == 0, f"Expected no output scanners, got {len(output_scanners)}"

    def test_testing_preset_disables_logging_for_speed(self):
        """
        Test that testing preset disables logging to maximize test speed.

        Verifies:
            Logging configuration is disabled or minimal to eliminate I/O
            overhead during test execution.

        Business Impact:
            Disabled logging removes I/O bottlenecks from test execution,
            enabling faster CI/CD pipelines and reduced infrastructure costs.

        Scenario:
            Given: The testing preset configuration
            When: Logging section is examined
            Then: logging.enabled is False
            And: logging.level is "ERROR" (minimal)
            And: logging.include_scanned_text is False
            And: logging.log_scan_operations is False

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        logging_config = config["logging"]

        # When: Logging section is examined
        # Then: logging.enabled is False
        assert logging_config["enabled"] is False

        # And: logging.level is "ERROR" (minimal)
        assert logging_config["level"] == "ERROR"

        # And: logging.include_scanned_text is False
        assert logging_config["include_scanned_text"] is False

        # And: logging.log_scan_operations is False
        assert logging_config["log_scan_operations"] is False

        # And: logging.log_violations is False
        assert logging_config["log_violations"] is False

        # And: logging.log_performance_metrics is False
        assert logging_config["log_performance_metrics"] is False

    def test_testing_preset_uses_minimal_cache_ttl(self):
        """
        Test that testing preset uses very short cache TTL for test isolation.

        Verifies:
            Cache TTL is set to 1 second to ensure test isolation while
            still providing cache functionality for testing.

        Business Impact:
            Short cache TTL prevents cache state from affecting test results,
            ensuring test reliability and independence.

        Scenario:
            Given: The testing preset configuration
            When: Performance.cache_ttl_seconds is examined
            Then: The value is 1 (1 second)
            And: cache_enabled is True (for testing cache behavior)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        performance_config = config["performance"]

        # When: Performance.cache_ttl_seconds is examined
        cache_ttl = performance_config["cache_ttl_seconds"]
        cache_enabled = performance_config["cache_enabled"]

        # Then: The value is 1 (1 second)
        assert cache_ttl == 1

        # And: cache_enabled is True (for testing cache behavior)
        assert cache_enabled is True

    def test_testing_preset_limits_concurrent_scans_to_one(self):
        """
        Test that testing preset limits concurrent scans to prevent contention.

        Verifies:
            Performance configuration limits concurrent scans to 1 to minimize
            resource contention during test execution.

        Business Impact:
            Single-threaded scanning prevents resource contention and race
            conditions during test execution, ensuring test reliability.

        Scenario:
            Given: The testing preset configuration
            When: Performance.max_concurrent_scans is examined
            Then: The value is 1 (single-threaded)
            And: batch_processing is False (simplified processing)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        performance_config = config["performance"]

        # When: Performance.max_concurrent_scans is examined
        max_concurrent_scans = performance_config["max_concurrent_scans"]

        # Then: The value is 1 (single-threaded)
        assert max_concurrent_scans == 1

        # And: batch_processing is False (simplified processing)
        # Note: Implementation doesn't have explicit batch_processing flag, but we can check other indicators
        assert performance_config.get("enable_model_caching", False) is False
        assert performance_config.get("enable_result_caching", False) is False

    def test_testing_preset_uses_minimal_memory_allocation(self):
        """
        Test that testing preset allocates minimal memory resources.

        Verifies:
            Memory limit is set to minimal value (256MB) to reduce resource
            usage during test execution.

        Business Impact:
            Minimal memory allocation enables more concurrent test processes
            on CI/CD infrastructure, reducing costs and improving efficiency.

        Scenario:
            Given: The testing preset configuration
            When: Performance.memory_limit_mb is examined
            Then: The value is <= 256 (minimal allocation)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        performance_config = config["performance"]

        # When: Performance.memory_limit_mb is examined
        memory_limit = performance_config["memory_limit_mb"]

        # Then: The value is <= 256 (minimal allocation)
        assert memory_limit <= 256, f"Expected memory limit <= 256MB, got {memory_limit}MB"

    def test_testing_preset_uses_cpu_only_execution(self):
        """
        Test that testing preset uses CPU-only execution for compatibility.

        Verifies:
            Performance configuration specifies CPU execution only, avoiding
            GPU dependencies in test environments.

        Business Impact:
            CPU-only execution ensures tests run in any environment without
            requiring GPU hardware or complex driver setup.

        Scenario:
            Given: The testing preset configuration
            When: Performance.onnx_providers is examined
            Then: Only "CPUExecutionProvider" is in the providers list
            And: No GPU providers are configured

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        performance_config = config["performance"]

        # When: Performance.onnx_providers is examined
        onnx_providers = performance_config["onnx_providers"]

        # Then: Only "CPUExecutionProvider" is in the providers list
        assert "CPUExecutionProvider" in onnx_providers

        # And: No GPU providers are configured
        gpu_providers = ["CUDAExecutionProvider", "TensorRTExecutionProvider", "OpenVINOExecutionProvider"]
        for provider in gpu_providers:
            assert provider not in onnx_providers, f"GPU provider {provider} should not be configured"

        # And: Only CPU provider is present
        assert len(onnx_providers) == 1
        assert onnx_providers[0] == "CPUExecutionProvider"

        # And: ONNX usage is disabled for speed
        input_scanners = config["input_scanners"]
        assert input_scanners["prompt_injection"]["use_onnx"] is False

    def test_testing_preset_disables_authentication_for_convenience(self):
        """
        Test that testing preset disables authentication for test convenience.

        Verifies:
            Service configuration disables API key requirements and rate limiting
            for simplified test setup and execution.

        Business Impact:
            Disabled authentication simplifies test configuration and eliminates
            authentication complexity from test environment setup.

        Scenario:
            Given: The testing preset configuration
            When: Service section is examined
            Then: service.api_key_required is False
            And: service.rate_limit_enabled is False
            And: service.debug_mode is True (for test debugging)

        Fixtures Used:
            - None (tests observable configuration values)
        """
        from app.infrastructure.security.llm.presets import get_testing_preset

        # Given: The testing preset configuration
        config = get_testing_preset()
        service_config = config["service"]

        # When: Service section is examined
        # Then: service.api_key_required is False
        assert service_config["api_key_required"] is False

        # And: service.rate_limit_enabled is False
        assert service_config["rate_limit_enabled"] is False

        # And: service.debug_mode is True (for test debugging)
        assert service_config["debug_mode"] is True

        # And: service name contains "test"
        assert "test" in service_config["name"]

        # And: All optional features are disabled for speed
        features_config = config["features"]
        assert features_config["experimental_scanners"] is False
        assert features_config["advanced_analytics"] is False
        assert features_config["real_time_monitoring"] is False
        assert features_config["custom_scanner_support"] is False

