r"""Template strings for VSCode Claude session files.

TWO-ENVIRONMENT SETUP:
======================

This system uses two separate Python virtual environments for proper isolation:

1. MCP-CODER ENVIRONMENT:
   - Location: {MCP_CODER_PROJECT_DIR}\.venv (where coordinator was run from)
   - Purpose: Contains mcp-coder executable and dependencies
   - Source: Set by coordinator before launching VS Code
   - Access: Added to PATH so mcp-coder commands work in project context

2. PROJECT ENVIRONMENT:
   - Location: {Current Directory}\.venv (issue-specific workspace)
   - Purpose: Contains project dependencies (pytest, etc.)
   - Activated: Direct activation with 'call .venv\Scripts\activate.bat'
   - Usage: Active Python environment for code execution

WORKFLOW:
---------
1. Coordinator sets MCP_CODER_PROJECT_DIR environment variable
2. VS Code launches in issue-specific directory
3. Script creates/activates project venv with dependencies
4. MCP-Coder tools added to PATH from install location
5. Automation runs using mcp-coder from PATH, project Python from venv

BENEFITS:
- Isolation: Each project gets its own dependencies
- Access: mcp-coder always available via PATH
- Correctness: Project code uses project Python/dependencies
- No conflicts: mcp-coder and project dependencies separated

"""

# Venv setup section for Windows
VENV_SECTION_WINDOWS = r"""echo Setting up environments...

REM Store the MCP-Coder environment path (from installation, not session)
if "{mcp_coder_install_path}" NEQ "" (
    set "MCP_CODER_VENV_PATH={mcp_coder_install_path}\.venv\Scripts"
    echo MCP-Coder environment: %MCP_CODER_VENV_PATH%
) else (
    echo ERROR: MCP_CODER_INSTALL_PATH not provided. This is a configuration issue.
    echo SOLUTION: The coordinator needs to determine the mcp-coder installation location.
    pause
    exit /b 1
)

REM Add MCP-Coder tools to PATH so they're available in project context
set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"

mcp-coder --version
echo   MCP-Coder install:    {mcp_coder_install_path}
echo   Project directory:    %CD%
echo.

REM Set MCP environment variables (for MCP server configuration)
set "MCP_CODER_PROJECT_DIR={session_folder_path}"
set "MCP_CODER_VENV_DIR={session_folder_path}\.venv"

REM Set up the project environment (current directory)
echo Project directory: %CD%
if not exist .venv\Scripts\activate.bat (
    echo Creating project virtual environment...
    uv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Activating project virtual environment...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment.
        pause
        exit /b 1
    )
    echo Installing project dependencies...
    setlocal EnableDelayedExpansion
    set UV_RETRY=0
    :retry_uv_sync
    uv sync --extra dev
    if errorlevel 1 (
        set /a UV_RETRY+=1
        if !UV_RETRY! LSS 3 (
            echo WARNING: uv sync failed ^(attempt !UV_RETRY! of 3^). Retrying in 5s...
            echo Common cause: file lock from antivirus or IDE indexing .venv
            timeout /t 5 /nobreak >nul
            goto :retry_uv_sync
        )
        echo ERROR: Failed to install dependencies after 3 attempts.
        echo TIP: Close other programs accessing .venv, then run: uv pip install -e ".[dev]"
        endlocal
        pause
        exit /b 1
    )
    endlocal
    set VENV_CREATED=1
) else (
    set VENV_CREATED=0
    echo Activating project virtual environment...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment.
        pause
        exit /b 1
    )
)

REM Install project in editable mode (ensures current code is always used)
uv pip install -e . --no-deps

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

for /f "delims=" %%i in ('mcp-coder prompt "{command} {issue_number}" --llm-method claude --output-format session-id --mcp-config .mcp.json --timeout {timeout}') do set SESSION_ID=%%i

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

claude "{command} {issue_number}"
"""

# Middle commands in multi-command flow for Windows (automated session resume)
AUTOMATED_RESUME_SECTION_WINDOWS = r"""echo.
echo === Step {step_number}: Automated Session ===
echo Running: {command}
echo.

mcp-coder prompt "{command}" --llm-method claude --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}

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

claude --resume %SESSION_ID% "{command}"
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

claude
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

# Gitignore entry
GITIGNORE_ENTRY = """
# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.txt
.vscodeclaude_analysis.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
"""
