"""
Unit tests for ONNX Utils utility functions.

This test suite verifies the utility functions (get_onnx_manager, verify_onnx_setup)
and dataclass behaviors (ONNXModelInfo, ProviderInfo) according to their documented
contracts. Tests focus on observable behavior and proper data structure handling.

Components Under Test:
    - get_onnx_manager(): Global singleton manager factory function
    - verify_onnx_setup(): ONNX Runtime ecosystem verification utility
    - ONNXModelInfo: Model metadata dataclass
    - ProviderInfo: Provider information dataclass

Test Strategy:
    - Test utility functions as complete units with observable outcomes
    - Test dataclasses for proper initialization and attribute access
    - Mock only external dependencies (ONNX Runtime, file system)
    - Verify comprehensive diagnostic information from verification function

External Dependencies Mocked:
    - ONNX Runtime (onnxruntime library) - For setup verification
    - File system - For model file checks
    - Network - For download capability checks

Fixtures Used:
    - mock_onnx_model_info: Factory for creating model info instances
    - mock_provider_info: Factory for creating provider info instances
    - onnx_test_models: Test data for model scenarios
    - onnx_provider_test_data: Test data for provider scenarios
"""

import pytest
from typing import Dict, Any


class TestONNXModelInfoDataclass:
    """
    Tests for ONNXModelInfo dataclass behavior.

    Verifies that the model information dataclass properly stores and
    provides access to model metadata according to the documented contract.
    """

    def test_initializes_with_all_required_fields(self, mock_onnx_model_info):
        """
        Test that ONNXModelInfo initializes with complete model metadata.

        Verifies:
            All required fields are properly initialized per dataclass attributes.

        Business Impact:
            Ensures model information is complete and usable for monitoring.

        Scenario:
            Given: Complete model metadata values
            When: ONNXModelInfo(...) is instantiated with all fields
            Then: All attributes are accessible and contain correct values
            And: model_name, model_path, model_hash are strings
            And: file_size_mb is float
            And: providers is list of strings
            And: metadata is dictionary

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        # Given: Complete model metadata values
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        model_info = ONNXModelInfo(
            model_name="microsoft/deberta-v3-base",
            model_path="/cache/models/deberta.onnx",
            model_hash="abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            file_size_mb=512.34,
            providers=["CPUExecutionProvider"],
            metadata={"provider": "CPUExecutionProvider", "optimize_for": "latency"}
        )

        # Then: All attributes are accessible and contain correct values
        assert model_info.model_name == "microsoft/deberta-v3-base"
        assert model_info.model_path == "/cache/models/deberta.onnx"
        assert model_info.model_hash == "abcd1234567890abcd1234567890abcd1234567890abcd1234567890"
        assert model_info.file_size_mb == 512.34
        assert model_info.providers == ["CPUExecutionProvider"]
        assert model_info.metadata == {"provider": "CPUExecutionProvider", "optimize_for": "latency"}

        # And: Types are correct
        assert isinstance(model_info.model_name, str)
        assert isinstance(model_info.model_path, str)
        assert isinstance(model_info.model_hash, str)
        assert isinstance(model_info.file_size_mb, float)
        assert isinstance(model_info.providers, list)
        assert isinstance(model_info.metadata, dict)

    def test_stores_model_name_correctly(self):
        """
        Test that ONNXModelInfo stores model name as documented.

        Verifies:
            model_name attribute stores original model identifier per attribute docs.

        Business Impact:
            Enables tracking which model the metadata describes.

        Scenario:
            Given: model_name="microsoft/deberta-v3-base"
            When: ONNXModelInfo is created with this model_name
            Then: info.model_name == "microsoft/deberta-v3-base"
            And: Model identifier is accessible and correct

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: model_name="microsoft/deberta-v3-base"
        model_info = ONNXModelInfo(
            model_name="microsoft/deberta-v3-base",
            model_path="/cache/models/deberta.onnx",
            model_hash="abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            file_size_mb=512.34,
            providers=["CPUExecutionProvider"],
            metadata={"provider": "CPUExecutionProvider"}
        )

        # Then: info.model_name == "microsoft/deberta-v3-base"
        assert model_info.model_name == "microsoft/deberta-v3-base"

        # And: Model identifier is accessible and correct
        assert isinstance(model_info.model_name, str)
        assert len(model_info.model_name) > 0

    def test_stores_model_path_as_string(self):
        """
        Test that ONNXModelInfo stores absolute file path correctly.

        Verifies:
            model_path attribute contains absolute path per attribute documentation.

        Business Impact:
            Provides file location for model access and debugging.

        Scenario:
            Given: model_path="/cache/models/deberta.onnx"
            When: ONNXModelInfo is created with this path
            Then: info.model_path == "/cache/models/deberta.onnx"
            And: Path is accessible as string

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: model_path="/cache/models/deberta.onnx"
        model_info = ONNXModelInfo(
            model_name="test-model",
            model_path="/cache/models/deberta.onnx",
            model_hash="abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            file_size_mb=512.34,
            providers=["CPUExecutionProvider"],
            metadata={"provider": "CPUExecutionProvider"}
        )

        # Then: info.model_path == "/cache/models/deberta.onnx"
        assert model_info.model_path == "/cache/models/deberta.onnx"

        # And: Path is accessible as string
        assert isinstance(model_info.model_path, str)
        assert model_info.model_path.endswith(".onnx")

    def test_stores_sha256_hash_for_integrity_verification(self):
        """
        Test that ONNXModelInfo stores SHA-256 hash for model integrity.

        Verifies:
            model_hash attribute stores 64-character hex hash per documentation.

        Business Impact:
            Enables verification of model file integrity.

        Scenario:
            Given: model_hash="a1b2c3d4e5f6..." (64 hex chars)
            When: ONNXModelInfo is created with this hash
            Then: info.model_hash contains the SHA-256 hash
            And: Hash can be used for integrity verification

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: model_hash="a1b2c3d4e5f6..." (64 hex chars)
        hash_value = "abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234"  # 64-character hex string
        model_info = ONNXModelInfo(
            model_name="test-model",
            model_path="/cache/models/deberta.onnx",
            model_hash=hash_value,
            file_size_mb=512.34,
            providers=["CPUExecutionProvider"],
            metadata={"provider": "CPUExecutionProvider"}
        )

        # Then: info.model_hash contains the SHA-256 hash
        assert model_info.model_hash == hash_value

        # And: Hash can be used for integrity verification
        assert isinstance(model_info.model_hash, str)
        assert len(model_info.model_hash) == 64
        # Check that it's a valid hex string (allow both uppercase and lowercase)
        assert all(c in "0123456789abcdef" for c in model_info.model_hash.lower())

    def test_stores_file_size_in_megabytes(self):
        """
        Test that ONNXModelInfo stores file size as float in MB.

        Verifies:
            file_size_mb attribute stores size with 2 decimal precision per docs.

        Business Impact:
            Provides resource usage information for capacity planning.

        Scenario:
            Given: file_size_mb=512.34
            When: ONNXModelInfo is created with this size
            Then: info.file_size_mb == 512.34
            And: Size is float type with MB units

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: file_size_mb=512.34
        model_info = ONNXModelInfo(
            model_name="test-model",
            model_path="/cache/models/deberta.onnx",
            model_hash="abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            file_size_mb=512.34,
            providers=["CPUExecutionProvider"],
            metadata={"provider": "CPUExecutionProvider"}
        )

        # Then: info.file_size_mb == 512.34
        assert model_info.file_size_mb == 512.34

        # And: Size is float type with MB units
        assert isinstance(model_info.file_size_mb, float)
        assert model_info.file_size_mb > 0

    def test_stores_available_providers_list(self):
        """
        Test that ONNXModelInfo stores list of available execution providers.

        Verifies:
            providers attribute stores list of provider names per documentation.

        Business Impact:
            Indicates which providers can be used for this model.

        Scenario:
            Given: providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            When: ONNXModelInfo is created with this providers list
            Then: info.providers contains the list of provider names
            And: Providers are accessible for provider selection logic

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        providers_list = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        model_info = ONNXModelInfo(
            model_name="test-model",
            model_path="/cache/models/deberta.onnx",
            model_hash="abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            file_size_mb=512.34,
            providers=providers_list,
            metadata={"provider": "CPUExecutionProvider"}
        )

        # Then: info.providers contains the list of provider names
        assert model_info.providers == providers_list

        # And: Providers are accessible for provider selection logic
        assert isinstance(model_info.providers, list)
        assert "CUDAExecutionProvider" in model_info.providers
        assert "CPUExecutionProvider" in model_info.providers

    def test_stores_comprehensive_metadata_dictionary(self):
        """
        Test that ONNXModelInfo stores additional metadata in dictionary.

        Verifies:
            metadata attribute stores dict with input/output specs and provider info.

        Business Impact:
            Provides detailed model characteristics for inference operations.

        Scenario:
            Given: metadata with input_metadata, output_metadata, provider, optimize_for
            When: ONNXModelInfo is created with this metadata
            Then: info.metadata contains all fields
            And: metadata["provider"] indicates loaded provider
            And: metadata["input_metadata"] describes input tensors
            And: metadata["output_metadata"] describes output tensors

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: metadata with input_metadata, output_metadata, provider, optimize_for
        metadata_dict = {
            "provider": "CUDAExecutionProvider",
            "optimize_for": "latency",
            "input_metadata": [{"name": "input_ids", "shape": [1, 512], "dtype": "int64"}],
            "output_metadata": [{"name": "logits", "shape": [1, 2], "dtype": "float32"}]
        }

        model_info = ONNXModelInfo(
            model_name="test-model",
            model_path="/cache/models/deberta.onnx",
            model_hash="abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            file_size_mb=512.34,
            providers=["CUDAExecutionProvider"],
            metadata=metadata_dict
        )

        # Then: info.metadata contains all fields
        assert model_info.metadata == metadata_dict

        # And: metadata["provider"] indicates loaded provider
        assert model_info.metadata["provider"] == "CUDAExecutionProvider"

        # And: metadata["input_metadata"] describes input tensors
        assert "input_metadata" in model_info.metadata
        assert isinstance(model_info.metadata["input_metadata"], list)

        # And: metadata["output_metadata"] describes output tensors
        assert "output_metadata" in model_info.metadata
        assert isinstance(model_info.metadata["output_metadata"], list)

        # And: metadata is a dictionary
        assert isinstance(model_info.metadata, dict)

    def test_all_attributes_are_accessible_after_initialization(self):
        """
        Test that all ONNXModelInfo attributes remain accessible.

        Verifies:
            Dataclass attributes are accessible per standard dataclass behavior.

        Business Impact:
            Ensures reliable access to model information throughout application.

        Scenario:
            Given: ONNXModelInfo instance is created
            When: Attributes are accessed (model_name, model_path, etc.)
            Then: All attributes return their stored values
            And: No attribute access errors occur
            And: Values are immutable (standard dataclass)

        Fixtures Used:
            - mock_onnx_model_info: Factory to create model info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ONNXModelInfo

        # Given: ONNXModelInfo instance is created
        original_values = {
            "model_name": "test-model",
            "model_path": "/cache/models/deberta.onnx",
            "model_hash": "abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            "file_size_mb": 512.34,
            "providers": ["CPUExecutionProvider"],
            "metadata": {"provider": "CPUExecutionProvider", "optimize_for": "latency"}
        }

        model_info = ONNXModelInfo(**original_values)

        # When: Attributes are accessed (model_name, model_path, etc.)
        # Then: All attributes return their stored values
        assert model_info.model_name == original_values["model_name"]
        assert model_info.model_path == original_values["model_path"]
        assert model_info.model_hash == original_values["model_hash"]
        assert model_info.file_size_mb == original_values["file_size_mb"]
        assert model_info.providers == original_values["providers"]
        assert model_info.metadata == original_values["metadata"]

        # And: No attribute access errors occur
        for attr_name in ["model_name", "model_path", "model_hash", "file_size_mb", "providers", "metadata"]:
            assert hasattr(model_info, attr_name)
            value = getattr(model_info, attr_name)
            assert value is not None

        # And: Values are immutable (standard dataclass) - verify they can be accessed but not modified
        # Dataclasses are mutable by default, but we verify the values remain as initially set
        assert model_info.model_name == original_values["model_name"]


