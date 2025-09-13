# Problem: Ineffective LLM Use in Testing

I'm finding myself in a situation where I feel like I'm not using coding assistant tools effectively during the work-checking phase. I think this is because the training data associated with these tools heavily features test-driven development.

The specific issue I'm working with right now is that I'm refactoring one of my infrastructure components, specifically the cache. I'm trying to make it less tied to domain-specific business logic and more reusable. This process involved creating an abstraction class for Redis, and then building on that a specific class associated with AI-based caching.

The overall code refactoring process was accomplished pretty effectively. However, where it really fell down was that none of the unit tests written for the prior code passed with the new approach. The unit tests themselves were far too brittle, ultimately mocking a lot of implementation details as opposed to anything that might survive a fundamental refactoring like this.

## Developing a Public Contract Approach

So, I explored the concept of public contracts. This involves writing extremely detailed docstrings for each Python module, as well as for the underlying classes and methods within them. I then created a function that exports just enough information from the Python module to create a Python stub, which I call the module's public contract. This public contract serves as the basis for all subsequent testing. The idea is that unless the contract changes, the tests should pass, regardless of the implementation approach. The associated terminology I've encountered for this is focusing more on behavioral testing as opposed to implementation testing.

However, I'm having a lot of trouble. My current process involves taking the public contracts, pulling out the associated imports, creating happy path mocks for those imports, and consolidating them into different fixture files. These fixture files are then made available either to multiple modules within the same overall cache component or specifically to the module being tested. I then had it write all these behavior-based tests, hoping they would be much more resilient through refactoring and would focus on the core functionality I'm looking to test, as opposed to implementation details.

## Challenges with LLM-Assisted Testing

That process went okay; it created extraordinarily detailed docstrings that essentially serve as testing specifications. Now, I'm trying to convert those docstrings into the actual tests themselves. However, I'm still having trouble with LLM hallucinations. The models are adding new attributes or not calling things in a way that conforms to the specified mocks. This led me to research the concept of behavior-driven testing, as I want to apply the same principles as I move up the testing pyramid towards component integration testing.

However, behavior-driven testing also seems to be a philosophy focused on describing things in advance, *before* writing the implementation code, similar to my research on test-driven development. This runs into a fundamental issue with the process for coding assistants. In an ideal world, it would be great to do behavior-driven development and then test-driven development for individual components, moving through that entire process. But I'm not enthusiastic about that approach. Given the sophistication of models to generate production-ready code that largely works, it feels like a ton of extra work, extra tool calls, and token spend that isn't useful, engaging in the "write a test that fails, fix the failing test, then refactor" cycle.

I understand philosophically how test-driven development and behavior-driven development approaches work, especially when releasing a new feature in a "greenfield" scenario. However, I find them really tough on the "brownfield" side, particularly when trying to ensure tests survive refactoring or that post-refactoring testing is truly useful.

The heart of my dilemma is this: today, the power of large language models built into coding assistants is such that we can generate a pretty solid working program in a few shots. When coding assistants have nothing but green fields and blue skies ahead, they can achieve a lot, and their hallucinations can be internally consistent because they have free rein.

However, once you actually have a codebase, hallucinations become much more problematic. I feel like some of this is an issue with the training data. If models are trained heavily on test-driven development, they are likely also trained on really specific implementation details. Consequently, the models naturally suggest many implementation-focused tests. I've been working hard to steer the model towards behavioral-driven testing, but I still end up with examples where they hallucinate implementation details that don't exist—even when explicitly told to adhere to mocks specified against public contracts—or the tests just don't seem to add value. I feel like I'm spending a lot of time writing tests without seeing the necessary value.

## Seeking Alternative Testing Strategies

Has anyone formulated a different approach that leverages the models' intelligence (for lack of a better term) to generate initial code, and then considers a testing approach more related to that? This is as opposed to spending tokens to do the "right thing" of behavior-driven development or test-driven development.

