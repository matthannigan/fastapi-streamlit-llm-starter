# Separate User-Facing Error Messages from Debugging Context

## Issue Type
🐛 Bug / 🎨 Enhancement

## Priority
**Medium** - Affects developer experience and error message quality, but doesn't impact functionality

## Component
`backend/app/core/exceptions.py` - Application exception base classes

## Problem Description

The current `ApplicationError` and `InfrastructureError` base classes append raw context dictionaries to user-facing error messages, resulting in verbose, redundant, and developer-unfriendly output.

### Current Behavior

When exceptions include context metadata, the `__str__()` method appends it to the formatted error message:

```python
# Current implementation in exceptions.py (lines 127-142)
def __str__(self) -> str:
    if self.context:
        return f"{self.message} (Context: {self.context})"
    return self.message
```

**Result in production startup failure:**

```
ERROR:    app.core.exceptions.ConfigurationError: 🔒 SECURITY ERROR: Production environment requires secure Redis connection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Current: Insecure connection (redis://)
✅ Required: TLS-enabled (rediss://) or authenticated connection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 How to fix this:
  [... comprehensive fix instructions ...]

📚 Detailed Documentation:
   • Security guide: docs/guides/infrastructure/CACHE.md#security
   • TLS setup: docs/guides/infrastructure/CACHE.md#tls-configuration

🌍 Environment Information:
   • Detected: production (confidence: 95.0%)
   • Redis URL: redis://localhost:6379
 (Context: {'redis_url': 'redis://localhost:6379', 'connection_type': 'redis', 'environment': 'production', 'confidence': 0.95, 'validation_type': 'production_security', 'required_fix': 'tls_connection', 'fix_options': ['tls_connection', 'automated_setup', 'insecure_override']})
```

**Issues:**
1. ❌ **Redundant Information** - Context dict duplicates information already in formatted message
2. ❌ **Poor Readability** - Raw dictionary dump is hard to parse
3. ❌ **Appears Twice** - Shows in both ERROR log line and traceback
4. ❌ **Looks Like Internal Debug Info Leaked** - Not polished for end-user consumption
5. ❌ **Violates Separation of Concerns** - Debugging metadata mixed with user-facing messages

### Expected Behavior

User-facing error messages should be clean and readable, while debugging context should be available separately for structured logging and internal diagnostics.

**Desired output:**

```
ERROR:    app.core.exceptions.ConfigurationError: 🔒 SECURITY ERROR: Production environment requires secure Redis connection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Current: Insecure connection (redis://)
✅ Required: TLS-enabled (rediss://) or authenticated connection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 How to fix this:
  [... comprehensive fix instructions ...]

📚 Detailed Documentation:
   • Security guide: docs/guides/infrastructure/CACHE.md#security

🌍 Environment Information:
   • Detected: production (confidence: 95.0%)
   • Redis URL: redis://localhost:6379
```

*(Context metadata available via structured logging for internal diagnostics)*

## Root Cause

The `ApplicationError` and `InfrastructureError` base classes unconditionally append context to string representation in `__str__()` method. This was originally designed to help debugging but conflates two different use cases:

1. **User-facing error messages** - Need to be clear, concise, and well-formatted
2. **Internal debugging metadata** - Need to be structured, comprehensive, and machine-readable

## Proposed Solution

### Architecture: Separate User-Facing from Debugging Interfaces

Modify the exception base classes to provide **two separate interfaces**:

1. `__str__()` - Clean user-facing message (no context)
2. `get_log_message()` - Structured debugging message (with context)

### Implementation

#### 1. Update `ApplicationError` Base Class

