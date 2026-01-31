# Step 16: Update Workspace Setup for New Templates

## LLM Prompt

```
Implement Step 16 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Update create_startup_script() to use new V2 templates with venv and mcp-coder.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/utils/vscodeclaude/workspace.py` | Modify - update create_startup_script() |
| `src/mcp_coder/utils/vscodeclaude/types.py` | Modify - add DEFAULT_PROMPT_TIMEOUT constant |
| `tests/utils/vscodeclaude/test_workspace.py` | Add - tests for V2 script generation |

## WHAT

### types.py - Add Timeout Constant

```python
# Default timeout for mcp-coder prompt calls in startup scripts (seconds)
DEFAULT_PROMPT_TIMEOUT: int = 300  # 5 minutes
```

### workspace.py - Update create_startup_script()

```python
def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    issue_url: str,
    is_intervention: bool,
    timeout: int = DEFAULT_PROMPT_TIMEOUT,
) -> Path:
    """Create platform-specific startup script.
    
    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title for banner
        status: Status label
        repo_name: Repo short name
        issue_url: GitHub issue URL
        is_intervention: If True, use intervention mode (no automation)
        timeout: Timeout for mcp-coder prompt calls (default: 300 seconds)
    
    Returns:
        Path to created script (.bat or .sh)
    
    The V2 templates include:
    - Venv creation/activation
    - mcp-coder prompt for automated analysis
    - mcp-coder prompt for /discuss
    - claude --resume for interactive session
    """
    from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
        AUTOMATED_SECTION_WINDOWS_V2,
        DISCUSSION_SECTION_WINDOWS,
        INTERACTIVE_SECTION_WINDOWS_V2,
        INTERVENTION_SCRIPT_WINDOWS_V2,
        STARTUP_SCRIPT_WINDOWS_V2,
        VENV_SECTION_WINDOWS,
        # Linux templates (for future)
        # AUTOMATED_SECTION_LINUX_V2,
        # etc.
    )
    
    is_windows = platform.system() == "Windows"
    
    # Get commands for this status
    initial_cmd, followup_cmd = HUMAN_ACTION_COMMANDS.get(status, (None, None))
    
    # Get emoji for status
    emoji = STATUS_EMOJI.get(status, "📋")
    
    # Truncate title if too long
    title_display = issue_title[:58] if len(issue_title) > 58 else issue_title
    
    if is_windows:
        if is_intervention:
            # Intervention mode - plain claude, no automation
            script_content = INTERVENTION_SCRIPT_WINDOWS_V2.format(
                emoji=emoji,
                issue_number=issue_number,
                title=title_display,
                repo=repo_name,
                status=status,
                issue_url=issue_url,
                venv_section=VENV_SECTION_WINDOWS,
            )
        else:
            # Normal mode - full automation flow
            automated_section = AUTOMATED_SECTION_WINDOWS_V2.format(
                initial_command=initial_cmd or "/issue_analyse",
                issue_number=issue_number,
                timeout=timeout,
            )
            
            discussion_section = DISCUSSION_SECTION_WINDOWS.format(
                timeout=timeout,
            )
            
            script_content = STARTUP_SCRIPT_WINDOWS_V2.format(
                emoji=emoji,
                issue_number=issue_number,
                title=title_display,
                repo=repo_name,
                status=status,
                issue_url=issue_url,
                venv_section=VENV_SECTION_WINDOWS,
                automated_section=automated_section,
                discussion_section=discussion_section,
                interactive_section=INTERACTIVE_SECTION_WINDOWS_V2,
            )
        
        script_path = folder_path / ".vscodeclaude_start.bat"
    else:
        # Linux - TODO: Implement in Step 17
        # For now, raise NotImplementedError or use legacy templates
        raise NotImplementedError(
            "Linux V2 templates not yet implemented. "
            "See Step 17 for Linux support."
        )
    
    # Write script
    script_path.write_text(script_content, encoding="utf-8")
    
    # Make executable on Linux (when implemented)
    if not is_windows:
        current_mode = script_path.stat().st_mode
        script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    return script_path
```

