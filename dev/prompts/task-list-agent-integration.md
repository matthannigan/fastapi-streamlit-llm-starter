**Usage Instructions**

1. **Create new agents first**: Run any agent creation commands based on previous recommendations
2. **Run this prompt**: Apply it to update the existing task list files
3. **Review output**: Verify the agent assignments make sense for your specific project context
4. **Iterate if needed**: If new technical requirements emerge, re-run this prompt

This prompt will consistently apply the Hybrid Strategy while preserving all your detailed task planning work and ensuring
optimal agent utilization for phased execution.

# Task List Agent Integration Prompt

You are tasked with enhancing deliverable task lists for execution by Claude agents.

## Instructions

1. **Read the current project PRD and Phase X plan files**:
    - `dev/taskplans/refactor-cache-infrastructure_PRD.md`
    - `dev/taskplans/refactor-cache-infrastructure_phase2_plan.md`

2. **Read the current task list files**:
    - `dev/taskplans/refactor-cache-infrastructure_phase2_tasks1-5.md`
    - `dev/taskplans/refactor-cache-infrastructure_phase2_tasks6-10.md`

3. **Analyze each deliverable** and determine:
    - Primary technical requirements and complexity patterns
    - Which specialized agents best match those requirements
    - Sequential dependencies between deliverables
    - Quality gate requirements (validation, security, compatibility)

4. **Add Agent Utilization Guide** at the top of each task list file with:
    - Sequential Development Path showing deliverable order and agent assignments
    - Parallel Development Opportunities where deliverables can run concurrently
    - Quality Gates showing validation checkpoints and responsible agents
    - Agent Handoff Points where deliverables transition between agents

5. **For each deliverable, add**:
    - **🤖 Recommended Agents**: Primary agent (required), Secondary agents (optional/specific subtasks)
    - **🎯 Rationale**: 1-2 sentence explanation of why these agents are optimal
    - **🔄 Dependencies**: Which deliverables must complete before this one begins
    - **✅ Quality Gate**: Which validation agent should review completion

6. **Preserve all existing content**:
    - Keep all original task numbers and descriptions unchanged
    - Maintain all technical specifications and acceptance criteria
    - Keep all completion checklists and notes

7. **Use this template structure**:

```markdown
# Phase W Task List: Deliverables X-Z

---

## 🔧 Agent Utilization Guide

### Sequential Development Path:
1. **Deliverable X**: [primary-agent] + [secondary-agent] (duration estimate)
2. **Deliverable Y**: [primary-agent] (depends on: Deliverable X)
[continue for all deliverables]

### Parallel Development Opportunities:
- **Deliverables X & Y**: Can run concurrently using [agent-1] and [agent-2]
- **Deliverables Z**: Requires completion of both X & Y

### Quality Gates:
- **After Deliverable X**: [validation-agent] for [specific validation type]
- **After Deliverable Y**: [validation-agent] for [specific validation type]
- **Before Phase Completion**: [security-agent] for security review

### Agent Handoff Points:
- **X → Y**: [primary-agent] completes foundation, [secondary-agent] handles integration
- **Y → Z**: [validation-agent] validates before [next-agent] begins

---

## Deliverable X: [Original Title]
**🤖 Recommended Agents**: [primary-agent] (primary), [secondary-agent] (secondary)
**🎯 Rationale**: [1-2 sentence explanation of why these agents are optimal]
**🔄 Dependencies**: [List prerequisite deliverables or "None"]
**✅ Quality Gate**: [validation-agent] for [validation type]

[All original content preserved exactly]
```

## Available Agents for Assignment

Base your recommendations on these available specialized agents:

### Existing Agents:

- cache-refactoring-specialist: Complex inheritance refactoring, parameter mapping, method override strategies
- monitoring-integration-specialist: Performance monitoring, metrics collection, analytics systems
- config-architecture-specialist: Configuration systems, validation frameworks, environment management
- integration-testing-architect: Comprehensive testing for inheritance hierarchies, migration validation
- module-architecture-specialist: Python module organization, import management, dependency resolution
- async-patterns-specialist: Python async/await patterns, concurrent programming, error handling
- compatibility-validation-specialist: Backwards compatibility, behavioral equivalence validation
- security-review-specialist: Security analysis for architecture changes, parameter handling

### Standard Agents:

- general-purpose: For simple tasks not requiring specialization
- docs-writer: For documentation creation following project standards

## Agent Selection Criteria

When recommending agents, consider:

1. Technical Complexity: More complex deliverables need specialized agents
2. Domain Expertise: Match agent expertise to deliverable requirements
3. Dependencies: Ensure agents can handle prerequisite knowledge
4. Quality Requirements: Include validation agents for critical deliverables
5. Performance Impact: Consider if monitoring specialists are needed
6. Security Implications: Include security review for architecture changes

## Output Requirements

1. Update each task list file with the Agent Utilization Guide and deliverable agent recommendations
2. Maintain all original content exactly as written
3. Ensure consistent formatting using the template structure
4. Verify agent assignments align with sequential development path
5. Document any assumptions made about deliverable dependencies

## Validation

After completing the updates:
1. Verify no original content was modified
2. Confirm all deliverables have appropriate agent assignments
3. Check that quality gates cover all critical validation points
4. Ensure the sequential development path is logical and efficient