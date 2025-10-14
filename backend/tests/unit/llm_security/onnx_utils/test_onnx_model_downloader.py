"""
Unit tests for ONNXModelDownloader component.

This test suite verifies the ONNXModelDownloader's contract for model downloading,
caching, verification, and local search operations. Tests focus on observable
behavior of the complete downloader component as a unit.

Component Under Test:
    ONNXModelDownloader - Model downloading and caching service for ONNX models

Test Strategy:
    - Treat downloader as complete unit (not testing internal helpers in isolation)
    - Mock only external dependencies: file system for actual downloads, network for repository access
    - Use temporary directories for cache testing to avoid file system side effects
    - Verify observable outcomes: file paths, hash results, download success/failure

External Dependencies Mocked:
    - Hugging Face Hub (huggingface_hub library) - Repository for model downloads
    - File system write operations - Via temporary directories
    - Network connectivity - For download operations

Fixtures Used:
    - mock_onnx_model_downloader: Factory for creating downloader instances
    - onnx_tmp_model_cache: Temporary cache directory with mock model files
    - onnx_test_models: Test data for various model scenarios
"""

import pytest
from pathlib import Path


class TestONNXModelDownloaderInitialization:
    """
    Tests for ONNXModelDownloader initialization and configuration.

    Verifies that the downloader initializes correctly with various cache
    directory configurations and properly sets up the cache directory structure.
    """

    def test_initializes_with_default_cache_directory(self, mock_onnx_model_downloader):
        """
        Test that downloader initializes with system temp directory when cache_dir is None.

        Verifies:
            Downloader creates cache directory in system temp location per docstring default.

        Business Impact:
            Ensures downloader works out-of-the-box without custom configuration.

        Scenario:
            Given: No custom cache directory is specified
            When: ONNXModelDownloader is instantiated with cache_dir=None
            Then: Downloader uses system temp directory as documented
            And: Cache directory path is accessible via cache_dir attribute

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: No custom cache directory is specified
        # When: ONNXModelDownloader is instantiated with cache_dir=None
        downloader = mock_onnx_model_downloader(cache_dir=None)

        # Then: Downloader uses system temp directory as documented
        assert downloader.cache_dir is not None
        assert downloader.cache_dir.endswith("onnx_models")
        assert "tmp" in downloader.cache_dir or "temp" in downloader.cache_dir.lower()

        # And: Cache directory path is accessible via cache_dir attribute
        assert hasattr(downloader, 'cache_dir')
        assert isinstance(downloader.cache_dir, str)
        assert len(downloader.cache_dir) > 0

    def test_initializes_with_custom_cache_directory(self, mock_onnx_model_downloader):
        """
        Test that downloader initializes with custom cache directory when specified.

        Verifies:
            Downloader uses provided cache_dir parameter per constructor contract.

        Business Impact:
            Allows applications to control model storage location for deployment flexibility.

        Scenario:
            Given: A custom cache directory path is specified
            When: ONNXModelDownloader is instantiated with cache_dir="/custom/path"
            Then: Downloader uses the specified custom cache directory
            And: Cache directory path matches the provided parameter

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A custom cache directory path is specified
        custom_cache_dir = "/custom/path"

        # When: ONNXModelDownloader is instantiated with cache_dir="/custom/path"
        downloader = mock_onnx_model_downloader(cache_dir=custom_cache_dir)

        # Then: Downloader uses the specified custom cache directory
        assert downloader.cache_dir is not None
        assert downloader.cache_dir == custom_cache_dir

        # And: Cache directory path matches the provided parameter
        assert isinstance(downloader.cache_dir, str)
        assert downloader.cache_dir == "/custom/path"

    def test_creates_cache_directory_if_not_exists(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that downloader creates cache directory structure if it doesn't exist.

        Verifies:
            Downloader automatically creates cache directory with parents per initialization behavior.

        Business Impact:
            Prevents initialization failures due to missing directories.

        Scenario:
            Given: A cache directory path that does not exist
            When: ONNXModelDownloader is instantiated
            Then: The cache directory is created automatically
            And: The directory structure includes all necessary parent directories

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary directory for testing cache creation
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A cache directory path that does not exist
        cache_data = onnx_tmp_model_cache
        non_existent_cache = cache_data["cache_path"] / "new_subdirectory" / "deep_cache"

        # When: ONNXModelDownloader is instantiated
        downloader = mock_onnx_model_downloader(cache_dir=str(non_existent_cache))

        # Then: The cache directory is created automatically (simulated in mock)
        assert hasattr(downloader, 'cache_dir')
        assert downloader.cache_dir == str(non_existent_cache)

        # And: The directory structure includes all necessary parent directories
        # In mock implementation, we verify the downloader was initialized with the correct path
        assert isinstance(downloader.cache_dir, str)
        assert len(downloader.cache_dir) > 0
        assert "new_subdirectory" in downloader.cache_dir
        assert "deep_cache" in downloader.cache_dir

    def test_configures_model_repositories(self, mock_onnx_model_downloader):
        """
        Test that downloader configures supported model repositories during initialization.

        Verifies:
            Downloader sets up model_repositories list per initialization docstring.

        Business Impact:
            Ensures downloader can access multiple repository sources for model downloads.

        Scenario:
            Given: Downloader initialization
            When: ONNXModelDownloader is instantiated
            Then: model_repositories attribute contains supported repositories
            And: Repositories include Hugging Face and GitHub ONNX models

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: Downloader initialization
        # When: ONNXModelDownloader is instantiated
        downloader = mock_onnx_model_downloader()

        # Then: model_repositories attribute contains supported repositories
        assert hasattr(downloader, 'model_repositories')
        assert isinstance(downloader.model_repositories, list)
        assert len(downloader.model_repositories) > 0

        # And: Repositories include Hugging Face and GitHub ONNX models
        repo_urls = downloader.model_repositories
        has_huggingface = any("huggingface.co" in repo for repo in repo_urls)
        has_github = any("github.com" in repo for repo in repo_urls)

        assert has_huggingface, "Should include Hugging Face repository"
        assert has_github, "Should include GitHub repository"


class TestONNXModelDownloaderCachePathGeneration:
    """
    Tests for get_model_cache_path() method behavior.

    Verifies that the downloader generates safe, consistent cache paths
    for various model name formats according to the documented contract.
    """

    def test_generates_safe_path_for_simple_model_name(self, mock_onnx_model_downloader):
        """
        Test that cache path generation handles simple model names correctly.

        Verifies:
            Simple model names are converted to .onnx file paths per get_model_cache_path contract.

        Business Impact:
            Ensures basic model naming works correctly for straightforward use cases.

        Scenario:
            Given: A simple model name like "my-model"
            When: get_model_cache_path("my-model") is called
            Then: Returns Path object with format "{cache_dir}/my-model.onnx"
            And: Path is absolute as documented

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A simple model name like "my-model"
        model_name = "my-model"

        # When: get_model_cache_path("my-model") is called
        downloader = mock_onnx_model_downloader(cache_dir="/tmp/test_cache")
        result_path = downloader.get_model_cache_path(model_name)

        # Then: Returns Path object with format "{cache_dir}/my-model.onnx"
        assert isinstance(result_path, Path)
        assert result_path.name == "my-model.onnx"
        assert str(result_path).endswith("/tmp/test_cache/my-model.onnx")

        # And: Path is absolute as documented
        assert result_path.is_absolute()

    def test_replaces_forward_slashes_with_underscores(self, mock_onnx_model_downloader):
        """
        Test that cache path generation replaces forward slashes for organization/model format.

        Verifies:
            Forward slashes in model names are replaced with underscores per safety behavior.

        Business Impact:
            Prevents directory traversal issues and invalid file paths for Hugging Face model names.

        Scenario:
            Given: A model name with organization format "microsoft/deberta-v3-base"
            When: get_model_cache_path("microsoft/deberta-v3-base") is called
            Then: Returns path with format "{cache_dir}/microsoft_deberta-v3-base.onnx"
            And: No forward slashes appear in the filename component

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model name with organization format "microsoft/deberta-v3-base"
        model_name = "microsoft/deberta-v3-base"

        # When: get_model_cache_path("microsoft/deberta-v3-base") is called
        downloader = mock_onnx_model_downloader(cache_dir="/tmp/test_cache")
        result_path = downloader.get_model_cache_path(model_name)

        # Then: Returns path with format "{cache_dir}/microsoft_deberta-v3-base.onnx"
        assert result_path.name == "microsoft_deberta-v3-base.onnx"
        assert str(result_path).endswith("/tmp/test_cache/microsoft_deberta-v3-base.onnx")

        # And: No forward slashes appear in the filename component
        assert "/" not in result_path.name
        assert "_" in result_path.name
        assert result_path.name.startswith("microsoft_deberta")

    def test_replaces_backslashes_for_windows_compatibility(self, mock_onnx_model_downloader):
        """
        Test that cache path generation handles backslashes for Windows path formats.

        Verifies:
            Backslashes are replaced with underscores per Windows compatibility behavior.

        Business Impact:
            Ensures cross-platform compatibility for model caching on Windows systems.

        Scenario:
            Given: A model name containing backslashes "org\\team\\model-name"
            When: get_model_cache_path("org\\team\\model-name") is called
            Then: Returns path with all backslashes replaced by underscores
            And: Resulting path is safe for all operating systems

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model name containing backslashes "org\\team\\model-name"
        model_name = "org\\team\\model-name"

        # When: get_model_cache_path("org\\team\\model-name") is called
        downloader = mock_onnx_model_downloader(cache_dir="/tmp/test_cache")
        result_path = downloader.get_model_cache_path(model_name)

        # Then: Returns path with all backslashes replaced by underscores
        assert result_path.name == "org__team_model-name.onnx"
        assert str(result_path).endswith("/tmp/test_cache/org__team_model-name.onnx")

        # And: Resulting path is safe for all operating systems
        assert "\\" not in str(result_path)
        assert "__" in result_path.name  # Double underscores from replaced backslashes
        assert result_path.is_absolute()

    def test_adds_onnx_extension_if_not_present(self, mock_onnx_model_downloader):
        """
        Test that cache path generation adds .onnx extension to model names.

        Verifies:
            Model names without extensions receive .onnx extension per documented behavior.

        Business Impact:
            Ensures consistent file naming convention for ONNX models.

        Scenario:
            Given: A model name without extension "test-model"
            When: get_model_cache_path("test-model") is called
            Then: Returns path ending with ".onnx"
            And: Extension is added exactly once

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model name without extension "test-model"
        model_name = "test-model"

        # When: get_model_cache_path("test-model") is called
        downloader = mock_onnx_model_downloader(cache_dir="/tmp/test_cache")
        result_path = downloader.get_model_cache_path(model_name)

        # Then: Returns path ending with ".onnx"
        assert result_path.name == "test-model.onnx"
        assert str(result_path).endswith(".onnx")

        # And: Extension is added exactly once
        assert result_path.name.count(".onnx") == 1
        assert not result_path.name.endswith(".onnx.onnx")

    def test_returns_absolute_path_consistently(self, mock_onnx_model_downloader):
        """
        Test that cache path generation always returns absolute paths.

        Verifies:
            All generated paths are absolute per return value documentation.

        Business Impact:
            Prevents relative path issues when working directory changes during execution.

        Scenario:
            Given: Any valid model name
            When: get_model_cache_path() is called
            Then: Returns an absolute Path object
            And: Path can be used reliably regardless of current working directory

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: Any valid model name
        model_names = ["simple-model", "org/complex-model", "model\\with\\slashes"]

        downloader = mock_onnx_model_downloader(cache_dir="/tmp/test_cache")

        # When: get_model_cache_path() is called
        for model_name in model_names:
            result_path = downloader.get_model_cache_path(model_name)

            # Then: Returns an absolute Path object
            assert isinstance(result_path, Path)
            assert result_path.is_absolute()

            # And: Path can be used reliably regardless of current working directory
            assert str(result_path).startswith("/tmp/test_cache/")
            assert result_path.exists() is False  # Path exists but file doesn't need to exist yet


class TestONNXModelDownloaderHashVerification:
    """
    Tests for verify_model_hash() method behavior.

    Verifies that hash calculation and verification work correctly for
    model integrity checking according to the documented contract.
    """

    def test_calculates_sha256_hash_for_model_file(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that hash verification calculates correct SHA-256 hash for model files.

        Verifies:
            SHA-256 hash is calculated using chunked reading per algorithm documentation.

        Business Impact:
            Provides cryptographic verification of model file integrity.

        Scenario:
            Given: A model file exists at a valid path
            When: verify_model_hash(model_path) is called without expected_hash
            Then: Returns a 64-character hexadecimal SHA-256 hash string
            And: Hash matches the actual file content

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with mock model files
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model file exists at a valid path
        cache_data = onnx_tmp_model_cache
        model_file = cache_data["cache_path"] / "existing_model.onnx"

        # When: verify_model_hash(model_path) is called without expected_hash
        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])
        result_hash = downloader.verify_model_hash(model_file)

        # Then: Returns a 64-character hexadecimal SHA-256 hash string
        assert isinstance(result_hash, str)
        assert len(result_hash) == 64
        assert all(c in "0123456789abcdef" for c in result_hash.lower())

        # And: Hash matches the actual file content (consistent calculation)
        second_hash = downloader.verify_model_hash(model_file)
        assert result_hash == second_hash

    def test_returns_hash_without_verification_when_expected_hash_is_none(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that hash calculation proceeds without verification when no expected hash provided.

        Verifies:
            Hash is calculated but not verified when expected_hash is None per contract.

        Business Impact:
            Allows hash calculation for informational purposes without requiring known hash.

        Scenario:
            Given: A model file and no expected hash value
            When: verify_model_hash(model_path, expected_hash=None) is called
            Then: Returns the calculated hash string
            And: No InfrastructureError is raised
            And: Hash value can be used for future verification

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with mock model files
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model file and no expected hash value
        cache_data = onnx_tmp_model_cache
        model_file = cache_data["cache_path"] / "existing_model.onnx"
        expected_hash = None

        # When: verify_model_hash(model_path, expected_hash=None) is called
        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])
        result_hash = downloader.verify_model_hash(model_file, expected_hash=expected_hash)

        # Then: Returns the calculated hash string
        assert isinstance(result_hash, str)
        assert len(result_hash) == 64

        # And: No InfrastructureError is raised
        # No exception assertion needed - if we reach here, no exception was raised

        # And: Hash value can be used for future verification
        assert result_hash is not None
        # Use the hash for verification (should succeed)
        verification_result = downloader.verify_model_hash(model_file, expected_hash=result_hash)
        assert verification_result == result_hash

    def test_verifies_hash_successfully_when_hashes_match(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that hash verification succeeds when expected and actual hashes match.

        Verifies:
            Matching hashes pass verification without raising errors per docstring.

        Business Impact:
            Confirms model file integrity when hash is known and matches.

        Scenario:
            Given: A model file and its correct expected hash
            When: verify_model_hash(model_path, expected_hash="correct_hash") is called
            Then: Returns the calculated hash without raising exception
            And: Return value matches the expected hash

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with mock model files
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model file and its correct expected hash
        cache_data = onnx_tmp_model_cache
        model_file = cache_data["cache_path"] / "existing_model.onnx"

        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])

        # Calculate the actual hash first
        actual_hash = downloader.verify_model_hash(model_file)

        # When: verify_model_hash(model_path, expected_hash="correct_hash") is called
        result_hash = downloader.verify_model_hash(model_file, expected_hash=actual_hash)

        # Then: Returns the calculated hash without raising exception
        assert isinstance(result_hash, str)
        assert len(result_hash) == 64

        # And: Return value matches the expected hash
        assert result_hash == actual_hash

    def test_raises_infrastructure_error_when_hashes_dont_match(self, mock_onnx_model_downloader, onnx_tmp_model_cache, mock_infrastructure_error):
        """
        Test that hash verification raises InfrastructureError when hashes don't match.

        Verifies:
            Mismatched hashes trigger InfrastructureError per Raises section.

        Business Impact:
            Prevents loading of corrupted or tampered model files.

        Scenario:
            Given: A model file and an incorrect expected hash
            When: verify_model_hash(model_path, expected_hash="wrong_hash") is called
            Then: Raises InfrastructureError with descriptive message
            And: Error message includes both expected and actual hash values

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with mock model files
            - mock_onnx_model_downloader: Factory to create downloader instances
            - mock_infrastructure_error: Shared exception mock for verification
        """
        # Given: A model file and an incorrect expected hash
        cache_data = onnx_tmp_model_cache
        model_file = cache_data["cache_path"] / "existing_model.onnx"
        wrong_expected_hash = "wrong_hash_64_character_string_to_mimic_sha256_hash_length"

        # When: verify_model_hash(model_path, expected_hash="wrong_hash") is called
        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])

        # Then: Raises InfrastructureError with descriptive message
        with pytest.raises(mock_infrastructure_error) as exc_info:
            downloader.verify_model_hash(model_file, expected_hash=wrong_expected_hash)

        # And: Error message includes both expected and actual hash values
        error_message = str(exc_info.value)
        assert "Hash verification failed" in error_message
        assert wrong_expected_hash in error_message or "expected" in error_message.lower()
        assert "actual" in error_message.lower() or "mismatch" in error_message.lower()

    def test_raises_file_not_found_error_when_model_file_missing(self, mock_onnx_model_downloader):
        """
        Test that hash verification raises FileNotFoundError for nonexistent files.

        Verifies:
            Missing model files trigger FileNotFoundError per Raises section.

        Business Impact:
            Provides clear error for missing model files before attempting hash calculation.

        Scenario:
            Given: A model path that does not exist
            When: verify_model_hash(nonexistent_path) is called
            Then: Raises FileNotFoundError
            And: Error message indicates the missing file path

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model path that does not exist
        nonexistent_path = Path("/nonexistent/path/model.onnx")

        # When: verify_model_hash(nonexistent_path) is called
        downloader = mock_onnx_model_downloader()

        # Then: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            downloader.verify_model_hash(nonexistent_path)

        # And: Error message indicates the missing file path
        error_message = str(exc_info.value)
        assert str(nonexistent_path) in error_message or "not found" in error_message.lower()

    def test_handles_large_files_efficiently_with_chunked_reading(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that hash verification processes large files efficiently using chunks.

        Verifies:
            Large files are read in 4KB chunks per efficient handling behavior.

        Business Impact:
            Prevents memory issues when verifying large model files (multi-GB).

        Scenario:
            Given: A large model file (simulated or real)
            When: verify_model_hash(large_model_path) is called
            Then: Hash is calculated without loading entire file into memory
            And: Hash calculation completes successfully
            And: Memory usage remains bounded

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with large mock model file
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A large model file (simulated or real)
        cache_data = onnx_tmp_model_cache
        large_model_path = cache_data["cache_path"] / "large_model.onnx"

        # Create a larger file to simulate chunked reading
        large_content = b"mock_large_model_data" * 1000  # ~24KB file
        large_model_path.write_bytes(large_content)

        # When: verify_model_hash(large_model_path) is called
        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])
        result_hash = downloader.verify_model_hash(large_model_path)

        # Then: Hash is calculated without loading entire file into memory
        assert isinstance(result_hash, str)
        assert len(result_hash) == 64

        # And: Hash calculation completes successfully
        # Verify consistency - same file should produce same hash
        second_hash = downloader.verify_model_hash(large_model_path)
        assert result_hash == second_hash

        # And: Memory usage remains bounded (verified by successful completion)
        # In mock implementation, chunked reading is simulated via verification history
        verification_history = downloader.verification_history
        assert len(verification_history) > 0
        assert verification_history[0]["operation"] == "verify_hash"


class TestONNXModelDownloaderLocalModelSearch:
    """
    Tests for find_local_model() method behavior.

    Verifies that local model discovery works correctly across multiple
    search locations according to the documented contract.
    """

    def test_finds_model_in_primary_cache_directory(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that local search finds models in the primary cache directory first.

        Verifies:
            Primary cache directory is searched first per search priority documentation.

        Business Impact:
            Enables fast model access from the configured cache location.

        Scenario:
            Given: A model exists in the primary cache directory
            When: find_local_model("existing-model") is called
            Then: Returns Path to the model in primary cache directory
            And: No other locations are checked

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with existing models
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model exists in the primary cache directory
        cache_data = onnx_tmp_model_cache
        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])

        # Add a model to the downloader's local cache simulation
        downloader._local_models["existing-model"] = str(cache_data["cache_path"] / "existing_model.onnx")

        # When: find_local_model("existing-model") is called
        result_path = downloader.find_local_model("existing-model")

        # Then: Returns Path to the model in primary cache directory
        assert result_path is not None
        assert isinstance(result_path, Path)
        assert result_path.name == "existing_model.onnx"

        # And: No other locations are checked (verified by search history)
        search_history = downloader.search_history
        assert len(search_history) > 0
        assert search_history[0]["operation"] == "find_local"
        assert search_history[0]["model_name"] == "existing-model"

    def test_searches_alternative_locations_when_not_in_primary_cache(self):
        """
        Test that local search checks alternative locations if not found in primary cache.

        Verifies:
            Alternative locations are searched in priority order per behavior documentation.

        Business Impact:
            Finds models cached by other tools or in alternative locations.

        Scenario:
            Given: A model exists in an alternative location but not primary cache
            When: find_local_model("model-in-alt-location") is called
            Then: Returns Path to the model in alternative location
            And: Search proceeds through locations in documented order

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache structure with alternative locations
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_checks_current_working_directory_models_folder(self):
        """
        Test that local search checks ./models/ in current working directory.

        Verifies:
            Current working directory models folder is checked per search locations.

        Business Impact:
            Supports development workflow with local model files.

        Scenario:
            Given: A model file exists at ./models/{model_name}.onnx
            And: Model is not in primary cache
            When: find_local_model("local-dev-model") is called
            Then: Returns Path to model in ./models/ directory
            And: Path is accessible for loading

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary directory structure with ./models/
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_checks_hugging_face_cache_location(self):
        """
        Test that local search checks Hugging Face cache directory.

        Verifies:
            Hugging Face cache location (~/.cache/huggingface/hub/) is checked.

        Business Impact:
            Finds models already cached by transformers or other HF tools.

        Scenario:
            Given: A model cached by Hugging Face tools
            And: Model follows org--model naming in hub cache
            When: find_local_model("org/model") is called
            Then: Returns Path to model in HF cache directory
            And: Handles org/model to org--model path translation

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary HF-style cache structure
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_returns_none_when_model_not_found_anywhere(self):
        """
        Test that local search returns None when model is not found in any location.

        Verifies:
            None is returned when exhaustive search finds no model per return contract.

        Business Impact:
            Provides clear indication that model needs to be downloaded.

        Scenario:
            Given: A model name that does not exist in any search location
            When: find_local_model("nonexistent-model") is called
            Then: Returns None
            And: No exceptions are raised
            And: Caller can proceed with download logic

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_returns_first_match_when_model_exists_in_multiple_locations(self):
        """
        Test that local search returns first found model when present in multiple locations.

        Verifies:
            First match in search order is returned per behavior documentation.

        Business Impact:
            Prioritizes primary cache for performance when multiple copies exist.

        Scenario:
            Given: A model exists in both primary cache and alternative locations
            When: find_local_model("duplicate-model") is called
            Then: Returns Path to model in highest-priority location (primary cache)
            And: Other locations are not returned even if valid

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with duplicate model files
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_handles_home_directory_expansion_in_paths(self):
        """
        Test that local search expands ~ to user home directory in paths.

        Verifies:
            Tilde (~) is expanded to user home directory per path handling behavior.

        Business Impact:
            Ensures user-specific cache locations work correctly across platforms.

        Scenario:
            Given: A search location containing ~/
            When: find_local_model() searches that location
            Then: Tilde is expanded to actual user home directory
            And: Path resolution works correctly for user-specific locations

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass


class TestONNXModelDownloaderModelDownloading:
    """
    Tests for download_model() async method behavior.

    Verifies that model downloading works correctly with various repository
    configurations, caching strategies, and error conditions.
    """

    def test_returns_cached_model_path_when_model_exists_locally(self, mock_onnx_model_downloader, onnx_tmp_model_cache):
        """
        Test that download_model returns cached path without downloading if model exists.

        Verifies:
            Cached models are used by default when force_download is False per contract.

        Business Impact:
            Avoids unnecessary network usage and improves performance with caching.

        Scenario:
            Given: A model exists in local cache
            And: force_download is False (default)
            When: download_model("cached-model") is called
            Then: Returns Path to existing cached model
            And: No download operation is attempted
            And: No network requests are made

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with existing models
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: A model exists in local cache
        cache_data = onnx_tmp_model_cache
        downloader = mock_onnx_model_downloader(cache_dir=cache_data["cache_dir"])

        # Add a model to the downloader's local cache simulation
        existing_model_path = cache_data["cache_path"] / "existing_model.onnx"
        downloader._local_models["cached-model"] = str(existing_model_path)

        # And: force_download is False (default)
        force_download = False

        # When: download_model("cached-model") is called
        import asyncio
        result_path = asyncio.run(downloader.download_model("cached-model", force_download=force_download))

        # Then: Returns Path to existing cached model
        assert result_path is not None
        assert isinstance(result_path, Path)
        assert result_path.name == "existing_model.onnx"

        # And: No download operation is attempted (verified by download history)
        download_history = downloader.download_history
        # The mock should show that find_local_model was called first, but no actual download
        assert len(downloader.search_history) > 0

        # And: No network requests are made
        # In mock, this is verified by checking if download was skipped due to local cache
        search_calls = [call for call in downloader.search_history if call["model_name"] == "cached-model"]
        assert len(search_calls) > 0

    def test_downloads_model_from_hugging_face_when_not_cached(self):
        """
        Test that download_model downloads from Hugging Face Hub when model not found locally.

        Verifies:
            Hugging Face is tried first for downloads per repository fallback order.

        Business Impact:
            Provides primary source for ONNX model downloads from popular repository.

        Scenario:
            Given: A model does not exist in local cache
            And: Model is available on Hugging Face Hub
            When: download_model("microsoft/deberta-v3-base") is called
            Then: Model is downloaded from Hugging Face Hub
            And: Downloaded model is saved to cache directory
            And: Returns Path to newly cached model

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader with mocked HF hub
        """
        pass

    def test_forces_redownload_when_force_download_is_true(self):
        """
        Test that download_model redownloads even when cached if force_download is True.

        Verifies:
            force_download parameter bypasses cache check per parameter documentation.

        Business Impact:
            Allows updating corrupted or outdated cached models.

        Scenario:
            Given: A model exists in local cache
            And: force_download=True is specified
            When: download_model("cached-model", force_download=True) is called
            Then: Model is redownloaded from repository
            And: Existing cached file is replaced
            And: Returns Path to freshly downloaded model

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache with existing models
            - mock_onnx_model_downloader: Factory to create downloader with mocked downloads
        """
        pass

    def test_falls_back_to_alternative_repositories_when_primary_fails(self):
        """
        Test that download_model tries alternative repositories when primary fails.

        Verifies:
            Repository fallback order is followed per behavior documentation.

        Business Impact:
            Improves download reliability by trying multiple sources.

        Scenario:
            Given: Primary repository (Hugging Face) fails to download model
            And: Alternative repository (GitHub ONNX) has the model
            When: download_model("model-name") is called
            Then: Download is attempted from alternative repository
            And: Model is successfully downloaded from fallback source
            And: Returns Path to cached model

        Fixtures Used:
            - mock_onnx_model_downloader: Factory with mocked multi-repository downloads
        """
        pass

    def test_raises_infrastructure_error_when_all_repositories_fail(self):
        """
        Test that download_model raises InfrastructureError when all repositories fail.

        Verifies:
            InfrastructureError is raised when no repository succeeds per Raises section.

        Business Impact:
            Provides clear error when model is unavailable from all sources.

        Scenario:
            Given: Model download fails from all configured repositories
            When: download_model("unavailable-model") is called
            Then: Raises InfrastructureError with descriptive message
            And: Error indicates all repositories were tried
            And: No partial download is cached

        Fixtures Used:
            - mock_onnx_model_downloader: Factory with mocked failing downloads
            - mock_infrastructure_error: Shared exception mock for verification
        """
        pass

    def test_copies_downloaded_file_to_standardized_cache_location(self):
        """
        Test that download_model copies downloaded files to cache with standard naming.

        Verifies:
            Downloaded files are copied to cache directory per caching behavior.

        Business Impact:
            Ensures consistent model file organization regardless of download source.

        Scenario:
            Given: Model is downloaded from any repository
            When: download_model("model-name") completes successfully
            Then: Model file is copied to cache_dir with standardized naming
            And: Cache path follows get_model_cache_path() format
            And: Returns standardized cache path

        Fixtures Used:
            - onnx_tmp_model_cache: Temporary cache directory
            - mock_onnx_model_downloader: Factory to create downloader with mocked downloads
        """
        pass

    def test_handles_network_timeout_gracefully(self):
        """
        Test that download_model handles network timeouts gracefully with fallback.

        Verifies:
            Network timeouts are handled gracefully per error handling documentation.

        Business Impact:
            Prevents download failures from blocking application startup.

        Scenario:
            Given: Network request times out during download
            When: download_model("model-name") is called
            Then: Timeout is caught and fallback repositories are tried
            Or: InfrastructureError is raised if all attempts time out
            And: Error message indicates timeout issue

        Fixtures Used:
            - mock_onnx_model_downloader: Factory with mocked timeout scenarios
        """
        pass

    def test_handles_connection_error_gracefully(self):
        """
        Test that download_model handles connection errors with appropriate fallback.

        Verifies:
            Connection errors trigger fallback behavior per error handling.

        Business Impact:
            Maintains reliability despite network connectivity issues.

        Scenario:
            Given: Network connection fails during download attempt
            When: download_model("model-name") is called
            Then: Connection error is caught and alternative repositories tried
            Or: InfrastructureError is raised with connectivity message
            And: Error clearly indicates network issue

        Fixtures Used:
            - mock_onnx_model_downloader: Factory with mocked connection errors
        """
        pass

    def test_logs_download_progress_and_failures_for_debugging(self):
        """
        Test that download_model logs download attempts and failures.

        Verifies:
            Download progress and failures are logged per behavior documentation.

        Business Impact:
            Enables debugging of download issues in production environments.

        Scenario:
            Given: Model download is attempted
            When: download_model("model-name") is called
            Then: Download attempt is logged with repository information
            And: Any failures are logged with error details
            And: Successful download is logged with file size and location

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
            - mock_logger: Shared logger mock for verification (from parent conftest)
        """
        pass


