# **Updated AI-Assisted Testing Workflow**

### **Modernized Multi-Step Process for Maintainable, Docstring-Driven Unit Tests**

Based on the project's current sophisticated testing philosophy, this document provides a structured workflow for collaborating with AI assistants to generate high-quality, behavior-driven unit tests that align with the project's docstring-driven development approach.

## **Core Philosophy Integration**

The project's current testing philosophy emphasizes:

> **The Golden Rule**: Test the public contract documented in the docstring. **Do NOT test the implementation code inside a function.** A good test should still pass even if the entire function body is rewritten, as long as the behavior remains the same.

### **Key Principles (Updated)**

1. **Docstring-Driven Testing**: Use comprehensive docstrings as test specifications
2. **Behavior Over Implementation**: Focus on observable outcomes, not internal processes
3. **Contract-Based Testing**: Test what functions promise to do, not how they do it
4. **Minimal Strategic Mocking**: Mock only at system boundaries, not internal collaborators
5. **Test Organization by Purpose**: Organize tests by functional purpose (functional/integration/unit/manual)

## **Enhanced 6-Step Workflow**

### **Step 1: Docstring Analysis & Contract Identification**

**Goal**: Extract testable behaviors from rich docstrings rather than analyzing code implementation

**Process**:
```
Please analyze the docstrings for [COMPONENT_NAME] and extract the testable contracts.

From each docstring, identify:
1. **Args contracts**: What inputs are valid? What validation rules exist?
2. **Returns contracts**: What should the output structure/content be?
3. **Raises contracts**: What exceptions should be raised for what conditions?
4. **Behavior contracts**: What observable outcomes are documented?
5. **Examples**: Any docstring examples that can become tests?

Focus ONLY on what's documented in docstrings. Ignore implementation details.

Component: [path/to/component]
Testing Tier: [Infrastructure >90% / Domain >70% / Core >85% / API >80%]
```

**Validation**: AI should list specific behaviors from docstrings without referencing implementation details.

### **Step 2: Test Architecture Planning**

**Goal**: Determine the appropriate test organization and fixture needs based on current project structure

**Process**:
```
Based on the docstring analysis, plan the test architecture for [COMPONENT_NAME].

Use the project's current test organization:

**Functional Tests** (if applicable):
- User-facing workflows that involve this component
- API contracts that this component supports
- End-to-end behaviors documented in docstrings

**Integration Tests** (if applicable):
- Component interactions with infrastructure services
- Cross-boundary behaviors documented in docstrings

**Unit Tests** (primary focus):
- Pure function behaviors from docstrings
- Individual component behaviors in isolation
- Input validation and error handling from docstring contracts

**Test File Organization**:
- Follow current project pattern: tests/[category]/test_[component_name].py
- Target coverage: [tier-appropriate percentage]
- Fixture requirements: [list needed mocks based on docstring dependencies]
```

### **Step 3: Fixture Design (System Boundary Mocking)**

**Goal**: Create fixtures that mock only at system boundaries, following current project patterns

**Process**:
```
Design fixtures for [COMPONENT_NAME] following the project's mocking hierarchy:

**ALWAYS Mock** (external systems):
- LLM APIs and external services
- Network calls to third parties
- File system operations (for unit tests)
- Database connections (for unit tests)

**SOMETIMES Mock** (infrastructure boundaries):
- Redis/cache services (depending on test scope)
- Time-dependent operations (for determinism)
- Configuration services (for test isolation)

**RARELY Mock** (internal collaborators):
- Internal business logic
- Domain services and utilities
- Internal helper functions

Create fixtures in appropriate conftest.py following the hierarchy:
- Global: tests/conftest.py (cross-cutting concerns)
- Category: tests/[category]/conftest.py (category-wide fixtures) 
- Component: tests/[category]/[component]/conftest.py (component-specific)

For each fixture, provide proper docstrings explaining purpose, scope, and usage.
```

### **Step 4: Docstring-to-Test Conversion**

**Goal**: Systematically convert docstring contracts into behavior-focused tests

**Process**:
```
Convert the docstring contracts into test implementations using this systematic mapping:

**Args section** → Input validation and boundary testing
**Returns section** → Output structure and content verification
**Raises section** → Exception condition testing
**Behavior section** → Observable outcome testing
**Examples section** → Direct conversion to executable tests

For each test:
1. Use descriptive names that reflect docstring behavior
2. Follow Arrange-Act-Assert pattern
3. Assert on outcomes, never on internal calls
4. Include comprehensive docstrings explaining WHY the test exists

Test Naming Pattern: `test_[documented_behavior]_[expected_outcome]`

Example:
```python
def test_validate_config_rejects_invalid_structure():
    """
    Test that config validation properly rejects malformed configurations.
    
    Docstring Contract: "Raises ValidationError if config is missing required fields"
    Business Impact: Prevents startup with invalid configuration
    Test Scenario: Config missing 'api_key' field should raise ValidationError
    """
```

### **Step 5: Behavior Verification & Anti-Pattern Check**

**Goal**: Ensure tests follow behavior-driven principles and avoid implementation coupling

**Review Checklist**:
```
Review each test against behavior-driven principles:

