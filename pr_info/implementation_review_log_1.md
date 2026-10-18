# review-implementation review log 1

## Round 1 — 2026-10-18
**Findings**:
Now let's view the actual implementation diffs, excluding pr_info noise.Implementation matches the plan exactly. The core risk is the `LINKED_VIA_PR` state added mid-step without updating the review material — this depends entirely on an unverifiable upstream predicate.Ruff is clean. Final report:

tests/cli/commands/test_check_branch_status_exit_code.py:121 — medium — `(LinkedBranchStatus.LINKED_VIA_PR, 0)` assumes upstream's `linked_branch_blocks` predicate was updated to exclude `LINKED_VIA_PR` from blocking. The installed `mcp_workspace` in this review environment only documents `linked_branch_blocks` as "True for every state other than OK and NOT_CHECKED" (no `LINKED_VIA_PR` exemption visible), and its `LinkedBranchStatus`/`BranchStatusReport` are stale relative to what the PR assumes, so this could not be verified here. Unlike the original six states (explicitly re-confirmed against upstream source across ~40 re-checks in step_2.md), the seventh member's non-blocking behavior rests on an unconfirmed assumption recorded only in a short note. If upstream's predicate wasn't actually updated, this specific parametrized case fails — self-catching via CI, but worth an explicit re-confirmation before merge given how rigorously every other API assumption in this PR was checked.

NO FINDINGS otherwise — `_exit_code` term ordering, shim re-export, docstring, and docs table all match the planned design correctly; ruff is clean.
**Decisions**:
Verdict(decision='tasks', tasks=["Verify that upstream's `linked_branch_blocks` predicate (in the actual mcp-workspace dependency this PR will ship against, not the possibly-stale reference checkout) excludes `LINKED_VIA_PR` from blocking. Confirm by reading the upstream source directly (via get_library_source or the mcp-workspace reference project's current code) rather than relying on the note in step_2.md. If the predicate does exclude it, record that confirmation (source + line) in step_2.md alongside the other ~40 re-checks. If it does NOT exclude it, fix the test expectation at tests/cli/commands/test_check_branch_status_exit_code.py:121 to match actual upstream behavior."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-18
**Findings**:
Now let's look at the actual implementation diffs, excluding pr_info.Implementation diff reviewed against main (`src/mcp_coder/checks/branch_status.py`, `src/mcp_coder/cli/commands/check_branch_status.py`, `docs/cli-reference.md`, `.claude/skills/implementation_approve/SKILL.md`, tests). The `_exit_code` tier ordering, shim re-exports, and tests match the plan exactly; mypy and pylint pass on the touched files. One finding:

`docs/cli-reference.md:781` — high — "A branch linked only through a closing PR is accepted" contradicts the shipped behavior: `_collect_linked_branch_status` only queries GitHub's `linkedBranches` GraphQL connection (`mcp_workspace/checks/branch_status.py:_collect_linked_branch_status`), with no PR-timeline fallback. An issue whose only connection to the branch is a closing PR reference (no explicit linked branch) resolves to `NOT_LINKED`, and `linked_branch_blocks(NOT_LINKED)` is `True` → exit 1, i.e. blocked, not accepted. This sentence isn't in the plan (`pr_info/steps/step_2.md` 2d draft) and appears to be an unverified addition that misdescribes the exit-code contract this issue is about.

NO FINDINGS otherwise.
**Decisions**:
Verdict(decision='tasks', tasks=["Fix docs/cli-reference.md:781 — remove or correct the claim that 'a branch linked only through a closing PR is accepted'. Per the shipped implementation, `_collect_linked_branch_status` only queries GitHub's `linkedBranches` GraphQL connection with no PR-timeline fallback, so a branch linked solely via a closing PR resolves to `NOT_LINKED`, which `linked_branch_blocks` treats as blocking (exit 1). Update the doc text to accurately describe this behavior, consistent with the plan in pr_info/steps/step_2.md."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-10-18
**Findings**:
No local `main` branch; use `origin/main`.Confirmed installed `mcp_workspace` matches the plan exactly — six states, correct predicate. No `LINKED_VIA_PR`, consistent with the step_2.md correction already applied.This matches the actual shipped behavior accurately and resolves round 2's finding correctly.

Everything in the diff — shim re-export, `_exit_code` terms/ordering/docstring, docs table, SKILL.md wording, and tests — matches the verified upstream API and the plan. Round 1 and round 2 findings are both resolved correctly. Ruff and mypy pass on touched files; pytest could not run due to an unrelated environment issue (`verify_github_security` missing from installed `mcp_workspace.github_operations`, surfaced via `mcp_coder/mcp_workspace_github.py`, a file untouched by this diff) that blocks collection of the entire test suite, not specific to this change.

NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
