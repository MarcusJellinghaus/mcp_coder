# Implementation Plan: Add `define-labels` CLI Command

## Summary

Move `workflows/define_labels.py` functionality into the `mcp-coder` CLI as a proper `define-labels` command, following the KISS principle by keeping all related code in a single command module.

## Goal

Enable users to sync GitHub workflow labels via:
```bash
mcp-coder define-labels [--project-dir PATH] [--dry-run]
```

## Architectural Changes

### Before
```
workflows/
├── define_labels.py      # Standalone script with all logic
├── define_labels.bat     # Windows batch wrapper
```

### After
```
src/mcp_coder/cli/commands/
├── define_labels.py      # CLI command with core logic (moved here)

tests/cli/commands/
├── test_define_labels.py # Tests (moved from tests/workflows/)

docs/getting-started/
├── LABEL_SETUP.md        # New consolidated documentation
```

### Design Decisions

1. **Import shared utilities**: `resolve_project_dir` is imported from `mcp_coder.workflows.utils` (not copied) to avoid code duplication
2. **Exception-based error handling**: Refactor `resolve_project_dir` and `apply_labels` to raise `ValueError` instead of calling `sys.exit(1)` - matches CLI pattern used by `resolve_execution_dir`
3. **Reuse existing infrastructure**: `LabelsManager` and `label_config.py` already provide GitHub API and config handling
4. **Follow existing CLI patterns**: Mirror structure of `verify.py`, `commit.py` commands
5. **Parent parser handles --log-level**: No `--log-level` on subparser (consistent with other commands)
6. **Config file fallback**: Keep existing behavior - tries local `workflows/config/labels.json` first, falls back to bundled package config

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/cli/commands/define_labels.py` | CLI command implementation |
| `tests/cli/commands/test_define_labels.py` | Unit and integration tests |
| `docs/getting-started/LABEL_SETUP.md` | Setup documentation |

## Files to Modify

| File | Changes |
|------|---------|
| `src/mcp_coder/cli/main.py` | Add subparser and command routing |
| `src/mcp_coder/cli/commands/help.py` | Add command to help text |
| `src/mcp_coder/workflows/utils.py` | Refactor `resolve_project_dir` to raise `ValueError` |
| `workflows/validate_labels.py` | Add try/except for `resolve_project_dir` |
| `tests/workflows/implement/test_core.py` | Update tests to expect `ValueError` |
| `README.md` | Add Setup section and command docs |
| `pr_info/DEVELOPMENT_PROCESS.md` | Update documentation link |
| `docs/configuration/CONFIG.md` | Update link to new documentation |

## Files to Delete

| File | Reason |
|------|--------|
| `workflows/define_labels.py` | Replaced by CLI command |
| `workflows/define_labels.bat` | No longer needed |
| `docs/configuration/LABEL_WORKFLOW_SETUP.md` | Replaced by new docs |
| `tests/workflows/test_define_labels.py` | Moved to new location |

## Implementation Steps Overview

1. **Step 1**: Create CLI command module with core logic; refactor `resolve_project_dir` to exceptions
2. **Step 2**: Integrate command into CLI (main.py + help.py)
3. **Step 3**: Move and update tests (minimal `TestExecuteDefineLabels`)
4. **Step 4**: Update documentation (including CONFIG.md and config location docs)
5. **Step 5**: Remove old files and verify

## Label Configuration

The command uses a two-location config system (documented in Step 4):

1. **Local override**: `project_dir/workflows/config/labels.json` - if exists
2. **Bundled fallback**: `mcp_coder/config/labels.json` - package default

This allows projects to customize labels while providing sensible defaults.

## Acceptance Criteria

- [ ] `mcp-coder define-labels` syncs labels to GitHub repository
- [ ] `mcp-coder define-labels --dry-run` previews changes without applying
- [ ] `mcp-coder define-labels --help` shows command description and options
- [ ] `mcp-coder help` includes `define-labels` in command list
- [ ] All tests pass (unit + mocked integration)
- [ ] Documentation complete and cross-referenced
- [ ] `resolve_project_dir` uses exception pattern (not `sys.exit`)
