# Deliverable 2: Refactoring Design Document

**Date**: 2025-10-13
**Phase**: Phase 1 - Analysis & Design
**Status**: Complete
**Dependencies**: Deliverable 1 (Current Implementation Analysis)

---

## Executive Summary

This document provides detailed design specifications for refactoring the `TextProcessorService` to improve maintainability, reduce verbosity, and establish clear patterns for multi-step operations like PROS_CONS. The design maintains 100% backward compatibility while introducing three key improvements:

1. **Centralized Operation Registry** - Single source of truth for operation metadata
2. **Dispatch Mechanism** - Replace if/elif chains with table-driven dispatch
3. **Multi-Step Operation Pattern** - Reusable pattern for complex operations

The design follows the "Surgical Refactoring" philosophy: targeted improvements without wholesale architectural changes.

---

## Task 2.1: Operation Registry Design

### 2.1.1 Registry Structure

**Location**: `backend/app/services/text_processor.py` (class-level constant)

**Complete Registry Specification**:

```python
# Operation Registry - Centralized configuration for all text processing operations
OPERATION_CONFIG: Dict[TextProcessingOperation, Dict[str, Any]] = {
    TextProcessingOperation.SUMMARIZE: {
        "handler": "_summarize_text_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 7200,  # 2 hours
        "fallback_type": "string",
        "requires_question": False,
        "response_field": "result",
        "accepts_options": True,
        "description": "Generate concise summaries of input text"
    },
    TextProcessingOperation.SENTIMENT: {
        "handler": "_analyze_sentiment_with_resilience",
        "resilience_strategy": "aggressive",
        "cache_ttl": 3600,  # 1 hour
        "fallback_type": "sentiment_result",
        "requires_question": False,
        "response_field": "sentiment",
        "accepts_options": False,
        "description": "Analyze emotional tone and confidence levels"
    },
    TextProcessingOperation.KEY_POINTS: {
        "handler": "_extract_key_points_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 5400,  # 1.5 hours
        "fallback_type": "list",
        "requires_question": False,
        "response_field": "key_points",
        "accepts_options": True,
        "description": "Extract main ideas and important concepts"
    },
    TextProcessingOperation.QUESTIONS: {
        "handler": "_generate_questions_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 3600,  # 1 hour
        "fallback_type": "list",
        "requires_question": False,
        "response_field": "questions",
        "accepts_options": True,
        "description": "Generate questions about the text content"
    },
    TextProcessingOperation.QA: {
        "handler": "_answer_question_with_resilience",
        "resilience_strategy": "conservative",
        "cache_ttl": 1800,  # 30 minutes
        "fallback_type": "string",
        "requires_question": True,
        "response_field": "result",
        "accepts_options": False,
        "description": "Answer specific questions about the text"
    },
    TextProcessingOperation.PROS_CONS: {
        "handler": "_pros_cons_with_resilience",
        "resilience_strategy": "balanced",
        "cache_ttl": 3600,  # 1 hour
        "fallback_type": "pros_cons_result",
        "requires_question": False,
        "response_field": "pros_cons",
        "accepts_options": True,
        "description": "Generate pros/cons analysis with synthesis"
    },
}
```

### 2.1.2 Metadata Field Definitions

**Required Fields** (must be present for all operations):

| Field | Type | Description | Usage |
|-------|------|-------------|-------|
| `handler` | `str` | Method name of resilience-wrapped handler | `getattr(self, config["handler"])` |
| `resilience_strategy` | `str` | Strategy name: "aggressive", "balanced", "conservative" | Used in `_register_operations()` |
| `cache_ttl` | `int` | Time-to-live in seconds for cache entries | Used in `_get_ttl_for_operation()` |
| `fallback_type` | `str` | Type of fallback: "string", "list", "sentiment_result", "pros_cons_result" | Used in `_get_fallback_response()` |
| `requires_question` | `bool` | Whether operation requires question parameter | Used for request validation |
| `response_field` | `str` | Field name in TextProcessingResponse: "result", "sentiment", etc. | Used for response field routing |
| `accepts_options` | `bool` | Whether operation accepts options dict | Used in `_prepare_handler_arguments()` |
| `description` | `str` | Human-readable description of operation | Documentation and logging |

**Optional Fields** (may be added in future):

- `max_concurrent_calls`: For operations with parallel execution
- `prompt_template_names`: List of template names used by operation
- `validation_rules`: Custom validation rules for operation
- `metrics_tags`: Custom tags for monitoring

