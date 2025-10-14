# Text Processor Service Refactoring Task Plan

## Context and Rationale

The `TextProcessorService` in `backend/app/services/text_processor.py` is well-architected but contains opportunities for targeted improvements to enhance maintainability, testability, and extensibility. This refactoring focuses on preparing the service for the upcoming `PROS_CONS` operation—a sophisticated multi-step AI workflow that generates pros/cons analysis through parallel AI calls followed by synthesis.

### Current State Analysis

**Strengths of Current Architecture:**
- Clear layered design (input → cache → AI → resilience → validation → fallback)
- Consistent resilience patterns with operation-specific strategies
- Comprehensive security through input sanitization and output validation
- Well-documented with extensive docstrings (850 lines including documentation)
- Handles 5 operations: SUMMARIZE, SENTIMENT, KEY_POINTS, QUESTIONS, QA

**Areas for Improvement:**
- **Operation Dispatch**: Growing `if/elif` chain (lines 439-450) will become unwieldy with complex operations
- **Testing Isolation**: Monolithic structure makes it harder to test individual operations independently
- **Multi-Step Operations**: No clear pattern for operations requiring multiple dependent AI calls
- **Operation Metadata**: No centralized registry of operation-specific behavior

### The PROS_CONS Challenge

The upcoming `PROS_CONS` operation introduces new complexity:
- **Three LLM calls**: Two parallel calls (pros, cons) followed by a dependent synthesis call
- **Complex orchestration**: Requires parallel execution with dependency management
- **Richer response structure**: Returns structured pros/cons lists plus synthesis
- **Longer processing time**: Multi-step nature requires robust resilience and caching

This operation type represents a new category: **multi-step dependent workflows** that don't fit cleanly into the current single-method-per-operation pattern.

### Design Philosophy: Targeted Improvement, Not Wholesale Rewrite

**Rejected Approach: Full Strategy Pattern**
After analysis, we rejected implementing a full Strategy Pattern with registry system because:
- Adds 6-7 new files and abstraction layers for only 6 operations
- Creates indirection that reduces code discoverability
- Doesn't significantly reduce touchpoints when adding operations
- Premature optimization for current scale (appropriate at 15-20+ operations, not 6)

**Adopted Approach: Surgical Refactoring**
Instead, we'll make targeted improvements:
1. Replace verbose `if/elif` chains with cleaner dispatch mechanisms
2. Extract reusable multi-step operation patterns
3. Improve operation metadata centralization
4. Enhance testability through better dependency injection
5. Add clear extension points without full plugin architecture

### Improvement Goals

- **Cleaner Operation Dispatch**: Replace growing `if/elif` chains with maintainable dispatch table
- **Multi-Step Pattern**: Establish clear pattern for complex operations like PROS_CONS
- **Enhanced Testability**: Make individual operations easier to test in isolation
- **Operation Registry**: Centralize operation metadata for resilience, fallbacks, and TTLs
- **Code Organization**: Group related methods logically without fragmenting across many files
- **Documentation**: Update docstrings and contracts to reflect new patterns

### Desired Outcome

A refactored `TextProcessorService` that:
- Maintains current architecture and all existing strengths
- Adds clean extension point for PROS_CONS and future multi-step operations
- Reduces code verbosity through dispatch tables and helper extraction
- Improves testability through better structure
- Preserves 100% backward compatibility with existing API
- Provides clear patterns for future operation additions

---

## Implementation Phases Overview

**Phase 1: Analysis & Design (Day 1)**
Analyze current implementation patterns, design improved dispatch mechanism, and create operation registry structure.

**Phase 2: Operation Metadata Centralization (Day 2)**
Extract operation-specific configuration into centralized registry for cleaner management.

**Phase 3: Dispatch Refactoring (Days 3-4)**
Replace `if/elif` chains with dispatch table and improve operation routing logic.

**Phase 4: Multi-Step Pattern Implementation (Day 5)**
Establish pattern for multi-step operations and implement PROS_CONS scaffold.

**Phase 5: Testing Infrastructure (Day 6)**
Add comprehensive tests for new patterns and improve test isolation capabilities.

