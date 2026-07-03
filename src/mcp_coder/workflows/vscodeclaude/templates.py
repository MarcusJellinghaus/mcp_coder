r"""Template strings for VSCode Claude session files.

TWO-ENVIRONMENT SETUP:
======================

This system uses two separate Python virtual environments for proper isolation:

1. MCP-CODER ENVIRONMENT:
   - Location: {MCP_CODER_PROJECT_DIR}/.venv (where coordinator was run from)
     (Windows: \.venv\Scripts; POSIX: /.venv/bin)
   - Purpose: Contains mcp-coder executable and dependencies
   - Source: Set by coordinator before launching VS Code
   - Access: Added to PATH so mcp-coder commands work in project context

2. PROJECT ENVIRONMENT:
   - Location: {Current Directory}/.venv (issue-specific workspace)
   - Purpose: Contains project dependencies (pytest, etc.)
   - Activated: Windows: 'call .venv\Scripts\activate.bat';
     POSIX: 'source .venv/bin/activate'
   - Usage: Active Python environment for code execution

WORKFLOW:
---------
1. Coordinator sets MCP_CODER_PROJECT_DIR environment variable
2. VS Code launches in issue-specific directory
3. Script creates/activates project venv with dependencies
4. MCP-Coder tools added to PATH from install location
5. Automation runs using mcp-coder from PATH, project Python from venv

PLATFORM TEMPLATES:
-------------------
Each section has a Windows variant (.bat, %VAR%, backslashes, Scripts/)
and a POSIX variant (sh, $VAR, forward slashes, bin/) chosen in Python at
script-creation time. No `case $(uname)` inside the generated shell — all
platform decisions are baked in by the caller in workspace.py for
testability.

BENEFITS:
- Isolation: Each project gets its own dependencies
- Access: mcp-coder always available via PATH
- Correctness: Project code uses project Python/dependencies
- No conflicts: mcp-coder and project dependencies separated

"""

# Venv setup section for Windows
#
# Provisioning is delegated to `tools/install.py` (canonical, edited in
# the repo, shipped in the wheel as a data-file at
# `<install-prefix>/share/mcp-coder/install.py`). It wraps the canonical
# install sequence — uv venv -> uv sync --extra dev -> GitHub overrides
# -> uv pip install -e . --no-deps. The same script is exercised by an
# integration test in this repo to prevent drift between the template
# and the installer.
VENV_SECTION_WINDOWS = r"""echo Setting up environments...

REM Store the MCP-Coder environment path (from installation, not session)
if "{mcp_coder_install_path}" NEQ "" (
    set "MCP_CODER_VENV_PATH={mcp_coder_install_path}\.venv\Scripts"
    echo MCP-Coder environment: %MCP_CODER_VENV_PATH%
) else (
    echo ERROR: MCP_CODER_INSTALL_PATH not provided. This is a configuration issue.
    echo SOLUTION: The coordinator needs to determine the mcp-coder installation location.
    exit /b 1
)

REM Add MCP-Coder tools to PATH (needed for install-env + the version check below;
REM activate.bat will overwrite PATH, so a second set is required after activation)
set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"

mcp-coder --version
echo   MCP-Coder install:    {mcp_coder_install_path}
echo   Project directory:    %CD%
echo.

REM Set MCP environment variables (for MCP server configuration)
set "MCP_CODER_PROJECT_DIR={session_folder_path}"
set "MCP_CODER_VENV_DIR={session_folder_path}\.venv"
REM See src/mcp_coder/llm/claude_settings.py for canonical value
set "MCP_TIMEOUT=30000"

REM Full git clone so setuptools_scm can read tags for version resolution (#817)
set "UV_GIT_SHALLOW=0"

REM Provision the project venv via the shared installer (single source of truth).
REM tools/install.py is the canonical script; the wheel ships it as a data file
REM at <install-prefix>/share/mcp-coder/install.py. workspace.py resolves the
REM path at session-launch time and substitutes it here.
"{mcp_coder_install_path}\.venv\Scripts\python.exe" "{install_script_path}" "%CD%" --source local --local-path "%CD%" --extras dev --use-sync --refresh{install_env_extra_flags}
if errorlevel 1 (
    echo ERROR: install-env failed.
    exit /b 1
)

REM Activate the venv that install-env created/refreshed
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

REM Re-ensure MCP-Coder tools remain in PATH after venv activation
REM (activate.bat overwrites PATH — do NOT remove this line, see #651/#694)
set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"

echo Environment setup complete.
echo - Project Python: %VIRTUAL_ENV%\Scripts\python.exe
echo - MCP-Coder tools available in PATH
echo.
"""

