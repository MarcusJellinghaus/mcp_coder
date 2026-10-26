# Step 2 — Move the VSCode probes from `sessions.py` into `detection.py`

See [summary.md](./summary.md). Requires step 1 (the test split) to be committed. One commit.

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`), then do this step exactly.
> This is a pure source refactor for issue #1319: move the 14 probe symbols verbatim from `sessions.py` to `detection.py` with a single `mcp__mcp-tools-py__move_symbol` call (dry run first). Never move or edit code by hand. The only hand edits allowed are:
> - import statements
> - moving the `HAS_WIN32GUI` `try/except ImportError` guard verbatim
> - one `logger = logging.getLogger(__name__)` line in `detection.py`
> - reverting rope's `detection.<name>` qualifications in `sessions.py` back to bare names
> - test patch-target strings whose function moved (module segment only)
> - two stale-name docstring edits in `test_detection.py`
>
> Use MCP tools only. Run all checks listed below, then make one commit.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/sessions.py` (source of the move)
- `src/mcp_coder/workflows/vscodeclaude/detection.py` (destination)
- `src/mcp_coder/workflows/vscodeclaude/assessment.py` (import line only)
- `src/mcp_coder/workflows/vscodeclaude/__init__.py` (re-export blocks only)
- `tests/workflows/vscodeclaude/`: `test_detection_probes.py`, `test_sessions_active_fallback.py`, `test_sessions_pid_identity.py`, `test_sessions.py` (imports only), `test_detection.py` (docstrings only)

## WHAT
Symbols moved, unchanged, in this order and in **one** `move_symbol` call:
`VSCODE_PROCESS_NAMES`, `LAUNCH_GRACE_SECONDS`, `check_vscode_running`, `_vscode_process_cache`, `_get_vscode_processes`, `clear_vscode_process_cache`, `_vscode_window_cache`, `_vscode_pids_cache`, `_get_vscode_pids`, `_get_vscode_window_titles`, `clear_vscode_window_cache`, `is_vscode_window_open_for_folder`, `is_vscode_open_for_folder`, `get_pid_create_time`.

Their signatures stay as they are, e.g.:
- `check_vscode_running(pid: int | None, create_time: float | None = …) -> bool`
- `get_pid_create_time(pid: int) -> float | None`

`HAS_WIN32GUI` can't be passed to `move_symbol` because it is assigned inside a `try` block. Its guard block (sessions.py lines 20–27, including the comment line) is cut and pasted verbatim as an import edit.

## HOW
- `detection.py` header after the docstring, **exactly**:
  ```python
  import logging
  from dataclasses import dataclass
  from datetime import UTC, datetime
  from pathlib import Path
  from typing import Any

  import psutil

  from .types import DetectionSignals, VSCodeClaudeSession

  # Optional Windows-only imports for window title detection
  try:
      import win32gui
      import win32process

      HAS_WIN32GUI = True
  except ImportError:
      HAS_WIN32GUI = False

  logger = logging.getLogger(__name__)
  ```
  The moved block (wherever rope placed it, with its comments) comes next, then the existing code. `detection.py` must not import `sessions` in any form. Delete any unguarded `import win32gui` / `import win32process` lines rope added.
- `sessions.py` imports: `json`, `logging`, `re`, `from datetime import UTC, datetime`, `from pathlib import Path`, `from typing import Any, cast`, `from ...utils.user_app_data import get_user_app_data_dir`, `from .config import sanitize_folder_name`, `from .detection import (HAS_WIN32GUI, LAUNCH_GRACE_SECONDS, check_vscode_running, get_pid_create_time, is_vscode_open_for_folder, is_vscode_window_open_for_folder)`, `from .helpers import load_to_be_deleted`, `from .types import VSCodeClaudeSession, VSCodeClaudeSessionStore`.
  - No `psutil`, no guard block, no `from mcp_coder.workflows.vscodeclaude import detection`.
  - `logger = logging.getLogger(__name__)` stays.
- `sessions.py` call sites: turn every `detection.<name>` rope introduced back into the bare `<name>`. Expected in `is_session_active` (`LAUNCH_GRACE_SECONDS`, `is_vscode_window_open_for_folder`, `check_vscode_running`, `is_vscode_open_for_folder`) and `update_session_pid` (`get_pid_create_time`). Net diff on those lines: zero.
- `assessment.py`:
  - `from .detection import capture_detection_snapshot, gather_signals, get_pid_create_time`
  - `from .sessions import load_sessions, save_sessions`
- `__init__.py`:
  - The `# Detection (Windows / IO boundary)` block becomes `from .detection import (DetectionSnapshot, capture_detection_snapshot, check_vscode_running, clear_vscode_process_cache, clear_vscode_window_cache, gather_signals, is_vscode_open_for_folder, is_vscode_window_open_for_folder)`.
  - The `# Session management` block keeps `add_session, get_session_for_issue, get_sessions_file_path, load_sessions, remove_session, save_sessions, update_session_pid, warn_orphan_folders`.
  - `__all__` stays unchanged.
- Convert any absolute imports rope added in `src/` to the package's relative style.

## ALGORITHM
```
move_symbol(sessions.py -> detection.py, 14 symbols, dry_run=True) -> files touched must be exactly sessions/detection/assessment/__init__
move_symbol(same, dry_run=False)
cut the guard block from sessions.py and paste it into detection.py; add logger; fix src imports; revert detection.<name> call sites
re-point the test patch targets (bulk replace per file, see below) and the test imports
edit the two docstrings in test_detection.py; run_ruff_fix F401; run checks + audits; commit
```