**Phase 6: Documentation & Validation (Day 7)**
Update contracts, docstrings, and perform comprehensive validation.

---

## Phase 1: Analysis & Design

### Deliverable 1: Current Implementation Analysis (Critical Path)
**Goal**: Thoroughly understand current patterns, dependencies, and extension points.

#### Task 1.1: Code Structure Analysis
- [X] Analyze current operation dispatch pattern:
  - [X] Document the `if/elif` chain in `process_text()` (lines 439-450)
  - [X] List all operation handler methods (`_*_with_resilience`, core methods)
  - [X] Map resilience decorator patterns (balanced, aggressive, conservative)
  - [X] Document fallback method patterns per operation type
- [X] Analyze operation-specific configuration:
  - [X] Document `_register_operations()` patterns (lines 306-324)
  - [X] Map operation names to resilience strategies
  - [X] List operation-specific settings (temperature, max_length, etc.)
  - [X] Document TTL mapping in `_get_ttl_for_operation()` (lines 820-854)
- [X] Document testing dependencies:
  - [X] List all test files depending on `TextProcessorService`
  - [X] Identify fixture patterns and test isolation challenges
  - [X] Note any mocking patterns for AI agent calls
  - [X] Document test coverage gaps

**Analysis Complete**: See `/Users/matth/Github/MGH/fastapi-streamlit-llm-starter/dev/taskplans/current/deliverable1_current-implementation-analysis.md`

#### Task 1.2: PROS_CONS Requirements Analysis
- [X] Design PROS_CONS operation structure:
  - [X] Define request model additions (operation enum, options)
  - [X] Design response model for pros/cons/synthesis structure
  - [X] Specify prompt templates for three AI calls
  - [X] Define parallel execution strategy (asyncio.gather, TaskGroup)
- [X] Plan implementation approach:
  - [X] Design method structure (`_generate_pros_cons`, `_get_pros`, `_get_cons`, `_synthesize_pros_cons`)
  - [X] Determine resilience strategy (balanced recommended)
  - [X] Plan caching strategy for multi-step operation
  - [X] Define fallback behavior when partial failures occur
- [X] Document integration points:
  - [X] List touchpoints in `process_text()` for new operation
  - [X] Identify shared models updates needed
  - [X] Note API endpoint implications
  - [X] Consider frontend integration requirements

**Analysis Complete**: See `/Users/matth/Github/MGH/fastapi-streamlit-llm-starter/dev/taskplans/current/deliverable1_current-implementation-analysis.md`

---

### Deliverable 2: Refactoring Design Document
**Goal**: Create detailed design for improved operation dispatch and organization.

#### Task 2.1: Operation Registry Design
- [X] Design centralized operation registry structure:
  ```python
  # Example structure to design:
  OPERATION_CONFIG = {
      TextProcessingOperation.SUMMARIZE: {
          "handler": "_summarize_text_with_resilience",
          "resilience_strategy": "balanced",
          "cache_ttl": 7200,
          "fallback_type": "string",
          "requires_question": False,
          "response_field": "result",
      },
      # ... additional operations
  }
  ```
  - [X] Define configuration schema for operation metadata
  - [X] Document required vs optional metadata fields
  - [X] Plan validation logic for registry consistency
  - [X] Design accessor methods for registry queries

#### Task 2.2: Dispatch Mechanism Design
- [X] Design improved operation routing:
  - [X] Create dispatch table mapping operations to handlers
  - [X] Design argument routing logic (text, question, options)
  - [X] Plan error handling for unknown operations
  - [X] Design response field routing (result, sentiment, key_points, etc.)
- [X] Design helper methods:
  - [X] `_dispatch_operation()`: Central routing method
  - [X] `_get_operation_handler()`: Handler lookup (part of _dispatch_operation)
  - [X] `_prepare_handler_arguments()`: Argument preparation
  - [X] `_route_response_to_field()`: Response field assignment