Perhaps the answer is that there *is* a good way to do this, a method that was done well in software development before coding assistants and large language models emerged, and we shouldn't discard those good ideas. However, for a smaller-scale project like this LLM starter template and Fast API I'm working on, it feels like I'm spending an excessive amount of time and tokens on testing and getting the tests to work.

Instead, I'm finding much more value in carefully examining the production code, linting it, and running MyPy with type checking. These practices seem to be far more effective at identifying potential errors or issues caused by hallucinations in how components work together, producing much greater value and more bug fixes than this enormously complicated test suite.

This is what I'm dealing with. I'm looking for advice, feedback, and direction: are others thinking about these questions in the context of the modern intelligence of LLMs? For instance, I use Claude Code and Claude Sonnet 4 as the primary engine, and Gemini for larger context windows, to check work or perform spot checks.

The training data for the kinds of tasks I've been doing isn't as focused on contemporary content. Some of this information, like the Redis caching refactoring example, should be generatable simply based on existing training data. It doesn't rely on a hypothetical 2025 Redis release to work well; it's about effectively using established tools with Fast API.

I'm going to synthesize this and put it out to both Claude and Gemini to see what feedback they might have. In a recent conversation with Gemini about the same issue, it basically came down to: "Do I have to do all this unit testing?" And the answer was, "Yes, you do." I responded with something to the effect of, "Yes, and I should eat more vegetables too."

I understand the "why" and the potential value, but it seems that many previously established practices, while causing a different level of work and developer effort—such as writing failing tests, fixing them with code refactors, and so on—might not be ideal with LLMs. While LLM time might not differ from traditional developer time, for someone newer to this or approaching it from a "vibe coding" perspective, it feels like an incredible waste of tokens to spend so much time and energy on tests when the production code works quite well. Perhaps my current work isn't as sophisticated, and for millions of lines of code, one truly relies on these robust practices. However, I'm trying to figure out a smaller-scale version of this and how to appropriately adjust my testing expectations. I'm not unwilling to do unit testing or other forms of testing; I want to find bugs and reduce problems caused by hallucinations. But I also don't want to spend half my token budget on tests rather than functionality.

# Advice: Claude Opus 4.1

This is a thoughtful and nuanced exploration of a real challenge in modern software development with LLMs. You've articulated several key tensions that many developers are grappling with as we adapt our practices to leverage AI coding assistants effectively.

## The Core Dilemma

You've identified a fundamental mismatch: LLMs are trained on established testing patterns (TDD/BDD) that assume iterative, human-paced development, but they can generate working code so quickly that the traditional red-green-refactor cycle feels wasteful. This creates a workflow impedance mismatch.

## Alternative Testing Strategies for LLM-Assisted Development

Here are some pragmatic approaches that might better align with your workflow:

### 1. Contract-First Integration Testing

Since you've already invested in public contracts, lean into them differently:
- Write fewer, more comprehensive integration tests that exercise the public API
- Focus on testing the "edges" - the entry and exit points of your modules
- Use property-based testing (hypothesis in Python) to generate test cases automatically based on your contracts
- This gives you confidence in behavior without brittle unit test implementation details

### 2. Snapshot Testing with Selective Assertions

- Generate representative input/output pairs for your functions
- Store these as snapshots that can be automatically verified
- When refactoring, update snapshots only when behavior intentionally changes
- Combine with selective assertions for critical invariants

### 3. "Smoke Test First" Approach

- Start with end-to-end smoke tests that verify the system works for key use cases
- Add focused unit tests only when you find bugs or edge cases
- This inverts the traditional pyramid - start wide, narrow only where needed

### 4. Type-Driven Development

You mentioned MyPy is catching more issues than tests. Lean into this:
- Use more sophisticated type hints (Protocol, TypedDict, Literal types)
- Consider runtime validation libraries (Pydantic, beartype) that bridge static and runtime checking
- These catch many bugs that tests would otherwise need to find

### 5. AI-Assisted Test Generation with Human Curation

