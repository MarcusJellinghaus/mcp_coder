"""Session orchestration for vscodeclaude feature.

Main functions for preparing, launching, and managing sessions.

Session Lifecycle Rules:
- Sessions are created for issues at human_action statuses with initial_command
- Eligible statuses: status-01:created, status-04:plan-review, status-07:code-review
- Ineligible: bot_pickup (02, 05, 08), bot_busy (03, 06, 09), pr-created (10)

Branch Handling Rules:
- status-01:created: Use linked branch if exists, fall back to 'main' if not
- status-04:plan-review: REQUIRE linked branch, skip if missing
- status-07:code-review: REQUIRE linked branch, skip if missing

Restart Behavior:
- Every restart runs 'git fetch origin' to sync with remote
- status-01 restarts: Stay on current branch, fetch only
- status-04/07 restarts: Verify linked branch, checkout if different, pull
- Status changes (01→04): Auto-switch to linked branch if repo is clean

Branch Verification on Restart:
1. git fetch origin (always, all statuses)
2. If status-04/07:
   a. Get linked branch from GitHub API
   b. If no linked branch → skip restart, show "!! No branch"
   c. Check repo dirty (git status --porcelain)
   d. If dirty → skip restart, show "!! Dirty"
   e. git checkout <linked_branch>
   f. git pull
   g. If git error → skip restart, show "!! Git error"
3. Update .vscodeclaude_status.txt with branch name
4. Regenerate session files
5. Launch VSCode

Cleanup Behavior:
- Stale sessions (status changed, closed, bot stage, pr-created) eligible for --cleanup
- Dirty folders (uncommitted changes) require manual cleanup, never auto-deleted

Dirty Folder Protection:
- Sessions with uncommitted git changes are never auto-deleted
- Display shows "!! Manual cleanup" for these cases
- Dirty detection: any output from 'git status --porcelain'

Status Table Indicators:
- (active): VSCode is running
- !! No branch: status-04/07 without linked branch
- !! Dirty: Repo has uncommitted changes, can't switch branch
- !! Git error: Git operation failed
- → Needs branch: Eligible issue at status-04/07 needs linked branch
- Blocked (label): Issue has ignore label
- → Delete (with --cleanup): Session is stale
- → Restart: Normal restart needed
- → Create and start: New session can be created

Intervention Sessions:
- Follow same branch rules as normal sessions
- is_intervention flag doesn't affect branch requirements

---

## Decision Matrix: Session Actions by State

### Launch Behavior (New Sessions)

| Status | Branch State | Action | Reason |
|--------|--------------|--------|--------|
| 01:created | No linked | Launch on `main` | Fallback allowed for status-01 |
| 01:created | Has linked | Launch on linked | Use linked branch if available |
| 04:plan-review | No linked | Skip, log error | Branch required for status-04 |
| 04:plan-review | Has linked | Launch on linked | Normal flow |
| 04:plan-review | Multiple linked | Skip, log error | Ambiguous branch state |
| 07:code-review | No linked | Skip, log error | Branch required for status-07 |
| 07:code-review | Has linked | Launch on linked | Normal flow |
| 07:code-review | Multiple linked | Skip, log error | Ambiguous branch state |
| 10:pr-created | Any | No session | PR-created issues don't need sessions |

### Restart Behavior (Existing Sessions)

| Status | Branch | VSCode | Folder | Blocked | Git Fetch | Action | Indicator |
|--------|--------|--------|--------|---------|-----------|--------|-----------|
| 01 | Any | Running | Any | No | - | No action | (active) |
| 01 | Any | Closed | Clean | No | Success | Restart, stay on branch | → Restart |
| 01 | Any | Closed | Dirty | No | Success | Skip | !! Dirty |
| 01 | Any | Closed | Clean | Yes | - | Skip | Blocked (label) |
| 01 | Any | Closed | Clean | No | Failed | Skip | !! Git error |
| 04 | No linked | Closed | Clean | No | Success | Skip | !! No branch |
| 04 | Multiple | Closed | Clean | No | Success | Skip | !! Multi-branch |
| 04 | Has linked | Running | Any | No | - | No action | (active) |
| 04 | Has linked | Closed | Dirty | No | Success | Skip | !! Dirty |
| 04 | Has linked | Closed | Clean | No | Failed | Skip | !! Git error |
| 04 | Has linked | Closed | Clean | No | Success | Checkout + pull + restart | → Restart |
| 04 | Has linked | Closed | Clean | Yes | - | Skip | Blocked (label) |
| 07 | No linked | Closed | Clean | No | Success | Skip | !! No branch |
| 07 | Multiple | Closed | Clean | No | Success | Skip | !! Multi-branch |
| 07 | Has linked | Running | Any | No | - | No action | (active) |
| 07 | Has linked | Closed | Dirty | No | Success | Skip | !! Dirty |
| 07 | Has linked | Closed | Clean | No | Failed | Skip | !! Git error |
| 07 | Has linked | Closed | Clean | No | Success | Checkout + pull + restart | → Restart |
| 07 | Has linked | Closed | Clean | Yes | - | Skip | Blocked (label) |

**Priority Order for Restart Decisions:**
1. VSCode running → (active)
2. Skip reason (no branch/dirty/git error/multi-branch) → !! indicators
3. Blocked label → Blocked (label)
4. Stale (status changed to ineligible) → → Delete (with --cleanup)
5. Normal flow → → Restart

### Status Display (No Existing Session)

| Status | Branch State | Issue State | Indicator |
|--------|--------------|-------------|-----------|
| 01 | Any | Open, eligible | → Create and start |
| 04 | No linked | Open, eligible | → Needs branch |
| 04 | Multiple linked | Open, eligible | → Needs branch |
| 04 | Has linked | Open, eligible | → Create and start |
| 07 | No linked | Open, eligible | → Needs branch |
| 07 | Multiple linked | Open, eligible | → Needs branch |
| 07 | Has linked | Open, eligible | → Create and start |
| 10:pr-created | Any | Open | (No session row) |

---

## Common Scenarios

### Scenario 1: Fresh Planning Session
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Not running
Folder: Does not exist
Action: Create folder, clone, checkout feature/issue-123, launch VSCode
```

### Scenario 2: Planning Approved, Status Changed
```
Initial: Status 04:plan-review on feature/issue-123
User approves plan, status changes to 05:bot-pickup
VSCode: Running
Action: No restart (bot status ineligible), marked stale for cleanup
Display: "→ Delete (with --cleanup)"
```

### Scenario 3: Restart After VSCode Closed
```
Status: 07:code-review
Branch: feature/issue-123 (linked)
VSCode: Closed (user closed it)
Folder: Clean (no uncommitted changes)
Restart flow:
  1. git fetch origin
  2. Get linked branch: feature/issue-123
  3. Check dirty: Clean
  4. git checkout feature/issue-123
  5. git pull
  6. Regenerate session files
  7. Launch VSCode
```

### Scenario 4: Restart Blocked by Uncommitted Work
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Closed
Folder: Dirty (user made changes)
Action: Skip restart
Display: "!! Dirty"
Reason: Can't switch branches with uncommitted changes
```

### Scenario 5: Issue Moved to Code Review, No Branch
```
Status: 07:code-review
Branch: None linked (forgot to link in GitHub)
VSCode: Closed
Action: Skip restart
Display: "!! No branch"
Reason: Status-07 requires linked branch
```

### Scenario 6: Multiple Branches Linked
```
Status: 04:plan-review
Branch: Multiple branches linked to issue in GitHub
VSCode: Closed
Action: Skip restart
Display: "!! Multi-branch"
Reason: Ambiguous which branch to use
Fix: Unlink all but one branch in GitHub
```

### Scenario 7: Status-01 Without Branch
```
Status: 01:created
Branch: No linked branch
VSCode: Not running
Folder: Does not exist
Action: Create folder, clone, checkout main, launch VSCode
Display: "→ Create and start"
Reason: Status-01 allows fallback to main
```

### Scenario 8: Network Failure on Restart
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Closed
Folder: Clean
git fetch origin: FAILS (network down)
Action: Skip restart
Display: "!! Git error"
Reason: Can't proceed without fetch
```

---

## State Transitions

```
NEW ISSUE (status-01:created)
    ├─► Has linked branch → Launch on linked branch
    └─► No linked branch → Launch on main

PLANNING PHASE (status-04:plan-review)
    ├─► Has linked branch + clean → Launch/restart
    ├─► Has linked branch + dirty → Skip (!! Dirty)
    ├─► No linked branch → Skip (!! No branch)
    └─► Multiple branches → Skip (!! Multi-branch)

CODE REVIEW (status-07:code-review)
    ├─► Has linked branch + clean → Launch/restart
    ├─► Has linked branch + dirty → Skip (!! Dirty)
    ├─► No linked branch → Skip (!! No branch)
    └─► Multiple branches → Skip (!! Multi-branch)

PR CREATED (status-10:pr-created)
    └─► No session created (displayed separately)
```
"""

