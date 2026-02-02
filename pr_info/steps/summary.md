# Issue #340: Enhanced define-labels with Issue Validation and coordinator issue-stats

## Summary

Enhance `mcp-coder define-labels` to automatically initialize and validate issues after syncing labels, add configurable stale timeouts for bot_busy labels, and create a new `mcp-coder coordinator issue-stats` command. Clean up the legacy `workflows/` folder by migrating functionality to CLI commands.

---

## Architectural / Design Changes

### 1. Extended `define-labels` Command Responsibility
**Before:** Sync labels to GitHub repository only.
**After:** Sync labels + initialize issues without status + validate issues + detect stale processes.

The command becomes a "repository health check" for the label workflow system, not just label syncing.

### 2. Configuration Schema Extension
**Change:** Add `stale_timeout_minutes` field to `bot_busy` labels in `labels.json`.
**Impact:** Enables per-label timeout configuration instead of hardcoded values.

### 3. New CLI Command Structure
**Addition:** `mcp-coder coordinator issue-stats` subcommand.
**Pattern:** Follows existing coordinator command structure (`coordinator/commands.py` pattern).

### 4. Legacy Script Migration
**Removal:** `workflows/` folder with standalone Python scripts.
**Migration:** Functionality moves to CLI commands with proper argument parsing and exit codes.

---

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/config/labels.json` | Modify | Add `stale_timeout_minutes` to bot_busy labels |
| `src/mcp_coder/cli/commands/define_labels.py` | Modify | Add validation, initialization, staleness detection |
| `src/mcp_coder/cli/main.py` | Modify | Wire up `coordinator issue-stats` subcommand |
| `tests/cli/commands/test_define_labels.py` | Modify | Add tests for new functionality |
| `docs/repository-setup.md` | Modify | Document new behavior |
| `docs/cli-reference.md` | Modify | Add exit codes, new command |

## Files to Create

| File | Description |
|------|-------------|
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | New issue-stats command implementation |
| `tests/cli/commands/coordinator/test_issue_stats.py` | Tests for issue-stats command |

## Files to Delete

| File | Reason |
|------|--------|
| `workflows/validate_labels.py` | Migrated to define_labels.py |
| `workflows/validate_labels.bat` | No longer needed |
| `workflows/issue_stats.py` | Migrated to coordinator/issue_stats.py |
| `workflows/issue_stats.bat` | No longer needed |
| `workflows/__init__.py` | Folder being removed |
| `tests/workflows/test_validate_labels.py` | Migrated to test_define_labels.py |
| `tests/workflows/test_issue_stats.py` | Migrated to coordinator/test_issue_stats.py |

---

## Exit Code Specification

| Code | Meaning | Condition |
|------|---------|-----------|
| 0 | Success | No errors or warnings |
| 1 | Errors | Issues with multiple status labels found |
| 2 | Warnings | Stale bot processes detected (no errors) |

---

## Data Structures

### Extended ValidationResults (define_labels.py)
```python
ValidationResults = TypedDict('ValidationResults', {
    'initialized': list[int],           # Issue numbers initialized
    'errors': list[dict],               # {'issue': int, 'labels': list[str]}
    'warnings': list[dict],             # {'issue': int, 'label': str, 'elapsed': int, 'threshold': int}
    'ok': list[int],                    # Issue numbers with valid single label
    'skipped': int,                     # Count of ignored issues
})
```

### IssueStats Output Structure (issue_stats.py)
```python
GroupedIssues = TypedDict('GroupedIssues', {
    'human_action': dict[str, list[IssueData]],
    'bot_pickup': dict[str, list[IssueData]],
    'bot_busy': dict[str, list[IssueData]],
    'errors': dict[str, list[IssueData]],  # 'no_status', 'multiple_status'
})
```

---

## Implementation Steps Overview

| Step | Focus | TDD Order |
|------|-------|-----------|
| 1 | Schema: Add `stale_timeout_minutes` to labels.json | Config test → Config change |
| 2 | define-labels: Issue initialization | Test → Implementation |
| 3 | define-labels: Validation & staleness detection | Test → Implementation |
| 4 | define-labels: Exit codes & output formatting | Test → Implementation |
| 5 | coordinator issue-stats: Core functions | Test → Implementation |
| 6 | coordinator issue-stats: CLI wiring | Test → Implementation |
| 7 | Cleanup: Delete workflows/ folder | Verify tests pass → Delete |
| 8 | Documentation updates | Update docs |

---

## Design Decisions Reference

| # | Topic | Decision |
|---|-------|----------|
| 1 | Dry-run behavior | Prevents ALL changes (labels + initialization) |
| 2 | Multiple status labels | Report only, no auto-fix |
| 3 | Implementing timeout | 120 minutes |
| 4 | Exit codes | 0=success, 1=errors, 2=warnings |
| 5 | Filter options | `--filter human\|bot\|all` |
| 6 | Threshold display | Show threshold in stale warnings |