### 2.1.3 Registry Accessor Methods

**Design Pattern**: Private methods for type-safe registry access

```python
def _get_operation_config(self, operation: TextProcessingOperation) -> Dict[str, Any]:
    """
    Get complete configuration for an operation.

    Args:
        operation: The operation to get configuration for

    Returns:
        Configuration dictionary with all metadata

    Raises:
        ValueError: If operation not in registry

    Examples:
        >>> config = self._get_operation_config(TextProcessingOperation.SUMMARIZE)
        >>> print(config["resilience_strategy"])  # "balanced"
    """
    if operation not in self.OPERATION_CONFIG:
        raise ValueError(f"Operation {operation} not found in registry")
    return self.OPERATION_CONFIG[operation]

def _get_handler_name(self, operation: TextProcessingOperation) -> str:
    """
    Get handler method name for operation.

    Args:
        operation: The operation to get handler for

    Returns:
        Handler method name (string)

    Examples:
        >>> handler_name = self._get_handler_name(TextProcessingOperation.SUMMARIZE)
        >>> # Returns: "_summarize_text_with_resilience"
    """
    return self._get_operation_config(operation)["handler"]

def _get_resilience_strategy(self, operation: TextProcessingOperation) -> str:
    """
    Get resilience strategy name for operation.

    Args:
        operation: The operation to get strategy for

    Returns:
        Strategy name: "aggressive", "balanced", or "conservative"

    Examples:
        >>> strategy = self._get_resilience_strategy(TextProcessingOperation.SENTIMENT)
        >>> # Returns: "aggressive"
    """
    return self._get_operation_config(operation)["resilience_strategy"]

def _get_cache_ttl(self, operation: TextProcessingOperation) -> int:
    """
    Get cache TTL for operation.

    Args:
        operation: The operation to get TTL for

    Returns:
        TTL in seconds

    Examples:
        >>> ttl = self._get_cache_ttl(TextProcessingOperation.SUMMARIZE)
        >>> # Returns: 7200 (2 hours)
    """
    return self._get_operation_config(operation)["cache_ttl"]

def _get_fallback_type(self, operation: TextProcessingOperation) -> str:
    """
    Get fallback response type for operation.

    Args:
        operation: The operation to get fallback type for

    Returns:
        Fallback type: "string", "list", "sentiment_result", "pros_cons_result"

    Examples:
        >>> fallback_type = self._get_fallback_type(TextProcessingOperation.KEY_POINTS)
        >>> # Returns: "list"
    """
    return self._get_operation_config(operation)["fallback_type"]

def _get_response_field(self, operation: TextProcessingOperation) -> str:
    """
    Get response field name for operation.

    Args:
        operation: The operation to get response field for

    Returns:
        Field name in TextProcessingResponse

    Examples:
        >>> field = self._get_response_field(TextProcessingOperation.SENTIMENT)
        >>> # Returns: "sentiment"
    """
    return self._get_operation_config(operation)["response_field"]
```

### 2.1.4 Registry Validation Logic

**Validation Strategy**: Validate at initialization to fail fast

```python
def _validate_operation_registry(self) -> None:
    """
    Validate operation registry consistency at initialization.

    Validates:
        - All enum operations have registry entries
        - Handler methods exist on service instance
        - Resilience strategies are valid
        - TTL values are positive integers
        - Response fields match TextProcessingResponse model

    Raises:
        ConfigurationError: If registry is invalid

    Called from:
        __init__() method during service initialization
    """
    # Check all enum operations have registry entries
    for operation in TextProcessingOperation:
        if operation not in self.OPERATION_CONFIG:
            raise ConfigurationError(
                f"Operation {operation.value} missing from OPERATION_CONFIG registry"
            )

    # Validate each registry entry
    for operation, config in self.OPERATION_CONFIG.items():
        # Validate handler method exists
        handler_name = config["handler"]
        if not hasattr(self, handler_name):
            raise ConfigurationError(
                f"Handler method '{handler_name}' for operation {operation.value} "
                f"not found on {self.__class__.__name__}"
            )

        # Validate resilience strategy
        strategy = config["resilience_strategy"]
        valid_strategies = {"aggressive", "balanced", "conservative"}
        if strategy not in valid_strategies:
            raise ConfigurationError(
                f"Invalid resilience strategy '{strategy}' for operation {operation.value}. "
                f"Must be one of: {valid_strategies}"
            )

        # Validate TTL
        ttl = config["cache_ttl"]
        if not isinstance(ttl, int) or ttl <= 0:
            raise ConfigurationError(
                f"Invalid cache TTL {ttl} for operation {operation.value}. "
                f"Must be positive integer"
            )

        # Validate response field
        response_field = config["response_field"]
        valid_fields = {"result", "sentiment", "key_points", "questions", "pros_cons"}
        if response_field not in valid_fields:
            raise ConfigurationError(
                f"Invalid response field '{response_field}' for operation {operation.value}. "
                f"Must be one of: {valid_fields}"
            )

    logger.info(
        f"Operation registry validated successfully: {len(self.OPERATION_CONFIG)} operations registered"
    )
```