# Automated analysis section for Windows (using mcp-coder prompt)
AUTOMATED_SECTION_WINDOWS = r"""echo.
echo === Step {step_number}: Automated Analysis ===
echo Running: {command} {issue_number}
echo.

for /f "delims=" %%i in ('mcp-coder prompt "{command} {issue_number}" --llm-method claude --output-format session-id --mcp-config {mcp_config} --timeout {timeout}') do set SESSION_ID=%%i

if "%SESSION_ID%"=="" (
    echo.
    echo ERROR: Failed to get session ID from automated analysis.
    echo The mcp-coder prompt command may have failed.
    echo Please check the error messages above and try running Claude manually.
    echo.
    pause
    exit /b 1
)

echo Session ID: %SESSION_ID%
"""

# Single-command flow for Windows (no step labels, no session ID)
INTERACTIVE_ONLY_SECTION_WINDOWS = r"""echo.
echo Running: {command} {issue_number}
echo.

claude --mcp-config {mcp_config} --strict-mcp-config "{command} {issue_number}"
"""

# Middle commands in multi-command flow for Windows (automated session resume)
AUTOMATED_RESUME_SECTION_WINDOWS = r"""echo.
echo === Step {step_number}: Automated Session ===
echo Running: {command}
echo.

mcp-coder prompt "{command}" --llm-method claude --session-id %SESSION_ID% --mcp-config {mcp_config} --timeout {timeout}

if errorlevel 1 (
    echo.
    echo WARNING: Step {step_number} encountered an error.
    echo Continuing to next step...
    echo.
)
"""

# Last command in multi-command flow for Windows (interactive session resume)
INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS = r"""echo.
echo === Step {step_number}: Interactive Session ===
echo You can now interact with Claude directly.
echo The conversation context from previous steps is preserved.
echo.

claude --mcp-config {mcp_config} --strict-mcp-config --resume %SESSION_ID% "{command}"
"""


# Main startup script for Windows (with venv and mcp-coder)
STARTUP_SCRIPT_WINDOWS = r"""@echo off
chcp 65001 >nul

echo.
echo ==========================================================================
echo {emoji} Issue #{issue_number} - {title}
echo Repo:   {repo}
echo Status: {status}
echo URL:    {issue_url}
echo ==========================================================================
echo.

{venv_section}

{command_sections}
"""

# Intervention mode for Windows (with venv activation)
INTERVENTION_SCRIPT_WINDOWS = r"""@echo off
chcp 65001 >nul

echo.
echo ==========================================================================
echo {emoji} Issue #{issue_number} - {title}
echo Repo:   {repo}
echo Status: {status}
echo URL:    {issue_url}
echo ==========================================================================
echo.

{venv_section}

echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo !! INTERVENTION MODE - Automation may be running elsewhere
echo !! Investigate manually. No automated analysis will run.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo.

claude --mcp-config {mcp_config} --strict-mcp-config
"""

