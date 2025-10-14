# Step 4: Implement Reporting and Complete Main Function

## Goal
Implement the summary reporting function and complete the main() orchestration with proper exit codes.

## Context
This step brings everything together: display validation results in a clear format and return appropriate exit codes for CI/CD integration.

## WHERE
**File**: `workflows/validate_labels.py`

## WHAT

### Function: Display Summary
```python
def display_summary(results: Dict[str, Any], repo_url: str) -> None:
    """Display validation results summary.
    
    Args:
        results: Results dictionary from process_issues()
        repo_url: Repository URL for generating issue links
        
    Output Format (plain text, Decision #5):
        Summary:
          Total issues processed: 47
          Skipped (ignore labels): 3
          Initialized with 'created': 5
            - Issue #12: Title (url)
            - Issue #45: Title (url)
          Errors (multiple status labels): 2
            - Issue #23: status-01:created, status-03:planning
            - Issue #56: status-04:plan-review, status-06:implementing
          Warnings (stale bot processes): 1
            - Issue #78: planning (20 minutes)
    
    Note: Uses plain text format (no emojis or colors, Decision #5)
    """
```

### Update: Complete main() Function
Update the main() function to:
1. Call `process_issues()` with all required parameters
2. Call `display_summary()` with results
3. Calculate and return proper exit code

## HOW

### Integration Points
- **URL formatting**: Use `f"{repo_url}/issues/{issue_number}"` for links
- **Exit codes**: Return via `sys.exit(code)`
- **Logging**: Log summary at INFO level before display

### Exit Code Logic
```python
# After display_summary():
has_errors = len(results["errors"]) > 0
has_warnings = len(results["warnings"]) > 0

# Exit code priority: errors take precedence (Decision #6)
if has_errors:
    logger.error(f"Validation completed with {len(results['errors'])} errors")
    sys.exit(1)  # Errors = exit 1 (even if warnings also present)
elif has_warnings:
    logger.warning(f"Validation completed with {len(results['warnings'])} warnings")
    sys.exit(2)  # Warnings only = exit 2
else:
    logger.info("Validation completed successfully - no errors or warnings")
    sys.exit(0)  # Success = exit 0
```

## ALGORITHM

### display_summary()
```python
# 1. Print header: "Summary:"
# 2. Print counts (processed, skipped, initialized)
# 3. If initialized issues exist:
#    - Print each with title and URL
# 4. Print error count
# 5. If errors exist:
#    - Print each with issue number and conflicting labels
# 6. Print warning count
# 7. If warnings exist:
#    - Print each with issue number, label, and elapsed time
```

### main() completion
```python
# (existing code from Step 2...)
# After fetching issues:

# Process issues with exception handling (Decision #22)
try:
    logger.info("Processing issues for validation...")
    results = process_issues(
        issues=filtered_issues,
        labels_config=labels_config,
        issue_manager=issue_manager,
        dry_run=args.dry_run
    )
except GithubException as e:
    logger.error(f"GitHub API error during validation: {e}")
    logger.error("Validation incomplete - some issues were not checked")
    logger.debug("Traceback:", exc_info=True)  # Log full traceback at DEBUG level
    sys.exit(1)

# Display results
display_summary(results, repo_url)

# Calculate exit code and exit
# Note: Errors take precedence over warnings (Decision #6)
has_errors = len(results["errors"]) > 0
has_warnings = len(results["warnings"]) > 0

if has_errors:
    logger.error(f"Validation completed with {len(results['errors'])} errors")
    sys.exit(1)  # Exit 1 even if warnings also exist
elif has_warnings:
    logger.warning(f"Validation completed with {len(results['warnings'])} warnings")
    sys.exit(2)
else:
    logger.info("Validation completed successfully")
    sys.exit(0)
```

## DATA

### Example Output
```
Summary:
  Total issues processed: 47
  Skipped (ignore labels): 3
  Initialized with 'created': 5
    - Issue #12: Add new feature (https://github.com/user/repo/issues/12)
    - Issue #45: Fix bug (https://github.com/user/repo/issues/45)
  Errors (multiple status labels): 2
    - Issue #23: status-01:created, status-03:planning
    - Issue #56: status-04:plan-review, status-06:implementing
  Warnings (stale bot processes): 1
    - Issue #78: status-03:planning (20 minutes)
```

## Tests to Write

**File**: `tests/workflows/test_validate_labels.py`

Add tests:
```python
def test_display_summary_no_issues(capsys):
    """Test display with no issues"""
    results = {
        "processed": 0,
        "skipped": 0,
        "initialized": [],
        "errors": [],
        "warnings": [],
        "ok": []
    }
    display_summary(results, "https://github.com/user/repo")
    captured = capsys.readouterr()
    assert "Total issues processed: 0" in captured.out

def test_display_summary_with_errors(capsys):
    """Test display with errors"""
    results = {
        "processed": 10,
        "skipped": 1,
        "initialized": [],
        "errors": [
            {"issue": 23, "labels": ["status-01:created", "status-03:planning"]}
        ],
        "warnings": [],
        "ok": [1, 2, 3]
    }
    display_summary(results, "https://github.com/user/repo")
    captured = capsys.readouterr()
    assert "Errors (multiple status labels): 1" in captured.out
    assert "Issue #23" in captured.out

def test_display_summary_with_warnings(capsys):
    """Test display with warnings"""
    results = {
        "processed": 10,
        "skipped": 0,
        "initialized": [],
        "errors": [],
        "warnings": [
            {"issue": 78, "label": "status-03:planning", "elapsed": 20}
        ],
        "ok": [1, 2, 3]
    }
    display_summary(results, "https://github.com/user/repo")
    captured = capsys.readouterr()
    assert "Warnings (stale bot processes): 1" in captured.out
    assert "Issue #78" in captured.out
    assert "20 minutes" in captured.out

def test_main_exit_code_success(monkeypatch):
    """Test main() returns 0 on success"""
    # Mock all dependencies to return successful results
    
def test_main_exit_code_errors(monkeypatch):
    """Test main() returns 1 when errors found"""
    
def test_main_exit_code_warnings(monkeypatch):
    """Test main() returns 2 when only warnings found"""
```

## LLM Prompt for Implementation

```
Please implement Step 4 from pr_info/steps/step_4.md

Review the summary at pr_info/steps/summary.md for context.

Key requirements:
- Implement display_summary() with clear formatted output
- Complete main() function by calling process_issues() with try/except for GithubException
- Add exception handling that logs error with traceback and exits with code 1
- Implement proper exit code logic (0/1/2)
- Add comprehensive tests for display and exit codes
- Use capsys fixture for testing output
- Test all three exit code scenarios plus API error scenario

After implementation:
1. Run the complete script end-to-end with test data
2. Verify output format matches specification
3. Test all exit codes (success, errors, warnings)
4. Run quality checks: pylint, pytest, mypy
5. Fix any issues found
6. Provide commit message
```

## Definition of Done
- [ ] display_summary() implemented with proper formatting
- [ ] main() function completed with process_issues() call wrapped in try/except
- [ ] GithubException handling logs error with traceback at DEBUG level
- [ ] Exit code logic implemented correctly (0/1/2)
- [ ] Output format matches specification exactly
- [ ] All tests passing including exit code tests and exception handling
- [ ] Script can be run end-to-end successfully
- [ ] All quality checks pass (pylint, pytest, mypy)