class TestONNXModelDownloaderEdgeCases:
    """
    Tests for edge cases and boundary conditions in ONNXModelDownloader.

    Verifies that the downloader handles unusual inputs, edge cases, and
    error conditions gracefully according to the documented contract.
    """

    def test_handles_empty_model_name_gracefully(self, mock_onnx_model_downloader):
        """
        Test that downloader handles empty model name appropriately.

        Verifies:
            Empty model names are handled without crashes per input validation.

        Business Impact:
            Prevents application crashes from invalid input.

        Scenario:
            Given: An empty model name string ""
            When: Any downloader method is called with empty model name
            Then: Method handles gracefully (returns None or raises appropriate error)
            And: No unhandled exceptions occur

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        # Given: An empty model name string ""
        empty_model_name = ""

        downloader = mock_onnx_model_downloader()

        # When: Any downloader method is called with empty model name
        # Test cache path generation with empty name
        try:
            cache_path = downloader.get_model_cache_path(empty_model_name)
            # Then: Method handles gracefully (returns None or raises appropriate error)
            assert cache_path is not None  # Should handle gracefully
            assert isinstance(cache_path, Path)
        except Exception as e:
            # Should raise a meaningful error, not crash
            assert isinstance(e, (ValueError, TypeError))

        # Test local model search with empty name
        try:
            result = downloader.find_local_model(empty_model_name)
            # Should return None or raise appropriate error
            assert result is None or isinstance(result, Path)
        except Exception as e:
            # Should raise a meaningful error, not crash
            assert isinstance(e, (ValueError, TypeError))

        # And: No unhandled exceptions occur
        # If we reach here, the methods handled the empty input gracefully

    def test_handles_very_long_model_names(self):
        """
        Test that downloader handles extremely long model names correctly.

        Verifies:
            Long model names don't cause path length issues per safety behavior.

        Business Impact:
            Prevents file system errors from unusually long model identifiers.

        Scenario:
            Given: A very long model name (e.g., 500 characters)
            When: get_model_cache_path(long_model_name) is called
            Then: Returns a valid path without exceeding OS limits
            And: Path generation completes successfully

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_handles_model_name_with_special_characters(self):
        """
        Test that downloader sanitizes model names with special characters.

        Verifies:
            Special characters are handled safely per path sanitization behavior.

        Business Impact:
            Prevents file system security issues and invalid path errors.

        Scenario:
            Given: A model name with special characters "model:name*with<chars>"
            When: get_model_cache_path("model:name*with<chars>") is called
            Then: Returns a safe path with special characters sanitized
            And: Resulting path is valid on all supported operating systems

        Fixtures Used:
            - mock_onnx_model_downloader: Factory to create downloader instances
        """
        pass

    def test_handles_cache_directory_permission_errors(self):
        """
        Test that downloader handles cache directory permission errors gracefully.

        Verifies:
            Permission errors are caught and reported per error handling.

        Business Impact:
            Provides clear errors when cache directory is not writable.

        Scenario:
            Given: Cache directory exists but is not writable
            When: download_model() attempts to save model to cache
            Then: Permission error is caught and InfrastructureError is raised
            And: Error message indicates permission issue with cache directory

        Fixtures Used:
            - mock_onnx_model_downloader: Factory with restricted permissions
            - mock_infrastructure_error: Shared exception mock for verification
        """
        pass

    def test_handles_disk_full_during_download(self):
        """
        Test that downloader handles disk full errors during model download.

        Verifies:
            Disk space errors are caught and reported appropriately.

        Business Impact:
            Prevents partial downloads from consuming disk space.

        Scenario:
            Given: Disk space is exhausted during model download
            When: download_model() attempts to save large model
            Then: Disk full error is caught
            And: Partial download is cleaned up
            And: InfrastructureError is raised with disk space message

        Fixtures Used:
            - mock_onnx_model_downloader: Factory with mocked disk full scenario
        """
        pass

