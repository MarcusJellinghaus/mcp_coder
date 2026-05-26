# Plan Review Log — Issue #629

**Issue:** iCoder: tiered tool display with click-to-toggle, detail modal, and Response typed-action refactor
**Branch:** `629-icoder-tiered-tool-display-with-click-to-toggle-detail-modal-and-response-typed-action-refactor`
**Base branch:** `main` (rebased fresh, pushed)
**Plan files:** `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_10.md`
**Prior implementation progress:** None (TASK_TRACKER.md is empty — all 10 steps pending)

## Round 1 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: Step 1 dispatch ordering between `AppCore` side effects (rotate event log, emit session_start) and UI action iteration is ambiguous.
- Critical: Tool render model inconsistent between steps 5/6/9 — `append_unit` writes atomic entry, `extend_open_unit` later appends per-line entries → on rebuild, tool body would render twice.
- Critical: `last_unit()` returns dict-insertion-order last, which after a mid-turn tool is the tool, not the turn — F2 opens the tool's modal mid-stream.
- Critical: Step 2 references `on_tool_error` event kind, which is not a standard langchain `astream_events` event. The correct path is `on_tool_end` with `ToolMessage.status == "error"`.
- Improvement: `Response(actions=())` empty tuple is the new "do nothing" sentinel — document it.
- Improvement: Rename `clear_recorded()` to `clear_state()` (or split) — it now wipes far more than `_recorded`.
- Improvement: Extract `format_tool_compressed(start, result) -> list[str]` into `stream_renderer.py` (alongside `format_tool_start`, `format_tool_oneline`). Step 6 and step 9 both reference it.
- Improvement: Drop dead `* 1` in step 7's `"\n\n─" * 1`.
- Improvement: `OutputLog` reaching `self.app._core.event_log` is a layering violation. Use `on_unit_event` callback parameter on `OutputLog.__init__` (matches existing `mirror` pattern).
- Improvement: Add a 5-line Textual API spike to step 8 — verify `event.y + scroll_offset.y` resolves to the correct `self.lines` index before authoring 10 click tests. Prefer `event.style.meta` if it exposes unit_id directly.
- Improvement: Step 9's `_open_tool_units: deque[str]` should be `dict[str, deque[str]]` keyed by raw tool name to match the renderer's per-name positional FIFO.
- Improvement: Step 9 — spell out replay timestamp policy (use event `t` offset; document as approximate).
- Improvement: Step 10 — add explicit "regenerate & visually inspect SVGs" note for snapshot tests.
- Improvement: Document in `summary.md` that `last_unit()` returns dict-insertion-order last (intentional for F2).
- Skip: pre-existing empty `commands/__init__.py` — not in scope.

**Decisions (supervisor):**
- All Improvements: accept and instruct `/plan_update`.
- Critical items: items #1 (dispatch ordering), #3 (`last_unit()` documentation), #4 (langchain event kind) → autonomous fixes. Item #2 (tool render model) → escalated to user as design question.
- Four design questions escalated to user (see below).

**User decisions:**
- **Q1 — `parent_id` field on `ContentUnit`:** **Keep** (per issue Decision). One nullable field, always `None` in v1, reserved for v2 nesting. Overrides the plan's "Simplifications adopted" drop.
- **Q2 — Detail modal close keys:** **Both Escape and Enter** (per issue). Modal's `Enter` binding gets `priority=True` to override `TextArea` default handling.
- **Q3 — Tool unit render model:** **Atomic**. `append_unit` writes one `(unit_id, None)` script entry on `tool_use_start`. When `tool_result` arrives, `update_unit_and_rerender(unit_id, ...)` replaces unit fields and re-renders. `extend_open_unit` is for assistant turns only and raises `ValueError` if called for a tool unit.
- **Q4 — Step 1 commit size:** **Single commit** per project rule (one step = one commit = one context window). No dual-path bridge.