# Cleanup
from .cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
    get_stale_sessions,
)

# Configuration
from .config import (
    get_github_username,
    load_repo_vscodeclaude_config,
    load_vscodeclaude_config,
    sanitize_folder_name,
)

# Helpers (re-exported for backward compatibility)
from .helpers import get_stage_display_name, truncate_title

# Issue filtering
from .issues import (
    _filter_eligible_vscodeclaude_issues,
    get_cached_eligible_vscodeclaude_issues,
    get_eligible_vscodeclaude_issues,
    get_human_action_labels,
    get_linked_branch_for_issue,
)

# Session launch
from .session_launch import (
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    regenerate_session_files,
)

# Session restart
from .session_restart import (
    handle_pr_created_issues,
    restart_closed_sessions,
)

# Session management
from .sessions import (
    add_session,
    check_vscode_running,
    clear_vscode_process_cache,
    clear_vscode_window_cache,
    get_active_session_count,
    get_session_for_issue,
    get_sessions_file_path,
    is_vscode_open_for_folder,
    is_vscode_window_open_for_folder,
    load_sessions,
    remove_session,
    save_sessions,
    update_session_pid,
)

# Status
from .status import (
    check_folder_dirty,
    display_status_table,
    get_folder_git_status,
    get_issue_current_status,
    get_next_action,
    is_issue_closed,
    is_session_stale,
)