✅ **GOOD Patterns**:
- Tests observable outcomes from docstrings
- Survives implementation refactoring
- Uses descriptive test names reflecting behavior
- Mocks only at system boundaries
- Asserts on function returns/side effects
- Documents business value in test docstrings

❌ **Anti-Patterns to Fix**:
- Tests internal method calls (mock.assert_called_with)
- Tests private attributes or methods
- Mocks internal collaborators unnecessarily  
- Names describe implementation, not behavior
- Tests undocumented behaviors
- Brittle assertions on internal state

**Refactoring Process**:
For any anti-patterns found, ask: "What observable outcome does this test actually validate?"
Then rewrite to test that outcome directly.
```

### **Step 6: Integration with Project Testing Ecosystem**

**Goal**: Ensure tests integrate properly with existing project structure and standards

**Integration Checklist**:
```
Final integration validation:

**Project Structure**:
- [ ] Tests placed in correct category directory
- [ ] Fixtures follow conftest.py hierarchy
- [ ] Imports use project patterns
- [ ] Naming follows project conventions

**Coverage & Quality**:
- [ ] Coverage meets tier requirements
- [ ] All docstring contracts have corresponding tests
- [ ] Test execution time is reasonable (<100ms per unit test)
- [ ] Tests pass consistently and independently

**Documentation**:
- [ ] Test docstrings explain WHY tests exist
- [ ] Complex fixtures have usage documentation
- [ ] Test organization is clear and logical
- [ ] README updated if needed for new test categories

**CI/CD Integration**:
- [ ] Tests work with pytest configuration
- [ ] Proper test markers for different categories
- [ ] Integration with existing make targets
```

## **Enhanced Prompt Templates**

### **Template 1: Docstring Contract Analysis**

```
I need to generate behavior-driven tests for [COMPONENT_NAME] using our docstring-driven testing approach.

First, analyze the docstrings for this component and extract the testable contracts:

**Component**: [path/to/component]
**Testing Tier**: [Infrastructure >90% / Domain >70% / etc.]

**Extract from each docstring:**

1. **Args Contracts**: What inputs are documented as valid/invalid?
2. **Returns Contracts**: What output structure/content is promised?
3. **Raises Contracts**: What exceptions are documented for what conditions?
4. **Behavior Contracts**: What observable outcomes are described?
5. **Examples**: Any docstring examples that demonstrate expected behavior?

**Critical**: Only extract what's explicitly documented in docstrings. Do not infer behaviors from implementation code.

**Core Principle**: We test the public contract documented in docstrings, NOT the implementation details.

Please provide a structured analysis of each public method's documented contracts.
```

### **Template 2: Test Architecture & Organization**

```
Based on the docstring contracts identified, design the test architecture following our current project structure:

**Current Test Organization**:
- `functional/`: End-to-end workflows and API contracts
- `integration/`: Component interaction testing  
- `unit/`: Isolated component testing (primary focus)
- `manual/`: Real service integration tests

**For [COMPONENT_NAME]:**

1. **Determine Test Category**: Which category best fits this component's role?
2. **Plan Test Files**: How should tests be organized? Single file or multiple?
3. **Identify Fixture Needs**: What external dependencies need mocking?
4. **Coverage Strategy**: How to achieve [X]% coverage focusing on docstring contracts?

**Mocking Strategy** (follow project hierarchy):
- **Always Mock**: External APIs, file system, databases, network calls
- **Sometimes Mock**: Redis, time operations, configuration (based on test scope)
- **Rarely Mock**: Internal business logic, domain services, utilities

Design the conftest.py fixture requirements and test file organization.
```

### **Template 3: Systematic Test Implementation**

```
Implement tests by systematically converting each docstring contract into test code:

**Conversion Rules**:
- **Args section** → Input validation and boundary tests
- **Returns section** → Output verification tests  
- **Raises section** → Exception condition tests
- **Behavior section** → Observable outcome tests
- **Examples section** → Direct executable test cases

**Implementation Requirements**:

1. **Test Structure**: Use Arrange-Act-Assert pattern
2. **Test Naming**: `test_[documented_behavior]_[expected_outcome]` 
3. **Test Documentation**: Include comprehensive docstrings explaining:
   - What behavior is being verified (from docstring)
   - Business impact of this test
   - Test scenario and success criteria
4. **Assertion Focus**: Assert on outcomes, never on internal method calls

**Anti-Patterns to Avoid**:
- `mock.assert_called_with()` assertions
- Testing private methods or attributes
- Testing undocumented behavior
- Implementation-coupled assertions

Generate complete test implementation focusing on the documented contracts.
```

## **Key Improvements Over Original Workflow**

1. **Docstring-Driven**: Starts with docstring analysis instead of code analysis
2. **Current Project Alignment**: Uses actual project structure and mocking philosophy
3. **Behavior-First**: Emphasizes observable outcomes over implementation testing
4. **Strategic Mocking**: Follows project's sophisticated mocking hierarchy
5. **Comprehensive Documentation**: Includes business impact and test purpose
6. **Integration Focus**: Ensures compatibility with existing project ecosystem

This updated workflow produces tests that align with the project's sophisticated testing philosophy while providing clear guidance for AI collaboration.