#### Task 2.3: Multi-Step Operation Pattern Design
- [X] Design pattern for multi-step operations:
  - [X] Define abstract pattern: setup → parallel execution → synthesis
  - [X] Create helper for parallel task execution with error handling
  - [X] Design partial failure handling strategy
  - [X] Plan result aggregation and cache key generation
- [X] Document pattern application to PROS_CONS:
  - [X] Sketch implementation structure
  - [X] Define sub-task resilience handling
  - [X] Plan cache strategy for composite results
  - [X] Design fallback behavior for partial failures

**Design Complete**: See `/Users/matth/Github/MGH/fastapi-streamlit-llm-starter/dev/taskplans/current/deliverable2_refactoring-design.md`

---

## Phase 2: Operation Metadata Centralization

### Deliverable 3: Operation Registry Implementation
**Goal**: Create centralized registry for all operation-specific configuration.

#### Task 3.1: Create Operation Configuration Registry
- [X] Implement `OPERATION_CONFIG` dictionary:
  - [X] Add entry for SUMMARIZE with full metadata
  - [X] Add entry for SENTIMENT with full metadata
  - [X] Add entry for KEY_POINTS with full metadata
  - [X] Add entry for QUESTIONS with full metadata
  - [X] Add entry for QA with full metadata
  - [ ] Add scaffold entry for PROS_CONS (to be implemented in Phase 4)
- [X] Add registry accessor methods:
  - [X] `_get_operation_config(operation)`: Get config for operation
  - [X] `_get_handler_name(operation)`: Get handler method name
  - [X] `_get_resilience_strategy(operation)`: Get resilience strategy
  - [X] `_get_cache_ttl_from_registry(operation)`: Get cache TTL from registry
  - [X] `_get_fallback_type(operation)`: Get fallback data type
  - [X] `_get_response_field(operation)`: Get response field name

#### Task 3.2: Refactor Configuration Methods
- [X] Refactor `_register_operations()`:
  - [X] Update to use registry for strategy lookup
  - [X] Remove hardcoded operation name strings (replaced with registry-driven map)
  - [X] Simplify registration loop using registry
  - [X] Support settings overrides for custom strategy configuration
- [X] Refactor `_get_ttl_for_operation()`:
  - [X] Replace internal dictionary with registry lookup
  - [X] Add fallback for operations not in registry
  - [X] Update docstring to reference registry
  - [X] Maintain backward compatibility with existing TTLs

#### Task 3.3: Add Registry Validation
- [X] Implement registry consistency checks:
  - [X] Validate all enum operations have registry entries
  - [X] Verify handler method names correspond to actual methods
  - [X] Check resilience strategies are valid enum values
  - [X] Validate TTL values are positive integers
  - [X] Validate response fields match TextProcessingResponse model
- [X] Add initialization validation:
  - [X] Call validation during `__init__`
  - [X] Log success message when validation passes
  - [X] Raise ConfigurationError for critical misconfigurations
  - [ ] Create unit tests for validation logic (deferred to Phase 5)

---

## Phase 3: Dispatch Refactoring

### Deliverable 4: Improved Operation Dispatch
**Goal**: Replace `if/elif` chains with maintainable dispatch mechanism.

#### Task 4.1: Implement Dispatch Helper Methods
- [X] Create `_dispatch_operation()` method:
  ```python
  async def _dispatch_operation(
      self,
      request: TextProcessingRequest,
      sanitized_text: str,
      sanitized_options: Dict[str, Any],
      sanitized_question: Optional[str]
  ) -> Any:
      """Central dispatch for operation execution."""
  ```
  - [X] Implement handler lookup from registry
  - [X] Add operation validation
  - [X] Implement handler invocation with proper arguments
  - [X] Add comprehensive error handling
- [X] Create `_prepare_handler_arguments()` method:
  - [X] Build argument dict based on operation requirements
  - [X] Include text for all operations
  - [X] Add options for operations that need them
  - [X] Include question only for QA operation
  - [X] Handle future operation-specific parameters

#### Task 4.2: Refactor `process_text()` Method
- [X] Replace `if/elif` chain (lines 439-450):
  - [X] Remove existing conditional blocks
  - [X] Add single call to `_dispatch_operation()`
  - [X] Update response field assignment logic
  - [X] Preserve all existing error handling
