# review-implementation review log 1

## Round 1 — 2026-08-25
**Findings**:
I'll start by gathering context.Now let me look at the source diffs.I reviewed the branch diff against `origin/main` (12 source files, 12 test files, 6 doc files; CI on the branch tip is green, so the tests did execute despite the local venv being unable to collect them).

`src/mcp_coder/cli/utils.py:380` — medium — `find_context_claude_md` returns only the nearest ancestor level with a hit, but Claude Code loads `CLAUDE.md` from *every* ancestor up to root; consequently the "outside `project_dir`" warning cannot fire whenever the project has its own `CLAUDE.md` (the normal case), leaving the ancestor-level drift the issue exists to surface unreported.
`src/mcp_coder/cli/utils.py:25` — low — `_CONTEXT_LABEL` "Project instructions (Claude cwd walk):" overclaims: it names the whole cwd walk while only the nearest level is reported, contrary to requirement 5's "word the label so it does not claim to be a complete account".
`pr_info/TASK_TRACKER.md:28` — medium — requirement 1's gating pre-flight marker probe (and its post-Step-7 repeat) is referenced but no result is recorded anywhere; the issue's sole acceptance evidence that the fix delivers the project's rules is therefore absent.
`src/mcp_coder/cli/utils.py:476` — low — `resolve_execution_dir` now walks the filesystem to root and emits OUTPUT/WARNING logging as a side effect of a "resolve" call; documented deviation from requirement 5 ("a small dedicated helper called next to each `resolve_execution_dir`") and flagged by the plan as an open reviewer decision.
`tests/cli/commands/test_implement.py:536` — low — still named `test_default_execution_dir_uses_cwd` while now asserting `project_dir=`; same stale name at `tests/cli/commands/test_create_pr.py:531` and `tests/cli/commands/test_create_plan.py:182`, whereas the equivalents in `test_prompt.py` and `test_execution_dir_integration.py` were renamed.
**Decisions**:
Verdict(decision='tasks', tasks=["In src/mcp_coder/cli/utils.py:380, change find_context_claude_md so it collects CLAUDE.md hits from every ancestor directory up to the filesystem root (matching how Claude Code loads context), not just the nearest ancestor level, so that the 'outside project_dir' warning still fires when the project has its own CLAUDE.md.", 'In pr_info/TASK_TRACKER.md:28, record the actual result of the requirement-1 gating pre-flight marker probe and its post-Step-7 repeat, so the acceptance evidence for the fix is documented.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-08-25
**Findings**:
I'll start by gathering context.`src/mcp_coder/cli/utils.py:357` — low — `find_context_claude_md` reports hits at *every* ancestor level, deliberately deviating from #1113's Decisions table and acceptance criterion ("every hit at the nearest ancestor level that has any"); the code is the better behaviour, so the issue text is what needs amending to keep acceptance checkable.
`pr_info/TASK_TRACKER.md:38` — medium — Requirement 1's gating pre-flight marker probe and the post-Step-7 repeat are recorded as NOT PERFORMED, so the issue's sole acceptance evidence that the driven project's rules actually reach the agent is still absent (needs a human/live-session run; the automated tests cover only the `cwd == project_dir` proxy).
`tests/cli/commands/test_verify_prompts_context.py:67` — low — class docstring "Every CLAUDE.md at the nearest ancestor level is named" contradicts the all-levels walk that `test_own_claude_md_does_not_mask_a_stale_ancestor` in the same class asserts.
`tests/cli/test_utils_context_root.py:151` — low — `test_report_logs_every_hit` docstring "Both files at the nearest level are named" carries the same stale nearest-level wording after the walk was changed to collect every level.
**Decisions**:
Verdict(decision='tasks', tasks=["In tests/cli/commands/test_verify_prompts_context.py:67, update the class docstring to describe the all-ancestor-levels walk actually asserted (e.g. every CLAUDE.md found at any ancestor level is named), removing the stale 'nearest ancestor level' wording that contradicts test_own_claude_md_does_not_mask_a_stale_ancestor.", "In tests/cli/test_utils_context_root.py:151, update the test_report_logs_every_hit docstring so it no longer says 'Both files at the nearest level are named'; word it to match the every-level collection behaviour the test verifies."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-08-25
**Findings**:
I'll start by gathering context.`src/mcp_coder/cli/utils.py:438` — medium — the outside-`project_dir` warning text ("the driven project's rules may not reach the agent") is factually wrong for the ancestor-hit case the all-levels walk now surfaces: when `project_dir` has its own `CLAUDE.md`, that file *is* loaded and only an extra ancestor file is flagged, so the load-bearing warning cries wolf on the common case.
`pr_info/TASK_TRACKER.md:38` — medium — requirement 1's gating pre-flight probe and the post-Step-7 repeat are still recorded as NOT PERFORMED; the issue's only acceptance evidence that the driven project's rules reach the agent remains absent (automated tests cover the `cwd == project_dir` proxy only).
`src/mcp_coder/cli/commands/check_branch_status.py:199` — low — hoisting the resolver out of the `--fix` block makes read-only runs (which never launch Claude) log "Claude working directory: …" and fail with exit 2 on a bad `--execution-dir`; the report asserts a Claude context that no Claude process will use.
`src/mcp_coder/cli/utils.py:357` — low — `find_context_claude_md` collects every ancestor level, deliberately deviating from #1113's Decisions table and acceptance criterion ("every hit at the nearest ancestor level that has any"); the code is the better behaviour, so the issue text is what still needs amending to keep acceptance checkable (unchanged from round 2).
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
