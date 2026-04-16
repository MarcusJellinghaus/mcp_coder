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
