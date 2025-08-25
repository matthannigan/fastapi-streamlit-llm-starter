# **Modern AI Prompt Templates for Docstring-Driven Testing**

## **Template Set for Current Project Architecture**

### **Template 1: Initial Philosophy Alignment**

```
I need to generate unit tests following our project's docstring-driven testing philosophy as described in `docs/guides/developer/TESTING.md`.

**Core Project Principles** (please confirm understanding):

1. **The Golden Rule**: "Test the public contract documented in the docstring. Do NOT test the implementation code inside a function."

2. **Docstring-Driven Development**: Use comprehensive docstrings as specifications for test generation, NOT the implementation code.

3. **Behavior-Focused Testing**: Test what functions SHOULD do (from docstrings), not how they currently work internally.

4. **Strategic Mocking Hierarchy**:
   - ALWAYS mock: External APIs, file system, databases, network calls
   - SOMETIMES mock: Redis, time operations, configuration (based on scope)
   - RARELY mock: Internal business logic, domain services, utilities

5. **Test Organization**: 
   - `backend/tests/functional/`: End-to-end workflows
   - `backend/tests/integration/`: Component interactions  
   - `backend/tests/unit/`: Isolated component behaviors (primary focus)
   - `backend/tests/manual/`: Real service integration

**Task**: Please confirm you understand these principles and are ready to apply docstring-driven test generation.

Before proceeding, explain why `mock.assert_called_with()` is considered an anti-pattern in our approach.
```

### **Template 2: Docstring Contract Extraction**

```
Analyze the docstrings for `backend/contracts/infrastructure/cache/base.pyi` and extract the testable contracts. All docstrings were prepared using `docs/guides/developer/DOCSTRINGS_CODE.md` guidance.

**IMPORTANT**: Only extract what is explicitly documented in the docstrings. Do NOT analyze the implementation code.

**For each public method, extract:**

1. **Args Contract**:
   - What input types are documented?
   - What validation rules are specified?
   - What input ranges or constraints are mentioned?
   - What inputs should cause validation errors?

2. **Returns Contract**:
   - What return type/structure is documented?
   - What are the possible return values?
   - Under what conditions are different values returned?

3. **Raises Contract**:
   - What exceptions are documented?
   - Under what specific conditions are they raised?
   - What should trigger each exception type?

4. **Behavior Contract**:
   - What observable outcomes are described?
   - What side effects are documented?
   - What state changes should occur?
   - What operations are performed in sequence?

5. **Examples**:
   - Are there usage examples in docstrings?
   - Do examples show expected inputs/outputs?
   - Can examples be converted to test cases?

**Output Format**:
```
Method: method_name()
Args: [documented arg constraints]
Returns: [documented return contract] 
Raises: [documented exceptions and conditions]
Behavior: [documented observable outcomes]
Examples: [any docstring examples]
```

**Critical Rule**: If a behavior isn't documented in the docstring, don't include it in the test contracts.

Save your new analysis or update a pre-existing one at `backend/contracts/infrastructure/cache/base.md`.
```

### **Template 3: Test Architecture Design**

```
Design the test architecture for `backend/app/infrastructure/cache/base.py` based on the docstring contracts documented in `backend/contracts/infrastructure/cache/base.md`.

**Architecture Decisions**:

3. **Test Class Structure**:
   - How should test classes be organized?
   - Group by: method, behavior type, scenario complexity?

4. **Fixture Requirements**:
   - What external dependencies need mocking (follow mocking hierarchy)?
   - What test data fixtures are needed?
   - What component instances need to be created?

**Mocking Strategy Application**:
Based on docstring analysis:
- **External Systems to Mock**: [list external dependencies mentioned in docstrings]
- **Infrastructure to Mock**: [list infrastructure mentioned in docstrings]  
- **Internal Components to NOT Mock**: [list internal collaborators to leave real]

**conftest.py Fixture Plan**:
- Global fixtures needed: [cross-cutting concerns]
- Category fixtures needed: [category-specific mocks]
- Component fixtures needed: [component-specific setup]

Design the complete testing architecture with proper fixture hierarchy.
```

### **Template 4: Systematic Test Implementation**

```
Implement tests by systematically converting each docstring contract into test code.

**Docstring Contracts**: [from previous analysis]
**Test Architecture**: [from previous design]

**Implementation Rules**:

1. **Systematic Conversion**:
   - Args section → `test_[method]_validates_[input_constraint]()`
   - Returns section → `test_[method]_returns_[expected_structure]()`
   - Raises section → `test_[method]_raises_[exception]_when_[condition]()`
   - Behavior section → `test_[method]_[observable_outcome]()`
   - Examples section → `test_[method]_[example_scenario]()`

2. **Test Structure Pattern**:
```python
def test_method_behavior_expected_outcome(self, fixtures):
    """
    Test that method produces documented behavior.
    
    Docstring Contract: [quote relevant docstring section]
    Business Impact: [why this matters to users/system]
    Test Scenario: [specific scenario being tested]
    Success Criteria: [what constitutes success]
    """
    # Arrange - Set up test data and configure mocks
    input_data = [test data based on docstring examples]
    mock_dependency.configure_for_scenario([based on docstring])
    
    # Act - Call the method being tested
    result = component.method(input_data)
    
    # Assert - Verify documented outcomes only
    assert result.[documented_property] == [expected_value]
    assert component.get_[observable_state]() == [expected_state]
```

3. **Assertion Focus**:
   - ✅ Assert on return values matching docstring contracts
   - ✅ Assert on documented side effects and state changes
   - ✅ Assert on documented exception conditions
   - ❌ Never assert on mock.assert_called_with()
   - ❌ Never test private methods or undocumented behavior

4. **Test Documentation Requirements**:
   Each test must include docstring with:
   - Brief description of behavior being verified
   - Reference to specific docstring contract
   - Business impact explanation
   - Test scenario description

**Generate complete test implementation** following these patterns for all identified contracts.
```

