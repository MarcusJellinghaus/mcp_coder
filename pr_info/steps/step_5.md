# Step 5: create-plan formatter pre-flight and formatted plan commit

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`.
> Write the tests first, then the code. Run pylint, mypy, the fast pytest set
> (`-n auto`) and `check_file_size` (max 750). Format, then make exactly one
> commit.

## WHERE

- `src/mcp_coder/workflows/create_plan/core.py`: `run_create_plan_workflow.body`
- `tests/workflows/create_plan/test_formatting.py` (new)
- Existing `tests/workflows/create_plan/*` tests: adapt only if they break.
  If one fails at the new pre-flight because its project dir has no loadable
  toolkit, patch `mcp_coder.workflows.create_plan.core.check_formatter_config`
  to return `None` in that test.

## WHAT

No new functions. Two insertions in `body()`:

1. After the `branch_name is None` check of Step 2 and before Step 3's
   `check_pr_info_not_exists`:

   ```python
   formatter_err = check_formatter_config(project_dir, warn_legacy_key=True)
   if formatter_err:
       failure = WorkflowFailure(
           category=FAILURE_LABELS["prereq"],
           stage="Prerequisites (formatter config)",
           message=formatter_err,
           elapsed_time=time.time() - start_time,
       )
       _handle_workflow_failure(failure, project_dir, update_issue_labels,
                                post_issue_comments, issue_number=issue_number)
       return 1
   ```

2. Directly before `commit_all_changes(commit_message, project_dir)`:
   `format_best_effort(project_dir, "plan commit")`.

## HOW

- Import:
  `from mcp_coder.workflow_steps.commit import check_formatter_config, format_best_effort`.
  The `formatter_mocks` fixture (step 1) patches `format_best_effort` here
  automatically.
- Add a short comment above the pre-flight: it runs after `manage_branch`
  because the plan branch may start from a base with a different config, and
  before `create_pr_info_structure` so a failure leaves no `pr_info/`.
- Precondition: after the change, if `check_file_size` (max 750) reports
  `src/mcp_coder/workflows/create_plan/core.py`, write one line to
  `pr_info/.blocked.txt` and stop.

## ALGORITHM

```
manage_branch(...) -> branch_name or fail
err = check_formatter_config(project_dir, warn_legacy_key=True)
if err: fail(prereq, "Prerequisites (formatter config)", err); return 1
check_pr_info_not_exists / create_pr_info_structure / prompts / validate
format_best_effort(project_dir, "plan commit"); commit_all_changes(...); git_push(...)
```

## DATA

Exit code `1` on a failed pre-flight, with the `planning_prereq_failed` label
via `_handle_workflow_failure`.

## Tests first (`test_formatting.py`)

Patch the module's externals the way the existing create-plan workflow tests
do (`is_working_directory_clean`, `check_prerequisites`, `manage_branch`,
`check_pr_info_not_exists`, `create_pr_info_structure`, `run_planning_prompts`,
`validate_output_files`, `commit_all_changes`, `git_push`,
`_handle_workflow_failure`). Record call order with a shared parent
`MagicMock` (`attach_mock`) or side effects that append to a list.

- The pre-flight runs after `manage_branch` and before
  `create_pr_info_structure` and `run_planning_prompts`.
- A pre-flight error → returns 1; `_handle_workflow_failure` gets a failure
  with `category == "planning_prereq_failed"` and the error text;
  `create_pr_info_structure` and `run_planning_prompts` are not called.
- Success path: `formatter_mocks.format_best_effort` is called with
  `project_dir` before `commit_all_changes`.
- The real `format_best_effort`, put back with
  `monkeypatch.setattr(core, "format_best_effort", commit.format_best_effort)`,
  with `commit.run_formatters` raising `FormatterConfigError` (and in a second
  case returning False): a WARNING is logged and `commit_all_changes` is still
  called; the workflow returns 0.

## Commit

`feat(create-plan): check the formatter config early and format the plan commit`
