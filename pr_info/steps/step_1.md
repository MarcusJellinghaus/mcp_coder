# Step 1: Move `TestGetStaleSessions` → `test_cleanup_get_stale_sessions.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> This is a pure refactoring: move code with `mcp__mcp-tools-py__move_symbol` only, and edit nothing by hand except imports.
> Use MCP tools only (no Bash). Produce exactly one commit.

## WHERE

- Source: `tests/workflows/vscodeclaude/test_cleanup.py`
- Destination (new): `tests/workflows/vscodeclaude/test_cleanup_get_stale_sessions.py`

## WHAT

- Move class `TestGetStaleSessions` (6 tests, currently starting at line 421) verbatim.
- No new functions or signatures are introduced.

## HOW (integration: imports only)

End state of the imports in the new file `test_cleanup_get_stale_sessions.py`:

```python
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.cleanup import get_stale_sessions
from mcp_coder.workflows.vscodeclaude.types import SessionAction
from tests.workflows.vscodeclaude.test_cleanup import (
    _assessment,
    _patch_sessions_file,
    _session,
)
```

End state of `test_cleanup.py`:
- `get_stale_sessions` is removed from the import list. It becomes
  `from mcp_coder.workflows.vscodeclaude.cleanup import cleanup_stale_sessions, delete_session_folder`.
- Everything else stays unchanged. That covers the module docstring, the other imports, all three helpers, and `TestCleanup`, `TestSoftDeleteAndRetry` and `TestCompositionScenarios`, which keep their order.

## ALGORITHM

```
1. Baseline: collect-only on test_cleanup.py and on tests/workflows/vscodeclaude/; run test_cleanup.py + test_status_display_scenario.py
2. move_symbol(TestGetStaleSessions, dry_run=True) -> must list only the two files
3. move_symbol(TestGetStaleSessions) for real
4. Fix imports to the end state above. If a name was imported via the package instead of the original module, rewrite it to the original module.
5. Run the checks and counts, then format and commit
```

## DATA (expected numbers)

- Baseline: `test_cleanup.py` = 29 collected; `tests/workflows/vscodeclaude/` = N (≈680, record the actual value); 30 passed.
- After the move: `test_cleanup.py` = 23, `test_cleanup_get_stale_sessions.py` = 6, directory = N.

## Preconditions / failure actions

For each condition below, write one line to `pr_info/.blocked.txt` and stop:
- The baseline collect count of `test_cleanup.py` is not 29, or the baseline run does not pass.
- The dry run lists any file other than the source and the destination.
- `move_symbol` raises `Token <…> cannot be matched`.
- `move_symbol` copies or moves a helper (`_session`, `_assessment`, `_patch_sessions_file`). Move the class back with `move_symbol` first.
- A collect count differs from the expected values, or a moved test fails.

## Verification (all MCP)

- `run_format_code`, `run_ruff_check` (F401 must be clean), `run_pylint_check`, `run_mypy_check`
- `run_pytest_check(extra_args=["--collect-only", "-q", <file>])` for each file and for the directory → the counts above
- `run_pytest_check(extra_args=["-q", "tests/workflows/vscodeclaude/test_cleanup.py", "tests/workflows/vscodeclaude/test_cleanup_get_stale_sessions.py", "tests/workflows/vscodeclaude/test_status_display_scenario.py"])` → 30 passed
- Fast unit tests with `-n auto` and the CLAUDE.md marker exclusion
- `git diff` (compact): only the import changes, the new file header/imports, and moved blocks

`.large-files-allowlist` is **not** changed in this step. `test_cleanup.py` is still over 750 lines (~860).

## Commit

`test(vscodeclaude): move TestGetStaleSessions to test_cleanup_get_stale_sessions.py (#1320)`