### **Template 5: Behavior Validation & Anti-Pattern Detection**

```
Review the implemented tests for behavior-driven quality and fix any anti-patterns.

**Review Criteria**:

✅ **Good Patterns** (keep these):
- Test names describe documented behavior, not implementation
- Tests assert on return values and documented side effects
- Tests would pass if implementation changed but behavior stayed same
- Mocks are only used for external systems and infrastructure
- Test docstrings explain business value and docstring contracts

❌ **Anti-Patterns** (fix these):
- Tests use `mock.assert_called_with()` or similar internal call assertions
- Tests reference private methods or undocumented behavior
- Test names describe "how" instead of "what"
- Tests mock internal business logic unnecessarily
- Tests couple to specific implementation details

**Refactoring Process**:
For each anti-pattern found:

1. **Identify the Intent**: What is this test trying to validate?
2. **Find the Behavior**: What docstring contract does this relate to?
3. **Rewrite for Outcome**: How can we test the observable outcome instead?

**Example Refactoring**:
```python
# ❌ BAD - Tests implementation details
def test_cache_calls_redis_set():
    mock_redis.set.assert_called_with("key", "value")

# ✅ GOOD - Tests documented behavior  
def test_cache_stores_and_retrieves_data():
    cache.store("key", "value")
    result = cache.retrieve("key") 
    assert result == "value"
```

**Quality Metrics**:
- All assertions focus on documented contracts: [Yes/No]
- No internal method call testing: [Yes/No]  
- Test names reflect behavior: [Yes/No]
- Coverage meets tier target: [percentage]
- Tests run independently and consistently: [Yes/No]

**Review each test** and provide refactoring suggestions for any anti-patterns found.
```

### **Template 6: Project Integration & Final Validation**

```
Perform final integration validation to ensure tests work within the project ecosystem.

**Project Integration Checklist**:

1. **Structure Compliance**:
   - Tests placed in correct directory: tests/[category]/
   - Fixtures follow conftest.py hierarchy properly
   - Import statements use project patterns
   - File and class naming follows project conventions

2. **Fixture Integration**:
   - Do fixtures integrate with existing global fixtures?
   - Are fixture scopes appropriate (session/module/function)?
   - Do fixture docstrings follow project documentation standards?
   - Are there any fixture conflicts or redundancies?

3. **Test Execution**:
   - Do tests run with existing pytest configuration?
   - Are proper test markers applied (@pytest.mark.asyncio, @pytest.mark.slow, etc.)?
   - Do tests work with parallel execution (pytest-xdist)?
   - Are test execution times reasonable for category?

4. **Coverage & Quality**:
   - Does coverage meet tier requirements: [X%]?
   - Are all docstring contracts covered by tests?
   - Do tests provide meaningful quality assurance?
   - Would removing any test reduce confidence in the system?

5. **Documentation Integration**:
   - Do test docstrings follow DOCSTRINGS_TESTS.md standards?
   - Is test organization documented clearly?
   - Are any README updates needed?
   - Do tests serve as living documentation?

6. **CI/CD Compatibility**:
   - Will tests work in GitHub Actions environment?
   - Are external dependencies properly mocked for CI?
   - Do tests integrate with existing make targets?
   - Are there any environment-specific issues?

**Final Validation**:
Run complete test validation:
```bash
# Test execution
pytest tests/[category]/test_[component].py -v

# Coverage check  
pytest tests/[category]/test_[component].py --cov=app.[component_path] --cov-report=term-missing

# Integration with existing suite
make test-backend-unit
```

**Deliverables**:
- [ ] All tests pass consistently
- [ ] Coverage meets project standards
- [ ] No anti-patterns remain
- [ ] Integration verified with existing test suite
- [ ] Documentation is complete and helpful

Provide final summary of test quality and any remaining recommendations.
```

## **Context Preservation Between Sessions**

### **Session State Template**

```markdown
## AI Testing Session Context

**Project**: FastAPI-Streamlit-LLM Template
**Component**: [component name and path]
**Session**: [X of Y] - [current step name]

**Completed Steps**:
- [✓] Step 1: Philosophy alignment confirmed
- [✓] Step 2: Docstring contracts extracted
- [ ] Step 3: Architecture designed
- [ ] Step 4: Tests implemented
- [ ] Step 5: Anti-patterns reviewed
- [ ] Step 6: Integration validated

**Key Decisions Made**:
- Test category: [functional/integration/unit/manual]
- Coverage target: [percentage based on tier]
- Mocking strategy: [external systems to mock]
- File organization: [single/multiple files, naming]

**Docstring Contracts Identified**:
[paste key contracts for context]

**Next Session Focus**: [what to work on next]

**Quality Standards**: 
- Follow Golden Rule: test docstring contracts, not implementation
- Use behavior-driven test names and assertions
- Mock only at system boundaries
- Include comprehensive test documentation
```

## **Key Improvements Over Original Approach**

1. **Docstring-First**: Starts with docstring analysis rather than code examination
2. **Current Project Alignment**: References actual project structure, philosophy, and patterns
3. **Sophisticated Mocking**: Follows project's nuanced mocking hierarchy
4. **Quality Integration**: Ensures compatibility with existing test ecosystem
5. **Documentation Focus**: Emphasizes business value and behavioral documentation
6. **Anti-Pattern Prevention**: Proactive detection and correction of implementation coupling

These templates should produce tests that fully align with the project's sophisticated testing philosophy while providing clear, actionable guidance for AI collaboration.