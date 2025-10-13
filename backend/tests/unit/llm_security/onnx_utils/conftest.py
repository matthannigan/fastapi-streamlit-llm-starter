"""
ONNX Utils module test fixtures providing mocks for ONNX Runtime and external dependencies.

This module provides test doubles for external dependencies of the LLM security ONNX utils
module, focusing on ONNX Runtime operations, model downloading, file system interactions,
and provider management scenarios.

SHARED MOCKS: MockInfrastructureError is imported from parent conftest.py
"""

from typing import Dict, Any, Optional, List, Tuple
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime, UTC
import tempfile
import shutil

# Import shared mocks from parent conftest - these are used across multiple modules
# MockInfrastructureError and its fixture are now defined in backend/tests/unit/llm_security/conftest.py

# Import classes that would normally be from the actual implementation
# from app.infrastructure.security.llm.onnx_utils import (
#     ONNXModelInfo, ProviderInfo, ONNXModelDownloader, ONNXProviderManager, ONNXModelManager
# )


# NOTE: MockInfrastructureError removed - now shared fixture in parent conftest.py


class MockONNXModelInfo:
    """Mock ONNXModelInfo for testing model metadata operations."""

    def __init__(self,
                 model_name: str = "test-model",
                 model_path: str = "/tmp/models/test-model.onnx",
                 model_hash: str = "abcd1234567890" * 4,
                 file_size_mb: float = 512.34,
                 providers: Optional[List[str]] = None,
                 metadata: Optional[Dict] = None):
        self.model_name = model_name
        self.model_path = model_path
        self.model_hash = model_hash
        self.file_size_mb = file_size_mb
        self.providers = providers or ["CPUExecutionProvider"]
        self.metadata = metadata or {
            "provider": "CPUExecutionProvider",
            "optimize_for": "latency",
            "input_metadata": [{"name": "input_ids", "shape": [1, 512], "dtype": "int64"}],
            "output_metadata": [{"name": "logits", "shape": [1, 2], "dtype": "float32"}]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization testing."""
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "model_hash": self.model_hash,
            "file_size_mb": self.file_size_mb,
            "providers": self.providers,
            "metadata": self.metadata
        }


class MockProviderInfo:
    """Mock ProviderInfo for testing provider detection and management."""

    def __init__(self,
                 name: str = "CPUExecutionProvider",
                 available: bool = True,
                 priority: int = 3,
                 description: str = "CPU-based execution",
                 device_type: str = "cpu"):
        self.name = name
        self.available = available
        self.priority = priority
        self.description = description
        self.device_type = device_type

    def __repr__(self):
        return f"MockProviderInfo(name='{self.name}', available={self.available}, priority={self.priority})"


class MockONNXModelDownloader:
    """Mock ONNXModelDownloader for testing model downloading and caching operations."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or "/tmp/onnx_models"
        self.model_repositories = ["https://huggingface.co", "https://github.com"]
        self._download_calls = []
        self._local_search_calls = []
        self._hash_verification_calls = []
        self._local_models = {}  # Simulate local cache

    def get_model_cache_path(self, model_name: str) -> Path:
        """Mock cache path generation."""
        self._local_search_calls.append({"operation": "get_cache_path", "model_name": model_name})
        safe_name = model_name.replace("/", "_").replace("\\", "_")
        return Path(self.cache_dir) / f"{safe_name}.onnx"

    def verify_model_hash(self, model_path: Path, expected_hash: Optional[str] = None) -> str:
        """Mock model hash verification."""
        # Import at runtime to avoid circular imports
        from ..conftest import MockInfrastructureError
        
        self._hash_verification_calls.append({
            "operation": "verify_hash",
            "model_path": str(model_path),
            "expected_hash": expected_hash
        })

        # Simulate hash calculation
        actual_hash = "mock_sha256_hash_" + str(hash(str(model_path)))

        if expected_hash and expected_hash != actual_hash:
            raise MockInfrastructureError(
                f"Hash verification failed for {model_path}",
                context={"expected": expected_hash, "actual": actual_hash}
            )

        return actual_hash

    def find_local_model(self, model_name: str) -> Optional[Path]:
        """Mock local model search."""
        self._local_search_calls.append({"operation": "find_local", "model_name": model_name})

        # Check if model is in simulated local cache
        if model_name in self._local_models:
            return Path(self._local_models[model_name])

        # Simulate finding some models locally
        if model_name == "existing-local-model":
            return Path(self.cache_dir) / "existing-local-model.onnx"

        return None

    async def download_model(self, model_name: str, force_download: bool = False) -> Path:
        """Mock model downloading."""
        # Import at runtime to avoid circular imports
        from ..conftest import MockInfrastructureError
        
        self._download_calls.append({
            "operation": "download",
            "model_name": model_name,
            "force_download": force_download,
            "timestamp": "mock-timestamp"
        })

        # Check if already exists locally
        if not force_download:
            local_path = self.find_local_model(model_name)
            if local_path:
                return local_path

        # Simulate download failures
        if "error" in model_name.lower():
            raise MockInfrastructureError(f"Failed to download model: {model_name}")

        # Simulate successful download
        cache_path = self.get_model_cache_path(model_name)
        self._local_models[model_name] = str(cache_path)

        return cache_path

    def reset_history(self):
        """Reset call history for test isolation."""
        self._download_calls.clear()
        self._local_search_calls.clear()
        self._hash_verification_calls.clear()

    @property
    def download_history(self) -> List[Dict]:
        """Get history of download calls for test verification."""
        return self._download_calls.copy()

    @property
    def search_history(self) -> List[Dict]:
        """Get history of search calls for test verification."""
        return self._local_search_calls.copy()

    @property
    def verification_history(self) -> List[Dict]:
        """Get history of hash verification calls for test verification."""
        return self._hash_verification_calls.copy()


class MockONNXProviderManager:
    """Mock ONNXProviderManager for testing provider detection and configuration."""

    def __init__(self):
        self.providers_cache = None
        self._detection_calls = []
        self._optimization_calls = []
        self._available_providers = {
            "CPUExecutionProvider": MockProviderInfo(
                name="CPUExecutionProvider",
                available=True,
                priority=3,
                description="Universal CPU execution provider",
                device_type="cpu"
            ),
            "CUDAExecutionProvider": MockProviderInfo(
                name="CUDAExecutionProvider",
                available=False,  # Mock as unavailable for testing
                priority=1,
                description="NVIDIA GPU acceleration",
                device_type="gpu"
            ),
            "CoreMLExecutionProvider": MockProviderInfo(
                name="CoreMLExecutionProvider",
                available=True,
                priority=2,
                description="Apple Silicon Neural Engine",
                device_type="npu"
            )
        }

    def detect_providers(self) -> List[MockProviderInfo]:
        """Mock provider detection."""
        self._detection_calls.append({"operation": "detect_providers", "timestamp": "mock-timestamp"})

        if self.providers_cache is None:
            # Return available providers sorted by priority
            available_providers = [
                provider for provider in self._available_providers.values()
                if provider.available
            ]
            available_providers.sort(key=lambda p: p.priority)
            self.providers_cache = available_providers

        return self.providers_cache

    def get_optimal_providers(self, preferred_providers: Optional[List[str]] = None) -> List[str]:
        """Mock optimal provider selection."""
        self._detection_calls.append({
            "operation": "get_optimal_providers",
            "preferred_providers": preferred_providers
        })

        available_providers = self.detect_providers()
        available_names = [p.name for p in available_providers]

        if preferred_providers:
            # Filter preferred providers that are available
            optimal = [p for p in preferred_providers if p in available_names]
            if optimal:
                return optimal

        return available_names

    def configure_session_options(self, optimize_for: str = 'latency') -> Any:
        """Mock session options configuration."""
        self._optimization_calls.append({
            "operation": "configure_session_options",
            "optimize_for": optimize_for
        })

        mock_options = Mock()
        mock_options.optimize_for = optimize_for
        mock_options.intra_op_num_threads = 1 if optimize_for == "latency" else 4
        mock_options.execution_mode = "ORT_SEQUENTIAL" if optimize_for == "latency" else "ORT_PARALLEL"

        return mock_options

    def get_provider_info(self, provider_name: str) -> Optional[MockProviderInfo]:
        """Mock provider information retrieval."""
        return self._available_providers.get(provider_name)

    def reset_history(self):
        """Reset call history for test isolation."""
        self._detection_calls.clear()
        self._optimization_calls.clear()
        self.providers_cache = None

    @property
    def detection_history(self) -> List[Dict]:
        """Get history of detection calls for test verification."""
        return self._detection_calls.copy()

    @property
    def optimization_history(self) -> List[Dict]:
        """Get history of optimization calls for test verification."""
        return self._optimization_calls.copy()


class MockONNXModelManager:
    """Mock ONNXModelManager for testing high-level model management."""

    def __init__(self, cache_dir: Optional[str] = None, preferred_providers: Optional[List[str]] = None, auto_download: bool = True):
        self.downloader = MockONNXModelDownloader(cache_dir)
        self.provider_manager = MockONNXProviderManager()
        self.preferred_providers = preferred_providers or ["CPUExecutionProvider"]
        self.auto_download = auto_download
        self.loaded_models = {}
        self._load_calls = []
        self._unload_calls = []

    async def load_model(self, model_name: str, optimize_for: str = 'latency', verify_hash: Optional[str] = None) -> Tuple[Any, str, Dict[str, Any]]:
        """Mock model loading with provider fallback."""
        # Import at runtime to avoid circular imports
        from ..conftest import MockInfrastructureError
        
        self._load_calls.append({
            "operation": "load_model",
            "model_name": model_name,
            "optimize_for": optimize_for,
            "verify_hash": verify_hash,
            "timestamp": "mock-timestamp"
        })

        # Check if already loaded
        if model_name in self.loaded_models:
            cached_model = self.loaded_models[model_name]
            return cached_model["session"], cached_model["tokenizer"], cached_model["info"]

        # Simulate model loading failures
        if "error" in model_name.lower():
            raise MockInfrastructureError(f"Failed to load model: {model_name}")

        # Mock model loading process
        model_path = await self.downloader.download_model(model_name)

        if verify_hash:
            self.downloader.verify_model_hash(model_path, verify_hash)

        # Mock session and tokenizer creation
        mock_session = Mock()
        mock_session.get_inputs = Mock(return_value=[Mock(name="input_ids", shape=[1, 512])])
        mock_session.get_outputs = Mock(return_value=[Mock(name="logits", shape=[1, 2])])

        mock_tokenizer = f"mock_tokenizer_{model_name}"

        # Create model info
        providers = self.provider_manager.get_optimal_providers(self.preferred_providers)
        model_info = MockONNXModelInfo(
            model_name=model_name,
            model_path=str(model_path),
            providers=providers,
            metadata={"provider": providers[0] if providers else "CPUExecutionProvider", "optimize_for": optimize_for}
        ).to_dict()

        # Cache the loaded model
        self.loaded_models[model_name] = {
            "session": mock_session,
            "tokenizer": mock_tokenizer,
            "info": model_info
        }

        return mock_session, mock_tokenizer, model_info

    def unload_model(self, model_name: str) -> None:
        """Mock model unloading."""
        self._unload_calls.append({
            "operation": "unload_model",
            "model_name": model_name,
            "timestamp": "mock-timestamp"
        })

        if model_name in self.loaded_models:
            del self.loaded_models[model_name]

    def clear_cache(self) -> None:
        """Mock cache clearing."""
        self.loaded_models.clear()
        self.downloader.reset_history()
        self.provider_manager.reset_history()

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Mock model information retrieval."""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]["info"]
        return None

    async def verify_model_compatibility(self, model_name: str) -> Dict[str, Any]:
        """Mock model compatibility verification."""
        return {
            "model_name": model_name,
            "model_loadable": "error" not in model_name.lower(),
            "model_path": str(self.downloader.get_model_cache_path(model_name)),
            "providers_available": self.provider_manager.get_optimal_providers(),
            "recommendations": [] if "error" not in model_name.lower() else ["Model format not supported"]
        }

    def reset_history(self):
        """Reset call history for test isolation."""
        self._load_calls.clear()
        self._unload_calls.clear()
        self.downloader.reset_history()
        self.provider_manager.reset_history()

    @property
    def load_history(self) -> List[Dict]:
        """Get history of load calls for test verification."""
        return self._load_calls.copy()

    @property
    def unload_history(self) -> List[Dict]:
        """Get history of unload calls for test verification."""
        return self._unload_calls.copy()


# Pytest Fixtures

# NOTE: mock_infrastructure_error fixture removed - now shared fixture in parent conftest.py


@pytest.fixture
def mock_onnx_model_info():
    """Factory fixture to create MockONNXModelInfo instances for testing."""
    def _create_info(**kwargs) -> MockONNXModelInfo:
        return MockONNXModelInfo(**kwargs)
    return _create_info


@pytest.fixture
def mock_provider_info():
    """Factory fixture to create MockProviderInfo instances for testing."""
    def _create_provider(**kwargs) -> MockProviderInfo:
        return MockProviderInfo(**kwargs)
    return _create_provider


@pytest.fixture
def mock_onnx_model_downloader():
    """Factory fixture to create MockONNXModelDownloader instances for testing."""
    def _create_downloader(cache_dir: Optional[str] = None) -> MockONNXModelDownloader:
        return MockONNXModelDownloader(cache_dir=cache_dir)
    return _create_downloader


@pytest.fixture
def mock_onnx_provider_manager():
    """Factory fixture to create MockONNXProviderManager instances for testing."""
    def _create_manager() -> MockONNXProviderManager:
        return MockONNXProviderManager()
    return _create_manager


@pytest.fixture
def mock_onnx_model_manager():
    """Factory fixture to create MockONNXModelManager instances for testing."""
    def _create_manager(cache_dir: Optional[str] = None,
                        preferred_providers: Optional[List[str]] = None,
                        auto_download: bool = True) -> MockONNXModelManager:
        return MockONNXModelManager(cache_dir=cache_dir, preferred_providers=preferred_providers, auto_download=auto_download)
    return _create_manager


@pytest.fixture
def onnx_test_models():
    """Test data for various ONNX model scenarios."""
    return {
        "basic_model": {
            "name": "microsoft/deberta-v3-base",
            "cache_path": "/tmp/models/microsoft_deberta-v3-base.onnx",
            "file_size_mb": 512.34,
            "providers": ["CPUExecutionProvider"],
            "hash": "abcd1234567890" * 4
        },
        "gpu_model": {
            "name": "nvidia/bert-large",
            "cache_path": "/tmp/models/nvidia_bert-large.onnx",
            "file_size_mb": 1024.56,
            "providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],
            "hash": "efgh5678901234" * 4
        },
        "error_model": {
            "name": "error/model-download-fails",
            "cache_path": "/tmp/models/error_model-download-fails.onnx",
            "file_size_mb": 256.78,
            "providers": ["CPUExecutionProvider"],
            "hash": "ijkl3456789012" * 4,
            "should_fail": True
        },
        "large_model": {
            "name": "huge/model-v2",
            "cache_path": "/tmp/models/huge_model-v2.onnx",
            "file_size_mb": 2048.90,
            "providers": ["CoreMLExecutionProvider", "CPUExecutionProvider"],
            "hash": "mnop7890123456" * 4
        }
    }


@pytest.fixture
def onnx_provider_test_data():
    """Test data for provider detection and management scenarios."""
    return {
        "cpu_only": {
            "available_providers": ["CPUExecutionProvider"],
            "expected_optimal": ["CPUExecutionProvider"],
            "system_type": "cpu_only"
        },
        "gpu_available": {
            "available_providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],
            "expected_optimal": ["CUDAExecutionProvider", "CPUExecutionProvider"],
            "system_type": "gpu_system"
        },
        "apple_silicon": {
            "available_providers": ["CoreMLExecutionProvider", "CPUExecutionProvider"],
            "expected_optimal": ["CoreMLExecutionProvider", "CPUExecutionProvider"],
            "system_type": "apple_silicon"
        },
        "no_providers": {
            "available_providers": [],
            "expected_optimal": [],
            "system_type": "minimal_installation"
        }
    }


@pytest.fixture
def onnx_session_options_test_data():
    """Test data for ONNX session configuration scenarios."""
    return {
        "latency_optimized": {
            "optimize_for": "latency",
            "expected_intra_threads": 1,
            "expected_execution_mode": "ORT_SEQUENTIAL",
            "use_case": "real_time_inference"
        },
        "throughput_optimized": {
            "optimize_for": "throughput",
            "expected_intra_threads": 4,
            "expected_execution_mode": "ORT_PARALLEL",
            "use_case": "batch_processing"
        },
        "balanced": {
            "optimize_for": "balanced",
            "expected_intra_threads": 2,
            "expected_execution_mode": "ORT_PARALLEL",
            "use_case": "general_purpose"
        }
    }


@pytest.fixture
def onnx_error_scenarios():
    """Various error scenarios for testing ONNX utils error handling."""
    return {
        "model_download_failed": {
            "model_name": "nonexistent/model",
            "error_type": "InfrastructureError",
            "expected_message": "Failed to download model",
            "should_retry": True
        },
        "hash_verification_failed": {
            "model_name": "test-model",
            "expected_hash": "wrong_hash",
            "actual_hash": "correct_hash",
            "error_type": "InfrastructureError",
            "expected_message": "Hash verification failed"
        },
        "model_loading_failed": {
            "model_name": "corrupted/model",
            "error_type": "InfrastructureError",
            "expected_message": "Failed to load model",
            "should_fallback": True
        },
        "provider_unavailable": {
            "preferred_providers": ["MissingProvider"],
            "fallback_providers": ["CPUExecutionProvider"],
            "error_type": "ValueError",
            "should_fallback": True
        },
        "file_system_error": {
            "cache_dir": "/invalid/path",
            "error_type": "OSError",
            "expected_message": "Permission denied",
            "should_fallback": False
        }
    }


@pytest.fixture
def onnx_performance_test_data():
    """Performance test data for ONNX operations timing and metrics."""
    return {
        "fast_load": {
            "model_name": "small-model",
            "expected_load_time_ms": 150,
            "expected_file_size_mb": 64.5,
            "memory_usage_mb": 128
        },
        "medium_load": {
            "model_name": "medium-model",
            "expected_load_time_ms": 800,
            "expected_file_size_mb": 512.0,
            "memory_usage_mb": 512
        },
        "slow_load": {
            "model_name": "large-model",
            "expected_load_time_ms": 3000,
            "expected_file_size_mb": 2048.0,
            "memory_usage_mb": 1024
        },
        "cache_hit": {
            "model_name": "cached-model",
            "expected_load_time_ms": 5,  # Very fast when cached
            "cache_hit": True
        }
    }


@pytest.fixture
def onnx_tmp_model_cache(tmp_path):
    """Temporary directory structure for testing model caching operations."""
    cache_dir = tmp_path / "onnx_models"
    cache_dir.mkdir(exist_ok=True)

    # Create some mock model files
    models = {
        "existing_model.onnx": b"mock_onnx_model_data_1",
        "another_model.onnx": b"mock_onnx_model_data_2",
        "subdir/nested_model.onnx": b"mock_onnx_model_data_3"
    }

    for model_file, content in models.items():
        model_path = cache_dir / model_file
        model_path.parent.mkdir(exist_ok=True)
        model_path.write_bytes(content)

    return {
        "cache_dir": str(cache_dir),
        "existing_models": list(models.keys()),
        "cache_path": cache_dir
    }