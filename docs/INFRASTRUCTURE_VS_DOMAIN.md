# Infrastructure vs Domain Services - Architecture Guide & Code Review Standards

## Executive Summary

This document establishes the architectural distinction between **Infrastructure Services** (reusable template components) and **Domain Services** (application-specific business logic) in our FastAPI LLM template. This distinction is critical for maintaining template reusability while providing clear customization points for developers.

## Core Concepts

### Infrastructure Services 🏗️
**Definition**: Technical capabilities that are agnostic to business logic and reusable across any project.

**Characteristics**:
- Business-agnostic abstractions
- Stable APIs that rarely change
- High test coverage requirements (>90%)
- Performance-critical implementations
- Configuration-driven behavior

**Examples**:
- Cache management (Redis, memory)
- Resilience patterns (circuit breakers, retries)
- AI provider integrations
- Monitoring and observability
- Security utilities

### Domain Services 💼
**Definition**: Business-specific implementations that solve particular use cases using infrastructure services.

**Characteristics**:
- Business logic implementation
- Composed of infrastructure services
- Expected to be replaced/modified per project
- Moderate test coverage requirements (>70%)
- Feature-driven development

**Examples**:
- Text processing workflows
- Document analysis pipelines
- Customer-specific integrations
- Business rule implementations

## Architecture Principles

### 1. Dependency Direction
```
Domain Services → Infrastructure Services → External Dependencies
(changeable)        (stable)               (managed)
```

### 2. Abstraction Levels
- **Infrastructure**: "HOW to do things" (caching, retrying, monitoring)
- **Domain**: "WHAT to do" (summarize text, analyze sentiment)

### 3. Reusability Spectrum
```
External Libraries ← Infrastructure Services ← Domain Services ← Application Code
(most reusable)                                              (least reusable)
```

## Code Review Guidelines

### For Infrastructure Service Reviews

**Review Focus**:
- API stability and backward compatibility
- Performance implications
- Error handling completeness
- Configuration flexibility
- Documentation quality
- Test coverage (must be >90%)

**Example Review Comment**:
```markdown
🏗️ **Infrastructure Service Review**

Since this modifies the cache service (infrastructure), please ensure:
- [ ] API remains backward compatible
- [ ] Performance benchmarks show no regression
- [ ] Error handling covers all edge cases
- [ ] Configuration allows for different deployment scenarios
- [ ] Test coverage remains above 90%
- [ ] Documentation includes usage examples

Remember: Infrastructure changes affect ALL projects using this template.
```

### For Domain Service Reviews

**Review Focus**:
- Business logic correctness
- Proper use of infrastructure services
- Code clarity for future developers
- Adequate test coverage (>70%)
- Example quality (if applicable)

**Example Review Comment**:
```markdown
💼 **Domain Service Review**

As this is domain logic (text processing example):
- [ ] Business logic is clear and well-documented
- [ ] Infrastructure services are used appropriately
- [ ] Code serves as a good example for template users
- [ ] Tests demonstrate proper patterns

Note: This code is meant to be replaced in actual projects, so prioritize clarity over optimization.
```

## Refactoring Request Templates

### Infrastructure Service Refactoring

```markdown
## Refactoring Request: [Service Name]

**Service Type**: Infrastructure Service 🏗️
**Impact**: All projects using this template

### Objectives
- [ ] Improve performance by X%
- [ ] Enhance API flexibility while maintaining compatibility
- [ ] Reduce coupling with external dependencies

### Constraints
- MUST maintain backward compatibility
- MUST maintain or improve test coverage (>90%)
- MUST update all dependent examples
- MUST benchmark performance impact

### Success Criteria
- No breaking changes to public APIs
- Performance improvement validated
- All existing tests pass
- Documentation updated
```

### Domain Service Refactoring

