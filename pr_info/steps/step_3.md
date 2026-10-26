# Step 3 — Cancel tests → `test_app_pilot_cancel.py`

## LLM prompt
> Read `pr_info/steps/summary.md` ("Common rules") and this file, `pr_info/steps/step_3.md`. Implement step 3 only:
> move the Escape, cancel and Ctrl+C tests plus `SlowLLMService` into the new file `tests/icoder/test_app_pilot_cancel.py`
> with `move_symbol`, in the order below. Fix imports, add `import pytest` + `pytestmark`, run the step's checks and
> make exactly one commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py`
- Destination (new): `tests/icoder/test_app_pilot_cancel.py`

## WHAT
These symbols move: 5 tests and the helper class `SlowLLMService`.
- 3a `["test_escape_cancels_streaming", "test_escape_when_idle_is_noop", "test_busy_indicator_resets_after_cancel", "test_session_preserved_after_cancel", "test_ctrl_c_does_not_quit"]`
- 3a' `["SlowLLMService"]`, alone

## HOW
- Both method-local `import time` lines stay inside their methods: `SlowLLMService.stream` and the function-local
  `SlowLLMServiceWithSession.stream`.
- Expected imports: `from __future__ import annotations`; `from collections.abc import Callable, Iterator`;
  `PermissionFrame`; `ICoderApp`; `BusyIndicator`; `OutputLog`; `StreamEvent`;
  `from tests.icoder.test_app_pilot import _submit_and_wait`.
- The moved code doesn't use `pytest`, so add `import pytest`, then `pytestmark = pytest.mark.textual_integration`
  below the import block. Never add a second `import pytest`.
- Remove whatever ruff `F401` reports in `test_app_pilot.py`.

## ALGORITHM
```
dry run 3a -> gate; real 3a
dry run 3a' -> gate; real 3a'
fix imports; add import pytest (if missing) + pytestmark
run the step checks
```

## DATA
- Collected: `test_app_pilot_cancel.py` gives **5**, `test_app_pilot.py` **71**, `tests/icoder/` equals the baseline recorded in step 1 (1062 on 2026-10-26).

## Commit
`test(icoder): split cancel pilot tests from test_app_pilot (#1323)`
