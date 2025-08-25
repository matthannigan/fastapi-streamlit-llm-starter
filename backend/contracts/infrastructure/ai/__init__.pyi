"""
AI Infrastructure Service Package

This package provides comprehensive AI model interaction utilities with built-in security,
safety, and performance optimizations. It serves as the primary interface for all AI-related
infrastructure capabilities in the application.

## Package Architecture

The AI infrastructure follows a layered security-first approach:
- **Input Layer**: Comprehensive sanitization and prompt injection protection
- **Processing Layer**: Safe prompt construction with template system
- **Output Layer**: Response validation and safety checks (future enhancement)

## Core Components

### Input Sanitization (`input_sanitizer.py`)
Comprehensive protection against prompt injection attacks and malicious input:
- **Basic Sanitization**: Fast input cleaning for general use cases
- **Advanced Sanitization**: Deep analysis with configurable security levels
- **Prompt Injection Detection**: ML-based detection of injection attempts
- **XSS Protection**: Web-safe input filtering
- **Custom Filtering**: Configurable sanitization rules

### Prompt Builder (`prompt_builder.py`)
Safe prompt construction with template management:
- **Template System**: Pre-defined prompt templates for common operations
- **Safe Construction**: Automatic escaping and validation
- **Dynamic Variables**: Secure variable substitution
- **Template Registry**: Centralized template management

## Security Features

- **Multi-Layer Protection**: Input sanitization + prompt construction validation
- **Configurable Security Levels**: Adjustable protection based on use case
- **Attack Detection**: Comprehensive prompt injection pattern recognition
- **Safe Defaults**: Secure-by-default configuration
- **Audit Logging**: Security event tracking and monitoring

## Performance Characteristics

- **Input Sanitization**: < 5ms per operation for basic mode, < 20ms for advanced
- **Prompt Building**: < 1ms per template operation
- **Memory Efficient**: Minimal memory overhead for template caching
- **Concurrent Safe**: Thread-safe operations for high-concurrency environments

## Usage Patterns

### Basic Input Sanitization
```python
from app.infrastructure.ai import sanitize_input

# Quick sanitization for general use
clean_input = sanitize_input(user_text)

# Advanced sanitization with custom options  
clean_input = sanitize_input_advanced(
    user_text, 
    options={"security_level": "high", "preserve_formatting": True}
)
```

### Prompt Construction
```python
from app.infrastructure.ai import create_safe_prompt, get_available_templates

# Use predefined template
prompt = create_safe_prompt("summarize", {"text": user_input, "max_length": 100})

# List available templates
templates = get_available_templates()
```

### Advanced Sanitization with Custom Rules
```python
from app.infrastructure.ai import PromptSanitizer, sanitize_options

# Custom sanitizer instance
sanitizer = PromptSanitizer(config={"strict_mode": True})
result = sanitizer.sanitize(text)

# Custom sanitization options
options = sanitize_options(security_level="maximum", preserve_whitespace=False)
clean_text = sanitize_input_advanced(text, options=options)
```

## Integration with Other Infrastructure

The AI infrastructure integrates seamlessly with:
- **Cache System**: Automatic caching of sanitized inputs and built prompts
- **Monitoring**: Performance metrics and security event tracking
- **Resilience**: Graceful handling of sanitization failures
- **Security**: Integration with authentication and authorization systems

## Configuration

AI infrastructure behavior is controlled through environment variables:

```bash
# Input Sanitization Configuration
AI_SANITIZATION_LEVEL=standard     # "basic", "standard", "strict", "maximum"
AI_PROMPT_INJECTION_DETECTION=true # Enable/disable injection detection
AI_PRESERVE_FORMATTING=false       # Preserve original text formatting
AI_CUSTOM_FILTERS=[]               # Custom sanitization rules

# Performance Configuration  
AI_SANITIZATION_TIMEOUT_MS=5000   # Timeout for sanitization operations
AI_TEMPLATE_CACHE_SIZE=100         # Number of templates to cache
AI_ENABLE_METRICS=true             # Enable performance monitoring
```

## Testing Support

The package includes comprehensive testing utilities:
- **Mock Sanitizers**: Configurable mock implementations for testing
- **Test Templates**: Pre-defined templates for test scenarios
- **Performance Benchmarks**: Automated performance validation
- **Security Test Cases**: Comprehensive prompt injection test suite

## Thread Safety

All components are designed for concurrent access:
- **Immutable Templates**: Template registry uses immutable data structures
- **Stateless Operations**: Sanitization operations maintain no state
- **Thread-Safe Caching**: Template cache uses concurrent-safe data structures
- **Atomic Operations**: All configuration updates are atomic
"""

from .prompt_builder import create_safe_prompt, get_available_templates
from .input_sanitizer import sanitize_input, sanitize_input_advanced, sanitize_options, PromptSanitizer

__all__ = ['create_safe_prompt', 'get_available_templates', 'sanitize_input', 'sanitize_input_advanced', 'sanitize_options', 'PromptSanitizer']
