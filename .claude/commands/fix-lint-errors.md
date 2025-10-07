# Fix Lint Errors with Parallel Processing

Analyze $AUGMENTS to determine the optimal approach for lint fixing using our @agent-lint-fixer.

**📂 SINGLE FILE DETECTION:**
IF $AUGMENTS contains only one specific file path (not a wildcard or directory):
- Launch a single @agent-lint-fixer agent to examine that file
- Target: comprehensive file review and clearing of lint errors for the specific file

**📁 MULTIPLE FILES/DIRECTORY/WILDCARD DETECTION:**
IF $AUGMENTS contains:
- Multiple specific file paths
- A directory path
- Wildcard patterns (like `**/*.py` or `backend/app/**/*.py`)

**🔄 PARALLEL PROCESSING STRATEGY:**
1. First, resolve all file paths matching the patterns/directories
2. Group files by directory for optimal processing (recommended max 3 agents)
3. Launch up to 3 parallel @agent-lint-fixer, each handling a subset

**⚙️ AGENT CONFIGURATION:**
Each agent will receive:
- Specific file(s) to process
- Clear scope boundaries to avoid duplicate work

**📊 COORDINATION LOGIC:**
- **2-3 files**: Single agent processes all
- **4-6 files**: 2 parallel agents (split by directory/logical grouping)
- **7+ files**: 3 parallel agents (distribute evenly)

**✅ VALIDATION AND ERROR HANDLING:**
- Verify file paths exist before launching agents
- Handle permission/access issues gracefully
- Provide clear feedback on which files are being processed by which agent
- Report aggregate results from all agents

**📋 REPORTING:**
After all agents complete, provide a comprehensive summary:
- Files processed by each agent
- Changes made across all files
- Any files that couldn't be processed and why
- Overall alignment with project docstring philosophy
- Run `make generate-contracts` from the project root