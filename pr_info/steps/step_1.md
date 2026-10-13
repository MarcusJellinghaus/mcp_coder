# Step 1 — dispatch_workflow(): add repo_name parameter and LABEL

See [summary.md](./summary.md) for context and the overall design.

Precondition: `dispatch_workflow()` in `core.py` must still have the
signature and structure described below (params dict built in one place,
`workflow_config` resolved before the `branch_strategy` if/else). If it
does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/core.py` — `dispatch_workflow()`
- `src/mcp_coder/cli/commands/coordinator/commands.py` —
  `execute_coordinator_run()` (the one call site)
- `tests/cli/commands/coordinator/test_core.py` — 5 existing
  `dispatch_workflow(...)` calls, plus the guard test
- `tests/cli/commands/coordinator/test_commands.py` —
  `test_execute_coordinator_run_single_repo_success`

## WHAT

New signature (insert `repo_name` after `repo_config`):

```python
def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    repo_name: str,
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str,
) -> None:
```

Add `repo_name` to the docstring `Args:` block.

## HOW

- `execute_coordinator_run()` already holds `repo_name` as its `for
  repo_name in repo_names:` loop variable. Add `repo_name=repo_name` to its
  `dispatch_workflow(...)` call.
- No new imports needed.

## ALGORITHM

The `from_issue` branch (`else:` of `workflow_config["branch_strategy"] ==
"main"`) currently does:

```python
repo_owner, repo_name = repo_id.owner, repo_id.repo_name

resolved_branch = branch_manager.get_branch_with_pr_fallback(
    issue_number=issue["number"],
    repo_owner=repo_owner,
    repo_name=repo_name,
)
```

This local `repo_name` would shadow the new `repo_name` parameter for the
rest of the function. Rename it to `issue_repo_name` (its downstream use in
the same call is the only other occurrence):

```python
repo_owner, issue_repo_name = repo_id.owner, repo_id.repo_name

resolved_branch = branch_manager.get_branch_with_pr_fallback(
    issue_number=issue["number"],
    repo_owner=repo_owner,
    repo_name=issue_repo_name,
)
```

Internal rename only — no change to `get_branch_with_pr_fallback`'s
behavior. With the shadowing gone, the new `repo_name` parameter stays valid
for the rest of the function, so `LABEL` can be built directly in the
existing `params = {...}` dict (Step 4 of the function):

```python
"LABEL": f"{repo_name} - #{issue['number']} - {workflow_config['workflow']}",
```

## DATA

`params` (the dict passed to `jenkins_client.start_job`) gains one key:

```python
{
    "REPO_URL": ...,
    "BRANCH_NAME": ...,
    "COMMAND": ...,
    "GITHUB_CREDENTIALS_ID": ...,
    "LABEL": "mcp_coder - #123 - implement",
}
```

## Tests (write/update first, TDD)

In `tests/cli/commands/coordinator/test_core.py`:

- Add `repo_name="mcp_coder"` (or an equivalent fixed string) to each of the
  5 existing `dispatch_workflow(...)` calls in this file so they match the
  new required parameter.
- In `TestDispatchWorkflowSilentFallthroughGuard.test_each_workflow_dispatches_its_verb`,
  pass a fixed `repo_name` (e.g. `"test_repo"`) and add an assertion that
  `params["LABEL"] == f"test_repo - #777 - {workflow}"` (issue number `777`
  already comes from `_make_issue`).

In `tests/cli/commands/coordinator/test_commands.py`, in
`test_execute_coordinator_run_single_repo_success`, after the existing
`assert mock_dispatch_workflow.call_count == 2`, add:

```python
for call in mock_dispatch_workflow.call_args_list:
    assert call.kwargs["repo_name"] == "mcp_coder"
```

(`"mcp_coder"` matches `args.repo` already set in this test.)

## Checks

Run pylint, pytest (unit marker set from CLAUDE.md), and mypy. All must
pass before committing.

## Commit

One commit: test updates + `core.py`/`commands.py` changes together.

---

## LLM prompt for this step

```
Implement Step 1 of pr_info/steps/summary.md, described in
pr_info/steps/step_1.md.

Follow TDD: update the listed tests first (they should fail), then make
the implementation changes in core.py and commands.py so they pass. Run
pylint, pytest, and mypy; fix anything they flag. Then create exactly one
commit containing the test and implementation changes together.
```
