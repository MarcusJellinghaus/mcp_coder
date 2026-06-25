# Plan Review Log — Issue #960

**Issue:** Remove commit-clipboard command, claude-code-sdk, and unused dependencies
**Branch:** 960-remove-commit-clipboard-command-claude-code-sdk-and-unused-dependencies
**Base:** main (branch up to date — no rebase needed)
**Plan files:** pr_info/steps/step_1.md … step_5.md, summary.md
**Implementation status:** Not started (TASK_TRACKER.md empty)

---

## Round 1 — 2026-06-25

**Findings** (from `/plan_review` engineer):
- #1 Stale doc line: `docs/architecture/architecture.md:182` references `claude_code_api.py`, which Step 4 deletes — would dangle. (formatting/stale-docs)
- #2 `formatters.py` module docstring ("text, verbose, raw") goes stale after the 3 formatters are removed. (formatting/boy-scout)
- #3 Step 4's `json`-import instruction is internally contradictory ("keep json" vs "drop if vulture flags"); `json` is still used by `print_stream_event`. (clarity)
- #4 `help.py` "prompt" command described as "via Claude API" — slightly misleading post-removal. (pre-existing, out of scope)
- Verified-correct (no action): `_verify_claude_before_use` fold + `@patch` validity, `ClaudeAPIError` relocation/repoint, the 3 module-level SDK test consumers, `vulture_whitelist.py:82` removal, step granularity/ordering (2→1, 4→3, 5 last), dependency removals applied during planning not deferred.

**Decisions**:
- #1 ACCEPT — real inherited gap; add to Step 4's architecture.md edit.
- #2 ACCEPT — cheap cleanup; add to Step 4.
- #3 ACCEPT — tighten wording; outcome already correct but protects implementer.
- #4 SKIP — pre-existing wording, outside issue surface; folding it in = scope drift.

**User decisions**: none — all findings were straightforward improvements handled autonomously (no design/requirements/scope questions).

**Changes** (via `/plan_update` engineer):
- `pr_info/steps/step_4.md`: extended architecture.md edit to also drop the `claude_code_api.py` line (~182); added bullet to refresh `formatters.py` module docstring to streaming-only; clarified `json` import is kept (used by `print_stream_event`) and removed the contradictory vulture hedge.
- `pr_info/steps/Decisions.md`: created; logged the three accepted triage decisions.

**Status**: plan changed — committing; loop continues with a fresh review round.
