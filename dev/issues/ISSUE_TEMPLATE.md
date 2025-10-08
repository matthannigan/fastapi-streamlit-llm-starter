# {{ISSUE_TITLE}}

**Priority:** {{PRIORITY_LEVEL}}
**Type:** {{ISSUE_TYPE}}
**Component:** {{AFFECTED_COMPONENT}}
**Effort:** {{ESTIMATED_EFFORT}}
**Status:** {{CURRENT_STATUS}}
**Date:** {{CREATION_DATE}}

---

## Description

{{BRIEF_DESCRIPTION_OF_THE_ISSUE}}

## Background

{{DETAILED_BACKGROUND_CONTEXT}}

**Historical Context:**
{{ANY_RELEVANT_HISTORY_OR_TIMELINE}}

**Root Cause Discovery:**
{{HOW_THE_ISSUE_WAS_ORIGINALLY_IDENTIFIED}}

## Problem Statement

{{CLEAR_PROBLEM_DESCRIPTION}}

### Observable Symptoms

{{WHAT_BEHAVIOR_OR_SYMPTOMS_ARE_OBSERVED}}

**Examples:**
{{CONCRETE_EXAMPLES_OF_THE_PROBLEM_IF_AVAILABLE}}

## Root Cause Analysis

{{DETAILED_ANALYSIS_OF_WHY_THE_PROBLEM_OCCURS}}

### Contributing Factors

1. **{{FACTOR_1}}**
   {{EXPLANATION_OF_FACTOR_1}}

2. **{{FACTOR_2}}**
   {{EXPLANATION_OF_FACTOR_2}}

3. **{{FACTOR_3}}**
   {{EXPLANATION_OF_FACTOR_3}}

## Current Implementation

{{DESCRIPTION_OF_HOW_THE_SYSTEM_CURRENTLY_WORKS}}

```python
# {{FILE_PATH}} ({{LINE_NUMBERS}})
{{CURRENT_CODE_IMPLEMENTATION}}

# {{COMPARISON_WITH_OTHER_SIMILAR_CODE}}
{{CODE_COMPARISON_TO_SHOW_DIFFERENCES}}
```

**Compare with similar patterns:**
- `{{SIMILAR_PATTERN_1}}` - {{HOW_IT_WORKS_CORRECTLY}} ✅
- `{{SIMILAR_PATTERN_2}}` - {{HOW_IT_WORKS_CORRECTLY}} ✅
- `{{CURRENT_PROBLEMATIC_PATTERN}}` - {{WHATS_WRONG}} ❌

## Proposed Solutions

### Solution 1: {{SOLUTION_1_NAME}} {{(IMPLEMENTATION_STATUS)}}

{{DESCRIPTION_OF_SOLUTION_1}}

**Implementation:**

```python
# {{FILE_PATH}}
{{DETAILED_IMPLEMENTATION_CODE_FOR_SOLUTION_1}}
```

**Benefits:**
- ✅ {{BENEFIT_1}}
- ✅ {{BENEFIT_2}}
- ✅ {{BENEFIT_3}}

**Considerations:**
- {{CONSIDERATION_1}}
- {{CONSIDERATION_2}}

### Solution 2: {{SOLUTION_2_NAME}} {{(RECOMMENDED)}}

{{DESCRIPTION_OF_SOLUTION_2}}

**Implementation:**

```python
# {{FILE_PATH}}
{{DETAILED_IMPLEMENTATION_CODE_FOR_SOLUTION_2}}
```

**Benefits:**
- ✅ {{BENEFIT_1}}
- ✅ {{BENEFIT_2}}
- ✅ {{BENEFIT_3}}

**Risks:**
- {{RISK_1}}
- {{RISK_2}}

### Solution 3: {{SOLUTION_3_NAME}} {{(ALTERNATIVE)}}

{{DESCRIPTION_OF_SOLUTION_3}}

**Implementation:**

```python
# {{FILE_PATH}}
{{DETAILED_IMPLEMENTATION_CODE_FOR_SOLUTION_3}}
```

**Benefits:**
- ✅ {{BENEFIT_1}}
- ✅ {{BENEFIT_2}}

## Recommended Implementation Plan

### Phase {{PHASE_NUMBER}}: {{PHASE_NAME}} {{(TIME_ESTIMATE)}}

{{DESCRIPTION_OF_THIS_PHASE}}

**Tasks:**
- [ ] {{TASK_1}}
- [ ] {{TASK_2}}
- [ ] {{TASK_3}}

**Expected Outcome:**
{{WHAT_THIS_PHASE_SHOULD_ACHIEVE}}

### Phase {{PHASE_NUMBER}}: {{PHASE_NAME}} {{(TIME_ESTIMATE)}}

{{DESCRIPTION_OF_THIS_PHASE}}

**Tasks:**
- [ ] {{TASK_1}}
- [ ] {{TASK_2}}

**Expected Outcome:**
{{WHAT_THIS_PHASE_SHOULD_ACHIEVE}}

## Impact Analysis

### Performance Impact

{{DESCRIPTION_OF_PERFORMANCE_IMPLICATIONS}}

**Before {{SOLUTION_NAME}}:**
{{PERFORMANCE_METRICS_BEFORE}}

**After {{SOLUTION_NAME}}:**
{{PERFORMANCE_METRICS_AFTER}}

**Potential with {{OTHER_SOLUTION}}:**
{{ADDITIONAL_PERFORMANCE_IMPROVEMENTS}}

### Files to Modify

**Core Changes:**
- `{{FILE_PATH_1}}` - {{DESCRIPTION_OF_CHANGES}} ({{LINE_COUNT}} lines)
- `{{FILE_PATH_2}}` - {{DESCRIPTION_OF_CHANGES}} ({{LINE_COUNT}} lines)