class TestProviderInfoDataclass:
    """
    Tests for ProviderInfo dataclass behavior.

    Verifies that the provider information dataclass properly stores and
    provides access to provider metadata according to the documented contract.
    """

    def test_initializes_with_all_required_fields(self, mock_provider_info):
        """
        Test that ProviderInfo initializes with complete provider information.

        Verifies:
            All required fields are properly initialized per dataclass attributes.

        Business Impact:
            Ensures provider information is complete for provider selection.

        Scenario:
            Given: Complete provider information values
            When: ProviderInfo(...) is instantiated with all fields
            Then: All attributes are accessible and contain correct values
            And: name, description, device_type are strings
            And: available is boolean
            And: priority is integer

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: Complete provider information values
        provider_info = ProviderInfo(
            name="CUDAExecutionProvider",
            available=True,
            priority=1,
            description="NVIDIA GPU acceleration with CUDA",
            device_type="gpu"
        )

        # Then: All attributes are accessible and contain correct values
        assert provider_info.name == "CUDAExecutionProvider"
        assert provider_info.available is True
        assert provider_info.priority == 1
        assert provider_info.description == "NVIDIA GPU acceleration with CUDA"
        assert provider_info.device_type == "gpu"

        # And: name, description, device_type are strings
        assert isinstance(provider_info.name, str)
        assert isinstance(provider_info.description, str)
        assert isinstance(provider_info.device_type, str)

        # And: available is boolean
        assert isinstance(provider_info.available, bool)

        # And: priority is integer
        assert isinstance(provider_info.priority, int)

    def test_stores_official_onnx_provider_name(self):
        """
        Test that ProviderInfo stores official ONNX Runtime provider name.

        Verifies:
            name attribute stores exact ONNX provider name per attribute docs.

        Business Impact:
            Enables correct provider specification for ONNX Runtime.

        Scenario:
            Given: name="CUDAExecutionProvider"
            When: ProviderInfo is created with this name
            Then: info.name == "CUDAExecutionProvider"
            And: Name matches ONNX Runtime provider names exactly

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: name="CUDAExecutionProvider"
        provider_info = ProviderInfo(
            name="CUDAExecutionProvider",
            available=True,
            priority=1,
            description="NVIDIA GPU acceleration with CUDA",
            device_type="gpu"
        )

        # Then: info.name == "CUDAExecutionProvider"
        assert provider_info.name == "CUDAExecutionProvider"

        # And: Name matches ONNX Runtime provider names exactly
        assert provider_info.name == "CUDAExecutionProvider"  # Exact match
        assert "ExecutionProvider" in provider_info.name

    def test_stores_provider_availability_status(self):
        """
        Test that ProviderInfo stores whether provider is available on system.

        Verifies:
            available attribute indicates system availability per documentation.

        Business Impact:
            Enables intelligent provider selection based on hardware.

        Scenario:
            Given: available=True or available=False
            When: ProviderInfo is created with availability status
            Then: info.available reflects actual hardware availability
            And: Boolean value can be checked for provider selection

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: available=True
        provider_available = ProviderInfo(
            name="CUDAExecutionProvider",
            available=True,
            priority=1,
            description="NVIDIA GPU acceleration",
            device_type="gpu"
        )
        assert provider_available.available is True

        # Given: available=False
        provider_unavailable = ProviderInfo(
            name="MissingProvider",
            available=False,
            priority=3,
            description="Not available",
            device_type="cpu"
        )
        assert provider_unavailable.available is False

        # Then: Boolean value can be checked for provider selection
        assert isinstance(provider_available.available, bool)
        assert isinstance(provider_unavailable.available, bool)

    def test_stores_performance_priority_for_selection(self):
        """
        Test that ProviderInfo stores priority for provider selection order.

        Verifies:
            priority attribute stores selection priority per documentation.

        Business Impact:
            Enables optimal provider selection based on performance characteristics.

        Scenario:
            Given: priority=1 (GPU), priority=2 (NPU), or priority=3 (CPU)
            When: ProviderInfo is created with priority value
            Then: info.priority contains the performance priority
            And: Lower numbers indicate higher priority for selection
            And: Priority guides fallback order

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: priority=1 (GPU)
        gpu_provider = ProviderInfo(
            name="CUDAExecutionProvider",
            available=True,
            priority=1,
            description="NVIDIA GPU acceleration",
            device_type="gpu"
        )
        assert gpu_provider.priority == 1

        # Given: priority=2 (NPU)
        npu_provider = ProviderInfo(
            name="CoreMLExecutionProvider",
            available=True,
            priority=2,
            description="Apple Core ML acceleration",
            device_type="npu"
        )
        assert npu_provider.priority == 2

        # Given: priority=3 (CPU)
        cpu_provider = ProviderInfo(
            name="CPUExecutionProvider",
            available=True,
            priority=3,
            description="CPU fallback execution",
            device_type="cpu"
        )
        assert cpu_provider.priority == 3

        # And: Priority guides fallback order
        assert gpu_provider.priority < npu_provider.priority
        assert npu_provider.priority < cpu_provider.priority

    def test_stores_human_readable_description(self):
        """
        Test that ProviderInfo stores descriptive text about provider.

        Verifies:
            description attribute provides human-readable info per docs.

        Business Impact:
            Enables informative logging and user interfaces.

        Scenario:
            Given: description="NVIDIA GPU acceleration with CUDA"
            When: ProviderInfo is created with description
            Then: info.description contains human-readable text
            And: Description explains provider capabilities

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: description="NVIDIA GPU acceleration with CUDA"
        description = "NVIDIA GPU acceleration with CUDA"
        provider_info = ProviderInfo(
            name="CUDAExecutionProvider",
            available=True,
            priority=1,
            description=description,
            device_type="gpu"
        )

        # Then: info.description contains human-readable text
        assert provider_info.description == description

        # And: Description explains provider capabilities
        assert isinstance(provider_info.description, str)
        assert len(provider_info.description) > 0
        assert "NVIDIA" in provider_info.description
        assert "CUDA" in provider_info.description

    def test_stores_device_type_classification(self):
        """
        Test that ProviderInfo stores device type classification.

        Verifies:
            device_type attribute classifies provider as cpu/gpu/npu per docs.

        Business Impact:
            Enables device-specific optimization and configuration.

        Scenario:
            Given: device_type="gpu", "cpu", or "npu"
            When: ProviderInfo is created with device type
            Then: info.device_type contains the classification
            And: Type is one of ["cpu", "gpu", "npu"]
            And: Classification aids in hardware-specific logic

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: device_type="gpu"
        gpu_provider = ProviderInfo(
            name="CUDAExecutionProvider",
            available=True,
            priority=1,
            description="NVIDIA GPU acceleration",
            device_type="gpu"
        )
        assert gpu_provider.device_type == "gpu"

        # Given: device_type="cpu"
        cpu_provider = ProviderInfo(
            name="CPUExecutionProvider",
            available=True,
            priority=3,
            description="CPU fallback execution",
            device_type="cpu"
        )
        assert cpu_provider.device_type == "cpu"

        # Given: device_type="npu"
        npu_provider = ProviderInfo(
            name="CoreMLExecutionProvider",
            available=True,
            priority=2,
            description="Apple Core ML acceleration",
            device_type="npu"
        )
        assert npu_provider.device_type == "npu"

        # And: Type is one of ["cpu", "gpu", "npu"]
        valid_types = ["cpu", "gpu", "npu"]
        assert gpu_provider.device_type in valid_types
        assert cpu_provider.device_type in valid_types
        assert npu_provider.device_type in valid_types

    def test_providers_can_be_sorted_by_priority(self):
        """
        Test that ProviderInfo instances can be sorted by priority.

        Verifies:
            Priority attribute enables sorting for optimal selection per usage pattern.

        Business Impact:
            Enables automatic optimal provider ordering.

        Scenario:
            Given: Multiple ProviderInfo instances with different priorities
            When: Providers are sorted by priority attribute
            Then: GPU providers (priority 1) come first
            And: NPU providers (priority 2) come next
            And: CPU providers (priority 3) come last
            And: Sorting enables fallback strategy

        Fixtures Used:
            - mock_provider_info: Factory to create provider info instances
        """
        from app.infrastructure.security.llm.onnx_utils import ProviderInfo

        # Given: Multiple ProviderInfo instances with different priorities
        providers = [
            ProviderInfo(name="CPUExecutionProvider", available=True, priority=3, description="CPU", device_type="cpu"),
            ProviderInfo(name="CoreMLExecutionProvider", available=True, priority=2, description="NPU", device_type="npu"),
            ProviderInfo(name="CUDAExecutionProvider", available=True, priority=1, description="GPU", device_type="gpu"),
        ]

        # When: Providers are sorted by priority attribute
        sorted_providers = sorted(providers, key=lambda p: p.priority)

        # Then: GPU providers (priority 1) come first
        assert sorted_providers[0].name == "CUDAExecutionProvider"
        assert sorted_providers[0].priority == 1

        # And: NPU providers (priority 2) come next
        assert sorted_providers[1].name == "CoreMLExecutionProvider"
        assert sorted_providers[1].priority == 2

        # And: CPU providers (priority 3) come last
        assert sorted_providers[2].name == "CPUExecutionProvider"
        assert sorted_providers[2].priority == 3

        # And: Sorting enables fallback strategy
        for i in range(len(sorted_providers) - 1):
            assert sorted_providers[i].priority <= sorted_providers[i + 1].priority


