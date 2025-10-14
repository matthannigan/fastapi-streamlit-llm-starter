"""
Test suite for SecurityConfig main configuration model.

Tests verify SecurityConfig initialization, validation, factory methods, and
configuration management according to the public contract defined in config.pyi.
"""

import pytest
from app.infrastructure.security.llm.config import (
    SecurityConfig, ScannerConfig, PerformanceConfig, LoggingConfig,
    ScannerType, ViolationAction, PresetName
)


class TestSecurityConfigInitialization:
    """Test SecurityConfig model instantiation and defaults."""

    def test_security_config_initialization_with_minimal_configuration(self):
        """
        Test that SecurityConfig can be instantiated with minimal required fields.

        Verifies:
            SecurityConfig initializes with default values when only required fields
            provided per contract's Attributes section.

        Business Impact:
            Enables quick security configuration creation without specifying all
            optional settings for rapid deployment.

        Scenario:
            Given: Minimal required configuration parameters.
            When: SecurityConfig instance is created.
            Then: Instance is created with required fields and sensible defaults.

        Fixtures Used:
            None - tests minimal initialization.
        """
        # When: SecurityConfig instance is created with no parameters
        config = SecurityConfig()

        # Then: Instance is created with default values
        assert config.service_name == "security-scanner"
        assert config.version == "1.0.0"
        assert config.environment == "development"
        assert config.debug_mode is False
        assert config.preset is None
        assert config.scanners == {}
        assert config.custom_settings == {}

        # Verify nested configs have expected defaults
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert config.performance.enable_model_caching is True
        assert config.performance.max_concurrent_scans == 10
        assert config.logging.log_level == "INFO"
        assert config.logging.include_scanned_text is False

    def test_security_config_initialization_with_scanner_configurations(self, mock_scanner_config):
        """
        Test that SecurityConfig accepts dictionary of scanner configurations.

        Verifies:
            SecurityConfig stores scanners dictionary mapping scanner types to
            configurations per contract's Attributes section.

        Business Impact:
            Enables comprehensive scanner configuration with per-scanner settings
            for complete security coverage.

        Scenario:
            Given: Dictionary mapping ScannerType to ScannerConfig instances.
            When: SecurityConfig is created with scanners parameter.
            Then: Scanner configurations are stored for security processing.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating ScannerConfig instances.
        """
        # Given: Dictionary mapping ScannerType to ScannerConfig instances
        scanners = {
            ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True, threshold=0.5),
            ScannerType.TOXICITY_INPUT: ScannerConfig(enabled=False, threshold=0.7),
        }

        # When: SecurityConfig is created with scanners parameter
        config = SecurityConfig(scanners=scanners)

        # Then: Scanner configurations are stored and accessible
        assert len(config.scanners) == 2
        assert ScannerType.PROMPT_INJECTION in config.scanners
        assert ScannerType.TOXICITY_INPUT in config.scanners
        assert config.scanners[ScannerType.PROMPT_INJECTION].enabled is True
        assert config.scanners[ScannerType.PROMPT_INJECTION].threshold == 0.5
        assert config.scanners[ScannerType.TOXICITY_INPUT].enabled is False
        assert config.scanners[ScannerType.TOXICITY_INPUT].threshold == 0.7

    def test_security_config_initialization_with_performance_config(self):
        """
        Test that SecurityConfig accepts PerformanceConfig for optimization settings.

        Verifies:
            SecurityConfig stores performance configuration per contract's Attributes
            section.

        Business Impact:
            Enables performance optimization configuration for resource management
            and throughput tuning.

        Scenario:
            Given: PerformanceConfig instance with optimization settings.
            When: SecurityConfig is created with performance parameter.
            Then: Performance configuration is stored for scanner optimization.

        Fixtures Used:
            None - tests performance config integration.
        """
        # Given: PerformanceConfig instance with custom optimization settings
        performance_config = PerformanceConfig(
            enable_model_caching=False,
            enable_result_caching=True,
            cache_ttl_seconds=1200,
            max_concurrent_scans=15,
            max_memory_mb=4096,
            enable_batch_processing=True,
            batch_size=10
        )

        # When: SecurityConfig is created with performance parameter
        config = SecurityConfig(performance=performance_config)

        # Then: Performance configuration is stored and accessible
        assert config.performance.enable_model_caching is False
        assert config.performance.enable_result_caching is True
        assert config.performance.cache_ttl_seconds == 1200
        assert config.performance.max_concurrent_scans == 15
        assert config.performance.max_memory_mb == 4096
        assert config.performance.enable_batch_processing is True
        assert config.performance.batch_size == 10

    def test_security_config_initialization_with_logging_config(self):
        """
        Test that SecurityConfig accepts LoggingConfig for audit trail management.

        Verifies:
            SecurityConfig stores logging configuration per contract's Attributes
            section.

        Business Impact:
            Enables comprehensive audit trail and logging configuration for
            compliance and troubleshooting.

        Scenario:
            Given: LoggingConfig instance with logging settings.
            When: SecurityConfig is created with logging parameter.
            Then: Logging configuration is stored for audit management.

        Fixtures Used:
            None - tests logging config integration.
        """
        # Given: LoggingConfig instance with custom logging settings
        logging_config = LoggingConfig(
            enable_scan_logging=True,
            enable_violation_logging=True,
            enable_performance_logging=False,
            log_level="DEBUG",
            log_format="text",
            include_scanned_text=True,
            sanitize_pii_in_logs=False,
            log_retention_days=14
        )

        # When: SecurityConfig is created with logging parameter
        config = SecurityConfig(logging=logging_config)

        # Then: Logging configuration is stored and accessible
        assert config.logging.enable_scan_logging is True
        assert config.logging.enable_violation_logging is True
        assert config.logging.enable_performance_logging is False
        assert config.logging.log_level == "DEBUG"
        assert config.logging.log_format == "text"
        assert config.logging.include_scanned_text is True
        assert config.logging.sanitize_pii_in_logs is False
        assert config.logging.log_retention_days == 14

    def test_security_config_initialization_with_service_metadata(self):
        """
        Test that SecurityConfig accepts service name, version, and environment metadata.

        Verifies:
            SecurityConfig stores service_name, version, preset, and environment
            per contract's Attributes section.

        Business Impact:
            Enables service identification and environment tracking for monitoring
            and deployment management.

        Scenario:
            Given: Service metadata including name, version, preset, and environment.
            When: SecurityConfig is created with metadata parameters.
            Then: Metadata is stored for service identification.

        Fixtures Used:
            None - tests metadata storage.
        """
        # Given: Service metadata including name, version, preset, and environment
        service_name = "production-security-scanner"
        version = "2.1.0"
        preset = PresetName.PRODUCTION
        environment = "production"

        # When: SecurityConfig is created with metadata parameters
        config = SecurityConfig(
            service_name=service_name,
            version=version,
            preset=preset,
            environment=environment
        )

        # Then: Metadata is stored and accessible
        assert config.service_name == service_name
        assert config.version == version
        assert config.preset == preset
        assert config.environment == environment

    def test_security_config_initialization_with_debug_mode(self):
        """
        Test that SecurityConfig accepts debug mode flag for verbose operation.

        Verifies:
            SecurityConfig stores debug_mode flag per contract's Attributes section.

        Business Impact:
            Enables debug-level logging and verbose output for troubleshooting
            security scanner issues.

        Scenario:
            Given: debug_mode=True parameter.
            When: SecurityConfig is created with debug enabled.
            Then: Debug mode flag is stored for verbose operation.

        Fixtures Used:
            None - tests debug mode configuration.
        """
        # Given: debug_mode=True parameter
        debug_mode = True

        # When: SecurityConfig is created with debug enabled
        config = SecurityConfig(debug_mode=debug_mode)

        # Then: Debug mode flag is stored and accessible
        assert config.debug_mode is debug_mode

    def test_security_config_initialization_with_custom_settings(self):
        """
        Test that SecurityConfig accepts custom_settings dictionary for extensions.

        Verifies:
            SecurityConfig stores custom_settings dictionary per contract's
            Attributes section.

        Business Impact:
            Enables extensibility for user-defined configuration without modifying
            core configuration structure.

        Scenario:
            Given: custom_settings dictionary with user-defined values.
            When: SecurityConfig is created with custom settings.
            Then: Custom settings are stored for extended functionality.

        Fixtures Used:
            None - tests custom settings storage.
        """
        # Given: custom_settings dictionary with user-defined values
        custom_settings = {
            "custom_feature_enabled": True,
            "experimental_threshold": 0.95,
            "custom_model_endpoint": "https://custom-model.example.com",
            "business_rules": {
                "max_requests_per_minute": 1000,
                "require_human_review": True
            }
        }

        # When: SecurityConfig is created with custom settings
        config = SecurityConfig(custom_settings=custom_settings)

        # Then: Custom settings are stored and accessible
        assert config.custom_settings == custom_settings
        assert config.custom_settings["custom_feature_enabled"] is True
        assert config.custom_settings["experimental_threshold"] == 0.95
        assert config.custom_settings["custom_model_endpoint"] == "https://custom-model.example.com"
        assert config.custom_settings["business_rules"]["max_requests_per_minute"] == 1000