- [X] Simplify response field routing:
  - [X] Create helper to route result to correct response field (`_set_response_field()`)
  - [X] Use registry metadata for field selection
  - [X] Handle special cases (sentiment, key_points, questions)
  - [X] Maintain backward compatibility

#### Task 4.3: Refactor Fallback Handling
- [X] Update `_get_fallback_response()` method:
  - [X] Use registry to determine fallback type
  - [X] Simplify fallback selection logic
  - [X] Maintain existing fallback values
  - [X] Improve fallback logging with operation metadata
- [X] Update exception handling in `process_text()`:
  - [X] Use registry for response field routing in fallback case
  - [X] Consolidate duplicated fallback logic
  - [X] Ensure consistent metadata setting
  - [X] Preserve existing fallback behavior

---

### Deliverable 5: Code Quality and Testing
**Goal**: Ensure refactored dispatch maintains behavior and quality.

#### Task 5.1: Unit Test Updates
- [ ] Update existing tests for dispatch refactoring:
  - [ ] Verify all operation tests still pass
  - [ ] Update tests that mock internal methods
  - [ ] Add tests for new dispatch helper methods
  - [ ] Test registry lookup logic
- [ ] Add tests for edge cases:
  - [ ] Test unknown operation handling
  - [ ] Test missing registry entry handling
  - [ ] Test handler method not found errors
  - [ ] Test argument preparation for all operation types

#### Task 5.2: Integration Testing
- [ ] Run comprehensive integration tests:
  - [ ] Execute all text processing integration tests
  - [ ] Test batch processing with multiple operation types
  - [ ] Verify caching behavior unchanged
  - [ ] Test resilience patterns still apply correctly
- [ ] Manual validation testing:
  - [ ] Test each operation via API endpoints
  - [ ] Verify response structure unchanged
  - [ ] Check processing times comparable
  - [ ] Test error responses match expectations

---

## Phase 4: Multi-Step Pattern Implementation

### Deliverable 6: Multi-Step Operation Framework
**Goal**: Establish pattern for complex multi-step operations like PROS_CONS.

#### Task 6.1: Add PROS_CONS to Shared Models
- [ ] Update `shared/shared/text_processing.py`:
  - [ ] Add `PROS_CONS = "pros_cons"` to `TextProcessingOperation` enum
  - [ ] Create `ProsConsResult` model with pros/cons/synthesis fields
  - [ ] Add `pros_cons: Optional[ProsConsResult] = None` to `TextProcessingResponse`
  - [ ] Add validation if needed for pros_cons options
- [ ] Update `backend/app/schemas.py`:
  - [ ] Import new models from shared
  - [ ] Update type exports if needed
  - [ ] Verify FastAPI integration works

#### Task 6.2: Implement PROS_CONS Core Methods
- [ ] Create resilience wrapper method:
  ```python
  @with_balanced_resilience("pros_cons_analysis")
  async def _pros_cons_with_resilience(
      self, text: str, options: Dict[str, Any]
  ) -> Dict[str, Any]:
      """Generate pros/cons analysis with resilience patterns."""
      return await self._generate_pros_cons(text, options)
  ```
- [ ] Implement main orchestration method:
  ```python
  async def _generate_pros_cons(
      self, text: str, options: Dict[str, Any]
  ) -> Dict[str, Any]:
      """Multi-step pros/cons generation with parallel execution."""
      # Step 1 & 2: Parallel pros and cons
      # Step 3: Synthesis
      # Return structured result
  ```
- [ ] Implement sub-task methods:
  - [ ] `_get_pros(text: str) -> List[str]`: Extract pro arguments
  - [ ] `_get_cons(text: str) -> List[str]`: Extract con arguments
  - [ ] `_synthesize_pros_cons(text: str, pros: List[str], cons: List[str]) -> str`: Create synthesis

#### Task 6.3: Add PROS_CONS to Registry and Dispatch
- [ ] Update operation registry:
  - [ ] Add PROS_CONS entry with handler, strategy, TTL, etc.
  - [ ] Set appropriate resilience strategy (balanced recommended)
  - [ ] Configure cache TTL (moderate: 3600 seconds / 1 hour)
  - [ ] Set response field to "pros_cons"
