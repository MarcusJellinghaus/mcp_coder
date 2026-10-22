# Summary — #1261 checkout-issue-branch: check out the PR head instead of creating a duplicate branch

## Problem

`execute_checkout_issue_branch()` (`src/mcp_coder/cli/commands/gh_tool.py`) resolves the
issue's branch with `IssueBranchManager.get_linked_branches()` only. Once a PR is opened,
GitHub drops the branch from `linkedBranches`, the lookup returns `[]`, and the command
creates a second remote branch for the issue.

## Architectural / design changes

- **Resolution goes through the library's 4-step fallback.**
  `get_branch_with_pr_fallback(issue_number, owner, repo_name)` checks, in order: linked
  branch, open PR that cross-references the issue, closed PR whose branch still exists, and
  the branch-name pattern. The manager is built the same way as in
  `services/branch_info.py:get_pr_for_issue`:
  `get_repository_identifier(project_dir)` → `IssueBranchManager(project_dir=..., repo_url=repo_id.https_url)`.
- **Pre-create checks run only when the fallback returns `None`.** `None` can mean three
  things: nothing found, ambiguous, or an API error. A new private helper,
  `_find_precreate_candidates()`, tells them apart. It combines:
  - `get_linked_branch_and_closing_prs_or_none(issue_number)`: linked branches plus the
    head branches of open closing PRs
  - `git ls-remote --heads origin`, run through the `execute_command` shim and filtered
    with the library's regex `(^|/)N[-_]`

  It returns an ordered `dict[branch, label]` (first source wins), or `None` if either
  lookup fails.
- **Candidate rule:** 0 → create the branch as today; 1 → check it out and log the source
  at INFO; 2 or more → new **exit code 3**, with the candidates logged.
- **Several linked branches → exit 3** (previously `branches[0]`, whose order is random).
- **New dependency edge:** `mcp_coder.cli.commands.gh_tool` → `mcp_coder.utils.subprocess_runner`.
  This is allowed by the `cli -> … -> utils` layering. GitPython stays unused.
- The existing path (checkout, the top-level `ValueError`/`Exception` → exit 2 handlers)
  is unchanged. API errors re-raised by the fallback's decorator end up there.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Branch checked out (found, single pre-create candidate, or created) |
| 1 | Issue not found, or branch creation failed |
| 2 | Error: invalid project dir, no repo identifier, lookup failed, `ls-remote` failed, API error, git checkout failed |
| 3 | Ambiguous: pre-create checks found two or more candidates |

### Candidate labels (used in both the INFO and the exit-3 logs)

- `linked branch <name>`
- `closing PR #<N> -> <head_ref_name>`
- `remote branch <name>`

## Files

| Action | Path |
|--------|------|
| Create | `tests/cli/commands/test_gh_tool_checkout.py`: checkout-issue-branch tests (moved out of `test_gh_tool.py`, which sits at the 750-line limit) |
| Modify | `tests/cli/commands/test_gh_tool.py`: remove the moved checkout tests and fixtures |
| Modify | `src/mcp_coder/cli/commands/gh_tool.py`: new resolution flow, `_find_precreate_candidates()`, docstring |
| Modify | `src/mcp_coder/cli/gh_parsers.py`: `checkout-issue-branch` epilog |
| Modify | `docs/cli-reference.md`: `### gh-tool checkout-issue-branch` section |
| Modify | `.claude/skills/implement_direct/SKILL.md`: step 2 handles exit 3 |

Unchanged: `command_catalog.py` (the one-line description stays).

## Steps

1. Move the checkout-issue-branch tests into their own file (pure refactor).
2. Resolution flow + pre-create checks + exit 3 (TDD), with function docstring.
3. Docs: parser epilog (TDD via the epilog test), `cli-reference.md`, `implement_direct` SKILL.

## Known limitation (documented, not fixed)

Several open PRs that only *mention* the issue, none of which closes it and none of whose
head branches match the name pattern, leave the pre-create checks empty. In that case a
branch is still created.
