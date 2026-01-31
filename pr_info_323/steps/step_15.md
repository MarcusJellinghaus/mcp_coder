# Step 15: Update VSCodeClaude Templates for Venv & mcp-coder (Windows)

## LLM Prompt

```
Implement Step 15 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Update Windows startup script templates to activate venv and use mcp-coder prompt.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py` | Modify - update Windows templates |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | Add - tests for new templates |

## WHAT

### vscodeclaude_templates.py - New Windows Templates

```python
# Venv setup section for Windows
VENV_SECTION_WINDOWS = r"""echo Checking Python environment...
if not exist .venv\Scripts\activate.bat (
    echo Creating virtual environment...
    uv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    uv sync --extra types
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    set VENV_CREATED=1
) else (
    set VENV_CREATED=0
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)
"""

# Automated analysis section for Windows (using mcp-coder prompt)
AUTOMATED_SECTION_WINDOWS_V2 = r"""echo.
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

# Interactive section for Windows (raw claude CLI)
INTERACTIVE_SECTION_WINDOWS_V2 = r"""echo.
echo === Step 3: Interactive Session ===
echo You can now interact with Claude directly.
echo The conversation context from previous steps is preserved.
echo.

claude --resume %SESSION_ID%
"""

# Main startup script for Windows (V2 - with venv and mcp-coder)
STARTUP_SCRIPT_WINDOWS_V2 = r"""@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

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

# Intervention mode for Windows (V2 - with venv activation)
INTERVENTION_SCRIPT_WINDOWS_V2 = r"""@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

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
```

## HOW

### Template Selection Logic

The `create_startup_script()` function will need to:
1. Detect if using new V2 templates (based on a flag or config)
2. Build the script by combining sections:
   - VENV_SECTION_WINDOWS (always)
   - AUTOMATED_SECTION_WINDOWS_V2 (if not intervention)
   - DISCUSSION_SECTION_WINDOWS (if not intervention)
   - INTERACTIVE_SECTION_WINDOWS_V2 (if not intervention)
   - Or INTERVENTION_SCRIPT_WINDOWS_V2 (if intervention)

### Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{emoji}` | Status emoji | 📝 |
| `{issue_number}` | GitHub issue number | 123 |
| `{title}` | Issue title (truncated) | Add feature X |
| `{repo}` | Repository short name | mcp-coder |
| `{status}` | Status label | status-07:code-review |
| `{issue_url}` | GitHub issue URL | https://github.com/... |
| `{initial_command}` | First slash command | /issue_analyse |
| `{timeout}` | Timeout in seconds | 300 |

## ALGORITHM

```
1. Define VENV_SECTION_WINDOWS template
2. Define AUTOMATED_SECTION_WINDOWS_V2 with mcp-coder prompt
3. Define DISCUSSION_SECTION_WINDOWS with mcp-coder prompt --session-id
4. Define INTERACTIVE_SECTION_WINDOWS_V2 with claude --resume
5. Define STARTUP_SCRIPT_WINDOWS_V2 combining all sections
6. Define INTERVENTION_SCRIPT_WINDOWS_V2 for intervention mode
```

## DATA

### Script Flow (Normal Mode)

```
1. Display banner (issue info)
2. Check/create venv, activate
3. Run mcp-coder prompt with initial command → capture SESSION_ID
4. If failed: show error, pause, exit
5. Run mcp-coder prompt "/discuss" with session-id
6. Run claude --resume for interactive session
```

### Script Flow (Intervention Mode)

```
1. Display banner (issue info)
2. Check/create venv, activate
3. Display intervention warning
4. Run plain claude (no automation)
```

### Test Coverage

```python
# test_vscodeclaude_cli.py

class TestTemplatesV2:
    """Test V2 template strings with venv and mcp-coder."""
    
    def test_venv_section_creates_venv_if_missing(self):
        """VENV_SECTION_WINDOWS creates venv when not present."""
        assert "if not exist .venv" in VENV_SECTION_WINDOWS
        assert "uv venv" in VENV_SECTION_WINDOWS
        assert "uv sync" in VENV_SECTION_WINDOWS
    
    def test_venv_section_activates_existing_venv(self):
        """VENV_SECTION_WINDOWS activates existing venv."""
        assert "call .venv\\Scripts\\activate.bat" in VENV_SECTION_WINDOWS
    
    def test_automated_section_uses_mcp_coder_prompt(self):
        """AUTOMATED_SECTION_WINDOWS_V2 uses mcp-coder prompt."""
        assert "mcp-coder prompt" in AUTOMATED_SECTION_WINDOWS_V2
        assert "--output-format session-id" in AUTOMATED_SECTION_WINDOWS_V2
        assert "--mcp-config .mcp.json" in AUTOMATED_SECTION_WINDOWS_V2
    
    def test_automated_section_captures_session_id(self):
        """AUTOMATED_SECTION_WINDOWS_V2 captures SESSION_ID."""
        assert "set SESSION_ID=" in AUTOMATED_SECTION_WINDOWS_V2
        assert 'if "%SESSION_ID%"==""' in AUTOMATED_SECTION_WINDOWS_V2
    
    def test_discussion_section_uses_session_id(self):
        """DISCUSSION_SECTION_WINDOWS passes session-id."""
        assert "mcp-coder prompt" in DISCUSSION_SECTION_WINDOWS
        assert "--session-id %SESSION_ID%" in DISCUSSION_SECTION_WINDOWS
    
    def test_interactive_section_uses_claude_resume(self):
        """INTERACTIVE_SECTION_WINDOWS_V2 uses claude --resume."""
        assert "claude --resume %SESSION_ID%" in INTERACTIVE_SECTION_WINDOWS_V2
    
    def test_startup_script_has_all_sections(self):
        """STARTUP_SCRIPT_WINDOWS_V2 includes all section placeholders."""
        assert "{venv_section}" in STARTUP_SCRIPT_WINDOWS_V2
        assert "{automated_section}" in STARTUP_SCRIPT_WINDOWS_V2
        assert "{discussion_section}" in STARTUP_SCRIPT_WINDOWS_V2
        assert "{interactive_section}" in STARTUP_SCRIPT_WINDOWS_V2
    
    def test_intervention_script_has_warning(self):
        """INTERVENTION_SCRIPT_WINDOWS_V2 shows intervention warning."""
        assert "INTERVENTION MODE" in INTERVENTION_SCRIPT_WINDOWS_V2
        assert "{venv_section}" in INTERVENTION_SCRIPT_WINDOWS_V2
        assert "claude" in INTERVENTION_SCRIPT_WINDOWS_V2
    
    def test_templates_include_timeout_placeholder(self):
        """Templates include {timeout} placeholder."""
        assert "{timeout}" in AUTOMATED_SECTION_WINDOWS_V2
        assert "{timeout}" in DISCUSSION_SECTION_WINDOWS
```

## Verification

```bash
# Run template tests
pytest tests/cli/commands/coordinator/test_vscodeclaude_cli.py::TestTemplatesV2 -v

# Type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py
```
