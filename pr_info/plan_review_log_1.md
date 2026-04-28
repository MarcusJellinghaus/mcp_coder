# Plan Review Log — Run 1

Issue: #925 — feat(verify): align value column across rows regardless of marker presence
Branch: 925-feat-verify-align-value-column-across-rows-regardless-of-marker-presence
Started: 2026-04-28

## Round 1 — 2026-04-28

**Findings**:
- F1 [critical, design] textwrap.wrap prefix construction in Step 2 has a bug due to _format_row.rstrip() interaction.
- F2 [improvement, test-gap] _format_row.rstrip() may shift alignment-invariant tests when value is empty.
- F3 [improvement, test-gap] Step 6 cross-section invariant filter is fuzzy.
- F4 [improvement, test-gap] Step 4 Tests section misses test_verify_orchestration.py::TestMcpConfigWarnings.
- F5 [improvement, test-gap] Step 2 wrap test contingency is wishy-washy.
- F6 [improvement, requirements] _LABEL_WIDTH=22 silently overruns for MCP labels like "langchain-mcp-adapters / PYTHONPATH" (35 chars).
- F7 [nit, other] Step files reference stale verify.py line numbers.
- F8 [improvement, test-gap] Step 6 cross-section test underestimates execute_verify mocking burden.
- F9 [improvement, scope] Step 5 misses MCP "server health check skipped" fallbacks at verify.py:650-651, 666-668.
- F10 [nit, design] _format_section install-hint continuation indent (27 spaces) doesn't match the new value column (32).

**Decisions**:
- F1: ask user (Q1 — design choice for wrap prefix construction).
- F2, F3, F4, F5, F7, F9, F10: accept (straightforward improvements / formatting / test-gap fixes).
- F6: ask user (Q2 — overrun policy).
- F8: ask user (Q3 — test scope).

**User decisions**:
- Q1 → A: Add `_format_row_prefix` helper; compose `_format_row` on top of it (DRY/KISS/TDD wins).
- Q2 → B: Per-section dynamic width for MCP warnings; clamp >= _LABEL_WIDTH; cross-section invariant relaxes to "value column >= 31" for MCP section.
- Q3 → C: Both — per-formatter parameterized invariants (workhorse) plus one end-to-end smoke test through execute_verify; extract _make_verify_mocks() into shared conftest.py.

**Changes**:
- summary.md: helpers list now three helpers; constants subsection notes _LABEL_WIDTH is global minimum (MCP may widen); modified-files table adds test_verify_orchestration.py and conftest.py; migration-site count updated.
- step_1.md: introduces `_format_row_prefix`; `_format_row` defined as composition; docstring contract for value=""; install-hint indent bumped to 32; new prefix-length test added; pre-Step-1 line-number note.
- step_2.md: wrap prefix uses `_format_row_prefix`; wrap test math pinned at width=80 (32+48 budget); pre-Step-1 line-number note.
- step_3.md: pre-Step-1 line-number note (no other content changes).
- step_4.md: optional `label_width` kwarg threaded through helpers; per-section dynamic width for MCP warnings; tests now list test_verify_orchestration.py::TestMcpConfigWarnings (lines 1093, 1117-1120); per-section overrun assertion added; pre-Step-1 line-number note.
- step_5.md: fourth migration site added for "server health check skipped" fallbacks; pre-Step-1 line-number note.
- step_6.md: cross-section invariant filter now uses explicit allow-list (skip "=== " and "  [" lines, parse indent to 2 or 4); MCP section invariant relaxed to ">= 31"; test plan restructured to per-formatter invariants + one end-to-end smoke; _make_verify_mocks() extracted to shared conftest.py.

**Status**: pending commit