- Let the LLM generate a comprehensive test suite
- Quickly review and delete tests that:
- Test implementation details
- Are redundant with type checking
- Don't add meaningful coverage
- Keep only high-value behavioral tests

## Practical Recommendations

**For your specific Redis cache refactoring:**

Based on your exploration, I can see you're dealing with a fundamental challenge at the intersection of LLM capabilities and traditional software engineering practices. Your public contract approach is actually quite sophisticated, and your frustrations are entirely valid.

### A Pragmatic "LLM-First" Testing Strategy

Rather than fighting against the grain of how LLMs naturally generate code, here's an approach that leverages their strengths:

#### 1. "Outside-In" Testing Strategy

Start with what LLMs do best - understanding and testing complete behaviors:
```python
# Instead of unit tests with complex mocks, focus on behavioral integration tests
class TestCacheBehaviors:
    @pytest.fixture
    async def cache_with_redis(self):
        """Real Redis instance for testing - no mocks"""
        cache = AIResponseCache(redis_url="redis://localhost:6379/1")
        await cache.connect()
        yield cache
        await cache.clear()
    
    async def test_cache_preserves_ai_response_structure(self, cache_with_redis):
        """Test the actual behavior users care about"""
        response = {"summary": "Test", "confidence": 0.95}
        await cache.cache_response("text", "summarize", {}, response)
        
        cached = await cache.get_cached_response("text", "summarize", {})
        assert cached == response  # What actually matters
```

#### 2. "Example-Driven Testing"

Use your docstrings as executable specifications:
```python
def docstring_to_test(func):
    """Extract examples from docstrings and convert to tests"""
    examples = extract_examples_from_docstring(func.__doc__)
    for example in examples:
        # Generate test from example
        test_code = generate_test_from_example(example)
        exec(test_code)  # Dynamic test generation
```

#### 3. "Regression-First" Approach

Instead of TDD, capture current behavior and protect against regressions:
```python
# Generate behavior snapshots for existing working code
def capture_behavior_snapshot(module):
    """Capture current module behavior as test baseline"""
    public_methods = get_public_methods(module)
    snapshots = {}
    
    for method in public_methods:
        # Generate representative inputs
        inputs = generate_test_inputs_for_signature(method)
        outputs = [method(*inp) for inp in inputs]
        snapshots[method.__name__] = list(zip(inputs, outputs))
    
    return snapshots

# Then generate tests from snapshots
def generate_regression_tests(snapshots):
    """Create tests that verify behavior hasn't changed"""
    # LLM can generate these easily from input/output pairs
```

#### 4. "Minimal Mock" Testing Pattern

Only mock external boundaries, test everything else with real implementations:
```python
@pytest.fixture
def minimal_test_stack():
    """Only mock what leaves the process boundary"""
    with patch('redis.asyncio.Redis') as mock_redis:
        # Everything else uses real implementations
        cache = GenericRedisCache()
        cache.redis = mock_redis
        yield cache
```

#### 5. Type-First Validation

Since you mentioned MyPy catches more issues, lean heavily into runtime type validation:
```python
from pydantic import BaseModel, validator
from typing import runtime_checkable, Protocol

@runtime_checkable
class CacheProtocol(Protocol):
    """Runtime-checkable protocol for cache implementations"""
    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any, ttl: Optional[int]) -> None: ...

# Use Pydantic for runtime validation
class CacheOperation(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None
    
    @validator('key')
    def key_must_be_valid(cls, v):
        if not v or len(v) > 250:
            raise ValueError('Invalid cache key')
        return v
```

### Practical Implementation Strategy

Given your Redis cache refactoring, here's a concrete approach: `[LLM_TESTING_STRATEGY.md](/Users/matth/Github/MGH/fastapi-streamlit-llm-starter.worktrees/refactor-cache/docs/guides/developer/LLM_TESTING_STRATEGY.md)`

## The Bottom Line

