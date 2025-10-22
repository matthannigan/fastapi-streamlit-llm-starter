### **The Generation Prompt**

**ROLE:** You are an expert senior software engineer specializing in test architecture and automation. You have a keen eye for detail and are adept at parsing technical documentation to create structured data.

**GOAL:** Your task is to act as a data extraction and transformation tool. You will read the provided Markdown files (`TEST_PLAN.md`, `README.md`, `INTEGRATION_TESTS.md`) and generate a single, unified `backend/tests/integration/seams_manifest.yaml` file. This file will serve as the canonical inventory for all planned, implemented, and deferred integration tests, helping to prevent redundancy and provide a clear overview of test coverage.

**INPUT FILES:**

1.  **`TEST_PLAN.md`**: These files are the primary source for tests with the status `PLANNED` or `DEFERRED`.
    - `backend/tests/integration/resilience/TEST_PLAN.md`
    - `backend/tests/integration/text_processor/TEST_PLAN.md`
2.  **`README.md`**: This file is the primary source for tests with the status `IMPLEMENTED`.
    - `backend/tests/integration/auth/README.md`
    - `backend/tests/integration/cache/README.md`
    - `backend/tests/integration/environment/README.md`
    - `backend/tests/integration/health/README.md`
    - `backend/tests/integration/startup/README.md`
3.  **`docs/guides/testing/INTEGRATION_TESTS.md`**: This file provides philosophical context and definitions for terms like "seam" and "integration test." Use it to understand the user's intent, but not as a direct source for manifest entries.

**OUTPUT SPECIFICATION:**
You must generate a YAML file with a root key named `seams`, which contains a list of "seam" objects. Each seam object must adhere to the following structure and rules:

```yaml
- id: string (required)
  description: string (required)
  status: string (required, one of: IMPLEMENTED | PLANNED | DEFERRED)
  components: list of strings (required)
  location: string (nullable)
  plan_source: string (required)
  priority: string (nullable)
  tags: list of strings (required)
```

**FIELD-BY-FIELD INSTRUCTIONS:**

  * **`id`**:

      * Create a unique, `kebab-case` string identifier.
      * Derive the ID from the core components and purpose. For example, "API → TextProcessorService → AIResponseCache" could become `textproc-api-cache-performance`. "ENVIRONMENT-AWARE SECURITY" could become `startup-env-aware-security`.

  * **`description`**:

      * Write a concise, one-sentence summary of the seam's purpose.
      * For `PLANNED` tests, use the `SEAM` title or the `BUSINESS VALUE` section from `TEST_PLAN.md`.
      * For `IMPLEMENTED` tests, synthesize a description from the relevant section header in `README.md`.

  * **`status`**:

      * Set to `IMPLEMENTED` if the seam is derived from `README.md`.
      * Set to `PLANNED` if the seam is derived from the P0, P1, or P2 sections of `TEST_PLAN.md`.
      * Set to `DEFERRED` if the seam is derived from the "Deferred/Eliminated" section of `TEST_PLAN.md`.

  * **`components`**:

      * Extract the list of components directly from the `COMPONENTS` field in `TEST_PLAN.md` or from the descriptive text in `README.md`.
      * This must be a YAML list of strings.

  * **`location`**:

      * This field is ONLY for `IMPLEMENTED` tests. For all others, it should be `null`.
      * In `README.md`, you will find filenames like `test_environment_aware_security.py`.
      * You must construct the full relative path from the project root: `tests/integration/startup/FILENAME.py`.

  * **`plan_source`**:

      * This field identifies the origin document.
      * Use `TEST_PLAN.md` for entries from that file.
      * Use `README.md` for entries from that file.

  * **`priority`**:

      * This field is ONLY for `PLANNED` tests. For all others, it should be `null`.
      * Extract the priority (`P0`, `P1`, `P2`) from the section headers in `TEST_PLAN.md`.

  * **`tags`**:

      * Generate a list of relevant, lowercase keywords. This requires some inference.
      * Good sources for tags include: components (e.g., `cache`, `api`), purpose (e.g., `performance`, `resilience`, `security`), and pytest markers mentioned in the docs (e.g., `auth`, `batch`).
      * For `IMPLEMENTED` startup tests, a `startup` tag is appropriate.

**STEP-BY-STEP PROCESS:**

1.  **Process `README.md`**: Go through the "Critical Integration Seams" section. For each of the numbered test files/seams listed, create a seam object with the status `IMPLEMENTED`. Carefully populate all fields according to the rules above.
2.  **Process `TEST_PLAN.md`**:
      * Go through the "P0 - Must Have", "P1 - Should Have", and "P2 - Could Have" sections. For each of the seams listed, create a seam object with the status `PLANNED`.
      * Go through the "Deferred/Eliminated" section. For each of the seams listed, create a seam object with the status `DEFERRED`.
3.  **Consolidate and Format**: Combine all generated seam objects into a single list under the `seams` root key. Ensure the final output is a single, valid YAML code block.

The final YAML should be a complete and accurate inventory based *only* on the information provided in the source files. Do not invent seams or add information not present in the documents.

---

I would also like to add deferred tests mentioned in `TEST_PLAN.md` files that have already been implemented. Are you able to review these files and only add documented seams not otherwise listed in implemented tests? All should be marked as deferred.
- `backend/tests/integration/auth/TESTING_PLAN.md`
- `backend/tests/integration/cache/TEST_PLAN.md`
- `backend/tests/integration/cache/TEST_PLAN_encryption.md`
- `backend/tests/integration/environment/TEST_PLAN.md`
- `backend/tests/integration/health/TEST_PLAN.md`
- `backend/tests/integration/startup/TEST_PLAN.md`