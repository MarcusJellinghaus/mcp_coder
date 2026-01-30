# Coordinator VSCodeClaude Command - Implementation Summary

## Overview

Add `mcp-coder coordinator vscodeclaude` command to manage multiple VSCode/Claude Code sessions for interactive workflow stages across repositories.

## Architecture / Design Changes

### New Files (Modular Structure)

```
src/mcp_coder/utils/vscodeclaude/
├── __init__.py           # Public API exports
├── types.py              # TypedDicts, constants
├── sessions.py           # JSON session management
├── config.py             # Config loading from TOML
├── issues.py             # GitHub issue filtering
├── workspace.py          # Git, folders, file creation
├── orchestrator.py       # Session preparation & launch
├── status.py             # Status display & staleness
└── cleanup.py            # Stale session cleanup

src/mcp_coder/cli/commands/coordinator/
└── vscodeclaude_templates.py    # Template strings only

tests/utils/vscodeclaude/
├── test_types.py         # Type and constant tests
├── test_sessions.py      # Session management tests
├── test_config.py        # Configuration tests
├── test_issues.py        # Issue selection tests
├── test_workspace.py     # Workspace setup tests
├── test_orchestrator.py  # Orchestration tests
├── test_status.py        # Status display tests
└── test_cleanup.py       # Cleanup tests

tests/cli/commands/coordinator/
└── test_vscodeclaude_cli.py     # CLI layer tests (templates, handlers)
```

### Modified Files

| File | Change |
|------|--------|
| `pyproject.toml` | Add `psutil` dependency |
| `src/mcp_coder/cli/main.py` | Add CLI parsers and routing |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Add command handlers |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Export new functions |

### Design Decisions

1. **Modular approach** - Business logic split into `utils/vscodeclaude/` package with focused modules (<400 lines each)
2. **Templates separated** - Large string constants in dedicated file for readability
3. **Reuse existing infrastructure** - `IssueManager`, `IssueBranchManager`, `load_labels_config`, `get_config_values`
4. **Late binding pattern** - Use `_get_coordinator()` for testability (matches existing code)
5. **Platform handling** - `pathlib` for paths, conditional templates for Windows/Linux
6. **Validation and cleanup** - Validate setup commands exist, cleanup on session failure
7. **Progress feedback** - Use `logger.info()` for long-running operations
8. **Testing strategy** - Unit tests + key integration tests for end-to-end workflows

### Data Flow

```
CLI Args → load_vscodeclaude_config() → get_eligible_vscodeclaude_issues()
    → create_working_folder() → setup_git_repo() → run_setup_commands()
    → create_workspace_files() → launch_vscode()
```

### Session Storage

Location: `~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json`

```json
{
  "sessions": [{
    "folder": "C:\\...\\mcp-coder_123",
    "repo": "owner/repo",
    "issue_number": 123,
    "status": "status-07:code-review",
    "vscode_pid": 12345,
    "started_at": "2024-01-22T10:30:00Z",
    "is_intervention": false
  }],
  "last_updated": "2024-01-22T10:35:00Z"
}
```

### Priority Order (Human Action Statuses)

```python
VSCODECLAUDE_PRIORITY = [
    "status-10:pr-created",    # Highest - show PR URL only
    "status-07:code-review",   # /implementation_review → /discuss
    "status-04:plan-review",   # /plan_review → /discuss  
    "status-01:created",       # /issue_analyse → /discuss
]
```

## Implementation Steps Overview

| Step | Focus | Files |
|------|-------|-------|
| 1 | Dependencies & Config | `pyproject.toml`, types |
| 2 | Templates | `vscodeclaude_templates.py` |
| 3 | Session Management | `utils/vscodeclaude/sessions.py` |
| 4 | Issue Selection | `utils/vscodeclaude/issues.py`, `config.py` |
| 5 | Workspace Setup | `utils/vscodeclaude/workspace.py` |
| 6 | VSCode Launch | `utils/vscodeclaude/orchestrator.py` |
| 7 | CLI Integration | `main.py`, `commands.py`, `__init__.py` |
| 8 | Status & Cleanup | `utils/vscodeclaude/status.py`, `cleanup.py` |
| 9 | Code Review Fixes | Bug fixes from first code review |
| 10 | Code Review Fixes (Round 2) | Stale check, type hints, test cleanup |
| 11 | Test Refactoring | Split tests to match `utils/vscodeclaude/` structure |
| 12 | Cache Integration | Use existing `get_all_cached_issues()` in vscodeclaude |
| 13 | Pass Cached Issues | Eliminate duplicate API calls via cache lookup |

## Performance Optimization (Steps 12-13)

The vscodeclaude command was experiencing 90+ second delays due to:
1. Direct `list_issues()` calls fetching ALL issues (7-45s per repo)
2. Duplicate `get_issue()` calls for staleness checks (~2s per session)

### Solution: Use Existing Issue Cache

The `coordinator run` command already has a working cache (`get_all_cached_issues()` in `issue_cache.py`).
The vscodeclaude feature now uses the **same cache** with the following flow:

```
get_all_cached_issues()     # Shared cache, returns ALL issues
        ↓
_filter_eligible_issues()   # coordinator run: bot_pickup labels
_filter_eligible_vscodeclaude_issues()  # vscodeclaude: human_action labels + assignee
        ↓
Pass cached issues dict to staleness checks (no individual get_issue calls)
```

### Performance Improvement

| Scenario | Before | After |
|----------|--------|-------|
| Cache hit | N/A | <1 second |
| Incremental refresh | N/A | 1-5 seconds |
| Full refresh (24h+) | 90+ seconds | Same (but rare) |
| Staleness checks | 2s per session | 0s (cache lookup) |

## Key Requirements Preserved

- Full CLI: `--repo`, `--max-sessions`, `--cleanup`, `--intervene`, `status` subcommand
- Session JSON tracking with PID via `psutil`
- Working folders: `{repo}_{issue_number}` with sanitized names
- Git clone/checkout/pull using system credentials with progress logging
- Platform-specific setup commands with validation (commands must exist in PATH)
- `.mcp.json` validation (required)
- VSCode workspace file with window title
- VSCode `tasks.json` with `runOn: folderOpen`
- Two-stage startup script (automated analysis → interactive `/discuss`)
- Status file `.vscodeclaude_status.md` in project root
- `.gitignore` modification
- Priority: later stages first (status-10 > status-07 > status-04 > status-01)
- Filter: assigned to user, human_action labels, ignore_labels excluded
- Stale detection and cleanup (requires `--cleanup` flag)
- Intervention mode for bot_busy stages
- Session recovery: cleanup working folder on session creation failure
- **Stale check in restart**: Don't restart sessions where issue status changed

## Config Schema Addition

```toml
[coordinator.vscodeclaude]
workspace_base = "C:\\Users\\Marcus\\Documents\\GitHub"
max_sessions = 3

[coordinator.repos.mcp_coder]
# Existing fields...
setup_commands_windows = ["uv venv", "uv sync --extra types"]
setup_commands_linux = ["uv venv", "uv sync --extra types"]
```

## Concurrency Note

**Warning**: Do not run multiple `vscodeclaude` commands concurrently. The session file (`vscodeclaude_sessions.json`) does not use file locking, so concurrent writes could result in lost session data.
