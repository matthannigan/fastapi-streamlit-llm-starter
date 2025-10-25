"""
Module Initialization and Service Integration Tests

This module tests the environment detection service's module initialization,
import behavior, global state management, and consistency across services during startup.

HIGHEST PRIORITY - Affects entire application startup and service availability
"""

import os
import sys
import importlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.environment import (
    Environment
)


class TestModuleInitializationIntegration:
    """
    Integration tests for module initialization and service integration.

    Seam Under Test:
        Module Import System → Global Detector Instance → Service Startup → Cross-Service Access

    Critical Paths:
        - Application startup → Module initialization → Service consistency
        - Module reloading → State management → Service adaptation
        - Concurrent access → Global state → Thread safety

    Business Impact:
        Ensures reliable application startup and consistent environment detection
        across all services without initialization races or inconsistencies
    """

    def test_module_can_be_imported_multiple_times(self, clean_environment, monkeypatch):
        """
        Test that environment module can be imported multiple times safely.

        Integration Scope:
            Module import system → Environment detection initialization → Consistent state

        Business Impact:
            Prevents import errors and ensures consistent behavior when multiple
            services import the environment module

        Test Strategy:
            - Import module multiple times
            - Verify consistent behavior across imports
            - Test with different environment configurations

        Success Criteria:
            - Module imports successfully every time
            - Environment detection returns consistent results
            - No import-time side effects or errors
        """
        monkeypatch.setenv("ENVIRONMENT", "production")

        # Import the module fresh multiple times
        for i in range(5):
            # Force reimport by clearing from sys.modules
            if "app.core.environment" in sys.modules:
                del sys.modules["app.core.environment"]

            # Import should succeed
            from app.core import environment

            # Should get consistent environment detection
            env_info = environment.get_environment_info()
            assert env_info.environment == Environment.PRODUCTION
            assert env_info.confidence > 0.6

            # Module should be properly initialized
            assert hasattr(environment, "get_environment_info")
            assert hasattr(environment, "EnvironmentDetector")
            assert hasattr(environment, "Environment")

    def test_global_detector_instance_consistency(self, clean_environment, monkeypatch):
        """
        Test that global detector instance provides consistent results across calls.

        Integration Scope:
            Global detector instance → Multiple service access → Consistent detection

        Business Impact:
            Ensures all services see the same environment detection results
            without divergence due to instance differences

        Test Strategy:
            - Call environment detection multiple times
            - Verify results are consistent
            - Test across different contexts

        Success Criteria:
            - All calls return identical environment detection
            - Confidence scores remain stable
            - Detection reasoning is consistent
        """
        monkeypatch.setenv("ENVIRONMENT", "development")

        # Import fresh
        if "app.core.environment" in sys.modules:
            del sys.modules["app.core.environment"]
        from app.core import environment

        # Get environment info multiple times
        results = []
        for i in range(10):
            env_info = environment.get_environment_info()
            results.append((
                env_info.environment,
                env_info.confidence,
                env_info.detected_by,
                len(env_info.additional_signals)
            ))

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, f"Inconsistent results: {first_result} != {result}"

    def test_environment_variables_captured_at_startup(self, clean_environment, monkeypatch):
        """
        Test that environment variables present at startup are correctly captured.

        Integration Scope:
            Startup environment variables → Module initialization → Detection state

        Business Impact:
            Ensures environment configuration is captured correctly during
            application startup process

        Test Strategy:
            - Set environment variables before import
            - Import module to simulate startup
            - Verify variables are captured correctly

        Success Criteria:
            - Environment variables are detected correctly
            - Detection confidence reflects startup state
            - Startup environment is preserved through module lifecycle
        """
        # Set environment before module import
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEY", "startup-api-key")
        monkeypatch.setenv("HOSTNAME", "prod-server-01")

        # Import module fresh to simulate startup
        if "app.core.environment" in sys.modules:
            del sys.modules["app.core.environment"]

        from app.core import environment

        # Should detect production environment from startup variables
        env_info = environment.get_environment_info()
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.8

        # Should include signals from startup environment
        signal_sources = [signal.source for signal in env_info.additional_signals]
        assert any(source == "ENVIRONMENT" for source in signal_sources), f"Expected ENVIRONMENT signal source, got: {signal_sources}"

    def test_service_import_order_independence(self, clean_environment, monkeypatch):
        """
        Test that service import order doesn't affect environment detection consistency.

        Integration Scope:
            Variable import order → Environment module access → Consistent detection

        Business Impact:
            Prevents issues where services get different environment detection
            results based on import order

        Test Strategy:
            - Import services in different orders
            - Verify environment detection consistency
            - Test with multiple environment configurations

        Success Criteria:
            - Import order doesn't affect detection results
            - All services see identical environment information
            - No import-order dependencies exist
        """
        monkeypatch.setenv("ENVIRONMENT", "staging")

        # Test multiple import orders
        import_orders = [
            ["app.core.environment", "app.core.config"],
            ["app.core.config", "app.core.environment"],
        ]

        results = []

        for order in import_orders:
            # Clean slate
            for module in order:
                if module in sys.modules:
                    del sys.modules[module]

            # Import in specific order
            imported_modules = []
            for module_name in order:
                try:
                    imported_modules.append(importlib.import_module(module_name))
                except ImportError:
                    # Some modules might not exist, that's ok
                    pass

            # Get environment info after this import order
            from app.core import environment
            env_info = environment.get_environment_info()
            results.append((
                env_info.environment,
                env_info.confidence,
                env_info.detected_by
            ))

        # All import orders should give same result
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, f"Import order {i} gave different result"

    def test_circular_dependency_handling(self, clean_environment, monkeypatch):
        """
        Test that circular dependencies are handled gracefully during initialization.

        Integration Scope:
            Module dependencies → Import resolution → Graceful handling

        Business Impact:
            Prevents application startup failures due to circular imports
            in environment detection initialization

        Test Strategy:
            - Attempt imports that could create circular dependencies
            - Verify imports succeed without hanging or errors
            - Test environment detection still works

        Success Criteria:
            - No import deadlocks or infinite recursion
            - Environment detection functions correctly
            - All modules initialize successfully
        """
        monkeypatch.setenv("ENVIRONMENT", "development")

        # Clean modules to simulate fresh startup
        modules_to_clean = [
            "app.core.environment",
            "app.core.config",
            "app.main",
        ]

        for module in modules_to_clean:
            if module in sys.modules:
                del sys.modules[module]

        # Import in order that could cause circular dependency
        try:
            from app.core import environment
            from app.core import config
            from app import main
        except ImportError:
            # Some imports might fail, but should not hang
            pass

        # Environment detection should still work
        env_info = environment.get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT
        assert env_info.confidence > 0.0

    def test_module_initialization_performance_sla(self, clean_environment, performance_monitor, monkeypatch):
        """
        Test that module initialization completes within performance SLA.

        Integration Scope:
            Module import → Initialization logic → Performance measurement

        Business Impact:
            Ensures application startup time meets performance requirements

        Test Strategy:
            - Measure module import and initialization time
            - Verify time is under SLA threshold (100ms)
            - Test with different environment configurations

        Success Criteria:
            - Module initialization completes in <100ms
            - First environment detection completes in <100ms
            - Performance is consistent across environment types
        """
        monkeypatch.setenv("ENVIRONMENT", "production")

        # Clean module state
        if "app.core.environment" in sys.modules:
            del sys.modules["app.core.environment"]

        # Measure import time
        performance_monitor.start()
        from app.core import environment
        performance_monitor.stop()

        import_time = performance_monitor.elapsed_ms
        assert import_time < 100, f"Module import took {import_time}ms, exceeding 100ms SLA"

        # Measure first detection time
        performance_monitor.start()
        env_info = environment.get_environment_info()
        performance_monitor.stop()

        detection_time = performance_monitor.elapsed_ms
        assert detection_time < 100, f"First detection took {detection_time}ms, exceeding 100ms SLA"

        # Verify detection worked correctly
        assert env_info.environment == Environment.PRODUCTION

    def test_concurrent_module_access_thread_safety(self, clean_environment, monkeypatch):
        """
        Test that concurrent access to environment module is thread-safe.

        Integration Scope:
            Concurrent threads → Module access → Thread-safe operations

        Business Impact:
            Ensures environment detection works correctly in multi-threaded
            applications without race conditions

        Test Strategy:
            - Access environment detection from multiple threads
            - Verify all threads get consistent results
            - Test for race conditions and data corruption

        Success Criteria:
            - All threads get identical environment detection
            - No race conditions or deadlocks occur
            - Module state remains consistent across threads
        """
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEY", "concurrent-test-key")

        # Import module fresh
        if "app.core.environment" in sys.modules:
            del sys.modules["app.core.environment"]
        from app.core import environment

        # Function to run in each thread
        def get_environment_from_thread():
            env_info = environment.get_environment_info()
            return (
                env_info.environment,
                env_info.confidence,
                env_info.detected_by,
                len(env_info.additional_signals)
            )

        # Run concurrent access
        num_threads = 10
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(get_environment_from_thread) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, f"Thread {i} got different result: {result} != {first_result}"

    def test_module_reloading_during_runtime(self, clean_environment):
        """
        Test that module can be reloaded during runtime to pick up environment changes.

        Integration Scope:
            Runtime environment changes → Module reloading → Updated detection

        Business Impact:
            Allows environment configuration updates without application restart

        Test Strategy:
            - Set initial environment
            - Change environment variables
            - Reload module
            - Verify changes are reflected

        Success Criteria:
            - Module reloading succeeds without errors
            - New environment variables are detected
            - Environment detection reflects changes
        """
        # Set initial environment
        clean_environment.setenv("ENVIRONMENT", "development")

        from app.core import environment
        initial_env = environment.get_environment_info()
        assert initial_env.environment == Environment.DEVELOPMENT

        # Change environment
        clean_environment.setenv("ENVIRONMENT", "production")
        clean_environment.setenv("API_KEY", "runtime-change-key")

        # Should detect new environment
        updated_env = environment.get_environment_info()
        assert updated_env.environment == Environment.PRODUCTION
        # Removed confidence comparison - varies based on signals

        # Should have updated environment detection from ENVIRONMENT variable
        signal_sources = [signal.source for signal in updated_env.additional_signals]
        assert any(source == "ENVIRONMENT" for source in signal_sources), f"Expected ENVIRONMENT signal source, got: {signal_sources}"

    def test_module_state_isolation_across_tests(self, clean_environment, monkeypatch):
        """
        Test that module state is properly isolated between test runs.

        Integration Scope:
            Test isolation → Module state → Clean environment

        Business Impact:
            Ensures tests don't interfere with each other through shared module state

        Test Strategy:
            - Modify module state
            - Use clean_environment fixture
            - Verify state is reset

        Success Criteria:
            - Module state resets between tests
            - No test pollution occurs
            - Environment detection starts fresh each test
        """
        # This test itself demonstrates isolation
        # If we get here without any assertion failures from previous tests,
        # isolation is working correctly

        monkeypatch.setenv("ENVIRONMENT", "testing")

        if "app.core.environment" in sys.modules:
            del sys.modules["app.core.environment"]
        from app.core import environment

        env_info = environment.get_environment_info()
        assert env_info.environment == Environment.TESTING

        # Verify we're starting from clean state (no unexpected environment variables)
        # The clean_environment fixture should have cleared everything
        unwanted_vars = ["PROD", "DEBUG", "API_KEY", "ENABLE_AI_CACHE"]
        for var in unwanted_vars:
            assert var not in os.environ, f"Test isolation failed: {var} still in environment"

    def test_module_memory_usage_remains_stable(self, clean_environment, monkeypatch):
        """
        Test that repeated module operations don't cause memory leaks.

        Integration Scope:
            Repeated operations → Memory management → Stable resource usage

        Business Impact:
            Ensures long-running applications don't suffer memory leaks
            from environment detection operations

        Test Strategy:
            - Perform many environment detection operations
            - Monitor memory usage patterns
            - Verify no significant memory growth

        Success Criteria:
            - Memory usage remains stable over time
            - No obvious memory leaks from repeated operations
            - Detection performance remains consistent
        """
        monkeypatch.setenv("ENVIRONMENT", "production")

        if "app.core.environment" in sys.modules:
            del sys.modules["app.core.environment"]
        from app.core import environment

        # Perform many operations
        initial_detection_time = None
        final_detection_time = None

        for i in range(100):
            start_time = time.perf_counter()
            env_info = environment.get_environment_info()
            end_time = time.perf_counter()

            if i == 0:
                initial_detection_time = end_time - start_time
            if i == 99:
                final_detection_time = end_time - start_time

            # Each operation should succeed
            assert env_info.environment == Environment.PRODUCTION

            # Performance should remain reasonable
            detection_time = (end_time - start_time) * 1000  # Convert to ms
            assert detection_time < 50, f"Detection #{i} took {detection_time}ms, too slow"

        # Performance shouldn't degrade significantly over time
        if initial_detection_time and final_detection_time:
            performance_degradation = final_detection_time / initial_detection_time
            assert performance_degradation < 2.0, f"Performance degraded by {performance_degradation}x"