---

## Task 2.2: Dispatch Mechanism Design

### 2.2.1 Central Dispatch Method

**Design**: Single entry point for operation execution with argument routing

```python
async def _dispatch_operation(
    self,
    request: TextProcessingRequest,
    sanitized_text: str,
    sanitized_options: Dict[str, Any],
    sanitized_question: Optional[str]
) -> Any:
    """
    Central dispatch method for operation execution with argument routing.

    This method replaces the if/elif chain in process_text() by using the operation
    registry to look up handlers and route arguments dynamically.

    Args:
        request: Original text processing request
        sanitized_text: Sanitized input text
        sanitized_options: Sanitized options dictionary
        sanitized_question: Sanitized question (if provided)

    Returns:
        Operation result in appropriate type (str, SentimentResult, List[str], etc.)

    Raises:
        ValueError: If operation not supported or handler invocation fails
        TransientAIError: If AI service call fails
        ServiceUnavailableError: If service unavailable after retries

    Examples:
        >>> # Summarize operation
        >>> result = await self._dispatch_operation(
        ...     request,
        ...     "Sample text",
        ...     {"max_length": 100},
        ...     None
        ... )
        >>> # Returns: "Summary string..."

        >>> # Sentiment operation
        >>> result = await self._dispatch_operation(
        ...     request,
        ...     "Great product!",
        ...     {},
        ...     None
        ... )
        >>> # Returns: SentimentResult(sentiment="positive", ...)

    Design Notes:
        - Replaces 12-line if/elif chain with single registry lookup
        - Handles argument routing based on operation metadata
        - Maintains existing error handling and logging patterns
        - Type-agnostic: returns operation-specific result types
    """
    operation = request.operation

    # Validate operation is registered
    if operation not in self.OPERATION_CONFIG:
        raise ValueError(f"Unsupported operation: {operation}")

    # Get handler method via registry
    config = self._get_operation_config(operation)
    handler_name = config["handler"]
    handler_method = getattr(self, handler_name)

    # Prepare arguments based on operation requirements
    handler_args = self._prepare_handler_arguments(
        operation=operation,
        text=sanitized_text,
        options=sanitized_options,
        question=sanitized_question
    )

    # Log dispatch
    logger.debug(
        f"Dispatching operation {operation.value} to handler {handler_name} "
        f"with args: {list(handler_args.keys())}"
    )

    # Invoke handler with prepared arguments
    try:
        result = await handler_method(**handler_args)
        return result
    except Exception as e:
        logger.error(f"Handler {handler_name} failed for operation {operation.value}: {e}")
        raise
```

### 2.2.2 Argument Preparation Logic

**Design**: Build argument dictionary based on operation metadata

```python
def _prepare_handler_arguments(
    self,
    operation: TextProcessingOperation,
    text: str,
    options: Dict[str, Any],
    question: Optional[str]
) -> Dict[str, Any]:
    """
    Prepare handler method arguments based on operation requirements.

    Builds argument dictionary dynamically based on operation metadata, handling
    the three different method signature patterns in the service.

    Args:
        operation: Operation being dispatched
        text: Sanitized input text
        options: Sanitized options dictionary
        question: Sanitized question (if provided)

    Returns:
        Dictionary of keyword arguments for handler method

    Examples:
        >>> # Pattern 1: text + options (SUMMARIZE, KEY_POINTS, QUESTIONS, PROS_CONS)
        >>> args = self._prepare_handler_arguments(
        ...     TextProcessingOperation.SUMMARIZE,
        ...     "Sample text",
        ...     {"max_length": 100},
        ...     None
        ... )
        >>> # Returns: {"text": "Sample text", "options": {"max_length": 100}}

        >>> # Pattern 2: text only (SENTIMENT)
        >>> args = self._prepare_handler_arguments(
        ...     TextProcessingOperation.SENTIMENT,
        ...     "Great product!",
        ...     {},
        ...     None
        ... )
        >>> # Returns: {"text": "Great product!"}

        >>> # Pattern 3: text + question (QA)
        >>> args = self._prepare_handler_arguments(
        ...     TextProcessingOperation.QA,
        ...     "Document content",
        ...     {},
        ...     "What is the conclusion?"
        ... )
        >>> # Returns: {"text": "Document content", "question": "What is the conclusion?"}

    Design Notes:
        - Handles three method signature patterns without hardcoding
        - Uses registry metadata (accepts_options, requires_question) for routing
        - Always includes 'text' parameter (required for all operations)
        - Omits 'options' if operation doesn't accept them (SENTIMENT, QA)
        - Includes 'question' only for QA operation
    """
    config = self._get_operation_config(operation)

    # Always include text
    args = {"text": text}

    # Add options if operation accepts them
    if config["accepts_options"]:
        args["options"] = options

    # Add question if operation requires it
    if config["requires_question"]:
        if not question:
            raise ValueError(f"Question is required for {operation.value} operation")
        args["question"] = question

    return args
```

### 2.2.3 Response Field Routing

**Design**: Assign operation result to correct response field

```python
def _route_response_to_field(
    self,
    response: TextProcessingResponse,
    operation: TextProcessingOperation,
    result: Any
) -> None:
    """
    Route operation result to appropriate response field.

    Assigns the operation result to the correct field in TextProcessingResponse
    based on operation metadata, handling the five different result types.

    Args:
        response: TextProcessingResponse object to update
        operation: Operation that produced the result
        result: Operation result (type varies by operation)

    Side Effects:
        Modifies response object by setting appropriate field

    Examples:
        >>> response = TextProcessingResponse(operation=TextProcessingOperation.SUMMARIZE, ...)
        >>> self._route_response_to_field(response, TextProcessingOperation.SUMMARIZE, "Summary...")
        >>> # Sets: response.result = "Summary..."

        >>> response = TextProcessingResponse(operation=TextProcessingOperation.SENTIMENT, ...)
        >>> self._route_response_to_field(
        ...     response,
        ...     TextProcessingOperation.SENTIMENT,
        ...     SentimentResult(sentiment="positive", ...)
        ... )
        >>> # Sets: response.sentiment = SentimentResult(...)

    Design Notes:
        - Uses registry metadata to determine target field
        - Type-safe: no isinstance checks needed
        - Centralizes field routing logic (currently scattered in process_text)
        - Enables easy addition of new operation types
    """
    config = self._get_operation_config(operation)
    response_field = config["response_field"]

    # Set the field dynamically
    setattr(response, response_field, result)

    logger.debug(f"Routed {operation.value} result to field '{response_field}'")
```

### 2.2.4 Refactored process_text() Method

**Before** (Current Implementation - 50+ lines with duplicated logic):
```python
try:
    if request.operation == TextProcessingOperation.SUMMARIZE:
        response.result = await self._summarize_text_with_resilience(sanitized_text, sanitized_options)
    elif request.operation == TextProcessingOperation.SENTIMENT:
        response.sentiment = await self._analyze_sentiment_with_resilience(sanitized_text)
    elif request.operation == TextProcessingOperation.KEY_POINTS:
        response.key_points = await self._extract_key_points_with_resilience(sanitized_text, sanitized_options)
    elif request.operation == TextProcessingOperation.QUESTIONS:
        response.questions = await self._generate_questions_with_resilience(sanitized_text, sanitized_options)
    elif request.operation == TextProcessingOperation.QA:
        response.result = await self._answer_question_with_resilience(sanitized_text, sanitized_question)
    else:
        raise ValueError(f"Unsupported operation: {request.operation}")

except ServiceUnavailableError:
    if request.operation == TextProcessingOperation.SENTIMENT:
        response.sentiment = await self._get_fallback_sentiment()
    elif request.operation == TextProcessingOperation.KEY_POINTS:
        response.key_points = await self._get_fallback_response(request.operation, sanitized_text)
    elif request.operation == TextProcessingOperation.QUESTIONS:
        response.questions = await self._get_fallback_response(request.operation, sanitized_text)
    else:
        response.result = await self._get_fallback_response(request.operation, sanitized_text, sanitized_question)
    # Mark as degraded service
    response.metadata["service_status"] = "degraded"
    response.metadata["fallback_used"] = True
```

