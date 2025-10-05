# Docstring Improvement with Parallel Processing

Analyze $AUGMENTS to determine the optimal approach for docstring improvement using our @agent-docstring-improver.

**📂 SINGLE FILE DETECTION:**
IF $AUGMENTS contains only one specific file path (not a wildcard or directory):
- Launch a single @agent-docstring-improver agent to examine that file
- Target: comprehensive docstring review and improvement for the specific file

**📁 MULTIPLE FILES/DIRECTORY/WILDCARD DETECTION:**
IF $AUGMENTS contains:
- Multiple specific file paths
- A directory path
- Wildcard patterns (like `**/*.py` or `backend/app/**/*.py`)

**EXCEPTION**
- `__init__.py` files generally require special handling and should not be batch processed
- Only launch a single @agent-docstring-improver agent if $AUGMENTS contains a single `__init__.py` file
- Do not process any `__init__.py` files found in a directory path search or that match a wildcard pattern 

**🔄 PARALLEL PROCESSING STRATEGY:**
1. First, resolve all file paths matching the patterns/directories
2. Group files by directory for optimal processing (recommended max 3 agents)
3. Launch up to 3 parallel @agent-docstring-improver agents, each handling a subset

**⚙️ AGENT CONFIGURATION:**
Each agent will receive:
- Specific file(s) to process
- Clear scope boundaries to avoid duplicate work
- Instructions to follow comprehensive docstring standards from `docs/guides/developer/DOCSTRINGS_CODE.md`

**📊 COORDINATION LOGIC:**
- **2-3 files**: Single agent processes all
- **4-6 files**: 2 parallel agents (split by directory/logical grouping)
- **7+ files**: 3 parallel agents (distribute evenly)
- Each agent runs `make generate-contracts` if they make changes

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