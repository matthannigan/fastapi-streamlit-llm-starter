"""
Test fixtures for config module unit tests.

This module provides reusable fixtures specific to cache configuration testing.
All fixtures provide 'happy path' behavior based on public contracts from 
backend/contracts/ directory.

Fixtures:
    - mock_validation_result: Mock ValidationResult for configuration validation testing
    
Note: Exception fixtures (ValidationError, ConfigurationError) are available
in the shared cache conftest.py file.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_validation_result():
    """
    Mock ValidationResult for testing configuration validation behavior.
    
    Provides 'happy path' mock of the config.ValidationResult contract with all methods
    returning successful validation behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.config import ValidationResult
    
    mock_result = MagicMock(spec=ValidationResult)
    
    # Mock successful validation state per contract
    mock_result.is_valid = True
    mock_result.errors = []
    mock_result.warnings = []
    
    # Mock methods per contract with successful behavior
    mock_result.add_error.return_value = None
    mock_result.add_warning.return_value = None
    
    return mock_result