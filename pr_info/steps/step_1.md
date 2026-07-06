# Step 1 — Extract `mlflow_verify.py` (pure move, one commit)

> Read `pr_info/steps/summary.md` first. This step performs the entire split as
> one atomic commit. It is a **pure "Move, Don't Change"** refactor — do not alter
> any function body. The only allowed edits are moves, import statements, `__all__`
> entries, `@patch` target strings, and the allowlist line.

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/mlflow_verify.py` | **create** (via `move_symbol`) |
| `src/mcp_coder/llm/mlflow_logger.py` | modify (remove functions, dead imports, `__all__` entry) |
| `src/mcp_coder/__init__.py` | re-export repointed (auto) — keep `verify_mlflow` in `__all__` |
| `src/mcp_coder/cli/commands/verify.py` | import repointed (auto) |
| `tests/llm/test_mlflow_verify.py` | retarget import line + 51 `@patch` strings |
| `.large-files-allowlist` | remove `src/mcp_coder/llm/mlflow_logger.py` line |

## WHAT — symbols moved (verbatim, no body edits)

Move these 5 module-level functions from `mlflow_logger.py` to `mlflow_verify.py`:

```python
def _check_tracking_uri(uri: str) -> dict[str, Any]: ...
def _probe_mlflow_connection(uri: str, experiment_name: str) -> tuple[dict[str, Any], dict[str, Any]]: ...
def _check_artifact_location(path: str | None) -> dict[str, Any]: ...
def _format_tracking_data(stats: TrackingStats, since: datetime | None) -> dict[str, Any]: ...
def verify_mlflow(since: datetime | None = None) -> dict[str, Any]: ...
```

`is_mlflow_available`, `MLflowLogger`, `get_mlflow_logger` **stay** in `mlflow_logger.py`.

## HOW — integration points

1. **`mlflow_verify.py` imports** (add exactly what the moved code references):
   ```python
   import os
   import sqlite3
   from datetime import datetime
   from importlib.metadata import PackageNotFoundError
   from importlib.metadata import version as pkg_version
   from typing import Any

   from ..config.mlflow_config import validate_tracking_uri
   from ..utils import load_mlflow_config
   from .mlflow_db_utils import TrackingStats, query_sqlite_tracking
   from .mlflow_logger import is_mlflow_available   # one-way sibling import, no cycle
   ```
   The moved functions call these **bare** (`is_mlflow_available()`, `load_mlflow_config()`,
   `query_sqlite_tracking(...)`), matching how the code reads today. Do **not** convert to
   qualified `mlflow_logger.<name>()` calls.

2. **`mlflow_logger.py` cleanup:** after the move, let `run_ruff_fix` drop the now-unused
   imports (`sqlite3`, `PackageNotFoundError`, `pkg_version`, `validate_tracking_uri`,
   `TrackingStats`, `query_sqlite_tracking`). Manually remove `"verify_mlflow"` from its
   `__all__`. Keep `os`, `datetime`, `load_mlflow_config` — the class still uses them.

3. **`__init__.py`:** `move_symbol` repoints `from .llm.mlflow_verify import verify_mlflow`.
   Confirm `verify_mlflow` is still listed in `__all__` (public API stays stable).

4. **Test retarget** (`tests/llm/test_mlflow_verify.py`): a single
   `edit_file(replace_all=True)` — `old="mcp_coder.llm.mlflow_logger."` →
   `new="mcp_coder.llm.mlflow_verify."`. This fixes all 51 `@patch` decorator strings
   (`is_mlflow_available`, `load_mlflow_config`, `query_sqlite_tracking`,
   `_probe_mlflow_connection`) whose names now resolve in `mlflow_verify`'s namespace.
   The dotted-prefix match is safe: the `from ... import verify_mlflow` line uses
   `mlflow_logger import` (space, not dot) and is repointed separately by `move_symbol`.

## ALGORITHM — execution order

```
1. move_symbol(dry_run=True) the 5 functions  -> preview; confirm consumers repointed
2. move_symbol(execute)                        -> creates mlflow_verify.py, repoints __init__/verify.py
3. add the import block to mlflow_verify.py; remove "verify_mlflow" from mlflow_logger.__all__
4. run_ruff_fix                                -> auto-remove dead imports in mlflow_logger.py
5. edit_file(replace_all) the test @patch strings; confirm test import line repointed
6. delete the mlflow_logger.py line in .large-files-allowlist
7. verify gates (compact-diff, file-size, format/ruff/lint-imports/vulture, pytest/pylint/mypy, tach)
```

## DATA — no data-structure changes

None. `verify_mlflow` and its helpers return the same `dict[str, Any]` result
shapes (`{"ok": bool, "value": str, ...}`, `overall_ok`, etc.). This step moves
code only; return values, signatures, and semantics are identical.

## Definition of done for this step (single commit)

- [ ] `mlflow_verify.py` holds the 5 functions with correct imports; ruff/mypy clean.
- [ ] `mlflow_logger.py` < 750 lines, dead imports gone, `verify_mlflow` off its `__all__`.
- [ ] `verify_mlflow` still importable as `from mcp_coder import verify_mlflow`.
- [ ] All 51 `@patch` strings + the import in `test_mlflow_verify.py` point to `mlflow_verify`.
- [ ] `.large-files-allowlist` no longer lists `mlflow_logger.py`.
- [ ] `compact-diff` shows only import + file-header changes.
- [ ] format, ruff, lint-imports, vulture, pytest, pylint, mypy, tach all pass.
- [ ] Exactly one commit: move + imports + tests + allowlist, all green.

## LLM Prompt

```
Implement Step 1 of pr_info/steps/step_1.md (read pr_info/steps/summary.md first).