## HOW

### Integration Points

1. Import new V2 templates from `vscodeclaude_templates.py`
2. Add `timeout` parameter with default from `types.py`
3. Format sections with timeout value
4. Combine sections into final script

### Backward Compatibility

- The function signature changes (new `timeout` parameter with default)
- All existing callers will continue to work due to default value
- Linux temporarily raises NotImplementedError (to be fixed in Step 17)

### Callers to Update

1. `prepare_and_launch_session()` in `orchestrator.py` - passes timeout
2. `regenerate_session_files()` in `orchestrator.py` - passes timeout

```python
# In orchestrator.py
script_path = create_startup_script(
    folder_path=folder_path,
    issue_number=issue_number,
    issue_title=issue_title,
    status=status,
    repo_name=repo_short_name,
    issue_url=issue_url,
    is_intervention=is_intervention,
    timeout=DEFAULT_PROMPT_TIMEOUT,  # Can be made configurable later
)
```

## ALGORITHM

```
1. Import V2 templates
2. Determine platform (Windows/Linux)
3. Get initial_command from HUMAN_ACTION_COMMANDS
4. If intervention: format INTERVENTION_SCRIPT with venv_section
5. Else: format each section with appropriate variables
6. Combine sections into STARTUP_SCRIPT
7. Write script to file
8. Return script path
```

## DATA

### Function Signature Change

```python
# Before
def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    issue_url: str,
    is_intervention: bool,
) -> Path:

# After
def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    issue_url: str,
    is_intervention: bool,
    timeout: int = DEFAULT_PROMPT_TIMEOUT,  # New parameter
) -> Path:
```

### Test Coverage

```python
# test_workspace.py

class TestCreateStartupScriptV2:
    """Test V2 startup script generation."""
    
    def test_creates_script_with_venv_section(self, tmp_path, monkeypatch):
        """Generated script includes venv setup."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )
        
        content = script_path.read_text()
        assert "uv venv" in content
        assert "activate.bat" in content
    
    def test_creates_script_with_mcp_coder_prompt(self, tmp_path, monkeypatch):
        """Generated script uses mcp-coder prompt."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )
        
        content = script_path.read_text()
        assert "mcp-coder prompt" in content
        assert "--output-format session-id" in content
        assert "--session-id %SESSION_ID%" in content
    
    def test_creates_script_with_claude_resume(self, tmp_path, monkeypatch):
        """Generated script ends with claude --resume."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )
        
        content = script_path.read_text()
        assert "claude --resume %SESSION_ID%" in content
    
    def test_uses_custom_timeout(self, tmp_path, monkeypatch):
        """Timeout parameter is used in script."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
            timeout=600,  # 10 minutes
        )
        
        content = script_path.read_text()
        assert "--timeout 600" in content
    
    def test_intervention_mode_no_automation(self, tmp_path, monkeypatch):
        """Intervention mode skips automation."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=True,
        )
        
        content = script_path.read_text()
        assert "INTERVENTION MODE" in content
        assert "mcp-coder prompt" not in content
        assert "uv venv" in content  # Venv still activated
    
    def test_linux_raises_not_implemented(self, tmp_path, monkeypatch):
        """Linux raises NotImplementedError until Step 17."""
        monkeypatch.setattr("platform.system", lambda: "Linux")
        
        with pytest.raises(NotImplementedError):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=123,
                issue_title="Test issue",
                status="status-07:code-review",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/123",
                is_intervention=False,
            )
```

## Verification

```bash
# Run workspace tests
pytest tests/utils/vscodeclaude/test_workspace.py::TestCreateStartupScriptV2 -v

# Type check
mypy src/mcp_coder/utils/vscodeclaude/workspace.py

# Integration test (manual)
# 1. Create a vscodeclaude session
# 2. Verify .vscodeclaude_start.bat contains expected content
# 3. Run the script manually to test venv activation and mcp-coder
```