- [ ] Update dispatch logic:
  - [ ] Ensure dispatcher handles pros_cons response field
  - [ ] Add fallback handling for PROS_CONS
  - [ ] Update `_register_operations()` to include pros_cons
  - [ ] Add PROS_CONS to operation validation

#### Task 6.4: Implement PROS_CONS Prompt Engineering
- [ ] Create prompt templates in `backend/app/infrastructure/ai/prompt_templates.py`:
  - [ ] Add "pros" template: "You strongly support this idea. List 3-5 compelling arguments in favor..."
  - [ ] Add "cons" template: "You strongly oppose this idea. List 3-5 compelling arguments against..."
  - [ ] Add "pros_cons_synthesis" template: "Synthesize the following perspectives into balanced analysis..."
- [ ] Update prompt building:
  - [ ] Use `create_safe_prompt()` for all three calls
  - [ ] Ensure proper sanitization of user input
  - [ ] Include options in prompts (e.g., num_points)
  - [ ] Add validation of prompt outputs

---

### Deliverable 7: PROS_CONS Error Handling and Fallbacks
**Goal**: Ensure robust error handling for multi-step operation.

#### Task 7.1: Partial Failure Handling
- [ ] Implement graceful degradation:
  - [ ] If pros call fails but cons succeeds, return partial result
  - [ ] If both pros/cons fail, use fallback message
  - [ ] If synthesis fails, return pros/cons without synthesis
  - [ ] Log appropriate warnings for partial failures
- [ ] Update fallback response:
  - [ ] Add PROS_CONS to `_get_fallback_response()`
  - [ ] Create appropriate fallback structure
  - [ ] Include service status in metadata
  - [ ] Test fallback triggers correctly

#### Task 7.2: Caching Strategy
- [ ] Implement intelligent caching:
  - [ ] Cache final composite result (pros + cons + synthesis)
  - [ ] Consider caching intermediate results (optional optimization)
  - [ ] Use appropriate TTL from registry (1 hour)
  - [ ] Ensure cache key includes all relevant parameters
- [ ] Test cache behavior:
  - [ ] Verify cache hit returns full structured result
  - [ ] Test cache miss triggers full execution
  - [ ] Validate cache key generation is consistent
  - [ ] Test TTL expiration behavior

---

## Phase 5: Testing Infrastructure

### Deliverable 8: Comprehensive Test Coverage
**Goal**: Ensure refactored service and PROS_CONS operation are thoroughly tested.

#### Task 8.1: Unit Tests for Registry and Dispatch
- [ ] Create/update tests in `backend/tests/unit/services/test_text_processor.py`:
  - [ ] Test operation registry structure and validation
  - [ ] Test `_get_operation_config()` for all operations
  - [ ] Test `_dispatch_operation()` routing logic
  - [ ] Test handler argument preparation
  - [ ] Test response field routing
- [ ] Test error conditions:
  - [ ] Unknown operation handling
  - [ ] Missing registry entry
  - [ ] Handler method not found
  - [ ] Invalid arguments to handler

#### Task 8.2: Unit Tests for PROS_CONS
- [ ] Test PROS_CONS operation methods:
  - [ ] Test `_get_pros()` with mocked AI agent
  - [ ] Test `_get_cons()` with mocked AI agent
  - [ ] Test `_synthesize_pros_cons()` with mocked AI agent
  - [ ] Test `_generate_pros_cons()` orchestration
  - [ ] Test parallel execution with asyncio
- [ ] Test error scenarios:
  - [ ] Pros call failure
  - [ ] Cons call failure
  - [ ] Both pros/cons failures
  - [ ] Synthesis call failure
  - [ ] Partial failure handling

#### Task 8.3: Integration Tests
- [ ] Create integration tests for PROS_CONS:
  - [ ] Test full PROS_CONS workflow with real AI calls (or realistic mocks)
  - [ ] Test caching behavior for PROS_CONS
  - [ ] Test resilience patterns apply correctly
  - [ ] Test batch processing with PROS_CONS operations