## Procedure
1. **Before the move:** record `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/"])` as N.
2. **Move.** Dry run first.
   - If the dry run touches any file besides `sessions.py`, `detection.py`, `assessment.py` and `__init__.py`: write one line to `pr_info/.blocked.txt` and stop.
   - After the real move: if any comment block of a moved symbol stayed behind in `sessions.py` (the comments above `VSCODE_PROCESS_NAMES`, `LAUNCH_GRACE_SECONDS`, `_vscode_process_cache`, `_vscode_window_cache`, `_vscode_pids_cache`): write one line to `pr_info/.blocked.txt` and stop.
3. **Src imports and call sites** as in HOW.
   - If `sessions.py` then differs from `main` anywhere outside its import block, the guard block and the removed moved regions, and restoring the original text is not a pure revert: write one line to `pr_info/.blocked.txt` and stop.
4. **Test patch targets.** Change the module segment only, using `mcp__mcp-workspace__edit_file`:
   - `test_detection_probes.py`: one `replace_all` of `mcp_coder.workflows.vscodeclaude.sessions` → `mcp_coder.workflows.vscodeclaude.detection`. This covers all 37 targets, the method-local import in `TestWindowTitleMatching`, and the module-level import.
   - `test_sessions_pid_identity.py`: one `replace_all` of `vscodeclaude.sessions.psutil.` → `vscodeclaude.detection.psutil.` (6 targets). The `get_sessions_file_path` targets stay.
   - `test_sessions_active_fallback.py`, only inside the three window-title tests (`test_returns_false_on_non_windows`, `test_requires_both_issue_and_repo_in_title`, `test_does_not_match_title_without_bracket_prefix`):
     - one `replace_all` of `vscodeclaude.sessions._get_vscode_` → `vscodeclaude.detection._get_vscode_` (4 targets)
     - three single edits of `sessions.HAS_WIN32GUI` → `detection.HAS_WIN32GUI`
     - The other 6 `sessions.HAS_WIN32GUI` targets, all `session_has_artifacts` / `check_vscode_running` / `is_vscode_open_for_folder` / `update_session_pid` targets and the caplog logger names stay.
   - `test_sessions_active_grace.py`, `test_sessions_lookup.py`, `test_sessions.py`: no string edits.
5. **Test imports.** Re-point the moved names to `mcp_coder.workflows.vscodeclaude.detection`:
   - `test_sessions.py`: `check_vscode_running`
   - `test_sessions_pid_identity.py`: `check_vscode_running`
   - `test_sessions_active_fallback.py`: `is_vscode_window_open_for_folder`
   - `test_detection_probes.py`: already done by step 4
6. **`test_detection.py` docstrings:**
   - line 4: `sessions helpers, so no real VSCode is required.` → `detection helpers, so no real VSCode is required.`
   - line 80: `"""Stub check_vscode_running as imported into the detection module."""` → `"""Stub check_vscode_running in the detection module."""`
7. Run `run_ruff_fix(select=["F401"])`, then `run_format_code`.

## DATA
- **Collect counts:** same as step 1's table (23 / 7 / 10 / 5 / 7 / 16 / 13), and `tests/workflows/vscodeclaude/` equals N.
- **Patch-target audit** (`mcp__mcp-workspace__search_files`, glob `tests/**/*.py`):

  | Pattern | Expected hits |
  |---|---|
  | `vscodeclaude\.sessions\.(psutil\|_get_vscode\|win32gui\|win32process\|_vscode_\|VSCODE_PROCESS_NAMES\|LAUNCH_GRACE_SECONDS\|get_pid_create_time\|clear_vscode)` | 0 |
  | `vscodeclaude\.sessions\.HAS_WIN32GUI` | 11 (fallback 6, grace 5) |
  | `vscodeclaude\.detection\.HAS_WIN32GUI` | 12 (`test_detection_probes.py` 9, fallback 3) |
  | `vscodeclaude\.sessions` in `test_detection_probes.py` | 0 |

- **Re-export audit:** `search_files(pattern="from (mcp_coder\\.workflows\\.vscodeclaude)?\\.sessions import", context_lines=12)`. No hit may list any of the 14 moved names or `HAS_WIN32GUI`.

If any count or audit differs: write one line to `pr_info/.blocked.txt` and stop.

## Checks (all must pass before committing)
- `mcp__mcp-tools-py__run_format_code`, `run_ruff_check`, `run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`. If it reports `cyclic-import`: write one line to `pr_info/.blocked.txt` and stop.
- `mcp__mcp-tools-py__run_pytest_check`, fast unit run: `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `run_pytest_check(extra_args=["-q", <the 7 test files>])` → 81 passed. If a previously passing test fails: write one line to `pr_info/.blocked.txt` and stop. Don't add patches, fixtures or conftest entries.
- `mcp__mcp-tools-py__run_lint_imports_check`, `run_tach_check`, `run_vulture_check`
- `mcp__mcp-workspace__check_file_size`: passes, with no stale allowlist entries. `sessions.py` is about 365 lines, `detection.py` about 545.
- Compact diff (`mcp__mcp-workspace__git` `diff`, `compact=true`). It may contain only:
  - import changes
  - the 8-line guard block moved between files
  - the `logger` line
  - the 50 patch-target lines
  - the two `test_detection.py` docstring edits
  - moved-block summaries and blank-line hunks

  There must be **no** hunk inside `is_session_active` or `update_session_pid`.

## Commit
`refactor(vscodeclaude): move VSCode probes from sessions into detection (#1319)`
