# Step 4: Exit Codes and Output Formatting in define-labels

## LLM Prompt
```
Implement Step 4 of Issue #340. Reference: pr_info/steps/summary.md

Update execute_define_labels() to:
1. Call initialization and validation after label sync
2. Print structured summary output
3. Return correct exit codes (0=success, 1=errors, 2=warnings)

Follow TDD: Write tests first, then implement.
```

---

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/test_define_labels.py` | Add test classes |
| `src/mcp_coder/cli/commands/define_labels.py` | Modify execute_define_labels |

---

## WHAT

### New/Modified Functions

```python
def format_validation_summary(
    label_changes: dict[str, list[str]],
    validation_results: ValidationResults,
    repo_url: str
) -> str:
    """Format the complete summary output.
    
    Returns:
        Formatted summary string for printing
    """

def execute_define_labels(args: argparse.Namespace) -> int:
    """Execute the define-labels command.
    
    Returns:
        Exit code: 0=success, 1=errors, 2=warnings
    """
```

### Test Classes

```python
class TestFormatValidationSummary:
    """Test format_validation_summary function."""
    
    def test_includes_label_sync_counts(self) -> None: ...
    def test_includes_initialized_issues(self) -> None: ...
    def test_includes_error_details(self) -> None: ...
    def test_includes_warning_with_threshold(self) -> None: ...


class TestExecuteDefineLabelsExitCodes:
    """Test exit codes from execute_define_labels."""
    
    def test_returns_zero_on_success(self) -> None: ...
    def test_returns_one_on_errors(self) -> None: ...
    def test_returns_two_on_warnings_only(self) -> None: ...
    def test_errors_take_precedence_over_warnings(self) -> None: ...
```

---

## HOW

### Integration Flow in execute_define_labels
```python
# After existing label sync...
results = apply_labels(project_dir, workflow_labels, dry_run=dry_run)

# NEW: Initialize and validate issues
if not dry_run or True:  # Always fetch for reporting
    issue_manager = IssueManager(project_dir)
    issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    
    # Initialize issues
    initialized = initialize_issues(issues, ...)
    
    # Validate issues
    validation = validate_issues(issues, labels_config, issue_manager, dry_run)
    validation['initialized'] = initialized

# Print summary
summary = format_validation_summary(results, validation, repo_url)
print(summary)

# Return exit code
if validation['errors']:
    return 1
elif validation['warnings']:
    return 2
return 0
```

---

## ALGORITHM

### format_validation_summary
```
1. Build "Labels synced:" line with Created/Updated/Deleted/Unchanged counts
2. Build "Issues initialized:" line with count
3. If errors: Build "Errors (multiple status labels):" with issue details
4. If warnings: Build "Warnings (stale bot processes):" with elapsed/threshold
5. Return joined lines
```

### Exit code logic
```
1. If len(errors) > 0: return 1
2. Elif len(warnings) > 0: return 2  
3. Else: return 0
```

---

## DATA

### Expected Output Format
```
Summary:
  Labels synced: Created=0, Updated=0, Deleted=0, Unchanged=10
  Issues initialized: 3
  Errors (multiple status labels): 1
    - Issue #45: status-01:created, status-03:planning
  Warnings (stale bot processes): 1
    - Issue #78: status-06:implementing for 150 minutes (threshold: 120)
```

### Dry-run Output Addition
```
DRY RUN MODE - Preview of changes:
  Would create 2 labels: status-01:created, status-02:awaiting-planning
  Would initialize 3 issues: #12, #45, #78
```

---

## VERIFICATION

```bash
pytest tests/cli/commands/test_define_labels.py::TestFormatValidationSummary -v
pytest tests/cli/commands/test_define_labels.py::TestExecuteDefineLabelsExitCodes -v

# Integration test
mcp-coder define-labels --dry-run --project-dir /path/to/repo
echo $?  # Should be 0, 1, or 2
```