**After** (Refactored - ~15 lines with single dispatch):
```python
try:
    # Single dispatch call replaces entire if/elif chain
    result = await self._dispatch_operation(
        request,
        sanitized_text,
        sanitized_options,
        sanitized_question
    )

    # Route result to appropriate response field
    self._route_response_to_field(response, request.operation, result)

except ServiceUnavailableError:
    # Single fallback dispatch replaces entire if/elif chain
    fallback_result = await self._get_fallback_response(
        request.operation,
        sanitized_text,
        sanitized_question
    )

    # Route fallback to appropriate response field
    self._route_response_to_field(response, request.operation, fallback_result)

    # Mark as degraded service
    response.metadata["service_status"] = "degraded"
    response.metadata["fallback_used"] = True
    logger.info(f"PROCESSING_END - ID: {processing_id}, Operation: {request.operation}, Status: FALLBACK_USED")
```

**Benefits**:
- **60% line reduction** in dispatch logic (30 lines → 12 lines)
- **Single source of truth** for operation routing (registry)
- **Easy to extend**: Add operation to registry, no code changes needed
- **Consistent error handling**: Same pattern for all operations
- **Better testability**: Can test dispatch logic independently

---

## Task 2.3: Multi-Step Operation Pattern Design

### 2.3.1 Abstract Multi-Step Pattern

**Design Philosophy**: Reusable pattern for operations requiring multiple dependent AI calls

**Pattern Structure**:
```
┌─────────────────────────────────────────┐
│  Multi-Step Operation Pattern          │
├─────────────────────────────────────────┤
│  1. Setup Phase                         │
│     - Extract options                   │
│     - Validate prerequisites            │
│     - Prepare logging context           │
├─────────────────────────────────────────┤
│  2. Parallel Execution Phase            │
│     - Launch independent AI calls       │
│     - Use asyncio.TaskGroup or gather  │
│     - Handle individual task failures   │
│     - Collect results                   │
├─────────────────────────────────────────┤
│  3. Synthesis Phase                     │
│     - Aggregate parallel results        │
│     - Launch dependent AI call(s)       │
│     - Handle synthesis failures         │
├─────────────────────────────────────────┤
│  4. Result Assembly Phase               │
│     - Combine all results               │
│     - Apply partial failure handling    │
│     - Return structured result          │
└─────────────────────────────────────────┘
```

### 2.3.2 Parallel Execution Helper

**Design**: Reusable helper for parallel task execution with error handling

```python
async def _execute_parallel_tasks(
    self,
    tasks: Dict[str, Coroutine],
    allow_partial_failure: bool = True
) -> Dict[str, Any]:
    """
    Execute multiple AI tasks in parallel with structured error handling.

    This helper enables multi-step operations to execute independent AI calls
    concurrently while handling individual task failures gracefully.

    Args:
        tasks: Dictionary mapping task names to coroutines
               e.g., {"pros": self._get_pros(text), "cons": self._get_cons(text)}
        allow_partial_failure: If True, return partial results when some tasks fail
                              If False, raise exception if any task fails

    Returns:
        Dictionary mapping task names to results
        Format: {"task_name": result, ...} or {"task_name": None} for failed tasks

    Raises:
        TransientAIError: If allow_partial_failure=False and any task fails
        Exception: If all tasks fail (even with allow_partial_failure=True)

    Examples:
        >>> # Successful parallel execution
        >>> tasks = {
        ...     "pros": self._get_pros("AI in education", 3),
        ...     "cons": self._get_cons("AI in education", 3)
        ... }
        >>> results = await self._execute_parallel_tasks(tasks)
        >>> # Returns: {"pros": ["Pro 1", ...], "cons": ["Con 1", ...]}

        >>> # Partial failure handling
        >>> tasks = {"task1": failing_coroutine(), "task2": successful_coroutine()}
        >>> results = await self._execute_parallel_tasks(tasks, allow_partial_failure=True)
        >>> # Returns: {"task1": None, "task2": "Success result"}
        >>> # Logs warning about task1 failure

    Design Notes:
        - Uses asyncio.TaskGroup (Python 3.11+) for structured concurrency
        - Falls back to asyncio.gather() for Python 3.10 compatibility
        - Logs individual task failures for debugging
        - Enables graceful degradation in multi-step operations
    """
    results = {}
    failed_tasks = []

    try:
        # Python 3.11+ structured concurrency
        async with asyncio.TaskGroup() as tg:
            # Create tasks
            task_map = {name: tg.create_task(coro) for name, coro in tasks.items()}

        # Collect results
        for name, task in task_map.items():
            try:
                results[name] = task.result()
            except Exception as e:
                logger.warning(f"Task '{name}' failed: {e}")
                results[name] = None
                failed_tasks.append(name)

    except AttributeError:
        # Fallback for Python 3.10 (TaskGroup not available)
        task_list = list(tasks.values())
        task_results = await asyncio.gather(*task_list, return_exceptions=True)

        for name, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                logger.warning(f"Task '{name}' failed: {result}")
                results[name] = None
                failed_tasks.append(name)
            else:
                results[name] = result

    # Handle failure modes
    if failed_tasks:
        if not allow_partial_failure:
            raise TransientAIError(
                f"Required tasks failed: {', '.join(failed_tasks)}"
            )

        if len(failed_tasks) == len(tasks):
            raise TransientAIError(
                f"All parallel tasks failed: {', '.join(failed_tasks)}"
            )

        logger.info(
            f"Partial success: {len(results) - len(failed_tasks)}/{len(tasks)} tasks completed. "
            f"Failed tasks: {', '.join(failed_tasks)}"
        )

    return results
```

