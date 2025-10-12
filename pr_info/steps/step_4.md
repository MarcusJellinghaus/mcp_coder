# Step 4: CLI Integration & Batch Launcher

## LLM Prompt
```
Implement Step 4 from pr_info/steps/summary.md: Create Windows batch launcher for issue_stats.py workflow.

Tasks:
1. Create issue_stats.bat following the pattern from define_labels.bat
2. Test the batch launcher with various argument combinations
3. Verify UTF-8 encoding setup works correctly
4. Run final code quality checks on entire implementation
5. Manual testing with real GitHub repository

Use ONLY MCP filesystem tools for all file operations (mcp__filesystem__*).
Reference workflows/define_labels.bat for exact patterns.
```

## WHERE: File Paths

### Files to CREATE
```
workflows/issue_stats.bat                   # Windows batch launcher
```

### No Python Files to Modify
All Python code completed in Step 3.

## WHAT: Batch Launcher Script

### issue_stats.bat (Complete Implementation)
```batch
@echo off
REM issue_stats.bat - Windows Batch Wrapper for Issue Statistics Workflow
REM
REM Usage:
REM   issue_stats.bat [--project-dir <path>] [--log-level <level>] [--filter <filter>] [--details]
REM
REM Parameters:
REM   --project-dir   Project directory path (default: current directory)
REM   --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
REM   --filter        Filter by category: all, human, bot (default: all)
REM   --details       Show individual issues with clickable links
REM
REM Examples:
REM   issue_stats.bat
REM   issue_stats.bat --filter human
REM   issue_stats.bat --details
REM   issue_stats.bat --project-dir "C:\my\project" --log-level DEBUG --filter bot --details
REM
REM This wrapper sets up the Python environment and executes the issue statistics workflow.

REM Set console to UTF-8 codepage to handle Unicode characters
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding for all I/O operations
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

python workflows\issue_stats.py %*

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
```

## HOW: Integration Points

### Script Location
- Place in `workflows/` directory (same as other workflow scripts)
- Must be at same level as `issue_stats.py`

### UTF-8 Encoding Setup
```batch
chcp 65001                           # UTF-8 code page
set PYTHONIOENCODING=utf-8           # Python I/O encoding
set PYTHONLEGACYWINDOWSFSENCODING=utf-8  # Legacy file system encoding
set PYTHONUTF8=1                     # Force UTF-8 mode
```

### PYTHONPATH Setup
```batch
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%
```
- `%~dp0` = batch file directory (workflows/)
- `..\src` = go up one level, then to src/
- Ensures Python can import `mcp_coder` modules

### Argument Pass-through
```batch
python workflows\issue_stats.py %*
```
- `%*` passes all command-line arguments unchanged
- Supports all flags: --project-dir, --log-level, --filter, --details

## ALGORITHM: Batch Script Flow

```
SET UTF-8 encodings (chcp, PYTHONIOENCODING, etc.)
SET PYTHONPATH to include src directory
EXECUTE python workflows\issue_stats.py with all arguments
IF ERRORLEVEL not 0:
    PRINT error message
    EXIT with error code
ELSE:
    PRINT success message
```

## DATA: Test Scenarios

### Manual Testing Commands
```batch
# Basic usage (default: all issues, summary view)
workflows\issue_stats.bat

# Filter by human action required
workflows\issue_stats.bat --filter human

# Filter by bot (both pickup and busy)
workflows\issue_stats.bat --filter bot

# Show details with clickable links
workflows\issue_stats.bat --details

# Debug mode with details
workflows\issue_stats.bat --log-level DEBUG --details

# Specific project directory
workflows\issue_stats.bat --project-dir "C:\path\to\repo"

# All options combined
workflows\issue_stats.bat --project-dir . --log-level INFO --filter human --details
```

### Expected Behaviors
1. **UTF-8 Support**: Handles Unicode characters in issue titles
2. **Error Propagation**: Python errors cause batch script to exit with non-zero
3. **Argument Forwarding**: All flags passed correctly to Python
4. **Path Resolution**: PYTHONPATH allows imports from src/mcp_coder
5. **Success Message**: Shows on successful completion

