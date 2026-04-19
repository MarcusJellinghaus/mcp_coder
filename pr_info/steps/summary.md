# Issue #856: Make Python-specific implement steps configurable via pyproject.toml

## Problem

The `implement` workflow hardcodes Python-specific steps (black+isort formatting, mypy type checking) that don't apply to non-Python projects. These steps should be configurable so the workflow works for any project type.

## Design Changes

### New config layer in `pyproject_config.py`

Add `ImplementConfig` dataclass and `get_implement_config()` following the same pattern as existing `get_prompts_config()` and `get_github_install_config()`. Reads `[tool.mcp-coder.implement]` section with two boolean keys: `format_code` and `check_type_hints`, both defaulting to `false` (opt-in).

### Config propagation through implement workflow

Config is read **once** in `core.py` (`run_implement_workflow`) and passed as boolean parameters to `task_processing.py` functions. This gates four call sites:

| Call site | What it gates |
|-----------|--------------|
| `task_processing.py` → `process_single_task()` Step 7 | Per-task mypy |
| `task_processing.py` → `process_single_task()` Step 8 | Per-task formatting |
| `core.py` → `run_implement_workflow()` Step 5 | Final mypy check |
| `core.py` → `run_implement_workflow()` Step 5 | Formatting after final mypy |

### Verify command: new PROJECT section

Informational section showing Python auto-detection (based on `pyproject.toml` existence) and the two toggle values. Does not affect exit code.

### Relationship to `RUN_MYPY_AFTER_EACH_TASK`

The existing `RUN_MYPY_AFTER_EACH_TASK` constant controls *when* mypy runs (per-task vs once at end). The new `check_type_hints` controls *whether* it runs at all. `check_type_hints=false` skips mypy everywhere regardless of the constant.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/pyproject_config.py` | Add `ImplementConfig` dataclass + `get_implement_config()` |
| `src/mcp_coder/workflows/implement/task_processing.py` | Add `format_code`/`check_type_hints` params, gate Steps 7-8 |
| `src/mcp_coder/workflows/implement/core.py` | Read config once, pass booleans down, gate Step 5 |
| `src/mcp_coder/cli/commands/verify.py` | Add `_print_project_section()` |
| `pyproject.toml` | Add `[tool.mcp-coder.implement]` section |
| `tests/utils/test_pyproject_config.py` | Tests for `get_implement_config()` |
| `tests/workflows/implement/test_task_processing.py` | Tests for gating behavior |
| `tests/workflows/implement/test_core.py` | Tests for config read + propagation |
| `tests/cli/commands/test_verify.py` | Tests for PROJECT section output |

## Defaults & Breaking Change

Both `format_code` and `check_type_hints` default to `false`. Existing Python projects relying on automatic formatting/mypy must add the config section to re-enable. This is intentional per the issue requirements.