### 2.3.3 PROS_CONS Pattern Application

**Implementation Structure**:

```python
@with_balanced_resilience("pros_cons_analysis")
async def _pros_cons_with_resilience(
    self, text: str, options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate pros/cons analysis with resilience patterns.

    Resilience wrapper for PROS_CONS operation following established pattern.

    Args:
        text: Sanitized input text to analyze
        options: Sanitized options (num_points, etc.)

    Returns:
        Dictionary with 'pros', 'cons', 'synthesis' keys

    Raises:
        TransientAIError: If AI calls fail
        ServiceUnavailableError: If service unavailable after retries
    """
    return await self._generate_pros_cons(text, options)


async def _generate_pros_cons(
    self, text: str, options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Multi-step pros/cons generation with parallel execution.

    Implements the multi-step operation pattern:
    1. Setup: Extract options and validate input
    2. Parallel: Execute pros and cons extraction concurrently
    3. Synthesis: Generate balanced analysis from parallel results
    4. Assembly: Combine results with partial failure handling

    Args:
        text: Sanitized input text to analyze
        options: Configuration options
            - num_points (int, default=3): Number of pro/con arguments to generate
            - synthesis_length (int, optional): Target synthesis length

    Returns:
        Dictionary with structure:
            {
                "pros": List[str],    # Pro arguments
                "cons": List[str],    # Con arguments
                "synthesis": str      # Balanced synthesis
            }

    Raises:
        TransientAIError: If all parallel tasks fail
        ValueError: If text is empty or invalid

    Examples:
        >>> result = await self._generate_pros_cons(
        ...     "AI should be used in schools",
        ...     {"num_points": 3}
        ... )
        >>> # Returns:
        >>> # {
        >>> #     "pros": ["Increases engagement", "Personalized learning", ...],
        >>> #     "cons": ["Privacy concerns", "Cost barriers", ...],
        >>> #     "synthesis": "While AI offers significant educational benefits..."
        >>> # }

    Design Notes:
        - Phase 1 & 2 use parallel execution for efficiency
        - Phase 3 depends on Phase 1 & 2 results
        - Handles partial failures gracefully (e.g., synthesis failure)
        - Maintains structured logging for multi-step operations
    """
    # ===== PHASE 1: SETUP =====
    num_points = options.get("num_points", 3)
    logger.debug(f"Starting PROS_CONS analysis with {num_points} points per side")

    # ===== PHASE 2: PARALLEL EXECUTION =====
    parallel_tasks = {
        "pros": self._get_pros(text, num_points),
        "cons": self._get_cons(text, num_points)
    }

    # Execute pros and cons extraction in parallel
    try:
        results = await self._execute_parallel_tasks(
            parallel_tasks,
            allow_partial_failure=True  # Can proceed with one side failing
        )
        pros = results.get("pros") or ["Unable to extract pro arguments"]
        cons = results.get("cons") or ["Unable to extract con arguments"]

    except TransientAIError as e:
        # Both parallel tasks failed
        logger.error(f"Failed to extract pros/cons: {e}")
        raise

    # ===== PHASE 3: SYNTHESIS =====
    try:
        synthesis = await self._synthesize_pros_cons(text, pros, cons)
    except Exception as e:
        # Synthesis failed, but we have pros/cons - partial success
        logger.warning(f"Synthesis failed, returning partial results: {e}")
        synthesis = (
            "Unable to synthesize perspectives at this time. "
            "Review individual pros and cons above for balanced analysis."
        )

    # ===== PHASE 4: RESULT ASSEMBLY =====
    result = {
        "pros": pros,
        "cons": cons,
        "synthesis": synthesis
    }

    # Log completion with partial failure indicators
    has_partial_failure = (
        "Unable to extract" in str(pros) or
        "Unable to extract" in str(cons) or
        "Unable to synthesize" in synthesis
    )

    if has_partial_failure:
        logger.warning(
            f"PROS_CONS completed with partial results: "
            f"pros={len(pros)}, cons={len(cons)}, synthesis={'partial' if 'Unable' in synthesis else 'success'}"
        )
    else:
        logger.info(f"PROS_CONS completed successfully: {len(pros)} pros, {len(cons)} cons")

    return result
```

