# Project Documentation Agent Guidance

This file provides guidance to coding assistants and agents when working with project documentation in the `docs` subdirectory of this repository.

General agent instructions regarding the repository overall are available at `../AGENTS.md`.

## Documentation Structure Overview

The project documentation is organized following a hierarchical, purpose-driven approach:

**Comprehensive documentation in `docs/` directory following `docs/DOCS_INDEX.md`:**

### 📖 Template Documentation Structure
- **`docs/README.md`**: Main project overview and quick start guide
- **`docs/get-started/`**: Setup & complete systems integration guide, installation checklist
- **`docs/reference/key-concepts/`**: Infrastructure vs Domain Services, Dual API Architecture
- **`docs/guides/`**: Comprehensive guides (backend, frontend, testing, deployment, customization)
- **`docs/guides/infrastructure/`**: AI, Cache, Monitoring, Resilience, Security services
- **`docs/guides/developer/`**: Authentication, code standards, Docker, documentation guidance

### 📚 Technical Deep Dives
- **`docs/reference/deep-dives/`**: FastAPI and Streamlit comprehensive technical analysis

### 📦 Code Reference (Auto-Generated)
- **`docs/code_ref/`**: Auto-generated code reference documentation (backend + frontend)
- **DO NOT EDIT** these files manually - they are generated via `make code_ref`
- Auto-generated files `./code_ref/**/index.md` correspond to `**/README.md` files throughout the repository structure

## Documentation Guidelines for Agents

### Essential Reading for Code Assistants

**Critical documentation files to understand before making changes:**
- **`docs/DOCS_INDEX.md`**: Complete documentation index with all available guides
- **`docs/get-started/SETUP_INTEGRATION.md`**: Complete systems integration guide
- **`docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md`**: Critical architectural distinction
- **`docs/reference/key-concepts/DUAL_API_ARCHITECTURE.md`**: Dual-API design patterns
- **`docs/guides/developer/CODE_STANDARDS.md`**: Standardized patterns and architectural guidelines
- **`docs/guides/developer/AUTHENTICATION.md`**: Authentication and authorization system
- **`docs/guides/get-started/TEMPLATE_CUSTOMIZATION.md`**: Understanding architecture for stability and customization

### Documentation Standards

**Key principles when working with documentation:**

1. **Reference existing structure** - Always check `docs/DOCS_INDEX.md` for current organization
2. **Point to canonical sources** - Link to detailed docs rather than duplicating content
3. **Maintain consistency** - Follow established formatting and organizational patterns
4. **Keep examples current** - Ensure code examples match current implementation
5. **Update cross-references** - When adding new docs, update relevant index and cross-reference files

**Writing standards for project documentation:**

- **Clarity**: Write for developers unfamiliar with the codebase
- **Actionability**: Include concrete steps and code examples
- **Currency**: Keep examples and references up to date with code changes
- **Navigation**: Provide clear cross-references and "See Also" sections
- **Testing**: Verify that documented procedures actually work

**Content guidelines:**
- Use consistent formatting with existing documentation
- Include both conceptual explanation and practical examples
- Reference specific file paths and line numbers when helpful
- Maintain the template-focused perspective (production-ready vs. educational examples)

### Auto-Generated Documentation

**Important restrictions and processes:**

**DO NOT EDIT these auto-generated files:**
- Any file in `docs/code_ref/`
- Files ending with `.generated.md`
- Index files that are marked as auto-generated

**To update auto-generated documentation:**
```bash
# Regenerate code reference documentation
make code_ref

# This will update all docs/code_ref/** files based on README.md files in the codebase
```

**Auto-generated mapping:**
- `docs/code_ref/backend/index.md` ← `backend/README.md`
- `docs/code_ref/frontend/index.md` ← `frontend/README.md`
- `docs/code_ref/**/index.md` ← corresponding `**/README.md` files

### Documentation Maintenance Tasks

**When working on documentation:**

1. **Adding new guides**: 
   - Place in appropriate `docs/guides/` subdirectory
   - Update `docs/DOCS_INDEX.md`
   - Add cross-references from related documentation

2. **Updating existing guides**:
   - Maintain existing file locations
   - Update modification dates
   - Check for broken internal links

3. **Architectural documentation**:
   - Update `docs/reference/key-concepts/` for major architectural changes
   - Coordinate with code changes to keep documentation current

4. **Developer guidance**:
   - Update `docs/guides/developer/` for new development patterns
   - Include practical examples and code snippets
   - Link to related infrastructure documentation

### Common Documentation Tasks for Agents

**Typical documentation work:**

1. **Updating API documentation**: Sync with backend changes
2. **Refreshing setup guides**: Keep installation and configuration current
3. **Expanding developer guides**: Add new patterns and best practices
4. **Maintaining cross-references**: Update links when files move or change
5. **Creating example documentation**: Document new infrastructure services or patterns

**Do NOT do without explicit request:**
- Create new top-level documentation sections
- Reorganize the existing documentation structure
- Create README.md files (follow the existing pattern of README.md placement)
- Modify auto-generated content

## See Also

- **Repository Overview**: `../AGENTS.md` for general repository guidance
- **Backend Development**: `../backend/AGENTS.md` for FastAPI-specific documentation needs
- **Frontend Development**: `../frontend/AGENTS.md` for Streamlit-specific documentation needs
- **Template Customization**: `../AGENTS.template-users.md` for user-facing documentation guidance
