"""
Unit tests for the CacheInterface abstract base class.

This module tests the abstract cache interface contract and ensures proper
abstraction behavior for all cache implementations. Tests focus on interface
correctness, abstract method enforcement, and polymorphic usage patterns.

Test Coverage:
    - Abstract class instantiation prevention
    - Abstract method enforcement (get, set, delete)
    - Type hints and interface contracts
    - Concrete implementation requirement validation
    - Polymorphic usage patterns

Business Impact:
    The CacheInterface ensures consistent behavior across different caching
    backends, enabling reliable polymorphic usage throughout the application.
    These tests verify that the interface contract is properly enforced.
"""

import pytest
from abc import ABC
from typing import Any, Optional
from unittest.mock import AsyncMock

# Import base module directly to avoid dependency chain issues
import sys
import importlib.util
from pathlib import Path

# Direct import of the base.py module bypassing __init__.py
backend_path = Path(__file__).parent.parent.parent.parent.parent
base_path = backend_path / "app" / "infrastructure" / "cache" / "base.py"
spec = importlib.util.spec_from_file_location("cache_base", str(base_path))
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load module spec for {base_path}")
cache_base_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_base_module)
CacheInterface = cache_base_module.CacheInterface


class TestCacheInterfaceAbstractBehavior:
    """
    Test suite for CacheInterface abstract class behavior and contract enforcement.
    
    Scope:
        - Abstract class instantiation prevention
        - Abstract method requirement validation
        - Interface contract verification
        - Type signature compliance
        
    Business Critical:
        Interface contract failures would break polymorphic cache usage throughout
        the application, causing runtime errors and inconsistent behavior.
        
    Test Strategy:
        - Unit tests for abstract behavior verification
        - Mock concrete implementations to test interface compliance
        - Type checking validation for method signatures
        - Contract enforcement testing
        
    Infrastructure Impact:
        All cache implementations depend on this interface for consistent behavior.
        Failures here would affect memory cache, Redis cache, and future implementations.
    """
    
    def test_cannot_instantiate_abstract_base_class(self):
        """
        Test that CacheInterface cannot be instantiated directly.
        
        Business Impact:
            Prevents developer errors by enforcing proper inheritance patterns
            
        Interface Contract:
            Abstract base class must prevent direct instantiation to enforce
            proper implementation of required methods
            
        Failure Risk:
            Direct instantiation would create broken cache objects that fail
            at runtime when methods are called
        """
        with pytest.raises(TypeError) as exc_info:
            CacheInterface()
        
        # Error message should indicate abstract methods prevent instantiation
        error_message = str(exc_info.value)
        assert "abstract" in error_message.lower()
        assert "instantiate" in error_message.lower()
    
    def test_inherits_from_abc(self):
        """
        Test that CacheInterface properly inherits from ABC.
        
        Technical Requirement:
            Interface must use ABC to enforce abstract method implementation
            
        Business Impact:
            Ensures proper abstract class behavior and method enforcement
            
        Verification:
            Confirms ABC inheritance enables abstract method decorators
        """
        assert issubclass(CacheInterface, ABC)
        assert isinstance(CacheInterface, type(ABC))
    
    def test_has_required_abstract_methods(self):
        """
        Test that CacheInterface defines all required abstract methods.
        
        Interface Contract:
            Must define get, set, and delete as abstract methods per docstring
            
        Business Impact:
            Missing abstract methods would allow incomplete implementations
            that fail at runtime with method calls
            
        Method Requirements:
            All methods must be async coroutines for consistent async patterns
        """
        # Check that abstract methods exist and are properly decorated
        abstract_methods = CacheInterface.__abstractmethods__
        
        expected_methods = {"get", "set", "delete"}
        assert abstract_methods == expected_methods, (
            f"Expected abstract methods {expected_methods}, "
            f"but found {abstract_methods}"
        )
    
    def test_get_method_signature(self):
        """
        Test that get method has correct signature per docstring contract.
        
        Docstring Contract:
            async def get(self, key: str) -> Any
            
        Business Impact:
            Incorrect signatures would break polymorphic usage and type checking
            
        Type Requirements:
            - key parameter must accept string type
            - return type should be Any (implementation-specific)
            - method must be async coroutine
        """
        get_method = getattr(CacheInterface, 'get')
        
        # Verify method exists and has correct annotations
        assert hasattr(CacheInterface, 'get')
        assert hasattr(get_method, '__annotations__')
        
        annotations = get_method.__annotations__
        
        # Check parameter types from docstring specification
        assert 'key' in annotations
        assert annotations['key'] == str
        
        # Return type is not explicitly annotated but docstring specifies behavior
        # Implementation-specific type handling is documented in docstring
    
    def test_set_method_signature(self):
        """
        Test that set method has correct signature per docstring contract.
        
        Docstring Contract:
            async def set(self, key: str, value: Any, ttl: Optional[int] = None)
            
        Business Impact:
            Incorrect signatures would break cache storage operations and
            prevent proper TTL handling across implementations
            
        Type Requirements:
            - key parameter must accept string type
            - value parameter must accept Any type for flexible data storage
            - ttl parameter must be Optional[int] with None default
        """
        set_method = getattr(CacheInterface, 'set')
        
        assert hasattr(CacheInterface, 'set')
        assert hasattr(set_method, '__annotations__')
        
        annotations = set_method.__annotations__
        
        # Check parameter types from docstring specification
        assert 'key' in annotations
        assert annotations['key'] == str
        assert 'value' in annotations
        assert annotations['value'] == Any
        assert 'ttl' in annotations
        assert annotations['ttl'] == Optional[int]
    
    def test_delete_method_signature(self):
        """
        Test that delete method has correct signature per docstring contract.
        
        Docstring Contract:
            async def delete(self, key: str)
            
        Business Impact:
            Incorrect signature would prevent proper cache invalidation and
            break cache cleanup operations
            
        Type Requirements:
            - key parameter must accept string type  
            - no return type specified (implementation-specific)
            - method must be async coroutine
        """
        delete_method = getattr(CacheInterface, 'delete')
        
        assert hasattr(CacheInterface, 'delete')
        assert hasattr(delete_method, '__annotations__')
        
        annotations = delete_method.__annotations__
        
        # Check parameter types from docstring specification
        assert 'key' in annotations
        assert annotations['key'] == str


