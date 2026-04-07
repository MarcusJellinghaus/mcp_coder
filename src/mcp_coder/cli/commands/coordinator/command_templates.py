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
which mcp-tools-py && mcp-tools-py --help
which mcp-workspace && mcp-workspace --help
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
where mcp-tools-py
mcp-tools-py --version
where mcp-workspace
mcp-workspace --version
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
#   6. Capture exit code and run watchdog set-status
#   7. Archive logs
#   8. Exit with captured RC
#
# Silent-death recovery watchdog (see issue #713)
#
# After the main mcp-coder command, each template captures $RC / %ERRORLEVEL%
# and runs a conditional set-status that only fires if the issue is still at
# the in-progress label (--from-status). This rescues issues stuck by a
# silent process death where Python cleanup never ran.
#
# Recovery matrix:
#   Clean success        → label already past in-progress → watchdog no-ops
#   Graceful failure     → Python set a specific failure label → watchdog no-ops
#   Silent death (#710)  → issue still at in-progress label → watchdog rescues
#   Hard kill of shell   → watchdog never runs → not recoverable (out of scope)
#
# The watchdog always runs (not gated on exit code). The original exit code
# is re-emitted via exit $RC / exit /b %RC% so Jenkins sees the real outcome.
CREATE_PLAN_COMMAND_TEMPLATE: str = """git checkout main
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra types
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?

mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
"""

IMPLEMENT_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra types
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?

mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
"""

CREATE_PR_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra types
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?

mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
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
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
set RC=%ERRORLEVEL%

mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --force

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs

exit /b %RC%
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
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
set RC=%ERRORLEVEL%

mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --force

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs

exit /b %RC%
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
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
set RC=%ERRORLEVEL%

mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --force

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs

exit /b %RC%
"""

# Priority order for processing issues (highest to lowest)
PRIORITY_ORDER: list[str] = [
    "status-08:ready-pr",
    "status-05:plan-ready",
    "status-02:awaiting-planning",
]