- [ ] Test API endpoints:
  - [ ] Create/update API tests for PROS_CONS endpoint
  - [ ] Test request validation
  - [ ] Test response structure
  - [ ] Test error responses

#### Task 8.4: Test Isolation Improvements
- [ ] Improve test fixtures:
  - [ ] Create fixtures for mocked operation handlers
  - [ ] Add fixtures for registry testing
  - [ ] Create helpers for testing multi-step operations
  - [ ] Document test patterns for future operations
- [ ] Improve test organization:
  - [ ] Group tests by operation type
  - [ ] Separate unit vs integration tests clearly
  - [ ] Add test markers for slow/fast tests
  - [ ] Document testing best practices

---

## Phase 6: Documentation & Validation

### Deliverable 9: Contract and Documentation Updates
**Goal**: Update all contracts, docstrings, and documentation to reflect changes.

#### Task 9.1: Contract File Updates
- [ ] Update `backend/contracts/services/text_processor.pyi`:
  - [ ] Add type hints for new helper methods (`_dispatch_operation`, etc.)
  - [ ] Add PROS_CONS method signatures
  - [ ] Update module docstring to mention PROS_CONS
  - [ ] Add registry type hints and structure
  - [ ] Update class docstring with new operation
- [ ] Verify contract completeness:
  - [ ] All public methods have signatures
  - [ ] All new operations documented
  - [ ] Type hints match implementation
  - [ ] Examples include PROS_CONS usage

#### Task 9.2: Docstring Updates
- [ ] Update method docstrings:
  - [ ] Add comprehensive docstring for `_dispatch_operation()`
  - [ ] Document operation registry structure and usage
  - [ ] Add docstrings for all PROS_CONS methods
  - [ ] Update `process_text()` docstring with new dispatch logic
- [ ] Update class docstring:
  - [ ] Add PROS_CONS to supported operations list (line 26)
  - [ ] Update architecture description if needed
  - [ ] Add example usage for PROS_CONS
  - [ ] Document multi-step operation pattern

#### Task 9.3: Developer Documentation
- [ ] Update `backend/README.md`:
  - [ ] Add PROS_CONS to operation descriptions
  - [ ] Document multi-step operation pattern
  - [ ] Update examples if needed
  - [ ] Note any breaking changes (should be none)
- [ ] Update relevant guides:
  - [ ] Update `docs/guides/infrastructure/AI_SERVICE.md` if needed
  - [ ] Document PROS_CONS in API documentation
  - [ ] Add examples to integration guide
  - [ ] Update troubleshooting if needed

---

### Deliverable 10: Final Validation and Rollout
**Goal**: Comprehensive validation before deployment.

#### Task 10.1: Comprehensive Test Execution
- [ ] Run full test suite:
  - [ ] Execute `make test-backend` from project root
  - [ ] Verify all unit tests pass
  - [ ] Verify all integration tests pass
  - [ ] Verify end-to-end tests pass
  - [ ] Check test coverage for new code (aim for >80%)
- [ ] Run type checking:
  - [ ] Execute mypy on backend codebase
  - [ ] Fix any type errors introduced
  - [ ] Verify contracts match implementation
  - [ ] Check for any type safety regressions

#### Task 10.2: Performance Validation
- [ ] Benchmark operation performance:
  - [ ] Test existing operations have comparable performance
  - [ ] Benchmark PROS_CONS processing time
  - [ ] Verify dispatch overhead is negligible
  - [ ] Test cache performance unchanged
- [ ] Load testing (optional):
  - [ ] Test concurrent operation processing
  - [ ] Test batch processing with mixed operations
  - [ ] Verify resilience patterns under load
  - [ ] Monitor resource usage

#### Task 10.3: API Validation
- [ ] Test API endpoints:
  - [ ] Test all existing operations via API
  - [ ] Test new PROS_CONS endpoint
  - [ ] Verify OpenAPI schema updated
  - [ ] Test error responses
