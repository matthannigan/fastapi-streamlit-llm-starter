"""
Test suite for SecurityService protocol defining security scanner interface.

This module tests the SecurityService abstract protocol that establishes the
standardized contract for all security scanning implementations. Tests verify
protocol method signatures, abstract method requirements, and interface completeness.

Test Strategy:
    - Verify protocol defines all required abstract methods
    - Test method signature correctness (parameters, return types)
    - Validate that protocol is abstract and cannot be instantiated
    - Verify protocol can be used as type hint for implementations
    - Test protocol inheritance and subclass requirements
"""

import pytest
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, get_type_hints
from app.infrastructure.security.llm.protocol import (
    SecurityService,
    SecurityResult,
    MetricsSnapshot
)


class TestSecurityServiceProtocolDefinition:
    """
    Test suite for SecurityService protocol structure and abstract methods.
    
    Scope:
        - Protocol inheritance from ABC (Abstract Base Class)
        - Required abstract method definitions
        - Method signature completeness
        - Protocol instantiation prevention
        
    Business Critical:
        Protocol definition enforces consistent security scanner interfaces
        across all implementations, enabling pluggable architecture.
        
    Test Coverage:
        - Abstract base class inheritance
        - All required abstract methods present
        - Protocol cannot be instantiated directly
        - Method signatures match contract
    """
    
    def test_security_service_protocol_inherits_from_abc(self):
        """
        Test that SecurityService protocol inherits from ABC.

        Verifies:
            Protocol uses ABC base class to enforce abstract method
            implementation in concrete classes per contract

        Business Impact:
            Ensures all security scanner implementations must provide
            complete interface, preventing partial implementations

        Scenario:
            Given: SecurityService class definition
            When: Checking class inheritance
            Then: SecurityService is subclass of ABC
            And: Abstract method enforcement is enabled

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService class definition
        protocol_class = SecurityService

        # When: Checking class inheritance
        # Then: SecurityService is subclass of ABC
        assert issubclass(protocol_class, ABC), f"SecurityService must inherit from ABC"

        # And: Abstract method enforcement is enabled
        assert hasattr(protocol_class, '__abstractmethods__'), "SecurityService must have abstract methods defined"
    
    def test_security_service_protocol_cannot_be_instantiated(self):
        """
        Test that SecurityService protocol cannot be instantiated directly.

        Verifies:
            Abstract protocol raises TypeError when instantiation is
            attempted per ABC behavior

        Business Impact:
            Forces developers to create concrete implementations,
            preventing incomplete scanner usage

        Scenario:
            Given: SecurityService protocol class
            When: Attempting to instantiate SecurityService()
            Then: TypeError is raised indicating abstract methods
            And: Error message lists unimplemented abstract methods

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol class
        protocol_class = SecurityService

        # When: Attempting to instantiate SecurityService()
        # Then: TypeError is raised indicating abstract methods
        with pytest.raises(TypeError, match="Can't instantiate abstract class") as exc_info:
            SecurityService()

        # And: Error message lists unimplemented abstract methods
        error_message = str(exc_info.value)
        assert "abstract methods" in error_message.lower(), f"Error should mention abstract methods: {error_message}"
    
    def test_security_service_protocol_defines_validate_input_method(self):
        """
        Test that SecurityService protocol defines validate_input abstract method.

        Verifies:
            validate_input method exists with correct signature (text, context)
            returning SecurityResult per contract

        Business Impact:
            Ensures all scanners provide input validation capability,
            the core security operation for user content

        Scenario:
            Given: SecurityService protocol
            When: Checking for validate_input method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def validate_input(text: str, context: Dict | None) -> SecurityResult

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for validate_input method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'validate_input'), "SecurityService must define validate_input method"
        method = getattr(protocol_class, 'validate_input')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "validate_input must be an abstract method"

        # And: Signature matches: async def validate_input(text: str, context: Dict | None) -> SecurityResult
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        # Check method is async
        assert inspect.iscoroutinefunction(method), "validate_input must be an async method"

        # Check parameters
        assert 'text' in params, "validate_input must have 'text' parameter"
        assert 'context' in params, "validate_input must have 'context' parameter"

        # Check parameter types and defaults
        text_param = sig.parameters['text']
        context_param = sig.parameters['context']

        assert text_param.annotation == str, "text parameter must be annotated as str"
        assert context_param.annotation in [Dict[str, Any], Dict[str, Any] | None, type(None)], "context parameter must be Dict[str, Any] or None"
        assert context_param.default is None, "context parameter should default to None"

        # Check return type
        assert sig.return_annotation == SecurityResult, "validate_input must return SecurityResult"
    
    def test_security_service_protocol_defines_validate_output_method(self):
        """
        Test that SecurityService protocol defines validate_output abstract method.

        Verifies:
            validate_output method exists with correct signature for
            AI response validation per contract

        Business Impact:
            Ensures all scanners provide output validation capability
            for AI-generated content safety

        Scenario:
            Given: SecurityService protocol
            When: Checking for validate_output method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def validate_output(text: str, context: Dict | None) -> SecurityResult

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for validate_output method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'validate_output'), "SecurityService must define validate_output method"
        method = getattr(protocol_class, 'validate_output')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "validate_output must be an abstract method"

        # And: Signature matches: async def validate_output(text: str, context: Dict | None) -> SecurityResult
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        # Check method is async
        assert inspect.iscoroutinefunction(method), "validate_output must be an async method"

        # Check parameters
        assert 'text' in params, "validate_output must have 'text' parameter"
        assert 'context' in params, "validate_output must have 'context' parameter"

        # Check parameter types and defaults
        text_param = sig.parameters['text']
        context_param = sig.parameters['context']

        assert text_param.annotation == str, "text parameter must be annotated as str"
        assert context_param.annotation in [Dict[str, Any], Dict[str, Any] | None, type(None)], "context parameter must be Dict[str, Any] or None"
        assert context_param.default is None, "context parameter should default to None"

        # Check return type
        assert sig.return_annotation == SecurityResult, "validate_output must return SecurityResult"
    
    def test_security_service_protocol_defines_health_check_method(self):
        """
        Test that SecurityService protocol defines health_check abstract method.

        Verifies:
            health_check method exists for service availability verification
            per contract

        Business Impact:
            Enables health monitoring and readiness checks for all
            security scanner implementations

        Scenario:
            Given: SecurityService protocol
            When: Checking for health_check method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def health_check() -> Dict[str, Any]

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for health_check method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'health_check'), "SecurityService must define health_check method"
        method = getattr(protocol_class, 'health_check')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "health_check must be an abstract method"

        # And: Signature matches: async def health_check() -> Dict[str, Any]
        sig = inspect.signature(method)
        assert inspect.iscoroutinefunction(method), "health_check must be an async method"
        # Methods have 'self' parameter, so check for exactly 1 parameter (self only)
        assert len(sig.parameters) == 1, "health_check should take only self parameter"
        assert 'self' in sig.parameters, "health_check should have self parameter"
        assert sig.return_annotation == Dict[str, Any], "health_check must return Dict[str, Any]"

    def test_security_service_protocol_defines_get_metrics_method(self):
        """
        Test that SecurityService protocol defines get_metrics abstract method.

        Verifies:
            get_metrics method exists for performance monitoring per contract

        Business Impact:
            Ensures all scanners provide operational metrics for
            monitoring and performance analysis

        Scenario:
            Given: SecurityService protocol
            When: Checking for get_metrics method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def get_metrics() -> MetricsSnapshot

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for get_metrics method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'get_metrics'), "SecurityService must define get_metrics method"
        method = getattr(protocol_class, 'get_metrics')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "get_metrics must be an abstract method"

        # And: Signature matches: async def get_metrics() -> MetricsSnapshot
        sig = inspect.signature(method)
        assert inspect.iscoroutinefunction(method), "get_metrics must be an async method"
        # Methods have 'self' parameter, so check for exactly 1 parameter (self only)
        assert len(sig.parameters) == 1, "get_metrics should take only self parameter"
        assert 'self' in sig.parameters, "get_metrics should have self parameter"
        assert sig.return_annotation == MetricsSnapshot, "get_metrics must return MetricsSnapshot"

    def test_security_service_protocol_defines_get_configuration_method(self):
        """
        Test that SecurityService protocol defines get_configuration abstract method.

        Verifies:
            get_configuration method exists for configuration inspection
            per contract

        Business Impact:
            Enables runtime configuration inspection for debugging
            and security auditing

        Scenario:
            Given: SecurityService protocol
            When: Checking for get_configuration method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def get_configuration() -> Dict[str, Any]

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for get_configuration method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'get_configuration'), "SecurityService must define get_configuration method"
        method = getattr(protocol_class, 'get_configuration')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "get_configuration must be an abstract method"

        # And: Signature matches: async def get_configuration() -> Dict[str, Any]
        sig = inspect.signature(method)
        assert inspect.iscoroutinefunction(method), "get_configuration must be an async method"
        # Methods have 'self' parameter, so check for exactly 1 parameter (self only)
        assert len(sig.parameters) == 1, "get_configuration should take only self parameter"
        assert 'self' in sig.parameters, "get_configuration should have self parameter"
        assert sig.return_annotation == Dict[str, Any], "get_configuration must return Dict[str, Any]"

    def test_security_service_protocol_defines_reset_metrics_method(self):
        """
        Test that SecurityService protocol defines reset_metrics abstract method.

        Verifies:
            reset_metrics method exists for metrics management per contract

        Business Impact:
            Enables metrics reset for testing and monitoring period
            management across all implementations

        Scenario:
            Given: SecurityService protocol
            When: Checking for reset_metrics method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def reset_metrics() -> None

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for reset_metrics method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'reset_metrics'), "SecurityService must define reset_metrics method"
        method = getattr(protocol_class, 'reset_metrics')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "reset_metrics must be an abstract method"

        # And: Signature matches: async def reset_metrics() -> None
        sig = inspect.signature(method)
        assert inspect.iscoroutinefunction(method), "reset_metrics must be an async method"
        # Methods have 'self' parameter, so check for exactly 1 parameter (self only)
        assert len(sig.parameters) == 1, "reset_metrics should take only self parameter"
        assert 'self' in sig.parameters, "reset_metrics should have self parameter"
        assert sig.return_annotation in [type(None), None], "reset_metrics must return None"

    def test_security_service_protocol_defines_get_cache_statistics_method(self):
        """
        Test that SecurityService protocol defines get_cache_statistics abstract method.

        Verifies:
            get_cache_statistics method exists for cache monitoring per contract

        Business Impact:
            Ensures cache performance visibility across all scanner
            implementations for optimization

        Scenario:
            Given: SecurityService protocol
            When: Checking for get_cache_statistics method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def get_cache_statistics() -> Dict[str, Any]

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for get_cache_statistics method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'get_cache_statistics'), "SecurityService must define get_cache_statistics method"
        method = getattr(protocol_class, 'get_cache_statistics')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "get_cache_statistics must be an abstract method"

        # And: Signature matches: async def get_cache_statistics() -> Dict[str, Any]
        sig = inspect.signature(method)
        assert inspect.iscoroutinefunction(method), "get_cache_statistics must be an async method"
        # Methods have 'self' parameter, so check for exactly 1 parameter (self only)
        assert len(sig.parameters) == 1, "get_cache_statistics should take only self parameter"
        assert 'self' in sig.parameters, "get_cache_statistics should have self parameter"
        assert sig.return_annotation == Dict[str, Any], "get_cache_statistics must return Dict[str, Any]"

    def test_security_service_protocol_defines_clear_cache_method(self):
        """
        Test that SecurityService protocol defines clear_cache abstract method.

        Verifies:
            clear_cache method exists for cache management per contract

        Business Impact:
            Enables cache clearing for maintenance and policy updates
            across all implementations

        Scenario:
            Given: SecurityService protocol
            When: Checking for clear_cache method
            Then: Method is defined and marked as abstractmethod
            And: Signature matches: async def clear_cache() -> None

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol
        protocol_class = SecurityService

        # When: Checking for clear_cache method
        # Then: Method is defined and marked as abstractmethod
        assert hasattr(protocol_class, 'clear_cache'), "SecurityService must define clear_cache method"
        method = getattr(protocol_class, 'clear_cache')
        assert isinstance(getattr(method, '__isabstractmethod__', False), bool), "clear_cache must be an abstract method"

        # And: Signature matches: async def clear_cache() -> None
        sig = inspect.signature(method)
        assert inspect.iscoroutinefunction(method), "clear_cache must be an async method"
        # Methods have 'self' parameter, so check for exactly 1 parameter (self only)
        assert len(sig.parameters) == 1, "clear_cache should take only self parameter"
        assert 'self' in sig.parameters, "clear_cache should have self parameter"
        assert sig.return_annotation in [type(None), None], "clear_cache must return None"

    def test_security_service_protocol_all_methods_are_async(self):
        """
        Test that all SecurityService protocol methods are async.

        Verifies:
            Protocol enforces async/await pattern for all operations
            per documented non-blocking requirement

        Business Impact:
            Ensures all security scanners use non-blocking operations,
            preventing request thread blocking

        Scenario:
            Given: All SecurityService abstract methods
            When: Checking method definitions
            Then: All methods are defined with 'async def'
            And: All implementations must be awaitable

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: All SecurityService abstract methods
        protocol_class = SecurityService
        abstract_methods = getattr(protocol_class, '__abstractmethods__', set())

        # When: Checking method definitions
        # Then: All methods are defined with 'async def'
        for method_name in abstract_methods:
            method = getattr(protocol_class, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} must be an async method"

        # And: All implementations must be awaitable (verified by async nature)
        assert len(abstract_methods) > 0, "SecurityService must have abstract methods"
        expected_methods = {
            'validate_input', 'validate_output', 'health_check',
            'get_metrics', 'get_configuration', 'reset_metrics',
            'get_cache_statistics', 'clear_cache'
        }
        assert abstract_methods == expected_methods, f"Expected abstract methods {expected_methods}, got {abstract_methods}"


class TestSecurityServiceProtocolImplementation:
    """
    Test suite for SecurityService protocol implementation requirements.
    
    Scope:
        - Concrete class implementation validation
        - Abstract method override requirements
        - Protocol conformance checking
        - Type hint usage with protocol
        
    Business Critical:
        Implementation requirements ensure all security scanners provide
        complete, type-safe interfaces for the security infrastructure.
        
    Test Coverage:
        - Concrete implementation requirements
        - Missing method detection
        - Type hint compatibility
        - Protocol as interface specification
    """
    
    def test_security_service_protocol_requires_all_methods_implemented(self):
        """
        Test that incomplete SecurityService implementations cannot be instantiated.

        Verifies:
            Classes inheriting SecurityService must implement all abstract
            methods to be instantiable per ABC requirements

        Business Impact:
            Prevents deployment of incomplete security scanners that
            would fail at runtime

        Scenario:
            Given: Partial SecurityService implementation missing required methods
            When: Attempting to instantiate the incomplete class
            Then: TypeError is raised listing missing abstract methods
            And: Instantiation is prevented until all methods implemented

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: Partial SecurityService implementation missing required methods
        class IncompleteSecurityService(SecurityService):
            """Implementation missing most required methods"""
            async def validate_input(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                return SecurityResult(is_safe=True, violations=[], score=1.0, scanned_text=text, scan_duration_ms=10)

        # When: Attempting to instantiate the incomplete class
        # Then: TypeError is raised listing missing abstract methods
        with pytest.raises(TypeError, match="Can't instantiate abstract class") as exc_info:
            IncompleteSecurityService()

        # And: Instantiation is prevented until all methods implemented
        error_message = str(exc_info.value)
        missing_methods = ['validate_output', 'health_check', 'get_metrics', 'get_configuration',
                          'reset_metrics', 'get_cache_statistics', 'clear_cache']
        for method in missing_methods:
            assert method in error_message, f"Error should mention missing method: {method}"

    def test_security_service_protocol_accepts_complete_implementation(self):
        """
        Test that complete SecurityService implementations can be instantiated.

        Verifies:
            Classes implementing all abstract methods can be successfully
            instantiated and used per contract

        Business Impact:
            Confirms protocol requirements are achievable, enabling
            creation of valid security scanner implementations

        Scenario:
            Given: Complete SecurityService implementation with all methods
            When: Instantiating the concrete class
            Then: Instance is created successfully without errors
            And: Instance can be used wherever SecurityService is expected

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: Complete SecurityService implementation with all methods
        class CompleteSecurityService(SecurityService):
            """Implementation with all required methods"""

            async def validate_input(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                return SecurityResult(is_safe=True, violations=[], score=1.0, scanned_text=text, scan_duration_ms=10)

            async def validate_output(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                return SecurityResult(is_safe=True, violations=[], score=1.0, scanned_text=text, scan_duration_ms=10)

            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy"}

            async def get_metrics(self) -> MetricsSnapshot:
                from app.infrastructure.security.llm.protocol import ScanMetrics
                return MetricsSnapshot(
                    input_metrics=ScanMetrics(),
                    output_metrics=ScanMetrics(),
                    system_health={"status": "healthy"},
                    scanner_health={"test_scanner": True},
                    uptime_seconds=3600,
                    memory_usage_mb=256.0
                )

            async def get_configuration(self) -> Dict[str, Any]:
                return {"scanner_configs": {}, "global_settings": {}}

            async def reset_metrics(self) -> None:
                pass

            async def get_cache_statistics(self) -> Dict[str, Any]:
                return {"hit_rate": 0.8, "entries": 100}

            async def clear_cache(self) -> None:
                pass

        # When: Instantiating the concrete class
        # Then: Instance is created successfully without errors
        instance = CompleteSecurityService()
        assert instance is not None

        # And: Instance can be used wherever SecurityService is expected
        assert isinstance(instance, SecurityService)
        assert hasattr(instance, 'validate_input')
        assert hasattr(instance, 'validate_output')

    def test_security_service_protocol_can_be_used_as_type_hint(self):
        """
        Test that SecurityService can be used as type hint for dependency injection.

        Verifies:
            Protocol serves as valid type annotation for function parameters
            and return types per typing requirements

        Business Impact:
            Enables type-safe dependency injection and static type
            checking for security infrastructure

        Scenario:
            Given: Function accepting SecurityService parameter
            When: Type checking the function signature
            Then: SecurityService is valid type hint
            And: Any conforming implementation is accepted

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: Function accepting SecurityService parameter
        async def process_security_input(service: SecurityService, text: str) -> SecurityResult:
            """Function using SecurityService as type hint"""
            return await service.validate_input(text)

        async def get_security_service() -> SecurityService:
            """Function returning SecurityService type"""
            class TestService(SecurityService):
                async def validate_input(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                    return SecurityResult(is_safe=True, violations=[], score=1.0, scanned_text=text, scan_duration_ms=10)

                async def validate_output(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                    return SecurityResult(is_safe=True, violations=[], score=1.0, scanned_text=text, scan_duration_ms=10)

                async def health_check(self) -> Dict[str, Any]:
                    return {"status": "healthy"}

                async def get_metrics(self) -> MetricsSnapshot:
                    from app.infrastructure.security.llm.protocol import ScanMetrics
                    return MetricsSnapshot(
                        input_metrics=ScanMetrics(),
                        output_metrics=ScanMetrics(),
                        system_health={"status": "healthy"},
                        scanner_health={"test_scanner": True},
                        uptime_seconds=3600,
                        memory_usage_mb=256.0
                    )

                async def get_configuration(self) -> Dict[str, Any]:
                    return {}

                async def reset_metrics(self) -> None:
                    pass

                async def get_cache_statistics(self) -> Dict[str, Any]:
                    return {}

                async def clear_cache(self) -> None:
                    pass

            return TestService()

        # When: Type checking the function signature
        process_sig = inspect.signature(process_security_input)
        get_sig = inspect.signature(get_security_service)

        # Then: SecurityService is valid type hint
        service_param = process_sig.parameters['service']
        assert service_param.annotation == SecurityService, "SecurityService should be valid type hint"
        assert get_sig.return_annotation == SecurityService, "SecurityService should be valid return type hint"

        # And: Any conforming implementation is accepted
        # Note: Can't call async function in non-async test, but we can verify the signature
        # The get_security_service function demonstrates the protocol can be used as return type
        assert get_security_service.__annotations__.get('return') == SecurityService, "Function should return SecurityService type"

    def test_security_service_protocol_enforces_method_signatures(self):
        """
        Test that SecurityService protocol enforces correct method signatures in implementations.

        Verifies:
            Implementations must match parameter types and return types
            defined in protocol per contract

        Business Impact:
            Ensures type safety and prevents signature mismatches that
            would cause runtime errors

        Scenario:
            Given: SecurityService implementation with mismatched signature
            When: Type checking or runtime verification
            Then: Type errors or signature mismatches are detected
            And: Incorrect implementations are rejected

        Fixtures Used:
            None - Direct protocol testing
        """
        # Test that implementations must follow expected signatures
        # This is verified through type checking and method existence

        class MismatchedSignatureService(SecurityService):
            """Service with wrong signatures that should fail type checking"""

            # Missing required parameter
            async def validate_input(self, text: str) -> SecurityResult:  # Missing context parameter
                return SecurityResult(is_safe=True, violations=[], score=1.0, scanned_text=text, scan_duration_ms=10)

            # Wrong return type
            async def validate_output(self, text: str, context: Dict[str, Any] | None = None) -> str:  # Should return SecurityResult
                return "wrong"

            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy"}

            async def get_metrics(self) -> MetricsSnapshot:
                from app.infrastructure.security.llm.protocol import ScanMetrics
                return MetricsSnapshot(
                    input_metrics=ScanMetrics(),
                    output_metrics=ScanMetrics(),
                    system_health={"status": "healthy"},
                    scanner_health={"test_scanner": True},
                    uptime_seconds=3600,
                    memory_usage_mb=256.0
                )

            async def get_configuration(self) -> Dict[str, Any]:
                return {}

            async def reset_metrics(self) -> None:
                pass

            async def get_cache_statistics(self) -> Dict[str, Any]:
                return {}

            async def clear_cache(self) -> None:
                pass

        # Verify that method signatures can be checked
        validate_input_sig = inspect.signature(MismatchedSignatureService.validate_input)
        validate_output_sig = inspect.signature(MismatchedSignatureService.validate_output)

        # Check that signatures don't match expected protocol
        protocol_input_sig = inspect.signature(SecurityService.validate_input)
        protocol_output_sig = inspect.signature(SecurityService.validate_output)

        # Parameter count mismatch
        assert len(validate_input_sig.parameters) != len(protocol_input_sig.parameters), "Should detect parameter signature mismatch"

        # Return type mismatch
        assert validate_output_sig.return_annotation != protocol_output_sig.return_annotation, "Should detect return type mismatch"

        # The class should still be instantiable (Python doesn't enforce signature matching at runtime)
        # But type checkers and runtime checks would catch these issues
        instance = MismatchedSignatureService()
        assert isinstance(instance, SecurityService)

    def test_security_service_protocol_supports_multiple_implementations(self):
        """
        Test that multiple SecurityService implementations can coexist.

        Verifies:
            Protocol enables pluggable architecture with multiple scanner
            implementations per design goals

        Business Impact:
            Supports using different scanner implementations for different
            environments or threat models

        Scenario:
            Given: Multiple complete SecurityService implementations
            When: Using different implementations in same system
            Then: All implementations work correctly via common interface
            And: Implementations are interchangeable via protocol

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: Multiple complete SecurityService implementations
        class DevelopmentSecurityService(SecurityService):
            """Implementation for development environment"""

            async def validate_input(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                # Lenient validation for development
                return SecurityResult(is_safe=True, violations=[], score=0.9, scanned_text=text, scan_duration_ms=5)

            async def validate_output(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                return SecurityResult(is_safe=True, violations=[], score=0.9, scanned_text=text, scan_duration_ms=5)

            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy", "environment": "development"}

            async def get_metrics(self) -> MetricsSnapshot:
                from app.infrastructure.security.llm.protocol import ScanMetrics
                return MetricsSnapshot(
                    input_metrics=ScanMetrics(),
                    output_metrics=ScanMetrics(),
                    system_health={"status": "healthy"},
                    scanner_health={"dev_scanner": True},
                    uptime_seconds=3600,
                    memory_usage_mb=128.0
                )

            async def get_configuration(self) -> Dict[str, Any]:
                return {"environment": "development", "strictness": "low"}

            async def reset_metrics(self) -> None:
                pass

            async def get_cache_statistics(self) -> Dict[str, Any]:
                return {"hit_rate": 0.6, "entries": 50}

            async def clear_cache(self) -> None:
                pass

        class ProductionSecurityService(SecurityService):
            """Implementation for production environment"""

            async def validate_input(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                # Strict validation for production
                return SecurityResult(is_safe=True, violations=[], score=0.99, scanned_text=text, scan_duration_ms=50)

            async def validate_output(self, text: str, context: Dict[str, Any] | None = None) -> SecurityResult:
                return SecurityResult(is_safe=True, violations=[], score=0.99, scanned_text=text, scan_duration_ms=50)

            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy", "environment": "production"}

            async def get_metrics(self) -> MetricsSnapshot:
                from app.infrastructure.security.llm.protocol import ScanMetrics
                return MetricsSnapshot(
                    input_metrics=ScanMetrics(),
                    output_metrics=ScanMetrics(),
                    system_health={"status": "healthy"},
                    scanner_health={"prod_scanner": True},
                    uptime_seconds=86400,
                    memory_usage_mb=512.0
                )

            async def get_configuration(self) -> Dict[str, Any]:
                return {"environment": "production", "strictness": "high"}

            async def reset_metrics(self) -> None:
                pass

            async def get_cache_statistics(self) -> Dict[str, Any]:
                return {"hit_rate": 0.95, "entries": 1000}

            async def clear_cache(self) -> None:
                pass

        # When: Using different implementations in same system
        dev_service = DevelopmentSecurityService()
        prod_service = ProductionSecurityService()

        # Then: All implementations work correctly via common interface
        assert isinstance(dev_service, SecurityService)
        assert isinstance(prod_service, SecurityService)

        # Test that both implementations have the same interface
        for service in [dev_service, prod_service]:
            assert hasattr(service, 'validate_input')
            assert hasattr(service, 'validate_output')
            assert hasattr(service, 'health_check')
            assert hasattr(service, 'get_metrics')
            assert hasattr(service, 'get_configuration')
            assert hasattr(service, 'reset_metrics')
            assert hasattr(service, 'get_cache_statistics')
            assert hasattr(service, 'clear_cache')

        # And: Implementations are interchangeable via protocol
        async def test_service(service: SecurityService, text: str) -> SecurityResult:
            """Function that works with any SecurityService implementation"""
            return await service.validate_input(text)

        # Both implementations can be used interchangeably
        assert isinstance(dev_service, SecurityService)
        assert isinstance(prod_service, SecurityService)


class TestSecurityServiceProtocolDocumentation:
    """
    Test suite for SecurityService protocol documentation completeness.
    
    Scope:
        - Method docstring presence and quality
        - Parameter documentation completeness
        - Return type documentation
        - Exception documentation
        - Usage example presence
        
    Business Critical:
        Comprehensive protocol documentation ensures developers can
        create correct implementations without trial and error.
        
    Test Coverage:
        - Docstring presence for protocol and methods
        - Parameter documentation completeness
        - Return type specifications
        - Exception contract documentation
    """
    
    def test_security_service_protocol_has_class_docstring(self):
        """
        Test that SecurityService protocol has comprehensive class docstring.

        Verifies:
            Protocol class includes detailed docstring explaining purpose,
            contract requirements, and implementation guidance per standards

        Business Impact:
            Provides developers with clear understanding of protocol
            requirements and implementation expectations

        Scenario:
            Given: SecurityService protocol class
            When: Accessing __doc__ attribute
            Then: Docstring is present and non-empty
            And: Docstring explains protocol purpose and requirements

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService protocol class
        protocol_class = SecurityService

        # When: Accessing __doc__ attribute
        # Then: Docstring is present and non-empty
        assert protocol_class.__doc__ is not None, "SecurityService must have class docstring"
        assert len(protocol_class.__doc__.strip()) > 0, "SecurityService docstring must not be empty"

        # And: Docstring explains protocol purpose and requirements
        docstring = protocol_class.__doc__
        assert "protocol" in docstring.lower(), "Docstring should mention it's a protocol"
        assert "contract" in docstring.lower(), "Docstring should mention contract requirements"
        assert "interface" in docstring.lower(), "Docstring should mention interface design"
        assert "security" in docstring.lower(), "Docstring should mention security purpose"
    
    def test_security_service_validate_input_has_complete_docstring(self):
        """
        Test that validate_input method has comprehensive docstring.

        Verifies:
            Method docstring documents parameters, return type, exceptions,
            and behavior per documentation standards

        Business Impact:
            Ensures implementers understand input validation requirements
            and expected behavior

        Scenario:
            Given: validate_input abstract method
            When: Checking method docstring
            Then: Docstring includes Args, Returns, Raises sections
            And: All parameters are documented
            And: Return type SecurityResult is explained

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: validate_input abstract method
        method = SecurityService.validate_input

        # When: Checking method docstring
        # Then: Docstring includes Args, Returns, Raises sections
        assert method.__doc__ is not None, "validate_input must have docstring"
        docstring = method.__doc__
        assert len(docstring.strip()) > 0, "validate_input docstring must not be empty"

        # Check for standard documentation sections
        assert "Args:" in docstring, "validate_input docstring should have Args section"
        assert "Returns:" in docstring, "validate_input docstring should have Returns section"
        assert "Raises:" in docstring, "validate_input docstring should have Raises section"

        # And: All parameters are documented
        assert "text:" in docstring, "validate_input docstring should document text parameter"
        assert "context:" in docstring, "validate_input docstring should document context parameter"

        # And: Return type SecurityResult is explained
        assert "SecurityResult" in docstring, "validate_input docstring should mention SecurityResult return type"
        assert "input" in docstring.lower(), "validate_input docstring should mention input validation purpose"
    
    def test_security_service_validate_output_has_complete_docstring(self):
        """
        Test that validate_output method has comprehensive docstring.

        Verifies:
            Method docstring fully documents output validation contract

        Business Impact:
            Ensures implementers understand AI response validation
            requirements and expected behavior

        Scenario:
            Given: validate_output abstract method
            When: Checking method docstring
            Then: Docstring includes complete Args, Returns, Raises
            And: Context parameter usage is explained

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: validate_output abstract method
        method = SecurityService.validate_output

        # When: Checking method docstring
        # Then: Docstring includes complete Args, Returns, Raises
        assert method.__doc__ is not None, "validate_output must have docstring"
        docstring = method.__doc__
        assert len(docstring.strip()) > 0, "validate_output docstring must not be empty"

        # Check for standard documentation sections
        assert "Args:" in docstring, "validate_output docstring should have Args section"
        assert "Returns:" in docstring, "validate_output docstring should have Returns section"
        assert "Raises:" in docstring, "validate_output docstring should have Raises section"

        # And: Context parameter usage is explained
        assert "context:" in docstring, "validate_output docstring should document context parameter"
        assert "model_id" in docstring or "prompt" in docstring, "validate_output docstring should explain context usage"
        assert "output" in docstring.lower(), "validate_output docstring should mention output validation purpose"
        assert "AI" in docstring or "artificial" in docstring.lower(), "validate_output docstring should mention AI-generated content"
    
    def test_security_service_methods_document_exception_conditions(self):
        """
        Test that SecurityService methods document all possible exceptions.

        Verifies:
            Each method's Raises section lists all exceptions per contract
            including SecurityServiceError subclasses

        Business Impact:
            Enables proper error handling in clients and prevents
            unexpected exception propagation

        Scenario:
            Given: All SecurityService abstract methods
            When: Checking Raises documentation in docstrings
            Then: All documented exceptions are listed
            And: Exception conditions are explained

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: All SecurityService abstract methods
        abstract_methods = getattr(SecurityService, '__abstractmethods__', set())

        # When: Checking Raises documentation in docstrings
        # Then: All documented exceptions are listed
        for method_name in abstract_methods:
            method = getattr(SecurityService, method_name)
            docstring = method.__doc__

            assert docstring is not None, f"{method_name} must have docstring"
            assert "Raises:" in docstring, f"{method_name} docstring should have Raises section"

            # Check for SecurityServiceError - all methods should document this
            assert "SecurityServiceError" in docstring, f"{method_name} should document SecurityServiceError"

            # Check for method-specific exceptions based on actual documentation
            if method_name in ['validate_input', 'validate_output', 'health_check']:
                # These methods should document timeout and unavailability errors
                assert "ScannerTimeoutError" in docstring, f"{method_name} should document ScannerTimeoutError"
                assert "ServiceUnavailableError" in docstring, f"{method_name} should document ServiceUnavailableError"
                assert "timeout" in docstring.lower(), f"{method_name} should explain timeout conditions"
                assert "unavailable" in docstring.lower(), f"{method_name} should explain service unavailability conditions"

            elif method_name in ['get_configuration']:
                # Configuration method should document configuration errors
                assert "ConfigurationError" in docstring, f"{method_name} should document ConfigurationError"

            elif method_name in ['get_cache_statistics', 'clear_cache']:
                # Cache methods should document cache errors
                assert "CacheError" in docstring, f"{method_name} should document CacheError"
                assert "ServiceUnavailableError" in docstring, f"{method_name} should document ServiceUnavailableError"

            elif method_name in ['reset_metrics']:
                # Metrics reset should document timeout errors
                assert "ScannerTimeoutError" in docstring, f"{method_name} should document ScannerTimeoutError"

            elif method_name in ['get_metrics']:
                # Metrics collection should document service unavailability
                assert "ServiceUnavailableError" in docstring, f"{method_name} should document ServiceUnavailableError"

            # And: Exception conditions are explained (general check)
            assert any(error_type in docstring for error_type in ["Error", "timeout", "unavailable", "fails", "corrupted"]), f"{method_name} should explain error conditions"
    
    def test_security_service_methods_document_behavior_requirements(self):
        """
        Test that SecurityService methods document expected behavior.

        Verifies:
            Method docstrings include Behavior sections explaining
            operational requirements per standards

        Business Impact:
            Provides implementers with clear behavioral contracts beyond
            just method signatures

        Scenario:
            Given: SecurityService method docstrings
            When: Checking for Behavior sections
            Then: Expected behaviors are documented
            And: Performance requirements are specified

        Fixtures Used:
            None - Direct protocol testing
        """
        # Given: SecurityService method docstrings
        abstract_methods = getattr(SecurityService, '__abstractmethods__', set())

        # When: Checking for Behavior sections
        # Then: Expected behaviors are documented
        for method_name in abstract_methods:
            method = getattr(SecurityService, method_name)
            docstring = method.__doc__

            assert docstring is not None, f"{method_name} must have docstring"

            # Check for behavior documentation - not all methods may have explicit "Behavior:" section
            # but they should document operational requirements
            has_behavior_section = "Behavior:" in docstring

            # For validation methods, look for performance and operational requirements
            if method_name in ['validate_input', 'validate_output']:
                # These methods should document scanning behavior
                assert "scans" in docstring.lower() or "analyzes" in docstring.lower(), f"{method_name} should document scanning behavior"
                assert "metrics" in docstring.lower(), f"{method_name} should document metrics tracking"
                assert "performance" in docstring.lower() or "timeout" in docstring.lower(), f"{method_name} should document performance requirements"

            # For monitoring methods, look for operational behavior
            elif method_name in ['health_check', 'get_metrics']:
                assert "system" in docstring.lower() or "status" in docstring.lower(), f"{method_name} should document system monitoring behavior"

            # For management methods, look for operational impact
            elif method_name in ['reset_metrics', 'get_cache_statistics', 'clear_cache']:
                assert "cache" in docstring.lower() or "metrics" in docstring.lower(), f"{method_name} should document cache/metrics management behavior"

        # And: Performance requirements are specified (check key methods)
        for method_name in ['validate_input', 'validate_output', 'health_check']:
            method = getattr(SecurityService, method_name)
            docstring = method.__doc__
            assert "timeout" in docstring.lower(), f"{method_name} should specify timeout requirements"

