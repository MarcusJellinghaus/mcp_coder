# Summary — Split `test_status_display.py` into concern-focused files (#438)

## Goal

Split the oversized test file
`tests/workflows/vscodeclaude/test_status_display.py` (~2176 lines, ~2.9× the
750-line hard limit) into 7 smaller, concern-focused files. This is a
**test-only ("orphan test") split**: the source module
`src/mcp_coder/workflows/vscodeclaude/status.py` is already under the limit and
**must not be touched**.

It is a **pure mechanical move** — no test logic changes. The compact diff at
the end must contain only import changes and new/deleted file headers.

## Architectural / design changes

There are **no production architectural changes**. `status.py` is untouched, so
there is **no source split**, **no `.importlinter` sub-layer work**, and no
change to any public API.

The only structural change is to the **test layout**:

- Two shared test helpers move from the test module into the directory's
  existing `conftest.py`, matching its established pattern (it already hosts
  directly-imported `make_*` builders *and* the auto-discovered
  `mock_vscodeclaude_config` fixture):
  - `_build_assessment` — plain function, **imported directly** by the files
    that need it.
  - `mock_status_checks` — pytest fixture, **auto-injected** via conftest
    discovery (no import needed by consumers).
- The 9 test classes are distributed across 7 files, one concern each. The kept
  file retains the original name.

### Target file map

| File | Class(es) | Source lines (original) | ~lines |
|------|-----------|-------------------------|--------|
| `test_status_display.py` (kept) | `TestStatusDisplay` | 120–583 | ~470 |
| `test_status_display_assessment_consumer.py` | `TestStatusAssessmentConsumer` | 2033–2176 | ~145 |
| `test_status_display_closed_prefix.py` | `TestClosedIssuePrefixDisplay` | 584–920 | ~340 |
| `test_status_display_delete_actions.py` | `TestBotStageSessionsDeleteAction`, `TestPrCreatedSessionsDeleteAction`, `TestDisplayStatusTableSoftDelete` | 921–1505 | ~585 |
| `test_status_display_branch_indicators.py` | `TestDisplayStatusTableBranchIndicators` | 1506–1755 | ~250 |
| `test_status_display_zombie.py` | `TestZombieSessionDisplay` | 1756–1889 | ~135 |
| `test_status_display_scenario.py` | `TestScenarioACrossModule` | 1890–2032 | ~145 |

## Folders / modules / files created or modified

**Modified:**
- `tests/workflows/vscodeclaude/conftest.py` — add `_build_assessment` +
  `mock_status_checks` (and their imports).
- `tests/workflows/vscodeclaude/test_status_display.py` — trimmed to
  `TestStatusDisplay` only; helpers removed; `_build_assessment` imported from
  conftest.
- `.large-files-allowlist` — remove the
  `tests/workflows/vscodeclaude/test_status_display.py` entry (closure gate).

**Created:**
- `tests/workflows/vscodeclaude/test_status_display_assessment_consumer.py`
- `tests/workflows/vscodeclaude/test_status_display_closed_prefix.py`
- `tests/workflows/vscodeclaude/test_status_display_delete_actions.py`
- `tests/workflows/vscodeclaude/test_status_display_branch_indicators.py`
- `tests/workflows/vscodeclaude/test_status_display_zombie.py`
- `tests/workflows/vscodeclaude/test_status_display_scenario.py`

**Untouched (explicitly):**
- `src/mcp_coder/workflows/vscodeclaude/status.py`
- `.importlinter` / `tach.toml`

## Shared import header (reference)

The original module-level imports, copied verbatim into each new file before
pruning:

```python
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.assessment import IssueFacts, assess_session
from mcp_coder.workflows.vscodeclaude.status import (
    check_folder_dirty,
    display_status_table,
    get_issue_current_status,
    get_next_action,
    is_issue_closed,
    is_session_stale,
)
from mcp_coder.workflows.vscodeclaude.types import (
    DetectionSignals,
    SessionAction,
    SessionAssessment,
    VSCodeClaudeSession,
)
```

Each new file additionally gets
`from tests.workflows.vscodeclaude.conftest import _build_assessment`.

## KISS: import handling

Do **not** hand-craft a minimal import subset per file. Instead:

1. Copy the full header verbatim into each new file.
2. Run `mcp__mcp-tools-py__run_ruff_fix(select=["F401"])` to auto-remove unused
   imports across all files.

The project's default ruff config only enables docstring rules and
`run_format_code` (isort+black) does **not** strip unused imports, so the
explicit `select=["F401"]` override is the deterministic lever. This removes the
only step that would otherwise need per-file human judgment.

Note the `ruff_fix(select=["F401"])` pruning of the *original*
`test_status_display.py` is expected to churn across steps 1–7 as classes leave
and the file keeps shrinking — it is **not** a one-shot cleanup finished in
Step 1. Each step re-runs F401 on the files it touches (original + newly
extracted), so imports left unused by that step's removal are pruned then.

## TDD note (test-only refactor)

Classic red-green TDD does not apply — there is no production code to drive out;
the tests *are* the artifact being moved. The equivalent discipline here is:
**every step keeps the full test suite green and passes all checks, as exactly
one commit.** Because each moved class stays collected (just from a new file),
`pytest` is green after every step.

## Ordering constraints (correctness)

- **Helpers land in `conftest.py` before/with their removal from the original.**
  Step 1 does the add + remove + re-import atomically in one commit.
- **The `.large-files-allowlist` entry is removed in the same commit that brings
  the kept file under 750** (the final extraction, Step 7) — no window where the
  file is under-limit but still allowlisted, and no premature removal that would
  fail the file-size check.

## Per-step verification

After each step, run the relevant subset of:
`run_format_code`, `run_lint_imports_check`, `run_vulture_check`,
`run_pytest_check` (with `-n auto` and the unit-test marker exclusions),
`run_pylint_check`, `run_mypy_check`.

Vulture warnings for this file (e.g. unused attribute `return_value`,
`repo_url`) are pre-existing and simply travel with the moved class bodies; for
this mechanical test-only move they are informational and **not** a blocking
gate — do not treat them as a step failure.

The final step additionally runs `mcp__mcp-workspace__check_file_size` and
`mcp-coder git-tool compact-diff` to prove the mechanical-move guarantee and the
under-750 result.

## Steps

1. `step_1.md` — Move shared helpers into `conftest.py`.
2. `step_2.md` — Extract `TestStatusAssessmentConsumer`.
3. `step_3.md` — Extract `TestClosedIssuePrefixDisplay`.
4. `step_4.md` — Extract the three delete-action classes.
5. `step_5.md` — Extract `TestDisplayStatusTableBranchIndicators`.
6. `step_6.md` — Extract `TestZombieSessionDisplay`.
7. `step_7.md` — Extract `TestScenarioACrossModule`, remove allowlist entry,
   final full verification.
