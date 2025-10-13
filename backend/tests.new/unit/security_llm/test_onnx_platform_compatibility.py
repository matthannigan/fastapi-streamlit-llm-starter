"""
ONNX Platform Compatibility Tests

This test suite validates ONNX runtime behavior across different platforms
and hardware configurations. It tests model loading, provider selection,
and fallback behavior on various environments.

## Test Coverage

- Platform detection and provider availability
- Model loading on different platforms (macOS, Linux, Windows)
- GPU acceleration when available (CUDA, CoreML, etc.)
- Graceful fallback to CPU when GPU unavailable
- Memory usage and performance validation
- Error handling and recovery scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Generator, Iterator, Any

from app.infrastructure.security.llm.onnx_utils import (
    ONNXModelManager,
    ONNXProviderManager,
    ONNXModelDownloader,
    get_onnx_manager,
    verify_onnx_setup,
)
from app.core.exceptions import InfrastructureError  # type: ignore


class TestONNXPlatformDetection:
    """Test ONNX platform detection and provider availability."""

    @pytest.fixture
    def mock_onnx_available(self) -> Iterator[Mock]:
        """Mock ONNX runtime as available."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
            mock_ort.__version__ = "1.18.0"
            mock_ort.get_available_providers.return_value = [
                "CPUExecutionProvider",
                "CUDAExecutionProvider",
                "CoreMLExecutionProvider"
            ]
            yield mock_ort

    @pytest.fixture
    def mock_onnx_unavailable(self) -> Iterator[Any]:
        """Mock ONNX runtime as unavailable."""
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("No module named 'onnxruntime'")
            yield

    def test_provider_detection_cuda_available(self, mock_onnx_available: Mock) -> None:
        """Test provider detection when CUDA is available."""
        manager = ONNXProviderManager()
        providers = manager.detect_providers()

        assert len(providers) >= 1
        assert any(p.name == "CPUExecutionProvider" for p in providers)
        assert any(p.name == "CUDAExecutionProvider" for p in providers)

        # Check provider info structure
        for provider in providers:
            assert hasattr(provider, "name")
            assert hasattr(provider, "available")
            assert hasattr(provider, "priority")
            assert hasattr(provider, "device_type")

    def test_provider_detection_cpu_only(self, mock_onnx_available: Mock) -> None:
        """Test provider detection when only CPU is available."""
        mock_onnx_available.get_available_providers.return_value = ["CPUExecutionProvider"]

        manager = ONNXProviderManager()
        providers = manager.detect_providers()

        assert len(providers) == 1
        assert providers[0].name == "CPUExecutionProvider"
        assert providers[0].device_type == "cpu"

    def test_provider_detection_onnx_unavailable(self, mock_onnx_unavailable: Any) -> None:
        """Test provider detection when ONNX is not available."""
        manager = ONNXProviderManager()
        providers = manager.detect_providers()

        assert providers == []

    def test_optimal_providers_with_preferences(self, mock_onnx_available: Mock) -> None:
        """Test optimal provider selection with preferences."""
        manager = ONNXProviderManager()

        # Preferred provider available
        providers = manager.get_optimal_providers(["CUDAExecutionProvider"])
        assert "CUDAExecutionProvider" in providers

        # Preferred provider not available
        providers = manager.get_optimal_providers(["TensorrtExecutionProvider"])
        assert "CPUExecutionProvider" in providers  # Should fallback to CPU

        # No preferences
        providers = manager.get_optimal_providers()
        assert len(providers) >= 1
        assert providers[0] in ["CUDAExecutionProvider", "CPUExecutionProvider"]

    def test_session_options_configuration(self, mock_onnx_available: Mock) -> None:
        """Test ONNX session options configuration."""
        manager = ONNXProviderManager()

        # Test latency optimization
        options = manager.configure_session_options("latency")
        mock_onnx_available.GraphOptimizationLevel.ORT_ENABLE_ALL.assert_called()
        mock_onnx_available.ExecutionMode.ORT_SEQUENTIAL.assert_called()

        # Test throughput optimization
        options = manager.configure_session_options("throughput")
        mock_onnx_available.ExecutionMode.ORT_PARALLEL.assert_called()

    def test_provider_info_retrieval(self, mock_onnx_available: Mock) -> None:
        """Test getting information about specific providers."""
        manager = ONNXProviderManager()
        manager.detect_providers()  # Initialize cache

        # Test existing provider
        info = manager.get_provider_info("CPUExecutionProvider")
        assert info is not None
        assert info.name == "CPUExecutionProvider"
        assert info.available is True

        # Test non-existing provider
        info = manager.get_provider_info("NonExistentProvider")
        assert info is None