Your frustrations are completely justified. The traditional TDD/BDD approach creates a fundamental impedance mismatch with LLM capabilities. You're not wrong to question spending half your token budget on tests rather than functionality.

The key insight is that **LLMs changed the economics of code generation**, but we haven't updated our testing practices to match. The approach I've outlined above - focusing on types, contracts, and behavioral testing rather than exhaustive unit testing - aligns much better with how LLMs naturally work.

For your Redis cache refactoring specifically, I'd suggest:

1. **Keep your public contracts** - they're valuable as documentation and type definitions
2. **Skip the brittle unit tests** - they're not adding value
3. **Write a few integration tests** that use real Redis (via Docker) to verify actual behavior
4. **Lean heavily on MyPy** and runtime type validation
5. **Use snapshot testing** to protect against regressions when refactoring

This isn't about being lazy or cutting corners - it's about adapting our practices to leverage the tools we have effectively. The "eat your vegetables" approach to testing made sense when writing code was the bottleneck. Now that LLMs can generate working code quickly, we need testing strategies that match this new reality.

Your comparison to eating vegetables is apt, but I'd reframe it: Traditional TDD is like insisting on cooking everything from scratch when you have access to a high-quality meal service. Sometimes the pragmatic choice is the right one.

# Advice: Gemini Pro 2.5

This is an incredibly insightful and well-articulated summary of a challenge that many developers are grappling with in the age of powerful coding assistants. You've hit upon a fundamental tension: established software development "best practices" were forged in an era where human-written code was the default, and the economics of time and effort were vastly different.

Your frustration is valid. The "eat your vegetables" analogy is perfect. You understand the nutritional value of robust testing, but the preparation process feels unnecessarily arduous and unsuited to your modern "kitchen."

Let's break down your situation and explore an alternative, LLM-native testing philosophy.

## The Core of the Conflict: Generative Speed vs. Verificative Rigor

You have correctly identified the root of the problem.

1.  **LLM Strength (Generation):** LLMs excel at generating plausible, often correct, "happy path" code based on high-level intent. They can fill in boilerplate, connect APIs, and structure classes with incredible speed. This is the "vibe coding" you mention—it feels fast and productive.
2.  **Traditional Testing Strength (Verification):** TDD/BDD are designed to force developers to think about specifications, edge cases, and contracts *before* implementation. They are tools for rigorous, deliberate thought, designed to prevent bugs that arise from unchecked assumptions.
3.  **The Mismatch:** The TDD/BDD cycle of "Red, Green, Refactor" feels wasteful when an LLM can jump straight to "Mostly Green" in a single shot. Asking an LLM to write a failing test first is often an awkward, token-intensive exercise in reverse-engineering a problem it's already trying to solve for you.

Furthermore, your observation about training data is spot on. LLMs have been trained on billions of lines of code from open-source projects. Many of those projects have tests that are tightly coupled to implementation details. Therefore, when asked to "write tests," the model's most probable path is to generate the kind of brittle, implementation-specific tests you're trying to avoid.

## A Proposed Alternative: The "Generate, Define, and Verify" (GDV) Workflow

Instead of fighting the LLM's nature, let's lean into it and adapt our process. This approach accepts that the initial code generation will be fast and imperfect, and shifts the human's primary role from *coder* to *architect and verifier*. Your "Public Contract" idea is the cornerstone of this.

Here is a step-by-step breakdown of the GDV workflow:

### Step 1: Generate (The Creative Phase)

This is where you leverage the LLM's speed.

  * **Prompt with Intent:** Give the LLM a high-level goal. "Refactor this Redis cache to be more abstract. Create a base `AbstractCache` class and a `RedisCache` implementation. Then, build an `AICache` on top of it that handles specific AI-related logic."
  * **Embrace the "First Draft":** Accept the output as a functional but unverified draft. It gets you 80% of the way there in 10% of the time. Don't worry about tests yet.
  * **Manual/Static Verification:** Do exactly what you found valuable: run the code, lint it, and run MyPy. Fix the obvious errors and inconsistencies that static analysis tools catch. These tools are deterministic and excellent at catching the type-related hallucinations LLMs are prone to.

