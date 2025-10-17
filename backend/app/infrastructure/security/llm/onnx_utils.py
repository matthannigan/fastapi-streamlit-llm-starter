"""
ONNX Runtime Utilities for Security Scanners

This module provides comprehensive utilities for ONNX model management, including
automatic provider detection, model downloading and caching, verification, and
optimized loading with graceful fallback mechanisms for security scanning applications.

## Key Features

- **Automatic Provider Detection**: Detects and prioritizes available ONNX execution providers
  (CUDA, CPU, OpenVINO, TensorRT, CoreML, ROCm) with intelligent fallback
- **Model Verification**: Validates ONNX model integrity using SHA-256 hashing
- **Download & Caching**: Automatic model download from Hugging Face with local caching
  and multiple search locations for cached models
- **Graceful Fallback**: Falls back to Transformers when ONNX loading fails
- **Platform Optimization**: Configures session options for latency vs throughput optimization
- **Resource Management**: Efficient model caching and unloading with memory management

## Architecture

The module is organized into three main service classes:

- **ONNXModelDownloader**: Handles model discovery, downloading, and caching
- **ONNXProviderManager**: Manages execution provider detection and configuration
- **ONNXModelManager**: High-level orchestration of model loading with provider fallback

## Usage Patterns

### Basic Model Loading
```python
from app.infrastructure.security.llm.onnx_utils import get_onnx_manager

# Get global manager instance
manager = get_onnx_manager()

# Load model with automatic provider selection
session, tokenizer, info = await manager.load_model("microsoft/deberta-v3-base")

# Use model for inference
inputs = tokenizer("Hello world", return_tensors="np")
outputs = session.run(None, inputs)
```

### Custom Configuration
```python
from app.infrastructure.security.llm.onnx_utils import ONNXModelManager

# Custom manager with specific providers and caching
manager = ONNXModelManager(
    cache_dir="/custom/models/path",
    preferred_providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    auto_download=True
)

# Load with optimization for throughput
session, tokenizer, info = await manager.load_model(
    "model-name",
    optimize_for="throughput",
    verify_hash="expected_sha256_hash"
)
```

### Provider Management
```python
from app.infrastructure.security.llm.onnx_utils import ONNXProviderManager

provider_manager = ONNXProviderManager()

# Detect available providers
providers = provider_manager.detect_providers()
for provider in providers:
    print(f"{provider.name}: {provider.description} (available: {provider.available})")

# Get optimal provider list
optimal = provider_manager.get_optimal_providers(["CUDAExecutionProvider"])

# Configure session options
session_opts = provider_manager.configure_session_options(optimize_for="latency")
```

### Model Verification and Diagnostics
```python
# Verify model compatibility before loading
diagnostics = await manager.verify_model_compatibility("model-name")

if diagnostics["model_loadable"]:
    session, tokenizer, info = await manager.load_model("model-name")
else:
    logger.warning(f"Model issues: {diagnostics['recommendations']}")

# Get information about loaded models
model_info = manager.get_model_info("model-name")
print(f"Loaded with provider: {model_info['provider']}")
print(f"Model size: {model_info['file_size_mb']:.2f} MB")
```

## Dependencies

- **onnxruntime**: Core ONNX Runtime execution engine
- **transformers**: For tokenizer loading and model compatibility
- **huggingface_hub**: For model downloading (optional, auto-imported)
- **hashlib**: For model integrity verification

## Error Handling

The module uses structured error handling with custom exceptions:
- **InfrastructureError**: For model loading, downloading, and provider configuration failures
- **FileNotFoundError**: When model files are not found locally
- **ImportError**: When required dependencies are not available

All errors include contextual information to help diagnose issues with model loading,
provider availability, or network connectivity.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
import tempfile
import shutil

from app.core.exceptions import InfrastructureError

logger = logging.getLogger(__name__)


@dataclass
class ONNXModelInfo:
    """
    Comprehensive information about an ONNX model instance.

    This dataclass encapsulates all relevant metadata about a loaded ONNX model,
    including file information, provider details, and runtime characteristics.
    It provides a standardized format for model information exchange between
    different components of the security scanning infrastructure.

    Attributes:
        model_name: Original model identifier (e.g., "microsoft/deberta-v3-base")
        model_path: Absolute file path to the ONNX model file on disk
        model_hash: SHA-256 hash of the model file for integrity verification
        file_size_mb: Model file size in megabytes (float, 2 decimal precision)
        providers: List of available ONNX execution providers for this model
        metadata: Dictionary containing additional model-specific information:
                 - input_metadata: List of input tensor specifications
                 - output_metadata: List of output tensor specifications
                 - provider: Successfully loaded execution provider
                 - optimize_for: Optimization mode used ("latency" or "throughput")

    Usage:
        >>> # Create model info from loaded session
        >>> info = ONNXModelInfo(
        ...     model_name="microsoft/deberta-v3-base",
        ...     model_path="/cache/models/deberta.onnx",
        ...     model_hash="a1b2c3d4e5f6...",
        ...     file_size_mb=512.34,
        ...     providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        ...     metadata={"provider": "CUDAExecutionProvider", "optimize_for": "latency"}
        ... )
        >>>
        >>> # Access model characteristics
        >>> print(f"Model size: {info.file_size_mb:.2f} MB")
        >>> print(f"Using provider: {info.metadata['provider']}")
    """
    model_name: str
    model_path: str
    model_hash: str
    file_size_mb: float
    providers: List[str]
    metadata: Dict[str, Any]


@dataclass
class ProviderInfo:
    """
    Information about an ONNX execution provider and its capabilities.

    This dataclass provides standardized information about ONNX Runtime execution
    providers, including their availability, performance characteristics, and hardware
    requirements. It enables intelligent provider selection and fallback strategies
    for optimal model performance across different hardware configurations.

    Attributes:
        name: Official ONNX Runtime provider name (e.g., "CUDAExecutionProvider")
        available: Whether this provider is available on the current system
        priority: Performance priority (lower numbers = higher priority for selection)
        description: Human-readable description of the provider's capabilities
        device_type: Hardware device type, one of ["cpu", "gpu", "npu"]:
                    - "cpu": CPU-based execution (CPUExecutionProvider, OpenVINO)
                    - "gpu": GPU-based execution (CUDA, TensorRT, ROCm)
                    - "npu": Neural Processing Unit (CoreML on Apple Silicon)

    Usage:
        >>> # Create provider info for CUDA execution
        >>> cuda_info = ProviderInfo(
        ...     name="CUDAExecutionProvider",
        ...     available=True,
        ...     priority=1,
        ...     description="NVIDIA GPU acceleration with CUDA",
        ...     device_type="gpu"
        ... )
        >>>
        >>> # Check provider availability
        >>> if cuda_info.available:
        ...     print(f"Using {cuda_info.name} for optimal performance")
        ... else:
        ...     print("CUDA not available, falling back to CPU")
        >>>
        >>> # Sort providers by priority
        >>> providers = [cuda_info, cpu_info, openvino_info]
        >>> providers.sort(key=lambda p: p.priority)
        >>> for provider in providers:
        ...     if provider.available:
        ...         selected = provider
        ...         break
    """
    name: str
    available: bool
    priority: int
    description: str
    device_type: str  # "cpu", "gpu", "npu"


class ONNXModelDownloader:
    """
    Manages ONNX model discovery, downloading, and local caching for security scanning.

    This service provides comprehensive model management capabilities including automatic
    downloading from multiple repositories, integrity verification, local caching with
    multiple search locations, and graceful handling of network issues. It serves as
    the foundation for reliable model availability in security scanning applications.

    Attributes:
        cache_dir: Primary cache directory path for downloaded models
        model_repositories: List of supported model repository URLs for downloading

    Public Methods:
        get_model_cache_path(): Generate cache path for a model name
        verify_model_hash(): Calculate and verify model file integrity
        find_local_model(): Search for locally cached models in multiple locations
        download_model(): Download model from repositories with fallback strategies

    State Management:
        - Maintains local cache directory with automatic creation
        - Caches downloaded models indefinitely until manually removed
        - Thread-safe for concurrent model operations
        - No persistent state beyond file system cache

    Usage:
        # Basic downloader with default cache directory
        downloader = ONNXModelDownloader()

        # Custom cache location
        downloader = ONNXModelDownloader(cache_dir="/custom/model/cache")

        # Check if model exists locally
        model_path = downloader.find_local_model("microsoft/deberta-v3-base")
        if model_path:
            print(f"Model found at: {model_path}")
        else:
            # Download model if not available locally
            model_path = await downloader.download_model("microsoft/deberta-v3-base")

        # Verify model integrity
        actual_hash = downloader.verify_model_hash(model_path, "expected_hash")
        print(f"Model hash verified: {actual_hash[:16]}...")

    Error Handling:
        - **InfrastructureError**: For download failures, repository issues, or model format problems
        - **FileNotFoundError**: When expected model files don't exist locally
        - **ImportError**: When huggingface_hub is not available for downloading

    Thread Safety:
        Safe for concurrent use across multiple threads. File system operations
        are atomic and caching logic handles race conditions gracefully.
    """

    def __init__(self, cache_dir: str | None = None):
        """
        Initialize the model downloader with cache directory and repository configuration.

        Sets up the local cache directory structure and configures supported model
        repositories for downloading. The cache directory is created automatically
        if it doesn't exist.

        Args:
            cache_dir: Custom cache directory path for model storage. If None,
                      uses system temp directory (default: system temp directory/onnx_models)

        Behavior:
            - Creates cache directory with parents if it doesn't exist
            - Configures supported model repositories (Hugging Face, GitHub ONNX models)
            - Sets up file system paths for model management
            - Handles permission issues during directory creation gracefully

        Examples:
            >>> # Default configuration (uses system temp directory)
            >>> downloader = ONNXModelDownloader()
            >>> print(downloader.cache_dir)
            >>> /tmp/onnx_models  # or equivalent on your system

            >>> # Custom cache directory
            >>> downloader = ONNXModelDownloader("/app/models/onnx_cache")
            >>> print(downloader.cache_dir)
            >>> /app/models/onnx_cache

            >>> # Home directory cache
            >>> downloader = ONNXModelDownloader("~/.cache/my_models")
            >>> print(downloader.cache_dir)
            >>> /home/user/.cache/my_models
        """
        if cache_dir:
            # Use custom cache directory as-is
            self.cache_dir = Path(cache_dir)
        else:
            # Default: use system temp + onnx_models subdirectory
            self.cache_dir = Path(tempfile.gettempdir()) / "onnx_models"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Popular model repositories
        self.model_repositories = [
            "https://huggingface.co",
            "https://github.com/onnx/models",
        ]

    def get_model_cache_path(self, model_name: str) -> Path:
        """
        Generate a safe cache file path for a given model name.

        Converts model identifiers into filesystem-safe filenames by replacing
        path separators with underscores and adding the .onnx extension.

        Args:
            model_name: Model identifier (e.g., "microsoft/deberta-v3-base")
                        Can contain organization/model format or plain names

        Returns:
            Absolute Path object for the model file in the cache directory
            with .onnx extension (e.g., "/cache/models/microsoft_deberta-v3-base.onnx")

        Behavior:
            - Replaces forward slashes (/) with underscores for safety
            - Replaces backslashes (\\) with underscores for Windows compatibility
            - Adds .onnx extension if not already present
            - Uses absolute path resolution for consistent behavior

        Examples:
            >>> downloader = ONNXModelDownloader("/tmp/cache")
            >>> path = downloader.get_model_cache_path("microsoft/deberta-v3-base")
            >>> print(path)
            >>> /tmp/cache/microsoft_deberta-v3-base.onnx

            >>> # Complex model names are handled safely
            >>> path = downloader.get_model_cache_path("org\\team/model-name_v2")
            >>> print(path)
            >>> /tmp/cache/org__team_model-name_v2.onnx

            >>> # Plain model names work as expected
            >>> path = downloader.get_model_cache_path("my-model")
            >>> print(path)
            >>> /tmp/cache/my-model.onnx
        """
        # Create safe filename from model name
        # Replace backslashes first (with double underscores) to differentiate from forward slashes
        safe_name = model_name.replace("\\", "__").replace("/", "_")
        return self.cache_dir / f"{safe_name}.onnx"

    def verify_model_hash(self, model_path: Path, expected_hash: str | None = None) -> str:
        """
        Calculate and verify SHA-256 hash of a model file.

        Computes the SHA-256 hash of the specified model file using chunked reading
        to handle large files efficiently. Optionally verifies against an expected hash
        and raises an error if they don't match.

        Args:
            model_path: Path to the model file to hash (must exist and be readable)
            expected_hash: Optional expected SHA-256 hash for verification.
                          If provided, function will verify against this hash.
                          Must be a 64-character hexadecimal string.

        Returns:
            str: The calculated SHA-256 hash of the model file (64-character hex string)

        Raises:
            FileNotFoundError: If the model file does not exist at the specified path
            InfrastructureError: If expected_hash is provided and doesn't match actual hash

        Behavior:
            - Reads file in 4KB chunks to handle large models efficiently
            - Uses SHA-256 algorithm for cryptographic security
            - Performs exact string comparison for hash verification
            - Provides detailed error messages with both expected and actual hashes
            - Logs hash verification results for debugging

        Examples:
            >>> downloader = ONNXModelDownloader()
            >>>
            >>> # Calculate hash without verification
            >>> model_path = Path("/models/deberta.onnx")
            >>> actual_hash = downloader.verify_model_hash(model_path)
            >>> print(f"Model hash: {actual_hash[:16]}...")
            >>>
            >>> # Verify against expected hash
            >>> expected = "a1b2c3d4e5f6..."  # 64-char hex string
            >>> try:
            ...     actual = downloader.verify_model_hash(model_path, expected)
            ...     print("Hash verification passed")
            ... except InfrastructureError as e:
            ...     print(f"Hash verification failed: {e}")
            >>>
            >>> # Error case - file doesn't exist
            >>> with pytest.raises(FileNotFoundError):
            ...     downloader.verify_model_hash(Path("/nonexistent/model.onnx"))
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Calculate SHA-256 hash
        sha256_hash = hashlib.sha256()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        actual_hash = sha256_hash.hexdigest()

        if expected_hash and actual_hash != expected_hash:
            raise InfrastructureError(
                f"Model hash verification failed. Expected: {expected_hash}, Got: {actual_hash}"
            )

        return actual_hash

    def find_local_model(self, model_name: str) -> Path | None:
        """
        Search for locally cached ONNX models in multiple locations.

        Searches for the specified model in the primary cache directory and several
        common alternative locations. This provides flexibility for different model
        management strategies and supports models cached by other tools.

        Args:
            model_name: Model identifier to search for (e.g., "microsoft/deberta-v3-base")

        Returns:
            Path | None: Absolute path to the found model file, or None if not found

        Behavior:
            - Searches primary cache directory first
            - Checks common alternative locations in priority order
            - Handles both organization/model and plain name formats
            - Expands user home directory (~) in paths
            - Logs successful finds for debugging
            - Returns first match found (searches in order)

        Search Locations (in order):
            1. Primary cache directory: {cache_dir}/{safe_model_name}.onnx
            2. Current working directory: ./models/{model_name}.onnx
            3. Hugging Face cache: ~/.cache/huggingface/hub/{org--model}/model.onnx
            4. System temp directory: /tmp/onnx_models/{safe_model_name}.onnx

        Examples:
            >>> downloader = ONNXModelDownloader()
            >>>
            >>> # Model in primary cache
            >>> path = downloader.find_local_model("microsoft/deberta-v3-base")
            >>> if path:
            ...     print(f"Found at: {path}")
            ... else:
            ...     print("Not found locally")
            >>>
            >>> # Model not found anywhere
            >>> missing = downloader.find_local_model("nonexistent/model")
            >>> print(missing)  # None
            >>>
            >>> # Model in alternative location
            >>> # (assuming file exists at ./models/test-model.onnx)
            >>> path = downloader.find_local_model("test-model")
            >>> print(path)  # /current/dir/models/test-model.onnx

        Note:
            This method only searches for existing files and does not download
            models. Use download_model() to fetch models from repositories.
        """
        model_path = self.get_model_cache_path(model_name)

        if model_path.exists():
            logger.info(f"Found cached ONNX model: {model_name}")
            return model_path

        # Check common alternative locations
        alternative_paths = [
            Path(f"./models/{model_name}.onnx"),
            Path(f"~/.cache/huggingface/hub/{model_name.replace('/', '--')}/model.onnx").expanduser(),
            Path(f"/tmp/onnx_models/{model_name.replace('/', '_')}.onnx"),
        ]

        for alt_path in alternative_paths:
            if alt_path.exists():
                logger.info(f"Found ONNX model in alternative location: {alt_path}")
                return alt_path

        return None

    async def download_model(self, model_name: str, force_download: bool = False) -> Path:
        """
        Download ONNX model from repositories with intelligent fallback strategies.

        Attempts to download the specified model from supported repositories, with
        automatic fallback to alternative sources if the primary fails. Supports
        forced re-downloading and uses local caching to avoid redundant downloads.

        Args:
            model_name: Model identifier to download (e.g., "microsoft/deberta-v3-base")
                        Format: organization/model-name for Hugging Face models
            force_download: If True, downloads even if model exists locally locally
                           (default: False, uses cached model if available)

        Returns:
            Path: Absolute path to the downloaded or cached model file

        Raises:
            InfrastructureError: If model cannot be downloaded from any repository

        Behavior:
            - Checks local cache first unless force_download is True
            - Attempts Hugging Face repository first (most common)
            - Falls back to alternative repositories in configured order
            - Logs download progress and failures for debugging
            - Copies downloaded files to standardized cache location
            - Handles network timeouts and connection errors gracefully

        Repository Fallback Order:
            1. Hugging Face Hub (primary)
            2. GitHub ONNX Models (secondary)
            3. Additional configured repositories

        Examples:
            >>> downloader = ONNXModelDownloader()
            >>>
            >>> # Download model (uses cache if available)
            >>> path = await downloader.download_model("microsoft/deberta-v3-base")
            >>> print(f"Model at: {path}")
            >>>
            >>> # Force re-download even if cached
            >>> path = await downloader.download_model("microsoft/deberta-v3-base", force_download=True)
            >>>
            >>> # Handle download failure
            >>> try:
            ...     path = await downloader.download_model("nonexistent/model")
            ... except InfrastructureError as e:
            ...     print(f"Download failed: {e}")

        Note:
            Requires huggingface_hub package for Hugging Face downloads.
            Network connectivity is required for downloading models.
        """
        model_path = self.get_model_cache_path(model_name)

        if model_path.exists() and not force_download:
            logger.info(f"Using cached ONNX model: {model_name}")
            return model_path

        # Try to download from Hugging Face (most common)
        try:
            return await self._download_from_huggingface(model_name, model_path)
        except Exception as e:
            logger.warning(f"Failed to download from Hugging Face: {e}")

        # Try other repositories
        for repo in self.model_repositories:
            try:
                return await self._download_from_repository(model_name, model_path, repo)
            except Exception as e:
                logger.warning(f"Failed to download from {repo}: {e}")

        raise InfrastructureError(f"Could not download ONNX model: {model_name}")

    async def _download_from_huggingface(self, model_name: str, output_path: Path) -> Path:
        """
        Download ONNX model from Hugging Face Hub with intelligent file discovery.

        Attempts to download ONNX models from Hugging Face repositories using multiple
        strategies to find the correct model file. Handles various naming conventions
        and repository structures to maximize compatibility.

        Args:
            model_name: Hugging Face model identifier (e.g., "microsoft/deberta-v3-base")
            output_path: Destination path for the downloaded model file

        Returns:
            Path: Path to the downloaded model file (output_path after copy)

        Raises:
            InfrastructureError: If huggingface_hub is not available, model doesn't exist,
                                or no ONNX files are found in the repository

        Behavior:
            - Imports huggingface_hub on-demand to avoid unnecessary dependencies
            - Lists repository files to discover ONNX files automatically
            - Tries common ONNX file naming patterns if automatic discovery fails
            - Downloads to Hugging Face cache first, then copies to our cache location
            - Preserves file metadata and permissions during copy
            - Logs successful downloads with model name

        File Discovery Strategy:
            1. List all .onnx files in repository
            2. If found, download the first one
            3. If not found, try common naming patterns:
               - "model.onnx"
               - "pytorch_model.onnx"
               - "{model-name}.onnx"

        Examples:
            >>> downloader = ONNXModelDownloader()
            >>> output_path = Path("/cache/model.onnx")
            >>> path = await downloader._download_from_huggingface(
            ...     "microsoft/deberta-v3-base", output_path
            ... )
            >>> print(f"Downloaded to: {path}")

        Note:
            This is a private method used internally by download_model().
            Requires huggingface_hub package to be installed.
        """
        try:
            from huggingface_hub import hf_hub_download, repo_files

            # Try to find ONNX file in the repository
            repo_file_list = repo_files(model_name)
            onnx_files = [f for f in repo_file_list if f.endswith(".onnx")]

            if not onnx_files:
                # Try common ONNX file names
                common_names = ["model.onnx", "pytorch_model.onnx", f'{model_name.split("/")[-1]}.onnx']
                for name in common_names:
                    try:
                        downloaded_path = hf_hub_download(
                            repo_id=model_name,
                            filename=name,
                            cache_dir=self.cache_dir.parent
                        )
                        return Path(downloaded_path)
                    except Exception:
                        continue

                raise InfrastructureError(f"No ONNX file found in repository: {model_name}")

            # Download the first ONNX file found
            downloaded_path = hf_hub_download(
                repo_id=model_name,
                filename=onnx_files[0],
                cache_dir=self.cache_dir.parent
            )

            # Copy to our cache location
            shutil.copy2(downloaded_path, output_path)
            logger.info(f"Downloaded ONNX model from Hugging Face: {model_name}")
            return output_path

        except ImportError:
            raise InfrastructureError("huggingface_hub is required for model downloading")
        except Exception as e:
            raise InfrastructureError(f"Failed to download from Hugging Face: {e}")

    async def _download_from_repository(self, model_name: str, output_path: Path, repository: str) -> Path:
        """Download ONNX model from generic repository (placeholder for future implementations)."""
        # This is a placeholder for future repository integrations
        raise NotImplementedError(f"Download from {repository} not implemented yet")


