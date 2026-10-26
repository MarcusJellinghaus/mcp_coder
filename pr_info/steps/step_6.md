# Step 6 — Approval-persist tests → `test_app_pilot_approval_persist.py`

## LLM prompt
> Read `pr_info/steps/summary.md` ("Common rules") and this file, `pr_info/steps/step_6.md`. Implement step 6 only:
> move the persist tests and their helpers into the new file `tests/icoder/test_app_pilot_approval_persist.py` with
> `move_symbol`, in the exact order below. Fix imports, including the stale `_UNPARSEABLE_TOOL` import, add
> `pytestmark`, run the step's checks and make exactly one commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py`
- Destination (new): `tests/icoder/test_app_pilot_approval_persist.py`

## WHAT
These symbols move: 6 test functions (11 collected), the helpers `_runtime_info`, `_persist_app` and `_spy_runtime_rules`, and the constant `_UNPARSEABLE_TOOL`.
- 6a `["test_persist_choice_writes_the_rule_to_settings_local", "test_persist_choice_also_applies_the_runtime_rule", "test_persist_choice_resolves_pending_with_persist_scope", "test_persist_end_to_end_yields_always_after_reload", "test_unparseable_tool_name_is_never_written_to_disk", "test_persist_write_failure_degrades_to_a_session_grant"]`
- 6b' `["_persist_app", "_spy_runtime_rules"]`
- 6b'' `["_runtime_info"]`, alone (its only caller `_persist_app` has moved)
- 6c `["_UNPARSEABLE_TOOL"]`, alone and last

## HOW
- Delete the stale `from tests.icoder.test_app_pilot import _UNPARSEABLE_TOOL` left in the destination.
- Expected imports: `from __future__ import annotations`; `import json`; `from pathlib import Path`; `import pytest`;
  `AppCore`; `EventLog`; `RuntimeInfo`; `from mcp_coder.icoder.permissions.approval import ApprovalDecision`;
  `LangchainEnforcementGateway`; `load_permission_config`; `matches`;
  `from mcp_coder.icoder.permissions.model import Policy, Rule`; `resolve`; `FakeLLMService`; `ICoderApp`; `OutputLog`;
  `from tests.icoder.test_app_pilot import (_APPROVAL_TOOL, _RecordingEngine, _author_project_ask, _isolate_user_layer, _open_modal_and_press)`.
- Add `pytestmark = pytest.mark.textual_integration` below the import block.
- The `pytest.param(..., id=...)` parametrize (six ids) arrives unchanged.
- Remove whatever ruff `F401` reports in `test_app_pilot.py`.

## ALGORITHM
```
for call in [6a, 6b', 6b'', 6c]:
    dry run -> gate; real call
delete the stale _UNPARSEABLE_TOOL import; fix imports; add pytestmark
run the step checks
```

## DATA
- Collected: `test_app_pilot_approval_persist.py` gives **11**, `test_app_pilot.py` **22**, `tests/icoder/` equals the baseline recorded in step 1 (1062 on 2026-10-26).

## Commit
`test(icoder): split approval-persist pilot tests from test_app_pilot (#1323)`
