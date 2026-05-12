# Plan Review Log — Issue #953

Branch: `953-vscodeclaude-session-detection-improvements`
Started: 2026-05-12
Reviewer: plan_review_supervisor

## Round 1

### Files reviewed

- `pr_info/steps/summary.md`
- `pr_info/steps/step_1.md`
- `pr_info/steps/step_2.md`
- `pr_info/steps/step_3.md`
- `pr_info/steps/step_4.md`
- `pr_info/steps/step_5.md`
- `pr_info/steps/step_6.md`
- `pr_info/steps/step_7.md`
- `pr_info/steps/step_8.md`

### Code cross-referenced

- `src/mcp_coder/workflows/vscodeclaude/sessions.py` (88, 210, 280, 482, 500, 593, 620)
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py` (205, 281, 308-320, 364)
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (422)
- `src/mcp_coder/workflows/vscodeclaude/status.py` (300-360)
- `src/mcp_coder/workflows/vscodeclaude/helpers.py` (62-91)
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (100, 301-307)
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py` (395-409)
- `src/mcp_coder/workflows/vscodeclaude/types.py`
- `src/mcp_coder/cli/commands/coordinator/commands.py` (560-636)

### Findings — see report

## Round 1 — 2026-05-12

**Findings**:
- [DESIGN] Step 2 — `vscode_pid_create_time` field handling: inconsistent type (required key) vs runtime expectation (`.get()` returns `None` for old JSON)
- [STRAIGHTFORWARD] Step 3 — 4th `get_workspace_file_path` call site missing (`session_restart.py:396`)
- [STRAIGHTFORWARD] Summary/step files step-number vs item-number mismatch unclarified
- [STRAIGHTFORWARD] Step 1 — `_vscode_pids_cache` refresh semantics interaction not noted
- [STRAIGHTFORWARD] Step 2 — existing `check_vscode_running(pid)` test callers need two-arg form
- [STRAIGHTFORWARD] Step 6 — "replace" vs "extend" wording contradiction between step_6.md and summary.md
- [STRAIGHTFORWARD] Step 8 — composition Scenario A cross-file assertion location unspecified
- [STRAIGHTFORWARD] Step 5 — zombie-row test does not assert `(Closed)` prefix preserved

**Decisions**: accept all 7 straightforward findings; escalate the DESIGN finding to the user with A/B/C options.

**User decisions**:
- Q: How to reconcile Step 2's TypedDict change with the "no migration" stance from the issue? Options A (NotRequired) / B (required + migration in `load_sessions`) / C (current looseness).
- A: **Option B** — keep field required, add backfill migration in `load_sessions`. This **overrides** the issue's "no explicit migration" decision.

**Changes** — 7 plan files updated:
- `step_1.md`: cache-semantics note added under HOW.
- `step_2.md`: Option B migration block in `load_sessions` (line ~53); reads switched to subscript; 5 existing `check_vscode_running(...)` test sites listed; override notice.
- `step_3.md`: 4th `get_workspace_file_path` site at `session_restart.py:396` added to WHERE + HOW.
- `step_5.md`: `(Closed)` prefix assertion added to zombie-row test.
- `step_6.md`: "extend the existing tail message" wording (not "replace").
- `step_8.md`: Scenario A's `display_status_table` assertion split out into `test_status_display.py`.
- `summary.md`: section #2 rewritten for Option B with override notice; section #3 says "four sites"; section #8 "extend"; `session_restart.py` moved from "Not modified" to "Modified"; numbering note added at top of Implementation Steps.

**Status**: applied; pending commit.

## Round 2 — 2026-05-12

**Findings**:
- [STRAIGHTFORWARD] step_2.md — `load_sessions` line-number pointer wrong (says 53; actual 50).
- [STRAIGHTFORWARD] step_2.md — migration block placement vague ("after JSON parse"); should anchor against the actual `load_sessions` validation block.
- [STRAIGHTFORWARD] step_2.md — no explicit note that `save_sessions` requires no changes.
- [STRAIGHTFORWARD] step_2.md — `helpers.py` not in WHERE list despite HOW referencing `build_session`.

**Decisions**: accept all 4. No design questions.

**User decisions**: none required.

**Changes** — 1 plan file updated:
- `step_2.md`: line number corrected to 50; migration snippet anchored to "after `data['last_updated'] = ""` validation, before `return cast(...)`"; loop variable corrected from `store["sessions"]` to `data["sessions"]` (engineer caught this — original snippet referenced a non-existent local); `save_sessions` no-change note added; `helpers.py` added to WHERE.

**Status**: applied; pending commit.

## Round 3 — 2026-05-12

**Findings**: zero new findings. Round 2 changes verified against source: `load_sessions` at `sessions.py:50`; migration anchor matches actual validation at lines 64-66; `data["sessions"]` is the correct local; `save_sessions` writes `store` whole (line 119); all 5 `check_vscode_running(` test sites match (lines 88, 93, 566, 584, 602); `helpers.py` `build_session` confirmed; cross-file consistency between `summary.md` and step files preserved.

**Decisions**: terminate loop. Plan is ready for approval.

**User decisions**: none.

**Changes**: none.

**Status**: no plan changes; review loop terminated.

---

## Final Status

**Rounds run**: 3
**Total findings**: 12 (8 Round 1 + 4 Round 2 + 0 Round 3).
**Design questions escalated**: 1 (Step 2 TypedDict — user chose Option B, overriding the issue's "no explicit migration" stance).
**Plan files changed**: 7 in Round 1, 1 in Round 2.
**Commits produced**:
- `003e992` — `docs(plan-953): apply Round 1 plan-review updates for session detection`
- `17b142b` — `docs(plan-953): tighten step_2 load_sessions migration placement`

**Outcome**: Plan is ready for approval. All cross-references verified against source code.