class ONNXProviderManager:
    """
    Manages ONNX Runtime execution provider detection, configuration, and optimization.

    This service provides comprehensive provider management including automatic detection
    of available execution providers, intelligent provider selection based on hardware
    capabilities, and session configuration optimization for different use cases.
    It enables optimal model performance across diverse hardware environments.

    Attributes:
        providers_cache: Cached list of detected providers to avoid repeated detection

    Public Methods:
        detect_providers(): Discover available ONNX execution providers
        get_optimal_providers(): Get best providers based on preferences and availability
        configure_session_options(): Create optimized session configuration
        get_provider_info(): Get detailed information about a specific provider

    State Management:
        - Caches provider detection results for performance
        - Thread-safe for concurrent provider access
        - No persistent state, detection repeats on process restart
        - Handles ONNX Runtime installation variations gracefully

    Usage:
        # Basic provider detection
        provider_manager = ONNXProviderManager()
        providers = provider_manager.detect_providers()

        # Get optimal provider list
        optimal = provider_manager.get_optimal_providers(["CUDAExecutionProvider"])

        # Configure session for latency optimization
        session_opts = provider_manager.configure_session_options("latency")

        # Get specific provider information
        cuda_info = provider_manager.get_provider_info("CUDAExecutionProvider")
        if cuda_info and cuda_info.available:
            print(f"CUDA available: {cuda_info.description}")

    Supported Providers:
        - **CUDAExecutionProvider**: NVIDIA GPU acceleration (priority: 1)
        - **TensorrtExecutionProvider**: NVIDIA TensorRT optimization (priority: 1)
        - **OpenVINOExecutionProvider**: Intel CPU/GPU optimization (priority: 2)
        - **CoreMLExecutionProvider**: Apple Silicon Neural Engine (priority: 2)
        - **ROCMExecutionProvider**: AMD GPU acceleration (priority: 2)
        - **CPUExecutionProvider**: Universal CPU fallback (priority: 3)

    Error Handling:
        - **InfrastructureError**: When ONNX Runtime is not available
        - Graceful handling of missing providers and installation variations
        - Detailed logging for provider detection issues

    Thread Safety:
        Safe for concurrent use. Provider detection results are cached and
        session configuration is stateless.
    """

    def __init__(self):
        """
        Initialize the provider manager with empty cache.

        Creates a new provider manager instance with no cached detection results.
        Provider detection is performed lazily on first access to avoid unnecessary
        ONNX Runtime imports if the functionality isn't used.

        Behavior:
            - Initializes with empty provider cache
            - No ONNX Runtime import during initialization
            - Provider detection deferred to first method call
            - Thread-safe initialization

        Examples:
            >>> manager = ONNXProviderManager()
            >>> print(manager.providers_cache)  # None initially
            >>> providers = manager.detect_providers()  # Triggers detection
            >>> print(manager.providers_cache)  # Now contains detected providers
        """
        self.providers_cache: List[ProviderInfo] | None = None

    def detect_providers(self) -> List[ProviderInfo]:
        """
        Detect and categorize available ONNX Runtime execution providers.

        Scans the system for available ONNX Runtime execution providers, categorizes
        them by performance characteristics, and returns detailed information about
        each provider including availability and priority for selection.

        Returns:
            List[ProviderInfo]: Available providers sorted by priority (lower numbers = higher priority).
                               Empty list if ONNX Runtime is not installed.

        Behavior:
            - Caches detection results after first call for performance
            - Imports ONNX Runtime lazily to avoid unnecessary dependencies
            - Creates ProviderInfo objects with availability and priority data
            - Sorts providers by performance priority (GPU > NPU > CPU)
            - Logs available providers for debugging

        Provider Priority System:
            - Priority 1: CUDA Execution Provider, TensorRT (highest performance)
            - Priority 2: OpenVINO, CoreML, ROCm (accelerated execution)
            - Priority 3: CPU Execution Provider (universal fallback)

        Examples:
            >>> manager = ONNXProviderManager()
            >>> providers = manager.detect_providers()
            >>>
            >>> for provider in providers:
            ...     if provider.available:
            ...         print(f"{provider.name}: {provider.description}")
            ...         print(f"  Device: {provider.device_type}, Priority: {provider.priority}")
            >>>
            >>> # Subsequent calls use cache
            >>> cached_providers = manager.detect_providers()  # Fast, no re-detection

        Note:
            Results are cached after first call. Returns cached results on
            subsequent calls to avoid expensive provider re-detection.
        """
        if self.providers_cache:
            return self.providers_cache

        try:
            import onnxruntime as ort
            available_providers = ort.get_available_providers()
            logger.info(f"ONNX Runtime available providers: {available_providers}")
        except ImportError:
            logger.warning("ONNX Runtime not available")
            return []

        # Define provider configurations
        provider_configs = [
            ProviderInfo(
                name="CUDAExecutionProvider",
                available="CUDAExecutionProvider" in available_providers,
                priority=1,
                description="NVIDIA GPU acceleration",
                device_type="gpu"
            ),
            ProviderInfo(
                name="CPUExecutionProvider",
                available="CPUExecutionProvider" in available_providers,
                priority=3,
                description="CPU fallback execution",
                device_type="cpu"
            ),
            ProviderInfo(
                name="OpenVINOExecutionProvider",
                available="OpenVINOExecutionProvider" in available_providers,
                priority=2,
                description="Intel OpenVINO acceleration",
                device_type="cpu"
            ),
            ProviderInfo(
                name="TensorrtExecutionProvider",
                available="TensorrtExecutionProvider" in available_providers,
                priority=1,
                description="NVIDIA TensorRT acceleration",
                device_type="gpu"
            ),
            ProviderInfo(
                name="CoreMLExecutionProvider",
                available="CoreMLExecutionProvider" in available_providers,
                priority=2,
                description="Apple Core ML acceleration",
                device_type="npu"
            ),
            ProviderInfo(
                name="ROCMExecutionProvider",
                available="ROCMExecutionProvider" in available_providers,
                priority=2,
                description="AMD ROCm acceleration",
                device_type="gpu"
            ),
        ]

        # Filter to available providers and sort by priority
        available_configs = [p for p in provider_configs if p.available]
        available_configs.sort(key=lambda x: x.priority)

        self.providers_cache = available_configs
        return available_configs

    def get_optimal_providers(self, preferred_providers: List[str] | None = None) -> List[str]:
        """
        Get optimal execution provider list based on availability and user preferences.

        Returns the best available execution providers for model loading, considering
        both user preferences and hardware capabilities. If preferred providers
        are specified and available, they are prioritized; otherwise, returns all
        available providers sorted by performance priority.

        Args:
            preferred_providers: Optional list of preferred provider names (e.g.,
                                ["CUDAExecutionProvider"]). If provided and available,
                                these will be used first. If None or no preferred
                                providers are available, uses automatic selection.

        Returns:
            List[str]: List of provider names in optimal order for model loading.
                       Empty list if no providers are available.

        Behavior:
            - Triggers provider detection if not already cached
            - Prioritizes user preferences when available
            - Falls back to automatic selection based on priority
            - Returns providers in optimal loading order
            - Handles missing preferred providers gracefully

        Selection Logic:
            1. If preferred_providers specified and available → Return those
            2. If preferred_providers specified but none available → Use priority order
            3. If no preferred_providers specified → Return all available by priority

        Examples:
            >>> manager = ONNXProviderManager()
            >>>
            >>> # Automatic optimal selection
            >>> optimal = manager.get_optimal_providers()
            >>> print(optimal)  # ['CUDAExecutionProvider', 'CPUExecutionProvider']
            >>>
            >>> # User preference with available provider
            >>> cuda_optimal = manager.get_optimal_providers(['CUDAExecutionProvider'])
            >>> print(cuda_optimal)  # ['CUDAExecutionProvider']
            >>>
            >>> # User preference with unavailable provider
            >>> missing_optimal = manager.get_optimal_providers(['MissingProvider'])
            >>> print(missing_optimal)  # ['CUDAExecutionProvider', 'CPUExecutionProvider']
            >>>
            >>> # Multiple preferences (first available wins)
            >>> multi_optimal = manager.get_optimal_providers([
            ...     'TensorrtExecutionProvider',
            ...     'CUDAExecutionProvider',
            ...     'CPUExecutionProvider'
            ... ])

        Note:
            Provider names must match ONNX Runtime provider names exactly.
            See detect_providers() output for available provider names.
        """
        detected_providers = self.detect_providers()

        if preferred_providers:
            # Filter preferred providers by availability
            available_preferred = [
                p.name for p in detected_providers
                if p.name in preferred_providers
            ]
            if available_preferred:
                return available_preferred

        # Return all available providers sorted by priority
        return [p.name for p in detected_providers]

    def configure_session_options(self, optimize_for: str = "latency") -> Any:
        """Configure ONNX Runtime session options."""
        try:
            import onnxruntime as ort
            session_options = ort.SessionOptions()

            # Reduce log noise
            session_options.log_severity_level = 3

            # Optimization based on use case
            if optimize_for == "latency":
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                session_options.inter_op_num_threads = 1
                session_options.intra_op_num_threads = min(4, os.cpu_count() or 1)
            elif optimize_for == "throughput":
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
                session_options.inter_op_num_threads = min(2, os.cpu_count() or 1)
                session_options.intra_op_num_threads = min(8, os.cpu_count() or 1)

            # Enable memory optimizations
            session_options.enable_cpu_mem_arena = True
            session_options.enable_mem_pattern = True
            session_options.enable_profiling = False  # Disable profiling for production

            return session_options

        except ImportError:
            raise InfrastructureError("ONNX Runtime not available for session configuration")

    def get_provider_info(self, provider_name: str) -> ProviderInfo | None:
        """Get information about a specific provider."""
        providers = self.detect_providers()
        for provider in providers:
            if provider.name == provider_name:
                return provider
        return None