```python
# backend/app/core/exceptions.py

class ApplicationError(Exception):
    """
    Base exception for all application-specific errors within the business logic layer.

    [... existing docstring ...]
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize ApplicationError with message and optional context.

        Args:
            message: Human-readable error description for display and logging
            context: Optional dictionary with additional debugging information,
                    error metadata, or relevant state data (not shown in user output)
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """
        Generate clean user-facing string representation.

        Returns:
            Clean error message without internal debugging context
        """
        return self.message

    def get_log_message(self) -> str:
        """
        Generate structured log message including debugging context.

        This method is intended for structured logging systems, monitoring,
        and internal diagnostics where the full context is valuable.

        Returns:
            String representation with context appended for debugging

        Examples:
            >>> error = ApplicationError("Config error", {"key": "redis_url"})
            >>> print(error)  # User output
            'Config error'
            >>> logger.error(error.get_log_message())  # Structured logging
            'Config error (Context: {'key': 'redis_url'})'
        """
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message

    def get_context(self) -> Dict[str, Any]:
        """
        Get debugging context for structured logging systems.

        Returns:
            Dictionary containing debugging context metadata
        """
        return self.context
```

#### 2. Update `InfrastructureError` Base Class

Apply the same pattern to `InfrastructureError` (lines 247-263):

```python
class InfrastructureError(Exception):
    """
    Base exception for infrastructure-related errors.

    [... existing docstring ...]
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Generate clean user-facing string representation."""
        return self.message

    def get_log_message(self) -> str:
        """Generate structured log message including debugging context."""
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message

    def get_context(self) -> Dict[str, Any]:
        """Get debugging context for structured logging systems."""
        return self.context
```

#### 3. Update Global Exception Handler (Optional Enhancement)

Update `backend/app/main.py` global exception handler to use structured logging:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging."""

    # Log with full context for internal diagnostics
    if hasattr(exc, 'get_log_message'):
        logger.error(f"Request failed: {exc.get_log_message()}")
    else:
        logger.error(f"Request failed: {exc}")

    # Return clean user-facing message
    return JSONResponse(
        status_code=get_http_status_for_exception(exc),
        content={
            "detail": str(exc),  # Clean message without context
            "type": exc.__class__.__name__
        }
    )
```

#### 4. Update Logging Patterns Across Codebase

Update error logging to use `get_log_message()` where context is valuable:

```python
# Before (context appears in user output)
try:
    validate_redis_security(...)
except ConfigurationError as e:
    logger.error(f"Redis security validation failed: {e}")
    raise

# After (context only in structured logs)
try:
    validate_redis_security(...)
except ConfigurationError as e:
    logger.error(f"Redis security validation failed: {e.get_log_message()}")
    raise
```

## Benefits

1. ✅ **Clean User-Facing Errors** - Users see well-formatted messages without internal metadata
2. ✅ **Rich Debugging Context** - Developers get full context via `get_log_message()` and `get_context()`
3. ✅ **Backward Compatible** - `str(exception)` still works, just returns cleaner output
4. ✅ **Structured Logging Ready** - Context available as dictionary for JSON logging
5. ✅ **Separation of Concerns** - Clear distinction between user interface and debugging interface
6. ✅ **Professional Output** - Error messages look polished and production-ready

## Migration Path

### Phase 1: Update Base Classes (Low Risk)
- Modify `ApplicationError` and `InfrastructureError` classes
- Update docstrings and examples
- Add tests for new methods

### Phase 2: Update Critical Logging (Medium Priority)
- Update logging in `main.py` global exception handler
- Update logging in startup sequence (`lifespan()`)
- Update critical security and infrastructure error logging

### Phase 3: Gradual Adoption (Optional)
- Update logging throughout codebase to use `get_log_message()`
- Add monitoring integration using `get_context()` for structured metadata
- Update tests to verify clean user output and rich debugging context

## Testing Requirements

### Unit Tests

```python
# tests/core/test_exceptions.py

def test_application_error_clean_user_output():
    """Verify user-facing output doesn't include context."""
    error = ApplicationError(
        "User-friendly error message",
        context={"debug": "internal", "trace_id": "123"}
    )

    # User output should be clean
    assert str(error) == "User-friendly error message"
    assert "Context:" not in str(error)
    assert "debug" not in str(error)


