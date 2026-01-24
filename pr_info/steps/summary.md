# Coordinator VSCodeClaude Command - Implementation Summary

## Overview

Add `mcp-coder coordinator vscodeclaude` command to manage multiple VSCode/Claude Code sessions for interactive workflow stages across repositories.

## Architecture / Design Changes

### New Files (Minimal Addition)

```
src/mcp_coder/cli/commands/coordinator/
├── vscodeclaude.py              # All business logic (single file)
└── vscodeclaude_templates.py    # Template strings only

tests/cli/commands/coordinator/
└── test_vscodeclaude.py         # All tests (single file)
```

### Modified Files

| File | Change |
|------|--------|
| `pyproject.toml` | Add `psutil` dependency |
| `src/mcp_coder/cli/main.py` | Add CLI parsers and routing |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Add command handlers |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Export new functions |

### Design Decisions

1. **Single module approach** - All logic in `vscodeclaude.py` (~600-800 lines) follows existing `core.py` pattern
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
| 1 | Dependencies & Config | `pyproject.toml`, types in `vscodeclaude.py` |
| 2 | Templates | `vscodeclaude_templates.py` |
| 3 | Session Management | `vscodeclaude.py` (load/save/check sessions) |
| 4 | Issue Selection | `vscodeclaude.py` (filtering, priority, GitHub username) |
| 5 | Workspace Setup | `vscodeclaude.py` (git, folders, files) |
| 6 | VSCode Launch | `vscodeclaude.py` (launch, banner) |
| 7 | CLI Integration | `main.py`, `commands.py`, `__init__.py` |
| 8 | Status & Cleanup | `vscodeclaude.py` (status display, cleanup logic) |

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
