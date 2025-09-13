# Docstring Templates and Guidance for Production Code

## Philosophy and Purpose

This project maintains a philosophical commitment to **rich, comprehensive docstrings** that serve two critical purposes:

1. **Demonstrating Best Practices**: Our docstrings exemplify high-quality code documentation for developers and future template users, showcasing professional standards for API documentation and code clarity.

2. **Test-Driven Documentation**: Our docstrings serve as the foundation for generating better, less brittle tests that focus on **what functions should do** rather than **how they currently work**. Well-documented behavior contracts enable behavior-based testing over implementation testing.

### Documentation Standards by Code Type

**🎯 COMPREHENSIVE DOCSTRINGS REQUIRED:**
- Public API functions and methods
- Core business logic components
- Service classes and their public methods
- Functions that will have tests written for them
- Complex algorithms or domain-specific logic

**📝 BASIC DOCSTRINGS SUFFICIENT:**
- Private methods (prefixed with `_`)
- Simple utility functions
- Internal helper classes
- Framework integration code
- One-line data transformations

*The goal is to document interfaces and contracts that external code depends on, not every implementation detail.*

---

## Production Code Docstring Templates

### Function/Method Docstring Template

```python
def function_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """
    [One-line summary of what the function does]
    
    [Optional: More detailed description of the purpose and use case]
    
    Args:
        arg1: Description including valid values, constraints, defaults
        arg2: Description including format requirements, optional nature
        
    Returns:
        Description of return value structure, possible states, data types
        
    Raises:
        SpecificException: When this specific condition occurs
        AnotherException: When this other condition occurs
        
    Behavior:
        - Key behavior #1 that external users can observe
        - Key behavior #2 that affects system state
        - Important side effects or state changes
        - Performance characteristics if relevant
        
    Examples:
        >>> result = function_name("valid_input", options)
        >>> assert result.status == "success"
        >>> 
        >>> # Error case
        >>> with pytest.raises(ValidationError):
        ...     function_name("", options)
    """
```

### Class Docstring Template

```python
class ServiceName:
    """
    [One-line summary of the class purpose]
    
    [Detailed description of what this class manages/provides]
    
    Attributes:
        public_attr: Description of public attribute and its purpose
        
    Public Methods:
        method1(): Brief description and primary use case
        method2(): Brief description and primary use case
        
    State Management:
        - How the class maintains state
        - Thread safety guarantees
        - Lifecycle considerations
        
    Usage:
        # Basic usage
        service = ServiceName(config)
        result = service.primary_method(input)
        
        # Advanced usage with error handling
        try:
            service = ServiceName(complex_config)
            result = service.process_with_fallback(data)
        except ConfigurationError:
            # Handle configuration issues
            pass
    """
```

---

## Writing Effective Docstring Components

### Args and Returns

#### Good Args Documentation
```python
def process_text(text: str, max_length: int = 1000, model: str = "gpt-4") -> ProcessedResult:
    """
    Args:
        text: Input text to process. Must be 1-50,000 characters, non-empty.
        max_length: Maximum output length in characters (100-5000, default: 1000)
        model: AI model to use, one of ["gpt-4", "claude-3", "gemini"] (default: "gpt-4")
    """
```

#### Good Returns Documentation  
```python
def analyze_sentiment(text: str) -> SentimentResult:
    """
    Returns:
        SentimentResult containing:
        - sentiment: str, one of ["positive", "negative", "neutral"] 
        - confidence: float, 0.0-1.0 confidence score
        - reasoning: str, explanation of the classification
        - metadata: dict, processing details including model_used and processing_time
    """
```

### Behavior

#### ✅ GOOD: Contract-Focused Behavior
```python
def process_document(doc: Document) -> ProcessedDocument:
    """
    Behavior:
        - Validates document format before processing
        - Retries failed operations up to 3 times with exponential backoff
        - Processes document sections in parallel when possible
        - Caches results for identical documents within session
        - Raises DocumentError for unsupported formats
        - Logs processing metrics for monitoring
        - Returns partial results if some sections fail
    """
```

