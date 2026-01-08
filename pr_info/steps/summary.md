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
├── define_labels.py      # CLI command with all logic (moved here)

tests/cli/commands/
├── test_define_labels.py # Tests (moved from tests/workflows/)

docs/getting-started/
├── LABEL_SETUP.md        # New consolidated documentation
```

### Design Decisions

1. **Single module approach**: All logic (`calculate_label_changes`, `apply_labels`, `resolve_project_dir`) lives in the CLI command module - no separate `label_sync.py` needed since there's no external reuse
2. **Reuse existing infrastructure**: `LabelsManager` and `label_config.py` already provide GitHub API and config handling
3. **Follow existing CLI patterns**: Mirror structure of `verify.py`, `commit.py` commands

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
| `README.md` | Add Setup section and command docs |
| `pr_info/DEVELOPMENT_PROCESS.md` | Update documentation link |

## Files to Delete

| File | Reason |
|------|--------|
| `workflows/define_labels.py` | Replaced by CLI command |
| `workflows/define_labels.bat` | No longer needed |
| `docs/configuration/LABEL_WORKFLOW_SETUP.md` | Replaced by new docs |
| `tests/workflows/test_define_labels.py` | Moved to new location |

## Implementation Steps Overview

1. **Step 1**: Create CLI command module with core logic
2. **Step 2**: Integrate command into CLI (main.py + help.py)
3. **Step 3**: Move and update tests
4. **Step 4**: Update documentation
5. **Step 5**: Remove old files and verify

## Acceptance Criteria

- [ ] `mcp-coder define-labels` syncs labels to GitHub repository
- [ ] `mcp-coder define-labels --dry-run` previews changes without applying
- [ ] `mcp-coder define-labels --help` shows command description and options
- [ ] `mcp-coder help` includes `define-labels` in command list
- [ ] All tests pass (unit + mocked integration)
- [ ] Documentation complete and cross-referenced