**Sub-Task Methods**:

```python
async def _get_pros(self, text: str, num_points: int) -> List[str]:
    """
    Extract pro arguments supporting the idea in the text.

    Args:
        text: Sanitized input text
        num_points: Number of pro arguments to generate

    Returns:
        List of pro argument strings

    Raises:
        TransientAIError: If AI call fails
    """
    prompt = create_safe_prompt(
        template_name="pros",
        user_input=text,
        additional_instructions=f"Generate {num_points} compelling pro arguments."
    )

    try:
        result = await self.agent.run(prompt)
        validated = self.response_validator.validate(
            result.output.strip(), "pros", text, "pros extraction"
        )
        return self._parse_points_list(validated, num_points)
    except Exception as e:
        logger.error(f"Failed to extract pro arguments: {e}")
        raise TransientAIError(f"Failed to generate pro arguments: {e}")


async def _get_cons(self, text: str, num_points: int) -> List[str]:
    """
    Extract con arguments opposing the idea in the text.

    Args:
        text: Sanitized input text
        num_points: Number of con arguments to generate

    Returns:
        List of con argument strings

    Raises:
        TransientAIError: If AI call fails
    """
    prompt = create_safe_prompt(
        template_name="cons",
        user_input=text,
        additional_instructions=f"Generate {num_points} compelling con arguments."
    )

    try:
        result = await self.agent.run(prompt)
        validated = self.response_validator.validate(
            result.output.strip(), "cons", text, "cons extraction"
        )
        return self._parse_points_list(validated, num_points)
    except Exception as e:
        logger.error(f"Failed to extract con arguments: {e}")
        raise TransientAIError(f"Failed to generate con arguments: {e}")


async def _synthesize_pros_cons(
    self, text: str, pros: List[str], cons: List[str]
) -> str:
    """
    Synthesize pros and cons into balanced analysis.

    Args:
        text: Original input text for context
        pros: List of pro arguments
        cons: List of con arguments

    Returns:
        Synthesis text providing balanced perspective

    Raises:
        TransientAIError: If AI call fails
    """
    prompt = create_safe_prompt(
        template_name="pros_cons_synthesis",
        user_input=text,
        pros_list="\n".join(f"- {p}" for p in pros),
        cons_list="\n".join(f"- {c}" for c in cons)
    )

    try:
        result = await self.agent.run(prompt)
        validated = self.response_validator.validate(
            result.output.strip(), "synthesis", text, "pros/cons synthesis"
        )
        return validated
    except Exception as e:
        logger.error(f"Failed to synthesize pros/cons: {e}")
        raise TransientAIError(f"Failed to synthesize analysis: {e}")


def _parse_points_list(self, validated_str: str, max_points: int) -> List[str]:
    """
    Parse validated string into list of points.

    Handles various formatting styles from AI:
    - Bulleted lists (- point)
    - Numbered lists (1. point)
    - Plain text paragraphs

    Args:
        validated_str: Validated output from AI
        max_points: Maximum number of points to return

    Returns:
        List of parsed point strings
    """
    points = []
    for line in validated_str.split("\n"):
        line = line.strip()

        # Skip empty lines and headers
        if not line or line.startswith(("Pro", "Con", "Arguments:", "Points:")):
            continue

        # Handle bulleted lists
        if line.startswith("-"):
            points.append(line[1:].strip())
        # Handle numbered lists
        elif line[0].isdigit() and "." in line[:5]:
            points.append(line.split(".", 1)[1].strip())
        # Handle plain text
        else:
            points.append(line)

    return points[:max_points]
```