This is issue #1030: a PURE "Move, Don't Change" split of
src/mcp_coder/llm/mlflow_logger.py — extract the verify block into a new sibling
src/mcp_coder/llm/mlflow_verify.py. Do NOT modify any function body.

Do exactly this, in order, using MCP tools only:
1. mcp__mcp-tools-py__move_symbol(dry_run=True) to move these 5 functions from
   src/mcp_coder/llm/mlflow_logger.py to src/mcp_coder/llm/mlflow_verify.py:
   _check_tracking_uri, _probe_mlflow_connection, _check_artifact_location,
   _format_tracking_data, verify_mlflow. Review the preview, then execute it.
2. Add to mlflow_verify.py the import block listed under "HOW" in step_1.md,
   including `from .mlflow_logger import is_mlflow_available`. Keep the moved
   functions calling names bare (no `mlflow_logger.` qualification).
3. Remove "verify_mlflow" from mlflow_logger.py's __all__. Confirm
   src/mcp_coder/__init__.py re-exports verify_mlflow from mlflow_verify and
   still lists it in __all__.
4. Run mcp__mcp-tools-py__run_ruff_fix to drop the now-unused imports in
   mlflow_logger.py (sqlite3, PackageNotFoundError, pkg_version,
   validate_tracking_uri, TrackingStats, query_sqlite_tracking).
5. In tests/llm/test_mlflow_verify.py do ONE edit_file(replace_all=True):
   "mcp_coder.llm.mlflow_logger." -> "mcp_coder.llm.mlflow_verify." (fixes the 51
   @patch targets). Confirm the `from ... import verify_mlflow` line points to
   mlflow_verify.
6. Remove the `src/mcp_coder/llm/mlflow_logger.py` line from .large-files-allowlist.
7. Verify everything: mcp__mcp-workspace__check_file_size (mlflow_logger.py must be
   < 750 and off the allowlist), run_format_code, run_ruff_check,
   run_lint_imports_check, run_vulture_check, run_pytest_check
   (extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration
   and not claude_api_integration and not formatter_integration and not
   github_integration and not langchain_integration"]), run_pylint_check,
   run_mypy_check. Also run `./tools/tach_check.sh` and `mcp-coder git-tool
   compact-diff` via Bash — the compact diff must show only import/file-header
   changes. Fix any failures before finishing. This is ONE commit.
```