class TestConcreteImplementationRequirements:
    """
    Test suite for concrete implementation requirements and interface compliance.
    
    Scope:
        - Concrete class implementation validation
        - Abstract method override requirements
        - Interface compliance verification
        - Polymorphic usage patterns
        
    Business Critical:
        Ensures that concrete cache implementations properly fulfill the interface
        contract, enabling reliable polymorphic usage across the application.
        
    Test Strategy:
        - Create minimal concrete implementations for testing
        - Verify abstract method override requirements
        - Test polymorphic usage patterns
        - Validate interface compliance
    """
    
    def test_concrete_class_requires_all_abstract_methods(self):
        """
        Test that concrete implementations must override all abstract methods.
        
        Business Impact:
            Prevents incomplete implementations that would fail at runtime
            
        Interface Contract:
            Concrete classes must implement get, set, and delete methods
            to be instantiable
            
        Implementation Requirement:
            All abstract methods must be overridden with proper async signatures
        """
        # Define incomplete implementation missing 'delete' method
        class IncompleteCache(CacheInterface):
            async def get(self, key: str):
                return None
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                pass
            # Missing delete method
        
        # Should not be able to instantiate incomplete implementation
        with pytest.raises(TypeError) as exc_info:
            IncompleteCache()
        
        error_message = str(exc_info.value)
        assert "abstract" in error_message.lower()
        assert "delete" in error_message.lower()
    
    def test_complete_implementation_can_be_instantiated(self):
        """
        Test that complete concrete implementations can be instantiated.
        
        Business Impact:
            Verifies that properly implemented cache classes work correctly
            with the abstract interface
            
        Interface Validation:
            Complete implementations should instantiate without errors and
            provide all required methods
            
        Polymorphic Usage:
            Instances should be usable through the CacheInterface type
        """
        class CompleteCache(CacheInterface):
            async def get(self, key: str):
                """Complete get implementation."""
                return None
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                """Complete set implementation."""
                pass
            
            async def delete(self, key: str):
                """Complete delete implementation."""  
                pass
        
        # Should be able to instantiate complete implementation
        cache = CompleteCache()
        
        # Should be instance of both the concrete class and interface
        assert isinstance(cache, CompleteCache)
        assert isinstance(cache, CacheInterface)
        
        # Should have all required methods
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')  
        assert hasattr(cache, 'delete')
    
    async def test_polymorphic_usage_pattern(self):
        """
        Test that concrete implementations work polymorphically through interface.
        
        Business Impact:
            Validates the primary use case of the interface - enabling polymorphic
            cache usage throughout the application
            
        Usage Pattern:
            Services should be able to accept CacheInterface type and work
            with any concrete implementation
            
        Interface Contract:
            All implementations must provide consistent async method signatures
        """
        class MockCache(CacheInterface):
            def __init__(self):
                self.storage = {}
            
            async def get(self, key: str):
                """Mock get returning stored values."""
                return self.storage.get(key)
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                """Mock set storing values in memory."""
                self.storage[key] = value
            
            async def delete(self, key: str):
                """Mock delete removing values from storage."""
                self.storage.pop(key, None)
        
        # Test polymorphic usage through interface type
        cache: CacheInterface = MockCache()
        
        # Should be able to use all interface methods
        await cache.set("test_key", "test_value")
        result = await cache.get("test_key")
        assert result == "test_value"
        
        await cache.delete("test_key")
        deleted_result = await cache.get("test_key")
        assert deleted_result is None
    
    def test_method_override_signature_compatibility(self):
        """
        Test that concrete method overrides maintain signature compatibility.
        
        Interface Contract:
            Concrete implementations must maintain compatible method signatures
            for proper polymorphic usage
            
        Business Impact:
            Signature incompatibilities would break existing code that depends
            on the interface contract
            
        Verification:
            Concrete methods should accept same parameter types as interface
        """
        class TestCache(CacheInterface):
            async def get(self, key: str):
                return None
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None):
                pass
            
            async def delete(self, key: str):
                pass
        
        cache = TestCache()
        
        # Verify method signatures are compatible with interface
        get_method = getattr(cache, 'get')
        set_method = getattr(cache, 'set')
        delete_method = getattr(cache, 'delete')
        
        # All methods should be callable (have __call__ method)
        assert callable(get_method)
        assert callable(set_method)  
        assert callable(delete_method)