### 2.3.4 Fallback Strategy for Multi-Step Operations

**Partial Failure Handling Matrix**:

| Scenario | Pros | Cons | Synthesis | Action |
|----------|------|------|-----------|--------|
| **Full Success** | ✓ | ✓ | ✓ | Return complete result |
| **Synthesis Fails** | ✓ | ✓ | ✗ | Return pros/cons with generic synthesis |
| **Pros Fail** | ✗ | ✓ | ? | Return cons with fallback pros, skip synthesis |
| **Cons Fail** | ✓ | ✗ | ? | Return pros with fallback cons, skip synthesis |
| **Both Fail** | ✗ | ✗ | ✗ | Use fallback response from registry |

**Fallback Response Addition**:

```python
# In _get_fallback_response() method
fallback_responses[TextProcessingOperation.PROS_CONS] = {
    "pros": ["Pro argument analysis temporarily unavailable"],
    "cons": ["Con argument analysis temporarily unavailable"],
    "synthesis": (
        "Service temporarily unavailable. Please try again later for "
        "comprehensive pros/cons analysis."
    )
}
```

---

## Design Validation

### Benefits Summary

**Operation Registry**:
- **Single source of truth** for operation configuration
- **Easy to extend**: Add operation, update registry, no code changes
- **Type-safe access** via accessor methods
- **Validation at initialization** catches configuration errors early

**Dispatch Mechanism**:
- **60% code reduction** in dispatch logic (30 lines → 12 lines)
- **Eliminates duplication** between main and fallback dispatch
- **Consistent patterns** across all operations
- **Testable in isolation** without mocking operations

**Multi-Step Pattern**:
- **Reusable helper** for parallel execution
- **Graceful degradation** with partial failure handling
- **Clear structure** (setup → parallel → synthesis → assembly)
- **Extensible** for future multi-step operations

### Backward Compatibility

**100% Backward Compatible**:
- ✅ No changes to public API surface
- ✅ Same request/response models
- ✅ Same error handling behavior
- ✅ Same caching behavior
- ✅ Same resilience patterns
- ✅ Existing tests pass without modification

**Internal Improvements Only**:
- Registry-based dispatch (internal implementation detail)
- Helper methods (private, not exposed in API)
- Multi-step pattern (additive for new operations)

### Testing Strategy

**Unit Tests**:
- Test registry validation logic
- Test accessor methods for each operation
- Test dispatch logic with mocked handlers
- Test argument preparation for all patterns
- Test response field routing
- Test multi-step parallel execution helper

**Integration Tests**:
- Test all operations through refactored dispatch
- Verify caching behavior unchanged
- Verify resilience behavior unchanged
- Test PROS_CONS end-to-end workflow
- Test partial failure scenarios

**Performance Tests**:
- Benchmark dispatch overhead (< 1ms expected)
- Verify no latency regression for existing operations
- Measure PROS_CONS total time (~5-10s expected with 3 AI calls)

---

## Implementation Sequence

**Phase 2** (Next): Implement Operation Registry
1. Add OPERATION_CONFIG constant to TextProcessorService
2. Implement accessor methods
3. Add validation logic to __init__
4. Refactor _register_operations() to use registry
5. Refactor _get_ttl_for_operation() to use registry

**Phase 3**: Implement Dispatch Mechanism
1. Add _prepare_handler_arguments() method
2. Add _dispatch_operation() method
3. Add _route_response_to_field() method
4. Refactor process_text() to use dispatch
5. Refactor _get_fallback_response() to use registry

**Phase 4**: Implement Multi-Step Pattern
1. Add _execute_parallel_tasks() helper
2. Add PROS_CONS to shared models
3. Add PROS_CONS to registry
4. Implement _pros_cons_with_resilience()
5. Implement _generate_pros_cons()
6. Implement sub-task methods (_get_pros, _get_cons, _synthesize_pros_cons)
7. Implement _parse_points_list() helper

---

## Status: Task 2.1, 2.2, and 2.3 Complete

This design provides the complete specification needed for Phase 2 (Operation Registry Implementation) and Phase 3 (Dispatch Refactoring) implementation.
