# Step 1: Create Vulture Whitelist

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Create the whitelist file for false positives.
Do not modify any other files in this step.
```

## WHERE
| File | Action |
|------|--------|
| `vulture_whitelist.py` | Create - new file in project root |

## WHAT

### vulture_whitelist.py
Create attribute-style whitelist file with all false positive references:

```python
# Vulture whitelist - false positives for dead code detection
# These items are intentionally unused or used dynamically
# Format: _.attribute_name (attribute-style whitelist)
#
# Review this list periodically - see separate issue for cleanup review

# Argparse subparsers (main.py) - standard argparse pattern
_.help_parser
_.verify_parser

# Enum-like constants (issue_manager.py) - GitHub API event types
_.LABELED
_.UNLABELED
_.CLOSED
_.REOPENED
_.ASSIGNED
_.UNASSIGNED
_.MILESTONED
_.DEMILESTONED
_.REFERENCED
_.CROSS_REFERENCED
_.COMMENTED
_.MENTIONED
_.SUBSCRIBED
_.UNSUBSCRIBED
_.RENAMED
_.LOCKED
_.UNLOCKED
_.REVIEW_REQUESTED
_.REVIEW_REQUEST_REMOVED
_.CONVERTED_TO_DRAFT
_.READY_FOR_REVIEW

# Base class attributes (base_manager.py) - used by subclasses/debugging
_._repo_owner
_._repo_name

# API completeness functions (GitHub operations) - kept for complete API
_.get_issue_events
_.add_comment
_.edit_comment
_.delete_comment
_.close_issue
_.reopen_issue
_.get_available_labels
_.get_pull_request
_.list_pull_requests
_.close_pull_request
_.repository_name
_.get_latest_ci_status
_.get_run_logs
_.delete_linked_branch
_.format_github_https_url

# Utility functions (kept for planned features)
_._detect_active_venv
_.find_virtual_environments
_.get_venv_python
_.get_python_info
_.get_project_dependencies
_.find_package_data_files
_.get_package_directory
_.has_mypy_errors
_._retry_with_backoff
_.has_incomplete_work
_._get_jenkins_config
_.get_queue_summary

# Workflow constants
_.workflow
_.branch_strategy
_.next_label
_.CONVERSATIONS_DIR

# Subprocess runner attributes
_.execution_error
_.runner_type

# Test fixtures (intentionally unused - trigger skip logic)
_.require_claude_cli
```

## HOW
1. Create `vulture_whitelist.py` at project root with all whitelisted items
2. Verify whitelist file is valid

## DATA - Whitelist Categories

### Argparse subparsers (main.py)
- `help_parser` - standard argparse pattern
- `verify_parser` - standard argparse pattern

### Enum-like constants (issue_manager.py lines 47-81)
Event type constants for GitHub API completeness:
- `LABELED`, `UNLABELED`, `CLOSED`, `REOPENED`, `ASSIGNED`, `UNASSIGNED`
- `MILESTONED`, `DEMILESTONED`, `REFERENCED`, `CROSS_REFERENCED`
- `COMMENTED`, `MENTIONED`, `SUBSCRIBED`, `UNSUBSCRIBED`, `RENAMED`
- `LOCKED`, `UNLOCKED`, `REVIEW_REQUESTED`, `REVIEW_REQUEST_REMOVED`
- `CONVERTED_TO_DRAFT`, `READY_FOR_REVIEW`

### Base class attributes (base_manager.py)
- `_repo_owner` - used by subclasses or debugging
- `_repo_name` - used by subclasses or debugging

### API completeness functions (GitHub operations)
Methods kept for complete API coverage even if not currently called:
- `get_issue_events`, `add_comment`, `edit_comment`, `delete_comment`
- `close_issue`, `reopen_issue`, `get_available_labels`
- `get_pull_request`, `list_pull_requests`, `close_pull_request`, `repository_name`
- `get_latest_ci_status`, `get_run_logs`, `delete_linked_branch`
- `format_github_https_url`

### Utility functions (kept for planned features)
- `_detect_active_venv`, `find_virtual_environments`, `get_venv_python`
- `get_python_info`, `get_project_dependencies`
- `find_package_data_files`, `get_package_directory`
- `has_mypy_errors`, `_retry_with_backoff`, `has_incomplete_work`
- `_get_jenkins_config`, `get_queue_summary`

### Workflow constants
- `workflow`, `branch_strategy`, `next_label`
- `CONVERSATIONS_DIR`

### Subprocess runner
- `execution_error`, `runner_type`

## ALGORITHM
```
1. Create vulture_whitelist.py with all false positive references
2. Verify vulture runs without errors on whitelist file
```

## VERIFICATION
```bash
# Verify whitelist file is valid:
vulture vulture_whitelist.py  # Should show no errors in whitelist itself
```