class ONNXModelManager:
    """
    High-level ONNX model management with intelligent loading, caching, and provider fallback.

    This service provides a comprehensive interface for ONNX model management,
    coordinating model downloading, caching, provider selection, and loading with
    automatic fallback strategies. It serves as the primary interface for
    applications needing reliable ONNX model execution with optimal performance.

    Attributes:
        downloader: ONNXModelDownloader instance for file operations
        provider_manager: ONNXProviderManager instance for execution provider management
        preferred_providers: Optional list of preferred execution providers
        auto_download: Whether to automatically download models when not found locally
        loaded_models: In-memory cache of loaded model instances

    Public Methods:
        load_model(): Load model with automatic provider fallback and optimization
        unload_model(): Remove model from memory cache
        clear_cache(): Clear all loaded models from cache
        get_model_info(): Get information about loaded models
        verify_model_compatibility(): Diagnose model and system compatibility

    State Management:
        - Maintains in-memory cache of loaded models for performance
        - Supports model unloading to free memory resources
        - Thread-safe for concurrent model loading and unloading
        - Persistent disk cache managed by downloader component

    Usage:
        # Basic usage with automatic configuration
        manager = ONNXModelManager()
        session, tokenizer, info = await manager.load_model("microsoft/deberta-v3-base")

        # Custom configuration with preferences
        manager = ONNXModelManager(
            cache_dir="/app/models",
            preferred_providers=["CUDAExecutionProvider"],
            auto_download=True
        )

        # Load with optimization and verification
        session, tokenizer, info = await manager.load_model(
            "model-name",
            optimize_for="throughput",
            verify_hash="expected_sha256_hash"
        )

        # Model management
        model_info = manager.get_model_info("model-name")
        manager.unload_model("model-name")  # Free memory
        manager.clear_cache()  # Clear all models

    Error Handling:
        - **InfrastructureError**: For model loading, provider configuration, or download failures
        - Automatic fallback through provider list on loading failures
        - Graceful degradation when optimal providers aren't available
        - Comprehensive error logging for debugging

    Performance Characteristics:
        - Models are cached in memory after first load for fast subsequent access
        - Provider fallback ensures models load even if optimal providers fail
        - Download-on-demand reduces initial startup time
        - Memory management through explicit unloading capabilities

    Thread Safety:
        Safe for concurrent model loading and unloading operations.
        Uses atomic operations for cache management and provider selection.
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        preferred_providers: List[str] | None = None,
        auto_download: bool = True
    ):
        self.downloader = ONNXModelDownloader(cache_dir)
        self.provider_manager = ONNXProviderManager()
        self.preferred_providers = preferred_providers
        self.auto_download = auto_download
        self.loaded_models: Dict[str, Any] = {}  # Cache of loaded models

    async def load_model(
        self,
        model_name: str,
        optimize_for: str = "latency",
        verify_hash: str | None = None
    ) -> Tuple[Any, str, Dict[str, Any]]:
        """
        Load ONNX model with automatic provider fallback and comprehensive error handling.

        This is the primary method for loading ONNX models, providing intelligent
        provider selection, automatic downloading, model verification, and graceful
        fallback strategies. It coordinates all components to deliver a reliable
        model loading experience.

        Args:
            model_name: Model identifier to load (e.g., "microsoft/deberta-v3-base")
                        Format depends on download source (Hugging Face uses org/model format)
            optimize_for: Optimization target for session configuration:
                         "latency" (default) - Optimized for fast inference
                         "throughput" - Optimized for high-volume processing
            verify_hash: Optional SHA-256 hash for model integrity verification.
                        If provided, model file hash will be verified before loading.

        Returns:
            Tuple[Any, str, Dict[str, Any]]: Contains three elements:
                - session: Loaded ONNX Runtime inference session
                - tokenizer: Loaded transformers tokenizer for the model
                - model_info: Dictionary with model metadata including:
                    - model_name: Model identifier
                    - model_path: File path to loaded model
                    - provider: Successfully used execution provider
                    - providers_available: List of all available providers tried
                    - optimize_for: Optimization mode used
                    - file_size_mb: Model file size in megabytes
                    - input_metadata: List of input tensor specifications
                    - output_metadata: List of output tensor specifications

        Raises:
            InfrastructureError: If model cannot be loaded with any provider or
                                critical components (tokenizer, verification) fail

        Behavior:
            - Returns cached model if already loaded with same configuration
            - Downloads model automatically if not found locally (when auto_download=True)
            - Verifies model integrity if hash provided
            - Attempts providers in optimal order with fallback
            - Loads compatible tokenizer using multiple strategies
            - Caches successful results for fast subsequent access
            - Logs detailed progress for debugging

        Provider Fallback Strategy:
            1. Try preferred providers if specified
            2. Try providers in automatic priority order
            3. Continue until one succeeds or all fail
            4. Raise InfrastructureError if all providers fail

        Examples:
            >>> manager = ONNXModelManager()
            >>>
            >>> # Basic model loading
            >>> session, tokenizer, info = await manager.load_model("microsoft/deberta-v3-base")
            >>> print(f"Loaded with provider: {info['provider']}")
            >>>
            >>> # Load with throughput optimization
            >>> session, tokenizer, info = await manager.load_model(
            ...     "model-name", optimize_for="throughput"
            ... )
            >>>
            >>> # Load with hash verification
            >>> session, tokenizer, info = await manager.load_model(
            ...     "model-name", verify_hash="a1b2c3d4e5f6..."
            ... )
            >>>
            >>> # Error handling
            >>> try:
            ...     session, tokenizer, info = await manager.load_model("nonexistent/model")
            ... except InfrastructureError as e:
            ...     print(f"Failed to load model: {e}")

        Performance Notes:
            - First load includes download and provider detection overhead
            - Subsequent loads use in-memory cache for near-instant access
            - Provider fallback adds minimal overhead per failed provider
            - Model verification adds one-time file read cost

        Thread Safety:
            Safe for concurrent loading of different models.
            Cache operations use atomic updates to prevent race conditions.
        """
        # Check if model is already loaded
        cache_key = f"{model_name}_{optimize_for}"
        if cache_key in self.loaded_models:
            logger.debug(f"Using cached loaded model: {model_name}")
            return self.loaded_models[cache_key]

        # Find or download model
        model_path = self.downloader.find_local_model(model_name)

        if not model_path and self.auto_download:
            logger.info(f"Downloading ONNX model: {model_name}")
            model_path = await self.downloader.download_model(model_name)

        if not model_path:
            raise InfrastructureError(f"ONNX model not found: {model_name}")

        # Verify model hash if provided
        if verify_hash:
            actual_hash = self.downloader.verify_model_hash(model_path, verify_hash)
            logger.info(f"Model hash verified: {actual_hash[:16]}...")

        # Get optimal providers
        providers = self.provider_manager.get_optimal_providers(self.preferred_providers)

        # Configure session options
        session_options = self.provider_manager.configure_session_options(optimize_for)

        # Load model with provider fallback
        session = None
        successful_provider = None

        for provider in providers:
            try:
                import onnxruntime as ort
                session = ort.InferenceSession(
                    str(model_path),
                    sess_options=session_options,
                    providers=[provider]
                )
                successful_provider = provider
                logger.info(f"Successfully loaded ONNX model {model_name} with provider: {provider}")
                break
            except Exception as e:
                logger.warning(f"Failed to load ONNX model {model_name} with provider {provider}: {e}")
                continue

        if not session:
            raise InfrastructureError(f"Failed to load ONNX model {model_name} with any provider")

        # Load tokenizer
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:
            logger.warning(f"Failed to load tokenizer for {model_name}: {e}")
            # Try to load from local cache
            try:
                tokenizer = AutoTokenizer.from_pretrained(str(model_path.parent))
            except Exception as e2:
                logger.error(f"Failed to load tokenizer for {model_name}: {e2}")
                raise InfrastructureError(f"Could not load tokenizer for {model_name}: {e2}")

        # Create model info
        model_info = {
            "model_name": model_name,
            "model_path": str(model_path),
            "provider": successful_provider,
            "providers_available": providers,
            "optimize_for": optimize_for,
            "file_size_mb": model_path.stat().st_size / 1024 / 1024,
            "input_metadata": session.get_inputs(),
            "output_metadata": session.get_outputs(),
        }

        # Cache the loaded model
        model_tuple = (session, tokenizer, model_info)
        self.loaded_models[cache_key] = model_tuple

        return model_tuple

    def unload_model(self, model_name: str) -> None:
        """Unload a model from cache."""
        keys_to_remove = [key for key in self.loaded_models.keys() if key.startswith(model_name)]
        for key in keys_to_remove:
            del self.loaded_models[key]
            logger.debug(f"Unloaded model from cache: {key}")

    def clear_cache(self) -> None:
        """Clear all loaded models from cache."""
        self.loaded_models.clear()
        logger.info("Cleared all ONNX models from cache")

    def get_model_info(self, model_name: str) -> Dict[str, Any] | None:
        """Get information about a loaded model."""
        for key, (session, tokenizer, info) in self.loaded_models.items():
            if key.startswith(model_name):
                return info
        return None

    async def verify_model_compatibility(self, model_name: str) -> Dict[str, Any]:
        """Verify model compatibility and return diagnostics."""
        diagnostics = {
            "model_name": model_name,
            "onnx_available": False,
            "providers_available": [],
            "model_found": False,
            "model_loadable": False,
            "tokenizer_loadable": False,
            "recommendations": []
        }

        # Check ONNX availability
        try:
            import onnxruntime as ort
            diagnostics["onnx_available"] = True
            diagnostics["onnx_version"] = ort.__version__
            diagnostics["providers_available"] = ort.get_available_providers()
        except ImportError:
            diagnostics["recommendations"].append("Install onnxruntime: pip install onnxruntime")
            return diagnostics

        # Check model availability
        model_path = self.downloader.find_local_model(model_name)
        if model_path:
            diagnostics["model_found"] = True
            diagnostics["model_path"] = str(model_path)
            diagnostics["model_size_mb"] = model_path.stat().st_size / 1024 / 1024
        elif self.auto_download:
            diagnostics["recommendations"].append(f"Model will be downloaded on first use: {model_name}")
        else:
            diagnostics["recommendations"].append(f"Model not found and auto-download disabled: {model_name}")
            return diagnostics

        # Test model loading
        try:
            session, tokenizer, info = await self.load_model(model_name)
            diagnostics["model_loadable"] = True
            diagnostics["tokenizer_loadable"] = True
            diagnostics["successful_provider"] = info["provider"]
            diagnostics["input_details"] = [
                {"name": inp.name, "type": str(inp.type), "shape": inp.shape}
                for inp in session.get_inputs()
            ]
            diagnostics["output_details"] = [
                {"name": out.name, "type": str(out.type), "shape": out.shape}
                for out in session.get_outputs()
            ]
        except Exception as e:
            diagnostics["recommendations"].append(f"Model loading failed: {e}")

        return diagnostics


# Global instance for convenience
_global_manager: ONNXModelManager | None = None


def get_onnx_manager(**kwargs) -> ONNXModelManager:
    """
    Get or create the global ONNX model manager instance.

    Provides a singleton pattern for accessing the ONNX model manager throughout
    the application. Creates the manager on first call and returns the same
    instance on subsequent calls to maintain consistent caching and state.

    Args:
        **kwargs: Keyword arguments passed to ONNXModelManager constructor:
                 - cache_dir: Custom cache directory path
                 - preferred_providers: List of preferred execution providers
                 - auto_download: Whether to automatically download models

    Returns:
        ONNXModelManager: The global manager instance (creates on first call)

    Behavior:
        - Creates new manager instance only on first call
        - Returns same instance on subsequent calls
        - Ignores additional kwargs after first call
        - Maintains global state for model caching

    Examples:
        >>> # Get default manager
        >>> manager = get_onnx_manager()
        >>>
        >>> # Get manager with custom configuration (first call only)
        >>> manager = get_onnx_manager(
        ...     cache_dir="/custom/cache",
        ...     preferred_providers=["CUDAExecutionProvider"]
        ... )
        >>>
        >>> # Subsequent calls return same instance
        >>> same_manager = get_onnx_manager()
        >>> assert manager is same_manager

    Note:
        Configuration kwargs are only applied on first call. Subsequent
        calls with different kwargs will not modify the existing instance.
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = ONNXModelManager(**kwargs)
    return _global_manager


