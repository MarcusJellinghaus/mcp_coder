# Step 5: Integration Testing Guide

## Manual Integration Testing with Real GitHub API

This document provides the commands and expected results for manual integration testing of the `validate_labels.py` script.

---

## Test 1: Help Flag

**Command:**
```cmd
workflows\validate_labels.bat --help
```

**Expected Output:**
- Help message showing usage information
- Lists all available options (--project-dir, --log-level, --dry-run)
- Exit code: 0

**Verification:**
```cmd
echo %ERRORLEVEL%
```
Should output: `0`

---

## Test 2: Dry-Run Mode

**Command:**
```cmd
workflows\validate_labels.bat --dry-run
```

**Expected Behavior:**
- Connects to GitHub API
- Fetches open issues
- Analyzes all issues for validation problems
- Does NOT make any changes (no labels added)
- Shows summary of what WOULD be done
- Exit code depends on findings (0 = success, 1 = errors, 2 = warnings)

**What to Look For:**
- Log messages showing "DRY RUN MODE: Changes will be previewed only"
- Messages like "DRY RUN - would add 'created' label" for issues needing initialization
- No actual API calls to modify labels
- Summary report showing issues that would be fixed

**Verification:**
```cmd
echo %ERRORLEVEL%
```

---

## Test 3: Normal Run (Real Changes)

**Command:**
```cmd
workflows\validate_labels.bat
```

**Expected Behavior:**
- Connects to GitHub API
- Fetches open issues
- Analyzes issues for validation problems
- MAKES ACTUAL CHANGES to GitHub (adds labels where needed)
- Shows summary of changes made
- Exit code depends on findings (0 = success, 1 = errors, 2 = warnings)

**What to Validate:**
1. Issues without status labels get "status-01:created" label added
2. Issues with multiple status labels are reported as ERRORS
3. Issues with stale bot_busy labels are reported as WARNINGS
4. Issues with ignore labels are skipped
5. Exit code matches validation results

**Verification:**
```cmd
echo %ERRORLEVEL%
```

---

## Test 4: Debug Logging

**Command:**
```cmd
workflows\validate_labels.bat --log-level DEBUG
```

**Expected Behavior:**
- Much more detailed output
- Shows API call counts
- Shows internal processing details
- Shows which issues are skipped and why
- Shows detailed label matching logic

**What to Look For:**
- Lines starting with `DEBUG:`
- API call counter at the end
- Detailed processing for each issue
- Full tracebacks if errors occur

---

## Test 5: Custom Project Directory

**Command:**
```cmd
workflows\validate_labels.bat --project-dir .
```

**Expected Behavior:**
- Should work exactly like normal run
- Uses current directory as project root
- Validates .git directory exists

**Alternative Test (should fail):**
```cmd
workflows\validate_labels.bat --project-dir C:\nonexistent
```
Should exit with error code 1 and message about invalid directory.

---

## Test 6: Combined Flags

**Command:**
```cmd
workflows\validate_labels.bat --dry-run --log-level DEBUG
```

**Expected Behavior:**
- Dry-run mode (no changes)
- Debug level logging
- Can see detailed processing without making changes

---

## Exit Code Validation

The script uses three exit codes:

| Exit Code | Meaning | When Used |
|-----------|---------|-----------|
| 0 | Success | All issues valid or successfully initialized |
| 1 | Errors | Issues with multiple status labels found |
| 2 | Warnings | Stale bot_busy processes detected |

**Priority:** Errors (1) take precedence over warnings (2)

**Test Scenarios:**

1. **Success (Exit 0):**
   - All issues have exactly one status label
   - No stale bot processes
   - Any initializations completed successfully

2. **Errors (Exit 1):**
   - At least one issue has multiple status labels
   - May also have warnings, but exit code is 1

3. **Warnings (Exit 2):**
   - At least one bot_busy label exceeded timeout
   - No issues with multiple labels

---

## Integration Test Checklist

Use this checklist to verify all functionality:

- [ ] Help flag shows usage information
- [ ] Dry-run mode prevents API changes
- [ ] Normal run mode makes actual changes
- [ ] Debug logging shows detailed information
- [ ] Custom project directory works
- [ ] Invalid project directory causes error
- [ ] Script detects issues without labels
- [ ] Script detects issues with multiple labels
- [ ] Script detects stale bot processes
- [ ] Script respects ignore_labels configuration
- [ ] Exit code 0 on success
- [ ] Exit code 1 on errors
- [ ] Exit code 2 on warnings only
- [ ] Batch file forwards all arguments correctly
- [ ] UTF-8 encoding works for Unicode labels

---

## Expected Repository State

**Before Running:**
Check current repository state:
```cmd
workflows\issue_stats.bat
```

**After Running:**
- Any issues without status labels should now have "status-01:created"
- Check GitHub web UI to verify labels were added correctly
- Re-run `issue_stats.bat` to see updated statistics

---

## Troubleshooting

### GitHub Authentication Errors
If you see authentication errors, ensure:
- GitHub credentials are configured (gh CLI or git config)
- Repository URL is correctly set in .git/config
- You have read/write access to the repository

### API Rate Limiting
If you hit rate limits:
- Wait for rate limit to reset
- Use `--dry-run` mode for testing without API writes
- Check rate limit status: `gh api rate_limit`

### Python Module Not Found
If you see import errors:
- Ensure you're running from project root
- Check PYTHONPATH is set correctly (batch file handles this)
- Verify all dependencies are installed: `pip install -r requirements.txt`

---

## Success Criteria

Integration testing is considered successful when:

1. ✅ All command-line flags work as documented
2. ✅ Dry-run mode prevents changes while showing what would happen
3. ✅ Normal mode successfully modifies GitHub labels
4. ✅ Exit codes correctly reflect validation results
5. ✅ Error handling works gracefully (no crashes)
6. ✅ Log output is clear and informative
7. ✅ Batch file wrapper functions correctly
8. ✅ Script handles edge cases (no issues, all valid, etc.)

---

## Manual Testing Performed

_Document your testing results below:_

### Test 1: Help Flag
- Command: `workflows\validate_labels.bat --help`
- Result: 
- Exit Code: 
- Status: [ ] PASS [ ] FAIL

### Test 2: Dry-Run Mode
- Command: `workflows\validate_labels.bat --dry-run`
- Result: 
- Exit Code: 
- Status: [ ] PASS [ ] FAIL

### Test 3: Normal Run
- Command: `workflows\validate_labels.bat`
- Result: 
- Exit Code: 
- Status: [ ] PASS [ ] FAIL

### Test 4: Debug Logging
- Command: `workflows\validate_labels.bat --log-level DEBUG`
- Result: 
- Exit Code: 
- Status: [ ] PASS [ ] FAIL

### Test 5: Exit Code Verification
- Tested all three exit codes (0, 1, 2)
- Status: [ ] PASS [ ] FAIL

---

## Notes

Add any additional observations, issues, or recommendations here:
