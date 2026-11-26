# Step 3 — Remove the pre-f626cf8 `.mcp-file-access` fallback

Read [summary.md](summary.md) first. One commit. Pure removal: no new behaviour, so no new
tests — delete the tests of the removed fallback first, then the code.

## LLM prompt

> Implement step 3 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_3.md`.
> Delete the fallback tests, then make the `mcp_coder.mcp_workspace` shim use plain imports
> and remove every `FILE_ACCESS_SUPPORTED` branch and the docs sentence about it. Run pylint,
> pytest (`-n auto`, fast unit markers), mypy, ruff, lint-imports, tach, vulture, deptry;
> format; commit.

## WHERE

- `src/mcp_coder/mcp_workspace.py`
- `src/mcp_coder/cli/commands/init_file_access.py`
- `src/mcp_coder/cli/commands/verify.py` (`_smoke_test_skip_reason`, imports)
- `src/mcp_coder/cli/commands/verify_sections.py` (`_file_access_row`, imports)
- `tests/cli/commands/test_init_file_access.py`
- `tests/cli/commands/test_verify_mcp_edit_smoke.py`
- `tests/cli/commands/test_verify_project_section.py`
- `docs/cli-reference.md` (init section)

## WHAT

### `src/mcp_coder/mcp_workspace.py`

```python
"""Wrapper for mcp-workspace file listing, gitignore and file access utilities."""

from mcp_workspace.file_tools.directory_utils import (
    FileAccess, get_file_access, is_path_gitignored, validate_access_rules,
)
from mcp_workspace.file_tools.directory_utils import list_files as _list_files
```

Delete `TYPE_CHECKING`, the `try/except ImportError` block, the `IntEnum` stand-ins and
`FILE_ACCESS_SUPPORTED` (also from `__all__`). Keep `list_files` and the step-2 formatter
re-exports.

### `init_file_access.py`

- Drop the `FILE_ACCESS_SUPPORTED` import.
- `_append_missing_rules`: always call `_warn_overridden_rules(project_dir, missing)`.
- `ensure_file_access_rules`: always validate (`if problems := validate_access_rules(...)`
  → `_invalid(...)`); delete the "does not support" warning branch and `supported`; the
  final return is `RulesOutcome(ok=True, changed=changed, skip_reason="")`. Remove the
  docstring sentence "Without `.mcp-file-access` support in mcp-workspace, rules are written
  without validation."

### `verify.py`

- Drop `FILE_ACCESS_SUPPORTED` and `is_path_gitignored` from the shim import.
- `_smoke_test_skip_reason`: delete the `if not FILE_ACCESS_SUPPORTED:` block; docstring
  "Honours `.mcp-file-access`." (drop "otherwise only gitignore counts"). Skip text
  `(see PROJECT)` is unchanged here (changes in step 4).

### `verify_sections.py`

- Drop the `FILE_ACCESS_SUPPORTED` import.
- `_file_access_row`: delete the `elif not FILE_ACCESS_SUPPORTED:` branch (the row itself is
  removed in step 4).

## HOW

`docs/cli-reference.md` init section, the `.scratch/` bullet: delete the sentence "Skipped
when mcp-workspace in the mcp-coder environment does not support `.mcp-file-access` (the rules
file is then written without validation)." Keep every "needs mcp-workspace ≥ `f626cf8`
wherever the MCP server runs" note (`docs/repository-setup/repo.md`, `README.md`,
`claude-code.md`).

## Tests

- `test_init_file_access.py`: delete `test_without_support_appends_but_never_ignores_scratch`,
  `test_without_support_creates_file` and class `TestShimFallback`; in
  `test_result_is_valid_and_scratch_writable` delete only the line
  `assert mcp_workspace.FILE_ACCESS_SUPPORTED is True`. Remove imports left unused
  (`types`, `importlib.util`, `sys`, `patch` — check each).
- `test_verify_mcp_edit_smoke.py`: delete `test_smoke_test_without_support_skips_when_gitignored`
  and `test_smoke_test_gitignore_check_error_without_support`.
- `test_verify_project_section.py::TestFileAccessRow`: drop the `supported` parameter, the
  `absent-unsupported` and `unsupported` cases, `_NOT_CHECKED` and the
  `verify_sections.FILE_ACCESS_SUPPORTED` patch.
- Final search of `src/`, `tests/`, `docs/` for `FILE_ACCESS_SUPPORTED`, `without_support`,
  `does not support .mcp-file-access` must find nothing.

## ALGORITHM

None.

## DATA

`RulesOutcome.skip_reason` is now only `""`, `"rules file invalid"` or `"rules file not written"`.
