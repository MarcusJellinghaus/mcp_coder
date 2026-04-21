# Issue #833 — Consume github_operations via shim + rebuild update_workflow_label (part 5 of 5)

## Goal

Replace `mcp_coder`'s local `utils/github_operations/` with a thin shim that imports from `mcp_workspace.github_operations`. Rebuild `update_workflow_label` as a standalone workflow function. Delete the local copy.

This is the final stage of a 5-issue cross-repo refactor. After this, there is exactly one copy of github_operations code (in mcp_workspace), and mcp_coder is a clean consumer.

## Architectural / Design Changes

### Before
```
mcp_coder.utils.github_operations/          ← Full local implementation
├── __init__.py                               (BaseGitHubManager, LabelsManager, etc.)
├── base_manager.py                           (PyGithub integration)
├── ci_results_manager.py                     (CI status checks)
├── github_utils.py                           (RepoIdentifier, parse_github_url)
├── labels_manager.py                         (Label CRUD)
├── label_config.py                           (labels.json loading)
├── pr_manager.py                             (PR operations)
└── issues/                                   (IssueManager with update_workflow_label)
    ├── manager.py                            (IssueManager class - owns update_workflow_label)
    ├── branch_manager.py, cache.py, ...
    └── types.py, labels_mixin.py, ...
```

All consumers import directly from `mcp_coder.utils.github_operations.*`.

### After
```
mcp_coder.mcp_workspace_github              ← Thin shim (re-exports from mcp_workspace)
mcp_coder.config.label_config               ← Relocated from utils/github_operations/
mcp_coder.workflow_utils.label_transitions   ← Standalone update_workflow_label function
```

- **Shim pattern**: `mcp_workspace_github.py` re-exports all GitHub classes/types from `mcp_workspace.github_operations` — same pattern as existing `mcp_workspace_git.py`.
- **`label_config.py`** moves to `config/` — it loads `labels.json` config, so it belongs next to the data it reads.
- **`update_workflow_label`** extracted from `IssueManager` method into a standalone function in `workflow_utils/label_transitions.py`. Takes `IssueManager` as a parameter instead of being a method on it.
- **Architecture boundary** enforced: only the shim may import from `mcp_workspace.github_operations`.

### Dependency flow change
```
Before: workflows → utils.github_operations → PyGithub/requests
After:  workflows → mcp_workspace_github (shim) → mcp_workspace.github_operations → PyGithub/requests
                  → workflow_utils.label_transitions → config.label_config
```

### Import linter changes
- New shim isolation contract for `mcp_workspace_github`
- `github_library_isolation` exception updated to shim
- `external_services` independence contract removed (github_operations deleted)
- `requests_library_isolation` exception updated to shim
- Layered architecture updated with shim in proper layer

### Tach changes
- `mcp_coder.mcp_workspace_github` added to `shim_workspace` layer
- Old `mcp_coder.utils.github_operations` no longer exists as a boundary

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/mcp_workspace_github.py` | Shim: re-exports from `mcp_workspace.github_operations` |
| `src/mcp_coder/workflow_utils/label_transitions.py` | Standalone `update_workflow_label` function |
| `src/mcp_coder/config/label_config.py` | Relocated from `utils/github_operations/` |
| `tests/test_mcp_workspace_github_smoke.py` | Smoke tests for shim imports |
| `tests/workflow_utils/test_label_transitions.py` | Migrated label update tests |
| `tests/config/test_label_config.py` | Relocated label config tests |
| `tests/config/__init__.py` | Package init (if not already present) |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/define_labels.py` | Import path update |
| `src/mcp_coder/cli/commands/set_status.py` | Import path update |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Import path update |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Import path update |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | Import path update |
| `src/mcp_coder/workflows/create_plan/core.py` | Import path + update_workflow_label call |
| `src/mcp_coder/workflows/create_plan/prerequisites.py` | Import path update |
| `src/mcp_coder/workflows/create_pr/core.py` | Import path + update_workflow_label call |
| `src/mcp_coder/workflows/implement/core.py` | Import path + update_workflow_label call |
| `src/mcp_coder/workflows/implement/ci_operations.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/config.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Import path update |
| `src/mcp_coder/__init__.py` | Import path update |
| `src/mcp_coder/checks/branch_status.py` | Import path update |
| `src/mcp_coder/checks/ci_log_parser.py` | Import path update (TYPE_CHECKING) |
| `src/mcp_coder/workflow_utils/failure_handling.py` | Import path + update_workflow_label call |
| `src/mcp_coder/workflow_utils/base_branch.py` | Import path update |
| `src/mcp_coder/cli/commands/gh_tool.py` | Import path update |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Import path update |
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | Import path update |
| `src/mcp_coder/utils/__init__.py` | Remove `github_operations` re-export |
| `.importlinter` | Architecture config updates |
| `tach.toml` | Architecture config updates |

**Note**: ~30 test files outside `tests/utils/github_operations/` also need import updates to use `mcp_coder.mcp_workspace_github` (covered in Step 4).

## Folders / Files Deleted

| Path | Notes |
|------|-------|
| `src/mcp_coder/utils/github_operations/` | Entire directory (all files + `issues/` subpackage) |
| `tests/utils/github_operations/` | Entire test directory (tests moved to mcp_workspace) |
| `tests/workflows/test_label_config.py` | Relocated to `tests/config/` |

## Implementation Steps Overview

| Step | Description | Commit message |
|------|-------------|----------------|
| 1 | Create shim + smoke tests | `feat: add mcp_workspace_github shim with smoke tests` |
| 2 | Relocate label_config.py + tests | `refactor: move label_config to config package` |
| 3 | Build label_transitions.py + migrate tests | `feat: rebuild update_workflow_label as standalone function` |
| 4 | Update all consumer imports to use shim | `refactor: switch github_operations imports to shim` |
| 5 | Update update_workflow_label call sites | `refactor: switch to standalone update_workflow_label` |
| 6 | Delete local github_operations + old tests | `refactor: delete local github_operations (now in mcp_workspace)` |
| 7 | Update .importlinter and tach.toml | `chore: update architecture configs for github shim` |

## Prerequisite

`mcp_workspace.github_operations` must be installed in the venv (from mcp_workspace `main` branch after issue ④). Verify at start of Step 1.
