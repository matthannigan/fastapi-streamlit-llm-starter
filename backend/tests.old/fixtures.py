"""
Reusable test data factories and fixtures.

This module contains fixtures that can be shared across multiple test files
to ensure consistent test data setup.
"""
import pytest


@pytest.fixture
def sample_text():
    """Sample text for testing text processing functionality."""
    return "Hello, world! This is a test message."


@pytest.fixture
def sample_user_data():
    """Sample user data for authentication tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_api_key():
    """Sample API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        "debug": True,
        "cache_enabled": True,
        "max_retries": 3
    } 