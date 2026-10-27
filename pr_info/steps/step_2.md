# Step 2: Move `TestSoftDeleteAndRetry` → `test_cleanup_retry.py`; drop the allowlist entry

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. Step 1 is already committed.
> This is a pure refactoring: move code with `mcp__mcp-tools-py__move_symbol` only, and edit nothing by hand except imports and
> the `.large-files-allowlist` line. Use MCP tools only (no Bash). Produce exactly one commit.

## WHERE

- Source: `tests/workflows/vscodeclaude/test_cleanup.py`
- Destination (new): `tests/workflows/vscodeclaude/test_cleanup_retry.py`
- `.large-files-allowlist`: remove the line `tests/workflows/vscodeclaude/test_cleanup.py` (match it by path, not by line number)

## WHAT

- Move class `TestSoftDeleteAndRetry` (9 tests) verbatim, including all 7 **method-local**
  `from mcp_coder.workflows.vscodeclaude.helpers import (TO_BE_DELETED_FILENAME, load_to_be_deleted)` blocks.
- No new functions or signatures are introduced.

## HOW (integration: imports only)

End state of the imports in the new file `test_cleanup_retry.py`. There is **no** module-level `helpers` import.

```python
import shutil
from pathlib import Path

import pytest

from mcp_coder.utils.folder_deletion import DeletionResult
from mcp_coder.workflows.vscodeclaude.cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
)
from mcp_coder.workflows.vscodeclaude.types import SessionAction
from tests.workflows.vscodeclaude.test_cleanup import (
    _assessment,
    _patch_sessions_file,
    _session,
)
```

`test_cleanup.py` keeps its import block as it was after step 1. Every name in it is still used by the helpers, `TestCleanup` or
`TestCompositionScenarios`. Only remove a name if ruff F401 reports it.

## ALGORITHM

```
1. move_symbol(TestSoftDeleteAndRetry, dry_run=True) -> must list only the two files
2. move_symbol(TestSoftDeleteAndRetry) for real
3. Confirm all 7 method-local helpers imports are still inside their methods, verbatim
4. Fix the imports to the end state above, then remove the allowlist line
5. Run the checks and counts, then format and commit
```

## DATA (expected numbers)

- `test_cleanup.py` = 14, `test_cleanup_get_stale_sessions.py` = 6, `test_cleanup_retry.py` = 9 (total 29).
- `tests/workflows/vscodeclaude/` = the baseline N recorded in step 1 (≈680).
- Line counts: `test_cleanup.py` ≈ 528, `test_cleanup_retry.py` ≈ 350. All files are under 750.

## Preconditions / failure actions

For each condition below, write one line to `pr_info/.blocked.txt` and stop:
- The dry run lists any file other than the source and the destination.
- `move_symbol` raises `Token <…> cannot be matched`.
- `move_symbol` hoists, drops or rewrites any method-local `helpers` import. Move the class back with `move_symbol` first.
- `move_symbol` copies or moves a helper. Move the class back with `move_symbol` first.
- A collect count differs from the expected values, or a moved test fails.

## Verification (all MCP)

- `run_format_code`, `run_ruff_check` (F401 must be clean), `run_pylint_check`, `run_mypy_check`
- `run_pytest_check(extra_args=["--collect-only", "-q", <file>])` for each of the three files and for the directory → the counts above
- `run_pytest_check(extra_args=["-q", "tests/workflows/vscodeclaude/test_cleanup.py", "tests/workflows/vscodeclaude/test_cleanup_get_stale_sessions.py", "tests/workflows/vscodeclaude/test_cleanup_retry.py", "tests/workflows/vscodeclaude/test_status_display_scenario.py"])` → 30 passed
- Fast unit tests with `-n auto` and the CLAUDE.md marker exclusion
- `run_lint_imports_check`, `run_tach_check`, `run_vulture_check`
- `check_file_size` passes and reports no stale allowlist entries
- `git diff` against the base branch (compact) shows only these non-moved hunks:
  - the `get_stale_sessions` import removal
  - the headers and import blocks of the two new files
  - moved-block preview/summary lines
  - blank-line-only hunks
  - the one allowlist line

## Commit

`test(vscodeclaude): move TestSoftDeleteAndRetry to test_cleanup_retry.py (#1320)`
