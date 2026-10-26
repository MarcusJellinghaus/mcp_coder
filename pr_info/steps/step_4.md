# Step 4 — Content-unit tests → `test_app_pilot_content_units.py`

## LLM prompt
> Read `pr_info/steps/summary.md` ("Common rules") and this file, `pr_info/steps/step_4.md`. Implement step 4 only:
> move the F2/click tests, the clickable content-unit, `/display` and resume-divider tests plus `_make_click_tool_unit`
> into the new file `tests/icoder/test_app_pilot_content_units.py` with `move_symbol`, in the order below. Fix
> imports, add `pytestmark`, run the step's checks and make exactly one commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py`
- Destination (new): `tests/icoder/test_app_pilot_content_units.py`

## WHAT
These symbols move: 16 tests and the helper `_make_click_tool_unit`.
- 4a `["test_f2_with_no_content_is_silent_noop", "test_f2_opens_modal_for_last_unit", "test_double_click_emits_content_detail_opened_event", "test_single_click_emits_tool_tier_toggled_event", "test_user_input_creates_clickable_unit"]`
- 4a' `["_make_click_tool_unit"]`, alone (all of its callers 1005/1021/1039 have moved)
- 4b `["test_tool_block_creates_clickable_unit", "test_assistant_text_creates_clickable_turn", "test_last_unit_returns_most_recent_inserted_unit_dict_order", "test_cancel_synthesizes_cancelled_tool_unit", "test_same_tool_out_of_order_results_pair_by_run_id", "test_cancel_resolves_the_open_same_name_unit"]`
- 4c `["test_stream_done_clears_renderer_fifo", "test_banner_stays_on_append_text", "test_display_oneline_rebuilds_all_tool_units_as_oneline", "test_display_compressed_wipes_per_unit_overrides", "test_resumed_divider_is_not_a_unit"]`

## HOW
- Both function-local `from mcp_coder.icoder.core.commands.display import register_display` lines stay inside their tests.
- Expected imports: `from __future__ import annotations`; `import json`; `import logging`;
  `from collections.abc import Callable`; `from datetime import datetime`; `from pathlib import Path`; `import pytest`;
  `AppCore`; `EventLog`; `RuntimeInfo`; `FakeLLMService`; `ICoderApp`; `DetailModal`; `InputArea`;
  `from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog`;
  `from mcp_coder.utils.mcp_verification import MCPServerInfo`;
  `from tests.icoder.test_app_pilot import _submit_and_wait`.
- Add `pytestmark = pytest.mark.textual_integration` below the import block.
- Remove whatever ruff `F401` reports in `test_app_pilot.py`.

## ALGORITHM
```
for call in [4a, 4a', 4b, 4c]:
    dry run -> gate; real call
fix imports; add pytestmark
run the step checks
```

## DATA
- Collected: `test_app_pilot_content_units.py` gives **16**, `test_app_pilot.py` **55**, `tests/icoder/` **1062**.

## Commit
`test(icoder): split content-unit pilot tests from test_app_pilot (#1323)`