class TestONNXModelDownloading:
    """Test ONNX model downloading and caching."""

    @pytest.fixture
    def mock_downloader(self, tmp_path: Path) -> ONNXModelDownloader:
        """Create a model downloader with temporary directory."""
        return ONNXModelDownloader(cache_dir=str(tmp_path))

    def test_cache_path_generation(self, mock_downloader: ONNXModelDownloader) -> None:
        """Test cache path generation for different model names."""
        path1 = mock_downloader.get_model_cache_path("test/model")
        path2 = mock_downloader.get_model_cache_path("test-model")
        path3 = mock_downloader.get_model_cache_path("test\\model")

        # All should result in valid filenames
        assert path1.name == "test_model.onnx"
        assert path2.name == "test-model.onnx"
        assert path3.name == "test_model.onnx"

    def test_local_model_finding(self, mock_downloader: ONNXModelDownloader) -> None:
        """Test finding locally cached models."""
        model_name = "test/model"

        # Create a cached model file
        cache_path = mock_downloader.get_model_cache_path(model_name)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("dummy model content")

        # Should find the cached model
        found_path = mock_downloader.find_local_model(model_name)
        assert found_path == cache_path

        # Should not find non-existent model
        not_found = mock_downloader.find_local_model("non/existent")
        assert not_found is None

    def test_model_hash_verification(self, mock_downloader: ONNXModelDownloader) -> None:
        """Test model hash verification."""
        # Create a test file
        test_file = mock_downloader.cache_dir / "test_model.onnx"
        test_content = b"test model content for hashing"
        test_file.write_bytes(test_content)

        # Calculate expected hash
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Test successful verification
        actual_hash = mock_downloader.verify_model_hash(test_file, expected_hash)
        assert actual_hash == expected_hash

        # Test failed verification
        with pytest.raises(InfrastructureError):
            mock_downloader.verify_model_hash(test_file, "wrong_hash")

        # Test verification without expected hash
        actual_hash = mock_downloader.verify_model_hash(test_file, None)
        assert actual_hash == expected_hash

    @pytest.mark.asyncio
    async def test_model_download_failure(self, mock_downloader: ONNXModelDownloader) -> None:
        """Test model download failure handling."""
        # Mock huggingface_hub to fail
        with patch("app.infrastructure.security.llm.onnx_utils.hf_hub_download") as mock_download:
            mock_download.side_effect = Exception("Download failed")

            with pytest.raises(InfrastructureError):
                await mock_downloader.download_model("non/existent/model")


