# Step 2 — Streaming tests → `test_app_pilot_streaming.py`

## LLM prompt
> Read `pr_info/steps/summary.md` ("Common rules") and this file, `pr_info/steps/step_2.md`. Implement step 2 only:
> move the streaming, busy-indicator, tool-result-rendering and chat.txt tests plus `ErrorAfterChunksLLMService`
> into the new file `tests/icoder/test_app_pilot_streaming.py` with `move_symbol`, using the exact call order below.
> Fix imports, add `pytestmark`, run the step's checks and make exactly one commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py`
- Destination (new): `tests/icoder/test_app_pilot_streaming.py`

## WHAT
These symbols move: 19 test functions (20 collected) and the helper class `ErrorAfterChunksLLMService`.

Move calls (dry run each one right before its real call):
- 2a `["test_llm_streaming", "test_streaming_single_chunk_no_newline", "test_model_stream_slash_text_never_dispatches", "test_streaming_multi_chunk_no_newlines", "test_streaming_mid_newline", "test_streaming_multiple_newlines_in_chunk"]`
- 2b `["test_streaming_empty_text_delta", "test_streaming_chunk_ends_on_newline", "test_streaming_newline_only_chunk", "test_streaming_tail_shows_partial_during_stream"]`
- 2c `["test_streaming_error_mid_line", "test_busy_indicator_resets_on_stream_error"]`
- 2c' `["ErrorAfterChunksLLMService"]`, alone (both of its callers have moved)
- 2d `["test_streaming_back_to_back_no_leakage", "test_streaming_tool_event_mid_line", "test_busy_indicator_shows_ready_on_startup", "test_busy_indicator_shows_ready_after_streaming", "test_busy_indicator_shows_tool_name_during_tool_use"]`
- 2e `["test_tool_result_renders_plain_text_by_default", "test_tool_result_renders_plain_text_when_no_format", "test_chat_txt_mirrors_visible_conversation"]`

## HOW
- `_submit_and_wait` stays in the base file. The new file imports it.
- Expected imports in the new file: `from __future__ import annotations`; `from collections.abc import Callable, Iterator`;
  `from unittest.mock import MagicMock`; `import pytest`; `EventLog`; `from mcp_coder.icoder.permissions.model import PermissionFrame`;
  `ICoderApp`; `BusyIndicator`; `InputArea`; `OutputLog`; `StreamEvent`;
  `from tests.icoder.test_app_pilot import _submit_and_wait`.
- Add `pytestmark = pytest.mark.textual_integration` directly below the import block. Add `import pytest` only if it is missing.
- Remove the imports that ruff `F401` now reports in `test_app_pilot.py`.

## ALGORITHM
```
for call in [2a, 2b, 2c, 2c', 2d, 2e]:
    dry run -> gate; real call
fix imports in both files; add pytestmark
run the step checks
```

## DATA
- Collected: `test_app_pilot_streaming.py` gives **20**, `test_app_pilot.py` **76**, `tests/icoder/` **1062**.

## Commit
`test(icoder): split streaming pilot tests from test_app_pilot (#1323)`
