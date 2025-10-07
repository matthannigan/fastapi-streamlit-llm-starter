"""
Test fixture execution order to debug environment detection issues.
"""
import os

def test_environment_variable_is_set():
    """Verify ENVIRONMENT is set by autouse fixture."""
    env = os.getenv("ENVIRONMENT")
    print(f"\n🔍 ENVIRONMENT variable: {env}")
    assert env == "testing", f"Expected 'testing', got '{env}'"

def test_environment_detector_sees_testing():
    """Verify environment detector sees 'testing' environment."""
    from app.core.environment.api import get_environment_info

    env_info = get_environment_info()
    print(f"\n🔍 Detected environment: {env_info.environment.value}")
    print(f"🔍 Confidence: {env_info.confidence}")
    print(f"🔍 Reasoning: {env_info.reasoning}")

    assert env_info.environment.value == "testing", (
        f"Expected 'testing', got '{env_info.environment.value}'. "
        f"Reasoning: {env_info.reasoning}"
    )
