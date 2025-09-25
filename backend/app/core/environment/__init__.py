"""
Unified Environment Detection Service

This module provides centralized environment detection capabilities for all backend
infrastructure services, eliminating code duplication and providing consistent
environment classification across cache, resilience, security, and other systems.

Re-exports for backward compatibility while organizing into submodules.
"""

# TODO: Add imports from submodules for backward compatibility
# from .enums import Environment, FeatureContext
# from .models import EnvironmentSignal, EnvironmentInfo, DetectionConfig
# from .detector import EnvironmentDetector
# from .api import (
#     environment_detector,
#     get_environment_info,
#     is_production_environment,
#     is_development_environment
# )
# from .security import (
#     SecurityLevel,
#     SecurityConfiguration,
#     SecurityValidationResult,
#     EnvironmentSecurityGenerator,
#     generate_security_config,
#     validate_security_config
# )

# __all__ = [
#     'Environment',
#     'FeatureContext', 
#     'EnvironmentSignal',
#     'EnvironmentInfo',
#     'DetectionConfig',
#     'EnvironmentDetector',
#     'environment_detector',
#     'get_environment_info',
#     'is_production_environment',
#     'is_development_environment',
#     'SecurityLevel',
#     'SecurityConfiguration',
#     'SecurityValidationResult',
#     'EnvironmentSecurityGenerator',
#     'generate_security_config',
#     'validate_security_config',
# ]