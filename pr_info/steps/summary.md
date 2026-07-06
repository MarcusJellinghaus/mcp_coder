# Summary — Split `mlflow_logger.py` → extract `mlflow_verify.py`

**Issue:** #1030 (part of #353 — oversized-file inventory)
**Type:** Pure "Move, Don't Change" file split. No behavior changes.
**Process reference:** `docs/processes-prompts/refactoring-guide.md`

## Goal / Definition of Done

`src/mcp_coder/llm/mlflow_logger.py` is **807 lines** — over the 750-line CI hard
limit (`mcp-coder check file-size --max-lines 750`) and currently grandfathered
in `.large-files-allowlist`.

Done when **all** hold:

- The 5 standalone `verify_mlflow` functions live in a new sibling
  `src/mcp_coder/llm/mlflow_verify.py`.
- `mlflow_logger.py` is **under 750 lines** and **removed** from
  `.large-files-allowlist`.
- `verify_mlflow` remains in the top-level public API (`mcp_coder.__all__`).
- `compact-diff` shows **only** import changes and new/deleted file headers
  (proof nothing was modified during the move).
- ruff / format / lint-imports / vulture / pytest / pylint / mypy all clean.

## Architectural / Design Changes

This is a **mechanical relocation**, not a design change. The only structural
shift is a new same-layer sibling module inside the `llm` package:

```
src/mcp_coder/llm/
├── mlflow_logger.py   (keep)  is_mlflow_available, MLflowLogger, get_mlflow_logger   ~600 lines
└── mlflow_verify.py   (new)   verify_mlflow + 4 helpers                              ~215 lines
```

Rationale for the cut line:

- The 5 verify functions are **already standalone** — they never touch the
  `MLflowLogger` class. Their only in-package dependency is `is_mlflow_available`,
  which `mlflow_verify.py` imports back from `mlflow_logger.py`.
- This produces a **one-way sibling import** (`mlflow_verify → mlflow_logger`),
  so there is **no import cycle**.
- **Import-linter:** both files are the same layer within `llm`; no contract
  change is expected. (`mlflow_verify` importing a sibling is one-directional.)
- **No `MLflowLogger` decomposition.** The class is ~520 lines; extracting the
  verify block alone brings the file under 750. Decomposing the class would be a
  logic change and is explicitly out of scope.

### Reference-style decision (locked by the issue)

`mlflow_verify.py` imports the names it needs **directly** and calls them **bare**
(`from .mlflow_logger import is_mlflow_available`, then `is_mlflow_available()`),
exactly as the code reads today — **not** qualified module calls. This keeps
production code clean and is why the test `@patch` targets must be retargeted to
the new namespace (see below).

## Symbols moved (source: lines ~586–790 of `mlflow_logger.py`)

| Symbol | Kind |
|---|---|
| `_check_tracking_uri` | helper |
| `_probe_mlflow_connection` | helper |
| `_check_artifact_location` | helper |
| `_format_tracking_data` | helper |
| `verify_mlflow` | public API |

## Import split (both sides)

| Import | `mlflow_logger.py` (after) | `mlflow_verify.py` (new) |
|---|---|---|
| `os` | keep (class uses it) | **add** (verify uses it) |
| `datetime` (from `datetime`) | keep | **add** |
| `load_mlflow_config` | keep (`__init__`, `get_mlflow_logger`) | **add** |
| `sqlite3` | **remove** (now unused) | **add** |
| `PackageNotFoundError` | **remove** | **add** |
| `version as pkg_version` | **remove** | **add** |
| `validate_tracking_uri` | **remove** | **add** |
| `TrackingStats` | **remove** | **add** |
| `query_sqlite_tracking` | **remove** | **add** |
| `is_mlflow_available` | (defined here) | **add** `from .mlflow_logger import is_mlflow_available` |
| `Any` (from `typing`) | keep | **add** |

> Unused-import removal on the `mlflow_logger.py` side is done **manually via
> `edit_file`** — the six imports above (`sqlite3`, `PackageNotFoundError`,
> `version as pkg_version`, `validate_tracking_uri`, `TrackingStats`,
> `query_sqlite_tracking`) are each used ONLY by the moved functions, so deletion
> is precise. This cannot be delegated to `run_ruff_fix` (F401): this repo's
> `pyproject.toml` sets `[tool.ruff.lint] select = ["D", "DOC"]` (F401 not enabled)
> and `[tool.pylint.messages_control]` disables `W0611`, so no gate would catch a
> leftover dead import — it would ship silently. Run `run_format_code` afterward.
> (`run_ruff_fix` may still be run as a harmless extra, but it is NOT the removal
> mechanism.) Keep `os`, `datetime`, `load_mlflow_config`, `Any` — the class still
> uses them. Adding imports to the **new** file is manual.

Also: remove `"verify_mlflow"` from `mlflow_logger.py`'s `__all__`.

## Files created / modified

**Created**
- `src/mcp_coder/llm/mlflow_verify.py` — new sibling module (auto-created by `move_symbol`).
- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` — this plan.

**Modified**
- `src/mcp_coder/llm/mlflow_logger.py` — remove 5 functions + dead imports + `__all__` entry.
- `src/mcp_coder/__init__.py` — re-export repointed to `mlflow_verify` (auto by `move_symbol`); keep in `__all__`.
- `src/mcp_coder/cli/commands/verify.py` — import repointed (auto by `move_symbol`).
- `tests/llm/test_mlflow_verify.py` — import line + **51** `@patch` string literals retargeted `mlflow_logger.` → `mlflow_verify.`.
- `.large-files-allowlist` — remove the `src/mcp_coder/llm/mlflow_logger.py` line.

**Unchanged (verified)**
- `tests/test_module_exports.py` — imports via top-level `mcp_coder` namespace; no edit once `__init__.py` is repointed.
- `tests/cli/commands/test_verify*.py` — the ~130 `@patch("mcp_coder.cli.commands.verify.verify_mlflow")` targets stay valid (because `verify.py` still imports the name) and must **NOT** be edited. Only `tests/llm/test_mlflow_verify.py` is retargeted.

## Why a single step / single commit

This is one interdependent, atomic move. Any partial commit (e.g. moving the
functions without retargeting the test `@patch` strings, or without fixing
imports) leaves the tree in a **red** state — failing tests or lint. The
"one commit = tests + implementation + checks passing" rule therefore maps to
**exactly one step** here; there are no independent A/B/C parts to separate.

TDD note: the behavior is already fully covered by the existing
`tests/llm/test_mlflow_verify.py` (472 lines). The "test-first" discipline for a
pure move is: retarget those existing tests to the new namespace and use them as
the green/red safety net that proves the move preserved behavior.

## Verification gates (run once, at the end)

1. `mcp-coder git-tool compact-diff` — remaining diff is imports + file headers only.
2. `mcp__mcp-workspace__check_file_size` — `mlflow_logger.py` < 750 and off allowlist.
3. `run_format_code`, `run_ruff_check`, `run_lint_imports_check`, `run_vulture_check`.
4. `run_pytest_check` (fast unit subset), `run_pylint_check`, `run_mypy_check`.
5. Bash-only (no MCP equivalent): `./tools/tach_check.sh`.