#### ❌ BAD: Implementation-Focused Behavior
```python
def process_document(doc: Document) -> ProcessedDocument:
    """
    Behavior:
        - Creates a DocumentProcessor instance
        - Calls _validate_format() internally 
        - Instantiates a RetryManager with 3 attempts
        - Uses ThreadPoolExecutor for parallel processing
        - Stores results in internal _cache dict
        - Updates self._last_processed timestamp
    """
```

#### Categories of Good Behavior Documentation

##### **1. State Changes and Side Effects**
Document what changes in the system after the function runs:

```python
def create_user(user_data: UserData) -> User:
    """
    Behavior:
        - Validates user data against business rules
        - Generates unique user ID if not provided
        - Encrypts password using bcrypt
        - Sends welcome email to user's address
        - Creates audit log entry for user creation
        - Returns user object with generated ID and timestamps
    """
```

##### **2. Error Handling and Edge Cases**
```python
def parse_config_file(filepath: str) -> Config:
    """
    Behavior:
        - Reads file from filesystem with UTF-8 encoding
        - Parses YAML format with strict validation
        - Applies default values for missing optional fields
        - Validates all required fields are present
        - Raises FileNotFoundError if file doesn't exist
        - Raises ConfigError for invalid YAML syntax
        - Raises ValidationError if required fields missing
        - Logs warnings for deprecated configuration keys
    """
```

##### **3. Resource Management and Cleanup**
```python
async def download_file(url: str, destination: str) -> DownloadResult:
    """
    Behavior:
        - Opens HTTP connection with 30-second timeout
        - Downloads file in 8KB chunks to manage memory
        - Creates destination directory if it doesn't exist
        - Overwrites existing file at destination
        - Closes all connections even if download fails
        - Updates download progress via callback if provided
        - Verifies file integrity with checksum if available
    """
```

##### **4. Resilience and Recovery Patterns**
*Particularly relevant for this LLM starter template:*

```python
async def with_resilience(operation: str, strategy: ResilienceStrategy) -> Any:
    """
    Behavior:
        - Applies circuit breaker pattern to prevent cascade failures
        - Retries failed operations according to strategy configuration
        - Falls back to alternative implementations when available
        - Tracks success/failure metrics for monitoring
        - Logs resilience actions for debugging
        - Respects timeout constraints to prevent resource exhaustion
        - Returns successfully processed result or raises ProcessingError
    """
```

---

### Examples

#### Function Examples Guidelines

**Examples should:**
- Show the most common usage patterns
- Demonstrate expected input/output format
- Include both success and error scenarios
- Be executable (can be run as doctests)
- Progress from simple to complex usage

#### Good Function Examples

```python
def validate_api_key(api_key: str, service: str) -> ValidationResult:
    """
    Validates API key format and permissions for a specific service.
    
    Examples:
        >>> # Valid API key
        >>> result = validate_api_key("sk-1234567890abcdef", "openai")
        >>> assert result.is_valid
        >>> assert result.service == "openai"
        
        >>> # Invalid format
        >>> result = validate_api_key("invalid-key", "openai")
        >>> assert not result.is_valid
        >>> assert "format" in result.error_message
        
        >>> # Valid format but wrong service
        >>> result = validate_api_key("sk-1234567890abcdef", "anthropic")
        >>> assert not result.is_valid
        >>> assert "service mismatch" in result.error_message
        
        >>> # Exception for empty key
        >>> with pytest.raises(ValueError):
        ...     validate_api_key("", "openai")
    """
```

#### Examples for Complex Functions

