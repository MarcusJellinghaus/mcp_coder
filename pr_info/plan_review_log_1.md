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

## Round 2 — 2026-04-28

**Findings**:
- F1 [critical, design] _format_freeform_row spec doesn't align with _format_row, contradicting the issue title and the Step 6 invariant.
- F2 [critical, correctness] Step 6 cross-section filter accepts pre-existing freeform indent-2 lines (Claude CLI:, Run with --debug, pip install, "uses Claude CLI" notice).
- F3 [improvement, correctness] ^  \[ regex over-skips real rows whose label or marker starts with [.
- F4 [improvement, accuracy] Plan says "extract _make_verify_mocks()" but the helper does not exist in test_verify_orchestration.py.
- F5 [critical, arithmetic] Value column is at index 32 (not 31); indent=4 rows are at 34 (not 33). Step 6 numbers are off by one.
- F6 [improvement, DRY] Install-hint indent hard-coded as 32; should derive from len(_format_row_prefix('', '', indent=2)).
- F7 [nit, clarity] Step 4 caller snippet missing outer if mcp_config_resolved: guard.
- F8 [nit, clarity] MCP CONFIG WARNINGS uses direct print (no textwrap.wrap); plan does not say so.
- F9 [nit, TDD] Step 3 tests don't pin an exact post-migration expected string for an installed-package row.
- F10 [nit, accounting] summary.md "10 distinct migration sites" claim is imprecise.

**Decisions**:
- F1: ask user (Q4 — design choice central to the issue).
- F2-F10: accept (mechanical fixes, formatting, DRY/TDD improvements).

**User decisions**:
- Q4 → C: Drop _format_freeform_row entirely. All label-less rows pass label="" to _format_row. KISS/DRY/YAGNI: a wrapper that delegates to _format_row(label="", ...) does not earn its own name once the layouts are identical.

**Changes**:
- summary.md: helpers list reverted to two (_format_row_prefix + _format_row); _format_freeform_row removed throughout; new derived constant _VALUE_COLUMN_INDENT added; "10 distinct migration sites" line dropped.
- step_1.md: _format_freeform_row removed (ALGORITHM, signature, tests); _format_row tests gain label="" parametrized case; install-hint pseudocode now uses _VALUE_COLUMN_INDENT; expected-string construction guidance added (derive, don't hand-count).
- step_3.md: pinned-string assertion added for an installed-package row.
- step_4.md: outer if mcp_config_resolved: guard restored in caller pseudocode; "direct print, no textwrap.wrap" note added.
- step_5.md: every _format_freeform_row(...) call rewritten as _format_row("", ...); MCP "server health check skipped" rewritten same way.
- step_6.md: cross-section invariant value-column index updated 31→32 and 33→34; ^  \[ regex tightened to line.strip() == "[Python]"; pre-existing freeform notice lines explicitly excluded; _make_verify_mocks() reworded as a new helper (not an extraction) with explicit mock list.

**Status**: pending commit
