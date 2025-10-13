"""
ONNX Configuration Tests

Tests for ONNX model loading, provider configuration, and fallback behavior.
This test suite validates that the scanner properly handles ONNX models,
provider fallback chains, and graceful degradation when ONNX is unavailable.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, List

from app.infrastructure.security.llm.scanners.local_scanner import (  # type: ignore
    ModelCache,
    PromptInjectionScanner,
    ToxicityScanner,
)
from app.infrastructure.security.llm.config import ScannerConfig, ViolationAction  # type: ignore


class TestModelCacheONNXSupport:
    """Test ModelCache ONNX support and provider configuration."""

    def test_model_cache_with_default_providers(self) -> None:
        """Test ModelCache initialization with default ONNX providers."""
        cache = ModelCache()

        assert cache._onnx_providers == ["CPUExecutionProvider"]
        assert isinstance(cache._onnx_available, bool)

    def test_model_cache_with_custom_providers(self) -> None:
        """Test ModelCache initialization with custom ONNX providers."""
        custom_providers: List[str] = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        cache = ModelCache(onnx_providers=custom_providers)

        assert cache._onnx_providers == custom_providers

    @patch("app.infrastructure.security.llm.scanners.local_scanner.logger")
    def test_onnx_availability_check_success(self, mock_logger: Mock) -> None:
        """Test successful ONNX availability check."""
        with patch("app.infrastructure.security.llm.scanners.local_scanner.ort") as mock_ort:
            mock_ort.get_available_providers.return_value = [
                "CPUExecutionProvider",
                "CUDAExecutionProvider"
            ]

            cache = ModelCache()

            assert cache._onnx_available is True
            mock_logger.info.assert_called_once()
            assert "ONNX Runtime available" in mock_logger.info.call_args[0][0]

    @patch("app.infrastructure.security.llm.scanners.local_scanner.logger")
    def test_onnx_availability_check_failure(self, mock_logger: Mock) -> None:
        """Test ONNX availability check when ONNX is not available."""
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("No module named 'onnxruntime'")

            cache = ModelCache()

            assert cache._onnx_available is False
            mock_logger.warning.assert_called_once()
            assert "ONNX Runtime not available" in mock_logger.warning.call_args[0][0]

    @patch("app.infrastructure.security.llm.scanners.local_scanner.logger")
    def test_onnx_availability_check_import_error(self, mock_logger: Mock) -> None:
        """Test ONNX availability check with ImportError during import."""
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("Import failed")

            cache = ModelCache()

            assert cache._onnx_available is False
            mock_logger.warning.assert_called_once()


class TestONNXProviderConfiguration:
    """Test ONNX provider configuration and fallback behavior."""

    @pytest.fixture
    def mock_scanner_config(self) -> ScannerConfig:
        """Create a mock scanner configuration."""
        return ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=True,
        )

    @pytest.fixture
    def model_cache_with_providers(self) -> ModelCache:
        """Create ModelCache with specific providers."""
        providers: List[str] = ["CUDAExecutionProvider", "CPUExecutionProvider", "CoreMLExecutionProvider"]
        return ModelCache(onnx_providers=providers)

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    async def test_onnx_model_loading_success(
        self,
        mock_tokenizer: Mock,
        mock_ort: Mock,
        mock_scanner_config: ScannerConfig,
        model_cache_with_providers: ModelCache
    ) -> None:
        """Test successful ONNX model loading with first provider."""
        # Mock ONNX session
        mock_session = Mock()
        mock_ort.InferenceSession.return_value = mock_session

        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        scanner = PromptInjectionScanner(mock_scanner_config, model_cache_with_providers)

        # Test ONNX model loading
        result = await scanner._load_onnx_model("test-model", {})

        assert result is not None
        assert result["type"] == "onnx"
        assert result["session"] is mock_session
        assert result["tokenizer"] is mock_tokenizer_instance

        # Verify first provider was used
        mock_ort.InferenceSession.assert_called_once_with(
            "test-model.onnx",
            sess_options=mock_ort.SessionOptions.return_value,
            providers=["CUDAExecutionProvider"]
        )

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.logger")
    async def test_onnx_provider_fallback_chain(
        self,
        mock_logger: Mock,
        mock_tokenizer: Mock,
        mock_ort: Mock,
        mock_scanner_config: ScannerConfig
    ) -> None:
        """Test ONNX provider fallback when first provider fails."""
        providers: List[str] = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        cache = ModelCache(onnx_providers=providers)

        # Mock ONNX session - first provider fails, second succeeds
        def side_effect_inference_session(*args: Any, **kwargs: Any) -> Mock:
            if kwargs.get("providers") == ["CUDAExecutionProvider"]:
                raise Exception("CUDA not available")
            mock_session = Mock()
            return mock_session

        mock_ort.InferenceSession.side_effect = side_effect_inference_session

        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        scanner = PromptInjectionScanner(mock_scanner_config, cache)

        # Test ONNX model loading with fallback
        result = await scanner._load_onnx_model("test-model", {})

        assert result is not None
        assert result["type"] == "onnx"

        # Verify both providers were tried
        assert mock_ort.InferenceSession.call_count == 2

        # Verify warning was logged for failed provider
        assert mock_logger.warning.call_count == 1
        assert "Failed to load ONNX model with provider CUDAExecutionProvider" in str(mock_logger.warning.call_args)

        # Verify success was logged for fallback provider
        assert mock_logger.info.call_count >= 1
        success_calls = [call for call in mock_logger.info.call_args_list
                        if "Successfully loaded ONNX model with provider" in str(call)]
        assert len(success_calls) >= 1

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.pipeline")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.logger")
    async def test_onnx_fallback_to_transformers(
        self,
        mock_logger: Mock,
        mock_pipeline: Mock,
        mock_ort: Mock,
        mock_scanner_config: ScannerConfig
    ) -> None:
        """Test fallback to Transformers when all ONNX providers fail."""
        providers: List[str] = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        cache = ModelCache(onnx_providers=providers)

        # Mock all ONNX providers failing
        mock_ort.InferenceSession.side_effect = Exception("All providers failed")

        # Mock Transformers pipeline
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance

        scanner = PromptInjectionScanner(mock_scanner_config, cache)

        # Test ONNX model loading with fallback to Transformers
        result = await scanner._load_onnx_model("test-model", {})

        # Should fallback to Transformers
        mock_pipeline.assert_called_once()
        assert mock_pipeline.call_args[1]["model"] == "test-model"
        assert mock_pipeline.call_args[1]["device"] == -1  # CPU fallback

        # Verify error was logged
        assert mock_logger.error.call_count == 1
        assert "Failed to load ONNX model test-model" in str(mock_logger.error.call_args)

        # Verify scanner fallback flag was set
        assert scanner._use_onnx is False

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    async def test_onnx_disabled_in_configuration(
        self,
        mock_tokenizer: Mock,
        mock_ort: Mock
    ) -> None:
        """Test scanner behavior when ONNX is disabled in configuration."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,  # ONNX disabled
        )

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # Verify ONNX is not used
        assert scanner._use_onnx is False

        # Should not try to load ONNX model
        with patch.object(scanner, "_load_transformers_model") as mock_load_transformers:
            mock_load_transformers.return_value = Mock()

            await scanner._load_model()

            mock_load_transformers.assert_called_once()
            assert mock_ort.InferenceSession.call_count == 0

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    async def test_onnx_unavailable_fallback(
        self,
        mock_tokenizer: Mock,
        mock_ort: Mock
    ) -> None:
        """Test fallback behavior when ONNX runtime is not available."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=True,  # ONNX requested but not available
        )

        # Create cache with ONNX unavailable
        with patch("app.infrastructure.security.llm.scanners.local_scanner.logger"):
            cache = ModelCache()
            cache._onnx_available = False  # Simulate ONNX unavailable

        scanner = PromptInjectionScanner(config, cache)

        # Verify ONNX is not used despite being requested
        assert scanner._use_onnx is False

        # Should use Transformers instead
        with patch.object(scanner, "_load_transformers_model") as mock_load_transformers:
            mock_load_transformers.return_value = Mock()

            await scanner._load_model()

            mock_load_transformers.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    async def test_onnx_inference_execution(
        self,
        mock_tokenizer: Mock,
        mock_ort: Mock
    ) -> None:
        """Test ONNX model inference execution."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=True,
        )

        # Setup successful ONNX model loading
        mock_session = Mock()
        mock_session.run.return_value = [Mock()]  # Mock output
        mock_ort.InferenceSession.return_value = mock_session

        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.return_value = {
            "input_ids": Mock(),
            "attention_mask": Mock()
        }
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # Load ONNX model
        model = await scanner._load_onnx_model("test-model", {})
        scanner._model = model

        # Mock numpy operations for output processing
        with patch("numpy.array") as mock_numpy:
            mock_output = Mock()
            mock_output.argmax.return_value = 1
            mock_output.__getitem__ = Mock(return_value=0.95)
            mock_numpy.return_value = [mock_output]

            # Test inference
            result = await scanner._run_inference("test text")

            assert result is not None
            assert len(result) == 1
            assert result[0]["label"] == "LABEL_1"
            assert result[0]["score"] == 0.95

            # Verify tokenizer was called
            mock_tokenizer_instance.assert_called_once_with(
                "test text",
                return_tensors="np",
                truncation=True,
                max_length=512
            )

            # Verify ONNX session was called
            mock_session.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.pipeline")
    async def test_transformers_inference_execution(self, mock_pipeline: Mock) -> None:
        """Test Transformers model inference execution."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,
        )

        # Mock Transformers pipeline
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [
            {"label": "toxic", "score": 0.85}
        ]
        mock_pipeline.return_value = mock_pipeline_instance

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # Mock Transformers model loading
        with patch.object(scanner, "_load_transformers_model") as mock_load:
            mock_transformers_model = Mock()
            mock_transformers_model["type"] = "transformers"
            mock_load.return_value = mock_transformers_model

            await scanner._load_model()
            scanner._model = mock_transformers_model

            # Test inference
            result = await scanner._run_inference("test text")

            assert result is not None
            assert len(result) == 1
            assert result[0]["label"] == "toxic"
            assert result[0]["score"] == 0.85

            # Verify pipeline was called
            mock_pipeline_instance.assert_called_once_with("test text")

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.logger")
    async def test_inference_error_handling(self, mock_logger: Mock) -> None:
        """Test error handling during model inference."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=True,
        )

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # Mock model that raises exception during inference
        scanner._model = {
            "type": "onnx",
            "session": Mock(),
            "tokenizer": Mock()
        }
        scanner._model["session"].run.side_effect = Exception("Inference failed")

        # Test inference error handling
        result = await scanner._run_inference("test text")

        assert result is None
        assert mock_logger.error.call_count == 1
        assert "Inference failed" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_device_selection_for_onnx(self) -> None:
        """Test device selection when ONNX is enabled."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=True,
        )

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # ONNX should return "onnx" as device
        device = scanner._get_device()
        assert device == "onnx"

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.torch")
    async def test_device_selection_for_transformers_mps(self, mock_torch: Mock) -> None:
        """Test device selection for Transformers with MPS available."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,
        )

        # Mock MPS available
        mock_torch.backends.mps.is_available.return_value = True

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        device = scanner._get_device()
        assert device == "mps"

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.torch")
    async def test_device_selection_for_transformers_cuda(self, mock_torch: Mock) -> None:
        """Test device selection for Transformers with CUDA available."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,
        )

        # Mock MPS not available, CUDA available
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = True

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        device = scanner._get_device()
        assert device == "cuda"

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.torch")
    async def test_device_selection_for_transformers_cpu(self, mock_torch: Mock) -> None:
        """Test device selection for Transformers with CPU fallback."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,
        )

        # Mock neither MPS nor CUDA available
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        device = scanner._get_device()
        assert device == "cpu"

    @pytest.mark.asyncio
    async def test_device_selection_torch_not_available(self) -> None:
        """Test device selection when PyTorch is not available."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,
        )

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # Mock ImportError when importing torch
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("No module named 'torch'")

            device = scanner._get_device()
            assert device == "cpu"


class TestMultipleScannerONNXConfiguration:
    """Test ONNX configuration across different scanner types."""

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    async def test_prompt_injection_scanner_onnx(
        self,
        mock_tokenizer: Mock,
        mock_ort: Mock
    ) -> None:
        """Test PromptInjectionScanner with ONNX configuration."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="prompt-injection-model",
            use_onnx=True,
        )

        # Mock ONNX components
        mock_session = Mock()
        mock_ort.InferenceSession.return_value = mock_session
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        await scanner._load_model()

        # Verify ONNX loading
        mock_ort.InferenceSession.assert_called_once()
        assert scanner._model["type"] == "onnx"

    @pytest.mark.asyncio
    @patch("app.infrastructure.security.llm.scanners.local_scanner.ort")
    @patch("app.infrastructure.security.llm.scanners.local_scanner.AutoTokenizer")
    async def test_toxicity_scanner_onnx(
        self,
        mock_tokenizer: Mock,
        mock_ort: Mock
    ) -> None:
        """Test ToxicityScanner with ONNX configuration."""
        config = ScannerConfig(
            enabled=True,
            threshold=0.7,
            action=ViolationAction.WARN,
            model_name="toxicity-model",
            use_onnx=True,
        )

        # Mock ONNX components
        mock_session = Mock()
        mock_ort.InferenceSession.return_value = mock_session
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        cache = ModelCache()
        scanner = ToxicityScanner(config, cache)

        await scanner._load_model()

        # Verify ONNX loading with correct cache key
        mock_ort.InferenceSession.assert_called_once()
        assert scanner._model["type"] == "onnx"

        # Verify cache key includes scanner type
        cache_key_used: str | None = None
        for call in cache._cache.keys():
            if "toxicity" in call:
                cache_key_used = call
                break
        assert cache_key_used is not None
        assert "onnx" in cache_key_used

    @pytest.mark.asyncio
    async def test_scanner_model_parameters(self) -> None:
        """Test that scanner model parameters are properly passed through."""
        model_params: Dict[str, Any] = {
            "max_length": 512,
            "truncation": True,
            "padding": True,
        }

        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            use_onnx=False,  # Use Transformers for easier parameter testing
            model_params=model_params,
        )

        with patch("app.infrastructure.security.llm.scanners.local_scanner.pipeline") as mock_pipeline:
            mock_pipeline.return_value = Mock()

            cache = ModelCache()
            scanner = PromptInjectionScanner(config, cache)

            await scanner._load_model()

            # Verify model parameters were passed
            mock_pipeline.assert_called_once()
            call_kwargs = mock_pipeline.call_args[1]
            assert call_kwargs["model"] == "test-model"
            assert call_kwargs["max_length"] == 512
            assert call_kwargs["truncation"] is True
            assert call_kwargs["padding"] is True

    def test_scanner_configuration_metadata_preservation(self) -> None:
        """Test that scanner configuration metadata is preserved."""
        metadata: Dict[str, Any] = {
            "description": "Test scanner",
            "severity": "high",
            "use_onnx": True,
            "redact": False,
        }

        config = ScannerConfig(
            enabled=True,
            threshold=0.8,
            action=ViolationAction.BLOCK,
            model_name="test-model",
            metadata=metadata,
        )

        cache = ModelCache()
        scanner = PromptInjectionScanner(config, cache)

        # Verify metadata is accessible
        assert scanner.config.metadata == metadata
        assert scanner.config.metadata["use_onnx"] is True
        assert scanner.config.metadata["redact"] is False
