# Summary: stop rebase-and-push from overwriting commits someone else pushed (#1382)

## Problem

`rebase_onto_branch` and `fetch_remote` refresh `origin/<branch>`. The later `git push --force-with-lease` then passes even when someone else pushed to the branch, so their commit is removed from the remote and the run reports success.

Confirmed for this plan through the real `_attempt_rebase_and_push` against a bare repo: outcome `ok`, foreign commit gone.

## Goal

A rebase-and-push must never remove a commit someone else pushed. If the branch has commits this checkout does not have, stop and report it.

## Architectural / design changes

**One guard, in one helper.** `_check_branch_not_moved(project_dir, pre_sha)` in `workflow_steps/rebase.py` requires the SHA of `origin/<branch>` to be an ancestor of the pre-rebase HEAD.

- It needs no network call and never raises.
- It returns `"passed" | "moved" | "skipped" | "error"`.
- It does all the guard's logging, so callers only branch on the status. `implement` discards the outcome and still gets the warning.
- It compares by SHA from `get_remote_branch_commit_sha`, because a tag named `origin/<branch>` makes a name comparison pass wrongly.
- `skipped` means the remote ref is absent (never-pushed branch, or a read error). The lease remains the backstop.

**The lease stays.** It still rejects any push that lands after the last fetch.

**Check after the rebase, against the pre-rebase HEAD.** `rebase_onto_branch` does its own fetch, so an earlier check could be out of date. Against the post-rebase HEAD a normal rebase would wrongly fail. A failed check therefore resets to the captured HEAD inside `_attempt_rebase_and_push`, because `implement`, `fix-conflict` and review do not reset on a failed outcome.

**New outcome `branch_moved`.** Added to `RebaseReason`.

| Helper status | `_attempt_rebase_and_push` result |
|---|---|
| `passed`, `skipped` | Lease push, as today |
| `moved` | Reset, return `branch_moved`, no push |
| `error` | Reset, return `push_failed`, no push |

An unreadable pre-rebase HEAD returns `rebase_failed` before rebasing.

**Shared text.** `BRANCH_MOVED_REASON` and `BRANCH_MOVED_NEXT_STEP` live in `workflow_steps/rebase.py`, because `workflow_steps/merge.py` cannot import from `workflows/review/`.

**`push_failed` is reworded.** It now also covers a check error where no push happened, and it no longer tells anyone to run `git push --force-with-lease`.

**Labels and exit codes do not change.** Review routes `branch_moved` to `status-07` through the existing `"rebase"` path. Other callers gain a comment or next step where they only logged or showed a raw reason.

## Caller behaviour on `branch_moved`

| Caller | Label / exit | Added feedback |
|---|---|---|
| `implement` | Continues (Decision 3) | Warning from the helper |
| Review | `status-07` | `_REBASE_HANDOFF` entry |
| `mcp-coder rebase` | Exit 2 | Helper log; two checks |
| `create-pr` pre-creation | Unchanged | None; its later plain push is rejected and reported |
| `create-pr` post-creation | Unchanged | New "PR Creation Failed" comment |
| `fix-conflict`, verdict | Unchanged | `Next step` in `_fail` |
| `fix-conflict`, no verdict | Unchanged | New "Fix Conflict Failed" comment |
| Auto-merge | `merge_failed` | `Next step` in `_failed` |
| `/rebase` skill | Stops | Check after the fetch and before the push |

## Files

### Created

| File | Purpose |
|---|---|
| `tests/workflow_steps/test_rebase_branch_moved.py` | Real-git and unit tests of the guard |
| `tests/workflows/rebase/test_workflow_branch_moved.py` | Real-git and unit tests of `run_rebase_workflow` |
| `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` to `step_7.md` | This plan |

### Modified

