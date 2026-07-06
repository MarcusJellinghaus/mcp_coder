# Plan Review Log — Issue #41

Validate `.mcp.json` is well-formed (hard fail on broken config)

Supervisor: technical lead (delegates all analysis/file ops to engineer subagents).
Base branch: `main` (branch based on current `origin/main` tip — no rebase needed).
Plan state at start: fresh plan (`step_1.md`, `step_2.md`, `summary.md`), no steps complete.

---

## Round 1 — 2026-07-06

**Findings** (from engineer `/plan_review`):
- #1 (bug) `_validate_mcp_config` calls `data.get()` on non-dict top-level JSON (`[]`/`42`) → uncaught `AttributeError`, crashes `execute_verify`.
- #2 Missing unit test for top-level non-object JSON.
- #3 No end-to-end malformed→exit-1 CLI test (only isolated `_compute_exit_code` + row-render).
- #4 Wrong tool prefixes in prompts (`mcp__tools-py__` → `mcp__mcp-tools-py__`).
- #5 (design) Malformed config still runs downstream MCP checks — indirect noise the feature meant to replace.
- #6 Two `MCP CONFIG*` sections split by `MCP SERVERS` (validity row before, placeholder warnings after).
- #7 New always-on `MCP CONFIG` section affects existing alignment/snapshot tests via conftest mock.
- #8 Step 1 trivially small (param dead until Step 2).

**Decisions**:
- #1 accept — genuine crash bug, add `isinstance(data, dict)` guard.
- #2 accept — add non-object JSON unit case.
- #3 accept — add full-CLI `TestExitCodeMatrix` malformed→exit-1 case.
- #4 accept — fix prefixes in summary + both steps.
- #5 ask-user — affects issue's core goal (scope).
- #6 skip — cosmetic output ordering; keep plan's smallest-diff choice.
- #7 accept — add explicit note so Step 2 budgets for updating alignment/snapshot assertions.
- #8 skip — split defensible (isolated TDD, each step green/one commit); keep.

**User decisions**:
- #5: **Short-circuit downstream.** On hard-fail, print `MCP CONFIG` diagnostic first, then skip remaining MCP health/smoke/prompt checks (guard `if mcp_config_resolved:` blocks on `mcp_config_ok is not False`).

**Changes** (engineer `/plan_update`):
- `step_2.md`: added `isinstance(data, dict)` hard-fail guard to algorithm; added non-object JSON unit case; added end-to-end `TestExitCodeMatrix` exit-1 case; added downstream short-circuit HOW + skip test; added alignment/snapshot impact note.
- `summary.md` + `step_1.md` + `step_2.md`: fixed `mcp__tools-py__` → `mcp__mcp-tools-py__` prefixes.
- Two-step structure, `verify.py`-localized scope, no new deps/CLI args preserved.

**Status**: plan changed → committing; loop continues (fresh review required).
**Commit**: `73f261c` (plan step files).
**Commit (round 2)**: `f7d09cd` (plan step files, added after Round 2 below).

## Round 2 — 2026-07-06

**Findings** (from engineer `/plan_review`, re-review):
- All six Round 1 revisions verified landed correctly and consistent with the real code.
- (a) `TestExitCodeMatrix` `_run_verify` helper hardcodes `resolve_mcp_config_path → None` and doesn't mock `parse_claude_mcp_list`/`verify_mcp_servers`; the new malformed→exit-1 case isn't a drop-in reuse.
- (b) Short-circuit HOW imprecise vs real code: test-prompt block (3c) is a bare `try:` (needs a NEW guard, not an edited condition); the "compute `claude_mcp_ok`" block sets `claude_mcp_ok=False` when 3a is skipped (harmless — exit 1 already forced).
- (c) `summary.md` files table omits `test_verify_alignment.py` (smoke test renders the new always-on row; stale `_collect_mcp_warnings` docstring ref).

**Decisions**: all three (a/b/c) accept — straightforward precision/clarity improvements, no design/scope questions. No user escalation needed.

**User decisions**: none this round.

**Changes** (engineer `/plan_update`):
- `step_2.md`: added `_run_verify` `mcp_config_path`-override note for the e2e test; added two short-circuit HOW precisions (new guard on 3c; leave `claude_mcp_ok` compute block as-is).
- `summary.md`: added low-priority "check" row for `test_verify_alignment.py` (alignment still passes; stale docstring ref to check).

**Status**: plan changed → committing; loop continues (fresh review required).
**Commit**: `f7d09cd` (`summary.md`, `step_2.md`).

## Round 3 — 2026-07-06

**Findings** (from engineer `/plan_review`, final re-review):
- All three Round 2 clarifications (a/b/c) verified landed correctly and internally consistent with the real `verify.py`/tests.
- No design/scope questions remain; User Decision #5 (short-circuit) correctly threaded.
- One trivial observation: per-step pytest marker string omits `copilot_cli_integration`/`jenkins_integration`/`llm_integration`/`textual_integration` vs the fuller CLAUDE.md set. Feature's tests are pure unit tests → nil practical effect. Present since Round 1.

**Decisions**: trivial marker observation → skip (cosmetic, nil effect; default to simpler plan, not worth a revision cycle). No other findings.

**User decisions**: none this round.

**Changes**: none — zero plan changes this round.

**Status**: no changes needed. Loop terminates.

---

## Final Status

- **Rounds run**: 3.
- **Plan commits produced**: `73f261c` (Round 1 revisions), `f7d09cd` (Round 2 clarifications).
- **User decisions**: 1 — malformed `.mcp.json` short-circuits downstream MCP checks (Round 1, finding #5).
- **Outcome**: Round 3 produced zero plan changes; engineer approved the plan as sound, well-scoped, and ready to implement. Plan verified internally consistent with the real `verify.py` and test files.
- **Verdict**: ✅ **Plan ready for approval / implementation.**