class TestONNXModelManager:
    """Test ONNX model manager with loading and caching."""

    @pytest.fixture
    def mock_manager(self, tmp_path: Path) -> ONNXModelManager:
        """Create a model manager with mocked dependencies."""
        return ONNXModelManager(cache_dir=str(tmp_path), auto_download=False)

    @pytest.mark.asyncio
    async def test_model_loading_success(self, mock_manager: ONNXModelManager) -> None:
        """Test successful model loading."""
        # Mock all dependencies
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            # Mock ONNX session
            mock_session = Mock()
            mock_ort.InferenceSession.return_value = mock_session
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

            # Mock tokenizer
            mock_tokenizer_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

            # Mock model file existence
            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                session, tokenizer, info = await mock_manager.load_model("test/model")

                assert session is mock_session
                assert tokenizer is mock_tokenizer_instance
                assert info["model_name"] == "test/model"
                assert info["provider"] == "CPUExecutionProvider"

    @pytest.mark.asyncio
    async def test_model_loading_with_provider_fallback(self, mock_manager: ONNXModelManager) -> None:
        """Test model loading with provider fallback."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            # Mock provider fallback (CUDA fails, CPU succeeds)
            def create_session_side_effect(*args: Any, **kwargs: Any) -> Mock:
                if kwargs.get("providers") == ["CUDAExecutionProvider"]:
                    raise Exception("CUDA not available")
                mock_session = Mock()
                mock_session.get_inputs.return_value = []
                mock_session.get_outputs.return_value = []
                return mock_session

            mock_ort.InferenceSession.side_effect = create_session_side_effect
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider", "CUDAExecutionProvider"]

            mock_tokenizer_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                session, tokenizer, info = await mock_manager.load_model("test/model")

                assert info["provider"] == "CPUExecutionProvider"

    @pytest.mark.asyncio
    async def test_model_loading_all_providers_fail(self, mock_manager: ONNXModelManager) -> None:
        """Test model loading when all providers fail."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
            mock_ort.InferenceSession.side_effect = Exception("All providers failed")
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                with pytest.raises(InfrastructureError):
                    await mock_manager.load_model("test/model")

    @pytest.mark.asyncio
    async def test_model_caching(self, mock_manager: ONNXModelManager) -> None:
        """Test model caching functionality."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            # Mock successful loading
            mock_session = Mock()
            mock_ort.InferenceSession.return_value = mock_session
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            mock_tokenizer_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                # Load model first time
                session1, tokenizer1, info1 = await mock_manager.load_model("test/model")

                # Load model second time (should use cache)
                session2, tokenizer2, info2 = await mock_manager.load_model("test/model")

                # Should be the same objects (cached)
                assert session1 is session2
                assert tokenizer1 is tokenizer2

                # Should have only loaded once
                assert mock_ort.InferenceSession.call_count == 1

    def test_model_unloading(self, mock_manager: ONNXModelManager) -> None:
        """Test model unloading from cache."""
        # Add some mock models to cache
        mock_manager.loaded_models = {
            "model1": (Mock(), Mock(), {}),
            "model2": (Mock(), Mock(), {}),
            "other_model": (Mock(), Mock(), {}),
        }

        # Unload specific model
        mock_manager.unload_model("model1")
        assert "model1" not in mock_manager.loaded_models
        assert "model2" in mock_manager.loaded_models

        # Clear all cache
        mock_manager.clear_cache()
        assert len(mock_manager.loaded_models) == 0

    def test_get_model_info(self, mock_manager: ONNXModelManager) -> None:
        """Test getting information about loaded models."""
        mock_info = {"model_name": "test/model", "provider": "CPUExecutionProvider"}
        mock_manager.loaded_models = {
            "test/model_latency": (Mock(), Mock(), mock_info),
            "other_model": (Mock(), Mock(), {}),
        }

        # Get existing model info
        info = mock_manager.get_model_info("test/model")
        assert info == mock_info

        # Get non-existent model info
        info = mock_manager.get_model_info("non/existent")
        assert info is None

    @pytest.mark.asyncio
    async def test_model_compatibility_verification(self, mock_manager: ONNXModelManager) -> None:
        """Test model compatibility verification."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            # Mock ONNX available
            mock_ort.__version__ = "1.18.0"
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

            # Mock model found and loadable
            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")
                mock_find.return_value.stat.return_value.st_size = 1024 * 1024  # 1MB

                with patch.object(mock_manager, "load_model") as mock_load:
                    mock_session = Mock()
                    mock_session.get_inputs.return_value = [Mock(name="input", type="float32", shape=[1, 512])]
                    mock_session.get_outputs.return_value = [Mock(name="output", type="float32", shape=[1, 2])]
                    mock_load.return_value = (mock_session, Mock(), {"provider": "CPUExecutionProvider"})

                    diagnostics = await mock_manager.verify_model_compatibility("test/model")

                    assert diagnostics["model_name"] == "test/model"
                    assert diagnostics["onnx_available"] is True
                    assert diagnostics["model_found"] is True
                    assert diagnostics["model_loadable"] is True
                    assert diagnostics["tokenizer_loadable"] is True
                    assert diagnostics["successful_provider"] == "CPUExecutionProvider"
                    assert "input_details" in diagnostics
                    assert "output_details" in diagnostics