### Step 2: Define (The Architectural Phase)

This is where your "Public Contract" idea becomes formalized and central to the entire process.

  * **Solidify the Contract:** Once the generated code is stable and seems to work, you—the human architect—review it and formalize its public-facing API.
  * **Write the Docstrings and Stubs:** Do exactly what you've been doing. Write detailed, specification-like docstrings for the public methods. Use a tool or a custom script to generate a Python stub file (`.pyi`) from these classes and methods. **This `.pyi` file is now the machine-readable, canonical source of truth for the component's behavior.**
  * **Why this is different:** You are not *predicting* behavior (like in BDD); you are *documenting and solidifying* the behavior of the generated code you've decided to keep. This contract is now the guardrail against both future refactoring mistakes and LLM hallucinations during test generation.

### Step 3: Verify (The Constrained Generation Phase)

Now, you use the LLM to generate tests, but you do so in a highly constrained environment to prevent hallucinations and ensure the tests are valuable. This is where we fix your current process.

The key to stopping hallucinations is to **drastically reduce the LLM's creative freedom.** Don't just tell it what the mocks are; provide them as immutable facts.

**A More Effective Prompting Strategy:**

Your prompt to the LLM for generating a test file should be structured and provide all necessary context *as code*.

```
[CONTEXT]
You are a senior software engineer writing behavioral tests using pytest. Your task is to write tests for the `AICache` class based *only* on its public contract and the provided mocks. You must not invent new attributes or methods. All interactions with external dependencies must use the provided pytest fixtures.

[PUBLIC CONTRACT UNDER TEST - AICache.pyi]
# This is the generated stub file. Provide the actual .pyi content here.
class AICache:
    def __init__(self, redis_cache: RedisCache) -> None:
        ...
    def get_embedding(self, key: str) -> list[float] | None:
        """
        Retrieves an embedding from the cache.
        Returns the embedding if found, otherwise None.
        """
        ...
    def set_embedding(self, key: str, embedding: list[float], ttl: int) -> None:
        """
        Stores an embedding in the cache with a specific TTL.
        """
        ...

[AVAILABLE MOCK FIXTURES - conftest.py]
# Provide the *exact* code for the mocks.
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_redis_cache():
    """A mock for the RedisCache dependency."""
    mock = MagicMock()
    # Pre-configure common behaviors based on the contract
    mock.get.return_value = None # Default case
    mock.set.return_value = True # Assume set always succeeds
    return mock

[TESTING SCENARIOS FROM DOCSTRINGS]
1.  **test_get_embedding_found:** When `get_embedding` is called with a key that exists in the underlying cache, it should call `redis_cache.get` with the correct key and return the deserialized embedding.
2.  **test_get_embedding_not_found:** When `get_embedding` is called with a key that does not exist, it should call `redis_cache.get` and return `None`.
3.  **test_set_embedding:** When `set_embedding` is called, it should serialize the data and call `redis_cache.set` with the correct key, serialized value, and TTL.

[TASK]
Write the pytest code for the `test_get_embedding_found` scenario in a file named `test_ai_cache.py`. Use the provided `mock_redis_cache` fixture.
```

**Why this prompt is more effective:**

  * **It's Explicitly Constrained:** Phrases like "based *only* on its public contract" and "must not invent" set clear rules.
  * **It Provides Code, Not Descriptions:** Giving the LLM the literal `.pyi` file and the `conftest.py` code is far more effective than describing them. The model is better at reading and using code than prose.
  * **It's Focused:** You ask it to write *one test* at a time. This reduces the cognitive load on the model and makes it easier to correct small errors. You can then use the correctly generated test as a few-shot example for the next one.

## Re-evaluating the Testing Pyramid in an LLM World