```python
async def process_with_ai(text: str, config: AIConfig) -> AIResponse:
    """
    Examples:
        >>> # Basic usage
        >>> config = AIConfig(model="gpt-4", max_tokens=1000)
        >>> response = await process_with_ai("Summarize this text", config)
        >>> assert response.status == "success"
        >>> assert len(response.content) > 0
        
        >>> # With custom settings
        >>> config = AIConfig(
        ...     model="claude-3", 
        ...     max_tokens=500,
        ...     temperature=0.7,
        ...     fallback_model="gpt-3.5"
        ... )
        >>> response = await process_with_ai("Complex analysis task", config)
        >>> assert response.model_used in ["claude-3", "gpt-3.5"]
        
        >>> # Error handling
        >>> invalid_config = AIConfig(model="nonexistent-model")
        >>> response = await process_with_ai("test", invalid_config)
        >>> assert response.status == "error"
        >>> assert response.error_type == "model_not_found"
    """
```

---

### Usage

#### Class Usage Guidelines

**Usage should:**
- Show complete initialization patterns
- Demonstrate typical workflows
- Include error handling strategies
- Show resource cleanup when necessary
- Progress from basic to advanced scenarios

#### Good Class Usage Examples

```python
class ResilienceService:
    """
    Manages resilience patterns for external service calls.
    
    Usage:
        # Basic initialization
        service = ResilienceService(
            circuit_breaker_threshold=5,
            retry_attempts=3
        )
        
        # Simple operation with resilience
        @service.with_resilience("api_call")
        async def call_external_api():
            return await some_api_call()
        
        result = await call_external_api()
        
        # Advanced configuration with custom strategy
        custom_strategy = ResilienceStrategy(
            retry_policy=ExponentialBackoff(max_attempts=5),
            circuit_breaker=CircuitBreakerConfig(failure_threshold=10),
            fallback=lambda: {"status": "degraded", "data": None}
        )
        
        service = ResilienceService(strategy=custom_strategy)
        
        # Monitoring and health checks
        health = service.get_health_status()
        metrics = service.get_metrics()
        
        # Resource cleanup
        await service.shutdown()
    """
```

#### Usage for Complex Services

```python
class AIServiceOrchestrator:
    """
    Usage:
        # Production setup with full configuration
        config = OrchestratorConfig(
            primary_model="gpt-4",
            fallback_models=["claude-3", "gpt-3.5"],
            rate_limits={"gpt-4": 100, "claude-3": 200},
            timeout_seconds=30
        )
        
        orchestrator = AIServiceOrchestrator(config)
        await orchestrator.initialize()
        
        try:
            # Process single request
            response = await orchestrator.process_request(
                text="Analyze this data",
                operation_type="analysis",
                priority="high"
            )
            
            # Batch processing
            requests = [
                ProcessRequest(text="Text 1", type="summary"),
                ProcessRequest(text="Text 2", type="analysis")
            ]
            results = await orchestrator.process_batch(requests)
            
            # Monitor system health
            if not orchestrator.is_healthy():
                # Handle degraded state
                await orchestrator.enable_degraded_mode()
                
        finally:
            await orchestrator.shutdown()
            
        # Context manager usage (recommended)
        async with AIServiceOrchestrator(config) as orchestrator:
            response = await orchestrator.process_request(text, "summary")
            # Automatic cleanup on exit
    """
```

---

### Language and Style Guidelines

**Use Active, Specific Language**
```python
# ❌ Vague
"""Behavior: Handles user input and does processing"""

# ✅ Specific  
"""Behavior: Validates user input format, processes text through AI model, returns structured results"""
```

**Focus on "What Happens" Not "How It Happens"**
```python
# ❌ Implementation details
"""Behavior: Creates HTTPSession object, iterates through retry_attempts list, calls requests.get()"""

# ✅ Observable behavior
"""Behavior: Makes HTTP request with automatic retries, handles network timeouts gracefully"""
```

**Document Guarantees and Invariants**
```python
def transfer_funds(from_account: str, to_account: str, amount: Decimal) -> TransferResult:
    """
    Behavior:
        - Validates both accounts exist and are active
        - Ensures from_account has sufficient balance
        - Performs atomic transfer (both accounts updated or neither)
        - Maintains account balance invariants (no negative balances)
        - Records transaction in audit log before updating balances
        - Sends notification to both account holders
        - Returns transaction ID for tracking
    """
```

---

## Using Rich Docstrings for Creating Tests

