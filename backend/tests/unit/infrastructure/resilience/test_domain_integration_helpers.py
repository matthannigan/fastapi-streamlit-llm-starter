"""
Helper utilities for tests that mix domain and infrastructure concerns.

This file provides utilities for tests that need to simulate domain service
registration with the resilience infrastructure. These are temporary helpers
until the domain/infrastructure test separation is fully implemented.
"""

from app.infrastructure.resilience import ResilienceStrategy


def register_text_processing_operations(resilience_service):
    """
    Register typical text processing operations with resilience service.
    
    This simulates what TextProcessorService would do during initialization.
    Used for tests that need to verify infrastructure behavior with registered operations.
    """
    operations = {
        "summarize_text": ResilienceStrategy.BALANCED,
        "analyze_sentiment": ResilienceStrategy.AGGRESSIVE,
        "extract_key_points": ResilienceStrategy.BALANCED,
        "generate_questions": ResilienceStrategy.BALANCED,
        "answer_question": ResilienceStrategy.CONSERVATIVE,
    }
    
    for operation_name, strategy in operations.items():
        resilience_service.register_operation(operation_name, strategy)
    
    return list(operations.keys())


def register_legacy_operation_names(resilience_service):
    """
    Register operations using legacy naming (for backward compatibility tests).
    
    These match the old hardcoded operation names that were in the orchestrator.
    """
    legacy_operations = {
        "summarize": ResilienceStrategy.CONSERVATIVE,
        "sentiment": ResilienceStrategy.AGGRESSIVE,
        "key_points": ResilienceStrategy.BALANCED,
        "questions": ResilienceStrategy.BALANCED,
        "qa": ResilienceStrategy.CRITICAL,
    }
    
    for operation_name, strategy in legacy_operations.items():
        resilience_service.register_operation(operation_name, strategy)
    
    return list(legacy_operations.keys())


def register_custom_operations(resilience_service, operations_config):
    """
    Register custom operations for testing specific scenarios.
    
    Args:
        resilience_service: The resilience service instance
        operations_config: Dict mapping operation names to ResilienceStrategy
    
    Returns:
        List of registered operation names
    """
    for operation_name, strategy in operations_config.items():
        resilience_service.register_operation(operation_name, strategy)
    
    return list(operations_config.keys())


class MockDomainService:
    """
    Mock domain service that registers operations.
    
    Useful for testing how the infrastructure handles domain service integration.
    """
    
    def __init__(self, resilience_service, operations=None):
        self.resilience_service = resilience_service
        self.registered_operations = []
        
        if operations is None:
            operations = {
                "domain_operation_1": ResilienceStrategy.BALANCED,
                "domain_operation_2": ResilienceStrategy.AGGRESSIVE,
            }
        
        self._register_operations(operations)
    
    def _register_operations(self, operations):
        """Register operations with the resilience service."""
        for operation_name, strategy in operations.items():
            self.resilience_service.register_operation(operation_name, strategy)
            self.registered_operations.append(operation_name)
    
    def get_registered_operations(self):
        """Get list of operations registered by this domain service."""
        return self.registered_operations.copy()


def create_test_resilience_service_with_operations(settings=None, operation_type="text_processing"):
    """
    Create a resilience service with pre-registered operations for testing.
    
    Args:
        settings: Optional settings object
        operation_type: Type of operations to register ("text_processing", "legacy", "custom")
    
    Returns:
        Tuple of (resilience_service, registered_operations)
    """
    from app.infrastructure.resilience import AIServiceResilience
    
    service = AIServiceResilience(settings=settings)
    
    if operation_type == "text_processing":
        operations = register_text_processing_operations(service)
    elif operation_type == "legacy":
        operations = register_legacy_operation_names(service)
    elif operation_type == "custom":
        custom_ops = {
            "test_op_1": ResilienceStrategy.BALANCED,
            "test_op_2": ResilienceStrategy.CRITICAL,
        }
        operations = register_custom_operations(service, custom_ops)
    else:
        raise ValueError(f"Unknown operation_type: {operation_type}")
    
    return service, operations 