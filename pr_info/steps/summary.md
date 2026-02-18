# Summary: Split `orchestrator.py` into Focused Modules

## Goal

Split `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` (~1,164 lines, in `.large-files-allowlist`) into smaller, single-responsibility modules. No logic changes — functions are moved as-is, only imports are adjusted.

---

## Architectural / Design Changes

### Before

```
vscodeclaude/
├── orchestrator.py       ← 1,164 lines; two distinct concerns + helper type + config fn + big docstring
├── config.py
├── types.py
├── cleanup.py
└── __init__.py
```

### After

```
vscodeclaude/
├── session_launch.py     ← NEW: launch_vscode, prepare_and_launch_session,
│                                process_eligible_issues, regenerate_session_files
├── session_restart.py    ← NEW: BranchPrepResult, _prepare_restart_branch,
│                                _build_cached_issues_by_repo, restart_closed_sessions,
│                                handle_pr_created_issues
├── config.py             ← UPDATED: receives _get_configured_repos()
├── types.py              ← unchanged
├── cleanup.py            ← UPDATED: import _get_configured_repos from config, not orchestrator
└── __init__.py           ← UPDATED: module docstring added, re-exports point to new modules
                             orchestrator.py deleted
```

### Design Decisions

| Decision | Rationale |
|---|---|
| `BranchPrepResult` stays in `session_restart.py` | Only used internally by `_prepare_restart_branch` + `restart_closed_sessions`, both of which live there. Moving it to `types.py` would be classification over practicality. |
| `_get_configured_repos` moves to `config.py` | Already used by `cleanup.py`; reads config — natural home alongside other config-reading functions. |
| Module docstring moves to `__init__.py` | Describes the whole vscodeclaude subsystem — package-level documentation. |
| No re-export shim in `orchestrator.py` | Per the refactoring guide: Clean Deletion, No Legacy Artifacts. |

### Import Dependency Flow (After)

```
session_restart.py
  └─imports─► session_launch.py   (regenerate_session_files, launch_vscode)
  └─imports─► config.py           (_get_configured_repos)
  └─imports─► types.py            (BranchPrepResult defined here)

cleanup.py
  └─imports─► config.py           (_get_configured_repos)   ← was orchestrator

__init__.py
  └─re-exports from session_launch + session_restart
```

---

## Files Created / Modified / Deleted

| File | Action |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | **CREATE** |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | **CREATE** |
| `src/mcp_coder/workflows/vscodeclaude/config.py` | **MODIFY** — add `_get_configured_repos` |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | **MODIFY** — add docstring, update re-exports |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | **MODIFY** — update import of `_get_configured_repos` |
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | **DELETE** |
| `.large-files-allowlist` | **MODIFY** — remove `orchestrator.py` entry |

### Test Files (existing — import paths need updating as out-of-scope follow-up)

| File | Status |
|---|---|
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | Patches `orchestrator.*` — will need updating in follow-up PR |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | Same |
| `tests/workflows/vscodeclaude/test_orchestrator_cache.py` | Same |
| `tests/workflows/vscodeclaude/test_orchestrator_regenerate.py` | Same |

> Test restructuring is explicitly out of scope per the issue. Tests will fail after Step 5 (deletion) until the follow-up PR addresses them.

---

## Implementation Steps Overview

| Step | Action | Files Touched |
|---|---|---|
| 1 | Create `session_launch.py` | new file |
| 2 | Create `session_restart.py` | new file |
| 3 | Move `_get_configured_repos` to `config.py`, update `cleanup.py` | config.py, cleanup.py |
| 4 | Update `__init__.py` re-exports + docstring | __init__.py |
| 5 | Delete `orchestrator.py`, update allowlist | orchestrator.py, .large-files-allowlist |
| 6 | Verify: lint-imports, tach check, pytest | — |
