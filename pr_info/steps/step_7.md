# Step 7 — Shutdown tests → `test_app_pilot_shutdown.py`

## LLM prompt
> Read `pr_info/steps/summary.md` ("Common rules") and this file, `pr_info/steps/step_7.md`. Implement step 7 only:
> move the shutdown tests, `_ApprovalPendingLLMService` and `_QUIT_TIMEOUT` into the new file
> `tests/icoder/test_app_pilot_shutdown.py` with `move_symbol`, in the exact order below. Fix imports, including the
> stale `_QUIT_TIMEOUT` import, add `pytestmark`, run the step's checks and make exactly one commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py`
- Destination (new): `tests/icoder/test_app_pilot_shutdown.py`

## WHAT
These symbols move: 3 tests, the helper class `_ApprovalPendingLLMService` and the constant `_QUIT_TIMEOUT`.
- 7a `["test_quit_with_approval_pending_exits_and_unwinds_worker", "test_shutdown_guard_drops_every_ui_call_from_worker_tail", "test_shutdown_race_runtime_error_is_logged_not_propagated"]`
- 7a' `["_ApprovalPendingLLMService"]`, alone
- 7b `["_QUIT_TIMEOUT"]`, alone and last. Its three-line `#:` comment must arrive directly above it.

## HOW
- Delete the stale `from tests.icoder.test_app_pilot import _QUIT_TIMEOUT` left in the destination.
- The `# pylint: disable=broad-exception-caught` comments arrive verbatim.
- Expected imports: `from __future__ import annotations`; `import asyncio`; `import contextlib`; `import logging`; `import queue`;
  `import threading`; `from collections.abc import Callable, Iterator`; `import pytest`; `AppCore`; `EventLog`;
  `from mcp_coder.icoder.permissions.approval import ApprovalEngine`; `PermissionFrame`; `ICoderApp`; `StreamEvent`;
  `from tests.icoder.test_app_pilot import _submit_and_wait`.
- Add `pytestmark = pytest.mark.textual_integration` below the import block.
- Remove whatever ruff `F401` reports in `test_app_pilot.py`. It should now match the base-file import end state in
  issue step 9. In particular, `asyncio`, `contextlib`, `logging`, `queue`, `threading`, `datetime` and `MagicMock` are gone.

## ALGORITHM
```
for call in [7a, 7a', 7b]:
    dry run -> gate; real call
delete the stale _QUIT_TIMEOUT import; fix imports; add pytestmark
run the step checks
```

## DATA
- Collected: `test_app_pilot_shutdown.py` gives **3**, `test_app_pilot.py` **19**, `tests/icoder/` equals the baseline recorded in step 1 (1062 on 2026-10-26).

## Commit
`test(icoder): split shutdown pilot tests from test_app_pilot (#1323)`
