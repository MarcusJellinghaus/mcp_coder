# Summary: Branch-issue linkage check falls back to closing PRs (#1255, closes #708)

## Problem

`update_workflow_label()` (`workflow_utils/label_transitions.py`) and
`validate_branch_issue_linkage()` (`workflows/create_pr/core.py`) verify the
branch against GitHub's `linkedBranches` only. Once a PR is opened, GitHub links
the PR to the issue and the branch drops out of `linkedBranches`. The check
then fails, and label transitions in fix-ci, fix-conflict, review and implement
re-runs are skipped, which leaves issues stuck on their busy label.

## Solution

Use one shared helper that makes **one** GraphQL request
(`IssueBranchManager.get_linked_branch_and_closing_prs_or_none()`). The branch
counts as linked if it is a linked branch **or** the head ref of an open PR
that closes the issue.

## Architectural / design changes

- **New primitive module** `mcp_coder.workflow_utils.branch_linkage` with
  `is_branch_linked_to_issue(branch_manager, issue_number, branch_name) -> Optional[bool]`.
  - `True`: the branch matches a linked branch or a closing PR's `head_ref_name`.
    Logged at INFO, naming the source (linked branch or closing PR #N).
  - `False`: neither source matches. Logged as WARNING, with a hint that a PR
    without `Closes #N` cannot be detected.
  - `None`: the lookup failed (the mcp-workspace method returned `None`).
    Logged as ERROR, so a GitHub outage is distinguishable from a real
    linkage miss.
- **All logging lives in the helper (KISS).** The callers only branch on the
  result (`if not linked: return False/None`). Both callers therefore log an
  error on a failed lookup and a warning on a miss, without duplicating the
  message text. The log lines come from the `branch_linkage` logger.
- **Strict check.** There is no branch-name-only fallback and no "open PR by
  head ref" fallback.
- **One request instead of two.** `get_linked_branches()` is no longer used by
  these two callers. Other callers (`gh_tool`, `create_plan`, vscodeclaude,
  coordinator) are unchanged; `checkout-issue-branch` is tracked in #1261.
- **Shim:** `mcp_coder.mcp_workspace_github` additionally re-exports
  `ClosingPRRef` (a NamedTuple with `number` and `head_ref_name`).
- **Behaviour that does not change:**
  - Both callers are non-blocking: they never raise.
  - `validated_issue_number` callers skip validation entirely.
  - `update_workflow_label()` still builds `IssueBranchManager` via `__new__`
    + `BaseGitHubManager.__init__`.
- **Known limitations** (documented in the helper docstring):
  - Only PRs that close the issue (`Closes #N` or a manual link) are seen.
  - Matching uses `head_ref_name` only, so a fork PR with the same branch name
    matches.
  - If create-pr's pre-PR linkage check fails, the PR body gets no
    `Closes #N` line, so the fallback can never match for that PR.
- **Duplicate log on failure is expected.** The mcp-workspace method logs its
  own warning/error on `None` paths, and the helper adds its ERROR line.

## Files created / modified

| Action | Path |
|---|---|
| Modify | `src/mcp_coder/mcp_workspace_github.py` (re-export `ClosingPRRef`) |
| Create | `src/mcp_coder/workflow_utils/branch_linkage.py` |
| Create | `tests/workflow_utils/test_branch_linkage.py` |
| Modify | `docs/architecture/architecture.md` (add `branch_linkage` to the `workflow_utils` list) |
| Modify | `src/mcp_coder/workflow_utils/label_transitions.py` |
| Modify | `tests/workflow_utils/test_label_transitions.py` |
| Modify | `src/mcp_coder/workflows/create_pr/core.py` |
| Modify | `tests/workflows/create_pr/test_workflow_helpers.py` |

No `tach.toml` / import-linter change is needed: `workflow_utils` already
depends on `mcp_workspace_github`, and `workflows` depends on `workflow_utils`.

## Steps

1. [step_1.md](./step_1.md): shim re-export, the `branch_linkage` helper, and its tests.
2. [step_2.md](./step_2.md): `update_workflow_label()` uses the helper, and its tests are re-patched.
3. [step_3.md](./step_3.md): `validate_branch_issue_linkage()` uses the helper, and its tests are re-patched (closes #708).
