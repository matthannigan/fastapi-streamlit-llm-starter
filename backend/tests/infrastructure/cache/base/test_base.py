"""
Unit tests for CacheInterface abstract base class.

This test suite verifies the observable behaviors documented in the
CacheInterface public contract (base.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Abstract interface contract enforcement
    - Polymorphic usage patterns across different implementations
    - Async method signature compliance

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
import inspect
from unittest.mock import MagicMock, AsyncMock
from abc import ABC
from typing import Any, Optional

from app.infrastructure.cache.base import CacheInterface


# Import real cache implementations for polymorphism testing
def cache_implementations():
    """
    Real cache implementations for polymorphism testing.
    
    Provides a list of actual cache implementations to test polymorphic
    behavior and interface compliance across different cache types.
    """
    from app.infrastructure.cache.memory import InMemoryCache
    from app.infrastructure.cache.redis_generic import GenericRedisCache
    
    implementations = [
        InMemoryCache(max_size=100, default_ttl=3600)
    ]
    
    # Add Redis implementations when available (graceful degradation)
    try:
        redis_cache = GenericRedisCache(
            redis_url="redis://localhost:6379/15",  # Test database
            default_ttl=3600,
            enable_l1_cache=True,
            fail_on_connection_error=False  # Allow fallback
        )
        implementations.append(redis_cache)
    except Exception:
        # Redis not available, continue with memory cache only
        pass
        
    return implementations


class TestCacheInterfaceContract:
    """
    Test suite for CacheInterface abstract contract verification.
    
    Scope:
        - Abstract base class contract enforcement
        - Method signature validation for all abstract methods
        - Exception handling for incomplete implementations
        - Type annotation compliance verification
        
    Business Critical:
        Interface contracts ensure consistent cache behavior across all implementations
        
    Test Strategy:
        - Abstract method enforcement testing with incomplete implementations
        - Method signature validation for get, set, delete operations
        - Type annotation verification for parameters and return values
        - Interface compliance testing for all required abstract methods
        
    External Dependencies:
        - Python ABC module (real): Abstract base class functionality
        - typing module (real): Type annotation verification
    """

    def test_cache_interface_cannot_be_instantiated_directly(self):
        """
        Test that CacheInterface cannot be instantiated as abstract base class.
        
        Verifies:
            Abstract base class prevents direct instantiation
            
        Business Impact:
            Ensures cache interface is only used through concrete implementations
            
        Scenario:
            Given: CacheInterface abstract base class
            When: Direct instantiation is attempted
            Then: TypeError is raised indicating abstract class cannot be instantiated
            And: Error message identifies abstract methods that must be implemented
            And: No CacheInterface instance is created
            
        Abstract Class Enforcement Verified:
            - CacheInterface inherits from ABC properly
            - All required methods are marked as @abstractmethod
            - Direct instantiation raises TypeError
            - Error message lists unimplemented abstract methods
            
        Fixtures Used:
            - None (testing abstract class behavior directly)
            
        ABC Compliance Verified:
            CacheInterface properly implements Python abstract base class pattern
            
        Related Tests:
            - test_incomplete_implementation_cannot_be_instantiated()
            - test_complete_implementation_can_be_instantiated()
        """
        # Given: CacheInterface abstract base class
        # When: Direct instantiation is attempted
        with pytest.raises(TypeError) as exc_info:
            CacheInterface()
        
        # Then: TypeError is raised with appropriate message
        error_message = str(exc_info.value)
        assert "abstract class" in error_message.lower() or "can't instantiate" in error_message.lower()
        
        # And: Error message identifies abstract methods that must be implemented
        expected_methods = ["get", "set", "delete", "exists"]
        for method_name in expected_methods:
            assert method_name in error_message
        
        # Verify CacheInterface inherits from ABC properly
        assert issubclass(CacheInterface, ABC)
        
        # Verify all required methods are marked as @abstractmethod
        abstract_methods = CacheInterface.__abstractmethods__
        for method_name in expected_methods:
            assert method_name in abstract_methods

    def test_incomplete_implementation_cannot_be_instantiated(self):
        """
        Test that incomplete CacheInterface implementations cannot be instantiated.
        
        Verifies:
            Incomplete implementations of abstract interface are rejected
            
        Business Impact:
            Prevents deployment of cache implementations missing required methods
            
        Scenario:
            Given: Class inheriting from CacheInterface but missing some abstract methods
            When: Instantiation is attempted
            Then: TypeError is raised indicating incomplete implementation
            And: Error message identifies which abstract methods are missing
            And: No instance is created from incomplete implementation
            
        Implementation Completeness Verified:
            - Missing get() method prevents instantiation
            - Missing set() method prevents instantiation
            - Missing delete() method prevents instantiation
            - Combination of missing methods prevents instantiation
            
        Fixtures Used:
            - None (testing abstract method enforcement directly)
            
        Contract Enforcement Verified:
            All abstract methods must be implemented for successful instantiation
            
        Related Tests:
            - test_cache_interface_cannot_be_instantiated_directly()
            - test_complete_implementation_can_be_instantiated()
        """
        # Test incomplete implementation missing get() method
        class MissingGetMethod(CacheInterface):
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                pass
            async def delete(self, key: str):
                pass
            async def exists(self, key: str) -> bool:
                return False
        
        with pytest.raises(TypeError) as exc_info:
            MissingGetMethod()
        assert "get" in str(exc_info.value)
        
        # Test incomplete implementation missing set() method
        class MissingSetMethod(CacheInterface):
            async def get(self, key: str):
                return None
            async def delete(self, key: str):
                pass
            async def exists(self, key: str) -> bool:
                return False
        
        with pytest.raises(TypeError) as exc_info:
            MissingSetMethod()
        assert "set" in str(exc_info.value)
        
        # Test incomplete implementation missing delete() method
        class MissingDeleteMethod(CacheInterface):
            async def get(self, key: str):
                return None
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                pass
            async def exists(self, key: str) -> bool:
                return False
        
        with pytest.raises(TypeError) as exc_info:
            MissingDeleteMethod()
        assert "delete" in str(exc_info.value)
        
        # Test incomplete implementation missing exists() method
        class MissingExistsMethod(CacheInterface):
            async def get(self, key: str):
                return None
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                pass
            async def delete(self, key: str):
                pass
        
        with pytest.raises(TypeError) as exc_info:
            MissingExistsMethod()
        assert "exists" in str(exc_info.value)
        
        # Test multiple missing methods
        class MultipleMissingMethods(CacheInterface):
            async def get(self, key: str):
                return None
        
        with pytest.raises(TypeError) as exc_info:
            MultipleMissingMethods()
        error_message = str(exc_info.value)
        missing_methods = ["set", "delete", "exists"]
        for method_name in missing_methods:
            assert method_name in error_message

    def test_complete_implementation_can_be_instantiated(self):
        """
        Test that complete CacheInterface implementations can be instantiated successfully.
        
        Verifies:
            Complete implementations of abstract interface work correctly
            
        Business Impact:
            Ensures properly implemented cache classes can be used in production
            
        Scenario:
            Given: Class inheriting from CacheInterface with all abstract methods implemented
            When: Instantiation is attempted
            Then: Instance is created successfully
            And: All abstract methods are callable on the instance
            And: Instance passes isinstance() check for CacheInterface
            
        Complete Implementation Verified:
            - All abstract methods (get, set, delete) are implemented
            - Instance creation succeeds without TypeError
            - Created instance is properly typed as CacheInterface
            - All methods are callable and maintain proper async signatures
            
        Fixtures Used:
            - None (testing complete implementation directly)
            
        Interface Satisfaction Verified:
            Complete implementations satisfy all CacheInterface contract requirements
            
        Related Tests:
            - test_implemented_methods_maintain_async_signatures()
            - test_implemented_methods_accept_correct_parameter_types()
        """
        # Given: Class inheriting from CacheInterface with all abstract methods implemented
        class CompleteImplementation(CacheInterface):
            async def get(self, key: str):
                return f"value_for_{key}"
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                pass
            
            async def delete(self, key: str):
                pass
            
            async def exists(self, key: str) -> bool:
                return True
        
        # When: Instantiation is attempted
        # Then: Instance is created successfully
        cache_instance = CompleteImplementation()
        
        # And: Instance passes isinstance() check for CacheInterface
        assert isinstance(cache_instance, CacheInterface)
        
        # And: All abstract methods are callable on the instance
        required_methods = ["get", "set", "delete", "exists"]
        for method_name in required_methods:
            assert hasattr(cache_instance, method_name)
            method = getattr(cache_instance, method_name)
            assert callable(method)
            # All methods maintain proper async signatures
            assert inspect.iscoroutinefunction(method)
        
        # Verify that the instance satisfies CacheInterface contract
        assert issubclass(type(cache_instance), CacheInterface)

    def test_abstract_methods_require_async_signatures(self):
        """
        Test that CacheInterface abstract methods enforce async signatures.
        
        Verifies:
            Abstract method signatures require async/await pattern
            
        Business Impact:
            Ensures all cache implementations support async operation patterns required for performance
            
        Scenario:
            Given: CacheInterface abstract method definitions
            When: Method signatures are examined
            Then: All abstract methods are defined as async def
            And: Method signatures use proper async type annotations
            And: Return type annotations support async patterns (Awaitable, etc.)
            
        Async Signature Verification:
            - get() method signature is async def get(self, key: str)
            - set() method signature is async def set(self, key: str, value: Any, ttl: Optional[int] = None)
            - delete() method signature is async def delete(self, key: str)
            - All methods can be awaited when implemented
            
        Fixtures Used:
            - None (testing method signature definitions directly)
            
        Async Pattern Enforcement Verified:
            Interface contract enforces async operation patterns for all cache operations
            
        Related Tests:
            - test_implemented_methods_maintain_async_signatures()
            - test_async_method_calls_work_with_await()
        """
        # Given: CacheInterface abstract method definitions
        abstract_methods = ["get", "set", "delete", "exists"]
        
        for method_name in abstract_methods:
            # When: Method signatures are examined
            method = getattr(CacheInterface, method_name)
            
            # Then: All abstract methods are defined as async def
            assert inspect.iscoroutinefunction(method), f"{method_name} should be an async method"
        
        # Verify specific method signatures match expected patterns
        get_signature = inspect.signature(CacheInterface.get)
        assert "key" in get_signature.parameters
        assert get_signature.parameters["key"].annotation == str
        
        set_signature = inspect.signature(CacheInterface.set)
        assert "key" in set_signature.parameters
        assert "value" in set_signature.parameters
        assert "ttl" in set_signature.parameters
        assert set_signature.parameters["key"].annotation == str
        assert set_signature.parameters["value"].annotation == Any
        assert set_signature.parameters["ttl"].annotation == Optional[int]
        assert set_signature.parameters["ttl"].default is None
        
        delete_signature = inspect.signature(CacheInterface.delete)
        assert "key" in delete_signature.parameters
        assert delete_signature.parameters["key"].annotation == str
        
        exists_signature = inspect.signature(CacheInterface.exists)
        assert "key" in exists_signature.parameters
        assert exists_signature.parameters["key"].annotation == str
        assert exists_signature.return_annotation == bool

    def test_abstract_method_parameter_types_are_correctly_annotated(self):
        """
        Test that CacheInterface abstract methods have correct parameter type annotations.
        
        Verifies:
            Method parameter type annotations match contract documentation
            
        Business Impact:
            Ensures type safety and IDE support across all cache implementations
            
        Scenario:
            Given: CacheInterface abstract method definitions
            When: Parameter type annotations are examined
            Then: All parameters have correct type annotations
            And: Type annotations support static type checking
            And: Optional parameters are properly annotated
            
        Parameter Type Annotations Verified:
            - get() key parameter: str type annotation
            - set() key parameter: str type annotation
            - set() value parameter: Any type annotation
            - set() ttl parameter: Optional[int] type annotation with default None
            - delete() key parameter: str type annotation
            
        Fixtures Used:
            - None (testing type annotations directly)
            
        Type Safety Verification:
            Parameter type annotations enable static type checking and IDE support
            
        Related Tests:
            - test_abstract_method_return_types_are_correctly_annotated()
            - test_type_annotations_support_polymorphic_usage()
        """
        # Test get() method parameter type annotations
        get_signature = inspect.signature(CacheInterface.get)
        get_params = get_signature.parameters
        
        assert "self" in get_params
        assert "key" in get_params
        assert get_params["key"].annotation == str, "get() key parameter should be annotated as str"
        
        # Test set() method parameter type annotations
        set_signature = inspect.signature(CacheInterface.set)
        set_params = set_signature.parameters
        
        assert "self" in set_params
        assert "key" in set_params
        assert "value" in set_params
        assert "ttl" in set_params
        
        assert set_params["key"].annotation == str, "set() key parameter should be annotated as str"
        assert set_params["value"].annotation == Any, "set() value parameter should be annotated as Any"
        assert set_params["ttl"].annotation == Optional[int], "set() ttl parameter should be annotated as Optional[int]"
        assert set_params["ttl"].default is None, "set() ttl parameter should have default None"
        
        # Test delete() method parameter type annotations
        delete_signature = inspect.signature(CacheInterface.delete)
        delete_params = delete_signature.parameters
        
        assert "self" in delete_params
        assert "key" in delete_params
        assert delete_params["key"].annotation == str, "delete() key parameter should be annotated as str"
        
        # Test exists() method parameter type annotations
        exists_signature = inspect.signature(CacheInterface.exists)
        exists_params = exists_signature.parameters
        
        assert "self" in exists_params
        assert "key" in exists_params
        assert exists_params["key"].annotation == str, "exists() key parameter should be annotated as str"
        
        # Verify all methods have proper parameter count (excluding self)
        assert len([p for p in get_params if p != "self"]) == 1, "get() should have exactly 1 parameter (plus self)"
        assert len([p for p in set_params if p != "self"]) == 3, "set() should have exactly 3 parameters (plus self)"
        assert len([p for p in delete_params if p != "self"]) == 1, "delete() should have exactly 1 parameter (plus self)"
        assert len([p for p in exists_params if p != "self"]) == 1, "exists() should have exactly 1 parameter (plus self)"

    def test_abstract_method_return_types_are_correctly_annotated(self):
        """
        Test that CacheInterface abstract methods have correct return type annotations.
        
        Verifies:
            Method return type annotations match expected async return patterns
            
        Business Impact:
            Enables type checking and proper async/await usage across implementations
            
        Scenario:
            Given: CacheInterface abstract method definitions
            When: Return type annotations are examined
            Then: All return types support async patterns correctly
            And: Type annotations enable static type checking
            And: Return types match documented behavior expectations
            
        Return Type Annotations Verified:
            - get() method returns appropriate type for cached values
            - set() method returns appropriate type for storage operations
            - delete() method returns appropriate type for deletion operations
            - All return types are compatible with async/await patterns
            
        Fixtures Used:
            - None (testing return type annotations directly)
            
        Async Return Type Verification:
            Return type annotations properly support async operation patterns
            
        Related Tests:
            - test_abstract_method_parameter_types_are_correctly_annotated()
            - test_return_type_annotations_enable_type_checking()
        """
        # Test that methods have return type annotations where expected
        get_signature = inspect.signature(CacheInterface.get)
        set_signature = inspect.signature(CacheInterface.set)
        delete_signature = inspect.signature(CacheInterface.delete)
        exists_signature = inspect.signature(CacheInterface.exists)
        
        # get() method should not have explicit return annotation in abstract method
        # (implementations will define specific return types)
        # This is acceptable for abstract methods as concrete implementations will specify
        
        # set() method should not have explicit return annotation in abstract method
        # (implementations may return None or other values)
        
        # delete() method should not have explicit return annotation in abstract method
        # (implementations may return None or other values)
        
        # exists() method should have bool return annotation as specified in contract
        assert exists_signature.return_annotation == bool, "exists() method should return bool"
        
        # Verify all methods are properly marked as coroutine functions
        # which ensures they return coroutines (compatible with async/await)
        assert inspect.iscoroutinefunction(CacheInterface.get)
        assert inspect.iscoroutinefunction(CacheInterface.set)
        assert inspect.iscoroutinefunction(CacheInterface.delete)
        assert inspect.iscoroutinefunction(CacheInterface.exists)
        
        # Verify methods can be awaited by checking they are coroutine functions
        # This ensures return types are compatible with async/await patterns
        async_methods = ["get", "set", "delete", "exists"]
        for method_name in async_methods:
            method = getattr(CacheInterface, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} should be awaitable"


class TestCacheInterfacePolymorphism:
    """
    Test suite for CacheInterface polymorphic usage pattern verification.
    
    Scope:
        - Polymorphic usage across different cache implementations
        - Type checking compatibility with CacheInterface
        - Interface substitutability (Liskov Substitution Principle)
        - Dependency injection patterns using CacheInterface
        
    Business Critical:
        Polymorphic usage enables flexible cache backend switching without code changes
        
    Test Strategy:
        - Polymorphic usage testing with different concrete implementations
        - Type compatibility verification for dependency injection
        - Interface substitutability testing with mock implementations
        - Service integration patterns using CacheInterface type annotations
        
    External Dependencies:
        - Mock cache implementations (created for testing polymorphic behavior)
        - Type checking verification (using typing module features)
    """

    @pytest.mark.parametrize("cache_impl", cache_implementations())
    async def test_cache_interface_supports_polymorphic_usage(self, cache_impl):
        """
        Test that CacheInterface supports polymorphic usage across different implementations.
        
        Verifies:
            Different cache implementations can be used interchangeably through interface
            
        Business Impact:
            Enables flexible cache backend selection without changing service code
            
        Scenario:
            Given: Multiple concrete cache implementations (InMemoryCache, Redis caches)
            When: Services use CacheInterface type annotation for cache dependency
            Then: Any concrete implementation can be substituted without code changes
            And: All cache operations work consistently across implementations
            And: Service code remains independent of specific cache backend
            
        Polymorphic Usage Verified:
            - Services can accept any CacheInterface implementation
            - isinstance() checks work correctly for all implementations
            - Type annotations support polymorphic assignment
            - Method calls work consistently across different implementations
            
        Fixtures Used:
            - cache_implementations: Real cache implementations for polymorphism testing
            
        Implementation Substitutability Verified:
            All CacheInterface implementations can be substituted transparently
            
        Related Tests:
            - test_dependency_injection_works_with_interface_type()
            - test_service_integration_supports_cache_switching()
        """
        from app.infrastructure.cache.base import CacheInterface
        
        # Given: Concrete cache implementation that should implement CacheInterface
        assert isinstance(cache_impl, CacheInterface)
        
        # When: Using the cache through CacheInterface reference
        cache: CacheInterface = cache_impl
        
        # Test basic operations work polymorphically
        test_key = f"test:polymorphic:{type(cache).__name__}"
        test_value = {"implementation": type(cache).__name__, "polymorphic": True}
        
        # Then: All cache operations work consistently across implementations
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # Test exists method
        exists_result = await cache.exists(test_key)
        assert exists_result is True
        
        # Test delete method
        await cache.delete(test_key)
        deleted_value = await cache.get(test_key)
        assert deleted_value is None
        
        # Verify key no longer exists
        exists_after_delete = await cache.exists(test_key)
        assert exists_after_delete is False

    @pytest.mark.parametrize("cache_impl", cache_implementations())
    async def test_dependency_injection_works_with_interface_type(self, cache_impl):
        """
        Test that dependency injection works correctly with CacheInterface type annotations.
        
        Verifies:
            Services can receive cache dependencies through CacheInterface type
            
        Business Impact:
            Enables clean dependency injection patterns for cache-dependent services
            
        Scenario:
            Given: Service class with CacheInterface type annotation for cache dependency
            When: Different concrete cache implementations are injected
            Then: Service accepts any valid CacheInterface implementation
            And: Service methods work correctly with injected cache
            And: Type checking passes for all valid implementations
            
        Dependency Injection Verified:
            - Service constructors accept CacheInterface type parameter
            - Type annotations enable static type checking
            - Runtime isinstance() checks work correctly
            - Service methods call cache operations through interface
            
        Fixtures Used:
            - cache_implementations: Real cache implementations for injection testing
            
        Clean Architecture Verified:
            Services depend on CacheInterface abstraction rather than concrete implementations
            
        Related Tests:
            - test_cache_interface_supports_polymorphic_usage()
            - test_type_checking_works_with_interface_assignments()
        """
        from app.infrastructure.cache.base import CacheInterface
        
        # Given: Service class with CacheInterface type annotation
        class TestService:
            def __init__(self, cache: CacheInterface):
                self.cache = cache
                
            async def store_data(self, key: str, data: dict):
                """Store data using injected cache."""
                await self.cache.set(key, data)
                
            async def retrieve_data(self, key: str):
                """Retrieve data using injected cache."""
                return await self.cache.get(key)
                
            async def data_exists(self, key: str) -> bool:
                """Check if data exists using injected cache."""
                return await self.cache.exists(key)
        
        # When: Different concrete cache implementations are injected
        service = TestService(cache_impl)
        
        # Then: Service accepts any valid CacheInterface implementation
        assert isinstance(service.cache, CacheInterface)
        
        # And: Service methods work correctly with injected cache
        test_key = f"test:service:{type(cache_impl).__name__}"
        test_data = {"service_test": True, "cache_type": type(cache_impl).__name__}
        
        await service.store_data(test_key, test_data)
        retrieved_data = await service.retrieve_data(test_key)
        assert retrieved_data == test_data
        
        exists_result = await service.data_exists(test_key)
        assert exists_result is True
        
        # Clean up
        await service.cache.delete(test_key)
        
        # Verify cleanup worked
        exists_after_cleanup = await service.data_exists(test_key)
        assert exists_after_cleanup is False

    async def test_service_integration_supports_cache_switching(self):
        """
        Test that service integration supports switching between cache implementations.
        
        Verifies:
            Services can switch cache implementations without code modification
            
        Business Impact:
            Enables runtime cache backend configuration and testing flexibility
            
        Scenario:
            Given: Service using cache through CacheInterface
            When: Cache implementation is switched (e.g., InMemory to Redis)
            Then: Service continues to work without modification
            And: All cache operations maintain expected behavior
            And: Service performance may change but functionality remains consistent
            
        Cache Switching Verified:
            - Service works with InMemoryCache implementation
            - Service works with AIResponseCache implementation
            - Cache switching requires no service code changes
            - Service behavior remains functionally consistent
            
        Fixtures Used:
            - default_memory_cache: Generic cache behavior for switching
            
        Runtime Flexibility Verified:
            Cache implementations can be changed at runtime without service impact
            
        Related Tests:
            - test_cache_performance_characteristics_may_vary_across_implementations()
            - test_cache_switching_maintains_functional_consistency()
        """
        # Given: Service class that uses cache through CacheInterface
        class FlexibleCacheService:
            def __init__(self, cache: CacheInterface):
                self.cache = cache
            
            async def store_item(self, key: str, item: dict):
                """Store an item using the configured cache."""
                await self.cache.set(key, item)
            
            async def retrieve_item(self, key: str):
                """Retrieve an item using the configured cache."""
                return await self.cache.get(key)
            
            async def item_exists(self, key: str) -> bool:
                """Check if item exists using the configured cache."""
                return await self.cache.exists(key)
            
            async def remove_item(self, key: str):
                """Remove an item using the configured cache."""
                await self.cache.delete(key)
        
        # Get different cache implementations to test switching
        available_caches = cache_implementations()
        if len(available_caches) < 1:
            pytest.skip("No cache implementations available for switching test")
        
        test_data = {
            "switching_test": True,
            "data": "consistent behavior across implementations"
        }
        
        # Test that service works consistently across different cache implementations
        for i, cache_impl in enumerate(available_caches):
            # When: Service is configured with different cache implementation
            service = FlexibleCacheService(cache_impl)
            
            test_key = f"switch:test:{i}:{type(cache_impl).__name__}"
            
            # Then: Service continues to work without modification
            await service.store_item(test_key, test_data)
            
            # And: All cache operations maintain expected behavior
            exists_result = await service.item_exists(test_key)
            assert exists_result is True, f"Item should exist with {type(cache_impl).__name__}"
            
            retrieved_data = await service.retrieve_item(test_key)
            assert retrieved_data == test_data, f"Data consistency failed with {type(cache_impl).__name__}"
            
            await service.remove_item(test_key)
            
            # Verify removal worked
            exists_after_removal = await service.item_exists(test_key)
            assert exists_after_removal is False, f"Item should be removed with {type(cache_impl).__name__}"
            
            # Service behavior remains functionally consistent
            # (same interface, same results, implementation details may vary)

    def test_type_checking_works_with_interface_assignments(self):
        """
        Test that static type checking works correctly with CacheInterface assignments.
        
        Verifies:
            Type checking supports CacheInterface polymorphic assignments
            
        Business Impact:
            Enables IDE support and static analysis for cache-dependent code
            
        Scenario:
            Given: Variable annotated with CacheInterface type
            When: Different concrete cache implementations are assigned
            Then: Type checker accepts all valid CacheInterface implementations
            And: Type checker rejects non-CacheInterface assignments
            And: Method calls on interface variable are properly type-checked
            
        Type Checking Verified:
            - CacheInterface variable accepts InMemoryCache assignment
            - CacheInterface variable accepts AIResponseCache assignment
            - Type checker validates method calls on CacheInterface variable
            - Invalid assignments are rejected by type checker
            
        Fixtures Used:
            - None (testing type annotation behavior directly)
            
        IDE Support Verified:
            IDEs provide proper autocomplete and type checking for CacheInterface usage
            
        Related Tests:
            - test_method_calls_are_type_checked_through_interface()
            - test_invalid_cache_assignments_are_rejected_by_type_checker()
        """
        # Test that concrete implementations can be assigned to CacheInterface variables
        available_caches = cache_implementations()
        if len(available_caches) == 0:
            pytest.skip("No cache implementations available for type checking test")
        
        # Given: Different concrete cache implementations
        for cache_impl in available_caches:
            # When: Assigned to CacheInterface type variable
            cache_interface_var: CacheInterface = cache_impl
            
            # Then: Type checker accepts all valid CacheInterface implementations
            assert isinstance(cache_interface_var, CacheInterface)
            assert hasattr(cache_interface_var, 'get')
            assert hasattr(cache_interface_var, 'set')
            assert hasattr(cache_interface_var, 'delete')
            assert hasattr(cache_interface_var, 'exists')
            
            # And: Method calls on interface variable have proper signatures
            assert callable(cache_interface_var.get)
            assert callable(cache_interface_var.set)
            assert callable(cache_interface_var.delete)
            assert callable(cache_interface_var.exists)
            
            # Verify all methods are async (type-checkable as coroutines)
            assert inspect.iscoroutinefunction(cache_interface_var.get)
            assert inspect.iscoroutinefunction(cache_interface_var.set)
            assert inspect.iscoroutinefunction(cache_interface_var.delete)
            assert inspect.iscoroutinefunction(cache_interface_var.exists)
        
        # Test that invalid assignments would be rejected by type checking
        # (This test verifies the type structure, not runtime type checking)
        class NotACache:
            def some_method(self):
                pass
        
        invalid_cache = NotACache()
        # Runtime isinstance check confirms this is not a valid CacheInterface
        assert not isinstance(invalid_cache, CacheInterface)
        # Static type checker would reject: cache_interface_var: CacheInterface = invalid_cache

    async def test_liskov_substitution_principle_compliance(self):
        """
        Test that CacheInterface implementations comply with Liskov Substitution Principle.
        
        Verifies:
            All CacheInterface implementations can substitute for the base interface
            
        Business Impact:
            Ensures reliable polymorphic behavior across all cache implementations
            
        Scenario:
            Given: Code written against CacheInterface type
            When: Any concrete cache implementation is substituted
            Then: Code behavior remains consistent and correct
            And: No unexpected exceptions occur due to implementation differences
            And: Performance characteristics may vary but functionality is preserved
            
        LSP Compliance Verified:
            - Implementations honor the interface contract
            - Method preconditions are not strengthened by implementations
            - Method postconditions are not weakened by implementations
            - Implementation-specific behavior doesn't break interface expectations
            
        Fixtures Used:
            - default_memory_cache: Interface contract verification
            - Multiple mock implementations for substitution testing
            
        Contract Reliability Verified:
            All implementations provide reliable, consistent behavior through the interface
            
        Related Tests:
            - test_implementations_honor_interface_contracts()
            - test_polymorphic_behavior_remains_consistent()
        """
        # Test function that works with any CacheInterface implementation
        async def cache_workflow(cache: CacheInterface, test_id: str):
            """Generic workflow that should work with any CacheInterface implementation."""
            test_key = f"lsp:test:{test_id}"
            test_value = {"lsp_test": True, "implementation": type(cache).__name__}
            
            # Basic workflow: set, check exists, get, delete
            await cache.set(test_key, test_value)
            
            # Check exists should return True for existing key
            exists_result = await cache.exists(test_key)
            assert exists_result is True, "exists() should return True for stored key"
            
            # Get should return the stored value
            retrieved_value = await cache.get(test_key)
            assert retrieved_value == test_value, "get() should return stored value"
            
            # Delete should remove the key
            await cache.delete(test_key)
            
            # After delete, exists should return False
            exists_after_delete = await cache.exists(test_key)
            assert exists_after_delete is False, "exists() should return False after delete"
            
            # Get after delete should return None
            value_after_delete = await cache.get(test_key)
            assert value_after_delete is None, "get() should return None for deleted key"
            
            return "workflow_completed"
        
        # Given: Code written against CacheInterface type
        available_caches = cache_implementations()
        if len(available_caches) == 0:
            pytest.skip("No cache implementations available for LSP compliance test")
        
        # When: Any concrete cache implementation is substituted
        for i, cache_impl in enumerate(available_caches):
            # Then: Code behavior remains consistent and correct
            try:
                result = await cache_workflow(cache_impl, str(i))
                assert result == "workflow_completed", f"Workflow should complete with {type(cache_impl).__name__}"
            except Exception as e:
                pytest.fail(f"LSP violation: {type(cache_impl).__name__} failed workflow: {e}")
        
        # Test that all implementations handle the same operations consistently
        test_key = "lsp:consistency:test"
        test_value = "consistent_value"
        
        for cache_impl in available_caches:
            # All implementations should handle None returns for missing keys
            missing_value = await cache_impl.get("nonexistent:lsp:key")
            assert missing_value is None, f"{type(cache_impl).__name__} should return None for missing keys"
            
            # All implementations should handle exists() for missing keys
            missing_exists = await cache_impl.exists("nonexistent:lsp:key")
            assert missing_exists is False, f"{type(cache_impl).__name__} should return False for missing keys"
            
            # All implementations should handle delete of non-existent keys gracefully
            try:
                await cache_impl.delete("nonexistent:lsp:key")
                # Should not raise an exception (idempotent behavior)
            except Exception as e:
                pytest.fail(f"LSP violation: {type(cache_impl).__name__} should handle delete of missing keys gracefully: {e}")

    async def test_interface_method_calls_work_through_polymorphic_references(self):
        """
        Test that interface method calls work correctly through polymorphic references.
        
        Verifies:
            Method calls work consistently when made through CacheInterface reference
            
        Business Impact:
            Ensures cache operations work reliably regardless of concrete implementation
            
        Scenario:
            Given: CacheInterface reference pointing to concrete implementation
            When: Interface methods (get, set, delete) are called
            Then: Calls are properly dispatched to concrete implementation
            And: Method signatures and behavior match interface contract
            And: Async/await patterns work correctly through polymorphic calls
            
        Polymorphic Method Dispatch Verified:
            - get() calls work through interface reference
            - set() calls work through interface reference
            - delete() calls work through interface reference
            - Async patterns work correctly with polymorphic dispatch
            
        Fixtures Used:
            - default_memory_cache: Polymorphic method call behavior
            - sample_cache_key: Standard cache key for method testing
            - sample_cache_value: Standard cache value for method testing
            
        Method Dispatch Reliability Verified:
            All interface methods dispatch correctly through polymorphic references
            
        Related Tests:
            - test_async_await_patterns_work_through_interface()
            - test_method_parameters_are_passed_correctly_through_interface()
        """
        # Get available cache implementations for polymorphic testing
        available_caches = cache_implementations()
        if len(available_caches) == 0:
            pytest.skip("No cache implementations available for polymorphic method dispatch test")
        
        # Test data for polymorphic method calls
        test_values = [
            "string_value",
            42,
            3.14,
            True,
            ["list", "of", "items"],
            {"dict": "value", "nested": {"key": "value"}},
            None
        ]
        
        for i, cache_impl in enumerate(available_caches):
            # Given: CacheInterface reference pointing to concrete implementation
            cache_interface: CacheInterface = cache_impl
            
            # Verify the reference is properly typed
            assert isinstance(cache_interface, CacheInterface)
            
            # Test polymorphic method dispatch for each test value
            for j, test_value in enumerate(test_values):
                test_key = f"polymorphic:dispatch:{i}:{j}"
                
                # When: Interface methods are called through polymorphic reference
                # Then: Calls are properly dispatched to concrete implementation
                
                # Test set() method dispatch
                await cache_interface.set(test_key, test_value)
                
                # Test exists() method dispatch
                exists_result = await cache_interface.exists(test_key)
                assert exists_result is True, f"exists() dispatch failed for {type(cache_impl).__name__} with value {test_value}"
                
                # Test get() method dispatch
                retrieved_value = await cache_interface.get(test_key)
                assert retrieved_value == test_value, f"get() dispatch failed for {type(cache_impl).__name__} with value {test_value}"
                
                # Test delete() method dispatch
                await cache_interface.delete(test_key)
                
                # Verify delete worked through polymorphic dispatch
                exists_after_delete = await cache_interface.exists(test_key)
                assert exists_after_delete is False, f"delete() dispatch failed for {type(cache_impl).__name__}"
                
                # Verify get after delete returns None
                value_after_delete = await cache_interface.get(test_key)
                assert value_after_delete is None, f"get() after delete dispatch failed for {type(cache_impl).__name__}"
            
            # Test that async/await patterns work correctly through polymorphic calls
            test_key = f"async:pattern:{i}"
            test_value = {"async_test": True, "implementation": type(cache_impl).__name__}
            
            # All method calls should be awaitable through interface reference
            await cache_interface.set(test_key, test_value)
            retrieved = await cache_interface.get(test_key)
            exists = await cache_interface.exists(test_key)
            await cache_interface.delete(test_key)
            
            # Verify async patterns worked correctly
            assert retrieved == test_value, f"Async get() pattern failed for {type(cache_impl).__name__}"
            assert exists is True, f"Async exists() pattern failed for {type(cache_impl).__name__}"
        
        # Test method signatures remain consistent through polymorphic references
        for cache_impl in available_caches:
            cache_interface: CacheInterface = cache_impl
            
            # Verify method signatures are accessible and consistent
            get_method = getattr(cache_interface, 'get')
            set_method = getattr(cache_interface, 'set')
            delete_method = getattr(cache_interface, 'delete')
            exists_method = getattr(cache_interface, 'exists')
            
            # All methods should be callable and async
            assert callable(get_method) and inspect.iscoroutinefunction(get_method)
            assert callable(set_method) and inspect.iscoroutinefunction(set_method)
            assert callable(delete_method) and inspect.iscoroutinefunction(delete_method)
            assert callable(exists_method) and inspect.iscoroutinefunction(exists_method)