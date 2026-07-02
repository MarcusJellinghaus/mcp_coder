# Plan Review Log — Issue #764 (iCoder: show log file path in /info)

Run 1 — supervised plan review.
Base branch: main | Branch: 764-icoder-show-log-file-path-in-info
Plan files: pr_info/steps/step_1.md, step_2.md, summary.md

---

## Round 1 — 2026-07-02
**Findings**: Engineer reviewed the plan against the real code and reported it implementable as written. All factual claims verified:
- `register_info` currently takes `runtime_info: RuntimeInfo` (non-optional), `mcp_manager` keyword-optional (info.py:120-124).
- `EventLog` already stores `self._logs_dir` (event_log.py:95) and exposes `current_path` → `self._path` (event_log.py:119-121); `_path` survives `close()` (event_log.py:190-198). `logs_dir` is a true one-liner; no `file_path` alias needed.
- Exactly 12 `register_info(...)` call sites in test_info_command.py; 1 production call site (icoder.py:139). `event_log` fixture already in conftest.py.
- Step structure sound: Step 1 = property + tests; Step 2 = signature+formatter+wiring+12 call-site updates+new test as one commit (correct — the required param breaks the call site, must land together). TDD ordering specified. No missing test steps.
- Requirements coverage complete: Decisions #1,#3,#4,#5,#6,#8 all covered.
- One design item: plan diverges from approved Decisions #2/#7 (no AppCore routing, no boundary assert). Divergence assessed technically sound and lower-risk; preserves all user-facing requirements.

**Decisions**: No straightforward fixes required — plan is code-accurate. Escalated the single design-divergence question to the repo owner.

**User decisions**: Q: Accept the KISS divergence from approved Decisions #2 (AppCore routing) and #7 (boundary assert), or rewrite to follow them? — A: **Accept the KISS divergence** (keep single `event_log` parameter; no `AppCore.mcp_manager`; no assert).

**Changes**: `pr_info/steps/summary.md` — added one sentence in the "KISS divergence" section recording that the repo owner explicitly approved the divergence on 2026-07-02 and that Decisions #2/#7 are superseded and must not be reverted to the AppCore route. No technical content of the plan changed.

**Status**: committed (see commit agent) — plan file changed → loop to Round 2 for a fresh review.

---

## Round 2 — 2026-07-02
**Findings**: Fresh review after Round 1's approval note. Verdict: Ready, no changes needed. Re-verified all Round 1 facts against real code (logs_dir at event_log.py:93, _format_info/register_info signatures at info.py:42/120, insertion point between MCP_CODER_* and Other env vars, wiring move at icoder.py:139, exactly 12 test call sites, conftest event_log fixture reusable). Approval note in summary.md introduced no contradiction. One informational nit: step docs referenced check tools with a malformed id `mcp__tools-py__...` (missing the `mcp-` segment).

**Decisions**: Accept the nit fix as a straightforward improvement (correct tool ids the implementer will run). No user escalation — no new design/requirements questions.

**User decisions**: none.

**Changes**: `pr_info/steps/step_1.md` (3 occurrences) and `pr_info/steps/step_2.md` (3 occurrences) — corrected `mcp__tools-py__run_{pylint,pytest,mypy}_check` → `mcp__mcp-tools-py__...`. Tool-id text only; no other content touched.

**Status**: committed — plan files changed → loop to Round 3 for a fresh review.

---