# Venv setup section for POSIX (macOS / Linux).
# See VENV_SECTION_WINDOWS above for the rationale; the install sequence
# is delegated to tools/install.py so both platforms share the same
# implementation.
VENV_SECTION_POSIX = r"""echo Setting up environments...

export MCP_CODER_VENV_PATH="{mcp_coder_install_path}/.venv/bin"
export MCP_CODER_PROJECT_DIR="{session_folder_path}"
export MCP_CODER_VENV_DIR="{session_folder_path}/.venv"
export MCP_TIMEOUT=30000
export UV_GIT_SHALLOW=0

export PATH="$MCP_CODER_VENV_PATH:$PATH"

mcp-coder --version
echo "  MCP-Coder install:    {mcp_coder_install_path}"
echo "  Project directory:    $PWD"
echo

# Provision the project venv via the shared installer.
# tools/install.py is the canonical script; the wheel ships it as a data
# file at <install-prefix>/share/mcp-coder/install.py. workspace.py
# resolves the path at session-launch time and substitutes it here.
"{mcp_coder_install_path}/.venv/bin/python" "{install_script_path}" "$PWD" --source local --local-path "$PWD" --extras dev --use-sync --refresh{install_env_extra_flags}

# Activate the venv that install-env created/refreshed
# shellcheck disable=SC1091
source .venv/bin/activate

# Re-prepend MCP-Coder tools to PATH (activate may overwrite PATH)
export PATH="$MCP_CODER_VENV_PATH:$PATH"

echo "Environment setup complete."
echo
"""

# Automated analysis section for POSIX (using mcp-coder prompt)
AUTOMATED_SECTION_POSIX = r"""echo
echo "=== Step {step_number}: Automated Analysis ==="
echo "Running: {command} {issue_number}"
echo

SESSION_ID=$(mcp-coder prompt "{command} {issue_number}" --llm-method claude --output-format session-id --mcp-config {mcp_config} --timeout {timeout})
if [ -z "$SESSION_ID" ]; then
    echo "ERROR: Failed to get session ID from automated analysis."
    exit 1
fi

echo "Session ID: $SESSION_ID"
"""

# Single-command flow for POSIX (no step labels, no session ID)
INTERACTIVE_ONLY_SECTION_POSIX = r"""echo
echo "Running: {command} {issue_number}"
echo

claude --mcp-config {mcp_config} --strict-mcp-config "{command} {issue_number}"
"""

# Middle commands in multi-command flow for POSIX (automated session resume)
AUTOMATED_RESUME_SECTION_POSIX = r"""echo
echo "=== Step {step_number}: Automated Session ==="
echo "Running: {command}"
echo

mcp-coder prompt "{command}" --llm-method claude --session-id "$SESSION_ID" --mcp-config {mcp_config} --timeout {timeout} || echo "WARNING: Step {step_number} encountered an error. Continuing..."
"""

# Last command in multi-command flow for POSIX (interactive session resume)
INTERACTIVE_RESUME_WITH_COMMAND_POSIX = r"""echo
echo "=== Step {step_number}: Interactive Session ==="
echo "You can now interact with Claude directly."
echo "The conversation context from previous steps is preserved."
echo

claude --mcp-config {mcp_config} --strict-mcp-config --resume "$SESSION_ID" "{command}"
"""

# Main startup script for POSIX (with venv and mcp-coder)
STARTUP_SCRIPT_POSIX = r"""#!/usr/bin/env bash
set -euo pipefail
trap 'read -r -p "Script failed (Enter to close)..."' ERR

echo
echo '=========================================================================='
echo '{emoji} Issue #{issue_number} - {title}'
echo 'Repo:   {repo}'
echo 'Status: {status}'
echo 'URL:    {issue_url}'
echo '=========================================================================='
echo

{venv_section}

{command_sections}
"""

# Intervention mode for POSIX (with venv activation)
INTERVENTION_SCRIPT_POSIX = r"""#!/usr/bin/env bash
set -euo pipefail
trap 'read -r -p "Script failed (Enter to close)..."' ERR

echo
echo '=========================================================================='
echo '{emoji} Issue #{issue_number} - {title}'
echo 'Repo:   {repo}'
echo 'Status: {status}'
echo 'URL:    {issue_url}'
echo '=========================================================================='
echo

{venv_section}

echo
echo '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
echo '!! INTERVENTION MODE - Automation may be running elsewhere'
echo '!! Investigate manually. No automated analysis will run.'
echo '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
echo

claude --mcp-config {mcp_config} --strict-mcp-config
"""


