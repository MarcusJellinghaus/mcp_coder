# Step 2: Template Strings

## LLM Prompt

```
Implement Step 2 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Create template strings for startup scripts, workspace files, etc.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py` | Create |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add template tests |

## WHAT

### vscodeclaude_templates.py - All Templates

```python
"""Template strings for VSCode Claude session files."""

# Startup script for Windows (.bat)
STARTUP_SCRIPT_WINDOWS = r'''@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  {emoji} {stage_name:40}  #{issue_number:6}  ║
echo ║  {title:56}  ║
echo ║  {repo} ^| {status:32}  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

{automated_section}

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  Ready for interactive discussion                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

{interactive_section}
'''

# Automated analysis section for Windows
AUTOMATED_SECTION_WINDOWS = r'''echo Running automated analysis...
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
'''

# Interactive section for Windows
INTERACTIVE_SECTION_WINDOWS = r'''claude --resume %SESSION_ID% {followup_command}
'''

# Intervention mode for Windows (no automated step)
INTERVENTION_SECTION_WINDOWS = r'''echo.
echo ⚠️  INTERVENTION MODE - Automation may be running elsewhere
echo    Investigate manually. No automated analysis will run.
echo.
claude
'''

# Startup script for Linux (.sh)
STARTUP_SCRIPT_LINUX = r'''#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  {emoji} {stage_name:40}  #{issue_number:6}  ║"
echo "║  {title:56}  ║"
echo "║  {repo} | {status:32}  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

{automated_section}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Ready for interactive discussion                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

{interactive_section}
'''

# Automated analysis section for Linux
AUTOMATED_SECTION_LINUX = r'''echo "Running automated analysis..."
claude -p "{initial_command}" --output-format json --mcp-config .mcp.json > .vscodeclaude_analysis.json 2>&1

SESSION_ID=$(python3 -c "import json; d=json.load(open('.vscodeclaude_analysis.json')); print(d.get('session_id',''))")

if [ -z "$SESSION_ID" ]; then
    echo "ERROR: Could not extract session ID from analysis output."
    echo "Please run Claude manually."
    exit 1
fi

echo "Session ID: $SESSION_ID"
'''

# Interactive section for Linux
INTERACTIVE_SECTION_LINUX = r'''claude --resume "$SESSION_ID" {followup_command}
'''

# Intervention mode for Linux
INTERVENTION_SECTION_LINUX = r'''echo ""
echo "⚠️  INTERVENTION MODE - Automation may be running elsewhere"
echo "   Investigate manually. No automated analysis will run."
echo ""
claude
'''

# VSCode workspace file template
WORKSPACE_FILE_TEMPLATE = '''{
    "folders": [
        {
            "path": "{folder_path}"
        }
    ],
    "settings": {
        "window.title": "[#{issue_number} {stage_short}] {title_short} - {repo_name}"
    }
}
'''

# VSCode tasks.json template
TASKS_JSON_TEMPLATE = '''{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "VSCodeClaude Startup",
            "type": "shell",
            "command": "{script_path}",
            "presentation": {
                "reveal": "always",
                "panel": "new",
                "focus": true
            },
            "runOptions": {
                "runOn": "folderOpen"
            },
            "problemMatcher": []
        }
    ]
}
'''

# Status markdown file template
STATUS_FILE_TEMPLATE = '''# VSCodeClaude Session

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
'''

# Intervention warning row for status file
INTERVENTION_ROW = '''| **Mode** | ⚠️ INTERVENTION |
'''

# Terminal banner template (for non-script contexts)
BANNER_TEMPLATE = '''
╔══════════════════════════════════════════════════════════════╗
║  {emoji} {stage_name:40}  #{issue_number:6}  ║
║  {title:56}  ║
║  {repo} | {status:32}  ║
╚══════════════════════════════════════════════════════════════╝
'''

# Gitignore entry
GITIGNORE_ENTRY = '''
# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.md
.vscodeclaude_analysis.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
'''
```

## HOW

### Integration Points

1. Templates imported in `vscodeclaude.py` for file generation
2. String `.format()` used with named placeholders
3. Platform detection determines which script template to use

### Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{emoji}` | Status emoji | 🔍 |
| `{stage_name}` | Human-readable stage | CODE REVIEW |
| `{issue_number}` | GitHub issue number | 123 |
| `{title}` | Issue title (truncated) | Add coordinator vscodeclaude |
| `{repo}` | Repository short name | mcp-coder |
| `{status}` | Full status label | status-07:code-review |
| `{initial_command}` | First slash command | /implementation_review |
| `{followup_command}` | Interactive command | /discuss |
| `{folder_path}` | Relative path to folder | ./mcp-coder_123 |
| `{script_path}` | Path to startup script | .vscodeclaude_start.bat |

## ALGORITHM

```
N/A - This step only defines template strings, no logic.
```

## DATA

### Test Coverage

```python
# test_vscodeclaude.py

class TestTemplates:
    """Test template strings."""
    
    def test_startup_script_windows_has_placeholders(self):
        """Windows script has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            STARTUP_SCRIPT_WINDOWS
        )
        assert "{emoji}" in STARTUP_SCRIPT_WINDOWS
        assert "{issue_number}" in STARTUP_SCRIPT_WINDOWS
        assert "{automated_section}" in STARTUP_SCRIPT_WINDOWS
    
    def test_startup_script_linux_has_placeholders(self):
        """Linux script has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            STARTUP_SCRIPT_LINUX
        )
        assert "{emoji}" in STARTUP_SCRIPT_LINUX
        assert "{issue_number}" in STARTUP_SCRIPT_LINUX
    
    def test_workspace_file_is_valid_json_template(self):
        """Workspace template produces valid JSON when formatted."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            WORKSPACE_FILE_TEMPLATE
        )
        import json
        formatted = WORKSPACE_FILE_TEMPLATE.format(
            folder_path="./test",
            issue_number=123,
            stage_short="review",
            title_short="Test title",
            repo_name="test-repo"
        )
        parsed = json.loads(formatted)
        assert "folders" in parsed
        assert "settings" in parsed
    
    def test_tasks_json_is_valid_json_template(self):
        """Tasks template produces valid JSON when formatted."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            TASKS_JSON_TEMPLATE
        )
        import json
        formatted = TASKS_JSON_TEMPLATE.format(script_path="test.bat")
        parsed = json.loads(formatted)
        assert parsed["tasks"][0]["runOptions"]["runOn"] == "folderOpen"
    
    def test_gitignore_entry_has_session_files(self):
        """Gitignore entry includes all generated files."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            GITIGNORE_ENTRY
        )
        assert ".vscodeclaude_status.md" in GITIGNORE_ENTRY
        assert ".vscodeclaude_analysis.json" in GITIGNORE_ENTRY
```

## Verification

```bash
# Run template tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestTemplates -v

# Type check templates file
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py
```
