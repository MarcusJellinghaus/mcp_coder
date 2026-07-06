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

**Status**: plan changes applied and committed (`7ceb6bc`) → triggered Round 2.

## Round 2 — 2026-07-06

**Findings** (re-check after Round 1 fixes):
- BLOCKER: none. improvement: none.
- [nit/mechanical — no plan change] `old_string` = `src/mcp_coder/cli/parsers.py` with empty `new_string` leaves a stray blank line where the entry was. Harmless — `load_allowlist()` ignores blank lines and the acceptance criterion is still met; the implementer can include the trailing newline for a perfectly clean deletion. Not a plan defect.
- [observation] Both Round-1 fixes read correctly: tool name is now `mcp__mcp-workspace__edit_file`; edit guidance simplified to a single-line edit. Scope, one-step-one-commit granularity, and the verification-gate decision all align with planning_principles.

**Factual verification (all CONFIRMED against live repo):**
- `.large-files-allowlist` has exactly one `src/mcp_coder/cli/parsers.py` line, in the position described.
- `parsers.py` is 560 lines (<750). `file_sizes.py`: `load_allowlist()` exists, `passed = len(violations) == 0`.
- The two out-of-scope stale entries remain, correctly deferred to #1029.

**Decisions**: nothing to fix; the one nit is handled at implementation time, not in the plan.

**User decisions**: none needed.

**Changes**: none. Zero plan files changed this round.

**Status**: no changes needed — review loop converged.

---

## Final Status

- **Rounds run**: 2.
- **Round 1**: fixed two instruction-text nits in `step_1.md` (edit-tool name typo; simplified edit guidance). Committed `7ceb6bc`.
- **Round 2**: zero plan changes — loop converged.
- **Escalations to user**: none. All findings were mechanical or observational; scope and design were correct and internally consistent.
- **Verdict**: **Plan is ready for approval.** Single step: remove the stale `src/mcp_coder/cli/parsers.py` line from `.large-files-allowlist` and verify via `mcp-coder check file-size --max-lines 750`. All factual claims verified against the live repo.