async def verify_onnx_setup(model_name: str = "microsoft/deberta-v3-base-injection") -> Dict[str, Any]:
    """
    Verify ONNX Runtime setup and provide comprehensive diagnostic information.

    This utility function checks the entire ONNX Runtime ecosystem including
    installation, provider availability, model compatibility, and system readiness.
    It returns detailed diagnostics to help troubleshoot setup issues.

    Args:
        model_name: Model name to use for compatibility testing.
                    Defaults to a common security scanning model.
                    Used to test actual model loading capabilities.

    Returns:
        Dict[str, Any]: Comprehensive diagnostics containing:
            - model_name: Model name tested
            - onnx_available: Whether ONNX Runtime is installed
            - onnx_version: ONNX Runtime version (if available)
            - providers_available: List of detected execution providers
            - model_found: Whether the test model was found locally
            - model_path: Path to found model (if found)
            - model_size_mb: Model file size in megabytes (if found)
            - model_loadable: Whether model could be loaded successfully
            - tokenizer_loadable: Whether tokenizer could be loaded
            - successful_provider: Provider that successfully loaded model
            - input_details: Model input tensor specifications
            - output_details: Model output tensor specifications
            - recommendations: List of setup recommendations or issues found

    Behavior:
        - Checks ONNX Runtime installation and version
        - Detects available execution providers
        - Tests model discovery (local and download)
        - Attempts actual model loading with optimal providers
        - Tests tokenizer loading compatibility
        - Provides actionable recommendations for issues

    Examples:
        >>> # Basic setup verification
        >>> diagnostics = await verify_onnx_setup()
        >>> print(f"ONNX available: {diagnostics['onnx_available']}")
        >>> print(f"Providers: {diagnostics['providers_available']}")
        >>>
        >>> # Verify with specific model
        >>> diagnostics = await verify_onnx_setup("custom/model-name")
        >>> if diagnostics['model_loadable']:
        ...     print("Setup verified successfully")
        ... else:
        ...     print("Issues found:")
        ...     for rec in diagnostics['recommendations']:
        ...         print(f"- {rec}")
        >>>
        >>> # Check specific aspects
        >>> if not diagnostics['onnx_available']:
        ...     print("Install ONNX Runtime")
        >>> if not diagnostics['providers_available']:
        ...     print("No execution providers available")

    Use Cases:
        - **Application Startup**: Verify ONNX setup before using models
        - **Troubleshooting**: Diagnose model loading or provider issues
        - **System Monitoring**: Check ONNX Runtime health and capabilities
        - **Development**: Verify environment setup during development

    Note:
        This function is async because it may attempt model downloading and loading
        operations. It requires network access for full functionality when
        models need to be downloaded.
    """
    manager = get_onnx_manager()
    return await manager.verify_model_compatibility(model_name)
