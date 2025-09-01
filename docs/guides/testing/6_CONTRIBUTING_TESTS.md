---
sidebar_label: Contributing
---

# Contributing to Tests

## Guidelines

1. **Write tests for new features**: All new code should include tests
2. **Maintain coverage**: Aim for >90% test coverage
3. **Test edge cases**: Include tests for error conditions and edge cases

> **📖 For comprehensive exception testing patterns**, see the **[Exception Handling Guide](../developer/EXCEPTION_HANDLING.md)** which covers:
> - Testing exception hierarchy and classification
> - Unit testing patterns for exception handling
> - API testing with proper status code validation
> - Exception classification testing for resilience patterns
> - Best practices for testing error scenarios
4. **Use appropriate mocks**: Mock external dependencies appropriately
5. **Keep tests fast**: Unit tests should run quickly
6. **Document complex tests**: Add comments for complex test logic

## Pull Request Requirements

Before submitting a pull request:

1. Run the full test suite: `make test`
2. Check code quality: `make lint`
3. Format code: `make format`
4. Ensure coverage doesn't decrease
5. Add tests for new functionality

## Best Practices Summary

### DO ✅

**Testing Approach:**
- **Test user-visible behavior** and external contracts
- **Mock at system boundaries** (external APIs, databases)
- **Write descriptive test names** that explain what behavior is being verified
- **Use property-based testing** (Hypothesis) for comprehensive edge case coverage
- **Keep tests fast and deterministic** (<60s total execution time)
- **Test the happy path thoroughly** before diving into edge cases
- **Delete tests that don't add value** or are primarily testing framework/library code

**Test Organization:**
- **Follow the test pyramid** (many unit, fewer integration, minimal E2E)
- **Focus on critical user paths** with integration tests
- **Use docstring-driven test development** for better test specifications
- **Group tests by behavior** rather than by implementation structure

**Maintenance:**
- **Refactor tests alongside production code** to maintain relevance
- **Measure meaningful metrics** (critical path coverage, test execution time)
- **Review tests regularly** using the 4-question maintenance check

### DON'T ❌

**Avoid These Testing Anti-Patterns:**
- **Don't test implementation details** (internal method calls, private state)
- **Don't mock internal components** (your own services, utilities, business logic)
- **Don't write tests for trivial code** (getters/setters, one-line functions)
- **Don't aim for 100% coverage** as a primary goal
- **Don't keep brittle tests "just in case"** - delete or refactor them
- **Don't test every edge case exhaustively** - use property-based testing instead
- **Don't verify exact function call counts** unless it's user-observable behavior

**Avoid These Development Habits:**
- **Don't skip tests because they're slow** - fix the speed issue
- **Don't disable tests instead of fixing them** - address the root cause
- **Don't write tests after the fact** - test-driven or docstring-driven development works better
- **Don't optimize for vanity metrics** (total test count, line coverage percentage)

### Getting Help

- **Check test output** for specific error messages and stack traces
- **Review test configuration** in `pytest.ini` for marker and execution settings
- **Check CI logs** for additional context and environment differences  
- **Refer to pytest documentation** for advanced usage patterns
- **Use debugging tools** like `--pdb` flag for interactive debugging