class TestInterfaceDocumentationCompliance:
    """
    Test suite for interface documentation compliance and contract clarity.
    
    Scope:
        - Docstring presence and completeness
        - Interface contract documentation
        - Usage example validation
        - Behavioral specification compliance
        
    Business Critical:
        Clear interface documentation enables proper implementation and usage
        patterns, reducing development errors and ensuring consistent behavior.
        
    Documentation Requirements:
        All methods must have comprehensive docstrings with Args, Returns,
        and Behavior sections per docstring standards.
    """
    
    def test_class_has_comprehensive_docstring(self):
        """
        Test that CacheInterface has comprehensive class-level documentation.
        
        Documentation Requirement:
            Class docstring must explain interface purpose, usage patterns,
            and implementation requirements per docstring standards
            
        Business Impact:
            Clear documentation reduces implementation errors and improves
            developer understanding of cache patterns
            
        Content Requirements:
            Must include usage examples, state management notes, and
            public method descriptions
        """
        class_docstring = CacheInterface.__doc__
        
        assert class_docstring is not None
        assert len(class_docstring.strip()) > 100, "Class docstring should be comprehensive"
        
        # Check for required sections per docstring standards
        docstring_content = class_docstring.lower()
        assert "public methods" in docstring_content
        assert "state management" in docstring_content  
        assert "usage" in docstring_content
        assert "async interface" in docstring_content
    
    def test_abstract_methods_have_detailed_docstrings(self):
        """
        Test that all abstract methods have detailed docstrings with required sections.
        
        Documentation Standard:
            Each method must have Args, Returns, and Behavior sections
            per DOCSTRINGS_CODE.md standards
            
        Business Impact:
            Detailed method documentation guides proper implementation and
            prevents behavioral inconsistencies across cache backends
            
        Required Sections:
            Args, Returns, Behavior sections must be present and comprehensive
        """
        # Test get method docstring
        get_docstring = CacheInterface.get.__doc__
        assert get_docstring is not None
        assert "Args:" in get_docstring
        assert "Returns:" in get_docstring  
        assert "Behavior:" in get_docstring
        assert "key:" in get_docstring.lower()
        
        # Test set method docstring
        set_docstring = CacheInterface.set.__doc__
        assert set_docstring is not None
        assert "Args:" in set_docstring
        assert "Behavior:" in set_docstring
        assert "key:" in set_docstring.lower()
        assert "value:" in set_docstring.lower()
        assert "ttl:" in set_docstring.lower()
        
        # Test delete method docstring  
        delete_docstring = CacheInterface.delete.__doc__
        assert delete_docstring is not None
        assert "Args:" in delete_docstring
        assert "Behavior:" in delete_docstring
        assert "key:" in delete_docstring.lower()
    
    def test_behavioral_specifications_documented(self):
        """
        Test that behavioral specifications are clearly documented in method docstrings.
        
        Behavioral Requirements:
            Docstrings must specify expected behavior patterns for consistent
            implementation across different cache backends
            
        Business Impact:
            Clear behavioral specifications ensure consistent user experience
            regardless of which cache backend is used
            
        Documentation Verification:
            Key behavioral aspects must be documented for each method
        """
        # Verify get method behavioral specifications
        get_docstring = CacheInterface.get.__doc__
        get_content = get_docstring.lower()
        assert "returns none" in get_content or "none if" in get_content
        assert "preserves" in get_content and "types" in get_content
        assert "thread" in get_content or "async" in get_content
        
        # Verify set method behavioral specifications
        set_docstring = CacheInterface.set.__doc__
        set_content = set_docstring.lower()
        assert "ttl" in set_content
        assert "overwrites" in set_content
        assert "gracefully" in set_content
        
        # Verify delete method behavioral specifications
        delete_docstring = CacheInterface.delete.__doc__
        delete_content = delete_docstring.lower()
        assert "immediately" in delete_content
        assert "no-op" in delete_content or "graceful" in delete_content
        assert "idempotent" in delete_content
    
    def test_interface_usage_examples_valid(self):
        """
        Test that usage examples in interface docstring represent valid patterns.
        
        Documentation Quality:
            Usage examples must demonstrate proper interface usage patterns
            and be syntactically correct
            
        Business Impact:
            Valid examples help developers implement and use cache interfaces
            correctly, reducing integration errors
            
        Example Validation:
            Examples should show polymorphic usage, basic operations, and
            service integration patterns
        """
        class_docstring = CacheInterface.__doc__
        
        # Check for usage example presence
        assert "Usage:" in class_docstring or "```python" in class_docstring
        
        # Verify example shows polymorphic usage
        assert "CacheInterface" in class_docstring
        assert "await" in class_docstring, "Examples should show async usage"
        
        # Check for key operation examples  
        docstring_content = class_docstring.lower()
        assert "set(" in docstring_content
        assert "get(" in docstring_content  
        assert "delete(" in docstring_content