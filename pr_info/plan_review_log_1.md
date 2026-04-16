# Plan Review Log — Issue #832

Plan review for: Prep: BaseGitHubManager token param + transition_issue_label primitive (part 1 of 5)

## Round 1 — 2026-04-16

**Findings**:
- F1 [Medium] Step 2 primitive's ALGORITHM does not guard against `get_issue()` returning empty IssueData (number=0). `get_issue()` swallows non-auth failures via `@_handle_github_errors(default_return=create_empty_issue_data())`, so calling `set_labels(0, ...)` afterward raises ValueError — a silent regression vs today's step-6 check.
- F2 [Low] New `TestTransitionIssueLabel` class should be decorated `@pytest.mark.git_integration` to match sibling `TestIssueManagerLabels` in the same file.
- F3 [Low] Step 1 parametrized token-forwarding test does not name its mocking approach (Mock(spec=Path) + is_git_repository patch).
- F4 [Low] Step 1 docstring instruction "Update docstrings to mention the new param" is underspecified — risks implementer drift.
- F5 [Low] Step 3 regression section should caveat: skim listed tests first, swap any log-text assertions for behavioural ones.
- F6 [Low, design] The step-7 INFO log `'Source label ... not present'` is dropped as a side-effect of the config-free primitive — new behaviour change not listed in the issue's "intentional changes."
- F7 No action — dependencies confirmed unchanged.

**Decisions**:
- F1: accept — apply fix (primitive explicitly returns False on empty IssueData + new test case).
- F2: accept — apply class marker.
- F3: accept — name the Mock(spec=Path) + is_git_repository approach.
- F4: accept — bound to a single Args line per __init__.
- F5: accept — add caveat.
- F6: ask user → user picked "Accept the loss" (Option A). Document removal in step_3.md and summary.md.
  - **Round 2 correction**: factual error in Round 1 — the INFO log IS asserted in one test (`test_update_workflow_label_removes_different_workflow_label`, line 635). Corrected across step_3.md, summary.md, Decisions.md in Round 2.
- F7: no action.

**User decisions**:
- Q: How should the plan handle the dropped `'Source label ... not present'` INFO log?
  A: **Accept the loss** (Option A). Keeps the primitive config-free and preserves the single get_issue() call. Document the removal.

**Changes**:
- `pr_info/steps/step_1.md` — named Mock(spec=Path) + is_git_repository mocking approach for parametrized test; bounded docstring update to a single Args line per __init__.
- `pr_info/steps/step_2.md` — added empty-IssueData guard to ALGORITHM (`if issue["number"] == 0: return False`); added test case `test_transition_get_issue_failure_returns_false`; added `@pytest.mark.git_integration` class marker note.
- `pr_info/steps/step_3.md` — added log-string assertion caveat; explicitly documented removal of `'Source label ... not present'` INFO log; tightened step-6 bullet to "primitive owns the fetch and the empty-IssueData guard".
- `pr_info/steps/summary.md` — added one-line note about the removed INFO log in the behaviour-change section.
- `pr_info/steps/Decisions.md` — new file logging Round 1 decisions.

**Status**: Plan files updated. Commit pending. Loop: another review round required (per supervisor workflow).

## Round 2 — 2026-04-16

**Findings**:
- F8 [CRITICAL, blocker] Round 1's claim "No tests assert the 'Source label ... not present' log" is factually wrong. `tests/utils/github_operations/test_issue_manager_label_update.py:635` asserts the exact string inside `test_update_workflow_label_removes_different_workflow_label`. Documentation in 4 files (step_3.md, summary.md, Decisions.md, plan_review_log_1.md) was incorrect; Step 3 would have failed without an explicit assertion rewrite.
- F9 [CRITICAL, blocker] Wrong patch path in step_1.md and Decisions.md #4: used `mcp_coder.utils.github_operations.base_manager.is_git_repository` but `base_manager.py` imports `git_operations` as a module and accesses `git_operations.is_git_repository(...)`. Correct target: `...base_manager.git_operations.is_git_repository` (matches existing `test_base_manager.py:232`).
- F10 [Low] Decisions.md #1 cross-reference quoted heading that didn't match summary.md's actual heading ("Intentional narrow behavior improvement (accepted)").
- F11 [Low] Duplicate/overlapping bullets in step_3.md "Delete from the old body" section (Round 1's insert overlapped an existing bullet).
- F12 [Low] Round 1 caveat mentioned the log phrase `'already has ... without ...'` — confirmed not present in the test suite; dead weight.
- F13 No scope expansion detected.

**Decisions**: All accepted — all fixes are straightforward mechanical corrections. No design questions, no user input needed.

**User decisions**: none required this round.

**Changes**:
- `pr_info/steps/step_3.md` — consolidated two overlapping INFO-log-removal bullets into one; replaced generic "skim… if any do…" caveat with a SPECIFIC instruction naming `test_update_workflow_label_removes_different_workflow_label`, line 635, the assertion to drop, and the behavioural assertions (lines 625/629/632) that cover the contract.
- `pr_info/steps/summary.md` — corrected "No tests assert this log" → names the specific test, line, and notes the assertion will be dropped.
- `pr_info/steps/Decisions.md` — corrected item #1 text; fixed cross-reference heading to match summary.md; corrected item #4 patch path to include `.git_operations.` module prefix.
- `pr_info/steps/step_1.md` — corrected patch path in "Test (write first)" section: `base_manager.is_git_repository` → `base_manager.git_operations.is_git_repository`.
- `pr_info/plan_review_log_1.md` — appended Round 2 correction note under F6 rationale in the Round 1 entry (engineer's own update during Round 2 edits).

**Status**: Plan files updated. Commit pending. Loop: another review round required.


## Round 3 — 2026-04-16

**Findings**:
- Verified Round 2 fixes landed correctly and the asserted facts are accurate:
  - F8 fix: Step 3 line 65 names `test_update_workflow_label_removes_different_workflow_label` and line 635 correctly; verified against actual test file at that exact line.
  - F9 fix: patch path `...base_manager.git_operations.is_git_repository` verified against `base_manager.py:16,200` (module import + attribute access) and existing `test_base_manager.py:232` style.
  - No cross-file contradictions about the INFO log fact.
- F14 [Low, polish] Decisions.md #6 still read as an open action ("before running, skim test assertions") even though the skim was actually completed in Round 2 and resolved in step_3.md:65. Not a blocker, but stale.
- F15 [Info] No scope expansion, no new dependencies introduced across Rounds 1-2.

**Decisions**: F14 — accept, apply (trivial polish to reflect resolved state). Everything else: no action.

**User decisions**: none required.

**Changes**:
- `pr_info/steps/Decisions.md` — rewrote item #6 from "skim-TODO" wording to "skim complete (Round 2)" summary naming the test, line, and the confirmation that the `'already has ... without ...'` phrase does not appear in any assertion.

**Status**: Plan files updated. Commit pending. Loop: one more review round expected to confirm clean state.
