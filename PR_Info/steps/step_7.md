# Step 7: Update Package Exports and Installation

## Objective
Update package exports and verify CLI installation works correctly with the reinstall script.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and all previous steps, implement Step 7: Update package exports and verify installation.

Requirements:
- Update src/mcp_coder/__init__.py to export CLI functions
- Verify pyproject.toml entry point configuration
- Test tools/reinstall.bat handles CLI entry point correctly
- Ensure mcp-coder command is available after installation
- Follow existing export patterns in __init__.py

Focus on proper package configuration and installation verification.
```

## WHERE (File Structure)
```
src/mcp_coder/__init__.py (updated)
pyproject.toml (verify configuration)
tools/reinstall.bat (verify and update if needed)
```

## WHAT (Functions & Updates)

### `src/mcp_coder/__init__.py` (additions)
```python
# Add CLI exports to existing imports
from .cli.main import main as cli_main
from .cli.commands.help import execute_help
from .cli.commands.commit import execute_commit_auto, execute_commit_clipboard

# Update __all__ list
__all__ = [
    # ... existing exports ...
    # CLI exports
    "cli_main",
    "execute_help", 
    "execute_commit_auto",
    "execute_commit_clipboard",
]
```

### pyproject.toml (verify)
```toml
[project.scripts]
mcp-coder = "mcp_coder.cli.main:main"
```

### tools/reinstall.bat (potential updates)
```batch
echo [4/4] Verifying CLI installation...
mcp-coder help
if %ERRORLEVEL% NEQ 0 (
    echo ✗ CLI installation verification failed!
    pause
    exit /b 1
)
echo ✓ CLI installation verified successfully
```

## HOW (Integration Points)

### Package Structure Verification
```python
# Ensure all CLI modules are properly importable
from mcp_coder.cli.main import main
from mcp_coder.cli.commands.help import execute_help
from mcp_coder.cli.commands.commit import execute_commit_auto, execute_commit_clipboard
```

### Entry Point Testing
```python
# Programmatic testing of entry point
import subprocess
result = subprocess.run(["mcp-coder", "help"], capture_output=True, text=True)
assert result.returncode == 0
```

## ALGORITHM (Verification Logic)
```
1. Update __init__.py with CLI exports following existing patterns
2. Verify pyproject.toml has correct entry point configuration
3. Update reinstall.bat to test CLI installation
4. Run installation test to verify mcp-coder command works
5. Test all CLI commands are accessible and functional
```

## DATA (Export Structure)

### CLI Module Exports
```python
# Main CLI entry point
cli_main: function  # Main CLI entry point

# Command executors
execute_help: function  # Help command executor
execute_commit_auto: function  # Auto commit executor
execute_commit_clipboard: function  # Clipboard commit executor
```

### Entry Point Configuration
```toml
[project.scripts]
mcp-coder = "mcp_coder.cli.main:main"  # Maps CLI command to main function
```

## Tests Required

### `tests/test_package_exports.py`
```python
def test_cli_imports_from_package():
    """Test that CLI functions can be imported from main package."""

def test_cli_main_function_exists():
    """Test that cli_main function is properly exported."""

def test_all_cli_commands_exported():
    """Test that all CLI command functions are exported."""
```

### `tests/cli/test_installation.py`
```python
def test_entry_point_configuration():
    """Test that entry point is correctly configured in pyproject.toml."""

def test_cli_command_available():
    """Test that mcp-coder command is available after installation."""

def test_reinstall_script_includes_cli_verification():
    """Test that reinstall script verifies CLI installation."""
```

## Installation Verification Steps

### Manual Testing Checklist
1. Run `tools/reinstall.bat`
2. Verify no errors during installation
3. Test `mcp-coder help` shows help
4. Test `mcp-coder commit auto` (in git repo)
5. Test `mcp-coder commit clipboard` (in git repo)
6. Verify all commands show appropriate errors outside git repos

### Automated Testing
```python
def test_full_installation_workflow():
    """Test complete installation and CLI functionality."""
    # Run reinstall script
    # Test CLI commands
    # Verify expected outputs and exit codes
```

## Reinstall Script Updates

### Current reinstall.bat Analysis
- Already has 4-step process
- Tests package import verification
- Could add CLI verification step

### Proposed Addition
```batch
echo [5/5] Verifying CLI installation...
echo Testing CLI help command...
mcp-coder help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ✗ CLI command not available!
    echo Make sure the package was installed correctly.
    pause
    exit /b 1
)
echo ✓ CLI installation verified successfully
```

## Error Scenarios to Handle

### Import Errors
```python
try:
    from .cli.main import main as cli_main
except ImportError as e:
    logger.warning(f"CLI module not available: {e}")
    # Handle gracefully - CLI might not be needed for all use cases
```

### Entry Point Issues
- Command not found after installation
- Permission issues on different platforms
- Path configuration problems

## Platform Considerations

### Windows
- Entry point should work in Command Prompt and PowerShell
- Verify .exe generation in Scripts directory

### Unix/Linux/macOS
- Entry point should work in bash/zsh
- Verify executable permissions

## Acceptance Criteria
1. ✅ CLI functions properly exported from main package
2. ✅ pyproject.toml entry point correctly configured
3. ✅ reinstall.bat includes CLI verification
4. ✅ `mcp-coder` command available after `pip install -e .`
5. ✅ All CLI commands work through entry point
6. ✅ Package imports work both programmatically and via CLI
7. ✅ Installation verification tests pass
8. ✅ Cross-platform compatibility verified
