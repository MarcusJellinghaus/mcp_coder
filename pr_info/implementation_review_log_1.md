# review-implementation review log 1

## Round 1 — 2026-11-27
**Findings**:
Now the source diff.Reviewing the #1483 diff: checking the commit helper semantics and the new tests next.Checking the remaining Linux templates and the new tracker-prep / review-log tests.src/mcp_coder/workflows/implement/task_tracker_prep.py:140 — low — `formatted` is assigned only after `_other_changed_files` returns, so if `get_full_status` raises after `format_best_effort` (line 136) has already rewritten files, the `finally` skips `_restore_formatted` and the step fails with the formatter's changes left in the tree.
src/mcp_coder/workflows/implement/task_tracker_prep.py:183 — low — `reset_hard(project_dir, "HEAD")` also reverts tracked changes to files the clean-tree check ignores (`DEFAULT_IGNORED_BUILD_ARTIFACTS`, e.g. a `uv.lock` rewritten by `mcp-coder setup`), so the docstring's "only discards what this step changed" is wrong.
**Decisions**:
Verdict(decision='tasks', tasks=["In src/mcp_coder/workflows/implement/task_tracker_prep.py around line 136-140, make sure the formatter's changes are restored if anything after format_best_effort raises, including get_full_status inside _other_changed_files. Set the `formatted` flag, or an equivalent guard, right after format_best_effort returns and before _other_changed_files is called, so the `finally` block always calls _restore_formatted. Add a unit test where get_full_status raises after formatting and assert that _restore_formatted is called.", 'In src/mcp_coder/workflows/implement/task_tracker_prep.py:183, replace reset_hard(project_dir, "HEAD") with a restore of only the paths this step changed, so tracked changes to files in DEFAULT_IGNORED_BUILD_ARTIFACTS (e.g. a uv.lock rewritten by setup) are kept. This makes the docstring\'s claim that it \'only discards what this step changed\' true. Add a test showing a pre-existing tracked change to an ignored build artifact survives the discard path.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-27
**Findings**:
Reviewing the branch's review-loop changes; checking `git_diff`'s output contract and the `sha_before` placement next.Source looks consistent; checking the docs gap (`docs/repository-setup/python.md` isn't in the diff) and the test fixture.No opt-out list in `python.md`, so no gap there. Running file-size check and the touched test suites.Tests pass (1748). Running mypy and pylint before finalising the report.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