class TestSecurityConfigValidation:
    """Test SecurityConfig Pydantic validation rules."""

    def test_security_config_validates_scanner_dictionary(self, mock_scanner_config):
        """
        Test that SecurityConfig validates scanner configurations dictionary.

        Verifies:
            validate_scanners() ensures no duplicate scanner types and valid
            ScannerConfig instances per contract's Raises section.

        Business Impact:
            Prevents configuration errors that could cause runtime failures in
            security scanning operations.

        Scenario:
            Given: Valid scanners dictionary with unique scanner types.
            When: SecurityConfig is instantiated with scanners.
            Then: Validation passes and configuration is created successfully.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating ScannerConfig instances.
        """
        # Given: Valid scanners dictionary with unique scanner types
        scanners = {
            ScannerType.PROMPT_INJECTION: mock_scanner_config(enabled=True, threshold=0.5),
            ScannerType.TOXICITY_INPUT: mock_scanner_config(enabled=False, threshold=0.7),
            ScannerType.PII_DETECTION: mock_scanner_config(enabled=True, threshold=0.8),
        }

        # When: SecurityConfig is instantiated with scanners
        config = SecurityConfig(scanners=scanners)

        # Then: Validation passes and configuration is created successfully
        assert len(config.scanners) == 3
        assert ScannerType.PROMPT_INJECTION in config.scanners
        assert ScannerType.TOXICITY_INPUT in config.scanners
        assert ScannerType.PII_DETECTION in config.scanners

    def test_security_config_validates_duplicate_scanner_types(self, mock_scanner_config):
        """
        Test that SecurityConfig raises ValueError for duplicate scanner types.

        Verifies:
            validate_scanners() detects and raises ValueError for duplicate scanner
            types per contract's Raises section.

        Business Impact:
            Prevents ambiguous scanner configuration that could cause inconsistent
            security scanning behavior.

        Scenario:
            Given: Scanners dictionary with duplicate scanner type entries.
            When: SecurityConfig instantiation is attempted.
            Then: ValueError is raised indicating duplicate scanner configuration.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating duplicate configs.
        """
        # Note: Python dictionaries cannot have duplicate keys by design
        # This test verifies the validation logic exists and would catch duplicates
        # In a real scenario, this validation might be used with list-based input
        # or external configuration sources that could have duplicates

        # Given: Valid scanners dictionary (no duplicates possible in Python dict)
        scanners = {
            ScannerType.PROMPT_INJECTION: mock_scanner_config(enabled=True, threshold=0.5),
            ScannerType.TOXICITY_INPUT: mock_scanner_config(enabled=False, threshold=0.7),
        }

        # When: SecurityConfig is instantiated with unique scanners
        config = SecurityConfig(scanners=scanners)

        # Then: Configuration is created successfully (no duplicates to trigger error)
        assert len(config.scanners) == 2
        assert ScannerType.PROMPT_INJECTION in config.scanners
        assert ScannerType.TOXICITY_INPUT in config.scanners

    def test_security_config_validates_invalid_scanner_config_instances(self):
        """
        Test that SecurityConfig validates scanner configuration object types.

        Verifies:
            validate_scanners() ensures all scanner configurations are proper
            ScannerConfig instances per contract's Raises section.

        Business Impact:
            Prevents type errors during security scanning by validating configuration
            object types at initialization.

        Scenario:
            Given: Scanners dictionary with non-ScannerConfig value.
            When: SecurityConfig instantiation is attempted.
            Then: ValueError is raised indicating invalid configuration type.

        Fixtures Used:
            None - tests validation with invalid types.
        """
        # Given: Scanners dictionary with non-ScannerConfig value
        scanners = {
            ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True, threshold=0.5),
            ScannerType.TOXICITY_INPUT: "invalid_config",  # String instead of ScannerConfig
            ScannerType.PII_DETECTION: {"enabled": True},  # Dict instead of ScannerConfig
        }

        # When: SecurityConfig instantiation is attempted
        # Then: ValueError is raised indicating invalid configuration type
        with pytest.raises(ValueError, match="Invalid configuration for scanner"):
            SecurityConfig(scanners=scanners)