def test_application_error_log_message_includes_context():
    """Verify structured logging includes full context."""
    error = ApplicationError(
        "Error occurred",
        context={"key": "value", "code": 42}
    )

    log_msg = error.get_log_message()
    assert "Error occurred" in log_msg
    assert "Context:" in log_msg
    assert "'key': 'value'" in log_msg
    assert "'code': 42" in log_msg


def test_application_error_get_context():
    """Verify context retrieval for structured logging systems."""
    context = {"trace_id": "abc123", "user_id": 456}
    error = ApplicationError("Test error", context=context)

    assert error.get_context() == context
    assert error.get_context()["trace_id"] == "abc123"


def test_application_error_no_context():
    """Verify clean output when no context provided."""
    error = ApplicationError("Simple error")

    assert str(error) == "Simple error"
    assert error.get_log_message() == "Simple error"
    assert error.get_context() == {}
```

### Integration Tests

```python
# tests/integration/test_startup_error_output.py

async def test_production_security_validation_clean_error_output(monkeypatch):
    """Verify production security errors have clean user-facing output."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("REDIS_URL", "redis://insecure:6379")

    with pytest.raises(ConfigurationError) as exc_info:
        async with lifespan(app):
            pass

    error_message = str(exc_info.value)

    # Should have comprehensive formatted message
    assert "🔒 SECURITY ERROR" in error_message
    assert "How to fix this" in error_message

    # Should NOT have raw context dict
    assert "Context: {" not in error_message
    assert "'redis_url':" not in error_message
    assert "'validation_type':" not in error_message
```

## Documentation Updates

### Files to Update

1. **`docs/guides/developer/EXCEPTION_HANDLING.md`**
   - Document the two interfaces: `__str__()` vs `get_log_message()`
   - Provide examples of when to use each
   - Show structured logging integration patterns

2. **`docs/guides/developer/CODE_STANDARDS.md`**
   - Add guidelines for exception context usage
   - Recommend using `get_log_message()` for internal logging
   - Emphasize clean user-facing messages

3. **`backend/app/core/exceptions.py`** (docstrings)
   - Update class docstrings with new methods
   - Add examples showing both user output and debug output

## Related Issues

- #TBD - Error message formatting standards
- #TBD - Structured logging implementation

## Impact Analysis

### Files to Modify (Minimal)
- `backend/app/core/exceptions.py` - Update base classes (~20 lines changed)
- `backend/app/main.py` - Update global exception handler (~5 lines)

### Files to Review (Optional)
- Any file logging exceptions with context (gradual migration)
- Test files for exception handling

### Breaking Changes
- **None** - This is backward compatible
- Existing code using `str(exception)` continues to work
- Context still available, just accessed differently

## Acceptance Criteria

- [ ] `ApplicationError.__str__()` returns clean message without context
- [ ] `ApplicationError.get_log_message()` returns message with context
- [ ] `ApplicationError.get_context()` returns context dictionary
- [ ] Same changes applied to `InfrastructureError`
- [ ] Unit tests pass with new behavior
- [ ] Integration tests verify clean startup error output
- [ ] Documentation updated with new patterns
- [ ] No breaking changes to existing code

## Additional Context

This issue was discovered during integration of Redis security validation into application startup. The beautifully formatted error messages with comprehensive fix instructions were being polluted by appended context dictionaries that duplicated information and looked unprofessional.

**Example error that triggered this issue:**
- Component: `backend/app/core/startup/redis_security.py`
- Function: `validate_production_security()` (line 251)
- Context passed: `redis_url`, `connection_type`, `environment`, `confidence`, `validation_type`, `required_fix`, `fix_options`

The formatted message already included all user-relevant information in a polished format, making the appended context redundant and distracting.

---

**Labels:** `enhancement`, `developer-experience`, `logging`, `exceptions`, `good-first-issue`

**Estimated Effort:** Small (2-4 hours)
- 1 hour: Implementation
- 1 hour: Testing
- 1 hour: Documentation
- 0.5 hour: Code review

**Priority Justification:** Medium priority because it doesn't affect functionality but significantly improves developer experience and production error message quality. Should be addressed before broader adoption of context-rich exceptions.