# Types and constants
from .types import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_PROMPT_TIMEOUT,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)

# Workspace setup
from .workspace import (
    create_startup_script,
    create_status_file,
    create_vscode_task,
    create_working_folder,
    create_workspace_file,
    get_working_folder_path,
    run_setup_commands,
    setup_git_repo,
    update_gitignore,
    validate_mcp_json,
    validate_setup_commands,
)

__all__ = [
    # Types
    "VSCodeClaudeSession",
    "VSCodeClaudeSessionStore",
    "VSCodeClaudeConfig",
    "RepoVSCodeClaudeConfig",
    # Constants
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_PROMPT_TIMEOUT",
    # Session management
    "get_sessions_file_path",
    "load_sessions",
    "save_sessions",
    "check_vscode_running",
    "clear_vscode_process_cache",
    "clear_vscode_window_cache",
    "is_vscode_open_for_folder",
    "is_vscode_window_open_for_folder",
    "get_session_for_issue",
    "add_session",
    "remove_session",
    "get_active_session_count",
    "update_session_pid",
    # Configuration
    "load_vscodeclaude_config",
    "load_repo_vscodeclaude_config",
    "get_github_username",
    "sanitize_folder_name",
    # Issue filtering
    "get_human_action_labels",
    "get_eligible_vscodeclaude_issues",
    "get_cached_eligible_vscodeclaude_issues",
    "_filter_eligible_vscodeclaude_issues",
    "get_linked_branch_for_issue",
    # Workspace setup
    "get_working_folder_path",
    "create_working_folder",
    "setup_git_repo",
    "validate_mcp_json",
    "validate_setup_commands",
    "run_setup_commands",
    "update_gitignore",
    "create_workspace_file",
    "create_startup_script",
    "create_vscode_task",
    "create_status_file",
    # Session launch
    "launch_vscode",
    "prepare_and_launch_session",
    "process_eligible_issues",
    "regenerate_session_files",
    # Session restart
    "restart_closed_sessions",
    "handle_pr_created_issues",
    # Helpers
    "get_stage_display_name",
    "truncate_title",
    # Status
    "get_issue_current_status",
    "is_issue_closed",
    "is_session_stale",
    "check_folder_dirty",
    "get_folder_git_status",
    "get_next_action",
    "display_status_table",
    # Cleanup
    "get_stale_sessions",
    "delete_session_folder",
    "cleanup_stale_sessions",
]
