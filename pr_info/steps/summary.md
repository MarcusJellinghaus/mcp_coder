# Implementation Plan: Validate and Reset GitHub Issue Labels

## Overview
Create a workflow script to validate and maintain GitHub issue labels, ensuring consistent status labeling across all issues and detecting workflow anomalies.

## Architecture & Design

### Design Philosophy
This implementation follows the **KISS principle** by maximizing reuse of existing patterns and minimizing new abstractions:

1. **Pattern Reuse**: Follows structure of existing workflow scripts (`define_labels.py`, `issue_stats.py`)
2. **Minimal Extension**: Adds only ONE new method to existing `IssueManager` class
3. **Linear Processing**: Simple sequential issue processing without complex grouping
4. **Report and Exit**: Detect and report problems, don't attempt auto-fixes
5. **Plain Text Output**: No emojis or colors, works everywhere (CI/CD, logs)

**Design Decisions:** See `pr_info/steps/Decisions.md` for detailed rationale on all choices made during plan review.

### Architectural Changes

#### New Components
1. **`workflows/validate_labels.py`** - Main workflow script (~300 lines)
   - Validates issue label consistency
   - Detects stale bot processes
   - Initializes missing status labels
   - Reports errors and warnings

2. **`workflows/validate_labels.bat`** - Windows batch file wrapper

#### Modified Components
1. **`src/mcp_coder/utils/github_operations/issue_manager.py`**
   - Add `get_issue_events()` method to retrieve issue timeline events
   - Returns event data for tracking when labels were applied

#### Test Coverage
1. **`tests/workflows/test_validate_labels.py`** - Unit tests for validation logic

### Integration Points

**Inputs:**
- `workflows/config/labels.json` - Label definitions via `load_labels_config()`
- GitHub Issues API - Open issues via `IssueManager.list_issues()`
- GitHub Events API - Label timeline via `IssueManager.get_issue_events()`

**Outputs:**
- Console output with validation results
- GitHub API calls to add missing labels (unless dry-run)
- Exit codes: 0 (success), 1 (errors), 2 (warnings only)

**Reused Utilities:**
- `workflows/utils.py::resolve_project_dir()` - Project directory resolution
- `workflows/label_config.py::load_labels_config()` - Config loading
- `mcp_coder.utils.log_utils::setup_logging()` - Logging configuration
- `IssueManager` - Issue operations
- `LabelsManager` - Label operations (for adding missing labels)

## Files to Create or Modify

### Files to CREATE:
```
workflows/validate_labels.py          # Main workflow script
workflows/validate_labels.bat         # Windows batch wrapper
tests/workflows/test_validate_labels.py  # Unit tests
pr_info/steps/summary.md              # This file
pr_info/steps/step_1.md               # Implementation steps
pr_info/steps/step_2.md
pr_info/steps/step_3.md
pr_info/steps/step_4.md
```

### Files to MODIFY:
```
src/mcp_coder/utils/github_operations/issue_manager.py  # Add get_issue_events()
```

## Core Functionality

### 1. Label Validation Rules
- **Missing Status**: Open issues without any workflow label get `status-01:created`
- **Double Status**: Issues with 2+ workflow labels are logged as ERROR
- **Stale Bot Process**: Bot-busy labels exceeding timeout are logged as WARNING
  - `implementing`: 60 minutes
  - `planning`: 15 minutes
  - `pr_creating`: 15 minutes
- **Ignore Labels**: Issues with ANY ignore label (e.g., "Overview") are skipped entirely
- **API Errors**: Event fetching failures cause script to stop (no silent failures)

### 2. Processing Flow
```
1. Load label configuration
2. Fetch all open issues from GitHub
3. Filter out ignored issues (e.g., "Overview" label)
4. For each issue:
   - Check status label count (0, 1, or 2+)
   - If 0: Add "created" label (unless dry-run)
   - If 2+: Log ERROR
   - If 1 and bot_busy: Check for stale (check timeline events)
5. Display summary with counts and details
6. Exit with appropriate code
```

### 3. Timeout Detection Algorithm
```
For each issue with bot_busy label:
1. Get issue events via GitHub Events API (will raise on API errors)
2. Find most recent "labeled" event for that specific label
3. Calculate elapsed time using helper function
4. If elapsed > timeout: Log WARNING with details
5. Log total API calls at DEBUG level
```

**Note:** API call counting helps monitor rate limit usage (logged at DEBUG level).

## Implementation Steps

1. **Step 1**: Extend IssueManager with Events API support
2. **Step 2**: Create validate_labels.py structure with argument parsing
3. **Step 3**: Implement core validation logic (status checks, stale detection)
4. **Step 4**: Implement reporting and main orchestration
5. **Step 5**: Create batch file and tests

## Success Criteria

- ✅ Script correctly identifies issues without status labels
- ✅ Script correctly detects issues with multiple status labels
- ✅ Script correctly detects stale bot processes with accurate timeouts
- ✅ Dry-run mode works without making any changes
- ✅ Clear, actionable output for manual review
- ✅ Exit codes work correctly (0/1/2)
- ✅ All quality checks pass (pylint, pytest, mypy)
- ✅ Follows existing codebase patterns and conventions

## Non-Goals (Kept Simple)

- ❌ Automatic removal of duplicate labels (too risky - report only)
- ❌ Automatic unsticking of stale processes (requires human judgment)
- ❌ Processing closed issues (requirement specifies open only)
- ❌ Complex categorization or grouping (linear processing sufficient)
- ❌ Historical analysis (focus on current state only)
- ❌ Debug mode for specific issues (KISS - use --dry-run instead)
- ❌ JSON output or fancy formatting (plain text for maximum compatibility)