**Changes:**
- `summary.md` — removed `parent_id`-drop simplification row; added `parent_id` to ContentUnit schema; added `last_unit()` semantics note; updated langchain wording to `on_tool_end` detection; updated modified-files rows for output_log/stream_renderer.
- `step_1.md` — added `Response(actions=())` empty-tuple sentinel docstring note; added dispatch-ordering paragraph (AppCore mutates state before returning; UI iterates actions in tuple order).
- `step_2.md` — replaced fictional `on_tool_error` with `on_tool_end` + `ToolMessage.status == "error"` detection; added required 5-line langchain spike before implementation.
- `step_5.md` — kept `parent_id` field (per user decision); made tools atomic (`extend_open_unit` raises `ValueError` for tool kind); added `update_unit_and_rerender(...)` helper; renamed `clear_recorded()` to `clear_state()` (now wipes `_tool_tier_overrides` too); 3 new TDD tests.
- `step_6.md` — added `format_tool_compressed(start, result) -> list[str]` to `stream_renderer.py`; `_render_unit_atomic` produces start lines always + body only when `unit.output` is set; 3 new stream-renderer tests.
- `step_7.md` — added `priority=True` to Enter binding (per user decision); dropped dead `* 1` multiplier in `build_detail_text`.
- `step_8.md` — added `on_unit_event` callback param to `OutputLog.__init__` (mirrors `mirror` callback pattern); removed direct `self.app._core.event_log` access; added Textual API click-coord spike at top of HOW.
- `step_9.md` — converted tool result handling to atomic via `update_unit_and_rerender` (no more `extend_open_unit` for tool body, fixes double-render bug); `_open_tool_units` keyed as `dict[str, deque[str]]` per tool name; replay timestamp formula `session_start + timedelta(seconds=event['t'])` documented as approximate.
- `step_10.md` — added mandatory visual SVG inspection rule for snapshot tests (no auto-bless via `--snapshot-update`).
- `step_3.md`, `step_4.md` — no changes needed (none of the 15 change items targeted these steps).

**Status:** committed (Round 1 plan changes)