Your intuition is right. The classic testing pyramid might need to be re-shaped.

  * **Foundation (Largest Area): Static Analysis.** As you discovered, `linting` and `mypy` provide immense value for minimal effort. They are your first and best defense against LLM integration errors and type-related hallucinations. This layer is now *more important than ever*.
  * **Middle Layer: Behavioral/Contract Tests.** These are the unit/component tests you're working on. Their purpose is not to test every line of implementation but to verify that the public contract is upheld. The GDV workflow is designed to generate these efficiently. You may have fewer of these than traditional unit tests, but they will be more resilient to refactoring.
  * **Upper Layers: Integration & E2E Tests.** This is where you get huge value. After contract-testing your individual components, use the LLM to write higher-level tests. For example: "Write a FastAPI test using `TestClient` that hits the `/cache/{item_id}` endpoint. It should verify that if the item is not in the `AICache`, a call is made to the downstream data source, and the result is then stored in the cache." These tests are naturally behavioral and are excellent for verifying that the "plumbing" between LLM-generated components is correct.

## Answering Your Core Dilemma

**You do not have to do "all this unit testing" in the traditional sense.** You should, however, invest in a robust verification process. The GDV workflow proposes that this process is less about the "Red-Green-Refactor" ritual and more about:

1.  Leveraging LLMs for a fast first draft.
2.  Applying your human intelligence to define and solidify the component's public contract.
3.  Using the LLM as a highly-constrained tool to generate behavioral tests that verify this contract.

This approach respects your token budget by focusing human and LLM effort on high-value activities. Defining the contract is a high-leverage task that makes test generation cheaper and more reliable. You spend fewer tokens on rounds of "fix the hallucinated test" and more on getting it right the first time by providing better context.

You are not wrong to question the old ways. You are on the right track by trying to find a new synthesis that leverages the incredible power of these new tools without being dogmatically bound to practices from a previous era.

# Advice: GPT5 (high)

## Short answer

You don’t have to go full TDD/BDD to get durable tests. For a small-ish Python/FastAPI codebase with an LLM-driven workflow, a high-ROI approach is:
-  Freeze a public contract per module (typed stubs) and enforce “no contract drift” in CI.
-  Replace mocks with fakes and shared “contract tests” that run against any implementation of the interface.
-  Add a handful of integration “approval” tests at boundaries (FastAPI endpoints + Redis) and a few property-based tests for tricky invariants (e.g., TTL).
-  Lean on strict static checks (mypy/pyright, ruff), import boundaries, and regressions-as-they-appear.
-  When you ask a model to write tests, constrain it with a small, machine-readable contract digest and a fixed test template that forbids imports outside the public API.

This preserves the benefits of behavior-focused testing without the token/time overhead or brittleness of test-driving everything.

## A concrete, LLM-aware testing workflow

### 1. Freeze the public contract as code (typed stubs)
-  Generate .pyi stubs for your modules and commit them under a contracts/ directory. These are the source of truth for “what is public,” not how it’s implemented.
-  Enforce drift:
   -  In local dev and CI, compare runtime objects to the stub using mypy.stubtest. If the runtime surface deviates (added/removed names, incompatible types), you’ll get a hard failure until you intentionally update the stubs (and tests).
   -  Treat the stub diffs as the “breaking change” review surface.

Example commands (don’t run yet—just illustrating):
-  Stub generation: stubgen -m yourpkg.cache -o contracts
-  Contract drift check: python -m mypy.stubtest yourpkg.cache --concise

### 2. Write shared contract tests (one suite, many implementations)
-  The tests exercise behavior defined by the contract and run against multiple implementations via parametrization: your Redis-backed cache and a simple in-memory fake. No mocking of internals—only the interface.

