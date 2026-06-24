# Implementation Review Log — Run 1

Issue #629 — iCoder: tiered tool display with click-to-toggle, detail modal, and Response typed-action refactor

Supervisor: technical lead (delegating all implementation to engineer subagents).

---

## Round 1 — 2026-06-24

**Findings** (from `/implementation_review`; no critical issues, real implementation diff confirmed, 4061 tests passing):
1. *(Accept)* `app.py` `_handle_stream_event` ToolResult branch silently drops an unpaired `ToolResult` when no open tool unit is found — FIFO desync goes unobserved.
2. *(Accept)* `langchain/agent.py` comment "Surface it via is_error instead of raising" is misleading — no `raise` was removed at that site.
3. *(Skip)* `finalize_open_unit` is a no-op — documented forward-compat hook; reviewer leans keep; removing churns 3 call sites for zero gain.
4. *(Skip)* Debounce timer set even for non-tool units — harmless, simpler than branching.
5. *(Skip)* `DetailModal` ignores clipboard `set_clipboard_text` result — acceptable for a TUI copy action.
6. *(Skip)* `output is not None` footer trigger — verified correct (keeps `└ done` for empty-output tools), documented.

**Decisions**:
- Accept 1: add `logger.warning` surfacing FIFO desync, mirroring the `_cleanup_orphan_tools` WARN style (consistent with Decision R2-07 — surface desync, don't recover silently).
- Accept 2: reword the misleading comment (Boy Scout doc fix).
- Skip 3–6: cosmetic/speculative/already-correct per knowledge-base scope rules.

**Changes**:
- `src/mcp_coder/icoder/ui/app.py` — added FIFO-desync WARN log in the `unit_id is None` ToolResult case; control flow unchanged.
- `src/mcp_coder/llm/providers/langchain/agent.py` — reworded misleading `on_tool_end` comment; no logic change.
- Quality checks: pylint PASS, mypy PASS, pytest 4061 passed / 2 skipped / 0 failed.

**Status**: committed (see commit agent).

## Round 2 — 2026-06-24

**Findings** (from fresh `/implementation_review`; verified the two Round-1 fixes are correct, no regressions):
1. *(Critical)* `.importlinter` "layered_architecture" contract whitelist missing the `/display` CLI→command import added in `cli/commands/icoder.py` → `run_lint_imports_check` BROKEN (1/23), a required CI gate. `info`/`color` already have identical whitelist exceptions.
2. *(Accept→Note)* 3 new snapshot tests in `test_snapshots.py` have no baseline `.svg`s. Already documented in TASK_TRACKER — `pytest-textual-snapshot` not installed here, module is `skipif win32`/`textual_integration` (excluded from CI). Manual pre-merge step.
3. *(Accept)* `output_log.py` `on_click` `chain==1` arms a debounce timer without stopping any in-flight `_pending_single`; two quick single clicks on different lines leave a stale timer that toggles a unit the user moved off. `chain==2` already cancels it.

**Decisions**:
- Accept 1: add the one-line whitelist entry mirroring the established `info`/`color` exception. NOT an escalation — the architectural exception for CLI→command imports already exists; this completes the pattern (skill: "simple whitelist additions, launch an engineer to fix").
- Accept 3: stop any pending single-click timer before arming a new one, mirroring the `chain==2` branch.
- Note 2: surface to user as a manual pre-merge step; cannot generate baselines in this env (missing plugin; CLAUDE.md says don't work around missing deps).

**Changes**:
- `.importlinter` — added `mcp_coder.cli.commands.icoder -> mcp_coder.icoder.core.commands.display`.
- `src/mcp_coder/icoder/ui/widgets/output_log.py` — guard `_pending_single` before arming new debounce timer.
- Gates: lint-imports PASSED (23 kept), pylint PASS, mypy PASS, pytest 4061 passed / 2 skipped / 0 failed.

**Status**: committed (see commit agent).

## Round 3 — 2026-06-24

**Findings** (fresh `/implementation_review`; verified `14521bc` fixes correct — lint-imports PASSED 23/23, click tests green):
1. *(Accept→Skip)* Replay timestamps: replayed assistant/tool units get `datetime.now()` while user-input units get the `session_start_time + t` offset; modal footer shows wall-clock vs relative time for replayed sessions. Cosmetic.
2. *(Skip)* An assistant turn opened by a trailing partial-line `TextChunk` can finalize as an empty unit; F2 would show "Assistant turn / 0 lines". Harmless, consistent with snapshot decision.

**Decisions**:
- Skip 1: purely cosmetic (replayed-session modal footer); the fix threads a timestamp through the shared live `_handle_stream_event` path — meaningful scope/risk for cosmetic payoff. Per KB scope rules, skip.
- Skip 2: harmless edge case aligned with documented design decision.

**Changes**: none — zero accepted code changes this round. Review loop terminates.

**Status**: no changes needed.

## Final Status

**Rounds run:** 3 review rounds (loop terminated when Round 3 produced zero accepted code changes).

**Commits produced by this review:**
- `ef3226a` — Surface unpaired ToolResult (FIFO-desync WARN log) + fix misleading langchain `is_error` comment.
- `14521bc` — Fix import-linter whitelist for `/display` (CI gate was BROKEN) + guard single-click debounce timer in `on_click`.
- (pending) — Whitelist 4 vulture false-positives for the iCoder tiered-tool-display symbols.
- (pending) — This review log.

**Final gate status:**
- pylint: PASS
- mypy: PASS
- pytest: 4061 passed / 2 skipped / 0 failed (fast unit subset); 94 textual-integration tests green
- `run_lint_imports_check`: PASSED — 23 contracts kept, 0 broken
- `run_vulture_check`: clean (no findings after whitelist additions)

**Known outstanding (not blocking CI, surfaced to user):**
- 3 new snapshot tests in `tests/icoder/test_snapshots.py` (`test_snapshot_default_tier`, `test_snapshot_after_display_oneline`, `test_snapshot_modal_over_tool`) lack baseline `.svg`s. `pytest-textual-snapshot` is not installed in this environment and the module is `skipif win32`/`textual_integration` (excluded from CI). **Manual pre-merge step:** run `pytest tests/icoder/test_snapshots.py --snapshot-update` in an environment with the plugin and visually inspect the SVGs before merge. Already documented in `TASK_TRACKER.md`.

**Skipped findings (cosmetic/speculative, per knowledge-base scope rules):** `finalize_open_unit` no-op (documented forward-compat hook); debounce timer armed for non-tool units (harmless); DetailModal swallows clipboard-failure result; replay timestamp wall-clock vs relative for assistant/tool units (cosmetic modal footer); empty assistant-turn finalize edge case (harmless).
