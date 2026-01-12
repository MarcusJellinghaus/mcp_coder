# Step 1: Add Vulture Dependency and Create Whitelist

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Add Vulture as a dev dependency and create the whitelist file for false positives.
Do not modify any other files in this step.
```

## WHERE
| File | Action |
|------|--------|
| `pyproject.toml` | Modify - add dependency |
| `vulture_whitelist.py` | Create - new file in project root |

## WHAT

### pyproject.toml change
Add `vulture>=2.14` to the existing `dev` optional dependencies list.

### vulture_whitelist.py
```python
# Vulture whitelist - false positives for dead code detection
# These items are intentionally unused or used dynamically

# Function signature:
def create_whitelist_entries() -> None:
    """Dummy function containing attribute references that vulture should ignore."""
    pass
```

## HOW
1. Edit `pyproject.toml` to add vulture to `[project.optional-dependencies].dev`
2. Create `vulture_whitelist.py` at project root with whitelisted items

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
1. Open pyproject.toml
2. Find [project.optional-dependencies].dev section
3. Add "vulture>=2.14" to the list
4. Create vulture_whitelist.py with all false positive references
5. Verify vulture runs without errors on whitelist file
```

## VERIFICATION
```bash
# After installation:
uv pip install vulture
vulture vulture_whitelist.py  # Should show no errors in whitelist itself
```