Well-documented interfaces naturally lead to better tests. Here's how different docstring sections translate into specific test patterns:

### Input Contracts
**Rich Docstring**
```python
def validate_config(config: dict) -> ValidationResult:
    """
    Args:
        config: Configuration dictionary with required keys:
               - 'model': str, one of ['gpt-4', 'claude', 'gemini']
               - 'timeout': int, 1-300 seconds
               - 'retries': int, 0-10 attempts
               Optional keys:
               - 'fallback_model': str, same options as 'model'
    """
```

**Generated Test:**
```python
def test_validate_config_required_fields():
    """Test validation requires all mandatory fields."""
    minimal_config = {
        'model': 'gpt-4',
        'timeout': 30,
        'retries': 3
    }
    result = validate_config(minimal_config)
    assert result.is_valid

def test_validate_config_invalid_model():
    """Test validation rejects invalid model names."""
    config = {'model': 'invalid-model', 'timeout': 30, 'retries': 3}
    result = validate_config(config)
    assert not result.is_valid
```

### Return Contracts
**Rich Docstring**
```python
def process_batch(items: List[str]) -> BatchResult:
    """
    Returns:
        BatchResult with:
        - success_count: int, number of successfully processed items
        - failed_items: List[str], items that failed processing
        - results: List[ProcessedItem], successful results in order
        - total_time: float, processing time in seconds
        
        Guarantees:
        - success_count + len(failed_items) == len(input items)
        - results list contains only successful items
        - failed_items preserves original input strings
    """
```

**Generated Test:**
```python
def test_process_batch_counts_match():
    """Test batch result counts match input per docstring guarantee."""
    items = ["item1", "item2", "item3"]
    result = process_batch(items)
    
    assert result.success_count + len(result.failed_items) == len(items)
    assert len(result.results) == result.success_count
```

### Behavior Contracts
**Rich Docstring**
```python
async def with_retry(operation: Callable, strategy: RetryStrategy) -> Any:
    """
    Behavior:
        - Attempts operation according to strategy.max_attempts
        - Waits strategy.delay_seconds between attempts
        - Raises original exception if all attempts fail
        - Returns immediately on first success
        - Logs each retry attempt for monitoring
    """
```

**Generated Test:**
```python
@pytest.mark.asyncio
async def test_with_retry_succeeds_immediately():
    """Test retry returns immediately on first success."""
    success_operation = AsyncMock(return_value="success")
    strategy = RetryStrategy(max_attempts=3, delay_seconds=1)
    
    result = await with_retry(success_operation, strategy)
    
    assert result == "success"
    success_operation.assert_called_once()  # No retries needed
```



## Common Docstring Anti-Patterns to Avoid

**❌ Restating the function signature:**
```python
def get_user_by_id(user_id: int) -> User:
    """Gets a user by ID."""  # Adds no value
```

**❌ Documenting implementation details:**
```python
def calculate_total(items: List[Item]) -> float:
    """Uses a for loop to iterate through items and sum their prices."""
```

**❌ Vague or unhelpful descriptions:**
```python
def process_data(data: dict) -> dict:
    """Processes the data and returns processed data."""
```

## Coding Assistant Integration

### Prompt for Improving Docstrings

Use this prompt with your coding assistant to enhance docstrings in existing code:

```
I want to improve the docstrings in [FILE/DIRECTORY] to follow our project's comprehensive documentation standards. Please review and enhance the docstrings using these guidelines:

**STANDARDS TO APPLY:**
1. Use our function/method template with Args, Returns, Raises, Behavior, and Examples sections
2. Use our class template with Attributes, Public Methods, State Management, and Usage sections
3. Focus on BEHAVIOR documentation that describes observable outcomes, not implementation details
4. Include practical EXAMPLES that show common usage patterns and error scenarios
5. Include comprehensive USAGE sections for classes that show initialization, typical workflows, and resource management

**BEHAVIOR DOCUMENTATION RULES:**
- Document what external observers can verify
- Focus on state changes, side effects, error conditions, and resource usage
- Avoid internal method calls, variable names, or implementation algorithms
- Write each behavior as a testable assertion

**EXAMPLES/USAGE RULES:**
- Show progression from simple to complex usage
- Include both success and error scenarios
- Make examples executable when possible
- For classes, show complete workflows including initialization and cleanup

**SCOPE:**
- Apply comprehensive docstrings to: public functions, service classes, core business logic
- Apply basic docstrings to: private methods, simple utilities, internal helpers

**APPROACH:**
1. Review existing docstrings and identify what's missing
2. Enhance Args/Returns/Raises sections with specific constraints and formats
3. Add or improve Behavior sections focusing on observable outcomes
4. Add practical Examples/Usage that demonstrate real-world scenarios
5. Ensure consistency with our template format

Please enhance the docstrings while preserving the existing code functionality. Focus on making the documentation serve as clear specifications for both users and test generation.
```

### Prompt for Test Generation from Docstrings

```
Generate comprehensive tests for [FUNCTION/CLASS] based strictly on its docstring specification. Use the docstrings as the primary specification for test generation.

**CORE PRINCIPLES:**
1. TEST WHAT'S DOCUMENTED: Only test behaviors, inputs, outputs, and exceptions mentioned in docstrings
2. IGNORE IMPLEMENTATION: Don't test internal methods, private attributes, or undocumented behavior  
3. FOCUS ON CONTRACTS: Test that the function fulfills its documented contract
4. USE DOCSTRING EXAMPLES: Convert docstring examples into actual test cases
5. TEST EDGE CASES FROM DOCS: If docstring mentions limits (1-50,000 characters), test the boundaries
6. DON'T OVER-TEST: If it's not in the docstring, it's probably not worth testing

**SYSTEMATIC APPROACH:**
- **Args section** → Input validation tests and boundary conditions
- **Returns section** → Return value structure and content verification  
- **Raises section** → Exception condition tests
- **Behavior section** → Observable outcome tests for each documented behavior
- **Examples section** → Convert to executable test cases

**TEST STRUCTURE:**
- Use descriptive test names that reflect documented behavior
- Group related tests in test classes  
- Include both positive and negative test cases
- Use appropriate fixtures and mocking for external dependencies

**AVOID TESTING:**
- Internal implementation details not mentioned in docstring
- Private methods or undocumented attributes
- Specific algorithms or data structures used internally
- Framework or library integration details

Generate tests that would pass as long as the function fulfills its documented contract, regardless of how it's implemented internally.
```

---

## Benefits of This Approach

### **For Development Quality:**
- Creates living documentation that stays current
- Establishes clear contracts between components
- Reduces ambiguity in API usage
- Demonstrates professional documentation standards

### **For Testing Quality:**
- Enables behavior-focused rather than implementation-focused tests
- Provides clear specifications for test generation
- Reduces test brittleness during refactoring
- Creates natural boundary testing from documented constraints

### **For Maintenance and Onboarding:**
- New team members can understand component contracts quickly
- Reduces time spent deciphering function behavior during debugging
- Makes refactoring safer by clearly defining what must be preserved
- Enables confident code changes when contracts are well-defined

### **For Template Users:**
- Showcases industry best practices for API documentation
- Provides examples of comprehensive function and class documentation
- Demonstrates how documentation can drive test quality
- Creates reusable patterns for their own projects

---

## Related Documentation

### **How This Document Connects:**
- **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)**: Test documentation standards that use production docstrings as specifications
- **[TESTING.md](./TESTING.md)**: Docstring-driven test development methodology and behavior-focused testing

### **Complementary Guides:**
- **[CODE_STANDARDS.md](./CODE_STANDARDS.md)**: Overall code quality standards that include docstring requirements
- **[EXCEPTION_HANDLING.md](./EXCEPTION_HANDLING.md)**: Exception documentation patterns that enhance testing

By maintaining this philosophical commitment to rich docstrings, we create a codebase that is both exemplary for developers and optimized for generating high-quality, maintainable tests.