# VSCode workspace file template
WORKSPACE_FILE_TEMPLATE = """{{
    "folders": [
        {{
            "path": "{folder_path}"
        }}
    ],
    "settings": {{
        "window.title": "[#{issue_number} {stage_short}] {title_short} - {repo_name}",
        "task.allowAutomaticTasks": "on"
    }}
}}
"""

# VSCode tasks.json template
TASKS_JSON_TEMPLATE = """{{
    "version": "2.0.0",
    "tasks": [
        {{
            "label": "VSCodeClaude Startup",
            "type": "shell",
            "command": "{script_path}",
            "presentation": {{
                "reveal": "always",
                "panel": "new",
                "focus": true
            }},
            "runOptions": {{
                "runOn": "folderOpen"
            }},
            "problemMatcher": []
        }},
        {{
            "label": "Open Status File",
            "type": "shell",
            "command": "code",
            "args": ["${{workspaceFolder}}/.vscodeclaude_status.txt"],
            "presentation": {{
                "reveal": "never"
            }},
            "runOptions": {{
                "runOn": "folderOpen"
            }},
            "problemMatcher": []
        }}
    ]
}}
"""

# Status file template (plain text banner format)
STATUS_FILE_TEMPLATE = """==========================================================================
{status_emoji} Issue #{issue_number} - {title}
Repo:    {repo}
Status:  {status_name}
Branch:  {branch}
Started: {started_at}
{intervention_line}URL:     {issue_url}
==========================================================================
"""

# Terminal banner template (for non-script contexts)
BANNER_TEMPLATE = """
==========================================================================
{emoji} Issue #{issue_number} - {title}
Repo:   {repo}
Status: {status}
URL:    {issue_url}
==========================================================================
"""

# Intervention line for status file (includes newline for proper formatting)
INTERVENTION_LINE = """Mode:    ⚠️ INTERVENTION
"""

# Intervention warning banner (printed by Python before a bare `claude` launch).
# Verbatim text lifted from the retired INTERVENTION_SCRIPT_* shell templates;
# no `{}` placeholders because it is emitted as-is (no shell, no formatting).
INTERVENTION_WARNING = """
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! INTERVENTION MODE - Automation may be running elsewhere
!! Investigate manually. No automated analysis will run.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

# Thin launcher for Windows (.bat).
#
# The startup script collapses to a one-line launcher that bootstraps into
# Python; all orchestration lives in `session_setup.py`. The only placeholder
# is the coordinator's install path (used to locate its venv Python). `%CD%`
# is the session/project directory — the single source of truth passed as the
# module argument. `|| pause` keeps the window open if the interpreter itself
# cannot start (session_setup's own `main` handles expected failures + exits 0).
LAUNCHER_WINDOWS = (
    "@echo off\n"
    '"{mcp_coder_install_path}\\.venv\\Scripts\\python.exe" '
    '-m mcp_coder.workflows.vscodeclaude.session_setup "%CD%" || pause\n'
)

# Thin launcher for POSIX (.sh). See LAUNCHER_WINDOWS for the rationale; `$PWD`
# is the session directory and `read -r -p` is the POSIX equivalent of `pause`.
LAUNCHER_POSIX = (
    "#!/usr/bin/env bash\n"
    '"{mcp_coder_install_path}/.venv/bin/python" '
    '-m mcp_coder.workflows.vscodeclaude.session_setup "$PWD" '
    '|| read -r -p "Session failed (Enter to close)..."\n'
)

# Gitignore entry
GITIGNORE_ENTRY = """
# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.txt
.vscodeclaude_analysis.json
.vscodeclaude_session.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
"""