## Implementation Checklist
- [ ] Create issue_stats.bat in workflows/ directory
- [ ] Copy UTF-8 encoding setup from define_labels.bat
- [ ] Copy PYTHONPATH setup from define_labels.bat
- [ ] Update script name in comments and calls
- [ ] Test: Run without arguments (should work with current directory)
- [ ] Test: Run with --filter human
- [ ] Test: Run with --details flag
- [ ] Test: Run with invalid arguments (should fail gracefully)
- [ ] Test: Run from different directory (verify PYTHONPATH works)
- [ ] Verify success/error messages display correctly

## Quality Checks - Final Verification

### Run All Code Quality Checks
```python
# Fast unit tests (no integration):
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Type checking (entire project):
mcp__code-checker__run_mypy_check()

# Code quality (entire project):
mcp__code-checker__run_pylint_check()

# Optional: Run with GitHub integration tests (slow, requires auth):
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto"],
    markers=["github_integration"]
)
```

### Verify All Files Created/Modified
```
✓ workflows/config/labels.json
✓ workflows/issue_stats.py
✓ workflows/issue_stats.bat
✓ tests/workflows/config/test_labels.json
✓ tests/workflows/test_issue_stats.py
✓ src/mcp_coder/utils/github_operations/issue_manager.py (list_issues added)
✓ tests/utils/github_operations/test_issue_manager.py (tests added)
```

## Manual Testing Procedure

### 1. Test with Real Repository
```bash
cd C:\path\to\mcp_coder
workflows\issue_stats.bat
```

**Verify:**
- Statistics display correctly grouped by category
- Zero-count statuses are shown
- Validation errors section appears (if any)
- Total count is accurate

### 2. Test Filter Modes
```bash
workflows\issue_stats.bat --filter human
workflows\issue_stats.bat --filter bot
```

**Verify:**
- Only requested categories shown
- Error section always visible
- Total counts adjust correctly

### 3. Test Details Mode
```bash
workflows\issue_stats.bat --details
```

**Verify:**
- Individual issues listed under each status
- Clickable links work in terminal (click to open browser)
- Long titles truncated at 80 characters with "..."
- Issue numbers and titles display correctly

### 4. Test Error Handling
```bash
workflows\issue_stats.bat --project-dir C:\nonexistent\path
```

**Verify:**
- Error message displayed
- Script exits with non-zero code
- No stack traces (clean error messages)

### 5. Test Logging Levels
```bash
workflows\issue_stats.bat --log-level DEBUG
workflows\issue_stats.bat --log-level WARNING
```

**Verify:**
- Appropriate log messages shown
- DEBUG shows detailed progress
- WARNING shows only important messages

## Expected Final Output Example

### Summary View (Default)
```
INFO:root:Starting issue statistics workflow...
INFO:root:Project directory: C:\Users\Marcus\Documents\GitHub\AutoRunner\Code\mcp_coder
INFO:root:Repository: mcp_coder
INFO:root:Fetching issues from GitHub...
INFO:root:Found 25 issues

=== Human Action Required ===
  status-01:created           3 issues
  status-04:plan-review       1 issue
  status-07:code-review       0 issues
  status-10:pr-created        0 issues

=== Bot Should Pickup ===
  status-02:awaiting-planning 2 issues
  status-05:plan-ready        1 issue
  status-08:ready-pr          0 issues

=== Bot Busy ===
  status-03:planning          0 issues
  status-06:implementing      1 issue
  status-09:pr-creating       0 issues

=== Validation Errors ===
  No status label: 2 issues
  Multiple status labels: 1 issue

Total: 25 issues (22 valid, 3 errors)

INFO:root:Issue statistics workflow completed successfully
Workflow completed successfully!
```

### Details View (--details flag)
```
=== Human Action Required ===
  status-01:created           3 issues
    - #109: task_list_statistics (https://github.com/MarcusJellinghaus/mcp_coder/issues/109)
    - #108: Implement user authentication system with OAuth2 support and multi-factor... (https://github.com/...)
    - #107: Fix critical bug in payment processing (https://github.com/MarcusJellinghaus/mcp_coder/issues/107)
  
  status-04:plan-review       1 issue
    - #95: Refactor database schema for better performance (https://github.com/...)

...
```

## Notes
- Batch file must use Windows line endings (CRLF)
- UTF-8 encoding is critical for Unicode issue titles
- PYTHONPATH setup allows imports from src/ directory
- Error propagation ensures CI/CD failures are detected
- Success message provides clear feedback to user
- Follow exact same pattern as define_labels.bat for consistency