## Round 2 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: `ToolResult` missing `raw_name` field — step 9's per-tool-name FIFO (`_open_tool_units: dict[str, deque[str]]`, keyed by raw name) cannot resolve from a `ToolResult` action that only carries the display name. Both live result branch and `cleanup_pending()`-synthesized results lack raw-name info. FIFO lookup silently fails or matches the wrong unit.
- Critical: `_render_unit_atomic` reconstruction of `ToolResult.output_lines/total_lines/truncated` from `ContentUnit.output: str` is unspecified in step 6. Either plumb `format_tools` into `OutputLog` or pre-render the triple at `tool_result` time. → escalated to user (Q5).
- Improvement: Performance — every `tool_result` triggers full `rebuild()`. Document as accepted-for-v1 trade-off; revisit if measurable.
- Improvement: Step 9 cancel-path ordering needs explicit sequence: `_flush_buffer → finalize_turn → cleanup_pending+update → _append_cancelled_marker → reset_busy → blank`.
- Improvement: `clear_recorded → clear_state` rename location ambiguous between step 5 and step 9. Pin to step 5.
- Improvement: Missing test `test_append_unit_assistant_turn_with_empty_lines_no_script_entry` for step 5 kind-branching.
- Improvement: Missing test `test_rebuild_with_pending_tool_renders_start_only` for step 6 in-flight tool rebuild.
- Improvement: Step 8 — commit to `event.y + self.scroll_offset.y` click-coord path (drop `event.style.meta` speculation since `RichLog` doesn't currently set `Strip` metadata).
- Improvement: Step 9 — replace defensive `dq.clear()` sweep on remaining `_open_tool_units` deques with a softer `logger.warning` if non-empty (silent sweep can hide FIFO desyncs).
- Improvement: Step 9 — note that orphan-cleanup batching could call `rebuild()` once instead of once per synthesized result, if needed for perf.
- Skip: pre-existing absence of `Strip` metadata on `RichLog` — not in scope.

**Decisions (supervisor):**
- All Improvements: accept and instruct `/plan_update`.
- Critical #1 (`ToolResult.raw_name`): autonomous fix.
- Critical #2 (ContentUnit storage): escalated to user as Q5.

**User decisions:**
- **Q5 — `ContentUnit` body storage shape:** **A — store both**. `ContentUnit` carries `output: str` (full, for modal) AND `output_lines: list[str]`, `total_lines: int`, `truncated: bool` (pre-rendered, for inline atomic render). Compute once at `tool_result` time; rebuild reads pre-rendered triple. No `format_tools` plumbing into `OutputLog` needed.

**Changes:**
- `summary.md` — updated `ContentUnit` schema box with new pre-rendered triple fields (`output_lines`, `total_lines`, `truncated`).
- `step_1.md` — UI dispatch comment now calls `output.clear_state()` directly with "see step 5 for the rename" pointer.
- `step_4.md` — added `raw_name: str` to `ToolResult` action; documented live + cancelled-cleanup populations; new test `test_tool_result_carries_raw_name`; test count → 7.
- `step_5.md` — `ContentUnit` gains pre-rendered triple fields (per user Q5 = A); explicit rename ownership of `clear_recorded → clear_state` (step 5 only); added `test_append_unit_assistant_turn_with_empty_lines_no_script_entry`; test count → 15.
- `step_6.md` — `format_tool_compressed` switched to explicit-fields signature (no `ToolResult` synthesis); `_render_unit_atomic` reads pre-rendered triple; added `test_rebuild_with_pending_tool_renders_start_only`; test count → 14.
- `step_8.md` — committed to `event.y + self.scroll_offset.y` click coords; dropped `event.style.meta` alternative and 5-line spike (RichLog has no Strip metadata).
- `step_9.md` — `result.raw_name` / `cancelled.raw_name` for FIFO lookups; pre-rendered triple computed at `tool_result` time (modal uses full `unit.output`); explicit "Cancel path ordering" subsection (1–7 sequence); soft-assert WARN-log replaces silent deque sweep; new "Performance note" section.
- `Decisions.md` (NEW) — consolidated design-decision log covering all R2 decisions with rationale. Engineer-initiated artifact; kept because it's exactly the file the supervisor's setup step expects (`pr_info/steps/Decisions.md`) for future implementer/reviewer context.

**Status:** committed (Round 2 plan changes)

## Round 3 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: Step 9 ALGORITHM destructures `_render_tool_output(...)` as a 3-tuple `(output_lines, total_lines, truncated)`, but the existing helper returns a 2-tuple `(lines, total)`. Either extend the helper to a 3-tuple (recommended) or compute `truncated = total > _TRUNCATION_THRESHOLD` at the call site.
- Critical: Step 5 TDD test #13 (`update_unit_and_rerender` body render) cannot pass under step 5 scope: step 5's `rebuild()` is allowed to be a no-op stub (per its LLM prompt), and post-R2 the body-render trigger is `output_lines` non-empty, not `output`. Either implement a minimal `rebuild()` in step 5 (step 6 then adds tier dispatch on top), or defer the test to step 6.
- Improvement: Step 5 HOW line ~63 still says "body lines when `unit.output` is set" — should be "when `unit.output_lines` is non-empty" (matches R2-02/R2-04 + Decisions.md).
- Improvement: Step 6 WHERE/LLM-prompt says step 9's ToolResult branch "calls" `format_tool_compressed` directly. It's actually invoked indirectly through `update_unit_and_rerender → rebuild → _render_unit_atomic`. Soften wording to prevent a redundant direct call in step 9.
- Improvement: Step 9 TDD test #4 description contradicts dict-insertion-order semantics ("returns tool, then turn, then turn"). Rewrite to: "after tool fires, `last_unit()` returns the tool unit; further turn text via `extend_open_unit` does NOT change `last_unit()`".
- Improvement: Step 5 test #15 — add half-line note that the "empty turn = no script entry" rule implies `rebuild()` produces zero output for an empty turn.
- Skip: Performance note (already accepted v1).
- Skip: F2 silent-noop and snapshot visual-inspection rule (already specified).

**Decisions (supervisor):**
- All Critical + Improvement items: accept and instruct `/plan_update`.
- Critical #1 fix: extend `_render_tool_output` to return `(lines, total, truncated)` — the helper already knows. Update step 2 / step 9 callers accordingly.
- Critical #2 fix: step 5 implements a minimal `rebuild()` (walk `_script`, call `_render_unit_atomic` per entry). Step 6 then adds tier-1 vs tier-2 dispatch inside `_render_unit_atomic`. Test #13 payload updated to pass the full pre-rendered triple.
- No user-facing design questions in this round.

**User decisions:** (none — round was fully autonomous)

**Changes:**
- `step_2.md` — added `_render_tool_output` 3-tuple extension to WHERE/WHAT; documents `truncated = total > _TRUNCATION_THRESHOLD` exposure and the two existing call-site updates.
- `step_5.md` — `rebuild()` is implemented minimally in step 5 (not stubbed); new ALGORITHM section with pseudocode; `_render_unit_atomic` body trigger changed from `unit.output` to `unit.output_lines`; LLM prompt drops "stub to no-op" language; test #13 payload now passes the full pre-rendered triple; test #15 extended with empty-turn → zero buffer lines invariant.
- `step_6.md` — `_render_unit_atomic` extended with tier dispatch (rebuild walk inherited from step 5, not rewritten); language for `format_tool_compressed` invocation is now "indirectly via `update_unit_and_rerender → rebuild → _render_unit_atomic`".
- `step_7.md` — destructure of `_render_tool_output` updated to 3-tuple (`output_lines, total, _truncated`) for consistency with R3-01.
- `step_9.md` — test #4 renamed/rewritten to `test_last_unit_returns_most_recent_inserted_unit_dict_order`, locking dict-insertion-order semantics for `last_unit()` / F2.
- `Decisions.md` — appended R3-01 through R3-07 entries with rationale.

**Status:** committed (Round 3 plan changes)

## Round 4 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: Step 5's `_render_unit_atomic` references `format_tool_compressed`, but the extraction lives in step 6 — backward cross-step dependency. Step 5 test #13 explicitly asserts `rendered_lines includes the body`, so step 5 *must* produce body lines; `format_tool_compressed` must exist before step 6. Breaks "each step = one green commit" independence.
- Improvement: Step 5's WHAT/state-additions list doesn't declare `_tool_tier_overrides: dict[str, Literal[...]]`, even though `clear_state()` wipes it. Field is implicitly required by step 5's tests; step 6 populates it. One-line addition closes the spec gap.
- No design/user questions.

**Decisions (supervisor):**
- Critical: move `format_tool_compressed` extraction from step 6 → step 5 (engineer's preferred option). Step 5's WHERE gains `stream_renderer.py`; step 5's WHAT/HOW add the extraction; the three `format_tool_compressed` tests (currently in step 6, #12-#14) move into step 5. Step 6 retains only the tier-dispatch change to `_render_unit_atomic`.
- Improvement: add `_tool_tier_overrides: dict[str, Literal["oneline","compressed"]] = {}` to step 5's WHAT, with one line noting it's introduced empty in step 5 and populated by step 6's `toggle_unit_tier`.
- All autonomous; round will continue.

**User decisions:** (none — round was fully autonomous)

**Changes:**
- `step_5.md` — added `stream_renderer.py` to WHERE; declared `_tool_tier_overrides` field in WHAT; added "Extracted helper" paragraph for `format_tool_compressed`; `_render_unit_atomic` ALGORITHM explicitly calls the helper; migrated 3 helper tests in (now tests #16–#18); LLM prompt updated to 18 tests.
- `step_6.md` — removed `stream_renderer.py` from WHERE; removed `format_tool_compressed` extraction paragraph; removed redundant `rebuild()` re-implementation (now a one-liner note that rebuild is unchanged from step 5); removed `_tool_tier_overrides` declaration (now in step 5); removed migrated tests; LLM prompt updated to 11 tests.
- `summary.md` — steps-overview table: step 5 now includes `stream_renderer.py (format_tool_compressed extracted)`; step 6 drops `rebuild()` from title and stream_renderer mention; modified-files row attributes `format_tool_compressed()` to step 5.
- `Decisions.md` — appended R4-01 (extraction move) + R4-02 (`_tool_tier_overrides` declaration).

**Status:** committed (Round 4 plan changes)

## Round 5 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: `format_tool_oneline` signature mismatch between step 3 and step 6. Step 3 currently defines `format_tool_oneline(start: ToolStart, result: ToolResult | None, duration_ms: int | None) -> str`. Step 6's `_render_unit_atomic` calls it as `format_tool_oneline(name=unit.tool_name, args=unit.args, duration_ms=unit.duration_ms, is_error=unit.is_error)` — explicit fields. Step 6 test #5 exercises this path and will fail at runtime. By analogy with R2-03 (where `format_tool_compressed` was switched to explicit fields for the same reason — atomic rebuild has no `ToolStart/ToolResult` objects to pass), `format_tool_oneline` should also use explicit fields.
- Skip: Step 7's loose `_render_tool_output(unit.output or "", full=True)` pseudocode omits `format_tools=` kwarg — step 7 already disclaims "implementer should tighten the algorithm". Not materially harmful.

**Decisions (supervisor):**
- Critical: change `format_tool_oneline` signature in step 3 to explicit fields (mirrors R2-03 for `format_tool_compressed`). Update step 3's WHAT, ALGORITHM, and the 7 test cases. Step 6's call site already uses the explicit-field shape — leave unchanged.
- All autonomous.

**User decisions:** (none — round was fully autonomous)

**Changes:**
- `step_3.md` — rewrote `format_tool_oneline` signature to explicit keyword-only fields `(*, name, args, duration_ms, is_error)`; updated WHAT/HOW/ALGORITHM with the new tri-state status semantics (`duration_ms=None,is_error=False` → running; `duration_ms!=None,is_error=False` → done; `is_error=True` → error); all 7 tests now call with explicit kwargs (no `ToolStart`/`ToolResult` construction); added `test_format_tool_oneline_error_without_duration` for cancel-before-completion case; updated LLM Prompt.
- `Decisions.md` — appended R5-01 entry documenting signature change and rationale (mirrors R2-03 for `format_tool_compressed`).
- Step 6 call site verified unchanged (already calls `format_tool_oneline(name=..., args=..., duration_ms=..., is_error=...)`).
- `summary.md` unchanged (only references the function by bare name, no signature documented).

**Status:** committed (Round 5 plan changes)

## Round 6 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: none.
- Improvement: Steps 5 and 6 invoke `format_tool_start` with kwargs `(name=..., args=...)`, but the existing function signature is `format_tool_start(action: ToolStart, full: bool = False)`. Implementer would catch on first test run, but the plan doesn't specify which option to take. Two options: (a) call sites synthesize `ToolStart(display_name=..., raw_name="", args=...)`, (b) refactor `format_tool_start` to explicit fields for consistency with R2-03 + R5-01.
- Skip: pre-existing `format_tool_start` signature outside plan scope; `full_text="(cancelled)"` field on cancelled tool unit (harmless — no renderer reads tool full_text); cosmetic tightening.

**Decisions (supervisor):**
- Improvement: accept, apply option (a) — synthesize `ToolStart(display_name=unit.tool_name, raw_name="", args=unit.args or {})` at the call sites in steps 5 and 6. Option (b) would refactor a pre-existing function unnecessarily; the simpler path matches the project's "don't refactor beyond what the task requires" rule. Document the choice in `Decisions.md` as R6-01.
- All autonomous.

**User decisions:** (none — round was fully autonomous)

**Changes:**
- `step_5.md` — `_render_unit_atomic` tool branch now spells out `format_tool_start(ToolStart(display_name=unit.tool_name, raw_name="", args=unit.args or {}))`; inline comment that only `display_name`/`args` are read so empty `raw_name` is harmless; noted `ToolStart` import from `llm/types.py`.
- `step_6.md` — same synthesis pattern applied to the compressed branch of `_render_unit_atomic`.
- `Decisions.md` — appended R6-01 documenting the call-site-synthesis choice and the rationale for not refactoring `format_tool_start` (asymmetry with R2-03 / R5-01 accepted to keep scope tight).

**Status:** committed (Round 6 plan changes)

## Round 7 — 2026-05-26

**Findings (from engineer subagent):**
- Critical: none.
- Improvement: none.
- Design questions: none.
- Skip: nothing flagged (diminishing returns acknowledged).

**Decisions (supervisor):** No plan changes required.

**User decisions:** none.

**Changes:** none.

**Status:** plan stable — loop exit condition met.

---

## Final Status

**Rounds run:** 7
**Plan-doc commits produced:** 6 (`3a0f394`, `65f7134`, `3a74f64`, `f0cbf18`, `acde176`, `b5b21e2`)
**Branch:** `629-icoder-tiered-tool-display-with-click-to-toggle-detail-modal-and-response-typed-action-refactor` (rebased on `main`, all commits pushed)

**Plan files reviewed and refined:**
- `pr_info/steps/summary.md`
- `pr_info/steps/step_1.md` through `pr_info/steps/step_10.md`
- `pr_info/steps/Decisions.md` (new — consolidated R2-* through R6-* design decisions with rationale)

**Total accepted changes:** 35+ items across 7 rounds.

**Cumulative high-level outcomes:**
- Architecture: atomic tool render model locked down (R1 Q3, R2-02 through R2-04); per-tool-name FIFO matching with `ToolResult.raw_name` (R2-01); explicit-fields signatures for `format_tool_oneline`, `format_tool_compressed` (R2-03, R5-01); call-site `ToolStart` synthesis for `format_tool_start` to keep scope tight (R6-01).
- Data model: `parent_id` retained on `ContentUnit` per issue Decision (R1 Q1); pre-rendered triple `(output_lines, total_lines, truncated)` added alongside full `output:str` for modal (R1 Q5 = A; R2-02); `_tool_tier_overrides` declared in step 5 (R4-02).
- Step independence: `format_tool_compressed` extraction moved from step 6 → step 5 to fix backward dependency (R4-01); minimal `rebuild()` ships in step 5 with tier dispatch added in step 6 (R3-02); `_render_tool_output` extended to return 3-tuple `(lines, total, truncated)` (R3-01).
- Behavior: modal closes on both `Escape` and `Enter` (R1 Q2); langchain error detection via `on_tool_end` + `ToolMessage.status == "error"` (R2 langchain fix); cancel-path ordering documented (R2-05); `clear_state()` rename pinned to step 5 (R2-06); soft-assert WARN-log instead of silent FIFO sweep (R2-07); commit to `event.y + scroll_offset.y` click coords (R2-08); rebuild perf trade-off accepted for v1 (R2-09).
- Tests: new tests in steps 4/5/6 covering `raw_name` propagation, empty-turn rebuild, in-flight tool rebuild, `last_unit()` dict-order semantics; snapshot visual-inspection rule (R2-10, R3-* additions).

**Plan is ready for approval and implementation.** Each of the 10 steps is now self-contained (commit-sized, leaves checks green after completion); cross-step references resolve cleanly; tool rendering, tier dispatch, FIFO matching, and cancel handling are all internally consistent.

**Recommended next action:** approve the plan and proceed to implementation (e.g., via `/implement` or equivalent workflow). The `TASK_TRACKER.md` is empty and will be populated as step 0 of implementation per project convention.