- [ ] Frontend integration:
  - [ ] Coordinate with frontend team for PROS_CONS UI
  - [ ] Test request/response flow
  - [ ] Verify error handling in UI
  - [ ] Document frontend integration points

#### Task 10.4: Code Quality Checks
- [ ] Run linting:
  - [ ] Execute `make lint-backend`
  - [ ] Fix any new linting issues
  - [ ] Ensure code formatting consistent
  - [ ] Verify no unused imports
- [ ] Code review preparation:
  - [ ] Create detailed PR description
  - [ ] Document design decisions
  - [ ] Highlight breaking changes (should be none)
  - [ ] Prepare demo of PROS_CONS functionality

---

## Implementation Notes

### Phase Execution Strategy

**PHASE 1: Analysis & Design (Day 1)**
- **Deliverable 1**: Current implementation analysis
- **Deliverable 2**: Refactoring design document
- **Success Criteria**: Complete understanding of current patterns, clear design for improvements

**PHASE 2: Operation Metadata Centralization (Day 2)**
- **Deliverable 3**: Operation registry implementation
- **Success Criteria**: All operation metadata centralized, registry validated, tests passing

**PHASE 3: Dispatch Refactoring (Days 3-4)**
- **Deliverable 4**: Improved operation dispatch
- **Deliverable 5**: Code quality and testing
- **Success Criteria**: `if/elif` chains replaced with dispatch table, all tests passing, no behavior changes

**PHASE 4: Multi-Step Pattern Implementation (Day 5)**
- **Deliverable 6**: Multi-step operation framework
- **Deliverable 7**: PROS_CONS error handling and fallbacks
- **Success Criteria**: PROS_CONS fully implemented and tested, robust error handling

**PHASE 5: Testing Infrastructure (Day 6)**
- **Deliverable 8**: Comprehensive test coverage
- **Success Criteria**: >80% test coverage for new code, all tests passing, improved test isolation

**PHASE 6: Documentation & Validation (Day 7)**
- **Deliverable 9**: Contract and documentation updates
- **Deliverable 10**: Final validation and rollout
- **Success Criteria**: Documentation complete, all validation passing, ready for deployment

### Risk Mitigation Strategies

**Low Risk Areas:**
- Adding operation registry (additive change)
- Adding new PROS_CONS operation (new feature)
- Documentation updates (no functional impact)

**Medium Risk Areas:**
- Refactoring dispatch mechanism (core processing logic)
- Modifying `process_text()` method (critical path)
- Multi-step operation pattern (new complexity)

**Mitigation Approaches:**
- Comprehensive unit and integration tests at each phase
- Preserve 100% backward compatibility with existing operations
- Incremental changes with validation after each deliverable
- Maintain existing resilience and caching behavior
- Clear rollback plan (keep Git history clean)
- Feature flag for PROS_CONS if needed for gradual rollout

### Success Metrics

**Quantitative Metrics:**
- Code maintainability: Reduce operation dispatch from 12 lines to ~5 lines
- Test coverage: Achieve >80% coverage for refactored code
- Performance: No degradation in operation processing time
- Lines of code: Net increase of 200-300 lines (adding PROS_CONS, registry, helpers)

**Qualitative Metrics:**
- Improved code readability and discoverability
- Clearer pattern for adding new operations
- Better test isolation for individual operations
- Documented multi-step operation pattern
- Enhanced developer experience

### Validation Checkpoints

**After Phase 2:**
- Registry structure complete and validated
- All existing tests still passing
- No behavior changes

**After Phase 3:**
- Dispatch refactoring complete
- All operations work through new dispatch
- Performance unchanged

**After Phase 4:**
- PROS_CONS fully functional
- Multi-step pattern documented
- Error handling robust

**Final Validation:**
- Complete test suite passing
- Performance benchmarks met
- Documentation complete
- API validation successful
- Ready for production deployment

### Long-term Benefits

**Immediate Benefits:**
- Cleaner operation dispatch mechanism
- Clear pattern for multi-step operations
- PROS_CONS feature ready for use
- Improved testability

