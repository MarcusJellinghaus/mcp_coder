# Step 5: Create Batch File and Final Integration

## Goal
Create Windows batch file wrapper and perform final integration testing to ensure the complete workflow operates correctly.

## Context
This is the final step that makes the script easily accessible on Windows and verifies everything works together properly.

## WHERE
**Files**: 
- `workflows/validate_labels.bat` (new file)
- Complete integration of all components

## WHAT

### Create Batch File
**File**: `workflows/validate_labels.bat`

```batch
@echo off
REM Validate GitHub issue labels workflow

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Navigate to project root (one level up from workflows)
cd /d "%SCRIPT_DIR%.."

REM Run the Python script with all arguments forwarded
python workflows\validate_labels.py %*
```

### Integration Testing Tasks
1. **Manual end-to-end test** - Run script on actual repository
2. **Test all command-line options** - Verify each flag works
3. **Test exit codes** - Verify correct codes in different scenarios
4. **Test dry-run mode** - Ensure no changes are made
5. **Test error handling** - Verify graceful failures

## HOW

### Batch File Integration
- **Location**: Place in `workflows/` directory
- **Pattern**: Copy structure from `define_labels.bat` and `issue_stats.bat`
- **Argument forwarding**: Use `%*` to forward all args to Python script

### Testing Strategy
- **Unit tests**: Already created in previous steps
- **Integration tests**: Manual testing with real GitHub API
- **Edge cases**: Test with various repository states

## ALGORITHM

### Integration Test Scenarios
```
1. Test with no issues:
   - Verify graceful handling of empty issue list
   
2. Test with issues needing initialization:
   - Run in dry-run mode first
   - Verify correct issues identified
   - Run without dry-run
   - Verify labels added correctly

3. Test with multiple status labels:
   - Create test issue with 2 status labels
   - Verify ERROR detection and reporting
   - Manually fix issue

4. Test with stale bot process:
   - Find or create issue stuck in bot_busy
   - Verify WARNING detection with correct time
   
5. Test with ignore labels:
   - Create issue with "Overview" label
   - Verify it's skipped correctly

6. Test exit codes:
   - echo %ERRORLEVEL% after each scenario
   - Verify: 0 (success), 1 (errors), 2 (warnings)
```

## DATA

### Test Checklist
```
☐ Batch file runs without errors
☐ --help flag works
☐ --log-level flag works (test DEBUG, INFO)
☐ --project-dir flag works with custom path
☐ --dry-run flag prevents changes
☐ Script detects issues without labels
☐ Script detects issues with multiple labels
☐ Script detects stale bot processes
☐ Script respects ignore_labels
☐ Exit code 0 on success
☐ Exit code 1 on errors
☐ Exit code 2 on warnings only
☐ Output format matches specification
```

## Tests to Write

**File**: `tests/workflows/test_validate_labels.py`

Add final integration-level tests:
```python
def test_script_runs_with_help_flag():
    """Test that script shows help without errors"""
    # Run subprocess with --help
    
def test_batch_file_exists():
    """Test that batch file is created and executable"""
    batch_path = Path("workflows/validate_labels.bat")
    assert batch_path.exists()
    
def test_full_workflow_integration(tmp_path, mock_github_api):
    """Test complete workflow from start to finish"""
    # Full end-to-end integration test with mocked GitHub
```

## LLM Prompt for Implementation

```
Please implement Step 5 from pr_info/steps/step_5.md

Review the summary at pr_info/steps/summary.md for context.

Key requirements:
- Create workflows/validate_labels.bat following existing pattern
- Perform manual integration testing with real GitHub API
- Test all command-line flags and options
- Verify exit codes work correctly in all scenarios
- Test dry-run mode thoroughly
- Add final integration tests
- Update any documentation if needed

Testing checklist:
1. Run: workflows\validate_labels.bat --help
2. Run: workflows\validate_labels.bat --dry-run
3. Run: workflows\validate_labels.bat --log-level DEBUG
4. Verify exit codes with: echo %ERRORLEVEL%
5. Test on repository with various issue states

After implementation:
1. Run complete quality checks: pylint, pytest, mypy
2. Fix any remaining issues
3. Run the script on the actual repository to verify it works
4. Document any findings or issues
5. Provide commit message
```

## Definition of Done
- [ ] validate_labels.bat created and working
- [ ] Batch file runs Python script correctly
- [ ] All command-line flags tested and working
- [ ] Exit codes verified (0, 1, 2)
- [ ] Dry-run mode verified (no API calls made)
- [ ] Manual integration testing completed
- [ ] All edge cases tested
- [ ] Complete test suite passing
- [ ] All quality checks pass (pylint, pytest, mypy)
- [ ] Script ready for production use

## Final Verification

Run through complete workflow:
```bash
# 1. Show help
workflows\validate_labels.bat --help

# 2. Dry-run to preview
workflows\validate_labels.bat --dry-run

# 3. Run with debug logging
workflows\validate_labels.bat --log-level DEBUG

# 4. Run normally
workflows\validate_labels.bat

# 5. Check exit code
echo Exit code: %ERRORLEVEL%
```

Expected results:
- Clear help message shown
- Dry-run shows changes without applying them
- Debug output shows detailed processing
- Normal run completes successfully
- Exit code matches validation results (0/1/2)