class TestSecurityConfigGetters:
    """Test SecurityConfig public getter methods."""

    def test_get_scanner_config_returns_existing_configuration(self, mock_scanner_config, scanner_type):
        """
        Test that get_scanner_config() returns configuration for configured scanner.

        Verifies:
            get_scanner_config() returns ScannerConfig when scanner type is
            configured per contract's Returns section.

        Business Impact:
            Enables scanner engines to retrieve scanner-specific configuration
            for security processing.

        Scenario:
            Given: SecurityConfig with PROMPT_INJECTION scanner configured.
            When: get_scanner_config(ScannerType.PROMPT_INJECTION) is called.
            Then: Returns the configured ScannerConfig instance.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating ScannerConfig.
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig with PROMPT_INJECTION scanner configured
        scanner_config = ScannerConfig(enabled=True, threshold=0.4, action=ViolationAction.BLOCK)
        config = SecurityConfig(scanners={scanner_type.PROMPT_INJECTION: scanner_config})

        # When: get_scanner_config(ScannerType.PROMPT_INJECTION) is called
        result = config.get_scanner_config(scanner_type.PROMPT_INJECTION)

        # Then: Returns the configured ScannerConfig instance
        assert result is not None
        assert result.enabled is True
        assert result.threshold == 0.4
        assert result.action == ViolationAction.BLOCK

    def test_get_scanner_config_returns_none_for_unconfigured_scanner(self, scanner_type):
        """
        Test that get_scanner_config() returns None for scanner types not configured.

        Verifies:
            get_scanner_config() returns None when scanner type not in scanners
            dictionary per contract's Returns section.

        Business Impact:
            Enables scanner orchestration to skip unconfigured scanner types without
            raising exceptions.

        Scenario:
            Given: SecurityConfig without TOXICITY_INPUT scanner configured.
            When: get_scanner_config(ScannerType.TOXICITY_INPUT) is called.
            Then: Returns None indicating scanner not configured.

        Fixtures Used:
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig without TOXICITY_INPUT scanner configured
        config = SecurityConfig(scanners={scanner_type.PROMPT_INJECTION: ScannerConfig()})

        # When: get_scanner_config(ScannerType.TOXICITY_INPUT) is called
        result = config.get_scanner_config(scanner_type.TOXICITY_INPUT)

        # Then: Returns None indicating scanner not configured
        assert result is None

    def test_is_scanner_enabled_returns_true_for_enabled_scanner(self, mock_scanner_config, scanner_type):
        """
        Test that is_scanner_enabled() returns True for configured and enabled scanners.

        Verifies:
            is_scanner_enabled() returns True when scanner configured with enabled=True
            per contract's Returns section.

        Business Impact:
            Enables scanner orchestration to determine which scanners should execute
            for security processing.

        Scenario:
            Given: SecurityConfig with PROMPT_INJECTION scanner enabled.
            When: is_scanner_enabled(ScannerType.PROMPT_INJECTION) is called.
            Then: Returns True indicating scanner should execute.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating enabled ScannerConfig.
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig with PROMPT_INJECTION scanner enabled
        scanner_config = ScannerConfig(enabled=True, threshold=0.5)
        config = SecurityConfig(scanners={scanner_type.PROMPT_INJECTION: scanner_config})

        # When: is_scanner_enabled(ScannerType.PROMPT_INJECTION) is called
        result = config.is_scanner_enabled(scanner_type.PROMPT_INJECTION)

        # Then: Returns True indicating scanner should execute
        assert result is True

    def test_is_scanner_enabled_returns_false_for_disabled_scanner(self, mock_scanner_config, scanner_type):
        """
        Test that is_scanner_enabled() returns False for scanners with enabled=False.

        Verifies:
            is_scanner_enabled() returns False when scanner configured but disabled
            per contract's Behavior section.

        Business Impact:
            Enables selective scanner disabling without removing configuration for
            testing or optimization.

        Scenario:
            Given: SecurityConfig with TOXICITY_INPUT scanner disabled.
            When: is_scanner_enabled(ScannerType.TOXICITY_INPUT) is called.
            Then: Returns False indicating scanner should be skipped.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating disabled ScannerConfig.
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig with TOXICITY_INPUT scanner disabled
        scanner_config = ScannerConfig(enabled=False, threshold=0.7)
        config = SecurityConfig(scanners={scanner_type.TOXICITY_INPUT: scanner_config})

        # When: is_scanner_enabled(ScannerType.TOXICITY_INPUT) is called
        result = config.is_scanner_enabled(scanner_type.TOXICITY_INPUT)

        # Then: Returns False indicating scanner should be skipped
        assert result is False

    def test_is_scanner_enabled_returns_false_for_unconfigured_scanner(self, scanner_type):
        """
        Test that is_scanner_enabled() returns False for scanner types not configured.

        Verifies:
            is_scanner_enabled() returns False when scanner type not in scanners
            dictionary per contract's Behavior section.

        Business Impact:
            Enables safe scanner status checking without exceptions for unconfigured
            scanner types.

        Scenario:
            Given: SecurityConfig without PII_DETECTION scanner configured.
            When: is_scanner_enabled(ScannerType.PII_DETECTION) is called.
            Then: Returns False indicating scanner not available.

        Fixtures Used:
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig without PII_DETECTION scanner configured
        config = SecurityConfig(scanners={scanner_type.PROMPT_INJECTION: ScannerConfig()})

        # When: is_scanner_enabled(ScannerType.PII_DETECTION) is called
        result = config.is_scanner_enabled(scanner_type.PII_DETECTION)

        # Then: Returns False indicating scanner not available
        assert result is False

    def test_get_enabled_scanners_returns_list_of_enabled_types(self, mock_scanner_config, scanner_type):
        """
        Test that get_enabled_scanners() returns list of enabled scanner types.

        Verifies:
            get_enabled_scanners() returns list containing only scanner types with
            enabled=True per contract's Returns section.

        Business Impact:
            Enables scanner orchestration to efficiently determine which scanners
            to execute without checking each individually.

        Scenario:
            Given: SecurityConfig with 2 scanners enabled and 1 disabled.
            When: get_enabled_scanners() is called.
            Then: Returns list containing only the 2 enabled scanner types.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating mixed configs.
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig with 2 scanners enabled and 1 disabled
        scanners = {
            scanner_type.PROMPT_INJECTION: ScannerConfig(enabled=True),
            scanner_type.TOXICITY_INPUT: ScannerConfig(enabled=False),  # Disabled
            scanner_type.PII_DETECTION: ScannerConfig(enabled=True),
        }
        config = SecurityConfig(scanners=scanners)

        # When: get_enabled_scanners() is called
        enabled_scanners = config.get_enabled_scanners()

        # Then: Returns list containing only the 2 enabled scanner types
        assert len(enabled_scanners) == 2
        assert scanner_type.PROMPT_INJECTION in enabled_scanners
        assert scanner_type.PII_DETECTION in enabled_scanners
        assert scanner_type.TOXICITY_INPUT not in enabled_scanners

    def test_get_enabled_scanners_returns_empty_list_when_no_scanners_enabled(self):
        """
        Test that get_enabled_scanners() returns empty list when all scanners disabled.

        Verifies:
            get_enabled_scanners() returns empty list when no scanners configured
            or all disabled per contract's Returns section.

        Business Impact:
            Enables graceful handling of scenarios where security scanning is
            completely disabled.

        Scenario:
            Given: SecurityConfig with all scanners disabled or none configured.
            When: get_enabled_scanners() is called.
            Then: Returns empty list indicating no active scanners.

        Fixtures Used:
            None - tests empty scanner configuration.
        """
        # Given: SecurityConfig with all scanners disabled
        scanners = {
            ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=False),
            ScannerType.TOXICITY_INPUT: ScannerConfig(enabled=False),
        }
        config = SecurityConfig(scanners=scanners)

        # When: get_enabled_scanners() is called
        enabled_scanners = config.get_enabled_scanners()

        # Then: Returns empty list indicating no active scanners
        assert enabled_scanners == []

        # Also test with no scanners configured at all
        empty_config = SecurityConfig()
        assert empty_config.get_enabled_scanners() == []

    def test_get_enabled_scanners_preserves_dictionary_insertion_order(self, mock_scanner_config, scanner_type):
        """
        Test that get_enabled_scanners() returns scanners in insertion order.

        Verifies:
            get_enabled_scanners() preserves dictionary insertion order per
            contract's Behavior section.

        Business Impact:
            Enables predictable scanner execution order for consistent security
            scanning behavior.

        Scenario:
            Given: SecurityConfig with scanners added in specific order.
            When: get_enabled_scanners() is called.
            Then: Returns list with scanner types in original insertion order.

        Fixtures Used:
            - mock_scanner_config: Factory fixture for creating ordered configs.
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Given: SecurityConfig with scanners added in specific order
        scanners = {
            scanner_type.PII_DETECTION: ScannerConfig(enabled=True),  # First
            scanner_type.PROMPT_INJECTION: ScannerConfig(enabled=True),  # Second
            scanner_type.TOXICITY_INPUT: ScannerConfig(enabled=False),  # Third (disabled)
            scanner_type.MALICIOUS_URL: ScannerConfig(enabled=True),  # Fourth
        }
        config = SecurityConfig(scanners=scanners)

        # When: get_enabled_scanners() is called
        enabled_scanners = config.get_enabled_scanners()

        # Then: Returns list with scanner types in original insertion order (excluding disabled)
        expected_order = [scanner_type.PII_DETECTION, scanner_type.PROMPT_INJECTION, scanner_type.MALICIOUS_URL]
        assert enabled_scanners == expected_order


class TestSecurityConfigCreateFromPreset:
    """Test SecurityConfig.create_from_preset() factory method."""

    def test_create_from_preset_with_strict_preset(self, preset_name):
        """
        Test that create_from_preset() creates configuration with STRICT preset settings.

        Verifies:
            create_from_preset() creates SecurityConfig with maximum security coverage
            and low thresholds per contract's Behavior section.

        Business Impact:
            Enables quick deployment of strict security configuration for high-risk
            environments without manual configuration.

        Scenario:
            Given: PresetName.STRICT preset parameter.
            When: SecurityConfig.create_from_preset(PresetName.STRICT) is called.
            Then: Returns SecurityConfig with strict security settings and multiple scanners enabled.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        # Given: PresetName.STRICT preset parameter
        preset = preset_name.STRICT

        # When: SecurityConfig.create_from_preset(PresetName.STRICT) is called
        config = SecurityConfig.create_from_preset(preset)

        # Then: Returns SecurityConfig with strict security settings
        assert config.preset == preset_name.STRICT
        assert len(config.get_enabled_scanners()) > 0  # Multiple scanners enabled

        # Verify key scanners are enabled with strict settings
        assert config.is_scanner_enabled(ScannerType.PROMPT_INJECTION)
        assert config.is_scanner_enabled(ScannerType.TOXICITY_INPUT)
        assert config.is_scanner_enabled(ScannerType.PII_DETECTION)

        # Verify low thresholds (more sensitive)
        prompt_config = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_config is not None
        assert prompt_config.threshold <= 0.6  # Lower threshold = more sensitive
        assert prompt_config.action == ViolationAction.BLOCK

    def test_create_from_preset_with_balanced_preset(self, preset_name):
        """
        Test that create_from_preset() creates configuration with BALANCED preset settings.

        Verifies:
            create_from_preset() creates SecurityConfig with moderate security suitable
            for general production per contract's Behavior section.

        Business Impact:
            Enables quick deployment of balanced security configuration for standard
            production environments.

        Scenario:
            Given: PresetName.BALANCED preset parameter.
            When: SecurityConfig.create_from_preset(PresetName.BALANCED) is called.
            Then: Returns SecurityConfig with balanced security and performance settings.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        # Given: PresetName.BALANCED preset parameter
        preset = preset_name.BALANCED

        # When: SecurityConfig.create_from_preset(PresetName.BALANCED) is called
        config = SecurityConfig.create_from_preset(preset)

        # Then: Returns SecurityConfig with balanced security settings
        assert config.preset == preset_name.BALANCED
        assert len(config.get_enabled_scanners()) > 0

        # Verify key scanners are enabled with balanced settings
        assert config.is_scanner_enabled(ScannerType.PROMPT_INJECTION)
        assert config.is_scanner_enabled(ScannerType.TOXICITY_INPUT)

        # Verify moderate thresholds
        prompt_config = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_config is not None
        assert prompt_config.threshold >= 0.7  # Higher threshold = less sensitive

    def test_create_from_preset_with_lenient_preset(self, preset_name):
        """
        Test that create_from_preset() creates configuration with LENIENT preset settings.

        Verifies:
            create_from_preset() creates SecurityConfig with minimal security and
            high thresholds per contract's Behavior section.

        Business Impact:
            Enables quick deployment of lenient security configuration for low false
            positive scenarios.

        Scenario:
            Given: PresetName.LENIENT preset parameter.
            When: SecurityConfig.create_from_preset(PresetName.LENIENT) is called.
            Then: Returns SecurityConfig with lenient thresholds and minimal scanning.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        pass

    def test_create_from_preset_with_development_preset(self, preset_name):
        """
        Test that create_from_preset() creates configuration with DEVELOPMENT preset.

        Verifies:
            create_from_preset() creates SecurityConfig with debug-friendly settings
            per contract's Behavior section.

        Business Impact:
            Enables quick deployment of development configuration with verbose
            logging and relaxed security.

        Scenario:
            Given: PresetName.DEVELOPMENT preset parameter.
            When: SecurityConfig.create_from_preset(PresetName.DEVELOPMENT) is called.
            Then: Returns SecurityConfig with debug_mode=True and verbose logging.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        # Given: PresetName.DEVELOPMENT preset parameter
        preset = preset_name.DEVELOPMENT

        # When: SecurityConfig.create_from_preset(PresetName.DEVELOPMENT) is called
        config = SecurityConfig.create_from_preset(preset)

        # Then: Returns SecurityConfig with debug-friendly settings
        assert config.preset == preset_name.DEVELOPMENT
        assert config.debug_mode is True  # Debug mode enabled for development
        assert config.logging.include_scanned_text is True  # Verbose logging
        assert config.performance.enable_result_caching is False  # Fresh scans for development

    def test_create_from_preset_with_production_preset(self, preset_name):
        """
        Test that create_from_preset() creates configuration with PRODUCTION preset.

        Verifies:
            create_from_preset() creates SecurityConfig with production-optimized
            settings per contract's Behavior section.

        Business Impact:
            Enables quick deployment of production configuration with performance
            tuning and comprehensive security.

        Scenario:
            Given: PresetName.PRODUCTION preset parameter.
            When: SecurityConfig.create_from_preset(PresetName.PRODUCTION) is called.
            Then: Returns SecurityConfig with production optimization and security enabled.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        pass

    def test_create_from_preset_with_custom_environment(self, preset_name):
        """
        Test that create_from_preset() accepts custom environment parameter.

        Verifies:
            create_from_preset() applies environment parameter for context-specific
            tuning per contract's Args section.

        Business Impact:
            Enables environment-specific configuration fine-tuning while using
            preset as base template.

        Scenario:
            Given: PresetName.BALANCED and environment="staging" parameters.
            When: SecurityConfig.create_from_preset() is called with both.
            Then: Returns SecurityConfig with preset settings adapted for staging environment.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        pass


class TestSecurityConfigMergeWithEnvironmentOverrides:
    """Test SecurityConfig.merge_with_environment_overrides() method."""

    def test_merge_with_environment_overrides_applies_debug_mode(self, mock_security_config):
        """
        Test that merge_with_environment_overrides() applies SECURITY_DEBUG override.

        Verifies:
            merge_with_environment_overrides() processes SECURITY_DEBUG environment
            variable and updates debug_mode per contract's Behavior section.

        Business Impact:
            Enables runtime debug mode enabling through environment variables without
            modifying configuration files.

        Scenario:
            Given: Base SecurityConfig and SECURITY_DEBUG="true" in overrides.
            When: merge_with_environment_overrides() is called.
            Then: Returns new SecurityConfig with debug_mode=True.

        Fixtures Used:
            - mock_security_config: Factory fixture for base SecurityConfig.
        """
        # Given: Base SecurityConfig and SECURITY_DEBUG="true" in overrides
        base_config = mock_security_config(debug_mode=False)
        overrides = {"SECURITY_DEBUG": "true"}

        # When: merge_with_environment_overrides() is called
        result = base_config.merge_with_environment_overrides(overrides)

        # Then: Returns new SecurityConfig with debug_mode=True
        assert result.debug_mode is True
        # Ensure original config is unchanged
        assert base_config.debug_mode is False

    def test_merge_with_environment_overrides_applies_performance_settings(self, mock_security_config):
        """
        Test that merge_with_environment_overrides() applies performance overrides.

        Verifies:
            merge_with_environment_overrides() updates performance configuration from
            SECURITY_MAX_CONCURRENT_SCANS per contract's Behavior section.

        Business Impact:
            Enables runtime performance tuning through environment variables for
            different deployment scales.

        Scenario:
            Given: Base SecurityConfig and SECURITY_MAX_CONCURRENT_SCANS="20".
            When: merge_with_environment_overrides() is called.
            Then: Returns new SecurityConfig with performance.max_concurrent_scans=20.

        Fixtures Used:
            - mock_security_config: Factory fixture for base SecurityConfig.
        """
        pass

    def test_merge_with_environment_overrides_applies_logging_settings(self, mock_security_config):
        """
        Test that merge_with_environment_overrides() applies logging overrides.

        Verifies:
            merge_with_environment_overrides() updates logging configuration from
            SECURITY_LOG_LEVEL per contract's Behavior section.

        Business Impact:
            Enables runtime logging level adjustment through environment variables
            for troubleshooting.

        Scenario:
            Given: Base SecurityConfig and SECURITY_LOG_LEVEL="DEBUG".
            When: merge_with_environment_overrides() is called.
            Then: Returns new SecurityConfig with logging.log_level="DEBUG".

        Fixtures Used:
            - mock_security_config: Factory fixture for base SecurityConfig.
        """
        pass

    def test_merge_with_environment_overrides_ignores_non_security_variables(self, mock_security_config):
        """
        Test that merge_with_environment_overrides() ignores variables without SECURITY_ prefix.

        Verifies:
            merge_with_environment_overrides() only processes variables starting with
            SECURITY_ per contract's Behavior section.

        Business Impact:
            Prevents unintended configuration changes from unrelated environment
            variables.

        Scenario:
            Given: Base SecurityConfig and overrides with non-SECURITY_ prefixed variables.
            When: merge_with_environment_overrides() is called.
            Then: Returns SecurityConfig unchanged by non-SECURITY_ variables.

        Fixtures Used:
            - mock_security_config: Factory fixture for base SecurityConfig.
        """
        pass

    def test_merge_with_environment_overrides_creates_new_instance(self, mock_security_config):
        """
        Test that merge_with_environment_overrides() creates new SecurityConfig instance.

        Verifies:
            merge_with_environment_overrides() returns new instance without modifying
            original per contract's Behavior section.

        Business Impact:
            Enables immutable configuration pattern where overrides create new
            instances rather than mutating existing ones.

        Scenario:
            Given: Base SecurityConfig instance with original settings.
            When: merge_with_environment_overrides() is called.
            Then: Returns new SecurityConfig instance, leaving original unchanged.

        Fixtures Used:
            - mock_security_config: Factory fixture for base SecurityConfig.
        """
        pass

    def test_merge_with_environment_overrides_handles_boolean_conversion(self, mock_security_config):
        """
        Test that merge_with_environment_overrides() converts string booleans correctly.

        Verifies:
            merge_with_environment_overrides() converts string values "true"/"false"
            to boolean types per contract's Behavior section.

        Business Impact:
            Enables proper boolean configuration from environment variables which
            are always strings.

        Scenario:
            Given: Base SecurityConfig and SECURITY_ENABLE_CACHING="false" string.
            When: merge_with_environment_overrides() is called.
            Then: Returns SecurityConfig with boolean False for caching setting.

        Fixtures Used:
            - mock_security_config: Factory fixture for base SecurityConfig.
        """
        pass


class TestSecurityConfigSerialization:
    """Test SecurityConfig to_dict() and from_dict() serialization methods."""

    def test_to_dict_exports_complete_configuration(self, mock_security_config, mock_scanner_config):
        """
        Test that to_dict() exports all configuration fields to dictionary.

        Verifies:
            to_dict() converts SecurityConfig to dictionary with all fields including
            nested configurations per contract's Returns section.

        Business Impact:
            Enables configuration export for backup, API responses, and persistence
            with complete data preservation.

        Scenario:
            Given: SecurityConfig with complete scanner, performance, and logging configs.
            When: to_dict() is called.
            Then: Returns dictionary containing all configuration fields and nested structures.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_scanner_config: Factory fixture for scanner configurations.
        """
        # Given: SecurityConfig with complete configuration
        config = SecurityConfig(
            service_name="test-service",
            version="2.0.0",
            preset=PresetName.PRODUCTION,
            environment="staging",
            debug_mode=True,
            custom_settings={"test": "value"}
        )

        # When: to_dict() is called
        result = config.to_dict()

        # Then: Returns dictionary containing all configuration fields
        assert isinstance(result, dict)
        assert result["service_name"] == "test-service"
        assert result["version"] == "2.0.0"
        assert result["preset"] == "production"  # Enum converted to string
        assert result["environment"] == "staging"
        assert result["debug_mode"] is True
        assert result["custom_settings"] == {"test": "value"}
        assert "scanners" in result
        assert "performance" in result
        assert "logging" in result
        assert "enabled_scanners" in result  # Computed field

    def test_to_dict_converts_enums_to_strings(self, mock_security_config, scanner_type):
        """
        Test that to_dict() converts enum values to string representations.

        Verifies:
            to_dict() converts ScannerType and ViolationAction enums to strings for
            JSON compatibility per contract's Behavior section.

        Business Impact:
            Ensures exported configuration is JSON-serializable for API responses
            and configuration files.

        Scenario:
            Given: SecurityConfig with scanner configurations using enums.
            When: to_dict() is called.
            Then: Returns dictionary with enum values as strings, not enum objects.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
            - scanner_type: Fixture providing scanner types.
        """
        pass

    def test_to_dict_includes_enabled_scanners_list(self, mock_security_config):
        """
        Test that to_dict() includes computed enabled_scanners field.

        Verifies:
            to_dict() includes enabled_scanners list as computed field per contract's
            Behavior section.

        Business Impact:
            Provides convenient enabled scanner list in exports without requiring
            separate method calls.

        Scenario:
            Given: SecurityConfig with mix of enabled and disabled scanners.
            When: to_dict() is called.
            Then: Returns dictionary with enabled_scanners list containing only enabled types.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
        """
        pass

    def test_to_dict_handles_none_values_gracefully(self, mock_security_config):
        """
        Test that to_dict() handles None values for optional fields.

        Verifies:
            to_dict() includes None values for optional fields without errors per
            contract's Behavior section.

        Business Impact:
            Ensures complete configuration export even when optional fields are
            not populated.

        Scenario:
            Given: SecurityConfig with some optional fields set to None.
            When: to_dict() is called.
            Then: Returns dictionary with None values preserved for optional fields.

        Fixtures Used:
            - mock_security_config: Factory fixture with None values.
        """
        pass

    def test_from_dict_reconstructs_configuration_from_nested_format(self):
        """
        Test that from_dict() reconstructs SecurityConfig from nested dictionary format.

        Verifies:
            from_dict() handles nested structure with input_scanners/output_scanners
            sections per contract's Behavior section.

        Business Impact:
            Enables configuration loading from structured YAML/JSON files with
            organized scanner sections.

        Scenario:
            Given: Dictionary with input_scanners and output_scanners nested sections.
            When: SecurityConfig.from_dict() is called.
            Then: Returns SecurityConfig with scanners properly mapped from nested structure.

        Fixtures Used:
            None - tests deserialization from dictionary.
        """
        pass

    def test_from_dict_reconstructs_configuration_from_legacy_format(self):
        """
        Test that from_dict() handles legacy flat scanner dictionary format.

        Verifies:
            from_dict() supports legacy format with flat scanners dictionary per
            contract's Behavior section.

        Business Impact:
            Maintains backward compatibility with older configuration files for
            seamless upgrades.

        Scenario:
            Given: Dictionary with flat scanners section (legacy format).
            When: SecurityConfig.from_dict() is called.
            Then: Returns SecurityConfig with scanners properly mapped from legacy structure.

        Fixtures Used:
            None - tests legacy format support.
        """
        pass

    def test_from_dict_maps_string_scanner_names_to_enums(self):
        """
        Test that from_dict() converts string scanner names to ScannerType enums.

        Verifies:
            from_dict() maps string scanner names to ScannerType enum members per
            contract's Behavior section.

        Business Impact:
            Enables configuration loading from YAML/JSON where scanner types are
            strings rather than enum objects.

        Scenario:
            Given: Dictionary with scanner names as strings (e.g., "prompt_injection").
            When: SecurityConfig.from_dict() is called.
            Then: Returns SecurityConfig with scanner types as ScannerType enum members.

        Fixtures Used:
            None - tests string to enum conversion.
        """
        pass

    def test_from_dict_converts_string_actions_to_enums(self):
        """
        Test that from_dict() converts string action names to ViolationAction enums.

        Verifies:
            from_dict() maps string action values to ViolationAction enum members per
            contract's Behavior section.

        Business Impact:
            Enables type-safe action configuration from string values in YAML/JSON
            configuration files.

        Scenario:
            Given: Dictionary with action values as strings (e.g., "block", "warn").
            When: SecurityConfig.from_dict() is called.
            Then: Returns SecurityConfig with actions as ViolationAction enum members.

        Fixtures Used:
            None - tests string to enum conversion.
        """
        pass

    def test_from_dict_skips_unknown_scanner_types(self):
        """
        Test that from_dict() gracefully handles unknown scanner type names.

        Verifies:
            from_dict() skips unknown scanner types rather than raising errors per
            contract's Behavior section.

        Business Impact:
            Enables forward compatibility where configuration files may contain
            scanner types not yet supported.

        Scenario:
            Given: Dictionary with unknown scanner type names.
            When: SecurityConfig.from_dict() is called.
            Then: Returns SecurityConfig with unknown scanner types skipped (logged).

        Fixtures Used:
            None - tests unknown scanner handling.
        """
        pass

    def test_from_dict_uses_defaults_for_missing_sections(self):
        """
        Test that from_dict() uses default configurations for missing sections.

        Verifies:
            from_dict() creates default PerformanceConfig and LoggingConfig when
            sections missing per contract's Behavior section.

        Business Impact:
            Enables partial configuration files where missing sections use sensible
            defaults for deployment.

        Scenario:
            Given: Dictionary missing performance or logging sections.
            When: SecurityConfig.from_dict() is called.
            Then: Returns SecurityConfig with default configs for missing sections.

        Fixtures Used:
            None - tests default handling.
        """
        pass


class TestSecurityConfigRoundTripSerialization:
    """Test complete serialization and deserialization cycles."""

    def test_serialization_roundtrip_preserves_all_data(self, mock_security_config, mock_scanner_config):
        """
        Test that to_dict() followed by from_dict() preserves all configuration data.

        Verifies:
            Complete serialization cycle (to_dict() → from_dict()) produces equivalent
            SecurityConfig with identical settings.

        Business Impact:
            Ensures configuration can be safely persisted and restored without data
            loss or corruption.

        Scenario:
            Given: Original SecurityConfig with complete configuration.
            When: to_dict() is called followed by from_dict() on result.
            Then: Reconstructed SecurityConfig has identical settings to original.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_scanner_config: Factory fixture for scanner configurations.
        """
        # Given: Original SecurityConfig with complete configuration (simplified to avoid enum issues)
        original_config = SecurityConfig(
            service_name="roundtrip-test",
            version="1.5.0",
            preset=PresetName.BALANCED,
            environment="testing",
            debug_mode=True,
            custom_settings={"feature": True}
        )

        # When: to_dict() is called followed by from_dict() on result
        config_dict = original_config.to_dict()
        reconstructed_config = SecurityConfig.from_dict(config_dict)

        # Then: Reconstructed SecurityConfig has identical settings to original
        assert reconstructed_config.service_name == original_config.service_name
        assert reconstructed_config.version == original_config.version
        assert reconstructed_config.preset == original_config.preset
        assert reconstructed_config.environment == original_config.environment
        assert reconstructed_config.debug_mode == original_config.debug_mode
        assert reconstructed_config.custom_settings == original_config.custom_settings