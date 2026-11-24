# review-implementation review log 1

## Round 1 — 2026-11-24
**Findings**:
Reviewing the branch diff against the issue; now checking `check_loop.py` and the command toolkit's grant format.Source diff looks consistent with the issue; now checking the test diffs for acceptance coverage.`src/mcp_coder/utils/prompt_slots.py:100` — low — The generic re-run list replaces the `check_instructions` fragment of every toolkit that declares Bash grants, not just the command toolkit. A third-party toolkit with wildcard grants (e.g. `Bash(make:*)`) would show "- `make:*`" under the "run each one unchanged" intro. Decision 4 scopes this to the command toolkit.

`src/mcp_coder/utils/prompt_slots.py:31` — low — `RERUN_INTRO` copies `_RERUN_INTRO` in `src/mcp_coder/toolkits/command/toolkit.py:29`, and only a comment keeps the two in sync. The toolkit layer may import from `utils`, so `toolkit.py` could import `RERUN_INTRO` and drop its copy. Not checked: whether `pr_info/plan_review_log_1.md` (not read) rejects that import on purpose.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/utils/prompt_slots.py (~line 100), limit the replacement of the `check_instructions` fragment with the generated re-run list to the command toolkit, as Decision 4 requires. Every other toolkit that declares Bash grants keeps its own `check_instructions` fragment unchanged. Add a test with a non-command toolkit that declares a wildcard grant such as `Bash(make:*)`, and assert that its fragment is not replaced and no `- `make:*`` line appears.', 'Remove the duplicate `_RERUN_INTRO` constant in src/mcp_coder/toolkits/command/toolkit.py:29. Import `RERUN_INTRO` from mcp_coder.utils.prompt_slots instead, and delete the comment that keeps the two copies in sync. First check pr_info/plan_review_log_1.md: if it rejects this import on purpose, leave the code as it is and expand the comment to say why. Run lint-imports after the change.'], escalate_reason=None)
**Changes**:
applied
