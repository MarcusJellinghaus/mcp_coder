# Step 1: Add Windows Template Constants

## Context
Reference: `pr_info/steps/summary.md`

This step adds four Windows batch script template constants to support Windows Jenkins executors. These templates mirror the existing Linux templates but use Windows-specific syntax.

## Objective
Add Windows command templates for:
1. Test command (environment verification)
2. Create-plan workflow
3. Implement workflow
4. Create-PR workflow

## WHERE
**File**: `src/mcp_coder/cli/commands/coordinator.py`

**Location**: Add after existing `DEFAULT_TEST_COMMAND` constant (around line 30)

## WHAT

### Constants to Add

#### 1. `DEFAULT_TEST_COMMAND_WINDOWS`
Windows equivalent of `DEFAULT_TEST_COMMAND` for environment verification.

#### 2. `CREATE_PLAN_COMMAND_WINDOWS`
Windows template for create-plan workflow.

#### 3. `IMPLEMENT_COMMAND_WINDOWS`
Windows template for implement workflow.

#### 4. `CREATE_PR_COMMAND_WINDOWS`
Windows template for create-pr workflow.

## HOW

### Integration Points
- **Import**: None needed (string constants)
- **Usage**: Will be used in Step 3 (template selection logic)
- **Position**: Add after `DEFAULT_TEST_COMMAND`, before `PRIORITY_ORDER`

### Template Content

All templates follow Windows batch script conventions:
- Start with `@echo ON`
- Use `%WORKSPACE%` for Jenkins workspace path
- Use `%VENV_BASE_DIR%` for virtual environment base directory
- Validate `%VENV_BASE_DIR%` with error handling
- Use `\.venv\Scripts\activate.bat` for virtual env activation
- Use `where` instead of `which` for command location
- Use `exit /b 1` for error exits
- Use `.mcp.json` for MCP config (not `.mcp.linux.json`)

## ALGORITHM

No algorithm needed - these are static string constants.

## DATA

### Constants Structure

```python
DEFAULT_TEST_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%
cd
dir

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

echo %VIRTUAL_ENV%
where python
python --version
pip list

echo Tools in current environment ===================
claude --version
where mcp-coder
mcp-coder --version
where mcp-code-checker
mcp-code-checker --version
where mcp-server-filesystem
mcp-server-filesystem --version
where mcp-config
mcp-config --version

echo llm verification =====================================
mcp-coder verify
claude --mcp-config .mcp.json --strict-mcp-config mcp list 
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"

mcp-coder --log-level debug prompt "What is 1 + 1?"
mcp-coder --log-level debug prompt "Which MCP server can you use?"
"""

CREATE_PLAN_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

echo command execution  =====================================
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json
"""

IMPLEMENT_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

echo command execution  =====================================
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json
"""

CREATE_PR_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

echo command execution  =====================================
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json
"""
```

### Key Differences from Linux Templates

| Aspect | Linux | Windows |
|--------|-------|---------|
| Shell header | `# Tool verification` | `@echo ON` |
| Path separator | `/` | `\\` |
| Env vars | `$VAR` | `%VAR%` |
| Venv activation | `source .venv/bin/activate` | `%VENV_BASE_DIR%\.venv\Scripts\activate.bat` |
| Command location | `which` | `where` |
| MCP config | `.mcp.linux.json` | `.mcp.json` |
| Git commands | `git checkout`, `git pull` | None (Jenkins handles) |
| Error exit | `exit 1` | `exit /b 1` |

## Implementation Steps

1. Open `src/mcp_coder/cli/commands/coordinator.py`
2. Locate `DEFAULT_TEST_COMMAND` constant (around line 23)
3. After `DEFAULT_TEST_COMMAND`, add a blank line and comment:
   ```python
   # Windows equivalent of DEFAULT_TEST_COMMAND
   ```
4. Add `DEFAULT_TEST_COMMAND_WINDOWS` constant
5. Add blank line and comment:
   ```python
   # Windows workflow command templates
   ```
6. Add `CREATE_PLAN_COMMAND_WINDOWS` constant
7. Add `IMPLEMENT_COMMAND_WINDOWS` constant
8. Add `CREATE_PR_COMMAND_WINDOWS` constant

## Testing

No tests needed for this step - these are static string constants. Template selection will be tested in Step 3.

## Validation

Run code quality checks to ensure no syntax errors:
```bash
mcp__code-checker__run_pylint_check
mcp__code-checker__run_mypy_check
```

## LLM Prompt for Implementation

```
I need to implement Step 1 of the Windows support implementation.

Context:
- Read pr_info/steps/summary.md for overall architecture
- Read pr_info/steps/step_1.md for detailed requirements

Task:
Add four Windows batch script template constants to src/mcp_coder/cli/commands/coordinator.py:
1. DEFAULT_TEST_COMMAND_WINDOWS
2. CREATE_PLAN_COMMAND_WINDOWS
3. IMPLEMENT_COMMAND_WINDOWS
4. CREATE_PR_COMMAND_WINDOWS

Requirements:
- Add after existing DEFAULT_TEST_COMMAND constant
- Use exact template content from step_1.md
- Follow Windows batch script conventions
- Use %WORKSPACE% and %VENV_BASE_DIR% environment variables
- Validate VENV_BASE_DIR with error handling
- Use .mcp.json for MCP config (not .mcp.linux.json)

After implementation:
- Run pylint and mypy checks using MCP tools
- Fix any issues found
```