class TestONNXIntegration:
    """Test ONNX integration with security scanners."""

    @pytest.mark.asyncio
    async def test_global_manager_singleton(self) -> None:
        """Test global manager singleton behavior."""
        # Reset global manager
        import app.infrastructure.security.llm.onnx_utils as utils
        utils._global_manager = None

        # Get manager twice - should be same instance
        manager1 = get_onnx_manager()
        manager2 = get_onnx_manager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_onnx_setup_verification(self) -> None:
        """Test ONNX setup verification utility."""
        with patch("app.infrastructure.security.llm.onnx_utils.get_onnx_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_manager.verify_model_compatibility.return_value = {"test": "data"}
            mock_get_manager.return_value = mock_manager

            result = await verify_onnx_setup("test/model")

            assert result == {"test": "data"}
            mock_manager.verify_model_compatibility.assert_called_once_with("test/model")

    def test_platform_specific_configurations(self) -> None:
        """Test platform-specific ONNX configurations."""
        manager = ONNXProviderManager()

        # Test on macOS
        with patch("platform.system", return_value="Darwin"):
            with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
                mock_ort.get_available_providers.return_value = [
                    "CPUExecutionProvider",
                    "CoreMLExecutionProvider"
                ]

                providers = manager.detect_providers()
                provider_names = [p.name for p in providers]

                assert "CPUExecutionProvider" in provider_names
                # CoreML might be available on Apple Silicon

        # Test on Linux
        with patch("platform.system", return_value="Linux"):
            with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
                mock_ort.get_available_providers.return_value = [
                    "CPUExecutionProvider",
                    "CUDAExecutionProvider"
                ]

                providers = manager.detect_providers()
                provider_names = [p.name for p in providers]

                assert "CPUExecutionProvider" in provider_names
                assert "CUDAExecutionProvider" in provider_names

        # Test on Windows
        with patch("platform.system", return_value="Windows"):
            with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
                mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

                providers = manager.detect_providers()
                provider_names = [p.name for p in providers]

                assert provider_names == ["CPUExecutionProvider"]


class TestONNXErrorScenarios:
    """Test ONNX error handling and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_onnx_runtime_not_available(self) -> None:
        """Test behavior when ONNX runtime is not available."""
        manager = ONNXModelManager(auto_download=False)

        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("No module named 'onnxruntime'")

            # Should fail when trying to load model
            with pytest.raises(InfrastructureError):
                await manager.load_model("test/model")

    @pytest.mark.asyncio
    async def test_model_file_corruption(self, tmp_path: Path) -> None:
        """Test handling of corrupted model files."""
        manager = ONNXModelManager(cache_dir=str(tmp_path), auto_download=False)

        # Create corrupted model file
        cache_path = manager.downloader.get_model_cache_path("test/model")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(b"corrupted model data")

        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
            mock_ort.InferenceSession.side_effect = Exception("Corrupted model file")
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

            with pytest.raises(InfrastructureError):
                await manager.load_model("test/model")

    @pytest.mark.asyncio
    async def test_memory_exhaustion_handling(self, mock_manager: ONNXModelManager) -> None:
        """Test handling of memory exhaustion during model loading."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort:
            mock_ort.InferenceSession.side_effect = MemoryError("Out of memory")
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                with pytest.raises(InfrastructureError):
                    await mock_manager.load_model("test/model")

    @pytest.mark.asyncio
    async def test_network_download_failure(self) -> None:
        """Test handling of network failures during model download."""
        manager = ONNXModelManager(auto_download=True)

        with patch("app.infrastructure.security.llm.onnx_utils.hf_hub_download") as mock_download:
            mock_download.side_effect = Exception("Network error")

            with pytest.raises(InfrastructureError):
                await manager.load_model("test/model")

    @pytest.mark.asyncio
    async def test_tokenizer_loading_failure(self, mock_manager: ONNXModelManager) -> None:
        """Test handling of tokenizer loading failures."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            # Mock successful ONNX loading
            mock_session = Mock()
            mock_ort.InferenceSession.return_value = mock_session
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]

            # Mock tokenizer failure
            mock_tokenizer.from_pretrained.side_effect = [
                Exception("Tokenizer not found"),
                Mock()  # Second call succeeds (fallback)
            ]

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                # Should succeed despite first tokenizer failure
                session, tokenizer, info = await mock_manager.load_model("test/model")
                assert session is not None
                assert tokenizer is not None

                # Should have tried tokenizer loading twice
                assert mock_tokenizer.from_pretrained.call_count == 2


class TestONNXPerformanceCharacteristics:
    """Test ONNX performance characteristics and optimization."""

    @pytest.mark.asyncio
    async def test_optimization_settings(self, mock_manager: ONNXModelManager) -> None:
        """Test different optimization settings."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            mock_session = Mock()
            mock_ort.InferenceSession.return_value = mock_session
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            mock_tokenizer_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                # Test latency optimization
                session1, _, info1 = await mock_manager.load_model("test/model", optimize_for="latency")
                assert info1["optimize_for"] == "latency"

                # Test throughput optimization
                session2, _, info2 = await mock_manager.load_model("test/model2", optimize_for="throughput")
                assert info2["optimize_for"] == "throughput"

    @pytest.mark.asyncio
    async def test_concurrent_model_loading(self, mock_manager: ONNXModelManager) -> None:
        """Test concurrent model loading behavior."""
        with patch("app.infrastructure.security.llm.onnx_utils.ort") as mock_ort, \
             patch("app.infrastructure.security.llm.onnx_utils.AutoTokenizer") as mock_tokenizer:

            mock_session = Mock()
            mock_ort.InferenceSession.return_value = mock_session
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            mock_tokenizer_instance = Mock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

            with patch.object(mock_manager.downloader, "find_local_model") as mock_find:
                mock_find.return_value = Path("/fake/path/model.onnx")

                # Load multiple models concurrently
                tasks = [
                    mock_manager.load_model(f"model_{i}")
                    for i in range(5)
                ]

                results = await asyncio.gather(*tasks)

                # All should succeed
                assert len(results) == 5
                for session, tokenizer, info in results:
                    assert session is not None
                    assert tokenizer is not None
                    assert "model_name" in info

                # Should have loaded each model once
                assert mock_ort.InferenceSession.call_count == 5
