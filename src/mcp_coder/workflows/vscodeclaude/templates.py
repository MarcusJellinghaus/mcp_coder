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
mcp-coder --version
echo   MCP-Coder install:    %MCP_CODER_PROJECT_DIR%
echo   Project directory:    %CD%
echo.

REM Store the MCP-Coder environment path (where this script is running from)
if defined MCP_CODER_PROJECT_DIR (
    set "MCP_CODER_VENV_PATH=%MCP_CODER_PROJECT_DIR%\.venv\Scripts"
    echo MCP-Coder environment: %MCP_CODER_VENV_PATH%
) else (
    echo ERROR: MCP_CODER_PROJECT_DIR not set. This script should be run from mcp-coder coordinator.
    echo SOLUTION: The coordinator needs to set this environment variable before launching VS Code.
    pause
    exit /b 1
)

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
    uv sync --extra dev
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
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

REM Add MCP-Coder tools to PATH so they're available in project context
set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"

echo Environment setup complete.
echo - Project Python: %VIRTUAL_ENV%\Scripts\python.exe
echo - MCP-Coder tools available in PATH
echo.
"""

# Automated analysis section for Windows (using mcp-coder prompt)
AUTOMATED_SECTION_WINDOWS = r"""echo.
echo === Step 1: Automated Analysis ===
echo Running: {initial_command} {issue_number}
echo.

for /f "delims=" %%i in ('mcp-coder prompt "{initial_command} {issue_number}" --output-format session-id --mcp-config .mcp.json --timeout {timeout}') do set SESSION_ID=%%i

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

# Discussion section for Windows (using mcp-coder prompt with session resume)
DISCUSSION_SECTION_WINDOWS = r"""echo.
echo === Step 2: Automated Discussion ===
echo Running: /discuss
echo.

mcp-coder prompt "/discuss" --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}

if errorlevel 1 (
    echo.
    echo WARNING: Discussion step encountered an error.
    echo Continuing to interactive session...
    echo.
)
"""

# Interactive section for Windows (raw claude CLI with resume)
INTERACTIVE_SECTION_WINDOWS = r"""echo.
echo === Step 3: Interactive Session ===
echo You can now interact with Claude directly.
echo The conversation context from previous steps is preserved.
echo.

claude --resume %SESSION_ID%
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

{automated_section}

{discussion_section}

{interactive_section}
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

# Startup script for Linux (.sh)
STARTUP_SCRIPT_LINUX = r"""#!/bin/bash
set -e

echo ""
echo "=========================================================================="
echo "{emoji} Issue #{issue_number} - {title}"
echo "Repo:   {repo}"
echo "Status: {status}"
echo "URL:    {issue_url}"
echo "=========================================================================="
echo ""

{automated_section}

echo ""
echo "=== Ready for interactive discussion ==="
echo ""

{interactive_section}
"""

# Automated analysis section for Linux
AUTOMATED_SECTION_LINUX = r"""echo "Running automated analysis..."
claude -p "{initial_command} {issue_number}" --output-format json --mcp-config .mcp.json > .vscodeclaude_analysis.json 2>&1

SESSION_ID=$(python3 -c "import json; d=json.load(open('.vscodeclaude_analysis.json')); print(d.get('session_id',''))")

if [ -z "$SESSION_ID" ]; then
    echo "ERROR: Could not extract session ID from analysis output."
    echo "Please run Claude manually."
    exit 1
fi

echo "Session ID: $SESSION_ID"
"""

# Interactive section for Linux
INTERACTIVE_SECTION_LINUX = r"""claude --resume "$SESSION_ID" {followup_command}
"""

# Intervention mode for Linux
INTERVENTION_SECTION_LINUX = r"""echo ""
echo "⚠️  INTERVENTION MODE - Automation may be running elsewhere"
echo "   Investigate manually. No automated analysis will run."
echo ""
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
