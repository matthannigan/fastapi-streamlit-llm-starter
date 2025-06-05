## Dependency Management for `shared/` Module

### Current State Analysis

**Problematic Pattern Found Throughout Codebase:**
Hard-coded relative path navigation using sys.path.insert with multiple levels of directory traversal.

**Files Affected:**
- `backend/tests/conftest.py`
- `frontend/app/config.py`
- `frontend/app/utils/api_client.py`
- `backend/app/services/text_processor.py`
- `backend/app/config.py`
- All test files in both backend and frontend

### Functional Gaps Identified

#### 1. **Path Resolution Brittleness**
- **Gap**: Hard-coded relative path navigation fails when files are moved
- **Impact**: Refactoring breaks imports, deployment issues in different environments
- **Evidence**: Each file calculates path differently, some with 3 levels, some with 4

#### 2. **IDE and Tooling Support**
- **Gap**: IDEs cannot resolve imports properly due to runtime path manipulation
- **Impact**: No autocomplete, no type checking, no refactoring support
- **Evidence**: Import statements like `from shared.models import` show as unresolved

#### 3. **Testing Infrastructure Complexity**
- **Gap**: Test files require complex path setup before imports
- **Impact**: Test isolation issues, harder to run individual tests
- **Evidence**: Every `conftest.py` has different path manipulation code

#### 4. **Distribution and Packaging**
- **Gap**: Cannot package shared module independently
- **Impact**: Impossible to distribute as separate package, complicates CI/CD
- **Evidence**: No `setup.py`, `pyproject.toml`, or proper package structure

### Opportunities for Improvement

#### Immediate Solutions (1-2 days effort)

**1. Convert to Proper Python Package**
- Set up proper `pyproject.toml` with build system requirements
- Define project metadata including name, version, and dependencies
- Configure optional development dependencies for testing

**2. Update Requirements Files**
- Use editable installation references to shared module
- Ensure both backend and frontend can properly import shared code

**3. Remove All sys.path Manipulation**
- Replace problematic path insertion with standard Python imports
- Enable clean import statements throughout the codebase

#### Long-term Benefits
- **Better IDE Support**: Full autocomplete and type checking
- **Easier Testing**: No path manipulation in test files
- **Proper Packaging**: Can distribute shared module independently
- **Cleaner Imports**: Standard Python import patterns
- **Version Management**: Can version shared module separately