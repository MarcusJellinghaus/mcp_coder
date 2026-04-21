# Step 2 — Relocate `label_config.py` to `config/` package + move tests

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Move `label_config.py` from `utils/github_operations/` to `config/` — it loads `labels.json` config, so it belongs next to the data it reads. Update all importers. Move the test file to match the new source structure.

## WHERE

- Move: `src/mcp_coder/utils/github_operations/label_config.py` → `src/mcp_coder/config/label_config.py`
- Move: `tests/workflows/test_label_config.py` → `tests/config/test_label_config.py`
- Create: `tests/config/__init__.py` (if not present)
- Modify: All files that import from `label_config` (update import paths)

## WHAT

No code changes to `label_config.py` itself — only move the file and update imports.

### Files that import from `label_config` (update all):

| File | Old import | New import |
|------|-----------|------------|
| `src/mcp_coder/cli/commands/define_labels.py` | `...utils.github_operations.label_config` | `...config.label_config` |
| `src/mcp_coder/cli/commands/set_status.py` | `...utils.github_operations.label_config` | `...config.label_config` |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | `....utils.github_operations.label_config` | `....config.label_config` |
| `src/mcp_coder/cli/commands/coordinator/core.py` | `....utils.github_operations.label_config` | `....config.label_config` |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | `...utils.github_operations.label_config` | `...config.label_config` |
| `src/mcp_coder/workflows/vscodeclaude/config.py` | `...utils.github_operations.label_config` | `...config.label_config` |
| `src/mcp_coder/utils/github_operations/issues/manager.py` | `..label_config` → `mcp_coder.config.label_config` |
| `tests/config/test_label_config.py` (relocated) | `mcp_coder.utils.github_operations.label_config` | `mcp_coder.config.label_config` |

### Test files that import from `label_config` (update all):

| File | Old import / mock target | New import / mock target |
|------|-------------------------|-------------------------|
| `tests/cli/commands/test_define_labels.py` | `mcp_coder.utils.github_operations.label_config.load_labels_config` (mock target) | `mcp_coder.config.label_config.load_labels_config` |
| `tests/cli/commands/test_define_labels_config.py` | `mcp_coder.utils.github_operations.label_config` | `mcp_coder.config.label_config` |
| `tests/cli/commands/test_define_labels_label_changes.py` | `mcp_coder.utils.github_operations.label_config` | `mcp_coder.config.label_config` |
| `tests/cli/commands/test_set_status.py` | lazy import of `mcp_coder.utils.github_operations.label_config` | `mcp_coder.config.label_config` |
| `tests/cli/commands/test_set_status_from_status.py` | lazy import of `mcp_coder.utils.github_operations.label_config` | `mcp_coder.config.label_config` |

**Note**: The import in `issues/manager.py` changes temporarily — that file will be deleted in Step 6.

**Note**: Several files have lazy imports of `label_config` functions inside function bodies (e.g., `get_labels_config_path` imported inline). These must also be updated:
- `src/mcp_coder/cli/commands/coordinator/core.py` — lazy imports at ~lines 196, 268
- `src/mcp_coder/workflows/vscodeclaude/config.py` — lazy import at ~line 27
- `src/mcp_coder/workflows/vscodeclaude/issues.py` — lazy import at ~line 31

## HOW

1. Copy `label_config.py` to `config/label_config.py`
2. Delete old `utils/github_operations/label_config.py`
3. Update all import paths in consumer files
4. Move test file to `tests/config/test_label_config.py`
5. Ensure `tests/config/__init__.py` exists
6. Update test imports

## ALGORITHM

No algorithm — file relocation + import path updates only.

## DATA

No data structure changes.

## Commit

```
refactor: move label_config to config package
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 2 from pr_info/steps/step_2.md.

Move label_config.py from utils/github_operations/ to config/. Update all import paths.
Move tests/workflows/test_label_config.py to tests/config/test_label_config.py.
Run all checks (pylint, mypy, pytest unit tests) after implementation.
```
