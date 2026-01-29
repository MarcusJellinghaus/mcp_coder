# VSCodeClaude Module Architecture

## Overview

The vscodeclaude feature was refactored from a monolithic 1895-line file in `cli/commands/coordinator/` 
to a properly separated module structure in `utils/vscodeclaude/`.

## Why This Refactoring?

The original `cli/commands/coordinator/vscodeclaude.py` violated separation of concerns:
- CLI layer should be **thin** - just argument parsing and calling business logic
- Business logic (file I/O, git operations, GitHub API calls) belongs in `utils/`
- This matches existing patterns: `utils/github_operations/`, `workflow_utils/`

## New Structure

```
src/mcp_coder/
├── utils/
│   └── vscodeclaude/
│       ├── __init__.py       # Public API exports
│       ├── types.py          # TypedDicts, constants (~100 lines)
│       ├── sessions.py       # JSON session management (~150 lines)
│       ├── config.py         # Config loading from TOML (~120 lines)
│       ├── issues.py         # GitHub issue filtering (~150 lines)
│       ├── workspace.py      # Git, folders, file creation (~400 lines)
│       ├── orchestrator.py   # Session preparation & launch (~300 lines)
│       ├── status.py         # Status display & staleness (~200 lines)
│       └── cleanup.py        # Stale session cleanup (~100 lines)
│
└── cli/
    └── commands/
        └── coordinator/
            ├── commands.py               # CLI handlers (unchanged)
            └── vscodeclaude_templates.py # Template strings (unchanged)
```

## Module Responsibilities

### types.py
- `VSCodeClaudeSession`, `VSCodeClaudeSessionStore`, `VSCodeClaudeConfig`, `RepoVSCodeClaudeConfig` TypedDicts
- Constants: `VSCODECLAUDE_PRIORITY`, `HUMAN_ACTION_COMMANDS`, `STATUS_EMOJI`, `DEFAULT_MAX_SESSIONS`

### sessions.py
- `get_sessions_file_path()` - Platform-specific path to sessions JSON
- `load_sessions()` / `save_sessions()` - JSON file I/O
- `add_session()` / `remove_session()` - Session CRUD
- `check_vscode_running()` - PID check via psutil
- `get_session_for_issue()` / `get_active_session_count()` / `update_session_pid()`

### config.py
- `load_vscodeclaude_config()` - Load `[coordinator.vscodeclaude]` from TOML
- `load_repo_vscodeclaude_config()` - Load per-repo setup commands
- `get_github_username()` - Get authenticated username via PyGithub
- `sanitize_folder_name()` - Clean strings for folder names

### issues.py
- `get_human_action_labels()` - Extract human_action labels from labels.json
- `get_eligible_vscodeclaude_issues()` - Filter and sort issues by priority
- `get_linked_branch_for_issue()` - Get linked branch via IssueBranchManager

### workspace.py
- `get_working_folder_path()` - Build folder path from config
- `create_working_folder()` - Create directory if not exists
- `setup_git_repo()` - Clone or checkout/pull
- `validate_mcp_json()` / `validate_setup_commands()` - Validation
- `run_setup_commands()` - Execute platform-specific setup
- `update_gitignore()` - Append vscodeclaude entries
- `create_workspace_file()` - Create .code-workspace JSON
- `create_startup_script()` - Create .bat or .sh script
- `create_vscode_task()` - Create .vscode/tasks.json
- `create_status_file()` - Create .vscodeclaude_status.md

### orchestrator.py
- `launch_vscode()` - Non-blocking VSCode launch
- `prepare_and_launch_session()` - Full session setup and launch
- `process_eligible_issues()` - Process repo's eligible issues
- `restart_closed_sessions()` - Restart sessions where VSCode closed
- `handle_pr_created_issues()` - Display PR URLs for pr-created status

### status.py
- `get_issue_current_status()` - Get current status label from GitHub
- `is_session_stale()` - Check if issue status changed
- `check_folder_dirty()` - Check for uncommitted git changes
- `get_next_action()` - Determine next action for session
- `display_status_table()` - Print formatted status table

### cleanup.py
- `get_stale_sessions()` - Find stale sessions with dirty status
- `delete_session_folder()` - Delete folder and remove from store
- `cleanup_stale_sessions()` - Clean up stale folders (dry-run or actual)

## CLI Layer

The CLI handlers in `commands.py` remain thin:
- `execute_coordinator_vscodeclaude()` - Parse args, call orchestrator functions
- `execute_coordinator_vscodeclaude_status()` - Call status display functions
- `_handle_intervention_mode()` - Handle --intervene flag

## Test Refactoring (TODO)

**Note:** The test file `tests/cli/commands/coordinator/test_vscodeclaude.py` (2871 lines) 
still needs refactoring to match the new structure:

```
tests/utils/vscodeclaude/
├── test_types.py
├── test_sessions.py
├── test_config.py
├── test_issues.py
├── test_workspace.py
├── test_orchestrator.py
├── test_status.py
└── test_cleanup.py
```

This is tracked for a future PR to keep changes manageable.

## Import Pattern

The `utils/vscodeclaude/__init__.py` re-exports the public API, so existing imports 
from `commands.py` continue to work with minimal changes:

```python
# Old (from monolithic file)
from .vscodeclaude import load_sessions, prepare_and_launch_session

# New (from utils package)
from ....utils.vscodeclaude import load_sessions, prepare_and_launch_session
```