```python
from typing import Protocol, Optional, TypeVar, Generic
import time

T = TypeVar("T")

class Cache(Protocol, Generic[T]):
    """Cache protocol.

    Markdown

    Args:
      key: Cache key.
      value: Cache value.
      ttl_seconds: Optional TTL in seconds.

    Behavior:
      - get(key) returns value if present and not expired, else None.
      - set(key, value, ttl_seconds) stores atomically.
      - delete(key) removes key; deleting absent keys is a no-op.
      - keys(prefix) lists keys by prefix. Order not guaranteed.
      - TTL tolerance: expiration may lag by <= 150ms under load.
    """

    def get(self, key: str) -> Optional[T]: ...
    def set(self, key: str, value: T, ttl_seconds: Optional[float] = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def keys(self, prefix: str = "") -> list[str]: ...
```
```python
# tests/contracts/test_cache_contract.py
import math
import time
import pytest
from hypothesis import given, strategies as st

# These factories are the extension point: point them at your real RedisCache and InMemoryCache.
IMPLEMENTATIONS = [
    pytest.param(lambda: InMemoryCache(), id="in-memory"),
    pytest.param(lambda: RedisCache(url="redis://localhost:6379/0"), id="redis"),
]

@given(k=st.text(min_size=1, max_size=32), v=st.binary(min_size=0, max_size=256))
@pytest.mark.parametrize("make_cache", IMPLEMENTATIONS)
def test_set_get_roundtrip(make_cache, k, v):
    c = make_cache()
    c.set(k, v)
    assert c.get(k) == v

@pytest.mark.parametrize("make_cache", IMPLEMENTATIONS)
def test_ttl_expiration_with_tolerance(make_cache):
    c = make_cache()
    c.set("k", b"v", ttl_seconds=0.25)
    start = time.perf_counter()
    # Busy-wait with small sleeps to avoid large wall clock uncertainty.
    while time.perf_counter() - start < 0.25 + 0.5:
        if c.get("k") is None:
            break
        time.sleep(0.01)
    elapsed = time.perf_counter() - start
    # Contract: must expire within 0.25s + 150ms tolerance (plus small loop overhead).
    assert elapsed <= 0.25 + 0.15 + 0.05

@pytest.mark.parametrize("make_cache", IMPLEMENTATIONS)
def test_delete_is_idempotent(make_cache):
    c = make_cache()
    c.delete("missing")
    c.set("a", b"x")
    c.delete("a")
    assert c.get("a") is None

@pytest.mark.parametrize("make_cache", IMPLEMENTATIONS)
def test_keys_prefix(make_cache):
    c = make_cache()
    for k in ["a:1", "a:2", "b:1"]:
        c.set(k, b"x")
    ks = set(c.keys("a:"))
    assert ks == {"a:1", "a:2"}
```

**Notes:**
-  This suite is stable across refactors because it depends only on the contract.
-  Hypothesis covers a lot of ground with little test code.
-  For time-based behavior, keep a small, explicit tolerance (or use freezegun if your impl supports injectable time).

### 3. Prefer fakes over mocks; use real infra selectively
-  Don’t mock internal functions. “Don’t mock what you don’t own.”
-  For Redis, either:
   -  Use fakeredis for fast local tests that approximate Redis semantics, or
   -  Use testcontainers to spin up ephemeral Redis in integration tests for true wire-level behavior.
   -  Keep only one place where you touch Redis specifics; the rest of the suite should stay on the interface.

### 4. Add a thin slice of high-value integration tests (“approval”/golden)
-  Hit FastAPI endpoints via TestClient with Redis running (fakeredis or testcontainers).
-  Snapshot structured JSON, not free-form strings, to reduce churn.
-  Use approval-style updates only when contract or behavior changes are intentional.
```python
# tests/integration/test_cache_via_api.py
from fastapi.testclient import TestClient

def test_cached_endpoint_roundtrip(app, live_redis):
    client = TestClient(app)
    r1 = client.get("/items/42")
    r2 = client.get("/items/42")
    assert r1.json() == r2.json()
    # Optional: assert a cache hit metric incremented, if you expose metrics via the public contract.
```

### 5. Enforce the contract mechanically (low token cost)
-  Stub generation:
   -  stubgen -m yourpkg.cache -o contracts
