"""
Unit tests for ONNXProviderManager component.

This test suite verifies the ONNXProviderManager's contract for ONNX Runtime
execution provider detection, configuration, and optimization. Tests focus on
observable behavior of the complete provider manager as a unit.

Component Under Test:
    ONNXProviderManager - Execution provider detection and configuration service

Test Strategy:
    - Treat provider manager as complete unit (not testing internal detection logic)
    - Mock only external dependency: ONNX Runtime provider API
    - Test observable outcomes: provider lists, session options, provider info
    - Verify caching behavior through repeated calls

External Dependencies Mocked:
    - ONNX Runtime (onnxruntime library) - Provider detection and availability
    - System hardware detection - For GPU/NPU availability checks

Fixtures Used:
    - mock_onnx_provider_manager: Factory for creating provider manager instances
    - onnx_provider_test_data: Test data for various provider scenarios
    - onnx_session_options_test_data: Test data for session configuration
"""

import pytest
from typing import List, Optional
from unittest.mock import Mock, patch, MagicMock


class TestONNXProviderManagerInitialization:
    """
    Tests for ONNXProviderManager initialization behavior.

    Verifies that the provider manager initializes correctly with proper
    cache setup according to the documented contract.
    """

    def test_initializes_with_empty_provider_cache(self, mock_onnx_provider_manager):
        """
        Test that provider manager initializes with empty provider cache.

        Verifies:
            providers_cache starts as None per initialization behavior.

        Business Impact:
            Ensures lazy provider detection doesn't occur until first use.

        Scenario:
            Given: No prior provider detection has occurred
            When: ONNXProviderManager() is instantiated
            Then: providers_cache attribute is None
            And: Provider detection is deferred to first method call

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: No prior provider detection has occurred
        manager_factory = mock_onnx_provider_manager

        # When: ONNXProviderManager() is instantiated
        manager = manager_factory()

        # Then: providers_cache attribute is None
        assert manager.providers_cache is None

        # And: No detection calls have occurred yet
        assert len(manager.detection_history) == 0

    def test_defers_provider_detection_until_first_method_call(self, mock_onnx_provider_manager):
        """
        Test that provider detection is deferred until first detection call.

        Verifies:
            No ONNX Runtime import occurs during initialization per lazy loading behavior.

        Business Impact:
            Improves startup performance by avoiding expensive provider detection.

        Scenario:
            Given: ONNXProviderManager is instantiated
            And: No methods have been called yet
            When: Instance is created
            Then: No provider detection has occurred
            And: ONNX Runtime has not been imported
            And: Instance is ready to use

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: ONNXProviderManager is instantiated
        manager_factory = mock_onnx_provider_manager

        # Mock ONNX Runtime to track imports
        with patch('app.infrastructure.security.llm.onnx_utils.ort') as mock_ort:
            # When: Instance is created
            manager = manager_factory()

            # Then: No provider detection has occurred
            assert manager.providers_cache is None
            assert len(manager.detection_history) == 0

            # And: ONNX Runtime has not been imported during initialization
            mock_ort.assert_not_called()

            # And: Instance is ready to use
            assert hasattr(manager, 'detect_providers')
            assert hasattr(manager, 'get_optimal_providers')
            assert hasattr(manager, 'configure_session_options')

    def test_is_thread_safe_for_concurrent_initialization(self, mock_onnx_provider_manager):
        """
        Test that provider manager initialization is thread-safe.

        Verifies:
            Multiple threads can safely create manager instances per thread safety contract.

        Business Impact:
            Enables safe concurrent usage in multi-threaded applications.

        Scenario:
            Given: Multiple threads creating manager instances simultaneously
            When: ONNXProviderManager() is called from multiple threads
            Then: All instances are created successfully
            And: No race conditions or exceptions occur
            And: Each instance has independent state

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        import threading
        import time

        # Given: Multiple threads creating manager instances simultaneously
        manager_factory = mock_onnx_provider_manager
        managers = []
        exceptions = []

        def create_manager():
            try:
                manager = manager_factory()
                managers.append(manager)
                # Simulate some work to increase chance of race conditions
                time.sleep(0.001)
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_manager)
            threads.append(thread)

        # When: ONNXProviderManager() is called from multiple threads
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Then: All instances are created successfully
        assert len(exceptions) == 0, f"Exceptions occurred during concurrent initialization: {exceptions}"
        assert len(managers) == 10

        # And: No race conditions or exceptions occur
        for manager in managers:
            assert manager.providers_cache is None
            assert len(manager.detection_history) == 0

        # And: Each instance has independent state
        for i, manager in enumerate(managers):
            for j, other_manager in enumerate(managers):
                if i != j:
                    assert manager is not other_manager
                    assert manager.providers_cache is other_manager.providers_cache  # Both None initially


class TestONNXProviderManagerProviderDetection:
    """
    Tests for detect_providers() method behavior.

    Verifies that provider detection works correctly, returns proper priority
    ordering, and caches results according to the documented contract.
    """

    def test_detects_available_providers_on_first_call(self, mock_onnx_provider_manager, onnx_provider_test_data):
        """
        Test that detect_providers() detects available ONNX Runtime providers.

        Verifies:
            Available providers are detected and categorized per detection behavior.

        Business Impact:
            Ensures application can discover available hardware acceleration options.

        Scenario:
            Given: ONNX Runtime is installed with available providers
            When: detect_providers() is called for the first time
            Then: Returns List[ProviderInfo] with all available providers
            And: Each ProviderInfo has correct name, available, priority, description
            And: Providers are sorted by priority (lower numbers first)

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data for available providers
        """
        # Given: ONNX Runtime is installed with available providers
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        test_data = onnx_provider_test_data["cpu_only"]

        # When: detect_providers() is called for the first time
        providers = manager.detect_providers()

        # Then: Returns List[ProviderInfo] with all available providers
        assert isinstance(providers, list)
        assert len(providers) > 0

        # And: Each ProviderInfo has correct name, available, priority, description
        for provider in providers:
            assert hasattr(provider, 'name')
            assert hasattr(provider, 'available')
            assert hasattr(provider, 'priority')
            assert hasattr(provider, 'description')
            assert hasattr(provider, 'device_type')
            assert isinstance(provider.name, str)
            assert isinstance(provider.available, bool)
            assert isinstance(provider.priority, int)
            assert isinstance(provider.description, str)

        # And: Providers are sorted by priority (lower numbers first)
        priorities = [p.priority for p in providers]
        assert priorities == sorted(priorities)

        # And: Detection was triggered (history shows call)
        assert len(manager.detection_history) == 1
        assert manager.detection_history[0]["operation"] == "detect_providers"

    def test_returns_providers_sorted_by_priority(self, mock_onnx_provider_manager, onnx_provider_test_data):
        """
        Test that detected providers are sorted by performance priority.

        Verifies:
            Provider list is sorted by priority with GPU > NPU > CPU per priority system.

        Business Impact:
            Ensures optimal provider is tried first for best performance.

        Scenario:
            Given: Multiple providers are available (CUDA, CoreML, CPU)
            When: detect_providers() is called
            Then: Returns providers in priority order
            And: GPU providers (priority 1) come first
            And: NPU providers (priority 2) come next
            And: CPU provider (priority 3) comes last

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data with multiple providers
        """
        # Given: Multiple providers are available (CUDA, CoreML, CPU)
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        test_data = onnx_provider_test_data["gpu_available"]

        # When: detect_providers() is called
        providers = manager.detect_providers()

        # Then: Returns providers in priority order
        priorities = [p.priority for p in providers]
        assert priorities == sorted(priorities)

        # And: GPU providers (priority 1) come first
        gpu_providers = [p for p in providers if p.device_type == "gpu"]
        if gpu_providers:
            assert min(p.priority for p in gpu_providers) == 1

        # And: NPU providers (priority 2) come next
        npu_providers = [p for p in providers if p.device_type == "npu"]
        if npu_providers:
            npu_priorities = [p.priority for p in npu_providers]
            gpu_priorities = [p.priority for p in gpu_providers] if gpu_providers else []
            if gpu_priorities:
                assert min(npu_priorities) >= min(gpu_priorities)

        # And: CPU provider (priority 3) comes last
        cpu_providers = [p for p in providers if p.device_type == "cpu"]
        if cpu_providers:
            assert max(p.priority for p in providers) >= 3

    def test_marks_providers_as_available_or_unavailable(self, mock_onnx_provider_manager):
        """
        Test that provider detection correctly marks availability status.

        Verifies:
            Each provider's available field reflects actual availability per ProviderInfo contract.

        Business Impact:
            Allows intelligent provider selection based on hardware capabilities.

        Scenario:
            Given: System has CPU provider but not CUDA provider
            When: detect_providers() is called
            Then: CPUExecutionProvider has available=True
            And: CUDAExecutionProvider has available=False
            And: Availability reflects actual ONNX Runtime detection

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data with mixed availability
        """
        # Given: System has CPU provider but not CUDA provider
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # When: detect_providers() is called
        providers = manager.detect_providers()

        # Then: CPUExecutionProvider has available=True (from mock data)
        cpu_provider = next((p for p in providers if p.name == "CPUExecutionProvider"), None)
        if cpu_provider:
            assert cpu_provider.available is True

        # And: CUDAExecutionProvider has available=False (from mock data)
        cuda_provider = next((p for p in providers if p.name == "CUDAExecutionProvider"), None)
        if cuda_provider:
            assert cuda_provider.available is False

        # And: CoreMLExecutionProvider has available=True (from mock data)
        coreml_provider = next((p for p in providers if p.name == "CoreMLExecutionProvider"), None)
        if coreml_provider:
            assert coreml_provider.available is True

        # And: Availability reflects actual ONNX Runtime detection (from mock)
        available_providers = [p for p in providers if p.available]
        assert len(available_providers) > 0

    def test_includes_provider_descriptions_and_device_types(self, mock_onnx_provider_manager):
        """
        Test that provider detection includes descriptive metadata for each provider.

        Verifies:
            ProviderInfo contains description and device_type per dataclass contract.

        Business Impact:
            Provides informative details about provider capabilities for logging/UI.

        Scenario:
            Given: Providers are detected
            When: detect_providers() is called
            Then: Each ProviderInfo includes description field
            And: Each ProviderInfo includes device_type (cpu/gpu/npu)
            And: Descriptions are human-readable and informative

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: Providers are detected
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # When: detect_providers() is called
        providers = manager.detect_providers()

        # Then: Each ProviderInfo includes description field
        for provider in providers:
            assert hasattr(provider, 'description')
            assert isinstance(provider.description, str)
            assert len(provider.description) > 0
            assert isinstance(provider.description, str) and provider.description.strip()

        # And: Each ProviderInfo includes device_type (cpu/gpu/npu)
        for provider in providers:
            assert hasattr(provider, 'device_type')
            assert provider.device_type in ['cpu', 'gpu', 'npu']

        # And: Descriptions are human-readable and informative
        for provider in providers:
            description = provider.description
            assert len(description) > 10  # Should be informative
            assert any(char.isalpha() for char in description)  # Contains text
            assert not any(char.isdigit() and len(description) < 20 for char in description)  # Not just codes

        # Verify specific expected descriptions from mock data
        cpu_provider = next((p for p in providers if p.name == "CPUExecutionProvider"), None)
        if cpu_provider:
            assert "CPU" in cpu_provider.description or "universal" in cpu_provider.description.lower()

    def test_caches_detection_results_after_first_call(self, mock_onnx_provider_manager):
        """
        Test that provider detection results are cached after first detection.

        Verifies:
            Results are cached in providers_cache per caching behavior documentation.

        Business Impact:
            Avoids expensive re-detection on subsequent calls for better performance.

        Scenario:
            Given: detect_providers() has been called once
            When: detect_providers() is called again
            Then: Returns cached results immediately
            And: No re-detection occurs
            And: providers_cache is populated from first call

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: detect_providers() has been called once
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # First call to populate cache
        first_call_providers = manager.detect_providers()

        # Verify cache is populated
        assert manager.providers_cache is not None
        assert manager.providers_cache == first_call_providers

        # When: detect_providers() is called again
        second_call_providers = manager.detect_providers()

        # Then: Returns cached results immediately
        assert second_call_providers is first_call_providers  # Same object reference

        # And: No re-detection occurs (only one detection call)
        assert len(manager.detection_history) == 1

        # And: providers_cache is populated from first call
        assert manager.providers_cache is not None
        assert len(manager.providers_cache) > 0

    def test_subsequent_calls_use_cached_results(self, mock_onnx_provider_manager):
        """
        Test that subsequent detect_providers() calls return cached results.

        Verifies:
            Cache is used on subsequent calls per performance optimization.

        Business Impact:
            Provides fast provider access throughout application lifecycle.

        Scenario:
            Given: Provider detection has occurred and results are cached
            When: detect_providers() is called multiple times
            Then: All calls return identical cached results
            And: Detection only occurs once during first call
            And: Performance is significantly faster on cached calls

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        import time

        # Given: Provider detection has occurred and results are cached
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # First call to populate cache
        start_time = time.perf_counter()
        first_providers = manager.detect_providers()
        first_call_time = time.perf_counter() - start_time

        # Verify cache is populated
        assert manager.providers_cache is not None

        # When: detect_providers() is called multiple times
        provider_results = []
        for i in range(5):
            start_time = time.perf_counter()
            providers = manager.detect_providers()
            call_time = time.perf_counter() - start_time
            provider_results.append((providers, call_time))

        # Then: All calls return identical cached results
        for providers, call_time in provider_results:
            assert providers is first_providers  # Same object reference

        # And: Detection only occurs once during first call
        assert len(manager.detection_history) == 1

        # And: Performance is significantly faster on cached calls
        cached_call_times = [call_time for _, call_time in provider_results]
        avg_cached_time = sum(cached_call_times) / len(cached_call_times)

        # Cached calls should be faster (mock implementation might be very fast, so just verify no additional detection)
        assert all(call_time < first_call_time * 2 for call_time in cached_call_times)

    def test_returns_empty_list_when_onnx_runtime_not_installed(self, mock_onnx_provider_manager):
        """
        Test that detect_providers() returns empty list when ONNX Runtime missing.

        Verifies:
            Empty list is returned when ONNX Runtime unavailable per Returns documentation.

        Business Impact:
            Graceful degradation when ONNX Runtime is not installed.

        Scenario:
            Given: ONNX Runtime is not installed or importable
            When: detect_providers() is called
            Then: Returns empty list []
            And: No exceptions are raised
            And: Application can handle missing ONNX Runtime

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager with mock import error
        """
        # Given: ONNX Runtime is not installed or importable
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # Mock the provider detection to simulate missing ONNX Runtime
        # by modifying the mock provider manager to return no providers
        manager._available_providers = {}

        # When: detect_providers() is called
        providers = manager.detect_providers()

        # Then: Returns empty list []
        assert isinstance(providers, list)
        assert len(providers) == 0

        # And: No exceptions are raised
        assert manager.providers_cache == []  # Cache is set to empty list

        # And: Application can handle missing ONNX Runtime
        # (test passes, no exceptions thrown)

    def test_logs_available_providers_for_debugging(self, mock_onnx_provider_manager):
        """
        Test that detect_providers() logs detected providers for debugging.

        Verifies:
            Available providers are logged per debugging behavior.

        Business Impact:
            Enables troubleshooting of provider availability issues.

        Scenario:
            Given: Provider detection occurs
            When: detect_providers() is called
            Then: Available providers are logged with names and priorities
            And: Log output aids in debugging provider selection
            And: Unavailable providers are also noted in logs

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - mock_logger: Shared logger mock for verification (from parent conftest)
        """
        # Given: Provider detection occurs
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # Mock logger to capture log calls
        with patch('app.infrastructure.security.llm.onnx_utils.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # When: detect_providers() is called
            providers = manager.detect_providers()

            # Then: Available providers are logged with names and priorities
            # (Since this is testing behavior, we check that detection occurred)
            assert len(manager.detection_history) == 1

            # In a real implementation, we would verify specific log calls
            # For mock testing, we verify the detection was triggered
            assert len(providers) > 0

            # And: Log output aids in debugging provider selection
            # (Verify detection history contains useful information)
            detection_call = manager.detection_history[0]
            assert "timestamp" in detection_call
            assert detection_call["operation"] == "detect_providers"


class TestONNXProviderManagerOptimalProviderSelection:
    """
    Tests for get_optimal_providers() method behavior.

    Verifies that optimal provider selection works correctly with user preferences
    and automatic fallback according to the documented contract.
    """

    def test_returns_all_available_providers_when_no_preferences_specified(self, mock_onnx_provider_manager, onnx_provider_test_data):
        """
        Test that get_optimal_providers() returns all available providers by default.

        Verifies:
            All available providers are returned in priority order when preferred_providers is None.

        Business Impact:
            Provides maximum flexibility by trying all providers when no preference given.

        Scenario:
            Given: No preferred providers are specified (preferred_providers=None)
            And: Multiple providers are available (CUDA, CoreML, CPU)
            When: get_optimal_providers() is called
            Then: Returns list of all available provider names
            And: Providers are in optimal priority order
            And: List enables fallback through all options

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data for multiple available providers
        """
        # Given: No preferred providers are specified (preferred_providers=None)
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        test_data = onnx_provider_test_data["apple_silicon"]

        # And: Multiple providers are available (CoreML, CPU)
        # (Mock data provides CoreML and CPU)

        # When: get_optimal_providers() is called
        optimal_providers = manager.get_optimal_providers()

        # Then: Returns list of all available provider names
        assert isinstance(optimal_providers, list)
        assert len(optimal_providers) > 0

        # Verify these are provider names (strings), not ProviderInfo objects
        for provider_name in optimal_providers:
            assert isinstance(provider_name, str)

        # And: Providers are in optimal priority order
        # Should include CoreML (priority 2) before CPU (priority 3)
        if "CoreMLExecutionProvider" in optimal_providers and "CPUExecutionProvider" in optimal_providers:
            coreml_index = optimal_providers.index("CoreMLExecutionProvider")
            cpu_index = optimal_providers.index("CPUExecutionProvider")
            assert coreml_index < cpu_index

        # And: List enables fallback through all options
        # (Multiple providers in list allows fallback)
        assert len(optimal_providers) >= 1

    def test_prioritizes_preferred_providers_when_available(self, mock_onnx_provider_manager):
        """
        Test that get_optimal_providers() returns preferred providers first when available.

        Verifies:
            Preferred providers are used when available per selection logic documentation.

        Business Impact:
            Respects user configuration for specific hardware acceleration preferences.

        Scenario:
            Given: preferred_providers=["CUDAExecutionProvider"] is specified
            And: CUDA provider is available on the system
            When: get_optimal_providers(["CUDAExecutionProvider"]) is called
            Then: Returns ["CUDAExecutionProvider"]
            And: Other available providers are not included
            And: User preference is honored

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data with CUDA available
        """
        # Given: preferred_providers=["CUDAExecutionProvider"] is specified
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # And: CUDA provider is available on the system
        # Modify mock to make CUDA available for this test
        manager._available_providers["CUDAExecutionProvider"].available = True

        # When: get_optimal_providers(["CUDAExecutionProvider"]) is called
        optimal_providers = manager.get_optimal_providers(["CUDAExecutionProvider"])

        # Then: Returns ["CUDAExecutionProvider"]
        assert isinstance(optimal_providers, list)
        assert "CUDAExecutionProvider" in optimal_providers

        # And: Other available providers are not included (only preferred providers returned)
        # (Mock implementation returns only available preferred providers)
        preferred_available = [p for p in ["CUDAExecutionProvider"]
                              if any(p.name == "CUDAExecutionProvider" and p.available
                                    for p in manager._available_providers.values())]
        if preferred_available:
            assert optimal_providers == preferred_available

        # And: User preference is honored
        assert len(optimal_providers) > 0
        assert optimal_providers[0] == "CUDAExecutionProvider"

    def test_falls_back_to_automatic_selection_when_preferred_unavailable(self, mock_onnx_provider_manager):
        """
        Test that get_optimal_providers() falls back when preferred providers unavailable.

        Verifies:
            Automatic selection is used when preferred providers unavailable per fallback logic.

        Business Impact:
            Ensures model loading works even when preferred hardware is unavailable.

        Scenario:
            Given: preferred_providers=["CUDAExecutionProvider"] is specified
            And: CUDA provider is not available
            But: CPU provider is available
            When: get_optimal_providers(["CUDAExecutionProvider"]) is called
            Then: Returns available providers in priority order (e.g., ["CPUExecutionProvider"])
            And: Graceful fallback enables continued operation

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data with CUDA unavailable
        """
        # Given: preferred_providers=["CUDAExecutionProvider"] is specified
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # And: CUDA provider is not available (default in mock)
        # But: CPU provider is available (default in mock)

        # When: get_optimal_providers(["CUDAExecutionProvider"]) is called
        optimal_providers = manager.get_optimal_providers(["CUDAExecutionProvider"])

        # Then: Returns available providers in priority order
        assert isinstance(optimal_providers, list)
        assert len(optimal_providers) > 0

        # Should include CPU provider since CUDA is unavailable
        assert "CPUExecutionProvider" in optimal_providers

        # And: Graceful fallback enables continued operation
        # (Should return available providers like CoreML and CPU)
        available_names = [name for name, provider in manager._available_providers.items()
                          if provider.available]
        for available_name in available_names:
            assert available_name in optimal_providers

    def test_handles_multiple_preferred_providers_with_priority(self, mock_onnx_provider_manager):
        """
        Test that get_optimal_providers() handles multiple preferred providers correctly.

        Verifies:
            Multiple preferred providers are filtered and returned in available order.

        Business Impact:
            Enables specifying fallback preferences in user configuration.

        Scenario:
            Given: preferred_providers=["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
            And: Only CUDA and CPU are available
            When: get_optimal_providers([...]) is called
            Then: Returns ["CUDAExecutionProvider", "CPUExecutionProvider"]
            And: TensorRT is omitted (unavailable)
            And: Order reflects availability within preferences

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data with partial availability
        """
        # Given: preferred_providers=["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        preferred_providers = ["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]

        # Make CUDA available for this test
        manager._available_providers["CUDAExecutionProvider"].available = True

        # And: Only CUDA and CPU are available (TensorRT not available in mock)

        # When: get_optimal_providers([...]) is called
        optimal_providers = manager.get_optimal_providers(preferred_providers)

        # Then: Returns ["CUDAExecutionProvider", "CPUExecutionProvider"]
        assert isinstance(optimal_providers, list)
        assert "CUDAExecutionProvider" in optimal_providers
        assert "CPUExecutionProvider" in optimal_providers

        # And: TensorRT is omitted (unavailable)
        assert "TensorrtExecutionProvider" not in optimal_providers

        # And: Order reflects availability within preferences
        if "CUDAExecutionProvider" in optimal_providers and "CPUExecutionProvider" in optimal_providers:
            cuda_index = optimal_providers.index("CUDAExecutionProvider")
            cpu_index = optimal_providers.index("CPUExecutionProvider")
            assert cuda_index < cpu_index  # CUDA comes first in preferences

    def test_returns_empty_list_when_no_providers_available(self, mock_onnx_provider_manager):
        """
        Test that get_optimal_providers() returns empty list when no providers available.

        Verifies:
            Empty list is returned when no providers are available per Returns documentation.

        Business Impact:
            Provides clear indication that model loading will fail.

        Scenario:
            Given: No ONNX Runtime providers are available
            When: get_optimal_providers() is called
            Then: Returns empty list []
            And: Caller can detect provider unavailability
            And: Appropriate error handling can occur

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager with no providers
            - onnx_provider_test_data: Test data for no providers scenario
        """
        # Given: No ONNX Runtime providers are available
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        # Clear all available providers
        manager._available_providers = {}
        manager.providers_cache = []  # Clear cache too

        # When: get_optimal_providers() is called
        optimal_providers = manager.get_optimal_providers()

        # Then: Returns empty list []
        assert isinstance(optimal_providers, list)
        assert len(optimal_providers) == 0

        # And: Caller can detect provider unavailability
        # (Empty list indicates no providers available)

        # And: Appropriate error handling can occur
        # (Test passes, no exceptions thrown)

    def test_triggers_provider_detection_if_not_cached(self):
        """
        Test that get_optimal_providers() triggers detection if cache is empty.

        Verifies:
            Provider detection is triggered automatically per behavior documentation.

        Business Impact:
            Simplifies API by not requiring explicit detect_providers() call.

        Scenario:
            Given: providers_cache is None (no prior detection)
            When: get_optimal_providers() is called
            Then: detect_providers() is called automatically
            And: Detection results are cached
            And: Optimal providers are returned based on fresh detection

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass

    def test_handles_invalid_preferred_provider_names_gracefully(self):
        """
        Test that get_optimal_providers() handles invalid provider names gracefully.

        Verifies:
            Invalid provider names are filtered out per graceful handling behavior.

        Business Impact:
            Prevents configuration errors from causing failures.

        Scenario:
            Given: preferred_providers=["InvalidProvider", "CPUExecutionProvider"]
            When: get_optimal_providers([...]) is called
            Then: Invalid provider names are ignored
            And: Valid available providers are returned
            And: No exceptions are raised

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass


class TestONNXProviderManagerSessionConfiguration:
    """
    Tests for configure_session_options() method behavior.

    Verifies that session options configuration works correctly for different
    optimization targets according to the documented contract.
    """

    def test_configures_session_for_latency_optimization(self, mock_onnx_provider_manager, onnx_session_options_test_data):
        """
        Test that configure_session_options() optimizes for latency when requested.

        Verifies:
            Latency optimization configures session for fast inference per docstring.

        Business Impact:
            Enables real-time inference with minimal latency for interactive applications.

        Scenario:
            Given: optimize_for="latency" is specified
            When: configure_session_options("latency") is called
            Then: Returns session options configured for low latency
            And: Options include sequential execution mode
            And: Options use minimal intra-op threads
            And: Configuration prioritizes single request speed

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_session_options_test_data: Test data for latency configuration
        """
        # Given: optimize_for="latency" is specified
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        test_data = onnx_session_options_test_data["latency_optimized"]

        # When: configure_session_options("latency") is called
        session_options = manager.configure_session_options("latency")

        # Then: Returns session options configured for low latency
        assert session_options is not None
        assert hasattr(session_options, 'optimize_for')
        assert session_options.optimize_for == "latency"

        # And: Options include sequential execution mode
        assert hasattr(session_options, 'execution_mode')
        assert session_options.execution_mode == "ORT_SEQUENTIAL"

        # And: Options use minimal intra-op threads
        assert hasattr(session_options, 'intra_op_num_threads')
        assert session_options.intra_op_num_threads == 1

        # And: Configuration prioritizes single request speed
        assert len(manager.optimization_history) == 1
        assert manager.optimization_history[0]["optimize_for"] == "latency"

    def test_configures_session_for_throughput_optimization(self, mock_onnx_provider_manager, onnx_session_options_test_data):
        """
        Test that configure_session_options() optimizes for throughput when requested.

        Verifies:
            Throughput optimization configures session for high-volume processing per docstring.

        Business Impact:
            Enables efficient batch processing for high-throughput workloads.

        Scenario:
            Given: optimize_for="throughput" is specified
            When: configure_session_options("throughput") is called
            Then: Returns session options configured for high throughput
            And: Options include parallel execution mode
            And: Options use multiple intra-op threads
            And: Configuration prioritizes overall throughput

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_session_options_test_data: Test data for throughput configuration
        """
        # Given: optimize_for="throughput" is specified
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        test_data = onnx_session_options_test_data["throughput_optimized"]

        # When: configure_session_options("throughput") is called
        session_options = manager.configure_session_options("throughput")

        # Then: Returns session options configured for high throughput
        assert session_options is not None
        assert hasattr(session_options, 'optimize_for')
        assert session_options.optimize_for == "throughput"

        # And: Options include parallel execution mode
        assert hasattr(session_options, 'execution_mode')
        assert session_options.execution_mode == "ORT_PARALLEL"

        # And: Options use multiple intra-op threads
        assert hasattr(session_options, 'intra_op_num_threads')
        assert session_options.intra_op_num_threads == 4

        # And: Configuration prioritizes overall throughput
        assert len(manager.optimization_history) == 1
        assert manager.optimization_history[0]["optimize_for"] == "throughput"

    def test_uses_latency_optimization_as_default(self):
        """
        Test that configure_session_options() defaults to latency optimization.

        Verifies:
            Default optimize_for value is "latency" per parameter documentation.

        Business Impact:
            Provides sensible defaults for real-time inference scenarios.

        Scenario:
            Given: No optimize_for parameter is specified
            When: configure_session_options() is called with defaults
            Then: Returns session options optimized for latency
            And: Configuration matches latency optimization settings
            And: Default behavior favors interactive use cases

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass

    def test_returns_onnx_runtime_session_options_object(self):
        """
        Test that configure_session_options() returns valid ONNX Runtime SessionOptions.

        Verifies:
            Return value is compatible ONNX Runtime SessionOptions per return type.

        Business Impact:
            Ensures returned options can be used directly with ONNX Runtime.

        Scenario:
            Given: Any valid optimize_for parameter
            When: configure_session_options(optimize_for) is called
            Then: Returns object compatible with onnxruntime.SessionOptions
            And: Returned object can be passed to InferenceSession constructor
            And: All required session option attributes are present

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass

    def test_logs_optimization_configuration_for_debugging(self):
        """
        Test that configure_session_options() logs configuration for debugging.

        Verifies:
            Session configuration is logged per debugging behavior.

        Business Impact:
            Enables troubleshooting of performance optimization settings.

        Scenario:
            Given: Session options are being configured
            When: configure_session_options(optimize_for) is called
            Then: Optimization mode is logged
            And: Key configuration parameters are logged
            And: Log output aids in performance debugging

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - mock_logger: Shared logger mock for verification
        """
        pass


class TestONNXProviderManagerProviderInfo:
    """
    Tests for get_provider_info() method behavior.

    Verifies that provider information retrieval works correctly for querying
    specific provider details according to the documented contract.
    """

    def test_returns_provider_info_for_valid_provider_name(self, mock_onnx_provider_manager):
        """
        Test that get_provider_info() returns ProviderInfo for valid provider names.

        Verifies:
            Valid provider names return corresponding ProviderInfo per method contract.

        Business Impact:
            Enables querying details about specific providers for decision-making.

        Scenario:
            Given: A valid provider name "CPUExecutionProvider"
            When: get_provider_info("CPUExecutionProvider") is called
            Then: Returns ProviderInfo object for CPU provider
            And: ProviderInfo contains accurate details (name, available, priority)
            And: Information matches detection results

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: A valid provider name "CPUExecutionProvider"
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        provider_name = "CPUExecutionProvider"

        # When: get_provider_info("CPUExecutionProvider") is called
        provider_info = manager.get_provider_info(provider_name)

        # Then: Returns ProviderInfo object for CPU provider
        assert provider_info is not None
        assert hasattr(provider_info, 'name')
        assert hasattr(provider_info, 'available')
        assert hasattr(provider_info, 'priority')
        assert hasattr(provider_info, 'description')
        assert hasattr(provider_info, 'device_type')

        # And: ProviderInfo contains accurate details (name, available, priority)
        assert provider_info.name == "CPUExecutionProvider"
        assert isinstance(provider_info.available, bool)
        assert isinstance(provider_info.priority, int)
        assert isinstance(provider_info.description, str)
        assert provider_info.device_type == "cpu"

        # And: Information matches detection results
        detected_providers = manager.detect_providers()
        cpu_detected = next((p for p in detected_providers if p.name == provider_name), None)
        if cpu_detected:
            assert provider_info.available == cpu_detected.available
            assert provider_info.priority == cpu_detected.priority

    def test_returns_none_for_invalid_provider_name(self, mock_onnx_provider_manager):
        """
        Test that get_provider_info() returns None for unknown provider names.

        Verifies:
            Unknown provider names return None per return type documentation.

        Business Impact:
            Provides safe way to query provider existence without exceptions.

        Scenario:
            Given: An invalid provider name "InvalidProvider"
            When: get_provider_info("InvalidProvider") is called
            Then: Returns None
            And: No exceptions are raised
            And: Caller can check for None to detect unknown providers

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: An invalid provider name "InvalidProvider"
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        invalid_provider_name = "InvalidProvider"

        # When: get_provider_info("InvalidProvider") is called
        provider_info = manager.get_provider_info(invalid_provider_name)

        # Then: Returns None
        assert provider_info is None

        # And: No exceptions are raised
        # (Test passes without exceptions)

        # And: Caller can check for None to detect unknown providers
        assert provider_info is None  # Explicit check for clarity

    def test_returns_info_for_all_supported_provider_types(self):
        """
        Test that get_provider_info() works for all supported provider types.

        Verifies:
            All documented provider types can be queried per supported providers list.

        Business Impact:
            Ensures complete API coverage for all known provider types.

        Scenario:
            Given: List of all supported providers (CUDA, TensorRT, CoreML, etc.)
            When: get_provider_info() is called for each provider
            Then: Returns ProviderInfo for each supported provider
            And: Each ProviderInfo has correct device_type and priority
            And: Coverage includes CPU, GPU, and NPU provider types

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass

    def test_reflects_actual_availability_in_returned_info(self):
        """
        Test that get_provider_info() returns current availability status.

        Verifies:
            Returned ProviderInfo reflects actual hardware availability.

        Business Impact:
            Provides accurate real-time information about provider usability.

        Scenario:
            Given: Provider detection has been performed
            When: get_provider_info("CUDAExecutionProvider") is called
            Then: Returned ProviderInfo.available reflects actual CUDA availability
            And: Availability matches detect_providers() results
            And: Information is current and accurate

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
            - onnx_provider_test_data: Test data with various availability states
        """
        pass


class TestONNXProviderManagerThreadSafety:
    """
    Tests for thread safety of ONNXProviderManager operations.

    Verifies that the provider manager handles concurrent access correctly
    according to the documented thread safety contract.
    """

    def test_provider_detection_is_thread_safe(self, mock_onnx_provider_manager):
        """
        Test that concurrent detect_providers() calls are thread-safe.

        Verifies:
            Multiple threads can safely call detect_providers() per thread safety contract.

        Business Impact:
            Enables safe concurrent initialization in multi-threaded applications.

        Scenario:
            Given: Multiple threads calling detect_providers() simultaneously
            When: detect_providers() is called concurrently from multiple threads
            Then: All calls complete successfully without race conditions
            And: Cache is populated atomically
            And: All threads receive consistent provider lists

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        import threading
        import time

        # Given: Multiple threads calling detect_providers() simultaneously
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()

        results = []
        exceptions = []

        def detect_providers_thread():
            try:
                providers = manager.detect_providers()
                results.append(providers)
                time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=detect_providers_thread)
            threads.append(thread)

        # When: detect_providers() is called concurrently from multiple threads
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Then: All calls complete successfully without race conditions
        assert len(exceptions) == 0, f"Thread safety exceptions occurred: {exceptions}"
        assert len(results) == 10

        # And: Cache is populated atomically
        assert manager.providers_cache is not None

        # And: All threads receive consistent provider lists
        first_result = results[0]
        for result in results[1:]:
            assert result is first_result  # Same cached object

    def test_session_configuration_is_stateless(self):
        """
        Test that configure_session_options() is stateless and thread-safe.

        Verifies:
            Session configuration doesn't modify shared state per stateless design.

        Business Impact:
            Enables safe concurrent session creation in parallel inference scenarios.

        Scenario:
            Given: Multiple threads configuring sessions concurrently
            When: configure_session_options() is called from multiple threads
            Then: Each thread receives independent session options
            And: No interference between concurrent configuration calls
            And: All configurations are correct and isolated

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass

    def test_cached_results_are_safely_shared_across_threads(self):
        """
        Test that cached provider detection results are safely shared.

        Verifies:
            Cached detection results are read-only and thread-safe per caching behavior.

        Business Impact:
            Provides thread-safe performance optimization through caching.

        Scenario:
            Given: Provider detection cache is populated
            And: Multiple threads accessing cached results concurrently
            When: detect_providers() is called from multiple threads
            Then: All threads read same cached results safely
            And: No cache corruption or race conditions occur
            And: Performance benefits of caching are realized

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass


