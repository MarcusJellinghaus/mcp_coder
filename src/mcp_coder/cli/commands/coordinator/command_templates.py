"""Command template strings for coordinator CLI operations.

This module centralizes all command templates used by the coordinator package:
- Test command templates (for coordinator test command)
- Workflow command templates (for coordinator run workflows)

All templates support format string placeholders:
- {log_level}: Logging level to use (debug, info, warning, error)
- {issue_number}: GitHub issue number (for create-plan workflows)
- {branch_name}: Git branch name (for implement and create-pr workflows)
"""

# Default test command for coordinator integration tests
# This comprehensive script verifies the complete environment setup
DEFAULT_TEST_COMMAND: str = """# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
export DISABLE_AUTOUPDATER=1
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra types
# Claude CLI verification
which claude
claude --mcp-config .mcp.json --strict-mcp-config mcp list
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir /workspace/repo --mcp-config .mcp.json
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

# Windows equivalent of DEFAULT_TEST_COMMAND
# Note: Using raw string (r""") for cleaner Windows path handling
DEFAULT_TEST_COMMAND_WINDOWS: str = r"""@echo ON

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

set DISABLE_AUTOUPDATER=1

echo Install type stubs in project environment ====================
uv sync --project %WORKSPACE%\repo --extra types

echo llm verification =====================================
mcp-coder verify
claude --mcp-config .mcp.json --strict-mcp-config mcp list 
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"

mcp-coder --log-level debug prompt "What is 1 + 1?"
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir %WORKSPACE%\repo --mcp-config .mcp.json

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

# Template selection mapping for execute_coordinator_test
TEST_COMMAND_TEMPLATES: dict[str, str] = {
    "windows": DEFAULT_TEST_COMMAND_WINDOWS,
    "linux": DEFAULT_TEST_COMMAND,
}

# Command templates for Jenkins workflows - Linux
# IMPORTANT: These templates assume Jenkins workspace clones repository to /workspace/repo
# The --project-dir parameter must match the Jenkins workspace structure
# All templates follow the pattern:
#   1. Checkout appropriate branch (main for planning, feature branch for implementation/PR)
#   2. Pull latest code
#   3. Verify tool versions
#   4. Sync dependencies
#   5. Execute mcp-coder command
CREATE_PLAN_COMMAND_TEMPLATE: str = """git checkout main
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra types
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

IMPLEMENT_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra types
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

CREATE_PR_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra types
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

# Windows workflow command templates
# Note: Using raw strings (r""") for cleaner Windows path handling
CREATE_PLAN_COMMAND_WINDOWS: str = r"""@echo ON

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

set DISABLE_AUTOUPDATER=1

echo Install type stubs in project environment ====================
uv sync --project %WORKSPACE%\repo --extra types

echo command execution  =====================================
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

IMPLEMENT_COMMAND_WINDOWS: str = r"""@echo ON

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

set DISABLE_AUTOUPDATER=1

echo Install type stubs in project environment ====================
uv sync --project %WORKSPACE%\repo --extra types

echo command execution  =====================================
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

CREATE_PR_COMMAND_WINDOWS: str = r"""@echo ON

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

set DISABLE_AUTOUPDATER=1

echo Install type stubs in project environment ====================
uv sync --project %WORKSPACE%\repo --extra types

echo command execution  =====================================
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

# Priority order for processing issues (highest to lowest)
PRIORITY_ORDER: list[str] = [
    "status-08:ready-pr",
    "status-05:plan-ready",
    "status-02:awaiting-planning",
]
