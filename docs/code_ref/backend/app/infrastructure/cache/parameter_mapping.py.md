---
sidebar_label: parameter_mapping
---

# [REFACTORED] Parameter Mapping Module for Cache Inheritance Refactoring

  file_path: `backend/app/infrastructure/cache/parameter_mapping.py`

This module provides comprehensive parameter mapping functionality to enable
AIResponseCache to properly inherit from GenericRedisCache. It separates
AI-specific parameters from generic Redis parameters and provides validation
to ensure compatibility between parameter sets.

## Classes

ValidationResult: Dataclass for parameter validation results
CacheParameterMapper: Main parameter mapping and validation logic

## Key Features

- Separates AI-specific parameters from generic Redis parameters
- Maps between AI parameter names and generic parameter equivalents
- Validates parameter compatibility and identifies conflicts
- Provides detailed validation results with specific error messages
- Supports parameter transformation and value validation
- Comprehensive logging for debugging parameter mapping issues

## Usage Examples

Basic parameter mapping:
```python
mapper = CacheParameterMapper()
ai_params = {
    'redis_url': 'redis://localhost:6379',
    'text_hash_threshold': 1000,
    'memory_cache_size': 100,
    'compression_threshold': 1000
}
generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
print(f"Generic: {generic_params}")
print(f"AI-specific: {ai_specific_params}")
```

### Parameter validation

```python
validation_result = mapper.validate_parameter_compatibility(ai_params)
if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Error: {error}")
else:
    print("All parameters are compatible")
```

## Architecture Context

This module is part of Phase 2 of the cache refactoring project, enabling
the inheritance structure where AIResponseCache extends GenericRedisCache
while maintaining backward compatibility and clear parameter separation.

## Dependencies

- dataclasses: For ValidationResult structure
- typing: For type annotations and generics
- logging: For debugging and monitoring
- app.core.exceptions: For custom exception handling
