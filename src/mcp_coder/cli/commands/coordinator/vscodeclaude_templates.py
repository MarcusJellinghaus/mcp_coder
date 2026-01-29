"""Template strings for VSCode Claude session files."""

# Startup script for Windows (.bat)
STARTUP_SCRIPT_WINDOWS = r"""@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  {emoji} {stage_name:46}  #{issue_number:6}  ║
echo ║  {title:58}  ║
echo ║  {repo:20} ^| {status:35}  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

{automated_section}

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  Ready for interactive discussion                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

{interactive_section}
"""

# Automated analysis section for Windows
AUTOMATED_SECTION_WINDOWS = r"""echo Running automated analysis...
claude -p "{initial_command}" --output-format json --mcp-config .mcp.json > .vscodeclaude_analysis.json 2>&1

REM Extract session_id using Python
for /f "delims=" %%i in ('python -c "import json; d=json.load(open('.vscodeclaude_analysis.json')); print(d.get('session_id',''))"') do set SESSION_ID=%%i

if "%SESSION_ID%"=="" (
    echo ERROR: Could not extract session ID from analysis output.
    echo Please run Claude manually.
    pause
    exit /b 1
)

echo Session ID: %SESSION_ID%
"""

# Interactive section for Windows
INTERACTIVE_SECTION_WINDOWS = r"""claude --resume %SESSION_ID% {followup_command}
"""

# Intervention mode for Windows (no automated step)
INTERVENTION_SECTION_WINDOWS = r"""echo.
echo ⚠️  INTERVENTION MODE - Automation may be running elsewhere
echo    Investigate manually. No automated analysis will run.
echo.
claude
"""

# Startup script for Linux (.sh)
STARTUP_SCRIPT_LINUX = r"""#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  {emoji} {stage_name:46}  #{issue_number:6}  ║"
echo "║  {title:58}  ║"
echo "║  {repo:20} | {status:35}  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

{automated_section}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Ready for interactive discussion                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

{interactive_section}
"""

# Automated analysis section for Linux
AUTOMATED_SECTION_LINUX = r"""echo "Running automated analysis..."
claude -p "{initial_command}" --output-format json --mcp-config .mcp.json > .vscodeclaude_analysis.json 2>&1

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
        "window.title": "[#{issue_number} {stage_short}] {title_short} - {repo_name}"
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
        }}
    ]
}}
"""

# Status markdown file template
STATUS_FILE_TEMPLATE = """# VSCodeClaude Session

| Field | Value |
|-------|-------|
| **Issue** | #{issue_number} |
| **Title** | {title} |
| **Status** | {status_emoji} {status_name} |
| **Repo** | {repo} |
| **Branch** | {branch} |
| **Started** | {started_at} |
{intervention_row}

[View Issue on GitHub]({issue_url})
"""

# Intervention warning row for status file
INTERVENTION_ROW = """| **Mode** | ⚠️ INTERVENTION |
"""

# Terminal banner template (for non-script contexts)
BANNER_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  {emoji} {stage_name:46}  #{issue_number:6}  ║
║  {title:58}  ║
║  {repo:20} | {status:35}  ║
╚══════════════════════════════════════════════════════════════╝
"""

# Gitignore entry
GITIGNORE_ENTRY = """
# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.md
.vscodeclaude_analysis.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
"""
