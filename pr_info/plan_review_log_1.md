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

## Round 3 — 2026-04-28

**Findings**:
- F1 [critical, correctness] Step 6 Layer 1 assertion (len(set(value_indices)) == 1) fails on mixed-indent formatters (_format_section: indent 2 + 4; _print_project_section: indent 2 + 4).
- F2 [major, correctness] Step 1 install-hint pseudocode uses print(...) but the surrounding _format_section builds a list (lines.append). Verbatim transcription would change behavior.
- F3 [minor, correctness] Step 6 cross-section filter excludes only [Python]; CONFIG section emits [mcp], [github], [jenkins], etc. Latent foot-gun if a future test mocks verify_config to return entries.
- F4 [nit, DRY] Step 6 Layer 2 hard-codes expected = 32/34 instead of deriving from _LABEL_WIDTH / _MARKER_SLOT_WIDTH or _VALUE_COLUMN_INDENT.
- F5 [nit, DRY/TDD] Step 1 TestFormatRowHelpers hand-writes literal 32 / 40 instead of deriving from constants — contradicts the plan's own derive-from-constants guidance.

**Decisions**:
- F1-F5: accept (mechanical / DRY / correctness fixes; no design choices).

**User decisions**:
- None this round.

**Changes**:
- step_1.md: install-hint pseudocode fixed (`print` → `lines.append`); TestFormatRowHelpers prefix-length and custom-label_width assertions derive expected from constants.
- step_6.md: Layer 1 ALGORITHM rewritten to group lines by indent before asserting per-indent column equality; Layer 2 generalizes the Python group-header filter to any `[name]` line; expected value column derived from _LABEL_WIDTH / _MARKER_SLOT_WIDTH (or `_VALUE_COLUMN_INDENT + (indent - 2)`).

**Status**: pending commit

## Round 4 — 2026-04-28

**Findings**:
- F1 [real, correctness] Step 6 Layer 1 indent-grouping does not filter install-hint continuation lines (indent=_VALUE_COLUMN_INDENT=32), causing spurious assertion failures on _format_section fixtures that include a failed entry with install_hint.
- F2 [nit, accuracy] Layer 1 bullet labels the MCP warnings render path as "_format_mcp_section (warnings render path)"; the warnings rendering is inline in execute_verify post-Step-4, not in _format_mcp_section.
- F3 [nit, completeness] Group-header regex does not allow hyphens; user-config section names like [my-section] would be misidentified as tabular rows.
- F4 [nit, clarity] _value_column_index helper is sketched ("use a regex or fixed offset") without a pinned definition.

**Decisions**:
- F1-F4: accept (mechanical correctness/clarity fixes; no design choices).

**User decisions**:
- None this round.

**Changes**:
- step_6.md: Layer 1 algorithm filters content_lines to only indent-2/4 tabular rows (excludes install-hint continuations); MCP CONFIG WARNINGS bullet relabeled with "(inline in execute_verify, post-Step-4 migration)" and tagged as per-section invariant; group-header regex character class extended to include hyphens; _value_column_index pinned to derived-from-constants definition with explicit docstring.

**Status**: pending commit

## Round 5 — 2026-04-28

**Findings**:
- F1 [critical, correctness] _value_column_index pinned in Round 4 is tautological: it derives `expected` from the same formula the assertion uses, so the test never catches drift. Test is a constants-consistency check, not an alignment-invariant check.
- F2 [broken-as-pinned, correctness] MCP CONFIG WARNINGS Layer-1 bullet asserts a per-section dynamic-width invariant, but the Layer 1 algorithm uses default label_width=_LABEL_WIDTH=22; the assertion would always pass or always fail vacuously.
- F3 [verified] Hyphen extension to group-header regex is safe — no ambiguity with [OK]/[WARN]/[ERR] markers due to `^  \[` anchor.
- F4 [verified] Layer 1 indent allow-list (2, 4) correctly excludes install-hint at indent=32 and accepts all real tabular rows.
- F5 [text-drift, same root as F1] Step 6 prose still describes _value_column_index as line-inspecting; pinned implementation is formula-only.
- F6 [implementer-divergence] Step 3 cross-row alignment test silently relies on Step 6's helper but doesn't say which one; without a concrete inspection helper, implementer would invent something different.

