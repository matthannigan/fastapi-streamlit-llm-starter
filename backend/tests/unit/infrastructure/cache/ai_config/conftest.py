"""
Test fixtures for ai_config module unit tests.

This module provides reusable fixtures specific to AI cache configuration testing.
All fixtures provide 'happy path' behavior based on public contracts from 
backend/contracts/ directory.

Fixtures:
    - mock_validation_result: Mock ValidationResult for parameter validation testing
    
Note: Exception fixtures (ValidationError, ConfigurationError) are available
in the shared cache conftest.py file.
"""

import pytest
from unittest.mock import MagicMock
from typing import Dict, Any, List, Set


@pytest.fixture
def mock_validation_result():
    """
    Mock ValidationResult for testing parameter validation behavior.
    
    Provides 'happy path' mock of the parameter_mapping.ValidationResult contract with all methods
    returning successful validation behavior as documented in the public interface.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.parameter_mapping import ValidationResult
    
    mock_result = MagicMock(spec=ValidationResult)
    
    # Mock successful validation state per contract
    mock_result.is_valid = True
    mock_result.errors = []
    mock_result.warnings = []
    mock_result.recommendations = []
    mock_result.parameter_conflicts = {}
    mock_result.ai_specific_params = set()
    mock_result.generic_params = set()
    mock_result.context = {}
    
    # Mock methods per contract with successful behavior
    mock_result.add_error.return_value = None
    mock_result.add_warning.return_value = None
    mock_result.add_recommendation.return_value = None
    mock_result.add_conflict.return_value = None
    
    return mock_result


