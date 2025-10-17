# Docstring Improvement with Change-Focused Review

Analyze $ARGUMENTS to determine the optimal approach for docstring improvement using up to 3 parallel, independent @agent-docstring-improver agents. Prioritize review of changed code areas while respecting existing documentation for unchanged components.

**🔍 CHANGE ANALYSIS (First Step):**
Before launching any agents, analyze git status to understand what has changed:

1. **Detect File Status**: Use `git status --porcelain` to categorize files:
   - **Modified (M)**: Existing files with changes - prioritize changed functions/classes
   - **Added (A)**: Newly staged files - complete docstring review needed
   - **Untracked (??)**: New files - complete docstring review needed
   - **Deleted (D)**: Removed files - skip

2. **Generate Change Context**: For modified files, run `git diff` to identify:
   - Specific functions/methods/classes that were modified
   - New code blocks added
   - Signature changes that affect docstring Args/Returns

3. **Change-Focused Instructions**: Include change analysis in agent instructions:
   - List specific functions/classes that were modified
   - Prioritize review of changed code areas
   - Respect existing docstrings for unchanged components
   - For new files, perform comprehensive review

**📂 SINGLE FILE DETECTION:**
IF $ARGUMENTS contains only one specific file path (not a wildcard or directory):
- Analyze the file's git status to determine review scope
- Launch a single @agent-docstring-improver agent with change-focused instructions
- For modified files: prioritize changed functions/classes only
- For new/untracked files: comprehensive docstring review

IF $ARGUMENTS contains only one specific file path AND a text string or list of text strings, it means the user wants those specific classes or methods to be the target of the docstring improvement within the single file.

**📁 MULTIPLE FILES/DIRECTORY/WILDCARD DETECTION:**
IF $ARGUMENTS contains:
- Multiple specific file paths
- A directory path
- Wildcard patterns (like `**/*.py` or `backend/app/**/*.py`)

**EXCEPTION**
- `__init__.py` files generally require special handling and should not be batch processed
- Only launch the @agent-docstring-improver agent for an `__init__.py` file if $ARGUMENTS explicitly mentions `__init__.py` 
- Do not process any `__init__.py` files found in a directory path search or that match a wildcard pattern

**🔄 PARALLEL PROCESSING STRATEGY:**
1. **CHANGE ANALYSIS FIRST**: Analyze git status for ALL resolved files to determine change scope
2. Group files by directory and change-type for optimal processing (recommended max 3 agents)
3. Launch up to 3 parallel @agent-docstring-improver agents, each handling a subset with change context

**⚙️ AGENT CONFIGURATION:**
Each agent will receive:
- Specific file(s) to process with change context
- Git change analysis highlighting modified functions/classes
- Clear scope boundaries to avoid duplicate work
- Instructions to follow comprehensive docstring standards from `docs/guides/developer/DOCSTRINGS_CODE.md`
- **Change-focused priority**: Focus review on modified code areas
- **Preservation directive**: Keep existing docstrings for unchanged components

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