**Decisions**:
- F1, F2, F5, F6: accept (correctness fixes; Round 4's pinning hardened the wrong contract).
- F3, F4: verified resolved by Round 4; no change.

**User decisions**:
- None this round.

**Changes**:
- step_6.md: split `_value_column_index` into `_expected_value_column(indent, *, label_width)` (formula-derived expected column) AND `_assert_value_at_column(line, expected_col)` (line-inspecting boundary check); rewrote Layer 1 + Layer 2 algorithms to use both helpers (assertion now catches drift); removed MCP CONFIG WARNINGS bullet from Layer 1 (per-section dynamic-width invariant belongs in step_4.md unit tests); Layer 2 mocks _collect_mcp_warnings to return empty list to avoid asserting on dynamic-width section.
- step_3.md: cross-row alignment test now uses _assert_value_at_column from shared conftest; expected column derived from constants.
- summary.md: tests/cli/commands/conftest.py hosts both _make_verify_mocks() and _assert_value_at_column / _expected_value_column.

**Status**: pending commit

## Round 6 — 2026-04-28

**Findings**:
- F1 [real, sequencing] step_3.md imports _assert_value_at_column from conftest.py and says "introduced by Step 6" — but Step 3 lands BEFORE Step 6, so the import would fail at Step 3 commit time.
- F2 [nit, symmetry] Step 3 hand-derives expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1 instead of calling _expected_value_column(indent=2) — minor consistency drift with Step 6.
- F3 [real, fixture composition] _make_verify_mocks() patches verify_github but conftest.py already has an autouse _mock_verify_github fixture; double-patching is fragile and the plan is silent on the overlap.
- F4 [nit, defensive] _assert_value_at_column reads line[expected_col - 1] without guarding expected_col >= 1; Python's negative-index wraparound would silently read the last char of the line.

**Decisions**:
- F1, F3: accept (real correctness issues — sequencing bug + fixture conflict).
- F2, F4: accept (small consistency / defensive-coding fixes).

**User decisions**:
- None this round.

**Changes**:
- step_3.md: introduces _expected_value_column and _assert_value_at_column in tests/cli/commands/conftest.py (moved from Step 6); cross-row alignment test now calls _expected_value_column(indent=2) instead of hand-deriving; helper guards expected_col >= 1.
- step_6.md: removes helper definitions (now reuses Step 3's); _make_verify_mocks() patch list no longer includes verify_github (already covered by autouse _mock_verify_github fixture); explicit note about composition with existing autouse fixtures.
- summary.md: tests/cli/commands/conftest.py row split: Step 3 hosts alignment helpers; Step 6 adds _make_verify_mocks().

**Status**: pending commit

## Round 7 — 2026-04-28

**Findings**: none (BLOCKING-ONLY review).
**Decisions**: n/a — no plan changes.
**User decisions**: none.
**Changes**: none.
**Status**: plan ready for implementation.

## Final Status

- Rounds run: 7 (Round 7 produced zero plan changes — loop terminated).
- Commits produced this review:
  1. c2aa092 — round 1 (10 findings, 3 user decisions: Q1=A, Q2=B, Q3=C)
  2. 9cc29d7 — round 2 (10 findings, 1 user decision: Q4=C)
  3. 26aa527 — round 3 (5 findings, no user decisions)
  4. 39fa662 — round 4 (4 findings, no user decisions)
  5. b22ed1e — round 5 (6 findings, no user decisions)
  6. a57c17b — round 6 (4 findings, no user decisions)
  7. (this commit) — round 7 + final status (zero findings, log close-out only)
- Total user decisions: 4 (Q1=A composition pattern; Q2=B per-section dynamic width for MCP warnings; Q3=C both per-formatter invariants + smoke test; Q4=C drop _format_freeform_row).
- Plan is ready for approval / implementation. The 6 step files (step_1 … step_6) and summary.md are internally consistent and have been verified to satisfy: imports/helpers/fixtures resolve at each step's commit time; no tautological assertions; full migration coverage of verify.py tabular rows; alignment invariant testable via _expected_value_column + _assert_value_at_column helpers introduced in Step 3 and reused in Step 6.