```markdown
## Refactoring Request: [Service Name]

**Service Type**: Domain Service 💼
**Impact**: Example/reference implementation only

### Objectives
- [ ] Improve example clarity
- [ ] Demonstrate best practices
- [ ] Simplify for better understanding

### Constraints
- Should showcase infrastructure usage patterns
- Should be easily replaceable
- Should avoid over-engineering

### Success Criteria
- Clearer demonstration of concepts
- Easier for developers to understand and modify
- Well-commented for learning purposes
```

## Decision Framework

### When to Put Code in Infrastructure

Ask these questions:
1. **Is it business-agnostic?** Can it work without knowing the specific use case?
2. **Is it reusable?** Would multiple different applications benefit?
3. **Is it stable?** Will the API remain consistent over time?
4. **Is it technical?** Does it solve a technical rather than business problem?

If YES to all → Infrastructure Service

### When to Put Code in Domain

Ask these questions:
1. **Is it business-specific?** Does it implement particular business rules?
2. **Is it an example?** Is it meant to show how to use infrastructure?
3. **Will it be replaced?** Do you expect users to swap it for their logic?
4. **Is it feature-driven?** Does it implement end-user features?

If YES to any → Domain Service

## File Header Standards

### Infrastructure Service Header
```python
"""
Infrastructure Service: Cache Management

⚠️ STABLE API - Changes affect all template users
📋 Minimum test coverage: 90%
🔧 Configuration-driven behavior

This service provides business-agnostic caching capabilities
used across all domain services.

Change with caution - ensure backward compatibility.
"""
```

### Domain Service Header
```python
"""
Domain Service: Text Processing

📚 EXAMPLE IMPLEMENTATION - Replace in your project
💡 Demonstrates infrastructure usage patterns
🔄 Expected to be modified/replaced

This service shows how to build business logic using
infrastructure services. It's meant as a learning example.
"""
```

## Pull Request Template Addition

```markdown
## Service Classification

**What type of service does this PR modify?**
- [ ] Infrastructure Service (reusable, stable API)
- [ ] Domain Service (business logic, example)
- [ ] Both

**For Infrastructure changes:**
- [ ] Backward compatibility maintained
- [ ] Performance impact measured
- [ ] Test coverage >90%
- [ ] Documentation updated

**For Domain changes:**
- [ ] Example clarity improved
- [ ] Infrastructure usage patterns clear
- [ ] Comments explain decisions
```

## Communication Examples

### In Code Reviews

**For Infrastructure Issues**:
> "This couples the cache service to Redis-specific features. As an infrastructure service, it should remain abstraction-friendly. Consider using the strategy pattern to keep Redis-specific optimizations separate."

**For Domain Issues**:
> "This text processing logic is getting complex. Since it's a domain service example, consider breaking it into smaller, more understandable pieces that better demonstrate the patterns users should follow."

### In Architecture Discussions

**Proposing Infrastructure Addition**:
> "I propose adding rate limiting as an infrastructure service because:
> 1. It's business-agnostic (works for any API endpoint)
> 2. It's reusable across all projects
> 3. It has a stable API (limit, window, strategy)
> 4. It solves a technical problem
> This would provide value to all template users."

**Proposing Domain Addition**:
> "The text processing examples should include a batch processing workflow because:
> 1. It demonstrates infrastructure composition patterns
> 2. It's a common use case users might implement
> 3. It shows performance optimization techniques
> This would help users understand how to build their own workflows."

## Metrics for Success

### Infrastructure Services
- **Stability**: < 2 breaking changes per year
- **Reusability**: Used by >80% of domain services
- **Performance**: <5ms overhead for operations
- **Test Coverage**: >90% with edge cases

### Domain Services
- **Clarity**: New developers understand in <30 minutes
- **Replaceability**: Can swap implementation in <1 day
- **Example Quality**: Demonstrates >3 infrastructure services
- **Documentation**: 1:1 comment-to-code ratio for complex logic

## Conclusion

By maintaining this distinction, we create a template that provides immediate value through battle-tested infrastructure while giving developers clear guidance on where to add their business logic. This separation is not just architectural—it's a communication tool that helps all stakeholders understand the stability guarantees and modification expectations for different parts of the codebase.