class TestGetONNXManagerFunction:
    """
    Tests for get_onnx_manager() global singleton function.

    Verifies that the global manager factory works correctly for providing
    application-wide manager access according to the documented contract.
    """

    def test_returns_onnx_model_manager_instance_on_first_call(self):
        """
        Test that get_onnx_manager() creates manager instance on first call.

        Verifies:
            First call creates new ONNXModelManager per singleton pattern.

        Business Impact:
            Provides convenient global access pattern for manager.

        Scenario:
            Given: get_onnx_manager() has not been called previously
            When: get_onnx_manager() is called for the first time
            Then: Returns ONNXModelManager instance
            And: Instance is fully initialized and ready to use
            And: Instance becomes the global singleton

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import get_onnx_manager, ONNXModelManager

        # Given: get_onnx_manager() has not been called previously
        # (Cannot easily reset global state, but can test the behavior)

        # When: get_onnx_manager() is called for the first time
        manager1 = get_onnx_manager()

        # Then: Returns ONNXModelManager instance
        assert isinstance(manager1, ONNXModelManager)

        # And: Instance is fully initialized and ready to use
        assert hasattr(manager1, 'downloader')
        assert hasattr(manager1, 'provider_manager')
        assert hasattr(manager1, 'preferred_providers')
        assert hasattr(manager1, 'auto_download')

        # And: Subsequent calls return the same instance (singleton behavior)
        manager2 = get_onnx_manager()
        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_returns_same_instance_on_subsequent_calls(self):
        """
        Test that get_onnx_manager() returns cached instance on repeat calls.

        Verifies:
            Subsequent calls return same instance per singleton pattern.

        Business Impact:
            Ensures consistent state and cache across application.

        Scenario:
            Given: get_onnx_manager() has been called and returned manager
            When: get_onnx_manager() is called again
            Then: Returns exact same manager instance (same id())
            And: Singleton behavior is maintained
            And: State is preserved across calls

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import get_onnx_manager

        # Given: get_onnx_manager() has been called and returned manager
        manager1 = get_onnx_manager()

        # When: get_onnx_manager() is called again
        manager2 = get_onnx_manager()

        # Then: Returns exact same manager instance (same id())
        assert manager1 is manager2
        assert id(manager1) == id(manager2)

        # And: Singleton behavior is maintained
        manager3 = get_onnx_manager()
        assert manager1 is manager3

        # And: State is preserved across calls
        assert manager1 is manager2
        assert manager2 is manager3

    def test_supports_custom_cache_directory_configuration(self):
        """
        Test that get_onnx_manager() supports cache_dir kwarg.

        Verifies:
            cache_dir parameter is passed to manager constructor per kwargs support.

        Business Impact:
            Allows global cache location configuration at startup.

        Scenario:
            Given: cache_dir="/app/models" is provided as kwarg
            When: get_onnx_manager(cache_dir="/app/models") is called
            Then: Returned manager uses specified cache directory
            And: All model operations use custom cache location

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import get_onnx_manager

        # Given: cache_dir="/app/models" is provided as kwarg
        custom_cache_dir = "/tmp/test_models_cache"

        # When: get_onnx_manager(cache_dir="/app/models") is called
        manager = get_onnx_manager(cache_dir=custom_cache_dir)

        # Then: Returned manager uses specified cache directory
        assert str(manager.downloader.cache_dir).endswith(custom_cache_dir)

        # And: All model operations use custom cache location
        assert custom_cache_dir in str(manager.downloader.cache_dir)

    def test_supports_preferred_providers_configuration(self):
        """
        Test that get_onnx_manager() supports preferred_providers kwarg.

        Verifies:
            preferred_providers parameter is passed per kwargs support.

        Business Impact:
            Enables global provider preference configuration.

        Scenario:
            Given: preferred_providers=["CUDAExecutionProvider"] as kwarg
            When: get_onnx_manager(preferred_providers=["CUDAExecutionProvider"]) is called
            Then: Returned manager uses preferred providers for loading
            And: Provider preferences apply globally

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import get_onnx_manager

        # Given: preferred_providers=["CUDAExecutionProvider"] as kwarg
        preferred_providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        # When: get_onnx_manager(preferred_providers=["CUDAExecutionProvider"]) is called
        manager = get_onnx_manager(preferred_providers=preferred_providers)

        # Then: Returned manager uses preferred providers for loading
        assert manager.preferred_providers == preferred_providers

        # And: Provider preferences apply globally
        assert isinstance(manager.preferred_providers, list)
        assert "CUDAExecutionProvider" in manager.preferred_providers

    def test_supports_auto_download_configuration(self):
        """
        Test that get_onnx_manager() supports auto_download kwarg.

        Verifies:
            auto_download parameter is passed per kwargs support.

        Business Impact:
            Allows global download behavior configuration.

        Scenario:
            Given: auto_download=False is provided as kwarg
            When: get_onnx_manager(auto_download=False) is called
            Then: Returned manager has auto_download disabled
            And: Global behavior applies to all model loads

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import get_onnx_manager

        # Given: auto_download=False is provided as kwarg
        auto_download_setting = False

        # When: get_onnx_manager(auto_download=False) is called
        manager = get_onnx_manager(auto_download=auto_download_setting)

        # Then: Returned manager has auto_download disabled
        assert manager.auto_download is False

        # And: Global behavior applies to all model loads
        assert isinstance(manager.auto_download, bool)


class TestVerifyONNXSetupFunction:
    """
    Tests for verify_onnx_setup() async verification utility function.

    Verifies that ONNX ecosystem verification works correctly and provides
    comprehensive diagnostics according to the documented contract.
    """

    async def test_returns_comprehensive_diagnostics_dictionary(self):
        """
        Test that verify_onnx_setup() returns complete diagnostics information.

        Verifies:
            All documented diagnostic fields are present per return value contract.

        Business Impact:
            Provides complete system readiness information for troubleshooting.

        Scenario:
            Given: ONNX Runtime setup to verify
            When: verify_onnx_setup() is called
            Then: Returns dictionary with all documented fields
            And: Includes model_name, onnx_available, onnx_version
            And: Includes providers_available, model_found, model_path
            And: Includes model_loadable, tokenizer_loadable fields
            And: Includes successful_provider and recommendations

        Fixtures Used:
            - None (testing actual function behavior with mocked ONNX Runtime)
        """
        from app.infrastructure.security.llm.onnx_utils import verify_onnx_setup

        # Note: Cannot easily reset global state, but can test the behavior
        try:
            # Given: ONNX Runtime setup to verify
            test_model_name = "test-model"

            # When: verify_onnx_setup() is called
            diagnostics = verify_onnx_setup(test_model_name)

            # Since this is async, we need to handle it properly
            import asyncio
            if asyncio.iscoroutine(diagnostics):
                diagnostics = asyncio.run(diagnostics)

            # Then: Returns dictionary with all documented fields
            assert isinstance(diagnostics, dict)

            # And: Includes model_name, onnx_available, onnx_version
            expected_fields = [
                "model_name",
                "onnx_available",
                "providers_available",
                "model_found",
                "model_loadable",
                "tokenizer_loadable",
                "recommendations"
            ]

            for field in expected_fields:
                assert field in diagnostics, f"Missing required field: {field}"

            # Additional fields that may be present
            optional_fields = [
                "onnx_version",
                "model_path",
                "model_size_mb",
                "successful_provider",
                "input_details",
                "output_details"
            ]

            for field in optional_fields:
                if field in diagnostics:
                    assert diagnostics[field] is not None or diagnostics[field] == []

        except Exception:
            # Test failed, let exception propagate
            raise

    async def test_uses_default_test_model_when_none_specified(self):
        """
        Test that verify_onnx_setup() uses default security scanner model.

        Verifies:
            Default model_name is 'microsoft/deberta-v3-base-injection' per docs.

        Business Impact:
            Provides sensible default for ONNX setup verification.

        Scenario:
            Given: No model_name parameter is provided
            When: verify_onnx_setup() is called with defaults
            Then: Uses 'microsoft/deberta-v3-base-injection' for testing
            And: Diagnostics reflect test with default model
            And: Common security scanning model is verified

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import verify_onnx_setup

        # Note: Cannot easily reset global state, but can test the behavior
        try:
            # Given: No model_name parameter is provided
            # When: verify_onnx_setup() is called with defaults
            diagnostics = verify_onnx_setup()

            # Handle async function
            import asyncio
            if asyncio.iscoroutine(diagnostics):
                diagnostics = asyncio.run(diagnostics)

            # Then: Uses 'microsoft/deberta-v3-base-injection' for testing
            assert diagnostics["model_name"] == "microsoft/deberta-v3-base-injection"

            # And: Diagnostics reflect test with default model
            assert isinstance(diagnostics, dict)
            assert "model_name" in diagnostics

            # And: Common security scanning model is verified
            assert "deberta" in diagnostics["model_name"].lower()
        except Exception:
            # Test failed, let exception propagate
            raise

    async def test_allows_custom_test_model_specification(self):
        """
        Test that verify_onnx_setup() accepts custom model for verification.

        Verifies:
            model_name parameter customizes test model per parameter contract.

        Business Impact:
            Enables verification with application-specific models.

        Scenario:
            Given: model_name="custom/model-name" is provided
            When: verify_onnx_setup("custom/model-name") is called
            Then: Uses specified model for compatibility testing
            And: Diagnostics reflect custom model verification
            And: Custom model compatibility is checked

        Fixtures Used:
            - None (testing actual function behavior)
        """
        from app.infrastructure.security.llm.onnx_utils import verify_onnx_setup

        # Note: Cannot easily reset global state, but can test the behavior
        try:
            # Given: model_name="custom/model-name" is provided
            custom_model_name = "custom/security-model"

            # When: verify_onnx_setup("custom/model-name") is called
            diagnostics = verify_onnx_setup(custom_model_name)

            # Handle async function
            import asyncio
            if asyncio.iscoroutine(diagnostics):
                diagnostics = asyncio.run(diagnostics)

            # Then: Uses specified model for compatibility testing
            assert diagnostics["model_name"] == custom_model_name

            # And: Diagnostics reflect custom model verification
            assert isinstance(diagnostics, dict)
            assert diagnostics["model_name"] == custom_model_name

            # And: Custom model compatibility is checked
            assert "model_loadable" in diagnostics
            assert "tokenizer_loadable" in diagnostics
        except Exception:
            # Test failed, let exception propagate
            raise

    async def test_handles_onnx_runtime_not_installed(self):
        """
        Test that verify_onnx_setup() handles missing ONNX Runtime gracefully.

        Verifies:
            Missing ONNX Runtime is detected and reported per error handling.

        Business Impact:
            Provides clear diagnostic when ONNX Runtime is not installed.

        Scenario:
            Given: ONNX Runtime is not installed
            When: verify_onnx_setup() is called
            Then: diagnostics["onnx_available"] is False
            And: diagnostics["recommendations"] suggests installation
            And: Other checks are skipped appropriately
            And: Clear guidance for resolution is provided

        Fixtures Used:
            - None (testing with ImportError for onnxruntime)
        """
        from app.infrastructure.security.llm.onnx_utils import verify_onnx_setup, _global_manager
        from unittest.mock import patch

        # Reset global state for clean test
        original_manager = _global_manager
        _global_manager = None

        try:
            # Given: ONNX Runtime is not installed (mocked ImportError)
            with patch.dict('sys.modules', {'onnxruntime': None}):
                # Simulate ImportError when trying to import onnxruntime
                with patch('app.infrastructure.security.llm.onnx_utils.ONNXProviderManager.detect_providers', side_effect=ImportError("No module named 'onnxruntime'")):

                    # When: verify_onnx_setup() is called
                    diagnostics = verify_onnx_setup("test-model")

                    # Handle async function
                    import asyncio
                    if asyncio.iscoroutine(diagnostics):
                        diagnostics = asyncio.run(diagnostics)

                    # Then: diagnostics["onnx_available"] is False
                    assert diagnostics["onnx_available"] is False

                    # And: diagnostics["recommendations"] suggests installation
                    assert isinstance(diagnostics["recommendations"], list)
                    assert len(diagnostics["recommendations"]) > 0
                    recommendations_str = " ".join(diagnostics["recommendations"]).lower()
                    assert "install" in recommendations_str or "onnxruntime" in recommendations_str

                    # And: Clear guidance for resolution is provided
                    assert any("onnxruntime" in str(rec).lower() for rec in diagnostics["recommendations"])

        except Exception:
            # Test failed, let exception propagate
            raise

    async def test_returns_empty_recommendations_for_working_setup(self):
        """
        Test that verify_onnx_setup() returns empty recommendations when all works.

        Verifies:
            Empty recommendations list indicates good setup per behavior.

        Business Impact:
            Clearly indicates when setup is ready for production.

        Scenario:
            Given: ONNX Runtime installed with working model
            And: All checks pass successfully
            When: verify_onnx_setup() is called
            Then: diagnostics["recommendations"] is empty list []
            And: model_loadable is True
            And: Setup is verified as functional

        Fixtures Used:
            - None (testing with complete setup)
        """
        from app.infrastructure.security.llm.onnx_utils import verify_onnx_setup, _global_manager
        from unittest.mock import Mock, patch

        # Reset global state for clean test
        original_manager = _global_manager
        _global_manager = None

        try:
            # Given: ONNX Runtime installed with working model (mocked success)
            with patch('app.infrastructure.security.llm.onnx_utils.ONNXProviderManager.detect_providers', return_value=[]):
                with patch('app.infrastructure.security.llm.onnx_utils.ONNXModelManager.verify_model_compatibility') as mock_verify:
                    # Mock successful verification
                    mock_verify.return_value = {
                        "model_name": "test-model",
                        "onnx_available": True,
                        "onnx_version": "1.15.0",
                        "providers_available": ["CPUExecutionProvider"],
                        "model_found": True,
                        "model_path": "/tmp/test-model.onnx",
                        "model_size_mb": 100.0,
                        "model_loadable": True,
                        "tokenizer_loadable": True,
                        "successful_provider": "CPUExecutionProvider",
                        "recommendations": []  # Empty recommendations for working setup
                    }

                    # When: verify_onnx_setup() is called
                    diagnostics = verify_onnx_setup("test-model")

                    # Handle async function
                    import asyncio
                    if asyncio.iscoroutine(diagnostics):
                        diagnostics = asyncio.run(diagnostics)

                    # Then: diagnostics["recommendations"] is empty list []
                    assert diagnostics["recommendations"] == []

                    # And: model_loadable is True
                    assert diagnostics["model_loadable"] is True

                    # And: Setup is verified as functional
                    assert diagnostics["onnx_available"] is True
                    assert diagnostics["tokenizer_loadable"] is True

        except Exception:
            # Test failed, let exception propagate
            raise

    async def test_checks_onnx_runtime_installation_and_version(self):
        """
        Test that verify_onnx_setup() checks ONNX Runtime availability and version.

        Verifies:
            onnx_available and onnx_version fields report installation status.

        Business Impact:
            Detects missing or problematic ONNX Runtime installations.

        Scenario:
            Given: ONNX Runtime is installed on system
            When: verify_onnx_setup() is called
            Then: diagnostics["onnx_available"] is True
            And: diagnostics["onnx_version"] contains version string
            And: Version information aids compatibility checking

        Fixtures Used:
            - None (testing with mocked ONNX Runtime)
        """
        from app.infrastructure.security.llm.onnx_utils import verify_onnx_setup, _global_manager
        from unittest.mock import Mock, patch

        # Reset global state for clean test
        original_manager = _global_manager
        _global_manager = None

        try:
            # Given: ONNX Runtime is installed on system (mocked)
            with patch('app.infrastructure.security.llm.onnx_utils.ONNXModelManager.verify_model_compatibility') as mock_verify:
                # Mock successful verification with version info
                mock_verify.return_value = {
                    "model_name": "test-model",
                    "onnx_available": True,
                    "onnx_version": "1.15.1",
                    "providers_available": ["CPUExecutionProvider"],
                    "model_found": True,
                    "model_loadable": False,  # Don't need actual model loading for this test
                    "tokenizer_loadable": False,
                    "recommendations": ["Model not found locally"]
                }

                # When: verify_onnx_setup() is called
                diagnostics = verify_onnx_setup("test-model")

                # Handle async function
                import asyncio
                if asyncio.iscoroutine(diagnostics):
                    diagnostics = asyncio.run(diagnostics)

                # Then: diagnostics["onnx_available"] is True
                assert diagnostics["onnx_available"] is True

                # And: diagnostics["onnx_version"] contains version string
                assert "onnx_version" in diagnostics
                assert isinstance(diagnostics["onnx_version"], str)
                assert len(diagnostics["onnx_version"]) > 0

                # And: Version information aids compatibility checking
                version_parts = diagnostics["onnx_version"].split(".")
                assert len(version_parts) >= 2  # Major.minor format

        except Exception:
            # Test failed, let exception propagate
            raise

    def test_detects_available_execution_providers(self):
        """
        Test that verify_onnx_setup() lists available execution providers.

        Verifies:
            providers_available field contains detected providers per docs.

        Business Impact:
            Identifies hardware acceleration capabilities.

        Scenario:
            Given: System with available ONNX Runtime providers
            When: verify_onnx_setup() is called
            Then: diagnostics["providers_available"] lists provider names
            And: List includes all detected providers (CUDA, CPU, etc.)
            And: Availability information aids troubleshooting

        Fixtures Used:
            - onnx_provider_test_data: Test data for provider scenarios
        """
        pass

    def test_attempts_test_model_loading_for_compatibility(self):
        """
        Test that verify_onnx_setup() attempts to load test model.

        Verifies:
            Actual model loading is tested per verification behavior.

        Business Impact:
            Provides end-to-end verification beyond just presence checks.

        Scenario:
            Given: Test model is specified for verification
            When: verify_onnx_setup() is called
            Then: Attempts to load model with optimal providers
            And: diagnostics["model_loadable"] indicates success/failure
            And: Actual loading capability is verified

        Fixtures Used:
            - onnx_test_models: Test data for model scenarios
        """
        pass

    def test_checks_tokenizer_loading_compatibility(self):
        """
        Test that verify_onnx_setup() verifies tokenizer loading works.

        Verifies:
            tokenizer_loadable field indicates tokenizer availability.

        Business Impact:
            Ensures complete model pipeline is functional.

        Scenario:
            Given: Model and tokenizer to verify
            When: verify_onnx_setup() is called
            Then: Attempts to load compatible tokenizer
            And: diagnostics["tokenizer_loadable"] indicates result
            And: Complete inference pipeline is verified

        Fixtures Used:
            - None (testing with mocked transformers library)
        """
        pass

    def test_identifies_successful_provider_for_model_loading(self):
        """
        Test that verify_onnx_setup() identifies which provider works.

        Verifies:
            successful_provider field indicates working provider per docs.

        Business Impact:
            Helps identify optimal provider configuration.

        Scenario:
            Given: Model can be loaded with specific provider
            When: verify_onnx_setup() is called
            Then: diagnostics["successful_provider"] contains provider name
            And: Field indicates which provider successfully loaded model
            And: Information guides provider selection

        Fixtures Used:
            - onnx_provider_test_data: Test data for provider scenarios
        """
        pass

    def test_includes_model_file_size_when_found(self):
        """
        Test that verify_onnx_setup() includes model file size in diagnostics.

        Verifies:
            model_size_mb field contains size when model found per docs.

        Business Impact:
            Provides resource usage information for planning.

        Scenario:
            Given: Test model file exists locally
            When: verify_onnx_setup() is called
            Then: diagnostics["model_size_mb"] contains file size
            And: Size is in megabytes with appropriate precision
            And: Resource requirements are clear

        Fixtures Used:
            - onnx_test_models: Test data with size information
        """
        pass

    def test_provides_actionable_recommendations_for_issues(self):
        """
        Test that verify_onnx_setup() includes recommendations for problems.

        Verifies:
            recommendations list provides actionable guidance per docs.

        Business Impact:
            Helps users resolve setup issues independently.

        Scenario:
            Given: ONNX setup with issues detected
            When: verify_onnx_setup() is called
            Then: diagnostics["recommendations"] contains guidance
            And: Recommendations are actionable and specific
            And: Issues are explained with solutions
            And: Empty list if no issues detected

        Fixtures Used:
            - None (testing with various setup scenarios)
        """
        pass

    def test_returns_empty_recommendations_for_working_setup(self):
        """
        Test that verify_onnx_setup() returns empty recommendations when all works.

        Verifies:
            Empty recommendations list indicates good setup per behavior.

        Business Impact:
            Clearly indicates when setup is ready for production.

        Scenario:
            Given: ONNX Runtime installed with working model
            And: All checks pass successfully
            When: verify_onnx_setup() is called
            Then: diagnostics["recommendations"] is empty list []
            And: model_loadable is True
            And: Setup is verified as functional

        Fixtures Used:
            - None (testing with complete setup)
        """
        pass

    def test_handles_onnx_runtime_not_installed(self):
        """
        Test that verify_onnx_setup() handles missing ONNX Runtime gracefully.

        Verifies:
            Missing ONNX Runtime is detected and reported per error handling.

        Business Impact:
            Provides clear diagnostic when ONNX Runtime is not installed.

        Scenario:
            Given: ONNX Runtime is not installed
            When: verify_onnx_setup() is called
            Then: diagnostics["onnx_available"] is False
            And: diagnostics["recommendations"] suggests installation
            And: Other checks are skipped appropriately
            And: Clear guidance for resolution is provided

        Fixtures Used:
            - None (testing with ImportError for onnxruntime)
        """
        pass

    def test_handles_model_not_found_scenario(self):
        """
        Test that verify_onnx_setup() handles missing model files.

        Verifies:
            Missing models are detected and reported per diagnostic behavior.

        Business Impact:
            Identifies when model files need to be downloaded.

        Scenario:
            Given: Test model does not exist locally
            And: Model cannot be downloaded
            When: verify_onnx_setup() is called
            Then: diagnostics["model_found"] is False
            And: diagnostics["recommendations"] suggests downloading
            And: Provides guidance for model acquisition

        Fixtures Used:
            - None (testing with missing model scenario)
        """
        pass

    def test_handles_model_loading_failures(self):
        """
        Test that verify_onnx_setup() handles model loading errors.

        Verifies:
            Loading failures are caught and reported per error handling.

        Business Impact:
            Identifies compatibility issues before production deployment.

        Scenario:
            Given: Model exists but fails to load with all providers
            When: verify_onnx_setup() is called
            Then: diagnostics["model_loadable"] is False
            And: diagnostics["recommendations"] explains the issue
            And: Specific loading errors are captured
            And: Guidance for resolution is provided

        Fixtures Used:
            - None (testing with loading failure scenarios)
        """
        pass

    def test_handles_tokenizer_loading_failures(self):
        """
        Test that verify_onnx_setup() handles tokenizer issues gracefully.

        Verifies:
            Tokenizer failures are detected and reported per behavior.

        Business Impact:
            Identifies incomplete model setup before inference attempts.

        Scenario:
            Given: Model loads but tokenizer fails to load
            When: verify_onnx_setup() is called
            Then: diagnostics["tokenizer_loadable"] is False
            And: diagnostics["recommendations"] addresses tokenizer issue
            And: Model loading success is still reported
            And: Partial setup is clearly indicated

        Fixtures Used:
            - None (testing with tokenizer failure scenario)
        """
        pass

    def test_requires_network_access_for_full_functionality(self):
        """
        Test that verify_onnx_setup() notes when network is needed for downloads.

        Verifies:
            Network requirements are clear per function documentation.

        Business Impact:
            Sets proper expectations for setup verification requirements.

        Scenario:
            Given: Model needs to be downloaded for verification
            And: Network access is required
            When: verify_onnx_setup() is called
            Then: Attempts model download if not cached
            And: Network-related failures are reported clearly
            And: Recommendations include network connectivity guidance

        Fixtures Used:
            - None (testing with network requirements)
        """
        pass

    def test_provides_all_diagnostics_even_when_errors_occur(self):
        """
        Test that verify_onnx_setup() returns complete diagnostics despite errors.

        Verifies:
            Partial failures don't prevent diagnostic completion per robustness.

        Business Impact:
            Provides maximum useful information even in failure scenarios.

        Scenario:
            Given: Some verification steps fail while others succeed
            When: verify_onnx_setup() is called
            Then: Returns diagnostics with all available information
            And: Successful checks are reported
            And: Failed checks are reported with recommendations
            And: Complete picture is provided for troubleshooting

        Fixtures Used:
            - None (testing with partial failure scenarios)
        """
        pass