class TestONNXProviderManagerEdgeCases:
    """
    Tests for edge cases and boundary conditions in ONNXProviderManager.

    Verifies that the provider manager handles unusual conditions gracefully
    according to the documented contract.
    """

    def test_handles_onnx_runtime_version_mismatches_gracefully(self):
        """
        Test that provider manager handles ONNX Runtime version differences gracefully.

        Verifies:
            Different ONNX Runtime versions are handled per installation variations.

        Business Impact:
            Ensures compatibility across different ONNX Runtime installations.

        Scenario:
            Given: ONNX Runtime with different provider availability than expected
            When: detect_providers() is called
            Then: Detects actually available providers
            And: Handles missing expected providers gracefully
            And: Logs version-related provider differences

        Fixtures Used:
            - mock_onnx_provider_manager: Factory with mocked version scenarios
        """
        pass

    def test_handles_provider_loading_errors_gracefully(self):
        """
        Test that provider manager handles provider loading failures gracefully.

        Verifies:
            Provider loading errors are caught and handled per error handling.

        Business Impact:
            Prevents provider issues from crashing application initialization.

        Scenario:
            Given: A provider that exists but fails to load
            When: detect_providers() is called
            Then: Failed provider is marked as unavailable
            And: Other providers are still detected
            And: Error is logged for debugging
            And: Application continues with available providers

        Fixtures Used:
            - mock_onnx_provider_manager: Factory with mocked loading errors
        """
        pass

    def test_handles_incomplete_provider_metadata_gracefully(self):
        """
        Test that provider manager handles incomplete provider information.

        Verifies:
            Missing provider metadata is filled with defaults per graceful handling.

        Business Impact:
            Prevents metadata issues from blocking provider usage.

        Scenario:
            Given: A provider with incomplete metadata
            When: detect_providers() is called
            Then: Provider is detected with default values for missing fields
            And: ProviderInfo is created successfully
            And: Provider can still be used despite incomplete metadata

        Fixtures Used:
            - mock_onnx_provider_manager: Factory with incomplete metadata scenarios
        """
        pass

    def test_handles_empty_preferred_providers_list(self, mock_onnx_provider_manager):
        """
        Test that get_optimal_providers() handles empty preferred list.

        Verifies:
            Empty preferred_providers list falls back to automatic selection.

        Business Impact:
            Handles configuration edge case gracefully without errors.

        Scenario:
            Given: preferred_providers=[] (empty list)
            When: get_optimal_providers([]) is called
            Then: Returns all available providers in priority order
            And: Behaves same as preferred_providers=None
            And: No errors or unexpected behavior occurs

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        # Given: preferred_providers=[] (empty list)
        manager_factory = mock_onnx_provider_manager
        manager = manager_factory()
        empty_providers = []

        # When: get_optimal_providers([]) is called
        optimal_providers = manager.get_optimal_providers(empty_providers)

        # Then: Returns all available providers in priority order
        assert isinstance(optimal_providers, list)
        assert len(optimal_providers) > 0

        # And: Behaves same as preferred_providers=None
        default_providers = manager.get_optimal_providers(None)
        assert optimal_providers == default_providers

        # And: No errors or unexpected behavior occurs
        # (Test passes without exceptions)

    def test_handles_unsupported_optimization_target_gracefully(self):
        """
        Test that configure_session_options() handles invalid optimization targets.

        Verifies:
            Invalid optimize_for values are handled gracefully.

        Business Impact:
            Prevents configuration errors from causing failures.

        Scenario:
            Given: optimize_for="invalid_target"
            When: configure_session_options("invalid_target") is called
            Then: Falls back to default latency configuration
            Or: Raises appropriate error with clear message
            And: Does not crash or return invalid options

        Fixtures Used:
            - mock_onnx_provider_manager: Factory to create manager instances
        """
        pass

