r"""Template strings for VSCode Claude session files.

The startup script is a **thin launcher** (one per platform) that bootstraps
into Python: `python -m mcp_coder.workflows.vscodeclaude.session_setup <CWD>`.
All shell orchestration that used to live here — env assembly, `install.py`
provisioning, session-ID capture, step chaining, the interactive `claude`
handoff and the banner — now lives in `session_setup.py`, driven by a typed
session-spec JSON (`.vscodeclaude_session.json`) written at launch time.

This module therefore only holds:

- the thin launchers (`LAUNCHER_WINDOWS` / `LAUNCHER_POSIX`),
- run-time banner / warning text consumed by `session_setup.render_banner`
  (`BANNER_TEMPLATE`, `INTERVENTION_WARNING`),
- the static VSCode workspace / tasks files and the status-file banner
  (`WORKSPACE_FILE_TEMPLATE`, `TASKS_JSON_TEMPLATE`, `STATUS_FILE_TEMPLATE`,
  `INTERVENTION_LINE`),
- and the `GITIGNORE_ENTRY` for the auto-generated session files.

TWO-ENVIRONMENT SETUP:
======================

The system still uses two separate Python virtual environments for isolation:

1. MCP-CODER ENVIRONMENT: the coordinator's `.venv` (contains the mcp-coder
   executable). Its Python is what the launcher invokes.
2. PROJECT ENVIRONMENT: the issue-specific workspace `.venv` (project
   dependencies), provisioned by `session_setup` via `tools/install.py`.

"""

# Terminal banner template (rendered by session_setup.render_banner).
BANNER_TEMPLATE = """
==========================================================================
{emoji} Issue #{issue_number} - {title}
Repo:   {repo}
Status: {status}
URL:    {issue_url}
==========================================================================
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

# Intervention line for status file (includes newline for proper formatting)
INTERVENTION_LINE = """Mode:    ⚠️ INTERVENTION
"""

# Gitignore entry
GITIGNORE_ENTRY = """
# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.txt
.vscodeclaude_analysis.json
.vscodeclaude_session.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
"""
