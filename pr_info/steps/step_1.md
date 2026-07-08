# Step 1 — Move shared helpers into `conftest.py`

> Prompt: Implement Step 1 of `pr_info/steps/summary.md` (#438). This is a
> mechanical, test-only move — no test logic changes. Move the two shared
> helpers `_build_assessment` and `mock_status_checks` from
> `tests/workflows/vscodeclaude/test_status_display.py` into the existing
> `tests/workflows/vscodeclaude/conftest.py`, then update the original file to
> import `_build_assessment` from conftest. Keep the full suite green. Produce
> exactly one commit.

## WHERE

- Modify `tests/workflows/vscodeclaude/conftest.py` (append helpers).
- Modify `tests/workflows/vscodeclaude/test_status_display.py` (remove helpers,
  add conftest import). Original file still holds all 9 classes after this step.

## WHAT

Move verbatim into `conftest.py` (original lines 28–117):

```python
def _build_assessment(
    session: VSCodeClaudeSession,
    *,
    is_closed: bool = False,
    is_running: bool = False,
    is_dirty: bool = False,
    is_stale: bool = False,
    is_ineligible: bool = False,
    stale_target: str | None = None,
) -> SessionAssessment: ...

@pytest.fixture
def mock_status_checks() -> Any: ...
```

## HOW

- `conftest.py` needs these imports added (some already present — do not
  duplicate): `from pathlib import Path`, `from typing import Any` (present),
  `import pytest` (present), and from the vscodeclaude packages:
  `IssueFacts`, `assess_session` (from `.assessment`),
  `DetectionSignals`, `SessionAssessment`, `VSCodeClaudeSession` (from
  `.types`). `_build_assessment` calls `assess_session`; `mock_status_checks`
  calls `_build_assessment` directly (same module — no import).
- In `test_status_display.py`, delete both helper definitions and add:
  `from tests.workflows.vscodeclaude.conftest import _build_assessment`.
  The `mock_status_checks` fixture is now auto-discovered — no import needed.
- Preconditions to confirm (grep): `conftest.py` does not already define
  `_build_assessment` / `mock_status_checks`, and no sibling test file imports
  them from the old location. (Issue states they are used only by this file.)

## ALGORITHM

```
copy _build_assessment + mock_status_checks text into conftest.py
add any missing imports to conftest.py (Path, IssueFacts, assess_session,
    DetectionSignals, SessionAssessment, VSCodeClaudeSession)
delete both helpers from test_status_display.py
add `from ...conftest import _build_assessment` to test_status_display.py
run ruff_fix(select=["F401"]) to prune leftover unused imports
```

## DATA

No data-structure changes. `_build_assessment` returns `SessionAssessment`;
`mock_status_checks` returns a builder callable
`(session) -> dict[str, SessionAssessment]`.

## Checks (must pass → one commit)

`run_format_code`, `run_ruff_fix(select=["F401"])`, `run_lint_imports_check`,
`run_vulture_check`, `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`,
`run_pylint_check`, `run_mypy_check`. Verify with `compact-diff` that only
import/move changes appear.
