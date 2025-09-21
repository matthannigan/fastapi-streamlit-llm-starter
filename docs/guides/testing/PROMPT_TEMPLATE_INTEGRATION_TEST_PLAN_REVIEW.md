
# Prompt Template: Integration Test Plan Review

## Goal

To perform a comprehensive review and critique of an integration test plan. The critique should be appended to the bottom of the specified test plan file.

## Context

You are an expert AI software developer reviewing a test plan for a complex system. Your review must be grounded in the project's established testing philosophy and the specific public contracts of the components involved.

### Step 1: Assimilate Core Testing Principles

Thoroughly review the following documents to understand the project's integration testing philosophy:

1.  `docs/guides/testing/INTEGRATION_TESTS.md`: For the high-level philosophy, definition of integration tests, and strategies for identifying critical seams.
2.  `docs/guides/testing/WRITING_TESTS.md`: For the principles of docstring-driven development and behavior-focused testing.

### Step 2: Understand the Public Contracts

Review the public contract definitions (`.pyi` files) for the components being tested. This is crucial for verifying that the test plan correctly interprets the component interactions.

**Relevant Contract Files:**
`[LIST_OF_RELEVANT_CONTRACTS]`

### Step 3: Analyze the Test Plan

Read the specified integration test plan file to understand its proposed scope, scenarios, and priorities.

**Test Plan to Review:**
`[PATH_TO_TEST_PLAN]`

### Step 4: Generate a Critique

Based on your analysis from the previous steps, generate a critique of the test plan. The critique should be constructive, balanced, and provide actionable recommendations.

**Critique Criteria:**

1.  **Alignment with Philosophy**: Does the plan adhere to the principles outlined in `INTEGRATION_TESTS.md`? Does it focus on testing behavior from the outside-in and target critical integration seams?
2.  **Contract Adherence**: Does the plan accurately reflect the public contracts of the components involved? Are the interactions to be tested valid?
3.  **Scenario Quality**: Are the test scenarios comprehensive, realistic, and behavior-focused? Do they cover a good range of success cases, failure modes, and edge cases?
4.  **Prioritization**: Is the implementation priority logical and risk-driven? Does it address the most critical and user-impacting functionality first?
5.  **Clarity and Structure**: Is the plan well-organized, clear, and easy to understand?

### Step 5: Format the Output

Append the critique to the end of the test plan file using the following Markdown format.

````markdown

---

## Critique of Integration Test Plan

[Provide a brief, high-level summary of your assessment.]

### Strengths

- [List 2-4 key strengths of the test plan. For example: excellent alignment with testing philosophy, comprehensive seam identification, logical prioritization, etc.]

### Areas for Improvement

- [List 1-3 specific, constructive areas where the plan could be improved. For example: could be more behavior-focused, lacks end-to-end validation, could benefit from more user-centric scenarios, etc.]

### Recommendations

1.  **[Actionable Recommendation 1]**: [Provide a concrete suggestion for improvement. For example: "Rephrase test scenarios to be more behavior-focused, emphasizing the observable outcomes from a user's perspective."]
2.  **[Actionable Recommendation 2]**: [Provide another concrete suggestion.]
3.  **[Actionable Recommendation 3]**: [Provide a final concrete suggestion, if applicable.]
````
