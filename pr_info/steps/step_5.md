# Step 5 — Approval tests → `test_app_pilot_approval.py`

## LLM prompt
> Read `pr_info/steps/summary.md` ("Common rules") and this file, `pr_info/steps/step_5.md`. Implement step 5 only:
> move the approval tests and their single-destination helpers into the new file `tests/icoder/test_app_pilot_approval.py`
> with `move_symbol`, in the exact order below. Never move the shared approval helpers. Fix imports, including the
> stale `_LONG_CMD` import, add `pytestmark`, run the step's checks and make exactly one commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py`
- Destination (new): `tests/icoder/test_app_pilot_approval.py`

## WHAT
These symbols move: 16 test functions (22 collected), the helpers `_push_approval_modal`, `_approval_prompt_text` and
`_recording_app`, and the constant `_LONG_CMD`.
- 5a `["test_approval_request_pushes_the_modal", "test_cancel_stream_also_cancels_pending_approvals", "test_approval_modal_states_the_over_grant", "test_approval_modal_args_widget_holds_full_args", "test_approval_modal_shows_persist_target_and_summary", "test_approval_modal_choice_dismisses_with_decision"]`
- 5b `["test_approval_modal_cancel_dismisses_with_none", "test_approval_modal_ctrl_c_copies_and_does_not_dismiss"]`
- 5b' `["_push_approval_modal", "_approval_prompt_text"]` (helpers only)
- 5c `["test_approval_choice_resolves_pending_with_decision", "test_allow_once_writes_no_runtime_rule", "test_session_choice_writes_a_runtime_rule", "test_cancel_turn_cancels_and_never_resolves", "test_ctrl_c_does_not_cancel_the_turn"]`
- 5d `["test_session_grant_is_honoured_by_resolve", "test_session_grant_does_not_survive_a_reload", "test_replayed_log_pushes_no_approval_modal"]`
- 5d' `["_recording_app"]`, alone
- 5e `["_LONG_CMD"]`, alone and last

**These never move:** `_APPROVAL_TOOL`, `_approval_event`, `_RecordingEngine`, `_isolate_user_layer`, `_author_project_ask`,
`_open_modal_and_press`.

## HOW
- 5e leaves a stale `from tests.icoder.test_app_pilot import _LONG_CMD` in the destination. Delete it; this is an import-only edit.
- Expected imports: `from __future__ import annotations`; `from pathlib import Path`; `from typing import Any`; `import pytest`;
  `from textual.pilot import Pilot`; `from textual.widgets import Static, TextArea`; `AppCore`; `EventLog`;
  `from mcp_coder.icoder.permissions.approval import ApprovalDecision`; `LangchainEnforcementGateway`;
  `load_permission_config`; `matches`;
  `from mcp_coder.icoder.permissions.model import Matcher, PermissionConfig, Policy, Rule`; `resolve`; `FakeLLMService`;
  `ICoderApp`; `ApprovalModal`; `OutputLog`;
  `from tests.icoder.test_app_pilot import (_APPROVAL_TOOL, _RecordingEngine, _approval_event, _author_project_ask, _isolate_user_layer, _open_modal_and_press)`.
- Add `pytestmark = pytest.mark.textual_integration` below the import block.
- Both `parametrize` decorators (×5 and ×3) arrive unchanged.
- Remove whatever ruff `F401` reports in `test_app_pilot.py`. The shared helpers are still used by the siblings, so
  they don't count as unused.

## ALGORITHM
```
for call in [5a, 5b, 5b', 5c, 5d, 5d', 5e]:
    dry run -> gate; real call
delete the stale _LONG_CMD import; fix imports; add pytestmark
assert the 6 shared helpers are still defined in test_app_pilot.py (list_symbols), else write one line to pr_info/.blocked.txt and stop
run the step checks
```

## DATA
- Collected: `test_app_pilot_approval.py` gives **22**, `test_app_pilot.py` **33**, `tests/icoder/` **1062**.

## Commit
`test(icoder): split approval pilot tests from test_app_pilot (#1323)`
