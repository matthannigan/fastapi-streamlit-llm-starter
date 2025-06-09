### **1\. Background**

The current structure of the `backend/tests/` directory has grown organically and lacks a clear, logical organization. Unit tests, integration tests, and utility-specific tests are mixed at various levels, making it difficult to navigate, locate relevant tests, and scale the test suite effectively. This disorganization increases cognitive load for developers and can slow down maintenance and development.

**Current Structure:**
```
backend/
  tests/
    security/
      __init__.py
      test_context_isolation.py
      test_response_validator.py
    services/
      __init__.py
      test_cache.py
      test_monitoring.py
      test_prompt_builder.py
    utils/
      __init__.py
      test_prompt_utils.py
    __init__.py
    conftest.py
    README.md
    test_auth.py
    test_cache.py
    test_config.py
    test_dependencies.py
    test_dependency_injection.py
    test_main.py
    test_manual_api.py
    test_manual_auth.py
    test_models.py
    test_process_endpoint_auth.py
    test_resilience_endpoints.py
    test_resilience.py
    test_sanitization.py
    test_text_processor.py
```

The goal of this task is to refactor the directory into a conventional, scalable structure that separates tests by type and mirrors the application's source code layout.

### **2\. Proposed Solution**

We will reorganize the `backend/tests/` directory to introduce two primary subdirectories: `unit/` and `integration/`. The `unit/` directory will further mirror the structure of the `backend/app/` source directory.

**Proposed New Structure:**
```
backend/  
  tests/  
    ├── __init__.py  
    ├── conftest.py  
    ├── README.md  
    |  
    ├── integration/  
    │   ├── __init__.py  
    │   ├── test_main_endpoints.py  
    │   ├── test_auth_endpoints.py  
    │   ├── test_resilience_endpoints.py  
    │   └── test_monitoring_endpoints.py  
    │  
    └── unit/  
        ├── __init__.py  
        ├── test_auth.py  
        ├── test_config.py  
        ├── test_dependencies.py  
        │  
        ├── security/  
        │   ├── __init__.py  
        │   ├── test_context_isolation.py  
        │   └── test_response_validator.py  
        │  
        ├── services/  
        │   ├── __init__.py  
        │   ├── test_cache.py  
        │   ├── test_monitoring.py  
        │   ├── test_resilience.py  
        │   └── test_text_processor.py  
        │  
        └── utils/  
            ├── __init__.py  
            ├── test_prompt_builder.py  
            ├── test_prompt_utils.py  
            └── test_sanitization.py
```

### **3\. Requirements & Acceptance Criteria**

#### **Requirements**

1. **Directory Creation:**  
   * Create a `tests/unit/` directory.  
   * Create a `tests/integration/` directory.  
   * Within `tests/unit/`, create subdirectories that mirror the `backend/app/` structure (`security/`, `services/`, `utils/`).  
2. **File Migration and Consolidation:**  
   * Move all unit test files from the tests/ root and subdirectories into the corresponding location under `tests/unit/`.  
   * Consolidate existing endpoint tests (e.g., `test\_main.py`, `test\_resilience\_endpoints.py`, `test\_process\_endpoint\_auth.py`) into the `tests/integration/` directory with clear, resource-oriented names.  
   * The two `test\_cache.py` files must be merged into a single `tests/unit/services/test\_cache.py`.  
3. **CI/Configuration Updates:**  
   * Update `backend/pytest.ini` to correctly discover tests in the new structure. The testpaths variable should be adjusted accordingly.  
   * Update the GitHub Actions workflow file (`.github/workflows/test.yml`) to ensure the Run backend tests step correctly targets the new test paths.  
4. **Documentation:**  
   * Update `backend/tests/README.md` to reflect the new structure and provide clear instructions on where to place new unit and integration tests.

#### **Acceptance Criteria**

* **AC1:** All existing tests are successfully moved to their new locations within the `tests/unit/` and `tests/integration/` directories.  
* **AC2:** The tests directory structure exactly matches the "Proposed New Structure" outlined above.  
* **AC3:** All backend tests pass successfully when run locally (`cd backend && pytest`).  
* **AC4:** The CI pipeline (GitHub Actions) passes successfully for the backend tests, demonstrating that `pytest.ini` and workflow files are correctly configured.  
* **AC5:** The `backend/tests/README.md` file is updated to explain the new testing structure.

### **4\. Tasks (Checklist)**

* \[ \] Create the directory `backend/tests/unit`.  
* \[ \] Create the directory `backend/tests/integration`.  
* \[ \] Create subdirectories inside `backend/tests/unit` to mirror the app directory (security, services, utils).  
* \[ \] Move `backend/tests/test\_auth.py` to `backend/tests/unit/test\_auth.py`.  
* \[ \] Move `backend/tests/test\_config.py` to `backend/tests/unit/test\_config.py`.  
* \[ \] Move `backend/tests/test\_dependencies.py` to `backend/tests/unit/test\_dependencies.py`.  
* \[ \] Move `backend/tests/security/` contents to `backend/tests/unit/security/`.  
* \[ \] Move and merge `backend/tests/services/test\_cache.py` and `backend/tests/test\_cache.py` into `backend/tests/unit/services/test\_cache.py`.  
* \[ \] Move remaining files from `backend/tests/services/` to `backend/tests/unit/services/`.  
* \[ \] Move files from `backend/tests/utils/` to `backend/tests/unit/utils/`.  
* \[ \] Move `backend/tests/test\_main.py` to `backend/tests/integration/test\_main\_endpoints.py`.  
* \[ \] Move `backend/tests/test\_resilience\_endpoints.p`y to `backend/tests/integration/test\_resilience\_endpoints.py`.  
* \[ \] Consolidate `test\_process\_endpoint\_auth.py` and parts of `test\_manual\_auth.py` into `backend/tests/integration/test\_auth\_endpoints.py`.  
* \[ \] Update `backend/pytest.ini` test paths.  
* \[ \] Update `.github/workflows/test.yml` to reflect the new test command/paths.  
* \[ \] Update `backend/tests/README.md` with new structural guidelines.  
* \[ \] Run all backend tests locally to confirm they pass.  
* \[ \] Submit a Pull Request and ensure all CI checks pass.

### **5\. Justification & Benefits**

* **Improved Maintainability:** Developers can quickly find tests for the code they are working on.  
* **Enhanced Clarity:** The separation between unit and integration tests makes the purpose and scope of each test explicit.  
* **Scalability:** The mirrored structure provides a clear pattern for adding new tests as the application grows.  
* **Adherence to Best Practices:** This structure aligns with widely accepted conventions in the Python community.

### **6\. Impact Assessment**

* This is a structural refactoring and should have **no impact on the application's runtime behavior**.  
* The primary impact is on the development workflow and CI pipeline, which will need to be adjusted to the new test paths.  
* Existing Pull Requests may need to be rebased after this change is merged.