-  Contract drift gate in CI:
   -  python -m mypy.stubtest yourpkg.cache --concise
-  Static checks:
   -  mypy/pyright in strict mode on the implementation.
   -  ruff for style errors that often correlate with LLM hallucinations (unused imports, undefined names).
-  Dependency boundaries:
   -  Use import-linter to forbid tests importing non-public modules or private names (no from yourpkg._internal import ...).

### 6. Make docstrings actionable without bloating prompts
Keep your rich “behavior spec” docstrings, but also derive a small machine-readable “contract digest” per module that an LLM can use without hallucinating:
-  JSON: public names, signatures, allowed exceptions, error codes/messages, tolerances, and fixture names it may assume exist.
-  The LLM gets only this JSON + a fixed pytest template to fill. No source code, no private modules.
-  Example contract digest (hand-authored or auto-emitted from code + docstrings):

```json
{
  "module": "yourpkg.cache",
  "protocol": "Cache[bytes]",
  "functions": [],
  "methods": {
    "get": {"args": ["key:str"], "returns": "Optional[bytes]"},
    "set": {"args": ["key:str", "value:bytes", "ttl_seconds:Optional[float]=None"], "returns": "None"},
    "delete": {"args": ["key:str"], "returns": "None"},
    "keys": {"args": ["prefix:str=''"], "returns": "list[str]"}
  },
  "invariants": [
    "get returns None when missing or expired",
    "ttl expiration tolerance <= 150ms",
    "delete is idempotent",
    "keys returns set-equivalent results; order undefined"
  ],
  "fixtures_allowed": ["in_memory_cache_factory", "redis_cache_factory"]
}
```

Feed that to the model with a locked test template that:
-  Imports only from the public module.
-  Uses only the whitelisted fixtures.
-  Fails the review if it imports anything else or references unknown attributes.

### 7. Use “No-Lies Mocks” when you must mock

If you must mock (e.g., network), wrap calls with validate_call (pydantic or beartype) or a custom guard so tests fail fast on wrong arguments/signatures rather than silently passing with a hallucinated call shape.

### 8. Keep the suite small; invest where it pays

Aim for:
-  1 shared contract test module per interface (20–40 assertions total, much covered via Hypothesis).
-  3–8 endpoint-level integration/approval tests that exercise happy paths and a couple of failure modes.
-  2–3 regression tests for bugs you’ve fixed.
-  Let types, linters, and contract drift checks catch the rest. You’ll spend far fewer tokens writing/maintaining tests and avoid brittle mock jungles.

## How to migrate from brittle tests
-  Triage: keep any existing tests that assert external behavior (e.g., endpoint results, persisted state). Delete tests that import or patch internal functions/classes.
-  Introduce the contract + shared suite first. Make both implementations pass (fake + real).
-  Then add 1–2 integration tests for the cache’s main user flows (FastAPI endpoints).
-  Only then consider unit tests for tricky edge cases not covered by property tests.

## Prompting tips to stop LLM hallucinations in tests
-  Always provide: the .pyi stub (or compact contract digest) + the list of allowed fixtures + a test template with TODO blocks.
-  Hard constraints:
   -  “Import only from yourpkg.cache and pytest/hypothesis. Do not import private modules or attributes.”
   -  “Use only fixtures: X, Y. If a needed fixture is missing, stop and ask.”
   -  “Do not patch; do not access internal attributes; treat order of keys() as undefined.”
   -  Ask for a self-check: “List every import and explain how each is allowed by the contract.”

Optional helpers you can add:
-  A script to regenerate stubs and fail on drift:
   -  make contracts or a small Python script that runs stubgen and stubtest, then diffs.
-  A tiny in-memory cache that exactly implements the public contract (seed for the shared suite).
-  A pytest marker @pytest.mark.contract that you can run quickly in pre-commit.

This will get you durable, behavior-first tests without going full TDD or paying a big token tax, while aligning with your existing docstring-as-spec approach.