| File | Step | Change |
|---|---|---|
| `src/mcp_coder/mcp_workspace_git.py` | 1 | Export `git_merge_base` |
| `src/mcp_coder/workflow_steps/rebase.py` | 1 | Reason, constants, helper, guard, log wording, docstrings |
| `tests/conftest.py` | 1 | `bare_remote` fixture |
| `tests/workflow_steps/test_rebase.py` | 1 | Autouse mocks, reason list |
| `tests/workflows/implement/test_core_failure_routing.py` | 1 | `implement` continues on `branch_moved` |
| `src/mcp_coder/workflows/rebase.py` | 2 | Two checks, docstring |
| `src/mcp_coder/cli/commands/rebase.py` | 2 | Exit contract |
| `tests/workflows/rebase/conftest.py` | 2 | `patched` fixture collaborators |
| `src/mcp_coder/workflows/review/handoff.py` | 3 | `branch_moved` entry, `push_failed` rewording |
| `tests/workflows/review/test_handoff_route.py` | 3 | Outcome builder and explicit lists |
| `src/mcp_coder/workflows/create_pr/post_creation.py` | 4 | Comment on `branch_moved` |
| `tests/workflows/create_pr/test_post_creation.py` | 4 | Comment tests |
| `tests/workflows/create_pr/test_workflow_labels.py` | 4 | Pinned call arguments |
| `src/mcp_coder/workflows/fix_conflict/core.py` | 5 | `Next step` and no-verdict comment |
| `tests/workflows/fix_conflict/test_core.py` | 5 | Both paths |
| `docs/cli-reference.md` | 5 | `fix-conflict` section |
| `src/mcp_coder/workflow_steps/merge.py` | 6 | `Next step` in `_failed` |
| `tests/workflow_steps/test_merge.py` | 6 | `Next step` test |
| `.claude/skills/rebase/SKILL.md` | 7 | Both checks |

No new folders are created, apart from `pr_info/steps/`.

## Steps

1. Guard in `_attempt_rebase_and_push`
2. `mcp-coder rebase` workflow
3. Review hand-off text
4. `create-pr` post-creation comment
5. `fix-conflict` feedback and docs, plus the conditional #1376 comment update
6. Auto-merge next step
7. `/rebase` skill

## Rules for every step

- **Tests first:** write the step's tests, confirm the new ones fail, then implement.
- **One commit per step:** tests, implementation and passing checks together.
- **Checks before committing:**
  - `mcp__mcp-tools-py__run_pylint_check`
  - `mcp__mcp-tools-py__run_mypy_check`
  - `mcp__mcp-tools-py__run_lint_imports_check`
  - `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
  - `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto"]`, `markers=["git_integration"]`, in steps 1 and 2
  - `mcp__mcp-tools-py__run_format_code`
- **File size:** CI's limit is 750 lines. Do not add anything to `tests/workflows/implement/test_core_workflow.py` or `src/mcp_coder/workflows/create_pr/core.py`, and do not touch `.large-files-allowlist`.
- **Test constraints:**
  - `subprocess_isolation` covers `tests`, so real-git tests use GitPython.
  - `tests.workflow_steps` and `tests.workflows` must not import from each other, so shared git setup is a fixture in `tests/conftest.py`.

## Out of scope

- Stopping `implement` on `branch_moved`.
- Automatically integrating the foreign commit.
- Pushes that do not use a lease.
- Blocking the LLM's `git` tool.
- Copies of the `/rebase` skill in sibling repos.
- A next step in `create-pr` pre-creation's failure comment.

## Accepted limits

- A fetch landing between the check and the push, such as an IDE autofetch, still defeats the lease.
- `get_remote_branch_commit_sha` returns `None` on a read error, so the check is skipped and the lease is the backstop.
- A remote rewritten by someone else's rebase stops the run, even with the same content.
- A re-run after an earlier run rebased locally, failed to push and did not reset also stops. `BRANCH_MOVED_NEXT_STEP` covers this.
- After `branch_moved`, review's `_flush_round_log` plain push is rejected and only logs a warning.
- If the reset also fails in `create-pr` post-creation, HEAD differs from `head_before`, so it logs "New commits were pushed" and waits for CI on an unpushed SHA.

## Dependencies

#1376 is independent. Step 5 owns this: if #1376 has already merged, it updates #1376's failure comment, which warns that re-running from a local checkout can reach this overwrite. If #1376 has not merged, Step 5 records in its commit message that the update falls to #1376.
