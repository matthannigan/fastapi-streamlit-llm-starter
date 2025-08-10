#!/usr/bin/env python3
"""
Environment Variable and Preset Validation Script - CORRECTED VERSION

This script validates all possible environment variable combinations and 
preset integrations for the enhanced middleware stack using the correct
app.core.middleware module (not enhanced_setup.py).

Usage:
    python validate_environment_configurations_corrected.py
    
Environment Variables Tested:
- RESILIENCE_PRESET (simple, development, production)
- Individual middleware enable/disable flags
- Configuration override combinations
- Redis URL and fallback scenarios
- Security and performance settings
- API versioning configurations
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentConfigurationValidator:
    """Comprehensive environment configuration testing."""
    
    def __init__(self):
        self.test_results = []
        self.original_env = dict(os.environ)
        
        # Define test environments
        self.preset_configurations = {
            'simple': {
                'RESILIENCE_PRESET': 'simple',
                'expected_features': ['rate_limiting', 'security_headers', 'compression', 'api_versioning']
            },
            'development': {
                'RESILIENCE_PRESET': 'development',
                'LOG_LEVEL': 'DEBUG',
                'COMPRESSION_LEVEL': '4',
                'SLOW_REQUEST_THRESHOLD': '2000',
                'MEMORY_MONITORING_ENABLED': 'true',
                'expected_features': ['rate_limiting', 'security_headers', 'compression', 'api_versioning', 'performance_monitoring']
            },
            'production': {
                'RESILIENCE_PRESET': 'production',
                'LOG_LEVEL': 'INFO',
                'COMPRESSION_LEVEL': '6',
                'SLOW_REQUEST_THRESHOLD': '5000',
                'MEMORY_MONITORING_ENABLED': 'false',
                'LOG_SENSITIVE_DATA': 'false',
                'expected_features': ['rate_limiting', 'security_headers', 'compression', 'api_versioning', 'performance_monitoring']
            }
        }
        
        # Environment variable test cases
        self.environment_test_cases = [
            # Basic middleware enable/disable combinations
            {
                'name': 'all_middleware_enabled',
                'env_vars': {
                    'RATE_LIMITING_ENABLED': 'true',
                    'COMPRESSION_ENABLED': 'true',
                    'API_VERSIONING_ENABLED': 'true',
                    'SECURITY_HEADERS_ENABLED': 'true',
                    'PERFORMANCE_MONITORING_ENABLED': 'true',
                    'REQUEST_LOGGING_ENABLED': 'true',
                    'REQUEST_SIZE_LIMITING_ENABLED': 'true'
                },
                'expected_middleware_count': 8
            },
            {
                'name': 'minimal_middleware',
                'env_vars': {
                    'RATE_LIMITING_ENABLED': 'false',
                    'COMPRESSION_ENABLED': 'false',
                    'API_VERSIONING_ENABLED': 'false',
                    'SECURITY_HEADERS_ENABLED': 'true',
                    'PERFORMANCE_MONITORING_ENABLED': 'false',
                    'REQUEST_LOGGING_ENABLED': 'true',
                    'REQUEST_SIZE_LIMITING_ENABLED': 'false'
                },
                'expected_middleware_count': 3  # Security, logging, CORS (global exception handler is not middleware)
            },
            {
                'name': 'version_compatibility_enabled',
                'env_vars': {
                    'API_VERSIONING_ENABLED': 'true',
                    'VERSION_COMPATIBILITY_ENABLED': 'true',
                    'DEFAULT_API_VERSION': '1.0',
                    'CURRENT_API_VERSION': '2.0',
                    'MIN_API_VERSION': '1.0',
                    'MAX_API_VERSION': '2.0'
                },
                'expected_middleware_count': 9  # Includes version compatibility middleware
            },
            # Redis configuration variations
            {
                'name': 'redis_available',
                'env_vars': {
                    'RATE_LIMITING_ENABLED': 'true',
                    'REDIS_URL': 'redis://localhost:6379',
                    'CUSTOM_RATE_LIMITS': '{"auth": {"requests": 100, "window": 60}}'
                },
                'expected_redis_configured': True
            },
            {
                'name': 'redis_unavailable',
                'env_vars': {
                    'RATE_LIMITING_ENABLED': 'true',
                    'REDIS_URL': '',  # Empty Redis URL should use local cache
                    'CUSTOM_RATE_LIMITS': '{"default": {"requests": 50, "window": 60}}'
                },
                'expected_redis_configured': False
            },
            # Compression configuration variations
            {
                'name': 'high_compression',
                'env_vars': {
                    'COMPRESSION_ENABLED': 'true',
                    'COMPRESSION_LEVEL': '9',
                    'COMPRESSION_MIN_SIZE': '512',
                    'COMPRESSION_ALGORITHMS': '["br", "gzip", "deflate"]',
                    'STREAMING_COMPRESSION_ENABLED': 'true'
                },
                'expected_settings': {
                    'compression_level': 9
                }
            },
            {
                'name': 'fast_compression',
                'env_vars': {
                    'COMPRESSION_ENABLED': 'true',
                    'COMPRESSION_LEVEL': '1',
                    'COMPRESSION_MIN_SIZE': '2048',
                    'STREAMING_COMPRESSION_ENABLED': 'false'
                },
                'expected_settings': {
                    'compression_level': 1
                }
            },
            # Security configuration variations
            {
                'name': 'enhanced_security',
                'env_vars': {
                    'SECURITY_HEADERS_ENABLED': 'true',
                    'MAX_HEADERS_COUNT': '50',
                    'MAX_REQUEST_SIZE': '5242880',  # 5MB
                    'REQUEST_SIZE_LIMITING_ENABLED': 'true'
                },
                'expected_settings': {
                    'max_request_size': 5242880
                }
            },
            # Performance monitoring variations
            {
                'name': 'detailed_monitoring',
                'env_vars': {
                    'PERFORMANCE_MONITORING_ENABLED': 'true',
                    'SLOW_REQUEST_THRESHOLD': '500',
                    'MEMORY_MONITORING_ENABLED': 'true',
                    'METRICS_EXPORT_ENABLED': 'true'
                },
                'expected_settings': {
                    'slow_request_threshold': 500
                }
            },
            {
                'name': 'minimal_monitoring',
                'env_vars': {
                    'PERFORMANCE_MONITORING_ENABLED': 'true',
                    'SLOW_REQUEST_THRESHOLD': '10000',
                    'MEMORY_MONITORING_ENABLED': 'false',
                    'METRICS_EXPORT_ENABLED': 'false'
                },
                'expected_settings': {
                    'slow_request_threshold': 10000
                }
            },
            # Complex configuration combinations
            {
                'name': 'production_like',
                'env_vars': {
                    'RESILIENCE_PRESET': 'production',
                    'RATE_LIMITING_ENABLED': 'true',
                    'REDIS_URL': 'redis://redis-cluster:6379',
                    'COMPRESSION_ENABLED': 'true',
                    'COMPRESSION_LEVEL': '6',
                    'API_VERSIONING_ENABLED': 'true',
                    'SECURITY_HEADERS_ENABLED': 'true',
                    'LOG_LEVEL': 'WARNING',
                    'MEMORY_MONITORING_ENABLED': 'false',
                    'VERSION_COMPATIBILITY_ENABLED': 'false'
                },
                'expected_middleware_count': 8
            }
        ]
    
    @contextmanager
    def environment_context(self, env_vars: Dict[str, str]):
        """Context manager for temporarily setting environment variables."""
        # Clear existing environment
        for key in list(os.environ.keys()):
            if key.startswith(('RESILIENCE_', 'RATE_', 'COMPRESSION_', 'API_', 
                              'SECURITY_', 'PERFORMANCE_', 'REQUEST_', 'VERSION_',
                              'LOG_', 'REDIS_', 'CUSTOM_', 'MAX_', 'MIN_',
                              'SLOW_', 'MEMORY_', 'METRICS_', 'STREAMING_')):
                del os.environ[key]
        
        # Set new environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            yield
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(self.original_env)
    
    def validate_settings_configuration(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Validate settings configuration with given environment variables."""
        try:
            # Import after setting environment variables
            from app.core.config import Settings
            
            # Create settings instance
            settings = Settings()
            
            # Test basic configuration loading
            config_data = {
                'rate_limiting_enabled': getattr(settings, 'rate_limiting_enabled', True),
                'compression_enabled': getattr(settings, 'compression_enabled', True),
                'api_versioning_enabled': getattr(settings, 'api_versioning_enabled', True),
                'security_headers_enabled': getattr(settings, 'security_headers_enabled', True),
                'performance_monitoring_enabled': getattr(settings, 'performance_monitoring_enabled', True),
                'request_logging_enabled': getattr(settings, 'request_logging_enabled', True),
                'request_size_limiting_enabled': getattr(settings, 'request_size_limiting_enabled', True),
                'version_compatibility_enabled': getattr(settings, 'version_compatibility_enabled', False),
            }
            
            # Test advanced configuration
            if hasattr(settings, 'compression_level'):
                config_data['compression_level'] = settings.compression_level
            if hasattr(settings, 'slow_request_threshold'):
                config_data['slow_request_threshold'] = settings.slow_request_threshold
            if hasattr(settings, 'max_request_size'):
                config_data['max_request_size'] = settings.max_request_size
            
            # Test Redis configuration
            redis_url = getattr(settings, 'redis_url', None)
            config_data['redis_configured'] = bool(redis_url and redis_url.strip())
            
            return {
                'success': True,
                'config': config_data,
                'settings_valid': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def validate_middleware_setup(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Validate middleware setup with given environment variables."""
        try:
            from app.core.config import Settings
            from app.core.middleware import (
                get_middleware_stats,
                validate_middleware_configuration,
                setup_enhanced_middleware
            )
            from fastapi import FastAPI
            
            # Create test application and settings
            app = FastAPI()
            settings = Settings()
            
            # Validate configuration
            validation_issues = validate_middleware_configuration(settings)
            
            # Test middleware setup function
            setup_enhanced_middleware(app, settings)
            
            # Get middleware statistics
            stats = get_middleware_stats(app)
            
            return {
                'success': True,
                'middleware_count': stats.get('total_middleware', 0),
                'enabled_features': stats.get('enabled_features', []),
                'validation_issues': validation_issues,
                'middleware_stack': stats.get('middleware_stack', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def test_preset_configuration(self, preset_name: str, preset_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific preset configuration."""
        logger.info(f"Testing preset: {preset_name}")
        
        env_vars = {k: v for k, v in preset_config.items() if k != 'expected_features'}
        expected_features = preset_config.get('expected_features', [])
        
        with self.environment_context(env_vars):
            # Test settings configuration
            settings_result = self.validate_settings_configuration(env_vars)
            
            # Test middleware setup
            middleware_result = self.validate_middleware_setup(env_vars)
            
            # Validate expected features
            features_valid = True
            missing_features = []
            if middleware_result.get('success') and expected_features:
                enabled_features = middleware_result.get('enabled_features', [])
                for feature in expected_features:
                    if feature not in enabled_features:
                        missing_features.append(feature)
                        features_valid = False
            
            return {
                'preset_name': preset_name,
                'settings_result': settings_result,
                'middleware_result': middleware_result,
                'features_valid': features_valid,
                'missing_features': missing_features,
                'success': settings_result.get('success', False) and middleware_result.get('success', False) and features_valid
            }
    
    def test_environment_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific environment variable case."""
        case_name = test_case['name']
        env_vars = test_case['env_vars']
        
        logger.info(f"Testing environment case: {case_name}")
        
        with self.environment_context(env_vars):
            # Test settings configuration
            settings_result = self.validate_settings_configuration(env_vars)
            
            # Test middleware setup
            middleware_result = self.validate_middleware_setup(env_vars)
            
            # Validate expectations
            expectations_met = True
            expectation_failures = []
            
            if middleware_result.get('success'):
                # Check expected middleware count
                if 'expected_middleware_count' in test_case:
                    expected_count = test_case['expected_middleware_count']
                    actual_count = middleware_result.get('middleware_count', 0)
                    if actual_count != expected_count:
                        expectations_met = False
                        expectation_failures.append(f"Expected {expected_count} middleware, got {actual_count}")
                
                # Check expected settings
                if 'expected_settings' in test_case and settings_result.get('success'):
                    expected_settings = test_case['expected_settings']
                    actual_config = settings_result.get('config', {})
                    for key, expected_value in expected_settings.items():
                        if key in actual_config:
                            actual_value = actual_config[key]
                            if actual_value != expected_value:
                                expectations_met = False
                                expectation_failures.append(f"Setting {key}: expected {expected_value}, got {actual_value}")
                        else:
                            expectations_met = False
                            expectation_failures.append(f"Setting {key} not found in configuration")
                
                # Check Redis configuration expectations
                if 'expected_redis_configured' in test_case and settings_result.get('success'):
                    expected_redis = test_case['expected_redis_configured']
                    actual_redis = settings_result.get('config', {}).get('redis_configured', False)
                    if actual_redis != expected_redis:
                        expectations_met = False
                        expectation_failures.append(f"Redis configured: expected {expected_redis}, got {actual_redis}")
            
            return {
                'case_name': case_name,
                'settings_result': settings_result,
                'middleware_result': middleware_result,
                'expectations_met': expectations_met,
                'expectation_failures': expectation_failures,
                'success': (settings_result.get('success', False) and 
                           middleware_result.get('success', False) and 
                           expectations_met)
            }
    
    def test_environment_variable_precedence(self) -> Dict[str, Any]:
        """Test environment variable precedence and override behavior."""
        logger.info("Testing environment variable precedence")
        
        precedence_tests = []
        
        # Test 1: Preset vs individual setting
        with self.environment_context({
            'RESILIENCE_PRESET': 'production',
            'COMPRESSION_LEVEL': '3'  # Override preset default
        }):
            settings_result = self.validate_settings_configuration({})
            if settings_result.get('success'):
                config = settings_result.get('config', {})
                compression_level = config.get('compression_level', 6)  # Default production is 6
                precedence_tests.append({
                    'test_name': 'individual_overrides_preset',
                    'success': compression_level == 3,
                    'expected': 3,
                    'actual': compression_level
                })
        
        # Test 2: Custom rate limits JSON parsing
        with self.environment_context({
            'RATE_LIMITING_ENABLED': 'true',
            'CUSTOM_RATE_LIMITS': '{"api_heavy": {"requests": 5, "window": 60}}'
        }):
            settings_result = self.validate_settings_configuration({})
            precedence_tests.append({
                'test_name': 'custom_rate_limits_parsing',
                'success': settings_result.get('success', False),
                'config_valid': bool(settings_result.get('config', {}).get('rate_limiting_enabled'))
            })
        
        # Test 3: Boolean environment variable parsing
        boolean_tests = ['true', 'True', 'TRUE', '1', 'yes', 'false', 'False', 'FALSE', '0', 'no']
        boolean_results = []
        
        for bool_value in boolean_tests:
            with self.environment_context({'COMPRESSION_ENABLED': bool_value}):
                settings_result = self.validate_settings_configuration({})
                if settings_result.get('success'):
                    config = settings_result.get('config', {})
                    actual_bool = config.get('compression_enabled', False)
                    expected_bool = bool_value.lower() in ('true', '1', 'yes')
                    boolean_results.append({
                        'input': bool_value,
                        'expected': expected_bool,
                        'actual': actual_bool,
                        'success': actual_bool == expected_bool
                    })
        
        return {
            'precedence_tests': precedence_tests,
            'boolean_parsing_tests': boolean_results,
            'success': all(test.get('success', False) for test in precedence_tests) and
                      all(test.get('success', False) for test in boolean_results)
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all environment configuration validation tests."""
        logger.info("Starting comprehensive environment configuration validation")
        start_time = time.time()
        
        results = {
            'start_time': start_time,
            'preset_tests': {},
            'environment_tests': {},
            'precedence_tests': {},
            'overall_success': True,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        }
        
        # Test all presets
        logger.info("Testing preset configurations...")
        for preset_name, preset_config in self.preset_configurations.items():
            preset_result = self.test_preset_configuration(preset_name, preset_config)
            results['preset_tests'][preset_name] = preset_result
            results['total_tests'] += 1
            if preset_result.get('success'):
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1
                results['overall_success'] = False
        
        # Test all environment cases
        logger.info("Testing environment variable cases...")
        for test_case in self.environment_test_cases:
            case_result = self.test_environment_case(test_case)
            results['environment_tests'][test_case['name']] = case_result
            results['total_tests'] += 1
            if case_result.get('success'):
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1
                results['overall_success'] = False
        
        # Test environment variable precedence
        logger.info("Testing environment variable precedence...")
        precedence_result = self.test_environment_variable_precedence()
        results['precedence_tests'] = precedence_result
        results['total_tests'] += 1
        if precedence_result.get('success'):
            results['passed_tests'] += 1
        else:
            results['failed_tests'] += 1
            results['overall_success'] = False
        
        # Calculate completion time
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']
        
        return results


def main():
    """Main execution function."""
    print("=" * 80)
    print("Environment Variable and Preset Configuration Validation - CORRECTED")
    print("=" * 80)
    
    validator = EnvironmentConfigurationValidator()
    
    try:
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()
        
        # Print summary
        print(f"\nValidation Summary:")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"Overall Success: {results['overall_success']}")
        
        # Print detailed results
        print(f"\n{'='*60}")
        print("PRESET CONFIGURATION RESULTS")
        print(f"{'='*60}")
        
        for preset_name, preset_result in results['preset_tests'].items():
            status = "✅ PASS" if preset_result.get('success') else "❌ FAIL"
            print(f"{preset_name}: {status}")
            
            if not preset_result.get('success'):
                if preset_result.get('missing_features'):
                    print(f"  Missing features: {preset_result['missing_features']}")
                if preset_result['settings_result'].get('error'):
                    print(f"  Settings error: {preset_result['settings_result']['error']}")
                if preset_result['middleware_result'].get('error'):
                    print(f"  Middleware error: {preset_result['middleware_result']['error']}")
            else:
                middleware_result = preset_result.get('middleware_result', {})
                print(f"  Middleware count: {middleware_result.get('middleware_count', 0)}")
                print(f"  Enabled features: {middleware_result.get('enabled_features', [])}")
        
        print(f"\n{'='*60}")
        print("ENVIRONMENT VARIABLE TEST RESULTS")
        print(f"{'='*60}")
        
        for case_name, case_result in results['environment_tests'].items():
            status = "✅ PASS" if case_result.get('success') else "❌ FAIL"
            print(f"{case_name}: {status}")
            
            if not case_result.get('success'):
                if case_result.get('expectation_failures'):
                    for failure in case_result['expectation_failures']:
                        print(f"  - {failure}")
                if case_result['settings_result'].get('error'):
                    print(f"  Settings error: {case_result['settings_result']['error']}")
                if case_result['middleware_result'].get('error'):
                    print(f"  Middleware error: {case_result['middleware_result']['error']}")
        
        print(f"\n{'='*60}")
        print("ENVIRONMENT VARIABLE PRECEDENCE RESULTS")
        print(f"{'='*60}")
        
        precedence_result = results['precedence_tests']
        precedence_status = "✅ PASS" if precedence_result.get('success') else "❌ FAIL"
        print(f"Environment variable precedence: {precedence_status}")
        
        if not precedence_result.get('success'):
            for test in precedence_result.get('precedence_tests', []):
                if not test.get('success'):
                    print(f"  {test['test_name']}: Expected {test.get('expected')}, got {test.get('actual')}")
            
            for test in precedence_result.get('boolean_parsing_tests', []):
                if not test.get('success'):
                    print(f"  Boolean parsing '{test['input']}': Expected {test['expected']}, got {test['actual']}")
        
        # Save detailed results to file
        results_file = '/Users/matth/Github/MGH/fastapi-streamlit-llm-starter/backend/environment_validation_report_corrected.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Return exit code
        return 0 if results['overall_success'] else 1
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())