**Review/Optional Updates:**
- `{{FILE_PATH_3}}` - {{DESCRIPTION_OF_CHANGES}}
- `{{FILE_PATH_4}}` - {{DESCRIPTION_OF_CHANGES}}

### Breaking Changes

{{DESCRIPTION_OF_ANY_BREAKING_CHANGES}}

- **{{BREAKING_CHANGE_LEVEL}}** - {{EXPLANATION}}
- {{DETAILS_ABOUT_BACKWARD_COMPATIBILITY}}

## Related Context

**Documentation:**
- `{{DOCUMENTATION_PATH_1}}` - {{DESCRIPTION}}
- `{{DOCUMENTATION_PATH_2}}` - {{DESCRIPTION}}

**Related Issues:**
- #{{RELATED_ISSUE_NUMBER}} - {{RELATED_ISSUE_TITLE}}
- #{{RELATED_ISSUE_NUMBER}} - {{RELATED_ISSUE_TITLE}}

**Current Implementation:**
- {{COMPONENT_1}}: `{{FILE_PATH}}` ({{DESCRIPTION}})
- {{COMPONENT_2}}: `{{FILE_PATH}}` ({{DESCRIPTION}})
- {{COMPONENT_3}}: `{{FILE_PATH}}` ({{DESCRIPTION}})

**PRDs and Design Docs:**
- `{{DESIGN_DOC_PATH}}` - {{DESCRIPTION}}

## Testing Requirements

### Unit Tests

```python
# {{TEST_FILE_PATH}}

def test_{{TEST_FUNCTION_NAME}}():
    """{{TEST_DESCRIPTION}}"""
    {{TEST_IMPLEMENTATION}}

def test_{{TEST_FUNCTION_NAME}}():
    """{{TEST_DESCRIPTION}}"""
    {{TEST_IMPLEMENTATION}}
```

### Integration Tests

```python
# {{INTEGRATION_TEST_FILE_PATH}}

async def test_{{TEST_FUNCTION_NAME}}():
    """{{TEST_DESCRIPTION}}"""
    {{INTEGRATION_TEST_IMPLEMENTATION}}
```

### Test Validation

1. {{VALIDATION_REQUIREMENT_1}}
2. {{VALIDATION_REQUIREMENT_2}}
3. {{VALIDATION_REQUIREMENT_3}}

## Monitoring and Observability

### Metrics to Track

{{METRICS_THAT_SHOULD_BE_TRACKED}}

### Expected Behavior

{{EXPECTED_BEHAVIOR_AFTER_IMPLEMENTATION}}

**Before Fix:**
{{UNDESIRED_BEHAVIOR}}

**After Fix:**
{{DESIRED_BEHAVIOR}}

## Decision

**Current Status:** {{CURRENT_IMPLEMENTATION_STATUS}}

**Impact Assessment:**
{{ASSESSMENT_OF_IMPACT_AND_SEVERITY}}

**Recommended Future Work** - {{RECOMMENDED_SOLUTION}}:

**Priority Justification:** {{WHY_THIS_PRIORITY_LEVEL}}

{{JUSTIFICATION_DETAILS}}

**Consider implementing if:**
1. {{CONDITION_1}}
2. {{CONDITION_2}}
3. {{CONDITION_3}}

**Alternative Approach:**
{{DESCRIPTION_OF_ALTERNATIVE_APPROACH}}

**Trade-offs:**
{{DESCRIPTION_OF_TRADE_OFFS}}

## Acceptance Criteria

- [ ] {{CRITERION_1}}
- [ ] {{CRITERION_2}}
- [ ] {{CRITERION_3}}
- [ ] {{CRITERION_4}}
- [ ] {{CRITERION_5}}

## Implementation Notes

### Suggested Approach

{{DETAILED_IMPLEMENTATION_GUIDANCE}}

1. **Step {{STEP_NUMBER}}**: {{STEP_NAME}} ({{TIME_ESTIMATE}})
   {{STEP_DETAILS}}

2. **Step {{STEP_NUMBER}}**: {{STEP_NAME}} ({{TIME_ESTIMATE}})
   {{STEP_DETAILS}}

3. **Step {{STEP_NUMBER}}**: {{STEP_NAME}} ({{TIME_ESTIMATE}})
   {{STEP_DETAILS}}

### Alternative: {{ALTERNATIVE_NAME}}

{{DESCRIPTION_OF_ALTERNATIVE_APPROACH}}

**Valid option because:**
{{REASONING}}

**Future decision point:** {{WHEN_TO_REVISIT_THIS}}

## Priority Justification

**{{PRIORITY_LEVEL}} Priority** because:
{{JUSTIFICATION_FOR_PRIORITY_LEVEL}}

**Consider prioritizing if:**
1. {{PRIORITY_CONDITION_1}}
2. {{PRIORITY_CONDITION_2}}
3. {{PRIORITY_CONDITION_3}}

---

## Labels

{{COMMA_SEPARATED_LIST_OF_LABELS}}

## References

- {{REFERENCE_1}}
- {{REFERENCE_2}}
- {{REFERENCE_3}}

---

**Instructions for LLM Use:**

1. Replace all `{{PLACEHOLDER}}` variables with specific information about your issue
2. Remove sections that don't apply to your specific issue
3. Adjust the level of detail based on issue complexity
4. For simple issues, focus on: Description, Problem Statement, Current Implementation, Proposed Solution, Acceptance Criteria
5. For complex issues, include: Background, Root Cause Analysis, Multiple Solutions, Implementation Plan, Impact Analysis
6. Always include concrete code examples when available
7. Use the Priority Justification section to explain why this issue deserves its priority level
8. Include file paths and line numbers whenever referencing specific code locations