# Summary: Move branch_status to checks/ Package

## Issue
#351 — Refactor: Move `branch_status` module to `checks/` package

## Goal
Pure file move — no functional changes. Improves architectural consistency by co-locating
all check commands' backing logic under `checks/`, alongside `file_sizes.py`.

---

## Architectural / Design Changes

### Before
```
src/mcp_coder/
├── checks/
│   ├── __init__.py          (exports file_sizes symbols)
│   └── file_sizes.py
└── workflow_utils/
    ├── __init__.py          (exports branch_status symbols)
    └── branch_status.py     ← lives here

tests/
└── workflow_utils/
    └── test_branch_status.py
```

### After
```
src/mcp_coder/
├── checks/
│   ├── __init__.py          (unchanged — no new exports added)
│   ├── file_sizes.py
│   └── branch_status.py     ← moved here
└── workflow_utils/
    ├── __init__.py          (branch_status block removed)
    └── (branch_status.py deleted)

tests/
└── checks/
    ├── __init__.py          (unchanged)
    ├── test_file_sizes.py
    └── test_branch_status.py  ← moved here
```

### Design Decisions
- **No re-exports from old location** — hard move, callers update their imports directly.
- **No new exports in `checks/__init__.py`** — callers import directly from `mcp_coder.checks.branch_status`,
  consistent with the pattern established by `check_branch_status.py` command.
- `checks/` package is the home for modules backing CLI `check` subcommands.

---

## Files Created
| File | Action |
|---|---|
| `src/mcp_coder/checks/branch_status.py` | Created (copy of old file) |
| `tests/checks/test_branch_status.py` | Created (copy of old test, imports updated) |

## Files Modified
| File | Change |
|---|---|
| `src/mcp_coder/workflow_utils/__init__.py` | Remove branch_status imports and exports |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Update import path |
| `src/mcp_coder/workflows/implement/core.py` | Update import path |
| `tests/cli/commands/test_check_branch_status.py` | Update import path |
| `docs/architecture/architecture.md` | Update branch_status location reference |
| `tach.toml` | Add `mcp_coder.checks` to cli/workflows depends_on (if tach check fails) |
| `.importlinter` | Add `mcp_coder.checks` to layered contract (if lint-imports fails) |

## Files Deleted
| File | Action |
|---|---|
| `src/mcp_coder/workflow_utils/branch_status.py` | Deleted |
| `tests/workflow_utils/test_branch_status.py` | Deleted |

---

## Constraints
- Pure move only — zero logic changes inside `branch_status.py`
- No backward-compatible re-exports from old location
- `checks/__init__.py` gets no new exports
