# Plan Review Log — Issue #820 (Run 1)

**Issue:** icoder: generic tool output rendering with compact/full modes
**Branch:** 820-icoder-tool-output-still-wired
**Base:** main (up to date, CI passing)
**Scope:** Rewrite `_render_tool_output()` for generic JSON rendering, replace ToolStart inline/block fields with raw args dict + `format_tool_start()` helper, add compact/full mode support, delete `testdata/` folder.

**Plan files:**
- `pr_info/steps/summary.md`
- `pr_info/steps/step_1.md` — add rendering helper functions + tests
- `pr_info/steps/step_2.md` — rewrite `_render_tool_output()` + tests
- `pr_info/steps/step_3.md` — `ToolStart` raw args + `format_tool_start()` + app.py
- `pr_info/steps/step_4.md` — delete `testdata/` folder

TASK_TRACKER.md is empty — plan has not started execution. Full review covers all 4 steps.

## Round 1 — 2026-04-16

**Findings (from review subagent):**
- **Blocker:** Step 3 scope missing `src/mcp_coder/llm/formatting/formatters.py` and `tests/llm/formatting/test_formatters.py`. Two consumers use the fields/helpers Step 3 changes (`ToolStart.inline_args/block_args`, `_format_tool_args`). CI would break.
- Step 3 "ToolResult footer update" subsection is misleading — Before/After blocks identical.
- Step 3 missing explicit note that `_render_tool_output()` call inherits `full=False` default from Step 2.
- Step 1 `_render_output_value` dict-scalar pseudocode ambiguous about quoting; dict insertion-order contract not stated.
- Step 3 `TestFormatToolStart` needs a test proving block-arg insertion order is preserved.
- Step 4 (delete `testdata/`) is correctly sized as its own commit — no change.
- Minor nits skipped: testdata stale between Step 3 and Step 4, snapshot tests unaffected, constant naming.

**Decisions:**
- Accept all 7 straightforward improvements.
- Escalate 2 design questions to user (CLI rendered scope; `_format_tool_args` removal).
- Autonomous: keep current "truncated to {len(output_lines)}" footer — matches existing tests, no change.

**User decisions:**
- **CLI rendered format:** Align CLI with iCoder. `print_stream_event()` rendered branch calls `format_tool_start(action, full=False)` including the `├──` separator. Single unified rendering path.
- **CLI text format:** Replace `_format_tool_args` with `_render_value_compact`-based rendering inline in `formatters.py`; delete the helper.

**Changes (applied by engineer):**
- `pr_info/steps/summary.md` — added `formatters.py` + `test_formatters.py` to "Files Modified" (Step 3).
- `pr_info/steps/step_1.md` — dict insertion-order note; scalar pseudocode uses `json.dumps(value)`.
- `pr_info/steps/step_3.md` — expanded Goal list; added formatters.py WHAT section; removed misleading ToolResult subsection; added `full=False` default note; added `test_block_preserves_arg_order`.
- `pr_info/steps/Decisions.md` — new file logging all 9 Round 1 decisions.

**Status:** Changes committed (see commit agent). Loop back to Round 2.