**Long-term Benefits:**
- Easier to add new operations (clearer extension points)
- Better maintainability (less code duplication)
- Scalable architecture for future complexity
- Strong foundation for additional multi-step operations
- Reduced cognitive load for developers

### Extension Points for Future Operations

**Adding Simple Operations (like current 5):**
1. Add enum value to `TextProcessingOperation`
2. Add entry to `OPERATION_CONFIG` registry
3. Implement `_operation_with_resilience()` and `_operation()` methods
4. Add prompt template if needed
5. Update tests

**Adding Multi-Step Operations (like PROS_CONS):**
1. Add enum value to `TextProcessingOperation`
2. Add result model to shared models
3. Add entry to `OPERATION_CONFIG` registry
4. Implement orchestration method with sub-tasks
5. Add prompt templates for each step
6. Implement partial failure handling
7. Update tests for multi-step execution

### Design Principles Maintained

**Throughout Refactoring:**
- Single Responsibility Principle: Service orchestrates, operations implement
- Open/Closed Principle: Easy to extend operations without modifying core logic
- DRY Principle: Extract common patterns (dispatch, registry lookup)
- YAGNI Principle: Don't add full Strategy Pattern when registry suffices
- Backward Compatibility: Zero breaking changes to existing API

### Post-Refactoring Maintenance

**Operation Management:**
- Document process for adding new operations in `backend/README.md`
- Create checklist for operation addition
- Maintain registry consistency
- Review operation performance periodically

**Code Quality:**
- Regular complexity reviews
- Monitor test coverage trends
- Refactor when patterns emerge
- Update documentation with learnings

### Sample PROS_CONS Ideas for Testing

**Silly Test Cases:**
1. "Wearing socks with sandals should be socially acceptable"
2. "Pineapple belongs on pizza"
3. "Cats should be required to wear tiny business suits"
4. "Breakfast cereal is the perfect dinner food"

**Semi-Serious Test Cases:**
1. "Remote work should be the default for all knowledge workers"
2. "API-first development is better than UI-first development"
3. "Every city should ban cars from downtown areas"
4. "Universal Basic Income should replace traditional welfare"
5. "All software should be open source by default"

---

## Reference: Original Discussion Context

### Original Issue: PROS_CONS Feature Request
**Source**: `dev/issues/2025-08-06_pros-cons-text-processor.md`

**Proposed Feature**: Add pros/cons analysis operation leveraging batch functionality
- Three LLM calls: pro arguments, con arguments, synthesis
- Demonstrates sophisticated AI workflows
- Shows value of parallel processing
- Creates compelling demo feature

**Technical Considerations**:
- Dependency handling between calls
- Partial result management if calls fail
- Result formatting for structured output
- Prompt engineering for distinct perspectives

### Design Discussion: Strategy Pattern vs Targeted Refactoring

**Strategy Pattern Proposal (Rejected)**:
- Create `ProcessingStrategy` protocol for all operations
- Implement separate strategy classes per operation
- Create strategy registry for operation lookup
- Benefits: Strong separation, easy to test strategies in isolation
- Drawbacks: Adds 6-7 files, indirection layer, premature optimization for 6 operations

**Targeted Refactoring Approach (Adopted)**:
- Keep service-based architecture
- Add operation registry for metadata
- Implement dispatch table for routing
- Extract multi-step patterns as needed
- Benefits: Maintains clarity, appropriate for scale, easier migration
- Rationale: Current architecture is sound, needs refinement not rewrite

**Key Insight**: Strategy Pattern is valuable at 15-20+ operations with varying lifecycles. At 6 operations, targeted improvements provide better ROI.

---

## Conclusion

This task plan provides a systematic approach to refactoring the `TextProcessorService` to improve maintainability, enhance testability, and add support for the sophisticated PROS_CONS multi-step operation. By following this phased approach, we can make targeted improvements while maintaining the service's existing strengths and preserving 100% backward compatibility.

The refactoring represents a thoughtful balance between adding necessary structure for future growth and avoiding premature over-engineering. The result will be a more maintainable service with clear patterns for extension, ready to support increasingly sophisticated AI workflows while remaining approachable for developers.
