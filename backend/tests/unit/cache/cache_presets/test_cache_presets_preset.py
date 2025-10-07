"""
Unit tests for CachePreset dataclass behavior.

This test suite verifies the observable behaviors documented in the
CachePreset dataclass public contract (cache_presets.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Preset configuration management and validation
    - Preset-to-config conversion functionality
    - Environment-specific preset optimization

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""



from app.infrastructure.cache.cache_presets import (CachePreset,
                                                    CacheStrategy)


class TestCachePresetDataclassBehavior:
    """
    Test suite for CachePreset dataclass initialization and basic behavior.

    Scope:
        - Preset dataclass field initialization and validation
        - Environment context assignment and handling
        - Preset description and naming conventions
        - Basic preset parameter organization

    Business Critical:
        Preset dataclass enables streamlined cache configuration for common deployment scenarios

    Test Strategy:
        - Unit tests for preset initialization with various parameter combinations
        - Environment context testing for deployment scenario mapping
        - Preset metadata validation (name, description) testing
        - Parameter organization and structure verification

    External Dependencies:
        - CacheStrategy enum (real): Strategy integration with presets
        - dataclasses module (real): Dataclass functionality
    """

    def test_cache_preset_initializes_with_complete_configuration_parameters(self):
        """
        Test that CachePreset initializes with complete configuration parameters.

        Verifies:
            Preset initialization includes all necessary cache configuration parameters

        Business Impact:
            Ensures presets provide complete configuration without requiring additional setup

        Scenario:
            Given: CachePreset initialization with comprehensive parameters
            When: Preset instance is created with all configuration fields
            Then: All cache configuration parameters are properly initialized
            And: Redis connection parameters are included
            And: Performance parameters are configured appropriately
            And: AI-specific parameters are included (when applicable)

        Complete Configuration Verified:
            - name and description provide preset identification
            - strategy specifies cache performance characteristics
            - Redis parameters (max_connections, connection_timeout) are configured
            - Performance parameters (default_ttl, compression settings) are included
            - AI optimization parameters are configured for AI-enabled presets

        Fixtures Used:
            - None (testing preset initialization directly)

        Configuration Completeness Verified:
            Presets provide complete cache configuration without external dependencies

        Related Tests:
            - test_cache_preset_validates_required_vs_optional_parameters()
            - test_cache_preset_organizes_parameters_by_functional_category()
        """
        # Test regular preset with complete configuration
        preset = CachePreset(
            name="Test Preset",
            description="Test preset for complete configuration",
            strategy=CacheStrategy.BALANCED,
            default_ttl=3600,
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=100,
            compression_threshold=1000,
            compression_level=6,
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["development", "testing"],
            ai_optimizations={},
        )

        # Verify all required fields are initialized
        assert (
            preset.name == "Test Preset"
        ), "Preset name should be properly initialized"
        assert (
            preset.description == "Test preset for complete configuration"
        ), "Preset description should be initialized"
        assert (
            preset.strategy == CacheStrategy.BALANCED
        ), "Strategy should be properly set"

        # Verify Redis connection parameters
        assert (
            preset.max_connections == 10
        ), "Redis max connections should be configured"
        assert (
            preset.connection_timeout == 5
        ), "Redis connection timeout should be configured"

        # Verify performance parameters
        assert preset.default_ttl == 3600, "Default TTL should be configured"
        assert preset.memory_cache_size == 100, "Memory cache size should be configured"
        assert (
            preset.compression_threshold == 1000
        ), "Compression threshold should be configured"
        assert preset.compression_level == 6, "Compression level should be configured"

        # Verify monitoring and logging parameters
        assert preset.enable_monitoring is True, "Monitoring should be configurable"
        assert preset.log_level == "INFO", "Log level should be configured"

        # Verify environment contexts
        assert preset.environment_contexts == [
            "development",
            "testing",
        ], "Environment contexts should be initialized"

        # Test AI-enabled preset with complete AI configuration
        ai_preset = CachePreset(
            name="AI Test Preset",
            description="AI-optimized test preset",
            strategy=CacheStrategy.AI_OPTIMIZED,
            default_ttl=1800,
            max_connections=15,
            connection_timeout=8,
            memory_cache_size=200,
            compression_threshold=500,
            compression_level=6,
            enable_ai_cache=True,
            enable_monitoring=True,
            log_level="DEBUG",
            environment_contexts=["ai-development"],
            ai_optimizations={
                "text_hash_threshold": 500,
                "hash_algorithm": "sha256",
                "operation_ttls": {"summarize": 1800, "sentiment": 900},
            },
        )

        # Verify AI-specific parameters are included
        assert (
            ai_preset.enable_ai_cache is True
        ), "AI cache should be enabled for AI presets"
        assert (
            ai_preset.ai_optimizations["text_hash_threshold"] == 500
        ), "AI optimization parameters should be configured"
        assert (
            "summarize" in ai_preset.ai_optimizations["operation_ttls"]
        ), "AI operation TTLs should be configured"
        assert (
            ai_preset.ai_optimizations["hash_algorithm"] == "sha256"
        ), "AI hash algorithm should be configured"

    def test_cache_preset_assigns_environment_contexts_appropriately(self):
        """
        Test that CachePreset assigns environment contexts for deployment scenario mapping.

        Verifies:
            Environment contexts enable appropriate preset selection for different deployments

        Business Impact:
            Enables automatic preset recommendation based on deployment environment characteristics

        Scenario:
            Given: CachePreset with environment_contexts configuration
            When: Preset is examined for environment applicability
            Then: Environment contexts list includes appropriate deployment scenarios
            And: Development presets include 'development', 'local' contexts
            And: Production presets include 'production', 'staging' contexts
            And: AI presets include AI-specific environment contexts

        Environment Context Assignment Verified:
            - Development presets: ['development', 'local', 'testing']
            - Production presets: ['production', 'staging']
            - AI presets: ['ai-development', 'ai-production']
            - Minimal presets: ['minimal', 'embedded', 'serverless']

        Fixtures Used:
            - None (testing environment context assignment directly)

        Environment Mapping Verified:
            Environment contexts enable intelligent preset recommendation for deployment scenarios

        Related Tests:
            - test_cache_preset_environment_contexts_support_deployment_classification()
            - test_cache_preset_contexts_enable_preset_recommendation_logic()
        """
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Test development preset environment contexts
        development_preset = CACHE_PRESETS["development"]
        assert (
            "development" in development_preset.environment_contexts
        ), "Development preset should include 'development' context"
        assert (
            "local" in development_preset.environment_contexts
        ), "Development preset should include 'local' context"

        # Test production preset environment contexts
        production_preset = CACHE_PRESETS["production"]
        assert (
            "production" in production_preset.environment_contexts
        ), "Production preset should include 'production' context"
        assert (
            "staging" in production_preset.environment_contexts
        ), "Production preset should include 'staging' context"

        # Test AI development preset contexts
        ai_dev_preset = CACHE_PRESETS["ai-development"]
        assert (
            "development" in ai_dev_preset.environment_contexts
        ), "AI development preset should include 'development' context"
        assert (
            "ai-development" in ai_dev_preset.environment_contexts
        ), "AI development preset should include 'ai-development' context"

        # Test AI production preset contexts
        ai_prod_preset = CACHE_PRESETS["ai-production"]
        assert (
            "production" in ai_prod_preset.environment_contexts
        ), "AI production preset should include 'production' context"
        assert (
            "ai-production" in ai_prod_preset.environment_contexts
        ), "AI production preset should include 'ai-production' context"

        # Test minimal preset contexts
        minimal_preset = CACHE_PRESETS["minimal"]
        assert (
            "minimal" in minimal_preset.environment_contexts
        ), "Minimal preset should include 'minimal' context"
        assert (
            "embedded" in minimal_preset.environment_contexts
        ), "Minimal preset should include 'embedded' context"
        assert (
            "serverless" in minimal_preset.environment_contexts
        ), "Minimal preset should include 'serverless' context"

        # Test disabled preset contexts
        disabled_preset = CACHE_PRESETS["disabled"]
        assert (
            "testing" in disabled_preset.environment_contexts
        ), "Disabled preset should include 'testing' context"
        assert (
            "minimal" in disabled_preset.environment_contexts
        ), "Disabled preset should include 'minimal' context"

        # Test simple preset has broad applicability
        simple_preset = CACHE_PRESETS["simple"]
        expected_contexts = ["development", "testing", "staging", "production"]
        for context in expected_contexts:
            assert (
                context in simple_preset.environment_contexts
            ), f"Simple preset should support '{context}' context"

        # Verify all presets have at least one environment context
        for preset_name, preset in CACHE_PRESETS.items():
            assert (
                len(preset.environment_contexts) > 0
            ), f"Preset '{preset_name}' should have at least one environment context"
            assert all(
                isinstance(ctx, str) for ctx in preset.environment_contexts
            ), f"All environment contexts for '{preset_name}' should be strings"

    def test_cache_preset_maintains_consistent_parameter_organization(self):
        """
        Test that CachePreset maintains consistent parameter organization across different presets.

        Verifies:
            Parameter organization follows consistent patterns across all preset types

        Business Impact:
            Ensures predictable preset behavior and simplified preset comparison

        Scenario:
            Given: Multiple CachePreset instances with different configurations
            When: Preset parameter organization is examined
            Then: All presets follow consistent parameter naming patterns
            And: Parameter categories are organized consistently
            And: Optional parameters are handled uniformly
            And: Parameter defaults follow consistent logic

        Parameter Organization Verified:
            - Basic parameters (name, description, strategy) are consistent
            - Connection parameters follow uniform naming and ranges
            - Performance parameters use consistent units and ranges
            - AI parameters are consistently organized when present

        Fixtures Used:
            - None (testing parameter organization patterns directly)

        Preset Consistency Verified:
            All presets follow consistent parameter organization for predictable behavior

        Related Tests:
            - test_cache_preset_parameter_naming_follows_conventions()
            - test_cache_preset_optional_parameters_have_sensible_defaults()
        """
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Get all preset instances
        all_presets = list(CACHE_PRESETS.values())

        # Verify all presets have consistent basic parameters
        required_basic_fields = ["name", "description", "strategy"]
        for preset in all_presets:
            for field in required_basic_fields:
                assert hasattr(
                    preset, field
                ), f"Preset '{preset.name}' should have '{field}' field"
                assert (
                    getattr(preset, field) is not None
                ), f"Preset '{preset.name}' should have non-None '{field}'"

        # Verify all presets have consistent connection parameters
        connection_fields = ["max_connections", "connection_timeout"]
        for preset in all_presets:
            for field in connection_fields:
                assert hasattr(
                    preset, field
                ), f"Preset '{preset.name}' should have '{field}' field"
                value = getattr(preset, field)
                assert isinstance(
                    value, int
                ), f"Connection parameter '{field}' should be integer in preset '{preset.name}'"
                assert (
                    value > 0
                ), f"Connection parameter '{field}' should be positive in preset '{preset.name}'"

        # Verify all presets have consistent performance parameters
        performance_fields = [
            "default_ttl",
            "memory_cache_size",
            "compression_threshold",
            "compression_level",
        ]
        for preset in all_presets:
            for field in performance_fields:
                assert hasattr(
                    preset, field
                ), f"Preset '{preset.name}' should have '{field}' field"
                value = getattr(preset, field)
                assert isinstance(
                    value, int
                ), f"Performance parameter '{field}' should be integer in preset '{preset.name}'"
                assert (
                    value > 0
                ), f"Performance parameter '{field}' should be positive in preset '{preset.name}'"

        # Verify consistent monitoring and logging parameters
        monitoring_fields = ["enable_ai_cache", "enable_monitoring", "log_level"]
        for preset in all_presets:
            for field in monitoring_fields:
                assert hasattr(
                    preset, field
                ), f"Preset '{preset.name}' should have '{field}' field"

        # Verify log levels use consistent values
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        for preset in all_presets:
            assert (
                preset.log_level in valid_log_levels
            ), f"Preset '{preset.name}' should use valid log level, got '{preset.log_level}'"

        # Verify environment contexts consistency
        for preset in all_presets:
            assert hasattr(
                preset, "environment_contexts"
            ), f"Preset '{preset.name}' should have environment_contexts"
            assert isinstance(
                preset.environment_contexts, list
            ), f"environment_contexts should be list in preset '{preset.name}'"
            assert (
                len(preset.environment_contexts) > 0
            ), f"Preset '{preset.name}' should have at least one environment context"

        # Verify AI parameters are consistently organized
        for preset in all_presets:
            assert hasattr(
                preset, "ai_optimizations"
            ), f"Preset '{preset.name}' should have ai_optimizations field"
            assert isinstance(
                preset.ai_optimizations, dict
            ), f"ai_optimizations should be dict in preset '{preset.name}'"

            # If AI is enabled, verify consistent AI parameter structure
            if preset.enable_ai_cache:
                ai_opts = preset.ai_optimizations
                expected_ai_fields = [
                    "text_hash_threshold",
                    "hash_algorithm",
                    "operation_ttls",
                ]
                for field in expected_ai_fields:
                    assert (
                        field in ai_opts
                    ), f"AI preset '{preset.name}' should have '{field}' in ai_optimizations"

        # Verify parameter ranges are consistent across presets
        for preset in all_presets:
            # TTL should be reasonable (1 second to 1 week)
            assert (
                1 <= preset.default_ttl <= 604800
            ), f"TTL in preset '{preset.name}' should be between 1s and 1 week"

            # Connection parameters should be reasonable
            assert (
                1 <= preset.max_connections <= 100
            ), f"max_connections in preset '{preset.name}' should be 1-100"
            assert (
                1 <= preset.connection_timeout <= 60
            ), f"connection_timeout in preset '{preset.name}' should be 1-60"

            # Compression level should be valid
            assert (
                1 <= preset.compression_level <= 9
            ), f"compression_level in preset '{preset.name}' should be 1-9"


class TestCachePresetValidation:
    """
    Test suite for CachePreset validation and consistency checking.

    Scope:
        - Preset parameter validation and range checking
        - Strategy-preset consistency validation
        - Environment context validation
        - AI optimization parameter validation

    Business Critical:
        Preset validation ensures deployment-ready configurations for all common scenarios

    Test Strategy:
        - Unit tests for preset validation with CACHE_PRESETS definitions
        - Strategy consistency validation across preset types
        - Environment context validation for deployment scenario coverage
        - AI parameter validation for AI-enabled preset types

    External Dependencies:
        - CACHE_PRESETS dictionary (real): Predefined preset validation
        - Validation logic (internal): Preset consistency checking
    """

    def test_cache_preset_validates_predefined_preset_configurations(self):
        """
        Test that predefined CACHE_PRESETS configurations pass validation.

        Verifies:
            All predefined presets in CACHE_PRESETS are valid and deployment-ready

        Business Impact:
            Ensures all predefined presets work correctly without configuration errors

        Scenario:
            Given: Predefined presets in CACHE_PRESETS dictionary
            When: Each preset is validated for configuration correctness
            Then: All presets pass parameter validation
            And: All preset parameter values are within acceptable ranges
            And: All presets have consistent strategy-parameter alignment
            And: All presets include complete configuration for their intended use

        Predefined Preset Validation Verified:
            - 'disabled' preset: Minimal configuration for testing scenarios
            - 'simple' preset: Balanced configuration for general use
            - 'development' preset: Development-optimized configuration
            - 'production' preset: Production-ready configuration
            - 'ai-development' preset: AI development configuration
            - 'ai-production' preset: AI production configuration

        Fixtures Used:
            - None (validating real CACHE_PRESETS definitions)

        Preset Quality Assurance Verified:
            All predefined presets meet quality standards for their intended deployment scenarios

        Related Tests:
            - test_cache_preset_validates_strategy_parameter_consistency()
            - test_cache_preset_validates_environment_context_appropriateness()
        """
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        expected_presets = [
            "disabled",
            "minimal",
            "simple",
            "development",
            "production",
            "ai-development",
            "ai-production",
        ]

        # Verify all expected presets exist
        for preset_name in expected_presets:
            assert (
                preset_name in CACHE_PRESETS
            ), f"Expected preset '{preset_name}' should exist in CACHE_PRESETS"

        # Validate each predefined preset
        for preset_name, preset in CACHE_PRESETS.items():
            # Basic configuration completeness
            assert preset.name, f"Preset '{preset_name}' should have a name"
            assert (
                preset.description
            ), f"Preset '{preset_name}' should have a description"
            assert preset.strategy, f"Preset '{preset_name}' should have a strategy"

            # Parameter range validation
            assert (
                1 <= preset.default_ttl <= 604800
            ), f"Preset '{preset_name}' TTL should be 1s-1week, got {preset.default_ttl}"
            assert (
                1 <= preset.max_connections <= 100
            ), f"Preset '{preset_name}' max_connections should be 1-100, got {preset.max_connections}"
            assert (
                1 <= preset.connection_timeout <= 60
            ), f"Preset '{preset_name}' connection_timeout should be 1-60s, got {preset.connection_timeout}"
            assert (
                1 <= preset.memory_cache_size <= 10000
            ), f"Preset '{preset_name}' memory_cache_size should be 1-10000, got {preset.memory_cache_size}"
            assert (
                1 <= preset.compression_level <= 9
            ), f"Preset '{preset_name}' compression_level should be 1-9, got {preset.compression_level}"

            # Verify boolean fields are properly set
            assert isinstance(
                preset.enable_ai_cache, bool
            ), f"Preset '{preset_name}' enable_ai_cache should be boolean"
            assert isinstance(
                preset.enable_monitoring, bool
            ), f"Preset '{preset_name}' enable_monitoring should be boolean"

            # Verify log level is valid
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
            assert (
                preset.log_level in valid_log_levels
            ), f"Preset '{preset_name}' should have valid log level, got '{preset.log_level}'"

            # Verify environment contexts are provided
            assert isinstance(
                preset.environment_contexts, list
            ), f"Preset '{preset_name}' environment_contexts should be list"
            assert (
                len(preset.environment_contexts) > 0
            ), f"Preset '{preset_name}' should have at least one environment context"

            # Verify ai_optimizations structure
            assert isinstance(
                preset.ai_optimizations, dict
            ), f"Preset '{preset_name}' ai_optimizations should be dict"

        # Specific validation for key presets
        # Disabled preset should be minimal
        disabled = CACHE_PRESETS["disabled"]
        assert disabled.default_ttl <= 300, "Disabled preset should have short TTL"
        assert (
            disabled.max_connections <= 2
        ), "Disabled preset should have minimal connections"
        assert (
            not disabled.enable_ai_cache
        ), "Disabled preset should not have AI features"

        # Production preset should be robust
        production = CACHE_PRESETS["production"]
        assert (
            production.default_ttl >= 3600
        ), "Production preset should have reasonable TTL"
        assert (
            production.max_connections >= 10
        ), "Production preset should support many connections"
        assert (
            production.compression_level >= 6
        ), "Production preset should have good compression"

        # AI presets should have AI optimizations
        ai_dev = CACHE_PRESETS["ai-development"]
        ai_prod = CACHE_PRESETS["ai-production"]

        for ai_preset, name in [(ai_dev, "ai-development"), (ai_prod, "ai-production")]:
            assert (
                ai_preset.enable_ai_cache
            ), f"AI preset '{name}' should have AI cache enabled"
            assert (
                "text_hash_threshold" in ai_preset.ai_optimizations
            ), f"AI preset '{name}' should have text_hash_threshold"
            assert (
                "operation_ttls" in ai_preset.ai_optimizations
            ), f"AI preset '{name}' should have operation_ttls"
            assert (
                "hash_algorithm" in ai_preset.ai_optimizations
            ), f"AI preset '{name}' should have hash_algorithm"

    def test_cache_preset_validates_strategy_parameter_consistency(self):
        """Test strategy-parameter consistency validation."""
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Group presets by strategy
        strategy_presets = {}
        for preset_name, preset in CACHE_PRESETS.items():
            strategy = preset.strategy
            if strategy not in strategy_presets:
                strategy_presets[strategy] = []
            strategy_presets[strategy].append((preset_name, preset))

        # Validate FAST strategy presets (development-focused)
        if CacheStrategy.FAST in strategy_presets:
            for preset_name, preset in strategy_presets[CacheStrategy.FAST]:
                # FAST strategy should have shorter TTLs for quick feedback
                assert (
                    preset.default_ttl <= 900
                ), f"FAST strategy preset '{preset_name}' should have short TTL (<=900s), got {preset.default_ttl}"

                # FAST strategy should have fewer connections (development-appropriate)
                assert (
                    preset.max_connections <= 5
                ), f"FAST strategy preset '{preset_name}' should have few connections (<=5), got {preset.max_connections}"

                # FAST strategy should have lower compression levels for speed
                assert (
                    preset.compression_level <= 6
                ), f"FAST strategy preset '{preset_name}' should have fast compression (<=6), got {preset.compression_level}"

    def test_cache_preset_validates_ai_optimization_parameters(self):
        """Test AI optimization parameter validation."""
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Get AI-enabled presets
        ai_presets = {
            name: preset
            for name, preset in CACHE_PRESETS.items()
            if preset.enable_ai_cache
        }
        non_ai_presets = {
            name: preset
            for name, preset in CACHE_PRESETS.items()
            if not preset.enable_ai_cache
        }

        # Validate AI-enabled presets have proper AI configuration
        for preset_name, preset in ai_presets.items():
            # Verify AI cache is enabled
            assert (
                preset.enable_ai_cache is True
            ), f"AI preset '{preset_name}' should have enable_ai_cache=True"

            # Verify AI optimizations are configured
            ai_opts = preset.ai_optimizations
            assert isinstance(
                ai_opts, dict
            ), f"AI preset '{preset_name}' ai_optimizations should be dict"
            assert (
                len(ai_opts) > 0
            ), f"AI preset '{preset_name}' should have non-empty ai_optimizations"

            # Verify text_hash_threshold is configured appropriately
            assert (
                "text_hash_threshold" in ai_opts
            ), f"AI preset '{preset_name}' should have text_hash_threshold"
            threshold = ai_opts["text_hash_threshold"]
            assert isinstance(
                threshold, int
            ), f"text_hash_threshold should be integer in preset '{preset_name}'"
            assert (
                100 <= threshold <= 10000
            ), f"text_hash_threshold should be 100-10000 in preset '{preset_name}', got {threshold}"

    def test_cache_preset_validates_environment_context_coverage(self):
        """Test environment context coverage validation."""
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Collect all environment contexts across all presets
        all_contexts = set()
        context_to_presets = {}

        for preset_name, preset in CACHE_PRESETS.items():
            for context in preset.environment_contexts:
                all_contexts.add(context)
                if context not in context_to_presets:
                    context_to_presets[context] = []
                context_to_presets[context].append(preset_name)

        # Verify development scenarios have coverage
        dev_contexts = ["development", "local"]
        dev_presets = set()
        for context in dev_contexts:
            if context in context_to_presets:
                dev_presets.update(context_to_presets[context])

        assert (
            len(dev_presets) >= 2
        ), f"Development scenarios should have at least 2 preset options, found: {dev_presets}"
        assert (
            "development" in dev_presets or "simple" in dev_presets
        ), "Development scenarios should include development or simple preset"


class TestCachePresetConversion:
    """
    Test suite for CachePreset conversion methods.

    Scope:
        - Preset-to-CacheConfig conversion with to_cache_config() method
        - Dictionary serialization with to_dict() method
        - Parameter mapping and transformation during conversion
        - Conversion data integrity verification

    Business Critical:
        Preset conversion enables integration with cache configuration and factory systems

    Test Strategy:
        - Unit tests for to_cache_config() method with different preset types
        - Dictionary conversion testing for serialization compatibility
        - Parameter mapping verification during conversion
        - Data integrity testing across conversion operations

    External Dependencies:
        - CacheConfig class (real): Conversion target for preset-to-config transformation
        - Parameter mapping logic (internal): Preset parameter transformation
    """

    def test_cache_preset_to_cache_config_produces_equivalent_configuration(self):
        """Test to_cache_config() produces equivalent configuration."""
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Test conversion with different preset types
        test_presets = ["simple", "production", "ai-development", "ai-production"]

        for preset_name in test_presets:
            preset = CACHE_PRESETS[preset_name]

            # Convert preset to cache config
            config = preset.to_cache_config()

            # Verify config is not None
            assert (
                config is not None
            ), f"Preset '{preset_name}' should convert to non-None config"

            # Verify basic parameter equivalence
            assert (
                config.default_ttl == preset.default_ttl
            ), f"TTL should be preserved in conversion for preset '{preset_name}'"
            assert (
                config.memory_cache_size == preset.memory_cache_size
            ), f"Memory cache size should be preserved for preset '{preset_name}'"
            assert (
                config.compression_threshold == preset.compression_threshold
            ), f"Compression threshold should be preserved for preset '{preset_name}'"
            assert (
                config.compression_level == preset.compression_level
            ), f"Compression level should be preserved for preset '{preset_name}'"

            # Verify environment context is mapped
            assert hasattr(
                config, "environment"
            ), f"Converted config should have environment field for preset '{preset_name}'"
            assert (
                config.environment in preset.environment_contexts
            ), f"Config environment should match preset contexts for '{preset_name}'"

    def test_cache_preset_to_dict_enables_serialization_and_storage(self):
        """Test to_dict() enables serialization and storage."""

        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Test dictionary conversion for different preset types
        test_presets = [
            "disabled",
            "simple",
            "production",
            "ai-development",
            "ai-production",
        ]

        for preset_name in test_presets:
            preset = CACHE_PRESETS[preset_name]

            # Convert to dictionary
            preset_dict = preset.to_dict()

            # Verify dictionary is not None and is actually a dict
            assert (
                preset_dict is not None
            ), f"Preset '{preset_name}' should convert to non-None dictionary"
            assert isinstance(
                preset_dict, dict
            ), f"to_dict() should return dict for preset '{preset_name}'"

            # Verify all preset fields are included
            expected_fields = [
                "name",
                "description",
                "strategy",
                "default_ttl",
                "max_connections",
                "connection_timeout",
                "memory_cache_size",
                "compression_threshold",
                "compression_level",
                "enable_ai_cache",
                "enable_monitoring",
                "log_level",
                "environment_contexts",
                "ai_optimizations",
            ]

            for field in expected_fields:
                assert (
                    field in preset_dict
                ), f"Dictionary should contain '{field}' field for preset '{preset_name}'"

    def test_cache_preset_conversion_handles_ai_parameters_correctly(self):
        """Test AI parameter conversion handling."""
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Get AI and non-AI presets
        ai_presets = {
            name: preset
            for name, preset in CACHE_PRESETS.items()
            if preset.enable_ai_cache
        }
        non_ai_presets = {
            name: preset
            for name, preset in CACHE_PRESETS.items()
            if not preset.enable_ai_cache
        }

        # Test AI parameter conversion for AI presets
        for preset_name, preset in ai_presets.items():
            # Test to_cache_config() conversion
            config = preset.to_cache_config()

            # Verify AI configuration is present and properly structured
            assert (
                config.ai_config is not None
            ), f"AI preset '{preset_name}' should have ai_config in converted config"

        # Test non-AI parameter conversion excludes AI parameters appropriately
        for preset_name, preset in non_ai_presets.items():
            # Test to_cache_config() conversion
            config = preset.to_cache_config()

            # Verify AI configuration is not present or is None/empty
            assert (
                config.ai_config is None
            ), f"Non-AI preset '{preset_name}' should not have ai_config in converted config"

    def test_cache_preset_conversion_maintains_environment_context_information(self):
        """Test environment context preservation during conversion."""
        from app.infrastructure.cache.cache_presets import CACHE_PRESETS

        # Test environment context preservation across conversion operations
        test_presets = [
            "development",
            "production",
            "ai-development",
            "ai-production",
            "simple",
        ]

        for preset_name in test_presets:
            preset = CACHE_PRESETS[preset_name]
            original_contexts = preset.environment_contexts.copy()

            # Test to_cache_config() preserves environment information
            config = preset.to_cache_config()

            # Verify environment is set in config (should be first context or appropriate mapping)
            assert hasattr(
                config, "environment"
            ), f"Converted config should have environment field for preset '{preset_name}'"
            assert (
                config.environment is not None
            ), f"Config environment should not be None for preset '{preset_name}'"
            assert (
                config.environment in original_contexts
            ), f"Config environment should be from original contexts for preset '{preset_name}'"

            # Test to_dict() preserves full environment context list
            preset_dict = preset.to_dict()

            assert (
                "environment_contexts" in preset_dict
            ), f"Dictionary should include environment_contexts for preset '{preset_name}'"
            assert isinstance(
                preset_dict["environment_contexts"], list
            ), f"environment_contexts should be list in dictionary for preset '{preset_name}'"
            assert (
                preset_dict["environment_contexts"] == original_contexts
            ), f"Dictionary should preserve all environment contexts for preset '{preset_name}'"
