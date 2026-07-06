# Plan Review Log — Issue #1023

Remove `parsers.py` from `.large-files-allowlist` (resolved by #90).

Supervisor: technical lead (delegates analysis to engineer subagent via `/plan_review` and `/plan_update`).
Base branch: `main` (branch up to date, no rebase needed).

---

## Round 1 — 2026-07-06

**Findings** (from `/plan_review` engineer subagent):
- [observation] Plan aligned with planning_principles: single step = single commit, verification is an exit gate. No design/scope issue.
- [nit/mechanical] step_1.md references `mcp__workspace__edit_file`; correct tool name is `mcp__mcp-workspace__edit_file`.
- [nit/mechanical] step_1.md over-specifies building `old_string` with "enough surrounding lines to be unique" — the `parsers.py` line is already unique; a bare single-line edit suffices.
- [observation] Manual CLI verification instead of an automated test — justified under KISS (no Python code to test; asserting a line's absence from a config file is brittle). Sound.

**Factual verification (all CONFIRMED against live repo):**
- `parsers.py` is 560 lines (<750); reported as a stale allowlist entry, not a violation.
- `.large-files-allowlist` contains `src/mcp_coder/cli/parsers.py` verbatim (unique), between `docs/processes-prompts/development-process.md` and `tools/safe_delete_folder.py`.
- The two other stale entries are correctly deferred to #1029.

**Decisions**:
- Accept both nits as autonomous mechanical fixes (fix the tool-name typo; simplify the edit instruction).
- No design/requirements questions to escalate — scope is correct and internally consistent.

**User decisions**: none needed this round.

**Changes**: instruct engineer to fix the two instruction-text nits in `step_1.md` via `/plan_update`.

**Status**: plan changes applied (pending) → triggers another review round.
