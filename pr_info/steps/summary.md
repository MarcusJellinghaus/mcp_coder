# Implementation Summary: `mcp-coder set-status` CLI Command

## Issue Reference
**Issue #301**: Add `mcp-coder set-status` CLI command to update GitHub issue labels

## Overview
Add a CLI command that allows users to update GitHub issue workflow labels directly from the command line. The command auto-detects the issue number from the current branch name and sets the specified status label.

## Architectural / Design Changes

### Design Principles Applied
- **KISS**: Direct use of existing `IssueManager.set_labels()` instead of adapting `update_workflow_label()` which has branch linkage validation we don't need
- **No workflow validation**: Per requirements, any status can be set regardless of current state (user controls workflow)
- **Full label names**: Users specify complete label names (e.g., `status-05:plan-ready`) for transparency

### Architecture Decisions

1. **New CLI Command Module**: `src/mcp_coder/cli/commands/set_status.py`
   - Follows existing command pattern (see `define_labels.py`)
   - Single `execute_set_status(args)` function
   - Returns int exit code (0=success, 1=error)

2. **Label Handling Strategy**:
   - Load valid labels from `src/mcp_coder/config/labels.json`
   - Validate user-provided label exists in config
   - Compute new labels: `(current_labels - all_status_*) + new_status`
   - Apply atomically via `IssueManager.set_labels()`

3. **Issue Detection**:
   - Primary: Extract from branch name using existing `extract_issue_number_from_branch()`
   - Override: `--issue` flag for explicit specification

4. **Slash Commands**: Simple markdown files that invoke the CLI

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/cli/commands/set_status.py` | CLI command implementation (~80 lines) |
| `tests/cli/commands/test_set_status.py` | Unit tests for the command |
| `.claude/commands/plan_approve.md` | Slash command for plan approval |
| `.claude/commands/implementation_approve.md` | Slash command for implementation approval |
| `.claude/commands/implementation_needs_rework.md` | Slash command for rework transition |

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/cli/main.py` | Register `set-status` subparser and route to handler |

## Dependencies (Existing - No Changes)

- `extract_issue_number_from_branch()` - `src/mcp_coder/utils/git_operations/branches.py`
- `get_current_branch_name()` - `src/mcp_coder/utils/git_operations/branches.py`
- `IssueManager.get_issue()` - `src/mcp_coder/utils/github_operations/issue_manager.py`
- `IssueManager.set_labels()` - `src/mcp_coder/utils/github_operations/issue_manager.py`
- `load_labels_config()` - `src/mcp_coder/utils/github_operations/label_config.py`
- `resolve_project_dir()` - `src/mcp_coder/workflows/utils.py`

## CLI Interface

```bash
# Auto-detect issue from branch
mcp-coder set-status status-05:plan-ready

# Explicit issue number
mcp-coder set-status status-08:ready-pr --issue 123

# Help shows available labels
mcp-coder set-status --help
```

## Implementation Steps

| Step | Description | Test-First |
|------|-------------|------------|
| 1 | Create test file with unit tests for `set_status.py` | Yes |
| 2 | Implement `set_status.py` command module | - |
| 3 | Register command in `main.py` (with dynamic help text from config) | - |
| 4 | Create slash command files | No (static markdown) |

## Decisions

See `pr_info/steps/Decisions.md` for discussed and agreed decisions:
- #1-4: Initial design decisions
- #5: Use existing IssueManager error for missing token
- #6: Catch and reformat GitHub errors when label not found on repo
- #7: Aim for 6-8 focused tests, let TDD drive actual count

## Success Criteria

1. `mcp-coder set-status <label>` works with branch-based issue detection
2. `mcp-coder set-status <label> --issue N` works with explicit issue
3. `mcp-coder set-status --help` displays available status labels
4. All existing `status-*` labels are removed before adding new one
5. Invalid label names produce clear error messages
6. Slash commands `/plan_approve`, `/implementation_approve`, `/implementation_needs_rework` work correctly
