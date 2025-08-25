
## Public Contract Stubs (Type Stubs)

### Purpose

This directory contains public contract stub files (``.pyi``) automatically generated from the production code in `backend/app`.

Each stub mirrors the public-facing interface of its corresponding source module while intentionally omitting implementation details. These stubs are used for tests, static analysis, and documentation where behavior and API shape matter more than internal logic.

### What appears in stubs

- Top-level imports (deduplicated, order preserved)
- Selected top-level public assignments, e.g.:
  - ALL_CAPS constants
  - Common public objects like `APIRouter`, `Blueprint`, `SQLAlchemy`
- Class definitions (including inheritance)
- Public function and method signatures (including `__init__`), with type hints
- Module, class, and function docstrings (properly indented)

### What is intentionally omitted

- All implementation code in function/method/class bodies (replaced with `...`)
- Private members (names starting with `_`) unless explicitly included during generation
- Most dunder methods if excluded during generation (with `__init__` typically retained)
- Nested imports and runtime-only constructs not relevant to the contract

### How to use these stubs

- Treat them as the authoritative public API surface for testing and review.
- Prefer generating tests against these stubs to validate behavior (signatures, docs) rather than implementation details.
- Use them for type-checking and as concise documentation of the API shape.

### Guidelines for AI coding assistants

When writing or refactoring tests, use the stubs here as the primary context. Avoid referencing `backend/app` implementation unless explicitly instructed. This ensures tests validate the public contract (what) rather than the implementation (how), making the suite more resilient to refactors and easier to maintain.