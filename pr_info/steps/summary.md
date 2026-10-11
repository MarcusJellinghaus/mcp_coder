# Summary: Support epic branches end to end (#1191)

## Goal

An epic is delivered on an epic branch (e.g. `epic/multi-language`). Each sub-issue names it in `### Base Branch`; its branch is cut from the epic branch and its PR targets it. The epic branch is merged to main last, by a manually created PR.

Most of this already works: create-plan, create-pr, review and the implement workflow's rebase step all honour an issue's `### Base Branch`. This change closes the remaining gaps:

1. `mcp-coder rebase` refuses any non-`main`/`master` base unless `--base-branch` is passed. It will now trust a base named in the issue.
2. A base branch missing on origin fails late or with a poor message. One shared helper now checks it and fails with a clear message.
3. `gh-tool get-base-branch` documents the wrong priority order and exits 0 printing `None` when detection fails.
4. The epic-branch procedure is not documented.

## Architectural / design changes

All changes centre on `workflow_utils/base_branch.py`, which stays the single home of base-branch logic.

- **Detection source is exposed.** New `BaseBranchSource` enum (`ISSUE`, `PR`, `MERGE_BASE`, `DEFAULT`) and `detect_base_branch_with_source()`, returning `(branch, source)` or `None`. `detect_base_branch()` delegates to it and keeps its plain `Optional[str]` return, so its existing callers are untouched.
- **Shared missing-base check.** New `check_base_branch_on_origin(project_dir, base) -> Optional[str]` runs `git ls-remote --exit-code --heads origin <base>` through the `mcp_coder.utils.subprocess_runner` shim (`execute_command`). It returns `None` when the branch exists, else one error message. `ls-remote` asks the remote directly, so it works in a fresh clone that lacks `origin/<base>`. No layering change: `workflow_utils` already depends on `mcp_coder.utils` (tach) and `failure_handling.py` already uses `execute_command`.
- **Rebase trust rule.** `workflows/rebase.py::_resolve_base_branch` accepts a detected base when its source is `ISSUE` or it is `main`/`master`; bases found by PR, merge-base or default heuristics on any other branch still need `--base-branch`. The `/rebase` skill is unchanged.
- **Callers of the missing-base check:**
  | Caller | Behaviour on a missing base |
  |---|---|
  | `mcp-coder rebase` | exit 2, before the `pr_info/` guard |
  | create-plan `manage_branch` (new-branch path, base set) | raises `BaseBranchMissingError`; `core.py` turns it into the `WorkflowFailure` message (reaches the issue comment) |
  | create-pr `create_pull_request` | returns `(None, msg)` |
  | implement rebase step `_attempt_rebase_and_push` | warns and returns `False` (this step never fails the workflow) |
- **create-plan error propagation.** `manage_branch` keeps its `Optional[str]` return (no churn in ~25 test mocks). The one new failure is a small exception re-raised past its catch-all, caught explicitly in `core.py`.

Not changed: `/rebase` skill, coordinator command templates, cross-repo base branches (unsupported by design), automatic "Closes" lists.

## Files

Modified (source):
- `src/mcp_coder/workflow_utils/base_branch.py` — enum, `detect_base_branch_with_source`, `check_base_branch_on_origin`
- `src/mcp_coder/workflows/rebase.py` — trust rule, missing-base check
- `src/mcp_coder/workflows/create_plan/prerequisites.py` — `BaseBranchMissingError`, check in `manage_branch`
- `src/mcp_coder/workflows/create_plan/core.py` — catch `BaseBranchMissingError`
- `src/mcp_coder/workflows/create_pr/core.py` — check in `create_pull_request`
- `src/mcp_coder/workflow_steps/rebase.py` — check in `_attempt_rebase_and_push`
- `src/mcp_coder/cli/commands/gh_tool.py` — `None` check, docstring order
- `src/mcp_coder/cli/parsers.py` — rebase `--base-branch` help text

Modified (tests):
- `tests/workflow_utils/test_base_branch.py`
- `tests/workflows/rebase/test_guards.py`, `tests/workflows/rebase/test_workflow.py`
- `tests/workflows/create_plan/test_branch_management.py`, `tests/workflows/create_plan/test_failure_handling.py`
- `tests/workflows/create_pr/test_repository.py`
- `tests/workflow_steps/test_rebase.py`
- `tests/cli/commands/test_gh_tool.py`

Modified (docs):
- `docs/cli-reference.md` — `rebase --base-branch` text; `gh-tool get-base-branch` priority order
- `docs/repository-setup/github.md` — new "Epic Branches" subsection

No new files or modules besides `pr_info/steps/`.

## Steps

1. `base_branch.py`: source enum, `detect_base_branch_with_source`, `check_base_branch_on_origin`
2. `mcp-coder rebase`: trust issue-named base, check base on origin
3. create-plan: missing-base check in `manage_branch`
4. create-pr: missing-base check in `create_pull_request`
5. Implement rebase step: missing-base check
6. `gh-tool get-base-branch`: `None` handling and priority docstring
7. Docs: epic-branch procedure and CLI reference fixes

Out of scope (manual, after merge): creating and pushing `epic/multi-language`; the sample-epic "Done when" run, recorded in the PR.
