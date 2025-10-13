# Issue #109: Task List Statistics - Implementation Summary

## Overview
Build a workflow script that displays GitHub issue statistics, grouped by workflow status labels, with validation for label consistency.

## Core Requirements
1. Display issues grouped by workflow status categories (human_action, bot_pickup, bot_busy)
2. Validate that each issue has exactly one valid status label
3. Show validation errors (no status, multiple status labels)
4. Support filtering by category (--filter all/human/bot)
5. Support details mode (--details) with clickable issue links including validation errors
6. Read label configuration from JSON file
7. Support ignoring issues with specific labels (JSON config + CLI override)
8. Fetch only open issues (not closed)
9. Console-only output (no caching, always fresh data)

## Architectural / Design Changes

### New Components
1. **Label Configuration** (`workflows/config/labels.json`)
   - Single source of truth for workflow status labels
   - Schema: `{internal_id, name, color, description, category}`
   - Categories: human_action, bot_pickup, bot_busy

2. **Issue Listing API** (`src/mcp_coder/utils/github_operations/issue_manager.py`)
   - New method: `list_issues(state="all", include_pull_requests=False)`
   - Handles GitHub API pagination automatically
   - Returns list of IssueData dictionaries

3. **Statistics Workflow** (`workflows/issue_stats.py`)
   - Standalone script following `define_labels.py` pattern
   - Load JSON → Fetch open issues → Filter ignored labels → Validate → Group → Display
   - Support for filtering, details mode, and ignore labels
   - Simple console output with basic formatting
   - Details mode shows validation errors with issue links

4. **Batch Launcher** (`workflows/issue_stats.bat`)
   - Windows wrapper with UTF-8 encoding setup
   - Pass-through arguments to Python script

### Design Principles Applied
- **KISS**: Keep labels.json as documentation/reference only
- **No premature abstraction**: Don't modify working `define_labels.py`
- **Acceptable duplication**: Two separate label definitions (for now)
- **Minimal changes**: Only add new functionality, don't refactor existing
- **Console-first**: Simple text output for readability

### Integration Points
- Uses existing `IssueManager` class (extends with new method)
- Uses existing `resolve_project_dir()` from `workflows.utils`
- Uses existing `setup_logging()` from `mcp_coder.utils.log_utils`
- Uses existing `get_github_repository_url()` for context

## Files to Create/Modify

### Files to CREATE
```
workflows/config/labels.json              # Label configuration (new)
workflows/issue_stats.py                  # Main statistics script (new)
workflows/issue_stats.bat                 # Windows launcher (new)
tests/workflows/test_issue_stats.py       # Unit tests (new)
tests/workflows/config/test_labels.json   # Test fixture (new)
pr_info/steps/summary.md                  # This file
pr_info/steps/step_1.md                   # Step 1 implementation plan
pr_info/steps/step_2.md                   # Step 2 implementation plan
pr_info/steps/step_3.md                   # Step 3 implementation plan
pr_info/steps/step_4.md                   # Step 4 implementation plan
pr_info/steps/step_5.md                   # Step 5 implementation plan
pr_info/steps/decisions.md                # Implementation decisions
```

### Files to MODIFY
```
src/mcp_coder/utils/github_operations/issue_manager.py    # Add list_issues()
tests/utils/github_operations/test_issue_manager.py       # Add list_issues tests
workflows/define_labels.py                                # Refactor to use JSON config (Step 5)
```

### Files NOT Modified (Intentional)
```
workflows/define_labels.py                # Keep as-is (working code)
src/mcp_coder/workflows/utils.py          # No constants added (KISS)
```

## Implementation Strategy

### Test-Driven Development Approach
Each step follows TDD pattern:
1. Write failing tests for new functionality
2. Implement minimal code to pass tests
3. Refactor if needed
4. Run all quality checks (pylint, pytest, mypy)

### Step Breakdown
1. **Step 1**: Label configuration + validation tests
2. **Step 2**: IssueManager.list_issues() + unit tests
3. **Step 3**: Core statistics logic + ignore labels + comprehensive tests
4. **Step 4**: CLI integration + batch launcher
5. **Step 5**: Refactor define_labels.py to use JSON config

## Success Criteria
- ✅ All tests pass (unit only, no integration tests)
- ✅ Code quality checks pass (pylint, pytest, mypy)
- ✅ Statistics display matches specification
- ✅ Validation errors detected correctly
- ✅ Validation errors shown in details mode with issue links
- ✅ Filter and details modes work
- ✅ Ignore labels feature works (JSON config + CLI)
- ✅ Only open issues fetched and displayed
- ✅ Terminal output is clear and readable
- ✅ Handles pagination (fetch all open issues)
- ✅ Zero-count statuses shown
- ✅ Follows existing code patterns
- ✅ define_labels.py refactored to use JSON config
